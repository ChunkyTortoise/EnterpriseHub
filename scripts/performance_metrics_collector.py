#!/usr/bin/env python3
"""
Performance Metrics Collector for Phase 2

Collects, aggregates, and analyzes performance metrics across all components.
Provides real-time monitoring and long-term baseline tracking.

Features:
1. Real-time metric collection from services
2. Baseline metric storage and retrieval
3. Performance trend analysis
4. Alert generation for degradation
5. Cost tracking and analysis
6. Metric aggregation and reporting
"""

import asyncio
import json
import statistics
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict, field
from collections import defaultdict, deque
from pathlib import Path
import sys
import logging

sys.path.append(str(Path(__file__).parent.parent))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Metric Data Structures
# ============================================================================

@dataclass
class PerformanceMetricPoint:
    """Single metric data point"""
    timestamp: datetime
    value: float
    unit: str
    component: str
    metric_name: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MetricAggregate:
    """Aggregated metric statistics"""
    metric_name: str
    component: str
    count: int
    min_value: float
    max_value: float
    avg_value: float
    median_value: float
    p95_value: float
    p99_value: float
    std_dev: float
    unit: str
    collection_period_minutes: int


@dataclass
class PerformanceAlert:
    """Performance degradation alert"""
    alert_id: str
    timestamp: datetime
    metric_name: str
    component: str
    severity: str  # 'info', 'warning', 'critical'
    current_value: float
    threshold: float
    baseline_value: float
    unit: str
    message: str


@dataclass
class CostAnalysis:
    """Cost analysis and projections"""
    period_start: datetime
    period_end: datetime
    period_days: int

    compute_cost: float
    database_cost: float
    cache_cost: float
    api_cost: float
    ml_cost: float

    compute_reduction_percent: float
    database_reduction_percent: float
    cache_reduction_percent: float
    api_reduction_percent: float
    ml_reduction_percent: float

    projected_annual_savings: float


# ============================================================================
# Metrics Collector
# ============================================================================

