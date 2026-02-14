# Wave 7: Agent Prompts for Finalization

Use these prompts in each repo to finalize Wave 7. Each can be run independently.

---

## Prompt 1: ai-orchestrator (Features 1-2)

```
## Task: Finalize Wave 7 — ai-orchestrator

Bead: EnterpriseHub-s2kg

### Context
Two new features are written with tests passing (66 tests):
- `agentforge/workflow_dag.py` — Workflow DAG with conditional routing
- `agentforge/streaming_agent.py` — Streaming ReAct agent responses
- `tests/test_workflow_dag.py` + `tests/test_streaming_agent.py`
- `agentforge/__init__.py` already updated with exports

### Steps
1. `cd /Users/cave/Documents/GitHub/ai-orchestrator`
2. `ruff check agentforge/workflow_dag.py agentforge/streaming_agent.py tests/test_workflow_dag.py tests/test_streaming_agent.py` — verify clean
3. `python3 -m pytest tests/test_workflow_dag.py tests/test_streaming_agent.py -q` — verify 66 pass
4. `git add agentforge/workflow_dag.py agentforge/streaming_agent.py agentforge/__init__.py tests/test_workflow_dag.py tests/test_streaming_agent.py`
5. Commit: `feat: add workflow DAG and streaming agent — Wave 7 (+66 tests)`
6. `git push`

### Pre-existing Issue (ignore)
- 1 test fails: test_perplexity_real_request (Perplexity API auth) — not Wave 7 related
```

---

## Prompt 2: docqa-engine (Features 3-4)

```
## Task: Finalize Wave 7 — docqa-engine

Bead: EnterpriseHub-qhc3

### Context
Two new features with tests passing (56 tests):
- `docqa_engine/context_compressor.py` — Context compression with token budget
- `docqa_engine/benchmark_runner.py` — Retrieval benchmark suite
- `tests/test_context_compressor.py` + `tests/test_benchmark_runner.py`
- `docqa_engine/__init__.py` already updated with exports
- `README.md` modified (staged)

### Steps
1. `cd /Users/cave/Documents/GitHub/docqa-engine`
2. `ruff check docqa_engine/context_compressor.py docqa_engine/benchmark_runner.py tests/test_context_compressor.py tests/test_benchmark_runner.py` — verify clean
3. `python3 -m pytest tests/test_context_compressor.py tests/test_benchmark_runner.py -q` — verify 56 pass
4. `git add docqa_engine/context_compressor.py docqa_engine/benchmark_runner.py docqa_engine/__init__.py tests/test_context_compressor.py tests/test_benchmark_runner.py README.md`
5. Check if `assets/` dir should be staged (may be benchmark data)
6. Commit: `feat: add context compression and retrieval benchmarks — Wave 7 (+56 tests)`
7. `git push`

### Pre-existing Issue (ignore)
- 4 failed + 9 errors in ChromaDB vector store tests — env issue, not Wave 7 related
```

---

## Prompt 3: EnterpriseHub (Features 5-6)

```
## Task: Finalize Wave 7 — EnterpriseHub

Bead: EnterpriseHub-6ag3

### Context
Two new Jorge bot features with tests passing (71 tests):
- `ghl_real_estate_ai/services/jorge/response_evaluator.py` (469 lines) — Bot response quality scoring
- `ghl_real_estate_ai/services/jorge/prompt_experiment_runner.py` (390 lines) — Prompt A/B testing
- `tests/test_response_evaluator.py` (310 lines)
- `tests/test_prompt_experiment_runner.py` (319 lines)

### Steps
1. `cd /Users/cave/Documents/GitHub/EnterpriseHub`
2. `ruff check ghl_real_estate_ai/services/jorge/response_evaluator.py ghl_real_estate_ai/services/jorge/prompt_experiment_runner.py tests/test_response_evaluator.py tests/test_prompt_experiment_runner.py` — verify clean
3. `python3 -m pytest tests/test_response_evaluator.py tests/test_prompt_experiment_runner.py -q` — verify 71 pass
4. `git add ghl_real_estate_ai/services/jorge/response_evaluator.py ghl_real_estate_ai/services/jorge/prompt_experiment_runner.py tests/test_response_evaluator.py tests/test_prompt_experiment_runner.py`
5. Also stage beads: `bd sync`
6. Commit: `feat: add response evaluator and prompt experiment runner — Wave 7 (+71 tests)`
7. `git push`

### Pre-existing Issue (ignore)
- test_decision_tracer.py collection error (import path issue with advanced_rag_system) — not Wave 7
```

