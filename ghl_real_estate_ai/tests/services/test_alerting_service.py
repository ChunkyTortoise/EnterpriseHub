"""
Tests for Jorge Alerting Service.

Validates alert rule checking, notification sending, and cooldowns.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.alerting_service import (
    Alert,
    AlertingService,
    AlertRule,
)


@pytest.fixture(autouse=True)
def reset_alerting_service():
    """Reset alerting service state before each test."""
    AlertingService._instance = None
    AlertingService._initialized = False
    yield
    AlertingService._instance = None
    AlertingService._initialized = False


class TestAlertingService:
    """Test suite for alerting functionality."""

    @pytest.fixture
    def alerting_service(self):
        """Create a fresh AlertingService instance for each test."""
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

        mock_smtp_instance = MagicMock()
        mock_smtp_instance.__enter__ = MagicMock(return_value=mock_smtp_instance)
        mock_smtp_instance.__exit__ = MagicMock(return_value=False)

        with patch("ghl_real_estate_ai.services.jorge.alerting_service.smtplib.SMTP") as mock_smtp:
            mock_smtp.return_value = mock_smtp_instance

            with patch.dict(
                "os.environ",
                {
                    "ALERT_EMAIL_TO": "test@example.com",
                    "ALERT_SMTP_HOST": "localhost",
                    "ALERT_SMTP_PORT": "587",
                },
            ):
                await alerting_service._send_email_alert(alert)
                mock_smtp.assert_called_once()
                mock_smtp_instance.send_message.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_email_alert_no_recipients(self, alerting_service):
        """Test email alert with no recipients configured."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="critical",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Should not raise when no recipients configured
        with patch.dict("os.environ", {"ALERT_EMAIL_TO": ""}):
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

        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()

        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.dict("os.environ", {"ALERT_SLACK_WEBHOOK_URL": "https://hooks.slack.com/test"}):
                await alerting_service._send_slack_alert(alert)
                mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_slack_alert_no_webhook(self, alerting_service):
        """Test Slack alert with no webhook configured."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="warning",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Should not raise when no webhook configured
        with patch.dict("os.environ", {}, clear=True):
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

        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()

        mock_post = AsyncMock()
        mock_post.__aenter__ = AsyncMock(return_value=mock_response)
        mock_post.__aexit__ = AsyncMock(return_value=None)

        mock_session = AsyncMock()
        mock_session.post = MagicMock(return_value=mock_post)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=None)

        with patch("aiohttp.ClientSession", return_value=mock_session):
            with patch.dict("os.environ", {"ALERT_WEBHOOK_URL": "https://example.com/webhook"}):
                await alerting_service._send_webhook_alert(alert)
                mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_webhook_alert_no_url(self, alerting_service):
        """Test webhook alert with no URL configured."""
        alert = Alert(
            id="test_alert",
            rule_name="test_rule",
            severity="info",
            message="Test alert message",
            triggered_at=1234567890.0,
            performance_stats={},
        )

        # Should not raise when no webhook URL configured
        with patch.dict("os.environ", {}, clear=True):
            await alerting_service._send_webhook_alert(alert)

    @pytest.mark.asyncio
    async def test_check_alert_rules(self, alerting_service):
        """Test checking alert rules against performance stats."""
        stats = {
            "error_rate": 0.10,
            "cache_hit_rate": 0.60,
            "handoff_success_rate": 0.98,
        }

        alerts = await alerting_service.check_alerts(stats)

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

        rules = await alerting_service.list_rules()
        assert any(r.name == "custom_rule" for r in rules)

    @pytest.mark.asyncio
    async def test_unregister_alert_rule(self, alerting_service):
        """Test removing an alert rule."""
        custom_rule = AlertRule(
            name="custom_rule",
            condition=lambda stats: True,
            severity="info",
            cooldown_seconds=300,
            channels=["email"],
        )
        await alerting_service.add_rule(custom_rule)

        await alerting_service.remove_rule("custom_rule")

        rules = await alerting_service.list_rules()
        assert not any(r.name == "custom_rule" for r in rules)

    @pytest.mark.asyncio
    async def test_alert_cooldown(self, alerting_service):
        """Test that alerts respect cooldown periods."""
        stats = {
            "error_rate": 0.10,
            "cache_hit_rate": 0.60,
        }

        alerts1 = await alerting_service.check_alerts(stats)
        assert len(alerts1) > 0

        alerts2 = await alerting_service.check_alerts(stats)
        assert len(alerts2) == 0