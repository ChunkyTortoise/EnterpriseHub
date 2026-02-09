"""Conversation Analytics Service for message analysis, sentiment, engagement, and quality."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from sklearn.feature_extraction.text import TfidfVectorizer

POSITIVE_WORDS = frozenset(
    {
        "love",
        "great",
        "excellent",
        "wonderful",
        "amazing",
        "fantastic",
        "perfect",
        "beautiful",
        "happy",
        "glad",
        "thrilled",
        "excited",
        "delighted",
        "pleased",
        "awesome",
        "outstanding",
        "superb",
        "brilliant",
        "terrific",
        "marvelous",
        "good",
        "nice",
        "fine",
        "lovely",
        "enjoy",
        "appreciate",
        "grateful",
        "thank",
        "thanks",
        "helpful",
        "impressive",
        "remarkable",
        "splendid",
        "fabulous",
        "incredible",
        "magnificent",
        "phenomenal",
        "spectacular",
        "positive",
        "optimistic",
        "enthusiastic",
        "eager",
        "confident",
        "comfortable",
        "satisfied",
        "content",
        "cheerful",
        "joyful",
        "warm",
        "friendly",
        "welcome",
        "pleasant",
        "charming",
        "elegant",
        "spacious",
        "gorgeous",
        "stunning",
        "ideal",
    }
)

NEGATIVE_WORDS = frozenset(
    {
        "terrible",
        "awful",
        "horrible",
        "bad",
        "worst",
        "hate",
        "angry",
        "frustrated",
        "disappointed",
        "annoyed",
        "upset",
        "unhappy",
        "sad",
        "disgusted",
        "furious",
        "outraged",
        "miserable",
        "dreadful",
        "appalling",
        "poor",
        "ugly",
        "dirty",
        "broken",
        "damaged",
        "defective",
        "expensive",
        "overpriced",
        "ridiculous",
        "absurd",
        "unacceptable",
        "rude",
        "disrespectful",
        "incompetent",
        "useless",
        "worthless",
        "boring",
        "tedious",
        "confusing",
        "complicated",
        "stressful",
        "problem",
        "issue",
        "complaint",
        "concern",
        "worry",
        "never",
        "reject",
        "refuse",
        "deny",
        "fail",
        "wrong",
        "error",
        "mistake",
        "fault",
        "flaw",
    }
)

RESOLUTION_PATTERNS = [
    r"\bthank\s*(you|s)\b",
    r"\bthanks\b",
    r"\bgoodbye\b",
    r"\bbye\b",
    r"\bappreciate\b",
    r"\bhelpful\b",
    r"\bperfect\b",
    r"\bschedule[d]?\b",
    r"\bgreat\s+help\b",
    r"\bthat\s*'?s?\s+all\b",
]


@dataclass
class ConversationMetrics:
    message_count: int
    avg_response_length: float
    user_message_ratio: float
    avg_sentiment: float
    topic_drift_score: float
    engagement_score: float
    resolution_detected: bool


@dataclass
class SentimentTrajectory:
    scores: list[float]
    trend: str
    overall: float


@dataclass
class HandoffEffectiveness:
    total_handoffs: int
    successful_resolutions: int
    avg_messages_after_handoff: float
    effectiveness_rate: float


class ConversationAnalytics:
    def __init__(self) -> None:
        self._resolution_re = [re.compile(p, re.IGNORECASE) for p in RESOLUTION_PATTERNS]

    def analyze(self, messages: list[dict[str, str]]) -> ConversationMetrics:
        if not messages:
            return ConversationMetrics(
                message_count=0,
                avg_response_length=0.0,
                user_message_ratio=0.0,
                avg_sentiment=0.0,
                topic_drift_score=0.0,
                engagement_score=0.0,
                resolution_detected=False,
            )
        n = len(messages)
        user_msgs = [m for m in messages if m.get("role") == "user"]
        lengths = [len(m.get("content", "")) for m in messages]
        sentiments = [self._score_sentiment(m.get("content", "")) for m in messages]

        return ConversationMetrics(
            message_count=n,
            avg_response_length=sum(lengths) / n if n else 0.0,
            user_message_ratio=len(user_msgs) / n if n else 0.0,
            avg_sentiment=sum(sentiments) / n if n else 0.0,
            topic_drift_score=self.detect_topic_drift(messages),
            engagement_score=self.engagement_score(messages),
            resolution_detected=self.detect_resolution(messages),
        )

    def sentiment_trajectory(self, messages: list[dict[str, str]]) -> SentimentTrajectory:
        if not messages:
            return SentimentTrajectory(scores=[], trend="stable", overall=0.0)
        scores = [self._score_sentiment(m.get("content", "")) for m in messages]
        overall = sum(scores) / len(scores)
        trend = self._compute_trend(scores)
        return SentimentTrajectory(scores=scores, trend=trend, overall=overall)

    def detect_topic_drift(self, messages: list[dict[str, str]]) -> float:
        if len(messages) < 2:
            return 0.0
        texts = [m.get("content", "") for m in messages]
        mid = len(texts) // 2
        first_half = " ".join(texts[:mid])
        second_half = " ".join(texts[mid:])
        if not first_half.strip() or not second_half.strip():
            return 0.0
        return self._tfidf_drift(first_half, second_half)

    def engagement_score(self, messages: list[dict[str, str]]) -> float:
        if not messages:
            return 0.0
        user_msgs = [m for m in messages if m.get("role") == "user"]
        if not user_msgs:
            return 0.0

        avg_len = sum(len(m.get("content", "")) for m in user_msgs) / len(user_msgs)
        length_score = min(avg_len / 100.0, 1.0)

        question_count = sum(1 for m in user_msgs if "?" in m.get("content", ""))
        question_score = min(question_count / max(len(user_msgs), 1), 1.0)

        ratio = len(user_msgs) / len(messages)
        ratio_score = min(ratio / 0.6, 1.0)

        return length_score * 0.4 + question_score * 0.3 + ratio_score * 0.3

    def detect_resolution(self, messages: list[dict[str, str]]) -> bool:
        if not messages:
            return False
        last_msgs = messages[-3:] if len(messages) >= 3 else messages
        for m in last_msgs:
            content = m.get("content", "").lower()
            for pat in self._resolution_re:
                if pat.search(content):
                    return True
        return False

    def handoff_effectiveness(
        self,
        conversations: list[list[dict[str, str]]],
        handoff_indices: list[int],
    ) -> HandoffEffectiveness:
        if not conversations:
            return HandoffEffectiveness(
                total_handoffs=0,
                successful_resolutions=0,
                avg_messages_after_handoff=0.0,
                effectiveness_rate=0.0,
            )
        total = len(conversations)
        resolutions = 0
        msgs_after: list[int] = []
        for conv, idx in zip(conversations, handoff_indices):
            after = conv[idx + 1 :] if idx + 1 < len(conv) else []
            msgs_after.append(len(after))
            if self.detect_resolution(after):
                resolutions += 1

        avg = sum(msgs_after) / total if total else 0.0
        return HandoffEffectiveness(
            total_handoffs=total,
            successful_resolutions=resolutions,
            avg_messages_after_handoff=avg,
            effectiveness_rate=resolutions / total if total else 0.0,
        )

    def quality_score(self, messages: list[dict[str, str]]) -> float:
        if not messages:
            return 0.0
        metrics = self.analyze(messages)
        sentiment_norm = (metrics.avg_sentiment + 1) / 2
        drift_score = 1.0 - metrics.topic_drift_score
        resolution_bonus = 0.2 if metrics.resolution_detected else 0.0
        raw = sentiment_norm * 0.25 + metrics.engagement_score * 0.25 + drift_score * 0.25 + resolution_bonus + 0.05
        return max(0.0, min(1.0, raw))

    def batch_analyze(self, conversations: list[list[dict[str, str]]]) -> list[ConversationMetrics]:
        return [self.analyze(conv) for conv in conversations]

    def _score_sentiment(self, text: str) -> float:
        words = set(re.findall(r"\b[a-z]+\b", text.lower()))
        pos = len(words & POSITIVE_WORDS)
        neg = len(words & NEGATIVE_WORDS)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    def _compute_trend(self, scores: list[float]) -> str:
        if len(scores) < 2:
            return "stable"
        first_half = scores[: len(scores) // 2] or scores[:1]
        second_half = scores[len(scores) // 2 :] or scores[-1:]
        avg_first = sum(first_half) / len(first_half)
        avg_second = sum(second_half) / len(second_half)
        diff = avg_second - avg_first
        if diff > 0.1:
            return "improving"
        if diff < -0.1:
            return "declining"
        return "stable"

    def _tfidf_drift(self, text_a: str, text_b: str) -> float:
        try:
            vectorizer = TfidfVectorizer()
            matrix = vectorizer.fit_transform([text_a, text_b])
            vec_a = matrix[0].toarray().flatten()
            vec_b = matrix[1].toarray().flatten()
            dot = sum(a * b for a, b in zip(vec_a, vec_b))
            norm_a = math.sqrt(sum(a * a for a in vec_a))
            norm_b = math.sqrt(sum(b * b for b in vec_b))
            if norm_a == 0 or norm_b == 0:
                return 1.0
            cosine_sim = dot / (norm_a * norm_b)
            return 1.0 - cosine_sim
        except Exception:
            return self._word_overlap_drift(text_a, text_b)

    def _word_overlap_drift(self, text_a: str, text_b: str) -> float:
        words_a = set(re.findall(r"\b[a-z]+\b", text_a.lower()))
        words_b = set(re.findall(r"\b[a-z]+\b", text_b.lower()))
        if not words_a or not words_b:
            return 1.0
        overlap = len(words_a & words_b)
        union = len(words_a | words_b)
        return 1.0 - (overlap / union) if union else 1.0
