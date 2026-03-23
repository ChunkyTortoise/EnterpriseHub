# Upwork Profile V2: Ready-to-Paste Copy

All copy below is ready to paste directly into your Upwork profile settings.

---

## 1. HOURLY RATE

**Set to:** `$85.00/hr`

Why $85: It's the sweet spot — high enough to signal quality, low enough to not scare off mid-market clients. Once you have 3-5 reviews, raise to $100. Your specialized profiles can be priced differently (see #9).

---

## 2. PROFILE TITLE (max 70 characters)

**Option A (recommended — 68 chars):**
```
AI Application Developer | LLM Agents, RAG & Analytics Dashboards
```

**Option B (if you want to emphasize Python — 65 chars):**
```
Python AI Engineer | Multi-Agent Systems, RAG & Data Dashboards
```

**Option C (if targeting more enterprise clients — 69 chars):**
```
Full-Stack AI Developer | Claude/GPT Integration, RAG & Dashboards
```

---

## 3. PROFILE OVERVIEW / BIO

Paste this entire block. The first two lines are what clients see before clicking "more" — they're optimized for search results.

```
I build production AI applications — multi-agent systems, RAG document Q&A, and analytics dashboards — with Python, FastAPI, and Streamlit. 7 public GitHub repos, 700+ automated tests, CI/CD on every project.

Portfolio: chunkytortoise.github.io

WHAT I BUILD:

AI Agent Systems
Multi-bot architectures with handoff logic, context management, and CRM integration. My EnterpriseHub platform runs 3 qualification bots across 82+ API routes with L1/L2/L3 caching and <200ms response overhead.

RAG & Document Q&A
Upload PDFs or DOCX files, ask questions, get cited answers. Hybrid retrieval (BM25 + dense vectors), prompt engineering lab with A/B testing, and cost tracking built in.

Data Analytics Dashboards
CSV/Excel upload to instant interactive dashboards. Auto-profiling, predictive modeling (XGBoost + SHAP explanations), marketing attribution, and PDF report generation.

LLM Integrations
Provider-agnostic LLM orchestration — Claude, GPT, Gemini, Perplexity through a single async interface. Fallback routing, retry logic, response caching, and benchmark tooling.

Web Scraping & Automation
YAML-configurable scrapers with change detection, competitor price monitoring, Excel-to-web app conversion, and SEO content scoring.

HOW I WORK:

Every project ships with automated tests, documentation, CI/CD, and a working demo mode. Your team can maintain it without me. All code is production-grade — not "works on my machine."

TECH STACK:
Python 3.11+ | FastAPI | Streamlit | PostgreSQL | Redis | Claude API | GPT API | Gemini | Docker | GitHub Actions | Plotly | pandas | scikit-learn | XGBoost | SQLAlchemy | Pydantic

CERTIFICATIONS:
19 completed/in-progress certifications (1,768+ hours) from Google, IBM, Microsoft, DeepLearning.AI, Vanderbilt, and Duke — covering AI/ML, data analytics, business intelligence, and generative AI.

Available for new projects. Response time: under 2 hours during Pacific business hours.
```

---

## 4. REMOVE "TRANSITION NOTE"

Delete this line from your current bio entirely:
> "TRANSITION NOTE: Enterprise developer → freelance. I bring corporate quality standards without corporate timelines."

Do not replace it with anything. Your work speaks for itself.

---

## 5. PORTFOLIO ITEMS (Add 4 more — you currently have 1)

For each item, add the screenshot/image, title, and description in Upwork's portfolio section. Take screenshots of each repo's README or demo output.

### Portfolio Item 1: EnterpriseHub (already exists — update description)

**Title:** `EnterpriseHub — AI-Powered Real Estate Platform`

**Description:**
```
Full-stack real estate AI platform with 3 qualification bots (Lead, Buyer, Seller), Streamlit BI dashboard, and multi-LLM orchestration.

Key features:
- Claude AI orchestration with L1/L2/L3 Redis caching (<200ms overhead)
- 82+ FastAPI routes with Pydantic validation and JWT auth
- GoHighLevel CRM integration with real-time sync
- 140+ dashboard components (Monte Carlo sim, sentiment analysis, churn detection)
- Cross-bot handoff with 0.7 confidence threshold

Stack: Python, FastAPI, Streamlit, PostgreSQL, Redis, Claude API, Docker
Tests: 313 automated | CI/CD: GitHub Actions
```

