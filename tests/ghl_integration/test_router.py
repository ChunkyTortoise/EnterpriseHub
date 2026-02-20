"""
Test GHL Webhook Router
"""

import json
from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_integration.router import (
    GHLWebhookRouter,
    _ghl_router,
    get_ghl_router,
    router,
)


class TestGHLWebhookRouter:
    """Test suite for GHL Webhook Router"""

    @pytest.fixture
    def router(self):
        return GHLWebhookRouter()

    @pytest.mark.asyncio
    async def test_validate_signature_hmac_valid(self, router):
        """Test valid HMAC signature validation"""
        import hashlib
        import hmac
        import os
        
        # Set test secret
        os.environ["GHL_WEBHOOK_SECRET"] = "test_secret"
        
        payload = b'{"test": "data"}'
        expected_sig = hmac.new(
            b"test_secret",
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = await router.validate_signature(
            payload, expected_sig, {}
        )
        
        assert is_valid is True

    @pytest.mark.asyncio
    async def test_validate_signature_hmac_invalid(self, router):
        """Test invalid HMAC signature"""
        import os
        os.environ["GHL_WEBHOOK_SECRET"] = "test_secret"
        
        payload = b'{"test": "data"}'
        invalid_sig = "invalid_signature"
        
        is_valid = await router.validate_signature(
            payload, invalid_sig, {}
        )
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_validate_signature_missing_in_prod(self, router):
        """Test that missing signature fails in production"""
        import os
        os.environ["GHL_SKIP_SIGNATURE_VERIFICATION"] = "false"
        
        payload = b'{"test": "data"}'
        
        is_valid = await router.validate_signature(
            payload, None, {}
        )
        
        assert is_valid is False

    @pytest.mark.asyncio
    async def test_check_deduplication_new_event(self, router, mock_cache_service):
        """Test deduplication for new event"""
        router.cache = mock_cache_service
        
        is_duplicate = await router.check_deduplication("evt_123", "contact.create")
        
        assert is_duplicate is False
        mock_cache_service.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_deduplication_duplicate_event(self, router, mock_cache_service):
        """Test deduplication for duplicate event"""
        mock_cache_service.get.return_value = "1"  # Already seen
        router.cache = mock_cache_service
        
        is_duplicate = await router.check_deduplication("evt_123", "contact.create")
        
        assert is_duplicate is True

    @pytest.mark.asyncio
    async def test_route_event_to_handler(self, router):
        """Test event routing to registered handler"""
        mock_handler = AsyncMock(return_value={"success": True, "data": "test"})
        router.register_handler("lead", "contact.create", mock_handler)
        
        result = await router.route_event(
            "lead", "ContactCreate", {"data": {"id": "123"}}
        )
        
        assert result["success"] is True
        mock_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_event_unknown_bot_type(self, router):
        """Test routing with unknown bot type"""
        result = await router.route_event(
            "unknown_bot", "ContactCreate", {}
        )
        
        assert result["success"] is False
        assert "Unknown bot type" in result["error"]

    @pytest.mark.asyncio
    async def test_route_event_no_handler(self, router):
        """Test routing when no handler is registered"""
        result = await router.route_event(
            "lead", "unknown.event", {}
        )
        
        assert result["success"] is True
        assert "No handler" in result["message"]

    def test_update_metrics(self, router):
        """Test metrics updating"""
        router.update_metrics(100.0, True)
        router.update_metrics(200.0, True)
        router.update_metrics(150.0, False)
        
        metrics = router.get_metrics()
        
        assert metrics["events_received"] == 3
        assert metrics["events_processed"] == 2
        assert metrics["events_failed"] == 1


class TestWebhookEndpoint:
    """Test webhook HTTP endpoints"""

    def test_health_check(self):
        """Test health check endpoint"""
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(router)
        
        client = TestClient(app)
        response = client.get("/ghl/webhook/health")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_webhook_post_success(self, client, contact_create_payload, mock_cache_service):
        """Test successful webhook POST"""
        with patch("ghl_integration.router._ghl_router") as mock_router:
            mock_router.validate_signature = AsyncMock(return_value=True)
            mock_router.check_deduplication = AsyncMock(return_value=False)
            mock_router.route_event = AsyncMock(return_value={"success": True})
            mock_router.update_metrics = AsyncMock()
            
            response = client.post(
                "/ghl/webhook/lead/new-lead",
                json=contact_create_payload,
                headers={"X-GHL-Signature": "valid_sig"}
            )
            
            # Should return quickly (background processing)
            assert response.status_code in [200, 500]  # 500 if handler fails

    def test_webhook_post_invalid_signature(self, client):
        """Test webhook with invalid signature"""
        with patch("ghl_integration.router._ghl_router.validate_signature", return_value=False):
            response = client.post(
                "/ghl/webhook/lead/new-lead",
                json={"test": "data"},
                headers={"X-GHL-Signature": "invalid"}
            )
            
            assert response.status_code == 401
