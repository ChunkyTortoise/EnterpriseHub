"""
Tests for /admin/settings bot tone editing endpoints.

Endpoints tested:
    GET    /admin/settings              - fetch all bot settings
    PUT    /admin/settings/{bot}        - partial update
    DELETE /api/jorge-{bot}/{id}/state  - reset conversation state
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes.admin_settings import router
from ghl_real_estate_ai.services.jorge import bot_settings_store

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def reset_store():
    """Reset the settings store to defaults before each test."""
    bot_settings_store.reset_to_defaults()
    yield
    bot_settings_store.reset_to_defaults()


@pytest.fixture()
def client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /admin/settings
# ---------------------------------------------------------------------------


def test_get_settings_returns_both_bots(client):
    resp = client.get("/admin/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "seller" in data
    assert "buyer" in data


def test_get_settings_seller_has_required_keys(client):
    resp = client.get("/admin/settings")
    seller = resp.json()["seller"]
    assert "system_prompt" in seller
    assert "jorge_phrases" in seller
    assert "questions" in seller
    assert isinstance(seller["jorge_phrases"], list)
    assert len(seller["jorge_phrases"]) > 0


def test_get_settings_buyer_has_required_keys(client):
    resp = client.get("/admin/settings")
    buyer = resp.json()["buyer"]
    assert "system_prompt" in buyer
    assert "jorge_phrases" in buyer
    assert "questions" in buyer


def test_get_settings_seller_has_four_questions(client):
    resp = client.get("/admin/settings")
    questions = resp.json()["seller"]["questions"]
    assert set(questions.keys()) == {"1", "2", "3", "4"}


def test_get_settings_buyer_has_four_questions(client):
    resp = client.get("/admin/settings")
    questions = resp.json()["buyer"]["questions"]
    assert set(questions.keys()) == {"1", "2", "3", "4"}


# ---------------------------------------------------------------------------
# PUT /admin/settings/{bot}
# ---------------------------------------------------------------------------


def test_put_seller_system_prompt(client):
    resp = client.put("/admin/settings/seller", json={"system_prompt": "Be very direct and use bullet points."})
    assert resp.status_code == 200
    assert resp.json()["system_prompt"] == "Be very direct and use bullet points."


def test_put_seller_questions(client):
    new_qs = {"1": "Why are you selling?", "2": "Timeline?", "3": "Condition?", "4": "Price?"}
    resp = client.put("/admin/settings/seller", json={"questions": new_qs})
    assert resp.status_code == 200
    assert resp.json()["questions"]["1"] == "Why are you selling?"


def test_put_seller_phrases(client):
    resp = client.put("/admin/settings/seller", json={"jorge_phrases": ["Hey", "Hi there", "Quick question"]})
    assert resp.status_code == 200
    assert resp.json()["jorge_phrases"] == ["Hey", "Hi there", "Quick question"]


def test_put_buyer_settings(client):
    resp = client.put("/admin/settings/buyer", json={"system_prompt": "Be concise."})
    assert resp.status_code == 200
    assert resp.json()["system_prompt"] == "Be concise."


def test_put_persists_to_store(client):
    client.put("/admin/settings/seller", json={"system_prompt": "Custom persona."})
    # Verify via GET
    get_resp = client.get("/admin/settings")
    assert get_resp.json()["seller"]["system_prompt"] == "Custom persona."


def test_put_invalid_bot_returns_400(client):
    resp = client.put("/admin/settings/lead", json={"system_prompt": "test"})
    assert resp.status_code == 400


def test_put_empty_body_returns_400(client):
    resp = client.put("/admin/settings/seller", json={})
    assert resp.status_code == 400


def test_put_partial_update_preserves_other_keys(client):
    # Set all fields first
    client.put("/admin/settings/seller", json={"jorge_phrases": ["Hello"]})
    # Update only questions
    client.put("/admin/settings/seller", json={"questions": {"1": "New Q1", "2": "Q2", "3": "Q3", "4": "Q4"}})
    # Phrases should still be there
    resp = client.get("/admin/settings")
    assert resp.json()["seller"]["jorge_phrases"] == ["Hello"]
    assert resp.json()["seller"]["questions"]["1"] == "New Q1"


# ---------------------------------------------------------------------------
# DELETE /api/jorge-{bot}/{contact_id}/state
# ---------------------------------------------------------------------------


def test_delete_state_unknown_bot_returns_400(client):
    resp = client.delete("/api/jorge-lead/contact123/state")
    assert resp.status_code == 400


def test_delete_state_clears_test_session(client):
    from ghl_real_estate_ai.api.routes.test_bots import _sessions

    _sessions["contact-abc"] = {"contact_id": "contact-abc", "history": [], "turn": 0}
    assert "contact-abc" in _sessions

    # Mock session manager to avoid Redis dependency
    mock_manager = AsyncMock()
    mock_manager.get_lead_conversations = AsyncMock(return_value=[])
    with patch(
        "ghl_real_estate_ai.services.conversation_session_manager.get_session_manager",
        return_value=mock_manager,
    ):
        resp = client.delete("/api/jorge-seller/contact-abc/state")

    assert resp.status_code == 200
    assert "contact-abc" not in _sessions
    assert resp.json()["status"] == "cleared"


def test_delete_state_clears_redis_sessions(client):
    mock_manager = AsyncMock()
    mock_manager.get_lead_conversations = AsyncMock(return_value=["sess-1", "sess-2"])
    mock_manager.delete_session = AsyncMock(return_value=True)

    with patch(
        "ghl_real_estate_ai.services.conversation_session_manager.get_session_manager",
        return_value=mock_manager,
    ):
        resp = client.delete("/api/jorge-buyer/contact-xyz/state")

    assert resp.status_code == 200
    data = resp.json()
    assert data["contact_id"] == "contact-xyz"
    assert data["bot"] == "buyer"
    assert "session:sess-1" in data["cleared"]
    assert "session:sess-2" in data["cleared"]
    assert mock_manager.delete_session.call_count == 2


def test_delete_state_succeeds_when_redis_unavailable(client):
    """Endpoint should still return 200 if Redis throws (graceful degradation)."""
    mock_manager = AsyncMock()
    mock_manager.get_lead_conversations = AsyncMock(side_effect=Exception("Redis down"))

    with patch(
        "ghl_real_estate_ai.services.conversation_session_manager.get_session_manager",
        return_value=mock_manager,
    ):
        resp = client.delete("/api/jorge-seller/contact-fail/state")

    assert resp.status_code == 200
    assert resp.json()["status"] == "cleared"


# ---------------------------------------------------------------------------
# Integration: store → settings-store accessors
# ---------------------------------------------------------------------------


def test_store_get_questions_returns_defaults():
    qs = bot_settings_store.get_questions("seller")
    assert "1" in qs
    assert "2" in qs
    assert "3" in qs
    assert "4" in qs


def test_store_update_and_read_back():
    bot_settings_store.update_bot_settings("seller", {"system_prompt": "Direct style."})
    assert bot_settings_store.get_system_prompt_override("seller") == "Direct style."


def test_store_phrases_returns_list():
    phrases = bot_settings_store.get_phrases("buyer")
    assert isinstance(phrases, list)
    assert len(phrases) > 0


def test_store_invalid_keys_ignored():
    bot_settings_store.update_bot_settings("seller", {"invalid_key": "value", "system_prompt": "OK"})
    settings = bot_settings_store.get_bot_settings("seller")
    assert "invalid_key" not in settings
    assert settings["system_prompt"] == "OK"
