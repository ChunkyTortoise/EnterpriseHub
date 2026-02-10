"""
Test Suite for Lead Bot Handoff Functionality

Tests for lead-to-buyer and lead-to-seller handoff scenarios.
Complements the existing 16 handoff service tests.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (

@pytest.mark.integration
    HandoffDecision,
    JorgeHandoffService,
)


class MockAnalyticsService:
    """Mock analytics service for tracking handoff events."""

    def __init__(self):
        self.events = []
        self.counters = {
            "lead_to_buyer": 0,
            "lead_to_seller": 0,
        }
        self.handoff_durations = []

    async def track_event(self, event_type: str, location_id: str, contact_id: str, data: dict):
        self.events.append(
            {
                "event_type": event_type,
                "location_id": location_id,
                "contact_id": contact_id,
                "data": data,
                "timestamp": datetime.now(timezone.utc),
            }
        )

        # Track counters for specific handoff types
        if event_type == "jorge_handoff":
            source = data.get("source_bot")
            target = data.get("target_bot")
            if source == "lead" and target == "buyer":
                self.counters["lead_to_buyer"] += 1
            elif source == "lead" and target == "seller":
                self.counters["lead_to_seller"] += 1

            # Track handoff duration if provided
            if "handoff_start_time" in data:
                duration = data.get("handoff_end_time", 0) - data.get("handoff_start_time", 0)
                self.handoff_durations.append(duration)


@pytest.fixture
def mock_analytics_service():
    """Provide a mock analytics service."""
    return MockAnalyticsService()


@pytest.fixture
def handoff_service(mock_analytics_service):
    """Provide a handoff service with mocked analytics."""
    return JorgeHandoffService(analytics_service=mock_analytics_service)


@pytest.fixture
def sample_conversation_history():
    """Sample conversation history for handoff testing."""
    return [
        {"role": "assistant", "content": "Hello! How can I help you today?", "timestamp": "2026-02-06T10:00:00Z"},
        {
            "role": "user",
            "content": "I'm looking to buy a home in Rancho Cucamonga.",
            "timestamp": "2026-02-06T10:05:00Z",
        },
        {"role": "assistant", "content": "Great! What's your budget?", "timestamp": "2026-02-06T10:06:00Z"},
        {
            "role": "user",
            "content": "I have a budget of $700,000 and I'm pre-approved.",
            "timestamp": "2026-02-06T10:10:00Z",
        },
    ]


@pytest.mark.asyncio
async def test_lead_to_buyer_handoff_high_confidence(handoff_service, sample_conversation_history):
    """Test lead-to-buyer handoff with high buying intent signals."""
    contact_id = "contact_123"
    intent_signals = {
        "buyer_intent_score": 0.85,
        "seller_intent_score": 0.1,
        "detected_intent_phrases": ["buyer intent detected", "budget mentioned"],
    }

    decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=intent_signals,
    )

    # Verify handoff is recommended (confidence > 0.7 threshold)
    assert decision is not None
    assert decision.source_bot == "lead"
    assert decision.target_bot == "buyer"
    assert decision.confidence == 0.85
    assert decision.confidence > 0.7
    assert decision.reason == "buyer_intent_detected"

    # Verify buyer tags are added during execution
    actions = await handoff_service.execute_handoff(
        decision=decision,
        contact_id=contact_id,
        location_id="loc_456",
    )

    # Check action sequence: remove lead tag, add buyer tag, add tracking tag
    action_types = [a["type"] for a in actions]
    assert "remove_tag" in action_types
    assert "add_tag" in action_types
    assert len(actions) == 3

    # Verify specific tags
    add_tag_actions = [a for a in actions if a["type"] == "add_tag"]
    add_tag_values = [a["tag"] for a in add_tag_actions]
    assert "Buyer-Lead" in add_tag_values
    assert "Handoff-Lead-to-Buyer" in add_tag_values

    # Verify analytics were recorded
    assert handoff_service.analytics_service.counters["lead_to_buyer"] == 1


@pytest.mark.asyncio
async def test_lead_to_seller_handoff_listing_signals(handoff_service, sample_conversation_history):
    """Test lead-to-seller handoff with seller intent signals."""
    contact_id = "contact_789"
    intent_signals = {
        "buyer_intent_score": 0.15,
        "seller_intent_score": 0.9,
        "detected_intent_phrases": ["seller intent detected", "home valuation request"],
    }

    decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=intent_signals,
    )

    # Verify handoff is recommended
    assert decision is not None
    assert decision.source_bot == "lead"
    assert decision.target_bot == "seller"
    assert decision.confidence == 0.9
    assert decision.reason == "seller_intent_detected"

    # Verify seller tags are added during execution
    actions = await handoff_service.execute_handoff(
        decision=decision,
        contact_id=contact_id,
        location_id="loc_456",
    )

    # Check action sequence
    action_types = [a["type"] for a in actions]
    assert "remove_tag" in action_types
    assert "add_tag" in action_types

    # Verify specific tags (seller uses same tag as lead for activation)
    add_tag_actions = [a for a in actions if a["type"] == "add_tag"]
    add_tag_values = [a["tag"] for a in add_tag_actions]
    assert "Needs Qualifying" in add_tag_values  # Seller uses "Needs Qualifying" tag
    assert "Handoff-Lead-to-Seller" in add_tag_values

    # Verify analytics were recorded
    assert handoff_service.analytics_service.counters["lead_to_seller"] == 1


@pytest.mark.asyncio
async def test_lead_handoff_confidence_thresholds(handoff_service, sample_conversation_history):
    """Test confidence threshold behavior for handoff decisions."""
    contact_id = "contact_threshold_test"

    # Test case 1: Low confidence (< 0.7) - should NOT trigger handoff
    low_confidence_signals = {
        "buyer_intent_score": 0.5,
        "seller_intent_score": 0.3,
        "detected_intent_phrases": [],
    }

    decision_low = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=low_confidence_signals,
    )

    assert decision_low is None  # No handoff for low confidence

    # Test case 2: Exactly at threshold (0.7) - should trigger handoff
    threshold_signals = {
        "buyer_intent_score": 0.7,
        "seller_intent_score": 0.3,
        "detected_intent_phrases": ["buyer intent detected"],
    }

    decision_threshold = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=threshold_signals,
    )

    assert decision_threshold is not None  # Handoff triggered at threshold
    assert decision_threshold.confidence == 0.7
    assert decision_threshold.target_bot == "buyer"

    # Test case 3: High confidence (> 0.7) - should trigger handoff
    high_confidence_signals = {
        "buyer_intent_score": 0.95,
        "seller_intent_score": 0.2,
        "detected_intent_phrases": ["buyer intent detected", "pre-approval mentioned"],
    }

    decision_high = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=high_confidence_signals,
    )

    assert decision_high is not None
    assert decision_high.confidence == 0.95


@pytest.mark.asyncio
async def test_lead_handoff_tag_swapping(handoff_service, sample_conversation_history):
    """Test that lead tags are removed and new bot-specific tags are added."""
    contact_id = "contact_tag_swap"

    # High buyer intent to trigger handoff
    intent_signals = {
        "buyer_intent_score": 0.8,
        "seller_intent_score": 0.1,
        "detected_intent_phrases": ["buyer intent detected"],
    }

    decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=intent_signals,
    )

    assert decision is not None

    # Execute handoff and verify tag swapping
    actions = await handoff_service.execute_handoff(
        decision=decision,
        contact_id=contact_id,
        location_id="loc_789",
    )

    # Verify tag removal (lead's activation tag)
    remove_tag_actions = [a for a in actions if a["type"] == "remove_tag"]
    assert len(remove_tag_actions) == 1
    assert remove_tag_actions[0]["tag"] == "Needs Qualifying"  # Lead tag

    # Verify tag addition (buyer's activation tag)
    add_tag_actions = [a for a in actions if a["type"] == "add_tag"]
    assert len(add_tag_actions) == 2  # Buyer tag + tracking tag

    buyer_tag_found = False
    tracking_tag_found = False

    for action in add_tag_actions:
        if action["tag"] == "Buyer-Lead":
            buyer_tag_found = True
        elif action["tag"] == "Handoff-Lead-to-Buyer":
            tracking_tag_found = True

    assert buyer_tag_found, "Buyer-Lead tag should be added"
    assert tracking_tag_found, "Handoff-Lead-to-Buyer tracking tag should be added"


@pytest.mark.asyncio
async def test_lead_handoff_tracking_and_analytics(handoff_service, sample_conversation_history):
    """Test that analytics are properly recorded for handoff events."""
    contact_id = "contact_analytics"

    # Test lead-to-buyer handoff analytics
    buyer_signals = {
        "buyer_intent_score": 0.85,
        "seller_intent_score": 0.1,
        "detected_intent_phrases": ["buyer intent detected"],
    }

    buyer_decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=sample_conversation_history,
        intent_signals=buyer_signals,
    )

    assert buyer_decision is not None

    await handoff_service.execute_handoff(
        decision=buyer_decision,
        contact_id=contact_id,
        location_id="loc_analytics",
    )

    # Test lead-to-seller handoff analytics
    seller_signals = {
        "buyer_intent_score": 0.1,
        "seller_intent_score": 0.88,
        "detected_intent_phrases": ["seller intent detected"],
    }

    seller_decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=f"{contact_id}_2",
        conversation_history=sample_conversation_history,
        intent_signals=seller_signals,
    )

    assert seller_decision is not None

    await handoff_service.execute_handoff(
        decision=seller_decision,
        contact_id=f"{contact_id}_2",
        location_id="loc_analytics",
    )

    # Verify counters
    assert handoff_service.analytics_service.counters["lead_to_buyer"] == 1
    assert handoff_service.analytics_service.counters["lead_to_seller"] == 1

    # Verify event recording
    events = handoff_service.analytics_service.events
    assert len(events) == 2

    # Check event data structure
    buyer_event = events[0]
    assert buyer_event["event_type"] == "jorge_handoff"
    assert buyer_event["data"]["source_bot"] == "lead"
    assert buyer_event["data"]["target_bot"] == "buyer"
    assert "confidence" in buyer_event["data"]
    assert "detected_phrases" in buyer_event["data"]

    seller_event = events[1]
    assert seller_event["event_type"] == "jorge_handoff"
    assert seller_event["data"]["target_bot"] == "seller"


@pytest.mark.asyncio
async def test_lead_handoff_with_conversation_context(handoff_service):
    """Test handoff decision uses full conversation history and context."""
    contact_id = "contact_context"

    # Rich conversation history with buyer intent signals
    rich_conversation = [
        {"role": "assistant", "content": "Welcome! How can I assist you?", "timestamp": "2026-02-06T09:00:00Z"},
        {
            "role": "user",
            "content": "I'm interested in buying a property in the area.",
            "timestamp": "2026-02-06T09:05:00Z",
        },
        {
            "role": "assistant",
            "content": "That's great! What type of property are you looking for?",
            "timestamp": "2026-02-06T09:06:00Z",
        },
        {
            "role": "user",
            "content": "I want a single-family home with a pool. My budget is $800,000.",
            "timestamp": "2026-02-06T09:10:00Z",
        },
        {
            "role": "assistant",
            "content": "Perfect! Are you pre-approved or working with a lender?",
            "timestamp": "2026-02-06T09:11:00Z",
        },
        {
            "role": "user",
            "content": "Yes, I've been pre-approved for $850,000 and I'm ready to move fast.",
            "timestamp": "2026-02-06T09:15:00Z",
        },
        {
            "role": "assistant",
            "content": "Excellent! Let me connect you with a buyer specialist.",
            "timestamp": "2026-02-06T09:16:00Z",
        },
    ]

    # Intent signals extracted from conversation context
    intent_signals = {
        "buyer_intent_score": 0.9,
        "seller_intent_score": 0.15,
        "detected_intent_phrases": [
            "buyer intent detected",
            "budget mentioned",
            "pre-approval mentioned",
        ],
    }

    decision = await handoff_service.evaluate_handoff(
        current_bot="lead",
        contact_id=contact_id,
        conversation_history=rich_conversation,
        intent_signals=intent_signals,
    )

    assert decision is not None
    assert decision.source_bot == "lead"
    assert decision.target_bot == "buyer"
    assert decision.confidence == 0.9

    # Verify context includes conversation details
    assert "contact_id" in decision.context
    assert decision.context["contact_id"] == contact_id
    assert "detected_phrases" in decision.context
    assert "conversation_turns" in decision.context
    assert decision.context["conversation_turns"] == len(rich_conversation)

    # Execute handoff and verify tracking
    actions = await handoff_service.execute_handoff(
        decision=decision,
        contact_id=contact_id,
        location_id="loc_context",
    )

    # Verify handoff was tracked in analytics with context
    events = handoff_service.analytics_service.events
    assert len(events) == 1
    assert events[0]["event_type"] == "jorge_handoff"
    assert events[0]["data"]["confidence"] == 0.9
    assert len(events[0]["data"]["detected_phrases"]) == 3


class TestLeadBotHandoffEdgeCases:
    """Edge case tests for lead bot handoff functionality."""

    @pytest.mark.asyncio
    async def test_no_handoff_same_intent_score(self, handoff_service, sample_conversation_history):
        """Test that handoff doesn't occur when buyer and seller scores are equal."""
        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.5,
            "detected_intent_phrases": [],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_equal",
            conversation_history=sample_conversation_history,
            intent_signals=intent_signals,
        )

        # Should return None when scores are equal (no clear direction)
        assert decision is None

    @pytest.mark.asyncio
    async def test_no_handoff_below_threshold_both(self, handoff_service, sample_conversation_history):
        """Test no handoff when both scores are below threshold."""
        intent_signals = {
            "buyer_intent_score": 0.3,
            "seller_intent_score": 0.25,
            "detected_intent_phrases": [],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_both_low",
            conversation_history=sample_conversation_history,
            intent_signals=intent_signals,
        )

        assert decision is None

    @pytest.mark.asyncio
    async def test_handoff_without_analytics_service(self, sample_conversation_history):
        """Test handoff execution works without analytics service."""
        service_no_analytics = JorgeHandoffService(analytics_service=None)

        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["buyer intent detected"],
        }

        decision = await service_no_analytics.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_no_analytics",
            conversation_history=sample_conversation_history,
            intent_signals=intent_signals,
        )

        assert decision is not None

        # Should not raise exception even without analytics
        actions = await service_no_analytics.execute_handoff(
            decision=decision,
            contact_id="contact_no_analytics",
            location_id="loc_no_analytics",
        )

        # Actions should still be generated correctly
        assert len(actions) == 3  # remove + 2 adds
        action_types = [a["type"] for a in actions]
        assert "remove_tag" in action_types
        assert action_types.count("add_tag") == 2


