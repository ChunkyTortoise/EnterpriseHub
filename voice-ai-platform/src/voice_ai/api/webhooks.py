"""Twilio status callback handler."""

from __future__ import annotations

import logging
from typing import Any

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/webhooks", tags=["webhooks"])

# Map Twilio status to our CallStatus enum values
TWILIO_STATUS_MAP = {
    "initiated": "initiated",
    "ringing": "ringing",
    "in-progress": "in_progress",
    "completed": "completed",
    "failed": "failed",
    "busy": "failed",
    "no-answer": "no_answer",
    "canceled": "failed",
}


@router.post("/twilio/status")
async def twilio_status_callback(request: Request) -> dict[str, str]:
    """Handle Twilio call status callbacks.

    Twilio sends status updates as the call progresses:
    initiated -> ringing -> in-progress -> completed
    """
    form_data = await request.form()
    call_sid = form_data.get("CallSid", "")
    call_status = form_data.get("CallStatus", "")
    call_duration = form_data.get("CallDuration", "0")

    logger.info(
        "Twilio status callback: sid=%s, status=%s, duration=%s",
        call_sid,
        call_status,
        call_duration,
    )

    our_status = TWILIO_STATUS_MAP.get(call_status)
    if our_status:
        logger.info("Mapped status: %s -> %s for call %s", call_status, our_status, call_sid)

    return {"status": "ok"}
