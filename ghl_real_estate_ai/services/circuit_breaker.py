"""
Enterprise Circuit Breaker Pattern Implementation
Provides fault tolerance for external service calls with intelligent recovery
"""

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""

    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, blocking requests
    HALF_OPEN = "half_open"  # Testing recovery


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker behavior"""

    failure_threshold: int = 5  # Failures to open circuit
    recovery_timeout: float = 60.0  # Seconds before trying half-open
    success_threshold: int = 3  # Successes to close from half-open
    timeout: float = 30.0  # Request timeout seconds
    expected_exception: type = Exception  # Exception type that triggers failure
    fallback: Optional[Callable] = None  # Fallback function


@dataclass
class CircuitBreakerStats:
    """Circuit breaker statistics"""

    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    timeout_requests: int = 0
    circuit_opens: int = 0
    fallback_calls: int = 0
    avg_response_time_ms: float = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None


class CircuitBreaker:
    """
    Circuit Breaker implementation for fault tolerance
    """

    def __init__(self, name: str, config: CircuitBreakerConfig):
        self.name = name
        self.config = config
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time: Optional[float] = None
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function through circuit breaker
        """
        async with self._lock:
            if await self._should_allow_request():
                return await self._execute_request(func, *args, **kwargs)
            else:
                return await self._handle_blocked_request(func, *args, **kwargs)

    async def _should_allow_request(self) -> bool:
        """Determine if request should be allowed based on circuit state"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.info(f"Circuit breaker {self.name} transitioning to HALF_OPEN")
                return True
            return False
        elif self.state == CircuitState.HALF_OPEN:
            return True

        return False

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt recovery"""
        if self.last_failure_time is None:
            return True

        return time.time() - self.last_failure_time >= self.config.recovery_timeout

    async def _execute_request(self, func: Callable, *args, **kwargs) -> Any:
        """Execute the actual request with timeout and error handling"""
        start_time = time.time()
        self.stats.total_requests += 1

        try:
            # Execute with timeout
            result = await asyncio.wait_for(self._run_function(func, *args, **kwargs), timeout=self.config.timeout)

            await self._handle_success(start_time)
            return result

        except asyncio.TimeoutError:
            await self._handle_timeout(start_time)
            raise
        except self.config.expected_exception as e:
            await self._handle_failure(start_time, e)
            raise
        except Exception as e:
            # Unexpected exceptions don't count as circuit breaker failures
            logger.warning(f"Unexpected exception in {self.name}: {e}")
            self._update_response_time(start_time)
            raise

    async def _run_function(self, func: Callable, *args, **kwargs) -> Any:
        """Run function handling both sync and async callables"""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, func, *args, **kwargs)

    async def _handle_success(self, start_time: float):
        """Handle successful request"""
        self.stats.successful_requests += 1
        self.stats.last_success_time = datetime.now()
        self._update_response_time(start_time)

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.config.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"Circuit breaker {self.name} closed after successful recovery")

        # Reset failure count on success in CLOSED state
        if self.state == CircuitState.CLOSED:
            self.failure_count = 0

    async def _handle_failure(self, start_time: float, exception: Exception):
        """Handle failed request"""
        self.stats.failed_requests += 1
        self.stats.last_failure_time = datetime.now()
        self._update_response_time(start_time)

        self.failure_count += 1
        self.last_failure_time = time.time()

        if self.state == CircuitState.CLOSED:
            if self.failure_count >= self.config.failure_threshold:
                self.state = CircuitState.OPEN
                self.stats.circuit_opens += 1
                logger.warning(
                    f"Circuit breaker {self.name} opened after {self.failure_count} failures. Last error: {exception}"
                )
        elif self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.warning(f"Circuit breaker {self.name} reopened during recovery attempt")

    async def _handle_timeout(self, start_time: float):
        """Handle request timeout"""
        self.stats.timeout_requests += 1
        self._update_response_time(start_time)
        await self._handle_failure(start_time, TimeoutError("Request timeout"))

    async def _handle_blocked_request(self, func: Callable, *args, **kwargs) -> Any:
        """Handle request blocked by open circuit"""
        if self.config.fallback:
            logger.info(f"Circuit breaker {self.name} is OPEN, using fallback")
            self.stats.fallback_calls += 1

            if asyncio.iscoroutinefunction(self.config.fallback):
                return await self.config.fallback(*args, **kwargs)
            else:
                return self.config.fallback(*args, **kwargs)
        else:
            raise CircuitBreakerError(f"Circuit breaker {self.name} is OPEN and no fallback available")

    def _update_response_time(self, start_time: float):
        """Update average response time statistics"""
        response_time_ms = (time.time() - start_time) * 1000
        total_requests = self.stats.total_requests
        current_avg = self.stats.avg_response_time_ms

        self.stats.avg_response_time_ms = (current_avg * (total_requests - 1) + response_time_ms) / total_requests

    def get_state(self) -> CircuitState:
        """Get current circuit breaker state"""
        return self.state

    def get_stats(self) -> Dict[str, Any]:
        """Get circuit breaker statistics"""
        success_rate = self.stats.successful_requests / max(self.stats.total_requests, 1)

        return {
            "name": self.name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "success_count": self.success_count,
            "success_rate": success_rate,
            "stats": {
                "total_requests": self.stats.total_requests,
                "successful_requests": self.stats.successful_requests,
                "failed_requests": self.stats.failed_requests,
                "timeout_requests": self.stats.timeout_requests,
                "circuit_opens": self.stats.circuit_opens,
                "fallback_calls": self.stats.fallback_calls,
                "avg_response_time_ms": self.stats.avg_response_time_ms,
                "last_failure_time": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
                "last_success_time": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None,
            },
        }

    def reset(self):
        """Reset circuit breaker to closed state"""
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        logger.info(f"Circuit breaker {self.name} manually reset")


