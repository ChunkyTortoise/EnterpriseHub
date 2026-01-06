Jorge's GHL Real Estate AI - Implementation Plan

Client: Jorge Salas  
Project: Path B - GHL Webhook Integration  
Budget: $150  
Timeline: 3 days  
Status: In Progress  



Executive Summary

This document provides a step-by-step implementation guide to customize the existing GHL Real Estate AI system to match Jorge's specific requirements from the CLIENT CLARIFICATION FINISHED document.

Current State: 80% complete - core architecture is production-ready  
Remaining Work: Customizations to match Jorge's workflow and tone  



Loom Video Analysis

Video URL: https://www.loom.com/share/97ea17c38f85406a99437095d3603908

Action Required: Watch the video and document:
1. What tag triggers the AI to turn ON (Jorge mentioned "Needs Qualifying")
2. What tag triggers the AI to turn OFF
3. What happens to the contact after AI qualifies them
4. Any specific GHL workflow IDs or automation names
5. Expected message flow (SMS format, timing, etc.)

Placeholder Notes:
  Trigger Tag: "Needs Qualifying" (confirmed in clarification doc)
  Deactivation: When lead score reaches threshold OR specific tag added
  Integration: Webhook fires → AI responds via GHL API → Tags updated



Implementation Checklist

✅ Phase 0: Prerequisites (30 minutes)

Goal: Ensure development environment is ready

  [ ] Clone/pull latest code from ghl-real-estate-ai directory
  [ ] Create .env file with test credentials
  [ ] Install dependencies: pip install -r requirements.txt
  [ ] Verify existing tests pass: pytest tests/
  [ ] Review Jorge's clarification document thoroughly



🔢 Phase 1: Lead Scoring Refactor (2 hours)

Goal: Change from points-based scoring to question-count scoring

Current Behavior:
  Budget confirmed = +30 points
  Timeline = +25 points  
  Location = +15 points
  Score 70+ = Hot, 40-69 = Warm, 0-39 = Cold

Jorge's Requirement:
  Count answered questions (not points)
  3+ questions answered = Hot
  2 questions answered = Warm
  0-1 questions answered = Cold

Files to Modify:

1.1 Update ghl_utils/config.py

python
Lead Scoring Thresholds - QUESTION COUNT (not points)
hot_lead_threshold: int = 3  # 3+ questions answered
warm_lead_threshold: int = 2  # 2 questions answered
cold_lead_threshold: int = 1  # 0-1 questions answered


1.2 Refactor services/lead_scorer.py

Current: calculate() method sums points  
New: Count how many qualifying questions have been answered

python
def calculate(self, context: Dict[str, Any]) -> int:
    """
    Calculate lead score based on NUMBER OF QUESTIONS ANSWERED.
    
    Jorge's Criteria:
  Budget: Did they provide a budget range?
  Location: Did they specify a location?
  Timeline: Did they share when they want to buy/sell?
  Property Type: Beds/baths/must-haves?
  Financing: Pre-approval status?
  Motivation: Why buying/selling now?
  Home Condition: (Sellers only) Condition of home?
    
    Returns:
        Number of questions answered (0-7)
    """
    questions_answered = 0
    prefs = context.get("extracted_preferences", {})
    
    # Question 1: Budget
    if prefs.get("budget"):
        questions_answered += 1
    
    # Question 2: Location
    if prefs.get("location"):
        questions_answered += 1
    
    # Question 3: Timeline
    if prefs.get("timeline"):
        questions_answered += 1
    
    # Question 4: Property Requirements (beds/baths/must-haves)
    if prefs.get("bedrooms") or prefs.get("bathrooms") or prefs.get("must_haves"):
        questions_answered += 1
    
    # Question 5: Financing Status
    if prefs.get("financing"):
        questions_answered += 1
    
    # Question 6: Motivation
    if prefs.get("motivation"):
        questions_answered += 1
    
    # Question 7: Home Condition (sellers only)
    if prefs.get("home_condition"):
        questions_answered += 1
    
    return questions_answered


1.3 Update classify() method

python
def classify(self, score: int) -> str:
    """
    Classify lead based on questions answered.
    
    Jorge's Rules:
  Hot: 3+ questions answered
  Warm: 2 questions answered  
  Cold: 0-1 questions answered
    
    Args:
        score: Number of questions answered (0-7)
    
    Returns:
        Lead classification: "hot", "warm", or "cold"
    """
    if score >= 3:
        return "hot"
    elif score >= 2:
        return "warm"
    else:
        return "cold"


