# Agent Execution Plan: All-Parallel Workstream Assignments

> **Total Effort**: ~395 hours across 6 parallel workstreams
> **Timeline**: 12 weeks (Weeks 1-12)
> **Agents**: 6 specialized builder agents + 1 coordinator
> **Revenue Target**: $8K-$15K by Week 8, $25K-$50K by Week 12

---

## Overview

Six workstreams launch simultaneously on Day 1. Three are fully independent (WS-3, WS-6, and the first week of all others). Three depend on WS-1 shared infrastructure completing by end of Week 2. Every workstream produces a deployable, revenue-generating product.

| # | Workstream | Agent | Hours | Depends On | First Revenue |
|---|-----------|-------|-------|------------|---------------|
| WS-1 | Shared Infrastructure | `infra-lead` | 30 | None | -- (enabler) |
| WS-2 | Voice AI Platform | `voice-ai-builder` | 160 | WS-1 | Week 8 |
| WS-3 | MCP Server Toolkit | `mcp-builder` | 60 | None | Week 6 |
| WS-4 | AI DevOps Suite | `devops-suite-builder` | 55 | WS-1 | Week 8 |
| WS-5 | RAG-as-a-Service | `rag-builder` | 80 | WS-1 | Week 8 |
| WS-6 | Course + GTM | `course-gtm-lead` | 40+ | None | Week 6 |

### Dependency Graph

```
Week 1          Week 2          Week 3+
────────────────────────────────────────────────────

WS-1 ██████████████▶ DONE
  │                   │
  │    ┌──────────────┼──────────────┐
  │    │              │              │
  ▼    ▼              ▼              ▼
WS-2 ░░░░░░░░░░░░░░████████████████████████████████▶ Week 12
       (scaffold)     (integrates shared-schemas)

WS-4 ░░░░░░░░░░░░░░████████████████████████▶ Week 10
       (scaffold)     (integrates shared-schemas)

WS-5 ░░░░░░░░░░░░░░████████████████████████████████▶ Week 12
       (scaffold)     (integrates shared-schemas)

WS-3 ██████████████████████████████████████▶ Week 8
      (fully independent)

WS-6 ██████████████████████████████████████████████▶ Week 12+
      (fully independent)

░░░ = can scaffold, but blocked on WS-1 for shared packages
███ = unblocked, full speed
```

---

## WS-1: Shared Infrastructure

| Field | Value |
|-------|-------|
| **Agent** | `infra-lead` |
| **Hours** | 30 |
| **Dependencies** | None |
| **Unblocks** | WS-2, WS-4, WS-5 |
| **Repo** | `shared-schemas/` (published as `shared-schemas` PyPI package) |

### Purpose

Create the foundational packages that all product repos import: tenant models, auth middleware, Stripe billing wrappers, and CI/CD templates. This is the critical path -- if it slips, three workstreams stall.

### Repository Structure

```
shared-schemas/
├── shared_schemas/
│   ├── __init__.py              # Package exports
│   ├── tenant.py                # TenantConfig, TenantTier enum, TenantLimits
│   ├── auth.py                  # JWTClaims, APIKeyConfig, Permission enum
│   ├── billing.py               # SubscriptionPlan, UsageRecord, InvoiceLine
│   ├── events.py                # DomainEvent base, TenantCreated, BillingEvent
│   └── validators.py            # Cross-field validators, tenant limit checks
├── shared_infra/
│   ├── __init__.py
│   ├── stripe_billing.py        # Create customer, subscribe, record usage, webhook handler
│   ├── auth_middleware.py       # FastAPI dependency: JWT validation, tenant extraction
│   ├── rate_limiter.py          # Token bucket per-tenant rate limiter (Redis-backed)
│   └── health.py                # Standard /health and /ready endpoint factory
├── ci_templates/
│   ├── python-test.yml          # GitHub Actions: pytest + coverage + ruff
│   ├── docker-build.yml         # Build, tag, push to GHCR
│   └── deploy-fly.yml           # Fly.io deploy with health check gate
├── tests/
│   ├── test_tenant.py
│   ├── test_auth.py
│   ├── test_billing.py
│   ├── test_stripe_billing.py
│   ├── test_auth_middleware.py
│   └── test_rate_limiter.py
├── pyproject.toml               # Hatch build system, version 0.1.0
└── README.md
```

### Files to Create (with descriptions)

| File | Lines (est.) | Description |
|------|-------------|-------------|
| `shared_schemas/tenant.py` | 80 | Pydantic models: `TenantConfig` (id, name, tier, limits, created_at), `TenantTier` enum (free/starter/pro/enterprise), `TenantLimits` (max_users, max_queries, storage_gb) |
| `shared_schemas/auth.py` | 60 | `JWTClaims` (sub, tenant_id, permissions, exp), `APIKeyConfig`, `Permission` enum (read/write/admin/billing) |
| `shared_schemas/billing.py` | 100 | `SubscriptionPlan` (stripe_price_id, tier, features), `UsageRecord` (tenant_id, metric, quantity, timestamp), `InvoiceLine` |
| `shared_schemas/events.py` | 50 | Base `DomainEvent` with id/timestamp/tenant_id, concrete events: `TenantCreated`, `SubscriptionChanged`, `UsageLimitReached` |
| `shared_infra/stripe_billing.py` | 150 | Async Stripe client wrapper: `create_customer()`, `create_subscription()`, `record_usage()`, `handle_webhook()`, idempotency keys |
| `shared_infra/auth_middleware.py` | 100 | FastAPI `Depends` callable: decode JWT, extract tenant, enforce permissions. Returns `AuthContext` |
| `shared_infra/rate_limiter.py` | 80 | Redis-backed token bucket: `check_rate_limit(tenant_id, endpoint)`, configurable per tier |
| `ci_templates/*.yml` | 50 each | Reusable GitHub Actions workflows with matrix testing (3.11, 3.12) |

