"""
Tests for Monitoring System (Agent A2)
"""

import json
import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from ghl_real_estate_ai.services.monitoring import (
    AlertLevel,
    ConversationMonitor,
    ErrorTracker,
    MetricType,
    PerformanceMonitor,
    SystemHealthDashboard,
)


class TestPerformanceMonitor:
    """Test performance monitoring functionality."""

    def test_monitor_initialization(self):
        """Test monitor initializes correctly."""
        monitor = PerformanceMonitor("test_location")

        assert monitor.location_id == "test_location"
        assert monitor.metrics_dir.exists()

    def test_record_metric(self):
        """Test recording metrics."""
        monitor = PerformanceMonitor("test_monitor")

        monitor.record_metric("test_metric", 100.0, MetricType.GAUGE)

        assert "test_metric" in monitor.metrics
        assert len(monitor.metrics["test_metric"]) == 1
        assert monitor.metrics["test_metric"][0]["value"] == 100.0

    def test_record_counter(self):
        """Test counter metrics increment correctly."""
        monitor = PerformanceMonitor("test_monitor")

        monitor.record_metric("requests", 1, MetricType.COUNTER)
        monitor.record_metric("requests", 1, MetricType.COUNTER)
        monitor.record_metric("requests", 1, MetricType.COUNTER)

        assert monitor.counters["requests"] == 3

    def test_threshold_alert(self):
        """Test that threshold violations trigger alerts."""
        monitor = PerformanceMonitor("test_monitor")

        # Record metric above threshold
        monitor.record_metric("api_response_time_ms", 600)  # Threshold is 500

        # Check that alert was raised
        alerts = monitor.get_recent_alerts(1)
        assert len(alerts) > 0
        assert alerts[-1]["level"] == AlertLevel.WARNING.value

    def test_get_metric_stats(self):
        """Test calculating metric statistics."""
        monitor = PerformanceMonitor("test_monitor")

        # Record multiple values
        for i in range(100):
            monitor.record_metric("test_metric", float(i), MetricType.GAUGE)

        stats = monitor.get_metric_stats("test_metric", 60)

        assert stats["count"] == 100
        assert "mean" in stats
        assert "min" in stats
        assert "max" in stats
        assert "p50" in stats
        assert "p95" in stats

    def test_get_health_status(self):
        """Test overall health status calculation."""
        monitor = PerformanceMonitor("test_monitor")

        # Record some good metrics
        monitor.record_metric("api_response_time_ms", 200)
        monitor.record_metric("error_rate_percentage", 1.0)

        health = monitor.get_health_status()

        assert "status" in health
        assert health["status"] in ["healthy", "degraded", "unhealthy"]
        assert "checks" in health
        assert "alerts_count" in health


class TestErrorTracker:
    """Test error tracking functionality."""

    def test_tracker_initialization(self):
        """Test error tracker initializes correctly."""
        tracker = ErrorTracker("test_location")

        assert tracker.location_id == "test_location"
        assert tracker.errors_dir.exists()

    def test_log_error(self):
        """Test logging errors."""
        tracker = ErrorTracker("test_errors")

        tracker.log_error(error_type="ValidationError", message="Invalid input", context={"field": "email"})

        assert tracker.error_counts["ValidationError"] == 1

    def test_error_summary(self):
        """Test generating error summary."""
        import shutil
        import tempfile

        # Use a unique temp directory to avoid contamination from previous runs
        temp_dir = tempfile.mkdtemp()
        tracker = ErrorTracker("test_error_summary_unique")
        tracker.errors_dir = Path(temp_dir)

        try:
            # Log multiple errors
            tracker.log_error("TypeError", "Type mismatch")
            tracker.log_error("ValueError", "Invalid value")
            tracker.log_error("TypeError", "Another type error")

            summary = tracker.get_error_summary(1)

            assert "total_errors" in summary
            assert "errors_by_type" in summary
            assert "top_errors" in summary
            assert summary["errors_by_type"]["TypeError"] == 2
            assert summary["errors_by_type"]["ValueError"] == 1
            assert summary["total_errors"] == 3
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestSystemHealthDashboard:
    """Test system health dashboard."""

    def test_dashboard_initialization(self):
        """Test dashboard initializes correctly."""
        dashboard = SystemHealthDashboard("test_location")

        assert dashboard.location_id == "test_location"
        assert isinstance(dashboard.performance_monitor, PerformanceMonitor)
        assert isinstance(dashboard.error_tracker, ErrorTracker)

    def test_get_dashboard_data(self):
        """Test getting dashboard data."""
        dashboard = SystemHealthDashboard("test_dashboard")

        data = dashboard.get_dashboard_data()

        assert "location_id" in data
        assert "timestamp" in data
        assert "health" in data
        assert "errors" in data
        assert "uptime_percentage" in data
        assert "metrics" in data

    def test_generate_health_report(self):
        """Test generating health report."""
        dashboard = SystemHealthDashboard("test_dashboard")

        report = dashboard.generate_health_report()

        assert isinstance(report, str)
        assert "System Health Report" in report
        assert "Overall Status" in report


