"""Stripe Checkout API routes for one-time digital product purchases.

Endpoints:
  POST /checkout/create-session  — create a Stripe Checkout session
  POST /checkout/webhook         — handle checkout.session.completed events
"""

import os

import stripe
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel

from ghl_real_estate_ai.config.stripe_products import PRODUCT_CATALOG
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/checkout", tags=["checkout"])

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")


# ---------- Request / Response schemas ----------


class CreateCheckoutSessionRequest(BaseModel):
    product_slug: str
    success_url: str = ""
    cancel_url: str = ""


class CheckoutSessionResponse(BaseModel):
    session_id: str
    checkout_url: str


# ---------- Endpoints ----------


@router.post("/create-session", response_model=CheckoutSessionResponse)
async def create_checkout_session(request: CreateCheckoutSessionRequest):
    """Create a Stripe Checkout session for a one-time product purchase."""
    product = PRODUCT_CATALOG.get(request.product_slug)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product '{request.product_slug}' not found",
        )

    price_id = product.get("stripe_price_id")
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Product '{request.product_slug}' has no Stripe price configured. "
                "Run scripts/create_stripe_products.py first."
            ),
        )

    success_url = request.success_url or os.getenv(
        "STRIPE_CHECKOUT_SUCCESS_URL",
        "http://localhost:8000/checkout_success.html?session_id={CHECKOUT_SESSION_ID}",
    )
    cancel_url = request.cancel_url or os.getenv(
        "STRIPE_CHECKOUT_CANCEL_URL",
        "http://localhost:8000/checkout.html",
    )

    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"product_slug": request.product_slug},
        )
    except stripe.error.StripeError as e:
        logger.error("Stripe error creating checkout session: %s", e)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Payment provider error: {e!s}",
        )

    logger.info(
        "Checkout session created",
        extra={
            "session_id": session.id,
            "product_slug": request.product_slug,
            "price_cents": product["price_cents"],
        },
    )

    return CheckoutSessionResponse(session_id=session.id, checkout_url=session.url)


@router.post("/webhook")
async def checkout_webhook(request: Request):
    """Handle Stripe webhook events for checkout session completions."""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured")
        raise HTTPException(status_code=500, detail="Webhook secret not configured")

    try:
        event = stripe.Webhook.construct_event(payload, signature, webhook_secret)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        customer_email = session.get("customer_details", {}).get("email", "unknown")
        product_slug = session.get("metadata", {}).get("product_slug", "unknown")
        amount_total = session.get("amount_total", 0)

        logger.info(
            "Checkout completed: %s purchased %s ($%.2f)",
            customer_email,
            product_slug,
            amount_total / 100,
            extra={
                "event_id": event["id"],
                "session_id": session["id"],
                "customer_email": customer_email,
                "product_slug": product_slug,
                "amount_total": amount_total,
                "payment_status": session.get("payment_status"),
            },
        )

    return {"status": "ok"}
