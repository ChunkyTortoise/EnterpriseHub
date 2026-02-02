"""Tests for RedisCacheBackend with mocked redis.asyncio — no running Redis needed."""

import pickle
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.embeddings.cache import RedisCacheBackend


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_redis_client():
    """Create a mock redis.asyncio client."""
    client = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.get = AsyncMock(return_value=None)
    client.setex = AsyncMock()
    client.delete = AsyncMock(return_value=1)
    client.scan = AsyncMock(return_value=(0, []))
    client.aclose = AsyncMock()
    return client


@pytest.fixture
def backend():
    return RedisCacheBackend(
        redis_url="redis://localhost:6379/0",
        key_prefix="test:",
        default_ttl=300,
    )


# ---------------------------------------------------------------------------
# Tests: Initialization & Connection Lifecycle
# ---------------------------------------------------------------------------

class TestInitialization:

    @pytest.mark.asyncio
    async def test_initialize_success(self, backend, mock_redis_client):
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        assert backend._available is True
        assert backend._client is mock_redis_client
        mock_redis_client.ping.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_initialize_import_error(self, backend):
        """When redis package is not installed, backend stays disabled."""
        with patch.dict("sys.modules", {"redis": None, "redis.asyncio": None}):
            # Force ImportError
            with patch("builtins.__import__", side_effect=ImportError("No module named 'redis'")):
                await backend.initialize()
        assert backend._available is False

    @pytest.mark.asyncio
    async def test_initialize_connection_refused(self, backend):
        """When Redis server is unreachable, backend stays disabled."""
        mock_client = AsyncMock()
        mock_client.ping = AsyncMock(side_effect=ConnectionError("Connection refused"))
        with patch("redis.asyncio.from_url", return_value=mock_client):
            await backend.initialize()
        assert backend._available is False

    @pytest.mark.asyncio
    async def test_close(self, backend, mock_redis_client):
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        await backend.close()
        assert backend._available is False
        assert backend._client is None
        mock_redis_client.aclose.assert_awaited_once()


# ---------------------------------------------------------------------------
# Tests: GET
# ---------------------------------------------------------------------------

class TestGet:

    @pytest.mark.asyncio
    async def test_get_hit(self, backend, mock_redis_client):
        value = [1.0, 2.0, 3.0]
        mock_redis_client.get = AsyncMock(return_value=pickle.dumps(value))

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        result = await backend.get("mykey")
        assert result == value
        mock_redis_client.get.assert_awaited_with("test:mykey")

    @pytest.mark.asyncio
    async def test_get_miss(self, backend, mock_redis_client):
        mock_redis_client.get = AsyncMock(return_value=None)

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        result = await backend.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_when_unavailable(self, backend):
        result = await backend.get("anything")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_error_returns_none(self, backend, mock_redis_client):
        mock_redis_client.get = AsyncMock(side_effect=Exception("timeout"))

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        result = await backend.get("bad")
        assert result is None


# ---------------------------------------------------------------------------
# Tests: SET
# ---------------------------------------------------------------------------

class TestSet:

    @pytest.mark.asyncio
    async def test_set_with_ttl(self, backend, mock_redis_client):
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        value = [0.1, 0.2]
        await backend.set("k", value, ttl=60)
        mock_redis_client.setex.assert_awaited_once_with(
            "test:k", 60, pickle.dumps(value)
        )

    @pytest.mark.asyncio
    async def test_set_uses_default_ttl_when_zero(self, backend, mock_redis_client):
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        await backend.set("k", [1.0], ttl=0)
        args = mock_redis_client.setex.call_args
        assert args[0][1] == 300  # default_ttl

    @pytest.mark.asyncio
    async def test_set_when_unavailable(self, backend):
        # Should not raise
        await backend.set("k", [1.0], ttl=10)

    @pytest.mark.asyncio
    async def test_set_error_swallowed(self, backend, mock_redis_client):
        mock_redis_client.setex = AsyncMock(side_effect=Exception("write fail"))
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        # Should not raise
        await backend.set("k", [1.0], ttl=10)


# ---------------------------------------------------------------------------
# Tests: DELETE
# ---------------------------------------------------------------------------

class TestDelete:

    @pytest.mark.asyncio
    async def test_delete_existing(self, backend, mock_redis_client):
        mock_redis_client.delete = AsyncMock(return_value=1)
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        result = await backend.delete("k")
        assert result is True

    @pytest.mark.asyncio
    async def test_delete_missing(self, backend, mock_redis_client):
        mock_redis_client.delete = AsyncMock(return_value=0)
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        result = await backend.delete("nope")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_when_unavailable(self, backend):
        result = await backend.delete("k")
        assert result is False


# ---------------------------------------------------------------------------
# Tests: CLEAR
# ---------------------------------------------------------------------------

class TestClear:

    @pytest.mark.asyncio
    async def test_clear_scans_and_deletes(self, backend, mock_redis_client):
        keys_batch = [b"test:a", b"test:b"]
        mock_redis_client.scan = AsyncMock(return_value=(0, keys_batch))
        mock_redis_client.delete = AsyncMock(return_value=2)

        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()

        await backend.clear()
        mock_redis_client.scan.assert_awaited()
        mock_redis_client.delete.assert_awaited_with(*keys_batch)

    @pytest.mark.asyncio
    async def test_clear_empty(self, backend, mock_redis_client):
        mock_redis_client.scan = AsyncMock(return_value=(0, []))
        with patch("redis.asyncio.from_url", return_value=mock_redis_client):
            await backend.initialize()
        await backend.clear()  # Should not raise

    @pytest.mark.asyncio
    async def test_clear_when_unavailable(self, backend):
        await backend.clear()  # Should not raise
