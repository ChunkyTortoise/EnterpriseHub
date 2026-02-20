"""Integration tests for Voice AI Platform API endpoints."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status
from httpx import AsyncClient

from voice_ai.main import create_app


@pytest.fixture
def app():
    """Create FastAPI app instance for testing."""
    return create_app()


@pytest.fixture
async def client(app):
    """Create async HTTP client for testing."""
    from httpx import ASGITransport

    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


class TestHealthEndpoint:
    """Test health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_200(self, client):
        """Test that /health returns 200 OK."""
        response = await client.get("/health")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "voice-ai-platform"


class TestCallsAPI:
    """Test calls management endpoints."""

    @pytest.mark.asyncio
    async def test_initiate_outbound_call(self, client, app):
        """Test POST /api/v1/calls/outbound initiates a call."""
        # Mock Twilio handler
        mock_twilio = MagicMock()
        mock_twilio.phone_number = "+15551234567"
        mock_twilio.initiate_outbound_call = AsyncMock(
            return_value={"call_sid": "CA123456", "status": "initiated"}
        )
        app.state.twilio_handler = mock_twilio

        request_data = {
            "to_number": "+15559876543",
            "bot_type": "lead",
            "context": {},
        }

        response = await client.post("/api/v1/calls/outbound", json=request_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["twilio_call_sid"] == "CA123456"
        assert data["direction"] == "outbound"
        assert data["status"] == "initiated"
        assert data["bot_type"] == "lead"

    @pytest.mark.asyncio
    async def test_handle_inbound_call_returns_twiml(self, client, app):
        """Test POST /api/v1/calls/inbound returns TwiML."""
        # Mock Twilio handler
        mock_twilio = MagicMock()
        mock_twilio.generate_stream_twiml.return_value = (
            '<?xml version="1.0" encoding="UTF-8"?><Response><Connect>'
            '<Stream url="wss://test.com/ws" /></Connect></Response>'
        )
        app.state.twilio_handler = mock_twilio

        form_data = {
            "CallSid": "CA123456",
            "From": "+15551234567",
            "To": "+15559876543",
        }

        response = await client.post("/api/v1/calls/inbound", data=form_data)

        assert response.status_code == status.HTTP_200_OK
        assert "application/xml" in response.headers["content-type"]
        assert "<Response>" in response.text
        assert "<Stream" in response.text

    @pytest.mark.asyncio
    async def test_get_call_by_id(self, client, app):
        """Test GET /api/v1/calls/{call_id} returns call details."""
        call_id = uuid.uuid4()
        mock_call = MagicMock()
        mock_call.id = call_id
        mock_call.tenant_id = uuid.uuid4()
        mock_call.twilio_call_sid = "CA123456"
        mock_call.direction = MagicMock(value="inbound")
        mock_call.from_number = "+15551234567"
        mock_call.to_number = "+15559876543"
        mock_call.status = MagicMock(value="completed")
        mock_call.bot_type = "lead"
        mock_call.duration_seconds = 120.5
        mock_call.lead_score = 85.0
        mock_call.sentiment_scores = {"positive": 0.8}
        mock_call.appointment_booked = True
        mock_call.created_at = "2025-01-01T10:00:00Z"
        mock_call.ended_at = "2025-01-01T10:02:00Z"

        # Mock database session and CallManager
        mock_db = AsyncMock()
        app.state.db_session = mock_db

        with patch("voice_ai.telephony.call_manager.CallManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_call = AsyncMock(return_value=mock_call)
            mock_manager_class.return_value = mock_manager

            response = await client.get(f"/api/v1/calls/{call_id}")

            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["id"] == str(call_id)
            assert data["status"] == "completed"
            assert data["bot_type"] == "lead"
            assert data["duration_seconds"] == 120.5
            assert data["lead_score"] == 85.0
            assert data["appointment_booked"] is True

    @pytest.mark.asyncio
    async def test_get_call_not_found(self, client, app):
        """Test GET /api/v1/calls/{call_id} returns 404 for non-existent call."""
        call_id = uuid.uuid4()

        mock_db = AsyncMock()
        app.state.db_session = mock_db

        with patch("voice_ai.telephony.call_manager.CallManager") as mock_manager_class:
            mock_manager = MagicMock()
            mock_manager.get_call = AsyncMock(return_value=None)
            mock_manager_class.return_value = mock_manager

            response = await client.get(f"/api/v1/calls/{call_id}")

            assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_list_calls_with_pagination(self, client):
        """Test GET /api/v1/calls returns paginated list."""
        response = await client.get("/api/v1/calls?page=1&size=25")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "size" in data
        assert data["page"] == 1
        assert data["size"] == 25


class TestWebhooksAPI:
    """Test webhook endpoints for Twilio callbacks."""

    @pytest.mark.asyncio
    async def test_twilio_status_callback(self, client):
        """Test POST /api/v1/webhooks/twilio/status processes status updates."""
        form_data = {
            "CallSid": "CA123456",
            "CallStatus": "completed",
            "CallDuration": "120",
        }

        response = await client.post("/api/v1/webhooks/twilio/status", data=form_data)

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "ok"


class TestTranscriptsAPI:
    """Test transcript retrieval endpoints (placeholder)."""

    @pytest.mark.asyncio
    async def test_get_call_transcript(self, client):
        """Test GET /api/v1/transcripts/{call_id} returns transcript."""
        # Placeholder - API not yet implemented
        call_id = uuid.uuid4()

        # When implemented, this should return the full transcript
        # For now, we expect 404 or similar
        # response = await client.get(f"/api/v1/transcripts/{call_id}")
        # assert response.status_code in [200, 404]
        pass


class TestAgentsAPI:
    """Test agent persona management endpoints (placeholder)."""

    @pytest.mark.asyncio
    async def test_list_agent_personas(self, client):
        """Test GET /api/v1/agents lists available personas."""
        # Placeholder - API not yet implemented
        # response = await client.get("/api/v1/agents")
        # assert response.status_code == 200
        pass

    @pytest.mark.asyncio
    async def test_create_agent_persona(self, client):
        """Test POST /api/v1/agents creates new persona."""
        # Placeholder - API not yet implemented
        # persona_data = {
        #     "name": "Jorge - Lead Bot",
        #     "bot_type": "lead",
        #     "voice_id": "21m00Tcm4TlvDq8ikWAM",
        #     "language": "en",
        # }
        # response = await client.post("/api/v1/agents", json=persona_data)
        # assert response.status_code == 201
        pass


class TestAnalyticsAPI:
    """Test analytics and reporting endpoints (placeholder)."""

    @pytest.mark.asyncio
    async def test_get_call_analytics(self, client):
        """Test GET /api/v1/analytics returns aggregated metrics."""
        # Placeholder - API not yet implemented
        # response = await client.get("/api/v1/analytics?period=7d")
        # assert response.status_code == 200
        # data = response.json()
        # assert "metrics" in data
        # assert "sentiment" in data
        # assert "costs" in data
        pass


class TestErrorHandling:
    """Test API error handling."""

    @pytest.mark.asyncio
    async def test_global_exception_handler(self, client, app):
        """Test that unhandled exceptions return 500 with structured error."""
        # Force an error by accessing non-existent endpoint that raises
        # (This is a basic test - in real code you'd test actual error scenarios)

        @app.get("/api/v1/test/error")
        async def force_error():
            raise ValueError("Test error")

        response = await client.get("/api/v1/test/error")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "error" in data
        assert data["error"] == "internal_server_error"


class TestCORS:
    """Test CORS middleware configuration."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses."""
        response = await client.options(
            "/health",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            },
        )

        # CORS middleware should add these headers
        assert "access-control-allow-origin" in response.headers


class TestWebSocketEndpoint:
    """Test WebSocket voice streaming endpoint (placeholder)."""

    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection for voice streaming."""
        # Placeholder - WebSocket testing requires special setup
        # from fastapi.testclient import TestClient
        # with TestClient(app) as test_client:
        #     with test_client.websocket_connect("/api/v1/voice/ws") as websocket:
        #         # Test bidirectional audio streaming
        #         pass
        pass
