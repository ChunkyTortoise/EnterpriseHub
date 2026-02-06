#!/usr/bin/env python3
"""
Jorge's Webhook Server - GHL Integration Endpoints

This server receives leads from GHL via webhooks and processes them
through Jorge's bot system, then sends responses back to clients.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import logging
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uvicorn
from datetime import datetime
import json

# Jorge's optimized bots
from jorge_lead_bot import create_jorge_lead_bot
from jorge_seller_bot import create_jorge_seller_bot
from ghl_client import GHLClient
from config_settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Jorge's Bot Webhook Server",
    description="Receives leads from GHL and processes with Jorge's AI bots",
    version="1.0.0"
)

# Initialize bots
lead_bot = create_jorge_lead_bot()
seller_bot = create_jorge_seller_bot()
ghl_client = GHLClient()


# Pydantic models for webhook payloads
class GHLWebhookPayload(BaseModel):
    """Standard GHL webhook payload"""
    contact_id: str
    location_id: str
    message: Optional[str] = ""
    contact_name: Optional[str] = ""
    contact_phone: Optional[str] = ""
    contact_email: Optional[str] = ""
    source: Optional[str] = "webhook"
    timestamp: Optional[str] = ""


class ManualProcessRequest(BaseModel):
    """Manual agent request to process a lead"""
    contact_id: str
    location_id: str
    message: str
    agent_name: Optional[str] = "agent"
    process_type: str = "auto"  # "auto", "lead", "seller"


@app.post("/webhook/ghl-contact")
async def handle_ghl_contact_webhook(payload: GHLWebhookPayload):
    """
    Handle new contact creation from GHL
    """
    try:
        logger.info(f"New contact webhook: {payload.contact_id}")

        if not payload.message:
            return JSONResponse({
                "status": "skipped",
                "reason": "No message to process"
            })

        # Determine if this is a buyer or seller lead
        lead_type = determine_lead_type(payload.message)

        if lead_type == "seller":
            result = await seller_bot.process_seller_message(
                contact_id=payload.contact_id,
                location_id=payload.location_id,
                message=payload.message
            )

            # Send Jorge's response back to client
            if result.response_message:
                await send_response_to_client(
                    contact_id=payload.contact_id,
                    message=result.response_message,
                    contact_phone=payload.contact_phone
                )

            return JSONResponse({
                "status": "processed",
                "type": "seller",
                "temperature": result.seller_temperature,
                "response_sent": bool(result.response_message)
            })

        else:  # buyer/lead
            result = await lead_bot.process_lead_message(
                contact_id=payload.contact_id,
                location_id=payload.location_id,
                message=payload.message
            )

            # Send response back to client
            if result.get("message"):
                await send_response_to_client(
                    contact_id=payload.contact_id,
                    message=result["message"],
                    contact_phone=payload.contact_phone
                )

            return JSONResponse({
                "status": "processed",
                "type": "lead",
                "score": result.get("lead_score", 0),
                "temperature": result.get("lead_temperature", "cold"),
                "response_sent": bool(result.get("message"))
            })

    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.post("/webhook/ghl-sms")
async def handle_ghl_sms_webhook(payload: GHLWebhookPayload):
    """
    Handle SMS messages received by GHL
    """
    try:
        logger.info(f"SMS webhook from {payload.contact_phone}: {payload.message}")

        # Get conversation context to determine if this is ongoing seller qualification
        # or new lead interaction

        lead_type = determine_lead_type(payload.message)

        if lead_type == "seller":
            result = await seller_bot.process_seller_message(
                contact_id=payload.contact_id,
                location_id=payload.location_id,
                message=payload.message
            )

            # Send Jorge's response via SMS
            await send_sms_response(
                phone=payload.contact_phone,
                message=result.response_message
            )

            return JSONResponse({
                "status": "processed",
                "type": "seller_sms",
                "response_sent": True
            })

        else:
            result = await lead_bot.process_lead_message(
                contact_id=payload.contact_id,
                location_id=payload.location_id,
                message=payload.message
            )

            # Send response via SMS
            await send_sms_response(
                phone=payload.contact_phone,
                message=result.get("message", "Thanks for your interest! I'll get back to you shortly.")
            )

            return JSONResponse({
                "status": "processed",
                "type": "lead_sms",
                "response_sent": True
            })

    except Exception as e:
        logger.error(f"SMS webhook error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.post("/agent/process-lead")
async def manual_lead_processing(request: ManualProcessRequest):
    """
    Manual lead processing endpoint for agents
    """
    try:
        logger.info(f"Manual processing by {request.agent_name}: {request.contact_id}")

        if request.process_type == "seller":
            result = await seller_bot.process_seller_message(
                contact_id=request.contact_id,
                location_id=request.location_id,
                message=request.message
            )

            return JSONResponse({
                "status": "success",
                "type": "seller",
                "result": {
                    "response": result.response_message,
                    "temperature": result.seller_temperature,
                    "questions_answered": result.questions_answered,
                    "qualification_complete": result.qualification_complete,
                    "next_steps": result.next_steps
                }
            })

        else:  # lead processing
            result = await lead_bot.process_lead_message(
                contact_id=request.contact_id,
                location_id=request.location_id,
                message=request.message
            )

            return JSONResponse({
                "status": "success",
                "type": "lead",
                "result": {
                    "response": result.get("message", ""),
                    "score": result.get("lead_score", 0),
                    "temperature": result.get("lead_temperature", "cold"),
                    "budget": result.get("budget_max"),
                    "timeline": result.get("timeline"),
                    "location": result.get("location_preferences")
                }
            })

    except Exception as e:
        logger.error(f"Manual processing error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.get("/agent/analytics/{contact_id}")
async def get_lead_analytics(contact_id: str, location_id: str):
    """
    Get analytics for a specific lead
    """
    try:
        # Try both lead and seller analytics
        lead_analytics = await lead_bot.get_lead_analytics(contact_id, location_id)
        seller_analytics = await seller_bot.get_seller_analytics(contact_id, location_id)

        return JSONResponse({
            "status": "success",
            "contact_id": contact_id,
            "lead_analytics": lead_analytics,
            "seller_analytics": seller_analytics
        })

    except Exception as e:
        logger.error(f"Analytics error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


@app.post("/test/simulate-lead")
async def simulate_lead_for_testing(request: ManualProcessRequest):
    """
    Test endpoint to simulate a lead for demonstration
    """
    try:
        logger.info(f"Simulating lead: {request.message}")

        # Process as if it came from a real webhook
        lead_type = determine_lead_type(request.message)

        if lead_type == "seller":
            result = await seller_bot.process_seller_message(
                contact_id=f"test_{datetime.now().strftime('%H%M%S')}",
                location_id=request.location_id or "test_location",
                message=request.message
            )

            return JSONResponse({
                "status": "demo_success",
                "type": "seller",
                "original_message": request.message,
                "jorge_response": result.response_message,
                "temperature": result.seller_temperature,
                "questions_answered": result.questions_answered,
                "actions_triggered": result.actions_taken
            })

        else:
            result = await lead_bot.process_lead_message(
                contact_id=f"test_{datetime.now().strftime('%H%M%S')}",
                location_id=request.location_id or "test_location",
                message=request.message
            )

            return JSONResponse({
                "status": "demo_success",
                "type": "lead",
                "original_message": request.message,
                "jorge_response": result.get("message", ""),
                "lead_score": result.get("lead_score", 0),
                "temperature": result.get("lead_temperature", "cold"),
                "budget_detected": result.get("budget_max"),
                "timeline_detected": result.get("timeline"),
                "actions_triggered": result.get("actions", [])
            })

    except Exception as e:
        logger.error(f"Simulation error: {e}")
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)


def determine_lead_type(message: str) -> str:
    """
    Determine if this is a buyer lead or seller lead
    """
    message_lower = message.lower()

    # Seller indicators
    seller_keywords = [
        "sell", "selling", "sell my house", "want to sell",
        "thinking about selling", "need to sell", "inherited",
        "divorce", "foreclosure", "cash offer", "buy my house",
        "what's it worth", "house value", "quick sale"
    ]

    # Buyer indicators
    buyer_keywords = [
        "buy", "buying", "looking for", "want to buy",
        "house hunting", "need a house", "find a home",
        "budget", "pre-approved", "mortgage", "first time buyer"
    ]

    seller_score = sum(1 for keyword in seller_keywords if keyword in message_lower)
    buyer_score = sum(1 for keyword in buyer_keywords if keyword in message_lower)

    if seller_score > buyer_score:
        return "seller"
    else:
        return "lead"


async def send_response_to_client(contact_id: str, message: str, contact_phone: Optional[str] = None):
    """
    Send bot response back to client via GHL
    """
    try:
        if contact_phone:
            # Send via SMS
            await send_sms_response(contact_phone, message)
        else:
            # Send via GHL messaging system
            await ghl_client.send_message(contact_id, message)

    except Exception as e:
        logger.error(f"Response delivery error: {e}")


async def send_sms_response(phone: str, message: str):
    """
    Send SMS response via GHL
    """
    try:
        # Use GHL SMS API to send response
        await ghl_client.send_sms(phone, message)
        logger.info(f"SMS sent to {phone}")

    except Exception as e:
        logger.error(f"SMS sending error: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "bots": "operational",
        "ghl_connection": "active"
    })


@app.get("/")
async def root():
    """Root endpoint with setup instructions"""
    return JSONResponse({
        "message": "Jorge's Bot Webhook Server",
        "status": "operational",
        "endpoints": {
            "ghl_contact_webhook": "/webhook/ghl-contact",
            "ghl_sms_webhook": "/webhook/ghl-sms",
            "manual_processing": "/agent/process-lead",
            "analytics": "/agent/analytics/{contact_id}",
            "test_simulation": "/test/simulate-lead"
        },
        "setup": {
            "ghl_webhook_url": "https://your-domain.com/webhook/ghl-contact",
            "sms_webhook_url": "https://your-domain.com/webhook/ghl-sms",
            "dashboard": "http://localhost:8503"
        }
    })


if __name__ == "__main__":
    print("🚀 Starting Jorge's Bot Webhook Server...")
    print(f"Dashboard available at: http://localhost:8503")
    print(f"Webhook server will run at: http://localhost:8000")
    print()
    print("GHL Webhook URLs to configure:")
    print("  Contact Created: http://localhost:8000/webhook/ghl-contact")
    print("  SMS Received: http://localhost:8000/webhook/ghl-sms")
    print()

    uvicorn.run(
        "jorge_webhook_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )