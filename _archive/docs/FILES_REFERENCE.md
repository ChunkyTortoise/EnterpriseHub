# Complete Files Reference
**Master index for Phase F development**

---

## 📋 Specification & Planning Documents

### DEVELOPMENT_SPEC.md
**Purpose**: Master specification for all Phase F work  
**Status**: READ THIS FIRST  
**Contains**:
- Executive overview
- 5 work streams with deliverables
- Technical specifications for each TODO
- Performance targets
- Testing requirements
- Risk mitigation
- Success criteria

**When to Reference**: When clarifying requirements, understanding dependencies, or checking acceptance criteria

---

### EXECUTION_GUIDE.md
**Purpose**: How to run all streams in parallel  
**Status**: READ THIS SECOND  
**Contains**:
- Quick start options (parallel, sequential, mixed)
- Stream-by-stream execution steps
- Timeline and checkpoints
- Agent assignments
- Quality gates between streams
- Success metrics

**When to Reference**: For overall coordination, tracking progress, understanding dependencies between streams

---

## 🎯 Stream-Specific Prompts

### STREAM_A_PROMPT.md
**Chat Audience**: Error handling specialist  
**Duration**: 2-3 hours  
**Main File**: `ghl_real_estate_ai/agents/jorge_buyer_bot.py`

**Contains**:
- 4 specific TODOs with implementation details
- Implementation strategy (4 phases)
- Test cases to write
- Success criteria
- Key constraints
- Reference implementations

**Test File**: `tests/agents/test_jorge_buyer_bot.py`  
**Support Services**:
- `ghl_real_estate_ai/services/enhanced_ghl_client.py`
- `ghl_real_estate_ai/services/event_publisher.py`

---

### STREAM_B_PROMPT.md
**Chat Audience**: Lead bot specialist  
**Duration**: 1-2 hours  
**Main File**: `ghl_real_estate_ai/agents/lead_bot.py` (line 1717)

**Contains**:
- Single TODO: PDF attachment for day 14 email
- Implementation details (3 steps)
- PDF generation service setup
- Email template enhancement
- Test cases
- Performance targets (<200ms)
- Fallback strategy

**Test File**: `tests/agents/test_lead_bot.py`  
**Support Services**:
- `ghl_real_estate_ai/services/cma_generator.py`
- `ghl_real_estate_ai/services/pdf_generator.py` (may create)
- `ghl_real_estate_ai/services/enhanced_ghl_client.py`

---

### STREAM_C_PROMPT.md
**Chat Audience**: Feature enablement specialist  
**Duration**: 2-4 hours  
**Main File**: `ghl_real_estate_ai/agents/jorge_seller_bot.py`

**Contains**:
- 3 optional features to enable
- Progressive Skills configuration
- Agent Mesh configuration
- MCP Integration configuration
- Test cases for each feature
- Environment variable setup
- Documentation template

**Config File** (to create): `ghl_real_estate_ai/config/feature_config.py`  
**Test File**: `tests/agents/test_jorge_seller_bot.py`  
**Documentation** (to create): `docs/FEATURE_FLAGS.md`  
**Support Services**:
- `ghl_real_estate_ai/services/progressive_skills_manager.py`
- `ghl_real_estate_ai/services/agent_mesh_coordinator.py`
- `ghl_real_estate_ai/services/mcp_client.py`

---

### STREAM_D_PROMPT.md
**Chat Audience**: QA/testing specialist  
**Duration**: 3-4 hours  
**Main Files** (to create): 
- `tests/load/test_concurrent_load.py`
- `tests/integration/test_full_jorge_flow.py`
- `tests/performance/test_response_times.py`

**Contains**:
- Load testing strategy (100+ concurrent users)
- Performance baseline tests
- Integration test scenarios
- Test fixtures and helpers
- Commands to run
- Performance report template
- Success criteria

**Documentation** (to create): `docs/PERFORMANCE_BASELINE.md`  
**Test Fixtures**: `tests/conftest.py` (enhancement)  
**Test Data**: `tests/fixtures/test_data.py` (create)

---

