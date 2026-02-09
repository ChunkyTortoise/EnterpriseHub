"""
Multi-Channel Sentiment Analysis Engine

Real-time sentiment and emotion tracking across SMS, voice, email, and chat
channels.  Computes per-message polarity, rolling sentiment trends, emotion
classification, and conversation-level engagement metrics.

Integrates with ``BehavioralTriggerDetector`` for composite behavioural scoring.

Usage::

    engine = get_sentiment_engine()
    result = await engine.analyze_message(
        contact_id="c_123",
        message="I really love that house on Haven Ave!",
        channel="sms",
    )
    print(result.polarity, result.emotion, result.trend)
"""

import logging
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


class Emotion(Enum):
    """Primary emotion categories for real-estate conversations."""

    EXCITED = "excited"
    INTERESTED = "interested"
    NEUTRAL = "neutral"
    HESITANT = "hesitant"
    FRUSTRATED = "frustrated"
    ANXIOUS = "anxious"
    CONFIDENT = "confident"
    DISAPPOINTED = "disappointed"


class SentimentTrend(Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DECLINING = "declining"


class Channel(Enum):
    SMS = "sms"
    VOICE = "voice"
    EMAIL = "email"
    CHAT = "chat"
    VIDEO = "video"


@dataclass
class SentimentResult:
    """Analysis result for a single message."""

    contact_id: str
    polarity: float  # -1.0 (very negative) to 1.0 (very positive)
    magnitude: float  # 0.0 to 1.0 (strength of sentiment)
    emotion: Emotion
    confidence: float  # 0.0 to 1.0
    channel: Channel
    intent_signals: List[str] = field(default_factory=list)
    key_phrases: List[str] = field(default_factory=list)
    timestamp: float = field(default_factory=time.time)


@dataclass
class ConversationSentiment:
    """Aggregated sentiment for a full conversation."""

    contact_id: str
    message_count: int
    avg_polarity: float
    polarity_variance: float
    dominant_emotion: Emotion
    trend: SentimentTrend
    engagement_score: float  # 0-1
    escalation_risk: float  # 0-1
    emotion_distribution: Dict[str, float] = field(default_factory=dict)
    sentiment_timeline: List[float] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Lexicon-based sentiment (fast, no ML dependency)
# ---------------------------------------------------------------------------

POSITIVE_PATTERNS: List[Tuple[str, float]] = [
    (r"\blove\b", 0.8),
    (r"\bexcited\b", 0.9),
    (r"\bperfect\b", 0.85),
    (r"\bamazing\b", 0.85),
    (r"\bgreat\b", 0.7),
    (r"\bgood\b", 0.5),
    (r"\binterested\b", 0.6),
    (r"\bbeautiful\b", 0.75),
    (r"\bwonderful\b", 0.8),
    (r"\bfantastic\b", 0.85),
    (r"\bready\b", 0.5),
    (r"\byes\b", 0.4),
    (r"\babsolutely\b", 0.7),
    (r"\bdefinitely\b", 0.65),
    (r"\bcan'?t wait\b", 0.85),
    (r"\blooking forward\b", 0.7),
    (r"\bdream home\b", 0.9),
    (r"\blet'?s do it\b", 0.8),
    (r"\bimpressed\b", 0.75),
    (r"\baffordable\b", 0.5),
]

NEGATIVE_PATTERNS: List[Tuple[str, float]] = [
    (r"\bhate\b", -0.8),
    (r"\bterrible\b", -0.85),
    (r"\bdisappointed\b", -0.7),
    (r"\bfrustrated\b", -0.75),
    (r"\btoo expensive\b", -0.6),
    (r"\bover\s*priced\b", -0.65),
    (r"\bnot interested\b", -0.7),
    (r"\bwaste of time\b", -0.8),
    (r"\bawful\b", -0.85),
    (r"\bhidden fees\b", -0.7),
    (r"\bscam\b", -0.9),
    (r"\bpushy\b", -0.6),
    (r"\bpressure\b", -0.5),
    (r"\bworried\b", -0.45),
    (r"\bnervous\b", -0.4),
    (r"\bcan'?t afford\b", -0.65),
    (r"\bgive up\b", -0.7),
    (r"\bstop\s*(contacting|texting|calling)\b", -0.85),
]

EMOTION_PATTERNS: Dict[Emotion, List[Tuple[str, float]]] = {
    Emotion.EXCITED: [
        (r"\bexcited\b", 0.9),
        (r"\bcan'?t wait\b", 0.85),
        (r"!{2,}", 0.6),
        (r"\bomg\b", 0.7),
        (r"\bwow\b", 0.65),
    ],
    Emotion.INTERESTED: [
        (r"\btell me more\b", 0.8),
        (r"\binterested\b", 0.75),
        (r"\bwhat about\b", 0.5),
        (r"\bhow much\b", 0.6),
        (r"\bwhen can\b", 0.65),
    ],
    Emotion.HESITANT: [
        (r"\bmaybe\b", 0.5),
        (r"\bnot sure\b", 0.65),
        (r"\bneed to think\b", 0.7),
        (r"\bi don'?t know\b", 0.6),
        (r"\blet me.*think\b", 0.6),
    ],
    Emotion.FRUSTRATED: [
        (r"\bfrustrat", 0.8),
        (r"\bannoyed\b", 0.7),
        (r"\bstop\b", 0.6),
        (r"\benough\b", 0.55),
        (r"\btired of\b", 0.7),
    ],
    Emotion.ANXIOUS: [
        (r"\bworried\b", 0.7),
        (r"\bnervous\b", 0.65),
        (r"\bscared\b", 0.75),
        (r"\bconcerned\b", 0.55),
        (r"\bafraid\b", 0.7),
    ],
    Emotion.CONFIDENT: [
        (r"\bready\b", 0.6),
        (r"\blet'?s do\b", 0.8),
        (r"\bdecided\b", 0.75),
        (r"\bgoing for it\b", 0.8),
        (r"\bdefinitely\b", 0.65),
    ],
    Emotion.DISAPPOINTED: [
        (r"\bdisappoint", 0.8),
        (r"\bexpected more\b", 0.7),
        (r"\bnot what i\b", 0.6),
        (r"\bunhappy\b", 0.7),
    ],
}

INTENT_PATTERNS: Dict[str, str] = {
    r"\bschedul\w*\s*(a\s*)?(tour|showing|visit)\b": "schedule_showing",
    r"\bhow much\b": "price_inquiry",
    r"\bpre[- ]?approv": "financing_inquiry",
    r"\bmake\s*(an?\s*)?offer\b": "make_offer",
    r"\bnegotiat": "negotiation",
    r"\bwalk\s*away\b": "disengagement",
    r"\bcompare\b": "comparison_shopping",
    r"\bopen house\b": "open_house_interest",
}


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------


class SentimentAnalysisEngine:
    """
    Lexicon + pattern-based sentiment engine optimised for speed (<5ms/msg).

    Maintains per-contact conversation history for trend detection and
    emotion distribution tracking.
    """

    # Rolling window for trend calculation
    TREND_WINDOW = 5
    # Escalation threshold
    ESCALATION_THRESHOLD = -0.3

    def __init__(self):
        self._conversation_history: Dict[str, List[SentimentResult]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyze_message(
        self,
        contact_id: str,
        message: str,
        channel: str = "sms",
    ) -> SentimentResult:
        """Analyse a single message and update conversation history."""
        text = message.lower().strip()
        channel_enum = self._resolve_channel(channel)

        polarity, magnitude = self._compute_polarity(text)
        emotion, emotion_conf = self._classify_emotion(text, polarity)
        intents = self._detect_intents(text)
        key_phrases = self._extract_key_phrases(text)

        result = SentimentResult(
            contact_id=contact_id,
            polarity=round(polarity, 4),
            magnitude=round(magnitude, 4),
            emotion=emotion,
            confidence=round(emotion_conf, 4),
            channel=channel_enum,
            intent_signals=intents,
            key_phrases=key_phrases,
        )

        self._conversation_history.setdefault(contact_id, []).append(result)
        return result

    async def get_conversation_sentiment(self, contact_id: str) -> ConversationSentiment:
        """Compute aggregated sentiment for a contact's conversation."""
        history = self._conversation_history.get(contact_id, [])
        if not history:
            return ConversationSentiment(
                contact_id=contact_id,
                message_count=0,
                avg_polarity=0.0,
                polarity_variance=0.0,
                dominant_emotion=Emotion.NEUTRAL,
                trend=SentimentTrend.STABLE,
                engagement_score=0.0,
                escalation_risk=0.0,
            )

        polarities = [r.polarity for r in history]
        avg_pol = sum(polarities) / len(polarities)
        variance = sum((p - avg_pol) ** 2 for p in polarities) / len(polarities)

        emotion_dist = self._compute_emotion_distribution(history)
        dominant = max(emotion_dist, key=emotion_dist.get, default="neutral")
        trend = self._compute_trend(polarities)
        engagement = self._compute_engagement(history)
        escalation = self._compute_escalation_risk(polarities, history)

        return ConversationSentiment(
            contact_id=contact_id,
            message_count=len(history),
            avg_polarity=round(avg_pol, 4),
            polarity_variance=round(variance, 4),
            dominant_emotion=Emotion(dominant),
            trend=trend,
            engagement_score=round(engagement, 4),
            escalation_risk=round(escalation, 4),
            emotion_distribution=emotion_dist,
            sentiment_timeline=polarities,
        )

    def clear_history(self, contact_id: Optional[str] = None) -> None:
        """Clear conversation history for a contact or all contacts."""
        if contact_id:
            self._conversation_history.pop(contact_id, None)
        else:
            self._conversation_history.clear()

    # ------------------------------------------------------------------
    # Polarity computation
    # ------------------------------------------------------------------

    def _compute_polarity(self, text: str) -> Tuple[float, float]:
        """Compute sentiment polarity and magnitude from text."""
        pos_scores: List[float] = []
        neg_scores: List[float] = []

        for pattern, weight in POSITIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                pos_scores.append(weight)

        for pattern, weight in NEGATIVE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                neg_scores.append(abs(weight))

        # Handle negation modifiers
        negation = bool(re.search(r"\b(not|no|never|don'?t|doesn'?t|wasn'?t|isn'?t|aren'?t)\b", text))
        if negation and pos_scores and not neg_scores:
            neg_scores = [s * 0.7 for s in pos_scores]
            pos_scores = []
        elif negation and neg_scores and not pos_scores:
            pos_scores = [s * 0.5 for s in neg_scores]
            neg_scores = []

        if not pos_scores and not neg_scores:
            return 0.0, 0.0

        pos_total = sum(pos_scores) / max(len(pos_scores), 1)
        neg_total = sum(neg_scores) / max(len(neg_scores), 1)

        polarity = pos_total - neg_total
        polarity = max(-1.0, min(1.0, polarity))
        magnitude = min((pos_total + neg_total) / 2, 1.0)

        return polarity, magnitude

    # ------------------------------------------------------------------
    # Emotion classification
    # ------------------------------------------------------------------

    def _classify_emotion(self, text: str, polarity: float) -> Tuple[Emotion, float]:
        """Classify the primary emotion with confidence."""
        scores: Dict[Emotion, float] = {}

        for emotion, patterns in EMOTION_PATTERNS.items():
            total = 0.0
            hits = 0
            for pattern, weight in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    total += weight
                    hits += 1
            if hits:
                scores[emotion] = total / hits

        if not scores:
            # Fall back to polarity-based classification
            if polarity > 0.3:
                return Emotion.INTERESTED, 0.5
            if polarity < -0.3:
                return Emotion.HESITANT, 0.5
            return Emotion.NEUTRAL, 0.6

        best_emotion = max(scores, key=scores.get)
        confidence = min(scores[best_emotion], 1.0)
        return best_emotion, confidence

    # ------------------------------------------------------------------
    # Intent detection
    # ------------------------------------------------------------------

    @staticmethod
    def _detect_intents(text: str) -> List[str]:
        intents: List[str] = []
        for pattern, intent in INTENT_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                intents.append(intent)
        return intents

    # ------------------------------------------------------------------
    # Key phrase extraction
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_key_phrases(text: str) -> List[str]:
        """Extract notable phrases from message."""
        phrases: List[str] = []
        price_match = re.findall(r"\$[\d,]+k?", text)
        phrases.extend(price_match)

        location_match = re.findall(
            r"\b(?:rancho cucamonga|victoria|haven|etiwanda|terra vista|central park)\b",
            text,
            re.IGNORECASE,
        )
        phrases.extend(location_match)

        bedroom_match = re.findall(r"\b\d\s*(?:br|bed(?:room)?s?)\b", text, re.IGNORECASE)
        phrases.extend(bedroom_match)

        return phrases[:5]

    # ------------------------------------------------------------------
    # Aggregation helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _compute_emotion_distribution(
        history: List[SentimentResult],
    ) -> Dict[str, float]:
        counts: Dict[str, int] = {}
        for r in history:
            key = r.emotion.value
            counts[key] = counts.get(key, 0) + 1
        total = len(history)
        return {k: round(v / total, 4) for k, v in counts.items()}

    def _compute_trend(self, polarities: List[float]) -> SentimentTrend:
        """Detect sentiment trend from recent messages."""
        if len(polarities) < 2:
            return SentimentTrend.STABLE

        recent = polarities[-self.TREND_WINDOW :]
        if len(recent) < 2:
            return SentimentTrend.STABLE

        # Simple linear slope
        n = len(recent)
        x_mean = (n - 1) / 2
        y_mean = sum(recent) / n
        numerator = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(recent))
        denominator = sum((i - x_mean) ** 2 for i in range(n))

        if denominator == 0:
            return SentimentTrend.STABLE

        slope = numerator / denominator

        if slope > 0.05:
            return SentimentTrend.IMPROVING
        if slope < -0.05:
            return SentimentTrend.DECLINING
        return SentimentTrend.STABLE

    @staticmethod
    def _compute_engagement(history: List[SentimentResult]) -> float:
        """Engagement score based on message frequency and magnitude."""
        if not history:
            return 0.0
        avg_magnitude = sum(r.magnitude for r in history) / len(history)
        msg_factor = min(len(history) / 10, 1.0)
        intent_factor = sum(1 for r in history if r.intent_signals) / max(len(history), 1)
        return min(avg_magnitude * 0.4 + msg_factor * 0.3 + intent_factor * 0.3, 1.0)

    def _compute_escalation_risk(self, polarities: List[float], history: List[SentimentResult]) -> float:
        """Risk of conversation escalation requiring human intervention."""
        if not polarities:
            return 0.0

        recent = polarities[-self.TREND_WINDOW :]
        avg_recent = sum(recent) / len(recent)

        # Strongly negative recent sentiment
        negativity = max(0, -avg_recent)

        # Frustration presence
        frustration = sum(
            1 for r in history[-self.TREND_WINDOW :] if r.emotion in (Emotion.FRUSTRATED, Emotion.DISAPPOINTED)
        ) / max(len(recent), 1)

        # Declining trend
        trend = self._compute_trend(polarities)
        trend_risk = 0.3 if trend == SentimentTrend.DECLINING else 0.0

        risk = negativity * 0.4 + frustration * 0.35 + trend_risk * 0.25
        return min(risk, 1.0)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_channel(channel: str) -> Channel:
        try:
            return Channel(channel.lower())
        except ValueError:
            return Channel.SMS


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[SentimentAnalysisEngine] = None


def get_sentiment_engine() -> SentimentAnalysisEngine:
    global _engine
    if _engine is None:
        _engine = SentimentAnalysisEngine()
    return _engine
