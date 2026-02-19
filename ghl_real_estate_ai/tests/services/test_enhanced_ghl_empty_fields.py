"""
Tests for empty-field graceful handling in EnhancedGHLClient.

Validates that update_contact skips empty custom field IDs
and trigger_workflow returns early on empty workflow_id.
"""

import os
from unittest.mock import AsyncMock, patch

import pytest

# Ensure test env vars are set before importing production code
for _k, _v in {
    "ANTHROPIC_API_KEY": "sk-ant-test-fake",
    "GHL_API_KEY": "test_ghl_api_key",
    "GHL_LOCATION_ID": "test_location_id",
    "JWT_SECRET_KEY": "test-jwt-secret-key-for-testing-only-minimum-32-chars",
}.items():
    if _k not in os.environ:
        os.environ[_k] = _v

from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient


@pytest.fixture
def client():
    """Create an EnhancedGHLClient in test mode."""
    with patch("ghl_real_estate_ai.services.enhanced_ghl_client.settings") as mock_settings:
        mock_settings.test_mode = True
        mock_settings.ghl_api_key = "test_key"
        mock_settings.ghl_location_id = "test_loc"
        mock_settings.webhook_base_url = "http://localhost"
        c = EnhancedGHLClient()
    # Ensure test_mode is on for _make_request
    return c


class TestUpdateContactEmptyFields:
    """Tests for update_contact empty/None custom field ID handling."""

    @pytest.mark.asyncio
    async def test_skips_empty_string_field_id(self, client):
        """Should skip custom fields with empty string IDs and not crash."""
        client._make_request = AsyncMock(return_value={"status": "ok"})
        client.cache_service = AsyncMock()
        client.cache_service.delete = AsyncMock()

        result = await client.update_contact(
            "contact_1",
            {"custom_fields": {"": "some_value", "valid_id": "real_value"}},
        )

        assert result is True
        # Verify only the valid field was sent
        call_args = client._make_request.call_args
        payload = call_args[1].get("data", {})
        custom_fields = payload.get("customFields", [])
        assert len(custom_fields) == 1
        assert custom_fields[0]["id"] == "valid_id"

    @pytest.mark.asyncio
    async def test_skips_none_field_id(self, client):
        """Should skip custom fields with None IDs."""
        client._make_request = AsyncMock(return_value={"status": "ok"})
        client.cache_service = AsyncMock()
        client.cache_service.delete = AsyncMock()

        result = await client.update_contact(
            "contact_1",
            {"custom_fields": {None: "some_value"}},
        )

        assert result is True
        call_args = client._make_request.call_args
        # _make_request is called as (method, endpoint, data=payload)
        payload = call_args[1].get("data") if "data" in call_args[1] else call_args[0][2] if len(call_args[0]) > 2 else {}
        # All fields were empty/None, so customFields should not be in payload
        assert "customFields" not in payload


class TestTriggerWorkflowEmptyId:
    """Tests for trigger_workflow empty workflow_id handling."""

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_empty_workflow_id(self, client):
        """Should return {} immediately when workflow_id is empty string."""
        client._make_request = AsyncMock()

        result = await client.trigger_workflow("contact_1", "")

        assert result == {}
        client._make_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_empty_dict_for_none_workflow_id(self, client):
        """Should return {} immediately when workflow_id is None."""
        client._make_request = AsyncMock()

        result = await client.trigger_workflow("contact_1", None)

        assert result == {}
        client._make_request.assert_not_called()

    @pytest.mark.asyncio
    async def test_proceeds_normally_for_valid_workflow_id(self, client):
        """Should proceed with API call when workflow_id is valid."""
        with patch("ghl_real_estate_ai.services.enhanced_ghl_client.settings") as mock_settings:
            mock_settings.test_mode = True
            result = await client.trigger_workflow("contact_1", "wf_abc123")

        # In test mode it returns a mock dict, not empty
        assert result.get("workflow_id") == "wf_abc123" or result.get("status") == "mocked"
