# Task 4: Braintrust Network Account Setup

**Agent Model**: Claude Sonnet 4.5
**Tools Required**: Browser automation (claude-in-chrome)
**Estimated Time**: 20-25 minutes
**Priority**: P1 (Medium - Unique model: 100% client rate, no platform fees)

---

## Objective

Create Braintrust freelance account with complete technical profile emphasizing AI/ML expertise.

## Prerequisites

**Why Braintrust?**
- **0% platform fees** - Keep 100% of client rate
- **BTRST token rewards** - Earn governance tokens for good work
- **Remote-first** - All jobs are remote
- **High-quality clients** - Vetted enterprises (Porsche, Nike, NASA)
- **Web3 native** - But accepts USD payments

**Required Info**:
- Email: caymanroden@gmail.com
- Location: Palm Springs, CA
- Rate: $75/hr (can adjust per client)
- Portfolio: chunkytortoise.github.io
- GitHub: github.com/ChunkyTortoise

---

## Agent Prompt

```
You are setting up a Braintrust freelance account for an AI/ML engineer.

CONTEXT:
- Braintrust = Web3 freelance network with 0% fees
- Talent keeps 100% of client rate
- High-quality remote clients (Fortune 500 companies)
- Goal: Create compelling technical profile to match with AI/ML projects

TASK CHECKLIST:

1. Navigate to usebraintrust.com/sign-up
2. Select "Join as Talent" (NOT "Hire Talent")
3. Create account with caymanroden@gmail.com

4. Complete basic profile:
   - Full name: Cayman Roden
   - Location: Palm Springs, CA, USA
   - Remote preference: Remote only
   - Timezone: Pacific Time (PT)
   - Available hours: 20-40 hrs/week
   - Rate: $75/hour (negotiable)

5. Complete professional profile:

   **Headline** (50 chars max):
   "AI/ML Engineer | RAG Systems | Multi-Agent Orchestration"

   **Professional Summary** (read from file):
   /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/braintrust-summary.md

   **Skills** (select/add):
   PRIMARY (Expert level):
   - Python
   - FastAPI
   - Machine Learning
   - Natural Language Processing (NLP)
   - RAG (Retrieval-Augmented Generation)
   - Multi-Agent Systems
   - Claude API / Anthropic
   - OpenAI API / GPT-4
   - PostgreSQL
   - Redis

   SECONDARY (Advanced level):
   - Docker
   - CI/CD (GitHub Actions)
   - Testing (pytest, TDD)
   - Streamlit
   - SQLAlchemy
   - Pydantic
   - LangChain
   - Vector Databases (ChromaDB, FAISS)

   **Years of Experience**: 20+ years software, 3+ years AI/ML

6. Add work experience:

   **Title**: Senior AI/ML Engineer (Freelance)
   **Company**: ChunkyTortoise Dev
   **Duration**: Jan 2022 - Present
   **Description**:
   - Built production RAG systems processing 1M+ documents
   - Reduced LLM costs by 89% via intelligent caching
   - Architected multi-agent orchestration (4.3M dispatches/sec)
   - Integrated Claude, GPT-4, Gemini APIs for enterprise clients
   - Delivered AI chatbots for real estate, legal, healthcare verticals

   **Title**: Software Engineer (Various)
   **Company**: 20+ years in tech industry
   **Duration**: 2000 - 2022
   **Description**: Full-stack development, system architecture, team leadership

7. Add education:
   (If user has degree, add here - otherwise skip or mark "Self-taught")
   **Degree**: Self-Taught / Bootcamp / Online Certifications
   **Focus**: Computer Science, Machine Learning, AI

8. Add portfolio items:

   **Project 1**: AgentForge Multi-LLM Orchestrator
   - Description: Production framework for Claude/GPT-4 orchestration
   - Tech: Python, FastAPI, Redis, PostgreSQL
   - Link: https://github.com/ChunkyTortoise/ai-orchestrator
   - Demo: https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/
   - Impact: 89% cost reduction, 4.3M dispatches/sec

   **Project 2**: DocQA RAG Engine
   - Description: Hybrid BM25/semantic search for document QA
   - Tech: FAISS, ChromaDB, scikit-learn, FastAPI
   - Link: https://github.com/ChunkyTortoise/docqa-engine
   - Impact: Processes 1M+ documents, <200ms response time

   **Project 3**: Real Estate AI Platform (EnterpriseHub)
   - Description: Multi-agent chatbot system for lead qualification
   - Tech: Claude API, PostgreSQL, Streamlit, GoHighLevel CRM
   - Link: https://github.com/ChunkyTortoise/EnterpriseHub
   - Impact: Automated lead scoring, 8,500+ test suite

9. Connect accounts:
   - GitHub: github.com/ChunkyTortoise
   - LinkedIn: linkedin.com/in/caymanroden
   - Portfolio: chunkytortoise.github.io

10. Set job preferences:
    - Remote only: YES
    - Contract type: Contract, Part-Time, Full-Time (all)
    - Industries: AI/ML, SaaS, FinTech, HealthTech, PropTech
    - Company size: All sizes
    - Min rate: $75/hour
    - Willing to relocate: NO

11. Complete profile verification:
    - Upload ID if required (skip for now, note for user)
    - Verify email
    - Complete skill assessments if available (optional, can skip)

12. Set notification preferences:
    - Email: New job matches (daily digest)
    - Email: Client messages (immediate)
    - BTRST token rewards: ON

13. Submit profile for review (if required)

14. Save profile status and URL to: /Users/cave/Documents/GitHub/EnterpriseHub/content/platform-setup/braintrust-complete.txt

SUCCESS CRITERIA:
✅ Braintrust account created
✅ Profile 90%+ complete
✅ 3 portfolio projects added
✅ GitHub + LinkedIn connected
✅ Job preferences configured
✅ Email verified
✅ Profile submitted for review (if applicable)

IMPORTANT NOTES:
- Braintrust may require profile review (1-3 days)
- Some features require BTRST tokens (can skip initially)
- If crypto wallet setup is optional, skip for now
- Take screenshots of completed profile and portfolio section
- If ID verification required, note for user
```

