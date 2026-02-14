# Interview Prep: Chase Ashley (FloPro Jamaica) - AI Secretary SaaS

**Date**: Thursday, February 12, 2026 at 10am Pacific (1pm EST)
**Project**: Development of AI Agent Secretary / Personal Assistant
**Company**: FloPro Jamaica

---

## 🎯 Quick Win Opening (30 seconds)

> "I've built a production multi-agent system that handles exactly this - task routing, calendar integration, and intelligent handoffs between specialized agents. For your AI secretary, I'd use a task classification layer that routes incoming requests to domain-specific sub-agents: calendar, email drafting, research, reminders. Let me walk you through the architecture."

---

## 📊 Portfolio Walkthrough (5 minutes)

### 1. EnterpriseHub - Multi-Agent Orchestration
**Repository**: github.com/ChunkyTortoise/EnterpriseHub
**Relevance**: **DIRECTLY APPLICABLE** - This is the foundation for your SaaS

**Key Components You'll Reuse**:

1. **Agent Mesh Coordinator** (`services/agent_mesh_coordinator.py`)
   - Routes tasks to specialized agents (Lead Bot, Buyer Bot, Seller Bot)
   - Governance layer prevents circular routing
   - Auto-scaling based on load
   - **Your use case**: Route secretary tasks to Calendar Agent, Email Agent, Research Agent

2. **Claude Orchestrator** (`services/claude_orchestrator.py`)
   - Multi-strategy response parsing (regex, JSON, Claude tools)
   - 3-tier caching (L1/L2/L3) - 88% hit rate = 89% cost reduction
   - <200ms overhead (P99: 0.095ms)
   - **Your use case**: Process user requests, extract intent, route to specialized agents

3. **Jorge Handoff Service** (`services/jorge/jorge_handoff_service.py`)
   - Cross-bot handoff with confidence scoring (0.7 threshold)
   - Circular prevention (30min cooldown)
   - Rate limiting (3/hr, 10/day per contact)
   - **Your use case**: Hand off tasks between secretary sub-agents (e.g., Calendar → Email for meeting invite drafting)

4. **Multi-Tenant Infrastructure**
   - PostgreSQL with tenant isolation
   - Redis namespacing by tenant
   - JWT auth with tenant_id claims
   - **Your use case**: Each SaaS customer = 1 tenant, their users = contacts

### 2. AgentForge - Tool Orchestration Engine
**Repository**: github.com/ChunkyTortoise/ai-orchestrator
**Stats**: 550+ tests, 4.3M tool dispatches/sec

**Relevance**:
- **Tool registry** for dynamic agent capabilities (calendar, email, search, etc.)
- **ReAct agent loop** for multi-step reasoning ("first check calendar, then draft email, then send")
- **Evaluation framework** to measure secretary quality
- **Memory system** to remember user preferences ("always schedule meetings in the morning")

**Demo Point**: *"I can show you the ReAct loop - it's how the secretary would break down 'Schedule a lunch meeting with John next week' into: (1) check John's email from context, (2) query calendar for availability, (3) pick a slot, (4) draft invite, (5) send."*

### 3. DocQA Engine - Knowledge Base for Secretary
**Repository**: github.com/ChunkyTortoise/docqa-engine
**Stats**: 500+ tests, hybrid retrieval (BM25 + semantic)

**Relevance**:
- **Document Q&A** for company policies, FAQ, user preferences
- **Conversation manager** for multi-turn context
- **Summarizer** for long email threads
- **Multi-hop reasoning** for complex queries

**Your use case**: "What's our policy on travel expense reimbursement?" → Secretary retrieves from knowledge base and answers

---

## 🏗️ SaaS Architecture Proposal

