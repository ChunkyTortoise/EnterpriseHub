"""
GHL Webhook Service - Path B Backend Integration
Handles webhook triggers from GoHighLevel for lead qualification
"""

import hashlib
import hmac
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import anthropic
import asyncio
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

# Jorge System 3.0 - Phase 5: Autonomous Expansion
# Import the Cleaner agent logic (Self-Healing Data Pipeline)
try:
    from ghl_real_estate_ai.agents.agent_swarm_orchestrator_v2 import AgentSwarmOrchestratorV2
    cleaner_orchestrator = AgentSwarmOrchestratorV2()
except ImportError:
    cleaner_orchestrator = None

# Phase 7: Autonomous Integration Orchestrator
try:
    from ghl_real_estate_ai.services.autonomous_integration_orchestrator import get_autonomous_integration_orchestrator
    orchestrator = get_autonomous_integration_orchestrator()
    asyncio.create_task(orchestrator.initialize_system())
except ImportError:
    orchestrator = None

# Phase 7: Model Retraining
try:
    from ghl_real_estate_ai.services.model_retraining_service import get_retraining_service
    retraining_service = get_retraining_service()
except ImportError:
    retraining_service = None

# Phase 7: Global Compliance Enforcer
from ghl_real_estate_ai.compliance_platform.engine.policy_enforcer import PolicyEnforcer
from ghl_real_estate_ai.services.agent_state_sync import sync_service

# Phase 7: Lead Bot V2 Intelligence
from ghl_real_estate_ai.services.autonomous_objection_handler import get_autonomous_objection_handler
from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler
from ghl_real_estate_ai.services.market_timing_opportunity_intelligence import MarketTimingOpportunityEngine

compliance_enforcer = PolicyEnforcer()
objection_handler = get_autonomous_objection_handler()
calendar_scheduler = get_smart_scheduler()
market_engine = MarketTimingOpportunityEngine()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="GHL Real Estate AI Webhook Service",
    description="AI-powered lead qualification for Jorge Sales",
    version="1.0.0",
)

# Initialize Anthropic client
anthropic_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Configuration
GHL_WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "")
GHL_API_KEY = os.getenv("GHL_API_KEY", "")
GHL_API_BASE_URL = "https://rest.gohighlevel.com/v1"

# Jorge's Qualification Criteria (from CLIENT CLARIFICATION)
QUALIFICATION_QUESTIONS = {
    "budget": "What's your budget range for this property?",
    "location": "Which neighborhoods or areas are you interested in?",
    "bedrooms": "How many bedrooms are you looking for?",
    "timeline": "When are you hoping to buy or sell?",
    "preapproval": "Are you pre-approved for a mortgage?",
    "motivation": "What's motivating your decision to buy/sell right now?",
    "seller_condition": "What's the current condition of your home?",  # For sellers
}


# Jorge's Lead Scoring Logic
def calculate_lead_score(answers: Dict[str, Any]) -> tuple[int, str]:
    """
    Calculate lead score based on Jorge's criteria:
    - Hot: 3+ qualifying questions answered
    - Warm: 2 qualifying questions answered
    - Cold: 1 or less qualifying questions answered
    """
    answered_count = sum(1 for v in answers.values() if v)

    if answered_count >= 3:
        return 85, "Hot"  # Score 85 = Hot Lead
    elif answered_count == 2:
        return 60, "Warm"  # Score 60 = Warm Lead
    else:
        return 25, "Cold"  # Score 25 = Cold Lead


class GHLWebhookPayload(BaseModel):
    """GHL webhook payload structure"""

    contactId: str
    locationId: str
    tags: Optional[List[str]] = []
    customFields: Optional[Dict[str, Any]] = {}
    type: str  # "ContactTagUpdate", "ContactFieldUpdate", etc.


class LeadQualificationState(BaseModel):
    """Track lead qualification progress"""

    contact_id: str
    current_question: str = "budget"
    answers: Dict[str, Any] = Field(default_factory=dict)
    message_count: int = 0
    score: int = 0
    status: str = "Cold"


# In-memory state (in production, use Redis or database)
qualification_states: Dict[str, LeadQualificationState] = {}


