Use this in a new chat.

```text
Portal API Phase 2: CI + OpenAPI Regression Locking (only)

Repository:
/Users/cave/Documents/New project/enterprisehub

Current baseline (already complete):
- Portal API Phase 1 contracts are typed and validated.
- Workflow file is: .github/workflows/portal-api-phase1.yml
- Targeted validation currently passes:
  - ruff check main.py portal_api modules
  - python3 -m py_compile (portal API/module set)
  - pytest -q -o addopts='' portal_api/tests/test_portal_api.py (21 passed)

Scope constraints (strict):
1) Work only on CI hardening + OpenAPI regression locking.
2) Do not change runtime endpoint behavior unless required to stabilize deterministic contracts.
3) Keep unrelated local changes intact.

Required implementation targets:
1) Add robust OpenAPI contract tests for critical routes:
   - `/`, `/health`, `/system/state`, `/system/state/details`, `/portal/swipe`, `/vapi/tools/book-tour`, `/ghl/sync`
   - verify response model refs and key request schema constraints
2) Add schema-level assertions for critical validation rules:
   - `Interaction.action` enum includes only `like` and `pass`
   - `/system/state/details` `limit` query bounds stay `ge=0`, `le=100`, default `5`
3) Harden CI workflow gate:
   - ensure `portal-api-phase1.yml` runs lint + compile + targeted tests deterministically
   - optionally add explicit test environment defaults if needed for stability
4) Keep tests non-brittle:
   - assert stable contract invariants, avoid over-coupling to ordering/noisy metadata

Primary files to inspect:
- /Users/cave/Documents/New project/enterprisehub/.github/workflows/portal-api-phase1.yml
- /Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/models.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/root.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/admin.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/portal.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/vapi.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py
- /Users/cave/Documents/New project/enterprisehub/README.md

Required validation commands:

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

Output format:
1) What you changed
2) Files touched
3) Validation results
4) Residual risks
5) Next 3 actions
```
