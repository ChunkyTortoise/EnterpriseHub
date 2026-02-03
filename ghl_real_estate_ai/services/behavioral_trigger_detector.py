"""
Behavioral Trigger Detector

Unified behavioral analysis service that combines multiple signal sources
to detect negotiation patterns, hedging language, response latency anomalies,
commitment signals, and Voss framework techniques.

Extends the lightweight ``NegotiationDriftDetector`` with:
- Granular hedging + commitment pattern matching with confidence weights
- Response latency anomaly detection with configurable baseline
- Urgency / stall / objection trigger classification
- Voss negotiation technique recommendation engine
- Composite scoring across all signal dimensions
"""

import logging
import math
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class TriggerType(str, Enum):
    HEDGING = "hedging"
    LATENCY_ANOMALY = "latency_anomaly"
    URGENCY_SHIFT = "urgency_shift"
    COMMITMENT_SIGNAL = "commitment_signal"
    OBJECTION = "objection"
    STALL = "stall"
    ENGAGEMENT_DROP = "engagement_drop"
    PRICE_SENSITIVITY = "price_sensitivity"


class NegotiationTechnique(str, Enum):
    MIRRORING = "mirroring"
    LABELING = "labeling"
    ANCHORING = "anchoring"
    CALIBRATED_QUESTION = "calibrated_question"
    TACTICAL_EMPATHY = "tactical_empathy"
    DIRECT_CHALLENGE = "direct_challenge"


class DriftDirection(str, Enum):
    WARMING = "warming"
    COOLING = "cooling"
    STABLE = "stable"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class BehavioralTrigger:
    type: TriggerType
    confidence: float  # 0.0 – 1.0
    description: str
    recommended_action: str
    raw_signal: dict = field(default_factory=dict)


@dataclass
class BehavioralAnalysis:
    """Aggregate result of behavioral analysis on a single message."""
    triggers: List[BehavioralTrigger]
    composite_score: float  # 0.0 (cold) – 1.0 (hot)
    drift_direction: str  # DriftDirection value
    hedging_score: float
    urgency_score: float
    commitment_score: float
    recommended_technique: Optional[str]  # NegotiationTechnique value
    latency_factor: float


# ---------------------------------------------------------------------------
# Pattern banks
# ---------------------------------------------------------------------------

# (regex, base_confidence)
HEDGING_PATTERNS: List[tuple] = [
    (r"\bmaybe\b", 0.60),
    (r"\bpossibly\b", 0.55),
    (r"\bperhaps\b", 0.55),
    (r"\bmight\b", 0.50),
    (r"\bcould\b", 0.45),
    (r"\bi\s+think\b", 0.40),
    (r"\bnot\s+sure\b", 0.65),
    (r"\bflexible\b", 0.70),
    (r"\bopen\s+to\b", 0.65),
    (r"\bnegotiable\b", 0.75),
    (r"\bdepends\b", 0.55),
    (r"\bconsider\b", 0.50),
    (r"\bif\s+the\s+price\b", 0.60),
    (r"\bwilling\s+to\b", 0.55),
    (r"\bwe'll\s+see\b", 0.50),
]

COMMITMENT_PATTERNS: List[tuple] = [
    (r"\bdefinitely\b", 0.85),
    (r"\bfor\s+sure\b", 0.80),
    (r"\babsolutely\b", 0.85),
    (r"\blet'?s\s+do\s+it\b", 0.90),
    (r"\bready\s+to\b", 0.75),
    (r"\bi\s+want\s+to\b", 0.70),
    (r"\bsign\s+me\s+up\b", 0.90),
    (r"\bwhen\s+can\s+we\b", 0.80),
    (r"\bschedule\b", 0.65),
    (r"\byes\b", 0.60),
]

