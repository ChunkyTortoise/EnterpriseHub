"""Tests for RedisHandoffRepository.

Uses fakeredis for isolated, fast unit tests without a real Redis server.
"""

import json
import time

import pytest

from ghl_real_estate_ai.services.jorge.handoff_repository import (
    _HISTORY_TTL,
    _LOCK_TTL,
    _OUTCOME_TTL,
    RedisHandoffRepository,
)

# ── Helpers ───────────────────────────────────────────────────────────


class FakeRedis:
    """Minimal async Redis fake for testing (subset of redis.asyncio API)."""

    def __init__(self):
        self._data: dict = {}
        self._expiries: dict = {}
        self._types: dict = {}  # key -> "string"|"list"|"zset"

    async def ping(self):
        return True

    async def aclose(self):
        pass

    # ── String ops ────────────────────────────────────────────────────

    async def set(self, key, value, nx=False, ex=None):
        if nx and key in self._data:
            return None
        self._data[key] = value
        if ex:
            self._expiries[key] = time.time() + ex
        self._types[key] = "string"
        return True

    async def get(self, key):
        return self._data.get(key)

    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
            self._expiries.pop(key, None)
            self._types.pop(key, None)
        return len(keys)

    # ── List ops ──────────────────────────────────────────────────────

    async def lpush(self, key, *values):
        if key not in self._data:
            self._data[key] = []
            self._types[key] = "list"
        for v in values:
            self._data[key].insert(0, v)
        return len(self._data[key])

    async def ltrim(self, key, start, stop):
        if key in self._data:
            self._data[key] = self._data[key][start : stop + 1]
        return True

    async def lrange(self, key, start, stop):
        if key not in self._data:
            return []
        if stop == -1:
            return self._data[key][start:]
        return self._data[key][start : stop + 1]

    async def expire(self, key, seconds):
        self._expiries[key] = time.time() + seconds
        return True

    # ── Sorted set ops ────────────────────────────────────────────────

    async def zadd(self, key, mapping):
        if key not in self._data:
            self._data[key] = {}
            self._types[key] = "zset"
        self._data[key].update(mapping)
        return len(mapping)

    async def zrangebyscore(self, key, min_score, max_score, withscores=False):
        if key not in self._data:
            return []
        items = self._data[key]
        max_val = float("inf") if max_score == "+inf" else float(max_score)
        min_val = float(min_score)
        results = [(member, score) for member, score in items.items() if min_val <= score <= max_val]
        results.sort(key=lambda x: x[1])
        if withscores:
            return results
        return [member for member, _ in results]

    # ── Scan ──────────────────────────────────────────────────────────

    async def scan_iter(self, match=None, count=100):
        import fnmatch

        for key in list(self._data.keys()):
            if match is None or fnmatch.fnmatch(key, match):
                yield key

    # ── Pipeline ──────────────────────────────────────────────────────

    def pipeline(self):
        return FakePipeline(self)


class FakePipeline:
    """Minimal pipeline that buffers and executes in order."""

    def __init__(self, redis: FakeRedis):
        self._redis = redis
        self._ops = []

    def lpush(self, key, *values):
        self._ops.append(("lpush", key, values))
        return self

    def ltrim(self, key, start, stop):
        self._ops.append(("ltrim", key, start, stop))
        return self

    def expire(self, key, seconds):
        self._ops.append(("expire", key, seconds))
        return self

    def zadd(self, key, mapping):
        self._ops.append(("zadd", key, mapping))
        return self

    async def execute(self):
        results = []
        for op in self._ops:
            if op[0] == "lpush":
                r = await self._redis.lpush(op[1], *op[2])
            elif op[0] == "ltrim":
                r = await self._redis.ltrim(op[1], op[2], op[3])
            elif op[0] == "expire":
                r = await self._redis.expire(op[1], op[2])
            elif op[0] == "zadd":
                r = await self._redis.zadd(op[1], op[2])
            else:
                r = None
            results.append(r)
        self._ops.clear()
        return results


def _make_repo() -> RedisHandoffRepository:
    """Create a repository with a fake Redis backend."""
    repo = RedisHandoffRepository(redis_url="redis://fake:6379")
    repo._redis = FakeRedis()
    repo._enabled = True
    return repo


# ── Tests ─────────────────────────────────────────────────────────────


