from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

_PREDICTION_IMPORT_ERROR = None
try:
    from ghl_real_estate_ai.api.routes import prediction as prediction_module
except Exception as exc:  # pragma: no cover - defensive import guard for flaky module graph
    prediction_module = None
    _PREDICTION_IMPORT_ERROR = str(exc)

skip_if_no_prediction = pytest.mark.skipif(
    prediction_module is None,
    reason=f"prediction module cannot be imported: {_PREDICTION_IMPORT_ERROR}",
)


def _make_client():
    app = FastAPI()
    app.include_router(prediction_module.router)
    app.dependency_overrides[prediction_module.get_current_user] = lambda: {"user_id": "u-123"}
    return TestClient(app, raise_server_exceptions=False)


def _make_obj(**kwargs):
    return SimpleNamespace(**kwargs)


@skip_if_no_prediction
def test_client_behavior_uses_repository_history_fetch():
    client = _make_client()

    psychology = _make_obj(profile_type="balanced")
    purchase = _make_obj(purchase_probability=0.81)
    patterns = _make_obj(patterns=["consistent_response"])
    financial = _make_obj(readiness_score=0.72)
    value = _make_obj(estimated_ltv=17500)
    strategy = {"jorge_methodology_fit_score": 0.88}

    with (
        patch.object(
            prediction_module, "_fetch_client_interaction_history", AsyncMock(return_value=[{"content": "msg"}])
        ) as mock_fetch,
        patch.object(
            prediction_module.client_analyzer, "analyze_client_psychology", AsyncMock(return_value=psychology)
        ),
        patch.object(prediction_module.client_analyzer, "predict_purchase_behavior", AsyncMock(return_value=purchase)),
        patch.object(prediction_module.client_analyzer, "assess_behavioral_patterns", AsyncMock(return_value=patterns)),
        patch.object(
            prediction_module.client_analyzer, "evaluate_financial_readiness", AsyncMock(return_value=financial)
        ),
        patch.object(prediction_module.client_analyzer, "predict_client_value", AsyncMock(return_value=value)),
        patch.object(
            prediction_module.client_analyzer, "determine_optimal_engagement_strategy", AsyncMock(return_value=strategy)
        ),
        patch.object(prediction_module.ws_manager, "broadcast_to_group", AsyncMock()),
    ):
        resp = client.post(
            "/prediction/client-behavior",
            json={"client_id": "c-001", "scenario": "purchase_timing"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["client_id"] == "c-001"
    assert body["purchase_prediction"]["purchase_probability"] == 0.81
    mock_fetch.assert_awaited_once_with("c-001")


@skip_if_no_prediction
def test_business_forecast_uses_profile_repository_values():
    client = _make_client()

    revenue = _make_obj(base_forecast=100000, growth_rate=0.12)
    market_share = _make_obj(share=0.18)
    team_projection = _make_obj(capacity_score=0.77)
    territory_analysis = _make_obj(expansion_score=0.66)
    opportunity = _make_obj(opportunity_type="market_expansion")
    strategic_plan = {"summary": "plan"}

    with (
        patch.object(
            prediction_module,
            "_fetch_business_profile",
            AsyncMock(
                return_value={
                    "target_markets": ["Dallas", "Houston"],
                    "team_size": 11,
                    "expansion_territories": ["Austin", "San Antonio"],
                }
            ),
        ),
        patch.object(prediction_module.business_forecaster, "forecast_revenue", AsyncMock(return_value=revenue)),
        patch.object(
            prediction_module.business_forecaster, "project_market_share_growth", AsyncMock(return_value=market_share)
        ),
        patch.object(
            prediction_module.business_forecaster, "forecast_team_performance", AsyncMock(return_value=team_projection)
        ),
        patch.object(
            prediction_module.business_forecaster,
            "analyze_territory_expansion",
            AsyncMock(return_value=territory_analysis),
        ),
        patch.object(
            prediction_module.business_forecaster,
            "identify_business_opportunities",
            AsyncMock(return_value=[opportunity]),
        ),
        patch.object(
            prediction_module.business_forecaster,
            "generate_strategic_business_plan",
            AsyncMock(return_value=strategic_plan),
        ),
        patch.object(prediction_module.ws_manager, "broadcast_to_group", AsyncMock()),
    ):
        resp = client.post(
            "/prediction/business-forecast",
            json={"metric_type": "revenue", "timeframe": "quarterly", "context": {}},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["metric_type"] == "revenue"
    assert body["strategic_plan"]["summary"] == "plan"
    assert body["team_performance_projection"]["capacity_score"] == 0.77


@skip_if_no_prediction
@pytest.mark.asyncio
async def test_continuous_monitoring_broadcast_payload_shape():
    async def _break_sleep(_seconds):
        raise asyncio.CancelledError()

    import asyncio

    with (
        patch.object(
            prediction_module,
            "prediction_health_check",
            AsyncMock(return_value={"engine_status": "healthy", "websocket_connections": 4}),
        ),
        patch.object(prediction_module.ws_manager, "broadcast_to_group", AsyncMock()) as mock_broadcast,
        patch.object(prediction_module.asyncio, "sleep", _break_sleep),
    ):
        with pytest.raises(asyncio.CancelledError):
            await prediction_module.continuous_prediction_monitoring()

    mock_broadcast.assert_awaited_once()
    args = mock_broadcast.await_args.args
    assert args[0] == "prediction_updates"
    payload = args[1]
    assert payload["type"] == "monitoring_tick"
    assert payload["status"] == "healthy"
    assert payload["websocket_connections"] == 4
    datetime.fromisoformat(payload["timestamp"])
