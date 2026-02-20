"""Tests for MetricsAggregator: percentiles, rolling windows, breakdowns."""

from datetime import datetime, timedelta

import pytest

from devops_suite.monitoring.metrics import MetricsAggregator


@pytest.fixture
def aggregator():
    return MetricsAggregator(window_seconds=300)


class TestMetricsAggregator:
    def test_record_and_compute_basic(self, aggregator):
        now = datetime.utcnow()
        for val in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
            aggregator.record("latency", val, timestamp=now)
        result = aggregator.compute_percentiles("latency", now=now)
        assert result is not None
        assert result.count == 10
        assert result.min == 10
        assert result.max == 100
        assert result.mean == 55.0

    def test_p50_p95_p99(self, aggregator):
        now = datetime.utcnow()
        for i in range(1, 101):
            aggregator.record("latency", float(i), timestamp=now)
        result = aggregator.compute_percentiles("latency", now=now)
        assert result is not None
        assert result.p50 == pytest.approx(50.0, abs=2)
        assert result.p95 == pytest.approx(95.0, abs=2)
        assert result.p99 == pytest.approx(99.0, abs=2)

    def test_rolling_window_prunes_old(self, aggregator):
        old = datetime.utcnow() - timedelta(seconds=600)
        now = datetime.utcnow()
        aggregator.record("latency", 100.0, timestamp=old)
        aggregator.record("latency", 50.0, timestamp=now)
        result = aggregator.compute_percentiles("latency", now=now)
        assert result is not None
        assert result.count == 1
        assert result.mean == 50.0

    def test_empty_metric_returns_none(self, aggregator):
        result = aggregator.compute_percentiles("nonexistent")
        assert result is None

    def test_single_value(self, aggregator):
        now = datetime.utcnow()
        aggregator.record("latency", 42.0, timestamp=now)
        result = aggregator.compute_percentiles("latency", now=now)
        assert result is not None
        assert result.p50 == 42.0
        assert result.count == 1

    def test_compute_by_agent(self, aggregator):
        now = datetime.utcnow()
        for i in range(10):
            aggregator.record("latency", float(i), timestamp=now, agent_id="agent-a")
        for i in range(10, 20):
            aggregator.record("latency", float(i), timestamp=now, agent_id="agent-b")
        by_agent = aggregator.compute_by_agent("latency", now=now)
        assert "agent-a" in by_agent
        assert "agent-b" in by_agent
        assert by_agent["agent-a"].max == 9.0
        assert by_agent["agent-b"].min == 10.0

    def test_compute_by_model(self, aggregator):
        now = datetime.utcnow()
        aggregator.record("cost", 0.01, timestamp=now, model="gpt-4")
        aggregator.record("cost", 0.001, timestamp=now, model="gpt-3.5")
        by_model = aggregator.compute_by_model("cost", now=now)
        assert "gpt-4" in by_model
        assert "gpt-3.5" in by_model

    def test_success_rate(self, aggregator):
        now = datetime.utcnow()
        for _ in range(8):
            aggregator.record("status", 1.0, timestamp=now)
        for _ in range(2):
            aggregator.record("status", 0.0, timestamp=now)
        rate = aggregator.success_rate(now=now)
        assert rate == pytest.approx(0.8)

    def test_success_rate_empty(self, aggregator):
        assert aggregator.success_rate() is None

    def test_get_metric_names(self, aggregator):
        aggregator.record("latency", 1.0)
        aggregator.record("cost", 0.01)
        names = aggregator.get_metric_names()
        assert set(names) == {"latency", "cost"}

    def test_clear_specific(self, aggregator):
        aggregator.record("latency", 1.0)
        aggregator.record("cost", 0.01)
        aggregator.clear("latency")
        assert aggregator.compute_percentiles("latency") is None
        assert aggregator.compute_percentiles("cost") is not None

    def test_clear_all(self, aggregator):
        aggregator.record("latency", 1.0)
        aggregator.record("cost", 0.01)
        aggregator.clear()
        assert aggregator.get_metric_names() == []
