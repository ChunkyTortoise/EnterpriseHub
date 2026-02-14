"""
Client Experience API Routes - Track B Phase 1 Endpoints

Client Journey Mapping and Experience Optimization endpoints:
- Client journey stage tracking and health monitoring
- Milestone progression management
- Journey personalization and optimization
- Real-time experience analytics
- AI-powered journey recommendations

Follows established architecture patterns:
- FastAPI route structure with /api/v1 prefix
- Multi-tenant isolation via location_id
- Pydantic models for validation
- Event publishing and memory service integration
"""

from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, HTTPException, Path, Query
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.client_journey_mapping import (
    JourneyStage,
    MilestoneType,
    get_client_journey_mapping,
)

logger = get_logger(__name__)
router = APIRouter(prefix="/api/v1/client-experience", tags=["Client Experience"])

# Request/Response Models


class JourneyTrackingRequest(BaseModel):
    """Request for client journey tracking."""

    client_id: str = Field(..., description="Client identifier")
    current_stage: str = Field(..., description="Current journey stage")
    context_data: Optional[Dict[str, Any]] = Field(None, description="Additional context")


class MilestoneProgressRequest(BaseModel):
    """Request for milestone progression."""

    client_id: str = Field(..., description="Client identifier")
    milestone_type: str = Field(..., description="Type of milestone to progress")
    completion_data: Optional[Dict[str, Any]] = Field(None, description="Completion details")


class JourneyPersonalizationRequest(BaseModel):
    """Request for journey personalization update."""

    client_id: str = Field(..., description="Client identifier")
    preferences: Dict[str, Any] = Field(..., description="Personalization preferences")


class StandardResponse(BaseModel):
    """Standard API response format."""

    success: bool
    data: Optional[Dict[str, Any]] = None
    processing_time_ms: float
    error: Optional[str] = None


# API Endpoints


