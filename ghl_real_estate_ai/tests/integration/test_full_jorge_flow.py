"""
Integration tests for full Jorge bot flow with cross-bot handoffs.

Tests end-to-end scenarios where leads transition between bots.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.api.schemas.ghl import (
    ActionType,
    GHLAction,
    GHLContact,
    GHLMessage,
    GHLWebhookEvent,
    MessageDirection,
    MessageType,
)
from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (

    HandoffDecision,
    JorgeHandoffService,
)


class TestFullJorgeFlow:
    """Integration tests for complete bot flows with handoffs."""

    @pytest.fixture
    def mock_analytics_service(self):
        """Create a mock analytics service."""
        analytics = MagicMock()
        analytics.track_event = AsyncMock()
        return analytics

    @pytest.fixture
    def handoff_service(self, mock_analytics_service):
        """Create a handoff service with mock analytics."""
        return JorgeHandoffService(analytics_service=mock_analytics_service)

    @pytest.fixture
    def mock_webhook_event(self):
        """Create a mock GHL webhook event."""
        return GHLWebhookEvent(
            type="InboundMessage",
            contact_id="test_contact_123",
            location_id="test_location_456",
            message=GHLMessage(
                type=MessageType.SMS,
                body="Test message",
                direction=MessageDirection.INBOUND,
                timestamp=datetime.utcnow(),
            ),
            contact=GHLContact(
                id="test_contact_123",
                first_name="Test",
                last_name="User",
                tags=["Needs Qualifying"],
            ),
        )

    @pytest.mark.asyncio
    async def test_lead_qualifies_as_buyer_full_flow(self, handoff_service, mock_analytics_service):
        """
        Test complete flow: Lead bot detects buyer intent -> handoff -> buyer bot.

        Scenario:
        1. Lead with "Needs Qualifying" tag sends buyer-intent message
        2. Lead bot processes and detects strong buyer intent
        3. Handoff service evaluates and triggers lead->buyer handoff
        4. Tags are swapped (remove Needs Qualifying, add Buyer-Lead)
        5. Tracking tag Handoff-Lead-to-Buyer is added
        6. Analytics event is logged
        7. Next message would route to buyer bot
        """
        contact_id = "lead_buyer_123"

        # Simulate lead bot detecting buyer intent
        lead_intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["I want to buy a house", "budget around 700k", "pre-approved"],
        }

        # Evaluate handoff
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I want to buy a house in Rancho Cucamonga"},
                {"role": "assistant", "content": "Great! What's your budget?"},
                {"role": "user", "content": "Around $700k, I'm pre-approved"},
            ],
            intent_signals=lead_intent_signals,
        )

        # Verify handoff decision
        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"
        assert decision.confidence >= 0.7

        # Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        # Convert to GHLActions for webhook compatibility
        ghl_actions = []
        for action in actions:
            if action["type"] == "add_tag":
                ghl_actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action["tag"]))
            elif action["type"] == "remove_tag":
                ghl_actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=action["tag"]))

        # Verify tag swap
        remove_tags = [a.tag for a in ghl_actions if a.type == ActionType.REMOVE_TAG]
        add_tags = [a.tag for a in ghl_actions if a.type == ActionType.ADD_TAG]

        assert "Needs Qualifying" in remove_tags  # Lead tag removed
        assert "Buyer-Lead" in add_tags  # Buyer tag added
        assert "Handoff-Lead-to-Buyer" in add_tags  # Tracking tag added

        # Verify analytics
        mock_analytics_service.track_event.assert_called_once()
        call_kwargs = mock_analytics_service.track_event.call_args.kwargs
        assert call_kwargs["event_type"] == "jorge_handoff"
        assert call_kwargs["data"]["source_bot"] == "lead"
        assert call_kwargs["data"]["target_bot"] == "buyer"

    @pytest.mark.asyncio
    async def test_seller_also_buying_full_flow(self, handoff_service, mock_analytics_service):
        """
        Test complete flow: Seller bot detects buyer intent -> handoff -> buyer bot.

        Scenario:
        1. Seller with "Needs Qualifying" tag mentions they also want to buy
        2. Seller bot processes and detects buyer intent (common scenario)
        3. Handoff service evaluates with lower threshold (0.6) for seller->buyer
        4. Tags remain (seller uses same tag) but tracking tag is added
        5. Next message would route to buyer bot
        """
        contact_id = "seller_buyer_456"

        # Simulate seller bot detecting buyer intent (seller also buying)
        seller_intent_signals = {
            "buyer_intent_score": 0.65,  # Above 0.6 threshold for seller->buyer
            "seller_intent_score": 0.3,
            "detected_intent_phrases": ["also looking to buy", "need to find a new place"],
        }

        # Evaluate handoff from seller to buyer
        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I need to sell my current home"},
                {"role": "assistant", "content": "What's your timeline for selling?"},
                {"role": "user", "content": "I need to sell in 3 months, but I'm also looking to buy a new place"},
            ],
            intent_signals=seller_intent_signals,
        )

        # Verify handoff decision (seller->buyer has 0.6 threshold)
        assert decision is not None
        assert decision.source_bot == "seller"
        assert decision.target_bot == "buyer"
        assert decision.confidence >= 0.6  # Above seller->buyer threshold (0.6)

        # Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        # Convert to GHLActions
        ghl_actions = []
        for action in actions:
            if action["type"] == "add_tag":
                ghl_actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action["tag"]))
            elif action["type"] == "remove_tag":
                ghl_actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=action["tag"]))

        # Verify actions
        remove_tags = [a.tag for a in ghl_actions if a.type == ActionType.REMOVE_TAG]
        add_tags = [a.tag for a in ghl_actions if a.type == ActionType.ADD_TAG]

        # Seller and lead use same tag "Needs Qualifying"
        assert "Needs Qualifying" in remove_tags
        assert "Buyer-Lead" in add_tags
        assert "Handoff-Seller-to-Buyer" in add_tags

        # Verify analytics
        mock_analytics_service.track_event.assert_called_once()
        call_kwargs = mock_analytics_service.track_event.call_args.kwargs
        assert call_kwargs["event_type"] == "jorge_handoff"
        assert call_kwargs["data"]["source_bot"] == "seller"
        assert call_kwargs["data"]["target_bot"] == "buyer"

    @pytest.mark.asyncio
    async def test_buyer_needs_to_sell_first_flow(self, handoff_service, mock_analytics_service):
        """
        Test complete flow: Buyer bot detects seller intent -> handoff -> seller bot.

        Scenario:
        1. Buyer with "Buyer-Lead" tag mentions they need to sell first
        2. Buyer bot processes and detects strong seller intent
        3. Handoff service evaluates with higher threshold (0.8) for buyer->seller
        4. Tags swapped and tracking tag added
        """
        contact_id = "buyer_seller_789"

        # Simulate buyer bot detecting seller intent
        buyer_intent_signals = {
            "buyer_intent_score": 0.15,
            "seller_intent_score": 0.85,
            "detected_intent_phrases": ["need to sell my house first", "want to list my home"],
        }

        # Evaluate handoff from buyer to seller
        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I'm looking for a 3BR in Victoria Gardens"},
                {"role": "assistant", "content": "Great area! What's your budget?"},
                {
                    "role": "user",
                    "content": "Before that, I need to sell my current house first. Can you help with that?",
                },
            ],
            intent_signals=buyer_intent_signals,
        )

        # Verify handoff decision (buyer->seller has 0.8 threshold)
        assert decision is not None
        assert decision.source_bot == "buyer"
        assert decision.target_bot == "seller"
        assert decision.confidence >= 0.8

        # Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        # Convert to GHLActions
        ghl_actions = []
        for action in actions:
            if action["type"] == "add_tag":
                ghl_actions.append(GHLAction(type=ActionType.ADD_TAG, tag=action["tag"]))
            elif action["type"] == "remove_tag":
                ghl_actions.append(GHLAction(type=ActionType.REMOVE_TAG, tag=action["tag"]))

        # Verify tag swap
        remove_tags = [a.tag for a in ghl_actions if a.type == ActionType.REMOVE_TAG]
        add_tags = [a.tag for a in ghl_actions if a.type == ActionType.ADD_TAG]

        assert "Buyer-Lead" in remove_tags
        assert "Needs Qualifying" in add_tags
        assert "Handoff-Buyer-to-Seller" in add_tags

        # Verify analytics
        mock_analytics_service.track_event.assert_called_once()
        call_kwargs = mock_analytics_service.track_event.call_args.kwargs
        assert call_kwargs["event_type"] == "jorge_handoff"
        assert call_kwargs["data"]["source_bot"] == "buyer"
        assert call_kwargs["data"]["target_bot"] == "seller"