"""Shared schemas for the portfolio product suite."""

from shared_schemas.auth import (
    APIKeySchema,
    JWTClaims,
    JWTPayload,
    Permission,
)
from shared_schemas.billing import (
    BillingPlan,
    InvoiceLine,
    SubscriptionPlan,
    UsageEvent,
    UsageEventType,
    UsageRecord,
)
from shared_schemas.events import (
    BillingEvent,
    DomainEvent,
    TenantCreated,
    UsageThresholdReached,
)
from shared_schemas.tenant import (
    TenantBase,
    TenantCreate,
    TenantLimits,
    TenantResponse,
    TenantStatus,
    TenantTier,
)
from shared_schemas.validators import (
    validate_tenant_limits,
    validate_weight_sum,
)

__all__ = [
    "TenantBase",
    "TenantCreate",
    "TenantLimits",
    "TenantResponse",
    "TenantStatus",
    "TenantTier",
    "APIKeySchema",
    "JWTClaims",
    "JWTPayload",
    "Permission",
    "BillingPlan",
    "InvoiceLine",
    "SubscriptionPlan",
    "UsageEvent",
    "UsageEventType",
    "UsageRecord",
    "BillingEvent",
    "DomainEvent",
    "TenantCreated",
    "UsageThresholdReached",
    "validate_tenant_limits",
    "validate_weight_sum",
]

__version__ = "0.1.0"
