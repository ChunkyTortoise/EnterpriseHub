"""
Jorge Bot Metrics Collector

Collects and aggregates operational metrics from bot interactions and
handoff events. Designed to be called inline from bot workflows with
minimal overhead. Accumulated metrics can be pushed to the AlertingService
for threshold evaluation.

Supports optional PostgreSQL persistence via a repository object so that
metrics survive process restarts.  When a repository is configured (via
``set_repository``), recorded interactions and handoffs are written through
to the database.  In-memory state is always authoritative; DB failures are
logged but never block the caller.

Usage:
    collector = BotMetricsCollector()
    collector.record_bot_interaction("lead", duration_ms=450.0, success=True, cache_hit=True)
    collector.record_handoff("lead", "buyer", success=True, duration_ms=120.0)
    summary = collector.get_bot_summary("lead")
    collector.feed_to_alerting(alerting_service)

    # Optional: enable DB persistence
    collector.set_repository(repo)
    await collector.load_from_db(since_minutes=60)
"""

import asyncio
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.jorge.telemetry import trace_operation

logger = logging.getLogger(__name__)

VALID_BOT_TYPES = frozenset({"lead", "buyer", "seller"})


@dataclass
class _BotInteraction:
    """A single bot interaction record."""

    bot_type: str
    duration_ms: float
    success: bool
    cache_hit: bool
    timestamp: float


@dataclass
class _HandoffRecord:
    """A single handoff event record."""

    source: str
    target: str
    success: bool
    duration_ms: float
    timestamp: float


