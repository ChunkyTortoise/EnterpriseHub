# Continuation Prompt — Jorge GHL Bots Finalization

Paste this into a new Claude Code chat to continue where we left off.

---

## PROMPT

```
We're finalizing Jorge's GHL real estate lead qualification bots. This is overdue client work.

## Context
- Codebase: /Users/cave/Projects/EnterpriseHub_new/
- Beads issue: EnterpriseHub-m9zc (open)
- 3 bots: Lead, Buyer, Seller (LangGraph + Claude AI + GHL CRM)
- 205 tests, 70/70 Jorge-specific tests passing
- Code-level fixes completed in last session (SMS, disclosure, prompts, fallbacks)

## What was done last session
1. Full audit of all Jorge bot files (architecture, prompts, config, tests, deployment)
2. Fixed SMS length mismatch (160→320 aligned across config + pipeline + .env)
3. Fixed SMS truncation to preserve AI disclosure footer (SB 243 compliance)
4. Tightened seller 4-question flow wording
5. Added persona-aware stall responses with response pools (no more template fatigue)
6. Rewrote compliance fallbacks in Jorge's conversational voice
7. Improved buyer bot fallback variety
8. Created JORGE_GHL_SETUP_GUIDE.md (step-by-step for GHL dashboard)
9. Wrote Perplexity Deep Research prompt (8 sections, not yet submitted)

## What needs to happen now (prioritized)
1. **Deploy the app** — Railway/Render/Fly.io configs exist. Need a public webhook URL for GHL.
2. **Run Perplexity deep research** — Prompt is in this file below. Paste into Perplexity Deep Research mode.
3. **Wire up Jorge's GHL account** — Follow JORGE_GHL_SETUP_GUIDE.md. Need Jorge's login or his help.
4. **CMA data decision** — Either get Attom API key ($99/mo) OR disable CMA for now (set SELLER_ENABLE_CMA=false in .env). Bot works fine without it.
5. **Live smoke test** — DEPLOYMENT_CHECKLIST.md has the full procedure.
6. **Multi-worker deployment** — Wire handoff service to Redis backend (currently in-memory).

## Key files to read first
- ghl_real_estate_ai/agents/JORGE_GHL_SETUP_GUIDE.md
- ghl_real_estate_ai/agents/DEPLOYMENT_CHECKLIST.md
- ghl_real_estate_ai/ghl_utils/jorge_config.py (lines 1-155 for questions + config)
- ghl_real_estate_ai/config/jorge_bots.yaml
- .env (lines 220-240 for Jorge settings)

## Critical finding from audit
CMA generation is 100% mock data (hardcoded 4bd/3ba/2800sqft, fake comp addresses). The Attom API client is built but disabled (ENABLE_MLS_INTEGRATION=false, ATTOM_API_KEY empty). Jorge CANNOT use CMA with real sellers until this is resolved.

Pick up from step 1 (deployment) unless I say otherwise.
```

---

## Perplexity Deep Research Prompt

