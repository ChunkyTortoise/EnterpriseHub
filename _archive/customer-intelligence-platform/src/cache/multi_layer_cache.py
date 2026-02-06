"""
Multi-Layer Caching System for Customer Intelligence Platform.

Implements a sophisticated caching hierarchy:
- L1: In-memory cache (fastest, smallest)
- L2: Redis cache (fast, distributed)
- L3: Application-level cache with compression
- Smart cache warming and invalidation
- Cache analytics and optimization
"""

import asyncio
import time
import logging
import pickle
import gzip
import json
import weakref
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple, Union, Callable, AsyncIterator
from dataclasses import dataclass, field
from contextlib import asynccontextmanager
from collections import OrderedDict, defaultdict
from functools import wraps
import hashlib
import threading

from ..core.optimized_redis_config import OptimizedRedisManager

logger = logging.getLogger(__name__)

@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    key: str
    value: Any
    created_at: datetime
    accessed_at: datetime
    expires_at: Optional[datetime]
    hit_count: int = 0
    size_bytes: int = 0
    level: str = ""  # L1, L2, L3
    compressed: bool = False

@dataclass
class CacheStats:
    """Cache performance statistics."""
    hits: int = 0
    misses: int = 0
    evictions: int = 0
    memory_usage_bytes: int = 0
    avg_access_time_ms: float = 0
    cache_levels: Dict[str, int] = field(default_factory=dict)

