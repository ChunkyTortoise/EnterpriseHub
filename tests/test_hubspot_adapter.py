import pytest
pytestmark = pytest.mark.integration

"""Tests for HubSpot CRM adapter."""


import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ghl_real_estate_ai.services.crm.hubspot_adapter import (
    HubSpotAdapter,
    HubSpotError,
)
from ghl_real_estate_ai.services.crm.protocol import CRMContact



@pytest.fixture()
def adapter() -> HubSpotAdapter:
    return HubSpotAdapter(api_key="test-token-123")


def _mock_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> httpx.Response:
    """Build a fake httpx.Response."""
    content = json.dumps(json_data).encode() if json_data is not None else text.encode()
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers={"content-type": "application/json"} if json_data is not None else {},
        request=httpx.Request("GET", "https://api.hubapi.com/test"),
    )


# ------------------------------------------------------------------
# Field mapping
# ------------------------------------------------------------------


class TestFieldMapping:
    """Verify CRMContact <-> HubSpot property mapping."""

    def test_contact_to_properties(self):
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

    def test_properties_to_contact(self):
        props = {
            "firstname": "John",
            "lastname": "Smith",
            "email": "john@example.com",
            "phone": "+15559876543",
            "hs_lead_status": "referral",
        }
        contact = HubSpotAdapter._properties_to_contact("hs-42", props)
        assert contact.id == "hs-42"
        assert contact.first_name == "John"
        assert contact.last_name == "Smith"
        assert contact.email == "john@example.com"
        assert contact.source == "referral"


# ------------------------------------------------------------------
# API methods
# ------------------------------------------------------------------


class TestCreateContact:
    """Test create_contact maps fields and parses response."""

    @pytest.mark.asyncio()
    async def test_create_contact_success(self, adapter: HubSpotAdapter):
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-101",
                "properties": {
                    "firstname": "Alice",
                    "lastname": "Wonderland",
                    "email": "alice@example.com",
                },
            },
        )
        with patch.object(adapter, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.create_contact(
                CRMContact(
                    first_name="Alice",
                    last_name="Wonderland",
                    email="alice@example.com",
                )
            )
        assert result.id == "hs-101"
        assert result.first_name == "Alice"
        mock_req.assert_called_once()
        call_args = mock_req.call_args
        assert call_args[0][0] == "POST"
        assert "/crm/v3/objects/contacts" in call_args[0][1]


class TestGetContact:
    """Test get_contact parses HubSpot response."""

    @pytest.mark.asyncio()
    async def test_get_contact_found(self, adapter: HubSpotAdapter):
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-202",
                "properties": {
                    "firstname": "Bob",
                    "lastname": "Builder",
                    "email": "bob@example.com",
                },
            },
        )
        with patch.object(adapter, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.get_contact("hs-202")
        assert result is not None
        assert result.id == "hs-202"
        assert result.first_name == "Bob"

    @pytest.mark.asyncio()
    async def test_get_contact_not_found(self, adapter: HubSpotAdapter):
        with patch.object(adapter, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.side_effect = HubSpotError(404, "Resource not found")
            result = await adapter.get_contact("nonexistent")
        assert result is None


class TestSearchContacts:
    """Test search_contacts builds query and parses results."""

    @pytest.mark.asyncio()
    async def test_search_returns_results(self, adapter: HubSpotAdapter):
        fake_resp = _mock_response(
            200,
            {
                "results": [
                    {
                        "id": "hs-301",
                        "properties": {
                            "firstname": "Carol",
                            "lastname": "Smith",
                            "email": "carol@example.com",
                        },
                    }
                ]
            },
        )
        with patch.object(adapter, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = fake_resp
            results = await adapter.search_contacts("carol@example.com", limit=5)
        assert len(results) == 1
        assert results[0].id == "hs-301"
        # Verify payload structure
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert payload["limit"] == 5
        assert payload["filterGroups"][0]["filters"][0]["value"] == "carol@example.com"


class TestSyncLead:
    """Test sync_lead applies temperature tag."""

    @pytest.mark.asyncio()
    async def test_sync_lead_success(self, adapter: HubSpotAdapter):
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-401",
                "properties": {
                    "firstname": "Dave",
                    "hs_lead_status": "Hot-Lead",
                    "lead_score": "90",
                },
            },
        )
        with patch.object(adapter, "_request", new_callable=AsyncMock) as mock_req:
            mock_req.return_value = fake_resp
            contact = CRMContact(id="hs-401", first_name="Dave")
            success = await adapter.sync_lead(contact, score=90, temperature="Hot-Lead")
        assert success is True
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert payload["properties"]["hs_lead_status"] == "Hot-Lead"
        assert payload["properties"]["lead_score"] == "90"

    @pytest.mark.asyncio()
    async def test_sync_lead_no_id(self, adapter: HubSpotAdapter):
        contact = CRMContact(first_name="Ghost")
        success = await adapter.sync_lead(contact, score=10, temperature="Cold-Lead")
        assert success is False


class TestErrorHandling:
    """Test error handling for auth failure and other errors."""

    @pytest.mark.asyncio()
    async def test_auth_failure(self, adapter: HubSpotAdapter):
        mock_resp = _mock_response(401, text="Unauthorized")
        with patch(
            "ghl_real_estate_ai.services.crm.hubspot_adapter.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_instance

            with pytest.raises(HubSpotError) as exc_info:
                await adapter.get_contact("any-id")
            assert exc_info.value.status_code == 401
            assert "Authentication failed" in exc_info.value.detail

    @pytest.mark.asyncio()
    async def test_server_error(self, adapter: HubSpotAdapter):
        mock_resp = _mock_response(500, text="Internal Server Error")
        with patch(
            "ghl_real_estate_ai.services.crm.hubspot_adapter.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_instance

            with pytest.raises(HubSpotError) as exc_info:
                await adapter.create_contact(CRMContact(first_name="Test"))
            assert exc_info.value.status_code == 500