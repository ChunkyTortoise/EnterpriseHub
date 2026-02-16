"""Billing and subscription schemas."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import uuid4

from pydantic import BaseModel, Field, computed_field

from shared_schemas.tenant import TenantLimits, TenantTier


class BillingInterval(str, Enum):
    """Billing frequency."""

    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionPlan(BaseModel):
    """A subscription plan tied to a tier."""

    id: str
    name: str
    stripe_price_id: str
    tier: TenantTier
    interval: BillingInterval
    price_cents: int
    features: list[str] = Field(default_factory=list)
    limits: TenantLimits


class UsageEventType(str, Enum):
    """Types of billable usage events."""

    RAG_QUERY = "rag_query"
    VOICE_MINUTE = "voice_minute"
    MCP_CALL = "mcp_call"
    PIPELINE_RUN = "pipeline_run"


class UsageEvent(BaseModel):
    """A billable usage event."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    event_type: UsageEventType
    quantity: float = 1.0
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict)


class UsageRecord(BaseModel):
    """Metered usage for billing."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    tenant_id: str
    metric: str
    quantity: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    stripe_subscription_item_id: str | None = None
    reported_to_stripe: bool = False


class InvoiceLine(BaseModel):
    """A single line on an invoice."""

    description: str
    quantity: float
    unit_price_cents: int
    currency: str = "USD"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_cents(self) -> int:
        return int(self.quantity * self.unit_price_cents)
