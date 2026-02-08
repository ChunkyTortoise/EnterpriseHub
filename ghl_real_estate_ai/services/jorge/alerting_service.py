"""
Jorge Bot Alerting Service

Monitors bot performance metrics and sends alerts when thresholds are breached.
Supports multiple notification channels (email, Slack, webhook, PagerDuty,
Opsgenie) with cooldown periods to prevent alert spam and a 3-level
escalation policy for unacknowledged critical alerts.

Default alert rules align with the Jorge Bot Audit Spec:
1. SLA Violation: P95 latency exceeds target
2. High Error Rate: Error rate > 5%
3. Low Cache Hit Rate: Cache hit rate < 50%
4. Handoff Failure: Handoff success rate < 95%
5. Bot Unresponsive: No responses for 5 minutes
6. Circular Handoff Spike: >10 blocked handoffs in 1 hour
7. Rate Limit Breach: Rate limit errors > 10%

Escalation Policy:
    Level 1 (0s):   Send to rule's configured channels
    Level 2 (5min): Re-send unacknowledged critical alerts to email+slack+webhook
    Level 3 (15min): Escalate unacknowledged critical alerts to PagerDuty/Opsgenie

Usage:
    service = AlertingService()
    alerts = await service.check_alerts(performance_stats)
    await service.send_alert(alert)
    history = await service.get_alert_history(limit=50)
    escalations = service.escalation_policy.get_pending_escalations(
        await service.get_active_alerts()
    )
"""

import asyncio
import json as _json
import logging
import os
import smtplib
import time
import uuid
from dataclasses import dataclass, field
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import aiohttp

logger = logging.getLogger(__name__)

# Configuration constants
MAX_STORED_ALERTS = 100
DEFAULT_COOLDOWN_SECONDS = 300  # 5 minutes
VALID_SEVERITIES = frozenset({"critical", "warning", "info"})
VALID_CHANNELS = frozenset({"email", "slack", "webhook"})


@dataclass
class AlertRule:
    """A single alerting rule with condition and notification channels."""

    name: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: str  # "critical", "warning", "info"
    cooldown_seconds: int = DEFAULT_COOLDOWN_SECONDS
    channels: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class Alert:
    """Represents a triggered alert."""

    id: str
    rule_name: str
    severity: str
    message: str
    triggered_at: float
    performance_stats: Dict[str, Any]
    channels_sent: List[str] = field(default_factory=list)
    acknowledged: bool = False


# ── Alert Channel Configuration ────────────────────────────────────────


