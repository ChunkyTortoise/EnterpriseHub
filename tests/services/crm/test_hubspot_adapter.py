"""Tests for HubSpotAdapter -- HubSpot CRM adapter."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from ghl_real_estate_ai.services.crm import CRMContact, HubSpotAdapter
from ghl_real_estate_ai.services.crm.hubspot_adapter import HubSpotError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

API_KEY = "test-hubspot-access-token"
BASE_URL = "https://api.hubapi.com"


@pytest.fixture()
def adapter() -> HubSpotAdapter:
    return HubSpotAdapter(api_key=API_KEY, base_url=BASE_URL)


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


class TestHubSpotAdapterInit:
    def test_stores_credentials(self, adapter: HubSpotAdapter):
        assert adapter._api_key == API_KEY
        assert adapter._base_url == BASE_URL

    def test_base_url_trailing_slash_stripped(self):
        a = HubSpotAdapter(api_key="k", base_url="https://api.hubapi.com/")
        assert a._base_url == "https://api.hubapi.com"

    def test_default_base_url(self):
        a = HubSpotAdapter(api_key="k")
        assert a._base_url == "https://api.hubapi.com"

    def test_headers_contain_auth(self, adapter: HubSpotAdapter):
        headers = adapter._headers()
        assert headers["Authorization"] == f"Bearer {API_KEY}"
        assert headers["Content-Type"] == "application/json"


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------


class TestHubSpotFieldMapping:
    def test_contact_to_properties_full(self):
        contact = CRMContact(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+15551234567",
            source="website",
        )
        props = HubSpotAdapter._contact_to_properties(contact)
        assert props["firstname"] == "Jane"
        assert props["lastname"] == "Doe"
        assert props["email"] == "jane@example.com"
        assert props["phone"] == "+15551234567"
        assert props["hs_lead_status"] == "website"

    def test_contact_to_properties_minimal(self):
        contact = CRMContact()
        props = HubSpotAdapter._contact_to_properties(contact)
        assert props == {}

    def test_properties_to_contact(self):
        props = {
            "firstname": "Bob",
            "lastname": "Jones",
            "email": "bob@example.com",
            "phone": "+19095551111",
            "hs_lead_status": "referral",
        }
        contact = HubSpotAdapter._properties_to_contact("hs-1", props)
        assert contact.id == "hs-1"
        assert contact.first_name == "Bob"
        assert contact.last_name == "Jones"
        assert contact.email == "bob@example.com"
        assert contact.phone == "+19095551111"
        assert contact.source == "referral"

    def test_properties_to_contact_missing_fields(self):
        contact = HubSpotAdapter._properties_to_contact("hs-2", {})
        assert contact.id == "hs-2"
        assert contact.first_name == ""
        assert contact.email is None


# ---------------------------------------------------------------------------
# HubSpotError
# ---------------------------------------------------------------------------


class TestHubSpotError:
    def test_error_attributes(self):
        err = HubSpotError(422, "Validation failed")
        assert err.status_code == 422
        assert err.detail == "Validation failed"
        assert "422" in str(err)
        assert "Validation failed" in str(err)


# ---------------------------------------------------------------------------
# Async CRM operations (mock _request)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestHubSpotCreateContact:
    async def test_create_contact_success(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "id": "hs-c1",
                "properties": {"firstname": "Jane", "lastname": "Doe"},
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        contact = CRMContact(
            first_name="Jane", last_name="Doe", tags=["VIP"], metadata={"k": "v"}
        )
        result = await adapter.create_contact(contact)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[0] == ("POST", "/crm/v3/objects/contacts")
        payload = call_args[1]["json_body"]
        assert "properties" in payload
        assert payload["properties"]["firstname"] == "Jane"
        assert result.id == "hs-c1"
        assert result.first_name == "Jane"
        # Tags and metadata are carried over from the input contact
        assert result.tags == ["VIP"]
        assert result.metadata == {"k": "v"}


@pytest.mark.asyncio
class TestHubSpotGetContact:
    async def test_get_contact_success(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "id": "hs-c2",
                "properties": {"firstname": "Alice", "email": "alice@example.com"},
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.get_contact("hs-c2")
        assert result is not None
        assert result.id == "hs-c2"
        assert result.first_name == "Alice"
        assert result.email == "alice@example.com"

    async def test_get_contact_not_found_returns_none(self, adapter: HubSpotAdapter):
        adapter._request = AsyncMock(
            side_effect=HubSpotError(404, "Resource not found")
        )
        result = await adapter.get_contact("missing-id")
        assert result is None

    async def test_get_contact_non_404_raises(self, adapter: HubSpotAdapter):
        adapter._request = AsyncMock(side_effect=HubSpotError(500, "Server error"))
        with pytest.raises(HubSpotError) as exc_info:
            await adapter.get_contact("hs-x")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
class TestHubSpotUpdateContact:
    async def test_update_contact_maps_keys(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "id": "hs-c3",
                "properties": {"firstname": "Updated"},
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.update_contact(
            "hs-c3", {"first_name": "Updated", "email": "new@example.com"}
        )

        call_args = adapter._request.call_args
        assert call_args[0] == ("PATCH", "/crm/v3/objects/contacts/hs-c3")
        payload = call_args[1]["json_body"]
        assert payload["properties"]["firstname"] == "Updated"
        assert payload["properties"]["email"] == "new@example.com"
        assert result.id == "hs-c3"

    async def test_update_maps_source_to_hs_lead_status(self, adapter: HubSpotAdapter):
        resp = _mock_response(200, {"id": "hs-c4", "properties": {}})
        adapter._request = AsyncMock(return_value=resp)

        await adapter.update_contact("hs-c4", {"source": "referral"})

        payload = adapter._request.call_args[1]["json_body"]
        assert payload["properties"]["hs_lead_status"] == "referral"


@pytest.mark.asyncio
class TestHubSpotSearchContacts:
    async def test_search_returns_list(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "results": [
                    {"id": "s-1", "properties": {"firstname": "A"}},
                    {"id": "s-2", "properties": {"firstname": "B"}},
                ]
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("test", limit=5)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[0] == ("POST", "/crm/v3/objects/contacts/search")
        payload = call_args[1]["json_body"]
        assert payload["limit"] == 5
        assert len(results) == 2
        assert results[0].id == "s-1"

    async def test_search_empty_results(self, adapter: HubSpotAdapter):
        resp = _mock_response(200, {"results": []})
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("nobody")
        assert results == []


@pytest.mark.asyncio
class TestHubSpotSyncLead:
    async def test_sync_lead_updates_status_and_score(self, adapter: HubSpotAdapter):
        resp = _mock_response(200, {"id": "sl-1", "properties": {}})
        adapter._request = AsyncMock(return_value=resp)

        contact = CRMContact(id="sl-1")
        result = await adapter.sync_lead(contact, score=85, temperature="Warm-Lead")

        assert result is True
        call_args = adapter._request.call_args
        payload = call_args[1]["json_body"]
        assert payload["properties"]["hs_lead_status"] == "Warm-Lead"
        assert payload["properties"]["lead_score"] == "85"

    async def test_sync_lead_no_contact_id_returns_false(self, adapter: HubSpotAdapter):
        contact = CRMContact(id=None)
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_empty_string_id_returns_false(
        self, adapter: HubSpotAdapter
    ):
        contact = CRMContact(id="")
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_api_failure_returns_false(self, adapter: HubSpotAdapter):
        adapter._request = AsyncMock(side_effect=HubSpotError(500, "Server error"))

        contact = CRMContact(id="sl-fail")
        result = await adapter.sync_lead(contact, score=20, temperature="Cold-Lead")
        assert result is False


# ---------------------------------------------------------------------------
# Extended operations (beyond CRMProtocol)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestHubSpotDeleteContact:
    async def test_delete_returns_true_on_success(self, adapter: HubSpotAdapter):
        resp = _mock_response(204)
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.delete_contact("del-1")
        assert result is True
        call_args = adapter._request.call_args
        assert call_args[0] == ("DELETE", "/crm/v3/objects/contacts/del-1")

    async def test_delete_returns_false_on_404(self, adapter: HubSpotAdapter):
        adapter._request = AsyncMock(
            side_effect=HubSpotError(404, "Resource not found")
        )
        result = await adapter.delete_contact("missing")
        assert result is False

    async def test_delete_non_404_raises(self, adapter: HubSpotAdapter):
        adapter._request = AsyncMock(side_effect=HubSpotError(500, "Server error"))
        with pytest.raises(HubSpotError):
            await adapter.delete_contact("del-x")


@pytest.mark.asyncio
class TestHubSpotListContacts:
    async def test_list_contacts_with_pagination(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "results": [
                    {"id": "lc-1", "properties": {"firstname": "First"}},
                    {"id": "lc-2", "properties": {"firstname": "Second"}},
                ],
                "paging": {"next": {"after": "cursor-abc"}},
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        contacts, next_cursor = await adapter.list_contacts(limit=2)

        assert len(contacts) == 2
        assert contacts[0].id == "lc-1"
        assert next_cursor == "cursor-abc"
        call_args = adapter._request.call_args
        assert call_args[1]["params"]["limit"] == 2

    async def test_list_contacts_last_page(self, adapter: HubSpotAdapter):
        resp = _mock_response(
            200,
            {
                "results": [{"id": "lc-3", "properties": {"firstname": "Only"}}],
            },
        )
        adapter._request = AsyncMock(return_value=resp)

        contacts, next_cursor = await adapter.list_contacts(limit=10)

        assert len(contacts) == 1
        assert next_cursor is None

    async def test_list_contacts_passes_after_cursor(self, adapter: HubSpotAdapter):
        resp = _mock_response(200, {"results": []})
        adapter._request = AsyncMock(return_value=resp)

        await adapter.list_contacts(limit=10, after="cursor-xyz")

        params = adapter._request.call_args[1]["params"]
        assert params["after"] == "cursor-xyz"

    async def test_list_contacts_caps_limit_at_100(self, adapter: HubSpotAdapter):
        resp = _mock_response(200, {"results": []})
        adapter._request = AsyncMock(return_value=resp)

        await adapter.list_contacts(limit=500)

        params = adapter._request.call_args[1]["params"]
        assert params["limit"] == 100