"""Production middleware infrastructure for Advanced RAG System.

This module provides essential middleware components for production deployments:
- Circuit breaker patterns for fault tolerance
- Rate limiting for API protection

These components help ensure system stability and prevent cascading failures
in production environments.

Example:
    ```python
    from src.middleware import circuit_breaker, rate_limiter
    from src.middleware.circuit_breaker import CircuitBreaker, CircuitState
    from src.middleware.rate_limiter import RateLimiter, RateLimitConfig

    # Circuit breaker decorator
    @circuit_breaker(name="openai_api", failure_threshold=5, timeout=60)
    async def call_openai(prompt: str):
        return await openai_client.generate(prompt)

    # Rate limiter decorator
    @rate_limiter(limit=100, window=60, key="user_id")
    async def search_endpoint(request):
        return await perform_search(request.query)

    # Direct circuit breaker usage
    breaker = CircuitBreaker(
        name="embedding_service",
        failure_threshold=5,
        reset_timeout=60.0,
    )

    async with breaker:
        result = await generate_embeddings(text)

    # Direct rate limiter usage
    limiter = RateLimiter(
        config=RateLimitConfig(rate=100, burst=150)
    )

    allowed, headers = await limiter.check_limit(key="user_123")
    if not allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    ```
"""

from src.middleware.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitBreakerError,
    CircuitState,
    circuit_breaker,
)
from src.middleware.rate_limiter import (
    RateLimitBackend,
    RateLimitConfig,
    RateLimiter,
    RateLimitError,
    rate_limiter,
)

__all__ = [
    # Circuit Breaker
    "CircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "CircuitBreakerError",
    "circuit_breaker",
    # Rate Limiter
    "RateLimiter",
    "RateLimitConfig",
    "RateLimitBackend",
    "RateLimitError",
    "rate_limiter",
]
