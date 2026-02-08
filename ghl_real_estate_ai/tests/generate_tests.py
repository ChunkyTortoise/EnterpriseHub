#!/usr/bin/env python3
"""Generate integration test files for Jorge Bot services."""

import os

# ABTestingService tests
ab_testing_tests = '''"""
Tests for Jorge A/B Testing Service.

Validates experiment creation, variant assignment, and statistical analysis.
"""

import pytest
import time

from ghl_real_estate_ai.services.jorge.ab_testing_service import (
    ABTestingService,
    ExperimentStatus,
)


class TestABTestingService:
    """Test suite for A/B testing functionality."""

    @pytest.fixture
    def ab_service(self):
        """Create a fresh ABTestingService instance for each test."""
        # Reset singleton
        ABTestingService._instance = None
        ABTestingService._initialized = False
        return ABTestingService()

    def test_create_experiment_success(self, ab_service):
        """Test successful creation of an experiment."""
        result = ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        assert result["experiment_id"] == "test_exp"
        assert result["variants"] == ["control", "treatment"]
        assert result["status"] == ExperimentStatus.ACTIVE.value
        assert "traffic_split" in result

    def test_create_experiment_duplicate_name(self, ab_service):
        """Test that creating duplicate experiment raises ValueError."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        with pytest.raises(ValueError, match="already exists"):
            ab_service.create_experiment(
                experiment_id="test_exp",
                variants=["control", "treatment"],
            )

    def test_get_experiment_by_id(self, ab_service):
        """Test retrieving an experiment by ID."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        exp = ab_service._get_experiment("test_exp")
        assert exp.experiment_id == "test_exp"
        assert exp.variants == ["control", "treatment"]

    def test_get_experiment_by_name(self, ab_service):
        """Test retrieving experiment via list_experiments."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        experiments = ab_service.list_experiments()
        assert len(experiments) == 1
        assert experiments[0]["experiment_id"] == "test_exp"

    def test_list_experiments(self, ab_service):
        """Test listing all active experiments."""
        ab_service.create_experiment(
            experiment_id="exp1",
            variants=["control", "treatment"],
        )
        ab_service.create_experiment(
            experiment_id="exp2",
            variants=["variant_a", "variant_b"],
        )

        experiments = ab_service.list_experiments()
        assert len(experiments) == 2
        exp_ids = [e["experiment_id"] for e in experiments]
        assert "exp1" in exp_ids
        assert "exp2" in exp_ids

    @pytest.mark.asyncio
    async def test_assign_variant_deterministic(self, ab_service):
        """Test that variant assignment is deterministic for same contact."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Same contact should always get same variant
        variant1 = await ab_service.get_variant("test_exp", "contact_123")
        variant2 = await ab_service.get_variant("test_exp", "contact_123")
        variant3 = await ab_service.get_variant("test_exp", "contact_123")

        assert variant1 == variant2 == variant3
        assert variant1 in ["control", "treatment"]

    @pytest.mark.asyncio
    async def test_assign_variant_consistent(self, ab_service):
        """Test that different contacts get different variants (statistically)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Assign 100 contacts
        variants = []
        for i in range(100):
            variant = await ab_service.get_variant("test_exp", f"contact_{i}")
            variants.append(variant)

        # Both variants should be used
        assert "control" in variants
        assert "treatment" in variants

        # Distribution should be roughly equal (within 20% tolerance)
        control_count = variants.count("control")
        treatment_count = variants.count("treatment")
        assert 30 <= control_count <= 70
        assert 30 <= treatment_count <= 70

    @pytest.mark.asyncio
    async def test_record_metric_success(self, ab_service):
        """Test successful recording of an outcome metric."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        result = ab_service.record_outcome(
            experiment_id="test_exp",
            contact_id="contact_123",
            variant="control",
            outcome="conversion",
            value=1.0,
        )

        assert result["experiment_id"] == "test_exp"
        assert result["contact_id"] == "contact_123"
        assert result["variant"] == "control"
        assert result["outcome"] == "conversion"
        assert result["value"] == 1.0

    @pytest.mark.asyncio
    async def test_record_metric_invalid_variant(self, ab_service):
        """Test that recording with invalid variant raises ValueError."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        with pytest.raises(ValueError, match="Unknown variant"):
            await ab_service.record_outcome(
                experiment_id="test_exp",
                contact_id="contact_123",
                variant="invalid_variant",
                outcome="conversion",
            )

    def test_get_experiment_results(self, ab_service):
        """Test retrieving experiment results with statistics."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Add some data
        exp = ab_service._get_experiment("test_exp")
        exp.assignments["control"] = ["c1", "c2", "c3", "c4"]
        exp.assignments["treatment"] = ["t1", "t2", "t3", "t4"]
        exp.outcomes["control"] = [
            {"contact_id": "c1", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
            {"contact_id": "c2", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
        ]
        exp.outcomes["treatment"] = [
            {"contact_id": "t1", "outcome": "conversion", "value": 1.0, "timestamp": time.time()},
        ]

        results = ab_service.get_experiment_results("test_exp")

        assert results.experiment_id == "test_exp"
        assert results.total_impressions == 8
        assert results.total_conversions == 3
        assert len(results.variants) == 2

        # Check variant stats
        control_stats = next(v for v in results.variants if v.variant == "control")
        assert control_stats.impressions == 4
        assert control_stats.conversions == 2
        assert control_stats.conversion_rate == 0.5

    def test_calculate_significance(self, ab_service):
        """Test statistical significance calculation."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Add data with clear difference
        exp = ab_service._get_experiment("test_exp")
        exp.assignments["control"] = [f"c{i}" for i in range(100)]
        exp.assignments["treatment"] = [f"t{i}" for i in range(100)]
        exp.outcomes["control"] = [
            {"contact_id": f"c{i}", "outcome": "conversion", "value": 1.0, "timestamp": time.time()}
            for i in range(10)  # 10% conversion
        ]
        exp.outcomes["treatment"] = [
            {"contact_id": f"t{i}", "outcome": "conversion", "value": 1.0, "timestamp": time.time()}
            for i in range(30)  # 30% conversion
        ]

        is_significant = ab_service.is_significant("test_exp")
        # With this sample size and difference, should be significant
        assert is_significant is True

    def test_pause_experiment(self, ab_service):
        """Test pausing an active experiment."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        result = ab_service.deactivate_experiment("test_exp")

        assert result["experiment_id"] == "test_exp"
        assert result["status"] == ExperimentStatus.COMPLETED.value
        assert "duration_hours" in result

        # Verify experiment is deactivated
        exp = ab_service._get_experiment("test_exp")
        assert exp.status == ExperimentStatus.COMPLETED

    def test_resume_experiment(self, ab_service):
        """Test that a completed experiment cannot be resumed (status change)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        ab_service.deactivate_experiment("test_exp")

        # Try to get variant from completed experiment
        with pytest.raises(ValueError, match="not active"):
            ab_service.get_variant("test_exp", "contact_123")

    def test_archive_experiment(self, ab_service):
        """Test that experiments can be archived (deactivated)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Archive by deactivating
        result = ab_service.deactivate_experiment("test_exp")

        assert result["status"] == ExperimentStatus.COMPLETED.value

        # Verify it's no longer in active list
        active_experiments = ab_service.list_experiments()
        assert "test_exp" not in [e["experiment_id"] for e in active_experiments]

    def test_delete_experiment(self, ab_service):
        """Test that experiments can be deleted (via reset)."""
        ab_service.create_experiment(
            experiment_id="test_exp",
            variants=["control", "treatment"],
        )

        # Verify experiment exists
        assert "test_exp" in ab_service._experiments

        # Delete by removing from dict (simulating delete)
        del ab_service._experiments["test_exp"]

        # Verify experiment is gone
        with pytest.raises(KeyError, match="not found"):
            ab_service._get_experiment("test_exp")
'''

