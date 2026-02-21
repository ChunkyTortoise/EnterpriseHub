"""Twilio and Stripe webhook handlers."""

from __future__ import annotations

import logging
import os

import stripe
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

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


@router.post("/stripe")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events with signature verification.

    Requires STRIPE_WEBHOOK_SECRET env var to be set.
    """
    webhook_secret = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        return JSONResponse(status_code=500, content={"error": "Webhook secret not configured"})

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        logger.warning("Invalid Stripe webhook payload")
        return JSONResponse(status_code=400, content={"error": "Invalid payload"})
    except stripe.SignatureVerificationError:
        logger.warning("Invalid Stripe webhook signature")
        return JSONResponse(status_code=400, content={"error": "Invalid signature"})

    event_type = event.get("type", "unknown")
    logger.info("Stripe webhook received: type=%s, id=%s", event_type, event.get("id"))

    # Handle specific event types
    if event_type == "invoice.payment_succeeded":
        logger.info("Payment succeeded for customer %s", event["data"]["object"].get("customer"))
    elif event_type == "invoice.payment_failed":
        logger.warning("Payment failed for customer %s", event["data"]["object"].get("customer"))
    elif event_type == "customer.subscription.deleted":
        logger.info(
            "Subscription cancelled for customer %s", event["data"]["object"].get("customer")
        )

    return JSONResponse(status_code=200, content={"status": "ok"})
