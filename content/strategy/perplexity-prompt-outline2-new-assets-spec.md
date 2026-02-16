# Perplexity Deep Research Prompt — Outline 2: New Assets Technical Spec

**Purpose**: Generate a comprehensive, agent-executable technical specification for building 5 new products + 3 micro-SaaS from existing code. The output must be detailed enough that a team of AI coding agents can execute tasks in parallel without human clarification.

---

## PROMPT (copy everything below this line)

```
I need you to research and synthesize a COMPREHENSIVE TECHNICAL SPECIFICATION for
building 5 new AI/ML products and 3 micro-SaaS wrappers. These will be built by a
swarm of AI coding agents working in parallel — so every task must be self-contained
with exact file structures, API signatures, dependency versions, and acceptance criteria.

## CONTEXT: MY EXISTING TECH STACK & CODE TO REUSE

All products are Python 3.11+, use pytest (8,500+ tests across 11 repos), Docker +
GitHub Actions CI, and follow these conventions:
- FastAPI for APIs (async)
- Pydantic v2 for schemas
- SQLAlchemy + Alembic for ORM/migrations
- Redis for caching (3-tier: L1 in-memory, L2 Redis, L3 persistent)
- PostgreSQL for persistence
- Claude/GPT/Gemini for AI reasoning
- Streamlit for dashboards
- Stripe for billing (MCP server already configured)
- snake_case files/functions, PascalCase classes, SCREAMING_SNAKE_CASE constants

### Existing Code That New Products MUST Reuse

| Repo | Reusable Components | Tests |
|------|-------------------|-------|
| **EnterpriseHub** | LeadBot/BuyerBot/SellerBot conversation engines, GHL CRM client (10 req/s rate limit), handoff orchestrator (0.7 confidence threshold), calendar booking service, Redis 3-tier cache, Stripe integration, A/B testing service, performance tracker (P50/P95/P99) | 5,100 |
| **ai-orchestrator (AgentForge)** | Multi-agent mesh, model registry, guardrails, ReAct loop, tool dispatch (4.3M/sec) | 550 |
| **docqa-engine** | RAG pipeline, cross-encoder re-ranking, multi-hop QA, query expansion, 89% cost reduction caching | 500 |
| **insight-engine** | Anomaly detection, KPI frameworks, SHAP, statistical testing, forecasting, Streamlit components | 640 |
| **scrape-and-serve** | Web scraping framework, data pipelines, content intelligence, data quality | 370 |
| **mcp-server-toolkit** | MCP server framework (already on PyPI as mcp-server-toolkit 0.1.0) | 185 |
| **prompt-engineering-lab** | Prompt versioning, safety checker, template management | 220 |

## THE 5 NEW PRODUCTS + 3 MICRO-SAAS TO BUILD

### PRODUCT 1: Voice AI Agent Platform for Real Estate
**Revenue target**: $5K-20K/mo | **Competition**: Low (45/100)

Build a turnkey voice AI system that handles inbound/outbound real estate calls —
lead qualification, appointment scheduling, buyer/seller follow-up. Leverages
EnterpriseHub's existing chatbots, GHL CRM, and handoff orchestration.

**Architecture:**
```
Phone Provider (Twilio/Vonage) → WebSocket → Deepgram STT (streaming)
    → Claude/GPT (intent + response generation, reuse LeadBot logic)
    → ElevenLabs TTS (streaming) → WebSocket → Phone Provider
                    ↕
        EnterpriseHub APIs (lead scoring, GHL sync, handoff, calendar booking)
