# Portal API Interview Evidence Bundle

Date: 2026-02-10
Repository: `/Users/cave/Documents/New project/enterprisehub`

## 1) Baseline and Completion Commits

- Phase 1 closure baseline: `f7109b8d`
- Phase 2 CI/OpenAPI baseline: `12d2863a`
- Interview completion commit: `TO_BE_FILLED_AFTER_COMMIT`

## 2) Final Validation Commands and Observed Results

Run from repo root:

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

Observed output summary:

- `ruff`: `All checks passed!`
- `py_compile`: no errors
- `pytest`: `24 passed in 0.56s`

## 3) Endpoint Contract Summary (Locked by Tests)

- `GET /` -> `RootResponse` (`200`)
- `GET /health` -> `HealthResponse` (`200`)
- `GET /system/state` -> `StateResponse` (`200`)
- `GET /system/state/details` -> `DetailedStateResponse` (`200`)
- `POST /portal/swipe` -> `SwipeResponse` (`200`), validation contract (`422` -> `HTTPValidationError`)
- `POST /vapi/tools/book-tour` -> `VapiToolResponse` (`200`)
- `POST /ghl/sync` -> `GHLSyncResponse` (`200`), service-failure contract (`500` -> `ErrorResponse`)

Additional locked constraints:

- `Interaction.action` enum is exactly `like | pass`
- `/system/state/details?limit` has `minimum=0`, `maximum=100`, default `5`

## 4) Negative-Path Proofs

- Invalid swipe action (`save`) returns `422`
- Invalid `limit` query values (`-1`, `101`, `abc`) return `422`
- Forced service exception in `/ghl/sync` returns `500` with error detail

## 5) Lightweight Performance Sanity Note (Single Local Run)

Command summary:

- Reset state
- Time one `GET /health`
- Execute swipe + booking
- Time one `GET /system/state/details?limit=2`

Observed sample timing (local, single run, non-benchmark):

- `health_ms=1.69`
- `state_details_ms=0.66`
- `state_details_status=200`

## 6) Interview Demo Script (Deterministic)

Use the README block under `Portal API (Phase 1)` -> `Interview Demo Run (5 minutes)`.

## 7) Remaining Production Tradeoffs to Call Out

- Auth/authz not fully implemented for this demo slice
- External integrations are simulated/simplified in some flows
- Observability depth is intentionally minimal for interview scope
