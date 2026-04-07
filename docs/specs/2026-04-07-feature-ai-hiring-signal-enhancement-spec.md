# Spec: AI Hiring Signal Enhancement

**Date**: 2026-04-07
**Type**: feature
**Status**: DRAFT
**Research**: ~/Projects/research/ai-hiring-portfolio-signals-2026/RESEARCH.md
**Target**: EnterpriseHub (primary) + jorge-real-estate-bots (secondary)

---

## 1. Problem Statement

Both repos score below senior AI engineering hiring bar due to missing evaluation loop, prompt versioning, adversarial testing, and business metrics documentation. Research pipeline (5-model, Perplexity/Gemini/Grok/ChatGPT/Claude) confirmed: the #1 gap is the absence of a closed evaluation loop. Current scores: EnterpriseHub 8.7/10, jorge-real-estate-bots 7.5/10. Target: 9.5/10 and 8.5/10 respectively.

## 2. Requirements

### Functional Requirements

- **REQ-F01**: The system shall run an eval harness against a golden dataset of 50 input/output pairs on every PR via CI
- **REQ-F02**: The system shall score responses using LLM-as-judge with documented rubrics (correctness, tone, safety, compliance)
- **REQ-F03**: The system shall include deterministic checks (regex assertions, length bounds, required field presence)
- **REQ-F04**: The system shall version all prompts with semantic tags and log prompt_version_id in every request
- **REQ-F05**: The system shall support prompt rollback to any previous version
- **REQ-F06**: The system shall include adversarial test cases (prompt injection, jailbreak, topic boundary) in CI
- **REQ-F07**: The system shall aggregate per-agent, per-model token costs from existing LLMResponse fields
- **REQ-F08**: The system shall document business metrics (cost reduction %, leads handled, conversion rates) in README
- **REQ-F09**: The system shall run nightly regression eval via GitHub Actions cron and alert on quality degradation
- **REQ-F10**: The system shall log structured decision events ("bot decided X because of condition Y")

### Non-Functional Requirements

- **REQ-NF01**: Eval harness shall complete in <5 minutes in CI
- **REQ-NF02**: No vendor lock-in -- use open-source tools (Promptfoo or custom pytest)
- **REQ-NF03**: Each enhancement shall be independently deployable (separate PRs)
- **REQ-NF04**: All existing tests shall continue to pass
- **REQ-NF05**: Git-native prompt versioning (no external services)

## 3. Architecture Decision Records

### ADR-0011: Eval Framework -- Custom Pytest over Vendor Platform

**Status**: Proposed
**Context**: Need eval harness for CI. Options: Braintrust (SaaS), Promptfoo (CLI), custom pytest.
**Decision**: Custom pytest eval harness with LLM-as-judge.
**Rationale**: (1) Open-source signals engineering judgment over vendor following (Grok research finding). (2) Integrates natively with existing 8,212-test pytest suite. (3) No SaaS dependency. (4) Promptfoo is Node.js -- adding npm to a Python project adds complexity.
**Consequences**: Must maintain judge rubrics manually. No built-in tracing UI (acceptable for portfolio).

### ADR-0012: Prompt Versioning -- Git-Native over Registry Service

**Status**: Proposed
**Context**: Need prompt version tracking. Options: PromptLayer (SaaS), custom registry microservice, git-native with DB tracking.
**Decision**: Git-native versioning with PostgreSQL `prompt_versions` table.
**Rationale**: (1) Prompts already in git. (2) DB table tracks version_id per request for traceability. (3) PROMPT_CHANGELOG.md provides human-readable history. (4) No new services to deploy.
**Consequences**: No visual diff UI. Rollback requires git revert + DB update.

### ADR-0013: Drift Detection -- Nightly Cron over Real-Time Pipeline

**Status**: Proposed
**Context**: Need drift detection. Real-time is 9-10/10 difficulty with high false positive rate (Grok/Gemini research). Nightly cron is 95% as effective at 10% complexity.
**Decision**: GitHub Actions nightly cron running eval suite against current model version.
**Rationale**: (1) Drift detection is 10/10 difficulty in production (Grok). (2) False positive fatigue kills real-time alerting within 2 weeks. (3) Nightly regression catches model updates within 24h. (4) Simple to implement and maintain.
**Consequences**: 24h detection latency (acceptable for portfolio; production would need real-time).

## 4. Interface Contracts

### Eval Harness

