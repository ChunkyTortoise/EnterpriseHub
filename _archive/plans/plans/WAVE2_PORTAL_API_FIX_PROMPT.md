# Wave 2: Portal API Fix - Agent Deployment Prompt

## Agent 4: Portal API Logic Refactor Specialist

**Bead**: EnterpriseHub-qu7
**Priority**: P0 (CRITICAL - Production Bug)
**Model**: Opus (complex refactoring)
**Estimated Time**: 45 minutes

---

## Mission

Fix critical production bug where high-intent lead detection is blocked by GHL API failures. The `_process_like()` method exits early when GHL authentication fails, preventing high-intent detection logic from executing.

---

## Context

### Current Behavior (BROKEN)
```
handle_swipe() → _process_like()
  ↓
try:
    await ghl_client.add_tags()  [FAILS with 401]
    ↓
except Exception:
    return result  [high_intent still False - NEVER REACHED DETECTION LOGIC]
```

### Expected Behavior (FIXED)
```
handle_swipe() → _process_like()
  ↓
1. Count recent likes (local, no API)
2. Detect high-intent (local logic)
3. Update memory (local)
4. Try GHL tagging (can fail gracefully)
```

### Evidence
- Test: `test_high_intent_detection` - Expects `high_intent=True` after 3 likes
- Actual: Returns `high_intent=False` due to early exit on GHL 401
- Logs: "Error processing like: Client error '401 Unauthorized'"
- Impact: High-value leads not flagged for immediate follow-up

---

## Files to Modify

### Primary Target
**File**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/portal_swipe_manager.py`
- **Lines 148-194**: `_process_like()` method - REFACTOR REQUIRED
- **Lines 367, 384**: Replace `datetime.utcnow()` with `datetime.now(datetime.UTC)`

### Test Files (Add Mocking)
**File 1**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_swipe.py`
- **Lines 38-42**: Add `mock_ghl_client` fixture
- **Target tests**: `test_high_intent_detection` (lines 69-96)

**File 2**: `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_api.py`
- Add GHL client mocking at module/fixture level
- **Target test**: `test_high_intent_detection_via_api` (lines 196-222)

---

## Implementation Steps

### Step 1: Refactor `_process_like()` Method

**Current Code** (lines 148-194):
```python
async def _process_like(self, lead_id: str, property_id: str, location_id: str) -> Dict[str, Any]:
    result = {"status": "logged", "trigger_sms": False, "high_intent": False}

    try:
        # This runs FIRST and can fail, blocking everything below
        await self.ghl_client.add_tags(lead_id, tags)

        # This NEVER RUNS if GHL fails
        recent_likes = self._count_recent_likes(lead_id, minutes=10)
        if recent_likes >= 3:
            result["high_intent"] = True
            # ... detection logic ...

    except Exception as e:
        logger.error(f"Error processing like: {e}")
        return result  # EARLY EXIT

    return result
```

**New Code** (REORDERED):
```python
async def _process_like(self, lead_id: str, property_id: str, location_id: str) -> Dict[str, Any]:
    """Process a 'like' action with high-intent detection BEFORE GHL API calls."""
    result = {"status": "logged", "trigger_sms": False, "high_intent": False}

    try:
        # STEP 1: Count recent likes (local operation, no external dependencies)
        recent_likes = self._count_recent_likes(lead_id, minutes=10)
        logger.info(f"Lead {lead_id} has {recent_likes} likes in last 10 minutes")

        # STEP 2: Detect high-intent behavior FIRST (before any API calls)
        if recent_likes >= 3:
            result["high_intent"] = True
            result["trigger_sms"] = True
            result["message"] = f"High intent detected: {recent_likes} likes in 10 minutes"
            logger.warning(f"⚡ HIGH INTENT DETECTED for {lead_id} - {recent_likes} likes")

        # STEP 3: Update memory (local operation)
        await self._update_liked_properties(lead_id, location_id, property_id)

        # STEP 4: Try GHL API calls (can fail without breaking high-intent flag)
        try:
            tags = ["portal_liked_property", "hot_lead"]
            if result["high_intent"]:
                tags.extend(["super_hot_lead", "immediate_followup"])

            await self.ghl_client.add_tags(lead_id, tags)
            logger.info(f"✅ Successfully tagged lead {lead_id} in GHL with {tags}")
            result["ghl_tagged"] = True

        except Exception as ghl_error:
            # Log but don't fail - high-intent flag already set
            logger.error(f"Failed to tag lead {lead_id} in GHL: {ghl_error}")
            result["ghl_tagged"] = False
            result["ghl_error"] = str(ghl_error)
            # Continue execution - high-intent detection already complete

    except Exception as e:
        logger.error(f"Error processing like: {e}")
        result["error"] = str(e)

    return result
```

