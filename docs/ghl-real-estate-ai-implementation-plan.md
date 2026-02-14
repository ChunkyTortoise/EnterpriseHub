# GHL Real Estate AI - Technical Implementation Plan

## Project Overview
**Goal:** Build conversational AI for real estate lead qualification on GoHighLevel
**Timeline:** 5-7 days (Option C: Hybrid MVP)
**Budget:** $100 fixed price
**Tech Stack:** FastAPI + Claude Sonnet 4.5 + Railway + Chroma/Pinecone

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         GoHighLevel                              │
│  (Contact SMS/Email) ──────────────────────────────────────────┐ │
└────────────────────────────────────────────────────────────────┼─┘
                                                                  │
                                    Webhook (POST /ghl/webhook)  │
                                                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        FastAPI Backend (Railway)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │   Webhook    │  │  Conversation│  │   Lead Scoring        │    │
│  │   Handler    │─▶│    Engine    │─▶│   & Tagging           │    │
│  └──────────────┘  └──────────────┘  └───────────────────────┘    │
│         │                  │                      │                 │
│         ▼                  ▼                      ▼                 │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────┐    │
│  │   Request    │  │  RAG Engine  │  │   GHL API Client      │    │
│  │ Validation   │  │  (Chroma)    │  │   (Update Tags)       │    │
│  └──────────────┘  └──────────────┘  └───────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Claude Sonnet 4.5   │
                        │   (Anthropic API)     │
                        └───────────────────────┘
                                    │
                                    ▼
                        ┌───────────────────────┐
                        │   Vector Database     │
                        │ (Property Listings +  │
                        │  FAQ + Agent Scripts) │
                        └───────────────────────┘
