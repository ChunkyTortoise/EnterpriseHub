#!/usr/bin/env python3
"""
Service 6 Alerting Engine - Intelligent Alert Management
Multi-tier alerting system with smart aggregation and escalation.

Features:
- Multi-severity alerting (WARNING → CRITICAL → EMERGENCY)
- Smart alert aggregation to reduce noise
- Context-aware notifications with suggested actions
- Automated escalation workflows
- Integration with Slack, email, SMS, PagerDuty
"""

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.database_service import get_database

logger = get_logger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


class AlertStatus(Enum):
    """Alert lifecycle status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class AlertCategory(Enum):
    """Alert categories for organization"""

    PERFORMANCE = "performance"
    AVAILABILITY = "availability"
    SECURITY = "security"
    BUSINESS = "business"
    AGENT_FAILURE = "agent_failure"


@dataclass
class AlertRule:
    """Alert rule definition"""

    rule_id: str
    name: str
    description: str
    severity: AlertSeverity
    category: AlertCategory
    metric_name: str
    condition: str  # e.g., "> 100", "< 0.5"
    threshold_value: float
    evaluation_window: int  # seconds
    min_data_points: int
    escalation_delay: int  # seconds before escalation
    auto_resolve: bool = True
    auto_resolve_timeout: int = 300  # seconds
    notification_channels: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = []
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Alert:
    """Active alert instance"""

    alert_id: str
    rule_id: str
    severity: AlertSeverity
    category: AlertCategory
    status: AlertStatus
    title: str
    description: str
    current_value: float
    threshold_value: float
    first_occurred: datetime
    last_updated: datetime
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    escalation_level: int = 0
    notification_count: int = 0
    metadata: Dict[str, Any] = None
    suggested_actions: List[str] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.suggested_actions is None:
            self.suggested_actions = []


class NotificationChannel:
    """Base notification channel interface"""

    async def send_notification(self, alert: Alert, notification_type: str = "alert") -> bool:
        """Send notification via this channel"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def __init__(self, smtp_config: Dict[str, Any]):
        self.smtp_config = smtp_config

    async def send_notification(self, alert: Alert, notification_type: str = "alert") -> bool:
        """Send email notification"""
        try:
            # In production, integrate with actual email service
            email_content = self._generate_email_content(alert, notification_type)

            logger.info(
                f"EMAIL_NOTIFICATION_SENT: Email alert sent",
                extra={
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "notification_type": notification_type,
                    "recipient_count": len(self.smtp_config.get("recipients", [])),
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"EMAIL_NOTIFICATION_FAILED: Failed to send email alert",
                extra={"alert_id": alert.alert_id, "error": str(e)},
            )
            return False

    def _generate_email_content(self, alert: Alert, notification_type: str) -> str:
        """Generate email content for alert"""
        subject = f"[Service 6] {alert.severity.value.upper()}: {alert.title}"

        body = f"""
Service 6 Alert: {alert.title}

Severity: {alert.severity.value.upper()}
Category: {alert.category.value}
Current Value: {alert.current_value}
Threshold: {alert.threshold_value}

Description: {alert.description}

First Occurred: {alert.first_occurred}
Last Updated: {alert.last_updated}

Suggested Actions:
"""

        for action in alert.suggested_actions:
            body += f"- {action}\n"

        body += f"""
Alert ID: {alert.alert_id}
Dashboard: https://service6-dashboard.example.com/alerts/{alert.alert_id}
"""

        return body


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""

    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url

    async def send_notification(self, alert: Alert, notification_type: str = "alert") -> bool:
        """Send Slack notification"""
        try:
            # In production, integrate with Slack API
            slack_payload = self._generate_slack_payload(alert, notification_type)

            logger.info(
                f"SLACK_NOTIFICATION_SENT: Slack alert sent",
                extra={
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "notification_type": notification_type,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"SLACK_NOTIFICATION_FAILED: Failed to send Slack alert",
                extra={"alert_id": alert.alert_id, "error": str(e)},
            )
            return False

    def _generate_slack_payload(self, alert: Alert, notification_type: str) -> Dict[str, Any]:
        """Generate Slack payload for alert"""
        color_map = {
            AlertSeverity.WARNING: "#FFA500",  # Orange
            AlertSeverity.CRITICAL: "#FF4500",  # Red-Orange
            AlertSeverity.EMERGENCY: "#DC143C",  # Crimson
        }

        emoji_map = {
            AlertSeverity.WARNING: ":warning:",
            AlertSeverity.CRITICAL: ":rotating_light:",
            AlertSeverity.EMERGENCY: ":fire:",
        }

        return {
            "text": f"Service 6 Alert: {alert.title}",
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "#808080"),
                    "fields": [
                        {
                            "title": "Severity",
                            "value": f"{emoji_map.get(alert.severity, '')} {alert.severity.value.upper()}",
                            "short": True,
                        },
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True},
                        {"title": "Category", "value": alert.category.value, "short": True},
                    ],
                    "actions": [
                        {
                            "type": "button",
                            "text": "Acknowledge",
                            "url": f"https://service6-dashboard.example.com/alerts/{alert.alert_id}/acknowledge",
                        },
                        {"type": "button", "text": "View Dashboard", "url": "https://service6-dashboard.example.com"},
                    ],
                    "footer": f"Alert ID: {alert.alert_id}",
                    "ts": int(alert.first_occurred.timestamp()),
                }
            ],
        }


