import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile, FinancialReadinessScore, PsychologicalCommitmentScore

@pytest.fixture
def mock_jorge_deps():
    with patch('ghl_real_estate_ai.agents.jorge_seller_bot.LeadIntentDecoder') as MockIntent, \
         patch('ghl_real_estate_ai.agents.jorge_seller_bot.ClaudeAssistant') as MockClaude:
        
        intent_instance = MockIntent.return_value
        mock_profile = MagicMock(spec=LeadIntentProfile)
        mock_profile.frs = MagicMock(spec=FinancialReadinessScore)
        mock_profile.frs.classification = "Warm Lead"
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
    """Test that the bot detects a stall and selects confrontational tone."""
    bot = JorgeSellerBot()
    
    history = [
        {"role": "user", "content": "I need to think about it."} # Stall keyword "think"
    ]
    
    result = await bot.process_seller_message("lead_123", "John Doe", history)
    
    assert result['stall_detected'] is True
    assert result['detected_stall_type'] == "thinking"
    assert result['current_tone'] == "CONFRONTATIONAL"
    assert result['response_content'] == "Mocked Jorge Response"

@pytest.mark.asyncio
async def test_jorge_seller_bot_take_away_mode(mock_jorge_deps):
    """Test that low PCS triggers take-away mode."""
    mock_jorge_deps['profile'].pcs.total_score = 10 # Low commitment
    
    bot = JorgeSellerBot()
    
    history = [
        {"role": "user", "content": "Just curious about value."}
    ]
    
    result = await bot.process_seller_message("lead_low", "Tire Kicker", history)
    
    assert result['stall_detected'] is False
    assert result['current_tone'] == "TAKE-AWAY"
    assert "TAKE-AWAY" in str(mock_jorge_deps['claude'].analyze_with_context.call_args)
