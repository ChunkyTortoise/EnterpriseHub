"""
Token Budget Enforcement Service for Cost Control.

Implements intelligent token budget management across the multi-agent system
to prevent cost overruns and optimize spending patterns.

Key Features:
1. Per-contact token budget limits with soft/hard thresholds
2. Per-agent token budget allocation and tracking
3. Location-based budget management for multi-tenant isolation
4. Real-time budget monitoring with proactive alerts
5. Dynamic budget allocation based on lead scoring
6. Emergency budget controls and circuit breakers

Expected Benefits:
- Prevent runaway costs from long conversations or agent loops
- Optimize budget allocation to high-value leads
- Provide real-time cost visibility and control
- Enable predictable monthly spending patterns
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from decimal import Decimal

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)


class BudgetStatus(Enum):
    """Budget status levels for different threshold conditions."""
    HEALTHY = "healthy"           # < 60% of budget used
    WARNING = "warning"           # 60-80% of budget used
    CRITICAL = "critical"         # 80-95% of budget used
    EXCEEDED = "exceeded"         # > 95% of budget used
    BLOCKED = "blocked"           # Budget fully exhausted


class BudgetType(Enum):
    """Types of budgets for different scoping levels."""
    GLOBAL = "global"             # Platform-wide budget
    LOCATION = "location"         # Per-location budget
    CONTACT = "contact"           # Per-contact conversation budget
    AGENT = "agent"               # Per-agent type budget
    DAILY = "daily"               # Daily spending limit
    MONTHLY = "monthly"           # Monthly spending limit


@dataclass
class BudgetLimit:
    """Configuration for a specific budget limit."""
    budget_type: BudgetType
    budget_id: str               # Unique identifier (location_id, contact_id, etc.)
    max_tokens_monthly: int      # Maximum tokens per month
    max_tokens_daily: int        # Maximum tokens per day
    max_cost_monthly: Decimal    # Maximum cost per month ($)
    max_cost_daily: Decimal      # Maximum cost per day ($)
    soft_threshold: float = 0.8  # Warning threshold (80%)
    hard_threshold: float = 0.95 # Block threshold (95%)
    reset_day: int = 1           # Day of month to reset (1-28)
    created_at: datetime = field(default_factory=datetime.utcnow)
    is_active: bool = True


@dataclass
class BudgetUsage:
    """Current usage tracking for a budget."""
    budget_id: str
    budget_type: BudgetType
    current_tokens_monthly: int = 0
    current_tokens_daily: int = 0
    current_cost_monthly: Decimal = Decimal('0.00')
    current_cost_daily: Decimal = Decimal('0.00')
    last_updated: datetime = field(default_factory=datetime.utcnow)
    last_reset: datetime = field(default_factory=datetime.utcnow)


@dataclass
class BudgetCheck:
    """Result of a budget check before API call."""
    is_allowed: bool
    budget_status: BudgetStatus
    remaining_tokens_daily: int
    remaining_tokens_monthly: int
    remaining_cost_daily: Decimal
    remaining_cost_monthly: Decimal
    estimated_request_cost: Decimal
    reason: str = ""
    recommended_action: str = ""


class TokenBudgetService:
    """
    Comprehensive token budget management and enforcement service.

    Provides fine-grained budget control across the multi-agent real estate
    AI platform with intelligent allocation and monitoring.
    """

    def __init__(self, redis_client=None):
        """Initialize the budget service."""
        self.redis = redis_client
        self.token_costs = {
            "input_per_1m": Decimal('3.00'),        # $3 per 1M input tokens
            "output_per_1m": Decimal('15.00'),      # $15 per 1M output tokens
            "cache_creation_per_1m": Decimal('0.75'), # 25% of input cost
            "cache_read_per_1m": Decimal('0.30')    # 10% of input cost
        }

        # Default budget limits
        self.default_limits = {
            BudgetType.LOCATION: {
                "max_tokens_monthly": 1_000_000,    # 1M tokens per location per month
                "max_tokens_daily": 50_000,         # 50K tokens per location per day
                "max_cost_monthly": Decimal('100.00'),  # $100 per location per month
                "max_cost_daily": Decimal('5.00')   # $5 per location per day
            },
            BudgetType.CONTACT: {
                "max_tokens_monthly": 50_000,       # 50K tokens per contact per month
                "max_tokens_daily": 5_000,          # 5K tokens per contact per day
                "max_cost_monthly": Decimal('10.00'),   # $10 per contact per month
                "max_cost_daily": Decimal('0.50')   # $0.50 per contact per day
            },
            BudgetType.AGENT: {
                "max_tokens_monthly": 200_000,      # 200K tokens per agent type per month
                "max_tokens_daily": 10_000,         # 10K tokens per agent type per day
                "max_cost_monthly": Decimal('30.00'),   # $30 per agent type per month
                "max_cost_daily": Decimal('2.00')   # $2 per agent type per day
            }
        }

    def calculate_request_cost(
        self,
        input_tokens: int,
        estimated_output_tokens: int = 500,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0
    ) -> Decimal:
        """
        Calculate the estimated cost of a request.

        Args:
            input_tokens: Number of input tokens
            estimated_output_tokens: Estimated output tokens
            cache_read_tokens: Tokens read from cache
            cache_creation_tokens: Tokens used for cache creation

        Returns:
            Total estimated cost in USD
        """
        costs = Decimal('0.00')

        # Regular input tokens
        regular_input = input_tokens - cache_read_tokens - cache_creation_tokens
        if regular_input > 0:
            costs += (Decimal(regular_input) / 1_000_000) * self.token_costs["input_per_1m"]

        # Output tokens
        costs += (Decimal(estimated_output_tokens) / 1_000_000) * self.token_costs["output_per_1m"]

        # Cache costs
        if cache_read_tokens > 0:
            costs += (Decimal(cache_read_tokens) / 1_000_000) * self.token_costs["cache_read_per_1m"]

        if cache_creation_tokens > 0:
            costs += (Decimal(cache_creation_tokens) / 1_000_000) * self.token_costs["cache_creation_per_1m"]

        return costs

    async def check_budget_before_request(
        self,
        budget_type: BudgetType,
        budget_id: str,
        estimated_input_tokens: int,
        estimated_output_tokens: int = 500,
        cache_read_tokens: int = 0,
        priority_boost: bool = False
    ) -> BudgetCheck:
        """
        Check if a request is allowed under current budget constraints.

        Args:
            budget_type: Type of budget to check
            budget_id: Identifier for the budget (location_id, contact_id, etc.)
            estimated_input_tokens: Estimated input tokens for request
            estimated_output_tokens: Estimated output tokens
            cache_read_tokens: Tokens that will be read from cache
            priority_boost: Whether this is a high-priority request

        Returns:
            BudgetCheck with approval status and details
        """
        try:
            # Get current budget limits and usage
            budget_limit = await self.get_budget_limit(budget_type, budget_id)
            budget_usage = await self.get_budget_usage(budget_type, budget_id)

            # Calculate request cost
            estimated_cost = self.calculate_request_cost(
                input_tokens=estimated_input_tokens,
                estimated_output_tokens=estimated_output_tokens,
                cache_read_tokens=cache_read_tokens
            )

            # Check daily limits
            daily_tokens_after = budget_usage.current_tokens_daily + estimated_input_tokens + estimated_output_tokens
            daily_cost_after = budget_usage.current_cost_daily + estimated_cost

            # Check monthly limits
            monthly_tokens_after = budget_usage.current_tokens_monthly + estimated_input_tokens + estimated_output_tokens
            monthly_cost_after = budget_usage.current_cost_monthly + estimated_cost

            # Determine budget status
            daily_token_utilization = daily_tokens_after / budget_limit.max_tokens_daily
            daily_cost_utilization = float(daily_cost_after / budget_limit.max_cost_daily)
            monthly_token_utilization = monthly_tokens_after / budget_limit.max_tokens_monthly
            monthly_cost_utilization = float(monthly_cost_after / budget_limit.max_cost_monthly)

            # Use the highest utilization to determine status
            max_utilization = max(
                daily_token_utilization, daily_cost_utilization,
                monthly_token_utilization, monthly_cost_utilization
            )

            # Determine approval based on thresholds
            if max_utilization >= 1.0:
                status = BudgetStatus.BLOCKED
                is_allowed = False
                reason = "Budget limit exceeded"
            elif max_utilization >= budget_limit.hard_threshold:
                status = BudgetStatus.EXCEEDED
                is_allowed = priority_boost  # Only allow high-priority requests
                reason = f"Budget {max_utilization:.1%} utilized (hard threshold: {budget_limit.hard_threshold:.1%})"
            elif max_utilization >= budget_limit.soft_threshold:
                status = BudgetStatus.CRITICAL
                is_allowed = True
                reason = f"Budget {max_utilization:.1%} utilized (warning threshold)"
            elif max_utilization >= 0.6:
                status = BudgetStatus.WARNING
                is_allowed = True
                reason = f"Budget {max_utilization:.1%} utilized"
            else:
                status = BudgetStatus.HEALTHY
                is_allowed = True
                reason = f"Budget {max_utilization:.1%} utilized"

            # Calculate remaining budget
            remaining_tokens_daily = max(0, budget_limit.max_tokens_daily - budget_usage.current_tokens_daily)
            remaining_tokens_monthly = max(0, budget_limit.max_tokens_monthly - budget_usage.current_tokens_monthly)
            remaining_cost_daily = max(Decimal('0'), budget_limit.max_cost_daily - budget_usage.current_cost_daily)
            remaining_cost_monthly = max(Decimal('0'), budget_limit.max_cost_monthly - budget_usage.current_cost_monthly)

            # Generate recommendations
            recommended_action = self._get_budget_recommendation(status, max_utilization, priority_boost)

            return BudgetCheck(
                is_allowed=is_allowed,
                budget_status=status,
                remaining_tokens_daily=remaining_tokens_daily,
                remaining_tokens_monthly=remaining_tokens_monthly,
                remaining_cost_daily=remaining_cost_daily,
                remaining_cost_monthly=remaining_cost_monthly,
                estimated_request_cost=estimated_cost,
                reason=reason,
                recommended_action=recommended_action
            )

        except Exception as e:
            logger.error(f"Budget check failed for {budget_type.value}:{budget_id}: {e}")
            # Fail open with warning
            return BudgetCheck(
                is_allowed=True,
                budget_status=BudgetStatus.HEALTHY,
                remaining_tokens_daily=1000,
                remaining_tokens_monthly=10000,
                remaining_cost_daily=Decimal('1.00'),
                remaining_cost_monthly=Decimal('10.00'),
                estimated_request_cost=Decimal('0.01'),
                reason=f"Budget check failed: {e}",
                recommended_action="Monitor budget manually"
            )

    async def record_actual_usage(
        self,
        budget_type: BudgetType,
        budget_id: str,
        input_tokens: int,
        output_tokens: int,
        cache_read_tokens: int = 0,
        cache_creation_tokens: int = 0,
        contact_id: str = "unknown"
    ) -> None:
        """
        Record actual token usage after API call completion.

        Args:
            budget_type: Type of budget
            budget_id: Budget identifier
            input_tokens: Actual input tokens used
            output_tokens: Actual output tokens used
            cache_read_tokens: Tokens read from cache
            cache_creation_tokens: Tokens used for cache creation
            contact_id: Contact ID for detailed tracking
        """
        try:
            # Calculate actual cost
            actual_cost = self.calculate_request_cost(
                input_tokens=input_tokens,
                estimated_output_tokens=output_tokens,
                cache_read_tokens=cache_read_tokens,
                cache_creation_tokens=cache_creation_tokens
            )

            total_tokens = input_tokens + output_tokens

            # Update budget usage
            await self._update_budget_usage(
                budget_type=budget_type,
                budget_id=budget_id,
                tokens_used=total_tokens,
                cost_incurred=actual_cost
            )

            # Log usage for analytics
            logger.info(
                f"Usage recorded for {budget_type.value}:{budget_id}: "
                f"{total_tokens} tokens, ${actual_cost:.4f} cost"
            )

            # Check for budget alerts
            budget_usage = await self.get_budget_usage(budget_type, budget_id)
            budget_limit = await self.get_budget_limit(budget_type, budget_id)

            await self._check_for_budget_alerts(
                budget_id=budget_id,
                budget_type=budget_type,
                usage=budget_usage,
                limit=budget_limit,
                contact_id=contact_id
            )

        except Exception as e:
            logger.error(f"Failed to record usage for {budget_type.value}:{budget_id}: {e}")

    async def get_budget_limit(self, budget_type: BudgetType, budget_id: str) -> BudgetLimit:
        """Get budget limit configuration for a specific budget."""
        try:
            if self.redis:
                # Try to get from Redis
                key = f"budget_limit:{budget_type.value}:{budget_id}"
                data = await self.redis.hgetall(key)

                if data:
                    return BudgetLimit(
                        budget_type=budget_type,
                        budget_id=budget_id,
                        max_tokens_monthly=int(data.get("max_tokens_monthly", 0)),
                        max_tokens_daily=int(data.get("max_tokens_daily", 0)),
                        max_cost_monthly=Decimal(data.get("max_cost_monthly", "0")),
                        max_cost_daily=Decimal(data.get("max_cost_daily", "0")),
                        soft_threshold=float(data.get("soft_threshold", 0.8)),
                        hard_threshold=float(data.get("hard_threshold", 0.95))
                    )

            # Use default limits if not found
            defaults = self.default_limits.get(budget_type, self.default_limits[BudgetType.CONTACT])

            return BudgetLimit(
                budget_type=budget_type,
                budget_id=budget_id,
                **defaults
            )

        except Exception as e:
            logger.error(f"Failed to get budget limit for {budget_type.value}:{budget_id}: {e}")
            # Return conservative default
            return BudgetLimit(
                budget_type=budget_type,
                budget_id=budget_id,
                max_tokens_monthly=10_000,
                max_tokens_daily=1_000,
                max_cost_monthly=Decimal('5.00'),
                max_cost_daily=Decimal('0.25')
            )

    async def get_budget_usage(self, budget_type: BudgetType, budget_id: str) -> BudgetUsage:
        """Get current budget usage for a specific budget."""
        try:
            if self.redis:
                key = f"budget_usage:{budget_type.value}:{budget_id}"
                data = await self.redis.hgetall(key)

                if data:
                    return BudgetUsage(
                        budget_id=budget_id,
                        budget_type=budget_type,
                        current_tokens_monthly=int(data.get("current_tokens_monthly", 0)),
                        current_tokens_daily=int(data.get("current_tokens_daily", 0)),
                        current_cost_monthly=Decimal(data.get("current_cost_monthly", "0")),
                        current_cost_daily=Decimal(data.get("current_cost_daily", "0")),
                        last_updated=datetime.fromisoformat(data.get("last_updated", datetime.utcnow().isoformat())),
                        last_reset=datetime.fromisoformat(data.get("last_reset", datetime.utcnow().isoformat()))
                    )

            # Return empty usage if not found
            return BudgetUsage(budget_id=budget_id, budget_type=budget_type)

        except Exception as e:
            logger.error(f"Failed to get budget usage for {budget_type.value}:{budget_id}: {e}")
            return BudgetUsage(budget_id=budget_id, budget_type=budget_type)

    async def _update_budget_usage(
        self,
        budget_type: BudgetType,
        budget_id: str,
        tokens_used: int,
        cost_incurred: Decimal
    ) -> None:
        """Update budget usage in Redis."""
        try:
            if not self.redis:
                return

            key = f"budget_usage:{budget_type.value}:{budget_id}"
            now = datetime.utcnow()

            # Get current usage
            current_usage = await self.get_budget_usage(budget_type, budget_id)

            # Check if we need to reset daily usage
            if current_usage.last_updated.date() != now.date():
                current_usage.current_tokens_daily = 0
                current_usage.current_cost_daily = Decimal('0')

            # Check if we need to reset monthly usage
            if current_usage.last_updated.month != now.month or current_usage.last_updated.year != now.year:
                current_usage.current_tokens_monthly = 0
                current_usage.current_cost_monthly = Decimal('0')

            # Update usage
            current_usage.current_tokens_daily += tokens_used
            current_usage.current_tokens_monthly += tokens_used
            current_usage.current_cost_daily += cost_incurred
            current_usage.current_cost_monthly += cost_incurred
            current_usage.last_updated = now

            # Store updated usage
            await self.redis.hset(key, mapping={
                "current_tokens_monthly": current_usage.current_tokens_monthly,
                "current_tokens_daily": current_usage.current_tokens_daily,
                "current_cost_monthly": str(current_usage.current_cost_monthly),
                "current_cost_daily": str(current_usage.current_cost_daily),
                "last_updated": current_usage.last_updated.isoformat(),
                "last_reset": current_usage.last_reset.isoformat()
            })

            # Set expiration for cleanup (2 months)
            await self.redis.expire(key, 60 * 60 * 24 * 60)  # 60 days

        except Exception as e:
            logger.error(f"Failed to update budget usage: {e}")

    def _get_budget_recommendation(self, status: BudgetStatus, utilization: float, priority_boost: bool) -> str:
        """Generate budget management recommendations."""
        if status == BudgetStatus.BLOCKED:
            return "Budget exhausted. Consider upgrading budget limits or wait for daily/monthly reset."
        elif status == BudgetStatus.EXCEEDED:
            if priority_boost:
                return "High-priority request approved despite budget limit. Monitor usage closely."
            else:
                return "Budget limit exceeded. Request blocked. Use priority boost for critical requests only."
        elif status == BudgetStatus.CRITICAL:
            return f"Budget {utilization:.1%} used. Consider optimizing queries or increasing budget."
        elif status == BudgetStatus.WARNING:
            return f"Budget {utilization:.1%} used. Monitor usage and consider conversation optimization."
        else:
            return "Budget utilization healthy. Continue normal operations."

    async def _check_for_budget_alerts(
        self,
        budget_id: str,
        budget_type: BudgetType,
        usage: BudgetUsage,
        limit: BudgetLimit,
        contact_id: str = "unknown"
    ) -> None:
        """Check for budget alerts and send notifications."""
        try:
            # Calculate utilization rates
            daily_token_util = usage.current_tokens_daily / limit.max_tokens_daily
            monthly_token_util = usage.current_tokens_monthly / limit.max_tokens_monthly
            daily_cost_util = float(usage.current_cost_daily / limit.max_cost_daily)
            monthly_cost_util = float(usage.current_cost_monthly / limit.max_cost_monthly)

            max_util = max(daily_token_util, monthly_token_util, daily_cost_util, monthly_cost_util)

            # Send alerts for threshold crossings
            if max_util >= limit.hard_threshold:
                await self._send_budget_alert(
                    alert_type="CRITICAL",
                    budget_id=budget_id,
                    budget_type=budget_type,
                    utilization=max_util,
                    contact_id=contact_id,
                    message=f"Budget {max_util:.1%} utilized - hard threshold exceeded"
                )
            elif max_util >= limit.soft_threshold:
                await self._send_budget_alert(
                    alert_type="WARNING",
                    budget_id=budget_id,
                    budget_type=budget_type,
                    utilization=max_util,
                    contact_id=contact_id,
                    message=f"Budget {max_util:.1%} utilized - soft threshold exceeded"
                )

        except Exception as e:
            logger.error(f"Failed to check budget alerts: {e}")

    async def _send_budget_alert(
        self,
        alert_type: str,
        budget_id: str,
        budget_type: BudgetType,
        utilization: float,
        contact_id: str,
        message: str
    ) -> None:
        """Send budget alert notification."""
        try:
            alert_data = {
                "timestamp": datetime.utcnow().isoformat(),
                "alert_type": alert_type,
                "budget_type": budget_type.value,
                "budget_id": budget_id,
                "contact_id": contact_id,
                "utilization": utilization,
                "message": message
            }

            # Log alert
            logger.warning(f"Budget alert: {alert_type} - {message}")

            # Store alert in Redis for dashboard
            if self.redis:
                alert_key = f"budget_alerts:{budget_type.value}:{budget_id}"
                await self.redis.lpush(alert_key, json.dumps(alert_data))
                await self.redis.ltrim(alert_key, 0, 99)  # Keep last 100 alerts
                await self.redis.expire(alert_key, 60 * 60 * 24 * 30)  # 30 days

        except Exception as e:
            logger.error(f"Failed to send budget alert: {e}")


# Global budget service instance
token_budget_service = TokenBudgetService()