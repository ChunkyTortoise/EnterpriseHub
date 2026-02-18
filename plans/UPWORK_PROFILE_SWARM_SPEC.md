# Upwork Profile Swarm Execution Spec
**Created**: 2026-02-17
**Status**: Ready for Execution
**Parent Bead**: EnterpriseHub-y920
**Agent Deployment**: Parallel Multi-Agent Swarm (5 agents)

---

## Mission Overview

Complete all Upwork profile improvements and content creation identified in the audit session.
The goal is maximum hiring conversion: get profile to 100% completeness, create all written assets
agents can produce, and set up the quick-close job strategy to earn first reviews.

**Agents Required**: 5
**What agents CAN do**: Write all copy, create all files, generate structured content
**What agents CANNOT do**: Log into Upwork, record video, click profile UI (human actions)

All output files go to: `/Users/cave/Documents/GitHub/EnterpriseHub/content/upwork/`

---

## Context: Your Portfolio Strengths

Use these throughout all copy. These are verified, benchmark-backed numbers.

```
KEY METRICS (verified):
- 89% LLM cost reduction via 3-tier Redis caching (88% hit rate)
- 4.3M tool dispatches/sec in AgentForge core engine
- <200ms orchestration overhead (P99: 0.095ms)
- 8,500+ automated tests across 11 repos, all CI green
- 33 Architecture Decision Records across 10 repos
- 3 CRM integrations: GoHighLevel, HubSpot, Salesforce
- 5 live Streamlit demos (prospects can try before hiring)
- 1 PyPI package published: mcp-server-toolkit
- P95 latency <300ms under 10 req/sec load

LIVE DEMOS:
- Prompt Lab: https://ct-prompt-lab.streamlit.app/
- LLM Starter: https://ct-llm-starter.streamlit.app/
- AgentForge: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

REPOS (public, GitHub: ChunkyTortoise):
- EnterpriseHub: CRM integrations (GHL, HubSpot, Salesforce) + chatbot
- ai-orchestrator (AgentForge): multi-agent system, 4.3M dispatch/sec
- docqa-engine: RAG Q&A, BM25+TF-IDF+semantic, citation tracking
- insight-engine: Streamlit analytics, anomaly detection, forecasting
- scrape-and-serve: async scraper + REST API
- mcp-toolkit: FastMCP v2 server toolkit (also on PyPI)
- prompt-engineering-lab: prompt versioning, safety checker
- llm-integration-starter: circuit breaker, streaming, fallback chains
- jorge_real_estate_bots: real estate AI (lead/buyer/seller bots)

TARGET RATE: $65-75/hr hourly | $55-60/hr entry rate (first 3-5 jobs)
LOCATION: Palm Springs, CA (Remote only)
PROFILE URL: upwork.com/freelancers/caymanroden
```

---

## Agent Deployment Plan

### Wave 1: Core Profile Copy (All Start Simultaneously)

**Agent 1 — Profile Copywriter**: Headline + Overview + Skills tags
**Agent 2 — Specialized Profiles Architect**: 3 specialized profile pages
**Agent 3 — Proposal Rewriter**: Rewrite/upgrade 5 existing proposals

### Wave 2: Quick-Close Strategy (Start After Wave 1)

**Agent 4 — Quick-Close Job Researcher**: Identify job types + write 3 targeted proposals
**Agent 5 — Video Script Writer**: Video intro script + portfolio item copy

---

## Detailed Task Specifications

---

### AGENT 1: Profile Copywriter

**Objective**: Write the complete Upwork main profile text — headline, overview, and skills list.

**Output file**: `content/upwork/profile-update.md`

**Context on Upwork's algorithm**:
- First ~200 chars of overview are shown in search results — lead with ROI
- Upwork indexes skill tags for search — match exactly what clients search
- Profile is scored on keyword density + completeness + engagement signals

---

#### DELIVERABLE 1: Headline (max 100 chars)

Write 3 headline variants. Client will pick one. Each must:
- Be keyword-rich (terms clients actually search)
- Lead with outcome, not role title
- Stay under 100 characters