### STREAM_E_PROMPT.md
**Chat Audience**: Documentation/DevOps specialist  
**Duration**: 2-3 hours  
**Files to Create**:
- `docs/API_SPEC.md`
- `docs/DEPLOYMENT.md`
- `docs/MONITORING.md`
- `docs/TROUBLESHOOTING.md`
- `.env.example`

**Contains**:
- OpenAPI specification
- Deployment runbooks
- Monitoring setup
- Troubleshooting procedures
- Feature flag documentation
- Configuration template

**Depends on**: Stream D (for performance metrics)

---

## 📁 Directory Structure (Post-Phase F)

```
ghl_real_estate_ai/
├── agents/
│   ├── jorge_lead_bot.py ✏️ (Stream B: PDF attachment)
│   ├── jorge_buyer_bot.py ✏️ (Stream A: 4 TODOs)
│   ├── jorge_seller_bot.py ✏️ (Stream C: Feature flags)
│   └── ...
├── services/
│   ├── enhanced_ghl_client.py (reference)
│   ├── event_publisher.py (reference)
│   ├── cma_generator.py (reference)
│   ├── pdf_generator.py ✨ (may create)
│   ├── progressive_skills_manager.py (reference)
│   ├── agent_mesh_coordinator.py (reference)
│   ├── mcp_client.py (reference)
│   └── buyer_error_handler.py ✨ (optional)
├── config/
│   ├── feature_config.py ✨ (Stream C)
│   └── ...
└── ...

tests/
├── agents/
│   ├── test_jorge_lead_bot.py ✏️ (Stream B: add PDF tests)
│   ├── test_jorge_buyer_bot.py ✏️ (Stream A: add error tests)
│   ├── test_jorge_seller_bot.py ✏️ (Stream C: add feature tests)
│   └── ...
├── load/ ✨ (Stream D: NEW)
│   ├── __init__.py
│   └── test_concurrent_load.py
├── integration/ ✨ (Stream D: NEW)
│   ├── __init__.py
│   └── test_full_jorge_flow.py
├── performance/ ✨ (Stream D: NEW)
│   ├── __init__.py
│   └── test_response_times.py
├── fixtures/ ✨ (Stream D: NEW)
│   ├── __init__.py
│   └── test_data.py
├── conftest.py ✏️ (Stream D: enhancement)
└── ...

docs/
├── API_SPEC.md ✨ (Stream E)
├── DEPLOYMENT.md ✏️ (Stream E: enhancement)
├── MONITORING.md ✨ (Stream E)
├── TROUBLESHOOTING.md ✨ (Stream E)
├── FEATURE_FLAGS.md ✨ (Stream C)
├── PERFORMANCE_BASELINE.md ✨ (Stream D)
└── ...

.env.example ✏️ (Stream E: create/update)

Legend:
✏️  = Modify existing file
✨ = Create new file
```

---

## 🔗 Cross-File Dependencies

### Build Order (if sequential)
```
1. DEVELOPMENT_SPEC.md (read)
2. EXECUTION_GUIDE.md (read)
3. STREAM_A_PROMPT.md → jorge_buyer_bot.py + test_jorge_buyer_bot.py
4. STREAM_B_PROMPT.md → lead_bot.py + test_lead_bot.py
5. STREAM_D_PROMPT.md → tests/load/, tests/integration/, tests/performance/
6. STREAM_C_PROMPT.md → feature_config.py + test updates
7. STREAM_E_PROMPT.md → docs/ + .env.example
```

### Integration Points
```
Stream A errors → Stream D tests (edge cases)
Stream B PDF → Stream D tests (performance)
Stream C features → Stream D tests (with features enabled)
Stream D metrics → Stream E docs (referenced in deployment)
```

### Shared References
```
jorge_seller_bot.py:
  - Stream A: Reference error handling patterns
  - Stream C: Enable feature flags
  - Stream D: Test with features enabled

test files:
  - Stream A: Add 6+ error handling tests
  - Stream B: Add 3+ PDF tests
  - Stream C: Add 6+ feature tests
  - Stream D: Add 15+ load/integration/performance tests

docs/:
  - Stream C: Create FEATURE_FLAGS.md
  - Stream D: Create PERFORMANCE_BASELINE.md
  - Stream E: Create API_SPEC.md, DEPLOYMENT.md, etc.
```

---

