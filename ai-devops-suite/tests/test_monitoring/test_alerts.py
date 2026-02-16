"""Tests for AlertManager: rules, cooldowns, thresholds, dispatching."""

import time

import pytest

from devops_suite.monitoring.alerts import (
    AlertCondition,
    AlertManager,
    AlertRuleConfig,
    NotificationChannel,
)


@pytest.fixture
def alert_manager():
    return AlertManager()


@pytest.fixture
def sample_rule():
    return AlertRuleConfig(
        rule_id="latency-high",
        name="High Latency Alert",
        metric_name="latency",
        condition=AlertCondition.GREATER_THAN,
        threshold=100.0,
        cooldown_seconds=60,
        channels=[NotificationChannel.WEBHOOK],
    )


class TestAlertManager:
    def test_add_and_get_rule(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        rules = alert_manager.get_rules()
        assert len(rules) == 1
        assert rules[0].rule_id == "latency-high"

    def test_remove_rule(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        removed = alert_manager.remove_rule("latency-high")
        assert removed is True
        assert len(alert_manager.get_rules()) == 0

    def test_remove_nonexistent_rule(self, alert_manager):
        removed = alert_manager.remove_rule("fake-id")
        assert removed is False

    def test_get_active_rules(self, alert_manager):
        rule1 = AlertRuleConfig(
            rule_id="r1", name="R1", metric_name="latency",
            condition=AlertCondition.GREATER_THAN, threshold=50.0, is_active=True,
        )
        rule2 = AlertRuleConfig(
            rule_id="r2", name="R2", metric_name="cost",
            condition=AlertCondition.GREATER_THAN, threshold=1.0, is_active=False,
        )
        alert_manager.add_rule(rule1)
        alert_manager.add_rule(rule2)
        active = alert_manager.get_active_rules()
        assert len(active) == 1
        assert active[0].rule_id == "r1"

    def test_greater_than_triggers(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        events = alert_manager.evaluate("latency", 150.0)
        assert len(events) == 1
        assert events[0].metric_value == 150.0
        assert events[0].rule_id == "latency-high"

    def test_greater_than_does_not_trigger(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        events = alert_manager.evaluate("latency", 50.0)
        assert len(events) == 0

    def test_less_than_condition(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="low-quality",
            name="Low Quality",
            metric_name="quality",
            condition=AlertCondition.LESS_THAN,
            threshold=50.0,
        )
        alert_manager.add_rule(rule)
        events = alert_manager.evaluate("quality", 30.0)
        assert len(events) == 1

    def test_equal_condition(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="zero-usage",
            name="Zero Usage",
            metric_name="tokens",
            condition=AlertCondition.EQUAL,
            threshold=0.0,
        )
        alert_manager.add_rule(rule)
        events = alert_manager.evaluate("tokens", 0.0)
        assert len(events) == 1

    def test_anomaly_condition(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="anomaly-detect",
            name="Anomaly",
            metric_name="latency",
            condition=AlertCondition.ANOMALY,
        )
        alert_manager.add_rule(rule)
        events = alert_manager.evaluate("latency", 100.0, is_anomaly=True)
        assert len(events) == 1

    def test_cooldown_prevents_repeat_firing(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="cooldown-test",
            name="Cooldown Test",
            metric_name="latency",
            condition=AlertCondition.GREATER_THAN,
            threshold=50.0,
            cooldown_seconds=2,
        )
        alert_manager.add_rule(rule)
        events1 = alert_manager.evaluate("latency", 100.0)
        assert len(events1) == 1
        # Immediate re-evaluation should be blocked by cooldown
        events2 = alert_manager.evaluate("latency", 100.0)
        assert len(events2) == 0

    def test_cooldown_expires_allows_refiring(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="cooldown-test",
            name="Cooldown Test",
            metric_name="latency",
            condition=AlertCondition.GREATER_THAN,
            threshold=50.0,
            cooldown_seconds=1,
        )
        alert_manager.add_rule(rule)
        events1 = alert_manager.evaluate("latency", 100.0)
        assert len(events1) == 1
        time.sleep(1.1)
        events2 = alert_manager.evaluate("latency", 100.0)
        assert len(events2) == 1

    def test_inactive_rule_does_not_trigger(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="inactive",
            name="Inactive",
            metric_name="latency",
            condition=AlertCondition.GREATER_THAN,
            threshold=50.0,
            is_active=False,
        )
        alert_manager.add_rule(rule)
        events = alert_manager.evaluate("latency", 100.0)
        assert len(events) == 0

    def test_wrong_metric_does_not_trigger(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        events = alert_manager.evaluate("cost", 1000.0)
        assert len(events) == 0

    def test_notification_dispatch(self, alert_manager):
        rule = AlertRuleConfig(
            rule_id="notify-test",
            name="Notify Test",
            metric_name="latency",
            condition=AlertCondition.GREATER_THAN,
            threshold=50.0,
            channels=[NotificationChannel.EMAIL, NotificationChannel.SLACK],
        )
        alert_manager.add_rule(rule)
        alert_manager.evaluate("latency", 100.0)
        log = alert_manager.get_notification_log()
        assert len(log) == 2
        assert {entry["channel"] for entry in log} == {"email", "slack"}

    def test_get_history(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        alert_manager.evaluate("latency", 150.0)
        history = alert_manager.get_history()
        assert len(history) == 1
        assert history[0].metric_name == "latency"

    def test_clear_history(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        alert_manager.evaluate("latency", 150.0)
        alert_manager.clear_history()
        assert len(alert_manager.get_history()) == 0
        assert len(alert_manager.get_notification_log()) == 0

    def test_multiple_rules_same_metric(self, alert_manager):
        rule1 = AlertRuleConfig(
            rule_id="r1", name="R1", metric_name="latency",
            condition=AlertCondition.GREATER_THAN, threshold=100.0,
        )
        rule2 = AlertRuleConfig(
            rule_id="r2", name="R2", metric_name="latency",
            condition=AlertCondition.GREATER_THAN, threshold=200.0,
        )
        alert_manager.add_rule(rule1)
        alert_manager.add_rule(rule2)
        events = alert_manager.evaluate("latency", 250.0)
        assert len(events) == 2

    def test_severity_field(self, alert_manager, sample_rule):
        alert_manager.add_rule(sample_rule)
        events = alert_manager.evaluate("latency", 150.0, severity="critical")
        assert events[0].severity == "critical"
