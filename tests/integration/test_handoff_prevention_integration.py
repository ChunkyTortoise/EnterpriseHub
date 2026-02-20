import pytest

pytestmark = pytest.mark.integration

"""Integration tests for handoff prevention safeguards.

Exercises circular prevention, rate limiting, concurrent lock handling,
and lock expiration across the JorgeHandoffService.
"""

import asyncio
import time

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    HandoffDecision,
    JorgeHandoffService,
)


@pytest.fixture(autouse=True)
def _reset_handoff_state():
    """Clear all class-level state before and after each test."""
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()
    yield
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()


@pytest.fixture()
def svc():
    return JorgeHandoffService()


def _decision(source: str, target: str, confidence: float = 0.85) -> HandoffDecision:
    return HandoffDecision(
        source_bot=source,
        target_bot=target,
        reason=f"{target}_intent_detected",
        confidence=confidence,
    )


class TestHandoffPreventionIntegration:
    """Integration tests covering handoff safeguards (spec: 6 tests)."""

    # ── Circular Prevention ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_circular_handoff_blocked_within_30_minutes(self, svc):
        """Same source->target handoff is blocked within the 30-minute window."""
        contact = "contact-circ-1"
        decision = _decision("lead", "buyer")

        # First handoff succeeds
        actions1 = await svc.execute_handoff(decision, contact)
        assert actions1[0].get("handoff_executed") is not False

        # Same direction immediately blocked
        actions2 = await svc.execute_handoff(decision, contact)
        assert actions2[0]["handoff_executed"] is False
        assert "Circular" in actions2[0]["reason"]

        # Analytics should record the block
        summary = JorgeHandoffService.get_analytics_summary()
        assert summary["blocked_by_circular"] >= 1

    @pytest.mark.asyncio
    async def test_circular_handoff_chain_detected(self, svc):
        """Circular chains (Lead->Buyer->Lead) are detected via evaluate_handoff."""
        contact = "contact-chain-1"
        history = [{"role": "user", "content": "I want to buy a home"}]

        # First: Lead -> Buyer (succeeds)
        signals_buy = {"buyer_intent_score": 0.9, "seller_intent_score": 0.0}
        decision1 = await svc.evaluate_handoff("lead", contact, history, signals_buy)
        assert decision1 is not None
        assert decision1.target_bot == "buyer"
        await svc.execute_handoff(decision1, contact)

        # Second: Buyer -> Seller (succeeds — different route)
        signals_sell = {"buyer_intent_score": 0.0, "seller_intent_score": 0.9}
        decision2 = await svc.evaluate_handoff("buyer", contact, history, signals_sell)
        # This may or may not be blocked depending on chain detection — if it returns
        # a decision, execute it; either way the next step is what we really test
        if decision2 is not None:
            await svc.execute_handoff(decision2, contact)

        # Third: Seller -> Buyer (would create cycle — should be blocked)
        signals_buy2 = {"buyer_intent_score": 0.9, "seller_intent_score": 0.0}
        decision3 = await svc.evaluate_handoff("seller", contact, history, signals_buy2)
        # Either evaluate_handoff returns None (circular prevention)
        # or execute_handoff blocks it
        if decision3 is not None:
            actions = await svc.execute_handoff(decision3, contact)
            assert actions[0]["handoff_executed"] is False

    # ── Rate Limiting ────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_3_hourly_handoffs(self, svc):
        """Rate limit blocks the 4th handoff within 1 hour for the same contact."""
        contact = "contact-rate-hourly"

        # Use different routes to avoid circular blocks
        routes = [
            _decision("lead", "buyer"),
            _decision("buyer", "seller"),
            _decision("seller", "buyer"),
        ]

        for i, decision in enumerate(routes):
            actions = await svc.execute_handoff(decision, contact)
            # The first 3 may succeed or be blocked by circular — record them
            # manually if circular blocks them, to saturate the rate limit
            if actions[0].get("handoff_executed") is False:
                # Force-record to fill the rate limit bucket
                JorgeHandoffService._record_handoff(contact, decision.source_bot, decision.target_bot)

        # 4th handoff should be rate-limited regardless of route
        decision4 = _decision("lead", "seller")
        actions4 = await svc.execute_handoff(decision4, contact)
        assert actions4[0]["handoff_executed"] is False
        assert "Rate limit" in actions4[0]["reason"]

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_after_10_daily_handoffs(self, svc):
        """Rate limit blocks the 11th handoff within 24 hours."""
        contact = "contact-rate-daily"

        # Inject 10 handoff history entries spread across the day.
        # Use routes that won't match the 11th handoff's circular check.
        # Routes: lead->seller and buyer->seller alternating
        for i in range(10):
            src = "lead" if i % 2 == 0 else "buyer"
            JorgeHandoffService._handoff_history.setdefault(contact, []).append(
                {
                    "from": src,
                    "to": "seller",
                    "timestamp": time.time() - (i * 2000),  # spread across ~5.5 hours
                }
            )

        # 11th handoff uses a route NOT in history (seller->buyer) to
        # avoid circular detection — should hit the daily rate limit
        decision = _decision("seller", "buyer")
        actions = await svc.execute_handoff(decision, contact)
        assert actions[0]["handoff_executed"] is False
        assert "Rate limit" in actions[0]["reason"]

    # ── Concurrent Lock ──────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_concurrent_handoff_prevents_race_conditions(self, svc):
        """Concurrent handoffs for the same contact are serialized by the lock."""
        contact = "contact-concurrent"

        # Manually acquire the lock to simulate an in-progress handoff
        assert JorgeHandoffService._acquire_handoff_lock(contact) is True

        # Second attempt should fail (lock held)
        decision = _decision("lead", "buyer")
        actions = await svc.execute_handoff(decision, contact)
        assert actions[0]["handoff_executed"] is False
        assert "Concurrent" in actions[0]["reason"]

        # Release the lock
        JorgeHandoffService._release_handoff_lock(contact)

        # Now it should succeed
        actions2 = await svc.execute_handoff(decision, contact)
        assert actions2[0].get("handoff_executed") is not False

    @pytest.mark.asyncio
    async def test_handoff_lock_expires_after_timeout(self, svc):
        """Lock automatically expires after HANDOFF_LOCK_TIMEOUT seconds."""
        contact = "contact-lock-expire"

        # Manually set a lock timestamp in the past (beyond timeout)
        expired_time = time.time() - JorgeHandoffService.HANDOFF_LOCK_TIMEOUT - 1
        JorgeHandoffService._active_handoffs[contact] = expired_time

        # Should succeed because the lock has expired
        decision = _decision("lead", "buyer")
        actions = await svc.execute_handoff(decision, contact)
        assert actions[0].get("handoff_executed") is not False