### High-Level System Design

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                         │
│  (Web App / Mobile App / Email Forwarding / SMS)           │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│                   API Gateway (FastAPI)                     │
│  - Authentication (JWT)                                     │
│  - Rate limiting (per tenant)                               │
│  - Request routing                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────────┐
│              Task Classification Layer                       │
│  (Claude Haiku for fast, cheap intent detection)           │
│                                                             │
│  Incoming: "Schedule a 30-min call with Sarah next Tuesday"│
│  Output: {                                                  │
│    "task_type": "calendar_scheduling",                      │
│    "entities": {                                            │
│      "contact": "Sarah",                                    │
│      "duration": 30,                                        │
│      "timeframe": "next Tuesday"                            │
│    },                                                       │
│    "priority": "medium"                                     │
│  }                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ├─────────────┬─────────────┬──────────────┐
                         │             │             │              │
             ┌───────────▼───┐ ┌──────▼─────┐ ┌────▼──────┐ ┌────▼────────┐
             │ Calendar Agent│ │ Email Agent│ │Research Agt│ │Reminder Agt │
             │ (Google Cal,  │ │ (Gmail API,│ │ (Web search│ │ (Push notif,│
             │  Outlook API) │ │  templates)│ │  Wikipedia)│ │  SMS, email)│
             └───────┬───────┘ └──────┬─────┘ └────┬──────┘ └─────┬───────┘
                     │                │             │              │
                     └────────────────┴─────────────┴──────────────┘
                                      │
                         ┌────────────▼─────────────┐
                         │   PostgreSQL + Redis     │
                         │  - User preferences      │
                         │  - Conversation history  │
                         │  - Task queue            │
                         │  - Cached responses      │
                         └──────────────────────────┘
```

### Core Features & Implementation

#### 1. Gmail/Outlook Integration

**OAuth 2.0 Flow**:
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

async def connect_gmail(user_id: str, auth_code: str):
    """Exchange auth code for tokens, store encrypted"""
    credentials = await exchange_auth_code(auth_code)

    # Encrypt and store tokens
    encrypted_tokens = fernet.encrypt(json.dumps({
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
    }).encode())

    await db.execute(
        "INSERT INTO email_connections (user_id, provider, encrypted_tokens) VALUES ($1, $2, $3)",
        user_id, "gmail", encrypted_tokens
    )

    return {"status": "connected", "email": credentials.id_token.get("email")}
```

**Email Monitoring** (Webhook approach):
```python
# Google Pub/Sub webhook for new emails
@app.post("/webhooks/gmail")
async def gmail_webhook(request: Request):
    """Receive push notifications for new emails"""
    data = await request.json()
    user_id = data["user_id"]

    # Fetch new email via Gmail API
    service = await get_gmail_service(user_id)
    message = service.users().messages().get(userId='me', id=data['message_id']).execute()

    # Process email (classify intent, draft response if appropriate)
    await process_incoming_email(user_id, message)
```

#### 2. Calendar Management

**Availability Detection**:
```python
async def find_available_slots(
    user_id: str,
    duration_minutes: int,
    start_date: date,
    end_date: date,
    preferences: dict
) -> list[dict]:
    """Find available calendar slots respecting preferences"""
    calendar_service = await get_calendar_service(user_id)

    # Get busy periods from Google Calendar
    busy_times = calendar_service.freebusy().query(
        body={
            "timeMin": start_date.isoformat(),
            "timeMax": end_date.isoformat(),
            "items": [{"id": "primary"}]
        }
    ).execute()

    # Apply user preferences (e.g., no meetings before 9am, no back-to-back)
    business_hours = preferences.get("business_hours", {"start": 9, "end": 17})
    buffer_minutes = preferences.get("buffer_minutes", 15)

    # Generate available slots
    slots = generate_slots(busy_times, duration_minutes, business_hours, buffer_minutes)
    return slots
```

