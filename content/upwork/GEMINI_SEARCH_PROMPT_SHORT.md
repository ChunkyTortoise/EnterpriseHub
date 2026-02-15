# Gemini Upwork Search - Concise Version

**For quick iterations** - use this shorter prompt if you want faster results.

---

# PROMPT START

Search Upwork for freelance Python/AI jobs posted in the last 7 days and evaluate them for me.

## My Profile

**Expert in**: RAG systems, FastAPI (async), Claude API, multi-agent orchestration, PostgreSQL + Redis, Streamlit dashboards, pytest/TDD

**Portfolio highlights**:
- 8,500+ tests across 11 repos (all CI green)
- 89% LLM cost reduction via caching
- 3 live Streamlit demos
- docqa-engine: hybrid RAG (BM25 + dense)
- EnterpriseHub: 5,100 tests, real estate AI platform
- AgentForge: multi-LLM orchestration (550+ tests)

**Rates**: $65-75/hr, $500+ fixed-price minimums

## Search Keywords (Priority Order)

1. "Claude API" OR "Anthropic"
2. "RAG" + "vector database"
3. "FastAPI" + "async"
4. "multi-agent" OR "AI orchestration"
5. "Streamlit dashboard"
6. "document processing" + "AI"

## Evaluation Criteria (Score each 0-10)

1. **Tech Match**: How well does it match RAG/FastAPI/Claude/multi-agent?
2. **Rate**: Is it ≥$65/hr or ≥$500 fixed?
3. **Client**: Payment verified? Previous hires? Money spent?
4. **Scope**: Clear requirements and realistic timeline?
5. **Portfolio Fit**: Can I showcase my demos/repos?

## Output Format (for each job)

```
Job: [Title]
URL: [Link]
Rate: [Amount] | Client: [hires/spent/verified?]
Fit Score: X.X/10
Match: [Which of my repos/demos applies]
Hook: [1-sentence proposal angle]
Rec: APPLY/SKIP | Priority: HIGH/MED/LOW
```

**Find 10-15 jobs, show top 10 by fit score, include URLs.**

# PROMPT END

---

## Follow-Up Prompts

After results:

- **"Expand on job #3 - give me full proposal outline"**
- **"Search for 10 more Streamlit-only jobs"**
- **"Which job is fastest to land? (easiest proposal)"**
- **"Find fixed-price $500-1000 quick wins only"**

---

## Quick Copy Command

```bash
# macOS - copy to clipboard
cat content/upwork/GEMINI_SEARCH_PROMPT_SHORT.md | pbcopy

# Then paste into https://gemini.google.com
```

---

**When to use SHORT vs LONG**:
- **SHORT**: Quick daily searches, specific keyword focus
- **LONG**: Comprehensive search, detailed evaluation, portfolio matching