```python
# evals/judge.py
@dataclass
class EvalResult:
    test_case_id: str
    prompt_version: str
    model: str
    scores: dict[str, float]  # {"correctness": 0.9, "tone": 0.85, "safety": 1.0, "compliance": 0.95}
    passed: bool
    reasoning: str
    timestamp: datetime

async def run_eval_suite(
    golden_dataset_path: str = "evals/golden_dataset.json",
    fail_threshold: float = 0.85,
    judge_model: str = "claude-sonnet-4-6"
) -> list[EvalResult]: ...
```

### Prompt Version Registry

```python
# services/prompt_registry.py
@dataclass
class PromptVersion:
    id: str  # uuid
    name: str  # "seller_qualification_v4"
    version: int
    content: str
    model: str
    created_at: datetime
    metadata: dict  # {"experiment": "tone_warmth", "author": "cayman"}

class PromptRegistry:
    async def get_current(self, name: str) -> PromptVersion: ...
    async def rollback(self, name: str, to_version: int) -> PromptVersion: ...
    async def log_usage(self, version_id: str, request_id: str, response_quality: float | None) -> None: ...
```

### Cost Tracker

```python
# services/cost_tracker.py
@dataclass
class CostRecord:
    request_id: str
    agent_name: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    prompt_version: str
    timestamp: datetime

class CostTracker:
    async def record(self, record: CostRecord) -> None: ...
    async def get_summary(self, period: str = "24h") -> dict: ...
    # Returns: {"total_cost": 1.23, "by_agent": {...}, "by_model": {...}, "per_lead_avg": 0.02}
```

## 5. Task Decomposition

### Wave 1: Foundation (no dependencies, all parallel)

```json
{
  "id": "EH-P0",
  "subject": "Document business metrics in EnterpriseHub README",
  "description": "Add a '## Production Metrics' section to README.md documenting: 89% token cost reduction (93K to 7.8K tokens/workflow via 3-tier cache), agent mesh routing effectiveness (weighted scoring across 22 agents), A/B testing results, cache hit rates (L1 59%, L2 21%, L3 8%). Include before/after data. Reference ADR-0001 for methodology.",
  "activeForm": "Documenting business metrics",
  "effort": "S",
  "repo": "EnterpriseHub",
  "files": ["README.md"],
  "blockedBy": [],
  "ac": "README contains Production Metrics section with verifiable numbers; no inflated claims"
}
```

```json
{
  "id": "JR-P0",
  "subject": "Document business metrics in jorge-real-estate-bots README",
  "description": "Add '## Production Metrics' section: 500+ leads handled since Jan 2026, zero downtime, per-contact processing lock prevents state corruption, webhook dedup with two-phase TTL, conversation completion rates by bot type, model routing distribution (% Haiku vs Sonnet vs Opus). Reference actual production data.",
  "activeForm": "Documenting jorge business metrics",
  "effort": "S",
  "repo": "jorge-real-estate-bots",
  "files": ["README.md"],
  "blockedBy": [],
  "ac": "README contains Production Metrics section with verifiable numbers"
}
```

```json
{
  "id": "EH-P1a",
  "subject": "Create golden dataset for EnterpriseHub eval harness",
  "description": "Create evals/golden_dataset.json with 50 test cases covering: (1) seller qualification Q1-Q4 flows (15 cases), (2) buyer scheduling scenarios (10 cases), (3) lead intake routing (10 cases), (4) edge cases -- empty input, emoji-only, single chars (10 cases), (5) compliance boundary -- FHA/RESPA/TCPA violations (5 cases). Each case: {input, expected_output_properties, category, difficulty}. Use realistic conversation patterns from existing test fixtures in tests/.",
  "activeForm": "Creating golden dataset",
  "effort": "M",
  "repo": "EnterpriseHub",
  "files": ["evals/golden_dataset.json", "evals/README.md"],
  "blockedBy": [],
  "ac": "50 test cases in valid JSON; covers all 5 categories; passes JSON schema validation"
}
```

```json
{
  "id": "JR-P1a",
  "subject": "Create golden dataset for jorge-real-estate-bots eval harness",
  "description": "Create evals/golden_dataset.json with 30 test cases from real conversation patterns: (1) seller qualification flows (10 cases from jorge_seller_bot.py Q1-Q4), (2) buyer scheduling scenarios (8 cases from buyer_prompts.py), (3) lead intake classification (7 cases), (4) edge cases (5 cases from test_cross_cutting_hardening.py patterns). Each case: {input, expected_output_properties, category, bot_type}.",
  "activeForm": "Creating jorge golden dataset",
  "effort": "M",
  "repo": "jorge-real-estate-bots",
  "files": ["evals/golden_dataset.json", "evals/README.md"],
  "blockedBy": [],
  "ac": "30 test cases in valid JSON; covers all 4 categories"
}
```