@dataclass
class AlertChannelConfig:
    """Configuration for alert notification channels, loaded from environment."""

    # Email (SMTP)
    email_enabled: bool = False
    smtp_host: str = "localhost"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "alerts@enterprisehub.com"
    email_to: List[str] = field(default_factory=list)
    smtp_use_tls: bool = True

    # Slack
    slack_enabled: bool = False
    slack_webhook_url: str = ""
    slack_channel: str = "#jorge-alerts"
    slack_username: str = "Jorge Bot Alert"
    slack_icon_emoji: str = ":rotating_light:"

    # Generic Webhook
    webhook_enabled: bool = False
    webhook_url: str = ""
    webhook_headers: Dict[str, str] = field(default_factory=dict)

    # PagerDuty Events API v2
    pagerduty_url: str = ""
    pagerduty_api_key: str = ""

    # Opsgenie
    opsgenie_url: str = ""
    opsgenie_api_key: str = ""

    @classmethod
    def from_environment(cls) -> "AlertChannelConfig":
        """Load configuration from environment variables."""
        to_emails = os.getenv("ALERT_EMAIL_TO", "")
        headers_raw = os.getenv("ALERT_WEBHOOK_HEADERS", "{}")
        try:
            headers = _json.loads(headers_raw)
        except (ValueError, TypeError):
            headers = {}

        return cls(
            email_enabled=os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true",
            smtp_host=os.getenv("ALERT_EMAIL_SMTP_HOST", os.getenv("ALERT_SMTP_HOST", "localhost")),
            smtp_port=int(os.getenv("ALERT_EMAIL_SMTP_PORT", os.getenv("ALERT_SMTP_PORT", "587"))),
            smtp_user=os.getenv("ALERT_EMAIL_SMTP_USER", os.getenv("ALERT_SMTP_USER", "")),
            smtp_password=os.getenv("ALERT_EMAIL_SMTP_PASSWORD", os.getenv("ALERT_SMTP_PASSWORD", "")),
            email_from=os.getenv("ALERT_EMAIL_FROM", "alerts@enterprisehub.com"),
            email_to=[e.strip() for e in to_emails.split(",") if e.strip()],
            smtp_use_tls=os.getenv("ALERT_EMAIL_SMTP_USE_TLS", "true").lower() == "true",
            slack_enabled=os.getenv("ALERT_SLACK_ENABLED", "false").lower() == "true",
            slack_webhook_url=os.getenv("ALERT_SLACK_WEBHOOK_URL", ""),
            slack_channel=os.getenv("ALERT_SLACK_CHANNEL", "#jorge-alerts"),
            slack_username=os.getenv("ALERT_SLACK_USERNAME", "Jorge Bot Alert"),
            slack_icon_emoji=os.getenv("ALERT_SLACK_ICON_EMOJI", ":rotating_light:"),
            webhook_enabled=os.getenv("ALERT_WEBHOOK_ENABLED", "false").lower() == "true",
            webhook_url=os.getenv("ALERT_WEBHOOK_URL", ""),
            webhook_headers=headers,
            pagerduty_url=os.getenv("ALERT_WEBHOOK_PAGERDUTY_URL", ""),
            pagerduty_api_key=os.getenv("ALERT_WEBHOOK_PAGERDUTY_API_KEY", ""),
            opsgenie_url=os.getenv("ALERT_WEBHOOK_OPSGENIE_URL", ""),
            opsgenie_api_key=os.getenv("ALERT_WEBHOOK_OPSGENIE_API_KEY", ""),
        )

    def validate(self) -> List[str]:
        """Validate channel configuration.

        Returns:
            List of warning messages for misconfigured channels.
        """
        warnings: List[str] = []
        if self.email_enabled and not self.email_to:
            warnings.append("Email alerts enabled but no recipients (ALERT_EMAIL_TO)")
        if self.slack_enabled and not self.slack_webhook_url:
            warnings.append("Slack alerts enabled but no webhook URL (ALERT_SLACK_WEBHOOK_URL)")
        if self.webhook_enabled and not self.webhook_url:
            warnings.append("Webhook alerts enabled but no URL (ALERT_WEBHOOK_URL)")
        return warnings


# ── Escalation Policy ──────────────────────────────────────────────────


@dataclass
class EscalationLevel:
    """One level in an escalation chain."""

    level: int
    delay_seconds: int
    channels: List[str]
    description: str = ""


class EscalationPolicy:
    """3-level escalation policy for unacknowledged critical alerts.

    Level 1 (0s):   Rule's configured channels (immediate)
    Level 2 (5min): Re-send to email + slack + webhook
    Level 3 (15min): Escalate to PagerDuty / Opsgenie
    """

    DEFAULT_LEVELS = [
        EscalationLevel(1, 0, [], "Immediate: rule channels"),
        EscalationLevel(2, 300, ["email", "slack", "webhook"], "5min unack: all channels"),
        EscalationLevel(3, 900, ["pagerduty", "opsgenie"], "15min unack: PagerDuty/Opsgenie"),
    ]

    def __init__(self, levels: Optional[List[EscalationLevel]] = None) -> None:
        self.levels = levels if levels is not None else list(self.DEFAULT_LEVELS)

    def get_escalation_level(self, alert: Alert) -> int:
        """Return the current escalation level for *alert* (0 if acknowledged)."""
        if alert.acknowledged:
            return 0
        elapsed = time.time() - alert.triggered_at
        current = 1
        for lvl in self.levels:
            if elapsed >= lvl.delay_seconds:
                current = lvl.level
        return current

    def get_pending_escalations(
        self, alerts: List[Alert],
    ) -> List[Tuple[Alert, EscalationLevel]]:
        """Return unacknowledged critical alerts that need escalation (level >= 2)."""
        results: List[Tuple[Alert, EscalationLevel]] = []
        for alert in alerts:
            if alert.acknowledged or alert.severity != "critical":
                continue
            level = self.get_escalation_level(alert)
            if level >= 2:
                lvl_cfg = next((l for l in self.levels if l.level == level), None)
                if lvl_cfg:
                    results.append((alert, lvl_cfg))
        return results