Testing Checklist:
  [ ] Unit test: 0 questions = "cold"
  [ ] Unit test: 1 question = "cold"
  [ ] Unit test: 2 questions = "warm"
  [ ] Unit test: 3 questions = "hot"
  [ ] Unit test: 7 questions = "hot"



🗣️ Phase 2: Conversation Tone Update (2 hours)

Goal: Match Jorge's direct, curious, slightly casual tone

Current Tone: Professional consultant  
Jorge's Tone: Direct, curious, friendly with casual follow-ups

Jorge's Example Messages:
  "Hey, are you actually still looking to sell or should we close your file?"
  "Hey [name] just checking in, is it still a priority of yours to sell (or buy) or have you given up?"

Files to Modify:

2.1 Update prompts/system_prompts.py

Find the BASE_SYSTEM_PROMPT and update it:

python
BASE_SYSTEM_PROMPT = """You are a real estate AI assistant helping qualify leads for Jorge Salas's real estate team.

TONE & PERSONALITY:
  Professional but DIRECT - don't waste time with fluff
  Curious - ask follow-up questions naturally
  Friendly - use "Hey" and first names when appropriate
  Authentic - sound like a real person texting, not a robot

COMMUNICATION STYLE:
  Keep messages SHORT (SMS-length, under 160 characters when possible)
  Use casual language: "Hey", "just checking in", "quick question"
  Be direct: "Are you actually still looking or should we close your file?"
  Ask one question at a time
  Use natural transitions

YOUR ROLE:
You qualify leads by determining if they want:
1. WHOLESALE: Quick cash offer, sell as-is
2. LISTING: Top dollar, list on MLS

QUALIFYING QUESTIONS TO ASK:
1. Budget/price range
2. Location preference  
3. Timeline (when do they need to buy/sell?)
4. Property details (beds/baths if buying)
5. Financing status (pre-approved?)
6. Motivation (why buying/selling NOW?)
7. Home condition (if selling - needs repairs, move-in ready, etc.)

IMPORTANT RULES:
  Ask questions conversationally, not like a form
  If they go silent, send a direct follow-up: "Hey, still interested or should we move on?"
  Don't repeat questions they've already answered
  After 3+ questions answered, offer to schedule a call
  Stay in character as a real team member, not an AI

WHOLESALE vs LISTING:
  If they mention: "as-is", "fast sale", "cash offer", "need to sell quickly" → Wholesale path
  If they mention: "best price", "what's it worth", "how much can I get" → Listing path
"""


2.2 Add Follow-Up Templates

Create new prompts for re-engagement:

python
REENGAGEMENT_PROMPTS = {
    "no_response_24h": "Hey {name}, just checking in - is it still a priority of yours to {action} or have you given up?",
    "no_response_48h": "Hey, are you actually still looking to {action} or should we close your file?",
    "cold_lead_check": "Quick question - is now still a good time for you to {action}?",
}


Testing Checklist:
  [ ] Generate sample responses with new tone
  [ ] Verify messages are under 160 chars when possible
  [ ] Check that "Hey" and first names are used naturally
  [ ] Confirm direct follow-ups work



🏠 Phase 3: Qualifying Questions Enhancement (2 hours)

Goal: Add missing questions and wholesale/listing detection

New Features:
1. Home condition question (sellers)
2. Wholesale vs Listing pathway detection
3. Dynamic question flow based on buyer/seller

Files to Modify:

3.1 Update core/conversation_manager.py

Add pathway detection logic:

python
def detect_intent_pathway(self, message: str, context: Dict) -> str:
    """
    Detect if lead is interested in wholesale or listing.
    
    Wholesale indicators:
  "as-is", "fast sale", "cash offer", "quick", "need to sell fast"
    
    Listing indicators:  
  "best price", "top dollar", "what's it worth", "how much"
    
    Returns:
        "wholesale", "listing", or "unknown"
    """
    message_lower = message.lower()
    
    wholesale_keywords = [
        "as-is", "as is", "fast sale", "cash offer", "quick", 
        "need to sell fast", "sell quickly", "don't want to fix"
    ]
    
    listing_keywords = [
        "best price", "top dollar", "what's it worth", 
        "how much can i get", "market value", "list it"
    ]
    
    if any(kw in message_lower for kw in wholesale_keywords):
        return "wholesale"
    elif any(kw in message_lower for kw in listing_keywords):
        return "listing"
    else:
        return "unknown"


