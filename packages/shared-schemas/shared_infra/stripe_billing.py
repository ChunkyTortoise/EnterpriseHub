"""Stripe billing integration service."""

from __future__ import annotations

from typing import Any

import stripe

from shared_schemas.events import DomainEvent, SubscriptionChanged
from shared_schemas.tenant import TenantTier


class StripeBillingError(Exception):
    """Raised when a Stripe operation fails."""


class StripeBillingService:
    """Manages Stripe customers, subscriptions, and usage reporting."""

    def __init__(self, stripe_api_key: str) -> None:
        self._api_key = stripe_api_key
        stripe.api_key = stripe_api_key

    async def create_customer(self, tenant_id: str, email: str, name: str) -> str:
        """Create a Stripe customer and return the customer ID."""
        try:
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata={"tenant_id": tenant_id},
            )
            return customer.id
        except stripe.StripeError as exc:
            raise StripeBillingError(f"Failed to create customer: {exc}") from exc

    async def create_subscription(self, customer_id: str, price_id: str) -> dict[str, Any]:
        """Create a subscription for a customer. Returns subscription dict."""
        try:
            subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{"price": price_id}],
            )
            return {
                "subscription_id": subscription.id,
                "status": subscription.status,
                "current_period_end": subscription.current_period_end,
            }
        except stripe.StripeError as exc:
            raise StripeBillingError(f"Failed to create subscription: {exc}") from exc

    async def record_usage(
        self,
        meter_event_name: str,
        tenant_id: str,
        quantity: int,
        idempotency_key: str | None = None,
    ) -> str:
        """Report metered usage via Stripe Billing Meter Events. Returns event identifier."""
        try:
            kwargs: dict[str, Any] = {
                "event_name": meter_event_name,
                "payload": {
                    "stripe_customer_id": tenant_id,
                    "value": str(quantity),
                },
            }
            if idempotency_key:
                kwargs["payload"]["idempotency_key"] = idempotency_key
            event = stripe.billing.MeterEvent.create(**kwargs)
            return event.identifier
        except stripe.StripeError as exc:
            raise StripeBillingError(f"Failed to record usage: {exc}") from exc

    async def handle_webhook(
        self,
        payload: bytes,
        sig_header: str,
        webhook_secret: str,
    ) -> DomainEvent | None:
        """Verify and process a Stripe webhook. Returns a domain event if relevant."""
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        except stripe.SignatureVerificationError as exc:
            raise StripeBillingError(f"Invalid webhook signature: {exc}") from exc

        event_type = event.get("type", "")
        data = event.get("data", {}).get("object", {})
        tenant_id = data.get("metadata", {}).get("tenant_id", "unknown")

        if event_type == "customer.subscription.updated":
            return SubscriptionChanged(
                tenant_id=tenant_id,
                old_tier=TenantTier.FREE,
                new_tier=TenantTier.PRO,
                payload={"stripe_event_id": event.get("id")},
            )

        if event_type == "invoice.payment_failed":
            return DomainEvent(
                event_type="billing.payment_failed",
                tenant_id=tenant_id,
                payload={"stripe_event_id": event.get("id")},
            )

        return None