---

## Prompt 4: Revenue-Sprint (Features 7-8)

```
## Task: Finalize Wave 7 — Revenue-Sprint

Bead: EnterpriseHub-jahs

### Context
Two new agent features with tests passing (74 tests):
- `portfolio-rag-core/src/agents/cost_aware_proposal.py` — Cost-aware proposal generation
- `portfolio-rag-core/src/agents/proposal_analytics.py` — Proposal performance analytics
- `portfolio-rag-core/src/agents/__init__.py` already updated
- `tests/test_cost_aware_proposal.py` + `tests/test_proposal_analytics.py`
- `README.md` modified (staged)

### Steps
1. `cd /Users/cave/Documents/GitHub/Revenue-Sprint`
2. `ruff check portfolio-rag-core/src/agents/cost_aware_proposal.py portfolio-rag-core/src/agents/proposal_analytics.py tests/test_cost_aware_proposal.py tests/test_proposal_analytics.py` — verify clean
3. `python3 -m pytest tests/test_cost_aware_proposal.py tests/test_proposal_analytics.py -q` — verify 74 pass
4. `git add portfolio-rag-core/src/agents/cost_aware_proposal.py portfolio-rag-core/src/agents/proposal_analytics.py portfolio-rag-core/src/agents/__init__.py tests/test_cost_aware_proposal.py tests/test_proposal_analytics.py README.md`
5. Commit: `feat: add cost-aware proposals and proposal analytics — Wave 7 (+74 tests)`
6. `git push`

### Full regression: 314 pass, 0 fail — clean
```

---

## Prompt 5: jorge_real_estate_bots (Features 9-10)

```
## Task: Finalize Wave 7 — jorge_real_estate_bots

Bead: EnterpriseHub-9hvu

### Context
Two new shared bot features with tests passing (77 tests):
- `bots/shared/funnel_attribution.py` — Multi-touch funnel attribution
- `bots/shared/lead_intelligence_rag.py` — Lead intelligence RAG
- `tests/shared/test_funnel_attribution.py` + `tests/shared/test_lead_intelligence_rag.py`

### IMPORTANT: Fix lint first
```bash
ruff check --fix tests/shared/test_funnel_attribution.py
```
This removes 2 unused imports: STAGE_EVALUATION, STAGE_INTENT

### Steps
1. `cd /Users/cave/Documents/GitHub/jorge_real_estate_bots`
2. `ruff check --fix tests/shared/test_funnel_attribution.py` — fix 2 unused imports
3. `ruff check bots/shared/funnel_attribution.py bots/shared/lead_intelligence_rag.py tests/shared/test_funnel_attribution.py tests/shared/test_lead_intelligence_rag.py` — verify clean
4. `python3 -m pytest tests/shared/test_funnel_attribution.py tests/shared/test_lead_intelligence_rag.py -q` — verify 77 pass
5. `git add bots/shared/funnel_attribution.py bots/shared/lead_intelligence_rag.py tests/shared/test_funnel_attribution.py tests/shared/test_lead_intelligence_rag.py`
6. Commit: `feat: add funnel attribution and lead intelligence RAG — Wave 7 (+77 tests)`
7. `git push`

### Full regression: 356 pass, 0 fail — clean
```

---

## Master Finalization (after all 5 repos shipped)

```
## Task: Close Wave 7 beads and update portfolio totals

1. `cd /Users/cave/Documents/GitHub/EnterpriseHub`
2. Close all beads:
   bd close EnterpriseHub-s2kg EnterpriseHub-qhc3 EnterpriseHub-6ag3 EnterpriseHub-jahs EnterpriseHub-9hvu
   bd close EnterpriseHub-yif5 --reason="Wave 7 shipped: 10 features, 344 tests across 5 repos"
3. `bd sync`
4. Update portfolio-repos.md with new test counts
5. Verify portfolio total: ~6,783+ tests (was ~6,439 pre-Wave 7, target was 8,100+)
```
