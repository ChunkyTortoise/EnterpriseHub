from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

import pytest

"""Tests for Agent Decision Cost Tracker."""

import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from ghl_real_estate_ai.services.agent_cost_tracker import (
    AgentCostSummary,
    CostAnomalyDetector,
    CostReport,
    DecisionCost,
    DecisionCostTracker,
    TokenEfficiencyMetrics,
)

# ---------------------------------------------------------------------------
# DecisionCost dataclass
# ---------------------------------------------------------------------------


class TestDecisionCost:
    def test_create_basic(self):
        dc = DecisionCost(
            agent_name="lead_bot",
            decision_type="qualification",
            input_tokens=100,
            output_tokens=50,
            total_tokens=150,
            cost_usd=0.003,
            latency_ms=120.5,
            timestamp=1000.0,
        )
        assert dc.agent_name == "lead_bot"
        assert dc.total_tokens == 150
        assert dc.metadata == {}

    def test_metadata_preserved(self):
        dc = DecisionCost(
            agent_name="a",
            decision_type="t",
            input_tokens=0,
            output_tokens=0,
            total_tokens=0,
            cost_usd=0.0,
            latency_ms=0.0,
            timestamp=0.0,
            metadata={"model": "opus"},
        )
        assert dc.metadata == {"model": "opus"}


# ---------------------------------------------------------------------------
# DecisionCostTracker
# ---------------------------------------------------------------------------


class TestDecisionCostTracker:
    def _make_tracker(self) -> DecisionCostTracker:
        return DecisionCostTracker()

    def test_record_returns_decision_cost(self):
        tracker = self._make_tracker()
        result = tracker.record("bot_a", "scoring", 100, 50, 0.005, 200.0)
        assert isinstance(result, DecisionCost)
        assert result.agent_name == "bot_a"
        assert result.total_tokens == 150

    def test_record_with_metadata(self):
        tracker = self._make_tracker()
        result = tracker.record("bot_a", "scoring", 10, 5, 0.001, 50.0, metadata={"run": 1})
        assert result.metadata == {"run": 1}

    def test_get_agent_summary_empty(self):
        tracker = self._make_tracker()
        summary = tracker.get_agent_summary("nonexistent")
        assert summary.decision_count == 0
        assert summary.total_cost == 0.0

    def test_get_agent_summary_single(self):
        tracker = self._make_tracker()
        tracker.record("bot_a", "scoring", 100, 50, 0.01, 100.0)
        summary = tracker.get_agent_summary("bot_a")
        assert summary.decision_count == 1
        assert summary.total_cost == 0.01
        assert summary.avg_cost == 0.01
        assert summary.total_tokens == 150
        assert summary.avg_latency == 100.0

    def test_get_agent_summary_multiple(self):
        tracker = self._make_tracker()
        tracker.record("bot_a", "scoring", 100, 50, 0.01, 100.0)
        tracker.record("bot_a", "routing", 200, 100, 0.03, 200.0)
        summary = tracker.get_agent_summary("bot_a")
        assert summary.decision_count == 2
        assert abs(summary.total_cost - 0.04) < 1e-9
        assert abs(summary.avg_cost - 0.02) < 1e-9
        assert summary.total_tokens == 450
        assert abs(summary.avg_latency - 150.0) < 1e-9

    def test_get_decision_type_summary_empty(self):
        tracker = self._make_tracker()
        result = tracker.get_decision_type_summary("unknown")
        assert result["decision_count"] == 0
        assert result["decision_type"] == "unknown"

    def test_get_decision_type_summary(self):
        tracker = self._make_tracker()
        tracker.record("bot_a", "scoring", 100, 50, 0.01, 80.0)
        tracker.record("bot_b", "scoring", 200, 100, 0.03, 120.0)
        result = tracker.get_decision_type_summary("scoring")
        assert result["decision_count"] == 2
        assert abs(result["total_cost"] - 0.04) < 1e-9

    def test_get_all_summaries(self):
        tracker = self._make_tracker()
        tracker.record("bot_a", "scoring", 100, 50, 0.01, 80.0)
        tracker.record("bot_b", "routing", 200, 100, 0.03, 120.0)
        summaries = tracker.get_all_summaries()
        assert "bot_a" in summaries
        assert "bot_b" in summaries
        assert summaries["bot_a"].decision_count == 1
        assert summaries["bot_b"].decision_count == 1

    def test_get_all_summaries_empty(self):
        tracker = self._make_tracker()
        assert tracker.get_all_summaries() == {}

    def test_get_top_costly_agents(self):
        tracker = self._make_tracker()
        tracker.record("cheap", "t", 10, 5, 0.001, 10.0)
        tracker.record("mid", "t", 100, 50, 0.01, 50.0)
        tracker.record("expensive", "t", 1000, 500, 0.10, 200.0)
        top = tracker.get_top_costly_agents(2)
        assert top == ["expensive", "mid"]

    def test_get_top_costly_agents_more_than_available(self):
        tracker = self._make_tracker()
        tracker.record("only", "t", 10, 5, 0.001, 10.0)
        top = tracker.get_top_costly_agents(5)
        assert top == ["only"]

    def test_get_cost_trend(self):
        tracker = self._make_tracker()
        tracker.record("bot", "t", 10, 5, 1.0, 10.0)
        tracker.record("bot", "t", 10, 5, 3.0, 10.0)
        tracker.record("bot", "t", 10, 5, 5.0, 10.0)
        trend = tracker.get_cost_trend("bot", 2)
        assert len(trend) == 3
        assert trend[0] == 1.0  # window=[1.0]
        assert trend[1] == 2.0  # window=[1.0, 3.0]
        assert trend[2] == 4.0  # window=[3.0, 5.0]

    def test_get_cost_trend_empty(self):
        tracker = self._make_tracker()
        assert tracker.get_cost_trend("bot", 3) == []

    def test_get_cost_trend_zero_window(self):
        tracker = self._make_tracker()
        tracker.record("bot", "t", 10, 5, 1.0, 10.0)
        assert tracker.get_cost_trend("bot", 0) == []


