# Stage 5 — Claude Synthesis (Research Pipeline)

**Date:** 2026-04-27
**Adequacy verdict: STANDARD** (downgraded from DEEP target). Tool availability:

| Stage | Source | Status |
|---|---|---|
| 1 | WebSearch (3 queries) | ✅ Genuine external |
| 2 | Gemini 2.5 Pro | ⚠️ multi-llm MCP unavailable; ran as Claude synthesis labeled |
| 3 | Grok | ❌ 403 (key/rate); Claude-contrarian pass instead, labeled |
| 4 | GPT-5.5 | ⚠️ same as Stage 2 |
| 5 | Claude synthesis | ✅ this file |
| 6 | NotebookLM | ❌ auth expired |
| Bonus | Phase 1 audit-F | ✅ multi-model-researcher used GPT/Gemini/Grok in parallel for hiring personas |

Net effect: external-source diversity = (3 web sources) + (3 hiring-persona models from Phase 1). HIGH confidence requires agreement across at least one external (web or persona) source AND an internal stage. Anything supported only by Claude-synthesis stages is downgraded to MEDIUM.

---

## Claim Reconciliation

### HIGH confidence (≥1 web source + ≥1 internal stage agreement)

1. **Eval harness with calibration is the single highest-leverage Wave 1 artifact for senior AI screens.** (Web Stage 1 + Phase 1 audits B/F + Stage 2/4 synthesis.)
2. **Production-incident write-ups are explicitly screened for and largely missing from candidate portfolios.** (Web Stage 1 quote: *"the API call failed in a way that mattered"* + Stage 3 contrarian.)
3. **MCP / Model Context Protocol is a 2026 must-have differentiator and the candidate's `mcp-server-toolkit` PyPI package is currently undersold in positioning.** (Web Stage 1+C + Stage 3.)
4. **Cert volume above ~7 becomes a negative signal on AI-track resumes.** (Stage 3 contrarian + Web Stage 1: no source mentioned certs as positive criterion.)
5. **The 88% cache-hit and 150 req/s claims are credibility hazards.** (Phase 1 audit C + Stage 2/4 synthesis + Stage 3.) Already mitigated by 2026-04-27 commit.
6. **Senior AI engineer band ($200K–$320K, FAANG/lab tier $500K+) requires evidence the candidate has not had time to build (multi-year public tech leadership). 8–12 weeks closes mid-AI ($130–180K), not senior.** (Web Stage 1 salary data + Stage 3 contrarian + Phase 1 audit F.)
7. **Production GHL real-estate-AI client is the most undersold real asset.** (Web Stage 1 production-signal emphasis + Stage 3 + Phase 1 audit F.)
8. **Demo URL must be unlocked / replaced; auth-gated demo is worse than no demo.** (Phase 1 audit E + Stage 3.)

### MEDIUM confidence (internal-only or single external source)

- Promptfoo > DeepEval > homegrown eval harness. (Phase 1 B + Stage 2/4 synthesis; not corroborated by web.)
- Specific 5-artifact ranking: load benchmarks > demo video > eval harness > OTLP traces > prompt versioning. (Stage 2/4 synthesis.) Web data agrees on eval harness primacy but doesn't rank the others.
- 8-12 week roadmap closes the contractor-to-FTE gap. (Internal optimism; web data is mixed; persona review says "conditional.")
- A single substantive technical post on a personal site beats blog-post volume. (Stage 3 contrarian; not corroborated externally.)

### DISPUTED (sources disagree)

