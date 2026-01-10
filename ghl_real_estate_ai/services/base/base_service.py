"""
Base service class providing common functionality for all GHL Real Estate AI services.

This class implements common patterns like error handling, logging, metrics,
health checking, and configuration management to reduce code duplication
across the 178+ service files.
"""

import asyncio
import logging
import time
import uuid
from abc import ABC, abstractmethod
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from .exceptions import (
    GHLRealEstateError,
    ConfigurationError,
    PerformanceError,
    TimeoutError,
    ValidationError,
    wrap_exception,
    is_recoverable_error,
    get_fallback_strategy,
)
from .protocols import HealthCheck, ConfigManager, CacheManager


T = TypeVar('T')


@dataclass
class ServiceMetrics:
    """Metrics tracking for service operations."""
    service_name: str
    operation_counts: Dict[str, int] = field(default_factory=dict)
    operation_times: Dict[str, List[float]] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    last_reset: datetime = field(default_factory=datetime.now)

    def record_operation(self, operation: str, duration: float) -> None:
        """Record successful operation."""
        self.operation_counts[operation] = self.operation_counts.get(operation, 0) + 1
        if operation not in self.operation_times:
            self.operation_times[operation] = []
        self.operation_times[operation].append(duration)

    def record_error(self, operation: str, error_type: str) -> None:
        """Record operation error."""
        error_key = f"{operation}.{error_type}"
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        stats = {
            "service_name": self.service_name,
            "total_operations": sum(self.operation_counts.values()),
            "total_errors": sum(self.error_counts.values()),
            "operations": {},
            "errors": dict(self.error_counts),
            "last_reset": self.last_reset.isoformat(),
        }

        for operation, times in self.operation_times.items():
            if times:
                stats["operations"][operation] = {
                    "count": self.operation_counts.get(operation, 0),
                    "avg_time": sum(times) / len(times),
                    "min_time": min(times),
                    "max_time": max(times),
                    "p95_time": sorted(times)[int(len(times) * 0.95)] if len(times) > 0 else 0,
                }

        return stats