class TestIntentSignalExtraction:
    """Tests for the intent signal extraction utility method."""

    def test_extract_buyer_intent_patterns(self):
        """Test buyer intent pattern detection."""
        messages = [
            "I want to buy a house",
            "I'm looking to buy a home in the area",
            "What's my budget? $500,000",
            "I'm pre-approved for a mortgage",
            "I need to find a new place",
        ]

        for message in messages:
            signals = JorgeHandoffService.extract_intent_signals(message)
            assert signals["buyer_intent_score"] > 0, f"Should detect buyer intent in: {message}"
            assert "buyer intent detected" in signals["detected_intent_phrases"]

    def test_extract_seller_intent_patterns(self):
        """Test seller intent pattern detection."""
        messages = [
            "I want to sell my home",
            "What's my home worth?",
            "I need a CMA for my property",
            "I'm looking to list my house",
            "I need to sell before I can buy",
        ]

        for message in messages:
            signals = JorgeHandoffService.extract_intent_signals(message)
            assert signals["seller_intent_score"] > 0, f"Should detect seller intent in: {message}"
            assert "seller intent detected" in signals["detected_intent_phrases"]

    def test_extract_no_intent(self):
        """Test no intent detection in neutral messages."""
        messages = [
            "Hello",
            "Thanks for the information",
            "I'll think about it",
        ]

        for message in messages:
            signals = JorgeHandoffService.extract_intent_signals(message)
            assert signals["buyer_intent_score"] == 0.0
            assert signals["seller_intent_score"] == 0.0
            assert len(signals["detected_intent_phrases"]) == 0

    def test_extract_multiple_patterns_boost_score(self):
        """Test that multiple pattern matches boost the score."""
        # Single pattern
        single_match = "I want to buy a house"
        signals_single = JorgeHandoffService.extract_intent_signals(single_match)

        # Multiple patterns
        multi_match = "I want to buy a house and I'm pre-approved with a budget of $500,000"
        signals_multi = JorgeHandoffService.extract_intent_signals(multi_match)

        # Score should be higher for multiple matches (capped at 1.0)
        assert signals_multi["buyer_intent_score"] >= signals_single["buyer_intent_score"]