# Pre-fit Strawman — Provisional Track Weights for Phase 1 Audit Emphasis

**Created:** 2026-04-27 (Phase 0)
**Scope:** This is a *provisional* scoring pass using only existing inventory. Phase 3 produces the binding track-fit assessment after the 6-agent audit and full research pipeline. Phase 1 agents read this so audit emphasis is track-aware.

---

## Phase 0 Pre-flight Results

| Check | Result | Action |
|---|---|---|
| Live demo HTTP | `303 redirect loop` (10 redirects, 2.5s) — likely Streamlit auth gate or stuck wake | **Flag for Phase 1-E** — visual-repo-auditor must investigate via Chrome MCP, log in with `demo_user/Demo1234!`, capture real screenshots. Do not assume the URL is broken; it may just be the auth-wall redirect pattern. |
| Audit directory | `docs/specs/audits/2026-04-27/` created | Ready |
| Parent epic | `EnterpriseHub-td5t` (P1, open) | All phase/wave issues link to this |
| Token budget recorded at start | (manual — caller to note in this file before Phase 1 launch) | Hard caps: Phase 1 ≤ $15, Phase 2 ≤ $25, Phase 3–4 ≤ $5 |

---

## Inventory Snapshot (read-only inputs)

**Certifications (1,831 hours / 21 certs):**
- AI/ML stack — 411h (IBM GenAI Engineering 144h, DeepLearning.AI Deep Learning 120h, Microsoft AI/ML Eng 75h, Duke LLMOps 48h, IBM RAG & Agentic AI 24h)
- Data/BI stack — 917h (Google DA 181h, Google Adv DA 200h, Google BI 80h, IBM BI 141h, Microsoft AI-Enhanced DA 120h, Microsoft Viz 87h, Microsoft GenAI for DA 108h)
- Other — 503h (Marketing 273h, Python for Everybody 60h, Linux/OSS 60h, Anthropic Claude Code 3h, plus Vanderbilt GenAI Strategy 40h, Google Cloud GenAI 25h, Vanderbilt ChatGPT 30h, etc.)

**Repo evidence (current):**
- EnterpriseHub: hero 39/50 (Cycle 1), 7,678 tests, multi-tier cache validated, agent mesh, compliance pipeline, ADRs ×10, public Streamlit demo
- mcp-server-toolkit: hero 42/50 (Cycle 2), PyPI published, 6 MCP servers
- docextract: hero 39/50 (Cycle 1), RAG/document AI
- 15+ supporting repos with 3,100+ tests across portfolio

**Production proof:**
- 1 production client (Jorge Real Estate Bots, live since Jan 2026)
- PyPI published package
- 6 live deployments
- 3 OSS PRs

**Funnel signal:**
- 50+ Indeed apps in 90 days → 0 phone screens (root cause: Data Analyst resume ATS poisoning, fixed 2026-04-07)
- ATS signal reset still pending (~7-14 days)

---

## Provisional Fit Scores (Strawman — Subject to Phase 3 Binding)

Using the rubric from the spec's Phase 3 (0–100 scale, weighted components). These are first-cut estimates from inventory only; Phase 1 audit will produce the binding artifact-evidence inputs.

| Track | Strawman | Confidence | Notes |
|---|---:|---|---|
| **AI/LLM Engineer (mid)** | **78** | High | Cert match strong (411h AI stack), repo evidence strong (3 hero repos), market demand high. Interview-readiness held back by missing eval harness + unverified load tests. |
| **AI/LLM Engineer (senior)** | **52** | Medium | Strong system-design depth (mesh, cache, handoff) and ADRs. Held back hard by: no public technical leadership, no eval/calibration evidence, no conference-grade write-up, cert tier (Coursera, not university grad-level). Senior is reachable with Wave 1+5 deliverables. |
| **Python Developer** | **74** | High | Repo breadth 18+ repos, deep test culture, OSS PRs, PyPI package. Cert match thinner than AI track but Python for Everybody + Linux/OSS provides foundation. Wide funnel, lower ceiling. |
| **QA/SDET (LLM eval niche)** | **70** | Medium-High | Test count is the leading number (12k+ across portfolio, 7,678 in EnterpriseHub alone) — that's a rare signal. Held back by *empty* `evals/` directory: the niche credential is missing the niche artifact. Wave 1 closes this completely. |
| **Solutions Engineer** | **62** | Medium | Multi-CRM evidence strong, demo polish medium, case studies exist but only the SE one is discoverable. Public speaking/content gap is structural; Wave 5 closes it. |

**Strawman verdict (provisional, NOT binding):**
- Top three within ~10 points (AI mid 78, Python 74, QA 70) → **Multi-track wedge looks viable** at the portfolio level.
- Senior-AI gap (52) is *closable* — concrete artifact deltas: eval harness with calibration, conference write-up, 1+ OSS RFC, public benchmark. All sequenced in Waves 1–5 of the spec.
- The QA/SDET niche has the highest *scarcity bonus* per unit of work (an LLM eval framework is a rarer credential than another generic Python repo). Wave 1 builds it; Wave 6 surfaces it as a distinct portfolio link.

---

## Audit Emphasis Cues for Phase 1

Each of the six Phase 1 agents should weight findings using this guidance:

- **Agent A (Architecture):** weight findings that signal senior-tier system design (e.g., circuit breaker correctness, async pattern depth, ADR coverage of non-obvious tradeoffs). De-emphasize cosmetic refactors.
- **Agent B (Evals):** this is THE highest-leverage audit. Empty `evals/` is a known gap. Quantify exactly what a senior ML engineer expects to see (golden datasets, calibration curves, A/B framework, regression gate in CI) and produce a buildable spec snippet for Wave 1.
- **Agent C (Observability/Performance):** focus on the "claim vs. evidence" delta — the BENCHMARK_VALIDATION_REPORT.md says "150 req/s" but no k6 scripts exist. That gap matters more than additional micro-optimizations.
- **Agent D (Security):** weight findings tied to hireable artifacts (threat model doc, audit log completeness) over CVE noise. A formal threat model is more credentialing than another `pip-audit` pass.
- **Agent E (Visual/UX):** the live demo redirect loop is the headline finding to investigate. A broken demo URL on a portfolio link is a screen-killer; this is P0 regardless of other visual scores.
- **Agent F (Hiring Persona):** all three personas should explicitly score "would I move this candidate to a phone screen in 60 seconds?" as the top-line question. Surface concrete objections — the user wants to know the *real* gap-to-senior, not encouragement.

---

## Open Questions for Phase 1+2 to Resolve

1. **Senior-tier path:** is the gap closable in 8–12 weeks given current artifact velocity? (Phase 1-F + Phase 2-Grok answer this with a contrarian read.)
2. **Multi-track vs. focus:** the strawman says wedge is viable. Phase 3 confirms or overrides with the binding score. Resume-strategy implications follow.
3. **Cert noise vs. signal:** with 21 certifications, which 5–8 actually move the needle on senior AI screens vs. become noise? (Phase 2 NotebookLM query c.)
4. **Demo URL:** is the redirect a known auth pattern, a regression, or a Streamlit Cloud sleep state? (Phase 1-E.)
5. **EnterpriseHub vs. portfolio:** if Phase 1-F persona review says "needs a second flagship," the negative-finding contingency activates. The spec is paused before Phase 2 spend.

---

**Phase 0 status: COMPLETE.** Proceed to Phase 1 (parallel 6-agent audit wave).
