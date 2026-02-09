"""
Real-Time Market Intelligence API Routes — Rancho Cucamonga

Exposes live market data, price trends, opportunity detection, alerts,
and neighborhood comparisons for the five core RC neighborhoods.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.real_time_market_intelligence import (
    get_market_intelligence,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/rc-market",
    tags=["Rancho Cucamonga Market Intelligence"],
)


# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------


class MarketSnapshotResponse(BaseModel):
    neighborhood: str
    median_price: int
    avg_days_on_market: int
    active_inventory: int
    avg_price_per_sqft: int
    appreciation_rate: float
    market_condition: str
    buyer_competition_index: float


class PriceTrendResponse(BaseModel):
    neighborhood: str
    period_days: int
    direction: str
    price_change_pct: float
    momentum: float
    support_level: int
    resistance_level: int
    forecast_30d_pct: float
    confidence: float


class OpportunityResponse(BaseModel):
    opportunity_id: str
    neighborhood: str
    opportunity_type: str
    score: float
    description: str
    recommended_action: str
    estimated_value: int
    time_sensitivity: str


class AlertResponse(BaseModel):
    alert_id: str
    severity: str
    neighborhood: str
    title: str
    message: str
    metric_name: str
    metric_value: float
    threshold: float


class PriceUpdateRequest(BaseModel):
    neighborhood: str = Field(..., description="Neighborhood name")
    price: int = Field(..., gt=0, description="New price data point")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/snapshot/{neighborhood}", response_model=MarketSnapshotResponse)
async def get_market_snapshot(neighborhood: str):
    """Get current market conditions for a Rancho Cucamonga neighborhood."""
    try:
        intel = get_market_intelligence()
        snap = await intel.get_market_snapshot(neighborhood)
        return MarketSnapshotResponse(
            neighborhood=snap.neighborhood,
            median_price=snap.median_price,
            avg_days_on_market=snap.avg_days_on_market,
            active_inventory=snap.active_inventory,
            avg_price_per_sqft=snap.avg_price_per_sqft,
            appreciation_rate=snap.appreciation_rate,
            market_condition=snap.market_condition.value,
            buyer_competition_index=snap.buyer_competition_index,
        )
    except Exception as e:
        logger.error("Market snapshot failed for %s: %s", neighborhood, e)
        raise HTTPException(500, f"Market snapshot error: {e}")


@router.get("/trends/{neighborhood}", response_model=PriceTrendResponse)
async def get_price_trends(
    neighborhood: str,
    days: int = Query(90, ge=7, le=365, description="Trend period in days"),
):
    """Get price trend analysis for a neighborhood."""
    try:
        intel = get_market_intelligence()
        trend = await intel.get_price_trends(neighborhood, days)
        return PriceTrendResponse(
            neighborhood=trend.neighborhood,
            period_days=trend.period_days,
            direction=trend.direction.value,
            price_change_pct=trend.price_change_pct,
            momentum=trend.momentum,
            support_level=trend.support_level,
            resistance_level=trend.resistance_level,
            forecast_30d_pct=trend.forecast_30d_pct,
            confidence=trend.confidence,
        )
    except Exception as e:
        logger.error("Price trends failed for %s: %s", neighborhood, e)
        raise HTTPException(500, f"Price trends error: {e}")


@router.get("/opportunities")
async def detect_opportunities(
    min_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum opportunity score"),
):
    """Scan all neighborhoods for actionable market opportunities."""
    try:
        intel = get_market_intelligence()
        opps = await intel.detect_opportunities(min_score)
        return {
            "opportunities": [
                OpportunityResponse(
                    opportunity_id=o.opportunity_id,
                    neighborhood=o.neighborhood,
                    opportunity_type=o.opportunity_type,
                    score=o.score,
                    description=o.description,
                    recommended_action=o.recommended_action,
                    estimated_value=o.estimated_value,
                    time_sensitivity=o.time_sensitivity,
                ).model_dump()
                for o in opps
            ],
            "total": len(opps),
        }
    except Exception as e:
        logger.error("Opportunity detection failed: %s", e)
        raise HTTPException(500, f"Opportunity detection error: {e}")


@router.get("/alerts")
async def check_market_alerts(
    appreciation_warning: Optional[float] = Query(None, description="Appreciation threshold"),
    dom_critical: Optional[float] = Query(None, description="Days-on-market threshold"),
    inventory_low: Optional[float] = Query(None, description="Low inventory threshold"),
):
    """Check for market threshold breaches and generate alerts."""
    try:
        intel = get_market_intelligence()
        thresholds = {}
        if appreciation_warning is not None:
            thresholds["appreciation_warning"] = appreciation_warning
        if dom_critical is not None:
            thresholds["dom_critical"] = dom_critical
        if inventory_low is not None:
            thresholds["inventory_low"] = inventory_low

        alerts = await intel.check_alerts(thresholds or None)
        return {
            "alerts": [
                AlertResponse(
                    alert_id=a.alert_id,
                    severity=a.severity.value,
                    neighborhood=a.neighborhood,
                    title=a.title,
                    message=a.message,
                    metric_name=a.metric_name,
                    metric_value=a.metric_value,
                    threshold=a.threshold,
                ).model_dump()
                for a in alerts
            ],
            "total": len(alerts),
        }
    except Exception as e:
        logger.error("Alert check failed: %s", e)
        raise HTTPException(500, f"Alert check error: {e}")


@router.get("/comparison")
async def compare_neighborhoods():
    """Compare all Rancho Cucamonga neighborhoods side-by-side."""
    try:
        intel = get_market_intelligence()
        comparison = await intel.get_neighborhood_comparison()
        return {"neighborhoods": comparison, "total": len(comparison)}
    except Exception as e:
        logger.error("Neighborhood comparison failed: %s", e)
        raise HTTPException(500, f"Comparison error: {e}")


@router.post("/price-update")
async def ingest_price_update(request: PriceUpdateRequest):
    """Ingest a new price data point for real-time tracking."""
    try:
        intel = get_market_intelligence()
        intel.ingest_price_update(request.neighborhood, request.price)
        return {
            "status": "ingested",
            "neighborhood": request.neighborhood,
            "price": request.price,
        }
    except Exception as e:
        logger.error("Price update ingestion failed: %s", e)
        raise HTTPException(500, f"Price update error: {e}")


@router.get("/health")
async def rc_market_health():
    """Health check for the real-time market intelligence service."""
    try:
        intel = get_market_intelligence()
        return {
            "status": "healthy",
            "service": "real_time_market_intelligence",
            "neighborhoods_tracked": len(intel._price_history),
            "alerts_generated": len(intel._alerts),
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
