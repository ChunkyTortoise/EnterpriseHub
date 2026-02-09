"""
Tests for GHL Webhook API endpoints.

Endpoints tested:
    POST /api/ghl/webhook      - Main GHL webhook handler
    POST /api/ghl/tag-webhook  - Tag-added webhook handler
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures & helpers
# ---------------------------------------------------------------------------

def _make_client():
    from ghl_real_estate_ai.api.main import app

    return TestClient(app, raise_server_exceptions=False)


def _bypass_webhook_verification():
    """Patch SecurityFramework.verify_webhook_signature as instance method."""

    async def _always_true(self, request, provider):
        return True

    return patch(
        "ghl_real_estate_ai.services.security_framework.SecurityFramework.verify_webhook_signature",
        new=_always_true,
    )


def _reject_webhook_verification():
    """Patch SecurityFramework.verify_webhook_signature to reject."""

    async def _always_false(self, request, provider):
        return False

    return patch(
        "ghl_real_estate_ai.services.security_framework.SecurityFramework.verify_webhook_signature",
        new=_always_false,
    )


def _mock_conversation_manager():
    mock = MagicMock()
    mock.get_context = AsyncMock(return_value={})
    mock.memory_service = MagicMock()
    mock.memory_service.save_context = AsyncMock()
    return patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock)


def _mock_ghl_client():
    mock = MagicMock()
    mock.send_message = AsyncMock()
    mock.add_tags = AsyncMock()
    mock.apply_actions = AsyncMock()
    return patch("ghl_real_estate_ai.api.routes.webhook.ghl_client_default", mock)


def _mock_analytics():
    mock = MagicMock()
    mock.track_event = AsyncMock()
    return patch("ghl_real_estate_ai.api.routes.webhook.analytics_service", mock)


def _all_webhook_mocks():
    """Return all mocks needed for webhook processing."""
    return (_bypass_webhook_verification(), _mock_conversation_manager(), _mock_ghl_client(), _mock_analytics())


def _inbound_webhook_payload(
    message="Hi, I want to sell my house",
    tags=None,
    contact_id="contact-123",
    location_id="loc-456",
    direction="inbound",
):
    return {
        "type": "InboundMessage",
        "contactId": contact_id,
        "locationId": location_id,
        "message": {"type": "SMS", "body": message, "direction": direction},
        "contact": {"contactId": contact_id, "firstName": "Test", "lastName": "Lead", "tags": tags or ["Needs Qualifying"]},
    }


def _tag_webhook_payload(tag="Needs Qualifying", contact_id="contact-123", location_id="loc-456"):
    return {
        "type": "ContactTagAdded",
        "contactId": contact_id,
        "locationId": location_id,
        "tag": tag,
        "contact": {"contactId": contact_id, "firstName": "Test", "lastName": "Lead", "tags": [tag]},
    }


# ---------------------------------------------------------------------------
# POST /api/ghl/webhook
# ---------------------------------------------------------------------------

class TestHandleGHLWebhook:

    def test_webhook_ignores_outbound_messages(self):
        payload = _inbound_webhook_payload(direction="outbound")
        p1, p2, p3, p4 = _all_webhook_mocks()
        with p1, p2, p3, p4:
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
        assert "outbound" in resp.json()["message"].lower()

    def test_webhook_requires_activation_tag(self):
        payload = _inbound_webhook_payload(tags=["Random-Tag"])
        p1, p2, p3, p4 = _all_webhook_mocks()
        with (
            p1, p2, p3, p4,
            patch("ghl_real_estate_ai.api.routes.webhook.settings") as mock_s,
            patch("ghl_real_estate_ai.api.routes.webhook.jorge_settings") as mock_j,
        ):
            mock_s.activation_tags = ["Needs Qualifying"]
            mock_s.deactivation_tags = ["AI-Off"]
            mock_j.JORGE_BUYER_MODE = False
            mock_j.JORGE_LEAD_MODE = False
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 200
        msg = resp.json()["message"].lower()
        assert "not triggered" in msg or "activation" in msg

    def test_webhook_deactivation_tag_overrides(self):
        payload = _inbound_webhook_payload(tags=["Needs Qualifying", "AI-Off"])
        p1, p2, p3, p4 = _all_webhook_mocks()
        with p1, p2, p3, p4:
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 200
        msg = resp.json()["message"].lower()
        assert "deactivat" in msg

    def test_webhook_opt_out_detection(self):
        payload = _inbound_webhook_payload(message="stop", tags=["Needs Qualifying"])
        p1, p2, p3, p4 = _all_webhook_mocks()
        with p1, p2, p3, p4:
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_webhook_invalid_signature_returns_401(self):
        payload = _inbound_webhook_payload()
        with _reject_webhook_verification():
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 401

    def test_webhook_malformed_payload_returns_422(self):
        with _bypass_webhook_verification():
            resp = _make_client().post("/api/ghl/webhook", json={"bad": "data"})
        assert resp.status_code == 422

    def test_webhook_missing_message_body_returns_422(self):
        payload = {"type": "InboundMessage", "contactId": "c-1", "locationId": "l-1", "message": {"type": "SMS", "direction": "inbound"}}
        with _bypass_webhook_verification():
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/ghl/tag-webhook
# ---------------------------------------------------------------------------

class TestHandleGHLTagWebhook:

    def test_tag_webhook_ignores_non_qualifying_tag(self):
        payload = _tag_webhook_payload(tag="Hot-Lead")
        p1, p2, p3, p4 = _all_webhook_mocks()
        with p1, p2, p3, p4:
            resp = _make_client().post("/api/ghl/tag-webhook", json=payload)
        assert resp.status_code == 200
        assert "ignored" in resp.json()["message"].lower()

    def test_tag_webhook_sends_outreach_for_new_contact(self):
        payload = _tag_webhook_payload(tag="Needs Qualifying")

        mock_conv = MagicMock()
        mock_conv.get_context = AsyncMock(return_value={})
        mock_conv.memory_service = MagicMock()
        mock_conv.memory_service.save_context = AsyncMock()

        with (
            _bypass_webhook_verification(),
            patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conv),
            _mock_ghl_client(),
            _mock_analytics(),
            patch("ghl_real_estate_ai.api.routes.webhook._get_tenant_ghl_client", new=AsyncMock(return_value=MagicMock(send_message=AsyncMock()))),
        ):
            resp = _make_client().post("/api/ghl/tag-webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True

    def test_tag_webhook_skips_if_outreach_already_sent(self):
        payload = _tag_webhook_payload(tag="Needs Qualifying")
        mock_conv = MagicMock()
        mock_conv.get_context = AsyncMock(return_value={"initial_outreach_sent": True})

        with _bypass_webhook_verification(), patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conv), _mock_ghl_client(), _mock_analytics():
            resp = _make_client().post("/api/ghl/tag-webhook", json=payload)
        assert resp.status_code == 200
        assert "already sent" in resp.json()["message"].lower()

    def test_tag_webhook_skips_if_conversation_exists(self):
        payload = _tag_webhook_payload(tag="Needs Qualifying")
        mock_conv = MagicMock()
        mock_conv.get_context = AsyncMock(return_value={"conversation_history": [{"role": "user", "content": "hi"}]})

        with _bypass_webhook_verification(), patch("ghl_real_estate_ai.api.routes.webhook.conversation_manager", mock_conv), _mock_ghl_client(), _mock_analytics():
            resp = _make_client().post("/api/ghl/tag-webhook", json=payload)
        assert resp.status_code == 200
        assert "already started" in resp.json()["message"].lower()

    def test_tag_webhook_malformed_payload_returns_422(self):
        with _bypass_webhook_verification():
            resp = _make_client().post("/api/ghl/tag-webhook", json={"type": "bad"})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# Opt-out phrases
# ---------------------------------------------------------------------------

class TestOptOutPhrases:

    @pytest.mark.parametrize("phrase", ["stop", "unsubscribe", "remove me", "not interested", "opt out", "no thanks"])
    def test_opt_out_phrases_recognized(self, phrase):
        payload = _inbound_webhook_payload(message=phrase, tags=["Needs Qualifying"])
        p1, p2, p3, p4 = _all_webhook_mocks()
        with p1, p2, p3, p4:
            resp = _make_client().post("/api/ghl/webhook", json=payload)
        assert resp.status_code == 200
        assert resp.json()["success"] is True