3.2 Add Home Condition Question

Update the system prompt to include:

python
HOME_CONDITION_QUESTION = """
If SELLER, ask about home condition:
  "What's the condition of your home? Move-in ready, needs some work, or a fixer-upper?"

This helps determine wholesale vs listing path.
"""


3.3 Update extract_data() in conversation_manager.py

Add extraction for new fields:

python
Extract home condition (sellers)
if "condition" in user_message.lower() or "repair" in user_message.lower():
    if "move-in ready" in user_message.lower() or "great shape" in user_message.lower():
        extracted["home_condition"] = "excellent"
    elif "some work" in user_message.lower() or "needs repairs" in user_message.lower():
        extracted["home_condition"] = "fair"
    elif "fixer" in user_message.lower() or "lots of work" in user_message.lower():
        extracted["home_condition"] = "poor"

Extract pathway preference
pathway = self.detect_intent_pathway(user_message, context)
if pathway != "unknown":
    extracted["pathway"] = pathway


Testing Checklist:
  [ ] Test wholesale keyword detection
  [ ] Test listing keyword detection
  [ ] Verify home condition extraction
  [ ] Check dynamic question flow



📅 Phase 4: Calendar Integration (3 hours)

Goal: AI finds available time slots on GHL calendar and offers them to leads

Jorge's Requirement: "The AI should look at our calendar on GHL and find a time slot that gives the lead an option to select."

Implementation Approach:

4.1 Research GHL Calendar API

Documentation: https://highlevel.stoplight.io/docs/integrations/

Endpoints needed:
  GET /calendars - List calendars
  GET /calendars/{calendarId}/free-slots - Get available slots
  POST /calendars/{calendarId}/appointments - Book appointment

4.2 Update services/ghl_client.py

Add calendar methods:

python
async def get_available_slots(
    self, 
    calendar_id: str, 
    start_date: str, 
    end_date: str,
    timezone: str = "America/Los_Angeles"
) -> List[Dict[str, Any]]:
    """
    Fetch available time slots from GHL calendar.
    
    Args:
        calendar_id: GHL calendar ID
        start_date: ISO format date (e.g., "2026-01-05")
        end_date: ISO format date (e.g., "2026-01-12")
        timezone: Timezone for slots
    
    Returns:
        List of available slots with start_time and end_time
    """
    endpoint = f"/calendars/{calendar_id}/free-slots"
    params = {
        "startDate": start_date,
        "endDate": end_date,
        "timezone": timezone
    }
    
    response = await self._make_request("GET", endpoint, params=params)
    return response.get("slots", [])

async def format_slots_for_user(self, slots: List[Dict]) -> str:
    """
    Format available slots into user-friendly text.
    
    Returns:
        "I have these times available:\n1. Mon Jan 6 at 2:00 PM\n2. Tue Jan 7 at 10:00 AM..."
    """
    formatted = "I have these times available:\n"
    for i, slot in enumerate(slots[:5], 1):  # Show max 5 slots
        # Parse slot time and format nicely
        start_time = slot["start_time"]  # ISO format
        # Convert to readable format
        formatted += f"{i}. {self._format_datetime(start_time)}\n"
    
    formatted += "\nWhich works best for you?"
    return formatted


4.3 Update conversation_manager.py

Add calendar check logic:

python
async def offer_calendar_slots(self, context: Dict) -> str:
    """
    When lead is qualified (hot), offer calendar slots.
    
    Returns:
        Message with available time slots
    """
    # Get lead score
    score = context.get("lead_score", 0)
    
    if score >= 3:  # Hot lead
        # Get slots for next 7 days
        today = datetime.now()
        start_date = today.strftime("%Y-%m-%d")
        end_date = (today + timedelta(days=7)).strftime("%Y-%m-%d")
        
        slots = await self.ghl_client.get_available_slots(
            calendar_id=settings.ghl_calendar_id,
            start_date=start_date,
            end_date=end_date
        )
        
        if slots:
            return await self.ghl_client.format_slots_for_user(slots)
        else:
            return "Let me have someone from the team reach out to schedule a time. What's the best number to call you?"
    
    return ""