**Link:** `https://github.com/ChunkyTortoise/EnterpriseHub`


### Portfolio Item 2: docqa-engine (NEW — add this)

**Title:** `docqa-engine — RAG Document Q&A with Prompt Lab`

**Description:**
```
RAG-based document question-answering system. Upload PDFs or Word docs, ask questions in natural language, get cited answers with source references.

Key features:
- Hybrid retrieval: BM25 + dense vector search for high-accuracy results
- Prompt engineering lab with A/B testing and evaluation scoring
- Multi-LLM support via provider-agnostic interface (Claude, GPT, Gemini)
- Cost tracking per query with token usage breakdown
- Zero-API-key demo mode — runs fully offline with mock LLM

Stack: Python, FastAPI, scikit-learn, NumPy, PyPDF2, python-docx, Streamlit
Tests: 94 automated | CI/CD: GitHub Actions (Python 3.11/3.12)
Demo: make demo (5 built-in demo documents)
```

**Link:** `https://github.com/ChunkyTortoise/docqa-engine`


### Portfolio Item 3: insight-engine (NEW — add this)

**Title:** `insight-engine — Data Analytics & Dashboard Platform`

**Description:**
```
Upload any CSV or Excel file and get instant interactive dashboards, predictive models, and PDF reports. Designed for non-technical users who need analytics without writing code.

Key features:
- Auto-profiling: data types, distributions, missing values, correlations in 2 minutes
- Predictive modeling with XGBoost + SHAP feature explanations
- Marketing attribution (First Touch, Last Touch, Linear, Time Decay, U-Shaped)
- Dashboard generation with Plotly (4-panel layouts, heatmaps, time series)
- 3 built-in demo datasets: e-commerce, marketing, HR attrition

Stack: Python, Streamlit, Pandas, Plotly, scikit-learn, XGBoost, SHAP
Tests: 63 automated | CI/CD: GitHub Actions (Python 3.11/3.12)
Demo: make demo
```

**Link:** `https://github.com/ChunkyTortoise/insight-engine`


### Portfolio Item 4: AgentForge / ai-orchestrator (NEW — add this)

**Title:** `AgentForge — Async LLM Orchestration Library`

**Description:**
```
Pip-installable Python library for working with multiple LLM providers through a single async interface. Swap providers without changing application code.

Key features:
- Unified interface for Claude, GPT, Gemini, OpenAI, and Perplexity
- Automatic provider fallback when primary provider fails
- Built-in retry logic with exponential backoff
- CLI tool: agentforge "prompt" --provider claude
- Benchmark command: compare response quality/speed across providers
- Full async/await support for high-concurrency applications

Stack: Python, asyncio, httpx, click (CLI)
Tests: 27 automated (22 pass, 5 skip without API keys)
CI/CD: GitHub Actions
Install: pip install agentforge
```

**Link:** `https://github.com/ChunkyTortoise/ai-orchestrator`


### Portfolio Item 5: scrape-and-serve (NEW — add this)

**Title:** `scrape-and-serve — Web Scraping & Excel-to-Web Tools`

**Description:**
```
Web scraping framework with YAML configuration, plus tools to convert Excel spreadsheets into interactive web applications.

Key features:
- YAML-configurable scraper: define targets, selectors, and schedules in config files
- Change detection: get alerts when monitored pages update
- Price monitor: track competitor pricing with historical charts and CSV export
- Excel-to-web converter: upload .xlsx, get a Streamlit CRUD app with SQLite backend
- SEO content tools: outline generation and quality scoring (0-100 scale)

Stack: Python, BeautifulSoup, httpx, Pandas, SQLite, Streamlit
Tests: 62 automated | CI/CD: GitHub Actions (Python 3.11/3.12)
Demo: make demo (sample products.csv, inventory.xlsx, scrape_config.yaml)
```

**Link:** `https://github.com/ChunkyTortoise/scrape-and-serve`

---