```

---

## File Structure

```
ghl-real-estate-ai/
├── api/
│   ├── __init__.py
│   ├── main.py                      # FastAPI app entry point
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── webhook.py               # GHL webhook handler
│   │   └── health.py                # Health check endpoint
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── ghl.py                   # GHL webhook models
│   │   └── conversation.py          # Conversation state models
│   └── middleware/
│       ├── __init__.py
│       └── auth.py                  # Webhook signature verification
│
├── core/
│   ├── __init__.py
│   ├── llm_client.py                # Claude API client (from agentforge)
│   ├── rag_engine.py                # RAG engine (from agentforge)
│   └── conversation_manager.py      # Conversation state management
│
├── services/
│   ├── __init__.py
│   ├── ghl_client.py                # GHL API wrapper
│   ├── lead_scorer.py               # Lead qualification logic
│   └── property_matcher.py          # Property recommendation engine
│
├── prompts/
│   ├── __init__.py
│   ├── system_prompts.py            # Base system prompts
│   ├── qualification_prompts.py     # Lead qualification templates
│   └── objection_handlers.py        # Objection handling scripts
│
├── data/
│   ├── knowledge_base/
│   │   ├── property_listings.json   # Sample property data
│   │   ├── faq.json                 # Real estate FAQ
│   │   └── agent_scripts.json       # Objection handlers
│   └── embeddings/
│       └── chroma_db/               # Vector database storage
│
├── tests/
│   ├── __init__.py
│   ├── test_webhook.py
│   ├── test_conversation.py
│   └── test_lead_scoring.py
│
├── utils/
│   ├── __init__.py
│   ├── logger.py                    # Structured logging
│   └── config.py                    # Environment configuration
│
├── .env.example                     # Environment template
├── .gitignore
├── requirements.txt
├── Dockerfile
├── railway.json                     # Railway deployment config
└── README.md
```

---

## API Contracts

### 1. GHL Webhook Endpoint

**Endpoint:** `POST /api/ghl/webhook`

**Request (from GHL):**
```json
{
  "type": "InboundMessage",
  "contactId": "contact_abc123",
  "locationId": "location_xyz789",
  "message": {
    "type": "SMS",
    "body": "Hi, I'm looking for a 3-bedroom house in Rancho Cucamonga under $400k",
    "direction": "inbound"
  },
  "contact": {
    "firstName": "Jane",
    "lastName": "Doe",
    "phone": "+15125551234",
    "email": "jane.doe@example.com",
    "tags": []
  }
}
```

**Response (to GHL):**
```json
{
  "success": true,
  "message": "Hey Jane! Rancho Cucamonga's market is hot right now—let me help you find the perfect fit. Just to make sure I point you to the best options:\n- Are you open to suburbs like Round Rock or Pflugerville, or strictly Rancho Cucamonga proper?\n- What's your ideal move-in timeline?\n- Any must-haves? (pool, good schools, walkable neighborhood)",
  "actions": [
    {
      "type": "send_message",
      "channel": "SMS",
      "body": "..."
    },
    {
      "type": "add_tags",
      "tags": ["AI-Engaged", "Budget-Under-400k", "Location-Rancho Cucamonga"]
    },
    {
      "type": "update_custom_field",
      "field": "lead_score",
      "value": "35"
    }
  ]
}
```

### 2. Conversation State Schema

**PostgreSQL Table: `conversations`**
```sql
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    conversation_history JSONB DEFAULT '[]',
    context_summary TEXT,
    lead_score INTEGER DEFAULT 0,
    qualified_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_contact_location (contact_id, location_id)
);
```

**Example `conversation_history` JSONB:**
```json
[
  {
    "role": "user",
    "content": "Hi, I'm looking for a 3-bedroom house in Rancho Cucamonga under $400k",
    "timestamp": "2025-01-02T10:00:00Z"
  },
  {
    "role": "assistant",
    "content": "Hey! Rancho Cucamonga's market is hot...",
    "timestamp": "2025-01-02T10:00:05Z"
  }
]
```

### 3. Lead Scoring API (Internal)

**Endpoint:** `POST /api/internal/score-lead`

**Request:**
```json
{
  "contact_id": "contact_abc123",
  "conversation_history": [...],
  "extracted_data": {
    "budget": 400000,
    "location": "Rancho Cucamonga",
    "bedrooms": 3,
    "timeline": "June 2025",
    "must_haves": ["good schools"]
  }
}
```

**Response:**
```json
{
  "score": 85,
  "classification": "hot",
  "reasoning": "Budget confirmed, timeline urgent (3 months), specific requirements indicate serious buyer",
  "recommended_actions": [
    "Tag as 'Hot Lead'",
    "Notify agent via SMS",
    "Schedule showing within 48 hours"
  ]
}
```

---

## Database Schema

### Vector Database (Chroma)

**Collection: `property_listings`**
```python
{
    "id": "prop_12345",
    "embedding": [0.123, -0.456, ...],  # 1536-dim vector
    "metadata": {
        "address": "123 Main St, Rancho Cucamonga, CA 91701",
        "price": 385000,
        "bedrooms": 3,
        "bathrooms": 2,
        "sqft": 1850,
        "neighborhood": "Etiwanda",
        "schools": ["Etiwanda Elementary (9/10)", "McCallum HS (8/10)"],
        "features": ["pool", "updated kitchen", "walkable"],
        "listing_url": "https://example.com/listing/12345"
    },
    "document": "Beautiful 3-bedroom home in Etiwanda with updated kitchen..."
}
```

**Collection: `faq`**
```python
{
    "id": "faq_001",
    "embedding": [0.789, -0.234, ...],
    "metadata": {
        "category": "financing",
        "question": "What credit score do I need?"
    },
    "document": "For conventional loans, 620+ is minimum. FHA allows 580+..."
}
```

**Collection: `agent_scripts`**
```python
{
    "id": "script_objection_price",
    "embedding": [0.345, -0.678, ...],
    "metadata": {
        "type": "objection_handler",
        "trigger": "price too high"
    },
    "document": "I totally understand—Rancho Cucamonga prices can feel steep. Here's the thing: this property is actually 8% under market average for the neighborhood..."
}
```

### PostgreSQL (Session State)

**Table: `conversation_context`**
```sql
CREATE TABLE conversation_context (
    id UUID PRIMARY KEY,
    contact_id VARCHAR(255) UNIQUE NOT NULL,
    extracted_preferences JSONB DEFAULT '{}',
    lead_score INTEGER DEFAULT 0,
    last_interaction TIMESTAMP,
    qualified BOOLEAN DEFAULT FALSE
);
```

**Example Row:**
```json
{
  "id": "uuid-here",
  "contact_id": "contact_abc123",
  "extracted_preferences": {
    "budget": {"min": 350000, "max": 400000},
    "location": ["Rancho Cucamonga", "Round Rock", "Pflugerville"],
    "bedrooms": 3,
    "bathrooms": {"min": 2},
    "must_haves": ["good schools", "walkable"],
    "timeline": "June 2025",
    "financing": "pre-approved"
  },
  "lead_score": 85,
  "last_interaction": "2025-01-02T10:05:00Z",
  "qualified": true
}
```

---

## Core Components Implementation

### 1. Webhook Handler (`api/routes/webhook.py`)

```python
from fastapi import APIRouter, Request, HTTPException, BackgroundTasks
from api.schemas.ghl import GHLWebhookEvent, GHLWebhookResponse
from services.ghl_client import GHLClient
from core.conversation_manager import ConversationManager
from utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/ghl", tags=["ghl"])