```

**Phases:**
- **MVP (80 hrs)**: Single-bot voice agent for lead qualification
  - Deepgram STT streaming integration
  - Conversation engine wrapping existing LeadBot
  - ElevenLabs TTS with configurable real estate agent persona
  - GHL appointment booking via existing calendar service
  - Call recording + transcript storage (PostgreSQL)

- **V1 (40 hrs)**: Multi-bot with analytics
  - Voice handoff between lead/buyer/seller bots (reuse handoff orchestrator)
  - Call analytics dashboard (reuse Insight Engine Streamlit components)
  - Sentiment tracking during calls

- **V2 (40 hrs)**: Multi-tenant productization
  - Tenant isolation
  - Client onboarding wizard (Streamlit)
  - Usage-based billing via Stripe (per-minute or subscription tiers)
  - White-label voice personas

**I need researched:**
- Deepgram Python SDK: streaming STT WebSocket API, event model, interim vs final
  results, language/model selection, pricing per minute
- ElevenLabs Python SDK: streaming TTS WebSocket API, voice cloning process,
  latency optimization, pricing per character
- Twilio Voice API vs Vonage: WebSocket media streams, pricing, Python SDK for
  programmable voice, SIP trunking
- Real-time voice AI architecture patterns: how to minimize end-to-end latency
  (target: <500ms response time), interrupt handling (barge-in detection),
  silence detection, turn-taking
- LiveKit / Daily.co / Pipecat: evaluate as voice AI infrastructure layer vs
  building directly on Twilio + Deepgram + ElevenLabs
- Voice AI compliance: call recording consent (two-party states), AI disclosure
  requirements, TCPA considerations for outbound

### PRODUCT 2: MCP Server Toolkit & Marketplace
**Revenue target**: $3K-8K/mo products + $5K-15K/project services | **Competition**: Very Low (35/100)

Expand existing PyPI package (mcp-server-toolkit 0.1.0) into a collection of
7 production-ready MCP servers plus an enhanced framework for building custom ones.

**7 MCP Servers to build:**

| # | Server | Reuse From | Core Function |
|---|--------|-----------|---------------|
| 1 | Database Query | New | Natural language → SQL for Postgres/MySQL/SQLite |
| 2 | Web Scraping | scrape-and-serve | Agent-driven scraping with structured extraction |
| 3 | CRM (GoHighLevel) | EnterpriseHub | AI agents query/update GHL CRM |
| 4 | File Processing | docqa-engine | PDF/CSV/Excel parsing for agent consumption |
| 5 | Email | New | Send/read/search emails via IMAP/SMTP |
| 6 | Calendar | EnterpriseHub | Booking/scheduling from agent workflows |
| 7 | Analytics | insight-engine | Query dashboards + generate insights |

**Phases:**
- **V1 (30 hrs)**: Enhanced framework + servers 1, 2, 4 (database, scraping, file)
- **V2 (30 hrs)**: Servers 3, 5, 6, 7 + Gumroad product page + lead magnet guide

**I need researched:**
- MCP Python SDK (latest stable, Feb 2026): complete server implementation API,
  tool/resource/prompt definition patterns, transport options (stdio, SSE, HTTP),
  authentication mechanisms
- MCP specification changes since initial release: any breaking changes, new
  capabilities (sampling, roots, elicitation), security model updates
- Existing MCP server implementations to study: what patterns do the official
  Anthropic MCP servers follow? What's the standard project structure?
- Text-to-SQL approaches: which library/model works best for natural language → SQL?
  (e.g., sqlglot, vanna.ai, DuckDB + LLM, raw prompt engineering)
- MCP marketplace/registry landscape: is there an emerging marketplace for MCP
  servers? How are others distributing/monetizing them?

### PRODUCT 3: AI Agent Compliance & Governance Toolkit
**Revenue target**: $2K-6K/mo | **Competition**: Low (40/100)

Framework-agnostic compliance layer that works with LangGraph, CrewAI, AgentForge,
or any custom agent system. Provides audit logging, content policy enforcement, cost
controls, PII detection, and explainability reporting.

**7 Components:**
1. **Audit Trail Logger** — structured logs of every agent action + decision (15 hrs)
2. **Content Policy Engine** — configurable rules for output filtering (15 hrs)
3. **Cost Controller** — per-agent/per-user budget limits with alerts (10 hrs)
4. **PII Detector** — real-time PII scanning in agent I/O (12 hrs)
5. **Explainability Reporter** — compliance reports from audit trails (15 hrs)
6. **Framework Adapters** — hooks for LangGraph, CrewAI, AgentForge (20 hrs)
7. **Monitoring Dashboard** — Streamlit UI (13 hrs)

**Phases:**
- **V1 (50 hrs)**: Components 1-4 + adapters for AgentForge + LangGraph
- **V2 (50 hrs)**: Components 5-7 + CrewAI adapter + full documentation

**I need researched:**
- AI governance frameworks and standards (Feb 2026): NIST AI RMF, EU AI Act
  requirements, ISO 42001, SOC 2 for AI systems — what specific controls must
  a compliance toolkit implement?
- PII detection libraries: Presidio (Microsoft), spaCy NER, AWS Comprehend,
  Google DLP — which is best for real-time agent I/O scanning? Benchmark
  accuracy, latency, and cost
- Agent observability tools: LangSmith, LangFuse, Helicone, Braintrust —
  what audit/logging patterns do they use? What gaps exist that a compliance
  toolkit can fill?
- Content policy patterns: how do OpenAI, Anthropic, and Google implement
  output filtering? What's the standard taxonomy for content categories?
- Cost control mechanisms: how to implement per-request token budgets,
  per-user spending limits, and alerting thresholds in a framework-agnostic way
- LangGraph middleware/callback patterns (latest API): how to inject
  pre/post-processing hooks without modifying user code
- CrewAI callback/event system: how to intercept agent actions for logging

### PRODUCT 4: Cohort-Based Course — "Production AI Agent Engineering"
**Revenue target**: $20K-80K/cohort | **Competition**: Medium (60/100)

6-week live course using my 11 repos as hands-on labs. Need complete course
infrastructure spec.

**Course structure:**
| Week | Topic | Lab Repo |
|------|-------|---------|
| 1 | Multi-Agent Architecture | AgentForge |
| 2 | Production RAG Pipelines | DocQA Engine |
| 3 | MCP Servers & Tool Integration | mcp-server-toolkit |
| 4 | Agent Orchestration & Handoffs | EnterpriseHub |
| 5 | Testing, Monitoring & Observability | Insight Engine |
| 6 | Deployment, Scaling & Cost Optimization | Docker/CI/Redis |

**I need researched:**
- Course platform comparison (Feb 2026): Kajabi vs Podia vs Circle vs Maven vs
  Teachable vs self-hosted. Compare: pricing, cohort features (live sessions,
  community, drip content, certificates), payment processing fees, API access
- Landing page builders for course pre-launch: Carrd, Webflow, Typedream,
  or build with Streamlit? Which converts best for technical courses?
- Waitlist tools: ConvertKit vs Beehiiv vs Buttondown for technical audience.
  Features needed: landing page, email sequences, referral program
- Discord vs Slack for course community: which is standard for technical
  cohort courses? Setup, bot integrations, async Q&A patterns
- Live session tooling: Zoom vs StreamYard vs Riverside for recorded teaching
  sessions with screen share + code walkthroughs
- Certificate generation: tools for issuing completion certificates (Certifier,
  Accredible, custom)
- Pricing psychology for technical courses: what price anchoring and tier
  structure converts best? Research Maven, Reforge, and similar platforms
- Marketing for cohort launches: proven pre-launch sequences (how many
  emails, what content, when to open enrollment, scarcity tactics)

### PRODUCT 5: Hosted RAG-as-a-Service (SaaS)
**Revenue target**: $3K-10K/mo | **Competition**: Medium (65/100)

Multi-tenant SaaS wrapper around DocQA Engine with web upload, API access,
team management, and usage-based Stripe billing.

**Architecture:**
```
Client → FastAPI (API Gateway) → Auth (JWT + API Keys) → Tenant Router
    → DocQA Engine (per-tenant index isolation)
    → PostgreSQL (multi-tenant: schema-per-tenant or RLS)
    → Redis (per-tenant caching with namespace isolation)
    → Stripe (usage metering + subscription management)
