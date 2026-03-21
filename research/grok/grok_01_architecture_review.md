# Grok Architecture Review: FastAPI Monorepo for Real Estate AI SaaS

*Source: Grok (grok.com) — Thought for 24s, 55 sources*

## Overall Assessment

**"This architecture is at a breaking point — classic 'successful but suffocating' monolith syndrome."**

You've built a genuinely ambitious real-estate AI SaaS (3 specialized qualification bots + 22 Claude agents + GHL/Stripe/Streamlit integrations), which is impressive. However, the current scale (555 flat services, 86 routers, god-classes >2.7k LOC, 147 direct deps, one giant `ghl_real_estate_ai/` package) combined with the listed anti-patterns makes further feature velocity, onboarding, and reliability extremely painful. This is the exact moment where many teams either refactor aggressively or watch the codebase become unmaintainable.

The stack itself is excellent (async-first FastAPI + Postgres + Redis + multi-LLM + CRM + payments + Streamlit). The high test count (8,600+) is a huge asset if you can make the tests fast and isolated again.

## Quick Severity Rating of Known Issues

| Issue | Severity | Root Cause | Immediate Pain |
|-------|----------|------------|----------------|
| Module-level singletons blocking async loop | **Critical** | Sync init on import | Startup hangs, deadlocks under load |
| No DI framework / heavy direct imports | **Critical** | Everything coupled | Impossible clean mocking, test fragility |
| Circular imports (services ↔ routes) | **High** | Flat package + bidirectional deps | Import hell, import-time side effects |
| Overlapping "client"/service names + god classes | **High** | No bounded contexts | Cognitive load, merge conflicts |
| Everything in one ghl_real_estate_ai/ package | **High** | No domain separation | 500+ file folder, impossible navigation |

## Recommended Target Architecture (Domain-Driven + Clean-ish)

Move to a feature/domain package structure (the pattern used successfully in production FastAPI monoliths at scale, including LLM-heavy apps). This is the consensus "gold standard" in 2025–2026:

```
src/
├── core/                    # shared, never import from domains
│   ├── config.py
│   ├── database.py          (async engine + session factory with yield)
│   ├── redis.py
│   ├── lifespan.py          # ← all singletons here, async init
│   ├── dependencies.py
│   ├── exceptions.py
│   └── adapters/            # abstract ports + concrete (GHL, Stripe, Claude, Gemini)
│
├── domains/                 # ← this is the game-changer
│   ├── leads/               # qualification, Lead Bot
│   │   ├── router.py
│   │   ├── schemas.py
│   │   ├── models.py        (SQLAlchemy)
│   │   ├── repository.py
│   │   ├── service.py       OR use_cases/
│   │   ├── bots/lead_bot.py # ← split the 2.8k monster
│   │   ├── ai/qualification_agent.py
│   │   └── dependencies.py
│   ├── buyers/
│   ├── sellers/
│   ├── properties/
│   ├── ai/                  # shared orchestration
│   │   ├── agents/          # 22 Claude agents as small, injectable classes
│   │   ├── orchestrator.py
│   │   ├── prompts/
│   │   └── llm_adapter.py   (Claude + Gemini via factory)
│   ├── crm/                 # GHL adapter + webhooks
│   ├── payments/
│   ├── webhooks/            # split the 2.7k webhook.py into per-provider handlers
│   └── ...
│
├── api/                     # thin layer only
│   ├── v1/
│   │   └── __init__.py      (include all domain routers)
│   └── main.py
│
├── tests/
│   ├── unit/domains/leads/...
│   └── integration/
└── streamlit/               # separate entrypoint, calls same API or shared core
```

**Key principles this enforces:**
- Each domain is self-contained and can be extracted to a microservice later
- Routers stay thin (only HTTP + call service)
- Business logic lives in services/use_cases/repositories (not 3k-line files)
- Adapters for all externals (GHL, Stripe, Claude) → easy mocking + provider swapping

## Immediate High-Impact Fixes (1–2 weeks)

### 1. Kill Module-Level Singletons
Move everything to lifespan + app.state (or `Depends(get_llm_client)` with `lru_cache`):

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_async_redis()
    app.state.claude = await init_claude_client()  # async!
    yield
    # cleanup
```

Never `Client()` at module level again.

### 2. Introduce Real DI Immediately
- Start with native FastAPI `Depends` + `Annotated` everywhere (you already have the power)
- Add `dependency-injector` or `dishka` if you want a full container (highly recommended for 500+ files)
- Override in tests: `app.dependency_overrides[get_lead_service] = mock_service`

### 3. Split the God Classes (start here — highest ROI)
- `event_publisher.py` → Redis Stream / Celery / custom EventBus + domain-specific publishers
- `lead_bot.py` → `qualification_flow.py` + `agent_runner.py` + `prompt_builder.py` + tiny `LeadBot` class
- `webhook.py` → `webhooks/ghl.py`, `webhooks/stripe.py` + registry in `core`

### 4. Stop Circular Imports
- Use full paths: `from src.domains.leads.service import ...`
- Pydantic relations → string literals + `.model_rebuild()` or forward refs
- Move shared things to `core/` so domains only depend inward

### 5. Dependency Hygiene
- Switch to `uv` or Poetry with groups (dev, ai, prod)
- Audit with `pip-audit` + `deptry`
- Target <80 direct runtime deps

## Longer-Term

- Adopt Repository + Use-Case (or full Clean Architecture with ports/adapters) inside each domain. This naturally kills overlapping "client" services.
- For the 22 Claude agents + 3 bots: build a tiny `AgentFactory(Depends(get_llm_adapter))` + prompt/version registry. Do NOT keep them as 22 separate giant files.
- Background tasks / Dramatiq/Celery for heavy AI qualification flows and CRM syncs (never block API)
- Streamlit → call your own FastAPI (or shared core if same process) — keep it thin

## Expected Benefits After Refactor

| Metric | Before | After |
|--------|--------|-------|
| Onboarding | New dev must understand 555-file mess | Can understand one domain in <1 day |
| Test speed | Slow/fragile due to coupling | Unit tests 10–100× faster with proper mocks |
| Feature velocity | Adding new bot = touching everywhere | Copy one domain folder + tweak |
| Reliability | Random deadlocks from sync init | Async loop clean |
| Scalability path | Everything coupled | Any domain can split to own service |

## Suggested Refactoring Roadmap

- **Week 1–2**: Core + DI + lifespan + split one god class (webhook) + move one domain (leads) to new structure
- **Month 1**: All domains migrated, services slimmed, circulars gone
- **Month 2**: Full test overhaul + agent factory + adapter layer
- **Ongoing**: Extract heavy domains to microservices only when needed (most teams never do — this structure scales to 50k+ LOC comfortably)

## Grok's Verdict

> "This is not theoretical — it is the exact pattern used in production LLM + SaaS FastAPI codebases that started exactly where you are now (flat → domain explosion → clean recovery). Your codebase has massive business value already baked in. A targeted refactor along these lines will unlock the next 10× growth without rewriting from scratch."
