"""Tenant schemas for multi-tenant product suite."""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TenantStatus(str, Enum):
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"


class TenantTier(str, Enum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class TenantLimits(BaseModel):
    """Resource limits per tenant tier."""

    model_config = ConfigDict(frozen=True)

    max_users: int = Field(ge=1, default=5)
    max_queries_per_day: int = Field(ge=0, default=1000)
    storage_gb: float = Field(ge=0, default=1.0)
    max_api_keys: int = Field(ge=1, default=3)
    rate_limit_rpm: int = Field(ge=1, default=100)


# Default limits per tier
TIER_LIMITS: dict[TenantTier, TenantLimits] = {
    TenantTier.FREE: TenantLimits(
        max_users=1, max_queries_per_day=100, storage_gb=0.5, max_api_keys=1, rate_limit_rpm=10
    ),
    TenantTier.STARTER: TenantLimits(
        max_users=5, max_queries_per_day=1000, storage_gb=5.0, max_api_keys=3, rate_limit_rpm=60
    ),
    TenantTier.PRO: TenantLimits(
        max_users=25, max_queries_per_day=50000, storage_gb=50.0, max_api_keys=10, rate_limit_rpm=300
    ),
    TenantTier.ENTERPRISE: TenantLimits(
        max_users=999, max_queries_per_day=999999, storage_gb=500.0, max_api_keys=50, rate_limit_rpm=1000
    ),
}


class TenantBase(BaseModel):
    """Base tenant model with core fields."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
    status: TenantStatus = TenantStatus.TRIAL
    tier: TenantTier = TenantTier.FREE
    stripe_customer_id: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    settings: dict = Field(default_factory=dict)

    @property
    def limits(self) -> TenantLimits:
        """Get the resource limits for this tenant's tier."""
        return TIER_LIMITS[self.tier]


class TenantCreate(BaseModel):
    """Schema for creating a new tenant."""

    name: str = Field(..., min_length=1, max_length=256)
    slug: str = Field(..., min_length=1, max_length=128, pattern=r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$")
    email: str = Field(...)
    plan: TenantTier = TenantTier.FREE

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("Invalid email format")
        return v.lower().strip()


class TenantResponse(TenantBase):
    """Tenant response with usage data."""

    usage_this_period: dict = Field(default_factory=dict)
    limits_info: TenantLimits | None = None
