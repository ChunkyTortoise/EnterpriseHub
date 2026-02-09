"""Intent Classification V2 with multi-label support and confidence calibration.

This module provides advanced intent classification capabilities including:
- Fine-tuned classifier with domain-specific intent detection
- Multi-label classification for complex queries
- Confidence calibration for reliable predictions
- Integration with existing QueryClassifier from retrieval module
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import MultiLabelBinarizer

from src.core.exceptions import RetrievalError


class IntentType(Enum):
    """Enumeration of query intent types.

    Covers both general information retrieval intents and
    real estate domain-specific intents.
    """

    # General Intents
    INFORMATIONAL = "informational"
    NAVIGATIONAL = "navigational"
    TRANSACTIONAL = "transactional"
    COMPARISON = "comparison"
    EXPLORATORY = "exploratory"

    # Real Estate Domain Intents
    PROPERTY_SEARCH = "property_search"
    PRICE_INQUIRY = "price_inquiry"
    LOCATION_QUERY = "location_query"
    BUYING_INTENT = "buying_intent"
    SELLING_INTENT = "selling_intent"
    INVESTMENT_RESEARCH = "investment_research"
    MARKET_ANALYSIS = "market_analysis"
    CMA_REQUEST = "cma_request"  # Comparative Market Analysis
    SHOWING_REQUEST = "showing_request"
    FINANCING_QUESTION = "financing_question"
    NEIGHBORHOOD_INFO = "neighborhood_info"
    SCHOOL_DISTRICT_QUERY = "school_district_query"
    AMENITIES_SEARCH = "amenities_search"
    AGENT_CONTACT = "agent_contact"


@dataclass
class IntentClassificationResult:
    """Result of single-label intent classification.

    Attributes:
        primary_intent: The main detected intent
        confidence: Confidence score (0.0-1.0), calibrated
        raw_confidence: Un-calibrated confidence score
        features: Dictionary of extracted features used for classification
        alternative_intents: List of secondary intents with scores
    """

    primary_intent: IntentType
    confidence: float
    raw_confidence: float
    features: Dict[str, Any]
    alternative_intents: List[Tuple[IntentType, float]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "primary_intent": self.primary_intent.value,
            "confidence": self.confidence,
            "raw_confidence": self.raw_confidence,
            "features": self.features,
            "alternative_intents": [(intent.value, score) for intent, score in self.alternative_intents],
        }


@dataclass
class MultiLabelResult:
    """Result of multi-label intent classification.

    Attributes:
        intents: List of detected intents with confidence scores
        primary_intent: The most confident intent
        confidence_scores: Dictionary mapping intents to calibrated confidence
        coverage_score: How well the labels cover the query intent (0.0-1.0)
        label_correlations: Correlation scores between detected intents
    """

    intents: List[IntentType]
    primary_intent: IntentType
    confidence_scores: Dict[IntentType, float]
    coverage_score: float
    label_correlations: Dict[Tuple[IntentType, IntentType], float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "intents": [i.value for i in self.intents],
            "primary_intent": self.primary_intent.value,
            "confidence_scores": {k.value: v for k, v in self.confidence_scores.items()},
            "coverage_score": self.coverage_score,
            "label_correlations": {f"{k[0].value},{k[1].value}": v for k, v in self.label_correlations.items()},
        }


@dataclass
class ClassifierConfig:
    """Configuration for intent classification.

    Attributes:
        min_confidence: Minimum confidence threshold for classification
        enable_calibration: Whether to use confidence calibration
        calibration_method: Calibration method ('isotonic', 'sigmoid')
        enable_multi_label: Whether to enable multi-label classification
        multi_label_threshold: Threshold for including labels in multi-label output
        max_labels: Maximum number of labels to return in multi-label mode
        domain: Domain context ('general', 'real_estate')
    """

    min_confidence: float = 0.6
    enable_calibration: bool = True
    calibration_method: str = "isotonic"  # 'isotonic' or 'sigmoid'
    enable_multi_label: bool = True
    multi_label_threshold: float = 0.3
    max_labels: int = 3
    domain: str = "real_estate"


class ConfidenceCalibrator:
    """Confidence calibration using temperature scaling and Platt scaling.

    Provides well-calibrated confidence scores that reflect true
    probabilities of correctness.
    """

    def __init__(self, method: str = "isotonic"):
        """Initialize calibrator.

        Args:
            method: Calibration method ('isotonic', 'sigmoid', 'temperature')
        """
        self.method = method
        self.temperature = 1.0
        self.platt_a = 1.0
        self.platt_b = 0.0
        self.is_fitted = False
        self._calibrated_classifier: Optional[CalibratedClassifierCV] = None

    def fit(self, logits: np.ndarray, labels: np.ndarray) -> "ConfidenceCalibrator":
        """Fit calibration parameters on validation data.

        Args:
            logits: Raw model outputs (before softmax)
            labels: True binary labels (1 for correct, 0 for incorrect)

        Returns:
            Self for method chaining
        """
        if len(logits) == 0:
            return self

        # Convert logits to probabilities
        probs = self._softmax(logits / self.temperature)

        if self.method == "temperature":
            self.temperature = self._fit_temperature_scaling(logits, labels)
        elif self.method == "sigmoid":
            self.platt_a, self.platt_b = self._fit_platt_scaling(probs, labels)
        elif self.method == "isotonic":
            # Use sklearn's isotonic regression
            from sklearn.isotonic import IsotonicRegression

            self._iso_regressor = IsotonicRegression(out_of_bounds="clip")
            self._iso_regressor.fit(probs, labels)

        self.is_fitted = True
        return self

    def calibrate(self, logits: np.ndarray) -> np.ndarray:
        """Apply calibration to logits.

        Args:
            logits: Raw model outputs

        Returns:
            Calibrated probabilities
        """
        if not self.is_fitted:
            return self._softmax(logits)

        probs = self._softmax(logits / self.temperature)

        if self.method == "sigmoid":
            return 1 / (1 + np.exp(-(self.platt_a * probs + self.platt_b)))
        elif self.method == "isotonic" and hasattr(self, "_iso_regressor"):
            return self._iso_regressor.predict(probs)

        return probs

    def _softmax(self, x: np.ndarray) -> np.ndarray:
        """Compute softmax values."""
        exp_x = np.exp(x - np.max(x, axis=-1, keepdims=True))
        return exp_x / np.sum(exp_x, axis=-1, keepdims=True)

    def _fit_temperature_scaling(self, logits: np.ndarray, labels: np.ndarray) -> float:
        """Fit temperature parameter for temperature scaling."""
        from scipy.optimize import minimize_scalar

        def nll_loss(t: float) -> float:
            scaled_logits = logits / t
            probs = self._softmax(scaled_logits)
            # Negative log-likelihood
            return -np.mean(np.log(probs[labels.astype(bool)] + 1e-10))

        result = minimize_scalar(nll_loss, bounds=(0.1, 10.0), method="bounded")
        return result.x

    def _fit_platt_scaling(self, probs: np.ndarray, labels: np.ndarray) -> Tuple[float, float]:
        """Fit Platt scaling parameters."""

        # Reshape for sklearn
        X = probs.reshape(-1, 1)
        clf = LogisticRegression(C=1e10, solver="lbfgs")
        clf.fit(X, labels)

        return clf.coef_[0][0], clf.intercept_[0]


class IntentClassifierV2:
    """Advanced intent classifier with multi-label support and calibration.

    Provides fine-tuned classification for domain-specific intents with
    confidence calibration and multi-label capabilities.

    Example:
        ```python
        classifier = IntentClassifierV2(domain="real_estate")

        # Single-label classification
        result = classifier.classify("Show me houses in Rancho Cucamonga")
        print(result.primary_intent)  # IntentType.PROPERTY_SEARCH
        print(result.confidence)  # 0.92 (calibrated)

        # Multi-label classification
        multi_result = classifier.classify_multi_label(
            "I'm looking to buy a 3-bedroom house in Etiwanda school district"
        )
        print(multi_result.intents)
        # [IntentType.BUYING_INTENT, IntentType.PROPERTY_SEARCH, IntentType.SCHOOL_DISTRICT_QUERY]
        ```
    """

    def __init__(self, config: Optional[ClassifierConfig] = None):
        """Initialize intent classifier.

        Args:
            config: Classification configuration
        """
        self.config = config or ClassifierConfig()
        self.calibrator = ConfidenceCalibrator(self.config.calibration_method)
        self._intent_patterns = self._build_intent_patterns()
        self._intent_keywords = self._build_intent_keywords()
        self._label_binarizer = MultiLabelBinarizer()
        self._label_binarizer.fit([[i.value for i in IntentType]])

        # Initialize mock model (in production, load fine-tuned model)
        self._init_mock_model()

    def _init_mock_model(self) -> None:
        """Initialize mock classification model."""
        # In production, this would load a fine-tuned transformer or sklearn model
        self._model = None
        self._feature_weights: Dict[IntentType, Dict[str, float]] = defaultdict(lambda: defaultdict(float))
        self._build_mock_weights()

    def _build_mock_weights(self) -> None:
        """Build mock feature weights for demonstration."""
        # Property search weights
        self._feature_weights[IntentType.PROPERTY_SEARCH] = {
            "house": 0.8,
            "home": 0.8,
            "property": 0.9,
            "listing": 0.7,
            "show": 0.6,
            "find": 0.6,
            "search": 0.7,
            "looking": 0.7,
            "bedroom": 0.8,
            "bathroom": 0.8,
            "sqft": 0.7,
        }

        # Buying intent weights
        self._feature_weights[IntentType.BUYING_INTENT] = {
            "buy": 0.9,
            "purchase": 0.9,
            "buying": 0.9,
            "offer": 0.7,
            "down payment": 0.8,
            "mortgage": 0.7,
            "pre-approved": 0.8,
            "first time": 0.6,
        }

        # Selling intent weights
        self._feature_weights[IntentType.SELLING_INTENT] = {
            "sell": 0.9,
            "selling": 0.9,
            "list": 0.8,
            "listing": 0.8,
            "market value": 0.8,
            "worth": 0.7,
            "appraisal": 0.7,
            "cma": 0.9,
        }

        # Price inquiry weights
        self._feature_weights[IntentType.PRICE_INQUIRY] = {
            "price": 0.9,
            "cost": 0.8,
            "how much": 0.9,
            "afford": 0.7,
            "budget": 0.8,
            "expensive": 0.6,
            "cheap": 0.6,
            "under": 0.7,
            "over": 0.7,
            "$": 0.7,
            "million": 0.7,
            "thousand": 0.6,
        }

        # Location query weights
        self._feature_weights[IntentType.LOCATION_QUERY] = {
            "rancho cucamonga": 0.9,
            "victoria": 0.8,
            "haven": 0.8,
            "etiwanda": 0.8,
            "terra vista": 0.8,
            "central park": 0.8,
            "ontario": 0.7,
            "fontana": 0.7,
            "upland": 0.7,
            "near": 0.6,
            "area": 0.6,
            "neighborhood": 0.7,
            "zip": 0.7,
        }

        # School district weights
        self._feature_weights[IntentType.SCHOOL_DISTRICT_QUERY] = {
            "school": 0.9,
            "district": 0.8,
            "education": 0.7,
            "elementary": 0.8,
            "high school": 0.8,
            "rating": 0.6,
            "test scores": 0.7,
        }

        # Market analysis weights
        self._feature_weights[IntentType.MARKET_ANALYSIS] = {
            "market": 0.9,
            "trend": 0.8,
            "appreciation": 0.8,
            "forecast": 0.7,
            "analysis": 0.7,
            "stats": 0.6,
            "statistics": 0.6,
            "average": 0.6,
            "median": 0.6,
        }

        # Investment research weights
        self._feature_weights[IntentType.INVESTMENT_RESEARCH] = {
            "invest": 0.9,
            "investment": 0.9,
            "rental": 0.8,
            "cash flow": 0.8,
            "cap rate": 0.9,
            "roi": 0.8,
            "return": 0.7,
            "flip": 0.8,
            "property management": 0.7,
        }

        # Financing question weights
        self._feature_weights[IntentType.FINANCING_QUESTION] = {
            "loan": 0.9,
            "mortgage": 0.9,
            "rate": 0.8,
            "interest": 0.8,
            "down payment": 0.8,
            "finance": 0.8,
            "lender": 0.7,
            "pre-approval": 0.8,
            "credit": 0.6,
            "debt": 0.6,
        }

        # Showing request weights
        self._feature_weights[IntentType.SHOWING_REQUEST] = {
            "tour": 0.9,
            "showing": 0.9,
            "view": 0.8,
            "see": 0.7,
            "visit": 0.8,
            "open house": 0.9,
            "schedule": 0.7,
            "appointment": 0.7,
            "available": 0.6,
        }

        # Agent contact weights
        self._feature_weights[IntentType.AGENT_CONTACT] = {
            "contact": 0.8,
            "agent": 0.9,
            "realtor": 0.9,
            "reach": 0.7,
            "call": 0.7,
            "email": 0.7,
            "talk": 0.6,
            "speak": 0.6,
            "jorge": 0.8,
        }

    def _build_intent_patterns(self) -> Dict[IntentType, List[re.Pattern]]:
        """Build regex patterns for intent detection."""
        patterns = {
            IntentType.PROPERTY_SEARCH: [
                re.compile(r"\b(show|find|search|look)\s+(me\s+)?(for\s+)?(a\s+)?(house|home|property|listing)", re.I),
                re.compile(r"\b(\d+)\s*(bed|bedroom)", re.I),
                re.compile(r"\b(\d+)\s*(bath|bathroom)", re.I),
            ],
            IntentType.BUYING_INTENT: [
                re.compile(r"\b(want\s+to\s+buy|looking\s+to\s+buy|interested\s+in\s+buying)", re.I),
                re.compile(r"\b(first\s+time\s+buyer|home\s+buyer)\b", re.I),
                re.compile(r"\b(pre[-\s]?approved|pre[-\s]?approval)\b", re.I),
            ],
            IntentType.SELLING_INTENT: [
                re.compile(r"\b(want\s+to\s+sell|thinking\s+about\s+selling)\b", re.I),
                re.compile(r"\bwhat\s+(is\s+)?my\s+(house|home)\s+worth\b", re.I),
                re.compile(r"\bmarket\s+value\b", re.I),
            ],
            IntentType.PRICE_INQUIRY: [
                re.compile(r"\bhow\s+much\s+(is|does|would)\b", re.I),
                re.compile(r"\bprice\s+range\b", re.I),
                re.compile(r"\$[\d,]+(\s*[KkMm])?", re.I),
            ],
            IntentType.LOCATION_QUERY: [
                re.compile(r"\b(in|near|around)\s+([A-Za-z\s]+)\b", re.I),
                re.compile(r"\b(zip\s*code?\s*\d{5})\b", re.I),
            ],
            IntentType.SCHOOL_DISTRICT_QUERY: [
                re.compile(r"\b(school\s+district|schools)\b", re.I),
                re.compile(r"\b(etiwanda|chaffey|alta\s+loma)\s+schools\b", re.I),
            ],
            IntentType.MARKET_ANALYSIS: [
                re.compile(r"\bmarket\s+(trend|analysis|report|condition)\b", re.I),
                re.compile(r"\b(how\s+is\s+the\s+market|market\s+update)\b", re.I),
            ],
            IntentType.INVESTMENT_RESEARCH: [
                re.compile(r"\b(investment\s+property|rental\s+property)\b", re.I),
                re.compile(r"\b(cap\s+rate|cash\s+flow|roi)\b", re.I),
            ],
            IntentType.FINANCING_QUESTION: [
                re.compile(r"\b(mortgage\s+rate|interest\s+rate)\b", re.I),
                re.compile(r"\b(down\s+payment|monthly\s+payment)\b", re.I),
            ],
            IntentType.SHOWING_REQUEST: [
                re.compile(r"\b(schedule\s+a\s+tour|book\s+a\s+showing)\b", re.I),
                re.compile(r"\b(when\s+can\s+I\s+see|view\s+this\s+property)\b", re.I),
            ],
            IntentType.AGENT_CONTACT: [
                re.compile(r"\b(contact\s+an?\s+agent|speak\s+to|talk\s+to)\b", re.I),
                re.compile(r"\b(reach\s+out|get\s+in\s+touch)\b", re.I),
            ],
        }
        return patterns

    def _build_intent_keywords(self) -> Dict[IntentType, Set[str]]:
        """Build keyword sets for intent detection."""
        return {
            IntentType.INFORMATIONAL: {
                "what",
                "how",
                "why",
                "when",
                "where",
                "who",
                "which",
                "information",
                "details",
                "about",
                "tell me",
            },
            IntentType.NAVIGATIONAL: {"go to", "find", "locate", "where is", "address", "directions"},
            IntentType.TRANSACTIONAL: {"buy", "sell", "purchase", "order", "book", "schedule", "contact"},
            IntentType.COMPARISON: {"compare", "versus", "vs", "difference", "better", "best", "or"},
            IntentType.EXPLORATORY: {"explore", "discover", "browse", "look around", "options", "available"},
        }

    def _extract_features(self, query: str) -> Dict[str, Any]:
        """Extract features from query for classification.

        Args:
            query: Input query string

        Returns:
            Dictionary of extracted features
        """
        query_lower = query.lower().strip()
        words = query_lower.split()

        features = {
            "length": len(query),
            "word_count": len(words),
            "has_question_mark": "?" in query,
            "has_price": bool(re.search(r"\$[\d,]+|\d+\s*[KkMm]\b|\d+\s*(thousand|million)", query)),
            "has_number": bool(re.search(r"\d+", query)),
            "pattern_matches": {},
            "keyword_matches": {},
            "weighted_scores": {},
        }

        # Pattern-based features
        for intent, patterns in self._intent_patterns.items():
            matches = sum(1 for pattern in patterns if pattern.search(query))
            features["pattern_matches"][intent.value] = matches

        # Keyword-based features
        query_words = set(words)
        for intent, keywords in self._intent_keywords.items():
            matches = len(query_words.intersection(keywords))
            features["keyword_matches"][intent.value] = matches

        # Weighted feature scoring
        for intent in IntentType:
            score = 0.0
            weights = self._feature_weights.get(intent, {})
            for word in words:
                score += weights.get(word, 0.0)
                # Check for multi-word phrases
                for phrase in weights.keys():
                    if " " in phrase and phrase in query_lower:
                        score += weights[phrase] * 1.5  # Boost for phrases
            features["weighted_scores"][intent.value] = score

        return features

    def _calculate_intent_scores(self, features: Dict[str, Any]) -> Dict[IntentType, float]:
        """Calculate raw intent scores.

        Args:
            features: Extracted features

        Returns:
            Dictionary mapping intents to scores
        """
        scores = {intent: 0.0 for intent in IntentType}

        # Pattern-based scoring
        pattern_matches = features["pattern_matches"]
        max_pattern = max(pattern_matches.values()) if pattern_matches else 1
        if max_pattern == 0:
            max_pattern = 1

        for intent in IntentType:
            if intent.value in pattern_matches:
                scores[intent] += pattern_matches[intent.value] / max_pattern * 0.4

        # Weighted feature scoring
        weighted_scores = features["weighted_scores"]
        max_weighted = max(weighted_scores.values()) if weighted_scores else 1
        if max_weighted == 0:
            max_weighted = 1

        for intent in IntentType:
            if intent.value in weighted_scores:
                scores[intent] += weighted_scores[intent.value] / max_weighted * 0.6

        # Boost for price mentions in price inquiry
        if features["has_price"]:
            scores[IntentType.PRICE_INQUIRY] += 0.3
            scores[IntentType.BUYING_INTENT] += 0.1

        return scores

    def classify(self, query: str) -> IntentClassificationResult:
        """Classify query intent with single-label output.

        Args:
            query: Input query string

        Returns:
            Classification result with calibrated confidence

        Raises:
            RetrievalError: If classification fails
        """
        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")

        try:
            features = self._extract_features(query)
            scores = self._calculate_intent_scores(features)

            # Get primary intent
            primary_intent = max(scores.keys(), key=lambda k: scores[k])
            raw_confidence = scores[primary_intent]

            # Normalize confidence
            max_score = max(scores.values()) if scores else 1
            if max_score > 0:
                raw_confidence = min(scores[primary_intent] / max_score, 1.0)

            # Apply calibration if enabled
            if self.config.enable_calibration and self.calibrator.is_fitted:
                # Simulate logits from scores
                logits = np.array([scores[i] for i in IntentType])
                calibrated_probs = self.calibrator.calibrate(logits)
                intent_idx = list(IntentType).index(primary_intent)
                confidence = float(calibrated_probs[intent_idx])
            else:
                confidence = raw_confidence

            # Get alternative intents
            sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)[1:4]  # Top 3 alternatives
            alternative_intents = [
                (intent, min(score / max_score if max_score > 0 else 0, 1.0)) for intent, score in sorted_intents
            ]

            # Apply minimum confidence threshold
            if confidence < self.config.min_confidence:
                primary_intent = IntentType.INFORMATIONAL
                confidence = max(confidence, self.config.min_confidence)

            return IntentClassificationResult(
                primary_intent=primary_intent,
                confidence=confidence,
                raw_confidence=raw_confidence,
                features=features,
                alternative_intents=alternative_intents,
            )

        except Exception as e:
            raise RetrievalError(f"Intent classification failed: {str(e)}") from e

    def classify_multi_label(self, query: str) -> MultiLabelResult:
        """Classify query with multi-label output.

        Args:
            query: Input query string

        Returns:
            Multi-label classification result
        """
        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")

        features = self._extract_features(query)
        scores = self._calculate_intent_scores(features)

        # Normalize scores to probabilities
        total_score = sum(scores.values())
        if total_score > 0:
            probabilities = {k: v / total_score for k, v in scores.items()}
        else:
            probabilities = {k: 1.0 / len(scores) for k in scores}

        # Apply calibration
        if self.config.enable_calibration and self.calibrator.is_fitted:
            logits = np.array([scores[i] for i in IntentType])
            calibrated = self.calibrator.calibrate(logits)
            probabilities = {intent: float(calibrated[i]) for i, intent in enumerate(IntentType)}

        # Select intents above threshold
        selected_intents = [
            intent for intent, prob in probabilities.items() if prob >= self.config.multi_label_threshold
        ]

        # Limit to max_labels
        if len(selected_intents) > self.config.max_labels:
            selected_intents = sorted(selected_intents, key=lambda i: probabilities[i], reverse=True)[
                : self.config.max_labels
            ]

        # Ensure at least one intent
        if not selected_intents:
            primary = max(probabilities.keys(), key=lambda k: probabilities[k])
            selected_intents = [primary]

        # Calculate coverage score
        coverage_score = sum(probabilities[i] for i in selected_intents)

        # Calculate label correlations
        correlations = {}
        for i, intent1 in enumerate(selected_intents):
            for intent2 in selected_intents[i + 1 :]:
                # Simple correlation based on co-occurrence patterns
                correlation = self._calculate_intent_correlation(intent1, intent2)
                correlations[(intent1, intent2)] = correlation

        primary_intent = max(selected_intents, key=lambda i: probabilities[i])

        return MultiLabelResult(
            intents=selected_intents,
            primary_intent=primary_intent,
            confidence_scores={i: probabilities[i] for i in selected_intents},
            coverage_score=min(coverage_score, 1.0),
            label_correlations=correlations,
        )

    def _calculate_intent_correlation(self, intent1: IntentType, intent2: IntentType) -> float:
        """Calculate correlation between two intents.

        Args:
            intent1: First intent
            intent2: Second intent

        Returns:
            Correlation score (0.0-1.0)
        """
        # Define known correlations
        correlations = {
            (IntentType.BUYING_INTENT, IntentType.PROPERTY_SEARCH): 0.85,
            (IntentType.BUYING_INTENT, IntentType.FINANCING_QUESTION): 0.70,
            (IntentType.BUYING_INTENT, IntentType.SCHOOL_DISTRICT_QUERY): 0.60,
            (IntentType.SELLING_INTENT, IntentType.CMA_REQUEST): 0.90,
            (IntentType.SELLING_INTENT, IntentType.MARKET_ANALYSIS): 0.75,
            (IntentType.PROPERTY_SEARCH, IntentType.LOCATION_QUERY): 0.80,
            (IntentType.PROPERTY_SEARCH, IntentType.PRICE_INQUIRY): 0.75,
            (IntentType.INVESTMENT_RESEARCH, IntentType.MARKET_ANALYSIS): 0.70,
            (IntentType.INVESTMENT_RESEARCH, IntentType.FINANCING_QUESTION): 0.65,
            (IntentType.SHOWING_REQUEST, IntentType.PROPERTY_SEARCH): 0.90,
            (IntentType.SHOWING_REQUEST, IntentType.BUYING_INTENT): 0.85,
        }

        key = (intent1, intent2)
        reverse_key = (intent2, intent1)

        if key in correlations:
            return correlations[key]
        elif reverse_key in correlations:
            return correlations[reverse_key]
        else:
            # Default correlation based on semantic similarity
            return 0.3

    def calibrate_confidence(self, validation_queries: List[str], true_labels: List[int]) -> "IntentClassifierV2":
        """Calibrate confidence scores using validation data.

        Args:
            validation_queries: List of validation queries
            true_labels: Binary labels (1 if classification was correct, 0 otherwise)

        Returns:
            Self for method chaining
        """
        if len(validation_queries) != len(true_labels):
            raise ValueError("Queries and labels must have same length")

        # Extract scores for calibration
        logits_list = []
        for query in validation_queries:
            features = self._extract_features(query)
            scores = self._calculate_intent_scores(features)
            logits = np.array([scores[i] for i in IntentType])
            logits_list.append(logits)

        logits_array = np.array(logits_list)
        labels_array = np.array(true_labels)

        self.calibrator.fit(logits_array, labels_array)
        return self

    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics.

        Returns:
            Dictionary with classifier statistics
        """
        return {
            "config": {
                "min_confidence": self.config.min_confidence,
                "enable_calibration": self.config.enable_calibration,
                "calibration_method": self.config.calibration_method,
                "enable_multi_label": self.config.enable_multi_label,
                "multi_label_threshold": self.config.multi_label_threshold,
                "max_labels": self.config.max_labels,
                "domain": self.config.domain,
            },
            "calibrator_fitted": self.calibrator.is_fitted,
            "intent_patterns": {k.value: len(v) for k, v in self._intent_patterns.items()},
            "num_intents": len(IntentType),
        }
