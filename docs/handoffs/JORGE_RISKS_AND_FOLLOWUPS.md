# Jorge Risks and Follow-ups (2026-02-17)

## Risk Register

1. **Tier C repository-wide collection noise (Non-blocking)**
- Severity: Medium
- Scope: unrelated `_archive/` and external subproject test trees.
- Impact: broad `pytest -k ...` collection fails before execution in non-Jorge areas.
- Mitigation: use scoped test targets for deployment gating; keep Tier A/B + dedicated regressions as hard gate.

2. **Staging validation not executed in this workspace**
- Severity: Medium
- Scope: WS5 runtime validation in staging-like environment.
- Impact: no live environment confirmation for webhook, scheduler, and bot-to-bot runtime edges.
- Mitigation: run the staging checklist in `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_ROLLBACK_AND_VERIFY.md` before production promotion.

3. **Deprecation warning backlog in wider codebase**
- Severity: Low
- Scope: `datetime.utcnow()`, library deprecations, FastAPI startup event deprecations, etc.
- Impact: warning noise; future-runtime upgrade risk.
- Mitigation: schedule dedicated warning-reduction cleanup outside this stabilization patch.

## Follow-up Actions

1. Create a scoped CI job for Jorge bots only:
- Target paths:
  - `ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
  - `ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
  - `tests/agents/test_lead_bot_entry_point.py`
  - `tests/agents/test_lead_bot_regressions.py`
  - `tests/api/test_bot_management_routes.py`
  - `tests/api/test_lead_bot_management_routes.py`

2. Add staging smoke automation (pre-deploy gate):
- lead handoff to buyer/seller,
- buyer/seller tagging verification,
- lead sequence pause/resume/cancel endpoint checks,
- rollback dry-run.

3. Isolate or quarantine legacy archived tests:
- exclude `_archive/` from default top-level test collection,
- move historical suites behind explicit opt-in markers/paths.

4. Plan deprecation cleanup sprint:
- replace `datetime.utcnow()` in touched/high-frequency paths,
- reduce noisy warnings in core CI lanes.