## 6. CERTIFICATIONS TO ADD

Add these in your Upwork profile's "Certifications" section. Include the provider and completion year. For "In Progress" ones, only add the completed ones to Upwork — listing incomplete certs undermines credibility.

**Add these completed certifications:**

| Certification Name | Issuing Organization | Year |
|---|---|---|
| Deep Learning Specialization | DeepLearning.AI (Coursera) | 2025 |
| IBM Generative AI Engineering Professional Certificate | IBM (Coursera) | 2025 |
| Generative AI for Strategic Leaders | Vanderbilt University (Coursera) | 2025 |
| LLMOps: Building Real-World Applications | Duke University (Coursera) | 2025 |
| Google Data Analytics Professional Certificate | Google (Coursera) | 2025 |
| IBM Business Intelligence Analyst Professional Certificate | IBM (Coursera) | 2025 |
| Generative AI for Data Analysis | Microsoft (Coursera) | 2025 |
| Python for Everybody Specialization | University of Michigan (Coursera) | 2025 |

**Do NOT add** the "In Progress" ones until they're completed. Showing incomplete work signals you're still learning, not that you're an expert.

---

## 7. SKILLS LIST

Remove your current skills and replace with this curated list. Order matters — Upwork shows the first ones most prominently.

**Set these skills (in this order):**

1. Python
2. FastAPI
3. LLM Integration
4. RAG
5. Streamlit
6. Prompt Engineering
7. Data Visualization
8. Machine Learning
9. API Development
10. Web Scraping
11. PostgreSQL
12. Data Analysis

**Why these:** Each one matches high-value, high-volume Upwork search terms. Generic skills like "Artificial Intelligence" and "Business Intelligence" get lost in noise. Specific skills like "FastAPI", "RAG", and "Prompt Engineering" match the exact queries clients use when posting $5K+ jobs.

---

## 8. FULL BIO (already included in #3 above)

The bio in section 3 IS the full restructured bio. Copy that entire block.

Key structural changes from your current bio:
- First 2 lines focus on WHAT you do + PROOF (700+ tests, 7 repos)
- Portfolio link immediately visible
- Sections use headers for scannability
- Each section leads with the client problem, not the technology
- "TRANSITION NOTE" removed entirely
- "AVAILABILITY" changed to evergreen wording (no "this month")
- Tech stack condensed to one line
- Certifications mentioned as a credibility signal

---

## 9. SPECIALIZED PROFILES

Create these two specialized profiles in Upwork Settings > Profile Settings > Specialized Profiles.

### Specialized Profile #1: AI/LLM Engineering

**Title:**
```
LLM & RAG Engineer | Claude/GPT Agents, Document Q&A & Prompt Optimization
```

**Rate:** `$100.00/hr`

**Overview:**
```
I build production LLM applications — multi-agent systems, RAG pipelines, and prompt-optimized AI workflows. 4 public repos focused on AI, 400+ automated tests.

WHAT I BUILD:

Multi-Agent Systems — Bots that coordinate, hand off context, and integrate with CRMs. My EnterpriseHub platform runs 3 AI agents with cross-bot handoff at 0.7 confidence threshold.

RAG Document Q&A — Upload documents, ask questions, get cited answers. My docqa-engine uses hybrid retrieval (BM25 + dense vectors) with a built-in prompt engineering lab for A/B testing.

LLM Orchestration — Provider-agnostic interface for Claude, GPT, Gemini, and Perplexity. Automatic fallback, retry logic, response caching, and cost tracking. Published as a pip-installable library (AgentForge).

Prompt Engineering — A/B testing frameworks, temperature tuning, evaluation scoring, and token cost optimization. Every prompt decision backed by data, not guesswork.

Every project includes automated tests, documentation, and CI/CD. Code runs in production, not just in notebooks.

Stack: Python | FastAPI | Claude API | GPT API | Gemini | LangChain | sentence-transformers | ChromaDB | asyncio
```

**Skills for this profile:**
1. LLM Integration
2. RAG
3. Prompt Engineering
4. Python
5. Claude API
6. FastAPI
7. Natural Language Processing
8. API Development


### Specialized Profile #2: Data Analytics & Dashboards