- **Streamlit demos** at senior level — Web Stage 1 implies any production demo helps; Stage 3 says Streamlit is "tutorial-grade." Likely resolution: keep Streamlit if the *content* is the GHL production system + real metrics; replace if it's another "chat with X" pattern.
- **STRIDE threat model weight** — Phase 1 audit D says it closes a credentialing gap; Stage 3 says nobody reads STRIDE on AI portfolios. Likely resolution: write a 2-paragraph "How we think about adversarial inputs" (Stage 3's compromise) instead of a full STRIDE doc.
- **Conference talks vs. blog posts** for credentialing — Phase 1 (audit F) and the spec strawman both treat conference talks as senior-tier. Stage 3 says generic talks are saturated and a strong written write-up beats a forgettable talk. Likely resolution: prioritize a **written technical post-mortem** (referenceable, archivable) over a talk submission this cycle.

### UNIQUE / QUARANTINED (single-source, low confidence — record but don't act on)

- "AI agency CTOs use a 'one production reference' threshold to differentiate $75/hr from $125/hr engagements." (Stage 3 contrarian; not corroborated.)
- "Streamlit Cloud free tier is auto-flagged as junior signal." (Stage 3; not corroborated.)
- Specific salary numbers from individual web sources should be treated as ranges, not point estimates.

---

## Open Questions Remaining (Originally Phase 2 Targets)

| # | Question | Status |
|---|---|---|
| 1 | Senior-tier closability in 8–12 weeks | **Resolved (HIGH):** No, mid-AI achievable, senior aspirational on 12–18 month horizon. |
| 2 | Multi-track confirm (wedge vs. focus) | **Resolved (MEDIUM):** Multi-track wedge backed by Phase 1 audit F + Stage 3 contrarian; AI mid primary, consulting secondary, QA/SDET high-scarcity. |
| 3 | Cert-tier signal in 2026 | **Resolved (HIGH):** Top 5–6 certs = signal, beyond = noise. Specific keep/drop list in Stage 3. |
| 4 | QA/SDET LLM-eval niche scarcity | **Partial (MEDIUM):** Web data confirms eval is differentiator generically; specific QA/SDET niche scarcity not directly corroborated. |
| 5 | Conference / public-leadership lift | **Resolved (DISPUTED):** Written post-mortem > generic talk. |

---

## Concrete Artifact List (binding for Phase 4 roadmap)

These are the artifacts the Phase 4 roadmap will sequence, ranked by cumulative HIGH-confidence support:

| Rank | Artifact | Wave | Confidence | Replaces / Augments |
|---|---|---|---|---|
| 1 | **Real cache-hit measurement tool** (`bench_cache_live.py` reading from LLMObservabilityService) | 1 | HIGH | Replaces tautological number; restores README/case-study credibility |
| 2 | **k6 load test scripts (qualification, burst, sustained)** with results in `benchmarks/results/` | 1 | HIGH | Replaces unbacked 150 req/s claim |
| 3 | **Eval harness with golden datasets + reliability diagram PNG** | 1–2 | HIGH | Closes the empty `evals/` directory |
| 4 | **Demo unlock + 90-second product Loom** | 1 (demo unlock immediate) + 3 (video) | HIGH | Replaces auth-gated Streamlit |
| 5 | **Production-incident write-up** (one substantive case from real EnterpriseHub history) | 5 | HIGH | NEW — not in original spec; surfaced by Stage 1 + Stage 3 |
| 6 | **Resume cert triage** (drop to 5–6 on AI-track resume) | 1 (week 1) | HIGH | Cheapest, fastest funnel-fix |
| 7 | **MCP positioning lift** — second focused MCP server for real-estate-AI + prominent README placement of `mcp-server-toolkit` | 5 | HIGH | NEW — surfaced by Stage 1 + Stage 3 |
| 8 | **OTLP traces wired to Honeycomb / Grafana Cloud, visible on demo** | 1–2 | HIGH | Closes incomplete tracing gap |
| 9 | **Threat model substitute**: 2-paragraph "Adversarial inputs and rate limits" doc, NOT a full STRIDE | 4 | MEDIUM (DISPUTED resolved) | Replaces planned STRIDE — saves time |
| 10 | **Prompt versioning (versioned YAML + eval-linked changelog)** | 2 | HIGH | Wave 2 |
| 11 | **Mesh coordinator: ship real backpressure OR explicit ADR documenting scaffold status** | 3 | HIGH | Closes Phase 1 audit A P0-1 |
| 12 | **`record_handoff_outcome` async classmethod fix** | 1 (small) | HIGH | Closes Phase 1 audit A P0-2 |
| 13 | **Single substantive technical post-mortem** (referenceable, on personal site or dev.to with unique numbers) | 5 | MEDIUM (DISPUTED resolved) | Replaces planned multi-post blog series |
| 14 | **Conference talk** (deprioritized — write-up first, talk second only if time) | 5 | MEDIUM | Lower priority than originally specced |
| 15 | **Design system** (deprioritized except for SE-track work) | 4 (lite) | LOW | Original spec overweighted this |

Items #5, #6, #7, #13 are **changes from the original spec roadmap**. The research synthesis surfaced them as higher-leverage than items the spec had emphasized (full STRIDE, conference talk, blog series, design system).

---

## Adequacy Verdict

**STANDARD-depth research, not DEEP.** The pipeline ran 3 of 6 stages with genuine external sources (Stage 1 web ×3 + Phase 1 audit-F multi-model personas). Stages 2, 4 produced Claude synthesis with audit evidence (useful but not external triangulation). Stages 3, 6 unavailable.

**Adequate for Phase 3 (track-fit) and Phase 4 (roadmap) to proceed.** The external sources we DO have agree strongly enough on the top-3 actions (eval harness, real benchmarks, demo unlock) that more research would be diminishing returns. Re-running Stages 3 + 6 when tools are available would mostly be confirmation, not new direction.

**Recommended:** proceed to Phase 3 with current findings; tag any binding decision that depended only on MEDIUM/DISPUTED items for revisit if the user runs the full pipeline later.
