"""Stripe billing service — wraps metered billing for all products."""

from __future__ import annotations

import logging
from typing import Any

import stripe

from shared_schemas.billing import UsageEvent

logger = logging.getLogger(__name__)


class StripeBillingService:
    """Wraps Stripe metered billing -- reuse across ALL products."""

    def __init__(self, api_key: str, webhook_secret: str | None = None):
        self.api_key = api_key
        self.webhook_secret = webhook_secret
        stripe.api_key = api_key

    async def create_customer(self, email: str, name: str, metadata: dict | None = None) -> dict:
        """Create a Stripe customer for a new tenant."""
        return stripe.Customer.create(
            email=email,
            name=name,
            metadata=metadata or {},
        )

    async def create_subscription(self, customer_id: str, price_id: str) -> dict:
        """Create a subscription for a customer."""
        return stripe.Subscription.create(
            customer=customer_id,
            items=[{"price": price_id}],
        )

    async def report_usage(self, event: UsageEvent) -> dict:
        """Report a usage event to Stripe's metering system."""
        return stripe.billing.MeterEvent.create(
            event_name=event.event_type.value,
            payload={
                "stripe_customer_id": event.tenant_id,
                "value": str(int(event.quantity)),
            },
        )

    async def create_checkout_session(
        self,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
    ) -> str:
        """Create a Stripe Checkout session and return the URL."""
        session = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return session.url

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict[str, Any]:
        """Verify and parse a Stripe webhook event.

        Args:
            payload: Raw request body bytes.
            sig_header: Value of the Stripe-Signature header.

        Returns:
            Parsed event dict.

        Raises:
            ValueError: If signature verification fails or webhook secret is not configured.
        """
        if not self.webhook_secret:
            raise ValueError("Webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(payload, sig_header, self.webhook_secret)
        except stripe.error.SignatureVerificationError as e:
            logger.warning("Webhook signature verification failed: %s", e)
            raise ValueError("Invalid webhook signature") from e

        logger.info("Received webhook event: type=%s id=%s", event["type"], event["id"])
        return dict(event)
