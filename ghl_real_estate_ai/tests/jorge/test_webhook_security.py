"""Webhook signature security tests for GHL webhook endpoints.

Tests cover:
- Valid HMAC-SHA256 signature accepted
- Invalid signature rejected with 401
- Missing signature rejected with 401
- Static shared secret accepted (GHL Custom Webhook action fallback)
- Body tampering detected
- verify_webhook decorator integration

Uses the same pattern as tests/unit/test_security_framework.py for
settings mocking and SecurityFramework instantiation.
"""

import hashlib
import hmac as hmac_module
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

# ---------------------------------------------------------------------------
# Mock settings before importing SecurityFramework (same pattern as
# tests/unit/test_security_framework.py)
# ---------------------------------------------------------------------------
TEST_WEBHOOK_SECRET = "test-webhook-secret-32chars-min!"

_settings_defaults = {
    "jwt_secret_key": "test-jwt-secret-key-for-testing-only-minimum-32-chars",
    "redis_url": "redis://localhost:6379/15",
    "ghl_webhook_secret": TEST_WEBHOOK_SECRET,
    "apollo_webhook_secret": "apollo-test-secret",
    "twilio_webhook_secret": "twilio-test-secret",
    "sendgrid_webhook_secret": "sendgrid-test-secret",
    "vapi_webhook_secret": "vapi-test-secret",
    "retell_webhook_secret": "retell-test-secret",
    "environment": "testing",
}

_mock_settings = MagicMock()
for k, v in _settings_defaults.items():
    setattr(_mock_settings, k, v)

