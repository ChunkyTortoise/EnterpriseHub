from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.lead_scoring import (
    FinancialReadinessScore,
    LeadIntentProfile,
    PsychologicalCommitmentScore,
)


@pytest.fixture
def mock_jorge_deps():
    mock_event_pub = AsyncMock()
    mock_ml = AsyncMock()
    mock_ml.predict_lead_journey = AsyncMock(return_value={})
    mock_ml.predict_conversion_probability = AsyncMock(return_value={"probability": 0.5})
    mock_ml.predict_optimal_touchpoints = AsyncMock(return_value={})

    with (
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder") as MockIntent,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.SellerIntentDecoder") as MockSellerIntent,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant") as MockClaude,
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher", return_value=mock_event_pub),
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine", return_value=mock_ml),
        patch("ghl_real_estate_ai.agents.jorge_seller_bot.GHLWorkflowService") as MockWorkflowService,
    ):
        seller_intent_instance = MockSellerIntent.return_value
        seller_intent_instance.analyze_seller = MagicMock(return_value=MagicMock())

        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.classification = "Warm Lead"
        mock_profile.frs.total_score = 40
        mock_profile.pcs = MagicMock()
        mock_profile.pcs.total_score = 50
        mock_profile.pcs.response_velocity_score = 70
        mock_profile.pcs.message_length_score = 70
        mock_profile.pcs.question_depth_score = 70
        mock_profile.pcs.objection_handling_score = 70
        mock_profile.pcs.call_acceptance_score = 70
        mock_profile.lead_id = "lead_123"
        mock_profile.lead_type = "seller"
        mock_profile.market_context = "rancho_cucamonga"
        mock_profile.next_best_action = "continue_qualification"
        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.analyze_with_context = AsyncMock(return_value={"content": "Mocked Jorge Response"})

        workflow_instance = MockWorkflowService.return_value
        workflow_instance.apply_auto_tags = AsyncMock(return_value={"success": True})

        yield {
            "intent": intent_instance,
            "claude": claude_instance,
            "profile": mock_profile,
            "workflow": workflow_instance,
        }


@pytest.mark.asyncio
async def test_jorge_seller_bot_stall_breaking(mock_jorge_deps):
    """Test that the bot processes a stall message and returns a valid response."""
    bot = JorgeSellerBot()

    history = [
        {"role": "user", "content": "I need to think about it."}
    ]

    result = await bot.process_seller_message(
        conversation_id="lead_123",
        user_message="I need to think about it.",
        seller_name="John Doe",
        conversation_history=history,
    )

    assert result["lead_id"] == "lead_123"
    assert "response_content" in result
    assert isinstance(result["frs_score"], (int, float))
    assert isinstance(result["handoff_signals"], dict)
    mock_jorge_deps["workflow"].apply_auto_tags.assert_awaited_once()


@pytest.mark.asyncio
async def test_jorge_seller_bot_educational_mode(mock_jorge_deps):
    """Test that low PCS still produces a valid response through the workflow."""
    mock_jorge_deps["profile"].pcs.total_score = 10

    bot = JorgeSellerBot()

    history = [{"role": "user", "content": "Just curious about value."}]

    result = await bot.process_seller_message(
        conversation_id="lead_low",
        user_message="Just curious about value.",
        seller_name="Tire Kicker",
        conversation_history=history,
    )

    assert result["lead_id"] == "lead_low"
    assert "response_content" in result
    assert isinstance(result["frs_score"], (int, float))
    assert isinstance(result["handoff_signals"], dict)


def test_budget_keyword_under_500_maps_to_500k(mock_jorge_deps):
    """Regression: 'under 500' should map to budget_max=500000, not 700000."""
    bot = JorgeSellerBot()
    preferences = bot._extract_preferences_from_conversation(
        [{"role": "user", "content": "I'm looking for something under 500 in this area"}]
    )

    assert preferences["budget_max"] == 500000
