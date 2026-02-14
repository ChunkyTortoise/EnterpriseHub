# Wave 7: Feature Specifications & Finalization Guide

**Status**: Code + tests written across all 5 repos. Needs lint fix, commit, push.
**Total New Tests**: 344 (exceeds ~272 estimate)
**Beads Master**: EnterpriseHub-yif5

---

## Current State (as of 2026-02-09)

### Verification Results

| Repo | Bead ID | New Tests | Status | Lint | Remaining |
|------|---------|-----------|--------|------|-----------|
| ai-orchestrator | EnterpriseHub-s2kg | 66 pass | Code ready | Clean | Commit + push |
| docqa-engine | EnterpriseHub-qhc3 | 56 pass | Code ready | Clean | Commit + push |
| EnterpriseHub | EnterpriseHub-6ag3 | 71 pass | Code ready | Clean | Commit + push |
| Revenue-Sprint | EnterpriseHub-jahs | 74 pass | Code ready | Clean | Commit + push |
| jorge_real_estate_bots | EnterpriseHub-9hvu | 77 pass | Code ready | 2 unused imports | Fix lint, commit + push |

### Pre-existing Issues (NOT Wave 7)
- **ai-orchestrator**: 1 failed test (Perplexity auth HTTP 401) — API key issue
- **docqa-engine**: 4 failed + 9 errors (ChromaDB vector store) — env issue
- **EnterpriseHub**: test_decision_tracer.py collection error — import path issue with `advanced_rag_system/src/__init__.py`

---

## Feature Specifications

### Feature 1: Workflow DAG (ai-orchestrator)
- **File**: `agentforge/workflow_dag.py` (new)
- **Tests**: `tests/test_workflow_dag.py` (~34 tests)
- **Cert**: IBM RAG & Agentic AI
- **Components**: WorkflowNode, WorkflowEdge, WorkflowDAG, DAGExecutor
- **Key**: Conditional routing on confidence/metrics, cycle detection, memoization

### Feature 2: Streaming Agent (ai-orchestrator)
- **File**: `agentforge/streaming_agent.py` (new)
- **Tests**: `tests/test_streaming_agent.py` (~32 tests)
- **Cert**: Duke LLMOps
- **Components**: StreamingReActAgent, AgentStreamEvent, StreamAggregator
- **Key**: Async generator yielding thought/action/observation/final events

### Feature 3: Context Compression (docqa-engine)
- **File**: `docqa_engine/context_compressor.py` (new)
- **Tests**: `tests/test_context_compressor.py` (~29 tests)
- **Cert**: Duke LLMOps
- **Components**: ContextCompressor, CompressedContext, TokenBudgetManager, Budget
- **Key**: Extractive (TF-IDF), truncation, token-ratio methods

### Feature 4: Retrieval Benchmark Suite (docqa-engine)
- **File**: `docqa_engine/benchmark_runner.py` (new)
- **Tests**: `tests/test_benchmark_runner.py` (~27 tests)
- **Cert**: IBM RAG & Agentic AI
- **Components**: BenchmarkSuite, BenchmarkResult, BenchmarkRegistry
- **Key**: MRR, NDCG@k, precision@k, recall@k metrics

### Feature 5: Response Evaluator (EnterpriseHub)
- **File**: `ghl_real_estate_ai/services/jorge/response_evaluator.py` (469 lines)
- **Tests**: `tests/test_response_evaluator.py` (310 lines)
- **Cert**: IBM GenAI Engineering
- **Components**: ResponseScore, ResponseEvaluator, per-bot tone profiles
- **Key**: Coherence, relevance, completeness, tone scoring

### Feature 6: Prompt Experiment Runner (EnterpriseHub)
- **File**: `ghl_real_estate_ai/services/jorge/prompt_experiment_runner.py` (390 lines)
- **Tests**: `tests/test_prompt_experiment_runner.py` (319 lines)
- **Cert**: Duke LLMOps
- **Components**: PromptExperiment, ExperimentResult, PromptExperimentRunner
- **Key**: Deterministic hash assignment, z-test significance, early stopping

