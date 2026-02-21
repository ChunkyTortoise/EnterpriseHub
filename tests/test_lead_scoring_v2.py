"""
Tests for Lead Scoring v2 Service

This module contains tests for the composite lead scoring system.
"""

import pytest

from ghl_real_estate_ai.services.lead_scoring_v2 import (
    CompositeScore,
    LeadClassification,
    LeadScoringServiceV2,
    ScoreHistory,
)


@pytest.fixture
def scoring_service():
    """Create a LeadScoringServiceV2 instance for testing."""
    return LeadScoringServiceV2()


class TestCompositeScoreCalculation:
    """Tests for composite score calculation."""

    @pytest.mark.asyncio
    async def test_hot_lead_classification(self, scoring_service):
        """Test that high scores result in hot lead classification."""
        result = await scoring_service.calculate_composite_score(
            frs_score=85,
            pcs_score=90,
            sentiment_score=80,
            engagement_score=75,
            data_completeness=90,
            conversation_depth=80,
        )

        assert result.classification == LeadClassification.HOT
        assert result.total_score >= 80
        assert result.total_score <= 100

    @pytest.mark.asyncio
    async def test_warm_lead_classification(self, scoring_service):
        """Test that medium-high scores result in warm lead classification."""
        result = await scoring_service.calculate_composite_score(
            frs_score=70,
            pcs_score=75,
            sentiment_score=65,
            engagement_score=60,
            data_completeness=70,
            conversation_depth=60,
        )

        assert result.classification == LeadClassification.WARM
        assert result.total_score >= 60
        assert result.total_score < 80

    @pytest.mark.asyncio
    async def test_lukewarm_lead_classification(self, scoring_service):
        """Test that medium scores result in lukewarm lead classification."""
        result = await scoring_service.calculate_composite_score(
            frs_score=50,
            pcs_score=55,
            sentiment_score=45,
            engagement_score=40,
            data_completeness=50,
            conversation_depth=40,
        )

        assert result.classification == LeadClassification.LUKEWARM
        assert result.total_score >= 40
        assert result.total_score < 60

    @pytest.mark.asyncio
    async def test_cold_lead_classification(self, scoring_service):
        """Test that low scores result in cold lead classification."""
        result = await scoring_service.calculate_composite_score(
            frs_score=30,
            pcs_score=35,
            sentiment_score=25,
            engagement_score=20,
            data_completeness=30,
            conversation_depth=20,
        )

        assert result.classification == LeadClassification.COLD
        assert result.total_score >= 20
        assert result.total_score < 40

    @pytest.mark.asyncio
    async def test_unqualified_lead_classification(self, scoring_service):
        """Test that very low scores result in unqualified lead classification."""
        result = await scoring_service.calculate_composite_score(
            frs_score=10,
            pcs_score=15,
            sentiment_score=5,
            engagement_score=0,
            data_completeness=10,
            conversation_depth=5,
        )

        assert result.classification == LeadClassification.UNQUALIFIED
        assert result.total_score < 20

    @pytest.mark.asyncio
    async def test_composite_score_formula(self, scoring_service):
        """Test that composite score is calculated using the correct formula."""
        result = await scoring_service.calculate_composite_score(
            frs_score=80,
            pcs_score=70,
            sentiment_score=60,
            engagement_score=50,
            data_completeness=80,
            conversation_depth=80,
        )

        # Expected: (80 * 0.40) + (70 * 0.35) + (60 * 0.15) + (50 * 0.10)
        # Expected: 32 + 24.5 + 9 + 5 = 70.5
        expected_score = 70.5
        assert abs(result.total_score - expected_score) < 0.01

    @pytest.mark.asyncio
    async def test_score_clamping(self, scoring_service):
        """Test that scores are clamped to 0-100 range."""
        # Test upper bound
        result = await scoring_service.calculate_composite_score(
            frs_score=150,
            pcs_score=150,
            sentiment_score=150,
            engagement_score=150,
            data_completeness=100,
            conversation_depth=100,
        )
        assert result.total_score <= 100

        # Test lower bound
        result = await scoring_service.calculate_composite_score(
            frs_score=-50,
            pcs_score=-50,
            sentiment_score=-50,
            engagement_score=-50,
            data_completeness=0,
            conversation_depth=0,
        )
        assert result.total_score >= 0