@router.post("/{location_id}/track-journey")
async def track_client_journey(
    location_id: str = Path(..., description="Location/tenant identifier"),
    request: JourneyTrackingRequest = ...,
    background_tasks: BackgroundTasks = ...,
) -> StandardResponse:
    """
    Track client journey progress and health.

    Monitors journey progression including:
    - Stage tracking and transitions
    - Milestone completion monitoring
    - Journey health assessment
    - Risk factor identification
    - Optimization recommendations
    """
    start_time = datetime.now()

    try:
        logger.info(f"Journey tracking: {request.client_id} in {location_id} -> {request.current_stage}")

        # Validate journey stage
        try:
            current_stage = JourneyStage(request.current_stage)
        except ValueError:
            valid_stages = [stage.value for stage in JourneyStage]
            raise HTTPException(
                status_code=400, detail=f"Invalid journey stage '{request.current_stage}'. Valid stages: {valid_stages}"
            )

        # Get journey mapping service
        journey_service = get_client_journey_mapping()

        # Track journey progress
        health_metrics = await journey_service.track_client_journey(
            client_id=request.client_id,
            location_id=location_id,
            current_stage=current_stage,
            context_data=request.context_data,
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format response
        response_data = {
            "client_id": health_metrics.client_id,
            "current_stage": health_metrics.current_stage.value,
            "health_status": health_metrics.health_status.value,
            "progress": {
                "overall_percentage": health_metrics.overall_progress_percentage,
                "milestones_completed": health_metrics.milestones_completed,
                "milestones_total": health_metrics.milestones_total,
                "milestones_overdue": health_metrics.milestones_overdue,
                "velocity_score": health_metrics.velocity_score,
            },
            "timing": {
                "journey_duration_days": health_metrics.journey_duration_days,
                "expected_completion_date": health_metrics.expected_completion_date.isoformat()
                if health_metrics.expected_completion_date
                else None,
                "projected_delay_days": health_metrics.projected_delay_days,
            },
            "engagement": {
                "client_engagement_score": health_metrics.client_engagement_score,
                "communication_responsiveness": health_metrics.communication_responsiveness,
                "satisfaction_indicators": health_metrics.satisfaction_indicators,
            },
            "risk_assessment": {
                "risk_factors": health_metrics.risk_factors,
                "escalation_needed": health_metrics.escalation_needed,
            },
            "recommendations": {
                "recommended_actions": health_metrics.recommended_actions,
                "automation_opportunities": health_metrics.automation_opportunities,
            },
            "confidence": {
                "assessment_confidence": health_metrics.assessment_confidence,
                "last_assessment": health_metrics.last_assessment.isoformat(),
            },
        }

        logger.info(
            f"Journey tracking complete: {health_metrics.health_status.value} health, "
            f"{health_metrics.overall_progress_percentage:.1f}% progress [{processing_time:.1f}ms]"
        )

        return StandardResponse(success=True, data=response_data, processing_time_ms=processing_time)

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Journey tracking failed: {e}")

        return StandardResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.post("/{location_id}/progress-milestone")
async def progress_client_milestone(
    location_id: str = Path(..., description="Location/tenant identifier"),
    request: MilestoneProgressRequest = ...,
    background_tasks: BackgroundTasks = ...,
) -> StandardResponse:
    """
    Progress a specific milestone in client journey.

    Handles milestone completion including:
    - Milestone status updates
    - Progress percentage tracking
    - Automated next step triggers
    - Stage progression evaluation
    """
    start_time = datetime.now()

    try:
        logger.info(f"Milestone progress: {request.client_id} -> {request.milestone_type}")

        # Validate milestone type
        try:
            milestone_type = MilestoneType(request.milestone_type)
        except ValueError:
            valid_types = [mtype.value for mtype in MilestoneType]
            raise HTTPException(
                status_code=400, detail=f"Invalid milestone type '{request.milestone_type}'. Valid types: {valid_types}"
            )

        # Get journey mapping service
        journey_service = get_client_journey_mapping()

        # Progress the milestone
        milestone = await journey_service.progress_milestone(
            client_id=request.client_id,
            location_id=location_id,
            milestone_type=milestone_type,
            completion_data=request.completion_data,
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format response
        response_data = {
            "milestone_id": milestone.milestone_id,
            "client_id": milestone.client_id,
            "milestone_type": milestone.milestone_type.value,
            "stage": milestone.stage.value,
            "completion_status": milestone.completion_status,
            "progress_percentage": milestone.progress_percentage,
            "title": milestone.title,
            "description": milestone.description,
            "timing": {
                "expected_completion": milestone.expected_completion.isoformat()
                if milestone.expected_completion
                else None,
                "actual_completion": milestone.actual_completion.isoformat() if milestone.actual_completion else None,
                "estimated_duration_days": milestone.estimated_duration_days,
            },
            "workflow": {
                "blocking_issues": milestone.blocking_issues,
                "dependencies": milestone.dependencies,
                "next_actions": milestone.next_actions,
            },
            "automation": {
                "triggered_actions": milestone.automated_actions_triggered,
                "personalization_applied": milestone.personalization_applied,
                "engagement_score": milestone.engagement_score,
            },
            "metadata": {
                "priority_level": milestone.priority_level,
                "created_at": milestone.created_at.isoformat(),
                "updated_at": milestone.updated_at.isoformat(),
            },
        }

        logger.info(
            f"Milestone progressed: {milestone_type.value} -> {milestone.completion_status} [{processing_time:.1f}ms]"
        )

        return StandardResponse(success=True, data=response_data, processing_time_ms=processing_time)

    except HTTPException:
        raise
    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Milestone progression failed: {e}")

        return StandardResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.put("/{location_id}/personalize-journey")
async def personalize_client_journey(
    location_id: str = Path(..., description="Location/tenant identifier"), request: JourneyPersonalizationRequest = ...
) -> StandardResponse:
    """
    Update client journey personalization settings.

    Configures personalized experience including:
    - Communication preferences
    - Content customization
    - Journey pacing adjustments
    - Support intensity levels
    - Automation triggers
    """
    start_time = datetime.now()

    try:
        logger.info(f"Journey personalization: {request.client_id} in {location_id}")

        # Get journey mapping service
        journey_service = get_client_journey_mapping()

        # Update personalization
        personalization = await journey_service.personalize_journey(
            client_id=request.client_id, location_id=location_id, preferences=request.preferences
        )

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        # Format response
        response_data = {
            "client_id": personalization.client_id,
            "location_id": personalization.location_id,
            "communication": {
                "preferred_channel": personalization.preferred_communication_channel,
                "frequency": personalization.communication_frequency,
                "timing": personalization.communication_timing,
            },
            "content": {
                "detail_level": personalization.content_detail_level,
                "market_updates": personalization.market_update_interest,
                "educational_content": personalization.educational_content_interest,
            },
            "journey": {
                "check_in_frequency": personalization.automated_check_in_frequency,
                "priority_areas": personalization.priority_focus_areas,
                "support_intensity": personalization.support_intensity_preference,
            },
            "optimization": {
                "successful_patterns": personalization.successful_interaction_patterns,
                "satisfaction_feedback": personalization.journey_satisfaction_feedback,
                "adaptation_insights": personalization.adaptation_insights,
            },
            "updated_at": datetime.now().isoformat(),
        }

        logger.info(f"Journey personalization updated for {request.client_id} [{processing_time:.1f}ms]")

        return StandardResponse(success=True, data=response_data, processing_time_ms=processing_time)

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Journey personalization failed: {e}")

        return StandardResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.get("/{location_id}/journey-insights/{client_id}")
async def get_client_journey_insights(
    location_id: str = Path(..., description="Location/tenant identifier"),
    client_id: str = Path(..., description="Client identifier"),
) -> StandardResponse:
    """
    Get comprehensive client journey insights and analytics.

    Provides detailed analysis including:
    - Journey progression analytics
    - Performance benchmarking
    - Optimization opportunities
    - Predictive insights
    - Risk assessments
    """
    start_time = datetime.now()

    try:
        logger.info(f"Journey insights request: {client_id} in {location_id}")

        # Get journey mapping service
        journey_service = get_client_journey_mapping()

        # Get comprehensive insights
        insights = await journey_service.get_journey_insights(client_id=client_id, location_id=location_id)

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"Journey insights retrieved for {client_id} [{processing_time:.1f}ms]")

        return StandardResponse(success=True, data=insights, processing_time_ms=processing_time)

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Journey insights failed: {e}")

        return StandardResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.get("/{location_id}/journey-health")
async def get_journey_health_summary(
    location_id: str = Path(..., description="Location/tenant identifier"),
    stage_filter: Optional[str] = Query(None, description="Filter by journey stage"),
    health_filter: Optional[str] = Query(None, description="Filter by health status"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
) -> StandardResponse:
    """
    Get journey health summary across all clients.

    Provides aggregate health insights including:
    - Health status distribution
    - Stage progression analytics
    - Risk factor analysis
    - Performance benchmarks
    """
    start_time = datetime.now()

    try:
        logger.info(f"Journey health summary for {location_id}")

        # Note: This would be implemented with database queries in production
        # For now, return a sample structure
        response_data = {
            "location_id": location_id,
            "summary": {
                "total_active_journeys": 0,
                "health_distribution": {"excellent": 0, "good": 0, "at_risk": 0, "critical": 0, "stalled": 0},
                "stage_distribution": {},
                "average_velocity_score": 0.0,
            },
            "filters_applied": {"stage_filter": stage_filter, "health_filter": health_filter, "limit": limit},
            "timestamp": datetime.now().isoformat(),
        }

        processing_time = (datetime.now() - start_time).total_seconds() * 1000

        logger.info(f"Journey health summary complete [{processing_time:.1f}ms]")

        return StandardResponse(success=True, data=response_data, processing_time_ms=processing_time)

    except Exception as e:
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        logger.error(f"Journey health summary failed: {e}")

        return StandardResponse(success=False, processing_time_ms=processing_time, error=str(e))


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """Health check for Client Experience services."""
    try:
        # Test service availability
        get_client_journey_mapping()

        # Test cache
        cache = get_cache_service()
        test_key = f"health_check:{datetime.now().timestamp()}"
        await cache.set(test_key, "test", 30)
        await cache.delete(test_key)

        return {
            "status": "healthy",
            "services": {"client_journey_mapping": "available", "cache_service": "available"},
            "supported_stages": [stage.value for stage in JourneyStage],
            "supported_milestones": [mtype.value for mtype in MilestoneType],
            "version": "v1.0.0",
            "timestamp": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"Client Experience health check failed: {e}")
        return {"status": "unhealthy", "error": str(e), "timestamp": datetime.now().isoformat()}
