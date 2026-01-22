"""
External Webhook Handlers for Service 6.

Handles incoming webhooks from:
- Twilio (SMS status updates and incoming messages)
- SendGrid (Email events)
- Apollo (Data enrichment events)
"""

from typing import Any, Dict, List
from fastapi import APIRouter, Request, BackgroundTasks, HTTPException, status
from pydantic import BaseModel

from ghl_real_estate_ai.services.security_framework import verify_webhook
from ghl_real_estate_ai.services.twilio_client import TwilioClient
from ghl_real_estate_ai.services.sendgrid_client import SendGridClient
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/webhooks", tags=["external_webhooks"])

# Initialize clients
twilio_client = TwilioClient()
sendgrid_client = SendGridClient()

@router.post("/twilio/sms-status")
@verify_webhook("twilio")
async def handle_twilio_sms_status(request: Request):
    """
    Handle Twilio SMS status callback.
    """
    try:
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        logger.info(f"Received Twilio SMS status: {webhook_data.get('MessageStatus')} for {webhook_data.get('MessageSid')}")
        
        success = await twilio_client.process_status_webhook(request, webhook_data)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to process Twilio status webhook"
            )
            
    except Exception as e:
        logger.error(f"Error processing Twilio status webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )

@router.post("/twilio/sms-incoming")
@verify_webhook("twilio")
async def handle_twilio_sms_incoming(request: Request):
    """
    Handle incoming SMS from Twilio.
    """
    try:
        form_data = await request.form()
        webhook_data = dict(form_data)
        
        from_number = webhook_data.get('From', 'Unknown')
        masked_number = f"{from_number[:5]}***{from_number[-4:]}" if len(from_number) > 9 else "***"
        
        logger.info(f"Received incoming SMS from {masked_number}")
        
        success = await twilio_client.process_incoming_webhook(request, webhook_data)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to process incoming SMS"
            )
            
    except Exception as e:
        logger.error(f"Error processing Twilio incoming webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )

@router.post("/sendgrid/events")
@verify_webhook("sendgrid")
async def handle_sendgrid_events(request: Request):
    """
    Handle SendGrid event webhooks.
    """
    try:
        events = await request.json()
        if not isinstance(events, list):
            events = [events]
            
        logger.info(f"Received {len(events)} SendGrid events")
        
        success = await sendgrid_client.process_event_webhook(request, events)
        
        if success:
            return {"status": "success"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to process SendGrid events"
            )
            
    except Exception as e:
        logger.error(f"Error processing SendGrid event webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )

@router.post("/apollo/enrichment")
@verify_webhook("apollo")
async def handle_apollo_enrichment(request: Request):
    """
    Handle Apollo.io enrichment webhooks.
    """
    try:
        payload = await request.json()
        logger.info(f"Received Apollo enrichment for {payload.get('email')}")
        
        # Enrichment logic would go here
        # For now, acknowledge receipt
        return {"status": "success", "processed": True}
            
    except Exception as e:
        logger.error(f"Error processing Apollo enrichment webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE, 
            detail=f"Service temporarily unavailable: {str(e)}"
        )
