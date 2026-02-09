"""Behavioral feature extraction for ML lead scoring."""
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class BehavioralFeatures:
    """Behavioral signals extracted from conversation patterns."""

    # Response time patterns
    avg_response_time_seconds: float = 0.0
    response_time_trend: float = 0.0  # Negative = getting faster (more engaged)

    # Message characteristics
    avg_message_length: float = 0.0
    emoji_density: float = 0.0  # Emojis per message
    question_ratio: float = 0.0  # % of messages that are questions

    # Temporal patterns
    preferred_hour: int = 12  # 0-23
    weekend_engagement: bool = False
    late_night_engagement: bool = False

    # Initiative signals
    initiative_ratio: float = 0.0  # % of conversations started by lead
    unprompted_messages: int = 0

    # Language signals
    financial_language_density: float = 0.0  # Financial terms per message
    urgency_language_density: float = 0.0  # Urgency terms per message

    def to_feature_vector(self) -> List[float]:
        """Convert to flat feature vector for ML models."""
        return [
            self.avg_response_time_seconds,
            self.response_time_trend,
            self.avg_message_length,
            self.emoji_density,
            self.question_ratio,
            float(self.preferred_hour),
            float(self.weekend_engagement),
            float(self.late_night_engagement),
            self.initiative_ratio,
            float(self.unprompted_messages),
            self.financial_language_density,
            self.urgency_language_density,
        ]

    @staticmethod
    def feature_names() -> List[str]:
        return [
            "avg_response_time_seconds",
            "response_time_trend",
            "avg_message_length",
            "emoji_density",
            "question_ratio",
            "preferred_hour",
            "weekend_engagement",
            "late_night_engagement",
            "initiative_ratio",
            "unprompted_messages",
            "financial_language_density",
            "urgency_language_density",
        ]


FINANCIAL_TERMS = {
    "pre-approved",
    "pre-approval",
    "mortgage",
    "down payment",
    "budget",
    "afford",
    "loan",
    "interest rate",
    "closing costs",
    "earnest money",
    "lender",
    "financing",
    "credit score",
    "debt-to-income",
}

URGENCY_TERMS = {
    "asap",
    "soon",
    "immediately",
    "urgent",
    "right away",
    "this week",
    "this month",
    "ready",
    "need to move",
    "deadline",
    "lease ending",
    "relocating",
    "transferred",
}


def extract_behavioral_features(
    messages: List[Dict[str, Any]],
    timestamps: Optional[List[datetime]] = None,
) -> BehavioralFeatures:
    """Extract behavioral features from conversation messages.

    Args:
        messages: List of {"role": "user"|"assistant", "content": "..."} dicts
        timestamps: Optional parallel list of message timestamps

    Returns:
        BehavioralFeatures dataclass
    """
    features = BehavioralFeatures()

    user_msgs = [m for m in messages if m.get("role") == "user"]
    if not user_msgs:
        return features

    # Message length
    lengths = [len(m.get("content", "")) for m in user_msgs]
    features.avg_message_length = sum(lengths) / len(lengths) if lengths else 0.0

    # Emoji density
    emoji_pattern = re.compile(
        "[\U0001f600-\U0001f64f\U0001f300-\U0001f5ff"
        "\U0001f680-\U0001f6ff\U0001f1e0-\U0001f1ff]"
    )
    total_emojis = sum(
        len(emoji_pattern.findall(m.get("content", ""))) for m in user_msgs
    )
    features.emoji_density = total_emojis / len(user_msgs) if user_msgs else 0.0

    # Question ratio
    questions = sum(1 for m in user_msgs if "?" in m.get("content", ""))
    features.question_ratio = questions / len(user_msgs) if user_msgs else 0.0

    # Financial and urgency language density
    for m in user_msgs:
        content_lower = m.get("content", "").lower()
        words = content_lower.split()
        if words:
            fin_count = sum(1 for term in FINANCIAL_TERMS if term in content_lower)
            urg_count = sum(1 for term in URGENCY_TERMS if term in content_lower)
            features.financial_language_density += fin_count / len(words)
            features.urgency_language_density += urg_count / len(words)

    if user_msgs:
        features.financial_language_density /= len(user_msgs)
        features.urgency_language_density /= len(user_msgs)

    # Response time patterns (if timestamps provided)
    if timestamps and len(timestamps) >= 2:
        response_times = []
        for i in range(1, len(timestamps)):
            if (
                messages[i].get("role") == "user"
                and messages[i - 1].get("role") == "assistant"
            ):
                delta = (timestamps[i] - timestamps[i - 1]).total_seconds()
                if 0 < delta < 86400:  # Ignore gaps > 24h
                    response_times.append(delta)

        if response_times:
            features.avg_response_time_seconds = sum(response_times) / len(
                response_times
            )
            if len(response_times) >= 3:
                first_half = response_times[: len(response_times) // 2]
                second_half = response_times[len(response_times) // 2 :]
                avg_first = sum(first_half) / len(first_half)
                avg_second = sum(second_half) / len(second_half)
                features.response_time_trend = avg_second - avg_first

        # Temporal patterns
        user_hours = [
            timestamps[i].hour
            for i in range(len(timestamps))
            if messages[i].get("role") == "user"
        ]
        if user_hours:
            features.preferred_hour = max(set(user_hours), key=user_hours.count)
            features.late_night_engagement = any(
                22 <= h or h < 6 for h in user_hours
            )

        user_weekdays = [
            timestamps[i].weekday()
            for i in range(len(timestamps))
            if messages[i].get("role") == "user"
        ]
        features.weekend_engagement = any(d >= 5 for d in user_weekdays)

    # Initiative: count user messages that start a new "turn" (first or after long gap)
    initiative_count = 0
    for i, m in enumerate(messages):
        if m.get("role") == "user":
            if i == 0:
                initiative_count += 1
            elif i >= 2 and messages[i - 1].get("role") == "user":
                features.unprompted_messages += 1

    total_user = len(user_msgs)
    features.initiative_ratio = (
        initiative_count / total_user if total_user > 0 else 0.0
    )

    return features