class PerformanceMetricsCollector:
    """Collects and analyzes performance metrics"""

    def __init__(self, retention_days: int = 30):
        self.metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=10000))
        self.baselines: Dict[str, Dict[str, float]] = {}
        self.alerts: List[PerformanceAlert] = []
        self.retention_days = retention_days
        self.alert_thresholds: Dict[str, float] = {}

    def record_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        component: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a performance metric"""
        key = f"{component}:{metric_name}"
        point = PerformanceMetricPoint(
            timestamp=datetime.now(),
            value=value,
            unit=unit,
            component=component,
            metric_name=metric_name,
            metadata=metadata or {}
        )
        self.metrics[key].append(point)

        # Check for alerts
        self._check_alerts(metric_name, component, value)

    def set_baseline(
        self,
        metric_name: str,
        component: str,
        baseline_value: float,
        unit: str
    ) -> None:
        """Set baseline for a metric"""
        key = f"{component}:{metric_name}"
        if key not in self.baselines:
            self.baselines[key] = {}
        self.baselines[key]['value'] = baseline_value
        self.baselines[key]['unit'] = unit
        self.baselines[key]['timestamp'] = datetime.now()

    def set_alert_threshold(
        self,
        metric_name: str,
        component: str,
        threshold: float,
        severity: str = "warning"
    ) -> None:
        """Set alert threshold for a metric"""
        key = f"{component}:{metric_name}:{severity}"
        self.alert_thresholds[key] = threshold

    def get_metric_aggregate(
        self,
        metric_name: str,
        component: str,
        minutes: int = 60
    ) -> Optional[MetricAggregate]:
        """Get aggregated metrics for a time period"""
        key = f"{component}:{metric_name}"

        if key not in self.metrics or not self.metrics[key]:
            return None

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_points = [
            p for p in self.metrics[key]
            if p.timestamp >= cutoff_time
        ]

        if not recent_points:
            return None

        values = [p.value for p in recent_points]
        sorted_values = sorted(values)

        return MetricAggregate(
            metric_name=metric_name,
            component=component,
            count=len(values),
            min_value=min(values),
            max_value=max(values),
            avg_value=statistics.mean(values),
            median_value=sorted_values[len(sorted_values) // 2],
            p95_value=sorted_values[int(len(sorted_values) * 0.95)] if len(sorted_values) > 1 else sorted_values[0],
            p99_value=sorted_values[int(len(sorted_values) * 0.99)] if len(sorted_values) > 1 else sorted_values[0],
            std_dev=statistics.stdev(values) if len(values) > 1 else 0,
            unit=recent_points[0].unit,
            collection_period_minutes=minutes
        )

    def _check_alerts(
        self,
        metric_name: str,
        component: str,
        current_value: float
    ) -> None:
        """Check if metric exceeds alert thresholds"""
        for severity in ['critical', 'warning']:
            key = f"{component}:{metric_name}:{severity}"

            if key not in self.alert_thresholds:
                continue

            threshold = self.alert_thresholds[key]
            baseline_key = f"{component}:{metric_name}"

            if baseline_key in self.baselines:
                baseline = self.baselines[baseline_key]['value']
                unit = self.baselines[baseline_key]['unit']

                # Check if metric exceeds threshold
                if current_value > threshold:
                    alert = PerformanceAlert(
                        alert_id=f"{component}_{metric_name}_{datetime.now().timestamp()}",
                        timestamp=datetime.now(),
                        metric_name=metric_name,
                        component=component,
                        severity=severity,
                        current_value=current_value,
                        threshold=threshold,
                        baseline_value=baseline,
                        unit=unit,
                        message=f"{component} {metric_name} exceeded threshold: {current_value:.2f} > {threshold:.2f} {unit}"
                    )
                    self.alerts.append(alert)

    def get_recent_alerts(self, minutes: int = 60) -> List[PerformanceAlert]:
        """Get recent alerts"""
        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        return [a for a in self.alerts if a.timestamp >= cutoff_time]

    def get_trend_analysis(
        self,
        metric_name: str,
        component: str,
        minutes: int = 60
    ) -> Dict[str, Any]:
        """Analyze metric trend"""
        key = f"{component}:{metric_name}"

        if key not in self.metrics or len(self.metrics[key]) < 2:
            return {"trend": "insufficient_data"}

        cutoff_time = datetime.now() - timedelta(minutes=minutes)
        recent_points = [
            p for p in self.metrics[key]
            if p.timestamp >= cutoff_time
        ]

        if len(recent_points) < 2:
            return {"trend": "insufficient_data"}

        # Calculate trend using simple linear regression
        x = np.arange(len(recent_points))
        y = np.array([p.value for p in recent_points])

        # Fit line
        coefficients = np.polyfit(x, y, 1)
        slope = coefficients[0]

        # Determine trend
        if abs(slope) < np.std(y) * 0.01:
            trend = "stable"
        elif slope > 0:
            trend = "increasing"
        else:
            trend = "decreasing"

        return {
            "trend": trend,
            "slope": float(slope),
            "current_value": y[-1],
            "first_value": y[0],
            "change_percent": ((y[-1] - y[0]) / y[0] * 100) if y[0] != 0 else 0
        }

    def export_metrics_json(self, output_path: str) -> None:
        """Export all metrics to JSON"""
        data = {
            "timestamp": datetime.now().isoformat(),
            "metrics_summary": {},
            "recent_alerts": [asdict(a) for a in self.get_recent_alerts(minutes=1440)]
        }

        # Aggregate metrics
        for key in self.metrics.keys():
            component, metric_name = key.split(':')
            aggregate = self.get_metric_aggregate(metric_name, component, minutes=1440)

            if aggregate:
                data["metrics_summary"][key] = asdict(aggregate)

        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2, default=str)

        logger.info(f"Metrics exported to {output_path}")


# ============================================================================
# Cost Analysis
# ============================================================================

class CostAnalyzer:
    """Analyzes infrastructure costs and projections"""

    def __init__(self):
        self.daily_costs = []

    def record_daily_cost(
        self,
        date: datetime,
        compute_cost: float,
        database_cost: float,
        cache_cost: float,
        api_cost: float,
        ml_cost: float
    ) -> None:
        """Record daily cost"""
        self.daily_costs.append({
            "date": date,
            "compute": compute_cost,
            "database": database_cost,
            "cache": cache_cost,
            "api": api_cost,
            "ml": ml_cost,
            "total": compute_cost + database_cost + cache_cost + api_cost + ml_cost
        })

    def analyze_cost_reduction(
        self,
        baseline_period_days: int = 30,
        optimized_period_days: int = 30
    ) -> Optional[CostAnalysis]:
        """Analyze cost reduction between periods"""
        if len(self.daily_costs) < baseline_period_days + optimized_period_days:
            return None

        baseline_costs = self.daily_costs[:baseline_period_days]
        optimized_costs = self.daily_costs[-optimized_period_days:]

        # Calculate averages
        baseline_compute = statistics.mean([c["compute"] for c in baseline_costs])
        baseline_database = statistics.mean([c["database"] for c in baseline_costs])
        baseline_cache = statistics.mean([c["cache"] for c in baseline_costs])
        baseline_api = statistics.mean([c["api"] for c in baseline_costs])
        baseline_ml = statistics.mean([c["ml"] for c in baseline_costs])
        baseline_total = sum([c["total"] for c in baseline_costs])

        optimized_compute = statistics.mean([c["compute"] for c in optimized_costs])
        optimized_database = statistics.mean([c["database"] for c in optimized_costs])
        optimized_cache = statistics.mean([c["cache"] for c in optimized_costs])
        optimized_api = statistics.mean([c["api"] for c in optimized_costs])
        optimized_ml = statistics.mean([c["ml"] for c in optimized_costs])
        optimized_total = sum([c["total"] for c in optimized_costs])

        # Calculate reductions
        def calc_reduction(baseline: float, optimized: float) -> float:
            if baseline == 0:
                return 0
            return ((baseline - optimized) / baseline) * 100

        return CostAnalysis(
            period_start=baseline_costs[0]["date"],
            period_end=optimized_costs[-1]["date"],
            period_days=baseline_period_days + optimized_period_days,

            compute_cost=optimized_compute,
            database_cost=optimized_database,
            cache_cost=optimized_cache,
            api_cost=optimized_api,
            ml_cost=optimized_ml,

            compute_reduction_percent=calc_reduction(baseline_compute, optimized_compute),
            database_reduction_percent=calc_reduction(baseline_database, optimized_database),
            cache_reduction_percent=calc_reduction(baseline_cache, optimized_cache),
            api_reduction_percent=calc_reduction(baseline_api, optimized_api),
            ml_reduction_percent=calc_reduction(baseline_ml, optimized_ml),

            projected_annual_savings=(baseline_total - optimized_total) * 365
        )


# ============================================================================
# Real-Time Monitoring Dashboard
# ============================================================================

class PerformanceMonitoringDashboard:
    """Real-time performance monitoring dashboard"""

    def __init__(self, collector: PerformanceMetricsCollector):
        self.collector = collector

    def generate_health_report(self) -> str:
        """Generate system health report"""
        lines = []
        lines.append("\n" + "=" * 100)
        lines.append("REAL-TIME PERFORMANCE MONITORING DASHBOARD")
        lines.append("=" * 100)

        lines.append(f"\nReport Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # Recent alerts
        recent_alerts = self.collector.get_recent_alerts(minutes=60)
        lines.append(f"\nRecent Alerts (last 60 min): {len(recent_alerts)}")

        if recent_alerts:
            for alert in recent_alerts[-5:]:  # Show last 5
                severity_icon = {
                    "info": "ℹ️",
                    "warning": "⚠️",
                    "critical": "🔴"
                }.get(alert.severity, "•")
                lines.append(f"{severity_icon} {alert.component}/{alert.metric_name}: {alert.message}")

        lines.append("\n" + "=" * 100)
        return "\n".join(lines)


# ============================================================================
# Demo Usage
# ============================================================================

def demo_metrics_collection():
    """Demonstrate metrics collection"""
    print("Performance Metrics Collector - Demo")
    print("=" * 100)

    collector = PerformanceMetricsCollector()

    # Set baselines
    collector.set_baseline("api_response_time_p95", "api", 200.0, "ms")
    collector.set_baseline("db_query_p90", "database", 50.0, "ms")
    collector.set_baseline("cache_hit_rate", "cache", 95.0, "%")

    # Set alert thresholds
    collector.set_alert_threshold("api_response_time_p95", "api", 250.0, "warning")
    collector.set_alert_threshold("api_response_time_p95", "api", 350.0, "critical")

    # Simulate metric collection
    print("\nSimulating metric collection...")

    # API metrics
    for i in range(60):
        value = 150 + np.random.normal(0, 20)  # Around 150ms
        collector.record_metric("api_response_time_p95", value, "ms", "api")

    # Database metrics
    for i in range(60):
        value = 35 + np.random.normal(0, 5)  # Around 35ms
        collector.record_metric("db_query_p90", value, "ms", "database")

    # Cache hit rate
    for i in range(60):
        value = 92 + np.random.normal(0, 2)  # Around 92%
        collector.record_metric("cache_hit_rate", value, "%", "cache")

    # Get aggregates
    print("\nMetric Aggregates (last 60 data points):")
    print("-" * 100)

    for component, metric in [("api", "api_response_time_p95"), ("database", "db_query_p90"), ("cache", "cache_hit_rate")]:
        aggregate = collector.get_metric_aggregate(metric, component, minutes=1440)
        if aggregate:
            print(f"\n{component.upper()}/{metric}:")
            print(f"  Count: {aggregate.count}")
            print(f"  Min: {aggregate.min_value:.2f} {aggregate.unit}")
            print(f"  Avg: {aggregate.avg_value:.2f} {aggregate.unit}")
            print(f"  P95: {aggregate.p95_value:.2f} {aggregate.unit}")
            print(f"  Max: {aggregate.max_value:.2f} {aggregate.unit}")

    # Get trends
    print("\nMetric Trends:")
    print("-" * 100)

    for component, metric in [("api", "api_response_time_p95"), ("database", "db_query_p90"), ("cache", "cache_hit_rate")]:
        trend = collector.get_trend_analysis(metric, component, minutes=1440)
        print(f"\n{component.upper()}/{metric}: {trend['trend']}")

    # Export metrics
    output_path = Path(__file__).parent / "metrics_export.json"
    collector.export_metrics_json(str(output_path))

    print(f"\n✅ Metrics exported to {output_path}")


if __name__ == "__main__":
    demo_metrics_collection()
