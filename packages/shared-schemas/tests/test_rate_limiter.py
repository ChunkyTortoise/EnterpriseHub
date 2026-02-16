"""Tests for rate limiter."""

from unittest.mock import AsyncMock

import pytest

from shared_infra.rate_limiter import RateLimiter
from shared_schemas.tenant import TenantTier


@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.script_load = AsyncMock(return_value="fake_sha")
    redis.evalsha = AsyncMock(return_value=[1, 9, 1700000060])
    return redis


@pytest.fixture
def limiter(mock_redis):
    return RateLimiter(mock_redis)


class TestRateLimiter:
    @pytest.mark.asyncio
    async def test_allowed_request(self, limiter, mock_redis):
        mock_redis.evalsha.return_value = [1, 9, 1700000060]
        result = await limiter.check_rate_limit("t-1", "/api/query", TenantTier.FREE)
        assert result.allowed is True
        assert result.remaining == 9

    @pytest.mark.asyncio
    async def test_denied_request(self, limiter, mock_redis):
        mock_redis.evalsha.return_value = [0, 0, 1700000060]
        result = await limiter.check_rate_limit("t-1", "/api/query", TenantTier.FREE)
        assert result.allowed is False
        assert result.remaining == 0

    @pytest.mark.asyncio
    async def test_script_loaded_once(self, limiter, mock_redis):
        await limiter.check_rate_limit("t-1", "/a", TenantTier.FREE)
        await limiter.check_rate_limit("t-1", "/b", TenantTier.FREE)
        mock_redis.script_load.assert_called_once()

    @pytest.mark.asyncio
    async def test_key_format(self, limiter, mock_redis):
        await limiter.check_rate_limit("tenant-abc", "/api/v1/query", TenantTier.PRO)
        call_args = mock_redis.evalsha.call_args
        assert call_args[0][2] == "ratelimit:tenant-abc:/api/v1/query"

    @pytest.mark.asyncio
    async def test_tier_limits_passed(self, limiter, mock_redis):
        await limiter.check_rate_limit("t-1", "/api", TenantTier.FREE)
        call_args = mock_redis.evalsha.call_args
        assert call_args[0][3] == 10

        await limiter.check_rate_limit("t-2", "/api", TenantTier.ENTERPRISE)
        call_args = mock_redis.evalsha.call_args
        assert call_args[0][3] == 1000

    @pytest.mark.asyncio
    async def test_custom_limits(self, mock_redis):
        custom = {TenantTier.FREE: 5, TenantTier.PRO: 500}
        limiter = RateLimiter(mock_redis, custom_limits=custom)
        await limiter.check_rate_limit("t-1", "/api", TenantTier.FREE)
        call_args = mock_redis.evalsha.call_args
        assert call_args[0][3] == 5

    @pytest.mark.asyncio
    async def test_reset_at_populated(self, limiter, mock_redis):
        mock_redis.evalsha.return_value = [1, 5, 1700000060]
        result = await limiter.check_rate_limit("t-1", "/api", TenantTier.FREE)
        assert result.reset_at is not None
