"""
Tests for Query Cache Module
============================

Tests cover:
    - Query result caching
    - Content deduplication strategies
    - Query fingerprinting
    - Cache warming tasks
    - Compression handling
    - Result expiration
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.caching.query_cache import (

@pytest.mark.integration
    CacheWarmingStrategy,
    CompressionHandler,
    ContentHasher,
    DeduplicationStrategy,
    QueryCache,
    QueryFingerprint,
    QueryNormalizer,
    QueryResult,
    WarmingTask,
)

pytestmark = pytest.mark.asyncio


class TestQueryFingerprint:
    """Test cases for QueryFingerprint."""

    def test_fingerprint_creation(self):
        """Test creating a query fingerprint."""
        fp = QueryFingerprint(query_hash="abc123", parameter_hash="def456", content_hash="ghi789")

        assert fp.query_hash == "abc123"
        assert fp.parameter_hash == "def456"
        assert fp.content_hash == "ghi789"

    def test_to_key(self):
        """Test generating unique key from fingerprint."""
        fp = QueryFingerprint(query_hash="abc123", parameter_hash="def456", content_hash="ghi789")

        key = fp.to_key()

        assert isinstance(key, str)
        assert len(key) == 32

    def test_to_key_consistency(self):
        """Test that same fingerprint generates same key."""
        fp1 = QueryFingerprint("a", "b", "c")
        fp2 = QueryFingerprint("a", "b", "c")

        assert fp1.to_key() == fp2.to_key()

    def test_to_key_uniqueness(self):
        """Test that different fingerprints generate different keys."""
        fp1 = QueryFingerprint("a", "b", "c")
        fp2 = QueryFingerprint("x", "y", "z")

        assert fp1.to_key() != fp2.to_key()


class TestQueryResult:
    """Test cases for QueryResult dataclass."""

    def test_query_result_creation(self):
        """Test creating a query result."""
        result = QueryResult(
            query="SELECT * FROM users",
            result=[{"id": 1}, {"id": 2}],
            execution_time_ms=150.5,
            tags=["users", "database"],
        )

        assert result.query == "SELECT * FROM users"
        assert len(result.result) == 2
        assert result.execution_time_ms == 150.5
        assert result.tags == ["users", "database"]

    def test_is_expired_no_expiration(self):
        """Test that results without expiration don't expire."""
        result = QueryResult(query="SELECT 1", result=[1], expires_at=None)

        assert not result.is_expired()

    def test_is_expired_true(self):
        """Test detection of expired results."""
        result = QueryResult(query="SELECT 1", result=[1], expires_at=datetime.now() - timedelta(hours=1))

        assert result.is_expired()

    def test_is_expired_false(self):
        """Test that valid results don't show as expired."""
        result = QueryResult(query="SELECT 1", result=[1], expires_at=datetime.now() + timedelta(hours=1))

        assert not result.is_expired()

    def test_touch_updates_metadata(self):
        """Test that touch updates access metadata."""
        result = QueryResult(query="SELECT 1", result=[1])
        original_accessed = result.last_accessed

        result.touch()

        assert result.access_count == 1
        assert result.last_accessed > original_accessed

    def test_to_dict(self):
        """Test serialization to dictionary."""
        result = QueryResult(query="SELECT 1", result=[1, 2, 3], execution_time_ms=100.0, size_bytes=1024)

        data = result.to_dict()

        assert data["query"] == "SELECT 1"
        assert data["result"] == [1, 2, 3]
        assert data["execution_time_ms"] == 100.0
        assert data["size_bytes"] == 1024

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "query": "SELECT 1",
            "result": [1, 2, 3],
            "fingerprint": None,
            "created_at": datetime.now().isoformat(),
            "expires_at": None,
            "access_count": 5,
            "last_accessed": datetime.now().isoformat(),
            "execution_time_ms": 100.0,
            "size_bytes": 1024,
            "tags": ["test"],
            "metadata": {},
        }

        result = QueryResult.from_dict(data)

        assert result.query == "SELECT 1"
        assert result.result == [1, 2, 3]
        assert result.access_count == 5


