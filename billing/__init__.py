"""
Billing enums and plan configuration for EnterpriseHub.

Provides subscription tiers, status enums, and plan configurations
for the EnterpriseHub SaaS platform.
"""

import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class PlanTier(str, Enum):
    """Plan tier enumeration."""

    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"


class SubscriptionStatus(str, Enum):
    """Subscription status enumeration."""

    INCOMPLETE = "incomplete"
    TRIALING = "trialing"
    ACTIVE = "active"
    PAST_DUE = "past_due"
    CANCELED = "canceled"
    UNPAID = "unpaid"
    PAUSED = "paused"


class ResourceType(str, Enum):
    """Resource type for usage tracking."""

    LEAD = "lead"
    QUERY = "query"
    API_CALL = "api_call"
    SMS = "sms"
    EMAIL = "email"
    REPORT = "report"
    EXPORT = "export"


# Default plan configurations (can be overridden by YAML config)
PLAN_CONFIGS: Dict[PlanTier, Dict[str, Any]] = {
    PlanTier.STARTER: {
        "name": "Starter",
        "description": "Perfect for small teams getting started with AI-powered real estate",
        "price_monthly_cents": 4900,  # $49.00
        "price_annual_cents": 47040,  # $470.40 (20% discount)
        "lead_quota": 100,
        "query_quota": 100,
        "features": {
            "lead_management": True,
            "buyer_bot": False,
            "seller_bot": False,
            "market_analysis": False,
            "cma_reports": False,
            "white_label": False,
            "api_access": False,
            "dedicated_support": False,
            "priority_processing": False,
            "custom_integrations": False,
        },
        "limits": {
            "team_members": 1,
            "concurrent_conversations": 10,
            "api_calls_per_day": 100,
            "exports_per_month": 5,
        },
        "support": {
            "email": True,
            "chat": False,
            "phone": False,
            "response_time_hours": 48,
        },
    },
    PlanTier.PROFESSIONAL: {
        "name": "Professional",
        "description": "For growing teams ready to automate their entire pipeline",
        "price_monthly_cents": 14900,  # $149.00
        "price_annual_cents": 143040,  # $1,430.40 (20% discount)
        "lead_quota": 500,
        "query_quota": 500,
        "features": {
            "lead_management": True,
            "buyer_bot": True,
            "seller_bot": True,
            "market_analysis": True,
            "cma_reports": True,
            "white_label": False,
            "api_access": True,
            "dedicated_support": False,
            "priority_processing": True,
            "custom_integrations": False,
        },
        "limits": {
            "team_members": 5,
            "concurrent_conversations": 50,
            "api_calls_per_day": 1000,
            "exports_per_month": 25,
        },
        "support": {
            "email": True,
            "chat": True,
            "phone": False,
            "response_time_hours": 24,
        },
    },
    PlanTier.ENTERPRISE: {
        "name": "Enterprise",
        "description": "White-label solution for brokerages and large teams",
        "price_monthly_cents": 49900,  # $499.00
        "price_annual_cents": 479040,  # $4,790.40 (20% discount)
        "lead_quota": -1,  # Unlimited
        "query_quota": -1,  # Unlimited
        "features": {
            "lead_management": True,
            "buyer_bot": True,
            "seller_bot": True,
            "market_analysis": True,
            "cma_reports": True,
            "white_label": True,
            "api_access": True,
            "dedicated_support": True,
            "priority_processing": True,
            "custom_integrations": True,
        },
        "limits": {
            "team_members": -1,  # Unlimited
            "concurrent_conversations": -1,  # Unlimited
            "api_calls_per_day": -1,  # Unlimited
            "exports_per_month": -1,  # Unlimited
        },
        "support": {
            "email": True,
            "chat": True,
            "phone": True,
            "response_time_hours": 4,
            "sla": True,
            "dedicated_manager": True,
        },
    },
}


class BillingError(Exception):
    """Base billing error."""

    pass


class PaymentFailedError(BillingError):
    """Raised when payment processing fails."""

    pass


class QuotaExceededError(BillingError):
    """Raised when usage quota is exceeded."""

    pass


class SubscriptionExpiredError(BillingError):
    """Raised when subscription is not active."""

    pass


