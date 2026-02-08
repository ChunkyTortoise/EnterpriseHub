"""
Redis Client Module
===================

Redis client wrapper with connection pooling, serialization, and distributed cache support.

Features:
    - Connection pooling for high-performance operations
    - Automatic serialization/deserialization (JSON, pickle, msgpack)
    - Distributed cache support with Redis Cluster
    - Health checks and connection monitoring
    - Pipeline support for batch operations
    - Pub/Sub support for cache invalidation

Example:
    >>> from src.caching.redis_client import RedisClient
    >>>
    >>> client = RedisClient("redis://localhost:6379/0")
    >>> await client.connect()
    >>>
    >>> # Basic operations
    >>> await client.set("key", {"data": "value"}, ttl=300)
    >>> value = await client.get("key")
    >>>
    >>> # Batch operations
    >>> await client.mset({"k1": "v1", "k2": "v2"})
    >>> values = await client.mget(["k1", "k2"])
"""

import asyncio
import json
import logging
import pickle
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar, Union

# Redis imports
try:
    import redis.asyncio as aioredis
    from redis.asyncio.connection import ConnectionPool
    from redis.asyncio.retry import Retry
    from redis.backoff import ExponentialBackoff
    from redis.cluster import RedisCluster
    from redis.exceptions import ConnectionError, RedisError, TimeoutError

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None
    ConnectionPool = None
    Retry = None
    ExponentialBackoff = None
    ConnectionError = Exception
    TimeoutError = Exception
    RedisError = Exception
    RedisCluster = None

# Optional msgpack for faster serialization
try:
    import msgpack

    MSGPACK_AVAILABLE = True
except ImportError:
    MSGPACK_AVAILABLE = False

logger = logging.getLogger(__name__)

T = TypeVar("T")


class SerializationFormat(Enum):
    """Supported serialization formats."""

    JSON = "json"
    PICKLE = "pickle"
    MSGPACK = "msgpack"
    STRING = "string"


@dataclass
class RedisConfig:
    """Configuration for Redis connection."""

    url: str = "redis://localhost:6379/0"
    max_connections: int = 50
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 5.0
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    decode_responses: bool = False

    # Pool configuration
    min_idle_connections: int = 5
    max_idle_connections: int = 20

    # Retry configuration
    retry_max_attempts: int = 3
    retry_base_delay: float = 0.1


@dataclass
class ConnectionStats:
    """Connection pool statistics."""

    total_connections: int = 0
    available_connections: int = 0
    in_use_connections: int = 0
    max_connections: int = 0
    connection_errors: int = 0
    last_health_check: Optional[float] = None


