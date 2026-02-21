"""
Integration tests for prediction API routes (ROADMAP-001 through ROADMAP-005).

Tests cover:
- ROADMAP-001: Interaction history from interaction_history table
- ROADMAP-002: Deal data from deals table
- ROADMAP-003: Target markets from user_settings (replaces hardcoded NYC/LA/Chicago)
- ROADMAP-004: Team data from user_settings (replaces hardcoded team_size=8)
- ROADMAP-005: Expansion plans from user_settings (replaces hardcoded territories)

Note: The prediction module has a heavy import chain with relative imports that
can break in isolation. These tests import the standalone helper functions and
utility by mocking the DB layer, verifying the SQL queries and fallback behavior.
"""

import asyncio
import importlib
import sys
from datetime import datetime, timedelta
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers: fake asyncpg rows and DB connection
# ---------------------------------------------------------------------------


class FakeRecord(dict):
    """Dict subclass that supports attribute-style access like asyncpg.Record."""

    pass


class FakeConnection:
    """Async context manager that mocks an asyncpg connection."""

    def __init__(self, fetchrow_result=None, fetch_result=None):
        self._fetchrow_result = fetchrow_result
        self._fetch_result = fetch_result or []
        self.call_log = []

    async def fetchrow(self, query, *args):
        self.call_log.append(("fetchrow", query, args))
        return self._fetchrow_result

    async def fetch(self, query, *args):
        self.call_log.append(("fetch", query, args))
        return self._fetch_result

    async def execute(self, query, *args):
        self.call_log.append(("execute", query, args))

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass


class FakeDatabase:
    def __init__(self, conn):
        self._conn = conn

    def get_connection(self):
        return self._conn


# ---------------------------------------------------------------------------
# Module-level helper — load prediction helpers without the heavy import chain
# We do this by pre-populating sys.modules with stubs for the heavy prediction
# engine dependencies, then importing the module.
# ---------------------------------------------------------------------------

_STUB_MODULES = [
    "ghl_real_estate_ai.prediction",
    "ghl_real_estate_ai.prediction.business_forecasting_engine",
    "ghl_real_estate_ai.prediction.client_behavior_analyzer",
    "ghl_real_estate_ai.prediction.deal_success_predictor",
    "ghl_real_estate_ai.prediction.jorge_prediction_engine",
    "ghl_real_estate_ai.prediction.market_intelligence_analyzer",
    "ghl_real_estate_ai.services.auth_service",
    "ghl_real_estate_ai.services.websocket_manager",
]


@pytest.fixture(autouse=True)
def _stub_heavy_deps():
    """Temporarily stub heavy prediction dependencies so the module can import."""
    originals = {}
    for mod_name in _STUB_MODULES:
        originals[mod_name] = sys.modules.get(mod_name)
        stub = ModuleType(mod_name)
        # Add minimal attributes the prediction module expects
        stub.ForecastTimeframe = MagicMock()
        stub.GrowthStrategy = MagicMock()
        stub.BusinessForecastingEngine = MagicMock()
        stub.ClientBehaviorAnalyzer = MagicMock()
        stub.DealStage = MagicMock()
        stub.DealSuccessPredictor = MagicMock()
        stub.JorgePredictionEngine = MagicMock()
        stub.PredictionContext = MagicMock()
        stub.TimeFrame = MagicMock()
        stub.MarketIntelligenceAnalyzer = MagicMock()
        stub.get_current_user = MagicMock()
        stub.WebSocketManager = MagicMock(return_value=MagicMock(get_connection_count=MagicMock(return_value=0)))
        sys.modules[mod_name] = stub

    yield

    # Restore original modules
    for mod_name, orig in originals.items():
        if orig is None:
            sys.modules.pop(mod_name, None)
        else:
            sys.modules[mod_name] = orig

    # Force reimport next time
    sys.modules.pop("ghl_real_estate_ai.api.routes.prediction", None)


def _import_prediction_helpers():
    """Import the prediction route module (with stubs in place)."""
    # Force reimport to pick up our stubs
    sys.modules.pop("ghl_real_estate_ai.api.routes.prediction", None)
    mod = importlib.import_module("ghl_real_estate_ai.api.routes.prediction")
    return mod


# ---------------------------------------------------------------------------
# ROADMAP-001: _fetch_client_interaction_history — DB wiring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_001_interaction_history_from_db():
    """ROADMAP-001: _fetch_client_interaction_history queries interaction_history table."""
    now = datetime.now()
    rows = [
        FakeRecord(
            {
                "interaction_type": "sms",
                "content": "Hello, interested in listing",
                "metadata": {"source": "ghl"},
                "created_at": now - timedelta(days=5),
            }
        ),
        FakeRecord(
            {
                "interaction_type": "email",
                "content": "Follow-up on CMA",
                "metadata": {"source": "manual"},
                "created_at": now - timedelta(days=2),
            }
        ),
    ]
    conn = FakeConnection(fetch_result=rows)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_client_interaction_history("client_001", limit=50)

    assert len(result) == 2
    assert result[0]["interaction_type"] == "sms"
    assert result[1]["interaction_type"] == "email"

    # Verify correct query was executed
    assert len(conn.call_log) == 1
    method, query, args = conn.call_log[0]
    assert method == "fetch"
    assert "interaction_history" in query
    assert args == ("client_001", 50)


