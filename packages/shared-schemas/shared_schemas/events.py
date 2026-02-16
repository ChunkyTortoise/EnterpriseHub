"""Domain event schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from shared_schemas.tenant import TenantTier


class DomainEvent(BaseModel):
    """Base domain event."""

    event_id: str = Field(default_factory=lambda: str(uuid4()))
    event_type: str
    tenant_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    payload: dict[str, Any] = Field(default_factory=dict)


class TenantCreated(DomainEvent):
    """Emitted when a new tenant is created."""

    event_type: str = "tenant.created"


class SubscriptionChanged(DomainEvent):
    """Emitted when a tenant's subscription tier changes."""

    event_type: str = "subscription.changed"
    old_tier: TenantTier
    new_tier: TenantTier


class UsageLimitReached(DomainEvent):
    """Emitted when a tenant hits a usage limit."""

    event_type: str = "usage.limit_reached"
    metric: str
    current_value: float
