"""
Tests for Jorge Cross-Bot Handoff Service.

Validates tag-driven bot-to-bot transitions and handoff logic.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (

    HandoffDecision,
    JorgeHandoffService,
)


class TestJorgeHandoffService:
    """Test suite for handoff service functionality."""

    @pytest.fixture
    def mock_analytics_service(self):
        """Create a mock analytics service."""
        analytics = MagicMock()
        analytics.track_event = AsyncMock()
        return analytics

    @pytest.fixture
    def handoff_service(self, mock_analytics_service):
        """Create a handoff service with mock analytics."""
        JorgeHandoffService._handoff_history.clear()
        JorgeHandoffService._active_handoffs.clear()
        return JorgeHandoffService(analytics_service=mock_analytics_service)

    @pytest.mark.asyncio
    async def test_lead_to_buyer_handoff_on_buyer_intent(self, handoff_service):
        """Test that buyer intent score >0.7 triggers lead->buyer handoff."""
        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["looking to buy", "budget around 600k"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_123",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"
        assert decision.reason == "buyer_intent_detected"
        assert decision.confidence == 0.85

    @pytest.mark.asyncio
    async def test_lead_to_seller_handoff_on_seller_intent(self, handoff_service):
        """Test that seller intent score >0.7 triggers lead->seller handoff."""
        intent_signals = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.75,
            "detected_intent_phrases": ["sell my house", "what's my home worth"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_456",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "seller"
        assert decision.reason == "seller_intent_detected"
        assert decision.confidence == 0.75

    @pytest.mark.asyncio
    async def test_no_handoff_below_confidence_threshold(self, handoff_service):
        """Test that score 0.5 does not trigger handoff (threshold is 0.7)."""
        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["might be interested"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="contact_789",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None

    @pytest.mark.asyncio
    async def test_handoff_generates_correct_tag_swap(self, handoff_service):
        """Test that execute_handoff removes source tag and adds target tag."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={"contact_id": "contact_123"},
        )

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Find tag actions
        remove_tags = [a for a in actions if a["type"] == "remove_tag"]
        add_tags = [a for a in actions if a["type"] == "add_tag"]

        # Should remove lead tag
        assert any(a["tag"] == "Needs Qualifying" for a in remove_tags)
        # Should add buyer tag
        assert any(a["tag"] == "Buyer-Lead" for a in add_tags)

    @pytest.mark.asyncio
    async def test_handoff_adds_tracking_tag(self, handoff_service):
        """Test that 'Handoff-Lead-to-Buyer' tracking tag is added."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={"contact_id": "contact_123"},
        )

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Find tracking tag
        tracking_tags = [a["tag"] for a in actions if a["type"] == "add_tag" and "Handoff" in a["tag"]]

        assert "Handoff-Lead-to-Buyer" in tracking_tags

    @pytest.mark.asyncio
    async def test_handoff_logs_analytics_event(self, handoff_service, mock_analytics_service):
        """Test that analytics_service.track_event is called for handoff."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={"contact_id": "contact_123", "detected_phrases": ["buyer intent detected"]},
        )

        await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Verify analytics event was logged
        mock_analytics_service.track_event.assert_called_once()
        call_args = mock_analytics_service.track_event.call_args

        assert call_args.kwargs["event_type"] == "jorge_handoff"
        assert call_args.kwargs["contact_id"] == "contact_123"
        assert call_args.kwargs["data"]["source_bot"] == "lead"
        assert call_args.kwargs["data"]["target_bot"] == "buyer"
        assert call_args.kwargs["data"]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_seller_to_buyer_handoff(self, handoff_service):
        """Test cross-direction handoff from seller to buyer (lower threshold 0.6)."""
        intent_signals = {
            "buyer_intent_score": 0.65,
            "seller_intent_score": 0.2,
            "detected_intent_phrases": ["also looking to buy", "need to find a new place"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id="contact_seller_123",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "seller"
        assert decision.target_bot == "buyer"
        assert decision.confidence == 0.65  # Above 0.6 threshold

    @pytest.mark.asyncio
    async def test_buyer_to_seller_handoff(self, handoff_service):
        """Test reverse handoff from buyer to seller (higher threshold 0.8)."""
        intent_signals = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.85,
            "detected_phrases": ["actually I need to sell first", "sell before buying"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="contact_buyer_456",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "buyer"
        assert decision.target_bot == "seller"
        assert decision.confidence == 0.85  # Above 0.8 threshold

    @pytest.mark.asyncio
    async def test_buyer_to_seller_no_handoff_below_threshold(self, handoff_service):
        """Test that buyer->seller handoff requires 0.8 threshold."""
        intent_signals = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.75,  # Below 0.8 threshold
            "detected_phrases": ["might sell"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="contact_buyer_789",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None  # Should not handoff below 0.8

    @pytest.mark.asyncio
    async def test_seller_to_buyer_no_handoff_below_threshold(self, handoff_service):
        """Test that seller->buyer handoff requires 0.6 threshold."""
        intent_signals = {
            "buyer_intent_score": 0.55,  # Below 0.6 threshold
            "seller_intent_score": 0.1,
            "detected_phrases": ["maybe looking"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id="contact_seller_789",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None  # Should not handoff below 0.6

    @pytest.mark.asyncio
    async def test_self_handoff_not_allowed(self, handoff_service):
        """Test that handoff to same bot is not allowed."""
        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["buyer intent"],
        }

        # Trying to handoff buyer -> buyer should not work
        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="contact_123",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None  # Self-handoff should be rejected

    @pytest.mark.asyncio
    async def test_extract_intent_signals_from_message(self, handoff_service):
        """Test intent signal extraction from user messages."""
        message = "I want to buy a house in Rancho Cucamonga with a budget around $700k. I'm pre-approved."

        signals = JorgeHandoffService.extract_intent_signals(message)

        assert signals["buyer_intent_score"] > 0
        assert "buyer intent detected" in signals["detected_intent_phrases"]

    @pytest.mark.asyncio
    async def test_extract_seller_intent_signals(self, handoff_service):
        """Test seller intent signal extraction from user messages."""
        message = "What's my home worth? I'm thinking about selling my house."

        signals = JorgeHandoffService.extract_intent_signals(message)

        assert signals["seller_intent_score"] > 0
        assert "seller intent detected" in signals["detected_intent_phrases"]

    @pytest.mark.asyncio
    async def test_execute_handoff_without_analytics(self):
        """Test that handoff works even without analytics service."""
        service = JorgeHandoffService(analytics_service=None)

        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={},
        )

        # Should not raise exception
        actions = await service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        assert len(actions) > 0
        # Should have remove_tag, add_tag (target), and add_tag (tracking)
        assert len([a for a in actions if a["type"] == "remove_tag"]) == 1
        assert len([a for a in actions if a["type"] == "add_tag"]) == 2

    @pytest.mark.asyncio
    async def test_handoff_tracks_seller_to_buyer(self, handoff_service, mock_analytics_service):
        """Test tracking tag for seller->buyer handoff."""
        decision = HandoffDecision(
            source_bot="seller",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.65,
            context={},
        )

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Find tracking tag
        tracking_tags = [a["tag"] for a in actions if a["type"] == "add_tag" and "Handoff" in a["tag"]]

        assert "Handoff-Seller-to-Buyer" in tracking_tags

    @pytest.mark.asyncio
    async def test_handoff_tracks_buyer_to_seller(self, handoff_service, mock_analytics_service):
        """Test tracking tag for buyer->seller handoff."""
        decision = HandoffDecision(
            source_bot="buyer",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.85,
            context={},
        )

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Find tracking tag
        tracking_tags = [a["tag"] for a in actions if a["type"] == "add_tag" and "Handoff" in a["tag"]]

        assert "Handoff-Buyer-to-Seller" in tracking_tags