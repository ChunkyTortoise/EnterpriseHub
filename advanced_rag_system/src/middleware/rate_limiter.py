"""Rate limiting implementation for Advanced RAG System.

Provides token bucket and sliding window rate limiting algorithms to protect
API endpoints from abuse and ensure fair resource allocation.

Features:
- Token bucket algorithm for smooth rate limiting
- Sliding window for precise control
- Per-user, per-IP, and per-endpoint limiting
- Redis backend for distributed rate limiting
- In-memory fallback for single-instance deployments
- Async support with proper concurrency handling
- Rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- Automatic 429 Too Many Requests responses
- Metrics integration for monitoring

Example:
    ```python
    # Using decorator
    @rate_limiter(limit=100, window=60, key="user_id")
    async def search_endpoint(request):
        return await perform_search(request.query)

    # Using context manager
    limiter = RateLimiter(
        config=RateLimitConfig(rate=100, burst=150)
    )

    async with limiter.acquire(key="user_123") as result:
        if not result.allowed:
            raise HTTPException(status_code=429)
        return await process_request()

    # Direct usage with headers
    limiter = RateLimiter(config=RateLimitConfig(rate=100, window=60))
    allowed, headers = await limiter.check_limit(key="user_123")

    if not allowed:
        return Response(
            status_code=429,
            headers=headers,
            content="Rate limit exceeded"
        )
    ```
"""

from __future__ import annotations

import asyncio
import functools
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Optional, Tuple, TypeVar, cast

from pydantic import BaseModel, Field, field_validator

from src.core.config import Settings, get_settings
from src.core.exceptions import RAGException
from src.monitoring.metrics import MetricsCollector, metrics_collector
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class RateLimitAlgorithm(str, Enum):
    """Rate limiting algorithms.

    Attributes:
        TOKEN_BUCKET: Token bucket for smooth rate limiting
        SLIDING_WINDOW: Sliding window for precise control
    """

    TOKEN_BUCKET = "token_bucket"
    SLIDING_WINDOW = "sliding_window"


class RateLimitBackend(str, Enum):
    """Rate limiter backend types.

    Attributes:
        MEMORY: In-memory storage (single instance)
        REDIS: Redis storage (distributed)
    """

    MEMORY = "memory"
    REDIS = "redis"


class RateLimitConfig(BaseModel):
    """Configuration for rate limiter.

    Attributes:
        rate: Maximum requests per window
        window: Time window in seconds
        burst: Maximum burst capacity (for token bucket)
        algorithm: Rate limiting algorithm
        backend: Storage backend
        key_prefix: Prefix for rate limit keys
        redis_url: Redis connection URL (if using Redis backend)
    """

    rate: int = Field(default=100, ge=1, description="Requests per window")
    window: int = Field(default=60, ge=1, description="Window in seconds")
    burst: int = Field(default=0, ge=0, description="Burst capacity")
    algorithm: RateLimitAlgorithm = Field(
        default=RateLimitAlgorithm.TOKEN_BUCKET,
        description="Rate limiting algorithm",
    )
    backend: RateLimitBackend = Field(
        default=RateLimitBackend.MEMORY,
        description="Storage backend",
    )
    key_prefix: str = Field(
        default="ratelimit",
        description="Key prefix for rate limits",
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for distributed backend",
    )

    @field_validator("burst")
    @classmethod
    def validate_burst(cls, v: int, info: Any) -> int:
        """Validate burst is at least rate if not specified."""
        if v == 0:
            # Default burst to rate
            rate = info.data.get("rate", 100)
            return rate
        return v


@dataclass
class RateLimitResult:
    """Result of a rate limit check.

    Attributes:
        allowed: Whether the request is allowed
        limit: Maximum requests allowed
        remaining: Remaining requests in window
        reset_time: Unix timestamp when limit resets
        retry_after: Seconds to wait before retry (if not allowed)
    """

    allowed: bool
    limit: int
    remaining: int
    reset_time: float
    retry_after: float = 0.0

    def to_headers(self) -> Dict[str, str]:
        """Convert to HTTP response headers.

        Returns:
            Dictionary of rate limit headers
        """
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_time)),
        }
        if not self.allowed:
            headers["Retry-After"] = str(int(self.retry_after) + 1)
        return headers


