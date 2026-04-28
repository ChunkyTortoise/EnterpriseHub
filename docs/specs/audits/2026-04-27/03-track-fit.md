> **⚠️ CORRECTION 2026-04-27:** Scoring below assumed "empty evals/" — that premise was wrong. Corrected scores (binding):
> - **AI/LLM Engineer (senior):** 47.5 → **~58.0** (eval/observability rigor lifts from 3/10 to 7/10 — eval harness already shipped 2026-04-07)
> - **QA/SDET (LLM eval niche):** 63.5 → **~73.5 NOW** (eval-framework-presence already 7/10, not 1/10; Wave 1 lift to ~78 from visibility surfacing)
> - Other tracks unchanged.
>
> **Wedge verdict still holds:** Multi-track — AI mid primary, QA/SDET niche secondary, consulting tertiary.
> **Senior-tier delta checklist:** 2 of 7 already in motion (eval harness ✓, prompt versioning ✓). See [CORRECTION.md](CORRECTION.md) for re-scoring rationale.

---

# Phase 3 — Track-Fit Assessment (Binding)

**Date:** 2026-04-27
**Inputs:** Phase 1 (six audit reports + synthesis), Phase 2 (research synthesis with adequacy=STANDARD), `~/.claude/reference/freelance/skills-certs.md` cert inventory, current repo inventory.
**Status:** Binding for Phase 4 roadmap. Supersedes the [00-prefit-strawman.md](00-prefit-strawman.md) provisional scores.

---

## Method

Per spec Phase 3 rubric, weighted 0–100 score per track. Each component scored 0–10 against the evidence, then weighted and summed.

Component definitions (lower bar = mid-AI band; higher bar = senior-AI lab tier):

- **repo evidence** — production signal, demonstrable artifacts, defensibility under technical screen
- **cert match** — specific certs that map to track (not generic volume)
- **market demand** — 2026 hiring volume + comp band
- **interview-readiness** — funnel state, ATS hygiene, demo accessibility, narrative coherence
- **system-design depth** — non-obvious tradeoffs, ADRs, scale evidence
- **public technical leadership** — write-ups, talks, OSS maintainership, peer signal
- **eval/observability rigor** — calibrated artifacts, traces, cost dashboards
- **OSS contributions** — published packages, accepted PRs to notable projects
- **test depth** — beyond count, coverage of behavior vs. mocks
- **niche scarcity bonus** — for QA/SDET LLM-eval and similar
- **demo polish** — first-impression artifact accessibility
- **case study quality** — narrative, ROI evidence, defensibility
- **multi-CRM evidence** — for SE track only

---

## Scores

### AI/LLM Engineer — MID ($95–130K target band)

| Component | Weight | Score | Weighted |
|---|---:|---:|---:|
| Repo evidence | 0.40 | 8.0 | 3.20 |
| Cert match (top 5: IBM GenAI, DeepLearning.AI, Duke LLMOps, IBM RAG, Anthropic Claude Code) | 0.20 | 9.0 | 1.80 |
| Market demand | 0.25 | 9.0 | 2.25 |
| Interview-readiness | 0.15 | 5.0 | 0.75 |
| **Total** | | | **79.0 / 100** |

**Verdict: VIABLE NOW.** The bottleneck is interview-readiness (ATS reset + demo unlock + cert resume triage), not artifacts. Items #4 and #6 in the [Phase 2 artifact list](05-claude-synthesis.md#concrete-artifact-list-binding-for-phase-4-roadmap) ship the readiness gap inside Week 1.

---

### AI/LLM Engineer — SENIOR ($180K+ target band, lab-tier $300K+ aspirational)

| Component | Weight | Score | Weighted |
|---|---:|---:|---:|
| System-design depth | 0.35 | 7.0 | 2.45 |
| Public technical leadership | 0.25 | 2.0 | 0.50 |
| Eval/observability rigor | 0.20 | 3.0 | 0.60 |
| Cert tier (Coursera vs. grad-school/ML-research) | 0.10 | 4.0 | 0.40 |
| Market | 0.10 | 8.0 | 0.80 |
| **Total** | | | **47.5 / 100** |

