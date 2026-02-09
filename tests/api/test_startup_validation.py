import pytest
pytestmark = pytest.mark.integration

"""Tests for Jorge Bot services startup validation and periodic alert stats.

Validates that _validate_jorge_services_config() correctly warns about
misconfigured environment variables without raising exceptions, and that
_build_alert_stats() produces the correct flat dict for AlertingService rules.
"""

import logging
import time

import pytest

from ghl_real_estate_ai.api.main import _build_alert_stats, _validate_jorge_services_config

@pytest.mark.integration


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch):
    """Clear all Jorge service env vars before each test."""
    for key in [
        "AB_TESTING_ENABLED",
        "PERFORMANCE_TRACKING_ENABLED",
        "PERFORMANCE_TRACKING_SAMPLE_RATE",
        "ALERT_EMAIL_ENABLED",
        "ALERT_EMAIL_SMTP_HOST",
        "ALERT_SMTP_HOST",
        "ALERT_EMAIL_TO",
        "ALERT_SLACK_ENABLED",
        "ALERT_SLACK_WEBHOOK_URL",
        "ALERT_WEBHOOK_ENABLED",
        "ALERT_WEBHOOK_URL",
        "BOT_METRICS_ENABLED",
        "BOT_METRICS_COLLECTION_INTERVAL",
    ]:
        monkeypatch.delenv(key, raising=False)


class TestABTestingValidation:
    def test_ab_testing_enabled_logs_info(self, monkeypatch, caplog):
        monkeypatch.setenv("AB_TESTING_ENABLED", "true")
        with caplog.at_level(logging.INFO):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "A/B testing is enabled" in caplog.text

    def test_ab_testing_disabled_no_log(self, monkeypatch, caplog):
        monkeypatch.setenv("AB_TESTING_ENABLED", "false")
        with caplog.at_level(logging.INFO):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "A/B testing is enabled" not in caplog.text


class TestPerformanceTrackingValidation:
    def test_valid_sample_rate_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "0.5")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "PERFORMANCE_TRACKING_SAMPLE_RATE" not in caplog.text

    def test_sample_rate_out_of_range_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "2.0")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "out of range" in caplog.text

    def test_sample_rate_negative_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "-0.5")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "out of range" in caplog.text

    def test_sample_rate_not_float_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "abc")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "not a valid float" in caplog.text

    def test_sample_rate_boundary_1_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "1.0")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "PERFORMANCE_TRACKING_SAMPLE_RATE" not in caplog.text

    def test_sample_rate_boundary_0_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "0.0")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "PERFORMANCE_TRACKING_SAMPLE_RATE" not in caplog.text


class TestAlertChannelValidation:
    def test_email_enabled_no_recipients_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("ALERT_EMAIL_ENABLED", "true")
        monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "smtp.test.com")
        # No ALERT_EMAIL_TO set
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "ALERT_EMAIL_TO" in caplog.text

    def test_slack_enabled_no_webhook_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("ALERT_SLACK_ENABLED", "true")
        # No ALERT_SLACK_WEBHOOK_URL set
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "ALERT_SLACK_WEBHOOK_URL" in caplog.text

    def test_webhook_enabled_no_url_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("ALERT_WEBHOOK_ENABLED", "true")
        # No ALERT_WEBHOOK_URL set
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "ALERT_WEBHOOK_URL" in caplog.text

    def test_all_channels_configured_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("ALERT_EMAIL_ENABLED", "true")
        monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "smtp.test.com")
        monkeypatch.setenv("ALERT_EMAIL_TO", "ops@test.com")
        monkeypatch.setenv("ALERT_SLACK_ENABLED", "true")
        monkeypatch.setenv("ALERT_SLACK_WEBHOOK_URL", "https://hooks.slack.com/xxx")
        monkeypatch.setenv("ALERT_WEBHOOK_ENABLED", "true")
        monkeypatch.setenv("ALERT_WEBHOOK_URL", "https://webhook.test.com")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "Alert channel config" not in caplog.text

    def test_all_channels_disabled_no_warning(self, monkeypatch, caplog):
        # All channels default to disabled
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "Alert channel config" not in caplog.text


class TestBotMetricsValidation:
    def test_valid_interval_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("BOT_METRICS_ENABLED", "true")
        monkeypatch.setenv("BOT_METRICS_COLLECTION_INTERVAL", "60")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "BOT_METRICS_COLLECTION_INTERVAL" not in caplog.text

    def test_very_low_interval_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("BOT_METRICS_ENABLED", "true")
        monkeypatch.setenv("BOT_METRICS_COLLECTION_INTERVAL", "5")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "very low" in caplog.text

    def test_invalid_interval_warns(self, monkeypatch, caplog):
        monkeypatch.setenv("BOT_METRICS_ENABLED", "true")
        monkeypatch.setenv("BOT_METRICS_COLLECTION_INTERVAL", "not_a_number")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "not a valid integer" in caplog.text

    def test_disabled_no_checks(self, monkeypatch, caplog):
        monkeypatch.setenv("BOT_METRICS_ENABLED", "false")
        monkeypatch.setenv("BOT_METRICS_COLLECTION_INTERVAL", "not_a_number")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        assert "BOT_METRICS_COLLECTION_INTERVAL" not in caplog.text