Format:
```
HEADLINE OPTIONS:
Option A: [text] ([X] chars)
Option B: [text] ([X] chars)
Option C: [text] ([X] chars)

RECOMMENDATION: Option [X] — reason
```

Target keywords to include (across all 3 options):
`RAG`, `LLM`, `AI Agent`, `Multi-Agent`, `FastAPI`, `Python`, `ChatGPT`, `Claude API`, `cost reduction`

---

#### DELIVERABLE 2: Overview (max 5,000 chars, aim 600-800 words)

**Structure (follow exactly)**:

**Hook** (first 3 sentences — shown in search snippet):
- Lead with a bold ROI/outcome claim
- Mention a specific metric
- State who you help

**What I Build** (3-5 bullet points):
- RAG & document AI systems
- Multi-agent orchestration pipelines
- AI chatbots with CRM integration (GHL, HubSpot, Salesforce)
- Production analytics dashboards (Streamlit)
- LLM cost optimization (caching, fallback chains)

**Proof Section** (numbered list of 5-7 metrics):
Use the key metrics above. Format as: "X result via Y method"

**Tech Stack** (one clean line each category):
- AI/ML: Claude API, GPT-4, Gemini, RAG (BM25/TF-IDF/semantic), LangChain alternatives
- Backend: FastAPI (async), SQLAlchemy, Pydantic, Alembic
- Databases: PostgreSQL, Redis (3-tier caching), ChromaDB, FAISS
- Testing: pytest, TDD, 80%+ coverage standard
- DevOps: Docker, GitHub Actions CI/CD

**Who I Work With** (2-3 sentences):
- Startups building first AI product
- Engineering teams adding AI to existing stack
- Founders who need production-quality code, not demos

**CTA** (1-2 sentences):
- Specific, low-friction next step
- Mention live demos are available

---

#### DELIVERABLE 3: Skills Tag List

Research and list exactly 15 skill tags optimized for Upwork search. Format:

```
SKILLS (paste into Upwork skills section in this order):
1. Large Language Models (LLM)
2. ...
[continue to 15]

RATIONALE: [1 sentence on ordering strategy]
```

Priority: high-search-volume tags first. Include a mix of:
- AI/ML specific (RAG, LLM, AI Agents, Prompt Engineering)
- Tech stack (Python, FastAPI, PostgreSQL)
- Outcome-oriented (Chatbot Development, API Development)

---

#### DELIVERABLE 4: Hourly Rate Recommendation

Write a 3-paragraph analysis:
1. Current market rate for AI/ML engineers on Upwork (2026)
2. Entry-rate strategy rationale (why $55-60/hr to get first reviews)
3. Rate ladder: what triggers moving to $65 → $75 → $85/hr

---

**Save to**: `content/upwork/profile-update.md`

**Format the file as**:
```markdown
# Upwork Profile Update
Generated: [date]

## Headline Options
[content]

## Overview (Ready to Paste)
[content]

## Skills Tags (Ordered)
[content]

## Rate Strategy
[content]

## Human Action Checklist
- [ ] Copy headline into Upwork profile title field
- [ ] Paste overview into About section
- [ ] Add skills in the order listed
- [ ] Set hourly rate to $[X]/hr
- [ ] Connect GitHub account (Settings > Connected Services)
```

---

### AGENT 2: Specialized Profiles Architect

**Objective**: Write 3 complete Upwork Specialized Profiles — separate landing pages that dramatically increase search surface area.

**Output file**: `content/upwork/specialized-profiles.md`

**Background on Upwork Specialized Profiles**:
Upwork allows up to 5 specialized profiles. Each has its own:
- Headline (100 chars)
- Overview (5,000 chars)
- Skills (up to 10 tags)
- Hourly rate (can differ from main)
- Portfolio items

Each specialized profile gets its own search ranking. This effectively creates 3 separate "listings" — 3x the discoverability.

---

#### SPECIALIZED PROFILE 1: RAG & Document AI Systems

**Target clients**: Companies needing document Q&A, knowledge bases, enterprise search, contract analysis, PDF processing.

**Target job searches**: "RAG engineer", "document AI", "knowledge base", "PDF chatbot", "semantic search", "LLM document processing"

