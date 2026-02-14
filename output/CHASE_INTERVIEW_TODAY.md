# Chase Ashley Interview Package - AI Secretary SaaS

**Date**: Thursday, February 12, 2026 at 10am Pacific (1pm EST)  
**Company**: FloPro Jamaica  
**Project**: Development of AI Agent Secretary / Personal Assistant  
**Status**: ⏳ TODAY - 4 HOURS FROM NOW

---

## ⚡ URGENT: Pre-Interview Checklist

### Right Now (4 hours before)
- [ ] Review this document completely
- [ ] Practice elevator pitch out loud 3 times
- [ ] Practice portfolio walkthrough (aim for 4.5 minutes)
- [ ] Review common Q&A answers

### 30 Minutes Before (9:30am PT)
- [ ] Open GitHub portfolio: github.com/ChunkyTortoise
- [ ] Open EnterpriseHub README with architecture diagram
- [ ] Open interview showcase: `EnterpriseHub/interview_showcase/README.md`
- [ ] Open benchmark results: `EnterpriseHub/benchmarks/RESULTS.md`
- [ ] Test screen share + audio on Upwork
- [ ] Glass of water nearby
- [ ] Bathroom break
- [ ] Close Slack, email, notifications
- [ ] Quiet room, headphones, good lighting

---

## 🎯 Quick Win Opening (30 seconds - MEMORIZE THIS)

> "I've built a production multi-agent system that handles exactly this - task routing, calendar integration, and intelligent handoffs between specialized agents. For your AI secretary, I'd use a task classification layer that routes incoming requests to domain-specific sub-agents: calendar, email drafting, research, reminders. Let me walk you through the architecture."

---

## 📊 Your Core Metrics (Memorize)

| Metric | Value |
|--------|-------|
| Total Tests | 8,500+ |
| EnterpriseHub Tests | 5,100+ |
| Orchestration Overhead | <200ms (P99: 0.095ms) |
| Cache Hit Rate | 88% |
| LLM Cost Reduction | 89% |
| Training Hours | 1,768 |
| Certifications | 21 |

---

## 🏗️ Architecture Proposal for AI Secretary

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
│    "entities": {"contact": "Sarah", "duration": 30, ...}   │
│  }                                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
           ┌─────────────┼─────────────┬──────────────┐
           │             │             │              │
   ┌───────▼───┐ ┌──────▼─────┐ ┌────▼──────┐ ┌────▼────────┐
   │ Calendar  │ │   Email    │ │ Research  │ │  Reminder   │
   │   Agent   │ │   Agent    │ │   Agent   │ │   Agent     │
   │(GCal/Outlook)│(Gmail API)│ │(Web search)│ │(Push/SMS)  │
   └───────┬───┘ └──────┬─────┘ └────┬──────┘ └─────┬───────┘
           └────────────┴─────────────┴──────────────┘
                              │
                 ┌────────────▼─────────────┐
                 │   PostgreSQL + Redis     │
                 │  - User preferences      │
                 │  - Conversation history  │
                 │  - Task queue            │
                 │  - Cached responses      │
                 └──────────────────────────┘
```

### Why This Architecture Works

1. **Task Classification First**: Cheap, fast routing (Claude Haiku = $0.00025/request)
2. **Specialized Agents**: Each agent optimized for its domain
3. **Shared State**: PostgreSQL for persistence, Redis for speed
4. **Scalable**: Add new agents without changing existing code

---

## 🔧 Technical Implementation Details

### 1. Gmail/Outlook OAuth Integration

```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from cryptography.fernet import Fernet

async def connect_gmail(user_id: str, auth_code: str):
    """Exchange auth code for tokens, store encrypted"""
    credentials = await exchange_auth_code(auth_code)
    
    # Encrypt and store tokens
    encrypted_tokens = fernet.encrypt(json.dumps({
        "access_token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
    }).encode())
    
    await db.execute(
        "INSERT INTO email_connections (user_id, provider, encrypted_tokens) VALUES ($1, $2, $3)",
        user_id, "gmail", encrypted_tokens
    )
    
    return {"status": "connected", "email": credentials.id_token.get("email")}
```

### 2. Calendar Availability Detection

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
    
    # Apply user preferences
    business_hours = preferences.get("business_hours", {"start": 9, "end": 17})
    buffer_minutes = preferences.get("buffer_minutes", 15)
    
    slots = generate_slots(busy_times, duration_minutes, business_hours, buffer_minutes)
    return slots
```

