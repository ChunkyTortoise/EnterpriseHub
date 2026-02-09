# Test Failure Fix Specification - Agent Team Orchestration
**Date**: February 9, 2026
**Objective**: Fix 620 test failures using parallel agent coordination
**Estimated Impact**: 620 failures → <50 failures (potentially all green)

---

## Executive Summary

### Root Causes Identified (5 Critical Issues)
1. **Portal API Logic Bug** - GHL auth failure causes early exit (2 tests, production bug)
2. **Property Matcher Data Mismatch** - Test config using wrong market (5 tests)
3. **RAG ChromaDB Version** - Pydantic v2 incompatibility (2 tests + cascading failures)
4. **Property Integration Collision** - Duplicate method names (1 test)
5. **Security False Positive** - Coverage DB corruption (0 tests, already fixed)

### Beads Tracking
- `EnterpriseHub-egv`: Portal API test failures (9 tests)
- `EnterpriseHub-0br`: Property Matcher test failures (5 tests)
- `EnterpriseHub-9yv`: RAG Multitenancy test failures (2 tests)
- `EnterpriseHub-14w`: Property Integration test failure (1 test)
- `EnterpriseHub-8fq`: Security/Access Control (0 tests, coverage cleanup)

---

## Phase 1: Quick Wins (Low-Risk, High-Impact)

### Agent 1: ChromaDB Upgrade Specialist
**Bead**: `EnterpriseHub-9yv`
**Priority**: P0 (CRITICAL - Blocks hundreds of tests)
**Complexity**: Low
**Estimated Time**: 15 minutes

#### Tasks:
1. **Update requirements.txt** (line 11)
   ```bash
   # FROM:
   chromadb==0.4.24

   # TO:
   chromadb==0.5.23
   ```

2. **Verify compatibility**
   - Check if API changes needed in `ghl_real_estate_ai/core/rag_engine.py`
   - Review ChromaDB 0.5.x migration guide
   - Confirm Pydantic v2 compatibility

3. **Install and test**
   ```bash
   pip install chromadb==0.5.23
   pytest ghl_real_estate_ai/tests/test_rag_multitenancy.py -v --tb=short
   ```

4. **Expected outcome**: 2 tests pass, CHROMA_AVAILABLE=True

#### Success Criteria:
- ✅ ChromaDB imports successfully
- ✅ No "BaseSettings" import errors
- ✅ `test_multitenancy_scoping` PASSES
- ✅ `test_multitenancy_no_global` PASSES
- ✅ Vector store returns non-empty results

#### Dependencies: None (can run immediately)

---

### Agent 2: Method Rename Specialist
**Bead**: `EnterpriseHub-14w`
**Priority**: P0 (CRITICAL - Production bug)
**Complexity**: Low
**Estimated Time**: 10 minutes

#### Tasks:
1. **Read source file**
   ```bash
   Read ghl_real_estate_ai/core/conversation_manager.py
   ```

2. **Rename duplicate method** (line 858)
   ```python
   # FROM:
   async def extract_data(self, contact_id: str, location_id: Optional[str] = None) -> int:
       """Calculate lead score for a contact."""
       context = await self.get_context(contact_id, location_id=location_id)
       return self.lead_scorer.calculate(context)

   # TO:
   async def calculate_lead_score(self, contact_id: str, location_id: Optional[str] = None) -> int:
       """Calculate lead score for a contact."""
       context = await self.get_context(contact_id, location_id=location_id)
       return self.lead_scorer.calculate(context)
   ```

3. **Verify no references**
   ```bash
   grep -r "\.extract_data\(" ghl_real_estate_ai/ | grep -v "test_" | grep -v ".pyc"
   ```

4. **Run test**
   ```bash
   pytest ghl_real_estate_ai/tests/test_property_integration.py::test_property_recommendation_for_warm_lead -v
   ```

#### Success Criteria:
- ✅ Method renamed without breaking legitimate `extract_data()` (line 273)
- ✅ No references to old method signature found
- ✅ `test_property_recommendation_for_warm_lead` PASSES
- ✅ Property recommendations show in system prompt for warm leads

#### Dependencies: None (can run immediately)

---

### Agent 3: Property Matcher Config Specialist
**Bead**: `EnterpriseHub-0br`
**Priority**: P1 (Test infrastructure)
**Complexity**: Low
**Estimated Time**: 20 minutes

