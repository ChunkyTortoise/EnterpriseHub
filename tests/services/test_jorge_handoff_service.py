"""Tests for Phase 3: Cross-Bot Handoff — JorgeHandoffService."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    HandoffDecision,
    JorgeHandoffService,
)


@pytest.fixture
def mock_analytics():
    analytics = AsyncMock()
    analytics.track_event = AsyncMock()
    return analytics


@pytest.fixture
def handoff_service(mock_analytics):
    return JorgeHandoffService(analytics_service=mock_analytics)


class TestEvaluateHandoff:
    """Tests for JorgeHandoffService.evaluate_handoff()."""

    @pytest.mark.asyncio
    async def test_lead_to_buyer_handoff_on_buyer_intent(self, handoff_service):
        """Buyer intent score >0.7 triggers handoff from lead to buyer."""
        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["looking to buy", "budget around 600k"],
        }
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="test_123",
            conversation_history=[{"role": "user", "content": "I want to buy a house"}],
            intent_signals=intent_signals,
        )
        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"
        assert decision.confidence == 0.85
        assert "buyer_intent_detected" in decision.reason

    @pytest.mark.asyncio
    async def test_lead_to_seller_handoff_on_seller_intent(self, handoff_service):
        """Seller intent phrases trigger handoff from lead to seller."""
        intent_signals = {
            "buyer_intent_score": 0.0,
            "seller_intent_score": 0.9,
            "detected_intent_phrases": ["sell my house"],
        }
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="test_456",
            conversation_history=[{"role": "user", "content": "I want to sell my house"}],
            intent_signals=intent_signals,
        )
        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "seller"
        assert decision.confidence == 0.9

    @pytest.mark.asyncio
    async def test_no_handoff_below_confidence_threshold(self, handoff_service):
        """Score 0.5 does not trigger handoff (threshold is 0.7 for lead->buyer)."""
        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": [],
        }
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="test_789",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision is None

    @pytest.mark.asyncio
    async def test_seller_to_buyer_handoff(self, handoff_service):
        """Cross-direction: seller to buyer with threshold 0.6."""
        intent_signals = {
            "buyer_intent_score": 0.7,
            "seller_intent_score": 0.2,
            "detected_intent_phrases": ["also looking to buy"],
        }
        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id="test_s2b",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision is not None
        assert decision.source_bot == "seller"
        assert decision.target_bot == "buyer"

    @pytest.mark.asyncio
    async def test_buyer_to_seller_handoff(self, handoff_service):
        """Reverse: buyer to seller requires higher threshold (0.8)."""
        intent_signals = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.85,
            "detected_intent_phrases": ["need to sell first"],
        }
        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="test_b2s",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision is not None
        assert decision.source_bot == "buyer"
        assert decision.target_bot == "seller"
        assert decision.confidence == 0.85


class TestExecuteHandoff:
    """Tests for JorgeHandoffService.execute_handoff()."""

    @pytest.mark.asyncio
    async def test_handoff_generates_correct_tag_swap(self, handoff_service):
        """Removes source tag, adds target tag."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={"detected_phrases": ["looking to buy"]},
        )
        actions = await handoff_service.execute_handoff(decision, contact_id="test_swap")

        remove_actions = [a for a in actions if a["type"] == "remove_tag"]
        add_actions = [a for a in actions if a["type"] == "add_tag"]

        # Should remove lead's tag ("Needs Qualifying")
        assert any(a["tag"] == "Needs Qualifying" for a in remove_actions)
        # Should add buyer's tag ("Buyer-Lead")
        assert any(a["tag"] == "Buyer-Lead" for a in add_actions)

    @pytest.mark.asyncio
    async def test_handoff_adds_tracking_tag(self, handoff_service):
        """Handoff-Lead-to-Buyer tracking tag is present."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.85,
            context={},
        )
        actions = await handoff_service.execute_handoff(decision, contact_id="test_track")

        add_tags = [a["tag"] for a in actions if a["type"] == "add_tag"]
        assert "Handoff-Lead-to-Buyer" in add_tags

    @pytest.mark.asyncio
    async def test_handoff_logs_analytics_event(self, handoff_service, mock_analytics):
        """analytics_service.track_event called with handoff data."""
        decision = HandoffDecision(
            source_bot="seller",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.7,
            context={"detected_phrases": ["also looking to buy"]},
        )
        await handoff_service.execute_handoff(decision, contact_id="test_analytics", location_id="loc_test")

        mock_analytics.track_event.assert_called_once()
        call_kwargs = mock_analytics.track_event.call_args.kwargs
        assert call_kwargs["event_type"] == "jorge_handoff"
        assert call_kwargs["location_id"] == "loc_test"
        assert call_kwargs["contact_id"] == "test_analytics"
        assert call_kwargs["data"]["source_bot"] == "seller"
        assert call_kwargs["data"]["target_bot"] == "buyer"
