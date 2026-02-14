"""
Tests for Jorge Handoff Router

Tests performance-based handoff routing including:
- SLA threshold detection (P95 latency, error rate)
- Deferral decision logic
- Retry mechanism with cooldown
- Auto-recovery when performance improves
- Integration with PerformanceTracker
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.handoff_router import (
    DeferralDecision,
    DeferredHandoff,
    HandoffRouter,
)
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


@pytest.fixture
def performance_tracker():
    """Create a fresh PerformanceTracker instance for each test."""
    PerformanceTracker.reset()
    return PerformanceTracker()


@pytest.fixture
def handoff_router(performance_tracker):
    """Create a fresh HandoffRouter instance with performance tracker."""
    router = HandoffRouter(performance_tracker=performance_tracker)
    return router


@pytest.fixture
def mock_analytics_service():
    """Mock analytics service for event tracking."""
    service = AsyncMock()
    service.track_event = AsyncMock()
    return service


class TestShouldDeferHandoff:
    """Tests for should_defer_handoff method."""

    @pytest.mark.asyncio
    async def test_no_data_allows_handoff(self, handoff_router):
        """When no performance data exists, handoff should be allowed."""
        decision = await handoff_router.should_defer_handoff("buyer_bot")

        assert not decision.should_defer
        assert "No performance data" in decision.reason
        assert decision.target_bot == "buyer_bot"

    @pytest.mark.asyncio
    async def test_healthy_bot_allows_handoff(self, handoff_router, performance_tracker):
        """Healthy bot (P95 < 100% SLA, error rate < 5%) allows handoff."""
        # Record good performance data
        for _ in range(20):
            await performance_tracker.track_operation("buyer_bot", "process", 1200.0, success=True)

        decision = await handoff_router.should_defer_handoff("buyer_bot")

        assert not decision.should_defer
        assert decision.target_bot == "buyer_bot"
        assert decision.p95_percent_of_sla < 1.0  # Less than 100% of SLA

    @pytest.mark.asyncio
    async def test_high_error_rate_defers_handoff(self, handoff_router, performance_tracker):
        """Error rate > 10% triggers deferral."""
        # Record operations with 20% error rate
        for i in range(20):
            success = i % 5 != 0  # 80% success = 20% error
            await performance_tracker.track_operation("buyer_bot", "process", 1000.0, success=success)

        decision = await handoff_router.should_defer_handoff("buyer_bot")

        assert decision.should_defer
        assert "Error rate" in decision.reason
        assert decision.error_rate > 0.10
        assert decision.target_bot == "buyer_bot"

    @pytest.mark.asyncio
    async def test_high_p95_latency_defers_handoff(self, handoff_router, performance_tracker):
        """P95 > 120% of SLA triggers deferral."""
        # SLA target for buyer_bot process operation is 1800ms
        # Record operations with P95 > 2160ms (120% of 1800)
        # All samples at high latency to guarantee P95 > threshold
        for _ in range(20):
            await performance_tracker.track_operation("buyer_bot", "process", 3000.0, success=True)

        decision = await handoff_router.should_defer_handoff("buyer_bot")

        assert decision.should_defer
        assert "P95 latency" in decision.reason
        assert decision.p95_percent_of_sla > 1.2  # > 120% of SLA
        assert decision.target_bot == "buyer_bot"

    @pytest.mark.asyncio
    async def test_warning_threshold_allows_but_warns(self, handoff_router, performance_tracker, caplog):
        """P95 100-120% of SLA or error rate 5-10% warns but allows handoff."""
        import logging

        caplog.set_level(logging.WARNING)

        # Record operations with error rate around 7% (warn threshold)
        for i in range(20):
            success = i % 14 != 0  # ~93% success = ~7% error
            await performance_tracker.track_operation("buyer_bot", "process", 1000.0, success=success)

        decision = await handoff_router.should_defer_handoff("buyer_bot")

        assert not decision.should_defer
        assert "Performance within acceptable limits" in decision.reason
        assert "approaching performance limits" in caplog.text


class TestDeferHandoff:
    """Tests for defer_handoff method."""

    @pytest.mark.asyncio
    async def test_defer_handoff_creates_record(self, handoff_router):
        """Deferring a handoff creates a deferred handoff record."""
        result = await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        assert result["deferred"] is True
        assert not result["permanent"]
        assert "retry_after" in result
        assert result["retry_count"] == 0
        assert result["max_retries"] == handoff_router.MAX_RETRIES

        # Check internal state
        assert "contact_123" in handoff_router._deferred_handoffs
        assert len(handoff_router._deferred_handoffs["contact_123"]) == 1

        deferred = handoff_router._deferred_handoffs["contact_123"][0]
        assert deferred.source_bot == "lead_bot"
        assert deferred.target_bot == "buyer_bot"
        assert deferred.deferral_reason == "High error rate"

    @pytest.mark.asyncio
    async def test_defer_handoff_increments_retry_count(self, handoff_router):
        """Multiple deferrals for same handoff increment retry count."""
        # First deferral
        await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        # Second deferral
        result = await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        assert result["retry_count"] == 1

    @pytest.mark.asyncio
    async def test_max_retries_creates_permanent_deferral(self, handoff_router):
        """Exceeding max retries creates a permanent deferral."""
        # Create MAX_RETRIES deferrals
        for _ in range(handoff_router.MAX_RETRIES):
            await handoff_router.defer_handoff(
                contact_id="contact_123",
                source_bot="lead_bot",
                target_bot="buyer_bot",
                reason="High error rate",
            )

        # Next deferral should be permanent
        result = await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        assert result["deferred"] is True
        assert result["permanent"] is True
        assert "Max retries exceeded" in result["reason"]

        stats = handoff_router.get_deferral_stats()
        assert stats["permanent_deferrals"] == 1

    @pytest.mark.asyncio
    async def test_defer_handoff_logs_analytics(self, mock_analytics_service):
        """Deferring a handoff logs analytics event."""
        router = HandoffRouter(analytics_service=mock_analytics_service)

        await router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
            location_id="loc_456",
        )

        mock_analytics_service.track_event.assert_awaited_once()
        call_args = mock_analytics_service.track_event.call_args
        assert call_args.kwargs["event_type"] == "jorge_handoff_deferred"
        assert call_args.kwargs["contact_id"] == "contact_123"
        assert call_args.kwargs["location_id"] == "loc_456"


class TestCheckDeferredHandoffs:
    """Tests for check_deferred_handoffs method."""

    @pytest.mark.asyncio
    async def test_check_before_cooldown_returns_empty(self, handoff_router, performance_tracker):
        """Checking deferred handoffs before cooldown returns empty list."""
        # Defer a handoff
        await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        # Check immediately (cooldown not elapsed)
        ready = await handoff_router.check_deferred_handoffs()

        assert len(ready) == 0

    @pytest.mark.asyncio
    async def test_check_after_cooldown_with_improved_performance(self, handoff_router, performance_tracker):
        """After cooldown, if performance improved, handoff is ready for retry."""
        # Record bad performance first (so deferral is justified)
        for i in range(20):
            success = i % 3 != 0  # ~67% success = ~33% error
            await performance_tracker.track_operation("buyer_bot", "process", 1000.0, success=success)

        # Defer a handoff (manually, not via should_defer which tracks stats)
        await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        # Simulate cooldown elapsed by modifying retry_after
        handoff_router._deferred_handoffs["contact_123"][0].retry_after = time.time() - 1

        # Record good performance (more samples to override previous bad data)
        for _ in range(50):
            await performance_tracker.track_operation("buyer_bot", "process", 1000.0, success=True)

        # Check deferred handoffs
        ready = await handoff_router.check_deferred_handoffs()

        assert len(ready) == 1
        assert ready[0]["contact_id"] == "contact_123"
        assert ready[0]["source_bot"] == "lead_bot"
        assert ready[0]["target_bot"] == "buyer_bot"
        assert "Performance within acceptable limits" in ready[0]["recovery_reason"]

        # Deferred handoff should be removed
        assert "contact_123" not in handoff_router._deferred_handoffs

        # Auto-recovery counter incremented
        stats = handoff_router.get_deferral_stats()
        assert stats["auto_recoveries"] == 1

    @pytest.mark.asyncio
    async def test_check_after_cooldown_with_poor_performance(self, handoff_router, performance_tracker):
        """After cooldown, if performance still poor, handoff remains deferred."""
        # Record bad performance
        for i in range(20):
            success = i % 3 != 0  # ~67% success = ~33% error
            await performance_tracker.track_operation("buyer_bot", "process", 1000.0, success=success)

        # Defer a handoff
        await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        # Simulate cooldown elapsed
        handoff_router._deferred_handoffs["contact_123"][0].retry_after = time.time() - 1

        # Check deferred handoffs (performance still bad)
        ready = await handoff_router.check_deferred_handoffs()

        assert len(ready) == 0
        assert "contact_123" in handoff_router._deferred_handoffs


class TestDeferralStats:
    """Tests for deferral statistics tracking."""

    @pytest.mark.asyncio
    async def test_deferral_stats_tracked(self, handoff_router):
        """Deferral statistics are correctly tracked."""
        # Defer handoffs for different bots
        await handoff_router.defer_handoff(
            contact_id="contact_1",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
        )

        await handoff_router.defer_handoff(
            contact_id="contact_2",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High P95 latency",
        )

        await handoff_router.defer_handoff(
            contact_id="contact_3",
            source_bot="buyer_bot",
            target_bot="seller_bot",
            reason="High error rate",
        )

        stats = handoff_router.get_deferral_stats()

        assert stats["total_deferrals"] == 3
        assert stats["current_deferred_count"] == 3
        assert stats["current_deferred_contacts"] == 3

        assert "buyer_bot" in stats["deferrals_by_bot"]
        assert stats["deferrals_by_bot"]["buyer_bot"]["total"] == 2

        assert "seller_bot" in stats["deferrals_by_bot"]
        assert stats["deferrals_by_bot"]["seller_bot"]["total"] == 1


class TestIntegrationWithHandoffService:
    """Integration tests with JorgeHandoffService."""

    @pytest.mark.asyncio
    async def test_handoff_deferred_when_target_slow(self, performance_tracker):
        """Handoff is deferred when target bot has poor performance."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            HandoffDecision,
            JorgeHandoffService,
        )

        # Reset handoff service state
        JorgeHandoffService.reset_analytics()

        # Record slow performance for buyer bot (all samples high to guarantee deferral)
        for _ in range(20):
            await performance_tracker.track_operation("buyer_bot", "process", 3000.0, success=True)

        # Create handoff service
        handoff_service = JorgeHandoffService()

        # Create handoff decision
        decision = HandoffDecision(
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="buyer_intent_detected",
            confidence=0.85,
        )

        # Execute handoff
        result = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_123",
        )

        # Should be deferred due to performance
        assert len(result) == 1
        assert result[0]["handoff_executed"] is False
        assert "Performance" in result[0]["reason"]
        assert result[0]["deferred"] is True

    @pytest.mark.asyncio
    async def test_handoff_executes_when_target_healthy(self, performance_tracker):
        """Handoff executes normally when target bot is healthy."""
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            HandoffDecision,
            JorgeHandoffService,
        )

        # Reset handoff service state
        JorgeHandoffService.reset_analytics()

        # Record good performance for buyer bot
        for _ in range(20):
            await performance_tracker.track_operation("buyer_bot", "process", 1200.0, success=True)

        # Create handoff service
        handoff_service = JorgeHandoffService()

        # Create handoff decision
        decision = HandoffDecision(
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="buyer_intent_detected",
            confidence=0.85,
        )

        # Execute handoff with unique contact to avoid circular detection
        result = await handoff_service.execute_handoff(
            decision=decision,
            contact_id="contact_healthy_test",
        )

        # Should execute normally
        assert len(result) > 0
        # Check that actions include tag operations (not deferral)
        has_tag_actions = any("type" in action for action in result)
        assert has_tag_actions


class TestPersistence:
    """Tests for database persistence."""

    @pytest.mark.asyncio
    async def test_set_repository_configures_persistence(self, handoff_router):
        """Setting repository enables persistence."""
        mock_repo = MagicMock()
        handoff_router.set_repository(mock_repo)

        assert handoff_router._repository is mock_repo

    @pytest.mark.asyncio
    async def test_defer_handoff_persists_to_db(self, handoff_router):
        """Deferred handoffs are persisted to database."""
        mock_repo = AsyncMock()
        mock_repo.save_deferral_event = AsyncMock()
        handoff_router.set_repository(mock_repo)

        await handoff_router.defer_handoff(
            contact_id="contact_123",
            source_bot="lead_bot",
            target_bot="buyer_bot",
            reason="High error rate",
            location_id="loc_456",
        )

        mock_repo.save_deferral_event.assert_awaited_once()
        call_args = mock_repo.save_deferral_event.call_args
        assert call_args.kwargs["contact_id"] == "contact_123"
        assert call_args.kwargs["source_bot"] == "lead_bot"
        assert call_args.kwargs["target_bot"] == "buyer_bot"
        assert call_args.kwargs["target_bot"] == "buyer_bot"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
