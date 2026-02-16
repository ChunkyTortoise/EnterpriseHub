"""Dashboard and metrics API."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/dashboards", tags=["dashboards"])


class DashboardSummary(BaseModel):
    name: str
    module: str
    widget_count: int


class MetricSummary(BaseModel):
    metric_name: str
    current_value: float
    p50: float | None = None
    p95: float | None = None
    p99: float | None = None


@router.get("", response_model=list[DashboardSummary])
async def list_dashboards() -> list[DashboardSummary]:
    return [
        DashboardSummary(name="Agent Overview", module="monitoring", widget_count=6),
        DashboardSummary(name="Prompt Lab", module="prompt_registry", widget_count=4),
        DashboardSummary(name="Pipeline Status", module="data_pipeline", widget_count=5),
        DashboardSummary(name="Alerts", module="alerts", widget_count=3),
    ]


@router.get("/metrics", response_model=list[MetricSummary])
async def get_metrics() -> list[MetricSummary]:
    return []
