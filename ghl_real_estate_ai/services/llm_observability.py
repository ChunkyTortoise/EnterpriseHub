"""LLM Observability Service for tracking model usage, latency, cost, and alerts."""

from __future__ import annotations

import statistics
import time
from collections import defaultdict
from dataclasses import dataclass


@dataclass
class LLMTrace:
    trace_id: str
    model: str
    provider: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cache_hit: bool = False
    status: str = "success"
    error_message: str | None = None
    timestamp: float = 0.0
    conversation_id: str | None = None
    cost_usd: float = 0.0


@dataclass
class LatencyReport:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    avg_ms: float
    min_ms: float
    max_ms: float
    sample_count: int


@dataclass
class ObservabilityDashboard:
    total_requests: int
    success_rate: float
    cache_hit_rate: float
    total_cost_usd: float
    avg_cost_per_request: float
    latency: LatencyReport
    error_breakdown: dict[str, int]
    model_breakdown: dict[str, int]
    requests_per_minute: float


class LLMObservabilityService:
    def __init__(self) -> None:
        self._traces: list[LLMTrace] = []

    def record_trace(self, trace: LLMTrace) -> None:
        self._traces.append(trace)

    def get_traces(
        self,
        limit: int = 100,
        model: str | None = None,
        status: str | None = None,
    ) -> list[LLMTrace]:
        filtered = self._traces
        if model is not None:
            filtered = [t for t in filtered if t.model == model]
        if status is not None:
            filtered = [t for t in filtered if t.status == status]
        return filtered[:limit]

    def latency_report(self, model: str | None = None) -> LatencyReport:
        traces = self._traces
        if model is not None:
            traces = [t for t in traces if t.model == model]
        if not traces:
            return LatencyReport(
                p50_ms=0.0,
                p95_ms=0.0,
                p99_ms=0.0,
                avg_ms=0.0,
                min_ms=0.0,
                max_ms=0.0,
                sample_count=0,
            )
        latencies = sorted(t.latency_ms for t in traces)
        n = len(latencies)
        return LatencyReport(
            p50_ms=self._percentile(latencies, 50),
            p95_ms=self._percentile(latencies, 95),
            p99_ms=self._percentile(latencies, 99),
            avg_ms=statistics.mean(latencies),
            min_ms=latencies[0],
            max_ms=latencies[-1],
            sample_count=n,
        )

    def dashboard(self) -> ObservabilityDashboard:
        total = len(self._traces)
        if total == 0:
            return ObservabilityDashboard(
                total_requests=0,
                success_rate=0.0,
                cache_hit_rate=0.0,
                total_cost_usd=0.0,
                avg_cost_per_request=0.0,
                latency=self.latency_report(),
                error_breakdown={},
                model_breakdown={},
                requests_per_minute=0.0,
            )

        success_count = sum(1 for t in self._traces if t.status == "success")
        cache_hits = sum(1 for t in self._traces if t.cache_hit)
        total_cost = sum(t.cost_usd for t in self._traces)

        error_breakdown: dict[str, int] = defaultdict(int)
        model_breakdown: dict[str, int] = defaultdict(int)
        for t in self._traces:
            if t.status != "success":
                error_breakdown[t.status] += 1
            model_breakdown[t.model] += 1

        timestamps = [t.timestamp for t in self._traces if t.timestamp > 0]
        if len(timestamps) >= 2:
            span_minutes = (max(timestamps) - min(timestamps)) / 60.0
            rpm = total / span_minutes if span_minutes > 0 else float(total)
        else:
            rpm = float(total)

        return ObservabilityDashboard(
            total_requests=total,
            success_rate=success_count / total,
            cache_hit_rate=cache_hits / total,
            total_cost_usd=total_cost,
            avg_cost_per_request=total_cost / total,
            latency=self.latency_report(),
            error_breakdown=dict(error_breakdown),
            model_breakdown=dict(model_breakdown),
            requests_per_minute=rpm,
        )

    def error_rate(self, window_seconds: float = 300) -> float:
        now = time.time()
        cutoff = now - window_seconds
        recent = [t for t in self._traces if t.timestamp >= cutoff]
        if not recent:
            return 0.0
        errors = sum(1 for t in recent if t.status != "success")
        return errors / len(recent)

    def cost_by_model(self) -> dict[str, float]:
        costs: dict[str, float] = defaultdict(float)
        for t in self._traces:
            costs[t.model] += t.cost_usd
        return dict(costs)

    def cost_by_conversation(self) -> dict[str, float]:
        costs: dict[str, float] = defaultdict(float)
        for t in self._traces:
            if t.conversation_id is not None:
                costs[t.conversation_id] += t.cost_usd
        return dict(costs)

    def sla_compliance(self, target_p95_ms: float = 2000.0) -> bool:
        report = self.latency_report()
        if report.sample_count == 0:
            return True
        return report.p95_ms <= target_p95_ms

    def alert_check(
        self,
        error_rate_threshold: float = 0.1,
        p95_threshold_ms: float = 5000.0,
    ) -> list[str]:
        alerts: list[str] = []
        rate = self.error_rate()
        if rate > error_rate_threshold:
            alerts.append(f"High error rate: {rate:.1%} exceeds threshold {error_rate_threshold:.1%}")
        report = self.latency_report()
        if report.sample_count > 0 and report.p95_ms > p95_threshold_ms:
            alerts.append(f"High P95 latency: {report.p95_ms:.0f}ms exceeds threshold {p95_threshold_ms:.0f}ms")
        return alerts

    def clear(self) -> None:
        self._traces.clear()

    @staticmethod
    def _percentile(sorted_values: list[float], pct: float) -> float:
        if not sorted_values:
            return 0.0
        n = len(sorted_values)
        idx = (pct / 100.0) * (n - 1)
        lower = int(idx)
        upper = min(lower + 1, n - 1)
        frac = idx - lower
        return sorted_values[lower] + frac * (sorted_values[upper] - sorted_values[lower])
