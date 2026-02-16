"""Call management API routes."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/calls", tags=["calls"])


class OutboundCallRequest(BaseModel):
    to_number: str
    bot_type: str = "lead"
    agent_persona_id: str | None = None
    context: dict[str, Any] = Field(default_factory=dict)


class CallResponse(BaseModel):
    id: str
    tenant_id: str
    twilio_call_sid: str | None = None
    direction: str
    from_number: str
    to_number: str
    status: str
    bot_type: str
    duration_seconds: float = 0
    lead_score: float | None = None
    sentiment_scores: dict = Field(default_factory=dict)
    appointment_booked: bool = False
    created_at: str | None = None
    ended_at: str | None = None


class PaginatedCallsResponse(BaseModel):
    items: list[CallResponse]
    total: int
    page: int
    size: int


@router.post("/inbound")
async def handle_inbound_call(request: Request) -> Response:
    """Handle inbound call webhook from Twilio.

    Returns TwiML that connects the call to our WebSocket voice pipeline.
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    from_number = form_data.get("From", "")
    to_number = form_data.get("To", "")

    # Generate TwiML to connect to our WebSocket
    twilio_handler = request.app.state.twilio_handler
    twiml = twilio_handler.generate_stream_twiml(call_id=call_sid)

    return Response(content=twiml, media_type="application/xml")


@router.post("/outbound", response_model=CallResponse)
async def initiate_outbound_call(
    body: OutboundCallRequest,
    request: Request,
) -> dict[str, Any]:
    """Initiate an outbound call via Twilio."""
    call_id = str(uuid.uuid4())

    twilio_handler = request.app.state.twilio_handler
    result = await twilio_handler.initiate_outbound_call(
        to_number=body.to_number,
        call_id=call_id,
    )

    return {
        "id": call_id,
        "tenant_id": "",  # Populated from auth
        "twilio_call_sid": result.get("call_sid"),
        "direction": "outbound",
        "from_number": twilio_handler.phone_number,
        "to_number": body.to_number,
        "status": "initiated",
        "bot_type": body.bot_type,
    }


@router.get("/{call_id}", response_model=CallResponse)
async def get_call(call_id: str, request: Request) -> dict[str, Any]:
    """Get call details by ID."""
    db = request.app.state.db_session
    from voice_ai.telephony.call_manager import CallManager

    manager = CallManager(db)
    call = await manager.get_call(call_id)
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")

    return {
        "id": str(call.id),
        "tenant_id": str(call.tenant_id),
        "twilio_call_sid": call.twilio_call_sid,
        "direction": call.direction.value if call.direction else "",
        "from_number": call.from_number or "",
        "to_number": call.to_number or "",
        "status": call.status.value if call.status else "",
        "bot_type": call.bot_type or "",
        "duration_seconds": call.duration_seconds or 0,
        "lead_score": call.lead_score,
        "sentiment_scores": call.sentiment_scores or {},
        "appointment_booked": call.appointment_booked or False,
        "created_at": str(call.created_at) if call.created_at else None,
        "ended_at": str(call.ended_at) if call.ended_at else None,
    }


@router.get("", response_model=PaginatedCallsResponse)
async def list_calls(
    request: Request,
    status: str | None = None,
    page: int = 1,
    size: int = 50,
) -> dict[str, Any]:
    """List calls with pagination and optional status filter."""
    # MVP: return empty paginated response
    return {
        "items": [],
        "total": 0,
        "page": page,
        "size": size,
    }
