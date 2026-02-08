"""
Optimized Multi-Layer Caching Service
Implements L1 (Memory) + L2 (Redis) + L3 (Database) caching strategy

Performance Targets:
- >90% cache hit rate
- <5ms average L1 cache response time
- <20ms average L2 cache response time
- Intelligent cache warming for high-traffic data
- Priority-based TTL management
- Batch operations for efficiency

Author: EnterpriseHub AI Performance Engineering
Version: 2.0.0 (Performance Optimized)
Last Updated: 2026-01-18
"""

import asyncio
import hashlib
import json
import logging
import pickle
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CachePriority(Enum):
    """Cache priority levels for TTL adjustment"""

    CRITICAL = "critical"  # 2x TTL - Business critical data
    HIGH = "high"  # 1.5x TTL - Frequently accessed
    NORMAL = "normal"  # 1x TTL - Standard data
    LOW = "low"  # 0.5x TTL - Rarely needed

    @classmethod
    def get_multiplier(cls, priority: str) -> float:
        multipliers = {
            "critical": 2.0,
            "high": 1.5,
            "normal": 1.0,
            "low": 0.5,
        }
        return multipliers.get(priority, 1.0)


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
        # Fix race condition: Initialize lock in constructor
        self._lock = asyncio.Lock()

    async def _get_lock(self) -> asyncio.Lock:
        # Lock is now always initialized in __init__
        return self._lock

    async def get(self, key: str) -> Optional[Any]:
        lock = await self._get_lock()
        async with lock:
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
        lock = await self._get_lock()
        async with lock:
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
            while len(self.cache) >= self.max_size or self.current_memory + size_bytes > self.max_memory_bytes:
                await self._evict_lru()

            # Add new item
            item = CacheItem(value=value, created_at=time.time(), ttl=ttl, size_bytes=size_bytes)

            self.cache[key] = item
            self.access_order.append(key)
            self.current_memory += size_bytes

            return True

    async def delete(self, key: str) -> bool:
        lock = await self._get_lock()
        async with lock:
            if key in self.cache:
                await self._remove_item(key)
                return True
            return False

    async def clear(self) -> bool:
        lock = await self._get_lock()
        async with lock:
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
            "size": len(self.cache),
            "max_size": self.max_size,
            "memory_used_mb": self.current_memory / (1024 * 1024),
            "memory_limit_mb": self.max_memory_bytes / (1024 * 1024),
            "memory_usage_percent": (self.current_memory / self.max_memory_bytes) * 100,
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
                decode_responses=False,
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
        # Fix race condition: Initialize lock in constructor
        self._lock = asyncio.Lock()

    async def _get_lock(self) -> asyncio.Lock:
        # Lock is now always initialized in __init__
        return self._lock

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache with fallback through layers"""
        start_time = time.time()

        try:
            # Try L1 (Memory) first
            value = await self.l1_cache.get(key)
            if value is not None:
                await self._update_stats("l1_hit", start_time)
                return value

            await self._update_stats("l1_miss")

            # Try L2 (Redis) second
            if self.l2_cache:
                value = await self.l2_cache.get(key)
                if value is not None:
                    # Backfill L1 with shorter TTL
                    await self.l1_cache.set(key, value, ttl=min(300, 60))
                    await self._update_stats("l2_hit", start_time)
                    return value

                await self._update_stats("l2_miss")

            # Try L3 (Compute) last
            value = await self.l3_cache.get(key)
            if value is not None:
                # Backfill L2 and L1
                await self.set(key, value, ttl=300)
                await self._update_stats("l3_hit", start_time)
                return value

            await self._update_stats("l3_miss", start_time)
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
                await self._update_stats("l1_hit")
            else:
                missing_keys.append(key)
                await self._update_stats("l1_miss")

        # Check L2 for missing keys
        if missing_keys and self.l2_cache:
            l2_results = await self.l2_cache.get_many(missing_keys)
            for key, value in l2_results.items():
                results[key] = value
                # Backfill L1
                await self.l1_cache.set(key, value, ttl=60)
                await self._update_stats("l2_hit")

            # Update missing keys
            missing_keys = [key for key in missing_keys if key not in l2_results]
            for _ in missing_keys:
                await self._update_stats("l2_miss")

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
        lock = await self._get_lock()
        async with lock:
            if stat_type == "l1_hit":
                self.stats.l1_hits += 1
            elif stat_type == "l1_miss":
                self.stats.l1_misses += 1
            elif stat_type == "l2_hit":
                self.stats.l2_hits += 1
            elif stat_type == "l2_miss":
                self.stats.l2_misses += 1
            elif stat_type == "l3_hit":
                self.stats.l3_hits += 1
            elif stat_type == "l3_miss":
                self.stats.l3_misses += 1

            self.stats.total_requests += 1

            if start_time:
                retrieval_time_ms = (time.time() - start_time) * 1000
                current_avg = self.stats.avg_retrieval_time_ms
                total = self.stats.total_requests
                self.stats.avg_retrieval_time_ms = (current_avg * (total - 1) + retrieval_time_ms) / total

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get detailed cache performance statistics"""
        return {
            "cache_stats": {
                "l1_hit_rate": self.stats.l1_hit_rate,
                "l2_hit_rate": self.stats.l2_hit_rate,
                "overall_hit_rate": self.stats.overall_hit_rate,
                "avg_retrieval_time_ms": self.stats.avg_retrieval_time_ms,
                "total_requests": self.stats.total_requests,
            },
            "l1_stats": self.l1_cache.get_stats(),
            "layer_breakdown": {
                "l1_hits": self.stats.l1_hits,
                "l1_misses": self.stats.l1_misses,
                "l2_hits": self.stats.l2_hits,
                "l2_misses": self.stats.l2_misses,
                "l3_hits": self.stats.l3_hits,
                "l3_misses": self.stats.l3_misses,
            },
        }


