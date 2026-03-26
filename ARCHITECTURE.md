# EnterpriseHub — Architecture

## Repository Layout

EnterpriseHub is a monorepo containing the core real estate AI platform plus several embedded research/portfolio sub-projects. This document explains the structure and why each sub-project lives here.

---

## Core Platform

```
ghl_real_estate_ai/          # Main FastAPI application
├── agents/                  # Jorge bot personalities (Lead, Buyer, Seller)
├── api/                     # FastAPI routes, middleware, enterprise auth
├── models/                  # SQLAlchemy models + Pydantic schemas
├── services/                # Business logic, integrations, AI orchestration
│   ├── jorge/               # Handoff, A/B testing, alerting, calendar
│   ├── response_pipeline/   # 5-stage post-processing pipeline
│   └── circuit_breaker.py   # CLOSED/OPEN/HALF_OPEN failover
├── streamlit_demo/          # Internal BI dashboard (requires running services)
└── tests/unit/              # Isolated unit tests (181 pass in CI)

streamlit_cloud/             # Public demo (zero external deps, Streamlit Cloud)
tests/                       # Integration & system tests (require PostgreSQL + Redis)
```

## Embedded Sub-Projects

These sub-projects are co-located to share auth, models, and CI infrastructure. Each is independently deployable.

| Directory | Purpose | Status |
|-----------|---------|--------|
| `advanced_rag_system/` | Production RAG: pgvector, BM25+RRF hybrid retrieval, semantic cache | Active — 1,012 tests |
| `rag-as-a-service/` | Multi-tenant RAG API with usage metering and Stripe billing | Active — 214 tests |
| `agentforge/` | Agent dispatch framework: 4.3M dispatches/sec, circuit breakers | Research |
| `ai-devops-suite/` | AI-assisted CI/CD pipeline analysis and PR review tools | Research |
| `voice-ai-platform/` | WebSocket voice pipeline (STT → Claude → TTS) | Prototype |
| `api-docs/` | Auto-generated OpenAPI documentation portal | Tooling |
| `auto-claude/` | MCP server utilities for Claude Code integration | Tooling |

## Test Organization

| Location | Count | Run In | Requires |
|----------|-------|--------|----------|
| `ghl_real_estate_ai/tests/unit/` | 181 | CI (gated, 50% cov) | Nothing |
| `tests/unit/` | 700+ | CI (extended, no gate) | Nothing |
| `tests/integration/` | ~2,000 | Local / staging | PostgreSQL + Redis |
| `tests/performance/` | ~300 | Local / staging | Full stack |
| `advanced_rag_system/tests/` | 1,012 | Separate CI | Embeddings model |
| `rag-as-a-service/tests/` | 214 | Separate CI | Nothing |

## AI Orchestration Architecture

```
Request
  └─► ResponsePipeline (5 stages)
        1. LanguageMirrorProcessor  — detect language
        2. TCPAOptOutProcessor      — compliance gate
        3. ComplianceCheckProcessor — FHA/RESPA enforcement
        4. AIDisclosureProcessor    — SB 243 footer
        5. SMSTruncationProcessor   — 320-char limit

  └─► LLMClient
        └─► CircuitBreaker (CLOSED/OPEN/HALF_OPEN)
              ├─ Primary:    Claude claude-sonnet-4-6
              ├─ Fallback 1: Gemini 1.5 Pro
              └─ Fallback 2: OpenRouter / GPT-4o

  └─► 3-Tier Cache
        ├─ L1: In-memory LRU  (60s TTL,  59.1% hit rate)
        ├─ L2: Redis          (300s TTL, 20.5% hit rate)
        └─ L3: PostgreSQL     (3600s TTL, 8.5% hit rate)
        → Total: 88.1% cache hit, 89% cost reduction
```

## Key Design Decisions

**Why a monorepo?** The `advanced_rag_system` and `rag-as-a-service` sub-projects share the same Pydantic models, auth middleware, and CI pipeline as the core platform. Extracting them would require duplicating ~2,000 lines of shared infrastructure.

**Why 6,497 test functions but only 1,100+ in CI?** Integration tests (the majority) require a running PostgreSQL database and Redis instance. CI now runs 1,100+ unit + agent tests that can execute with zero external dependencies. The 50% coverage gate on unit tests ensures the core business logic is covered; full integration suites run in staging.

**Why GoHighLevel?** GHL is the dominant CRM in the US real estate market. The `enhanced_ghl_client.py` provides rate-limited, retry-safe access to GHL's REST API with real-time webhook processing.