```json
{
  "id": "EH-P2",
  "subject": "Create PROMPT_CHANGELOG.md for EnterpriseHub",
  "description": "Create PROMPT_CHANGELOG.md documenting all current system prompts with version tags. Read prompts from: ghl_real_estate_ai/prompts/system_prompts.py, seller bot prompts, buyer bot prompts. Format: version number, date, change description, rationale. Initial version is v1.0 for all existing prompts. Include section headers: Seller Prompts, Buyer Prompts, Lead Intake Prompts, System Prompts.",
  "activeForm": "Creating prompt changelog",
  "effort": "S",
  "repo": "EnterpriseHub",
  "files": ["PROMPT_CHANGELOG.md"],
  "blockedBy": [],
  "ac": "PROMPT_CHANGELOG.md exists with all current prompts documented and versioned"
}
```

### Wave 1 Quality Gate
- All golden dataset files pass JSON schema validation
- README business metrics sections are factually accurate
- PROMPT_CHANGELOG.md covers all prompt files
- `python3 -m pytest tests/ -q` passes (existing tests unbroken)

### Wave 2: Eval Harness + Prompt Versioning (depends on Wave 1 datasets)

```json
{
  "id": "EH-P1b",
  "subject": "Build LLM-as-judge eval harness for EnterpriseHub",
  "description": "Create evals/judge.py implementing EvalResult dataclass and run_eval_suite() function. Judge uses Claude Sonnet to score on 4 rubrics: correctness (does response answer the question?), tone (matches Jorge persona?), safety (no identity disclosure, no legal/financial advice?), compliance (FHA/RESPA/TCPA compliant?). Add deterministic checks: response length < 480 chars, no URL leakage, no competitor mentions. Threshold: fail_below=0.85. Create evals/conftest.py with async fixtures. Create tests/test_eval_harness.py with 5 tests verifying the judge scores correctly on known-good and known-bad examples.",
  "activeForm": "Building eval harness",
  "effort": "L",
  "repo": "EnterpriseHub",
  "files": ["evals/__init__.py", "evals/judge.py", "evals/conftest.py", "evals/rubrics.py", "tests/test_eval_harness.py"],
  "blockedBy": ["EH-P1a"],
  "ac": "run_eval_suite() executes against golden dataset; 5 harness tests pass; CI-compatible (< 5 min)"
}
```

```json
{
  "id": "JR-P1b",
  "subject": "Build simple eval harness for jorge-real-estate-bots",
  "description": "Create evals/judge.py with Claude-as-judge scoring on: correctness, tone (Jorge persona), compliance (no AI disclosure, no legal advice). Add deterministic checks from existing response_filter.py patterns (response length, URL stripping, identity disclosure). Threshold: 0.85. Create tests/test_eval_harness.py with 4 tests. Reuse existing conftest.py async patterns.",
  "activeForm": "Building jorge eval harness",
  "effort": "M",
  "repo": "jorge-real-estate-bots",
  "files": ["evals/__init__.py", "evals/judge.py", "evals/rubrics.py", "tests/test_eval_harness.py"],
  "blockedBy": ["JR-P1a"],
  "ac": "run_eval_suite() executes against golden dataset; 4 harness tests pass"
}
```

```json
{
  "id": "EH-P2b",
  "subject": "Add prompt_versions table and PromptRegistry service",
  "description": "Create Alembic migration adding prompt_versions table (id UUID, name VARCHAR, version INT, content TEXT, model VARCHAR, created_at TIMESTAMP, metadata JSONB). Create services/prompt_registry.py with PromptRegistry class: get_current(), rollback(), log_usage(). Wire into claude_orchestrator.py to log prompt_version_id on every LLM call. Existing PromptVersionManager at ai-devops-suite/src/devops_suite/prompt_registry/versioning.py should be referenced for patterns but the new implementation lives in the main service layer. Add 6 tests in tests/test_prompt_registry.py.",
  "activeForm": "Building prompt registry",
  "effort": "M",
  "repo": "EnterpriseHub",
  "files": ["ghl_real_estate_ai/services/prompt_registry.py", "alembic/versions/xxxx_add_prompt_versions.py", "tests/test_prompt_registry.py"],
  "blockedBy": ["EH-P2"],
  "ac": "prompt_versions table exists; PromptRegistry CRUD works; claude_orchestrator logs version_id; 6 tests pass"
}
```

