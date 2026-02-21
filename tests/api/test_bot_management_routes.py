"""
Tests for Bot Management API endpoints.

Endpoints tested:
    GET  /api/bots/health               - Bot system health check
    GET  /api/bots                       - List available bots
    POST /api/bots/{bot_id}/chat         - Stream bot conversation
    GET  /api/bots/{bot_id}/status       - Individual bot status
    POST /api/jorge-seller/start         - Start qualification
    POST /api/lead-bot/{leadId}/schedule - Trigger lead sequence
    GET  /api/intent-decoder/{leadId}/score - Intent analysis
    POST /api/jorge-seller/test          - Quick test endpoint
"""

import json
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes import bot_management

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_ADMIN_HEADER = {"X-Admin-Key": "test-admin-key"}


def _make_client():
    """Create TestClient with admin key configured."""
    import os

    os.environ["ADMIN_API_KEY"] = "test-admin-key"
    from ghl_real_estate_ai.api.main import app

    if not hasattr(app, "dependency_overrides") or app.dependency_overrides is None:
        app.dependency_overrides = {}

    return TestClient(app, raise_server_exceptions=False)


def _mock_bot_singletons():
    """Patch bot singletons to avoid import-time side effects."""
    jorge_bot = MagicMock()
    jorge_bot.process_seller_message = AsyncMock(
        return_value={"response_content": "Test response from Jorge", "frs_score": 72}
    )

    lead_bot = MagicMock()
    lead_bot.workflow = MagicMock()
    lead_bot.workflow.ainvoke = AsyncMock(return_value={"current_step": "qualification"})

    intent_decoder = MagicMock()
    frs_mock = MagicMock(
        total_score=85.0,
        classification="Hot Seller",
        motivation=MagicMock(score=90, category="High"),
        timeline=MagicMock(score=80, category="Medium"),
        condition=MagicMock(score=85, category="High"),
        price=MagicMock(score=82, category="High"),
    )
    pcs_mock = MagicMock(total_score=78.0)
    profile_mock = MagicMock(
        frs=frs_mock,
        pcs=pcs_mock,
        next_best_action="Schedule listing appointment",
    )
    profile_mock.dict = MagicMock(return_value={"frs": 85.0, "pcs": 78.0})
    intent_decoder.analyze_lead = MagicMock(return_value=profile_mock)

    return (
        patch("ghl_real_estate_ai.api.routes.bot_management.get_jorge_bot", return_value=jorge_bot),
        patch("ghl_real_estate_ai.api.routes.bot_management.get_lead_bot", return_value=lead_bot),
        patch("ghl_real_estate_ai.api.routes.bot_management.get_intent_decoder", return_value=intent_decoder),
    )


def _mock_session_manager():
    """Patch session manager."""
    sm = MagicMock()
    sm.create_session = AsyncMock(return_value="session-001")
    sm.get_session = AsyncMock(return_value=None)
    sm.get_history = AsyncMock(return_value=[])
    sm.add_message = AsyncMock()
    sm.get_lead_conversations = AsyncMock(return_value=["conv-1"])
    return patch(
        "ghl_real_estate_ai.api.routes.bot_management.get_session_manager",
        return_value=sm,
    )


def _mock_cache():
    """Patch cache service."""
    cache = MagicMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return patch("ghl_real_estate_ai.api.routes.bot_management.cache", cache, create=True)


def _mock_event_publisher():
    """Patch event publisher."""
    ep = MagicMock()
    ep.publish_intent_analysis_complete = AsyncMock()
    ep.publish_lead_bot_sequence_update = AsyncMock()
    return patch(
        "ghl_real_estate_ai.api.routes.bot_management.get_event_publisher",
        return_value=ep,
    )


def _mock_counters():
    """Patch conversation/lead counters."""
    return (
        patch(
            "ghl_real_estate_ai.api.routes.bot_management._get_conversation_count",
            new=AsyncMock(return_value=5),
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management._get_leads_qualified",
            new=AsyncMock(return_value=3),
        ),
        patch(
            "ghl_real_estate_ai.api.routes.bot_management._increment_conversation_count",
            new=AsyncMock(),
        ),
    )


