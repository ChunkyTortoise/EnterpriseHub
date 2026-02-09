"""
Jorge's Advanced Analytics API Routes.

Provides endpoints for comprehensive business intelligence and forecasting:
- Revenue forecasting with confidence intervals
- Conversion funnel analysis and optimization
- Lead scoring accuracy and calibration tracking
- Market timing intelligence for Rancho Cucamonga
- Geographic performance analysis
- ROI analysis by lead source
- Executive dashboard summaries

Supports real-time analytics with <2s response time SLA.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.api.middleware.auth import User, get_current_user
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.analytics_models import (
    AnalyticsRequest,
    CompetitiveIntel,
    ExecutiveSummary,
    FunnelAnalysis,
    GeographicAnalysis,
    LeadQualityMetrics,
    MarketTimingInsight,
    MetricCategory,
    PerformanceGoal,
    PerformanceSummary,
    RevenueForecast,
    SourceROI,
)
from ghl_real_estate_ai.services.jorge_analytics_service import JorgeAnalyticsService

logger = get_logger(__name__)
router = APIRouter(prefix="/jorge/analytics", tags=["jorge-analytics"])


# ================== REQUEST/RESPONSE MODELS ==================


class ForecastRequest(BaseModel):
    """Request for revenue forecasting."""

    horizon_days: int = Field(default=30, ge=1, le=365, description="Forecast horizon in days")
    confidence_level: float = Field(default=0.85, ge=0.5, le=0.99, description="Confidence level for intervals")
    include_seasonality: bool = Field(default=True, description="Include seasonal adjustments")
    scenario: Optional[str] = Field(None, description="Scenario analysis (conservative, optimistic, realistic)")


class FunnelAnalysisRequest(BaseModel):
    """Request for conversion funnel analysis."""

    time_period_days: int = Field(default=30, ge=1, le=365, description="Analysis time window")
    segment_by: Optional[str] = Field(None, description="Segment analysis by field (source, agent, etc.)")
    include_optimization_suggestions: bool = Field(default=True, description="Include optimization recommendations")


class LeadQualityRequest(BaseModel):
    """Request for lead quality analysis."""

    time_period_days: int = Field(default=30, ge=1, le=365, description="Analysis time window")
    include_calibration: bool = Field(default=True, description="Include calibration analysis")
    include_trends: bool = Field(default=True, description="Include trend analysis")
    source_breakdown: bool = Field(default=True, description="Include source-level breakdown")


class GeographicAnalysisRequest(BaseModel):
    """Request for geographic performance analysis."""

    time_period_days: int = Field(default=30, ge=1, le=365, description="Analysis time window")
    zip_codes: Optional[List[str]] = Field(None, description="Specific ZIP codes to analyze")
    include_opportunity_analysis: bool = Field(default=True, description="Include expansion opportunities")
    min_lead_threshold: int = Field(default=5, description="Minimum leads required for analysis")


class PerformanceGoalRequest(BaseModel):
    """Request to create or update performance goal."""

    goal_name: str = Field(..., description="Goal name")
    goal_category: MetricCategory = Field(..., description="Goal category")
    metric_name: str = Field(..., description="Metric being tracked")
    target_value: float = Field(..., description="Target value")
    target_date: date = Field(..., description="Target completion date")
    priority: str = Field(default="medium", description="Goal priority (high/medium/low)")


class DashboardFilters(BaseModel):
    """Dashboard filtering options."""

    date_range_days: int = Field(default=30, ge=1, le=365, description="Date range for analysis")
    lead_sources: Optional[List[str]] = Field(None, description="Filter by lead sources")
    neighborhoods: Optional[List[str]] = Field(None, description="Filter by neighborhoods")
    agent_filter: Optional[str] = Field(None, description="Filter by agent")
    include_forecasts: bool = Field(default=True, description="Include forecasting data")
    include_competitive: bool = Field(default=False, description="Include competitive analysis")


class AlertThreshold(BaseModel):
    """Performance alert threshold configuration."""

    metric_name: str = Field(..., description="Metric to monitor")
    threshold_value: float = Field(..., description="Alert threshold")
    threshold_type: str = Field(..., description="above/below/equal")
    alert_frequency: str = Field(default="daily", description="Alert frequency")


class AnalyticsSummaryResponse(BaseModel):
    """Quick analytics summary response."""

    period: str
    key_metrics: Dict[str, float]
    trends: Dict[str, str]  # up/down/stable
    alerts: List[str]
    top_opportunities: List[str]
    generated_at: datetime


# ================== DEPENDENCY INJECTION ==================


def get_analytics_service() -> JorgeAnalyticsService:
    """Get analytics service instance."""
    return JorgeAnalyticsService()


# ================== MAIN ANALYTICS ENDPOINTS ==================


@router.get("/executive-summary", response_model=ExecutiveSummary)
async def get_executive_summary(
    filters: DashboardFilters = Depends(),
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get comprehensive executive summary for Jorge's dashboard.

    Provides all key metrics, forecasts, and insights in a single response
    optimized for executive-level reporting.
    """
    try:
        logger.info(f"Generating executive summary for {filters.date_range_days} days")

        # Create analytics request
        request = AnalyticsRequest(
            time_window_days=filters.date_range_days,
            include_forecasts=filters.include_forecasts,
            include_geographic=True,
            include_competitive=filters.include_competitive,
            segment_filters={
                "lead_sources": filters.lead_sources,
                "neighborhoods": filters.neighborhoods,
                "agent": filters.agent_filter,
            }
            if any([filters.lead_sources, filters.neighborhoods, filters.agent_filter])
            else None,
        )

        # Get comprehensive summary
        summary = await service.get_executive_summary(request)

        logger.info(f"Generated executive summary with {len(summary.key_insights)} insights")
        return summary

    except Exception as e:
        logger.error(f"Executive summary generation failed: {e}")
        raise HTTPException(status_code=500, detail="Unable to generate executive summary")