class BotMetricsCollector:
    """Collects and aggregates bot operational metrics.

    Thread-safe, in-memory metrics collection that can feed aggregated
    values into the AlertingService for rule evaluation.
    """

    # ── Singleton ─────────────────────────────────────────────────────
    _instance: Optional["BotMetricsCollector"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "BotMetricsCollector":
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self) -> None:
        if self._initialized:
            return
        self._interactions: List[_BotInteraction] = []
        self._handoffs: List[_HandoffRecord] = []
        self._data_lock = threading.Lock()
        self._repository: Any = None  # Optional MetricsRepository for DB persistence
        self._initialized = True
        logger.info("BotMetricsCollector initialized")

    # ── Persistence Configuration ─────────────────────────────────────

    def set_repository(self, repository: Any) -> None:
        """Attach a repository for write-through PostgreSQL persistence.

        The repository object must implement:
            - ``save_interaction(bot_type, duration_ms, success, cache_hit, timestamp)``
              (async, returns None)
            - ``save_handoff(source, target, success, duration_ms, timestamp)``
              (async, returns None)
            - ``load_interactions(since_timestamp)``
              (async, returns list of dicts with keys matching _BotInteraction fields)
            - ``load_handoffs(since_timestamp)``
              (async, returns list of dicts with keys matching _HandoffRecord fields)

        Args:
            repository: A repository instance (or None to disable persistence).
        """
        self._repository = repository
        logger.info(
            "BotMetricsCollector persistence %s",
            "enabled" if repository else "disabled",
        )

    async def load_from_db(self, since_minutes: int = 60) -> int:
        """Hydrate in-memory metrics from the database.

        Loads interactions and handoffs recorded within the last
        ``since_minutes`` and merges them into in-memory storage,
        deduplicating by timestamp.

        Args:
            since_minutes: How far back to load (default 60 minutes).

        Returns:
            Total number of records loaded from DB.
        """
        if self._repository is None:
            return 0

        cutoff = time.time() - (since_minutes * 60)
        loaded = 0

        try:
            db_interactions = await self._repository.load_interactions(cutoff)
            existing_timestamps = {i.timestamp for i in self._interactions}
            for row in db_interactions:
                if row["timestamp"] not in existing_timestamps:
                    interaction = _BotInteraction(
                        bot_type=row["bot_type"],
                        duration_ms=row["duration_ms"],
                        success=row["success"],
                        cache_hit=row.get("cache_hit", False),
                        timestamp=row["timestamp"],
                    )
                    with self._data_lock:
                        self._interactions.append(interaction)
                    loaded += 1
        except Exception as exc:
            logger.warning("Failed to load interactions from DB: %s", exc)

        try:
            db_handoffs = await self._repository.load_handoffs(cutoff)
            existing_ho_timestamps = {h.timestamp for h in self._handoffs}
            for row in db_handoffs:
                if row["timestamp"] not in existing_ho_timestamps:
                    handoff = _HandoffRecord(
                        source=row["source"],
                        target=row["target"],
                        success=row["success"],
                        duration_ms=row["duration_ms"],
                        timestamp=row["timestamp"],
                    )
                    with self._data_lock:
                        self._handoffs.append(handoff)
                    loaded += 1
        except Exception as exc:
            logger.warning("Failed to load handoffs from DB: %s", exc)

        if loaded:
            logger.info("Loaded %d metric records from database", loaded)
        return loaded

    # ── Recording ─────────────────────────────────────────────────────

    @trace_operation("jorge.metrics", "record_bot_interaction")
    def record_bot_interaction(
        self,
        bot_type: str,
        duration_ms: float,
        success: bool,
        cache_hit: bool = False,
    ) -> None:
        """Record a single bot interaction.

        If a repository is configured, the interaction is also persisted
        to PostgreSQL (fire-and-forget; DB errors are logged, not raised).

        Args:
            bot_type: One of "lead", "buyer", "seller".
            duration_ms: Response time in milliseconds.
            success: Whether the interaction completed without error.
            cache_hit: Whether a cache hit contributed to the response.

        Raises:
            ValueError: If bot_type is not recognized.
        """
        if bot_type not in VALID_BOT_TYPES:
            raise ValueError(f"Invalid bot_type '{bot_type}'. Must be one of: {sorted(VALID_BOT_TYPES)}")

        interaction = _BotInteraction(
            bot_type=bot_type,
            duration_ms=duration_ms,
            success=success,
            cache_hit=cache_hit,
            timestamp=time.time(),
        )

        with self._data_lock:
            self._interactions.append(interaction)

        # Write-through to DB (fire-and-forget on error)
        if self._repository is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._persist_interaction(interaction))
                else:
                    loop.run_until_complete(self._persist_interaction(interaction))
            except RuntimeError:
                logger.debug("No event loop available for DB write-through of interaction")

        logger.debug(
            "Recorded %s bot interaction: %sms, success=%s, cache_hit=%s",
            bot_type,
            duration_ms,
            success,
            cache_hit,
        )

    @trace_operation("jorge.metrics", "record_handoff")
    def record_handoff(
        self,
        source: str,
        target: str,
        success: bool,
        duration_ms: float,
    ) -> None:
        """Record a cross-bot handoff event.

        If a repository is configured, the handoff is also persisted
        to PostgreSQL (fire-and-forget; DB errors are logged, not raised).

        Args:
            source: Source bot type (e.g. "lead").
            target: Target bot type (e.g. "buyer").
            success: Whether the handoff completed successfully.
            duration_ms: Handoff latency in milliseconds.
        """
        record = _HandoffRecord(
            source=source,
            target=target,
            success=success,
            duration_ms=duration_ms,
            timestamp=time.time(),
        )

        with self._data_lock:
            self._handoffs.append(record)

        # Write-through to DB (fire-and-forget on error)
        if self._repository is not None:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(self._persist_handoff(record))
                else:
                    loop.run_until_complete(self._persist_handoff(record))
            except RuntimeError:
                logger.debug("No event loop available for DB write-through of handoff")

        logger.debug(
            "Recorded handoff %s->%s: %sms, success=%s",
            source,
            target,
            duration_ms,
            success,
        )

    # ── Summaries ─────────────────────────────────────────────────────

    @trace_operation("jorge.metrics", "get_bot_summary")
    def get_bot_summary(self, bot_type: str, window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated metrics for a specific bot type.

        Args:
            bot_type: One of "lead", "buyer", "seller".
            window_minutes: How far back to look (default 60 minutes).

        Returns:
            Dict with total_interactions, success_rate, avg_duration_ms,
            p95_duration_ms, error_rate, and cache_hit_rate.

        Raises:
            ValueError: If bot_type is not recognized.
        """
        if bot_type not in VALID_BOT_TYPES:
            raise ValueError(f"Invalid bot_type '{bot_type}'. Must be one of: {sorted(VALID_BOT_TYPES)}")

        cutoff = time.time() - (window_minutes * 60)

        with self._data_lock:
            relevant = [i for i in self._interactions if i.bot_type == bot_type and i.timestamp >= cutoff]

        return self._compute_interaction_summary(relevant)

    @trace_operation("jorge.metrics", "get_system_summary")
    def get_system_summary(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get aggregated metrics across all bots.

        Args:
            window_minutes: How far back to look (default 60 minutes).

        Returns:
            Dict with per-bot summaries, handoff summary, and overall totals.
        """
        cutoff = time.time() - (window_minutes * 60)

        with self._data_lock:
            all_interactions = [i for i in self._interactions if i.timestamp >= cutoff]
            all_handoffs = [h for h in self._handoffs if h.timestamp >= cutoff]

        # Per-bot breakdown
        bots: Dict[str, Dict[str, Any]] = {}
        for bot_type in VALID_BOT_TYPES:
            bot_interactions = [i for i in all_interactions if i.bot_type == bot_type]
            bots[bot_type] = self._compute_interaction_summary(bot_interactions)

        # Handoff summary
        handoff_total = len(all_handoffs)
        handoff_successes = sum(1 for h in all_handoffs if h.success)
        handoff_durations = [h.duration_ms for h in all_handoffs]

        handoff_summary = {
            "total_handoffs": handoff_total,
            "success_rate": (round(handoff_successes / handoff_total, 4) if handoff_total > 0 else 0.0),
            "failure_rate": (round(1.0 - handoff_successes / handoff_total, 4) if handoff_total > 0 else 0.0),
            "avg_duration_ms": (
                round(sum(handoff_durations) / len(handoff_durations), 2) if handoff_durations else 0.0
            ),
            "p95_duration_ms": (self._percentile(handoff_durations, 95) if handoff_durations else 0.0),
        }

        # Overall totals
        overall = self._compute_interaction_summary(all_interactions)

        return {
            "bots": bots,
            "handoffs": handoff_summary,
            "overall": overall,
        }

    # ── Alerting Integration ──────────────────────────────────────────

    @trace_operation("jorge.metrics", "feed_to_alerting")
    def feed_to_alerting(self, alerting_service: Any) -> None:
        """Push current metric aggregates to the AlertingService.

        Computes summary metrics and records them in the alerting service
        so that threshold rules can be evaluated.

        Args:
            alerting_service: An AlertingService instance.
        """
        system = self.get_system_summary()

        # Overall error rate
        overall = system["overall"]
        alerting_service.record_metric("error_rate", overall["error_rate"])

        # Overall cache hit rate
        alerting_service.record_metric("cache_hit_rate", overall["cache_hit_rate"])

        # Per-bot response time p95
        bot_metric_map = {
            "lead": "lead_bot.response_time_p95",
            "buyer": "buyer_bot.response_time_p95",
            "seller": "seller_bot.response_time_p95",
        }
        for bot_type, metric_name in bot_metric_map.items():
            bot_summary = system["bots"].get(bot_type, {})
            p95 = bot_summary.get("p95_duration_ms", 0.0)
            alerting_service.record_metric(metric_name, p95)

        # Handoff metrics
        handoff = system["handoffs"]
        alerting_service.record_metric("handoff.response_time_p95", handoff["p95_duration_ms"])
        alerting_service.record_metric("handoff.failure_rate", handoff["failure_rate"])

        logger.info("Fed %d metrics to AlertingService", 7)

    # ── DB Write-Through Helpers ─────────────────────────────────────

    async def _persist_interaction(self, interaction: _BotInteraction) -> None:
        """Write a single interaction to the database repository."""
        try:
            await self._repository.save_interaction(
                bot_type=interaction.bot_type,
                duration_ms=interaction.duration_ms,
                success=interaction.success,
                cache_hit=interaction.cache_hit,
                timestamp=interaction.timestamp,
            )
        except Exception as exc:
            logger.debug("DB write-through failed for interaction: %s", exc)

    async def _persist_handoff(self, record: _HandoffRecord) -> None:
        """Write a single handoff record to the database repository."""
        try:
            await self._repository.save_handoff(
                source=record.source,
                target=record.target,
                success=record.success,
                duration_ms=record.duration_ms,
                timestamp=record.timestamp,
            )
        except Exception as exc:
            logger.debug("DB write-through failed for handoff: %s", exc)

    # ── Internal Helpers ──────────────────────────────────────────────

    @staticmethod
    def _compute_interaction_summary(
        interactions: List[_BotInteraction],
    ) -> Dict[str, Any]:
        """Compute aggregate statistics from a list of interactions.

        Args:
            interactions: List of _BotInteraction records.

        Returns:
            Dict with total_interactions, success_rate, avg_duration_ms,
            p95_duration_ms, error_rate, and cache_hit_rate.
        """
        total = len(interactions)
        if total == 0:
            return {
                "total_interactions": 0,
                "success_rate": 0.0,
                "avg_duration_ms": 0.0,
                "p95_duration_ms": 0.0,
                "error_rate": 0.0,
                "cache_hit_rate": 0.0,
            }

        successes = sum(1 for i in interactions if i.success)
        cache_hits = sum(1 for i in interactions if i.cache_hit)
        durations = [i.duration_ms for i in interactions]

        return {
            "total_interactions": total,
            "success_rate": round(successes / total, 4),
            "avg_duration_ms": round(sum(durations) / total, 2),
            "p95_duration_ms": BotMetricsCollector._percentile(durations, 95),
            "error_rate": round(1.0 - successes / total, 4),
            "cache_hit_rate": round(cache_hits / total, 4),
        }

    @staticmethod
    def _percentile(values: List[float], pct: int) -> float:
        """Compute the pct-th percentile of a list of values.

        Uses nearest-rank method.

        Args:
            values: List of numeric values.
            pct: Percentile to compute (0-100).

        Returns:
            The percentile value, or 0.0 if the list is empty.
        """
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = max(0, int(len(sorted_vals) * pct / 100) - 1)
        return round(sorted_vals[idx], 2)

    def last_interaction_time(self) -> float:
        """Return the timestamp of the most recent bot interaction.

        Returns:
            Unix timestamp of the last interaction, or current time if none recorded.
        """
        with self._data_lock:
            if self._interactions:
                return max(i.timestamp for i in self._interactions)
        return time.time()

    # ── Testing Support ───────────────────────────────────────────────

    @classmethod
    def reset(cls) -> None:
        """Reset singleton state. For testing only."""
        with cls._lock:
            if cls._instance is not None:
                cls._instance._interactions.clear()
                cls._instance._handoffs.clear()
                cls._instance._repository = None
                cls._instance._initialized = False
            cls._instance = None
