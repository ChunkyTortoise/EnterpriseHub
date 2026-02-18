"""
Unit tests for EnhancedGHLClient (aiohttp-based enhanced GHL client).

Source: ghl_real_estate_ai/services/enhanced_ghl_client.py
"""

import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, PropertyMock, patch

import aiohttp
import pytest

# ---------------------------------------------------------------------------
# Module-level patches — heavy imports guarded
# ---------------------------------------------------------------------------

_SETTINGS_PATH = "ghl_real_estate_ai.services.enhanced_ghl_client.settings"
_MODULE = "ghl_real_estate_ai.services.enhanced_ghl_client"


def _make_config(**overrides):
    """Build a GHLConfig with test-safe defaults."""
    defaults = {
        "api_key": "test-key",
        "location_id": "test-loc",
        "base_url": "https://services.leadconnectorhq.com",
        "webhook_base_url": "https://webhook.test",
        "timeout": 5,
        "max_retries": 2,
        "retry_delay": 0.01,
        "rate_limit_requests_per_minute": 300,
    }
    defaults.update(overrides)

    with patch(f"{_SETTINGS_PATH}") as mock_s:
        mock_s.ghl_api_key = defaults["api_key"]
        mock_s.ghl_location_id = defaults["location_id"]
        mock_s.webhook_base_url = defaults["webhook_base_url"]
        mock_s.test_mode = False

        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLConfig

        return GHLConfig(**defaults)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_settings():
    with patch(f"{_SETTINGS_PATH}") as m:
        m.ghl_api_key = "test-key"
        m.ghl_location_id = "test-loc"
        m.webhook_base_url = "https://webhook.test"
        m.test_mode = False
        m.webhook_timeout_seconds = 5
        yield m


@pytest.fixture
def mock_cache():
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.delete = AsyncMock()
    return cache


@pytest.fixture
def client(mock_settings, mock_cache):
    """Create an EnhancedGHLClient with mocked dependencies."""
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient, GHLConfig

    config = GHLConfig(
        api_key="test-key",
        location_id="test-loc",
        base_url="https://services.leadconnectorhq.com",
        webhook_base_url="https://webhook.test",
        timeout=5,
        max_retries=2,
        retry_delay=0.01,
        rate_limit_requests_per_minute=300,
    )
    c = EnhancedGHLClient(config=config, cache_service=mock_cache)
    return c


