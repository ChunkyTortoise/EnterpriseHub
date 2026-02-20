"""Unit tests for quota enforcement — tier limits, quota checking."""

from __future__ import annotations

import pytest
from fastapi import HTTPException
from unittest.mock import AsyncMock

from rag_service.billing.quota_service import (
    TierName,
    TIER_QUOTAS,
    get_tier_quota,
    check_quota_or_raise,
)


class TestTierQuotas:
    def test_free_tier_limits(self):
        q = TIER_QUOTAS["free"]
        assert q.max_documents == 100
        assert q.max_queries_per_month == 1_000
        assert q.max_storage_mb == 500

    def test_starter_tier_limits(self):
        q = TIER_QUOTAS["starter"]
        assert q.max_documents == 500

    def test_pro_tier_limits(self):
        q = TIER_QUOTAS["pro"]
        assert q.max_documents == 10_000
        assert q.max_queries_per_month == 50_000

    def test_business_tier_limits(self):
        q = TIER_QUOTAS["business"]
        assert q.max_documents == 999_999

    def test_enterprise_tier_limits(self):
        q = TIER_QUOTAS["enterprise"]
        assert q.max_storage_mb == 999_999

    def test_tier_quota_is_frozen(self):
        q = TIER_QUOTAS["free"]
        with pytest.raises(AttributeError):
            q.max_documents = 999


class TestGetTierQuota:
    def test_known_tier(self):
        q = get_tier_quota("pro")
        assert q.max_documents == 10_000

    def test_unknown_tier_returns_starter(self):
        q = get_tier_quota("nonexistent")
        assert q == TIER_QUOTAS["starter"]


class TestCheckQuotaOrRaise:
    @pytest.mark.asyncio
    async def test_within_quota_passes(self):
        tracker = AsyncMock()
        tracker.check_quota.return_value = True
        # Should not raise
        await check_quota_or_raise(tracker, "t1", "pro", "documents")

    @pytest.mark.asyncio
    async def test_exceeds_quota_raises_429(self):
        tracker = AsyncMock()
        tracker.check_quota.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await check_quota_or_raise(tracker, "t1", "free", "documents")
        assert exc_info.value.status_code == 429
        assert "quota_exceeded" in str(exc_info.value.detail)

    @pytest.mark.asyncio
    async def test_error_includes_tier(self):
        tracker = AsyncMock()
        tracker.check_quota.return_value = False
        with pytest.raises(HTTPException) as exc_info:
            await check_quota_or_raise(tracker, "t1", "starter", "queries")
        assert exc_info.value.detail["tier"] == "starter"


class TestTierNameEnum:
    def test_all_tiers(self):
        assert TierName.FREE.value == "free"
        assert TierName.STARTER.value == "starter"
        assert TierName.PRO.value == "pro"
        assert TierName.BUSINESS.value == "business"
        assert TierName.ENTERPRISE.value == "enterprise"

    def test_tier_count(self):
        assert len(TierName) == 5
