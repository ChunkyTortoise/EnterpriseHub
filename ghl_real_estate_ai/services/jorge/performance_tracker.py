"""
Jorge Performance Tracker Service

Tracks latency, throughput, cache hits, and SLA compliance for all Jorge bot operations.
Uses in-memory storage with rolling windows (1h, 24h, 7d) and provides 
percentile-based latency stats, throughput metrics, and SLA violation detection.

Usage:
    tracker = PerformanceTracker()
    
    # Manual tracking
    await tracker.track_operation("lead_bot", "qualify", 1500, True)
    
    # Context manager for async operations
    async with tracker.track_async_operation("lead_bot", "process"):
        await process_lead()
    
    # Get stats
    stats = await tracker.get_bot_stats("lead_bot")
    
    # Check SLA compliance
    compliance = await tracker.check_sla_compliance()

SLA Targets (Phase 4 Audit Spec):
    - Lead Bot P95 < 2000ms
    - Buyer Bot P95 < 2500ms
    - Seller Bot P95 < 2500ms
    - Handoff P95 < 500ms
"""

import asyncio
import logging
import math
import statistics
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, AsyncIterator, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


# ── SLA Configuration (from Phase 4 Audit Spec) ─────────────────────────
SLA_CONFIG: Dict[str, Dict[str, float]] = {
    "lead_bot": {
        "full_qualification": {"p50_target": 500, "p95_target": 2000, "p99_target": 3000},
        "process": {"p50_target": 300, "p95_target": 1500, "p99_target": 2000},
        "handoff": {"p50_target": 100, "p95_target": 500, "p99_target": 800},
    },
    "buyer_bot": {
        "full_qualification": {"p50_target": 800, "p95_target": 2500, "p99_target": 3500},
        "process": {"p50_target": 400, "p95_target": 1800, "p99_target": 2500},
        "handoff": {"p50_target": 100, "p95_target": 500, "p99_target": 800},
    },
    "seller_bot": {
        "full_qualification": {"p50_target": 700, "p95_target": 2500, "p99_target": 3500},
        "process": {"p50_target": 400, "p95_target": 1800, "p99_target": 2500},
        "handoff": {"p50_target": 100, "p95_target": 500, "p99_target": 800},
    },
    "handoff": {
        "execute": {"p50_target": 100, "p95_target": 500, "p99_target": 800},
    },
}

# Rolling window configurations (in seconds)
WINDOWS = {
    "1h": 3600,
    "24h": 86400,
    "7d": 604800,
}

# Bot names for validation
VALID_BOT_NAMES = frozenset(["lead_bot", "buyer_bot", "seller_bot", "handoff"])


@dataclass
class _OperationEntry:
    """A single recorded operation timing."""
    timestamp: float
    duration_ms: float
    success: bool = True
    cache_hit: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class _SLATarget:
    """SLA target thresholds for an operation."""
    operation: str
    target_p50_ms: float
    target_p95_ms: float
    target_p99_ms: float = 0.0


