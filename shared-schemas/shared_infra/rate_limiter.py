"""Redis-backed token bucket rate limiter with per-tenant configuration."""

from __future__ import annotations

import time
import logging

from redis import asyncio as aioredis
from redis.exceptions import NoScriptError

logger = logging.getLogger(__name__)

# Lua script for atomic token bucket operation
TOKEN_BUCKET_SCRIPT = """
local key = KEYS[1]
local max_tokens = tonumber(ARGV[1])
local refill_rate = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = max_tokens
    last_refill = now
end

-- Refill tokens based on elapsed time
local elapsed = now - last_refill
local new_tokens = elapsed * refill_rate
tokens = math.min(max_tokens, tokens + new_tokens)

-- Try to consume tokens
if tokens >= requested then
    tokens = tokens - requested
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return 1  -- allowed
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return 0  -- denied
end
"""


class TokenBucketRateLimiter:
    """Redis-backed token bucket rate limiter.

    Supports per-tenant configurable limits with atomic Redis operations.
    """

    def __init__(
        self,
        redis: aioredis.Redis,
        default_max_tokens: int = 100,
        default_refill_rate: float = 10.0,  # tokens per second
    ):
        self.redis = redis
        self.default_max_tokens = default_max_tokens
        self.default_refill_rate = default_refill_rate
        self._script_sha: str | None = None

    async def _ensure_script(self) -> str:
        """Load the Lua script into Redis if not already loaded."""
        if self._script_sha is None:
            self._script_sha = await self.redis.script_load(TOKEN_BUCKET_SCRIPT)
        return self._script_sha

    async def check_rate_limit(
        self,
        tenant_id: str,
        endpoint: str = "default",
        max_tokens: int | None = None,
        refill_rate: float | None = None,
        tokens_requested: int = 1,
    ) -> bool:
        """Check if a request is within rate limits.

        Args:
            tenant_id: The tenant making the request.
            endpoint: Optional endpoint identifier for per-endpoint limits.
            max_tokens: Max bucket size (overrides default).
            refill_rate: Tokens per second refill rate (overrides default).
            tokens_requested: Number of tokens this request consumes.

        Returns:
            True if the request is allowed, False if rate limited.
        """
        key = f"ratelimit:bucket:{tenant_id}:{endpoint}"
        now = time.time()
        max_t = max_tokens or self.default_max_tokens
        rate = refill_rate or self.default_refill_rate

        sha = await self._ensure_script()
        try:
            result = await self.redis.evalsha(
                sha, 1, key, str(max_t), str(rate), str(now), str(tokens_requested)
            )
            return bool(result)
        except NoScriptError:
            # Script evicted from cache, reload
            self._script_sha = None
            sha = await self._ensure_script()
            result = await self.redis.evalsha(
                sha, 1, key, str(max_t), str(rate), str(now), str(tokens_requested)
            )
            return bool(result)

    async def get_remaining_tokens(self, tenant_id: str, endpoint: str = "default") -> float:
        """Get the approximate number of remaining tokens for a tenant."""
        key = f"ratelimit:bucket:{tenant_id}:{endpoint}"
        data = await self.redis.hmget(key, "tokens", "last_refill")

        if data[0] is None:
            return float(self.default_max_tokens)

        tokens = float(data[0])
        last_refill = float(data[1])
        elapsed = time.time() - last_refill
        refilled = elapsed * self.default_refill_rate
        return min(self.default_max_tokens, tokens + refilled)

    async def reset(self, tenant_id: str, endpoint: str = "default") -> None:
        """Reset the rate limit bucket for a tenant."""
        key = f"ratelimit:bucket:{tenant_id}:{endpoint}"
        await self.redis.delete(key)
