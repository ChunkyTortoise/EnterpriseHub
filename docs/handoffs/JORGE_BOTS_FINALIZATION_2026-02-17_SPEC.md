# Jorge Bots Finalization Spec (2026-02-17)

## 1) Objective
Complete and finalize the Jorge bot stabilization effort so it can be handed to Jorge with full implementation evidence, regression safety, and deployment readiness.

This spec covers the four requested tracks:
1. Broader regression sweep.
2. Add/strengthen regression tests for each fix.
3. Clean up remaining test/runtime noise.
4. Prepare clean commit/PR package.

And adds finalization items required for a production-ready Jorge handoff.

## 2) Current Baseline
The following fixes are already implemented in code and validated with focused tests/smokes:
- Lead bot handoff crash fix and enhanced graph handoff routing.
- Lead bot phone/email key compatibility (`lead_*` + `contact_*`).
- Buyer intelligence middleware API alignment (`enhance_bot_context`).
- Buyer/seller auto-tagging API alignment (`apply_auto_tags`).
- Seller budget extraction correction (`under 500` -> `500000`).
- Buyer response sentiment API fix (`analyze_sentiment`).
- Buyer persona `json` import fix.
- Churn timezone-aware datetime fix.
- Lead sequence management API schema + tuple return handling fix.
- Buyer test harness compatibility fix for patched event publisher resolution.

## 3) Scope And Deliverables

### 3.1 Technical Deliverables
- All bot and related API tests passing at agreed confidence level.
- New regression tests for each bug fixed.
- Reduced non-actionable warning/error noise in test runs.
- Clean commit set that includes only Jorge-related bot finalization changes.

### 3.2 Handoff Deliverables For Jorge
- Execution summary (what changed, why, risk).
- Test evidence summary (commands + pass/fail + warnings).
- Known non-blockers and follow-up tickets.
- File-level change map.
- Rollback and verification instructions.

## 4) Workstream Plan

### WS1: Broader Regression Sweep
Run tests in this order and capture outputs.

#### Tier A: Bot Core
- `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_entry_point.py`

#### Tier B: Integration/Routes Around Changes
- `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_bot_management_routes.py`
- Add and run dedicated tests for `lead_bot_management` route behavior (see WS2).

#### Tier C: Optional Full Bot Suite Gate
- `pytest -q -c /dev/null -p pytest_asyncio -k "lead_bot or jorge_buyer_bot or jorge_seller_bot or lead_bot_management"`

#### Exit Criteria WS1
- No failing tests in Tier A/B.
- Tier C either passes or has documented non-blocking unrelated failures.

### WS2: Regression Test Hardening
Add explicit tests for every fixed issue.

#### Required Test Cases
1. Lead handoff node no longer crashes:
- Path: `ghl_real_estate_ai/agents/lead_bot.py`
- Assert: no `NameError`, handoff event recorded.

2. Lead phone/email fallback compatibility:
- Assert Day 3/7/14/30 nodes work with only `lead_phone`/`lead_email` present.

3. Enhanced graph includes handoff check:
- Assert compiled enhanced graph contains `check_handoff_signals` and routes via conditional short-circuit.

4. Buyer intelligence middleware call signature:
- Assert bot calls `enhance_bot_context` with expected args.

5. Buyer/seller workflow tagging API:
- Assert `apply_auto_tags` called from both bots.

6. Buyer persona service JSON usage:
- Add unit that exercises JSON cache serialize/deserialize path.

7. Buyer response sentiment API:
- Assert `analyze_sentiment` invoked and response generation succeeds.

8. Churn timezone safety:
- Assert aware datetime input does not raise and computes inactivity correctly.

9. Lead bot management route schema/tuple handling:
- Assert `create_sequence` uses service contract (`create_sequence`, `sequence_status`, `sequence_started_at`).
- Assert pause/resume/cancel map tuple outcomes to proper HTTP codes.

10. Seller budget parser fix:
- Assert phrase `under 500` maps to `500000`.

