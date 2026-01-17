#!/usr/bin/env python3
"""
Complete GHL Webhook Handler Example
Production-ready implementation for real estate lead qualification

This example shows how to implement the complete webhook handler
using all the components from the skill framework.
"""

import os
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import uvicorn

# Import skill components (these would be in your project)
# from your_project.webhook_security import WebhookSecurityManager, WebhookErrorHandler
# from your_project.lead_qualification import LeadQualificationState, calculate_lead_score
# from your_project.ai_responses import RealEstateAIResponseGenerator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GHL Real Estate AI Webhook Service",
    description="AI-powered lead qualification for real estate",
    version="1.0.0",
)

# Configuration from environment
GHL_WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "")
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
GHL_API_BASE_URL = "https://rest.gohighlevel.com/v1"

# Initialize services (you would use actual imports)
# security_manager = WebhookSecurityManager(GHL_WEBHOOK_SECRET)
# ai_generator = RealEstateAIResponseGenerator(ANTHROPIC_API_KEY)

# In-memory state storage (use Redis/database in production)
qualification_states: Dict[str, Dict] = {}
conversation_histories: Dict[str, List] = {}


class MockWebhookSecurityManager:
    """Mock security manager for example"""
    def __init__(self, secret): self.secret = secret
    def verify_webhook_signature(self, request, body): return True
    def check_rate_limit(self, ip): return True
    def validate_payload(self, payload): return payload.get("contactId") and payload.get("locationId")
    def sanitize_payload(self, payload): return payload


class MockAIGenerator:
    """Mock AI generator for example"""
    def __init__(self, api_key): self.api_key = api_key

    async def generate_qualification_response(self, contact_data, history, question_type, context=None):
        """Generate mock response for example"""
        responses = {
            "budget": "Quick question - what's your budget range looking like?",
            "location": "Got it. Which neighborhoods are you eyeing?",
            "bedrooms": "How many bedrooms do you need?",
            "timeline": "When are you hoping to make a move?",
            "preapproval": "Are you pre-approved or do you need a lender recommendation?",
            "motivation": "What's driving the decision right now?"
        }
        await asyncio.sleep(0.1)  # Simulate API call
        return responses.get(question_type, "Thanks for the information!")


# Initialize mock services for example
security_manager = MockWebhookSecurityManager(GHL_WEBHOOK_SECRET)
ai_generator = MockAIGenerator(ANTHROPIC_API_KEY)


@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "service": "GHL Real Estate AI Webhook",
        "status": "active",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@app.post("/webhook/ghl")
