# EnterpriseHub: Real Estate AI & BI Platform

**Purpose**: AI-powered lead qualification, chatbot orchestration, and BI dashboards for the Rancho Cucamonga real estate market.

**References**:
- `.claude/reference/domain-context.md` (market, terminology, bots)
- `.claude/reference/quality-standards.md` (perf targets, testing, KPIs)
- [`AGENTS.md`](AGENTS.md) (human agent personas and workflows)

**On entry**: run `bd list`; priorities P0: ichh, qnef; P1: az91, ja6d.

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
- **Alembic migrations**: Always require DROP/ALTER column operations to include a corresponding rollback migration in `downgrade()`

## Critical Services
| Service | File | Key Behavior |
|---------|------|-------------|
| Claude Orchestration | `services/claude_orchestrator.py` | Multi-strategy parsing, L1/L2/L3 cache, <200ms overhead |
| Agent Mesh | `services/agent_mesh_coordinator.py` | Governance, routing, auto-scaling, audit trails |
| GHL Client | `services/enhanced_ghl_client.py` | 10 req/s rate limit, real-time CRM sync |
| Jorge Handoff | `services/jorge/jorge_handoff_service.py` | 0.7 confidence threshold, 3/hr + 10/day rate limits |

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

## Task Tracking
Uses **Beads** (`bd`): `bd ready` for available work, `bd close` when done, `bd sync` + `git push` before ending sessions.

## Landing the Plane

When ending a session, complete ALL steps in order:

1. Run tests + linters if code changed
2. Update Beads task status (`bd close` / `bd sync`)
3. Push to remote:
   ```bash
   git pull --rebase && bd sync && git push
   git status  # must show "up to date with origin"
   ```

Work is NOT complete until `git push` succeeds. Stranded local commits = incomplete work.
