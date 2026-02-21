"""Stripe webhook handler with signature verification."""

from __future__ import annotations

import logging
import os

import stripe
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/stripe")
async def stripe_webhook(request: Request) -> JSONResponse:
    """Handle Stripe webhook events with signature verification.

    Requires STRIPE_WEBHOOK_SECRET env var (or RAG_STRIPE_WEBHOOK_SECRET).
    """
    webhook_secret = os.environ.get(
        "STRIPE_WEBHOOK_SECRET",
        os.environ.get("RAG_STRIPE_WEBHOOK_SECRET", ""),
    )
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

    if event_type == "invoice.payment_succeeded":
        logger.info("Payment succeeded for customer %s", event["data"]["object"].get("customer"))
    elif event_type == "invoice.payment_failed":
        logger.warning("Payment failed for customer %s", event["data"]["object"].get("customer"))
    elif event_type == "customer.subscription.deleted":
        logger.info(
            "Subscription cancelled for customer %s", event["data"]["object"].get("customer")
        )

    return JSONResponse(status_code=200, content={"status": "ok"})