#### Exit Criteria WS2
- All added tests green.
- Each bug fixed has at least one direct regression test.

### WS3: Test/Runtime Noise Cleanup
Focus on warnings/errors that reduce signal quality.

#### Priority Fixes
1. Unclosed `aiohttp` connectors in tests:
- Ensure clients are explicitly closed in teardown or fixture finalizers.

2. `datetime.utcnow()` deprecation:
- Replace with timezone-aware usage in touched/critical paths.

3. Pytest cache warnings from `/dev/null` config usage:
- Use a writable temp config/cache dir when running CI-quality sweeps.

4. Known upstream/library warnings:
- Document as non-blockers if outside project control.

#### Exit Criteria WS3
- No unclosed connector errors in targeted test runs.
- Deprecation noise reduced in changed paths.
- Remaining warnings categorized and documented.

### WS4: Commit And PR Finalization
Create a clean, reviewable submission.

#### Steps
1. Stage only relevant files (exclude unrelated dirty worktree files).
2. Commit in logical chunks:
- `fix(jorge-bots): stabilize lead/buyer/seller integration paths`
- `test(jorge-bots): add regression coverage for stabilization fixes`
- `chore(test): reduce runtime noise in bot test harness`
3. Generate PR description:
- Problem summary
- Fix map
- Test evidence
- Risk/rollback

#### Exit Criteria WS4
- No unrelated files staged.
- PR description includes reproducible validation commands.

## 5) Additional Finalization Needed Before Sending To Jorge

### WS5: Staging/Runtime Validation
- Execute bot smoke flows in a staging-like environment.
- Validate key runtime paths:
  - Lead handoff to buyer/seller.
  - Buyer qualification and tagging.
  - Seller qualification and tagging.
  - Lead sequence pause/resume/cancel API behavior.

### WS6: Jorge Delivery Package
Prepare these artifacts:
- `JORGE_DELIVERY_SUMMARY.md` (executive summary).
- `JORGE_TEST_EVIDENCE.md` (commands and outcomes).
- `JORGE_CHANGE_MAP.md` (file-by-file rationale).
- `JORGE_RISKS_AND_FOLLOWUPS.md` (open items and severity).
- `JORGE_ROLLBACK_AND_VERIFY.md` (rollback + post-deploy checks).

## 6) Definition Of Done
All items below must be true:
- WS1 through WS4 complete.
- WS5 smoke validation complete or explicitly waived with reason.
- WS6 handoff package complete and internally reviewed.
- All critical fixes backed by regression tests.
- No known P0/P1 unresolved defects in changed areas.

## 7) Constraints
- Do not revert unrelated pre-existing changes in the worktree.
- Keep changes scoped to Jorge bot finalization unless explicitly approved.
- Prefer minimal, high-confidence fixes with explicit test coverage.

## 8) Recommended Execution Order
1. WS2 (close test gaps while context is fresh).
2. WS1 (run broader sweep with new tests).
3. WS3 (cleanup warnings/noise).
4. WS4 (clean commit/PR).
5. WS5 and WS6 (final staging + handoff package).

## 9) Current High-Value Files In Scope
- `ghl_real_estate_ai/agents/lead_bot.py`
- `ghl_real_estate_ai/agents/lead/workflow_nodes_enhanced.py`
- `ghl_real_estate_ai/agents/jorge_buyer_bot.py`
- `ghl_real_estate_ai/agents/jorge_seller_bot.py`
- `ghl_real_estate_ai/agents/buyer/response_generator.py`
- `ghl_real_estate_ai/services/buyer_persona_service.py`
- `ghl_real_estate_ai/services/churn_detection_service.py`
- `ghl_real_estate_ai/api/routes/lead_bot_management.py`
- Related tests under `ghl_real_estate_ai/tests/` and `tests/`.

## 10) Handoff Acceptance Checklist (For Jorge)
- [ ] Technical summary reviewed.
- [ ] Regression evidence reviewed.
- [ ] Known risks understood.
- [ ] Rollback plan accepted.
- [ ] Deployment gate approved.
