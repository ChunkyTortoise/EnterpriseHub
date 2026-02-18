"""
Unit tests for GHLAPIClient (httpx-based GHL API wrapper).

Source: ghl_real_estate_ai/ghl_utils/ghl_api_client.py
"""

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_httpx():
    """Mock httpx.AsyncClient for all GHLAPIClient tests."""
    with patch("ghl_real_estate_ai.ghl_utils.ghl_api_client.httpx.AsyncClient") as cls_mock:
        instance = AsyncMock()
        cls_mock.return_value = instance
        yield instance


@pytest.fixture
def client(mock_httpx):
    """Create a GHLAPIClient with mocked httpx."""
    from ghl_real_estate_ai.ghl_utils.ghl_api_client import GHLAPIClient

    return GHLAPIClient(api_key="test-key", location_id="test-loc")


def _ok_response(json_body: dict, status_code: int = 200) -> MagicMock:
    """Build a fake httpx.Response that passes raise_for_status."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = b"ok"
    resp.json.return_value = json_body
    resp.raise_for_status = MagicMock()  # no-op
    return resp


def _error_response(status_code: int, body: dict | None = None) -> httpx.HTTPStatusError:
    """Build an httpx.HTTPStatusError with a fake response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.content = b'{"error":"bad"}'
    resp.json.return_value = body or {"error": "bad"}
    return httpx.HTTPStatusError("error", request=MagicMock(), response=resp)


# ---------------------------------------------------------------------------
# Initialisation
# ---------------------------------------------------------------------------


class TestGHLAPIClientInit:
    """Initialisation and validation tests."""

    def test_requires_api_key(self, mock_httpx):
        from ghl_real_estate_ai.ghl_utils.ghl_api_client import GHLAPIClient

        with pytest.raises(ValueError, match="GHL_API_KEY is required"):
            GHLAPIClient(api_key=None, location_id="loc")

    def test_requires_location_id(self, mock_httpx):
        from ghl_real_estate_ai.ghl_utils.ghl_api_client import GHLAPIClient

        with pytest.raises(ValueError, match="GHL_LOCATION_ID is required"):
            GHLAPIClient(api_key="key", location_id=None)

    def test_headers_set(self, client):
        assert "Bearer test-key" in client.headers["Authorization"]
        assert client.headers["Content-Type"] == "application/json"

    def test_base_url(self, client):
        assert client.BASE_URL == "https://services.leadconnectorhq.com"


# ---------------------------------------------------------------------------
# Async context manager
# ---------------------------------------------------------------------------


class TestContextManager:
    async def test_aenter_returns_self(self, client):
        result = await client.__aenter__()
        assert result is client

    async def test_aexit_closes_client(self, client, mock_httpx):
        mock_httpx.aclose = AsyncMock()
        await client.__aexit__(None, None, None)
        mock_httpx.aclose.assert_awaited_once()

    async def test_close_method(self, client, mock_httpx):
        mock_httpx.aclose = AsyncMock()
        await client.close()
        mock_httpx.aclose.assert_awaited_once()


# ---------------------------------------------------------------------------
# _make_request
# ---------------------------------------------------------------------------


class TestMakeRequest:
    async def test_success_returns_data(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"contacts": []}))
        result = await client._make_request("GET", "contacts")
        assert result["success"] is True
        assert result["status_code"] == 200

    async def test_http_status_error(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(side_effect=_error_response(401))
        result = await client._make_request("GET", "contacts")
        assert result["success"] is False
        assert result["status_code"] == 401

    async def test_http_status_error_no_json_body(self, client, mock_httpx):
        err = _error_response(500)
        err.response.content = b""
        err.response.json.side_effect = Exception("no json")
        mock_httpx.request = AsyncMock(side_effect=err)
        result = await client._make_request("GET", "contacts")
        assert result["success"] is False
        assert result["details"] == {}

    async def test_generic_exception(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(side_effect=RuntimeError("boom"))
        result = await client._make_request("GET", "contacts")
        assert result["success"] is False
        assert result["status_code"] == 500
        assert "boom" in result["error"]

    async def test_empty_response_content(self, client, mock_httpx):
        resp = MagicMock()
        resp.status_code = 204
        resp.content = b""
        resp.raise_for_status = MagicMock()
        mock_httpx.request = AsyncMock(return_value=resp)
        result = await client._make_request("DELETE", "contacts/123")
        assert result["success"] is True
        assert result["data"] == {}


# ---------------------------------------------------------------------------
# Contacts
# ---------------------------------------------------------------------------


class TestContacts:
    async def test_get_contacts_default_params(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"contacts": []}))
        result = await client.get_contacts()
        assert result["success"] is True
        call_kwargs = mock_httpx.request.call_args
        params = call_kwargs.kwargs.get("params") or call_kwargs[1].get("params")
        assert params["locationId"] == "test-loc"
        assert params["limit"] == 100

    async def test_get_contacts_with_query(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"contacts": []}))
        await client.get_contacts(query="john")
        params = mock_httpx.request.call_args.kwargs.get("params") or mock_httpx.request.call_args[1].get("params")
        assert params["query"] == "john"

    async def test_get_contact_by_id(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "c1"}))
        result = await client.get_contact("c1")
        assert result["success"] is True

    async def test_create_contact(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "new"}))
        result = await client.create_contact({"firstName": "Jane"})
        assert result["success"] is True
        call_data = mock_httpx.request.call_args.kwargs.get("json") or mock_httpx.request.call_args[1].get("json")
        assert call_data["locationId"] == "test-loc"

    async def test_update_contact(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "c1"}))
        result = await client.update_contact("c1", {"firstName": "Updated"})
        assert result["success"] is True

    async def test_add_tag_to_contact(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"tags": ["Hot-Lead"]}))
        result = await client.add_tag_to_contact("c1", "Hot-Lead")
        assert result["success"] is True

    async def test_search_contacts_by_email(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"contacts": [{"email": "a@b.com"}]}))
        result = await client.search_contacts_by_email("a@b.com")
        assert result["success"] is True