Write:
- **Headline** (3 variants, pick best)
- **Overview** (400-500 words):
  - Hook: what problem this solves (slow document search, hallucinating chatbots)
  - What you build specifically
  - Technical proof points (docqa-engine metrics, BM25+semantic hybrid)
  - Relevant case: real estate doc AI, enterprise RAG
  - CTA with demo link
- **Skills** (10 tags optimized for this niche)
- **Portfolio item**: Write title + 150-word description for docqa-engine

---

#### SPECIALIZED PROFILE 2: AI Chatbot & CRM Integration

**Target clients**: Agencies using GoHighLevel, HubSpot, or Salesforce who want to add AI chatbots. Real estate companies, SaaS startups with CRM workflows.

**Target job searches**: "GoHighLevel AI", "HubSpot chatbot", "CRM integration AI", "AI chatbot developer", "Claude chatbot", "GPT-4 chatbot integration"

Write:
- **Headline** (3 variants, pick best)
- **Overview** (400-500 words):
  - Hook: "Your CRM has 10,000 leads. Your team can't call all of them."
  - What you build (chatbot that qualifies leads, logs to CRM, triggers workflows)
  - Relevant case: jorge_real_estate_bots (GHL, buyer/seller/lead bots)
  - EnterpriseHub CRM adapters (GHL, HubSpot, Salesforce — unified protocol)
  - CTA
- **Skills** (10 tags)
- **Portfolio item**: Write title + 150-word description for EnterpriseHub / jorge bots

---

#### SPECIALIZED PROFILE 3: Multi-Agent AI Systems & LLM Orchestration

**Target clients**: Engineering teams building autonomous AI workflows, research pipelines, content automation, data processing pipelines.

**Target job searches**: "AI agent developer", "LangChain developer", "AutoGen", "multi-agent", "LLM orchestration", "AI automation", "ReAct agent"

Write:
- **Headline** (3 variants, pick best)
- **Overview** (400-500 words):
  - Hook: lead with 4.3M dispatches/sec and the testing-first approach
  - What you build (orchestrators, agent meshes, evaluation frameworks)
  - Technical depth: ReAct loop, circuit breakers, token cost tracking
  - Why testing matters for AI agents (non-deterministic behavior)
  - CTA with AgentForge demo link
- **Skills** (10 tags)
- **Portfolio item**: Write title + 150-word description for AgentForge

---

**File format**:
```markdown
# Upwork Specialized Profiles
Generated: [date]

---

## Specialized Profile 1: RAG & Document AI Systems

### Headline Options
...

### Overview (Ready to Paste)
...

### Skills (10 tags, ordered)
...

### Portfolio Item Description
...

---

## Specialized Profile 2: AI Chatbot & CRM Integration
[same structure]

---

## Specialized Profile 3: Multi-Agent AI Systems & LLM Orchestration
[same structure]

---

## Human Action Checklist
- [ ] Go to Upwork > Profile > Specialized Profiles > Create New
- [ ] Create Profile 1: [title], paste headline + overview + skills
- [ ] Create Profile 2: [title], paste headline + overview + skills
- [ ] Create Profile 3: [title], paste headline + overview + skills
- [ ] Add portfolio item to each specialized profile
```

---

### AGENT 3: Proposal Rewriter

**Objective**: Rewrite all 5 existing Upwork proposals to maximize conversion using the ROI-first framework from the audit.

**Read first** (these files exist):
- `content/upwork/proposals/proposal-1-semantic-rag.md`
- `content/upwork/proposals/proposal-2-education-rag.md`
- `content/upwork/proposals/proposal-3-rag-debugging.md`
- `content/upwork/proposals/proposal-4-modular-ai-platform.md`
- `content/upwork/proposals/proposal-5-support-chatbot.md`

**Output**: Rewrite each file in-place. Add `## Rewrite Notes` section at bottom of each.

---

**Proposal Formula (apply to all 5)**:

