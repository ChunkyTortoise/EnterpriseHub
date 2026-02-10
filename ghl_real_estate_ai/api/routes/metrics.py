"""Prometheus metrics endpoints."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse

from ghl_real_estate_ai.services.performance_tracker import get_performance_tracker

router = APIRouter(tags=["Metrics"])


@router.get("/metrics", include_in_schema=False)
async def get_metrics() -> PlainTextResponse:
    tracker = get_performance_tracker()
    payload = tracker.export_prometheus_metrics()
    return PlainTextResponse(payload or "", media_type="text/plain")