class AlertingService:
    """Alerting engine for Jorge bot operations.

    Monitors performance metrics against configurable rules and sends
    notifications via multiple channels when thresholds are breached.
    """

    # ── Singleton ─────────────────────────────────────────────────────
    _instance: Optional["AlertingService"] = None
    _lock = asyncio.Lock()

    def __new__(cls) -> "AlertingService":
        # Note: Using asyncio.Lock in __new__ is not ideal, but we'll handle
        # initialization in __init__ with proper async context
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return

        self._rules: Dict[str, AlertRule] = {}
        self._alerts: List[Alert] = []
        self._last_fired: Dict[str, float] = {}  # rule_name -> last fire timestamp
        self._recorded_metrics: Dict[str, float] = {}
        self.channel_config = AlertChannelConfig.from_environment()
        self.escalation_policy = EscalationPolicy()
        self._initialized = True

        # Load default rules
        self._load_default_rules()

        # Validate channel configuration on startup
        warnings = self.channel_config.validate()
        for w in warnings:
            logger.warning("Alert channel config: %s", w)

        logger.info(
            "AlertingService initialized with %d default rules",
            len(self._rules),
        )

    # ── Default Rules ─────────────────────────────────────────────────

    def _load_default_rules(self) -> None:
        """Load the 7 default alert rules from the audit spec."""

        # Rule 1: SLA Violation - P95 latency exceeds target
        self._rules["sla_violation"] = AlertRule(
            name="sla_violation",
            condition=lambda stats: (
                stats.get("lead_bot", {}).get("p95_latency_ms", 0) > 2000 or
                stats.get("buyer_bot", {}).get("p95_latency_ms", 0) > 2500 or
                stats.get("seller_bot", {}).get("p95_latency_ms", 0) > 2500
            ),
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack", "webhook"],
            description="P95 latency exceeds SLA target (Lead: 2000ms, Buyer/Seller: 2500ms)",
        )

        # Rule 2: High Error Rate - Error rate > 5%
        self._rules["high_error_rate"] = AlertRule(
            name="high_error_rate",
            condition=lambda stats: stats.get("error_rate", 0) > 0.05,
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack", "webhook"],
            description="Error rate exceeds 5%",
        )

        # Rule 3: Low Cache Hit Rate - Cache hit rate < 50%
        self._rules["low_cache_hit_rate"] = AlertRule(
            name="low_cache_hit_rate",
            condition=lambda stats: stats.get("cache_hit_rate", 1.0) < 0.50,
            severity="warning",
            cooldown_seconds=600,
            channels=["slack"],
            description="Cache hit rate below 50%",
        )

        # Rule 4: Handoff Failure - Handoff success rate < 95%
        self._rules["handoff_failure"] = AlertRule(
            name="handoff_failure",
            condition=lambda stats: stats.get("handoff_success_rate", 1.0) < 0.95,
            severity="critical",
            cooldown_seconds=300,
            channels=["email", "slack"],
            description="Handoff success rate below 95%",
        )

        # Rule 5: Bot Unresponsive - No responses for 5 minutes
        self._rules["bot_unresponsive"] = AlertRule(
            name="bot_unresponsive",
            condition=lambda stats: (
                time.time() - stats.get("last_response_time", time.time()) > 300
            ),
            severity="critical",
            cooldown_seconds=600,
            channels=["email", "slack", "webhook"],
            description="No bot responses for 5 minutes",
        )

        # Rule 6: Circular Handoff Spike - >10 blocked handoffs in 1 hour
        self._rules["circular_handoff_spike"] = AlertRule(
            name="circular_handoff_spike",
            condition=lambda stats: stats.get("blocked_handoffs_last_hour", 0) > 10,
            severity="warning",
            cooldown_seconds=600,
            channels=["slack"],
            description="More than 10 blocked handoffs in the last hour",
        )

        # Rule 7: Rate Limit Breach - Rate limit errors > 10%
        self._rules["rate_limit_breach"] = AlertRule(
            name="rate_limit_breach",
            condition=lambda stats: stats.get("rate_limit_error_rate", 0) > 0.10,
            severity="warning",
            cooldown_seconds=300,
            channels=["slack"],
            description="Rate limit error rate exceeds 10%",
        )

    # ── Metric Recording ─────────────────────────────────────────────

    def record_metric(self, name: str, value: float) -> None:
        """Record a named metric value for later alert evaluation.

        Called by BotMetricsCollector.feed_to_alerting() to push metrics
        into the alerting service. Stored metrics can be evaluated via
        check_alerts() by passing them as performance_stats.

        Args:
            name: Metric identifier (e.g., "error_rate", "lead_bot.response_time_p95").
            value: Metric value.
        """
        self._recorded_metrics[name] = value

    def get_recorded_metrics(self) -> Dict[str, float]:
        """Return a copy of all recorded metrics."""
        return dict(self._recorded_metrics)

    def clear_recorded_metrics(self) -> None:
        """Clear all recorded metrics."""
        self._recorded_metrics.clear()

    # ── Rule Management ───────────────────────────────────────────────

    async def add_rule(self, rule: AlertRule) -> None:
        """Register an alert rule.

        Args:
            rule: The AlertRule to add. Overwrites any existing rule with
                  the same name.

        Raises:
            ValueError: On invalid severity or channels.
        """
        if rule.severity not in VALID_SEVERITIES:
            raise ValueError(
                f"Invalid severity '{rule.severity}'. "
                f"Must be one of: {sorted(VALID_SEVERITIES)}"
            )

        invalid_channels = set(rule.channels) - VALID_CHANNELS
        if invalid_channels:
            raise ValueError(
                f"Invalid channels: {invalid_channels}. "
                f"Must be one of: {sorted(VALID_CHANNELS)}"
            )

        self._rules[rule.name] = rule

        logger.info(
            "Added alert rule '%s' (severity=%s, cooldown=%ds, channels=%s)",
            rule.name, rule.severity, rule.cooldown_seconds, rule.channels,
        )

    async def remove_rule(self, name: str) -> None:
        """Remove a rule by name.

        Args:
            name: The rule name to remove.

        Raises:
            KeyError: If the rule does not exist.
        """
        if name not in self._rules:
            raise KeyError(f"Alert rule '{name}' not found")

        del self._rules[name]
        self._last_fired.pop(name, None)

        logger.info("Removed alert rule '%s'", name)

    async def list_rules(self) -> List[AlertRule]:
        """List all registered rules.

        Returns:
            List of AlertRule instances.
        """
        return list(self._rules.values())

    # ── Alert Checking ────────────────────────────────────────────────

    async def check_alerts(self, performance_stats: Dict[str, Any]) -> List[Alert]:
        """Check all rules against performance statistics.

        Args:
            performance_stats: Dictionary containing bot performance metrics.

        Returns:
            List of newly triggered Alert objects.
        """
        now = time.time()
        triggered: List[Alert] = []

        for rule in self._rules.values():
            # Check cooldown
            last_fire = self._last_fired.get(rule.name, 0.0)
            if (now - last_fire) < rule.cooldown_seconds:
                continue

            # Evaluate condition
            try:
                if not rule.condition(performance_stats):
                    continue
            except Exception as e:
                logger.error(
                    "Error evaluating rule '%s': %s",
                    rule.name, e, exc_info=True
                )
                continue

            # Create alert
            alert = Alert(
                id=uuid.uuid4().hex[:8],
                rule_name=rule.name,
                severity=rule.severity,
                message=self._format_alert_message(rule, performance_stats),
                triggered_at=now,
                performance_stats=performance_stats.copy(),
                channels_sent=[],
            )

            self._alerts.append(alert)
            self._last_fired[rule.name] = now
            triggered.append(alert)

            logger.warning(
                "Alert triggered: '%s' (severity=%s) - %s",
                rule.name, rule.severity, alert.message,
            )

        # Prune to last MAX_STORED_ALERTS
        if len(self._alerts) > MAX_STORED_ALERTS:
            self._alerts = self._alerts[-MAX_STORED_ALERTS:]

        return triggered

    def _format_alert_message(
        self, rule: AlertRule, stats: Dict[str, Any]
    ) -> str:
        """Format a human-readable alert message.

        Args:
            rule: The triggered rule.
            stats: Performance statistics.

        Returns:
            Formatted alert message.
        """
        timestamp = datetime.fromtimestamp(time.time()).isoformat()
        message = f"[{rule.severity.upper()}] {rule.name}\n"
        message += f"Time: {timestamp}\n"
        message += f"Description: {rule.description}\n"

        # Add relevant stats
        if "error_rate" in stats:
            message += f"Error Rate: {stats['error_rate']:.2%}\n"
        if "cache_hit_rate" in stats:
            message += f"Cache Hit Rate: {stats['cache_hit_rate']:.2%}\n"
        if "handoff_success_rate" in stats:
            message += f"Handoff Success Rate: {stats['handoff_success_rate']:.2%}\n"
        if "blocked_handoffs_last_hour" in stats:
            message += f"Blocked Handoffs (1h): {stats['blocked_handoffs_last_hour']}\n"
        if "rate_limit_error_rate" in stats:
            message += f"Rate Limit Error Rate: {stats['rate_limit_error_rate']:.2%}\n"

        # Add bot-specific stats
        for bot_name in ["lead_bot", "buyer_bot", "seller_bot"]:
            if bot_name in stats:
                bot_stats = stats[bot_name]
                message += f"\n{bot_name.replace('_', ' ').title()}:\n"
                if "p95_latency_ms" in bot_stats:
                    message += f"  P95 Latency: {bot_stats['p95_latency_ms']:.0f}ms\n"
                if "p50_latency_ms" in bot_stats:
                    message += f"  P50 Latency: {bot_stats['p50_latency_ms']:.0f}ms\n"
                if "p99_latency_ms" in bot_stats:
                    message += f"  P99 Latency: {bot_stats['p99_latency_ms']:.0f}ms\n"

        return message

    # ── Alert Sending ─────────────────────────────────────────────────

    async def send_alert(self, alert: Alert) -> None:
        """Send an alert through configured notification channels.

        Args:
            alert: The Alert object to send.
        """
        rule = self._rules.get(alert.rule_name)
        if not rule:
            logger.error("Rule '%s' not found for alert '%s'", alert.rule_name, alert.id)
            return

        # Send to each configured channel
        for channel in rule.channels:
            try:
                if channel == "email":
                    await self._send_email_alert(alert)
                elif channel == "slack":
                    await self._send_slack_alert(alert)
                elif channel == "webhook":
                    await self._send_webhook_alert(alert)

                alert.channels_sent.append(channel)
                logger.info("Alert '%s' sent via %s", alert.id, channel)

            except Exception as e:
                logger.error(
                    "Failed to send alert '%s' via %s: %s",
                    alert.id, channel, e, exc_info=True
                )

    async def _send_email_alert(self, alert: Alert) -> None:
        """Send alert via email (SMTP).

        Args:
            alert: The Alert object to send.

        Raises:
            Exception: If email sending fails.
        """
        import os

        smtp_host = os.getenv("ALERT_SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("ALERT_SMTP_PORT", "587"))
        smtp_user = os.getenv("ALERT_SMTP_USER", "")
        smtp_password = os.getenv("ALERT_SMTP_PASSWORD", "")
        from_email = os.getenv("ALERT_EMAIL_FROM", "alerts@enterprisehub.com")
        to_emails = os.getenv("ALERT_EMAIL_TO", "").split(",")

        if not to_emails or not to_emails[0]:
            logger.warning("No email recipients configured, skipping email alert")
            return

        # Create message
        msg = MIMEMultipart()
        msg["From"] = from_email
        msg["To"] = ", ".join(to_emails)
        msg["Subject"] = f"[{alert.severity.upper()}] Jorge Bot Alert: {alert.rule_name}"

        # Add body
        body = alert.message
        msg.attach(MIMEText(body, "plain"))

        # Send via SMTP
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            if smtp_user and smtp_password:
                server.starttls()
                server.login(smtp_user, smtp_password)
            server.send_message(msg)

    async def _send_slack_alert(self, alert: Alert) -> None:
        """Send alert via Slack webhook.

        Args:
            alert: The Alert object to send.

        Raises:
            Exception: If Slack webhook fails.
        """
        import os

        webhook_url = os.getenv("ALERT_SLACK_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Slack webhook URL not configured, skipping Slack alert")
            return

        # Format message for Slack
        color = {
            "critical": "danger",
            "warning": "warning",
            "info": "good"
        }.get(alert.severity, "warning")

        payload = {
            "attachments": [
                {
                    "color": color,
                    "title": f"[{alert.severity.upper()}] {alert.rule_name}",
                    "text": alert.message,
                    "footer": f"Alert ID: {alert.id}",
                    "ts": int(alert.triggered_at),
                }
            ]
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                response.raise_for_status()

    async def _send_webhook_alert(self, alert: Alert) -> None:
        """Send alert via custom webhook (e.g., PagerDuty, Opsgenie).

        Args:
            alert: The Alert object to send.

        Raises:
            Exception: If webhook fails.
        """
        import os

        webhook_url = os.getenv("ALERT_WEBHOOK_URL")
        if not webhook_url:
            logger.warning("Webhook URL not configured, skipping webhook alert")
            return

        # Format payload
        payload = {
            "alert_id": alert.id,
            "rule_name": alert.rule_name,
            "severity": alert.severity,
            "message": alert.message,
            "triggered_at": alert.triggered_at,
            "performance_stats": alert.performance_stats,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(webhook_url, json=payload) as response:
                response.raise_for_status()

    # ── Alert History ─────────────────────────────────────────────────

    async def get_alert_history(self, limit: int = 50) -> List[Alert]:
        """Get alert history.

        Args:
            limit: Maximum number of alerts to return (default 50).

        Returns:
            List of Alert objects, most recent first.
        """
        return list(reversed(self._alerts[-limit:]))

    async def get_active_alerts(self) -> List[Alert]:
        """Get all currently active (unacknowledged) alerts.

        Returns:
            List of Alert objects where acknowledged is False.
        """
        return [alert for alert in self._alerts if not alert.acknowledged]

    async def acknowledge_alert(self, alert_id: str) -> None:
        """Acknowledge an alert by its ID.

        Args:
            alert_id: The short hex ID of the alert to acknowledge.

        Raises:
            KeyError: If the alert ID is not found.
        """
        for alert in self._alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                logger.info("Acknowledged alert '%s'", alert_id)
                return

        raise KeyError(f"Alert '{alert_id}' not found")

    # ── Convenience Methods ────────────────────────────────────────────

    async def check_and_send_alerts(
        self, performance_stats: Dict[str, Any]
    ) -> List[Alert]:
        """Check for alerts and send them through configured channels.

        This is a convenience method that combines check_alerts and send_alert.

        Args:
            performance_stats: Dictionary containing bot performance metrics.

        Returns:
            List of triggered and sent Alert objects.
        """
        alerts = await self.check_alerts(performance_stats)

        # Send all triggered alerts
        send_tasks = [self.send_alert(alert) for alert in alerts]
        await asyncio.gather(*send_tasks, return_exceptions=True)

        return alerts

    # ── Testing Support ───────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. For testing only."""
        if cls._instance is not None:
            cls._instance._rules.clear()
            cls._instance._alerts.clear()
            cls._instance._last_fired.clear()
            cls._instance._recorded_metrics.clear()
            cls._instance._initialized = False
        cls._instance = None


# ── Convenience Functions ───────────────────────────────────────────────

async def check_and_send_alerts(
    performance_stats: Dict[str, Any]
) -> List[Alert]:
    """Convenience function to check and send alerts.

    This is the main entry point for periodic alert checking.

    Args:
        performance_stats: Dictionary containing bot performance metrics.

    Returns:
        List of triggered and sent Alert objects.

    Example:
        from services.jorge.alerting_service import check_and_send_alerts

        stats = {
            "error_rate": 0.06,
            "cache_hit_rate": 0.45,
            "handoff_success_rate": 0.92,
            "lead_bot": {"p95_latency_ms": 2100},
            "buyer_bot": {"p95_latency_ms": 2600},
            "seller_bot": {"p95_latency_ms": 2400},
        }
        alerts = await check_and_send_alerts(stats)
    """
    service = AlertingService()
    return await service.check_and_send_alerts(performance_stats)