conversation_manager = ConversationManager()
ghl_client = GHLClient()

@router.post("/webhook")
async def handle_ghl_webhook(
    event: GHLWebhookEvent,
    background_tasks: BackgroundTasks
):
    """
    Handle incoming messages from GoHighLevel.
    Process conversation and return AI response.
    """
    logger.info(f"Received webhook for contact: {event.contactId}")

    # 1. Validate webhook signature (if GHL provides it)
    # validate_ghl_signature(request.headers, request.body)

    # 2. Extract message
    user_message = event.message.body
    contact_id = event.contactId
    contact_info = event.contact

    # 3. Get conversation context
    context = await conversation_manager.get_context(contact_id)

    # 4. Generate AI response
    ai_response = await conversation_manager.generate_response(
        user_message=user_message,
        contact_info=contact_info,
        context=context
    )

    # 5. Update conversation state
    await conversation_manager.update_context(
        contact_id=contact_id,
        user_message=user_message,
        ai_response=ai_response.message,
        extracted_data=ai_response.extracted_data
    )

    # 6. Calculate lead score
    lead_score = await conversation_manager.calculate_lead_score(
        contact_id=contact_id
    )

    # 7. Prepare GHL actions (tags, custom fields)
    actions = []

    # Tag based on extracted preferences
    if ai_response.extracted_data.get("budget"):
        budget = ai_response.extracted_data["budget"]
        if budget < 300000:
            actions.append({"type": "add_tag", "tag": "Budget-Under-300k"})
        elif budget < 500000:
            actions.append({"type": "add_tag", "tag": "Budget-300k-500k"})

    # Tag based on lead score
    if lead_score >= 80:
        actions.append({"type": "add_tag", "tag": "Hot-Lead"})
        actions.append({"type": "trigger_workflow", "workflow_id": "notify_agent"})
    elif lead_score >= 50:
        actions.append({"type": "add_tag", "tag": "Warm-Lead"})

    # 8. Send response back to GHL (in background)
    background_tasks.add_task(
        ghl_client.send_message,
        contact_id=contact_id,
        message=ai_response.message,
        channel=event.message.type  # SMS or Email
    )

    background_tasks.add_task(
        ghl_client.apply_actions,
        contact_id=contact_id,
        actions=actions
    )

    # 9. Return immediate response
    return GHLWebhookResponse(
        success=True,
        message=ai_response.message,
        actions=actions
    )
