"""
Enterprise Scaling Monitor for Phase 4 Infrastructure

Provides comprehensive monitoring and alerting for:
- Redis cluster health and performance
- Database shard health and query performance
- Cross-system latency tracking
- Automatic scaling recommendations

Performance Targets:
- Redis cluster: 99.95% uptime, <1ms latency
- Database sharding: <50ms P90 single-shard, <100ms P95 cross-shard
- Real-time alerting: <5 second detection time
- Dashboard refresh: <1 second

Integration:
- Phase 2 optimizations (connection pools, indexes, caching)
- GHL webhook performance monitoring
- ML inference latency tracking
"""

import asyncio
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Callable
from collections import defaultdict, deque
from enum import Enum
import json
import logging

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


class ComponentType(str, Enum):
    """Infrastructure component types."""
    REDIS_CLUSTER = "redis_cluster"
    DATABASE_SHARD = "database_shard"
    CONNECTION_POOL = "connection_pool"
    ML_INFERENCE = "ml_inference"
    GHL_WEBHOOK = "ghl_webhook"
    CACHE = "cache"


@dataclass
class PerformanceTarget:
    """Performance target configuration."""
    component: ComponentType
    metric_name: str
    target_value: float
    threshold_warning: float
    threshold_critical: float
    unit: str = "ms"
    description: str = ""


@dataclass
class Alert:
    """Infrastructure alert."""
    alert_id: str
    component: ComponentType
    severity: AlertSeverity
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        result['timestamp'] = self.timestamp.isoformat()
        if self.resolved_at:
            result['resolved_at'] = self.resolved_at.isoformat()
        return result


@dataclass
class ComponentHealth:
    """Health status for a component."""
    component: ComponentType
    component_id: str
    is_healthy: bool = True
    health_score: float = 100.0

    # Performance metrics
    avg_latency_ms: float = 0.0
    p95_latency_ms: float = 0.0
    p99_latency_ms: float = 0.0
    error_rate: float = 0.0

    # Availability
    uptime_percent: float = 99.95
    last_downtime: Optional[datetime] = None
    consecutive_failures: int = 0

    # Resource utilization
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    connection_utilization: float = 0.0

    # Timestamps
    last_check: Optional[datetime] = None
    last_healthy: Optional[datetime] = None


@dataclass
class ScalingRecommendation:
    """Automatic scaling recommendation."""
    recommendation_id: str
    component: ComponentType
    component_id: str
    recommendation_type: str  # scale_up, scale_down, add_replica, remove_shard, etc.
    reason: str
    urgency: str  # immediate, scheduled, advisory
    estimated_impact: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    applied: bool = False
    applied_at: Optional[datetime] = None


