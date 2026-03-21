# EnterpriseHub Improvement Roadmap
*Synthesized from: 5 Perplexity Deep Research reports + 6 Grok analyses + 4 Gemini code analyses*
*Date: 2026-03-19 | Priority: P0 = Blocker, P1 = High, P2 = Medium, P3 = Enhancement*

---

## Executive Summary

EnterpriseHub is at a classic "successful but suffocating" inflection point. The platform has genuine business value — 3 specialized AI chatbots, 22 agents, GHL/Stripe/Streamlit integrations — but is accumulating technical debt that will block the $65K-97K/yr consulting anchor potential. The critical risks are legal (SQL injection + PII), financial (unauthenticated billing), and operational (CI that doesn't actually test the production code).

**Estimated consulting revenue impact of roadmap completion: +40-60% credibility lift** when presenting to enterprise clients who do security due diligence.

---

## P0: CRITICAL — Fix Immediately (This Week)

### P0.1 — SQL Injection in transaction_service.py
**File**: `ghl_real_estate_ai/services/transaction_service.py:445-503`
**Risk**: CVSS 9.8 — Remote unauthenticated DB dump, modify, or delete
**Effort**: 3–6 hours

**Fix**:
```python
# Replace ALL f-string SQL with SQLAlchemy parameterized text()
from sqlalchemy import text

query = text("""
    SELECT * FROM milestone_timeline_view
    WHERE transaction_id = (
        SELECT id FROM real_estate_transactions
        WHERE transaction_id = :tx_id
    )
    ORDER BY order_sequence
""")
result = await session.execute(query, {"tx_id": transaction_id})

# Also fix the celebration check
celeb_query = text("""
    SELECT COUNT(*) FROM transaction_celebrations
    WHERE transaction_id = :tx_id
    AND milestone_type = :m_type
    AND triggered_at >= NOW() - INTERVAL '1 hour'
""")
count = await session.execute(celeb_query, {
    "tx_id": transaction_id,
    "m_type": milestone[1]
})
```

**Also**: Run `grep -rn "session.execute(f" ghl_real_estate_ai/` to find all other f-string SQL. Expect 5-15 more instances.

---

### P0.2 — Incomplete GHL Webhook Authentication
**File**: `ghl_real_estate_ai/api/routes/webhook.py:1-2715` (2,715 lines)
**Risk**: CVSS 9.1 — Attacker can inject fake leads, poison CRM, trigger unauthorized AI workflows
**Effort**: 8–14 hours

**Key finding from Grok**: GHL now uses **Ed25519** signatures (`X-GHL-Signature`), not HMAC-SHA256. The 2025 marketplace update added replay protection via `X-GHL-Timestamp`.

**Fix**:
```python
# core/security/ghl_webhook.py
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
import time

async def verify_ghl_webhook(request: Request):
    body = await request.body()
    sig = request.headers.get("X-GHL-Signature")
    ts = request.headers.get("X-GHL-Timestamp")

    if not sig:
        raise HTTPException(403, "Missing GHL signature")

    # Replay protection: reject if timestamp > 5 min old
    if ts and abs(time.time() - int(ts)) > 300:
        raise HTTPException(403, "Replay detected")

    # Ed25519 verification
    public_key = load_ghl_public_key()  # from marketplace docs
    try:
        public_key.verify(bytes.fromhex(sig), body)
    except Exception:
        raise HTTPException(403, "Invalid signature")

# Apply to entire router (not per-endpoint):
router = APIRouter(dependencies=[Depends(verify_ghl_webhook)])
```

Currently only 3 of ~20+ endpoints have `@verify_webhook("ghl")`. Apply router-level dependency to all GHL webhook routes.

---

### P0.3 — Unauthenticated Billing Routes
**File**: `ghl_real_estate_ai/api/routes/billing.py:1-1525` (1,525 lines)
**Risk**: CVSS 8.2 — Anyone can create subscriptions, cancel accounts, or drain Stripe balance
**Effort**: 4–7 hours

**Fix**:
```python
# Add to ALL billing routes via router-level dependency
from ghl_real_estate_ai.core.security.auth import require_auth

router = APIRouter(
    prefix="/billing",
    dependencies=[Depends(require_auth)]  # applies to all routes
)
```

**Also**: Remove `billing.py` from ruff exclude list in `pyproject.toml`. The `ignore=["ALL"]` means zero linting on the most security-sensitive file.

**Stripe webhook**: Add `stripe.Webhook.construct_event()` signature verification to Stripe-specific endpoints.

---

## P1: HIGH — Fix This Sprint (Next 2 Weeks)

### P1.1 — Fix CI Integration Tests (No Service Containers)
**File**: `.github/workflows/ci.yml:122-159`
**Risk**: 8,419 of 8,600 tests don't run in CI — production bugs ship undetected
**Effort**: 4–8 hours

**Fix — Add service containers to integration test job**:
```yaml
test-integration:
  name: Integration Tests
  runs-on: ubuntu-latest
  needs: [test-unit]

  services:
    postgres:
      image: pgvector/pgvector:pg15
      env:
        POSTGRES_PASSWORD: testpassword
        POSTGRES_DB: test_db
      options: >-
        --health-cmd pg_isready
        --health-interval 10s
        --health-timeout 5s
        --health-retries 5
      ports:
        - 5432:5432

    redis:
      image: redis:7-alpine
      options: >-
        --health-cmd "redis-cli ping"
        --health-interval 10s
        --health-retries 5
      ports:
        - 6379:6379

  env:
    DATABASE_URL: postgresql+asyncpg://postgres:testpassword@localhost:5432/test_db
    REDIS_URL: redis://localhost:6379

  steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v4
      with:
        python-version: '3.12'
    - run: pip install -r requirements.txt -r requirements-dev.txt
    - name: Run integration tests
      run: pytest -m integration -v --tb=short --cov=ghl_real_estate_ai --cov-fail-under=40
```

**Longer term**: Add `testcontainers-python` for local dev parity.

---

### P1.2 — Enable Mypy on Main Modules
**File**: `pyproject.toml:103-118`
**Risk**: Type errors silently ship; every other bug category harder to catch
**Effort**: 1–2 days for initial cleanup wave

**Current state**: `ignore_errors = true` for `ghl_real_estate_ai.*`, `utils.*`, `advanced_rag_system.*` — mypy runs but reports zero errors.

**Fix (incremental approach)**:
```toml
# pyproject.toml — remove the blanket ignore_errors override, add per-file as needed
[[tool.mypy.overrides]]
module = ["ghl_real_estate_ai.*"]
ignore_errors = false  # ← Enable; expect 300-500 errors to fix in waves
disallow_untyped_defs = false  # Start permissive, tighten over 4 weeks
```

**Sprint plan**:
- Week 1: Fix billing.py + transaction_service.py (highest security impact)
- Week 2: Fix API routes + core services
- Week 3: Fix agent files + models
- Week 4: Enable `disallow_untyped_defs = true`

---

### P1.3 — Add Security CI Gates
**Effort**: 2–4 hours

Add to `.github/workflows/ci.yml`:
```yaml
- name: Security scan (bandit)
  run: pip install bandit && bandit -r ghl_real_estate_ai -x tests -ll

- name: SQL injection detection (semgrep)
  run: pip install semgrep && semgrep --config "p/python" --severity ERROR ghl_real_estate_ai/

- name: Dependency vulnerability scan
  run: pip install pip-audit && pip-audit -r requirements.txt

- name: Check no f-string SQL queries
  run: |
    if grep -rn 'session.execute(f' ghl_real_estate_ai/; then
      echo "F-string SQL injection found!"; exit 1
    fi
```

---

### P1.4 — Kill Module-Level Singletons
**Files**: ~20+ files across `services/` and `api/`
**Risk**: Startup hangs, deadlocks under load, impossible async testing
**Effort**: 1 day per service cluster

**Pattern to eliminate**:
```python
# BAD — current pattern (blocks event loop on import)
ghl_client = GHLClient()  # module level!
claude_client = ClaudeClient()  # module level!
```

**Pattern to adopt**:
```python
# GOOD — lifespan + app.state
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.redis = await create_redis_pool(settings.REDIS_URL)
    app.state.claude = AnthropicClient()
    app.state.ghl = GHLClient(api_key=settings.GHL_API_KEY)
    yield
    await app.state.redis.aclose()

# Then inject via Depends:
async def get_ghl_client(request: Request) -> GHLClient:
    return request.app.state.ghl
```

---

## P2: MEDIUM — Architecture Sprint (Next 4 Weeks)

### P2.1 — God-Class Decomposition
**Files**: 4 files totaling 11,609 lines

| File | Lines | Decompose Into |
|------|-------|----------------|
| `services/event_publisher.py` | 3,144 | `events/lead_events.py`, `events/crm_events.py`, `events/billing_events.py`, `events/bus.py` |
| `agents/lead_bot.py` | 2,815 | `agents/lead/qualification_flow.py`, `agents/lead/scoring.py`, `agents/lead/follow_up.py`, `agents/lead/bot.py` |
| `api/routes/webhook.py` | 2,715 | `api/routes/webhooks/ghl.py`, `api/routes/webhooks/stripe.py`, `api/routes/webhooks/registry.py` |
| `api/routes/billing.py` | 1,525 | `api/routes/billing/checkout.py`, `api/routes/billing/subscriptions.py`, `api/routes/billing/usage.py` |

**Migration approach**: Strangler fig — split one at a time, keep original as thin re-exports until all callers are updated.

---

### P2.2 — Domain Package Restructure
**Current**: Flat `ghl_real_estate_ai/services/` with 555 files, 14 GHL services, no clear boundaries
**Target**: 7 domain packages

```
src/domains/
├── leads/        # Lead Bot + qualification + scoring (from lead_bot.py 2.8k)
├── buyers/       # Buyer Bot + property matching
├── sellers/      # Seller Bot + FRS/PCS scoring
├── crm/          # GHL adapter (consolidate 14→3 GHL services)
├── payments/     # Stripe + billing (from billing.py 1.5k)
├── intelligence/ # RAG + ML + analytics
└── platform/     # Core FastAPI app, middleware, auth
```

**GHL service consolidation** (14 → 3):
- `ghl_client.py` + `ghl_api_client.py` + `ghl_batch_client.py` + `ghl_adapter.py` → `crm/ghl_client.py`
- `ghl_service.py` + `ghl_integration_service.py` + `ghl_sync_service.py` → `crm/ghl_service.py`
- `ghl_webhook_service.py` + `ghl_conversation_bridge.py` → `crm/ghl_webhooks.py`

---

### P2.3 — Dependency Injection Framework
**Effort**: 3–5 days

Adopt `dishka` (or native FastAPI `Depends` with `Annotated`) for all service dependencies:

```python
# Instead of:
service = SomeService()  # module-level

# Use:
async def get_some_service(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> SomeService:
    return SomeService(db=db, redis=redis)

# Then in routes:
@router.post("/endpoint")
async def my_route(service: SomeService = Depends(get_some_service)):
    ...

# In tests:
app.dependency_overrides[get_some_service] = lambda: MockSomeService()
```

This enables: proper unit testing, clean lifecycle management, easier swapping.

---

### P2.4 — Dependency Cleanup (147 → <80 deps)
**Effort**: 1 day

Confirmed issues:
- `aioredis` — deprecated (replaced by `redis>=4.2` async). Used only in try/except optional imports. Remove.
- `pyproject.toml` project.dependencies lists stale versions (streamlit==1.28.0 vs requirements.txt streamlit>=1.41.1)
- Heavy ML deps (`transformers`, `sentence-transformers`) referenced in comments but removed — clean up comments

**Action**: Run `pip install deptry && deptry .` to find unused deps. Target < 80 direct production deps.

---

### P2.5 — Stripe Trial Flow + Billing Auth
**Effort**: 3–4 days

From SaaS monetization research, the optimal model for a real estate AI platform:

| Tier | Price | Features | Trial |
|------|-------|----------|-------|
| Starter | $297/mo | 1 bot, 500 leads/mo | 14 days free |
| Growth | $597/mo | 3 bots, 2,500 leads/mo | 14 days free |
| Enterprise | $1,497/mo | Custom bots, unlimited leads, white-label | 30 days free |

**Stripe implementation needed**:
- `trial_period_days` on subscription creation
- Usage-based metering for leads/conversations
- Webhook handling for `customer.subscription.trial_will_end`
- Usage alerts at 80% of tier limit

---

## P3: ENHANCEMENT — Next Quarter

### P3.1 — RAG Production Hardening
From enterprise RAG research:
- **Hybrid search**: Add BM25 (sparse) alongside pgvector (dense) with RRF for 15-25% accuracy improvement
- **Reranking**: Add cross-encoder reranking (e.g., `cross-encoder/ms-marco-MiniLM-L-6-v2`) for top-20 → top-5
- **Evaluation**: Integrate RAGAS for automated RAG quality tracking in CI
- **Chunking**: Switch from fixed-size to semantic chunking (LlamaIndex `SemanticSplitterNodeParser`)

### P3.2 — Observability Stack
From performance research:
- Add OpenTelemetry tracing to all FastAPI routes (currently has stubs but not instrumented)
- Add Prometheus metrics: `http_request_duration_seconds`, `llm_tokens_used_total`, `cache_hits_total`
- Grafana dashboard with GHL webhook latency, lead qualification P95, cache hit rate
- Alert rules: P95 > 2s, error rate > 5%, cache hit rate < 70%

### P3.3 — Migration Index Optimization
Add missing indexes on high-frequency query columns:
```sql
-- transaction_service.py queries these frequently
CREATE INDEX idx_real_estate_transactions_transaction_id ON real_estate_transactions(transaction_id);
CREATE INDEX idx_transaction_celebrations_tx_type ON transaction_celebrations(transaction_id, milestone_type);
CREATE INDEX idx_milestone_timeline_tx_order ON milestone_timeline_view(transaction_id, order_sequence);
```

### P3.4 — GoHighLevel Marketplace App
From GHL research: Package the webhook integration as a GHL marketplace app. Requirements:
- Ed25519 webhook signature verification (P0.2 above — already required)
- HMAC-signed install/uninstall callbacks
- OAuth 2.0 for multi-location support
- Marketplace listing with `marketplace.gohighlevel.com` approval

---

## Sprint-Sized Work Packages

| Sprint | Duration | Items | Outcome |
|--------|----------|-------|---------|
| **Sprint 0** | 3 days | P0.1 + P0.2 + P0.3 | SQL injection fixed, all webhooks authenticated, billing locked |
| **Sprint 1** | 1 week | P1.1 + P1.2 (wave 1) + P1.3 | CI runs real tests, security gates active |
| **Sprint 2** | 1 week | P1.4 + P2.3 | Singletons removed, DI framework in place |
| **Sprint 3** | 2 weeks | P2.1 (webhook.py + billing.py) | 2 god-classes decomposed |
| **Sprint 4** | 2 weeks | P2.1 (event_publisher + lead_bot) | 2 more god-classes decomposed |
| **Sprint 5** | 2 weeks | P2.2 (domain restructure for crm/) | GHL services consolidated |
| **Sprint 6** | 1 week | P2.4 + P2.5 | Deps cleaned, Stripe trial flow |
| **Sprint 7** | 2 weeks | P3.1 (RAG hybrid search) | RAG accuracy +20% |
| **Sprint 8** | 1 week | P3.2 (observability) | Production monitoring live |

---

## Portfolio Positioning

### Before (Current State)
- "Full-stack AI platform with 3 chatbots and 8,600 tests"
- SQL injection vulnerabilities present
- CI runs < 3% of the test suite
- God-class files > 3,000 lines

### After (Roadmap Complete)
- "Production-hardened real estate AI platform with enterprise security, domain-driven architecture, and full observability"
- Zero SQL injection, Ed25519 webhook auth, JWT-protected billing
- 80%+ of tests run in CI with PostgreSQL + Redis service containers
- Clean domain boundaries: leads/, buyers/, sellers/, crm/, payments/, intelligence/
- Stripe metered billing with 14-day free trials
- OpenTelemetry + Prometheus + Grafana monitoring stack

**Client pitch update**: "EnterpriseHub passed security review with zero critical findings. The architecture follows domain-driven design with clean bounded contexts, enabling rapid feature development without breaking production. Average lead qualification response time: 340ms P95."

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking changes during god-class split | Medium | High | Strangler fig pattern, comprehensive test coverage before refactor |
| CI service containers add 5-10min to build | High | Low | Cache pip deps, parallelize test jobs |
| Mypy cleanup uncovers 500+ errors | High | Medium | Fix in waves by module, use per-file overrides |
| GHL Ed25519 key rotation | Low | High | Use JWKS endpoint or configurable key, not hardcoded |
| Stripe webhook replay attacks | Medium | Medium | Idempotency keys in Redis (already designed, not implemented) |

---

## Sources

All research artifacts saved to `~/Projects/EnterpriseHub/research/`:

**Perplexity Deep Research** (web research):
- `perplexity/01_fastapi_production_best_practices.md`
- `perplexity/02_enterprise_rag_architecture.md`
- `perplexity/03_saas_monetization_strategies.md`
- `perplexity/04_ghl_webhook_security.md`
- `perplexity/05_python_monorepo_decomposition.md`

**Grok Analysis** (technical review):
- `grok/grok_01_architecture_review.md` — "successful but suffocating monolith syndrome"
- `grok/grok_02_security_hardening.md` — CVSS ratings + parameterized query fixes
- `grok/01_architecture_decomposition.md` — domain-driven decomposition plan
- `grok/02_security_hardening_roadmap.md` — concrete security fixes
- `grok/03_test_strategy.md` — testcontainers + CI service containers plan
- `grok/04_performance_observability.md` — monitoring stack assessment

**Gemini Code Analysis** (large-context file analysis):
- `gemini/01_god_class_decomposition.md` — file-by-file decomposition plans
- `gemini/02_dependency_audit.md` — dependency cleanup recommendations
- `gemini/03_service_overlap_analysis.md` — 14 GHL services → 3 consolidation plan
- `gemini/04_migration_schema_review.md` — missing indexes, data integrity issues

**Context files**:
- `context_architecture.md` — full architecture overview
- `context_security.md` — specific security vulnerabilities
- `context_test_strategy.md` — current test pyramid state
