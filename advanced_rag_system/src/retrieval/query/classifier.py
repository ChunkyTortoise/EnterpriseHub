"""Query classification for intelligent retrieval routing.

This module provides query classification capabilities to route different
types of queries to optimal retrieval strategies and enhance search performance.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from src.core.exceptions import RetrievalError


class QueryType(Enum):
    """Enumeration of query types for classification.

    Each type corresponds to different retrieval strategies:
    - FACTUAL: Direct fact lookups, best with exact/sparse retrieval
    - CONCEPTUAL: Broad concept exploration, benefits from dense retrieval
    - PROCEDURAL: How-to questions, benefits from structured retrieval
    - COMPARATIVE: Comparison questions, benefits from multi-query approach
    - EXPLORATORY: Open-ended exploration, benefits from query expansion
    - TECHNICAL: Technical/domain-specific queries, benefits from specialized routing
    """

    FACTUAL = "factual"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    COMPARATIVE = "comparative"
    EXPLORATORY = "exploratory"
    TECHNICAL = "technical"


@dataclass
class ClassificationResult:
    """Result of query classification.

    Attributes:
        query_type: Predicted query type
        confidence: Confidence score (0.0-1.0)
        features: Dictionary of extracted features
        recommendations: Recommended retrieval strategies
    """

    query_type: QueryType
    confidence: float
    features: Dict[str, Any]
    recommendations: Dict[str, float]


@dataclass
class ClassifierConfig:
    """Configuration for query classification.

    Attributes:
        min_confidence: Minimum confidence threshold for classification
        use_patterns: Whether to use regex pattern matching
        use_keywords: Whether to use keyword-based classification
        use_length: Whether to consider query length in classification
        pattern_weight: Weight for pattern-based features
        keyword_weight: Weight for keyword-based features
        length_weight: Weight for length-based features
        custom_patterns: Custom patterns for domain-specific classification
    """

    min_confidence: float = 0.6
    use_patterns: bool = True
    use_keywords: bool = True
    use_length: bool = True
    pattern_weight: float = 0.4
    keyword_weight: float = 0.4
    length_weight: float = 0.2
    custom_patterns: Optional[Dict[str, List[str]]] = None


class QueryClassifier:
    """Rule-based query classifier for retrieval routing.

    Classifies queries into different types to enable intelligent routing
    to optimal retrieval strategies. Uses pattern matching, keyword analysis,
    and structural features.

    Example:
        ```python
        classifier = QueryClassifier()

        # Classify a factual query
        result = classifier.classify("What is the capital of France?")
        # Result: QueryType.FACTUAL with high confidence

        # Classify a conceptual query
        result = classifier.classify("How does machine learning work?")
        # Result: QueryType.CONCEPTUAL with recommendations for dense retrieval
        ```
    """

    def __init__(self, config: Optional[ClassifierConfig] = None):
        """Initialize query classifier.

        Args:
            config: Classification configuration
        """
        self.config = config or ClassifierConfig()
        self._patterns = self._build_patterns()
        self._keywords = self._build_keywords()

    def _build_patterns(self) -> Dict[QueryType, List[re.Pattern]]:
        """Build regex patterns for each query type.

        Returns:
            Dictionary mapping query types to compiled regex patterns
        """
        patterns = {
            QueryType.FACTUAL: [
                re.compile(r"\b(what|who|when|where|which)\s+is\b", re.IGNORECASE),
                re.compile(r"\bdefin(e|ition)\b", re.IGNORECASE),
                re.compile(r"\bmean(ing)?\s+of\b", re.IGNORECASE),
                re.compile(r"\b(name|list)\s+of\b", re.IGNORECASE),
                re.compile(r"\b(how many|how much)\b", re.IGNORECASE),
                re.compile(r"^\w+\s+is\s+\w+$", re.IGNORECASE),  # Simple "X is Y" patterns
            ],
            QueryType.CONCEPTUAL: [
                re.compile(r"\b(explain|understand|concept|principle|theory)\b", re.IGNORECASE),
                re.compile(r"\b(how does|why does)\b", re.IGNORECASE),
                re.compile(r"\bwhat are the.*(benefit|advantage|principle|concept)\b", re.IGNORECASE),
                re.compile(r"\b(overview|introduction|basics)\b", re.IGNORECASE),
                re.compile(r"\b(understand|comprehend|grasp)\b", re.IGNORECASE),
            ],
            QueryType.PROCEDURAL: [
                re.compile(r"\b(how to|how can I|how do I)\b", re.IGNORECASE),
                re.compile(r"\b(step|guide|tutorial|instruction)\b", re.IGNORECASE),
                re.compile(r"\b(implement|create|build|make|setup|install)\b", re.IGNORECASE),
                re.compile(r"\b(process|procedure|method|approach)\b", re.IGNORECASE),
                re.compile(r"\bwalk me through\b", re.IGNORECASE),
            ],
            QueryType.COMPARATIVE: [
                re.compile(r"\b(vs|versus|compare|comparison|difference|better)\b", re.IGNORECASE),
                re.compile(r"\b(between|among)\b.*\band\b", re.IGNORECASE),
                re.compile(r"\b(which is|what is the difference)\b", re.IGNORECASE),
                re.compile(r"\b(pros and cons|advantages and disadvantages)\b", re.IGNORECASE),
                re.compile(r"\b(or|either)\b.*\bor\b", re.IGNORECASE),
            ],
            QueryType.EXPLORATORY: [
                re.compile(r"\b(explore|discover|find out|learn about)\b", re.IGNORECASE),
                re.compile(r"\b(anything|something|everything)\s+about\b", re.IGNORECASE),
                re.compile(r"\b(research|investigate|study)\b", re.IGNORECASE),
                re.compile(r"\b(what can|what should|what might)\b", re.IGNORECASE),
                re.compile(r"\b(general|broad|overall)\b.*\b(information|overview)\b", re.IGNORECASE),
            ],
            QueryType.TECHNICAL: [
                re.compile(r"\b(api|algorithm|function|method|class|library)\b", re.IGNORECASE),
                re.compile(r"\b(error|exception|bug|debug|troubleshoot)\b", re.IGNORECASE),
                re.compile(r"\b(code|syntax|parameter|argument|variable)\b", re.IGNORECASE),
                re.compile(r"\b(configuration|setup|deployment|optimization)\b", re.IGNORECASE),
                re.compile(r"\b(framework|tool|package|module|dependency)\b", re.IGNORECASE),
            ],
        }

        # Add custom patterns if provided
        if self.config.custom_patterns:
            for query_type, pattern_strings in self.config.custom_patterns.items():
                try:
                    query_type_enum = QueryType(query_type)
                    custom_patterns = [re.compile(p, re.IGNORECASE) for p in pattern_strings]
                    if query_type_enum in patterns:
                        patterns[query_type_enum].extend(custom_patterns)
                    else:
                        patterns[query_type_enum] = custom_patterns
                except (ValueError, re.error):
                    # Invalid query type or pattern, skip
                    continue

        return patterns

    def _build_keywords(self) -> Dict[QueryType, Set[str]]:
        """Build keyword sets for each query type.

        Returns:
            Dictionary mapping query types to keyword sets
        """
        return {
            QueryType.FACTUAL: {
                "definition",
                "meaning",
                "is",
                "called",
                "named",
                "refers",
                "stands",
                "capital",
                "population",
                "number",
                "count",
                "amount",
                "size",
                "weight",
                "date",
                "year",
                "time",
                "location",
                "place",
                "country",
                "city",
            },
            QueryType.CONCEPTUAL: {
                "concept",
                "principle",
                "theory",
                "idea",
                "notion",
                "understanding",
                "explanation",
                "reasoning",
                "logic",
                "rationale",
                "basis",
                "foundation",
                "philosophy",
                "approach",
                "methodology",
                "framework",
                "paradigm",
            },
            QueryType.PROCEDURAL: {
                "how",
                "steps",
                "procedure",
                "process",
                "method",
                "way",
                "guide",
                "tutorial",
                "instruction",
                "manual",
                "recipe",
                "workflow",
                "protocol",
                "create",
                "build",
                "make",
                "implement",
                "setup",
                "install",
                "configure",
            },
            QueryType.COMPARATIVE: {
                "compare",
                "comparison",
                "versus",
                "difference",
                "similar",
                "different",
                "better",
                "worse",
                "best",
                "worst",
                "pros",
                "cons",
                "advantages",
                "disadvantages",
                "benefits",
                "drawbacks",
                "trade-offs",
            },
            QueryType.EXPLORATORY: {
                "explore",
                "discover",
                "investigate",
                "research",
                "study",
                "examine",
                "analyze",
                "survey",
                "overview",
                "general",
                "broad",
                "comprehensive",
                "anything",
                "everything",
                "all",
                "various",
                "multiple",
                "diverse",
            },
            QueryType.TECHNICAL: {
                "code",
                "programming",
                "software",
                "development",
                "api",
                "function",
                "method",
                "algorithm",
                "implementation",
                "syntax",
                "error",
                "debug",
                "optimization",
                "performance",
                "configuration",
                "deployment",
                "testing",
            },
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
            "starts_with_wh": words[0] in {"what", "who", "when", "where", "why", "which", "how"} if words else False,
            "pattern_matches": {},
            "keyword_matches": {},
        }

        # Pattern-based features
        if self.config.use_patterns:
            for query_type, patterns in self._patterns.items():
                matches = sum(1 for pattern in patterns if pattern.search(query))
                features["pattern_matches"][query_type.value] = matches

        # Keyword-based features
        if self.config.use_keywords:
            query_words = set(words)
            for query_type, keywords in self._keywords.items():
                matches = len(query_words.intersection(keywords))
                features["keyword_matches"][query_type.value] = matches

        return features

    def _calculate_scores(self, features: Dict[str, Any]) -> Dict[QueryType, float]:
        """Calculate classification scores for each query type.

        Args:
            features: Extracted features

        Returns:
            Dictionary mapping query types to scores
        """
        scores = {query_type: 0.0 for query_type in QueryType}

        # Pattern-based scoring
        if self.config.use_patterns:
            pattern_matches = features["pattern_matches"]
            max_pattern_matches = max(pattern_matches.values()) if pattern_matches.values() else 1
            if max_pattern_matches == 0:
                max_pattern_matches = 1

            for query_type in QueryType:
                pattern_score = pattern_matches.get(query_type.value, 0) / max_pattern_matches
                scores[query_type] += pattern_score * self.config.pattern_weight

        # Keyword-based scoring
        if self.config.use_keywords:
            keyword_matches = features["keyword_matches"]
            max_keyword_matches = max(keyword_matches.values()) if keyword_matches.values() else 1
            if max_keyword_matches == 0:
                max_keyword_matches = 1

            for query_type in QueryType:
                keyword_score = keyword_matches.get(query_type.value, 0) / max_keyword_matches
                scores[query_type] += keyword_score * self.config.keyword_weight

        # Length-based scoring
        if self.config.use_length:
            word_count = features["word_count"]
            # Heuristic: short queries tend to be factual, longer ones conceptual/exploratory
            if word_count <= 3:
                scores[QueryType.FACTUAL] += 0.3 * self.config.length_weight
            elif word_count <= 6:
                scores[QueryType.PROCEDURAL] += 0.2 * self.config.length_weight
                scores[QueryType.COMPARATIVE] += 0.2 * self.config.length_weight
            else:
                scores[QueryType.CONCEPTUAL] += 0.3 * self.config.length_weight
                scores[QueryType.EXPLORATORY] += 0.3 * self.config.length_weight

        # Question mark bonus for factual queries
        if features["has_question_mark"]:
            scores[QueryType.FACTUAL] += 0.1
            scores[QueryType.PROCEDURAL] += 0.05

        # WH-word patterns
        if features["starts_with_wh"]:
            scores[QueryType.FACTUAL] += 0.2
            scores[QueryType.CONCEPTUAL] += 0.1

        return scores

    def _get_recommendations(self, query_type: QueryType, confidence: float) -> Dict[str, float]:
        """Get retrieval strategy recommendations based on query type.

        Args:
            query_type: Classified query type
            confidence: Classification confidence

        Returns:
            Dictionary of recommended strategies with weights
        """
        recommendations = {
            "dense_retrieval_weight": 0.5,
            "sparse_retrieval_weight": 0.5,
            "query_expansion": 0.0,
            "hyde_generation": 0.0,
            "multi_query": 0.0,
            "reranking": 0.5,
        }

        # Adjust based on query type
        if query_type == QueryType.FACTUAL:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.3,
                    "sparse_retrieval_weight": 0.7,  # Better for exact matches
                    "query_expansion": 0.2,
                    "hyde_generation": 0.1,
                    "multi_query": 0.2,
                }
            )

        elif query_type == QueryType.CONCEPTUAL:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.7,  # Better for semantic understanding
                    "sparse_retrieval_weight": 0.3,
                    "query_expansion": 0.6,
                    "hyde_generation": 0.8,  # Very beneficial for concepts
                    "multi_query": 0.4,
                }
            )

        elif query_type == QueryType.PROCEDURAL:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.6,
                    "sparse_retrieval_weight": 0.4,
                    "query_expansion": 0.7,  # Expand with procedural terms
                    "hyde_generation": 0.6,
                    "multi_query": 0.5,
                    "reranking": 0.7,  # Important for step ordering
                }
            )

        elif query_type == QueryType.COMPARATIVE:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.6,
                    "sparse_retrieval_weight": 0.4,
                    "query_expansion": 0.8,  # Expand to find all comparison points
                    "hyde_generation": 0.5,
                    "multi_query": 0.8,  # Generate queries for each item
                    "reranking": 0.8,  # Critical for comparison relevance
                }
            )

        elif query_type == QueryType.EXPLORATORY:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.7,
                    "sparse_retrieval_weight": 0.3,
                    "query_expansion": 0.9,  # Maximum expansion for exploration
                    "hyde_generation": 0.7,
                    "multi_query": 0.9,  # Multiple perspectives
                    "reranking": 0.6,
                }
            )

        elif query_type == QueryType.TECHNICAL:
            recommendations.update(
                {
                    "dense_retrieval_weight": 0.4,
                    "sparse_retrieval_weight": 0.6,  # Better for technical terms
                    "query_expansion": 0.5,
                    "hyde_generation": 0.4,
                    "multi_query": 0.3,
                    "reranking": 0.8,  # Important for technical accuracy
                }
            )

        # Scale by confidence
        for key in recommendations:
            if key != "dense_retrieval_weight" and key != "sparse_retrieval_weight":
                recommendations[key] *= confidence

        return recommendations

    def classify(self, query: str) -> ClassificationResult:
        """Classify a query and provide retrieval recommendations.

        Args:
            query: Input query string

        Returns:
            Classification result with type, confidence, and recommendations

        Raises:
            RetrievalError: If classification fails
        """
        if not query or not query.strip():
            raise RetrievalError("Query cannot be empty")

        try:
            # Extract features
            features = self._extract_features(query)

            # Calculate scores
            scores = self._calculate_scores(features)

            # Find best classification
            best_type = max(scores.keys(), key=lambda k: scores[k])
            confidence = scores[best_type]

            # Normalize confidence to [0, 1]
            max_possible_score = (
                self.config.pattern_weight + self.config.keyword_weight + self.config.length_weight + 0.3
            )  # Extra bonuses
            confidence = min(confidence / max_possible_score, 1.0)

            # Use fallback if confidence too low
            if confidence < self.config.min_confidence:
                best_type = QueryType.CONCEPTUAL  # Safe default
                confidence = self.config.min_confidence

            # Get recommendations
            recommendations = self._get_recommendations(best_type, confidence)

            return ClassificationResult(
                query_type=best_type, confidence=confidence, features=features, recommendations=recommendations
            )

        except Exception as e:
            raise RetrievalError(f"Query classification failed: {str(e)}") from e

    def get_stats(self) -> Dict[str, Any]:
        """Get classifier statistics.

        Returns:
            Dictionary with classifier statistics
        """
        return {
            "config": {
                "min_confidence": self.config.min_confidence,
                "use_patterns": self.config.use_patterns,
                "use_keywords": self.config.use_keywords,
                "use_length": self.config.use_length,
                "weights": {
                    "pattern": self.config.pattern_weight,
                    "keyword": self.config.keyword_weight,
                    "length": self.config.length_weight,
                },
            },
            "patterns": {query_type.value: len(patterns) for query_type, patterns in self._patterns.items()},
            "keywords": {query_type.value: len(keywords) for query_type, keywords in self._keywords.items()},
            "query_types": [qt.value for qt in QueryType],
        }
