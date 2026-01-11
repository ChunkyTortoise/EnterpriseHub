"""
Advanced Monitoring and Alerting System
=======================================

Comprehensive monitoring, alerting, and observability platform for the
Agent Enhancement System with real-time metrics, intelligent alerting,
and automated response capabilities.
"""

import asyncio
import logging
import time
import json
import smtplib
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import aiofiles
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to track"""
    COUNTER = "counter"         # Incremental values
    GAUGE = "gauge"            # Point-in-time values
    HISTOGRAM = "histogram"     # Distribution of values
    TIMER = "timer"            # Duration measurements


class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    LOG = "log"
    CONSOLE = "console"


@dataclass
class MetricPoint:
    """Individual metric data point"""
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class Alert:
    """Alert definition and state"""
    id: str
    name: str
    description: str
    severity: AlertSeverity
    condition: str  # Alert condition expression
    threshold: float
    duration_seconds: int = 0  # How long condition must be true
    notification_channels: List[NotificationChannel] = field(default_factory=list)
    labels: Dict[str, str] = field(default_factory=dict)
    active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    last_triggered: Optional[datetime] = None
    trigger_count: int = 0


@dataclass
class AlertInstance:
    """Active alert instance"""
    alert: Alert
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    trigger_value: float = 0.0
    context: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """
    High-performance metrics collection with time-series storage
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.metric_metadata: Dict[str, Dict[str, Any]] = {}
        self.collection_stats = {
            "total_metrics": 0,
            "metrics_per_second": 0.0,
            "unique_metric_names": 0
        }
        self._last_stats_update = time.time()

    def record_metric(self,
                     name: str,
                     value: float,
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric data point"""

        metric_point = MetricPoint(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {}
        )

        # Store metric with labels as part of the key
        metric_key = self._create_metric_key(name, labels or {})
        self.metrics[metric_key].append(metric_point)

        # Update metadata
        if metric_key not in self.metric_metadata:
            self.metric_metadata[metric_key] = {
                "name": name,
                "type": metric_type.value,
                "labels": labels or {},
                "first_seen": datetime.now(),
                "last_seen": datetime.now(),
                "sample_count": 0
            }

        self.metric_metadata[metric_key]["last_seen"] = datetime.now()
        self.metric_metadata[metric_key]["sample_count"] += 1

        # Update collection stats
        self.collection_stats["total_metrics"] += 1
        self._update_collection_stats()

        # Clean old metrics
        self._cleanup_old_metrics()

    def get_metric_values(self,
                         name: str,
                         labels: Optional[Dict[str, str]] = None,
                         time_range_minutes: int = 60) -> List[MetricPoint]:
        """Get metric values within time range"""

        metric_key = self._create_metric_key(name, labels or {})

        if metric_key not in self.metrics:
            return []

        cutoff_time = datetime.now() - timedelta(minutes=time_range_minutes)

        return [
            point for point in self.metrics[metric_key]
            if point.timestamp >= cutoff_time
        ]

    def calculate_metric_statistics(self,
                                  name: str,
                                  labels: Optional[Dict[str, str]] = None,
                                  time_range_minutes: int = 60) -> Dict[str, float]:
        """Calculate statistics for a metric"""

        values = self.get_metric_values(name, labels, time_range_minutes)

        if not values:
            return {}

        numeric_values = [point.value for point in values]

        return {
            "count": len(numeric_values),
            "min": min(numeric_values),
            "max": max(numeric_values),
            "avg": sum(numeric_values) / len(numeric_values),
            "latest": numeric_values[-1] if numeric_values else 0.0,
            "rate_per_minute": len(numeric_values) / max(1, time_range_minutes)
        }

    def get_all_metric_names(self) -> List[str]:
        """Get list of all unique metric names"""
        return list(set(
            metadata["name"] for metadata in self.metric_metadata.values()
        ))

    def _create_metric_key(self, name: str, labels: Dict[str, str]) -> str:
        """Create unique key for metric with labels"""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _update_collection_stats(self) -> None:
        """Update collection performance statistics"""
        current_time = time.time()
        time_diff = current_time - self._last_stats_update

        if time_diff >= 1.0:  # Update every second
            metrics_in_period = self.collection_stats["total_metrics"]
            self.collection_stats["metrics_per_second"] = metrics_in_period / time_diff
            self.collection_stats["unique_metric_names"] = len(self.metric_metadata)
            self._last_stats_update = current_time

    def _cleanup_old_metrics(self) -> None:
        """Remove old metrics beyond retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        for metric_key, points in self.metrics.items():
            # Remove old points
            while points and points[0].timestamp < cutoff_time:
                points.popleft()

            # Remove empty metrics
            if not points:
                del self.metrics[metric_key]
                if metric_key in self.metric_metadata:
                    del self.metric_metadata[metric_key]


class AlertingEngine:
    """
    Intelligent alerting engine with condition evaluation and notification
    """

    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics_collector = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.active_alert_instances: Dict[str, AlertInstance] = {}
        self.alert_history: List[AlertInstance] = []
        self.notification_handlers: Dict[NotificationChannel, Callable] = {}

        # Alert evaluation state
        self.condition_state: Dict[str, Dict] = {}  # Tracks condition duration
        self.evaluation_stats = {
            "evaluations_per_second": 0.0,
            "total_evaluations": 0,
            "active_alerts": 0
        }

    def add_alert(self, alert: Alert) -> None:
        """Add an alert definition"""
        self.alerts[alert.id] = alert
        self.condition_state[alert.id] = {
            "condition_start": None,
            "last_evaluation": None,
            "consecutive_true": 0
        }
        logger.info(f"Added alert: {alert.name} ({alert.id})")

    def remove_alert(self, alert_id: str) -> bool:
        """Remove an alert definition"""
        if alert_id in self.alerts:
            del self.alerts[alert_id]
            if alert_id in self.condition_state:
                del self.condition_state[alert_id]

            # Resolve any active instances
            if alert_id in self.active_alert_instances:
                self._resolve_alert(alert_id)

            logger.info(f"Removed alert: {alert_id}")
            return True
        return False

    def register_notification_handler(self,
                                    channel: NotificationChannel,
                                    handler: Callable) -> None:
        """Register a notification handler for a channel"""
        self.notification_handlers[channel] = handler
        logger.info(f"Registered notification handler for {channel.value}")

    async def evaluate_alerts(self) -> None:
        """Evaluate all active alerts"""
        for alert_id, alert in self.alerts.items():
            if not alert.active:
                continue

            try:
                await self._evaluate_single_alert(alert)
                self.evaluation_stats["total_evaluations"] += 1
            except Exception as e:
                logger.error(f"Error evaluating alert {alert_id}: {e}")

        # Update evaluation stats
        self.evaluation_stats["active_alerts"] = len(self.active_alert_instances)

    async def _evaluate_single_alert(self, alert: Alert) -> None:
        """Evaluate a single alert condition"""
        condition_met, trigger_value = await self._evaluate_condition(
            alert.condition, alert.threshold
        )

        state = self.condition_state[alert.id]

        if condition_met:
            if state["condition_start"] is None:
                state["condition_start"] = datetime.now()
                state["consecutive_true"] = 1
            else:
                state["consecutive_true"] += 1

            # Check if condition has been true long enough
            if state["condition_start"]:
                duration = (datetime.now() - state["condition_start"]).total_seconds()

                if duration >= alert.duration_seconds:
                    await self._trigger_alert(alert, trigger_value)

        else:
            # Reset condition state
            if state["condition_start"] is not None:
                state["condition_start"] = None
                state["consecutive_true"] = 0

                # Resolve alert if it was active
                if alert.id in self.active_alert_instances:
                    await self._resolve_alert(alert.id)

        state["last_evaluation"] = datetime.now()

    async def _evaluate_condition(self, condition: str, threshold: float) -> tuple[bool, float]:
        """Evaluate alert condition against metrics"""

        try:
            # Parse condition (simplified parser for demo)
            # Format: "metric_name operator value [time_range]"
            # Example: "api_response_time > 1000 5m"

            parts = condition.strip().split()
            if len(parts) < 3:
                return False, 0.0

            metric_name = parts[0]
            operator = parts[1]
            expected_value = float(parts[2])
            time_range_minutes = 5  # Default

            # Parse time range if provided
            if len(parts) > 3:
                time_str = parts[3]
                if time_str.endswith('m'):
                    time_range_minutes = int(time_str[:-1])
                elif time_str.endswith('h'):
                    time_range_minutes = int(time_str[:-1]) * 60

            # Get metric statistics
            stats = self.metrics_collector.calculate_metric_statistics(
                metric_name, time_range_minutes=time_range_minutes
            )

            if not stats:
                return False, 0.0

            # Use 'avg' as the evaluation value (could be configurable)
            current_value = stats.get("avg", 0.0)

            # Evaluate condition
            if operator == ">":
                condition_met = current_value > expected_value
            elif operator == "<":
                condition_met = current_value < expected_value
            elif operator == ">=":
                condition_met = current_value >= expected_value
            elif operator == "<=":
                condition_met = current_value <= expected_value
            elif operator == "==":
                condition_met = abs(current_value - expected_value) < 0.01
            else:
                logger.warning(f"Unknown operator in condition: {operator}")
                return False, 0.0

            return condition_met, current_value

        except Exception as e:
            logger.error(f"Error evaluating condition '{condition}': {e}")
            return False, 0.0

    async def _trigger_alert(self, alert: Alert, trigger_value: float) -> None:
        """Trigger an alert and send notifications"""

        # Don't trigger if already active
        if alert.id in self.active_alert_instances:
            return

        alert_instance = AlertInstance(
            alert=alert,
            triggered_at=datetime.now(),
            trigger_value=trigger_value,
            context={
                "condition": alert.condition,
                "threshold": alert.threshold,
                "actual_value": trigger_value
            }
        )

        self.active_alert_instances[alert.id] = alert_instance
        alert.last_triggered = datetime.now()
        alert.trigger_count += 1

        logger.warning(f"Alert triggered: {alert.name} (value: {trigger_value})")

        # Send notifications
        await self._send_notifications(alert_instance)

    async def _resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert"""

        if alert_id not in self.active_alert_instances:
            return

        alert_instance = self.active_alert_instances[alert_id]
        alert_instance.resolved_at = datetime.now()

        # Move to history
        self.alert_history.append(alert_instance)
        del self.active_alert_instances[alert_id]

        logger.info(f"Alert resolved: {alert_instance.alert.name}")

        # Send resolution notification
        await self._send_resolution_notification(alert_instance)

        # Keep history size manageable
        if len(self.alert_history) > 1000:
            self.alert_history = self.alert_history[-1000:]

    async def _send_notifications(self, alert_instance: AlertInstance) -> None:
        """Send alert notifications through configured channels"""

        for channel in alert_instance.alert.notification_channels:
            handler = self.notification_handlers.get(channel)

            if handler:
                try:
                    await self._execute_notification_handler(
                        handler, alert_instance, "triggered"
                    )
                except Exception as e:
                    logger.error(f"Failed to send notification via {channel.value}: {e}")

    async def _send_resolution_notification(self, alert_instance: AlertInstance) -> None:
        """Send alert resolution notifications"""

        for channel in alert_instance.alert.notification_channels:
            handler = self.notification_handlers.get(channel)

            if handler:
                try:
                    await self._execute_notification_handler(
                        handler, alert_instance, "resolved"
                    )
                except Exception as e:
                    logger.error(f"Failed to send resolution notification via {channel.value}: {e}")

    async def _execute_notification_handler(self,
                                          handler: Callable,
                                          alert_instance: AlertInstance,
                                          action: str) -> None:
        """Execute a notification handler"""

        if asyncio.iscoroutinefunction(handler):
            await handler(alert_instance, action)
        else:
            # Run sync handler in executor
            await asyncio.get_event_loop().run_in_executor(
                None, handler, alert_instance, action
            )

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of alerting system state"""
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(self.active_alert_instances),
            "alerts_in_history": len(self.alert_history),
            "evaluation_stats": self.evaluation_stats,
            "active_alert_details": {
                alert_id: {
                    "name": instance.alert.name,
                    "severity": instance.alert.severity.value,
                    "triggered_at": instance.triggered_at,
                    "duration_minutes": (datetime.now() - instance.triggered_at).total_seconds() / 60,
                    "trigger_value": instance.trigger_value
                }
                for alert_id, instance in self.active_alert_instances.items()
            }
        }


