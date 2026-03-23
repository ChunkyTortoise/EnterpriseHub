# Portal API Comprehensive Evaluation + Completion Spec

Date: 2026-02-10  
Repo: `/Users/cave/Documents/New project/enterprisehub`  
Scope: `main.py`, `portal_api/**`, `modules/**`, `.github/workflows/portal-api-phase1.yml`

## 1) Objective

Complete the remaining Portal API development work with a full quality evaluation, production-readiness hardening, and deterministic validation evidence.

## 2) Current Confirmed Baseline

- Modular API is active under `/portal_api` with entrypoint `/main.py`.
- Root (`/`) and health (`/health`) endpoints have explicit response models.
- Reset endpoint aliases are active: `POST /system/reset`, `POST /admin/reset`, `POST /reset`.
- State endpoint aliases are active: `GET /system/state`, `GET /admin/state`, `GET /state`.
- Detailed state endpoint aliases are active: `GET /system/state/details`, `GET /admin/state/details`, `GET /state/details`.
- Swipe action validation is typed to `Literal["like", "pass"]`.
- Outbound call usage is dependency-injected through services.
- Response models are present for portal, vapi, ghl, admin, root, and health endpoints.
- Vapi request payloads are typed and support both JSON object and JSON-string `arguments`.
- Failure-path coverage includes GHL service exception handling and malformed Vapi argument fallback.
- OpenAPI contract checks cover root/health/state-details response-model bindings and `limit` parameter bounds.
- Current targeted validation is green:
  - `ruff check main.py portal_api modules`
  - `python3 -m py_compile` on portal API/module file set
  - `pytest -q -o addopts='' portal_api/tests/test_portal_api.py` (21 passed)

## 3) Remaining Gaps

- No mandatory Phase 1 gaps remain based on current validation and contract checks.
- Optional next-step hardening: add OpenAPI schema assertions to lock response-model contracts in CI.

## 4) Evaluation Framework (Must Pass)

## A. API Contract Integrity

- Every endpoint has explicit request/response models where applicable.
- Alias endpoints return byte-for-byte equivalent payloads for same logical resource.
- Query/path/body validation failures return deterministic `422` or documented `4xx`/`5xx`.
- No route leaks untyped ad-hoc response shapes.

## B. Behavior Correctness

- `/portal/swipe` `action="like"` triggers expected high-intent + GHL action path.
- `/portal/swipe` `action="pass"` increments interaction count without GHL side effects.
- `/vapi/tools/book-tour` preserves required-field failures with stable message contract.
- `/system/reset` reliably clears interaction/action/booking counters and recents.

## C. State/Observability Consistency

- `/system/state` aggregate counters remain consistent with `/system/state/details` sub-counts.
- `limit` semantics for details endpoint are validated:
  - `limit=0` returns empty recents while preserving counts.
  - invalid limits reject with `422`.
  - upper-bound behavior is deterministic (`le=100`).

## D. Failure-Path Robustness

- GHL router error handling is validated (service exception -> HTTP 500).
- Vapi payload parse fallback remains stable for malformed string arguments.
- Missing optional payload sections do not crash routes.

## E. CI/Quality Gate Reliability

- Workflow name/path consistency fixed for Phase 1.
- Lint, compile, and targeted tests are the mandatory gate.
- Optional expanded tests can run locally without affecting deterministic minimum gate.

## 5) Implementation Plan (Execution Order)

## Phase A: Contract Finalization

- Add root response model and bind it to `/`.
- Convert remaining raw `Dict[str, Any]` route signatures to typed response classes.
- Keep payload compatibility unchanged unless an improvement is explicitly documented.

## Phase B: Deep Test Expansion

- Add cross-check test: `/system/state` counts must equal summarized `/system/state/details`.
- Add GHL failure-path test using dependency override or monkeypatch.
- Add malformed Vapi argument string test to confirm graceful parse fallback.
- Add route-schema assertions where useful (minimal, non-brittle).

## Phase C: CI + Workflow Coherency

- Rename workflow file to `portal-api-phase1.yml`.
- Update workflow trigger paths to reference the new filename.
- Keep commands identical unless adding proven-safe checks.

## Phase D: Docs + Handoff Readiness

- Update README portal API section with current endpoint matrix and alias map.
- Record exact validation command bundle and expected passing output.
- Produce handoff prompt for fresh-chat continuation.

## 6) Required File Targets

- `/Users/cave/Documents/New project/enterprisehub/main.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/app.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/dependencies.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/models.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/root.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/admin.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/portal.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/vapi.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py`
- `/Users/cave/Documents/New project/enterprisehub/modules/inventory_manager.py`
- `/Users/cave/Documents/New project/enterprisehub/modules/ghl_sync.py`
- `/Users/cave/Documents/New project/enterprisehub/modules/appointment_manager.py`
- `/Users/cave/Documents/New project/enterprisehub/modules/voice_trigger.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`
- `/Users/cave/Documents/New project/enterprisehub/.github/workflows/portal-api-phase1.yml`
- `/Users/cave/Documents/New project/enterprisehub/README.md`

## 7) Validation Commands (Required End-of-Run)

```bash
ruff check main.py portal_api modules

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
  modules/inventory_manager.py \
  modules/ghl_sync.py \
  modules/appointment_manager.py \
  modules/voice_trigger.py

pytest -q -o addopts='' portal_api/tests/test_portal_api.py
```

## 8) Completion Criteria

- All endpoint contracts are explicit and typed.
- Targeted tests cover contract, behavior, alias parity, and key failure paths.
- Validation commands pass with exact reported status.
- Workflow naming/path consistency is corrected for Phase 1.
- Handoff prompt and file list are updated and ready for immediate continuation.

## 9) Output Format For Continuation Runs

1. What you changed  
2. Files touched  
3. Validation results  
4. Next 3 actions

## 10) Guardrails

- Keep existing local changes; do not revert unrelated files.
- Continue with concrete implementation + tests (no planning-only response).
- Preserve API compatibility unless explicitly improving contracts.
- Report exact pass/fail from final validation commands.
