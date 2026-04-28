> **⚠️ CORRECTION 2026-04-27:** Wave 1 scope reduced ~50%. The eval harness, prompt versioning, adversarial tests, cost governance service, and nightly regression workflow were already shipped 2026-04-07 (commit `e2e5311f`). Items removed from Wave 1: build harness, build promptfoo wiring, build evals/README.md, build adversarial tests, build nightly cron. Items added to Wave 1: reliability diagram PNG (from existing baseline data), README cross-link to evals/README.md + PROMPT_CHANGELOG.md (visibility lift). Wave 1 effort: ~12 days → ~6 days. See [CORRECTION.md](CORRECTION.md).

---

# Phase 4 — Strategic Roadmap (Binding)

**Date:** 2026-04-27
**Inputs:** [Phase 3 track-fit](03-track-fit.md), [Phase 2 synthesis](05-claude-synthesis.md), [Phase 1 audit synthesis](01-audit-synthesis.md).
**Verdict guiding the plan:** multi-track wedge — **AI/LLM Engineer (mid) primary**, **QA/SDET LLM-eval niche secondary**, consulting tertiary (warm-only).
**Senior AI track:** explicitly out of scope for *this* 8–12 week cycle; deltas listed in Phase 3 are the 12–18 month horizon plan, started but not completed by Week 12.

---

## Roadmap Diff from Original Spec Plan

| Change | Direction | Why |
|---|---|---|
| **Add Wave 0 (immediate)** | new | 5-min demo unlock + cert resume triage are 0-day funnel fixes; they shouldn't sit behind Wave 1 |
| **Wave 1 expanded** | scope+ | Add `bench_cache_live.py`, k6 scripts, eval harness with QA-track-friendly framing |
| **Wave 5 conference talk** | replaced | Production-incident write-up + second MCP server replace the talk |
| **Wave 4 STRIDE** | reduced | 2-paragraph "adversarial inputs" doc instead of full STRIDE |
| **Wave 4 design system** | reduced | Lite token extraction only; not full library |
| **Wave 6 case study refresh** | added explicit cert-triage step | Day-1 fix gets a Wave-6 final-pass validation |
| **QA/SDET-track surface** | new | Wave 1–2 deliverable: `evals/README.md` + landing page positioning EnterpriseHub-as-eval-platform |
| **Mesh coordinator** | priority++ | P0-A1 (Phase 1 audit A) — either ship real backpressure or ADR documenting scaffold; was buried in original Wave 3 |

---

## Wave 0 — Funnel Unlock (Day 1, ≤2 hours total)

Independent of code. Highest funnel-leverage-per-minute work in the entire plan.

| Item | Owner | Effort | Beads |
|---|---|---|---|
| **Streamlit Cloud demo unlock** (Sharing → Public) | user | 5 min | `EnterpriseHub-j50d` |
| **Cert resume triage** — drop AI-track resume to 5–6 named certs (KEEP: IBM GenAI Eng, DeepLearning.AI Deep Learning, Duke LLMOps, IBM RAG, Anthropic Claude Code; DROP from AI variant: marketing certs, ChatGPT for Personal Automation, Microsoft Data Viz). Rebuild Python and QA/SDET variants in parallel. | user (+ assist) | 60–90 min | new beads issue |
| **Resume rotation in active applications** — replace stale resume in LinkedIn Open To Work, Indeed profile, Upwork hourly profile | user | 20 min | new |
| **ATS-score check baseline** (run `ats-optimizer.py` against 5 fresh job postings; record scores) | user | 30 min | new |

**Gate:** Wave 1 does not begin until Wave 0 ships. Without the demo unlock + resume fix, Wave 1 polish is wasted spend on a broken funnel.

---

## Wave 1 — Credibility & Eval Foundation (Weeks 1–2)

Closes the Phase 1 P0 register and produces the first multi-track unlock artifact.

### Code (~12 engineering days)