def verify_webhook_signature(request: Request, body: bytes) -> bool:
    """Verify GHL webhook signature for security"""
    if not GHL_WEBHOOK_SECRET:
        logger.warning("GHL_WEBHOOK_SECRET not set - skipping verification in dev mode")
        return True

    signature = request.headers.get("X-GHL-Signature", "")
    computed = hmac.new(GHL_WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()

    return hmac.compare_digest(signature, computed)


def get_ai_response(
    contact_data: Dict, conversation_history: List, question_type: str
) -> str:
    """
    Generate AI response using Claude with Jorge's tone:
    Professional, friendly, direct, and curious
    """

    system_prompt = """You are an AI assistant for Jorge Sales, a professional real estate agent. 
Your communication style is:
- Professional and friendly
- Direct and to-the-point (SMS-optimized, under 160 characters)
- Curious and genuinely interested
- Never robotic or overly formal

Examples of Jorge's tone:
- "Hey, are you actually still looking to sell or should we close your file?"
- "Hey [name] just checking in, is it still a priority of yours to buy or have you given up?"

Your goal is to qualify leads by asking the right questions naturally in conversation.
Keep responses SHORT (1-2 sentences max). This is SMS, not email.
"""

    # Build conversation context
    messages = []
    for msg in conversation_history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    # Add current question based on what we need to know
    if question_type == "budget":
        question = "Quick question - what's your budget range looking like?"
    elif question_type == "location":
        question = "Got it. Which neighborhoods are you eyeing?"
    elif question_type == "bedrooms":
        question = "How many bedrooms do you need?"
    elif question_type == "timeline":
        question = "When are you hoping to make a move?"
    elif question_type == "preapproval":
        question = "Are you pre-approved or do you need a lender recommendation?"
    elif question_type == "motivation":
        question = "Just curious - what's driving the decision right now?"
    else:
        question = "Thanks for that info. Anything else I should know?"

    messages.append(
        {
            "role": "user",
            "content": f"Generate a natural follow-up question to ask about: {question_type}. Keep it under 160 chars.",
        }
    )

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            system=system_prompt,
            messages=messages,
        )

        return response.content[0].text.strip()

    except Exception as e:
        logger.error(f"Anthropic API error: {e}")
        # Fallback to direct question
        return question


async def safe_send_sms(contact_id: str, location_id: str, message: str, agent_name: str = "AI Assistant"):
    """
    Checks message for compliance and sends via GHL if allowed.
    Logs activity to the dashboard live feed.
    """
    # 1. Compliance Check (FHA)
    compliance = await compliance_enforcer.intercept_message(message)
    if not compliance["allowed"]:
        logger.warning(f"🚫 BLOCKED non-compliant message for {contact_id}: {compliance['violations']}")
        # Log to dashboard
        await sync_service.record_agent_thought(
            "ComplianceBot", 
            f"BLOCKED: FHA violation for {contact_id}. Suggestion: {compliance['suggestion']}", 
            "Error"
        )
        return

    # 2. Log successful delivery attempt to dashboard
    await sync_service.record_agent_thought(agent_name, f"Sending message to {contact_id}: {message[:50]}...")

    # 3. Send via GHL
    await send_sms_via_ghl(contact_id, location_id, message)


async def send_sms_via_ghl(contact_id: str, location_id: str, message: str):
    """Send SMS message via GHL API"""
    import httpx

    url = f"{GHL_API_BASE_URL}/conversations/messages"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "contactId": contact_id,
        "locationId": location_id,
        "message": message,
        "type": "SMS",
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"SMS sent to contact {contact_id}")
            return response.json()

    except Exception as e:
        logger.error(f"Failed to send SMS: {e}")
        raise


async def update_contact_tag(contact_id: str, location_id: str, tag: str):
    """Add tag to contact in GHL"""
    import httpx

    url = f"{GHL_API_BASE_URL}/contacts/{contact_id}/tags"

    headers = {
        "Authorization": f"Bearer {GHL_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {"tags": [tag]}

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            logger.info(f"Tag '{tag}' added to contact {contact_id}")

    except Exception as e:
        logger.error(f"Failed to update tag: {e}")


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "service": "GHL Real Estate AI Webhook",
        "status": "active",
        "version": "1.0.0",
        "for": "Jorge Sales",
    }


