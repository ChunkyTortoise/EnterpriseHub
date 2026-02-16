"""Cross-field validators and utility validation functions."""

from shared_schemas.tenant import TenantLimits, TenantTier, TIER_LIMITS


def validate_tenant_limits(tier: TenantTier, requested_limits: TenantLimits) -> list[str]:
    """Validate that requested limits don't exceed tier maximums.

    Returns a list of violation messages (empty if valid).
    """
    tier_max = TIER_LIMITS[tier]
    violations: list[str] = []

    if requested_limits.max_users > tier_max.max_users:
        violations.append(
            f"max_users {requested_limits.max_users} exceeds tier limit {tier_max.max_users}"
        )
    if requested_limits.max_queries_per_day > tier_max.max_queries_per_day:
        violations.append(
            f"max_queries_per_day {requested_limits.max_queries_per_day} exceeds tier limit {tier_max.max_queries_per_day}"
        )
    if requested_limits.storage_gb > tier_max.storage_gb:
        violations.append(
            f"storage_gb {requested_limits.storage_gb} exceeds tier limit {tier_max.storage_gb}"
        )
    if requested_limits.max_api_keys > tier_max.max_api_keys:
        violations.append(
            f"max_api_keys {requested_limits.max_api_keys} exceeds tier limit {tier_max.max_api_keys}"
        )
    if requested_limits.rate_limit_rpm > tier_max.rate_limit_rpm:
        violations.append(
            f"rate_limit_rpm {requested_limits.rate_limit_rpm} exceeds tier limit {tier_max.rate_limit_rpm}"
        )

    return violations


def validate_weight_sum(
    weights: dict[str, float], tolerance: float = 0.01, expected_sum: float = 1.0
) -> bool:
    """Validate that weights sum to expected value within tolerance.

    Args:
        weights: Dictionary of weight name -> value pairs.
        tolerance: Allowed deviation from expected_sum.
        expected_sum: Target sum for all weights.

    Returns:
        True if valid, raises ValueError otherwise.
    """
    total = sum(weights.values())
    if abs(total - expected_sum) > tolerance:
        raise ValueError(
            f"Weights sum to {total:.4f}, expected {expected_sum} (tolerance: {tolerance})"
        )

    for name, value in weights.items():
        if value < 0:
            raise ValueError(f"Weight '{name}' is negative: {value}")

    return True
