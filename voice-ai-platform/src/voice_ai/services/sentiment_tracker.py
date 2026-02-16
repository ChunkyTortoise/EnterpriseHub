"""Real-time sentiment scoring during voice calls."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)

# Simple keyword-based sentiment (production would use a model)
POSITIVE_WORDS = {
    "great", "excellent", "perfect", "love", "amazing", "wonderful", "fantastic",
    "happy", "interested", "excited", "yes", "absolutely", "definitely", "sure",
    "thank", "thanks", "appreciate", "good", "nice",
}

NEGATIVE_WORDS = {
    "no", "not", "never", "bad", "terrible", "awful", "hate", "dislike",
    "expensive", "overpriced", "waste", "scam", "frustrated", "angry",
    "disappointed", "problem", "issue", "complaint", "worst",
}


@dataclass
class SentimentScore:
    """Sentiment analysis result for a text segment."""

    score: float  # -1.0 (negative) to 1.0 (positive)
    label: str  # "positive" | "neutral" | "negative"
    positive_count: int = 0
    negative_count: int = 0


@dataclass
class SentimentTracker:
    """Tracks real-time sentiment across a voice conversation.

    Maintains a rolling window of sentiment scores per transcript segment.
    """

    _scores: list[SentimentScore] = field(default_factory=list, repr=False)

    def analyze(self, text: str) -> SentimentScore:
        """Analyze sentiment of a text segment."""
        words = set(re.findall(r"\b\w+\b", text.lower()))

        positive_count = len(words & POSITIVE_WORDS)
        negative_count = len(words & NEGATIVE_WORDS)

        total = positive_count + negative_count
        if total == 0:
            score = 0.0
            label = "neutral"
        else:
            score = (positive_count - negative_count) / total
            if score > 0.1:
                label = "positive"
            elif score < -0.1:
                label = "negative"
            else:
                label = "neutral"

        result = SentimentScore(
            score=round(score, 3),
            label=label,
            positive_count=positive_count,
            negative_count=negative_count,
        )
        self._scores.append(result)
        return result

    @property
    def average_sentiment(self) -> float:
        """Return the average sentiment across all analyzed segments."""
        if not self._scores:
            return 0.0
        return round(sum(s.score for s in self._scores) / len(self._scores), 3)

    @property
    def sentiment_distribution(self) -> dict[str, int]:
        """Return count of positive/neutral/negative segments."""
        dist = {"positive": 0, "neutral": 0, "negative": 0}
        for s in self._scores:
            dist[s.label] += 1
        return dist

    def get_summary(self) -> dict:
        """Return a summary of sentiment across the conversation."""
        return {
            "average": self.average_sentiment,
            "distribution": self.sentiment_distribution,
            "total_segments": len(self._scores),
        }

    def reset(self) -> None:
        """Reset sentiment tracking (e.g., for a new call)."""
        self._scores.clear()
