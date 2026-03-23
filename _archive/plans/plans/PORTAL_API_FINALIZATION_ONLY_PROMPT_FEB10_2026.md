Use this in a new chat.

```text
FINALIZATION-ONLY RUN (ONE PASS, NO PARTIAL STOP)

Repository:
/Users/cave/Documents/New project/enterprisehub

Primary execution spec:
- /Users/cave/Documents/New project/enterprisehub/plans/PORTAL_API_COMPREHENSIVE_EVAL_AND_COMPLETION_SPEC_FEB10_2026.md

You must close Portal API Phase 1 in this single run. Do not stop after planning or partial edits.

Hard requirements:
1) Implement remaining contract typing closure across root/admin/related routers.
2) Expand tests to include failure paths and state/details consistency assertions.
3) Keep CI workflow naming/path references consistent with phase1 (`portal-api-phase1.yml`).
4) Update README Portal API section to match the final endpoint + alias matrix and validation bundle.
5) Run all required validation commands and report exact results.

Execution constraints:
- Keep unrelated local changes intact; do not revert unrelated files.
- Preserve existing API behavior/compatibility unless explicitly tightening contracts.
- If you find a mismatch between docs/code/tests/workflow, resolve it now (not as follow-up).
- Treat this as completion/finalization, not analysis.

Mandatory completion targets:
- Root endpoint has explicit response model.
- No remaining ad-hoc raw Dict response signatures where typed models are expected.
- Failure-path tests include:
  - service exception path (GHL -> HTTP 500),
  - malformed string arguments path (Vapi parse fallback),
  - invalid limit validation path for state details.
- State aggregation parity test:
  - /system/state counters align with /system/state/details aggregate summaries.
- Workflow file is phase1-consistent in filename and trigger scope.
- README includes final endpoint list, aliases, and exact validation commands.

Required files to inspect/update as needed:
- /Users/cave/Documents/New project/enterprisehub/main.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/app.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/dependencies.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/models.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/root.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/admin.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/portal.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/vapi.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/routers/ghl.py
- /Users/cave/Documents/New project/enterprisehub/modules/inventory_manager.py
- /Users/cave/Documents/New project/enterprisehub/modules/ghl_sync.py
- /Users/cave/Documents/New project/enterprisehub/modules/appointment_manager.py
- /Users/cave/Documents/New project/enterprisehub/modules/voice_trigger.py
- /Users/cave/Documents/New project/enterprisehub/portal_api/tests/test_portal_api.py
- /Users/cave/Documents/New project/enterprisehub/.github/workflows/portal-api-phase1.yml
- /Users/cave/Documents/New project/enterprisehub/README.md

Required end-of-run validation commands:

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

Completion gate:
- Do not claim done unless all three validation commands pass.
- If any command fails, fix and re-run until green within this run.

Required final response format:
1) What you changed
2) Files touched
3) Validation results (exact command outputs summarized with pass counts)
4) Remaining risks (if any)
5) Next 3 actions
```