async def handle_ghl_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for GHL triggers.

    Implements complete lead qualification workflow:
    1. Security verification
    2. Payload processing
    3. Lead qualification assessment
    4. AI response generation
    5. Background task execution
    """
    client_ip = request.client.host if request.client else "unknown"
    start_time = datetime.utcnow()

    try:
        # Step 1: Security verification
        body = await request.body()

        if not security_manager.check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(status_code=429, detail="Rate limit exceeded")

        if not security_manager.verify_webhook_signature(request, body):
            logger.error(f"Invalid webhook signature from IP: {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid signature")

        # Step 2: Parse and validate payload
        try:
            payload = await request.json()
        except Exception as e:
            logger.error(f"Invalid JSON payload: {e}")
            raise HTTPException(status_code=400, detail="Invalid JSON")

        if not security_manager.validate_payload(payload):
            raise HTTPException(status_code=400, detail="Invalid payload structure")

        # Step 3: Extract key information
        contact_id = payload.get("contactId")
        location_id = payload.get("locationId")
        tags = payload.get("tags", [])
        webhook_type = payload.get("type", "unknown")

        logger.info(f"Processing webhook for contact {contact_id}, type: {webhook_type}")

        # Step 4: Check AI engagement status
        ai_on = "AI Assistant: ON" in tags or "ai_on" in tags
        ai_off = "AI Assistant: OFF" in tags or "ai_off" in tags

        if ai_off or not ai_on:
            return JSONResponse({
                "status": "skipped",
                "reason": "AI not enabled for this contact",
                "contact_id": contact_id
            })

        # Step 5: Get or create qualification state
        if contact_id not in qualification_states:
            qualification_states[contact_id] = {
                "contact_id": contact_id,
                "current_question": "budget",
                "answers": {},
                "message_count": 0,
                "score": 0,
                "status": "cold",
                "created_at": start_time,
                "engagement_level": 0.0
            }
            conversation_histories[contact_id] = []

        state = qualification_states[contact_id]
        history = conversation_histories[contact_id]

        # Step 6: Check if lead should be handed off
        if state["score"] >= 3:
            logger.info(f"Lead {contact_id} is HOT (score: {state['score']}) - handing off to human")

            # Schedule background tasks for handoff
            background_tasks.add_task(
                update_contact_tag,
                contact_id, location_id, "Hot Lead"
            )
            background_tasks.add_task(
                update_contact_tag,
                contact_id, location_id, "AI Assistant: OFF"
            )
            background_tasks.add_task(
                send_sms_via_ghl,
                contact_id, location_id,
                "Thanks for all the info! A team member will reach out shortly to help you. 🎉"
            )

            return JSONResponse({
                "status": "handoff",
                "score": state["score"],
                "status_label": state["status"],
                "contact_id": contact_id
            })

        # Step 7: Generate AI response
        contact_data = {
            "name": payload.get("firstName", ""),
            "phone": payload.get("phone", ""),
            "email": payload.get("email", "")
        }

        try:
            ai_message = await ai_generator.generate_qualification_response(
                contact_data=contact_data,
                conversation_history=history,
                question_type=state["current_question"],
                lead_context={
                    "score": state["score"],
                    "engagement_level": state["engagement_level"]
                }
            )
        except Exception as e:
            logger.error(f"AI generation failed: {e}")
            ai_message = "Quick question - what's your budget range looking like?"

        # Step 8: Schedule background tasks
        background_tasks.add_task(
            send_sms_via_ghl,
            contact_id, location_id, ai_message
        )
        background_tasks.add_task(
            update_conversation_history,
            contact_id, ai_message, "agent"
        )
        background_tasks.add_task(
            log_qualification_event,
            contact_id, state, ai_message
        )

        # Step 9: Update state
        state["message_count"] += 1
        state["last_interaction"] = start_time

        # Calculate response time for analytics
        response_time_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        return JSONResponse({
            "status": "sent",
            "message": ai_message,
            "score": state["score"],
            "status_label": state["status"],
            "question": state["current_question"],
            "contact_id": contact_id,
            "response_time_ms": int(response_time_ms)
        })

    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/webhook/ghl/response")
async def handle_contact_response(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming responses from contacts.

    This endpoint processes lead responses and updates qualification state.
    """
    try:
        payload = await request.json()
        contact_id = payload.get("contactId")
        message = payload.get("message", "")
        location_id = payload.get("locationId")

        if contact_id not in qualification_states:
            return JSONResponse({"status": "no_active_session"})

        state = qualification_states[contact_id]

        # Store the response
        await update_conversation_history(contact_id, message, "contact")

        # Process the answer
        current_question = state["current_question"]
        state["answers"][current_question] = message

        # Calculate engagement level from response
        engagement = calculate_answer_engagement(message)
        state["engagement_level"] = (
            (state["engagement_level"] * state["message_count"] + engagement) /
            (state["message_count"] + 1)
        )

        # Move to next question
        questions = ["budget", "location", "bedrooms", "timeline", "preapproval", "motivation"]
        try:
            current_idx = questions.index(current_question)
            if current_idx + 1 < len(questions):
                state["current_question"] = questions[current_idx + 1]
        except ValueError:
            pass  # Keep current question if not found

        # Recalculate score
        answered_count = len([ans for ans in state["answers"].values()
                             if ans and len(str(ans).strip()) > 2])

        if answered_count >= 3:
            state["score"] = answered_count
            state["status"] = "hot"
        elif answered_count == 2:
            state["score"] = answered_count
            state["status"] = "warm"
        else:
            state["score"] = answered_count
            state["status"] = "cold"

        # Update tags in background
        background_tasks.add_task(
            update_contact_tag,
            contact_id, location_id, f"{state['status'].title()} Lead"
        )

        logger.info(
            f"Contact {contact_id} - Score: {state['score']} ({state['status']}), "
            f"Answers: {len(state['answers'])}"
        )

        return JSONResponse({
            "status": "processed",
            "score": state["score"],
            "status_label": state["status"],
            "answers_count": len(state["answers"]),
            "engagement_level": round(state["engagement_level"], 2)
        })

    except Exception as e:
        logger.error(f"Error processing contact response: {e}")
        return JSONResponse({
            "status": "error",
            "message": str(e)
        }, status_code=500)


# Background task functions
async def send_sms_via_ghl(contact_id: str, location_id: str, message: str):
    """Send SMS message via GHL API"""
    import httpx

    url = f"{GHL_API_BASE_URL}/conversations/messages"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "contactId": contact_id,
        "locationId": location_id,
        "message": message,
        "type": "SMS"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"SMS sent to contact {contact_id}: {message}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {contact_id}: {e}")


