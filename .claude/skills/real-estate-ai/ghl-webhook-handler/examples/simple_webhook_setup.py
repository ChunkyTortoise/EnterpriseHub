#!/usr/bin/env python3
"""
Simple GHL Webhook Setup Example
Minimal implementation for getting started with lead qualification

This example shows the simplest way to implement Jorge's lead qualification
system with just the essential components.
"""

import os
import hashlib
import hmac
from datetime import datetime
from typing import Dict

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse

# Simple in-memory storage (use database in production)
leads = {}

app = FastAPI(title="Simple GHL Lead Qualifier")

# Environment configuration
WEBHOOK_SECRET = os.getenv("GHL_WEBHOOK_SECRET", "your-secret-here")


def verify_signature(request: Request, body: bytes) -> bool:
    """Verify webhook came from GoHighLevel"""
    signature = request.headers.get("X-GHL-Signature", "")
    if not WEBHOOK_SECRET or not signature:
        return False

    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(signature, expected)


def score_lead(answers: Dict[str, str]) -> tuple[int, str]:
    """
    Jorge's simple scoring: count meaningful answers

    Hot: 3+ questions answered
    Warm: 2 questions answered
    Cold: 1 or less answered
    """
    meaningful_answers = 0

    for answer in answers.values():
        if answer and len(str(answer).strip()) > 2:
            meaningful_answers += 1

    if meaningful_answers >= 3:
        return meaningful_answers, "hot"
    elif meaningful_answers == 2:
        return meaningful_answers, "warm"
    else:
        return meaningful_answers, "cold"


@app.post("/webhook")
async def handle_webhook(request: Request):
    """Main webhook handler"""

    # Security check
    body = await request.body()
    if not verify_signature(request, body):
        raise HTTPException(status_code=401, detail="Invalid signature")

    # Parse webhook data
    data = await request.json()
    contact_id = data.get("contactId")

    if not contact_id:
        raise HTTPException(status_code=400, detail="Missing contact ID")

    # Initialize or get lead state
    if contact_id not in leads:
        leads[contact_id] = {
            "answers": {},
            "current_question": "budget",
            "score": 0,
            "status": "cold"
        }

    lead = leads[contact_id]

    # Check if already qualified
    if lead["status"] == "hot":
        return JSONResponse({
            "status": "qualified",
            "message": "Thanks! A team member will contact you soon."
        })

    # Determine next question
    questions = {
        "budget": "What's your budget range?",
        "location": "Which areas interest you?",
        "bedrooms": "How many bedrooms?",
        "timeline": "When do you want to move?",
        "preapproval": "Are you pre-approved?",
        "motivation": "What's driving your decision?"
    }

    current_q = lead["current_question"]
    message = questions.get(current_q, "Tell me more about what you're looking for.")

    return JSONResponse({
        "status": "question",
        "message": message,
        "score": lead["score"],
        "classification": lead["status"]
    })


@app.post("/webhook/response")
async def handle_response(request: Request):
    """Handle lead responses to questions"""

    data = await request.json()
    contact_id = data.get("contactId")
    message = data.get("message", "")

    if contact_id not in leads:
        return JSONResponse({"status": "no_session"})

    lead = leads[contact_id]

    # Store answer
    current_q = lead["current_question"]
    lead["answers"][current_q] = message

    # Move to next question
    questions = ["budget", "location", "bedrooms", "timeline", "preapproval", "motivation"]
    try:
        current_idx = questions.index(current_q)
        if current_idx + 1 < len(questions):
            lead["current_question"] = questions[current_idx + 1]
    except ValueError:
        pass

    # Update score
    score, status = score_lead(lead["answers"])
    lead["score"] = score
    lead["status"] = status

    return JSONResponse({
        "status": "updated",
        "score": score,
        "classification": status
    })


@app.get("/")
def health_check():
    """Health check"""
    return {
        "service": "Simple GHL Lead Qualifier",
        "version": "1.0",
        "leads_tracked": len(leads)
    }


@app.get("/leads/{contact_id}")
def get_lead_status(contact_id: str):
    """Get lead qualification status"""
    if contact_id not in leads:
        raise HTTPException(status_code=404, detail="Lead not found")

    lead = leads[contact_id]
    return {
        "contact_id": contact_id,
        "score": lead["score"],
        "status": lead["status"],
        "answers": lead["answers"],
        "next_question": lead["current_question"]
    }


if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Simple GHL Lead Qualifier")
    print("📋 Jorge's 7-Question System Active")
    print(f"🔐 Security: {'ON' if WEBHOOK_SECRET else 'OFF'}")

    uvicorn.run(app, host="0.0.0.0", port=8000)


"""
SETUP INSTRUCTIONS:

1. Install dependencies:
   pip install fastapi uvicorn

2. Set your webhook secret:
   export GHL_WEBHOOK_SECRET="your_secret_from_ghl"

3. Run the server:
   python simple_webhook_setup.py

4. Configure GHL webhook to POST to:
   https://your-domain.com/webhook

5. Test with a simple curl request:
   curl -X POST http://localhost:8000/webhook/response \
     -H "Content-Type: application/json" \
     -d '{"contactId": "test123", "message": "500k budget"}'

EXPECTED WORKFLOW:

1. Lead comes in → webhook triggers
2. System asks: "What's your budget range?"
3. Lead responds: "Around 500k"
4. System asks: "Which areas interest you?"
5. Lead responds: "Rancho Cucamonga downtown"
6. System asks: "How many bedrooms?"
7. Lead responds: "3 bedrooms"

After 3 meaningful answers → Lead marked as "HOT"

LEAD SCORING:
- HOT (3+): Ready for agent handoff
- WARM (2): Continue nurturing
- COLD (≤1): Needs more engagement

This simple version handles the core qualification logic
without the complexity of AI responses or advanced features.
"""