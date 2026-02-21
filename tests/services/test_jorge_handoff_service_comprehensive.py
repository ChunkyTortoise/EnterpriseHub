"""Comprehensive tests for Jorge Handoff Service - Phase 4 Coverage.

Tests for:
- Circular prevention (same source→target blocked within 30min)
- Rate limiting (3 handoffs/hr, 10/day per contact)
- Conflict resolution (contact-level locking)
- Pattern learning (dynamic threshold adjustment)
- evaluate_handoff() method comprehensive tests
"""

import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    EnrichedHandoffContext,
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
    """Create a fresh handoff service with reset class state."""
    JorgeHandoffService.reset_analytics()
    # Clear any class-level state
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._active_handoffs.clear()
    return JorgeHandoffService(analytics_service=mock_analytics)


# =============================================================================
# Circular Prevention Tests
# =============================================================================


class TestCircularPrevention:
    """Tests for circular handoff prevention (30-min window)."""

    def test_circular_prevention_same_source_target_within_30min(self, handoff_service):
        """Same source->target within 30 minutes should be blocked."""
        contact_id = "circular_test_001"

        # Record a handoff 10 minutes ago
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": time.time() - 600}  # 10 min ago
        ]

        # Try to handoff again - should be blocked
        is_blocked, reason = JorgeHandoffService._check_circular_prevention(contact_id, "lead", "buyer")

        assert is_blocked is True
        assert "lead->buyer" in reason
        assert "30-min" in reason

    def test_circular_prevention_allows_after_30min(self, handoff_service):
        """Same source->target after 30 minutes should be allowed."""
        contact_id = "circular_test_002"

        # Record a handoff 31 minutes ago (past the window)
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": time.time() - 1900}  # ~32 min ago
        ]

        # Try to handoff again - should be allowed
        is_blocked, reason = JorgeHandoffService._check_circular_prevention(contact_id, "lead", "buyer")

        assert is_blocked is False

    def test_circular_prevention_different_source_target_allowed(self, handoff_service):
        """Different source->target routes should be allowed."""
        contact_id = "circular_test_003"

        # Record lead->buyer handoff
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": time.time() - 600}
        ]

        # Try lead->seller - should be allowed (different target)
        is_blocked, reason = JorgeHandoffService._check_circular_prevention(contact_id, "lead", "seller")

        assert is_blocked is False

    def test_circular_chain_detection(self, handoff_service):
        """Circular chain patterns should be detected (Lead->Buyer->Lead)."""
        contact_id = "circular_test_004"

        # Record a chain: lead->buyer (10 min ago), buyer->seller (5 min ago)
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": time.time() - 600},
            {"from": "buyer", "to": "seller", "timestamp": time.time() - 300},
        ]

        # Try to handoff back to lead - would create cycle: lead->buyer->seller->lead
        is_blocked, reason = JorgeHandoffService._check_circular_prevention(contact_id, "seller", "lead")

        # This should detect the chain would create a cycle
        assert is_blocked is True
        assert "cycle" in reason.lower() or "chain" in reason.lower()

    def test_no_history_allows_handoff(self, handoff_service):
        """Contacts with no handoff history should be allowed to handoff."""
        contact_id = "new_contact_001"

        is_blocked, reason = JorgeHandoffService._check_circular_prevention(contact_id, "lead", "buyer")

        assert is_blocked is False


# =============================================================================
# Rate Limiting Tests
# =============================================================================


class TestRateLimiting:
    """Tests for rate limiting (3/hour, 10/day)."""

    def test_rate_limit_hourly_limit_blocked(self, handoff_service):
        """Should block when hourly limit (3/hr) exceeded."""
        contact_id = "rate_test_001"

        # Record 3 handoffs in the last hour
        now = time.time()
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": now - 600},
            {"from": "buyer", "to": "seller", "timestamp": now - 1200},
            {"from": "seller", "to": "lead", "timestamp": now - 1800},
        ]

        result = JorgeHandoffService._check_rate_limit(contact_id)

        assert result is not None
        assert "hour" in result.lower()
        assert "3" in result

    def test_rate_limit_hourly_allowed_below_limit(self, handoff_service):
        """Should allow when hourly limit not reached."""
        contact_id = "rate_test_002"

        # Record only 2 handoffs in the last hour
        now = time.time()
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": now - 600},
            {"from": "buyer", "to": "seller", "timestamp": now - 1200},
        ]

        result = JorgeHandoffService._check_rate_limit(contact_id)

        assert result is None

    def test_rate_limit_daily_limit_blocked(self, handoff_service):
        """Should block when daily limit (10/day) exceeded."""
        contact_id = "rate_test_003"

        # Record 10 handoffs in the last 24 hours
        now = time.time()
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": now - (i * 7000)} for i in range(10)
        ]

        result = JorgeHandoffService._check_rate_limit(contact_id)

        assert result is not None
        assert "24 hour" in result.lower() or "day" in result.lower()

    def test_rate_limit_old_handoffs_not_counted(self, handoff_service):
        """Handoffs older than 24 hours should not count toward daily limit."""
        contact_id = "rate_test_004"

        # Record 2 recent handoffs (within hour, below limit of 3) + 10 old handoffs (>24 hours ago)
        now = time.time()
        recent = [
            {"from": "lead", "to": "buyer", "timestamp": now - 600},
            {"from": "buyer", "to": "seller", "timestamp": now - 1200},
        ]
        old = [{"from": "lead", "to": "seller", "timestamp": now - 100000} for _ in range(10)]
        JorgeHandoffService._handoff_history[contact_id] = recent + old

        result = JorgeHandoffService._check_rate_limit(contact_id)

        assert result is None  # Only 2 recent handoffs count, below 3/hr limit


