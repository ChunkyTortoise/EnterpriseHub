"""shared-schemas — Multi-tenant schemas for AI portfolio products."""

from shared_schemas.auth import APIKeyConfig, JWTClaims, Permission
from shared_schemas.billing import BillingInterval, InvoiceLine, SubscriptionPlan, UsageEvent, UsageEventType, UsageRecord
from shared_schemas.events import DomainEvent, SubscriptionChanged, TenantCreated, UsageLimitReached
from shared_schemas.tenant import TenantConfig, TenantLimits, TenantTier
from shared_schemas.validators import get_default_limits, validate_tenant_limits

__all__ = [
    "APIKeyConfig",
    "BillingInterval",
    "DomainEvent",
    "InvoiceLine",
    "JWTClaims",
    "Permission",
    "SubscriptionChanged",
    "SubscriptionPlan",
    "TenantConfig",
    "TenantCreated",
    "TenantLimits",
    "TenantTier",
    "UsageEvent",
    "UsageEventType",
    "UsageLimitReached",
    "UsageRecord",
    "get_default_limits",
    "validate_tenant_limits",
]

__version__ = "0.1.0"
