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
import statistics
import threading
import time
from collections import deque
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Any, AsyncIterator, Callable, Dict, List, Optional

from ghl_real_estate_ai.models.bot_context_types import (
    PerformanceMetrics,
    SLAComplianceResult,
)
from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

logger = logging.getLogger(__name__)


# ── SLA Configuration (from Phase 4 Audit Spec) ─────────────────────────
SLA_CONFIG: Dict[str, Dict[str, Dict[str, float]]] = {
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
        self._repository: Any = None  # Optional MetricsRepository for DB persistence
        self._initialized = True

        # Initialize data structures for each bot and window
        for bot_name in VALID_BOT_NAMES:
            self._operations[bot_name] = {}
            for window_name in WINDOWS:
                self._operations[bot_name][window_name] = deque(maxlen=10000)

        # Register default SLAs from audit spec
        self._register_default_slas()

        logger.info("PerformanceTracker initialized with %d bots, %d windows", len(VALID_BOT_NAMES), len(WINDOWS))

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

    # ── Persistence Configuration ─────────────────────────────────────

    def set_repository(self, repository: Any) -> None:
        """Attach a repository for write-through PostgreSQL persistence.

        The repository object must implement:
            - ``save_performance_operation(bot_name, operation, duration_ms,
              success, cache_hit, metadata, timestamp)`` (async, returns None)
            - ``load_performance_operations(since_timestamp)``
              (async, returns list of dicts)

        Args:
            repository: A repository instance (or None to disable persistence).
        """
        self._repository = repository
        logger.info(
            "PerformanceTracker persistence %s",
            "enabled" if repository else "disabled",
        )

    async def _persist_operation(
        self,
        entry: "_OperationEntry",
        bot_name: str,
        operation: str,
    ) -> None:
        """Write a single performance operation to the database repository."""
        try:
            await self._repository.save_performance_operation(
                bot_name=bot_name,
                operation=operation,
                duration_ms=entry.duration_ms,
                success=entry.success,
                cache_hit=entry.cache_hit,
                metadata=entry.metadata,
                timestamp=entry.timestamp,
            )
        except Exception as exc:
            logger.debug("DB write-through failed for performance op: %s", exc)

    # ── Core Tracking Methods ───────────────────────────────────────────

    @trace_operation("jorge.performance", "track_operation")
    async def track_operation(
        self,
        bot_name: str,
        operation: str,
        duration_ms: float,
        success: bool = True,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Track a bot operation with timing and success status.

        Args:
            bot_name: Bot name (e.g., "lead_bot", "buyer_bot", "seller_bot", "handoff").
            operation: Operation name (e.g., "qualify", "process", "handoff").
            duration_ms: Duration in milliseconds.
            success: Whether the operation succeeded.
            cache_hit: Whether the result was served from cache.
            metadata: Optional key-value metadata to attach.

        Raises:
            ValueError: If bot_name is not in VALID_BOT_NAMES.
        """
        if bot_name not in VALID_BOT_NAMES:
            raise ValueError(f"Invalid bot_name '{bot_name}'. Must be one of {VALID_BOT_NAMES}")

        entry = _OperationEntry(
            timestamp=time.time(),
            duration_ms=duration_ms,
            success=success,
            cache_hit=cache_hit,
            metadata=metadata or {},
        )

        with self._data_lock:
            # Add to all rolling windows
            for window_name in WINDOWS:
                self._operations[bot_name][window_name].append(entry)

        # Write-through to DB (fire-and-forget on error)
        if self._repository is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._persist_operation(entry, bot_name, operation))
            except RuntimeError:
                logger.debug("No event loop for performance DB write-through")

        logger.debug(
            "Recorded %s.%s: %.2fms (success=%s, cache_hit=%s)",
            bot_name,
            operation,
            duration_ms,
            success,
            cache_hit,
        )

    @asynccontextmanager
    async def track_async_operation(
        self,
        bot_name: str,
        operation: str,
        cache_hit: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AsyncIterator[None]:
        """Async context manager that auto-records start/end timing.

        Usage:
            async with tracker.track_async_operation("lead_bot", "process"):
                await process_lead()

        Args:
            bot_name: Bot name to track.
            operation: Operation name to track.
            cache_hit: Whether the result was served from cache.
            metadata: Optional key-value metadata to attach.

        Yields:
            None
        """
        start = time.perf_counter()
        success = True
        try:
            yield
        except Exception as e:
            logger.debug(f"Async operation tracking failed for {bot_name}.{operation}: {e}")
            success = False
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000.0
            await self.track_operation(bot_name, operation, elapsed_ms, success, cache_hit, metadata)

    # ── Metrics Retrieval ─────────────────────────────────────────────

    async def get_percentile(
        self,
        bot_name: str,
        percentile: float,
        window: str = "1h",
    ) -> float:
        """Get a specific percentile value for a bot's operations.

        Args:
            bot_name: Bot name to query.
            percentile: Percentile value (0-100).
            window: Rolling window ("1h", "24h", "7d").

        Returns:
            The percentile value in milliseconds.

        Raises:
            ValueError: If bot_name or window is invalid.
        """
        if bot_name not in VALID_BOT_NAMES:
            raise ValueError(f"Invalid bot_name '{bot_name}'")
        if window not in WINDOWS:
            raise ValueError(f"Invalid window '{window}'. Must be one of {list(WINDOWS.keys())}")

        durations = self._get_durations_in_window(bot_name, window)

        if not durations:
            return 0.0

        sorted_durations = sorted(durations)
        return self._percentile(sorted_durations, percentile)

    @trace_operation("jorge.performance", "get_bot_stats")
    async def get_bot_stats(
        self,
        bot_name: str,
        window: str = "1h",
    ) -> PerformanceMetrics:
        """Get comprehensive statistics for a specific bot.

        Args:
            bot_name: Bot name to query.
            window: Rolling window ("1h", "24h", "7d").

        Returns:
            Dict with keys:
                - p50, p95, p99: Latency percentiles in ms
                - mean, min, max: Additional latency stats
                - count: Total number of operations
                - success_count: Number of successful operations
                - error_count: Number of failed operations
                - cache_hit_count: Number of cache hits
                - cache_hit_rate: Cache hit rate (0-1)
                - success_rate: Success rate (0-1)

        Raises:
            ValueError: If bot_name or window is invalid.
        """
        if bot_name not in VALID_BOT_NAMES:
            raise ValueError(f"Invalid bot_name '{bot_name}'")
        if window not in WINDOWS:
            raise ValueError(f"Invalid window '{window}'. Must be one of {list(WINDOWS.keys())}")

        entries = self._get_entries_in_window(bot_name, window)

        if not entries:
            return {
                "p50": 0.0,
                "p95": 0.0,
                "p99": 0.0,
                "mean": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0,
                "success_count": 0,
                "error_count": 0,
                "cache_hit_count": 0,
                "cache_hit_rate": 0.0,
                "success_rate": 0.0,
            }

        durations = [e.duration_ms for e in entries]
        sorted_durations = sorted(durations)

        success_count = sum(1 for e in entries if e.success)
        error_count = len(entries) - success_count
        cache_hit_count = sum(1 for e in entries if e.cache_hit)

        return {
            "p50": self._percentile(sorted_durations, 50),
            "p95": self._percentile(sorted_durations, 95),
            "p99": self._percentile(sorted_durations, 99),
            "mean": round(statistics.mean(sorted_durations), 2),
            "min": round(min(sorted_durations), 2),
            "max": round(max(sorted_durations), 2),
            "count": len(entries),
            "success_count": success_count,
            "error_count": error_count,
            "cache_hit_count": cache_hit_count,
            "cache_hit_rate": round(cache_hit_count / len(entries), 4) if entries else 0.0,
            "success_rate": round(success_count / len(entries), 4) if entries else 0.0,
        }

    async def get_all_stats(self, window: str = "1h") -> dict[str, PerformanceMetrics]:
        """Get statistics for all bots.

        Args:
            window: Rolling window ("1h", "24h", "7d").

        Returns:
            Dict mapping bot names to their statistics dicts.
        """
        stats: Dict[str, Any] = {}

        for bot_name in VALID_BOT_NAMES:
            stats[bot_name] = await self.get_bot_stats(bot_name, window)

        return stats

    @trace_operation("jorge.performance", "check_sla_compliance")
    async def check_sla_compliance(self, window: str = "1h") -> list[SLAComplianceResult]:
        """Check SLA compliance for all registered SLAs.

        Args:
            window: Rolling window ("1h", "24h", "7d").

        Returns:
            List of compliance dicts, one per bot/operation combination.
            Each dict contains:
                - bot_name: Bot name
                - operation: Operation name
                - compliant: Whether SLA is met
                - p50_target, p95_target, p99_target: SLA targets
                - p50_actual, p95_actual, p99_actual: Actual values
                - violations: List of violation messages
        """
        compliance_list: List[Dict[str, Any]] = []

        for bot_name in VALID_BOT_NAMES:
            if bot_name not in self._sla_targets:
                continue

            for operation, target in self._sla_targets[bot_name].items():
                stats = await self.get_bot_stats(bot_name, window)
                violations: List[str] = []

                if stats["count"] > 0:
                    if stats["p50"] > target.target_p50_ms:
                        violations.append(f"p50 {stats['p50']:.1f}ms exceeds target {target.target_p50_ms:.0f}ms")
                    if stats["p95"] > target.target_p95_ms:
                        violations.append(f"p95 {stats['p95']:.1f}ms exceeds target {target.target_p95_ms:.0f}ms")
                    if target.target_p99_ms > 0 and stats["p99"] > target.target_p99_ms:
                        violations.append(f"p99 {stats['p99']:.1f}ms exceeds target {target.target_p99_ms:.0f}ms")

                compliance_list.append(
                    {
                        "bot_name": bot_name,
                        "operation": operation,
                        "compliant": len(violations) == 0,
                        "p50_target": target.target_p50_ms,
                        "p95_target": target.target_p95_ms,
                        "p99_target": target.target_p99_ms,
                        "p50_actual": stats["p50"],
                        "p95_actual": stats["p95"],
                        "p99_actual": stats["p99"],
                        "violations": violations,
                    }
                )

        return compliance_list

    # ── Internal Helpers ──────────────────────────────────────────────

    def _get_entries_in_window(
        self,
        bot_name: str,
        window: str,
    ) -> List[_OperationEntry]:
        """Get entries within the rolling window.

        Args:
            bot_name: Bot name.
            window: Window name ("1h", "24h", "7d").

        Returns:
            List of entries within the window.
        """
        window_seconds = WINDOWS[window]
        cutoff = time.time() - window_seconds

        with self._data_lock:
            entries = self._operations.get(bot_name, {}).get(window, deque())
            return [e for e in entries if e.timestamp >= cutoff]

    def _get_durations_in_window(
        self,
        bot_name: str,
        window: str,
    ) -> List[float]:
        """Get duration values within the rolling window.

        Args:
            bot_name: Bot name.
            window: Window name ("1h", "24h", "7d").

        Returns:
            List of duration_ms values within the window.
        """
        entries = self._get_entries_in_window(bot_name, window)
        return [e.duration_ms for e in entries]

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

        value = sorted_data[lower_idx] + fraction * (sorted_data[upper_idx] - sorted_data[lower_idx])
        return round(value, 2)

    # ── Testing Support ───────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. For testing only."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._operations.clear()
                cls._instance._sla_targets.clear()
                cls._instance._repository = None
                cls._instance._initialized = False
            cls._instance = None


# ── Decorator for Performance Tracking ─────────────────────────────────


def track_performance(bot_name: str, operation: str):
    """Decorator to track performance of async functions.

    Usage:
        @track_performance("lead_bot", "qualify")
        async def qualify_lead(lead_data):
            # ... qualification logic
            return result

    Args:
        bot_name: Bot name (e.g., "lead_bot", "buyer_bot", "seller_bot", "handoff").
        operation: Operation name (e.g., "qualify", "process", "handoff").

    Returns:
        Decorator function.
    """

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracker = PerformanceTracker()
            start = time.perf_counter()
            success = True
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                logger.debug(f"Performance tracking decorator failed for {bot_name}.{operation}: {e}")
                success = False
                raise
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                await tracker.track_operation(bot_name, operation, elapsed_ms, success)

        return wrapper

    return decorator


# ── Convenience Functions ─────────────────────────────────────────────


async def get_performance_summary(window: str = "1h") -> dict[str, Any]:
    """Get a performance summary for all bots.

    Args:
        window: Rolling window ("1h", "24h", "7d").

    Returns:
        Dict with overall stats and per-bot breakdown.
    """
    tracker = PerformanceTracker()
    all_stats = await tracker.get_all_stats(window)
    compliance = await tracker.check_sla_compliance(window)

    # Calculate overall metrics
    total_operations = sum(s["count"] for s in all_stats.values())
    total_success = sum(s["success_count"] for s in all_stats.values())
    total_errors = sum(s["error_count"] for s in all_stats.values())
    total_cache_hits = sum(s["cache_hit_count"] for s in all_stats.values())

    # Count SLA violations
    sla_violations = [c for c in compliance if not c["compliant"]]

    return {
        "window": window,
        "timestamp": time.time(),
        "overall": {
            "total_operations": total_operations,
            "total_success": total_success,
            "total_errors": total_errors,
            "total_cache_hits": total_cache_hits,
            "overall_success_rate": round(total_success / total_operations, 4) if total_operations > 0 else 0.0,
            "overall_cache_hit_rate": round(total_cache_hits / total_operations, 4) if total_operations > 0 else 0.0,
            "sla_compliant_count": len(compliance) - len(sla_violations),
            "sla_violation_count": len(sla_violations),
        },
        "bots": all_stats,
        "sla_compliance": compliance,
    }