class LRUCache:
    """Thread-safe LRU cache implementation with size limits."""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.current_memory_bytes = 0

        self.cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self.lock = threading.RLock()

        # Statistics
        self.stats = CacheStats()

    def get(self, key: str) -> Optional[CacheEntry]:
        """Get item from cache and update access time."""
        with self.lock:
            if key in self.cache:
                entry = self.cache[key]

                # Check expiration
                if entry.expires_at and datetime.utcnow() > entry.expires_at:
                    self._remove_entry(key)
                    self.stats.misses += 1
                    return None

                # Move to end (most recently used)
                self.cache.move_to_end(key)
                entry.accessed_at = datetime.utcnow()
                entry.hit_count += 1

                self.stats.hits += 1
                return entry

            self.stats.misses += 1
            return None

    def put(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> bool:
        """Put item in cache with optional TTL."""
        with self.lock:
            # Calculate size
            try:
                size = len(pickle.dumps(value))
            except:
                size = len(str(value).encode())

            # Check if we have space
            if (len(self.cache) >= self.max_size or
                self.current_memory_bytes + size > self.max_memory_bytes):
                self._evict_lru()

            # Create entry
            now = datetime.utcnow()
            expires_at = now + timedelta(seconds=ttl_seconds) if ttl_seconds else None

            entry = CacheEntry(
                key=key,
                value=value,
                created_at=now,
                accessed_at=now,
                expires_at=expires_at,
                size_bytes=size,
                level="L1"
            )

            # Remove old entry if exists
            if key in self.cache:
                self._remove_entry(key)

            # Add new entry
            self.cache[key] = entry
            self.current_memory_bytes += size

            return True

    def remove(self, key: str) -> bool:
        """Remove item from cache."""
        with self.lock:
            if key in self.cache:
                self._remove_entry(key)
                return True
            return False

    def clear(self):
        """Clear all items from cache."""
        with self.lock:
            self.cache.clear()
            self.current_memory_bytes = 0
            self.stats = CacheStats()

    def _remove_entry(self, key: str):
        """Remove entry and update memory usage."""
        entry = self.cache.pop(key, None)
        if entry:
            self.current_memory_bytes -= entry.size_bytes

    def _evict_lru(self):
        """Evict least recently used items."""
        evicted_count = 0
        target_size = min(self.max_size // 2, self.max_size - 10)
        target_memory = self.max_memory_bytes * 0.8  # 80% of max

        while (len(self.cache) > target_size or
               self.current_memory_bytes > target_memory):
            if not self.cache:
                break

            # Remove oldest item
            key, entry = self.cache.popitem(last=False)
            self.current_memory_bytes -= entry.size_bytes
            evicted_count += 1

        self.stats.evictions += evicted_count
        logger.debug(f"Evicted {evicted_count} items from L1 cache")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        with self.lock:
            total_requests = self.stats.hits + self.stats.misses
            hit_rate = self.stats.hits / total_requests if total_requests > 0 else 0

            return {
                "hits": self.stats.hits,
                "misses": self.stats.misses,
                "hit_rate": hit_rate,
                "evictions": self.stats.evictions,
                "memory_usage_mb": self.current_memory_bytes / (1024 * 1024),
                "item_count": len(self.cache),
                "max_size": self.max_size
            }

class CacheKeyGenerator:
    """Intelligent cache key generation with automatic versioning."""

    def __init__(self, version: str = "v1"):
        self.version = version
        self.namespace_versions: Dict[str, str] = {}

    def generate_key(
        self,
        namespace: str,
        identifier: Union[str, Dict[str, Any]],
        tags: Optional[List[str]] = None
    ) -> str:
        """Generate cache key with automatic versioning."""
        # Handle dictionary identifiers
        if isinstance(identifier, dict):
            # Sort keys for consistency
            id_str = "|".join(f"{k}:{v}" for k, v in sorted(identifier.items()))
        else:
            id_str = str(identifier)

        # Include tags
        tag_str = ""
        if tags:
            tag_str = "|tags:" + "|".join(sorted(tags))

        # Get namespace version
        namespace_version = self.namespace_versions.get(namespace, "1")

        # Generate final key
        key_parts = [
            self.version,
            namespace,
            namespace_version,
            id_str,
            tag_str
        ]

        key = ":".join(filter(None, key_parts))
        return hashlib.md5(key.encode()).hexdigest()[:32]

    def invalidate_namespace(self, namespace: str):
        """Invalidate all keys in a namespace by incrementing version."""
        current_version = int(self.namespace_versions.get(namespace, "1"))
        self.namespace_versions[namespace] = str(current_version + 1)
        logger.info(f"Invalidated namespace '{namespace}' - new version: {current_version + 1}")

class MultiLayerCache:
    """Multi-layer caching system with intelligent promotion/demotion."""

    def __init__(
        self,
        redis_manager: OptimizedRedisManager,
        l1_max_size: int = 1000,
        l1_max_memory_mb: int = 100,
        l2_default_ttl: int = 3600,
        l3_default_ttl: int = 7200,
        enable_compression: bool = True,
        enable_analytics: bool = True
    ):
        self.redis_manager = redis_manager
        self.l2_default_ttl = l2_default_ttl
        self.l3_default_ttl = l3_default_ttl
        self.enable_compression = enable_compression
        self.enable_analytics = enable_analytics

        # Cache layers
        self.l1_cache = LRUCache(l1_max_size, l1_max_memory_mb)

        # Key management
        self.key_generator = CacheKeyGenerator()

        # Analytics
        self.access_patterns: Dict[str, List[datetime]] = defaultdict(list)
        self.promotion_stats: Dict[str, int] = defaultdict(int)
        self.global_stats = CacheStats()

        # Background tasks
        self.background_tasks: List[asyncio.Task] = []
        self._stop_background_tasks = False

    async def start_background_tasks(self):
        """Start background cache management tasks."""
        self.background_tasks = [
            asyncio.create_task(self._cache_warming_task()),
            asyncio.create_task(self._analytics_aggregation_task()),
            asyncio.create_task(self._cleanup_task())
        ]
        logger.info("Multi-layer cache background tasks started")

    async def stop_background_tasks(self):
        """Stop background tasks."""
        self._stop_background_tasks = True
        for task in self.background_tasks:
            task.cancel()
        await asyncio.gather(*self.background_tasks, return_exceptions=True)
        logger.info("Multi-layer cache background tasks stopped")

    async def get(
        self,
        key: str,
        default: Any = None,
        promote_to_l1: bool = True
    ) -> Any:
        """Get item from cache with automatic layer promotion."""
        start_time = time.perf_counter()

        try:
            # Try L1 first
            l1_entry = self.l1_cache.get(key)
            if l1_entry:
                self._record_access(key, "L1", time.perf_counter() - start_time)
                return l1_entry.value

            # Try L2 (Redis)
            l2_value = await self.redis_manager.get_with_optimization(key, pool='cache')
            if l2_value is not None:
                # Deserialize if needed
                if isinstance(l2_value, dict) and l2_value.get('_compressed'):
                    value = self._decompress_value(l2_value['data'])
                else:
                    value = l2_value

                # Promote to L1 if requested and frequently accessed
                if promote_to_l1 and self._should_promote_to_l1(key):
                    self.l1_cache.put(key, value, ttl_seconds=300)  # 5 min in L1
                    self.promotion_stats["L2_to_L1"] += 1

                self._record_access(key, "L2", time.perf_counter() - start_time)
                return value

            # Try L3 (Application cache with longer TTL)
            l3_key = f"l3:{key}"
            l3_value = await self.redis_manager.get_with_optimization(l3_key, pool='main')
            if l3_value is not None:
                # Decompress if needed
                if isinstance(l3_value, dict) and l3_value.get('_compressed'):
                    value = self._decompress_value(l3_value['data'])
                else:
                    value = l3_value

                # Consider promotion to L2
                if self._should_promote_to_l2(key):
                    await self.set_l2(key, value, ttl_seconds=self.l2_default_ttl)
                    self.promotion_stats["L3_to_L2"] += 1

                self._record_access(key, "L3", time.perf_counter() - start_time)
                return value

            # Cache miss
            self.global_stats.misses += 1
            self._record_access(key, "MISS", time.perf_counter() - start_time)
            return default

        except Exception as e:
            logger.error(f"Error getting from cache: {e}")
            return default

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        level: str = "auto"
    ) -> bool:
        """Set item in appropriate cache level."""
        try:
            if level == "auto":
                level = self._determine_optimal_level(key, value)

            if level == "L1" or level == "auto":
                success = self.l1_cache.put(key, value, ttl_seconds or 300)
                if success:
                    self.global_stats.cache_levels["L1"] = self.global_stats.cache_levels.get("L1", 0) + 1

            if level == "L2" or level == "auto":
                await self.set_l2(key, value, ttl_seconds or self.l2_default_ttl)

            if level == "L3":
                await self.set_l3(key, value, ttl_seconds or self.l3_default_ttl)

            return True

        except Exception as e:
            logger.error(f"Error setting cache: {e}")
            return False

    async def set_l2(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set item in L2 cache (Redis) with optional compression."""
        try:
            # Compress if beneficial
            if self.enable_compression and self._should_compress(value):
                compressed_data = self._compress_value(value)
                cache_value = {"_compressed": True, "data": compressed_data}
            else:
                cache_value = value

            await self.redis_manager.set_with_optimization(
                key, cache_value, ttl=ttl_seconds, pool='cache'
            )

            self.global_stats.cache_levels["L2"] = self.global_stats.cache_levels.get("L2", 0) + 1
            return True

        except Exception as e:
            logger.error(f"Error setting L2 cache: {e}")
            return False

    async def set_l3(self, key: str, value: Any, ttl_seconds: int) -> bool:
        """Set item in L3 cache with compression."""
        try:
            l3_key = f"l3:{key}"

            # Always compress L3 data
            compressed_data = self._compress_value(value)
            cache_value = {"_compressed": True, "data": compressed_data}

            await self.redis_manager.set_with_optimization(
                l3_key, cache_value, ttl=ttl_seconds, pool='main'
            )

            self.global_stats.cache_levels["L3"] = self.global_stats.cache_levels.get("L3", 0) + 1
            return True

        except Exception as e:
            logger.error(f"Error setting L3 cache: {e}")
            return False

    async def delete(self, key: str, all_levels: bool = True) -> bool:
        """Delete item from cache levels."""
        success = True

        try:
            # L1
            self.l1_cache.remove(key)

            if all_levels:
                # L2
                redis_client = await self.redis_manager._get_redis()
                await redis_client.delete(key)

                # L3
                l3_key = f"l3:{key}"
                await redis_client.delete(l3_key)

            return success

        except Exception as e:
            logger.error(f"Error deleting from cache: {e}")
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern."""
        try:
            redis_client = await self.redis_manager._get_redis()

            # Find matching keys
            keys = []
            cursor = 0

            while True:
                cursor, batch_keys = await redis_client.scan(
                    cursor=cursor, match=pattern, count=100
                )
                keys.extend(batch_keys)

                if cursor == 0:
                    break

            # Delete keys
            if keys:
                await redis_client.delete(*keys)

                # Also delete from L1
                for key in keys:
                    self.l1_cache.remove(key)

            logger.info(f"Invalidated {len(keys)} keys matching pattern: {pattern}")
            return len(keys)

        except Exception as e:
            logger.error(f"Error invalidating pattern: {e}")
            return 0

    def _should_compress(self, value: Any) -> bool:
        """Determine if value should be compressed."""
        if not self.enable_compression:
            return False

        try:
            # Estimate size
            if isinstance(value, (str, bytes)):
                size = len(value.encode() if isinstance(value, str) else value)
            else:
                size = len(pickle.dumps(value))

            # Compress if larger than 1KB
            return size > 1024

        except:
            return False

    def _compress_value(self, value: Any) -> bytes:
        """Compress value for storage."""
        try:
            serialized = pickle.dumps(value)
            compressed = gzip.compress(serialized, compresslevel=6)
            return compressed
        except Exception as e:
            logger.warning(f"Compression failed: {e}")
            return pickle.dumps(value)

    def _decompress_value(self, compressed_data: bytes) -> Any:
        """Decompress value from storage."""
        try:
            if isinstance(compressed_data, str):
                compressed_data = compressed_data.encode('latin-1')

            decompressed = gzip.decompress(compressed_data)
            return pickle.loads(decompressed)
        except Exception as e:
            logger.warning(f"Decompression failed: {e}")
            return pickle.loads(compressed_data)

    def _determine_optimal_level(self, key: str, value: Any) -> str:
        """Determine optimal cache level for a key-value pair."""
        # Size-based logic
        try:
            size = len(pickle.dumps(value))

            # Small, frequently accessed items -> L1
            if size < 10 * 1024:  # < 10KB
                return "L1"

            # Medium items -> L2
            elif size < 100 * 1024:  # < 100KB
                return "L2"

            # Large items -> L3
            else:
                return "L3"

        except:
            return "L2"  # Default to L2

    def _should_promote_to_l1(self, key: str) -> bool:
        """Check if key should be promoted to L1 based on access patterns."""
        if not self.enable_analytics:
            return True

        recent_accesses = [
            access_time for access_time in self.access_patterns.get(key, [])
            if datetime.utcnow() - access_time < timedelta(minutes=5)
        ]

        # Promote if accessed multiple times in last 5 minutes
        return len(recent_accesses) >= 3

    def _should_promote_to_l2(self, key: str) -> bool:
        """Check if key should be promoted to L2 based on access patterns."""
        if not self.enable_analytics:
            return True

        recent_accesses = [
            access_time for access_time in self.access_patterns.get(key, [])
            if datetime.utcnow() - access_time < timedelta(hours=1)
        ]

        # Promote if accessed multiple times in last hour
        return len(recent_accesses) >= 2

    def _record_access(self, key: str, level: str, duration: float):
        """Record cache access for analytics."""
        if not self.enable_analytics:
            return

        now = datetime.utcnow()
        self.access_patterns[key].append(now)

        # Keep only recent access times (last 24 hours)
        cutoff_time = now - timedelta(hours=24)
        self.access_patterns[key] = [
            t for t in self.access_patterns[key] if t >= cutoff_time
        ]

        # Update global stats
        if level == "MISS":
            self.global_stats.misses += 1
        else:
            self.global_stats.hits += 1

        # Record access time
        access_times = getattr(self.global_stats, '_access_times', [])
        access_times.append(duration * 1000)  # Convert to ms

        # Keep only recent access times
        if len(access_times) > 1000:
            access_times = access_times[-1000:]

        self.global_stats._access_times = access_times
        self.global_stats.avg_access_time_ms = sum(access_times) / len(access_times)

    async def _cache_warming_task(self):
        """Background task to warm cache with frequently accessed data."""
        while not self._stop_background_tasks:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes

                # Identify hot keys that should be warmed
                hot_keys = []
                for key, accesses in self.access_patterns.items():
                    # Keys accessed more than 10 times in last hour
                    recent_accesses = [
                        t for t in accesses
                        if datetime.utcnow() - t < timedelta(hours=1)
                    ]

                    if len(recent_accesses) > 10:
                        hot_keys.append(key)

                # Warm L1 cache with hot keys from L2
                for key in hot_keys[:20]:  # Limit to top 20
                    if not self.l1_cache.get(key):  # Not in L1
                        l2_value = await self.redis_manager.get_with_optimization(key, pool='cache')
                        if l2_value is not None:
                            self.l1_cache.put(key, l2_value, ttl_seconds=600)

                if hot_keys:
                    logger.debug(f"Warmed {len(hot_keys)} hot keys in L1 cache")

            except Exception as e:
                logger.error(f"Error in cache warming task: {e}")

    async def _analytics_aggregation_task(self):
        """Background task to aggregate cache analytics."""
        while not self._stop_background_tasks:
            try:
                await asyncio.sleep(60)  # Run every minute

                # Clean old access patterns
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                keys_to_remove = []

                for key, accesses in self.access_patterns.items():
                    recent_accesses = [t for t in accesses if t >= cutoff_time]

                    if recent_accesses:
                        self.access_patterns[key] = recent_accesses
                    else:
                        keys_to_remove.append(key)

                # Remove keys with no recent accesses
                for key in keys_to_remove:
                    del self.access_patterns[key]

            except Exception as e:
                logger.error(f"Error in analytics aggregation task: {e}")

    async def _cleanup_task(self):
        """Background task to cleanup expired cache entries."""
        while not self._stop_background_tasks:
            try:
                await asyncio.sleep(3600)  # Run every hour

                # Cleanup L1 expired entries (handled automatically by LRU)
                # L2 and L3 cleanup handled by Redis TTL

                logger.debug("Cache cleanup completed")

            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    async def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive cache statistics."""
        l1_stats = self.l1_cache.get_stats()
        redis_stats = await self.redis_manager.get_performance_metrics()

        total_requests = self.global_stats.hits + self.global_stats.misses
        hit_rate = self.global_stats.hits / total_requests if total_requests > 0 else 0

        return {
            "global": {
                "total_requests": total_requests,
                "hit_rate": hit_rate,
                "avg_access_time_ms": self.global_stats.avg_access_time_ms,
                "cache_levels": self.global_stats.cache_levels,
                "promotion_stats": dict(self.promotion_stats)
            },
            "l1_cache": l1_stats,
            "l2_cache": {
                "redis_stats": redis_stats,
                "default_ttl": self.l2_default_ttl
            },
            "l3_cache": {
                "default_ttl": self.l3_default_ttl,
                "compression_enabled": self.enable_compression
            },
            "analytics": {
                "active_keys": len(self.access_patterns),
                "analytics_enabled": self.enable_analytics
            },
            "timestamp": datetime.utcnow().isoformat()
        }

# Decorator for automatic caching
def cached(
    ttl_seconds: int = 300,
    key_prefix: str = "",
    level: str = "auto",
    cache_instance: Optional[MultiLayerCache] = None
):
    """Decorator for automatic function result caching."""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            if not cache_instance:
                return await func(*args, **kwargs)

            # Generate cache key
            key_data = {
                "function": func.__name__,
                "args": str(args),
                "kwargs": sorted(kwargs.items()) if kwargs else []
            }

            cache_key = cache_instance.key_generator.generate_key(
                namespace=key_prefix or func.__module__,
                identifier=key_data
            )

            # Try to get from cache
            cached_result = await cache_instance.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = await func(*args, **kwargs)
            await cache_instance.set(cache_key, result, ttl_seconds, level)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we'll need to handle differently
            return func(*args, **kwargs)

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator

# Context manager for cache transactions
@asynccontextmanager
async def cache_transaction(cache: MultiLayerCache, keys: List[str]):
    """Context manager for transactional cache operations."""
    # Store original values
    original_values = {}
    for key in keys:
        original_values[key] = await cache.get(key)

    try:
        yield cache
    except Exception:
        # Rollback on error
        for key, value in original_values.items():
            if value is not None:
                await cache.set(key, value)
            else:
                await cache.delete(key)
        raise