# Singleton instance
_optimized_cache = None


def get_optimized_cache_service(redis_url: Optional[str] = None) -> OptimizedCacheService:
    """Get singleton optimized cache service"""
    global _optimized_cache
    if _optimized_cache is None:
        _optimized_cache = OptimizedCacheService(redis_url)
    return _optimized_cache


def get_cache_service(redis_url: Optional[str] = None) -> OptimizedCacheService:
    """Alias for get_optimized_cache_service for backward compatibility."""
    return get_optimized_cache_service(redis_url)


# ============================================================================
# ENHANCED CACHING METHODS FOR PERFORMANCE OPTIMIZATION
# ============================================================================


class EnhancedCacheService(OptimizedCacheService):
    """
    Enhanced cache service with priority-based TTL, intelligent warming,
    and performance monitoring.

    Targets: 90% hit rate, <5ms L1 response, <20ms L2 response
    """

    def __init__(self, redis_url: Optional[str] = None):
        super().__init__(redis_url)
        self._warm_cache_configs: List[Dict[str, Any]] = []
        self._performance_thresholds = {
            "hit_rate_warning": 0.80,
            "hit_rate_critical": 0.60,
            "l1_response_ms_warning": 5.0,
            "l2_response_ms_warning": 20.0,
        }
        logger.info("EnhancedCacheService initialized with performance optimizations")

    async def set_with_priority(self, key: str, value: Any, ttl: int = 300, priority: str = "normal") -> bool:
        """
        Set cache value with priority-based TTL adjustment

        Args:
            key: Cache key
            value: Value to cache
            ttl: Base TTL in seconds
            priority: 'critical', 'high', 'normal', or 'low'

        Returns:
            bool: Success status
        """
        multiplier = CachePriority.get_multiplier(priority)
        adjusted_ttl = int(ttl * multiplier)
        return await self.set(key, value, adjusted_ttl)

    async def get_or_compute(self, key: str, compute_func: Callable, ttl: int = 300, priority: str = "normal") -> Any:
        """
        Get from cache or compute and cache the result

        This is the preferred method for caching expensive computations.
        """
        # Try cache first
        value = await self.get(key)
        if value is not None:
            return value

        # Compute value
        if asyncio.iscoroutinefunction(compute_func):
            value = await compute_func()
        else:
            value = compute_func()

        # Cache it
        if value is not None:
            await self.set_with_priority(key, value, ttl, priority)

        return value

    def register_warm_config(self, key_pattern: str, data_loader: Callable, ttl: int = 3600, priority: str = "high"):
        """Register a cache warming configuration"""
        self._warm_cache_configs.append(
            {
                "key_pattern": key_pattern,
                "data_loader": data_loader,
                "ttl": ttl,
                "priority": priority,
            }
        )

    async def warm_all_registered(self) -> Dict[str, bool]:
        """Execute cache warming for all registered configurations"""
        results = {}
        for config in self._warm_cache_configs:
            try:
                key = config["key_pattern"]
                loader = config["data_loader"]
                ttl = config["ttl"]
                priority = config["priority"]

                if asyncio.iscoroutinefunction(loader):
                    data = await loader()
                else:
                    data = loader()

                success = await self.set_with_priority(key, data, ttl, priority)
                results[key] = success

            except Exception as e:
                logger.error(f"Cache warming error for {config['key_pattern']}: {e}")
                results[config["key_pattern"]] = False

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Cache warming completed: {successful}/{len(results)} successful")
        return results

    async def warm_default_data(self) -> Dict[str, bool]:
        """
        Warm cache with default high-traffic data for the platform

        Includes:
        - Popular market data
        - Lead scoring models
        - AI response templates
        - Churn risk thresholds
        """
        results = {}

        # Popular market data
        markets = ["austin", "dallas", "houston", "san_antonio", "fort_worth"]
        for market in markets:
            key = f"market_data:{market}"
            data = {
                "market": market,
                "avg_price": 450000 + (hash(market) % 100000),
                "inventory": 200 + (hash(market) % 100),
                "trends": "stable",
                "days_on_market_avg": 45,
                "price_per_sqft": 220,
                "cached_at": datetime.now().isoformat(),
            }
            results[key] = await self.set_with_priority(key, data, 3600, "critical")

        # Lead scoring models
        scoring_models = {
            "demographic_weights": {"age": 0.3, "income": 0.4, "location": 0.3},
            "behavioral_weights": {"engagement": 0.5, "response_time": 0.3, "interactions": 0.2},
            "market_factors": {"inventory": 0.4, "price_trend": 0.6},
            "version": "2.1.0",
            "cached_at": datetime.now().isoformat(),
        }
        results["lead_scoring_models"] = await self.set_with_priority(
            "lead_scoring_models", scoring_models, 7200, "critical"
        )

        # AI response templates
        ai_templates = {
            "property_description": "Based on your preferences for {criteria}, this {property_type} offers...",
            "market_analysis": "The {market} market shows {trend} with {data_points}...",
            "lead_qualification": "Your profile indicates {qualification_level} based on...",
            "follow_up": "Following up on our conversation about {topic}...",
            "cached_at": datetime.now().isoformat(),
        }
        results["ai_response_templates"] = await self.set_with_priority(
            "ai_response_templates", ai_templates, 1800, "high"
        )

        # Churn risk thresholds
        churn_thresholds = {
            "critical": 80,
            "high": 60,
            "medium": 30,
            "low": 0,
            "inactivity_warning_days": 14,
            "inactivity_churn_days": 30,
            "cached_at": datetime.now().isoformat(),
        }
        results["churn_risk_thresholds"] = await self.set_with_priority(
            "churn_risk_thresholds", churn_thresholds, 3600, "high"
        )

        successful = sum(1 for v in results.values() if v)
        logger.info(f"Default cache warming completed: {successful}/{len(results)} successful")
        return results

    def check_performance_health(self) -> Dict[str, Any]:
        """
        Check cache performance against thresholds

        Returns health status and recommendations
        """
        stats = self.get_performance_stats()
        health = {
            "status": "healthy",
            "issues": [],
            "recommendations": [],
        }

        # Check hit rate
        hit_rate = stats["cache_stats"]["overall_hit_rate"]
        if hit_rate < self._performance_thresholds["hit_rate_critical"]:
            health["status"] = "critical"
            health["issues"].append(f"Hit rate {hit_rate:.1%} below critical threshold")
            health["recommendations"].append("Run cache warming immediately")
        elif hit_rate < self._performance_thresholds["hit_rate_warning"]:
            health["status"] = "warning"
            health["issues"].append(f"Hit rate {hit_rate:.1%} below warning threshold")
            health["recommendations"].append("Review cache key patterns")

        # Check response times
        avg_time = stats["cache_stats"]["avg_retrieval_time_ms"]
        if avg_time > self._performance_thresholds["l2_response_ms_warning"]:
            if health["status"] == "healthy":
                health["status"] = "warning"
            health["issues"].append(f"Average response time {avg_time:.1f}ms above threshold")
            health["recommendations"].append("Check Redis connection pool size")

        health["metrics"] = stats
        return health

    async def reset_metrics(self):
        """Reset performance metrics"""
        lock = await self._get_lock()
        async with lock:
            self.stats = CacheStats()
        logger.info("Cache metrics reset")