4.4 Add to .env

bash
GHL_CALENDAR_ID=your_calendar_id_here


Testing Checklist:
  [ ] Test API connection to GHL calendar
  [ ] Verify slot retrieval works
  [ ] Check slot formatting is user-friendly
  [ ] Test booking flow (if implementing)
  [ ] Handle "no slots available" gracefully



🔄 Phase 5: AI On/Off Toggle Logic (1 hour)

Goal: Ensure AI only activates when specific GHL tag is added

Jorge's Setup: 
  Video shows "ai assistant on and off tag removal" automation
  AI should activate when contact tagged "Needs Qualifying"
  AI should deactivate when certain conditions met

Files to Modify:

5.1 Update api/routes/webhook.py

Enhance tag checking logic:

python
@router.post("/ghl/webhook")
async def handle_ghl_webhook(request: Request):
    """
    Handle incoming GHL webhooks.
    
    Triggers:
  Contact tagged "Needs Qualifying" → AI turns ON
  Contact tagged "AI-Off" or "Qualified" → AI turns OFF
    """
    payload = await request.json()
    
    # Extract contact info
    contact_id = payload.get("contactId")
    location_id = payload.get("locationId")
    tags = payload.get("tags", [])
    
    # Check if AI should be active
    activation_tags = settings.activation_tags  # ["Needs Qualifying", "Hit List"]
    deactivation_tags = settings.deactivation_tags  # ["AI-Off", "Qualified", "Stop-Bot"]
    
    should_activate = any(tag in tags for tag in activation_tags)
    should_deactivate = any(tag in tags for tag in deactivation_tags)
    
    if should_deactivate:
        logger.info(f"AI deactivated for contact {contact_id} - deactivation tag present")
        return {"status": "success", "message": "AI deactivated"}
    
    if not should_activate:
        logger.info(f"AI not triggered for contact {contact_id} - activation tag not present")
        return {"status": "success", "message": "AI not triggered"}
    
    # AI is active - proceed with conversation
    # ... existing logic ...


5.2 Update ghl_utils/config.py

Ensure tags are configurable:

python
Activation & Trigger Settings
activation_tags: list[str] = ["Needs Qualifying", "Hit List"]
deactivation_tags: list[str] = ["AI-Off", "Qualified", "Stop-Bot", "Hot Lead"]


Testing Checklist:
  [ ] Test webhook with "Needs Qualifying" tag → AI responds
  [ ] Test webhook without tag → AI silent
  [ ] Test webhook with "AI-Off" tag → AI deactivates
  [ ] Verify tag names match Jorge's GHL setup



🧪 Phase 6: Testing & Validation (2 hours)

Goal: Ensure all customizations work together

6.1 Unit Tests

Create tests/test_jorge_requirements.py:

python
import pytest
from services.lead_scorer import LeadScorer

def test_lead_scoring_question_count():
    """Test Jorge's question-count scoring logic."""
    scorer = LeadScorer()
    
    # Cold: 0 questions
    context = {"extracted_preferences": {}}
    assert scorer.calculate(context) == 0
    assert scorer.classify(0) == "cold"
    
    # Cold: 1 question
    context = {"extracted_preferences": {"budget": "300k"}}
    assert scorer.calculate(context) == 1
    assert scorer.classify(1) == "cold"
    
    # Warm: 2 questions
    context = {"extracted_preferences": {"budget": "300k", "location": "Austin"}}
    assert scorer.calculate(context) == 2
    assert scorer.classify(2) == "warm"
    
    # Hot: 3 questions
    context = {
        "extracted_preferences": {
            "budget": "300k",
            "location": "Austin",
            "timeline": "3 months"
        }
    }
    assert scorer.calculate(context) == 3
    assert scorer.classify(3) == "hot"

def test_wholesale_vs_listing_detection():
    """Test pathway detection."""
    from core.conversation_manager import ConversationManager
    
    manager = ConversationManager()
    
    # Wholesale
    assert manager.detect_intent_pathway("I need to sell as-is", {}) == "wholesale"
    assert manager.detect_intent_pathway("looking for a quick cash offer", {}) == "wholesale"
    
    # Listing
    assert manager.detect_intent_pathway("What's the best price I can get?", {}) == "listing"
    assert manager.detect_intent_pathway("I want top dollar", {}) == "listing"


