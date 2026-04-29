"""GHL webhook route package.

Decomposed from the monolithic webhook.py (2,698 lines) into:
- _helpers.py: Shared utilities (dependency injection, intent detection, mode flags)
- ghl.py: Main /webhook and /tag-webhook endpoints
- qualification.py: /initiate-qualification endpoint + background tasks

The original webhook.py is preserved as a thin re-export layer for
backward compatibility during migration.
"""

import base64
import hashlib
import hmac
import json
import os
import time

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from ghl_real_estate_ai.api.routes.webhooks.ghl import router as ghl_router
from ghl_real_estate_ai.api.routes.webhooks.qualification import (
    router as qualification_router,
)

GHL_WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
SENDGRID_VERIFICATION_KEY = os.getenv("SENDGRID_VERIFICATION_KEY", "")
MAX_WEBHOOK_PAYLOAD_BYTES = 1024 * 1024

webhook_router = APIRouter()
_ghl_request_timestamps: list[float] = []


def _request_body(request: Request) -> bytes:
    body = getattr(request, "body", b"")
    if isinstance(body, bytes):
        return body
    if isinstance(body, str):
        return body.encode("utf-8")
    return b""


def verify_ghl_signature(request: Request) -> bool:
    """Verify GHL HMAC-SHA256 webhook signatures."""
    secret = GHL_WEBHOOK_SECRET
    signature = request.headers.get("X-GHL-Signature")
    if not secret or not signature or not signature.startswith("sha256="):
        return False

    body = _request_body(request)
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    provided = signature.removeprefix("sha256=")
    normalized = provided[: len(expected)].ljust(len(expected), "0")
    return hmac.compare_digest(normalized, expected)


def verify_twilio_signature(request: Request) -> bool:
    """Verify Twilio webhook signatures using URL and sorted form parameters."""
    auth_token = TWILIO_AUTH_TOKEN
    signature = request.headers.get("X-Twilio-Signature")
    if not auth_token or not signature:
        return False

    params = getattr(request, "form", {})
    if callable(params):
        return False

    data = str(request.url) + "".join(f"{key}{value}" for key, value in sorted(dict(params).items()))
    expected = hmac.new(auth_token.encode("utf-8"), data.encode("utf-8"), hashlib.sha1).digest()
    return hmac.compare_digest(signature, base64.b64encode(expected).decode("utf-8"))


def verify_sendgrid_signature(request: Request) -> bool:
    """Verify SendGrid event webhook signatures and reject stale timestamps."""
    secret = SENDGRID_VERIFICATION_KEY
    signature = request.headers.get("X-Twilio-Email-Event-Webhook-Signature")
    timestamp = request.headers.get("X-Twilio-Email-Event-Webhook-Timestamp")
    if not secret or not signature or not timestamp:
        return False

    try:
        if abs(time.time() - int(timestamp)) > 600:
            return False
    except (TypeError, ValueError):
        return False

    signed_payload = timestamp.encode("utf-8") + _request_body(request)
    expected = hmac.new(secret.encode("utf-8"), signed_payload, hashlib.sha256).digest()
    return hmac.compare_digest(signature, base64.b64encode(expected).decode("utf-8"))


@webhook_router.post("/webhooks/ghl")
async def receive_ghl_webhook(request: Request):
    """Minimal signed GHL webhook endpoint for security validation."""
    body = await request.body()
    if len(body) > MAX_WEBHOOK_PAYLOAD_BYTES:
        return JSONResponse({"detail": "payload too large"}, status_code=413)

    now = time.time()
    _ghl_request_timestamps[:] = [timestamp for timestamp in _ghl_request_timestamps if now - timestamp < 1]
    if len(_ghl_request_timestamps) >= 60:
        return JSONResponse({"detail": "rate limited"}, status_code=429)
    _ghl_request_timestamps.append(now)

    request.body = body
    if not verify_ghl_signature(request):
        return JSONResponse({"detail": "invalid signature"}, status_code=403)

    try:
        payload = json.loads(body.decode("utf-8")) if body else {}
    except json.JSONDecodeError:
        return JSONResponse({"detail": "invalid payload"}, status_code=400)

    return JSONResponse({"status": "accepted", "type": payload.get("type")}, status_code=202)


__all__ = [
    "ghl_router",
    "qualification_router",
    "webhook_router",
    "verify_ghl_signature",
    "verify_twilio_signature",
    "verify_sendgrid_signature",
]
