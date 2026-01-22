"""
Stripe Billing Service

Core service for subscription management, usage tracking, and billing operations.
Integrates with Stripe API for payment processing and invoice management.
"""

import os
import stripe
from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, Dict, List, Any
import hashlib
import hmac
from uuid import uuid4

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.api.schemas.billing import (
    SubscriptionTier,
    SubscriptionStatus,
    SUBSCRIPTION_TIERS,
    CreateSubscriptionRequest,
    ModifySubscriptionRequest,
    SubscriptionResponse,
    UsageRecordRequest,
    UsageRecordResponse,
    BillingError
)

logger = get_logger(__name__)


class BillingServiceError(Exception):
    """Base exception for billing service errors."""

    def __init__(self, message: str, recoverable: bool = True, stripe_error_code: Optional[str] = None):
        self.message = message
        self.recoverable = recoverable
        self.stripe_error_code = stripe_error_code
        super().__init__(message)


class BillingService:
    """
    Core Stripe billing integration service.

    Handles subscription lifecycle, usage tracking, and payment processing
    with comprehensive error handling and webhook signature verification.
    """

    def __init__(self):
        """Initialize Stripe client and configuration."""
        # Initialize Stripe with secret key
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY environment variable required")

        # Webhook secret for signature verification
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not set - webhook verification disabled")

        # Configuration
        self.api_version = "2023-10-16"  # Stripe API version
        stripe.api_version = self.api_version

        logger.info("BillingService initialized successfully")


    # ===================================================================
    # Customer Management
    # ===================================================================

    async def create_or_get_customer(self, location_id: str, email: Optional[str] = None,
                                   name: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or retrieve existing Stripe customer for a location.

        Args:
            location_id: GHL location ID
            email: Customer email (optional)
            name: Customer name (optional)

        Returns:
            Stripe customer object with customer_id

        Raises:
            BillingServiceError: If customer creation fails
        """
        try:
            # Check if customer already exists
            existing_customers = stripe.Customer.list(
                metadata={"location_id": location_id},
                limit=1
            )

            if existing_customers.data:
                customer = existing_customers.data[0]
                logger.info(f"Found existing customer {customer.id} for location {location_id}")
                return customer

            # Create new customer
            customer_data = {
                "metadata": {"location_id": location_id},
                "description": f"EnterpriseHub customer for location {location_id}"
            }

            if email:
                customer_data["email"] = email
            if name:
                customer_data["name"] = name

            customer = stripe.Customer.create(**customer_data)

            logger.info(f"Created new Stripe customer {customer.id} for location {location_id}")
            return customer

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create/get customer for location {location_id}: {e}")
            raise BillingServiceError(
                f"Customer creation failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    def _get_price_id(self, tier: SubscriptionTier, currency: str) -> str:
        """
        Phase 7: Multi-Currency Support.
        Get localized price ID for a tier and currency.
        """
        tier_config = SUBSCRIPTION_TIERS[tier]
        curr = currency.lower()
        
        # Mapping for international expansion (EMEA/APAC)
        currency_price_suffix = {
            "usd": "",
            "eur": "_eur",
            "gbp": "_gbp",
            "aud": "_aud",
            "sgd": "_sgd"
        }
        
        suffix = currency_price_suffix.get(curr, f"_{curr}")
        price_id = f"{tier_config.stripe_price_id}{suffix}"
        
        logger.info(f"Resolved Price ID: {price_id} for currency {currency}")
        return price_id

    # ===================================================================
    # Subscription Management
    # ===================================================================

    async def create_subscription(self, request: CreateSubscriptionRequest) -> Dict[str, Any]:
        """
        Create a new subscription with Stripe.

        Args:
            request: Subscription creation request with tier, payment method, etc.

        Returns:
            Created Stripe subscription object

        Raises:
            BillingServiceError: If subscription creation fails
        """
        try:
            # Get tier configuration
            tier_config = SUBSCRIPTION_TIERS[request.tier]

            # Create or get customer
            customer = await self.create_or_get_customer(
                request.location_id,
                request.email,
                request.name
            )

            # Attach payment method to customer
            stripe.PaymentMethod.attach(
                request.payment_method_id,
                customer=customer.id
            )

            # Set as default payment method
            stripe.Customer.modify(
                customer.id,
                invoice_settings={"default_payment_method": request.payment_method_id}
            )

            # Calculate trial end if trial requested
            trial_end = None
            if request.trial_days > 0:
                from datetime import timedelta
                trial_end = int((datetime.now() + timedelta(days=request.trial_days)).timestamp())

            # Create subscription
            subscription_data = {
                "customer": customer.id,
                "items": [{
                    "price": self._get_price_id(request.tier, request.currency),
                    "quantity": 1
                }],
                "metadata": {
                    "location_id": request.location_id,
                    "tier": request.tier.value,
                    "usage_allowance": str(tier_config.usage_allowance),
                    "overage_rate": str(tier_config.overage_rate),
                    "currency": request.currency
                },
                "expand": ["latest_invoice.payment_intent"],
                "payment_behavior": "default_incomplete",
                "collection_method": "charge_automatically"
            }

            if trial_end:
                subscription_data["trial_end"] = trial_end

            subscription = stripe.Subscription.create(**subscription_data)

            logger.info(f"Created subscription {subscription.id} for location {request.location_id}")

            return subscription

        except stripe.error.CardError as e:
            # Card was declined
            logger.error(f"Card declined for subscription creation: {e}")
            raise BillingServiceError(
                f"Payment method declined: {e.user_message}",
                recoverable=True,
                stripe_error_code=e.code
            )
        except stripe.error.InvalidRequestError as e:
            # Invalid parameters
            logger.error(f"Invalid request for subscription creation: {e}")
            raise BillingServiceError(
                f"Invalid subscription request: {str(e)}",
                recoverable=False,
                stripe_error_code=e.code
            )
        except Exception as e:
            logger.error(f"Unexpected error creating subscription: {e}")
            raise BillingServiceError(
                f"Subscription creation failed: {str(e)}",
                recoverable=True
            )


    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """
        Retrieve subscription details from Stripe.

        Args:
            subscription_id: Stripe subscription ID

        Returns:
            Stripe subscription object
        """
        try:
            subscription = stripe.Subscription.retrieve(
                subscription_id,
                expand=["customer", "latest_invoice"]
            )
            return subscription
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise BillingServiceError(
                f"Subscription retrieval failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    async def modify_subscription(self, subscription_id: str,
                                request: ModifySubscriptionRequest) -> Dict[str, Any]:
        """
        Modify an existing subscription (tier change, payment method, etc.).

        Args:
            subscription_id: Stripe subscription ID
            request: Modification request

        Returns:
            Updated Stripe subscription object
        """
        try:
            # Get current subscription
            current_subscription = await self.get_subscription(subscription_id)

            update_data = {}

            # Handle tier change
            if request.tier:
                tier_config = SUBSCRIPTION_TIERS[request.tier]
                update_data["items"] = [{
                    "id": current_subscription["items"]["data"][0]["id"],
                    "price": tier_config.stripe_price_id
                }]
                update_data["metadata"] = {
                    **current_subscription.metadata,
                    "tier": request.tier.value,
                    "usage_allowance": str(tier_config.usage_allowance),
                    "overage_rate": str(tier_config.overage_rate)
                }
                update_data["proration_behavior"] = "create_prorations"

            # Handle payment method change
            if request.payment_method_id:
                # Attach new payment method to customer
                stripe.PaymentMethod.attach(
                    request.payment_method_id,
                    customer=current_subscription.customer
                )

                # Update customer's default payment method
                stripe.Customer.modify(
                    current_subscription.customer,
                    invoice_settings={"default_payment_method": request.payment_method_id}
                )

            # Handle cancellation scheduling
            if request.cancel_at_period_end is not None:
                update_data["cancel_at_period_end"] = request.cancel_at_period_end

            # Apply updates if any
            if update_data:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    **update_data
                )

                logger.info(f"Modified subscription {subscription_id}")
                return subscription
            else:
                return current_subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to modify subscription {subscription_id}: {e}")
            raise BillingServiceError(
                f"Subscription modification failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    async def cancel_subscription(self, subscription_id: str,
                                immediate: bool = False) -> Dict[str, Any]:
        """
        Cancel a subscription immediately or at period end.

        Args:
            subscription_id: Stripe subscription ID
            immediate: If True, cancel immediately; otherwise at period end

        Returns:
            Canceled Stripe subscription object
        """
        try:
            if immediate:
                # Cancel immediately
                subscription = stripe.Subscription.cancel(subscription_id)
                logger.info(f"Canceled subscription {subscription_id} immediately")
            else:
                # Schedule cancellation at period end
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True
                )
                logger.info(f"Scheduled cancellation for subscription {subscription_id} at period end")

            return subscription

        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise BillingServiceError(
                f"Subscription cancellation failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    # ===================================================================
    # Usage Recording
    # ===================================================================

    async def add_usage_record(self, request: UsageRecordRequest) -> Dict[str, Any]:
        """
        Add a usage record to Stripe for billing.

        Args:
            request: Usage record request with lead details and pricing

        Returns:
            Created Stripe usage record
        """
        try:
            # Generate idempotency key to prevent duplicate billing
            idempotency_key = self._generate_idempotency_key(
                request.subscription_id,
                request.lead_id,
                request.contact_id
            )

            # Get subscription to find the subscription item
            subscription = await self.get_subscription(str(request.subscription_id))
            subscription_item_id = subscription["items"]["data"][0]["id"]

            # Create usage record in Stripe
            usage_record = stripe.UsageRecord.create(
                subscription_item=subscription_item_id,
                quantity=1,  # Always 1 lead
                timestamp=int(datetime.now(timezone.utc).timestamp()),
                action="increment",
                idempotency_key=idempotency_key
            )

            logger.info(
                f"Created usage record {usage_record.id} for subscription {request.subscription_id}, "
                f"lead {request.lead_id}, amount ${request.amount}"
            )

            return usage_record

        except stripe.error.StripeError as e:
            logger.error(f"Failed to create usage record: {e}")
            raise BillingServiceError(
                f"Usage record creation failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    def _generate_idempotency_key(self, subscription_id: int, lead_id: str,
                                contact_id: str) -> str:
        """
        Generate idempotency key for usage records to prevent duplicates.

        Args:
            subscription_id: Database subscription ID
            lead_id: GHL lead ID
            contact_id: GHL contact ID

        Returns:
            SHA256 hash as idempotency key
        """
        key_data = f"{subscription_id}:{lead_id}:{contact_id}:{datetime.now().date()}"
        return hashlib.sha256(key_data.encode()).hexdigest()[:32]


    # ===================================================================
    # Webhook Processing
    # ===================================================================

    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify Stripe webhook signature for security.

        Args:
            payload: Raw webhook payload bytes
            signature: Stripe signature header

        Returns:
            True if signature is valid, False otherwise
        """
        if not self.webhook_secret:
            logger.warning("Webhook signature verification disabled - no secret configured")
            return True

        try:
            stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            return True
        except stripe.error.SignatureVerificationError:
            logger.error("Invalid webhook signature")
            return False
        except Exception as e:
            logger.error(f"Webhook signature verification error: {e}")
            return False


    async def process_webhook_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process Stripe webhook event.

        Args:
            event: Stripe event object

        Returns:
            Processing result with actions taken
        """
        event_type = event.get("type")
        event_data = event.get("data", {}).get("object", {})

        logger.info(f"Processing webhook event {event['id']} of type {event_type}")

        actions_taken = []

        try:
            if event_type == "invoice.payment_succeeded":
                # Payment successful - update subscription usage
                actions_taken.append("reset_usage_counter")
                actions_taken.append("update_subscription_period")

            elif event_type == "invoice.payment_failed":
                # Payment failed - mark subscription as past due
                actions_taken.append("mark_subscription_past_due")
                actions_taken.append("send_payment_failed_notification")

            elif event_type == "customer.subscription.updated":
                # Subscription updated - sync with database
                actions_taken.append("sync_subscription_status")
                actions_taken.append("update_tier_configuration")

            elif event_type == "customer.subscription.deleted":
                # Subscription canceled - deactivate features
                actions_taken.append("mark_subscription_canceled")
                actions_taken.append("deactivate_billing_features")

            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                actions_taken.append(f"logged_unhandled_event_{event_type}")

            return {
                "event_id": event["id"],
                "event_type": event_type,
                "processed": True,
                "actions_taken": actions_taken,
                "error": None
            }

        except Exception as e:
            logger.error(f"Failed to process webhook event {event['id']}: {e}")
            return {
                "event_id": event["id"],
                "event_type": event_type,
                "processed": False,
                "actions_taken": actions_taken,
                "error": str(e)
            }


    # ===================================================================
    # Invoice Management
    # ===================================================================

    async def get_customer_invoices(self, customer_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve invoices for a customer.

        Args:
            customer_id: Stripe customer ID
            limit: Maximum number of invoices to return

        Returns:
            List of invoice objects
        """
        try:
            invoices = stripe.Invoice.list(
                customer=customer_id,
                limit=limit,
                expand=["data.subscription"]
            )

            return invoices.data

        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve invoices for customer {customer_id}: {e}")
            raise BillingServiceError(
                f"Invoice retrieval failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )


    async def get_upcoming_invoice(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the upcoming invoice for a customer.

        Args:
            customer_id: Stripe customer ID

        Returns:
            Upcoming invoice object or None if no upcoming invoice
        """
        try:
            upcoming_invoice = stripe.Invoice.upcoming(customer=customer_id)
            return upcoming_invoice

        except stripe.error.InvalidRequestError:
            # No upcoming invoice (common for customers without active subscriptions)
            return None
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve upcoming invoice for customer {customer_id}: {e}")
            raise BillingServiceError(
                f"Upcoming invoice retrieval failed: {str(e)}",
                recoverable=True,
                stripe_error_code=e.code if hasattr(e, 'code') else None
            )