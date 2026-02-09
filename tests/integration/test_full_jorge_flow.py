import pytest
pytestmark = pytest.mark.integration

"""
Full Jorge Bot Flow Integration Tests

Comprehensive end-to-end integration tests covering the complete lifecycle of
lead qualification through the Jorge bot family:
- Lead qualification flow (initial contact -> scoring -> action)
- Buyer qualification flow (discovery -> financial assessment -> property matching)
- Seller analysis flow (intent -> stall detection -> strategy -> response)
- Conversation persistence and state management
- Cross-bot communication and handoff

All external services (Claude AI, event publisher, ML analytics, property matcher)
are mocked. Test data uses realistic Rancho Cucamonga market context.
"""

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest

from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.models.lead_scoring import (
    BuyerIntentProfile,
    ConditionRealism,
    FinancialReadinessScore,
    LeadIntentProfile,
    MotivationSignals,
    PriceResponsiveness,
    PsychologicalCommitmentScore,
    TimelineCommitment,
)
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState

# ---------------------------------------------------------------------------
# Shared helpers and fixtures
# ---------------------------------------------------------------------------


def _make_buyer_intent_profile(
    *,
    financial_readiness: float = 75.0,
    budget_clarity: float = 80.0,
    financing_status_score: float = 85.0,
    urgency_score: float = 65.0,
    timeline_pressure: float = 70.0,
    consequence_awareness: float = 60.0,
    preference_clarity: float = 70.0,
    market_realism: float = 75.0,
    decision_authority: float = 80.0,
    buyer_temperature: str = "warm",
    confidence_level: float = 85.0,
    conversation_turns: int = 3,
    key_insights: Dict[str, Any] | None = None,
    next_qualification_step: str = "preferences",
) -> BuyerIntentProfile:
    """Factory for BuyerIntentProfile with sensible Rancho Cucamonga defaults."""
    return BuyerIntentProfile(
        financial_readiness=financial_readiness,
        budget_clarity=budget_clarity,
        financing_status_score=financing_status_score,
        urgency_score=urgency_score,
        timeline_pressure=timeline_pressure,
        consequence_awareness=consequence_awareness,
        preference_clarity=preference_clarity,
        market_realism=market_realism,
        decision_authority=decision_authority,
        buyer_temperature=buyer_temperature,
        confidence_level=confidence_level,
        conversation_turns=conversation_turns,
        key_insights=key_insights or {"has_specific_timeline": True, "mentions_financing": True},
        next_qualification_step=next_qualification_step,
    )


def _make_seller_intent_profile(
    *,
    frs_total: float = 72.0,
    pcs_total: float = 65.0,
    frs_classification: str = "Warm Lead",
    lead_id: str = "seller_lead_001",
    next_best_action: str = "schedule_call",
) -> LeadIntentProfile:
    """Factory for LeadIntentProfile (seller) with Rancho Cucamonga defaults."""
    return LeadIntentProfile(
        lead_id=lead_id,
        frs=FinancialReadinessScore(
            total_score=frs_total,
            motivation=MotivationSignals(score=75, detected_markers=["relocating"], category="High Intent"),
            timeline=TimelineCommitment(score=70, target_date=None, category="High Commitment"),
            condition=ConditionRealism(score=65, acknowledged_defects=["needs_paint"], category="Realistic"),
            price=PriceResponsiveness(score=60, zestimate_mentioned=False, category="Price-Aware"),
            classification=frs_classification,
        ),
        pcs=PsychologicalCommitmentScore(
            total_score=pcs_total,
            response_velocity_score=80,
            message_length_score=70,
            question_depth_score=65,
            objection_handling_score=60,
            call_acceptance_score=55,
        ),
        lead_type="seller",
        market_context="Rancho Cucamonga - Etiwanda",
        next_best_action=next_best_action,
        stall_breaker_suggested=None,
    )


def _make_buyer_state(
    *,
    buyer_id: str = "test_buyer_123",
    buyer_name: str = "John Doe",
    conversation_history: List[Dict[str, str]] | None = None,
    financial_readiness_score: float = 0.0,
    buying_motivation_score: float = 0.0,
    financing_status: str = "unknown",
    urgency_level: str = "browsing",
    current_qualification_step: str = "budget",
    next_action: str = "qualify",
    is_qualified: bool = False,
) -> BuyerBotState:
    """Factory for BuyerBotState with Rancho Cucamonga buyer data."""
    if conversation_history is None:
        conversation_history = [
            {"role": "user", "content": "Looking for a 3br house under $700k in Etiwanda"},
            {"role": "assistant", "content": "Great choice! Etiwanda has lovely family homes. What is your timeline?"},
            {"role": "user", "content": "Need to move in 3 months, pre-approved for $680k"},
        ]
    return BuyerBotState(
        buyer_id=buyer_id,
        buyer_name=buyer_name,
        target_areas=None,
        conversation_history=conversation_history,
        intent_profile=None,
        budget_range=None,
        financing_status=financing_status,
        urgency_level=urgency_level,
        property_preferences=None,
        current_qualification_step=current_qualification_step,
        objection_detected=False,
        detected_objection_type=None,
        next_action=next_action,
        response_content="",
        matched_properties=[],
        financial_readiness_score=financial_readiness_score,
        buying_motivation_score=buying_motivation_score,
        is_qualified=is_qualified,
        current_journey_stage="discovery",
        properties_viewed_count=0,
        last_action_timestamp=None,
    )


