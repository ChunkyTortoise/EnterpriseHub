"""
Optimized Multi-Layer Caching Service
Implements L1 (Memory) + L2 (Redis) + L3 (Database) caching strategy
"""

import asyncio
import json
import pickle
import time
import logging
from typing import Any, Optional, Dict, List, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
import hashlib

logger = logging.getLogger(__name__)

@dataclass
class CacheStats:
    """Cache performance statistics"""
    l1_hits: int = 0
    l1_misses: int = 0
    l2_hits: int = 0
    l2_misses: int = 0
    l3_hits: int = 0
    l3_misses: int = 0
    evictions: int = 0
    total_requests: int = 0
    avg_retrieval_time_ms: float = 0

    @property
    def l1_hit_rate(self) -> float:
        total = self.l1_hits + self.l1_misses
        return self.l1_hits / max(total, 1)

    @property
    def l2_hit_rate(self) -> float:
        total = self.l2_hits + self.l2_misses
        return self.l2_hits / max(total, 1)

    @property
    def overall_hit_rate(self) -> float:
        hits = self.l1_hits + self.l2_hits + self.l3_hits
        total = hits + self.l3_misses
        return hits / max(total, 1)

@dataclass
class CacheItem:
    """Cache item with metadata"""
    value: Any
    created_at: float
    ttl: int
    access_count: int = 0
    last_accessed: float = field(default_factory=time.time)
    size_bytes: int = 0

    def is_expired(self) -> bool:
        return time.time() > (self.created_at + self.ttl)

    def mark_accessed(self):
        self.access_count += 1
        self.last_accessed = time.time()

class L1MemoryCache:
    """Level 1: In-memory cache with LRU eviction"""

    def __init__(self, max_size: int = 1000, max_memory_mb: int = 100):
        self.max_size = max_size
        self.max_memory_bytes = max_memory_mb * 1024 * 1024
        self.cache: Dict[str, CacheItem] = {}
        self.access_order: List[str] = []  # LRU tracking
        self.current_memory = 0
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        async with self.lock:
            if key not in self.cache:
                return None
            
            item = self.cache[key]
            if item.is_expired():
                await self._remove_item(key)
                return None
            
            # Update LRU order
            self.access_order.remove(key)
            self.access_order.append(key)
            item.mark_accessed()
            
            return item.value

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        async with self.lock:
            # Calculate item size
            try:
                size_bytes = len(pickle.dumps(value))
            except:
                size_bytes = 1024  # Default estimate

            # Check memory limits
            if size_bytes > self.max_memory_bytes:
                logger.warning(f"Item too large for L1 cache: {size_bytes} bytes")
                return False

            # Remove existing item if present
            if key in self.cache:
                await self._remove_item(key)

            # Evict items if necessary
            while (len(self.cache) >= self.max_size or 
                   self.current_memory + size_bytes > self.max_memory_bytes):
                await self._evict_lru()

            # Add new item
            item = CacheItem(
                value=value,
                created_at=time.time(),
                ttl=ttl,
                size_bytes=size_bytes
            )
            
            self.cache[key] = item
            self.access_order.append(key)
            self.current_memory += size_bytes
            
            return True

    async def delete(self, key: str) -> bool:
        async with self.lock:
            if key in self.cache:
                await self._remove_item(key)
                return True
            return False

    async def clear(self) -> bool:
        async with self.lock:
            self.cache.clear()
            self.access_order.clear()
            self.current_memory = 0
            return True

    async def _remove_item(self, key: str):
        """Remove item and update memory tracking"""
        if key in self.cache:
            item = self.cache[key]
            self.current_memory -= item.size_bytes
            del self.cache[key]
            if key in self.access_order:
                self.access_order.remove(key)

    async def _evict_lru(self):
        """Evict least recently used item"""
        if self.access_order:
            lru_key = self.access_order[0]
            await self._remove_item(lru_key)

    def get_stats(self) -> Dict[str, Any]:
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'memory_used_mb': self.current_memory / (1024 * 1024),
            'memory_limit_mb': self.max_memory_bytes / (1024 * 1024),
            'memory_usage_percent': (self.current_memory / self.max_memory_bytes) * 100
        }