### 3. Email Drafting with Approval Workflow

```python
async def draft_email(user_id: str, intent: str, context: dict) -> dict:
    """Draft email using templates + LLM customization"""
    template = EMAIL_TEMPLATES.get(intent, "")
    
    response = await claude.messages.create(
        model="claude-3-haiku-20240307",
        messages=[{"role": "user", "content": f"""
        You are drafting an email. Template: {template}
        Context: {json.dumps(context)}
        Customize naturally. Output only the email body.
        """}],
        max_tokens=500
    )
    
    draft = response.content[0].text
    
    # Save draft for user review (NEVER auto-send by default)
    await db.execute(
        "INSERT INTO email_drafts (user_id, recipient, subject, body, status) VALUES ($1, $2, $3, $4, 'pending_review')",
        user_id, context["recipient"], context["subject"], draft
    )
    
    return {"draft_id": draft_id, "body": draft}
```

### 4. User Preference Learning

```python
async def learn_from_edits(user_id: str, original_draft: str, edited_draft: str):
    """Learn from user edits to improve future drafts"""
    prompt = f"""
    Compare these two email drafts and identify what the user prefers:
    
    Original: {original_draft}
    Edited: {edited_draft}
    
    What patterns can we infer? (tone, structure, phrases)
    Output as JSON.
    """
    
    insights = await claude.messages.create(...)
    await update_preferences(user_id, insights)
```

---

## 💬 Mock Q&A - Practice These

### Q: "How would you handle email prioritization?"

**A**: "Multi-factor scoring system:

1. **Sender importance**: Check if sender is in priority_contacts list
2. **Content urgency**: Claude classifies as 'urgent', 'important', 'routine'
3. **Context clues**: Keywords like 'ASAP', 'deadline' boost priority
4. **Time sensitivity**: Meeting requests for next 24 hours = high priority

Score formula: `priority = (sender × 0.4) + (urgency × 0.3) + (keywords × 0.2) + (time × 0.1)`

Present top 5 in dashboard, auto-respond to routine stuff, flag urgent for immediate attention."

### Q: "What about data privacy for email content?"

**A**: "Critical for trust. My approach:

1. **Encryption at rest**: Fernet encryption for all email content in PostgreSQL
2. **Encryption in transit**: TLS 1.3 for all API calls
3. **Zero-knowledge option**: User's encryption key derived from password
4. **Minimal retention**: Auto-delete after 30 days unless saved
5. **Access controls**: Each user only accesses their own data
6. **GDPR compliance**: Data export, right to be forgotten

For enterprise, offer on-premise deployment where they run it on their own infrastructure."

### Q: "How do you prevent the secretary from sending embarrassing emails?"

**A**: "Multi-layer safety:

1. **Default to draft mode**: Secretary NEVER sends without user approval
2. **Confidence scoring**: If confidence <0.8, require review
3. **Dry-run mode**: First 2 weeks - drafts everything, sends nothing
4. **Audit trail**: Log every draft with reasoning
5. **Undo/recall**: 30-second grace period (Gmail API supports this)
6. **Profanity filter**: Block offensive language
7. **Recipient whitelist**: 'Only send to these domains' rule

User can adjust auto-send aggressiveness in settings."

### Q: "How would you monetize this SaaS?"

**A**: "Freemium + tiered pricing:

| Tier | Price | Features |
|------|-------|----------|
| Free | $0 | 50 AI actions/month, 1 email account |
| Pro | $19/mo | 500 actions, 3 accounts, advanced preferences |
| Team | $49/user/mo | Unlimited, shared scheduling, Slack integration |
| Enterprise | Custom | On-premise, SSO, custom training |

Additional revenue: Usage overages ($0.10/action), add-ons (CRM integration $10/mo), API access ($99/mo)"

### Q: "What's your timeline to MVP?"

**A**: "Based on my existing EnterpriseHub codebase:

**Phase 1 - Core Secretary (4 weeks)**:
- Week 1-2: Gmail OAuth, email fetching, task classification
- Week 3: Calendar API, availability detection
- Week 4: Email drafting, review UI

**Phase 2 - Multi-Tenant SaaS (3 weeks)**:
- Week 5: User registration, auth, tenant isolation
- Week 6: Stripe billing, usage tracking
- Week 7: Admin dashboard

**Phase 3 - Polish & Launch (2 weeks)**:
- Week 8: Security audit, performance optimization
- Week 9: Beta testing, bug fixes, launch

