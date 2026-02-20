from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes.market_intelligence_v2 import router


def _make_client():
    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def test_sentiment_radar_success():
    client = _make_client()

    registry = MagicMock()
    registry.get_market_config.return_value = SimpleNamespace(market_name="Rancho Cucamonga")

    signal = MagicMock()
    signal.to_dict.return_value = {"signal_type": "inventory", "impact_score": 0.8}
    profile = SimpleNamespace(
        location="Rancho Cucamonga",
        overall_sentiment=0.71,
        trend_direction="improving",
        velocity=0.34,
        seller_motivation_index=0.63,
        optimal_outreach_window="next_14_days",
        confidence_score=0.86,
        key_signals=[signal],
        last_updated=datetime.now(),
    )
    radar = MagicMock()
    radar.analyze_market_sentiment = AsyncMock(return_value=profile)

    with (
        patch("ghl_real_estate_ai.api.routes.market_intelligence_v2.get_market_registry", return_value=registry),
        patch("ghl_real_estate_ai.api.routes.market_intelligence_v2.get_market_sentiment_radar", AsyncMock(return_value=radar)),
    ):
        resp = client.get("/api/v2/market-intelligence/markets/rancho_cucamonga/sentiment/radar?timeframe_days=21")

    assert resp.status_code == 200
    body = resp.json()
    assert body["market_id"] == "rancho_cucamonga"
    assert body["timeframe_days"] == 21
    assert body["overall_sentiment"] == 0.71
    assert len(body["key_signals"]) == 1


def test_sentiment_alerts_success():
    client = _make_client()

    registry = MagicMock()
    registry.get_market_config.return_value = SimpleNamespace(market_name="Rancho Cucamonga")

    alert = SimpleNamespace(
        alert_id="alert-1",
        priority=SimpleNamespace(value="high"),
        location="Rancho Cucamonga",
        trigger_type=SimpleNamespace(value="seller_motivation_spike"),
        message="Seller motivation rising rapidly",
        recommended_action="Launch outreach sprint",
        target_audience="motivated_sellers",
        timing_window="48h",
        expected_lead_quality="high",
        generated_at=datetime.now(),
    )
    radar = MagicMock()
    radar.generate_sentiment_alerts = AsyncMock(return_value=[alert])

    with (
        patch("ghl_real_estate_ai.api.routes.market_intelligence_v2.get_market_registry", return_value=registry),
        patch("ghl_real_estate_ai.api.routes.market_intelligence_v2.get_market_sentiment_radar", AsyncMock(return_value=radar)),
    ):
        resp = client.get("/api/v2/market-intelligence/markets/rancho_cucamonga/sentiment/alerts")

    assert resp.status_code == 200
    body = resp.json()
    assert body["market_id"] == "rancho_cucamonga"
    assert len(body["alerts"]) == 1
    assert body["alerts"][0]["alert_id"] == "alert-1"


def test_sentiment_routes_return_404_for_unknown_market():
    client = _make_client()

    registry = MagicMock()
    registry.get_market_config.return_value = None

    with patch("ghl_real_estate_ai.api.routes.market_intelligence_v2.get_market_registry", return_value=registry):
        radar_resp = client.get("/api/v2/market-intelligence/markets/unknown/sentiment/radar")
        alerts_resp = client.get("/api/v2/market-intelligence/markets/unknown/sentiment/alerts")

    assert radar_resp.status_code == 404
    assert alerts_resp.status_code == 404
