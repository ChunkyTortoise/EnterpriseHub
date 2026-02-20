"""
Retry mechanism with exponential backoff for buyer bot operations.
"""

import asyncio
import random
from typing import Callable, TypeVar

from ghl_real_estate_ai.agents.buyer.exceptions import (
    BuyerIntentAnalysisError,
    ClaudeAPIError,
    ComplianceValidationError,
    NetworkError,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

T = TypeVar("T")


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 500,
        exponential_base: float = 2.0,
        jitter_factor: float = 0.1,
    ):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.exponential_base = exponential_base
        self.jitter_factor = jitter_factor


DEFAULT_RETRY_CONFIG = RetryConfig()

RETRYABLE_EXCEPTIONS = (ClaudeAPIError, NetworkError)
NON_RETRYABLE_EXCEPTIONS = (BuyerIntentAnalysisError, ComplianceValidationError)


async def async_retry_with_backoff(
    coro_factory: Callable[[], T],
    retry_config: RetryConfig = None,
    context_label: str = "operation"
) -> T:
    """
    Retry an async operation with exponential backoff and jitter.

    Args:
        coro_factory: Callable that returns a new coroutine on each invocation.
        retry_config: Retry configuration. Uses DEFAULT_RETRY_CONFIG if None.
        context_label: Label for logging.

    Returns:
        The result of the coroutine on success.

    Raises:
        The last exception if all retries are exhausted, or immediately
        for non-retryable exceptions.
    """
    config = retry_config or DEFAULT_RETRY_CONFIG
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await coro_factory()
        except NON_RETRYABLE_EXCEPTIONS:
            raise
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < config.max_retries:
                backoff_ms = config.initial_backoff_ms * (config.exponential_base ** attempt)
                jitter = backoff_ms * config.jitter_factor * (2 * random.random() - 1)
                sleep_seconds = (backoff_ms + jitter) / 1000.0
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} for {context_label}: {e}. "
                    f"Backing off {sleep_seconds:.3f}s"
                )
                await asyncio.sleep(sleep_seconds)
            else:
                logger.error(f"All {config.max_retries} retries exhausted for {context_label}: {e}")
                raise

    raise last_exception  # Should not reach here, but safety net