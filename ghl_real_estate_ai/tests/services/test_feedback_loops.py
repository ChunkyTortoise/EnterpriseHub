"""
Tests for Jorge Phase 3 Feedback Loops.

Validates all 5 closed-loop feedback mechanisms.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.feedback_loops import (
    ABANDONMENT_SILENCE_SECONDS,
    MAX_ROUTING_WEIGHT,
    MIN_ROUTING_WEIGHT,
    RECOVERY_MAX_ATTEMPTS,
    WEIGHT_DECAY_FACTOR,
    WEIGHT_RECOVERY_FACTOR,
    AbandonmentRecord,
    FeedbackLoopManager,
)


@pytest.fixture
def mock_handoff_service():
    svc = MagicMock()
    svc.MIN_LEARNING_SAMPLES = 10
    svc.get_learned_adjustments = MagicMock(return_value={
        "adjustment": -0.05,
        "success_rate": 0.85,
        "sample_size": 20,
    })
    return svc


@pytest.fixture
def mock_ab_testing():
    svc = MagicMock()
    svc.get_promotion_candidates = MagicMock(return_value=[])
    svc.deactivate_experiment = MagicMock()
    return svc


@pytest.fixture
def mock_alerting():
    svc = AsyncMock()
    svc.check_escalations = AsyncMock(return_value=[])
    svc.send_alert = AsyncMock()
    svc._send_pagerduty_alert = AsyncMock()
    svc._send_opsgenie_alert = AsyncMock()
    return svc


@pytest.fixture
def mock_perf_tracker():
    tracker = AsyncMock()
    tracker.get_bot_stats = AsyncMock(return_value={
        "p50": 200.0,
        "p95": 800.0,
        "p99": 1200.0,
        "mean": 300.0,
        "min": 50.0,
        "max": 1500.0,
        "count": 100,
        "success_count": 95,
        "error_count": 5,
        "cache_hit_count": 60,
        "cache_hit_rate": 0.6,
        "success_rate": 0.95,
    })
    return tracker


@pytest.fixture
def manager(mock_handoff_service, mock_ab_testing, mock_alerting, mock_perf_tracker):
    return FeedbackLoopManager(
        handoff_service=mock_handoff_service,
        ab_testing_service=mock_ab_testing,
        alerting_service=mock_alerting,
        performance_tracker=mock_perf_tracker,
    )


# ── Loop 1: Threshold Adjustment ────────────────────────────────────


class TestLoop1ThresholdAdjustment:
    """Loop 1: Handoff outcome -> threshold adjustment."""

    @pytest.mark.asyncio
    async def test_reports_adjustments_for_all_routes(self, manager, mock_handoff_service):
        result = await manager.run_threshold_adjustment_loop()

        assert result["status"] == "ok"
        assert "lead->buyer" in result["adjustments"]
        assert "lead->seller" in result["adjustments"]
        assert "buyer->seller" in result["adjustments"]
        assert "seller->buyer" in result["adjustments"]
        assert mock_handoff_service.get_learned_adjustments.call_count == 4

    @pytest.mark.asyncio
    async def test_marks_effective_when_sufficient_samples(self, manager, mock_handoff_service):
        mock_handoff_service.get_learned_adjustments.return_value = {
            "adjustment": -0.05, "success_rate": 0.85, "sample_size": 20,
        }
        result = await manager.run_threshold_adjustment_loop()

        for route in result["adjustments"].values():
            assert route["effective"] is True

    @pytest.mark.asyncio
    async def test_marks_not_effective_when_insufficient_samples(self, manager, mock_handoff_service):
        mock_handoff_service.get_learned_adjustments.return_value = {
            "adjustment": 0.0, "success_rate": 0.0, "sample_size": 5,
        }
        result = await manager.run_threshold_adjustment_loop()

        for route in result["adjustments"].values():
            assert route["effective"] is False

    @pytest.mark.asyncio
    async def test_skips_when_no_handoff_service(self):
        mgr = FeedbackLoopManager()
        result = await mgr.run_threshold_adjustment_loop()
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_increments_loop_stats(self, manager):
        await manager.run_threshold_adjustment_loop()
        await manager.run_threshold_adjustment_loop()

        stats = manager.get_loop_stats()
        assert stats["threshold_adjustment"]["runs"] == 2
        assert stats["threshold_adjustment"]["last_run"] > 0


# ── Loop 2: Abandonment Recovery ────────────────────────────────────


class TestLoop2AbandonmentRecovery:
    """Loop 2: Abandonment detection -> recovery trigger."""

    @pytest.mark.asyncio
    async def test_detects_silent_contact(self, manager):
        old_time = time.time() - ABANDONMENT_SILENCE_SECONDS - 60
        manager.report_handoff_activity("c1", "lead", "buyer", old_time)

        result = await manager.run_abandonment_recovery_loop()

        assert result["detected"] == 1
        assert result["recoveries"][0]["contact_id"] == "c1"
        assert result["recoveries"][0]["action"] == "nudge"

    @pytest.mark.asyncio
    async def test_no_recovery_if_contact_active(self, manager):
        manager.report_handoff_activity("c1", "lead", "buyer", time.time())
        manager.report_contact_activity("c1")

        result = await manager.run_abandonment_recovery_loop()
        assert result["detected"] == 0

    @pytest.mark.asyncio
    async def test_nudge_then_revert(self, manager):
        old_time = time.time() - ABANDONMENT_SILENCE_SECONDS - 60
        manager.report_handoff_activity("c1", "lead", "buyer", old_time)

        # First run: nudge
        r1 = await manager.run_abandonment_recovery_loop()
        assert r1["recoveries"][0]["action"] == "nudge"

        # Second run: revert (still silent)
        r2 = await manager.run_abandonment_recovery_loop()
        assert r2["recoveries"][0]["action"] == "revert"
        assert r2["recoveries"][0]["target_bot"] == "lead"  # reverts to source

    @pytest.mark.asyncio
    async def test_max_recovery_attempts(self, manager):
        old_time = time.time() - ABANDONMENT_SILENCE_SECONDS - 60
        manager.report_handoff_activity("c1", "lead", "buyer", old_time)

        # Exhaust recovery attempts
        for _ in range(RECOVERY_MAX_ATTEMPTS):
            await manager.run_abandonment_recovery_loop()

        # No more recoveries
        r = await manager.run_abandonment_recovery_loop()
        assert r["detected"] == 0

    @pytest.mark.asyncio
    async def test_old_records_cleaned_up(self, manager):
        very_old = time.time() - 7200  # 2 hours ago
        manager.report_handoff_activity("c_old", "lead", "buyer", very_old)

        result = await manager.run_abandonment_recovery_loop()
        assert "c_old" not in manager._abandonment_records

    @pytest.mark.asyncio
    async def test_loop_stats_tracked(self, manager):
        old_time = time.time() - ABANDONMENT_SILENCE_SECONDS - 60
        manager.report_handoff_activity("c1", "lead", "buyer", old_time)

        await manager.run_abandonment_recovery_loop()

        stats = manager.get_loop_stats()
        assert stats["abandonment_recovery"]["runs"] == 1
        assert stats["abandonment_recovery"]["recoveries"] == 1


# ── Loop 3: A/B Test Promotion ──────────────────────────────────────


class TestLoop3ABTestPromotion:
    """Loop 3: A/B test result -> strategy selection."""

    @pytest.mark.asyncio
    async def test_no_candidates_no_promotions(self, manager, mock_ab_testing):
        mock_ab_testing.get_promotion_candidates.return_value = []

        result = await manager.run_ab_test_promotion_loop()
        assert result["candidates_found"] == 0
        assert result["promoted"] == []

    @pytest.mark.asyncio
    async def test_promotes_winning_variant(self, manager, mock_ab_testing):
        mock_ab_testing.get_promotion_candidates.return_value = [
            {
                "experiment_id": "greeting_style",
                "winning_variant": "empathetic",
                "control_variant": "formal",
                "p_value": 0.02,
                "lift_percent": 15.5,
                "sample_size": 500,
                "runtime_days": 7.0,
                "winner_conversion_rate": 0.35,
                "control_conversion_rate": 0.30,
            }
        ]

        result = await manager.run_ab_test_promotion_loop()

        assert result["candidates_found"] == 1
        assert len(result["promoted"]) == 1
        assert result["promoted"][0]["winning_variant"] == "empathetic"
        assert result["promoted"][0]["auto_deactivated"] is True
        mock_ab_testing.deactivate_experiment.assert_called_once_with("greeting_style")

    @pytest.mark.asyncio
    async def test_skip_deactivation_when_disabled(self, manager, mock_ab_testing):
        mock_ab_testing.get_promotion_candidates.return_value = [
            {
                "experiment_id": "test_exp",
                "winning_variant": "a",
                "control_variant": "b",
                "p_value": 0.01,
                "lift_percent": 20.0,
                "sample_size": 1000,
                "runtime_days": 10.0,
                "winner_conversion_rate": 0.4,
                "control_conversion_rate": 0.33,
            }
        ]

        result = await manager.run_ab_test_promotion_loop(auto_deactivate=False)

        assert result["promoted"][0]["auto_deactivated"] is False
        mock_ab_testing.deactivate_experiment.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_when_no_ab_service(self):
        mgr = FeedbackLoopManager()
        result = await mgr.run_ab_test_promotion_loop()
        assert result["status"] == "skipped"


# ── Loop 4: Alert Escalation ────────────────────────────────────────


class TestLoop4AlertEscalation:
    """Loop 4: Alert firing -> escalation action."""

    @pytest.mark.asyncio
    async def test_no_escalations_when_no_alerts(self, manager, mock_alerting):
        mock_alerting.check_escalations.return_value = []

        result = await manager.run_alert_escalation_loop()
        assert result["total_escalated"] == 0

    @pytest.mark.asyncio
    async def test_escalates_unacknowledged_critical(self, manager, mock_alerting):
        mock_alert = MagicMock()
        mock_alert.id = "abc123"
        mock_alert.rule_name = "sla_violation"
        mock_alert.severity = "critical"
        mock_alert.triggered_at = time.time() - 600  # 10 min ago

        mock_level = MagicMock()
        mock_level.level = 2
        mock_level.channels = ["email", "slack"]
        mock_level.description = "5min unack: all channels"

        mock_alerting.check_escalations.return_value = [(mock_alert, mock_level)]

        result = await manager.run_alert_escalation_loop()

        assert result["total_escalated"] == 1
        assert result["escalations"][0]["alert_id"] == "abc123"
        assert result["escalations"][0]["escalation_level"] == 2

    @pytest.mark.asyncio
    async def test_skips_when_no_alerting_service(self):
        mgr = FeedbackLoopManager()
        result = await mgr.run_alert_escalation_loop()
        assert result["status"] == "skipped"


# ── Loop 5: Routing Weight Adjustment ───────────────────────────────


class TestLoop5RoutingWeights:
    """Loop 5: Performance metric -> routing weight adjustment."""

    @pytest.mark.asyncio
    async def test_healthy_bot_weight_recovers(self, manager, mock_perf_tracker):
        # Healthy stats: P95 well under SLA, high success rate
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 200.0, "p95": 800.0, "p99": 1200.0,
            "mean": 300.0, "min": 50.0, "max": 1500.0,
            "count": 100, "success_count": 98, "error_count": 2,
            "cache_hit_count": 60, "cache_hit_rate": 0.6, "success_rate": 0.98,
        }

        # Set initial weight below max
        manager._routing_weights.weights["lead_bot"] = 0.8

        result = await manager.run_routing_weight_loop()

        assert result["status"] == "ok"
        assert manager.get_routing_weight("lead_bot") == 0.85  # 0.8 + 0.05

    @pytest.mark.asyncio
    async def test_sla_breach_reduces_weight(self, manager, mock_perf_tracker):
        # SLA breach: P95 > 1500ms (lead_bot process target)
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 800.0, "p95": 2200.0, "p99": 3000.0,
            "mean": 1000.0, "min": 200.0, "max": 3500.0,
            "count": 100, "success_count": 90, "error_count": 10,
            "cache_hit_count": 30, "cache_hit_rate": 0.3, "success_rate": 0.90,
        }

        result = await manager.run_routing_weight_loop()

        # Weight should decrease
        for adj in result["adjustments"]:
            assert adj["reason"] == "sla_breach"
            assert adj["new_weight"] < adj["old_weight"]

    @pytest.mark.asyncio
    async def test_weight_clamped_to_min(self, manager, mock_perf_tracker):
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 800.0, "p95": 2200.0, "p99": 3000.0,
            "mean": 1000.0, "min": 200.0, "max": 3500.0,
            "count": 100, "success_count": 90, "error_count": 10,
            "cache_hit_count": 30, "cache_hit_rate": 0.3, "success_rate": 0.90,
        }

        # Set weight already at min
        manager._routing_weights.weights["lead_bot"] = MIN_ROUTING_WEIGHT

        result = await manager.run_routing_weight_loop()

        assert manager.get_routing_weight("lead_bot") == MIN_ROUTING_WEIGHT

    @pytest.mark.asyncio
    async def test_weight_clamped_to_max(self, manager, mock_perf_tracker):
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 200.0, "p95": 800.0, "p99": 1200.0,
            "mean": 300.0, "min": 50.0, "max": 1500.0,
            "count": 100, "success_count": 98, "error_count": 2,
            "cache_hit_count": 60, "cache_hit_rate": 0.6, "success_rate": 0.98,
        }

        # Weight already at max
        manager._routing_weights.weights["lead_bot"] = MAX_ROUTING_WEIGHT

        result = await manager.run_routing_weight_loop()
        assert manager.get_routing_weight("lead_bot") == MAX_ROUTING_WEIGHT

    @pytest.mark.asyncio
    async def test_no_data_no_adjustment(self, manager, mock_perf_tracker):
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 0.0, "p95": 0.0, "p99": 0.0,
            "mean": 0.0, "min": 0.0, "max": 0.0,
            "count": 0, "success_count": 0, "error_count": 0,
            "cache_hit_count": 0, "cache_hit_rate": 0.0, "success_rate": 0.0,
        }

        result = await manager.run_routing_weight_loop()
        assert result["adjustments"] == []

    @pytest.mark.asyncio
    async def test_skips_when_no_perf_tracker(self):
        mgr = FeedbackLoopManager()
        result = await mgr.run_routing_weight_loop()
        assert result["status"] == "skipped"

    @pytest.mark.asyncio
    async def test_low_success_rate_reduces_weight(self, manager, mock_perf_tracker):
        # Success rate < 90% even if P95 is within SLA
        mock_perf_tracker.get_bot_stats.return_value = {
            "p50": 200.0, "p95": 800.0, "p99": 1200.0,
            "mean": 300.0, "min": 50.0, "max": 1500.0,
            "count": 100, "success_count": 80, "error_count": 20,
            "cache_hit_count": 60, "cache_hit_rate": 0.6, "success_rate": 0.80,
        }

        result = await manager.run_routing_weight_loop()

        for adj in result["adjustments"]:
            assert adj["reason"] == "sla_breach"


# ── Run All Loops ───────────────────────────────────────────────────


class TestRunAllLoops:
    """Test the combined run_all_loops method."""

    @pytest.mark.asyncio
    async def test_runs_all_5_loops(self, manager):
        result = await manager.run_all_loops()

        assert "loop_1_threshold_adjustment" in result
        assert "loop_2_abandonment_recovery" in result
        assert "loop_3_ab_test_promotion" in result
        assert "loop_4_alert_escalation" in result
        assert "loop_5_routing_weights" in result

        # All should have status "ok"
        for key in result:
            assert result[key]["status"] == "ok"

    @pytest.mark.asyncio
    async def test_all_loops_skipped_when_no_services(self):
        mgr = FeedbackLoopManager()
        result = await mgr.run_all_loops()

        assert result["loop_1_threshold_adjustment"]["status"] == "skipped"
        # Loop 2 always runs (doesn't require external service)
        assert result["loop_2_abandonment_recovery"]["status"] == "ok"
        assert result["loop_3_ab_test_promotion"]["status"] == "skipped"
        assert result["loop_4_alert_escalation"]["status"] == "skipped"
        assert result["loop_5_routing_weights"]["status"] == "skipped"
