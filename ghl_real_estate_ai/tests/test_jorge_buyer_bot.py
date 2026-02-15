from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile


@pytest.fixture
def mock_buyer_deps():
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
        claude_instance.generate_response = AsyncMock(return_value={"content": "Mocked Buyer Response"})

        matcher_instance = MockMatcher.return_value
        matcher_instance.find_matches = AsyncMock(
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

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "matcher": matcher_instance,
            "event": event_instance,
            "profile": mock_profile,
        }


@pytest.mark.asyncio
async def test_jorge_buyer_bot_qualification_flow(mock_buyer_deps):
    """Test the complete buyer qualification workflow."""
    bot = JorgeBuyerBot()

    history = [{"role": "user", "content": "I want to buy a house in Rancho Cucamonga for $700k. I am pre-approved."}]

    result = await bot.process_buyer_conversation(
        conversation_id="buyer_123",
        user_message="I want to buy a house in Rancho Cucamonga for $700k. I am pre-approved.",
        buyer_name="Jane Doe",
        conversation_history=history,
    )

    assert result["lead_id"] == "buyer_123"
    assert "response_content" in result
    assert "is_qualified" in result
    assert "financial_readiness_score" in result or "financial_readiness" in result
    assert isinstance(result.get("handoff_signals", {}), dict)

    # Verify buyer qualification complete event was published
    mock_buyer_deps["event"].publish_buyer_qualification_complete.assert_called_once()


@pytest.mark.asyncio
async def test_jorge_buyer_bot_low_qualification(mock_buyer_deps):
    """Test that low scores lead to unqualified status."""
    mock_buyer_deps["profile"].financial_readiness = 20.0
    mock_buyer_deps["profile"].urgency_score = 30.0
    mock_buyer_deps["profile"].financing_status_score = 10.0
    mock_buyer_deps["profile"].budget_clarity = 10.0

    bot = JorgeBuyerBot()

    history = [{"role": "user", "content": "Just looking around."}]

    result = await bot.process_buyer_conversation(
        conversation_id="buyer_low",
        user_message="Just looking around.",
        buyer_name="Window Shopper",
        conversation_history=history,
    )

    assert result["is_qualified"] is False
    assert result["lead_id"] == "buyer_low"
    assert isinstance(result.get("handoff_signals", {}), dict)
