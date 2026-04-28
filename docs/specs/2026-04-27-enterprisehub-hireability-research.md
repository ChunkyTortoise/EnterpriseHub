# Companion Research File — 2026-04-27 EnterpriseHub Hireability Spec

**Cache validity:** Reusable for 7 days per spec-creator convention. Re-run external stages when external tools become available.
**Adequacy verdict:** STANDARD (downgraded from DEEP target — see Stage availability below).

---

## Tool Availability Snapshot (2026-04-27)

| Stage | Source | Status | File |
|---|---|---|---|
| 0 | Pre-flight (live demo + budget cap + prefit strawman) | ✅ Complete | [`audits/2026-04-27/00-prefit-strawman.md`](audits/2026-04-27/00-prefit-strawman.md) |
| 1 | WebSearch (3 queries: hiring requirements, salary bands, commodity vs. differentiator) | ✅ Genuine external | [`audits/2026-04-27/01-perplexity.md`](audits/2026-04-27/01-perplexity.md) |
| 2 | Gemini 2.5 Pro deep technical | ⚠️ multi-llm MCP unavailable; ran as Claude synthesis with Phase 1 audit evidence | [`audits/2026-04-27/02-04-gemini-gpt.md`](audits/2026-04-27/02-04-gemini-gpt.md) |
| 3 | Grok contrarian | ❌ MCP returned 403 in two attempts | [`audits/2026-04-27/03-grok.md`](audits/2026-04-27/03-grok.md) (Claude-as-contrarian, labeled) |
| 4 | GPT-5.5-thinking structured roadmap | ⚠️ same as Stage 2 | [`audits/2026-04-27/02-04-gemini-gpt.md`](audits/2026-04-27/02-04-gemini-gpt.md) |
| 5 | Claude synthesis | ✅ Complete | [`audits/2026-04-27/05-claude-synthesis.md`](audits/2026-04-27/05-claude-synthesis.md) |
| 6 | NotebookLM institutional knowledge | ❌ Auth expired (Google sign-in required) | not produced this run |

**External-source diversity achieved:** 3 web sources (Stage 1) + 3 hiring-persona models from Phase 1 audit-F (`multi-model-researcher` agent successfully queried Gemini + GPT + Grok in parallel for that audit). Net: 6 external voices, asymmetrically distributed. Re-running Stages 3 + 6 + clean Stage 2/4 with available tools would add the remaining triangulation.

---

## Phase 1 Inputs (Audit Side)

| Audit | Score | Lead findings |
|---|---|---|
| A — Architecture | 7/10 | Mesh coordinator scaffolded; `record_handoff_outcome` async hazard; `api/main.py` lifespan monolith |
| B — Eval / Prompt | 2/10 | Empty `evals/` + orphan `__pycache__`; un-reconciled threshold tuples; keyword-counting evaluator |
| C — Observability | 4/10 | 88% cache-hit tautology; missing k6 scripts; Honeycomb auth not wired; mock cost dashboard |
| D — Security | 7/10 | Solid baseline; soft secret fallback (fixed); bcrypt truncation; missing STRIDE/threat-model doc |
| E — Visual / Demo | 3.8/10 → 7+/10 | Demo auth-gated (5-min unlock); 5 outdated palette screenshots; no glassmorphism |
| F — Hiring Persona | conditional contingency | Multi-track wedge verdict; senior ceiling 58 without Wave 1 |

Full reports in `audits/2026-04-27/audit-{A..F}-*.md`. Synthesis in `01-audit-synthesis.md`.

---

## Phase 2 Claim Confidence Matrix

### HIGH (≥1 external source + ≥1 internal stage)

1. Eval harness with calibration is the single highest-leverage Wave 1 artifact for senior AI screens.
2. Production-incident write-ups are explicitly screened for; largely missing from candidate portfolios.
3. MCP / Model Context Protocol is a 2026 must-have differentiator; `mcp-server-toolkit` is undersold.
4. Cert volume above ~7 becomes a negative signal on AI-track resumes.
5. 88% cache-hit / 150 req/s claims are credibility hazards (already mitigated 2026-04-27).
6. Senior AI band requires evidence the candidate has not had time to build (multi-year public tech leadership). 8-12 weeks closes mid-AI ($130-180K), not senior.
7. Production GHL real-estate-AI client is the most undersold real asset.
8. Demo URL must be unlocked / replaced; auth-gated demo is worse than no demo.

### MEDIUM (internal-only or single-source external)

- promptfoo > DeepEval > homegrown for eval harness.
- 5-artifact ranking: load benchmarks > demo video > eval > OTLP > prompt versioning.
- 8–12 week roadmap closes contractor-to-FTE gap (treated as conditional).
- Single substantive technical post beats blog-post volume.

### DISPUTED (sources disagree — resolutions in `04-roadmap.md`)

- Streamlit demos at senior level — keep if production content; replace if "chat with X" pattern. Resolution: keep.
- STRIDE threat model weight — replace full STRIDE with 2-paragraph adversarial-inputs doc. Resolution in `REQ-W4-1`.
- Conference talks vs. blog posts — production-incident write-up replaces conference talk. Resolution in `REQ-W5-2`.

### UNIQUE / QUARANTINED

- "Agency CTOs use 'one production reference' threshold for $75 vs $125/hr." (Stage 3, not corroborated.)
- "Streamlit Cloud free tier auto-flagged as junior signal." (Stage 3, not corroborated.)

---

## Track-Fit Snapshot

| Track | Score (now) | Score (post-Wave-1) | Verdict |
|---|---:|---:|---|
| AI/LLM Engineer (mid) | 79.0 | 84+ | **PRIMARY** |
| AI/LLM Engineer (senior) | 47.5 | 62 | 12–18 month horizon |
| Python Developer | 73.5 | 76 | Wide funnel, lower ceiling |
| QA/SDET (LLM eval niche) | 63.5 | 75.5 | **SECONDARY (highest leverage)** |
| Solutions Engineer | 49.7 | 54.7 | Suppress |

**Wedge verdict:** Multi-track. AI mid + QA/SDET niche + consulting tertiary.

Full method in `03-track-fit.md`.

---

## Key External Sources (Stage 1 web, archived)

- Levels.fyi Anthropic salaries — $563K–$756K Senior/Lead
- Glassdoor Anthropic — median $600K
- KORE1 LLM Engineer hiring guide 2026 (production-signal emphasis)
- ByteByteGo MCP vs RAG vs Agents — 2026 must-haves
- TechTarget in-demand AI skills — agentic RAG + LLMOps + governance as differentiators
- Clarifai LLM trends 2026

Full link list in `01-perplexity.md`.

---

## When to Re-Run This Pipeline

- **Hard re-run trigger:** any HIGH-confidence claim disputed by primary evidence (e.g., a phone screen reveals a hiring manager actually IS reading STRIDE docs — flips DISPUTED to HIGH against current resolution).
- **Soft refresh:** at the Wave 6 measurement gate (Week 12), to validate market signal hasn't shifted before Cycle 2 planning.
- **Tool-availability re-run:** when NotebookLM / Grok / multi-llm MCP are restored, run Stages 3 + 6 + clean 2/4 to upgrade adequacy from STANDARD → DEEP.