def _make_seller_state(
    *,
    lead_id: str = "seller_lead_001",
    lead_name: str = "Maria Garcia",
    property_address: str = "12345 Etiwanda Ave, Rancho Cucamonga, CA",
    conversation_history: List[Dict[str, str]] | None = None,
    current_tone: str = "direct",
    next_action: str = "respond",
) -> JorgeSellerState:
    """Factory for JorgeSellerState with Rancho Cucamonga seller data."""
    if conversation_history is None:
        conversation_history = [
            {"role": "user", "content": "I want to sell my house in Etiwanda"},
            {"role": "assistant", "content": "Great! What is your timeline for selling?"},
            {"role": "user", "content": "I need to sell within 60 days, relocating for work"},
        ]
    return JorgeSellerState(
        lead_id=lead_id,
        lead_name=lead_name,
        property_address=property_address,
        conversation_history=conversation_history,
        intent_profile=None,
        current_tone=current_tone,
        stall_detected=False,
        detected_stall_type=None,
        next_action=next_action,
        response_content="",
        psychological_commitment=0.0,
        is_qualified=False,
        current_journey_stage="qualification",
        follow_up_count=0,
        last_action_timestamp=None,
    )


def _rancho_cucamonga_properties(count: int = 3) -> List[Dict[str, Any]]:
    """Generate sample Rancho Cucamonga property listings."""
    listings = [
        {
            "id": "prop_etiwanda_001",
            "address": "7890 Etiwanda Ave, Rancho Cucamonga, CA 91739",
            "price": 685000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1850,
            "area": "Etiwanda",
            "type": "single_family",
            "status": "active",
        },
        {
            "id": "prop_victoria_002",
            "address": "4567 Victoria Park Ln, Rancho Cucamonga, CA 91739",
            "price": 725000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2200,
            "area": "Victoria",
            "type": "single_family",
            "status": "active",
        },
        {
            "id": "prop_haven_003",
            "address": "2345 Haven Ave, Rancho Cucamonga, CA 91730",
            "price": 599000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1650,
            "area": "Haven",
            "type": "single_family",
            "status": "active",
        },
        {
            "id": "prop_terra_004",
            "address": "8901 Terra Vista Pkwy, Rancho Cucamonga, CA 91730",
            "price": 890000,
            "bedrooms": 4,
            "bathrooms": 3,
            "sqft": 2600,
            "area": "Terra Vista",
            "type": "single_family",
            "status": "active",
        },
        {
            "id": "prop_central_005",
            "address": "1234 Central Park W, Rancho Cucamonga, CA 91730",
            "price": 550000,
            "bedrooms": 3,
            "bathrooms": 2,
            "sqft": 1500,
            "area": "Central Park",
            "type": "townhouse",
            "status": "active",
        },
    ]
    return listings[:count]


# ---------------------------------------------------------------------------
# Mock context managers for buyer and seller bot dependencies
# ---------------------------------------------------------------------------


def _buyer_bot_patches():
    """Return a dict of patches for JorgeBuyerBot external dependencies."""
    mock_event_publisher = AsyncMock()
    mock_event_publisher.publish_bot_status_update = AsyncMock()
    mock_event_publisher.publish_buyer_intent_analysis = AsyncMock()
    mock_event_publisher.publish_property_match_update = AsyncMock()
    mock_event_publisher.publish_buyer_follow_up_scheduled = AsyncMock()
    mock_event_publisher.publish_buyer_qualification_complete = AsyncMock()
    mock_event_publisher.publish_conversation_update = AsyncMock()

    mock_ml_analytics = MagicMock()
    mock_ml_analytics.predict_lead_journey = AsyncMock()
    mock_ml_analytics.predict_conversion_probability = AsyncMock()
    mock_ml_analytics.predict_optimal_touchpoints = AsyncMock()

    return {
        "event_publisher": mock_event_publisher,
        "ml_analytics": mock_ml_analytics,
    }


def _seller_bot_patches():
    """Return a dict of patches for JorgeSellerBot external dependencies."""
    mock_event_publisher = AsyncMock()
    mock_event_publisher.publish_bot_status_update = AsyncMock()
    mock_event_publisher.publish_jorge_qualification_progress = AsyncMock()
    mock_event_publisher.publish_conversation_update = AsyncMock()

    # Journey analysis mock
    mock_journey = MagicMock()
    mock_journey.conversion_probability = 0.72
    mock_journey.stage_progression_velocity = 0.85
    mock_journey.processing_time_ms = 15.0

    # Conversion analysis mock
    mock_conversion = MagicMock()
    mock_conversion.urgency_score = 75.0
    mock_conversion.optimal_action = "schedule_call"
    mock_conversion.processing_time_ms = 12.0

    # Touchpoint analysis mock
    mock_touchpoint = MagicMock()
    mock_touchpoint.response_pattern = "engaged_fast_responder"
    mock_touchpoint.processing_time_ms = 10.0

    mock_ml_analytics = MagicMock()
    mock_ml_analytics.predict_lead_journey = AsyncMock(return_value=mock_journey)
    mock_ml_analytics.predict_conversion_probability = AsyncMock(return_value=mock_conversion)
    mock_ml_analytics.predict_optimal_touchpoints = AsyncMock(return_value=mock_touchpoint)

    return {
        "event_publisher": mock_event_publisher,
        "ml_analytics": mock_ml_analytics,
        "journey_analysis": mock_journey,
        "conversion_analysis": mock_conversion,
        "touchpoint_analysis": mock_touchpoint,
    }


# ===========================================================================
# 1. TestLeadQualificationFlow
# ===========================================================================