**Title:**
```
Data Analytics Engineer | Interactive Dashboards, Predictive Models & BI Reports
```

**Rate:** `$75.00/hr`

**Overview:**
```
I build data analytics tools that turn raw CSV/Excel data into interactive dashboards, predictive models, and executive reports. No manual analysis — upload your data and get insights in minutes.

WHAT I BUILD:

Analytics Dashboards — Plotly-powered interactive charts with filters, drill-downs, and 4-panel layouts. Designed for executives who need answers, not spreadsheets.

Predictive Modeling — XGBoost and scikit-learn models with SHAP feature explanations. Know not just WHAT will happen, but WHY.

Marketing Attribution — First Touch, Last Touch, Linear, Time Decay, and U-Shaped attribution models. See which channels actually drive revenue.

Auto-Profiling — Upload any dataset and get instant analysis: data types, distributions, missing values, correlations, outliers. 2 minutes vs. 2 hours of manual EDA.

PDF Reports — Export any dashboard or analysis as a formatted PDF for stakeholders who don't use web tools.

My insight-engine platform handles the full pipeline: upload, clean, analyze, model, visualize, export. 63 automated tests, 3 demo datasets included.

Stack: Python | Streamlit | Plotly | Pandas | scikit-learn | XGBoost | SHAP | PostgreSQL | SQLAlchemy
```

**Skills for this profile:**
1. Data Visualization
2. Streamlit
3. Data Analysis
4. Python
5. Machine Learning
6. Plotly
7. Business Intelligence
8. PostgreSQL

---

## 10. PROFILE VIDEO SCRIPT (60-90 seconds)

Record this with your webcam or screen + voiceover. Keep it natural — don't read word-for-word. Hit these beats:

```
[0-10 sec — Introduction]
"Hi, I'm Cayman. I'm a Python developer who builds AI-powered applications — things like multi-agent systems, document Q&A tools, and data analytics dashboards."

[10-30 sec — What you build, with screen share]
(Switch to screen recording showing EnterpriseHub or insight-engine running)
"Here's an example — this is a platform I built that takes raw data and generates interactive dashboards, predictive models, and reports automatically. The whole thing runs on FastAPI and Streamlit with a PostgreSQL backend."

[30-50 sec — Why you're different]
"What makes my work different from a typical freelancer is that everything I build comes with automated tests, CI/CD pipelines, and documentation. I have 7 public repos on GitHub with over 700 tests between them. You can run any of them with 'make demo' and see exactly how they work before we even talk."

[50-65 sec — Credibility]
"I also have certifications from Google, IBM, Microsoft, and DeepLearning.AI — about 1,700 hours of structured training in AI, machine learning, and data analytics."

[65-80 sec — Call to action]
"If you need an AI application built, a dashboard created, or an LLM integrated into your product — send me a message. I respond within 2 hours and I'm happy to do a quick call to scope your project."

[80-90 sec — Close]
"Thanks for watching. I look forward to working with you."
```

**Recording tips:**
- Good lighting, clean background
- Look at the camera, not the screen
- Screen share portion should show your BEST-LOOKING project running (insight-engine dashboards are probably most visual)
- Keep it under 90 seconds — clients skip long videos

---

## 11. FIRST REVIEWS STRATEGY

### Approach A: Quick-Win Fixed-Price Proposals

Apply to 15-20 jobs per week in your first month using these templates. Target jobs in the $200-$800 range to get fast completions and reviews.

**Template 1: CSV/Data Dashboard Job**

```
Hi [Client Name],

I built a data analytics platform (insight-engine) that does exactly what you're describing — takes CSV/Excel data and generates interactive dashboards with Plotly.

You can see it running here: https://github.com/ChunkyTortoise/insight-engine

For your project, I'd:
1. Ingest your data files and auto-profile the structure
2. Build the specific charts/KPIs you need
3. Deploy as a Streamlit app you can share with your team
4. Include export-to-PDF for stakeholders

I can have a working prototype within [2-3 days]. Happy to do a quick call to confirm the scope.

Cayman
```

**Template 2: LLM/AI Integration Job**

