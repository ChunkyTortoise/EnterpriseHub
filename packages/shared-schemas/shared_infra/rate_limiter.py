"""Redis-backed token bucket rate limiter."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from shared_schemas.tenant import TenantTier

_TIER_LIMITS: dict[TenantTier, int] = {
    TenantTier.FREE: 10,
    TenantTier.STARTER: 60,
    TenantTier.PRO: 300,
    TenantTier.ENTERPRISE: 1000,
}

_RATE_LIMIT_SCRIPT = """
local key = KEYS[1]
local limit = tonumber(ARGV[1])
local window = tonumber(ARGV[2])
local now = tonumber(ARGV[3])

local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
local tokens = tonumber(bucket[1])
local last_refill = tonumber(bucket[2])

if tokens == nil then
    tokens = limit
    last_refill = now
end

local elapsed = now - last_refill
local refill = math.floor(elapsed * limit / window)
tokens = math.min(limit, tokens + refill)
last_refill = now

if tokens > 0 then
    tokens = tokens - 1
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, window * 2)
    return {1, tokens, now + window}
else
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
    redis.call('EXPIRE', key, window * 2)
    return {0, 0, now + window}
end
"""


class RateLimitResult:
    """Result of a rate limit check."""

    __slots__ = ("allowed", "remaining", "reset_at")

    def __init__(self, allowed: bool, remaining: int, reset_at: datetime) -> None:
        self.allowed = allowed
        self.remaining = remaining
        self.reset_at = reset_at


class RateLimiter:
    """Per-tenant rate limiter backed by Redis."""

    def __init__(self, redis_client: Any, custom_limits: dict[TenantTier, int] | None = None) -> None:
        self._redis = redis_client
        self._limits = {**_TIER_LIMITS, **(custom_limits or {})}
        self._script_sha: str | None = None

    def _get_limit(self, tier: TenantTier) -> int:
        return self._limits.get(tier, _TIER_LIMITS[TenantTier.FREE])

    async def _ensure_script(self) -> str:
        if self._script_sha is None:
            self._script_sha = await self._redis.script_load(_RATE_LIMIT_SCRIPT)
        return self._script_sha

    async def check_rate_limit(
        self,
        tenant_id: str,
        endpoint: str,
        tier: TenantTier,
    ) -> RateLimitResult:
        """Check if a request is within rate limits."""
        limit = self._get_limit(tier)
        window = 60
        key = f"ratelimit:{tenant_id}:{endpoint}"
        now = int(datetime.utcnow().timestamp())

        sha = await self._ensure_script()
        result = await self._redis.evalsha(sha, 1, key, limit, window, now)

        allowed = bool(result[0])
        remaining = int(result[1])
        reset_at = datetime.utcfromtimestamp(int(result[2]))

        return RateLimitResult(allowed=allowed, remaining=remaining, reset_at=reset_at)