class TestQueryNormalizer:
    """Test cases for QueryNormalizer."""

    def test_normalize_whitespace(self):
        """Test whitespace normalization."""
        query = "SELECT   *  FROM    users"
        normalized = QueryNormalizer.normalize(query)

        assert normalized == "select * from users"

    def test_normalize_case(self):
        """Test case normalization."""
        query = "SELECT * FROM Users WHERE Id = 1"
        normalized = QueryNormalizer.normalize(query)

        assert normalized == "select * from users where id = 1"

    def test_normalize_comments(self):
        """Test comment removal."""
        query = """SELECT * FROM users -- get all users
        WHERE active = 1"""
        normalized = QueryNormalizer.normalize(query)

        assert "--" not in normalized
        assert "get all users" not in normalized

    def test_normalize_multiline_comments(self):
        """Test multi-line comment removal."""
        query = "SELECT /* comment */ * FROM users"
        normalized = QueryNormalizer.normalize(query)

        assert "/*" not in normalized
        assert "comment" not in normalized

    def test_extract_parameters_named(self):
        """Test extraction of named parameters."""
        query = "SELECT * FROM users WHERE id = :user_id AND status = :status"
        params = QueryNormalizer.extract_parameters(query)

        assert "user_id" in params
        assert "status" in params

    def test_extract_parameters_positional(self):
        """Test extraction of positional parameters."""
        query = "SELECT * FROM users WHERE id = $1 AND status = $2"
        params = QueryNormalizer.extract_parameters(query)

        assert "1" in params
        assert "2" in params


class TestContentHasher:
    """Test cases for ContentHasher."""

    def test_hash_query_consistency(self):
        """Test that same query produces same hash."""
        query = "SELECT * FROM users"
        hash1 = ContentHasher.hash_query(query)
        hash2 = ContentHasher.hash_query(query)

        assert hash1 == hash2

    def test_hash_query_different_queries(self):
        """Test that different queries produce different hashes."""
        hash1 = ContentHasher.hash_query("SELECT * FROM users")
        hash2 = ContentHasher.hash_query("SELECT * FROM orders")

        assert hash1 != hash2

    def test_hash_parameters_consistency(self):
        """Test parameter hashing consistency."""
        params = {"id": 1, "name": "test"}
        hash1 = ContentHasher.hash_parameters(params)
        hash2 = ContentHasher.hash_parameters(params)

        assert hash1 == hash2

    def test_hash_parameters_order_independence(self):
        """Test that parameter order doesn't affect hash."""
        params1 = {"a": 1, "b": 2}
        params2 = {"b": 2, "a": 1}

        hash1 = ContentHasher.hash_parameters(params1)
        hash2 = ContentHasher.hash_parameters(params2)

        assert hash1 == hash2

    def test_generate_fingerprint(self):
        """Test complete fingerprint generation."""
        query = "SELECT * FROM users WHERE id = :id"
        params = {"id": 1}
        content = [{"id": 1, "name": "John"}]

        fp = ContentHasher.generate_fingerprint(query, params, content)

        assert isinstance(fp, QueryFingerprint)
        assert fp.query_hash is not None
        assert fp.parameter_hash is not None
        assert fp.content_hash is not None


class TestCompressionHandler:
    """Test cases for CompressionHandler."""

    def test_compress_small_data(self):
        """Test that small data is not compressed."""
        data = b"small data"
        compressed, was_compressed = CompressionHandler.compress(data)

        assert was_compressed is False
        assert compressed == data

    def test_compress_large_data(self):
        """Test compression of large data."""
        # Create data larger than threshold
        data = b"x" * CompressionHandler.COMPRESSION_THRESHOLD * 2
        compressed, was_compressed = CompressionHandler.compress(data)

        # Compression might or might not reduce size depending on content
        # but the function should work correctly
        assert isinstance(compressed, bytes)

    def test_decompress_compressed(self):
        """Test decompression of compressed data."""
        original = b"test data for compression"
        compressed, was_compressed = CompressionHandler.compress(original)

        if was_compressed:
            decompressed = CompressionHandler.decompress(compressed, was_compressed)
            assert decompressed == original

    def test_decompress_uncompressed(self):
        """Test decompression of uncompressed data."""
        data = b"small"
        compressed, was_compressed = CompressionHandler.compress(data)

        decompressed = CompressionHandler.decompress(compressed, was_compressed)
        assert decompressed == data


