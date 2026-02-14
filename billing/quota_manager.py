"""
Quota manager and usage tracker for billing enforcement in EnterpriseHub.

Provides quota checking, usage recording, and enforcement
at multiple layers of the application.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

from billing import ResourceType, SubscriptionStatus, PlanTier, get_plan_config

logger = logging.getLogger(__name__)


class QuotaManager:
    """
    Manages quota checking and enforcement for locations/tenants.
    
    Provides methods to check if locations have quota available
    and to increment usage counters.
    """
    
    def __init__(self, db_connection=None) -> None:
        """
        Initialize quota manager.
        
        Args:
            db_connection: Database connection pool or session factory
        """
        self.db = db_connection
    
    async def check_lead_quota(self, location_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a location has lead quota available.
        
        Args:
            location_id: Location ID
            
        Returns:
            Tuple of (has_quota, error_message)
            - has_quota: True if quota is available, False otherwise
            - error_message: Reason if quota not available, None otherwise
        """
        subscription = await self._get_active_subscription(location_id)
        
        if not subscription:
            return False, "No active subscription found"
        
        status = subscription.get("status")
        if status not in [SubscriptionStatus.TRIALING.value, SubscriptionStatus.ACTIVE.value]:
            return False, f"Subscription is {status}"
        
        usage_allowance = subscription.get("usage_allowance", 100)
        usage_current = subscription.get("usage_current", 0)
        
        # Unlimited quota
        if usage_allowance == -1:
            return True, None
        
        if usage_current >= usage_allowance:
            return False, f"Lead quota exceeded ({usage_allowance} leads per period, {usage_allowance - usage_current} remaining)"
        
        return True, None
    
    async def check_query_quota(self, location_id: str) -> tuple[bool, Optional[str]]:
        """
        Check if a location has query quota available.
        
        Args:
            location_id: Location ID
            
        Returns:
            Tuple of (has_quota, error_message)
        """
        subscription = await self._get_active_subscription(location_id)
        
        if not subscription:
            return False, "No active subscription found"
        
        status = subscription.get("status")
        if status not in [SubscriptionStatus.TRIALING.value, SubscriptionStatus.ACTIVE.value]:
            return False, f"Subscription is {status}"
        
        # Get plan config for query quota
        tier = PlanTier(subscription["tier"])
        plan_config = get_plan_config(tier)
        query_quota = plan_config.get("query_quota", 100)
        
        # Unlimited quota
        if query_quota == -1:
            return True, None
        
        # Get current query usage
        query_usage = await self._get_query_usage(location_id)
        
        if query_usage >= query_quota:
            return False, f"Query quota exceeded ({query_quota} queries per period)"
        
        return True, None
    
    async def check_feature_access(
        self,
        location_id: str,
        feature: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check if a location has access to a specific feature.
        
        Args:
            location_id: Location ID
            feature: Feature name (e.g., "buyer_bot", "cma_reports", "white_label")
            
        Returns:
            Tuple of (has_access, error_message)
        """
        subscription = await self._get_active_subscription(location_id)
        
        if not subscription:
            return False, "No active subscription found"
        
        status = subscription.get("status")
        if status not in [SubscriptionStatus.TRIALING.value, SubscriptionStatus.ACTIVE.value]:
            return False, f"Subscription is {status}"
        
        # Check plan config for feature
        tier = PlanTier(subscription["tier"])
        plan_config = get_plan_config(tier)
        
        if plan_config.get("features", {}).get(feature, False):
            return True, None
        
        return False, f"Feature '{feature}' not available on your plan"
    
    async def get_usage_summary(self, location_id: str) -> Dict[str, Any]:
        """
        Get a summary of current usage and quota for a location.
        
        Returns:
            Dict with quota info, usage stats, and remaining capacity
        """
        subscription = await self._get_active_subscription(location_id)
        
        if not subscription:
            return {
                "has_subscription": False,
                "quota": 0,
                "used": 0,
                "remaining": 0,
                "percentage_used": 0,
            }
        
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
            "status": subscription["status"],
            "is_active": subscription["status"] in [
                SubscriptionStatus.TRIALING.value,
                SubscriptionStatus.ACTIVE.value,
            ],
            "quota": usage_allowance,
            "used": usage_current,
            "remaining": remaining,
            "percentage_used": round(percentage, 2),
            "period_start": subscription.get("current_period_start"),
            "period_end": subscription.get("current_period_end"),
        }
    
    async def _get_active_subscription(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get active subscription for a location."""
        if self.db is None:
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
                location_id
            )
            return dict(row) if row else None
    
    async def _get_query_usage(self, location_id: str) -> int:
        """Get current query usage for a location in this billing period."""
        if self.db is None:
            return 0
        
        async with self.db.acquire() as conn:
            result = await conn.fetchval(
                """
                SELECT COALESCE(SUM(quantity), 0)
                FROM usage_records ur
                JOIN subscriptions s ON ur.subscription_id = s.id
                WHERE s.location_id = $1
                AND ur.resource_type = 'query'
                AND ur.timestamp >= s.current_period_start
                """,
                location_id
            )
            return result or 0


