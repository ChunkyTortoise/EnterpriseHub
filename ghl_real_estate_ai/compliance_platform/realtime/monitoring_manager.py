"""
Real-Time Compliance Monitoring Manager

Orchestrates all real-time monitoring components for enterprise compliance:
- WebSocket server for live dashboard updates
- Redis pub/sub for event distribution
- Notification services for alerts
- Metrics collection and caching
- Threshold-based alerting with cooldown

Supports EU AI Act, SEC AI Guidance, HIPAA, and GDPR monitoring.
"""

import asyncio
import json
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

import redis.asyncio as redis
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


# =============================================================================
# Models
# =============================================================================


class ThresholdOperator(str, Enum):
    """Comparison operators for threshold evaluation."""

    LT = "lt"  # Less than
    GT = "gt"  # Greater than
    EQ = "eq"  # Equal to
    LTE = "lte"  # Less than or equal
    GTE = "gte"  # Greater than or equal
    NEQ = "neq"  # Not equal


class AlertSeverity(str, Enum):
    """Alert severity levels."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class AlertStatus(str, Enum):
    """Alert status tracking."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class MonitoringThreshold(BaseModel):
    """
    Threshold definition for compliance metrics monitoring.

    Defines when to trigger an alert based on metric values.
    """

    metric: str = Field(..., description="Metric name, e.g., 'compliance_score', 'violation_count'")
    operator: ThresholdOperator = Field(..., description="Comparison operator")
    value: float = Field(..., description="Threshold value to compare against")
    severity: AlertSeverity = Field(default=AlertSeverity.MEDIUM, description="Alert severity if triggered")
    notification_channels: List[str] = Field(
        default_factory=lambda: ["websocket", "email"], description="Channels to notify: websocket, email, slack, sms"
    )
    cooldown_minutes: int = Field(default=60, ge=0, description="Minimum minutes between re-triggering the same alert")
    description: Optional[str] = Field(default=None, description="Human-readable description")

    def evaluate(self, actual_value: float) -> bool:
        """Evaluate if the threshold is breached."""
        operators = {
            ThresholdOperator.LT: lambda a, b: a < b,
            ThresholdOperator.GT: lambda a, b: a > b,
            ThresholdOperator.EQ: lambda a, b: abs(a - b) < 0.001,
            ThresholdOperator.LTE: lambda a, b: a <= b,
            ThresholdOperator.GTE: lambda a, b: a >= b,
            ThresholdOperator.NEQ: lambda a, b: abs(a - b) >= 0.001,
        }
        return operators[self.operator](actual_value, self.value)


class MonitoringRule(BaseModel):
    """
    Monitoring rule that groups thresholds with configuration.

    Rules can target specific models or apply globally.
    """

    id: str = Field(default_factory=lambda: f"rule_{uuid4().hex[:12]}")
    name: str = Field(..., description="Rule name for identification")
    description: str = Field(..., description="Detailed description of what this rule monitors")
    enabled: bool = Field(default=True, description="Whether the rule is active")
    model_ids: List[str] = Field(default_factory=list, description="Target model IDs. Empty list means all models.")
    thresholds: List[MonitoringThreshold] = Field(default_factory=list, description="Thresholds that trigger alerts")
    check_interval_seconds: int = Field(default=300, ge=10, description="How often to check this rule (seconds)")
    last_triggered: Optional[datetime] = Field(default=None, description="Last time this rule triggered")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: str = Field(default="system")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")


class ComplianceMetrics(BaseModel):
    """
    Real-time compliance metrics snapshot for a model.

    Provides current state and trend information.
    """

    model_id: str
    model_name: str
    compliance_score: float = Field(ge=0, le=100)
    risk_level: str = Field(description="minimal, limited, high, unacceptable")
    violation_count: int = Field(ge=0)
    critical_violations: int = Field(ge=0)
    high_violations: int = Field(default=0, ge=0)
    pending_remediations: int = Field(ge=0)
    last_assessment: datetime
    score_trend: str = Field(default="stable", description="Score trend: improving, stable, declining")
    score_change_24h: float = Field(default=0.0, description="Score change in last 24 hours")
    regulation_scores: Dict[str, float] = Field(default_factory=dict)
    category_scores: Dict[str, float] = Field(default_factory=dict)
    certifications_expiring_30d: int = Field(default=0)
    days_since_assessment: int = Field(default=0)
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ComplianceAlert(BaseModel):
    """
    Alert generated from monitoring threshold breach.
    """

    alert_id: str = Field(default_factory=lambda: f"alert_{uuid4().hex[:12]}")
    rule_id: str
    rule_name: str
    threshold: MonitoringThreshold
    model_id: str
    model_name: str
    severity: AlertSeverity
    status: AlertStatus = Field(default=AlertStatus.ACTIVE)
    title: str
    message: str
    metric_value: float
    threshold_value: float
    triggered_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# =============================================================================
