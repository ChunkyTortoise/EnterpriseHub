# Jorge Delivery Specification — Source of Truth

> **All agents MUST read this file before making any changes.**
> **Do NOT add features, abstractions, or "improvements" beyond what is listed here.**
> **If a task is not in JORGE_TASKS.md, do not do it.**

---

## 1. CLIENT CONTEXT

**Client**: Jorge Salas — real estate agent, Rancho Cucamonga CA
**Platform**: GoHighLevel (GHL) CRM
**Budget**: $150 fixed price
**Core Deliverable**: AI bots that qualify seller/buyer leads via SMS through GHL
**Quality Bar**: Responses must sound "100% human — like something a professional would actually write, not AI"

---

## 2. SELLER BOT SPECIFICATION (Primary Deliverable)

### 2.1 Trigger
- **Tag**: `Needs Qualifying` (ONLY this tag — NOT "Hit List")
- Bot activates immediately when this tag is applied
- Bot deactivates when any of: `AI-Off`, `Qualified`, `Stop-Bot`, `Seller-Qualified`

### 2.2 The 4 Questions (asked one at a time, in order)

| # | Type | Exact Text |
|---|------|-----------|
| Q1 | Motivation | "What's got you considering wanting to sell, where would you move to" |
| Q2 | Timeline | "If our team sold your home within the next 30 to 45 days, would that pose a problem for you" |
| Q3 | Condition | "How would you describe your home, would you say it's move-in ready or would it need some work" |
| Q4 | Price | "What price would incentivize you to sell" |

**Rules**:
- Ask ONE question at a time
- Wait for response before asking next
- If answer is vague, push for specifics before moving on
- If user answers multiple questions at once, acknowledge and continue to next unanswered

### 2.3 Temperature Classification

| Temperature | Criteria | Actions |
|-------------|----------|---------|
| **Hot** | All 4 questions answered + timeline accepted (30-45 days) + response quality >= 0.7 + responsive | Tag "Hot-Seller", move to priority call stage, notify human immediately |
| **Warm** | 3+ questions answered + response quality >= 0.5, timeline > 45 days or some hesitation | Tag "Warm-Seller", enter short-term nurture |
| **Cold** | Vague answers or stops responding, long timeline or just exploring | Tag "Cold-Seller", enter long-term nurture |

### 2.4 Follow-Up Logic

| Phase | Interval | Duration |
|-------|----------|----------|
| Active | Every 2-3 days | First 30 days |
| Long-term | Every 14 days | Ongoing after 30 days |

Schedule: Days 2, 5, 8, 11, 14, 17, 20, 23, 26, 29, then every 14 days.

### 2.5 Tone Rules (MANDATORY)

- Direct but natural
- Professional and human
- Short sentences, occasional commas instead of periods
- **NO emojis** — ever
- **NO hyphens** — ever
- No robotic phrasing
- Confrontational and straightforward
- Sound like a real person texting, not an AI
- SMS limit: < 160 characters

