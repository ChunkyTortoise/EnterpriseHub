# Portal API Advanced Demo Enhancement PR Summary

## Suggested PR Title

`Portal API: add tenant isolation, p95 performance gates, and multilingual detection (10/10 demo)`

## Suggested PR Body

### Why

This PR upgrades the Portal API interview/demo slice from baseline deterministic reliability to production-thinking evidence in three areas:

1. Tenant isolation safety (zero cross-tenant leakage)
2. Performance validation as p95 pass/fail gates
3. Multilingual readiness with typed language detection contracts

### What changed

1. Tenant context + isolation
   - Added canonical tenant resolution (`X-Tenant-ID` header, payload fallback, default tenant)
   - Partitioned in-memory interactions/actions/bookings by tenant
   - Updated tenant-scoped behavior for deck, swipe, state, state-details, and book-tour
2. Performance gating
   - Extended latency script to probe `health`, `deck`, `swipe`
   - Added configurable p95 thresholds with non-zero exit on breach
   - Wired into interview demo step `9/10`
3. Multilingual detection
   - Added `POST /language/detect`
   - Added typed request/response models
   - Implemented deterministic detector (`en`, `es`, `he`, fallback `unknown`)
   - Wired into interview demo step `10/10`
4. Contract and docs updates
   - Expanded test suite to cover new functionality
   - Refreshed OpenAPI snapshot lock
   - Updated README and evidence/completion specs

### Validation run

Executed from repo root:

```bash
bash -n scripts/portal_api_validate.sh scripts/portal_api_interview_demo.sh
ruff check main.py portal_api modules scripts/portal_api_client_example.py scripts/portal_api_latency_sanity.py
python3 -m py_compile main.py portal_api/app.py portal_api/dependencies.py portal_api/models.py portal_api/routers/root.py portal_api/routers/vapi.py portal_api/routers/portal.py portal_api/routers/ghl.py portal_api/routers/admin.py portal_api/routers/language.py modules/inventory_manager.py modules/ghl_sync.py modules/appointment_manager.py modules/voice_trigger.py scripts/portal_api_client_example.py scripts/portal_api_latency_sanity.py
pytest -q -o addopts='' --confcutdir=portal_api/tests portal_api/tests
bash scripts/portal_api_interview_demo.sh
```

Observed results:

1. `ruff`: pass
2. `py_compile`: pass
3. `pytest`: `51 passed`
4. Demo script: `10/10` pass

### Interview-facing proof outputs

1. `[PASS] tenant_a and tenant_b are fully isolated`
2. `[PASS] p95 thresholds met`
3. `[PASS] multilingual readiness verified (en/es/he)`
4. `[PASS] interview demo flow completed (10/10)`

### Risk / mitigation

1. Risk: tenant scoping regressions in default flow
   - Mitigation: explicit `tenant_default` fallback + backward compatibility tests
2. Risk: noisy local environments affecting perf checks
   - Mitigation: configurable runs/timeout/thresholds with deterministic script behavior
3. Risk: language heuristic false positives on edge cases
   - Mitigation: explicit demo scope + typed `unknown` fallback