class UsageTracker:
    """
    Tracks usage of billable resources for locations/tenants.
    
    Records detailed usage events and updates subscription counters.
    """
    
    def __init__(self, db_connection=None) -> None:
        """
        Initialize usage tracker.
        
        Args:
            db_connection: Database connection pool or session factory
        """
        self.db = db_connection
    
    async def record_usage(
        self,
        location_id: str,
        resource_type: ResourceType,
        quantity: int = 1,
        lead_id: Optional[str] = None,
        contact_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record usage of a billable resource.
        
        Args:
            location_id: Location ID
            resource_type: Type of resource used
            quantity: Amount used (default 1)
            lead_id: Optional lead ID for context
            contact_id: Optional contact ID for context
            metadata: Optional additional metadata
            
        Returns:
            Created usage record
        """
        subscription = await self._get_active_subscription(location_id)
        
        if self.db is None:
            return {"id": "mock", "location_id": location_id, "resource_type": resource_type.value}
        
        async with self.db.acquire() as conn:
            # Create usage record
            record = await conn.fetchrow(
                """
                INSERT INTO usage_records (
                    subscription_id, lead_id, contact_id, resource_type,
                    quantity, timestamp, billing_period_start, billing_period_end, metadata
                )
                SELECT 
                    s.id, $2, $3, $4, $5, NOW(), s.current_period_start, s.current_period_end, $6
                FROM subscriptions s
                WHERE s.location_id = $1
                AND s.status IN ('trialing', 'active', 'past_due')
                RETURNING *
                """,
                location_id,
                lead_id,
                contact_id,
                resource_type.value,
                quantity,
                metadata or {},
            )
            
            # Update subscription usage counters for leads
            if resource_type == ResourceType.LEAD and record:
                await conn.execute(
                    """
                    UPDATE subscriptions
                    SET usage_current = usage_current + $2,
                        updated_at = NOW()
                    WHERE id = $1
                    """,
                    record["subscription_id"],
                    quantity,
                )
            
            logger.debug(
                f"Recorded usage: {resource_type.value} x{quantity} for location {location_id}"
            )
            
            return dict(record) if record else {}
    
    async def record_lead_processed(
        self,
        location_id: str,
        lead_id: str,
        contact_id: str,
        was_qualified: bool = False,
    ) -> Dict[str, Any]:
        """
        Convenience method to record lead processing.
        
        Args:
            location_id: Location ID
            lead_id: Lead ID
            contact_id: Contact ID
            was_qualified: Whether the lead was qualified
        """
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.LEAD,
            quantity=1,
            lead_id=lead_id,
            contact_id=contact_id,
            metadata={"qualified": was_qualified},
        )
    
    async def record_query(
        self,
        location_id: str,
        query_type: str,
        result_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Convenience method to record a query.
        
        Args:
            location_id: Location ID
            query_type: Type of query (e.g., "property_search", "market_analysis")
            result_count: Number of results returned
        """
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.QUERY,
            quantity=1,
            metadata={"query_type": query_type, "result_count": result_count},
        )
    
    async def record_api_call(
        self,
        location_id: str,
        endpoint: str,
        method: str = "GET",
    ) -> Dict[str, Any]:
        """
        Convenience method to record API call.
        
        Args:
            location_id: Location ID
            endpoint: API endpoint path
            method: HTTP method
        """
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.API_CALL,
            quantity=1,
            metadata={"endpoint": endpoint, "method": method},
        )
    
    async def record_sms_sent(
        self,
        location_id: str,
        contact_id: str,
        message_length: int,
    ) -> Dict[str, Any]:
        """Convenience method to record SMS sent."""
        # Count SMS segments (160 chars per segment)
        segments = (message_length + 159) // 160
        
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.SMS,
            quantity=segments,
            contact_id=contact_id,
            metadata={"message_length": message_length, "segments": segments},
        )
    
    async def record_email_sent(
        self,
        location_id: str,
        contact_id: str,
        email_type: str = "notification",
    ) -> Dict[str, Any]:
        """Convenience method to record email sent."""
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.EMAIL,
            quantity=1,
            contact_id=contact_id,
            metadata={"email_type": email_type},
        )
    
    async def record_report_generated(
        self,
        location_id: str,
        report_type: str,
        contact_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Convenience method to record report generation."""
        return await self.record_usage(
            location_id=location_id,
            resource_type=ResourceType.REPORT,
            quantity=1,
            contact_id=contact_id,
            metadata={"report_type": report_type},
        )
    
    async def get_usage_report(
        self,
        location_id: str,
        start_date: datetime,
        end_date: datetime,
        resource_type: Optional[ResourceType] = None,
    ) -> Dict[str, Any]:
        """
        Generate a usage report for a location over a date range.
        
        Returns:
            Dict with usage statistics and breakdown by resource type
        """
        if self.db is None:
            return {
                "location_id": location_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_records": 0,
                "by_resource_type": {},
            }
        
        async with self.db.acquire() as conn:
            # Build query
            if resource_type:
                rows = await conn.fetch(
                    """
                    SELECT resource_type, quantity, timestamp, metadata
                    FROM usage_records ur
                    JOIN subscriptions s ON ur.subscription_id = s.id
                    WHERE s.location_id = $1
                    AND ur.timestamp >= $2
                    AND ur.timestamp <= $3
                    AND ur.resource_type = $4
                    ORDER BY ur.timestamp DESC
                    """,
                    location_id,
                    start_date,
                    end_date,
                    resource_type.value,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT resource_type, quantity, timestamp, metadata
                    FROM usage_records ur
                    JOIN subscriptions s ON ur.subscription_id = s.id
                    WHERE s.location_id = $1
                    AND ur.timestamp >= $2
                    AND ur.timestamp <= $3
                    ORDER BY ur.timestamp DESC
                    """,
                    location_id,
                    start_date,
                    end_date,
                )
            
            # Aggregate by resource type
            by_type: Dict[str, int] = {}
            
            for row in rows:
                rt = row["resource_type"]
                by_type[rt] = by_type.get(rt, 0) + row["quantity"]
            
            return {
                "location_id": location_id,
                "start_date": start_date,
                "end_date": end_date,
                "total_records": len(rows),
                "by_resource_type": by_type,
            }
    
    async def get_usage_by_day(
        self,
        location_id: str,
        days: int = 30,
        resource_type: Optional[ResourceType] = None,
    ) -> list[Dict[str, Any]]:
        """
        Get daily usage breakdown for the last N days.
        
        Returns:
            List of daily usage stats
        """
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)
        
        if self.db is None:
            return []
        
        async with self.db.acquire() as conn:
            if resource_type:
                rows = await conn.fetch(
                    """
                    SELECT DATE(ur.timestamp) as date, SUM(ur.quantity) as total
                    FROM usage_records ur
                    JOIN subscriptions s ON ur.subscription_id = s.id
                    WHERE s.location_id = $1
                    AND ur.timestamp >= $2
                    AND ur.resource_type = $3
                    GROUP BY DATE(ur.timestamp)
                    ORDER BY DATE(ur.timestamp)
                    """,
                    location_id,
                    start_date,
                    resource_type.value,
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT DATE(ur.timestamp) as date, SUM(ur.quantity) as total
                    FROM usage_records ur
                    JOIN subscriptions s ON ur.subscription_id = s.id
                    WHERE s.location_id = $1
                    AND ur.timestamp >= $2
                    GROUP BY DATE(ur.timestamp)
                    ORDER BY DATE(ur.timestamp)
                    """,
                    location_id,
                    start_date,
                )
            
            return [
                {
                    "date": str(row["date"]),
                    "total": row["total"] or 0,
                }
                for row in rows
            ]
    
    async def reset_quotas(self) -> int:
        """
        Reset lead usage counters for all subscriptions at period start.
        
        This should be called by a scheduled job at the start of each billing period.
        
        Returns:
            Number of subscriptions reset
        """
        if self.db is None:
            return 0
        
        async with self.db.acquire() as conn:
            result = await conn.execute(
                """
                UPDATE subscriptions
                SET usage_current = 0,
                    updated_at = NOW()
                WHERE status IN ('trialing', 'active', 'past_due')
                AND current_period_start <= NOW()
                """
            )
            
            count = int(result.split()[-1]) if result else 0
            logger.info(f"Reset quotas for {count} subscriptions")
            return count
    
    async def _get_active_subscription(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Get active subscription for a location."""
        if self.db is None:
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
                location_id
            )
            return dict(row) if row else None


# Global instances
_quota_manager: Optional[QuotaManager] = None
_usage_tracker: Optional[UsageTracker] = None


def get_quota_manager(db_connection=None) -> QuotaManager:
    """Get or create the global quota manager instance."""
    global _quota_manager
    if _quota_manager is None:
        _quota_manager = QuotaManager(db_connection)
    return _quota_manager


def get_usage_tracker(db_connection=None) -> UsageTracker:
    """Get or create the global usage tracker instance."""
    global _usage_tracker
    if _usage_tracker is None:
        _usage_tracker = UsageTracker(db_connection)
    return _usage_tracker


def reset_quota_managers() -> None:
    """Reset global instances (useful for testing)."""
    global _quota_manager, _usage_tracker
    _quota_manager = None
    _usage_tracker = None