**Meeting Scheduling with Confirmation**:
```python
async def schedule_meeting(
    user_id: str,
    attendees: list[str],
    duration: int,
    proposed_times: list[datetime],
    subject: str,
    notes: str = ""
) -> dict:
    """Schedule meeting after confirming availability"""
    # Check attendee availability (if they're also users)
    available_slot = await find_mutual_availability(user_id, attendees, proposed_times)

    if not available_slot:
        return {"status": "no_availability", "suggested_times": await suggest_alternatives(user_id, attendees, duration)}

    # Create calendar event
    event = {
        "summary": subject,
        "description": notes,
        "start": {"dateTime": available_slot.isoformat(), "timeZone": "America/Los_Angeles"},
        "end": {"dateTime": (available_slot + timedelta(minutes=duration)).isoformat(), "timeZone": "America/Los_Angeles"},
        "attendees": [{"email": email} for email in attendees]
    }

    calendar_service = await get_calendar_service(user_id)
    created_event = calendar_service.events().insert(calendarId='primary', body=event, sendUpdates='all').execute()

    return {"status": "scheduled", "event_id": created_event["id"], "meeting_link": created_event.get("hangoutLink")}
```

#### 3. Email Drafting & Sending

**Template-Based Drafting**:
```python
EMAIL_TEMPLATES = {
    "meeting_invite": """
Hi {recipient_name},

I'd like to schedule a {duration}-minute {meeting_type} to discuss {topic}.

I have availability on:
{available_times}

Please let me know what works for you.

Best regards,
{sender_name}
""",
    "follow_up": """
Hi {recipient_name},

Following up on {context}. {specific_request}

{closing}
""",
    # ... more templates
}

async def draft_email(
    user_id: str,
    intent: str,
    context: dict
) -> dict:
    """Draft email using templates + LLM customization"""
    # Get template
    template = EMAIL_TEMPLATES.get(intent, "")

    # Use Claude to customize template with context
    prompt = f"""
You are drafting an email on behalf of a user. Use this template as a starting point:

{template}

Context: {json.dumps(context)}

Customize the email to be natural, professional, and specific to the context. Output only the email body.
"""

    response = await claude.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=500
    )

    draft = response.content[0].text

    # Save draft for user review
    await db.execute(
        "INSERT INTO email_drafts (user_id, recipient, subject, body, status) VALUES ($1, $2, $3, $4, 'pending_review')",
        user_id, context["recipient"], context["subject"], draft
    )

    return {"draft_id": draft_id, "body": draft}
```

#### 4. User Preferences & Learning

**Preference Schema**:
```python
@dataclass
class UserPreferences:
    """Learned preferences for secretary behavior"""
    # Calendar
    business_hours: dict  # {"start": 9, "end": 17}
    preferred_meeting_times: list[str]  # ["morning", "early afternoon"]
    buffer_minutes: int  # Time between meetings
    no_meeting_days: list[str]  # ["Friday"]

    # Email
    email_tone: str  # "formal", "casual", "friendly"
    signature: str
    auto_respond_to: list[str]  # Email addresses that get auto-responses

    # General
    timezone: str
    language: str
    priority_contacts: list[str]  # VIPs who get faster responses

async def learn_from_edits(user_id: str, original_draft: str, edited_draft: str):
    """Learn from user edits to improve future drafts"""
    # Use Claude to analyze what changed
    prompt = f"""
Compare these two email drafts and identify what the user prefers:

Original:
{original_draft}

Edited:
{edited_draft}

What patterns or preferences can we infer? (e.g., tone, structure, specific phrases)
Output as JSON.
"""

    insights = await claude.messages.create(...)

    # Update user preferences
    await update_preferences(user_id, insights)
```

---

## 💬 Mock Q&A

### Q: "How would you handle email prioritization?"

**A**: "Multi-factor scoring system:

1. **Sender importance**: Check if sender is in `priority_contacts` list, or has high email frequency with user
2. **Content urgency**: Use Claude to classify as 'urgent', 'important', 'routine', 'informational'
3. **Context clues**: Keywords like 'ASAP', 'urgent', 'deadline', 'reminder' boost priority
4. **Time sensitivity**: Meeting requests for next 24 hours = high priority

