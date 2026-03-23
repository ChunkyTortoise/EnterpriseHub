# GTM Workflow Builder — Statement of Work Template

**Version**: 1.0 | **Date**: 2026-02-19 | **Provider**: Cayman Roden — AI/ML Engineer

---

## About This Service

I build end-to-end GTM automation systems that connect your sales conversations directly to your CRM, automatically generate proposals, and define your ideal customer profile — all powered by AI agents integrated with GoHighLevel via MCP.

**Core differentiator**: GHL MCP integration means your automations don't just write content — they execute CRM actions, update contact fields, trigger workflows, and move deals through your pipeline in real time.

---

## Service Tiers

---

### Tier 1 — GTM Starter | $2,500

**Ideal for**: Solo consultants and small agencies ready to automate their first sales workflow.

#### Deliverables

| # | Deliverable | Description |
|---|-------------|-------------|
| 1 | GHL Audit + Integration Setup | Review existing GHL instance, configure MCP connection, map contact fields and pipeline stages |
| 2 | Proposal-from-Transcript Agent | AI agent that ingests a sales call transcript and outputs a structured proposal draft (PDF-ready) |
| 3 | ICP Definition Document | AI-generated ICP from your last 20-30 closed/lost contacts using GHL field data |
| 4 | 1 Automated Workflow | One GHL trigger → AI action → GHL update sequence (e.g., new lead → score → tag → assign) |
| 5 | Handoff Documentation | Setup guide, prompt templates, how-to-run runbook |

#### Timeline

| Week | Milestones |
|------|-----------|
| 1 | GHL audit, MCP setup, field mapping |
| 2 | Proposal agent build + ICP extraction |
| 3 | Workflow automation + testing |
| 4 | QA, documentation, handoff call |

**Total**: 4 weeks

#### Payment Terms

- 50% upfront ($1,250) to begin
- 50% on delivery ($1,250)
- Payment via Stripe or wire

---

### Tier 2 — GTM Growth | $3,500

**Ideal for**: Agencies and sales teams who want a full AI-powered GTM stack, not just one workflow.

#### Deliverables

*Includes everything in Tier 1, plus:*

| # | Deliverable | Description |
|---|-------------|-------------|
| 6 | 3 Automated Workflows | Lead routing, follow-up sequence trigger, deal stage transition — all GHL-native |
| 7 | Outreach Personalization Agent | AI agent that pulls contact data from GHL and writes personalized outreach sequences |
| 8 | Weekly GTM Status Report | Automated digest: new leads, proposals sent, pipeline movement, response rates |
| 9 | 30-Day Support Window | Bug fixes, prompt tuning, minor workflow adjustments via async Slack/email |

#### Timeline

| Week | Milestones |
|------|-----------|
| 1 | GHL audit, MCP setup, 3-workflow mapping |
| 2 | Proposal agent + ICP extraction |
| 3 | Outreach agent + 3 workflows built |
| 4 | Status report setup, integration testing |
| 5 | QA, documentation, handoff |

**Total**: 5 weeks

#### Payment Terms

- 40% upfront ($1,400) to begin
- 30% at midpoint — Week 3 ($1,050)
- 30% on delivery ($1,050)
- Payment via Stripe or wire

---

### Tier 3 — GTM Enterprise | $5,000

**Ideal for**: Teams managing $50K+ in monthly pipeline who need a production-grade GTM intelligence layer.

#### Deliverables

*Includes everything in Tier 1 + Tier 2, plus:*

| # | Deliverable | Description |
|---|-------------|-------------|
| 10 | Revenue Intelligence Dashboard | Streamlit app: pipeline value, deal velocity, conversion rates, weekly trends — refreshes from GHL + Stripe |
| 11 | Multi-Agent Orchestration | Agents coordinate: transcript → proposal → CRM update → outreach trigger — one end-to-end flow |
| 12 | Custom MCP Tool (if needed) | Build a bespoke MCP tool for any GHL action not covered by standard toolset |
| 13 | A/B Test Framework | Test 2 outreach variants, track response rates, auto-select winner after 50 sends |
| 14 | 90-Day Support Window | Priority bug fixes, model upgrades, new workflow additions as scope allows |
| 15 | Monthly Strategy Call | 60-min monthly review: what's working, what to optimize, next month's roadmap |

