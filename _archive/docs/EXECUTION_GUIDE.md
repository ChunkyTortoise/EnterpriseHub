# Phase F Execution Guide
**How to Run 5 Work Streams in Parallel**

---

## Quick Start (5 minutes)

### What You Have
- **DEVELOPMENT_SPEC.md** - Master spec with all requirements
- **STREAM_A_PROMPT.md** - Buyer bot error handling (2-3 hours)
- **STREAM_B_PROMPT.md** - Lead bot PDF enhancement (1-2 hours)
- **STREAM_C_PROMPT.md** - Optional feature integration (2-4 hours)
- **STREAM_D_PROMPT.md** - Testing & validation (3-4 hours)
- **STREAM_E_PROMPT.md** - Documentation & deployment (2-3 hours)

### What to Do Next

**Option 1: Parallel Execution (Fastest - 3-4 hours)**
```
Chat 1: Start Stream A (Buyer bot error handling)
Chat 2: Start Stream B (Lead bot PDF enhancement)
Chat 3: Start Stream D (Testing - infrastructure setup)
↓ (When A & B complete)
Chat 4: Start Stream C (Optional features)
↓ (When D baseline complete)
Chat 5: Start Stream E (Documentation)

Total Time: 3-4 hours parallel
```

**Option 2: Sequential Execution (Safer - 10-15 hours)**
```
Hour 0-3: Stream A (Buyer bot error handling)
Hour 3-4: Stream B (Lead bot PDF enhancement)
Hour 4-7: Stream D (Testing)
Hour 7-11: Stream C (Optional features)
Hour 11-14: Stream E (Documentation)

Total Time: 14 hours sequential
```

**Option 3: Mixed (Recommended - 5-6 hours)**
```
Phase 1 (parallel, 2-3 hours):
  - Stream A: Buyer bot errors
  - Stream B: Lead bot PDF
  - Stream D: Test infrastructure

Phase 2 (parallel, 1.5-2 hours):
  - Stream C: Feature flags
  - Stream D: Load testing (continues)

Phase 3 (sequential, 2-3 hours):
  - Stream E: Documentation

Total Time: 5-6 hours
```

---

## Execution by Stream

### Stream A: Buyer Bot Error Handling

**Start This First** (can overlap with B)

**Who**: Error handling specialist  
**Duration**: 2-3 hours  
**Prompt File**: STREAM_A_PROMPT.md

**Quick Steps**:
1. Read `STREAM_A_PROMPT.md` completely
2. Read `jorge_buyer_bot.py` lines 190-430
3. Implement 4 TODOs:
   - Retry mechanism (line 196)
   - Human escalation (line 211)
   - Financial fallback (line 405)
   - Compliance escalation (line 418)
4. Write 6+ test cases
5. Run: `pytest tests/agents/test_jorge_buyer_bot.py -v`
6. Verify: All 20 tests still passing

**Success Indicator**: 4/4 TODOs complete, tests green ✓

---

### Stream B: Lead Bot PDF Enhancement

**Start This First** (can overlap with A)

**Who**: Lead bot specialist  
**Duration**: 1-2 hours  
**Prompt File**: STREAM_B_PROMPT.md

**Quick Steps**:
1. Read `STREAM_B_PROMPT.md` completely
2. Check if PDF library available: `grep reportlab requirements.txt`
3. Implement PDF attachment for day 14 email
4. Write 3+ test cases
5. Run: `pytest tests/agents/test_lead_bot.py -v`
6. Manual test: Send email with PDF, verify in GHL

**Success Indicator**: PDF attaches to email, <200ms generation ✓

---

### Stream C: Optional Feature Integration

**Start After A & B** (or in parallel if enough capacity)

**Who**: Feature enablement specialist  
**Duration**: 2-4 hours  
**Prompt File**: STREAM_C_PROMPT.md

**Quick Steps**:
1. Read `STREAM_C_PROMPT.md` completely
2. Understand 3 features:
   - Progressive Skills (68% token reduction)
   - Agent Mesh (multi-agent routing)
   - MCP Integration (standardized services)
