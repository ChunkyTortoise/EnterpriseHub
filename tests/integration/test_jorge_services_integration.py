"""
Jorge Services Cross-Service Integration Tests

Verifies interactions between the 4 Jorge monitoring services:
- PerformanceTracker: latency percentiles and SLA compliance
- BotMetricsCollector: per-bot interaction and handoff aggregation
- AlertingService: threshold-based alerting with cooldowns
- ABTestingService: experiment management, variant assignment, outcomes

All services are singletons reset before and after each test to ensure isolation.
"""

from unittest.mock import AsyncMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker


@pytest.fixture(autouse=True)
def reset_all():
    """Reset all 4 singleton services before and after each test."""
    PerformanceTracker.reset()
    BotMetricsCollector.reset()
    AlertingService.reset()
    ABTestingService.reset()
    yield
    PerformanceTracker.reset()
    BotMetricsCollector.reset()
    AlertingService.reset()
    ABTestingService.reset()


class TestJorgeServicesIntegration:
    """Cross-service integration tests for the Jorge monitoring stack."""

    @pytest.mark.asyncio
    async def test_performance_feeds_alerting(self):
        """Track slow operations via PerformanceTracker, then feed stats to
        AlertingService.check_alerts and verify SLA violation alerts fire."""
        tracker = PerformanceTracker()
        alerting = AlertingService()

        # Track operations that exceed SLA targets for lead_bot
        # SLA target for lead_bot P95 is 2000ms -- push durations well above that
        for _ in range(20):
            await tracker.track_operation("lead_bot", "process", 3500.0, success=True)

        stats = await tracker.get_bot_stats("lead_bot", window="1h")

        # Verify the P95 actually exceeds the SLA target
        assert stats["p95"] > 2000.0, f"Expected P95 > 2000ms for alert trigger, got {stats['p95']}"

        # Build a stats dict shaped for AlertingService default rules
        alert_stats = {
            "lead_bot": {"p95_latency_ms": stats["p95"]},
            "buyer_bot": {"p95_latency_ms": 0},
            "seller_bot": {"p95_latency_ms": 0},
            "error_rate": 1.0 - stats["success_rate"],
        }

        triggered = await alerting.check_alerts(alert_stats)

        # The sla_violation rule should fire because lead_bot P95 > 2000
        sla_alerts = [a for a in triggered if a.rule_name == "sla_violation"]
        assert len(sla_alerts) >= 1, f"Expected sla_violation alert, got rules: {[a.rule_name for a in triggered]}"
        assert sla_alerts[0].severity == "critical"

    @pytest.mark.asyncio
    async def test_metrics_collector_aggregates_multiple_bots(self):
        """Record interactions for all 3 bot types and verify
        get_system_summary returns data for each bot."""
        collector = BotMetricsCollector()

        # Record interactions across all bot types
        collector.record_bot_interaction("lead", duration_ms=200.0, success=True)
        collector.record_bot_interaction("lead", duration_ms=350.0, success=True, cache_hit=True)
        collector.record_bot_interaction("buyer", duration_ms=500.0, success=True)
        collector.record_bot_interaction("buyer", duration_ms=150.0, success=False)
        collector.record_bot_interaction("seller", duration_ms=300.0, success=True)
        collector.record_bot_interaction("seller", duration_ms=400.0, success=True, cache_hit=True)

        # Also record a handoff
        collector.record_handoff("lead", "buyer", success=True, duration_ms=120.0)

        summary = collector.get_system_summary(window_minutes=60)

        # All 3 bots should be present
        assert "lead" in summary["bots"]
        assert "buyer" in summary["bots"]
        assert "seller" in summary["bots"]

        # Verify per-bot counts
        assert summary["bots"]["lead"]["total_interactions"] == 2
        assert summary["bots"]["buyer"]["total_interactions"] == 2
        assert summary["bots"]["seller"]["total_interactions"] == 2

        # Verify lead bot has a cache hit
        assert summary["bots"]["lead"]["cache_hit_rate"] > 0.0

        # Verify buyer bot has an error
        assert summary["bots"]["buyer"]["error_rate"] > 0.0

        # Verify overall totals
        assert summary["overall"]["total_interactions"] == 6

        # Verify handoff data
        assert summary["handoffs"]["total_handoffs"] == 1
        assert summary["handoffs"]["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_ab_testing_with_performance_tracking(self):
        """Full A/B + performance tracking flow: create experiment, assign
        variants, track operation latency per variant, record outcomes,
        and verify results aggregate correctly."""
        ab_service = ABTestingService()
        tracker = PerformanceTracker()

        # Create a response tone experiment
        ab_service.create_experiment(
            "tone_test",
            ["formal", "casual"],
            traffic_split={"formal": 0.5, "casual": 0.5},
        )

        contacts = [f"contact_{i}" for i in range(10)]
        variant_durations = {"formal": 300.0, "casual": 450.0}

        for contact_id in contacts:
            variant = await ab_service.get_variant("tone_test", contact_id)

            # Simulate tracking the operation duration for this variant
            duration = variant_durations[variant]
            await tracker.track_operation("lead_bot", "process", duration, success=True)

            # Record a conversion outcome for each contact
            await ab_service.record_outcome("tone_test", contact_id, variant, "conversion", value=1.0)

        # Verify A/B results
        results = ab_service.get_experiment_results("tone_test")
        assert results.total_impressions == 10
        assert results.total_conversions == 10

        # Each variant should have impressions
        for vs in results.variants:
            assert vs.impressions > 0, f"Variant '{vs.variant}' has no impressions"
            assert vs.conversions > 0, f"Variant '{vs.variant}' has no conversions"

        # Verify performance tracker also captured the operations
        lead_stats = await tracker.get_bot_stats("lead_bot", window="1h")
        assert lead_stats["count"] == 10
        assert lead_stats["success_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_full_workflow_track_collect_alert(self):
        """Full monitoring workflow: record interactions via BotMetricsCollector,
        get system summary, and feed a high-error-rate stats dict to
        AlertingService.check_alerts to trigger the high_error_rate rule.

        AlertingService.send_alert is mocked to prevent real HTTP/SMTP calls.
        """
        collector = BotMetricsCollector()
        alerting = AlertingService()

        # Record a mix of successes and failures to produce a high error rate (>5%)
        for _ in range(8):
            collector.record_bot_interaction("lead", duration_ms=200.0, success=True)
        for _ in range(5):
            collector.record_bot_interaction("lead", duration_ms=800.0, success=False)

        summary = collector.get_system_summary(window_minutes=60)
        overall = summary["overall"]

        # Confirm the error rate exceeds the 5% threshold
        assert overall["error_rate"] > 0.05, (
            f"Expected error_rate > 0.05 for alert trigger, got {overall['error_rate']}"
        )

        # Build a stats dict shaped for the alerting rules
        alert_stats = {
            "error_rate": overall["error_rate"],
            "cache_hit_rate": overall["cache_hit_rate"],
        }

        # Mock send_alert to prevent real notifications
        with patch.object(alerting, "send_alert", new_callable=AsyncMock) as mock_send:
            triggered = await alerting.check_and_send_alerts(alert_stats)

            # high_error_rate rule should fire (error_rate > 0.05)
            error_alerts = [a for a in triggered if a.rule_name == "high_error_rate"]
            assert len(error_alerts) >= 1, f"Expected high_error_rate alert, got: {[a.rule_name for a in triggered]}"
            assert error_alerts[0].severity == "critical"

            # Verify send_alert was called for each triggered alert
            assert mock_send.call_count == len(triggered)

    @pytest.mark.asyncio
    async def test_multiple_bots_concurrent_tracking(self):
        """Track operations for all 3 bots plus handoff via PerformanceTracker,
        retrieve get_all_stats, and verify each bot has recorded data."""
        tracker = PerformanceTracker()

        # Track operations for each bot type
        for _ in range(5):
            await tracker.track_operation("lead_bot", "qualify", 250.0, success=True)
        for _ in range(5):
            await tracker.track_operation("buyer_bot", "process", 400.0, success=True)
        for _ in range(5):
            await tracker.track_operation("seller_bot", "process", 350.0, success=True)
        for _ in range(3):
            await tracker.track_operation("handoff", "execute", 80.0, success=True)

        all_stats = await tracker.get_all_stats(window="1h")

        # Verify each bot has data
        assert all_stats["lead_bot"]["count"] == 5
        assert all_stats["buyer_bot"]["count"] == 5
        assert all_stats["seller_bot"]["count"] == 5
        assert all_stats["handoff"]["count"] == 3

        # Verify latency values are reasonable
        assert all_stats["lead_bot"]["p50"] == 250.0
        assert all_stats["buyer_bot"]["p50"] == 400.0
        assert all_stats["seller_bot"]["p50"] == 350.0
        assert all_stats["handoff"]["p50"] == 80.0

        # All operations succeeded
        for bot_name in ["lead_bot", "buyer_bot", "seller_bot", "handoff"]:
            assert all_stats[bot_name]["success_rate"] == 1.0
            assert all_stats[bot_name]["error_count"] == 0

    @pytest.mark.asyncio
    async def test_metrics_reset_isolation(self):
        """Record data in both BotMetricsCollector and PerformanceTracker,
        reset only BotMetricsCollector, and verify PerformanceTracker
        retains its data while the collector is empty."""
        collector = BotMetricsCollector()
        tracker = PerformanceTracker()

        # Record data in both services
        collector.record_bot_interaction("lead", duration_ms=200.0, success=True)
        collector.record_bot_interaction("buyer", duration_ms=300.0, success=True)
        await tracker.track_operation("lead_bot", "process", 200.0, success=True)
        await tracker.track_operation("buyer_bot", "process", 300.0, success=True)

        # Verify both have data
        summary_before = collector.get_system_summary(window_minutes=60)
        assert summary_before["overall"]["total_interactions"] == 2

        lead_stats_before = await tracker.get_bot_stats("lead_bot", window="1h")
        assert lead_stats_before["count"] == 1

        # Reset only the collector
        BotMetricsCollector.reset()

        # Collector should be empty after reset
        fresh_collector = BotMetricsCollector()
        summary_after = fresh_collector.get_system_summary(window_minutes=60)
        assert summary_after["overall"]["total_interactions"] == 0

        # PerformanceTracker should still have its data
        lead_stats_after = await tracker.get_bot_stats("lead_bot", window="1h")
        assert lead_stats_after["count"] == 1
        assert lead_stats_after["p50"] == 200.0

        buyer_stats_after = await tracker.get_bot_stats("buyer_bot", window="1h")
        assert buyer_stats_after["count"] == 1
        assert buyer_stats_after["p50"] == 300.0
