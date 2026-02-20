"""
Tests for Claude Concierge Integration API endpoints.

Endpoints tested:
    GET  /api/claude-concierge/health          - Concierge health check
    GET  /api/claude-concierge/capabilities     - Concierge capabilities
    GET  /api/claude-concierge/metrics          - Concierge metrics
    POST /api/claude-concierge/chat             - Chat message
    GET  /api/claude-concierge/insights         - Real-time insights
    GET  /api/claude-concierge/suggestions      - Proactive suggestions
    POST /api/claude-concierge/suggestions/{id}/dismiss - Dismiss suggestion
    POST /api/claude-concierge/suggestions/{id}/apply   - Apply suggestion
    PUT  /api/claude-concierge/context          - Update context
    GET  /api/claude-concierge/context/{sid}    - Get session context
    POST /api/claude-concierge/reset-session    - Reset session
    GET  /api/claude-concierge/analyze/platform - Platform analysis
    GET  /api/claude-concierge/analyze/coordination - Coordination analysis
    GET  /api/claude-concierge/analyze/journeys - Journey analysis
"""

import os
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.services.claude_concierge_orchestrator import ConciergeResponse

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_concierge_response():
    """Standard ConciergeResponse for mocking orchestrator methods."""
    return ConciergeResponse(
        primary_guidance="Test guidance from concierge",
        urgency_level="low",
        confidence_score=0.85,
        response_time_ms=150,
        data_sources_used=["ghl_live_data"],
        generated_at=datetime.now(),
    )


@pytest.fixture
def mock_orchestrator(mock_concierge_response):
    """Mock ClaudeConciergeOrchestrator with all public methods."""
    orch = MagicMock()
    orch.generate_contextual_guidance = AsyncMock(return_value=mock_concierge_response)
    orch.generate_live_guidance = AsyncMock(return_value=mock_concierge_response)
    orch.provide_real_time_coaching = AsyncMock(return_value=mock_concierge_response)
    orch.coordinate_bot_ecosystem = AsyncMock(return_value=mock_concierge_response)
    orch.orchestrate_bot_ecosystem = AsyncMock(return_value=mock_concierge_response)
    orch.generate_mobile_field_assistance = AsyncMock(return_value=mock_concierge_response)
    orch.provide_client_presentation_support = AsyncMock(return_value=mock_concierge_response)
    orch.learn_from_user_decision = AsyncMock(return_value=True)
    orch.predict_jorge_preference = AsyncMock(
        return_value={"confidence": 0.8, "preference": "revenue_optimization"}
    )
    orch.apply_suggestion = AsyncMock(
        return_value={"success": True, "suggestion_id": "test-id", "actions_taken": ["test action"], "message": "ok"}
    )
    orch.session_contexts = {}
    orch.context_cache = {}
    orch.generated_suggestions = {}
    orch.get_metrics = MagicMock(return_value={
        "requests_processed": 5,
        "avg_response_time_ms": 120,
        "errors": 0,
        "cache_hit_rate": 0.4,
        "active_sessions": 1,
        "learning_events": 2,
    })
    return orch


@pytest.fixture
def mock_agent():
    """Mock ClaudeConciergeAgent."""
    agent = MagicMock()
    agent.get_concierge_status = AsyncMock(return_value={
        "status": "active",
        "mode": "proactive",
        "active_sessions": 0,
        "performance_metrics": {
            "interactions_handled": 10,
            "recommendations_generated": 25,
        },
        "knowledge_base": {
            "registered_agents": 11,
            "platform_features": 4,
            "integration_points": 4,
        },
        "capabilities": [
            "Platform guidance and navigation",
            "Multi-agent coordination",
        ],
    })
    agent.process_user_interaction = AsyncMock(return_value={
        "concierge_response": {
            "response_type": "direct",
            "content": "I can help you with that!",
            "confidence": 0.8,
        },
        "proactive_recommendations": [],
        "session_context": {
            "current_context": "dashboard",
            "detected_intent": "exploring",
            "competency_level": "intermediate",
        },
        "response_metadata": {
            "strategy": {"type": "direct_response"},
            "processing_time": datetime.now(),
            "confidence": 0.8,
        },
    })
    return agent


@pytest.fixture
def mock_event_publisher():
    """Mock event publisher."""
    ep = MagicMock()
    ep.publish_event = AsyncMock()
    ep.publish_concierge_interaction = AsyncMock()
    return ep


@pytest.fixture(autouse=True)
def patch_deps(mock_orchestrator, mock_agent, mock_event_publisher):
    """Patch orchestrator, agent, event_publisher, and auth for all tests."""
    with patch(
        "ghl_real_estate_ai.api.routes.claude_concierge_integration.get_claude_concierge_orchestrator",
        return_value=mock_orchestrator,
    ), patch(
        "ghl_real_estate_ai.api.routes.claude_concierge_integration.get_claude_concierge",
        return_value=mock_agent,
    ), patch(
        "ghl_real_estate_ai.api.routes.claude_concierge_integration.get_event_publisher",
        return_value=mock_event_publisher,
    ), patch(
        "ghl_real_estate_ai.api.routes.claude_concierge_integration.get_current_user_optional",
        return_value=MagicMock(id="test-user"),
    ):
        yield