### Test Targets

- **Test count**: 40+ tests
- **Coverage**: 95%+ (this is foundational -- no gaps allowed)
- **Performance**: All unit tests < 50ms each

### Milestones

| Week | Deliverable | Verification |
|------|------------|--------------|
| 1 | `shared_schemas/` complete: tenant, auth, billing, events models. All validators passing. | `pytest tests/ -v` -- 20+ tests green |
| 2 | `shared_infra/` complete: Stripe billing, auth middleware, rate limiter. CI templates. Published to PyPI (or local wheel). | Other repos can `pip install shared-schemas` and import all modules. Integration test with mock Stripe passes. |

### Definition of Done

- [ ] `pip install shared-schemas` works from PyPI or local wheel
- [ ] All 40+ tests passing with 95%+ coverage
- [ ] WS-2, WS-4, WS-5 agents confirm successful import
- [ ] CI templates used by at least one downstream repo
- [ ] README with usage examples for each module

---

## WS-2: Voice AI Platform

| Field | Value |
|-------|-------|
| **Agent** | `voice-ai-builder` |
| **Hours** | 160 |
| **Dependencies** | WS-1 (shared schemas, Stripe billing) |
| **Repo** | `voice-ai-platform/` |
| **Pricing** | $0.10-$0.20/min, deployed on Fly.io |

### Purpose

Build a production voice AI platform that wraps EnterpriseHub's Lead/Buyer/Seller bots behind phone calls. Twilio handles telephony, Deepgram does STT, ElevenLabs does TTS, and Pipecat orchestrates the real-time pipeline. Multi-tenant from Day 1, per-minute Stripe billing.

### Repository Structure

```
voice-ai-platform/
├── src/voice_ai/
│   ├── __init__.py
│   ├── config.py                    # Settings via pydantic-settings, env var loading
│   ├── main.py                      # FastAPI app factory, lifespan, middleware
│   ├── api/
│   │   ├── __init__.py
│   │   ├── calls.py                 # POST /calls/initiate, GET /calls/{id}, POST /calls/{id}/end
│   │   ├── agents.py                # CRUD for agent personas (voice, personality, bot type)
│   │   ├── transcripts.py           # GET /calls/{id}/transcript, search, export
│   │   ├── analytics.py             # GET /analytics/calls, /analytics/sentiment, /analytics/costs
│   │   ├── webhooks.py              # Twilio status callbacks, Stripe billing webhooks
│   │   └── tenants.py               # Tenant onboarding, config, limits
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── voice_pipeline.py        # Pipecat pipeline: STT -> LLM -> TTS orchestration
│   │   ├── stt_processor.py         # Deepgram streaming STT, interim results, endpointing
│   │   ├── tts_processor.py         # ElevenLabs streaming TTS, voice cloning config
│   │   ├── llm_processor.py         # Claude/GPT adapter, context windowing, token tracking
│   │   ├── leadbot_adapter.py       # Wraps LeadBotWorkflow for voice context
│   │   ├── buyerbot_adapter.py      # Wraps JorgeBuyerBot for voice context
│   │   ├── sellerbot_adapter.py     # Wraps JorgeSellerBot for voice context
│   │   └── handoff_manager.py       # Voice-to-voice bot handoff, warm transfer
│   ├── telephony/
│   │   ├── __init__.py
│   │   ├── twilio_handler.py        # TwiML generation, WebSocket media streams
│   │   ├── call_manager.py          # Call state machine: ringing -> active -> ended
│   │   └── recording.py             # Call recording, storage (S3/R2), retention policy
│   ├── models/
│   │   ├── __init__.py
│   │   ├── call.py                  # Call, CallStatus, CallParticipant SQLAlchemy models
│   │   ├── agent_persona.py         # AgentPersona: name, voice_id, bot_type, system_prompt
│   │   └── call_analytics.py        # CallMetrics, SentimentSnapshot, CostBreakdown
│   ├── services/
│   │   ├── __init__.py
│   │   ├── ghl_sync.py              # Sync call outcomes to GHL contacts/opportunities
│   │   ├── calendar_booking.py      # Voice-triggered calendar booking via GHL
│   │   ├── sentiment_tracker.py     # Real-time sentiment from transcript chunks
│   │   ├── pii_detector.py          # Redact SSN, CC numbers from transcripts
│   │   └── billing_service.py       # Per-minute usage tracking, Stripe metered billing
│   └── dashboard/
│       └── call_analytics_app.py    # Streamlit: call volume, avg duration, sentiment, costs
├── tests/
│   ├── unit/
│   │   ├── test_voice_pipeline.py
│   │   ├── test_stt_processor.py
│   │   ├── test_tts_processor.py
│   │   ├── test_llm_processor.py
│   │   ├── test_bot_adapters.py
│   │   ├── test_call_manager.py
│   │   ├── test_billing_service.py
│   │   ├── test_sentiment_tracker.py
│   │   └── test_pii_detector.py
│   ├── integration/
│   │   ├── test_twilio_webhooks.py
│   │   ├── test_ghl_sync.py
│   │   ├── test_full_call_flow.py
│   │   └── test_multi_tenant.py
│   └── load/
│       ├── test_concurrent_calls.py
│       └── test_pipeline_latency.py
├── alembic/
│   └── versions/                    # DB migrations
├── fly.toml                         # Fly.io config: 2 vCPU, 4GB RAM, auto-scale
├── Dockerfile                       # Multi-stage: builder + runtime
├── docker-compose.yml               # Local dev: app + postgres + redis
└── pyproject.toml                   # Dependencies: pipecat, deepgram-sdk, elevenlabs, twilio, stripe
```

