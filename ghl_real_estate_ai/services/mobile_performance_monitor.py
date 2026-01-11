"""
Mobile Performance Monitor (Phase 4: Mobile Optimization)

Comprehensive performance monitoring system specifically designed for mobile
Claude AI integration. Tracks mobile-specific metrics and optimizations.

Features:
- Mobile-specific performance metrics
- Battery usage monitoring
- Network efficiency tracking
- Voice processing performance
- Touch interaction analytics
- Real-time performance alerts
- Mobile optimization recommendations
- Automated performance tuning

Performance Targets:
- Voice processing: <100ms
- Claude integration: <150ms
- Battery impact: <5% per hour
- Data usage: 70% reduction vs desktop
- Touch response: <50ms
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
import time
import statistics
from collections import defaultdict, deque
import threading

# Local imports
from ghl_real_estate_ai.config.mobile.settings import (
    MOBILE_PERFORMANCE_TARGETS,
    MOBILE_CLAUDE_CONFIG,
    REALTIME_CONFIG
)

logger = logging.getLogger(__name__)


class MetricType(Enum):
    """Types of performance metrics"""
    RESPONSE_TIME = "response_time"
    BATTERY_USAGE = "battery_usage"
    DATA_USAGE = "data_usage"
    VOICE_PROCESSING = "voice_processing"
    TOUCH_INTERACTION = "touch_interaction"
    MEMORY_USAGE = "memory_usage"
    NETWORK_LATENCY = "network_latency"
    CACHE_PERFORMANCE = "cache_performance"


class AlertLevel(Enum):
    """Performance alert levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""
    metric_type: MetricType
    value: float
    unit: str
    timestamp: datetime
    agent_id: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    target_value: Optional[float] = None
    meets_target: Optional[bool] = None


@dataclass
class PerformanceAlert:
    """Performance alert notification"""
    alert_id: str
    level: AlertLevel
    metric_type: MetricType
    message: str
    value: float
    threshold: float
    agent_id: str
    timestamp: datetime
    recommendations: List[str] = field(default_factory=list)
    auto_action_taken: bool = False


@dataclass
class MobilePerformanceProfile:
    """Performance profile for a mobile device/agent"""
    agent_id: str
    device_info: Dict[str, Any]
    baseline_metrics: Dict[MetricType, float]
    current_performance: Dict[MetricType, float]
    optimization_history: List[Dict[str, Any]] = field(default_factory=list)
    last_updated: datetime = field(default_factory=datetime.now)