```
I'm building an AI-powered real estate lead qualification system for a realtor (Jorge)
in Rancho Cucamonga, CA using GoHighLevel (GHL) as the CRM. The system has 3 autonomous
chatbots that communicate via SMS through GHL:

1. **Lead Bot** — Initial lead temperature assessment (Hot/Warm/Cold), routes to Buyer
   or Seller bot based on intent signals
2. **Buyer Bot** — Financial readiness scoring (pre-approval, budget, DTI calculation),
   property preference extraction, affordability calculation, persona classification
   (first-time buyer, investor, upgrader, relocation, downsizer)
3. **Seller Bot** — 4-question simple qualification flow: (1) property address,
   (2) motivation/relocation reason, (3) timeline (can you sell in 30-45 days?),
   (4) property condition (move-in ready vs needs work). Includes CMA generation,
   stall detection, and psychology-aware response strategies.

**Tech stack:** FastAPI backend, LangGraph orchestration, Claude AI for response
generation, PostgreSQL + Redis caching, GHL API v2 for CRM sync (custom fields,
tags, workflows, calendar booking).

**Current capabilities:**
- Cross-bot handoff with circular prevention, rate limiting (3/hr, 10/day per contact)
- Response pipeline: language detection, TCPA opt-out (STOP/unsubscribe), FHA/RESPA
  compliance checking, SB 243 AI disclosure footer, SMS truncation (320 chars)
- Calendar auto-booking for HOT sellers via GHL calendar API
- Tag-based routing: "Needs Qualifying" → Lead/Seller, "Buyer-Lead" → Buyer,
  "AI-Off"/"Stop-Bot" → deactivation
- Temperature-based workflow triggers (Hot/Warm/Cold → different GHL automation
  workflows)
- 205 passing integration tests, all against mocked services

**I need expert guidance on these specific areas:**

### 1. GHL Bot Best Practices (2025-2026)
- What are the current best practices for building AI chatbots inside GoHighLevel?
- What GHL-native features should we leverage vs. custom-build? (e.g., GHL's built-in
  AI bot "Conversation AI" vs. our custom Claude-powered bot)
- Should we use GHL's Conversation AI as a fallback or replacement for any part of
  our system?
- What are the recommended GHL webhook patterns for inbound/outbound message handling?
- Are there GHL Marketplace apps or third-party integrations that solve parts of this
  better than custom code?

### 2. Real Estate Lead Qualification Best Practices
- What questions do top-performing ISAs (Inside Sales Agents) ask buyer and seller
  leads in the first SMS conversation?
- Is our 4-question seller qualification flow optimal? What's missing?
- For buyer qualification via SMS, what's the ideal conversation flow to determine
  financial readiness without being pushy?
- What conversion rate benchmarks should we target for SMS-based AI lead qualification
  in Southern California real estate (2025-2026)?
- How do top teams handle the "I'm just looking" / window shopper objection via text?

### 3. SMS Compliance & Deliverability
- What are the current TCPA, A2P 10DLC, and carrier filtering requirements for
  automated real estate SMS in California (2025-2026)?
- Are there specific phrases or patterns that trigger carrier spam filters?
- What's the recommended message cadence (frequency, timing) to avoid being flagged?
- Does California SB 243 (AI disclosure) actually apply to SMS conversations, and
  what's the exact compliance requirement?
- Should we be using a dedicated SMS provider (Twilio, etc.) instead of GHL's built-in
  messaging?

### 4. CMA (Comparative Market Analysis) Automation
- What data sources can we integrate for automated CMA generation without MLS access?
- Are there APIs (Zillow, Redfin, ATTOM, CoreLogic, Realtor.com) that provide comp
  data suitable for automated seller conversations?
- What's the legal/ethical boundary for providing automated property valuations to
  sellers via chatbot?
- What accuracy should we expect from automated vs. agent-prepared CMAs?

### 5. Deployment & Production Architecture
- What's the best hosting approach for a FastAPI + Redis + PostgreSQL real estate
  bot system? (Railway, Render, AWS, DigitalOcean, etc.)
- What's the recommended architecture for handling GHL webhook traffic at scale
  (100-1000 leads/month)?
- How should we handle webhook reliability (retries, dead letter queue, idempotency)?
- What monitoring and alerting setup is standard for production chatbot systems?

### 6. Competitive Landscape
- What are the top AI chatbot solutions for real estate lead qualification in 2025-2026?
  (e.g., Structurely, Ylopo, Chime, kvCORE, Sierra, CINC, Follow Up Boss)
- How does a custom-built Claude-powered system compare to these off-the-shelf
  solutions?
- What features do the best solutions offer that we might be missing?
- What's the typical pricing for these solutions, and what's the cost advantage of
  custom-building?

### 7. Conversation Design & Psychology
- What conversation design patterns maximize SMS engagement for real estate leads?
- How should bot personality/tone differ for buyer vs. seller leads?
- What are the best objection-handling frameworks for automated real estate conversations?
- When should the bot hand off to a human, and what's the optimal handoff message?
- How do you handle leads who respond days or weeks later (re-engagement)?

### 8. GHL-Specific Technical Questions
- What's the optimal GHL pipeline setup for bot-qualified leads?
- Should we use GHL Opportunities for tracking bot-qualified leads?
- What custom fields are most useful for real estate bot qualification data?
- How should GHL workflows be structured to complement (not conflict with) our
  bot automation?
- What GHL reporting/analytics should we set up to measure bot performance?

Please provide actionable, specific recommendations with examples where possible.
Prioritize recommendations by impact (what will most improve lead conversion) and
effort (what's easiest to implement). Include any recent changes to GHL's platform,
TCPA regulations, or the real estate AI landscape from 2025-2026.
```