class RateLimitError(RAGException):
    """Exception raised when rate limit is exceeded.

    Attributes:
        key: Rate limit key that was exceeded
        limit: Maximum requests allowed
        retry_after: Seconds to wait before retry
    """

    def __init__(
        self,
        message: str,
        key: str,
        limit: int,
        retry_after: float,
        headers: Optional[Dict[str, str]] = None,
    ) -> None:
        """Initialize rate limit error.

        Args:
            message: Error message
            key: Rate limit key
            limit: Maximum requests allowed
            retry_after: Seconds to wait
            headers: Rate limit headers
        """
        super().__init__(
            message=message,
            details={
                "key": key,
                "limit": limit,
                "retry_after": retry_after,
            },
            error_code="RATE_LIMIT_EXCEEDED",
        )
        self.key = key
        self.limit = limit
        self.retry_after = retry_after
        self.headers = headers or {}


class RateLimitStorage(ABC):
    """Abstract base class for rate limit storage backends."""

    @abstractmethod
    async def check_and_increment(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit and increment counter.

        Args:
            key: Rate limit key
            config: Rate limit configuration

        Returns:
            Rate limit result
        """
        pass

    @abstractmethod
    async def get_current_count(self, key: str, window: int) -> int:
        """Get current request count for key.

        Args:
            key: Rate limit key
            window: Time window in seconds

        Returns:
            Current request count
        """
        pass

    @abstractmethod
    async def reset(self, key: str) -> None:
        """Reset rate limit for key.

        Args:
            key: Rate limit key
        """
        pass


class MemoryRateLimitStorage(RateLimitStorage):
    """In-memory rate limit storage using token bucket algorithm.

    This implementation uses a token bucket approach for smooth rate limiting
    with proper concurrency handling via asyncio locks.
    """

    def __init__(self) -> None:
        """Initialize memory storage."""
        # Token bucket storage: key -> (tokens, last_update)
        self._buckets: Dict[str, Tuple[float, float]] = {}
        # Sliding window storage: key -> list of timestamps
        self._windows: Dict[str, list] = {}
        self._lock = asyncio.Lock()

    async def check_and_increment(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm.

        Args:
            key: Rate limit key
            config: Rate limit configuration

        Returns:
            Rate limit result
        """
        async with self._lock:
            now = time.time()
            bucket_key = f"{config.key_prefix}:{key}"

            if config.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                return self._check_token_bucket(bucket_key, config, now)
            else:
                return await self._check_sliding_window(bucket_key, config, now)

    def _check_token_bucket(
        self,
        key: str,
        config: RateLimitConfig,
        now: float,
    ) -> RateLimitResult:
        """Check rate limit using token bucket.

        Args:
            key: Storage key
            config: Configuration
            now: Current timestamp

        Returns:
            Rate limit result
        """
        burst = config.burst if config.burst > 0 else config.rate
        rate_per_second = config.rate / config.window

        # Get or create bucket
        if key in self._buckets:
            tokens, last_update = self._buckets[key]
            # Add tokens based on time elapsed
            elapsed = now - last_update
            tokens = min(burst, tokens + elapsed * rate_per_second)
        else:
            tokens = burst

        # Check if request can be allowed
        if tokens >= 1:
            tokens -= 1
            self._buckets[key] = (tokens, now)
            remaining = int(tokens)
            reset_time = now + (1 - tokens) / rate_per_second if rate_per_second > 0 else now + config.window

            return RateLimitResult(
                allowed=True,
                limit=burst,
                remaining=remaining,
                reset_time=reset_time,
            )
        else:
            # Request denied
            self._buckets[key] = (tokens, now)
            retry_after = (1 - tokens) / rate_per_second if rate_per_second > 0 else config.window

            return RateLimitResult(
                allowed=False,
                limit=burst,
                remaining=0,
                reset_time=now + retry_after,
                retry_after=retry_after,
            )

    async def _check_sliding_window(
        self,
        key: str,
        config: RateLimitConfig,
        now: float,
    ) -> RateLimitResult:
        """Check rate limit using sliding window.

        Args:
            key: Storage key
            config: Configuration
            now: Current timestamp

        Returns:
            Rate limit result
        """
        window_start = now - config.window

        # Get or create window
        if key not in self._windows:
            self._windows[key] = []

        # Remove old entries
        self._windows[key] = [ts for ts in self._windows[key] if ts > window_start]

        current_count = len(self._windows[key])

        if current_count < config.rate:
            # Allow request
            self._windows[key].append(now)
            remaining = config.rate - current_count - 1

            # Calculate reset time (oldest entry in window + window size)
            if self._windows[key]:
                reset_time = self._windows[key][0] + config.window
            else:
                reset_time = now + config.window

            return RateLimitResult(
                allowed=True,
                limit=config.rate,
                remaining=remaining,
                reset_time=reset_time,
            )
        else:
            # Deny request
            reset_time = self._windows[key][0] + config.window if self._windows[key] else now + config.window
            retry_after = reset_time - now

            return RateLimitResult(
                allowed=False,
                limit=config.rate,
                remaining=0,
                reset_time=reset_time,
                retry_after=max(0, retry_after),
            )

    async def get_current_count(self, key: str, window: int) -> int:
        """Get current request count.

        Args:
            key: Rate limit key
            window: Time window

        Returns:
            Current count
        """
        async with self._lock:
            now = time.time()
            window_start = now - window

            if key in self._windows:
                return len([ts for ts in self._windows[key] if ts > window_start])
            return 0

    async def reset(self, key: str) -> None:
        """Reset rate limit for key.

        Args:
            key: Rate limit key
        """
        async with self._lock:
            if key in self._buckets:
                del self._buckets[key]
            if key in self._windows:
                del self._windows[key]


class RedisRateLimitStorage(RateLimitStorage):
    """Redis-backed rate limit storage for distributed deployments.

    Uses Redis for distributed rate limiting across multiple instances.
    Implements sliding window algorithm with Redis sorted sets.
    """

    def __init__(self, redis_url: str) -> None:
        """Initialize Redis storage.

        Args:
            redis_url: Redis connection URL
        """
        self.redis_url = redis_url
        self._redis: Any = None
        self._lock = asyncio.Lock()

    async def _get_redis(self) -> Any:
        """Get or create Redis connection.

        Returns:
            Redis client
        """
        if self._redis is None:
            try:
                import redis.asyncio as aioredis

                self._redis = await aioredis.from_url(
                    self.redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
            except ImportError:
                logger.error("redis_not_installed")
                raise RuntimeError("Redis support requires 'redis' package")
        return self._redis

    async def check_and_increment(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> RateLimitResult:
        """Check rate limit using Redis sliding window.

        Args:
            key: Rate limit key
            config: Rate limit configuration

        Returns:
            Rate limit result
        """
        redis = await self._get_redis()
        now = time.time()
        window_start = now - config.window
        redis_key = f"{config.key_prefix}:{key}"

        try:
            # Use Redis pipeline for atomic operations
            pipe = redis.pipeline()

            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)

            # Count current entries
            pipe.zcard(redis_key)

            # Add current request
            pipe.zadd(redis_key, {str(now): now})

            # Set expiration
            pipe.expire(redis_key, config.window)

            # Execute pipeline
            results = await pipe.execute()
            current_count = results[1]  # zcard result

            if current_count < config.rate:
                # Request allowed
                remaining = config.rate - current_count - 1

                # Get oldest entry for reset time
                oldest = await redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + config.window
                else:
                    reset_time = now + config.window

                return RateLimitResult(
                    allowed=True,
                    limit=config.rate,
                    remaining=remaining,
                    reset_time=reset_time,
                )
            else:
                # Request denied - remove the entry we just added
                await redis.zrem(redis_key, str(now))

                oldest = await redis.zrange(redis_key, 0, 0, withscores=True)
                if oldest:
                    reset_time = oldest[0][1] + config.window
                    retry_after = reset_time - now
                else:
                    reset_time = now + config.window
                    retry_after = config.window

                return RateLimitResult(
                    allowed=False,
                    limit=config.rate,
                    remaining=0,
                    reset_time=reset_time,
                    retry_after=max(0, retry_after),
                )

        except Exception as e:
            logger.error("redis_rate_limit_error", error=str(e), key=key)
            # Fail open - allow request on Redis error
            return RateLimitResult(
                allowed=True,
                limit=config.rate,
                remaining=config.rate - 1,
                reset_time=now + config.window,
            )

    async def get_current_count(self, key: str, window: int) -> int:
        """Get current request count from Redis.

        Args:
            key: Rate limit key
            window: Time window

        Returns:
            Current count
        """
        redis = await self._get_redis()
        now = time.time()
        window_start = now - window

        try:
            await redis.zremrangebyscore(key, 0, window_start)
            return await redis.zcard(key)
        except Exception as e:
            logger.error("redis_get_count_error", error=str(e), key=key)
            return 0

    async def reset(self, key: str) -> None:
        """Reset rate limit in Redis.

        Args:
            key: Rate limit key
        """
        redis = await self._get_redis()
        try:
            await redis.delete(key)
        except Exception as e:
            logger.error("redis_reset_error", error=str(e), key=key)


class RateLimiter:
    """Rate limiter with configurable backend and algorithm.

    Provides rate limiting with support for multiple backends (memory, Redis)
    and algorithms (token bucket, sliding window).

    Attributes:
        config: Rate limit configuration
        storage: Storage backend instance

    Example:
        ```python
        # Basic usage
        limiter = RateLimiter(config=RateLimitConfig(rate=100, window=60))
        allowed, headers = await limiter.check_limit(key="user_123")

        # With decorator
        limiter = RateLimiter(config=RateLimitConfig(rate=100, window=60))

        @limiter.limit(key_func=lambda req: req.user_id)
        async def api_endpoint(request):
            return await process(request)

        # Context manager
        async with limiter.acquire(key="user_123") as result:
            if not result.allowed:
                raise HTTPException(status_code=429)
            return await process()
        ```
    """

    def __init__(
        self,
        config: Optional[RateLimitConfig] = None,
        storage: Optional[RateLimitStorage] = None,
        metrics: Optional[MetricsCollector] = None,
        settings: Optional[Settings] = None,
    ) -> None:
        """Initialize rate limiter.

        Args:
            config: Rate limit configuration
            storage: Custom storage backend
            metrics: Metrics collector
            settings: Application settings
        """
        self.config = config or RateLimitConfig()
        self._metrics = metrics or metrics_collector
        self._settings = settings or get_settings()

        # Initialize storage
        if storage:
            self._storage = storage
        elif self.config.backend == RateLimitBackend.REDIS and self.config.redis_url:
            self._storage = RedisRateLimitStorage(self.config.redis_url)
        else:
            self._storage = MemoryRateLimitStorage()

        logger.info(
            "rate_limiter_initialized",
            algorithm=self.config.algorithm.value,
            backend=self.config.backend.value,
            rate=self.config.rate,
            window=self.config.window,
        )

    async def check_limit(self, key: str) -> Tuple[bool, Dict[str, str]]:
        """Check if request is within rate limit.

        Args:
            key: Rate limit key (e.g., user ID, IP address)

        Returns:
            Tuple of (allowed, headers)
        """
        result = await self._storage.check_and_increment(key, self.config)

        # Record metrics
        if self._metrics:
            try:
                if not result.allowed:
                    self._metrics.increment_errors(
                        error_type="rate_limit",
                        component="rate_limiter",
                        operation="check_limit",
                    )
            except Exception:
                pass

        headers = result.to_headers()
        return result.allowed, headers

    async def is_allowed(self, key: str) -> bool:
        """Simple check if request is allowed.

        Args:
            key: Rate limit key

        Returns:
            True if request is allowed
        """
        allowed, _ = await self.check_limit(key)
        return allowed

    async def get_remaining(self, key: str) -> int:
        """Get remaining requests for key.

        Args:
            key: Rate limit key

        Returns:
            Remaining request count
        """
        result = await self._storage.check_and_increment(key, self.config)
        return result.remaining if result.allowed else 0

    async def reset(self, key: str) -> None:
        """Reset rate limit for key.

        Args:
            key: Rate limit key
        """
        await self._storage.reset(f"{self.config.key_prefix}:{key}")
        logger.info("rate_limit_reset", key=key)

    def limit(
        self,
        key_func: Optional[Callable[..., str]] = None,
        key: Optional[str] = None,
    ) -> Callable[[F], F]:
        """Decorator to rate limit a function.

        Args:
            key_func: Function to extract key from arguments
            key: Static key (used if key_func not provided)

        Returns:
            Decorator function

        Example:
            ```python
            limiter = RateLimiter(config=RateLimitConfig(rate=100, window=60))

            @limiter.limit(key_func=lambda req: req.user_id)
            async def api_endpoint(request):
                return await process(request)
            ```
        """

        def decorator(func: F) -> F:
            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                # Determine rate limit key
                if key_func:
                    try:
                        rate_key = key_func(*args, **kwargs)
                    except Exception as e:
                        logger.error("key_func_error", error=str(e))
                        rate_key = key or "default"
                else:
                    rate_key = key or "default"

                # Check rate limit
                allowed, headers = await self.check_limit(rate_key)

                if not allowed:
                    error = RateLimitError(
                        message=f"Rate limit exceeded for key: {rate_key}",
                        key=rate_key,
                        limit=self.config.rate,
                        retry_after=float(headers.get("Retry-After", self.config.window)),
                        headers=headers,
                    )
                    raise error

                # Call the function
                result = await func(*args, **kwargs)
                return result

            return cast(F, async_wrapper)

        return decorator

    async def acquire(self, key: str) -> RateLimitResult:
        """Acquire rate limit token.

        Args:
            key: Rate limit key

        Returns:
            Rate limit result
        """
        return await self._storage.check_and_increment(key, self.config)


def rate_limiter(
    limit: int = 100,
    window: int = 60,
    key: str = "default",
    key_func: Optional[Callable[..., str]] = None,
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.TOKEN_BUCKET,
    backend: RateLimitBackend = RateLimitBackend.MEMORY,
    redis_url: Optional[str] = None,
) -> Callable[[F], F]:
    """Decorator to add rate limiting to a function.

    Creates a rate limiter with the given configuration and applies it
    to the decorated function.

    Args:
        limit: Maximum requests per window
        window: Time window in seconds
        key: Static rate limit key
        key_func: Function to extract key from arguments
        algorithm: Rate limiting algorithm
        backend: Storage backend
        redis_url: Redis URL for distributed backend

    Returns:
        Decorator function

    Example:
        ```python
        @rate_limiter(limit=100, window=60, key="user_id")
        async def search_endpoint(request):
            return await perform_search(request.query)

        @rate_limiter(limit=10, window=60, key_func=lambda req: req.ip_address)
        async def public_api(request):
            return await process(request)
        ```
    """
    config = RateLimitConfig(
        rate=limit,
        window=window,
        algorithm=algorithm,
        backend=backend,
        redis_url=redis_url,
    )

    limiter = RateLimiter(config=config)
    return limiter.limit(key_func=key_func, key=key)


# Global rate limiter registry
_rate_limiters: Dict[str, RateLimiter] = {}


def get_rate_limiter(
    name: str,
    config: Optional[RateLimitConfig] = None,
) -> RateLimiter:
    """Get or create a rate limiter by name.

    Args:
        name: Rate limiter name
        config: Optional configuration (used if creating new)

    Returns:
        RateLimiter instance
    """
    if name not in _rate_limiters:
        if config is None:
            config = RateLimitConfig()
        _rate_limiters[name] = RateLimiter(config=config)
    return _rate_limiters[name]
