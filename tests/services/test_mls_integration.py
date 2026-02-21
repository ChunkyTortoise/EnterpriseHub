import pytest

pytestmark = pytest.mark.integration

"""Tests for Phase 4: Real MLS Data Integration.

Validates that JorgeSellerEngine uses real MLS data when available
and gracefully falls back to mock data on failure or missing address.
"""

import sys
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.negotiation import ListingHistory
from ghl_real_estate_ai.services.mls_client import MLSClient


def _mock_swarm_module():
    """Create a mock for the lead_intelligence_swarm module.

    The swarm is lazy-imported inside process_seller_response, so we
    inject it into sys.modules before the engine runs.
    """
    mock_swarm_obj = MagicMock()
    swarm_result = MagicMock()
    swarm_result.agent_insights = []
    mock_swarm_obj.analyze_lead_comprehensive = AsyncMock(return_value=swarm_result)

    mock_module = MagicMock()
    mock_module.lead_intelligence_swarm = mock_swarm_obj
    return mock_module


def _make_seller_engine(mls_client=None):
    """Build a JorgeSellerEngine with mocked dependencies.

    All heavy services imported inside __init__ are patched at their
    source modules so the engine can be constructed cheaply.
    """
    conversation_manager = AsyncMock()
    conversation_manager.get_context = AsyncMock(
        return_value={
            "seller_preferences": {},
            "contact_name": "Test Seller",
            "conversation_history": [],
            "days_since_first_contact": 10,
        }
    )
    conversation_manager.extract_seller_data = AsyncMock(
        return_value={
            "property_address": "123 Main St, Rancho Cucamonga, CA",
            "questions_answered": 2,
            "price_expectation": "650000",
            "response_quality": 0.8,
        }
    )
    conversation_manager.update_context = AsyncMock()

    ghl_client = AsyncMock()

    # Patch at source modules (these are lazy-imported inside __init__)
    with (
        patch("ghl_real_estate_ai.services.analytics_service.AnalyticsService"),
        patch("ghl_real_estate_ai.core.governance_engine.GovernanceEngine") as mock_gov_cls,
        patch("ghl_real_estate_ai.core.recovery_engine.RecoveryEngine") as mock_rec_cls,
        patch("ghl_real_estate_ai.services.predictive_lead_scorer_v2.PredictiveLeadScorerV2") as mock_scorer_cls,
        patch("ghl_real_estate_ai.services.dynamic_pricing_optimizer.DynamicPricingOptimizer") as mock_pricing_cls,
        patch(
            "ghl_real_estate_ai.services.psychographic_segmentation_engine.PsychographicSegmentationEngine"
        ) as mock_psycho_cls,
        patch(
            "ghl_real_estate_ai.services.seller_psychology_analyzer.get_seller_psychology_analyzer"
        ) as mock_get_psych,
    ):
        # Governance: enforce returns message unchanged
        mock_gov_cls.return_value.enforce = MagicMock(side_effect=lambda msg: msg)

        # Recovery: safe fallback
        mock_rec_cls.return_value.get_safe_fallback = MagicMock(return_value="Safe fallback message")

        # Predictive scorer
        scorer_result = MagicMock()
        scorer_result.closing_probability = 0.5
        scorer_result.overall_priority_score = 60
        scorer_result.priority_level = MagicMock(value="medium")
        scorer_result.net_yield_estimate = 0.15
        mock_scorer_cls.return_value.calculate_predictive_score = AsyncMock(return_value=scorer_result)

        # Pricing optimizer
        pricing_result = MagicMock()
        pricing_result.final_price = 25.0
        pricing_result.tier = "standard"
        pricing_result.justification = "test"
        pricing_result.expected_roi = 12.5
        mock_pricing_cls.return_value.calculate_lead_price = AsyncMock(return_value=pricing_result)

        # Psychographic engine
        mock_psycho_cls.return_value.detect_persona = AsyncMock(
            return_value={
                "primary_persona": "unknown",
            }
        )
        mock_psycho_cls.return_value.get_system_prompt_override = MagicMock(return_value="")

        # Psychology analyzer
        psych_analyzer = AsyncMock()
        psych_profile = MagicMock()
        psych_profile.motivation_type = "financial"
        psych_profile.urgency_level = "medium"
        psych_analyzer.analyze_seller_psychology = AsyncMock(return_value=psych_profile)
        mock_get_psych.return_value = psych_analyzer

        from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

        config = MagicMock()
        config.JORGE_SIMPLE_MODE = True
        config.HOT_QUESTIONS_REQUIRED = 4
        config.HOT_QUALITY_THRESHOLD = 0.7
        config.WARM_QUESTIONS_REQUIRED = 2
        config.WARM_QUALITY_THRESHOLD = 0.4

        engine = JorgeSellerEngine(
            conversation_manager=conversation_manager,
            ghl_client=ghl_client,
            config=config,
            mls_client=mls_client,
        )

    return engine


def _make_listing_history(**overrides):
    """Create a ListingHistory with sensible defaults."""
    defaults = {
        "original_list_price": Decimal("700000"),
        "current_price": Decimal("675000"),
        "days_on_market": 45,
        "price_drops": [
            {"old_price": 700000, "new_price": 675000, "percentage": 3.6},
        ],
    }
    defaults.update(overrides)
    return ListingHistory(**defaults)