```
LINE 1-2: Mirror the client's specific problem back to them.
           DO NOT start with "Hi, I'm Cayman" or "I saw your job posting".
           START with: "You need [specific thing they described]."

LINE 3-4: One relevant metric or proof point tied to their specific need.
           Link to the most relevant live demo.

LINE 5-8: Brief description of your exact approach for THIS job.
           Be specific — mention their stack/tools if they mentioned them.
           Show you read the posting.

LINE 9-11: Social proof or relevant portfolio item.
            Reference the specific repo or demo that maps to their problem.

LAST LINE: Low-friction CTA.
           "Available for a 15-minute call this week — or I can send a
            working prototype of [specific thing] if that's more useful."
```

**Word count target**: 150-250 words. Not more. Clients skim.

**Tone**: Confident and direct. No hedging ("I think I could", "I believe"). No flattery ("Great project!"). No boilerplate.

**For each proposal, add at the bottom**:
```markdown
## Rewrite Notes
- Key change: [what the main improvement was]
- Hook used: [first line]
- Demo linked: [URL]
- Estimated conversion lift: [why this version is stronger]
```

---

### AGENT 4: Quick-Close Job Strategy

**Objective**: Create a strategy and 3 ready-to-send proposals specifically targeting small, fast-close jobs ($150-$500 fixed price) designed to earn first reviews quickly.

**Output file**: `content/upwork/quick-close-strategy.md`

**Background**:
The main blocker to getting hired on Upwork with 0 reviews is that clients default to
experienced freelancers. The fastest path to first review is:
1. Target small scope, fast-deliverable jobs ($150-$500)
2. Propose a scoped deliverable that takes 4-8 hrs to complete
3. Deliver fast, ask for review
4. Repeat 3-5 times to build JSS, then move up-market

---

#### DELIVERABLE 1: Quick-Close Job Types

Research and document 5 specific job categories that:
- Are common on Upwork (high volume of postings)
- Match your skills perfectly
- Can be delivered in 4-8 hours
- Typically pay $150-$500 fixed

For each category write:
```
Category: [name]
Typical posting title: [example]
Typical budget: $X-$Y
Deliverable: [exactly what you'd deliver]
Time to complete: [hours]
Your edge: [why you specifically win these]
```

---

#### DELIVERABLE 2: Three Ready-to-Send Proposals

Write 3 complete proposals for these specific job types. These are template proposals
that can be sent with minor customization (<5 min per send).

**Proposal A: "Debug My RAG System" / "Fix LLM Retrieval Quality"**
- Target: someone whose RAG is returning wrong/hallucinated answers
- Deliverable: diagnosis + fix recommendations + code patch
- Price range to propose: $200-$400
- Time: 4-6 hours

**Proposal B: "Build a Simple Streamlit Dashboard"**
- Target: someone needing data visualization from CSV/API
- Deliverable: working Streamlit app deployed on Streamlit Cloud
- Price range to propose: $150-$350
- Time: 3-5 hours

**Proposal C: "Integrate ChatGPT/Claude into My Python App"**
- Target: developer who has a Python app and wants to add AI
- Deliverable: working LLM integration with streaming, error handling
- Price range to propose: $200-$400
- Time: 4-6 hours

**Each proposal** (use the formula from Agent 3):
150-200 words, ROI hook first, link a relevant demo, specific scoped deliverable, direct CTA.

---

#### DELIVERABLE 3: First-Review Playbook

Write a 500-word playbook covering:
1. How to find and filter quick-close jobs (Upwork search filters)
2. How to customize the template proposals in <5 min
3. What to do after getting hired (communication, speed, delivery)
4. Exactly how/when to ask for the review
5. When to raise rates (after 3 reviews with 5-star JSS)

---

**File format**:
```markdown
# Quick-Close Job Strategy
Generated: [date]

## Job Categories (5)
[content]

## Ready-to-Send Proposals

### Proposal A: Debug My RAG System
[content]

### Proposal B: Build a Streamlit Dashboard
[content]

### Proposal C: Integrate LLM into Python App
[content]

## First-Review Playbook
[content]

## Human Action Checklist
- [ ] Set Upwork search filters: Fixed price, $150-$500, Posted: Last 24 hours
- [ ] Search: "RAG debugging" | "Streamlit dashboard" | "ChatGPT integration"
- [ ] Send 2-3 proposals per day using templates above
- [ ] After delivery: send review request message (template in playbook)
```

