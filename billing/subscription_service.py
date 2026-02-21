"""
Subscription service for managing billing lifecycle in EnterpriseHub.

Provides business logic for subscription management,
plan upgrades/downgrades, and quota enforcement.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from billing import (
    PaymentFailedError,
    PlanTier,
    SubscriptionStatus,
    get_plan_config,
    get_plan_price,
)
from billing.stripe_client import get_stripe_client

logger = logging.getLogger(__name__)


class SubscriptionService:
    """
    Service for managing subscriptions and billing operations.

    Coordinates between local database state and Stripe,
    handling plan changes, cancellations, and quota management.
    """

    TRIAL_DAYS = 14
    GRACE_PERIOD_HOURS = 48

    def __init__(self, db_connection=None) -> None:
        """
        Initialize subscription service.

        Args:
            db_connection: Database connection pool or session factory
        """
        self.stripe = get_stripe_client()
        self.db = db_connection

    async def create_subscription(
        self,
        location_id: str,
        plan_tier: PlanTier,
        email: str,
        name: str,
        payment_method_id: Optional[str] = None,
        billing_interval: str = "month",
        trial_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create a new subscription for a location/tenant.

        Args:
            location_id: Location/tenant ID
            plan_tier: Plan tier (starter, professional, enterprise)
            email: Customer email
            name: Customer name
            payment_method_id: Stripe payment method ID
            billing_interval: "month" or "year"
            trial_days: Override default trial period

        Returns:
            Created subscription record
        """
        trial_days = trial_days or self.TRIAL_DAYS

        # Check if location already has an active subscription
        existing = await self._get_active_subscription(location_id)
        if existing:
            raise ValueError(f"Location {location_id} already has an active subscription")

        # Get plan config
        plan_config = get_plan_config(plan_tier)

        # Create Stripe customer
        stripe_customer = await self.stripe.create_customer(
            email=email,
            name=name,
            location_id=location_id,
        )
        stripe_customer_id = stripe_customer["id"]

        # Create Stripe subscription
        try:
            stripe_sub = await self.stripe.create_subscription(
                customer_id=stripe_customer_id,
                plan_tier=plan_tier,
                payment_method_id=payment_method_id,
                trial_days=trial_days,
                billing_interval=billing_interval,
            )
        except PaymentFailedError:
            # If payment fails, still create subscription in incomplete state
            logger.warning(f"Payment failed for location {location_id}, creating incomplete subscription")
            stripe_sub = {"id": None, "status": "incomplete"}

        # Create local subscription record
        now = datetime.now(timezone.utc)
        subscription_id = str(uuid.uuid4())

        subscription = {
            "id": subscription_id,
            "location_id": location_id,
            "stripe_customer_id": stripe_customer_id,
            "stripe_subscription_id": stripe_sub.get("id"),
            "tier": plan_tier.value,
            "status": stripe_sub.get("status", "incomplete"),
            "billing_interval": billing_interval,
            "current_period_start": now,
            "current_period_end": now,  # Will be updated by webhook
            "usage_allowance": plan_config.get("lead_quota", 100),
            "usage_current": 0,
            "trial_end": None,
            "cancel_at_period_end": False,
            "created_at": now,
            "updated_at": now,
        }

        # Save to database
        await self._save_subscription(subscription)

        logger.info(f"Created subscription for location {location_id}: {plan_tier.value}")
        return subscription

    async def upgrade_subscription(
        self,
        location_id: str,
        new_plan_tier: PlanTier,
        billing_interval: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Upgrade a location to a higher plan tier.

        Stripe handles proration automatically.
        """
        subscription = await self._get_active_subscription(location_id)
        if not subscription:
            raise ValueError(f"No active subscription found for location {location_id}")

        current_tier = PlanTier(subscription["tier"])

        # Validate upgrade (can't downgrade here)
        plan_order = [PlanTier.STARTER, PlanTier.PROFESSIONAL, PlanTier.ENTERPRISE]
        if plan_order.index(new_plan_tier) <= plan_order.index(current_tier):
            raise ValueError(f"Cannot upgrade from {current_tier.value} to {new_plan_tier.value}")

        # Get new plan config
        plan_config = get_plan_config(new_plan_tier)
        interval = billing_interval or subscription["billing_interval"]

        # Update Stripe subscription
        if subscription.get("stripe_subscription_id"):
            try:
                await self.stripe.update_subscription(
                    subscription_id=subscription["stripe_subscription_id"],
                    plan_tier=new_plan_tier,
                    billing_interval=interval,
                )
            except PaymentFailedError as e:
                logger.error(f"Failed to upgrade subscription in Stripe: {e}")
                raise

        # Update local record
        subscription["tier"] = new_plan_tier.value
        subscription["billing_interval"] = interval
        subscription["usage_allowance"] = plan_config.get("lead_quota", 100)
        subscription["updated_at"] = datetime.now(timezone.utc)

        await self._save_subscription(subscription)

        logger.info(f"Upgraded location {location_id} to {new_plan_tier.value}")
        return subscription

    async def downgrade_subscription(
        self,
        location_id: str,
        new_plan_tier: PlanTier,
        billing_interval: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Downgrade a location to a lower plan tier.

        Changes take effect at the end of the current billing period.
        """
        subscription = await self._get_active_subscription(location_id)
        if not subscription:
            raise ValueError(f"No active subscription found for location {location_id}")

        current_tier = PlanTier(subscription["tier"])

        # Validate downgrade
        plan_order = [PlanTier.STARTER, PlanTier.PROFESSIONAL, PlanTier.ENTERPRISE]
        if plan_order.index(new_plan_tier) >= plan_order.index(current_tier):
            raise ValueError(f"Cannot downgrade from {current_tier.value} to {new_plan_tier.value}")

        # For downgrades, schedule the change at period end
        interval = billing_interval or subscription["billing_interval"]

        # Update Stripe subscription
        if subscription.get("stripe_subscription_id"):
            try:
                await self.stripe.update_subscription(
                    subscription_id=subscription["stripe_subscription_id"],
                    plan_tier=new_plan_tier,
                    billing_interval=interval,
                )
            except PaymentFailedError as e:
                logger.error(f"Failed to schedule downgrade in Stripe: {e}")
                raise

        # Note: We don't immediately update the local record for downgrades
        # The webhook will update it when the change takes effect

        logger.info(f"Scheduled downgrade for location {location_id} to {new_plan_tier.value}")
        return subscription

    async def cancel_subscription(
        self,
        location_id: str,
        immediately: bool = False,
    ) -> Dict[str, Any]:
        """
        Cancel a location's subscription.

        Args:
            location_id: Location ID
            immediately: If True, cancel immediately. Otherwise, cancel at period end.
        """
        subscription = await self._get_active_subscription(location_id)
        if not subscription:
            raise ValueError(f"No active subscription found for location {location_id}")

        # Cancel in Stripe
        if subscription.get("stripe_subscription_id"):
            try:
                await self.stripe.cancel_subscription(
                    subscription_id=subscription["stripe_subscription_id"],
                    immediately=immediately,
                )
            except PaymentFailedError as e:
                logger.error(f"Failed to cancel subscription in Stripe: {e}")
                raise

        # Update local record
        now = datetime.now(timezone.utc)
        if immediately:
            subscription["status"] = SubscriptionStatus.CANCELED.value
            subscription["canceled_at"] = now
            subscription["cancel_at_period_end"] = False
        else:
            subscription["cancel_at_period_end"] = True
            # Status stays "active" until period end

        subscription["updated_at"] = now
        await self._save_subscription(subscription)

        logger.info(f"Canceled subscription for location {location_id} (immediately={immediately})")
        return subscription

    async def reactivate_subscription(self, location_id: str) -> Dict[str, Any]:
        """
        Reactivate a subscription that was set to cancel at period end.
        """
        subscription = await self._get_subscription_by_location(location_id)
        if not subscription:
            raise ValueError(f"No subscription found for location {location_id}")

        if not subscription.get("cancel_at_period_end"):
            raise ValueError("Subscription is not scheduled for cancellation")

        # Reactivate in Stripe
        if subscription.get("stripe_subscription_id"):
            try:
                await self.stripe.update_subscription(
                    subscription_id=subscription["stripe_subscription_id"],
                    cancel_at_period_end=False,
                )
            except PaymentFailedError as e:
                logger.error(f"Failed to reactivate subscription in Stripe: {e}")
                raise

        # Update local record
        subscription["cancel_at_period_end"] = False
        subscription["updated_at"] = datetime.now(timezone.utc)
        await self._save_subscription(subscription)

        logger.info(f"Reactivated subscription for location {location_id}")
        return subscription

    async def sync_with_stripe(self, location_id: str) -> Dict[str, Any]:
        """
        Synchronize local subscription state with Stripe.

        Call this periodically or after receiving webhooks.
        """
        subscription = await self._get_subscription_by_location(location_id)
        if not subscription:
            raise ValueError(f"No subscription found for location {location_id}")

        if not subscription.get("stripe_subscription_id"):
            logger.warning(f"No Stripe subscription ID for location {location_id}")
            return subscription

        # Fetch latest from Stripe
        try:
            stripe_sub = await self.stripe.get_subscription(subscription["stripe_subscription_id"])
        except PaymentFailedError:
            logger.warning(f"Could not fetch subscription from Stripe for location {location_id}")
            return subscription

        # Update local state
        subscription["status"] = stripe_sub.get("status", subscription["status"])

        if stripe_sub.get("current_period_start"):
            subscription["current_period_start"] = datetime.fromtimestamp(
                stripe_sub["current_period_start"], tz=timezone.utc
            )

        if stripe_sub.get("current_period_end"):
            subscription["current_period_end"] = datetime.fromtimestamp(
                stripe_sub["current_period_end"], tz=timezone.utc
            )

        if stripe_sub.get("trial_end"):
            subscription["trial_end"] = datetime.fromtimestamp(stripe_sub["trial_end"], tz=timezone.utc)

        subscription["cancel_at_period_end"] = stripe_sub.get("cancel_at_period_end", False)
        subscription["updated_at"] = datetime.now(timezone.utc)

        await self._save_subscription(subscription)

        logger.info(f"Synced subscription for location {location_id}")
        return subscription

    async def get_subscription(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get the active subscription for a location."""
        return await self._get_active_subscription(location_id)

    async def get_subscription_details(self, location_id: str) -> Dict[str, Any]:
        """Get detailed subscription info including plan details."""
        subscription = await self.get_subscription(location_id)

        if not subscription:
            return {"has_subscription": False}

        plan_config = get_plan_config(PlanTier(subscription["tier"]))

        usage_allowance = subscription.get("usage_allowance", 100)
        usage_current = subscription.get("usage_current", 0)

        if usage_allowance == -1:  # Unlimited
            remaining = -1
            percentage = 0
        else:
            remaining = max(0, usage_allowance - usage_current)
            percentage = (usage_current / usage_allowance * 100) if usage_allowance > 0 else 0

        return {
            "has_subscription": True,
            "plan_tier": subscription["tier"],
            "plan_name": plan_config.get("name", subscription["tier"]),
            "status": subscription["status"],
            "is_active": subscription["status"]
            in [
                SubscriptionStatus.TRIALING.value,
                SubscriptionStatus.ACTIVE.value,
            ],
            "is_trial": subscription["status"] == SubscriptionStatus.TRIALING.value,
            "billing_interval": subscription.get("billing_interval", "month"),
            "current_period_start": subscription.get("current_period_start"),
            "current_period_end": subscription.get("current_period_end"),
            "trial_end": subscription.get("trial_end"),
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "usage_allowance": usage_allowance,
            "usage_current": usage_current,
            "usage_remaining": remaining,
            "percentage_used": round(percentage, 2),
            "features": plan_config.get("features", {}),
            "limits": plan_config.get("limits", {}),
        }

    async def _get_active_subscription(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get active subscription for a location."""
        if self.db is None:
            # Return mock for testing
            return None

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM subscriptions
                WHERE location_id = $1
                AND status IN ('trialing', 'active', 'past_due')
                ORDER BY created_at DESC
                LIMIT 1
                """,
                location_id,
            )
            return dict(row) if row else None

    async def _get_subscription_by_location(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get any subscription (active or not) for a location."""
        if self.db is None:
            return None

        async with self.db.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT * FROM subscriptions
                WHERE location_id = $1
                ORDER BY created_at DESC
                LIMIT 1
                """,
                location_id,
            )
            return dict(row) if row else None

    async def _save_subscription(self, subscription: Dict[str, Any]) -> None:
        """Save subscription to database."""
        if self.db is None:
            return

        async with self.db.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO subscriptions (
                    id, location_id, stripe_customer_id, stripe_subscription_id,
                    tier, status, billing_interval, current_period_start,
                    current_period_end, usage_allowance, usage_current,
                    trial_end, cancel_at_period_end, created_at, updated_at
                ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15)
                ON CONFLICT (id) DO UPDATE SET
                    tier = EXCLUDED.tier,
                    status = EXCLUDED.status,
                    billing_interval = EXCLUDED.billing_interval,
                    current_period_start = EXCLUDED.current_period_start,
                    current_period_end = EXCLUDED.current_period_end,
                    usage_allowance = EXCLUDED.usage_allowance,
                    usage_current = EXCLUDED.usage_current,
                    trial_end = EXCLUDED.trial_end,
                    cancel_at_period_end = EXCLUDED.cancel_at_period_end,
                    updated_at = EXCLUDED.updated_at
                """,
                subscription["id"],
                subscription["location_id"],
                subscription["stripe_customer_id"],
                subscription.get("stripe_subscription_id"),
                subscription["tier"],
                subscription["status"],
                subscription.get("billing_interval", "month"),
                subscription["current_period_start"],
                subscription["current_period_end"],
                subscription["usage_allowance"],
                subscription["usage_current"],
                subscription.get("trial_end"),
                subscription.get("cancel_at_period_end", False),
                subscription["created_at"],
                subscription["updated_at"],
            )


# Global service instance
_subscription_service: Optional[SubscriptionService] = None


def get_subscription_service(db_connection=None) -> SubscriptionService:
    """Get or create the global subscription service instance."""
    global _subscription_service
    if _subscription_service is None:
        _subscription_service = SubscriptionService(db_connection)
    return _subscription_service


def reset_subscription_service() -> None:
    """Reset the global subscription service (useful for testing)."""
    global _subscription_service
    _subscription_service = None
