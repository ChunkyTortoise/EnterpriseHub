"""
Redis Caching Infrastructure for Multi-Tenant Continuous Memory System.

Provides Redis caching with:
- Connection pooling and health monitoring
- Multi-level caching strategies
- Automatic failover handling
- Performance optimization
"""

import asyncio
import json
import time
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import logging

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class RedisConnectionError(Exception):
    """Redis connection related errors."""
    pass


class RedisHealthStatus:
    """Redis health monitoring."""

    def __init__(self):
        self.is_healthy = False
        self.last_check = None
        self.consecutive_failures = 0
        self.total_operations = 0
        self.successful_operations = 0
        self.avg_response_time_ms = 0.0
        self.memory_usage_mb = 0.0
        self.connected_clients = 0
        self.hit_rate = 0.0
        self.last_error = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for monitoring."""
        return {
            "is_healthy": self.is_healthy,
            "last_check": self.last_check.isoformat() if self.last_check else None,
            "consecutive_failures": self.consecutive_failures,
            "total_operations": self.total_operations,
            "successful_operations": self.successful_operations,
            "avg_response_time_ms": self.avg_response_time_ms,
            "memory_usage_mb": self.memory_usage_mb,
            "connected_clients": self.connected_clients,
            "hit_rate": self.hit_rate,
            "last_error": str(self.last_error) if self.last_error else None
        }


class EnhancedRedisClient:
    """
    Enhanced Redis client with monitoring, health checks, and caching patterns.
    """

    def __init__(
        self,
        redis_url: Optional[str] = None,
        max_connections: int = 20,
        retry_attempts: int = 3,
        health_check_interval: int = 30,
        default_ttl: int = 3600
    ):
        """
        Initialize Redis client.

        Args:
            redis_url: Redis connection URL
            max_connections: Maximum connection pool size
            retry_attempts: Number of retry attempts for operations
            health_check_interval: Health check interval in seconds
            default_ttl: Default TTL for cached items in seconds
        """
        self.redis_url = redis_url or getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        self.max_connections = max_connections
        self.retry_attempts = retry_attempts
        self.health_check_interval = health_check_interval
        self.default_ttl = default_ttl

        # Redis client
        self.client = None
        self.initialized = False

        # Health monitoring
        self.health = RedisHealthStatus()
        self._health_check_task = None

        # Performance metrics
        self.metrics = {
            "total_gets": 0,
            "total_sets": 0,
            "total_deletes": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "avg_response_time_ms": 0.0,
            "peak_response_time_ms": 0.0,
            "connection_errors": 0,
            "operation_errors": 0
        }

        # Cache key patterns for multi-tenant isolation
        self.key_patterns = {
            "conversation_memory": "conv_memory:{tenant_id}:{contact_id}",
            "behavioral_prefs": "behavioral:{conversation_id}",
            "property_interactions": "property:{conversation_id}",
            "tenant_config": "tenant_config:{tenant_id}",
            "claude_performance": "claude_perf:{tenant_id}:{date}",
            "system_health": "system_health:{component}"
        }

        logger.info(f"Redis client initialized - URL: {self._mask_url(self.redis_url)}")

    def _mask_url(self, url: str) -> str:
        """Mask sensitive parts of Redis URL for logging."""
        if url is None:
            return "None"
        if '@' in url:
            parts = url.split('@')
            return f"{parts[0].split('://')[0]}://***@{parts[1]}"
        return url

    async def initialize(self) -> bool:
        """
        Initialize Redis connection.

        Returns:
            True if successful, False otherwise
        """
        if self.initialized:
            return True

        try:
            import aioredis

            # Create Redis connection with pool
            self.client = aioredis.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                decode_responses=True,
                retry_on_timeout=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )

            # Verify connection with ping
            if await self._perform_health_check():
                self.initialized = True
                self.health.is_healthy = True
                logger.info("Redis connection initialized successfully")

                # Start background health monitoring
                self._health_check_task = asyncio.create_task(self._background_health_monitor())
                return True
            else:
                logger.error("Redis health check failed during initialization")
                await self.close()
                return False

        except Exception as e:
            logger.error(f"Failed to initialize Redis client: {e}")
            self.health.last_error = e
            self.health.consecutive_failures += 1
            return False

    async def close(self):
        """Close Redis connection."""
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self.client:
            await self.client.close()
            self.client = None

        self.initialized = False
        logger.info("Redis connection closed")

    async def get(self, key: str, default: Any = None) -> Optional[Any]:
        """
        Get value from Redis with automatic retry and metrics.

        Args:
            key: Redis key
            default: Default value if key not found

        Returns:
            Cached value or default
        """
        if not await self._ensure_connected():
            return default

        start_time = time.time()

        try:
            for attempt in range(self.retry_attempts):
                try:
                    value = await self.client.get(key)

                    if value is not None:
                        self.metrics["cache_hits"] += 1
                        self._record_successful_operation("get", time.time() - start_time)

                        # Try to deserialize JSON
                        try:
                            return json.loads(value)
                        except (json.JSONDecodeError, TypeError):
                            return value
                    else:
                        self.metrics["cache_misses"] += 1
                        self._record_successful_operation("get", time.time() - start_time)
                        return default

                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        raise
                    await asyncio.sleep(0.1 * (attempt + 1))  # Exponential backoff

        except Exception as e:
            self._record_failed_operation("get", time.time() - start_time, e)
            logger.error(f"Redis GET error for key {key}: {e}")
            return default

        finally:
            self.metrics["total_gets"] += 1

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        nx: bool = False
    ) -> bool:
        """
        Set value in Redis with automatic retry and metrics.

        Args:
            key: Redis key
            value: Value to cache
            ttl: TTL in seconds (uses default if None)
            nx: Only set if key doesn't exist

        Returns:
            True if successful, False otherwise
        """
        if not await self._ensure_connected():
            return False

        start_time = time.time()
        ttl = ttl or self.default_ttl

        try:
            # Serialize value if needed
            if isinstance(value, (dict, list, tuple)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)

            for attempt in range(self.retry_attempts):
                try:
                    if nx:
                        result = await self.client.set(key, serialized_value, ex=ttl, nx=True)
                    else:
                        result = await self.client.setex(key, ttl, serialized_value)

                    success = result is not None and result != False

                    if success:
                        self._record_successful_operation("set", time.time() - start_time)

                    return success

                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        raise
                    await asyncio.sleep(0.1 * (attempt + 1))

        except Exception as e:
            self._record_failed_operation("set", time.time() - start_time, e)
            logger.error(f"Redis SET error for key {key}: {e}")
            return False

        finally:
            self.metrics["total_sets"] += 1

    async def setex(self, key: str, ttl: int, value: Any) -> bool:
        """Set value with explicit TTL."""
        return await self.set(key, value, ttl=ttl)

    async def delete(self, *keys: str) -> int:
        """
        Delete keys from Redis.

        Args:
            keys: Keys to delete

        Returns:
            Number of keys deleted
        """
        if not await self._ensure_connected():
            return 0

        start_time = time.time()

        try:
            for attempt in range(self.retry_attempts):
                try:
                    deleted_count = await self.client.delete(*keys)
                    self._record_successful_operation("delete", time.time() - start_time)
                    return deleted_count

                except Exception as e:
                    if attempt == self.retry_attempts - 1:
                        raise
                    await asyncio.sleep(0.1 * (attempt + 1))

        except Exception as e:
            self._record_failed_operation("delete", time.time() - start_time, e)
            logger.error(f"Redis DELETE error for keys {keys}: {e}")
            return 0

        finally:
            self.metrics["total_deletes"] += 1

    async def exists(self, key: str) -> bool:
        """Check if key exists in Redis."""
        if not await self._ensure_connected():
            return False

        try:
            result = await self.client.exists(key)
            return result > 0

        except Exception as e:
            logger.error(f"Redis EXISTS error for key {key}: {e}")
            return False

    async def expire(self, key: str, ttl: int) -> bool:
        """Set TTL on existing key."""
        if not await self._ensure_connected():
            return False

        try:
            return await self.client.expire(key, ttl)

        except Exception as e:
            logger.error(f"Redis EXPIRE error for key {key}: {e}")
            return False

    async def get_multi(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once."""
        if not await self._ensure_connected():
            return {}

        try:
            values = await self.client.mget(keys)
            result = {}

            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value

            return result

        except Exception as e:
            logger.error(f"Redis MGET error: {e}")
            return {}

    async def set_multi(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple key-value pairs."""
        if not await self._ensure_connected():
            return False

        try:
            # Serialize values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list, tuple)):
                    serialized_mapping[key] = json.dumps(value, default=str)
                else:
                    serialized_mapping[key] = str(value)

            # Use pipeline for efficiency
            pipe = self.client.pipeline()

            for key, value in serialized_mapping.items():
                if ttl:
                    pipe.setex(key, ttl, value)
                else:
                    pipe.set(key, value)

            await pipe.execute()
            return True

        except Exception as e:
            logger.error(f"Redis MSET error: {e}")
            return False

    # Caching pattern helpers

    async def get_or_compute(
        self,
        key: str,
        compute_func,
        ttl: Optional[int] = None,
        force_refresh: bool = False
    ) -> Any:
        """
        Get value from cache or compute and cache it.

        Args:
            key: Cache key
            compute_func: Async function to compute value
            ttl: TTL for cached value
            force_refresh: Force recomputation

        Returns:
            Cached or computed value
        """
        if not force_refresh:
            cached_value = await self.get(key)
            if cached_value is not None:
                return cached_value

        # Compute new value
        try:
            if asyncio.iscoroutinefunction(compute_func):
                value = await compute_func()
            else:
                value = compute_func()

            # Cache the computed value
            await self.set(key, value, ttl=ttl)
            return value

        except Exception as e:
            logger.error(f"Error computing value for key {key}: {e}")
            # Return stale value if available
            return await self.get(key)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching pattern."""
        if not await self._ensure_connected():
            return 0

        try:
            # Scan for matching keys
            keys = []
            cursor = 0

            while True:
                cursor, batch = await self.client.scan(cursor, match=pattern, count=100)
                keys.extend(batch)
                if cursor == 0:
                    break

            # Delete matching keys
            if keys:
                return await self.delete(*keys)

            return 0

        except Exception as e:
            logger.error(f"Error invalidating pattern {pattern}: {e}")
            return 0

    # Multi-tenant caching helpers

    def build_key(self, pattern_name: str, **kwargs) -> str:
        """Build cache key from pattern and parameters."""
        pattern = self.key_patterns.get(pattern_name)
        if not pattern:
            raise ValueError(f"Unknown key pattern: {pattern_name}")

        return pattern.format(**kwargs)

    async def get_conversation_memory(self, tenant_id: str, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation memory from cache."""
        key = self.build_key("conversation_memory", tenant_id=tenant_id, contact_id=contact_id)
        return await self.get(key)

    async def set_conversation_memory(
        self,
        tenant_id: str,
        contact_id: str,
        memory_data: Dict[str, Any],
        ttl: int = 1800
    ) -> bool:
        """Set conversation memory in cache."""
        key = self.build_key("conversation_memory", tenant_id=tenant_id, contact_id=contact_id)
        return await self.set(key, memory_data, ttl=ttl)

    async def invalidate_conversation_cache(self, tenant_id: str, contact_id: str) -> bool:
        """Invalidate conversation cache."""
        key = self.build_key("conversation_memory", tenant_id=tenant_id, contact_id=contact_id)
        return await self.delete(key) > 0

    # Health monitoring

    async def _ensure_connected(self) -> bool:
        """Ensure Redis connection is available."""
        if not self.initialized:
            return await self.initialize()

        if not self.health.is_healthy:
            logger.warning("Redis unhealthy, attempting reconnection")
            return await self.initialize()

        return True

    async def _perform_health_check(self) -> bool:
        """Perform Redis health check."""
        try:
            # Ping test
            pong = await self.client.ping()
            if pong:
                # Get Redis info for metrics
                info = await self.client.info()

                if 'used_memory' in info:
                    self.health.memory_usage_mb = info['used_memory'] / (1024 * 1024)

                if 'connected_clients' in info:
                    self.health.connected_clients = info['connected_clients']

                self.health.last_check = datetime.utcnow()
                self.health.consecutive_failures = 0
                return True

        except Exception as e:
            logger.error(f"Redis health check failed: {e}")
            self.health.consecutive_failures += 1
            self.health.last_error = e

        return False

    async def _background_health_monitor(self):
        """Background task for continuous health monitoring."""
        while self.initialized:
            try:
                self.health.is_healthy = await self._perform_health_check()

                # Update hit rate
                total_ops = self.metrics["cache_hits"] + self.metrics["cache_misses"]
                if total_ops > 0:
                    self.health.hit_rate = self.metrics["cache_hits"] / total_ops

                # Log health status if unhealthy
                if not self.health.is_healthy:
                    logger.warning(f"Redis health check failed. Consecutive failures: {self.health.consecutive_failures}")

                await asyncio.sleep(self.health_check_interval)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.health_check_interval)

    def _record_successful_operation(self, operation: str, duration_seconds: float):
        """Record successful operation metrics."""
        self.health.total_operations += 1
        self.health.successful_operations += 1

        duration_ms = duration_seconds * 1000

        # Update average response time
        if self.health.total_operations > 1:
            self.health.avg_response_time_ms = (
                (self.health.avg_response_time_ms * (self.health.total_operations - 1) + duration_ms) /
                self.health.total_operations
            )
        else:
            self.health.avg_response_time_ms = duration_ms

        # Update peak response time
        if duration_ms > self.metrics["peak_response_time_ms"]:
            self.metrics["peak_response_time_ms"] = duration_ms

    def _record_failed_operation(self, operation: str, duration_seconds: float, error: Exception):
        """Record failed operation metrics."""
        self.health.total_operations += 1
        self.health.last_error = error
        self.metrics["operation_errors"] += 1

        if "connection" in str(error).lower():
            self.metrics["connection_errors"] += 1

    def get_health_status(self) -> Dict[str, Any]:
        """Get current health status."""
        return self.health.to_dict()

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        total_gets = self.metrics["total_gets"]
        hit_rate = self.metrics["cache_hits"] / total_gets if total_gets > 0 else 0

        return {
            **self.metrics,
            "hit_rate": hit_rate,
            "health_status": self.get_health_status(),
            "connection_pool_size": self.max_connections
        }


# Global Redis client instance
redis_client = EnhancedRedisClient(
    max_connections=getattr(settings, 'redis_max_connections', 20),
    retry_attempts=getattr(settings, 'redis_retry_attempts', 3),
    health_check_interval=getattr(settings, 'redis_health_check_interval', 30),
    default_ttl=getattr(settings, 'redis_default_ttl', 3600)
)


async def initialize_redis():
    """Initialize global Redis client."""
    return await redis_client.initialize()


async def close_redis():
    """Close global Redis client."""
    await redis_client.close()


async def get_redis_health() -> Dict[str, Any]:
    """Get Redis health status."""
    return redis_client.get_health_status()


async def get_redis_metrics() -> Dict[str, Any]:
    """Get Redis performance metrics."""
    return redis_client.get_performance_metrics()