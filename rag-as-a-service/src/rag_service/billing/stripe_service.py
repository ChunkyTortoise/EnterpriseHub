"""RAG billing service — report query usage to Stripe meter."""

from __future__ import annotations

import logging

from shared_schemas import UsageEvent, UsageEventType

logger = logging.getLogger(__name__)


class RAGBillingService:
    """Stripe billing integration for RAG-as-a-Service."""

    def __init__(self, stripe_billing=None):
        """Initialize with shared StripeBillingService."""
        self.stripe = stripe_billing

    async def report_query_usage(self, tenant_id: str, query_count: int = 1) -> dict | None:
        """Report RAG query usage to Stripe metering."""
        if not self.stripe:
            logger.debug("Stripe billing not configured, skipping usage report")
            return None

        event = UsageEvent(
            tenant_id=tenant_id,
            event_type=UsageEventType.RAG_QUERY,
            quantity=query_count,
            metadata={"service": "rag-as-a-service"},
        )

        try:
            result = await self.stripe.report_usage(event)
            logger.info("Reported %d queries for tenant %s", query_count, tenant_id)
            return result
        except Exception:
            logger.exception("Failed to report usage for tenant %s", tenant_id)
            return None

    async def create_subscription(
        self, customer_id: str, tier: str = "starter"
    ) -> dict | None:
        """Create a subscription for a tenant."""
        if not self.stripe:
            return None

        price_map = {
            "starter": "price_starter_rag",
            "pro": "price_pro_rag",
            "business": "price_business_rag",
        }

        price_id = price_map.get(tier)
        if not price_id:
            raise ValueError(f"Unknown tier: {tier}")

        return await self.stripe.create_subscription(customer_id, price_id)

    async def get_checkout_url(
        self,
        customer_id: str,
        tier: str,
        success_url: str = "https://app.example.com/success",
        cancel_url: str = "https://app.example.com/cancel",
    ) -> str | None:
        """Generate a Stripe checkout URL for a tier upgrade."""
        if not self.stripe:
            return None

        price_map = {
            "starter": "price_starter_rag",
            "pro": "price_pro_rag",
            "business": "price_business_rag",
        }

        price_id = price_map.get(tier)
        if not price_id:
            raise ValueError(f"Unknown tier: {tier}")

        return await self.stripe.create_checkout_session(
            customer_id, price_id, success_url, cancel_url
        )
