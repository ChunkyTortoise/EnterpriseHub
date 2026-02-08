# Portfolio Expansion Spec — February 2026

**Target**: 6 projects, +334 tests, 2 new repos, portfolio total 5,500+ → 5,800+ tests

---

## Overview

| # | Repo | Type | Bead ID | Tests | Status |
|---|------|------|---------|-------|--------|
| 1 | insight-engine | Enhancement | `EnterpriseHub-sxc` | +74 | Existing (76 tests) |
| 2 | docqa-engine | Enhancement + Fix | `EnterpriseHub-ywj` | +36 | Existing (152 pass, 5 fail) |
| 3 | ai-orchestrator | Enhancement | `EnterpriseHub-ge6` | +42 | Existing (109 pass) |
| 4 | scrape-and-serve | Enhancement + New Module | `EnterpriseHub-ct9` | +40 | Existing (93 tests) |
| 5 | prompt-engineering-lab | **New Repo** | `EnterpriseHub-2s9` | ~66 | Greenfield |
| 6 | llm-integration-starter | **New Repo** | `EnterpriseHub-can` | ~76 | Greenfield |

---

## Execution Strategy

### Agent Teams (3 parallel groups)

**Group A — Existing Repo Enhancements (4 repos)**
Each repo gets a dedicated agent:
- Agent A1: insight-engine (+74 tests)
- Agent A2: docqa-engine (fix 5 + add 36)
- Agent A3: ai-orchestrator (+42 tests)
- Agent A4: scrape-and-serve (+40 tests)

**Group B — New Repo: prompt-engineering-lab**
- Agent B1: Scaffold + core modules
- Agent B2: Tests + CI

**Group C — New Repo: llm-integration-starter**
- Agent C1: Scaffold + core modules
- Agent C2: Tests + CI

### Sequencing
1. **Phase 1**: Group A (all 4 in parallel) — enhance existing repos
2. **Phase 2**: Group B + C (parallel) — build new repos
3. **Phase 3**: Portfolio site update (add 2 new project cards)
4. **Phase 4**: Memory/beads sync + push all

---

## Project 1: insight-engine (+74 tests)

**Bead**: `EnterpriseHub-sxc`
**Path**: `/Users/cave/Documents/GitHub/insight-engine`
**Current**: 76 tests, 11 modules (profiler, cleaner, predictor, attribution, anomaly_detector, dashboard_generator, report_generator, forecaster, clustering, feature_lab)

### What Exists
- `insight_engine/forecaster.py` — Time series forecasting (ARIMA-like, trend decomposition)
- `insight_engine/clustering.py` — K-means, DBSCAN, silhouette scoring
- `insight_engine/feature_lab.py` — Feature engineering (encoding, scaling, interactions)
- Test files exist for all three but need expansion

### New Tests (74 total)

**test_forecaster.py** (+25 tests):
- Trend detection (upward, downward, flat, seasonal)
- Forecast horizon (1-step, multi-step, full range)
- Missing data handling (gaps, NaN, short series)
- Confidence intervals (width, symmetry, coverage)
- Decomposition components (trend, seasonal, residual)
- Edge cases (constant series, single point, negative values)
- Multiple frequency support (daily, weekly, monthly)

**test_clustering.py** (+25 tests):
- K-means (k=2,3,5, convergence, random seed reproducibility)
- DBSCAN (eps/min_samples tuning, noise detection, single cluster)
- Silhouette score (perfect clusters, overlapping, single cluster)
- Elbow method (optimal k detection, flat curve)
- Cluster assignment (new point assignment, boundary points)
- Edge cases (empty dataset, single point, all identical, high dimensional)
- Mixed dtypes (numeric only validation)

**test_feature_lab.py** (+24 tests):
- One-hot encoding (categorical, high cardinality, unknown categories)
- Label encoding (ordered categories, consistency)
- Standard scaling (mean=0 std=1, inverse transform)
- Min-max scaling (range [0,1], custom range, zero-variance)
- Interaction features (pairwise products, polynomial)
- Datetime features (year, month, day, hour, day_of_week)
- Missing value indicators (binary flags)
- Feature selection (variance threshold, correlation filter)