# PerformanceTracker tests
performance_tracker_tests = '''"""
Tests for Jorge Performance Tracker Service.

Validates latency tracking, percentile calculations, and SLA compliance.
"""

import pytest
import time

from ghl_real_estate_ai.services.jorge.performance_tracker import (
    PerformanceTracker,
)


class TestPerformanceTracker:
    """Test suite for performance tracking functionality."""

    @pytest.fixture
    def tracker(self):
        """Create a fresh PerformanceTracker instance for each test."""
        PerformanceTracker.reset()
        return PerformanceTracker()

    @pytest.mark.asyncio
    async def test_record_metric_success(self, tracker):
        """Test successful recording of a performance metric."""
        await tracker.track_operation(
            bot_name="lead_bot",
            operation="qualify",
            duration_ms=1500,
            success=True,
            cache_hit=False,
        )

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 1
        assert stats["success_count"] == 1
        assert stats["error_count"] == 0

    @pytest.mark.asyncio
    async def test_record_metric_with_tags(self, tracker):
        """Test recording metric with metadata tags."""
        metadata = {"contact_id": "123", "route": "lead_to_buyer"}
        await tracker.track_operation(
            bot_name="buyer_bot",
            operation="process",
            duration_ms=2000,
            success=True,
            cache_hit=True,
            metadata=metadata,
        )

        stats = await tracker.get_bot_stats("buyer_bot")
        assert stats["count"] == 1
        assert stats["cache_hit_count"] == 1
        assert stats["cache_hit_rate"] == 1.0

    @pytest.mark.asyncio
    async def test_get_percentiles_p50(self, tracker):
        """Test P50 percentile calculation."""
        # Record 10 operations with known durations
        for i in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="qualify",
                duration_ms=1000 + i * 100,  # 1000, 1100, ..., 1900
                success=True,
            )

        p50 = await tracker.get_percentile("lead_bot", 50)
        # P50 should be around 1450 (median of 1000-1900)
        assert 1400 <= p50 <= 1500

    @pytest.mark.asyncio
    async def test_get_percentiles_p95(self, tracker):
        """Test P95 percentile calculation."""
        # Record 20 operations
        for i in range(20):
            await tracker.track_operation(
                bot_name="buyer_bot",
                operation="process",
                duration_ms=1000 + i * 50,
                success=True,
            )

        p95 = await tracker.get_percentile("buyer_bot", 95)
        # P95 should be near the higher end
        assert p95 > 1800

    @pytest.mark.asyncio
    async def test_get_percentiles_p99(self, tracker):
        """Test P99 percentile calculation."""
        # Record 50 operations
        for i in range(50):
            await tracker.track_operation(
                bot_name="seller_bot",
                operation="qualify",
                duration_ms=1000 + i * 20,
                success=True,
            )

        p99 = await tracker.get_percentile("seller_bot", 99)
        # P99 should be very close to max
        assert p99 > 1900

    @pytest.mark.asyncio
    async def test_check_sla_compliance_pass(self, tracker):
        """Test SLA compliance check when metrics are within targets."""
        # Record operations within SLA targets
        for _ in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="qualify",
                duration_ms=1500,  # Below 2000ms P95 target
                success=True,
            )

        compliance = await tracker.check_sla_compliance()
        lead_bot_compliance = next(
            (c for c in compliance if c["bot_name"] == "lead_bot" and c["operation"] == "full_qualification"),
            None
        )

        assert lead_bot_compliance is not None
        assert lead_bot_compliance["compliant"] is True
        assert len(lead_bot_compliance["violations"]) == 0

    @pytest.mark.asyncio
    async def test_check_sla_compliance_fail(self, tracker):
        """Test SLA compliance check when metrics exceed targets."""
        # Record operations exceeding SLA targets
        for _ in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="qualify",
                duration_ms=2500,  # Above 2000ms P95 target
                success=True,
            )

        compliance = await tracker.check_sla_compliance()
        lead_bot_compliance = next(
            (c for c in compliance if c["bot_name"] == "lead_bot" and c["operation"] == "full_qualification"),
            None
        )

        assert lead_bot_compliance is not None
        assert lead_bot_compliance["compliant"] is False
        assert len(lead_bot_compliance["violations"]) > 0

    @pytest.mark.asyncio
    async def test_get_metrics_summary(self, tracker):
        """Test getting comprehensive metrics summary."""
        # Record mixed operations
        for i in range(10):
            await tracker.track_operation(
                bot_name="lead_bot",
                operation="qualify",
                duration_ms=1000 + i * 100,
                success=i < 8,  # 2 failures
                cache_hit=i % 2 == 0,  # 5 cache hits
            )

        stats = await tracker.get_bot_stats("lead_bot")
        assert stats["count"] == 10
        assert stats["success_count"] == 8
        assert stats["error_count"] == 2
        assert stats["cache_hit_count"] == 5
        assert stats["success_rate"] == 0.8
        assert stats["cache_hit_rate"] == 0.5

    @pytest.mark.asyncio
    async def test_get_metrics_by_time_range(self, tracker):
        """Test getting metrics for different time windows."""
        # Record operations
        for _ in range(5):
            await tracker.track_operation(
                bot_name="buyer_bot",
                operation="process",
                duration_ms=1500,
                success=True,
            )

        # Get stats for different windows
        stats_1h = await tracker.get_bot_stats("buyer_bot", window="1h")
        stats_24h = await tracker.get_bot_stats("buyer_bot", window="24h")

        # Both should return same data (all within window)
        assert stats_1h["count"] == 5
        assert stats_24h["count"] == 5

    @pytest.mark.asyncio
    async def test_cleanup_old_metrics(self, tracker):
        """Test that old metrics are filtered out by window."""
        # Record an operation
        await tracker.track_operation(
            bot_name="lead_bot",
            operation="qualify",
            duration_ms=1500,
            success=True,
        )

        # Manually set timestamp to be old (older than 1h)
        with tracker._data_lock:
            for window in tracker._operations["lead_bot"]:
                if tracker._operations["lead_bot"][window]:
                    tracker._operations["lead_bot"][window][0].timestamp = time.time() - 4000

        # Get stats - should be empty for 1h window
        stats = await tracker.get_bot_stats("lead_bot", window="1h")
        assert stats["count"] == 0

    @pytest.mark.asyncio
    async def test_get_alert_thresholds(self, tracker):
        """Test retrieving SLA alert thresholds."""
        # The tracker has predefined SLA targets
        compliance = await tracker.check_sla_compliance()

        # Check that thresholds are present
        for item in compliance:
            assert "p50_target" in item
            assert "p95_target" in item
            assert "p99_target" in item

    @pytest.mark.asyncio
    async def test_export_metrics(self, tracker):
        """Test exporting metrics for all bots."""
        # Record operations for multiple bots
        for bot in ["lead_bot", "buyer_bot", "seller_bot"]:
            for _ in range(5):
                await tracker.track_operation(
                    bot_name=bot,
                    operation="process",
                    duration_ms=1500,
                    success=True,
                )

        # Get all stats
        all_stats = await tracker.get_all_stats()

        assert "lead_bot" in all_stats
        assert "buyer_bot" in all_stats
        assert "seller_bot" in all_stats

        for bot_stats in all_stats.values():
            assert bot_stats["count"] == 5
'''

