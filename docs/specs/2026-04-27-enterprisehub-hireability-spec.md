# EnterpriseHub Hireability Transformation — Master Spec

**Spec ID:** 2026-04-27-enterprisehub-hireability
**Owner:** Cayman Roden
**Status:** Active (Wave 0 in flight)
**Cycle:** 8–12 weeks (Weeks 17–28 of 2026)
**Parent epic:** [`EnterpriseHub-td5t`](#beads-tracking)
**Companion research:** [`2026-04-27-enterprisehub-hireability-research.md`](2026-04-27-enterprisehub-hireability-research.md)
**Source plan:** `~/.claude/plans/create-a-deep-spec-cosmic-cascade.md`

---

## 1. Context

A freelance AI engineer with 21 certifications (1,831 hrs), 18+ portfolio repos, 12,000+ aggregate tests, one published PyPI MCP package, and one production GHL real-estate-AI client is pivoting from contract/freelance into FTE-eligible AI/LLM Engineer roles. The funnel was broken (50+ Indeed apps in 90 days → 0 phone screens; root cause was Data Analyst resume ATS poisoning, fixed 2026-04-07). EnterpriseHub is the largest demonstrable surface in the portfolio (7,678 tests, multi-tier cache, agent mesh, Jorge bots, GHL integration, public Streamlit demo).

A 6-agent parallel audit + abbreviated 6-stage research pipeline (run 2026-04-27) produced binding findings:

- **Multi-track wedge is the right portfolio play.** Three tracks within 12 points: AI/LLM Engineer mid (79.0/100), Python Developer (73.5/100), QA/SDET LLM-eval niche (75.5/100 post-Wave-1). Senior AI ($180K+ / lab-tier $300K+) is *aspirational only* on a 12–18 month horizon, not this cycle.
- **Two of the most-cited case study numbers were credibility hazards** (88% cache hit rate as a tautology; 150 req/s claim with no Locust/k6 backing). Both already mitigated in the [2026-04-27 commit](#hot-fixes-already-shipped).
- **Single highest-leverage Wave 1 artifact:** eval harness with calibration. Lifts mid-AI, QA/SDET niche, AND senior-tier delta progress simultaneously.
- **Most undersold real assets:** production GHL client + `mcp-server-toolkit` PyPI package + EnterpriseHub's compliance pipeline (FHA/RESPA/TCPA).
- **Replacements from original spec plan:** production-incident write-up replaces conference talk; 2-paragraph adversarial-inputs doc replaces full STRIDE; design tokens lite replaces design system; second focused MCP server added as senior-tier delta.

Full audit and research artifacts: [`docs/specs/audits/2026-04-27/`](audits/2026-04-27/).

## 2. Goal & Success Criteria

**Goal.** Transform EnterpriseHub from "impressive freelance project" into a multi-track portfolio centerpiece that converts ≥3 phone screens within 30 days of Week 12.

**Success criteria (binding):**

1. Track decision evidence-based — multi-track wedge recorded in [`03-track-fit.md`](audits/2026-04-27/03-track-fit.md). ✅ done.
2. Wave 0 ships in ≤24 hours of spec activation: demo unlocked, AI-track resume cert-triaged.
3. Wave 1 ships clean by end of Week 2: eval harness in CI, real benchmarks committed, CASE_STUDY.md walked down to honest numbers.
4. Hero audit score 39/50 → 47+/50 by Wave 6 (measured weekly).
5. Phone screens ≥3 in the 30-day post-Wave-6 measurement window (vs. 0 prior 90 days).
6. Senior-tier deltas: 4 of 7 in motion by Week 12 (eval ✓, public benchmark ✓, MCP-2 ✓, production write-up ✓). Remaining 3 begin Cycle 2 (months 4–6).

## 3. Out of Scope

- Lab-tier ($300K+) senior FTE positioning — 12–18 month horizon, not this cycle.
- Solutions Engineer track polish — fit score 49.7; messaging only.
- Data Analyst track — retired 2026-04-07.
- Pricing/Gumroad SKU work — separate freelance-ops cycle.
- Direct outreach automation beyond the Wave 5 calibration experiment — sends remain manual.
- Building new skills/agents — this spec composes existing tooling.
- Changes to other portfolio repos (`docextract`, `mcp-server-toolkit`, etc.) — they get their own hireability specs after EnterpriseHub validates the pattern.

## 4. EARS-Style Requirements

### 4.1 Wave 0 — Funnel Unlock (Day 1)

- **REQ-W0-1.** When the spec is activated, the user shall toggle Streamlit Cloud Sharing → Public for `ct-enterprise-ai` (5-min user action) so any visitor can reach the dashboard without a Google login wall. *Closes audit E P0-3.*
- **REQ-W0-2.** When the AI-track resume is regenerated, it shall display ≤6 named certifications, retaining only IBM GenAI Engineering, DeepLearning.AI Deep Learning, Duke LLMOps, IBM RAG & Agentic AI, and Anthropic Claude Code in Action. *Per Phase 3 Stage 3 contrarian.*
- **REQ-W0-3.** When the resume is rotated, the user shall replace the stale variant in LinkedIn Open To Work, Indeed profile, and Upwork hourly profile within 24 hours. *Closes ATS-poisoning recovery loop.*
- **REQ-W0-4.** When Wave 0 closes, `ats-optimizer.py` shall be run against 5 fresh postings; baseline scores recorded in `~/.claude/reference/freelance/revenue-tracker.md`.

### 4.2 Wave 1 — Credibility & Eval (Weeks 1–2)

- **REQ-W1-1.** When `python -m benchmarks.bench_cache_live` is executed against a running stack, it shall read real hit/miss counters from `LLMObservabilityService` and produce a measurement (not a sample of an input distribution). *Closes audit C P0-1 fully; the 2026-04-27 commit was a partial credibility patch.*
- **REQ-W1-2.** Where load tests are claimed in CASE_STUDY.md or BENCHMARK_VALIDATION_REPORT.md, the system shall provide reproducible k6 scripts in `benchmarks/k6/{qualification_load,burst,sustained}.js` with results in `benchmarks/results/2026-W17/`. *Closes audit C P0-2.*
- **REQ-W1-3.** When a PR is opened, the eval harness in `.github/workflows/evals.yml` shall run promptfoo against golden datasets (`evals/datasets/{qualification,handoff,compliance}/*.jsonl`, sizes ≥500/400/300) and emit a reliability diagram PNG to `evals/results/2026-W17/`. *Closes audit B P0-4.*
- **REQ-W1-4.** Where `evals/` exists, an `evals/README.md` shall document the harness for QA/SDET-track positioning (separate landing for the eval-platform framing).
- **REQ-W1-5.** When `record_handoff_outcome` is called, it shall use `asyncio.create_task` from a running loop, not `asyncio.get_event_loop()` from a classmethod. *Closes audit A P0-2.*
- **REQ-W1-6.** When `docker compose -f docker-compose.observability.yml up` runs, it shall start cleanly with `otel-collector-config.yaml` present. *Closes audit C P0-9.*
- **REQ-W1-7.** Where claims appear in CASE_STUDY.md, BENCHMARK_VALIDATION_REPORT.md, or README.md that previously cited 88% cache hit rate or 150 req/s, the docs shall be revised to reflect Wave 1 measurements (or honest design-target framing where measurement is impossible). *Closes the credibility-hazard surface area completely.*
- **REQ-W1-8.** When Wave 1 closes, `/visual-audit EnterpriseHub --full` shall report first-impression score >7/10 and 0 P0 findings.

### 4.3 Wave 2 — Prompt Versioning + Cost Visibility (Weeks 3–4)

- **REQ-W2-1.** When prompts are changed, a versioned YAML in `prompts/` shall capture the new version with an eval-delta entry in a changelog file.
- **REQ-W2-2.** Where the LLM cost dashboard renders, it shall read live data from `LLMObservabilityService` rather than `random.seed(42)` mock data. *Closes audit C P0-10.*
- **REQ-W2-3.** When a request flows through the orchestrator and handoff service, OTLP traces shall be visible in Honeycomb (or Grafana Cloud) with `insecure=False` and proper auth headers. *Closes audit C P1-5.*

### 4.4 Wave 3 — Mesh Decision + ML + Demo Video (Weeks 5–6)

- **REQ-W3-1.** When Wave 3 begins, the team shall make an explicit choice on `AgentMeshCoordinator`: either implement real backpressure + health checks, or write `docs/adr/0011-agent-mesh-buildout-strategy.md` documenting the scaffold status with a graduation plan. Not both. *Closes audit A P0-1.*
- **REQ-W3-2.** Where handoff state lives across multiple workers, `docs/adr/0012-handoff-state-isolation.md` shall document the latency-vs-consistency tradeoff. *Closes audit A P1-4.*
- **REQ-W3-3.** When predictive-bot or seller-bot code paths execute, they shall use real `ml_analytics_engine` / `feature_engineering` modules, not `bots_stub.py` no-ops. Training data, model card documented in `docs/ml/`.
- **REQ-W3-4.** When `api/main.py` is loaded, startup shall be orchestrated by a `StartupOrchestrator` class with phased startup + tests, not the 300-line lifespan monolith. *Closes audit A P0-3.*
- **REQ-W3-5.** When Wave 3 closes, a 90-second product demo Loom shall be embedded in README hero (no narration overlay; clicks + outputs only per Stage 3 contrarian).

### 4.5 Wave 4 — Security Doc + Design Lite (Weeks 7–8)

- **REQ-W4-1.** Where adversarial-input handling is described, `docs/security/adversarial-inputs.md` shall provide a 2-paragraph write-up covering prompt injection, rate limits, audit logging, and FHA/RESPA/TCPA edge cases. *Replaces planned full STRIDE per Phase 2 DISPUTED resolution.*
- **REQ-W4-2.** When `_get_signing_secret` is called in `api_monetization.py`, it shall fail-closed with a RuntimeError if `API_KEY_SIGNING_SECRET` is unset or <32 chars. *Already shipped 2026-04-27; Wave 4 validates 100% test coverage on this path.*
- **REQ-W4-3.** When user passwords exceed 72 bytes, `jwt_auth.py` shall raise a 422 (matching `enhanced_auth.py`), not silently truncate. *Closes audit D P1-6.*
- **REQ-W4-4.** Where the Obsidian Ember theme is applied, design tokens shall be extracted into `streamlit_demo/.streamlit/tokens.toml` (or equivalent) for reuse — but no full component library shall be built. *Phase 2 DISPUTED resolution.*
- **REQ-W4-5.** When dashboard screenshots are referenced in the README, they shall match the current Ember theme (5 specific screenshots re-captured). *Closes audit E P1-7.*

### 4.6 Wave 5 — Public Technical Leadership (Weeks 9–10)

- **REQ-W5-1.** When Wave 5 closes, a second focused MCP server shall be published to PyPI solving one specific real-estate-AI workflow problem (MLS, GHL contact, or FHA-compliance tool). *Phase 2 senior-tier delta.*
- **REQ-W5-2.** When Wave 5 closes, a substantive production-incident write-up shall be published on the user's personal site or dev.to with unique numbers from real EnterpriseHub history. *Replaces conference-talk plan per Phase 2 DISPUTED resolution.*
- **REQ-W5-3.** When the orchestrator's 5-turn tool loop terminates by max-turn exhaustion, a Prometheus counter `tool_loop_max_turns_reached_total` shall increment and a structured warning log shall fire. *Closes audit A P1-1; provides the lived debugging story for the blog post.*
- **REQ-W5-4.** Before scaling outreach, the user shall send 5 personalized cold emails A/B (subject-line variant) and measure reply rate. Decision to scale to 10-prospect list gated on this calibration. *Spec plan original.*

### 4.7 Wave 6 — Conversion + Final Polish (Weeks 11–12)

- **REQ-W6-1.** When Wave 6 closes, CASE_STUDY.md shall incorporate all Wave 1–5 numbers and the production-incident narrative.
- **REQ-W6-2.** When Wave 6 closes, three resume variants (AI Engineer, Python Developer, QA/SDET LLM eval) shall be regenerated incorporating Wave 1–5 artifacts.
- **REQ-W6-3.** When Wave 6 closes, every link in resumes/profiles shall be validated end-to-end: AI = EnterpriseHub repo, Python = mcp-server-toolkit, QA = `evals/` README + datasets, consulting = production GHL case study.
- **REQ-W6-4.** When Wave 6 closes, `/hero-audit EnterpriseHub` shall report ≥47/50.
- **REQ-W6-5.** When Wave 6 closes, the 30-day phone-screen measurement window shall open with logging in `~/.claude/reference/freelance/revenue-tracker.md`.

## 5. Verification Plan

**Layer 0 — File presence per wave:** files described in REQ-* exist; `bd ready` shows wave's issues closed.

**Layer 1 — Code health (per wave gate):**
- `pytest` green at the wave's coverage gate (≥80% retained).
- `ruff check`, `mypy`, `bandit`, `pip-audit` clean.
- `bd sync` pushed.

**Layer 2 — End-to-end signal:**
- `/visual-audit EnterpriseHub --full` after Wave 1 (P0 trend down), Wave 3 (visual scores up), Wave 6 (final).
- `/hero-audit EnterpriseHub` weekly Friday — score tracked against 47+/50 target.
- Live demo URL responds <2s P95 from a clean session.
- Eval harness in CI runs on every PR with pass/fail gate visible in README badge.
- Phone-screen count tracked in revenue-tracker.md; 30-day post-Wave-6 window shows ≥3 (vs. 0 prior).

## 6. Rollback Triggers

- **Phase 2 adequacy <0.85** → already triggered (STANDARD adequacy verdict). Mitigated: re-run external stages (NotebookLM, Gemini, GPT, Grok) when tools are available; treat MEDIUM/DISPUTED items as soft until validated.
- **Any wave regresses Hero Audit score by >2 points** → pause, write incident note, replan next wave.
- **ML integration in Wave 3 introduces >5% latency regression** → revert to stub fallback, file P1, ship rest of wave without it.
- **Phone screen lands during Waves 1–4** → freeze in-flight code, jump to Wave 6 narrative refresh + interview prep, resume after interview cycle closes.

## 7. ADR Pointers

ADRs to be written during execution (anchors for senior-tier credentialing):
- `docs/adr/0011-agent-mesh-buildout-strategy.md` (Wave 3, REQ-W3-1)
- `docs/adr/0012-handoff-state-isolation.md` (Wave 3, REQ-W3-2)
- Optional `docs/adr/0013-eval-harness-promptfoo-vs-deepeval.md` (Wave 1) — if the choice has a non-obvious tradeoff worth recording.

## 8. Hot-Fixes Already Shipped (Pre-Wave-0)

Committed 2026-04-27 in `81c65f78` → `546267d2`:
- `api_monetization.py:518` fail-closed signing-secret pattern (closed `EnterpriseHub-3nw8`).
- `bench_cache.py` honest framing — Monte Carlo simulation labeling (closed `EnterpriseHub-dvvt`).
- `benchmarks/run_all.py` — caller updates for `modeled_hit_rate` rename.
- Pre-existing test failure (`tests/caching/test_analytics.py::TestHitMissRatio::test_total`) filed as separate P2 bug.

## 9. Beads Tracking

Parent epic: `EnterpriseHub-td5t` (open).

Wave epics (created when Wave 0 ships): one per Wave 0–6 with `bd dep add wave-N+1 wave-N`.

Existing related issues:
- `EnterpriseHub-j50d` — Demo unlock (Wave 0, user action)
- `EnterpriseHub-3nw8` — Secret fail-closed ✅ closed
- `EnterpriseHub-dvvt` — Bench cache honest framing ✅ closed
- `EnterpriseHub-qnef` — Jorge testimonial request (related, supports Wave 5 outreach)

## 10. Cadence Integration

- Daily `/freelance-ops` continues; this spec produces evidence the digest references.
- Weekly `/hero-audit EnterpriseHub` (Fridays) — the wave checkpoint.
- Bi-weekly ATS check via `ats-optimizer.py` — score delta logged.
- Wave-boundary session-close hygiene: `git status → bd sync → commit → bd sync → push`.

## 11. Cross-References

- [Phase 1 audit synthesis](audits/2026-04-27/01-audit-synthesis.md) — P0/P1/P2 register
- [Phase 2 research synthesis (Stage 5)](audits/2026-04-27/05-claude-synthesis.md) — claim confidence matrix
- [Phase 3 track-fit (binding)](audits/2026-04-27/03-track-fit.md) — wedge verdict + scoring
- [Phase 4 roadmap (binding)](audits/2026-04-27/04-roadmap.md) — wave-by-wave detail
- [Companion research file](2026-04-27-enterprisehub-hireability-research.md) — cached external findings
- Source plan: `~/.claude/plans/create-a-deep-spec-cosmic-cascade.md`
