"""Cross-field validators and tenant limit defaults."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from shared_schemas.tenant import TenantLimits, TenantTier

_DEFAULT_LIMITS: dict[str, dict[str, int | float]] = {
    "FREE": {"max_users": 1, "max_queries_per_day": 100, "max_storage_gb": 1.0, "max_api_keys": 1},
    "STARTER": {"max_users": 5, "max_queries_per_day": 1_000, "max_storage_gb": 10.0, "max_api_keys": 3},
    "PRO": {"max_users": 25, "max_queries_per_day": 10_000, "max_storage_gb": 100.0, "max_api_keys": 10},
    "ENTERPRISE": {"max_users": 999_999, "max_queries_per_day": 999_999, "max_storage_gb": 999_999.0, "max_api_keys": 999_999},
}


def get_default_limits(tier: TenantTier) -> TenantLimits:
    """Return default TenantLimits for the given tier."""
    from shared_schemas.tenant import TenantLimits

    return TenantLimits(**_DEFAULT_LIMITS[tier.value.upper()])


def validate_tenant_limits(tier: TenantTier, limits: TenantLimits | None) -> TenantLimits:
    """Return limits if provided, otherwise default limits for the tier."""
    if limits is not None:
        return limits
    return get_default_limits(tier)
