# Jorge Bots Finalization File Index (2026-02-17)

## A) Core Code Files (Primary Scope)
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/lead_bot.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/lead/workflow_nodes_enhanced.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/jorge_buyer_bot.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/jorge_seller_bot.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/agents/buyer/response_generator.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/buyer_persona_service.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/churn_detection_service.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/api/routes/lead_bot_management.py`

## B) Test Files (Add/Update)
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/tests/agents/test_lead_bot_entry_point.py`
- `/Users/cave/Documents/GitHub/EnterpriseHub/tests/api/test_bot_management_routes.py`
- Additional targeted tests under:
  - `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/`
  - `/Users/cave/Documents/GitHub/EnterpriseHub/tests/`

## C) Finalization/Handoff Docs (This Package)
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_BOTS_FINALIZATION_2026-02-17_SPEC.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_BOTS_FINALIZATION_2026-02-17_PROMPT.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_BOTS_FINALIZATION_2026-02-17_FILE_INDEX.md`

## D) Jorge Delivery Docs To Produce
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_DELIVERY_SUMMARY.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_TEST_EVIDENCE.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_CHANGE_MAP.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_RISKS_AND_FOLLOWUPS.md`
- `/Users/cave/Documents/GitHub/EnterpriseHub/docs/handoffs/JORGE_ROLLBACK_AND_VERIFY.md`

## E) Suggested Evidence Commands
- `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_entry_point.py`
- `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_bot_management_routes.py`

## F) Stage Only Relevant Files
Before commit, verify with:
- `git status --short`
- `git diff --name-only --cached`

Do not include unrelated modified files already present in the repo worktree.