class BaseService(ABC):
    """
    Abstract base class for all GHL Real Estate AI services.

    Provides common functionality including:
    - Structured logging
    - Error handling with domain-specific exceptions
    - Performance monitoring and metrics
    - Health checking
    - Configuration management
    - Circuit breaker pattern for external dependencies
    - Graceful degradation strategies
    """

    def __init__(
        self,
        service_name: Optional[str] = None,
        config_manager: Optional[ConfigManager] = None,
        cache_manager: Optional[CacheManager] = None,
        logger: Optional[logging.Logger] = None,
        enable_metrics: bool = True,
    ):
        """
        Initialize the base service.

        Args:
            service_name: Name of the service (defaults to class name)
            config_manager: Configuration manager instance
            cache_manager: Cache manager instance
            logger: Logger instance
            enable_metrics: Whether to enable metrics tracking
        """
        self.service_name = service_name or self.__class__.__name__
        self.service_id = str(uuid.uuid4())

        # Set up logging
        self.logger = logger or logging.getLogger(f"ghl_real_estate_ai.{self.service_name}")

        # Dependencies
        self.config_manager = config_manager
        self.cache_manager = cache_manager

        # Metrics and monitoring
        self.enable_metrics = enable_metrics
        if enable_metrics:
            self.metrics = ServiceMetrics(service_name=self.service_name)
        else:
            self.metrics = None

        # Circuit breaker state
        self._circuit_breaker_state: Dict[str, Dict[str, Any]] = {}

        # Initialization tracking
        self._initialized = False
        self._initialization_error: Optional[Exception] = None

        self.logger.info(f"Initializing {self.service_name} service (ID: {self.service_id})")

    async def initialize(self) -> None:
        """
        Initialize the service. Called before first use.

        Override this method in subclasses to implement service-specific initialization.
        """
        try:
            await self._initialize_implementation()
            self._initialized = True
            self.logger.info(f"{self.service_name} service initialized successfully")
        except Exception as e:
            self._initialization_error = e
            self.logger.error(f"Failed to initialize {self.service_name}: {e}")
            raise wrap_exception(e, f"{self.service_name} initialization", {"service_id": self.service_id})

    @abstractmethod
    async def _initialize_implementation(self) -> None:
        """
        Service-specific initialization logic.

        Override this method in subclasses.
        """
        pass

    def _ensure_initialized(self) -> None:
        """Ensure service is initialized before use."""
        if self._initialization_error:
            raise self._initialization_error
        if not self._initialized:
            raise ConfigurationError(f"{self.service_name} not initialized. Call initialize() first.")

    async def execute_with_monitoring(
        self,
        operation_name: str,
        operation_func: Callable[[], T],
        timeout_seconds: Optional[float] = None,
        retry_count: int = 0,
        fallback_func: Optional[Callable[[], T]] = None,
    ) -> T:
        """
        Execute an operation with comprehensive monitoring and error handling.

        Args:
            operation_name: Name of the operation for logging/metrics
            operation_func: Function to execute
            timeout_seconds: Operation timeout
            retry_count: Number of retries for recoverable errors
            fallback_func: Fallback function if operation fails

        Returns:
            Operation result

        Raises:
            GHLRealEstateError: When operation fails and no fallback available
        """
        self._ensure_initialized()

        start_time = time.time()
        operation_id = str(uuid.uuid4())

        self.logger.debug(f"Starting {operation_name} (ID: {operation_id})")

        # Check circuit breaker
        if self._is_circuit_open(operation_name):
            if fallback_func:
                self.logger.warning(f"Circuit breaker open for {operation_name}, using fallback")
                return await self._execute_fallback(operation_name, fallback_func, start_time)
            else:
                raise PerformanceError(f"Circuit breaker open for {operation_name} and no fallback available")

        exception = None
        for attempt in range(retry_count + 1):
            try:
                # Execute with timeout if specified
                if timeout_seconds:
                    result = await asyncio.wait_for(
                        self._run_async_operation(operation_func),
                        timeout=timeout_seconds
                    )
                else:
                    result = await self._run_async_operation(operation_func)

                # Record success metrics
                duration = time.time() - start_time
                if self.metrics:
                    self.metrics.record_operation(operation_name, duration)

                self.logger.debug(f"Completed {operation_name} (ID: {operation_id}) in {duration:.3f}s")

                # Reset circuit breaker on success
                self._record_circuit_success(operation_name)

                return result

            except asyncio.TimeoutError as e:
                exception = TimeoutError(f"{operation_name} timed out after {timeout_seconds}s")
                break  # Don't retry timeout errors

            except Exception as e:
                exception = wrap_exception(e, operation_name, {"attempt": attempt + 1, "service_id": self.service_id})

                # Record error metrics
                if self.metrics:
                    self.metrics.record_error(operation_name, type(e).__name__)

                # Check if error is recoverable and we have retries left
                if attempt < retry_count and is_recoverable_error(exception):
                    wait_time = 2 ** attempt  # Exponential backoff
                    self.logger.warning(
                        f"{operation_name} failed (attempt {attempt + 1}/{retry_count + 1}): {e}. "
                        f"Retrying in {wait_time}s"
                    )
                    await asyncio.sleep(wait_time)
                    continue
                else:
                    # Record circuit breaker failure
                    self._record_circuit_failure(operation_name)
                    break

        # If we get here, all retries failed
        duration = time.time() - start_time
        self.logger.error(f"Failed {operation_name} (ID: {operation_id}) after {duration:.3f}s: {exception}")

        # Try fallback if available
        if fallback_func:
            self.logger.info(f"Attempting fallback for {operation_name}")
            try:
                return await self._execute_fallback(operation_name, fallback_func, start_time)
            except Exception as fallback_error:
                self.logger.error(f"Fallback also failed for {operation_name}: {fallback_error}")

        raise exception

    async def _run_async_operation(self, operation_func: Callable[[], T]) -> T:
        """Run operation function, handling both sync and async functions."""
        if asyncio.iscoroutinefunction(operation_func):
            return await operation_func()
        else:
            return operation_func()

    async def _execute_fallback(self, operation_name: str, fallback_func: Callable[[], T], start_time: float) -> T:
        """Execute fallback function with monitoring."""
        try:
            result = await self._run_async_operation(fallback_func)
            duration = time.time() - start_time
            if self.metrics:
                self.metrics.record_operation(f"{operation_name}.fallback", duration)
            self.logger.info(f"Fallback succeeded for {operation_name} in {duration:.3f}s")
            return result
        except Exception as e:
            if self.metrics:
                self.metrics.record_error(operation_name, "fallback_failed")
            raise wrap_exception(e, f"{operation_name} fallback", {"service_id": self.service_id})

    def _is_circuit_open(self, operation_name: str) -> bool:
        """Check if circuit breaker is open for an operation."""
        if operation_name not in self._circuit_breaker_state:
            return False

        state = self._circuit_breaker_state[operation_name]

        if state["state"] != "open":
            return False

        # Check if circuit should be half-open
        if datetime.now() > state["open_until"]:
            state["state"] = "half_open"
            return False

        return True

    def _record_circuit_success(self, operation_name: str) -> None:
        """Record successful operation for circuit breaker."""
        if operation_name not in self._circuit_breaker_state:
            self._circuit_breaker_state[operation_name] = {
                "failures": 0,
                "state": "closed",
                "open_until": None,
            }

        state = self._circuit_breaker_state[operation_name]
        state["failures"] = 0
        state["state"] = "closed"
        state["open_until"] = None

    def _record_circuit_failure(self, operation_name: str) -> None:
        """Record failed operation for circuit breaker."""
        if operation_name not in self._circuit_breaker_state:
            self._circuit_breaker_state[operation_name] = {
                "failures": 0,
                "state": "closed",
                "open_until": None,
            }

        state = self._circuit_breaker_state[operation_name]
        state["failures"] += 1

        # Open circuit after 5 failures
        if state["failures"] >= 5:
            state["state"] = "open"
            state["open_until"] = datetime.now() + timedelta(minutes=5)
            self.logger.warning(f"Circuit breaker opened for {operation_name} due to repeated failures")

    async def check_health(self) -> Dict[str, Any]:
        """
        Perform health check on the service.

        Returns:
            Health status information
        """
        try:
            health_info = {
                "service_name": self.service_name,
                "service_id": self.service_id,
                "status": "healthy",
                "initialized": self._initialized,
                "timestamp": datetime.now().isoformat(),
            }

            # Add service-specific health checks
            service_health = await self._check_service_health()
            health_info.update(service_health)

            # Add metrics if available
            if self.metrics:
                health_info["metrics"] = self.metrics.get_stats()

            # Add circuit breaker states
            health_info["circuit_breakers"] = self._circuit_breaker_state.copy()

            return health_info

        except Exception as e:
            return {
                "service_name": self.service_name,
                "service_id": self.service_id,
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }

    async def _check_service_health(self) -> Dict[str, Any]:
        """
        Service-specific health checks.

        Override this method in subclasses to add custom health checks.

        Returns:
            Service-specific health information
        """
        return {"custom_checks": "none"}

    def validate_input(self, data: Any, schema: Type[T], context: str) -> T:
        """
        Validate input data against a schema.

        Args:
            data: Input data to validate
            schema: Pydantic model or dataclass to validate against
            context: Context for error messages

        Returns:
            Validated data

        Raises:
            ValidationError: When validation fails
        """
        try:
            if hasattr(schema, '__dataclass_fields__'):
                # Handle dataclasses
                if isinstance(data, schema):
                    return data
                elif isinstance(data, dict):
                    return schema(**data)
                else:
                    raise ValueError(f"Expected {schema.__name__} or dict, got {type(data).__name__}")
            elif hasattr(schema, 'parse_obj'):
                # Handle Pydantic models
                if isinstance(data, schema):
                    return data
                else:
                    return schema.parse_obj(data)
            else:
                raise ValueError(f"Unsupported schema type: {schema}")

        except Exception as e:
            raise ValidationError(
                f"Input validation failed for {context}: {e}",
                details={"schema": schema.__name__, "data_type": type(data).__name__}
            )

    async def get_cached_or_compute(
        self,
        cache_key: str,
        compute_func: Callable[[], T],
        ttl: Optional[int] = None,
        use_fallback_on_error: bool = True,
    ) -> T:
        """
        Get value from cache or compute and cache it.

        Args:
            cache_key: Cache key
            compute_func: Function to compute value if not cached
            ttl: Time to live in seconds
            use_fallback_on_error: Whether to compute if cache fails

        Returns:
            Cached or computed value
        """
        if not self.cache_manager:
            return await self._run_async_operation(compute_func)

        try:
            cached_value = await self.cache_manager.get(cache_key)
            if cached_value is not None:
                self.logger.debug(f"Cache hit for key: {cache_key}")
                return cached_value
        except Exception as e:
            self.logger.warning(f"Cache get failed for key {cache_key}: {e}")
            if not use_fallback_on_error:
                raise

        # Compute value
        self.logger.debug(f"Cache miss for key: {cache_key}, computing value")
        value = await self._run_async_operation(compute_func)

        # Cache the computed value
        try:
            await self.cache_manager.set(cache_key, value, ttl)
            self.logger.debug(f"Cached value for key: {cache_key}")
        except Exception as e:
            self.logger.warning(f"Cache set failed for key {cache_key}: {e}")

        return value

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value with fallback."""
        if self.config_manager:
            try:
                return self.config_manager.get(key, default)
            except Exception as e:
                self.logger.warning(f"Config get failed for key {key}: {e}")
        return default

    async def cleanup(self) -> None:
        """
        Cleanup service resources.

        Override this method in subclasses to implement custom cleanup logic.
        """
        self.logger.info(f"Cleaning up {self.service_name} service")
        try:
            await self._cleanup_implementation()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def _cleanup_implementation(self) -> None:
        """
        Service-specific cleanup logic.

        Override this method in subclasses.
        """
        pass