**Key Changes**:
1. ✅ High-intent detection runs FIRST (lines after "STEP 2")
2. ✅ GHL calls wrapped in nested try/except (lines after "STEP 4")
3. ✅ Errors in GHL don't affect high-intent flag
4. ✅ Added `ghl_tagged` and `ghl_error` keys for debugging

### Step 2: Fix Deprecated Datetime Usage

**Line 367**:
```python
# FROM:
"timestamp": datetime.utcnow().isoformat()

# TO:
"timestamp": datetime.now(datetime.UTC).isoformat()
```

**Line 384**:
```python
# FROM:
cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

# TO:
cutoff_time = datetime.now(datetime.UTC) - timedelta(minutes=minutes)
```

**Add import if needed** (check top of file):
```python
from datetime import datetime, timedelta  # Ensure datetime is imported
```

### Step 3: Add GHL Client Mocking - test_portal_swipe.py

**Add after line 42**:
```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_ghl_client():
    """Mock GHL client to avoid real API calls in tests."""
    mock = Mock()
    mock.add_tags = AsyncMock(return_value={"status": "success"})
    return mock

@pytest.fixture
def swipe_manager(temp_interactions_file, mock_ghl_client):
    """Create PortalSwipeManager with mocked GHL client."""
    manager = PortalSwipeManager(interactions_path=temp_interactions_file)
    # Inject mock GHL client
    manager.ghl_client = mock_ghl_client
    return manager
```

**Verify test uses fixture** (line 69):
```python
@pytest.mark.asyncio
async def test_high_intent_detection(swipe_manager):  # Uses fixture with mock
    # Test code...
```

### Step 4: Add GHL Client Mocking - test_portal_api.py

**Add near imports (around line 10)**:
```python
from unittest.mock import AsyncMock, Mock, patch
```

**Add fixture after line 40**:
```python
@pytest.fixture
def mock_ghl_for_api_tests(mocker):
    """Mock GHL client for API-level tests."""
    # Mock at the class level where it's instantiated
    mock_client = Mock()
    mock_client.add_tags = AsyncMock(return_value={"status": "success"})

    # Patch the EnhancedGHLClient constructor
    mocker.patch(
        "ghl_real_estate_ai.services.portal_swipe_manager.EnhancedGHLClient",
        return_value=mock_client
    )
    return mock_client
```

**Update test to use fixture** (line 196):
```python
@pytest.mark.asyncio
async def test_high_intent_detection_via_api(client, mock_ghl_for_api_tests):
    # Test code...
```

---

## Verification Steps

### Test 1: Direct Service Test
```bash
source .venv/bin/activate
pytest ghl_real_estate_ai/tests/test_portal_swipe.py::test_high_intent_detection -v --tb=short
```

**Expected**: ✅ PASSED (high_intent=True on 3rd like)

### Test 2: API Endpoint Test
```bash
pytest ghl_real_estate_ai/tests/test_portal_api.py::test_high_intent_detection_via_api -v --tb=short
```

**Expected**: ✅ PASSED (high_intent=True via API)

### Test 3: All Portal Tests
```bash
pytest ghl_real_estate_ai/tests/test_portal_api.py -v
pytest ghl_real_estate_ai/tests/test_portal_swipe.py -v
```

**Expected**: All tests PASS (9+ portal API tests, 13+ swipe tests)

### Test 4: Verify No Regressions
```bash
pytest ghl_real_estate_ai/tests/test_portal_api.py ghl_real_estate_ai/tests/test_portal_swipe.py -v --tb=short
```

**Expected**: No new failures introduced

---

## Success Criteria

