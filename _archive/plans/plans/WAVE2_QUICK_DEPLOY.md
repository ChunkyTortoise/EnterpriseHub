# Wave 2: Quick Deploy Reference

## Copy-Paste Agent Prompt

```
Fix critical Portal API bug where high-intent lead detection is blocked by GHL API failures.

MISSION: Refactor _process_like() method to run high-intent detection BEFORE GHL API calls.

FILES TO MODIFY:
1. /Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/portal_swipe_manager.py
   - Lines 148-194: Reorder logic (high-intent FIRST, GHL SECOND with nested try/except)
   - Lines 367, 384: Fix datetime.utcnow() → datetime.now(datetime.UTC)

2. /Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_swipe.py
   - Add mock_ghl_client fixture after line 42
   - Inject mock into swipe_manager fixture

3. /Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_api.py
   - Add mock_ghl_for_api_tests fixture
   - Patch EnhancedGHLClient constructor

VERIFICATION:
```bash
source .venv/bin/activate
pytest ghl_real_estate_ai/tests/test_portal_swipe.py::test_high_intent_detection -v
pytest ghl_real_estate_ai/tests/test_portal_api.py::test_high_intent_detection_via_api -v
```

SUCCESS CRITERIA:
- Both high_intent_detection tests PASS
- No real GHL API calls in test logs
- high_intent=True when 3+ likes detected
- GHL failures don't prevent high-intent flag from being set

DETAILED SPEC: See /Users/cave/Documents/GitHub/EnterpriseHub/plans/WAVE2_PORTAL_API_FIX_PROMPT.md
```

## Agent Deployment Command

```python
Task(
    subagent_type="general-purpose",
    description="Fix Portal API high-intent bug",
    model="opus",
    prompt="""See /Users/cave/Documents/GitHub/EnterpriseHub/plans/WAVE2_PORTAL_API_FIX_PROMPT.md for complete instructions."""
)
```

## Key File Paths

### To Modify
- `ghl_real_estate_ai/services/portal_swipe_manager.py`
- `ghl_real_estate_ai/tests/test_portal_swipe.py`
- `ghl_real_estate_ai/tests/test_portal_api.py`

### To Read (Context)
- `ghl_real_estate_ai/services/enhanced_ghl_client.py`
- `ghl_real_estate_ai/api/routes/portal.py`

## Bead
- **ID**: EnterpriseHub-qu7
- **Priority**: P0
- **Status**: Open (ready for fix)

## Test Commands

### Quick Test (2 failing tests)
```bash
source .venv/bin/activate
pytest ghl_real_estate_ai/tests/test_portal_api.py::test_high_intent_detection_via_api \
       ghl_real_estate_ai/tests/test_portal_swipe.py::test_high_intent_detection \
       -v --tb=short
```

### Full Portal Tests
```bash
pytest ghl_real_estate_ai/tests/test_portal_api.py ghl_real_estate_ai/tests/test_portal_swipe.py -v
```

## Expected Timeline
- **Agent work**: 30-45 minutes
- **Testing**: 10 minutes
- **Total**: ~1 hour