class L2RedisCache:
    """Level 2: Redis cache with connection pooling"""

    def __init__(self, redis_url: str, max_connections: int = 50):
        self.redis_url = redis_url
        self.redis = None
        self.enabled = False
        self.max_connections = max_connections
        self._initialize_redis()

    def _initialize_redis(self):
        try:
            import redis.asyncio as redis
            from redis.asyncio.connection import ConnectionPool

            self.connection_pool = ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=2,  # Fast timeout for cache
                socket_connect_timeout=2,
                decode_responses=False
            )

            self.redis = redis.Redis(connection_pool=self.connection_pool)
            self.enabled = True
            logger.info("L2 Redis cache initialized")
        except Exception as e:
            logger.warning(f"Redis cache unavailable: {e}")
            self.enabled = False

    async def get(self, key: str) -> Optional[Any]:
        if not self.enabled:
            return None
        
        try:
            # Add prefix for namespacing
            cache_key = f"l2:{key}"
            data = await self.redis.get(cache_key)
            if data:
                return pickle.loads(data)
            return None
        except Exception as e:
            logger.error(f"L2 cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        if not self.enabled:
            return False
        
        try:
            cache_key = f"l2:{key}"
            data = pickle.dumps(value)
            await self.redis.set(cache_key, data, ex=ttl)
            return True
        except Exception as e:
            logger.error(f"L2 cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        if not self.enabled:
            return False
        
        try:
            cache_key = f"l2:{key}"
            await self.redis.delete(cache_key)
            return True
        except Exception as e:
            logger.error(f"L2 cache delete error: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Batch get operation for efficiency"""
        if not self.enabled:
            return {}
        
        try:
            cache_keys = [f"l2:{key}" for key in keys]
            pipeline = self.redis.pipeline()
            for cache_key in cache_keys:
                pipeline.get(cache_key)
            
            results = await pipeline.execute()
            
            output = {}
            for key, data in zip(keys, results):
                if data:
                    try:
                        output[key] = pickle.loads(data)
                    except:
                        pass  # Skip corrupted entries
            
            return output
        except Exception as e:
            logger.error(f"L2 cache get_many error: {e}")
            return {}

    async def set_many(self, items: Dict[str, Tuple[Any, int]]) -> bool:
        """Batch set operation for efficiency"""
        if not self.enabled:
            return False
        
        try:
            pipeline = self.redis.pipeline()
            for key, (value, ttl) in items.items():
                cache_key = f"l2:{key}"
                data = pickle.dumps(value)
                pipeline.set(cache_key, data, ex=ttl)
            
            await pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"L2 cache set_many error: {e}")
            return False

class L3DatabaseCache:
    """Level 3: Database/computed values (fallback)"""

    def __init__(self):
        self.compute_functions: Dict[str, Any] = {}

    def register_compute_function(self, pattern: str, func):
        """Register function to compute values for cache misses"""
        self.compute_functions[pattern] = func

    async def get(self, key: str) -> Optional[Any]:
        """Compute value using registered functions"""
        for pattern, func in self.compute_functions.items():
            if pattern in key:
                try:
                    return await func(key)
                except Exception as e:
                    logger.error(f"L3 compute error for {key}: {e}")
        return None

class OptimizedCacheService:
    """
    Multi-layer cache service with intelligent routing
    """

    def __init__(self, redis_url: Optional[str] = None):
        # Initialize cache layers
        self.l1_cache = L1MemoryCache(max_size=1000, max_memory_mb=100)
        self.l2_cache = L2RedisCache(redis_url) if redis_url else None
        self.l3_cache = L3DatabaseCache()
        
        # Performance tracking
        self.stats = CacheStats()
        self.lock = asyncio.Lock()

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback through layers"""
        start_time = time.time()
        
        try:
            # Try L1 (Memory) first
            value = await self.l1_cache.get(key)
            if value is not None:
                await self._update_stats('l1_hit', start_time)
                return value
            
            await self._update_stats('l1_miss')

            # Try L2 (Redis) second
            if self.l2_cache:
                value = await self.l2_cache.get(key)
                if value is not None:
                    # Backfill L1 with shorter TTL
                    await self.l1_cache.set(key, value, ttl=min(300, 60))
                    await self._update_stats('l2_hit', start_time)
                    return value
                
                await self._update_stats('l2_miss')

            # Try L3 (Compute) last
            value = await self.l3_cache.get(key)
            if value is not None:
                # Backfill L2 and L1
                await self.set(key, value, ttl=300)
                await self._update_stats('l3_hit', start_time)
                return value
            
            await self._update_stats('l3_miss', start_time)
            return None

        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None

    async def set(self, key: str, value: Any, ttl: int = 300) -> bool:
        """Set value in all appropriate cache layers"""
        try:
            success = True
            
            # Set in L1 (Memory) with shorter TTL
            l1_ttl = min(ttl, 300)  # Max 5 minutes in memory
            await self.l1_cache.set(key, value, ttl=l1_ttl)
            
            # Set in L2 (Redis) if available
            if self.l2_cache:
                redis_success = await self.l2_cache.set(key, value, ttl=ttl)
                success = success and redis_success
            
            return success

        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False

    async def delete(self, key: str) -> bool:
        """Delete from all cache layers"""
        try:
            l1_success = await self.l1_cache.delete(key)
            l2_success = await self.l2_cache.delete(key) if self.l2_cache else True
            
            return l1_success or l2_success

        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False

    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """Efficient batch get operation"""
        results = {}
        missing_keys = []

        # Check L1 first for all keys
        for key in keys:
            value = await self.l1_cache.get(key)
            if value is not None:
                results[key] = value
                self.stats.l1_hits += 1
            else:
                missing_keys.append(key)
                self.stats.l1_misses += 1

        # Check L2 for missing keys
        if missing_keys and self.l2_cache:
            l2_results = await self.l2_cache.get_many(missing_keys)
            for key, value in l2_results.items():
                results[key] = value
                # Backfill L1
                await self.l1_cache.set(key, value, ttl=60)
                self.stats.l2_hits += 1
            
            # Update missing keys
            missing_keys = [key for key in missing_keys if key not in l2_results]
            self.stats.l2_misses += len(missing_keys)

        return results

    async def set_many(self, items: Dict[str, Tuple[Any, int]]) -> bool:
        """Efficient batch set operation"""
        try:
            # Set in L1
            for key, (value, ttl) in items.items():
                l1_ttl = min(ttl, 300)
                await self.l1_cache.set(key, value, ttl=l1_ttl)

            # Set in L2 if available
            if self.l2_cache:
                await self.l2_cache.set_many(items)

            return True

        except Exception as e:
            logger.error(f"Batch cache set error: {e}")
            return False

    def register_compute_function(self, pattern: str, func):
        """Register function to compute cache misses"""
        self.l3_cache.register_compute_function(pattern, func)

    async def invalidate_pattern(self, pattern: str):
        """Invalidate all keys matching pattern"""
        # For L1, we need to check all keys
        keys_to_remove = []
        for key in self.l1_cache.cache.keys():
            if pattern in key:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            await self.l1_cache.delete(key)

        # For L2 (Redis), we'd need a more sophisticated approach
        # This is a simplified version
        if self.l2_cache and self.l2_cache.enabled:
            try:
                # In production, you'd use Redis SCAN with pattern matching
                logger.info(f"Pattern invalidation requested: {pattern}")
            except Exception as e:
                logger.error(f"Pattern invalidation failed: {e}")

    async def warm_cache(self, items: Dict[str, Tuple[Any, int]]):
        """Warm cache with frequently accessed items"""
        logger.info(f"Warming cache with {len(items)} items")
        await self.set_many(items)

    async def _update_stats(self, stat_type: str, start_time: Optional[float] = None):
        """Update performance statistics"""
        async with self.lock:
            if stat_type == 'l1_hit':
                self.stats.l1_hits += 1
            elif stat_type == 'l1_miss':
                self.stats.l1_misses += 1
            elif stat_type == 'l2_hit':
                self.stats.l2_hits += 1
            elif stat_type == 'l2_miss':
                self.stats.l2_misses += 1
            elif stat_type == 'l3_hit':
                self.stats.l3_hits += 1
            elif stat_type == 'l3_miss':
                self.stats.l3_misses += 1

            self.stats.total_requests += 1

            if start_time:
                retrieval_time_ms = (time.time() - start_time) * 1000
                current_avg = self.stats.avg_retrieval_time_ms
                total = self.stats.total_requests
                self.stats.avg_retrieval_time_ms = (
                    (current_avg * (total - 1) + retrieval_time_ms) / total
                )

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed cache performance statistics"""
        return {
            'cache_stats': {
                'l1_hit_rate': self.stats.l1_hit_rate,
                'l2_hit_rate': self.stats.l2_hit_rate,
                'overall_hit_rate': self.stats.overall_hit_rate,
                'avg_retrieval_time_ms': self.stats.avg_retrieval_time_ms,
                'total_requests': self.stats.total_requests
            },
            'l1_stats': self.l1_cache.get_stats(),
            'layer_breakdown': {
                'l1_hits': self.stats.l1_hits,
                'l1_misses': self.stats.l1_misses,
                'l2_hits': self.stats.l2_hits,
                'l2_misses': self.stats.l2_misses,
                'l3_hits': self.stats.l3_hits,
                'l3_misses': self.stats.l3_misses
            }
        }

# Singleton instance
_optimized_cache = None

def get_optimized_cache_service(redis_url: Optional[str] = None) -> OptimizedCacheService:
    """Get singleton optimized cache service"""
    global _optimized_cache
    if _optimized_cache is None:
        _optimized_cache = OptimizedCacheService(redis_url)
    return _optimized_cache