## 📊 File Complexity Matrix

| File | Complexity | Size | Lines of Code | Existing? |
|------|-----------|------|---------------|-----------|
| jorge_buyer_bot.py | HIGH | 961 | 961 | YES |
| jorge_lead_bot.py | VERY HIGH | 2,269 | 2,269 | YES |
| jorge_seller_bot.py | VERY HIGH | 1,941 | 1,941 | YES |
| feature_config.py | MEDIUM | - | 150-200 | NO |
| pdf_generator.py | MEDIUM | - | 100-150 | NO (maybe) |
| test_concurrent_load.py | MEDIUM | - | 200-300 | NO |
| test_full_jorge_flow.py | MEDIUM | - | 300-400 | NO |
| test_response_times.py | LOW | - | 150-200 | NO |
| API_SPEC.md | MEDIUM | - | 500+ lines | NO |
| DEPLOYMENT.md | MEDIUM | - | 400+ lines | NO |
| MONITORING.md | LOW | - | 300+ lines | NO |
| TROUBLESHOOTING.md | MEDIUM | - | 400+ lines | NO |

**Total New Code**: ~1,000-1,500 lines  
**Total Modified Code**: ~100-200 lines  
**Total Documentation**: ~1,500+ lines

---

## 🧪 Test File Dependencies

```
test_jorge_buyer_bot.py:
  ├── imports: jorge_buyer_bot.py
  ├── uses: BuyerBot class
  ├── mocks: GHL API, Claude API, PropertyMatcher
  └── Stream A: Add 6+ tests for error handling

test_jorge_lead_bot.py:
  ├── imports: lead_bot.py
  ├── uses: LeadBot class
  ├── mocks: CMAGenerator, PDFGenerator, GHL
  └── Stream B: Add 3+ tests for PDF

test_concurrent_load.py (NEW):
  ├── uses: All 3 bots
  ├── mocks: External services
  ├── measures: Response times, errors, throughput
  └── Stream D: Stress test 100+ users

test_full_jorge_flow.py (NEW):
  ├── uses: All 3 bots in sequence
  ├── simulates: Real lead qualification flow
  └── Stream D: End-to-end validation

test_response_times.py (NEW):
  ├── uses: Individual bot response times
  ├── measures: p50, p95, p99 latencies
  └── Stream D: Performance baseline
```

---

## 🔍 Code Search Reference

### Find existing patterns:
```bash
# Find error handling examples
grep -rn "try:" ghl_real_estate_ai/agents/

# Find existing tests
find tests/ -name "*.py" | head -5

# Find PDF handling (if exists)
grep -rn "pdf\|PDF" ghl_real_estate_ai/

# Find feature flags
grep -rn "enable_" ghl_real_estate_ai/agents/

# Find state management
grep -rn "State\|state" ghl_real_estate_ai/services/
```

### Key class locations:
```
BuyerBot: ghl_real_estate_ai/agents/jorge_buyer_bot.py:1
LeadBot: ghl_real_estate_ai/agents/lead_bot.py:1
SellerBot: ghl_real_estate_ai/agents/jorge_seller_bot.py:1
GHLClient: ghl_real_estate_ai/services/enhanced_ghl_client.py
EventPublisher: ghl_real_estate_ai/services/event_publisher.py
```

---

## 📝 Command Reference

### Run by Stream
```bash
# Stream A: Buyer bot tests
pytest tests/agents/test_jorge_buyer_bot.py -v

# Stream B: Lead bot tests
pytest tests/agents/test_lead_bot.py -v

# Stream C: Feature tests (with features enabled)
ENABLE_PROGRESSIVE_SKILLS=true pytest tests/agents/ -v

# Stream D: Load tests
pytest tests/load/ -v -s

# Stream D: Integration tests
pytest tests/integration/ -v -s

# Stream D: Performance tests
pytest tests/performance/ -v -s

# Stream E: Dry run (no actual deploy)
./scripts/deployment_dry_run.sh
```

### Check readiness
```bash
# All tests
pytest tests/ -v

# Coverage report
pytest tests/ --cov=ghl_real_estate_ai --cov-report=html

# Specific coverage
pytest tests/agents/ --cov=ghl_real_estate_ai.agents

# Lint & type check
flake8 ghl_real_estate_ai/ tests/
mypy ghl_real_estate_ai/
```