#### Tasks:
1. **Option A: Force Austin Market (Quick Fix)**

   Add to `ghl_real_estate_ai/tests/conftest.py` or test file:
   ```python
   import os
   import pytest

   @pytest.fixture(scope="session", autouse=True)
   def force_austin_market():
       """Force Austin market for property matcher tests."""
       original = os.environ.get("JORGE_MARKET")
       os.environ["JORGE_MARKET"] = "austin"
       yield
       if original:
           os.environ["JORGE_MARKET"] = original
       else:
           os.environ.pop("JORGE_MARKET", None)
   ```

2. **Option B: Update Test Expectations (Proper Fix)**

   Update `ghl_real_estate_ai/tests/test_property_matcher.py`:
   ```python
   # Line 16 - Accept both prefixes:
   assert matcher.listings[0]["id"].startswith(("prop_", "rc_"))

   # Line 23 - Use Rancho-appropriate budget:
   matches = matcher.find_matches({"budget": 700000}, limit=1)
   assert len(matches) == 1
   assert matches[0]["price"] <= 700000

   # Line 32 - Use Rancho neighborhood:
   matches = matcher.find_matches({"location": "Alta Loma"}, limit=1)
   assert len(matches) == 1
   assert "Alta Loma" in matches[0]["address"]["neighborhood"]
   ```

3. **Fix deprecated method test** (line 49)
   ```python
   # FROM:
   score = matcher._calculate_match_score(prop, prefs)

   # TO:
   from ghl_real_estate_ai.services.property_matching_strategy import BasicFilteringStrategy
   strategy = BasicFilteringStrategy()
   score = strategy._calculate_basic_score(prop, prefs)
   ```

4. **Run tests**
   ```bash
   pytest ghl_real_estate_ai/tests/test_property_matcher.py -v --tb=short
   pytest ghl_real_estate_ai/tests/test_property_matcher_ml.py::TestPropertyMatcherUIIntegration::test_enhanced_property_matcher_integration -v
   ```

#### Success Criteria:
- ✅ All 5 property matcher tests PASS
- ✅ Tests work regardless of JORGE_MARKET setting
- ✅ No hardcoded Austin-specific data in tests
- ✅ Strategy pattern tests use correct API

#### Dependencies: None (can run immediately)

#### Recommendation: Start with Option A (quick), refactor to Option B later

---

## Phase 2: Critical Production Bug (Requires Careful Testing)

### Agent 4: Portal API Logic Refactor Specialist
**Bead**: `EnterpriseHub-egv`
**Priority**: P0 (CRITICAL - Production bug)
**Complexity**: Medium
**Estimated Time**: 45 minutes

#### Tasks:

##### Task 4.1: Refactor `_process_like()` Logic
**File**: `ghl_real_estate_ai/services/portal_swipe_manager.py`
**Lines**: 148-194

**Strategy**: Move high-intent detection BEFORE GHL API calls

```python
async def _process_like(self, lead_id: str, property_id: str, location_id: str) -> Dict[str, Any]:
    """Process a 'like' action with high-intent detection FIRST."""
    result = {"status": "logged", "trigger_sms": False, "high_intent": False}

    try:
        # STEP 1: Count recent likes (local operation, no external deps)
        recent_likes = self._count_recent_likes(lead_id, minutes=10)
        logger.info(f"Lead {lead_id} has {recent_likes} likes in last 10 minutes")

        # STEP 2: Detect high-intent behavior (BEFORE GHL calls)
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

##### Task 4.2: Fix Deprecated Datetime Usage
**Lines**: 367, 384

```python
# FROM:
datetime.utcnow()

# TO:
datetime.now(datetime.UTC)
```

##### Task 4.3: Add GHL Client Mocking
**File**: `ghl_real_estate_ai/tests/test_portal_swipe.py`
**Lines**: 38-42

```python
import pytest
from unittest.mock import AsyncMock, Mock

@pytest.fixture
def mock_ghl_client(mocker):
    """Mock GHL client to avoid real API calls in tests."""
    mock = Mock()
    mock.add_tags = AsyncMock(return_value={"status": "success"})
    return mock

@pytest.fixture
def swipe_manager(temp_interactions_file, mock_ghl_client):
    """Create a PortalSwipeManager instance with mocked GHL client."""
    manager = PortalSwipeManager(
        interactions_path=temp_interactions_file
    )
    # Inject mock GHL client
    manager.ghl_client = mock_ghl_client
    return manager
