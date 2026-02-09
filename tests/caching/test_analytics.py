"""
Tests for Cache Analytics Module
================================

Tests cover:
    - Metrics collection and aggregation
    - Hit/miss ratio calculations
    - Cost analysis
    - Performance report generation
    - Alert threshold monitoring
    - Export functionality
"""

import json
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.caching.analytics import (

@pytest.mark.integration
    CacheAnalytics,
    CacheMetrics,
    CostAnalysis,
    HitMissRatio,
    JSONMetricsExporter,
    MetricType,
    PerformanceReport,
    PrometheusMetricsExporter,
    TimeWindow,
)

pytestmark = pytest.mark.asyncio


class TestCacheMetrics:
    """Test cases for CacheMetrics dataclass."""

    def test_cache_metrics_creation(self):
        """Test creating cache metrics."""
        metrics = CacheMetrics(cache_name="test_cache", hits=100, misses=50, latencies_ms=[10.0, 20.0, 30.0])

        assert metrics.cache_name == "test_cache"
        assert metrics.hits == 100
        assert metrics.misses == 50

    def test_total_requests(self):
        """Test total requests calculation."""
        metrics = CacheMetrics(hits=100, misses=50)

        assert metrics.total_requests == 150

    def test_hit_rate(self):
        """Test hit rate calculation."""
        metrics = CacheMetrics(hits=80, misses=20)

        assert metrics.hit_rate == 0.8

    def test_hit_rate_zero_division(self):
        """Test hit rate with no requests."""
        metrics = CacheMetrics(hits=0, misses=0)

        assert metrics.hit_rate == 0.0

    def test_miss_rate(self):
        """Test miss rate calculation."""
        metrics = CacheMetrics(hits=80, misses=20)

        assert metrics.miss_rate == 0.2

    def test_latency_percentiles(self):
        """Test latency percentile calculations."""
        latencies = list(range(1, 101))  # 1-100 ms
        metrics = CacheMetrics(latencies_ms=latencies)

        assert metrics.avg_latency_ms == 50.5
        assert metrics.p50_latency_ms == 51  # 50th percentile of 1-100 = 51
        assert metrics.p95_latency_ms == 96  # 95th percentile of 1-100 = 96
        assert metrics.p99_latency_ms == 100  # 99th percentile = 100

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metrics = CacheMetrics(cache_name="test", hits=100, misses=50, latencies_ms=[10.0, 20.0])

        data = metrics.to_dict()

        assert data["cache_name"] == "test"
        assert data["hits"] == 100
        assert data["hit_rate"] == 100 / 150


class TestHitMissRatio:
    """Test cases for HitMissRatio dataclass."""

    def test_hit_miss_ratio_creation(self):
        """Test creating hit/miss ratio."""
        ratio = HitMissRatio(hits=100, misses=50, timeframe="1h")

        assert ratio.hits == 100
        assert ratio.misses == 50
        assert ratio.timeframe == "1h"

    def test_total(self):
        """Test total operations calculation."""
        ratio = HitMissRatio(hits=100, misses=50)

        assert ratio.total == 150

    def test_ratio(self):
        """Test ratio calculation."""
        ratio = HitMissRatio(hits=100, misses=50)

        assert ratio.ratio == 2.0  # 100/50

    def test_ratio_infinite(self):
        """Test ratio with zero misses."""
        ratio = HitMissRatio(hits=100, misses=0)

        assert ratio.ratio == float("inf")

    def test_hit_rate_percentage(self):
        """Test hit rate as percentage."""
        ratio = HitMissRatio(hits=80, misses=20)

        assert ratio.hit_rate == 80.0

    def test_str_representation(self):
        """Test string representation."""
        ratio = HitMissRatio(hits=80, misses=20)

        assert "80/20" in str(ratio)
        assert "80.0%" in str(ratio)


class TestCostAnalysis:
    """Test cases for CostAnalysis dataclass."""

    def test_cost_analysis_creation(self):
        """Test creating cost analysis."""
        analysis = CostAnalysis(hits=1000, misses=100, cost_per_hit=0.0001, cost_per_miss=0.01)

        assert analysis.hits == 1000
        assert analysis.misses == 100

    def test_total_hits_cost(self):
        """Test total hits cost calculation."""
        analysis = CostAnalysis(hits=1000, misses=0, cost_per_hit=0.0001)

        assert analysis.total_hits_cost == 0.1  # 1000 * 0.0001

    def test_total_misses_cost(self):
        """Test total misses cost calculation."""
        analysis = CostAnalysis(hits=0, misses=100, cost_per_miss=0.01)

        assert analysis.total_misses_cost == 1.0  # 100 * 0.01

    def test_total_cost(self):
        """Test total cost calculation."""
        analysis = CostAnalysis(hits=1000, misses=100)

        expected = (1000 * 0.0001) + (100 * 0.01)
        assert analysis.total_cost == expected

    def test_cost_without_cache(self):
        """Test cost without caching."""
        analysis = CostAnalysis(hits=1000, misses=100, cost_per_miss=0.01)

        assert analysis.cost_without_cache == 1100 * 0.01

    def test_cost_savings(self):
        """Test cost savings calculation."""
        analysis = CostAnalysis(hits=1000, misses=100)

        savings = analysis.cost_savings
        assert savings > 0  # Should have savings with caching

    def test_savings_percentage(self):
        """Test savings percentage calculation."""
        analysis = CostAnalysis(hits=900, misses=100)

        percentage = analysis.savings_percentage
        assert 0 <= percentage <= 100


