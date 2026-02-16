"""Billing and usage schemas for Stripe metered billing."""

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class UsageEventType(str, Enum):
    VOICE_MINUTE = "voice_minute"
    RAG_QUERY = "rag_query"
    SCRAPE_REQUEST = "scrape_request"
    PROMPT_EVALUATION = "prompt_evaluation"
    AGENT_INVOCATION = "agent_invocation"


class UsageEvent(BaseModel):
    """Single usage event reported to Stripe."""

    tenant_id: str
    event_type: UsageEventType
    quantity: float = Field(gt=0)
    metadata: dict = Field(default_factory=dict)
    timestamp: str | None = None  # ISO 8601; Stripe uses Unix


class BillingPlan(BaseModel):
    """Billing plan definition."""

    name: str
    stripe_price_id: str
    features: dict = Field(default_factory=dict)
    limits: dict = Field(default_factory=dict)  # e.g., {"voice_minutes": 500}


class SubscriptionPlan(BaseModel):
    """Subscription plan with tier mapping."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    name: str = Field(..., min_length=1)
    stripe_price_id: str
    tier: str  # maps to TenantTier
    monthly_price_cents: int = Field(ge=0)
    features: dict = Field(default_factory=dict)
    included_usage: dict = Field(default_factory=dict)  # e.g., {"rag_queries": 10000}


class UsageRecord(BaseModel):
    """Aggregated usage record for a tenant."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(default_factory=uuid4)
    tenant_id: UUID
    metric: UsageEventType
    quantity: float = Field(ge=0)
    period_start: datetime
    period_end: datetime
    reported_to_stripe: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InvoiceLine(BaseModel):
    """Single line item on an invoice."""

    description: str
    quantity: float = Field(ge=0)
    unit_price_cents: int = Field(ge=0)
    total_cents: int = Field(ge=0)
    metric: UsageEventType | None = None
