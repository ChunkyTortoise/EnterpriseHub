"""Admin cost dashboard endpoint.

GET /admin/cost-dashboard?period=24h
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from ghl_real_estate_ai.database.session import async_session_factory
from ghl_real_estate_ai.services.cost_governance import CostTracker

router = APIRouter(tags=["Cost Governance"])

_VALID_PERIODS = {"1h", "6h", "24h", "7d", "30d"}


@router.get("/admin/cost-dashboard")
async def cost_dashboard(period: str = Query("24h", description="Time period")) -> dict[str, Any]:
    """Return cost summary for the requested period."""
    if period not in _VALID_PERIODS:
        period = "24h"
    tracker = CostTracker(async_session_factory)
    return await tracker.get_summary(period)