class Serializer:
    """Handles serialization and deserialization of cache values."""

    def __init__(self, default_format: SerializationFormat = SerializationFormat.JSON):
        self.default_format = default_format
        self._serializers: Dict[SerializationFormat, Callable] = {
            SerializationFormat.JSON: self._json_serialize,
            SerializationFormat.PICKLE: self._pickle_serialize,
            SerializationFormat.MSGPACK: self._msgpack_serialize,
            SerializationFormat.STRING: self._string_serialize,
        }
        self._deserializers: Dict[SerializationFormat, Callable] = {
            SerializationFormat.JSON: self._json_deserialize,
            SerializationFormat.PICKLE: self._pickle_deserialize,
            SerializationFormat.MSGPACK: self._msgpack_deserialize,
            SerializationFormat.STRING: self._string_deserialize,
        }

    def serialize(self, value: Any, format: Optional[SerializationFormat] = None) -> bytes:
        """Serialize a value to bytes."""
        fmt = format or self.default_format
        serializer = self._serializers.get(fmt, self._json_serialize)
        return serializer(value)

    def deserialize(self, data: bytes, format: Optional[SerializationFormat] = None) -> Any:
        """Deserialize bytes to a value."""
        if data is None:
            return None

        fmt = format or self.default_format
        deserializer = self._deserializers.get(fmt, self._json_deserialize)
        return deserializer(data)

    def _json_serialize(self, value: Any) -> bytes:
        """Serialize using JSON."""
        return json.dumps(value, default=self._json_default).encode("utf-8")

    def _json_deserialize(self, data: bytes) -> Any:
        """Deserialize using JSON."""
        return json.loads(data.decode("utf-8"))

    def _pickle_serialize(self, value: Any) -> bytes:
        """Serialize using pickle."""
        return pickle.dumps(value, protocol=pickle.HIGHEST_PROTOCOL)

    def _pickle_deserialize(self, data: bytes) -> Any:
        """Deserialize using pickle."""
        return pickle.loads(data)

    def _msgpack_serialize(self, value: Any) -> bytes:
        """Serialize using msgpack."""
        if not MSGPACK_AVAILABLE:
            return self._json_serialize(value)
        return msgpack.packb(value, use_bin_type=True)

    def _msgpack_deserialize(self, data: bytes) -> Any:
        """Deserialize using msgpack."""
        if not MSGPACK_AVAILABLE:
            return self._json_deserialize(data)
        return msgpack.unpackb(data, raw=False)

    def _string_serialize(self, value: Any) -> bytes:
        """Serialize as string."""
        return str(value).encode("utf-8")

    def _string_deserialize(self, data: bytes) -> Any:
        """Deserialize as string."""
        return data.decode("utf-8")

    def _json_default(self, obj: Any) -> Any:
        """Default JSON serializer for custom types."""
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, set):
            return list(obj)
        if hasattr(obj, "__dict__"):
            return asdict(obj) if hasattr(obj, "__dataclass_fields__") else obj.__dict__
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class BaseRedisClient(ABC):
    """Abstract base class for Redis clients."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to Redis."""
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to Redis."""
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[Any]:
        """Get value by key."""
        pass

    @abstractmethod
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """Set value with optional TTL."""
        pass

    @abstractmethod
    async def delete(self, key: str) -> int:
        """Delete key(s)."""
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass

    @abstractmethod
    async def ttl(self, key: str) -> int:
        """Get TTL of a key."""
        pass

    @abstractmethod
    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration on a key."""
        pass


