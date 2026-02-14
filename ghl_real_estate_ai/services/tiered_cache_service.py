"""
Tiered Cache Service - High-Performance Multi-Layer Caching

Provides a zero-configuration tiered caching system with:
- L1 Memory Cache: Thread-safe LRU with <1ms latency (10,000 items max)
- L2 Redis Cache: Distributed cache with <5ms latency (persistent)
- Automatic L2 → L1 promotion after 2 accesses
- Comprehensive metrics tracking
- Background cleanup tasks

Performance Targets:
- ML scoring: 200ms → 20ms (90% reduction via L1 cache hits)
- Overall latency: 70% reduction average
- Memory efficiency: Intelligent eviction with TTL management

Author: Claude Sonnet 4
Date: 2026-01-17
"""

import asyncio
import hashlib
import pickle
import threading
import time
import weakref
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from functools import wraps
from typing import Any, Callable, Dict, Generic, Optional, TypeVar

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Type variable for generic cache operations
T = TypeVar("T")


@dataclass
class CacheMetrics:
    """Comprehensive cache performance metrics."""

    # L1 Memory Cache Metrics
    l1_hits: int = 0
    l1_misses: int = 0
    l1_evictions: int = 0
    l1_size_current: int = 0
    l1_size_max: int = 10000
    l1_total_latency_ms: float = 0.0

    # L2 Redis Cache Metrics
    l2_hits: int = 0
    l2_misses: int = 0
    l2_promotions: int = 0  # L2 → L1 promotions
    l2_total_latency_ms: float = 0.0

    # Overall Performance
    total_requests: int = 0
    cache_hit_ratio: float = 0.0
    average_latency_ms: float = 0.0

    # Background Tasks
    cleanup_runs: int = 0
    expired_items_cleaned: int = 0
    last_cleanup_time: Optional[datetime] = None

    def update_l1_hit(self, latency_ms: float):
        """Update L1 hit metrics."""
        self.l1_hits += 1
        self.total_requests += 1
        self.l1_total_latency_ms += latency_ms
        self._recalculate_ratios()

    def update_l1_miss(self, latency_ms: float):
        """Update L1 miss metrics."""
        self.l1_misses += 1
        self.total_requests += 1
        self.l1_total_latency_ms += latency_ms
        self._recalculate_ratios()

    def update_l2_hit(self, latency_ms: float, promoted: bool = False):
        """Update L2 hit metrics."""
        self.l2_hits += 1
        self.total_requests += 1
        self.l2_total_latency_ms += latency_ms
        if promoted:
            self.l2_promotions += 1
        self._recalculate_ratios()

    def update_l2_miss(self, latency_ms: float):
        """Update L2 miss metrics."""
        self.l2_misses += 1
        self.total_requests += 1
        self.l2_total_latency_ms += latency_ms
        self._recalculate_ratios()

    def record_eviction(self):
        """Record L1 cache eviction."""
        self.l1_evictions += 1

    def record_cleanup(self, expired_count: int):
        """Record background cleanup run."""
        self.cleanup_runs += 1
        self.expired_items_cleaned += expired_count
        self.last_cleanup_time = datetime.now()

    def _recalculate_ratios(self):
        """Recalculate derived metrics."""
        total_hits = self.l1_hits + self.l2_hits
        if self.total_requests > 0:
            self.cache_hit_ratio = total_hits / self.total_requests
            total_latency = self.l1_total_latency_ms + self.l2_total_latency_ms
            self.average_latency_ms = total_latency / self.total_requests

    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive metrics summary."""
        return {
            "performance": {
                "hit_ratio_percent": round(self.cache_hit_ratio * 100, 2),
                "average_latency_ms": round(self.average_latency_ms, 3),
                "total_requests": self.total_requests,
                "performance_improvement": f"{round((1 - self.cache_hit_ratio) * 100, 1)}% reduction in backend calls",
            },
            "l1_memory_cache": {
                "hits": self.l1_hits,
                "misses": self.l1_misses,
                "hit_ratio_percent": round(self.l1_hits / max(1, self.l1_hits + self.l1_misses) * 100, 2),
                "current_size": self.l1_size_current,
                "max_size": self.l1_size_max,
                "utilization_percent": round(self.l1_size_current / self.l1_size_max * 100, 2),
                "evictions": self.l1_evictions,
                "average_latency_ms": round(self.l1_total_latency_ms / max(1, self.l1_hits + self.l1_misses), 3),
            },
            "l2_redis_cache": {
                "hits": self.l2_hits,
                "misses": self.l2_misses,
                "hit_ratio_percent": round(self.l2_hits / max(1, self.l2_hits + self.l2_misses) * 100, 2),
                "promotions_to_l1": self.l2_promotions,
                "average_latency_ms": round(self.l2_total_latency_ms / max(1, self.l2_hits + self.l2_misses), 3),
            },
            "background_tasks": {
                "cleanup_runs": self.cleanup_runs,
                "expired_items_cleaned": self.expired_items_cleaned,
                "last_cleanup": self.last_cleanup_time.isoformat() if self.last_cleanup_time else "Never",
            },
        }


@dataclass
class CacheItem(Generic[T]):
    """Cache item with metadata for tiered caching."""

    value: T
    created_at: float
    expires_at: float
    access_count: int = 0
    last_access: float = field(default_factory=time.time)
    size_bytes: int = 0
    source: str = "unknown"  # "l1", "l2", "function"

    def __post_init__(self):
        """Calculate size estimate after initialization."""
        if self.size_bytes == 0:
            try:
                # Estimate size using pickle serialization
                self.size_bytes = len(pickle.dumps(self.value))
            except (pickle.PickleError, AttributeError, TypeError):
                # Fallback size estimate for non-picklable objects
                self.size_bytes = 1024  # 1KB default

    @property
    def is_expired(self) -> bool:
        """Check if item is expired."""
        return time.time() > self.expires_at

    @property
    def should_promote(self) -> bool:
        """Check if item should be promoted to L1 cache."""
        return self.access_count >= 2  # Promote after 2 accesses

    @property
    def age_seconds(self) -> float:
        """Get item age in seconds."""
        return time.time() - self.created_at

    def access(self):
        """Record access to item."""
        self.access_count += 1
        self.last_access = time.time()


class LRUCache(Generic[T]):
    """Thread-safe LRU cache with TTL and size limits."""

    def __init__(self, max_size: int = 10000, default_ttl: int = 300):
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheItem[T]] = OrderedDict()
        self._lock = threading.RLock()
        self._metrics_ref: Optional[weakref.ref] = None

    def set_metrics_ref(self, metrics: CacheMetrics):
        """Set weak reference to metrics for tracking."""
        self._metrics_ref = weakref.ref(metrics)

    def get(self, key: str) -> Optional[T]:
        """Get item from cache with LRU management."""
        start_time = time.perf_counter()

        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._record_miss(start_time)
                return None

            if item.is_expired:
                del self._cache[key]
                self._record_miss(start_time)
                return None

            # Move to end (most recently used)
            self._cache.move_to_end(key)
            item.access()

            self._record_hit(start_time)
            return item.value

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> bool:
        """Set item in cache with eviction management."""
        ttl = ttl or self.default_ttl
        now = time.time()

        with self._lock:
            # Create cache item
            item = CacheItem(value=value, created_at=now, expires_at=now + ttl, source="l1")

            # Add/update item
            if key in self._cache:
                self._cache[key] = item
                self._cache.move_to_end(key)
            else:
                self._cache[key] = item

                # Evict if needed
                while len(self._cache) > self.max_size:
                    self._evict_lru()

            return True

    def delete(self, key: str) -> bool:
        """Delete item from cache."""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False

    def clear(self):
        """Clear all items from cache."""
        with self._lock:
            self._cache.clear()

    def cleanup_expired(self) -> int:
        """Remove expired items and return count."""
        expired_keys = []
        now = time.time()

        with self._lock:
            for key, item in self._cache.items():
                if now > item.expires_at:
                    expired_keys.append(key)

            for key in expired_keys:
                del self._cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self._lock:
            total_size_bytes = sum(item.size_bytes for item in self._cache.values())
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "total_size_bytes": total_size_bytes,
                "utilization_percent": len(self._cache) / self.max_size * 100,
            }

    def _evict_lru(self):
        """Evict least recently used item."""
        if self._cache:
            key, _ = self._cache.popitem(last=False)  # Remove first (oldest)
            if self._metrics_ref and self._metrics_ref():
                self._metrics_ref().record_eviction()

    def _record_hit(self, start_time: float):
        """Record cache hit in metrics."""
        latency_ms = (time.perf_counter() - start_time) * 1000
        if self._metrics_ref and self._metrics_ref():
            self._metrics_ref().update_l1_hit(latency_ms)

    def _record_miss(self, start_time: float):
        """Record cache miss in metrics."""
        latency_ms = (time.perf_counter() - start_time) * 1000
        if self._metrics_ref and self._metrics_ref():
            self._metrics_ref().update_l1_miss(latency_ms)


class RedisBackend:
    """Async Redis backend for L2 cache."""

    def __init__(self, redis_url: Optional[str] = None, max_connections: int = 50):
        self.redis_url = redis_url or settings.redis_url
        self.max_connections = max_connections
        self.redis = None
        self.enabled = False
        self._connection_pool = None

    async def initialize(self):
        """Initialize Redis connection."""
        if not self.redis_url:
            logger.info("Redis URL not configured, L2 cache disabled")
            return

        try:
            import redis.asyncio as redis
            from redis.asyncio.connection import ConnectionPool

            self._connection_pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=5,
                socket_connect_timeout=5,
                decode_responses=False,
            )

            self.redis = redis.Redis(connection_pool=self._connection_pool)

            # Test connection
            await self.redis.ping()
            self.enabled = True
            logger.info(f"L2 Redis cache initialized: {self.redis_url}")

        except ImportError:
            logger.warning("Redis package not installed, L2 cache disabled")
        except Exception as e:
            logger.warning(f"Redis connection failed, L2 cache disabled: {e}")

    async def get(self, key: str) -> Optional[bytes]:
        """Get raw bytes from Redis."""
        if not self.enabled:
            return None

        try:
            return await self.redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    async def set(self, key: str, data: bytes, ttl: int) -> bool:
        """Set raw bytes in Redis."""
        if not self.enabled:
            return False

        try:
            await self.redis.set(key, data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from Redis."""
        if not self.enabled:
            return False

        try:
            result = await self.redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    async def close(self):
        """Close Redis connection."""
        if self.enabled and self._connection_pool:
            await self._connection_pool.disconnect()
            logger.info("Redis connection pool closed")


