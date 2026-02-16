"""Per-minute Stripe billing using shared_infra.StripeBillingService."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from enum import Enum

from shared_schemas import UsageEvent, UsageEventType

logger = logging.getLogger(__name__)


class BillingTier(str, Enum):
    PAYG = "payg"
    GROWTH = "growth"
    ENTERPRISE = "enterprise"
    WHITELABEL = "whitelabel"


# Per-minute rates by tier
TIER_RATES: dict[BillingTier, float] = {
    BillingTier.PAYG: 0.20,
    BillingTier.GROWTH: 0.15,
    BillingTier.ENTERPRISE: 0.12,
    BillingTier.WHITELABEL: 0.10,
}


@dataclass
class BillingService:
    """Per-minute voice call billing via Stripe metered billing.

    Tracks call duration and reports usage to Stripe on call end.
    Each minute (rounded up) is reported as one usage event.
    """

    stripe_billing: object  # StripeBillingService instance

    def get_rate(self, tier: BillingTier) -> float:
        """Get the per-minute rate for a billing tier."""
        return TIER_RATES.get(tier, TIER_RATES[BillingTier.PAYG])

    def calculate_cost(self, duration_seconds: float, tier: BillingTier) -> float:
        """Calculate the cost for a call based on duration and tier.

        Duration is rounded up to the nearest minute.
        """
        minutes = math.ceil(duration_seconds / 60.0) if duration_seconds > 0 else 0
        rate = self.get_rate(tier)
        return round(minutes * rate, 4)

    def calculate_minutes(self, duration_seconds: float) -> int:
        """Calculate billable minutes (rounded up) from duration in seconds."""
        return math.ceil(duration_seconds / 60.0) if duration_seconds > 0 else 0

    async def report_call_usage(
        self,
        tenant_id: str,
        duration_seconds: float,
        tier: BillingTier = BillingTier.PAYG,
        call_id: str | None = None,
    ) -> dict:
        """Report call usage to Stripe metered billing.

        Args:
            tenant_id: The Stripe customer ID for the tenant.
            duration_seconds: Call duration in seconds.
            tier: The billing tier for rate calculation.
            call_id: Optional call ID for metadata.

        Returns:
            Stripe meter event response.
        """
        minutes = self.calculate_minutes(duration_seconds)
        if minutes == 0:
            logger.info("Zero-minute call, skipping billing for tenant %s", tenant_id)
            return {}

        event = UsageEvent(
            tenant_id=tenant_id,
            event_type=UsageEventType.VOICE_MINUTE,
            quantity=float(minutes),
            metadata={
                "call_id": call_id or "",
                "duration_seconds": duration_seconds,
                "tier": tier.value,
                "rate_per_minute": self.get_rate(tier),
            },
        )

        result = await self.stripe_billing.report_usage(event)
        cost = self.calculate_cost(duration_seconds, tier)
        logger.info(
            "Reported %d minutes for tenant %s (tier=%s, cost=$%.4f)",
            minutes,
            tenant_id,
            tier.value,
            cost,
        )
        return result

    def get_cost_breakdown(
        self,
        duration_seconds: float,
        cost_stt: float = 0,
        cost_tts: float = 0,
        cost_llm: float = 0,
        cost_telephony: float = 0,
        tier: BillingTier = BillingTier.PAYG,
    ) -> dict:
        """Calculate full cost breakdown for a call."""
        revenue = self.calculate_cost(duration_seconds, tier)
        total_cogs = cost_stt + cost_tts + cost_llm + cost_telephony
        return {
            "revenue": revenue,
            "cogs": {
                "stt": cost_stt,
                "tts": cost_tts,
                "llm": cost_llm,
                "telephony": cost_telephony,
                "total": total_cogs,
            },
            "gross_profit": round(revenue - total_cogs, 4),
            "gross_margin": round((revenue - total_cogs) / revenue, 4) if revenue > 0 else 0,
        }