class RedisClient(BaseRedisClient):
    """
    High-level Redis client with connection pooling and serialization.

    Features:
        - Connection pooling for performance
        - Automatic serialization/deserialization
        - Health monitoring
        - Pipeline support
        - Pub/Sub support

    Args:
        config: RedisConfig instance or URL string
        serializer: Serializer instance for data encoding
    """

    def __init__(self, config: Union[str, RedisConfig] = None, serializer: Optional[Serializer] = None):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package not installed. Install with: pip install redis")

        if isinstance(config, str):
            self.config = RedisConfig(url=config)
        else:
            self.config = config or RedisConfig()

        self.serializer = serializer or Serializer()
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[aioredis.Redis] = None
        self._pubsub: Optional[aioredis.client.PubSub] = None
        self._connected = False
        self._lock = asyncio.Lock()
        self._stats = ConnectionStats()

    async def connect(self) -> None:
        """Establish connection to Redis with retry logic."""
        async with self._lock:
            if self._connected:
                return

            try:
                retry = Retry(
                    ExponentialBackoff(cap=2.0, base=self.config.retry_base_delay), self.config.retry_max_attempts
                )

                self._pool = ConnectionPool.from_url(
                    self.config.url,
                    max_connections=self.config.max_connections,
                    socket_timeout=self.config.socket_timeout,
                    socket_connect_timeout=self.config.socket_connect_timeout,
                    retry_on_timeout=self.config.retry_on_timeout,
                    health_check_interval=self.config.health_check_interval,
                    retry=retry,
                    decode_responses=False,  # We handle decoding ourselves
                )

                self._client = aioredis.Redis(connection_pool=self._pool)

                # Test connection
                await self._client.ping()

                self._connected = True
                self._stats.max_connections = self.config.max_connections
                self._stats.last_health_check = asyncio.get_event_loop().time()

                logger.info(f"Connected to Redis at {self.config.url}")

            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise ConnectionError(f"Redis connection failed: {e}")

    async def disconnect(self) -> None:
        """Close Redis connection and cleanup resources."""
        async with self._lock:
            if not self._connected:
                return

            try:
                if self._pubsub:
                    await self._pubsub.close()

                if self._pool:
                    await self._pool.disconnect()

                self._connected = False
                logger.info("Disconnected from Redis")

            except Exception as e:
                logger.error(f"Error disconnecting from Redis: {e}")
                raise

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on Redis connection."""
        if not self._connected or not self._client:
            return {"status": "disconnected", "healthy": False}

        try:
            start_time = asyncio.get_event_loop().time()
            await self._client.ping()
            latency_ms = (asyncio.get_event_loop().time() - start_time) * 1000

            info = await self._client.info()

            self._stats.last_health_check = asyncio.get_event_loop().time()

            return {
                "status": "connected",
                "healthy": True,
                "latency_ms": round(latency_ms, 2),
                "redis_version": info.get("redis_version", "unknown"),
                "used_memory_human": info.get("used_memory_human", "unknown"),
                "connected_clients": info.get("connected_clients", 0),
                "total_connections_received": info.get("total_connections_received", 0),
            }
        except Exception as e:
            self._stats.connection_errors += 1
            return {"status": "error", "healthy": False, "error": str(e)}

    async def get(self, key: str) -> Optional[Any]:
        """Get and deserialize value by key."""
        if not self._connected:
            await self.connect()

        try:
            data = await self._client.get(key)
            if data is None:
                return None
            return self.serializer.deserialize(data)
        except Exception as e:
            logger.error(f"Error getting key {key}: {e}")
            raise

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """
        Serialize and set value with optional TTL.

        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
            nx: Only set if key does not exist
            xx: Only set if key exists
        """
        if not self._connected:
            await self.connect()

        try:
            serialized = self.serializer.serialize(value)

            kwargs = {}
            if ttl is not None:
                kwargs["ex"] = ttl
            if nx:
                kwargs["nx"] = True
            if xx:
                kwargs["xx"] = True

            result = await self._client.set(key, serialized, **kwargs)
            return result is True
        except Exception as e:
            logger.error(f"Error setting key {key}: {e}")
            raise

    async def setnx(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value only if key does not exist."""
        return await self.set(key, value, ttl=ttl, nx=True)

    async def getset(self, key: str, value: Any) -> Optional[Any]:
        """Get old value and set new value atomically."""
        if not self._connected:
            await self.connect()

        try:
            serialized = self.serializer.serialize(value)
            old_data = await self._client.getset(key, serialized)
            if old_data is None:
                return None
            return self.serializer.deserialize(old_data)
        except Exception as e:
            logger.error(f"Error in getset for key {key}: {e}")
            raise

    async def delete(self, *keys: str) -> int:
        """Delete one or more keys."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Error deleting keys {keys}: {e}")
            raise

    async def exists(self, key: str) -> bool:
        """Check if key exists."""
        if not self._connected:
            await self.connect()

        try:
            result = await self._client.exists(key)
            return result > 0
        except Exception as e:
            logger.error(f"Error checking existence of key {key}: {e}")
            raise

    async def ttl(self, key: str) -> int:
        """Get TTL of a key in seconds. Returns -2 if key doesn't exist, -1 if no TTL."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.ttl(key)
        except Exception as e:
            logger.error(f"Error getting TTL for key {key}: {e}")
            raise

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration time on a key."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.expire(key, seconds)
        except Exception as e:
            logger.error(f"Error setting expiration for key {key}: {e}")
            raise

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys at once. Returns dict of key -> value."""
        if not self._connected:
            await self.connect()

        if not keys:
            return {}

        try:
            values = await self._client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self.serializer.deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Error in mget: {e}")
            raise

    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple keys at once."""
        if not self._connected:
            await self.connect()

        if not mapping:
            return True

        try:
            # Serialize all values
            serialized_mapping = {k: self.serializer.serialize(v) for k, v in mapping.items()}

            # Use pipeline for atomic operation
            async with self._client.pipeline() as pipe:
                pipe.mset(serialized_mapping)
                if ttl:
                    for key in mapping.keys():
                        pipe.expire(key, ttl)
                await pipe.execute()

            return True
        except Exception as e:
            logger.error(f"Error in mset: {e}")
            raise

    async def incr(self, key: str, amount: int = 1) -> int:
        """Increment a key's value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.incr(key, amount)
        except Exception as e:
            logger.error(f"Error incrementing key {key}: {e}")
            raise

    async def decr(self, key: str, amount: int = 1) -> int:
        """Decrement a key's value."""
        if not self._connected:
            await self.connect()

        try:
            return await self._client.decr(key, amount)
        except Exception as e:
            logger.error(f"Error decrementing key {key}: {e}")
            raise

    async def keys(self, pattern: str = "*") -> List[str]:
        """Get keys matching pattern. Use with caution in production."""
        if not self._connected:
            await self.connect()

        try:
            result = await self._client.keys(pattern)
            if isinstance(result, list):
                return [k.decode("utf-8") if isinstance(k, bytes) else k for k in result]
            return []
        except Exception as e:
            logger.error(f"Error getting keys with pattern {pattern}: {e}")
            raise

    async def scan_keys(self, pattern: str = "*", count: int = 100, cursor: int = 0) -> tuple:
        """Scan keys matching pattern (non-blocking)."""
        if not self._connected:
            await self.connect()

        try:
            new_cursor, keys = await self._client.scan(cursor=cursor, match=pattern, count=count)
            decoded_keys = [k.decode("utf-8") if isinstance(k, bytes) else k for k in keys]
            return new_cursor, decoded_keys
        except Exception as e:
            logger.error(f"Error scanning keys: {e}")
            raise

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self._connected:
            await self.connect()

        deleted = 0
        cursor = 0

        try:
            while True:
                cursor, keys = await self.scan_keys(pattern, count=100, cursor=cursor)
                if keys:
                    deleted += await self._client.delete(*keys)
                if cursor == 0:
                    break
            return deleted
        except Exception as e:
            logger.error(f"Error deleting pattern {pattern}: {e}")
            raise

    @asynccontextmanager
    async def pipeline(self):
        """Context manager for Redis pipeline operations."""
        if not self._connected:
            await self.connect()

        async with self._client.pipeline() as pipe:
            yield pipe

    async def subscribe(self, channel: str, callback: Callable[[str, Any], None]) -> None:
        """Subscribe to a Pub/Sub channel."""
        if not self._connected:
            await self.connect()

        try:
            self._pubsub = self._client.pubsub()
            await self._pubsub.subscribe(channel)

            # Start listener task
            asyncio.create_task(self._pubsub_listener(callback))

        except Exception as e:
            logger.error(f"Error subscribing to channel {channel}: {e}")
            raise

    async def _pubsub_listener(self, callback: Callable[[str, Any], None]) -> None:
        """Listen for Pub/Sub messages."""
        try:
            async for message in self._pubsub.listen():
                if message["type"] == "message":
                    channel = message["channel"].decode("utf-8")
                    data = self.serializer.deserialize(message["data"])
                    await callback(channel, data)
        except Exception as e:
            logger.error(f"Error in Pub/Sub listener: {e}")

    async def publish(self, channel: str, message: Any) -> int:
        """Publish message to a channel."""
        if not self._connected:
            await self.connect()

        try:
            serialized = self.serializer.serialize(message)
            return await self._client.publish(channel, serialized)
        except Exception as e:
            logger.error(f"Error publishing to channel {channel}: {e}")
            raise

    def get_stats(self) -> ConnectionStats:
        """Get connection statistics."""
        if self._pool:
            self._stats.total_connections = len(self._pool._connections)
        return self._stats

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()