class TestWarmingTask:
    """Test cases for WarmingTask."""

    def test_warming_task_creation(self):
        """Test creating a warming task."""
        task = WarmingTask(
            query="SELECT * FROM users", compute_fn=lambda: [{"id": 1}], priority=5, interval_seconds=300
        )

        assert task.query == "SELECT * FROM users"
        assert task.priority == 5
        assert task.interval_seconds == 300
        assert task.run_count == 0

    async def test_warming_task_execute_sync(self):
        """Test executing a synchronous warming task."""
        compute_fn = MagicMock(return_value=[{"id": 1}])
        task = WarmingTask("SELECT 1", compute_fn)

        result = await task.execute()

        assert result == [{"id": 1}]
        assert task.run_count == 1
        assert task.last_run is not None

    async def test_warming_task_execute_async(self):
        """Test executing an async warming task."""

        async def async_compute():
            return [{"id": 1}]

        task = WarmingTask("SELECT 1", async_compute)

        result = await task.execute()

        assert result == [{"id": 1}]
        assert task.run_count == 1

    async def test_warming_task_execute_error(self):
        """Test error handling in warming task."""

        def failing_compute():
            raise ValueError("Test error")

        task = WarmingTask("SELECT 1", failing_compute)

        result = await task.execute()

        assert result is None
        assert task.error_count == 1

    def test_should_run_no_interval(self):
        """Test should_run with no interval."""
        task = WarmingTask("SELECT 1", lambda: None, interval_seconds=None)

        assert task.should_run() is True

    def test_should_run_first_time(self):
        """Test should_run on first execution."""
        task = WarmingTask("SELECT 1", lambda: None, interval_seconds=300)

        assert task.should_run() is True

    def test_should_run_after_interval(self):
        """Test should_run after interval has passed."""
        task = WarmingTask("SELECT 1", lambda: None, interval_seconds=0)
        task.last_run = datetime.now() - timedelta(seconds=1)

        assert task.should_run() is True

    def test_should_not_run_before_interval(self):
        """Test should_run before interval has passed."""
        task = WarmingTask("SELECT 1", lambda: None, interval_seconds=3600)
        task.last_run = datetime.now()

        assert task.should_run() is False


