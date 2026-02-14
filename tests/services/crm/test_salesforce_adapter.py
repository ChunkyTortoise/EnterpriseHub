"""Tests for SalesforceAdapter -- Salesforce CRM adapter."""

from __future__ import annotations

import time
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from ghl_real_estate_ai.services.crm import CRMContact
from ghl_real_estate_ai.services.crm.salesforce_adapter import (

    SalesforceAdapter,
    SalesforceError,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

CLIENT_ID = "test-client-id"
CLIENT_SECRET = "test-client-secret"
INSTANCE_URL = "https://na1.salesforce.com"


@pytest.fixture()
def adapter() -> SalesforceAdapter:
    a = SalesforceAdapter(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        instance_url=INSTANCE_URL,
    )
    # Pre-set a valid token so tests skip auth round-trip
    a._access_token = "test-token-123"
    a._token_expires_at = time.monotonic() + 3600
    return a


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


class TestSalesforceAdapterInit:
    def test_stores_credentials(self, adapter: SalesforceAdapter):
        assert adapter._client_id == CLIENT_ID
        assert adapter._client_secret == CLIENT_SECRET
        assert adapter._instance_url == INSTANCE_URL

    def test_instance_url_trailing_slash_stripped(self):
        a = SalesforceAdapter(
            client_id="c", client_secret="s",
            instance_url="https://na1.salesforce.com/",
        )
        assert a._instance_url == "https://na1.salesforce.com"

    def test_base_url_defaults_to_instance_url(self):
        a = SalesforceAdapter(
            client_id="c", client_secret="s",
            instance_url="https://na1.salesforce.com",
        )
        assert a._base_url == "https://na1.salesforce.com"

    def test_base_url_override(self):
        a = SalesforceAdapter(
            client_id="c", client_secret="s",
            instance_url="https://na1.salesforce.com",
            base_url="https://test.salesforce.com",
        )
        assert a._base_url == "https://test.salesforce.com"

    def test_initial_token_is_none(self):
        a = SalesforceAdapter(
            client_id="c", client_secret="s",
            instance_url="https://na1.salesforce.com",
        )
        assert a._access_token is None
        assert a._token_expires_at == 0.0


# ---------------------------------------------------------------------------
# OAuth 2.0 Authentication
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSalesforceAuth:
    async def test_authenticate_fetches_new_token(self):
        adapter = SalesforceAdapter(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            instance_url=INSTANCE_URL,
        )
        mock_resp = _mock_response(200, {
            "access_token": "new-token-abc",
            "expires_in": 7200,
        })
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            token = await adapter._authenticate()

        assert token == "new-token-abc"
        assert adapter._access_token == "new-token-abc"
        assert adapter._token_expires_at > time.monotonic()

    async def test_authenticate_returns_cached_token(self, adapter: SalesforceAdapter):
        # Token is already set and not expired
        token = await adapter._authenticate()
        assert token == "test-token-123"

    async def test_authenticate_refreshes_expired_token(self):
        adapter = SalesforceAdapter(
            client_id=CLIENT_ID, client_secret=CLIENT_SECRET,
            instance_url=INSTANCE_URL,
        )
        adapter._access_token = "old-token"
        adapter._token_expires_at = time.monotonic() - 100  # Expired

        mock_resp = _mock_response(200, {
            "access_token": "refreshed-token",
            "expires_in": 7200,
        })
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            token = await adapter._authenticate()

        assert token == "refreshed-token"

    async def test_authenticate_failure_raises(self):
        adapter = SalesforceAdapter(
            client_id="bad", client_secret="bad",
            instance_url=INSTANCE_URL,
        )
        mock_resp = _mock_response(401, text="Invalid credentials")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(SalesforceError) as exc_info:
                await adapter._authenticate()
            assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# Field mapping
# ---------------------------------------------------------------------------


class TestSalesforceFieldMapping:
    def test_contact_to_salesforce_full(self):
        contact = CRMContact(
            first_name="Jane",
            last_name="Doe",
            email="jane@example.com",
            phone="+15551234567",
            source="website",
        )
        fields = SalesforceAdapter._contact_to_salesforce(contact)
        assert fields["FirstName"] == "Jane"
        assert fields["LastName"] == "Doe"
        assert fields["Email"] == "jane@example.com"
        assert fields["Phone"] == "+15551234567"
        assert fields["LeadSource"] == "website"

    def test_contact_to_salesforce_minimal(self):
        contact = CRMContact()
        fields = SalesforceAdapter._contact_to_salesforce(contact)
        assert fields == {}

    def test_salesforce_to_contact(self):
        record = {
            "FirstName": "Bob",
            "LastName": "Jones",
            "Email": "bob@example.com",
            "Phone": "+19095551111",
            "LeadSource": "referral",
        }
        contact = SalesforceAdapter._salesforce_to_contact("sf-1", record)
        assert contact.id == "sf-1"
        assert contact.first_name == "Bob"
        assert contact.last_name == "Jones"
        assert contact.email == "bob@example.com"
        assert contact.phone == "+19095551111"
        assert contact.source == "referral"

    def test_salesforce_to_contact_missing_fields(self):
        contact = SalesforceAdapter._salesforce_to_contact("sf-2", {})
        assert contact.id == "sf-2"
        assert contact.first_name == ""
        assert contact.email is None


# ---------------------------------------------------------------------------
# SalesforceError
# ---------------------------------------------------------------------------


class TestSalesforceError:
    def test_error_attributes(self):
        err = SalesforceError(422, "Validation failed")
        assert err.status_code == 422
        assert err.detail == "Validation failed"
        assert "422" in str(err)
        assert "Validation failed" in str(err)

    def test_rate_limit_error(self):
        err = SalesforceError(429, "Rate limit exceeded")
        assert err.status_code == 429


# ---------------------------------------------------------------------------
# Request helper
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSalesforceRequest:
    async def test_request_clears_token_on_401(self, adapter: SalesforceAdapter):
        """401 response should clear cached token for re-auth on next call."""
        mock_resp = _mock_response(401, text="Unauthorized")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(SalesforceError) as exc_info:
                await adapter._request("GET", "/sobjects/Contact/test")
            assert exc_info.value.status_code == 401

        # Token cache should be cleared
        assert adapter._access_token is None
        assert adapter._token_expires_at == 0.0

    async def test_request_raises_on_429(self, adapter: SalesforceAdapter):
        mock_resp = _mock_response(429, text="Rate limit")
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.request.return_value = mock_resp
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(SalesforceError) as exc_info:
                await adapter._request("GET", "/sobjects/Contact/test")
            assert exc_info.value.status_code == 429


# ---------------------------------------------------------------------------
# Async CRM operations (mock _request)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
class TestSalesforceCreateContact:
    async def test_create_contact_success(self, adapter: SalesforceAdapter):
        resp = _mock_response(201, {"id": "sf-c1", "success": True})
        adapter._request = AsyncMock(return_value=resp)

        contact = CRMContact(
            first_name="Jane", last_name="Doe",
            tags=["VIP"], metadata={"k": "v"},
        )
        result = await adapter.create_contact(contact)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[0] == ("POST", "/sobjects/Contact")
        payload = call_args[1]["json_body"]
        assert payload["FirstName"] == "Jane"
        assert payload["LastName"] == "Doe"
        assert result.id == "sf-c1"
        assert result.first_name == "Jane"
        assert result.tags == ["VIP"]
        assert result.metadata == {"k": "v"}


@pytest.mark.asyncio
class TestSalesforceGetContact:
    async def test_get_contact_success(self, adapter: SalesforceAdapter):
        resp = _mock_response(200, {
            "Id": "sf-c2",
            "FirstName": "Alice",
            "Email": "alice@example.com",
        })
        adapter._request = AsyncMock(return_value=resp)

        result = await adapter.get_contact("sf-c2")
        assert result is not None
        assert result.id == "sf-c2"
        assert result.first_name == "Alice"
        assert result.email == "alice@example.com"

    async def test_get_contact_not_found_returns_none(self, adapter: SalesforceAdapter):
        adapter._request = AsyncMock(
            side_effect=SalesforceError(404, "Resource not found"),
        )
        result = await adapter.get_contact("missing-id")
        assert result is None

    async def test_get_contact_non_404_raises(self, adapter: SalesforceAdapter):
        adapter._request = AsyncMock(
            side_effect=SalesforceError(500, "Server error"),
        )
        with pytest.raises(SalesforceError) as exc_info:
            await adapter.get_contact("sf-x")
        assert exc_info.value.status_code == 500


@pytest.mark.asyncio
class TestSalesforceUpdateContact:
    async def test_update_contact_maps_keys(self, adapter: SalesforceAdapter):
        # PATCH returns 204 (no content), then GET returns updated record
        patch_resp = _mock_response(204)
        get_resp = _mock_response(200, {
            "Id": "sf-c3",
            "FirstName": "Updated",
            "LastName": "",
            "Email": "new@example.com",
        })
        adapter._request = AsyncMock(side_effect=[patch_resp, get_resp])

        result = await adapter.update_contact(
            "sf-c3", {"first_name": "Updated", "email": "new@example.com"},
        )

        # First call is PATCH, second is GET
        calls = adapter._request.call_args_list
        assert calls[0][0] == ("PATCH", "/sobjects/Contact/sf-c3")
        payload = calls[0][1]["json_body"]
        assert payload["FirstName"] == "Updated"
        assert payload["Email"] == "new@example.com"
        assert calls[1][0] == ("GET", "/sobjects/Contact/sf-c3")
        assert result.id == "sf-c3"
        assert result.first_name == "Updated"

    async def test_update_maps_source_to_leadsource(self, adapter: SalesforceAdapter):
        patch_resp = _mock_response(204)
        get_resp = _mock_response(200, {"Id": "sf-c4", "LeadSource": "referral"})
        adapter._request = AsyncMock(side_effect=[patch_resp, get_resp])

        await adapter.update_contact("sf-c4", {"source": "referral"})

        payload = adapter._request.call_args_list[0][1]["json_body"]
        assert payload["LeadSource"] == "referral"


@pytest.mark.asyncio
class TestSalesforceSearchContacts:
    async def test_search_returns_list(self, adapter: SalesforceAdapter):
        resp = _mock_response(200, {
            "searchRecords": [
                {"Id": "s-1", "FirstName": "A", "LastName": ""},
                {"Id": "s-2", "FirstName": "B", "LastName": ""},
            ],
        })
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("test", limit=5)

        adapter._request.assert_awaited_once()
        call_args = adapter._request.call_args
        assert call_args[0] == ("GET", "/search/")
        assert "LIMIT 5" in call_args[1]["params"]["q"]
        assert len(results) == 2
        assert results[0].id == "s-1"

    async def test_search_empty_results(self, adapter: SalesforceAdapter):
        resp = _mock_response(200, {"searchRecords": []})
        adapter._request = AsyncMock(return_value=resp)

        results = await adapter.search_contacts("nobody")
        assert results == []


@pytest.mark.asyncio
class TestSalesforceSyncLead:
    async def test_sync_lead_updates_source_and_score(self, adapter: SalesforceAdapter):
        patch_resp = _mock_response(204)
        get_resp = _mock_response(200, {"Id": "sl-1"})
        adapter._request = AsyncMock(side_effect=[patch_resp, get_resp])

        contact = CRMContact(id="sl-1")
        result = await adapter.sync_lead(contact, score=85, temperature="Warm-Lead")

        assert result is True
        payload = adapter._request.call_args_list[0][1]["json_body"]
        assert payload["LeadSource"] == "Warm-Lead"
        assert payload["lead_score__c"] == "85"

    async def test_sync_lead_no_contact_id_returns_false(self, adapter: SalesforceAdapter):
        contact = CRMContact(id=None)
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_empty_string_id_returns_false(self, adapter: SalesforceAdapter):
        contact = CRMContact(id="")
        result = await adapter.sync_lead(contact, score=50, temperature="Warm-Lead")
        assert result is False

    async def test_sync_lead_api_failure_returns_false(self, adapter: SalesforceAdapter):
        adapter._request = AsyncMock(
            side_effect=SalesforceError(500, "Server error"),
        )
        contact = CRMContact(id="sl-fail")
        result = await adapter.sync_lead(contact, score=20, temperature="Cold-Lead")
        assert result is False