```

**Phases:**
- **MVP (40 hrs)**: Single-tenant, API key auth, document upload, query, Stripe checkout
- **V1 (40 hrs)**: Multi-tenant isolation, web UI, team management, usage dashboard

**I need researched:**
- Multi-tenant PostgreSQL patterns: schema-per-tenant vs row-level security (RLS)
  vs database-per-tenant. Pros/cons for a SaaS with <100 tenants initially.
  How to implement with SQLAlchemy + Alembic migrations
- Vector store multi-tenancy: how to isolate document embeddings per tenant.
  ChromaDB collections, Qdrant namespaces, pgvector schemas — which approach?
- Stripe usage-based billing: metered billing API, usage record reporting,
  invoice generation. Exact Python implementation with stripe-python SDK
- API key management: best practices for issuing, rotating, rate-limiting
  API keys in FastAPI. Libraries: fastapi-key-auth, custom middleware patterns
- SaaS onboarding flows: what's the minimum viable signup → first-value
  experience for a developer-focused RAG SaaS?
- Deployment: Railway vs Render vs Fly.io vs self-hosted VPS for a
  FastAPI + PostgreSQL + Redis SaaS. Compare pricing at 10, 100, 1000 users

### MICRO-SAAS 1: Agent Monitoring Dashboard
**Source**: Insight Engine + AgentForge | **Revenue**: $29-199/mo | **Effort**: 40 hrs

Observability SaaS for AI agent fleets — latency, cost, success rate, error
tracking. Streamlit frontend + FastAPI backend.

### MICRO-SAAS 2: Web Data Pipeline API
**Source**: Scrape-and-Serve | **Revenue**: $39-299/mo | **Effort**: 30 hrs

Scheduled scraping + LLM extraction as a hosted API service.

### MICRO-SAAS 3: Prompt Registry SaaS
**Source**: Prompt Toolkit | **Revenue**: $19-99/mo | **Effort**: 25 hrs

Team prompt versioning, A/B testing, and analytics as a hosted service.

## WHAT I NEED YOU TO RESEARCH AND PRODUCE

For EACH product/micro-SaaS above, produce a detailed technical spec:

### 1. Architecture & Design
- **System architecture diagram** (component-level): services, databases,
  external APIs, message flows
- **Data models**: exact SQLAlchemy/Pydantic definitions for all new entities
- **API design**: REST endpoints with method, path, request/response schemas,
  auth requirements
- **Configuration**: environment variables, config files, feature flags
- **Dependencies**: exact PyPI packages with version pins (research latest
  stable as of Feb 2026)

### 2. Repository Structure
- **New repo or module within existing repo?** — recommend for each product
- **Exact file/directory layout** following my existing conventions
- **Shared libraries** that should be extracted for cross-product reuse
- **Docker setup**: Dockerfile, docker-compose with all services
- **CI/CD**: GitHub Actions workflow for test + lint + build + deploy

### 3. External Service Integration Specs
For every external service (Deepgram, ElevenLabs, Twilio, Stripe, etc.):
- **SDK version** and installation
- **Authentication pattern** (API keys, OAuth, WebSocket tokens)
- **Rate limits** and how to handle them
- **Pricing** per unit (critical for margin calculations)
- **Python code pattern** for the most common operation
- **Error handling**: what errors to expect and recovery strategies

### 4. Implementation Blueprint
For each component:
- **Algorithm/approach**: specific technique with rationale
- **Error handling**: failure modes and recovery
- **Performance targets**: latency (P50/P95/P99), throughput, memory
- **Security**: input validation, auth, encryption, data isolation
- **Scaling path**: how it grows from 1 to 100 to 1000 users

### 5. Testing Strategy
- **Unit tests**: boundaries, mocks, assertions
- **Integration tests**: end-to-end with real services (or stubs)
- **Load tests**: scenarios and expected performance
- **Minimum test count per product** (target 80%+ coverage)

### 6. Parallel Execution Plan (CRITICAL)
Structure the ENTIRE spec for maximum parallelism:

- **Phase 1 (Weeks 1-4)**: Which products/components can be built simultaneously?
  Group into 3-5 independent workstreams.
- **Phase 2 (Weeks 5-8)**: What builds on Phase 1? What's newly parallelizable?
- **Phase 3 (Weeks 9-12)**: Integration, testing, productization
- **Shared contracts**: Define ALL cross-product interfaces upfront so agents
  building different products don't conflict
- **Integration points**: Exact moments where products connect, with contract tests

### 7. Go-to-Market Technical Requirements
For each product:
- **Gumroad product page**: what screenshots/demos are needed
- **Documentation site**: what's the minimum docs for launch (quickstart,
  API reference, examples)
- **Demo/sandbox**: what's needed for prospects to try before buying
- **Monitoring**: what metrics to track post-launch (Sentry, PostHog, custom)

### 8. Cost Analysis
For each product:
- **Infrastructure cost** at 10, 100, 1000 users/month
- **API costs** (LLM tokens, STT/TTS minutes, etc.) per request
- **Margin analysis**: revenue per user minus costs
- **Break-even point**: how many users to cover fixed costs

## OUTPUT FORMAT

Structure as a comprehensive spec document with:
1. **Shared Contracts section** at the top (interfaces used by multiple products)
2. **Per-product sections** that are self-contained (an agent reads ONE section
   and can implement it completely)
3. **Dependency graph** showing build order and parallelism
4. **Risk register**: what could go wrong and mitigations
5. Tables for all API signatures, dependency lists, file structures, and cost models
6. Code snippets for critical interface definitions and integration patterns

The goal: a team of 5-8 AI coding agents should be able to read this spec,
each claim a workstream, and build in parallel for 4 weeks with minimal
coordination overhead.
```
