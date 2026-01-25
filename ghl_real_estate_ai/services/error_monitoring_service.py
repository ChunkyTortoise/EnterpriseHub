"""
Error Monitoring and Analytics Service for Jorge's Real Estate AI Platform.

Provides comprehensive error tracking, analytics, and monitoring capabilities
including real-time error dashboards, correlation tracking, and alerting.

Features:
- Structured error collection and analysis
- Real-time error rate monitoring
- Error pattern recognition
- Correlation tracking across services
- Performance impact analysis
- Automated alerting and notifications
- Error resolution tracking
"""

import asyncio
import time
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta, timezone
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class ErrorCategory(Enum):
    """Error categories for Jorge's platform."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    BUSINESS_LOGIC = "business_logic"
    EXTERNAL_API = "external_api"
    DATABASE = "database"
    NETWORK = "network"
    SYSTEM = "system"
    WEBSOCKET = "websocket"
    PERFORMANCE = "performance"


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class ErrorEvent:
    """Structured error event for tracking."""

    error_id: str
    correlation_id: str
    timestamp: float
    endpoint: str
    error_type: str
    category: ErrorCategory
    message: str
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    stack_trace: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    resolution_time: Optional[float] = None
    resolved: bool = False


@dataclass
class ErrorPattern:
    """Identified error pattern."""

    pattern_id: str
    category: ErrorCategory
    error_signature: str
    occurrences: int
    first_seen: float
    last_seen: float
    affected_users: int
    affected_endpoints: List[str]
    resolution_suggestions: List[str] = field(default_factory=list)


@dataclass
class ErrorMetrics:
    """Error metrics for monitoring."""

    timestamp: float
    total_errors: int
    error_rate: float  # errors per minute
    unique_errors: int
    avg_resolution_time: float
    critical_errors: int
    category_breakdown: Dict[str, int] = field(default_factory=dict)
    endpoint_breakdown: Dict[str, int] = field(default_factory=dict)


class ErrorMonitoringService:
    """Comprehensive error monitoring and analytics service."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service or CacheService()
        self.event_publisher = get_event_publisher()

        # In-memory storage for real-time monitoring
        self.recent_errors: deque = deque(maxlen=1000)  # Last 1000 errors
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.metrics_history: deque = deque(maxlen=288)  # 24 hours of 5-min intervals

        # Configuration
        self.alert_thresholds = {
            "error_rate_warning": 10.0,    # errors per minute
            "error_rate_critical": 50.0,   # errors per minute
            "unique_errors_warning": 5,    # unique errors in 5 minutes
            "critical_errors_threshold": 1  # any critical error triggers alert
        }

        # Monitoring intervals
        self.metrics_interval = 300  # 5 minutes
        self.pattern_analysis_interval = 600  # 10 minutes

        # Start background monitoring
        asyncio.create_task(self._start_monitoring())

    async def record_error(
        self,
        error_id: str,
        correlation_id: str,
        endpoint: str,
        error_type: str,
        category: ErrorCategory,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
        stack_trace: Optional[str] = None
    ):
        """Record a new error event."""

        error_event = ErrorEvent(
            error_id=error_id,
            correlation_id=correlation_id,
            timestamp=time.time(),
            endpoint=endpoint,
            error_type=error_type,
            category=category,
            message=message,
            context=context or {},
            user_id=user_id,
            session_id=session_id,
            user_agent=user_agent,
            ip_address=ip_address,
            stack_trace=stack_trace
        )

        # Store in recent errors for real-time monitoring
        self.recent_errors.append(error_event)

        # Cache for persistence
        await self._cache_error_event(error_event)

        # Update pattern analysis
        await self._analyze_error_pattern(error_event)

        # Check for immediate alerts
        await self._check_immediate_alerts(error_event)

        # Publish event for real-time dashboards
        await self._publish_error_event(error_event)

        logger.info(
            f"Error event recorded: {error_id}",
            extra={
                "error_id": error_id,
                "correlation_id": correlation_id,
                "category": category.value,
                "endpoint": endpoint,
                "jorge_monitoring": True
            }
        )

    async def get_error_metrics(
        self,
        timeframe_minutes: int = 60
    ) -> Dict[str, Any]:
        """Get error metrics for the specified timeframe."""

        cutoff_time = time.time() - (timeframe_minutes * 60)
        relevant_errors = [
            error for error in self.recent_errors
            if error.timestamp >= cutoff_time
        ]

        if not relevant_errors:
            return self._empty_metrics()

        total_errors = len(relevant_errors)
        error_rate = total_errors / timeframe_minutes
        unique_errors = len(set(error.error_type for error in relevant_errors))

        # Resolution times for resolved errors
        resolution_times = [
            error.resolution_time - error.timestamp
            for error in relevant_errors
            if error.resolved and error.resolution_time
        ]
        avg_resolution_time = statistics.mean(resolution_times) if resolution_times else 0

        # Category breakdown
        category_counts = defaultdict(int)
        for error in relevant_errors:
            category_counts[error.category.value] += 1

        # Endpoint breakdown
        endpoint_counts = defaultdict(int)
        for error in relevant_errors:
            endpoint_counts[error.endpoint] += 1

        # Critical errors
        critical_errors = sum(
            1 for error in relevant_errors
            if error.category in [ErrorCategory.SYSTEM, ErrorCategory.DATABASE]
        )

        return {
            "timeframe_minutes": timeframe_minutes,
            "total_errors": total_errors,
            "error_rate": round(error_rate, 2),
            "unique_errors": unique_errors,
            "avg_resolution_time": round(avg_resolution_time, 2),
            "critical_errors": critical_errors,
            "category_breakdown": dict(category_counts),
            "endpoint_breakdown": dict(sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)),
            "timestamp": time.time()
        }

    async def get_error_trends(
        self,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get error trends over time."""

        trends = []
        current_time = time.time()

        for i in range(hours):
            hour_start = current_time - ((i + 1) * 3600)
            hour_end = current_time - (i * 3600)

            hour_errors = [
                error for error in self.recent_errors
                if hour_start <= error.timestamp < hour_end
            ]

            trends.append({
                "hour": i,
                "timestamp": hour_end,
                "total_errors": len(hour_errors),
                "error_rate": len(hour_errors) / 60,  # per minute
                "categories": {
                    category.value: sum(1 for error in hour_errors if error.category == category)
                    for category in ErrorCategory
                }
            })

        return list(reversed(trends))

    async def get_error_patterns(
        self,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Get identified error patterns."""

        patterns = sorted(
            self.error_patterns.values(),
            key=lambda p: p.occurrences,
            reverse=True
        )[:limit]

        return [
            {
                "pattern_id": pattern.pattern_id,
                "category": pattern.category.value,
                "error_signature": pattern.error_signature,
                "occurrences": pattern.occurrences,
                "first_seen": pattern.first_seen,
                "last_seen": pattern.last_seen,
                "affected_users": pattern.affected_users,
                "affected_endpoints": pattern.affected_endpoints,
                "resolution_suggestions": pattern.resolution_suggestions,
                "is_recent": (time.time() - pattern.last_seen) < 3600  # Last hour
            }
            for pattern in patterns
        ]

    async def get_top_errors(
        self,
        timeframe_minutes: int = 60,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get top errors by frequency."""

        cutoff_time = time.time() - (timeframe_minutes * 60)
        relevant_errors = [
            error for error in self.recent_errors
            if error.timestamp >= cutoff_time
        ]

        # Count by error type and endpoint
        error_counts = defaultdict(lambda: {
            "count": 0,
            "endpoints": set(),
            "users": set(),
            "latest_occurrence": 0,
            "category": None,
            "sample_message": ""
        })

        for error in relevant_errors:
            key = f"{error.error_type}:{error.endpoint}"
            error_counts[key]["count"] += 1
            error_counts[key]["endpoints"].add(error.endpoint)
            if error.user_id:
                error_counts[key]["users"].add(error.user_id)
            error_counts[key]["latest_occurrence"] = max(
                error_counts[key]["latest_occurrence"],
                error.timestamp
            )
            error_counts[key]["category"] = error.category.value
            if not error_counts[key]["sample_message"]:
                error_counts[key]["sample_message"] = error.message

        # Convert to list and sort
        top_errors = sorted(
            [
                {
                    "error_signature": key,
                    "count": data["count"],
                    "affected_endpoints": len(data["endpoints"]),
                    "affected_users": len(data["users"]),
                    "latest_occurrence": data["latest_occurrence"],
                    "category": data["category"],
                    "sample_message": data["sample_message"]
                }
                for key, data in error_counts.items()
            ],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

        return top_errors

    async def mark_error_resolved(
        self,
        error_id: str,
        resolution_time: Optional[float] = None
    ):
        """Mark an error as resolved."""

        resolution_time = resolution_time or time.time()

        # Find and update the error in recent errors
        for error in self.recent_errors:
            if error.error_id == error_id:
                error.resolved = True
                error.resolution_time = resolution_time
                break

        # Update in cache
        await self.cache_service.set(
            f"error_resolution:{error_id}",
            {"resolved": True, "resolution_time": resolution_time},
            ttl=86400  # 24 hours
        )

        logger.info(
            f"Error marked as resolved: {error_id}",
            extra={"error_id": error_id, "resolution_time": resolution_time}
        )

    async def get_error_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive data for error dashboard."""

        # Current metrics
        current_metrics = await self.get_error_metrics(timeframe_minutes=60)

        # Trends
        trends = await self.get_error_trends(hours=24)

        # Top errors
        top_errors = await self.get_top_errors(timeframe_minutes=60, limit=10)

        # Patterns
        patterns = await self.get_error_patterns(limit=10)

        # Health status
        health_status = await self._calculate_health_status()

        return {
            "overview": {
                "current_metrics": current_metrics,
                "health_status": health_status,
                "last_updated": time.time()
            },
            "trends": trends,
            "top_errors": top_errors,
            "patterns": patterns,
            "alerts": await self._get_active_alerts()
        }

    async def _cache_error_event(self, error_event: ErrorEvent):
        """Cache error event for persistence."""

        await self.cache_service.set(
            f"error_event:{error_event.error_id}",
            {
                "error_id": error_event.error_id,
                "correlation_id": error_event.correlation_id,
                "timestamp": error_event.timestamp,
                "endpoint": error_event.endpoint,
                "error_type": error_event.error_type,
                "category": error_event.category.value,
                "message": error_event.message,
                "context": error_event.context,
                "resolved": error_event.resolved
            },
            ttl=604800  # 7 days
        )

    async def _analyze_error_pattern(self, error_event: ErrorEvent):
        """Analyze error for pattern recognition."""

        # Create error signature
        signature = f"{error_event.error_type}:{error_event.endpoint}"

        if signature in self.error_patterns:
            pattern = self.error_patterns[signature]
            pattern.occurrences += 1
            pattern.last_seen = error_event.timestamp
            if error_event.endpoint not in pattern.affected_endpoints:
                pattern.affected_endpoints.append(error_event.endpoint)
        else:
            self.error_patterns[signature] = ErrorPattern(
                pattern_id=f"pattern_{len(self.error_patterns)}",
                category=error_event.category,
                error_signature=signature,
                occurrences=1,
                first_seen=error_event.timestamp,
                last_seen=error_event.timestamp,
                affected_users=1 if error_event.user_id else 0,
                affected_endpoints=[error_event.endpoint],
                resolution_suggestions=self._get_resolution_suggestions(error_event)
            )

    def _get_resolution_suggestions(self, error_event: ErrorEvent) -> List[str]:
        """Get resolution suggestions based on error type and category."""

        suggestions_map = {
            ErrorCategory.VALIDATION: [
                "Review input validation rules",
                "Check API request format",
                "Verify required fields are present"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Check token expiration",
                "Verify authentication service status",
                "Review authentication configuration"
            ],
            ErrorCategory.EXTERNAL_API: [
                "Check external service status",
                "Verify API credentials",
                "Implement retry mechanism",
                "Add circuit breaker"
            ],
            ErrorCategory.DATABASE: [
                "Check database connection pool",
                "Review query performance",
                "Verify database service health",
                "Check for deadlocks"
            ],
            ErrorCategory.WEBSOCKET: [
                "Check WebSocket connection stability",
                "Review message format validation",
                "Verify client connection state",
                "Implement reconnection logic"
            ]
        }

        return suggestions_map.get(error_event.category, ["Review error details", "Check logs"])

    async def _check_immediate_alerts(self, error_event: ErrorEvent):
        """Check if error event triggers immediate alerts."""

        # Critical error alert
        if error_event.category in [ErrorCategory.SYSTEM, ErrorCategory.DATABASE]:
            await self._send_alert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Error Detected",
                message=f"Critical error in {error_event.endpoint}: {error_event.message}",
                context={"error_id": error_event.error_id, "correlation_id": error_event.correlation_id}
            )

        # High error rate check
        recent_errors_count = len([
            error for error in self.recent_errors
            if error.timestamp > (time.time() - 300)  # Last 5 minutes
        ])

        if recent_errors_count > self.alert_thresholds["error_rate_critical"] * 5:
            await self._send_alert(
                severity=AlertSeverity.CRITICAL,
                title="High Error Rate Detected",
                message=f"Error rate exceeded critical threshold: {recent_errors_count} errors in 5 minutes",
                context={"error_count": recent_errors_count, "timeframe": "5_minutes"}
            )

    async def _send_alert(
        self,
        severity: AlertSeverity,
        title: str,
        message: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Send alert notification."""

        alert_data = {
            "alert_id": f"alert_{int(time.time() * 1000)}",
            "severity": severity.value,
            "title": title,
            "message": message,
            "context": context or {},
            "timestamp": time.time(),
            "jorge_platform": True
        }

        # Publish alert event
        await self.event_publisher.publish_error_alert(
            alert_id=alert_data["alert_id"],
            severity=severity.value,
            title=title,
            message=message,
            context=context or {}
        )

        logger.warning(
            f"Error Alert [{severity.value.upper()}]: {title}",
            extra=alert_data
        )

    async def _publish_error_event(self, error_event: ErrorEvent):
        """Publish error event for real-time dashboards."""

        try:
            await self.event_publisher.publish_error_event(
                error_id=error_event.error_id,
                correlation_id=error_event.correlation_id,
                error_type=error_event.error_type,
                category=error_event.category.value,
                endpoint=error_event.endpoint,
                message=error_event.message
            )
        except Exception as e:
            logger.warning(f"Failed to publish error event: {e}")

    async def _start_monitoring(self):
        """Start background monitoring tasks."""

        asyncio.create_task(self._metrics_collector())
        asyncio.create_task(self._pattern_analyzer())

    async def _metrics_collector(self):
        """Collect metrics periodically."""

        while True:
            try:
                await asyncio.sleep(self.metrics_interval)

                metrics = await self.get_error_metrics(timeframe_minutes=5)

                # Store metrics
                self.metrics_history.append(ErrorMetrics(
                    timestamp=time.time(),
                    total_errors=metrics["total_errors"],
                    error_rate=metrics["error_rate"],
                    unique_errors=metrics["unique_errors"],
                    avg_resolution_time=metrics["avg_resolution_time"],
                    critical_errors=metrics["critical_errors"],
                    category_breakdown=metrics["category_breakdown"],
                    endpoint_breakdown=metrics["endpoint_breakdown"]
                ))

                # Check thresholds
                await self._check_metric_thresholds(metrics)

            except Exception as e:
                logger.error(f"Error in metrics collector: {e}")

    async def _pattern_analyzer(self):
        """Analyze error patterns periodically."""

        while True:
            try:
                await asyncio.sleep(self.pattern_analysis_interval)

                # Clean old patterns
                cutoff_time = time.time() - 86400  # 24 hours
                self.error_patterns = {
                    k: v for k, v in self.error_patterns.items()
                    if v.last_seen > cutoff_time
                }

                # Analyze new patterns
                high_frequency_patterns = [
                    pattern for pattern in self.error_patterns.values()
                    if pattern.occurrences >= 10 and (time.time() - pattern.last_seen) < 3600
                ]

                if high_frequency_patterns:
                    await self._send_alert(
                        severity=AlertSeverity.WARNING,
                        title="High Frequency Error Patterns Detected",
                        message=f"{len(high_frequency_patterns)} error patterns with high frequency",
                        context={"patterns": [p.pattern_id for p in high_frequency_patterns]}
                    )

            except Exception as e:
                logger.error(f"Error in pattern analyzer: {e}")

    async def _check_metric_thresholds(self, metrics: Dict[str, Any]):
        """Check if metrics exceed thresholds."""

        error_rate = metrics["error_rate"]

        if error_rate >= self.alert_thresholds["error_rate_critical"]:
            await self._send_alert(
                severity=AlertSeverity.CRITICAL,
                title="Critical Error Rate",
                message=f"Error rate: {error_rate:.1f} errors/min",
                context={"metrics": metrics}
            )
        elif error_rate >= self.alert_thresholds["error_rate_warning"]:
            await self._send_alert(
                severity=AlertSeverity.WARNING,
                title="High Error Rate",
                message=f"Error rate: {error_rate:.1f} errors/min",
                context={"metrics": metrics}
            )

    async def _calculate_health_status(self) -> Dict[str, Any]:
        """Calculate overall system health status."""

        recent_metrics = await self.get_error_metrics(timeframe_minutes=15)

        if recent_metrics["critical_errors"] > 0:
            status = "critical"
            message = f"{recent_metrics['critical_errors']} critical errors"
        elif recent_metrics["error_rate"] > self.alert_thresholds["error_rate_warning"]:
            status = "warning"
            message = f"High error rate: {recent_metrics['error_rate']:.1f}/min"
        elif recent_metrics["total_errors"] > 0:
            status = "ok"
            message = "Some errors detected, monitoring"
        else:
            status = "healthy"
            message = "No errors detected"

        return {
            "status": status,
            "message": message,
            "metrics": recent_metrics
        }

    async def _get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get currently active alerts."""

        # This would typically fetch from a persistent store
        # For now, return empty list as alerts are sent immediately
        return []

    def _empty_metrics(self) -> Dict[str, Any]:
        """Return empty metrics structure."""

        return {
            "timeframe_minutes": 60,
            "total_errors": 0,
            "error_rate": 0.0,
            "unique_errors": 0,
            "avg_resolution_time": 0.0,
            "critical_errors": 0,
            "category_breakdown": {},
            "endpoint_breakdown": {},
            "timestamp": time.time()
        }


# Global instance
_error_monitoring_service = None


def get_error_monitoring_service() -> ErrorMonitoringService:
    """Get the global error monitoring service instance."""
    global _error_monitoring_service
    if _error_monitoring_service is None:
        _error_monitoring_service = ErrorMonitoringService()
    return _error_monitoring_service