### Test Targets

- **Test count**: 120+ tests (80 unit, 30 integration, 10 load)
- **Coverage**: 85%+
- **Performance**: Pipeline latency P95 < 800ms (STT + LLM + TTS)

### Week-by-Week Milestones

| Week | Deliverable | Key Files | Verification |
|------|------------|-----------|--------------|
| 1-2 | Pipecat pipeline scaffolding. STT (Deepgram streaming) and TTS (ElevenLabs) processors working in isolation. Basic FastAPI app with health check. | `voice_pipeline.py`, `stt_processor.py`, `tts_processor.py`, `main.py`, `config.py` | Audio-in -> text -> audio-out in pytest with mock audio. P95 < 500ms for STT alone. |
| 3-4 | Twilio integration. Inbound/outbound calls connect to pipeline. Bot adapters wrap Lead/Buyer/Seller bots. Call state machine complete. | `twilio_handler.py`, `call_manager.py`, `leadbot_adapter.py`, `buyerbot_adapter.py`, `sellerbot_adapter.py` | End-to-end call: Twilio -> STT -> LeadBot -> TTS -> Twilio. 20+ integration tests pass. |
| 5-6 | GHL sync (call outcomes pushed to CRM). Sentiment tracker (real-time). Call analytics models + API. Recording with PII redaction. | `ghl_sync.py`, `sentiment_tracker.py`, `call_analytics.py`, `pii_detector.py`, `recording.py` | GHL contact updated after call. Sentiment scores stored. PII redacted from transcripts. |
| 7-8 | Per-minute Stripe billing. Streamlit call analytics dashboard. Multi-tenant isolation (tenant-scoped calls, separate billing). | `billing_service.py`, `call_analytics_app.py`, `tenants.py` | Stripe usage records created per call. Dashboard shows call volume, costs, sentiment. Tenants isolated. |
| 9-10 | White-label features: custom voice personas, branded greetings, tenant-specific bot configs. Handoff manager for voice-to-voice bot transitions. | `agent_persona.py`, `handoff_manager.py` | Tenant A uses Voice X, Tenant B uses Voice Y. Warm handoff from LeadBot to BuyerBot mid-call. |
| 11-12 | Load testing (50 concurrent calls). Hardening: circuit breakers, graceful degradation, retry logic. Fly.io production deployment. | `test_concurrent_calls.py`, `test_pipeline_latency.py`, `fly.toml` | 50 concurrent calls with P95 < 800ms. Zero dropped calls under load. Fly.io deploy succeeds with health check. |

### Definition of Done

- [ ] 120+ tests passing, 85%+ coverage
- [ ] End-to-end call flow: dial in -> STT -> bot response -> TTS -> caller hears response
- [ ] Per-minute billing active on Stripe (test mode verified)
- [ ] GHL contact updated with call outcome, sentiment, transcript link
- [ ] Fly.io deployed, handling 50 concurrent calls at P95 < 800ms
- [ ] Streamlit dashboard live with call analytics
- [ ] Multi-tenant: 3 tenants operating independently

---

## WS-3: MCP Server Toolkit

| Field | Value |
|-------|-------|
| **Agent** | `mcp-builder` |
| **Hours** | 60 |
| **Dependencies** | None (fully independent) |
| **Repo** | `mcp-server-toolkit/` |
| **Pricing** | $49-$149/server, custom integrations $500+ |

### Purpose

Build a toolkit of production MCP servers that developers can install from PyPI. Includes an enhanced framework (auth, caching, rate limiting, telemetry) and 7 pre-built servers covering the most common AI-agent needs.

### Repository Structure

