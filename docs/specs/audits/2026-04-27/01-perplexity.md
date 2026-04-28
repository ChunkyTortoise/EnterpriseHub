# Stage 1 — Web Landscape Research (Perplexity-equivalent)

**Method:** Three WebSearch queries scoped to 2026 hiring market, salary bands, and commodity-vs-differentiator skill classification.
**Date:** 2026-04-27
**Sources:** Cited inline; full URLs in the closing list.

---

## Query A — "2026 senior AI LLM engineer hiring portfolio requirements"

**Headline findings:**

- 2026 hiring managers scan portfolios for **production signals**: how candidates handle failures, structure data, connect systems, and ship working software — not just "did the API call succeed."
- The single most-cited interview prompt: *"Show me one project where the hard problem was not 'call the API' but 'the API call failed in a way that mattered.'"*
- Portfolio-required topic areas: **retrieval, structured outputs, autonomous agents, evaluation, deployment.** RAG is the single most in-demand AI engineering skill in 2026.
- **Eval harness expectations** are explicit and specific: hallucination checks, accuracy scoring, domain constraint validation, response explainability. Validation must include rule-based, statistical, OR semantic checks. Alignment + performance monitoring is table stakes.
- **Observability stack expectation:** Prometheus + Grafana (or cloud-native equivalents). Continuous monitoring, performance testing, error monitoring required.
- **Senior LLM engineer comp** runs **$200K–$320K**, with a 25–40% premium over comparable ML engineer roles.

**Implication for EnterpriseHub:** the empty `evals/` directory is exactly the gap the screen will hit. The README needs a "production failure case study" — a moment where something broke and the response shows judgment.

---

## Query B — "2026 AI engineer salary bands FAANG vs startup contract vs FTE"

**Top of market (FAANG / AI labs):**