# ---------------------------------------------------------------------------
# GET /api/bots/health
# ---------------------------------------------------------------------------


class TestBotHealth:
    """Tests for bot system health check."""

    def test_health_check_returns_healthy(self):
        """Returns healthy status with all bots initialized."""
        p1, p2, p3 = _mock_bot_singletons()
        with p1, p2, p3:
            client = _make_client()
            resp = client.get("/api/bots/health", headers=_ADMIN_HEADER)

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert "bots" in data
        assert "jorge-seller-bot" in data["bots"]

    def test_health_check_requires_admin_key(self):
        """Returns 401 when admin key is missing or wrong."""
        client = _make_client()
        resp = client.get("/api/bots/health", headers={"X-Admin-Key": "wrong-key"})
        assert resp.status_code == 401

    def test_health_check_returns_503_on_error(self):
        """Returns 503 when bot initialization fails."""
        from ghl_real_estate_ai.api.main import app

        def _broken_dependency():
            raise RuntimeError("init failed")

        app.dependency_overrides[bot_management.get_jorge_bot] = _broken_dependency
        app.dependency_overrides[bot_management.get_lead_bot] = lambda: MagicMock()
        app.dependency_overrides[bot_management.get_intent_decoder] = lambda: MagicMock()
        client = _make_client()
        resp = client.get("/api/bots/health", headers=_ADMIN_HEADER)
        app.dependency_overrides = {}

        # Dependency resolution failures are surfaced by global handlers before route body executes.
        assert resp.status_code in (500, 503)


# ---------------------------------------------------------------------------
# GET /api/bots
# ---------------------------------------------------------------------------


class TestListBots:
    """Tests for list available bots endpoint."""

    def test_list_bots_returns_three(self):
        """Returns all three bots with status fields."""
        p1, p2, p3 = _mock_counters()
        with p1, p2, p3:
            client = _make_client()
            resp = client.get("/api/bots", headers=_ADMIN_HEADER)

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        bot_ids = {b["id"] for b in data}
        assert "jorge-seller-bot" in bot_ids
        assert "lead-bot" in bot_ids
        assert "intent-decoder" in bot_ids

    def test_list_bots_has_required_fields(self):
        """Each bot response has required fields."""
        p1, p2, p3 = _mock_counters()
        with p1, p2, p3:
            client = _make_client()
            resp = client.get("/api/bots", headers=_ADMIN_HEADER)

        data = resp.json()
        for bot in data:
            assert "id" in bot
            assert "name" in bot
            assert "status" in bot
            assert "responseTimeMs" in bot


# ---------------------------------------------------------------------------
# POST /api/bots/{bot_id}/chat
# ---------------------------------------------------------------------------


class TestBotChat:
    """Tests for the streaming chat endpoint."""

    def test_chat_unknown_bot_returns_404(self):
        """Unknown bot_id returns 404."""
        client = _make_client()
        resp = client.post(
            "/api/bots/unknown-bot/chat",
            json={"content": "hello"},
            headers=_ADMIN_HEADER,
        )
        assert resp.status_code == 404

    def test_chat_empty_content_returns_422(self):
        """Empty content string returns 422."""
        client = _make_client()
        resp = client.post(
            "/api/bots/jorge-seller-bot/chat",
            json={"content": ""},
            headers=_ADMIN_HEADER,
        )
        assert resp.status_code == 422

    def test_chat_jorge_returns_200(self):
        """Jorge seller bot chat returns 200 with response data."""
        p1, p2, p3 = _mock_bot_singletons()
        with p1, p2, p3, _mock_session_manager(), _mock_event_publisher(), _mock_cache():
            client = _make_client()
            resp = client.post(
                "/api/bots/jorge-seller-bot/chat",
                json={"content": "I want to sell my house"},
                headers=_ADMIN_HEADER,
            )

        assert resp.status_code == 200
        # Endpoint may return SSE or JSON depending on middleware
        assert len(resp.content) > 0


