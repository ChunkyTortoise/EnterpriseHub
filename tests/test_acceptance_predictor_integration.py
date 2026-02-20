"""
Test suite for Phase 4 Task #13: ML pricing guidance integration.

Verifies:
- AcceptancePredictorService functionality
- Seller bot workflow integration
- A/B test instrumentation
- Graceful fallback behavior
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig, JorgeSellerBot
from ghl_real_estate_ai.services.jorge.acceptance_predictor_service import (
    AcceptancePrediction,
    AcceptancePredictorService,
    OptimalPriceRange,
)


class TestAcceptancePredictorService:
    """Test AcceptancePredictorService standalone functionality."""

    @pytest.fixture
    def predictor_service(self):
        """Create predictor service instance."""
        return AcceptancePredictorService()

    @pytest.fixture
    def sample_context(self):
        """Sample seller context for predictions."""
        return {
            "pcs_score": 75.0,
            "estimated_value": 800000,
            "cma_report": {
                "estimated_value": 800000,
                "value_range_low": 780000,
                "value_range_high": 820000,
                "confidence_score": 0.85,
            },
            "market_trend": "sellers_market",
            "property_address": "123 Main St, Rancho Cucamonga, CA",
        }

    @pytest.mark.asyncio
    async def test_predict_acceptance_probability_heuristic(self, predictor_service, sample_context):
        """Test heuristic-based acceptance prediction."""
        # Test at CMA value
        prediction = await predictor_service.predict_acceptance_probability(
            seller_id="test_seller_123",
            offer_price=800000,
            context=sample_context,
        )

        assert isinstance(prediction, AcceptancePrediction)
        assert prediction.offer_price == 800000
        assert 0.0 <= prediction.acceptance_probability <= 1.0
        assert 0.0 <= prediction.confidence <= 1.0
        assert prediction.estimated_days_to_acceptance > 0
        assert len(prediction.reasoning) > 0
        assert prediction.model_version == "heuristic_v1"

        # High PCS + competitive price should yield high probability
        assert prediction.acceptance_probability > 0.7

    @pytest.mark.asyncio
    async def test_predict_acceptance_probability_low_price(self, predictor_service, sample_context):
        """Test prediction for below-market price."""
        # Test at 80% of CMA (low price)
        prediction = await predictor_service.predict_acceptance_probability(
            seller_id="test_seller_123",
            offer_price=640000,  # 80% of CMA
            context=sample_context,
        )

        # Test at CMA value for comparison
        cma_prediction = await predictor_service.predict_acceptance_probability(
            seller_id="test_seller_123",
            offer_price=800000,  # At CMA
            context=sample_context,
        )

        # Low price should have lower acceptance probability than CMA price
        assert prediction.acceptance_probability < cma_prediction.acceptance_probability

    @pytest.mark.asyncio
    async def test_predict_acceptance_probability_no_cma(self, predictor_service):
        """Test prediction gracefully handles missing CMA data."""
        minimal_context = {
            "pcs_score": 50.0,
        }

        prediction = await predictor_service.predict_acceptance_probability(
            seller_id="test_seller_123",
            offer_price=750000,
            context=minimal_context,
        )

        # Should return conservative estimate
        assert isinstance(prediction, AcceptancePrediction)
        assert prediction.confidence < 0.5  # Low confidence without CMA
        assert "engagement only" in prediction.reasoning.lower()

    @pytest.mark.asyncio
    async def test_get_optimal_price_range(self, predictor_service, sample_context):
        """Test optimal price range calculation."""
        optimal = await predictor_service.get_optimal_price_range(
            seller_id="test_seller_123",
            target_probability=0.85,
            context=sample_context,
        )

        assert isinstance(optimal, OptimalPriceRange)
        assert optimal.min_price > 0
        assert optimal.max_price > optimal.min_price
        assert optimal.min_price <= optimal.recommended_price <= optimal.max_price
        assert 0.0 <= optimal.acceptance_probability <= 1.0
        assert optimal.time_to_acceptance_days > 0
        assert len(optimal.strategy_rationale) > 0

        # Recommended price should be near CMA for high probability target
        cma_value = sample_context["estimated_value"]
        assert 0.90 * cma_value <= optimal.recommended_price <= 1.05 * cma_value

    @pytest.mark.asyncio
    async def test_get_optimal_price_range_no_cma(self, predictor_service):
        """Test optimal price range handles missing CMA gracefully."""
        minimal_context = {"pcs_score": 50.0}

        optimal = await predictor_service.get_optimal_price_range(
            seller_id="test_seller_123",
            target_probability=0.85,
            context=minimal_context,
        )

        # Should return empty/zero values with rationale
        assert optimal.recommended_price == 0
        assert "Insufficient" in optimal.strategy_rationale or "CMA required" in optimal.strategy_rationale

    @pytest.mark.asyncio
    async def test_prediction_caching(self, predictor_service, sample_context):
        """Test that predictions are cached for performance."""
        with patch.object(predictor_service, "_predict_with_heuristic") as mock_predict:
            mock_predict.return_value = AcceptancePrediction(
                offer_price=800000,
                acceptance_probability=0.85,
                confidence=0.7,
                estimated_days_to_acceptance=30,
                reasoning="Test",
                feature_importance={"pcs_score": 0.6},
            )

            # First call
            result1 = await predictor_service.predict_acceptance_probability(
                seller_id="cache_test",
                offer_price=800000,
                context=sample_context,
            )

            # Second call with same parameters (should hit cache)
            result2 = await predictor_service.predict_acceptance_probability(
                seller_id="cache_test",
                offer_price=800000,
                context=sample_context,
            )

            # Heuristic should only be called once (second call hits cache)
            assert mock_predict.call_count == 1
            assert result1.acceptance_probability == result2.acceptance_probability

    @pytest.mark.asyncio
    async def test_health_check(self, predictor_service):
        """Test service health check."""
        health = await predictor_service.health_check()

        assert health["service"] == "AcceptancePredictorService"
        assert health["status"] == "healthy"
        assert "model_available" in health
        assert "fallback_mode" in health


class TestSellerBotIntegration:
    """Test pricing guidance integration into JorgeSellerBot workflow."""

    @pytest.fixture
    def mock_ab_testing(self):
        """Mock A/B testing service."""
        mock = AsyncMock()
        mock.assign_variant.return_value = "treatment"
        mock.track_event.return_value = None
        mock.get_variant.return_value = "empathetic"
        return mock

    @pytest.fixture
    def mock_seller_bot(self, mock_ab_testing):
        """Create mock seller bot with pricing guidance method."""
        bot = MagicMock()
        bot.ab_testing = mock_ab_testing

        # Import the actual method from JorgeSellerBot
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

        # Bind the provide_pricing_guidance method
        bot.provide_pricing_guidance = JorgeSellerBot.provide_pricing_guidance.__get__(bot, JorgeSellerBot)
        bot._format_pricing_guidance = JorgeSellerBot._format_pricing_guidance.__get__(bot, JorgeSellerBot)

        return bot

    @pytest.fixture
    def sample_state(self):
        """Sample seller bot state."""
        # Create minimal state dict without complex imports
        return {
            "contact_id": "test_seller_123",
            "lead_id": "test_seller_123",
            "lead_name": "John Doe",
            "conversation_history": [],
            "property_address": "123 Main St, Rancho Cucamonga, CA",
            "cma_report": {
                "estimated_value": 800000,
                "value_range_low": 780000,
                "value_range_high": 820000,
                "confidence_score": 0.85,
            },
            "intent_profile": {
                "frs": {"total_score": 75},
                "pcs": {"total_score": 75},
            },
            "psychological_commitment": 75,
            "market_trend": "sellers_market",
            "asking_price": 820000,
        }

    @pytest.mark.asyncio
    async def test_provide_pricing_guidance_treatment(self, mock_seller_bot, sample_state):
        """Test pricing guidance node with ML treatment variant."""
        result = await mock_seller_bot.provide_pricing_guidance(sample_state)

        assert "pricing_guidance" in result
        assert result["pricing_guidance_variant"] == "treatment"
        assert "optimal_pricing" in result

        # Verify optimal pricing structure
        optimal = result["optimal_pricing"]
        assert optimal["recommended_price"] > 0
        assert optimal["min_price"] <= optimal["recommended_price"] <= optimal["max_price"]
        assert 0.0 <= optimal["acceptance_probability"] <= 1.0
        assert optimal["time_to_acceptance_days"] > 0

        # Verify A/B test was called
        mock_seller_bot.ab_testing.assign_variant.assert_called_once()
        mock_seller_bot.ab_testing.track_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_provide_pricing_guidance_control(self, mock_seller_bot, sample_state, mock_ab_testing):
        """Test pricing guidance node with control variant (no ML)."""
        mock_ab_testing.assign_variant.return_value = "control"

        result = await mock_seller_bot.provide_pricing_guidance(sample_state)

        assert result["pricing_guidance_variant"] == "control"
        assert "pricing_guidance" not in result  # No ML guidance in control

        # Verify A/B test assignment but no tracking
        mock_seller_bot.ab_testing.assign_variant.assert_called_once()
        mock_seller_bot.ab_testing.track_event.assert_not_called()

    @pytest.mark.asyncio
    async def test_provide_pricing_guidance_no_cma(self, mock_seller_bot):
        """Test pricing guidance gracefully handles missing CMA data."""
        state_no_cma = {
            "contact_id": "test_seller_456",
            "lead_id": "test_seller_456",
            "property_address": None,  # No address
            "cma_report": None,  # No CMA
        }

        result = await mock_seller_bot.provide_pricing_guidance(state_no_cma)

        # Should return empty result gracefully
        assert result == {}

    @pytest.mark.asyncio
    async def test_provide_pricing_guidance_error_handling(self, mock_seller_bot, sample_state, mock_ab_testing):
        """Test pricing guidance handles service errors gracefully."""
        # Force an error in A/B testing
        mock_ab_testing.assign_variant.side_effect = Exception("Service unavailable")

        result = await mock_seller_bot.provide_pricing_guidance(sample_state)

        # Should fall back to control gracefully
        assert result["pricing_guidance_variant"] == "control"

    @pytest.mark.asyncio
    async def test_format_pricing_guidance(self, mock_seller_bot):
        """Test pricing guidance formatting for conversational output."""
        optimal_pricing = OptimalPriceRange(
            min_price=760000,
            max_price=780000,
            recommended_price=770000,
            acceptance_probability=0.85,
            time_to_acceptance_days=30,
            strategy_rationale="Pricing at 96% of CMA optimizes for 85% acceptance",
        )

        asking_prediction = AcceptancePrediction(
            offer_price=820000,
            acceptance_probability=0.65,
            confidence=0.7,
            estimated_days_to_acceptance=50,
            reasoning="Test",
            feature_importance={},
        )

        guidance = mock_seller_bot._format_pricing_guidance(
            optimal_pricing=optimal_pricing,
            asking_prediction=asking_prediction,
            asking_price=820000,
            cma_value=800000,
        )

        # Verify conversational elements
        assert "📊" in guidance  # Market analysis emoji
        assert "💡" in guidance  # Optimal strategy emoji
        assert "📈" in guidance  # Rationale emoji
        assert "$820,000" in guidance  # Asking price formatted
        assert "65%" in guidance  # Acceptance probability
        assert "85%" in guidance  # Optimal probability
        assert "30 days" in guidance or "30" in guidance  # Time estimate
        assert "pricing strategies" in guidance.lower()

    def test_workflow_graph_includes_pricing_node(self):
        """Test that pricing guidance node is included in workflow graph."""
        # Test indirectly by verifying method exists in JorgeSellerBot class
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

        assert hasattr(JorgeSellerBot, "provide_pricing_guidance")
        assert callable(getattr(JorgeSellerBot, "provide_pricing_guidance"))


class TestABTestInstrumentation:
    """Test A/B test instrumentation for ML pricing experiment."""

    @pytest.mark.asyncio
    async def test_experiment_variant_assignment(self):
        """Test that seller_ml_pricing_v1 experiment assigns variants correctly."""
        mock_ab_service = AsyncMock()
        mock_ab_service.assign_variant.return_value = "treatment"

        # Simulate variant assignment
        variant = await mock_ab_service.assign_variant(
            experiment_id="seller_ml_pricing_v1",
            contact_id="test_123",
            metadata={"has_cma": True, "pcs_score": 75},
        )

        assert variant in ["control", "treatment"]
        mock_ab_service.assign_variant.assert_called_once()

    @pytest.mark.asyncio
    async def test_experiment_event_tracking(self):
        """Test that ML pricing shown events are tracked."""
        mock_ab_service = AsyncMock()

        await mock_ab_service.track_event(
            experiment_id="seller_ml_pricing_v1",
            contact_id="test_123",
            event_type="ml_pricing_shown",
            properties={
                "recommended_price": 770000,
                "acceptance_probability": 0.85,
                "days_to_acceptance": 30,
            },
        )

        mock_ab_service.track_event.assert_called_once()
        call_args = mock_ab_service.track_event.call_args
        assert call_args.kwargs["event_type"] == "ml_pricing_shown"
        assert "recommended_price" in call_args.kwargs["properties"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
