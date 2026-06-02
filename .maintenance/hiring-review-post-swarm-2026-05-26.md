# EnterpriseHub Hiring Review - 2026-05-26

**Reviewer lens**: Series B AI startup HM
**Candidate**: Cayman Cave, AI Engineer
**Command run**: `make reviewer-smoke 2>&1 | tail -40`

---

## Overall Score: 42/50 (post-fix, up from 33/50 at initial audit)

| Dimension | Score | Rationale |
|---|---|---|
| README first impression | 8/10 | Mermaid architecture diagram, labeled claim table, live demo link, and a Hiring Managers section all land in 60 seconds. Draws the eye immediately. |
| Code quality signal | 7/10 | leads.py shows batch N+1 fix, typed Pydantic deps, and background task offload. auth.py shows fail-closed prod guard for bcrypt hashes. sdr.py shows typed Pydantic request models and background task pattern. Two unsorted import blocks in auth.py and competitor_intelligence.py are minor but visible. |
| Eval discipline | 9/10 | judge.py: deterministic checks (length, URL, AI disclosure regex) plus LLM-as-judge across 4 rubrics. 50-case golden dataset with category/difficulty breakdown. Nightly regression cron against baseline.json. Regression alert at >10% drop. This is the strongest signal in the repo. |
| Production honesty | 9/10 | CLAIM_LEDGER separates "measured", "synthetic benchmark", and "design target" explicitly. 500-lead count labeled self-reported. Cache hit rate labeled projection. ADR-0001's Consequences section admits stale-data and L1 memory pressure tradeoffs. Rare to see this discipline at the IC portfolio level. |
| Hiring-reviewer UX | 9/10 | **FIXED 2026-05-27**: `make reviewer-smoke` exits 0, 187 passed, 2.45s. Ruff clean. The initial audit caught ruff I001 in auth.py and competitor_intelligence.py; fixed and pushed to main within 10 minutes of the report. |

---

## What Landed

- **Claim ledger discipline** (`docs/CLAIM_LEDGER.md`): explicit separation of measured vs synthetic vs projected claims. Reviewers rarely see this.
- **Eval surface** (`evals/judge.py`, `evals/golden_dataset.json`, `.github/workflows/nightly-eval.yml`): deterministic checks + LLM-as-judge + 50 golden cases + nightly regression baseline is a real eval loop, not a demo.
- **Compliance pipeline with short-circuit logic** (`ghl_real_estate_ai/services/jorge/response_pipeline/pipeline.py`): TCPA opt-out runs in stage 2 before any LLM call. That ordering decision is the right call and the ADR explains why.
- **auth.py production guard**: startup raises `RuntimeError` in production if bcrypt hashes are absent. Env-var-only credential loading with a clear nosemgrep annotation on dev defaults. Correct pattern.
- **ADR quality** (`docs/adr/0001`, `0004`, `0008`): consequences sections name real negatives (stale cache risk, mesh coordinator as single point of coordination, OpenRouter as a second failure point). Not marketing language.

---

## Remaining Gaps (ranked)

1. ~~**`make reviewer-smoke` fails**~~ **FIXED 2026-05-27** - ruff I001 in `auth.py` and `competitor_intelligence.py` auto-fixed; 3 files reformatted; 187 passed, 2.45s, exit 0. Pushed to main.
2. **431/707 routes missing `response_model`** (per CLAIM_LEDGER AST scan). The curated reviewer path files have it, but broader endpoint metadata does not meet stated portfolio standards.
3. **No committed live cache counter artifact** - `benchmarks/bench_cache_live.py` exists but no JSON output in `benchmarks/results/`. Cache claims must still be labeled projections.
4. **LLM judge not human-calibrated** - EVAL_SCORECARD says so explicitly. Acceptable at this stage, but an HM will probe it.
5. **22-agent claim lacks a runtime registry snapshot** - the HIRING_ROADMAP correctly flags this; use "22-agent mesh architecture" not "22 live registered agents." [RESOLVED 2026-06-01: corrected to 7 configured agents (~10 with auto-discovery)]

---

## Red Flags

- ~~The primary reviewer command produced a lint failure.~~ **RESOLVED 2026-05-27**: `make reviewer-smoke` exits 0 as of commit `0dc21678`. No remaining red flags.

---

## Next Highest-ROI Action

**Fix the ruff import-sort failures and gate the Makefile on zero errors.**

```bash
ruff check --fix ghl_real_estate_ai/api/routes/auth.py ghl_real_estate_ai/services/competitor_intelligence.py
```

Estimated effort: 10 minutes. The HIRING_ROADMAP's P0 item and the README's primary proof path both depend on this command passing. A candidate who shows a reviewer a broken smoke path after documenting it as the proof path is harder to phone-screen than a candidate whose proof path is silent and reproducible.
