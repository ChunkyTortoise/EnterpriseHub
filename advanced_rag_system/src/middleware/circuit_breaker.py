"""Circuit breaker pattern implementation for Advanced RAG System.

Provides fault tolerance through circuit breaker patterns that prevent
cascading failures when external services (OpenAI API, vector stores, etc.)
become unavailable or degraded.

The circuit breaker has three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Circuit is tripped, requests fail fast
- HALF_OPEN: Testing if service has recovered

Features:
- Configurable failure thresholds and reset timeouts
- Exponential backoff for retries
- Async context manager support
- Health check integration
- Metrics integration for monitoring
- Per-operation circuit breakers with decorator support

Example:
    ```python
    # Using decorator
    @circuit_breaker(name="openai_api", failure_threshold=5, timeout=60)
    async def call_openai(prompt: str):
        return await openai_client.generate(prompt)

    # Using context manager
    breaker = CircuitBreaker(
        name="embedding_service",
        failure_threshold=5,
        reset_timeout=60.0,
    )
    
    async with breaker:
        result = await generate_embeddings(text)

    # Direct usage
    breaker = CircuitBreaker(name="vector_store")
    
    @breaker.protect
    async def query_vector_store(query: str):
        return await vector_store.search(query)
    ```
"""

from __future__ import annotations

import asyncio
import functools
import time
from enum import Enum
from typing import Any, Callable, Dict, Optional, TypeVar, cast

from pydantic import BaseModel, Field

from src.core.exceptions import RAGException
from src.monitoring.health import HealthChecker, HealthResult, HealthStatus, health_checker
from src.monitoring.metrics import MetricsCollector, metrics_collector
from src.utils.logging import get_logger

logger = get_logger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class CircuitState(str, Enum):
    """Circuit breaker states.

    Attributes:
        CLOSED: Normal operation - requests pass through
        OPEN: Circuit tripped - requests fail fast
        HALF_OPEN: Testing recovery - limited requests allowed
    """

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerConfig(BaseModel):
    """Configuration for circuit breaker.

    Attributes:
        name: Unique identifier for this circuit breaker
        failure_threshold: Number of failures before opening circuit
        success_threshold: Number of successes in half-open to close circuit
        reset_timeout: Seconds before attempting recovery (half-open)
        half_open_max_calls: Max calls allowed in half-open state
        exponential_base: Base for exponential backoff
        max_retry_delay: Maximum retry delay in seconds
    """

    name: str = Field(default="default", description="Circuit breaker name")
    failure_threshold: int = Field(
        default=5, ge=1, description="Failures before opening circuit"
    )
    success_threshold: int = Field(
        default=3, ge=1, description="Successes to close from half-open"
    )
    reset_timeout: float = Field(
        default=60.0, ge=1.0, description="Seconds before recovery attempt"
    )
    half_open_max_calls: int = Field(
        default=3, ge=1, description="Max calls in half-open state"
    )
    exponential_base: float = Field(
        default=2.0, ge=1.0, description="Exponential backoff base"
    )
    max_retry_delay: float = Field(
        default=60.0, ge=1.0, description="Maximum retry delay"
    )


class CircuitBreakerError(RAGException):
    """Exception raised when circuit breaker is open.

    Attributes:
        circuit_name: Name of the circuit that is open
        state: Current circuit state
        last_failure: Last exception that caused the circuit to open
    """

    def __init__(
        self,
        message: str,
        circuit_name: str,
        state: CircuitState,
        last_failure: Optional[Exception] = None,
    ) -> None:
        """Initialize circuit breaker error.

        Args:
            message: Error message
            circuit_name: Name of the circuit
            state: Current circuit state
            last_failure: Last failure that caused open state
        """
        super().__init__(
            message=message,
            details={
                "circuit_name": circuit_name,
                "state": state.value,
                "last_failure": str(last_failure) if last_failure else None,
            },
            error_code="CIRCUIT_BREAKER_OPEN",
        )
        self.circuit_name = circuit_name
        self.state = state
        self.last_failure = last_failure