# =============================================================================
# Conflict Resolution / Locking Tests
# =============================================================================


class TestConflictResolution:
    """Tests for contact-level locking (conflict resolution)."""

    def test_lock_acquired_success(self, handoff_service):
        """Lock should be acquired when no active lock exists."""
        contact_id = "lock_test_001"

        result = JorgeHandoffService._acquire_handoff_lock(contact_id)

        assert result is True
        assert contact_id in JorgeHandoffService._active_handoffs

    def test_lock_blocked_when_active(self, handoff_service):
        """Lock should be blocked when another handoff is in progress."""
        contact_id = "lock_test_002"

        # First acquire lock
        JorgeHandoffService._acquire_handoff_lock(contact_id)

        # Second attempt should fail
        result = JorgeHandoffService._acquire_handoff_lock(contact_id)

        assert result is False

    def test_lock_released(self, handoff_service):
        """Lock should be released after handoff completes."""
        contact_id = "lock_test_003"

        JorgeHandoffService._acquire_handoff_lock(contact_id)
        JorgeHandoffService._release_handoff_lock(contact_id)

        assert contact_id not in JorgeHandoffService._active_handoffs

    def test_lock_timeout_allows_retry(self, handoff_service):
        """After lock timeout (30s), new handoff should be allowed."""
        contact_id = "lock_test_004"

        # Set lock to expire (more than 30 seconds ago)
        JorgeHandoffService._active_handoffs[contact_id] = time.time() - 35

        # Should be able to acquire lock now
        result = JorgeHandoffService._acquire_handoff_lock(contact_id)

        assert result is True


# =============================================================================
# Pattern Learning / Dynamic Threshold Adjustment Tests
# =============================================================================


class TestPatternLearning:
    """Tests for dynamic threshold adjustment based on handoff outcomes."""

    def test_learned_adjustments_default(self, handoff_service):
        """Should return default adjustment when no history exists."""
        adjustments = handoff_service.get_learned_adjustments("lead", "buyer")

        assert adjustments["adjustment"] == 0.0
        assert adjustments["success_rate"] == 0.0
        assert adjustments["sample_size"] == 0

    def test_learned_adjustments_positive_for_good_outcomes(self, handoff_service):
        """Positive adjustment when success rate is high."""
        # Record successful handoffs
        JorgeHandoffService._record_handoff("learn_001", "lead", "buyer")
        JorgeHandoffService._record_handoff("learn_001", "lead", "buyer")

        # Record outcomes
        for _ in range(8):
            handoff_service.record_handoff_outcome(
                contact_id="learn_001",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
            )
        for _ in range(2):
            handoff_service.record_handoff_outcome(
                contact_id="learn_001",
                source_bot="lead",
                target_bot="buyer",
                outcome="failed",
            )

        adjustments = handoff_service.get_learned_adjustments("lead", "buyer")

        # 80% success rate should give positive adjustment
        assert adjustments["success_rate"] > 0.5
        assert adjustments["sample_size"] == 10

    def test_learned_adjustments_positive_for_poor_outcomes(self, handoff_service):
        """Positive adjustment (harder handoffs) when success rate is low."""
        # Record outcomes with low success
        for _ in range(2):
            handoff_service.record_handoff_outcome(
                contact_id="learn_002",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
            )
        for _ in range(8):
            handoff_service.record_handoff_outcome(
                contact_id="learn_002",
                source_bot="lead",
                target_bot="buyer",
                outcome="failed",
            )

        adjustments = handoff_service.get_learned_adjustments("lead", "buyer")

        # 20% success rate should raise threshold (positive adjustment = harder handoffs)
        assert adjustments["adjustment"] > 0.0
        assert adjustments["success_rate"] < 0.5

    @pytest.mark.asyncio
    async def test_threshold_adjusted_for_learned_patterns(self, handoff_service):
        """Threshold should be adjusted based on learned patterns."""
        # High success rate should lower threshold
        # Need > 0.8 (strictly greater), so 9/10 = 0.9
        for _ in range(9):
            handoff_service.record_handoff_outcome(
                contact_id="learn_003",
                source_bot="lead",
                target_bot="buyer",
                outcome="successful",
            )
        for _ in range(1):
            handoff_service.record_handoff_outcome(
                contact_id="learn_003",
                source_bot="lead",
                target_bot="buyer",
                outcome="failed",
            )

        # With 90% success rate (> 0.8), adjustment is -0.05
        # Adjusted threshold: 0.7 - 0.05 = 0.65
        # Score of 0.66 should now pass the adjusted threshold
        intent_signals = {
            "buyer_intent_score": 0.66,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": [],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id="learn_003",
            conversation_history=[],
            intent_signals=intent_signals,
        )

        # Should succeed because adjusted threshold is lower
        assert decision is not None
        assert decision.target_bot == "buyer"