class EnterpriseScalingMonitor:
    """
    Comprehensive monitoring for Phase 4 enterprise infrastructure.

    Features:
    - Real-time health monitoring
    - Performance target tracking
    - Automatic alerting
    - Scaling recommendations
    - Integration with existing Phase 2 optimizations
    """

    def __init__(self):
        """Initialize enterprise scaling monitor."""

        # Performance targets (Phase 4 requirements)
        self.performance_targets: List[PerformanceTarget] = [
            # Redis cluster targets
            PerformanceTarget(
                component=ComponentType.REDIS_CLUSTER,
                metric_name="avg_latency",
                target_value=1.0,
                threshold_warning=3.0,
                threshold_critical=5.0,
                unit="ms",
                description="Redis cluster average operation latency"
            ),
            PerformanceTarget(
                component=ComponentType.REDIS_CLUSTER,
                metric_name="uptime",
                target_value=99.95,
                threshold_warning=99.9,
                threshold_critical=99.5,
                unit="%",
                description="Redis cluster uptime percentage"
            ),
            PerformanceTarget(
                component=ComponentType.REDIS_CLUSTER,
                metric_name="replication_lag",
                target_value=100.0,
                threshold_warning=500.0,
                threshold_critical=1000.0,
                unit="ms",
                description="Maximum replication lag across cluster"
            ),

            # Database shard targets
            PerformanceTarget(
                component=ComponentType.DATABASE_SHARD,
                metric_name="p90_latency",
                target_value=50.0,
                threshold_warning=100.0,
                threshold_critical=200.0,
                unit="ms",
                description="Database P90 query latency"
            ),
            PerformanceTarget(
                component=ComponentType.DATABASE_SHARD,
                metric_name="cross_shard_p95",
                target_value=100.0,
                threshold_warning=150.0,
                threshold_critical=300.0,
                unit="ms",
                description="Cross-shard query P95 latency"
            ),

            # Connection pool targets
            PerformanceTarget(
                component=ComponentType.CONNECTION_POOL,
                metric_name="acquisition_time",
                target_value=5.0,
                threshold_warning=20.0,
                threshold_critical=50.0,
                unit="ms",
                description="Connection pool acquisition time"
            ),
            PerformanceTarget(
                component=ComponentType.CONNECTION_POOL,
                metric_name="utilization",
                target_value=70.0,
                threshold_warning=85.0,
                threshold_critical=95.0,
                unit="%",
                description="Connection pool utilization"
            ),

            # ML inference targets
            PerformanceTarget(
                component=ComponentType.ML_INFERENCE,
                metric_name="inference_time",
                target_value=500.0,
                threshold_warning=800.0,
                threshold_critical=1000.0,
                unit="ms",
                description="ML model inference time"
            ),

            # GHL webhook targets
            PerformanceTarget(
                component=ComponentType.GHL_WEBHOOK,
                metric_name="processing_time",
                target_value=1000.0,
                threshold_warning=2000.0,
                threshold_critical=5000.0,
                unit="ms",
                description="GHL webhook processing time"
            ),

            # Cache targets (integrated with Phase 2)
            PerformanceTarget(
                component=ComponentType.CACHE,
                metric_name="hit_rate",
                target_value=95.0,
                threshold_warning=85.0,
                threshold_critical=70.0,
                unit="%",
                description="Cache hit rate percentage"
            ),
        ]

        # Component health tracking
        self.component_health: Dict[str, ComponentHealth] = {}

        # Alert management
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: deque = deque(maxlen=10000)

        # Scaling recommendations
        self.recommendations: List[ScalingRecommendation] = []

        # Metrics history for trend analysis
        self.metrics_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []

        # Monitor state
        self.initialized = False
        self.monitoring_active = False

        logger.info("Enterprise Scaling Monitor initialized")

    async def initialize(
        self,
        redis_cluster_manager=None,
        shard_manager=None
    ) -> bool:
        """
        Initialize monitoring with infrastructure managers.

        Args:
            redis_cluster_manager: Redis cluster manager instance
            shard_manager: Database shard manager instance

        Returns:
            True if initialization successful
        """
        try:
            self.redis_cluster_manager = redis_cluster_manager
            self.shard_manager = shard_manager

            # Start background monitoring
            self.background_tasks = [
                asyncio.create_task(self._health_collection_worker()),
                asyncio.create_task(self._alert_evaluation_worker()),
                asyncio.create_task(self._scaling_advisor_worker()),
                asyncio.create_task(self._metrics_aggregation_worker()),
                asyncio.create_task(self._trend_analysis_worker()),
            ]

            self.initialized = True
            self.monitoring_active = True

            logger.info("Enterprise Scaling Monitor started")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize monitoring: {e}")
            return False

    async def record_metric(
        self,
        component: ComponentType,
        component_id: str,
        metric_name: str,
        value: float,
        tags: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Record a performance metric.

        Args:
            component: Component type
            component_id: Component identifier
            metric_name: Metric name
            value: Metric value
            tags: Optional metric tags
        """
        metric_key = f"{component.value}:{component_id}:{metric_name}"

        metric_entry = {
            "timestamp": time.time(),
            "component": component.value,
            "component_id": component_id,
            "metric_name": metric_name,
            "value": value,
            "tags": tags or {}
        }

        self.metrics_history[metric_key].append(metric_entry)

        # Update component health
        await self._update_component_health(component, component_id, metric_name, value)

        # Check for threshold violations
        await self._check_thresholds(component, component_id, metric_name, value)

    async def _update_component_health(
        self,
        component: ComponentType,
        component_id: str,
        metric_name: str,
        value: float
    ) -> None:
        """Update component health based on metric."""
        health_key = f"{component.value}:{component_id}"

        if health_key not in self.component_health:
            self.component_health[health_key] = ComponentHealth(
                component=component,
                component_id=component_id
            )

        health = self.component_health[health_key]
        health.last_check = datetime.utcnow()

        # Update specific metrics
        if metric_name == "avg_latency":
            health.avg_latency_ms = value
        elif metric_name == "p95_latency":
            health.p95_latency_ms = value
        elif metric_name == "p99_latency":
            health.p99_latency_ms = value
        elif metric_name == "error_rate":
            health.error_rate = value
        elif metric_name == "uptime":
            health.uptime_percent = value
        elif metric_name == "cpu_percent":
            health.cpu_percent = value
        elif metric_name == "memory_percent":
            health.memory_percent = value

        # Calculate overall health score
        health.health_score = self._calculate_health_score(health)
        health.is_healthy = health.health_score >= 80

        if health.is_healthy:
            health.last_healthy = datetime.utcnow()
            health.consecutive_failures = 0
        else:
            health.consecutive_failures += 1

    def _calculate_health_score(self, health: ComponentHealth) -> float:
        """Calculate overall health score (0-100)."""
        score = 100.0

        # Latency impact (up to -30 points)
        if health.avg_latency_ms > 0:
            target = self._get_target_for_metric(health.component, "avg_latency")
            if target and health.avg_latency_ms > target.target_value:
                latency_penalty = min(30, (health.avg_latency_ms / target.target_value - 1) * 10)
                score -= latency_penalty

        # Error rate impact (up to -40 points)
        if health.error_rate > 0:
            error_penalty = min(40, health.error_rate * 10)
            score -= error_penalty

        # Uptime impact (up to -30 points)
        if health.uptime_percent < 99.95:
            uptime_penalty = min(30, (99.95 - health.uptime_percent) * 10)
            score -= uptime_penalty

        return max(0.0, score)

    def _get_target_for_metric(
        self,
        component: ComponentType,
        metric_name: str
    ) -> Optional[PerformanceTarget]:
        """Get performance target for a metric."""
        for target in self.performance_targets:
            if target.component == component and target.metric_name == metric_name:
                return target
        return None

    async def _check_thresholds(
        self,
        component: ComponentType,
        component_id: str,
        metric_name: str,
        value: float
    ) -> None:
        """Check if metric violates thresholds."""
        target = self._get_target_for_metric(component, metric_name)

        if not target:
            return

        alert_id = f"{component.value}:{component_id}:{metric_name}"

        # Determine if threshold is exceeded
        # For some metrics, lower is worse (uptime, hit_rate)
        inverse_metrics = {"uptime", "hit_rate"}

        if metric_name in inverse_metrics:
            is_critical = value < target.threshold_critical
            is_warning = value < target.threshold_warning
        else:
            is_critical = value > target.threshold_critical
            is_warning = value > target.threshold_warning

        if is_critical:
            await self._create_or_update_alert(
                alert_id=alert_id,
                component=component,
                severity=AlertSeverity.CRITICAL,
                message=f"{target.description} is critical: {value:.2f}{target.unit}",
                metric_name=metric_name,
                current_value=value,
                threshold=target.threshold_critical
            )
        elif is_warning:
            await self._create_or_update_alert(
                alert_id=alert_id,
                component=component,
                severity=AlertSeverity.WARNING,
                message=f"{target.description} is elevated: {value:.2f}{target.unit}",
                metric_name=metric_name,
                current_value=value,
                threshold=target.threshold_warning
            )
        else:
            # Resolve existing alert if threshold is no longer exceeded
            if alert_id in self.active_alerts:
                await self._resolve_alert(alert_id)

    async def _create_or_update_alert(
        self,
        alert_id: str,
        component: ComponentType,
        severity: AlertSeverity,
        message: str,
        metric_name: str,
        current_value: float,
        threshold: float
    ) -> None:
        """Create or update an alert."""
        if alert_id in self.active_alerts:
            # Update existing alert
            alert = self.active_alerts[alert_id]
            alert.severity = severity
            alert.message = message
            alert.current_value = current_value
            alert.timestamp = datetime.utcnow()
        else:
            # Create new alert
            alert = Alert(
                alert_id=alert_id,
                component=component,
                severity=severity,
                message=message,
                metric_name=metric_name,
                current_value=current_value,
                threshold=threshold
            )
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)

            # Notify callbacks
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(alert)
                    else:
                        callback(alert)
                except Exception as e:
                    logger.error(f"Alert callback error: {e}")

            logger.warning(f"Alert created: {alert.message}")

    async def _resolve_alert(self, alert_id: str) -> None:
        """Resolve an active alert."""
        if alert_id in self.active_alerts:
            alert = self.active_alerts[alert_id]
            alert.resolved = True
            alert.resolved_at = datetime.utcnow()

            del self.active_alerts[alert_id]
            logger.info(f"Alert resolved: {alert_id}")

    # Background workers
    async def _health_collection_worker(self) -> None:
        """Collect health metrics from all components."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(5)  # Collect every 5 seconds

                # Collect from Redis cluster
                if self.redis_cluster_manager:
                    await self._collect_redis_metrics()

                # Collect from database shards
                if self.shard_manager:
                    await self._collect_shard_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health collection error: {e}")

    async def _collect_redis_metrics(self) -> None:
        """Collect metrics from Redis cluster."""
        try:
            health = await self.redis_cluster_manager.get_cluster_health()
            perf = await self.redis_cluster_manager.get_performance_metrics()

            await self.record_metric(
                ComponentType.REDIS_CLUSTER,
                "cluster",
                "avg_latency",
                health.get("avg_latency_ms", 0)
            )

            await self.record_metric(
                ComponentType.REDIS_CLUSTER,
                "cluster",
                "replication_lag",
                health.get("max_replication_lag_ms", 0)
            )

            if perf.get("latency"):
                await self.record_metric(
                    ComponentType.REDIS_CLUSTER,
                    "cluster",
                    "p99_latency",
                    perf["latency"].get("p99_ms", 0)
                )

        except Exception as e:
            logger.error(f"Redis metrics collection error: {e}")

    async def _collect_shard_metrics(self) -> None:
        """Collect metrics from database shards."""
        try:
            health = await self.shard_manager.get_shard_health()

            for shard_id, shard_data in health.get("shards", {}).items():
                await self.record_metric(
                    ComponentType.DATABASE_SHARD,
                    shard_id,
                    "avg_latency",
                    shard_data.get("avg_query_time_ms", 0)
                )

                await self.record_metric(
                    ComponentType.DATABASE_SHARD,
                    shard_id,
                    "p95_latency",
                    shard_data.get("p95_query_time_ms", 0)
                )

            # Cross-shard metrics
            cross_shard = health.get("cross_shard", {})
            if cross_shard:
                await self.record_metric(
                    ComponentType.DATABASE_SHARD,
                    "cross_shard",
                    "cross_shard_p95",
                    cross_shard.get("avg_time_ms", 0)
                )

        except Exception as e:
            logger.error(f"Shard metrics collection error: {e}")

    async def _alert_evaluation_worker(self) -> None:
        """Evaluate and manage alerts."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(10)  # Evaluate every 10 seconds

                # Check for stale alerts
                current_time = datetime.utcnow()
                for alert_id, alert in list(self.active_alerts.items()):
                    age = (current_time - alert.timestamp).total_seconds()

                    # Auto-escalate long-running alerts
                    if age > 300 and alert.severity == AlertSeverity.WARNING:  # 5 minutes
                        alert.severity = AlertSeverity.CRITICAL
                        logger.warning(f"Alert escalated to critical: {alert_id}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Alert evaluation error: {e}")

    async def _scaling_advisor_worker(self) -> None:
        """Generate scaling recommendations."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(60)  # Analyze every minute

                await self._analyze_scaling_needs()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scaling advisor error: {e}")

    async def _analyze_scaling_needs(self) -> None:
        """Analyze metrics and generate scaling recommendations."""
        # Check connection pool utilization
        for health_key, health in self.component_health.items():
            if health.component == ComponentType.CONNECTION_POOL:
                if health.connection_utilization > 85:
                    recommendation = ScalingRecommendation(
                        recommendation_id=f"scale_{health.component_id}_{int(time.time())}",
                        component=health.component,
                        component_id=health.component_id,
                        recommendation_type="scale_up",
                        reason=f"Connection pool utilization at {health.connection_utilization:.1f}%",
                        urgency="scheduled" if health.connection_utilization < 95 else "immediate",
                        estimated_impact="Prevent connection exhaustion, improve latency"
                    )
                    self.recommendations.append(recommendation)
                    logger.info(f"Scaling recommendation: {recommendation.reason}")

        # Check database shard balance
        if self.shard_manager:
            try:
                health = await self.shard_manager.get_shard_health()
                routing = health.get("routing", {})

                if routing.get("balance_score", 100) < 70:
                    recommendation = ScalingRecommendation(
                        recommendation_id=f"rebalance_{int(time.time())}",
                        component=ComponentType.DATABASE_SHARD,
                        component_id="all",
                        recommendation_type="rebalance",
                        reason=f"Shard balance score at {routing['balance_score']:.1f}%",
                        urgency="scheduled",
                        estimated_impact="Improve query distribution and latency consistency"
                    )
                    self.recommendations.append(recommendation)

            except Exception as e:
                logger.error(f"Shard analysis error: {e}")

    async def _metrics_aggregation_worker(self) -> None:
        """Aggregate metrics for reporting."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(60)  # Aggregate every minute

                # Calculate aggregate metrics
                await self._calculate_aggregate_metrics()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Metrics aggregation error: {e}")

    async def _calculate_aggregate_metrics(self) -> None:
        """Calculate aggregate metrics across all components."""
        # Aggregate latencies by component type
        component_latencies = defaultdict(list)

        for metric_key, history in self.metrics_history.items():
            if not history:
                continue

            recent = [m["value"] for m in history if time.time() - m["timestamp"] < 300]
            if recent:
                component = metric_key.split(":")[0]
                component_latencies[component].extend(recent)

        # Log aggregate stats
        for component, latencies in component_latencies.items():
            if latencies:
                avg = sum(latencies) / len(latencies)
                logger.debug(f"{component} avg latency: {avg:.2f}ms")

    async def _trend_analysis_worker(self) -> None:
        """Analyze trends for predictive alerting."""
        while self.monitoring_active:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes

                await self._analyze_trends()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Trend analysis error: {e}")

    async def _analyze_trends(self) -> None:
        """Analyze metric trends for early warning."""
        for metric_key, history in self.metrics_history.items():
            if len(history) < 100:
                continue

            # Simple trend detection using linear regression-like approach
            values = [m["value"] for m in list(history)[-100:]]
            timestamps = [m["timestamp"] for m in list(history)[-100:]]

            # Calculate average slope
            if len(values) >= 2:
                time_span = timestamps[-1] - timestamps[0]
                if time_span > 0:
                    slope = (values[-1] - values[0]) / time_span

                    # Alert on concerning trends
                    if abs(slope) > 0.1:  # Significant change
                        component = metric_key.split(":")[0]
                        logger.info(
                            f"Trend detected for {metric_key}: "
                            f"{'increasing' if slope > 0 else 'decreasing'} "
                            f"at {abs(slope):.4f}/sec"
                        )

    async def close(self) -> None:
        """Stop monitoring and cleanup."""
        self.monitoring_active = False

        for task in self.background_tasks:
            task.cancel()

        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        logger.info("Enterprise Scaling Monitor stopped")

    def add_alert_callback(self, callback: Callable) -> None:
        """Add callback for alert notifications."""
        self.alert_callbacks.append(callback)

    async def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "components": {
                key: {
                    "health_score": h.health_score,
                    "is_healthy": h.is_healthy,
                    "avg_latency_ms": h.avg_latency_ms,
                    "p95_latency_ms": h.p95_latency_ms,
                    "error_rate": h.error_rate,
                    "uptime_percent": h.uptime_percent
                }
                for key, h in self.component_health.items()
            },
            "active_alerts": [a.to_dict() for a in self.active_alerts.values()],
            "alert_count": {
                "critical": len([a for a in self.active_alerts.values()
                               if a.severity == AlertSeverity.CRITICAL]),
                "warning": len([a for a in self.active_alerts.values()
                              if a.severity == AlertSeverity.WARNING])
            },
            "recommendations": [
                {
                    "id": r.recommendation_id,
                    "type": r.recommendation_type,
                    "reason": r.reason,
                    "urgency": r.urgency
                }
                for r in self.recommendations[-10:]  # Last 10 recommendations
            ],
            "performance_targets": [
                {
                    "component": t.component.value,
                    "metric": t.metric_name,
                    "target": t.target_value,
                    "unit": t.unit
                }
                for t in self.performance_targets
            ]
        }

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "summary": {
                "total_components": len(self.component_health),
                "healthy_components": len([h for h in self.component_health.values() if h.is_healthy]),
                "active_alerts": len(self.active_alerts),
                "recommendations": len(self.recommendations)
            },
            "targets_status": []
        }

        # Check each performance target
        for target in self.performance_targets:
            # Find current value from component health
            current_value = None
            for key, health in self.component_health.items():
                if health.component == target.component:
                    if target.metric_name == "avg_latency":
                        current_value = health.avg_latency_ms
                    elif target.metric_name == "p95_latency":
                        current_value = health.p95_latency_ms
                    # Add more mappings as needed

            if current_value is not None:
                met = (current_value <= target.target_value
                       if target.metric_name not in {"uptime", "hit_rate"}
                       else current_value >= target.target_value)

                report["targets_status"].append({
                    "component": target.component.value,
                    "metric": target.metric_name,
                    "target": target.target_value,
                    "current": current_value,
                    "unit": target.unit,
                    "met": met
                })

        return report


# Global monitor instance
_enterprise_monitor: Optional[EnterpriseScalingMonitor] = None


async def get_enterprise_monitor() -> EnterpriseScalingMonitor:
    """Get or create global enterprise monitor."""
    global _enterprise_monitor

    if _enterprise_monitor is None:
        _enterprise_monitor = EnterpriseScalingMonitor()

    return _enterprise_monitor


__all__ = [
    "EnterpriseScalingMonitor",
    "Alert",
    "AlertSeverity",
    "ComponentType",
    "ComponentHealth",
    "PerformanceTarget",
    "ScalingRecommendation",
    "get_enterprise_monitor",
]
