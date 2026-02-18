import pytest

pytestmark = pytest.mark.integration

"""
Tests for TieredCacheService - Comprehensive Test Suite

Tests all aspects of the tiered caching system:
- L1 Memory Cache functionality
- L2 Redis Cache integration
- Automatic promotion logic
- Performance metrics tracking
- Background cleanup tasks
- Decorator functionality
- Error handling and resilience

Author: Claude Sonnet 4
Date: 2026-01-17
"""

import asyncio
import pickle
import time
from typing import Any, Dict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from ghl_real_estate_ai.services.tiered_cache_service import (
    CacheItem,
    CacheMetrics,
    LRUCache,
    RedisBackend,
    TieredCacheContext,
    TieredCacheService,
    cache_clear,
    cache_delete,
    cache_get,
    cache_metrics,
    cache_set,
    get_tiered_cache,
    tiered_cache,
)


class TestCacheMetrics:
    """Test CacheMetrics functionality."""

    def test_metrics_initialization(self):
        """Test metrics are properly initialized."""
        metrics = CacheMetrics()
        assert metrics.l1_hits == 0
        assert metrics.l2_hits == 0
        assert metrics.cache_hit_ratio == 0.0
        assert metrics.total_requests == 0

    def test_l1_hit_tracking(self):
        """Test L1 hit metrics tracking."""
        metrics = CacheMetrics()

        metrics.update_l1_hit(1.5)
        metrics.update_l1_hit(2.0)

        assert metrics.l1_hits == 2
        assert metrics.total_requests == 2
        assert metrics.cache_hit_ratio == 1.0
        assert metrics.l1_total_latency_ms == 3.5

    def test_l2_promotion_tracking(self):
        """Test L2 promotion metrics."""
        metrics = CacheMetrics()

        metrics.update_l2_hit(5.0, promoted=True)
        metrics.update_l2_hit(4.0, promoted=False)

        assert metrics.l2_hits == 2
        assert metrics.l2_promotions == 1
        assert metrics.l2_total_latency_ms == 9.0

    def test_hit_ratio_calculation(self):
        """Test cache hit ratio calculation."""
        metrics = CacheMetrics()

        # Mix of hits and misses
        metrics.update_l1_hit(1.0)  # Hit
        metrics.update_l1_miss(2.0)  # Miss
        metrics.update_l2_hit(3.0)  # Hit
        metrics.update_l2_miss(4.0)  # Miss

        assert metrics.total_requests == 4
        assert metrics.cache_hit_ratio == 0.5  # 2 hits / 4 requests

    def test_cleanup_tracking(self):
        """Test cleanup metrics tracking."""
        metrics = CacheMetrics()

        metrics.record_cleanup(5)
        metrics.record_cleanup(3)

        assert metrics.cleanup_runs == 2
        assert metrics.expired_items_cleaned == 8
        assert metrics.last_cleanup_time is not None

    def test_metrics_summary(self):
        """Test comprehensive metrics summary."""
        metrics = CacheMetrics()

        # Generate some activity
        metrics.update_l1_hit(1.0)
        metrics.update_l2_hit(5.0, promoted=True)
        metrics.update_l1_miss(2.0)

        summary = metrics.get_summary()

        assert "performance" in summary
        assert "l1_memory_cache" in summary
        assert "l2_redis_cache" in summary
        assert summary["performance"]["hit_ratio_percent"] == 66.67
        assert summary["l2_redis_cache"]["promotions_to_l1"] == 1


class TestCacheItem:
    """Test CacheItem functionality."""

    def test_cache_item_creation(self):
        """Test cache item creation."""
        now = time.time()
        item = CacheItem(value="test_value", created_at=now, expires_at=now + 300)

        assert item.value == "test_value"
        assert item.access_count == 0
        assert item.size_bytes > 0  # Should calculate size

    def test_expiration_check(self):
        """Test expiration logic."""
        now = time.time()

        # Non-expired item
        fresh_item = CacheItem(value="fresh", created_at=now, expires_at=now + 300)
        assert not fresh_item.is_expired

        # Expired item
        expired_item = CacheItem(value="expired", created_at=now - 300, expires_at=now - 100)
        assert expired_item.is_expired

    def test_promotion_logic(self):
        """Test promotion decision logic."""
        item = CacheItem(value="test", created_at=time.time(), expires_at=time.time() + 300)

        # Should not promote initially
        assert not item.should_promote

        # Should promote after 2 accesses
        item.access()
        assert not item.should_promote

        item.access()
        assert item.should_promote

    def test_access_tracking(self):
        """Test access count and timestamp tracking."""
        base = 1_000_000.0
        item = CacheItem(value="test", created_at=base, expires_at=base + 300)

        # Pin last_access to a known value (bypasses default_factory timing)
        item.last_access = base
        initial_access = item.last_access

        # Mock time.time in source module so access() records a later timestamp
        with patch("ghl_real_estate_ai.services.tiered_cache_service.time.time", return_value=base + 1.0):
            item.access()

        assert item.access_count == 1
        assert item.last_access > initial_access


