"""Quota enforcement service — tier-based limits for documents, queries, and storage."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from fastapi import HTTPException, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class TierName(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    BUSINESS = "business"
    ENTERPRISE = "enterprise"


@dataclass(frozen=True)
class TierQuota:
    """Resource limits for a billing tier."""

    max_documents: int
    max_queries_per_month: int
    max_storage_mb: int


TIER_QUOTAS: dict[str, TierQuota] = {
    "free": TierQuota(max_documents=100, max_queries_per_month=1_000, max_storage_mb=500),
    "starter": TierQuota(max_documents=500, max_queries_per_month=5_000, max_storage_mb=1_000),
    "pro": TierQuota(max_documents=10_000, max_queries_per_month=50_000, max_storage_mb=10_000),
    "business": TierQuota(
        max_documents=999_999, max_queries_per_month=500_000, max_storage_mb=100_000
    ),
    "enterprise": TierQuota(
        max_documents=999_999, max_queries_per_month=999_999, max_storage_mb=999_999
    ),
}

# Map request paths to the resource type they consume
RESOURCE_PATHS: dict[str, str] = {
    "POST /api/v1/documents": "documents",
    "POST /api/v1/query": "queries",
    "POST /api/v1/query/stream": "queries",
}


class QuotaEnforcementMiddleware(BaseHTTPMiddleware):
    """Middleware that checks tenant quotas before allowing resource-consuming requests."""

    async def dispatch(self, request: Request, call_next) -> Response:
        path_key = f"{request.method} {request.url.path}"
        resource = RESOURCE_PATHS.get(path_key)

        if resource is None:
            return await call_next(request)

        tenant_id = getattr(request.state, "tenant_id", None)
        tier = getattr(request.state, "tenant_tier", "starter")

        if tenant_id is None:
            return await call_next(request)

        usage_tracker = getattr(request.app.state, "usage_tracker", None)
        if usage_tracker is None:
            return await call_next(request)

        within_quota = await usage_tracker.check_quota(tenant_id, tier, resource)
        if not within_quota:
            quota = TIER_QUOTAS.get(tier, TIER_QUOTAS["starter"])
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "quota_exceeded",
                    "message": f"{resource.title()} limit exceeded for {tier} tier",
                    "tier": tier,
                    "limit": getattr(quota, f"max_{resource}_per_month", None)
                    or getattr(quota, f"max_{resource}", None),
                    "upgrade_url": "/api/v1/usage/upgrade",
                },
            )

        return await call_next(request)


def get_tier_quota(tier: str) -> TierQuota:
    """Get quota limits for a tier name."""
    return TIER_QUOTAS.get(tier, TIER_QUOTAS["starter"])


async def check_quota_or_raise(
    usage_tracker, tenant_id: str, tier: str, resource: str
) -> None:
    """Check quota and raise HTTPException if exceeded. Use in route handlers."""
    within_quota = await usage_tracker.check_quota(tenant_id, tier, resource)
    if not within_quota:
        quota = get_tier_quota(tier)
        raise HTTPException(
            status_code=429,
            detail={
                "error": "quota_exceeded",
                "message": f"{resource.title()} limit exceeded for {tier} tier",
                "tier": tier,
                "upgrade_url": "/api/v1/usage/upgrade",
            },
        )
