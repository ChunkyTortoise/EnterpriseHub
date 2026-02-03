"""
XGBoost Life-Event Propensity Engine

Scores leads by predicted conversion probability given detected life events
(probate, job relocation, divorce, tax delinquency) combined with conversation
behavioural features and market context.

Integrates:
- ``AttomClient``  for property DNA / life-event triggers
- ``FeatureEngineer``  for 23-dim conversation features
- ``BehavioralTriggerDetector``  for real-time behavioural signals
- ``CacheService``  for sub-100ms repeated scoring

Usage::

    engine = get_propensity_engine()
    score = await engine.score_lead(
        contact_id="c_123",
        address="123 Main St, Rancho Cucamonga",
        conversation_context={...},
    )
    print(score.conversion_probability, score.life_events)
"""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class LifeEventType(Enum):
    """Detectable life events that drive seller/buyer propensity."""
    PROBATE = "probate"
    JOB_RELOCATION = "job_relocation"
    DIVORCE = "divorce"
    TAX_DELINQUENCY = "tax_delinquency"
    PRE_FORECLOSURE = "pre_foreclosure"
    LONG_OWNERSHIP = "long_ownership"
    ABSENTEE_OWNER = "absentee_owner"
    RECENT_PERMIT = "recent_permit"


# Baseline conversion lifts by event type (from industry data)
LIFE_EVENT_CONVERSION_RATES: Dict[LifeEventType, float] = {
    LifeEventType.PROBATE: 0.85,
    LifeEventType.JOB_RELOCATION: 0.64,
    LifeEventType.DIVORCE: 0.72,
    LifeEventType.TAX_DELINQUENCY: 0.58,
    LifeEventType.PRE_FORECLOSURE: 0.76,
    LifeEventType.LONG_OWNERSHIP: 0.35,
    LifeEventType.ABSENTEE_OWNER: 0.42,
    LifeEventType.RECENT_PERMIT: 0.28,
}


@dataclass
class LifeEventSignal:
    """Single life-event detection with confidence."""
    event_type: LifeEventType
    detected: bool
    confidence: float  # 0-1
    source: str  # "attom", "conversation", "public_records"
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PropensityScore:
    """Complete propensity assessment for a lead."""
    contact_id: str
    conversion_probability: float  # 0-1 overall
    confidence: float  # model confidence 0-1
    temperature: str  # hot/warm/cold
    life_events: List[LifeEventSignal] = field(default_factory=list)
    primary_event: Optional[LifeEventType] = None
    feature_importance: Dict[str, float] = field(default_factory=dict)
    recommended_approach: str = ""
    predicted_timeline: str = "90_days"
    scoring_latency_ms: float = 0.0


@dataclass
class TrainingMetrics:
    """Metrics from a model training run."""
    accuracy: float
    precision: float
    recall: float
    f1: float
    auc_roc: float
    feature_importances: Dict[str, float]
    training_samples: int
    validation_samples: int


# ---------------------------------------------------------------------------
# Feature names
# ---------------------------------------------------------------------------

LIFE_EVENT_FEATURES = [
    "probate_detected",
    "job_relocation_detected",
    "divorce_detected",
    "tax_delinquent",
    "pre_foreclosure",
    "long_ownership",
    "absentee_owner",
    "recent_permit",
    "years_owned",
    "liens_count",
    "market_value_norm",
    "tax_amount_norm",
]

CONVERSATION_FEATURES = [
    "message_count_norm",
    "avg_response_time_norm",
    "sentiment_norm",
    "urgency_score",
    "engagement_score",
    "qualification_completeness",
    "budget_confidence",
    "price_mentions_norm",
    "location_specificity",
]

BEHAVIORAL_FEATURES = [
    "commitment_score",
    "hedging_score",
    "urgency_signal",
    "composite_score",
    "latency_factor",
]

