"""Logging utilities for Advanced RAG System.

Provides structured logging with JSON output support for production
environments and human-readable format for development.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, List, Optional

import structlog
from structlog.processors import JSONRenderer
from structlog.stdlib import BoundLogger

from src.core.config import Settings, get_settings


def configure_logging(
    settings: Optional[Settings] = None,
    json_format: bool = False,
) -> None:
    """Configure structured logging for the application.

    Args:
        settings: Application settings (uses defaults if None)
        json_format: Force JSON output (auto-detected from settings if None)
    """
    if settings is None:
        settings = get_settings()

    # Determine output format
    use_json = json_format or not settings.debug

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.log_level),
    )

    # Configure structlog
    shared_processors: List[Any] = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.ExtraAdder(),
    ]

    if use_json:
        # Production: JSON format
        structlog.configure(
            processors=shared_processors + [JSONRenderer()],
            wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )
    else:
        # Development: Pretty console format
        structlog.configure(
            processors=shared_processors
            + [
                structlog.dev.ConsoleRenderer(
                    colors=True,
                    sort_keys=False,
                )
            ],
            wrapper_class=structlog.make_filtering_bound_logger(getattr(logging, settings.log_level)),
            context_class=dict,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )


def get_logger(name: str) -> BoundLogger:
    """Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)  # type: ignore[no-any-return]


class ContextualLogger:
    """Logger with automatic context binding.

    Provides a convenient way to add persistent context to all log messages.

    Example:
        ```python
        logger = ContextualLogger("my_module", request_id="abc123")
        logger.info("Processing request")  # Includes request_id in log
        ```
    """

    def __init__(self, name: str, **context: Any) -> None:
        """Initialize contextual logger.

        Args:
            name: Logger name
            **context: Persistent context fields
        """
        self._logger = get_logger(name).bind(**context)

    def debug(self, message: str, **extra: Any) -> None:
        """Log debug message."""
        self._logger.debug(message, **extra)

    def info(self, message: str, **extra: Any) -> None:
        """Log info message."""
        self._logger.info(message, **extra)

    def warning(self, message: str, **extra: Any) -> None:
        """Log warning message."""
        self._logger.warning(message, **extra)

    def error(self, message: str, **extra: Any) -> None:
        """Log error message."""
        self._logger.error(message, **extra)

    def exception(self, message: str, **extra: Any) -> None:
        """Log exception with traceback."""
        self._logger.exception(message, **extra)

    def bind(self, **context: Any) -> "ContextualLogger":
        """Create new logger with additional context.

        Args:
            **context: Additional context fields

        Returns:
            New ContextualLogger with merged context
        """
        return ContextualLogger(
            self._logger._logger.name,
            **context,
        )


def log_execution_time(
    logger: Optional[BoundLogger] = None,
    level: str = "debug",
    message: str = "Operation completed",
) -> Any:
    """Decorator to log function execution time.

    Args:
        logger: Logger to use (creates default if None)
        level: Log level (debug, info, warning, error)
        message: Log message prefix

    Example:
        ```python
        @log_execution_time(message="Embedding generation")
        async def generate_embeddings(texts):
            ...
        ```
    """
    import functools
    import time

    def decorator(func: Any) -> Any:
        nonlocal logger
        if logger is None:
            logger = get_logger(func.__module__)

        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_method = getattr(logger, level)
                log_method(
                    message,
                    duration_ms=round(elapsed * 1000, 2),
                    function=func.__name__,
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    f"{message} failed",
                    duration_ms=round(elapsed * 1000, 2),
                    function=func.__name__,
                    error=str(e),
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                elapsed = time.perf_counter() - start
                log_method = getattr(logger, level)
                log_method(
                    message,
                    duration_ms=round(elapsed * 1000, 2),
                    function=func.__name__,
                )
                return result
            except Exception as e:
                elapsed = time.perf_counter() - start
                logger.error(
                    f"{message} failed",
                    duration_ms=round(elapsed * 1000, 2),
                    function=func.__name__,
                    error=str(e),
                )
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Import asyncio here to avoid issues with the decorator
import asyncio
