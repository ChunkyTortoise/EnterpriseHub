# Portal API Interview Completion Spec

Date: 2026-02-10  
Repository: `/Users/cave/Documents/New project/enterprisehub`  
Owner: Candidate  
Primary audience: Interview panel + technical reviewer

## 1) Objective

Complete and package the Portal API work so it is demonstrably production-minded for interview discussion: typed contracts, deterministic CI validation, documented behavior, and a clear live demo path.

## 2) Locked Baseline (Already Done)

- Phase 1 closure commit: `f7109b8d`
- Phase 2 CI/OpenAPI locking commit: `12d2863a`
- Current targeted validation status (local):
  - `ruff check main.py portal_api modules` passes
  - `python3 -m py_compile` portal/module set passes
  - `pytest -q -o addopts='' portal_api/tests/test_portal_api.py` passes (`24 passed`)
- Completion commits:
  - `5bc2455a` (contracts + docs + evidence)
  - `6bd4d7a7` (workflow dependency fix)
- Remote workflow confirmation:
  - `portal-api-phase1` run `21859818555` passed on 2026-02-10
- Critical route OpenAPI refs are now locked for:
  - `/`, `/health`, `/system/state`, `/system/state/details`, `/portal/swipe`, `/vapi/tools/book-tour`, `/ghl/sync`

## 3) Remaining Work To Complete Before Interview

## Priority P0 (Must Complete)

1. [x] Push latest commit and confirm CI green in GitHub.
2. [x] Add OpenAPI error contract for `POST /ghl/sync` 500 path and lock with test.
3. [x] Ensure interview branch is clean from unrelated edits (do not mix unrelated files in any final Portal API commit).
4. [x] Prepare evidence artifacts (commands + expected outputs + endpoint contract summary).

## Priority P1 (Strongly Recommended)

1. [x] Update README Portal API section with final route matrix and what is contract-locked.
2. [x] Add a short “demo run” block with exact command + curl/test flow.
3. [x] Rehearse a 5-minute deterministic demo covering success + validation failure path.

## Priority P2 (Optional if Time)

1. [x] Add explicit schema assertions for 422 validation response bindings on selected routes.
2. [x] Add one lightweight performance sanity check (single run timing note, not benchmark claims).

## 4) Detailed Implementation Plan

## Workstream A: CI + Branch Hygiene

### Tasks
- Push `12d2863a`.
- Verify workflow `.github/workflows/portal-api-phase1.yml` succeeds on remote.
- Keep unrelated local changes untouched:
  - `streamlit_cloud/app.py`
  - `tests/conftest.py`
  - `tests/test_app_structure.py`
  - `enterprise-ui/`
  - `plans/CLIENT_SHOWCASE_*`

### Acceptance Criteria
- Remote CI status is green for the portal workflow.
- No unrelated files staged/committed in Portal API completion commits.

## Workstream B: OpenAPI Error Contract Finalization

### Scope
- `POST /ghl/sync` can raise HTTP 500 on service exception; this must be represented in OpenAPI and tested.

### Target Files
- `/Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py`
- `/Users/cave/Documents/New project/enterprisehub/portal_api/models.py` (if adding explicit error model)
- `/Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py`

### Tasks
1. Add explicit response metadata for 500 on `/ghl/sync`.
2. If needed, define a small typed error schema (or consistently reference FastAPI validation/error structure).
3. Add OpenAPI test assertions verifying `500` response entry exists and schema/description binding is stable.
4. Keep runtime behavior unchanged.

### Acceptance Criteria
- OpenAPI includes deterministic 500 response documentation for `/ghl/sync`.
- Tests fail if this contract regresses.

## Workstream C: Documentation + Interview Packet

### Target Files
- `/Users/cave/Documents/New project/enterprisehub/README.md`
- `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_PHASE2_CI_OPENAPI_PROMPT_FEB10_2026.md` (reference only)
- `/Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_INTERVIEW_COMPLETION_SPEC_FEB10_2026.md` (this file)

### Tasks
1. Add a compact Portal API “Contract Guarantees” section:
   - typed request/response models
   - strict swipe action enum
   - `limit` bounds (`ge=0`, `le=100`, default `5`)
   - CI gate commands
2. Add a copy-paste demo sequence for interview use.
3. Add “Known limitation / next step” callout:
   - auth, real external integrations, observability depth

### Acceptance Criteria
- Reviewer can understand guarantees + demo without inspecting source.
- Candidate can speak clearly about what is locked vs intentionally not built.

## Workstream D: Demo Rehearsal and Evidence

### Demo Script (5 minutes)
1. `POST /system/reset`
2. `GET /portal/deck?contact_id=lead_001`
3. `POST /portal/swipe` with `action=like`
4. `POST /vapi/tools/book-tour`
5. `GET /system/state`
6. `GET /system/state/details?limit=2`
7. Negative-path proof: invalid swipe action (`save`) returns 422

### Evidence Bundle
- Latest commit hashes (`f7109b8d`, `12d2863a`, plus final cleanup commit)
- Test count and pass output
- OpenAPI contract assertions summary
- One-slide narrative:
  - Problem
  - Design choices
  - Deterministic quality gate
  - Remaining tradeoffs

### Acceptance Criteria
- Demo runs end-to-end with deterministic outputs.
- Candidate can explain each endpoint’s contract and failure behavior.

## 5) Validation Commands (Final Gate)

```bash
cd /Users/cave/Documents/New\ project/enterprisehub

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

## 6) Interview Talking Points (Concise)

1. Why typed contracts were introduced (predictability + generated docs + safer client integration).
2. Why CI is intentionally scoped (fast deterministic gate on high-value files).
3. How OpenAPI regression locking prevents silent contract drift.
4. Tradeoffs accepted (in-memory demo services, simplified auth/integration boundaries).
5. Next production steps (auth, persistence hardening, real provider fault isolation, telemetry).

## 7) Risks and Mitigations

- Risk: Unrelated local changes contaminate final commit.
  - Mitigation: stage explicit file list only.
- Risk: OpenAPI docs diverge from runtime edge-case behavior.
  - Mitigation: contract tests on critical success + failure schemas.
- Risk: Demo fails due to environment drift.
  - Mitigation: deterministic reset-first flow and exact command list.

## 8) Definition of Done

All of the following are true:

1. Remote CI is green for Portal API workflow after latest changes.
2. OpenAPI includes and tests 500-path contract for `/ghl/sync`.
3. Validation commands pass locally without touching unrelated work.
4. README includes contract guarantees + interview demo flow.
5. Candidate can run the 5-minute script and explain contract/failure guarantees clearly.
