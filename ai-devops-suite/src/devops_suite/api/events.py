"""Telemetry event ingestion API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/events", tags=["events"])


class EventType(str, Enum):
    AGENT_START = "agent.start"
    AGENT_END = "agent.end"
    AGENT_ERROR = "agent.error"
    LLM_CALL = "llm.call"
    TOOL_CALL = "tool.call"
    TOKEN_USAGE = "token.usage"


class AgentEventIn(BaseModel):
    event_type: EventType
    agent_id: str
    trace_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float | None = None
    model: str | None = None
    tokens_input: int | None = None
    tokens_output: int | None = None
    cost_usd: float | None = None
    status: str | None = None
    error_type: str | None = None
    error_message: str | None = None
    metadata: dict | None = None


class IngestResponse(BaseModel):
    accepted: int


@router.post("", response_model=IngestResponse)
async def ingest_event(event: AgentEventIn) -> IngestResponse:
    return IngestResponse(accepted=1)


@router.post("/batch", response_model=IngestResponse)
async def ingest_events_batch(events: list[AgentEventIn]) -> IngestResponse:
    if len(events) > 1000:
        raise HTTPException(status_code=400, detail="Max 1000 events per batch")
    return IngestResponse(accepted=len(events))