**Verdict: NOT VIABLE this cycle. 12–18 month horizon.**

The dominant deficits are public technical leadership (no published technical write-ups with audience; no OSS maintainership of a notable project) and eval/observability rigor. System-design depth is *strong* (handoff service, response pipeline, multi-tier cache, agent mesh — even with the scaffolding — are senior-tier patterns), but is being undersold by the missing artifacts.

**Score after Wave 1 + Wave 5 ships** (with eval harness, OTLP, real benchmarks, and a substantive technical write-up): projected **62/100.** Closes the lab-tier ceiling persona-F flagged at ~58.

**Score required to convert at lab-tier (Anthropic / OpenAI / FAANG GenAI):** ~80/100. Reaching that requires sustained public technical leadership over 12–24 months that this 8–12 week roadmap cannot fabricate.

---

### Python Developer (broad backend / production-Python roles, $80–110K → $130K)

| Component | Weight | Score | Weighted |
|---|---:|---:|---:|
| Repo breadth | 0.35 | 9.0 | 3.15 |
| Test depth (behavior, not just count) | 0.25 | 7.0 | 1.75 |
| OSS contributions | 0.15 | 6.0 | 0.90 |
| Cert match | 0.10 | 5.0 | 0.50 |
| Market | 0.15 | 7.0 | 1.05 |
| **Total** | | | **73.5 / 100** |

**Verdict: VIABLE.** Wider funnel than AI track, lower ceiling. The primary constraint is positioning: Python-track resume should *suppress* the AI/ML cert pile and *lead* with production system + PyPI package + 12K test depth. Currently the resume variants exist but the cert hierarchy on each isn't differentiated enough per Stage 3 contrarian's read.

---

### QA/SDET — LLM Eval Niche ($80–100K standard, $110–130K with niche)

| Component | Weight | Score | Weighted |
|---|---:|---:|---:|
| Test count + structure | 0.30 | 8.5 | 2.55 |
| Eval framework presence | 0.30 | 1.0 (currently empty `evals/`) → 8.0 (after Wave 1 ships) | 0.30 → 2.40 |
| CI rigor | 0.20 | 8.0 | 1.60 |
| Niche scarcity bonus | 0.20 | 9.0 | 1.80 |
| **Total** | | | **63.5 / 100 (now) → 75.5 / 100 (after Wave 1)** |

**Verdict: HIGHEST LEVERAGE-PER-UNIT-OF-WORK.** Currently the eval-framework-presence component is the binding constraint at 1/10. Wave 1's eval harness lifts this from "missing the niche credential" to "rare credential held." Niche scarcity in 2026 is verified by Phase 2 web data — agentic-RAG/LLMOps/eval is named as differentiator-tier work.

This is the track where the smallest amount of additional work produces the largest score delta.

---

### Solutions Engineer ($65–95K, contract-friendly)

| Component | Weight | Score | Weighted |
|---|---:|---:|---:|
| Demo polish | 0.30 | 4.0 (auth-gated) → 7.5 (after demo unlock + Loom) | 1.20 → 2.25 |
| Case study quality | 0.25 | 6.0 | 1.50 |
| Public speaking/content | 0.20 | 2.0 | 0.40 |
| Multi-CRM evidence | 0.15 | 8.5 (HubSpot OAuth + Salesforce + GHL adapter pattern) | 1.275 |
| Market | 0.10 | 6.0 | 0.60 |
| **Total** | | | **49.7 / 100 (now) → 54.7 / 100 (post demo unlock)** |

**Verdict: NOT THE RIGHT WEDGE.** Lower ceiling, requires public-speaking work that Stage 3 deprioritized, and the strongest component (multi-CRM evidence) only modestly weights. Use SE messaging in proposal copy when applying to multi-CRM-AI gigs, but do not center the resume around it.