```

##### Task 4.4: Add Similar Mocking for API Tests
**File**: `ghl_real_estate_ai/tests/test_portal_api.py`

```python
@pytest.fixture
def mock_swipe_manager(mocker):
    """Mock swipe manager's GHL client for API tests."""
    # Patch at import/instantiation level
    mocker.patch(
        "ghl_real_estate_ai.services.portal_swipe_manager.EnhancedGHLClient"
    )
```

##### Task 4.5: Run Comprehensive Tests
```bash
# Test direct service
pytest ghl_real_estate_ai/tests/test_portal_swipe.py::test_high_intent_detection -v --tb=short

# Test via API
pytest ghl_real_estate_ai/tests/test_portal_api.py::test_high_intent_detection_via_api -v --tb=short

# Run all portal tests
pytest ghl_real_estate_ai/tests/test_portal_api.py -v
pytest ghl_real_estate_ai/tests/test_portal_swipe.py -v
```

#### Success Criteria:
- ✅ High-intent detection runs BEFORE GHL API calls
- ✅ Tests pass even when GHL API is unavailable/mocked
- ✅ Production gracefully handles GHL failures (logs error, continues)
- ✅ No performance regression (remove retry delays in test env)
- ✅ All 9 portal API tests PASS
- ✅ Both high_intent_detection tests PASS

#### Edge Cases to Test:
1. GHL API returns 401 → high_intent still detected ✅
2. GHL API times out → high_intent still detected ✅
3. Network error during tagging → high_intent still detected ✅
4. Lead with exactly 3 likes → triggers high_intent=True ✅
5. Lead with 2 likes → high_intent=False ✅

#### Dependencies:
- **MUST complete after Agents 1-3** to avoid merge conflicts
- Consider running in isolated branch for testing

---

## Phase 3: Verification & Integration

### Agent 5: Test Verification Coordinator
**Priority**: P1
**Complexity**: Low
**Estimated Time**: 30 minutes

#### Tasks:

##### Task 5.1: Run Full Test Suite
```bash
pytest ghl_real_estate_ai/tests/ -v --tb=short -x
```

##### Task 5.2: Generate Coverage Report
```bash
pytest ghl_real_estate_ai/tests/ --cov=ghl_real_estate_ai --cov-report=html --cov-report=term
```

##### Task 5.3: Identify Remaining Failures
```bash
pytest ghl_real_estate_ai/tests/ --tb=no -q | grep FAILED > remaining_failures.txt
```

##### Task 5.4: Categorize Remaining Failures
- Import errors (fix imports)
- Data dependency failures (add fixtures)
- Async/timeout issues (adjust timeouts)
- Mock/patch issues (fix test setup)

##### Task 5.5: Update Beads
```bash
bd close EnterpriseHub-9yv  # RAG ChromaDB
bd close EnterpriseHub-14w  # Property Integration
bd close EnterpriseHub-0br  # Property Matcher
bd close EnterpriseHub-egv  # Portal API
bd close EnterpriseHub-8fq  # Security (already done)
```

#### Success Criteria:
- ✅ Test count: 620 failures → <50 failures (or all green)
- ✅ Coverage: Maintains or improves current coverage %
- ✅ No new failures introduced
- ✅ All beads closed and synced

---

## Phase 4: Commit & Push

### Agent 6: Git Workflow Manager
**Priority**: P1
**Complexity**: Low
**Estimated Time**: 15 minutes

#### Tasks:

##### Task 6.1: Review Changes
```bash
git status
git diff
```

##### Task 6.2: Stage Changes
```bash
git add ghl_real_estate_ai/requirements.txt
git add ghl_real_estate_ai/core/conversation_manager.py
git add ghl_real_estate_ai/core/rag_engine.py
git add ghl_real_estate_ai/services/portal_swipe_manager.py
git add ghl_real_estate_ai/tests/test_property_matcher.py
git add ghl_real_estate_ai/tests/test_portal_swipe.py
git add ghl_real_estate_ai/tests/test_portal_api.py
git add ghl_real_estate_ai/tests/conftest.py
```

##### Task 6.3: Commit with Descriptive Message
```bash
git commit -m "$(cat <<'EOF'
fix: resolve 620 test failures - 5 root causes addressed

- ChromaDB: Upgrade 0.4.24 → 0.5.23 (Pydantic v2 compat)
- Portal API: Reorder high-intent detection before GHL calls
- Property Matcher: Add market-agnostic test config
- Property Integration: Rename duplicate extract_data() method
- Tests: Add GHL client mocking, fix deprecated datetime calls

