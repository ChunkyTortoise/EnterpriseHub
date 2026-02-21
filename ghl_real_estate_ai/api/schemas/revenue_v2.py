"""Strict response contracts for revenue-critical v2 APIs."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field


class ResponseSource(str, Enum):
    DATABASE = "database"
    CACHE = "cache"
    LIVE_PROVIDER = "live_provider"


class RevenueError(BaseModel):
    error_code: str
    error_message: str
    recoverable: bool
    suggested_action: str
    correlation_id: str


class RevenueV2Envelope(BaseModel):
    """Single strict envelope for all v2 monetized responses."""

    source: ResponseSource
    data_freshness_seconds: int = Field(ge=0)
    generated_at: datetime
    correlation_id: str
    data: Dict[str, Any]
    error: Optional[RevenueError] = None

    model_config = ConfigDict(extra="forbid")


class RevenueSSEEvent(BaseModel):
    event: str
    correlation_id: str
    payload: Dict[str, Any]

    model_config = ConfigDict(extra="forbid")


def new_correlation_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