---

## 📱 Quick Reference Card

### For Stream A Agent
```
File: STREAM_A_PROMPT.md
Work: ghl_real_estate_ai/agents/jorge_buyer_bot.py
Test: tests/agents/test_jorge_buyer_bot.py
Tasks: 4 TODOs + 6 test cases
Time: 2-3 hours
Done when: All tests green + code reviewed
```

### For Stream B Agent
```
File: STREAM_B_PROMPT.md
Work: ghl_real_estate_ai/agents/lead_bot.py:1717
Test: tests/agents/test_lead_bot.py
Tasks: PDF attachment + 3 test cases
Time: 1-2 hours
Done when: PDF <200ms + tests passing
```

### For Stream C Agent
```
File: STREAM_C_PROMPT.md
Work: ghl_real_estate_ai/config/feature_config.py (NEW)
Test: tests/agents/test_jorge_seller_bot.py
Docs: docs/FEATURE_FLAGS.md (NEW)
Tasks: 3 features + tests + docs
Time: 2-4 hours
Done when: All features enabled + docs complete
```

### For Stream D Agent
```
File: STREAM_D_PROMPT.md
Work: tests/load/, tests/integration/, tests/performance/
Docs: docs/PERFORMANCE_BASELINE.md (NEW)
Tasks: 3 test suites + report
Time: 3-4 hours
Done when: 100 users <5% error + report written
```

### For Stream E Agent
```
File: STREAM_E_PROMPT.md
Work: docs/ (5 files) + .env.example
Depends: Stream D (for metrics)
Tasks: API spec + deployment + monitoring + troubleshooting
Time: 2-3 hours
Done when: All docs complete + runbooks tested
```

---

## 🎓 Learning Resources

### If you need help with:

**Error handling in Python**:
- Read: Stream A Prompt section "TODO 1-4"
- Example: `ghl_real_estate_ai/services/enhanced_ghl_client.py` (rate limiting)

**Async/await testing**:
- Read: Stream D Prompt section "Test File Structure"
- Reference: `tests/agents/test_jorge_seller_bot.py`

**Load testing**:
- Read: Stream D Prompt section "Load Testing"
- Tool: `asyncio`, `concurrent.futures.ThreadPoolExecutor`

**PDF generation**:
- Read: Stream B Prompt section "PDF Generation"
- Library: ReportLab (if available) or WeasyPrint

**Feature flags**:
- Read: Stream C Prompt section "Feature Flag Configuration"
- Pattern: Environment variables → configuration classes

**Deployment runbooks**:
- Read: Stream E Prompt section "Deployment Runbook"
- Tool: Kubernetes or Docker Compose

---

## ✅ Verification Checklist

Before considering Phase F complete:

- [ ] Read DEVELOPMENT_SPEC.md (master understanding)
- [ ] Read EXECUTION_GUIDE.md (overall plan)
- [ ] Assign agents to streams (A, B, C, D, E)
- [ ] Each agent reads their stream prompt
- [ ] Stream A & B start (parallel)
- [ ] Stream D infrastructure setup starts
- [ ] After 2 hours: A & B should be complete
- [ ] Stream C & D full execution continues
- [ ] Stream E waits for D baseline
- [ ] All tests passing: `pytest tests/ -v`
- [ ] All docs created and reviewed
- [ ] Code ready for staging deployment
- [ ] Performance validated: <200ms p95
- [ ] Ready for production deployment ✓

---

## 🚀 Next Steps

1. **NOW**: Open `EXECUTION_GUIDE.md`, choose execution strategy
2. **NEXT**: Open `STREAM_A_PROMPT.md` and `STREAM_B_PROMPT.md`
3. **THEN**: Assign agents, start parallel work
4. **MONITOR**: Use checkpoints from EXECUTION_GUIDE.md
5. **COMPLETE**: All 5 streams done, ready to deploy

---

**Questions? Check DEVELOPMENT_SPEC.md for technical details or EXECUTION_GUIDE.md for coordination.**

**Phase F is designed for parallel execution. Use multiple agents in multiple chats simultaneously.**

**Let's build! 🚀**