```

### 2. Conversation Manager (`core/conversation_manager.py`)

```python
from typing import Dict, List, Optional
from dataclasses import dataclass
from core.llm_client import LLMClient
from core.rag_engine import RAGEngine
from prompts.system_prompts import REAL_ESTATE_SYSTEM_PROMPT
from services.lead_scorer import LeadScorer
import json
import re

@dataclass
class AIResponse:
    message: str
    extracted_data: Dict
    reasoning: str

class ConversationManager:
    def __init__(self):
        self.llm_client = LLMClient(provider="claude", model="claude-sonnet-4-20250514")
        self.rag_engine = RAGEngine(collection_name="real_estate_kb")
        self.lead_scorer = LeadScorer()
        self.context_store = {}  # Replace with Redis/Postgres

    async def get_context(self, contact_id: str) -> Dict:
        """Retrieve conversation context for contact."""
        if contact_id in self.context_store:
            return self.context_store[contact_id]
        return {
            "conversation_history": [],
            "extracted_preferences": {},
            "lead_score": 0
        }

    async def generate_response(
        self,
        user_message: str,
        contact_info: Dict,
        context: Dict
    ) -> AIResponse:
        """Generate AI response using Claude + RAG."""

        # 1. Retrieve relevant knowledge
        relevant_docs = await self.rag_engine.search(
            query=user_message,
            top_k=3
        )

        # 2. Build conversation history
        conversation_history = context.get("conversation_history", [])
        conversation_history.append({
            "role": "user",
            "content": user_message
        })

        # 3. Extract structured data from conversation
        extraction_prompt = f"""
        Analyze this conversation and extract:
        - Budget (min/max if range)
        - Location preferences
        - Bedrooms/bathrooms
        - Timeline
        - Must-have features
        - Objections/concerns

        Previous context: {json.dumps(context.get('extracted_preferences', {}))}
        New message: {user_message}

        Return JSON only.
        """

        extraction_response = await self.llm_client.agenerate(
            prompt=extraction_prompt,
            system_prompt="You are a data extraction specialist.",
            temperature=0
        )

        try:
            extracted_data = json.loads(extraction_response.content)
        except:
            extracted_data = {}

        # 4. Build system prompt with context
        system_prompt = REAL_ESTATE_SYSTEM_PROMPT.format(
            contact_name=contact_info.get("firstName", "there"),
            extracted_preferences=json.dumps(extracted_data, indent=2),
            relevant_knowledge="\n\n".join([doc["document"] for doc in relevant_docs])
        )

        # 5. Generate response
        ai_response = await self.llm_client.agenerate(
            prompt=user_message,
            system_prompt=system_prompt,
            temperature=0.7,
            max_tokens=500
        )

        return AIResponse(
            message=ai_response.content,
            extracted_data=extracted_data,
            reasoning=""
        )

    async def calculate_lead_score(self, contact_id: str) -> int:
        """Calculate lead score based on conversation."""
        context = await self.get_context(contact_id)
        return self.lead_scorer.calculate(context)
```

### 3. Lead Scorer (`services/lead_scorer.py`)

```python
class LeadScorer:
    """Calculate lead quality score (0-100)."""

    def calculate(self, context: Dict) -> int:
        score = 0
        prefs = context.get("extracted_preferences", {})

        # Budget confirmed (+30 points)
        if prefs.get("budget"):
            score += 30
            # Pre-approved financing (+15 bonus)
            if prefs.get("financing") == "pre-approved":
                score += 15

        # Timeline confirmed (+25 points)
        timeline = prefs.get("timeline", "")
        if timeline:
            score += 25
            # Urgent timeline (< 3 months) (+10 bonus)
            if any(word in timeline.lower() for word in ["asap", "immediately", "this month", "next month"]):
                score += 10

        # Location specified (+15 points)
        if prefs.get("location"):
            score += 15

        # Specific requirements (+10 points)
        if prefs.get("bedrooms") or prefs.get("must_haves"):
            score += 10

        # Engagement (message count) (+10 points if > 3 messages)
        if len(context.get("conversation_history", [])) > 6:  # 3 back-and-forth
            score += 10

        return min(score, 100)