class TestPerformanceReport:
    """Test cases for PerformanceReport dataclass."""

    def test_performance_report_creation(self):
        """Test creating performance report."""
        report = PerformanceReport(timeframe="1h", cache_names=["cache1", "cache2"], recommendations=["Increase TTL"])

        assert report.timeframe == "1h"
        assert report.cache_names == ["cache1", "cache2"]
        assert report.recommendations == ["Increase TTL"]

    def test_to_dict(self):
        """Test serialization to dictionary."""
        metrics = CacheMetrics(cache_name="test", hits=100, misses=50)
        report = PerformanceReport(timeframe="1h", cache_names=["test"], metrics={"test": metrics})

        data = report.to_dict()

        assert data["timeframe"] == "1h"
        assert "test" in data["metrics"]

    def test_to_json(self):
        """Test JSON export."""
        report = PerformanceReport(timeframe="1h", cache_names=["test"])

        json_str = report.to_json()

        # Should be valid JSON
        data = json.loads(json_str)
        assert data["timeframe"] == "1h"

    def test_to_csv(self):
        """Test CSV export."""
        metrics = CacheMetrics(cache_name="test", hits=100, misses=50, latencies_ms=[10, 20, 30])
        report = PerformanceReport(timeframe="1h", cache_names=["test"], metrics={"test": metrics})

        csv_str = report.to_csv()

        assert "cache_name" in csv_str
        assert "test" in csv_str
        assert "100" in csv_str

    def test_to_prometheus_metrics(self):
        """Test Prometheus metrics export."""
        metrics = CacheMetrics(cache_name="test", hits=100, misses=50)
        report = PerformanceReport(timeframe="1h", cache_names=["test"], metrics={"test": metrics})

        prom_str = report.to_prometheus_metrics()

        assert "# HELP" in prom_str
        assert "# TYPE" in prom_str
        assert "cache_test_hits" in prom_str
        assert "100" in prom_str