# Enhanced singleton getter
_enhanced_cache = None


def get_enhanced_cache_service(redis_url: Optional[str] = None) -> EnhancedCacheService:
    """Get singleton enhanced cache service"""
    global _enhanced_cache
    if _enhanced_cache is None:
        _enhanced_cache = EnhancedCacheService(redis_url)
    return _enhanced_cache


# ============================================================================
# CACHING DECORATOR FOR EASY FUNCTION CACHING
# ============================================================================


def cached(ttl: int = 300, priority: str = "normal", key_prefix: str = ""):
    """
    Decorator for caching function results

    Usage:
        @cached(ttl=600, priority="high", key_prefix="lead_score")
        async def calculate_lead_score(lead_id: str):
            # Expensive computation...
            return score
    """

    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}" if key_prefix else func.__name__
            if args:
                cache_key += f":{':'.join(str(a) for a in args)}"
            if kwargs:
                sorted_kwargs = json.dumps(kwargs, sort_keys=True, default=str)
                cache_key += f":{hashlib.md5(sorted_kwargs.encode()).hexdigest()[:8]}"

            cache = get_enhanced_cache_service()

            # Try cache first
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Cache result
            await cache.set_with_priority(cache_key, result, ttl, priority)

            return result

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't use async caching easily
            # Just call the function directly
            return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# ============================================================================
