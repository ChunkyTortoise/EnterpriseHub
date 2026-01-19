"""
Subscription Manager Service

High-level subscription management service that orchestrates billing operations,
usage tracking, and integrates with the DynamicPricingOptimizer for usage-based billing.
"""

from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Optional, Dict, List, Any
import asyncio

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.billing_service import BillingService, BillingServiceError
from ghl_real_estate_ai.api.schemas.billing import (
    SubscriptionTier,
    SubscriptionStatus,
    SUBSCRIPTION_TIERS,
    CreateSubscriptionRequest,
    ModifySubscriptionRequest,
    SubscriptionResponse,
    UsageRecordRequest,
    UsageSummary,
    TierDistribution
)

logger = get_logger(__name__)


class SubscriptionManagerError(Exception):
    """Exception for subscription management errors."""
    pass


class SubscriptionManager:
    """
    High-level subscription management service.

    Orchestrates subscription lifecycle, usage monitoring, and billing
    integration with dynamic pricing optimization.
    """

    def __init__(self):
        """Initialize subscription manager with billing service."""
        self.billing_service = BillingService()
        logger.info("SubscriptionManager initialized")


    # ===================================================================
    # Subscription Lifecycle
    # ===================================================================

    async def initialize_subscription(self, request: CreateSubscriptionRequest) -> SubscriptionResponse:
        """
        Initialize a new subscription with complete setup workflow.

        Args:
            request: Subscription creation request

        Returns:
            Complete subscription response with status and configuration

        Raises:
            SubscriptionManagerError: If initialization fails
        """
        try:
            logger.info(f"Initializing subscription for location {request.location_id}, tier {request.tier}")

            # Create subscription in Stripe
            stripe_subscription = await self.billing_service.create_subscription(request)

            # Get tier configuration
            tier_config = SUBSCRIPTION_TIERS[request.tier]

            # Store subscription in database (database operations would go here)
            subscription_data = {
                "location_id": request.location_id,
                "stripe_subscription_id": stripe_subscription.id,
                "stripe_customer_id": stripe_subscription.customer,
                "tier": request.tier.value,
                "status": stripe_subscription.status,
                "current_period_start": datetime.fromtimestamp(
                    stripe_subscription.current_period_start, tz=timezone.utc
                ),
                "current_period_end": datetime.fromtimestamp(
                    stripe_subscription.current_period_end, tz=timezone.utc
                ),
                "usage_allowance": tier_config.usage_allowance,
                "usage_current": 0,  # Start with 0 usage
                "overage_rate": tier_config.overage_rate,
                "base_price": tier_config.price_monthly,
                "trial_end": datetime.fromtimestamp(
                    stripe_subscription.trial_end, tz=timezone.utc
                ) if stripe_subscription.trial_end else None,
                "cancel_at_period_end": stripe_subscription.cancel_at_period_end or False
            }

            # TODO: Insert into database
            # await db.subscriptions.insert(subscription_data)

            # TODO: Store customer mapping
            # await db.stripe_customers.insert({
            #     "location_id": request.location_id,
            #     "stripe_customer_id": stripe_subscription.customer,
            #     "email": request.email,
            #     "name": request.name
            # })

            logger.info(f"Successfully initialized subscription {stripe_subscription.id}")

            return SubscriptionResponse(
                id=1,  # TODO: Get from database
                **subscription_data,
                usage_percentage=0.0,
                next_invoice_date=datetime.fromtimestamp(
                    stripe_subscription.current_period_end, tz=timezone.utc
                ),
                created_at=datetime.now(timezone.utc)
            )

        except BillingServiceError as e:
            logger.error(f"Billing service error during subscription initialization: {e}")
            raise SubscriptionManagerError(f"Subscription initialization failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error during subscription initialization: {e}")
            raise SubscriptionManagerError(f"Subscription initialization failed: {str(e)}")


    async def get_active_subscription(self, location_id: str) -> Optional[SubscriptionResponse]:
        """
        Get active subscription for a location.

        Args:
            location_id: GHL location ID

        Returns:
            Active subscription or None if no active subscription
        """
        try:
            # TODO: Query database for active subscription
            # subscription_record = await db.subscriptions.filter(
            #     location_id=location_id,
            #     status="active"
            # ).first()

            # For now, return None (no database integration yet)
            logger.info(f"Queried active subscription for location {location_id}")
            return None

        except Exception as e:
            logger.error(f"Error retrieving active subscription for {location_id}: {e}")
            return None


    async def handle_tier_change(self, subscription_id: int, new_tier: SubscriptionTier,
                               immediate: bool = True) -> SubscriptionResponse:
        """
        Handle subscription tier upgrade or downgrade.

        Args:
            subscription_id: Database subscription ID
            new_tier: Target subscription tier
            immediate: If True, change immediately with proration

        Returns:
            Updated subscription details

        Raises:
            SubscriptionManagerError: If tier change fails
        """
        try:
            # TODO: Get current subscription from database
            # current_subscription = await db.subscriptions.get(id=subscription_id)

            logger.info(f"Changing subscription {subscription_id} to tier {new_tier}")

            # Get new tier configuration
            new_tier_config = SUBSCRIPTION_TIERS[new_tier]

            # Modify subscription in Stripe
            modify_request = ModifySubscriptionRequest(tier=new_tier)
            stripe_subscription = await self.billing_service.modify_subscription(
                "subscription_id_placeholder",  # TODO: Use actual Stripe ID
                modify_request
            )

            # Calculate proration and update database
            period_start = datetime.fromtimestamp(
                stripe_subscription.current_period_start, tz=timezone.utc
            )
            period_end = datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=timezone.utc
            )

            # Reset usage allowance for new tier
            usage_reset_data = {
                "tier": new_tier.value,
                "usage_allowance": new_tier_config.usage_allowance,
                "overage_rate": new_tier_config.overage_rate,
                "base_price": new_tier_config.price_monthly,
                # Keep current usage unless it's a period reset
            }

            # TODO: Update database
            # await db.subscriptions.update(subscription_id, usage_reset_data)

            logger.info(f"Successfully changed subscription {subscription_id} to {new_tier}")

            return SubscriptionResponse(
                id=subscription_id,
                location_id="placeholder",  # TODO: Get from database
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_subscription.customer,
                tier=new_tier,
                status=SubscriptionStatus(stripe_subscription.status),
                current_period_start=period_start,
                current_period_end=period_end,
                **usage_reset_data,
                usage_current=0,  # TODO: Get from database
                usage_percentage=0.0,  # Will be calculated
                trial_end=None,
                cancel_at_period_end=stripe_subscription.cancel_at_period_end or False,
                next_invoice_date=period_end,
                created_at=datetime.now(timezone.utc)
            )

        except BillingServiceError as e:
            logger.error(f"Billing error during tier change: {e}")
            raise SubscriptionManagerError(f"Tier change failed: {e.message}")
        except Exception as e:
            logger.error(f"Unexpected error during tier change: {e}")
            raise SubscriptionManagerError(f"Tier change failed: {str(e)}")


    # ===================================================================
    # Usage Monitoring & Billing
    # ===================================================================

    async def handle_usage_threshold(self, location_id: str, current_usage: int,
                                   period_usage_allowance: int) -> Dict[str, Any]:
        """
        Monitor usage thresholds and trigger alerts/actions.

        Args:
            location_id: GHL location ID
            current_usage: Current period usage count
            period_usage_allowance: Usage allowance for current tier

        Returns:
            Threshold status and actions taken
        """
        try:
            usage_percentage = (current_usage / period_usage_allowance) * 100 if period_usage_allowance > 0 else 0

            # Define threshold levels
            thresholds = {
                "warning": 75,    # 75% usage warning
                "critical": 90,   # 90% usage alert
                "overage": 100    # Usage overage
            }

            actions_taken = []

            if usage_percentage >= thresholds["overage"]:
                # Usage overage - start billing overages
                overage_count = current_usage - period_usage_allowance
                actions_taken.append(f"overage_billing_active_{overage_count}_leads")

            elif usage_percentage >= thresholds["critical"]:
                # Critical threshold - alert customer and admin
                actions_taken.append("critical_usage_alert_sent")

            elif usage_percentage >= thresholds["warning"]:
                # Warning threshold - notify customer
                actions_taken.append("usage_warning_sent")

            # Log threshold status
            logger.info(
                f"Usage threshold check for {location_id}: "
                f"{current_usage}/{period_usage_allowance} ({usage_percentage:.1f}%) - "
                f"Actions: {actions_taken}"
            )

            return {
                "location_id": location_id,
                "usage_current": current_usage,
                "usage_allowance": period_usage_allowance,
                "usage_percentage": round(usage_percentage, 2),
                "threshold_level": self._get_threshold_level(usage_percentage, thresholds),
                "actions_taken": actions_taken,
                "overage_billing_active": usage_percentage >= thresholds["overage"]
            }

        except Exception as e:
            logger.error(f"Error in usage threshold handling for {location_id}: {e}")
            return {
                "location_id": location_id,
                "error": str(e),
                "actions_taken": []
            }


    def _get_threshold_level(self, usage_percentage: float, thresholds: Dict[str, float]) -> str:
        """Determine current threshold level based on usage percentage."""
        if usage_percentage >= thresholds["overage"]:
            return "overage"
        elif usage_percentage >= thresholds["critical"]:
            return "critical"
        elif usage_percentage >= thresholds["warning"]:
            return "warning"
        else:
            return "normal"


    async def calculate_overage_cost(self, subscription_id: int, overage_count: int) -> Decimal:
        """
        Calculate cost for usage overage.

        Args:
            subscription_id: Database subscription ID
            overage_count: Number of leads over allowance

        Returns:
            Total overage cost
        """
        try:
            # TODO: Get subscription details from database
            # subscription = await db.subscriptions.get(id=subscription_id)
            # overage_rate = subscription.overage_rate

            # Placeholder overage rate (from Professional tier)
            overage_rate = SUBSCRIPTION_TIERS[SubscriptionTier.PROFESSIONAL].overage_rate

            total_overage_cost = overage_rate * Decimal(overage_count)

            logger.info(
                f"Calculated overage cost for subscription {subscription_id}: "
                f"{overage_count} leads × ${overage_rate} = ${total_overage_cost}"
            )

            return total_overage_cost

        except Exception as e:
            logger.error(f"Error calculating overage cost: {e}")
            return Decimal("0.00")


    async def bill_usage_overage(self, subscription_id: int, lead_id: str, contact_id: str,
                               lead_price: Decimal, tier: str) -> Dict[str, Any]:
        """
        Bill for usage overage when customer exceeds their allowance.

        Args:
            subscription_id: Database subscription ID
            lead_id: GHL lead ID
            contact_id: GHL contact ID
            lead_price: Calculated lead price from DynamicPricingOptimizer
            tier: Lead quality tier (hot/warm/cold)

        Returns:
            Billing result with usage record details
        """
        try:
            # TODO: Get subscription billing period from database
            period_start = datetime.now(timezone.utc).replace(day=1)  # Placeholder
            period_end = period_start + timedelta(days=32)
            period_end = period_end.replace(day=1) - timedelta(days=1)  # Last day of month

            # Create usage record request
            usage_request = UsageRecordRequest(
                subscription_id=subscription_id,
                lead_id=lead_id,
                contact_id=contact_id,
                amount=lead_price,
                tier=tier,
                billing_period_start=period_start,
                billing_period_end=period_end
            )

            # Record usage with Stripe
            stripe_usage_record = await self.billing_service.add_usage_record(usage_request)

            # TODO: Store usage record in database
            # await db.usage_records.insert({
            #     "subscription_id": subscription_id,
            #     "stripe_usage_record_id": stripe_usage_record.id,
            #     "lead_id": lead_id,
            #     "contact_id": contact_id,
            #     "quantity": 1,
            #     "amount": lead_price,
            #     "tier": tier,
            #     "billing_period_start": period_start,
            #     "billing_period_end": period_end
            # })

            logger.info(
                f"Billed overage for subscription {subscription_id}: "
                f"Lead {lead_id}, ${lead_price} ({tier} tier)"
            )

            return {
                "success": True,
                "stripe_usage_record_id": stripe_usage_record.id,
                "amount_billed": lead_price,
                "tier": tier,
                "billing_period": f"{period_start.date()} to {period_end.date()}"
            }

        except BillingServiceError as e:
            logger.error(f"Billing service error during overage billing: {e}")
            return {
                "success": False,
                "error": e.message,
                "recoverable": e.recoverable
            }
        except Exception as e:
            logger.error(f"Unexpected error during overage billing: {e}")
            return {
                "success": False,
                "error": str(e),
                "recoverable": True
            }


    # ===================================================================
    # Analytics & Reporting
    # ===================================================================

    async def get_usage_summary(self, location_id: str) -> Optional[UsageSummary]:
        """
        Get current period usage summary for a location.

        Args:
            location_id: GHL location ID

        Returns:
            Usage summary with current period statistics
        """
        try:
            # TODO: Get subscription and usage data from database
            # subscription = await db.subscriptions.filter(location_id=location_id, status="active").first()
            # if not subscription:
            #     return None

            # current_period_start = subscription.current_period_start
            # current_period_end = subscription.current_period_end

            # usage_records = await db.usage_records.filter(
            #     subscription_id=subscription.id,
            #     billing_period_start__lte=current_period_start,
            #     billing_period_end__gte=current_period_end
            # ).all()

            # Placeholder data
            usage_allowance = 150  # Professional tier
            usage_current = 87
            usage_remaining = max(0, usage_allowance - usage_current)
            overage_count = max(0, usage_current - usage_allowance)

            base_cost = SUBSCRIPTION_TIERS[SubscriptionTier.PROFESSIONAL].price_monthly
            overage_rate = SUBSCRIPTION_TIERS[SubscriptionTier.PROFESSIONAL].overage_rate
            overage_cost = overage_rate * Decimal(overage_count)
            total_cost = base_cost + overage_cost

            return UsageSummary(
                subscription_id=1,  # Placeholder
                period_start=datetime.now(timezone.utc).replace(day=1),
                period_end=datetime.now(timezone.utc).replace(day=1) + timedelta(days=32),
                usage_allowance=usage_allowance,
                usage_current=usage_current,
                usage_remaining=usage_remaining,
                overage_count=overage_count,
                base_cost=base_cost,
                overage_cost=overage_cost,
                total_cost=total_cost,
                usage_by_tier={
                    "hot": 24,
                    "warm": 38,
                    "cold": 25
                }
            )

        except Exception as e:
            logger.error(f"Error getting usage summary for {location_id}: {e}")
            return None


    async def get_tier_distribution(self) -> TierDistribution:
        """
        Get subscription tier distribution analytics.

        Returns:
            Tier distribution with counts and percentages
        """
        try:
            # TODO: Query database for actual tier distribution
            # tier_counts = await db.subscriptions.group_by('tier').count()

            # Placeholder data
            starter_count = 12
            professional_count = 23
            enterprise_count = 8
            total_subscriptions = starter_count + professional_count + enterprise_count

            if total_subscriptions > 0:
                starter_percentage = round((starter_count / total_subscriptions) * 100, 1)
                professional_percentage = round((professional_count / total_subscriptions) * 100, 1)
                enterprise_percentage = round((enterprise_count / total_subscriptions) * 100, 1)
            else:
                starter_percentage = professional_percentage = enterprise_percentage = 0.0

            return TierDistribution(
                starter_count=starter_count,
                professional_count=professional_count,
                enterprise_count=enterprise_count,
                starter_percentage=starter_percentage,
                professional_percentage=professional_percentage,
                enterprise_percentage=enterprise_percentage,
                total_subscriptions=total_subscriptions
            )

        except Exception as e:
            logger.error(f"Error getting tier distribution: {e}")
            return TierDistribution()  # Return empty distribution


    # ===================================================================
    # Subscription Health & Monitoring
    # ===================================================================

    async def check_subscription_health(self, location_id: str) -> Dict[str, Any]:
        """
        Perform health check on a subscription.

        Args:
            location_id: GHL location ID

        Returns:
            Health check results with status and recommendations
        """
        try:
            subscription = await self.get_active_subscription(location_id)

            if not subscription:
                return {
                    "location_id": location_id,
                    "status": "no_subscription",
                    "healthy": False,
                    "recommendations": ["Consider subscribing to enable advanced features"]
                }

            health_issues = []
            recommendations = []

            # Check subscription status
            if subscription.status != SubscriptionStatus.ACTIVE:
                health_issues.append(f"Subscription status is {subscription.status}")
                recommendations.append("Resolve payment issues to reactivate subscription")

            # Check usage patterns
            if subscription.usage_percentage > 90:
                health_issues.append("High usage detected (>90% of allowance)")
                recommendations.append("Consider upgrading tier to avoid overage charges")

            # Check upcoming renewal
            days_to_renewal = (subscription.next_invoice_date - datetime.now(timezone.utc)).days
            if days_to_renewal <= 3:
                recommendations.append("Subscription renewal approaching")

            return {
                "location_id": location_id,
                "subscription_id": subscription.id,
                "status": "healthy" if not health_issues else "issues_detected",
                "healthy": len(health_issues) == 0,
                "health_issues": health_issues,
                "recommendations": recommendations,
                "usage_percentage": subscription.usage_percentage,
                "days_to_renewal": days_to_renewal
            }

        except Exception as e:
            logger.error(f"Error checking subscription health for {location_id}: {e}")
            return {
                "location_id": location_id,
                "status": "health_check_failed",
                "healthy": False,
                "error": str(e)
            }