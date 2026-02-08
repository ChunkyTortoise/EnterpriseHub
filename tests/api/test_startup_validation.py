"""Tests for Jorge Bot services startup validation.

Validates that _validate_jorge_services_config() correctly warns about
misconfigured environment variables without raising exceptions.
"""

import logging

import pytest

from ghl_real_estate_ai.api.main import _validate_jorge_services_config


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
