# LinkedIn Sprint — February 7, 2026

## Objective
Maximize hiring visibility across 4 parallel workstreams in one session.

---

## Workstream 1: Connection Requests (Browser)
**Owner**: Main agent (browser automation)
**Target**: 20-30 connection requests sent

### Strategy
- Connect with people whose posts we commented on (Greg Coquillo, Shubham Vora, Ayesha Shafique, Aditya Sharma, Taseer Mehboob)
- Connect with AI/ML engineers, hiring managers, and recruiters visible in feed
- Use personalized notes referencing shared interest in AI engineering
- Prioritize: people who posted AI content, recruiters at AI companies, engineers at target companies

### Connection Note Templates
1. **Post commenter**: "Great post on [topic] — I commented with my experience building [relevant system]. Would love to connect and follow your content."
2. **AI Engineer**: "Fellow AI engineer here — I build multi-agent systems and RAG pipelines in Python/FastAPI. Would love to connect."
3. **Recruiter**: "AI Engineer with production LLM orchestration experience (7 open-source repos, 750+ tests). Open to full-time and contract roles."

---

## Workstream 2: Job Applications Research (Agent)
**Owner**: Research agent (background)
**Target**: Curated list of 15-20 matching roles

### Search Criteria
- **Titles**: AI Engineer, ML Engineer, LLM Engineer, Python Backend Engineer, AI Platform Engineer
- **Skills match**: Python, FastAPI, LLM/Claude/GPT, RAG, Redis, PostgreSQL, multi-agent systems
- **Location**: Remote-friendly, US-based
- **Level**: Mid to Senior (3+ years equivalent experience)
- **Sources**: LinkedIn Jobs, AI-specific job boards, YC companies

### Output
- Company name, role title, link, match score, key requirements, salary range if listed
- Sorted by match quality
- Flag any that mention: real estate, chatbots, multi-agent, or RAG (direct experience match)

---

## Workstream 3: Experience Role Addition (Browser)
**Owner**: Main agent (browser automation, after connections)
**Target**: Add "AI Engineer — EnterpriseHub Platform" role

### Role Details
- **Title**: AI Engineer
- **Company**: Self-employed / Independent
- **Duration**: January 2023 – Present
- **Location**: Palm Springs, California (Remote)
- **Description**:
  Architected and built a production AI platform for real estate operations:
  - Multi-agent chatbot system (3 specialized bots) with cross-bot handoff orchestration, confidence-based routing, and A/B testing framework
  - LLM orchestration layer supporting Claude, Gemini, GPT, and Perplexity with 3-tier caching (memory/Redis/PostgreSQL) — 89% token cost reduction
  - RAG pipeline with hybrid BM25 + dense retrieval for document Q&A
  - FastAPI async backend, Streamlit BI dashboards, GoHighLevel CRM integration
  - 750+ automated tests across 7 open-source repositories, all CI green

  Stack: Python, FastAPI, PostgreSQL, Redis, Claude API, Streamlit, Docker, GitHub Actions

### Skills to Tag
Python, FastAPI, LLM, Claude, RAG, Redis, PostgreSQL, Multi-Agent Systems, AI Engineering

---

## Workstream 4: Week 2 Content Drafts (Agent)
**Owner**: Writing agent (background)
**Target**: 3 new post drafts

### Post Topics
Based on what performed well in Week 1 and gaps in content strategy:

1. **"The hidden cost of AI agent memory"** — Deep dive into why most agent memory implementations fail at scale. Reference 3-tier cache architecture, real numbers on cache hit rates, and the PostgreSQL long-term pattern storage approach.

2. **"I replaced 4 Python linters with one tool"** — Practical post about ruff replacing black, isort, flake8, and pylint. Show before/after CI pipeline, speed gains, and config simplification. Developers love tooling posts.

3. **"What I learned benchmarking 4 LLM providers on the same task"** — Deeper version of Post 5, with specific latency numbers (p50/p95/p99), cost per query breakdowns, and when to use which provider. Reference the open-source agentforge benchmark tool.

### Format Requirements
- 150-250 words each
- Opening hook (pain point or contrarian take)
- 3-5 specific technical details with real numbers
- Engagement question at the end
- 3-5 hashtags
- No emojis, no AI-generated feel
- Written in Cayman's voice (direct, technical, experience-backed)

---

## Execution Plan

```
[PARALLEL]
├── Agent A (background): Job listings research → output to plans/JOB_LISTINGS_FEB7.md
├── Agent B (background): Week 2 post drafts → output to plans/LINKEDIN_POSTS_WEEK2.md
└── Main thread (browser):
    ├── Step 1: Add Experience role to LinkedIn profile
    └── Step 2: Send 20-30 connection requests
```

## Success Criteria
- [ ] 15+ matching job listings compiled with links
- [ ] 3 new post drafts ready to publish
- [ ] AI Engineer experience role added to profile
- [ ] 20+ connection requests sent