6.2 Integration Test

Test full conversation flow:

python
async def test_full_qualification_flow():
    """Simulate a hot lead conversation."""
    
    # Simulate webhook with "Needs Qualifying" tag
    payload = {
        "contactId": "test_123",
        "locationId": "test_loc",
        "tags": ["Needs Qualifying"],
        "message": "Hi, I'm interested in selling my home"
    }
    
    # AI should respond
    response = await handle_ghl_webhook(payload)
    
    # Verify AI asks first question
    assert "budget" in response["message"].lower() or "price" in response["message"].lower()
    
    # Simulate answers to 3 questions
    # ... (simulate conversation) ...
    
    # After 3 questions, lead should be "hot"
    # AI should offer calendar slots
    # Verify "Hot Lead" tag gets applied


6.3 Manual Testing Checklist

  [ ] Send test webhook to /api/ghl/webhook
  [ ] Verify AI only responds when "Needs Qualifying" tag present
  [ ] Test conversation with direct tone
  [ ] Confirm 3+ questions triggers "hot" classification
  [ ] Test calendar slot offering
  [ ] Verify wholesale vs listing detection
  [ ] Test re-engagement messages
  [ ] Check all responses are SMS-length friendly



🚀 Phase 7: Railway Deployment (1 hour)

Goal: Deploy to production with Jorge's configuration

7.1 Environment Variables

Create Railway project and set these variables:

bash
Required
ANTHROPIC_API_KEY=sk-ant-...
GHL_API_KEY=...
GHL_LOCATION_ID=...
GHL_CALENDAR_ID=...

Optional
CLAUDE_MODEL=claude-sonnet-4-20250514
ENVIRONMENT=production
LOG_LEVEL=INFO

Lead Scoring (Jorge's settings)
HOT_LEAD_THRESHOLD=3
WARM_LEAD_THRESHOLD=2

Tags (match Jorge's GHL setup)
ACTIVATION_TAGS=["Needs Qualifying","Hit List"]
DEACTIVATION_TAGS=["AI-Off","Qualified","Stop-Bot","Hot Lead"]


7.2 Deploy Command

bash
From ghl-real-estate-ai directory
railway up

Or connect to GitHub and auto-deploy
railway link


7.3 Verify Deployment

bash
Test webhook endpoint
curl -X POST https://your-app.railway.app/api/ghl/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "contactId": "test_123",
    "locationId": "your_location_id",
    "tags": ["Needs Qualifying"],
    "message": "I want to sell my house"
  }'


Deployment Checklist:
  [ ] Railway project created
  [ ] Environment variables set
  [ ] App deployed successfully
  [ ] Webhook URL accessible
  [ ] Test webhook with curl
  [ ] Configure webhook in Jorge's GHL
  [ ] Monitor logs for first real conversation



Summary: Code Files to Modify

| File | Changes | Priority |
|------|---------|----------|
| ghl_utils/config.py | Update lead thresholds to 3/2/1 | High |
| services/lead_scorer.py | Refactor to count questions, not points | High |
| prompts/system_prompts.py | Update tone to be direct/curious | High |
| core/conversation_manager.py | Add pathway detection, home condition | Medium |
| services/ghl_client.py | Add calendar slot methods | Medium |
| api/routes/webhook.py | Enhance tag checking logic | Low |
| tests/test_jorge_requirements.py | Create new test file | Medium |



Timeline

Day 1 (4 hours):
  Phase 1: Lead Scoring Refactor
  Phase 2: Conversation Tone Update

Day 2 (5 hours):
  Phase 3: Qualifying Questions Enhancement
  Phase 4: Calendar Integration
  Phase 5: AI On/Off Toggle

Day 3 (3 hours):
  Phase 6: Testing & Validation
  Phase 7: Railway Deployment

Total: 12 hours



Next Steps

1. Watch Jorge's Loom video and document the exact automation flow
2. Start with Phase 1 (lead scoring) as it's the foundation
3. Test each phase before moving to the next
4. Deploy to Railway once all phases pass testing
5. Train Jorge on how to use and monitor the system



_Last Updated: [Current Date]_




_This document will be updated as implementation progresses._