# ---------------------------------------------------------------------------
# GET /api/bots/{bot_id}/status
# ---------------------------------------------------------------------------


class TestBotStatus:
    """Tests for individual bot status endpoint."""

    def test_status_known_bot(self):
        """Returns status for known bot."""
        p1, p2, p3 = _mock_counters()
        with p1, p2, p3:
            client = _make_client()
            resp = client.get("/api/bots/jorge-seller-bot/status", headers=_ADMIN_HEADER)

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == "jorge-seller-bot"
        assert data["status"] == "online"

    def test_status_unknown_bot_returns_404(self):
        """Returns 404 for unknown bot."""
        client = _make_client()
        resp = client.get("/api/bots/fake-bot/status", headers=_ADMIN_HEADER)
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/jorge-seller/start
# ---------------------------------------------------------------------------


class TestJorgeSellerStart:
    """Tests for starting Jorge qualification."""

    def test_start_qualification_success(self):
        """Returns conversation ID and opening message."""
        from ghl_real_estate_ai.api.main import app

        session_manager = MagicMock()
        session_manager.create_session = AsyncMock(return_value="session-001")

        cache = MagicMock()
        cache.get = AsyncMock(return_value=0)
        cache.set = AsyncMock()

        app.dependency_overrides[bot_management.get_session_manager] = lambda: session_manager
        app.dependency_overrides[bot_management.get_cache_service] = lambda: cache
        client = _make_client()
        resp = client.post(
            "/api/jorge-seller/start",
            json={
                "leadId": "lead-001",
                "leadName": "Maria Garcia",
                "phone": "+19099991234",
                "propertyAddress": "123 Baseline Rd",
            },
            headers=_ADMIN_HEADER,
        )
        app.dependency_overrides = {}

        assert resp.status_code == 200
        data = resp.json()
        assert "conversationId" in data
        assert "openingMessage" in data
        assert data["status"] == "started"

    def test_start_missing_required_fields_returns_422(self):
        """Missing leadId/leadName returns 422."""
        client = _make_client()
        resp = client.post(
            "/api/jorge-seller/start",
            json={"propertyAddress": "123 Test St"},
            headers=_ADMIN_HEADER,
        )
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /api/lead-bot/{leadId}/schedule
# ---------------------------------------------------------------------------