3. Create `config/feature_config.py` with all configurations
4. Enable each feature in seller bot
5. Write tests for each feature
6. Create `docs/FEATURE_FLAGS.md`
7. Update `.env.example`

**Success Indicator**: All 3 features configurable, tests pass ✓

---

### Stream D: Testing & Validation

**Start in Phase 1** (infrastructure), continue in parallel

**Who**: QA/testing specialist  
**Duration**: 3-4 hours  
**Prompt File**: STREAM_D_PROMPT.md

**Quick Steps**:
1. Read `STREAM_D_PROMPT.md` completely
2. Create test directory structure:
   ```
   tests/load/
   tests/integration/
   tests/performance/
   ```
3. Phase 1 (1 hour): Setup fixtures & conftest
4. Phase 2 (1 hour): Write load tests (concurrent users)
5. Phase 3 (45 min): Write performance baseline tests
6. Phase 4 (60 min): Write integration tests
7. Phase 5 (30 min): Run regression tests
8. Phase 6 (30 min): Create performance report

**Commands**:
```bash
# Run load tests
pytest tests/load/test_concurrent_load.py -v -s

# Run performance tests
pytest tests/performance/test_response_times.py -v -s

# Run integration tests
pytest tests/integration/test_full_jorge_flow.py -v -s

# Run all with coverage
pytest tests/ --cov=ghl_real_estate_ai --cov-report=html
```

**Success Indicator**: 100 users <5% error, p95 <200ms, all tests pass ✓

---

### Stream E: Documentation & Deployment

**Start After A-D Complete** (or parallel if docs work separately)

**Who**: Documentation/DevOps specialist  
**Duration**: 2-3 hours  
**Prompt File**: STREAM_E_PROMPT.md

**Quick Steps**:
1. Read `STREAM_E_PROMPT.md` completely
2. Create `docs/API_SPEC.md` (1 hour)
   - Authentication
   - Lead endpoints
   - Buyer endpoints
   - Seller endpoints
   - Webhooks
   - Rate limits
3. Create `docs/DEPLOYMENT.md` (45 min)
   - Pre-deployment checklist
   - Staging deployment
   - Production blue-green
   - Rollback procedure
4. Create `docs/MONITORING.md` (45 min)
   - Key metrics
   - Prometheus queries
   - Grafana dashboard
5. Create `docs/TROUBLESHOOTING.md` (30 min)
   - 6+ common issues
   - Investigation steps
   - Solutions
6. Update `.env.example` (15 min)
7. Create `docs/FEATURE_FLAGS.md` (15 min)

**Success Indicator**: All documentation complete, ready to deploy ✓

---

## Parallel Execution Strategy

### Timeline: Mixed Approach (5-6 hours total)

```
00:00 - START
├─ Agent 1 starts Stream A (Buyer errors)
├─ Agent 2 starts Stream B (Lead PDF)
└─ Agent 3 starts Stream D Phase 1 (Test setup)

02:00 - CHECKPOINT 1
├─ A: 80% complete (implementing TODOs)
├─ B: 70% complete (PDF generation)
├─ D: 40% complete (test infrastructure ready)
Status: ON TRACK

03:00 - CHECKPOINT 2
├─ A: COMPLETE ✓ (all tests passing)
├─ B: COMPLETE ✓ (PDF working)
├─ D: 70% complete (load tests running)
├─ Agent 4 starts Stream C (Optional features)
└─ Agent 5 starts Stream E (Documentation)

04:00 - CHECKPOINT 3
├─ C: 50% complete (Progressive Skills working)
├─ D: 95% complete (performance baseline established)
├─ E: 30% complete (API spec drafted)
Status: ALL STREAMS ACTIVE, GOOD PROGRESS

05:00 - CHECKPOINT 4
├─ C: 90% complete (all features enabled)
├─ D: COMPLETE ✓ (all tests, report ready)
├─ E: 70% complete (deployment docs drafted)
Status: NEARLY DONE

06:00 - COMPLETE ✓
├─ A: DONE ✓ (Buyer bot hardened)
├─ B: DONE ✓ (Lead bot enhanced)
├─ C: DONE ✓ (Features enabled)
├─ D: DONE ✓ (Fully tested)
└─ E: DONE ✓ (Documented)

ALL STREAMS COMPLETE - READY FOR PRODUCTION
```

