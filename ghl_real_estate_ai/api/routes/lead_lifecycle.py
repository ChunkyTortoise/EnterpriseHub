"""
Lead Lifecycle Management API Routes for Phase 2.

Provides endpoints for:
- Lead stage tracking and transitions
- Re-engagement campaigns
- Lead health scoring
- Automated nurture sequences
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field

from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/lifecycle", tags=["lead-lifecycle"])


# Request/Response Models
class StageTransition(BaseModel):
    """Request model for stage transition."""
    contact_id: str
    new_stage: str = Field(..., description="Target stage (cold, warm, hot, qualified, lost)")
    reason: Optional[str] = Field(default=None, description="Reason for transition")
    notes: Optional[str] = Field(default=None, description="Additional notes")


class ReengagementRequest(BaseModel):
    """Request model for re-engagement campaign."""
    contact_ids: Optional[List[str]] = Field(default=None, description="Specific contacts to re-engage")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Filters for auto-selecting contacts")
    template: str = Field(..., description="Message template to use")
    schedule_at: Optional[str] = Field(default=None, description="ISO timestamp to schedule")


class LeadHealth(BaseModel):
    """Response model for lead health."""
    contact_id: str
    health_score: float
    last_interaction: str
    days_since_contact: int
    engagement_level: str
    risk_level: str
    recommended_action: str


class LifecycleMetrics(BaseModel):
    """Response model for lifecycle metrics."""
    total_leads: int
    by_stage: Dict[str, int]
    avg_time_to_qualified: float
    conversion_rate: float
    churn_rate: float
    active_nurture_sequences: int


# Lead Stage Management
@router.post("/stages/transition")
async def transition_lead_stage(
    location_id: str,
    transition: StageTransition,
    background_tasks: BackgroundTasks
):
    """
    Manually transition a lead to a new stage.
    
    Updates lead stage and triggers appropriate automations.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Get or start journey for this contact
        journey = lifecycle_tracker.get_journey(transition.contact_id)
        if not journey:
            journey_id = lifecycle_tracker.start_journey(
                contact_id=transition.contact_id,
                contact_name=transition.contact_id,
                source="api"
            )
        else:
            journey_id = journey.get("id", transition.contact_id)
        
        # Transition to new stage
        lifecycle_tracker.transition_stage(journey_id, transition.new_stage)
        
        result = {
            "old_stage": journey.get("current_stage") if journey else "unknown",
            "journey_id": journey_id
        }
        
        logger.info(f"Transitioned contact {transition.contact_id} to stage {transition.new_stage}")
        
        return {
            "success": True,
            "contact_id": transition.contact_id,
            "old_stage": result.get("old_stage"),
            "new_stage": transition.new_stage,
            "transitioned_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error transitioning lead stage: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to transition stage: {str(e)}")


@router.get("/stages/{location_id}/{contact_id}/history")
async def get_stage_history(location_id: str, contact_id: str):
    """
    Get complete stage transition history for a lead.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        journey = lifecycle_tracker.get_journey(contact_id)
        
        if not journey:
            history = []
        else:
            # Extract stage transitions from journey events
            history = [
                {
                    "stage": event.get("new_stage", event.get("stage", "unknown")),
                    "timestamp": event.get("timestamp"),
                    "event": event.get("event_type")
                }
                for event in journey.get("events", [])
                if event.get("event_type") in ["stage_transition", "journey_start"]
            ]
        
        return {
            "contact_id": contact_id,
            "history": history,
            "current_stage": history[-1]["stage"] if history else None
        }
        
    except Exception as e:
        logger.error(f"Error fetching stage history: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {str(e)}")


# Lead Health Monitoring
@router.get("/health/{location_id}/{contact_id}", response_model=LeadHealth)
async def get_lead_health(location_id: str, contact_id: str):
    """
    Get health score and engagement metrics for a specific lead.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        journey = lifecycle_tracker.get_journey(contact_id)
        
        if not journey:
            raise HTTPException(status_code=404, detail="Lead not found")
        
        # Calculate basic health from journey
        summary = lifecycle_tracker.get_journey_summary(contact_id)
        
        health = {
            "contact_id": contact_id,
            "health_score": summary.get("progression_rate", 0.0),
            "last_interaction": summary.get("last_event_time", datetime.now().isoformat()),
            "days_since_contact": summary.get("duration_days", 0),
            "engagement_level": "high" if summary.get("progression_rate", 0) > 0.7 else "medium" if summary.get("progression_rate", 0) > 0.4 else "low",
            "risk_level": "low" if summary.get("progression_rate", 0) > 0.7 else "medium" if summary.get("progression_rate", 0) > 0.4 else "high",
            "recommended_action": "Continue nurturing" if summary.get("progression_rate", 0) > 0.5 else "Re-engage immediately"
        }
        
        return LeadHealth(**health)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error calculating lead health: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to calculate health: {str(e)}")


