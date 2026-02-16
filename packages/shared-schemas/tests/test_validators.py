"""Unit tests for validators — default limits, limit validation."""

from __future__ import annotations

import pytest

from shared_schemas.tenant import TenantConfig, TenantLimits, TenantTier
from shared_schemas.validators import get_default_limits, validate_tenant_limits


class TestGetDefaultLimits:
    def test_free_tier_defaults(self):
        limits = get_default_limits(TenantTier.FREE)
        assert limits.max_users == 1
        assert limits.max_queries_per_day == 100
        assert limits.max_storage_gb == 1.0
        assert limits.max_api_keys == 1

    def test_starter_tier_defaults(self):
        limits = get_default_limits(TenantTier.STARTER)
        assert limits.max_users == 5
        assert limits.max_queries_per_day == 1_000
        assert limits.max_storage_gb == 10.0
        assert limits.max_api_keys == 3

    def test_pro_tier_defaults(self):
        limits = get_default_limits(TenantTier.PRO)
        assert limits.max_users == 25
        assert limits.max_queries_per_day == 10_000

    def test_enterprise_tier_defaults(self):
        limits = get_default_limits(TenantTier.ENTERPRISE)
        assert limits.max_users == 999_999
        assert limits.max_api_keys == 999_999

    def test_all_tiers_return_frozen_limits(self):
        for tier in TenantTier:
            limits = get_default_limits(tier)
            with pytest.raises(Exception):
                limits.max_users = 0


class TestValidateTenantLimits:
    def test_returns_provided_limits(self):
        custom = TenantLimits(max_users=3, max_queries_per_day=50)
        result = validate_tenant_limits(TenantTier.PRO, custom)
        assert result.max_users == 3

    def test_returns_defaults_when_none(self):
        result = validate_tenant_limits(TenantTier.STARTER, None)
        assert result.max_users == 5

    def test_each_tier_has_defaults(self):
        for tier in TenantTier:
            result = validate_tenant_limits(tier, None)
            assert isinstance(result, TenantLimits)