| Criterion | Status | Verification |
|-----------|--------|--------------|
| High-intent detection runs BEFORE GHL calls | ⬜ | Code review line 148-194 |
| GHL failures don't block high-intent flag | ⬜ | `result["high_intent"]` set regardless of GHL |
| Tests use mocked GHL client | ⬜ | No real HTTP calls in test logs |
| Deprecated datetime fixed | ⬜ | No `utcnow()` calls remaining |
| `test_high_intent_detection` PASSES | ⬜ | pytest output shows PASSED |
| `test_high_intent_detection_via_api` PASSES | ⬜ | pytest output shows PASSED |
| No performance regression | ⬜ | Tests complete in <2 seconds each |
| All portal tests PASS | ⬜ | 20+ total tests passing |

---

## Edge Cases to Validate

1. **GHL returns 401** → high_intent still detected ✅
2. **GHL times out** → high_intent still detected ✅
3. **Network error** → high_intent still detected ✅
4. **Exactly 3 likes** → `high_intent=True` ✅
5. **Only 2 likes** → `high_intent=False` ✅
6. **Mock doesn't break other tests** → All portal tests still pass ✅

---

## Rollback Plan

If any step fails:

1. **Stop immediately** - Don't proceed to next file
2. **Document error** - Capture full traceback
3. **Revert changes**:
   ```bash
   git checkout -- ghl_real_estate_ai/services/portal_swipe_manager.py
   git checkout -- ghl_real_estate_ai/tests/test_portal_swipe.py
   git checkout -- ghl_real_estate_ai/tests/test_portal_api.py
   ```
4. **Report to user** - Describe what failed and why

---

## Post-Fix Actions

### If All Tests Pass:

1. **Stage changes**:
   ```bash
   git add ghl_real_estate_ai/services/portal_swipe_manager.py
   git add ghl_real_estate_ai/tests/test_portal_swipe.py
   git add ghl_real_estate_ai/tests/test_portal_api.py
   ```

2. **Commit with message**:
   ```bash
   git commit -m "fix: portal API high-intent detection blocked by GHL failures

   Reorder _process_like() logic to run high-intent detection BEFORE GHL API
   calls. This ensures lead scoring works even when GHL is unavailable.

   - High-intent detection now runs first (local, no dependencies)
   - GHL tagging wrapped in nested try/except (fails gracefully)
   - Add GHL client mocking in tests (no real API calls)
   - Fix deprecated datetime.utcnow() calls

   Fixes EnterpriseHub-qu7

   Production Impact: Critical - High-intent leads now properly flagged
   Test Results: 2 tests fixed (high_intent_detection variants)

   Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
   ```

3. **Update bead**:
   ```bash
   bd close EnterpriseHub-qu7 --reason="Portal API refactored, high-intent detection fixed, tests passing"
   ```

4. **Sync and push**:
   ```bash
   bd sync
   git push origin main
   ```

---

## Reference Files

### Key Files (Read Before Starting)
1. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/portal_swipe_manager.py` - Main fix target
2. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_swipe.py` - Direct service tests
3. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_api.py` - API endpoint tests

### Related Files (Context)
4. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/enhanced_ghl_client.py` - GHL client implementation
5. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/api/routes/portal.py` - Portal API routes

### Investigation Reports
6. `/Users/cave/Documents/GitHub/EnterpriseHub/plans/TEST_FAILURE_FIX_SPEC_FEB9.md` - Full specification
7. Agent 1 Report (from Wave 1) - Portal API detailed analysis

---

## Agent Coordination

**You are Agent 4 in a multi-agent workflow**

- **Wave 1**: Complete ✅ (Agents 1-3)
- **Wave 2**: YOU ARE HERE (Agent 4)
- **Wave 3**: Will run after you (Agents 5-6 for verification & git)

**Your responsibilities**:
1. Fix the production bug
2. Ensure tests pass
3. Don't introduce regressions
4. Report completion status clearly

**On Success**: Report "Wave 2 Complete ✅" with test results
**On Failure**: Report error immediately, don't proceed

---

## Final Checklist Before Starting

- [ ] Read all 3 key files (portal_swipe_manager.py, 2 test files)
- [ ] Understand current broken flow vs. expected flow
- [ ] Have rollback plan ready
- [ ] Know success criteria (2 tests must pass)
- [ ] Ready to report detailed results

---

**Status**: Ready for Agent 4 deployment
**Next Command**: Deploy agent with this prompt
