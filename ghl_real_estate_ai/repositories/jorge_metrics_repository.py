"""Async CRUD repository for Jorge bot metrics persistence.

Uses raw SQL with parameterized queries (asyncpg style).  All write
operations are fire-and-forget safe: database failures are logged but
never raised to callers so that in-memory operation is never blocked.

Tables managed:
    - jorge_bot_interactions
    - jorge_handoff_events
    - jorge_performance_operations
    - jorge_alert_rules
    - jorge_alerts

Usage:
    repo = JorgeMetricsRepository(dsn="postgresql://...")
    await repo.save_interaction("lead", 450.0, True, True, time.time())
    rows = await repo.load_interactions(since_timestamp=cutoff)
"""

import json
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class JorgeMetricsRepository:
    """Async CRUD repository for Jorge bot metrics tables.

    All public methods catch and log database exceptions internally so
    that callers (BotMetricsCollector, PerformanceTracker, AlertingService)
    are never blocked by persistence failures.
    """

    def __init__(self, dsn: str) -> None:
        """Initialize with a PostgreSQL DSN.

        Args:
            dsn: PostgreSQL connection string, e.g. ``postgresql://user:pass@host/db``.
        """
        self._dsn = dsn
        self._pool: Any = None  # asyncpg.Pool, lazily created
        logger.info("JorgeMetricsRepository initialized (dsn=%s...)", dsn[:30] if dsn else "")

    async def _get_pool(self) -> Any:
        """Lazily create and return the asyncpg connection pool."""
        if self._pool is None:
            try:
                import asyncpg

                self._pool = await asyncpg.create_pool(self._dsn, min_size=1, max_size=5)
            except Exception as exc:
                logger.error("Failed to create asyncpg pool: %s", exc)
                raise
        return self._pool

    # ── Bot Interactions ──────────────────────────────────────────────

    async def save_interaction(
        self,
        bot_type: str,
        duration_ms: float,
        success: bool,
        cache_hit: bool,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a bot interaction record.

        Args:
            bot_type: One of "lead", "buyer", "seller".
            duration_ms: Response latency in milliseconds.
            success: Whether the interaction succeeded.
            cache_hit: Whether a cache hit contributed.
            timestamp: Unix timestamp of the interaction.
            metadata: Optional JSON metadata.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_bot_interactions
                    (bot_type, duration_ms, success, cache_hit, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                bot_type,
                duration_ms,
                success,
                cache_hit,
                timestamp,
                json.dumps(metadata) if metadata else None,
            )
        except Exception as exc:
            logger.warning("Failed to save interaction: %s", exc)

    async def load_interactions(self, since_timestamp: float) -> List[Dict[str, Any]]:
        """Load interactions recorded since a Unix timestamp.

        Args:
            since_timestamp: Unix timestamp cutoff.

        Returns:
            List of dicts with keys: bot_type, duration_ms, success, cache_hit, timestamp.
        """
        try:
            pool = await self._get_pool()
            rows = await pool.fetch(
                """
                SELECT bot_type, duration_ms, success, cache_hit, timestamp, metadata
                FROM jorge_bot_interactions
                WHERE timestamp >= $1
                ORDER BY timestamp ASC
                """,
                since_timestamp,
            )
            return [
                {
                    "bot_type": r["bot_type"],
                    "duration_ms": r["duration_ms"],
                    "success": r["success"],
                    "cache_hit": r["cache_hit"],
                    "timestamp": r["timestamp"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load interactions: %s", exc)
            return []

    # ── Handoff Events ────────────────────────────────────────────────

    async def save_handoff(
        self,
        source: str,
        target: str,
        success: bool,
        duration_ms: float,
        timestamp: float,
    ) -> None:
        """Insert a handoff event record.

        Args:
            source: Source bot type.
            target: Target bot type.
            success: Whether the handoff succeeded.
            duration_ms: Handoff latency in milliseconds.
            timestamp: Unix timestamp of the handoff.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_handoff_events
                    (source_bot, target_bot, success, duration_ms, timestamp)
                VALUES ($1, $2, $3, $4, $5)
                """,
                source,
                target,
                success,
                duration_ms,
                timestamp,
            )
        except Exception as exc:
            logger.warning("Failed to save handoff: %s", exc)

    async def load_handoffs(self, since_timestamp: float) -> List[Dict[str, Any]]:
        """Load handoff events since a Unix timestamp.

        Args:
            since_timestamp: Unix timestamp cutoff.

        Returns:
            List of dicts with keys: source, target, success, duration_ms, timestamp.
        """
        try:
            pool = await self._get_pool()
            rows = await pool.fetch(
                """
                SELECT source_bot, target_bot, success, duration_ms, timestamp
                FROM jorge_handoff_events
                WHERE timestamp >= $1
                ORDER BY timestamp ASC
                """,
                since_timestamp,
            )
            return [
                {
                    "source": r["source_bot"],
                    "target": r["target_bot"],
                    "success": r["success"],
                    "duration_ms": r["duration_ms"],
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load handoffs: %s", exc)
            return []

    # ── Performance Operations ────────────────────────────────────────

    async def save_performance_operation(
        self,
        bot_name: str,
        operation: str,
        duration_ms: float,
        success: bool,
        cache_hit: bool,
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[float] = None,
    ) -> None:
        """Insert a performance operation record.

        Args:
            bot_name: Bot name (e.g., "lead_bot").
            operation: Operation name (e.g., "qualify").
            duration_ms: Duration in milliseconds.
            success: Whether the operation succeeded.
            cache_hit: Whether a cache hit contributed.
            metadata: Optional JSON metadata.
            timestamp: Unix timestamp (defaults to now).
        """
        ts = timestamp if timestamp is not None else time.time()
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_performance_operations
                    (bot_name, operation, duration_ms, success, cache_hit, metadata, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
                """,
                bot_name,
                operation,
                duration_ms,
                success,
                cache_hit,
                json.dumps(metadata) if metadata else None,
                ts,
            )
        except Exception as exc:
            logger.warning("Failed to save performance operation: %s", exc)

    async def load_performance_operations(self, since_timestamp: float) -> List[Dict[str, Any]]:
        """Load performance operations since a Unix timestamp.

        Args:
            since_timestamp: Unix timestamp cutoff.

        Returns:
            List of dicts with keys matching JorgePerformanceOperationDB fields.
        """
        try:
            pool = await self._get_pool()
            rows = await pool.fetch(
                """
                SELECT bot_name, operation, duration_ms, success, cache_hit,
                       metadata, timestamp
                FROM jorge_performance_operations
                WHERE timestamp >= $1
                ORDER BY timestamp ASC
                """,
                since_timestamp,
            )
            return [
                {
                    "bot_name": r["bot_name"],
                    "operation": r["operation"],
                    "duration_ms": r["duration_ms"],
                    "success": r["success"],
                    "cache_hit": r["cache_hit"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
                    "timestamp": r["timestamp"],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load performance operations: %s", exc)
            return []

    # ── Alerts ────────────────────────────────────────────────────────

    async def save_alert(
        self,
        rule_name: str,
        severity: str,
        message: str,
        triggered_at: float,
        performance_stats: Optional[Dict[str, Any]] = None,
        channels_sent: Optional[List[str]] = None,
    ) -> None:
        """Insert an alert record.

        Args:
            rule_name: Name of the rule that triggered the alert.
            severity: Alert severity ("critical", "warning", "info").
            message: Alert message text.
            triggered_at: Unix timestamp when the alert fired.
            performance_stats: Snapshot of performance stats at alert time.
            channels_sent: List of notification channels used.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_alerts
                    (rule_name, severity, message, triggered_at,
                     performance_stats, channels_sent)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                rule_name,
                severity,
                message,
                triggered_at,
                json.dumps(performance_stats) if performance_stats else None,
                json.dumps(channels_sent) if channels_sent else None,
            )
        except Exception as exc:
            logger.warning("Failed to save alert: %s", exc)

    async def load_alerts(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Load recent alerts, most recent first.

        Args:
            limit: Maximum number of alerts to return.

        Returns:
            List of alert dicts.
        """
        try:
            pool = await self._get_pool()
            rows = await pool.fetch(
                """
                SELECT id, rule_name, severity, message, triggered_at,
                       performance_stats, channels_sent,
                       acknowledged, acknowledged_at, acknowledged_by
                FROM jorge_alerts
                ORDER BY triggered_at DESC
                LIMIT $1
                """,
                limit,
            )
            return [
                {
                    "id": r["id"],
                    "rule_name": r["rule_name"],
                    "severity": r["severity"],
                    "message": r["message"],
                    "triggered_at": r["triggered_at"],
                    "performance_stats": (
                        json.loads(r["performance_stats"]) if r["performance_stats"] else None
                    ),
                    "channels_sent": (
                        json.loads(r["channels_sent"]) if r["channels_sent"] else None
                    ),
                    "acknowledged": r["acknowledged"],
                    "acknowledged_at": r["acknowledged_at"],
                    "acknowledged_by": r["acknowledged_by"],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load alerts: %s", exc)
            return []

    async def acknowledge_alert_db(self, alert_id: int, acknowledged_by: str) -> Dict[str, Any]:
        """Acknowledge an alert in the database.

        Args:
            alert_id: Primary key of the alert row.
            acknowledged_by: Identifier of who acknowledged.

        Returns:
            Dict with alert_id, acknowledged, acknowledged_at, acknowledged_by.
            Empty dict on failure.
        """
        now = time.time()
        try:
            pool = await self._get_pool()
            row = await pool.fetchrow(
                """
                UPDATE jorge_alerts
                SET acknowledged = TRUE,
                    acknowledged_at = $1,
                    acknowledged_by = $2
                WHERE id = $3
                RETURNING id, acknowledged, acknowledged_at, acknowledged_by
                """,
                now,
                acknowledged_by,
                alert_id,
            )
            if row:
                return {
                    "alert_id": row["id"],
                    "acknowledged": row["acknowledged"],
                    "acknowledged_at": row["acknowledged_at"],
                    "acknowledged_by": row["acknowledged_by"],
                }
            logger.warning("Alert %d not found for acknowledgment", alert_id)
            return {}
        except Exception as exc:
            logger.warning("Failed to acknowledge alert %d: %s", alert_id, exc)
            return {}

    # ── Alert Rules ───────────────────────────────────────────────────

    async def save_alert_rule(
        self,
        name: str,
        condition_config: Dict[str, Any],
        severity: str,
        cooldown_seconds: int,
        channels: List[str],
        description: str = "",
    ) -> None:
        """Upsert an alert rule (INSERT ON CONFLICT UPDATE).

        Args:
            name: Unique rule name.
            condition_config: JSON-serializable condition configuration.
            severity: Alert severity.
            cooldown_seconds: Minimum seconds between alerts.
            channels: Notification channels list.
            description: Human-readable description.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_alert_rules
                    (name, condition_config, severity, cooldown_seconds,
                     channels, description)
                VALUES ($1, $2, $3, $4, $5, $6)
                ON CONFLICT (name) DO UPDATE SET
                    condition_config = EXCLUDED.condition_config,
                    severity = EXCLUDED.severity,
                    cooldown_seconds = EXCLUDED.cooldown_seconds,
                    channels = EXCLUDED.channels,
                    description = EXCLUDED.description,
                    updated_at = NOW()
                """,
                name,
                json.dumps(condition_config),
                severity,
                cooldown_seconds,
                json.dumps(channels),
                description,
            )
        except Exception as exc:
            logger.warning("Failed to save alert rule '%s': %s", name, exc)

    async def load_alert_rules(self) -> List[Dict[str, Any]]:
        """Load all active alert rules.

        Returns:
            List of alert rule dicts.
        """
        try:
            pool = await self._get_pool()
            rows = await pool.fetch(
                """
                SELECT id, name, condition_config, severity, cooldown_seconds,
                       channels, description, active
                FROM jorge_alert_rules
                WHERE active = TRUE
                ORDER BY name ASC
                """
            )
            return [
                {
                    "id": r["id"],
                    "name": r["name"],
                    "condition_config": (
                        json.loads(r["condition_config"]) if r["condition_config"] else {}
                    ),
                    "severity": r["severity"],
                    "cooldown_seconds": r["cooldown_seconds"],
                    "channels": json.loads(r["channels"]) if r["channels"] else [],
                    "description": r["description"],
                    "active": r["active"],
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load alert rules: %s", exc)
            return []

    async def toggle_alert_rule(self, name: str, active: bool) -> None:
        """Enable or disable an alert rule by name.

        Args:
            name: The rule name.
            active: True to enable, False to disable.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                UPDATE jorge_alert_rules
                SET active = $1, updated_at = NOW()
                WHERE name = $2
                """,
                active,
                name,
            )
        except Exception as exc:
            logger.warning("Failed to toggle alert rule '%s': %s", name, exc)

    # ── Handoff Outcomes ─────────────────────────────────────────────

    async def save_handoff_outcome(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        outcome: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Insert a handoff outcome record.

        Args:
            contact_id: The contact that was handed off.
            source_bot: Bot that initiated the handoff.
            target_bot: Bot that received the handoff.
            outcome: One of "successful", "failed", "reverted", "timeout".
            timestamp: Unix timestamp of the outcome.
            metadata: Optional JSON metadata.
        """
        try:
            pool = await self._get_pool()
            await pool.execute(
                """
                INSERT INTO jorge_handoff_outcomes
                    (contact_id, source_bot, target_bot, outcome, timestamp, metadata)
                VALUES ($1, $2, $3, $4, $5, $6)
                """,
                contact_id,
                source_bot,
                target_bot,
                outcome,
                timestamp,
                json.dumps(metadata) if metadata else None,
            )
        except Exception as exc:
            logger.warning("Failed to save handoff outcome: %s", exc)

    async def load_handoff_outcomes(
        self,
        since_timestamp: float,
        source_bot: Optional[str] = None,
        target_bot: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load handoff outcomes since a Unix timestamp.

        Args:
            since_timestamp: Unix timestamp cutoff.
            source_bot: Optional filter by source bot.
            target_bot: Optional filter by target bot.

        Returns:
            List of dicts with keys: contact_id, source_bot, target_bot,
            outcome, timestamp, metadata.
        """
        try:
            pool = await self._get_pool()
            query = """
                SELECT contact_id, source_bot, target_bot, outcome,
                       timestamp, metadata
                FROM jorge_handoff_outcomes
                WHERE timestamp >= $1
            """
            params: list = [since_timestamp]
            idx = 2

            if source_bot is not None:
                query += f" AND source_bot = ${idx}"
                params.append(source_bot)
                idx += 1

            if target_bot is not None:
                query += f" AND target_bot = ${idx}"
                params.append(target_bot)

            query += " ORDER BY timestamp ASC"

            rows = await pool.fetch(query, *params)
            return [
                {
                    "contact_id": r["contact_id"],
                    "source_bot": r["source_bot"],
                    "target_bot": r["target_bot"],
                    "outcome": r["outcome"],
                    "timestamp": r["timestamp"],
                    "metadata": json.loads(r["metadata"]) if r["metadata"] else None,
                }
                for r in rows
            ]
        except Exception as exc:
            logger.warning("Failed to load handoff outcomes: %s", exc)
            return []

    # ── Cleanup ───────────────────────────────────────────────────────

    async def close(self) -> None:
        """Close the connection pool."""
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