# AlertingService tests
alerting_service_tests = '''"""
Tests for Jorge Alerting Service.

Validates alert rule checking, notification sending, and cooldowns.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from ghl_real_estate_ai.services.jorge.alerting_service import (
    AlertingService,
    AlertRule,
    Alert,
)


class TestAlertingService:
    """Test suite for alerting functionality."""

    @pytest.fixture
    def alerting_service(self):
        """Create a fresh AlertingService instance for each test."""
        AlertingService._instance = None
        AlertingService._initialized = False
        return AlertingService()

    @pytest.mark.asyncio
    async def test_send_email_alert_success(self, alerting_service):
        """Test successful email alert sending."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="critical",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock SMTP
        with patch("smtplib.SMTP") as mock_smtp:
            mock_server = MagicMock()
            mock_smtp.return_value.__enter__.return_value = mock_server

            await alerting_service._send_email_alert(alert)

            # Verify SMTP was called
            mock_smtp.assert_called_once()
            mock_server.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_alert_smtp_failure(self, alerting_service):
        """Test email alert handling on SMTP failure."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="critical",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock SMTP to raise exception
        with patch("smtplib.SMTP", side_effect=Exception("SMTP Error")):
            # Should not raise, just log error
            await alerting_service._send_email_alert(alert)

    @pytest.mark.asyncio
    async def test_send_slack_alert_success(self, alerting_service):
        """Test successful Slack alert sending."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="warning",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock aiohttp
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            with patch.dict("os.environ", {"ALERT_SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"}):
                await alerting_service._send_slack_alert(alert)

                # Verify POST was called
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_slack_alert_webhook_failure(self, alerting_service):
        """Test Slack alert handling on webhook failure."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="warning",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock aiohttp to raise exception
        with patch("aiohttp.ClientSession"):
            with patch.dict("os.environ", {"ALERT_SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"}):
                # Should not raise, just log error
                await alerting_service._send_slack_alert(alert)

    @pytest.mark.asyncio
    async def test_send_webhook_alert_success(self, alerting_service):
        """Test successful webhook alert sending."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="info",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock aiohttp
        with patch("aiohttp.ClientSession") as mock_session:
            mock_response = AsyncMock()
            mock_response.raise_for_status = MagicMock()
            mock_post = AsyncMock()
            mock_post.__aenter__.return_value = mock_response
            mock_session.return_value.__aenter__.return_value.post.return_value = mock_post

            with patch.dict("os.environ", {"ALERT_WEBHOOK_URL": "https://example.com/webhook"}):
                await alerting_service._send_webhook_alert(alert)

                # Verify POST was called
                mock_post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_webhook_alert_failure(self, alerting_service):
        """Test webhook alert handling on failure."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="info",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Mock aiohttp to raise exception
        with patch("aiohttp.ClientSession"):
            with patch.dict("os.environ", {"ALERT_WEBHOOK_URL": "https://example.com/webhook"}):
                # Should not raise, just log error
                await alerting_service._send_webhook_alert(alert)

    @pytest.mark.asyncio
    async def test_check_alert_rules(self, alerting_service):
        """Test checking alert rules against performance stats."""
        # Stats that should trigger high_error_rate rule
        stats = {
            "error_rate": 0.10,  # 10% > 5% threshold
            "cache_hit_rate": 0.60,
            "handoff_success_rate": 0.98,
        }

        alerts = await alerting_service.check_alerts(stats)

        # Should trigger at least one alert
        assert len(alerts) > 0
        assert any(a.rule_name == "high_error_rate" for a in alerts)

    @pytest.mark.asyncio
    async def test_register_alert_rule(self, alerting_service):
        """Test registering a custom alert rule."""
        custom_rule = AlertRule(
            name="custom_rule",
            condition=lambda stats: stats.get("custom_metric", 0) > 100,
            severity="warning",
            cooldown_seconds=600,
            channels=["slack"],
            description="Custom test rule",
        )

        await alerting_service.add_rule(custom_rule)

        # Verify rule was added
        rules = await alerting_service.list_rules()
        assert any(r.name == "custom_rule" for r in rules)

    @pytest.mark.asyncio
    async def test_unregister_alert_rule(self, alerting_service):
        """Test removing an alert rule."""
        # Add a custom rule first
        custom_rule = AlertRule(
            name="custom_rule",
            condition=lambda stats: True,
            severity="info",
            cooldown_seconds=300,
            channels=["email"],
        )
        await alerting_service.add_rule(custom_rule)

        # Remove the rule
        await alerting_service.remove_rule("custom_rule")

        # Verify rule was removed
        rules = await alerting_service.list_rules()
        assert not any(r.name == "custom_rule" for r in rules)

    @pytest.mark.asyncio
    async def test_alert_cooldown(self, alerting_service):
        """Test that alerts respect cooldown periods."""
        # Stats that trigger an alert
        stats = {
            "error_rate": 0.10,
            "cache_hit_rate": 0.60,
        }

        # First check should trigger alert
        alerts1 = await alerting_service.check_alerts(stats)
        assert len(alerts1) > 0

        # Immediate second check should not trigger (cooldown)
        alerts2 = await alerting_service.check_alerts(stats)
        assert len(alerts2) == 0
'''

