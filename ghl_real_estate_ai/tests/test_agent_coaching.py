"""
Tests for Real-Time Agent Coaching Service.
"""

import pytest

from ghl_real_estate_ai.services.agent_coaching import AgentCoachingService, CoachingTip



@pytest.fixture
def coaching_service():
    return AgentCoachingService()


def test_analyze_conversation_buying_signal(coaching_service):
    """Test detecting buying signals."""
    history = [
        {"sender": "agent", "message": "How can I help?"},
        {"sender": "lead", "message": "I am ready to move forward"},
    ]
    context = {"name": "John"}
    tips = coaching_service.analyze_conversation_live(history, context)

    assert len(tips) > 0
    assert any("Buying Signal" in tip.title for tip in tips)


def test_analyze_conversation_location(coaching_service):
    """Test detecting location mentions."""
    history = [{"sender": "lead", "message": "I like miami beach"}]
    context = {"name": "Jane"}
    tips = coaching_service.analyze_conversation_live(history, context)

    assert any("Location Mentioned" in tip.title for tip in tips)


def test_get_jorge_template(coaching_service):
    """Test getting Jorge-style templates."""
    context = {"name": "Bob", "location": "Brickell"}
    template = coaching_service.get_jorge_template("budget", context)
    # The actual template is "What price range are you comfortable with? Ballpark is fine."
    assert "price range" in template.lower()

    reengagement = coaching_service.get_jorge_template("reengagement", context)
    assert "Bob" in reengagement
    assert "Brickell" in reengagement


def test_analyze_agent_performance(coaching_service):
    """Test agent performance analysis."""
    conversations = [
        {
            "messages": [
                {"sender": "agent", "message": "Hey! Quick question?"},
                {"sender": "lead", "message": "Yes?"},
                {"sender": "agent", "message": "See you there, appointment set!"},
            ]
        }
    ]
    report = coaching_service.analyze_agent_performance("agent_1", conversations)
    assert report["agent_id"] == "agent_1"
    assert "metrics" in report
    assert report["metrics"]["total_conversations"] == 1
    assert any("appointment" in s for s in report["strengths"])


def test_get_objection_handler(coaching_service):
    """Test getting objection handlers."""
    context = {"name": "Alice"}
    handler = coaching_service.get_objection_handler("price_too_high", context)
    assert "Price Objection" in handler["title"]
    assert "Alice" in handler["personalized_response"]


def test_get_closing_technique(coaching_service):
    """Test getting closing techniques."""
    result = coaching_service.get_closing_technique(9.0, "high")
    assert result["recommended"]["name"] == "Direct Close"

    result_low = coaching_service.get_closing_technique(5.0, "low")
    # For score <= 6 and urgency == "low", it might return "Trial Close" or "Takeaway Close"
    # Actually checking the implementation:
    # 1. score > 8 & high -> Direct
    # 2. score > 6 -> Either/Or
    # 3. urgency == low -> Trial
    # 4. default -> Takeaway
    # For (5.0, "low"), only condition 3 and 4 apply. 3 comes first in list.
    assert result_low["recommended"]["name"] == "Trial Close"