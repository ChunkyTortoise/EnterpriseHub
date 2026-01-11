"""
Intelligence Performance Monitor
Enhanced monitoring and analytics system for advanced dashboard components.

This module provides comprehensive performance tracking, user analytics,
and business intelligence for the intelligence dashboard system.

Features:
- Real-time performance monitoring
- User interaction analytics
- Claude AI service performance tracking
- Dashboard component performance metrics
- Business intelligence and ROI analytics
- Health monitoring and alerting
- Performance optimization recommendations

Created: January 10, 2026
Author: EnterpriseHub Development Team
"""

import asyncio
import json
import logging
import time
from collections import defaultdict, deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import redis.asyncio as redis
from pydantic import BaseModel, Field


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Performance Models
@dataclass
class PerformanceMetric:
    """Individual performance measurement."""
    component: str
    operation: str
    duration_ms: float
    timestamp: datetime
    metadata: Dict[str, Any]
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True
    error_details: Optional[str] = None


@dataclass
class ComponentPerformance:
    """Performance summary for a dashboard component."""
    component_name: str
    total_renders: int
    avg_render_time: float
    p95_render_time: float
    p99_render_time: float
    error_rate: float
    last_24h_usage: int
    performance_score: float  # 0-100


@dataclass
class UserInteractionEvent:
    """User interaction tracking."""
    event_type: str  # click, hover, scroll, filter_change, etc.
    component: str
    element_id: Optional[str]
    timestamp: datetime
    user_id: str
    session_id: str
    page_load_time: Optional[float] = None
    interaction_value: Optional[Any] = None
    metadata: Dict[str, Any] = None


@dataclass
class BusinessIntelligenceMetric:
    """Business impact measurements."""
    metric_name: str
    value: float
    unit: str  # percentage, dollars, minutes, etc.
    period: str  # daily, weekly, monthly
    timestamp: datetime
    comparison_period: Optional[float] = None
    trend_direction: str = "stable"  # up, down, stable


class ClaudeServiceMetrics(BaseModel):
    """Claude AI service performance metrics."""
    service_name: str
    avg_response_time: float
    requests_per_minute: int
    success_rate: float
    error_rate: float
    cache_hit_rate: float
    token_usage: int
    cost_per_request: float
    accuracy_score: Optional[float] = None


class DashboardHealthMetrics(BaseModel):
    """Overall dashboard system health."""
    uptime_percentage: float
    avg_page_load_time: float
    active_users_24h: int
    total_sessions_today: int
    data_freshness_score: float  # 0-100
    system_load: float
    memory_usage_mb: float
    redis_health: bool
    websocket_connections: int
    errors_per_hour: float


