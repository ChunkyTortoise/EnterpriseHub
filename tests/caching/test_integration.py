"""
Integration Tests for Caching Layer
===================================

Tests cover:
    - End-to-end caching workflows
    - Component interactions
    - Redis integration (if available)
    - Performance characteristics
    - Error recovery
"""

import asyncio
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.caching import (
    CacheAnalytics,
    DeduplicationStrategy,
    EvictionPolicy,
    MockEmbeddingService,
    QueryCache,
    RedisClient,
    SemanticCache,
)

pytestmark = pytest.mark.asyncio


class TestCacheIntegration:
    """Integration tests for cache components working together."""

    async def test_semantic_and_query_cache_together(self):
        """Test semantic cache and query cache working together."""
        # Create shared embedding service
        embedding_service = MockEmbeddingService(dimensions=384)

        # Create caches
        semantic_cache = SemanticCache(
            redis_client=None,
            embedding_service=embedding_service,
            similarity_threshold=0.85,
            eviction_policy=EvictionPolicy.LRU,
            max_entries=100,
            enable_persistence=False,
        )

        query_cache = QueryCache(
            redis_client=None,
            dedup_strategy=DeduplicationStrategy.CONTENT_HASH,
            enable_compression=False,
            default_ttl=300,
        )

        # Store in semantic cache
        await semantic_cache.set("How do I reset my password?", {"action": "reset_password"}, tags=["help", "password"])

        # Store in query cache
        await query_cache.set(
            "SELECT * FROM users WHERE id = 1", [{"id": 1, "name": "John"}], tags=["users", "database"]
        )

        # Retrieve from both
        semantic_result = await semantic_cache.get("How do I reset my password?")
        query_result = await query_cache.get("SELECT * FROM users WHERE id = 1")

        assert semantic_result is not None
        assert query_result is not None

    async def test_analytics_with_caches(self):
        """Test analytics tracking cache operations."""
        analytics = CacheAnalytics(redis_client=None, enable_persistence=False)

        cache = SemanticCache(redis_client=None, enable_persistence=False)

        # Perform operations and record to analytics
        await cache.set("query1", {"data": 1})

        result = await cache.get("query1")
        if result:
            await analytics.record_hit("semantic_cache", response_time_ms=5.0)

        result = await cache.get("nonexistent")
        if not result:
            await analytics.record_miss("semantic_cache", computation_time_ms=100.0)

        # Check analytics
        metrics = await analytics.get_metrics("semantic_cache")
        assert metrics.hits == 1
        assert metrics.misses == 1

    async def test_cache_invalidation_cascade(self):
        """Test invalidation across multiple cache layers."""
        semantic_cache = SemanticCache(redis_client=None, enable_persistence=False)

        query_cache = QueryCache(redis_client=None, enable_persistence=False)

        # Store in both caches
        await semantic_cache.set("user:123", {"name": "John"}, tags=["user"])
        await query_cache.set("SELECT * FROM users WHERE id = 123", [{"name": "John"}], tags=["user"])

        # Invalidate by tag in both
        await semantic_cache.invalidate_by_tag("user")
        await query_cache.invalidate_by_tag("user")

        # Verify both are cleared
        assert await semantic_cache.get("user:123") is None
        assert await query_cache.get("SELECT * FROM users WHERE id = 123") is None

    async def test_high_load_scenario(self):
        """Test cache behavior under high load."""
        cache = SemanticCache(
            redis_client=None,
            embedding_service=MockEmbeddingService(),
            max_entries=50,
            eviction_policy=EvictionPolicy.LRU,
            enable_persistence=False,
        )

        # Simulate many concurrent operations
        async def operation(i):
            await cache.set(f"key_{i}", {"data": i})
            return await cache.get(f"key_{i}")

        tasks = [operation(i) for i in range(100)]
        results = await asyncio.gather(*tasks)

        # Some should succeed (not all due to eviction)
        successful = sum(1 for r in results if r is not None)
        assert successful > 0
        assert len(cache._memory_cache) <= 50


class TestRedisIntegration:
    """Integration tests with Redis (skipped if Redis unavailable)."""

    @pytest.fixture
    async def redis_client(self):
        """Create Redis client for integration tests."""
        try:
            client = RedisClient("redis://localhost:6379/15")  # Use DB 15 for tests
            await client.connect()
            yield client
            await client.disconnect()
        except Exception:
            pytest.skip("Redis not available")

    async def test_redis_basic_operations(self, redis_client):
        """Test basic Redis operations."""
        # Set value
        await redis_client.set("test_key", {"data": "value"}, ttl=60)

        # Get value
        result = await redis_client.get("test_key")
        assert result == {"data": "value"}

        # Delete value
        await redis_client.delete("test_key")
        result = await redis_client.get("test_key")
        assert result is None

    async def test_redis_batch_operations(self, redis_client):
        """Test Redis batch operations."""
        # Set multiple
        await redis_client.mset({"key1": "value1", "key2": "value2", "key3": "value3"})

        # Get multiple
        results = await redis_client.mget(["key1", "key2", "key3"])
        assert len(results) == 3
        assert results["key1"] == "value1"

        # Cleanup
        await redis_client.delete("key1", "key2", "key3")

    async def test_redis_ttl(self, redis_client):
        """Test Redis TTL functionality."""
        await redis_client.set("ttl_key", "value", ttl=3600)

        ttl = await redis_client.ttl("ttl_key")
        assert ttl > 0

        # Update expiration
        await redis_client.expire("ttl_key", 60)
        ttl = await redis_client.ttl("ttl_key")
        assert ttl <= 60

        await redis_client.delete("ttl_key")

    async def test_redis_health_check(self, redis_client):
        """Test Redis health check."""
        health = await redis_client.health_check()

        assert health["status"] == "connected"
        assert health["healthy"] is True
        assert "latency_ms" in health

    async def test_semantic_cache_with_redis(self, redis_client):
        """Test semantic cache with Redis persistence."""
        cache = SemanticCache(
            redis_client=redis_client, embedding_service=MockEmbeddingService(), enable_persistence=True
        )

        # Store value
        await cache.set("test_query", {"result": "data"}, ttl=60)

        # Retrieve value
        result = await cache.get("test_query")
        assert result is not None

        # Cleanup
        await cache.clear()


