# Parallel Execution Spec: Jorge GHL Bots — Code-Side Improvements

**Created**: 2026-02-19
**Beads**: EnterpriseHub-2vtb, EnterpriseHub-b4w1, EnterpriseHub-i3nc, EnterpriseHub-xdtv
**Parent**: EnterpriseHub-m9zc (Jorge GHL deployment — BLOCKED on credentials)
**Prerequisite**: None of these require GHL credentials. All can run in parallel.

---

## Workstream A: Wire `is_first_message` Pipeline (EnterpriseHub-2vtb)

**Effort**: 30 min | **Risk**: Low | **Tests**: 2 new + verify 114 existing

### Problem
The `ResponsePostProcessor` pipeline (5 stages: Language → TCPA → Compliance → AI Disclosure → SMS Truncation) is fully tested but **only used in tests**. The webhook handler (`api/routes/webhook.py`) calls bots directly and applies ad-hoc compliance/truncation, missing the proactive SB 1001 first-message disclosure.

### Implementation

**File 1: `ghl_real_estate_ai/api/routes/webhook.py`**

Add imports at top:
```python
from ghl_real_estate_ai.services.jorge.response_pipeline.factory import get_response_pipeline
from ghl_real_estate_ai.services.jorge.response_pipeline.models import ProcessingContext
```

Add pipeline wiring in 3 locations (seller, buyer, lead):

**Seller Bot (~line 641, after response generation):**
```python
# Wire response pipeline (SB 1001 disclosure + SMS truncation)
is_first_message = not history or len(history) == 0
pipeline_context = ProcessingContext(
    contact_id=contact_id,
    bot_mode="seller",
    channel="sms",
    user_message=user_message,
    is_first_message=is_first_message,
)
pipeline = get_response_pipeline()
processed = await pipeline.process(final_seller_msg, pipeline_context)
final_seller_msg = processed.message
```

**Buyer Bot (~line 797):** Same pattern, `bot_mode="buyer"`
**Lead Bot (~line 962):** Same pattern, `bot_mode="lead"`

### Key Files
| File | Change | Lines |
|------|--------|-------|
| `api/routes/webhook.py` | Add 2 imports + 3 wiring blocks | Top, ~641, ~797, ~962 |

### Tests
- `test_webhook_first_message_gets_proactive_disclosure()`
- `test_webhook_subsequent_message_gets_footer_only()`
- Verify all 114 existing Jorge tests still pass

### Conversation History Detection
```python
history = await conversation_manager.get_conversation_history(contact_id)
is_first_message = not history or len(history) == 0
```
Edge cases: `None` → first, `[]` → first, `[{...}]` → not first.

---

## Workstream B: Redis Handoff Backend (EnterpriseHub-b4w1)

**Effort**: 5 hours | **Risk**: Medium | **Tests**: 8 new

### Problem
`JorgeHandoffService` stores ALL handoff state in 4 class-level dicts. Single-worker only. Explicitly flagged: "NOT safe for multi-worker deployments" (line 130).

### In-Memory State Inventory

| Variable | Type | Purpose | Redis Key Pattern | TTL |
|----------|------|---------|-------------------|-----|
| `_handoff_history` | `Dict[str, List]` | Circular prevention + rate limiting | `handoff:history:{contact_id}` (sorted set) | 7 days |
| `_handoff_outcomes` | `Dict[str, List]` | Success/failure tracking per route | `handoff:outcomes:{route}` (list) | None |
| `_active_handoffs` | `Dict[str, float]` | Concurrent handoff locks | `handoff:lock:{contact_id}` (string) | 30 sec |
| `_analytics` | `Dict[str, Any]` | Aggregate metrics | N/A (transient, no persistence) | — |

### Implementation

**New File: `ghl_real_estate_ai/services/jorge/handoff_repository.py`**

```python
class RedisHandoffRepository:
    """Redis-backed persistence for JorgeHandoffService state."""

    async def initialize(self, redis_url: str) -> None
    async def save_handoff_history(self, contact_id: str, event: dict) -> None
    async def load_handoff_history(self, contact_id: str, since_ts: float) -> list[dict]
    async def save_handoff_outcome(self, route: str, outcome: dict) -> None
    async def load_handoff_outcomes(self, since_ts: float) -> dict[str, list[dict]]
    async def acquire_lock(self, contact_id: str, timeout: int = 30) -> bool
    async def release_lock(self, contact_id: str) -> None
    async def cleanup_expired(self) -> None
```

**Existing integration points:**
- `jorge_handoff_service.py:434` — `set_repository()` method already exists
- `jorge_handoff_service.py:load_from_database(since_minutes)` — hydration method ready
- Redis pattern: `redis.asyncio` with ConnectionPool (same as `tiered_cache_service.py:311`)

**Wiring (in `api/main.py` lifespan):**
```python
handoff_repo = RedisHandoffRepository(redis_url=settings.redis_url)
await handoff_repo.initialize()
handoff_service.set_repository(handoff_repo)
await handoff_service.load_from_database(since_minutes=10080)  # 7 days
```