class TieredCacheService:
    """
    High-performance tiered cache service.

    Provides automatic L1 (memory) + L2 (Redis) caching with:
    - Zero-configuration setup
    - Automatic promotion based on access patterns
    - Comprehensive performance metrics
    - Background maintenance tasks
    """

    _instance: Optional["TieredCacheService"] = None
    _lock = threading.Lock()

    def __new__(cls) -> "TieredCacheService":
        """Singleton pattern for global cache instance."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize tiered cache service."""
        # Prevent re-initialization of singleton
        if hasattr(self, "_initialized"):
            return

        self._initialized = True

        # Cache layers
        self.l1_cache: LRUCache = LRUCache(max_size=10000, default_ttl=1800)  # 30min for better hit rates
        self.l2_backend = RedisBackend()

        # Metrics and monitoring
        self.metrics = CacheMetrics()
        self.l1_cache.set_metrics_ref(self.metrics)

        # Background tasks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._maintenance_interval = 300  # 5 minutes
        self._shutdown_event = asyncio.Event()

        logger.info("TieredCacheService initialized")

    async def start(self):
        """Start cache service and background tasks."""
        await self.l2_backend.initialize()

        # Start background cleanup task
        if not self._cleanup_task or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._background_cleanup())

        logger.info("TieredCacheService started with background maintenance")

    async def stop(self):
        """Stop cache service and cleanup resources."""
        self._shutdown_event.set()

        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        await self.l2_backend.close()
        self.l1_cache.clear()

        logger.info("TieredCacheService stopped")

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from tiered cache.

        Flow:
        1. Try L1 memory cache (fastest)
        2. Try L2 Redis cache
        3. Return None if not found
        """
        # Try L1 first
        value = self.l1_cache.get(key)
        if value is not None:
            return value

        # Try L2 with promotion logic
        start_time = time.perf_counter()
        data = await self.l2_backend.get(key)

        if data is None:
            self.metrics.update_l2_miss((time.perf_counter() - start_time) * 1000)
            return None

        try:
            # Deserialize from L2
            cache_item: CacheItem = pickle.loads(data)

            if cache_item.is_expired:
                await self.l2_backend.delete(key)
                self.metrics.update_l2_miss((time.perf_counter() - start_time) * 1000)
                return None

            # Record access
            cache_item.access()

            # Promote to L1 if accessed enough
            promoted = False
            if cache_item.should_promote:
                self.l1_cache.set(key, cache_item.value, int(cache_item.expires_at - time.time()))
                promoted = True

            self.metrics.update_l2_hit((time.perf_counter() - start_time) * 1000, promoted)

            # Update L2 with new access count
            await self._set_l2(key, cache_item, int(cache_item.expires_at - time.time()))

            return cache_item.value

        except (pickle.PickleError, AttributeError, EOFError, ImportError) as e:
            logger.error(f"Cache deserialization error for key {key}: {str(e)}")
            await self.l2_backend.delete(key)
            self.metrics.update_l2_miss((time.perf_counter() - start_time) * 1000)
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """
        Set value in tiered cache.

        Strategy:
        - Always store in both L1 and L2 for immediate access
        - L1 provides sub-millisecond access
        - L2 provides persistence across restarts
        """
        success_l1 = self.l1_cache.set(key, value, ttl)
        success_l2 = await self._set_l2(
            key, CacheItem(value=value, created_at=time.time(), expires_at=time.time() + ttl, source="direct"), ttl
        )

        return success_l1 and success_l2

    async def delete(self, key: str) -> bool:
        """Delete key from both cache layers."""
        success_l1 = self.l1_cache.delete(key)
        success_l2 = await self.l2_backend.delete(key)

        return success_l1 or success_l2

    async def clear(self) -> bool:
        """Clear both cache layers."""
        self.l1_cache.clear()

        if self.l2_backend.enabled:
            try:
                await self.l2_backend.redis.flushdb()
                return True
            except Exception as e:
                logger.error(f"Redis clear error: {e}")
                return False

        return True

    def get_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics_data = self.metrics.get_summary()

        # Add L1 cache stats
        l1_stats = self.l1_cache.get_stats()
        metrics_data["l1_memory_cache"].update(l1_stats)

        # Add L2 status
        metrics_data["l2_redis_cache"]["enabled"] = self.l2_backend.enabled

        return metrics_data

    async def _set_l2(self, key: str, item: CacheItem, ttl: int) -> bool:
        """Set item in L2 cache with serialization."""
        if not self.l2_backend.enabled:
            return True  # Consider success if L2 not available

        try:
            data = pickle.dumps(item)
            return await self.l2_backend.set(key, data, ttl)
        except Exception as e:
            logger.error(f"L2 cache serialization error for key {key}: {e}")
            return False

    async def _background_cleanup(self):
        """Background task for cache maintenance."""
        logger.info("Background cache cleanup started")

        while not self._shutdown_event.is_set():
            try:
                # Clean expired items from L1
                expired_count = self.l1_cache.cleanup_expired()

                if expired_count > 0:
                    self.metrics.record_cleanup(expired_count)
                    logger.debug(f"Cleaned {expired_count} expired items from L1 cache")

                # Update metrics
                self.metrics.l1_size_current = len(self.l1_cache._cache)

                # Wait for next cleanup cycle
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=self._maintenance_interval)

            except asyncio.TimeoutError:
                continue  # Normal timeout, continue cleanup cycle
            except Exception as e:
                logger.error(f"Background cleanup error: {e}")
                await asyncio.sleep(60)  # Wait before retry


def tiered_cache(ttl: int = 300, key_prefix: str = ""):
    """
    Decorator for automatic function result caching using tiered cache.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        key_prefix: Optional prefix for cache keys

    Example:
        @tiered_cache(ttl=3600, key_prefix="lead_score")
        async def calculate_lead_score(lead_id: str, model_version: str):
            # Expensive ML computation
            return complex_scoring_logic(lead_id, model_version)
    """

    def decorator(func: Callable) -> Callable:
        cache_service = TieredCacheService()

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = _generate_cache_key(func, args, kwargs, key_prefix)

            # Try cache first
            cached_result = await cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_service.set(cache_key, result, ttl)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, check if we're in an async context
            try:
                asyncio.get_running_loop()
                # We're in async context, need to schedule the coroutine
                return asyncio.create_task(async_wrapper(*args, **kwargs))
            except RuntimeError:
                # No event loop, this shouldn't happen but fallback to direct execution
                return func(*args, **kwargs)

        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper

    return decorator


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict, prefix: str = "") -> str:
    """Generate deterministic cache key from function and arguments."""
    # Create base key from function name
    func_name = f"{func.__module__}.{func.__name__}"

    # Serialize arguments
    try:
        # Convert args and kwargs to strings
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))

        # Create hash for consistent key length
        content = f"{func_name}:{args_str}:{kwargs_str}"
        key_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # Combine with prefix
        if prefix:
            return f"{prefix}:{func_name}:{key_hash}"
        else:
            return f"tiered_cache:{func_name}:{key_hash}"

    except Exception as e:
        logger.warning(f"Cache key generation error: {e}")
        # Fallback to simple key
        return f"tiered_cache:{func_name}:fallback"


# Global service instance
_global_cache_service: Optional[TieredCacheService] = None


async def get_tiered_cache() -> TieredCacheService:
    """Get the global tiered cache service instance."""
    global _global_cache_service

    if _global_cache_service is None:
        _global_cache_service = TieredCacheService()
        await _global_cache_service.start()

    return _global_cache_service


# Convenience functions for direct cache access
async def cache_get(key: str) -> Optional[Any]:
    """Get value from tiered cache."""
    cache = await get_tiered_cache()
    return await cache.get(key)


async def cache_set(key: str, value: Any, ttl: int = 300) -> bool:
    """Set value in tiered cache."""
    cache = await get_tiered_cache()
    return await cache.set(key, value, ttl)


async def cache_delete(key: str) -> bool:
    """Delete value from tiered cache."""
    cache = await get_tiered_cache()
    return await cache.delete(key)


async def cache_clear() -> bool:
    """Clear tiered cache."""
    cache = await get_tiered_cache()
    return await cache.clear()


async def cache_metrics() -> Dict[str, Any]:
    """Get tiered cache performance metrics."""
    cache = await get_tiered_cache()
    return cache.get_metrics()


# Context manager for cache lifecycle
class TieredCacheContext:
    """Context manager for tiered cache lifecycle management."""

    def __init__(self):
        self.cache_service: Optional[TieredCacheService] = None

    async def __aenter__(self):
        self.cache_service = TieredCacheService()
        await self.cache_service.start()
        return self.cache_service

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.cache_service:
            await self.cache_service.stop()


# Export main interfaces
__all__ = [
    "TieredCacheService",
    "CacheMetrics",
    "CacheItem",
    "tiered_cache",
    "get_tiered_cache",
    "cache_get",
    "cache_set",
    "cache_delete",
    "cache_clear",
    "cache_metrics",
    "TieredCacheContext",
]