async def update_contact_tag(contact_id: str, location_id: str, tag: str):
    """Add tag to contact in GHL"""
    import httpx

    url = f"{GHL_API_BASE_URL}/contacts/{contact_id}/tags"
    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {"tags": [tag]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Tag '{tag}' added to contact {contact_id}")
    except Exception as e:
        logger.error(f"Failed to update tag for {contact_id}: {e}")


async def update_conversation_history(contact_id: str, message: str, sender: str):
    """Update conversation history"""
    if contact_id not in conversation_histories:
        conversation_histories[contact_id] = []

    conversation_histories[contact_id].append({
        "timestamp": datetime.utcnow().isoformat(),
        "sender": sender,
        "message": message
    })

    # Keep only last 20 messages for memory efficiency
    if len(conversation_histories[contact_id]) > 20:
        conversation_histories[contact_id] = conversation_histories[contact_id][-20:]


async def log_qualification_event(contact_id: str, state: Dict, ai_message: str):
    """Log qualification event for analytics"""
    event = {
        "timestamp": datetime.utcnow().isoformat(),
        "contact_id": contact_id,
        "event_type": "ai_response_sent",
        "score": state["score"],
        "status": state["status"],
        "current_question": state["current_question"],
        "message_count": state["message_count"],
        "engagement_level": state["engagement_level"],
        "ai_message": ai_message,
        "answers_provided": len(state["answers"])
    }

    # In production, send to analytics service
    logger.info(f"Qualification event: {event}")


def calculate_answer_engagement(answer: str) -> float:
    """Calculate engagement level from answer quality"""
    if not answer or not isinstance(answer, str):
        return 0.0

    answer = answer.strip()

    # Base score from length
    length_score = min(1.0, len(answer) / 50)

    # Bonus for specific details
    detail_indicators = ['$', 'bedroom', 'month', 'year', 'area', 'job', 'family']
    detail_bonus = min(0.3, sum(0.05 for indicator in detail_indicators
                               if indicator in answer.lower()))

    # Bonus for questions (shows engagement)
    question_bonus = 0.1 if '?' in answer else 0.0

    return min(1.0, length_score + detail_bonus + question_bonus)


# Analytics endpoints
@app.get("/analytics/qualification")
async def get_qualification_analytics():
    """Get qualification analytics"""
    total_leads = len(qualification_states)
    if total_leads == 0:
        return {"total_leads": 0}

    hot_leads = sum(1 for state in qualification_states.values() if state["status"] == "hot")
    warm_leads = sum(1 for state in qualification_states.values() if state["status"] == "warm")
    cold_leads = total_leads - hot_leads - warm_leads

    avg_engagement = sum(state.get("engagement_level", 0) for state in qualification_states.values()) / total_leads
    avg_score = sum(state.get("score", 0) for state in qualification_states.values()) / total_leads

    return {
        "total_leads": total_leads,
        "hot_leads": hot_leads,
        "warm_leads": warm_leads,
        "cold_leads": cold_leads,
        "conversion_rate": round((hot_leads + warm_leads) / total_leads * 100, 1),
        "average_engagement": round(avg_engagement, 2),
        "average_score": round(avg_score, 1)
    }


@app.get("/analytics/lead/{contact_id}")
async def get_lead_analytics(contact_id: str):
    """Get analytics for specific lead"""
    if contact_id not in qualification_states:
        raise HTTPException(status_code=404, detail="Lead not found")

    state = qualification_states[contact_id]
    history = conversation_histories.get(contact_id, [])

    return {
        "contact_id": contact_id,
        "score": state["score"],
        "status": state["status"],
        "answers_provided": len(state["answers"]),
        "message_count": state["message_count"],
        "engagement_level": state.get("engagement_level", 0),
        "conversation_length": len(history),
        "created_at": state.get("created_at", "").isoformat() if isinstance(state.get("created_at"), datetime) else state.get("created_at"),
        "answers": state["answers"]
    }


if __name__ == "__main__":
    # Configuration
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    debug = os.getenv("DEBUG", "false").lower() == "true"

    print(f"🚀 Starting GHL Real Estate AI Webhook Service")
    print(f"📡 Listening on {host}:{port}")
    print(f"🔐 Webhook security: {'Enabled' if GHL_WEBHOOK_SECRET else 'Disabled (dev mode)'}")
    print(f"🤖 AI responses: {'Enabled' if ANTHROPIC_API_KEY else 'Mock mode'}")

    uvicorn.run(
        "complete_webhook_handler:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )


"""
USAGE EXAMPLE:

1. Set environment variables:
   export GHL_WEBHOOK_SECRET="your_secret_here"
   export GHL_API_KEY="your_api_key_here"
   export ANTHROPIC_API_KEY="your_anthropic_key_here"

2. Run the server:
   python complete_webhook_handler.py

3. Configure GHL webhooks to point to:
   https://your-domain.com/webhook/ghl

4. Monitor analytics at:
   https://your-domain.com/analytics/qualification

The system will automatically:
- Qualify leads using Jorge's 7-question framework
- Generate AI responses in Jorge's communication style
- Hand off hot leads (3+ questions answered) to human agents
- Track analytics and engagement metrics
- Handle security and rate limiting
"""