---

## Wedge Recommendation (BINDING)

**Top three within 12 points: AI mid (79.0), Python (73.5), QA/SDET post-Wave-1 (75.5).** Per the spec's rubric, this is the **multi-track wedge** verdict.

**Recommended portfolio funneling:**

1. **Primary: AI/LLM Engineer (mid).** Highest score, highest comp ceiling at the viable band, market demand strongest. Direct LinkedIn + targeted job-board applications (NOT cold Indeed mass-apply). Anchor: EnterpriseHub + `mcp-server-toolkit`.

2. **Secondary (parallel funnel): QA/SDET — LLM eval niche.** Once Wave 1 ships eval harness, this is a *rare credential* in the candidate pool. A separate resume variant emphasizing 12K+ tests + LLM-as-judge + golden datasets + CI gating. Apply to companies hiring "AI QA" / "LLM evaluator" / "ML test engineer" roles. Comp ceiling lower than AI Mid but funnel scarcer = better conversion.

3. **Tertiary (warm-only): Consulting / contract.** Phase 1 audit F flagged this as the strongest *current* fit. Use for $20–50K real-estate-AI builds, $75–125/hr engagements. Direct outreach (already in spec Wave 5), not job-board apps. **Single key signal needed:** named client reference (Jorge testimonial — already in beads `EnterpriseHub-qnef` ready P0).

**Suppress entirely from this cycle:** Solutions Engineer (lower fit), Data Analyst (post-2026-04-07 ATS-poisoning recovery — keep DA resume retired), Senior AI lab-tier (12-18 month horizon).

---

## Concrete Deltas to Senior-Tier — Produce These, In This Order

The user's stated worry about senior qualification, addressed in artifact form. Each item maps to a Wave; check off as completed. **Senior is NOT this cycle's target — these are positioned for the 12–18 month horizon, but Wave-1 deliverables already start the clock.**

- [ ] **Eval harness with calibration results visible in README** *(Wave 1, this cycle — also closes mid-AI gap)*
- [ ] **Public benchmark with reproducible numbers** (k6 + bench_cache_live.py) *(Wave 1, this cycle)*
- [ ] **One substantive production-incident write-up** with unique numbers (referenceable, archivable) *(Wave 5, this cycle — REPLACES planned conference talk)*
- [ ] **Second focused MCP server** solving a specific real-estate-AI workflow problem, published to PyPI *(Wave 5 stretch — bridges 2026 differentiator gap)*
- [ ] **One ADR co-authored or RFC published** in a notable OSS project *(12–18 month horizon — NOT Wave 5 this cycle)*
- [ ] **Sustained technical writing presence** (4–6 substantive posts with measured engagement, not generic Medium content) *(12–18 month horizon)*
- [ ] **OSS maintainership of a notable project** OR primary author on a tier-1 conference paper *(12–18 month horizon)*

---

## Implications for Phase 4 Roadmap

The Phase 2 artifact list (Stage 5) provided 15 ranked items. With this Phase 3 wedge verdict, Phase 4 should:

1. **Front-load the multi-track unlock items** (Wave 1): cert resume triage, demo unlock, eval harness, real benchmarks. These lift ALL three viable tracks simultaneously.
2. **Add a QA/SDET-track-specific surface** in Wave 1–2: an `evals/README.md` and a separate landing page or repo subsection that markets EnterpriseHub-as-LLM-eval-platform. Same artifact, different framing for the QA/SDET resume variant.
3. **Replace the conference-talk slot in Wave 5** with the production-incident write-up. Higher-confidence artifact, lower time cost, more screen-readable.
4. **Add the "second focused MCP server"** to Wave 5 (or earlier if quick) as the differentiator-class artifact for senior horizon.
5. **Deprioritize SE-track polish** (design system, public speaking) — keep only the case-study refresh in Wave 6 since it serves AI mid AND consulting.
6. **Make resume cert triage a Day-1 task** — single highest-ROI funnel improvement.
