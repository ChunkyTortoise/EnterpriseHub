"""Unit tests for SecurityFramework.

Tests cover: JWT generation/validation, webhook signature verification,
input sanitization, rate limiting, CORS, phone/email validation.
"""

import hashlib
import hmac
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import jwt as pyjwt
import pytest
from fastapi import HTTPException

# We need to mock settings before importing SecurityFramework
_settings_defaults = {
    "jwt_secret_key": "test-jwt-secret-key-for-testing-only-minimum-32-chars",
    "redis_url": "redis://localhost:6379/0",
    "ghl_webhook_secret": "ghl-test-secret",
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
        RateLimitType,
        SecurityConfig,
        SecurityFramework,
        SecurityLevel,
    )


def _make_mock_request(headers: dict | None = None, client_host: str = "127.0.0.1", url_path: str = "/api/test"):
    """Create a mock FastAPI Request."""
    request = MagicMock()
    request.headers = headers or {}
    request.client = MagicMock()
    request.client.host = client_host
    request.url = MagicMock()
    request.url.path = url_path
    request.method = "POST"
    request.state = MagicMock()
    return request


@pytest.fixture
def security():
    """Create a SecurityFramework with mocked settings."""
    with patch("ghl_real_estate_ai.services.security_framework.settings", _mock_settings):
        fw = SecurityFramework(redis_url="redis://localhost:6379/0")
    # SecurityConfig defaults capture settings at class-definition time, so we must
    # override webhook_signing_secrets explicitly to ensure test values are used.
    fw.config.webhook_signing_secrets = {
        "ghl": "ghl-test-secret",
        "apollo": "apollo-test-secret",
        "twilio": "twilio-test-secret",
        "sendgrid": "sendgrid-test-secret",
        "vapi": "vapi-test-secret",
        "retell": "retell-test-secret",
    }
    return fw


# ---------------------------------------------------------------------------
# JWT tests
# ---------------------------------------------------------------------------


class TestJWTGeneration:
    def test_generate_jwt_token_default_role(self, security):
        token = security.generate_jwt_token("user-123")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_generate_jwt_token_admin_role(self, security):
        token = security.generate_jwt_token("admin-1", role="admin")
        payload = pyjwt.decode(
            token,
            security.config.jwt_secret_key,
            algorithms=[security.config.jwt_algorithm],
            audience="service6-api",
        )
        assert payload["role"] == "admin"
        assert payload["sub"] == "admin-1"

    def test_generate_jwt_token_additional_claims(self, security):
        token = security.generate_jwt_token("user-1", additional_claims={"tenant_id": "t-1"})
        payload = pyjwt.decode(
            token,
            security.config.jwt_secret_key,
            algorithms=[security.config.jwt_algorithm],
            audience="service6-api",
        )
        assert payload["tenant_id"] == "t-1"

    def test_jwt_token_has_expiry(self, security):
        token = security.generate_jwt_token("user-1")
        payload = pyjwt.decode(
            token,
            security.config.jwt_secret_key,
            algorithms=[security.config.jwt_algorithm],
            audience="service6-api",
        )
        assert "exp" in payload
        assert payload["exp"] > time.time()


class TestJWTValidation:
    @pytest.mark.asyncio
    async def test_validate_valid_token(self, security):
        token = security.generate_jwt_token("user-1", role="user")
        payload = await security.validate_jwt_token(token)
        assert payload["sub"] == "user-1"
        assert payload["role"] == "user"

    @pytest.mark.asyncio
    async def test_validate_expired_token(self, security):
        expired_payload = {
            "sub": "user-1",
            "role": "user",
            "iat": datetime.utcnow() - timedelta(hours=48),
            "exp": datetime.utcnow() - timedelta(hours=1),
            "iss": "service6-lead-engine",
            "aud": "service6-api",
        }
        token = pyjwt.encode(expired_payload, security.config.jwt_secret_key, algorithm=security.config.jwt_algorithm)
        with pytest.raises(HTTPException) as exc_info:
            await security.validate_jwt_token(token)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_invalid_token(self, security):
        with pytest.raises(HTTPException) as exc_info:
            await security.validate_jwt_token("not.a.valid.token")
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_wrong_secret(self, security):
        token = pyjwt.encode(
            {
                "sub": "user-1",
                "role": "user",
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=1),
                "iss": "service6-lead-engine",
                "aud": "service6-api",
            },
            "wrong-secret-key-that-does-not-match",
            algorithm="HS256",
        )
        with pytest.raises(HTTPException) as exc_info:
            await security.validate_jwt_token(token)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Webhook signature verification tests
# ---------------------------------------------------------------------------


