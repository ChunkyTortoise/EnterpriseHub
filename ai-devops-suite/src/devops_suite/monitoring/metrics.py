"""Metrics aggregation with P50/P95/P99 percentiles and rolling windows."""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class PercentileResult:
    p50: float
    p95: float
    p99: float
    count: int
    mean: float
    min: float
    max: float


@dataclass
class MetricPoint:
    value: float
    timestamp: datetime
    agent_id: str | None = None
    model: str | None = None


class MetricsAggregator:
    """Aggregates telemetry into percentile metrics with rolling windows."""

    def __init__(self, window_seconds: int = 300):
        self.window_seconds = window_seconds
        self._points: dict[str, list[MetricPoint]] = {}

    def record(self, metric_name: str, value: float, timestamp: datetime | None = None,
               agent_id: str | None = None, model: str | None = None) -> None:
        if metric_name not in self._points:
            self._points[metric_name] = []
        self._points[metric_name].append(
            MetricPoint(value=value, timestamp=timestamp or datetime.utcnow(),
                        agent_id=agent_id, model=model)
        )

    def _prune(self, metric_name: str, now: datetime | None = None) -> list[MetricPoint]:
        now = now or datetime.utcnow()
        cutoff = now - timedelta(seconds=self.window_seconds)
        points = [p for p in self._points.get(metric_name, []) if p.timestamp >= cutoff]
        self._points[metric_name] = points
        return points

    def compute_percentiles(self, metric_name: str, now: datetime | None = None) -> PercentileResult | None:
        points = self._prune(metric_name, now)
        if not points:
            return None
        values = sorted(p.value for p in points)
        return PercentileResult(
            p50=_percentile(values, 0.50),
            p95=_percentile(values, 0.95),
            p99=_percentile(values, 0.99),
            count=len(values),
            mean=statistics.mean(values),
            min=values[0],
            max=values[-1],
        )

    def compute_by_agent(self, metric_name: str, now: datetime | None = None) -> dict[str, PercentileResult]:
        points = self._prune(metric_name, now)
        by_agent: dict[str, list[float]] = {}
        for p in points:
            key = p.agent_id or "unknown"
            by_agent.setdefault(key, []).append(p.value)
        result = {}
        for agent_id, values in by_agent.items():
            values.sort()
            result[agent_id] = PercentileResult(
                p50=_percentile(values, 0.50),
                p95=_percentile(values, 0.95),
                p99=_percentile(values, 0.99),
                count=len(values),
                mean=statistics.mean(values),
                min=values[0],
                max=values[-1],
            )
        return result

    def compute_by_model(self, metric_name: str, now: datetime | None = None) -> dict[str, PercentileResult]:
        points = self._prune(metric_name, now)
        by_model: dict[str, list[float]] = {}
        for p in points:
            key = p.model or "unknown"
            by_model.setdefault(key, []).append(p.value)
        result = {}
        for model, values in by_model.items():
            values.sort()
            result[model] = PercentileResult(
                p50=_percentile(values, 0.50),
                p95=_percentile(values, 0.95),
                p99=_percentile(values, 0.99),
                count=len(values),
                mean=statistics.mean(values),
                min=values[0],
                max=values[-1],
            )
        return result

    def success_rate(self, now: datetime | None = None) -> float | None:
        points = self._prune("status", now)
        if not points:
            return None
        successes = sum(1 for p in points if p.value == 1.0)
        return successes / len(points)

    def get_metric_names(self) -> list[str]:
        return list(self._points.keys())

    def clear(self, metric_name: str | None = None) -> None:
        if metric_name:
            self._points.pop(metric_name, None)
        else:
            self._points.clear()


def _percentile(sorted_values: list[float], pct: float) -> float:
    """Compute percentile from a sorted list using nearest-rank method."""
    if not sorted_values:
        return 0.0
    idx = max(0, int(len(sorted_values) * pct) - 1)
    return sorted_values[min(idx, len(sorted_values) - 1)]
