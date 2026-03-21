"""
Billing Notification Service

Lightweight dispatcher for billing lifecycle notifications:
trial ending, payment failures, usage thresholds, and cancellations.

Integrates with MonitoringService for alerts. Designed with hooks
for future email/SMS dispatch.
"""

from typing import Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class BillingNotificationService:
    """Dispatches billing lifecycle notifications via monitoring alerts."""

    def __init__(self, monitoring_service=None):
        self._monitoring = monitoring_service

    async def notify_trial_ending(self, subscription_id: int, days_remaining: int) -> None:
        """Notify that a trial subscription will end soon."""
        logger.info(
            "Trial ending notification dispatched",
            extra={"subscription_id": subscription_id, "days_remaining": days_remaining},
        )
        if self._monitoring:
            await self._monitoring.create_alert(
                service_name="billing",
                severity="warning",
                title="Trial Ending Soon",
                message=f"Subscription {subscription_id} trial ends in {days_remaining} day(s)",
                metadata={"subscription_id": subscription_id, "days_remaining": days_remaining},
            )
        # Hook: future email/SMS dispatch goes here

    async def notify_payment_failed(self, subscription_id: int, invoice_id: str) -> None:
        """Notify that a subscription payment failed."""
        logger.warning(
            "Payment failed notification dispatched",
            extra={"subscription_id": subscription_id, "invoice_id": invoice_id},
        )
        if self._monitoring:
            await self._monitoring.create_alert(
                service_name="billing",
                severity="critical",
                title="Payment Failed",
                message=f"Payment failed for subscription {subscription_id}, invoice {invoice_id}",
                metadata={"subscription_id": subscription_id, "invoice_id": invoice_id},
            )
        # Hook: future email/SMS dispatch goes here

    async def notify_usage_threshold(self, location_id: str, threshold_pct: int) -> None:
        """Notify that usage has crossed a threshold (e.g., 80%)."""
        logger.info(
            "Usage threshold notification dispatched",
            extra={"location_id": location_id, "threshold_pct": threshold_pct},
        )
        if self._monitoring:
            await self._monitoring.create_alert(
                service_name="billing",
                severity="warning",
                title=f"Usage at {threshold_pct}%",
                message=f"Location {location_id} has used {threshold_pct}% of their allowance",
                metadata={"location_id": location_id, "threshold_pct": threshold_pct},
            )
        # Hook: future email/SMS dispatch goes here

    async def notify_subscription_canceled(self, subscription_id: int) -> None:
        """Notify that a subscription was canceled."""
        logger.info(
            "Subscription canceled notification dispatched",
            extra={"subscription_id": subscription_id},
        )
        if self._monitoring:
            await self._monitoring.create_alert(
                service_name="billing",
                severity="info",
                title="Subscription Canceled",
                message=f"Subscription {subscription_id} has been canceled",
                metadata={"subscription_id": subscription_id},
            )
        # Hook: future email/SMS dispatch goes here


_notification_service: Optional[BillingNotificationService] = None


def get_billing_notification_service(monitoring_service=None) -> BillingNotificationService:
    """Get or create the singleton BillingNotificationService."""
    global _notification_service
    if _notification_service is None:
        _notification_service = BillingNotificationService(monitoring_service=monitoring_service)
    return _notification_service
