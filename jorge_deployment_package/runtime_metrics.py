#!/usr/bin/env python3
"""
In-process runtime metrics registry for the Jorge FastAPI services.
"""

from collections import deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock
from typing import Any, Deque, Dict


@dataclass
class RequestEvent:
    timestamp: datetime
    latency_ms: float
    status_code: int
    path: str


class RuntimeMetricsRegistry:
    """Tracks counters and rolling-window latency/error metrics."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._events: Deque[RequestEvent] = deque()
        self._max_history_seconds = 24 * 60 * 60

        self.requests_total = 0
        self.errors_total = 0
        self.latency_ms_sum = 0.0
        self.latency_ms_count = 0
        self.five_minute_violations = 0

        self.ghl_calls_total = 0
        self.ghl_calls_failed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.signature_failures = 0
        self.duplicate_webhooks = 0
        self.feature_flag_evaluations_total: Dict[str, int] = {}
        self.feature_flag_enabled_total: Dict[str, int] = {}
        self.feature_flag_blocked_total: Dict[str, int] = {}
        self.growth_feature_events_total: Dict[str, int] = {}

    def record_request(self, path: str, latency_ms: float, status_code: int) -> None:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._events.append(
                RequestEvent(
                    timestamp=now,
                    latency_ms=max(0.0, float(latency_ms)),
                    status_code=int(status_code),
                    path=path,
                )
            )
            self._purge_old(now)

            self.requests_total += 1
            self.latency_ms_sum += max(0.0, float(latency_ms))
            self.latency_ms_count += 1

            if status_code >= 500:
                self.errors_total += 1
            if latency_ms > 300000:
                self.five_minute_violations += 1

    def record_ghl_call(self, success: bool) -> None:
        with self._lock:
            self.ghl_calls_total += 1
            if not success:
                self.ghl_calls_failed += 1

    def record_cache_hit(self) -> None:
        with self._lock:
            self.cache_hits += 1

    def record_cache_miss(self) -> None:
        with self._lock:
            self.cache_misses += 1

    def record_signature_failure(self) -> None:
        with self._lock:
            self.signature_failures += 1

    def record_duplicate_webhook(self) -> None:
        with self._lock:
            self.duplicate_webhooks += 1

    def record_feature_flag_evaluation(
        self,
        feature_name: str,
        enabled: bool,
        reason: str = "",
    ) -> None:
        with self._lock:
            self._increment_dict_counter(self.feature_flag_evaluations_total, feature_name)
            if enabled:
                self._increment_dict_counter(self.feature_flag_enabled_total, feature_name)
            else:
                self._increment_dict_counter(self.feature_flag_blocked_total, feature_name)
                if reason:
                    blocked_reason_key = f"{feature_name}:{reason}"
                    self._increment_dict_counter(self.feature_flag_blocked_total, blocked_reason_key)

    def record_growth_feature_event(self, feature_name: str, event_name: str) -> None:
        with self._lock:
            key = f"{feature_name}:{event_name}"
            self._increment_dict_counter(self.growth_feature_events_total, key)

    def snapshot(self) -> Dict[str, Any]:
        now = datetime.now(timezone.utc)
        with self._lock:
            self._purge_old(now)
            return {
                "generated_at": now.isoformat(),
                "overall": self._window_stats(window_seconds=self._max_history_seconds, now=now),
                "windows": {
                    "1m": self._window_stats(window_seconds=60, now=now),
                    "5m": self._window_stats(window_seconds=300, now=now),
                    "24h": self._window_stats(window_seconds=24 * 60 * 60, now=now),
                },
                "counters": {
                    "requests_total": self.requests_total,
                    "errors_total": self.errors_total,
                    "latency_ms_sum": self.latency_ms_sum,
                    "latency_ms_count": self.latency_ms_count,
                    "latency_ms_p95": self._p95([event.latency_ms for event in self._events]),
                    "ghl_calls_total": self.ghl_calls_total,
                    "ghl_calls_failed": self.ghl_calls_failed,
                    "cache_hits": self.cache_hits,
                    "cache_misses": self.cache_misses,
                    "signature_failures": self.signature_failures,
                    "duplicate_webhooks": self.duplicate_webhooks,
                    "five_minute_violations": self.five_minute_violations,
                    "feature_flag_evaluations_total": dict(self.feature_flag_evaluations_total),
                    "feature_flag_enabled_total": dict(self.feature_flag_enabled_total),
                    "feature_flag_blocked_total": dict(self.feature_flag_blocked_total),
                    "growth_feature_events_total": dict(self.growth_feature_events_total),
                },
                "rates": {
                    "avg_response_ms": self._average(
                        total=self.latency_ms_sum,
                        count=self.latency_ms_count,
                    ),
                    "ghl_success_rate": self._ghl_success_rate(),
                    "cache_hit_rate": self._cache_hit_rate(),
                },
            }

    def _window_stats(self, window_seconds: int, now: datetime) -> Dict[str, Any]:
        cutoff = now.timestamp() - float(window_seconds)
        events = [event for event in self._events if event.timestamp.timestamp() >= cutoff]
        latencies = [event.latency_ms for event in events]
        errors = [event for event in events if event.status_code >= 500]
        five_minute_violations = [event for event in events if event.latency_ms > 300000]
        return {
            "requests_total": len(events),
            "errors_total": len(errors),
            "latency_ms_sum": sum(latencies),
            "latency_ms_count": len(latencies),
            "latency_ms_avg": self._average(sum(latencies), len(latencies)),
            "latency_ms_p95": self._p95(latencies),
            "five_minute_violations": len(five_minute_violations),
        }

    @staticmethod
    def _average(total: float, count: int) -> float:
        if count <= 0:
            return 0.0
        return float(total) / float(count)

    @staticmethod
    def _p95(latencies: list[float]) -> float:
        if not latencies:
            return 0.0
        ordered = sorted(latencies)
        index = int(round(0.95 * (len(ordered) - 1)))
        return float(ordered[index])

    def _ghl_success_rate(self) -> float:
        if self.ghl_calls_total == 0:
            return 1.0
        return max(0.0, 1.0 - (self.ghl_calls_failed / self.ghl_calls_total))

    def _cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total

    def _purge_old(self, now: datetime) -> None:
        cutoff = now.timestamp() - float(self._max_history_seconds)
        while self._events and self._events[0].timestamp.timestamp() < cutoff:
            self._events.popleft()

    @staticmethod
    def _increment_dict_counter(counter_dict: Dict[str, int], key: str) -> None:
        counter_dict[key] = counter_dict.get(key, 0) + 1
