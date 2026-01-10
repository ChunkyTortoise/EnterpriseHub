"""
Integration Cache Manager

Multi-layer caching system for Dashboard/GHL integration performance optimization.
Provides Redis + in-memory caching with automatic failover and performance monitoring.

Performance Targets:
- L1 cache (in-memory): <1ms
- L2 cache (Redis): <10ms
- Cache miss (database): <50ms
- Cache hit rate: >80%

Features:
- Multi-layer caching (L1: memory, L2: Redis, L3: database)
- Automatic failover on Redis connection issues
- LRU eviction for memory cache
- TTL management and expiration
- Performance metrics and monitoring
- Cache invalidation patterns
"""

import asyncio
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union, Callable
from collections import OrderedDict
from functools import wraps

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    data: Any
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: datetime = None

    def __post_init__(self):
        if self.last_accessed is None:
            self.last_accessed = self.created_at

    @property
    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() > self.expires_at

    @property
    def age_seconds(self) -> float:
        """Get age of cache entry in seconds."""
        return (datetime.now() - self.created_at).total_seconds()


@dataclass
class CacheMetrics:
    """Cache performance metrics."""
    l1_hits: int = 0
    l2_hits: int = 0
    cache_misses: int = 0
    total_requests: int = 0
    avg_l1_latency_ms: float = 0.0
    avg_l2_latency_ms: float = 0.0
    avg_miss_latency_ms: float = 0.0

    @property
    def hit_rate(self) -> float:
        """Calculate overall cache hit rate."""
        total_hits = self.l1_hits + self.l2_hits
        return total_hits / max(self.total_requests, 1)

    @property
    def l1_hit_rate(self) -> float:
        """Calculate L1 cache hit rate."""
        return self.l1_hits / max(self.total_requests, 1)

    @property
    def l2_hit_rate(self) -> float:
        """Calculate L2 cache hit rate."""
        return self.l2_hits / max(self.total_requests, 1)