class CircuitBreaker:
    """Circuit breaker implementation for fault tolerance.

    Implements the circuit breaker pattern to prevent cascading failures
    when external services become unavailable. Tracks failures and
    automatically transitions between states based on configured thresholds.

    Attributes:
        config: Circuit breaker configuration
        state: Current circuit state
        failure_count: Current consecutive failure count
        success_count: Current consecutive success count (in half-open)
        last_failure_time: Timestamp of last failure
        last_exception: Last exception that caused failure
        half_open_calls: Number of calls in half-open state

    Example:
        ```python
        breaker = CircuitBreaker(
            config=CircuitBreakerConfig(
                name="openai_api",
                failure_threshold=5,
                reset_timeout=60.0,
            )
        )

        # Context manager
        async with breaker:
            result = await openai_client.generate(prompt)

        # Decorator
        @breaker.protect
        async def generate_embedding(text: str):
            return await embedding_client.embed(text)
        ```
    """

    def __init__(
        self,
        config: Optional[CircuitBreakerConfig] = None,
        name: Optional[str] = None,
        failure_threshold: Optional[int] = None,
        reset_timeout: Optional[float] = None,
        metrics: Optional[MetricsCollector] = None,
        health_checker_ref: Optional[HealthChecker] = None,
    ) -> None:
        """Initialize circuit breaker.

        Args:
            config: Full configuration object (takes precedence)
            name: Circuit breaker name (if config not provided)
            failure_threshold: Failures before opening (if config not provided)
            reset_timeout: Seconds before recovery (if config not provided)
            metrics: Metrics collector for monitoring
            health_checker_ref: Health checker for integration
        """
        if config:
            self.config = config
        else:
            self.config = CircuitBreakerConfig(
                name=name or "default",
                failure_threshold=failure_threshold or 5,
                reset_timeout=reset_timeout or 60.0,
            )

        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[float] = None
        self._last_exception: Optional[Exception] = None
        self._half_open_calls = 0
        self._lock = asyncio.Lock()
        self._metrics = metrics or metrics_collector
        self._health_checker = health_checker_ref

        # Register with health checker if provided
        if self._health_checker:
            self._health_checker.register(
                f"circuit_breaker_{self.config.name}",
                self.health_check,
            )

        logger.info(
            "circuit_breaker_initialized",
            name=self.config.name,
            failure_threshold=self.config.failure_threshold,
            reset_timeout=self.config.reset_timeout,
        )

    @property
    def state(self) -> CircuitState:
        """Get current circuit state.

        Returns:
            Current circuit state
        """
        return self._state

    @property
    def failure_count(self) -> int:
        """Get current failure count.

        Returns:
            Number of consecutive failures
        """
        return self._failure_count

    @property
    def is_open(self) -> bool:
        """Check if circuit is open.

        Returns:
            True if circuit is open
        """
        return self._state == CircuitState.OPEN

    @property
    def is_closed(self) -> bool:
        """Check if circuit is closed.

        Returns:
            True if circuit is closed
        """
        return self._state == CircuitState.CLOSED

    @property
    def is_half_open(self) -> bool:
        """Check if circuit is half-open.

        Returns return:
            True if circuit is half-open
        """
        return self._state == CircuitState.HALF_OPEN

    async def health_check(self) -> HealthResult:
        """Perform health check for this circuit breaker.

        Returns:
            Health result based on circuit state
        """
        if self._state == CircuitState.OPEN:
            return HealthResult.unhealthy(
                message=f"Circuit breaker {self.config.name} is OPEN",
                details={
                    "circuit_name": self.config.name,
                    "state": self._state.value,
                    "failure_count": self._failure_count,
                    "last_failure": self._last_failure_time,
                },
            )
        elif self._state == CircuitState.HALF_OPEN:
            return HealthResult.degraded(
                message=f"Circuit breaker {self.config.name} is HALF_OPEN (recovering)",
                details={
                    "circuit_name": self.config.name,
                    "state": self._state.value,
                    "success_count": self._success_count,
                },
            )
        else:
            return HealthResult.healthy(
                message=f"Circuit breaker {self.config.name} is CLOSED",
                details={
                    "circuit_name": self.config.name,
                    "state": self._state.value,
                    "failure_count": self._failure_count,
                },
            )

    async def _can_execute(self) -> bool:
        """Check if execution is allowed based on current state.

        Returns:
            True if execution should proceed
        """
        async with self._lock:
            if self._state == CircuitState.CLOSED:
                return True

            if self._state == CircuitState.OPEN:
                # Check if reset timeout has elapsed
                if self._last_failure_time is not None:
                    elapsed = time.time() - self._last_failure_time
                    if elapsed >= self.config.reset_timeout:
                        logger.info(
                            "circuit_breaker_half_open",
                            name=self.config.name,
                            elapsed=elapsed,
                        )
                        self._state = CircuitState.HALF_OPEN
                        self._half_open_calls = 0
                        self._success_count = 0
                        self._record_state_transition(CircuitState.HALF_OPEN)
                        return True
                return False

            if self._state == CircuitState.HALF_OPEN:
                # Allow limited calls in half-open state
                if self._half_open_calls < self.config.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False

            return False

    async def _on_success(self) -> None:
        """Handle successful execution."""
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.config.success_threshold:
                    logger.info(
                        "circuit_breaker_closed",
                        name=self.config.name,
                        success_count=self._success_count,
                    )
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._half_open_calls = 0
                    self._last_exception = None
                    self._record_state_transition(CircuitState.CLOSED)
            else:
                # Reset failure count on success in closed state
                if self._failure_count > 0:
                    self._failure_count = 0

            self._record_success()

    async def _on_failure(self, exception: Exception) -> None:
        """Handle failed execution.

        Args:
            exception: The exception that occurred
        """
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            self._last_exception = exception

            if self._state == CircuitState.HALF_OPEN:
                # Failure in half-open immediately opens circuit
                logger.warning(
                    "circuit_breaker_open_from_half_open",
                    name=self.config.name,
                    exception=str(exception),
                )
                self._state = CircuitState.OPEN
                self._record_state_transition(CircuitState.OPEN)
            elif self._state == CircuitState.CLOSED:
                if self._failure_count >= self.config.failure_threshold:
                    logger.warning(
                        "circuit_breaker_open",
                        name=self.config.name,
                        failure_count=self._failure_count,
                        exception=str(exception),
                    )
                    self._state = CircuitState.OPEN
                    self._record_state_transition(CircuitState.OPEN)

            self._record_failure()

    def _record_success(self) -> None:
        """Record success metric."""
        if self._metrics:
            try:
                # Use increment_requests as a proxy for circuit breaker metrics
                # In a real implementation, you'd have dedicated circuit breaker metrics
                pass
            except Exception:
                pass

    def _record_failure(self) -> None:
        """Record failure metric."""
        if self._metrics:
            try:
                self._metrics.increment_errors(
                    error_type="circuit_breaker",
                    component=self.config.name,
                    operation="protected_call",
                )
            except Exception:
                pass

    def _record_state_transition(self, new_state: CircuitState) -> None:
        """Record state transition metric.

        Args:
            new_state: The new circuit state
        """
        logger.info(
            "circuit_breaker_state_transition",
            name=self.config.name,
            from_state=self._state.value,
            to_state=new_state.value,
        )

    async def __aenter__(self) -> CircuitBreaker:
        """Async context manager entry.

        Returns:
            Self if execution is allowed

        Raises:
            CircuitBreakerError: If circuit is open
        """
        if not await self._can_execute():
            raise CircuitBreakerError(
                message=f"Circuit breaker '{self.config.name}' is OPEN",
                circuit_name=self.config.name,
                state=self._state,
                last_failure=self._last_exception,
            )
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Async context manager exit.

        Args:
            exc_type: Exception type if one occurred
            exc_val: Exception value if one occurred
            exc_tb: Exception traceback if one occurred
        """
        if exc_val is not None:
            await self._on_failure(exc_val)
        else:
            await self._on_success()

    def protect(self, func: F) -> F:
        """Decorator to protect a function with this circuit breaker.

        Args:
            func: Function to protect

        Returns:
            Wrapped function with circuit breaker protection
        """

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            async with self:
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            if not asyncio.iscoroutinefunction(func):
                # Synchronous function
                if not self._can_execute_sync():
                    raise CircuitBreakerError(
                        message=f"Circuit breaker '{self.config.name}' is OPEN",
                        circuit_name=self.config.name,
                        state=self._state,
                        last_failure=self._last_exception,
                    )
                try:
                    result = func(*args, **kwargs)
                    self._on_success_sync()
                    return result
                except Exception as e:
                    self._on_failure_sync(e)
                    raise
            else:
                # Should not reach here for async functions
                raise RuntimeError("Use async_wrapper for async functions")

        if asyncio.iscoroutinefunction(func):
            return cast(F, async_wrapper)
        else:
            return cast(F, sync_wrapper)

    def _can_execute_sync(self) -> bool:
        """Synchronous version of _can_execute for sync functions.

        Returns:
            True if execution should proceed
        """
        if self._state == CircuitState.CLOSED:
            return True

        if self._state == CircuitState.OPEN:
            if self._last_failure_time is not None:
                elapsed = time.time() - self._last_failure_time
                if elapsed >= self.config.reset_timeout:
                    # Note: This is a simplified version - in production,
                    # you'd want proper locking for thread safety
                    self._state = CircuitState.HALF_OPEN
                    self._half_open_calls = 0
                    self._success_count = 0
                    return True
            return False

        if self._state == CircuitState.HALF_OPEN:
            if self._half_open_calls < self.config.half_open_max_calls:
                self._half_open_calls += 1
                return True
            return False

        return False

    def _on_success_sync(self) -> None:
        """Synchronous version of _on_success."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            if self._success_count >= self.config.success_threshold:
                self._state = CircuitState.CLOSED
                self._failure_count = 0
                self._half_open_calls = 0
                self._last_exception = None
        else:
            if self._failure_count > 0:
                self._failure_count = 0

    def _on_failure_sync(self, exception: Exception) -> None:
        """Synchronous version of _on_failure.

        Args:
            exception: The exception that occurred
        """
        self._failure_count += 1
        self._last_failure_time = time.time()
        self._last_exception = exception

        if self._state == CircuitState.HALF_OPEN:
            self._state = CircuitState.OPEN
        elif self._state == CircuitState.CLOSED:
            if self._failure_count >= self.config.failure_threshold:
                self._state = CircuitState.OPEN

    def get_retry_delay(self, attempt: int) -> float:
        """Calculate exponential backoff delay for retries.

        Args:
            attempt: Retry attempt number (0-indexed)

        Returns:
            Delay in seconds before next retry
        """
        delay = min(
            self.config.exponential_base ** attempt,
            self.config.max_retry_delay,
        )
        return delay

    def to_dict(self) -> Dict[str, Any]:
        """Convert circuit breaker state to dictionary.

        Returns:
            Dictionary representation of current state
        """
        return {
            "name": self.config.name,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "half_open_calls": self._half_open_calls,
            "config": self.config.model_dump(),
        }