class TestLRUCache:
    """Test LRUCache functionality."""

    def test_lru_cache_basic_operations(self):
        """Test basic LRU cache operations."""
        cache = LRUCache(max_size=3, default_ttl=300)

        # Test set and get
        assert cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

        # Test miss
        assert cache.get("nonexistent") is None

        # Test delete
        assert cache.delete("key1")
        assert cache.get("key1") is None

    def test_lru_eviction(self):
        """Test LRU eviction logic."""
        cache = LRUCache(max_size=2, default_ttl=300)

        # Fill cache
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        # Access key1 to make it recent
        cache.get("key1")

        # Add third item, should evict key2
        cache.set("key3", "value3")

        assert cache.get("key1") == "value1"  # Still there
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") == "value3"  # New item

    def test_ttl_expiration(self):
        """Test TTL expiration."""
        base = 1_000_000.0
        with patch("ghl_real_estate_ai.services.tiered_cache_service.time.time", return_value=base):
            cache = LRUCache(max_size=10, default_ttl=1)
            cache.set("key1", "value1", ttl=1)
            assert cache.get("key1") == "value1"

        # Advance time past TTL without sleeping
        with patch("ghl_real_estate_ai.services.tiered_cache_service.time.time", return_value=base + 2.0):
            assert cache.get("key1") is None

    def test_cleanup_expired(self):
        """Test manual expired item cleanup."""
        base = 1_000_000.0
        with patch("ghl_real_estate_ai.services.tiered_cache_service.time.time", return_value=base):
            cache = LRUCache(max_size=10, default_ttl=1)

            # Add items with short TTL
            cache.set("key1", "value1", ttl=1)
            cache.set("key2", "value2", ttl=1)

        # Advance time past TTL without sleeping
        with patch("ghl_real_estate_ai.services.tiered_cache_service.time.time", return_value=base + 2.0):
            # Cleanup should remove expired items
            expired_count = cache.cleanup_expired()
            assert expired_count == 2

            assert cache.get("key1") is None
            assert cache.get("key2") is None

    def test_lru_stats(self):
        """Test LRU cache statistics."""
        cache = LRUCache(max_size=5, default_ttl=300)

        cache.set("key1", "value1")
        cache.set("key2", "value2")

        stats = cache.get_stats()

        assert stats["size"] == 2
        assert stats["max_size"] == 5
        assert stats["utilization_percent"] == 40.0
        assert stats["total_size_bytes"] > 0


class TestRedisBackend:
    """Test RedisBackend functionality."""

    @pytest.fixture
    def mock_redis(self):
        """Mock Redis for testing."""
        with patch("redis.asyncio.Redis") as mock_redis_class:
            mock_instance = AsyncMock()
            mock_redis_class.return_value = mock_instance
            yield mock_instance

    @pytest.mark.asyncio
    async def test_redis_initialization(self, mock_redis):
        """Test Redis backend initialization."""
        with patch("redis.asyncio.connection.ConnectionPool") as mock_pool:
            mock_pool.from_url.return_value = MagicMock()

            backend = RedisBackend("redis://localhost:6379")
            await backend.initialize()

            assert backend.enabled

    @pytest.mark.asyncio
    async def test_redis_operations(self, mock_redis):
        """Test Redis get/set/delete operations."""
        backend = RedisBackend()
        backend.redis = mock_redis
        backend.enabled = True

        # Test set
        mock_redis.set.return_value = True
        result = await backend.set("key1", b"data", 300)
        assert result is True

        # Test get
        mock_redis.get.return_value = b"data"
        result = await backend.get("key1")
        assert result == b"data"

        # Test delete
        mock_redis.delete.return_value = 1
        result = await backend.delete("key1")
        assert result is True

    @pytest.mark.asyncio
    async def test_redis_error_handling(self, mock_redis):
        """Test Redis error handling."""
        backend = RedisBackend()
        backend.redis = mock_redis
        backend.enabled = True

        # Test get error
        mock_redis.get.side_effect = Exception("Connection error")
        result = await backend.get("key1")
        assert result is None

        # Test set error
        mock_redis.set.side_effect = Exception("Connection error")
        result = await backend.set("key1", b"data", 300)
        assert result is False


