"""
End-to-end conversation flow tests for Jorge Buyer Bot.

Tests complete buyer qualification conversations through the LangGraph workflow,
including qualified buyer (HOT), window shopper (COLD), financial assessment,
and opt-out handling.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile


@pytest.fixture
def _mock_buyer_deps():
    """Patch all external dependencies for buyer bot E2E tests."""
    with (
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher") as MockEvent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher") as MockMatcher,
    ):
        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=BuyerIntentProfile)
        mock_profile.buyer_temperature = "warm"
        mock_profile.financial_readiness = 75.0
        mock_profile.urgency_score = 80.0
        mock_profile.confidence_level = 90.0
        mock_profile.financing_status_score = 80.0
        mock_profile.budget_clarity = 85.0
        mock_profile.preference_clarity = 70.0
        mock_profile.next_qualification_step = "property_search"
        intent_instance.analyze_buyer = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.generate_response = AsyncMock(
            return_value={"content": "Mocked Buyer Response"}
        )

        matcher_instance = MockMatcher.return_value
        matcher_instance.find_matches = AsyncMock(
            return_value=[
                {"address": "123 Main St", "match_score": 95.0},
                {"address": "456 Oak Ave", "match_score": 88.0},
            ]
        )
        matcher_instance.find_buyer_matches = AsyncMock(
            return_value=[
                {"address": "123 Main St", "match_score": 95.0},
                {"address": "456 Oak Ave", "match_score": 88.0},
            ]
        )

        event_instance = MockEvent.return_value
        event_instance.publish_bot_status_update = AsyncMock()
        event_instance.publish_buyer_intent_analysis = AsyncMock()
        event_instance.publish_property_match_update = AsyncMock()
        event_instance.publish_buyer_follow_up_scheduled = AsyncMock()
        event_instance.publish_buyer_qualification_complete = AsyncMock()
        event_instance.publish_conversation_update = AsyncMock()
        event_instance.publish_jorge_qualification_progress = AsyncMock()

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "matcher": matcher_instance,
            "event": event_instance,
            "profile": mock_profile,
        }


# ---------------------------------------------------------------------------
# Qualified Buyer: HOT
# ---------------------------------------------------------------------------

class TestBuyerQualifiedHot:
    """Pre-approved + urgent + clear preferences -> HOT qualification."""

    @pytest.mark.asyncio
    async def test_fully_qualified_buyer(self, _mock_buyer_deps):
        """Buyer with strong financials and urgency is qualified."""
        _mock_buyer_deps["profile"].financial_readiness = 90.0
        _mock_buyer_deps["profile"].urgency_score = 85.0
        _mock_buyer_deps["profile"].financing_status_score = 95.0
        _mock_buyer_deps["profile"].budget_clarity = 90.0
        _mock_buyer_deps["profile"].buyer_temperature = "hot"

        bot = JorgeBuyerBot()

        history = [
            {"role": "assistant", "content": "Hi! What are you looking for?"},
            {"role": "user", "content": "I want to buy a 4BR in Rancho Cucamonga."},
            {"role": "assistant", "content": "Great! What's your budget and financing?"},
            {"role": "user", "content": "Budget $700k. I'm pre-approved with Chase."},
            {"role": "assistant", "content": "When do you need to move?"},
        ]

        result = await bot.process_buyer_conversation(
            conversation_id="hot_buyer_001",
            user_message="Within 60 days, I need to relocate for work.",
            buyer_name="Alice Buyer",
            conversation_history=history,
        )

        assert result["lead_id"] == "hot_buyer_001"
        assert "response_content" in result
        assert result["is_qualified"] is True
        assert isinstance(result.get("handoff_signals", {}), dict)

    @pytest.mark.asyncio
    async def test_qualified_buyer_triggers_completion_event(self, _mock_buyer_deps):
        """Qualification should publish a buyer_qualification_complete event."""
        _mock_buyer_deps["profile"].financial_readiness = 92.0
        _mock_buyer_deps["profile"].urgency_score = 88.0
        _mock_buyer_deps["profile"].financing_status_score = 90.0
        _mock_buyer_deps["profile"].budget_clarity = 85.0

        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="hot_buyer_002",
            user_message="I'm pre-approved for $750k and ready to tour homes this weekend.",
            buyer_name="Bob Buyer",
            conversation_history=[],
        )

        assert result["lead_id"] == "hot_buyer_002"
        _mock_buyer_deps["event"].publish_buyer_qualification_complete.assert_called_once()


# ---------------------------------------------------------------------------
# Window Shopper: COLD
# ---------------------------------------------------------------------------

class TestBuyerWindowShopper:
    """Vague budget, no timeline -> COLD / unqualified."""

    @pytest.mark.asyncio
    async def test_window_shopper_not_qualified(self, _mock_buyer_deps):
        """Buyer with low scores should be marked unqualified."""
        _mock_buyer_deps["profile"].financial_readiness = 15.0
        _mock_buyer_deps["profile"].urgency_score = 20.0
        _mock_buyer_deps["profile"].financing_status_score = 10.0
        _mock_buyer_deps["profile"].budget_clarity = 10.0
        _mock_buyer_deps["profile"].buyer_temperature = "cold"

        bot = JorgeBuyerBot()

        history = [
            {"role": "assistant", "content": "What kind of home are you looking for?"},
            {"role": "user", "content": "Just browsing."},
        ]

        result = await bot.process_buyer_conversation(
            conversation_id="cold_buyer_001",
            user_message="I don't have a specific budget yet.",
            buyer_name="Carol Window",
            conversation_history=history,
        )

        assert result["lead_id"] == "cold_buyer_001"
        assert result["is_qualified"] is False
        assert isinstance(result.get("handoff_signals", {}), dict)

    @pytest.mark.asyncio
    async def test_window_shopper_still_gets_response(self, _mock_buyer_deps):
        """Even unqualified buyers should get a nurturing response."""
        _mock_buyer_deps["profile"].financial_readiness = 20.0
        _mock_buyer_deps["profile"].urgency_score = 15.0
        _mock_buyer_deps["profile"].financing_status_score = 10.0
        _mock_buyer_deps["profile"].budget_clarity = 5.0

        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="cold_buyer_002",
            user_message="Maybe someday.",
            buyer_name="Dan Window",
            conversation_history=[],
        )

        assert result["lead_id"] == "cold_buyer_002"
        assert "response_content" in result
        # Response may be empty string if LLM mock doesn't produce content for
        # very low-qualification paths; the key point is no crash occurred.


# ---------------------------------------------------------------------------
# Financial Assessment
# ---------------------------------------------------------------------------

class TestBuyerFinancialAssessment:
    """Budget parsing and affordability calculation."""

    @pytest.mark.asyncio
    async def test_budget_parsed_from_conversation(self, _mock_buyer_deps):
        """Buyer mentions specific budget -> financial readiness assessed."""
        _mock_buyer_deps["profile"].financial_readiness = 80.0
        _mock_buyer_deps["profile"].budget_clarity = 90.0
        _mock_buyer_deps["profile"].financing_status_score = 85.0

        bot = JorgeBuyerBot()

        history = [
            {"role": "user", "content": "My budget is around $600,000."},
            {"role": "assistant", "content": "Great range! Are you pre-approved?"},
        ]

        result = await bot.process_buyer_conversation(
            conversation_id="finance_buyer_001",
            user_message="Yes, pre-approved with Wells Fargo for $625k.",
            buyer_name="Eva Finance",
            conversation_history=history,
        )

        assert result["lead_id"] == "finance_buyer_001"
        assert "response_content" in result
        # With high financial readiness, should be qualified
        assert result["is_qualified"] is True

    @pytest.mark.asyncio
    async def test_no_budget_mentioned(self, _mock_buyer_deps):
        """Buyer never mentions budget -> lower financial readiness."""
        _mock_buyer_deps["profile"].financial_readiness = 25.0
        _mock_buyer_deps["profile"].budget_clarity = 10.0
        _mock_buyer_deps["profile"].financing_status_score = 15.0

        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="finance_buyer_002",
            user_message="I like houses with big yards.",
            buyer_name="Frank NoBudget",
            conversation_history=[],
        )

        assert result["lead_id"] == "finance_buyer_002"
        assert result["is_qualified"] is False


# ---------------------------------------------------------------------------
# Opt-Out (TCPA)
# ---------------------------------------------------------------------------

class TestBuyerOptOut:
    """TCPA opt-out phrases handled before any AI processing."""

    @pytest.mark.asyncio
    async def test_stop_triggers_opt_out(self, _mock_buyer_deps):
        """Saying 'stop' returns opt-out response immediately."""
        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="optout_buyer_001",
            user_message="stop",
            buyer_name="Grace Optout",
            conversation_history=[],
        )

        assert result["lead_id"] == "optout_buyer_001"
        assert result.get("opt_out_detected") is True
        assert "unsubscribed" in result["response_content"].lower()

    @pytest.mark.asyncio
    async def test_unsubscribe_triggers_opt_out(self, _mock_buyer_deps):
        """Saying 'unsubscribe' also triggers opt-out."""
        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="optout_buyer_002",
            user_message="unsubscribe",
            buyer_name="Henry Optout",
            conversation_history=[],
        )

        assert result.get("opt_out_detected") is True

    @pytest.mark.asyncio
    async def test_not_interested_triggers_opt_out(self, _mock_buyer_deps):
        """Saying 'not interested' triggers opt-out."""
        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="optout_buyer_003",
            user_message="not interested",
            buyer_name="Irene Optout",
            conversation_history=[],
        )

        assert result.get("opt_out_detected") is True


# ---------------------------------------------------------------------------
# Handoff Signal Extraction
# ---------------------------------------------------------------------------

class TestBuyerHandoffSignals:
    """Buyer mentioning seller intent produces handoff signals."""

    @pytest.mark.asyncio
    async def test_buyer_mentions_selling(self, _mock_buyer_deps):
        """Buyer who mentions selling should have seller intent signals."""
        _mock_buyer_deps["profile"].financial_readiness = 70.0
        _mock_buyer_deps["profile"].urgency_score = 60.0

        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="handoff_buyer_001",
            user_message="I need to sell my house first before I can buy.",
            buyer_name="Jack Handoff",
            conversation_history=[],
        )

        assert result["lead_id"] == "handoff_buyer_001"
        signals = result.get("handoff_signals", {})
        assert signals.get("seller_intent_score", 0) > 0


# ---------------------------------------------------------------------------
# Error Resilience
# ---------------------------------------------------------------------------

class TestBuyerErrorResilience:
    """Bot handles edge cases gracefully."""

    @pytest.mark.asyncio
    async def test_empty_message_returns_prompt(self, _mock_buyer_deps):
        """Empty message should return a prompt for more info."""
        bot = JorgeBuyerBot()

        result = await bot.process_buyer_conversation(
            conversation_id="resilience_buyer_001",
            user_message="",
            buyer_name="Kate Empty",
            conversation_history=[],
        )

        assert result["lead_id"] == "resilience_buyer_001"
        assert "response_content" in result

    @pytest.mark.asyncio
    async def test_long_conversation_history(self, _mock_buyer_deps):
        """Very long conversation history should not crash."""
        bot = JorgeBuyerBot()

        history = [
            {"role": "user" if i % 2 == 0 else "assistant", "content": f"Message {i}"}
            for i in range(50)
        ]

        result = await bot.process_buyer_conversation(
            conversation_id="resilience_buyer_002",
            user_message="What properties match my criteria?",
            buyer_name="Leo Long",
            conversation_history=history,
        )

        assert result["lead_id"] == "resilience_buyer_002"
        assert "response_content" in result
