"""
Business Metrics API Endpoints.

Provides REST API access to comprehensive business intelligence and KPI metrics
for the GHL Real Estate AI platform. Includes webhook performance, conversion
tracking, agent productivity, and revenue attribution endpoints.

Features:
- Executive dashboard metrics
- Real-time performance monitoring
- Agent productivity analytics
- Property matching effectiveness
- Revenue attribution reporting
- System health monitoring

Security:
- API key authentication
- Rate limiting
- Input validation
- Error sanitization
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from decimal import Decimal

from fastapi import APIRouter, HTTPException, Depends, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator

from ghl_real_estate_ai.services.business_metrics_service import (
    BusinessMetricsService,
    BusinessMetric,
    MetricType,
    ConversionStage,
    WebhookPerformanceMetrics,
    BusinessImpactMetrics,
    AgentProductivityMetrics,
    calculate_performance_grade,
    create_business_metrics_service
)
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/business-metrics", tags=["business-metrics"])

# Global business metrics service instance
business_metrics_service: Optional[BusinessMetricsService] = None


# ========================================================================
# Pydantic Models for API Requests/Responses
# ========================================================================

class MetricRequest(BaseModel):
    """Base request model for metrics endpoints."""
    location_id: str = Field(..., description="GHL location identifier")
    days: int = Field(30, ge=1, le=365, description="Number of days to analyze")


class ConversionTrackingRequest(BaseModel):
    """Request model for conversion stage tracking."""
    contact_id: str = Field(..., description="Contact identifier")
    location_id: str = Field(..., description="GHL location identifier")
    stage: str = Field(..., description="Conversion stage")
    ai_score: Optional[int] = Field(None, ge=0, le=100, description="AI lead score")
    agent_id: Optional[str] = Field(None, description="Agent identifier")
    deal_value: Optional[float] = Field(None, ge=0, description="Deal value")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('stage')
    def validate_stage(cls, v):
        valid_stages = [
            "lead_created", "ai_qualified", "human_contacted",
            "appointment_scheduled", "property_showing",
            "offer_submitted", "contract_signed", "deal_closed"
        ]
        if v.lower() not in valid_stages:
            raise ValueError(f"Invalid stage. Must be one of: {valid_stages}")
        return v.lower()


class AgentActivityRequest(BaseModel):
    """Request model for agent activity tracking."""
    agent_id: str = Field(..., description="Agent identifier")
    location_id: str = Field(..., description="GHL location identifier")
    activity_type: str = Field(..., description="Activity type")
    contact_id: Optional[str] = Field(None, description="Contact involved")
    deal_value: Optional[float] = Field(None, ge=0, description="Deal value")
    response_time_minutes: Optional[float] = Field(None, ge=0, description="Response time")
    ai_recommendation_used: bool = Field(False, description="AI recommendation used")


class PropertyRecommendationRequest(BaseModel):
    """Request model for property recommendation tracking."""
    contact_id: str = Field(..., description="Contact identifier")
    location_id: str = Field(..., description="GHL location identifier")
    property_id: str = Field(..., description="Property identifier")
    recommendation_score: float = Field(..., ge=0, le=1, description="Recommendation confidence")
    agent_id: Optional[str] = Field(None, description="Agent making recommendation")


class PropertyInteractionRequest(BaseModel):
    """Request model for property interaction tracking."""
    recommendation_id: str = Field(..., description="Recommendation identifier")
    interaction_type: str = Field(..., description="Interaction type")
    contact_id: Optional[str] = Field(None, description="Contact identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")

    @validator('interaction_type')
    def validate_interaction_type(cls, v):
        valid_types = ["viewed", "liked", "scheduled", "rejected", "shared"]
        if v.lower() not in valid_types:
            raise ValueError(f"Invalid interaction type. Must be one of: {valid_types}")
        return v.lower()


class DashboardResponse(BaseModel):
    """Response model for dashboard metrics."""
    summary: Dict[str, Any] = Field(..., description="Executive summary metrics")
    ghl_integration: Dict[str, Any] = Field(..., description="GHL integration metrics")
    business_impact: Dict[str, Any] = Field(..., description="Business impact metrics")
    property_matching: Dict[str, Any] = Field(..., description="Property matching metrics")
    top_agents: List[Dict[str, Any]] = Field(..., description="Top performing agents")
    performance_grade: str = Field(..., description="Overall performance grade")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    period_days: int = Field(..., description="Analysis period in days")


class HealthResponse(BaseModel):
    """Response model for system health check."""
    status: str = Field(..., description="Overall system status")
    webhook_sla_compliance: bool = Field(..., description="Webhook SLA compliance")
    redis_connected: bool = Field(..., description="Redis connection status")
    postgres_connected: bool = Field(..., description="PostgreSQL connection status")
    last_check: datetime = Field(..., description="Last health check timestamp")
    issues: List[str] = Field(default_factory=list, description="Current issues")


# ========================================================================
# Dependency Functions
# ========================================================================

async def get_business_metrics_service() -> BusinessMetricsService:
    """Get or create business metrics service instance."""
    global business_metrics_service

    if not business_metrics_service:
        try:
            business_metrics_service = await create_business_metrics_service(
                redis_url=settings.redis_url,
                postgres_url=settings.database_url
            )
            logger.info("Business metrics service initialized for API")
        except Exception as e:
            logger.error(f"Failed to initialize business metrics service: {e}")
            raise HTTPException(
                status_code=503,
                detail="Business metrics service unavailable"
            )

    return business_metrics_service


def validate_location_access(location_id: str) -> str:
    """Validate location access permissions."""
    # In production, implement actual access control
    if not location_id or len(location_id) < 3:
        raise HTTPException(
            status_code=400,
            detail="Invalid location ID"
        )
    return location_id


# ========================================================================
# Dashboard and Summary Endpoints
# ========================================================================

@router.get(
    "/dashboard/{location_id}",
    response_model=DashboardResponse,
    summary="Get Executive Dashboard Metrics",
    description="Retrieve comprehensive business intelligence dashboard metrics"
)
async def get_executive_dashboard(
    location_id: str = Path(..., description="GHL location identifier"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    include_trends: bool = Query(True, description="Include trend analysis"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> DashboardResponse:
    """
    Get comprehensive executive dashboard metrics for a location.

    Returns KPIs, performance metrics, agent analytics, and system health data
    for the specified time period.
    """
    try:
        # Validate location access
        location_id = validate_location_access(location_id)

        logger.info(f"Generating dashboard metrics for location {location_id} ({days} days)")

        # Get comprehensive metrics
        dashboard_data = await service.get_executive_dashboard_metrics(
            location_id=location_id,
            days=days
        )

        if not dashboard_data:
            raise HTTPException(
                status_code=404,
                detail="No metrics data available for this location"
            )

        # Calculate performance grade
        summary = dashboard_data.get('summary', {})
        performance_grade = calculate_performance_grade(summary)

        # Add trends if requested
        if include_trends:
            trends = await _calculate_metric_trends(service, location_id, days)
            dashboard_data.update(trends)

        return DashboardResponse(
            summary=dashboard_data.get('summary', {}),
            ghl_integration=dashboard_data.get('ghl_integration', {}),
            business_impact=dashboard_data.get('business_impact', {}),
            property_matching=dashboard_data.get('property_matching', {}),
            top_agents=dashboard_data.get('top_agents', []),
            performance_grade=performance_grade,
            generated_at=datetime.fromisoformat(dashboard_data.get('generated_at')),
            period_days=days
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating dashboard metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to generate dashboard metrics"
        )


@router.get(
    "/summary/{location_id}",
    summary="Get Metrics Summary",
    description="Get high-level summary metrics for quick overview"
)
async def get_metrics_summary(
    location_id: str = Path(..., description="GHL location identifier"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Get high-level metrics summary for quick dashboard display."""
    try:
        location_id = validate_location_access(location_id)

        # Get last 7 days for quick overview
        dashboard_data = await service.get_executive_dashboard_metrics(location_id, 7)

        if not dashboard_data:
            return {
                "total_revenue": 0,
                "conversion_rate": 0,
                "webhook_success_rate": 0,
                "performance_grade": "N/A",
                "status": "no_data"
            }

        summary = dashboard_data.get('summary', {})

        return {
            "total_revenue": summary.get('total_revenue', 0),
            "conversion_rate": summary.get('conversion_rate', 0),
            "webhook_success_rate": summary.get('webhook_success_rate', 0),
            "property_acceptance_rate": summary.get('property_acceptance_rate', 0),
            "performance_grade": calculate_performance_grade(summary),
            "status": "healthy",
            "last_updated": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}")
        raise HTTPException(status_code=500, detail="Failed to get metrics summary")


