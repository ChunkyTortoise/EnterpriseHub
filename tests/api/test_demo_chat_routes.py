"""Tests for the public demo chat stream endpoints.

Endpoints tested:
    GET  /demo/warm         - cold-start wake ping (no DB touch)
    POST /demo/chat/stream  - SSE replay stream (Mode A)
    GET  /demo/mesh/status  - seeded mesh snapshot
"""

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes import demo_chat

pytestmark = pytest.mark.unit


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(demo_chat.router)
    return TestClient(app, raise_server_exceptions=False)


def _parse_sse_events(body: str) -> list[dict]:
    events = []
    for frame in body.split("\n\n"):
        for line in frame.split("\n"):
            if line.startswith("data: "):
                events.append(json.loads(line[6:]))
    return events


class TestWarm:
    def test_warm_returns_ok_without_db(self):
        response = _make_client().get("/demo/warm")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["uptime_s"] >= 0
        assert payload["live_ai"] is False


class TestChatStream:
    def test_stream_is_sse_and_terminates_with_done(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "Qualify new seller lead"})
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/event-stream")
        events = _parse_sse_events(response.text)
        assert events[-1]["type"] == "done"

    def test_seller_keywords_replay_handoff_trace(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "qualify this seller"})
        events = _parse_sse_events(response.text)
        handoffs = [e for e in events if e["type"] == "handoff"]
        assert len(handoffs) == 1
        assert handoffs[0]["data"]["from"] == "lead"
        assert handoffs[0]["data"]["to"] == "seller"
        assert handoffs[0]["data"]["confidence"] >= handoffs[0]["data"]["threshold"]

    def test_buyer_keywords_select_buyer_trace(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "match David to listings"})
        events = _parse_sse_events(response.text)
        starts = [e for e in events if e["type"] == "message_start"]
        assert any(e.get("bot") == "buyer" for e in starts)

    def test_unmatched_input_falls_back_to_default_trace(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "xyzzy"})
        events = _parse_sse_events(response.text)
        assert events[-1]["type"] == "done"
        assert any(e["type"] == "telemetry" for e in events)

    def test_bot_messages_stream_as_multiple_token_chunks(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "seller"})
        events = _parse_sse_events(response.text)
        bot_start = next(e for e in events if e["type"] == "message_start" and e["role"] == "bot")
        bot_tokens = [e for e in events if e["type"] == "token" and e["messageId"] == bot_start["messageId"]]
        assert len(bot_tokens) > 3

    def test_oversize_input_rejected(self):
        response = _make_client().post("/demo/chat/stream", json={"message": "x" * 301})
        assert response.status_code == 422

    def test_empty_input_rejected(self):
        response = _make_client().post("/demo/chat/stream", json={"message": ""})
        assert response.status_code == 422


class TestLiveAiRateLimit:
    def test_per_ip_window_denies_after_limit(self):
        demo_chat._ip_windows.clear()
        demo_chat._global_window.clear()
        for _ in range(demo_chat._PER_IP_LIMIT):
            assert demo_chat._live_ai_allowed("1.2.3.4") is True
        assert demo_chat._live_ai_allowed("1.2.3.4") is False
        # A different IP still passes until the global cap.
        assert demo_chat._live_ai_allowed("5.6.7.8") is True
        demo_chat._ip_windows.clear()
        demo_chat._global_window.clear()

    def test_global_daily_cap_denies_all_ips(self):
        demo_chat._ip_windows.clear()
        demo_chat._global_window.clear()
        import time

        now = time.time()
        demo_chat._global_window.extend([now] * demo_chat._GLOBAL_DAILY_LIMIT)
        assert demo_chat._live_ai_allowed("9.9.9.9") is False
        demo_chat._ip_windows.clear()
        demo_chat._global_window.clear()


class TestMeshStatus:
    def test_snapshot_shape_and_honest_labeling(self):
        response = _make_client().get("/demo/mesh/status")
        assert response.status_code == 200
        payload = response.json()
        assert payload["snapshot"] is True
        assert len(payload["agents"]) == 7
        assert payload["budget"]["hourly_gate_usd"] == 50