@pytest.mark.asyncio
async def test_roadmap_001_interaction_history_db_error_returns_empty():
    """ROADMAP-001: Returns empty list on DB error (graceful degradation)."""
    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, side_effect=Exception("DB down")):
        result = await mod._fetch_client_interaction_history("client_001")

    assert result == []


# ---------------------------------------------------------------------------
# ROADMAP-002: _fetch_deal_data — DB wiring
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_002_deal_data_from_db():
    """ROADMAP-002: _fetch_deal_data queries deals table and returns real data."""
    deal_row = FakeRecord(
        {
            "deal_id": "deal_100",
            "property_value": 750000.0,
            "offer_amount": 725000.0,
            "commission_rate": 0.05,
            "current_stage": "negotiation",
        }
    )
    conn = FakeConnection(fetchrow_result=deal_row)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_deal_data("deal_100", "negotiation", None)

    assert result["deal_id"] == "deal_100"
    assert result["property_value"] == 750000.0
    assert result["offer_amount"] == 725000.0
    assert result["commission_rate"] == 0.05

    # Verify query hit the deals table
    method, query, _ = conn.call_log[0]
    assert method == "fetchrow"
    assert "deals" in query


@pytest.mark.asyncio
async def test_roadmap_002_deal_data_fallback_when_not_found():
    """ROADMAP-002: Falls back to context/defaults when deal not in DB."""
    conn = FakeConnection(fetchrow_result=None)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_deal_data("deal_missing", "listing", {"property_value": 600000})

    assert result["deal_id"] == "deal_missing"
    assert result["property_value"] == 600000.0
    assert result["current_stage"] == "listing"


@pytest.mark.asyncio
async def test_roadmap_002_deal_data_db_error_returns_fallback():
    """ROADMAP-002: Returns fallback on DB error (graceful degradation)."""
    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, side_effect=Exception("timeout")):
        result = await mod._fetch_deal_data("deal_err", "closing", None)

    assert result["deal_id"] == "deal_err"
    assert result["property_value"] == 500000.0  # default fallback


# ---------------------------------------------------------------------------
# ROADMAP-003/004/005: _fetch_business_profile — target markets, team, expansion
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_003_004_005_business_profile_from_db():
    """ROADMAP-003/004/005: Reads target_markets, team_size, expansion_territories from user_settings."""
    profile_row = FakeRecord(
        {
            "target_markets": ["Austin", "Denver", "Portland"],
            "team_size": 12,
            "expansion_territories": ["Tampa", "Charlotte"],
        }
    )
    conn = FakeConnection(fetchrow_result=profile_row)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_business_profile("user_001")

    assert result["target_markets"] == ["Austin", "Denver", "Portland"]
    assert result["team_size"] == 12
    assert result["expansion_territories"] == ["Tampa", "Charlotte"]

    # Verify query hit user_settings
    method, query, args = conn.call_log[0]
    assert "user_settings" in query
    assert args == ("user_001",)


@pytest.mark.asyncio
async def test_roadmap_003_target_markets_csv_string_parsed():
    """ROADMAP-003: CSV string target_markets is parsed into list."""
    profile_row = FakeRecord(
        {
            "target_markets": "Boston, Philadelphia, Baltimore",
            "team_size": 5,
            "expansion_territories": "Newark, Hartford",
        }
    )
    conn = FakeConnection(fetchrow_result=profile_row)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_business_profile("user_002")

    assert result["target_markets"] == ["Boston", "Philadelphia", "Baltimore"]
    assert result["team_size"] == 5
    assert result["expansion_territories"] == ["Newark", "Hartford"]


@pytest.mark.asyncio
async def test_roadmap_003_004_005_fallback_when_no_user_settings():
    """ROADMAP-003/004/005: Returns defaults when user_settings row is missing."""
    conn = FakeConnection(fetchrow_result=None)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_business_profile("user_missing")

    assert result["target_markets"] == ["NYC", "LA", "Chicago"]
    assert result["team_size"] == 8
    assert result["expansion_territories"] == ["Miami", "Rancho Cucamonga", "Seattle"]


@pytest.mark.asyncio
async def test_roadmap_003_004_005_db_error_returns_defaults():
    """ROADMAP-003/004/005: Returns defaults on DB error (graceful degradation)."""
    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, side_effect=Exception("refused")):
        result = await mod._fetch_business_profile("user_err")

    assert result["target_markets"] == ["NYC", "LA", "Chicago"]
    assert result["team_size"] == 8


# ---------------------------------------------------------------------------
# Utility: _normalize_string_list
# ---------------------------------------------------------------------------


def test_normalize_string_list_with_list():
    """_normalize_string_list passes through list values."""
    mod = _import_prediction_helpers()
    assert mod._normalize_string_list(["a", "b"], ["fallback"]) == ["a", "b"]


