"""
GHL Webhook endpoints for Real Estate AI qualification assistant.

Handles incoming webhooks from GHL when contacts need qualification,
processes them through AI conversation flow, and sends responses back via GHL API.

Webhook Flow:
1. Receive GHL webhook (contact tagged "Needs Qualifying")
2. Start AI qualification conversation
3. Send qualifying questions via GHL SMS/email
4. Process responses and calculate lead score
5. Tag lead appropriately and hand off to human when qualified
"""
from fastapi import APIRouter, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
import hashlib
import hmac
import json
import asyncio
from datetime import datetime

from core.config import settings
from services.lead_scorer import LeadScorer
from services.ghl_service import GHLService
from services.claude_service import ClaudeService

router = APIRouter(prefix="/webhooks", tags=["webhooks"])

# Initialize services
lead_scorer = LeadScorer()
ghl_service = GHLService()
claude_service = ClaudeService()


def verify_ghl_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify GHL webhook signature for security.

    Args:
        payload: Raw request body
        signature: X-GHL-Signature header
        secret: Webhook secret from GHL

    Returns:
        True if signature is valid
    """
    if not secret:
        return True  # Skip verification if no secret configured

    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(f"sha256={expected_signature}", signature)


@router.post("/ghl/contact-updated")
async def handle_contact_updated(request: Request):
    """
    Handle GHL contact update webhooks.

    Triggered when:
    - Contact is tagged "Needs Qualifying"
    - Contact responds to messages (conversation continues)
    - Contact reaches qualification threshold (hand off to human)

    Returns:
        200: Webhook processed successfully
        400: Invalid webhook data
        401: Invalid signature
        500: Processing error
    """
    try:
        # Get raw body and signature
        body = await request.body()
        signature = request.headers.get("x-ghl-signature", "")

        # Verify webhook signature
        if settings.ghl_webhook_secret:
            if not verify_ghl_signature(body, signature, settings.ghl_webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")

        # Parse webhook data
        try:
            webhook_data = json.loads(body.decode())
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")

        # Extract event type and contact data
        event_type = webhook_data.get("type")
        contact_data = webhook_data.get("contact", {})
        contact_id = contact_data.get("id")

        if not contact_id:
            raise HTTPException(status_code=400, detail="Missing contact ID")

        # Route to appropriate handler based on event
        if event_type == "ContactUpdate":
            result = await handle_contact_qualification(contact_data)
        elif event_type == "ConversationMessageReceived":
            result = await handle_message_received(webhook_data)
        else:
            # Log unknown event types but don't fail
            print(f"Unknown webhook event type: {event_type}")
            result = {"status": "ignored", "reason": f"Unknown event type: {event_type}"}

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Webhook processing error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal processing error")


async def handle_contact_qualification(contact_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle contact that needs qualification.

    Args:
        contact_data: Contact information from GHL webhook

    Returns:
        Processing result with status and actions taken
    """
    contact_id = contact_data.get("id")
    tags = contact_data.get("tags", [])

    # Check if contact needs qualification
    if "Needs Qualifying" not in tags:
        return {"status": "ignored", "reason": "Contact doesn't need qualification"}

    # Check if AI is already active for this contact
    if "AI Active" in tags:
        return {"status": "ignored", "reason": "AI already active for this contact"}

    # Start qualification process
    try:
        # Tag contact as AI Active
        await ghl_service.add_tag(contact_id, "AI Active")

        # Send initial qualifying message
        initial_message = await claude_service.generate_initial_message(contact_data)
        await ghl_service.send_message(contact_id, initial_message)

        return {
            "status": "started",
            "contact_id": contact_id,
            "action": "AI qualification started",
            "message_sent": True
        }

    except Exception as e:
        print(f"Error starting qualification for {contact_id}: {str(e)}")
        return {
            "status": "error",
            "contact_id": contact_id,
            "error": str(e)
        }