```
Hi [Client Name],

I've built several LLM integrations — including a provider-agnostic library (AgentForge) that supports Claude, GPT, Gemini, and Perplexity through a single interface.

Relevant repo: https://github.com/ChunkyTortoise/ai-orchestrator

For your project, I'd:
1. Set up the LLM integration with proper error handling and retry logic
2. Add response caching to reduce API costs
3. Include fallback routing if the primary provider goes down
4. Write tests so your team can maintain it confidently

I've done this exact pattern multiple times. Happy to walk you through my approach on a quick call.

Cayman
```

**Template 3: Web Scraping Job**

```
Hi [Client Name],

I built a scraping framework (scrape-and-serve) with YAML-configurable selectors, change detection, and automated alerts.

Repo: https://github.com/ChunkyTortoise/scrape-and-serve

For your project, I'd:
1. Configure the scraper for your target site(s)
2. Set up scheduling and change detection
3. Output to your preferred format (CSV, database, API)
4. Handle anti-bot measures and rate limiting

I can usually deliver a working scraper within [2-4 days] for straightforward sites. Want to discuss the specifics?

Cayman
```

**Template 4: General Python/FastAPI Job**

```
Hi [Client Name],

This is a great fit for my stack. I build production Python applications with FastAPI, PostgreSQL, and Redis — my largest project (EnterpriseHub) has 82+ API routes with full test coverage.

Repo: https://github.com/ChunkyTortoise/EnterpriseHub

For your project, I'd:
1. [Specific step addressing their requirement #1]
2. [Specific step addressing their requirement #2]
3. [Specific step addressing their requirement #3]
4. Automated tests + documentation included

Available to start immediately. Happy to discuss on a call.

Cayman
```

### Approach B: Get Initial Reviews Fast

These tactics work specifically for breaking the "zero reviews" barrier:

1. **Upwork Project Catalog** — Create 2-3 fixed-price "products" in Upwork's catalog:
   - "CSV-to-Interactive-Dashboard" at $500
   - "Connect Your App to Claude/GPT API" at $300
   - "Web Scraper Setup (YAML Config)" at $600
   Catalog items get organic traffic without you applying to jobs.

2. **Boosted Proposals** — For your first 10 applications, use Upwork's "Boost" feature (costs extra Connects). The ROI of a first review is enormous.

3. **Lower your rate temporarily for the FIRST 2-3 jobs only** — Consider $50-65/hr for your first 3 contracts to win them. After getting 3 five-star reviews, raise to $85/hr. The reviews are worth more than the hourly difference.

4. **Respond fast** — Upwork tracks response time. Being in the top 10% of responders dramatically improves your visibility in client searches.

5. **"Rising Talent" badge** — Complete your profile 100% (photo, video, skills, portfolio, certifications, availability). Upwork awards "Rising Talent" to strong new profiles, which is a huge trust signal.

---

## IMPLEMENTATION CHECKLIST

Do these in order:

- [ ] Update rate to $85/hr
- [ ] Change title to Option A
- [ ] Replace entire bio with the new copy from section 3
- [ ] Add 4 new portfolio items (sections 5.2-5.5)
- [ ] Update portfolio item 1 description (section 5.1)
- [ ] Add 8 completed certifications (section 6)
- [ ] Replace skills list with the new 12 skills (section 7)
- [ ] Create Specialized Profile #1: AI/LLM (section 9)
- [ ] Create Specialized Profile #2: Data Analytics (section 9)
- [ ] Record and upload profile video (section 10)
- [ ] Create 2-3 Project Catalog items (section 11)
- [ ] Apply to 15+ jobs this week using templates (section 11)
- [ ] Enable "Boosted Proposals" for first 10 applications

---

## WHAT NOT TO DO

- Don't mention being "new to freelancing" or "transitioning" anywhere
- Don't list "In Progress" certifications — only completed ones
- Don't use buzzwords like "Cinematic UI", "Institutional-Grade", or "Technical Co-Founder"
- Don't price below $65/hr on your main profile (undermines everything else)
- Don't write proposals longer than 150 words (clients skim)
- Don't apply to jobs that are clearly below your skill level ($10-15/hr jobs)
- Don't copy-paste the same proposal to every job — customize the first 2 lines
