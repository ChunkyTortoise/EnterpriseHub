# Wave 2 Deployment - Ready to Execute

**Status**: ✅ Bead updated to `in_progress`
**Bead**: EnterpriseHub-qu7 (P0)
**Assigned**: Agent 4

---

## 🚀 Deploy Command

```python
Task(
    subagent_type="general-purpose",
    description="Fix Portal API high-intent bug",
    model="opus",
    prompt=open('/Users/cave/Documents/GitHub/EnterpriseHub/plans/AGENT4_DEPLOY_PROMPT.txt').read()
)
```

### Or use Task tool directly:

```
subagent_type: general-purpose
description: Fix Portal API high-intent bug
model: opus
prompt: [Contents of AGENT4_DEPLOY_PROMPT.txt]
```

---

## 📁 Files Inventory

### Primary Targets (Will be Modified)
1. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/portal_swipe_manager.py`
   - Lines 148-194: Refactor `_process_like()`
   - Lines 367, 384: Fix deprecated datetime

2. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_swipe.py`
   - Add mock_ghl_client fixture
   - Update swipe_manager fixture

3. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/tests/test_portal_api.py`
   - Add mock_ghl_for_api_tests fixture
   - Update test signature

### Context Files (Reference Only)
4. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/services/enhanced_ghl_client.py`
5. `/Users/cave/Documents/GitHub/EnterpriseHub/ghl_real_estate_ai/api/routes/portal.py`

### Specification Files
6. `/Users/cave/Documents/GitHub/EnterpriseHub/plans/AGENT4_DEPLOY_PROMPT.txt` - **Main prompt**
7. `/Users/cave/Documents/GitHub/EnterpriseHub/plans/WAVE2_PORTAL_API_FIX_PROMPT.md` - Full spec
8. `/Users/cave/Documents/GitHub/EnterpriseHub/plans/WAVE2_QUICK_DEPLOY.md` - Quick reference

---

## 🎯 What This Fix Does

### Problem
```
User likes 3 properties → High-intent detection should trigger
                       → GHL API fails (401 Unauthorized)
                       → Method exits early
                       → high_intent flag NEVER SET
                       → Lead not flagged for follow-up ❌
```

### Solution
```
User likes 3 properties → Count likes (local)
                       → SET high_intent=True ✅
                       → Update memory
                       → Try GHL tagging (optional, can fail)
                       → Lead properly flagged ✅
```

---

## ✅ Expected Outcomes

### Tests Fixed
- `test_high_intent_detection` - PASSES
- `test_high_intent_detection_via_api` - PASSES

### Production Impact
- High-intent leads properly detected even when GHL is down
- No more missed hot leads due to API failures
- Graceful degradation (GHL tags optional, detection mandatory)

### Code Quality
- Deprecated datetime.utcnow() removed
- Proper test mocking (no real API calls)
- Clear separation of business logic vs. external APIs

---

## 📊 Verification Plan

### Phase 1: Unit Tests (Quick - 2 min)
```bash
source .venv/bin/activate
pytest ghl_real_estate_ai/tests/test_portal_swipe.py::test_high_intent_detection -v
pytest ghl_real_estate_ai/tests/test_portal_api.py::test_high_intent_detection_via_api -v
```

### Phase 2: Full Portal Suite (Medium - 5 min)
```bash
pytest ghl_real_estate_ai/tests/test_portal_api.py ghl_real_estate_ai/tests/test_portal_swipe.py -v
```

### Phase 3: Smoke Test (Optional - 1 min)
```bash
pytest ghl_real_estate_ai/tests/ -k "portal" -v --tb=no
```

---

## 🔄 Rollback Plan

If anything fails:
```bash
git checkout -- ghl_real_estate_ai/services/portal_swipe_manager.py
git checkout -- ghl_real_estate_ai/tests/test_portal_swipe.py
git checkout -- ghl_real_estate_ai/tests/test_portal_api.py
bd update EnterpriseHub-qu7 --status=open
```

---

## 📈 Progress Tracking

**Wave 1**: ✅ Complete (3 beads closed in 7 min)
**Wave 2**: 🔄 In Progress (Agent 4 deploying)
**Wave 3**: ⏳ Pending (Verification & Git workflow)

---

## ⏱️ Timeline

- **Agent work**: 30-45 minutes
- **Testing**: 5-10 minutes
- **Git workflow**: 5 minutes
- **Total**: ~1 hour

---

## 🎬 Next Steps After Wave 2

1. **Immediate**: Run verification tests
2. **If passing**: Commit changes, close bead, sync
3. **If failing**: Review errors, rollback if needed
4. **Then**: Deploy Wave 3 (verification & final git push)

---

**Ready to deploy?** The prompt is loaded, bead is updated, all specs are ready.

Just say **"deploy agent 4"** or paste the prompt into a new Task tool call.
