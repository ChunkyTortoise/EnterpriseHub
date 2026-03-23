# Portfolio Monetization Spec

**Status**: Active | **Created**: 2026-02-08 | **Owner**: Cayman Roden
**Constraint**: $0 budget. All channels must be free to list/join.

---

## Table of Contents

1. [Asset Inventory](#1-asset-inventory)
2. [Channel Strategy](#2-channel-strategy)
3. [Gumroad Products (4 listings)](#3-gumroad-products)
4. [Fiverr Gigs (3 listings)](#4-fiverr-gigs)
5. [Cold Outreach Campaign](#5-cold-outreach-campaign)
6. [Content Marketing (Free Distribution)](#6-content-marketing)
7. [Portfolio Site Fixes](#7-portfolio-site-fixes)
8. [Pending Deployments](#8-pending-deployments)
9. [Execution Timeline](#9-execution-timeline)
10. [Revenue Projections](#10-revenue-projections)

---

## 1. Asset Inventory

### Production-Ready Assets (Sellable Today)

| # | Repo | Tests | Live Demo | REST API | Docker | CLI | License |
|---|------|-------|-----------|----------|--------|-----|---------|
| 1 | EnterpriseHub | 4,937 | ct-enterprise-ai.streamlit.app | FastAPI | Yes (3 compose files) | No | MIT |
| 2 | docqa-engine | 322 | ct-document-engine.streamlit.app | FastAPI (auth, rate limit, metering) | No | No | MIT |
| 3 | insight-engine | 313 | ct-insight-engine.streamlit.app | No | No | No | MIT |
| 4 | scrape-and-serve | 236 | ct-scrape-and-serve.streamlit.app | No | No | No | MIT |
| 5 | mcp-toolkit | 158 | ct-mcp-toolkit.streamlit.app | No | No | `mcp-toolkit` CLI | MIT |
| 6 | ai-orchestrator | 214 | PENDING | FastAPI | No | `agentforge` CLI | MIT |
| 7 | jorge_real_estate_bots | 279 | — | 3 FastAPI services | Docker | No | MIT |
| 8 | Revenue-Sprint | 240 | — | No | Docker | CLI | MIT |
| 9 | prompt-engineering-lab | 127 | PENDING | No | No | `pel` CLI | MIT |
| 10 | llm-integration-starter | 149 | PENDING | No | No | CLI | MIT |
| 11 | multi-agent-starter-kit | — | — | No | No | No | MIT |

**Total**: 11 repos, 7,016+ tests, 5 live demos, all MIT licensed.

### Key Differentiators (vs. typical GitHub repos)
- Every repo has CI (GitHub Actions, green)
- Every repo has comprehensive tests (not hello-world)
- 5 repos have **live, clickable demos** — prospects can try before buying
- Production patterns: rate limiting, caching, auth, error handling
- Docker-ready deployment for the ones that need it
- DEMO_MODE in key apps — works without API keys or databases

---

## 2. Channel Strategy

### Priority Order (speed to first dollar)

| Priority | Channel | Cost | Time to Revenue | Revenue Type |
|----------|---------|------|-----------------|--------------|
| **P0** | Gumroad | Free (10% cut) | 1-3 days after listing | Per-sale ($29-99) |
| **P0** | Fiverr | Free to join | 3-7 days after approval | Per-gig ($50-500) |
| **P1** | Cold email | Free | 1-2 weeks | Project ($500-5K) |
| **P1** | Reddit/HN posts | Free | 1-3 days (traffic spike) | Leads → Gumroad/services |
| **P2** | GitHub Sponsors | Free | 2-4 weeks | Recurring ($5-50/mo) |
| **P2** | Dev.to articles | Free | 1-2 weeks (SEO) | Leads |
| **P3** | Product Hunt | Free | Launch day spike | Visibility → all channels |
| **P3** | Twitter/X threads | Free | Ongoing | Brand awareness |

### Channel Dependencies
```
Gumroad listings ──→ Reddit/HN posts (need product links)
                 ──→ Cold emails (need proof links)
                 ──→ Dev.to articles (need product links)
Fiverr gigs ───────→ Independent (no dependencies)
Portfolio fixes ───→ Cold emails (need updated site)
```

**Critical path**: Gumroad listings first. Everything else references them.

---

## 3. Gumroad Products

### Product 1: AI Document Q&A Engine — $49

**Repo**: docqa-engine
**Tagline**: "Upload documents, ask questions, get cited answers. Production-ready RAG pipeline in pure Python."

**Gumroad Description**:
```
What You Get:
- Complete RAG pipeline: upload → chunk → embed → retrieve → answer → cite
- Hybrid retrieval (BM25 + dense cosine + Reciprocal Rank Fusion)
- 5 chunking strategies (fixed, sentence, semantic, paragraph, custom)
- Prompt engineering lab with A/B testing
- Citation accuracy scoring (faithfulness, coverage, redundancy)
- REST API with auth, rate limiting, and metering (FastAPI)
- Streamlit UI with 4 tabs
- 322 passing tests, GitHub Actions CI
- Works without API keys (TF-IDF embeddings, no OpenAI required)

Tech Stack: Python 3.11+, Streamlit, FastAPI, scikit-learn, PyPDF2

Formats: PDF, DOCX, TXT, MD, CSV

Live Demo: https://ct-document-engine.streamlit.app

Who This Is For:
- Developers adding document Q&A to their product
- Consultants building RAG solutions for clients
- Teams evaluating retrieval strategies before committing to a vector DB
- Anyone tired of LangChain's 50+ dependency overhead

What Makes This Different:
- Zero external API dependencies for core retrieval (no OpenAI, no Pinecone)
- Production patterns: rate limiting, auth, metering, cost tracking
- Evaluation built in: MRR, NDCG@K, Precision@K, Recall@K
- Not a toy — 322 tests, CI pipeline, structured error handling
```

**Thumbnail text**: "Document Q&A Engine | RAG Pipeline | 322 Tests | Live Demo"
**Tags**: RAG, document-qa, python, fastapi, streamlit, nlp, ai

---

### Product 2: AgentForge — Multi-LLM Orchestrator — $39

**Repo**: ai-orchestrator
**Tagline**: "One interface for Claude, GPT, Gemini, and Perplexity. Swap providers with one parameter change."

**Gumroad Description**:
```
What You Get:
- Unified async interface for 4 LLM providers (Claude, Gemini, OpenAI, Perplexity)
- 2 core dependencies (~15 KB) vs. LangChain (50+ deps, ~50 MB)
- Token-aware rate limiting with token bucket algorithm
- Exponential backoff with jitter and configurable retry
- Prompt templates with {{variable}} substitution
- Function calling abstraction across providers
- Structured JSON output extraction with schema validation
- Per-request cost tracking with provider breakdown
- Streaming support
- Click CLI tool
- Streamlit visualization dashboard
- 214 passing tests, GitHub Actions CI
- Mock provider for testing without API keys

Tech Stack: Python 3.11+, httpx (async), Click, Streamlit, FastAPI

Who This Is For:
- Teams building LLM-powered products who don't want vendor lock-in
- Developers who need multi-provider fallback chains
- Anyone who finds LangChain too heavy for what they need
- Consultants who switch between Claude/GPT/Gemini per client

What Makes This Different:
- 15 KB vs. 50 MB — this is httpx + dotenv, not a framework
- Mock provider included — run all tests without spending on API keys
- Cost tracking per request — know exactly what each call costs
- Function calling works the same across Claude, GPT, and Gemini
```

**Thumbnail text**: "AgentForge | 4 LLM Providers | 214 Tests | 15KB Core"
**Tags**: llm, ai, claude, openai, gemini, python, multi-provider, orchestrator

---

### Product 3: Web Scraper & Price Monitor Toolkit — $29

**Repo**: scrape-and-serve
**Tagline**: "YAML-configurable scrapers, price monitoring, SEO scoring, and Excel-to-web-app converter."

**Gumroad Description**:
```
What You Get:
- YAML-configurable web scrapers with CSS selectors
- SHA-256 change detection for competitor price monitoring
- Historical price tracking with alert thresholds
- SEO content scoring (0-100) across 5 dimensions
- Keyword density and readability analysis
- Excel (.xlsx/.csv/.tsv) to SQLite + auto-generated Streamlit CRUD app
- Async job scheduler with status tracking
- Data validation engine (type, range, regex, custom)
- Streamlit dashboard with Plotly charts
- 236 passing tests, GitHub Actions CI

Tech Stack: Python 3.11+, BeautifulSoup4, httpx (async), Pandas, Streamlit, Plotly

Live Demo: https://ct-scrape-and-serve.streamlit.app

Who This Is For:
- E-commerce teams monitoring competitor pricing
- SEO professionals scoring content quality
- Agencies building scraping solutions for clients
- Anyone with Excel files who wants a web app instead

What Makes This Different:
- YAML config, not code — non-developers can define scrapers
- Price history with charts, not just current prices
- SEO scoring built in — competitors charge $50/mo for this alone
- Excel-to-app converter is a standalone product inside this product
```

**Thumbnail text**: "Scrape & Serve | Price Monitor | SEO Scorer | 236 Tests"
**Tags**: web-scraping, price-monitoring, seo, python, streamlit, automation

---

### Product 4: Data Intelligence Dashboard — $39

**Repo**: insight-engine
**Tagline**: "Upload CSV/Excel, get instant dashboards, predictions, clustering, and attribution — no code."

**Gumroad Description**:
```
What You Get:
- Auto-profiler: detects column types, distributions, outliers, correlations
- 4 marketing attribution models (first-touch, last-touch, linear, time-decay)
- Predictive modeling: auto-detect classification/regression + SHAP explanations
- K-means & DBSCAN clustering with silhouette scoring
- Time series forecasting (moving average, exponential smoothing, ensemble)
- Anomaly detection (Z-score + IQR)
- Data cleaning: dedup (exact + fuzzy), standardization, smart imputation
- Feature engineering lab: scaling, encoding, polynomials, interactions
- Dashboard generator with Plotly auto-layout
- Markdown/PDF report generation
- 313 passing tests, GitHub Actions CI

Tech Stack: Python 3.11+, Streamlit, Plotly, scikit-learn, XGBoost, SHAP, Pandas

Live Demo: https://ct-insight-engine.streamlit.app

Who This Is For:
- Marketing teams who need attribution without hiring a data scientist
- Analysts who want instant dashboards from any CSV
- Consultants delivering insights to clients on tight timelines
- Small businesses who can't afford Tableau/Looker licenses

What Makes This Different:
- Upload → dashboard in 30 seconds, not 30 hours
- SHAP explanations included — not just predictions, but WHY
- Attribution models — most dashboard tools don't do this
- PDF report export — deliver to stakeholders immediately
```

**Thumbnail text**: "Insight Engine | Auto-Dashboard | ML Predictions | 313 Tests"
**Tags**: dashboard, analytics, machine-learning, python, streamlit, data-science

---

### Gumroad Setup Checklist

```
[ ] Create Gumroad account (free)
[ ] Set up Stripe/PayPal for payouts
[ ] Create 4 product listings with descriptions above
[ ] Upload ZIP of each repo (clean, with README)
[ ] Set pricing: $49, $39, $29, $39
[ ] Add thumbnail images (can use Streamlit demo screenshots)
[ ] Add live demo links in description
[ ] Enable "pay what you want" with minimum price (captures higher willingness)
[ ] Create a profile page with portfolio link
[ ] Set up discount code "LAUNCH" for 20% off (drives urgency)
```

---

## 4. Fiverr Gigs

### Gig 1: "I will build a RAG document Q&A system" — $100-500

**Category**: Programming & Tech > AI Services > AI Applications
**Tags**: rag, document-qa, chatbot, python, fastapi, ai

**Title**: I will build a RAG document Q&A system with cited answers

**Description**:
```
I'll build a production-ready document Q&A system that lets your users
upload documents and ask questions with source citations.

What I deliver:
✓ Document ingestion pipeline (PDF, DOCX, TXT, CSV)
✓ Hybrid retrieval (BM25 + semantic search)
✓ Cited answers with confidence scores
✓ Streamlit UI or REST API (your choice)
✓ Deployed and tested with your documents

My proof: docqa-engine — 322 tests, live demo at
ct-document-engine.streamlit.app

Packages:
- Basic ($100): RAG pipeline with your docs, Streamlit UI, deployed
- Standard ($250): + REST API, auth, rate limiting, custom prompt tuning
- Premium ($500): + multi-format support, evaluation metrics, production Docker

Timeline: 3-7 days depending on package.

Tech: Python, FastAPI, Streamlit, scikit-learn (no expensive vector DB required)
```

**FAQ**:
- "Do I need an OpenAI API key?" → No, core retrieval uses TF-IDF. Optional LLM for answer generation.
- "Can this work with my existing app?" → Yes, the REST API integrates with any stack.
- "How many documents can it handle?" → Tested with 1000+ documents. Scales with your hardware.

---

### Gig 2: "I will create an AI chatbot with multi-agent handoff" — $200-500

**Category**: Programming & Tech > AI Services > AI Chatbots
**Tags**: chatbot, ai-agent, multi-agent, python, fastapi, crm

**Title**: I will build an AI chatbot with intelligent agent handoff

**Description**:
```
I'll build a multi-agent chatbot system where specialized bots handle
different conversation types and hand off to each other seamlessly.

What I deliver:
✓ Custom AI chatbot with your knowledge base
✓ Multi-agent routing based on intent detection
✓ Confidence-based handoff between agents
✓ Conversation history and analytics
✓ CRM integration (optional)

My proof: EnterpriseHub — 4,937 tests, 3 specialized bots with
real-time handoff. Live demo at ct-enterprise-ai.streamlit.app

Packages:
- Basic ($200): Single chatbot, custom knowledge base, Streamlit UI
- Standard ($350): + multi-agent handoff, intent detection, analytics
- Premium ($500): + CRM integration, Docker deployment, monitoring

Timeline: 5-10 days depending on package.

Tech: Python, FastAPI, Claude/GPT (your choice), Streamlit, PostgreSQL
```

---

### Gig 3: "I will build a data dashboard from your CSV/Excel" — $50-200

**Category**: Programming & Tech > Data Science > Data Visualization
**Tags**: dashboard, streamlit, data-visualization, analytics, python

**Title**: I will turn your CSV or Excel data into an interactive dashboard

**Description**:
```
Upload your data, get a deployed interactive dashboard with charts,
filters, and export — in 3-5 days.

What I deliver:
✓ Interactive Streamlit dashboard with Plotly charts
✓ Auto-profiling of your data (types, distributions, outliers)
✓ Filters, search, and drill-down
✓ PDF/CSV export
✓ Deployed on Streamlit Cloud (free hosting)

My proof: insight-engine — 313 tests, auto-detects the best charts
for your data. Live demo at ct-insight-engine.streamlit.app

Packages:
- Basic ($50): Dashboard with 3-5 charts, filters, deployed
- Standard ($100): + predictive modeling, clustering, PDF reports
- Premium ($200): + marketing attribution, anomaly detection, custom branding

Timeline: 2-5 days depending on package.

Tech: Python, Streamlit, Plotly, Pandas, scikit-learn
```

---

### Fiverr Setup Checklist

```
[ ] Create Fiverr seller account (free)
[ ] Complete profile (photo, bio, skills, portfolio links)
[ ] Create 3 gig listings with descriptions above
[ ] Take screenshots of live demos for gig gallery (3-5 per gig)
[ ] Set up gig packages (Basic/Standard/Premium)
[ ] Add FAQ to each gig
[ ] Set delivery times (3-10 days)
[ ] Add portfolio links to profile
```

---

## 5. Cold Outreach Campaign

### Target Segments

| Segment | Pain Point | Our Solution | Proof Asset |
|---------|-----------|--------------|-------------|
| AI startups (pre-Series A) | Need RAG/agent features fast | docqa-engine, AgentForge | Live demos + test counts |
| Real estate tech companies | Lead qualification at scale | EnterpriseHub, Jorge Bots | Full platform demo |
| Marketing agencies | Dashboard/reporting for clients | insight-engine | Live demo + PDF export |
| E-commerce companies | Competitor price monitoring | scrape-and-serve | Live demo |
| Consulting firms | AI integration for their clients | Full portfolio | 11 repos, 7K tests |

### Email Template 1: AI Startup CTO

```
Subject: RAG pipeline with 322 tests — open source, ready to fork

Hi [Name],

I saw [Company] is building [product with AI/doc features]. I built an
open-source RAG engine that might save your team 2-3 weeks:

→ Live demo: https://ct-document-engine.streamlit.app
→ 322 tests, CI green, hybrid retrieval (BM25 + dense), REST API with auth

It's MIT licensed — fork it free, or I can customize it for your stack
in 1-2 weeks.

I also built a multi-LLM orchestrator (Claude/GPT/Gemini) with 214 tests
if you're dealing with provider switching.

Portfolio: https://chunkytortoise.github.io/projects.html
(11 repos, 7,000+ tests, all CI green)

Happy to do a 15-min walkthrough if useful.

Best,
Cayman Roden
```

### Email Template 2: Agency / Consulting

```
Subject: Instant dashboards for your clients — live demo inside

Hi [Name],

I built a tool that turns any CSV/Excel into an interactive dashboard
with predictions and PDF reports in 30 seconds:

→ Try it: https://ct-insight-engine.streamlit.app

If your team spends time building one-off dashboards for clients, this
could be your base template. It includes attribution models, clustering,
anomaly detection — things clients usually pay extra for.

I can white-label and customize it for your agency in 3-5 days ($800-2K).
Or you can fork the MIT-licensed repo and build on it yourself.

Portfolio: https://chunkytortoise.github.io/services.html

Best,
Cayman Roden
```

### Email Template 3: E-commerce / Price Monitoring

```
Subject: Competitor price monitoring with change alerts — free demo

Hi [Name],

I noticed [Company] operates in a competitive market. I built a price
monitoring toolkit that tracks competitor prices, detects changes (SHA-256),
and alerts you when prices shift:

→ Live demo: https://ct-scrape-and-serve.streamlit.app

It also includes SEO content scoring and historical price charts.
236 tests, production-ready.

I can set it up for your specific competitors in 3-5 days ($150-500).

Best,
Cayman Roden
```

### Outreach Execution Plan

```
Phase 1 (Days 1-3): Find 30 targets
  - 10 AI startups from YC batch pages (free, public)
  - 10 agencies from Clutch.co free listings
  - 10 e-commerce companies from LinkedIn search

Phase 2 (Days 3-5): Send 10 emails/day
  - Personalize first line per company
  - Include relevant demo link
  - Track opens with free tool (Mailtrack for Gmail)

Phase 3 (Week 2): Follow up non-responders
  - Single follow-up 5 days after initial email
  - Add value (e.g., "I added X feature since my last email")
```

---

## 6. Content Marketing (Free Distribution)

### Reddit Posts (r/Python, r/MachineLearning, r/SideProject, r/webdev)

**Post 1 — r/Python + r/SideProject**:
```
Title: I built 11 Python repos with 7,000+ tests and live demos — here's what I learned

Body:
Over the past few months I built a portfolio of AI/data tools, all open source:

- Document Q&A engine (RAG) — 322 tests, live demo
- Multi-LLM orchestrator (Claude/GPT/Gemini) — 214 tests, 15KB core
- Data intelligence dashboard — 313 tests, upload CSV → instant charts
- Web scraper with price monitoring — 236 tests, YAML config
- MCP toolkit (6 servers, 32 tools) — 158 tests
- ... and 6 more

Every repo has CI, MIT license, and works without API keys (demo modes).

Live demos: [link to projects page]
GitHub: [link]

Lessons learned:
1. TDD saves time, not costs time — caught 3 major bugs pre-deploy
2. Demo mode is essential — recruiters/clients won't set up your env
3. Small dependencies > frameworks — AgentForge is 15KB vs LangChain's 50MB
4. Live demos close deals — 2 client conversations started from Streamlit links

Happy to answer questions about any of the repos.
```

**Post 2 — r/MachineLearning**:
```
Title: Open-source RAG pipeline with hybrid retrieval — no vector DB, no OpenAI required

Body:
Built a document Q&A engine that uses BM25 + TF-IDF dense retrieval with
Reciprocal Rank Fusion. No external API needed for the core retrieval.

Key features:
- 5 chunking strategies
- Citation scoring (faithfulness, coverage)
- Evaluation metrics (MRR, NDCG@K, Precision@K)
- REST API with auth and rate limiting
- 322 tests

Live demo: https://ct-document-engine.streamlit.app
Repo: [link]

The big insight: for many use cases, TF-IDF + BM25 with good chunking
beats vector embeddings. Especially when your corpus is <10K docs and
you need explainability.

[details about architecture]
```

### Hacker News (Show HN)

```
Title: Show HN: AgentForge — Multi-LLM orchestrator in 15KB (Claude, GPT, Gemini, Perplexity)

URL: [GitHub repo link]

Text:
I got tired of LangChain's 50+ dependency overhead for simple LLM calls.
AgentForge is a unified async interface for 4 providers in 2 dependencies
(httpx + dotenv).

- Swap providers with one parameter change
- Function calling works the same across Claude, GPT, and Gemini
- Token-aware rate limiting, retry with jitter
- Cost tracking per request
- Mock provider for testing without API keys
- 214 tests, CI green

The core idea: if you're just making LLM calls with retries and cost
tracking, you don't need a framework. You need a thin client.
```

### Dev.to Articles (3 planned)

| # | Title | Target Keywords | Links To |
|---|-------|-----------------|----------|
| 1 | "Building a RAG Pipeline Without a Vector Database" | rag, bm25, python, document-qa | docqa-engine Gumroad + demo |
| 2 | "Why I Replaced LangChain with 15KB of httpx" | langchain alternative, llm, python | AgentForge Gumroad + demo |
| 3 | "From CSV to Dashboard in 30 Seconds with Python" | streamlit, dashboard, data-viz | insight-engine Gumroad + demo |

---

## 7. Portfolio Site Fixes

### Updates Needed

| File | Change | Priority |
|------|--------|----------|
| `projects.html` | Update test counts (EnterpriseHub: 3,577→4,937, docqa: 236→322, etc.) | P0 |
| `projects.html` | Update total from "5,300+" to "7,000+" | P0 |
| `services.html` | Update "8 public repos" to "11 public repos" in CTA | P1 |
| `services.html` | Add Gumroad links to each service as "Get the starter kit" | P1 |
| `services.html` | Add Fiverr link alongside Upwork in footer/CTA | P1 |
| `index.html` | Update hero stats if they reference old numbers | P1 |
| NEW section | Add "Starter Kits" section linking to Gumroad products | P2 |

### New Section for services.html (after Quick Wins)

```html
<!-- Starter Kits -->
<div class="mb-12">
    <div class="flex items-center gap-3 mb-6">
        <h2 class="text-xl font-bold">Starter Kits</h2>
        <span class="bg-purple-100 text-purple-700 text-xs px-3 py-1 rounded-full font-medium">One-Time Purchase</span>
    </div>
    <p class="text-gray-600 text-sm mb-6">Production-ready codebases you can fork, customize, and deploy. Every kit includes tests, CI, documentation, and a live demo.</p>
    <div class="grid md:grid-cols-2 gap-6">
        <div class="bg-white rounded-xl border p-6">
            <h3 class="font-bold mb-1">AI Document Q&A Engine</h3>
            <p class="text-sm text-purple-600 font-medium mb-2">$49</p>
            <p class="text-gray-600 text-sm mb-3">RAG pipeline with hybrid retrieval, REST API, citation scoring. 322 tests.</p>
            <a href="[GUMROAD_LINK]" class="inline-block bg-purple-600 text-white text-xs px-4 py-1.5 rounded hover:bg-purple-700 transition">Get Starter Kit</a>
        </div>
        <!-- ... 3 more products ... -->
    </div>
</div>
```

---

## 8. Pending Deployments

### 3 Streamlit Apps to Deploy

| App | Repo | Entry Point | Streamlit Cloud URL |
|-----|------|-------------|---------------------|
| AgentForge | ai-orchestrator | `app.py` | ct-agentforge.streamlit.app |
| Prompt Lab | prompt-engineering-lab | `app.py` | ct-prompt-lab.streamlit.app |
| LLM Starter | llm-integration-starter | `app.py` | ct-llm-starter.streamlit.app |

**Deployment steps** (per app):
1. Go to share.streamlit.io
2. Connect GitHub repo
3. Set main file path to `app.py`
4. Set Python version to 3.11
5. Add any env vars (most have DEMO_MODE=true)
6. Deploy

**Time**: ~15 min total for all 3.

---

## 9. Execution Timeline

### Day 1 (Today)
```
Morning:
[ ] Create Gumroad account
[ ] Create 4 product listings (copy is ready above)
[ ] Take screenshots of live demos for thumbnails
[ ] Set up "LAUNCH" discount code (20% off)

Afternoon:
[ ] Create Fiverr seller account
[ ] Complete Fiverr profile (use portfolio site content)
[ ] Create 3 gig listings (copy is ready above)
[ ] Take demo screenshots for Fiverr gallery
```

### Day 2
```
[ ] Deploy 3 pending Streamlit apps (15 min)
[ ] Update portfolio site test counts + stats (15 min)
[ ] Add Gumroad links to portfolio site (30 min)
[ ] Add Fiverr link to portfolio site footer (5 min)
[ ] Git push portfolio site updates
```

### Day 3
```
[ ] Find 30 cold outreach targets (YC, Clutch, LinkedIn)
[ ] Send first 10 cold emails (use templates above)
[ ] Post on r/Python or r/SideProject (use post template above)
```

### Day 4-5
```
[ ] Send 10 more cold emails per day
[ ] Post "Show HN" for AgentForge
[ ] Write first Dev.to article ("RAG Without a Vector Database")
[ ] Monitor Gumroad/Fiverr for first orders
```

### Week 2
```
[ ] Follow up on cold emails (non-responders)
[ ] Second Reddit post (r/MachineLearning)
[ ] Second Dev.to article
[ ] Set up GitHub Sponsors
[ ] Optimize Fiverr gigs based on impressions data
[ ] Kialash Persad call (Tue Feb 10, 4 PM EST)
```

---

## 10. Revenue Projections (Conservative)

### Month 1

| Channel | Units/Gigs | Avg Price | Revenue |
|---------|-----------|-----------|---------|
| Gumroad | 5-10 sales | $39 avg | $195-390 |
| Fiverr | 2-4 gigs | $150 avg | $300-600 |
| Cold email | 1 project | $1,000 | $1,000 |
| **Total** | | | **$1,495-1,990** |

### Month 2 (with SEO + content compounding)

| Channel | Units/Gigs | Avg Price | Revenue |
|---------|-----------|-----------|---------|
| Gumroad | 10-20 sales | $39 avg | $390-780 |
| Fiverr | 4-8 gigs | $200 avg | $800-1,600 |
| Cold email | 2 projects | $1,500 avg | $3,000 |
| GitHub Sponsors | 5-10 sponsors | $10 avg | $50-100 |
| **Total** | | | **$4,240-5,480** |

### Existing Pipeline (Could Close Any Day)
- **FloPro Jamaica**: Awaiting contract offer at $75/hr
- **Kialash Persad**: Call Tuesday, potential full-time/contract

---

## Appendix A: GitHub Sponsors Tiers

```
$5/mo  — Supporter: Name in README sponsors section
$15/mo — Builder: Priority GitHub issue responses (24h)
$50/mo — Enterprise: 30-min monthly call, priority feature requests
```

## Appendix B: Product Hunt Launch Plan

**Product**: AgentForge (most likely to get traction on PH)
**Tagline**: "Multi-LLM orchestrator in 15KB — swap Claude, GPT, Gemini with one line"
**Timing**: Tuesday or Wednesday (best PH days)
**Assets needed**: Logo, 3-5 screenshots, 60-second demo GIF
**Hunter**: Self-launch (or find a hunter with followers)

## Appendix C: Gumroad Product ZIP Contents

Each ZIP should include:
```
product-name/
├── README.md           (setup instructions)
├── LICENSE              (MIT)
├── pyproject.toml       (or requirements.txt)
├── app.py               (Streamlit entry point)
├── src/                 (or module directory)
├── tests/               (full test suite)
├── .github/workflows/   (CI config)
├── DEMO_MODE.md         (how to run without API keys)
└── CUSTOMIZATION.md     (guide to adapting for your use case)
```

Add `CUSTOMIZATION.md` to each repo before packaging. This is the value-add
over just cloning the public GitHub repo — a guided walkthrough of how to
adapt it for the buyer's specific use case.

---

*End of spec. Execute in order: Gumroad → Fiverr → Cold outreach → Content.*
