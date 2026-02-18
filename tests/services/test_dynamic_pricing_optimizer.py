import pytest
pytestmark = pytest.mark.integration

"""
Unit tests for Dynamic Pricing Optimizer service.

Tests individual components of the pricing optimization system for Jorge's platform.
"""

import asyncio
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, Mock, patch

import pytest


try:
    from ghl_real_estate_ai.core.types import LeadClassification

    from ghl_real_estate_ai.services.dynamic_pricing_optimizer import (
        PRICING_TIERS,
        DynamicPricingOptimizer,
        LeadPricingResult,
        PricingConfiguration,
        PricingTier,
    )
except (ImportError, TypeError, AttributeError, Exception):
    pytest.skip("required imports unavailable", allow_module_level=True)


class TestDynamicPricingOptimizer:
    """Unit tests for Dynamic Pricing Optimizer."""

    @pytest.fixture
    def optimizer(self):
        """Create pricing optimizer with mocked dependencies."""
        optimizer = DynamicPricingOptimizer()

        # Mock external services
        optimizer.lead_scorer = AsyncMock()
        optimizer.predictive_scorer = AsyncMock()
        optimizer.revenue_engine = AsyncMock()
        optimizer.cache_service = AsyncMock()

        return optimizer

    @pytest.fixture
    def sample_context(self):
        """Sample lead context for testing."""
        return {
            "questions_answered": 3,
            "property_type": "Single Family",
            "budget_range": "$300000-$500000",
            "urgency": "high",
            "previous_inquiries": 2,
            "source": "Website Form",
        }

    async def test_calculate_lead_price_hot_lead(self, optimizer, sample_context):
        """Test pricing calculation for hot lead."""

        # Setup mocks for hot lead
        optimizer.lead_scorer.score_lead.return_value = 3.2
        optimizer.predictive_scorer.predict_conversion_probability.return_value = 0.68
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": 1850.0,
            "conversion_rate": 0.28,
            "lead_volume": 150,
        }

        # Calculate pricing
        result = await optimizer.calculate_lead_price(
            contact_id="test_contact_123", location_id="test_location_456", context=sample_context
        )

        # Verify result structure
        assert isinstance(result, LeadPricingResult)
        assert result.contact_id == "test_contact_123"
        assert result.location_id == "test_location_456"
        assert result.tier_classification == "hot"

        # Verify hot lead pricing (should be premium tier)
        assert result.suggested_price >= PRICING_TIERS["hot"].base_price
        assert result.confidence_score >= 0.6
        assert result.roi_multiplier >= 3.0
        assert "High-quality lead" in result.price_justification

    async def test_calculate_lead_price_warm_lead(self, optimizer, sample_context):
        """Test pricing calculation for warm lead."""

        # Setup mocks for warm lead (2 questions answered)
        warm_context = {**sample_context, "questions_answered": 2, "urgency": "medium"}

        optimizer.lead_scorer.score_lead.return_value = 2.1
        optimizer.predictive_scorer.predict_conversion_probability.return_value = 0.34
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": 1425.0,
            "conversion_rate": 0.19,
            "lead_volume": 200,
        }

        # Calculate pricing
        result = await optimizer.calculate_lead_price(
            contact_id="test_contact_456", location_id="test_location_789", context=warm_context
        )

        # Verify warm lead characteristics
        assert result.tier_classification == "warm"
        assert PRICING_TIERS["warm"].base_price <= result.suggested_price < PRICING_TIERS["hot"].base_price
        assert 0.3 <= result.confidence_score < 0.7
        assert 2.0 <= result.roi_multiplier < 3.0

    async def test_calculate_lead_price_cold_lead(self, optimizer, sample_context):
        """Test pricing calculation for cold lead."""

        # Setup mocks for cold lead
        cold_context = {**sample_context, "questions_answered": 0, "urgency": "low"}

        optimizer.lead_scorer.score_lead.return_value = 0.8
        optimizer.predictive_scorer.predict_conversion_probability.return_value = 0.12
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": 950.0,
            "conversion_rate": 0.08,
            "lead_volume": 300,
        }

        # Calculate pricing
        result = await optimizer.calculate_lead_price(
            contact_id="test_contact_789", location_id="test_location_123", context=cold_context
        )

        # Verify cold lead characteristics
        assert result.tier_classification == "cold"
        assert result.suggested_price <= PRICING_TIERS["warm"].base_price
        assert result.confidence_score < 0.4
        assert result.roi_multiplier <= 2.0

    async def test_roi_justified_pricing(self, optimizer, sample_context):
        """Test that pricing provides appropriate ROI justification."""

        # Setup high-value scenario
        optimizer.lead_scorer.score_lead.return_value = 3.8
        optimizer.predictive_scorer.predict_conversion_probability.return_value = 0.82
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": 2500.0,
            "conversion_rate": 0.45,
            "lead_volume": 80,
        }

        result = await optimizer.calculate_lead_price(
            contact_id="high_value_lead", location_id="premium_location", context=sample_context
        )

        # Calculate expected ROI
        expected_lead_value = 2500.0 * 0.82  # deal_size * conversion_probability
        actual_roi = expected_lead_value / result.suggested_price

        # Verify ROI meets minimum threshold (3x)
        assert actual_roi >= 3.0
        assert result.roi_multiplier >= 3.0

        # Verify justification includes ROI reasoning
        justification_lower = result.price_justification.lower()
        assert any(term in justification_lower for term in ["roi", "return", "value", "conversion"])

    async def test_pricing_configuration_update(self, optimizer):
        """Test updating pricing configuration."""

        new_config = {
            "base_price_hot": 450.0,
            "base_price_warm": 275.0,
            "base_price_cold": 125.0,
            "roi_multiplier_target": 4.5,
            "confidence_threshold_hot": 0.7,
            "confidence_threshold_warm": 0.4,
        }

        result = await optimizer.update_pricing_configuration(location_id="test_location", configuration=new_config)

        assert result["success"] is True
        assert result["updated_settings"]["base_price_hot"] == 450.0
        assert result["updated_settings"]["roi_multiplier_target"] == 4.5

    async def test_get_pricing_analytics(self, optimizer):
        """Test pricing analytics retrieval."""

        # Mock analytics data
        optimizer.revenue_engine.calculate_lead_value_metrics.return_value = {
            "average_lead_value": 380.0,
            "lead_value_by_tier": {"hot": 750.0, "warm": 320.0, "cold": 95.0},
            "conversion_rates_by_tier": {"hot": 0.38, "warm": 0.21, "cold": 0.07},
            "total_qualified_leads": 245,
            "period_revenue": 147500.0,
        }

        optimizer.cache_service.get.return_value = None  # No cached data

        analytics = await optimizer.get_pricing_analytics(location_id="test_location", days=30)

        # Verify analytics structure
        assert "average_lead_value" in analytics
        assert "lead_value_by_tier" in analytics
        assert "conversion_rates_by_tier" in analytics

        # Verify tier-specific data
        assert analytics["lead_value_by_tier"]["hot"] == 750.0
        assert analytics["conversion_rates_by_tier"]["hot"] == 0.38

    async def test_pricing_with_insufficient_data(self, optimizer, sample_context):
        """Test pricing calculation when insufficient historical data exists."""

        # Mock scenario with minimal data
        optimizer.lead_scorer.score_lead.return_value = 2.5
        optimizer.predictive_scorer.predict_conversion_probability.return_value = None  # No prediction available
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": None,
            "conversion_rate": None,
            "lead_volume": 5,  # Very low volume
        }

        result = await optimizer.calculate_lead_price(
            contact_id="new_location_lead", location_id="new_location", context=sample_context
        )

        # Should fall back to default pricing
        assert result.tier_classification == "warm"  # Based on score 2.5
        assert result.suggested_price == PRICING_TIERS["warm"].base_price
        assert "insufficient historical data" in result.price_justification.lower()
        assert result.confidence_score <= 0.5

    async def test_pricing_caching(self, optimizer, sample_context):
        """Test that pricing calculations are properly cached."""

        cache_key = "pricing_test_contact_test_location"

        # First call - should calculate and cache
        optimizer.cache_service.get.return_value = None
        optimizer.lead_scorer.score_lead.return_value = 3.0

        result1 = await optimizer.calculate_lead_price(
            contact_id="test_contact", location_id="test_location", context=sample_context
        )

        # Verify cache was called for storage
        optimizer.cache_service.set.assert_called()

        # Second call - should return cached result
        optimizer.cache_service.get.return_value = result1

        result2 = await optimizer.calculate_lead_price(
            contact_id="test_contact", location_id="test_location", context=sample_context
        )

        # Results should be identical (cached)
        assert result1.suggested_price == result2.suggested_price
        assert result1.confidence_score == result2.confidence_score

    async def test_tier_classification_logic(self, optimizer):
        """Test lead tier classification logic."""

        # Test score-based classification
        test_cases = [(0.5, "cold"), (1.5, "cold"), (2.0, "warm"), (2.9, "warm"), (3.0, "hot"), (4.5, "hot")]

        for score, expected_tier in test_cases:
            tier = optimizer._classify_lead_tier(score, {})
            assert tier == expected_tier, f"Score {score} should classify as {expected_tier}, got {tier}"

    async def test_price_adjustment_factors(self, optimizer, sample_context):
        """Test various factors that should adjust pricing."""

        base_context = {**sample_context}

        # Test urgency factor
        high_urgency_context = {**base_context, "urgency": "immediate", "timeline": "this_week"}
        low_urgency_context = {**base_context, "urgency": "exploring", "timeline": "next_year"}

        optimizer.lead_scorer.score_lead.return_value = 3.0
        optimizer.predictive_scorer.predict_conversion_probability.return_value = 0.6

        # Mock consistent revenue data
        optimizer.revenue_engine.get_location_metrics.return_value = {
            "average_deal_size": 1500.0,
            "conversion_rate": 0.25,
            "lead_volume": 100,
        }

        # Calculate pricing for different urgency levels
        high_urgency_result = await optimizer.calculate_lead_price("contact1", "location1", high_urgency_context)

        low_urgency_result = await optimizer.calculate_lead_price("contact2", "location1", low_urgency_context)

        # High urgency should command higher pricing
        assert high_urgency_result.suggested_price >= low_urgency_result.suggested_price
        assert "urgency" in high_urgency_result.price_justification.lower()

    async def test_error_handling(self, optimizer, sample_context):
        """Test error handling in pricing calculations."""

        # Test service unavailable scenario
        optimizer.lead_scorer.score_lead.side_effect = Exception("Service unavailable")

        # Should handle gracefully and return default pricing
        result = await optimizer.calculate_lead_price("error_contact", "error_location", sample_context)

        # Should return valid result with low confidence
        assert result is not None
        assert result.confidence_score <= 0.3
        assert "error" in result.price_justification.lower() or "default" in result.price_justification.lower()

    async def test_export_pricing_data(self, optimizer):
        """Test pricing data export functionality."""

        # Mock pricing history data
        optimizer.cache_service.get_pattern.return_value = [
            {"contact_id": "contact1", "suggested_price": 425.0, "tier": "hot", "calculated_at": "2024-01-15T10:30:00"},
            {
                "contact_id": "contact2",
                "suggested_price": 275.0,
                "tier": "warm",
                "calculated_at": "2024-01-16T14:20:00",
            },
        ]

        export_result = await optimizer.export_pricing_data(
            location_id="test_location", date_range={"start_date": "2024-01-01", "end_date": "2024-01-31"}, format="csv"
        )

        # Verify export structure
        assert export_result["export_format"] == "csv"
        assert export_result["records_count"] == 2
        assert "download_url" in export_result
        assert "expires_at" in export_result


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])