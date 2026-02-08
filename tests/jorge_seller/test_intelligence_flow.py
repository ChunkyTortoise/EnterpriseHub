from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.negotiation import (
    ListingBehaviorPattern,
    SellerMotivationType,
    SellerPsychologyProfile,
    UrgencyLevel,
)
from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine


class TestJorgeIntelligenceFlow:
    """
    Tests for Jorge's 2026 Intelligence layer, focusing on
    psychological tone adaptation and market-aware messaging.
    """

    @pytest.fixture
    def tone_engine(self):
        return JorgeToneEngine()

    def test_take_away_close_emotional_attachment(self, tone_engine):
        """Verify tone engine uses loss aversion for high emotional attachment."""
        profile = SellerPsychologyProfile(
            motivation_type=SellerMotivationType.EMOTIONAL,
            urgency_level=UrgencyLevel.LOW,
            urgency_score=20.0,
            behavioral_pattern=ListingBehaviorPattern.OVERPRICED_STUBBORN,
            emotional_attachment_score=85.0,  # HIGH
            financial_pressure_score=10.0,
            flexibility_score=15.0,
            relationship_importance=90.0,
        )

        message = tone_engine.generate_take_away_close(seller_name="John", psychology_profile=profile)

        assert "john," in message.lower()
        assert "too attached" in message.lower()
        # The middle sentence might be truncated to fit 160 chars
        assert "homeowner" in message.lower()

    def test_net_yield_justification_distressed(self, tone_engine):
        """Verify tone engine is more aggressive for distressed sellers."""
        profile = SellerPsychologyProfile(
            motivation_type=SellerMotivationType.DISTRESSED,
            urgency_level=UrgencyLevel.CRITICAL,
            urgency_score=95.0,
            behavioral_pattern=ListingBehaviorPattern.MOTIVATED_SELLER,
            emotional_attachment_score=5.0,
            financial_pressure_score=98.0,
            flexibility_score=80.0,
            relationship_importance=10.0,
        )

        message = tone_engine.generate_net_yield_justification(
            price_expectation=500000,
            ai_valuation=420000,
            net_yield=0.84,
            seller_name="Sarah",
            psychology_profile=profile,
        )

        assert "sarah," in message.lower()
        assert "pipe dream" in message.lower()
        assert "financial reality check" in message.lower()
        assert "solve this problem" in message.lower()

    def test_net_yield_justification_standard(self, tone_engine):
        """Verify standard net yield justification for non-distressed."""
        profile = SellerPsychologyProfile(
            motivation_type=SellerMotivationType.FINANCIAL,
            urgency_level=UrgencyLevel.MODERATE,
            urgency_score=50.0,
            behavioral_pattern=ListingBehaviorPattern.PRICE_DROPPER,
            emotional_attachment_score=30.0,
            financial_pressure_score=60.0,
            flexibility_score=40.0,
            relationship_importance=50.0,
        )

        message = tone_engine.generate_net_yield_justification(
            price_expectation=500000,
            ai_valuation=420000,
            net_yield=0.84,
            repair_estimate=25000,
            seller_name="Mike",
            psychology_profile=profile,
        )

        assert "mike," in message.lower()
        assert "repairs needed" in message.lower()
        assert "net yield is too low" in message.lower()

    def test_cost_of_waiting_loss_aversion(self, tone_engine):
        """Verify cost of waiting message generation."""
        message = tone_engine.generate_cost_of_waiting_message(
            seller_name="Robert", market_trend="rising interest rates"
        )

        assert "robert," in message.lower()
        assert "rate volatility" in message.lower()
        assert "equity" in message.lower()

    @patch("ghl_real_estate_ai.services.national_market_intelligence.get_national_market_intelligence")
    @pytest.mark.asyncio
    async def test_seller_engine_market_integration(self, mock_get_market, tone_engine):
        """Verify JorgeSellerEngine integrates market data into insights."""
        from unittest.mock import AsyncMock

        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        mock_market_intel = MagicMock()
        mock_get_market.return_value = mock_market_intel

        # Mock metrics
        mock_metrics = MagicMock()
        mock_metrics.inventory_trend = "exploding"
        mock_metrics.days_on_market = 45
        mock_market_intel.get_market_metrics = AsyncMock(return_value=mock_metrics)

        # Mock dependencies for JorgeSellerEngine
        mock_conv_manager = MagicMock()
        mock_ghl_client = MagicMock()

        engine = JorgeSellerEngine(conversation_manager=mock_conv_manager, ghl_client=mock_ghl_client)
        insight = await engine._get_market_insight("Austin, TX")

        assert "Austin, TX" in insight
        assert "exploding" in insight
        assert "losing leverage" in insight