class TestNeverRaises:
    def test_no_env_vars_does_not_raise(self, caplog):
        """Validation should never raise — app must always start."""
        with caplog.at_level(logging.DEBUG):
            _validate_jorge_services_config(logging.getLogger("test"))

    def test_garbage_env_vars_does_not_raise(self, monkeypatch, caplog):
        """Even with garbage values, validation should not raise."""
        monkeypatch.setenv("PERFORMANCE_TRACKING_ENABLED", "true")
        monkeypatch.setenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "garbage")
        monkeypatch.setenv("BOT_METRICS_ENABLED", "true")
        monkeypatch.setenv("BOT_METRICS_COLLECTION_INTERVAL", "garbage")
        monkeypatch.setenv("ALERT_EMAIL_ENABLED", "true")
        with caplog.at_level(logging.WARNING):
            _validate_jorge_services_config(logging.getLogger("test"))
        # Should have warnings but no exceptions


# =====================================================================
# _build_alert_stats tests
# =====================================================================


@pytest.fixture(autouse=True)
def _reset_singletons():
    """Reset singleton services between tests."""
    from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
    from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
    from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()
    yield
    BotMetricsCollector.reset()
    PerformanceTracker.reset()
    JorgeHandoffService._handoff_history.clear()
    JorgeHandoffService._handoff_outcomes.clear()
    JorgeHandoffService._active_handoffs.clear()
    JorgeHandoffService.reset_analytics()


class TestBuildAlertStats:
    """Tests for _build_alert_stats() used by the periodic alerting loop."""

    @pytest.mark.asyncio
    async def test_returns_all_required_keys(self):
        """Stats dict has all keys the 7 alert rules check."""
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        stats = await _build_alert_stats(BotMetricsCollector(), PerformanceTracker())

        assert "lead_bot" in stats
        assert "p95_latency_ms" in stats["lead_bot"]
        assert "buyer_bot" in stats
        assert "seller_bot" in stats
        assert "error_rate" in stats
        assert "cache_hit_rate" in stats
        assert "handoff_success_rate" in stats
        assert "last_response_time" in stats
        assert "blocked_handoffs_last_hour" in stats
        assert "rate_limit_error_rate" in stats

    @pytest.mark.asyncio
    async def test_p95_values_from_performance_tracker(self):
        """P95 latencies come from PerformanceTracker, not BotMetricsCollector."""
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        tracker = PerformanceTracker()
        for _ in range(50):
            await tracker.track_operation("lead_bot", "process", 100.0)
        # Add one slow request to push P95 up
        await tracker.track_operation("lead_bot", "process", 5000.0)

        stats = await _build_alert_stats(BotMetricsCollector(), tracker)
        # P95 should be > 0 since we added data
        assert stats["lead_bot"]["p95_latency_ms"] > 0

    @pytest.mark.asyncio
    async def test_error_rate_from_metrics_collector(self):
        """Error rate comes from BotMetricsCollector system summary."""
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        mc = BotMetricsCollector()
        # Record 8 successes and 2 failures → 20% error rate
        for _ in range(8):
            mc.record_bot_interaction("lead", duration_ms=100, success=True)
        for _ in range(2):
            mc.record_bot_interaction("lead", duration_ms=100, success=False)

        stats = await _build_alert_stats(mc, PerformanceTracker())
        assert stats["error_rate"] == pytest.approx(0.2, abs=0.01)

    @pytest.mark.asyncio
    async def test_no_data_returns_safe_defaults(self):
        """With no recorded data, all values are safe defaults (no alerts fire)."""
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        stats = await _build_alert_stats(BotMetricsCollector(), PerformanceTracker())

        # P95 latencies should be 0 (no data)
        assert stats["lead_bot"]["p95_latency_ms"] == 0.0
        # Error rate should be 0
        assert stats["error_rate"] == 0.0
        # Cache hit rate defaults to safe value (won't trigger low_cache_hit_rate)
        assert stats["cache_hit_rate"] >= 0.0
        # Handoff success rate safe
        assert stats["handoff_success_rate"] >= 0.0
        # No blocked handoffs
        assert stats["blocked_handoffs_last_hour"] == 0
        assert stats["rate_limit_error_rate"] == 0.0

    @pytest.mark.asyncio
    async def test_handoff_analytics_integration(self):
        """Blocked handoff counts come from JorgeHandoffService analytics."""
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import (
            HandoffDecision,
            JorgeHandoffService,
        )
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        svc = JorgeHandoffService()
        # Execute a handoff, then try the same route (should be blocked as circular)
        decision = HandoffDecision(
            source_bot="lead",
            target_bot="buyer",
            reason="buyer_intent",
            confidence=0.9,
        )
        await svc.execute_handoff(decision, "contact-1")
        await svc.execute_handoff(decision, "contact-1")  # blocked

        stats = await _build_alert_stats(BotMetricsCollector(), PerformanceTracker())
        assert stats["blocked_handoffs_last_hour"] >= 1


class TestLastInteractionTime:
    """Tests for BotMetricsCollector.last_interaction_time()."""

    def test_returns_current_time_when_no_interactions(self):
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector

        mc = BotMetricsCollector()
        t = mc.last_interaction_time()
        assert abs(t - time.time()) < 2

    def test_returns_latest_interaction_timestamp(self):
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector

        mc = BotMetricsCollector()
        mc.record_bot_interaction("lead", duration_ms=50, success=True)
        t = mc.last_interaction_time()
        assert abs(t - time.time()) < 2