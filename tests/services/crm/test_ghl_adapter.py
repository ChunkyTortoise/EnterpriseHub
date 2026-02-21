"""Tests for GHLAdapter -- GoHighLevel CRM adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ghl_real_estate_ai.services.crm import CRMContact, GHLAdapter
from ghl_real_estate_ai.services.crm.ghl_adapter import GHLError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

API_KEY = "test-ghl-api-key"
LOCATION_ID = "loc-abc-123"
BASE_URL = "https://services.leadconnectorhq.com"


@pytest.fixture()
def adapter() -> GHLAdapter:
    return GHLAdapter(api_key=API_KEY, location_id=LOCATION_ID, base_url=BASE_URL)


def _mock_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> httpx.Response:
    """Build a fake httpx.Response with a .json() method."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.text = text
    return resp


# ---------------------------------------------------------------------------
# Initialisation & helpers
# ---------------------------------------------------------------------------


class TestGHLAdapterInit:
    def test_stores_credentials(self, adapter: GHLAdapter):
        assert adapter._api_key == API_KEY
        assert adapter._location_id == LOCATION_ID
        assert adapter._base_url == BASE_URL

    def test_base_url_trailing_slash_stripped(self):
        a = GHLAdapter(api_key="k", location_id="l", base_url="https://example.com/")
        assert a._base_url == "https://example.com"

    def test_default_base_url(self):
        a = GHLAdapter(api_key="k", location_id="l")
        assert a._base_url == "https://services.leadconnectorhq.com"


class TestGHLHeaders:
    def test_headers_contain_auth(self, adapter: GHLAdapter):
        headers = adapter._headers
        assert headers["Authorization"] == f"Bearer {API_KEY}"
        assert headers["Version"] == "2021-07-28"
        assert headers["Content-Type"] == "application/json"


class TestGHLFieldMapping:
    def test_contact_to_ghl_full(self):
        contact = CRMContact(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+15551234567",
            source="web",
            tags=["Hot-Lead"],
        )
        payload = GHLAdapter._contact_to_ghl(contact, "loc-1")
        assert payload["locationId"] == "loc-1"
        assert payload["firstName"] == "Jane"
        assert payload["lastName"] == "Doe"
        assert payload["email"] == "jane@example.com"
        assert payload["phone"] == "+15551234567"
        assert payload["source"] == "web"
        assert payload["tags"] == ["Hot-Lead"]

    def test_contact_to_ghl_minimal(self):
        contact = CRMContact()
        payload = GHLAdapter._contact_to_ghl(contact, "loc-1")
        assert payload == {"locationId": "loc-1"}

    def test_ghl_to_contact(self):
        data = {
            "id": "ghl-1",
            "firstName": "Bob",
            "lastName": "Jones",
            "email": "bob@example.com",
            "phone": "+19095551111",
            "source": "referral",
            "tags": ["VIP"],
            "customField1": "extra",
        }
        contact = GHLAdapter._ghl_to_contact(data)
        assert contact.id == "ghl-1"
        assert contact.first_name == "Bob"
        assert contact.last_name == "Jones"
        assert contact.email == "bob@example.com"
        assert contact.phone == "+19095551111"
        assert contact.source == "referral"
        assert contact.tags == ["VIP"]
        assert contact.metadata == {"customField1": "extra"}

    def test_ghl_to_contact_missing_fields(self):
        contact = GHLAdapter._ghl_to_contact({})
        assert contact.id == ""
        assert contact.first_name == ""
        assert contact.email is None


# ---------------------------------------------------------------------------
# GHLError
# ---------------------------------------------------------------------------


class TestGHLError:
    def test_error_attributes(self):
        err = GHLError(422, "Validation failed")
        assert err.status_code == 422
        assert err.detail == "Validation failed"
        assert "422" in str(err)
        assert "Validation failed" in str(err)


