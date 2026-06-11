"""Tests for GET /api/portfolio/telemetry.

Follows the minimal-app pattern from test_demo_chat_routes.py:
- Spin up a bare FastAPI with only the portfolio_telemetry router.
- Use TestClient (sync, no running event loop required).
- Mock service imports so the test suite has no Redis/Postgres deps.
"""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from ghl_real_estate_ai.api.routes import portfolio_telemetry

pytestmark = pytest.mark.unit

_FAKE_CACHE_METRICS = {
    "requests_processed": 42,
    "avg_response_time": 0.087,
    "errors": 1,
}

_FAKE_DASHBOARD = {
    "date": "2026-06-11",
    "realtime_metrics": {
        "progressive_tokens_today": 1000,
        "current_tokens_today": 1200,
        "efficiency_percent": 16.7,
    },
    "status": "operational",
}

_FAKE_EFFICIENCY = {
    "period_days": 7,
    "analysis_date": "2026-06-11T00:00:00",
    "summary": {},
}

_FAKE_MESH_STATUS = {
    "timestamp": "2026-06-11T00:00:00",
    "agents": {"total": 3, "active": 3, "idle": 2, "busy": 1, "error": 0},
    "tasks": {"active": 1, "completed_today": 5, "failed_today": 0},
    "performance": {},
    "costs": {
        "total_cost_today": 0.12,
        "current_hour_cost": 0.01,
        "projected_monthly_cost": 3.6,
    },
}


# ---------------------------------------------------------------------------
# Override the autouse compliance guard fixture - it triggers a network fetch
# for the tiktoken BPE file which fails in a sandboxed test environment.
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def disable_compliance_guard(mocker):
    mocker.patch(
        "ghl_real_estate_ai.api.routes.portfolio_telemetry._collect_cache",
        side_effect=lambda: _collect_cache_orig(),
    )
    # Just yield - we do the real patching per-test via the helpers below.
    # The override here prevents the global conftest fixture from running its
    # import chain that requires a network-fetched tiktoken model file.
    yield


def _make_client() -> TestClient:
    app = FastAPI()
    app.include_router(portfolio_telemetry.router)
    return TestClient(app, raise_server_exceptions=False)


# Keep a reference to the real function so the autouse override can call it
# when tests don't patch it themselves.
_collect_cache_orig = portfolio_telemetry._collect_cache


# ---------------------------------------------------------------------------
# Patch helpers - target the source modules directly since the route functions
# use lazy imports (import inside the function body).
# ---------------------------------------------------------------------------


def _patch_orchestrator(metrics: dict | None = None, raises: Exception | None = None):
    mock_orch = MagicMock()
    if raises:
        mock_orch.get_performance_metrics.side_effect = raises
    else:
        mock_orch.get_performance_metrics.return_value = metrics or _FAKE_CACHE_METRICS
    return patch(
        "ghl_real_estate_ai.services.claude_orchestrator.get_claude_orchestrator",
        return_value=mock_orch,
    )


def _patch_token_tracker(raises: Exception | None = None):
    mock_tracker = MagicMock()
    if raises:
        mock_tracker.get_realtime_dashboard = AsyncMock(side_effect=raises)
        mock_tracker.get_efficiency_report = AsyncMock(side_effect=raises)
    else:
        mock_tracker.get_realtime_dashboard = AsyncMock(return_value=_FAKE_DASHBOARD)
        mock_tracker.get_efficiency_report = AsyncMock(return_value=_FAKE_EFFICIENCY)
    return patch(
        "ghl_real_estate_ai.services.token_tracker.get_token_tracker",
        return_value=mock_tracker,
    )


def _patch_mesh_coordinator(raises: Exception | None = None):
    mock_coord = MagicMock()
    if raises:
        mock_coord.get_mesh_status = AsyncMock(side_effect=raises)
    else:
        mock_coord.get_mesh_status = AsyncMock(return_value=_FAKE_MESH_STATUS)
    return patch(
        "ghl_real_estate_ai.services.agent_mesh_coordinator.get_mesh_coordinator",
        return_value=mock_coord,
    )


# ---------------------------------------------------------------------------
# Tests: happy path
# ---------------------------------------------------------------------------