class TestErrorRecovery:
    """Tests for error handling and recovery."""

    async def test_cache_graceful_degradation(self):
        """Test cache continues to work when Redis fails."""
        # Create cache without Redis
        cache = SemanticCache(redis_client=None, enable_persistence=False)

        # Should still work
        await cache.set("key", "value")
        result = await cache.get("key")

        assert result is not None

    async def test_analytics_with_errors(self):
        """Test analytics handles errors gracefully."""
        analytics = CacheAnalytics(enable_persistence=False)

        # Record various events
        await analytics.record_hit("cache")
        await analytics.record_miss("cache")
        await analytics.record_error("cache", ValueError("Test error"))

        # Should still provide metrics
        metrics = await analytics.get_metrics("cache")
        assert metrics.hits == 1
        assert metrics.misses == 1
        assert metrics.errors == 1

    async def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        cache = QueryCache(enable_persistence=False)

        # Try to cache None
        await cache.set("key", None)
        result = await cache.get("key")

        assert result is not None
        data, _ = result
        assert data is None


class TestPerformanceCharacteristics:
    """Tests for performance characteristics."""

    async def test_large_result_caching(self):
        """Test caching of large results."""
        cache = QueryCache(enable_persistence=False, enable_compression=True)

        # Create large result
        large_result = [{"id": i, "data": "x" * 1000} for i in range(1000)]

        await cache.set("large_query", large_result)
        result = await cache.get("large_query")

        assert result is not None
        data, _ = result
        assert len(data) == 1000

    async def test_concurrent_access(self):
        """Test concurrent cache access."""
        cache = SemanticCache(enable_persistence=False)

        # Concurrent writes
        async def write(i):
            await cache.set(f"key_{i}", {"value": i})

        # Concurrent reads
        async def read(i):
            return await cache.get(f"key_{i}")

        # Mix of reads and writes
        tasks = []
        for i in range(50):
            tasks.append(write(i))
            tasks.append(read(i))

        await asyncio.gather(*tasks)

        # Cache should be in consistent state
        assert len(cache._memory_cache) <= 50

    async def test_memory_pressure(self):
        """Test cache behavior under memory pressure."""
        cache = SemanticCache(max_entries=10, eviction_policy=EvictionPolicy.LRU, enable_persistence=False)

        # Add more entries than max
        for i in range(20):
            await cache.set(f"key_{i}", {"data": i})

        # Should not exceed max
        assert len(cache._memory_cache) <= 10


class TestFactoryFunctions:
    """Tests for factory functions."""

    async def test_create_semantic_cache(self):
        """Test semantic cache factory function."""
        from src.caching.semantic_cache import create_semantic_cache

        cache = create_semantic_cache(redis_url=None, embedding_provider="mock", similarity_threshold=0.9)

        assert isinstance(cache, SemanticCache)
        assert cache.similarity_threshold == 0.9

    async def test_create_query_cache(self):
        """Test query cache factory function."""
        from src.caching.query_cache import create_query_cache

        cache = await create_query_cache(redis_url=None, dedup_strategy=DeduplicationStrategy.CONTENT_HASH)

        assert isinstance(cache, QueryCache)
        assert cache.dedup_strategy == DeduplicationStrategy.CONTENT_HASH

    async def test_create_cache_analytics(self):
        """Test analytics factory function."""
        from src.caching.analytics import create_cache_analytics

        analytics = await create_cache_analytics(redis_url=None, retention_minutes=30)

        assert isinstance(analytics, CacheAnalytics)
        assert analytics.retention_minutes == 30


class TestEdgeCases:
    """Tests for edge cases and boundary conditions."""

    async def test_empty_string_key(self):
        """Test caching with empty string key."""
        cache = SemanticCache(enable_persistence=False)

        await cache.set("", {"data": "empty"})
        result = await cache.get("")

        assert result is not None

    async def test_very_long_key(self):
        """Test caching with very long key."""
        cache = SemanticCache(enable_persistence=False)

        long_key = "x" * 10000
        await cache.set(long_key, {"data": "long"})
        result = await cache.get(long_key)

        assert result is not None

    async def test_unicode_characters(self):
        """Test caching with unicode characters."""
        cache = QueryCache(enable_persistence=False)

        unicode_query = "SELECT * FROM users WHERE name = '日本語'"
        await cache.set(unicode_query, [{"name": "日本語"}])
        result = await cache.get(unicode_query)

        assert result is not None

    async def test_special_characters(self):
        """Test caching with special characters."""
        cache = QueryCache(enable_persistence=False)

        special_query = "SELECT * FROM users WHERE data LIKE '%<script>%'"
        await cache.set(special_query, [{"data": "<script>alert('xss')</script>"}])
        result = await cache.get(special_query)

        assert result is not None

    async def test_nested_data_structures(self):
        """Test caching with nested data."""
        cache = QueryCache(enable_persistence=False)

        nested_data = {"level1": {"level2": {"level3": [1, 2, {"deep": "value"}]}}}

        await cache.set("nested", nested_data)
        result = await cache.get("nested")

        assert result is not None
        data, _ = result
        assert data["level1"]["level2"]["level3"][2]["deep"] == "value"