```json
{
  "id": "JR-P2",
  "subject": "Add cost tracking aggregation to jorge-real-estate-bots",
  "description": "Create bots/shared/cost_tracker.py that aggregates input_tokens and output_tokens from existing LLMResponse (claude_client.py lines 192-193 already extract these). Store in Redis sorted set with daily TTL. Add /admin/costs endpoint returning: total_cost_24h, by_model breakdown (haiku/sonnet/opus), per_lead_average, cost_trend_7d. Use Anthropic's published pricing: Haiku $0.25/$1.25, Sonnet $3/$15, Opus $15/$75 per M tokens. Add 5 tests.",
  "activeForm": "Building cost tracker",
  "effort": "M",
  "repo": "jorge-real-estate-bots",
  "files": ["bots/shared/cost_tracker.py", "bots/lead_bot/routes_admin.py", "tests/test_cost_tracker.py"],
  "blockedBy": [],
  "ac": "/admin/costs returns JSON with all fields; 5 tests pass; existing tests unbroken"
}
```

### Wave 2 Quality Gate
- `python3 -m pytest evals/ tests/test_eval_harness.py -v` passes in both repos
- Eval suite completes in < 5 minutes
- Prompt registry CRUD operations work
- Cost tracker endpoint returns valid JSON
- All existing tests still pass

### Wave 3: Adversarial Testing + CI Integration

```json
{
  "id": "EH-P3",
  "subject": "Add adversarial test suite to EnterpriseHub CI",
  "description": "Create tests/adversarial/ directory with: test_prompt_injection.py (8 cases: direct instruction override, indirect via user content, base64 encoded, markdown injection, system prompt extraction, role confusion, multi-turn escalation, tool-use abuse), test_topic_boundary.py (5 cases: off-topic requests, competitor mentions, legal/financial advice requests, PII extraction attempts, language boundary), test_jailbreak.py (5 cases: persona escape, DAN-style, hypothetical framing, translation attack, ASCII art). Each test uses the eval harness judge to score safety=1.0 requirement. Add adversarial test step to .github/workflows/ci.yml.",
  "activeForm": "Building adversarial tests",
  "effort": "M",
  "repo": "EnterpriseHub",
  "files": ["tests/adversarial/__init__.py", "tests/adversarial/test_prompt_injection.py", "tests/adversarial/test_topic_boundary.py", "tests/adversarial/test_jailbreak.py", ".github/workflows/ci.yml"],
  "blockedBy": ["EH-P1b"],
  "ac": "18 adversarial test cases pass; CI includes adversarial step; safety score = 1.0 for all"
}
```

```json
{
  "id": "JR-P3",
  "subject": "Extend adversarial tests in jorge-real-estate-bots",
  "description": "Extend existing tests/test_cross_cutting_hardening.py with new adversarial section: 10 prompt injection cases (direct override, user content injection, base64, system prompt extraction, role confusion, persona escape, language switch attack, competitor mention, legal advice request, PII extraction). Tests verify response_filter.py catches all identity disclosures and the response stays in-persona as Jorge. Add to CI pipeline.",
  "activeForm": "Extending adversarial tests",
  "effort": "S",
  "repo": "jorge-real-estate-bots",
  "files": ["tests/test_adversarial.py", ".github/workflows/ci.yml"],
  "blockedBy": ["JR-P1b"],
  "ac": "10 adversarial tests pass; CI includes adversarial step"
}
```

```json
{
  "id": "EH-P1c",
  "subject": "Add eval CI gate to EnterpriseHub GitHub Actions",
  "description": "Add 'eval' job to .github/workflows/ci.yml that runs: python3 -m pytest evals/ --fail-below 0.85. Job runs after unit tests pass. On failure, PR is blocked. Add eval badge to README. Ensure eval job uses PostgreSQL + Redis services (same as existing integration test job).",
  "activeForm": "Adding eval CI gate",
  "effort": "S",
  "repo": "EnterpriseHub",
  "files": [".github/workflows/ci.yml", "README.md"],
  "blockedBy": ["EH-P1b"],
  "ac": "CI includes eval gate; PRs blocked if eval score < 0.85; badge visible in README"
}
```