### Implementation Notes
- All tests must be pure unit tests (no external dependencies)
- Use `numpy` and `pandas` fixtures from conftest
- Follow existing test patterns (class-based, descriptive method names)

---

## Project 2: docqa-engine (fix 5 + add 36 tests)

**Bead**: `EnterpriseHub-ywj`
**Path**: `/Users/cave/Documents/GitHub/docqa-engine`
**Current**: 152 passing, 5 failing

### Fix 5 Failing Tests
1. `test_chunking.py::TestFixedSize::test_short_text` — Assertion threshold
2. `test_chunking.py::TestSlidingWindow::test_full_overlap` — Assertion logic
3. `test_citation_scorer.py::TestSingleCitation::test_relevance_with_query` — `> 0.5` should be `>= 0.5`
4. `test_evaluator.py::TestContextRelevancy::test_relevant_context` — `> 0.3` threshold too high for TF-IDF
5. `test_evaluator.py::TestAnswerRelevancy::test_relevant_answer` — `> 0.2` threshold too high

### New Tests (+36)

**test_chunking.py** (+12 tests):
- Fixed-size chunking (exact split, remainder handling, unicode)
- Sliding window (overlap calculation, step size, window coverage)
- Sentence-based chunking (period splitting, abbreviation handling)
- Paragraph-based chunking (double newline, mixed separators)
- Edge cases (empty string, single char, very long text, no separators)
- Chunk metadata (offset tracking, chunk_id uniqueness)

**test_citation_scorer.py** (+12 tests):
- Faithfulness scoring (exact match, partial match, hallucinated)
- Relevance scoring (on-topic, off-topic, partial relevance)
- Multi-citation scoring (batch processing, aggregation)
- Edge cases (empty citation, empty source, very long texts)
- Score bounds (always 0.0-1.0, deterministic)
- With/without query context (query boost verification)

**test_evaluator.py** (+12 tests):
- Context precision (highly precise, mixed quality, irrelevant)
- Context recall (full coverage, partial, zero)
- Answer correctness (exact match, semantic match, wrong)
- Faithfulness metric (grounded, ungrounded, mixed)
- RAGAS-style composite score (end-to-end pipeline)
- Edge cases (empty answer, empty context, very short texts)

### Implementation Notes
- Adjust thresholds with `>=` instead of `>` where TF-IDF similarity produces exact boundary values
- Use `pytest.approx` for floating-point comparisons where appropriate

---

## Project 3: ai-orchestrator (+42 tests)

**Bead**: `EnterpriseHub-ge6`
**Path**: `/Users/cave/Documents/GitHub/ai-orchestrator`
**Current**: 109 passing, 1 integration failure, 4 skipped | 2,370 LOC

### New Tests (+42)

**test_tools.py** (+14 tests):
- Async handler execution (async function as tool handler)
- Tool parameter validation (missing required, extra params)
- Batch execution with mixed results (some succeed, some fail)
- Tool dependency chains (tool A output feeds tool B)
- Large parameter schemas (nested objects, arrays)
- Claude format round-trip (to_claude → parse → execute)
- OpenAI format round-trip (to_openai → parse → execute)
- Empty/malformed tool call responses