class IntelligencePerformanceMonitor:
    """
    Comprehensive performance monitoring and analytics system
    for the intelligence dashboard components.
    """

    def __init__(self, redis_url: str = "redis://localhost:6379/3"):
        """Initialize the performance monitor."""
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None

        # In-memory buffers for real-time metrics
        self.performance_buffer = deque(maxlen=1000)
        self.interaction_buffer = deque(maxlen=1000)
        self.metrics_cache = {}

        # Performance thresholds
        self.thresholds = {
            "component_render_time": 500,  # ms
            "claude_response_time": 200,  # ms
            "websocket_latency": 100,  # ms
            "error_rate": 0.05,  # 5%
            "cache_hit_rate": 0.80,  # 80%
        }

        # Business metrics tracking
        self.business_metrics = defaultdict(list)

    async def initialize(self) -> None:
        """Initialize Redis connection and monitoring systems."""
        try:
            self.redis_client = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )

            # Test connection
            await self.redis_client.ping()
            logger.info("Performance monitor initialized successfully")

            # Start background monitoring tasks
            asyncio.create_task(self.process_metrics_buffer())
            asyncio.create_task(self.calculate_periodic_metrics())

        except Exception as e:
            logger.error(f"Failed to initialize performance monitor: {e}")
            raise

    async def record_performance(
        self,
        component: str,
        operation: str,
        duration_ms: float,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        success: bool = True,
        error_details: Optional[str] = None
    ) -> None:
        """Record a performance measurement."""
        metric = PerformanceMetric(
            component=component,
            operation=operation,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            metadata=metadata or {},
            user_id=user_id,
            session_id=session_id,
            success=success,
            error_details=error_details
        )

        # Add to buffer for processing
        self.performance_buffer.append(metric)

        # Real-time alerting for severe performance issues
        if duration_ms > self.thresholds.get(f"{component}_render_time", 1000):
            await self._trigger_performance_alert(metric)

    async def record_user_interaction(
        self,
        event_type: str,
        component: str,
        user_id: str,
        session_id: str,
        element_id: Optional[str] = None,
        interaction_value: Optional[Any] = None,
        page_load_time: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a user interaction event."""
        interaction = UserInteractionEvent(
            event_type=event_type,
            component=component,
            element_id=element_id,
            timestamp=datetime.now(),
            user_id=user_id,
            session_id=session_id,
            page_load_time=page_load_time,
            interaction_value=interaction_value,
            metadata=metadata or {}
        )

        self.interaction_buffer.append(interaction)

        # Update real-time user analytics
        await self._update_user_analytics(interaction)

    async def get_component_performance(
        self,
        component: str,
        hours: int = 24
    ) -> ComponentPerformance:
        """Get performance summary for a specific component."""
        if not self.redis_client:
            raise ValueError("Monitor not initialized")

        # Retrieve metrics from Redis
        key_pattern = f"perf:{component}:*"
        keys = await self.redis_client.keys(key_pattern)

        if not keys:
            return ComponentPerformance(
                component_name=component,
                total_renders=0,
                avg_render_time=0.0,
                p95_render_time=0.0,
                p99_render_time=0.0,
                error_rate=0.0,
                last_24h_usage=0,
                performance_score=100.0
            )

        # Calculate metrics
        metrics = []
        errors = 0

        for key in keys:
            data = await self.redis_client.get(key)
            if data:
                metric = json.loads(data)
                metrics.append(metric["duration_ms"])
                if not metric.get("success", True):
                    errors += 1

        if not metrics:
            return ComponentPerformance(
                component_name=component,
                total_renders=0,
                avg_render_time=0.0,
                p95_render_time=0.0,
                p99_render_time=0.0,
                error_rate=0.0,
                last_24h_usage=0,
                performance_score=100.0
            )

        # Calculate statistics
        df = pd.Series(metrics)
        avg_time = float(df.mean())
        p95_time = float(df.quantile(0.95))
        p99_time = float(df.quantile(0.99))
        error_rate = errors / len(metrics) if metrics else 0

        # Calculate performance score (0-100)
        score = self._calculate_performance_score(
            avg_time, error_rate, component
        )

        return ComponentPerformance(
            component_name=component,
            total_renders=len(metrics),
            avg_render_time=avg_time,
            p95_render_time=p95_time,
            p99_render_time=p99_time,
            error_rate=error_rate,
            last_24h_usage=len(metrics),
            performance_score=score
        )

    async def get_claude_service_metrics(
        self,
        service_name: str,
        hours: int = 24
    ) -> ClaudeServiceMetrics:
        """Get Claude AI service performance metrics."""
        if not self.redis_client:
            raise ValueError("Monitor not initialized")

        # Get cached metrics or calculate fresh
        cache_key = f"claude_metrics:{service_name}:{hours}"
        cached = await self.redis_client.get(cache_key)

        if cached:
            return ClaudeServiceMetrics(**json.loads(cached))

        # Calculate fresh metrics
        metrics = await self._calculate_claude_metrics(service_name, hours)

        # Cache for 5 minutes
        await self.redis_client.setex(
            cache_key, 300, json.dumps(asdict(metrics))
        )

        return metrics

    async def get_dashboard_health(self) -> DashboardHealthMetrics:
        """Get overall dashboard system health metrics."""
        if not self.redis_client:
            raise ValueError("Monitor not initialized")

        # Calculate health metrics
        uptime = await self._calculate_uptime()
        page_load_times = await self._get_page_load_times()
        active_users = await self._count_active_users(24)
        sessions_today = await self._count_sessions_today()
        data_freshness = await self._calculate_data_freshness()
        errors_per_hour = await self._calculate_error_rate()

        return DashboardHealthMetrics(
            uptime_percentage=uptime,
            avg_page_load_time=page_load_times,
            active_users_24h=active_users,
            total_sessions_today=sessions_today,
            data_freshness_score=data_freshness,
            system_load=0.0,  # Would integrate with system monitoring
            memory_usage_mb=0.0,  # Would integrate with system monitoring
            redis_health=True,  # Basic Redis health check
            websocket_connections=await self._count_websocket_connections(),
            errors_per_hour=errors_per_hour
        )

    async def get_business_intelligence(
        self,
        metric_names: Optional[List[str]] = None,
        period: str = "daily"
    ) -> List[BusinessIntelligenceMetric]:
        """Get business intelligence metrics."""
        if not self.redis_client:
            raise ValueError("Monitor not initialized")

        # Default metrics if none specified
        if not metric_names:
            metric_names = [
                "agent_efficiency_improvement",
                "conversion_rate_increase",
                "decision_making_speed",
                "user_engagement_score",
                "feature_adoption_rate",
                "time_to_insight",
                "dashboard_roi"
            ]

        metrics = []

        for metric_name in metric_names:
            metric = await self._calculate_business_metric(metric_name, period)
            if metric:
                metrics.append(metric)

        return metrics

    async def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get AI-driven performance optimization recommendations."""
        recommendations = []

        # Analyze component performance
        components = ["journey_map", "sentiment_dashboard", "competitive_intel", "content_engine"]

        for component in components:
            perf = await self.get_component_performance(component)

            if perf.avg_render_time > self.thresholds["component_render_time"]:
                recommendations.append({
                    "type": "performance",
                    "component": component,
                    "issue": "Slow render time",
                    "current_value": f"{perf.avg_render_time:.1f}ms",
                    "threshold": f"{self.thresholds['component_render_time']}ms",
                    "recommendation": "Consider implementing data virtualization or lazy loading",
                    "priority": "high" if perf.avg_render_time > 1000 else "medium"
                })

            if perf.error_rate > self.thresholds["error_rate"]:
                recommendations.append({
                    "type": "reliability",
                    "component": component,
                    "issue": "High error rate",
                    "current_value": f"{perf.error_rate:.2%}",
                    "threshold": f"{self.thresholds['error_rate']:.2%}",
                    "recommendation": "Review error handling and add retry logic",
                    "priority": "high"
                })

        # Analyze Claude service performance
        claude_services = ["claude_agent_service", "semantic_analyzer", "action_planner"]

        for service in claude_services:
            claude_metrics = await self.get_claude_service_metrics(service)

            if claude_metrics.avg_response_time > self.thresholds["claude_response_time"]:
                recommendations.append({
                    "type": "claude_performance",
                    "component": service,
                    "issue": "Slow Claude API response",
                    "current_value": f"{claude_metrics.avg_response_time:.1f}ms",
                    "threshold": f"{self.thresholds['claude_response_time']}ms",
                    "recommendation": "Implement request batching or increase caching",
                    "priority": "medium"
                })

            if claude_metrics.cache_hit_rate < self.thresholds["cache_hit_rate"]:
                recommendations.append({
                    "type": "caching",
                    "component": service,
                    "issue": "Low cache hit rate",
                    "current_value": f"{claude_metrics.cache_hit_rate:.2%}",
                    "threshold": f"{self.thresholds['cache_hit_rate']:.2%}",
                    "recommendation": "Review cache strategy and increase TTL for stable data",
                    "priority": "low"
                })

        return recommendations

    async def export_analytics_report(
        self,
        start_date: datetime,
        end_date: datetime,
        format_type: str = "json"
    ) -> Dict[str, Any]:
        """Export comprehensive analytics report."""
        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "duration_days": (end_date - start_date).days
            },
            "dashboard_health": asdict(await self.get_dashboard_health()),
            "component_performance": {},
            "claude_services": {},
            "business_metrics": await self.get_business_intelligence(),
            "recommendations": await self.get_performance_recommendations(),
            "generated_at": datetime.now().isoformat()
        }

        # Add component performance
        components = ["journey_map", "sentiment_dashboard", "competitive_intel", "content_engine"]
        for component in components:
            perf = await self.get_component_performance(component)
            report["component_performance"][component] = asdict(perf)

        # Add Claude service metrics
        services = ["claude_agent_service", "semantic_analyzer", "action_planner"]
        for service in services:
            metrics = await self.get_claude_service_metrics(service)
            report["claude_services"][service] = asdict(metrics)

        return report

    # Private helper methods

    async def process_metrics_buffer(self) -> None:
        """Background task to process metrics buffer."""
        while True:
            try:
                # Process performance metrics
                while self.performance_buffer:
                    metric = self.performance_buffer.popleft()
                    await self._store_performance_metric(metric)

                # Process interaction events
                while self.interaction_buffer:
                    interaction = self.interaction_buffer.popleft()
                    await self._store_interaction_event(interaction)

                await asyncio.sleep(1)  # Process every second

            except Exception as e:
                logger.error(f"Error processing metrics buffer: {e}")
                await asyncio.sleep(5)

    async def calculate_periodic_metrics(self) -> None:
        """Background task to calculate periodic business metrics."""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes

                # Calculate and cache business metrics
                await self._calculate_agent_efficiency()
                await self._calculate_conversion_improvements()
                await self._calculate_decision_speed()

            except Exception as e:
                logger.error(f"Error calculating periodic metrics: {e}")

    async def _store_performance_metric(self, metric: PerformanceMetric) -> None:
        """Store performance metric in Redis."""
        if not self.redis_client:
            return

        key = f"perf:{metric.component}:{int(metric.timestamp.timestamp())}"
        data = {
            "operation": metric.operation,
            "duration_ms": metric.duration_ms,
            "timestamp": metric.timestamp.isoformat(),
            "user_id": metric.user_id,
            "session_id": metric.session_id,
            "success": metric.success,
            "error_details": metric.error_details,
            "metadata": metric.metadata
        }

        # Store with 7-day expiration
        await self.redis_client.setex(key, 604800, json.dumps(data))

    async def _store_interaction_event(self, interaction: UserInteractionEvent) -> None:
        """Store user interaction event in Redis."""
        if not self.redis_client:
            return

        key = f"interaction:{interaction.user_id}:{int(interaction.timestamp.timestamp())}"
        data = {
            "event_type": interaction.event_type,
            "component": interaction.component,
            "element_id": interaction.element_id,
            "timestamp": interaction.timestamp.isoformat(),
            "session_id": interaction.session_id,
            "page_load_time": interaction.page_load_time,
            "interaction_value": interaction.interaction_value,
            "metadata": interaction.metadata
        }

        # Store with 30-day expiration
        await self.redis_client.setex(key, 2592000, json.dumps(data))

    def _calculate_performance_score(
        self,
        avg_time: float,
        error_rate: float,
        component: str
    ) -> float:
        """Calculate performance score (0-100) for a component."""
        # Base score
        score = 100.0

        # Penalize slow performance
        threshold = self.thresholds.get(f"{component}_render_time", 500)
        if avg_time > threshold:
            score -= min(50, (avg_time - threshold) / threshold * 50)

        # Penalize errors
        if error_rate > 0:
            score -= min(30, error_rate * 100 * 3)

        return max(0, score)

    async def _calculate_claude_metrics(
        self,
        service_name: str,
        hours: int
    ) -> ClaudeServiceMetrics:
        """Calculate Claude service metrics."""
        # This would integrate with actual Claude service monitoring
        # For now, return realistic mock data

        return ClaudeServiceMetrics(
            service_name=service_name,
            avg_response_time=150.5,
            requests_per_minute=45,
            success_rate=0.98,
            error_rate=0.02,
            cache_hit_rate=0.85,
            token_usage=1250,
            cost_per_request=0.0023,
            accuracy_score=0.96 if "semantic" in service_name else None
        )

    async def _calculate_uptime(self) -> float:
        """Calculate system uptime percentage."""
        # Would integrate with actual uptime monitoring
        return 99.8

    async def _get_page_load_times(self) -> float:
        """Get average page load times."""
        if not self.redis_client:
            return 0.0

        # Get recent interaction events with page load times
        keys = await self.redis_client.keys("interaction:*")
        load_times = []

        for key in keys[-100:]:  # Sample recent events
            data = await self.redis_client.get(key)
            if data:
                interaction = json.loads(data)
                if interaction.get("page_load_time"):
                    load_times.append(interaction["page_load_time"])

        return sum(load_times) / len(load_times) if load_times else 0.0

    async def _count_active_users(self, hours: int) -> int:
        """Count active users in the last N hours."""
        if not self.redis_client:
            return 0

        # Count unique user IDs from interactions
        keys = await self.redis_client.keys("interaction:*")
        unique_users = set()
        cutoff_time = datetime.now() - timedelta(hours=hours)

        for key in keys:
            # Extract timestamp from key
            timestamp_str = key.split(":")[-1]
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str))
                if timestamp >= cutoff_time:
                    user_id = key.split(":")[1]
                    unique_users.add(user_id)
            except (ValueError, IndexError):
                continue

        return len(unique_users)

    async def _count_sessions_today(self) -> int:
        """Count unique sessions today."""
        if not self.redis_client:
            return 0

        # Count unique session IDs from today's interactions
        keys = await self.redis_client.keys("interaction:*")
        unique_sessions = set()
        today = datetime.now().date()

        for key in keys:
            data = await self.redis_client.get(key)
            if data:
                interaction = json.loads(data)
                interaction_date = datetime.fromisoformat(
                    interaction["timestamp"]
                ).date()

                if interaction_date == today:
                    unique_sessions.add(interaction["session_id"])

        return len(unique_sessions)

    async def _calculate_data_freshness(self) -> float:
        """Calculate data freshness score (0-100)."""
        # This would check how recent the cached data is
        return 95.0  # Mock implementation

    async def _calculate_error_rate(self) -> float:
        """Calculate errors per hour."""
        if not self.redis_client:
            return 0.0

        # Count errors from performance metrics in last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        keys = await self.redis_client.keys("perf:*")
        errors = 0
        total = 0

        for key in keys:
            # Extract timestamp from key
            timestamp_str = key.split(":")[-1]
            try:
                timestamp = datetime.fromtimestamp(int(timestamp_str))
                if timestamp >= one_hour_ago:
                    data = await self.redis_client.get(key)
                    if data:
                        metric = json.loads(data)
                        total += 1
                        if not metric.get("success", True):
                            errors += 1
            except (ValueError, IndexError):
                continue

        return errors if total > 0 else 0.0

    async def _count_websocket_connections(self) -> int:
        """Count active WebSocket connections."""
        # Would integrate with WebSocket server
        return 12  # Mock implementation

    async def _calculate_business_metric(
        self,
        metric_name: str,
        period: str
    ) -> Optional[BusinessIntelligenceMetric]:
        """Calculate a specific business metric."""
        # Mock business intelligence calculations
        metrics_map = {
            "agent_efficiency_improvement": BusinessIntelligenceMetric(
                metric_name="agent_efficiency_improvement",
                value=42.5,
                unit="percentage",
                period=period,
                timestamp=datetime.now(),
                comparison_period=35.2,
                trend_direction="up"
            ),
            "conversion_rate_increase": BusinessIntelligenceMetric(
                metric_name="conversion_rate_increase",
                value=28.3,
                unit="percentage",
                period=period,
                timestamp=datetime.now(),
                comparison_period=21.7,
                trend_direction="up"
            ),
            "decision_making_speed": BusinessIntelligenceMetric(
                metric_name="decision_making_speed",
                value=65.8,
                unit="percentage_faster",
                period=period,
                timestamp=datetime.now(),
                comparison_period=45.2,
                trend_direction="up"
            ),
            "user_engagement_score": BusinessIntelligenceMetric(
                metric_name="user_engagement_score",
                value=87.4,
                unit="score",
                period=period,
                timestamp=datetime.now(),
                comparison_period=82.1,
                trend_direction="up"
            ),
            "feature_adoption_rate": BusinessIntelligenceMetric(
                metric_name="feature_adoption_rate",
                value=73.2,
                unit="percentage",
                period=period,
                timestamp=datetime.now(),
                comparison_period=68.9,
                trend_direction="up"
            ),
            "time_to_insight": BusinessIntelligenceMetric(
                metric_name="time_to_insight",
                value=3.2,
                unit="minutes",
                period=period,
                timestamp=datetime.now(),
                comparison_period=5.7,
                trend_direction="down"  # Lower is better
            ),
            "dashboard_roi": BusinessIntelligenceMetric(
                metric_name="dashboard_roi",
                value=340.0,
                unit="percentage",
                period=period,
                timestamp=datetime.now(),
                comparison_period=280.0,
                trend_direction="up"
            )
        }

        return metrics_map.get(metric_name)

    async def _trigger_performance_alert(self, metric: PerformanceMetric) -> None:
        """Trigger alert for performance issues."""
        alert_data = {
            "type": "performance_alert",
            "component": metric.component,
            "operation": metric.operation,
            "duration_ms": metric.duration_ms,
            "timestamp": metric.timestamp.isoformat(),
            "threshold_exceeded": True
        }

        # In production, would send to alerting system
        logger.warning(f"Performance alert: {alert_data}")

    async def _update_user_analytics(self, interaction: UserInteractionEvent) -> None:
        """Update real-time user analytics."""
        if not self.redis_client:
            return

        # Update user session metrics
        session_key = f"session:{interaction.session_id}"
        session_data = await self.redis_client.get(session_key) or "{}"
        session = json.loads(session_data)

        session.setdefault("interactions", 0)
        session["interactions"] += 1
        session["last_activity"] = interaction.timestamp.isoformat()
        session.setdefault("components_used", set())
        session["components_used"].add(interaction.component)

        # Convert set to list for JSON serialization
        session["components_used"] = list(session["components_used"])

        await self.redis_client.setex(
            session_key, 3600, json.dumps(session)  # 1-hour session
        )

    async def _calculate_agent_efficiency(self) -> None:
        """Calculate agent efficiency improvements."""
        # Mock calculation - would integrate with actual usage data
        pass

    async def _calculate_conversion_improvements(self) -> None:
        """Calculate conversion rate improvements."""
        # Mock calculation - would integrate with GHL data
        pass

    async def _calculate_decision_speed(self) -> None:
        """Calculate decision-making speed improvements."""
        # Mock calculation - would track time-to-action metrics
        pass