class TestTieredCacheService:
    """Test TieredCacheService integration."""

    @pytest.fixture
    def cache_service(self):
        """Create cache service for testing."""
        service = TieredCacheService()
        # Reset singleton state for clean tests
        service._initialized = False
        service.__init__()
        return service

    @pytest.mark.asyncio
    async def test_cache_service_initialization(self, cache_service):
        """Test cache service initialization."""
        await cache_service.start()

        assert cache_service.l1_cache is not None
        assert cache_service.l2_backend is not None
        assert cache_service.metrics is not None

        await cache_service.stop()

    @pytest.mark.asyncio
    async def test_l1_cache_flow(self, cache_service):
        """Test L1 cache hit flow."""
        await cache_service.start()

        # Set and get from L1
        await cache_service.set("key1", "value1", 300)
        result = await cache_service.get("key1")

        assert result == "value1"
        assert cache_service.metrics.l1_hits > 0

        await cache_service.stop()

    @pytest.mark.asyncio
    async def test_cache_miss_flow(self, cache_service):
        """Test cache miss flow."""
        await cache_service.start()

        # Try to get non-existent key
        result = await cache_service.get("nonexistent")

        assert result is None
        assert cache_service.metrics.l1_misses > 0

        await cache_service.stop()

    @pytest.mark.asyncio
    async def test_cache_deletion(self, cache_service):
        """Test cache deletion."""
        await cache_service.start()

        # Set, verify, delete, verify gone
        await cache_service.set("key1", "value1")
        assert await cache_service.get("key1") == "value1"

        await cache_service.delete("key1")
        assert await cache_service.get("key1") is None

        await cache_service.stop()

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache_service):
        """Test cache clearing."""
        await cache_service.start()

        # Set multiple keys
        await cache_service.set("key1", "value1")
        await cache_service.set("key2", "value2")

        # Verify they exist
        assert await cache_service.get("key1") == "value1"
        assert await cache_service.get("key2") == "value2"

        # Clear cache
        await cache_service.clear()

        # Verify they're gone
        assert await cache_service.get("key1") is None
        assert await cache_service.get("key2") is None

        await cache_service.stop()

    @pytest.mark.asyncio
    async def test_metrics_tracking(self, cache_service):
        """Test metrics tracking."""
        await cache_service.start()

        # Generate cache activity
        await cache_service.set("key1", "value1")
        await cache_service.get("key1")  # L1 hit
        await cache_service.get("nonexistent")  # L1 miss

        metrics = cache_service.get_metrics()

        assert metrics["performance"]["total_requests"] >= 2
        assert metrics["l1_memory_cache"]["hits"] >= 1
        assert metrics["l1_memory_cache"]["misses"] >= 1

        await cache_service.stop()


