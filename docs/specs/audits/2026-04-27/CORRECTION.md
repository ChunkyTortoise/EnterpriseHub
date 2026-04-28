# Correction — 2026-04-27 Audit Error and Re-scoring

**Discovered:** 2026-04-27 (post-spec-publication, mid-status-update)
**Severity:** Material — affects Phase 1 audit B, Phase 3 track-fit scoring, Phase 4 roadmap Wave 1 scope, and master spec REQ-W1-3, REQ-W1-4.
**Trigger:** `git log --oneline -5` revealed prior commit `e2e5311f` (2026-04-07) shipping a full hiring-signal enhancement that the audit failed to detect.

---

## The Error

[Phase 1 Audit B (Eval & Prompt Engineering Maturity)](audit-B-evals.md) reported:

> "Empty evals/ + orphan `__pycache__` referencing deleted `generate_scorecard.py` is a smoking-gun signal of an abandoned eval attempt"

**This was wrong.** The `evals/` directory is fully populated. Verified on disk 2026-04-27:

```
evals/
├── __init__.py
├── README.md           (140 lines, dataset distribution + schema)
├── golden_dataset.json (802 lines, 50 hand-curated test cases)
├── judge.py            (280 lines, LLM-as-judge with 4 rubrics)
├── rubrics.py          (95 lines)
├── baseline.json       (10 lines, regression baseline)
└── compare_baseline.py (51 lines, baseline comparison tool)
```

Plus, also already shipped on 2026-04-07:
- **Prompt versioning:** `prompt_versions` PostgreSQL table, `ghl_real_estate_ai/services/prompt_registry.py`, `PROMPT_CHANGELOG.md` (241 lines, 25+ prompts versioned)
- **Adversarial testing:** 18 test cases across `tests/adversarial/{test_prompt_injection,test_jailbreak,test_topic_boundary}.py`
- **Cost governance:** `ghl_real_estate_ai/services/cost_governance.py`, `/admin/cost-dashboard` endpoint, $100/hr emergency shutdown
- **Nightly regression:** `.github/workflows/nightly-eval.yml` (cron 2am UTC, baseline comparison, auto-creates GitHub issue on >10% quality drop)
- **Prior spec:** [`docs/specs/2026-04-07-feature-ai-hiring-signal-enhancement-spec.md`](../../2026-04-07-feature-ai-hiring-signal-enhancement-spec.md) (455 lines, 5-wave structure, ADRs 0011/0012/0013)

## Why the Audit Missed It

Best guess: Audit B's exploration looked at the wrong path or a stale cache. The earlier explorer agent that informed [`00-prefit-strawman.md`](00-prefit-strawman.md) propagated the same blind spot, which is why the prefit strawman scored QA/SDET-eval at 1/10 on the eval-framework-presence component.

**Quality-control failure:** the audit synthesis pass should have spot-checked the highest-stakes claim ("empty evals/") with a direct `ls` before publication. It did not.

## Re-scoring (Binding — Supersedes Original Track-Fit)

| Track | Original score | Corrected score | Delta |
|---|---:|---:|---:|
| AI/LLM Engineer (mid) | 79.0 | 79.0 | unchanged (cert/repo/market components dominate) |
| AI/LLM Engineer (senior) | 47.5 | **~58** | +10.5 — eval/observability rigor lifts from 3/10 to 7/10 |
| Python Developer | 73.5 | 73.5 | unchanged |
| QA/SDET (LLM eval niche) | 63.5 (now) → 75.5 (post-Wave-1) | **~73.5 (now)** → 78 (post-Wave-1 surface lift) | binding constraint *already cleared*; Wave 1 just elevates visibility |
| Solutions Engineer | 49.7 | 49.7 | unchanged |

**Wedge verdict still holds:** Multi-track — AI mid primary, QA/SDET niche secondary. The QA/SDET niche is *already held* not pending Wave 1.

