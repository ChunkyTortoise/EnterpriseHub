import hashlib
import hmac
import json
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi.testclient import TestClient
import pytest

import jorge_fastapi_lead_bot as lead_api
from webhook_idempotency import FileBackedIdempotencyStore


def sign_payload(secret: str, raw_payload: bytes) -> str:
    return hmac.new(secret.encode("utf-8"), raw_payload, hashlib.sha256).hexdigest()


def webhook_payload() -> dict:
    return {
        "type": "contact.updated",
        "location_id": "loc-1",
        "contact_id": "contact-1",
        "timestamp": "2026-02-10T10:00:00Z",
        "contact": {"firstName": "Jorge"},
    }


def post_webhook(client: TestClient, payload: dict, signature: Optional[str]):
    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"content-type": "application/json"}
    if signature is not None:
        headers["X-GHL-Signature"] = signature
    return client.post("/webhook/ghl", content=raw_payload, headers=headers), raw_payload


@pytest.fixture
def test_client(tmp_path, monkeypatch):
    store = FileBackedIdempotencyStore(str(tmp_path / "webhook_idempotency.json"), ttl_seconds=3600)
    monkeypatch.setattr(lead_api, "webhook_idempotency_store", store)
    monkeypatch.setattr(lead_api.settings, "is_production", lambda: True)
    return TestClient(lead_api.app)


def test_valid_signature_is_accepted(test_client, monkeypatch):
    async def fake_handle_contact_update(webhook_data, background_tasks):
        return {"status": "acknowledged", "note": "patched"}

    monkeypatch.setattr(lead_api, "handle_contact_update", fake_handle_contact_update)

    payload = webhook_payload()
    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = sign_payload(lead_api.settings.webhook_secret, raw_payload)

    response, _ = post_webhook(test_client, payload, signature)

    assert response.status_code == 200
    assert response.json()["status"] == "acknowledged"


def test_invalid_signature_is_rejected(test_client):
    payload = webhook_payload()
    response, _ = post_webhook(test_client, payload, "bad-signature")

    assert response.status_code == 403


def test_missing_signature_is_rejected(test_client):
    payload = webhook_payload()
    response, _ = post_webhook(test_client, payload, None)

    assert response.status_code == 403


def test_duplicate_event_is_processed_once(test_client, monkeypatch):
    calls = {"count": 0}

    async def fake_handle_contact_update(webhook_data, background_tasks):
        calls["count"] += 1
        return {"status": "acknowledged"}

    monkeypatch.setattr(lead_api, "handle_contact_update", fake_handle_contact_update)

    payload = webhook_payload()
    raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = sign_payload(lead_api.settings.webhook_secret, raw_payload)

    first_response, _ = post_webhook(test_client, payload, signature)
    second_response, _ = post_webhook(test_client, payload, signature)

    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert first_response.json()["status"] == "acknowledged"
    assert second_response.json()["status"] == "duplicate_ignored"
    assert calls["count"] == 1


def test_idempotency_ttl_expiry_behavior(tmp_path):
    store = FileBackedIdempotencyStore(str(tmp_path / "ttl_store.json"), ttl_seconds=1)
    now = datetime(2026, 2, 10, 10, 0, 0, tzinfo=timezone.utc)

    first = store.check_and_mark("evt-1", seen_at=now)
    duplicate_before_expiry = store.check_and_mark("evt-1", seen_at=now + timedelta(milliseconds=800))
    after_expiry = store.check_and_mark("evt-1", seen_at=now + timedelta(seconds=2))

    assert first is False
    assert duplicate_before_expiry is True
    assert after_expiry is False