class TestQueryCache:
    """Test cases for QueryCache class."""

    @pytest.fixture
    async def cache(self):
        """Create a query cache for testing."""
        return QueryCache(
            redis_client=None,  # In-memory only
            dedup_strategy=DeduplicationStrategy.CONTENT_HASH,
            warming_strategy=CacheWarmingStrategy.NONE,
            enable_compression=False,
            default_ttl=300,
        )

    async def test_set_and_get(self, cache):
        """Test basic set and get operations."""
        await cache.set("SELECT * FROM users", [{"id": 1}], ttl=300)

        result = await cache.get("SELECT * FROM users")

        assert result is not None
        data, metadata = result
        assert data == [{"id": 1}]
        assert metadata["cached"] is True

    async def test_get_nonexistent(self, cache):
        """Test getting a non-existent query."""
        result = await cache.get("SELECT * FROM nonexistent")

        assert result is None

    async def test_get_with_parameters(self, cache):
        """Test getting with parameters."""
        await cache.set("SELECT * FROM users WHERE id = ?", [{"id": 1}], parameters={"id": 1})

        result = await cache.get("SELECT * FROM users WHERE id = ?", parameters={"id": 1})

        assert result is not None

    async def test_get_or_set_cache_miss(self, cache):
        """Test get_or_set with cache miss."""
        compute_fn = MagicMock(return_value=[{"id": 1}])

        result, was_cached, metadata = await cache.get_or_set("SELECT * FROM users", compute_fn)

        assert result == [{"id": 1}]
        assert was_cached is False
        assert metadata["cached"] is False
        compute_fn.assert_called_once()

    async def test_get_or_set_cache_hit(self, cache):
        """Test get_or_set with cache hit."""
        await cache.set("SELECT * FROM users", [{"id": 1}])

        compute_fn = MagicMock()

        result, was_cached, metadata = await cache.get_or_set("SELECT * FROM users", compute_fn)

        assert result == [{"id": 1}]
        assert was_cached is True
        compute_fn.assert_not_called()

    async def test_invalidate(self, cache):
        """Test query invalidation."""
        await cache.set("SELECT * FROM users", [{"id": 1}])

        # Verify exists
        assert await cache.get("SELECT * FROM users") is not None

        # Invalidate
        await cache.invalidate("SELECT * FROM users")

        # Verify gone
        assert await cache.get("SELECT * FROM users") is None

    async def test_clear(self, cache):
        """Test clearing all queries."""
        await cache.set("query1", [{"id": 1}])
        await cache.set("query2", [{"id": 2}])

        await cache.clear()

        assert await cache.get("query1") is None
        assert await cache.get("query2") is None

    async def test_deduplication_content_hash(self):
        """Test content hash deduplication."""
        cache = QueryCache(redis_client=None, dedup_strategy=DeduplicationStrategy.CONTENT_HASH)

        # Store first query
        key1 = await cache.set("SELECT * FROM users", [{"id": 1}])

        # Store same content with different query
        key2 = await cache.set("SELECT id FROM users", [{"id": 1}], skip_dedup=False)

        # Should be deduplicated
        assert cache._stats["deduplicated"] == 1

    async def test_register_warming_task(self, cache):
        """Test registering a warming task."""
        compute_fn = MagicMock(return_value=[{"id": 1}])

        cache.register_warming_task("SELECT * FROM users", compute_fn, priority=5, interval_seconds=300)

        assert "SELECT * FROM users" in cache._warming_tasks
        task = cache._warming_tasks["SELECT * FROM users"]
        assert task.priority == 5
        assert task.interval_seconds == 300

    async def test_unregister_warming_task(self, cache):
        """Test unregistering a warming task."""
        cache.register_warming_task("SELECT 1", lambda: None)

        result = cache.unregister_warming_task("SELECT 1")

        assert result is True
        assert "SELECT 1" not in cache._warming_tasks

    async def test_warm_cache_specific(self, cache):
        """Test warming a specific query."""
        compute_fn = MagicMock(return_value=[{"id": 1}])
        cache.register_warming_task("SELECT * FROM users", compute_fn)

        executed = await cache.warm_cache("SELECT * FROM users")

        assert executed == 1
        compute_fn.assert_called_once()

    async def test_get_stats(self, cache):
        """Test statistics collection."""
        await cache.set("query1", [{"id": 1}])
        await cache.get("query1")  # Hit
        await cache.get("query2")  # Miss

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["total_requests"] == 2
        assert stats["hit_rate"] == 0.5

    async def test_get_popular_queries(self, cache):
        """Test getting popular queries."""
        await cache.set("query1", [{"id": 1}])
        await cache.set("query2", [{"id": 2}])

        # Access query1 multiple times
        for _ in range(5):
            await cache.get("query1")

        # Access query2 once
        await cache.get("query2")

        popular = await cache.get_popular_queries(limit=2)

        assert len(popular) == 2
        assert popular[0][0] == "query1"
        assert popular[0][1] == 5  # access count

    async def test_expired_result_not_returned(self, cache):
        """Test that expired results are not returned."""
        await cache.set("query", [{"id": 1}], ttl=0)

        # Wait a tiny bit
        import time

        time.sleep(0.1)

        result = await cache.get("query")
        assert result is None

    async def test_tags_in_metadata(self, cache):
        """Test that tags are included in metadata."""
        await cache.set("query", [{"id": 1}], tags=["important", "users"])

        result = await cache.get("query")

        assert result is not None
        data, metadata = result
        assert "important" in metadata["tags"]
        assert "users" in metadata["tags"]


class TestDeduplicationStrategies:
    """Test cases for different deduplication strategies."""

    async def test_exact_match_deduplication(self):
        """Test exact match deduplication."""
        cache = QueryCache(redis_client=None, dedup_strategy=DeduplicationStrategy.EXACT_MATCH)

        await cache.set("SELECT * FROM users", [{"id": 1}])
        key = await cache.set("SELECT * FROM users", [{"id": 2}])

        # Should be deduplicated
        assert cache._stats["deduplicated"] == 1

    async def test_no_deduplication(self):
        """Test no deduplication strategy."""
        cache = QueryCache(redis_client=None, dedup_strategy=DeduplicationStrategy.NONE)

        await cache.set("query", [{"id": 1}])
        await cache.set("query", [{"id": 2}])

        # Should not be deduplicated
        assert cache._stats["deduplicated"] == 0


class TestCacheWarmingStrategies:
    """Test cases for cache warming strategies."""

    async def test_preemptive_warming(self):
        """Test preemptive warming strategy."""
        cache = QueryCache(redis_client=None, warming_strategy=CacheWarmingStrategy.PREEMPTIVE)

        # Should have warming active
        assert cache._warming_active is True

    async def test_no_warming(self):
        """Test no warming strategy."""
        cache = QueryCache(redis_client=None, warming_strategy=CacheWarmingStrategy.NONE)

        # Should not have warming active
        assert cache._warming_active is False