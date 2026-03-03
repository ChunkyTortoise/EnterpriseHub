"""Strict response contracts for revenue-critical v2 APIs."""

from datetime import date, datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResponseSource(str, Enum):
    DATABASE = "database"
    CACHE = "cache"
    LIVE_PROVIDER = "live_provider"


class ErrorEnvelope(BaseModel):
    code: str
    message: str
    correlation_id: str
    retryable: bool
    details: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(extra="forbid")


class ResponseMeta(BaseModel):
    source: ResponseSource
    correlation_id: str
    generated_at: datetime
    freshness_seconds: int = Field(ge=0)

    model_config = ConfigDict(extra="forbid")


class RevenueV2Envelope(BaseModel):
    """Strict envelope for monetized v2 routes."""

    data: Dict[str, Any]
    meta: ResponseMeta
    error: Optional[ErrorEnvelope] = None

    model_config = ConfigDict(extra="forbid")


class RevenueSSEEvent(BaseModel):
    event: str
    correlation_id: str
    payload: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


class PilotKPIRecord(BaseModel):
    tenant_id: str
    week_start: date
    leads_received: int = Field(ge=0)
    qualified_leads: int = Field(ge=0)
    response_sla_pct: float = Field(ge=0.0, le=100.0)
    appointments_booked: int = Field(ge=0)
    cost_per_qualified_lead: float = Field(ge=0.0)

    model_config = ConfigDict(extra="forbid")


class OutcomeEvent(BaseModel):
    event_id: str
    tenant_id: str
    lead_id: str
    event_type: str
    event_value: Optional[float] = None
    timestamp: datetime

    model_config = ConfigDict(extra="forbid")


def new_correlation_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