---

## Summary Content File

**Create**: `content/platform-setup/braintrust-summary.md`

```markdown
# Braintrust Professional Summary

Senior AI/ML Engineer with 20+ years of software development experience, specializing in production-ready AI systems. I build RAG engines, multi-agent orchestration frameworks, and LLM-powered applications that reduce costs and improve performance.

## Core Expertise
- **RAG Systems**: Hybrid BM25/semantic search, vector databases, document processing
- **Multi-Agent AI**: Claude/GPT-4 orchestration, agent mesh coordination, handoff logic
- **Backend Engineering**: FastAPI (async), PostgreSQL, Redis caching, SQLAlchemy
- **Testing & Quality**: TDD, 80%+ coverage, 8,500+ automated tests across projects
- **AI Cost Optimization**: 89% LLM cost reduction via intelligent caching strategies

## Recent Projects
- **AgentForge**: Multi-LLM orchestration framework (4.3M dispatches/sec, <200ms overhead)
- **DocQA Engine**: RAG system for enterprise document QA (1M+ documents indexed)
- **EnterpriseHub**: Real estate AI platform with multi-bot conversation orchestration

## What I Deliver
- Clean, tested, production-ready code (not prototypes)
- Complete solutions: code + tests + docs + deployment
- Performance metrics: P50/P95/P99 latency, cost analysis, benchmarks
- Fast iteration: async communication, daily commits, over-documented

## Industries
Real estate AI, legal document processing, healthcare chatbots, enterprise integrations (CRM, Stripe, HubSpot, Salesforce).

## Remote Work
100% remote since 2020. Comfortable with async communication, GitHub-first workflows, and US/EU/APAC timezone collaboration.
```

---

## Expected Output

**File**: `content/platform-setup/braintrust-complete.txt`

```
Braintrust Network Setup - COMPLETE
Date: 2026-02-15
Profile URL: https://usebraintrust.com/talent/caymanroden (or similar)
Status: Pending Review (or Active)

✅ Account created and verified
✅ Profile 95% complete
✅ Rate set: $75/hour
✅ 3 portfolio projects added:
   - AgentForge Multi-LLM Orchestrator
   - DocQA RAG Engine
   - EnterpriseHub AI Platform
✅ GitHub connected: github.com/ChunkyTortoise
✅ LinkedIn connected: linkedin.com/in/caymanroden
✅ Job preferences: Remote only, AI/ML focused
✅ Skills added: 18 technical skills (Python, FastAPI, RAG, etc.)

Profile Review Status:
- Submitted for review: Yes
- Expected approval: 1-3 business days
- Review criteria: Technical depth, portfolio quality, experience

Screenshots saved:
- braintrust-profile.png
- braintrust-portfolio.png
- braintrust-skills.png

Next Steps:
- If ID verification required: Upload government ID
- If crypto wallet setup available: Connect MetaMask (optional)
- Check email for job matches (daily digest)
- Respond to client inquiries within 24hrs
- Earn BTRST tokens for completed projects
```

---

## Braintrust Unique Features

**BTRST Token Rewards**:
- Earn tokens for completing projects
- Higher rating = more tokens
- Tokens = governance rights in network
- Can convert to USD or hold for network benefits

**Vetting Process**:
- Not everyone is approved
- Focus on senior talent (5+ years experience)
- Portfolio and GitHub review
- Response time matters (< 24hr preferred)

**Client Quality**:
- Fortune 500 companies (Porsche, Nike, NASA)
- Web3 startups with funding
- Remote-first culture
- Long-term contracts (3-12 months typical)

---

## Revenue Impact

**First Contract** (expected timeline):
- Profile approval: 1-3 days
- First match: 1-4 weeks
- Contract start: 2-6 weeks from signup

**Typical Engagement**:
- Rate: $75-125/hour (your rate is negotiable)
- Hours: 20-40/week
- Duration: 3-6 months average
- Monthly: $6K-20K (depending on hours)

**Long-Term Potential**:
- Build reputation: Higher rates ($100-150/hr)
- BTRST token value appreciation
- Repeat clients and referrals
- Annual potential: $100K-200K (full-time equivalent)