class TestConfidenceIntervals:
    """Tests for confidence interval calculation."""

    @pytest.mark.asyncio
    async def test_confidence_interval_calculation(self, scoring_service):
        """Test that confidence intervals are calculated correctly."""
        result = await scoring_service.calculate_composite_score(
            frs_score=50,
            pcs_score=50,
            sentiment_score=50,
            engagement_score=50,
            data_completeness=60,
            conversation_depth=50,
        )

        lower, upper = result.confidence_interval
        assert lower < result.total_score < upper
        assert (upper - lower) <= 50  # Max interval width

    @pytest.mark.asyncio
    async def test_high_confidence_narrow_interval(self, scoring_service):
        """Test that high confidence results in narrow confidence interval."""
        result = await scoring_service.calculate_composite_score(
            frs_score=50,
            pcs_score=50,
            sentiment_score=50,
            engagement_score=50,
            data_completeness=90,
            conversation_depth=90,
        )

        lower, upper = result.confidence_interval
        interval_width = upper - lower
        assert interval_width < 20  # Narrow interval for high confidence

    @pytest.mark.asyncio
    async def test_low_confidence_wide_interval(self, scoring_service):
        """Test that low confidence results in wide confidence interval."""
        result = await scoring_service.calculate_composite_score(
            frs_score=50,
            pcs_score=50,
            sentiment_score=50,
            engagement_score=50,
            data_completeness=20,
            conversation_depth=20,
        )

        lower, upper = result.confidence_interval
        interval_width = upper - lower
        assert interval_width > 30  # Wide interval for low confidence


class TestCustomWeights:
    """Tests for custom weight functionality."""

    @pytest.mark.asyncio
    async def test_custom_weights(self, scoring_service):
        """Test that custom weights are applied correctly."""
        custom_weights = {
            "frs": 0.50,
            "pcs": 0.30,
            "sentiment": 0.10,
            "engagement": 0.10,
        }

        result = await scoring_service.calculate_composite_score(
            frs_score=80,
            pcs_score=60,
            sentiment_score=50,
            engagement_score=50,
            data_completeness=80,
            conversation_depth=80,
            custom_weights=custom_weights,
        )

        assert result.scoring_weights == custom_weights

        # Expected: (80 * 0.50) + (60 * 0.30) + (50 * 0.10) + (50 * 0.10)
        # Expected: 40 + 18 + 5 + 5 = 68
        expected_score = 68.0
        assert abs(result.total_score - expected_score) < 0.01

    @pytest.mark.asyncio
    async def test_weight_normalization(self, scoring_service):
        """Test that weights are normalized if they don't sum to 1.0."""
        custom_weights = {
            "frs": 0.5,
            "pcs": 0.3,
            "sentiment": 0.1,
            "engagement": 0.1,
        }

        result = await scoring_service.calculate_composite_score(
            frs_score=50,
            pcs_score=50,
            sentiment_score=50,
            engagement_score=50,
            data_completeness=50,
            conversation_depth=50,
            custom_weights=custom_weights,
        )

        # Weights should be normalized
        weight_sum = sum(result.scoring_weights.values())
        assert abs(weight_sum - 1.0) < 0.01


class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_zero_scores(self, scoring_service):
        """Test handling of zero scores."""
        result = await scoring_service.calculate_composite_score(
            frs_score=0, pcs_score=0, sentiment_score=0, engagement_score=0, data_completeness=0, conversation_depth=0
        )

        assert result.total_score == 0.0
        assert result.classification == LeadClassification.UNQUALIFIED

    @pytest.mark.asyncio
    async def test_perfect_scores(self, scoring_service):
        """Test handling of perfect scores."""
        result = await scoring_service.calculate_composite_score(
            frs_score=100,
            pcs_score=100,
            sentiment_score=100,
            engagement_score=100,
            data_completeness=100,
            conversation_depth=100,
        )

        assert result.total_score == 100.0
        assert result.classification == LeadClassification.HOT

    @pytest.mark.asyncio
    async def test_boundary_scores(self, scoring_service):
        """Test classification boundary scores."""
        # Test hot boundary (80)
        result = await scoring_service.calculate_composite_score(
            frs_score=80,
            pcs_score=80,
            sentiment_score=80,
            engagement_score=80,
            data_completeness=80,
            conversation_depth=80,
        )
        assert result.classification == LeadClassification.HOT

        # Test warm boundary (60)
        result = await scoring_service.calculate_composite_score(
            frs_score=60,
            pcs_score=60,
            sentiment_score=60,
            engagement_score=60,
            data_completeness=60,
            conversation_depth=60,
        )
        assert result.classification == LeadClassification.WARM

        # Test lukewarm boundary (40)
        result = await scoring_service.calculate_composite_score(
            frs_score=40,
            pcs_score=40,
            sentiment_score=40,
            engagement_score=40,
            data_completeness=40,
            conversation_depth=40,
        )
        assert result.classification == LeadClassification.LUKEWARM

        # Test cold boundary (20)
        result = await scoring_service.calculate_composite_score(
            frs_score=20,
            pcs_score=20,
            sentiment_score=20,
            engagement_score=20,
            data_completeness=20,
            conversation_depth=20,
        )
        assert result.classification == LeadClassification.COLD


