"""Tests for AlertingService.

Covers default rule loading, rule management, alert checking with cooldown,
error handling in conditions, alert sending through channels, and alert
history/acknowledgement workflows.
"""

import time

import pytest
from unittest.mock import patch, AsyncMock

from ghl_real_estate_ai.services.jorge.alerting_service import (
    AlertingService,
    AlertRule,
    Alert,
)


@pytest.fixture(autouse=True)
def reset_service():
    """Reset AlertingService singleton before and after each test."""
    AlertingService.reset()
    yield
    AlertingService.reset()


class TestAlertingService:
    """Tests for AlertingService."""

    # ── 1. Default rules ───────────────────────────────────────────────

    def test_default_rules_loaded(self):
        """Service initializes with exactly 7 default alert rules."""
        service = AlertingService()
        expected_rules = {
            "sla_violation",
            "high_error_rate",
            "low_cache_hit_rate",
            "handoff_failure",
            "bot_unresponsive",
            "circular_handoff_spike",
            "rate_limit_breach",
        }
        assert set(service._rules.keys()) == expected_rules
        assert len(service._rules) == 7

    # ── 2. Add valid rule ──────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_rule_valid(self):
        """A rule with valid severity and channels is registered."""
        service = AlertingService()
        custom_rule = AlertRule(
            name="custom_test_rule",
            condition=lambda stats: stats.get("foo", 0) > 10,
            severity="warning",
            cooldown_seconds=120,
            channels=["slack"],
            description="Custom test rule",
        )
        await service.add_rule(custom_rule)

        assert "custom_test_rule" in service._rules
        assert service._rules["custom_test_rule"].severity == "warning"
        assert service._rules["custom_test_rule"].channels == ["slack"]

    # ── 3. Invalid severity ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_rule_invalid_severity_raises(self):
        """Adding a rule with an invalid severity raises ValueError."""
        service = AlertingService()
        bad_rule = AlertRule(
            name="bad_severity",
            condition=lambda stats: True,
            severity="panic",
            channels=["email"],
        )
        with pytest.raises(ValueError, match="Invalid severity 'panic'"):
            await service.add_rule(bad_rule)

    # ── 4. Invalid channels ────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_add_rule_invalid_channels_raises(self):
        """Adding a rule with an unrecognized channel raises ValueError."""
        service = AlertingService()
        bad_rule = AlertRule(
            name="bad_channel",
            condition=lambda stats: True,
            severity="info",
            channels=["sms", "email"],
        )
        with pytest.raises(ValueError, match="Invalid channels"):
            await service.add_rule(bad_rule)

    # ── 5. check_alerts triggers on matching stats ─────────────────────

    @pytest.mark.asyncio
    async def test_check_alerts_triggers(self):
        """check_alerts returns alerts when conditions are met (high_error_rate)."""
        service = AlertingService()
        stats = {"error_rate": 0.10}  # > 0.05 threshold

        alerts = await service.check_alerts(stats)
        triggered_names = [a.rule_name for a in alerts]

        assert "high_error_rate" in triggered_names
        # Verify the alert object structure
        her_alert = next(a for a in alerts if a.rule_name == "high_error_rate")
        assert her_alert.severity == "critical"
        assert her_alert.acknowledged is False
        assert her_alert.performance_stats == stats

    # ── 6. Cooldown prevents re-triggering ─────────────────────────────

    @pytest.mark.asyncio
    async def test_check_alerts_cooldown(self):
        """An alert should not re-trigger within its cooldown window."""
        service = AlertingService()
        stats = {"error_rate": 0.10}

        # First check -- should trigger
        first_alerts = await service.check_alerts(stats)
        assert any(a.rule_name == "high_error_rate" for a in first_alerts)

        # Second check immediately -- should NOT trigger (cooldown = 300s)
        second_alerts = await service.check_alerts(stats)
        high_error_second = [
            a for a in second_alerts if a.rule_name == "high_error_rate"
        ]
        assert len(high_error_second) == 0

    # ── 7. Condition errors are handled gracefully ─────────────────────

    @pytest.mark.asyncio
    async def test_check_alerts_condition_error_handled(self):
        """A rule whose condition raises an exception is skipped, not propagated."""
        service = AlertingService()

        def exploding_condition(stats):
            raise RuntimeError("boom")

        bad_rule = AlertRule(
            name="exploding_rule",
            condition=exploding_condition,
            severity="warning",
            channels=["slack"],
            description="This rule always explodes",
        )
        await service.add_rule(bad_rule)

        # Should not raise -- the error is caught and logged
        alerts = await service.check_alerts({"error_rate": 0.01})

        # The exploding rule should NOT appear in triggered alerts
        assert all(a.rule_name != "exploding_rule" for a in alerts)

    # ── 8. send_alert populates channels_sent ──────────────────────────

    @pytest.mark.asyncio
    async def test_send_alert_channels(self):
        """send_alert dispatches to configured channels and records them."""
        service = AlertingService()

        # Trigger high_error_rate (channels: email, slack, webhook)
        stats = {"error_rate": 0.10}
        alerts = await service.check_alerts(stats)
        alert = next(a for a in alerts if a.rule_name == "high_error_rate")

        # Mock all three channel senders
        p1 = patch.object(service, "_send_email_alert", new_callable=AsyncMock)
        p2 = patch.object(service, "_send_slack_alert", new_callable=AsyncMock)
        p3 = patch.object(service, "_send_webhook_alert", new_callable=AsyncMock)
        with p1 as mock_email, p2 as mock_slack, p3 as mock_webhook:
            await service.send_alert(alert)

            mock_email.assert_awaited_once_with(alert)
            mock_slack.assert_awaited_once_with(alert)
            mock_webhook.assert_awaited_once_with(alert)

        # channels_sent should reflect all three
        assert set(alert.channels_sent) == {"email", "slack", "webhook"}

    # ── 9. Alert history ordering and limit ────────────────────────────

    @pytest.mark.asyncio
    async def test_get_alert_history(self):
        """get_alert_history returns alerts most-recent-first, respecting limit."""
        service = AlertingService()

        # Manually insert 5 alerts with sequential timestamps
        for i in range(5):
            service._alerts.append(
                Alert(
                    id=f"alert_{i}",
                    rule_name="test",
                    severity="info",
                    message=f"Alert {i}",
                    triggered_at=1000.0 + i,
                    performance_stats={},
                )
            )

        # Full history -- most recent first
        history = await service.get_alert_history(limit=50)
        assert len(history) == 5
        assert history[0].id == "alert_4"
        assert history[-1].id == "alert_0"

        # Limited history
        limited = await service.get_alert_history(limit=3)
        assert len(limited) == 3
        # Should be the 3 most recent, newest first
        assert limited[0].id == "alert_4"
        assert limited[1].id == "alert_3"
        assert limited[2].id == "alert_2"

    # ── 10. Active alerts filter acknowledged ──────────────────────────

    @pytest.mark.asyncio
    async def test_get_active_alerts_filter_acknowledged(self):
        """get_active_alerts excludes acknowledged alerts."""
        service = AlertingService()

        # Insert two alerts
        service._alerts.append(
            Alert(
                id="ack_me",
                rule_name="test",
                severity="info",
                message="Will be acknowledged",
                triggered_at=time.time(),
                performance_stats={},
            )
        )
        service._alerts.append(
            Alert(
                id="keep_me",
                rule_name="test",
                severity="info",
                message="Stay active",
                triggered_at=time.time(),
                performance_stats={},
            )
        )

        # Acknowledge one
        await service.acknowledge_alert("ack_me")

        active = await service.get_active_alerts()
        active_ids = [a.id for a in active]
        assert "ack_me" not in active_ids
        assert "keep_me" in active_ids

        # Acknowledging unknown ID raises KeyError
        with pytest.raises(KeyError, match="not_real"):
            await service.acknowledge_alert("not_real")