class PerformanceTracker:
    """Performance tracking service for Jorge bots.

    Thread-safe, in-memory performance monitoring with rolling-window
    storage and percentile-based latency analysis.
    
    Supports:
    - Response time tracking (P50, P95, P99)
    - Request counts (success, error, total)
    - Cache hit rates
    - SLA compliance checking
    - Multiple rolling windows (1h, 24h, 7d)
    """

    # ── Singleton ─────────────────────────────────────────────────────
    _instance: Optional["PerformanceTracker"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "PerformanceTracker":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        
        # Rolling windows: bot -> operation -> window -> deque of entries
        self._operations: Dict[str, Dict[str, Dict[str, deque]]] = {}
        self._sla_targets: Dict[str, Dict[str, _SLATarget]] = {}
        self._data_lock = threading.Lock()
        self._initialized = True
        
        # Initialize data structures for each bot and window
        for bot_name in VALID_BOT_NAMES:
            self._operations[bot_name] = {}
            for window_name in WINDOWS:
                self._operations[bot_name][window_name] = deque(maxlen=10000)
        
        # Register default SLAs from audit spec
        self._register_default_slas()
        
        logger.info("PerformanceTracker initialized with %d bots, %d windows", 
                   len(VALID_BOT_NAMES), len(WINDOWS))

    def _register_default_slas(self) -> None:
        """Register SLA targets from SLA_CONFIG."""
        for bot_name, operations in SLA_CONFIG.items():
            self._sla_targets[bot_name] = {}
            for operation, targets in operations.items():
                self._sla_targets[bot_name][operation] = _SLATarget(
                    operation=operation,
                    target_p50_ms=targets["p50_target"],
                    target_p95_ms=targets["p95_target"],
                    target_p99_ms=targets.get("p99_target", 0.0),
                )
        logger.info("Registered %d SLA targets", sum(len(v) for v in self._sla_targets.values()))

    # ── Timing ────────────────────────────────────────────────────────

    def record_operation(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Record a single operation's timing.

        Args:
            operation: Operation name (e.g. "lead_bot.full_qualification").
            duration_ms: Duration in milliseconds.
            metadata: Optional key-value metadata to attach.
        """
        entry = _OperationEntry(
            timestamp=time.time(),
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

        with self._data_lock:
            if operation not in self._operations:
                self._operations[operation] = []
            self._operations[operation].append(entry)

        logger.debug(
            "Recorded %s: %.2fms%s",
            operation,
            duration_ms,
            f" ({metadata})" if metadata else "",
        )

    @asynccontextmanager
    async def track_operation(
        self, operation: str, metadata: Optional[Dict[str, Any]] = None
    ) -> AsyncIterator[None]:
        """Async context manager that auto-records start/end timing.

        Usage:
            async with tracker.track_operation("lead_bot.process"):
                await process_lead()

        Args:
            operation: Operation name to track.
            metadata: Optional key-value metadata to attach.

        Yields:
            None
        """
        start = time.perf_counter()
        try:
            yield
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            self.record_operation(operation, elapsed_ms, metadata)

    # ── Metrics Retrieval ─────────────────────────────────────────────

    def get_latency_stats(
        self, operation: str, window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Return latency percentile statistics for an operation.

        Args:
            operation: Operation name to query.
            window_minutes: Rolling window size in minutes (default 60).

        Returns:
            Dict with keys: p50, p95, p99, mean, min, max, count.
            Returns zeroed dict if no data exists.
        """
        durations = self._get_durations_in_window(operation, window_minutes)

        if not durations:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
            }

        sorted_durations = sorted(durations)

        return {
            "p50": self._percentile(sorted_durations, 50),
            "p95": self._percentile(sorted_durations, 95),
            "p99": self._percentile(sorted_durations, 99),
            "mean": round(statistics.mean(sorted_durations), 2),
            "min": round(min(sorted_durations), 2),
            "max": round(max(sorted_durations), 2),
            "count": len(sorted_durations),
        }

    def get_throughput(
        self, operation: str, window_minutes: int = 60
    ) -> Dict[str, Any]:
        """Return throughput metrics for an operation.

        Args:
            operation: Operation name to query.
            window_minutes: Rolling window size in minutes (default 60).

        Returns:
            Dict with keys: total, per_minute, per_second.
        """
        cutoff = time.time() - (window_minutes * 60)

        with self._data_lock:
            entries = self._operations.get(operation, [])
            in_window = [e for e in entries if e.timestamp >= cutoff]

        total = len(in_window)
        window_seconds = window_minutes * 60

        return {
            "total": total,
            "per_minute": round(total / window_minutes, 2) if window_minutes > 0 else 0.0,
            "per_second": round(total / window_seconds, 4) if window_seconds > 0 else 0.0,
        }

    def get_all_operations(self) -> List[str]:
        """List all tracked operation names.

        Returns:
            Sorted list of operation name strings.
        """
        with self._data_lock:
            return sorted(self._operations.keys())

    # ── SLA Monitoring ────────────────────────────────────────────────

    def register_sla(
        self, operation: str, target_p95_ms: float, target_p50_ms: float
    ) -> None:
        """Register SLA targets for an operation.

        Args:
            operation: Operation name.
            target_p95_ms: Maximum acceptable p95 latency in ms.
            target_p50_ms: Maximum acceptable p50 latency in ms.
        """
        with self._data_lock:
            self._sla_targets[operation] = _SLATarget(
                operation=operation,
                target_p50_ms=target_p50_ms,
                target_p95_ms=target_p95_ms,
            )

        logger.info(
            "Registered SLA for '%s': p50 <= %.0fms, p95 <= %.0fms",
            operation,
            target_p50_ms,
            target_p95_ms,
        )

    def check_sla_compliance(self, operation: str) -> Dict[str, Any]:
        """Check SLA compliance for a specific operation.

        Args:
            operation: Operation name to check.

        Returns:
            Dict with keys: compliant, p95_target, p95_actual, p50_target,
            p50_actual, violations.

        Raises:
            KeyError: If no SLA is registered for the operation.
        """
        with self._data_lock:
            if operation not in self._sla_targets:
                raise KeyError(f"No SLA registered for operation '{operation}'")
            target = self._sla_targets[operation]

        stats = self.get_latency_stats(operation)
        violations: List[str] = []

        p50_actual = stats["p50"]
        p95_actual = stats["p95"]

        if stats["count"] > 0:
            if p50_actual > target.target_p50_ms:
                violations.append(
                    f"p50 {p50_actual:.1f}ms exceeds target {target.target_p50_ms:.0f}ms"
                )
            if p95_actual > target.target_p95_ms:
                violations.append(
                    f"p95 {p95_actual:.1f}ms exceeds target {target.target_p95_ms:.0f}ms"
                )

        return {
            "compliant": len(violations) == 0,
            "p95_target": target.target_p95_ms,
            "p95_actual": p95_actual,
            "p50_target": target.target_p50_ms,
            "p50_actual": p50_actual,
            "violations": violations,
        }

    def get_sla_report(self) -> Dict[str, Any]:
        """Return SLA compliance status for all registered SLAs.

        Returns:
            Dict mapping operation names to their compliance status dicts.
            Includes an overall 'all_compliant' flag.
        """
        with self._data_lock:
            operations = list(self._sla_targets.keys())

        report: Dict[str, Any] = {}
        all_compliant = True

        for operation in operations:
            compliance = self.check_sla_compliance(operation)
            report[operation] = compliance
            if not compliance["compliant"]:
                all_compliant = False

        report["all_compliant"] = all_compliant
        return report

    # ── Cleanup ───────────────────────────────────────────────────────

    def _cleanup_old_entries(self, max_age_seconds: int = 3600) -> int:
        """Prune entries older than the specified window.

        Args:
            max_age_seconds: Maximum age in seconds (default 3600 = 1 hour).

        Returns:
            Number of entries removed.
        """
        cutoff = time.time() - max_age_seconds
        removed = 0

        with self._data_lock:
            for operation in self._operations:
                original = self._operations[operation]
                pruned = [e for e in original if e.timestamp >= cutoff]
                removed += len(original) - len(pruned)
                self._operations[operation] = pruned

        if removed > 0:
            logger.info("Cleaned up %d old entries (max_age=%ds)", removed, max_age_seconds)

        return removed

    # ── Internal Helpers ──────────────────────────────────────────────

    def _get_durations_in_window(
        self, operation: str, window_minutes: int
    ) -> List[float]:
        """Extract duration values within the rolling window.

        Args:
            operation: Operation name.
            window_minutes: Window size in minutes.

        Returns:
            List of duration_ms values within the window.
        """
        cutoff = time.time() - (window_minutes * 60)

        with self._data_lock:
            entries = self._operations.get(operation, [])
            return [e.duration_ms for e in entries if e.timestamp >= cutoff]

    @staticmethod
    def _percentile(sorted_data: List[float], pct: int) -> float:
        """Calculate a percentile from pre-sorted data.

        Uses linear interpolation between nearest ranks.

        Args:
            sorted_data: Pre-sorted list of values.
            pct: Percentile (0-100).

        Returns:
            The interpolated percentile value, rounded to 2 decimals.
        """
        if not sorted_data:
            return 0.0

        n = len(sorted_data)
        if n == 1:
            return round(sorted_data[0], 2)

        # Rank calculation (0-indexed)
        rank = (pct / 100.0) * (n - 1)
        lower_idx = int(rank)
        upper_idx = min(lower_idx + 1, n - 1)
        fraction = rank - lower_idx

        value = sorted_data[lower_idx] + fraction * (
            sorted_data[upper_idx] - sorted_data[lower_idx]
        )
        return round(value, 2)

    # ── Testing Support ───────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. For testing only."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._operations.clear()
                cls._instance._sla_targets.clear()
                cls._instance._initialized = False
            cls._instance = None