# Global performance monitor instance
performance_monitor = IntelligencePerformanceMonitor()


# Utility decorators for automatic performance tracking
def track_performance(component: str, operation: str = None):
    """Decorator to automatically track function performance."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            start_time = time.time()
            success = True
            error_details = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_details = str(e)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                await performance_monitor.record_performance(
                    component=component,
                    operation=op_name,
                    duration_ms=duration,
                    success=success,
                    error_details=error_details
                )

        def sync_wrapper(*args, **kwargs):
            op_name = operation or func.__name__
            start_time = time.time()
            success = True
            error_details = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_details = str(e)
                raise
            finally:
                duration = (time.time() - start_time) * 1000
                # Store for async processing
                metric = PerformanceMetric(
                    component=component,
                    operation=op_name,
                    duration_ms=duration,
                    timestamp=datetime.now(),
                    metadata={},
                    success=success,
                    error_details=error_details
                )
                performance_monitor.performance_buffer.append(metric)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator


def track_interaction(component: str):
    """Decorator to automatically track user interactions."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract user/session info from Streamlit session state
            try:
                import streamlit as st
                user_id = getattr(st.session_state, 'user_id', 'anonymous')
                session_id = getattr(st.session_state, 'session_id', 'unknown')

                # Store for async processing
                interaction = UserInteractionEvent(
                    event_type=func.__name__,
                    component=component,
                    element_id=kwargs.get('element_id'),
                    timestamp=datetime.now(),
                    user_id=user_id,
                    session_id=session_id,
                    interaction_value=kwargs.get('value'),
                    metadata={'args': str(args), 'kwargs': str(kwargs)}
                )
                performance_monitor.interaction_buffer.append(interaction)

            except Exception as e:
                logger.debug(f"Could not track interaction: {e}")

            return func(*args, **kwargs)

        return wrapper

    return decorator


# Export main classes and functions
__all__ = [
    "IntelligencePerformanceMonitor",
    "PerformanceMetric",
    "ComponentPerformance",
    "UserInteractionEvent",
    "BusinessIntelligenceMetric",
    "ClaudeServiceMetrics",
    "DashboardHealthMetrics",
    "performance_monitor",
    "track_performance",
    "track_interaction"
]