"""
Jorge's Real Estate AI Platform - Client Demonstration API
Professional client demo environment management with ROI calculations
Version: 2.0.0
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from ...middleware.rate_limiting import rate_limit
from ...services.authentication import get_current_user, verify_admin_access
from ...services.client_demo_service import ClientDemoService, DemoScenario

logger = logging.getLogger(__name__)

# Initialize router with tags and metadata for OpenAPI documentation
router = APIRouter(
    prefix="/api/v1/client-demonstrations", tags=["Client Demonstrations"], dependencies=[Depends(get_current_user)]
)

# Initialize demo service
demo_service = ClientDemoService()


# ================================================================
# PYDANTIC MODELS FOR API
# ================================================================


class DemoSessionRequest(BaseModel):
    """Request model for creating a new demo session"""

    scenario: DemoScenario = Field(..., description="Demo scenario type")
    client_name: Optional[str] = Field(None, description="Custom client name")
    agency_name: Optional[str] = Field(None, description="Custom agency name")
    custom_params: Optional[Dict[str, Any]] = Field(None, description="Custom parameters to override defaults")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "scenario": "luxury_agent",
                "client_name": "Patricia Williams",
                "agency_name": "Elite Properties Group",
                "custom_params": {"monthly_leads": 30, "avg_deal_size": 950000},
            }
        }
    )


class DemoSessionResponse(BaseModel):
    """Response model for demo session data"""

    session_id: str
    client_profile: Dict[str, Any]
    demo_leads: List[Dict[str, Any]]
    demo_properties: List[Dict[str, Any]]
    demo_conversations: List[Dict[str, Any]]
    roi_calculation: Dict[str, Any]
    performance_metrics: Dict[str, Any]
    created_at: str
    expires_at: str
    status: str = "active"


class SessionExtendRequest(BaseModel):
    """Request model for extending session duration"""

    additional_hours: int = Field(default=1, ge=1, le=24, description="Hours to extend (1-24)")


class ROICalculationResponse(BaseModel):
    """Response model for ROI calculations"""

    scenario: str
    time_horizon_months: int
    traditional_costs: Dict[str, Any]
    jorge_costs: Dict[str, Any]
    jorge_benefits: Dict[str, Any]
    summary: Dict[str, Any]
    calculation_timestamp: str


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""

    response_times: Dict[str, str]
    conversion_rates: Dict[str, str]
    accuracy_scores: Dict[str, str]
    monthly_performance: Dict[str, Any]
    operational_efficiency: Dict[str, Any]
    client_satisfaction: Dict[str, Any]
    business_impact: Dict[str, str]


# ================================================================
# DEMO SESSION MANAGEMENT ENDPOINTS
# ================================================================


@router.post("/sessions", response_model=DemoSessionResponse)
@rate_limit(requests=10, window=60)  # 10 demo sessions per minute
async def create_demo_session(request: DemoSessionRequest, current_user: dict = Depends(get_current_user)):
    """
    Create a new client demonstration session with realistic data

    Creates a complete demo environment including:
    - Client profile based on market scenario
    - Realistic lead data with conversation history
    - Property inventory with matching algorithms
    - ROI calculations showing Jorge AI benefits
    - Performance metrics demonstrating improvements

    **Demo Scenarios:**
    - `luxury_agent`: High-value properties ($1M+), sophisticated clients
    - `mid_market`: Standard residential ($300-600K), typical families
    - `first_time_buyer`: Entry-level properties, educational focus
    - `investor_focused`: Investment properties, ROI emphasis
    - `high_volume`: Large-scale operations, efficiency focus
    """
    try:
        # Initialize demo service if needed
        await demo_service.initialize()

        # Create demo session
        demo_env = await demo_service.create_demo_session(
            scenario=request.scenario,
            client_name=request.client_name,
            agency_name=request.agency_name,
            custom_params=request.custom_params,
        )

        # Convert to response format
        response = DemoSessionResponse(
            session_id=demo_env.session_id,
            client_profile=demo_env.client_profile.__dict__,
            demo_leads=demo_env.demo_leads,
            demo_properties=demo_env.demo_properties,
            demo_conversations=demo_env.demo_conversations,
            roi_calculation=demo_env.roi_calculation,
            performance_metrics=demo_env.performance_metrics,
            created_at=demo_env.created_at.isoformat(),
            expires_at=demo_env.expires_at.isoformat(),
        )

        logger.info(
            f"Created demo session {demo_env.session_id} for user {current_user.get('id')} "
            f"with scenario {request.scenario.value}"
        )

        return response

    except Exception as e:
        logger.error(f"Error creating demo session: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}", response_model=DemoSessionResponse)
@rate_limit(requests=60, window=60)  # 60 requests per minute for session access
async def get_demo_session(
    session_id: str = Path(..., description="Demo session ID"), current_user: dict = Depends(get_current_user)
):
    """
    Retrieve existing demo session data

    Returns complete demo environment including all generated data,
    ROI calculations, and performance metrics. Sessions expire after
    2 hours and are automatically cleaned up.
    """
    try:
        await demo_service.initialize()
        demo_env = await demo_service.get_demo_session(session_id)

        if not demo_env:
            raise HTTPException(status_code=404, detail="Demo session not found or has expired")

        response = DemoSessionResponse(
            session_id=demo_env.session_id,
            client_profile=demo_env.client_profile.__dict__,
            demo_leads=demo_env.demo_leads,
            demo_properties=demo_env.demo_properties,
            demo_conversations=demo_env.demo_conversations,
            roi_calculation=demo_env.roi_calculation,
            performance_metrics=demo_env.performance_metrics,
            created_at=demo_env.created_at.isoformat(),
            expires_at=demo_env.expires_at.isoformat(),
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving demo session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/extend")
@rate_limit(requests=10, window=60)
async def extend_demo_session(
    session_id: str = Path(..., description="Demo session ID"),
    request: SessionExtendRequest = SessionExtendRequest(),
    current_user: dict = Depends(get_current_user),
):
    """
    Extend demo session duration

    Extends the expiration time for an active demo session.
    Useful for longer client presentations or follow-up meetings.
    """
    try:
        await demo_service.initialize()
        success = await demo_service.extend_demo_session(session_id, request.additional_hours)

        if not success:
            raise HTTPException(status_code=404, detail="Demo session not found or has expired")

        return JSONResponse(
            {
                "status": "success",
                "message": f"Session extended by {request.additional_hours} hours",
                "session_id": session_id,
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extending demo session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/sessions/{session_id}/reset", response_model=DemoSessionResponse)
@rate_limit(requests=5, window=60)
async def reset_demo_session(
    session_id: str = Path(..., description="Demo session ID"), current_user: dict = Depends(get_current_user)
):
    """
    Reset demo session with fresh data

    Creates new demo data while preserving the client profile.
    Useful for multiple demonstrations with the same scenario
    but fresh examples.
    """
    try:
        await demo_service.initialize()
        demo_env = await demo_service.reset_demo_session(session_id)

        response = DemoSessionResponse(
            session_id=demo_env.session_id,
            client_profile=demo_env.client_profile.__dict__,
            demo_leads=demo_env.demo_leads,
            demo_properties=demo_env.demo_properties,
            demo_conversations=demo_env.demo_conversations,
            roi_calculation=demo_env.roi_calculation,
            performance_metrics=demo_env.performance_metrics,
            created_at=demo_env.created_at.isoformat(),
            expires_at=demo_env.expires_at.isoformat(),
        )

        logger.info(f"Reset demo session {session_id} for user {current_user.get('id')}")
        return response

    except Exception as e:
        logger.error(f"Error resetting demo session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/sessions/{session_id}")
@rate_limit(requests=20, window=60)
async def cleanup_demo_session(
    session_id: str = Path(..., description="Demo session ID"), current_user: dict = Depends(get_current_user)
):
    """
    Manually cleanup demo session

    Immediately removes demo session and all associated data.
    Sessions are automatically cleaned up after expiration,
    but this allows manual cleanup when done with demonstration.
    """
    try:
        await demo_service.initialize()
        success = await demo_service.cleanup_demo_session(session_id)

        if not success:
            raise HTTPException(status_code=404, detail="Demo session not found")

        return JSONResponse(
            {"status": "success", "message": "Demo session cleaned up successfully", "session_id": session_id}
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning up demo session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ================================================================
# ROI AND ANALYTICS ENDPOINTS
# ================================================================


@router.get("/sessions/{session_id}/roi", response_model=ROICalculationResponse)
@rate_limit(requests=60, window=60)
async def get_roi_calculation(
    session_id: str = Path(..., description="Demo session ID"), current_user: dict = Depends(get_current_user)
):
    """
    Get detailed ROI calculation for demo session

    Returns comprehensive ROI analysis comparing traditional methods
    vs Jorge AI platform, including:
    - Cost breakdowns for both approaches
    - Benefit calculations with conservative estimates
    - Net savings and ROI percentages
    - Payback period analysis
    """
    try:
        await demo_service.initialize()
        demo_env = await demo_service.get_demo_session(session_id)

        if not demo_env:
            raise HTTPException(status_code=404, detail="Demo session not found or has expired")

        roi_calculation = demo_env.roi_calculation
        roi_calculation["calculation_timestamp"] = datetime.utcnow().isoformat()

        return ROICalculationResponse(**roi_calculation)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting ROI calculation for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/sessions/{session_id}/performance", response_model=PerformanceMetricsResponse)
@rate_limit(requests=60, window=60)
async def get_performance_metrics(
    session_id: str = Path(..., description="Demo session ID"), current_user: dict = Depends(get_current_user)
):
    """
    Get performance metrics for demo session

    Returns detailed performance comparison between traditional
    methods and Jorge AI platform across key metrics:
    - Response times (traditional vs Jorge)
    - Conversion rates and improvements
    - Accuracy scores and quality metrics
    - Operational efficiency gains
    - Client satisfaction improvements
    """
    try:
        await demo_service.initialize()
        demo_env = await demo_service.get_demo_session(session_id)

        if not demo_env:
            raise HTTPException(status_code=404, detail="Demo session not found or has expired")

        return PerformanceMetricsResponse(**demo_env.performance_metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting performance metrics for {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ================================================================
# DEMONSTRATION UTILITIES
# ================================================================


@router.get("/scenarios")
async def get_available_scenarios(current_user: dict = Depends(get_current_user)):
    """
    Get list of available demonstration scenarios

    Returns all supported demo scenarios with descriptions
    and typical use cases for client presentations.
    """
    scenarios = {
        "luxury_agent": {
            "name": "Luxury Real Estate Agent",
            "description": "High-end properties ($1M+) with sophisticated clientele",
            "typical_deal_size": "$850K - $3.5M",
            "monthly_leads": "20-30",
            "focus": "White-glove service, immediate response, luxury amenities",
            "roi_highlights": "Premium service scaling, higher conversion rates",
        },
        "mid_market": {
            "name": "Mid-Market Residential Agent",
            "description": "Standard residential properties with typical families",
            "typical_deal_size": "$300K - $600K",
            "monthly_leads": "40-50",
            "focus": "Efficiency, consistency, good school districts",
            "roi_highlights": "Volume scaling, process automation",
        },
        "first_time_buyer": {
            "name": "First-Time Buyer Specialist",
            "description": "Entry-level properties with extensive buyer education",
            "typical_deal_size": "$250K - $400K",
            "monthly_leads": "50-70",
            "focus": "Education, guidance, financing assistance",
            "roi_highlights": "Streamlined education, faster closings",
        },
        "investor_focused": {
            "name": "Investment Property Specialist",
            "description": "Investment properties with ROI-focused analysis",
            "typical_deal_size": "$500K - $2M",
            "monthly_leads": "25-40",
            "focus": "Market analysis, ROI calculations, portfolio growth",
            "roi_highlights": "Instant analysis, faster deal velocity",
        },
        "high_volume": {
            "name": "High-Volume Operations",
            "description": "Large-scale operations focusing on efficiency",
            "typical_deal_size": "$300K - $500K",
            "monthly_leads": "100-150",
            "focus": "Scale, automation, team coordination",
            "roi_highlights": "Massive efficiency gains, quality at scale",
        },
    }

    return JSONResponse({"scenarios": scenarios, "total_available": len(scenarios)})


@router.post("/sessions/cleanup-expired")
@rate_limit(requests=5, window=300)  # 5 requests per 5 minutes
async def cleanup_expired_sessions(
    current_user: dict = Depends(verify_admin_access),  # Admin only
):
    """
    Cleanup all expired demo sessions

    Administrative endpoint to manually trigger cleanup of
    expired demo sessions. Normally handled automatically,
    but useful for maintenance or troubleshooting.
    """
    try:
        await demo_service.initialize()
        expired_count = await demo_service.cleanup_expired_sessions()

        return JSONResponse(
            {
                "status": "success",
                "message": f"Cleaned up {expired_count} expired sessions",
                "expired_sessions_removed": expired_count,
            }
        )

    except Exception as e:
        logger.error(f"Error during expired session cleanup: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ================================================================
# HEALTH AND STATUS ENDPOINTS
# ================================================================


@router.get("/health")
async def demo_service_health():
    """
    Check demo service health status

    Returns status of demo service components including
    Redis connectivity and session management capabilities.
    """
    try:
        await demo_service.initialize()

        # Test Redis connectivity
        test_session = await demo_service.get_demo_session("health-check-test")

        return JSONResponse(
            {
                "status": "healthy",
                "service": "client_demonstrations",
                "redis_connected": True,
                "timestamp": datetime.utcnow().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Demo service health check failed: {str(e)}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "service": "client_demonstrations",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