# Global circuit breaker registry
_circuit_breakers: Dict[str, CircuitBreaker] = {}


def get_circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None,
    **kwargs: Any,
) -> CircuitBreaker:
    """Get or create a circuit breaker by name.

    Args:
        name: Circuit breaker name
        config: Optional configuration (used if creating new)
        **kwargs: Additional arguments for CircuitBreaker constructor

    Returns:
        CircuitBreaker instance
    """
    if name not in _circuit_breakers:
        if config is None:
            config = CircuitBreakerConfig(name=name, **kwargs)
        _circuit_breakers[name] = CircuitBreaker(config=config)
    return _circuit_breakers[name]


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    success_threshold: int = 3,
    timeout: float = 60.0,
    half_open_max_calls: int = 3,
) -> Callable[[F], F]:
    """Decorator to add circuit breaker protection to a function.

    Creates or reuses a circuit breaker with the given name and configuration.

    Args:
        name: Circuit breaker name (shared across decorated functions)
        failure_threshold: Failures before opening circuit
        success_threshold: Successes to close from half-open
        timeout: Seconds before attempting recovery
        half_open_max_calls: Max calls in half-open state

    Returns:
        Decorator function

    Example:
        ```python
        @circuit_breaker(name="openai_api", failure_threshold=5, timeout=60)
        async def call_openai(prompt: str):
            return await openai_client.generate(prompt)
        ```
    """
    config = CircuitBreakerConfig(
        name=name,
        failure_threshold=failure_threshold,
        success_threshold=success_threshold,
        reset_timeout=timeout,
        half_open_max_calls=half_open_max_calls,
    )

    def decorator(func: F) -> F:
        breaker = get_circuit_breaker(name, config)
        return breaker.protect(func)

    return decorator