@pytest.mark.integration
class TestLeadQualificationFlow:
    """Lead -> Qualification -> Action: end-to-end qualification pipeline."""

    @pytest.mark.asyncio
    async def test_lead_qualification_full_flow(self):
        """Complete flow: initial contact -> intent analysis -> scoring -> follow-up action."""
        buyer_profile = _make_buyer_intent_profile(
            financial_readiness=75.0,
            urgency_score=65.0,
            buyer_temperature="warm",
            next_qualification_step="preferences",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=buyer_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={
                "content": "Great news! Based on your pre-approval and timeline, I have some excellent Etiwanda properties to show you."
            }
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(3))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=False)

            result = await bot.process_buyer_conversation(
                buyer_id="lead_rc_001",
                buyer_name="Alex Thompson",
                conversation_history=[
                    {"role": "user", "content": "Hi, I'm looking for a 3br house in Etiwanda under $700k"},
                    {"role": "assistant", "content": "Welcome! Etiwanda is a wonderful area. What is your timeline?"},
                    {"role": "user", "content": "Pre-approved for $680k, need to move in 3 months"},
                ],
            )

        # Step 1: Intent was analyzed
        mock_intent_decoder.analyze_buyer.assert_called_once()

        # Step 2: Intent analysis event was published
        patches["event_publisher"].publish_buyer_intent_analysis.assert_awaited()

        # Step 3: Properties were matched
        mock_property_matcher.find_matches.assert_called_once()

        # Step 4: Final qualification result
        assert result["buyer_id"] == "lead_rc_001"
        assert result.get("financial_readiness_score") == 75.0
        assert result.get("buying_motivation_score") == 65.0
        assert result.get("is_qualified") is True

        # Step 5: Qualification complete event was published
        patches["event_publisher"].publish_buyer_qualification_complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lead_with_high_intent_fast_tracks(self):
        """Hot lead with high scores gets accelerated qualification path."""
        hot_profile = _make_buyer_intent_profile(
            financial_readiness=92.0,
            urgency_score=88.0,
            financing_status_score=95.0,
            buyer_temperature="hot",
            next_qualification_step="property_tour",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=hot_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={"content": "I am excited to help! Let us schedule property tours in Victoria this weekend."}
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(5))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_hot", enable_bot_intelligence=False)

            result = await bot.process_buyer_conversation(
                buyer_id="hot_lead_rc_002",
                buyer_name="Sarah Chen",
                conversation_history=[
                    {"role": "user", "content": "I'm pre-approved for $900k and need a house in Victoria ASAP"},
                    {"role": "assistant", "content": "Wonderful! Victoria has stunning properties. Tell me more."},
                    {"role": "user", "content": "4br, pool, ready to close in 30 days. Cash plus financing."},
                ],
            )

        # Hot lead is qualified immediately
        assert result.get("is_qualified") is True
        assert result.get("financial_readiness_score") == 92.0
        assert result.get("buying_motivation_score") == 88.0

        # Properties were matched for hot lead
        mock_property_matcher.find_matches.assert_called_once()

        # Event publisher received hot-lead qualification
        patches["event_publisher"].publish_buyer_qualification_complete.assert_awaited_once()
        call_kwargs = patches["event_publisher"].publish_buyer_qualification_complete.call_args
        assert call_kwargs.kwargs["qualification_status"] == "qualified"

    @pytest.mark.asyncio
    async def test_lead_with_low_intent_enters_nurture(self):
        """Cold lead with low scores enters nurture sequence instead of fast-track."""
        cold_profile = _make_buyer_intent_profile(
            financial_readiness=20.0,
            urgency_score=15.0,
            financing_status_score=10.0,
            budget_clarity=25.0,
            buyer_temperature="cold",
            next_qualification_step="budget",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=cold_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={
                "content": "I would love to help when you are ready. Here is some info about the Rancho Cucamonga market."
            }
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=[])

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_cold", enable_bot_intelligence=False)

            result = await bot.process_buyer_conversation(
                buyer_id="cold_lead_rc_003",
                buyer_name="Window Shopper",
                conversation_history=[
                    {"role": "user", "content": "Just browsing, maybe someday"},
                ],
            )

        # Cold lead is NOT qualified
        assert result.get("is_qualified") is False
        assert result.get("financial_readiness_score") == 20.0
        assert result.get("buying_motivation_score") == 15.0

        # Qualification complete event reflects nurture status
        patches["event_publisher"].publish_buyer_qualification_complete.assert_awaited_once()
        call_kwargs = patches["event_publisher"].publish_buyer_qualification_complete.call_args
        assert call_kwargs.kwargs["qualification_status"] == "needs_nurturing"

    @pytest.mark.asyncio
    async def test_lead_qualification_handles_missing_data(self):
        """Graceful handling when conversation history is empty or data is incomplete."""
        # Profile with minimal data -- decoder still returns something
        minimal_profile = _make_buyer_intent_profile(
            financial_readiness=30.0,
            urgency_score=10.0,
            financing_status_score=0.0,
            budget_clarity=0.0,
            buyer_temperature="ice_cold",
            next_qualification_step="budget",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=minimal_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={"content": "Hi there! I would love to help you explore homes in Rancho Cucamonga."}
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=[])

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_minimal", enable_bot_intelligence=False)

            # Empty conversation history -- should not crash
            result = await bot.process_buyer_conversation(
                buyer_id="sparse_lead_rc_004",
                buyer_name="",
                conversation_history=[],
            )

        # Bot should still return a valid result without errors
        assert result.get("buyer_id") == "sparse_lead_rc_004"
        assert result.get("is_qualified") is False
        # No exception means graceful handling
        assert "error" not in result or result.get("error") is None


# ===========================================================================
# 2. TestBuyerQualificationFlow
# ===========================================================================