class MobilePerformanceMonitor:
    """
    📊 Mobile Performance Monitor for Claude AI

    Comprehensive monitoring system for mobile-specific performance
    metrics with real-time optimization and alerting.
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self.performance_targets = MOBILE_PERFORMANCE_TARGETS
        self.claude_config = MOBILE_CLAUDE_CONFIG
        self.realtime_config = REALTIME_CONFIG

        # Metric storage (time-series data)
        self.metrics: Dict[MetricType, deque] = {
            metric_type: deque(maxlen=10000)  # Keep last 10k metrics per type
            for metric_type in MetricType
        }

        # Real-time performance tracking
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.agent_profiles: Dict[str, MobilePerformanceProfile] = {}

        # Alert management
        self.active_alerts: List[PerformanceAlert] = []
        self.alert_history: deque = deque(maxlen=1000)

        # Performance thresholds
        self.thresholds = self._initialize_performance_thresholds()

        # Optimization recommendations cache
        self.optimization_cache: Dict[str, List[str]] = {}

        # Background monitoring
        self._monitoring_task = None
        self._performance_lock = threading.Lock()

    def _initialize_performance_thresholds(self) -> Dict[MetricType, Dict[str, float]]:
        """Initialize performance thresholds for alerts"""
        return {
            MetricType.RESPONSE_TIME: {
                "warning": 200,  # 200ms
                "critical": 500,  # 500ms
                "emergency": 1000  # 1 second
            },
            MetricType.VOICE_PROCESSING: {
                "warning": 150,  # 150ms
                "critical": 300,  # 300ms
                "emergency": 1000  # 1 second
            },
            MetricType.BATTERY_USAGE: {
                "warning": 8.0,  # 8% per hour
                "critical": 15.0,  # 15% per hour
                "emergency": 25.0  # 25% per hour
            },
            MetricType.DATA_USAGE: {
                "warning": 10.0,  # 10MB per hour
                "critical": 50.0,  # 50MB per hour
                "emergency": 100.0  # 100MB per hour
            },
            MetricType.MEMORY_USAGE: {
                "warning": 100.0,  # 100MB
                "critical": 200.0,  # 200MB
                "emergency": 500.0  # 500MB
            },
            MetricType.NETWORK_LATENCY: {
                "warning": 100,  # 100ms
                "critical": 500,  # 500ms
                "emergency": 2000  # 2 seconds
            }
        }

    async def start_monitoring(self):
        """Start background performance monitoring"""
        if self._monitoring_task and not self._monitoring_task.done():
            return  # Already running

        self._monitoring_task = asyncio.create_task(self._monitoring_worker())
        logger.info("Mobile performance monitoring started")

    async def stop_monitoring(self):
        """Stop background performance monitoring"""
        if self._monitoring_task and not self._monitoring_task.done():
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass

        logger.info("Mobile performance monitoring stopped")

    def record_metric(
        self,
        metric_type: MetricType,
        value: float,
        unit: str,
        agent_id: str,
        session_id: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> PerformanceMetric:
        """
        Record a performance metric

        Args:
            metric_type: Type of metric
            value: Metric value
            unit: Unit of measurement
            agent_id: Agent identifier
            session_id: Optional session identifier
            context: Additional context data

        Returns:
            PerformanceMetric object
        """
        with self._performance_lock:
            # Get target value for this metric type
            target_value = self._get_target_value(metric_type)

            # Create metric
            metric = PerformanceMetric(
                metric_type=metric_type,
                value=value,
                unit=unit,
                timestamp=datetime.now(),
                agent_id=agent_id,
                session_id=session_id,
                context=context or {},
                target_value=target_value,
                meets_target=value <= target_value if target_value else None
            )

            # Store metric
            self.metrics[metric_type].append(metric)

            # Update agent profile
            self._update_agent_profile(agent_id, metric)

            # Check for alerts
            self._check_performance_alerts(metric)

            logger.debug(f"Recorded {metric_type.value}: {value}{unit} for agent {agent_id}")
            return metric

    def record_voice_processing_time(
        self,
        agent_id: str,
        processing_time_ms: float,
        session_id: Optional[str] = None,
        audio_quality: float = 0.0,
        context: Dict[str, Any] = None
    ):
        """Record voice processing performance"""
        self.record_metric(
            metric_type=MetricType.VOICE_PROCESSING,
            value=processing_time_ms,
            unit="ms",
            agent_id=agent_id,
            session_id=session_id,
            context={
                "audio_quality": audio_quality,
                **(context or {})
            }
        )

    def record_claude_response_time(
        self,
        agent_id: str,
        response_time_ms: float,
        session_id: Optional[str] = None,
        request_type: str = "coaching",
        context: Dict[str, Any] = None
    ):
        """Record Claude AI response time"""
        self.record_metric(
            metric_type=MetricType.RESPONSE_TIME,
            value=response_time_ms,
            unit="ms",
            agent_id=agent_id,
            session_id=session_id,
            context={
                "request_type": request_type,
                **(context or {})
            }
        )

    def record_battery_usage(
        self,
        agent_id: str,
        battery_drain_percent_per_hour: float,
        current_battery_level: float,
        context: Dict[str, Any] = None
    ):
        """Record battery usage metrics"""
        self.record_metric(
            metric_type=MetricType.BATTERY_USAGE,
            value=battery_drain_percent_per_hour,
            unit="%/hour",
            agent_id=agent_id,
            context={
                "current_battery_level": current_battery_level,
                **(context or {})
            }
        )

    def record_data_usage(
        self,
        agent_id: str,
        data_usage_mb: float,
        session_id: Optional[str] = None,
        data_type: str = "api_calls",
        context: Dict[str, Any] = None
    ):
        """Record data usage metrics"""
        self.record_metric(
            metric_type=MetricType.DATA_USAGE,
            value=data_usage_mb,
            unit="MB",
            agent_id=agent_id,
            session_id=session_id,
            context={
                "data_type": data_type,
                **(context or {})
            }
        )

    def record_touch_interaction(
        self,
        agent_id: str,
        interaction_time_ms: float,
        interaction_type: str,
        context: Dict[str, Any] = None
    ):
        """Record touch interaction performance"""
        self.record_metric(
            metric_type=MetricType.TOUCH_INTERACTION,
            value=interaction_time_ms,
            unit="ms",
            agent_id=agent_id,
            context={
                "interaction_type": interaction_type,
                **(context or {})
            }
        )

    def _get_target_value(self, metric_type: MetricType) -> Optional[float]:
        """Get target value for metric type"""
        target_map = {
            MetricType.RESPONSE_TIME: self.performance_targets.get("claude_integration_time"),
            MetricType.VOICE_PROCESSING: self.performance_targets.get("voice_response_time"),
            MetricType.BATTERY_USAGE: 5.0,  # 5% per hour target
            MetricType.DATA_USAGE: 5.0,  # 5MB per hour target
            MetricType.TOUCH_INTERACTION: self.performance_targets.get("ui_render_time"),
            MetricType.MEMORY_USAGE: 50.0,  # 50MB target
            MetricType.NETWORK_LATENCY: 50.0  # 50ms target
        }
        return target_map.get(metric_type)

    def _update_agent_profile(self, agent_id: str, metric: PerformanceMetric):
        """Update agent performance profile"""
        if agent_id not in self.agent_profiles:
            self.agent_profiles[agent_id] = MobilePerformanceProfile(
                agent_id=agent_id,
                device_info={},
                baseline_metrics={},
                current_performance={}
            )

        profile = self.agent_profiles[agent_id]
        profile.current_performance[metric.metric_type] = metric.value
        profile.last_updated = metric.timestamp

    def _check_performance_alerts(self, metric: PerformanceMetric):
        """Check if metric triggers performance alerts"""
        thresholds = self.thresholds.get(metric.metric_type)
        if not thresholds:
            return

        alert_level = None
        threshold_value = None

        if metric.value >= thresholds.get("emergency", float('inf')):
            alert_level = AlertLevel.EMERGENCY
            threshold_value = thresholds["emergency"]
        elif metric.value >= thresholds.get("critical", float('inf')):
            alert_level = AlertLevel.CRITICAL
            threshold_value = thresholds["critical"]
        elif metric.value >= thresholds.get("warning", float('inf')):
            alert_level = AlertLevel.WARNING
            threshold_value = thresholds["warning"]

        if alert_level:
            self._create_performance_alert(metric, alert_level, threshold_value)

    def _create_performance_alert(
        self,
        metric: PerformanceMetric,
        level: AlertLevel,
        threshold: float
    ):
        """Create performance alert"""
        alert_id = f"{metric.agent_id}_{metric.metric_type.value}_{int(time.time())}"

        # Generate recommendations
        recommendations = self._generate_optimization_recommendations(metric, level)

        alert = PerformanceAlert(
            alert_id=alert_id,
            level=level,
            metric_type=metric.metric_type,
            message=self._format_alert_message(metric, level, threshold),
            value=metric.value,
            threshold=threshold,
            agent_id=metric.agent_id,
            timestamp=metric.timestamp,
            recommendations=recommendations
        )

        # Take automatic action for critical/emergency alerts
        if level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]:
            self._take_automatic_action(alert, metric)

        self.active_alerts.append(alert)
        self.alert_history.append(alert)

        logger.warning(f"Performance alert: {alert.message}")

    def _format_alert_message(
        self,
        metric: PerformanceMetric,
        level: AlertLevel,
        threshold: float
    ) -> str:
        """Format alert message"""
        return (
            f"{level.value.upper()}: {metric.metric_type.value} "
            f"({metric.value}{metric.unit}) exceeded threshold ({threshold}{metric.unit}) "
            f"for agent {metric.agent_id}"
        )

    def _generate_optimization_recommendations(
        self,
        metric: PerformanceMetric,
        level: AlertLevel
    ) -> List[str]:
        """Generate optimization recommendations"""
        recommendations = []

        if metric.metric_type == MetricType.RESPONSE_TIME:
            recommendations.extend([
                "Switch to battery saver mode",
                "Enable aggressive caching",
                "Reduce coaching frequency",
                "Use offline coaching suggestions"
            ])

        elif metric.metric_type == MetricType.VOICE_PROCESSING:
            recommendations.extend([
                "Reduce audio quality settings",
                "Enable audio compression",
                "Use shorter audio chunks",
                "Switch to text-only mode"
            ])

        elif metric.metric_type == MetricType.BATTERY_USAGE:
            recommendations.extend([
                "Enable battery saver mode",
                "Reduce background processing",
                "Lower screen brightness",
                "Disable real-time features"
            ])

        elif metric.metric_type == MetricType.DATA_USAGE:
            recommendations.extend([
                "Enable data compression",
                "Switch to offline mode",
                "Reduce API call frequency",
                "Use cached responses"
            ])

        return recommendations

    def _take_automatic_action(self, alert: PerformanceAlert, metric: PerformanceMetric):
        """Take automatic corrective action"""
        try:
            if alert.metric_type == MetricType.BATTERY_USAGE and alert.level == AlertLevel.EMERGENCY:
                # Switch to battery saver mode
                self._enable_battery_saver_mode(alert.agent_id)
                alert.auto_action_taken = True

            elif alert.metric_type == MetricType.DATA_USAGE and alert.level == AlertLevel.CRITICAL:
                # Enable aggressive compression
                self._enable_data_compression(alert.agent_id)
                alert.auto_action_taken = True

            elif alert.metric_type == MetricType.RESPONSE_TIME and alert.level == AlertLevel.EMERGENCY:
                # Switch to offline mode
                self._enable_offline_mode(alert.agent_id)
                alert.auto_action_taken = True

        except Exception as e:
            logger.error(f"Error taking automatic action for alert {alert.alert_id}: {e}")

    def _enable_battery_saver_mode(self, agent_id: str):
        """Enable battery saver mode for agent"""
        logger.info(f"Auto-enabled battery saver mode for agent {agent_id}")
        # This would integrate with mobile coaching service to change mode

    def _enable_data_compression(self, agent_id: str):
        """Enable data compression for agent"""
        logger.info(f"Auto-enabled data compression for agent {agent_id}")
        # This would update service configurations

    def _enable_offline_mode(self, agent_id: str):
        """Enable offline mode for agent"""
        logger.info(f"Auto-enabled offline mode for agent {agent_id}")
        # This would switch to cached responses only

    async def _monitoring_worker(self):
        """Background monitoring worker"""
        while True:
            try:
                await self._perform_periodic_checks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in monitoring worker: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _perform_periodic_checks(self):
        """Perform periodic performance checks"""
        # Clean up old metrics
        self._cleanup_old_metrics()

        # Clean up resolved alerts
        self._cleanup_resolved_alerts()

        # Update performance trends
        self._update_performance_trends()

    def _cleanup_old_metrics(self):
        """Remove metrics older than retention period"""
        cutoff_time = datetime.now() - timedelta(hours=self.retention_hours)

        for metric_type in MetricType:
            metrics_deque = self.metrics[metric_type]
            # Remove old metrics from the front of deque
            while metrics_deque and metrics_deque[0].timestamp < cutoff_time:
                metrics_deque.popleft()

    def _cleanup_resolved_alerts(self):
        """Remove resolved alerts"""
        # Remove alerts older than 1 hour that are not critical
        cutoff_time = datetime.now() - timedelta(hours=1)

        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp > cutoff_time or alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY]
        ]

    def _update_performance_trends(self):
        """Update performance trends and baselines"""
        for agent_id, profile in self.agent_profiles.items():
            # Update baseline metrics if we have enough data
            for metric_type in MetricType:
                recent_metrics = [
                    m for m in self.metrics[metric_type]
                    if m.agent_id == agent_id and
                    m.timestamp > datetime.now() - timedelta(hours=1)
                ]

                if len(recent_metrics) >= 5:  # Need at least 5 metrics
                    values = [m.value for m in recent_metrics]
                    baseline = statistics.median(values)
                    profile.baseline_metrics[metric_type] = baseline

    def get_agent_performance_summary(self, agent_id: str) -> Dict[str, Any]:
        """Get performance summary for an agent"""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return {"error": "Agent profile not found"}

        # Calculate recent performance
        recent_metrics = {}
        for metric_type in MetricType:
            recent = [
                m for m in self.metrics[metric_type]
                if m.agent_id == agent_id and
                m.timestamp > datetime.now() - timedelta(minutes=30)
            ]

            if recent:
                values = [m.value for m in recent]
                recent_metrics[metric_type.value] = {
                    "current": values[-1],
                    "average": statistics.mean(values),
                    "min": min(values),
                    "max": max(values),
                    "count": len(values)
                }

        # Get active alerts for this agent
        agent_alerts = [
            alert for alert in self.active_alerts
            if alert.agent_id == agent_id
        ]

        return {
            "agent_id": agent_id,
            "last_updated": profile.last_updated.isoformat(),
            "recent_performance": recent_metrics,
            "baseline_metrics": {
                k.value: v for k, v in profile.baseline_metrics.items()
            },
            "active_alerts": [
                {
                    "level": alert.level.value,
                    "metric": alert.metric_type.value,
                    "message": alert.message,
                    "recommendations": alert.recommendations
                }
                for alert in agent_alerts
            ],
            "performance_score": self._calculate_performance_score(agent_id)
        }

    def _calculate_performance_score(self, agent_id: str) -> float:
        """Calculate overall performance score for agent (0-100)"""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return 0.0

        score = 100.0

        # Deduct points for active alerts
        for alert in [a for a in self.active_alerts if a.agent_id == agent_id]:
            if alert.level == AlertLevel.EMERGENCY:
                score -= 30
            elif alert.level == AlertLevel.CRITICAL:
                score -= 20
            elif alert.level == AlertLevel.WARNING:
                score -= 10

        # Deduct points for poor performance metrics
        for metric_type, current_value in profile.current_performance.items():
            target_value = self._get_target_value(metric_type)
            if target_value and current_value > target_value:
                # Performance below target
                ratio = current_value / target_value
                if ratio > 2:  # More than 2x target
                    score -= 15
                elif ratio > 1.5:  # 1.5-2x target
                    score -= 10
                elif ratio > 1.2:  # 1.2-1.5x target
                    score -= 5

        return max(0.0, score)

    def get_system_performance_overview(self) -> Dict[str, Any]:
        """Get overall system performance overview"""
        total_agents = len(self.agent_profiles)
        total_alerts = len(self.active_alerts)

        # Alert breakdown
        alert_breakdown = defaultdict(int)
        for alert in self.active_alerts:
            alert_breakdown[alert.level.value] += 1

        # Recent metric summary
        metric_summary = {}
        for metric_type in MetricType:
            recent_values = [
                m.value for m in self.metrics[metric_type]
                if m.timestamp > datetime.now() - timedelta(minutes=30)
            ]

            if recent_values:
                metric_summary[metric_type.value] = {
                    "count": len(recent_values),
                    "average": statistics.mean(recent_values),
                    "p95": statistics.quantiles(recent_values, n=20)[18] if len(recent_values) >= 20 else max(recent_values)
                }

        # Performance scores
        performance_scores = [
            self._calculate_performance_score(agent_id)
            for agent_id in self.agent_profiles.keys()
        ]

        avg_performance_score = statistics.mean(performance_scores) if performance_scores else 0

        return {
            "system_health": {
                "total_agents": total_agents,
                "average_performance_score": avg_performance_score,
                "healthy_agents": len([s for s in performance_scores if s >= 80]),
                "degraded_agents": len([s for s in performance_scores if 60 <= s < 80]),
                "critical_agents": len([s for s in performance_scores if s < 60])
            },
            "alerts": {
                "total_active": total_alerts,
                "breakdown": dict(alert_breakdown),
                "critical_issues": alert_breakdown["critical"] + alert_breakdown["emergency"]
            },
            "recent_metrics": metric_summary,
            "performance_targets": {
                "voice_processing_ms": self.performance_targets.get("voice_response_time"),
                "claude_integration_ms": self.performance_targets.get("claude_integration_time"),
                "ui_render_ms": self.performance_targets.get("ui_render_time")
            },
            "timestamp": datetime.now().isoformat()
        }

    def get_optimization_recommendations(self, agent_id: str) -> List[Dict[str, Any]]:
        """Get optimization recommendations for an agent"""
        profile = self.agent_profiles.get(agent_id)
        if not profile:
            return []

        recommendations = []

        # Check recent alerts for recommendations
        recent_alerts = [
            alert for alert in self.active_alerts
            if alert.agent_id == agent_id and
            alert.timestamp > datetime.now() - timedelta(hours=1)
        ]

        for alert in recent_alerts:
            for rec in alert.recommendations:
                recommendations.append({
                    "type": "alert_based",
                    "priority": alert.level.value,
                    "metric": alert.metric_type.value,
                    "recommendation": rec,
                    "impact": "high" if alert.level in [AlertLevel.CRITICAL, AlertLevel.EMERGENCY] else "medium"
                })

        # Add proactive recommendations based on trends
        for metric_type, current_value in profile.current_performance.items():
            baseline = profile.baseline_metrics.get(metric_type)
            target = self._get_target_value(metric_type)

            if baseline and current_value > baseline * 1.2:  # 20% worse than baseline
                recommendations.append({
                    "type": "trend_based",
                    "priority": "medium",
                    "metric": metric_type.value,
                    "recommendation": f"Performance degradation detected in {metric_type.value}",
                    "impact": "medium"
                })

        return recommendations[:10]  # Return top 10 recommendations