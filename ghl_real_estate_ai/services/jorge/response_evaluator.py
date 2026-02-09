"""
Jorge Response Evaluator

Automated bot response quality scoring across multiple dimensions:
coherence, relevance, completeness, and tone matching. Each bot type
(lead, buyer, seller) has a distinct tone profile used for evaluation.

Integrates with ``ABTestingService`` for variant-level quality comparison
so that A/B experiments can include response quality as a tracked metric.

Usage:
    evaluator = ResponseEvaluator()
    score = evaluator.evaluate("What's my budget?", "Based on ...", bot_type="buyer")
    print(score.overall)  # 0.0 - 1.0

    # Compare A/B variants
    comparison = evaluator.compare_variants(
        experiment_id="greeting_style",
        scores_a=[0.85, 0.90, 0.88],
        scores_b=[0.78, 0.80, 0.82],
    )
"""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ResponseScore:
    """Quality scores for a single bot response."""

    coherence: float
    relevance: float
    completeness: float
    tone_match: float
    overall: float
    bot_type: str = ""
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dictionary."""
        return {
            "coherence": round(self.coherence, 4),
            "relevance": round(self.relevance, 4),
            "completeness": round(self.completeness, 4),
            "tone_match": round(self.tone_match, 4),
            "overall": round(self.overall, 4),
            "bot_type": self.bot_type,
            "details": self.details,
        }


@dataclass
class VariantComparison:
    """Result of comparing two A/B test variant quality scores."""

    variant_a_mean: float = 0.0
    variant_b_mean: float = 0.0
    difference: float = 0.0
    p_value: Optional[float] = None
    is_significant: bool = False
    recommended_variant: Optional[str] = None


# ── Tone Profiles ──────────────────────────────────────────────────────

# Each profile contains keywords/phrases characteristic of the bot's
# desired personality plus a description for documentation.
TONE_PROFILES: Dict[str, Dict[str, object]] = {
    "lead": {
        "description": "Professional, formal language, data-driven",
        "keywords": [
            "market", "data", "analysis", "statistics", "report",
            "opportunity", "investment", "portfolio", "assessment",
            "recommend", "evaluate", "metrics", "performance",
            "professional", "accordingly", "furthermore", "regarding",
        ],
        "anti_keywords": [
            "awesome", "super", "totally", "gonna", "wanna",
        ],
    },
    "buyer": {
        "description": "Warm, empathetic, encouraging",
        "keywords": [
            "exciting", "wonderful", "congratulations", "happy",
            "understand", "feel", "help", "together", "dream",
            "home", "perfect", "love", "welcome", "great",
            "support", "journey", "absolutely", "fantastic",
        ],
        "anti_keywords": [
            "unfortunately", "impossible", "cannot", "denied",
        ],
    },
    "seller": {
        "description": "Confident, assertive, market-savvy",
        "keywords": [
            "market", "value", "competitive", "advantage", "equity",
            "demand", "pricing", "strategy", "position", "leverage",
            "maximize", "strong", "confident", "results", "proven",
            "negotiate", "offer", "premium", "exclusive",
        ],
        "anti_keywords": [
            "maybe", "perhaps", "uncertain", "possibly", "might",
        ],
    },
}

_SENTENCE_ENDINGS = re.compile(r"[.!?]+")


class ResponseEvaluator:
    """Evaluates bot response quality across multiple dimensions."""

    def __init__(self) -> None:
        self._tone_profiles = dict(TONE_PROFILES)
        logger.info("ResponseEvaluator initialized with %d tone profiles", len(self._tone_profiles))

    # ── Coherence ──────────────────────────────────────────────────────

    def score_coherence(self, response: str) -> float:
        """Measure sentence flow and logical consistency.

        Heuristics:
        - Sentence count and average length (very short or very long = lower score)
        - Transition word usage (indicates logical flow)
        - No repeated sentences (indicates copy-paste or loop)

        Args:
            response: The bot response text.

        Returns:
            Score between 0.0 and 1.0.
        """
        if not response or not response.strip():
            return 0.0

        text = response.strip()
        sentences = [s.strip() for s in _SENTENCE_ENDINGS.split(text) if s.strip()]

        if not sentences:
            return 0.3  # text with no sentence-ending punctuation

        # Single sentence gets a baseline score
        if len(sentences) == 1:
            word_count = len(sentences[0].split())
            if word_count < 3:
                return 0.3
            return 0.7

        # --- Sub-scores ---

        # 1. Sentence length consistency (std-dev of word counts)
        word_counts = [len(s.split()) for s in sentences]
        mean_wc = sum(word_counts) / len(word_counts)
        variance = sum((wc - mean_wc) ** 2 for wc in word_counts) / len(word_counts)
        std_dev = math.sqrt(variance)
        # Low std-dev relative to mean → high score
        length_score = max(0.0, 1.0 - (std_dev / max(mean_wc, 1.0)) * 0.5)

        # 2. Transition words
        transition_words = {
            "additionally", "also", "furthermore", "moreover", "however",
            "therefore", "consequently", "meanwhile", "specifically",
            "for example", "in addition", "as a result", "on the other hand",
            "first", "second", "third", "finally", "next", "then",
        }
        lower_text = text.lower()
        transition_count = sum(1 for tw in transition_words if tw in lower_text)
        transition_score = min(1.0, transition_count / max(1, len(sentences) - 1))

        # 3. No duplicate sentences
        unique_ratio = len(set(s.lower() for s in sentences)) / len(sentences)

        coherence = (
            length_score * 0.35
            + transition_score * 0.30
            + unique_ratio * 0.35
        )
        return round(max(0.0, min(1.0, coherence)), 4)

    # ── Relevance ──────────────────────────────────────────────────────

    def score_relevance(self, query: str, response: str) -> float:
        """Measure query-response keyword/semantic overlap.

        Uses normalized token overlap (Jaccard-like) between query and
        response words, weighted toward query coverage.

        Args:
            query: The user's query text.
            response: The bot response text.

        Returns:
            Score between 0.0 and 1.0.
        """
        if not query or not query.strip() or not response or not response.strip():
            return 0.0

        query_tokens = self._tokenize(query)
        response_tokens = self._tokenize(response)

        if not query_tokens:
            return 0.0

        # What fraction of query tokens appear in the response?
        overlap = query_tokens & response_tokens
        query_coverage = len(overlap) / len(query_tokens)

        # Bonus for response length being reasonable relative to query
        length_ratio = len(response_tokens) / max(len(query_tokens), 1)
        length_bonus = min(1.0, length_ratio / 3.0)  # at 3x query length, full bonus

        relevance = query_coverage * 0.7 + length_bonus * 0.3
        return round(max(0.0, min(1.0, relevance)), 4)

    # ── Completeness ───────────────────────────────────────────────────

    def score_completeness(
        self,
        query: str,
        response: str,
        key_points: Optional[List[str]] = None,
    ) -> float:
        """Check if key points are addressed in the response.

        If key_points are provided, measures how many are covered.
        Otherwise, uses a heuristic based on response length and structure.

        Args:
            query: The user's query text.
            response: The bot response text.
            key_points: Optional list of expected key points.

        Returns:
            Score between 0.0 and 1.0.
        """
        if not response or not response.strip():
            return 0.0

        if key_points:
            if not key_points:
                return 1.0

            response_lower = response.lower()
            covered = sum(
                1 for kp in key_points
                if kp.lower() in response_lower
            )
            return round(covered / len(key_points), 4)

        # Heuristic: longer, structured responses are more complete
        sentences = [s.strip() for s in _SENTENCE_ENDINGS.split(response) if s.strip()]
        sentence_count = max(len(sentences), 1)

        # At least 2 sentences for a reasonable answer
        sentence_score = min(1.0, sentence_count / 3.0)

        # Word count heuristic — at least 20 words for completeness
        word_count = len(response.split())
        word_score = min(1.0, word_count / 30.0)

        completeness = sentence_score * 0.5 + word_score * 0.5
        return round(max(0.0, min(1.0, completeness)), 4)

    # ── Tone ───────────────────────────────────────────────────────────

    def score_tone(self, response: str, bot_type: str) -> float:
        """Match response against bot personality profile.

        Args:
            response: The bot response text.
            bot_type: One of 'lead', 'buyer', 'seller'.

        Returns:
            Score between 0.0 and 1.0.
        """
        if not response or not response.strip():
            return 0.0

        profile = self._tone_profiles.get(bot_type)
        if profile is None:
            logger.warning("Unknown bot_type '%s', returning neutral score", bot_type)
            return 0.5

        keywords: list = profile["keywords"]  # type: ignore[assignment]
        anti_keywords: list = profile["anti_keywords"]  # type: ignore[assignment]

        response_lower = response.lower()
        response_words = set(response_lower.split())

        # Keyword presence
        keyword_hits = sum(1 for kw in keywords if kw in response_lower)
        keyword_score = min(1.0, keyword_hits / max(3, len(keywords) * 0.3))

        # Anti-keyword penalty
        anti_hits = sum(1 for akw in anti_keywords if akw in response_words)
        anti_penalty = min(0.4, anti_hits * 0.15)

        tone = keyword_score - anti_penalty
        return round(max(0.0, min(1.0, tone)), 4)

    # ── A/B Testing Integration ───────────────────────────────────────

    def compare_variants(
        self,
        experiment_id: str,
        scores_a: List[float],
        scores_b: List[float],
        alpha: float = 0.05,
    ) -> VariantComparison:
        """Compare response quality between two A/B variants.

        Uses a two-sample z-test on overall quality scores.

        Args:
            experiment_id: A/B experiment identifier (for logging).
            scores_a: Quality scores for variant A.
            scores_b: Quality scores for variant B.
            alpha: Significance threshold (default 0.05).

        Returns:
            VariantComparison with means, p-value, and recommendation.
        """
        if not scores_a or not scores_b:
            return VariantComparison()

        mean_a = sum(scores_a) / len(scores_a)
        mean_b = sum(scores_b) / len(scores_b)
        diff = mean_a - mean_b

        p_value = self._two_sample_z_test(scores_a, scores_b)
        is_sig = p_value < alpha if p_value is not None else False

        recommended = None
        if is_sig:
            recommended = "A" if mean_a > mean_b else "B"

        comparison = VariantComparison(
            variant_a_mean=round(mean_a, 4),
            variant_b_mean=round(mean_b, 4),
            difference=round(diff, 4),
            p_value=round(p_value, 6) if p_value is not None else None,
            is_significant=is_sig,
            recommended_variant=recommended,
        )

        logger.info(
            "Variant comparison for '%s': A=%.3f B=%.3f diff=%.3f p=%s sig=%s",
            experiment_id,
            mean_a,
            mean_b,
            diff,
            f"{p_value:.4f}" if p_value is not None else "N/A",
            is_sig,
        )

        return comparison

    # ── Full Evaluation ────────────────────────────────────────────────

    def evaluate(
        self,
        query: str,
        response: str,
        bot_type: str = "lead",
        key_points: Optional[List[str]] = None,
    ) -> ResponseScore:
        """Run full evaluation across all dimensions.

        Weights:
        - Coherence: 25%
        - Relevance: 30%
        - Completeness: 25%
        - Tone match: 20%

        Args:
            query: The user's query text.
            response: The bot response text.
            bot_type: One of 'lead', 'buyer', 'seller'.
            key_points: Optional list of expected key points.

        Returns:
            ResponseScore with all individual scores and weighted overall.
        """
        coherence = self.score_coherence(response)
        relevance = self.score_relevance(query, response)
        completeness = self.score_completeness(query, response, key_points)
        tone_match = self.score_tone(response, bot_type)

        overall = (
            coherence * 0.25
            + relevance * 0.30
            + completeness * 0.25
            + tone_match * 0.20
        )

        return ResponseScore(
            coherence=coherence,
            relevance=relevance,
            completeness=completeness,
            tone_match=tone_match,
            overall=round(overall, 4),
            bot_type=bot_type,
            details={
                "query_length": len(query),
                "response_length": len(response),
                "key_points_requested": len(key_points or []),
            },
        )

    # ── Internal Helpers ───────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        """Lowercase tokenization with stopword removal."""
        stopwords = {
            "a", "an", "the", "is", "are", "was", "were", "be", "been",
            "being", "have", "has", "had", "do", "does", "did", "will",
            "would", "could", "should", "may", "might", "shall", "can",
            "to", "of", "in", "for", "on", "with", "at", "by", "from",
            "as", "into", "about", "between", "through", "during",
            "and", "but", "or", "nor", "not", "so", "yet", "both",
            "i", "me", "my", "we", "our", "you", "your", "it", "its",
            "this", "that", "these", "those", "what", "which", "who",
        }
        words = set(re.sub(r"[^a-z0-9\s]", "", text.lower()).split())
        return words - stopwords

    @staticmethod
    def _two_sample_z_test(
        sample_a: List[float],
        sample_b: List[float],
    ) -> Optional[float]:
        """Two-sample z-test for means, returning a two-sided p-value.

        Uses normal approximation.  Returns None when variance is zero
        or samples are too small.

        Args:
            sample_a: Observations for group A.
            sample_b: Observations for group B.

        Returns:
            Two-sided p-value (0-1) or None if test is not applicable.
        """
        n1, n2 = len(sample_a), len(sample_b)
        if n1 < 2 or n2 < 2:
            return None

        mean1 = sum(sample_a) / n1
        mean2 = sum(sample_b) / n2

        var1 = sum((x - mean1) ** 2 for x in sample_a) / (n1 - 1)
        var2 = sum((x - mean2) ** 2 for x in sample_b) / (n2 - 1)

        se = math.sqrt(var1 / n1 + var2 / n2)
        if se == 0:
            return None

        z = abs(mean1 - mean2) / se
        p_value = math.erfc(z / math.sqrt(2))
        return p_value
