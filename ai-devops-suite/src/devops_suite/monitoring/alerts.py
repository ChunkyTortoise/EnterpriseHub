"""Alert management with threshold rules, cooldowns, and notification channels."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum


class AlertCondition(str, Enum):
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    EQUAL = "eq"
    ANOMALY = "anomaly"


class NotificationChannel(str, Enum):
    WEBHOOK = "webhook"
    EMAIL = "email"
    SLACK = "slack"


@dataclass
class AlertRuleConfig:
    rule_id: str
    name: str
    metric_name: str
    condition: AlertCondition
    threshold: float | None = None
    cooldown_seconds: int = 300
    channels: list[NotificationChannel] = field(default_factory=lambda: [NotificationChannel.WEBHOOK])
    is_active: bool = True


@dataclass
class AlertEvent:
    rule_id: str
    rule_name: str
    metric_name: str
    metric_value: float
    threshold: float | None
    severity: str
    message: str
    triggered_at: float


class AlertManager:
    """Evaluates alert rules with cooldowns and dispatches notifications."""

    def __init__(self) -> None:
        self._rules: dict[str, AlertRuleConfig] = {}
        self._last_fired: dict[str, float] = {}
        self._history: list[AlertEvent] = []
        self._notification_log: list[dict] = []

    def add_rule(self, rule: AlertRuleConfig) -> None:
        self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str) -> bool:
        return self._rules.pop(rule_id, None) is not None

    def get_rules(self) -> list[AlertRuleConfig]:
        return list(self._rules.values())

    def get_active_rules(self) -> list[AlertRuleConfig]:
        return [r for r in self._rules.values() if r.is_active]

    def evaluate(self, metric_name: str, value: float, is_anomaly: bool = False,
                 severity: str = "warning") -> list[AlertEvent]:
        now = time.time()
        events = []
        for rule in self._rules.values():
            if not rule.is_active or rule.metric_name != metric_name:
                continue
            last = self._last_fired.get(rule.rule_id, 0)
            if now - last < rule.cooldown_seconds:
                continue

            triggered = False
            if rule.condition == AlertCondition.GREATER_THAN and rule.threshold is not None:
                triggered = value > rule.threshold
            elif rule.condition == AlertCondition.LESS_THAN and rule.threshold is not None:
                triggered = value < rule.threshold
            elif rule.condition == AlertCondition.EQUAL and rule.threshold is not None:
                triggered = abs(value - rule.threshold) < 1e-9
            elif rule.condition == AlertCondition.ANOMALY:
                triggered = is_anomaly

            if triggered:
                event = AlertEvent(
                    rule_id=rule.rule_id,
                    rule_name=rule.name,
                    metric_name=metric_name,
                    metric_value=value,
                    threshold=rule.threshold,
                    severity=severity,
                    message=f"Alert '{rule.name}': {metric_name}={value:.4f} (condition: {rule.condition.value}, threshold: {rule.threshold})",
                    triggered_at=now,
                )
                self._history.append(event)
                self._last_fired[rule.rule_id] = now
                self._dispatch(rule, event)
                events.append(event)
        return events

    def _dispatch(self, rule: AlertRuleConfig, event: AlertEvent) -> None:
        for channel in rule.channels:
            self._notification_log.append({
                "channel": channel.value,
                "rule_id": rule.rule_id,
                "event": event.message,
                "timestamp": event.triggered_at,
            })

    def get_history(self, limit: int = 100) -> list[AlertEvent]:
        return self._history[-limit:]

    def get_notification_log(self) -> list[dict]:
        return list(self._notification_log)

    def clear_history(self) -> None:
        self._history.clear()
        self._notification_log.clear()
        self._last_fired.clear()