# Monitoring Manager
# =============================================================================


class RealTimeMonitoringManager:
    """
    Orchestrates real-time compliance monitoring.

    Connects WebSocket server, Redis pub/sub, and notification services
    to provide comprehensive real-time monitoring capabilities.

    Features:
    - Configurable monitoring rules with thresholds
    - Metrics caching for fast queries
    - Cooldown periods to prevent alert fatigue
    - Alert acknowledgment tracking
    - Background monitoring loops
    - Event-driven reactions
    - Default sensible rules
    """

    # Redis channel names
    CHANNEL_ALERTS = "compliance:alerts"
    CHANNEL_METRICS = "compliance:metrics"
    CHANNEL_EVENTS = "compliance:events"

    # Cache key prefixes
    CACHE_METRICS = "compliance:metrics:cache"
    CACHE_ALERTS = "compliance:alerts:history"
    CACHE_COOLDOWNS = "compliance:cooldowns"

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        enable_websocket: bool = True,
        enable_notifications: bool = True,
        check_interval: int = 60,
        metrics_ttl: int = 300,
        alert_history_limit: int = 1000,
    ):
        """
        Initialize the Real-Time Monitoring Manager.

        Args:
            redis_url: Redis connection URL
            enable_websocket: Enable WebSocket broadcasting
            enable_notifications: Enable external notifications (email, slack)
            check_interval: Default interval for metrics collection (seconds)
            metrics_ttl: How long to cache metrics (seconds)
            alert_history_limit: Maximum alerts to keep in history
        """
        self.redis_url = redis_url
        self.enable_websocket = enable_websocket
        self.enable_notifications = enable_notifications
        self.check_interval = check_interval
        self.metrics_ttl = metrics_ttl
        self.alert_history_limit = alert_history_limit

        # Internal state
        self._rules: Dict[str, MonitoringRule] = {}
        self._metrics_cache: Dict[str, ComplianceMetrics] = {}
        self._alert_history: List[ComplianceAlert] = []
        self._cooldowns: Dict[str, datetime] = {}  # rule:model -> last_triggered
        self._running: bool = False
        self._tasks: List[asyncio.Task] = []

        # Redis connections (initialized lazily)
        self._redis: Optional[redis.Redis] = None
        self._pubsub: Optional[redis.client.PubSub] = None

        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {
            "assessment_completed": [],
            "violation_detected": [],
            "score_changed": [],
            "remediation_completed": [],
            "certification_expiring": [],
        }

        # Notification callback (to be set by consumer)
        self._notification_callback: Optional[Callable] = None

        # WebSocket broadcast callback (to be set by websocket server)
        self._websocket_broadcast: Optional[Callable] = None

        # Compliance service reference (to be injected)
        self._compliance_service = None

        logger.info(
            "RealTimeMonitoringManager initialized",
            extra={
                "redis_url": redis_url,
                "check_interval": check_interval,
                "websocket_enabled": enable_websocket,
                "notifications_enabled": enable_notifications,
            },
        )

    # =========================================================================
    # Lifecycle Management
    # =========================================================================

    async def start(self) -> None:
        """
        Start all monitoring components.

        Initializes Redis connections and starts background tasks for:
        - Metrics collection loop
        - Threshold checking loop
        - Redis event subscriber
        """
        if self._running:
            logger.warning("Monitoring manager already running")
            return

        try:
            # Initialize Redis connection
            self._redis = redis.from_url(self.redis_url, encoding="utf-8", decode_responses=True)
            await self._redis.ping()
            logger.info("Redis connection established")

            # Initialize pub/sub
            self._pubsub = self._redis.pubsub()
            await self._pubsub.subscribe(
                self.CHANNEL_EVENTS,
                self.CHANNEL_ALERTS,
            )

            self._running = True

            # Start background tasks
            self._tasks = [
                asyncio.create_task(self._metrics_collection_loop()),
                asyncio.create_task(self._threshold_check_loop()),
                asyncio.create_task(self._event_subscriber_loop()),
                asyncio.create_task(self._cleanup_loop()),
            ]

            logger.info("Monitoring manager started with background tasks")

        except redis.ConnectionError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to start monitoring manager: {e}")
            raise

    async def stop(self) -> None:
        """
        Gracefully stop all monitoring components.
        """
        if not self._running:
            return

        logger.info("Stopping monitoring manager...")
        self._running = False

        # Cancel background tasks
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        self._tasks.clear()

        # Close Redis connections
        if self._pubsub:
            await self._pubsub.unsubscribe()
            await self._pubsub.close()
            self._pubsub = None

        if self._redis:
            await self._redis.close()
            self._redis = None

        logger.info("Monitoring manager stopped")

    @property
    def is_running(self) -> bool:
        """Check if monitoring manager is running."""
        return self._running

    # =========================================================================
    # Configuration
    # =========================================================================

    def set_compliance_service(self, service) -> None:
        """
        Inject compliance service reference for metrics collection.

        Args:
            service: ComplianceService instance
        """
        self._compliance_service = service
        logger.debug("Compliance service injected")

    def set_notification_callback(self, callback: Callable) -> None:
        """
        Set callback for external notifications.

        Args:
            callback: Async callable(alert: ComplianceAlert, channels: List[str])
        """
        self._notification_callback = callback
        logger.debug("Notification callback configured")

    def set_websocket_broadcast(self, broadcast: Callable) -> None:
        """
        Set WebSocket broadcast function.

        Args:
            broadcast: Async callable(message: dict)
        """
        self._websocket_broadcast = broadcast
        logger.debug("WebSocket broadcast configured")

    def register_event_handler(self, event_type: str, handler: Callable) -> None:
        """
        Register handler for specific event types.

        Args:
            event_type: Event type (assessment_completed, violation_detected, etc.)
            handler: Async callable to handle the event
        """
        if event_type not in self._event_handlers:
            self._event_handlers[event_type] = []
        self._event_handlers[event_type].append(handler)
        logger.debug(f"Handler registered for event: {event_type}")

    # =========================================================================
    # Rule Management
    # =========================================================================

    def add_rule(self, rule: MonitoringRule) -> bool:
        """
        Add a monitoring rule.

        Args:
            rule: MonitoringRule to add

        Returns:
            True if added successfully, False if rule ID already exists
        """
        if rule.id in self._rules:
            logger.warning(f"Rule {rule.id} already exists")
            return False

        self._rules[rule.id] = rule
        logger.info(f"Monitoring rule added: {rule.name} ({rule.id})")
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """
        Remove a monitoring rule.

        Args:
            rule_id: Rule ID to remove

        Returns:
            True if removed, False if not found
        """
        if rule_id not in self._rules:
            return False

        del self._rules[rule_id]
        logger.info(f"Monitoring rule removed: {rule_id}")
        return True

    def get_rule(self, rule_id: str) -> Optional[MonitoringRule]:
        """Get a specific rule by ID."""
        return self._rules.get(rule_id)

    def get_rules(self, enabled_only: bool = False) -> List[MonitoringRule]:
        """
        Get all monitoring rules.

        Args:
            enabled_only: If True, return only enabled rules

        Returns:
            List of MonitoringRule objects
        """
        rules = list(self._rules.values())
        if enabled_only:
            rules = [r for r in rules if r.enabled]
        return rules

    def enable_rule(self, rule_id: str) -> bool:
        """Enable a rule."""
        if rule_id not in self._rules:
            return False
        self._rules[rule_id].enabled = True
        logger.info(f"Rule enabled: {rule_id}")
        return True

    def disable_rule(self, rule_id: str) -> bool:
        """Disable a rule."""
        if rule_id not in self._rules:
            return False
        self._rules[rule_id].enabled = False
        logger.info(f"Rule disabled: {rule_id}")
        return True

    def update_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update rule properties.

        Args:
            rule_id: Rule to update
            updates: Dictionary of property updates

        Returns:
            True if updated successfully
        """
        if rule_id not in self._rules:
            return False

        rule = self._rules[rule_id]
        for key, value in updates.items():
            if hasattr(rule, key) and key not in ("id", "created_at"):
                setattr(rule, key, value)

        logger.info(f"Rule updated: {rule_id}")
        return True

    # =========================================================================
    # Metrics Collection
    # =========================================================================

    async def collect_metrics(self, model_id: str) -> Optional[ComplianceMetrics]:
        """
        Collect current compliance metrics for a model.

        Args:
            model_id: Model ID to collect metrics for

        Returns:
            ComplianceMetrics if successful, None otherwise
        """
        if not self._compliance_service:
            logger.warning("Compliance service not configured")
            return None

        try:
            # Use the refactored async service method for efficient DB querying
            metrics = await self._compliance_service.get_realtime_metrics(model_id)
            if not metrics:
                logger.warning(f"Failed to collect metrics for model: {model_id}")
                return None

            # Calculate trend and score change based on previous cached value
            previous_metrics = self._metrics_cache.get(model_id)
            if previous_metrics:
                metrics.score_change_24h = metrics.compliance_score - previous_metrics.compliance_score
                if metrics.score_change_24h > 2:
                    metrics.score_trend = "improving"
                elif metrics.score_change_24h < -2:
                    metrics.score_trend = "declining"
                else:
                    metrics.score_trend = "stable"

            # Cache the metrics
            self._metrics_cache[model_id] = metrics

            # Persist to Redis
            if self._redis:
                cache_key = f"{self.CACHE_METRICS}:{model_id}"
                await self._redis.setex(cache_key, self.metrics_ttl, metrics.model_dump_json())

            logger.debug(f"Metrics collected for model: {model_id}")
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics for {model_id}: {e}")
            return None

    async def collect_all_metrics(self) -> Dict[str, ComplianceMetrics]:
        """
        Collect metrics for all registered models.

        Returns:
            Dictionary mapping model_id to ComplianceMetrics
        """
        if not self._compliance_service:
            return {}

        results = {}
        # Fixed: must await async service methods
        models = await self._compliance_service.list_models()

        for model in models:
            metrics = await self.collect_metrics(model.model_id)
            if metrics:
                results[model.model_id] = metrics

        logger.info(f"Collected metrics for {len(results)} models")
        return results

    def get_cached_metrics(self, model_id: str) -> Optional[ComplianceMetrics]:
        """
        Get cached metrics for fast access.

        Args:
            model_id: Model ID to get metrics for

        Returns:
            Cached ComplianceMetrics or None if not cached
        """
        return self._metrics_cache.get(model_id)

    def get_all_cached_metrics(self) -> Dict[str, ComplianceMetrics]:
        """Get all cached metrics."""
        return dict(self._metrics_cache)

    # =========================================================================
    # Threshold Checking
    # =========================================================================

    async def check_thresholds(self, metrics: ComplianceMetrics) -> List[ComplianceAlert]:
        """
        Check all thresholds against metrics.

        Args:
            metrics: ComplianceMetrics to check

        Returns:
            List of triggered alerts
        """
        alerts = []

        for rule in self.get_rules(enabled_only=True):
            alert = await self.evaluate_rule(rule, metrics)
            if alert:
                alerts.append(alert)

        return alerts

    async def evaluate_rule(self, rule: MonitoringRule, metrics: ComplianceMetrics) -> Optional[ComplianceAlert]:
        """
        Evaluate a single rule against metrics.

        Args:
            rule: MonitoringRule to evaluate
            metrics: ComplianceMetrics to check against

        Returns:
            ComplianceAlert if rule triggered, None otherwise
        """
        # Check if rule applies to this model
        if rule.model_ids and metrics.model_id not in rule.model_ids:
            return None

        # Get metric values from the metrics object
        metric_values = {
            "compliance_score": metrics.compliance_score,
            "risk_level_numeric": self._risk_level_to_numeric(metrics.risk_level),
            "violation_count": float(metrics.violation_count),
            "critical_violations": float(metrics.critical_violations),
            "high_violations": float(metrics.high_violations),
            "pending_remediations": float(metrics.pending_remediations),
            "score_change_24h": metrics.score_change_24h,
            "days_since_assessment": float(metrics.days_since_assessment),
            "certifications_expiring_30d": float(metrics.certifications_expiring_30d),
        }

        # Check each threshold
        for threshold in rule.thresholds:
            if threshold.metric not in metric_values:
                continue

            actual_value = metric_values[threshold.metric]
            if threshold.evaluate(actual_value):
                # Check cooldown
                cooldown_key = f"{rule.id}:{metrics.model_id}:{threshold.metric}"
                if self._is_in_cooldown(cooldown_key, threshold.cooldown_minutes):
                    logger.debug(f"Alert suppressed by cooldown: {cooldown_key}")
                    continue

                # Create alert
                alert = self._create_alert(rule, threshold, metrics, actual_value)
                await self.trigger_alert(rule, threshold, metrics, alert)

                # Update cooldown
                self._cooldowns[cooldown_key] = datetime.now(timezone.utc)
                rule.last_triggered = datetime.now(timezone.utc)

                return alert

        return None

    def _is_in_cooldown(self, cooldown_key: str, cooldown_minutes: int) -> bool:
        """Check if an alert is still in cooldown period."""
        if cooldown_key not in self._cooldowns:
            return False

        last_triggered = self._cooldowns[cooldown_key]
        cooldown_expires = last_triggered + timedelta(minutes=cooldown_minutes)
        return datetime.now(timezone.utc) < cooldown_expires

    def _risk_level_to_numeric(self, risk_level: str) -> float:
        """Convert risk level string to numeric value."""
        mapping = {
            "minimal": 0,
            "limited": 1,
            "high": 2,
            "unacceptable": 3,
            "unknown": -1,
        }
        return float(mapping.get(risk_level.lower(), -1))

    def _create_alert(
        self,
        rule: MonitoringRule,
        threshold: MonitoringThreshold,
        metrics: ComplianceMetrics,
        actual_value: float,
    ) -> ComplianceAlert:
        """Create an alert from a triggered threshold."""
        operator_text = {
            ThresholdOperator.LT: "below",
            ThresholdOperator.GT: "above",
            ThresholdOperator.EQ: "equal to",
            ThresholdOperator.LTE: "at or below",
            ThresholdOperator.GTE: "at or above",
            ThresholdOperator.NEQ: "not equal to",
        }

        title = f"{rule.name}: {threshold.metric} threshold breached"
        message = (
            f"Model '{metrics.model_name}' has {threshold.metric} "
            f"{operator_text[threshold.operator]} threshold. "
            f"Current value: {actual_value:.2f}, Threshold: {threshold.value:.2f}"
        )

        return ComplianceAlert(
            rule_id=rule.id,
            rule_name=rule.name,
            threshold=threshold,
            model_id=metrics.model_id,
            model_name=metrics.model_name,
            severity=threshold.severity,
            title=title,
            message=message,
            metric_value=actual_value,
            threshold_value=threshold.value,
            metadata={
                "risk_level": metrics.risk_level,
                "compliance_score": metrics.compliance_score,
                "violation_count": metrics.violation_count,
            },
        )

    # =========================================================================
    # Alert Management
    # =========================================================================

    async def trigger_alert(
        self,
        rule: MonitoringRule,
        threshold: MonitoringThreshold,
        metrics: ComplianceMetrics,
        alert: ComplianceAlert,
    ) -> None:
        """
        Trigger an alert - publish to WebSocket, Redis, and notifications.

        Args:
            rule: The rule that triggered
            threshold: The threshold that was breached
            metrics: Current metrics
            alert: The alert to trigger
        """
        # Add to history
        self._alert_history.append(alert)
        if len(self._alert_history) > self.alert_history_limit:
            self._alert_history = self._alert_history[-self.alert_history_limit :]

        logger.warning(
            f"Alert triggered: {alert.title}",
            extra={
                "alert_id": alert.alert_id,
                "rule_id": rule.id,
                "model_id": metrics.model_id,
                "severity": alert.severity.value,
                "metric_value": alert.metric_value,
                "threshold_value": alert.threshold_value,
            },
        )

        # Publish to Redis
        if self._redis:
            try:
                await self._redis.publish(self.CHANNEL_ALERTS, alert.model_dump_json())

                # Store in alerts history in Redis
                await self._redis.lpush(self.CACHE_ALERTS, alert.model_dump_json())
                await self._redis.ltrim(self.CACHE_ALERTS, 0, self.alert_history_limit - 1)

            except Exception as e:
                logger.error(f"Failed to publish alert to Redis: {e}")

        # Broadcast via WebSocket
        if self.enable_websocket and self._websocket_broadcast:
            try:
                await self._websocket_broadcast(
                    {
                        "type": "compliance_alert",
                        "data": alert.model_dump(),
                    }
                )
            except Exception as e:
                logger.error(f"Failed to broadcast alert via WebSocket: {e}")

        # Send external notifications
        if self.enable_notifications and self._notification_callback:
            try:
                await self._notification_callback(alert, threshold.notification_channels)
            except Exception as e:
                logger.error(f"Failed to send notification: {e}")

    def get_alert_history(
        self,
        model_id: Optional[str] = None,
        hours: int = 24,
        severity: Optional[AlertSeverity] = None,
        status: Optional[AlertStatus] = None,
    ) -> List[ComplianceAlert]:
        """
        Get recent alert history.

        Args:
            model_id: Filter by model ID
            hours: Look back period in hours
            severity: Filter by severity
            status: Filter by status

        Returns:
            List of alerts matching criteria
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        alerts = [a for a in self._alert_history if a.triggered_at >= cutoff]

        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        if status:
            alerts = [a for a in alerts if a.status == status]

        return sorted(alerts, key=lambda a: a.triggered_at, reverse=True)

    def acknowledge_alert(
        self,
        alert_id: str,
        acknowledged_by: str,
        notes: Optional[str] = None,
    ) -> bool:
        """
        Acknowledge an alert.

        Args:
            alert_id: Alert ID to acknowledge
            acknowledged_by: User acknowledging the alert
            notes: Optional acknowledgment notes

        Returns:
            True if acknowledged successfully
        """
        for alert in self._alert_history:
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_at = datetime.now(timezone.utc)
                alert.acknowledged_by = acknowledged_by
                if notes:
                    alert.metadata["acknowledgment_notes"] = notes

                logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
                return True

        return False

    def resolve_alert(
        self,
        alert_id: str,
        resolved_by: str,
        resolution_notes: Optional[str] = None,
    ) -> bool:
        """
        Mark an alert as resolved.

        Args:
            alert_id: Alert ID to resolve
            resolved_by: User resolving the alert
            resolution_notes: Optional resolution notes

        Returns:
            True if resolved successfully
        """
        for alert in self._alert_history:
            if alert.alert_id == alert_id:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.now(timezone.utc)
                alert.resolved_by = resolved_by
                if resolution_notes:
                    alert.metadata["resolution_notes"] = resolution_notes

                logger.info(f"Alert resolved: {alert_id} by {resolved_by}")
                return True

        return False

    def get_active_alerts(self, model_id: Optional[str] = None) -> List[ComplianceAlert]:
        """Get all active (non-resolved) alerts."""
        alerts = [a for a in self._alert_history if a.status in (AlertStatus.ACTIVE, AlertStatus.ACKNOWLEDGED)]

        if model_id:
            alerts = [a for a in alerts if a.model_id == model_id]

        return alerts

    # =========================================================================
    # Event Handlers
    # =========================================================================

    async def on_assessment_completed(self, event: Dict[str, Any]) -> None:
        """
        Handle assessment completed event.

        Triggers metrics refresh and threshold checking.
        """
        model_id = event.get("model_id")
        if not model_id:
            return

        logger.info(f"Assessment completed event for model: {model_id}")

        # Refresh metrics
        metrics = await self.collect_metrics(model_id)
        if metrics:
            # Check thresholds
            alerts = await self.check_thresholds(metrics)
            if alerts:
                logger.info(f"Generated {len(alerts)} alerts from assessment")

        # Invoke registered handlers
        for handler in self._event_handlers.get("assessment_completed", []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def on_violation_detected(self, event: Dict[str, Any]) -> None:
        """
        Handle violation detected event.

        Creates immediate alert for critical violations.
        """
        model_id = event.get("model_id")
        severity = event.get("severity", "medium")
        violation_id = event.get("violation_id")

        logger.info(f"Violation detected: {violation_id} (severity: {severity})", extra={"model_id": model_id})

        # For critical violations, trigger immediate alert
        if severity == "critical":
            # Refresh metrics and check
            metrics = await self.collect_metrics(model_id) if model_id else None
            if metrics:
                await self.check_thresholds(metrics)

        # Invoke registered handlers
        for handler in self._event_handlers.get("violation_detected", []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    async def on_score_changed(self, event: Dict[str, Any]) -> None:
        """
        Handle score change event.

        Checks for significant score drops.
        """
        model_id = event.get("model_id")
        old_score = event.get("old_score", 0)
        new_score = event.get("new_score", 0)
        change = new_score - old_score

        logger.info(f"Score changed for model {model_id}: {old_score:.1f} -> {new_score:.1f} ({change:+.1f})")

        # Refresh metrics for significant changes
        if abs(change) >= 5:
            metrics = await self.collect_metrics(model_id) if model_id else None
            if metrics:
                await self.check_thresholds(metrics)

        # Invoke registered handlers
        for handler in self._event_handlers.get("score_changed", []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Event handler error: {e}")

    # =========================================================================
    # Background Tasks
    # =========================================================================

    async def _metrics_collection_loop(self) -> None:
        """Periodically collect metrics for all models."""
        while self._running:
            try:
                await self.collect_all_metrics()
                logger.debug("Metrics collection cycle completed")
            except Exception as e:
                logger.error(f"Metrics collection error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _threshold_check_loop(self) -> None:
        """Periodically check thresholds for all cached metrics."""
        while self._running:
            try:
                for model_id, metrics in self._metrics_cache.items():
                    await self.check_thresholds(metrics)

                logger.debug("Threshold check cycle completed")
            except Exception as e:
                logger.error(f"Threshold check error: {e}")

            await asyncio.sleep(self.check_interval)

    async def _event_subscriber_loop(self) -> None:
        """Listen for events from Redis pub/sub."""
        if not self._pubsub:
            return

        while self._running:
            try:
                message = await self._pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

                if message and message["type"] == "message":
                    channel = message["channel"]
                    data = json.loads(message["data"])

                    if channel == self.CHANNEL_EVENTS:
                        event_type = data.get("event_type")
                        if event_type == "assessment_completed":
                            await self.on_assessment_completed(data)
                        elif event_type == "violation_detected":
                            await self.on_violation_detected(data)
                        elif event_type == "score_changed":
                            await self.on_score_changed(data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Event subscriber error: {e}")
                await asyncio.sleep(1)

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of old data."""
        while self._running:
            try:
                # Clean up old cooldowns
                now = datetime.now(timezone.utc)
                expired_keys = [
                    key
                    for key, timestamp in self._cooldowns.items()
                    if (now - timestamp).total_seconds() > 86400  # 24 hours
                ]
                for key in expired_keys:
                    del self._cooldowns[key]

                if expired_keys:
                    logger.debug(f"Cleaned up {len(expired_keys)} expired cooldowns")

            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

            await asyncio.sleep(3600)  # Run every hour

    # =========================================================================
    # Default Rules
    # =========================================================================

    def load_default_rules(self) -> None:
        """
        Load sensible default monitoring rules.

        Provides out-of-the-box monitoring for common compliance scenarios.
        """
        default_rules = [
            # Critical: Score below 50%
            MonitoringRule(
                id="default_critical_score",
                name="Critical Compliance Score",
                description="Alert when compliance score drops below 50%",
                thresholds=[
                    MonitoringThreshold(
                        metric="compliance_score",
                        operator=ThresholdOperator.LT,
                        value=50.0,
                        severity=AlertSeverity.CRITICAL,
                        notification_channels=["websocket", "email", "slack"],
                        cooldown_minutes=30,
                        description="Compliance score critically low",
                    )
                ],
                check_interval_seconds=60,
                tags=["compliance", "critical"],
            ),
            # High: Score drops more than 10% in 24h
            MonitoringRule(
                id="default_score_drop",
                name="Significant Score Drop",
                description="Alert when score drops more than 10% in 24 hours",
                thresholds=[
                    MonitoringThreshold(
                        metric="score_change_24h",
                        operator=ThresholdOperator.LT,
                        value=-10.0,
                        severity=AlertSeverity.HIGH,
                        notification_channels=["websocket", "email"],
                        cooldown_minutes=120,
                        description="Score dropped significantly",
                    )
                ],
                check_interval_seconds=300,
                tags=["compliance", "trend"],
            ),
            # High: Any critical violation
            MonitoringRule(
                id="default_critical_violation",
                name="Critical Violations Detected",
                description="Alert when any critical violation is detected",
                thresholds=[
                    MonitoringThreshold(
                        metric="critical_violations",
                        operator=ThresholdOperator.GTE,
                        value=1.0,
                        severity=AlertSeverity.CRITICAL,
                        notification_channels=["websocket", "email", "slack", "sms"],
                        cooldown_minutes=15,
                        description="Critical violation requires immediate attention",
                    )
                ],
                check_interval_seconds=60,
                tags=["violations", "critical"],
            ),
            # Medium: Multiple violations
            MonitoringRule(
                id="default_multiple_violations",
                name="Multiple Violations",
                description="Alert when 5 or more violations exist",
                thresholds=[
                    MonitoringThreshold(
                        metric="violation_count",
                        operator=ThresholdOperator.GTE,
                        value=5.0,
                        severity=AlertSeverity.MEDIUM,
                        notification_channels=["websocket", "email"],
                        cooldown_minutes=240,
                        description="Multiple violations need review",
                    )
                ],
                check_interval_seconds=300,
                tags=["violations"],
            ),
            # Low: Warning score threshold
            MonitoringRule(
                id="default_warning_score",
                name="Compliance Warning",
                description="Warning when compliance score drops below 70%",
                thresholds=[
                    MonitoringThreshold(
                        metric="compliance_score",
                        operator=ThresholdOperator.LT,
                        value=70.0,
                        severity=AlertSeverity.LOW,
                        notification_channels=["websocket"],
                        cooldown_minutes=360,
                        description="Compliance score in warning zone",
                    )
                ],
                check_interval_seconds=600,
                tags=["compliance", "warning"],
            ),
            # Medium: Stale assessment
            MonitoringRule(
                id="default_stale_assessment",
                name="Stale Assessment",
                description="Alert when assessment is more than 30 days old",
                thresholds=[
                    MonitoringThreshold(
                        metric="days_since_assessment",
                        operator=ThresholdOperator.GT,
                        value=30.0,
                        severity=AlertSeverity.MEDIUM,
                        notification_channels=["websocket", "email"],
                        cooldown_minutes=1440,  # 24 hours
                        description="Assessment needs refresh",
                    )
                ],
                check_interval_seconds=3600,
                tags=["assessment", "freshness"],
            ),
            # High: Pending remediations
            MonitoringRule(
                id="default_pending_remediations",
                name="Pending Remediations",
                description="Alert when there are too many pending remediations",
                thresholds=[
                    MonitoringThreshold(
                        metric="pending_remediations",
                        operator=ThresholdOperator.GTE,
                        value=3.0,
                        severity=AlertSeverity.HIGH,
                        notification_channels=["websocket", "email"],
                        cooldown_minutes=480,
                        description="Multiple remediations pending",
                    )
                ],
                check_interval_seconds=600,
                tags=["remediation"],
            ),
            # Low: Certification expiring
            MonitoringRule(
                id="default_cert_expiring",
                name="Certifications Expiring",
                description="Alert when certifications are expiring within 30 days",
                thresholds=[
                    MonitoringThreshold(
                        metric="certifications_expiring_30d",
                        operator=ThresholdOperator.GTE,
                        value=1.0,
                        severity=AlertSeverity.LOW,
                        notification_channels=["websocket", "email"],
                        cooldown_minutes=2880,  # 48 hours
                        description="Certification renewal needed",
                    )
                ],
                check_interval_seconds=86400,  # Daily
                tags=["certification"],
            ),
            # High: High risk level
            MonitoringRule(
                id="default_high_risk",
                name="High Risk Level",
                description="Alert when model has high or unacceptable risk",
                thresholds=[
                    MonitoringThreshold(
                        metric="risk_level_numeric",
                        operator=ThresholdOperator.GTE,
                        value=2.0,  # high = 2, unacceptable = 3
                        severity=AlertSeverity.HIGH,
                        notification_channels=["websocket", "email", "slack"],
                        cooldown_minutes=720,
                        description="High risk level requires review",
                    )
                ],
                check_interval_seconds=600,
                tags=["risk"],
            ),
        ]

        for rule in default_rules:
            self.add_rule(rule)

        logger.info(f"Loaded {len(default_rules)} default monitoring rules")

    # =========================================================================
    # Statistics & Reporting
    # =========================================================================

    def get_monitoring_stats(self) -> Dict[str, Any]:
        """Get monitoring system statistics."""
        active_alerts = self.get_active_alerts()

        return {
            "status": "running" if self._running else "stopped",
            "rules_total": len(self._rules),
            "rules_enabled": len([r for r in self._rules.values() if r.enabled]),
            "models_monitored": len(self._metrics_cache),
            "alerts_active": len(active_alerts),
            "alerts_critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "alerts_high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
            "alerts_total_24h": len(self.get_alert_history(hours=24)),
            "cooldowns_active": len(self._cooldowns),
            "redis_connected": self._redis is not None,
            "websocket_enabled": self.enable_websocket,
            "notifications_enabled": self.enable_notifications,
        }

    async def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Get summary data for monitoring dashboard.

        Returns aggregated metrics, alerts, and system health.
        """
        metrics_list = list(self._metrics_cache.values())
        active_alerts = self.get_active_alerts()

        # Calculate averages
        avg_score = 0.0
        if metrics_list:
            avg_score = sum(m.compliance_score for m in metrics_list) / len(metrics_list)

        # Risk distribution
        risk_distribution = {"minimal": 0, "limited": 0, "high": 0, "unacceptable": 0}
        for m in metrics_list:
            if m.risk_level in risk_distribution:
                risk_distribution[m.risk_level] += 1

        # Alert severity distribution
        alert_severity = {
            "critical": len([a for a in active_alerts if a.severity == AlertSeverity.CRITICAL]),
            "high": len([a for a in active_alerts if a.severity == AlertSeverity.HIGH]),
            "medium": len([a for a in active_alerts if a.severity == AlertSeverity.MEDIUM]),
            "low": len([a for a in active_alerts if a.severity == AlertSeverity.LOW]),
        }

        return {
            "summary": {
                "total_models": len(metrics_list),
                "average_compliance_score": round(avg_score, 1),
                "active_alerts": len(active_alerts),
                "critical_alerts": alert_severity["critical"],
            },
            "risk_distribution": risk_distribution,
            "alert_severity": alert_severity,
            "recent_alerts": [a.model_dump() for a in self.get_alert_history(hours=1)[:5]],
            "monitoring_stats": self.get_monitoring_stats(),
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }


# =============================================================================
# Factory function
# =============================================================================


def create_monitoring_manager(
    redis_url: str = "redis://localhost:6379", load_defaults: bool = True, **kwargs
) -> RealTimeMonitoringManager:
    """
    Factory function to create and configure a monitoring manager.

    Args:
        redis_url: Redis connection URL
        load_defaults: Whether to load default monitoring rules
        **kwargs: Additional arguments for RealTimeMonitoringManager

    Returns:
        Configured RealTimeMonitoringManager instance
    """
    manager = RealTimeMonitoringManager(redis_url=redis_url, **kwargs)

    if load_defaults:
        manager.load_default_rules()

    return manager
