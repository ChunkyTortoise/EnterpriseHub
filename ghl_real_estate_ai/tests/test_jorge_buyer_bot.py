from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot
from ghl_real_estate_ai.models.buyer_persona import BuyerPersonaType
from ghl_real_estate_ai.models.lead_scoring import BuyerIntentProfile


@pytest.fixture
def mock_buyer_deps():
    with (
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_event_publisher") as MockEvent,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.PropertyMatcher") as MockMatcher,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLClient") as MockGhlClient,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.GHLWorkflowService") as MockWorkflowService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.ChurnDetectionService") as MockChurnService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.LeadScoringIntegration") as MockLeadScoring,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.SentimentAnalysisService") as MockSentiment,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.BuyerPersonaService") as MockPersonaService,
        patch("ghl_real_estate_ai.agents.jorge_buyer_bot.get_buyer_conversation_memory") as MockConversationMemory,
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

        workflow_instance = MockWorkflowService.return_value
        workflow_instance.apply_auto_tags = AsyncMock(return_value={"success": True})

        lead_scoring_instance = MockLeadScoring.return_value
        lead_scoring_instance.calculate_and_store_composite_score = AsyncMock(
            return_value={"composite_score_data": {"total_score": 72.0}}
        )

        churn_instance = MockChurnService.return_value
        churn_instance.assess_churn_risk = AsyncMock(
            return_value=SimpleNamespace(
                risk_score=18.0,
                risk_level=SimpleNamespace(value="low"),
                recommended_action=SimpleNamespace(value="value_reminder"),
            )
        )

        sentiment_instance = MockSentiment.return_value
        sentiment_instance.analyze_sentiment = AsyncMock(
            return_value=SimpleNamespace(sentiment=SimpleNamespace(value="neutral"), confidence=0.8, escalation_required=SimpleNamespace(value="none"))
        )
        sentiment_instance.get_response_tone_adjustment = MagicMock(return_value={"tone": "professional", "pace": "normal"})

        persona_instance = MockPersonaService.return_value
        persona_instance.classify_buyer_type = AsyncMock(
            return_value=SimpleNamespace(persona_type=BuyerPersonaType.UNKNOWN, confidence=0.5, detected_signals=[])
        )
        persona_instance.get_persona_insights = AsyncMock(
            return_value=SimpleNamespace(model_dump=lambda: {"tone": "friendly", "content_focus": "general"})
        )

        ghl_client_instance = MockGhlClient.return_value
        ghl_client_instance.add_contact_tags = AsyncMock()
        ghl_client_instance.add_contact_note = AsyncMock()
        ghl_client_instance.send_message = AsyncMock()

        conversation_memory = MockConversationMemory.return_value
        conversation_memory.enabled = False
        conversation_memory.load_state = AsyncMock(return_value=None)
        conversation_memory.save_state = AsyncMock()

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "matcher": matcher_instance,
            "event": event_instance,
            "profile": mock_profile,
            "workflow": workflow_instance,
        }


@pytest.mark.asyncio
async def test_jorge_buyer_bot_qualification_flow(mock_buyer_deps):
    """Test the complete buyer qualification workflow."""
    bot = JorgeBuyerBot(enable_bot_intelligence=False)

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
    mock_buyer_deps["workflow"].apply_auto_tags.assert_awaited_once()


@pytest.mark.asyncio
async def test_jorge_buyer_bot_low_qualification(mock_buyer_deps):
    """Test that low scores lead to unqualified status."""
    mock_buyer_deps["profile"].financial_readiness = 20.0
    mock_buyer_deps["profile"].urgency_score = 30.0
    mock_buyer_deps["profile"].financing_status_score = 10.0
    mock_buyer_deps["profile"].budget_clarity = 10.0

    bot = JorgeBuyerBot(enable_bot_intelligence=False)

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


@pytest.mark.asyncio
async def test_gather_buyer_intelligence_calls_enhance_bot_context(mock_buyer_deps):
    """Regression: Buyer bot should call enhance_bot_context with updated middleware signature."""
    bot = JorgeBuyerBot(enable_bot_intelligence=False)

    bot.intelligence_middleware = MagicMock()
    bot.intelligence_middleware.enhance_bot_context = AsyncMock(return_value=SimpleNamespace())

    state = {
        "buyer_id": "buyer_999",
        "location_id": "rancho_cucamonga",
        "conversation_history": [{"role": "user", "content": "Budget around 700k"}],
        "property_preferences": {"beds": 3},
        "budget_range": {"max": 700000},
        "urgency_level": "high",
    }

    result = await bot.gather_buyer_intelligence(state)

    assert "intelligence_context" in result
    bot.intelligence_middleware.enhance_bot_context.assert_awaited_once_with(
        bot_type="jorge-buyer",
        lead_id="buyer_999",
        location_id="rancho_cucamonga",
        conversation_context=state["conversation_history"],
        preferences={
            "property_preferences": {"beds": 3},
            "budget_range": {"max": 700000},
            "urgency_level": "high",
        },
    )