@router.get("/health/{location_id}/at-risk")
async def get_at_risk_leads(
    location_id: str,
    threshold: float = Query(default=0.3, description="Health score threshold (0-1)")
):
    """
    Get list of leads at risk of going cold.
    
    Returns leads with health scores below the threshold.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Get all journeys and filter by low progression rate (at-risk)
        # For now, return empty list as we'd need to iterate all journeys
        # This would be implemented by the service layer in production
        at_risk_leads = []
        
        return {
            "location_id": location_id,
            "threshold": threshold,
            "at_risk_count": len(at_risk_leads),
            "leads": at_risk_leads
        }
        
    except Exception as e:
        logger.error(f"Error identifying at-risk leads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to identify at-risk leads: {str(e)}")


# Re-engagement Campaigns
@router.post("/reengage/campaign", status_code=202)
async def create_reengagement_campaign(
    location_id: str,
    request: ReengagementRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a re-engagement campaign for dormant leads.
    
    Automatically selects leads based on filters or uses provided contact list.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Generate campaign ID
        import time
        campaign_id = f"reeng_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"
        
        # In production, this would trigger actual re-engagement
        # For now, just log the campaign creation
        logger.info(f"Re-engagement campaign {campaign_id} created for {len(request.contact_ids or [])} contacts")
        
        logger.info(f"Created re-engagement campaign {campaign_id} for location {location_id}")
        
        return {
            "campaign_id": campaign_id,
            "status": "scheduled" if request.schedule_at else "processing",
            "message": "Re-engagement campaign created successfully"
        }
        
    except Exception as e:
        logger.error(f"Error creating re-engagement campaign: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")


@router.get("/reengage/{location_id}/eligible")
async def get_eligible_for_reengagement(
    location_id: str,
    days_inactive: int = Query(default=30, description="Days since last contact")
):
    """
    Get list of leads eligible for re-engagement.
    
    Returns leads that haven't been contacted in specified days.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Get eligible leads based on inactivity
        # In production, this would query all journeys and filter by last activity
        eligible_leads = []
        
        return {
            "location_id": location_id,
            "days_inactive": days_inactive,
            "eligible_count": len(eligible_leads),
            "leads": eligible_leads
        }
        
    except Exception as e:
        logger.error(f"Error finding eligible leads: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to find eligible leads: {str(e)}")


# Lifecycle Metrics
@router.get("/metrics/{location_id}", response_model=LifecycleMetrics)
async def get_lifecycle_metrics(
    location_id: str,
    days: int = Query(default=30, description="Number of days to analyze")
):
    """
    Get comprehensive lifecycle metrics for a location.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Get stage analytics
        stage_data = lifecycle_tracker.get_stage_analytics()
        funnel = lifecycle_tracker.get_conversion_funnel()
        
        metrics = {
            "total_leads": sum(stage_data.get("stage_distribution", {}).values()),
            "by_stage": stage_data.get("stage_distribution", {}),
            "avg_time_to_qualified": stage_data.get("avg_time_in_stage", {}).get("qualified", 0.0),
            "conversion_rate": funnel.get("overall_conversion_rate", 0.0),
            "churn_rate": 0.0,  # Not tracked yet
            "active_nurture_sequences": 0  # Not tracked yet
        }
        
        return LifecycleMetrics(**metrics)
        
    except Exception as e:
        logger.error(f"Error fetching lifecycle metrics: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to fetch metrics: {str(e)}")


# Automated Nurture Sequences
@router.post("/nurture/start")
async def start_nurture_sequence(
    location_id: str,
    contact_id: str,
    sequence_type: str = Query(..., description="Type of nurture sequence"),
    background_tasks: BackgroundTasks = None
):
    """
    Start an automated nurture sequence for a lead.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Generate sequence ID
        import time
        sequence_id = f"seq_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{int(time.time() * 1000000) % 1000000}"
        
        # Log sequence start
        logger.info(f"Started nurture sequence {sequence_id} for contact {contact_id}")
        
        logger.info(f"Started nurture sequence {sequence_id} for contact {contact_id}")
        
        return {
            "sequence_id": sequence_id,
            "contact_id": contact_id,
            "sequence_type": sequence_type,
            "status": "active"
        }
        
    except Exception as e:
        logger.error(f"Error starting nurture sequence: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to start sequence: {str(e)}")


@router.post("/nurture/{sequence_id}/stop")
async def stop_nurture_sequence(location_id: str, sequence_id: str):
    """
    Stop an active nurture sequence.
    """
    try:
        lifecycle_tracker = LeadLifecycleTracker(location_id)
        
        # Log sequence stop
        logger.info(f"Stopped nurture sequence {sequence_id}")
        result = {"stopped": True}
        
        return {
            "sequence_id": sequence_id,
            "status": "stopped",
            "stopped_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error stopping nurture sequence: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to stop sequence: {str(e)}")


# Health check
@router.get("/health")
async def lifecycle_health():
    """Health check for lead lifecycle endpoints."""
    return {
        "status": "healthy",
        "service": "lead-lifecycle",
        "timestamp": datetime.now().isoformat()
    }
