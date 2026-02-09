"""Tests for CRM adapters -- GHL and HubSpot."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, patch

import httpx
import pytest

from ghl_real_estate_ai.services.crm.ghl_adapter import GHLAdapter, GHLError
from ghl_real_estate_ai.services.crm.hubspot_adapter import (
    HubSpotAdapter,
    HubSpotError,
)
from ghl_real_estate_ai.services.crm.protocol import CRMContact, CRMProtocol

# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _mock_response(
    status_code: int = 200,
    json_data: dict | None = None,
    text: str = "",
) -> httpx.Response:
    """Build a fake httpx.Response."""
    content = (
        json.dumps(json_data).encode()
        if json_data is not None
        else text.encode()
    )
    return httpx.Response(
        status_code=status_code,
        content=content,
        headers=(
            {"content-type": "application/json"}
            if json_data is not None
            else {}
        ),
        request=httpx.Request("GET", "https://test.example.com"),
    )


# ==================================================================
# GHL Adapter Tests (10 tests)
# ==================================================================


class TestGHLAdapter:
    """Tests for the GoHighLevel CRM adapter."""

    @pytest.fixture()
    def adapter(self) -> GHLAdapter:
        return GHLAdapter(
            api_key="ghl-test-key",
            location_id="loc-123",
        )

    # ---- test_create_contact_success ----

    @pytest.mark.asyncio()
    async def test_create_contact_success(self, adapter: GHLAdapter) -> None:
        """POST /contacts/ with locationId, returns CRMContact."""
        fake_resp = _mock_response(
            200,
            {
                "contact": {
                    "id": "ghl-001",
                    "firstName": "Jane",
                    "lastName": "Doe",
                    "email": "jane@example.com",
                    "phone": "+15551234567",
                    "tags": ["buyer"],
                    "source": "website",
                }
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.create_contact(
                CRMContact(
                    first_name="Jane",
                    last_name="Doe",
                    email="jane@example.com",
                    phone="+15551234567",
                    tags=["buyer"],
                    source="website",
                )
            )
        assert result.id == "ghl-001"
        assert result.first_name == "Jane"
        assert result.email == "jane@example.com"
        mock_req.assert_called_once()
        call_args = mock_req.call_args
        assert call_args[0][0] == "POST"
        assert "/contacts/" in call_args[0][1]
        payload = call_args[1]["json_body"]
        assert payload["locationId"] == "loc-123"
        assert payload["firstName"] == "Jane"

    # ---- test_get_contact_found ----

    @pytest.mark.asyncio()
    async def test_get_contact_found(self, adapter: GHLAdapter) -> None:
        """GET /contacts/{id} returns a parsed CRMContact."""
        fake_resp = _mock_response(
            200,
            {
                "contact": {
                    "id": "ghl-002",
                    "firstName": "Bob",
                    "lastName": "Builder",
                    "email": "bob@example.com",
                    "tags": [],
                }
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.get_contact("ghl-002")
        assert result is not None
        assert result.id == "ghl-002"
        assert result.first_name == "Bob"

    # ---- test_get_contact_not_found_returns_none ----

    @pytest.mark.asyncio()
    async def test_get_contact_not_found_returns_none(
        self, adapter: GHLAdapter
    ) -> None:
        """GET /contacts/{id} with 404 returns None."""
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.side_effect = GHLError(404, "Resource not found")
            result = await adapter.get_contact("nonexistent")
        assert result is None

    # ---- test_update_contact_success ----

    @pytest.mark.asyncio()
    async def test_update_contact_success(self, adapter: GHLAdapter) -> None:
        """PUT /contacts/{id} maps CRM keys to GHL keys."""
        fake_resp = _mock_response(
            200,
            {
                "contact": {
                    "id": "ghl-003",
                    "firstName": "Updated",
                    "lastName": "Name",
                    "email": "updated@example.com",
                    "tags": [],
                }
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.update_contact(
                "ghl-003", {"first_name": "Updated", "email": "updated@example.com"}
            )
        assert result.first_name == "Updated"
        call_args = mock_req.call_args
        assert call_args[0][0] == "PUT"
        payload = call_args[1]["json_body"]
        assert payload["firstName"] == "Updated"
        assert payload["email"] == "updated@example.com"

    # ---- test_search_contacts_returns_list ----

    @pytest.mark.asyncio()
    async def test_search_contacts_returns_list(
        self, adapter: GHLAdapter
    ) -> None:
        """GET /contacts/search returns a list of CRMContacts."""
        fake_resp = _mock_response(
            200,
            {
                "contacts": [
                    {
                        "id": "ghl-004",
                        "firstName": "Carol",
                        "lastName": "Smith",
                        "email": "carol@example.com",
                        "tags": [],
                    },
                    {
                        "id": "ghl-005",
                        "firstName": "Carol",
                        "lastName": "Jones",
                        "email": "carolj@example.com",
                        "tags": [],
                    },
                ]
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            results = await adapter.search_contacts("Carol", limit=5)
        assert len(results) == 2
        assert results[0].id == "ghl-004"
        assert results[1].last_name == "Jones"
        call_args = mock_req.call_args
        assert call_args[1]["params"]["query"] == "Carol"
        assert call_args[1]["params"]["limit"] == 5

    # ---- test_sync_lead_applies_temperature_tag ----

    @pytest.mark.asyncio()
    async def test_sync_lead_applies_temperature_tag(
        self, adapter: GHLAdapter
    ) -> None:
        """sync_lead updates contact with temperature tag and score."""
        fake_resp = _mock_response(
            200,
            {
                "contact": {
                    "id": "ghl-006",
                    "firstName": "Dave",
                    "tags": ["Hot-Lead"],
                }
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            contact = CRMContact(id="ghl-006", first_name="Dave")
            success = await adapter.sync_lead(
                contact, score=90, temperature="Hot-Lead"
            )
        assert success is True
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert "Hot-Lead" in payload["tags"]
        assert payload["lead_score"] == "90"

    # ---- test_sync_lead_missing_contact ----

    @pytest.mark.asyncio()
    async def test_sync_lead_missing_contact(
        self, adapter: GHLAdapter
    ) -> None:
        """sync_lead with no contact id returns False."""
        contact = CRMContact(first_name="Ghost")
        success = await adapter.sync_lead(
            contact, score=10, temperature="Cold-Lead"
        )
        assert success is False

    # ---- test_headers_include_auth ----

    def test_headers_include_auth(self, adapter: GHLAdapter) -> None:
        """_headers property includes Authorization and Version."""
        headers = adapter._headers
        assert headers["Authorization"] == "Bearer ghl-test-key"
        assert "Version" in headers
        assert headers["Content-Type"] == "application/json"

    # ---- test_implements_crm_protocol ----

    def test_implements_crm_protocol(self, adapter: GHLAdapter) -> None:
        """GHLAdapter is an instance of CRMProtocol."""
        assert isinstance(adapter, CRMProtocol)

    # ---- test_server_error_raises ----

    @pytest.mark.asyncio()
    async def test_server_error_raises(self, adapter: GHLAdapter) -> None:
        """500 status from GHL API raises GHLError."""
        mock_resp = _mock_response(500, text="Internal Server Error")
        with patch(
            "ghl_real_estate_ai.services.crm.ghl_adapter.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_instance = AsyncMock()
            mock_instance.request.return_value = mock_resp
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_instance

            with pytest.raises(GHLError) as exc_info:
                await adapter.create_contact(
                    CRMContact(first_name="Test")
                )
            assert exc_info.value.status_code == 500


# ==================================================================
# HubSpot Adapter Tests (10 tests)
# ==================================================================


class TestHubSpotAdapter:
    """Tests for the HubSpot CRM adapter."""

    @pytest.fixture()
    def adapter(self) -> HubSpotAdapter:
        return HubSpotAdapter(api_key="hs-test-key")

    # ---- test_create_contact_maps_fields ----

    @pytest.mark.asyncio()
    async def test_create_contact_maps_fields(
        self, adapter: HubSpotAdapter
    ) -> None:
        """create_contact sends properties payload with mapped field names."""
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
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.create_contact(
                CRMContact(
                    first_name="Alice",
                    last_name="Wonderland",
                    email="alice@example.com",
                    tags=["buyer"],
                )
            )
        assert result.id == "hs-101"
        assert result.first_name == "Alice"
        assert result.tags == ["buyer"]
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert payload["properties"]["firstname"] == "Alice"

    # ---- test_get_contact_parses_response ----

    @pytest.mark.asyncio()
    async def test_get_contact_parses_response(
        self, adapter: HubSpotAdapter
    ) -> None:
        """get_contact returns a properly parsed CRMContact."""
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-202",
                "properties": {
                    "firstname": "Bob",
                    "lastname": "Builder",
                    "email": "bob@example.com",
                    "phone": "+15559876543",
                },
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.get_contact("hs-202")
        assert result is not None
        assert result.id == "hs-202"
        assert result.first_name == "Bob"
        assert result.phone == "+15559876543"

    # ---- test_get_contact_not_found ----

    @pytest.mark.asyncio()
    async def test_get_contact_not_found(
        self, adapter: HubSpotAdapter
    ) -> None:
        """get_contact returns None for 404."""
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.side_effect = HubSpotError(404, "Resource not found")
            result = await adapter.get_contact("nonexistent")
        assert result is None

    # ---- test_update_contact_sends_patch ----

    @pytest.mark.asyncio()
    async def test_update_contact_sends_patch(
        self, adapter: HubSpotAdapter
    ) -> None:
        """update_contact sends PATCH with mapped properties."""
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-303",
                "properties": {
                    "firstname": "Updated",
                    "lastname": "Person",
                },
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            result = await adapter.update_contact(
                "hs-303", {"first_name": "Updated"}
            )
        assert result.first_name == "Updated"
        call_args = mock_req.call_args
        assert call_args[0][0] == "PATCH"
        assert "hs-303" in call_args[0][1]
        payload = call_args[1]["json_body"]
        assert payload["properties"]["firstname"] == "Updated"

    # ---- test_search_contacts_builds_filter ----

    @pytest.mark.asyncio()
    async def test_search_contacts_builds_filter(
        self, adapter: HubSpotAdapter
    ) -> None:
        """search_contacts builds CONTAINS_TOKEN filter and parses results."""
        fake_resp = _mock_response(
            200,
            {
                "results": [
                    {
                        "id": "hs-401",
                        "properties": {
                            "firstname": "Carol",
                            "lastname": "Smith",
                            "email": "carol@example.com",
                        },
                    }
                ]
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            results = await adapter.search_contacts(
                "carol@example.com", limit=5
            )
        assert len(results) == 1
        assert results[0].id == "hs-401"
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert payload["limit"] == 5
        filters = payload["filterGroups"][0]["filters"]
        assert filters[0]["operator"] == "CONTAINS_TOKEN"
        assert filters[0]["value"] == "carol@example.com"

    # ---- test_sync_lead_success ----

    @pytest.mark.asyncio()
    async def test_sync_lead_success(self, adapter: HubSpotAdapter) -> None:
        """sync_lead updates contact with temperature and score."""
        fake_resp = _mock_response(
            200,
            {
                "id": "hs-501",
                "properties": {
                    "firstname": "Dave",
                    "hs_lead_status": "Hot-Lead",
                    "lead_score": "90",
                },
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            contact = CRMContact(id="hs-501", first_name="Dave")
            success = await adapter.sync_lead(
                contact, score=90, temperature="Hot-Lead"
            )
        assert success is True
        call_args = mock_req.call_args
        payload = call_args[1]["json_body"]
        assert payload["properties"]["hs_lead_status"] == "Hot-Lead"
        assert payload["properties"]["lead_score"] == "90"

    # ---- test_delete_contact_success ----

    @pytest.mark.asyncio()
    async def test_delete_contact_success(
        self, adapter: HubSpotAdapter
    ) -> None:
        """delete_contact sends DELETE and returns True."""
        fake_resp = _mock_response(204)
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            success = await adapter.delete_contact("hs-601")
        assert success is True
        call_args = mock_req.call_args
        assert call_args[0][0] == "DELETE"
        assert "hs-601" in call_args[0][1]

    # ---- test_list_contacts_with_pagination ----

    @pytest.mark.asyncio()
    async def test_list_contacts_with_pagination(
        self, adapter: HubSpotAdapter
    ) -> None:
        """list_contacts returns contacts and next cursor."""
        fake_resp = _mock_response(
            200,
            {
                "results": [
                    {
                        "id": "hs-701",
                        "properties": {
                            "firstname": "Eve",
                            "lastname": "Adams",
                        },
                    },
                    {
                        "id": "hs-702",
                        "properties": {
                            "firstname": "Frank",
                            "lastname": "Burns",
                        },
                    },
                ],
                "paging": {"next": {"after": "cursor-abc"}},
            },
        )
        with patch.object(
            adapter, "_request", new_callable=AsyncMock
        ) as mock_req:
            mock_req.return_value = fake_resp
            contacts, next_cursor = await adapter.list_contacts(
                limit=2, after=None
            )
        assert len(contacts) == 2
        assert contacts[0].id == "hs-701"
        assert contacts[1].first_name == "Frank"
        assert next_cursor == "cursor-abc"
        call_args = mock_req.call_args
        assert call_args[1]["params"]["limit"] == 2

    # ---- test_implements_crm_protocol ----

    def test_implements_crm_protocol(self, adapter: HubSpotAdapter) -> None:
        """HubSpotAdapter is an instance of CRMProtocol."""
        assert isinstance(adapter, CRMProtocol)

    # ---- test_auth_error_handling ----

    @pytest.mark.asyncio()
    async def test_auth_error_handling(
        self, adapter: HubSpotAdapter
    ) -> None:
        """401 from HubSpot API raises HubSpotError with status 401."""
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
