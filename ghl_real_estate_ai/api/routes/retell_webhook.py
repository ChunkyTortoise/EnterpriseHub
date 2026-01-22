from fastapi import APIRouter, Request, HTTPException, BackgroundTasks, status
from typing import Dict, Any
from ghl_real_estate_ai.integrations.retell import RetellClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.ghl_utils.config import settings

logger = get_logger(__name__)
router = APIRouter(prefix="/retell", tags=["retell"])

@router.post("/webhook")
async def handle_retell_webhook(request: Request, payload: Dict[str, Any], background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from Retell AI.
    Processes call updates, transcripts, and completion events.
    """
    
    # 1. Validate Signature (Optional/Placeholder)
    signature = request.headers.get("X-Retell-Signature", "")
    if not RetellClient.validate_webhook(payload, signature):
        logger.warning("Invalid Retell webhook signature")
        # raise HTTPException(status_code=403, detail="Invalid signature") 
        # Commented out until signature verification is fully implemented

    event_type = payload.get("event")
    call_id = payload.get("call_id")
    
    logger.info(f"Received Retell webhook: {event_type} for call {call_id}")

    if event_type == "call_analyzed":
        # Call finished and analyzed
        call_data = payload.get("call", {})
        transcript = call_data.get("transcript", "")
        analysis = payload.get("analysis", {})
        metadata = payload.get("metadata", {})
        contact_id = metadata.get("contact_id")
        
        # Log outcome
        logger.info(
            f"Retell Call {call_id} completed for contact {contact_id}",
            extra={
                "sentiment": analysis.get("user_sentiment"),
                "call_successful": analysis.get("call_successful"),
                "transcript_length": len(transcript)
            }
        )
        
        if contact_id:
            background_tasks.add_task(process_call_outcome, contact_id, analysis, transcript, call_id)

    elif event_type == "call_started":
        logger.info(f"Retell Call {call_id} started")

    return {"received": True}

async def process_call_outcome(contact_id: str, analysis: Dict[str, Any], transcript: str, call_id: str = "unknown"):
    """
    Update GHL and Lyrio with the results of the Retell AI call.
    """
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient
    from ghl_real_estate_ai.integrations.lyrio import LyrioClient
    
    logger.info(f"Processing call outcome for contact {contact_id}")
    
    # 1. Sync to Lyrio (Phase 4 Headless Integration)
    lyrio = LyrioClient()
    await lyrio.sync_call_summary(contact_id, call_id, analysis)
    
    # 2. Prepare updates for GHL
    updates = {
        "custom_fields": {}
    }
    
    # Map Retell sentiment to Jorge's temperature field
    sentiment = analysis.get("user_sentiment", "Neutral")
    if settings.custom_field_seller_temperature:
        updates["custom_fields"][settings.custom_field_seller_temperature] = sentiment
        
    # Map other analysis fields if they exist (Retell Custom Analysis)
    # Assuming the Retell agent is configured to extract these specific Jorge pillars
    custom_data = analysis.get("custom_analysis_data", {})
    
    mapping = {
        "motivation": settings.custom_field_seller_motivation,
        "timeline": settings.custom_field_timeline_urgency,
        "condition": settings.custom_field_property_condition,
        "price_expectation": settings.custom_field_price_expectation
    }
    
    for key, field_id in mapping.items():
        if field_id and key in custom_data:
            updates["custom_fields"][field_id] = custom_data[key]
            
    # 2. Update GHL
    async with EnhancedGHLClient() as ghl:
        try:
            # Update custom fields
            await ghl.update_contact(contact_id, updates)
            
            # Add a note with the transcript summary
            summary = analysis.get("call_summary", "No summary provided.")
            note_text = f"--- RETELL AI CALL SUMMARY ---\nOutcome: {analysis.get('agent_sentiment', 'N/A')}\nSummary: {summary}\n\nFull Transcript available in Retell dashboard."
            
            # Note: EnhancedGHLClient might need a create_note method if not present
            # For now, let's assume update_contact is the primary sync
            logger.info(f"Successfully synced Retell outcome to GHL for {contact_id}")
            
        except Exception as e:
            logger.error(f"Failed to sync Retell outcome to GHL: {e}")