**Fallback**: If Redis unavailable, continue with in-memory state (single-worker mode).

### Key Files
| File | Change |
|------|--------|
| `services/jorge/handoff_repository.py` | **NEW** — RedisHandoffRepository class |
| `services/jorge/jorge_handoff_service.py` | Minor: ensure load_from_database handles Redis schema |
| `api/main.py` | Wire repository in lifespan startup |

### Tests
- `test_save_and_load_handoff_history()`
- `test_circular_prevention_across_workers()`
- `test_rate_limit_counters_redis()`
- `test_lock_acquisition_and_release()`
- `test_lock_auto_expiry()`
- `test_outcome_aggregation_per_route()`
- `test_graceful_fallback_no_redis()`
- `test_hydration_on_startup()`

---

## Workstream C: Tier 2 Perplexity Features (EnterpriseHub-i3nc)

**Effort**: 2 hours | **Risk**: Low | **Tests**: 6 new

### C1: "Just Looking" Objection Handler

**Current pattern** in `agents/seller/stall_detector.py`:
```python
STALL_KEYWORDS = {
    "thinking": ["think", "pondering", "consider", "decide"],
    "get_back": ["get back", "later", "next week", "busy"],
    "zestimate": ["zestimate", "zillow", "online value", "estimate says"],
    "agent": ["agent", "realtor", "broker", "with someone"],
}
```

**Add to `stall_detector.py` (line ~25):**
```python
"just_looking": ["just looking", "just browsing", "exploring options",
                  "kicking tires", "not ready yet", "window shopping",
                  "just curious"],
```

**Add to `agents/seller/response_generator.py` friendly_responses (~line 35):**
```python
"just_looking": [
    "Hey, I appreciate that. Most people start that way. Quick question — if a serious buyer showed up with cash and wanted to close fast, would that be worth exploring?",
    "Totally fair! That said, would it help to know what your home could go for in today's market? No strings attached.",
    "No pressure at all. A lot of folks just want a number to keep in their back pocket. Want me to pull some comps from your area?",
]
```

**Add to `agents/buyer/response_generator.py` (~line 50):**
```python
"just_looking": [
    "Hey, totally get it! A lot of buyers start by exploring. What area are you most curious about?",
    "No rush at all. Most people browse for a while before diving in. What caught your eye so far?",
    "That's a great way to start. Want me to send you some listings in a specific area so you can get a feel for the market?",
]
```

### C2: CMA Disclaimer + Confidence Routing

**Add to `ghl_utils/jorge_config.py` (after line ~215):**
```python
CMA_DISCLAIMERS = {
    "high": "This estimate is based on {comp_count} comparable sales in your area. Market conditions, property condition, and buyer demand may affect actual value. Not a professional appraisal.",
    "medium": "This is a preliminary estimate based on limited comparable data. For a precise valuation, Jorge can walk you through it in person.",
    "low": "We don't have enough recent sales data to give a reliable estimate for your area right now. Jorge can provide a personalized analysis.",
}
CMA_CONFIDENCE_THRESHOLDS = {"high": 70.0, "medium": 50.0}
```

**Modify `agents/seller/cma_service.py` (after line ~69):**
```python
confidence = cma_report.get("confidence_score", 0)
if confidence >= CMA_CONFIDENCE_THRESHOLDS["high"]:
    disclaimer = CMA_DISCLAIMERS["high"].format(comp_count=cma_report.get("comp_count", "several"))
elif confidence >= CMA_CONFIDENCE_THRESHOLDS["medium"]:
    disclaimer = CMA_DISCLAIMERS["medium"]
else:
    disclaimer = CMA_DISCLAIMERS["low"]
cma_report["disclaimer"] = disclaimer
cma_report["use_full_cma"] = confidence >= CMA_CONFIDENCE_THRESHOLDS["medium"]
```

### C3: Re-engagement (Documentation Only)

Re-engagement templates already exist at `prompts/reengagement_templates.py` (3 tiers: 24h/48h/72h). Dormancy detector is a GHL-side concern (workflow trigger based on `last_bot_interaction` custom field timestamp). No code changes needed — just document in setup guide that GHL should have a "Dormant Lead Re-engagement" workflow using the bot's `last_bot_interaction` field.

### Key Files
| File | Change |
|------|--------|
| `agents/seller/stall_detector.py` | Add `just_looking` keywords (line ~25) |
| `agents/seller/response_generator.py` | Add `just_looking` responses (line ~35) |
| `agents/buyer/response_generator.py` | Add `just_looking` responses (line ~50) |
| `ghl_utils/jorge_config.py` | Add CMA disclaimers + thresholds (line ~215) |
| `agents/seller/cma_service.py` | Add confidence routing + disclaimer injection (line ~69) |

### Tests
- `test_just_looking_detected_as_stall()` (seller)
- `test_just_looking_detected_as_stall()` (buyer)
- `test_just_looking_response_in_jorge_voice()`
- `test_cma_high_confidence_full_disclaimer()`
- `test_cma_low_confidence_fallback_message()`
- `test_cma_disclaimer_appended_to_report()`

