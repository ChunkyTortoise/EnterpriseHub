# Jorge Test Evidence (2026-02-17)

## Environment
- Repo: `/Users/cave/Documents/GitHub/EnterpriseHub`
- Runner: local `pytest` with `pytest_asyncio`
- Date: 2026-02-17

## WS1 Tier A (Required)

1. `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
- Status: PASS
- Result: `3 passed`

2. `pytest -q -c /dev/null -p pytest_asyncio ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
- Status: PASS
- Result: `3 passed`

3. `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_entry_point.py`
- Status: PASS
- Result: `27 passed`

## WS1 Tier B (Required)

4. `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_bot_management_routes.py`
- Status: PASS
- Result: `16 passed`

5. `pytest -q -c /dev/null -p pytest_asyncio tests/api/test_lead_bot_management_routes.py`
- Status: PASS
- Result: `11 passed`

## WS1 Tier C (Optional Gate)

6. `pytest -q -c /dev/null -p pytest_asyncio -k "lead_bot or jorge_buyer_bot or jorge_seller_bot or lead_bot_management"`
- Status: NON-BLOCKING FAIL (collection phase)
- Failure class: unrelated repository-wide collection/import issues outside scoped Jorge paths.
- Examples:
  - `_archive/...` syntax/import errors
  - missing optional packages in other subprojects (`rag_service`, `pydantic_ai`, `supermemory`, `streamlit.testing`)
  - import-path mismatch in multi-project test trees

## WS2 Additional Regression Commands

7. `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_lead_bot_regressions.py`
- Status: PASS
- Result: `3 passed`

8. `pytest -q -c /dev/null -p pytest_asyncio tests/agents/test_buyer_response_generator_regressions.py`
- Status: PASS
- Result: `1 passed`

9. `pytest -q -c /dev/null -p pytest_asyncio tests/test_buyer_persona.py -k llm_persona_json_round_trip`
- Status: PASS
- Result: `1 passed`

10. `pytest -q -c /dev/null -p pytest_asyncio tests/test_churn_detection.py -k timezone_aware_last_activity`
- Status: PASS
- Result: `1 passed`

## WS3 Noise Cleanup Verification
Used writable cache path to remove `/dev` cache warnings in scoped sweeps:

- `pytest -q -c /dev/null -p pytest_asyncio -o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3 ghl_real_estate_ai/tests/test_jorge_buyer_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio -o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3 ghl_real_estate_ai/tests/test_jorge_seller_bot.py`
- `pytest -q -c /dev/null -p pytest_asyncio -o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3 tests/agents/test_lead_bot_entry_point.py`
- `pytest -q -c /dev/null -p pytest_asyncio -o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3 tests/api/test_bot_management_routes.py`
- `pytest -q -c /dev/null -p pytest_asyncio -o cache_dir=/Users/cave/Documents/GitHub/EnterpriseHub/.pytest_cache_ws3 tests/api/test_lead_bot_management_routes.py`

Observed in all five runs:
- `PytestCacheWarning`: `0`
- Unclosed connector/session errors: `0`

## Notes
- Deprecation and upstream library warnings remain in broader code paths; these are documented in risks and are not regressions introduced by this finalization pass.