URGENCY_PATTERNS: List[tuple] = [
    (r"\basap\b", 0.90),
    (r"\bimmediately\b", 0.85),
    (r"\burgent\b", 0.90),
    (r"\bright\s+away\b", 0.85),
    (r"\bthis\s+week\b", 0.70),
    (r"\btoday\b", 0.75),
    (r"\btomorrow\b", 0.70),
    (r"\bneed\s+to\s+move\b", 0.80),
    (r"\bquickly\b", 0.70),
    (r"\bsoon\b", 0.55),
]

OBJECTION_PATTERNS: List[tuple] = [
    (r"\btoo\s+expensive\b", 0.80),
    (r"\btoo\s+high\b", 0.75),
    (r"\bcan'?t\s+afford\b", 0.85),
    (r"\bnot\s+interested\b", 0.90),
    (r"\bnot\s+ready\b", 0.70),
    (r"\bnot\s+now\b", 0.65),
    (r"\bneed\s+more\s+time\b", 0.60),
    (r"\bwant\s+to\s+wait\b", 0.65),
]

STALL_PATTERNS: List[tuple] = [
    (r"\bget\s+back\s+to\s+you\b", 0.75),
    (r"\bthink\s+about\s+it\b", 0.70),
    (r"\btalk\s+to\s+my\b", 0.65),
    (r"\bneed\s+to\s+discuss\b", 0.60),
    (r"\bjust\s+browsing\b", 0.80),
    (r"\bjust\s+looking\b", 0.80),
    (r"\bno\s+rush\b", 0.70),
]