async def handle_message_received(webhook_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle incoming message from contact during qualification.

    Args:
        webhook_data: Full webhook data including message and contact info

    Returns:
        Processing result with response status
    """
    message_data = webhook_data.get("message", {})
    contact_data = webhook_data.get("contact", {})

    contact_id = contact_data.get("id")
    message_text = message_data.get("body", "")
    direction = message_data.get("direction")  # "inbound" or "outbound"

    # Only process inbound messages from contact
    if direction != "inbound":
        return {"status": "ignored", "reason": "Outbound message"}

    # Check if AI is active for this contact
    tags = contact_data.get("tags", [])
    if "AI Active" not in tags:
        return {"status": "ignored", "reason": "AI not active for this contact"}

    try:
        # Get conversation history
        conversation_history = await ghl_service.get_conversation_history(contact_id)

        # Generate AI response
        response_data = await claude_service.process_message(
            message_text=message_text,
            contact_data=contact_data,
            conversation_history=conversation_history
        )

        # Send AI response
        if response_data.get("response_message"):
            await ghl_service.send_message(contact_id, response_data["response_message"])

        # Check if qualification is complete
        if response_data.get("qualification_complete"):
            # Calculate final lead score
            score_result = lead_scorer.calculate_with_reasoning(response_data.get("context", {}))

            # Tag based on score and hand off to human
            await finalize_qualification(contact_id, score_result)

            return {
                "status": "completed",
                "contact_id": contact_id,
                "lead_score": score_result["score"],
                "classification": score_result["classification"],
                "handed_off": True
            }

        return {
            "status": "continued",
            "contact_id": contact_id,
            "response_sent": True,
            "qualification_complete": False
        }

    except Exception as e:
        print(f"Error processing message for {contact_id}: {str(e)}")
        return {
            "status": "error",
            "contact_id": contact_id,
            "error": str(e)
        }


async def finalize_qualification(contact_id: str, score_result: Dict[str, Any]) -> None:
    """
    Finalize qualification process and hand off to human.

    Args:
        contact_id: GHL contact ID
        score_result: Lead scoring results with classification and actions
    """
    classification = score_result["classification"]
    score = score_result["score"]

    # Remove AI tags
    await ghl_service.remove_tag(contact_id, "AI Active")
    await ghl_service.remove_tag(contact_id, "Needs Qualifying")

    # Add classification tag
    if classification == "hot":
        await ghl_service.add_tag(contact_id, "Hot Lead")
        # Notify agent immediately
        await ghl_service.notify_agent(contact_id, f"Hot lead qualified! Score: {score}")
    elif classification == "warm":
        await ghl_service.add_tag(contact_id, "Warm Lead")
    else:
        await ghl_service.add_tag(contact_id, "Cold Lead")

    # Send handoff message
    handoff_message = f"Thank you for the information! I've gathered your requirements and one of our agents will follow up with you soon. Your lead score: {score}/100"
    await ghl_service.send_message(contact_id, handoff_message)


@router.get("/ghl/test")
async def test_webhook():
    """
    Test endpoint to verify webhook is accessible.

    Returns:
        Webhook status and configuration info
    """
    return {
        "status": "active",
        "timestamp": datetime.now().isoformat(),
        "webhook_secret_configured": bool(settings.ghl_webhook_secret),
        "services": {
            "lead_scorer": "available",
            "ghl_service": "available",
            "claude_service": "available"
        }
    }


@router.post("/ghl/manual-trigger")
async def manual_trigger_qualification(contact_id: str):
    """
    Manually trigger qualification for a contact (for testing).

    Args:
        contact_id: GHL contact ID to start qualification

    Returns:
        Trigger result
    """
    try:
        # Simulate contact update webhook
        fake_contact_data = {
            "id": contact_id,
            "tags": ["Needs Qualifying"]
        }

        result = await handle_contact_qualification(fake_contact_data)
        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))