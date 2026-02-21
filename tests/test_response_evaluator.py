from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

import pytest

"""Tests for Jorge Response Evaluator."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ghl_real_estate_ai.services.jorge.response_evaluator import (
    TONE_PROFILES,
    ResponseEvaluator,
    ResponseScore,
    VariantComparison,
)

# ---------------------------------------------------------------------------
# ResponseScore dataclass
# ---------------------------------------------------------------------------


class TestResponseScore:
    def test_create_score(self):
        score = ResponseScore(coherence=0.8, relevance=0.9, completeness=0.7, tone_match=0.6, overall=0.75)
        assert score.coherence == 0.8
        assert score.relevance == 0.9
        assert score.completeness == 0.7
        assert score.tone_match == 0.6
        assert score.overall == 0.75

    def test_score_range(self):
        score = ResponseScore(coherence=0.0, relevance=0.0, completeness=0.0, tone_match=0.0, overall=0.0)
        assert score.overall == 0.0

    def test_perfect_score(self):
        score = ResponseScore(coherence=1.0, relevance=1.0, completeness=1.0, tone_match=1.0, overall=1.0)
        assert score.overall == 1.0


# ---------------------------------------------------------------------------
# Coherence scoring
# ---------------------------------------------------------------------------


class TestScoreCoherence:
    def setup_method(self):
        self.evaluator = ResponseEvaluator()

    def test_empty_response(self):
        assert self.evaluator.score_coherence("") == 0.0

    def test_whitespace_only(self):
        assert self.evaluator.score_coherence("   ") == 0.0

    def test_single_short_sentence(self):
        score = self.evaluator.score_coherence("Hi.")
        assert 0.0 < score < 1.0

    def test_single_sentence(self):
        score = self.evaluator.score_coherence("The market analysis shows strong growth potential for this area.")
        assert score == 0.7

    def test_multi_sentence_with_transitions(self):
        response = (
            "The property values have increased. Furthermore, demand remains strong. "
            "Therefore, now is a good time to invest."
        )
        score = self.evaluator.score_coherence(response)
        assert score > 0.5

    def test_duplicate_sentences_lower_score(self):
        response = "Great property. Great property. Great property."
        score = self.evaluator.score_coherence(response)
        # Duplicate sentences should reduce score
        unique_response = "Great property. Good location. Nice price."
        unique_score = self.evaluator.score_coherence(unique_response)
        assert score < unique_score

    def test_no_punctuation(self):
        # Text without punctuation is treated as a single sentence
        score = self.evaluator.score_coherence("some text without any punctuation at all")
        assert score == 0.7

    def test_score_between_0_and_1(self):
        response = (
            "First, let me review the data. Additionally, market trends are positive. "
            "Moreover, comparable sales support this valuation."
        )
        score = self.evaluator.score_coherence(response)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Relevance scoring
# ---------------------------------------------------------------------------


class TestScoreRelevance:
    def setup_method(self):
        self.evaluator = ResponseEvaluator()

    def test_empty_query(self):
        assert self.evaluator.score_relevance("", "Some response") == 0.0

    def test_empty_response(self):
        assert self.evaluator.score_relevance("What is the price?", "") == 0.0

    def test_high_overlap(self):
        query = "What is the price of the house?"
        response = "The price of the house is $500,000 based on recent comparable sales."
        score = self.evaluator.score_relevance(query, response)
        assert score > 0.5

    def test_no_overlap(self):
        query = "Tell me about the weather"
        response = "Our financing options include various mortgage types."
        score = self.evaluator.score_relevance(query, response)
        assert score < 0.5

    def test_partial_overlap(self):
        query = "What about the neighborhood schools?"
        response = "The neighborhood has several highly-rated elementary schools."
        score = self.evaluator.score_relevance(query, response)
        assert score > 0.3

    def test_score_between_0_and_1(self):
        score = self.evaluator.score_relevance("budget question", "budget answer here")
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# Completeness scoring
# ---------------------------------------------------------------------------


class TestScoreCompleteness:
    def setup_method(self):
        self.evaluator = ResponseEvaluator()

    def test_empty_response(self):
        assert self.evaluator.score_completeness("query", "") == 0.0

    def test_with_key_points_all_covered(self):
        response = "The price is $500K. The lot size is 5000 sqft. It has 3 bedrooms."
        key_points = ["price", "lot size", "bedrooms"]
        score = self.evaluator.score_completeness("details?", response, key_points)
        assert score == 1.0

    def test_with_key_points_partial(self):
        response = "The price is $500K."
        key_points = ["price", "lot size", "bedrooms"]
        score = self.evaluator.score_completeness("details?", response, key_points)
        assert 0.3 <= score <= 0.4  # 1 out of 3

    def test_with_key_points_none_covered(self):
        response = "I can help you with that."
        key_points = ["price", "lot size", "bedrooms"]
        score = self.evaluator.score_completeness("details?", response, key_points)
        assert score == 0.0

    def test_no_key_points_long_response(self):
        response = (
            "The property features an open floor plan with modern finishes. "
            "The kitchen was recently renovated with granite countertops. "
            "The backyard is spacious and well-maintained."
        )
        score = self.evaluator.score_completeness("Tell me about this property?", response)
        assert score > 0.5

    def test_no_key_points_short_response(self):
        score = self.evaluator.score_completeness("Tell me everything", "Ok.")
        assert score < 0.3


# ---------------------------------------------------------------------------
# Tone scoring
# ---------------------------------------------------------------------------


class TestScoreTone:
    def setup_method(self):
        self.evaluator = ResponseEvaluator()

    def test_empty_response(self):
        assert self.evaluator.score_tone("", "lead") == 0.0

    def test_lead_professional_tone(self):
        response = (
            "Based on our market analysis and data, I recommend evaluating "
            "this investment opportunity. The performance metrics are strong."
        )
        score = self.evaluator.score_tone(response, "lead")
        assert score > 0.5

    def test_buyer_warm_tone(self):
        response = (
            "How exciting! I understand how you feel about finding your dream home. "
            "I'm happy to help you on this wonderful journey together."
        )
        score = self.evaluator.score_tone(response, "buyer")
        assert score > 0.5

    def test_seller_confident_tone(self):
        response = (
            "Your property is in a strong competitive position. I'm confident "
            "we can maximize your equity with the right pricing strategy."
        )
        score = self.evaluator.score_tone(response, "seller")
        assert score > 0.5

    def test_unknown_bot_type(self):
        score = self.evaluator.score_tone("Some response text here.", "unknown_bot")
        assert score == 0.5

    def test_anti_keywords_reduce_score(self):
        # "awesome" and "totally" are anti-keywords for lead bot
        response_clean = "Based on our market analysis and data, the metrics look good."
        response_anti = "Awesome! Totally gonna check the market data."
        score_clean = self.evaluator.score_tone(response_clean, "lead")
        score_anti = self.evaluator.score_tone(response_anti, "lead")
        assert score_clean > score_anti


# ---------------------------------------------------------------------------
# Full evaluation
# ---------------------------------------------------------------------------


class TestEvaluate:
    def setup_method(self):
        self.evaluator = ResponseEvaluator()

    def test_basic_evaluation(self):
        query = "What is this property worth?"
        response = (
            "Based on our market analysis, comparable properties in the area "
            "indicate a value of approximately $500,000. Furthermore, recent "
            "data shows strong market performance in this neighborhood."
        )
        score = self.evaluator.evaluate(query, response, bot_type="lead")
        assert isinstance(score, ResponseScore)
        assert 0.0 <= score.overall <= 1.0
        assert 0.0 <= score.coherence <= 1.0
        assert 0.0 <= score.relevance <= 1.0
        assert 0.0 <= score.completeness <= 1.0
        assert 0.0 <= score.tone_match <= 1.0

    def test_empty_response_low_scores(self):
        score = self.evaluator.evaluate("What is the price?", "")
        assert score.overall == 0.0
        assert score.coherence == 0.0
        assert score.relevance == 0.0

    def test_overall_is_weighted_average(self):
        query = "What is this worth?"
        response = (
            "Based on market data and analysis, this property is valued at $500K. "
            "Additionally, the investment opportunity shows strong metrics."
        )
        score = self.evaluator.evaluate(query, response, bot_type="lead")
        expected = score.coherence * 0.25 + score.relevance * 0.30 + score.completeness * 0.25 + score.tone_match * 0.20
        assert abs(score.overall - round(expected, 4)) < 0.001

    def test_with_key_points(self):
        query = "Property details?"
        response = "The price is $500K and it has 3 bedrooms."
        key_points = ["price", "bedrooms"]
        score = self.evaluator.evaluate(query, response, bot_type="lead", key_points=key_points)
        assert score.completeness == 1.0

    def test_default_bot_type_is_lead(self):
        score = self.evaluator.evaluate(
            "market analysis?",
            "The market data shows strong performance metrics and analysis results.",
        )
        # Default is lead, should still work
        assert isinstance(score, ResponseScore)


# ---------------------------------------------------------------------------
# Tone profiles
# ---------------------------------------------------------------------------


class TestToneProfiles:
    def test_all_profiles_exist(self):
        assert "lead" in TONE_PROFILES
        assert "buyer" in TONE_PROFILES
        assert "seller" in TONE_PROFILES

    def test_profiles_have_keywords(self):
        for bot_type, profile in TONE_PROFILES.items():
            assert "keywords" in profile, f"Missing keywords for {bot_type}"
            assert "anti_keywords" in profile, f"Missing anti_keywords for {bot_type}"
            assert len(profile["keywords"]) > 0