```
mcp-server-toolkit/
├── mcp_toolkit/
│   ├── __init__.py
│   ├── framework/
│   │   ├── __init__.py
│   │   ├── base_server.py           # MCPServer base class: tool registration, lifecycle hooks
│   │   ├── auth.py                  # API key + JWT auth for MCP connections
│   │   ├── caching.py              # Redis-backed response cache with TTL per tool
│   │   ├── rate_limiter.py         # Per-client token bucket rate limiter
│   │   ├── telemetry.py            # OpenTelemetry spans for every tool call
│   │   └── testing.py              # MCPTestClient: mock transport, assertion helpers
│   └── servers/
│       ├── __init__.py
│       ├── database_query/
│       │   ├── __init__.py
│       │   ├── server.py            # Natural language -> SQL (read-only by default)
│       │   ├── schema_introspector.py  # Auto-discover tables, columns, relationships
│       │   └── query_validator.py   # SQL injection prevention, query complexity limits
│       ├── web_scraping/
│       │   ├── __init__.py
│       │   ├── server.py            # URL -> structured data extraction
│       │   ├── extractors.py        # CSS selector, XPath, LLM-based extraction
│       │   └── rate_controller.py   # Polite crawling: robots.txt, delays, concurrency
│       ├── crm_ghl/
│       │   ├── __init__.py
│       │   ├── server.py            # GoHighLevel CRUD: contacts, opportunities, pipelines
│       │   └── field_mapper.py      # Map natural language fields to GHL custom fields
│       ├── file_processing/
│       │   ├── __init__.py
│       │   ├── server.py            # PDF/DOCX/CSV -> structured text + metadata
│       │   └── chunker.py           # Configurable chunking strategies for RAG
│       ├── email/
│       │   ├── __init__.py
│       │   ├── server.py            # Send/search/draft emails via SMTP/IMAP or API
│       │   └── template_engine.py   # Jinja2 email templates with variable injection
│       ├── calendar/
│       │   ├── __init__.py
│       │   ├── server.py            # Google Calendar / GHL calendar CRUD
│       │   └── availability.py      # Free slot finder, timezone handling
│       └── analytics/
│           ├── __init__.py
│           ├── server.py            # Query metrics, generate charts, anomaly detection
│           └── chart_generator.py   # Matplotlib/Plotly chart generation as base64
├── examples/
│   ├── quickstart.py               # 10-line example: start a server
│   ├── multi_server.py             # Run multiple servers behind one endpoint
│   └── custom_server.py            # Build your own server using the framework
├── tests/
│   ├── framework/
│   │   ├── test_base_server.py
│   │   ├── test_auth.py
│   │   ├── test_caching.py
│   │   ├── test_rate_limiter.py
│   │   └── test_telemetry.py
│   └── servers/
│       ├── test_database_query.py
│       ├── test_web_scraping.py
│       ├── test_crm_ghl.py
│       ├── test_file_processing.py
│       ├── test_email.py
│       ├── test_calendar.py
│       └── test_analytics.py
├── docs/
│   ├── getting-started.md
│   ├── framework-guide.md
│   └── server-reference.md
├── pyproject.toml                   # mcp-server-toolkit[all] or per-server extras
└── README.md
```

### Test Targets

- **Test count**: 80+ tests
- **Coverage**: 90%+
- **Performance**: Tool call response < 200ms (cached), < 2s (uncached DB/web)

### Week-by-Week Milestones

| Week | Deliverable | Key Files | Verification |
|------|------------|-----------|--------------|
| 1-3 | Framework complete (base server, auth, caching, rate limiter, telemetry, test client). First 3 servers: database_query, web_scraping, file_processing. | `framework/*.py`, `servers/database_query/`, `servers/web_scraping/`, `servers/file_processing/` | Framework: 25+ tests. Each server has 5+ tests. `MCPTestClient` can invoke tools and assert responses. |
| 4-6 | Remaining 4 servers: crm_ghl, email, calendar, analytics. All servers passing integration tests against real services (sandbox/test accounts). | `servers/crm_ghl/`, `servers/email/`, `servers/calendar/`, `servers/analytics/` | 80+ total tests. GHL sandbox CRUD works. Email sends to Mailtrap. Calendar creates/reads events. |
| 7-8 | PyPI publish (`pip install mcp-server-toolkit`). Gumroad product pages (individual servers + bundle). Documentation site. Examples directory. | `pyproject.toml`, `docs/`, `examples/` | `pip install mcp-server-toolkit[database]` works. Gumroad pages live. README has quickstart that works in < 5 minutes. |

### Definition of Done

- [ ] 80+ tests passing, 90%+ coverage
- [ ] Published on PyPI with per-server extras (`[database]`, `[web]`, `[crm]`, `[all]`)
- [ ] 7 servers functional with real-service integration tests
- [ ] Framework extensible: new server in < 100 lines of code
- [ ] Gumroad product pages live with pricing
- [ ] Documentation: getting started, framework guide, per-server reference

---

## WS-4: AI DevOps Suite

| Field | Value |
|-------|-------|
| **Agent** | `devops-suite-builder` |
| **Hours** | 55 |
| **Dependencies** | WS-1 (shared schemas, auth) |
| **Repo** | `ai-devops-suite/` |
| **Pricing** | $49-$199/mo subscription |
| **Origin** | Merged from: insight-engine, prompt-engineering-lab, scrape-and-serve |

### Purpose

Consolidate three micro-SaaS repos into one unified AI DevOps platform. Agent monitoring (from insight-engine), prompt registry with A/B testing (from prompt-engineering-lab), and web data pipelines (from scrape-and-serve). Single Streamlit dashboard, single Stripe subscription.

### Repository Structure

