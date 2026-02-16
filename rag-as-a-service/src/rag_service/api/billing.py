"""Billing API — usage tracking and subscription management."""

from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/billing", tags=["billing"])


class UsageResponse(BaseModel):
    tenant_id: str
    queries_this_month: int = 0
    storage_bytes: int = 0
    documents: int = 0
    queries_limit: int = 0
    storage_limit_mb: int = 0
    documents_limit: int = 0
    overage_queries: int = 0


class CheckoutResponse(BaseModel):
    checkout_url: str | None = None


@router.get("/usage", response_model=UsageResponse)
async def get_usage(request: Request):
    """Get current usage stats for the tenant."""
    tenant_id = request.state.tenant_id
    tier = getattr(request.state, "tenant_tier", "starter")

    usage_tracker = request.app.state.usage_tracker
    stats = await usage_tracker.get_usage(tenant_id, tier)

    return UsageResponse(
        tenant_id=stats.tenant_id,
        queries_this_month=stats.queries_this_month,
        storage_bytes=stats.storage_bytes,
        documents=stats.documents,
        queries_limit=stats.queries_limit,
        storage_limit_mb=stats.storage_limit_mb,
        documents_limit=stats.documents_limit,
        overage_queries=stats.overage_queries,
    )


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(request: Request, tier: str = "pro"):
    """Create a Stripe checkout session for tier upgrade."""
    tenant_id = request.state.tenant_id

    billing = getattr(request.app.state, "billing_service", None)
    if not billing:
        return CheckoutResponse(checkout_url=None)

    url = await billing.get_checkout_url(
        customer_id=tenant_id,
        tier=tier,
    )
    return CheckoutResponse(checkout_url=url)
