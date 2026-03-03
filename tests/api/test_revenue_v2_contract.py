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
        if "information_schema.columns" in query:
            # Default to tenant-enforceable schema unless a test overrides this.
            return [{"column_name": "tenant_id"}]
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
    assert "X-Correlation-Id" in response.headers

    assert payload["meta"]["source"] == "database"
    assert payload["error"] is None
    assert payload["data"]["location_id"] == "loc_1"


def test_billing_v2_not_found_returns_standard_error_contract():
    client = _build_client(FakeDB(FakeConn()))

    response = client.get("/api/v2/billing/subscriptions/missing")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["code"] == "subscription_not_found"
    assert payload["error"]["retryable"] is False
    assert payload["error"]["correlation_id"] == payload["meta"]["correlation_id"]


def test_prediction_v2_requires_tenant_scope():
    client = _build_client(FakeDB(FakeConn()))

    response = client.get("/api/v2/prediction/deal-outcome/deal_1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["code"] == "tenant_scope_required"


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

    response = client.get("/api/v2/prediction/deal-outcome/deal_1?tenant_id=t_1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["meta"]["source"] == "database"
    assert payload["data"]["deal_id"] == "deal_1"
    assert payload["data"]["tenant_id"] == "t_1"
    assert 5.0 <= payload["data"]["closing_probability"] <= 95.0


def test_prediction_v2_tenant_scope_violation_is_blocked():
    row = {
        "deal_id": "deal_1",
        "tenant_id": "t_other",
        "current_stage": "negotiation",
        "offer_amount": 450000,
        "property_value": 500000,
        "commission_rate": 0.06,
        "updated_at": None,
    }
    client = _build_client(FakeDB(FakeConn(fetchrow_map={"FROM deals": row})))

    response = client.get("/api/v2/prediction/deal-outcome/deal_1?tenant_id=t_1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["code"] == "tenant_scope_violation"
    assert payload["error"]["retryable"] is False


def test_prediction_v2_provider_timeout_returns_standard_retryable_error():
    class TimeoutConn:
        async def fetchrow(self, query: str, *args):
            raise TimeoutError("provider timeout")

    class TimeoutDB:
        @asynccontextmanager
        async def get_connection(self):
            yield TimeoutConn()

    async def _fake_get_database():
        return TimeoutDB()

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    client = TestClient(app)

    response = client.get("/api/v2/prediction/deal-outcome/deal_1?tenant_id=t_1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["code"] == "prediction_query_failed"
    assert payload["error"]["retryable"] is True
    assert payload["error"]["correlation_id"] == payload["meta"]["correlation_id"]


def test_market_stream_v2_emits_sse_events():
    rows = [
        {"property_id": "p1", "market_score": 78.5, "roi_projection": 0.12},
        {"property_id": "p2", "market_score": 83.1, "roi_projection": 0.15},
    ]
    client = _build_client(FakeDB(FakeConn(fetch_map={"FROM property_analyses": rows})))

    with client.stream(
        "GET",
        "/api/v2/market-intelligence/recommendations/stream?market_id=m1&lead_id=l1&tenant_id=t_1",
    ) as response:
        body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "event: start" in body
    assert "event: token" in body
    assert "event: complete" in body


def test_market_stream_v2_missing_tenant_yields_error_event():
    client = _build_client(FakeDB(FakeConn()))

    with client.stream("GET", "/api/v2/market-intelligence/recommendations/stream?market_id=m1&lead_id=l1") as response:
        body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "event: start" in body
    assert "event: error" in body
    assert "tenant_scope_required" in body


def test_market_stream_v2_provider_timeout_yields_error_event():
    class TimeoutConn:
        async def fetch(self, query: str, *args):
            raise TimeoutError("provider timeout")

    class TimeoutDB:
        @asynccontextmanager
        async def get_connection(self):
            yield TimeoutConn()

    async def _fake_get_database():
        return TimeoutDB()

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    client = TestClient(app)

    with client.stream(
        "GET",
        "/api/v2/market-intelligence/recommendations/stream?market_id=m1&lead_id=l1&tenant_id=t_1",
    ) as response:
        body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "event: error" in body
    assert "market_stream_failed" in body


def test_prediction_v2_returns_scope_unenforceable_when_tenant_column_missing():
    row = {
        "deal_id": "deal_1",
        "current_stage": "negotiation",
        "offer_amount": 450000,
        "property_value": 500000,
        "commission_rate": 0.06,
        "updated_at": None,
    }
    client = _build_client(
        FakeDB(
            FakeConn(
                fetch_map={"information_schema.columns": []},
                fetchrow_map={"FROM deals": row},
            )
        )
    )

    response = client.get("/api/v2/prediction/deal-outcome/deal_1?tenant_id=t_1")
    payload = response.json()
    assert response.status_code == 200
    assert payload["error"]["code"] == "tenant_scope_unenforceable"


def test_market_stream_scope_unenforceable_when_tenant_column_missing():
    client = _build_client(FakeDB(FakeConn(fetch_map={"information_schema.columns": []})))

    with client.stream(
        "GET",
        "/api/v2/market-intelligence/recommendations/stream?market_id=m1&lead_id=l1&tenant_id=t_1",
    ) as response:
        body = "".join(chunk.decode() if isinstance(chunk, bytes) else chunk for chunk in response.iter_raw())

    assert response.status_code == 200
    assert "event: error" in body
    assert "tenant_scope_unenforceable" in body


def test_weekly_proof_pack_requires_tenant_scope():
    client = _build_client(FakeDB(FakeConn()))

    response = client.get("/api/v2/reports/weekly-proof-pack")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"]["code"] == "tenant_scope_required"


def test_weekly_proof_pack_returns_kpi_and_markdown():
    row = {
        "tenant_id": "tenant_demo",
        "week_start": "2026-03-03",
        "leads_received": 12,
        "qualified_leads": 7,
        "response_sla_pct": 91.2,
        "appointments_booked": 3,
        "cost_per_qualified_lead": 19.5,
        "updated_at": None,
    }
    client = _build_client(FakeDB(FakeConn(fetchrow_map={"FROM pilot_kpi_records": row})))

    response = client.get("/api/v2/reports/weekly-proof-pack?tenant_id=tenant_demo")
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"]["source"] == "database"
    assert payload["data"]["tenant_id"] == "tenant_demo"
    assert "kpi" in payload["data"]
    assert "proof_pack_markdown" in payload["data"]


def test_weekly_proof_pack_requested_week_missing_returns_non_retryable():
    class EmptyConn:
        async def fetchrow(self, query: str, *args):
            if "FROM pilot_kpi_records" in query:
                return None
            return None

        async def fetch(self, query: str, *args):
            if "information_schema.columns" in query:
                return [{"column_name": "tenant_id"}]
            return []

    class EmptyDB:
        @asynccontextmanager
        async def get_connection(self):
            yield EmptyConn()

    async def _fake_get_database():
        return EmptyDB()

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    client = TestClient(app)

    response = client.get("/api/v2/reports/weekly-proof-pack?tenant_id=tenant_demo&week_start=2026-03-03")
    payload = response.json()
    assert response.status_code == 200
    assert payload["error"]["code"] == "weekly_proof_pack_unavailable"
    assert payload["error"]["retryable"] is False


def test_weekly_proof_pack_db_unavailable_uses_file_fallback():
    class ErrorConn:
        async def fetchrow(self, query: str, *args):
            raise RuntimeError("db unavailable")

        async def fetch(self, query: str, *args):
            return []

    class ErrorDB:
        @asynccontextmanager
        async def get_connection(self):
            yield ErrorConn()

    async def _fake_get_database():
        return ErrorDB()

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    client = TestClient(app)

    response = client.get("/api/v2/reports/weekly-proof-pack?tenant_id=tenant_demo")
    payload = response.json()
    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"]["source"] == "live_provider"


def test_weekly_proof_pack_allow_latest_fallback_returns_latest_week():
    class FallbackConn:
        async def fetchrow(self, query: str, *args):
            if "week_start = $2::date" in query:
                return None
            if "ORDER BY week_start DESC" in query:
                return {
                    "tenant_id": "tenant_demo",
                    "week_start": "2026-03-10",
                    "leads_received": 20,
                    "qualified_leads": 11,
                    "response_sla_pct": 93.0,
                    "appointments_booked": 4,
                    "cost_per_qualified_lead": 17.0,
                    "updated_at": None,
                }
            return None

        async def fetch(self, query: str, *args):
            return []

    class FallbackDB:
        @asynccontextmanager
        async def get_connection(self):
            yield FallbackConn()

    async def _fake_get_database():
        return FallbackDB()

    app = FastAPI()
    app.include_router(revenue_v2.router)
    revenue_v2.get_database = _fake_get_database
    client = TestClient(app)

    response = client.get(
        "/api/v2/reports/weekly-proof-pack?tenant_id=tenant_demo&week_start=2026-03-03&allow_latest_fallback=true"
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["error"] is None
    assert payload["meta"]["source"] == "database"
    assert str(payload["data"]["week_start"]) == "2026-03-10"