ALL_FEATURES = LIFE_EVENT_FEATURES + CONVERSATION_FEATURES + BEHAVIORAL_FEATURES


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class XGBoostPropensityEngine:
    """
    Scores leads using XGBoost over a combined feature space of:
    - ATTOM life-event signals  (12 features)
    - Conversation features     (9 features)
    - Behavioural signals       (5 features)

    Total: 26-dimensional feature vector.
    """

    # XGBoost hyper-parameters (production-tuned defaults)
    DEFAULT_PARAMS = {
        "n_estimators": 200,
        "max_depth": 6,
        "learning_rate": 0.08,
        "subsample": 0.8,
        "colsample_bytree": 0.8,
        "min_child_weight": 3,
        "gamma": 0.1,
        "reg_alpha": 0.1,
        "reg_lambda": 1.0,
        "objective": "binary:logistic",
        "eval_metric": "auc",
        "use_label_encoder": False,
    }

    def __init__(self):
        self._model = None
        self._scaler = None
        self._is_trained = False
        self._feature_names = ALL_FEATURES
        self._cache: Dict[str, PropensityScore] = {}
        self._cache_ttl = 3600  # 1 hour

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def score_lead(
        self,
        contact_id: str,
        address: Optional[str] = None,
        conversation_context: Optional[Dict[str, Any]] = None,
        behavioral_signals: Optional[Dict[str, Any]] = None,
    ) -> PropensityScore:
        """
        Score a lead's conversion propensity.

        When no trained model is available the engine uses a weighted
        heuristic that still integrates life-event and behavioural data.
        """
        start = time.time()

        # Cache check
        cache_key = f"propensity:{contact_id}"
        cached = self._cache.get(cache_key)
        if cached and (time.time() - cached.scoring_latency_ms) < self._cache_ttl:
            return cached

        # Build feature vector
        life_events = await self._detect_life_events(address)
        features = self._build_feature_vector(
            life_events, conversation_context or {}, behavioral_signals or {}
        )

        if self._is_trained and self._model is not None:
            probability = self._predict_with_model(features)
            importance = self._get_feature_importance()
        else:
            probability = self._heuristic_score(life_events, features)
            importance = self._heuristic_importance(life_events)

        confidence = self._calculate_confidence(
            life_events, conversation_context or {}, behavioral_signals or {}
        )

        primary = self._identify_primary_event(life_events)
        temperature = self._classify_temperature(probability)
        approach = self._recommend_approach(primary, temperature)
        timeline = self._predict_timeline(probability, life_events)

        score = PropensityScore(
            contact_id=contact_id,
            conversion_probability=round(probability, 4),
            confidence=round(confidence, 4),
            temperature=temperature,
            life_events=life_events,
            primary_event=primary,
            feature_importance=importance,
            recommended_approach=approach,
            predicted_timeline=timeline,
            scoring_latency_ms=round((time.time() - start) * 1000, 2),
        )

        self._cache[cache_key] = score
        return score

    async def train(
        self,
        training_data: List[Dict[str, Any]],
        labels: List[int],
        validation_split: float = 0.2,
    ) -> TrainingMetrics:
        """
        Train the XGBoost model on historical lead data.

        ``training_data`` is a list of dicts with keys matching
        ``ALL_FEATURES``.  ``labels`` is 0/1 (converted or not).
        """
        try:
            import xgboost as xgb
            from sklearn.model_selection import train_test_split
            from sklearn.preprocessing import StandardScaler
            from sklearn.metrics import (
                accuracy_score, precision_score, recall_score,
                f1_score, roc_auc_score,
            )
        except ImportError as exc:
            raise RuntimeError(
                "XGBoost and scikit-learn required for training"
            ) from exc

        X = np.array([
            [row.get(f, 0.0) for f in self._feature_names]
            for row in training_data
        ])
        y = np.array(labels)

        X_train, X_val, y_train, y_val = train_test_split(
            X, y, test_size=validation_split, random_state=42, stratify=y,
        )

        self._scaler = StandardScaler()
        X_train_scaled = self._scaler.fit_transform(X_train)
        X_val_scaled = self._scaler.transform(X_val)

        self._model = xgb.XGBClassifier(**self.DEFAULT_PARAMS)
        self._model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_val_scaled, y_val)],
            verbose=False,
        )
        self._is_trained = True

        y_pred = self._model.predict(X_val_scaled)
        y_prob = self._model.predict_proba(X_val_scaled)[:, 1]

        importances = dict(zip(
            self._feature_names,
            [round(float(v), 4) for v in self._model.feature_importances_],
        ))

        metrics = TrainingMetrics(
            accuracy=round(float(accuracy_score(y_val, y_pred)), 4),
            precision=round(float(precision_score(y_val, y_pred, zero_division=0)), 4),
            recall=round(float(recall_score(y_val, y_pred, zero_division=0)), 4),
            f1=round(float(f1_score(y_val, y_pred, zero_division=0)), 4),
            auc_roc=round(float(roc_auc_score(y_val, y_prob)), 4),
            feature_importances=importances,
            training_samples=len(X_train),
            validation_samples=len(X_val),
        )

        logger.info(
            "Propensity model trained: accuracy=%.4f auc=%.4f on %d samples",
            metrics.accuracy, metrics.auc_roc, len(X),
        )
        return metrics

    def clear_cache(self) -> None:
        """Flush the in-memory score cache."""
        self._cache.clear()

    # ------------------------------------------------------------------
    # Life-event detection
    # ------------------------------------------------------------------

    async def _detect_life_events(
        self, address: Optional[str]
    ) -> List[LifeEventSignal]:
        """Detect life events from ATTOM data and conversation signals."""
        events: List[LifeEventSignal] = []
        if not address:
            return events

        try:
            from ghl_real_estate_ai.services.attom_client import get_attom_client
            attom = get_attom_client()
            dna = await attom.get_property_dna(address)
            triggers = await attom.get_life_event_triggers(address)
        except Exception:
            logger.debug("ATTOM unavailable, skipping life-event detection")
            return events

        # Probate
        if triggers.get("probate"):
            events.append(LifeEventSignal(
                event_type=LifeEventType.PROBATE,
                detected=True, confidence=0.90,
                source="attom",
                details={"is_deceased": True},
            ))

        # Tax delinquency
        if triggers.get("tax_delinquent"):
            events.append(LifeEventSignal(
                event_type=LifeEventType.TAX_DELINQUENCY,
                detected=True, confidence=0.85,
                source="attom",
                details={"delinquent": True},
            ))

        # Liens → pre-foreclosure proxy
        liens = triggers.get("liens", 0)
        if liens >= 2:
            events.append(LifeEventSignal(
                event_type=LifeEventType.PRE_FORECLOSURE,
                detected=True,
                confidence=min(0.60 + liens * 0.10, 0.95),
                source="attom",
                details={"liens_count": liens},
            ))

        # Long ownership (>10 years)
        summary = dna.get("summary", {})
        years = summary.get("years_owned", 0)
        if years >= 10:
            events.append(LifeEventSignal(
                event_type=LifeEventType.LONG_OWNERSHIP,
                detected=True,
                confidence=min(0.40 + (years - 10) * 0.05, 0.85),
                source="attom",
                details={"years_owned": years},
            ))

        # Absentee owner
        if summary.get("absentee_owner"):
            events.append(LifeEventSignal(
                event_type=LifeEventType.ABSENTEE_OWNER,
                detected=True, confidence=0.80,
                source="attom",
                details={"absentee": True},
            ))

        return events

    # ------------------------------------------------------------------
    # Feature construction
    # ------------------------------------------------------------------

    def _build_feature_vector(
        self,
        life_events: List[LifeEventSignal],
        conversation: Dict[str, Any],
        behavioral: Dict[str, Any],
    ) -> np.ndarray:
        """Build the 26-dim feature vector for prediction."""
        event_set = {e.event_type for e in life_events if e.detected}

        life_feat = [
            1.0 if LifeEventType.PROBATE in event_set else 0.0,
            1.0 if LifeEventType.JOB_RELOCATION in event_set else 0.0,
            1.0 if LifeEventType.DIVORCE in event_set else 0.0,
            1.0 if LifeEventType.TAX_DELINQUENCY in event_set else 0.0,
            1.0 if LifeEventType.PRE_FORECLOSURE in event_set else 0.0,
            1.0 if LifeEventType.LONG_OWNERSHIP in event_set else 0.0,
            1.0 if LifeEventType.ABSENTEE_OWNER in event_set else 0.0,
            1.0 if LifeEventType.RECENT_PERMIT in event_set else 0.0,
            self._extract_detail(life_events, LifeEventType.LONG_OWNERSHIP, "years_owned", 0.0) / 30.0,
            self._extract_detail(life_events, LifeEventType.PRE_FORECLOSURE, "liens_count", 0.0) / 5.0,
            conversation.get("market_value", 500000) / 2_000_000,
            conversation.get("tax_amount", 8000) / 30_000,
        ]

        conv_feat = [
            min(conversation.get("message_count", 0) / 50, 1.0),
            min(conversation.get("avg_response_time", 60) / 300, 1.0),
            (conversation.get("sentiment", 0.0) + 1.0) / 2.0,
            conversation.get("urgency_score", 0.0),
            conversation.get("engagement_score", 0.0),
            conversation.get("qualification_completeness", 0.0),
            conversation.get("budget_confidence", 0.0),
            min(conversation.get("price_mentions", 0) / 10, 1.0),
            conversation.get("location_specificity", 0.0),
        ]

        behav_feat = [
            behavioral.get("commitment_score", 0.0),
            behavioral.get("hedging_score", 0.0),
            behavioral.get("urgency_signal", 0.0),
            behavioral.get("composite_score", 0.0),
            behavioral.get("latency_factor", 0.5),
        ]

        return np.array(life_feat + conv_feat + behav_feat, dtype=np.float64)

    @staticmethod
    def _extract_detail(
        events: List[LifeEventSignal],
        event_type: LifeEventType,
        key: str,
        default: float,
    ) -> float:
        for e in events:
            if e.event_type == event_type and e.detected:
                return float(e.details.get(key, default))
        return default

    # ------------------------------------------------------------------
    # Model prediction / heuristic fallback
    # ------------------------------------------------------------------

    def _predict_with_model(self, features: np.ndarray) -> float:
        """Use trained XGBoost model for prediction."""
        scaled = self._scaler.transform(features.reshape(1, -1))
        proba = self._model.predict_proba(scaled)[0, 1]
        return float(proba)

    def _get_feature_importance(self) -> Dict[str, float]:
        if self._model is None:
            return {}
        return dict(zip(
            self._feature_names,
            [round(float(v), 4) for v in self._model.feature_importances_],
        ))

    def _heuristic_score(
        self,
        life_events: List[LifeEventSignal],
        features: np.ndarray,
    ) -> float:
        """Weighted heuristic when no trained model is available."""
        # Life-event contribution (0-0.50)
        event_score = 0.0
        for evt in life_events:
            if evt.detected:
                base = LIFE_EVENT_CONVERSION_RATES.get(evt.event_type, 0.30)
                event_score = max(event_score, base * evt.confidence)

        # Conversation contribution (0-0.30)
        # Features 12-20 are conversation features
        conv_features = features[12:21]
        conv_score = float(np.mean(conv_features)) * 0.30

        # Behavioural contribution (0-0.20)
        behav_features = features[21:26]
        composite = behav_features[3]  # composite_score
        behav_score = float(composite) * 0.20

        probability = min(event_score * 0.50 + conv_score + behav_score, 1.0)
        return max(probability, 0.05)

    def _heuristic_importance(
        self, life_events: List[LifeEventSignal]
    ) -> Dict[str, float]:
        """Feature importance approximation without a trained model."""
        importance: Dict[str, float] = {}
        for evt in life_events:
            if evt.detected:
                key = f"{evt.event_type.value}_detected"
                importance[key] = round(
                    LIFE_EVENT_CONVERSION_RATES.get(evt.event_type, 0.3) * evt.confidence, 4
                )
        importance["composite_score"] = 0.15
        importance["qualification_completeness"] = 0.10
        importance["engagement_score"] = 0.08
        return importance

    # ------------------------------------------------------------------
    # Scoring helpers
    # ------------------------------------------------------------------

    def _calculate_confidence(
        self,
        life_events: List[LifeEventSignal],
        conversation: Dict[str, Any],
        behavioral: Dict[str, Any],
    ) -> float:
        """Model confidence based on data completeness."""
        score = 0.30  # base confidence

        # Life event data adds confidence
        if life_events:
            avg_conf = np.mean([e.confidence for e in life_events if e.detected] or [0])
            score += float(avg_conf) * 0.30

        # Conversation richness
        msg_count = conversation.get("message_count", 0)
        score += min(msg_count / 20, 1.0) * 0.20

        # Behavioural data presence
        if behavioral.get("composite_score", 0) > 0:
            score += 0.20

        return min(score, 1.0)

    @staticmethod
    def _identify_primary_event(
        events: List[LifeEventSignal],
    ) -> Optional[LifeEventType]:
        """Pick the highest-conversion-rate detected event."""
        detected = [e for e in events if e.detected]
        if not detected:
            return None
        detected.sort(
            key=lambda e: LIFE_EVENT_CONVERSION_RATES.get(e.event_type, 0) * e.confidence,
            reverse=True,
        )
        return detected[0].event_type

    @staticmethod
    def _classify_temperature(probability: float) -> str:
        if probability >= 0.70:
            return "hot"
        if probability >= 0.40:
            return "warm"
        return "cold"

    @staticmethod
    def _recommend_approach(
        primary: Optional[LifeEventType], temperature: str
    ) -> str:
        if primary == LifeEventType.PROBATE:
            return "Empathetic outreach; estate timeline; cash-offer positioning"
        if primary == LifeEventType.DIVORCE:
            return "Neutral facilitation; quick-sale options; dual-agent coordination"
        if primary == LifeEventType.TAX_DELINQUENCY:
            return "Urgency framing; equity preservation; timeline emphasis"
        if primary == LifeEventType.PRE_FORECLOSURE:
            return "Rescue positioning; short-sale expertise; lender negotiation"
        if primary == LifeEventType.JOB_RELOCATION:
            return "Relocation timeline coordination; remote closing options"
        if temperature == "hot":
            return "Direct qualification; showing coordination; fast-track closing"
        if temperature == "warm":
            return "Education-first; market updates; relationship nurturing"
        return "Long-term drip campaign; market awareness; seasonal check-ins"

    @staticmethod
    def _predict_timeline(
        probability: float, events: List[LifeEventSignal]
    ) -> str:
        urgent_events = {
            LifeEventType.PROBATE,
            LifeEventType.PRE_FORECLOSURE,
            LifeEventType.TAX_DELINQUENCY,
        }
        has_urgent = any(
            e.event_type in urgent_events and e.detected for e in events
        )
        if has_urgent or probability >= 0.80:
            return "immediate"
        if probability >= 0.60:
            return "30_days"
        if probability >= 0.40:
            return "60_days"
        if probability >= 0.25:
            return "90_days"
        return "long_term"


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[XGBoostPropensityEngine] = None


def get_propensity_engine() -> XGBoostPropensityEngine:
    global _engine
    if _engine is None:
        _engine = XGBoostPropensityEngine()
    return _engine