**Total: 9 weeks to production-ready MVP**

Assumptions: 20-25 hrs/week, you handle UI/UX design, we use existing services (Stripe, Twilio)."

---

## 🎤 Questions to Ask Chase

1. **"What's your target market - individuals or businesses?"**
   - Affects feature prioritization

2. **"Do you have UI/UX designs already?"**
   - If no, I can recommend design systems

3. **"What's your expected launch date?"**
   - Align timeline with expectations

4. **"Are you open to using existing services (Stripe, Twilio, SendGrid)?"**
   - Faster than building in-house

5. **"What's your biggest concern - speed to market, cost optimization, or feature richness?"**
   - Helps prioritize tradeoffs

---

## 🛠️ Assets to Screen Share

### Primary Assets

1. **GitHub Portfolio**: github.com/ChunkyTortoise
   - Show EnterpriseHub README with architecture diagram
   - Highlight: 5,100+ tests, CI green

2. **Key Code Files**:
   - `services/agent_mesh_coordinator.py` - Task routing
   - `services/claude_orchestrator.py` - Multi-strategy parsing
   - `services/jorge/jorge_handoff_service.py` - Handoff logic

3. **Benchmark Results**: `EnterpriseHub/benchmarks/RESULTS.md`
   - <200ms latency
   - 88% cache hit rate
   - 89% cost reduction

### Live Demo (If Time Permits)

```bash
cd EnterpriseHub/interview_showcase
docker compose up --build
```

- Open http://localhost:8501
- Click "Run Chase Scenario"
- Show: deterministic routing, approval workflow, cache metrics

---

## 💰 Rate Discussion

### Your Rates

| Type | Rate |
|------|------|
| Hourly | $65-75/hr |
| Custom Project | $1,500-$4,000 |
| Enterprise Phase | $8,000-$12,000 |

### For This Project

**MVP Estimate**: ~$11,000 fixed
- 9 weeks × 20 hrs/week × $65/hr = $11,700
- Round to $11,000 for simplicity

**Or Hourly**: $70/hr, estimated 180 hours = $12,600

---

## 📋 Closing Script

> "Thanks for walking me through the project, Chase. This aligns perfectly with my experience - I've already built the core architecture you need in EnterpriseHub. I'm excited about the AI secretary concept and the potential for FloPro Jamaica.
>
> I'll send you a follow-up with an architecture diagram specifically for your use case tomorrow morning. 
>
> What's the best next step from your perspective - would you like a detailed proposal, or should we do a deeper technical dive first?"

---

## 📞 Post-Interview Actions

### Within 2 Hours

Send thank-you message on Upwork:
```
Hi Chase,

Thanks for taking the time to discuss the AI Secretary project today. I'm excited about building this for FloPro Jamaica - the task classification and multi-agent architecture we discussed is exactly what I've implemented in EnterpriseHub.

I'll put together an architecture diagram and share it tomorrow morning.

Looking forward to next steps.

Best,
Cayman
```

### Within 24 Hours

Create and share:
1. 1-page architecture diagram for AI Secretary
2. Detailed proposal with timeline and pricing
3. Link to interview showcase demo

---

## 🚨 Emergency Backup Plan

**If internet drops**:
- "Apologies, my connection dropped. Can I call you back in 2 minutes?"
- Have phone ready for backup

**If screen share fails**:
- "Let me paste the GitHub links in chat instead."
- github.com/ChunkyTortoise

**If you blank on a question**:
- "That's a great question - let me think through the architecture for a moment."
- Pause, refer to notes

**If they ask something you don't know**:
- "I haven't implemented that specific scenario yet, but here's how I'd approach it..."
- Be honest, show problem-solving

---

## ✅ Success Signals

**Good signs**:
- They ask about timeline/availability
- They mention budget expectations
- They want to introduce you to team
- They ask for a proposal
- They share concerns openly

**Red flags**:
- Vague requirements
- Unrealistic timeline
- Budget shopping
- Free spec work requests

---

## 📞 Your Contact Info

- **Email**: caymanroden@gmail.com
- **Phone**: (310) 982-0492 (Pacific Time)
- **GitHub**: github.com/ChunkyTortoise
- **Portfolio**: chunkytortoise.github.io
- **LinkedIn**: linkedin.com/in/caymanroden
- **Availability**: 20-25 hrs/week, can start immediately

---

**Good luck! You've got this. 🚀**

**Remember**: You've already built what they need. You're not asking for a chance - you're offering a solution.