class InvalidPlanError(BillingError):
    """Raised when an invalid plan is specified."""

    pass


class FeatureNotAvailableError(BillingError):
    """Raised when a feature is not available on the current plan."""

    pass


def load_plans_from_yaml(config_path: Optional[str] = None) -> Dict[PlanTier, Dict[str, Any]]:
    """
    Load plan configurations from YAML file.

    Args:
        config_path: Path to plans.yaml file. If None, uses default location.

    Returns:
        Dictionary of plan configurations
    """
    if config_path is None:
        config_path = os.environ.get("BILLING_CONFIG_PATH", str(Path(__file__).parent.parent / "config" / "plans.yaml"))

    path = Path(config_path)
    if not path.exists():
        return PLAN_CONFIGS

    with open(path, "r") as f:
        yaml_config = yaml.safe_load(f)

    if not yaml_config or "plans" not in yaml_config:
        return PLAN_CONFIGS

    configs = {}
    for plan_key, plan_data in yaml_config["plans"].items():
        try:
            tier = PlanTier(plan_key)
            configs[tier] = plan_data
        except ValueError:
            continue

    return configs if configs else PLAN_CONFIGS


# Cached plan configs (loaded once)
_cached_plans: Optional[Dict[PlanTier, Dict[str, Any]]] = None


def get_plan_config(plan_tier: PlanTier) -> Dict[str, Any]:
    """
    Get configuration for a plan tier.

    Args:
        plan_tier: The plan tier to get configuration for

    Returns:
        Dictionary containing plan configuration

    Raises:
        InvalidPlanError: If plan tier is not found
    """
    global _cached_plans

    if _cached_plans is None:
        _cached_plans = load_plans_from_yaml()

    if plan_tier not in _cached_plans:
        raise InvalidPlanError(f"Invalid plan tier: {plan_tier}")

    return _cached_plans[plan_tier]


def is_feature_available(plan_tier: PlanTier, feature: str) -> bool:
    """
    Check if a feature is available on a plan tier.

    Args:
        plan_tier: The plan tier to check
        feature: The feature name to check

    Returns:
        True if feature is available, False otherwise
    """
    config = get_plan_config(plan_tier)
    return config.get("features", {}).get(feature, False)


def get_plan_price(plan_tier: PlanTier, interval: str = "month") -> int:
    """
    Get price in cents for a plan tier and billing interval.

    Args:
        plan_tier: The plan tier
        interval: "month" or "year"

    Returns:
        Price in cents
    """
    config = get_plan_config(plan_tier)
    if interval == "year":
        return config.get("price_annual_cents", 0)
    return config.get("price_monthly_cents", 0)


def get_lead_quota(plan_tier: PlanTier) -> int:
    """
    Get lead quota for a plan tier.

    Args:
        plan_tier: The plan tier

    Returns:
        Lead quota (-1 = unlimited)
    """
    config = get_plan_config(plan_tier)
    return config.get("lead_quota", 0)


def get_query_quota(plan_tier: PlanTier) -> int:
    """
    Get query quota for a plan tier.

    Args:
        plan_tier: The plan tier

    Returns:
        Query quota (-1 = unlimited)
    """
    config = get_plan_config(plan_tier)
    return config.get("query_quota", 0)


def get_plan_limit(plan_tier: PlanTier, limit_name: str) -> int:
    """
    Get a specific limit for a plan tier.

    Args:
        plan_tier: The plan tier
        limit_name: The limit to check

    Returns:
        Limit value (-1 = unlimited)
    """
    config = get_plan_config(plan_tier)
    return config.get("limits", {}).get(limit_name, 0)


def get_all_plans() -> Dict[PlanTier, Dict[str, Any]]:
    """
    Get all plan configurations.

    Returns:
        Dictionary of all plan configurations
    """
    global _cached_plans

    if _cached_plans is None:
        _cached_plans = load_plans_from_yaml()

    return _cached_plans


def reload_plans() -> None:
    """
    Reload plan configurations from YAML file.

    Call this after updating the plans.yaml file.
    """
    global _cached_plans
    _cached_plans = load_plans_from_yaml()
