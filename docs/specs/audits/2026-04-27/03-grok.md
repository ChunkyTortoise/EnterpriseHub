# Stage 3 — Contrarian Challenge

**Method note:** Grok MCP returned 403 in two attempts (likely API key/rate limit). This stage is a **Claude-playing-contrarian** pass over the Phase 1 evidence + Stage 1 web findings + Stage 2/4 synthesis. It is *not* a separate-model voice — downstream synthesis (Stage 5) should weight accordingly: HIGH confidence requires agreement with a non-Claude source, not just internal-Claude agreement across stages.

---

## What's overhyped on the consensus list

**STRIDE threat models:** mostly theater for senior AI hiring. STRIDE is a deliverable for SOC2 audits, not a portfolio screener. A senior AI hiring manager will spend 0 seconds on a STRIDE doc. They might glance for a 2-paragraph "How we think about adversarial inputs to LLM systems" — that's it. Don't write a full STRIDE.

**Medium / dev.to blog posts:** signal value collapsed in 2024. Saturated with AI-generated content. A *single* substantive technical post on a personal site or as a dev.to post-mortem can move the needle, but only if it has unique numbers (e.g., "We measured 89% cache hit on production traffic — here's the cache-eviction strategy that made it work"). Generic "Three-tier cache cut our LLM bill 89%" is a saturated template.

**Design system:** unless the role involves frontend ownership, design tokens for a Streamlit dashboard are noise. Solutions Engineer track is the only one that meaningfully weights this. Skip for the AI-engineering tracks.

**Generic conference talks:** PyCon AI track is not the differentiator it was in 2022–23. Senior screens look at *what was said*, not *that you spoke*. A talk title that doesn't immediately demonstrate technical novelty will be ignored. Better: a written technical write-up that's referenceable, archivable, citable in interviews.

**Eval harness obsession:** mostly correct, but with a sharp footnote — the harness itself is now table-stakes (commodity). What differentiates is **the dataset** (golden dataset of 500+ real-distribution samples is rarer than yet another DeepEval/promptfoo wiring). The screener cares about whether you've done the messy work of curating golden data, not whether you typed `pip install promptfoo`.

---

## What looks impressive but isn't

**7,678 tests.** Test count is a junior-diligence proxy, not a senior-judgment signal. A senior reviewer will sample 10 tests at random and ask "is this testing behavior or implementation?" If half are mocks of mocks, the count actively hurts. EnterpriseHub's parametrized TCPA tests (with Spanish keywords) are the senior-tier signal — surface those specifically. The aggregate count buries the actual evidence.

**Cert stacking (21 certs).** Above ~7 certs, additional volume becomes a red flag. The hiring-manager mental model: "this person collects credentials instead of producing." On a senior AI resume, 3–5 named certs maximum, only the ones with technical depth (DeepLearning.AI Deep Learning Specialization, Duke LLMOps, IBM GenAI Engineering — keep these). Drop the marketing certs from the AI-track resume entirely. They're noise that signals "data analyst trying to pivot."

**Streamlit dashboards.** "Premium" is a stretch. Streamlit is a tutorial-grade signal in 2026. Necessary if the demo runs there, but never lead with it. Lead with the *production GHL integration* — that's the rarer artifact.

**PyPI package count.** One published package is enough; counting them is junior. Treat `mcp-server-toolkit` as one *artifact*, not part of a "and here are 4 more packages" list.

**Streamlit Cloud demo.** Free-tier sleeping app + auth gate (Phase 0 finding) is worse than no demo because it visibly fails on first impression. Either upgrade to a paid tier with always-on, or replace with a 90-second Loom showing the live system at the user's discretion.

---

## What hiring managers actually ignore in 2026

- **Code coverage percentages on the README badge.** 80%+ has been performative for years. Senior reviewers care about *what's tested*, not the bar.
- **CI green badge.** Expected. Not a signal.
- **"Production-grade" / "enterprise-ready" / "battle-tested" copy on the README.** Reverse-signals — used by candidates without production evidence.
- **"Multi-LLM orchestration."** Saturated keyword. Everyone has wired Claude + GPT. The specific decision *why and when to route* is what matters.
- **Cert hours total ("1,831 hours!").** Reads as "I sat through videos." Replace with "I shipped X to production with metrics Y."
- **GitHub stars under ~200.** Not a positive signal at this band.
- **Mermaid architecture diagrams that show 6 boxes and 8 arrows.** Universal cliché. A hand-annotated screenshot of the actual production system with one weird tradeoff explained in 2 sentences beats it.