class NotificationHandlers:
    """
    Built-in notification handlers for various channels
    """

    @staticmethod
    async def console_handler(alert_instance: AlertInstance, action: str) -> None:
        """Console notification handler"""
        alert = alert_instance.alert
        severity_icon = {
            AlertSeverity.INFO: "ℹ️",
            AlertSeverity.WARNING: "⚠️",
            AlertSeverity.ERROR: "❌",
            AlertSeverity.CRITICAL: "🚨"
        }

        icon = severity_icon.get(alert.severity, "❓")

        if action == "triggered":
            print(f"\n{icon} ALERT TRIGGERED: {alert.name}")
            print(f"Severity: {alert.severity.value.upper()}")
            print(f"Description: {alert.description}")
            print(f"Condition: {alert.condition}")
            print(f"Trigger Value: {alert_instance.trigger_value}")
            print(f"Threshold: {alert.threshold}")
            print(f"Time: {alert_instance.triggered_at}")
        else:
            print(f"\n✅ ALERT RESOLVED: {alert.name}")
            print(f"Duration: {(alert_instance.resolved_at - alert_instance.triggered_at).total_seconds():.1f} seconds")

    @staticmethod
    async def log_handler(alert_instance: AlertInstance, action: str) -> None:
        """Log file notification handler"""
        alert = alert_instance.alert

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "alert_id": alert.id,
            "alert_name": alert.name,
            "severity": alert.severity.value,
            "condition": alert.condition,
            "trigger_value": alert_instance.trigger_value,
            "threshold": alert.threshold
        }

        if action == "resolved":
            log_entry["duration_seconds"] = (alert_instance.resolved_at - alert_instance.triggered_at).total_seconds()

        # Write to alert log file
        async with aiofiles.open("alerts.log", "a") as f:
            await f.write(json.dumps(log_entry) + "\n")

    @staticmethod
    async def email_handler(alert_instance: AlertInstance, action: str) -> None:
        """Email notification handler"""
        # This would require SMTP configuration
        alert = alert_instance.alert

        subject = f"[{alert.severity.value.upper()}] {alert.name} - {action.title()}"

        if action == "triggered":
            body = f"""
Alert: {alert.name}
Severity: {alert.severity.value.upper()}
Description: {alert.description}
Condition: {alert.condition}
Trigger Value: {alert_instance.trigger_value}
Threshold: {alert.threshold}
Time: {alert_instance.triggered_at}

Please investigate immediately.
"""
        else:
            duration = (alert_instance.resolved_at - alert_instance.triggered_at).total_seconds()
            body = f"""
Alert: {alert.name}
Status: RESOLVED
Duration: {duration:.1f} seconds
Resolved at: {alert_instance.resolved_at}

The alert condition is no longer met.
"""

        logger.info(f"Email notification: {subject}")
        # In production, would send actual email
        # await send_email(subject, body, recipients)


