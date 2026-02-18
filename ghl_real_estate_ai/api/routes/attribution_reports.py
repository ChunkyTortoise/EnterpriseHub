"""
Attribution Reports API - Dashboard Integration for Jorge's Lead Source Analytics.

Provides REST endpoints for accessing lead source performance data, reports,
and real-time analytics for Jorge's marketing dashboard integration.

Key Features:
- Source performance metrics and ROI analysis
- Weekly and monthly attribution reports
- Real-time alerts and recommendations
- Export capabilities for marketing analysis
- Trend analysis and forecasting data
- Campaign optimization insights
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.attribution_analytics import AttributionAnalytics, AttributionModel
from ghl_real_estate_ai.services.lead_source_tracker import LeadSource, LeadSourceTracker

logger = get_logger(__name__)
router = APIRouter(prefix="/attribution", tags=["attribution"])

# Initialize analytics services
attribution_analytics = AttributionAnalytics()
lead_source_tracker = LeadSourceTracker()


# Pydantic models for API responses
class SourcePerformanceResponse(BaseModel):
    """Source performance metrics response."""

    source: str
    total_leads: int
    qualified_leads: int
    hot_leads: int
    conversion_rate: float = Field(description="Deal conversion rate")
    qualification_rate: float = Field(description="Lead qualification rate")
    total_revenue: float
    avg_deal_size: float
    cost_per_lead: float
    cost_per_qualified_lead: float
    roi: float = Field(description="Return on investment")
    avg_lead_score: float
    avg_budget: float


class AlertResponse(BaseModel):
    """Performance alert response."""

    alert_type: str
    source: str
    severity: str
    title: str
    description: str
    current_value: float
    previous_value: float
    change_percentage: float
    recommendations: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None


class WeeklySummaryResponse(BaseModel):
    """Weekly performance summary response."""

    period: Dict[str, str]
    totals: Dict[str, Any]
    top_sources: List[Dict[str, Any]]
    biggest_changes: List[Dict[str, Any]]
    alerts_count: int


class AttributionReportResponse(BaseModel):
    """Complete attribution report response."""

    period_start: datetime
    period_end: datetime
    generated_at: datetime
    total_leads: int
    total_qualified_leads: int
    total_revenue: float
    total_cost: float
    overall_roi: float
    source_performance: List[SourcePerformanceResponse]
    active_alerts: List[AlertResponse]
    optimization_recommendations: List[Dict[str, Any]]


class TrendDataResponse(BaseModel):
    """Trend data response."""

    monthly_performance: List[Dict[str, Any]]
    growth_rates: Dict[str, float]


@router.get("/performance", response_model=List[SourcePerformanceResponse])
async def get_source_performance(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    source: Optional[str] = Query(None, description="Specific source to filter"),
    min_leads: int = Query(5, description="Minimum leads to include source"),
    sort_by: str = Query("roi", description="Sort by: roi, leads, revenue, conversion_rate"),
    order: str = Query("desc", description="Sort order: asc, desc"),
):
    """
    Get source performance metrics for the specified period.

    Returns performance data for all active lead sources with conversion rates,
    ROI, and other key metrics for Jorge's marketing optimization.
    """
    try:
        # Parse dates
        parsed_start = None
        parsed_end = None

        if start_date:
            parsed_start = datetime.fromisoformat(start_date)
        if end_date:
            parsed_end = datetime.fromisoformat(end_date)

        # Get performance data
        if source:
            # Single source performance
            try:
                lead_source = LeadSource(source)
                performance = await lead_source_tracker.get_source_performance(lead_source, parsed_start, parsed_end)
                performances = [performance] if performance else []
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid source: {source}")
        else:
            # All sources performance
            performances = await lead_source_tracker.get_all_source_performance(parsed_start, parsed_end, min_leads)

        # Convert to response format
        response_data = []
        for perf in performances:
            response_data.append(
                SourcePerformanceResponse(
                    source=perf.source.value,
                    total_leads=perf.total_leads,
                    qualified_leads=perf.qualified_leads,
                    hot_leads=perf.hot_leads,
                    conversion_rate=perf.conversion_rate,
                    qualification_rate=perf.qualification_rate,
                    total_revenue=perf.total_revenue,
                    avg_deal_size=perf.avg_deal_size,
                    cost_per_lead=perf.cost_per_lead,
                    cost_per_qualified_lead=perf.cost_per_qualified_lead,
                    roi=perf.roi,
                    avg_lead_score=perf.avg_lead_score,
                    avg_budget=perf.avg_budget,
                )
            )

        # Sort results
        sort_key_map = {
            "roi": lambda x: x.roi,
            "leads": lambda x: x.total_leads,
            "revenue": lambda x: x.total_revenue,
            "conversion_rate": lambda x: x.conversion_rate,
        }

        if sort_by in sort_key_map:
            response_data.sort(key=sort_key_map[sort_by], reverse=(order == "desc"))

        logger.info(f"Retrieved performance data for {len(response_data)} sources")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve performance data")


@router.get("/report", response_model=AttributionReportResponse)
async def generate_attribution_report(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    attribution_model: str = Query("last_touch", description="Attribution model"),
    include_forecasts: bool = Query(True, description="Include channel forecasts"),
    include_cohorts: bool = Query(True, description="Include cohort analysis"),
    background_tasks: BackgroundTasks = None,
):
    """
    Generate comprehensive attribution analysis report.

    Creates a complete report with source performance, alerts, recommendations,
    and advanced analytics for Jorge's marketing decision-making.
    """
    try:
        # Parse dates
        parsed_start = None
        parsed_end = None

        if start_date:
            parsed_start = datetime.fromisoformat(start_date)
        if end_date:
            parsed_end = datetime.fromisoformat(end_date)

        # Parse attribution model
        try:
            model = AttributionModel(attribution_model)
        except ValueError:
            model = AttributionModel.LAST_TOUCH

        # Generate report
        report = await attribution_analytics.generate_attribution_report(
            start_date=parsed_start,
            end_date=parsed_end,
            attribution_model=model,
            include_forecasts=include_forecasts,
            include_cohorts=include_cohorts,
        )

        # Convert to response format
        source_performances = []
        if report.source_performance:
            for perf in report.source_performance:
                source_performances.append(
                    SourcePerformanceResponse(
                        source=perf.source.value,
                        total_leads=perf.total_leads,
                        qualified_leads=perf.qualified_leads,
                        hot_leads=perf.hot_leads,
                        conversion_rate=perf.conversion_rate,
                        qualification_rate=perf.qualification_rate,
                        total_revenue=perf.total_revenue,
                        avg_deal_size=perf.avg_deal_size,
                        cost_per_lead=perf.cost_per_lead,
                        cost_per_qualified_lead=perf.cost_per_qualified_lead,
                        roi=perf.roi,
                        avg_lead_score=perf.avg_lead_score,
                        avg_budget=perf.avg_budget,
                    )
                )

        alerts = []
        if report.active_alerts:
            for alert in report.active_alerts:
                alerts.append(
                    AlertResponse(
                        alert_type=alert.alert_type.value,
                        source=alert.source.value,
                        severity=alert.severity,
                        title=alert.title,
                        description=alert.description,
                        current_value=alert.current_value,
                        previous_value=alert.previous_value,
                        change_percentage=alert.change_percentage,
                        recommendations=alert.recommendations,
                        created_at=alert.created_at,
                        expires_at=alert.expires_at,
                    )
                )

        response = AttributionReportResponse(
            period_start=report.period_start,
            period_end=report.period_end,
            generated_at=report.generated_at,
            total_leads=report.total_leads,
            total_qualified_leads=report.total_qualified_leads,
            total_revenue=report.total_revenue,
            total_cost=report.total_cost,
            overall_roi=report.overall_roi,
            source_performance=source_performances,
            active_alerts=alerts,
            optimization_recommendations=report.optimization_recommendations or [],
        )

        logger.info(f"Generated attribution report with {len(source_performances)} sources")
        return response

    except Exception as e:
        logger.error(f"Error generating attribution report: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate report")


@router.get("/weekly-summary", response_model=WeeklySummaryResponse)
async def get_weekly_summary(location_id: Optional[str] = Query(None, description="Location ID filter")):
    """
    Get weekly performance summary for Jorge's dashboard.

    Provides high-level metrics, top sources, biggest changes, and alerts
    for the current week compared to the previous week.
    """
    try:
        summary = await attribution_analytics.get_weekly_summary(location_id)

        if "error" in summary:
            raise HTTPException(status_code=500, detail=summary["error"])

        response = WeeklySummaryResponse(**summary)

        logger.info("Generated weekly attribution summary")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting weekly summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate weekly summary")


@router.get("/trends", response_model=TrendDataResponse)
async def get_monthly_trends():
    """
    Get monthly trend analysis for dashboard charts.

    Returns 6 months of historical performance data with growth rates
    for trend visualization in Jorge's marketing dashboard.
    """
    try:
        trends = await attribution_analytics.get_monthly_trends()

        if "error" in trends:
            raise HTTPException(status_code=500, detail=trends["error"])

        response = TrendDataResponse(**trends)

        logger.info("Generated monthly trends data")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monthly trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate trends")


@router.get("/alerts", response_model=List[AlertResponse])
async def get_active_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: low, medium, high, critical"),
    source: Optional[str] = Query(None, description="Filter by source"),
    limit: int = Query(20, description="Maximum alerts to return"),
):
    """
    Get active performance alerts for Jorge's monitoring dashboard.

    Returns current alerts for underperforming sources, ROI drops,
    cost spikes, and other issues requiring attention.
    """
    try:
        # Get current performance data to generate alerts
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        performances = await lead_source_tracker.get_all_source_performance(start_date, end_date, min_leads=1)

        # Generate alerts
        alerts = await attribution_analytics._generate_performance_alerts(performances)

        # Filter by severity
        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Filter by source
        if source:
            try:
                lead_source = LeadSource(source)
                alerts = [a for a in alerts if a.source == lead_source]
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid source: {source}")

        # Limit results
        alerts = alerts[:limit]

        # Convert to response format
        response_data = []
        for alert in alerts:
            response_data.append(
                AlertResponse(
                    alert_type=alert.alert_type.value,
                    source=alert.source.value,
                    severity=alert.severity,
                    title=alert.title,
                    description=alert.description,
                    current_value=alert.current_value,
                    previous_value=alert.previous_value,
                    change_percentage=alert.change_percentage,
                    recommendations=alert.recommendations,
                    created_at=alert.created_at,
                    expires_at=alert.expires_at,
                )
            )

        logger.info(f"Retrieved {len(response_data)} active alerts")
        return response_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")


@router.get("/recommendations")
async def get_optimization_recommendations():
    """
    Get optimization recommendations for Jorge's marketing strategy.

    Returns actionable insights for budget reallocation, source optimization,
    and campaign improvements based on current performance data.
    """
    try:
        recommendations = await lead_source_tracker.get_source_recommendations()

        logger.info(f"Generated {len(recommendations.get('recommendations', []))} optimization recommendations")
        return recommendations

    except Exception as e:
        logger.error(f"Error getting recommendations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to generate recommendations")


@router.get("/sources")
async def get_available_sources():
    """
    Get list of all available lead sources for filtering and configuration.

    Returns enumeration of all supported lead sources with their classifications
    for use in dashboard filters and campaign setup.
    """
    try:
        sources = []
        for source in LeadSource:
            sources.append(
                {
                    "value": source.value,
                    "display_name": source.value.replace("_", " ").title(),
                    "category": _get_source_category(source),
                }
            )

        return {
            "sources": sources,
            "categories": [
                "Digital Marketing",
                "Real Estate Platforms",
                "Referrals",
                "Direct",
                "Traditional",
                "Events",
                "Other",
            ],
        }

    except Exception as e:
        logger.error(f"Error getting sources: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get sources")


@router.post("/track-event")
async def track_attribution_event(source: str, event_type: str, metadata: Optional[Dict[str, Any]] = None):
    """
    Track attribution event for external system integration.

    Allows Jorge to manually track events from other systems (e.g., closed deals
    from CRM, marketing costs from ad platforms) for complete attribution analysis.
    """
    try:
        # Validate source
        try:
            lead_source = LeadSource(source)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid source: {source}")

        # Track the event
        await lead_source_tracker.track_source_performance(lead_source, event_type, metadata)

        logger.info(f"Tracked {event_type} event for {source}")
        return {
            "success": True,
            "message": f"Event {event_type} tracked for {source}",
            "timestamp": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to track event")


@router.get("/export/csv")
async def export_performance_csv(
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    sources: Optional[str] = Query(None, description="Comma-separated source list"),
):
    """
    Export performance data as CSV for Jorge's external analysis.

    Generates CSV download with source performance metrics for importing
    into spreadsheets or other analysis tools.
    """
    try:
        # Parse dates
        parsed_start = None
        parsed_end = None

        if start_date:
            parsed_start = datetime.fromisoformat(start_date)
        if end_date:
            parsed_end = datetime.fromisoformat(end_date)

        # Parse sources filter
        source_filter = []
        if sources:
            source_names = [s.strip() for s in sources.split(",")]
            for name in source_names:
                try:
                    source_filter.append(LeadSource(name))
                except ValueError:
                    pass  # Skip invalid sources

        # Get performance data
        performances = await lead_source_tracker.get_all_source_performance(parsed_start, parsed_end, min_leads=1)

        # Filter by sources if specified
        if source_filter:
            performances = [p for p in performances if p.source in source_filter]

        # Generate CSV content
        csv_lines = [
            "Source,Total Leads,Qualified Leads,Hot Leads,Conversion Rate,Qualification Rate,"
            "Total Revenue,Avg Deal Size,Cost Per Lead,Cost Per Qualified Lead,ROI,Avg Lead Score,Avg Budget"
        ]

        for perf in performances:
            csv_lines.append(
                f"{perf.source.value},{perf.total_leads},{perf.qualified_leads},"
                f"{perf.hot_leads},{perf.conversion_rate:.4f},{perf.qualification_rate:.4f},"
                f"{perf.total_revenue:.2f},{perf.avg_deal_size:.2f},{perf.cost_per_lead:.2f},"
                f"{perf.cost_per_qualified_lead:.2f},{perf.roi:.4f},{perf.avg_lead_score:.2f},"
                f"{perf.avg_budget:.2f}"
            )

        csv_content = "\n".join(csv_lines)

        logger.info(f"Generated CSV export with {len(performances)} sources")

        return {
            "content": csv_content,
            "filename": f"attribution_report_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv",
            "content_type": "text/csv",
        }

    except Exception as e:
        logger.error(f"Error exporting CSV: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to export CSV")


def _get_source_category(source: LeadSource) -> str:
    """Get category for a lead source."""
    digital_marketing = [
        LeadSource.FACEBOOK_ORGANIC,
        LeadSource.FACEBOOK_ADS,
        LeadSource.GOOGLE_ORGANIC,
        LeadSource.GOOGLE_ADS,
        LeadSource.INSTAGRAM_ORGANIC,
        LeadSource.INSTAGRAM_ADS,
        LeadSource.YOUTUBE,
        LeadSource.TIKTOK,
        LeadSource.LINKEDIN,
    ]

    real_estate_platforms = [
        LeadSource.ZILLOW,
        LeadSource.REALTOR_COM,
        LeadSource.TRULIA,
        LeadSource.REDFIN,
        LeadSource.HOMES_COM,
        LeadSource.MLS,
    ]

    referrals = [LeadSource.AGENT_REFERRAL, LeadSource.CLIENT_REFERRAL, LeadSource.VENDOR_REFERRAL]

    direct = [LeadSource.DIRECT, LeadSource.WEBSITE, LeadSource.PHONE_CALL, LeadSource.EMAIL, LeadSource.TEXT_MESSAGE]

    traditional = [LeadSource.PRINT_AD, LeadSource.RADIO, LeadSource.TV, LeadSource.BILLBOARD, LeadSource.DIRECT_MAIL]

    events = [LeadSource.OPEN_HOUSE, LeadSource.NETWORKING_EVENT, LeadSource.TRADE_SHOW]

    if source in digital_marketing:
        return "Digital Marketing"
    elif source in real_estate_platforms:
        return "Real Estate Platforms"
    elif source in referrals:
        return "Referrals"
    elif source in direct:
        return "Direct"
    elif source in traditional:
        return "Traditional"
    elif source in events:
        return "Events"
    else:
        return "Other"