@pytest.mark.integration
class TestBuyerQualificationFlow:
    """Buyer discovery -> Financial assessment -> Property matching -> Response."""

    @pytest.mark.asyncio
    async def test_buyer_qualification_full_flow(self):
        """Complete: intent -> financial assessment -> property match -> response."""
        profile = _make_buyer_intent_profile(
            financial_readiness=78.0,
            financing_status_score=82.0,
            budget_clarity=85.0,
            urgency_score=70.0,
            preference_clarity=75.0,
            buyer_temperature="warm",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={
                "content": "Based on your pre-approval, here are three stunning Etiwanda homes within budget."
            }
        )

        etiwanda_properties = _rancho_cucamonga_properties(3)
        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=etiwanda_properties)

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_full", enable_bot_intelligence=False)

            state = _make_buyer_state(buyer_id="buyer_full_001", buyer_name="David Park")

            # --- Step 1: Analyze buyer intent ---
            intent_result = await bot.analyze_buyer_intent(state)
            assert intent_result["intent_profile"] is not None
            assert intent_result["financial_readiness_score"] == 78.0
            assert intent_result["buying_motivation_score"] == 70.0
            state.update(intent_result)

            # --- Step 2: Assess financial readiness ---
            financial_result = await bot.assess_financial_readiness(state)
            assert financial_result["financing_status"] == "pre_approved"
            state.update(financial_result)

            # --- Step 3: Qualify property needs ---
            property_needs = await bot.qualify_property_needs(state)
            assert property_needs["urgency_level"] in ("immediate", "3_months")
            state.update(property_needs)

            # --- Step 4: Match properties ---
            match_result = await bot.match_properties(state)
            assert len(match_result.get("matched_properties", [])) > 0
            state.update(match_result)

            # --- Step 5: Generate response ---
            response_result = await bot.generate_buyer_response(state)
            assert response_result["response_content"] != ""
            assert response_result["next_action"] == "send_response"

    @pytest.mark.asyncio
    async def test_buyer_with_preapproval_qualifies_faster(self):
        """Pre-approved buyer is recognized as financially ready immediately."""
        preapproved_profile = _make_buyer_intent_profile(
            financial_readiness=90.0,
            financing_status_score=95.0,
            budget_clarity=90.0,
            urgency_score=80.0,
            buyer_temperature="hot",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=preapproved_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={"content": "With your strong pre-approval, let us tour these Terra Vista homes this weekend!"}
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(5))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_preapproved", enable_bot_intelligence=False)

            state = _make_buyer_state(
                buyer_id="preapproved_buyer_001",
                buyer_name="Lisa Wang",
                conversation_history=[
                    {"role": "user", "content": "Pre-approved for $850k, looking for 4br in Terra Vista"},
                    {
                        "role": "assistant",
                        "content": "Excellent! Terra Vista is a premium area. When do you need to move?",
                    },
                    {"role": "user", "content": "Within 60 days, relocating from LA for work"},
                ],
            )

            # Step 1: Intent analysis
            intent_result = await bot.analyze_buyer_intent(state)
            state.update(intent_result)
            assert intent_result["financial_readiness_score"] == 90.0

            # Step 2: Financial assessment should reflect pre-approved status
            financial_result = await bot.assess_financial_readiness(state)
            assert financial_result["financing_status"] == "pre_approved"
            state.update(financial_result)

            # Step 3: Properties matched with full listings
            state.update(await bot.qualify_property_needs(state))
            match_result = await bot.match_properties(state)
            assert len(match_result["matched_properties"]) > 0

    @pytest.mark.asyncio
    async def test_buyer_budget_mismatch_gets_education(self):
        """Buyer with unrealistic budget expectations receives market education."""
        unrealistic_profile = _make_buyer_intent_profile(
            financial_readiness=35.0,
            financing_status_score=20.0,
            budget_clarity=30.0,
            urgency_score=40.0,
            market_realism=20.0,
            buyer_temperature="lukewarm",
            next_qualification_step="budget",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=unrealistic_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={
                "content": "The Rancho Cucamonga market typically starts around $500k for entry-level homes. Let me help you explore options."
            }
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=[])

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_mismatch", enable_bot_intelligence=False)

            state = _make_buyer_state(
                buyer_id="mismatch_buyer_001",
                buyer_name="Budget Mismatch Buyer",
                conversation_history=[
                    {"role": "user", "content": "I want a 4br house with pool for under $300k in Victoria"},
                ],
            )

            # Analyze intent
            intent_result = await bot.analyze_buyer_intent(state)
            state.update(intent_result)

            # Financial assessment shows low readiness
            financial_result = await bot.assess_financial_readiness(state)
            assert financial_result["financing_status"] != "pre_approved"
            state.update(financial_result)

            # Property needs show low urgency
            needs_result = await bot.qualify_property_needs(state)
            state.update(needs_result)

            # No properties match the unrealistic criteria
            match_result = await bot.match_properties(state)
            assert len(match_result.get("matched_properties", [])) == 0
            assert match_result["next_action"] in ("educate_market", "qualify_more")

    @pytest.mark.asyncio
    async def test_buyer_multi_turn_conversation_flow(self):
        """Multi-turn conversation maintains state across sequential workflow invocations."""
        # Turn 1 profile: initial discovery
        turn1_profile = _make_buyer_intent_profile(
            financial_readiness=40.0,
            urgency_score=30.0,
            buyer_temperature="lukewarm",
            next_qualification_step="financing",
        )
        # Turn 2 profile: after buyer provides more detail
        turn2_profile = _make_buyer_intent_profile(
            financial_readiness=75.0,
            urgency_score=70.0,
            financing_status_score=85.0,
            buyer_temperature="warm",
            next_qualification_step="preferences",
            conversation_turns=5,
        )

        call_count = {"n": 0}

        def _rotating_analyze(buyer_id, history):
            call_count["n"] += 1
            return turn1_profile if call_count["n"] == 1 else turn2_profile

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(side_effect=_rotating_analyze)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={"content": "Thanks for the details! With your pre-approval, we have great options in Haven."}
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(2))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_multi", enable_bot_intelligence=False)

            # --- Turn 1: Initial contact ---
            result_turn1 = await bot.process_buyer_conversation(
                buyer_id="multi_buyer_001",
                buyer_name="Multi Turn Buyer",
                conversation_history=[
                    {"role": "user", "content": "I might be interested in buying a house in Haven"},
                ],
            )
            assert result_turn1.get("is_qualified") is False
            assert result_turn1.get("financial_readiness_score") == 40.0

            # --- Turn 2: Buyer provides financing details ---
            result_turn2 = await bot.process_buyer_conversation(
                buyer_id="multi_buyer_001",
                buyer_name="Multi Turn Buyer",
                conversation_history=[
                    {"role": "user", "content": "I might be interested in buying a house in Haven"},
                    {"role": "assistant", "content": "Haven is wonderful! What is your budget situation?"},
                    {"role": "user", "content": "Just got pre-approved for $650k, need to move in 2 months"},
                ],
            )
            assert result_turn2.get("is_qualified") is True
            assert result_turn2.get("financial_readiness_score") == 75.0

            # Verify intent decoder was called twice (once per turn)
            assert mock_intent_decoder.analyze_buyer.call_count == 2