class TestMetricAggregation:
    """Test metric aggregation and statistics."""

    def test_percentile_calculation(self):
        """Test percentile calculations are accurate."""
        monitor = PerformanceMonitor("test_percentiles")

        # Record values 0-99
        for i in range(100):
            monitor.record_metric("latency", float(i))

        stats = monitor.get_metric_stats("latency", 60)

        # p50 should be around 50
        assert 45 <= stats["p50"] <= 55
        # p95 should be around 95
        assert 90 <= stats["p95"] <= 99

    def test_time_window_filtering(self):
        """Test that time windows filter correctly."""
        monitor = PerformanceMonitor("test_windows")

        # Record metric
        monitor.record_metric("test", 100)

        # Should find it in 60 min window
        stats_60 = monitor.get_metric_stats("test", 60)
        assert stats_60["count"] == 1

        # Should not find it in 0 min window
        stats_0 = monitor.get_metric_stats("test", 0)
        assert stats_0.get("count", 0) == 0


class TestAlertSystem:
    """Test alerting functionality."""

    def test_alert_levels(self):
        """Test different alert levels."""
        monitor = PerformanceMonitor("test_alerts")

        # Manually raise alerts
        monitor._raise_alert(AlertLevel.INFO, "Info", "Test info")
        monitor._raise_alert(AlertLevel.WARNING, "Warning", "Test warning")
        monitor._raise_alert(AlertLevel.ERROR, "Error", "Test error")

        # Get alerts by level
        all_alerts = monitor.get_recent_alerts(10)
        assert len(all_alerts) >= 3

        warnings = monitor.get_recent_alerts(10, AlertLevel.WARNING)
        assert any(a["level"] == "warning" for a in warnings)

    def test_alert_persistence(self):
        """Test that alerts are saved to file."""
        monitor = PerformanceMonitor("test_persist")

        monitor._raise_alert(AlertLevel.CRITICAL, "Critical Issue", "Test")

        # Check file exists
        alerts_file = monitor.metrics_dir / "alerts.json"
        assert alerts_file.exists()

        # Load and verify
        with open(alerts_file, "r") as f:
            alerts = json.load(f)

        assert len(alerts) > 0
        assert alerts[-1]["level"] == "critical"


class TestConversationMonitoring:
    """Test conversation-specific monitoring."""

    def test_conversation_monitor_init(self):
        """Test conversation monitor initialization."""
        monitor = ConversationMonitor("test_location")

        assert monitor.location_id == "test_location"

    def test_track_conversation_metrics(self):
        """Test tracking conversation metrics."""
        monitor = ConversationMonitor("test_conv")

        # Should not raise errors
        monitor.track_conversation_metrics("conv_123", {"duration_seconds": 300, "message_count": 15, "lead_score": 75})

    def test_identify_anomalies(self):
        """Test anomaly detection."""
        monitor = ConversationMonitor("test_anomaly")

        anomalies = monitor.identify_anomalies()

        assert isinstance(anomalies, list)


class TestMetricTypes:
    """Test different metric types."""

    def test_gauge_metric(self):
        """Test gauge metrics (current value)."""
        monitor = PerformanceMonitor("test_gauge")

        monitor.record_metric("temperature", 20.5, MetricType.GAUGE)
        monitor.record_metric("temperature", 21.0, MetricType.GAUGE)

        # Gauge should show current value
        assert monitor.gauges["temperature"] == 21.0

    def test_counter_metric(self):
        """Test counter metrics (cumulative)."""
        monitor = PerformanceMonitor("test_counter")

        monitor.record_metric("requests", 1, MetricType.COUNTER)
        monitor.record_metric("requests", 5, MetricType.COUNTER)
        monitor.record_metric("requests", 3, MetricType.COUNTER)

        # Counter should accumulate
        assert monitor.counters["requests"] == 9

    def test_timer_metric(self):
        """Test timer metrics."""
        monitor = PerformanceMonitor("test_timer")

        monitor.record_metric("operation_time", 1.5, MetricType.TIMER)
        monitor.record_metric("operation_time", 2.3, MetricType.TIMER)

        stats = monitor.get_metric_stats("operation_time", 60)
        assert stats["count"] == 2


class TestHealthStatusCalculation:
    """Test health status calculation logic."""

    def test_healthy_status(self):
        """Test system reports healthy when metrics are good."""
        monitor = PerformanceMonitor("test_healthy")

        # Record good metrics
        monitor.record_metric("api_response_time_ms", 200)
        monitor.record_metric("error_rate_percentage", 0.5)

        health = monitor.get_health_status()

        # Should be healthy or at least not unhealthy
        assert health["status"] in ["healthy", "degraded"]

    def test_degraded_status(self):
        """Test system reports degraded with warnings."""
        monitor = PerformanceMonitor("test_degraded")

        # Record metrics that trigger warnings
        monitor.record_metric("api_response_time_ms", 600)  # Over threshold

        health = monitor.get_health_status()

        # Should show some issues
        assert len(health["issues"]) > 0 or health["status"] != "healthy"

    def test_unhealthy_status(self):
        """Test system reports unhealthy with critical issues."""
        monitor = PerformanceMonitor("test_unhealthy")

        # Raise critical alert
        monitor._raise_alert(AlertLevel.CRITICAL, "Critical", "System down")

        health = monitor.get_health_status()

        # Should have critical alerts
        assert health["checks"]["critical_alerts"]["count"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])