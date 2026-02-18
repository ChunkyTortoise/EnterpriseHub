"""
Tests for Redis Client Module
=============================

Tests cover:
    - Connection management
    - Serialization/deserialization
    - Basic operations (get, set, delete)
    - Batch operations (mget, mset)
    - Key scanning and pattern matching
    - Pub/Sub functionality
    - Health checks
    - Error handling
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import pytest
import pytest_asyncio

# Skip all tests if redis is not available
try:
    import redis.asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.caching.redis_client import (

    ConnectionStats,
    RedisClient,
    RedisConfig,
    SerializationFormat,
    Serializer,
)

pytestmark = pytest.mark.asyncio


class TestSerializer:
    """Test cases for Serializer class."""

    def test_json_serialize_dict(self):
        """Test JSON serialization of dictionary."""
        serializer = Serializer(SerializationFormat.JSON)
        data = {"key": "value", "number": 42}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

    def test_json_serialize_list(self):
        """Test JSON serialization of list."""
        serializer = Serializer(SerializationFormat.JSON)
        data = [1, 2, 3, "test"]
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == data

    def test_json_serialize_datetime(self):
        """Test JSON serialization handles datetime."""
        serializer = Serializer(SerializationFormat.JSON)
        data = {"timestamp": datetime(2024, 1, 1, 12, 0, 0)}
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized["timestamp"] == "2024-01-01T12:00:00"

    def test_pickle_serialize(self):
        """Test pickle serialization."""
        serializer = Serializer(SerializationFormat.PICKLE)
        data = {"complex": object()}  # Pickle can serialize objects
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert isinstance(deserialized, dict)

    def test_string_serialize(self):
        """Test string serialization."""
        serializer = Serializer(SerializationFormat.STRING)
        data = 12345
        serialized = serializer.serialize(data)
        deserialized = serializer.deserialize(serialized)
        assert deserialized == "12345"

    def test_deserialize_none(self):
        """Test deserializing None returns None."""
        serializer = Serializer()
        result = serializer.deserialize(None)
        assert result is None


class TestRedisConfig:
    """Test cases for RedisConfig dataclass."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RedisConfig()
        assert config.url == "redis://localhost:6379/0"
        assert config.max_connections == 50
        assert config.socket_timeout == 5.0

    def test_custom_config(self):
        """Test custom configuration values."""
        config = RedisConfig(url="redis://custom:6379/1", max_connections=100, socket_timeout=10.0)
        assert config.url == "redis://custom:6379/1"
        assert config.max_connections == 100
        assert config.socket_timeout == 10.0


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")
class TestRedisClient:
    """Test cases for RedisClient class."""

    @pytest_asyncio.fixture
    async def mock_redis_client(self):
        """Create a RedisClient with mocked Redis connection."""
        with patch("src.caching.redis_client.ConnectionPool") as mock_pool:
            with patch("src.caching.redis_client.aioredis.Redis") as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis_class.return_value = mock_redis
                mock_pool.from_url.return_value = MagicMock()

                client = RedisClient("redis://localhost:6379/0")
                client._pool = mock_pool
                client._client = mock_redis
                client._connected = True

                yield client, mock_redis

    async def test_connect_success(self):
        """Test successful connection to Redis."""
        with patch("src.caching.redis_client.ConnectionPool") as mock_pool:
            with patch("src.caching.redis_client.aioredis.Redis") as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis.ping.return_value = True
                mock_redis_class.return_value = mock_redis

                client = RedisClient("redis://localhost:6379/0")
                await client.connect()

                assert client._connected is True
                mock_redis.ping.assert_called_once()

    async def test_connect_failure(self):
        """Test connection failure handling."""
        with patch("src.caching.redis_client.ConnectionPool"):
            with patch("src.caching.redis_client.aioredis.Redis") as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis.ping.side_effect = Exception("Connection refused")
                mock_redis_class.return_value = mock_redis

                client = RedisClient("redis://localhost:6379/0")

                with pytest.raises(Exception):
                    await client.connect()

    async def test_get_existing_key(self, mock_redis_client):
        """Test getting an existing key."""
        client, mock_redis = mock_redis_client

        mock_redis.get.return_value = b'{"data": "value"}'

        result = await client.get("test_key")

        assert result == {"data": "value"}
        mock_redis.get.assert_called_once_with("test_key")

    async def test_get_missing_key(self, mock_redis_client):
        """Test getting a non-existent key."""
        client, mock_redis = mock_redis_client

        mock_redis.get.return_value = None

        result = await client.get("missing_key")

        assert result is None

    async def test_set_with_ttl(self, mock_redis_client):
        """Test setting a key with TTL."""
        client, mock_redis = mock_redis_client

        mock_redis.set.return_value = True

        result = await client.set("test_key", {"data": "value"}, ttl=300)

        assert result is True
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == "test_key"
        assert call_args[1]["ex"] == 300

    async def test_set_nx(self, mock_redis_client):
        """Test set only if not exists."""
        client, mock_redis = mock_redis_client

        mock_redis.set.return_value = True

        result = await client.set("test_key", "value", nx=True)

        assert result is True
        call_args = mock_redis.set.call_args
        assert call_args[1]["nx"] is True

    async def test_delete_single_key(self, mock_redis_client):
        """Test deleting a single key."""
        client, mock_redis = mock_redis_client

        mock_redis.delete.return_value = 1

        result = await client.delete("test_key")

        assert result == 1
        mock_redis.delete.assert_called_once_with("test_key")

    async def test_delete_multiple_keys(self, mock_redis_client):
        """Test deleting multiple keys."""
        client, mock_redis = mock_redis_client

        mock_redis.delete.return_value = 3

        result = await client.delete("key1", "key2", "key3")

        assert result == 3
        mock_redis.delete.assert_called_once_with("key1", "key2", "key3")

    async def test_exists_true(self, mock_redis_client):
        """Test checking existence of existing key."""
        client, mock_redis = mock_redis_client

        mock_redis.exists.return_value = 1

        result = await client.exists("test_key")

        assert result is True

    async def test_exists_false(self, mock_redis_client):
        """Test checking existence of non-existent key."""
        client, mock_redis = mock_redis_client

        mock_redis.exists.return_value = 0

        result = await client.exists("test_key")

        assert result is False

    async def test_ttl_existing(self, mock_redis_client):
        """Test getting TTL of key with expiration."""
        client, mock_redis = mock_redis_client

        mock_redis.ttl.return_value = 300

        result = await client.ttl("test_key")

        assert result == 300

    async def test_expire(self, mock_redis_client):
        """Test setting expiration on key."""
        client, mock_redis = mock_redis_client

        mock_redis.expire.return_value = True

        result = await client.expire("test_key", 600)

        assert result is True
        mock_redis.expire.assert_called_once_with("test_key", 600)

    async def test_mget(self, mock_redis_client):
        """Test getting multiple keys."""
        client, mock_redis = mock_redis_client

        mock_redis.mget.return_value = [b'"value1"', None, b'"value3"']

        result = await client.mget(["key1", "key2", "key3"])

        assert result == {"key1": "value1", "key3": "value3"}

    async def test_mget_empty(self, mock_redis_client):
        """Test mget with empty key list."""
        client, mock_redis = mock_redis_client

        result = await client.mget([])

        assert result == {}

    async def test_mset(self, mock_redis_client):
        """Test setting multiple keys."""
        client, mock_redis = mock_redis_client

        mock_redis.pipeline.return_value.__aenter__ = AsyncMock()
        mock_redis.pipeline.return_value.__aexit__ = AsyncMock()

        result = await client.mset({"key1": "value1", "key2": "value2"})

        assert result is True

    async def test_incr(self, mock_redis_client):
        """Test incrementing a counter."""
        client, mock_redis = mock_redis_client

        mock_redis.incr.return_value = 6

        result = await client.incr("counter", amount=5)

        assert result == 6
        mock_redis.incr.assert_called_once_with("counter", 5)

    async def test_decr(self, mock_redis_client):
        """Test decrementing a counter."""
        client, mock_redis = mock_redis_client

        mock_redis.decr.return_value = 3

        result = await client.decr("counter", amount=2)

        assert result == 3
        mock_redis.decr.assert_called_once_with("counter", 2)

    async def test_scan_keys(self, mock_redis_client):
        """Test scanning keys with pattern."""
        client, mock_redis = mock_redis_client

        mock_redis.scan.return_value = (0, [b"key1", b"key2"])

        cursor, keys = await client.scan_keys(pattern="test:*", count=10)

        assert cursor == 0
        assert keys == ["key1", "key2"]

    async def test_health_check_healthy(self, mock_redis_client):
        """Test health check when Redis is healthy."""
        client, mock_redis = mock_redis_client

        mock_redis.ping.return_value = True
        mock_redis.info.return_value = {
            "redis_version": "6.2.0",
            "used_memory_human": "1.5M",
            "connected_clients": 10,
        }

        result = await client.health_check()

        assert result["status"] == "connected"
        assert result["healthy"] is True
        assert "latency_ms" in result

    async def test_health_check_unhealthy(self, mock_redis_client):
        """Test health check when Redis is unhealthy."""
        client, mock_redis = mock_redis_client

        mock_redis.ping.side_effect = Exception("Connection lost")

        result = await client.health_check()

        assert result["status"] == "error"
        assert result["healthy"] is False

    async def test_context_manager(self):
        """Test async context manager."""
        with patch("src.caching.redis_client.ConnectionPool"):
            with patch("src.caching.redis_client.aioredis.Redis") as mock_redis_class:
                mock_redis = AsyncMock()
                mock_redis_class.return_value = mock_redis

                async with RedisClient("redis://localhost:6379/0") as client:
                    assert client._connected is True


class TestConnectionStats:
    """Test cases for ConnectionStats."""

    def test_default_stats(self):
        """Test default statistics values."""
        stats = ConnectionStats()
        assert stats.total_connections == 0
        assert stats.available_connections == 0
        assert stats.connection_errors == 0

    def test_custom_stats(self):
        """Test custom statistics values."""
        stats = ConnectionStats(
            total_connections=10, available_connections=5, in_use_connections=5, max_connections=20, connection_errors=2
        )
        assert stats.total_connections == 10
        assert stats.available_connections == 5
        assert stats.connection_errors == 2
