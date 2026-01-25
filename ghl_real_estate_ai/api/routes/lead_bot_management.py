"""
Lead Bot Management API Routes

Provides endpoints for managing Lead Bot 3-7-30 day sequence automation.
Integrates with frontend for sequence control and monitoring.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel

from ghl_real_estate_ai.services.scheduler_startup import get_scheduler_startup_service
from ghl_real_estate_ai.services.lead_sequence_scheduler import get_lead_scheduler
from ghl_real_estate_ai.services.lead_sequence_state_service import get_sequence_service, SequenceDay
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.middleware.jwt_auth import require_auth

logger = get_logger(__name__)
router = APIRouter(prefix="/api/lead-bot", tags=["lead-bot-management"])

# Request/Response Models

class CreateSequenceRequest(BaseModel):
    lead_id: str
    lead_name: str
    phone: str
    email: Optional[str] = None
    property_address: Optional[str] = None
    start_delay_minutes: int = 1  # Default 1 minute delay

class SequenceResponse(BaseModel):
    success: bool
    message: str
    sequence_id: Optional[str] = None
    scheduled_actions: Optional[Dict[str, str]] = None

class SequenceStatusResponse(BaseModel):
    lead_id: str
    current_day: Optional[str] = None
    status: str  # active, paused, completed, failed
    progress: Dict[str, Any]
    next_action: Optional[Dict[str, Any]] = None
    sequence_started_at: Optional[str] = None
    last_activity_at: Optional[str] = None

class SchedulerHealthResponse(BaseModel):
    status: str  # healthy, degraded, failed, not_started
    uptime_seconds: Optional[float] = None
    active_jobs: int
    scheduler_running: bool
    last_error: Optional[str] = None

class ManualTriggerRequest(BaseModel):
    lead_id: str
    sequence_day: str  # "DAY_3", "DAY_7", "DAY_14", "DAY_30"
    action_type: str  # "sms", "call", "email"

# Dependency for scheduler service
async def get_scheduler_service():
    """Get scheduler startup service with error handling"""
    try:
        return get_scheduler_startup_service()
    except Exception as e:
        logger.error(f"Failed to get scheduler service: {e}")
        raise HTTPException(status_code=503, detail="Scheduler service unavailable")

# API Routes

@router.post("/sequences", response_model=SequenceResponse)
async def create_sequence(
    request: CreateSequenceRequest,
    scheduler_service = Depends(get_scheduler_service),
    _auth = Depends(require_auth)
):
    """
    Create a new 3-7-30 day lead sequence

    Initializes sequence state and schedules first action (Day 3 SMS).
    """
    try:
        logger.info(f"Creating new sequence for lead {request.lead_id}")

        # Get services
        sequence_service = get_sequence_service()
        lead_scheduler = get_lead_scheduler()

        if not lead_scheduler or not lead_scheduler.enabled:
            raise HTTPException(
                status_code=503,
                detail="Lead sequence scheduler is not available"
            )

        # Create initial sequence state
        from ghl_real_estate_ai.services.lead_sequence_state_service import LeadSequenceState

        sequence_state = LeadSequenceState(
            lead_id=request.lead_id,
            current_day=SequenceDay.DAY_3,
            sequence_phase="day_3_pending",
            started_at=datetime.now(),
            next_scheduled_at=datetime.now(),
            lead_metadata={
                "name": request.lead_name,
                "phone": request.phone,
                "email": request.email,
                "property_address": request.property_address
            }
        )

        # Save sequence state
        await sequence_service.save_state(sequence_state)

        # Schedule first action (Day 3 SMS)
        success = await lead_scheduler.schedule_sequence_start(
            lead_id=request.lead_id,
            sequence_day=SequenceDay.DAY_3,
            delay_minutes=request.start_delay_minutes
        )

        if success:
            return SequenceResponse(
                success=True,
                message=f"Sequence created for lead {request.lead_id}",
                sequence_id=request.lead_id,
                scheduled_actions={
                    "day_3_sms": f"Scheduled in {request.start_delay_minutes} minutes",
                    "day_7_call": "Will be scheduled after Day 3 completion",
                    "day_14_email": "Will be scheduled after Day 7 completion",
                    "day_30_sms": "Will be scheduled after Day 14 completion"
                }
            )
        else:
            raise HTTPException(
                status_code=500,
                detail="Failed to schedule sequence start"
            )

    except Exception as e:
        logger.error(f"Error creating sequence for lead {request.lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sequences/{lead_id}", response_model=SequenceStatusResponse)
async def get_sequence_status(
    lead_id: str,
    _auth = Depends(require_auth)
):
    """
    Get current status of a lead's sequence

    Returns detailed progress and next scheduled actions.
    """
    try:
        sequence_service = get_sequence_service()
        sequence_state = await sequence_service.get_state(lead_id)

        if not sequence_state:
            raise HTTPException(
                status_code=404,
                detail=f"No sequence found for lead {lead_id}"
            )

        # Build progress information
        progress = {
            "day_3_completed": sequence_state.day_3_completed,
            "day_7_completed": sequence_state.day_7_completed,
            "day_14_completed": sequence_state.day_14_completed,
            "day_30_completed": sequence_state.day_30_completed,
            "day_3_delivered_at": sequence_state.day_3_delivered_at.isoformat() if sequence_state.day_3_delivered_at else None,
            "day_7_delivered_at": sequence_state.day_7_delivered_at.isoformat() if sequence_state.day_7_delivered_at else None,
            "day_14_delivered_at": sequence_state.day_14_delivered_at.isoformat() if sequence_state.day_14_delivered_at else None,
            "day_30_delivered_at": sequence_state.day_30_delivered_at.isoformat() if sequence_state.day_30_delivered_at else None,
            "response_count": sequence_state.response_count,
            "engagement_status": sequence_state.engagement_status
        }

        # Determine next action
        next_action = None
        if not sequence_state.day_3_completed:
            next_action = {
                "action": "Day 3 SMS",
                "scheduled_for": sequence_state.next_scheduled_at.isoformat() if sequence_state.next_scheduled_at else None
            }
        elif not sequence_state.day_7_completed:
            next_action = {
                "action": "Day 7 Voice Call",
                "scheduled_for": sequence_state.next_scheduled_at.isoformat() if sequence_state.next_scheduled_at else None
            }
        elif not sequence_state.day_14_completed:
            next_action = {
                "action": "Day 14 Email",
                "scheduled_for": sequence_state.next_scheduled_at.isoformat() if sequence_state.next_scheduled_at else None
            }
        elif not sequence_state.day_30_completed:
            next_action = {
                "action": "Day 30 SMS",
                "scheduled_for": sequence_state.next_scheduled_at.isoformat() if sequence_state.next_scheduled_at else None
            }

        return SequenceStatusResponse(
            lead_id=lead_id,
            current_day=sequence_state.current_day.value if sequence_state.current_day else None,
            status=sequence_state.status or "unknown",
            progress=progress,
            next_action=next_action,
            sequence_started_at=sequence_state.started_at.isoformat() if sequence_state.started_at else None,
            last_activity_at=sequence_state.last_action_at.isoformat() if sequence_state.last_action_at else None
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting sequence status for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/{lead_id}/pause")
async def pause_sequence(
    lead_id: str,
    _auth = Depends(require_auth)
):
    """
    Pause an active sequence

    Stops future scheduled actions until resumed.
    """
    try:
        sequence_service = get_sequence_service()

        result = await sequence_service.pause_sequence(lead_id)

        if result:
            return {"success": True, "message": f"Sequence paused for lead {lead_id}"}
        else:
            raise HTTPException(status_code=404, detail=f"No active sequence found for lead {lead_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing sequence for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/{lead_id}/resume")
async def resume_sequence(
    lead_id: str,
    _auth = Depends(require_auth)
):
    """
    Resume a paused sequence

    Reschedules pending actions to continue the sequence.
    """
    try:
        sequence_service = get_sequence_service()

        result = await sequence_service.resume_sequence(lead_id)

        if result:
            return {"success": True, "message": f"Sequence resumed for lead {lead_id}"}
        else:
            raise HTTPException(status_code=404, detail=f"No paused sequence found for lead {lead_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming sequence for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sequences/{lead_id}/cancel")
async def cancel_sequence(
    lead_id: str,
    _auth = Depends(require_auth)
):
    """
    Cancel an active sequence

    Permanently stops the sequence and marks it as completed.
    """
    try:
        sequence_service = get_sequence_service()

        result = await sequence_service.complete_sequence(lead_id, "cancelled")

        if result:
            return {"success": True, "message": f"Sequence cancelled for lead {lead_id}"}
        else:
            raise HTTPException(status_code=404, detail=f"No active sequence found for lead {lead_id}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling sequence for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scheduler/status", response_model=SchedulerHealthResponse)
async def get_scheduler_status(
    scheduler_service = Depends(get_scheduler_service),
    _auth = Depends(require_auth)
):
    """
    Get scheduler health status and metrics

    Provides real-time scheduler status for monitoring.
    """
    try:
        health_status = scheduler_service.get_health_status()
        metrics = await scheduler_service.get_scheduler_metrics()

        return SchedulerHealthResponse(
            status=health_status["status"],
            uptime_seconds=metrics.get("uptime_seconds", 0),
            active_jobs=health_status.get("job_count", 0),
            scheduler_running=health_status.get("scheduler_running", False),
            last_error=health_status.get("last_error")
        )

    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/scheduler/restart")
async def restart_scheduler(
    scheduler_service = Depends(get_scheduler_service),
    _auth = Depends(require_auth)
):
    """
    Restart the scheduler (admin function)

    Useful for recovery from errors or configuration changes.
    """
    try:
        result = await scheduler_service.restart_scheduler()

        return result

    except Exception as e:
        logger.error(f"Error restarting scheduler: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/manual-trigger", response_model=Dict[str, Any])
async def manual_trigger(
    request: ManualTriggerRequest,
    scheduler_service = Depends(get_scheduler_service),
    _auth = Depends(require_auth)
):
    """
    Manually trigger a sequence action (testing/recovery)

    Bypasses normal scheduling to execute an action immediately.
    """
    try:
        logger.info(f"Manual trigger requested: {request.lead_id} - {request.sequence_day} {request.action_type}")

        lead_scheduler = get_lead_scheduler()

        if not lead_scheduler or not lead_scheduler.enabled:
            raise HTTPException(
                status_code=503,
                detail="Lead sequence scheduler is not available"
            )

        # Convert string to SequenceDay enum
        sequence_day_mapping = {
            "DAY_3": SequenceDay.DAY_3,
            "DAY_7": SequenceDay.DAY_7,
            "DAY_14": SequenceDay.DAY_14,
            "DAY_30": SequenceDay.DAY_30
        }

        sequence_day = sequence_day_mapping.get(request.sequence_day.upper())
        if not sequence_day:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid sequence_day: {request.sequence_day}. Must be one of: {list(sequence_day_mapping.keys())}"
            )

        # Trigger the action directly
        success = await lead_scheduler._execute_sequence_action(
            request.lead_id,
            sequence_day,
            request.action_type
        )

        if success:
            return {
                "success": True,
                "message": f"Successfully triggered {request.sequence_day} {request.action_type} for lead {request.lead_id}",
                "executed_at": datetime.now().isoformat()
            }
        else:
            return {
                "success": False,
                "message": f"Failed to trigger {request.sequence_day} {request.action_type} for lead {request.lead_id}",
                "executed_at": datetime.now().isoformat()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in manual trigger: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/test-sequence")
async def test_sequence(
    lead_id: str = Query(default="test-lead-1"),
    scheduler_service = Depends(get_scheduler_service),
    _auth = Depends(require_auth)
):
    """
    Create a test sequence for validation

    Creates a test sequence with immediate execution for testing purposes.
    """
    try:
        result = await scheduler_service.trigger_manual_test(lead_id)
        return result

    except Exception as e:
        logger.error(f"Error creating test sequence: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check(scheduler_service = Depends(get_scheduler_service)):
    """
    Simple health check for load balancers

    Returns 200 if scheduler is healthy, 503 if not.
    """
    try:
        is_healthy = scheduler_service.is_healthy()

        if is_healthy:
            return {"status": "healthy", "timestamp": datetime.now().isoformat()}
        else:
            raise HTTPException(
                status_code=503,
                detail="Scheduler is not healthy"
            )

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")

# Export router for main app
__all__ = ["router"]