import pytest

pytestmark = pytest.mark.integration

"""Tests for AlertingService.

Covers default rule loading, rule management, alert checking with cooldown,
error handling in conditions, alert sending through channels, alert
history/acknowledgement workflows, channel configuration, escalation policy,
PagerDuty/Opsgenie formatting, and all 7 default alert rules.
"""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.jorge.alerting_service import (
    Alert,
    AlertChannelConfig,
    AlertingService,
    AlertRule,
    EscalationLevel,
    EscalationPolicy,
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
        high_error_second = [a for a in second_alerts if a.rule_name == "high_error_rate"]
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


# ════════════════════════════════════════════════════════════════════════
#  P5 — Alert Channel Configuration & Escalation Tests
# ════════════════════════════════════════════════════════════════════════


class TestAlertChannelConfig:
    """Tests for AlertChannelConfig env-based configuration."""

    def test_from_environment_defaults(self, monkeypatch):
        """All channels are disabled by default."""
        # Clear all ALERT_ vars
        for key in list(vars().keys()):
            pass
        cfg = AlertChannelConfig.from_environment()
        assert cfg.email_enabled is False
        assert cfg.slack_enabled is False
        assert cfg.webhook_enabled is False

    def test_from_environment_email_enabled(self, monkeypatch):
        monkeypatch.setenv("ALERT_EMAIL_ENABLED", "true")
        monkeypatch.setenv("ALERT_EMAIL_TO", "a@x.com, b@x.com")
        monkeypatch.setenv("ALERT_EMAIL_SMTP_HOST", "smtp.test.com")
        monkeypatch.setenv("ALERT_EMAIL_SMTP_PORT", "465")

        cfg = AlertChannelConfig.from_environment()
        assert cfg.email_enabled is True
        assert cfg.email_to == ["a@x.com", "b@x.com"]
        assert cfg.smtp_host == "smtp.test.com"
        assert cfg.smtp_port == 465

    def test_from_environment_slack_enabled(self, monkeypatch):
        monkeypatch.setenv("ALERT_SLACK_ENABLED", "true")
        monkeypatch.setenv("ALERT_SLACK_WEBHOOK_URL", "https://hooks.slack.com/x")
        monkeypatch.setenv("ALERT_SLACK_CHANNEL", "#ops")

        cfg = AlertChannelConfig.from_environment()
        assert cfg.slack_enabled is True
        assert cfg.slack_webhook_url == "https://hooks.slack.com/x"
        assert cfg.slack_channel == "#ops"

    def test_from_environment_pagerduty(self, monkeypatch):
        monkeypatch.setenv("ALERT_WEBHOOK_PAGERDUTY_URL", "https://pd.com/v2")
        monkeypatch.setenv("ALERT_WEBHOOK_PAGERDUTY_API_KEY", "pdkey123")

        cfg = AlertChannelConfig.from_environment()
        assert cfg.pagerduty_url == "https://pd.com/v2"
        assert cfg.pagerduty_api_key == "pdkey123"

    def test_from_environment_opsgenie(self, monkeypatch):
        monkeypatch.setenv("ALERT_WEBHOOK_OPSGENIE_URL", "https://og.com/v2")
        monkeypatch.setenv("ALERT_WEBHOOK_OPSGENIE_API_KEY", "ogkey456")

        cfg = AlertChannelConfig.from_environment()
        assert cfg.opsgenie_url == "https://og.com/v2"
        assert cfg.opsgenie_api_key == "ogkey456"

    def test_from_environment_webhook_headers(self, monkeypatch):
        monkeypatch.setenv(
            "ALERT_WEBHOOK_HEADERS",
            '{"Authorization": "Bearer tok"}',
        )
        cfg = AlertChannelConfig.from_environment()
        assert cfg.webhook_headers == {"Authorization": "Bearer tok"}

    def test_from_environment_bad_json_headers(self, monkeypatch):
        monkeypatch.setenv("ALERT_WEBHOOK_HEADERS", "not-json")
        cfg = AlertChannelConfig.from_environment()
        assert cfg.webhook_headers == {}

    def test_validate_email_no_recipients(self):
        cfg = AlertChannelConfig(email_enabled=True, email_to=[])
        warnings = cfg.validate()
        assert any("email" in w.lower() for w in warnings)

    def test_validate_slack_no_url(self):
        cfg = AlertChannelConfig(slack_enabled=True, slack_webhook_url="")
        warnings = cfg.validate()
        assert any("slack" in w.lower() for w in warnings)

    def test_validate_webhook_no_url(self):
        cfg = AlertChannelConfig(webhook_enabled=True, webhook_url="")
        warnings = cfg.validate()
        assert any("webhook" in w.lower() for w in warnings)

    def test_validate_all_ok(self):
        cfg = AlertChannelConfig(
            email_enabled=True,
            email_to=["a@b.com"],
            slack_enabled=True,
            slack_webhook_url="https://hooks.slack.com/x",
            webhook_enabled=True,
            webhook_url="https://hook.example.com",
        )
        assert cfg.validate() == []


class TestEscalationPolicy:
    """Tests for the 3-level escalation policy."""

    def _make_alert(self, severity="critical", triggered_at=None, ack=False):
        return Alert(
            id="esc-test",
            rule_name="test_rule",
            severity=severity,
            message="test",
            triggered_at=triggered_at or time.time(),
            performance_stats={},
            acknowledged=ack,
        )

    def test_acknowledged_alert_level_zero(self):
        policy = EscalationPolicy()
        alert = self._make_alert(ack=True)
        assert policy.get_escalation_level(alert) == 0

    def test_fresh_alert_level_one(self):
        policy = EscalationPolicy()
        alert = self._make_alert(triggered_at=time.time())
        assert policy.get_escalation_level(alert) == 1

    def test_5min_old_alert_level_two(self):
        policy = EscalationPolicy()
        alert = self._make_alert(triggered_at=time.time() - 310)
        assert policy.get_escalation_level(alert) == 2

    def test_15min_old_alert_level_three(self):
        policy = EscalationPolicy()
        alert = self._make_alert(triggered_at=time.time() - 910)
        assert policy.get_escalation_level(alert) == 3

    def test_pending_escalations_only_critical(self):
        policy = EscalationPolicy()
        critical = self._make_alert(
            severity="critical",
            triggered_at=time.time() - 310,
        )
        warning = self._make_alert(
            severity="warning",
            triggered_at=time.time() - 310,
        )
        results = policy.get_pending_escalations([critical, warning])
        assert len(results) == 1
        assert results[0][0].severity == "critical"
        assert results[0][1].level == 2

    def test_pending_escalations_excludes_acknowledged(self):
        policy = EscalationPolicy()
        alert = self._make_alert(
            triggered_at=time.time() - 910,
            ack=True,
        )
        assert policy.get_pending_escalations([alert]) == []

    def test_default_levels_structure(self):
        policy = EscalationPolicy()
        assert len(policy.levels) == 3
        assert policy.levels[0].level == 1
        assert policy.levels[0].delay_seconds == 0
        assert policy.levels[1].level == 2
        assert policy.levels[1].delay_seconds == 300
        assert policy.levels[2].level == 3
        assert policy.levels[2].delay_seconds == 900

    def test_custom_levels(self):
        custom = [EscalationLevel(1, 0, [], "immediate")]
        policy = EscalationPolicy(levels=custom)
        assert len(policy.levels) == 1


class TestAlertRuleChannelSpec:
    """Verify all 7 rules match the spec's channel/cooldown requirements."""

    def test_sla_violation_channels(self):
        svc = AlertingService()
        rule = svc._rules["sla_violation"]
        assert set(rule.channels) == {"email", "slack", "webhook"}
        assert rule.severity == "critical"
        assert rule.cooldown_seconds == 300

    def test_high_error_rate_channels(self):
        svc = AlertingService()
        rule = svc._rules["high_error_rate"]
        assert set(rule.channels) == {"email", "slack", "webhook"}
        assert rule.severity == "critical"
        assert rule.cooldown_seconds == 300

    def test_low_cache_hit_rate_channels(self):
        svc = AlertingService()
        rule = svc._rules["low_cache_hit_rate"]
        assert rule.channels == ["slack"]
        assert rule.severity == "warning"
        assert rule.cooldown_seconds == 600

    def test_handoff_failure_channels(self):
        svc = AlertingService()
        rule = svc._rules["handoff_failure"]
        assert set(rule.channels) == {"email", "slack"}
        assert rule.severity == "critical"
        assert rule.cooldown_seconds == 300

    def test_bot_unresponsive_channels(self):
        svc = AlertingService()
        rule = svc._rules["bot_unresponsive"]
        assert set(rule.channels) == {"email", "slack", "webhook"}
        assert rule.severity == "critical"
        assert rule.cooldown_seconds == 600

    def test_circular_handoff_spike_channels(self):
        svc = AlertingService()
        rule = svc._rules["circular_handoff_spike"]
        assert rule.channels == ["slack"]
        assert rule.severity == "warning"
        assert rule.cooldown_seconds == 600

    def test_rate_limit_breach_channels(self):
        svc = AlertingService()
        rule = svc._rules["rate_limit_breach"]
        assert rule.channels == ["slack"]
        assert rule.severity == "warning"
        assert rule.cooldown_seconds == 300


class TestAllRuleConditions:
    """Verify each of the 7 default rules triggers on correct input."""

    @pytest.mark.asyncio
    async def test_sla_violation_triggers(self):
        svc = AlertingService()
        stats = {"lead_bot": {"p95_latency_ms": 2100}}
        alerts = await svc.check_alerts(stats)
        assert any(a.rule_name == "sla_violation" for a in alerts)

    @pytest.mark.asyncio
    async def test_high_error_rate_triggers(self):
        svc = AlertingService()
        alerts = await svc.check_alerts({"error_rate": 0.06})
        assert any(a.rule_name == "high_error_rate" for a in alerts)

    @pytest.mark.asyncio
    async def test_low_cache_hit_rate_triggers(self):
        svc = AlertingService()
        alerts = await svc.check_alerts({"cache_hit_rate": 0.40})
        assert any(a.rule_name == "low_cache_hit_rate" for a in alerts)

    @pytest.mark.asyncio
    async def test_handoff_failure_triggers(self):
        svc = AlertingService()
        alerts = await svc.check_alerts({"handoff_success_rate": 0.90})
        assert any(a.rule_name == "handoff_failure" for a in alerts)

    @pytest.mark.asyncio
    async def test_bot_unresponsive_triggers(self):
        svc = AlertingService()
        stats = {"last_response_time": time.time() - 400}
        alerts = await svc.check_alerts(stats)
        assert any(a.rule_name == "bot_unresponsive" for a in alerts)

    @pytest.mark.asyncio
    async def test_circular_handoff_spike_triggers(self):
        svc = AlertingService()
        alerts = await svc.check_alerts({"blocked_handoffs_last_hour": 15})
        assert any(a.rule_name == "circular_handoff_spike" for a in alerts)

    @pytest.mark.asyncio
    async def test_rate_limit_breach_triggers(self):
        svc = AlertingService()
        alerts = await svc.check_alerts({"rate_limit_error_rate": 0.12})
        assert any(a.rule_name == "rate_limit_breach" for a in alerts)


class TestChannelSending:
    """Tests for email/Slack/webhook/PagerDuty/Opsgenie sending."""

    def _make_alert(self):
        return Alert(
            id="ch-test",
            rule_name="high_error_rate",
            severity="critical",
            message="Error rate 10%",
            triggered_at=time.time(),
            performance_stats={"error_rate": 0.10},
        )

    @pytest.mark.asyncio
    async def test_email_skips_when_no_recipients(self):
        svc = AlertingService()
        svc.channel_config.email_to = []
        alert = self._make_alert()
        # Should not raise
        await svc._send_email_alert(alert)

    @pytest.mark.asyncio
    async def test_slack_skips_when_no_url(self):
        svc = AlertingService()
        svc.channel_config.slack_webhook_url = ""
        alert = self._make_alert()
        await svc._send_slack_alert(alert)

    @pytest.mark.asyncio
    async def test_webhook_skips_when_no_url(self):
        svc = AlertingService()
        svc.channel_config.webhook_url = ""
        svc.channel_config.pagerduty_url = ""
        svc.channel_config.opsgenie_url = ""
        alert = self._make_alert()
        await svc._send_webhook_alert(alert)

    @pytest.mark.asyncio
    async def test_webhook_routes_to_pagerduty(self):
        svc = AlertingService()
        svc.channel_config.pagerduty_url = "https://pd.com"
        svc.channel_config.pagerduty_api_key = "key"
        alert = self._make_alert()

        with patch.object(
            svc,
            "_send_pagerduty_alert",
            new_callable=AsyncMock,
        ) as mock_pd:
            await svc._send_webhook_alert(alert)
            mock_pd.assert_awaited_once_with(alert)

    @pytest.mark.asyncio
    async def test_webhook_routes_to_opsgenie(self):
        svc = AlertingService()
        svc.channel_config.pagerduty_url = ""
        svc.channel_config.opsgenie_url = "https://og.com"
        svc.channel_config.opsgenie_api_key = "key"
        alert = self._make_alert()

        with patch.object(
            svc,
            "_send_opsgenie_alert",
            new_callable=AsyncMock,
        ) as mock_og:
            await svc._send_webhook_alert(alert)
            mock_og.assert_awaited_once_with(alert)

    @pytest.mark.asyncio
    async def test_pagerduty_payload_format(self):
        svc = AlertingService()
        svc.channel_config.pagerduty_url = "https://pd.test"
        svc.channel_config.pagerduty_api_key = "rk123"
        alert = self._make_alert()

        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post = AsyncMock(return_value=mock_resp)
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.post = MagicMock(return_value=mock_post)
            mock_session_cls.return_value = mock_session

            await svc._send_pagerduty_alert(alert)

            # Verify the post was called with PD URL
            mock_session.post.assert_called_once()
            call_args = mock_session.post.call_args
            assert call_args[0][0] == "https://pd.test"
            payload = call_args[1]["json"]
            assert payload["routing_key"] == "rk123"
            assert payload["event_action"] == "trigger"
            assert "jorge" in payload["dedup_key"]
            assert payload["payload"]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_opsgenie_payload_format(self):
        svc = AlertingService()
        svc.channel_config.opsgenie_url = "https://og.test"
        svc.channel_config.opsgenie_api_key = "gk456"
        alert = self._make_alert()

        mock_resp = AsyncMock()
        mock_resp.raise_for_status = MagicMock()
        mock_post = AsyncMock(return_value=mock_resp)
        mock_post.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_post.__aexit__ = AsyncMock(return_value=False)

        with patch("aiohttp.ClientSession") as mock_session_cls:
            mock_session = AsyncMock()
            mock_session.__aenter__ = AsyncMock(return_value=mock_session)
            mock_session.__aexit__ = AsyncMock(return_value=False)
            mock_session.post = MagicMock(return_value=mock_post)
            mock_session_cls.return_value = mock_session

            await svc._send_opsgenie_alert(alert)

            call_args = mock_session.post.call_args
            assert call_args[0][0] == "https://og.test"
            payload = call_args[1]["json"]
            assert payload["priority"] == "P1"
            assert "jorge" in payload["tags"]
            headers = call_args[1]["headers"]
            assert "GenieKey gk456" in headers["Authorization"]


class TestCheckAndSendAlerts:
    """Tests for check_and_send_alerts convenience method."""

    @pytest.mark.asyncio
    async def test_check_and_send_fires_within_30_seconds(self):
        """Alerts fire within 30 seconds of threshold breach (spec requirement)."""
        svc = AlertingService()
        stats = {"error_rate": 0.10}

        before = time.time()
        alerts = await svc.check_and_send_alerts(stats)
        after = time.time()

        assert len(alerts) > 0
        for alert in alerts:
            assert alert.triggered_at >= before
            assert alert.triggered_at <= after
            assert (after - before) < 30.0

    @pytest.mark.asyncio
    async def test_check_and_send_sends_to_channels(self):
        svc = AlertingService()
        stats = {"error_rate": 0.10}

        with (
            patch.object(svc, "_send_email_alert", new_callable=AsyncMock),
            patch.object(svc, "_send_slack_alert", new_callable=AsyncMock),
            patch.object(svc, "_send_webhook_alert", new_callable=AsyncMock),
        ):
            alerts = await svc.check_and_send_alerts(stats)

        assert any(a.rule_name == "high_error_rate" for a in alerts)


class TestCheckEscalations:
    """Tests for the check_escalations convenience method."""

    @pytest.mark.asyncio
    async def test_check_escalations_returns_stale_critical(self):
        svc = AlertingService()
        svc._alerts.append(
            Alert(
                id="stale-crit",
                rule_name="high_error_rate",
                severity="critical",
                message="old",
                triggered_at=time.time() - 400,
                performance_stats={},
            )
        )

        escalations = await svc.check_escalations()
        assert len(escalations) == 1
        assert escalations[0][0].id == "stale-crit"
        assert escalations[0][1].level == 2

    @pytest.mark.asyncio
    async def test_check_escalations_skips_acknowledged(self):
        svc = AlertingService()
        svc._alerts.append(
            Alert(
                id="acked",
                rule_name="high_error_rate",
                severity="critical",
                message="acked",
                triggered_at=time.time() - 400,
                performance_stats={},
                acknowledged=True,
            )
        )

        escalations = await svc.check_escalations()
        assert len(escalations) == 0

    @pytest.mark.asyncio
    async def test_check_escalations_skips_warning(self):
        svc = AlertingService()
        svc._alerts.append(
            Alert(
                id="warn",
                rule_name="low_cache_hit_rate",
                severity="warning",
                message="old warning",
                triggered_at=time.time() - 400,
                performance_stats={},
            )
        )

        escalations = await svc.check_escalations()
        assert len(escalations) == 0


class TestMetricRecording:
    """Tests for record_metric integration."""

    def test_record_and_retrieve_metrics(self):
        svc = AlertingService()
        svc.record_metric("error_rate", 0.05)
        svc.record_metric("cache_hit_rate", 0.70)

        metrics = svc.get_recorded_metrics()
        assert metrics["error_rate"] == 0.05
        assert metrics["cache_hit_rate"] == 0.70

    def test_clear_recorded_metrics(self):
        svc = AlertingService()
        svc.record_metric("error_rate", 0.05)
        svc.clear_recorded_metrics()
        assert svc.get_recorded_metrics() == {}

    @pytest.mark.asyncio
    async def test_remove_rule(self):
        svc = AlertingService()
        await svc.remove_rule("rate_limit_breach")
        assert "rate_limit_breach" not in svc._rules

    @pytest.mark.asyncio
    async def test_remove_nonexistent_rule_raises(self):
        svc = AlertingService()
        with pytest.raises(KeyError, match="nonexistent"):
            await svc.remove_rule("nonexistent")

    @pytest.mark.asyncio
    async def test_list_rules(self):
        svc = AlertingService()
        rules = await svc.list_rules()
        assert len(rules) == 7
        assert all(isinstance(r, AlertRule) for r in rules)
