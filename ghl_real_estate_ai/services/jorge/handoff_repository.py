"""
Redis-backed repository for handoff outcome persistence.

Implements the interface expected by ``JorgeHandoffService.set_repository()``:
    - save_handoff_outcome(contact_id, source_bot, target_bot, outcome, timestamp, metadata)
    - load_handoff_outcomes(since_timestamp, source_bot=None, target_bot=None)

Also provides Redis-backed replacements for the in-memory handoff history
and lock dicts used by the handoff service for circular prevention and
conflict detection.
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Key prefixes
_OUTCOME_KEY = "handoff:outcomes:{route}"  # Redis list per route
_HISTORY_KEY = "handoff:history:{contact_id}"  # Sorted set (score=timestamp)
_LOCK_KEY = "handoff:lock:{contact_id}"  # String with TTL

# TTLs
_OUTCOME_TTL = 60 * 60 * 24 * 30  # 30 days
_HISTORY_TTL = 60 * 60 * 24 * 7  # 7 days
_LOCK_TTL = 30  # seconds (matches HANDOFF_LOCK_TIMEOUT)


class RedisHandoffRepository:
    """Redis-backed persistence for handoff outcomes, history, and locks.

    Falls back gracefully to in-memory operation when Redis is unavailable,
    logging warnings but never raising to callers.
    """

    def __init__(self, redis_url: Optional[str] = None, key_prefix: str = "jorge:"):
        self._redis_url = redis_url or os.getenv("REDIS_URL", "")
        self._prefix = key_prefix
        self._redis = None
        self._enabled = False

    # ── Lifecycle ─────────────────────────────────────────────────────

    async def initialize(self) -> bool:
        """Connect to Redis. Returns True if connection succeeds."""
        if not self._redis_url:
            logger.info("RedisHandoffRepository: No REDIS_URL, persistence disabled")
            return False

        try:
            import redis.asyncio as aioredis
            from redis.asyncio.connection import ConnectionPool

            pool = ConnectionPool.from_url(
                self._redis_url,
                max_connections=10,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=True,
            )
            self._redis = aioredis.Redis(connection_pool=pool)
            await self._redis.ping()
            self._enabled = True
            logger.info("RedisHandoffRepository: Connected to Redis")
            return True

        except ImportError:
            logger.warning("RedisHandoffRepository: redis package not installed")
            return False
        except Exception as exc:
            logger.warning("RedisHandoffRepository: Connection failed: %s", exc)
            return False

    async def close(self) -> None:
        """Shut down Redis connection pool."""
        if self._redis is not None:
            await self._redis.aclose()
            self._redis = None
            self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    # ── Key helpers ───────────────────────────────────────────────────

    def _key(self, template: str, **kwargs: str) -> str:
        return self._prefix + template.format(**kwargs)

    # ── Outcomes (required by set_repository interface) ────────────────

    async def save_handoff_outcome(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
        outcome: str,
        timestamp: float,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Persist a single handoff outcome record."""
        if not self._enabled:
            return

        route = f"{source_bot}->{target_bot}"
        key = self._key(_OUTCOME_KEY, route=route)
        record = json.dumps({
            "contact_id": contact_id,
            "source_bot": source_bot,
            "target_bot": target_bot,
            "outcome": outcome,
            "timestamp": timestamp,
            "metadata": metadata or {},
        })

        try:
            pipe = self._redis.pipeline()
            pipe.lpush(key, record)
            pipe.ltrim(key, 0, 999)  # cap at 1000 per route
            pipe.expire(key, _OUTCOME_TTL)
            await pipe.execute()
        except Exception as exc:
            logger.warning("RedisHandoffRepository: save_handoff_outcome failed: %s", exc)

    async def load_handoff_outcomes(
        self,
        since_timestamp: float,
        source_bot: Optional[str] = None,
        target_bot: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Load outcome records newer than since_timestamp.

        Returns list of dicts with keys:
            contact_id, source_bot, target_bot, outcome, timestamp, metadata
        """
        if not self._enabled:
            return []

        try:
            # Discover all outcome keys
            pattern = self._key(_OUTCOME_KEY, route="*")
            keys = []
            async for key in self._redis.scan_iter(match=pattern, count=100):
                keys.append(key)

            results: List[Dict[str, Any]] = []
            for key in keys:
                raw_items = await self._redis.lrange(key, 0, -1)
                for raw in raw_items:
                    try:
                        record = json.loads(raw)
                    except (json.JSONDecodeError, TypeError):
                        continue

                    if record.get("timestamp", 0) < since_timestamp:
                        continue
                    if source_bot and record.get("source_bot") != source_bot:
                        continue
                    if target_bot and record.get("target_bot") != target_bot:
                        continue
                    results.append(record)

            return results

        except Exception as exc:
            logger.warning("RedisHandoffRepository: load_handoff_outcomes failed: %s", exc)
            return []

    # ── History (circular prevention) ─────────────────────────────────

    async def record_handoff_history(
        self,
        contact_id: str,
        source_bot: str,
        target_bot: str,
    ) -> None:
        """Record a handoff event for circular-prevention checks."""
        if not self._enabled:
            return

        key = self._key(_HISTORY_KEY, contact_id=contact_id)
        entry = json.dumps({"from": source_bot, "to": target_bot})
        now = time.time()

        try:
            pipe = self._redis.pipeline()
            pipe.zadd(key, {entry: now})
            pipe.expire(key, _HISTORY_TTL)
            await pipe.execute()
        except Exception as exc:
            logger.warning("RedisHandoffRepository: record_handoff_history failed: %s", exc)

    async def get_handoff_history(
        self,
        contact_id: str,
        since: float = 0,
    ) -> List[Dict[str, Any]]:
        """Get handoff history entries for a contact since a timestamp."""
        if not self._enabled:
            return []

        key = self._key(_HISTORY_KEY, contact_id=contact_id)

        try:
            entries = await self._redis.zrangebyscore(key, since, "+inf", withscores=True)
            results = []
            for entry_json, score in entries:
                try:
                    entry = json.loads(entry_json)
                    entry["timestamp"] = score
                    results.append(entry)
                except (json.JSONDecodeError, TypeError):
                    continue
            return results
        except Exception as exc:
            logger.warning("RedisHandoffRepository: get_handoff_history failed: %s", exc)
            return []

    # ── Locks (conflict detection) ────────────────────────────────────

    async def acquire_lock(self, contact_id: str, ttl: int = _LOCK_TTL) -> bool:
        """Try to acquire a handoff lock. Returns True if acquired."""
        if not self._enabled:
            return True  # permissive fallback

        key = self._key(_LOCK_KEY, contact_id=contact_id)
        try:
            acquired = await self._redis.set(key, "1", nx=True, ex=ttl)
            return bool(acquired)
        except Exception as exc:
            logger.warning("RedisHandoffRepository: acquire_lock failed: %s", exc)
            return True  # permissive fallback

    async def release_lock(self, contact_id: str) -> None:
        """Release a handoff lock."""
        if not self._enabled:
            return

        key = self._key(_LOCK_KEY, contact_id=contact_id)
        try:
            await self._redis.delete(key)
        except Exception as exc:
            logger.warning("RedisHandoffRepository: release_lock failed: %s", exc)

    # ── Health ────────────────────────────────────────────────────────

    async def health_check(self) -> Dict[str, Any]:
        """Return health status for monitoring."""
        if not self._enabled:
            return {"status": "disabled", "connected": False}

        try:
            await self._redis.ping()
            return {"status": "healthy", "connected": True}
        except Exception as exc:
            return {"status": "unhealthy", "connected": False, "error": str(exc)}
