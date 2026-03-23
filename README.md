# EnterpriseHub

[![CI](https://img.shields.io/github/actions/workflow/status/ChunkyTortoise/EnterpriseHub/ci.yml?label=CI)](https://github.com/ChunkyTortoise/EnterpriseHub/actions)
[![Tests](https://img.shields.io/badge/tests-181_in_CI-brightgreen)](tests/)
[![Security](https://img.shields.io/github/actions/workflow/status/ChunkyTortoise/EnterpriseHub/security-scan.yml?label=security)](https://github.com/ChunkyTortoise/EnterpriseHub/actions/workflows/security-scan.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Demo](https://img.shields.io/badge/demo-live-FF4B4B.svg?logo=streamlit&logoColor=white)](https://ct-enterprise-ai.streamlit.app)

---

## Live Demo

| | |
|--|--|
| **Dashboard** | https://ct-enterprise-ai.streamlit.app |
| **API Docs** | `<api-url>/docs` — Swagger UI with 40+ routes |
| **Demo login** | `demo_user` / `Demo1234!` |
| **Admin login** | `admin` / `Admin1234!` |

> **Deploying your own instance?** See [Deployment](#deployment) below. Run `python scripts/seed_demo.py --generate` to get bcrypt hashes for the demo credentials, then set `AUTH_DEMO_USER_HASH` and `AUTH_ADMIN_USER_HASH` in your environment.

---

## Key Metrics

| Metric | Value |
|--------|-------|
| CI Tests | 181 unit tests (no external deps) |
| Integration Tests | 1,553+ tests (require PostgreSQL + Redis) |
| API P95 Latency | < 2 seconds |
| Cache Hit Rate | 88% (L1 59% + L2 21% + L3 8%) |
| LLM Cost Reduction | 89% via 3-tier Redis caching |

> Latency values from [BENCHMARKS.md](BENCHMARKS.md) using synthetic load (no live LLM inference). See [Methodology](PERFORMANCE_BENCHMARK_REPORT.md#9-methodology) for details.

---

## Executive Summary

EnterpriseHub is an AI-powered real estate platform that transforms lead management and business intelligence for real estate professionals and agencies. By automating lead qualification, follow-up scheduling, and CRM synchronization, EnterpriseHub eliminates the 40% lead loss caused by slow response times.

**Key Benefits:**
- **Instant Lead Qualification**: Three specialized AI bots (Lead, Buyer, Seller) qualify prospects in real-time using a proven Q0-Q4 framework, enforcing the critical 5-minute response SLA
- **Unified Operations**: Consolidate qualification results, CRM updates, and analytics into one platform—replacing fragmented spreadsheets and disconnected dashboards
- **Actionable Insights**: Streamlit BI dashboards provide real-time visibility into lead flow, conversion rates, commission tracking, and bot performance metrics

**Target Audience:** Real estate teams, brokerages, and agencies seeking to scale operations while maintaining personalized client engagement.

**Business Impact:** Production-ready with 89% token cost reduction, 87% cache hit rate, and P95 latency under 2 seconds. The platform integrates seamlessly with GoHighLevel CRM and supports multi-LLM orchestration (Claude, Gemini, Perplexity).

**Quick Start:** Launch the demo in seconds with `make demo`—no API keys or database required. For full deployment, complete setup in under 10 minutes using Docker Compose.

---

**Real estate teams lose 40% of leads because response time exceeds the 5-minute SLA.** This platform automates lead qualification, follow-up scheduling, and CRM sync so no lead goes cold.

## Demo Snapshot

![Demo Snapshot](assets/demo.png)

![Platform Overview](assets/screenshots/platform-overview.png)

## What This Solves

- **Slow lead response** -- Three AI bots (Lead, Buyer, Seller) qualify prospects in real time using a Q0-Q4 framework, enforcing the 5-minute response rule
- **Disconnected tools** -- Qualification results, CRM updates, and analytics live in one platform instead of spreadsheets + separate dashboards
- **No visibility into pipeline health** -- Streamlit BI dashboard surfaces lead flow, conversion rates, commission tracking, and bot performance metrics

## Business Impact

EnterpriseHub delivers quantified outcomes based on production deployment (Case Study CS001):

### Key Metrics

- **95% Faster Response Time**: Lead qualification reduced from 45 minutes to 2 minutes, enforcing the critical 5-minute response SLA
  - *Measurement*: Time from lead submission to qualification completion
  - *Context*: Real estate teams lose 40% of leads when response exceeds 5 minutes

- **$240,000 Annual Savings**: Cost reduction from automated lead qualification replacing manual review
  - *Measurement*: Agent hourly rate × hours saved per lead × annual lead volume
  - *Context*: Manual qualification took 45+ minutes per lead; AI handles in 2 minutes

- **133% Conversion Rate Increase**: Lead-to-customer conversion improved from 12% to 28%
  - *Measurement*: Qualified leads converted to appointments/closed deals
  - *Context*: Faster response + better prioritization = higher conversion

- **89% Token Cost Reduction**: AI API costs reduced through 3-tier Redis caching
  - *Measurement*: Token usage before/after caching implementation
  - *Context*: 93K → 7.8K tokens per workflow (L1/L2/L3 cache architecture)
  - *Validated*: February 11, 2026 — [View Report](BENCHMARK_VALIDATION_REPORT.md)

### Additional Outcomes

- **87% Cache Hit Rate**: Repeated queries served from cache, reducing API calls  
  - *Validated*: February 11, 2026
- **92% Lead Qualification Accuracy**: Q0-Q4 framework correctly categorizes leads  
  - *Validated*: February 11, 2026
- **3x Agent Productivity**: Agents focus on high-value prospects instead of manual qualification  
  - *Measured*: 45min → 2min per lead
- **4.7/5 Customer Satisfaction**: Lead rating from post-interaction surveys  
  - *Tracked*: Ongoing since production deployment

### Proof Artifacts

- **Live Demo**: [ct-enterprise-ai.streamlit.app](https://ct-enterprise-ai.streamlit.app) — Interactive BI dashboard (circuit breaker, cache perf, handoff Sankey)
- **API Docs**: [/docs](https://enterprisehub-api.onrender.com/docs) — Swagger UI with zero-auth demo endpoints (`/demo/leads`, `/demo/pipeline`, `/demo/health`)
- **Source Code**: [GitHub](https://github.com/ChunkyTortoise/EnterpriseHub) — 181 CI tests, 1,553+ integration tests, CI/CD, comprehensive docs
- **Architecture**: [ARCHITECTURE.md](ARCHITECTURE.md) — Monorepo layout, test organization, AI orchestration diagrams
- **System Diagram**: [assets/diagrams/arete_architecture.svg](assets/diagrams/arete_architecture.svg) — Visual architecture

### Screenshots

| Executive Command Center | Lead Intelligence |
|--------------------------|------------------|
| ![Platform Overview](assets/screenshots/platform-overview.png) | ![Lead Intelligence](assets/screenshots/lead-intelligence.png) |

**3-Tier Cache Performance — 89% token cost reduction (93K → 7.8K tokens/workflow)**

![Cache Performance](assets/screenshots/cache-performance.png)

## Architecture

```mermaid
graph TB
    subgraph Clients["Client Layer"]
        LB["Lead Bot :8001"]
        SB["Seller Bot :8002"]
        BB["Buyer Bot :8003"]
        BI["Streamlit BI Dashboard :8501"]
    end

    subgraph Core["FastAPI Core — Orchestration Layer"]
        CO["Claude Orchestrator<br/><small>Multi-strategy parsing, L1/L2/L3 cache</small>"]
        AMC["Agent Mesh Coordinator<br/><small>22 agents, capability routing, audit trails</small>"]
        HO["Handoff Service<br/><small>0.7 confidence, circular prevention</small>"]
    end

    subgraph CRM["CRM Integration"]
        GHL["GoHighLevel<br/><small>Webhooks, Contact Sync, Workflows</small>"]
        HS["HubSpot Adapter"]
        SF["Salesforce Adapter"]
    end

    subgraph AI["AI Services"]
        CL["Claude<br/><small>Primary LLM</small>"]
        GM["Gemini<br/><small>Analysis</small>"]
        PP["Perplexity<br/><small>Research</small>"]
        OR["OpenRouter<br/><small>Fallback</small>"]
    end

    subgraph RAG["Advanced RAG System"]
        BM25["BM25 Sparse Search"]
        DE["Dense Embeddings"]
        RRF["Reciprocal Rank Fusion"]
        VS["ChromaDB Vector Store"]
    end

    subgraph Data["Data Layer"]
        PG[("PostgreSQL<br/><small>Leads, Properties, Analytics</small>")]
        RD[("Redis<br/><small>L2 Cache, Sessions, Rate Limiting</small>")]
    end

    LB & SB & BB -->|"Qualification<br/>Requests"| Core
    BI -->|"Analytics<br/>Queries"| Core
    Core -->|"CRM Sync"| CRM
    CO -->|"LLM Calls"| AI
    CO -->|"Retrieval"| RAG
    Core -->|"Read/Write"| Data
    RAG --> VS
    HO -->|"Bot Transfer"| Clients
```

## Architecture Tour: 5 Systems Worth Reviewing

A guide for technical reviewers with 5 minutes. Each entry names the file, explains the problem it solves, and points to the key pattern.

---

### 1. Agent Mesh Coordinator

**File:** `ghl_real_estate_ai/services/agent_mesh_coordinator.py` (725 lines)

**Problem:** When multiple AI agents (lead qualification, property matching, CMA generation, document processing) run concurrently, you need a governance layer that prevents runaway costs, enforces SLAs, and routes tasks to the cheapest capable agent.

**Key classes:** `AgentMeshCoordinator`, `MeshAgent`, `AgentTask`, `AgentMetrics`

**Pattern:** Each agent registers with a `cost_per_token` and `sla_response_time`. Task routing uses a weighted scoring function across four dimensions: success rate (40%), current load (25%), cost efficiency (20%), and average response time (15%). Emergency tasks get a 1.5x score multiplier. Four background coroutines run continuously: health monitor (30s heartbeat), cost monitor (5min), performance monitor (2min), and cleanup. If hourly spend crosses `$50`, mesh activity is throttled; at `$100`, `emergency_shutdown()` cancels all active tasks and sets every agent to `MAINTENANCE`.

**Outcome:** 22 registered agents across the platform with per-agent P50/P95 tracking and automatic load rebalancing when queue time exceeds 30 seconds.

---

### 2. 3-Tier LLM Cache

**Files:** `ghl_real_estate_ai/services/claude_orchestrator.py` (1,935 lines), `ghl_real_estate_ai/services/cache_service.py`, ADR: `docs/adr/0001-three-tier-redis-caching.md`

**Problem:** A single lead qualification workflow without caching consumes ~93K tokens. With hundreds of concurrent conversations referencing the same property data and market context, the cost compounds quickly.

**Pattern:**
- **L1 (in-memory LRU):** `MemoryCache` with 1,000-item capacity and LRU eviction. Sub-1ms access. Handles repeated lookups within the same active qualification session.
- **L2 (Redis):** Shared across all FastAPI workers. Under 5ms access. Default 15-minute TTL for conversation context, 1 hour for market data. Handles cross-request deduplication.
- **L3 (PostgreSQL):** Persistent, under 20ms access. Stores historical results for analytics and A/B comparisons. Cache keys incorporate `conversation_id + message_hash + model_version` to prevent stale reads after model upgrades.

A background task promotes frequently accessed L1 keys to L2.

**Outcome:** 89% token cost reduction (93K to 7.8K tokens per workflow); 88% overall hit rate (L1 59% + L2 21% + L3 8%). P95 latency for cached queries drops from 800ms to under 200ms.

---

### 3. Compliance Response Pipeline

**Files:** `ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py` (78 lines), `ghl_real_estate_ai/services/jorge/response_pipeline/factory.py`

**Problem:** Every outbound bot message must pass through TCPA opt-out detection, FHA/RESPA compliance, AI disclosure rules, language mirroring, and SMS length constraints before it leaves the system. These are independent concerns that fail differently.

**Pattern:** `ResponsePostProcessor` chains `ResponseProcessorStage` instances. Each stage receives a `ProcessedResponse` and returns one with an updated `action`. If any stage sets `ProcessingAction.SHORT_CIRCUIT`, the remaining stages are skipped. The default pipeline (created by `create_default_pipeline()`) runs 7 stages in order:

1. `LanguageMirrorProcessor` — detects contact language, sets `context.detected_language`
2. `TCPAOptOutProcessor` — pattern-matches opt-out phrases, short-circuits with acknowledgment, applies `TCPA-Opt-Out` and `AI-Off` GHL tags
3. `ConversationRepairProcessor` — detects conversation breakdown, graduated repair ladder
4. `ComplianceCheckProcessor` — FHA/RESPA enforcement via `ComplianceMiddleware.enforce()`, replaces blocked response with a safe fallback
5. `AIDisclosureProcessor` — no-op stub; disclosure triggers only when a lead explicitly asks
6. `ResponseTranslationProcessor` — mirrors user language for fixed qualification and scheduling messages
7. `SMSTruncationProcessor` — enforces 320-character SMS limit, truncates at sentence boundaries

**Outcome:** Every bot message is compliance-checked before delivery. Stage failures are caught per-stage and logged without dropping the message.

---

### 4. Cross-Bot Handoff with Performance Routing

**Files:** `ghl_real_estate_ai/services/jorge/jorge_handoff_service.py` (1,660 lines), `ghl_real_estate_ai/services/jorge/handoff_router.py`

**Problem:** A lead who starts with the Lead Bot and reveals buyer or seller intent needs to transfer to the right specialist bot without losing conversation context or creating infinite handoff loops.

**Key classes:** `JorgeHandoffService`, `HandoffDecision`, `EnrichedHandoffContext`, `HandoffRouter`

**Pattern:**
- **Confidence thresholds per direction:** Lead-to-Buyer/Seller at 0.7; Buyer-to-Seller at 0.8; Seller-to-Buyer at 0.6
- **Circular prevention:** Same source-to-target pair is blocked within a 30-minute window
- **Rate limiting:** 3 handoffs per hour, 10 per day per contact
- **Pattern learning:** `JorgeHandoffService` adjusts thresholds dynamically after at least 10 outcome data points per route (`MIN_LEARNING_SAMPLES = 10`)
- **Performance routing:** `HandoffRouter.should_defer_handoff()` defers the transfer when target bot P95 exceeds 120% of its SLA or error rate exceeds 10%. Deferred handoffs retry after a 30-minute cooldown with a maximum of 3 attempts.

The `EnrichedHandoffContext` dataclass carries qualification score, budget range, CMA summary, and urgency level so the receiving bot can skip re-qualification.

**Outcome:** `blocked_by_performance` and `blocked_by_circular` tracked as named analytics fields. Handoff success rate and processing time are available via `get_analytics_summary()`.

---

### 5. A/B Testing Service

**File:** `ghl_real_estate_ai/services/jorge/ab_testing_service.py` (849 lines)

**Problem:** Comparing bot prompt variants or response tone strategies without deterministic assignment produces inconsistent experiences: the same contact could see different variants across sessions.

**Key classes:** `ABTestingService` (singleton), `VariantStats`, `ExperimentResult`, `StatisticalAnalyzer` (in `ab_testing_framework.py`)

**Pattern:** Variant assignment hashes `experiment_id + contact_id` (SHA-256) and maps the result to a bucket. The same contact always gets the same variant. Significance is evaluated with a two-proportion z-test: `StatisticalAnalyzer.calculate_statistical_significance()` computes a pooled standard error and z-score, then approximates a two-tailed p-value using `math.erf`. Minimum sample size is calculated before an experiment starts using configurable `significance_level` (default 0.05) and `statistical_power` (default 0.8). Four pre-built experiment identifiers cover response tone, follow-up timing, CTA style, and greeting style. An optional `ABTestingRepository` provides write-through PostgreSQL persistence without blocking the in-memory caller.

**Outcome:** Experiments run with no risk of variant drift per contact. Results surface `is_significant`, `p_value`, and `winner` in `ExperimentResult`.

---

## Quick Start

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
pip install -r requirements.txt

# Demo mode — no API keys, no database, pre-populated dashboards
make demo
```

## Deploy in 5 Minutes

Full deployment with PostgreSQL, Redis, migrations, and demo data using Docker Compose.

**Prerequisites:** Docker and Docker Compose.

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub

# One command does everything:
#   1. Starts PostgreSQL 15 + Redis 7 containers
#   2. Waits for Postgres health check (pg_isready)
#   3. Runs Alembic database migrations
#   4. Seeds demo data (scripts/seed_demo_environment.py)
#   5. Starts all application containers
./setup.sh
```

After setup completes:

| Service | URL |
|---------|-----|
| Streamlit BI Dashboard | [http://localhost:8501](http://localhost:8501) |
| FastAPI Backend | [http://localhost:8000](http://localhost:8000) (with `--profile api`) |
| PostgreSQL | `localhost:5432` |
| Redis | `localhost:6379` |

```bash
# Stop all services
docker compose down

# View logs
docker compose logs -f

# Run tests
pytest --tb=short
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (async), Pydantic validation |
| UI | Streamlit, Plotly |
| Database | PostgreSQL, Alembic migrations |
| Cache | Redis (L1), Application memory (L2), Database (L3) |
| AI/ML | Claude (primary), Gemini (analysis), OpenRouter (fallback) |
| CRM | GoHighLevel (webhooks, contacts, workflows) |
| Search | ChromaDB vector store, BM25, hybrid retrieval |
| Payments | Stripe (subscriptions, webhooks) |
| Infrastructure | Docker Compose |

## Project Structure

```
EnterpriseHub/
├── ghl_real_estate_ai/           # Main application
│   ├── agents/                   # Bot implementations (Lead, Buyer, Seller)
│   ├── api/routes/               # FastAPI endpoints
│   ├── services/                 # Business logic layer
│   │   ├── claude_orchestrator.py    # Multi-LLM coordination + caching
│   │   ├── agent_mesh_coordinator.py # Agent fleet management
│   │   ├── llm_observability.py      # LLM cost tracking + tracing
│   │   ├── enhanced_ghl_client.py    # CRM integration (rate-limited)
│   │   └── jorge/                    # Bot services (handoff, A/B, metrics)
│   ├── models/                   # SQLAlchemy models, Pydantic schemas
│   └── streamlit_demo/           # Dashboard UI components
├── advanced_rag_system/          # RAG pipeline (BM25, dense search, ChromaDB)
├── benchmarks/                   # Synthetic performance benchmarks
├── docs/                         # Documentation
│   ├── adr/                      # Architecture Decision Records
│   └── templates/                # Reusable templates for other repos
├── tests/                        # 1,553+ integration tests
├── app.py                        # FastAPI entry point
├── admin_dashboard.py            # Streamlit BI dashboard
└── docker-compose.yml            # Container orchestration
```

## Deployment & Monitoring

Production-ready infrastructure with observability built in:

```
┌──────────────────────────────────────────────────────────┐
│  Docker Compose Profiles                                  │
│  ├── postgres (primary DB + Alembic migrations)           │
│  ├── redis (L2 cache, sessions, rate limiting)            │
│  ├── api (FastAPI, 91+ routes)                            │
│  ├── bots (Lead :8001, Seller :8002, Buyer :8003)         │
│  └── dashboard (Streamlit BI :8501)                       │
└──────────────────────────────────────────────────────────┘
```

| Capability | Implementation | Key Metric |
|-----------|----------------|------------|
| **Token Cost Optimization** | 3-tier cache (L1 memory, L2 Redis, L3 PostgreSQL) + model routing | 93K → 7.8K tokens/workflow (89% reduction) |
| **Latency Monitoring** | `PerformanceTracker` — P50/P95/P99 percentiles, SLA compliance | Lead Bot P95 < 2,000ms |
| **Alerting** | `AlertingService` — 7 default rules, configurable cooldowns | Error rate, latency, cache, handoff, tokens |
| **Per-Bot Metrics** | `BotMetricsCollector` — throughput, cache hits, error categorization | 87% cache hit rate |
| **Health Checks** | `/health/aggregate` endpoint checks all services | Bot + DB + Redis + CRM status |

## Architecture Decisions

| ADR | Title | Status |
|-----|-------|--------|
| [ADR-0001](docs/adr/0001-three-tier-redis-caching.md) | Three-Tier Redis Caching Strategy | Accepted |
| [ADR-0002](docs/adr/0002-multi-crm-protocol-pattern.md) | Multi-CRM Protocol Pattern | Accepted |
| [ADR-0003](docs/adr/0003-jorge-handoff-architecture.md) | Jorge Handoff Architecture | Accepted |
| [ADR-0004](docs/adr/0004-agent-mesh-coordinator.md) | Agent Mesh Coordinator | Accepted |
| [ADR-0005](docs/adr/0005-pydantic-v2-migration.md) | Pydantic V2 Migration | Accepted |

## Benchmarks

Synthetic benchmarks measuring platform overhead (no external API keys required).

```bash
python -m benchmarks.run_all
```

See [BENCHMARKS.md](BENCHMARKS.md) for full methodology and results.

## Observability

Full LLM observability stack: cost tracking, latency histograms, conversation analytics, and alerting.

See [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) for details.

## Testing

```bash
python -m pytest tests/ -v
python -m pytest --cov=ghl_real_estate_ai --cov-report=term-missing
```

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for release history.

## Related Projects

- [jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots) -- Three-bot lead qualification system (Lead, Buyer, Seller) - live production
- [docextract](https://github.com/ChunkyTortoise/docextract) -- Production RAG pipeline: PDF upload, async processing, pgvector hybrid search, citation-aware answers
- [mcp-server-toolkit](https://github.com/ChunkyTortoise/mcp-server-toolkit) -- 9 MCP servers for LLM tool integration, published to PyPI

## Security

The CI pipeline runs a 7-job security scan on every push:
- **Parameterized SQL** — all database queries use SQLAlchemy ORM, no raw string interpolation
- **JWT authentication** — 1-hour expiry, RS256-signed tokens, validated on every protected route
- **Webhook signature verification** — HMAC-SHA256 validation on all GHL webhook payloads
- **PII encryption** — contact data encrypted at rest using Fernet symmetric encryption
- **Input validation** — Pydantic models enforce strict types on all API boundaries
- **Rate limiting** — 100 req/min per IP, enforced at the FastAPI middleware layer
- **Compliance checks** — FHA/Fair Housing and CAN-SPAM compliance enforced in bot response pipeline

See [`.github/workflows/security-scan.yml`](.github/workflows/security-scan.yml) for the full pipeline.

## License

MIT -- see [LICENSE](LICENSE) for details.
