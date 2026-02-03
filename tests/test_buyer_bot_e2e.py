"""
B2: End-to-end test for Jorge Buyer Bot 6-node workflow.
Tests that the buyer bot can process a conversation without errors.
"""
import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch


def create_mock_buyer_intent_profile():
    """Create a realistic BuyerIntentProfile mock."""
    profile = MagicMock()
    profile.financial_readiness = 65.0
    profile.budget_clarity = 70.0
    profile.financing_status_score = 60.0
    profile.urgency_score = 55.0
    profile.timeline_pressure = 50.0
    profile.consequence_awareness = 40.0
    profile.preference_clarity = 80.0
    profile.market_realism = 60.0
    profile.decision_authority = 75.0
    profile.buyer_temperature = "warm"
    profile.confidence_level = 0.7
    profile.conversation_turns = 3
    profile.key_insights = {"budget_mentioned": True, "area_preference": "Rancho Cucamonga"}
    profile.next_qualification_step = "financial_verification"
    return profile


def create_mock_event_publisher():
    """Create mock event publisher with all required async methods."""
    publisher = MagicMock()
    publisher.publish_bot_status_update = AsyncMock()
    publisher.publish_buyer_intent_analysis = AsyncMock()
    publisher.publish_property_match_update = AsyncMock()
    publisher.publish_buyer_follow_up_scheduled = AsyncMock()
    publisher.publish_buyer_qualification_complete = AsyncMock()
    return publisher


async def test_buyer_bot_workflow():
    """Test buyer bot end-to-end with mock state simulating a real buyer inquiry."""

    conversation_history = [
        {"role": "user", "content": "Hi, I'm looking for a home in Rancho Cucamonga"},
        {"role": "assistant", "content": "Great! What size home are you looking for and whats your budget?"},
        {"role": "user", "content": "I want a 4 bedroom house, budget is under $700k"},
        {"role": "assistant", "content": "Are you pre-approved for financing?"},
        {"role": "user", "content": "Yes I got pre-approved last week for up to $700k"},
    ]

    mock_profile = create_mock_buyer_intent_profile()
    mock_publisher = create_mock_event_publisher()

    sample_matches = [
        {
            "id": "prop_002",
            "address": "8721 Haven Ave, Rancho Cucamonga, CA 91730",
            "price": 599000,
            "beds": 4,
            "baths": 2,
            "description": "Spacious 4bd/2ba near Haven",
            "match_score": 1.5,
        },
        {
            "id": "prop_004",
            "address": "10382 Victoria St, Rancho Cucamonga, CA 91730",
            "price": 650000,
            "beds": 4,
            "baths": 3,
            "description": "Recently renovated 4bd/3ba in Victoria",
            "match_score": 1.3,
        },
    ]

    with patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder") as MockDecoder, \
         patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant") as MockClaude, \
         patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher", return_value=mock_publisher), \
         patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher") as MockMatcher, \
         patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_ml_analytics_engine") as MockML, \
         patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BOT_INTELLIGENCE_AVAILABLE", False):

        # Configure mocks
        mock_decoder_instance = MockDecoder.return_value
        mock_decoder_instance.analyze_buyer.return_value = mock_profile

        mock_claude_instance = MockClaude.return_value
        mock_claude_instance.generate_response = AsyncMock(return_value={
            "content": "Found some great options matching your criteria in Rancho Cucamonga"
        })

        mock_matcher_instance = MockMatcher.return_value
        mock_matcher_instance.find_matches.return_value = sample_matches

        mock_ml_instance = MockML.return_value

        # Import and instantiate after patching
        from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

        bot = JorgeBuyerBot(tenant_id="test_buyer", enable_bot_intelligence=False)

        # Run the workflow
        result = await bot.process_buyer_conversation(
            buyer_id="test_buyer_001",
            buyer_name="Test Buyer",
            conversation_history=conversation_history,
        )

        # Verify results
        print(f"Workflow completed successfully!")
        print(f"  buyer_id: {result.get('buyer_id', 'N/A')}")
        print(f"  qualification_status: {result.get('qualification_status', 'N/A')}")
        print(f"  response_content: {result.get('response_content', 'N/A')[:80]}")
        print(f"  is_qualified: {result.get('is_qualified', 'N/A')}")
        print(f"  matched_properties: {len(result.get('matched_properties', []))}")
        print(f"  buyer_temperature: {result.get('buyer_temperature', 'N/A')}")

        # Assertions
        assert result.get("qualification_status") != "error", \
            f"Workflow produced an error: {result.get('error')}"

        # Workflow should complete with either a response or a scheduled action
        has_response = bool(result.get("response_content"))
        has_scheduled = result.get("follow_up_scheduled", False)
        has_next_action = bool(result.get("next_action"))
        assert has_response or has_scheduled or has_next_action, \
            "Workflow produced no response, no scheduled action, and no next action"

        print("\nAll buyer bot E2E assertions passed!")
        return result


if __name__ == "__main__":
    result = asyncio.run(test_buyer_bot_workflow())
    sys.exit(0 if result else 1)
