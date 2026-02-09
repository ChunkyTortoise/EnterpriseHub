"""Tests for LLM Observability Service."""

from __future__ import annotations

import time

import pytest

from ghl_real_estate_ai.services.llm_observability import (
    LatencyReport,
    LLMObservabilityService,
    LLMTrace,
    ObservabilityDashboard,
)


@pytest.fixture
def svc() -> LLMObservabilityService:
    return LLMObservabilityService()


def _trace(
    *,
    model: str = "claude-opus-4-6",
    provider: str = "anthropic",
    input_tokens: int = 100,
    output_tokens: int = 200,
    latency_ms: float = 150.0,
    cache_hit: bool = False,
    status: str = "success",
    error_message: str | None = None,
    conversation_id: str | None = None,
    cost_usd: float = 0.01,
    timestamp: float = 0.0,
    trace_id: str = "",
) -> LLMTrace:
    return LLMTrace(
        trace_id=trace_id or f"t-{time.time_ns()}",
        model=model,
        provider=provider,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        latency_ms=latency_ms,
        cache_hit=cache_hit,
        status=status,
        error_message=error_message,
        timestamp=timestamp or time.time(),
        conversation_id=conversation_id,
        cost_usd=cost_usd,
    )


class TestRecordAndRetrieve:
    def test_record_single_trace(self, svc: LLMObservabilityService) -> None:
        t = _trace(trace_id="t-1")
        svc.record_trace(t)
        traces = svc.get_traces()
        assert len(traces) == 1
        assert traces[0].trace_id == "t-1"

    def test_record_multiple_traces(self, svc: LLMObservabilityService) -> None:
        for i in range(5):
            svc.record_trace(_trace(trace_id=f"t-{i}"))
        assert len(svc.get_traces()) == 5

    def test_get_traces_limit(self, svc: LLMObservabilityService) -> None:
        for i in range(10):
            svc.record_trace(_trace(trace_id=f"t-{i}"))
        assert len(svc.get_traces(limit=3)) == 3

    def test_filter_by_model(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(model="claude-opus-4-6"))
        svc.record_trace(_trace(model="gpt-4"))
        svc.record_trace(_trace(model="claude-opus-4-6"))
        result = svc.get_traces(model="gpt-4")
        assert len(result) == 1
        assert result[0].model == "gpt-4"

    def test_filter_by_status(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(status="success"))
        svc.record_trace(_trace(status="error", error_message="timeout"))
        svc.record_trace(_trace(status="success"))
        result = svc.get_traces(status="error")
        assert len(result) == 1
        assert result[0].status == "error"

    def test_filter_by_model_and_status(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(model="gpt-4", status="success"))
        svc.record_trace(_trace(model="gpt-4", status="error"))
        svc.record_trace(_trace(model="claude-opus-4-6", status="error"))
        result = svc.get_traces(model="gpt-4", status="error")
        assert len(result) == 1


class TestLatencyReport:
    def test_percentiles_computed(self, svc: LLMObservabilityService) -> None:
        latencies = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        for lat in latencies:
            svc.record_trace(_trace(latency_ms=float(lat)))
        report = svc.latency_report()
        assert isinstance(report, LatencyReport)
        assert report.sample_count == 10
        assert report.min_ms == 10.0
        assert report.max_ms == 100.0
        assert report.p50_ms == pytest.approx(55.0, abs=10)
        assert report.p95_ms >= report.p50_ms
        assert report.p99_ms >= report.p95_ms

    def test_latency_report_by_model(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(model="fast-model", latency_ms=10.0))
        svc.record_trace(_trace(model="fast-model", latency_ms=20.0))
        svc.record_trace(_trace(model="slow-model", latency_ms=500.0))
        report = svc.latency_report(model="fast-model")
        assert report.sample_count == 2
        assert report.max_ms == 20.0

    def test_latency_report_empty(self, svc: LLMObservabilityService) -> None:
        report = svc.latency_report()
        assert report.sample_count == 0
        assert report.p50_ms == 0.0
        assert report.avg_ms == 0.0


class TestDashboard:
    def test_dashboard_aggregation(self, svc: LLMObservabilityService) -> None:
        now = time.time()
        svc.record_trace(_trace(status="success", cache_hit=True, cost_usd=0.01, timestamp=now))
        svc.record_trace(_trace(status="success", cache_hit=False, cost_usd=0.02, timestamp=now))
        svc.record_trace(_trace(status="error", cache_hit=False, cost_usd=0.0, timestamp=now))
        dash = svc.dashboard()
        assert isinstance(dash, ObservabilityDashboard)
        assert dash.total_requests == 3
        assert dash.success_rate == pytest.approx(2 / 3, abs=0.01)
        assert dash.cache_hit_rate == pytest.approx(1 / 3, abs=0.01)
        assert dash.total_cost_usd == pytest.approx(0.03)
        assert dash.avg_cost_per_request == pytest.approx(0.01)
        assert "error" in dash.error_breakdown
        assert dash.error_breakdown["error"] == 1

    def test_dashboard_model_breakdown(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(model="a"))
        svc.record_trace(_trace(model="a"))
        svc.record_trace(_trace(model="b"))
        dash = svc.dashboard()
        assert dash.model_breakdown["a"] == 2
        assert dash.model_breakdown["b"] == 1

    def test_dashboard_empty(self, svc: LLMObservabilityService) -> None:
        dash = svc.dashboard()
        assert dash.total_requests == 0
        assert dash.success_rate == 0.0
        assert dash.cache_hit_rate == 0.0
        assert dash.total_cost_usd == 0.0