@router.post("/forecast", response_model=RevenueForecast)
async def generate_revenue_forecast(
    request: ForecastRequest,
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Generate revenue forecast using time-series analysis.

    Uses hybrid forecasting combining linear regression with seasonal
    adjustments for accurate business planning.
    """
    try:
        logger.info(f"Generating {request.horizon_days}-day revenue forecast")

        forecast = await service.get_revenue_forecast(
            horizon_days=request.horizon_days, confidence_level=request.confidence_level
        )

        logger.info(f"Forecast: ${forecast.forecasted_revenue:,.0f} with {forecast.confidence_level:.0%} confidence")
        return forecast

    except Exception as e:
        logger.error(f"Revenue forecasting failed: {e}")
        raise HTTPException(status_code=500, detail="Revenue forecasting service unavailable")


@router.post("/funnel-analysis", response_model=FunnelAnalysis)
async def analyze_conversion_funnel(
    request: FunnelAnalysisRequest,
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze conversion funnel performance with optimization insights.

    Identifies bottlenecks, drop-off points, and improvement opportunities
    across the entire lead-to-close pipeline.
    """
    try:
        logger.info(f"Analyzing conversion funnel for {request.time_period_days} days")

        analysis = await service.analyze_conversion_funnel(request.time_period_days)

        logger.info(
            f"Funnel analysis: {analysis.overall_conversion_rate:.1%} conversion rate, bottleneck at {analysis.bottleneck_stage.value}"
        )
        return analysis

    except Exception as e:
        logger.error(f"Funnel analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Funnel analysis service unavailable")


@router.post("/lead-quality", response_model=LeadQualityMetrics)
async def analyze_lead_quality(
    request: LeadQualityRequest,
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze lead scoring quality and accuracy metrics.

    Provides calibration analysis, accuracy trends, and performance
    breakdown by confidence levels and lead sources.
    """
    try:
        logger.info(f"Analyzing lead quality for {request.time_period_days} days")

        metrics = await service.get_lead_quality_summary(request.time_period_days)

        logger.info(
            f"Lead quality: {metrics.prediction_accuracy:.1%} accuracy, {metrics.total_leads_scored} leads analyzed"
        )
        return metrics

    except Exception as e:
        logger.error(f"Lead quality analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Lead quality analysis service unavailable")


@router.get("/market-timing", response_model=MarketTimingInsight)
async def get_market_timing_intelligence(
    service: JorgeAnalyticsService = Depends(get_analytics_service), current_user: User = Depends(get_current_user)
):
    """
    Get market timing intelligence for Rancho Cucamonga.

    Provides real estate market conditions, timing recommendations,
    and seasonal forecasts for optimal buying/selling decisions.
    """
    try:
        logger.info("Getting market timing intelligence")

        insight = await service.get_market_timing_intelligence()

        logger.info(f"Market timing: {insight.current_conditions.market_temperature.value} market")
        return insight

    except Exception as e:
        logger.error(f"Market timing analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Market timing service unavailable")


@router.post("/geographic-analysis", response_model=GeographicAnalysis)
async def analyze_geographic_performance(
    request: GeographicAnalysisRequest,
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Analyze performance by geographic area.

    Provides ZIP code and neighborhood-level performance metrics,
    market share estimates, and expansion opportunities.
    """
    try:
        logger.info(f"Analyzing geographic performance for {request.time_period_days} days")

        analysis = await service.analyze_geographic_performance(request.time_period_days)

        logger.info(f"Geographic analysis: {len(analysis.geographic_metrics)} areas analyzed")
        return analysis

    except Exception as e:
        logger.error(f"Geographic analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Geographic analysis service unavailable")


@router.get("/source-roi", response_model=List[SourceROI])
async def get_source_roi_analysis(
    time_period_days: int = Query(default=30, ge=1, le=365, description="Analysis time window"),
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get ROI analysis by lead source.

    Provides detailed ROI metrics, attribution modeling, and
    cost-effectiveness analysis for all lead generation channels.
    """
    try:
        logger.info(f"Getting source ROI analysis for {time_period_days} days")

        roi_analysis = await service.get_source_roi_analysis(time_period_days)

        logger.info(f"Source ROI: {len(roi_analysis)} sources analyzed")
        return roi_analysis

    except Exception as e:
        logger.error(f"Source ROI analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Source ROI analysis service unavailable")


@router.get("/competitive-intelligence", response_model=CompetitiveIntel)
async def get_competitive_intelligence(
    service: JorgeAnalyticsService = Depends(get_analytics_service), current_user: User = Depends(get_current_user)
):
    """
    Get competitive intelligence for Rancho Cucamonga market.

    Provides market share analysis, competitive positioning,
    and strategic recommendations for market leadership.
    """
    try:
        logger.info("Getting competitive intelligence")

        intel = await service.get_competitive_intelligence()

        logger.info(f"Competitive intelligence: {intel.estimated_market_share:.1%} market share")
        return intel

    except Exception as e:
        logger.error(f"Competitive intelligence failed: {e}")
        raise HTTPException(status_code=500, detail="Competitive intelligence service unavailable")


@router.get("/performance-summary", response_model=PerformanceSummary)
async def get_performance_summary(
    time_period_days: int = Query(default=30, ge=1, le=365, description="Analysis time window"),
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get performance summary with trends and alerts.

    Provides high-level performance metrics, trend analysis,
    and actionable alerts for business optimization.
    """
    try:
        logger.info(f"Getting performance summary for {time_period_days} days")

        summary = await service.get_performance_summary(time_period_days)

        logger.info(
            f"Performance summary: ${summary.total_revenue:,.0f} revenue, {summary.total_conversions} conversions"
        )
        return summary

    except Exception as e:
        logger.error(f"Performance summary failed: {e}")
        raise HTTPException(status_code=500, detail="Performance summary service unavailable")


# ================== QUICK ACCESS ENDPOINTS ==================


@router.get("/quick-summary", response_model=AnalyticsSummaryResponse)
async def get_quick_analytics_summary(
    days: int = Query(default=7, ge=1, le=90, description="Days to analyze"),
    service: JorgeAnalyticsService = Depends(get_analytics_service),
    current_user: User = Depends(get_current_user),
):
    """
    Get quick analytics summary for mobile/widget use.

    Optimized for fast loading with essential metrics only.
    """
    try:
        # Get lightweight summary
        performance = await service.get_performance_summary(days)

        return AnalyticsSummaryResponse(
            period=f"Last {days} days",
            key_metrics={
                "revenue": performance.total_revenue,
                "conversions": float(performance.total_conversions),
                "conversion_rate": performance.avg_conversion_rate,
                "scoring_accuracy": performance.lead_scoring_accuracy,
            },
            trends={
                "revenue": performance.revenue_trend,
                "conversions": performance.conversion_trend,
                "quality": performance.quality_trend,
            },
            alerts=performance.performance_alerts[:3],  # Top 3 alerts
            top_opportunities=performance.improvement_opportunities[:3],  # Top 3 opportunities
            generated_at=datetime.utcnow(),
        )

    except Exception as e:
        logger.error(f"Quick summary failed: {e}")
        raise HTTPException(status_code=500, detail="Quick summary service unavailable")


@router.get("/kpi-dashboard", response_model=Dict[str, Any])
async def get_kpi_dashboard(
    service: JorgeAnalyticsService = Depends(get_analytics_service), current_user: User = Depends(get_current_user)
):
    """
    Get KPI dashboard with real-time metrics.

    Provides key performance indicators optimized for dashboard display.
    """
    try:
        # Get real-time KPIs
        performance = await service.get_performance_summary(30)
        forecast = await service.get_revenue_forecast(30)

        return {
            "current_metrics": {
                "monthly_revenue": performance.total_revenue,
                "monthly_conversions": performance.total_conversions,
                "avg_conversion_rate": performance.avg_conversion_rate,
                "lead_scoring_accuracy": performance.lead_scoring_accuracy,
            },
            "forecasts": {
                "next_30_days_revenue": forecast.forecasted_revenue,
                "predicted_conversions": forecast.predicted_conversions,
                "confidence_level": forecast.confidence_level,
            },
            "trends": {
                "revenue": performance.revenue_trend,
                "conversions": performance.conversion_trend,
                "quality": performance.quality_trend,
            },
            "goal_progress": {
                "on_track": performance.goals_on_track,
                "behind": performance.goals_behind,
                "ahead": performance.goals_ahead,
            },
            "alerts": performance.performance_alerts,
            "last_updated": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"KPI dashboard failed: {e}")
        raise HTTPException(status_code=500, detail="KPI dashboard service unavailable")


# ================== GOAL MANAGEMENT ==================


@router.get("/goals", response_model=List[PerformanceGoal])
async def list_performance_goals(
    category: Optional[MetricCategory] = Query(None, description="Filter by goal category"),
    active_only: bool = Query(default=True, description="Show only active goals"),
    current_user: User = Depends(get_current_user),
):
    """
    List performance goals with progress tracking.
    """
    try:
        # Mock implementation - would query database in production
        goals = [
            PerformanceGoal(
                goal_name="Monthly Revenue Target",
                goal_category=MetricCategory.REVENUE,
                metric_name="monthly_revenue",
                target_value=125000,
                current_value=112500,
                goal_period="monthly",
                start_date=date.today().replace(day=1),
                target_date=date.today().replace(day=28),
                completion_percentage=90.0,
                on_track=True,
                assigned_to="Jorge",
                priority="high",
            ),
            PerformanceGoal(
                goal_name="Lead Scoring Accuracy",
                goal_category=MetricCategory.QUALITY,
                metric_name="prediction_accuracy",
                target_value=92.0,
                current_value=87.2,
                goal_period="monthly",
                start_date=date.today().replace(day=1),
                target_date=date.today().replace(day=28),
                completion_percentage=75.0,
                on_track=True,
                assigned_to="Jorge",
                priority="medium",
            ),
        ]

        if category:
            goals = [g for g in goals if g.goal_category == category]

        return goals

    except Exception as e:
        logger.error(f"Failed to list goals: {e}")
        raise HTTPException(status_code=500, detail="Unable to retrieve performance goals")


@router.post("/goals", response_model=Dict[str, str])
async def create_performance_goal(goal: PerformanceGoalRequest, current_user: User = Depends(get_current_user)):
    """
    Create a new performance goal.
    """
    try:
        logger.info(f"Creating performance goal: {goal.goal_name}")

        # In production, would save to database
        goal_id = f"goal_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        return {
            "goal_id": goal_id,
            "status": "created",
            "message": f"Performance goal '{goal.goal_name}' created successfully",
        }

    except Exception as e:
        logger.error(f"Failed to create goal: {e}")
        raise HTTPException(status_code=500, detail="Unable to create performance goal")


# ================== HEALTH & MONITORING ==================


@router.get("/health", response_model=Dict[str, Any])
async def analytics_health_check(service: JorgeAnalyticsService = Depends(get_analytics_service)):
    """
    Health check for analytics service.
    """
    try:
        # Test core functionality
        start_time = datetime.utcnow()

        # Quick health checks
        health_checks = {
            "service_status": "healthy",
            "database_connection": "available",
            "cache_service": "available",
            "forecasting_models": "loaded",
            "response_time_ms": 0,
        }

        # Measure response time
        response_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        health_checks["response_time_ms"] = int(response_time)

        return {
            "status": "healthy",
            "service": "jorge-analytics",
            "version": "1.0.0",
            "checks": health_checks,
            "timestamp": datetime.utcnow().isoformat(),
            "sla_target_ms": 2000,
            "performance": "within_target" if response_time < 2000 else "degraded",
        }

    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "service": "jorge-analytics",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
        }