```
ai-devops-suite/
├── src/devops_suite/
│   ├── __init__.py
│   ├── config.py                    # Unified settings, feature flags per tier
│   ├── main.py                      # FastAPI app, mount all routers
│   ├── api/
│   │   ├── __init__.py
│   │   ├── events.py                # POST /events (agent telemetry ingestion)
│   │   ├── dashboards.py            # GET /dashboards, custom dashboard CRUD
│   │   ├── alerts.py                # CRUD alert rules, GET /alerts/history
│   │   ├── prompts.py               # CRUD prompt versions, GET /prompts/{id}/history
│   │   ├── experiments.py           # A/B test CRUD, GET /experiments/{id}/results
│   │   ├── jobs.py                  # Scraping job CRUD, GET /jobs/{id}/runs
│   │   ├── schedules.py             # Cron schedule CRUD for recurring jobs
│   │   └── extractions.py           # GET /extractions (scraped data query)
│   ├── monitoring/
│   │   ├── __init__.py
│   │   ├── metrics.py               # MetricsCollector: ingest, aggregate, query time-series
│   │   ├── anomaly.py               # Z-score + IQR anomaly detection on metrics
│   │   └── alerts.py                # AlertEngine: rule evaluation, notification dispatch
│   ├── prompt_registry/
│   │   ├── __init__.py
│   │   ├── versioning.py            # Prompt version control: create, diff, rollback
│   │   ├── ab_testing.py            # Experiment engine: variant assignment, significance calc
│   │   ├── safety.py                # Prompt injection detection, output validation
│   │   └── templates.py             # Jinja2 prompt templates with typed variables
│   ├── data_pipeline/
│   │   ├── __init__.py
│   │   ├── scraper.py               # Configurable web scraper: CSS/XPath/LLM extraction
│   │   ├── extractor.py             # Structured data extraction, schema validation
│   │   ├── scheduler.py             # APScheduler-based job scheduling
│   │   └── quality.py               # Data quality checks: completeness, freshness, accuracy
│   ├── models/
│   │   ├── __init__.py
│   │   ├── metrics.py               # Metric, MetricSeries, AnomalyEvent
│   │   ├── prompt.py                # PromptVersion, Experiment, Variant
│   │   └── pipeline.py              # ScrapingJob, Schedule, Extraction
│   ├── billing/
│   │   ├── __init__.py
│   │   └── subscription.py          # Tier enforcement (Starter: 1K events/day, Pro: 50K, Enterprise: unlimited)
│   └── dashboard/
│       └── unified_app.py           # Streamlit: 3-tab layout (Monitoring | Prompts | Data)
├── tests/
│   ├── test_metrics.py
│   ├── test_anomaly.py
│   ├── test_alerts.py
│   ├── test_versioning.py
│   ├── test_ab_testing.py
│   ├── test_safety.py
│   ├── test_scraper.py
│   ├── test_scheduler.py
│   ├── test_quality.py
│   └── test_subscription.py
├── Dockerfile
├── docker-compose.yml               # app + postgres + redis + scheduler
└── pyproject.toml
```

### Test Targets

- **Test count**: 70+ tests
- **Coverage**: 85%+
- **Performance**: Event ingestion < 10ms P95, dashboard load < 2s

### Week-by-Week Milestones

| Week | Deliverable | Key Files | Verification |
|------|------------|-----------|--------------|
| 1-2 | Unified repo scaffolding. FastAPI app with shared auth (from WS-1). Models for all three modules defined. | `main.py`, `config.py`, `models/*.py`, `api/*.py` (stubs) | App starts, auth middleware rejects unauthenticated requests, models create tables via Alembic. |
| 3-4 | Agent monitoring: metrics ingestion, time-series queries, anomaly detection, alerting rules. (Port from insight-engine.) | `monitoring/*.py`, `api/events.py`, `api/dashboards.py`, `api/alerts.py` | Ingest 10K events, query aggregates, anomaly flags on synthetic spikes. 20+ tests pass. |
| 5-6 | Prompt registry: version control, A/B testing engine, safety checks. (Port from prompt-engineering-lab.) | `prompt_registry/*.py`, `api/prompts.py`, `api/experiments.py` | Create prompt, make 3 versions, run A/B test with mock responses, statistical significance calculated. 15+ tests pass. |
| 7-8 | Web data pipeline: scraper, scheduler, quality checks. (Port from scrape-and-serve.) | `data_pipeline/*.py`, `api/jobs.py`, `api/schedules.py`, `api/extractions.py` | Scrape a test site, store structured data, schedule recurring job, quality check passes. 15+ tests pass. |
| 9-10 | Unified Streamlit dashboard (3 tabs). Stripe subscription billing with tier enforcement. Docker Compose production config. | `dashboard/unified_app.py`, `billing/subscription.py`, `Dockerfile`, `docker-compose.yml` | Dashboard renders all 3 tabs. Free tier limited to 1K events/day. Docker Compose starts all services. |

### Definition of Done

- [ ] 70+ tests passing, 85%+ coverage
- [ ] Three modules (monitoring, prompts, pipeline) accessible from single API
- [ ] Stripe subscription with 3 tiers enforced
- [ ] Unified Streamlit dashboard with live data
- [ ] Docker Compose one-command startup
- [ ] Original 3 repos archived with redirect to this repo

---

## WS-5: RAG-as-a-Service

| Field | Value |
|-------|-------|
| **Agent** | `rag-builder` |
| **Hours** | 80 |
| **Dependencies** | WS-1 (shared schemas, Stripe billing) |
| **Repo** | `rag-as-a-service/` |
| **Pricing** | $99-$999/mo + $0.005/query overage |

### Purpose

Productize EnterpriseHub's RAG system (from `advanced_rag_system/`) into a multi-tenant SaaS. Tenants upload documents, create collections, and query them via API. Usage-based billing, PII detection, audit logging. Web UI for non-technical users.

### Repository Structure