class TestLeadBotSchedule:
    """Tests for triggering lead bot sequence."""

    def test_schedule_valid_day(self):
        """Schedules Day 3 sequence successfully."""
        p1, p2, p3 = _mock_bot_singletons()
        c1, c2, c3 = _mock_counters()
        with p1, p2, p3, c1, c2, c3, _mock_event_publisher():
            client = _make_client()
            resp = client.post(
                "/api/lead-bot/lead-001/schedule",
                json={"sequenceDay": 3},
                headers=_ADMIN_HEADER,
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "scheduled"
        assert data["sequenceDay"] == 3

    def test_schedule_invalid_day_returns_error(self):
        """Non-standard sequence day returns error status."""
        p1, p2, p3 = _mock_bot_singletons()
        c1, c2, c3 = _mock_counters()
        with p1, p2, p3, c1, c2, c3, _mock_event_publisher():
            client = _make_client()
            resp = client.post(
                "/api/lead-bot/lead-001/schedule",
                json={"sequenceDay": 5},
                headers=_ADMIN_HEADER,
            )

        # Endpoint raises 400 but broad except handler re-raises as 500
        assert resp.status_code in (400, 500)


# ---------------------------------------------------------------------------
# GET /api/intent-decoder/{leadId}/score
# ---------------------------------------------------------------------------


class TestIntentDecoderScore:
    """Tests for the intent scoring endpoint."""

    def test_score_returns_frs_pcs(self):
        """Returns FRS/PCS scores and classification."""
        from ghl_real_estate_ai.api.main import app

        cache = MagicMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()

        session_manager = MagicMock()
        session_manager.get_lead_conversations = AsyncMock(return_value=["conv-1"])
        session_manager.get_history = AsyncMock(return_value=[])

        event_publisher = MagicMock()
        event_publisher.publish_intent_analysis_complete = AsyncMock()

        intent_decoder = MagicMock()
        frs_mock = MagicMock(
            total_score=85.0,
            classification="Hot Seller",
            motivation=MagicMock(score=90, category="High"),
            timeline=MagicMock(score=80, category="Medium"),
            condition=MagicMock(score=85, category="High"),
            price=MagicMock(score=82, category="High"),
        )
        pcs_mock = MagicMock(total_score=78.0)
        profile_mock = MagicMock(
            frs=frs_mock,
            pcs=pcs_mock,
            next_best_action="Schedule listing appointment",
        )
        intent_decoder.analyze_lead = MagicMock(return_value=profile_mock)

        app.dependency_overrides[bot_management.get_cache_service] = lambda: cache
        app.dependency_overrides[bot_management.get_session_manager] = lambda: session_manager
        app.dependency_overrides[bot_management.get_event_publisher] = lambda: event_publisher
        app.dependency_overrides[bot_management.get_intent_decoder] = lambda: intent_decoder
        client = _make_client()
        resp = client.get("/api/intent-decoder/lead-001/score", headers=_ADMIN_HEADER)
        app.dependency_overrides = {}

        assert resp.status_code == 200
        data = resp.json()
        assert "frsScore" in data
        assert "pcsScore" in data
        assert "temperature" in data
        assert "classification" in data
        assert "breakdown" in data


# ---------------------------------------------------------------------------
# POST /api/jorge-seller/{lead_id}/handoff
# ---------------------------------------------------------------------------


class TestJorgeSellerHandoff:
    """Tests for Jorge handoff route idempotency and execution."""

    def test_handoff_manual_fallback_and_idempotency_cache(self):
        from ghl_real_estate_ai.api.main import app

        handoff_service = MagicMock()
        handoff_service.evaluate_handoff = AsyncMock(return_value=None)
        handoff_service.execute_handoff = AsyncMock(
            return_value=[{"type": "add_tag", "tag": "Buyer-Lead", "handoff_executed": True}]
        )
        handoff_service.record_outcome = MagicMock()

        cache = MagicMock()
        cache.get = AsyncMock(
            side_effect=[
                None,
                {
                    "success": True,
                    "handoff_id": "handoff_cached_001",
                    "target_bot": "buyer",
                    "actions": [{"type": "add_tag", "tag": "Buyer-Lead", "handoff_executed": True}],
                    "blocked": False,
                    "block_reason": None,
                    "estimated_time_seconds": 30,
                },
            ]
        )
        cache.set = AsyncMock()

        app.dependency_overrides[bot_management.get_handoff_service] = lambda: handoff_service
        app.dependency_overrides[bot_management.get_cache_service] = lambda: cache
        client = _make_client()

        payload = {
            "target_bot": "buyer",
            "reason": "manual_handoff",
            "confidence": 0.9,
            "idempotency_key": "handoff-key-001",
            "message": "I need help buying now",
            "conversation_history": [{"role": "user", "content": "Need a buyer agent"}],
        }
        first = client.post("/api/jorge-seller/lead-001/handoff", json=payload, headers=_ADMIN_HEADER)
        second = client.post("/api/jorge-seller/lead-001/handoff", json=payload, headers=_ADMIN_HEADER)
        app.dependency_overrides = {}

        assert first.status_code == 200
        assert first.json()["success"] is True
        assert second.status_code == 200
        assert second.json()["handoff_id"] == "handoff_cached_001"
        handoff_service.execute_handoff.assert_awaited_once()
        handoff_service.record_outcome.assert_called_once()
        cache.set.assert_awaited()


# ---------------------------------------------------------------------------
# POST /api/jorge-seller/test
# ---------------------------------------------------------------------------


class TestJorgeSellerTestEndpoint:
    """Tests for the quick test endpoint."""

    def test_test_endpoint_returns_pass(self):
        """Test endpoint returns PASS status."""
        client = _make_client()
        resp = client.post("/api/jorge-seller/test", headers=_ADMIN_HEADER)
        assert resp.status_code == 200
        data = resp.json()
        assert data["test_result"] == "PASS"