# ---------------------------------------------------------------------------
# CostAnomalyDetector
# ---------------------------------------------------------------------------


class TestCostAnomalyDetector:
    def test_detect_no_anomalies(self):
        detector = CostAnomalyDetector()
        costs = [1.0, 1.1, 0.9, 1.0, 1.05]
        assert detector.detect_anomalies(costs) == []

    def test_detect_spike(self):
        detector = CostAnomalyDetector()
        costs = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 100.0]
        anomalies = detector.detect_anomalies(costs)
        assert 9 in anomalies

    def test_detect_empty(self):
        detector = CostAnomalyDetector()
        assert detector.detect_anomalies([]) == []

    def test_detect_single_value(self):
        detector = CostAnomalyDetector()
        assert detector.detect_anomalies([5.0]) == []

    def test_detect_zero_stdev(self):
        detector = CostAnomalyDetector()
        assert detector.detect_anomalies([1.0, 1.0, 1.0]) == []

    def test_is_anomalous_true(self):
        detector = CostAnomalyDetector()
        history = [1.0, 1.0, 1.0, 1.0, 1.0]
        assert detector.is_anomalous(100.0, history) is True

    def test_is_anomalous_false(self):
        detector = CostAnomalyDetector()
        history = [1.0, 1.1, 0.9, 1.0, 1.05]
        assert detector.is_anomalous(1.02, history) is False

    def test_is_anomalous_short_history(self):
        detector = CostAnomalyDetector()
        assert detector.is_anomalous(100.0, [1.0]) is False

    def test_is_anomalous_zero_stdev_different(self):
        detector = CostAnomalyDetector()
        assert detector.is_anomalous(5.0, [1.0, 1.0, 1.0]) is True


# ---------------------------------------------------------------------------
# TokenEfficiencyMetrics
# ---------------------------------------------------------------------------


class TestTokenEfficiencyMetrics:
    def test_compute_efficiency(self):
        m = TokenEfficiencyMetrics()
        assert m.compute_efficiency(0.9, 1000) == 0.9 / 1000

    def test_compute_efficiency_zero_tokens(self):
        m = TokenEfficiencyMetrics()
        assert m.compute_efficiency(0.9, 0) == 0.0

    def test_compute_cost_per_quality(self):
        m = TokenEfficiencyMetrics()
        assert m.compute_cost_per_quality(0.10, 0.5) == 0.20

    def test_compute_cost_per_quality_zero_quality(self):
        m = TokenEfficiencyMetrics()
        assert m.compute_cost_per_quality(0.10, 0.0) == math.inf

    def test_compare_agents(self):
        m = TokenEfficiencyMetrics()
        summaries = {
            "efficient": AgentCostSummary(0.01, 0.01, 100, 10, 50.0),
            "wasteful": AgentCostSummary(0.10, 0.10, 5000, 10, 200.0),
        }
        rankings = m.compare_agents(summaries)
        keys = list(rankings.keys())
        assert keys[0] == "efficient"
        assert keys[1] == "wasteful"
        assert rankings["efficient"] == 10.0
        assert rankings["wasteful"] == 500.0

    def test_compare_agents_zero_decisions(self):
        m = TokenEfficiencyMetrics()
        summaries = {
            "idle": AgentCostSummary(0.0, 0.0, 0, 0, 0.0),
        }
        rankings = m.compare_agents(summaries)
        assert rankings["idle"] == 0.0


# ---------------------------------------------------------------------------
# CostReport dataclass
# ---------------------------------------------------------------------------


class TestCostReport:
    def test_create_report(self):
        report = CostReport(
            agent_summaries={"a": AgentCostSummary(0.1, 0.1, 1000, 1, 50.0)},
            total_cost=0.1,
            total_tokens=1000,
            anomalies=[],
            efficiency_rankings={"a": 1000.0},
            generated_at=1000.0,
        )
        assert report.total_cost == 0.1
        assert "a" in report.agent_summaries
        assert report.anomalies == []
