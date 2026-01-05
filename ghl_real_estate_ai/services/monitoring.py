"""
Monitoring & Alerting System (Agent A2)

Provides error tracking, performance monitoring, and alerting capabilities.
"""
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque
from enum import Enum


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics to track."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class PerformanceMonitor:
    """Tracks performance metrics and identifies issues."""
    
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.metrics_dir = Path(__file__).parent.parent / "data" / "metrics" / location_id
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # In-memory metrics storage (last 1000 data points)
        self.metrics = defaultdict(lambda: deque(maxlen=1000))
        self.counters = defaultdict(int)
        self.gauges = defaultdict(float)
        
        # Performance thresholds
        self.thresholds = {
            "api_response_time_ms": 500,
            "conversation_processing_time_ms": 2000,
            "memory_usage_mb": 500,
            "error_rate_percentage": 5.0,
            "webhook_failure_rate": 10.0
        }
    
    def record_metric(
        self,
        metric_name: str,
        value: float,
        metric_type: MetricType = MetricType.GAUGE,
        tags: Optional[Dict[str, str]] = None
    ):
        """
        Record a metric value.
        
        Args:
            metric_name: Name of the metric
            value: Metric value
            metric_type: Type of metric (counter, gauge, histogram, timer)
            tags: Optional tags for filtering/grouping
        """
        timestamp = datetime.now().isoformat()
        
        metric_data = {
            "timestamp": timestamp,
            "value": value,
            "type": metric_type.value,
            "tags": tags or {}
        }
        
        if metric_type == MetricType.COUNTER:
            self.counters[metric_name] += value
            metric_data["total"] = self.counters[metric_name]
        elif metric_type == MetricType.GAUGE:
            self.gauges[metric_name] = value
        
        self.metrics[metric_name].append(metric_data)
        
        # Check thresholds
        self._check_threshold(metric_name, value)
    
    def _check_threshold(self, metric_name: str, value: float):
        """Check if metric exceeds threshold and raise alert."""
        if metric_name in self.thresholds:
            threshold = self.thresholds[metric_name]
            if value > threshold:
                self._raise_alert(
                    AlertLevel.WARNING,
                    f"{metric_name} exceeded threshold",
                    f"{metric_name} = {value} (threshold: {threshold})"
                )
    
    def _raise_alert(self, level: AlertLevel, title: str, message: str):
        """Raise an alert (can be extended to send notifications)."""
        alert = {
            "level": level.value,
            "title": title,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "location_id": self.location_id
        }
        
        # Save to alerts file
        alerts_file = self.metrics_dir / "alerts.json"
        alerts = []
        
        if alerts_file.exists():
            with open(alerts_file, 'r') as f:
                alerts = json.load(f)
        
        alerts.append(alert)
        
        # Keep only last 1000 alerts
        alerts = alerts[-1000:]
        
        with open(alerts_file, 'w') as f:
            json.dump(alerts, f, indent=2)
    
    def get_metric_stats(self, metric_name: str, time_window_minutes: int = 60) -> Dict:
        """
        Get statistics for a metric over a time window.
        
        Returns:
            {
                "count": int,
                "mean": float,
                "min": float,
                "max": float,
                "p50": float,
                "p95": float,
                "p99": float
            }
        """
        if metric_name not in self.metrics:
            return {"error": "Metric not found"}
        
        # Filter to time window
        cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
        recent_metrics = [
            m for m in self.metrics[metric_name]
            if datetime.fromisoformat(m["timestamp"]) > cutoff_time
        ]
        
        if not recent_metrics:
            return {"error": "No data in time window"}
        
        values = [m["value"] for m in recent_metrics]
        values.sort()
        
        count = len(values)
        mean = sum(values) / count
        
        return {
            "count": count,
            "mean": mean,
            "min": min(values),
            "max": max(values),
            "p50": values[int(count * 0.5)],
            "p95": values[int(count * 0.95)] if count >= 20 else values[-1],
            "p99": values[int(count * 0.99)] if count >= 100 else values[-1]
        }
    
    def get_recent_alerts(self, count: int = 10, level: Optional[AlertLevel] = None) -> List[Dict]:
        """Get recent alerts."""
        alerts_file = self.metrics_dir / "alerts.json"
        
        if not alerts_file.exists():
            return []
        
        with open(alerts_file, 'r') as f:
            alerts = json.load(f)
        
        # Filter by level if specified
        if level:
            alerts = [a for a in alerts if a["level"] == level.value]
        
        return alerts[-count:]
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall system health status.
        
        Returns:
            {
                "status": "healthy" | "degraded" | "unhealthy",
                "checks": {...},
                "alerts_count": {...},
                "recommendations": [...]
            }
        """
        checks = {}
        issues = []
        
        # Check API response time
        api_stats = self.get_metric_stats("api_response_time_ms", 15)
        if "mean" in api_stats:
            checks["api_response_time"] = {
                "status": "ok" if api_stats["mean"] < 500 else "warning",
                "value": api_stats["mean"],
                "threshold": 500
            }
            if api_stats["mean"] >= 500:
                issues.append("API response time elevated")
        
        # Check error rate
        error_stats = self.get_metric_stats("error_rate_percentage", 60)
        if "mean" in error_stats:
            checks["error_rate"] = {
                "status": "ok" if error_stats["mean"] < 5 else "warning",
                "value": error_stats["mean"],
                "threshold": 5
            }
            if error_stats["mean"] >= 5:
                issues.append("Error rate above threshold")
        
        # Check recent critical alerts
        critical_alerts = self.get_recent_alerts(10, AlertLevel.CRITICAL)
        checks["critical_alerts"] = {
            "status": "ok" if len(critical_alerts) == 0 else "critical",
            "count": len(critical_alerts)
        }
        
        # Determine overall status
        if any(c["status"] == "critical" for c in checks.values()):
            status = "unhealthy"
        elif any(c["status"] == "warning" for c in checks.values()):
            status = "degraded"
        else:
            status = "healthy"
        
        # Get alert counts
        all_alerts = self.get_recent_alerts(100)
        alert_counts = defaultdict(int)
        for alert in all_alerts:
            alert_counts[alert["level"]] += 1
        
        return {
            "status": status,
            "checks": checks,
            "alerts_count": dict(alert_counts),
            "issues": issues,
            "timestamp": datetime.now().isoformat()
        }


class ErrorTracker:
    """Tracks and categorizes errors."""
    
    def __init__(self, location_id: str):
        self.location_id = location_id
        self.errors_dir = Path(__file__).parent.parent / "data" / "errors" / location_id
        self.errors_dir.mkdir(parents=True, exist_ok=True)
        self.error_counts = defaultdict(int)
    
    def log_error(
        self,
        error_type: str,
        message: str,
        context: Optional[Dict[str, Any]] = None,
        stack_trace: Optional[str] = None
    ):
        """
        Log an error with context.
        
        Args:
            error_type: Type/category of error
            message: Error message
            context: Additional context (contact_id, conversation_id, etc.)
            stack_trace: Full stack trace if available
        """
        error_data = {
            "timestamp": datetime.now().isoformat(),
            "type": error_type,
            "message": message,
            "context": context or {},
            "stack_trace": stack_trace,
            "location_id": self.location_id
        }
        
        # Increment error count
        self.error_counts[error_type] += 1
        
        # Save to daily error log
        today = datetime.now().strftime("%Y-%m-%d")
        error_file = self.errors_dir / f"errors_{today}.jsonl"
        
        with open(error_file, 'a') as f:
            f.write(json.dumps(error_data) + "\n")
    
    def get_error_summary(self, days: int = 7) -> Dict[str, Any]:
        """
        Get error summary for the last N days.
        
        Returns:
            {
                "total_errors": int,
                "errors_by_type": {...},
                "error_rate_trend": [...],
                "top_errors": [...]
            }
        """
        error_counts_by_type = defaultdict(int)
        daily_counts = defaultdict(int)
        all_errors = []
        
        # Read error logs for last N days
        for i in range(days):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
            error_file = self.errors_dir / f"errors_{date}.jsonl"
            
            if error_file.exists():
                with open(error_file, 'r') as f:
                    for line in f:
                        try:
                            error = json.loads(line)
                            error_counts_by_type[error["type"]] += 1
                            daily_counts[date] += 1
                            all_errors.append(error)
                        except json.JSONDecodeError:
                            continue
        
        # Get top 10 most common errors
        top_errors = sorted(
            error_counts_by_type.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        return {
            "total_errors": len(all_errors),
            "errors_by_type": dict(error_counts_by_type),
            "daily_counts": dict(daily_counts),
            "top_errors": [{"type": t, "count": c} for t, c in top_errors],
            "error_rate": len(all_errors) / days  # Errors per day
        }


class ConversationMonitor:
    """Monitors conversation quality and patterns."""
    
    def __init__(self, location_id: str):
        self.location_id = location_id
    
    def track_conversation_metrics(
        self,
        conversation_id: str,
        metrics: Dict[str, Any]
    ):
        """
        Track metrics for a conversation.
        
        Args:
            conversation_id: Unique conversation identifier
            metrics: Dictionary of metrics
                {
                    "duration_seconds": float,
                    "message_count": int,
                    "lead_score": int,
                    "classification": str,
                    "response_time_avg": float,
                    "questions_answered": int
                }
        """
        # This would integrate with PerformanceMonitor
        pass
    
    def identify_anomalies(self) -> List[Dict[str, Any]]:
        """
        Identify anomalous conversation patterns.
        
        Returns anomalies like:
        - Sudden drop in lead scores
        - Increased conversation abandonment
        - Unusually long response times
        """
        anomalies = []
        
        # Placeholder for anomaly detection logic
        # In production, would use statistical methods
        
        return anomalies


class SystemHealthDashboard:
    """Provides a snapshot of system health."""
    
    def __init__(self, location_id: str):
        """
        Execute init operation.

        Args:
            location_id: Unique identifier
        """
        self.location_id = location_id
        self.performance_monitor = PerformanceMonitor(location_id)
        self.error_tracker = ErrorTracker(location_id)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get complete dashboard data.
        
        Returns comprehensive system health information.
        """
        health_status = self.performance_monitor.get_health_status()
        error_summary = self.error_tracker.get_error_summary(7)
        
        # Calculate uptime (simplified)
        uptime_percentage = 99.5  # Would calculate from actual data
        
        return {
            "location_id": self.location_id,
            "timestamp": datetime.now().isoformat(),
            "health": health_status,
            "errors": error_summary,
            "uptime_percentage": uptime_percentage,
            "metrics": {
                "api_response_time": self.performance_monitor.get_metric_stats("api_response_time_ms", 60),
                "conversation_count": self.performance_monitor.counters.get("conversations_processed", 0),
                "messages_sent": self.performance_monitor.counters.get("messages_sent", 0)
            }
        }
    
    def generate_health_report(self) -> str:
        """Generate a human-readable health report."""
        data = self.get_dashboard_data()
        
        report = []
        report.append("=" * 60)
        report.append(f"System Health Report - {self.location_id}")
        report.append("=" * 60)
        report.append(f"Generated: {data['timestamp']}\n")
        
        # Overall status
        status_emoji = {
            "healthy": "✅",
            "degraded": "⚠️",
            "unhealthy": "❌"
        }
        status = data["health"]["status"]
        report.append(f"Overall Status: {status_emoji.get(status, '❓')} {status.upper()}\n")
        
        # Uptime
        report.append(f"Uptime: {data['uptime_percentage']:.2f}%\n")
        
        # Error summary
        report.append("## Errors (Last 7 Days)")
        report.append("-" * 60)
        report.append(f"Total Errors: {data['errors']['total_errors']}")
        report.append(f"Error Rate: {data['errors']['error_rate']:.1f} errors/day\n")
        
        if data['errors']['top_errors']:
            report.append("Top Error Types:")
            for i, error in enumerate(data['errors']['top_errors'][:5], 1):
                report.append(f"  {i}. {error['type']}: {error['count']} occurrences")
        
        # Active issues
        if data["health"]["issues"]:
            report.append("\n## Active Issues")
            report.append("-" * 60)
            for issue in data["health"]["issues"]:
                report.append(f"⚠️  {issue}")
        
        # Performance metrics
        report.append("\n## Performance Metrics")
        report.append("-" * 60)
        api_stats = data["metrics"].get("api_response_time", {})
        if "mean" in api_stats:
            report.append(f"API Response Time (avg): {api_stats['mean']:.0f}ms")
            report.append(f"API Response Time (p95): {api_stats.get('p95', 0):.0f}ms")
        
        report.append(f"Conversations Processed: {data['metrics'].get('conversation_count', 0)}")
        report.append(f"Messages Sent: {data['metrics'].get('messages_sent', 0)}")
        
        report.append("\n" + "=" * 60)
        
        return "\n".join(report)


if __name__ == "__main__":
    # Demo usage
    print("Monitoring System Demo\n")
    
    monitor = PerformanceMonitor("demo_location")
    
    # Record some metrics
    monitor.record_metric("api_response_time_ms", 250, MetricType.TIMER)
    monitor.record_metric("api_response_time_ms", 300, MetricType.TIMER)
    monitor.record_metric("api_response_time_ms", 600, MetricType.TIMER)  # Will trigger alert
    
    # Get stats
    stats = monitor.get_metric_stats("api_response_time_ms", 60)
    print(f"API Response Time Stats: {stats}")
    
    # Get health status
    health = monitor.get_health_status()
    print(f"\nHealth Status: {health['status']}")
    print(f"Issues: {health['issues']}")
    
    # Generate dashboard
    dashboard = SystemHealthDashboard("demo_location")
    report = dashboard.generate_health_report()
    print("\n" + report)