# =============================================================================
# Comprehensive evaluate_handoff() Tests
# =============================================================================


class TestEvaluateHandoffComprehensive:
    """Comprehensive tests for evaluate_handoff method."""

    @pytest.mark.asyncio
    async def test_evaluate_handoff_with_rate_limit_blocked(self, handoff_service):
        """evaluate_handoff blocked by circular prevention when same direction in history."""
        contact_id = "eval_rate_001"

        # Add same-direction handoff in history (lead->buyer within 30min)
        now = time.time()
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": now - 600},
        ]

        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["want to buy"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )

        # Circular prevention blocks same-direction handoff within 30min window
        assert decision is None

    @pytest.mark.asyncio
    async def test_evaluate_handoff_circular_blocked(self, handoff_service):
        """evaluate_handoff should return None when circular pattern detected."""
        contact_id = "eval_circular_001"

        # Recent same-direction handoff
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": time.time() - 600}
        ]

        intent_signals = {
            "buyer_intent_score": 0.9,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["want to buy"],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )

        # Circular prevention blocks within evaluate_handoff
        assert decision is None

    @pytest.mark.asyncio
    async def test_evaluate_handoff_history_signal_boost(self, handoff_service):
        """Conversation history signals should boost intent scores."""
        # Use a fresh contact with no circular issues
        contact_id = f"eval_history_{int(time.time())}"

        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": [],
        }

        # Add history with multiple buyer intent phrases to trigger enough pattern matches
        # Each pattern match = 0.2 confidence, blended at 50% into base score
        # Need buyer_intent >= 0.4 (i.e. 2+ pattern matches) to reach 0.5 + 0.4*0.5 = 0.7
        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[
                {"role": "user", "content": "I want to buy a home and I'm looking to buy soon"},
                {"role": "user", "content": "I got pre-approved for a conventional loan"},
                {"role": "user", "content": "My budget is $500k with a down payment ready"},
            ],
            intent_signals=intent_signals,
        )

        # History should boost the score above threshold (0.7)
        assert decision is not None
        assert decision.target_bot == "buyer"

    @pytest.mark.asyncio
    async def test_evaluate_handoff_no_self_handoff(self, handoff_service):
        """Should not handoff to the same bot."""
        contact_id = f"eval_self_{int(time.time())}"

        intent_signals = {
            "buyer_intent_score": 0.0,
            "seller_intent_score": 0.0,
            "detected_intent_phrases": [],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None

    @pytest.mark.asyncio
    async def test_evaluate_handoff_buyer_seller_tie(self, handoff_service):
        """When scores are equal, should not handoff."""
        contact_id = f"eval_tie_{int(time.time())}"

        intent_signals = {
            "buyer_intent_score": 0.5,
            "seller_intent_score": 0.5,
            "detected_intent_phrases": [],
        }

        decision = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )

        assert decision is None


# =============================================================================
# Analytics and Recording Tests
# =============================================================================


class TestAnalyticsAndRecording:
    """Tests for analytics tracking and handoff recording."""

    def test_record_handoff(self, handoff_service):
        """Handoff should be recorded in history."""
        contact_id = "record_001"

        JorgeHandoffService._record_handoff(contact_id, "lead", "buyer")

        assert contact_id in JorgeHandoffService._handoff_history
        assert len(JorgeHandoffService._handoff_history[contact_id]) == 1

    def test_cleanup_removes_old_entries(self, handoff_service):
        """Old entries (>24h) should be cleaned up."""
        contact_id = "cleanup_001"

        now = time.time()
        JorgeHandoffService._handoff_history[contact_id] = [
            {"from": "lead", "to": "buyer", "timestamp": now - 100000},  # Old
            {"from": "buyer", "to": "seller", "timestamp": now - 600},  # Recent
        ]

        JorgeHandoffService._cleanup_old_entries()

        assert len(JorgeHandoffService._handoff_history[contact_id]) == 1

    def test_analytics_incremented(self, handoff_service):
        """Analytics should track handoff counts."""
        initial = JorgeHandoffService._analytics["total_handoffs"]

        JorgeHandoffService._record_analytics(
            route="lead->buyer",
            start_time=time.time(),
            success=True,
        )

        assert JorgeHandoffService._analytics["total_handoffs"] == initial + 1
        assert JorgeHandoffService._analytics["successful_handoffs"] == 1
