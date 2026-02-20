"""Call analytics API routes."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Request

from voice_ai.models.call_analytics import (
    CallAnalyticsResponse,
    CallMetrics,
    CostBreakdown,
    SentimentSummary,
)

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/calls", response_model=CallAnalyticsResponse)
async def get_call_analytics(
    request: Request,
    period: str = "7d",
    group_by: str | None = None,
) -> CallAnalyticsResponse:
    """Get aggregated call analytics for a time period.

    Periods: 1d, 7d, 30d, 90d
    """
    period_days = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}.get(period, 7)
    end_date = datetime.now(UTC)
    start_date = end_date - timedelta(days=period_days)

    # MVP: return empty analytics (DB query in production)
    return CallAnalyticsResponse(
        period=period,
        start_date=start_date,
        end_date=end_date,
        metrics=CallMetrics(),
        sentiment=SentimentSummary(),
        costs=CostBreakdown(),
        calls_by_bot_type={},
        calls_by_direction={},
    )