def _aiohttp_response(status: int = 200, json_body: dict | None = None, text_body: str = ""):
    """Build a fake aiohttp response as an async context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.json = AsyncMock(return_value=json_body or {})
    resp.text = AsyncMock(return_value=text_body)
    return resp


def _session_with_response(status=200, json_body=None):
    """Create a mock aiohttp session where GET/POST/PUT/DELETE return a context manager."""
    resp = _aiohttp_response(status, json_body)
    ctx = MagicMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=False)

    session = AsyncMock(spec=aiohttp.ClientSession)
    session.get.return_value = ctx
    session.post.return_value = ctx
    session.put.return_value = ctx
    session.delete.return_value = ctx
    session.close = AsyncMock()
    return session


# ---------------------------------------------------------------------------
# Async context manager lifecycle
# ---------------------------------------------------------------------------


class TestLifecycle:
    async def test_aenter_creates_session(self, client):
        with patch("aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = AsyncMock()
            result = await client.__aenter__()
            assert result is client
            assert client.session is not None

    async def test_aexit_closes_session(self, client):
        session = AsyncMock()
        client.session = session
        await client.__aexit__(None, None, None)
        session.close.assert_awaited_once()
        assert client.session is None

    async def test_close_when_no_session(self, client):
        client.session = None
        await client.close()  # should not raise

    async def test_ensure_session_idempotent(self, client):
        with patch("aiohttp.ClientSession") as mock_cls:
            mock_cls.return_value = AsyncMock()
            await client._ensure_session()
            first_session = client.session
            await client._ensure_session()
            assert client.session is first_session


# ---------------------------------------------------------------------------
# _handle_response
# ---------------------------------------------------------------------------


class TestHandleResponse:
    async def test_200_returns_json(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(200, {"ok": True})
        result = await client._handle_response(resp)
        assert result == {"ok": True}

    async def test_201_accepted(self, client):
        resp = _aiohttp_response(201, {"id": "new"})
        result = await client._handle_response(resp)
        assert result["id"] == "new"

    async def test_429_rate_limit(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(429, {})
        with pytest.raises(GHLAPIException, match="Rate limit exceeded"):
            await client._handle_response(resp)

    async def test_401_auth_failure(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(401, {})
        with pytest.raises(GHLAPIException, match="Authentication failed"):
            await client._handle_response(resp)

    async def test_403_auth_failure(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(403, {})
        with pytest.raises(GHLAPIException, match="Authentication failed"):
            await client._handle_response(resp)

    async def test_404_not_found(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(404, {})
        with pytest.raises(GHLAPIException, match="Resource not found"):
            await client._handle_response(resp)

    async def test_500_server_error(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        resp = _aiohttp_response(500, {"message": "Internal error", "code": "ERR"})
        with pytest.raises(GHLAPIException, match="Internal error"):
            await client._handle_response(resp)

    async def test_content_type_error_fallback(self, client):
        resp = AsyncMock()
        resp.status = 200
        resp.json = AsyncMock(side_effect=aiohttp.ContentTypeError(MagicMock(), MagicMock()))
        resp.text = AsyncMock(return_value="plain text")
        result = await client._handle_response(resp)
        assert result == {"message": "plain text"}


# ---------------------------------------------------------------------------
# _execute_request — retry logic
# ---------------------------------------------------------------------------


class TestRetryLogic:
    async def test_retries_on_client_error(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        session = _session_with_response()
        # Make get raise a ClientError every time
        session.get.side_effect = aiohttp.ClientError("conn failed")
        client.session = session

        with pytest.raises(GHLAPIException, match="Network error after 2 retries"):
            await client._execute_request("GET", "/contacts")

        # 1 initial + 2 retries = 3 total
        assert session.get.call_count == 3

    async def test_retry_succeeds_on_second_attempt(self, client):
        ok_resp = _aiohttp_response(200, {"ok": True})
        ok_ctx = MagicMock()
        ok_ctx.__aenter__ = AsyncMock(return_value=ok_resp)
        ok_ctx.__aexit__ = AsyncMock(return_value=False)

        session = _session_with_response()
        session.get.side_effect = [aiohttp.ClientError("fail"), ok_ctx]
        client.session = session

        result = await client._execute_request("GET", "/contacts")
        assert result == {"ok": True}
        assert session.get.call_count == 2

    async def test_unsupported_method_raises(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        client.session = _session_with_response()
        with pytest.raises(GHLAPIException, match="Unsupported HTTP method"):
            await client._execute_request("PATCH", "/contacts")

    async def test_unexpected_error_raises(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        session = _session_with_response()
        session.get.side_effect = RuntimeError("unexpected")
        client.session = session

        with pytest.raises(GHLAPIException, match="Unexpected error"):
            await client._execute_request("GET", "/contacts")


# ---------------------------------------------------------------------------
# _make_request — rate limiting & test mode
# ---------------------------------------------------------------------------


class TestMakeRequest:
    async def test_test_mode_returns_mock(self, client, mock_settings):
        mock_settings.test_mode = True
        result = await client._make_request("GET", "/contacts")
        assert result["test_mode"] is True

    async def test_rate_limited_request(self, client):
        client._execute_request = AsyncMock(return_value={"data": "ok"})
        result = await client._make_request("GET", "/contacts", use_rate_limit=True)
        assert result == {"data": "ok"}
        client._execute_request.assert_awaited_once()

    async def test_bypass_rate_limit(self, client):
        client._execute_request = AsyncMock(return_value={"data": "ok"})
        result = await client._make_request("GET", "/contacts", use_rate_limit=False)
        assert result == {"data": "ok"}


# ---------------------------------------------------------------------------
# Webhook processing
# ---------------------------------------------------------------------------


class TestWebhookProcessing:
    async def test_contact_create_webhook(self, client):
        payload = {
            "type": "ContactCreate",
            "contactId": "c1",
            "locationId": "test-loc",
            "contact": {"email": "a@b.com"},
        }
        result = await client.process_webhook(payload)
        assert result["status"] == "processed"
        assert result["action"] == "contact_created"

    async def test_inbound_message_webhook(self, client):
        payload = {
            "type": "InboundMessage",
            "contactId": "c1",
            "locationId": "test-loc",
            "message": {"type": "SMS", "body": "Hello"},
        }
        result = await client.process_webhook(payload)
        assert result["status"] == "processed"
        assert result["action"] == "message_logged"

    async def test_wrong_location_ignored(self, client):
        payload = {"type": "ContactCreate", "contactId": "c1", "locationId": "other-loc"}
        result = await client.process_webhook(payload)
        assert result["status"] == "ignored"
        assert result["reason"] == "different_location"

    async def test_unhandled_webhook_type(self, client):
        payload = {"type": "TaskCompleted", "contactId": "c1", "locationId": "test-loc"}
        result = await client.process_webhook(payload)
        assert result["status"] == "unhandled"

    async def test_contact_update_webhook_missing_handler(self, client):
        """ContactUpdate handler is referenced but not implemented — exception caught."""
        payload = {"type": "ContactUpdate", "contactId": "c1", "locationId": "test-loc"}
        result = await client.process_webhook(payload)
        assert result["status"] == "error"

    async def test_opportunity_create_webhook_missing_handler(self, client):
        """OpportunityCreate handler is referenced but not implemented."""
        payload = {"type": "OpportunityCreate", "contactId": "c1", "locationId": "test-loc"}
        result = await client.process_webhook(payload)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# Contact management
# ---------------------------------------------------------------------------


class TestContactManagement:
    async def test_update_contact_success(self, client, mock_cache):
        client._make_request = AsyncMock(return_value={})
        result = await client.update_contact("c1", {"first_name": "Jane", "email": "j@b.com"})
        assert result is True
        mock_cache.delete.assert_awaited_once()

    async def test_update_contact_failure(self, client):
        client._make_request = AsyncMock(side_effect=Exception("fail"))
        result = await client.update_contact("c1", {"first_name": "Jane"})
        assert result is False

    async def test_search_contacts(self, client):
        client._make_request = AsyncMock(
            return_value={
                "contacts": [
                    {"id": "c1", "firstName": "John", "lastName": "Doe"},
                ]
            }
        )
        results = await client.search_contacts({"email": "j@b.com"})
        assert len(results) == 1
        assert results[0].id == "c1"

    async def test_search_contacts_failure(self, client):
        client._make_request = AsyncMock(side_effect=Exception("fail"))
        results = await client.search_contacts({"query": "test"})
        assert results == []


# ---------------------------------------------------------------------------
# Opportunity management
# ---------------------------------------------------------------------------


class TestOpportunityManagement:
    async def test_create_opportunity_success(self, client):
        client._make_request = AsyncMock(return_value={"opportunity": {"id": "opp1"}})
        opp_id = await client.create_opportunity(
            {
                "name": "Deal",
                "contact_id": "c1",
                "pipeline_id": "p1",
                "pipeline_stage_id": "s1",
            }
        )
        assert opp_id == "opp1"

    async def test_create_opportunity_no_id_returned(self, client):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        client._make_request = AsyncMock(return_value={"opportunity": {}})
        with pytest.raises(GHLAPIException, match="No ID returned"):
            await client.create_opportunity(
                {
                    "name": "Deal",
                    "contact_id": "c1",
                    "pipeline_id": "p1",
                    "pipeline_stage_id": "s1",
                }
            )

    async def test_update_opportunity_stage_success(self, client):
        client._make_request = AsyncMock(return_value={})
        result = await client.update_opportunity_stage("opp1", "s2", reason="qualified")
        assert result is True

    async def test_update_opportunity_stage_failure(self, client):
        client._make_request = AsyncMock(side_effect=Exception("fail"))
        result = await client.update_opportunity_stage("opp1", "s2")
        assert result is False

    async def test_get_opportunities_by_contact(self, client):
        client._make_request = AsyncMock(
            return_value={
                "opportunities": [
                    {
                        "id": "opp1",
                        "name": "Deal",
                        "contactId": "c1",
                        "pipelineId": "p1",
                        "pipelineStageId": "s1",
                        "status": "open",
                        "monetaryValue": 50000,
                    }
                ]
            }
        )
        opps = await client.get_opportunities_by_contact("c1")
        assert len(opps) == 1
        assert opps[0].monetary_value == pytest.approx(50000.0)

    async def test_get_opportunities_by_contact_failure(self, client):
        client._make_request = AsyncMock(side_effect=Exception("fail"))
        opps = await client.get_opportunities_by_contact("c1")
        assert opps == []


# ---------------------------------------------------------------------------
# Utility methods
# ---------------------------------------------------------------------------


class TestUtilityMethods:
    def test_parse_datetime_iso_z(self, client):
        result = client._parse_datetime("2025-06-15T10:30:00.000Z")
        assert result is not None
        assert result.year == 2025
        assert result.month == 6

    def test_parse_datetime_iso_no_ms(self, client):
        result = client._parse_datetime("2025-06-15T10:30:00Z")
        assert result is not None

    def test_parse_datetime_space_format(self, client):
        result = client._parse_datetime("2025-06-15 10:30:00")
        assert result is not None

    def test_parse_datetime_none(self, client):
        assert client._parse_datetime(None) is None

    def test_parse_datetime_invalid(self, client):
        assert client._parse_datetime("not-a-date") is None

    def test_is_lead_silent_no_date(self, client):
        assert client._is_lead_silent({}) is True

    def test_is_lead_silent_recent_message(self, client):
        recent = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
        assert client._is_lead_silent({"lastMessageDate": recent}) is False

    def test_is_lead_silent_old_message(self, client):
        from datetime import timedelta

        old = (datetime.utcnow() - timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        assert client._is_lead_silent({"lastMessageDate": old}) is True


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------


class TestHealthCheck:
    async def test_health_check_test_mode(self, client, mock_settings):
        mock_settings.test_mode = True
        result = await client.health_check()
        assert result["status"] == "healthy"
        assert result["mode"] == "test"

    async def test_health_check_live_success(self, client, mock_settings):
        mock_settings.test_mode = False
        client._make_request = AsyncMock(return_value={"location": {"name": "Jorge Office"}})
        result = await client.health_check()
        assert result["status"] == "healthy"
        assert result["location_name"] == "Jorge Office"

    async def test_health_check_auth_failure(self, client, mock_settings):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        mock_settings.test_mode = False
        client._make_request = AsyncMock(side_effect=GHLAPIException("Auth failed", status_code=401))
        result = await client.health_check()
        assert result["status"] == "unhealthy"
        assert result["api_accessible"] is False

    async def test_health_check_rate_limited(self, client, mock_settings):
        from ghl_real_estate_ai.services.enhanced_ghl_client import GHLAPIException

        mock_settings.test_mode = False
        client._make_request = AsyncMock(side_effect=GHLAPIException("Rate limited", status_code=429))
        result = await client.health_check()
        assert result["status"] == "rate_limited"

    async def test_health_check_unexpected_error(self, client, mock_settings):
        mock_settings.test_mode = False
        client._make_request = AsyncMock(side_effect=RuntimeError("network down"))
        result = await client.health_check()
        assert result["status"] == "unhealthy"
        assert result["api_accessible"] is False