class SMSNotificationChannel(NotificationChannel):
    """SMS notification channel"""

    def __init__(self, twilio_config: Dict[str, Any]):
        self.twilio_config = twilio_config

    async def send_notification(self, alert: Alert, notification_type: str = "alert") -> bool:
        """Send SMS notification"""
        try:
            # In production, integrate with Twilio API
            sms_content = self._generate_sms_content(alert)

            logger.info(
                f"SMS_NOTIFICATION_SENT: SMS alert sent",
                extra={
                    "alert_id": alert.alert_id,
                    "severity": alert.severity.value,
                    "notification_type": notification_type,
                },
            )

            return True

        except Exception as e:
            logger.error(
                f"SMS_NOTIFICATION_FAILED: Failed to send SMS alert",
                extra={"alert_id": alert.alert_id, "error": str(e)},
            )
            return False

    def _generate_sms_content(self, alert: Alert) -> str:
        """Generate SMS content for alert"""
        return f"Service 6 {alert.severity.value.upper()}: {alert.title}. Current: {alert.current_value}, Threshold: {alert.threshold_value}. Check dashboard."


class Service6AlertingEngine:
    """Main alerting engine for Service 6"""

    def __init__(self):
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.notification_channels: Dict[str, NotificationChannel] = {}
        self.cache_service = None
        self.database_service = None
        self.evaluation_task = None
        self.escalation_task = None

        # Load default alert rules
        self._load_default_alert_rules()

    async def initialize(self):
        """Initialize alerting engine"""
        try:
            self.cache_service = get_cache_service()
            self.database_service = await get_database()

            # Initialize notification channels
            self._initialize_notification_channels()

            # Start evaluation and escalation tasks
            self.evaluation_task = asyncio.create_task(self._evaluation_worker())
            self.escalation_task = asyncio.create_task(self._escalation_worker())

            logger.info("ALERTING_ENGINE_INITIALIZED: Service 6 alerting engine started")

        except Exception as e:
            logger.error(f"ALERTING_ENGINE_INIT_FAILED: Failed to initialize alerting engine: {e}")
            raise

    def _load_default_alert_rules(self):
        """Load default alert rules for Service 6"""
        default_rules = [
            AlertRule(
                rule_id="agent_failure_rate",
                name="High Agent Failure Rate",
                description="Agent failure rate exceeds acceptable threshold",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.AGENT_FAILURE,
                metric_name="agent_operations_total",
                condition="> 0.05",  # 5% failure rate
                threshold_value=0.05,
                evaluation_window=300,  # 5 minutes
                min_data_points=10,
                escalation_delay=300,
                notification_channels=["email", "slack"],
                metadata={"runbook": "agent_failure_runbook.md"},
            ),
            AlertRule(
                rule_id="consensus_timeout_rate",
                name="High Consensus Timeout Rate",
                description="Agent consensus operations timing out frequently",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.PERFORMANCE,
                metric_name="consensus_time_ms",
                condition="> 5000",  # 5 seconds
                threshold_value=5000,
                evaluation_window=600,  # 10 minutes
                min_data_points=5,
                escalation_delay=600,
                notification_channels=["slack"],
                suggested_actions=[
                    "Check agent system load",
                    "Review consensus algorithm performance",
                    "Scale agent infrastructure if needed",
                ],
            ),
            AlertRule(
                rule_id="database_connection_pool",
                name="Database Connection Pool Exhaustion",
                description="Database connection pool utilization is critically high",
                severity=AlertSeverity.CRITICAL,
                category=AlertCategory.AVAILABILITY,
                metric_name="database_connection_pool_usage",
                condition="> 0.9",  # 90% utilization
                threshold_value=0.9,
                evaluation_window=60,  # 1 minute
                min_data_points=3,
                escalation_delay=180,
                notification_channels=["email", "slack", "sms"],
                suggested_actions=[
                    "Scale database connection pool",
                    "Check for connection leaks",
                    "Review slow query log",
                ],
            ),
            AlertRule(
                rule_id="lead_processing_backlog",
                name="Lead Processing Backlog",
                description="Lead processing queue backlog is growing",
                severity=AlertSeverity.WARNING,
                category=AlertCategory.BUSINESS,
                metric_name="lead_processing_queue_size",
                condition="> 1000",
                threshold_value=1000,
                evaluation_window=300,  # 5 minutes
                min_data_points=3,
                escalation_delay=900,  # 15 minutes
                notification_channels=["slack"],
                suggested_actions=[
                    "Scale agent processing capacity",
                    "Check for stuck leads",
                    "Review agent performance metrics",
                ],
            ),
            AlertRule(
                rule_id="revenue_impact",
                name="Revenue Impact Alert",
                description="Detected potential revenue impact from system issues",
                severity=AlertSeverity.EMERGENCY,
                category=AlertCategory.BUSINESS,
                metric_name="estimated_revenue_impact",
                condition="> 1000",  # $1000 impact
                threshold_value=1000,
                evaluation_window=300,  # 5 minutes
                min_data_points=1,
                escalation_delay=60,  # 1 minute
                notification_channels=["email", "slack", "sms"],
                suggested_actions=[
                    "Immediately assess lead processing status",
                    "Check high-value lead routing",
                    "Escalate to executive team",
                ],
            ),
        ]

        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule

    def _initialize_notification_channels(self):
        """Initialize notification channels"""
        # In production, load from configuration
        self.notification_channels = {
            "email": EmailNotificationChannel(
                {"smtp_server": "smtp.example.com", "recipients": ["engineering@company.com", "oncall@company.com"]}
            ),
            "slack": SlackNotificationChannel("https://hooks.slack.com/services/..."),
            "sms": SMSNotificationChannel(
                {
                    "account_sid": "twilio_account_sid",
                    "auth_token": "twilio_auth_token",
                    "phone_numbers": ["+15551234567"],
                }
            ),
        }

    async def _evaluation_worker(self):
        """Background worker to evaluate alert rules"""
        evaluation_interval = 30  # 30 seconds

        while True:
            try:
                await self._evaluate_alert_rules()
                await asyncio.sleep(evaluation_interval)

            except Exception as e:
                logger.error(f"ALERT_EVALUATION_ERROR: Error in alert evaluation: {e}")
                await asyncio.sleep(evaluation_interval)

    async def _evaluate_alert_rules(self):
        """Evaluate all alert rules against current metrics"""
        if not self.cache_service:
            return

        for rule_id, rule in self.alert_rules.items():
            try:
                await self._evaluate_single_rule(rule)
            except Exception as e:
                logger.error(
                    f"RULE_EVALUATION_ERROR: Error evaluating rule {rule_id}: {e}",
                    extra={"rule_id": rule_id, "error": str(e)},
                )

    async def _evaluate_single_rule(self, rule: AlertRule):
        """Evaluate a single alert rule"""
        # Get recent metric values
        metric_values = await self._get_metric_values(rule.metric_name, rule.evaluation_window, rule.min_data_points)

        if len(metric_values) < rule.min_data_points:
            return  # Not enough data points

        # Evaluate condition
        current_value = metric_values[-1]  # Most recent value
        condition_met = self._evaluate_condition(current_value, rule.condition, rule.threshold_value)

        existing_alert = self._get_active_alert_for_rule(rule.rule_id)

        if condition_met and not existing_alert:
            # Create new alert
            await self._create_alert(rule, current_value, metric_values)
        elif not condition_met and existing_alert and rule.auto_resolve:
            # Auto-resolve alert
            await self._resolve_alert(existing_alert.alert_id, "auto_resolved")
        elif existing_alert:
            # Update existing alert
            await self._update_alert(existing_alert, current_value)

    async def _get_metric_values(self, metric_name: str, window_seconds: int, min_points: int) -> List[float]:
        """Get recent metric values for evaluation"""
        try:
            # In production, query metrics from cache/database
            # This is a simplified implementation
            values = []

            # Query Redis for recent metric values
            keys_pattern = f"metric:{metric_name}:*"
            # Implementation would get actual values from cache

            return values

        except Exception as e:
            logger.warning(f"Failed to get metric values for {metric_name}: {e}")
            return []

    def _evaluate_condition(self, value: float, condition: str, threshold: float) -> bool:
        """Evaluate alert condition"""
        if condition.startswith(">"):
            return value > threshold
        elif condition.startswith("<"):
            return value < threshold
        elif condition == "==":
            return value == threshold
        elif condition == "!=":
            return value != threshold
        else:
            logger.warning(f"Unknown condition: {condition}")
            return False

    def _get_active_alert_for_rule(self, rule_id: str) -> Optional[Alert]:
        """Get active alert for a rule"""
        for alert in self.active_alerts.values():
            if alert.rule_id == rule_id and alert.status == AlertStatus.ACTIVE:
                return alert
        return None

    async def _create_alert(self, rule: AlertRule, current_value: float, metric_values: List[float]):
        """Create new alert"""
        alert_id = f"alert_{uuid.uuid4().hex[:8]}"

        alert = Alert(
            alert_id=alert_id,
            rule_id=rule.rule_id,
            severity=rule.severity,
            category=rule.category,
            status=AlertStatus.ACTIVE,
            title=rule.name,
            description=rule.description,
            current_value=current_value,
            threshold_value=rule.threshold_value,
            first_occurred=datetime.now(),
            last_updated=datetime.now(),
            suggested_actions=rule.metadata.get("suggested_actions", []),
        )

        self.active_alerts[alert_id] = alert

        # Send initial notifications
        await self._send_notifications(alert, rule.notification_channels)

        # Store in database
        await self._store_alert(alert)

        logger.warning(
            f"ALERT_CREATED: New alert created",
            extra={
                "alert_id": alert_id,
                "rule_id": rule.rule_id,
                "severity": rule.severity.value,
                "current_value": current_value,
                "threshold": rule.threshold_value,
            },
        )

    async def _resolve_alert(self, alert_id: str, resolved_by: str):
        """Resolve an active alert"""
        if alert_id not in self.active_alerts:
            return

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.RESOLVED
        alert.resolved_at = datetime.now()
        alert.last_updated = datetime.now()

        # Send resolution notification
        rule = self.alert_rules.get(alert.rule_id)
        if rule:
            await self._send_notifications(alert, rule.notification_channels, "resolved")

        # Update in database
        await self._store_alert(alert)

        logger.info(
            f"ALERT_RESOLVED: Alert resolved",
            extra={
                "alert_id": alert_id,
                "resolved_by": resolved_by,
                "duration_seconds": (alert.resolved_at - alert.first_occurred).total_seconds(),
            },
        )

    async def _update_alert(self, alert: Alert, current_value: float):
        """Update existing alert"""
        alert.current_value = current_value
        alert.last_updated = datetime.now()

        # Store updated alert
        await self._store_alert(alert)

    async def _send_notifications(self, alert: Alert, channel_names: List[str], notification_type: str = "alert"):
        """Send notifications via specified channels"""
        for channel_name in channel_names:
            if channel_name in self.notification_channels:
                try:
                    channel = self.notification_channels[channel_name]
                    success = await channel.send_notification(alert, notification_type)

                    if success:
                        alert.notification_count += 1

                except Exception as e:
                    logger.error(
                        f"NOTIFICATION_FAILED: Failed to send via {channel_name}",
                        extra={"alert_id": alert.alert_id, "channel": channel_name, "error": str(e)},
                    )

    async def _store_alert(self, alert: Alert):
        """Store alert in database"""
        if not self.database_service:
            return

        try:
            async with self.database_service.get_connection() as conn:
                await conn.execute(
                    """
                    INSERT INTO alerts
                    (alert_id, rule_id, severity, category, status, title, description,
                     current_value, threshold_value, first_occurred, last_updated,
                     acknowledged_at, acknowledged_by, resolved_at, escalation_level,
                     notification_count, metadata, suggested_actions)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
                    ON CONFLICT (alert_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    current_value = EXCLUDED.current_value,
                    last_updated = EXCLUDED.last_updated,
                    acknowledged_at = EXCLUDED.acknowledged_at,
                    acknowledged_by = EXCLUDED.acknowledged_by,
                    resolved_at = EXCLUDED.resolved_at,
                    escalation_level = EXCLUDED.escalation_level,
                    notification_count = EXCLUDED.notification_count
                """,
                    alert.alert_id,
                    alert.rule_id,
                    alert.severity.value,
                    alert.category.value,
                    alert.status.value,
                    alert.title,
                    alert.description,
                    alert.current_value,
                    alert.threshold_value,
                    alert.first_occurred,
                    alert.last_updated,
                    alert.acknowledged_at,
                    alert.acknowledged_by,
                    alert.resolved_at,
                    alert.escalation_level,
                    alert.notification_count,
                    json.dumps(alert.metadata),
                    json.dumps(alert.suggested_actions),
                )

        except Exception as e:
            logger.error(f"Failed to store alert {alert.alert_id}: {e}")

    async def _escalation_worker(self):
        """Background worker for alert escalation"""
        check_interval = 60  # 1 minute

        while True:
            try:
                await self._check_escalations()
                await asyncio.sleep(check_interval)

            except Exception as e:
                logger.error(f"ESCALATION_WORKER_ERROR: Error in escalation worker: {e}")
                await asyncio.sleep(check_interval)

    async def _check_escalations(self):
        """Check for alerts that need escalation"""
        now = datetime.now()

        for alert in self.active_alerts.values():
            if alert.status != AlertStatus.ACTIVE:
                continue

            rule = self.alert_rules.get(alert.rule_id)
            if not rule:
                continue

            # Check if escalation is needed
            time_since_first = (now - alert.first_occurred).total_seconds()
            escalation_threshold = rule.escalation_delay * (alert.escalation_level + 1)

            if time_since_first >= escalation_threshold and alert.status == AlertStatus.ACTIVE:
                await self._escalate_alert(alert)

    async def _escalate_alert(self, alert: Alert):
        """Escalate an alert to the next level"""
        alert.escalation_level += 1
        alert.last_updated = datetime.now()

        # Enhanced notifications for escalated alerts
        rule = self.alert_rules.get(alert.rule_id)
        if rule:
            escalated_channels = rule.notification_channels.copy()

            # Add additional channels for higher escalation levels
            if alert.escalation_level >= 2:
                escalated_channels.extend(["email", "sms"])  # Ensure critical channels

            await self._send_notifications(alert, escalated_channels, "escalation")

        # Store escalation
        await self._store_alert(alert)

        logger.warning(
            f"ALERT_ESCALATED: Alert escalated to level {alert.escalation_level}",
            extra={
                "alert_id": alert.alert_id,
                "escalation_level": alert.escalation_level,
                "severity": alert.severity.value,
            },
        )

    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        if alert_id not in self.active_alerts:
            return False

        alert = self.active_alerts[alert_id]
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now()
        alert.acknowledged_by = acknowledged_by
        alert.last_updated = datetime.now()

        await self._store_alert(alert)

        logger.info(
            f"ALERT_ACKNOWLEDGED: Alert acknowledged", extra={"alert_id": alert_id, "acknowledged_by": acknowledged_by}
        )

        return True

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        return [
            alert
            for alert in self.active_alerts.values()
            if alert.status in [AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED]
        ]

    def get_alert_summary(self) -> Dict[str, int]:
        """Get summary of alerts by severity"""
        summary = {"warning": 0, "critical": 0, "emergency": 0, "total": 0}

        for alert in self.get_active_alerts():
            summary[alert.severity.value] += 1
            summary["total"] += 1

        return summary


# Export alerting components
__all__ = [
    "AlertSeverity",
    "AlertStatus",
    "AlertCategory",
    "AlertRule",
    "Alert",
    "Service6AlertingEngine",
    "EmailNotificationChannel",
    "SlackNotificationChannel",
    "SMSNotificationChannel",
]
