"""Tests for cross-field validators."""

import pytest

from shared_schemas.tenant import TenantLimits, TenantTier
from shared_schemas.validators import validate_tenant_limits, validate_weight_sum


class TestValidateTenantLimits:
    def test_within_limits(self):
        limits = TenantLimits(max_users=1, max_queries_per_day=50, storage_gb=0.3, max_api_keys=1, rate_limit_rpm=10)
        violations = validate_tenant_limits(TenantTier.FREE, limits)
        assert violations == []

    def test_exceeds_users(self):
        limits = TenantLimits(max_users=10, max_queries_per_day=50, storage_gb=0.3, max_api_keys=1, rate_limit_rpm=10)
        violations = validate_tenant_limits(TenantTier.FREE, limits)
        assert len(violations) == 1
        assert "max_users" in violations[0]

    def test_exceeds_multiple(self):
        limits = TenantLimits(
            max_users=999, max_queries_per_day=999999, storage_gb=500, max_api_keys=50, rate_limit_rpm=1000
        )
        violations = validate_tenant_limits(TenantTier.FREE, limits)
        assert len(violations) == 5

    def test_enterprise_no_violations(self):
        limits = TenantLimits(
            max_users=999, max_queries_per_day=999999, storage_gb=500, max_api_keys=50, rate_limit_rpm=1000
        )
        violations = validate_tenant_limits(TenantTier.ENTERPRISE, limits)
        assert violations == []

    def test_exact_limit_is_valid(self):
        from shared_schemas.tenant import TIER_LIMITS
        free_limits = TIER_LIMITS[TenantTier.FREE]
        violations = validate_tenant_limits(TenantTier.FREE, free_limits)
        assert violations == []


class TestValidateWeightSum:
    def test_valid_weights(self):
        weights = {"a": 0.4, "b": 0.3, "c": 0.3}
        assert validate_weight_sum(weights) is True

    def test_weights_sum_to_one_within_tolerance(self):
        weights = {"a": 0.333, "b": 0.333, "c": 0.334}
        assert validate_weight_sum(weights) is True

    def test_invalid_sum(self):
        weights = {"a": 0.5, "b": 0.6}
        with pytest.raises(ValueError, match="Weights sum to"):
            validate_weight_sum(weights)

    def test_negative_weight(self):
        weights = {"a": 1.5, "b": -0.5}
        with pytest.raises(ValueError, match="negative"):
            validate_weight_sum(weights)

    def test_custom_expected_sum(self):
        weights = {"a": 50, "b": 50}
        assert validate_weight_sum(weights, expected_sum=100.0) is True

    def test_empty_weights(self):
        with pytest.raises(ValueError, match="Weights sum to"):
            validate_weight_sum({})
