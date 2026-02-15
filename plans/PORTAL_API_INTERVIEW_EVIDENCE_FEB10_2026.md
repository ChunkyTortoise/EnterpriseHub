# Portal API Interview Evidence Bundle

Date: 2026-02-10  
Repository: `/Users/cave/Documents/New project/enterprisehub`

## 1) Scope Executed

Advanced demo enhancement scope completed on top of the hardened baseline:

1. Tenant isolation (header-first tenant context, payload fallback, default tenant compatibility)
2. Performance validation with p95 threshold gates
3. Deterministic multilingual detection endpoint (`en/es/he/unknown`)
4. Demo script upgraded from `7/7` to `10/10`
5. OpenAPI snapshot refreshed and re-locked

## 2) Validation Bundle Run

Executed from repo root:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh

ruff check main.py portal_api modules scripts/portal_api_client_example.py scripts/portal_api_latency_sanity.py

python3 -m py_compile \
  main.py \
  portal_api/app.py \
  portal_api/dependencies.py \
  portal_api/models.py \
  portal_api/routers/root.py \
  portal_api/routers/vapi.py \
  portal_api/routers/portal.py \
  portal_api/routers/ghl.py \
  portal_api/routers/admin.py \
  portal_api/routers/language.py \
  modules/inventory_manager.py \
  modules/ghl_sync.py \
  modules/appointment_manager.py \
  modules/voice_trigger.py \
  scripts/portal_api_client_example.py \
  scripts/portal_api_latency_sanity.py

pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests

bash scripts/portal_api_interview_demo.sh
```

Observed outcomes:

1. `bash -n`: pass
2. `ruff`: `All checks passed!`
3. `py_compile`: pass
4. `pytest`: `51 passed`
5. Demo script: pass (`10/10`)

## 3) Demo Output Evidence (10/10)

Observed advanced-step output lines:

1. `[STEP] 8/10 tenant isolation proof`
2. `[PASS] tenant_a and tenant_b are fully isolated`
3. `[STEP] 9/10 performance validation`
4. `[PASS] p95 thresholds met`
5. `[STEP] 10/10 multi-language detection`
6. `[PASS] multilingual readiness verified (en/es/he)`
7. `[PASS] interview demo flow completed (10/10)`

## 4) Performance Gate Snapshot

From the same `10/10` demo run:

| endpoint | runs | avg_ms | p95_ms | max_ms | p95_threshold_ms | status |
|---|---:|---:|---:|---:|---:|---|
| health | 10 | 0.42 | 0.55 | 0.55 | 50.00 | PASS |
| deck | 10 | 0.74 | 1.35 | 1.35 | 200.00 | PASS |
| swipe | 10 | 0.95 | 1.55 | 1.55 | 100.00 | PASS |

## 5) Tenant Isolation Proof Points

Validated behavior:

1. Swipe in `tenant_a` does not remove property from `tenant_b` deck.
2. `tenant_b` activity does not increment `tenant_a` counters.
3. Header tenant takes precedence over payload fallback.
4. No-header flows continue to operate on `tenant_default`.

## 6) Contract Lock Evidence

OpenAPI contract changes are snapshot-locked:

1. New `POST /language/detect` request/response schemas
2. Tenant header parameters on tenant-scoped routes
3. Tenant fields in state/detail snapshots

Lock status:

1. Snapshot refreshed: `portal_api/tests/openapi_snapshot.json`
2. Lock test: `portal_api/tests/test_portal_api_openapi_snapshot.py` (pass)

## 7) Interview Talk Track Anchors

1. Multi-tenant safety: deterministic zero-leak tests and script proof
2. Production operability: p95 gates with explicit pass/fail exits
3. Multilingual readiness: working endpoint + fixture-backed tests (`en/es/he`)
4. Discipline: all changes contract-locked and reproducibly validated
