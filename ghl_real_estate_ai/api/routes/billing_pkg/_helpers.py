"""Shared helpers for billing route handlers.

Extracted from billing.py to support decomposition into domain-specific
billing modules. Contains:
- Dependency injection factories
- Retry logic with exponential backoff
- Billing event tracking
- Webhook event storage
"""

import asyncio
from typing import Any, Dict

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.billing_service import BillingService
from ghl_real_estate_ai.services.monitoring_service import AlertSeverity, MonitoringService
from ghl_real_estate_ai.services.subscription_manager import SubscriptionManager

logger = get_logger(__name__)


# ── Dependency injection factories ──────────────────────────────────────


def get_billing_service() -> BillingService:
    return BillingService()


def get_subscription_manager() -> SubscriptionManager:
    return SubscriptionManager()


def get_monitoring_service() -> MonitoringService:
    return MonitoringService()


# ── Retry logic ─────────────────────────────────────────────────────────


async def retry_with_exponential_backoff(
    func,
    *args,
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    **kwargs,
) -> Any:
    """Execute a function with exponential backoff retry on failure.

    Args:
        func: Async callable to retry.
        max_retries: Maximum number of retry attempts.
        base_delay: Initial delay in seconds.
        max_delay: Maximum delay cap in seconds.

    Returns:
        The result of the successful function call.

    Raises:
        The last exception if all retries are exhausted.
    """
    last_exception = None
    for attempt in range(max_retries + 1):
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                delay = min(base_delay * (2**attempt), max_delay)
                logger.warning(
                    "Billing operation failed (attempt %d/%d), retrying in %.1fs: %s",
                    attempt + 1,
                    max_retries + 1,
                    delay,
                    str(e),
                )
                await asyncio.sleep(delay)

    raise last_exception  # type: ignore[misc]


# ── Event tracking ──────────────────────────────────────────────────────


async def track_billing_event(event_type: str, data: Dict[str, Any]) -> None:
    """Track a billing event for analytics and auditing."""
    try:
        monitoring = get_monitoring_service()
        await monitoring.track_event(event_type, data)
    except Exception as e:
        logger.warning("Failed to track billing event %s: %s", event_type, e)


async def store_webhook_event(
    event_data: Dict[str, Any], processing_result: Dict[str, Any]
) -> None:
    """Store a Stripe webhook event for audit trail."""
    try:
        monitoring = get_monitoring_service()
        await monitoring.store_event(
            event_type="stripe_webhook",
            data={**event_data, "processing_result": processing_result},
        )
    except Exception as e:
        logger.warning("Failed to store webhook event: %s", e)
