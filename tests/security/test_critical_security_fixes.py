import pytest
pytestmark = pytest.mark.integration

"""
CRITICAL SECURITY TESTS

Tests to verify that all critical silent failure vulnerabilities have been properly fixed.
These tests ensure that the security fixes prevent silent failures that could mask
important system issues or compromise security policies.
"""

import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest

from ghl_real_estate_ai.api.middleware.jwt_auth import JWTAuth
from ghl_real_estate_ai.api.schemas.ghl import ActionType, GHLAction, MessageType
from ghl_real_estate_ai.services.ghl_client import GHLClient


class TestCriticalSecurityFixes:
    """Test suite for critical security vulnerability fixes."""

    def setup_method(self):
        """Set up test environment."""
        self.client = GHLClient(api_key="test-key", location_id="test-location")

    @pytest.mark.asyncio
    async def test_remove_tags_no_longer_silent_failure(self):
        """
        CRITICAL TEST: Verify remove_tags no longer silently fails.

        Before fix: Method logged intent but didn't actually remove tags
        After fix: Method properly removes tags or raises exception
        """
        with patch("httpx.AsyncClient") as mock_client:
            # Setup mock to simulate tag removal
            mock_response_get = Mock()
            mock_response_get.raise_for_status = Mock()
            mock_response_get.json.return_value = {"tags": ["tag1", "tag2", "tag3"]}

            mock_response_put = Mock()
            mock_response_put.raise_for_status = Mock()
            mock_response_put.json.return_value = {"status": "success"}

            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.get.return_value = mock_response_get
            mock_client_instance.put.return_value = mock_response_put

            # Test successful tag removal
            result = await self.client.remove_tags("contact123", ["tag2"])

            # Verify actual API calls were made
            assert mock_client_instance.get.called
            assert mock_client_instance.put.called

            # Verify proper response structure
            assert result["status"] == "success"
            assert "removed_tags" in result
            assert "remaining_tags" in result

    @pytest.mark.asyncio
    async def test_remove_tags_validation_errors(self):
        """Test that remove_tags properly validates inputs and raises errors."""

        # Test empty contact_id
        with pytest.raises(ValueError, match="Contact ID is required"):
            await self.client.remove_tags("", ["tag1"])

        # Test None contact_id
        with pytest.raises(ValueError, match="Contact ID is required"):
            await self.client.remove_tags(None, ["tag1"])

        # Test empty tags list
        with pytest.raises(ValueError, match="Valid tags list is required"):
            await self.client.remove_tags("contact123", [])

        # Test None tags
        with pytest.raises(ValueError, match="Valid tags list is required"):
            await self.client.remove_tags("contact123", None)

    def test_get_conversations_no_longer_silent_failure(self):
        """
        CRITICAL TEST: Verify get_conversations no longer returns empty array on errors.

        Before fix: Returned [] on any API error
        After fix: Raises appropriate exceptions
        """
        with patch("httpx.Client") as mock_client:
            # Setup mock to simulate HTTP error
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.side_effect = httpx.HTTPStatusError(
                "Server Error", request=Mock(), response=Mock(status_code=500)
            )

            # Should now raise exception instead of returning empty list
            with pytest.raises(httpx.HTTPStatusError):
                self.client.get_conversations(limit=10)

    def test_get_opportunities_no_longer_silent_failure(self):
        """
        CRITICAL TEST: Verify get_opportunities no longer returns empty array on errors.

        Before fix: Returned [] on any API error
        After fix: Raises appropriate exceptions
        """
        with patch("httpx.Client") as mock_client:
            # Setup mock to simulate timeout
            mock_client_instance = mock_client.return_value.__enter__.return_value
            mock_client_instance.get.side_effect = httpx.TimeoutException("Request timeout")

            # Should now raise ConnectionError instead of returning empty list
            with pytest.raises(ConnectionError, match="Timeout fetching opportunities"):
                self.client.get_opportunities()

    def test_jwt_no_weak_secret_fallback(self):
        """
        CRITICAL TEST: Verify JWT authentication no longer allows weak secret fallbacks.

        Before fix: Used weak dev secret as fallback
        After fix: Raises ValueError if no proper secret is set
        """
        # Test with no JWT_SECRET_KEY environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY environment variable must be set"):
                # This should fail during module import/initialization
                import importlib

                from ghl_real_estate_ai.api.middleware import jwt_auth

                importlib.reload(jwt_auth)

    def test_jwt_requires_strong_secret(self):
        """Test that JWT requires secrets of minimum length."""
        weak_secret = "short"

        with patch.dict(os.environ, {"JWT_SECRET_KEY": weak_secret}):
            with pytest.raises(ValueError, match="JWT_SECRET_KEY must be at least 32 characters"):
                import importlib

                from ghl_real_estate_ai.api.middleware import jwt_auth

                importlib.reload(jwt_auth)

    @pytest.mark.asyncio
    async def test_apply_actions_critical_failure_escalation(self):
        """
        CRITICAL TEST: Verify apply_actions properly escalates critical failures.

        Before fix: Continued with other actions even after critical failures
        After fix: Raises RuntimeError for critical security action failures
        """
        actions = [
            GHLAction(type=ActionType.REMOVE_TAG, tag="security-tag"),
            GHLAction(type=ActionType.ADD_TAG, tag="normal-tag"),
        ]

        with patch.object(self.client, "remove_tags") as mock_remove:
            mock_remove.side_effect = Exception("Critical tag removal failed")

            # Should raise RuntimeError and stop processing
            with pytest.raises(RuntimeError, match="Critical security action failed"):
                await self.client.apply_actions("contact123", actions)

    def test_dashboard_fetch_no_silent_masking(self):
        """
        CRITICAL TEST: Verify dashboard fetch no longer masks critical failures.

        Before fix: Returned error structure that looked like valid data
        After fix: Raises RuntimeError on fetch failures
        """
        with patch.object(self.client, "get_conversations") as mock_conversations:
            mock_conversations.side_effect = Exception("API failure")

            # Should raise RuntimeError instead of returning masked error data
            with pytest.raises(RuntimeError, match="Dashboard data fetch failed"):
                self.client.fetch_dashboard_data()

    def test_jwt_token_validation_enhanced(self):
        """Test enhanced JWT token validation."""
        # Test with missing required fields
        token_payload = {"exp": datetime.utcnow() + timedelta(minutes=30)}

        with patch("jose.jwt.decode", return_value=token_payload):
            from fastapi import HTTPException

            from ghl_real_estate_ai.api.middleware.jwt_auth import JWTAuth

            with pytest.raises(HTTPException) as exc_info:
                JWTAuth.verify_token("invalid-token")

            assert exc_info.value.status_code == 401
            assert "Invalid token structure" in str(exc_info.value.detail)


class TestSecurityLogging:
    """Test that security events are properly logged with error IDs."""

    @pytest.mark.asyncio
    async def test_security_events_have_error_ids(self):
        """Verify all security failures include proper error IDs for tracking."""
        client = GHLClient(api_key="test", location_id="test")

        with patch("ghl_real_estate_ai.ghl_utils.logger.get_logger") as mock_logger:
            logger_instance = Mock()
            mock_logger.return_value = logger_instance

            # Test validation error logging
            try:
                await client.remove_tags("", ["tag"])
            except ValueError:
                pass

            # Verify error was logged with proper structure
            logger_instance.error.assert_called()
            call_args = logger_instance.error.call_args
            extra_data = call_args[1]["extra"]

            assert "error_id" in extra_data
            assert "security_event" in extra_data
            assert extra_data["error_id"].startswith("GHL_")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])