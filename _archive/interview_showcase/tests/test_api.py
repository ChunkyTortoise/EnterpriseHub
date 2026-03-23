from __future__ import annotations

import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

API_DIR = Path(__file__).resolve().parents[1] / "api"
sys.path.insert(0, str(API_DIR))

from main import app, state  # noqa: E402


@pytest.fixture(autouse=True)
def reset_state() -> None:
    state.events.clear()
    state.user_current_bot.clear()
    state.user_handoffs.clear()
    state.approvals.clear()
    state.mem_cache.clear()
    state.latencies_ms.clear()
    state.metrics.update(
        {
            "total_requests": 0,
            "cache_hits": 0,
            "cache_misses": 0,
            "blocked_cross_tenant": 0,
            "handoffs_executed": 0,
            "prevented_loops": 0,
            "approvals_created": 0,
            "approvals_approved": 0,
            "approvals_rejected": 0,
            "cost_without_cache": 0.0,
            "actual_cost": 0.0,
        }
    )


client = TestClient(app)


def test_health() -> None:
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"


def test_multilingual_detection_spanish() -> None:
    res = client.post(
        "/v1/demo/message",
        json={"tenant_id": "tenant-a", "user_id": "u1", "message": "Hola, gracias por tu ayuda", "channel": "web"},
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["language"] == "es"


def test_deterministic_task_router_calendar() -> None:
    res = client.post(
        "/v1/demo/message",
        json={
            "tenant_id": "tenant-a",
            "user_id": "u1",
            "message": "Please schedule a meeting Thursday afternoon",
            "channel": "web",
        },
    )
    assert res.status_code == 200
    assert res.json()["task_type"] == "calendar"


def test_cross_tenant_access_blocked() -> None:
    res = client.post(
        "/v1/demo/message",
        json={
            "tenant_id": "tenant-a",
            "requested_tenant_id": "tenant-b",
            "user_id": "u1",
            "message": "Get profile",
            "channel": "web",
        },
    )
    assert res.status_code == 403


def test_handoff_loop_prevention() -> None:
    # lead -> buyer
    first = client.post(
        "/v1/demo/message",
        json={"tenant_id": "tenant-a", "user_id": "u1", "message": "I want to buy a home", "channel": "web"},
    )
    assert first.status_code == 200
    assert first.json()["handoff"]["executed"] is True
    assert first.json()["handoff"]["target_bot"] == "buyer"

    # buyer -> lead should be blocked as immediate reverse route
    second = client.post(
        "/v1/demo/message",
        json={"tenant_id": "tenant-a", "user_id": "u1", "message": "I am not ready, just browsing", "channel": "web"},
    )
    assert second.status_code == 200
    assert second.json()["handoff"]["executed"] is False
    assert second.json()["handoff"]["prevented_loop"] is True


def test_cache_hit_on_repeat_request() -> None:
    payload = {"tenant_id": "tenant-a", "user_id": "u1", "message": "Draft an email reply", "channel": "web"}
    first = client.post("/v1/demo/message", json=payload)
    second = client.post("/v1/demo/message", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["from_cache"] is False
    assert second.json()["from_cache"] is True

    metrics = client.get("/v1/metrics").json()
    assert metrics["cache_hits"] >= 1


def test_schedule_request_requires_approval() -> None:
    res = client.post(
        "/v1/demo/message",
        json={
            "tenant_id": "tenant-a",
            "user_id": "u1",
            "message": "Schedule a meeting with Alex tomorrow at 3pm",
            "channel": "web",
        },
    )
    assert res.status_code == 200
    payload = res.json()
    assert payload["approval_required"] is True
    assert payload["action_executed"] is False
    assert payload["approval_id"] is not None


def test_approval_decision_flow() -> None:
    res = client.post(
        "/v1/demo/message",
        json={
            "tenant_id": "tenant-a",
            "user_id": "u1",
            "message": "Send this email to Alex with the schedule details",
            "channel": "web",
        },
    )
    approval_id = res.json()["approval_id"]
    assert approval_id

    pending = client.get("/v1/approvals", params={"tenant_id": "tenant-a", "status": "pending"})
    assert pending.status_code == 200
    assert any(item["approval_id"] == approval_id for item in pending.json())

    decision = client.post(
        f"/v1/approvals/{approval_id}/decision",
        json={"decision": "approve", "reason": "looks good"},
    )
    assert decision.status_code == 200
    assert decision.json()["status"] == "approved"

    metrics = client.get("/v1/metrics").json()
    assert metrics["approvals_created"] >= 1
    assert metrics["approvals_approved"] >= 1
