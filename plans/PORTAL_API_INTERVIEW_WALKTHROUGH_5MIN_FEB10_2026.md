# Portal API 5-Minute Interview Walkthrough

Date: 2026-02-10  
Repo: `/Users/cave/Documents/New project/enterprisehub`

## 0:00-0:30 Problem + Goal

"I hardened a deterministic FastAPI demo and then added three senior-signal upgrades: strict tenant isolation, p95 performance gates, and multilingual readiness (`en/es/he`) while keeping backwards compatibility."

## 0:30-1:45 Tenant Isolation (Step 8/10)

What changed:

1. Canonical tenant context resolution in `portal_api/dependencies.py`:
   - `X-Tenant-ID` header first
   - payload fallback (`location_id` where applicable)
   - default `tenant_default`
2. In-memory state partitioned by tenant in:
   - `modules/inventory_manager.py`
   - `modules/ghl_sync.py`
   - `modules/appointment_manager.py`
3. Tenant-aware reads/writes in:
   - `GET /portal/deck`
   - `POST /portal/swipe`
   - `GET /system/state`
   - `GET /system/state/details`
   - `POST /vapi/tools/book-tour`

Proof shown:

1. Swipe in `tenant_a`
2. Confirm `prop_001` still appears in `tenant_b` deck
3. Confirm tenant-specific counters are isolated

## 1:45-2:45 Performance Gates (Step 9/10)

What changed:

1. `scripts/portal_api_latency_sanity.py` now probes:
   - `/health`
   - `/portal/deck?contact_id=lead_001`
   - `/portal/swipe`
2. Reports `avg`, `p95`, `max`, threshold, pass/fail
3. Exits non-zero when any threshold is breached

Configured thresholds:

1. health p95 <= 50ms
2. deck p95 <= 200ms
3. swipe p95 <= 100ms

Interview point:

"This moves performance from anecdotal to deterministic release-gate behavior."

## 2:45-3:45 Multilingual Readiness (Step 10/10)

What changed:

1. Added `POST /language/detect`
2. Added models in `portal_api/models.py`:
   - `LanguageDetectRequest`
   - `LanguageDetectResponse`
3. Added deterministic detector in `portal_api/routers/language.py`:
   - Hebrew via Unicode range
   - Spanish via accent + stopword heuristics
   - English via stopword heuristic
   - fallback `unknown`

Proof shown:

1. English fixture -> `en`
2. Spanish fixture -> `es`
3. Hebrew fixture -> `he`
4. Ambiguous text -> `unknown`

## 3:45-4:30 Contract + Test Discipline

1. OpenAPI snapshot refreshed and locked in `portal_api/tests/openapi_snapshot.json`
2. Tests expanded for tenant isolation + language detection
3. Final test status: `51 passed`
4. Demo script status: `10/10` pass

## 4:30-5:00 Close

"I prioritized correctness under constraints: isolation safety, measurable p95 gates, and extensible multilingual API contracts, with deterministic scripts and snapshot-locked contracts for repeatable verification."