**Good examples** (Jorge's actual texting style):
- "Hey! What's up?"
- "sounds good. What time works best to talk?"
- "Sure, what price did you have in mind? whens a good time to talk?"
- "Would today around 2:00 or closer to 4:30 work better for you?"

**Bad examples** (AI-sounding — NEVER do this):
- "I understand your concerns about the timeline. Let me help you explore your options."
- "Thank you for sharing that information. Based on your responses..."
- "That's a great question! Here are some things to consider..."
- Any sentence with "I'd be happy to" or "Let me help you with that"

### 2.6 Exit Logic

If seller says "stop", "unsubscribe", "don't contact me", "not interested", "remove me", "no more messages", or any opt-out intent:
1. Apply "AI-Off" tag immediately
2. Send: "No problem at all, reach out whenever you're ready"
3. End ALL automation — no follow-ups, no messages

### 2.7 Hot Seller Handoff

When a seller qualifies as Hot:
1. Message: "[Name], based on your responses our team needs to speak with you today. What time works best for a quick call?"
2. Apply "Hot-Seller" tag
3. Trigger agent notification workflow
4. Remove "Needs Qualifying" tag

### 2.8 Initial Outreach

When "Needs Qualifying" tag is applied and no conversation exists:
- Bot sends first message proactively
- Tone: casual, friendly intro
- Example: "Hey [name], saw your property inquiry. Are you still thinking about selling?"
- Then waits for response before asking Q1

---

## 3. BUYER BOT SPECIFICATION

### 3.1 Purpose
Send people properties based on their criteria and follow up with them.

### 3.2 Qualification Flow
1. Analyze buyer intent (buying vs browsing)
2. Assess financial readiness (pre-approved? budget range?)
3. Extract property preferences (beds, baths, area, price range)
4. Match properties to criteria
5. Send property recommendations via SMS
6. Schedule follow-up actions

### 3.3 Buyer Temperature
- **Hot Buyer**: Pre-approved, specific budget, timeline < 3 months
- **Warm Buyer**: Working on financing, general preferences, 3-6 month timeline
- **Cold Buyer**: Browsing, no budget clarity, no timeline

### 3.4 Follow-Up
Same pattern as seller: 2-3 days for 30 days, then every 14 days.
Content: property updates, new listings matching criteria, market changes.

---

## 4. LEAD BOT SPECIFICATION

### 4.1 Purpose
Initial qualification to determine if lead is buyer or seller, then route to appropriate bot.

### 4.2 Flow
1. Receive incoming message
2. Detect intent (buyer vs seller vs unknown)
3. Begin qualification sequence (3-7-30 day pattern)
4. Route to seller or buyer bot based on detected intent

---

## 5. DASHBOARD SPECIFICATION

### 5.1 Requirements
Single Streamlit dashboard with 4 tabs:

**Tab 1: Lead Pipeline**
- Funnel: New → Qualifying → Hot / Warm / Cold
- Count per stage
- Conversion rates between stages

**Tab 2: Bot Activity**
- Recent conversations (last 20)
- Messages sent today / this week
- Average response time
- Bot uptime status

**Tab 3: Temperature Map**
- Pie/donut chart: Hot vs Warm vs Cold breakdown
- Trend line: temperature changes over time
- List of hot leads requiring immediate action

**Tab 4: Follow-Up Queue**
- Upcoming follow-ups (next 7 days)
- Overdue follow-ups
- Follow-up completion rate

### 5.2 Design
- Clean, professional (no "Obsidian Elite" theming)
- White/light background
- Standard Streamlit components
- Real data where available, clearly labeled mock data where not

---

## 6. GHL INTEGRATION MAP

### 6.1 Tags Used

| Tag | Applied When | Removed When |
|-----|-------------|-------------|
| Needs Qualifying | Manually by Jorge | Bot qualifies or deactivates |
| Hot-Seller | All 4 questions + timeline + quality | — |
| Warm-Seller | 3+ questions + decent quality | Becomes Hot |
| Cold-Seller | Vague/unresponsive | Becomes Warm/Hot |
| AI-Off | Seller opts out OR manual | — |
| Qualified | Handoff complete | — |
| Stop-Bot | Manual override | — |

### 6.2 Webhook Flow

```
GHL Incoming Message
    ↓
POST /api/ghl/webhook
    ↓
Check: "Needs Qualifying" in tags? → No → Return (no processing)
    ↓ Yes
Check: Any deactivation tag? → Yes → Return (bot deactivated)
    ↓ No
Check: Opt-out message? → Yes → Apply "AI-Off", send exit msg, return
    ↓ No
Route to JorgeSellerEngine.process_seller_response()
    ↓
Extract data → Calculate temperature → Generate response
    ↓
Apply tags + custom fields → Send response → Schedule follow-up
```

### 6.3 New Endpoint Needed

```
POST /api/ghl/initiate-qualification
Body: { contact_id, location_id }
Purpose: Send initial outreach when "Needs Qualifying" tag is applied
Jorge creates GHL workflow: Tag Applied → HTTP Request → This endpoint
```

### 6.4 Custom Fields Updated

| Field | Value |
|-------|-------|
| seller_temperature | hot / warm / cold |
| seller_motivation | Extracted from Q1 |
| timeline_urgency | Extracted from Q2 |
| property_condition | Extracted from Q3 |
| price_expectation | Extracted from Q4 |
| questions_answered | 0-4 |
| qualification_score | 0-100 |

---

## 7. CRITICAL FILES MAP

### Must Modify
| File | Change |
|------|--------|
| `ghl_real_estate_ai/ghl_utils/config.py` | Remove "Hit List" from activation_tags |
| `ghl_real_estate_ai/ghl_utils/jorge_config.py` | Add JORGE_SIMPLE_MODE flag |
| `ghl_real_estate_ai/api/routes/webhook.py` | Add opt-out detection, add initiate endpoint |
| `ghl_real_estate_ai/services/jorge/jorge_seller_engine.py` | Gate enterprise branches behind config |
| `ghl_real_estate_ai/prompts/system_prompts.py` | Review/tune for human tone |

### Must Verify (Read-Only)
| File | What to Verify |
|------|---------------|
| `ghl_real_estate_ai/services/jorge/jorge_tone_engine.py` | Tone enforcement working |
| `ghl_real_estate_ai/services/jorge/jorge_followup_engine.py` | Schedule matches spec |
| `ghl_real_estate_ai/services/jorge/jorge_followup_scheduler.py` | Scheduler functional |
| `ghl_real_estate_ai/agents/jorge_buyer_bot.py` | Buyer flow runs |
| `ghl_real_estate_ai/agents/jorge_seller_bot.py` | Seller flow runs |
| `ghl_real_estate_ai/agents/lead_bot.py` | Lead flow runs |
| `ghl_real_estate_ai/core/conversation_manager.py` | Context management works |

### Must Create
| File | Purpose |
|------|---------|
| `ghl_real_estate_ai/streamlit_demo/jorge_delivery_dashboard.py` | Focused 4-tab dashboard |
| `JORGE_DEPLOYMENT_GUIDE.md` | Setup instructions for Jorge |
| Integration test file | End-to-end webhook test |

---

## 8. ARCHITECTURE CONSTRAINTS

### DO
- Use existing services (ConversationManager, GHLClient, ToneEngine)
- Keep changes minimal and focused
- Test every change
- Follow existing code patterns (async/await, Pydantic models, logging)

### DO NOT
- Add new dependencies
- Create new abstractions or frameworks
- Add enterprise features (A/B testing, swarm intelligence, psychology analysis)
- Refactor existing code that works
- Add type annotations to code you didn't change
- Create documentation files beyond what's specified
- Over-engineer for hypothetical future requirements

---

## 9. TESTING REQUIREMENTS

### Seller Bot E2E Test
Simulate 5-message conversation:
1. Initial outreach → seller responds with interest
2. Q1 (motivation) → seller answers
3. Q2 (timeline) → seller accepts 30-45 days
4. Q3 (condition) → seller says move-in ready
5. Q4 (price) → seller gives number
→ Verify: temperature = "hot", tags = ["Hot-Seller"], "Needs Qualifying" removed

### Opt-Out Test
1. Mid-conversation seller says "stop"
→ Verify: "AI-Off" tag applied, exit message sent, no further processing

### Edge Cases
- No response after first question → follow-up triggers
- Vague answer → confrontational push for specifics
- Multiple answers in one message → skip ahead correctly
- Off-topic message → redirect to next question

---

## 10. DELIVERY CHECKLIST

```
[x] "Hit List" removed from activation_tags in config.py (A1)
[x] Opt-out message detection added to webhook (A5)
[x] Enterprise response branches gated behind JORGE_SIMPLE_MODE (A3)
[x] Duplicate arbitrage code removed from seller_engine (A4)
[x] Initiate-qualification endpoint created (A6)
[x] Buyer bot verified end-to-end (B2)
[x] Focused 4-tab dashboard created (C1-C6)
[x] Integration tests pass — 19/19 (D1-D4, D6)
[x] Deployment guide written (D5)
[ ] All responses sound human in testing — NEEDS LIVE REVIEW
```