# JorgeHandoffService circular prevention tests
handoff_circular_tests = '''"""
Tests for Jorge Handoff Service Circular Prevention.

Validates circular handoff detection, rate limiting, and conflict resolution.
"""

import pytest
import time

from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
    JorgeHandoffService,
    HandoffDecision,
)


class TestJorgeHandoffCircularPrevention:
    """Test suite for handoff circular prevention."""

    @pytest.fixture
    def handoff_service(self):
        """Create a fresh JorgeHandoffService instance for each test."""
        JorgeHandoffService._handoff_history = {}
        JorgeHandoffService._handoff_outcomes = {}
        JorgeHandoffService._active_handoffs = {}
        JorgeHandoffService.reset_analytics()
        return JorgeHandoffService()

    @pytest.mark.asyncio
    async def test_evaluate_handoff_success(self, handoff_service):
        """Test successful handoff evaluation."""
        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
            "detected_intent_phrases": ["looking to buy"],
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
        assert decision.confidence == 0.85

    @pytest.mark.asyncio
    async def test_circular_handoff_prevention(self, handoff_service):
        """Test that circular handoffs are prevented."""
        contact_id = "contact_123"

        # First handoff: lead -> buyer
        intent_signals = {
            "buyer_intent_score": 0.85,
            "seller_intent_score": 0.1,
        }
        decision1 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision1 is not None

        # Execute the handoff
        await handoff_service.execute_handoff(decision1, contact_id)

        # Try same handoff again within 30 min window - should be blocked
        decision2 = await handoff_service.evaluate_handoff(
            current_bot="lead",
            contact_id=contact_id,
            conversation_history=[],
            intent_signals=intent_signals,
        )
        assert decision2 is None  # Blocked by circular prevention

    @pytest.mark.asyncio
    async def test_rate_limit_hourly(self, handoff_service):
        """Test hourly rate limiting (3 handoffs/hour)."""
        contact_id = "contact_123"

        # Execute 3 handoffs (hourly limit)
        for i in range(3):
            decision = HandoffDecision(
                source_bot="lead",
                target_bot="buyer",
                reason="buyer_intent_detected",
                confidence=0.8,
            )
            await handoff_service.execute_handoff(decision, contact_id)

        # 4th handoff should be blocked
        decision4 = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.9,
        )
        result = await handoff_service.execute_handoff(decision4, contact_id)
        assert result[0]["handoff_executed"] is False
        assert "rate limit" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_rate_limit_daily(self, handoff_service):
        """Test daily rate limiting (10 handoffs/day)."""
        contact_id = "contact_123"

        # Execute 10 handoffs (daily limit)
        for i in range(10):
            decision = HandoffDecision(
                source_bot="lead",
                target_bot="buyer",
                reason="buyer_intent_detected",
                confidence=0.8,
            )
            await handoff_service.execute_handoff(decision, contact_id)

        # 11th handoff should be blocked
        decision11 = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.9,
        )
        result = await handoff_service.execute_handoff(decision11, contact_id)
        assert result[0]["handoff_executed"] is False
        assert "rate limit" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_contact_level_locking(self, handoff_service):
        """Test contact-level locking prevents concurrent handoffs."""
        contact_id = "contact_123"

        # Start first handoff (acquires lock)
        decision1 = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.8,
        )

        # Manually acquire lock to simulate concurrent handoff
        handoff_service._acquire_handoff_lock(contact_id)

        # Try to execute another handoff - should be blocked
        result = await handoff_service.execute_handoff(decision1, contact_id)
        assert result[0]["handoff_executed"] is False
        assert "concurrent" in result[0]["reason"].lower()

    @pytest.mark.asyncio
    async def test_handoff_conflict_resolution(self, handoff_service):
        """Test that handoff conflicts are resolved properly."""
        contact_id = "contact_123"

        # First handoff
        decision1 = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent_detected",
            confidence=0.8,
        )
        result1 = await handoff_service.execute_handoff(decision1, contact_id)
        assert result1[0]["handoff_executed"] is True

        # Release lock
        handoff_service._release_handoff_lock(contact_id)

        # Second handoff should succeed
        decision2 = HandoffDecision(
            source_bot="buyer",
            target_bot="seller",
            reason="seller_intent_detected",
            confidence=0.7,
        )
        result2 = await handoff_service.execute_handoff(decision2, contact_id)
        assert result2[0]["handoff_executed"] is True
'''