class IntegrationCacheManager:
    """
    Multi-layer cache manager for integration performance.

    Provides three cache layers:
    - L1: In-memory cache (fastest, limited size)
    - L2: Redis cache (fast, shared across instances)
    - L3: Database/source (slowest, authoritative)
    """

    def __init__(
        self,
        redis_client=None,
        l1_max_size: int = 1000,
        default_ttl: int = 300  # 5 minutes
    ):
        """
        Initialize cache manager.

        Args:
            redis_client: Optional Redis client for L2 cache
            l1_max_size: Maximum number of entries in L1 cache
            default_ttl: Default TTL for cache entries (seconds)
        """
        self.redis_client = redis_client
        self.l1_max_size = l1_max_size
        self.default_ttl = default_ttl

        # L1 cache: In-memory with LRU eviction
        self._l1_cache: OrderedDict[str, CacheEntry] = OrderedDict()

        # Performance metrics
        self.metrics = CacheMetrics()

        # Cache configuration per namespace
        self._namespace_config: Dict[str, Dict[str, Any]] = {}

        logger.info(f"Integration Cache Manager initialized with L1 size={l1_max_size}, default TTL={default_ttl}s")

    async def get(
        self,
        key: str,
        namespace: str = "default",
        fallback_func: Optional[Callable] = None,
        ttl: Optional[int] = None
    ) -> Any:
        """
        Get value from cache with multi-layer fallback.

        Args:
            key: Cache key
            namespace: Cache namespace for organization
            fallback_func: Function to call on cache miss
            ttl: Time-to-live override

        Returns:
            Cached value or result of fallback_func
        """
        full_key = self._build_key(namespace, key)
        start_time = time.time()

        try:
            # Try L1 cache first
            l1_start = time.time()
            l1_result = await self._get_from_l1(full_key)

            if l1_result is not None:
                self.metrics.l1_hits += 1
                self.metrics.total_requests += 1
                self._update_latency_metric('l1', (time.time() - l1_start) * 1000)
                return l1_result

            # Try L2 cache (Redis)
            if self.redis_client:
                l2_start = time.time()
                l2_result = await self._get_from_l2(full_key)

                if l2_result is not None:
                    self.metrics.l2_hits += 1
                    self.metrics.total_requests += 1
                    self._update_latency_metric('l2', (time.time() - l2_start) * 1000)

                    # Promote to L1 cache
                    await self._set_l1(full_key, l2_result, ttl or self.default_ttl)
                    return l2_result

            # Cache miss - use fallback function
            self.metrics.cache_misses += 1
            self.metrics.total_requests += 1

            if fallback_func:
                miss_start = time.time()
                result = await self._execute_fallback(fallback_func)
                self._update_latency_metric('miss', (time.time() - miss_start) * 1000)

                # Cache the result in both layers
                await self.set(key, result, namespace, ttl)
                return result

            return None

        except Exception as e:
            logger.error(f"Error getting cache key {full_key}: {e}")
            # Fallback to direct function call on cache error
            if fallback_func:
                return await self._execute_fallback(fallback_func)
            return None

    async def set(
        self,
        key: str,
        value: Any,
        namespace: str = "default",
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache across all layers.

        Args:
            key: Cache key
            value: Value to cache
            namespace: Cache namespace
            ttl: Time-to-live override
        """
        full_key = self._build_key(namespace, key)
        cache_ttl = ttl or self.default_ttl

        try:
            # Set in both L1 and L2 caches
            await asyncio.gather(
                self._set_l1(full_key, value, cache_ttl),
                self._set_l2(full_key, value, cache_ttl),
                return_exceptions=True  # Don't fail if one cache fails
            )

        except Exception as e:
            logger.error(f"Error setting cache key {full_key}: {e}")

    async def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Delete key from all cache layers.

        Args:
            key: Cache key to delete
            namespace: Cache namespace

        Returns:
            True if key was found and deleted
        """
        full_key = self._build_key(namespace, key)

        try:
            deleted = False

            # Delete from L1
            if full_key in self._l1_cache:
                del self._l1_cache[full_key]
                deleted = True

            # Delete from L2 (Redis)
            if self.redis_client:
                redis_deleted = await self.redis_client.delete(full_key)
                if redis_deleted:
                    deleted = True

            return deleted

        except Exception as e:
            logger.error(f"Error deleting cache key {full_key}: {e}")
            return False

    async def invalidate_namespace(self, namespace: str) -> int:
        """
        Invalidate all keys in a namespace.

        Args:
            namespace: Namespace to invalidate

        Returns:
            Number of keys invalidated
        """
        try:
            pattern = f"{namespace}:*"
            invalidated = 0

            # Invalidate L1 cache
            keys_to_remove = [key for key in self._l1_cache.keys() if key.startswith(f"{namespace}:")]
            for key in keys_to_remove:
                del self._l1_cache[key]
                invalidated += 1

            # Invalidate L2 cache (Redis)
            if self.redis_client:
                # Note: In production, you'd want to use SCAN for large datasets
                redis_keys = await self.redis_client.keys(pattern)
                if redis_keys:
                    await self.redis_client.delete(*redis_keys)
                    invalidated += len(redis_keys)

            logger.info(f"Invalidated {invalidated} keys in namespace '{namespace}'")
            return invalidated

        except Exception as e:
            logger.error(f"Error invalidating namespace {namespace}: {e}")
            return 0

    async def _get_from_l1(self, key: str) -> Any:
        """Get value from L1 (in-memory) cache."""
        if key in self._l1_cache:
            entry = self._l1_cache[key]

            if entry.is_expired:
                del self._l1_cache[key]
                return None

            # Update access tracking and move to end (LRU)
            entry.hit_count += 1
            entry.last_accessed = datetime.now()
            self._l1_cache.move_to_end(key)

            return entry.data

        return None

    async def _get_from_l2(self, key: str) -> Any:
        """Get value from L2 (Redis) cache."""
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(key)
            if cached_data:
                # Parse JSON data
                if isinstance(cached_data, bytes):
                    cached_data = cached_data.decode('utf-8')

                return json.loads(cached_data)

        except Exception as e:
            logger.error(f"L2 cache get error for {key}: {e}")

        return None

    async def _set_l1(self, key: str, value: Any, ttl: int) -> None:
        """Set value in L1 (in-memory) cache."""
        try:
            # Check if we need to evict entries
            if len(self._l1_cache) >= self.l1_max_size and key not in self._l1_cache:
                # Remove least recently used entry
                self._l1_cache.popitem(last=False)

            # Create cache entry
            entry = CacheEntry(
                key=key,
                data=value,
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=ttl)
            )

            self._l1_cache[key] = entry

        except Exception as e:
            logger.error(f"L1 cache set error for {key}: {e}")

    async def _set_l2(self, key: str, value: Any, ttl: int) -> None:
        """Set value in L2 (Redis) cache."""
        if not self.redis_client:
            return

        try:
            # Serialize data
            serialized_data = json.dumps(value, default=str)

            # Set with TTL
            await self.redis_client.setex(key, ttl, serialized_data)

        except Exception as e:
            logger.error(f"L2 cache set error for {key}: {e}")

    def _build_key(self, namespace: str, key: str) -> str:
        """Build full cache key with namespace."""
        return f"{namespace}:{key}"

    async def _execute_fallback(self, fallback_func: Callable) -> Any:
        """Execute fallback function safely."""
        try:
            if asyncio.iscoroutinefunction(fallback_func):
                return await fallback_func()
            else:
                return fallback_func()
        except Exception as e:
            logger.error(f"Fallback function execution failed: {e}")
            raise

    def _update_latency_metric(self, layer: str, latency_ms: float) -> None:
        """Update latency metrics for cache layer."""
        metric_key = f'avg_{layer}_latency_ms'

        if layer == 'l1':
            hits_key = 'l1_hits'
        elif layer == 'l2':
            hits_key = 'l2_hits'
        else:
            hits_key = 'cache_misses'

        total_ops = getattr(self.metrics, hits_key)
        current_avg = getattr(self.metrics, metric_key)

        if total_ops > 0:
            new_avg = ((current_avg * (total_ops - 1)) + latency_ms) / total_ops
            setattr(self.metrics, metric_key, new_avg)

    async def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics."""
        return {
            **asdict(self.metrics),
            'l1_size': len(self._l1_cache),
            'l1_max_size': self.l1_max_size,
            'redis_connected': self.redis_client is not None
        }

    async def clear_l1_cache(self) -> int:
        """Clear L1 cache and return number of entries cleared."""
        cleared = len(self._l1_cache)
        self._l1_cache.clear()
        logger.info(f"Cleared {cleared} entries from L1 cache")
        return cleared

    async def get_cache_info(self) -> Dict[str, Any]:
        """Get detailed cache information."""
        l1_entries = []
        for key, entry in list(self._l1_cache.items()):
            l1_entries.append({
                'key': key,
                'age_seconds': entry.age_seconds,
                'hit_count': entry.hit_count,
                'expires_in': (entry.expires_at - datetime.now()).total_seconds(),
                'is_expired': entry.is_expired
            })

        return {
            'l1_cache': {
                'size': len(self._l1_cache),
                'max_size': self.l1_max_size,
                'entries': l1_entries
            },
            'l2_cache': {
                'connected': self.redis_client is not None,
                'type': 'Redis' if self.redis_client else 'None'
            },
            'metrics': await self.get_metrics()
        }


def cache_result(
    namespace: str = "default",
    ttl: int = 300,
    cache_manager: Optional[IntegrationCacheManager] = None
):
    """
    Decorator to automatically cache function results.

    Args:
        namespace: Cache namespace
        ttl: Time-to-live for cached result
        cache_manager: Cache manager instance (uses global if None)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            cache_key = f"{func.__name__}:{hash(str(args) + str(sorted(kwargs.items())))}"

            # Use provided cache manager or get global instance
            manager = cache_manager or get_integration_cache_manager()

            # Try to get from cache
            result = await manager.get(
                key=cache_key,
                namespace=namespace,
                fallback_func=lambda: func(*args, **kwargs),
                ttl=ttl
            )

            return result

        return wrapper
    return decorator


# Singleton instance
_integration_cache_manager = None


def get_integration_cache_manager(**kwargs) -> IntegrationCacheManager:
    """Get singleton integration cache manager instance."""
    global _integration_cache_manager
    if _integration_cache_manager is None:
        _integration_cache_manager = IntegrationCacheManager(**kwargs)
    return _integration_cache_manager


# Export main classes
__all__ = [
    "IntegrationCacheManager",
    "CacheEntry",
    "CacheMetrics",
    "cache_result",
    "get_integration_cache_manager"
]