---

### AGENT 5: Video Intro Script + Portfolio Items

**Objective**: Write the video intro script and portfolio item copy for 5 portfolio pieces.

**Output file**: `content/upwork/video-and-portfolio.md`

---

#### DELIVERABLE 1: Video Intro Script (90 seconds)

Upwork video intros are shown on your profile. They're the single highest-conversion element
after reviews. Clients who watch videos hire at ~3x the rate.

Write a script for a 90-second video (approximately 220-240 words at natural speaking pace).

**Structure**:
```
[0:00-0:10] Hook: bold opening statement (not "Hi I'm Cayman")
[0:10-0:25] What you build + who you help (specific, not generic)
[0:25-0:50] One concrete example with a metric
             ("I built a RAG system that cut document search time by 80%...")
[0:50-1:10] Your process / what makes you different
             (testing-first, production-ready, not just demos)
[1:10-1:25] Social proof: 8,500 tests, live demos, PyPI package
[1:25-1:30] CTA: "I'd love to hear about your project"
```

**Tone**: Confident, warm, direct. Not salesy. Technical but not jargon-heavy.
**Format the script with**: [ACTION] cues for where to gesture/show screen.

Also write:
- **Thumbnail text** (what text to overlay on the video thumbnail, max 8 words)
- **Recording tips** (5 bullet points on setup: lighting, background, delivery pace)

---

#### DELIVERABLE 2: Portfolio Item Copy (5 items)

Write title + 200-word description for each portfolio item.
Clients read these before deciding to contact. Lead with the problem solved and outcome,
then tech details.

**Portfolio Item 1: AgentForge — Multi-Agent AI Orchestration**
- Repo: ai-orchestrator
- Demo: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
- Key metric: 4.3M tool dispatches/sec, <200ms P99 overhead

**Portfolio Item 2: Document Q&A Engine (RAG)**
- Repo: docqa-engine
- Key metrics: BM25+semantic hybrid, 500+ tests, <200ms P95

**Portfolio Item 3: Enterprise CRM AI Integration**
- Repo: EnterpriseHub
- Key metrics: 3 CRM adapters (GHL, HubSpot, Salesforce), unified protocol, ~5,100 tests

**Portfolio Item 4: Real Estate AI Bot System**
- Repo: jorge_real_estate_bots
- Key metrics: Lead/Buyer/Seller bots, PostgreSQL, Redis cache, 360+ tests

**Portfolio Item 5: LLM Integration Starter (PyPI Package)**
- Repo: mcp-toolkit + llm-integration-starter
- Key metrics: Published on PyPI as mcp-server-toolkit, circuit breaker, streaming, 250+ tests

**Format for each**:
```
### [Title]
**Problem solved**: [1 sentence]
**What I built**: [2-3 sentences]
**Results/metrics**: [bullet list]
**Tech used**: [comma list]
**Live demo / repo**: [URL]
```

---

**File format**:
```markdown
# Video Intro & Portfolio Items
Generated: [date]

## Video Intro Script (90 seconds)
[script with timing markers and action cues]

## Thumbnail Text
[text]

## Recording Tips
[5 bullets]

---

## Portfolio Items

### 1. AgentForge — Multi-Agent AI Orchestration
[content]

### 2. Document Q&A Engine (RAG)
[content]

### 3. Enterprise CRM AI Integration
[content]

### 4. Real Estate AI Bot System
[content]

### 5. LLM Integration Starter (PyPI Package)
[content]

---

## Human Action Checklist
- [ ] Record video intro using script above (phone camera is fine, good lighting matters most)
- [ ] Upload to Upwork: Profile > Video Introduction > Upload
- [ ] Add portfolio items: Profile > Portfolio > Add Work
- [ ] For each item: title, description, screenshot of live demo or repo
- [ ] Link live demo URL in each portfolio item
```

---

## Bead Management

After all agents complete, update these beads:

