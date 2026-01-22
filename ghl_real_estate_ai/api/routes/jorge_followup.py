"""
Jorge Martinez Follow-up Automation API Routes.

Provides endpoints for:
- Webhook-triggered follow-up execution
- Batch processing of scheduled follow-ups
- Follow-up system statistics and analytics
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query
from typing import Dict, Any, Optional
import logging

from ghl_real_estate_ai.services.jorge.jorge_followup_scheduler import JorgeFollowUpScheduler
from ghl_real_estate_ai.core.conversation_manager import ConversationManager
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jorge-followup", tags=["jorge-followup"])

# Initialize components
conversation_manager = ConversationManager()
ghl_client = GHLClient()
analytics_service = AnalyticsService()
scheduler = JorgeFollowUpScheduler(conversation_manager, ghl_client, analytics_service)

@router.post("/webhook")
async def trigger_followup_webhook(
    payload: Dict[str, Any],
    background_tasks: BackgroundTasks
):
    """
    Endpoint for GHL Workflows to trigger an automated follow-up.
    
    Payload expects:
    - contact_id: str
    - location_id: str
    - trigger_type: str (initial_follow_up, qualification_retry, etc.)
    """
    contact_id = payload.get("contact_id")
    location_id = payload.get("location_id")
    
    if not contact_id or not location_id:
        raise HTTPException(status_code=400, detail="Missing contact_id or location_id")
    
    logger.info(f"Follow-up webhook received for contact {contact_id}")
    
    # Process in background to avoid GHL timeout
    background_tasks.add_task(
        scheduler.process_webhook_follow_up,
        contact_id=contact_id,
        location_id=location_id,
        webhook_data=payload
    )
    
    return {"status": "accepted", "message": "Follow-up processing initiated"}

@router.post("/process-batch")
async def process_batch_followups(
    batch_size: int = Query(default=50, ge=1, le=100),
    location_id: Optional[str] = None
):
    """
    Trigger batch processing of all due follow-ups.
    Can be called by a cron job.
    """
    results = await scheduler.process_scheduled_follow_ups(
        batch_size=batch_size,
        location_id=location_id
    )
    return results

@router.get("/stats")
async def get_followup_stats(
    location_id: Optional[str] = None,
    days: int = Query(default=30, ge=1, le=90)
):
    """
    Get follow-up system performance statistics.
    """
    stats = await scheduler.get_follow_up_statistics(
        location_id=location_id,
        date_range_days=days
    )
    return stats

@router.post("/setup-workflows/{location_id}")
async def setup_ghl_workflows(location_id: str):
    """
    Create/Update GHL workflow templates for this location.
    """
    results = await scheduler.create_ghl_workflow_triggers(location_id)
    return results