```

---

## Deployment Steps (Railway)

### Prerequisites
- Railway account (free tier)
- GHL trial account
- Anthropic API key

### Step 1: Prepare Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init
```

### Step 2: Configure Environment Variables

**In Railway dashboard, add:**
```env
ANTHROPIC_API_KEY=sk-ant-xxxxx
GHL_API_KEY=your_ghl_api_key
GHL_LOCATION_ID=your_location_id
DATABASE_URL=postgresql://... (auto-provided by Railway)
REDIS_URL=redis://... (if using Redis addon)
ENVIRONMENT=production
LOG_LEVEL=info
```

### Step 3: Create `railway.json`

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn api.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 4: Deploy

```bash
# Deploy to Railway
railway up

# Get deployment URL
railway ontario_mills
# Output: https://your-app.railway.app
```

### Step 5: Configure GHL Webhook

1. Go to GHL Settings > Integrations > Webhooks
2. Add webhook URL: `https://your-app.railway.app/api/ghl/webhook`
3. Select events: `InboundMessage`
4. Save

### Step 6: Test End-to-End

```bash
# Send test SMS to GHL number
# Should receive AI response within 2-3 seconds
```

---

## Testing Strategy

### Unit Tests
```python
# tests/test_lead_scoring.py
def test_lead_scorer_high_score():
    context = {
        "extracted_preferences": {
            "budget": 400000,
            "timeline": "ASAP",
            "location": "Rancho Cucamonga",
            "financing": "pre-approved"
        },
        "conversation_history": [{"role": "user"}] * 8
    }
    scorer = LeadScorer()
    score = scorer.calculate(context)
    assert score >= 80
```

### Integration Tests
```python
# tests/test_webhook.py
@pytest.mark.asyncio
async def test_webhook_end_to_end():
    payload = {
        "contactId": "test_123",
        "message": {"body": "Looking for 3bed house in Rancho Cucamonga"},
        "contact": {"firstName": "Test"}
    }
    response = await client.post("/api/ghl/webhook", json=payload)
    assert response.status_code == 200
    assert "Rancho Cucamonga" in response.json()["message"]
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Webhook response time | < 3 seconds | 95th percentile |
| Claude API latency | < 2 seconds | Average |
| RAG retrieval time | < 200ms | Average |
| Database query time | < 50ms | Average |
| Concurrent conversations | 50+ | Load test |

---

## Cost Breakdown (Monthly Estimates)

| Service | Free Tier | Paid (if exceeded) |
|---------|-----------|-------------------|
| Railway hosting | 500 hours/month free | $5/month after |
| Anthropic API | $0 (pay-per-use) | ~$2-5 for 1000 conversations |
| Chroma (embedded) | Free | N/A |
| PostgreSQL (Railway) | 1GB free | $5/month for 5GB |
| **Total** | **$0-7/month** | **Scalable** |

---

## Security Checklist

- [ ] Webhook signature verification implemented
- [ ] API keys stored in environment variables (never in code)
- [ ] Rate limiting on webhook endpoint (max 100 req/min per contact)
- [ ] Input sanitization for user messages
- [ ] HTTPS enforced on all endpoints
- [ ] Database connection pooling configured
- [ ] Error messages don't leak sensitive data
- [ ] Logging excludes PII (phone numbers, emails)

---

## Next Steps

1. ✅ **Review this plan** - Any questions or changes?
2. ⏭️ **Create knowledge base** - Real estate FAQ + sample listings
3. ⏭️ **Write system prompts** - Lead qualification + objection handling
4. ⏭️ **Set up project structure** - Initialize files and dependencies
5. ⏭️ **Deploy to Railway** - Test end-to-end flow

**Ready to proceed?** I'll now create the knowledge base and system prompts.