with patch("ghl_real_estate_ai.services.security_framework.settings", _mock_settings):
    from ghl_real_estate_ai.services.security_framework import (
        SecurityFramework,
        verify_webhook,
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _compute_hmac_signature(secret: str, payload: bytes) -> str:
    """Compute a valid HMAC-SHA256 signature for the given payload."""
    return hmac_module.new(secret.encode(), payload, hashlib.sha256).hexdigest()


def _make_mock_request(headers: dict = None, client_host: str = "127.0.0.1"):
    """Create a mock FastAPI Request."""
    request = MagicMock()
    request.headers = headers or {}
    request.client = MagicMock()
    request.client.host = client_host
    request.url = MagicMock()
    request.url.path = "/api/ghl/webhook"
    request.method = "POST"
    request.state = MagicMock()
    return request


@pytest.fixture
def security():
    """Create a SecurityFramework with test webhook secrets."""
    with patch("ghl_real_estate_ai.services.security_framework.settings", _mock_settings):
        fw = SecurityFramework(redis_url="redis://localhost:6379/15")
    fw.config.webhook_signing_secrets = {
        "ghl": TEST_WEBHOOK_SECRET,
        "apollo": "apollo-test-secret",
        "twilio": "twilio-test-secret",
        "sendgrid": "sendgrid-test-secret",
        "vapi": "vapi-test-secret",
        "retell": "retell-test-secret",
    }
    return fw


# ---------------------------------------------------------------------------
# /webhook endpoint: valid signature
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_valid_hmac_signature_accepted(security):
    """Valid HMAC-SHA256 signature should be accepted."""
    body = json.dumps({
        "contact_id": "contact-123",
        "location_id": "loc-456",
        "message": "I want to buy a house",
    }).encode()
    signature = _compute_hmac_signature(TEST_WEBHOOK_SECRET, body)
    request = _make_mock_request(headers={"X-GHL-Signature": signature})

    result = security._verify_ghl_signature(request, body)
    assert result is True


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_invalid_signature_rejected(security):
    """Wrong HMAC signature should return False (invalid)."""
    body = json.dumps({
        "contact_id": "contact-123",
        "message": "Hello",
    }).encode()
    request = _make_mock_request(headers={"X-GHL-Signature": "definitely-not-valid"})

    result = security._verify_ghl_signature(request, body)
    assert result is False


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_missing_signature_raises_401(security):
    """Missing X-GHL-Signature header should raise HTTPException(401)."""
    body = json.dumps({"contact_id": "contact-123"}).encode()
    request = _make_mock_request(headers={})

    with pytest.raises(HTTPException) as exc_info:
        security._verify_ghl_signature(request, body)
    assert exc_info.value.status_code == 401


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_static_secret_accepted(security):
    """GHL Custom Webhook actions send the raw secret as the signature.
    This should be accepted as valid (fallback path)."""
    body = json.dumps({
        "contact_id": "contact-123",
        "message": "Hello from custom webhook action",
    }).encode()
    # Send the raw secret as the signature (GHL Custom Webhook behavior)
    request = _make_mock_request(headers={"X-GHL-Signature": TEST_WEBHOOK_SECRET})

    result = security._verify_ghl_signature(request, body)
    assert result is True


# ---------------------------------------------------------------------------
# /tag-webhook endpoint: signature verification
# (Uses same _verify_ghl_signature, but we test distinct payloads)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.jorge
def test_tag_webhook_valid_signature_accepted(security):
    """Valid signature on tag-webhook payload should be accepted."""
    body = json.dumps({
        "contact_id": "contact-789",
        "location_id": "loc-456",
        "tag": "Needs Qualifying",
    }).encode()
    signature = _compute_hmac_signature(TEST_WEBHOOK_SECRET, body)
    request = _make_mock_request(headers={"X-GHL-Signature": signature})
    request.url.path = "/api/ghl/tag-webhook"

    result = security._verify_ghl_signature(request, body)
    assert result is True


@pytest.mark.unit
@pytest.mark.jorge
def test_tag_webhook_invalid_signature_rejected(security):
    """Invalid signature on tag-webhook should return False."""
    body = json.dumps({
        "contact_id": "contact-789",
        "tag": "Needs Qualifying",
    }).encode()
    request = _make_mock_request(headers={"X-GHL-Signature": "bad-signature"})
    request.url.path = "/api/ghl/tag-webhook"

    result = security._verify_ghl_signature(request, body)
    assert result is False


@pytest.mark.unit
@pytest.mark.jorge
def test_tag_webhook_missing_signature_raises_401(security):
    """Missing signature on tag-webhook should raise HTTPException(401)."""
    body = json.dumps({"tag": "Buyer-Lead"}).encode()
    request = _make_mock_request(headers={})
    request.url.path = "/api/ghl/tag-webhook"

    with pytest.raises(HTTPException) as exc_info:
        security._verify_ghl_signature(request, body)
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Body tampering detection
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_tampered_body_rejected(security):
    """If the body is tampered after signing, the signature should not match."""
    original_body = json.dumps({"contact_id": "c-123", "amount": 100}).encode()
    signature = _compute_hmac_signature(TEST_WEBHOOK_SECRET, original_body)

    # Tamper with the body
    tampered_body = json.dumps({"contact_id": "c-123", "amount": 999999}).encode()
    request = _make_mock_request(headers={"X-GHL-Signature": signature})

    result = security._verify_ghl_signature(request, tampered_body)
    assert result is False


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_empty_body_valid_signature(security):
    """An empty body with valid signature for that empty body should be accepted."""
    body = b""
    signature = _compute_hmac_signature(TEST_WEBHOOK_SECRET, body)
    request = _make_mock_request(headers={"X-GHL-Signature": signature})

    result = security._verify_ghl_signature(request, body)
    assert result is True


# ---------------------------------------------------------------------------
# verify_webhook_signature async method (integration with decorator path)
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.jorge
@pytest.mark.asyncio
async def test_verify_webhook_signature_async_valid(security):
    """The async verify_webhook_signature method should return True for valid GHL sig."""
    body = json.dumps({"event": "contact.message"}).encode()
    signature = _compute_hmac_signature(TEST_WEBHOOK_SECRET, body)
    request = _make_mock_request(headers={"X-GHL-Signature": signature})
    request.body = AsyncMock(return_value=body)

    result = await security.verify_webhook_signature(request, "ghl")
    assert result is True


@pytest.mark.unit
@pytest.mark.jorge
@pytest.mark.asyncio
async def test_verify_webhook_signature_async_invalid(security):
    """The async verify_webhook_signature should return False for bad GHL sig."""
    body = json.dumps({"event": "contact.message"}).encode()
    request = _make_mock_request(headers={"X-GHL-Signature": "wrong"})
    request.body = AsyncMock(return_value=body)

    result = await security.verify_webhook_signature(request, "ghl")
    assert result is False


@pytest.mark.unit
@pytest.mark.jorge
@pytest.mark.asyncio
async def test_verify_webhook_signature_async_missing_raises(security):
    """The async verify_webhook_signature should raise HTTPException for missing sig."""
    body = json.dumps({"event": "test"}).encode()
    request = _make_mock_request(headers={})
    request.body = AsyncMock(return_value=body)

    with pytest.raises(HTTPException) as exc_info:
        await security.verify_webhook_signature(request, "ghl")
    assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Misconfigured secret
# ---------------------------------------------------------------------------


@pytest.mark.unit
@pytest.mark.jorge
def test_webhook_no_secret_configured_raises_500():
    """If no GHL webhook secret is configured, should raise HTTPException(500)."""
    with patch("ghl_real_estate_ai.services.security_framework.settings", _mock_settings):
        fw = SecurityFramework(redis_url="redis://localhost:6379/15")
    # Clear the secret
    fw.config.webhook_signing_secrets = {"ghl": ""}

    body = json.dumps({"event": "test"}).encode()
    signature = "any-signature"
    request = _make_mock_request(headers={"X-GHL-Signature": signature})

    with pytest.raises(HTTPException) as exc_info:
        fw._verify_ghl_signature(request, body)
    assert exc_info.value.status_code == 500