# ===========================================================================
# 3. TestSellerAnalysisFlow
# ===========================================================================


@pytest.mark.integration
class TestSellerAnalysisFlow:
    """Seller inquiry -> Qualification -> CMA / Strategy selection."""

    @pytest.fixture
    def seller_config(self):
        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig

        return JorgeFeatureConfig(
            enable_progressive_skills=False,
            enable_agent_mesh=False,
            enable_mcp_integration=False,
            enable_adaptive_questioning=False,
            enable_track3_intelligence=True,
            enable_bot_intelligence=False,
        )

    @pytest.mark.asyncio
    async def test_seller_analysis_full_flow(self, seller_config):
        """Complete: intent -> stall detection -> strategy -> response."""
        seller_profile = _make_seller_intent_profile(
            frs_total=72.0,
            pcs_total=65.0,
            frs_classification="Warm Lead",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_lead = MagicMock(return_value=seller_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(
            return_value={
                "content": "Maria, based on recent Etiwanda sales, your property could be very attractive to buyers right now."
            }
        )

        sp = _seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(tenant_id="test_seller", config=seller_config)

            result = await bot.process_seller_message(
                lead_id="seller_full_001",
                lead_name="Maria Garcia",
                history=[
                    {"role": "user", "content": "I want to sell my house at 12345 Etiwanda Ave"},
                    {"role": "assistant", "content": "Great! What is your timeline for selling?"},
                    {"role": "user", "content": "Need to sell within 60 days, relocating for work"},
                ],
            )

        # Intent was analyzed
        mock_intent_decoder.analyze_lead.assert_called_once()

        # Strategy was selected
        assert result.get("current_tone") is not None

        # Response was generated
        assert result.get("response_content") != ""

        # ML analytics were consulted for strategy
        sp["ml_analytics"].predict_lead_journey.assert_awaited()
        sp["ml_analytics"].predict_conversion_probability.assert_awaited()

    @pytest.mark.asyncio
    async def test_seller_stall_detection_and_recovery(self, seller_config):
        """Detects stall language and applies recovery strategy."""
        profile = _make_seller_intent_profile(
            frs_total=45.0,
            pcs_total=30.0,
            frs_classification="Lukewarm Lead",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_lead = MagicMock(return_value=profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(
            return_value={
                "content": "I understand you need time. Would it be helpful if I shared recent comps for your neighborhood?"
            }
        )

        sp = _seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(tenant_id="test_stall", config=seller_config)

            state = _make_seller_state(
                lead_id="stall_seller_001",
                lead_name="Stalling Steve",
                conversation_history=[
                    {"role": "user", "content": "I want to sell my house"},
                    {"role": "assistant", "content": "Great! When are you looking to sell?"},
                    {"role": "user", "content": "I need to think about it, let me get back to you next week"},
                ],
            )

            # Step 1: Analyze intent
            intent_result = await bot.analyze_intent(state)
            state.update(intent_result)
            assert state["intent_profile"] is not None

            # Step 2: Detect stall
            stall_result = await bot.detect_stall(state)
            state.update(stall_result)
            assert stall_result["stall_detected"] is True
            assert stall_result["detected_stall_type"] in ("get_back", "thinking")

            # Stall detection event was published
            sp["event_publisher"].publish_conversation_update.assert_awaited()

            # Step 3: Strategy adapts to stall
            strategy_result = await bot.select_strategy(state)
            state.update(strategy_result)
            assert state["current_tone"] == "UNDERSTANDING"

            # Step 4: Response addresses the stall
            response_result = await bot.generate_jorge_response(state)
            assert response_result["response_content"] != ""

    @pytest.mark.asyncio
    async def test_seller_hot_lead_accelerated_path(self, seller_config):
        """High-intent seller gets enthusiastic strategy and fast-tracked."""
        hot_profile = _make_seller_intent_profile(
            frs_total=88.0,
            pcs_total=82.0,
            frs_classification="Hot Lead",
            next_best_action="schedule_listing_appointment",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_lead = MagicMock(return_value=hot_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(
            return_value={
                "content": "Maria, the market is hot right now! Let us schedule a listing appointment this week."
            }
        )

        sp = _seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(tenant_id="test_hot_seller", config=seller_config)

            result = await bot.process_seller_message(
                lead_id="hot_seller_001",
                lead_name="Motivated Maria",
                history=[
                    {"role": "user", "content": "I need to sell my Victoria home urgently, relocating"},
                    {"role": "assistant", "content": "I can help with an urgent sale. What is your bottom-line price?"},
                    {"role": "user", "content": "Looking for around $800k, home is in great condition"},
                ],
            )

        # Hot lead should be qualified
        assert result.get("is_qualified") is True
        assert result.get("psychological_commitment") == 82.0

        # Strategy should be enthusiastic for high PCS
        assert result.get("current_tone") == "ENTHUSIASTIC"

        # Response content should be generated
        assert result.get("response_content") != ""

    @pytest.mark.asyncio
    async def test_seller_objection_handling_flow(self, seller_config):
        """Handles pricing objections using Zestimate stall-breaker pattern."""
        objection_profile = _make_seller_intent_profile(
            frs_total=50.0,
            pcs_total=40.0,
            frs_classification="Lukewarm Lead",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_lead = MagicMock(return_value=objection_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(
            return_value={
                "content": "Online estimates cannot see your home's unique features. Let me show you actual recent sales nearby."
            }
        )

        sp = _seller_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            bot = JorgeSellerBot(tenant_id="test_objection", config=seller_config)

            state = _make_seller_state(
                lead_id="objection_seller_001",
                lead_name="Zestimate Zelda",
                conversation_history=[
                    {"role": "user", "content": "I want to sell my house in Haven"},
                    {"role": "assistant", "content": "Haven is a great area. What price were you thinking?"},
                    {"role": "user", "content": "Zillow says my home is worth $950k, I want at least that"},
                ],
            )

            # Step 1: Analyze intent
            intent_result = await bot.analyze_intent(state)
            state.update(intent_result)

            # Step 2: Detect Zestimate stall
            stall_result = await bot.detect_stall(state)
            state.update(stall_result)
            assert stall_result["stall_detected"] is True
            assert stall_result["detected_stall_type"] == "zestimate"

            # Step 3: Strategy should address Zestimate concern
            strategy_result = await bot.select_strategy(state)
            state.update(strategy_result)
            assert state["current_tone"] == "UNDERSTANDING"

            # Step 4: Response should educate about pricing
            response_result = await bot.generate_jorge_response(state)
            assert response_result["response_content"] != ""


# ===========================================================================
# 4. TestConversationPersistence
# ===========================================================================


@pytest.mark.integration
class TestConversationPersistence:
    """State management: persistence across turns and qualification progress."""

    @pytest.mark.asyncio
    async def test_conversation_state_persists_across_turns(self):
        """State fields updated by one node are visible to subsequent nodes."""
        profile = _make_buyer_intent_profile(
            financial_readiness=70.0,
            urgency_score=60.0,
            financing_status_score=80.0,
            buyer_temperature="warm",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={"content": "Let me find matching properties for you in Central Park."}
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(2))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_persist", enable_bot_intelligence=False)

            state = _make_buyer_state(
                buyer_id="persist_buyer_001",
                buyer_name="Persistent Pete",
            )

            # Node 1: intent sets profile
            result1 = await bot.analyze_buyer_intent(state)
            state.update(result1)
            assert state["intent_profile"] is not None
            assert state["financial_readiness_score"] == 70.0

            # Node 2: financial uses the profile set by node 1
            result2 = await bot.assess_financial_readiness(state)
            state.update(result2)
            assert state["financing_status"] == "pre_approved"

            # Node 3: property needs uses profile from node 1
            result3 = await bot.qualify_property_needs(state)
            state.update(result3)
            assert state["urgency_level"] in ("immediate", "3_months")

            # Node 4: matching uses budget from node 2
            result4 = await bot.match_properties(state)
            state.update(result4)

            # State has accumulated all updates
            assert state["intent_profile"] is not None
            assert state["financing_status"] == "pre_approved"
            assert state.get("properties_viewed_count", 0) >= 0

    @pytest.mark.asyncio
    async def test_qualification_progress_preserved(self):
        """Partial qualification state is preserved when a later step has insufficient data."""
        partial_profile = _make_buyer_intent_profile(
            financial_readiness=45.0,
            urgency_score=35.0,
            financing_status_score=40.0,
            budget_clarity=30.0,
            buyer_temperature="lukewarm",
            next_qualification_step="financing",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=partial_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(return_value={"content": "Tell me more about your budget."})

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=[])

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            bot = JorgeBuyerBot(tenant_id="test_partial", enable_bot_intelligence=False)

            state = _make_buyer_state(
                buyer_id="partial_buyer_001",
                buyer_name="Partial Progress Buyer",
                conversation_history=[
                    {"role": "user", "content": "Thinking about buying, not sure about budget yet"},
                ],
            )

            # Intent analysis succeeds with partial data
            intent_result = await bot.analyze_buyer_intent(state)
            state.update(intent_result)
            assert state["intent_profile"] is not None
            assert state["current_qualification_step"] == "financing"

            # Financial assessment returns needs_approval (low financing score)
            financial_result = await bot.assess_financial_readiness(state)
            state.update(financial_result)
            assert state["financing_status"] in ("needs_approval", "unknown")

            # Property matching yields no results (no budget range extracted)
            match_result = await bot.match_properties(state)
            state.update(match_result)
            assert match_result["next_action"] == "qualify_more"

            # The qualification step from intent analysis is preserved
            assert state["current_qualification_step"] == "financing"

    @pytest.mark.asyncio
    async def test_bot_type_transition(self):
        """Lead transitions from seller bot to buyer bot with context preservation."""
        seller_profile = _make_seller_intent_profile(
            frs_total=55.0,
            pcs_total=45.0,
            frs_classification="Lukewarm Lead",
            lead_id="transition_lead_001",
        )

        buyer_profile = _make_buyer_intent_profile(
            financial_readiness=65.0,
            urgency_score=55.0,
            buyer_temperature="warm",
        )

        mock_seller_decoder = MagicMock()
        mock_seller_decoder.analyze_lead = MagicMock(return_value=seller_profile)

        mock_buyer_decoder = MagicMock()
        mock_buyer_decoder.analyze_buyer = MagicMock(return_value=buyer_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(return_value={"content": "Seller response."})
        mock_claude.generate_response = AsyncMock(return_value={"content": "Buyer response."})

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(2))

        sp = _seller_bot_patches()
        bp = _buyer_bot_patches()

        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig

        seller_config = JorgeFeatureConfig(
            enable_progressive_skills=False,
            enable_agent_mesh=False,
            enable_mcp_integration=False,
            enable_adaptive_questioning=False,
            enable_track3_intelligence=True,
            enable_bot_intelligence=False,
        )

        # Shared conversation history that evolves
        shared_history = [
            {"role": "user", "content": "I own a property in Haven but also looking to buy in Etiwanda"},
            {"role": "assistant", "content": "I can help with both! Let us start with your selling goals."},
            {"role": "user", "content": "Want to sell my Haven place for $600k and buy in Etiwanda for $700k"},
        ]

        # --- Phase 1: Seller bot processes the lead ---
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_seller_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            seller_bot = JorgeSellerBot(tenant_id="test_transition_seller", config=seller_config)

            seller_result = await seller_bot.process_seller_message(
                lead_id="transition_lead_001",
                lead_name="Dual Intent Diana",
                history=shared_history,
            )

        seller_pcs = seller_result.get("psychological_commitment", 0)
        seller_qualified = seller_result.get("is_qualified", False)

        # --- Phase 2: Buyer bot processes the same lead ---
        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_buyer_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: bp["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: bp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_transition_buyer", enable_bot_intelligence=False)

            buyer_result = await buyer_bot.process_buyer_conversation(
                buyer_id="transition_lead_001",
                buyer_name="Dual Intent Diana",
                conversation_history=shared_history,
            )

        # Context preservation: same lead processed through both bots
        assert seller_result.get("lead_id") is not None or seller_result.get("response_content") != ""
        assert buyer_result.get("buyer_id") == "transition_lead_001"

        # Both bots produced valid results from the shared conversation
        assert seller_result.get("response_content") != ""
        assert buyer_result.get("financial_readiness_score") == 65.0


# ===========================================================================
# 5. TestCrossBotCommunication
# ===========================================================================


@pytest.mark.integration
class TestCrossBotCommunication:
    """Bot handoff: lead qualification -> specialized bot routing."""

    @pytest.mark.asyncio
    async def test_lead_to_buyer_bot_handoff(self):
        """Lead qualifies as buyer -> routed to buyer bot with preserved context."""
        buyer_profile = _make_buyer_intent_profile(
            financial_readiness=80.0,
            urgency_score=72.0,
            buyer_temperature="warm",
            next_qualification_step="property_search",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_buyer = MagicMock(return_value=buyer_profile)

        mock_claude = AsyncMock()
        mock_claude.generate_response = AsyncMock(
            return_value={
                "content": "Welcome! I will be your dedicated buyer specialist for finding homes in Rancho Cucamonga."
            }
        )

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(3))

        patches = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: patches["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: patches["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_handoff_buyer", enable_bot_intelligence=False)

            # Simulate handoff: lead bot identified buyer intent and passes context
            handoff_context = {
                "lead_id": "handoff_buyer_001",
                "lead_name": "Handoff Harry",
                "identified_intent": "buyer",
                "conversation_history": [
                    {"role": "user", "content": "I am looking to buy a home in Victoria"},
                    {"role": "assistant", "content": "Let me connect you with our buyer specialist."},
                    {"role": "user", "content": "Pre-approved for $750k, want a 4br with garage"},
                ],
                "lead_score": 78,
            }

            # Buyer bot processes the handed-off lead
            result = await buyer_bot.process_buyer_conversation(
                buyer_id=handoff_context["lead_id"],
                buyer_name=handoff_context["lead_name"],
                conversation_history=handoff_context["conversation_history"],
            )

        # Buyer bot successfully processed the handoff
        assert result.get("buyer_id") == "handoff_buyer_001"
        assert result.get("is_qualified") is True
        assert result.get("financial_readiness_score") == 80.0

        # Properties were matched for the buyer
        mock_property_matcher.find_matches.assert_called()

        # Events track the buyer qualification
        patches["event_publisher"].publish_buyer_qualification_complete.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_lead_to_seller_bot_handoff(self):
        """Seller lead identified -> routed to seller bot with preserved context."""
        seller_profile = _make_seller_intent_profile(
            frs_total=70.0,
            pcs_total=60.0,
            frs_classification="Warm Lead",
            lead_id="handoff_seller_001",
        )

        mock_intent_decoder = MagicMock()
        mock_intent_decoder.analyze_lead = MagicMock(return_value=seller_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(
            return_value={
                "content": "I would love to help you sell your Central Park property. Let us discuss the market."
            }
        )

        sp = _seller_bot_patches()

        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig

        seller_config = JorgeFeatureConfig(
            enable_progressive_skills=False,
            enable_agent_mesh=False,
            enable_mcp_integration=False,
            enable_adaptive_questioning=False,
            enable_track3_intelligence=True,
            enable_bot_intelligence=False,
        )

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_intent_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            seller_bot = JorgeSellerBot(tenant_id="test_handoff_seller", config=seller_config)

            # Simulate handoff from lead bot to seller bot
            handoff_context = {
                "lead_id": "handoff_seller_001",
                "lead_name": "Seller Sam",
                "identified_intent": "seller",
                "conversation_history": [
                    {"role": "user", "content": "I own a home in Central Park and want to sell it"},
                    {"role": "assistant", "content": "I will connect you with our seller specialist."},
                    {"role": "user", "content": "Want to sell for $580k, house is 3br 2ba"},
                ],
            }

            result = await seller_bot.process_seller_message(
                lead_id=handoff_context["lead_id"],
                lead_name=handoff_context["lead_name"],
                history=handoff_context["conversation_history"],
            )

        # Seller bot processed the handoff successfully
        assert result.get("response_content") != ""
        assert result.get("intent_profile") is not None

        # Qualification was performed
        assert result.get("psychological_commitment") == 60.0

        # Events were published for the seller workflow
        sp["event_publisher"].publish_bot_status_update.assert_awaited()
        sp["event_publisher"].publish_jorge_qualification_progress.assert_awaited()

    @pytest.mark.asyncio
    async def test_intelligence_preserved_during_handoff(self):
        """Context (conversation history, scores, insights) is preserved during bot transition."""
        # Phase 1: Seller bot produces intelligence
        seller_profile = _make_seller_intent_profile(
            frs_total=60.0,
            pcs_total=50.0,
            frs_classification="Lukewarm Lead",
            lead_id="intel_handoff_001",
        )

        mock_seller_decoder = MagicMock()
        mock_seller_decoder.analyze_lead = MagicMock(return_value=seller_profile)

        mock_claude = AsyncMock()
        mock_claude.analyze_with_context = AsyncMock(return_value={"content": "Seller side response."})
        mock_claude.generate_response = AsyncMock(return_value={"content": "Buyer side response with context."})

        sp = _seller_bot_patches()

        from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeFeatureConfig

        seller_config = JorgeFeatureConfig(
            enable_progressive_skills=False,
            enable_agent_mesh=False,
            enable_mcp_integration=False,
            enable_adaptive_questioning=False,
            enable_track3_intelligence=True,
            enable_bot_intelligence=False,
        )

        conversation_history = [
            {"role": "user", "content": "I am selling my Etiwanda home but also need to buy in Victoria"},
            {"role": "assistant", "content": "I can help with both transitions. Let us discuss your sale first."},
            {"role": "user", "content": "My home is worth about $650k, and I want to buy around $800k in Victoria"},
        ]

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_seller_bot",
            LeadIntentDecoder=lambda: mock_seller_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: sp["event_publisher"],
            get_ml_analytics_engine=lambda tid: sp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            seller_bot = JorgeSellerBot(tenant_id="test_intel_seller", config=seller_config)

            seller_result = await seller_bot.process_seller_message(
                lead_id="intel_handoff_001",
                lead_name="Intel Ian",
                history=conversation_history,
            )

        # Capture seller intelligence for handoff
        seller_intelligence = {
            "seller_pcs": seller_result.get("psychological_commitment"),
            "seller_qualified": seller_result.get("is_qualified"),
            "seller_tone": seller_result.get("current_tone"),
            "conversation_history": conversation_history,
        }

        # Phase 2: Buyer bot receives the intelligence
        buyer_profile = _make_buyer_intent_profile(
            financial_readiness=70.0,
            urgency_score=60.0,
            buyer_temperature="warm",
        )

        mock_buyer_decoder = MagicMock()
        mock_buyer_decoder.analyze_buyer = MagicMock(return_value=buyer_profile)

        mock_property_matcher = MagicMock()
        mock_property_matcher.find_matches = MagicMock(return_value=_rancho_cucamonga_properties(3))

        bp = _buyer_bot_patches()

        with patch.multiple(
            "ghl_real_estate_ai.agents.jorge_buyer_bot",
            BuyerIntentDecoder=lambda: mock_buyer_decoder,
            ClaudeAssistant=lambda: mock_claude,
            get_event_publisher=lambda: bp["event_publisher"],
            PropertyMatcher=lambda: mock_property_matcher,
            get_ml_analytics_engine=lambda tid: bp["ml_analytics"],
            BOT_INTELLIGENCE_AVAILABLE=False,
        ):
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            buyer_bot = JorgeBuyerBot(tenant_id="test_intel_buyer", enable_bot_intelligence=False)

            # Buyer bot receives the same conversation history (intelligence preserved)
            buyer_result = await buyer_bot.process_buyer_conversation(
                buyer_id="intel_handoff_001",
                buyer_name="Intel Ian",
                conversation_history=seller_intelligence["conversation_history"],
            )

        # Conversation history was preserved through handoff
        assert mock_buyer_decoder.analyze_buyer.call_args[0][1] == conversation_history

        # Both bots produced results from the shared context
        assert seller_result.get("response_content") != ""
        assert buyer_result.get("buyer_id") == "intel_handoff_001"

        # Seller intelligence is available for decision making
        assert seller_intelligence["seller_pcs"] is not None
        assert seller_intelligence["seller_qualified"] is not None

        # Buyer bot qualified the lead independently
        assert buyer_result.get("financial_readiness_score") == 70.0
        assert buyer_result.get("is_qualified") is True


# ===========================================================================
# 6. TestCrossBotHandoffService
# ===========================================================================


@pytest.mark.integration
class TestCrossBotHandoffService:
    """End-to-end: handoff service evaluates intent and generates tag swap actions."""

    @pytest.mark.asyncio
    async def test_lead_qualifies_as_buyer_full_flow(self):
        """Lead bot -> handoff service detects buyer intent -> tag swap to buyer bot."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            JorgeHandoffService,
        )

        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()
        service = JorgeHandoffService(analytics_service=mock_analytics)

        # Step 1: Extract intent signals from a buyer-intent message
        # Message must trigger 3+ patterns to exceed 0.7 threshold
        msg = "I want to buy a 3BR house, I'm pre-approved with budget around $680k"
        signals = JorgeHandoffService.extract_intent_signals(msg)
        assert signals["buyer_intent_score"] >= 0.7

        # Step 2: Evaluate handoff from lead bot
        decision = await service.evaluate_handoff(
            current_bot="lead",
            contact_id="flow_lead_001",
            conversation_history=[
                {"role": "user", "content": msg},
            ],
            intent_signals=signals,
        )
        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"

        # Step 3: Execute handoff and verify tag actions
        actions = await service.execute_handoff(decision, contact_id="flow_lead_001")

        remove_tags = [a["tag"] for a in actions if a["type"] == "remove_tag"]
        add_tags = [a["tag"] for a in actions if a["type"] == "add_tag"]

        assert "Needs Qualifying" in remove_tags
        assert "Buyer-Lead" in add_tags
        assert "Handoff-Lead-to-Buyer" in add_tags

        # Step 4: Analytics event was logged
        mock_analytics.track_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_seller_also_buying_full_flow(self):
        """Seller bot -> handoff service detects buyer intent -> tag swap to buyer bot."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            JorgeHandoffService,
        )

        mock_analytics = AsyncMock()
        mock_analytics.track_event = AsyncMock()
        service = JorgeHandoffService(analytics_service=mock_analytics)

        # Seller mentions they also need to find a new place (threshold 0.6)
        signals = {
            "buyer_intent_score": 0.7,
            "seller_intent_score": 0.2,
            "detected_intent_phrases": ["also looking to buy", "need to find a new place"],
        }

        decision = await service.evaluate_handoff(
            current_bot="seller",
            contact_id="flow_seller_001",
            conversation_history=[
                {"role": "user", "content": "Selling my house but also need to find a new place in Victoria"},
            ],
            intent_signals=signals,
        )
        assert decision is not None
        assert decision.source_bot == "seller"
        assert decision.target_bot == "buyer"

        actions = await service.execute_handoff(decision, contact_id="flow_seller_001")

        remove_tags = [a["tag"] for a in actions if a["type"] == "remove_tag"]
        add_tags = [a["tag"] for a in actions if a["type"] == "add_tag"]

        assert "Needs Qualifying" in remove_tags  # seller's tag
        assert "Buyer-Lead" in add_tags
        assert "Handoff-Seller-to-Buyer" in add_tags
        mock_analytics.track_event.assert_called_once()
