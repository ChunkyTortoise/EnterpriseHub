"""
Commission Forecast Engine API Routes

Exposes revenue forecasting, Monte Carlo simulation, and executive
summary generation from pipeline data.
"""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.commission_forecast_engine import (
    get_forecast_engine,
)

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/commission-forecast",
    tags=["Commission Forecasting"],
)


# ---------------------------------------------------------------------------
# Request / Response Models
# ---------------------------------------------------------------------------


class PipelineDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal identifier")
    contact_name: str = Field("", description="Contact name")
    property_value: int = Field(..., gt=0, description="Property value in dollars")
    stage: str = Field(
        "prospect", description="Deal stage: prospect, qualified, showing, offer, under_contract, closed"
    )
    expected_close_month: int = Field(..., ge=1, le=12, description="Expected close month (1-12)")
    deal_type: str = Field("buyer", description="Deal type: buyer or seller")
    commission_rate: Optional[float] = Field(None, ge=0, le=0.10)


class ForecastRequest(BaseModel):
    pipeline: List[PipelineDealInput] = Field(..., min_length=1, description="Pipeline deals")
    horizon_months: int = Field(3, ge=1, le=12, description="Forecast horizon in months")
    current_month: Optional[int] = Field(None, ge=1, le=12)


class MonthlyForecastResponse(BaseModel):
    month: int
    expected_revenue: float
    weighted_pipeline: float
    deal_count: int
    seasonal_factor: float
    confidence_low: float
    confidence_high: float


class ForecastResponse(BaseModel):
    total_expected: float
    total_weighted: float
    monthly_forecasts: List[MonthlyForecastResponse]
    deal_count: int
    avg_deal_value: float
    avg_commission: float
    forecast_horizon_months: int


class MonteCarloRequest(BaseModel):
    pipeline: List[PipelineDealInput] = Field(..., min_length=1)
    simulations: int = Field(1000, ge=100, le=10000, description="Number of simulations")
    target_revenue: float = Field(0.0, ge=0, description="Target revenue for probability calculation")


class MonteCarloResponse(BaseModel):
    simulations: int
    mean_revenue: float
    median_revenue: float
    std_dev: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    worst_case: float
    best_case: float
    probability_above_target: float


class ExecutiveSummaryRequest(BaseModel):
    pipeline: List[PipelineDealInput] = Field(..., min_length=1)
    horizon_months: int = Field(3, ge=1, le=12)
    include_monte_carlo: bool = Field(True, description="Include Monte Carlo simulation")
    target_revenue: float = Field(0.0, ge=0)


class ExecutiveSummaryResponse(BaseModel):
    total_pipeline_value: int
    weighted_pipeline_value: float
    expected_commission: float
    forecast_confidence: str
    top_deals: List[Dict[str, Any]]
    monthly_breakdown: List[Dict[str, Any]]
    risk_factors: List[str]
    opportunities: List[str]
    recommendation: str
    monte_carlo: Optional[MonteCarloResponse] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/forecast", response_model=ForecastResponse)
async def forecast_revenue(request: ForecastRequest):
    """Generate weighted revenue forecast from pipeline data."""
    try:
        engine = get_forecast_engine()
        pipeline_dicts = [d.model_dump() for d in request.pipeline]
        result = await engine.forecast_revenue(
            pipeline=pipeline_dicts,
            horizon_months=request.horizon_months,
            current_month=request.current_month,
        )
        return ForecastResponse(
            total_expected=result.total_expected,
            total_weighted=result.total_weighted,
            monthly_forecasts=[
                MonthlyForecastResponse(
                    month=f.month,
                    expected_revenue=f.expected_revenue,
                    weighted_pipeline=f.weighted_pipeline,
                    deal_count=f.deal_count,
                    seasonal_factor=f.seasonal_factor,
                    confidence_low=f.confidence_low,
                    confidence_high=f.confidence_high,
                )
                for f in result.monthly_forecasts
            ],
            deal_count=result.deal_count,
            avg_deal_value=result.avg_deal_value,
            avg_commission=result.avg_commission,
            forecast_horizon_months=result.forecast_horizon_months,
        )
    except Exception as e:
        logger.error("Revenue forecast failed: %s", e)
        raise HTTPException(500, f"Forecast error: {e}")


@router.post("/monte-carlo", response_model=MonteCarloResponse)
async def run_monte_carlo(request: MonteCarloRequest):
    """Run Monte Carlo simulation on pipeline to model revenue distribution."""
    try:
        engine = get_forecast_engine()
        pipeline_dicts = [d.model_dump() for d in request.pipeline]
        result = await engine.monte_carlo_simulation(
            pipeline=pipeline_dicts,
            simulations=request.simulations,
            target_revenue=request.target_revenue,
        )
        return MonteCarloResponse(
            simulations=result.simulations,
            mean_revenue=result.mean_revenue,
            median_revenue=result.median_revenue,
            std_dev=result.std_dev,
            percentile_10=result.percentile_10,
            percentile_25=result.percentile_25,
            percentile_75=result.percentile_75,
            percentile_90=result.percentile_90,
            worst_case=result.worst_case,
            best_case=result.best_case,
            probability_above_target=result.probability_above_target,
        )
    except Exception as e:
        logger.error("Monte Carlo simulation failed: %s", e)
        raise HTTPException(500, f"Monte Carlo error: {e}")


@router.post("/executive-summary", response_model=ExecutiveSummaryResponse)
async def generate_executive_summary(request: ExecutiveSummaryRequest):
    """Generate executive reporting summary from pipeline data."""
    try:
        engine = get_forecast_engine()
        pipeline_dicts = [d.model_dump() for d in request.pipeline]

        forecast = await engine.forecast_revenue(
            pipeline=pipeline_dicts,
            horizon_months=request.horizon_months,
        )

        mc_result = None
        mc_response = None
        if request.include_monte_carlo:
            mc_result = await engine.monte_carlo_simulation(
                pipeline=pipeline_dicts,
                target_revenue=request.target_revenue,
            )
            mc_response = MonteCarloResponse(
                simulations=mc_result.simulations,
                mean_revenue=mc_result.mean_revenue,
                median_revenue=mc_result.median_revenue,
                std_dev=mc_result.std_dev,
                percentile_10=mc_result.percentile_10,
                percentile_25=mc_result.percentile_25,
                percentile_75=mc_result.percentile_75,
                percentile_90=mc_result.percentile_90,
                worst_case=mc_result.worst_case,
                best_case=mc_result.best_case,
                probability_above_target=mc_result.probability_above_target,
            )

        summary = await engine.generate_executive_summary(forecast, mc_result)

        return ExecutiveSummaryResponse(
            total_pipeline_value=summary.total_pipeline_value,
            weighted_pipeline_value=summary.weighted_pipeline_value,
            expected_commission=summary.expected_commission,
            forecast_confidence=summary.forecast_confidence,
            top_deals=summary.top_deals,
            monthly_breakdown=summary.monthly_breakdown,
            risk_factors=summary.risk_factors,
            opportunities=summary.opportunities,
            recommendation=summary.recommendation,
            monte_carlo=mc_response,
        )
    except Exception as e:
        logger.error("Executive summary generation failed: %s", e)
        raise HTTPException(500, f"Executive summary error: {e}")


@router.get("/health")
async def forecast_health():
    """Health check for the commission forecast engine."""
    try:
        engine = get_forecast_engine()
        return {
            "status": "healthy",
            "service": "commission_forecast_engine",
            "default_commission_rate": engine.default_rate,
        }
    except Exception as e:
        return {"status": "degraded", "error": str(e)}