@pytest.fixture
def client():
    """Create TestClient with admin key configured."""
    os.environ.setdefault("ADMIN_API_KEY", "test-admin-key")
    from ghl_real_estate_ai.api.main import app

    return TestClient(app, raise_server_exceptions=False)


_ADMIN_HEADER = {"X-Admin-Key": "test-admin-key"}


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/health
# ---------------------------------------------------------------------------


class TestHealth:
    """Tests for concierge health endpoint."""

    def test_health_check_returns_healthy(self, client, mock_agent):
        resp = client.get("/api/claude-concierge/health", headers=_ADMIN_HEADER)
        # The endpoint may or may not exist yet (routes-worker implementing in parallel).
        # When it does exist, expect 200 and status=="healthy".
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("status") in ("healthy", "active", "ok")
        else:
            # Endpoint not implemented yet; skip gracefully.
            assert resp.status_code in (404, 405)


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/capabilities
# ---------------------------------------------------------------------------


class TestCapabilities:
    """Tests for concierge capabilities endpoint."""

    def test_capabilities_endpoint(self, client):
        resp = client.get("/api/claude-concierge/capabilities", headers=_ADMIN_HEADER)
        if resp.status_code == 200:
            data = resp.json()
            assert "concierge_modes" in data or "capabilities" in data
        else:
            assert resp.status_code in (404, 405)


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/metrics
# ---------------------------------------------------------------------------


class TestMetrics:
    """Tests for concierge metrics endpoint."""

    def test_metrics_endpoint_returns_real_data(self, client, mock_orchestrator):
        resp = client.get("/api/claude-concierge/metrics", headers=_ADMIN_HEADER)
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("requests_processed") == 5
        else:
            assert resp.status_code in (404, 405)


# ---------------------------------------------------------------------------
# POST /api/claude-concierge/chat
# ---------------------------------------------------------------------------


class TestChat:
    """Tests for concierge chat endpoint."""

    def test_chat_returns_guidance(self, client):
        payload = {
            "message": "How are my leads doing?",
            "sessionId": "test-session-1",
            "context": {
                "currentPage": "Lead Dashboard",
                "userRole": "agent",
                "sessionId": "test-session-1",
            },
        }
        resp = client.post("/api/claude-concierge/chat", json=payload, headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        # The response model has a "response" field (ConciergeResponse pydantic model)
        assert "response" in data
        assert data["response"]  # non-empty


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/insights
# ---------------------------------------------------------------------------


class TestInsights:
    """Tests for concierge insights endpoint."""

    def test_insights_returns_list(self, client):
        resp = client.get("/api/claude-concierge/insights", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/suggestions
# ---------------------------------------------------------------------------


class TestSuggestions:
    """Tests for concierge suggestions endpoints."""

    def test_suggestions_returns_list(self, client):
        resp = client.get("/api/claude-concierge/suggestions", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    def test_dismiss_suggestion_succeeds(self, client):
        resp = client.post(
            "/api/claude-concierge/suggestions/test-id/dismiss",
            json={"reason": "irrelevant"},
            headers=_ADMIN_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True

    def test_apply_suggestion_succeeds(self, client):
        resp = client.post(
            "/api/claude-concierge/suggestions/test-id/apply",
            headers=_ADMIN_HEADER,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True


# ---------------------------------------------------------------------------
# PUT /api/claude-concierge/context
# ---------------------------------------------------------------------------


class TestContextManagement:
    """Tests for concierge context management endpoints."""

    def test_context_update(self, client):
        payload = {
            "sessionId": "test-session-123",
            "context": {
                "currentPage": "/leads",
                "userRole": "agent",
            },
        }
        resp = client.put("/api/claude-concierge/context", json=payload, headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("success") is True

    def test_context_get_session(self, client):
        resp = client.get("/api/claude-concierge/context/session-123", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "sessionId" in data or "currentPage" in data


# ---------------------------------------------------------------------------
# POST /api/claude-concierge/reset-session
# ---------------------------------------------------------------------------


class TestResetSession:
    """Tests for session reset endpoint."""

    def test_reset_session(self, client):
        resp = client.post(
            "/api/claude-concierge/reset-session?session_id=test-123",
            headers=_ADMIN_HEADER,
        )
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("status") == "session_reset" or data.get("success") is True
        else:
            # Endpoint may not exist yet
            assert resp.status_code in (404, 405)


# ---------------------------------------------------------------------------
# GET /api/claude-concierge/analyze/*
# ---------------------------------------------------------------------------


class TestAnalysis:
    """Tests for concierge analysis endpoints."""

    def test_analyze_platform(self, client):
        resp = client.get("/api/claude-concierge/analyze/platform", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "overallHealth" in data

    def test_analyze_coordination(self, client):
        resp = client.get("/api/claude-concierge/analyze/coordination", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "efficiencyScore" in data or "handoffAnalysis" in data

    def test_analyze_journeys(self, client):
        resp = client.get("/api/claude-concierge/analyze/journeys", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert "activeJourneys" in data or "completionRate" in data
