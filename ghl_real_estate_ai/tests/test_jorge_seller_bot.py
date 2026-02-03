import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile, FinancialReadinessScore, PsychologicalCommitmentScore

@pytest.fixture
def mock_jorge_deps():
    mock_event_pub = AsyncMock()
    mock_ml = AsyncMock()
    mock_ml.predict_lead_journey = AsyncMock(return_value={})
    mock_ml.predict_conversion_probability = AsyncMock(return_value={"probability": 0.5})
    mock_ml.predict_optimal_touchpoints = AsyncMock(return_value={})

    with patch('ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder') as MockIntent, \
         patch('ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant') as MockClaude, \
         patch('ghl_real_estate_ai.agents.jorge_seller_bot.get_event_publisher', return_value=mock_event_pub), \
         patch('ghl_real_estate_ai.agents.jorge_seller_bot.get_ml_analytics_engine', return_value=mock_ml):

        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.classification = "Warm Lead"
        mock_profile.frs.total_score = 40
        mock_profile.pcs = MagicMock(spec=PsychologicalCommitmentScore)
        mock_profile.pcs.total_score = 50
        intent_instance.analyze_lead = MagicMock(return_value=mock_profile)

        claude_instance = MockClaude.return_value
        claude_instance.analyze_with_context = AsyncMock(return_value={"content": "Mocked Jorge Response"})

        yield {
            'intent': intent_instance,
            'claude': claude_instance,
            'profile': mock_profile
        }

@pytest.mark.asyncio
async def test_jorge_seller_bot_stall_breaking(mock_jorge_deps):
    """Test that the bot detects a stall and selects understanding tone."""
    bot = JorgeSellerBot()

    history = [
        {"role": "user", "content": "I need to think about it."}  # Stall keyword "think"
    ]

    result = await bot.process_seller_message("lead_123", "John Doe", history)

    assert result['stall_detected'] is True
    assert result['detected_stall_type'] == "thinking"
    assert result['current_tone'] == "UNDERSTANDING"
    assert result['response_content'] == "Mocked Jorge Response"

@pytest.mark.asyncio
async def test_jorge_seller_bot_educational_mode(mock_jorge_deps):
    """Test that low PCS triggers educational tone (supportive approach)."""
    mock_jorge_deps['profile'].pcs.total_score = 10  # Low commitment

    bot = JorgeSellerBot()

    history = [
        {"role": "user", "content": "Just curious about value."}
    ]

    result = await bot.process_seller_message("lead_low", "Tire Kicker", history)

    assert result['stall_detected'] is False
    assert result['current_tone'] == "EDUCATIONAL"
    assert "EDUCATIONAL" in str(mock_jorge_deps['claude'].analyze_with_context.call_args)