**test_prompt_template.py** (+14 tests):
- Conditional rendering ({{#if}} blocks if supported, else test partial with missing vars)
- Template composition (combine two templates)
- Variable type coercion (int, float, list rendering)
- Template inheritance (extend base template)
- Large template rendering (100+ variables)
- Registry persistence (add, get, list, overwrite)
- Render with extra variables (ignored gracefully)
- Missing variable error messages (clear, actionable)

**test_rate_limiter.py** (+14 tests):
- Concurrent access safety (asyncio.gather with 50 acquires)
- Burst capacity (fill to max, drain, refill timing)
- Multiple limiters (per-provider rate limiting)
- Zero-capacity edge case
- Negative capacity rejection
- Time-based refill accuracy (verify token regeneration rate)
- Async context manager usage
- Integration with retry decorator (rate limit → backoff → retry)

### Implementation Notes
- Use `pytest-asyncio` for async tests
- Mock `time.monotonic()` for rate limiter timing tests
- All tests must pass without API keys (mock provider only)

---

## Project 4: scrape-and-serve (+40 tests)

**Bead**: `EnterpriseHub-ct9`
**Path**: `/Users/cave/Documents/GitHub/scrape-and-serve`
**Current**: 93 tests (scheduler.py has 0 tests — critical gap!)

### New Test File: test_scheduler.py (+15 tests)
- `test_add_job` — Job registration returns name
- `test_remove_job` — Task cancellation, status cleanup
- `test_on_change_callback` — Callback invocation on change
- `test_run_once` — Single execution, status update
- `test_run_once_error` — Exception handling in run
- `test_get_status` — Individual job status query
- `test_get_all_status` — Aggregate status
- `test_disabled_job_skipped` — enabled=False not scheduled
- `test_job_not_found` — KeyError on unknown job
- `test_callback_error_handling` — Callback exceptions don't crash scheduler
- `test_multiple_jobs` — Register 3+ jobs
- `test_status_counts` — total_jobs, active_jobs, total_runs accuracy
- `test_schedule_config_defaults` — Default interval_seconds=3600
- `test_start_stop_lifecycle` — Start sets _running, stop clears
- `test_run_count_increments` — Each run_once increments count

### Enhanced test_seo_content.py (+10 tests)
- `test_readability_empty_text` — Edge case
- `test_score_content_no_headings` — Missing heading penalty
- `test_score_content_meta_too_long` — >160 chars penalty
- `test_score_content_meta_too_short` — <50 chars penalty
- `test_score_content_title_bounds` — Title length checks
- `test_outline_single_keyword` — One keyword
- `test_keyword_density_zero_matches` — Not found
- `test_readability_very_long_sentences` — Paragraph sentences
- `test_score_content_max_100` — Score capped
- `test_analyze_keyword_no_title` — Title not provided

### New Module + Tests: validators.py (+15 tests)

**New file**: `scrape_and_serve/validators.py` (~150 LOC)

```python
@dataclass
class ValidationResult:
    valid: bool
    issues: list[str]
    warnings: list[str]

def validate_scrape_result(result: ScrapeResult) -> ValidationResult: ...
def validate_price_data(points: list[PricePoint]) -> ValidationResult: ...
def validate_config(config: dict) -> ValidationResult: ...
def validate_url(url: str) -> bool: ...
def validate_css_selector(selector: str) -> bool: ...
```

**test_validators.py** (+15 tests):
- `test_valid_scrape_result` — No issues
- `test_empty_items` — Flag empty results
- `test_missing_required_fields` — Missing field detection
- `test_valid_price_data` — Clean data passes
- `test_price_range_violation` — Negative price
- `test_price_spike_warning` — >50% change warning
- `test_valid_config` — Clean YAML passes
- `test_config_missing_url` — Required field
- `test_config_short_interval` — <30s warning
- `test_valid_url` — Good URL passes
- `test_invalid_url` — Bad URL fails
- `test_valid_css_selector` — `.class #id` passes
- `test_empty_css_selector` — Empty string fails
- `test_duplicate_items` — Hash-based duplicate detection
- `test_chronological_order` — Timestamp ordering check

---

## Project 5: prompt-engineering-lab (~66 tests) — NEW REPO

**Bead**: `EnterpriseHub-2s9`
**Path**: `/Users/cave/Documents/GitHub/prompt-engineering-lab` (to create)

### Architecture
Composable prompt engineering toolkit: strategies, evaluation, safety, optimization.

### Package Structure
```
promptlab/
├── __init__.py
├── cli.py                    # Click CLI (render, eval, scan, compare)
├── core/
│   ├── template.py           # Jinja2-based PromptTemplate
│   ├── variable.py           # TypedVariable with constraints
│   ├── message.py            # Message, Conversation
│   └── version.py            # VersionedPrompt with diff/rollback
├── strategies/
│   ├── base.py               # BaseStrategy ABC
│   ├── zero_shot.py          # ZeroShotStrategy
│   ├── few_shot.py           # FewShotStrategy (dynamic example selection)
│   ├── chain_of_thought.py   # CoT (zero-shot + manual)
│   ├── self_consistency.py   # Multi-path + majority vote
│   ├── tree_of_thought.py    # BFS/DFS thought exploration
│   ├── react.py              # Reason + Act loop
│   └── meta_prompt.py        # Prompt-that-writes-prompts
├── chains/
│   ├── pipeline.py           # Sequential chain
│   ├── router.py             # Conditional branching
│   ├── parallel.py           # Fan-out/fan-in
│   └── transform.py          # Output parsing/reshaping
├── evaluation/
│   ├── evaluator.py          # Orchestrator
│   ├── metrics.py            # ExactMatch, Contains, Regex, SemanticSimilarity
│   ├── rubric.py             # LLM-as-judge (G-Eval style)
│   ├── dataset.py            # EvalDataset from JSONL/CSV
│   └── report.py             # EvalReport with pass_rate
├── safety/
│   ├── injection.py          # Prompt injection detection
│   ├── pii.py                # PII scanning + redaction
│   ├── guardrails.py         # Output validation
│   └── sanitizer.py          # Input normalization
├── providers/
│   ├── base.py               # BaseLLMProvider ABC
│   ├── mock.py               # MockProvider (deterministic)
│   └── replay.py             # ReplayProvider (recorded responses)
├── structured/
│   ├── schema.py             # OutputSchema (JSON Schema)
│   ├── extractor.py          # StructuredExtractor
│   └── constrained.py        # ConstrainedPrompt
└── optimization/
    ├── optimizer.py           # Iterative prompt improvement
    ├── candidates.py          # Variation generation
    └── selector.py            # BestOfN, Tournament
```

### Dependencies
**Runtime**: click, jinja2, jsonschema, pydantic
**Dev**: pytest, pytest-asyncio, pytest-cov, ruff

### Test Plan (66 tests)
| Module | Tests | Key Areas |
|--------|-------|-----------|
| core (4 files) | 14 | Template rendering, variable validation, versioning diff/rollback |
| strategies (7 files) | 16 | Each strategy: build_prompt + execute with mock |
| chains (4 files) | 8 | Pipeline context passing, router matching, parallel aggregation |
| evaluation (5 files) | 12 | Metrics scoring, dataset loading, report generation |
| safety (4 files) | 8 | Injection detection, PII redaction, guardrail validation |
| providers (2 files) | 4 | Mock determinism, replay record/playback |
| structured (3 files) | 4 | JSON extraction, schema validation |
| optimization (3 files) | 4 | Iteration loop, candidate generation |
| cli | 4 | render, eval, scan commands |

### Key Differentiator
Fills portfolio gap: none of the existing 8 projects focus on prompt engineering methodology. EnterpriseHub *uses* prompts; this project *engineers* them.

---

## Project 6: llm-integration-starter (~76 tests) — NEW REPO

**Bead**: `EnterpriseHub-can`
**Path**: `/Users/cave/Documents/GitHub/llm-integration-starter` (to create)

### Architecture
Production-grade LLM integration patterns: official SDKs, Pydantic, circuit breakers, middleware, observability.

### Differentiation from AgentForge

| Dimension | AgentForge | llm-integration-starter |
|-----------|------------|------------------------|
| HTTP layer | Raw httpx | Official SDKs (anthropic, openai) |
| Structured output | JSON schema + regex | Pydantic models + auto-retry |
| Resilience | Retry + fallback | Retry + fallback + **circuit breaker** |
| Observability | logging only | **OpenTelemetry** spans + metrics |
| Safety | None | **Guardrails** middleware |
| Caching | None | **Response cache** with TTL |
| Conversations | Single-shot | **Multi-turn** with token window |
| Budget | Passive tracking | **Hard budget enforcement** |
| Routing | Manual | **Intelligent model router** |
| Middleware | None | **Composable hook pipeline** |

### Package Structure
```
llm_starter/
├── __init__.py
├── client.py                 # LLMClient (main entry point)
├── config.py                 # Pydantic BaseSettings
├── types.py                  # Message, Response, Usage
├── exceptions.py             # Exception hierarchy
├── cli.py                    # Click CLI (chat, cost, health, models)
├── providers/
│   ├── base.py               # BaseProvider Protocol
│   ├── anthropic.py          # Claude via anthropic SDK
│   ├── openai_provider.py    # GPT via openai SDK
│   ├── google.py             # Gemini via google-generativeai
│   └── mock.py               # MockProvider
├── structured/
│   ├── extractor.py          # Pydantic model extraction + auto-retry
│   └── validators.py         # Custom validators
├── resilience/
│   ├── retry.py              # Exponential backoff with jitter
│   ├── circuit_breaker.py    # CLOSED → OPEN → HALF_OPEN
│   ├── fallback.py           # Provider fallback chain
│   └── rate_limiter.py       # Token bucket
├── middleware/
│   ├── base.py               # Middleware protocol + chain
│   ├── logging_mw.py         # Structured request/response logging
│   ├── guardrails.py         # PII, injection, toxicity checks
│   └── cache.py              # Response cache with TTL
├── cost/
│   ├── tracker.py            # Per-call usage recording
│   ├── budget.py             # Hard/soft budget limits
│   └── pricing.py            # 2026 model rates
├── observability/
│   ├── tracing.py            # OpenTelemetry spans
│   └── metrics.py            # Counters, histograms
├── conversation/
│   ├── manager.py            # Multi-turn state + token window
│   └── memory.py             # Sliding window strategy
└── router/
    └── router.py             # Route by cost/quality/latency
```

### Dependencies
**Runtime**: anthropic, openai, google-generativeai, pydantic, pydantic-settings, click, opentelemetry-api, python-dotenv
**Dev**: pytest, pytest-asyncio, pytest-cov, ruff, pyright

### Test Plan (76 tests)
| Module | Tests | Key Areas |
|--------|-------|-----------|
| client | 6 | Init, chat, stream, health, multi-turn, errors |
| config | 4 | Defaults, env override, validation |
| types | 4 | Serialization, equality |
| exceptions | 3 | Hierarchy, formatting |
| cli | 5 | Click CliRunner commands |
| providers (4 files) | 12 | Mock SDK responses, error mapping |
| structured (2 files) | 8 | Pydantic extraction, retry, nested models |
| resilience (4 files) | 16 | Circuit breaker states, retry timing, fallback chain |
| middleware (3 files) | 11 | Chain ordering, PII detection, cache TTL |
| cost (3 files) | 10 | Math, budget limits, pricing lookup |
| observability | 3 | Span attributes, metric recording |
| conversation | 4 | Window management, trimming |
| router | 4 | Profile matching, custom routing |

---

## Shared Patterns (All Repos)

### CI/CD
```yaml
# .github/workflows/ci.yml
runs-on: ubuntu-latest
matrix: python 3.11, 3.12
steps: checkout → setup-python → install → ruff check → ruff format --check → pytest -v
```

### Project Config
```toml
# pyproject.toml pattern
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-v --tb=short"
```

### File Boilerplate
```python
"""Module docstring."""
from __future__ import annotations
# stdlib imports
# third-party imports
# local imports
```

---

## Success Criteria

1. All 4 existing repos: CI green after changes
2. 2 new repos: created, pushed, CI green
3. Total portfolio tests: 5,500+ → 5,800+
4. Portfolio site: 11 project cards (9 + 2)
5. All beads closed with commit references
6. Memory updated with new repo details
