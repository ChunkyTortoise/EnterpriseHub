"""
End-to-end cross-bot handoff tests for Jorge bots.

Tests complete handoff flows including:
- Lead -> Seller handoff with context preservation
- Lead -> Buyer handoff with context preservation
- Seller -> Buyer cross-qualification handoff
- Circular prevention (same route blocked within 30min)
- Rate limiting (4th handoff in 1 hour blocked)
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    HandoffDecision,
    JorgeHandoffService,
)


@pytest.fixture
def mock_analytics_service():
    """Create a mock analytics service."""
    analytics = MagicMock()
    analytics.track_event = AsyncMock()
    return analytics


@pytest.fixture
def handoff_service(mock_analytics_service):
    """Create a fresh handoff service with cleared class-level state."""
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService.reset_analytics()
    return JorgeHandoffService(analytics_service=mock_analytics_service)


# ---------------------------------------------------------------------------
# Lead -> Seller Handoff
# ---------------------------------------------------------------------------


class TestLeadToSellerHandoff:
    """Lead bot detects seller intent -> handoff to seller bot with context."""

    @pytest.mark.asyncio
    async def test_lead_to_seller_full_flow(self, handoff_service, mock_analytics_service):
        """Strong seller intent triggers lead->seller handoff with tag swap."""
        contact_id = "e2e_lead_seller_001"

        intent_signals = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.85,
            "detected_intent_phrases": ["sell my house", "what's my home worth"],
        }

        # Step 1: Evaluate handoff
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I want to sell my house in Rancho Cucamonga"},
                {"role": "assistant", "content": "I can help with that! Tell me more."},
                {"role": "user", "content": "What's my home worth? I'm thinking of listing."},
            ],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "seller"
        assert decision.confidence >= 0.7
        assert decision.reason == "seller_intent_detected"

        # Step 2: Execute handoff
        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        # Step 3: Verify tag actions
        remove_tags = [a["tag"] for a in actions if a.get("type") == "remove_tag"]
        add_tags = [a["tag"] for a in actions if a.get("type") == "add_tag"]

        assert "Needs Qualifying" in remove_tags
        assert "Seller-Lead" in add_tags
        assert "Handoff-Lead-to-Seller" in add_tags

        # Step 4: Verify analytics
        mock_analytics_service.track_event.assert_called_once()
        call_kwargs = mock_analytics_service.track_event.call_args.kwargs
        assert call_kwargs["event_type"] == "jorge_handoff"
        assert call_kwargs["data"]["source_bot"] == "lead"
        assert call_kwargs["data"]["target_bot"] == "seller"

    @pytest.mark.asyncio
    async def test_lead_to_seller_context_preserved(self, handoff_service):
        """Handoff decision includes enriched context for receiving bot."""
        intent_signals = {
            "buyer_intent_score": 0.05,
            "seller_intent_score": 0.9,
            "detected_intent_phrases": ["sell my house"],
            "qualification_score": 65.0,
            "temperature": "warm",
            "property_address": "123 Main St, Rancho Cucamonga",
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="e2e_context_001",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.enriched_context is not None
        assert decision.enriched_context.source_qualification_score == 65.0
        assert decision.enriched_context.source_temperature == "warm"
        assert decision.enriched_context.property_address == "123 Main St, Rancho Cucamonga"


# ---------------------------------------------------------------------------
# Lead -> Buyer Handoff
# ---------------------------------------------------------------------------


class TestLeadToBuyerHandoff:
    """Lead bot detects buyer intent -> handoff to buyer bot with context."""

    @pytest.mark.asyncio
    async def test_lead_to_buyer_full_flow(self, handoff_service, mock_analytics_service):
        """Strong buyer intent triggers lead->buyer handoff with tag swap."""
        contact_id = "e2e_lead_buyer_001"

        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.05,
            "detected_intent_phrases": ["looking to buy", "budget around 700k", "pre-approved"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I'm looking to buy a 3BR in Rancho Cucamonga"},
                {"role": "assistant", "content": "What's your budget?"},
                {"role": "user", "content": "Around $700k, I'm pre-approved."},
            ],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "lead"
        assert decision.target_bot == "buyer"
        assert decision.confidence >= 0.7

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        remove_tags = [a["tag"] for a in actions if a.get("type") == "remove_tag"]
        add_tags = [a["tag"] for a in actions if a.get("type") == "add_tag"]

        assert "Needs Qualifying" in remove_tags
        assert "Buyer-Lead" in add_tags
        assert "Handoff-Lead-to-Buyer" in add_tags

        mock_analytics_service.track_event.assert_called_once()

    @pytest.mark.asyncio
    async def test_lead_to_buyer_below_threshold_no_handoff(self, handoff_service):
        """Weak buyer intent (below 0.7) should NOT trigger handoff."""
        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["might be interested"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="e2e_no_handoff_001",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None


# ---------------------------------------------------------------------------
# Seller -> Buyer Cross-Qualification
# ---------------------------------------------------------------------------


class TestSellerToBuyerHandoff:
    """Seller bot detects buyer intent -> cross-qualification handoff."""

    @pytest.mark.asyncio
    async def test_seller_to_buyer_lower_threshold(self, handoff_service):
        """Seller->buyer uses 0.6 threshold (lower than lead->buyer)."""
        intent_signals = {
            "buyer_intent_score": 0.65,
            "seller_intent_score": 0.2,
            "detected_intent_phrases": ["also looking to buy", "need a new place"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id="e2e_seller_buyer_001",
            conversation_history=[
                {"role": "user", "content": "I'm selling my home but also need to buy."},
            ],
            intent_signals=intent_signals,
        )

        assert decision is not None
        assert decision.source_bot == "seller"
        assert decision.target_bot == "buyer"
        assert decision.confidence >= 0.6

        actions = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="e2e_seller_buyer_001",
        )

        add_tags = [a["tag"] for a in actions if a.get("type") == "add_tag"]
        assert "Handoff-Seller-to-Buyer" in add_tags

    @pytest.mark.asyncio
    async def test_buyer_to_seller_higher_threshold(self, handoff_service):
        """Buyer->seller requires 0.8 threshold (higher to prevent premature handoffs)."""
        # Below threshold: should NOT trigger
        intent_signals_below = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.75,
            "detected_intent_phrases": ["might sell"],
        }

        decision_below = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="e2e_buyer_seller_below",
            conversation_history=[],
            intent_signals=intent_signals_below,
        )
        assert decision_below is None

        # Above threshold: should trigger
        intent_signals_above = {
            "buyer_intent_score": 0.1,
            "seller_intent_score": 0.85,
            "detected_intent_phrases": ["sell my house first", "need to list"],
        }

        decision_above = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="e2e_buyer_seller_above",
            conversation_history=[],
            intent_signals=intent_signals_above,
        )

        assert decision_above is not None
        assert decision_above.source_bot == "buyer"
        assert decision_above.target_bot == "seller"
        assert decision_above.confidence >= 0.8


# ---------------------------------------------------------------------------
# Circular Prevention
# ---------------------------------------------------------------------------


class TestCircularPrevention:
    """Same route blocked within 30min window."""

    @pytest.mark.asyncio
    async def test_same_route_blocked_within_window(self, handoff_service):
        """Second identical handoff within 30min should be blocked."""
        contact_id = "e2e_circular_001"

        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.05,
            "detected_intent_phrases": ["want to buy"],
        }

        # First handoff succeeds
        decision1 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision1 is not None

        await handoff_service.execute_handoff(
            decision=decision1,
            contact_id=contact_id,
        )

        # Second identical handoff should be blocked at evaluate_handoff level
        # because circular prevention is checked there too
        decision2 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )

        # Should be blocked by circular prevention
        assert decision2 is None

    @pytest.mark.asyncio
    async def test_different_contact_not_blocked(self, handoff_service):
        """Same route for different contacts should NOT be blocked."""
        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.05,
            "detected_intent_phrases": ["want to buy"],
        }

        # Contact A
        decision_a = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="e2e_contact_a",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision_a is not None
        await handoff_service.execute_handoff(decision=decision_a, contact_id="e2e_contact_a")

        # Contact B (different contact, same route)
        decision_b = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="e2e_contact_b",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision_b is not None

    @pytest.mark.asyncio
    async def test_execute_handoff_also_blocks_circular(self, handoff_service):
        """Execute_handoff has its own circular check that blocks duplicate executions."""
        contact_id = "e2e_circular_exec_001"

        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.9,
            context={"contact_id": contact_id},
        )

        # First execution succeeds
        actions1 = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )
        add_tags1 = [a["tag"] for a in actions1 if a.get("type") == "add_tag"]
        assert "Handoff-Lead-to-Buyer" in add_tags1

        # Second execution should be blocked
        actions2 = await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        # Should contain a blocked reason
        blocked = [a for a in actions2 if a.get("handoff_executed") is False]
        assert len(blocked) > 0


# ---------------------------------------------------------------------------
# Rate Limiting
# ---------------------------------------------------------------------------


class TestRateLimiting:
    """4th handoff in 1 hour should be blocked."""

    @pytest.mark.asyncio
    async def test_hourly_rate_limit_blocks_4th_handoff(self, handoff_service):
        """3 handoffs allowed per hour, 4th is blocked."""
        contact_id = "e2e_ratelimit_001"

        # Execute 3 handoffs (all should succeed)
        for i in range(3):
            decision = HandoffDecision(
                source_bot="lead",
                target_bot="buyer",
                reason="buyer_intent_detected",
                confidence=0.9,
                context={},
            )
            # Clear the circular check by using different source->target combos
            # Actually, we need to record history manually since execute blocks circulars
            JorgeHandoffService._record_handoff(contact_id, "lead", "buyer")

        # Now the 4th execution should be rate-limited
        decision4 = HandoffDecision(
            source_bot="lead",
            target_bot="seller",  # Different target to avoid circular block
            reason="seller_intent_detected",
            confidence=0.85,
            context={},
        )

        actions = await handoff_service.execute_handoff(
            decision=decision4,
            contact_id=contact_id,
        )

        # Should be rate-limited
        blocked = [a for a in actions if a.get("handoff_executed") is False]
        assert len(blocked) > 0
        assert "Rate limit" in blocked[0].get("reason", "")

    @pytest.mark.asyncio
    async def test_rate_limit_different_contacts_independent(self, handoff_service):
        """Rate limits are per-contact, not global."""
        # Exhaust rate limit for contact A
        for i in range(3):
            JorgeHandoffService._record_handoff("e2e_rate_contact_a", "lead", "buyer")

        # Contact B should still work
        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.05,
            "detected_intent_phrases": ["want to buy"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="e2e_rate_contact_b",
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision is not None


# ---------------------------------------------------------------------------
# Self-Handoff Prevention
# ---------------------------------------------------------------------------


class TestSelfHandoffPrevention:
    """Bot cannot hand off to itself."""

    @pytest.mark.asyncio
    async def test_buyer_to_buyer_blocked(self, handoff_service):
        """Buyer bot cannot hand off to buyer bot."""
        intent_signals = {
            "buyer_intent_score": 0.95,
            "seller_intent_score": 0.0,
            "detected_intent_phrases": ["buyer intent"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="buyer",
            contact_id="e2e_self_handoff_001",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None

    @pytest.mark.asyncio
    async def test_seller_to_seller_blocked(self, handoff_service):
        """Seller bot cannot hand off to seller bot."""
        intent_signals = {
            "buyer_intent_score": 0.0,
            "seller_intent_score": 0.95,
            "detected_intent_phrases": ["seller intent"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="seller",
            contact_id="e2e_self_handoff_002",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None


# ---------------------------------------------------------------------------
# Intent Signal Extraction
# ---------------------------------------------------------------------------


class TestIntentSignalExtraction:
    """Verify extract_intent_signals produces correct scores."""

    def test_buyer_phrases_detected(self):
        """Buyer phrases produce positive buyer_intent_score."""
        signals = JorgeHandoffService.extract_intent_signals(
            "I want to buy a house with budget $700k. I'm pre-approved."
        )
        assert signals["buyer_intent_score"] > 0
        assert "buyer intent detected" in signals["detected_intent_phrases"]

    def test_seller_phrases_detected(self):
        """Seller phrases produce positive seller_intent_score."""
        signals = JorgeHandoffService.extract_intent_signals("What's my home worth? I want to sell my house.")
        assert signals["seller_intent_score"] > 0
        assert "seller intent detected" in signals["detected_intent_phrases"]

    def test_neutral_message_no_intent(self):
        """Neutral messages produce zero scores."""
        signals = JorgeHandoffService.extract_intent_signals("Hello, how are you?")
        assert signals["buyer_intent_score"] == 0.0
        assert signals["seller_intent_score"] == 0.0
        assert len(signals["detected_intent_phrases"]) == 0


# ---------------------------------------------------------------------------
# Analytics Tracking
# ---------------------------------------------------------------------------


class TestHandoffAnalytics:
    """Verify analytics are recorded for handoff operations."""

    @pytest.mark.asyncio
    async def test_successful_handoff_recorded(self, handoff_service):
        """Successful handoff increments analytics counters."""
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.9,
            context={},
        )

        await handoff_service.execute_handoff(
            decision=decision,
            contact_id="e2e_analytics_001",
        )

        summary = JorgeHandoffService.get_analytics_summary()
        assert summary["total_handoffs"] >= 1
        assert summary["successful_handoffs"] >= 1
        assert "lead->buyer" in summary["handoffs_by_route"]

    @pytest.mark.asyncio
    async def test_blocked_handoff_recorded(self, handoff_service):
        """Blocked handoff increments blocked counters."""
        contact_id = "e2e_analytics_blocked"

        # Exhaust rate limit
        for _ in range(3):
            JorgeHandoffService._record_handoff(contact_id, "lead", "buyer")

        decision = HandoffDecision(
            source_bot="lead",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.85,
            context={},
        )

        await handoff_service.execute_handoff(
            decision=decision,
            contact_id=contact_id,
        )

        summary = JorgeHandoffService.get_analytics_summary()
        assert summary["blocked_by_rate_limit"] >= 1