class AdvancedMonitoringSystem:
    """
    Main monitoring system coordinating metrics collection and alerting
    """

    def __init__(self, evaluation_interval: int = 30):
        self.evaluation_interval = evaluation_interval
        self.metrics_collector = MetricsCollector()
        self.alerting_engine = AlertingEngine(self.metrics_collector)

        # Monitoring tasks
        self._evaluation_task: Optional[asyncio.Task] = None
        self._metrics_collection_task: Optional[asyncio.Task] = None
        self._running = False

        # System integration
        self.system_integrations: List[Callable] = []

    async def initialize(self) -> None:
        """Initialize the monitoring system"""
        logger.info("Initializing Advanced Monitoring System")

        # Register built-in notification handlers
        self.alerting_engine.register_notification_handler(
            NotificationChannel.CONSOLE, NotificationHandlers.console_handler
        )
        self.alerting_engine.register_notification_handler(
            NotificationChannel.LOG, NotificationHandlers.log_handler
        )
        self.alerting_engine.register_notification_handler(
            NotificationChannel.EMAIL, NotificationHandlers.email_handler
        )

        # Setup default alerts for Agent Enhancement System
        await self._setup_default_alerts()

        # Start monitoring loops
        self._running = True
        self._evaluation_task = asyncio.create_task(self._evaluation_loop())
        self._metrics_collection_task = asyncio.create_task(self._system_metrics_collection_loop())

        logger.info("Advanced Monitoring System initialized")

    async def shutdown(self) -> None:
        """Shutdown the monitoring system"""
        logger.info("Shutting down Advanced Monitoring System")

        self._running = False

        if self._evaluation_task:
            self._evaluation_task.cancel()
        if self._metrics_collection_task:
            self._metrics_collection_task.cancel()

        # Wait for tasks to complete
        if self._evaluation_task:
            try:
                await self._evaluation_task
            except asyncio.CancelledError:
                pass

        if self._metrics_collection_task:
            try:
                await self._metrics_collection_task
            except asyncio.CancelledError:
                pass

        logger.info("Advanced Monitoring System shut down")

    def record_metric(self,
                     name: str,
                     value: float,
                     metric_type: MetricType = MetricType.GAUGE,
                     labels: Optional[Dict[str, str]] = None) -> None:
        """Record a metric (convenience method)"""
        self.metrics_collector.record_metric(name, value, metric_type, labels)

    def add_alert(self, alert: Alert) -> None:
        """Add an alert definition (convenience method)"""
        self.alerting_engine.add_alert(alert)

    def register_system_integration(self, integration_func: Callable) -> None:
        """Register a system integration for automatic metrics collection"""
        self.system_integrations.append(integration_func)

    async def get_monitoring_report(self) -> Dict[str, Any]:
        """Generate comprehensive monitoring report"""
        return {
            "timestamp": datetime.now(),
            "metrics_collector": {
                "collection_stats": self.metrics_collector.collection_stats,
                "metric_count": len(self.metrics_collector.metrics),
                "unique_metrics": len(self.metrics_collector.get_all_metric_names())
            },
            "alerting_engine": self.alerting_engine.get_alert_summary(),
            "system_health": await self._collect_system_health_metrics()
        }

    async def _setup_default_alerts(self) -> None:
        """Setup default alerts for the Agent Enhancement System"""

        # High API response time alert
        api_response_alert = Alert(
            id="high_api_response_time",
            name="High API Response Time",
            description="API response time is above acceptable threshold",
            severity=AlertSeverity.WARNING,
            condition="api_response_time_ms > 1000",
            threshold=1000.0,
            duration_seconds=60,  # Must be high for 1 minute
            notification_channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
        )
        self.alerting_engine.add_alert(api_response_alert)

        # High error rate alert
        error_rate_alert = Alert(
            id="high_error_rate",
            name="High Error Rate",
            description="Error rate is above acceptable threshold",
            severity=AlertSeverity.ERROR,
            condition="error_rate_percent > 5",
            threshold=5.0,
            duration_seconds=30,
            notification_channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
        )
        self.alerting_engine.add_alert(error_rate_alert)

        # Low cache hit rate alert
        cache_hit_alert = Alert(
            id="low_cache_hit_rate",
            name="Low Cache Hit Rate",
            description="Cache hit rate is below optimal threshold",
            severity=AlertSeverity.WARNING,
            condition="cache_hit_rate_percent < 70",
            threshold=70.0,
            duration_seconds=300,  # Must be low for 5 minutes
            notification_channels=[NotificationChannel.CONSOLE]
        )
        self.alerting_engine.add_alert(cache_hit_alert)

        # High memory usage alert
        memory_usage_alert = Alert(
            id="high_memory_usage",
            name="High Memory Usage",
            description="System memory usage is critically high",
            severity=AlertSeverity.CRITICAL,
            condition="memory_usage_percent > 90",
            threshold=90.0,
            duration_seconds=120,
            notification_channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
        )
        self.alerting_engine.add_alert(memory_usage_alert)

        # Database performance alert
        db_performance_alert = Alert(
            id="slow_database_queries",
            name="Slow Database Queries",
            description="Database query response time is too high",
            severity=AlertSeverity.WARNING,
            condition="database_response_time_ms > 500",
            threshold=500.0,
            duration_seconds=90,
            notification_channels=[NotificationChannel.CONSOLE, NotificationChannel.LOG]
        )
        self.alerting_engine.add_alert(db_performance_alert)

    async def _evaluation_loop(self) -> None:
        """Main alert evaluation loop"""
        while self._running:
            try:
                await self.alerting_engine.evaluate_alerts()
                await asyncio.sleep(self.evaluation_interval)
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")
                await asyncio.sleep(self.evaluation_interval)

    async def _system_metrics_collection_loop(self) -> None:
        """Collect system metrics from various sources"""
        while self._running:
            try:
                # Collect system resource metrics
                await self._collect_system_resource_metrics()

                # Run registered system integrations
                for integration in self.system_integrations:
                    try:
                        if asyncio.iscoroutinefunction(integration):
                            await integration(self)
                        else:
                            integration(self)
                    except Exception as e:
                        logger.error(f"System integration error: {e}")

                await asyncio.sleep(30)  # Collect every 30 seconds

            except Exception as e:
                logger.error(f"Metrics collection error: {e}")
                await asyncio.sleep(30)

    async def _collect_system_resource_metrics(self) -> None:
        """Collect basic system resource metrics"""
        import psutil

        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        self.record_metric("cpu_usage_percent", cpu_percent, MetricType.GAUGE)

        # Memory metrics
        memory = psutil.virtual_memory()
        self.record_metric("memory_usage_percent", memory.percent, MetricType.GAUGE)
        self.record_metric("memory_usage_bytes", memory.used, MetricType.GAUGE)

        # Disk metrics
        disk = psutil.disk_usage('/')
        disk_usage_percent = (disk.used / disk.total) * 100
        self.record_metric("disk_usage_percent", disk_usage_percent, MetricType.GAUGE)

        # Network metrics
        net_io = psutil.net_io_counters()
        self.record_metric("network_bytes_sent", net_io.bytes_sent, MetricType.COUNTER)
        self.record_metric("network_bytes_recv", net_io.bytes_recv, MetricType.COUNTER)

    async def _collect_system_health_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive system health metrics"""
        health_metrics = {}

        # Get recent metrics for key indicators
        for metric_name in ["cpu_usage_percent", "memory_usage_percent", "api_response_time_ms"]:
            stats = self.metrics_collector.calculate_metric_statistics(metric_name, time_range_minutes=10)
            if stats:
                health_metrics[metric_name] = stats

        return health_metrics


# Global monitoring system instance
monitoring_system = AdvancedMonitoringSystem()


# Integration functions for the Agent Enhancement System
async def collect_optimization_engine_metrics(monitoring_system: AdvancedMonitoringSystem) -> None:
    """Collect metrics from the optimization engine"""
    try:
        from .system_optimization_engine import optimization_engine

        # Cache metrics
        cache_stats = optimization_engine.cache.cache_stats
        total_requests = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
        if total_requests > 0:
            hit_rate = (cache_stats.get("hits", 0) / total_requests) * 100
            monitoring_system.record_metric("cache_hit_rate_percent", hit_rate)

        # Event bus metrics
        event_stats = optimization_engine.event_bus.get_stats()
        monitoring_system.record_metric("event_queue_size", event_stats["queue_size"])
        monitoring_system.record_metric("events_processed_total", event_stats["processing_stats"]["processed"], MetricType.COUNTER)

    except Exception as e:
        logger.error(f"Error collecting optimization engine metrics: {e}")


async def collect_database_metrics(monitoring_system: AdvancedMonitoringSystem) -> None:
    """Collect metrics from the database layer"""
    try:
        from .optimized_database_layer import optimized_db

        db_report = await optimized_db.get_database_performance_report()
        operation_stats = db_report["operation_stats"]

        monitoring_system.record_metric("database_response_time_ms", operation_stats["average_response_time"])
        monitoring_system.record_metric("database_cache_hit_rate", operation_stats["cache_hit_rate"])

        # Connection pool metrics
        if "connection_pool_stats" in db_report:
            pool_stats = db_report["connection_pool_stats"]
            monitoring_system.record_metric("database_active_connections", pool_stats["active_connections"])
            monitoring_system.record_metric("database_pool_hits", pool_stats["pool_hits"], MetricType.COUNTER)

    except Exception as e:
        logger.error(f"Error collecting database metrics: {e}")


async def collect_api_metrics(monitoring_system: AdvancedMonitoringSystem) -> None:
    """Collect metrics from the API layer"""
    try:
        from .enhanced_api_performance import enhanced_api_layer

        api_report = await enhanced_api_layer.get_performance_report()
        global_stats = api_report["global_stats"]

        monitoring_system.record_metric("api_response_time_ms", global_stats["average_response_time"])

        # Error rate calculation
        total_requests = global_stats["total_requests"]
        if total_requests > 0:
            error_rate = (global_stats["total_errors"] / total_requests) * 100
            monitoring_system.record_metric("error_rate_percent", error_rate)

        monitoring_system.record_metric("api_requests_total", total_requests, MetricType.COUNTER)
        monitoring_system.record_metric("api_throughput_per_second", global_stats["throughput_per_second"])

    except Exception as e:
        logger.error(f"Error collecting API metrics: {e}")


# Register system integrations
monitoring_system.register_system_integration(collect_optimization_engine_metrics)
monitoring_system.register_system_integration(collect_database_metrics)
monitoring_system.register_system_integration(collect_api_metrics)