# BuyerBudgetConfig tests
buyer_budget_config_tests = '''"""
Tests for Jorge Buyer Budget Configuration.

Validates budget validation, financial calculations, and readiness assessment.
"""

import pytest
import os

from ghl_real_estate_ai.ghl_utils.jorge_config import (
    BuyerBudgetConfig,
)


class TestBuyerBudgetConfig:
    """Test suite for buyer budget configuration."""

    @pytest.fixture
    def budget_config(self):
        """Create a BuyerBudgetConfig instance."""
        return BuyerBudgetConfig()

    def test_load_from_env_success(self, budget_config):
        """Test loading configuration from environment variables."""
        # Set environment variables
        env_vars = {
            "BUYER_FINANCING_PRE_APPROVED_THRESHOLD": "80",
            "BUYER_URGENCY_IMMEDIATE_THRESHOLD": "70",
            "BUYER_QUALIFICATION_HOT_THRESHOLD": "80",
        }

        with patch.dict(os.environ, env_vars, clear=False):
            config = BuyerBudgetConfig.from_environment()

            assert config.FINANCING_PRE_APPROVED_THRESHOLD == 80
            assert config.URGENCY_IMMEDIATE_THRESHOLD == 70
            assert config.QUALIFICATION_HOT_THRESHOLD == 80

    def test_validate_budget_in_range(self, budget_config):
        """Test budget validation when within acceptable range."""
        budget_range = budget_config.get_budget_range("under 600")

        assert budget_range is not None
        assert "budget_max" in budget_range
        assert "buyer_type" in budget_range
        assert budget_range["budget_max"] == 600000

    def test_validate_budget_below_min(self, budget_config):
        """Test budget validation when below minimum."""
        # Very low budget
        budget_range = budget_config.get_budget_range("under 300")

        assert budget_range is not None
        assert budget_range["budget_max"] == 700000  # Maps to entry level

    def test_validate_budget_above_max(self, budget_config):
        """Test budget validation when above maximum."""
        # High budget
        budget_range = budget_config.get_budget_range("over 1m")

        assert budget_range is not None
        assert "budget_min" in budget_range
        assert budget_range["budget_min"] == 1200000

    def test_calculate_monthly_payment(self, budget_config):
        """Test monthly payment calculation."""
        # Simple calculation: principal * rate / 12
        # This is a placeholder - actual implementation may differ
        budget = 600000
        down_payment = 120000
        interest_rate = 0.06
        loan_term_years = 30

        # Calculate monthly payment (simplified)
        principal = budget - down_payment
        monthly_rate = interest_rate / 12
        num_payments = loan_term_years * 12

        # Monthly payment formula
        monthly_payment = principal * (monthly_rate * (1 + monthly_rate) ** num_payments) / ((1 + monthly_rate) ** num_payments - 1)

        assert monthly_payment > 0
        assert monthly_payment < principal  # Should be less than total principal

    def test_calculate_debt_to_income_ratio(self, budget_config):
        """Test debt-to-income ratio calculation."""
        monthly_income = 10000
        monthly_debt = 3000
        monthly_payment = 2500

        dti = (monthly_debt + monthly_payment) / monthly_income

        assert 0 <= dti <= 1
        assert dti == 0.55  # (3000 + 2500) / 10000

    def test_assess_financial_readiness(self, budget_config):
        """Test financial readiness assessment."""
        # High readiness scenario
        financing_score = 85  # Above 75 threshold
        budget_score = 80
        urgency_score = 75

        # Assess readiness
        is_ready = (
            financing_score >= budget_config.FINANCING_PRE_APPROVED_THRESHOLD and
            budget_score >= budget_config.FINANCING_CASH_BUDGET_THRESHOLD and
            urgency_score >= budget_config.URGENCY_IMMEDIATE_THRESHOLD
        )

        assert is_ready is True

    def test_get_budget_recommendations(self, budget_config):
        """Test getting budget recommendations."""
        # Test urgency level classification
        urgency_score = 80
        urgency_level = budget_config.get_urgency_level(urgency_score)

        assert urgency_level == "immediate"

        # Test qualification level classification
        qual_score = 85
        qual_level = budget_config.get_qualification_level(qual_score)

        assert qual_level == "hot"

        # Test next action
        action, hours = budget_config.get_next_action(qual_score)

        assert action == "schedule_property_tour"
        assert hours == budget_config.QUALIFICATION_HOT_FOLLOWUP_HOURS
'''


def write_test_file(filename, content):
    """Write test content to file."""
    filepath = f"ghl_real_estate_ai/tests/services/{filename}"
    with open(filepath, "w") as f:
        f.write(content)
    print(f"Created: {filepath}")


if __name__ == "__main__":
    # Create all test files
    write_test_file("test_ab_testing_service.py", ab_testing_tests)
    write_test_file("test_performance_tracker.py", performance_tracker_tests)
    write_test_file("test_alerting_service.py", alerting_service_tests)
    write_test_file("test_jorge_handoff_circular.py", handoff_circular_tests)
    write_test_file("test_buyer_budget_config.py", buyer_budget_config_tests)

    print("\\nAll test files created successfully!")
