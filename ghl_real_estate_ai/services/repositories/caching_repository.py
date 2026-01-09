"""
Caching Repository Decorator Implementation

Provides caching capabilities for any property repository using the Decorator pattern.
Supports multiple cache backends and configurable TTL.
"""

import asyncio
import json
import hashlib
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
import pickle

try:
    import redis
    HAS_REDIS = True
except ImportError:
    HAS_REDIS = False

try:
    from .interfaces import (
        IPropertyRepository, PropertyQuery, RepositoryResult, RepositoryMetadata,
        RepositoryError
    )
except ImportError:
    from interfaces import (
        IPropertyRepository, PropertyQuery, RepositoryResult, RepositoryMetadata,
        RepositoryError
    )


class CacheBackend:
    """Abstract base class for cache backends"""

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        raise NotImplementedError

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set value in cache with optional TTL"""
        raise NotImplementedError

    async def delete(self, key: str):
        """Delete value from cache"""
        raise NotImplementedError

    async def clear(self):
        """Clear all cached values"""
        raise NotImplementedError

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        raise NotImplementedError


class MemoryCacheBackend(CacheBackend):
    """In-memory cache backend"""

    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: Dict[str, tuple] = {}  # key -> (value, expires_at)
        self._access_order: List[str] = []  # For LRU eviction

    async def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self._cache:
            value, expires_at = self._cache[key]

            # Check expiration
            if expires_at and datetime.now() > expires_at:
                await self.delete(key)
                return None

            # Update access order for LRU
            if key in self._access_order:
                self._access_order.remove(key)
            self._access_order.append(key)

            return value

        return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set value in memory cache"""
        expires_at = None
        if ttl:
            expires_at = datetime.now() + ttl

        # Evict if necessary
        while len(self._cache) >= self.max_size and key not in self._cache:
            if self._access_order:
                oldest_key = self._access_order.pop(0)
                del self._cache[oldest_key]

        self._cache[key] = (value, expires_at)

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    async def delete(self, key: str):
        """Delete from memory cache"""
        if key in self._cache:
            del self._cache[key]
        if key in self._access_order:
            self._access_order.remove(key)

    async def clear(self):
        """Clear memory cache"""
        self._cache.clear()
        self._access_order.clear()

    async def exists(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        if key not in self._cache:
            return False

        # Check expiration
        _, expires_at = self._cache[key]
        if expires_at and datetime.now() > expires_at:
            await self.delete(key)
            return False

        return True


class RedisCacheBackend(CacheBackend):
    """Redis cache backend"""

    def __init__(self, redis_url: str = "redis://localhost:6379", key_prefix: str = "prop_cache:"):
        if not HAS_REDIS:
            raise RepositoryError("Redis cache requires 'redis' package")

        self.redis_url = redis_url
        self.key_prefix = key_prefix
        self._client: Optional[redis.Redis] = None

    async def connect(self):
        """Connect to Redis"""
        self._client = redis.from_url(self.redis_url, decode_responses=False)
        # Test connection
        await self._client.ping()

    async def disconnect(self):
        """Disconnect from Redis"""
        if self._client:
            await self._client.close()

    def _make_key(self, key: str) -> str:
        """Create prefixed cache key"""
        return f"{self.key_prefix}{key}"

    async def get(self, key: str) -> Optional[Any]:
        """Get value from Redis cache"""
        if not self._client:
            return None

        try:
            cached_data = await self._client.get(self._make_key(key))
            if cached_data:
                return pickle.loads(cached_data)
        except Exception:
            pass  # Cache miss or error

        return None

    async def set(self, key: str, value: Any, ttl: Optional[timedelta] = None):
        """Set value in Redis cache"""
        if not self._client:
            return

        try:
            serialized = pickle.dumps(value)
            cache_key = self._make_key(key)

            if ttl:
                await self._client.setex(cache_key, int(ttl.total_seconds()), serialized)
            else:
                await self._client.set(cache_key, serialized)
        except Exception as e:
            print(f"Redis cache set error: {e}")

    async def delete(self, key: str):
        """Delete from Redis cache"""
        if not self._client:
            return

        try:
            await self._client.delete(self._make_key(key))
        except Exception as e:
            print(f"Redis cache delete error: {e}")

    async def clear(self):
        """Clear Redis cache (all keys with prefix)"""
        if not self._client:
            return

        try:
            pattern = f"{self.key_prefix}*"
            keys = await self._client.keys(pattern)
            if keys:
                await self._client.delete(*keys)
        except Exception as e:
            print(f"Redis cache clear error: {e}")

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis cache"""
        if not self._client:
            return False

        try:
            return bool(await self._client.exists(self._make_key(key)))
        except Exception:
            return False


class CachingRepository(IPropertyRepository):
    """
    Repository decorator that adds caching capabilities to any repository.

    Uses Decorator pattern to wrap existing repositories with caching functionality.
    """

    def __init__(self, wrapped_repository: IPropertyRepository, cache_backend: CacheBackend,
                 default_ttl: timedelta = timedelta(minutes=15)):
        """
        Initialize caching repository.

        Args:
            wrapped_repository: The repository to wrap with caching
            cache_backend: Cache backend implementation
            default_ttl: Default cache time-to-live
        """
        super().__init__(f"cached_{wrapped_repository.name}")

        self.wrapped_repository = wrapped_repository
        self.cache_backend = cache_backend
        self.default_ttl = default_ttl

        # Cache statistics
        self.cache_hits = 0
        self.cache_misses = 0
        self.cache_sets = 0

    async def connect(self) -> bool:
        """Connect both wrapped repository and cache backend"""
        # Connect wrapped repository
        if not await self.wrapped_repository.connect():
            return False

        # Connect cache backend if needed
        if hasattr(self.cache_backend, 'connect'):
            await self.cache_backend.connect()

        self._is_connected = True
        return True

    async def disconnect(self):
        """Disconnect both wrapped repository and cache backend"""
        await self.wrapped_repository.disconnect()

        if hasattr(self.cache_backend, 'disconnect'):
            await self.cache_backend.disconnect()

        self._is_connected = False

    async def health_check(self) -> Dict[str, Any]:
        """Combined health check for repository and cache"""
        repo_health = await self.wrapped_repository.health_check()

        cache_health = {
            "cache_backend": type(self.cache_backend).__name__,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self._calculate_hit_rate(),
            "cache_sets": self.cache_sets
        }

        return {
            "repository": repo_health,
            "cache": cache_health,
            "status": repo_health.get("status", "unknown")
        }

    async def find_properties(self, query: PropertyQuery) -> RepositoryResult:
        """Find properties with caching"""
        # Check cache first if enabled
        if query.use_cache:
            cache_key = self._generate_cache_key(query, "find_properties")
            cached_result = await self._get_from_cache(cache_key)

            if cached_result:
                self.cache_hits += 1
                cached_result.metadata.cache_hit = True
                return cached_result

            self.cache_misses += 1

        # Get from wrapped repository
        result = await self.wrapped_repository.find_properties(query)

        # Cache successful results
        if result.success and query.use_cache:
            ttl = query.cache_ttl or self.default_ttl
            await self._set_in_cache(cache_key, result, ttl)
            self.cache_sets += 1

        return result

    async def get_property_by_id(self, property_id: str) -> Optional[Dict[str, Any]]:
        """Get property by ID with caching"""
        cache_key = f"property_id:{property_id}"
        cached_property = await self._get_from_cache(cache_key)

        if cached_property:
            self.cache_hits += 1
            return cached_property

        self.cache_misses += 1

        # Get from wrapped repository
        property_data = await self.wrapped_repository.get_property_by_id(property_id)

        # Cache result
        if property_data:
            await self._set_in_cache(cache_key, property_data, self.default_ttl)
            self.cache_sets += 1

        return property_data

    async def count_properties(self, query: PropertyQuery) -> int:
        """Count properties with caching"""
        if query.use_cache:
            cache_key = self._generate_cache_key(query, "count_properties")
            cached_count = await self._get_from_cache(cache_key)

            if cached_count is not None:
                self.cache_hits += 1
                return cached_count

            self.cache_misses += 1

        # Get from wrapped repository
        count = await self.wrapped_repository.count_properties(query)

        # Cache result
        if query.use_cache:
            ttl = query.cache_ttl or self.default_ttl
            await self._set_in_cache(cache_key, count, ttl)
            self.cache_sets += 1

        return count

    def get_supported_filters(self) -> List[str]:
        """Delegate to wrapped repository"""
        return self.wrapped_repository.get_supported_filters()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Combined performance metrics"""
        wrapped_metrics = self.wrapped_repository.get_performance_metrics()

        cache_metrics = {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": self._calculate_hit_rate(),
            "cache_sets": self.cache_sets,
            "cache_backend": type(self.cache_backend).__name__
        }

        return {
            "wrapped_repository": wrapped_metrics,
            "cache_metrics": cache_metrics,
            "repository_type": "caching_decorator"
        }

    # Cache management methods
    async def invalidate_cache(self, pattern: str = None):
        """Invalidate cache entries"""
        if pattern:
            # For pattern-based invalidation, we'd need more sophisticated cache backend
            # For now, just clear all
            await self.cache_backend.clear()
        else:
            await self.cache_backend.clear()

    async def warm_cache(self, queries: List[PropertyQuery]):
        """Pre-warm cache with common queries"""
        for query in queries:
            try:
                await self.find_properties(query)
            except Exception as e:
                print(f"Cache warm-up failed for query: {e}")

    # Private methods
    def _generate_cache_key(self, query: PropertyQuery, operation: str) -> str:
        """Generate cache key from query parameters"""
        # Convert query to deterministic string representation
        query_dict = {
            "operation": operation,
            "min_price": query.min_price,
            "max_price": query.max_price,
            "min_bedrooms": query.min_bedrooms,
            "max_bedrooms": query.max_bedrooms,
            "min_bathrooms": query.min_bathrooms,
            "max_bathrooms": query.max_bathrooms,
            "min_sqft": query.min_sqft,
            "max_sqft": query.max_sqft,
            "property_types": sorted(query.property_types) if query.property_types else None,
            "neighborhoods": sorted(query.neighborhoods) if query.neighborhoods else None,
            "zip_codes": sorted(query.zip_codes) if query.zip_codes else None,
            "location": query.location,
            "latitude": query.latitude,
            "longitude": query.longitude,
            "radius_miles": query.radius_miles,
            "required_amenities": sorted(query.required_amenities),
            "preferred_amenities": sorted(query.preferred_amenities),
            "max_days_on_market": query.max_days_on_market,
            "min_year_built": query.min_year_built,
            "max_year_built": query.max_year_built,
            "sort_by": query.sort_by,
            "sort_order": query.sort_order.value,
            "page": query.pagination.page,
            "limit": query.pagination.limit,
            "semantic_query": query.semantic_query,
            "filters": [(f.field, f.operator.value, f.value) for f in query.filters]
        }

        # Create hash from deterministic representation
        query_json = json.dumps(query_dict, sort_keys=True, default=str)
        query_hash = hashlib.md5(query_json.encode()).hexdigest()

        return f"query:{query_hash}"

    async def _get_from_cache(self, key: str) -> Optional[Any]:
        """Get value from cache with error handling"""
        try:
            return await self.cache_backend.get(key)
        except Exception as e:
            print(f"Cache get error: {e}")
            return None

    async def _set_in_cache(self, key: str, value: Any, ttl: timedelta):
        """Set value in cache with error handling"""
        try:
            await self.cache_backend.set(key, value, ttl)
        except Exception as e:
            print(f"Cache set error: {e}")

    def _calculate_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total_requests = self.cache_hits + self.cache_misses
        if total_requests == 0:
            return 0.0
        return (self.cache_hits / total_requests) * 100.0