# EXAMPLE USAGE AND TESTING
# ============================================================================

if __name__ == "__main__":

    async def test_enhanced_cache():
        """Test enhanced cache service"""
        cache = get_enhanced_cache_service()

        print("=" * 60)
        print("Enhanced Cache Service Test")
        print("=" * 60)

        # Test 1: Warm default data
        print("\n1. Warming cache with default data...")
        warming_results = await cache.warm_default_data()
        print(f"   Warmed {sum(warming_results.values())} entries")

        # Test 2: Priority-based caching
        print("\n2. Testing priority-based TTL...")
        await cache.set_with_priority("test:critical", {"data": "critical"}, 100, "critical")
        await cache.set_with_priority("test:high", {"data": "high"}, 100, "high")
        await cache.set_with_priority("test:normal", {"data": "normal"}, 100, "normal")
        await cache.set_with_priority("test:low", {"data": "low"}, 100, "low")
        print("   Set items with different priorities")

        # Test 3: Get operations for hit rate testing
        print("\n3. Testing cache hits (100 operations)...")
        for i in range(100):
            # Mix of hits and misses
            key = f"market_data:{'austin' if i % 2 == 0 else 'dallas'}"
            await cache.get(key)

        # Test 4: Performance health check
        print("\n4. Checking performance health...")
        health = cache.check_performance_health()
        print(f"   Status: {health['status']}")
        print(f"   Hit Rate: {health['metrics']['cache_stats']['overall_hit_rate']:.1%}")
        print(f"   Avg Response: {health['metrics']['cache_stats']['avg_retrieval_time_ms']:.2f}ms")

        if health["issues"]:
            print(f"   Issues: {health['issues']}")
        if health["recommendations"]:
            print(f"   Recommendations: {health['recommendations']}")

        print("\n" + "=" * 60)
        print("Test completed!")

    asyncio.run(test_enhanced_cache())
