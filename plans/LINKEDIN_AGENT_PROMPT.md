# LinkedIn Optimization — Agent Kickoff Prompt

Copy the prompt below into a new Claude Code chat to begin implementation.

---

## PROMPT (copy from here)

```
I need to implement the LinkedIn optimization spec at `plans/LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md`.

## Context
- My LinkedIn: https://www.linkedin.com/in/caymanroden/
- Current score: 3.1/10 — strong tech substance, zero visibility
- 14 gaps identified (G1-G14), prioritized fixes, 90-day content strategy
- The spec has section-by-section rewrites ready to use

## What I Need Help With

### Phase 1: Profile Copy (Do First)
1. **Headline rewrite** — finalize from the 4 options in spec section 2.1
2. **About section rewrite** — use spec section 2.2 template, personalize for my voice
3. **Experience restructure** — rewrite EnterpriseHub bullets per spec section 2.3
4. **Education** — help me decide what to put (I need to fill in the placeholder)
5. **Skills audit** — generate the full ordered list of 25-30 skills per spec section 2.5
6. **Featured section** — write descriptions for all 5 items per spec section 2.6
7. **Projects section** — write descriptions for all 7 repos per spec section 2.11

### Phase 2: Content Strategy
8. **First 5 LinkedIn posts** — draft using the templates in spec Part 3:
   - Introduction post ("I've been building AI systems...")
   - Technical insight (token cost reduction framework)
   - Project showcase (multi-agent chatbot handoff)
   - Hot take (an AI trend opinion)
   - How-I-Built-It (EnterpriseHub deep dive)
9. **Connection request templates** — 3 variants (for engineers, recruiters, CTOs)

### Phase 3: Supplementary Assets
10. **Banner image text/layout spec** — dimensions, text, tech logos to include
11. **Recommendation request templates** — 3 templates for different relationship types
12. **Open to Work settings** — final list of job titles and locations

## Key Files to Reference
- `plans/LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md` — the full spec (primary reference)
- `CLAUDE.md` — project context, tech stack, bot APIs
- `.claude/reference/domain-context.md` — market/domain context
- `README.md` — project overview for accurate descriptions

## Repos to Reference for Descriptions
- EnterpriseHub: FastAPI + Streamlit + PostgreSQL + Redis + Claude/Gemini AI, 91+ routes, 11 CI workflows
- jorge_real_estate_bots: 3 AI chatbots, cross-bot handoff, A/B testing, 279 tests
- Revenue-Sprint: Injection Tester + RAG Cost Optimizer + Agent Orchestrator, 240 tests
- ai-orchestrator (AgentForge): Unified async LLM interface, benchmarking, 27 tests
- insight-engine: Auto-profiling analytics, dashboards, attribution, 63 tests
- docqa-engine: RAG Q&A + prompt lab, BM25+dense retrieval, 94 tests
- scrape-and-serve: Web scraping + Excel-to-web + SEO tools, 62 tests

## Constraints
- Keep my voice authentic — I'm direct, technical, no-BS
- No emoji in professional copy (About, Experience) unless specifically for LinkedIn posts
- All metrics must be accurate and traceable to real work
- Don't oversell — "independent project" not "startup", "platform" not "Bloomberg alternative"
```

---

## Files the Agent Will Need

| File | Purpose |
|------|---------|
| `plans/LINKEDIN_OPTIMIZATION_SPEC_FEB_2026.md` | Full spec with all 14 gaps, rewrites, content strategy |
| `CLAUDE.md` | Tech stack, services, bot APIs, architecture |
| `.claude/reference/domain-context.md` | Real estate market context, terminology |
| `README.md` | Project overview |
| `.claude/reference/quality-standards.md` | Performance metrics, KPIs |

## Expected Outputs

The agent should produce a single deliverable document with:
1. Finalized headline (1 choice from 4 options)
2. Finalized About section (~200 words)
3. Restructured Experience bullets
4. Education recommendation
5. Ordered skills list (25-30)
6. Featured section descriptions (5 items)
7. Projects section descriptions (7 repos)
8. 5 draft LinkedIn posts (ready to publish)
9. 3 connection request templates
10. Banner image spec
11. 3 recommendation request templates
12. Open to Work settings