def test_normalize_string_list_with_csv():
    """_normalize_string_list parses comma-separated strings."""
    mod = _import_prediction_helpers()
    assert mod._normalize_string_list("x, y, z", ["fallback"]) == ["x", "y", "z"]


def test_normalize_string_list_empty_falls_back():
    """_normalize_string_list returns fallback for empty input."""
    mod = _import_prediction_helpers()
    assert mod._normalize_string_list([], ["default"]) == ["default"]
    assert mod._normalize_string_list("", ["default"]) == ["default"]
    assert mod._normalize_string_list(None, ["default"]) == ["default"]


# ---------------------------------------------------------------------------
# ROADMAP-006: _fetch_market_snapshot + _detect_market_changes
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_006_fetch_market_snapshot_from_db():
    """ROADMAP-006: _fetch_market_snapshot queries deals table."""
    snapshot_row = FakeRecord(
        {
            "active_deals": 15,
            "avg_property_value": 650000.0,
            "avg_commission_rate": 0.05,
            "closing_deals": 3,
            "new_deals_24h": 5,
        }
    )
    conn = FakeConnection(fetchrow_result=snapshot_row)
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._fetch_market_snapshot()

    assert result["active_deals"] == 15
    assert result["avg_property_value"] == 650000.0
    assert result["closing_deals"] == 3
    assert result["new_deals_24h"] == 5

    # Verify query hit deals table
    method, query, _ = conn.call_log[0]
    assert method == "fetchrow"
    assert "deals" in query


@pytest.mark.asyncio
async def test_roadmap_006_fetch_market_snapshot_db_error_returns_defaults():
    """ROADMAP-006: Returns defaults on DB error (graceful degradation)."""
    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, side_effect=Exception("DB down")):
        result = await mod._fetch_market_snapshot()

    assert result["active_deals"] == 0
    assert result["avg_property_value"] == 0


def test_roadmap_006_detect_market_changes_no_previous():
    """ROADMAP-006: No changes when previous snapshot is None."""
    mod = _import_prediction_helpers()
    current = {"avg_property_value": 500000, "new_deals_24h": 2, "closing_deals": 1}
    assert mod._detect_market_changes(None, current) == []


def test_roadmap_006_detect_property_value_shift():
    """ROADMAP-006: Detects >5% property value shift."""
    mod = _import_prediction_helpers()
    previous = {"avg_property_value": 500000, "new_deals_24h": 2, "closing_deals": 3}
    current = {"avg_property_value": 540000, "new_deals_24h": 2, "closing_deals": 3}

    changes = mod._detect_market_changes(previous, current)
    assert len(changes) == 1
    assert changes[0]["metric"] == "avg_property_value"
    assert "increased" in changes[0]["description"]


def test_roadmap_006_detect_closing_pipeline_change():
    """ROADMAP-006: Detects closing pipeline changes."""
    mod = _import_prediction_helpers()
    previous = {"avg_property_value": 500000, "new_deals_24h": 2, "closing_deals": 3}
    current = {"avg_property_value": 500000, "new_deals_24h": 2, "closing_deals": 5}

    changes = mod._detect_market_changes(previous, current)
    assert any(c["metric"] == "closing_deals" for c in changes)


# ---------------------------------------------------------------------------
# ROADMAP-007: _gather_monitoring_data
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_roadmap_007_gather_monitoring_data_from_db():
    """ROADMAP-007: _gather_monitoring_data queries interaction_history + deals."""
    call_count = 0

    async def _mock_fetchrow(query, *args):
        nonlocal call_count
        call_count += 1
        if "interaction_history" in query:
            return FakeRecord({"recent_interactions": 12})
        if "deals" in query and "listing" in query:
            return FakeRecord({"total_active": 20, "listing": 8, "negotiation": 7, "closing": 5})
        # _fetch_market_snapshot inner query
        if "deals" in query and "avg_property_value" in query:
            return FakeRecord(
                {
                    "active_deals": 20,
                    "avg_property_value": 600000,
                    "avg_commission_rate": 0.05,
                    "closing_deals": 5,
                    "new_deals_24h": 3,
                }
            )
        return None

    conn = FakeConnection()
    conn.fetchrow = _mock_fetchrow
    db = FakeDatabase(conn)

    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, return_value=db):
        result = await mod._gather_monitoring_data()

    assert result["recent_interactions"] == 12
    assert result["deal_pipeline"]["total_active"] == 20
    assert result["deal_pipeline"]["closing"] == 5
    assert "market_snapshot" in result


@pytest.mark.asyncio
async def test_roadmap_007_gather_monitoring_data_db_error_returns_defaults():
    """ROADMAP-007: Returns defaults on DB error."""
    mod = _import_prediction_helpers()

    with patch.object(mod, "get_database", new_callable=AsyncMock, side_effect=Exception("timeout")):
        result = await mod._gather_monitoring_data()

    assert result["recent_interactions"] == 0
    assert result["deal_pipeline"] == {}