---

## Agent Assignments

### Option 1: 5 Agents (Maximum Parallelization)

```
Agent 1: Stream A (Buyer Bot)
Agent 2: Stream B (Lead Bot)
Agent 3: Stream D (Testing)
Agent 4: Stream C (Features) - starts after A & B
Agent 5: Stream E (Docs) - starts after D
```

### Option 2: 3 Agents (Practical)

```
Agent 1: Streams A + C
Agent 2: Streams B + D
Agent 3: Streams D + E
```

### Option 3: 1-2 Agents (Sequential)

```
Agent 1: Streams A → B → C → D → E
Agent 2: (Optional backup/review)
```

---

## Quality Gates Between Streams

### Gate 1: After A & B (Before C)
**Requirement**: All tests passing, no regressions
```bash
pytest tests/agents/ -v  # Must be 20/20 ✓
```

### Gate 2: After C (Before D)
**Requirement**: Feature flags working, no side effects
```bash
ENABLE_PROGRESSIVE_SKILLS=true pytest tests/agents/ -v  # Must pass
```

### Gate 3: After D (Before E)
**Requirement**: Performance baselines established
```bash
# Load test report generated
# p95 latency documented
# Error rates validated
```

### Gate 4: After E (Before Deployment)
**Requirement**: Documentation complete and accurate
```bash
# Runbooks tested manually
# Deployment verified in staging
# Monitoring dashboards verified
```

---

## Communication Between Streams

### Stream A → All Others
- Provides error handling patterns
- May affect Stream D (more edge case tests)
- No blocking dependencies

### Stream B → All Others
- Provides PDF generation pattern
- May affect Stream D (performance of PDF)
- No blocking dependencies

### Stream D → Stream E
- **MUST COMPLETE FIRST** - E needs performance metrics
- Stream E needs load test report
- E documents the metrics from D

### Stream C → Stream D
- **CAN RUN PARALLEL** - independent
- D should test features enabled
- C needs test results to validate features

---

## Success Criteria Summary

| Stream | Completion Target | Validation |
|--------|-------------------|-----------|
| A | 4 TODOs + 6 tests | `pytest tests/agents/test_jorge_buyer_bot.py -v` ✓ |
| B | PDF attached + test | `pytest tests/agents/test_lead_bot.py -v` ✓ |
| C | 3 features enabled | `pytest tests/ -k "feature"` ✓ |
| D | Load test + baseline | `pytest tests/load/ -v` ✓ |
| E | 5 doc files | Files created, readable ✓ |

**Overall**: 20/20 tests passing, <200ms p95, <5% error rate, production-ready ✓

---

## Risk Mitigation

### If Stream A Blocks
- Most complex, high impact
- Mitigation: Start first, get feedback early
- Fallback: Disable features if too complex

### If Stream B Has Issues
- Independent, easier to fix
- Mitigation: Test in staging first
- Fallback: PDF optional, email still sends

### If Stream D Finds Bottleneck
- Testing might reveal performance issues
- Mitigation: Have D communicate early (checkpoint 2)
- Fallback: Optimize in parallel with other streams

### If Stream E Gets Blocked
- Documentation can't start until D complete
- Mitigation: Draft templates early
- Fallback: Minimal docs sufficient for MVP

---

## Daily Standup Format