**Senior-tier delta checklist updated:** 2 of 7 already in motion before Cycle 2 (eval harness ✓, prompt versioning ✓ — both shipped 2026-04-07). Remaining 5: public benchmark, MCP-2, production write-up, OSS RFC, sustained writing.

## Wave 1 Scope Reduction

The following Wave 1 items are **already complete** and removed from this cycle's roadmap:

- ~~REQ-W1-3: Eval harness with promptfoo + 3 golden datasets~~ — **done** (different framework: pytest-based + LLM-as-judge with custom rubrics, but functionally equivalent and arguably more defensible than promptfoo wiring)
- ~~REQ-W1-4: `evals/README.md` for QA-track positioning~~ — **already exists** ([evals/README.md](../../../evals/README.md))
- ~~Prompt registry / versioned YAML~~ (Wave 2 REQ-W2-1) — **done** (`PromptRegistry` service + `PROMPT_CHANGELOG.md`)
- ~~Adversarial tests~~ (was implicit Wave 4 work) — **done** (`tests/adversarial/`)
- ~~Nightly regression workflow~~ — **done** (`.github/workflows/nightly-eval.yml`)
- ~~Cost governance service~~ — **done** (`services/cost_governance.py`)

**What's actually missing on the eval/prompt/cost surface:**

- **Cost dashboard live-data wiring:** Streamlit page (`25_LLM_Cost_Analytics.py:31`) still uses `random.seed(42)` mock per Audit C P0-10. The cost service exists; the dashboard hasn't been wired to it. Wave 2 REQ-W2-2 still applies.
- **Reliability diagram PNG in README:** the eval results aren't surfaced in the README hero. Adding a 10-bin calibration plot from existing baseline data is a 1-hour task that closes the visible-evidence gap.
- **Cross-link from main README to `evals/README.md`:** the credential exists but isn't discoverable from the top-level repo. README hero update needed.
- **Golden dataset expansion:** 50 cases is a defensible starting set; the Wave 1 spec target was 500/400/300. Expansion is a Wave 6 stretch goal, not Wave 1 P0.

## Revised Wave 1 Scope (Binding)

Wave 1 (Weeks 1–2) now ships:

- [ ] `bench_cache_live.py` reading real `LLMObservabilityService` counters
- [ ] k6 load test scripts (`benchmarks/k6/{qualification_load,burst,sustained}.js`) with results in `benchmarks/results/2026-W17/`
- [ ] `record_handoff_outcome` async classmethod fix (audit A P0-2)
- [ ] `docker-compose.observability.yml` + `otel-collector-config.yaml` fix (audit C P0-9)
- [ ] CASE_STUDY.md / BENCHMARK_VALIDATION_REPORT.md / README walk-down to honest numbers
- [ ] **Reliability diagram PNG** generated from existing eval baseline + cross-linked in README hero (NEW — replaces "build harness")
- [ ] **README cross-link to evals/README.md + PROMPT_CHANGELOG.md + nightly-eval workflow** (NEW — visibility lift)

Effort estimate drops from ~12 engineering days to ~6.

## Lessons Captured

1. **Audit synthesis must spot-check headline claims directly.** Agent reports are not authoritative for filesystem state.
2. **Prior-spec discovery should be explicit Phase 0 step.** The Phase 0 pre-flight included live demo health and budget cap but not "scan `docs/specs/` for prior specs in the same problem space." Adding to plan template.
3. **The user said "we shipped this 3 weeks ago" silently** — by leaving the prior spec doc in the repo. Next pre-flight should include `git log --since="3 months ago" --oneline | head -30` to surface recent meaningful work.

## Files Updated as Part of This Correction

- This file (new): `docs/specs/audits/2026-04-27/CORRECTION.md`
- Banner added at top of: `audit-B-evals.md`, `01-audit-synthesis.md`, `03-track-fit.md`, `04-roadmap.md`, `2026-04-27-enterprisehub-hireability-spec.md`
- Wave 1 beads epic description updated (`EnterpriseHub-imkl`)
