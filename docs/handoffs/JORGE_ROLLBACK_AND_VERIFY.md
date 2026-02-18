# Jorge Rollback and Verify (2026-02-17)

## Pre-Deploy Verification (Local)
Run from `/Users/cave/Documents/GitHub/EnterpriseHub`:

1. `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
2. `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
3. `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_entry_point.py`
4. `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_regressions.py`
5. `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_bot_management_routes.py`
6. `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_lead_bot_management_routes.py`

Optional low-noise run mode:
- Append `-o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3` to suppress `/dev` cache warnings.

## Staging Runtime Verification (WS5)

Use a staging URL and auth token.

1. Create sequence:
```bash
curl -X POST "$STAGING_URL/api/lead-bot/sequences" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"lead_id":"staging-lead-1","lead_name":"Stage Lead","phone":"+15555550123","email":"stage@example.com","start_delay_minutes":0}'
```

2. Check status mapping fields:
```bash
curl -H "Authorization: Bearer $TOKEN" "$STAGING_URL/api/lead-bot/sequences/staging-lead-1"
```
Expect:
- `status` from `sequence_status`
- `sequence_started_at` populated

3. Pause/resume/cancel tuple mapping:
```bash
curl -X POST -H "Authorization: Bearer $TOKEN" "$STAGING_URL/api/lead-bot/sequences/staging-lead-1/pause"
curl -X POST -H "Authorization: Bearer $TOKEN" "$STAGING_URL/api/lead-bot/sequences/staging-lead-1/resume"
curl -X POST -H "Authorization: Bearer $TOKEN" "$STAGING_URL/api/lead-bot/sequences/staging-lead-1/cancel"
```
Expect proper 200/404/400 behavior by scenario.

4. Lead handoff smoke:
- Send buyer-intent and seller-intent messages through lead bot path.
- Verify handoff signals and status events are emitted.

5. Tagging smoke:
- Run one buyer and one seller conversation.
- Confirm `apply_auto_tags` outcomes in CRM tags/custom fields.

## Rollback Plan

### If committed and deployed
1. Identify deployed commit(s) for Jorge finalization.
2. Revert in reverse order:
```bash
git revert <newest_commit_hash>
git revert <older_commit_hash>
```
3. Redeploy reverted build.
4. Re-run Pre-Deploy Verification commands against reverted state.

### If changes are uncommitted local-only
- Reset by restoring only Jorge-scoped files from the previous known-good branch point.
- Do not touch unrelated dirty worktree files.

## Post-Rollback Checks

1. Re-run sequence API checks (`create/status/pause/resume/cancel`).
2. Re-run lead handoff smoke.
3. Re-run buyer/seller tagging smoke.
4. Confirm no increase in error logs for lead, buyer, seller bots.