- **Anthropic / OpenAI senior:** total comp $545K–$756K (Levels.fyi data). OpenAI senior $620–730K, lead $700K+.
- **Anthropic Lead Software Engineer:** $756K total comp ceiling.
- AI-focused companies use simpler IC1–IC4 ladders (vs FAANG's L4-L8 sprawl). Compensation **heavily weighted toward equity** — outsized upside if valuation grows.
- **Base salary range** for senior at AI labs: $300K–$425K. Equity differential is the spread.

**Mid-market / startup:**

- Seed-stage startups now offering FAANG-level cash for "select elite talent" — but this is a narrow band, not the typical hire.
- $300K retention bonuses (2-yr vest) at OpenAI for new-grad technical hires (Aug 2025). Signals aggressive FTE incentives beyond base.
- Remote + full-SF salary + equity is achievable at some SF startups for proven candidates.

**Implication for the candidate's track-fit:** The $130K+ band the spec targets is the *floor* of mid-market AI engineering, not senior at top-tier labs. A clean entry into mid-market AI engineer ($130–180K) is realistic at the 8–12 week milestone. Anthropic/OpenAI tier ($500K+) is aspirational and would require substantially more public technical leadership and deeper system-design evidence than the current portfolio supports.

---

## Query C — "2026 GenAI commodity skills saturated vs differentiator scarce"

**Strategic / scarce / differentiator skills (the things that move screens):**
- **Agentic RAG** (not basic RAG — basic RAG is commodity)
- **LLMOps** (deployment, monitoring, drift detection at production scale)
- **AI output validation** (eval harness with statistical/semantic checks)
- **Governance and security** (specifically MCP security, AI red-teaming, application security applied to AI)

**Commoditizing skills (saturated, no longer differentiates):**
- Basic RAG implementations (BM25 + dense, off-the-shelf embeddings)
- Off-the-shelf agent frameworks (CrewAI, AG2, BeeAI) without custom orchestration
- Streamlit "chat with X" demos
- "I added an LLM call to my CRUD app" projects
- Cert collections without production evidence

**2026 portfolio expectation (per industry analysts):**
"By the end of a structured learning path, your portfolio should have an LLM app, a fine-tuned model, a RAG system, at least one diffusion-based project, and an AI agent system."

**Specifically called out as 2026 must-have technologies:** RAG, LLMOps, agents, MCP. Frameworks: CrewAI, AG2, BeeAI, Model Context Protocol.

**Implication for EnterpriseHub:**
- **What we have that's commodity:** basic RAG (in `advanced_rag_system/`), Streamlit demo, agent frameworks, multi-LLM orchestrator.
- **What we have that's scarce-adjacent:** the production GHL integration (real CRM, real money flowing) is rarer than the agent code. The compliance pipeline (FHA/RESPA/TCPA) is genuinely differentiating — most portfolios have nothing comparable.
- **What we don't have:** LLMOps observability (incomplete), AI output validation (empty evals/), MCP security or red-teaming evidence (none).
- **MCP positioning is a quiet asset:** the user already published `mcp-server-toolkit` to PyPI — that's literally one of the 2026 must-haves and rarely seen on portfolios. Should be more prominent.

---

## Cross-Query Patterns

1. **"Production signals" beats "code volume."** Three queries agreed: hiring managers scan for evidence the candidate has shipped to real users with real consequences. EnterpriseHub's *one production GHL client* is genuinely scarce and underweighted in current positioning.
2. **Eval harness is the single most-named 2026 differentiator.** Mentioned in Query A directly, Query C as "AI output validation," and the comp data in Query B implicitly (senior-tier roles screen for it). The empty `evals/` is the highest-leverage repair.
3. **MCP-related skills are emerging high-signal.** Mentioned in Query C as a must-have, Query A as part of the agent/tooling stack. The user's PyPI package is exactly this.
4. **Cert stacking is no longer signal.** None of the three queries mention certifications as a portfolio criterion. The 21-cert stack is at best neutral, at worst a "less than the production work" indicator.
5. **The 8–12 week roadmap can plausibly close mid-market ($130–180K) gap; cannot plausibly close lab-tier ($300K+) gap.** Web data says comp at top labs requires evidence the user does not currently have time to produce in this window (multi-year public tech leadership, peer-reviewed contributions, tier-1 OSS maintainership).

---

## Inputs to Stage 5 (Synthesis)

- HIGH-confidence claims (≥2 sources):
  - Eval harness is table-stakes for senior AI engineering screens.
  - RAG is the most-demanded 2026 skill.
  - Production-failure case studies are explicitly screened for.
  - MCP / Model Context Protocol is named as a 2026 must-have.
  - $130K is the entry point for mid-market AI engineer; $300K+ requires lab-tier evidence.

- DISPUTED across sources:
  - Whether Streamlit demos are still credible at senior level (some sources include, others say "tutorial-grade").
  - Specific weight of conference talks vs. tech blog posts.

- NEW LEADS for Stage 6 NotebookLM:
  - "Production failure case study" — does any of EnterpriseHub's history (CASE_STUDY.md, recent commits) contain a real incident worth writing up?
  - MCP positioning — is `mcp-server-toolkit` undersold given 2026 demand signal?

---

## Sources

- [Top 10 Most In-Demand AI Engineering Skills and Salary Ranges in 2026 — Second Talent](https://www.secondtalent.com/resources/most-in-demand-ai-engineering-skills-and-salary-ranges/)
- [How to Hire LLM Engineers in 2026 — KORE1](https://www.kore1.com/hire-llm-engineers-2026/)
- [5 AI Portfolio Projects That Actually Get You Hired in 2026 — DEV.to](https://dev.to/klement_gunndu/5-ai-portfolio-projects-that-actually-get-you-hired-in-2026-5bpl)
- [AI Engineer Cost in 2026 — Arsum](https://arsum.com/blog/posts/hire-ai-engineer/)
- [Anthropic Salaries — Levels.fyi](https://www.levels.fyi/companies/anthropic/salaries)
- [How Much Does Anthropic Pay in 2026? — Glassdoor](https://www.glassdoor.com/Salary/Anthropic-Salaries-E8109027.htm)
- [Breaking Into AI in 2026 — DataExec](https://dataexec.io/p/breaking-into-ai-in-2026-what-anthropic-openai-and-meta-actually-hire-for)
- [Anthropic Software Engineer Salary $563K–$756K — Levels.fyi](https://www.levels.fyi/companies/anthropic/salaries/software-engineer)
- [AI Engineer Salary Guide 2026 — KORE1](https://www.kore1.com/ai-engineer-salary-guide/)
- [Generative AI Roadmap 2026 — Scaler](https://www.scaler.com/blog/generative-ai-roadmap/)
- [The most in-demand AI skills — TechTarget](https://www.techtarget.com/searchcio/tip/In-demand-AI-skills)
- [MCP vs RAG vs AI Agents — ByteByteGo](https://blog.bytebytego.com/p/ep202-mcp-vs-rag-vs-ai-agents)
- [Top LLMs and AI Trends for 2026 — Clarifai](https://www.clarifai.com/blog/llms-and-ai-trends)