class TestTelemetryHappyPath:
    def test_returns_200(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {"correctness": 0.9}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            response = _make_client().get("/api/portfolio/telemetry")

        assert response.status_code == 200

    def test_top_level_shape(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {"correctness": 0.9}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            payload = _make_client().get("/api/portfolio/telemetry").json()

        assert "generated_at" in payload
        assert "sections" in payload
        assert set(payload["sections"].keys()) == {"cache", "tokens", "mesh", "evals"}

    def test_cache_section_data(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            payload = _make_client().get("/api/portfolio/telemetry").json()

        cache = payload["sections"]["cache"]
        assert cache["available"] is True
        assert cache["data"]["requests_processed"] == 42

    def test_tokens_section_data(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            payload = _make_client().get("/api/portfolio/telemetry").json()

        tokens = payload["sections"]["tokens"]
        assert tokens["available"] is True
        assert "realtime" in tokens["data"]
        assert "efficiency_7d" in tokens["data"]

    def test_mesh_section_data(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            payload = _make_client().get("/api/portfolio/telemetry").json()

        mesh = payload["sections"]["mesh"]
        assert mesh["available"] is True
        assert mesh["data"]["agents"]["total"] == 3


# ---------------------------------------------------------------------------
# Tests: graceful degradation
# ---------------------------------------------------------------------------


class TestTelemetryDegradation:
    def test_cache_failure_degrades_gracefully(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(raises=RuntimeError("Redis down")),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            response = _make_client().get("/api/portfolio/telemetry")

        assert response.status_code == 200
        sections = response.json()["sections"]
        assert sections["cache"]["available"] is False
        assert "Redis down" in sections["cache"]["reason"]
        assert sections["tokens"]["available"] is True
        assert sections["mesh"]["available"] is True

    def test_tokens_failure_degrades_gracefully(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(raises=ConnectionError("no redis")),
            _patch_mesh_coordinator(),
        ):
            response = _make_client().get("/api/portfolio/telemetry")

        assert response.status_code == 200
        sections = response.json()["sections"]
        assert sections["tokens"]["available"] is False
        assert sections["cache"]["available"] is True
        assert sections["mesh"]["available"] is True

    def test_mesh_failure_degrades_gracefully(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(raises=Exception("coordinator not ready")),
        ):
            response = _make_client().get("/api/portfolio/telemetry")

        assert response.status_code == 200
        sections = response.json()["sections"]
        assert sections["mesh"]["available"] is False
        assert "coordinator not ready" in sections["mesh"]["reason"]
        assert sections["cache"]["available"] is True
        assert sections["tokens"]["available"] is True

    def test_all_services_failing_still_returns_200(self, tmp_path):
        # No baseline.json -> evals also unavailable
        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(raises=Exception("boom")),
            _patch_token_tracker(raises=Exception("boom")),
            _patch_mesh_coordinator(raises=Exception("boom")),
        ):
            response = _make_client().get("/api/portfolio/telemetry")

        assert response.status_code == 200
        sections = response.json()["sections"]
        assert sections["cache"]["available"] is False
        assert sections["tokens"]["available"] is False
        assert sections["mesh"]["available"] is False
        assert sections["evals"]["available"] is False


# ---------------------------------------------------------------------------
# Tests: evals section
# ---------------------------------------------------------------------------


class TestEvalsSection:
    def test_reads_baseline_json(self, tmp_path):
        rubrics = {"correctness": 0.90, "tone": 0.90, "safety": 1.00, "compliance": 0.95}
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": rubrics, "generated": "2026-04-07"}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            evals = _make_client().get("/api/portfolio/telemetry").json()["sections"]["evals"]

        assert evals["available"] is True
        assert evals["baseline"]["rubrics"]["safety"] == 1.00
        assert evals["baseline"]["generated"] == "2026-04-07"

    def test_no_latest_results_when_file_absent(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            evals = _make_client().get("/api/portfolio/telemetry").json()["sections"]["evals"]

        assert evals["available"] is True
        assert "latest" not in evals

    def test_includes_latest_results_when_present(self, tmp_path):
        (tmp_path / "baseline.json").write_text(json.dumps({"rubrics": {}}))
        (tmp_path / "latest_results.json").write_text(json.dumps({"score": 0.95, "run_id": "abc"}))

        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            evals = _make_client().get("/api/portfolio/telemetry").json()["sections"]["evals"]

        assert evals["available"] is True
        assert evals["latest"]["run_id"] == "abc"

    def test_missing_baseline_returns_unavailable(self, tmp_path):
        with (
            patch.object(portfolio_telemetry, "_EVALS_DIR", tmp_path),
            _patch_orchestrator(),
            _patch_token_tracker(),
            _patch_mesh_coordinator(),
        ):
            evals = _make_client().get("/api/portfolio/telemetry").json()["sections"]["evals"]

        assert evals["available"] is False
        assert "baseline.json" in evals["reason"]
