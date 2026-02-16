"""Tests for token bucket rate limiter (mocked Redis)."""

import pytest

from shared_infra.rate_limiter import TokenBucketRateLimiter


@pytest.fixture
def rate_limiter(mock_redis):
    return TokenBucketRateLimiter(
        redis=mock_redis, default_max_tokens=10, default_refill_rate=1.0
    )


class TestCheckRateLimit:
    async def test_allowed_by_default(self, rate_limiter):
        result = await rate_limiter.check_rate_limit("tenant1")
        assert result is True

    async def test_custom_limits(self, rate_limiter):
        result = await rate_limiter.check_rate_limit(
            "tenant1", max_tokens=50, refill_rate=5.0
        )
        assert result is True

    async def test_per_endpoint_keys(self, rate_limiter):
        r1 = await rate_limiter.check_rate_limit("t1", endpoint="api/query")
        r2 = await rate_limiter.check_rate_limit("t1", endpoint="api/upload")
        assert r1 is True
        assert r2 is True

    async def test_multiple_tokens_requested(self, rate_limiter):
        result = await rate_limiter.check_rate_limit("t1", tokens_requested=5)
        assert result is True


class TestGetRemainingTokens:
    async def test_full_bucket(self, rate_limiter):
        remaining = await rate_limiter.get_remaining_tokens("new_tenant")
        assert remaining == 10.0

    async def test_partial_bucket(self, rate_limiter, mock_redis):
        import time
        mock_redis._hash_store["ratelimit:bucket:t1:default"] = {
            "tokens": "5",
            "last_refill": str(time.time() - 2),
        }
        remaining = await rate_limiter.get_remaining_tokens("t1")
        # 5 tokens + ~2 seconds * 1 token/sec = ~7
        assert remaining >= 6.0
        assert remaining <= 10.0


class TestReset:
    async def test_reset_bucket(self, rate_limiter, mock_redis):
        mock_redis._hash_store["ratelimit:bucket:t1:default"] = {"tokens": "0"}
        await rate_limiter.reset("t1")
        remaining = await rate_limiter.get_remaining_tokens("t1")
        assert remaining == 10.0


class TestScriptReload:
    async def test_handles_script_eviction(self, rate_limiter, mock_redis):
        """Verify that the limiter reloads its Lua script if Redis evicts it."""
        from redis.exceptions import NoScriptError

        call_count = 0

        async def failing_then_ok(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise NoScriptError("NOSCRIPT")
            return 1

        mock_redis.evalsha = failing_then_ok
        # Force script load so _script_sha is set
        await rate_limiter._ensure_script()

        result = await rate_limiter.check_rate_limit("t1")
        assert result is True
        assert call_count == 2  # First call failed, second succeeded after reload