class TestSellerEngineMlsIntegration:
    """Seller engine uses real MLS data when available."""

    @pytest.mark.asyncio
    async def test_seller_engine_uses_mls_when_available(self):
        """Real listing history from MLS is used when MLSClient returns data."""
        mls_client = AsyncMock(spec=MLSClient)
        real_history = _make_listing_history(days_on_market=90)
        mls_client.get_listing_history = AsyncMock(return_value=real_history)

        engine = _make_seller_engine(mls_client=mls_client)

        with patch.dict(sys.modules, {"ghl_real_estate_ai.agents.lead_intelligence_swarm": _mock_swarm_module()}):
            result = await engine.process_seller_response(
                contact_id="seller_001",
                user_message="I want to sell my house for 650k",
                location_id="loc_test",
            )

        # MLS client was called
        mls_client.get_listing_history.assert_awaited_once()

        # Psychology analyzer received the real listing history (not mock)
        psych_call = engine.psychology_analyzer.analyze_seller_psychology
        psych_call.assert_awaited_once()
        call_kwargs = psych_call.call_args
        listing_arg = call_kwargs.kwargs.get("listing_history") or call_kwargs.args[1]
        assert listing_arg.days_on_market == 90

        # Engine still returns a valid response
        assert "message" in result
        assert result["temperature"] in ("hot", "warm", "cold")

    @pytest.mark.asyncio
    async def test_seller_engine_fallback_when_mls_fails(self):
        """Mock data used when MLS throws an exception."""
        mls_client = AsyncMock(spec=MLSClient)
        mls_client.get_listing_history = AsyncMock(side_effect=Exception("API timeout"))

        engine = _make_seller_engine(mls_client=mls_client)

        with patch.dict(sys.modules, {"ghl_real_estate_ai.agents.lead_intelligence_swarm": _mock_swarm_module()}):
            result = await engine.process_seller_response(
                contact_id="seller_002",
                user_message="What's my home worth?",
                location_id="loc_test",
            )

        # MLS was attempted
        mls_client.get_listing_history.assert_awaited_once()

        # Psychology analyzer was still called with fallback data
        psych_call = engine.psychology_analyzer.analyze_seller_psychology
        psych_call.assert_awaited_once()
        call_kwargs = psych_call.call_args
        listing_arg = call_kwargs.kwargs.get("listing_history") or call_kwargs.args[1]
        # Fallback uses days_since_first_contact from context (10)
        assert listing_arg.days_on_market == 10

        assert "message" in result

    @pytest.mark.asyncio
    async def test_seller_engine_fallback_when_no_address(self):
        """Mock data used when no property address is available."""
        mls_client = AsyncMock(spec=MLSClient)
        mls_client.get_listing_history = AsyncMock()

        engine = _make_seller_engine(mls_client=mls_client)

        # Override extract to return no address
        engine.conversation_manager.extract_seller_data = AsyncMock(
            return_value={
                "questions_answered": 1,
                "price_expectation": "500000",
                "response_quality": 0.7,
                # No property_address key
            }
        )

        with patch.dict(sys.modules, {"ghl_real_estate_ai.agents.lead_intelligence_swarm": _mock_swarm_module()}):
            result = await engine.process_seller_response(
                contact_id="seller_003",
                user_message="Just thinking about selling",
                location_id="loc_test",
            )

        # MLS should NOT be called because there's no address
        mls_client.get_listing_history.assert_not_awaited()

        # Psychology analysis is skipped entirely (no property_address)
        engine.psychology_analyzer.analyze_seller_psychology.assert_not_awaited()

        assert "message" in result
        assert result["temperature"] in ("hot", "warm", "cold")

    @pytest.mark.asyncio
    async def test_psychology_analyzer_with_real_listing_data(self):
        """Price drops in real listing data are detected in psychology profile."""
        mls_client = AsyncMock(spec=MLSClient)
        real_history = _make_listing_history(
            original_list_price=Decimal("750000"),
            current_price=Decimal("700000"),
            days_on_market=60,
            price_drops=[
                {"old_price": 750000, "new_price": 725000, "percentage": 3.3},
                {"old_price": 725000, "new_price": 700000, "percentage": 3.4},
            ],
        )
        mls_client.get_listing_history = AsyncMock(return_value=real_history)

        engine = _make_seller_engine(mls_client=mls_client)

        with patch.dict(sys.modules, {"ghl_real_estate_ai.agents.lead_intelligence_swarm": _mock_swarm_module()}):
            await engine.process_seller_response(
                contact_id="seller_004",
                user_message="I need to sell, the market is dropping",
                location_id="loc_test",
            )

        # Verify psychology analyzer received listing with price drops
        psych_call = engine.psychology_analyzer.analyze_seller_psychology
        psych_call.assert_awaited_once()
        call_kwargs = psych_call.call_args
        listing_arg = call_kwargs.kwargs.get("listing_history") or call_kwargs.args[1]

        assert listing_arg.days_on_market == 60
        assert len(listing_arg.price_drops) == 2
        assert listing_arg.original_list_price == Decimal("750000")
        assert listing_arg.current_price == Decimal("700000")
