"""
Enterprise Design System Performance Monitor
Real-time monitoring and analytics for enterprise UI components.

Tracks component usage, performance metrics, and user interactions
to provide insights for optimization and business impact measurement.

Created: January 10, 2026
Author: EnterpriseHub Design Team
"""

import time
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from collections import defaultdict
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ComponentMetrics:
    """Performance metrics for enterprise components."""
    component_name: str
    render_count: int
    avg_render_time: float
    total_render_time: float
    error_count: int
    success_rate: float
    last_rendered: datetime
    theme_mode: str  # unified, legacy, fallback


@dataclass
class UsageAnalytics:
    """Usage analytics for enterprise components."""
    component_name: str
    daily_usage: int
    weekly_usage: int
    monthly_usage: int
    unique_sessions: int
    bounce_rate: float
    engagement_score: float


@dataclass
class PerformanceAlert:
    """Performance alert for component issues."""
    component_name: str
    alert_type: str
    severity: str
    message: str
    timestamp: datetime
    threshold_value: float
    actual_value: float


class EnterpriseDesignSystemMonitor:
    """
    Comprehensive monitoring system for Enterprise Design System components.

    Provides real-time performance tracking, usage analytics, and automated
    alerting for enterprise UI components.
    """

    def __init__(self):
        """Initialize the performance monitor."""
        self.metrics: Dict[str, ComponentMetrics] = {}
        self.usage_analytics: Dict[str, UsageAnalytics] = defaultdict(lambda: UsageAnalytics(
            component_name="",
            daily_usage=0,
            weekly_usage=0,
            monthly_usage=0,
            unique_sessions=0,
            bounce_rate=0.0,
            engagement_score=0.0
        ))
        self.performance_alerts: List[PerformanceAlert] = []
        self.session_data: Dict[str, Dict] = {}

        # Performance thresholds
        self.thresholds = {
            "max_render_time": 100,  # milliseconds
            "min_success_rate": 99.0,  # percentage
            "max_error_rate": 1.0,    # percentage
            "max_bounce_rate": 30.0   # percentage
        }

        # Component registry
        self.component_registry = {
            "enterprise_metric": {"category": "core", "critical": True},
            "enterprise_kpi_grid": {"category": "core", "critical": True},
            "enterprise_card": {"category": "layout", "critical": False},
            "enterprise_badge": {"category": "display", "critical": False},
            "enterprise_progress_ring": {"category": "feedback", "critical": False},
            "enterprise_status_indicator": {"category": "status", "critical": True},
            "apply_plotly_theme": {"category": "visualization", "critical": False}
        }

    def track_component_render(
        self,
        component_name: str,
        render_time: float,
        success: bool = True,
        theme_mode: str = "unified"
    ) -> None:
        """
        Track component rendering performance.

        Args:
            component_name: Name of the enterprise component
            render_time: Rendering time in milliseconds
            success: Whether the render was successful
            theme_mode: Theme mode used (unified, legacy, fallback)
        """
        try:
            current_time = datetime.now()

            if component_name not in self.metrics:
                self.metrics[component_name] = ComponentMetrics(
                    component_name=component_name,
                    render_count=0,
                    avg_render_time=0.0,
                    total_render_time=0.0,
                    error_count=0,
                    success_rate=100.0,
                    last_rendered=current_time,
                    theme_mode=theme_mode
                )

            metric = self.metrics[component_name]
            metric.render_count += 1
            metric.total_render_time += render_time
            metric.avg_render_time = metric.total_render_time / metric.render_count
            metric.last_rendered = current_time
            metric.theme_mode = theme_mode

            if not success:
                metric.error_count += 1

            metric.success_rate = ((metric.render_count - metric.error_count) / metric.render_count) * 100

            # Check for performance alerts
            self._check_performance_thresholds(component_name, metric)

            logger.debug(f"Tracked {component_name}: {render_time}ms, success={success}")

        except Exception as e:
            logger.error(f"Error tracking component render: {e}")

    def track_component_usage(
        self,
        component_name: str,
        session_id: str,
        user_action: str = "view"
    ) -> None:
        """
        Track component usage analytics.

        Args:
            component_name: Name of the enterprise component
            session_id: Unique session identifier
            user_action: Type of user interaction (view, click, interact)
        """
        try:
            current_time = datetime.now()

            # Update usage analytics
            usage = self.usage_analytics[component_name]
            usage.component_name = component_name
            usage.daily_usage += 1

            # Track session data
            if session_id not in self.session_data:
                self.session_data[session_id] = {
                    "start_time": current_time,
                    "components_used": set(),
                    "total_interactions": 0
                }

            session = self.session_data[session_id]
            session["components_used"].add(component_name)
            session["total_interactions"] += 1

            # Update unique sessions for this component
            components_in_session = [
                comp for comp in session["components_used"]
                if comp == component_name
            ]
            if len(components_in_session) == 1:  # First time this component used in session
                usage.unique_sessions += 1

            logger.debug(f"Tracked usage for {component_name}: {user_action}")

        except Exception as e:
            logger.error(f"Error tracking component usage: {e}")

    def _check_performance_thresholds(
        self,
        component_name: str,
        metric: ComponentMetrics
    ) -> None:
        """Check if component metrics exceed performance thresholds."""
        try:
            current_time = datetime.now()

            # Check render time threshold
            if metric.avg_render_time > self.thresholds["max_render_time"]:
                alert = PerformanceAlert(
                    component_name=component_name,
                    alert_type="performance",
                    severity="warning" if metric.avg_render_time < self.thresholds["max_render_time"] * 1.5 else "critical",
                    message=f"Average render time exceeds threshold: {metric.avg_render_time:.1f}ms",
                    timestamp=current_time,
                    threshold_value=self.thresholds["max_render_time"],
                    actual_value=metric.avg_render_time
                )
                self.performance_alerts.append(alert)

            # Check success rate threshold
            if metric.success_rate < self.thresholds["min_success_rate"]:
                alert = PerformanceAlert(
                    component_name=component_name,
                    alert_type="reliability",
                    severity="critical",
                    message=f"Success rate below threshold: {metric.success_rate:.1f}%",
                    timestamp=current_time,
                    threshold_value=self.thresholds["min_success_rate"],
                    actual_value=metric.success_rate
                )
                self.performance_alerts.append(alert)

        except Exception as e:
            logger.error(f"Error checking performance thresholds: {e}")

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary for all components."""
        try:
            total_renders = sum(m.render_count for m in self.metrics.values())
            total_errors = sum(m.error_count for m in self.metrics.values())
            avg_success_rate = sum(m.success_rate for m in self.metrics.values()) / len(self.metrics) if self.metrics else 100.0

            # Calculate theme adoption
            theme_usage = defaultdict(int)
            for metric in self.metrics.values():
                theme_usage[metric.theme_mode] += metric.render_count

            theme_adoption = {
                mode: (count / total_renders * 100) if total_renders > 0 else 0
                for mode, count in theme_usage.items()
            }

            # Get most used components
            most_used = sorted(
                self.metrics.values(),
                key=lambda m: m.render_count,
                reverse=True
            )[:5]

            # Get recent alerts
            recent_alerts = [
                alert for alert in self.performance_alerts
                if alert.timestamp > datetime.now() - timedelta(hours=24)
            ]

            return {
                "overview": {
                    "total_renders": total_renders,
                    "total_errors": total_errors,
                    "overall_success_rate": avg_success_rate,
                    "components_monitored": len(self.metrics),
                    "unified_theme_adoption": theme_adoption.get("unified", 0)
                },
                "most_used_components": [
                    {
                        "name": m.component_name,
                        "renders": m.render_count,
                        "avg_render_time": round(m.avg_render_time, 2),
                        "success_rate": round(m.success_rate, 2)
                    }
                    for m in most_used
                ],
                "theme_adoption": theme_adoption,
                "recent_alerts": [
                    {
                        "component": alert.component_name,
                        "type": alert.alert_type,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat()
                    }
                    for alert in recent_alerts[-10:]  # Last 10 alerts
                ],
                "performance_score": self._calculate_performance_score()
            }

        except Exception as e:
            logger.error(f"Error generating performance summary: {e}")
            return {"error": str(e)}

    def _calculate_performance_score(self) -> float:
        """Calculate overall performance score (0-100)."""
        try:
            if not self.metrics:
                return 100.0

            # Weighted scoring
            weights = {
                "success_rate": 0.4,
                "render_performance": 0.3,
                "theme_adoption": 0.2,
                "error_frequency": 0.1
            }

            # Success rate score (average of all components)
            avg_success_rate = sum(m.success_rate for m in self.metrics.values()) / len(self.metrics)
            success_score = min(avg_success_rate, 100.0)

            # Render performance score (inverse of average render time)
            avg_render_time = sum(m.avg_render_time for m in self.metrics.values()) / len(self.metrics)
            render_score = max(0, 100 - (avg_render_time / self.thresholds["max_render_time"]) * 50)

            # Theme adoption score (percentage using unified theme)
            total_renders = sum(m.render_count for m in self.metrics.values())
            unified_renders = sum(
                m.render_count for m in self.metrics.values()
                if m.theme_mode == "unified"
            )
            theme_score = (unified_renders / total_renders * 100) if total_renders > 0 else 100

            # Error frequency score
            total_errors = sum(m.error_count for m in self.metrics.values())
            error_score = max(0, 100 - (total_errors / total_renders * 1000)) if total_renders > 0 else 100

            # Calculate weighted score
            performance_score = (
                success_score * weights["success_rate"] +
                render_score * weights["render_performance"] +
                theme_score * weights["theme_adoption"] +
                error_score * weights["error_frequency"]
            )

            return round(performance_score, 1)

        except Exception as e:
            logger.error(f"Error calculating performance score: {e}")
            return 0.0

    def export_metrics(self, format_type: str = "json") -> str:
        """Export performance metrics in specified format."""
        try:
            summary = self.get_performance_summary()

            if format_type.lower() == "json":
                return json.dumps(summary, indent=2, default=str)
            elif format_type.lower() == "csv":
                # Convert to CSV format
                import io
                import csv

                output = io.StringIO()
                writer = csv.writer(output)

                # Write headers
                writer.writerow([
                    "Component", "Render Count", "Avg Render Time (ms)",
                    "Success Rate (%)", "Error Count", "Theme Mode", "Last Rendered"
                ])

                # Write data
                for metric in self.metrics.values():
                    writer.writerow([
                        metric.component_name,
                        metric.render_count,
                        round(metric.avg_render_time, 2),
                        round(metric.success_rate, 2),
                        metric.error_count,
                        metric.theme_mode,
                        metric.last_rendered.isoformat()
                    ])

                return output.getvalue()
            else:
                return json.dumps(summary, indent=2, default=str)

        except Exception as e:
            logger.error(f"Error exporting metrics: {e}")
            return f"Export error: {str(e)}"

    async def cleanup_old_data(self, days_to_keep: int = 30) -> None:
        """Clean up old monitoring data."""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_to_keep)

            # Clean up old alerts
            self.performance_alerts = [
                alert for alert in self.performance_alerts
                if alert.timestamp > cutoff_date
            ]

            # Clean up old session data
            old_sessions = [
                session_id for session_id, data in self.session_data.items()
                if data["start_time"] < cutoff_date
            ]

            for session_id in old_sessions:
                del self.session_data[session_id]

            logger.info(f"Cleaned up monitoring data older than {days_to_keep} days")

        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")


# Global performance monitor instance
performance_monitor = EnterpriseDesignSystemMonitor()


def track_render_performance(component_name: str):
    """Decorator to automatically track component render performance."""
    def decorator(func):
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            theme_mode = "unified"  # Default assumption

            try:
                # Check if unified theme is available (assume in kwargs or global context)
                theme_mode = kwargs.get('theme_mode', 'unified')
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(f"Component render failed: {e}")
                raise
            finally:
                render_time = (time.time() - start_time) * 1000  # Convert to milliseconds
                performance_monitor.track_component_render(
                    component_name=component_name,
                    render_time=render_time,
                    success=success,
                    theme_mode=theme_mode
                )
        return wrapper
    return decorator


def track_usage(component_name: str, session_id: str = "default"):
    """Track component usage for analytics."""
    performance_monitor.track_component_usage(
        component_name=component_name,
        session_id=session_id,
        user_action="view"
    )


# Export public interface
__all__ = [
    "EnterpriseDesignSystemMonitor",
    "ComponentMetrics",
    "UsageAnalytics",
    "PerformanceAlert",
    "performance_monitor",
    "track_render_performance",
    "track_usage"
]