class TestEngagementScoreCalculation:
    """Tests for engagement score calculation."""

    def test_engagement_score_empty_history(self, scoring_service):
        """Test engagement score with empty conversation history."""
        score = scoring_service._calculate_engagement_score([])
        assert score == 0.0

    def test_engagement_score_single_message(self, scoring_service):
        """Test engagement score with single message."""
        history = [{"role": "user", "content": "Hello"}]
        score = scoring_service._calculate_engagement_score(history)
        assert score > 0
        assert score <= 100

    def test_engagement_score_multiple_messages(self, scoring_service):
        """Test engagement score with multiple messages."""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
            {"role": "user", "content": "How are you?"},
        ]
        score = scoring_service._calculate_engagement_score(history)
        assert score > 0
        assert score <= 100

    def test_engagement_score_with_questions(self, scoring_service):
        """Test that questions increase engagement score."""
        history_with_questions = [
            {"role": "user", "content": "What is the price?"},
            {"role": "user", "content": "When can I see it?"},
        ]
        history_without_questions = [
            {"role": "user", "content": "I want to buy"},
            {"role": "user", "content": "Call me"},
        ]

        score_with_questions = scoring_service._calculate_engagement_score(history_with_questions)
        score_without_questions = scoring_service._calculate_engagement_score(history_without_questions)

        assert score_with_questions > score_without_questions


class TestDataCompletenessCalculation:
    """Tests for data completeness calculation."""

    def test_data_completeness_empty(self, scoring_service):
        """Test data completeness with empty lead data."""
        score = scoring_service._calculate_data_completeness({})
        assert score == 0.0

    def test_data_completeness_partial(self, scoring_service):
        """Test data completeness with partial data."""
        lead_data = {
            "frs_score": 50,
            "pcs_score": 60,
        }
        score = scoring_service._calculate_data_completeness(lead_data)
        assert score > 0
        assert score < 100

    def test_data_completeness_full(self, scoring_service):
        """Test data completeness with full data."""
        lead_data = {
            "frs_score": 50,
            "pcs_score": 60,
            "sentiment_score": 70,
            "budget": "500000",
            "timeline": "3 months",
            "preferences": "3 bedroom",
        }
        score = scoring_service._calculate_data_completeness(lead_data)
        assert score == 100.0


class TestUpdateLeadScore:
    """Tests for update_lead_score method."""

    @pytest.mark.asyncio
    async def test_update_lead_score_basic(self, scoring_service):
        """Test basic lead score update."""
        conversation_history = [
            {"role": "user", "content": "I'm looking to buy a house"},
        ]
        lead_data = {
            "frs_score": 70,
            "pcs_score": 75,
            "sentiment_score": 60,
        }

        result = await scoring_service.update_lead_score(
            contact_id="test-contact-1", conversation_history=conversation_history, lead_data=lead_data
        )

        assert result.total_score > 0
        assert result.classification in [
            LeadClassification.HOT,
            LeadClassification.WARM,
            LeadClassification.LUKEWARM,
            LeadClassification.COLD,
            LeadClassification.UNQUALIFIED,
        ]

    @pytest.mark.asyncio
    async def test_update_lead_score_with_empty_history(self, scoring_service):
        """Test lead score update with empty conversation history."""
        lead_data = {
            "frs_score": 50,
            "pcs_score": 50,
            "sentiment_score": 50,
        }

        result = await scoring_service.update_lead_score(
            contact_id="test-contact-2", conversation_history=[], lead_data=lead_data
        )

        # Should still calculate a score even with empty history
        assert result.total_score >= 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