- [ ] **Real cache-hit measurement tool** — `bench_cache_live.py` reading from `LLMObservabilityService` counters (or instrument as needed). Produce honest hit-rate number. May be lower than 88%; that's fine. (Phase 2 artifact #1)
- [ ] **k6 load test scripts** in `benchmarks/k6/`: `qualification_load.js`, `burst.js`, `sustained.js`. Run against local stack + Render staging. Results JSON in `benchmarks/results/2026-W17/`. (Phase 2 #2)
- [ ] **Eval harness** — promptfoo + 3 golden datasets in `evals/datasets/{qualification,handoff,compliance}/*.jsonl` (sizes 500/400/300). Reliability diagram PNG in `evals/results/2026-W17/`. CI gate in `.github/workflows/evals.yml`. (Phase 2 #3)
- [ ] **`evals/README.md`** — QA/SDET-track surface; positions EnterpriseHub as an LLM-eval reference implementation. (New from Phase 3)
- [ ] **`record_handoff_outcome` async fix** — convert classmethod to instance method using `asyncio.create_task`. (Phase 1 audit A P0-2)
- [ ] **`docker-compose.observability.yml` + missing `otel-collector-config.yaml`** — fix mount, get the local stack starting. (Phase 1 audit C P0-9)

### Narrative

- [ ] **CASE_STUDY.md walk-down** — replace "88% cache hit rate, 150 req/s sustained" with the real Wave 1 numbers. New caveat language: "design-target distribution × real-traffic measurement window of N requests." (Stage 3 contrarian: "Most overcooked claim: 8.5/10 self-rating language. Drop self-scoring entirely.")
- [ ] **README hero refresh** — lead with production GHL client + `mcp-server-toolkit` PyPI; demote test count to a footnote. (Phase 2 + Stage 3)

### Verification gate

Wave 1 complete when: (1) `python -m benchmarks.bench_cache_live` produces a real number, (2) k6 results checked into the repo, (3) eval harness CI runs on a PR and the reliability diagram PNG is visible in README, (4) re-`/visual-audit` shows demo unlocked + first-impression score >7/10, (5) revised CASE_STUDY contains no unbacked numbers.

---

## Wave 2 — Prompt Versioning + Cost Visibility (Weeks 3–4)

### Code

- [ ] **Prompt registry** — versioned YAML in `prompts/` with eval-linked changelog. Each prompt change requires an eval delta entry. (Phase 2 #10)
- [ ] **Real cost dashboard** — replace `25_LLM_Cost_Analytics.py` `random.seed(42)` mock with live read from `LLMObservabilityService`. (Phase 1 audit C P0-10)
- [ ] **OTLP exporter wired** to Honeycomb (free tier acceptable) or Grafana Cloud. Auth headers configured (close `otel_config.py:122` insecure flag). Trace visible from a real request through orchestrator + handoff. (Phase 2 #8 + Phase 1 audit C P1-5)

### Verification

Cost dashboard shows real numbers, OTLP traces visible in Honeycomb UI, prompts have version pins. CI runs eval gate on every PR.

---

## Wave 3 — Mesh Decision + Real ML + Demo Video (Weeks 5–6)

### Code

- [ ] **Mesh coordinator: ship real backpressure OR write ADR documenting scaffold status** — explicit either-or, not both. (Phase 1 audit A P0-1) Document choice in `docs/adr/0011-agent-mesh-buildout-strategy.md`.
- [ ] **Multi-worker handoff state ADR** — `docs/adr/0012-handoff-state-isolation.md`. (Phase 1 audit A P1-4)
- [ ] **Real ML integration** — replace `bots_stub.py` no-ops with actual `ml_analytics_engine` and `feature_engineering`. Document training data + model card.
- [ ] **`StartupOrchestrator` extraction** from `api/main.py` lifespan monolith. Tested. (Phase 1 audit A P0-3)

### Narrative

- [ ] **Demo video** — 90-second product walkthrough Loom (Stage 3 contrarian: short, no narration overlay, just clicks and outputs). Embedded in README + LinkedIn featured.

### Verification

Re-run Phase 1 agents A, B, C, E. Score delta tracked in `docs/specs/audits/2026-04-27/03-track-fit.md` update section.

---

## Wave 4 — Security Doc + Light Design (Weeks 7–8)

### Code & Docs

- [ ] **Adversarial-inputs write-up** (2 paragraphs) in `docs/security/adversarial-inputs.md` — Stage 3 compromise; replaces full STRIDE. Covers prompt injection, rate limits, audit logging, FHA/RESPA/TCPA edge cases.
- [ ] **`api_monetization.py` had a P0 — already fixed week 0**; this wave validates fix has 100% test coverage on the new `_get_signing_secret` path.
- [ ] **bcrypt 72-byte truncation fix** — `jwt_auth.py:252-275` (Phase 1 audit D P1-6).
- [ ] **Design tokens lite** — extract Obsidian Ember palette into reusable token file; do NOT build a component library. (Phase 1 audit E P1-7 / P1-8)
- [ ] **Screenshot refresh** — re-capture 5 dashboard screenshots in current Ember theme; update README hero. (Phase 1 audit E P1-7)

### Narrative

- [ ] **Tech blog post draft** (drafted Wave 4, published Wave 5 after polish): "Production debugging of an LLM tool-loop max-turn exhaustion" — using the Phase 1 audit A P1-1 finding as a real lived debugging story. Replaces the planned "Three-tier cache" post (Stage 3: too saturated a topic).

---

## Wave 5 — Public Technical Leadership (Weeks 9–10)

### Code

- [ ] **Second focused MCP server** — published to PyPI as `mcp-real-estate-tools` (or similar). Solves one specific real-estate-AI workflow (MLS listing tool, GHL contact tool, or FHA-compliance tool). Forms differentiator pair with existing `mcp-server-toolkit`. (Phase 2 #7)
- [ ] **Tool-loop telemetry + Prometheus counter** — close Phase 1 audit A P1-1, the basis for the published blog post.

### Narrative

- [ ] **Production-incident write-up published** — chosen from real EnterpriseHub history (e.g., the 88%-tautology discovery itself, the auth-gated demo, the asyncio.classmethod issue). Personal site or dev.to with unique numbers. **Replaces the planned conference talk.** (Phase 2 #5 + Phase 3 senior-tier delta)
- [ ] **Recruiter outreach calibration experiment** — 5 personalized cold emails A/B (subject-line variant). Measure reply rate. Decide whether to scale to 10-prospect list. (Spec plan original)
- [ ] **`/audit-scorecard` template** for prospect outreach — 3 prospect targets identified in advance; scorecards drafted.

---

## Wave 6 — Conversion + Final Polish (Weeks 11–12)

### Code

- [ ] **Final P1 sweep** — clear remaining items from [01-audit-synthesis.md](01-audit-synthesis.md) P1 register that survived Waves 1-5.
- [ ] **Eval harness expansion** — golden datasets grown to 750/600/450 if time allows. Reliability diagram regenerated.

### Narrative

- [ ] **CASE_STUDY.md final rewrite** — incorporates all Wave 1-5 numbers. ROI section expanded with the production-incident write-up and the second MCP package.
- [ ] **Resume final pass** — three variants (AI Engineer, Python Developer, QA/SDET LLM eval) regenerated incorporating Wave 1-5 artifacts.
- [ ] **1-pager PDF** for recruiter outreach — DESIGN-FREE — plain doc with verifiable links.
- [ ] **Track-specific portfolio link audit** — every link in resumes/profiles validated end-to-end (AI = EnterpriseHub repo, Python = mcp-server-toolkit, QA = `evals/` README + datasets, consulting = production GHL case study).
- [ ] **Final hero re-audit** — `/hero-audit EnterpriseHub` target ≥47/50.
- [ ] **30-day measurement window opens** — phone-screen count tracked in `~/.claude/reference/freelance/revenue-tracker.md`.

### Senior-tier deltas in motion (NOT completed this cycle)

- One MCP package published ✓ (Wave 5)
- One production-incident write-up published ✓ (Wave 5)
- Eval harness with calibration in README ✓ (Wave 1)
- Public benchmark with reproducible numbers ✓ (Wave 1)
- ADR co-authored in notable OSS — *not started this cycle, candidates: Anthropic skill repos, promptfoo, dspy*
- Sustained technical writing presence — *Wave 5 post is post 1 of 4–6; cycle 2 in months 4–6*

---

## Dependency Graph

```
Wave 0 (funnel unlock) ──► Wave 1 (eval+benchmarks+credibility) ─┐
                                                                  ├─► Wave 5 (MCP-2 + write-up + outreach) ──► Wave 6 (final polish + measurement)
Wave 2 (prompts+cost+OTLP) ─┐                                    │
                            ├─► Wave 3 (mesh+ML+video) ──► Wave 4 (security+design lite) ‖ Wave 5
Wave 1 ─────────────────────┘
```

Waves 4 and 5 partially overlap — security doc and design polish don't block writing.

---

## Cadence Integration

- **Daily `/freelance-ops`:** continues. Phase 1 audit findings + this roadmap inform digest priorities.
- **Weekly `/hero-audit EnterpriseHub`:** every Friday. Score tracked against 47+/50 target.
- **Bi-weekly ATS check:** `ats-optimizer.py` against 5 fresh postings. Score delta to revenue-tracker.
- **Wave gates:** session-close hygiene (git status → bd sync → commit → push) at every wave boundary.
- **Calibration experiment (Wave 5):** 5 cold emails before scaling outreach.
- **Early-exit pivot:** if a phone screen lands during Waves 1–4, freeze and jump to Wave 6 narrative refresh + interview prep.

---

## Beads Epic Structure

Parent: `EnterpriseHub-td5t` (already created).

Wave epics to create:
- Wave 0 — Funnel unlock
- Wave 1 — Credibility + eval foundation
- Wave 2 — Prompts + cost + OTLP
- Wave 3 — Mesh + ML + demo video
- Wave 4 — Security + design lite
- Wave 5 — MCP-2 + production write-up
- Wave 6 — Conversion + final polish

P0/P1 issues from [01-audit-synthesis.md](01-audit-synthesis.md) child of corresponding wave epic. Dependency: each wave depends on the previous wave's epic via `bd dep add`.

(Wave 0 demo-unlock issue `EnterpriseHub-j50d` already exists — needs to be linked under the Wave 0 epic when created.)

---

## Success Criteria (Revised, Binding)

1. ✅ **Track decision evidence-based** — multi-track wedge (AI mid primary, QA/SDET secondary, consulting tertiary). Recorded in [03-track-fit.md](03-track-fit.md).
2. **Wave 0 ships in 24 hours.** Demo unlocked, AI-track resume cert-triaged.
3. **Wave 1 ships clean by end of Week 2.** Eval harness in CI, real benchmarks committed, CASE_STUDY.md walked down to honest numbers.
4. **Hero score 39 → 47+/50** by Wave 6 (`/hero-audit` measured).
5. **Phone screens ≥3 in 30-day post-Wave-6 window** (vs. 0 prior 90 days).
6. **Senior-tier deltas: 4 of 7 in motion** by Week 12 (eval, benchmark, MCP-2, write-up). Remaining 3 begin in Cycle 2 (months 4–6).
