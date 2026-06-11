"""Read-only portfolio telemetry aggregation endpoint.

GET /api/portfolio/telemetry
Returns a single JSON document with aggregate metrics from the cache,
token, mesh, and eval subsystems. Every section degrades gracefully to
{"available": false, "reason": "<short>"} so the endpoint always returns 200.
No authentication required - only aggregate metrics are exposed; no API keys,
secrets, or PII appear in any section payload.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/portfolio", tags=["Portfolio"])

_EVALS_DIR = Path(__file__).resolve().parents[4] / "evals"


# ---------------------------------------------------------------------------
# Section collectors
# ---------------------------------------------------------------------------


def _collect_cache() -> dict[str, Any]:
    try:
        from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

        metrics = get_claude_orchestrator().get_performance_metrics()
        return {"available": True, "data": metrics}
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:120]}


async def _collect_tokens() -> dict[str, Any]:
    try:
        from ghl_real_estate_ai.services.token_tracker import get_token_tracker

        tracker = get_token_tracker()
        dashboard = await tracker.get_realtime_dashboard()
        efficiency = await tracker.get_efficiency_report(days=7)
        return {"available": True, "data": {"realtime": dashboard, "efficiency_7d": efficiency}}
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:120]}


async def _collect_mesh() -> dict[str, Any]:
    try:
        from ghl_real_estate_ai.services.agent_mesh_coordinator import get_mesh_coordinator

        status = await get_mesh_coordinator().get_mesh_status()
        return {"available": True, "data": status}
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:120]}


def _collect_evals() -> dict[str, Any]:
    try:
        baseline_path = _EVALS_DIR / "baseline.json"
        if not baseline_path.exists():
            return {"available": False, "reason": "baseline.json not found"}

        baseline = json.loads(baseline_path.read_text())

        result: dict[str, Any] = {"available": True, "baseline": baseline}

        latest_path = _EVALS_DIR / "latest_results.json"
        if latest_path.exists():
            result["latest"] = json.loads(latest_path.read_text())

        return result
    except Exception as exc:
        return {"available": False, "reason": str(exc)[:120]}


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------


@router.get("/telemetry", summary="Aggregate portfolio telemetry")
async def get_portfolio_telemetry() -> JSONResponse:
    """Return aggregate metrics across cache, token, mesh, and eval subsystems.

    Always returns HTTP 200. Individual sections degrade to
    {"available": false, "reason": "..."} when their backing service is
    unavailable.
    """
    sections: dict[str, Any] = {}

    sections["cache"] = _collect_cache()
    sections["tokens"] = await _collect_tokens()
    sections["mesh"] = await _collect_mesh()
    sections["evals"] = _collect_evals()

    payload = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "sections": sections,
    }
    return JSONResponse(content=payload, status_code=200)
