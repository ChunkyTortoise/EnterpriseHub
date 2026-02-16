"""Domain events for cross-service communication."""

from datetime import datetime, timezone
from uuid import UUID, uuid4

from pydantic import BaseModel, Field


class DomainEvent(BaseModel):
    """Base class for all domain events."""

    event_id: UUID = Field(default_factory=uuid4)
    event_type: str = ""
    tenant_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict = Field(default_factory=dict)

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        if not cls.__dict__.get("event_type"):
            cls.model_fields["event_type"].default = cls.__name__


class TenantCreated(DomainEvent):
    """Emitted when a new tenant is created."""

    event_type: str = "TenantCreated"
    tenant_name: str
    tier: str
    email: str


class BillingEvent(DomainEvent):
    """Emitted for billing-related state changes."""

    event_type: str = "BillingEvent"
    action: str  # "subscription_created", "payment_failed", "usage_reported"
    stripe_event_id: str | None = None
    amount_cents: int | None = None


class UsageThresholdReached(DomainEvent):
    """Emitted when a tenant approaches or exceeds usage limits."""

    event_type: str = "UsageThresholdReached"
    metric: str
    current_usage: float
    limit: float
    percentage: float = Field(ge=0, le=200)