```
rag-as-a-service/
├── src/rag_service/
│   ├── __init__.py
│   ├── config.py                    # Settings: embedding model, chunk size, vector DB URL
│   ├── main.py                      # FastAPI app, lifespan (init vector DB, load models)
│   ├── api/
│   │   ├── __init__.py
│   │   ├── documents.py             # POST /documents/upload, GET /documents, DELETE
│   │   ├── queries.py               # POST /query (main RAG endpoint), GET /query/history
│   │   ├── collections.py           # CRUD collections (group of documents)
│   │   ├── tenants.py               # Tenant onboarding, config, usage stats
│   │   ├── auth.py                  # API key management, OAuth integration
│   │   ├── billing.py               # GET /billing/usage, GET /billing/invoices
│   │   └── teams.py                 # Team management: invite, roles, permissions
│   ├── core/
│   │   ├── __init__.py
│   │   ├── rag_engine.py            # Main RAG orchestrator: retrieve + rerank + generate
│   │   ├── document_processor.py    # PDF/DOCX/HTML -> chunks with metadata
│   │   ├── embedding_service.py     # OpenAI/Cohere/local embedding with batching
│   │   ├── retriever.py             # Hybrid retrieval: dense + sparse + metadata filters
│   │   └── query_expander.py        # HyDE, multi-query expansion, query decomposition
│   ├── multi_tenant/
│   │   ├── __init__.py
│   │   ├── tenant_router.py         # Route requests to tenant-specific vector namespaces
│   │   ├── schema_manager.py        # Per-tenant Postgres schemas, migration runner
│   │   └── isolation.py             # Enforce tenant boundaries: no cross-tenant data leaks
│   ├── models/
│   │   ├── __init__.py
│   │   ├── shared.py                # Document, Chunk, Query, QueryResult
│   │   └── tenant_models.py         # Tenant, TenantConfig, UsageQuota
│   ├── billing/
│   │   ├── __init__.py
│   │   ├── stripe_service.py        # Metered billing: $0.005/query after included quota
│   │   └── usage_tracker.py         # Count queries, storage, documents per tenant per day
│   ├── compliance/
│   │   ├── __init__.py
│   │   ├── pii_detector.py          # Detect/redact PII in uploaded documents and queries
│   │   └── audit_logger.py          # Immutable audit trail: who queried what, when, response
│   └── dashboard/
│       └── admin_app.py             # Streamlit admin: tenant overview, usage graphs, health
├── web_ui/
│   ├── package.json                 # React or Svelte project
│   ├── src/
│   │   ├── App.svelte               # Main app shell
│   │   ├── pages/
│   │   │   ├── Upload.svelte        # Document upload with drag-and-drop
│   │   │   ├── Query.svelte         # Chat-style query interface
│   │   │   ├── Collections.svelte   # Collection management
│   │   │   └── Settings.svelte      # API keys, billing, team management
│   │   └── lib/
│   │       └── api.ts               # Typed API client
│   └── vite.config.ts
├── tests/
│   ├── unit/
│   │   ├── test_rag_engine.py
│   │   ├── test_document_processor.py
│   │   ├── test_retriever.py
│   │   ├── test_query_expander.py
│   │   ├── test_pii_detector.py
│   │   ├── test_usage_tracker.py
│   │   └── test_tenant_isolation.py
│   ├── integration/
│   │   ├── test_upload_query_flow.py
│   │   ├── test_multi_tenant.py
│   │   ├── test_billing_flow.py
│   │   └── test_compliance.py
│   └── load/
│       ├── test_concurrent_queries.py
│       └── test_large_document_ingestion.py
├── Dockerfile
├── docker-compose.yml               # app + postgres + redis + qdrant/pgvector
└── pyproject.toml
```

### Test Targets

- **Test count**: 90+ tests
- **Coverage**: 85%+
- **Performance**: Query P95 < 3s (including LLM generation), document ingestion > 10 pages/sec

### Week-by-Week Milestones

| Week | Deliverable | Key Files | Verification |
|------|------------|-----------|--------------|
| 1-2 | Multi-tenant infrastructure: tenant router, schema manager, isolation layer. Postgres per-tenant schemas. FastAPI app with auth (from WS-1). | `multi_tenant/*.py`, `main.py`, `config.py`, `api/tenants.py`, `api/auth.py` | Create 3 tenants, verify schema isolation, confirm cross-tenant queries return empty. 15+ tests. |
| 3-4 | RAG engine: document processor, embedding service, retriever, query expander. Port core logic from `advanced_rag_system/`. | `core/*.py`, `api/documents.py`, `api/queries.py`, `api/collections.py` | Upload PDF, query it, get relevant answer. Hybrid retrieval outperforms dense-only on test set. 25+ tests. |
| 5-6 | API endpoints complete. Stripe usage billing ($0.005/query overage). Usage tracker with daily aggregation. | `api/*.py`, `billing/*.py` | Full CRUD on documents/collections. Stripe metered billing creates usage records. Dashboard shows usage. |
| 7-8 | PII detection (pre-ingestion scan + query-time redaction). Audit logger (immutable trail). Compliance API endpoints. | `compliance/*.py` | PII detected in test documents (SSN, email, phone). Audit log queryable. No PII in stored chunks. |
| 9-10 | Web UI: document upload, chat-style query, collection management, settings/billing page. | `web_ui/` | Svelte app connects to API. Upload -> query -> see results flow works end-to-end. |
| 11-12 | Load testing (100 concurrent queries, 1000-page document ingestion). Render/Fly.io deployment. Production hardening. | `tests/load/`, `Dockerfile`, `docker-compose.yml` | 100 concurrent queries at P95 < 3s. 1000-page PDF ingested in < 100s. Production deploy healthy. |

### Definition of Done

- [ ] 90+ tests passing, 85%+ coverage
- [ ] Multi-tenant: 5 tenants with complete data isolation verified
- [ ] Upload PDF -> query -> relevant answer in < 3s P95
- [ ] Stripe metered billing tracking queries per tenant
- [ ] PII detection blocks sensitive content from entering vector store
- [ ] Audit log records every query with tenant, timestamp, response hash
- [ ] Web UI functional for document upload and querying
- [ ] Deployed on Render/Fly.io, handling 100 concurrent queries