### Close (agents do this as they finish each file)
- `bd comment EnterpriseHub-y920 "Agent [N] completed: [filename]"` as each file is written

### Create new child beads (human action items agents can't do)

After writing all files, create the following child beads under `EnterpriseHub-y920`:

```bash
# Bead: Record video intro
bd create EnterpriseHub-y920-video \
  --title "Upwork: Record and upload video intro" \
  --priority P1 \
  --type task \
  --description "Script ready at content/upwork/video-and-portfolio.md. 90-second script. Phone camera OK. Upload to Profile > Video Introduction. Est: 30 min."

# Bead: Apply profile update  
bd create EnterpriseHub-y920-profile \
  --title "Upwork: Manually apply profile-update.md to profile" \
  --priority P1 \
  --type task \
  --description "Copy from content/upwork/profile-update.md. Update headline, overview, skills, rate. Est: 15 min."

# Bead: Create specialized profiles
bd create EnterpriseHub-y920-specprofiles \
  --title "Upwork: Create 3 specialized profiles" \
  --priority P1 \
  --type task \
  --description "Content ready at content/upwork/specialized-profiles.md. Profile > Specialized Profiles > Add. Est: 30 min."

# Bead: Add portfolio items
bd create EnterpriseHub-y920-portfolio \
  --title "Upwork: Add 5 portfolio items" \
  --priority P2 \
  --type task \
  --description "Descriptions at content/upwork/video-and-portfolio.md. Add screenshots of live demos. Est: 30 min."

# Bead: Connect GitHub
bd create EnterpriseHub-y920-github \
  --title "Upwork: Connect GitHub account" \
  --priority P2 \
  --type task \
  --description "Settings > Connected Services > GitHub. 2 min."

# Bead: Quick-close campaign
bd create EnterpriseHub-y920-quickclose \
  --title "Upwork: Send 2-3 quick-close proposals daily (first reviews)" \
  --priority P1 \
  --type task \
  --description "Strategy + templates at content/upwork/quick-close-strategy.md. Target: 3 reviews in 30 days. Use search filters: Fixed price $150-500, Last 24hr."
```

### Close parent when all files are written
```bash
bd close EnterpriseHub-y920 --reason "All Upwork content created: profile-update.md, specialized-profiles.md, proposals rewritten, quick-close-strategy.md, video-and-portfolio.md"
```

---

## Output Summary

| File | Agent | Contents |
|------|-------|----------|
| `content/upwork/profile-update.md` | Agent 1 | Headline (3 variants), overview, skills, rate strategy |
| `content/upwork/specialized-profiles.md` | Agent 2 | 3 full specialized profile pages |
| `content/upwork/proposals/proposal-1-semantic-rag.md` | Agent 3 | Rewritten |
| `content/upwork/proposals/proposal-2-education-rag.md` | Agent 3 | Rewritten |
| `content/upwork/proposals/proposal-3-rag-debugging.md` | Agent 3 | Rewritten |
| `content/upwork/proposals/proposal-4-modular-ai-platform.md` | Agent 3 | Rewritten |
| `content/upwork/proposals/proposal-5-support-chatbot.md` | Agent 3 | Rewritten |
| `content/upwork/quick-close-strategy.md` | Agent 4 | Job types, 3 proposals, playbook |
| `content/upwork/video-and-portfolio.md` | Agent 5 | 90-sec script, 5 portfolio descriptions |

---

## Human Action Items (After Agents Complete)

All of these require manual Upwork UI interaction:

| Priority | Action | Time | Source File |
|----------|--------|------|-------------|
| P1 | Apply profile headline + overview + skills | 15 min | `profile-update.md` |
| P1 | Create 3 specialized profiles | 30 min | `specialized-profiles.md` |
| P1 | Record + upload video intro | 30 min | `video-and-portfolio.md` |
| P1 | Send 2-3 quick-close proposals daily | 15 min/day | `quick-close-strategy.md` |
| P2 | Connect GitHub account | 2 min | Settings > Connected Services |
| P2 | Add 5 portfolio items | 30 min | `video-and-portfolio.md` |
| P2 | Set hourly rate per recommendation | 2 min | `profile-update.md` |