# ---------------------------------------------------------------------------
# Opportunities
# ---------------------------------------------------------------------------


class TestOpportunities:
    async def test_get_opportunities_no_filter(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"opportunities": []}))
        result = await client.get_opportunities()
        assert result["success"] is True

    async def test_get_opportunities_with_filters(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"opportunities": []}))
        await client.get_opportunities(pipeline_id="p1", status="open")
        params = mock_httpx.request.call_args.kwargs.get("params") or mock_httpx.request.call_args[1].get("params")
        assert params["pipelineId"] == "p1"
        assert params["status"] == "open"

    async def test_get_opportunity_by_id(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "opp1"}))
        result = await client.get_opportunity("opp1")
        assert result["success"] is True

    async def test_create_opportunity(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "new_opp"}))
        result = await client.create_opportunity({"name": "Deal"})
        assert result["success"] is True

    async def test_update_opportunity(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "opp1"}))
        result = await client.update_opportunity("opp1", {"status": "won"})
        assert result["success"] is True


# ---------------------------------------------------------------------------
# Pipelines & Conversations & Custom Fields
# ---------------------------------------------------------------------------


class TestPipelinesConversationsFields:
    async def test_get_pipelines(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"pipelines": []}))
        result = await client.get_pipelines()
        assert result["success"] is True

    async def test_get_conversations(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"conversations": []}))
        result = await client.get_conversations("c1")
        assert result["success"] is True

    async def test_send_message(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"messageId": "m1"}))
        result = await client.send_message("c1", "Hello!")
        assert result["success"] is True

    async def test_send_message_email(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"messageId": "m2"}))
        result = await client.send_message("c1", "Hi", message_type="Email")
        assert result["success"] is True

    async def test_get_custom_fields(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"customFields": []}))
        result = await client.get_custom_fields()
        assert result["success"] is True

    async def test_update_custom_field(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"id": "c1"}))
        result = await client.update_custom_field("c1", "field_1", 42)
        assert result["success"] is True


# ---------------------------------------------------------------------------
# Helper / aggregate methods
# ---------------------------------------------------------------------------


class TestHelperMethods:
    async def test_get_hot_leads_filters_by_date(self, client, mock_httpx):
        # Source uses naive datetime.now() as cutoff, so test data must also be naive
        recent_iso = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M:%S")
        old_iso = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S")
        contacts_payload = {
            "contacts": [
                {"id": "c1", "dateAdded": recent_iso},
                {"id": "c2", "dateAdded": old_iso},
            ]
        }
        mock_httpx.request = AsyncMock(return_value=_ok_response(contacts_payload))
        result = await client.get_hot_leads(days=7)
        assert result["success"] is True
        assert result["data"]["count"] == 1
        assert result["data"]["contacts"][0]["id"] == "c1"

    async def test_get_hot_leads_api_failure(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(side_effect=_error_response(500))
        result = await client.get_hot_leads()
        assert result["success"] is False

    async def test_deal_pipeline_summary(self, client, mock_httpx):
        opps_payload = {
            "opportunities": [
                {"pipelineStageId": "s1", "monetaryValue": 100000},
                {"pipelineStageId": "s1", "monetaryValue": 200000},
                {"pipelineStageId": "s2", "monetaryValue": 50000},
            ]
        }
        mock_httpx.request = AsyncMock(return_value=_ok_response(opps_payload))
        result = await client.get_deal_pipeline_summary()
        assert result["success"] is True
        summary = result["data"]
        assert summary["total_deals"] == 3
        assert summary["total_value"] == pytest.approx(350000.0)
        assert summary["by_stage"]["s1"]["count"] == 2
        assert summary["by_stage"]["s2"]["value"] == pytest.approx(50000.0)

    async def test_deal_pipeline_summary_api_failure(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(side_effect=_error_response(500))
        result = await client.get_deal_pipeline_summary()
        assert result["success"] is False


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    async def test_healthy(self, client, mock_httpx):
        mock_httpx.request = AsyncMock(return_value=_ok_response({"contacts": []}))
        result = await client.health_check()
        assert result["healthy"] is True
        assert result["api_key_valid"] is True
        assert result["location_id"] == "test-loc"

    async def test_unhealthy_from_api_failure(self, client, mock_httpx):
        """When _make_request returns success=False, health_check reports unhealthy."""
        mock_httpx.request = AsyncMock(side_effect=_error_response(500))
        result = await client.health_check()
        assert result["healthy"] is False

    async def test_unhealthy_from_exception(self, client):
        """When get_contacts itself raises, the except branch returns error key."""
        client.get_contacts = AsyncMock(side_effect=RuntimeError("network down"))
        result = await client.health_check()
        assert result["healthy"] is False
        assert "network down" in result["error"]