---

## WS-6: Course + GTM

| Field | Value |
|-------|-------|
| **Agent** | `course-gtm-lead` |
| **Hours** | 40+ ongoing |
| **Dependencies** | None (fully independent) |
| **Repo** | `course-infrastructure/` |
| **Pricing** | $797-$1,997/cohort, $397 self-paced |

### Purpose

Launch a cohort-based course teaching AI agent development using EnterpriseHub as the case study. Build all supporting infrastructure: Maven platform, Discord community, ConvertKit email sequences, GitHub Classroom labs, and go-to-market materials.

### Repository Structure

```
course-infrastructure/
├── platform/
│   ├── maven_setup.md               # Maven course config: modules, pricing, schedule
│   └── circle_migration.md          # Community migration plan if needed
├── community/
│   ├── discord_setup.py             # Bot for Discord server: roles, welcome, lab submissions
│   ├── bot_config.yaml              # Channel structure, auto-role rules, moderation
│   └── channel_structure.md         # Channel plan: general, labs, showcase, office-hours
├── marketing/
│   ├── convertkit_sequences/
│   │   ├── waitlist_welcome.md      # 5-email welcome sequence for waitlist signups
│   │   ├── pre_launch.md            # 7-email pre-launch countdown sequence
│   │   ├── cart_open.md             # 3-email cart open sequence with urgency
│   │   └── onboarding.md            # Post-purchase: access, Discord invite, Week 1 prep
│   ├── landing_page/
│   │   ├── index.html               # Course landing page (standalone, no framework)
│   │   └── styles.css
│   └── social_templates/
│       ├── twitter_threads.md       # 10 thread templates for launch campaign
│       ├── linkedin_posts.md        # 10 LinkedIn post templates
│       └── hn_show.md               # Show HN post draft
├── labs/
│   ├── week1_mcp_basics/            # Lab: Build your first MCP server
│   │   ├── README.md
│   │   ├── starter/                 # Student starter code
│   │   └── solution/               # Instructor solution
│   ├── week2_rag_pipeline/          # Lab: Document ingestion + retrieval
│   ├── week3_agent_orchestration/   # Lab: Multi-agent coordination
│   ├── week4_voice_ai/             # Lab: Voice pipeline with Pipecat
│   ├── week5_production/           # Lab: Deploy, monitor, scale
│   └── week6_capstone/             # Lab: Build your own AI product
├── certificates/
│   └── certifier_template.json     # Certificate template config
└── infrastructure/
    ├── github_classroom.md          # Classroom org setup, assignment configs
    └── codespace_config/
        ├── .devcontainer.json       # Codespace: Python 3.11, postgres, redis
        └── setup.sh                 # Post-create: install deps, seed data
```

### Test Targets

- **Test count**: 20+ (Discord bot tests, email template validation, lab starter tests)
- **Coverage**: N/A (mostly content + config)
- **Quality gate**: All 6 lab starters run without errors in Codespace

### Week-by-Week Milestones

| Week | Deliverable | Verification |
|------|------------|--------------|
| 1-2 | Maven course created (title, description, pricing, 6-week schedule). Discord server live (channels, roles, bot). ConvertKit waitlist form + welcome sequence active. | Maven URL accessible. Discord join link works. Waitlist signup triggers email sequence. |
| 3-4 | GitHub Classroom org configured. Week 1-3 lab environments (Codespace configs). Labs run in < 2 min setup time. | `devcontainer.json` builds, lab starters pass `pytest`, Classroom assignment auto-creates repos. |
| 5-6 | Pre-launch email sequence active. Landing page deployed. Week 4-6 labs complete. All social templates drafted. | Landing page live. Pre-launch emails sending. All 6 labs run successfully in Codespace. |
| 7-12 | Cohort 1 delivery. Weekly office hours. Content marketing (2 posts/week). Product Hunt + HN launch prep. Post-cohort: self-paced version conversion. | Cohort 1 enrolled (target: 15-25 students). Completion rate > 70%. NPS > 50. Self-paced version live by Week 12. |

### Definition of Done

- [ ] Maven course live with pricing and enrollment
- [ ] Discord community active with 50+ members
- [ ] ConvertKit sequences: waitlist, pre-launch, cart, onboarding
- [ ] 6 labs functional in GitHub Codespace
- [ ] Landing page converting at > 5% from social traffic
- [ ] Cohort 1 launched with 15+ students
- [ ] Self-paced version available by Week 12

---

## Cross-Workstream Integration Checkpoints

These are synchronization points where the coordinator (`portfolio-coordinator` agent) validates cross-workstream compatibility.

### Week 2 Checkpoint: Foundation Lock

| Check | Owner | Criteria |
|-------|-------|----------|
| `shared-schemas` published and importable | WS-1 | `pip install shared-schemas` succeeds. All models importable. |
| WS-2, WS-4, WS-5 scaffolded with shared-schemas dependency | WS-2/4/5 | `from shared_schemas import TenantConfig` works in each repo. |
| WS-3 framework functional | WS-3 | `MCPTestClient` can invoke a tool and get a response. |
| WS-6 waitlist live | WS-6 | ConvertKit form collecting signups. |

### Week 4 Checkpoint: Core Functionality

