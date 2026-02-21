"""
Stripe webhook handler for EnterpriseHub.

Processes Stripe webhook events and updates local subscription state.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Request, status

from billing import SubscriptionStatus
from billing.stripe_client import get_stripe_client

router = APIRouter(prefix="/webhook", tags=["billing-webhooks"])

logger = logging.getLogger(__name__)


class WebhookProcessor:
    """
    Processes Stripe webhook events.

    Handles all webhook event types and updates local state accordingly.
    """

    def __init__(self, db_connection=None) -> None:
        """
        Initialize webhook processor.

        Args:
            db_connection: Database connection pool or session factory
        """
        self.db = db_connection
        self.stripe = get_stripe_client()

    async def process_event(self, event: Dict[str, Any]) -> bool:
        """
        Process a Stripe webhook event.

        Args:
            event: Stripe event object

        Returns:
            True if processed successfully
        """
        event_type = event.get("type")
        event_id = event.get("id")
        event_data = event.get("data", {}).get("object", {})

        logger.info(f"Processing webhook: {event_type} ({event_id})")

        # Check for duplicate events (idempotency)
        if await self._is_duplicate_event(event_id):
            logger.debug(f"Duplicate webhook event: {event_id}")
            return True

        # Record event receipt
        await self._record_event(event_id, event_type, event_data)

        # Map event types to handlers
        handlers = {
            "invoice.payment_succeeded": self._handle_invoice_payment_succeeded,
            "invoice.payment_failed": self._handle_invoice_payment_failed,
            "customer.subscription.created": self._handle_subscription_created,
            "customer.subscription.updated": self._handle_subscription_updated,
            "customer.subscription.deleted": self._handle_subscription_deleted,
            "customer.subscription.trial_will_end": self._handle_trial_will_end,
            "checkout.session.completed": self._handle_checkout_completed,
            "customer.created": self._handle_customer_created,
            "customer.updated": self._handle_customer_updated,
        }

        handler = handlers.get(event_type)
        if handler:
            try:
                await handler(event_data)
                await self._mark_event_processed(event_id, True)
                return True
            except Exception as e:
                logger.error(f"Failed to process {event_type}: {e}")
                await self._mark_event_processed(event_id, False, str(e))
                return False
        else:
            logger.debug(f"No handler for event type: {event_type}")
            await self._mark_event_processed(event_id, True)
            return True

    async def _handle_invoice_payment_succeeded(self, invoice: Dict[str, Any]) -> None:
        """Handle successful invoice payment."""
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return

        if self.db is None:
            return

        async with self.db.acquire() as conn:
            # Find local subscription
            row = await conn.fetchrow(
                """
                SELECT * FROM subscriptions
                WHERE stripe_subscription_id = $1
                """,
                subscription_id,
            )

            if not row:
                logger.warning(f"Subscription not found for invoice: {subscription_id}")
                return

            # Update subscription status
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'active',
                    updated_at = NOW()
                WHERE stripe_subscription_id = $1
                """,
                subscription_id,
            )

            # Update period dates from invoice
            if invoice.get("period_start"):
                period_start = datetime.fromtimestamp(invoice["period_start"], tz=timezone.utc)
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET current_period_start = $2
                    WHERE stripe_subscription_id = $1
                    """,
                    subscription_id,
                    period_start,
                )

            if invoice.get("period_end"):
                period_end = datetime.fromtimestamp(invoice["period_end"], tz=timezone.utc)
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET current_period_end = $2
                    WHERE stripe_subscription_id = $1
                    """,
                    subscription_id,
                    period_end,
                )

            # Record invoice
            await conn.execute(
                """
                INSERT INTO invoices (
                    stripe_invoice_id, subscription_id, stripe_customer_id,
                    amount_due, amount_paid, status, period_start, period_end,
                    paid_at, hosted_invoice_url, invoice_pdf
                )
                SELECT $1, s.id, $2, $3, $4, $5, $6, $7, NOW(), $8, $9
                FROM subscriptions s
                WHERE s.stripe_subscription_id = $10
                ON CONFLICT (stripe_invoice_id) DO UPDATE SET
                    status = EXCLUDED.status,
                    amount_paid = EXCLUDED.amount_paid,
                    paid_at = EXCLUDED.paid_at
                """,
                invoice.get("id"),
                invoice.get("customer"),
                invoice.get("amount_due", 0) / 100,  # Convert from cents
                invoice.get("amount_paid", 0) / 100,
                "paid",
                datetime.fromtimestamp(invoice["period_start"], tz=timezone.utc)
                if invoice.get("period_start")
                else None,
                datetime.fromtimestamp(invoice["period_end"], tz=timezone.utc) if invoice.get("period_end") else None,
                invoice.get("hosted_invoice_url"),
                invoice.get("invoice_pdf"),
                subscription_id,
            )

            logger.info(f"Invoice payment succeeded for subscription: {subscription_id}")

    async def _handle_invoice_payment_failed(self, invoice: Dict[str, Any]) -> None:
        """Handle failed invoice payment."""
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return

        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'past_due',
                    updated_at = NOW()
                WHERE stripe_subscription_id = $1
                """,
                subscription_id,
            )

            logger.warning(f"Invoice payment failed for subscription: {subscription_id}")

    async def _handle_subscription_created(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription creation."""
        stripe_sub_id = subscription.get("id")
        customer_id = subscription.get("customer")

        logger.info(f"Subscription created in Stripe: {stripe_sub_id}")

        # Update local subscription if it exists
        if self.db is None:
            return

        async with self.db.acquire() as conn:
            # Find by customer ID
            await conn.execute(
                """
                UPDATE subscriptions
                SET stripe_subscription_id = $2,
                    status = $3,
                    current_period_start = $4,
                    current_period_end = $5,
                    updated_at = NOW()
                WHERE stripe_customer_id = $1
                AND stripe_subscription_id IS NULL
                """,
                customer_id,
                stripe_sub_id,
                subscription.get("status"),
                datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc)
                if subscription.get("current_period_start")
                else None,
                datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc)
                if subscription.get("current_period_end")
                else None,
            )

    async def _handle_subscription_updated(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription update."""
        stripe_sub_id = subscription.get("id")

        if self.db is None:
            return

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM subscriptions
                WHERE stripe_subscription_id = $1
                """,
                stripe_sub_id,
            )

            if not row:
                logger.warning(f"Subscription not found for update: {stripe_sub_id}")
                return

            # Update status
            stripe_status = subscription.get("status")

            # Update period dates
            period_start = None
            period_end = None
            trial_end = None

            if subscription.get("current_period_start"):
                period_start = datetime.fromtimestamp(subscription["current_period_start"], tz=timezone.utc)
            if subscription.get("current_period_end"):
                period_end = datetime.fromtimestamp(subscription["current_period_end"], tz=timezone.utc)
            if subscription.get("trial_end"):
                trial_end = datetime.fromtimestamp(subscription["trial_end"], tz=timezone.utc)

            # Determine tier from price
            tier = row["tier"]  # Keep existing tier
            items = subscription.get("items", {}).get("data", [])
            if items:
                price_id = items[0].get("price", {}).get("id")
                # Could look up tier from price ID mapping

            await conn.execute(
                """
                UPDATE subscriptions
                SET status = $2,
                    current_period_start = COALESCE($3, current_period_start),
                    current_period_end = COALESCE($4, current_period_end),
                    trial_end = COALESCE($5, trial_end),
                    cancel_at_period_end = $6,
                    updated_at = NOW()
                WHERE stripe_subscription_id = $1
                """,
                stripe_sub_id,
                stripe_status,
                period_start,
                period_end,
                trial_end,
                subscription.get("cancel_at_period_end", False),
            )

            logger.info(f"Subscription updated: {stripe_sub_id}")

    async def _handle_subscription_deleted(self, subscription: Dict[str, Any]) -> None:
        """Handle subscription deletion (cancellation)."""
        stripe_sub_id = subscription.get("id")

        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE subscriptions
                SET status = 'canceled',
                    cancel_at_period_end = FALSE,
                    updated_at = NOW()
                WHERE stripe_subscription_id = $1
                """,
                stripe_sub_id,
            )

            logger.info(f"Subscription canceled: {stripe_sub_id}")

    async def _handle_trial_will_end(self, subscription: Dict[str, Any]) -> None:
        """Handle trial ending soon notification."""
        stripe_sub_id = subscription.get("id")

        logger.info(f"Trial ending soon for subscription: {stripe_sub_id}")

        # Could trigger email notification here
        # For now, just log the event

    async def _handle_checkout_completed(self, session: Dict[str, Any]) -> None:
        """Handle checkout session completion."""
        customer_id = session.get("customer")
        subscription_id = session.get("subscription")

        logger.info(f"Checkout completed: customer={customer_id}, subscription={subscription_id}")

        # The subscription handlers will update the local state
        # This handler can be used for post-checkout actions

    async def _handle_customer_created(self, customer: Dict[str, Any]) -> None:
        """Handle customer creation."""
        customer_id = customer.get("id")
        email = customer.get("email")

        logger.info(f"Customer created in Stripe: {customer_id} ({email})")

        if self.db is None:
            return

        # Record customer mapping
        location_id = customer.get("metadata", {}).get("location_id")
        if location_id:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO stripe_customers (
                        location_id, stripe_customer_id, email, name
                    )
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (location_id) DO UPDATE SET
                        stripe_customer_id = EXCLUDED.stripe_customer_id,
                        email = EXCLUDED.email,
                        name = EXCLUDED.name,
                        updated_at = NOW()
                    """,
                    location_id,
                    customer_id,
                    email,
                    customer.get("name"),
                )

    async def _handle_customer_updated(self, customer: Dict[str, Any]) -> None:
        """Handle customer update."""
        customer_id = customer.get("id")

        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE stripe_customers
                SET email = $2,
                    name = $3,
                    updated_at = NOW()
                WHERE stripe_customer_id = $1
                """,
                customer_id,
                customer.get("email"),
                customer.get("name"),
            )

    async def _is_duplicate_event(self, event_id: str) -> bool:
        """Check if event has already been processed."""
        if self.db is None:
            return False

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id FROM billing_events
                WHERE event_id = $1 AND processed = TRUE
                """,
                event_id,
            )
            return row is not None

    async def _record_event(self, event_id: str, event_type: str, event_data: Dict[str, Any]) -> None:
        """Record event receipt."""
        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO billing_events (event_id, event_type, payload, processed)
                VALUES ($1, $2, $3, FALSE)
                ON CONFLICT (event_id) DO NOTHING
                """,
                event_id,
                event_type,
                {"id": event_id, "type": event_type, "data_id": event_data.get("id")},
            )

    async def _mark_event_processed(self, event_id: str, success: bool, error: Optional[str] = None) -> None:
        """Mark event as processed."""
        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                UPDATE billing_events
                SET processed = TRUE,
                    processed_at = NOW(),
                    error_message = $2
                WHERE event_id = $1
                """,
                event_id,
                error,
            )