PRICE_SENSITIVITY_PATTERNS: List[tuple] = [
    (r"\bhow\s+much\b", 0.50),
    (r"\bprice\b", 0.40),
    (r"\bbudget\b", 0.55),
    (r"\bcost\b", 0.45),
    (r"\bafford\b", 0.60),
    (r"\bcheaper\b", 0.70),
    (r"\bdiscount\b", 0.65),
    (r"\blower\b", 0.50),
]


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class BehavioralTriggerDetector:
    """
    Stateless message-level behavioral analysis.

    Usage::

        detector = BehavioralTriggerDetector()
        result = await detector.analyze_message(
            message="Maybe if the price is right",
            contact_id="c_123",
            response_latency_ms=45000,
        )
        print(result.hedging_score, result.composite_score)
    """

    # Configurable weights for composite score
    WEIGHT_COMMITMENT = 0.30
    WEIGHT_URGENCY = 0.25
    WEIGHT_HEDGING_INV = 0.20  # inverse: high hedging = low composite
    WEIGHT_LATENCY = 0.15
    WEIGHT_LENGTH = 0.10

    # Latency baseline (ms) — responses under this are "fast"
    LATENCY_BASELINE_MS = 60_000  # 1 minute

    async def analyze_message(
        self,
        message: str,
        contact_id: str,
        conversation_history: Optional[List[Dict]] = None,
        response_latency_ms: Optional[float] = None,
    ) -> BehavioralAnalysis:
        """
        Analyze a single message for behavioral triggers.

        Returns a ``BehavioralAnalysis`` with individual dimension scores
        and an overall composite score.
        """
        triggers: List[BehavioralTrigger] = []

        # --- 1. Hedging ---
        hedging_score, hedging_triggers = self._detect_patterns(
            message, HEDGING_PATTERNS, TriggerType.HEDGING,
            "Lead is hedging — showing internal flexibility.",
            "Use Labeling to surface the underlying concern.",
        )
        triggers.extend(hedging_triggers)

        # --- 2. Commitment ---
        commitment_score, commit_triggers = self._detect_patterns(
            message, COMMITMENT_PATTERNS, TriggerType.COMMITMENT_SIGNAL,
            "Commitment signal detected.",
            "Reinforce commitment and move toward close.",
        )
        triggers.extend(commit_triggers)

        # --- 3. Urgency ---
        urgency_score, urgency_triggers = self._detect_patterns(
            message, URGENCY_PATTERNS, TriggerType.URGENCY_SHIFT,
            "Urgency signal detected.",
            "Capitalize on urgency — present next steps immediately.",
        )
        triggers.extend(urgency_triggers)

        # --- 4. Objections ---
        _, objection_triggers = self._detect_patterns(
            message, OBJECTION_PATTERNS, TriggerType.OBJECTION,
            "Objection raised.",
            "Acknowledge concern with Tactical Empathy, then reframe.",
        )
        triggers.extend(objection_triggers)

        # --- 5. Stalls ---
        _, stall_triggers = self._detect_patterns(
            message, STALL_PATTERNS, TriggerType.STALL,
            "Stall detected — lead delaying decision.",
            "Use Direct Challenge or take-away close.",
        )
        triggers.extend(stall_triggers)

        # --- 6. Price sensitivity ---
        _, price_triggers = self._detect_patterns(
            message, PRICE_SENSITIVITY_PATTERNS, TriggerType.PRICE_SENSITIVITY,
            "Price sensitivity detected.",
            "Anchor with market data before discussing price.",
        )
        triggers.extend(price_triggers)

        # --- 7. Latency analysis ---
        latency_factor = self._analyze_latency(response_latency_ms)
        if response_latency_ms is not None and latency_factor >= 0.7:
            triggers.append(BehavioralTrigger(
                type=TriggerType.LATENCY_ANOMALY,
                confidence=latency_factor,
                description="Slow response indicates internal deliberation.",
                recommended_action="High latency suggests flexibility — probe gently.",
                raw_signal={"latency_ms": response_latency_ms},
            ))

        # --- 8. Engagement drop (conversation history) ---
        engagement_drop = self._detect_engagement_drop(
            message, conversation_history or [],
        )
        if engagement_drop > 0.5:
            triggers.append(BehavioralTrigger(
                type=TriggerType.ENGAGEMENT_DROP,
                confidence=engagement_drop,
                description="Message length dropped significantly.",
                recommended_action="Re-engage with an open-ended Calibrated Question.",
                raw_signal={"drop_factor": engagement_drop},
            ))

        # --- Composite scoring ---
        composite = self._compute_composite(
            hedging_score, commitment_score, urgency_score, latency_factor, message,
        )

        # --- Drift direction ---
        drift = self._compute_drift(
            hedging_score, commitment_score, urgency_score, conversation_history or [],
        )

        # --- Technique recommendation ---
        technique = self._recommend_technique(
            hedging_score, commitment_score, urgency_score,
            bool(stall_triggers), bool(objection_triggers),
        )

        return BehavioralAnalysis(
            triggers=triggers,
            composite_score=round(composite, 3),
            drift_direction=drift,
            hedging_score=round(hedging_score, 3),
            urgency_score=round(urgency_score, 3),
            commitment_score=round(commitment_score, 3),
            recommended_technique=technique,
            latency_factor=round(latency_factor, 3),
        )

    # ------------------------------------------------------------------
    # Pattern detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_patterns(
        message: str,
        patterns: List[tuple],
        trigger_type: TriggerType,
        description: str,
        action: str,
    ) -> tuple:
        """Match patterns and return (aggregate_score, list[BehavioralTrigger])."""
        triggers: List[BehavioralTrigger] = []
        total_confidence = 0.0
        hit_count = 0

        for regex, base_conf in patterns:
            if re.search(regex, message, re.IGNORECASE):
                hit_count += 1
                total_confidence += base_conf
                triggers.append(BehavioralTrigger(
                    type=trigger_type,
                    confidence=base_conf,
                    description=description,
                    recommended_action=action,
                    raw_signal={"pattern": regex},
                ))

        # Normalize score: diminishing returns on multiple hits
        if hit_count == 0:
            score = 0.0
        else:
            avg_conf = total_confidence / hit_count
            # Logarithmic scaling: more hits increase score but with diminishing returns
            score = min(1.0, avg_conf * (1 + math.log1p(hit_count - 1) * 0.3))

        return score, triggers

    # ------------------------------------------------------------------
    # Latency analysis
    # ------------------------------------------------------------------

    def _analyze_latency(self, latency_ms: Optional[float]) -> float:
        """
        Convert response latency to a 0-1 factor.
        Fast responses → low factor (engaged).
        Slow responses → high factor (deliberating / flexible).
        """
        if latency_ms is None:
            return 0.0
        if latency_ms <= 0:
            return 0.0
        # Sigmoid-like curve centered at baseline
        ratio = latency_ms / self.LATENCY_BASELINE_MS
        return min(1.0, 1 / (1 + math.exp(-3 * (ratio - 1))))

    # ------------------------------------------------------------------
    # Engagement drop
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_engagement_drop(
        current_message: str,
        history: List[Dict],
    ) -> float:
        """
        Compare current message length to recent average.
        A significant drop suggests disengagement.
        """
        if not history:
            return 0.0

        recent_lengths = []
        for entry in history[-5:]:
            body = entry.get("message", entry.get("body", ""))
            if body:
                recent_lengths.append(len(body.split()))

        if not recent_lengths:
            return 0.0

        avg_len = sum(recent_lengths) / len(recent_lengths)
        current_len = len(current_message.split())

        if avg_len <= 0:
            return 0.0

        drop_ratio = 1 - (current_len / avg_len)
        return max(0.0, min(1.0, drop_ratio))

    # ------------------------------------------------------------------
    # Composite scoring
    # ------------------------------------------------------------------

    def _compute_composite(
        self,
        hedging: float,
        commitment: float,
        urgency: float,
        latency: float,
        message: str,
    ) -> float:
        """
        Compute 0-1 composite score where higher = hotter lead.
        Hedging is inverted (high hedging lowers the score).
        Message length adds a small engagement signal.
        """
        word_count = len(message.split())
        length_factor = min(1.0, word_count / 50)

        score = (
            self.WEIGHT_COMMITMENT * commitment
            + self.WEIGHT_URGENCY * urgency
            + self.WEIGHT_HEDGING_INV * (1 - hedging)
            + self.WEIGHT_LATENCY * (1 - latency)  # fast response = higher score
            + self.WEIGHT_LENGTH * length_factor
        )
        return max(0.0, min(1.0, score))

    # ------------------------------------------------------------------
    # Drift direction
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_drift(
        hedging: float,
        commitment: float,
        urgency: float,
        history: List[Dict],
    ) -> str:
        """Infer whether the lead is warming or cooling."""
        heat = commitment + urgency
        cold = hedging

        if heat > cold + 0.3:
            return DriftDirection.WARMING.value
        elif cold > heat + 0.3:
            return DriftDirection.COOLING.value
        return DriftDirection.STABLE.value

    # ------------------------------------------------------------------
    # Technique recommendation (Voss framework)
    # ------------------------------------------------------------------

    @staticmethod
    def _recommend_technique(
        hedging: float,
        commitment: float,
        urgency: float,
        has_stall: bool,
        has_objection: bool,
    ) -> Optional[str]:
        """
        Recommend a Voss negotiation technique based on signal profile.

        Priority:
        1. Stall → Direct Challenge
        2. Objection → Tactical Empathy
        3. High hedging → Labeling
        4. High commitment → Anchoring (lock in)
        5. High urgency → Calibrated Question (qualify further)
        """
        if has_stall:
            return NegotiationTechnique.DIRECT_CHALLENGE.value
        if has_objection:
            return NegotiationTechnique.TACTICAL_EMPATHY.value
        if hedging >= 0.5:
            return NegotiationTechnique.LABELING.value
        if commitment >= 0.6:
            return NegotiationTechnique.ANCHORING.value
        if urgency >= 0.5:
            return NegotiationTechnique.CALIBRATED_QUESTION.value
        return None


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_detector: Optional[BehavioralTriggerDetector] = None


def get_behavioral_detector() -> BehavioralTriggerDetector:
    global _detector
    if _detector is None:
        _detector = BehavioralTriggerDetector()
    return _detector