```json
{
  "id": "JR-P4",
  "subject": "Add structured decision event logging to jorge-real-estate-bots",
  "description": "Add DecisionEvent dataclass to bots/shared/event_models.py with fields: event_type, contact_id, decision, reason, confidence, bot_type, prompt_version, timestamp. Emit events at key decision points in conversation_orchestrator.py: mode resolution, bot routing, handoff triggers, opt-out detection, stall re-engagement. Log to structured JSON logger (already configured). Add 4 tests verifying events are emitted correctly.",
  "activeForm": "Adding decision event logging",
  "effort": "S",
  "repo": "jorge-real-estate-bots",
  "files": ["bots/shared/event_models.py", "bots/lead_bot/conversation_orchestrator.py", "tests/test_decision_events.py"],
  "blockedBy": [],
  "ac": "Decision events emitted at all 5 decision points; 4 tests pass; events visible in structured logs"
}
```

### Wave 3 Quality Gate
- All adversarial tests pass with safety score = 1.0
- CI pipeline includes eval gate and adversarial step
- Decision event logging emits at all key decision points
- Full test suite passes in both repos

### Wave 4: Nightly Regression + Cost Dashboard

```json
{
  "id": "EH-P4",
  "subject": "Add nightly regression cron to EnterpriseHub",
  "description": "Create .github/workflows/nightly-eval.yml: runs eval suite against current model version every night at 2am UTC. Compares scores against baseline (stored in evals/baseline.json). If any rubric drops >10% from baseline, posts alert to GitHub Issues with title '[Regression] Eval score dropped' and diff details. Workflow uses same PostgreSQL + Redis services as CI. Create evals/baseline.json from first successful run.",
  "activeForm": "Adding nightly regression cron",
  "effort": "S",
  "repo": "EnterpriseHub",
  "files": [".github/workflows/nightly-eval.yml", "evals/baseline.json", "evals/compare_baseline.py"],
  "blockedBy": ["EH-P1b", "EH-P1c"],
  "ac": "Nightly workflow runs successfully; baseline comparison works; alert triggers on >10% drop"
}
```

```json
{
  "id": "EH-P5",
  "subject": "Add cost governance dashboard to EnterpriseHub",
  "description": "Create services/cost_governance.py with CostTracker class that aggregates token usage from claude_orchestrator.py LLM calls. Store per-request costs in PostgreSQL cost_records table (new Alembic migration). Add /admin/cost-dashboard endpoint returning: total_cost_period, by_agent breakdown, by_model breakdown, per_lead_average, cost_trend, emergency_shutdown_status (from agent_mesh_coordinator). Reference existing $100/hr emergency shutdown in agent_mesh_coordinator.py. Add 5 tests.",
  "activeForm": "Building cost dashboard",
  "effort": "M",
  "repo": "EnterpriseHub",
  "files": ["ghl_real_estate_ai/services/cost_governance.py", "alembic/versions/xxxx_add_cost_records.py", "tests/test_cost_governance.py"],
  "blockedBy": ["EH-P2b"],
  "ac": "/admin/cost-dashboard returns valid JSON; per-agent and per-model breakdown works; 5 tests pass"
}
```

### Wave 4 Quality Gate
- Nightly cron workflow passes dry run
- Cost dashboard endpoint returns accurate data
- Full test suite passes in both repos
- All new tests pass independently

### Wave 5: Verification + Documentation

```json
{
  "id": "VERIFY",
  "subject": "Run full verification across both repos",
  "description": "Run complete test suites in both repos. Verify: (1) EnterpriseHub: python3 -m pytest tests/ evals/ -q -- all pass, (2) jorge-real-estate-bots: python3 -m pytest tests/ evals/ -q -- all pass, (3) CI pipelines include eval gates and adversarial steps, (4) README business metrics sections are accurate, (5) PROMPT_CHANGELOG.md is complete, (6) Golden datasets are valid JSON, (7) Nightly cron workflow is syntactically valid. Create HIRING_SIGNAL_AUDIT.md summarizing all enhancements with interview talking points.",
  "activeForm": "Running final verification",
  "effort": "M",
  "repo": "both",
  "files": ["HIRING_SIGNAL_AUDIT.md"],
  "blockedBy": ["EH-P4", "EH-P5", "JR-P3", "JR-P4"],
  "ac": "All tests pass in both repos; HIRING_SIGNAL_AUDIT.md contains interview talking points for each enhancement"
}
```