| Check | Owner | Criteria |
|-------|-------|----------|
| Voice pipeline end-to-end | WS-2 | Twilio call -> STT -> bot -> TTS -> response heard. |
| 3 MCP servers passing integration tests | WS-3 | database_query, web_scraping, file_processing all green. |
| Agent monitoring ingesting events | WS-4 | 10K events ingested, queried, anomaly detected. |
| RAG engine answering queries | WS-5 | Upload doc -> query -> relevant answer. |
| Labs 1-3 running in Codespace | WS-6 | Students can complete Week 1-3 labs. |

### Week 8 Checkpoint: Revenue Ready

| Check | Owner | Criteria |
|-------|-------|----------|
| Voice AI billing active | WS-2 | Per-minute Stripe charges on test calls. |
| MCP toolkit on PyPI | WS-3 | `pip install mcp-server-toolkit` works. Gumroad pages live. |
| DevOps Suite subscription billing | WS-4 | 3 tiers enforced, Stripe subscriptions active. |
| RAG billing active | WS-5 | Per-query overage charges on Stripe test mode. |
| Cohort 1 launched | WS-6 | 15+ students enrolled, Week 1 delivered. |
| Cross-product auth | ALL | Single API key works across Voice AI, DevOps, RAG (via shared auth middleware). |

### Week 12 Checkpoint: Production Maturity

| Check | Owner | Criteria |
|-------|-------|----------|
| Voice AI: 50 concurrent calls | WS-2 | Load test passes, Fly.io deployed. |
| MCP: 7 servers, all documented | WS-3 | PyPI downloads > 100, documentation complete. |
| DevOps: unified dashboard live | WS-4 | 3 modules in single Streamlit app. |
| RAG: multi-tenant production | WS-5 | 5 tenants, 100 concurrent queries, PII detection. |
| Course: Cohort 1 complete | WS-6 | > 70% completion, NPS > 50, self-paced version live. |
| Bundle pricing live | ALL | Cross-product discount: Voice + RAG + DevOps at 20% off. |

---

## Success Metrics

| Metric | WS-1 | WS-2 | WS-3 | WS-4 | WS-5 | WS-6 |
|--------|------|------|------|------|------|------|
| **Tests** | 40+ | 120+ | 80+ | 70+ | 90+ | 20+ |
| **Coverage** | 95% | 85% | 90% | 85% | 85% | N/A |
| **P95 Latency** | N/A | < 800ms | < 200ms (cached) | < 10ms (ingest) | < 3s (query) | N/A |
| **Uptime Target** | N/A | 99.5% | N/A (library) | 99.5% | 99.5% | N/A |
| **Time to First Deploy** | Week 2 | Week 8 | Week 7 (PyPI) | Week 10 | Week 10 | Week 2 (Maven) |

---

## Revenue Targets

| Workstream | Product | Week 4 | Week 8 | Week 12 |
|-----------|---------|--------|--------|---------|
| WS-2 | Voice AI Platform | $0 (building) | $500-$1K (beta users) | $3K-$5K/mo |
| WS-3 | MCP Server Toolkit | $0 (building) | $500-$1.5K (PyPI + Gumroad) | $2K-$4K/mo |
| WS-4 | AI DevOps Suite | $0 (building) | $0 (building) | $1K-$3K/mo |
| WS-5 | RAG-as-a-Service | $0 (building) | $0 (building) | $2K-$5K/mo |
| WS-6 | Cohort Course | $2K-$5K (pre-sales) | $8K-$15K (Cohort 1) | $12K-$20K (Cohort 1 + self-paced) |
| **TOTAL** | | **$2K-$5K** | **$9K-$17.5K** | **$20K-$37K/mo** |

### Revenue Acceleration Levers

1. **Course pre-sales (Week 2-4)**: Fastest path to revenue. Launch waitlist + pre-sale at $597 early bird. Target 10 pre-sales = $5,970.
2. **MCP servers on Gumroad (Week 7)**: Individual servers at $49-$149. Bundle at $299. Target 20 sales in first month.
3. **Voice AI beta program (Week 8)**: 5 beta customers at $99/mo + usage. Validate pricing before general launch.
4. **Cross-sell bundle (Week 12)**: Voice + RAG + DevOps at $399/mo (20% discount vs individual). Target 10 bundle subscribers.
5. **Enterprise consulting**: Every product generates consulting leads. Target 2 consulting engagements at $5K-$15K each by Week 12.

---

## Agent Coordination Protocol

### Communication

- **Daily**: Each agent posts progress to `#workstream-updates` (async, < 5 lines)
- **Weekly**: Portfolio coordinator reviews all workstreams, flags blockers
- **Blocking issues**: Immediately escalate to coordinator via `@portfolio-coordinator`

### Dependency Resolution

When a downstream agent (WS-2/4/5) is blocked on WS-1:
1. Work on non-dependent tasks (scaffolding, tests, documentation)
2. Use mock implementations of shared-schemas interfaces
3. Swap mocks for real imports once WS-1 publishes

### Quality Gates (All Workstreams)

Before any PR merges:
- [ ] All tests passing
- [ ] Coverage meets workstream target
- [ ] No secrets in code (`ruff` + pre-commit hook)
- [ ] Type checking passes (`pyright` basic mode)
- [ ] API endpoints documented (OpenAPI auto-generated)

### Handoff Protocol

When a workstream completes:
1. Agent writes `HANDOFF.md` in repo root (architecture decisions, known issues, operational runbook)
2. Portfolio coordinator reviews
3. Repo transferred to maintenance mode (bug fixes only, no new features until post-launch metrics collected)