class CircuitBreakerError(Exception):
    """Exception raised when circuit breaker is open"""

    pass


class CircuitBreakerManager:
    """
    Manages multiple circuit breakers for different services
    """

    def __init__(self):
        self.breakers: Dict[str, CircuitBreaker] = {}

    def create_breaker(self, name: str, config: CircuitBreakerConfig) -> CircuitBreaker:
        """Create a new circuit breaker"""
        breaker = CircuitBreaker(name, config)
        self.breakers[name] = breaker
        logger.info(f"Created circuit breaker: {name}")
        return breaker

    def get_breaker(self, name: str) -> Optional[CircuitBreaker]:
        """Get existing circuit breaker by name"""
        return self.breakers.get(name)

    def get_all_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all circuit breakers"""
        return {name: breaker.get_stats() for name, breaker in self.breakers.items()}

    def reset_all(self):
        """Reset all circuit breakers"""
        for breaker in self.breakers.values():
            breaker.reset()
        logger.info("All circuit breakers reset")


# Global circuit breaker manager
_circuit_manager = CircuitBreakerManager()


def circuit_breaker(
    name: str,
    failure_threshold: int = 5,
    recovery_timeout: float = 60.0,
    success_threshold: int = 3,
    timeout: float = 30.0,
    expected_exception: type = Exception,
    fallback: Optional[Callable] = None,
):
    """
    Decorator to apply circuit breaker pattern to functions
    """
    config = CircuitBreakerConfig(
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        success_threshold=success_threshold,
        timeout=timeout,
        expected_exception=expected_exception,
        fallback=fallback,
    )

    breaker = _circuit_manager.create_breaker(name, config)

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)

        return wrapper

    return decorator


def get_circuit_manager() -> CircuitBreakerManager:
    """Get global circuit breaker manager"""
    return _circuit_manager


# Predefined fallback functions
async def claude_fallback(*args, **kwargs) -> str:
    """Fallback for Claude API calls"""
    return "Service temporarily unavailable. Please try again later."


async def ghl_fallback(*args, **kwargs) -> Dict[str, Any]:
    """Fallback for GHL API calls"""
    return {"error": "GHL service unavailable", "retry_after": 60}


async def redis_fallback(*args, **kwargs) -> None:
    """Fallback for Redis calls (returns None, disables caching)"""
    logger.warning("Redis unavailable, operating without cache")
    return None