class TestCacheAnalytics:
    """Test cases for CacheAnalytics class."""

    @pytest.fixture
    async def analytics(self):
        """Create analytics instance for testing."""
        return CacheAnalytics(
            redis_client=None,  # In-memory only
            retention_minutes=60,
            enable_persistence=False,
        )

    async def test_record_hit(self, analytics):
        """Test recording a cache hit."""
        await analytics.record_hit("test_cache", response_time_ms=5.0)

        metrics = await analytics.get_metrics("test_cache")
        assert metrics.hits == 1
        assert 5.0 in metrics.latencies_ms

    async def test_record_miss(self, analytics):
        """Test recording a cache miss."""
        await analytics.record_miss("test_cache", computation_time_ms=150.0)

        metrics = await analytics.get_metrics("test_cache")
        assert metrics.misses == 1

    async def test_record_eviction(self, analytics):
        """Test recording a cache eviction."""
        await analytics.record_eviction("test_cache", size_bytes=1024)

        metrics = await analytics.get_metrics("test_cache")
        assert metrics.evictions == 1

    async def test_record_error(self, analytics):
        """Test recording a cache error."""
        error = ValueError("Test error")
        await analytics.record_error("test_cache", error)

        metrics = await analytics.get_metrics("test_cache")
        assert metrics.errors == 1

    async def test_record_latency(self, analytics):
        """Test recording operation latency."""
        await analytics.record_latency("test_cache", latency_ms=25.0)

        metrics = await analytics.get_metrics("test_cache")
        assert 25.0 in metrics.latencies_ms

    async def test_get_metrics_specific_cache(self, analytics):
        """Test getting metrics for specific cache."""
        await analytics.record_hit("cache1")
        await analytics.record_hit("cache2")

        metrics = await analytics.get_metrics("cache1")

        assert metrics.cache_name == "cache1"
        assert metrics.hits == 1

    async def test_get_metrics_all_caches(self, analytics):
        """Test getting metrics for all caches."""
        await analytics.record_hit("cache1")
        await analytics.record_hit("cache2")

        all_metrics = await analytics.get_metrics()

        assert "cache1" in all_metrics
        assert "cache2" in all_metrics

    async def test_get_hit_miss_ratio(self, analytics):
        """Test getting hit/miss ratio."""
        await analytics.record_hit("test_cache")
        await analytics.record_hit("test_cache")
        await analytics.record_miss("test_cache")

        ratio = await analytics.get_hit_miss_ratio("test_cache")

        assert ratio.hits == 2
        assert ratio.misses == 1
        assert ratio.hit_rate == pytest.approx(66.67, abs=0.01)

    async def test_get_cost_analysis(self, analytics):
        """Test getting cost analysis."""
        await analytics.record_hit("test_cache")
        await analytics.record_miss("test_cache")

        analysis = await analytics.get_cost_analysis("test_cache")

        assert analysis.hits == 1
        assert analysis.misses == 1
        assert analysis.total_cost > 0

    async def test_generate_report(self, analytics):
        """Test generating performance report."""
        await analytics.record_hit("cache1")
        await analytics.record_miss("cache2")

        report = await analytics.generate_report()

        assert report.timeframe == "1h"
        assert "cache1" in report.cache_names
        assert "cache2" in report.cache_names
        assert report.hit_miss_ratio is not None
        assert report.cost_analysis is not None

    async def test_generate_report_with_recommendations(self, analytics):
        """Test that report includes recommendations."""
        # Create low hit rate scenario
        for _ in range(10):
            await analytics.record_miss("low_hit_cache")
        await analytics.record_hit("low_hit_cache")

        report = await analytics.generate_report()

        assert len(report.recommendations) > 0

    async def test_alert_callback(self, analytics):
        """Test alert callback registration and triggering."""
        callback_mock = MagicMock()
        analytics.register_alert_callback(callback_mock)

        # Set low threshold to trigger alert
        analytics.alert_thresholds["hit_rate_min"] = 0.9

        # Record events that should trigger alert
        await analytics.record_hit("test_cache")
        await analytics.record_miss("test_cache")
        await analytics.record_miss("test_cache")
        await analytics.record_miss("test_cache")

        # Alert should have been triggered
        callback_mock.assert_called()

    async def test_clear_metrics_specific(self, analytics):
        """Test clearing metrics for specific cache."""
        await analytics.record_hit("cache1")
        await analytics.record_hit("cache2")

        await analytics.clear_metrics("cache1")

        metrics1 = await analytics.get_metrics("cache1")
        metrics2 = await analytics.get_metrics("cache2")

        assert metrics1.hits == 0
        assert metrics2.hits == 1

    async def test_clear_metrics_all(self, analytics):
        """Test clearing all metrics."""
        await analytics.record_hit("cache1")
        await analytics.record_hit("cache2")

        await analytics.clear_metrics()

        all_metrics = await analytics.get_metrics()

        assert len(all_metrics) == 0

    async def test_timeframe_parsing(self, analytics):
        """Test timeframe string parsing."""
        assert analytics._parse_timeframe("1m") == 1
        assert analytics._parse_timeframe("5m") == 5
        assert analytics._parse_timeframe("1h") == 60
        assert analytics._parse_timeframe("24h") == 1440
        assert analytics._parse_timeframe("1d") == 1440

    async def test_calculate_trends(self, analytics):
        """Test trend calculation."""
        # Record some events
        await analytics.record_hit("test_cache")
        await analytics.record_hit("test_cache")

        trends = await analytics._calculate_trends(["test_cache"], "1h")

        assert "test_cache" in trends


class TestJSONMetricsExporter:
    """Test cases for JSONMetricsExporter."""

    async def test_export_success(self, tmp_path):
        """Test successful JSON export."""
        filepath = tmp_path / "metrics.json"
        exporter = JSONMetricsExporter(str(filepath))

        report = PerformanceReport(timeframe="1h", cache_names=["test"])

        result = await exporter.export(report)

        assert result is True
        assert filepath.exists()

        # Verify content
        with open(filepath) as f:
            data = json.load(f)
            assert data["timeframe"] == "1h"

    async def test_export_failure(self, tmp_path):
        """Test JSON export failure handling."""
        # Use invalid path
        exporter = JSONMetricsExporter("/nonexistent/path/metrics.json")

        report = PerformanceReport(timeframe="1h", cache_names=["test"])

        result = await exporter.export(report)

        assert result is False


class TestPrometheusMetricsExporter:
    """Test cases for PrometheusMetricsExporter."""

    async def test_export_success(self, tmp_path):
        """Test successful Prometheus export."""
        filepath = tmp_path / "metrics.prom"
        exporter = PrometheusMetricsExporter(str(filepath))

        metrics = CacheMetrics(cache_name="test", hits=100, misses=50)
        report = PerformanceReport(timeframe="1h", cache_names=["test"], metrics={"test": metrics})

        result = await exporter.export(report)

        assert result is True
        assert filepath.exists()

        # Verify content
        content = filepath.read_text()
        assert "# HELP" in content
        assert "cache_test_hits" in content


class TestMetricTypes:
    """Test cases for MetricType enum."""

    def test_metric_type_values(self):
        """Test metric type values."""
        assert MetricType.HIT.value == "hit"
        assert MetricType.MISS.value == "miss"
        assert MetricType.EVICTION.value == "eviction"
        assert MetricType.ERROR.value == "error"
        assert MetricType.LATENCY.value == "latency"


class TestTimeWindows:
    """Test cases for TimeWindow enum."""

    def test_time_window_values(self):
        """Test time window values in seconds."""
        assert TimeWindow.MINUTE_1.value == 60
        assert TimeWindow.MINUTE_5.value == 300
        assert TimeWindow.HOUR_1.value == 3600
        assert TimeWindow.HOUR_24.value == 86400