Score formula:
```python
priority_score = (sender_weight * 0.4) + (urgency_weight * 0.3) + (keywords_weight * 0.2) + (time_weight * 0.1)
```

Present top 5 highest-scoring emails in dashboard, auto-respond to routine stuff ('Your package has shipped'), flag urgent items for immediate attention."

### Q: "What about data privacy for email content?"

**A**: "Critical for trust. My approach:

1. **Encryption at rest**: All email content encrypted with Fernet (symmetric encryption) before storing in PostgreSQL
2. **Encryption in transit**: TLS 1.3 for all API calls, OAuth tokens stored encrypted
3. **Zero-knowledge architecture** (optional tier): User's encryption key derived from their password - we never see plaintext
4. **Minimal retention**: Only store emails actively being processed, auto-delete after 30 days unless user explicitly saves
5. **Access controls**: Each user can only access their own data (tenant_id + user_id in WHERE clauses)
6. **Compliance**: GDPR-compliant data export, right to be forgotten (hard delete all user data)

For extra-paranoid users, offer **on-premise deployment** option where they run the secretary on their own infrastructure."

### Q: "How do you prevent the secretary from sending embarrassing emails?"

**A**: "Multi-layer safety:

1. **Default to draft mode**: Secretary NEVER sends emails without user approval by default. User must click 'Send' in UI.
2. **Confidence scoring**: If secretary's confidence <0.8, require review. High confidence (>0.9) = optional auto-send for trusted scenarios (e.g., meeting confirmations)
3. **Dry-run mode**: User can enable 'practice mode' for first 2 weeks - secretary drafts everything but sends nothing
4. **Audit trail**: Log every drafted email with timestamp, reasoning, confidence score - user can review decision-making
5. **Undo/recall**: 30-second grace period to recall sent email (Gmail API supports this)
6. **Profanity filter**: Block emails containing profanity, offensive language (using moderation API)
7. **Recipient whitelist**: User can set 'only send to these domains' rule (e.g., internal company emails only)

**User override**: Settings panel lets user adjust auto-send aggressiveness from 'never' to 'always review' to 'auto-send routine stuff'."

### Q: "How would you monetize this SaaS?"

**A**: "Freemium + tiered pricing:

**Free Tier** (acquisition):
- 50 AI actions/month (email drafts, calendar checks, reminders)
- 1 connected email account
- Basic calendar integration
- 7-day conversation history

**Pro Tier** ($19/mo):
- 500 AI actions/month
- 3 connected accounts (Gmail + Outlook + iCloud)
- Advanced preferences (meeting buffer, no-meeting days)
- 90-day history
- Priority support

**Team Tier** ($49/user/mo, min 5 users):
- Unlimited AI actions
- Shared secretary for team scheduling
- Meeting room booking
- Slack/Teams integration
- Admin dashboard for team analytics

**Enterprise Tier** (Custom pricing):
- On-premise deployment option
- SSO (SAML/OKTA)
- Custom AI training on company data
- SLA guarantees
- Dedicated support

**Additional revenue streams**:
- **Usage overages**: $0.10 per AI action beyond plan limit
- **Add-ons**: CRM integration ($10/mo), advanced search ($5/mo), voice secretary ($15/mo)
- **API access**: $99/mo for developer API (build custom secretary integrations)"

### Q: "What's your timeline to MVP?"

**A**: "Based on my existing EnterpriseHub codebase, I'd estimate:

**Phase 1 - Core Secretary (4 weeks)**:
- Week 1-2: Gmail OAuth integration, email fetching, basic task classification
- Week 3: Calendar API integration, availability detection
- Week 4: Email drafting, review UI, sending

**Phase 2 - Multi-Tenant SaaS (3 weeks)**:
- Week 5: User registration, authentication, tenant isolation
- Week 6: Subscription billing (Stripe), usage tracking
- Week 7: Admin dashboard, analytics

