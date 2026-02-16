"""Tenant configuration schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class TenantTier(str, Enum):
    """Subscription tier for a tenant."""

    FREE = "FREE"
    STARTER = "STARTER"
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"


class TenantLimits(BaseModel):
    """Resource limits for a tenant."""

    model_config = ConfigDict(frozen=True)

    max_users: int = 1
    max_queries_per_day: int = 100
    max_storage_gb: float = 1.0
    max_api_keys: int = 1


class TenantConfig(BaseModel):
    """Full tenant configuration."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    tier: TenantTier = TenantTier.FREE
    limits: TenantLimits | None = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def _set_default_limits(self) -> TenantConfig:
        if self.limits is None:
            from shared_schemas.validators import get_default_limits

            object.__setattr__(self, "limits", get_default_limits(self.tier))
        return self
