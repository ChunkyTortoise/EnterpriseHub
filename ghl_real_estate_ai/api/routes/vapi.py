"""
Vapi Tool Integration for Jorge's Voice AI.

Provides endpoints for Vapi.ai to call tools during voice conversations:
- check-availability: Checks Jorge's calendar for open slots.
- book-tour: Finalizes the appointment in GHL.
"""

import json
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.calendar_scheduler import (
    AppointmentType,
    CalendarScheduler,
    get_smart_scheduler,
)
from ghl_real_estate_ai.services.security_framework import verify_webhook

logger = get_logger(__name__)
router = APIRouter(prefix="/vapi/tools", tags=["vapi"])


def get_vapi_scheduler() -> CalendarScheduler:
    """Dependency wrapper to avoid FastAPI inspecting get_smart_scheduler params."""
    return get_smart_scheduler()


class ToolCallPayload(BaseModel):
    """Payload from Vapi tool call."""

    toolCall: Dict[str, Any]
    call: Optional[Dict[str, Any]] = None


@router.post("/check-availability")
@verify_webhook("vapi")
async def vapi_check_availability(
    request: Request, payload: ToolCallPayload, scheduler: CalendarScheduler = Depends(get_vapi_scheduler)
):
    """
    Vapi Tool: Checks Jorge's calendar for open slots.
    """
    logger.info("Vapi tool call: check-availability")

    tool_call = payload.toolCall
    args = tool_call.get("function", {}).get("arguments", {})

    # Map Vapi's 'date' argument if provided
    # Note: CalendarScheduler currently looks ahead from 'now'
    # We can refine this to handle specific dates if needed.

    try:
        # Default to property showing for Vapi tour inquiries
        slots = await scheduler.get_available_slots(appointment_type=AppointmentType.PROPERTY_SHOWING, days_ahead=5)

        # Format slots for AI to read easily
        formatted_slots = [s.format_for_lead() for s in slots]

        result = {"status": "success", "slots": formatted_slots}

        return {"results": [{"toolCallId": tool_call.get("id"), "result": json.dumps(result)}]}
    except Exception as e:
        logger.error(f"Error in vapi_check_availability: {e}")
        return {"results": [{"toolCallId": tool_call.get("id"), "error": str(e)}]}


@router.post("/book-tour")
@verify_webhook("vapi")
async def vapi_book_tour(
    request: Request, payload: ToolCallPayload, scheduler: CalendarScheduler = Depends(get_vapi_scheduler)
):
    """
    Vapi Tool: Finalizes the appointment in GHL.
    """
    logger.info("Vapi tool call: book-tour")

    tool_call = payload.toolCall
    args = tool_call.get("function", {}).get("arguments", {})

    contact_id = args.get("contact_id")
    slot_time_str = args.get("slot_time")
    property_address = args.get("property_address", "Private Viewing")

    if not contact_id:
        # Try to find contact ID from call metadata if provided by Vapi
        if payload.call and payload.call.get("customer"):
            # This would require a lookup service
            logger.warning("contact_id missing in Vapi call, metadata lookup not yet implemented")
            pass

    if not contact_id or not slot_time_str:
        return {"results": [{"toolCallId": tool_call.get("id"), "error": "Missing contact_id or slot_time"}]}

    try:
        # For Vapi bookings, we might need a dummy lead score if it bypasses standard flow
        # Or we assume they are already qualified if the AI is offering booking.
        # We'll use a score of 5 to pass the internal validation.

        # We need to find the TimeSlot object or create one from the string
        # For now, we'll try to book using the GHL client directly through scheduler
        # or adapt scheduler to take raw times.

        # NOTE: book_appointment expects a TimeSlot object.
        # In a real integration, we'd find the matching TimeSlot from the previous check.

        # For prototype parity with main.py, we'll implement a direct booking
        from datetime import datetime

        try:
            start_time = datetime.fromisoformat(slot_time_str.replace("Z", "+00:00"))
        except ValueError:
            # Handle human readable or other formats if needed
            raise HTTPException(status_code=400, detail="Invalid time format")

        calendar_response = await scheduler.ghl_client.create_appointment(
            contact_id=contact_id,
            calendar_id=scheduler.calendar_id,
            start_time=start_time.isoformat(),
            title=f"Viewing: {property_address} (Voice AI)",
            assigned_user_id=None,  # Default to location default
        )

        result = {
            "status": "success",
            "confirmation": "Appointment booked successfully.",
            "appointment_id": calendar_response.get("id"),
        }

        # --- ESCALATION CONFIRMATION (Phase 7) ---
        try:
            from ghl_real_estate_ai.core.conversation_manager import ConversationManager
            from ghl_real_estate_ai.services.jorge.jorge_seller_engine import JorgeSellerEngine

            # Get location_id from args or fallback to scheduler's client
            location_id = args.get("location_id") or scheduler.ghl_client.location_id

            if location_id:
                conv_mgr = ConversationManager()
                jorge_engine = JorgeSellerEngine(conv_mgr, scheduler.ghl_client)
                await jorge_engine.handle_vapi_booking(contact_id, location_id, result)
                logger.info(f"✅ Triggered Jorge escalation confirmation for {contact_id}")
        except Exception as jorge_e:
            logger.error(f"Failed to trigger Jorge escalation confirmation: {jorge_e}")

        return {"results": [{"toolCallId": tool_call.get("id"), "result": json.dumps(result)}]}
    except Exception as e:
        logger.error(f"Error in vapi_book_tour: {e}")
        return {"results": [{"toolCallId": tool_call.get("id"), "error": str(e)}]}