#### Timeline

| Week | Milestones |
|------|-----------|
| 1 | Full GHL audit, architecture design sign-off |
| 2-3 | Core agents: proposal, ICP, outreach |
| 4-5 | Workflows + orchestration layer |
| 6 | Revenue dashboard + A/B framework |
| 7 | Integration testing, load testing |
| 8 | QA, documentation, onboarding call |

**Total**: 8 weeks

#### Payment Terms

- 33% upfront ($1,650) to begin
- 33% at midpoint — Week 4 ($1,650)
- 34% on delivery ($1,700)
- Payment via Stripe or wire

---

## Scope Boundaries (All Tiers)

### In Scope
- GHL MCP integration and configuration
- AI agent development (Claude claude-sonnet-4-6 or Haiku depending on task)
- Prompt engineering and optimization
- GHL contact field mapping and workflow design
- Testing with real data samples (provided by client)
- Documentation and runbooks
- Video walkthrough of each deliverable

### Out of Scope
- GHL account creation or subscription management
- Data migration from other CRMs
- Website or landing page development
- Ad copy or paid media
- Legal review of communications
- Ongoing AI API costs (client provides own Anthropic key)

---

## Technical Requirements (Client-Side)

| Requirement | Tier 1 | Tier 2 | Tier 3 |
|-------------|--------|--------|--------|
| GHL account (any plan) | Required | Required | Required |
| Anthropic API key | Required | Required | Required |
| Access to 20+ closed contacts in GHL | Recommended | Required | Required |
| Stripe account | Optional | Optional | Required |
| 3 sales call transcripts (any format) | Required | Required | Required |

---

## Change Order Policy

Changes to scope after kickoff are billed at $75/hr. Any change increasing scope by >20% requires a new SOW. Minor adjustments (prompt tuning, field remapping) within the 30/90-day support window are included.

---

## Intellectual Property

All code, prompts, and workflows delivered are owned by the client upon final payment. Cayman Roden retains the right to use anonymized architecture patterns as portfolio case studies unless the client requests confidentiality in writing.

---

## How to Engage

1. Book a 30-min scoping call: [calendly link]
2. Receive customized SOW based on your GHL setup and goals
3. Sign + pay upfront deposit to begin
4. Weekly async check-ins via Slack or Loom

**Contact**: cayman@[domain] | LinkedIn: [profile]

---

## Appendix A: GHL MCP Integration Overview

The GHL MCP (Model Context Protocol) server exposes GoHighLevel's API as a set of AI-callable tools. This means AI agents in this system can:

- **Read**: contacts, conversations, pipeline stages, custom fields, tags, calendars
- **Write**: update contact fields, add tags, create notes, trigger workflows, book appointments
- **Search**: find contacts by field value, query pipeline stages, retrieve conversation history

This is not a webhook integration or Zapier automation. The AI agent reasons about what CRM action to take and executes it directly — with full context from the conversation or transcript that triggered it.

**Example flow** (Tier 1 Proposal Agent):
```
Sales call recording → Transcription → Proposal Agent (Claude)
  → Reads GHL contact fields for this prospect
  → Generates scoped proposal with real numbers
  → Creates proposal note in GHL contact record
  → Tags contact "Proposal-Sent"
  → Triggers GHL "Follow-Up Sequence" workflow
```

---

## Appendix B: Sample ICP Output Format

```
## Ideal Customer Profile — [Client Name]

### Demographics
- Company size: 5-25 employees
- Industry: Real estate, insurance, financial services
- Role: Founder or VP Sales

### Behavioral Signals (from GHL data)
- Responded within 24 hours to initial outreach
- Had a phone/video call before closing
- Pipeline stage "Proposal Sent" → "Closed Won" in < 14 days

### Anti-ICP Signals
- Opened emails but never replied
- Budget objection raised in call notes
- "Research" tag applied by previous agent

### Recommended Messaging Angles
- Specific ROI metric from similar clients
- Speed to first result ("live in 2 weeks")
- Done-for-you vs. DIY positioning
```