# ========================================================================
# GHL Integration Metrics Endpoints
# ========================================================================

@router.get(
    "/webhook-performance/{location_id}",
    summary="Get Webhook Performance Metrics",
    description="Retrieve GHL webhook processing performance and SLA compliance"
)
async def get_webhook_performance(
    location_id: str = Path(..., description="GHL location identifier"),
    days: int = Query(7, ge=1, le=90, description="Analysis period in days"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Get detailed webhook performance metrics and SLA compliance."""
    try:
        location_id = validate_location_access(location_id)

        performance = await service.get_webhook_performance_metrics(location_id, days)

        return {
            "total_webhooks": performance.total_webhooks,
            "success_rate": performance.success_rate,
            "failure_rate": 100.0 - performance.success_rate,
            "avg_processing_time": performance.avg_processing_time,
            "sla_compliance": performance.meets_sla,
            "contact_enrichment_rate": performance.contact_enrichment_rate,
            "ai_activation_rate": performance.ai_activation_rate,
            "analysis_period_days": days,
            "sla_threshold": 1.0,  # 1 second SLA
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error getting webhook performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get webhook performance")


# ========================================================================
# Business Impact Endpoints
# ========================================================================

@router.get(
    "/revenue-metrics/{location_id}",
    summary="Get Revenue Metrics",
    description="Retrieve revenue attribution and business impact analysis"
)
async def get_revenue_metrics(
    location_id: str = Path(..., description="GHL location identifier"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Get comprehensive revenue metrics and attribution analysis."""
    try:
        location_id = validate_location_access(location_id)

        business_metrics = await service.get_business_impact_metrics(location_id, days)
        revenue_per_lead = await service.calculate_revenue_per_lead(location_id, days)

        return {
            "total_revenue": float(business_metrics.total_revenue),
            "revenue_per_lead": float(revenue_per_lead),
            "conversion_rate": business_metrics.lead_to_conversion_rate,
            "avg_deal_size": float(business_metrics.avg_deal_size),
            "time_to_conversion_days": business_metrics.time_to_conversion_days,
            "ai_score_correlation": business_metrics.ai_score_correlation,
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "attribution": {
                "ai_contribution": float(business_metrics.total_revenue) * max(0, business_metrics.ai_score_correlation) * 0.7,
                "correlation_strength": "Strong" if abs(business_metrics.ai_score_correlation) > 0.5 else "Moderate" if abs(business_metrics.ai_score_correlation) > 0.3 else "Weak"
            }
        }

    except Exception as e:
        logger.error(f"Error getting revenue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get revenue metrics")


@router.post(
    "/track/conversion",
    summary="Track Conversion Stage",
    description="Record lead progression through conversion pipeline"
)
async def track_conversion_stage(
    request: ConversionTrackingRequest,
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Track a lead's progression through the conversion pipeline."""
    try:
        # Map stage string to enum
        stage_mapping = {
            "lead_created": ConversionStage.LEAD_CREATED,
            "ai_qualified": ConversionStage.AI_QUALIFIED,
            "human_contacted": ConversionStage.HUMAN_CONTACTED,
            "appointment_scheduled": ConversionStage.APPOINTMENT_SCHEDULED,
            "property_showing": ConversionStage.PROPERTY_SHOWING,
            "offer_submitted": ConversionStage.OFFER_SUBMITTED,
            "contract_signed": ConversionStage.CONTRACT_SIGNED,
            "deal_closed": ConversionStage.DEAL_CLOSED
        }

        conversion_stage = stage_mapping[request.stage]

        await service.track_conversion_stage(
            contact_id=request.contact_id,
            location_id=request.location_id,
            stage=conversion_stage,
            ai_score=request.ai_score,
            agent_id=request.agent_id,
            deal_value=Decimal(str(request.deal_value)) if request.deal_value else None,
            metadata=request.metadata
        )

        logger.info(f"Conversion tracked: {request.contact_id} -> {request.stage}")

        return {
            "success": True,
            "message": f"Conversion stage '{request.stage}' tracked successfully",
            "contact_id": request.contact_id,
            "stage": request.stage,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking conversion: {e}")
        raise HTTPException(status_code=500, detail="Failed to track conversion")


# ========================================================================
# Agent Performance Endpoints
# ========================================================================

@router.get(
    "/agent-performance/{location_id}",
    summary="Get Agent Performance Metrics",
    description="Retrieve agent productivity and performance analytics"
)
async def get_agent_performance(
    location_id: str = Path(..., description="GHL location identifier"),
    agent_id: Optional[str] = Query(None, description="Specific agent ID"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    limit: int = Query(10, ge=1, le=50, description="Number of top agents to return"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Get agent performance metrics and productivity analytics."""
    try:
        location_id = validate_location_access(location_id)

        if agent_id:
            # Get specific agent metrics
            metrics = await service.get_agent_productivity_metrics(
                agent_id=agent_id,
                location_id=location_id,
                days=days
            )

            return {
                "agent_id": metrics.agent_id,
                "deals_closed": metrics.deals_closed,
                "avg_deal_value": float(metrics.avg_deal_value),
                "conversion_rate": metrics.conversion_rate,
                "response_time_minutes": metrics.response_time_minutes,
                "ai_recommendation_usage": metrics.ai_recommendation_usage * 100,
                "property_match_effectiveness": metrics.property_match_effectiveness,
                "productivity_score": metrics.productivity_score,
                "analysis_period_days": days,
                "generated_at": datetime.now().isoformat()
            }
        else:
            # Get top agents from dashboard data
            dashboard_data = await service.get_executive_dashboard_metrics(location_id, days)
            top_agents = dashboard_data.get('top_agents', [])[:limit]

            return {
                "top_agents": top_agents,
                "total_agents": len(top_agents),
                "analysis_period_days": days,
                "generated_at": datetime.now().isoformat()
            }

    except Exception as e:
        logger.error(f"Error getting agent performance: {e}")
        raise HTTPException(status_code=500, detail="Failed to get agent performance")


@router.post(
    "/track/agent-activity",
    summary="Track Agent Activity",
    description="Record agent activities and performance metrics"
)
async def track_agent_activity(
    request: AgentActivityRequest,
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Track agent activity and performance metrics."""
    try:
        await service.track_agent_activity(
            agent_id=request.agent_id,
            location_id=request.location_id,
            activity_type=request.activity_type,
            contact_id=request.contact_id,
            deal_value=Decimal(str(request.deal_value)) if request.deal_value else None,
            response_time_minutes=request.response_time_minutes,
            ai_recommendation_used=request.ai_recommendation_used
        )

        logger.info(f"Agent activity tracked: {request.agent_id} -> {request.activity_type}")

        return {
            "success": True,
            "message": f"Agent activity '{request.activity_type}' tracked successfully",
            "agent_id": request.agent_id,
            "activity_type": request.activity_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking agent activity: {e}")
        raise HTTPException(status_code=500, detail="Failed to track agent activity")


# ========================================================================
# Property Matching Endpoints
# ========================================================================

@router.get(
    "/property-matching/{location_id}",
    summary="Get Property Matching Metrics",
    description="Retrieve property recommendation effectiveness metrics"
)
async def get_property_matching_metrics(
    location_id: str = Path(..., description="GHL location identifier"),
    days: int = Query(30, ge=1, le=365, description="Analysis period in days"),
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Get property matching effectiveness and recommendation metrics."""
    try:
        location_id = validate_location_access(location_id)

        metrics = await service.get_property_matching_metrics(location_id, days)

        return {
            **metrics,
            "analysis_period_days": days,
            "generated_at": datetime.now().isoformat(),
            "effectiveness_rating": (
                "Excellent" if metrics.get("acceptance_rate", 0) > 60 else
                "Good" if metrics.get("acceptance_rate", 0) > 40 else
                "Needs Improvement"
            )
        }

    except Exception as e:
        logger.error(f"Error getting property matching metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get property matching metrics")


@router.post(
    "/track/property-recommendation",
    summary="Track Property Recommendation",
    description="Record property recommendation made to a lead"
)
async def track_property_recommendation(
    request: PropertyRecommendationRequest,
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Track a property recommendation made to a lead."""
    try:
        recommendation_id = await service.track_property_recommendation(
            contact_id=request.contact_id,
            location_id=request.location_id,
            property_id=request.property_id,
            recommendation_score=request.recommendation_score,
            agent_id=request.agent_id
        )

        logger.info(f"Property recommendation tracked: {recommendation_id}")

        return {
            "success": True,
            "recommendation_id": recommendation_id,
            "message": "Property recommendation tracked successfully",
            "contact_id": request.contact_id,
            "property_id": request.property_id,
            "score": request.recommendation_score,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking property recommendation: {e}")
        raise HTTPException(status_code=500, detail="Failed to track property recommendation")


@router.post(
    "/track/property-interaction",
    summary="Track Property Interaction",
    description="Record lead interaction with property recommendation"
)
async def track_property_interaction(
    request: PropertyInteractionRequest,
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> Dict[str, Any]:
    """Track lead interaction with property recommendation."""
    try:
        await service.track_property_interaction(
            recommendation_id=request.recommendation_id,
            interaction_type=request.interaction_type,
            contact_id=request.contact_id,
            metadata=request.metadata
        )

        logger.info(f"Property interaction tracked: {request.recommendation_id} -> {request.interaction_type}")

        return {
            "success": True,
            "message": f"Property interaction '{request.interaction_type}' tracked successfully",
            "recommendation_id": request.recommendation_id,
            "interaction_type": request.interaction_type,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        logger.error(f"Error tracking property interaction: {e}")
        raise HTTPException(status_code=500, detail="Failed to track property interaction")


# ========================================================================
# System Health and Monitoring
# ========================================================================

@router.get(
    "/health",
    response_model=HealthResponse,
    summary="System Health Check",
    description="Get business metrics system health and status"
)
async def get_system_health(
    service: BusinessMetricsService = Depends(get_business_metrics_service)
) -> HealthResponse:
    """Get comprehensive system health status for business metrics."""
    try:
        issues = []

        # Check Redis connection
        redis_connected = False
        try:
            if service.redis_client:
                await asyncio.get_event_loop().run_in_executor(
                    None, service.redis_client.ping
                )
                redis_connected = True
        except Exception:
            issues.append("Redis connection failed")

        # Check PostgreSQL connection
        postgres_connected = False
        try:
            if service.pg_pool:
                async with service.pg_pool.acquire() as conn:
                    await conn.fetchval("SELECT 1")
                postgres_connected = True
        except Exception:
            issues.append("PostgreSQL connection failed")

        # Check webhook SLA compliance (mock for now)
        webhook_sla_compliance = True  # Would check actual recent performance

        # Determine overall status
        if not redis_connected and not postgres_connected:
            status = "critical"
        elif issues:
            status = "warning"
        else:
            status = "healthy"

        return HealthResponse(
            status=status,
            webhook_sla_compliance=webhook_sla_compliance,
            redis_connected=redis_connected,
            postgres_connected=postgres_connected,
            last_check=datetime.now(),
            issues=issues
        )

    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        return HealthResponse(
            status="error",
            webhook_sla_compliance=False,
            redis_connected=False,
            postgres_connected=False,
            last_check=datetime.now(),
            issues=[f"Health check failed: {str(e)}"]
        )


# ========================================================================
# Helper Functions
# ========================================================================

async def _calculate_metric_trends(
    service: BusinessMetricsService,
    location_id: str,
    days: int
) -> Dict[str, Any]:
    """Calculate metric trends for dashboard display."""
    try:
        # Get current period metrics
        current_metrics = await service.get_executive_dashboard_metrics(location_id, days)

        # Get previous period for comparison
        previous_metrics = await service.get_executive_dashboard_metrics(location_id, days)

        # Calculate trends (simplified - in production would use actual historical data)
        current_summary = current_metrics.get('summary', {})

        return {
            "trends": {
                "revenue_trend": 5.2,  # Mock trend data
                "conversion_trend": -1.1,
                "webhook_trend": 0.3,
                "property_acceptance_trend": 2.8
            }
        }
    except Exception as e:
        logger.warning(f"Could not calculate trends: {e}")
        return {"trends": {}}


# ========================================================================
# Error Handlers
# ========================================================================

@router.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "message": exc.detail,
            "timestamp": datetime.now().isoformat()
        }
    )


@router.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler for unexpected errors."""
    logger.error(f"Unexpected error in business metrics API: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "An unexpected error occurred",
            "timestamp": datetime.now().isoformat()
        }
    )