---

## What's missing from the consensus that would actually move screens

1. **An incident write-up.** "Here's the production bug we found in week N, what it cost, how we caught it, and the change we made to prevent recurrence." Senior reviewers screen for this specifically. EnterpriseHub recent commits show real fixes (`security: bump CVE deps`, `fix: guard AnalyticsService instantiation`) — these are write-up candidates.

2. **A measurement that contradicts intuition.** Numbers that surprised the team. "We expected the L2 cache to dominate; it didn't because of X." Reveals real engineering thinking. The current 88% / 150 req/s claims are the *opposite* — they're suspiciously round and confirm-the-thesis numbers.

3. **A "why we did NOT use X" decision.** Negative-space ADRs reveal taste. "We considered LangGraph for the agent mesh and rejected it because…" is more senior than "we chose LangGraph because it's popular."

4. **A real cost/latency tradeoff curve.** Not a static number — a curve. P50/P95/P99 by model, by cache tier, by input length. Most portfolios have nothing comparable.

5. **A direct user-flow video.** 90 seconds, no narration overlay, just clicks and outputs. Senior reviewers under time pressure want to *see the thing work*, not read about it.

6. **An MCP-specific differentiator.** With MCP named as a 2026 must-have in Stage 1, the user's `mcp-server-toolkit` is undersold. A second, *focused* MCP server that solves a specific real-estate-AI workflow problem (e.g., MLS listing tool, GHL contact tool, FHA-compliance tool) is a higher-signal artifact than another generic agent demo.

---

## The Coursera cert problem

**The honest read:** 21 Coursera certs reads as "career changer who learned by watching" if not contextualized correctly. The volume itself becomes a negative around cert #8 in pure AI-engineer screens.

**Triage rule for the AI-track resume:**
- KEEP (signal): IBM GenAI Engineering, DeepLearning.AI Deep Learning, Duke LLMOps, IBM RAG & Agentic AI, Anthropic Claude Code in Action.
- DROP from the AI-track resume entirely (move to a separate "Continuing Education" hidden section if needed): Google Marketing, Meta Social Media, Vanderbilt ChatGPT for Personal Automation, Microsoft Data Visualization (unless applying to data-engineering hybrid roles).
- The Google Data Analytics + Adv DA stack is genuinely useful for *data-engineer* roles — keep on a separate Data Engineering resume variant, drop entirely from AI-engineer resume.

**Total certs visible on AI-track resume: 5–6 max.** The remaining are hidden assets, not displayed. This is the single highest-leverage resume change available right now and it's free.

---

## The honest gap

**Is 8–12 weeks enough to close mid-AI ($130K)?** Yes, if Wave 1 (eval + honest benchmarks) ships clean and the resume cert problem gets fixed week 1. The production GHL client + MCP package + (post-Wave-1) eval harness is enough evidence for mid-market AI engineer screens. The funnel will move with ATS reset + better targeting (LinkedIn outreach pairing, not just Indeed cold apps).

**Is 8–12 weeks enough to close senior-AI ($180K+)?** Almost certainly not. Senior at AI labs requires:
- Multi-year demonstrated public technical leadership (blog series with audience, OSS maintainership, conference circuit, peer reviews).
- Evidence of working at senior scale (millions of requests, real outage post-mortems, multi-team coordination).
- A unique technical contribution that's defensible in a peer-engineer interview at depth.

The portfolio described has the *substrate* for senior — production system, real compliance domain, multi-LLM orchestrator, MCP package. What it lacks is *time-in-public* — that takes 12-24 months minimum to establish credibly. The 8–12 week roadmap should target mid-AI definitively and *position* for senior on a 12-18 month horizon, not promise it.

**Most undersold real asset:** the production GHL real-estate-AI client. "I have one production AI client paying me money" is rarer in the candidate pool than 21 certs and 12K tests combined. It should be in the resume's first three lines, not buried.

**Most overcooked claim:** "8.5/10 architecturally" (the user's own pre-fit assessment in [00-prefit-strawman.md](00-prefit-strawman.md)). Drop self-rating language entirely from public-facing materials. Self-scoring reads as junior insecurity. Let the artifacts make the case.