---

## Workstream D: Deploy Infrastructure (EnterpriseHub-xdtv)

**Effort**: 1.5 hours | **Risk**: Low | **Tests**: Smoke test only

### D1: Fix Dockerfile

**File**: `ghl_real_estate_ai/Dockerfile`

**Current (WRONG):**
```dockerfile
CMD ["streamlit", "run", "streamlit_demo/app.py", ...]
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
```

**Fix to:**
```dockerfile
EXPOSE 8000
CMD ["uvicorn", "ghl_real_estate_ai.api.main:socketio_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/api/health/live || exit 1
```

### D2: Fix railway.toml

**File**: `ghl_real_estate_ai/railway.toml`

**Change**: `app` → `socketio_app`, add `--workers 4`
```toml
[deploy]
startCommand = "uvicorn ghl_real_estate_ai.api.main:socketio_app --host 0.0.0.0 --port $PORT --workers 4"
```

### D3: Create fly.toml

**New File**: `ghl_real_estate_ai/fly.toml`
```toml
app = "jorge-ghl-bots"
primary_region = "lax"

[build]
dockerfile = "Dockerfile"

[env]
ENVIRONMENT = "production"
LOG_LEVEL = "info"

[http_service]
internal_port = 8000
force_https = true
auto_stop_machines = true
auto_start_machines = true

[[http_service.checks]]
grace_period = "10s"
interval = "30s"
timeout = "5s"
method = "get"
path = "/api/health/live"

[[vm]]
memory = "512mb"
cpu_kind = "shared"
cpus = 1
```

### D4: Fix health.py (Hardcoded Hosts)

**File**: `ghl_real_estate_ai/api/health.py` (lines 79-86)

**Current (WRONG):**
```python
self.redis_client = redis.Redis(host="localhost", port=6379, ...)
self.db_pool = await asyncpg.create_pool("postgresql://localhost:5432/ghl_real_estate", ...)
```

**Fix to:**
```python
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
db_url = os.getenv("DATABASE_URL", "postgresql://localhost:5432/ghl_real_estate")
self.redis_client = redis.from_url(redis_url, decode_responses=True)
self.db_pool = await asyncpg.create_pool(db_url)
```

### D5: Add Missing Dependencies

**File**: `requirements.txt`

Add:
```
asyncpg>=0.29.0,<1.0
python-socketio>=5.9.0,<6.0
```

### D6: Add Startup Env Validation

**File**: `ghl_real_estate_ai/api/main.py` (in lifespan, before service init)

```python
def _validate_required_env_vars():
    required = ["REDIS_URL", "DATABASE_URL", "GHL_API_KEY", "ANTHROPIC_API_KEY"]
    missing = [v for v in required if not os.getenv(v)]
    if missing:
        logger.error("Missing required env vars: %s", ", ".join(missing))
        raise RuntimeError(f"Cannot start without: {', '.join(missing)}")
```

### Key Files
| File | Change |
|------|--------|
| `ghl_real_estate_ai/Dockerfile` | Fix CMD, EXPOSE, HEALTHCHECK |
| `ghl_real_estate_ai/railway.toml` | Fix startCommand |
| `ghl_real_estate_ai/fly.toml` | **NEW** |
| `ghl_real_estate_ai/api/health.py` | Read from env vars |
| `requirements.txt` | Add asyncpg, python-socketio |
| `ghl_real_estate_ai/api/main.py` | Add env validation |

---

## Parallel Execution Map

```
     ┌─────────────────────┐
     │   All 4 Independent  │
     │   (No Dependencies)  │
     └──────┬──┬──┬──┬─────┘
            │  │  │  │
    ┌───────▼┐ │  │  │
    │   A    │ │  │  │  Wire is_first_message (30 min)
    └────────┘ │  │  │
       ┌───────▼┐ │  │
       │   B    │ │  │  Redis handoff backend (5 hrs)
       └────────┘ │  │
          ┌───────▼┐ │
          │   C    │ │  Tier 2 features (2 hrs)
          └────────┘ │
             ┌───────▼┐
             │   D    │  Deploy infrastructure (1.5 hrs)
             └────────┘
                 │
          ┌──────▼──────┐
          │ Integration  │
          │   Test Run   │  pytest full suite
          └──────────────┘
```

All 4 workstreams are fully independent. No shared files between them (webhook.py is only touched by A, handoff_service by B, stall_detector/cma_service by C, Dockerfile/health by D).

---

## Verification Checklist

After all 4 workstreams complete:
1. `pytest ghl_real_estate_ai/tests/ --timeout=30 -q` — all 114+ Jorge tests pass
2. New tests for A (2), B (8), C (6) pass
3. `docker build -f ghl_real_estate_ai/Dockerfile .` — builds successfully
4. Manual review: first-message disclosure text, just_looking responses, CMA disclaimers
5. `grep -r "localhost" ghl_real_estate_ai/api/health.py` — no hardcoded hosts remain
