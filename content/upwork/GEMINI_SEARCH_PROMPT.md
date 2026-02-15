# Gemini Upwork Job Search & Evaluation Prompt

**Usage**: Copy this entire prompt and paste it into Gemini (gemini.google.com)

---

# PROMPT START

I need you to search Upwork for freelance jobs that match my skills and evaluate their suitability. Here's my complete profile:

## My Skills & Expertise

**Core Competencies**:
- AI/ML: Claude API, GPT-4, Gemini, RAG systems (BM25/TF-IDF/semantic), Multi-Agent Systems, NLP, Prompt Engineering
- Backend: FastAPI (async), SQLAlchemy, Pydantic, Alembic, Click CLI, REST APIs
- Databases: PostgreSQL, Redis (3-tier caching), SQLite, ChromaDB, FAISS vector databases
- Testing: pytest, TDD, unittest.mock, 80%+ coverage, integration testing
- DevOps: Docker, GitHub Actions CI/CD, monitoring, alerting (P50/P95/P99)
- Data Science: scikit-learn, pandas, forecasting, clustering, anomaly detection
- Web: httpx (async), BeautifulSoup, Playwright, Streamlit
- Security: Fernet encryption, JWT, OAuth 2.0, PII protection, CCPA/GDPR

**Programming Languages**: Python 3.11+ (expert), SQL, JavaScript, Bash

## Portfolio Proof Points

