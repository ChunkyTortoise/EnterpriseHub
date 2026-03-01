from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes import revenue_v2


class FakeConn:
    def __init__(self, *, fetchrow_map: dict[str, Any] | None = None, fetch_map: dict[str, Any] | None = None):
        self.fetchrow_map = fetchrow_map or {}
        self.fetch_map = fetch_map or {}

    async def fetchrow(self, query: str, *args):
        for key, value in self.fetchrow_map.items():
            if key in query:
                return value
        return None

    async def fetch(self, query: str, *args):
        for key, value in self.fetch_map.items():
            if key in query:
                return value
        return []


class FakeDB:
    def __init__(self, conn: FakeConn):
        self.conn = conn

    @asynccontextmanager
    async def get_connection(self):
        yield self.conn


def _build_client(fake_db: FakeDB) -> TestClient:
    async def _fake_get_database():
        return fake_db

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    return TestClient(app)


def test_billing_v2_success_contract_and_headers():
    row = {
        "id": 11,
        "location_id": "loc_1",
        "tier": "professional",
        "status": "active",
        "current_period_end": "2026-03-01T00:00:00Z",
        "updated_at": None,
    }
    client = _build_client(FakeDB(FakeConn(fetchrow_map={"FROM subscriptions": row})))

    response = client.get("/api/v2/billing/subscriptions/loc_1")
    payload = response.json()

    assert response.status_code == 200
    assert response.headers["X-Response-Source"] == "database"
    assert "X-Data-Freshness" in response.headers
    assert payload["source"] == "database"
    assert payload["error"] is None
    assert payload["data"]["location_id"] == "loc_1"


def test_billing_v2_not_found_returns_standard_error_contract():
    client = _build_client(FakeDB(FakeConn()))

    response = client.get("/api/v2/billing/subscriptions/missing")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["error_code"] == "subscription_not_found"
    assert payload["error"]["recoverable"] is True
    assert payload["error"]["correlation_id"] == payload["correlation_id"]


def test_prediction_v2_contract():
    row = {
        "deal_id": "deal_1",
        "current_stage": "negotiation",
        "offer_amount": 450000,
        "property_value": 500000,
        "commission_rate": 0.06,
        "updated_at": None,
    }
    client = _build_client(FakeDB(FakeConn(fetchrow_map={"FROM deals": row})))

    response = client.get("/api/v2/prediction/deal-outcome/deal_1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["source"] == "database"
    assert payload["data"]["deal_id"] == "deal_1"
    assert 5.0 <= payload["data"]["closing_probability"] <= 95.0


def test_market_stream_v2_emits_sse_events():
    rows = [
        {"property_id": "p1", "market_score": 78.5, "roi_projection": 0.12},
        {"property_id": "p2", "market_score": 83.1, "roi_projection": 0.15},
    ]
    client = _build_client(FakeDB(FakeConn(fetch_map={"FROM property_analyses": rows})))

    with client.stream("GET", "/api/v2/market-intelligence/recommendations/stream?market_id=m1&lead_id=l1") as response:
        body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "event: start" in body
    assert "event: token" in body
    assert "event: complete" in body