### Feature 7: Cost-Aware Proposal Generation (Revenue-Sprint)
- **File**: `portfolio-rag-core/src/agents/cost_aware_proposal.py` (new)
- **Tests**: `tests/test_cost_aware_proposal.py` (~37 tests)
- **Cert**: Duke LLMOps
- **Components**: ProposalBudget, CostAwareProposalAgent, ProposalCostTracker
- **Key**: Token budget enforcement, graceful degradation to template

### Feature 8: Proposal Performance Analytics (Revenue-Sprint)
- **File**: `portfolio-rag-core/src/agents/proposal_analytics.py` (new)
- **Tests**: `tests/test_proposal_analytics.py` (~37 tests)
- **Cert**: Google Analytics
- **Components**: ProposalOutcome, ProposalAnalytics, ABComparison
- **Key**: Acceptance rates, category stats, z-test A/B comparison

### Feature 9: Funnel Attribution Tracker (jorge_real_estate_bots)
- **File**: `bots/shared/funnel_attribution.py` (new)
- **Tests**: `tests/shared/test_funnel_attribution.py` (~40 tests)
- **Cert**: Google Analytics
- **Components**: FunnelEvent, FunnelTracker, AttributionModel, FunnelReport
- **Key**: First-touch, last-touch, linear, time-decay attribution

### Feature 10: Lead Intelligence RAG (jorge_real_estate_bots)
- **File**: `bots/shared/lead_intelligence_rag.py` (new)
- **Tests**: `tests/shared/test_lead_intelligence_rag.py` (~37 tests)
- **Cert**: IBM RAG & Agentic AI
- **Components**: LeadEmbedding, LeadIntelligenceRAG, RAGContext
- **Key**: Hybrid keyword + TF-IDF cosine similarity search

---

## Finalization Checklist Per Repo

### Each repo needs:
1. [ ] Fix any ruff lint issues (`ruff check --fix`)
2. [ ] Run new feature tests: `pytest <test_files> -q`
3. [ ] Run full regression: `pytest --tb=short -q`
4. [ ] Verify __init__.py exports include new features
5. [ ] `git add <new_files> <modified_files>`
6. [ ] `git commit -m "feat: add Wave 7 features — <feature names> (+N tests)"`
7. [ ] `git push`

### Repo-specific files to stage:

**ai-orchestrator** (EnterpriseHub-s2kg):
```
git add agentforge/workflow_dag.py agentforge/streaming_agent.py \
  agentforge/__init__.py tests/test_workflow_dag.py tests/test_streaming_agent.py
```

**docqa-engine** (EnterpriseHub-qhc3):
```
git add docqa_engine/context_compressor.py docqa_engine/benchmark_runner.py \
  docqa_engine/__init__.py tests/test_context_compressor.py tests/test_benchmark_runner.py
```

**EnterpriseHub** (EnterpriseHub-6ag3):
```
git add ghl_real_estate_ai/services/jorge/response_evaluator.py \
  ghl_real_estate_ai/services/jorge/prompt_experiment_runner.py \
  tests/test_response_evaluator.py tests/test_prompt_experiment_runner.py
```

**Revenue-Sprint** (EnterpriseHub-jahs):
```
git add portfolio-rag-core/src/agents/cost_aware_proposal.py \
  portfolio-rag-core/src/agents/proposal_analytics.py \
  portfolio-rag-core/src/agents/__init__.py \
  tests/test_cost_aware_proposal.py tests/test_proposal_analytics.py
```

**jorge_real_estate_bots** (EnterpriseHub-9hvu):
```
ruff check --fix tests/shared/test_funnel_attribution.py
git add bots/shared/funnel_attribution.py bots/shared/lead_intelligence_rag.py \
  tests/shared/test_funnel_attribution.py tests/shared/test_lead_intelligence_rag.py
```

---

## Post-Wave 7 Portfolio Totals (Expected)

| Repo | Before | Wave 7 | After |
|------|--------|--------|-------|
| ai-orchestrator | 423 | +66 | ~489 |
| docqa-engine | 501 | +56 | ~557 |
| EnterpriseHub | ~4,996 | +71 | ~5,067 |
| Revenue-Sprint | 240 | +74 | ~314 |
| jorge_real_estate_bots | 279 | +77 | ~356 |
| **Total** | **~6,439** | **+344** | **~6,783** |

---

## Continuation Prompts

See `wave7-prompts.md` for per-agent prompts to finalize each repo.