Fixes EnterpriseHub-egv, EnterpriseHub-0br, EnterpriseHub-9yv,
EnterpriseHub-14w, EnterpriseHub-8fq

Test Results: 620 failures → <50 failures (estimated)
Production Impact: Critical high-intent detection bug fixed

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
EOF
)"
```

##### Task 6.4: Sync Beads
```bash
bd sync
```

##### Task 6.5: Push to Remote
```bash
git push origin main
```

#### Success Criteria:
- ✅ Clean commit with descriptive message
- ✅ All beads synced with git
- ✅ Changes pushed to remote
- ✅ CI/CD pipeline passes (if configured)

---

## Execution Strategy

### Parallel Execution Plan

**Wave 1 (Parallel - No Dependencies):**
```
Agent 1 (ChromaDB)  ─┐
Agent 2 (Method)    ─┼─→ Complete independently
Agent 3 (Config)    ─┘
```

**Wave 2 (Sequential - Depends on Wave 1):**
```
Wave 1 Complete → Agent 4 (Portal API) → Complete
```

**Wave 3 (Sequential - Depends on All):**
```
Agent 4 Complete → Agent 5 (Verification) → Agent 6 (Git) → Done
```

### Estimated Timeline
- **Wave 1**: 20 minutes (parallel)
- **Wave 2**: 45 minutes (sequential)
- **Wave 3**: 45 minutes (sequential)
- **Total**: ~110 minutes (~2 hours)

### Risk Mitigation

**High Risk Areas:**
1. Portal API refactor (production code, complex logic)
   - Mitigation: Extensive testing, isolated branch

2. ChromaDB upgrade (potential API breaking changes)
   - Mitigation: Check migration guide, test all RAG functionality

**Low Risk Areas:**
1. Method rename (simple refactor)
2. Test config (test-only changes)
3. Coverage cleanup (already done)

### Rollback Plan

If any agent encounters issues:

1. **Stop immediately** - Don't proceed to next phase
2. **Document error** - Capture full stack trace
3. **Revert changes** - `git checkout -- <file>`
4. **Update bead** - Add notes about blocker
5. **Escalate** - Ask user for guidance

---

## Agent Coordination Protocol

### Communication
- Each agent reports completion to main coordinator
- Errors block dependent agents
- Success metrics logged for each phase

### Handoff Points
1. Wave 1 → Wave 2: All quick wins complete
2. Wave 2 → Wave 3: Portal API verified
3. Wave 3 → Complete: All tests pass, committed

### Quality Gates
- ✅ Each agent runs targeted tests before handoff
- ✅ No agent proceeds if predecessor failed
- ✅ Full suite verification before commit
- ✅ Manual review of git diff before push

---

## Success Metrics

### Quantitative
- **Test Failures**: 620 → <50 (>92% reduction)
- **Test Pass Rate**: ~86% → >98%
- **Coverage**: Maintain ≥80% (or current %)
- **Execution Time**: ~2 hours total

### Qualitative
- ✅ All beads closed
- ✅ Production bugs fixed (high-intent detection, method collision)
- ✅ Test infrastructure improved (mocking, market config)
- ✅ No regressions introduced
- ✅ Clean git history

---

## Post-Completion Tasks

1. **Update MEMORY.md**: Record lessons learned
2. **Create PR** (if using feature branch)
3. **Update documentation**: Note ChromaDB version requirement
4. **Monitor production**: Verify high-intent detection working
5. **Schedule tech debt**: Address remaining <50 failures

---

## Appendix: Agent Specifications

### Agent Types Available
- **general-purpose**: Research, debugging, multi-step tasks
- **Explore**: Fast codebase exploration
- **Bash**: Command execution specialist

### Recommended Agent Assignments
- Agent 1 (ChromaDB): `general-purpose` or `Bash`
- Agent 2 (Method): `general-purpose`
- Agent 3 (Config): `general-purpose`
- Agent 4 (Portal API): `general-purpose` (most complex)
- Agent 5 (Verification): `general-purpose`
- Agent 6 (Git): `Bash`

### Agent Tool Access
All agents have access to: Read, Edit, Write, Bash, Grep, Glob

### Model Selection
- **Haiku**: Simple edits (Agents 2, 3)
- **Sonnet**: Standard complexity (Agents 1, 5, 6)
- **Opus**: Complex refactoring (Agent 4)

---

**Prepared by**: Claude Sonnet 4.5
**Status**: Ready for execution
**Next Step**: Deploy Agent Wave 1 (3 parallel agents)