# Global processor instance
_webhook_processor: Optional[WebhookProcessor] = None


def get_webhook_processor(db_connection=None) -> WebhookProcessor:
    """Get or create the global webhook processor instance."""
    global _webhook_processor
    if _webhook_processor is None:
        _webhook_processor = WebhookProcessor(db_connection)
    return _webhook_processor


@router.post("/stripe")
async def stripe_webhook(request: Request):
    """
    Stripe webhook endpoint.

    Receives and processes webhook events from Stripe.
    """
    try:
        # Get raw payload
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            logger.warning("Missing Stripe signature header")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Missing signature",
            )

        # Verify and construct event
        stripe_client = get_stripe_client()
        try:
            event = await stripe_client.construct_webhook_event(payload, sig_header)
        except ValueError as e:
            logger.warning(f"Invalid webhook: {e}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )

        event_id = event.get("id")
        event_type = event.get("type")

        # Process the event
        processor = get_webhook_processor()
        try:
            processed = await processor.process_event(event)

            return {"received": True, "processed": processed}

        except Exception as e:
            logger.error(f"Error processing webhook {event_id}: {e}")

            # Still return 200 to prevent Stripe retries
            # The error is logged for investigation
            return {
                "received": True,
                "processed": False,
                "error": str(e),
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in webhook handler: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal error",
        )


@router.get("/health")
async def webhook_health():
    """Health check endpoint for webhook service."""
    return {"status": "healthy", "service": "billing-webhooks"}