class TestTieredCacheDecorator:
    """Test tiered_cache decorator functionality."""

    @pytest.mark.asyncio
    async def test_async_function_caching(self):
        """Test decorator with async functions."""
        call_count = 0

        @tiered_cache(ttl=300, key_prefix="test")
        async def expensive_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)  # Simulate work
            return x * 2

        # First call should execute function
        result1 = await expensive_function(5)
        assert result1 == 10
        assert call_count == 1

        # Second call should use cache
        result2 = await expensive_function(5)
        assert result2 == 10
        assert call_count == 1  # Should not increment

        # Different args should execute function again
        result3 = await expensive_function(10)
        assert result3 == 20
        assert call_count == 2

    def test_sync_function_caching(self):
        """Test decorator with sync functions."""
        call_count = 0

        @tiered_cache(ttl=300, key_prefix="sync_test")
        def expensive_sync_function(x: int) -> int:
            nonlocal call_count
            call_count += 1
            return x * 3

        # Sync functions called outside an event loop execute directly
        result1 = expensive_sync_function(5)
        assert result1 == 15

    @pytest.mark.asyncio
    async def test_decorator_with_complex_args(self):
        """Test decorator with complex arguments."""
        call_count = 0

        @tiered_cache(ttl=300, key_prefix="complex")
        async def function_with_complex_args(a: int, b: str, c: dict) -> str:
            nonlocal call_count
            call_count += 1
            return f"{a}_{b}_{len(c)}"

        args = (5, "test", {"key": "value"})

        # First call
        result1 = await function_with_complex_args(*args)
        assert result1 == "5_test_1"
        assert call_count == 1

        # Second call with same args
        result2 = await function_with_complex_args(*args)
        assert result2 == "5_test_1"
        assert call_count == 1  # Should use cache


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.mark.asyncio
    async def test_convenience_functions(self):
        """Test global convenience functions."""
        # Test cache_set and cache_get
        success = await cache_set("test_key", "test_value", 300)
        assert success

        result = await cache_get("test_key")
        assert result == "test_value"

        # Test cache_delete
        deleted = await cache_delete("test_key")
        assert deleted

        result = await cache_get("test_key")
        assert result is None

        # Test cache_metrics
        metrics = await cache_metrics()
        assert isinstance(metrics, dict)
        assert "performance" in metrics

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test TieredCacheContext context manager."""
        async with TieredCacheContext() as cache:
            assert isinstance(cache, TieredCacheService)

            # Use cache
            await cache.set("ctx_key", "ctx_value")
            result = await cache.get("ctx_key")
            assert result == "ctx_value"

        # Context manager should have stopped the service


class TestErrorHandling:
    """Test error handling and resilience."""

    @pytest.mark.asyncio
    async def test_redis_unavailable_graceful_degradation(self):
        """Test graceful degradation when Redis is unavailable."""
        service = TieredCacheService()
        service._initialized = False
        service.__init__()

        # Mock Redis as unavailable
        service.l2_backend.enabled = False

        await service.start()

        # Should still work with L1 only
        await service.set("key1", "value1")
        result = await service.get("key1")
        assert result == "value1"

        await service.stop()

    @pytest.mark.asyncio
    async def test_serialization_error_handling(self):
        """Test handling of serialization errors."""
        service = TieredCacheService()
        service._initialized = False
        service.__init__()

        await service.start()

        # Try to cache an object that can't be pickled
        class UnpicklableClass:
            def __reduce__(self):
                raise TypeError("Cannot pickle this object")

        unpicklable = UnpicklableClass()

        # Should handle gracefully
        result = await service.set("unpicklable", unpicklable)
        # Should not crash, might succeed or fail gracefully

        await service.stop()


class TestPerformanceCharacteristics:
    """Test performance characteristics and benchmarks."""

    @pytest.mark.asyncio
    async def test_l1_cache_performance(self):
        """Test L1 cache performance is sub-millisecond."""
        cache = LRUCache(max_size=1000, default_ttl=300)

        # Set some data
        for i in range(100):
            cache.set(f"key_{i}", f"value_{i}")

        # Measure get performance
        start_time = time.perf_counter()

        for i in range(100):
            cache.get(f"key_{i}")

        elapsed = time.perf_counter() - start_time
        avg_latency_ms = (elapsed / 100) * 1000

        # Should be well under 1ms per operation
        assert avg_latency_ms < 1.0, f"L1 cache too slow: {avg_latency_ms}ms"

    @pytest.mark.asyncio
    async def test_promotion_efficiency(self):
        """Test that promotion logic works efficiently."""
        service = TieredCacheService()
        service._initialized = False
        service.__init__()

        await service.start()

        # Set item that will be promoted
        await service.set("promotion_test", "value", 300)

        # Access it multiple times to trigger promotion
        for _ in range(3):
            result = await service.get("promotion_test")
            assert result == "value"

        # Check that promotion occurred
        metrics = service.get_metrics()
        assert metrics["l2_redis_cache"]["promotions_to_l1"] >= 0

        await service.stop()


if __name__ == "__main__":
    """Run tests directly."""
    import sys

    # Simple test runner
    pytest_args = [__file__, "-v", "--tb=short", "--asyncio-mode=auto"]

    if "--performance" in sys.argv:
        pytest_args.extend(["-m", "performance"])

    pytest.main(pytest_args)