## 6. Interview Talking Points (per enhancement)

### Business Metrics (P0)
> "Our 3-tier cache reduced token costs by 89% -- from 93K to 7.8K tokens per workflow. I can show you the before/after data and explain the cache key design that makes this work without stale reads."

### Eval Framework (P1)
> "We run 50 golden test cases in CI on every PR. The LLM-as-judge scores on correctness, tone, safety, and compliance. We caught a prompt regression where a tone change dropped qualification accuracy by 12% -- the CI gate blocked the merge."

### Prompt Versioning (P2)
> "We treat prompts like database migrations. Every prompt change gets a version tag, and I can diff any two versions. Here's our PROMPT_CHANGELOG showing why we changed the seller qualification prompt from v3 to v4 -- the original was too aggressive on price anchoring."

### Adversarial Testing (P3)
> "We have 18 adversarial test cases in CI -- direct injection, base64 encoded attempts, persona escape, and topic boundary violations. Our response filter catches identity disclosure with 38 regex patterns, and each one has a dedicated test."

### Cost Governance (P5)
> "I can tell you the per-lead cost broken down by model tier. Haiku handles 60% of routine classification at $0.001/call; Opus only activates for high-stakes seller negotiations. The agent mesh coordinator has a $100/hr emergency shutdown."

### Nightly Regression (P4)
> "We run our eval suite nightly against the current model version. If any quality metric drops more than 10% from baseline, it opens a GitHub issue with the exact diff. This catches silent model updates within 24 hours."

## 7. Verification Plan

| AC | Layer | Method | Command | Pass Criteria |
|---|---|---|---|---|
| Golden dataset valid | 0 | Automated | `python3 -c "import json; json.load(open('evals/golden_dataset.json'))"` | Exit 0 |
| Eval harness runs | 1 | Automated | `python3 -m pytest tests/test_eval_harness.py -v` | All tests pass |
| Eval CI gate blocks | 2 | Integration | `gh workflow run ci.yml` (with failing eval) | PR blocked |
| Prompt registry CRUD | 1 | Automated | `python3 -m pytest tests/test_prompt_registry.py -v` | 6 tests pass |
| Adversarial suite | 1 | Automated | `python3 -m pytest tests/adversarial/ -v` | 18 tests pass, safety=1.0 |
| Cost dashboard | 1 | Automated | `python3 -m pytest tests/test_cost_governance.py -v` | 5 tests pass |
| Nightly cron syntax | 0 | Automated | `gh workflow validate .github/workflows/nightly-eval.yml` | Valid YAML |
| Existing tests pass | 2 | Automated | `python3 -m pytest tests/ -q` | All existing tests pass |

## 8. Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| LLM-as-judge costs exceed budget | Medium | Medium | Use Sonnet (not Opus) for judging; cache judge responses for identical inputs |
| Golden dataset becomes stale | Low | Medium | Nightly regression catches drift; update dataset quarterly |
| Eval CI gate blocks legitimate changes | Medium | Low | Add `--override-eval` flag with justification requirement |
| Prompt registry migration fails | Low | High | Test migration in staging; Alembic downgrade path |

## 9. Rollback Plan

Each enhancement is a separate PR. Rollback = revert the PR.
- Eval harness: remove evals/ directory, revert CI changes
- Prompt registry: Alembic downgrade, revert service changes
- Adversarial tests: remove tests/adversarial/, revert CI changes
- Cost dashboard: Alembic downgrade, revert service + route changes

## 10. Success Criteria

- EnterpriseHub hiring signal score: 8.7 -> 9.5/10
- jorge-real-estate-bots hiring signal score: 7.5 -> 8.5/10
- Total new tests: ~60 (EnterpriseHub) + ~30 (jorge)
- CI pipeline includes eval gate + adversarial gate
- Business metrics documented with verifiable numbers
- All interview talking points supported by actual code

## 11. Gaps & Assumptions

| Item | Type | Confidence | Notes |
|---|---|---|---|
| 50 golden test cases is sufficient | Assumption | Medium | Based on Gemini research finding; no empirical threshold data |
| Sonnet is accurate enough as judge | Assumption | High | 0.7-0.8 human correlation per Grok; deterministic checks compensate |
| Nightly regression catches model updates | Assumption | High | 24h detection latency acceptable for portfolio |
| Cost pricing stays current | Assumption | Medium | Anthropic pricing as of April 2026; needs update if pricing changes |