class TestErrorRate:
    def test_error_rate_within_window(self, svc: LLMObservabilityService) -> None:
        now = time.time()
        svc.record_trace(_trace(status="success", timestamp=now))
        svc.record_trace(_trace(status="error", timestamp=now))
        svc.record_trace(_trace(status="success", timestamp=now))
        svc.record_trace(_trace(status="error", timestamp=now))
        rate = svc.error_rate(window_seconds=300)
        assert rate == pytest.approx(0.5)

    def test_error_rate_excludes_old_traces(self, svc: LLMObservabilityService) -> None:
        old = time.time() - 600
        now = time.time()
        svc.record_trace(_trace(status="error", timestamp=old))
        svc.record_trace(_trace(status="success", timestamp=now))
        rate = svc.error_rate(window_seconds=300)
        assert rate == 0.0

    def test_error_rate_empty(self, svc: LLMObservabilityService) -> None:
        assert svc.error_rate() == 0.0


class TestCostBreakdown:
    def test_cost_by_model(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(model="a", cost_usd=0.05))
        svc.record_trace(_trace(model="a", cost_usd=0.03))
        svc.record_trace(_trace(model="b", cost_usd=0.10))
        costs = svc.cost_by_model()
        assert costs["a"] == pytest.approx(0.08)
        assert costs["b"] == pytest.approx(0.10)

    def test_cost_by_conversation(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace(conversation_id="c-1", cost_usd=0.01))
        svc.record_trace(_trace(conversation_id="c-1", cost_usd=0.02))
        svc.record_trace(_trace(conversation_id="c-2", cost_usd=0.05))
        svc.record_trace(_trace(conversation_id=None, cost_usd=0.99))
        costs = svc.cost_by_conversation()
        assert costs["c-1"] == pytest.approx(0.03)
        assert costs["c-2"] == pytest.approx(0.05)
        # None conversation_id excluded or stored under special key
        assert len(costs) >= 2


class TestSLACompliance:
    def test_sla_pass(self, svc: LLMObservabilityService) -> None:
        for _ in range(20):
            svc.record_trace(_trace(latency_ms=100.0))
        assert svc.sla_compliance(target_p95_ms=2000.0) is True

    def test_sla_fail(self, svc: LLMObservabilityService) -> None:
        for _ in range(20):
            svc.record_trace(_trace(latency_ms=6000.0))
        assert svc.sla_compliance(target_p95_ms=2000.0) is False

    def test_sla_empty(self, svc: LLMObservabilityService) -> None:
        # No data => compliant by default
        assert svc.sla_compliance() is True


class TestAlertCheck:
    def test_alert_high_error_rate(self, svc: LLMObservabilityService) -> None:
        now = time.time()
        for _ in range(10):
            svc.record_trace(_trace(status="error", timestamp=now))
        alerts = svc.alert_check(error_rate_threshold=0.1)
        assert any("error" in a.lower() for a in alerts)

    def test_alert_high_latency(self, svc: LLMObservabilityService) -> None:
        for _ in range(20):
            svc.record_trace(_trace(latency_ms=10000.0))
        alerts = svc.alert_check(p95_threshold_ms=5000.0)
        assert any("latency" in a.lower() or "p95" in a.lower() for a in alerts)

    def test_no_alerts_healthy(self, svc: LLMObservabilityService) -> None:
        now = time.time()
        for _ in range(20):
            svc.record_trace(_trace(status="success", latency_ms=100.0, timestamp=now))
        alerts = svc.alert_check()
        assert len(alerts) == 0


class TestClear:
    def test_clear(self, svc: LLMObservabilityService) -> None:
        svc.record_trace(_trace())
        svc.record_trace(_trace())
        svc.clear()
        assert len(svc.get_traces()) == 0


class TestStress:
    def test_many_traces(self, svc: LLMObservabilityService) -> None:
        for i in range(1000):
            svc.record_trace(
                _trace(
                    latency_ms=float(i % 100),
                    model=f"model-{i % 3}",
                    cost_usd=0.001 * (i % 10),
                )
            )
        assert len(svc.get_traces(limit=100)) == 100
        report = svc.latency_report()
        assert report.sample_count == 1000
        dash = svc.dashboard()
        assert dash.total_requests == 1000
