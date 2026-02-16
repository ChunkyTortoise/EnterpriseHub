"""Tests for quota enforcement service."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock

from rag_service.billing.quota_service import (
    TIER_QUOTAS,
    QuotaEnforcementMiddleware,
    TierName,
    TierQuota,
    check_quota_or_raise,
    get_tier_quota,
)
from rag_service.billing.usage_tracker import UsageTracker


class TestTierQuotas:
    """Tier quota configuration tests."""

    def test_all_tiers_defined(self):
        for tier in TierName:
            assert tier.value in TIER_QUOTAS

    def test_starter_limits(self):
        q = TIER_QUOTAS["starter"]
        assert q.max_documents == 500
        assert q.max_queries_per_month == 5_000
        assert q.max_storage_mb == 1_000

    def test_pro_limits(self):
        q = TIER_QUOTAS["pro"]
        assert q.max_documents == 10_000
        assert q.max_queries_per_month == 50_000
        assert q.max_storage_mb == 10_000

    def test_business_limits(self):
        q = TIER_QUOTAS["business"]
        assert q.max_documents == 999_999
        assert q.max_queries_per_month == 500_000

    def test_tiers_are_monotonically_increasing(self):
        ordered = ["free", "starter", "pro", "business", "enterprise"]
        for i in range(len(ordered) - 1):
            lower = TIER_QUOTAS[ordered[i]]
            upper = TIER_QUOTAS[ordered[i + 1]]
            assert upper.max_documents >= lower.max_documents
            assert upper.max_queries_per_month >= lower.max_queries_per_month
            assert upper.max_storage_mb >= lower.max_storage_mb

    def test_get_tier_quota_known(self):
        assert get_tier_quota("pro") == TIER_QUOTAS["pro"]

    def test_get_tier_quota_unknown_returns_starter(self):
        assert get_tier_quota("nonexistent") == TIER_QUOTAS["starter"]


class TestCheckQuotaOrRaise:
    """Tests for the check_quota_or_raise helper."""

    @pytest.mark.asyncio
    async def test_within_quota_does_not_raise(self):
        tracker = UsageTracker()
        await check_quota_or_raise(tracker, "t1", "pro", "queries")

    @pytest.mark.asyncio
    async def test_exceeded_quota_raises_429(self):
        tracker = UsageTracker()
        # Exhaust starter query quota
        for _ in range(5_001):
            await tracker.increment_queries("t1")

        with pytest.raises(Exception) as exc_info:
            await check_quota_or_raise(tracker, "t1", "starter", "queries")
        assert exc_info.value.status_code == 429
        assert "quota_exceeded" in str(exc_info.value.detail)


class TestQuotaEnforcementMiddleware:
    """Tests for the middleware integration."""

    @pytest.mark.asyncio
    async def test_non_resource_path_passes_through(self):
        middleware = QuotaEnforcementMiddleware(app=MagicMock())
        request = MagicMock()
        request.method = "GET"
        request.url.path = "/health"
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        resp = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_missing_tenant_passes_through(self):
        middleware = QuotaEnforcementMiddleware(app=MagicMock())
        request = MagicMock()
        request.method = "POST"
        request.url.path = "/api/v1/query"
        request.state = MagicMock(spec=[])  # no tenant_id attribute
        call_next = AsyncMock(return_value=MagicMock(status_code=200))
        resp = await middleware.dispatch(request, call_next)
        call_next.assert_awaited_once()
