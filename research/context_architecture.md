# EnterpriseHub Architecture Context (for Research Tools)

## What This Is
A real estate AI SaaS platform built on FastAPI + Streamlit + PostgreSQL + Redis + Claude AI.
Target market: Rancho Cucamonga real estate agents. Domain: AI-driven lead qualification, chatbots, BI dashboards.

## Stack
- **API**: FastAPI (async), Python 3.12
- **Frontend**: Streamlit BI dashboards
- **Database**: PostgreSQL + Alembic migrations
- **Cache**: 3-tier (L1 in-memory, L2 Redis, L3 PostgreSQL), 88% cache hit rate
- **AI**: Claude (primary), Gemini, Perplexity
- **CRM**: GoHighLevel (GHL) integration
- **Billing**: Stripe (partial integration)
- **Auth**: JWT (1hr), 100 req/min rate limit

## Scale Metrics
- 555 service files in `ghl_real_estate_ai/services/`
- 86 API route files in `ghl_real_estate_ai/api/routes/`
- 3 chatbots (Lead Bot, Buyer Bot, Seller Bot)
- 22 Claude Code agents
- 8,600+ test functions (only ~181 run in CI without external deps)
- 147 direct Python dependencies
- 14 Alembic migrations

## God-Class Files (Critical)
| File | Lines | Problem |
|------|-------|---------|
| `services/event_publisher.py` | 3,144 | All event types in one class |
| `agents/lead_bot.py` | 2,815 | State machine + scoring + follow-up all mixed |
| `api/routes/webhook.py` | 2,715 | All GHL webhook handling, partial auth |
| `api/routes/billing.py` | 1,525 | No auth, excluded from all linters |
| `api/routes/bot_management.py` | 1,704 | All bot management in one file |
| `services/claude_orchestrator.py` | 1,935 | Multi-model routing + caching + parsing |

## Known Architecture Issues
1. Module-level singleton instantiation (blocking async event loop)
2. No dependency injection framework (direct service instantiation in routes)
3. Circular imports between services and routes
4. Services directory has overlapping responsibilities (e.g., 3 different "client" services)
5. No clear domain boundaries (everything in `ghl_real_estate_ai/`)

## CI Pipeline Status
- CI workflow exists (`ci.yml`) but integration tests run WITHOUT service containers
- Unit tests run on `ghl_real_estate_ai/tests/unit/` - no PostgreSQL/Redis
- Integration tests: `pytest -m integration` without postgres/redis → fail in CI
- mypy runs but `ignore_errors = true` for ALL main modules
- ruff excludes `billing.py` entirely from linting
- `continue-on-error: true` on extended unit tests

## Dependency Issues
- `aioredis` deprecated (replaced by redis-py async)
- `pyproject.toml` project.dependencies shows stale versions vs requirements.txt
- Heavy ML deps (sentence-transformers, transformers) removed but still referenced in comments
- `langgraph==1.0.6` pinned (major API changes in recent versions)