class RedisClusterClient(BaseRedisClient):
    """
    Redis Cluster client for distributed caching.

    Features:
        - Automatic sharding across cluster nodes
        - Node failure handling
        - Read from replicas support
    """

    def __init__(
        self,
        startup_nodes: List[Dict[str, Union[str, int]]],
        serializer: Optional[Serializer] = None,
        skip_full_coverage_check: bool = False,
        max_connections_per_node: int = 50,
    ):
        if not REDIS_AVAILABLE or RedisCluster is None:
            raise ImportError("Redis cluster support not available")

        self.startup_nodes = startup_nodes
        self.serializer = serializer or Serializer()
        self.skip_full_coverage_check = skip_full_coverage_check
        self.max_connections_per_node = max_connections_per_node
        self._cluster: Optional[RedisCluster] = None
        self._connected = False
        self._lock = asyncio.Lock()

    async def connect(self) -> None:
        """Connect to Redis Cluster."""
        async with self._lock:
            if self._connected:
                return

            try:
                self._cluster = RedisCluster(
                    startup_nodes=self.startup_nodes,
                    skip_full_coverage_check=self.skip_full_coverage_check,
                    max_connections_per_node=self.max_connections_per_node,
                    decode_responses=False,
                )

                # Test connection
                await self._cluster.ping()

                self._connected = True
                logger.info(f"Connected to Redis Cluster with {len(self.startup_nodes)} nodes")

            except Exception as e:
                logger.error(f"Failed to connect to Redis Cluster: {e}")
                raise ConnectionError(f"Redis Cluster connection failed: {e}")

    async def disconnect(self) -> None:
        """Disconnect from Redis Cluster."""
        async with self._lock:
            if self._cluster:
                await self._cluster.close()
                self._connected = False
                logger.info("Disconnected from Redis Cluster")

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cluster."""
        if not self._connected:
            await self.connect()

        data = await self._cluster.get(key)
        if data is None:
            return None
        return self.serializer.deserialize(data)

    async def set(self, key: str, value: Any, ttl: Optional[int] = None, nx: bool = False, xx: bool = False) -> bool:
        """Set value in cluster."""
        if not self._connected:
            await self.connect()

        serialized = self.serializer.serialize(value)

        kwargs = {}
        if ttl is not None:
            kwargs["ex"] = ttl
        if nx:
            kwargs["nx"] = True
        if xx:
            kwargs["xx"] = True

        result = await self._cluster.set(key, serialized, **kwargs)
        return result is True

    async def delete(self, *keys: str) -> int:
        """Delete keys from cluster."""
        if not self._connected:
            await self.connect()

        return await self._cluster.delete(*keys)

    async def exists(self, key: str) -> bool:
        """Check if key exists in cluster."""
        if not self._connected:
            await self.connect()

        result = await self._cluster.exists(key)
        return result > 0

    async def ttl(self, key: str) -> int:
        """Get TTL from cluster."""
        if not self._connected:
            await self.connect()

        return await self._cluster.ttl(key)

    async def expire(self, key: str, seconds: int) -> bool:
        """Set expiration in cluster."""
        if not self._connected:
            await self.connect()

        return await self._cluster.expire(key, seconds)

    async def mget(self, keys: List[str]) -> Dict[str, Any]:
        """Get multiple keys from cluster."""
        if not self._connected:
            await self.connect()

        if not keys:
            return {}

        values = await self._cluster.mget(keys)
        result = {}
        for key, value in zip(keys, values):
            if value is not None:
                result[key] = self.serializer.deserialize(value)
        return result

    async def mset(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple keys in cluster."""
        if not self._connected:
            await self.connect()

        if not mapping:
            return True

        serialized_mapping = {k: self.serializer.serialize(v) for k, v in mapping.items()}

        await self._cluster.mset(serialized_mapping)

        if ttl:
            for key in mapping.keys():
                await self._cluster.expire(key, ttl)

        return True

    async def health_check(self) -> Dict[str, Any]:
        """Check cluster health."""
        if not self._connected:
            return {"status": "disconnected", "healthy": False}

        try:
            await self._cluster.ping()
            cluster_info = await self._cluster.cluster_info()

            return {
                "status": "connected",
                "healthy": True,
                "cluster_slots_assigned": cluster_info.get("cluster_slots_assigned", 0),
                "cluster_slots_ok": cluster_info.get("cluster_slots_ok", 0),
                "cluster_known_nodes": cluster_info.get("cluster_known_nodes", 0),
            }
        except Exception as e:
            return {"status": "error", "healthy": False, "error": str(e)}


# Convenience factory function
async def create_redis_client(url: str = "redis://localhost:6379/0", **kwargs) -> RedisClient:
    """
    Factory function to create and connect a Redis client.

    Args:
        url: Redis connection URL
        **kwargs: Additional configuration options

    Returns:
        Connected RedisClient instance
    """
    config = RedisConfig(url=url, **kwargs)
    client = RedisClient(config)
    await client.connect()
    return client


# Import datetime for serializer
from datetime import datetime