class TestSaveAndLoadOutcomes:
    """Tests for the outcome persistence interface (set_repository contract)."""

    @pytest.mark.asyncio
    async def test_save_and_load_round_trip(self):
        repo = _make_repo()
        now = time.time()
        await repo.save_handoff_outcome(
            contact_id="c1",
            source_bot="lead",
            target_bot="buyer",
            outcome="accepted",
            timestamp=now,
            metadata={"confidence": 0.85},
        )

        results = await repo.load_handoff_outcomes(since_timestamp=now - 60)
        assert len(results) == 1
        assert results[0]["contact_id"] == "c1"
        assert results[0]["source_bot"] == "lead"
        assert results[0]["target_bot"] == "buyer"
        assert results[0]["outcome"] == "accepted"
        assert results[0]["metadata"]["confidence"] == 0.85

    @pytest.mark.asyncio
    async def test_load_filters_by_timestamp(self):
        repo = _make_repo()
        old_ts = time.time() - 3600
        new_ts = time.time()

        await repo.save_handoff_outcome("c1", "lead", "buyer", "accepted", old_ts)
        await repo.save_handoff_outcome("c2", "lead", "seller", "accepted", new_ts)

        results = await repo.load_handoff_outcomes(since_timestamp=new_ts - 10)
        assert len(results) == 1
        assert results[0]["contact_id"] == "c2"

    @pytest.mark.asyncio
    async def test_load_filters_by_source_bot(self):
        repo = _make_repo()
        now = time.time()
        await repo.save_handoff_outcome("c1", "lead", "buyer", "accepted", now)
        await repo.save_handoff_outcome("c2", "seller", "lead", "rejected", now)

        results = await repo.load_handoff_outcomes(since_timestamp=now - 60, source_bot="lead")
        assert len(results) == 1
        assert results[0]["contact_id"] == "c1"

    @pytest.mark.asyncio
    async def test_load_returns_empty_when_disabled(self):
        repo = _make_repo()
        repo._enabled = False
        results = await repo.load_handoff_outcomes(since_timestamp=0)
        assert results == []

    @pytest.mark.asyncio
    async def test_save_noop_when_disabled(self):
        repo = _make_repo()
        repo._enabled = False
        # Should not raise
        await repo.save_handoff_outcome("c1", "lead", "buyer", "ok", time.time())


class TestHandoffHistory:
    """Tests for circular-prevention history (sorted sets)."""

    @pytest.mark.asyncio
    async def test_record_and_retrieve_history(self):
        repo = _make_repo()
        await repo.record_handoff_history("c1", "lead", "buyer")
        entries = await repo.get_handoff_history("c1")
        assert len(entries) == 1
        assert entries[0]["from"] == "lead"
        assert entries[0]["to"] == "buyer"
        assert "timestamp" in entries[0]

    @pytest.mark.asyncio
    async def test_history_filters_by_since(self):
        repo = _make_repo()
        # Record with old timestamp by manipulating the sorted set directly
        key = repo._key("handoff:history:{contact_id}", contact_id="c1")
        old_entry = json.dumps({"from": "lead", "to": "buyer"})
        await repo._redis.zadd(key, {old_entry: time.time() - 7200})

        await repo.record_handoff_history("c1", "seller", "lead")

        recent = await repo.get_handoff_history("c1", since=time.time() - 60)
        assert len(recent) == 1
        assert recent[0]["from"] == "seller"

    @pytest.mark.asyncio
    async def test_history_empty_for_unknown_contact(self):
        repo = _make_repo()
        entries = await repo.get_handoff_history("unknown_contact")
        assert entries == []


class TestLocks:
    """Tests for handoff conflict detection (Redis SET NX)."""

    @pytest.mark.asyncio
    async def test_acquire_and_release(self):
        repo = _make_repo()
        assert await repo.acquire_lock("c1") is True
        # Second acquire should fail (NX)
        assert await repo.acquire_lock("c1") is False
        # Release and reacquire
        await repo.release_lock("c1")
        assert await repo.acquire_lock("c1") is True

    @pytest.mark.asyncio
    async def test_lock_permissive_when_disabled(self):
        repo = _make_repo()
        repo._enabled = False
        assert await repo.acquire_lock("c1") is True


class TestHealthAndLifecycle:
    """Tests for health check and connection lifecycle."""

    @pytest.mark.asyncio
    async def test_health_check_when_enabled(self):
        repo = _make_repo()
        health = await repo.health_check()
        assert health["status"] == "healthy"
        assert health["connected"] is True

    @pytest.mark.asyncio
    async def test_health_check_when_disabled(self):
        repo = _make_repo()
        repo._enabled = False
        health = await repo.health_check()
        assert health["status"] == "disabled"
        assert health["connected"] is False

    @pytest.mark.asyncio
    async def test_close_resets_state(self):
        repo = _make_repo()
        assert repo.enabled is True
        await repo.close()
        assert repo.enabled is False
        assert repo._redis is None

    @pytest.mark.asyncio
    async def test_initialize_without_url_returns_false(self, monkeypatch):
        monkeypatch.delenv("REDIS_URL", raising=False)
        repo = RedisHandoffRepository(redis_url="")
        result = await repo.initialize()
        assert result is False
        assert repo.enabled is False
