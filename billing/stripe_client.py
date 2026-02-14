"""
Stripe client for EnterpriseHub billing.

Provides async wrapper around Stripe API with idempotency support,
proper error handling, and logging.
"""
from __future__ import annotations

import logging
import hashlib
from typing import Any, Dict, Optional

import stripe

from billing import PlanTier, get_plan_config, PaymentFailedError

logger = logging.getLogger(__name__)


class StripeClient:
    """
    Async Stripe client wrapper with idempotency support.
    
    Handles customer management, subscriptions, payment methods,
    and billing portal sessions.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        publishable_key: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ) -> None:
        """
        Initialize Stripe client with API keys.
        
        Args:
            api_key: Stripe secret key (defaults to STRIPE_SECRET_KEY env var)
            publishable_key: Stripe publishable key
            webhook_secret: Stripe webhook signing secret
        """
        import os
        
        self.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY")
        self.publishable_key = publishable_key or os.environ.get("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = webhook_secret or os.environ.get("STRIPE_WEBHOOK_SECRET")
        
        if not self.api_key:
            logger.warning("Stripe API key not configured - billing disabled")
            self.enabled = False
        else:
            stripe.api_key = self.api_key
            self.enabled = True
            logger.info("Stripe client initialized successfully")
    
    def _generate_idempotency_key(self, prefix: str, identifier: str) -> str:
        """Generate idempotency key for Stripe API calls."""
        key = f"{prefix}:{identifier}:{self.api_key[:8] if self.api_key else 'none'}"
        return hashlib.sha256(key.encode()).hexdigest()[:32]
    
    async def create_customer(
        self,
        email: str,
        name: str,
        location_id: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Create a new Stripe customer.
        
        Args:
            email: Customer email
            name: Customer name
            location_id: Location/tenant ID for multi-tenant systems
            metadata: Optional metadata dict
            
        Returns:
            Stripe customer object
            
        Raises:
            PaymentFailedError: If customer creation fails
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            idempotency_key = self._generate_idempotency_key("cust", email)
            
            customer_metadata = metadata or {}
            if location_id:
                customer_metadata["location_id"] = location_id
            
            customer = stripe.Customer.create(
                email=email,
                name=name,
                metadata=customer_metadata,
                idempotency_key=idempotency_key,
            )
            
            logger.info(f"Created Stripe customer: {customer.id} for {email}")
            return customer
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Stripe customer: {e}")
            raise PaymentFailedError(f"Failed to create customer: {e.user_message or str(e)}")
    
    async def get_customer(self, customer_id: str) -> Dict[str, Any]:
        """Retrieve a Stripe customer by ID."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            return stripe.Customer.retrieve(customer_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve customer {customer_id}: {e}")
            raise PaymentFailedError(f"Failed to retrieve customer: {str(e)}")
    
    async def update_customer(
        self,
        customer_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Update a Stripe customer."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            return stripe.Customer.modify(customer_id, **kwargs)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update customer {customer_id}: {e}")
            raise PaymentFailedError(f"Failed to update customer: {str(e)}")
    
    async def create_subscription(
        self,
        customer_id: str,
        plan_tier: PlanTier,
        payment_method_id: Optional[str] = None,
        trial_days: int = 14,
        billing_interval: str = "month"
    ) -> Dict[str, Any]:
        """
        Create a new subscription for a customer.
        
        Args:
            customer_id: Stripe customer ID
            plan_tier: Plan tier (starter, professional, enterprise)
            payment_method_id: Optional payment method to attach
            trial_days: Number of trial days (default 14)
            billing_interval: "month" or "year"
            
        Returns:
            Stripe subscription object
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            # Get price ID from environment based on plan tier
            price_id = self._get_price_id(plan_tier, billing_interval)
            
            # Build subscription items
            items = [{"price": price_id}]
            
            # Build subscription data
            subscription_data: Dict[str, Any] = {
                "customer": customer_id,
                "items": items,
                "metadata": {
                    "plan_tier": plan_tier.value,
                    "billing_interval": billing_interval,
                },
            }
            
            # Add trial period if specified
            if trial_days > 0:
                subscription_data["trial_period_days"] = trial_days
            
            # Add default payment method if provided
            if payment_method_id:
                subscription_data["default_payment_method"] = payment_method_id
            
            idempotency_key = self._generate_idempotency_key(
                "sub", f"{customer_id}:{plan_tier.value}"
            )
            
            subscription = stripe.Subscription.create(
                **subscription_data,
                idempotency_key=idempotency_key,
            )
            
            logger.info(f"Created subscription: {subscription.id} for customer {customer_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create subscription: {e}")
            raise PaymentFailedError(f"Failed to create subscription: {e.user_message or str(e)}")
    
    async def update_subscription(
        self,
        subscription_id: str,
        plan_tier: Optional[PlanTier] = None,
        billing_interval: Optional[str] = None,
        cancel_at_period_end: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """
        Update an existing subscription.
        
        Used for plan upgrades/downgrades and cancellation settings.
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            update_data: Dict[str, Any] = {}
            
            # Update plan if provided
            if plan_tier and billing_interval:
                price_id = self._get_price_id(plan_tier, billing_interval)
                
                # Get current subscription to find the item ID
                current = stripe.Subscription.retrieve(subscription_id)
                if current and current.get("items", {}).get("data"):
                    item_id = current["items"]["data"][0]["id"]
                    update_data["items"] = [{"id": item_id, "price": price_id}]
                    update_data["metadata"] = {
                        "plan_tier": plan_tier.value,
                        "billing_interval": billing_interval,
                    }
            
            # Update cancellation settings
            if cancel_at_period_end is not None:
                update_data["cancel_at_period_end"] = cancel_at_period_end
            
            if not update_data:
                # Nothing to update
                return stripe.Subscription.retrieve(subscription_id)
            
            subscription = stripe.Subscription.modify(
                subscription_id,
                **update_data,
            )
            
            logger.info(f"Updated subscription: {subscription_id}")
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to update subscription {subscription_id}: {e}")
            raise PaymentFailedError(f"Failed to update subscription: {str(e)}")
    
    async def cancel_subscription(
        self,
        subscription_id: str,
        immediately: bool = False
    ) -> Dict[str, Any]:
        """
        Cancel a subscription.
        
        Args:
            subscription_id: Stripe subscription ID
            immediately: If True, cancel immediately. Otherwise, cancel at period end.
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            if immediately:
                subscription = stripe.Subscription.delete(subscription_id)
                logger.info(f"Canceled subscription immediately: {subscription_id}")
            else:
                subscription = stripe.Subscription.modify(
                    subscription_id,
                    cancel_at_period_end=True,
                )
                logger.info(f"Set subscription to cancel at period end: {subscription_id}")
            
            return subscription
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to cancel subscription {subscription_id}: {e}")
            raise PaymentFailedError(f"Failed to cancel subscription: {str(e)}")
    
    async def get_subscription(self, subscription_id: str) -> Dict[str, Any]:
        """Retrieve a subscription by ID."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            return stripe.Subscription.retrieve(subscription_id)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to retrieve subscription {subscription_id}: {e}")
            raise PaymentFailedError(f"Failed to retrieve subscription: {str(e)}")
    
    async def create_payment_method(
        self,
        customer_id: str,
        payment_method_id: str
    ) -> Dict[str, Any]:
        """Attach a payment method to a customer."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            payment_method = stripe.PaymentMethod.attach(
                payment_method_id,
                customer=customer_id,
            )
            
            # Set as default payment method
            stripe.Customer.modify(
                customer_id,
                invoice_settings={"default_payment_method": payment_method_id},
            )
            
            logger.info(f"Attached payment method {payment_method_id} to customer {customer_id}")
            return payment_method
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to attach payment method: {e}")
            raise PaymentFailedError(f"Failed to attach payment method: {str(e)}")
    
    async def get_payment_methods(self, customer_id: str) -> list[Dict[str, Any]]:
        """Get all payment methods for a customer."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            methods = stripe.PaymentMethod.list(
                customer=customer_id,
                type="card",
            )
            return methods.data
        except stripe.error.StripeError as e:
            logger.error(f"Failed to list payment methods: {e}")
            raise PaymentFailedError(f"Failed to list payment methods: {str(e)}")
    
    async def create_billing_portal_session(
        self,
        customer_id: str,
        return_url: str
    ) -> Dict[str, Any]:
        """Create a Stripe Billing Portal session."""
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url,
            )
            return session
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create billing portal session: {e}")
            raise PaymentFailedError(f"Failed to create billing portal: {str(e)}")
    
    async def create_checkout_session(
        self,
        customer_id: str,
        plan_tier: PlanTier,
        billing_interval: str = "month",
        success_url: str = "",
        cancel_url: str = "",
    ) -> Dict[str, Any]:
        """
        Create a Stripe Checkout session for subscription.
        
        Args:
            customer_id: Stripe customer ID
            plan_tier: Plan tier to subscribe to
            billing_interval: "month" or "year"
            success_url: URL to redirect on success
            cancel_url: URL to redirect on cancel
            
        Returns:
            Stripe checkout session object
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            price_id = self._get_price_id(plan_tier, billing_interval)
            
            session = stripe.checkout.Session.create(
                customer=customer_id,
                mode="subscription",
                line_items=[{
                    "price": price_id,
                    "quantity": 1,
                }],
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "plan_tier": plan_tier.value,
                    "billing_interval": billing_interval,
                },
            )
            
            logger.info(f"Created checkout session: {session.id}")
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create checkout session: {e}")
            raise PaymentFailedError(f"Failed to create checkout session: {str(e)}")
    
    async def construct_webhook_event(
        self,
        payload: bytes,
        sig_header: str
    ) -> Dict[str, Any]:
        """
        Construct and verify a webhook event.
        
        Args:
            payload: Raw request body
            sig_header: Stripe-Signature header value
            
        Returns:
            Verified Stripe event object
            
        Raises:
            ValueError: If signature verification fails
        """
        if not self.enabled or not self.webhook_secret:
            raise RuntimeError("Stripe webhook secret not configured")
        
        try:
            event = stripe.Webhook.construct_event(
                payload,
                sig_header,
                self.webhook_secret,
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {e}")
            raise ValueError(f"Invalid payload: {str(e)}")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            raise ValueError(f"Invalid signature: {str(e)}")
    
    async def report_usage(
        self,
        subscription_item_id: str,
        quantity: int,
        timestamp: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Report usage for metered billing.
        
        Args:
            subscription_item_id: Stripe subscription item ID
            quantity: Usage quantity to report
            timestamp: Unix timestamp (defaults to now)
            
        Returns:
            Usage record object
        """
        if not self.enabled:
            raise RuntimeError("Stripe is not configured")
        
        try:
            import time
            ts = timestamp or int(time.time())
            
            record = stripe.SubscriptionItem.create_usage_record(
                subscription_item_id,
                quantity=quantity,
                timestamp=ts,
                action="increment",
            )
            
            logger.debug(f"Reported usage: {quantity} for item {subscription_item_id}")
            return record
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to report usage: {e}")
            raise PaymentFailedError(f"Failed to report usage: {str(e)}")
    
    def _get_price_id(self, plan_tier: PlanTier, interval: str) -> str:
        """
        Get Stripe price ID for a plan tier and interval.
        
        Looks up price IDs from environment variables.
        """
        import os
        
        # Map plan tier and interval to environment variable names
        env_var_map = {
            (PlanTier.STARTER, "month"): "STRIPE_STARTER_PRICE_ID",
            (PlanTier.STARTER, "year"): "STRIPE_STARTER_ANNUAL_PRICE_ID",
            (PlanTier.PROFESSIONAL, "month"): "STRIPE_PROFESSIONAL_PRICE_ID",
            (PlanTier.PROFESSIONAL, "year"): "STRIPE_PROFESSIONAL_ANNUAL_PRICE_ID",
            (PlanTier.ENTERPRISE, "month"): "STRIPE_ENTERPRISE_PRICE_ID",
            (PlanTier.ENTERPRISE, "year"): "STRIPE_ENTERPRISE_ANNUAL_PRICE_ID",
        }
        
        env_var = env_var_map.get((plan_tier, interval))
        if not env_var:
            raise ValueError(f"No price ID configured for {plan_tier.value} {interval}")
        
        price_id = os.environ.get(env_var)
        if not price_id:
            raise RuntimeError(f"Missing price ID for {plan_tier.value} {interval}: {env_var}")
        
        return price_id


# Global client instance
_stripe_client: Optional[StripeClient] = None


def get_stripe_client() -> StripeClient:
    """Get or create the global Stripe client instance."""
    global _stripe_client
    if _stripe_client is None:
        _stripe_client = StripeClient()
    return _stripe_client


def reset_stripe_client() -> None:
    """Reset the global Stripe client (useful for testing)."""
    global _stripe_client
    _stripe_client = None
