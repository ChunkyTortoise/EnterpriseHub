# Gemini Proposal Writing Prompt

**Use this AFTER** Gemini finds suitable jobs to generate customized proposals.

---

# PROMPT START

Write a customized Upwork proposal for this job. Use my portfolio evidence to demonstrate expertise.

## Job Details

**Job Title**: [Paste job title]
**Job Description**: [Paste full job description]
**Rate/Budget**: [Paste rate]
**Client Info**: [Paste client hire count, spend, location]

## My Profile for This Proposal

**Relevant Portfolio**:
- **EnterpriseHub** (~5,100 tests): Real estate AI platform, multi-bot orchestration, FastAPI async, PostgreSQL + Redis, 3-tier caching (89% cost reduction), GHL CRM integration
- **docqa-engine** (500+ tests): Hybrid RAG (BM25 + dense embeddings), reciprocal rank fusion, cross-encoder re-ranking, 94 automated quality scenarios, precision@k/recall@k metrics
- **AgentForge** (550+ tests): Multi-LLM orchestration, async provider abstraction (Claude/GPT/Gemini/local), ReAct agent loop, evaluation framework, tracing
- **insight-engine** (640+ tests): Streamlit analytics dashboards, statistical testing, KPI framework, anomaly detection, SHAP explainability
- **jorge_real_estate_bots** (360+ tests): 3-bot conversational AI, cross-bot handoff (0.7 confidence threshold), rate limiting, circular prevention, pattern learning

**Live Demos**:
- Prompt Lab: https://ct-prompt-lab.streamlit.app/
- LLM Starter: https://ct-llm-starter.streamlit.app/
- AgentForge: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/

**Key Metrics**:
- 8,500+ automated tests across 11 repos
- 89% LLM cost reduction (88% cache hit rate verified)
- 4.3M tool dispatches/sec in AgentForge
- P99 orchestration overhead: 0.095ms
- 33 Architecture Decision Records documenting tradeoffs
- Docker + CI/CD across all repos

**Skills**: Python 3.11+, FastAPI (async), RAG (BM25/dense/hybrid), Claude/GPT/Gemini APIs, PostgreSQL, Redis (L1/L2/L3 caching), SQLAlchemy, Alembic, pytest/TDD, Streamlit, Docker, GitHub Actions

**Rate**: $65-75/hr or $500-4,000 fixed depending on scope

**Experience**: 20+ years software engineering, production AI systems in real estate and document processing

## Proposal Requirements

**Structure** (300 words max):
1. **Hook** (1-2 sentences): Demonstrate I understand their SPECIFIC problem, not generic AI
2. **Credibility** (1 paragraph): Match ONE specific repo/metric to their need
3. **Approach** (3 bullet points): What I'd do differently/better than other applicants
4. **Evidence Table** (4-5 rows): Their requirement → My implementation
5. **CTA** (1 sentence): Portfolio link + next step

**Tone**: Professional, confident but not arrogant, metric-driven, business-focused

**Must Include**:
- At least ONE specific metric (89% cost reduction, 8,500+ tests, P99 latency, etc.)
- Link to relevant live demo if applicable
- Portfolio link: https://chunkytortoise.github.io
- GitHub: https://github.com/ChunkyTortoise

**Must Avoid**:
- ❌ Generic statements ("I'm an expert in AI")
- ❌ Listing all my skills
- ❌ Copy-paste feel
- ❌ Overpromising
- ❌ Mentioning price/rate (Upwork handles that)
- ❌ More than 300 words

## Examples of Good Hooks

**For RAG job**:
"The distinction you draw between 'RAG for chatbots' and 'RAG for meaning-critical systems' is exactly right. I built docqa-engine specifically because pure semantic search returns chunks that are *similar* but not *correct*."

**For optimization job**:
"Debugging a RAG system that's 'functional but not performant' requires someone who can read the existing pipeline, find the bottleneck, and fix it without breaking what works. I've implemented a 3-tier caching layer that reduced redundant LLM calls by 89%."

**For FastAPI job**:
"Your tech stack — FastAPI, PostgreSQL, Redis — is essentially what I already have running in production. EnterpriseHub (~5,100 tests) is a modular AI system built on exactly these technologies."

## Example Evidence Table Format

```markdown
| Your Requirement | My Implementation |
|-----------------|-------------------|
| RAG pipeline | Hybrid BM25 + dense retrieval (docqa-engine, 500+ tests) |
| Cost optimization | 89% LLM cost reduction via 3-tier Redis caching |
| Production quality | 8,500+ tests across 11 repos, all CI green |
| FastAPI + async | EnterpriseHub (5,100 tests) with async orchestration |
```

## Output Format

Provide:
1. **The complete proposal** (ready to copy-paste into Upwork)
2. **Why this approach**: 2-3 sentences explaining the positioning strategy
3. **Alternative hook**: One different opening in case I prefer it
4. **Which demo to emphasize**: If multiple repos apply, which to lead with

**Write the proposal now.**

# PROMPT END

---

## Workflow

1. **Gemini finds jobs** (use GEMINI_SEARCH_PROMPT.md)
2. **Copy job details** from a HIGH priority match
3. **Paste this prompt** + job details into Gemini
4. **Get customized proposal** ready to submit
5. **Track application**:
   ```bash
   python scripts/upwork_tracker.py update <id> --status applied
   ```

## Quick Iteration

If the first proposal isn't quite right:

- **"Make it more technical - emphasize the RAG architecture"**
- **"Shorten to 200 words"**
- **"Lead with the 89% cost reduction metric instead"**
- **"Give me 3 different hook options to choose from"**
- **"Focus more on the live Streamlit demos"**

---

## Example Usage

```
[Paste GEMINI_PROPOSAL_PROMPT.md]

Job Title: Senior RAG Engineer for Document Intelligence
Job Description: We need an expert to build a RAG system for processing 10K+ financial documents. Must use hybrid retrieval, have experience with reranking, and optimize for precision over recall. Python, FastAPI, PostgreSQL required.
Rate/Budget: $70/hr, 20-30 hrs/week, 3-month contract
Client Info: 5 hires, $25K spent, payment verified, US-based
```

Gemini will generate a tailored proposal emphasizing docqa-engine's hybrid retrieval, 94 quality scenarios, and precision@k metrics.

---

## Pro Tips

1. **Paste the FULL job description** - more context = better proposal
2. **Mention client budget** - helps Gemini calibrate scope
3. **Note client location/industry** - can tailor examples
4. **Ask for multiple versions** if you're unsure which angle to take
5. **Request specific CTAs**: "End with an offer to do a paid 2-hour scoping call"

---

**Last Updated**: 2026-02-15