class TestWebhookVerification:
    def test_ghl_valid_hmac_signature(self, security):
        body = b'{"event": "contact.create"}'
        secret = security.config.webhook_signing_secrets["ghl"]
        signature = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        request = _make_mock_request(headers={"X-GHL-Signature": signature})
        result = security._verify_ghl_signature(request, body)
        assert result is True

    def test_ghl_valid_static_secret_signature(self, security):
        """GHL Custom Webhook actions send the raw secret as signature."""
        body = b'{"event": "contact.create"}'
        secret = security.config.webhook_signing_secrets["ghl"]
        request = _make_mock_request(headers={"X-GHL-Signature": secret})
        result = security._verify_ghl_signature(request, body)
        assert result is True

    def test_ghl_missing_signature_raises(self, security):
        body = b'{"event": "test"}'
        request = _make_mock_request(headers={})
        with pytest.raises(HTTPException) as exc_info:
            security._verify_ghl_signature(request, body)
        assert exc_info.value.status_code == 401

    def test_ghl_invalid_signature_returns_false(self, security):
        body = b'{"event": "test"}'
        request = _make_mock_request(headers={"X-GHL-Signature": "invalid-signature"})
        result = security._verify_ghl_signature(request, body)
        assert result is False

    def test_apollo_valid_signature(self, security):
        body = b'{"event": "contact.updated"}'
        secret = security.config.webhook_signing_secrets["apollo"]
        expected = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
        request = _make_mock_request(headers={"X-Apollo-Signature": f"sha256={expected}"})
        result = security._verify_apollo_signature(request, body)
        assert result is True

    def test_apollo_missing_signature(self, security):
        body = b'{"event": "test"}'
        request = _make_mock_request(headers={})
        result = security._verify_apollo_signature(request, body)
        assert result is False

    def test_vapi_valid_secret(self, security):
        body = b'{"call_id": "123"}'
        request = _make_mock_request(headers={"x-vapi-secret": "vapi-test-secret"})
        result = security._verify_vapi_signature(request, body)
        assert result is True

    def test_vapi_missing_secret(self, security):
        body = b'{"call_id": "123"}'
        request = _make_mock_request(headers={})
        result = security._verify_vapi_signature(request, body)
        assert result is False

    def test_vapi_wrong_secret(self, security):
        body = b'{"call_id": "123"}'
        request = _make_mock_request(headers={"x-vapi-secret": "wrong-secret"})
        result = security._verify_vapi_signature(request, body)
        assert result is False


# ---------------------------------------------------------------------------
# Input sanitization tests
# ---------------------------------------------------------------------------


class TestSanitization:
    def test_sanitize_html_tags(self, security):
        result = security.sanitize_input("<script>alert('xss')</script>")
        assert "<script>" not in result
        # The sanitizer replaces < before &, so &lt; gets double-encoded to &amp;lt;
        assert "&amp;lt;script&amp;gt;" in result

    def test_sanitize_null_bytes(self, security):
        result = security.sanitize_input("hello\x00world")
        assert "\x00" not in result
        assert "helloworld" in result

    def test_sanitize_long_string(self, security):
        long_input = "a" * 20000
        result = security.sanitize_input(long_input)
        assert len(result) <= 10000

    def test_sanitize_dict(self, security):
        data = {"name": "<b>bold</b>", "nested": {"val": "safe"}}
        result = security.sanitize_input(data)
        # Double-encoding: < replaced first, then & in &lt; replaced to &amp;lt;
        assert "<b>" not in result["name"]
        assert "&amp;lt;b&amp;gt;" in result["name"]
        assert result["nested"]["val"] == "safe"

    def test_sanitize_list(self, security):
        data = ["<img>", "normal"]
        result = security.sanitize_input(data)
        assert "<img>" not in result[0]
        assert "&amp;lt;img&amp;gt;" in result[0]
        assert result[1] == "normal"

    def test_sanitize_non_string_passthrough(self, security):
        assert security.sanitize_input(42) == 42
        assert security.sanitize_input(None) is None


# ---------------------------------------------------------------------------
# Validation tests
# ---------------------------------------------------------------------------


class TestValidation:
    def test_valid_phone_numbers(self, security):
        assert security.validate_phone_number("+1-909-555-1234") is True
        assert security.validate_phone_number("(909) 555-1234") is True
        assert security.validate_phone_number("9095551234") is True

    def test_invalid_phone_numbers(self, security):
        assert security.validate_phone_number("123") is False
        assert security.validate_phone_number("not-a-phone") is False

    def test_valid_emails(self, security):
        assert security.validate_email("jorge@lyrio.io") is True
        assert security.validate_email("test+tag@example.com") is True

    def test_invalid_emails(self, security):
        assert security.validate_email("not-an-email") is False
        assert security.validate_email("@no-local.com") is False
        assert security.validate_email("missing@") is False


# ---------------------------------------------------------------------------
# CORS tests
# ---------------------------------------------------------------------------


class TestCORS:
    def test_allowed_origin_exact(self, security):
        assert security.is_allowed_origin("https://app.gohighlevel.com") is True

    def test_allowed_origin_wildcard(self, security):
        assert security.is_allowed_origin("https://sub.gohighlevel.com") is True

    def test_disallowed_origin(self, security):
        assert security.is_allowed_origin("https://evil.com") is False

    def test_localhost_allowed(self, security):
        assert security.is_allowed_origin("http://localhost:3000") is True


# ---------------------------------------------------------------------------
# Security headers tests
# ---------------------------------------------------------------------------


class TestSecurityHeaders:
    def test_add_security_headers(self, security):
        response = MagicMock()
        response.headers = {}
        result = security.add_security_headers(response)
        assert result.headers["X-Content-Type-Options"] == "nosniff"
        assert result.headers["X-Frame-Options"] == "DENY"
        assert "Strict-Transport-Security" in result.headers


# ---------------------------------------------------------------------------
# Client IP extraction tests
# ---------------------------------------------------------------------------


class TestClientIP:
    def test_forwarded_for(self, security):
        request = _make_mock_request(headers={"X-Forwarded-For": "1.2.3.4, 5.6.7.8"})
        assert security._get_client_ip(request) == "1.2.3.4"

    def test_real_ip(self, security):
        request = _make_mock_request(headers={"X-Real-IP": "10.0.0.1"})
        assert security._get_client_ip(request) == "10.0.0.1"

    def test_fallback_to_client_host(self, security):
        request = _make_mock_request(headers={}, client_host="192.168.1.1")
        assert security._get_client_ip(request) == "192.168.1.1"