- **11 production repositories** with 8,500+ automated tests, all CI green
- **33 Architecture Decision Records** documenting engineering tradeoffs
- **89% LLM cost reduction** via 3-tier Redis caching (88% hit rate verified)
- **4.3M tool dispatches/sec** in AgentForge core engine
- **<200ms orchestration overhead** (P99: 0.095ms) for multi-agent AI workflows
- **Docker support** across all 10 repos (Dockerfile + docker-compose)
- **3 live Streamlit demos** (https://ct-prompt-lab.streamlit.app/, https://ct-llm-starter.streamlit.app/, https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/)
- **1 PyPI package** (mcp-server-toolkit)
- **3 CRM integrations** (GoHighLevel, HubSpot, Salesforce) with unified protocol
- **Mermaid architecture diagrams** in every README
- **20+ years software engineering** experience

## Key Projects

1. **EnterpriseHub** (~5,100 tests): Real estate AI platform with multi-bot orchestration, GHL CRM integration, 3-tier caching, FastAPI async backend, PostgreSQL + Redis
2. **AgentForge** (550+ tests): Multi-LLM orchestration framework with async interface, provider abstraction, ReAct agent loop, tracing
3. **docqa-engine** (500+ tests): RAG system with BM25 + dense hybrid retrieval, cross-encoder re-ranking, 94 automated quality scenarios
4. **insight-engine** (640+ tests): Streamlit analytics dashboard with statistical testing, KPI framework, anomaly detection
5. **jorge_real_estate_bots** (360+ tests): 3-bot system with cross-bot handoff, confidence scoring, rate limiting, pattern learning

## Rate Ranges

- **Hourly (contract)**: $65-75/hr (target)
- **Project (quick wins)**: $300-800
- **Project (custom)**: $1,500-4,000
- **Project (enterprise)**: $8,000-12,000/phase

**Minimum acceptable**: $55/hr for hourly, $500 for fixed-price

## Job Search Criteria

### High-Priority Keywords (Search for these)

**Premium tier ($70-100+/hr)**:
1. "Claude API" OR "Anthropic"
2. "multi-agent" OR "AI orchestration"
3. "RAG optimization"
4. "LLM cost reduction" OR "LLM cost optimization"
5. "async Python" + "FastAPI"

**Solid tier ($60-75/hr)**:
6. "RAG" + "vector database"
7. "semantic search" + "embeddings"
8. "FastAPI" + "PostgreSQL" + "Redis"
9. "Streamlit dashboard" OR "Streamlit analytics"
10. "document processing" + "AI"
11. "AI chatbot integration"
12. "retrieval augmented generation"

**Quick wins ($500-1,500 fixed)**:
13. "Streamlit" + fixed price $500-1,500
14. "Python automation" + "proof of concept"
15. "AI dashboard" + fixed price

### Client Red Flags (AVOID these)

❌ No payment method verified
❌ 0 hires, $0 spent
❌ Rate < $40/hr for expert work
❌ "Junior" or "Entry level" for complex AI
❌ "Test project" for $50
❌ Vague requirements with huge scope
❌ "Simple chatbot" (usually not simple)
❌ Location only in very low-budget countries

### Green Flags (PRIORITIZE these)

✅ Payment verified
✅ 1+ previous hires
✅ $1,000+ total spent
✅ Clear, specific requirements
✅ Mentions specific technologies I know
✅ Realistic timeline
✅ Based in US, Canada, UK, EU, Australia
✅ Rate ≥ $60/hr or fixed ≥ $500

## Your Task

**Step 1**: Search Upwork for jobs matching the high-priority keywords above. Focus on recently posted jobs (last 7 days).

**Step 2**: For each job you find, evaluate it using this scoring system:

### Evaluation Criteria (Score 0-10 for each)

1. **Technical Match** (0-10):
   - 10: Perfect match (RAG, FastAPI, async Python, Claude, multi-agent)
   - 7-9: Strong match (2-3 of my core skills)
   - 4-6: Partial match (1-2 of my skills)
   - 0-3: Weak match (generic Python/AI)

2. **Rate/Budget** (0-10):
   - 10: $75+/hr or $2,000+ fixed
   - 8-9: $65-74/hr or $1,000-1,999 fixed
   - 6-7: $55-64/hr or $500-999 fixed
   - 0-5: Below my minimums

3. **Client Quality** (0-10):
   - 10: Payment verified, 5+ hires, $10K+ spent, 5-star reviews
   - 7-9: Payment verified, 2-4 hires, $1K-9K spent
   - 4-6: Payment verified, 1 hire, $100-999 spent
   - 0-3: No payment method or no history

4. **Scope Clarity** (0-10):
   - 10: Crystal clear requirements, deliverables, timeline
   - 7-9: Clear requirements, some ambiguity
   - 4-6: Vague but workable
   - 0-3: Very vague or unrealistic scope

5. **Portfolio Showcase Opportunity** (0-10):
   - 10: Perfect fit for my live demos (Streamlit, RAG, multi-agent)
   - 7-9: Good fit for 2-3 repos
   - 4-6: Can reference 1-2 repos
   - 0-3: Hard to connect to my work

**Overall Fit Score**: Average of the 5 criteria

**Step 3**: Output in this format:

```
## Job #1: [Title]

**URL**: [Upwork job URL]
**Posted**: [Date]
**Rate/Budget**: [Amount]
**Client**: [Hire count] hires, [Amount] spent, [Yes/No] payment verified

**Description Summary**: [2-3 sentence summary of what they need]

**Evaluation Scores**:
- Technical Match: X/10 - [brief reason]
- Rate/Budget: X/10 - [brief reason]
- Client Quality: X/10 - [brief reason]
- Scope Clarity: X/10 - [brief reason]
- Portfolio Showcase: X/10 - [brief reason]

**Overall Fit Score: X.X/10**

**My Portfolio Match**:
- [Relevant repo 1]: [Why it matches]
- [Relevant repo 2]: [Why it matches]
- [Key metric to mention]: [e.g., "89% cost reduction" or "8,500+ tests"]

**Proposal Angle**: [1-2 sentence hook for cover letter]

**Red Flags**: [Any concerns, or "None"]
**Green Flags**: [Positive indicators, or "None"]

**Recommendation**: APPLY / CONSIDER / SKIP
**Priority**: HIGH / MEDIUM / LOW

---
```

**Step 4**: After listing all jobs, provide a summary:

```
## Summary

**Total Jobs Found**: X
**Recommended to Apply**: X (HIGH priority) + X (MEDIUM priority)
**Skip**: X

**Top 3 Priorities** (in order):
1. [Job title] - Fit: X/10 - [Why it's #1]
2. [Job title] - Fit: X/10 - [Why it's #2]
3. [Job title] - Fit: X/10 - [Why it's #3]

**Estimated Connects Needed**: X (for recommended jobs)
**Estimated Time to Apply**: X hours (assuming customized proposals)
```

## Additional Instructions

- Search for at least 15-20 jobs across different keyword combinations
- Prioritize jobs posted in the last 7 days
- If you find more than 20 good matches, show only the top 10 by Overall Fit Score
- Include the actual Upwork job URLs so I can click through
- Be honest about red flags - I'd rather skip bad fits than waste connects
- For "Overall Fit Score", only recommend "APPLY" if score ≥ 7.0/10
- For priority, use: HIGH (≥8.5), MEDIUM (7.0-8.4), LOW (<7.0)

## What Success Looks Like

I'm looking for 5-10 high-quality jobs where:
- I can credibly demonstrate expertise with my existing portfolio
- The rate/budget is fair for the scope
- The client seems serious and well-funded
- I can write a compelling, specific proposal highlighting relevant proof points

**Start the search now.** Focus on RAG, Claude API, FastAPI, and multi-agent keywords first, then expand to other terms if needed.

# PROMPT END

---

## How to Use This Prompt

1. **Copy everything** from "# PROMPT START" to "# PROMPT END"
2. **Paste into Gemini** at https://gemini.google.com
3. **Review the results** - Gemini will search and evaluate jobs
4. **Track recommended jobs** using the tracker:
   ```bash
   python scripts/upwork_tracker.py add <url> --title "..." --rate "..." --fit <score>
   ```
5. **Write customized proposals** for HIGH priority jobs first

## Tips for Best Results

- **Run multiple times** with different keyword focuses if needed
- **Ask Gemini to elaborate** on any job that looks interesting
- **Request proposal angles** for specific jobs: "Give me a detailed proposal outline for Job #3"
- **Update criteria** if you want different rate ranges or priorities

## Example Follow-Up Prompts

After Gemini returns results, you can ask:

- "Give me a detailed proposal outline for Job #5, emphasizing my RAG expertise"
- "Search for 10 more jobs focusing only on 'Streamlit dashboard' and 'data analytics'"
- "Which of these jobs best showcases my EnterpriseHub project?"
- "Rank these by fastest time-to-revenue (quick fixed-price wins first)"

---

**Last Updated**: 2026-02-15
