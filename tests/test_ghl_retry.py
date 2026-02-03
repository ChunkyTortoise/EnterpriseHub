"""
Tests for GHL client retry logic (send_message and add_tags).

The retry mechanism in ghl_real_estate_ai/services/ghl_client.py uses:
- 3 max attempts
- Exponential backoff: 0.5s, 1.0s
- Retries on httpx.HTTPError (includes timeouts and 5xx)
- Raises the last error after exhausting retries
"""

import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

try:
    from ghl_real_estate_ai.services.ghl_client import GHLClient
    from ghl_real_estate_ai.api.schemas.ghl import MessageType
except (ImportError, TypeError, AttributeError):
    pytest.skip("GHL client imports unavailable", allow_module_level=True)


@pytest.fixture
def ghl_client():
    """Create a GHLClient with dummy credentials, test_mode disabled."""
    with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings:
        mock_settings.test_mode = False
        mock_settings.ghl_api_key = "test-key"
        mock_settings.ghl_location_id = "test-location"
        mock_settings.webhook_timeout_seconds = 10
        client = GHLClient(api_key="test-key", location_id="test-location")
    return client


def _make_response(status_code: int, json_data: dict = None):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data or {"ok": True}
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            f"{status_code} error",
            request=MagicMock(),
            response=resp,
        )
    else:
        resp.raise_for_status.return_value = None
    return resp


class TestSendMessageRetry:
    """Test retry behavior in GHLClient.send_message."""

    @pytest.mark.asyncio
    async def test_send_message_retries_on_timeout(self, ghl_client):
        """send_message retries on timeout, succeeds on second attempt."""
        success_response = _make_response(200, {"messageId": "msg_1"})

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectTimeout("Connection timed out")
            return success_response

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await ghl_client.send_message("contact_1", "Hello")
            assert result == {"messageId": "msg_1"}
            assert call_count == 2
            mock_sleep.assert_called_once_with(0.5)  # first retry waits 0.5s

    @pytest.mark.asyncio
    async def test_send_message_retries_on_5xx(self, ghl_client):
        """send_message retries on 5xx HTTP errors."""
        error_response = _make_response(502)
        success_response = _make_response(200, {"messageId": "msg_2"})

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                resp = error_response
                resp.raise_for_status()  # raises HTTPStatusError
            return success_response

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await ghl_client.send_message("contact_2", "Hi")
            assert result == {"messageId": "msg_2"}
            assert call_count == 3

    @pytest.mark.asyncio
    async def test_send_message_succeeds_on_second_try(self, ghl_client):
        """send_message fails once then succeeds on the second attempt."""
        success_response = _make_response(200, {"messageId": "msg_ok"})

        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.HTTPError("Temporary failure")
            return success_response

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await ghl_client.send_message("contact_ok", "Retry me")
            assert result == {"messageId": "msg_ok"}
            assert call_count == 2
            mock_sleep.assert_called_once_with(0.5)

    @pytest.mark.asyncio
    async def test_send_message_gives_up_after_3_retries(self, ghl_client):
        """send_message raises after exhausting all 3 attempts."""
        async def mock_post(*args, **kwargs):
            raise httpx.ConnectTimeout("Connection timed out")

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.ConnectTimeout):
                await ghl_client.send_message("contact_3", "Fail")

            # Should have slept twice (after attempt 1 and 2, not after 3)
            assert mock_sleep.call_count == 2

    @pytest.mark.asyncio
    async def test_add_tags_retries_on_failure(self, ghl_client):
        """add_tags retries on HTTP errors and succeeds."""
        success_response = _make_response(200, {"tags": ["hot-lead"]})

        call_count = 0

        async def mock_put(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise httpx.ConnectTimeout("Timeout")
            return success_response

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.put = mock_put
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            result = await ghl_client.add_tags("contact_4", ["hot-lead"])
            assert result == {"tags": ["hot-lead"]}
            assert call_count == 2

    @pytest.mark.asyncio
    async def test_retry_uses_exponential_backoff(self, ghl_client):
        """Retries use exponential backoff: 0.5s then 1.0s."""
        async def mock_post(*args, **kwargs):
            raise httpx.ConnectTimeout("Timeout")

        with patch("ghl_real_estate_ai.services.ghl_client.settings") as mock_settings, \
             patch("httpx.AsyncClient") as mock_client_cls, \
             patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep:
            mock_settings.test_mode = False
            mock_settings.webhook_timeout_seconds = 10

            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client_cls.return_value = mock_client

            with pytest.raises(httpx.ConnectTimeout):
                await ghl_client.send_message("contact_5", "Backoff test")

            # Verify exponential backoff: 0.5 * 2^0 = 0.5, 0.5 * 2^1 = 1.0
            calls = mock_sleep.call_args_list
            assert len(calls) == 2
            assert calls[0].args[0] == pytest.approx(0.5)
            assert calls[1].args[0] == pytest.approx(1.0)