@app.post("/webhook/ghl")
async def handle_ghl_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Main webhook endpoint for GHL triggers

    Trigger conditions (from Jorge's clarification):
    - Contact tagged "AI Assistant: ON"
    - Disengagement when score >= 70
    """

    # Verify webhook signature
    body = await request.body()
    if not verify_webhook_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")

    # Parse payload
    try:
        payload = await request.json()
        logger.info(f"Received webhook: {payload}")
        
        # Phase 5: Self-Healing Data Pipeline (The Cleaner)
        if cleaner_orchestrator:
            logger.info("Triggering 'The Cleaner' agent for data standardization...")
            payload = await cleaner_orchestrator.run_cleaner(payload)
            logger.info(f"Cleaned payload: {payload}")
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    contact_id = payload.get("contactId")
    location_id = payload.get("locationId")
    tags = payload.get("tags", [])
    hook_type = payload.get("type")

    # Phase 7: Handle Opportunity Status Changes for Retraining
    if hook_type == "OpportunityStatusUpdate" and retraining_service:
        status = payload.get("status", "").lower()
        value = float(payload.get("monetaryValue", 0.0))
        if status in ["won", "lost", "abandoned"]:
            logger.info(f"🎯 Capturing outcome for retraining: {contact_id} -> {status}")
            background_tasks.add_task(retraining_service.record_outcome, contact_id, status, value)
            return JSONResponse({"status": "outcome_recorded"})

    # Check if AI should engage
    ai_on = "AI Assistant: ON" in tags or "ai_on" in tags
    ai_off = "AI Assistant: OFF" in tags or "ai_off" in tags

    if ai_off or not ai_on:
        logger.info(f"AI not engaged for contact {contact_id} - tags: {tags}")
        return JSONResponse({"status": "skipped", "reason": "AI not enabled"})

    # Phase 7: Autonomous Processing via Orchestrator
    if orchestrator:
        logger.info(f"🚀 Processing lead {contact_id} via Autonomous Integration Orchestrator (Phase 7)")
        # Map GHL payload to expected activity data
        activity_data = {
            "tags": tags,
            "customFields": payload.get("customFields", {}),
            "type": payload.get("type")
        }
        # In GHL webhooks, the message is often in customFields or another field depending on trigger
        recent_messages = [payload.get("message", "")] if payload.get("message") else []
        
        results = await orchestrator.process_lead_comprehensive(
            lead_id=contact_id,
            activity_data=activity_data,
            context={"location_id": location_id, "recent_messages": recent_messages}
        )
        
        # Phase 7: Regional Compliance Audit
        from ghl_real_estate_ai.agents.regional_compliance_agent import get_compliance_agent
        compliance = get_compliance_agent()
        # Region could be determined from location_id or custom field
        region = payload.get("customFields", {}).get("region", "TX")
        
        # Check if an automated response was generated
        objection_result = results.get("component_results", {}).get("objection_handling", {})
        if objection_result.get("objection_detected") and objection_result.get("suggested_response"):
            ai_message = objection_result["suggested_response"]
            
            # Compliance check before sending
            warnings = compliance.audit_message(ai_message, region)
            if warnings:
                logger.warning(f"⚠️ Compliance Warning for lead {contact_id}: {warnings}")
                # In strict mode, we might block the message here. 
                # For now, we log and proceed with Jorge's approval.

            background_tasks.add_task(safe_send_sms, contact_id, location_id, ai_message, "Orchestrator")
            return JSONResponse({"status": "responded_to_objection", "message": ai_message})

    # Phase 7: Lead Bot V2 Intelligence Flow
    lead_message = payload.get("message", {}).get("body", "")
    lead_name = payload.get("contact", {}).get("firstName", "there")
    custom_fields = payload.get("customFields", {})
    
    # 1. Autonomous Objection Resolution
    if lead_message:
        obj_response = await objection_handler.handle_objection_flow(
            contact_id, lead_message, {"name": lead_name, "custom_fields": custom_fields}
        )
        if obj_response and obj_response.confidence_score > 0.8:
            logger.info(f"✅ Auto-resolved objection for {contact_id}: {obj_response.analysis.category}")
            background_tasks.add_task(safe_send_sms, contact_id, location_id, obj_response.generated_message, "ObjectionBot")
            return JSONResponse({"status": "objection_resolved", "message": obj_response.generated_message})

    # 2. Get or create qualification state
    if contact_id not in qualification_states:
        qualification_states[contact_id] = LeadQualificationState(contact_id=contact_id)

    state = qualification_states[contact_id]

    # 3. Proactive Scheduling for Hot Leads
    if state.score >= 70 or "Hot Lead" in tags:
        contact_info = {
            "contact_id": contact_id,
            "first_name": lead_name,
            "phone": payload.get("contact", {}).get("phone"),
            "email": payload.get("contact", {}).get("email")
        }
        extracted_data = {
            "budget": custom_fields.get("budget"),
            "location": custom_fields.get("location"),
            "motivation": custom_fields.get("motivation"),
            "timeline": custom_fields.get("timeline")
        }
        
        booked, booking_msg, booking_actions = await calendar_scheduler.handle_appointment_request(
            contact_id, contact_info, state.score // 10, extracted_data, lead_message
        )
        
        if booked:
            logger.info(f"📅 Proactive scheduling triggered for {contact_id}")
            background_tasks.add_task(safe_send_sms, contact_id, location_id, booking_msg, "SchedulerBot")
            # Apply GHL actions (tags, etc.) if any
            if booking_actions:
                from ghl_real_estate_ai.services.ghl_client import GHLClient
                ghl = GHLClient()
                background_tasks.add_task(ghl.apply_actions, contact_id, booking_actions)
            
            return JSONResponse({"status": "appointment_offered", "message": booking_msg})

    # 4. Investor "Prime Arbitrage" Pitch
    if "investor" in str(tags).lower() or "investor" in str(custom_fields.get("motivation")).lower():
        market_area = custom_fields.get("region", "austin").lower()
        opportunities = await market_engine.identify_investment_opportunities(
            client_budget=float(custom_fields.get("budget", 500000)),
            risk_tolerance="medium",
            investment_goals=["appreciation", "arbitrage"],
            time_horizon="1_year"
        )
        if opportunities:
            best_opp = opportunities[0]
            pitch = f"Hey {lead_name}, I just analyzed the {market_area} market and found a {best_opp.opportunity_type.value} opportunity with a projected {best_opp.roi_estimate}% ROI. Are you interested in the details?"
            background_tasks.add_task(safe_send_sms, contact_id, location_id, pitch, "MarketBot")
            return JSONResponse({"status": "investor_pitch_sent", "message": pitch})

    # Check if we should disengage (score >= 70) - Original logic fallback
    if state.score >= 70:
        logger.info(
            f"Lead {contact_id} is HOT (score: {state.score}) - handing off to human"
        )

        # Tag as "Hot Lead" in GHL
        background_tasks.add_task(
            update_contact_tag, contact_id, location_id, "Hot Lead"
        )

        # Turn off AI
        background_tasks.add_task(
            update_contact_tag, contact_id, location_id, "AI Assistant: OFF"
        )

        # Send handoff message
        handoff_msg = "Thanks for all the info! A team member will reach out shortly to help you. 🎉"
        background_tasks.add_task(
            safe_send_sms, contact_id, location_id, handoff_msg, "System"
        )

        return JSONResponse(
            {"status": "handoff", "score": state.score, "status_label": state.status}
        )

    # Generate next qualifying question
    conversation_history = []  # In production, load from DB

    ai_message = get_ai_response(payload, conversation_history, state.current_question)

    # Send SMS via GHL
    background_tasks.add_task(safe_send_sms, contact_id, location_id, ai_message, "SalesBot")

    # Update state
    state.message_count += 1

    return JSONResponse(
        {
            "status": "sent",
            "message": ai_message,
            "score": state.score,
            "question": state.current_question,
        }
    )


@app.post("/webhook/ghl/response")
async def handle_contact_response(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming responses from contacts
    Extract answers and update lead score
    """

    payload = await request.json()
    contact_id = payload.get("contactId")
    message = payload.get("message", "")
    location_id = payload.get("locationId")

    if contact_id not in qualification_states:
        return JSONResponse({"status": "no_active_session"})

    state = qualification_states[contact_id]

    # Store answer (in production, use NLP to extract structured data)
    state.answers[state.current_question] = message

    # Move to next question
    questions = list(QUALIFICATION_QUESTIONS.keys())
    current_idx = questions.index(state.current_question)

    if current_idx + 1 < len(questions):
        state.current_question = questions[current_idx + 1]

    # Recalculate score
    score, status = calculate_lead_score(state.answers)
    state.score = score
    state.status = status

    # Update GHL tags based on status
    if status == "Hot":
        background_tasks.add_task(
            update_contact_tag, contact_id, location_id, "Hot Lead"
        )
    elif status == "Warm":
        background_tasks.add_task(
            update_contact_tag, contact_id, location_id, "Warm Lead"
        )
    else:
        background_tasks.add_task(
            update_contact_tag, contact_id, location_id, "Cold Lead"
        )

    logger.info(
        f"Contact {contact_id} - Score: {score} ({status}), Answers: {len(state.answers)}"
    )

    return JSONResponse(
        {
            "status": "processed",
            "score": score,
            "status_label": status,
            "answers_count": len(state.answers),
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