# ---------------------------------------------------------------------------
# Async CRM operations (mock _request)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestGHLCreateContact:
    async def test_create_contact_success(self, adapter: GHLAdapter):
        resp = _mock_response(
            200,
            {"contact": {"id": "c-1", "firstName": "Jane", "lastName": "Doe"}},
        )
        adapter._request = AsyncMock(return_value=resp)

        contact = CRMContact(first_name="Jane", last_name="Doe")
        result = await adapter.create_contact(contact)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[0] == ("POST", "/contacts/")
        assert result.id == "c-1"
        assert result.first_name == "Jane"


@pytest.mark.asyncio
class TestGHLGetContact:
    async def test_get_contact_success(self, adapter: GHLAdapter):
        resp = _mock_response(
            200,
            {"contact": {"id": "c-2", "firstName": "Alice"}},
        )
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.get_contact("c-2")
        assert result is not None
        assert result.id == "c-2"
        assert result.first_name == "Alice"

    async def test_get_contact_not_found_returns_none(self, adapter: GHLAdapter):
        adapter._request = AsyncMock(side_effect=GHLError(404, "Resource not found"))

        result = await adapter.get_contact("missing-id")
        assert result is None

    async def test_get_contact_non_404_raises(self, adapter: GHLAdapter):
        adapter._request = AsyncMock(side_effect=GHLError(500, "Server error"))

        with pytest.raises(GHLError) as exc_info:
            await adapter.get_contact("c-x")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
class TestGHLUpdateContact:
    async def test_update_contact_maps_keys(self, adapter: GHLAdapter):
        resp = _mock_response(
            200,
            {"contact": {"id": "c-3", "firstName": "Updated"}},
        )
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.update_contact("c-3", {"first_name": "Updated", "email": "new@example.com"})

        call_args = adapter._request.call_args
        assert call_args[0] == ("PUT", "/contacts/c-3")
        payload = call_args[1]["json_body"]
        assert payload["firstName"] == "Updated"
        assert payload["email"] == "new@example.com"
        assert result.id == "c-3"


@pytest.mark.asyncio
class TestGHLSearchContacts:
    async def test_search_returns_list(self, adapter: GHLAdapter):
        resp = _mock_response(
            200,
            {
                "contacts": [
                    {"id": "s-1", "firstName": "A"},
                    {"id": "s-2", "firstName": "B"},
                ]
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("test", limit=5)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[1]["params"]["query"] == "test"
        assert call_args[1]["params"]["limit"] == 5
        assert len(results) == 2
        assert results[0].id == "s-1"

    async def test_search_empty_results(self, adapter: GHLAdapter):
        resp = _mock_response(200, {"contacts": []})
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("nobody")
        assert results == []


@pytest.mark.asyncio
class TestGHLSyncLead:
    async def test_sync_lead_updates_tags_and_score(self, adapter: GHLAdapter):
        resp = _mock_response(200, {"contact": {"id": "sl-1"}})
        adapter._request = AsyncMock(return_value=resp)

        contact = CRMContact(id="sl-1", tags=["Hot-Lead", "VIP"])
        result = await adapter.sync_lead(contact, score=85, temperature="Warm-Lead")

        assert result is True
        call_args = adapter._request.call_args
        payload = call_args[1]["json_body"]
        # Hot-Lead removed, VIP kept, Warm-Lead added
        assert "Hot-Lead" not in payload["tags"]
        assert "VIP" in payload["tags"]
        assert "Warm-Lead" in payload["tags"]
        assert payload["lead_score"] == "85"

    async def test_sync_lead_no_contact_id_returns_false(self, adapter: GHLAdapter):
        contact = CRMContact(id=None)
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_empty_string_id_returns_false(self, adapter: GHLAdapter):
        contact = CRMContact(id="")
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_api_failure_returns_false(self, adapter: GHLAdapter):
        adapter._request = AsyncMock(side_effect=GHLError(500, "Server error"))

        contact = CRMContact(id="sl-fail")
        result = await adapter.sync_lead(contact, score=20, temperature="Cold-Lead")
        assert result is False
