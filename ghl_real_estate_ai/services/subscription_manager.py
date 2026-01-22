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

            # Store subscription in database
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
                "usage_current": 0,
                "overage_rate": tier_config.overage_rate,
                "base_price": tier_config.price_monthly,
                "currency": request.currency,
                "trial_end": datetime.fromtimestamp(
                    stripe_subscription.trial_end, tz=timezone.utc
                ) if stripe_subscription.trial_end else None,
                "cancel_at_period_end": stripe_subscription.cancel_at_period_end or False
            }

            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            # Insert subscription into database
            async with db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO subscriptions (
                        location_id, stripe_subscription_id, stripe_customer_id,
                        tier, status, current_period_start, current_period_end,
                        usage_allowance, usage_current, overage_rate, base_price,
                        currency, trial_end, cancel_at_period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
                    ON CONFLICT (location_id) DO UPDATE SET
                        stripe_subscription_id = EXCLUDED.stripe_subscription_id,
                        status = EXCLUDED.status,
                        current_period_start = EXCLUDED.current_period_start,
                        current_period_end = EXCLUDED.current_period_end,
                        tier = EXCLUDED.tier,
                        usage_allowance = EXCLUDED.usage_allowance,
                        currency = EXCLUDED.currency
                """, 
                    subscription_data["location_id"],
                    subscription_data["stripe_subscription_id"],
                    subscription_data["stripe_customer_id"],
                    subscription_data["tier"],
                    subscription_data["status"],
                    subscription_data["current_period_start"],
                    subscription_data["current_period_end"],
                    subscription_data["usage_allowance"],
                    subscription_data["usage_current"],
                    subscription_data["overage_rate"],
                    subscription_data["base_price"],
                    subscription_data["currency"],
                    subscription_data["trial_end"],
                    subscription_data["cancel_at_period_end"]
                )

                # Store customer mapping
                await conn.execute("""
                    INSERT INTO stripe_customers (location_id, stripe_customer_id, email, name)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (location_id) DO UPDATE SET
                        stripe_customer_id = EXCLUDED.stripe_customer_id,
                        email = EXCLUDED.email,
                        name = EXCLUDED.name
                """, request.location_id, stripe_subscription.customer, request.email, request.name)

            logger.info(f"Successfully initialized subscription {stripe_subscription.id}")

            # Get the inserted record to return correct ID
            async with db.get_connection() as conn:
                db_id = await conn.fetchval("SELECT id FROM subscriptions WHERE location_id = $1", request.location_id)

            return SubscriptionResponse(
                id=db_id,
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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            async with db.get_connection() as conn:
                row = await conn.fetchrow("""
                    SELECT * FROM subscriptions 
                    WHERE location_id = $1 AND status = 'active'
                """, location_id)

            if row:
                sub_data = dict(row)
                usage_percentage = (sub_data['usage_current'] / sub_data['usage_allowance']) * 100 if sub_data['usage_allowance'] > 0 else 0
                return SubscriptionResponse(
                    **sub_data,
                    usage_percentage=round(usage_percentage, 2),
                    next_invoice_date=sub_data['current_period_end']
                )
            
            logger.info(f"No active subscription found for location {location_id}")
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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            # Get current subscription from database
            async with db.get_connection() as conn:
                current_row = await conn.fetchrow("SELECT * FROM subscriptions WHERE id = $1", subscription_id)
            
            if not current_row:
                raise SubscriptionManagerError(f"Subscription {subscription_id} not found")
            
            current_sub = dict(current_row)
            logger.info(f"Changing subscription {subscription_id} to tier {new_tier}")

            # Get new tier configuration
            new_tier_config = SUBSCRIPTION_TIERS[new_tier]

            # Modify subscription in Stripe
            modify_request = ModifySubscriptionRequest(
                tier=new_tier,
                currency=current_sub.get('currency', 'usd')
            )
            stripe_subscription = await self.billing_service.modify_subscription(
                current_sub['stripe_subscription_id'],
                modify_request
            )

            # Reset usage allowance for new tier
            usage_reset_data = {
                "tier": new_tier.value,
                "usage_allowance": new_tier_config.usage_allowance,
                "overage_rate": new_tier_config.overage_rate,
                "base_price": new_tier_config.price_monthly,
                "currency": current_sub.get('currency', 'usd'),
                "current_period_start": datetime.fromtimestamp(stripe_subscription.current_period_start, tz=timezone.utc),
                "current_period_end": datetime.fromtimestamp(stripe_subscription.current_period_end, tz=timezone.utc),
                "status": stripe_subscription.status
            }

            # Update database
            async with db.get_connection() as conn:
                await conn.execute("""
                    UPDATE subscriptions SET
                        tier = $1, usage_allowance = $2, overage_rate = $3,
                        base_price = $4, current_period_start = $5, current_period_end = $6,
                        status = $7, currency = $8, updated_at = NOW()
                    WHERE id = $9
                """, 
                    usage_reset_data["tier"],
                    usage_reset_data["usage_allowance"],
                    usage_reset_data["overage_rate"],
                    usage_reset_data["base_price"],
                    usage_reset_data["current_period_start"],
                    usage_reset_data["current_period_end"],
                    usage_reset_data["status"],
                    usage_reset_data["currency"],
                    subscription_id
                )

            logger.info(f"Successfully changed subscription {subscription_id} to {new_tier}")

            return SubscriptionResponse(
                id=subscription_id,
                location_id=current_sub['location_id'],
                stripe_subscription_id=stripe_subscription.id,
                stripe_customer_id=stripe_subscription.customer,
                tier=new_tier,
                status=SubscriptionStatus(stripe_subscription.status),
                currency=usage_reset_data["currency"],
                current_period_start=usage_reset_data["current_period_start"],
                current_period_end=usage_reset_data["current_period_end"],
                **usage_reset_data,
                usage_current=current_sub['usage_current'],
                usage_percentage=0.0,  # Will be calculated by client
                trial_end=None,
                cancel_at_period_end=stripe_subscription.cancel_at_period_end or False,
                next_invoice_date=usage_reset_data["current_period_end"],
                created_at=current_sub['created_at']
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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            async with db.get_connection() as conn:
                overage_rate = await conn.fetchval("SELECT overage_rate FROM subscriptions WHERE id = $1", subscription_id)

            if overage_rate is None:
                overage_rate = SUBSCRIPTION_TIERS[SubscriptionTier.PROFESSIONAL].overage_rate

            total_overage_cost = Decimal(str(overage_rate)) * Decimal(overage_count)

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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            # Get subscription billing period from database
            async with db.get_connection() as conn:
                sub_row = await conn.fetchrow("""
                    SELECT current_period_start, current_period_end 
                    FROM subscriptions WHERE id = $1
                """, subscription_id)
            
            if not sub_row:
                raise SubscriptionManagerError(f"Subscription {subscription_id} not found")

            period_start = sub_row['current_period_start']
            period_end = sub_row['current_period_end']

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

            # Store usage record in database
            async with db.get_connection() as conn:
                await conn.execute("""
                    INSERT INTO usage_records (
                        subscription_id, stripe_usage_record_id, lead_id, contact_id,
                        quantity, amount, tier, billing_period_start, billing_period_end
                    ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
                """, 
                    subscription_id, stripe_usage_record.id, lead_id, contact_id,
                    1, lead_price, tier, period_start, period_end
                )
                
                # Increment current usage count
                await conn.execute("UPDATE subscriptions SET usage_current = usage_current + 1 WHERE id = $1", subscription_id)

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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            async with db.get_connection() as conn:
                subscription = await conn.fetchrow("SELECT * FROM subscriptions WHERE location_id = $1 AND status = 'active'", location_id)
                if not subscription:
                    return None

                sub_data = dict(subscription)
                
                # Count usage by tier from usage_records
                tier_counts_rows = await conn.fetch("""
                    SELECT tier, COUNT(*) as count 
                    FROM usage_records 
                    WHERE subscription_id = $1 
                      AND billing_period_start = $2
                    GROUP BY tier
                """, sub_data['id'], sub_data['current_period_start'])
                
                usage_by_tier = {row['tier']: row['count'] for row in tier_counts_rows}

            usage_allowance = sub_data['usage_allowance']
            usage_current = sub_data['usage_current']
            usage_remaining = max(0, usage_allowance - usage_current)
            overage_count = max(0, usage_current - usage_allowance)

            base_cost = sub_data['base_price']
            overage_rate = sub_data['overage_rate']
            overage_cost = overage_rate * Decimal(overage_count)
            total_cost = base_cost + overage_cost

            return UsageSummary(
                subscription_id=sub_data['id'],
                period_start=sub_data['current_period_start'],
                period_end=sub_data['current_period_end'],
                usage_allowance=usage_allowance,
                usage_current=usage_current,
                usage_remaining=usage_remaining,
                overage_count=overage_count,
                base_cost=base_cost,
                overage_cost=overage_cost,
                total_cost=total_cost,
                usage_by_tier=usage_by_tier
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
            from ghl_real_estate_ai.services.database_service import get_database
            db = await get_database()
            
            async with db.get_connection() as conn:
                rows = await conn.fetch("""
                    SELECT tier, COUNT(*) as count 
                    FROM subscriptions 
                    WHERE status = 'active'
                    GROUP BY tier
                """)
            
            tier_counts = {row['tier']: row['count'] for row in rows}
            
            starter_count = tier_counts.get(SubscriptionTier.STARTER.value, 0)
            professional_count = tier_counts.get(SubscriptionTier.PROFESSIONAL.value, 0)
            enterprise_count = tier_counts.get(SubscriptionTier.ENTERPRISE.value, 0)
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