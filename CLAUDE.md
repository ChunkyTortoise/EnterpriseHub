# EnterpriseHub: Real Estate AI & BI Platform

**Domain**: Rancho Cucamonga real estate market with AI-powered lead qualification, chatbot orchestration, and BI dashboards.

**References**: `.claude/reference/domain-context.md` (market, terminology, bots) | `.claude/reference/quality-standards.md` (perf targets, testing, KPIs)

---

## Architecture

**Stack**: FastAPI (async) | Streamlit BI | PostgreSQL + Alembic | Redis cache (L1/L2/L3) | Claude + Gemini + Perplexity AI | GoHighLevel CRM | Stripe | Docker Compose

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Jorge Bots    │    │  BI Dashboard    │    │  GHL Integration│
│ (Lead/Buyer/    │◄──►│  (Streamlit)     │◄──►│  (CRM Sync)     │
│  Seller)        │    │                  │    │                 │
└────────┬────────┘    └────────┬─────────┘    └────────┬────────┘
         └──────────────────────┼───────────────────────┘
                    ┌───────────▼──────────┐
                    │    FastAPI Core      │
                    │  (Orchestration)     │
                    └───────────┬──────────┘
                    ┌───────────▼──────────┐
                    │   PostgreSQL + Redis │
                    └──────────────────────┘
```

## Code Organization
```
advanced_rag_system/src/       # RAG: core/, embeddings/, vector_store/
ghl_real_estate_ai/            # Main app
├── agents/                    # Bot personalities and behaviors
├── api/                       # FastAPI routes and middleware
├── models/                    # SQLAlchemy models, Pydantic schemas
├── services/                  # Business logic, integrations
├── utils/                     # Shared utilities
└── streamlit_demo/            # BI dashboard components
```

## Conventions
- **Files/Functions**: `snake_case` | **Classes**: `PascalCase` | **Constants**: `SCREAMING_SNAKE_CASE`
- **Env vars**: `PROJECT_FEATURE_NAME` | **DB tables**: `plural_snake_case`
- **Errors**: Explicit exception types, structured JSON responses (`error`, `message`, `field`, `code`)

## Agent & MCP Landscape

### Claude Code Agents (17)
All agents are **domain-agnostic** -- they adapt to this project's domain via CLAUDE.md and reference files.

| Agent | Purpose |
|-------|---------|
| architecture-sentinel | Deep architectural analysis and design guidance |
| security-auditor | Vulnerability research and security compliance |
| performance-optimizer | Performance profiling and scalability tuning |
| integration-test-workflow | Multi-agent coordination and integration testing |
| compliance-risk | Regulatory compliance monitoring and risk assessment |
| intent-decoder | Multi-modal conversation intelligence and intent analysis |
| handoff-orchestrator | Agent-to-agent transitions and context preservation |
| conversation-design | Conversational AI architecture and dialogue quality |
| database-migration | Schema design, migrations, and data infrastructure |
| ml-pipeline | ML model quality, training pipelines, and optimization |
| predictive-analytics | Forecasting, conversion optimization, and trend analysis |
| rag-pipeline-optimizer | RAG systems engineering and information retrieval |
| api-consistency | REST API design, standardization, and governance |
| devops-infrastructure | CI/CD pipelines, containers, and deployment automation |
| cost-token-optimization | AI cost engineering and token efficiency |
| dashboard-design | Streamlit BI dashboard architecture and visualization |
| kpi-definition | Business intelligence KPI frameworks and metrics |

### MCP Servers (5)
| Server | Package | Purpose |
|--------|---------|---------|
| memory | `@modelcontextprotocol/server-memory` | Knowledge graph persistence |
| postgres | `@modelcontextprotocol/server-postgres` | Direct DB queries via `${DATABASE_URL}` |
| redis | `@gongrzhe/server-redis-mcp` | Cache inspection via `${REDIS_URL}` |
| stripe | `@stripe/mcp` | Billing management via `${STRIPE_SECRET_KEY}` |
| playwright | `@playwright/mcp` | E2E browser testing |

## Critical Services
| Service | File | Key Behavior |
|---------|------|-------------|
| Claude Orchestration | `services/claude_orchestrator.py` | Multi-strategy parsing, L1/L2/L3 cache, <200ms overhead |
| Agent Mesh | `services/agent_mesh_coordinator.py` | Governance, routing, auto-scaling, audit trails |
| GHL Client | `services/enhanced_ghl_client.py` | 10 req/s rate limit, real-time CRM sync |
| BI Dashboards | `streamlit_demo/components/` | Monte Carlo, sentiment, churn detection |

## Security Essentials
- **PII**: Encrypted at rest (Fernet) | **API Keys**: Env vars only, never hardcoded
- **Auth**: JWT (1hr), 100 req/min rate limit | **Validation**: Pydantic on all inputs
- **Compliance**: DRE, Fair Housing, CCPA, CAN-SPAM

## Critical Files
| File | Purpose | Priority |
|------|---------|----------|
| `app.py` | FastAPI entry point | HIGH |
| `services/claude_orchestrator.py` | AI coordination | HIGH |
| `agents/jorge_*_bot.py` | Bot implementations | HIGH |
| `services/enhanced_ghl_client.py` | CRM integration | MEDIUM |
| `models/` | Data models | MEDIUM |
| `streamlit_demo/` | BI dashboard | MEDIUM |
| `.env` | Environment secrets | CRITICAL |

---

**Version**: 7.0 | **Last Updated**: February 5, 2026
