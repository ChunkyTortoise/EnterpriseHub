import pytest

import ghl_client as ghl_module
from ghl_client import GHLClient
import jorge_fastapi_lead_bot as lead_api


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, responses, calls):
        self._responses = responses
        self._calls = calls

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def request(self, method, url, headers=None, json=None, params=None):
        self._calls.append(
            {
                "method": method,
                "url": url,
                "headers": headers,
                "json": json,
                "params": params,
            }
        )
        if self._responses:
            return self._responses.pop(0)
        return FakeResponse(200, {"ok": True})


@pytest.mark.asyncio
async def test_send_sms_uses_expected_payload(monkeypatch):
    calls = []
    responses = [FakeResponse(201, {"ok": True})]

    def client_factory(*args, **kwargs):
        return FakeAsyncClient(responses, calls)

    monkeypatch.setattr(ghl_module.httpx, "AsyncClient", client_factory)

    client = GHLClient(access_token="token")
    client.max_retries = 1

    ok = await client.send_sms("+15551234567", "Hello from Jorge")

    assert ok is True
    assert calls[0]["method"] == "POST"
    assert calls[0]["json"]["phone"] == "+15551234567"
    assert calls[0]["json"]["type"] == "SMS"


@pytest.mark.asyncio
async def test_update_contact_custom_fields_rejects_malformed_payload():
    client = GHLClient(access_token="token")

    assert await client.update_contact_custom_fields("contact-1", {}) is False
    assert await client.update_contact_custom_fields("contact-1", {"": "x"}) is False


@pytest.mark.asyncio
async def test_update_contact_custom_fields_success(monkeypatch):
    calls = []
    responses = [FakeResponse(200, {"updated": True})]

    def client_factory(*args, **kwargs):
        return FakeAsyncClient(responses, calls)

    monkeypatch.setattr(ghl_module.httpx, "AsyncClient", client_factory)

    client = GHLClient(access_token="token")
    client.max_retries = 1

    ok = await client.update_contact_custom_fields(
        "contact-2", {"lead_temperature": "HOT", "ai_lead_score": 88}
    )

    assert ok is True
    payload = calls[0]["json"]
    assert payload["customFields"][0]["id"] == "lead_temperature"


@pytest.mark.asyncio
async def test_add_contact_tags_returns_false_if_any_tag_fails(monkeypatch):
    calls = []
    responses = [FakeResponse(201, {}), FakeResponse(500, {})]

    def client_factory(*args, **kwargs):
        return FakeAsyncClient(responses, calls)

    monkeypatch.setattr(ghl_module.httpx, "AsyncClient", client_factory)

    client = GHLClient(access_token="token")
    client.max_retries = 1

    ok = await client.add_contact_tags("contact-3", ["Priority-High", "Hot-Lead"])

    assert ok is False
    assert len(calls) == 2


@pytest.mark.asyncio
async def test_update_ghl_contact_uses_contract_methods(monkeypatch):
    class FakeGHL:
        def __init__(self):
            self.field_updates = []
            self.tag_updates = []

        async def update_contact_custom_fields(self, contact_id, updates):
            self.field_updates.append((contact_id, updates))
            return True

        async def add_contact_tags(self, contact_id, tags):
            self.tag_updates.append((contact_id, tags))
            return True

    fake_ghl = FakeGHL()
    monkeypatch.setattr(lead_api, "ghl_client", fake_ghl)

    await lead_api.update_ghl_contact(
        contact_id="contact-4",
        location_id="loc-4",
        analysis_result={
            "lead_score": 91,
            "lead_temperature": "HOT",
            "jorge_priority": "high",
            "estimated_commission": 10000,
            "jorge_validation": {
                "passes_jorge_criteria": True,
                "service_area_match": True,
            },
        },
    )

    assert len(fake_ghl.field_updates) == 1
    assert len(fake_ghl.tag_updates) == 1