```
Stream A: "Made progress on [TODO], now working on [TODO]"
         "Blocker: [if any]"
         "ETA: [time until complete]"

Stream B: "PDF generation working, adding tests"
         "No blockers, on track"
         "ETA: 30 minutes"

Stream C: "Set up feature config, testing Progressive Skills"
         "Need clarification on [question]"
         "ETA: 90 minutes"

Stream D: "Test infrastructure ready, running load tests"
         "Baseline metrics being captured"
         "ETA: 2 hours"

Stream E: "Waiting for D to complete, draft docs ready"
         "No blockers (waiting game)"
         "ETA: 1 hour after D"
```

---

## Handoff Checklist

When a stream completes, handoff to next agent:

- [ ] All code merged to feature branch
- [ ] All tests passing (specify: X/X ✓)
- [ ] Code reviewed (if applicable)
- [ ] Documentation updated
- [ ] No breaking changes
- [ ] Performance validated
- [ ] No new security issues
- [ ] Ready for next stream

---

## Final Validation (Before Production)

```bash
# 1. All tests passing
pytest tests/ -v --tb=short  # Must show 25+/25+ ✓

# 2. Performance targets met
pytest tests/performance/ -v  # Must show p95 <200ms

# 3. Load handling validated
pytest tests/load/ -v  # Must show <5% error at 100 users

# 4. No regressions
pytest tests/agents/ -v  # Must show all 20 original passing

# 5. Features work correctly
ENABLE_PROGRESSIVE_SKILLS=true pytest tests/ -v

# 6. Documentation complete
ls -la docs/*.md  # Must show 6+ files

# 7. Deployment validated in staging
./scripts/smoke_test.sh staging  # Must pass

# 8. Ready for production
./scripts/production_readiness_check.py  # Green lights
```

---

## Escalation Path

If a stream gets stuck:

1. **First 30 minutes**: Try to resolve within stream
2. **30-60 minutes**: Ask for help from related stream
3. **60+ minutes**: Escalate to lead/architect
4. **Blocker detected**: Mark stream as blocked, pivot to other work

Example:
```
Stream A blocked on GHL API question
→ Ask Stream E (has API knowledge)
→ If unresolved: Ask Stream A lead (specialist)
→ If still blocked: Escalate to architecture review
```

---

## Post-Completion

After all 5 streams complete:

1. **Code Review** (1 hour)
   - Review all changes
   - Verify quality standards
   - Approve for merge

2. **Integration Testing** (1 hour)
   - Test all streams together
   - Verify no conflicts
   - Validate full system

3. **Staging Deployment** (2 hours)
   - Deploy to staging
   - Run full smoke tests
   - Monitor 1 hour
   - Verify ready for production

4. **Production Deployment** (1 hour)
   - Blue-green deployment
   - Canary monitoring
   - Full traffic switchover
   - 30-minute monitoring

**Total Post-Completion**: 4-5 hours

---

## Success Metrics

| Metric | Target | Current |
|--------|--------|---------|
| Code coverage | ≥80% | TBD |
| Test pass rate | 100% | TBD |
| API latency p95 | <200ms | TBD |
| Bot response p95 | <500ms | TBD |
| Error rate | <5% at 100 users | TBD |
| Load sustained | 100 concurrent users | TBD |
| Documentation | Complete | TBD |
| Production ready | YES | TBD |

---

## Next Steps

1. **NOW** (5 minutes):
   - Assign agents to streams
   - Copy stream prompts to chats
   - Start streams A, B, D

2. **Hour 2** (Checkpoint 1):
   - Review progress
   - Unblock any issues
   - Start stream C if ready

3. **Hour 4** (Checkpoint 2):
   - Complete streams A, B
   - Start stream E (docs)
   - Monitor stream D

4. **Hour 6** (Final):
   - All streams complete
   - Merge to feature branch
   - Ready for staging deployment

---

## Questions Before Starting?

- Which agent assignment works best for your team?
- Do you want parallel, sequential, or mixed execution?
- Any streams that need more detail before starting?
- Any blockers we should anticipate?

**Ready to execute Phase F?** ✓

Let's build production-ready Jorge bots! 🚀