**Phase 3 - Polish & Launch (2 weeks)**:
- Week 8: Security audit, performance optimization, caching
- Week 9: Beta testing with 10-20 users, bug fixes, launch

**Total**: 9 weeks to production-ready MVP.

**Assumptions**:
- 20-25 hrs/week availability
- You handle UI/UX design (I implement)
- We use existing services (Stripe, Twilio) vs building from scratch

**After MVP**:
- Outlook integration: +2 weeks
- Mobile app: +4 weeks
- Voice secretary: +3 weeks"

---

## 🛠️ Assets to Screen Share

1. **EnterpriseHub Architecture Diagram**
   - Show agent mesh coordinator
   - Highlight handoff service (analogous to task routing in secretary)

2. **Claude Orchestrator Code** (`services/claude_orchestrator.py`)
   - Multi-strategy parsing
   - Caching architecture
   - Error handling

3. **AgentForge ReAct Loop** (`ai-orchestrator/agents/react_agent.py`)
   - Multi-step reasoning demonstration
   - Tool registry pattern

4. **Live Demo** (if stable internet):
   - Streamlit dashboard showing agent performance metrics
   - Or: Local docker-compose spin-up of Jorge bots

5. **Benchmark Results** (`EnterpriseHub/benchmarks/RESULTS.md`)
   - <200ms orchestration overhead
   - 88% cache hit rate
   - Cost reduction graphs

---

## 🎤 Closing Questions to Ask

1. **"What's your target market - individuals or businesses? That affects the feature prioritization."**
2. **"Do you have UI/UX designs already, or would you like me to recommend a design system?"**
3. **"What's your expected launch date? Want to make sure timeline aligns."**
4. **"Are you open to using existing services (Stripe, Twilio, SendGrid) or prefer building everything in-house?"**
5. **"What's your biggest concern - speed to market, cost optimization, or feature richness?"**

---

## ⚡ Rapid-Fire Prep

**If they ask about...**
- **Scalability**: Horizontal FastAPI scaling, PostgreSQL read replicas, Redis cluster, Kubernetes
- **Cost**: $500-1000/mo infrastructure at 1,000 users (AWS: RDS, ElastiCache, ECS), LLM costs ~$0.02/user/mo with caching
- **Security**: OAuth 2.0, JWT, Fernet encryption, rate limiting, GDPR compliance
- **Testing**: 5,100+ tests in EnterpriseHub, pytest, mocks, CI on every commit, 80%+ coverage
- **Deployment**: Docker Compose locally, ECS Fargate for production, GitHub Actions CI/CD, blue-green deployments

**Your rates**:
- Hourly: $65-75/hr
- Project: $8,000-$12,000 for MVP (9 weeks * 20 hrs/week * $65/hr = $11,700)
- Equity: Open to equity + reduced rate if aligned on vision

---

## 🎯 Post-Interview Action Items

1. **Send thank-you message** within 2 hours:
   - "Thanks for the call Chase. I'm excited about the secretary vision - I'll sketch out the Gmail OAuth flow and task routing architecture and share it with you tomorrow."

2. **Follow-up artifact** (within 24 hours):
   - 1-page system architecture diagram (mermaid or draw.io)
   - Include: API Gateway → Task Classification → Agent Routing → Calendar/Email APIs → Database
   - Label with EnterpriseHub components that map to each part

3. **Proposal** (if conversation went well):
   - Draft formal proposal with:
     - Project scope (MVP features)
     - Timeline (9 weeks)
     - Milestones (Phase 1, 2, 3)
     - Deliverables (code, tests, docs, deployment)
     - Pricing ($11,000 fixed or $70/hr)
     - Payment terms (30% upfront, 40% at Phase 2, 30% at launch)

4. **Next steps**:
   - If they mention equity, ask: "What % equity for how much rate reduction?"
   - If they want to move fast, propose: "I can start next Monday - let's finalize scope by EOD Friday."
   - If they're evaluating multiple devs, say: "I'm available for a technical deep-dive call with your CTO if that helps."
