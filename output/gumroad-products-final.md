# Gumroad Product Pages -- Final Copy

**Author**: Cayman Roden | **GitHub**: [ChunkyTortoise](https://github.com/ChunkyTortoise)
**Last Updated**: 2026-02-09

---

# Product 1: AI Document Q&A Engine

## Headline

**Stop Paying $200/Month for RAG. Build Production Document Q&A in Hours.**

## Subheadline

A complete, self-hosted retrieval-augmented generation pipeline with hybrid search, citation scoring, and a production REST API -- no external APIs, no recurring fees.

## The Problem

Every RAG tutorial gets you 80% of the way there, then you spend weeks building authentication, evaluation metrics, and production infrastructure. Meanwhile, hosted solutions like Pinecone + LangChain cost $200-500/month and lock you into their ecosystem. You need a production-ready RAG system you own completely -- one that works offline, handles real document workloads, and gives you confidence scores on every answer.

## The Solution

The DocQA Engine is a fully self-hosted RAG pipeline that combines BM25 keyword precision with dense vector similarity for retrieval accuracy that neither approach achieves alone. It ships with a FastAPI REST API (JWT auth, rate limiting, usage metering), a Streamlit demo UI, and built-in evaluation metrics so you can measure and improve retrieval quality from day one. Upload documents, ask questions, get cited answers -- deployed in hours, not months.

## Key Features

- **Hybrid Retrieval System** -- Combines BM25 keyword matching with dense vector similarity for 40% better precision than keyword-only search
- **5 Chunking Strategies** -- Fixed-size, sentence-based, paragraph, recursive, and semantic chunking to match any document type
- **Citation Scoring** -- Every answer includes source citations with confidence scores so users can verify claims
- **Production REST API** -- FastAPI endpoints with JWT authentication, 100 req/min rate limiting, and usage metering built in
- **Streamlit Demo UI** -- Ready-to-use interface for testing documents and queries immediately after install
- **Built-in Evaluation Metrics** -- Precision, recall, and F1 scoring for continuous retrieval quality improvement
- **Zero External Dependencies** -- Core retrieval runs entirely offline. No OpenAI, no Pinecone, no recurring SaaS bills
- **Configurable Pipeline** -- YAML-based configuration for all retrieval parameters. Swap components without changing code

## Technical Specs

| Spec | Detail |
|------|--------|
| **Language** | Python 3.11+ |
| **API Framework** | FastAPI |
| **UI Framework** | Streamlit |
| **Vector Store** | ChromaDB (included), optional Qdrant/Weaviate |
| **ML/NLP** | scikit-learn, PyPDF2, sentence-transformers |
| **Auth** | PyJWT |
| **Config** | YAML |
| **Docker** | Dockerfile + docker-compose.yml included |
| **Tests** | 322 automated tests |
| **CI Status** | All passing |

## Who Is This For?

- **Startup CTOs** building AI-powered documentation or knowledge base products who need a production foundation, not another tutorial
- **Enterprise engineers** migrating off legacy search systems who need hybrid retrieval with evaluation metrics to prove ROI
- **Solo developers** creating domain-specific Q&A tools (legal, medical, technical) who want full control over their data pipeline
- **AI consultants** who need a white-label RAG solution they can deploy for multiple clients under MIT license

## What's Included

```
docqa-engine/
  src/            -- Core pipeline, retrieval, chunking, evaluation, API routes
  ui/             -- Streamlit demo app with upload, query, and evaluation pages
  config/         -- YAML configuration for pipeline and chunking strategies
  tests/          -- 322 automated tests
  Dockerfile      -- Container deployment
  docker-compose.yml
  README.md       -- Getting started guide
  CUSTOMIZATION.md -- Deep customization guide
  API_REFERENCE.md -- REST API documentation
  DEPLOYMENT.md   -- Production deployment guide
  ARCHITECTURE.md -- System architecture overview
```

**License**: MIT -- use in unlimited commercial projects
**Updates**: 90 days of free updates included
**Support**: Email support at caymanroden@gmail.com

## Pricing

**$49** -- one-time purchase. No subscriptions, no per-query fees, no usage limits.

**Launch Special**: First 10 buyers get 20% off -- just **$39**.

Compare: Pinecone + LangChain = $200-500/month. This pays for itself on day one.

## Social Proof

- 322 automated tests with full CI pipeline passing
- Extracted from a production system processing 1,000+ pages in under 2 seconds
- Part of a portfolio with 11 repos and 7,016+ total tests -- all CI green
- Live demo available at [ct-document-engine.streamlit.app](https://ct-document-engine.streamlit.app)
- Built by an engineer running production AI systems in real estate, not weekend tutorials repackaged

## Call to Action

**Get the DocQA Engine now for $49** and stop paying monthly rent on your RAG infrastructure. Full source code, 322 tests, Docker-ready, 30-day money-back guarantee. You will be running production document Q&A before lunch.

---
---

# Product 2: AgentForge -- Multi-LLM Orchestrator

## Headline

**One API for Claude, Gemini, OpenAI, and Perplexity. 15KB. Not 50MB.**

## Subheadline

A lightweight, production-grade orchestrator that unifies four LLM providers under a single async Python interface with built-in cost tracking, rate limiting, and structured outputs.

## The Problem

Every LLM provider has a different API signature, different rate limits, different response formats, and different error handling. Building a multi-provider application means maintaining four separate integration layers, each with its own retry logic, cost tracking, and response parsing. LangChain solves this but brings 50MB+ of dependencies and abstractions you do not need. You want provider flexibility without the complexity tax.

## The Solution

AgentForge normalizes Claude, Gemini, OpenAI, and Perplexity behind a single method call. One interface, consistent response structures, automatic rate limiting, and per-request cost tracking -- all in a 15KB core. Switch providers with a config change, compare models side by side, and stay under budget with granular cost monitoring. The built-in mock provider means you can develop and test without burning a single API dollar.

## Key Features

- **Unified Async Interface** -- Single API for Claude, Gemini, OpenAI, and Perplexity with consistent response formats
- **Token-Aware Rate Limiting** -- Automatic throttling based on each provider's specific token and request limits
- **Exponential Backoff** -- Intelligent retry with configurable backoff for rate limits and transient errors
- **Function Calling** -- Native support for tool/function calling across all providers in one consistent pattern
- **Structured JSON Output** -- Guaranteed JSON responses with Pydantic validation. No more parsing surprises
- **Per-Request Cost Tracking** -- Cumulative cost monitoring with configurable budget limits and alerts
- **Streaming Support** -- Full streaming response handling for real-time chat applications
- **Mock Provider** -- Built-in mock LLM for development and testing without spending on API calls

## Technical Specs

| Spec | Detail |
|------|--------|
| **Language** | Python 3.11+ |
| **HTTP Client** | httpx (async/sync) |
| **API Framework** | FastAPI (optional REST wrapper) |
| **UI Framework** | Streamlit (demo app) |
| **CLI** | Click |
| **Validation** | Pydantic |
| **Config** | YAML / environment variables |
| **Docker** | Dockerfile + docker-compose.yml included |
| **Tests** | 214 automated tests |
| **Core Size** | ~15KB (vs. LangChain's 50MB+) |

## Who Is This For?

- **AI application developers** building products that need provider flexibility -- switch from OpenAI to Claude without rewriting integration code
- **Startup teams** comparing model performance and costs across providers before committing to one
- **Backend engineers** who need a lightweight LLM gateway without the dependency bloat of LangChain
- **Freelancers and consultants** delivering AI projects to clients who may have different provider preferences

## What's Included

```
ai-orchestrator/
  src/            -- Core orchestrator, 5 provider implementations, features (rate limiter, retry, cost tracker, function calling, structured output)
  cli/            -- Click CLI tool for quick testing
  ui/             -- Streamlit demo with chat, model comparison, and cost dashboard
  examples/       -- 4 ready-to-run examples (basic chat, function calling, cost tracking, streaming)
  config/         -- Provider configuration
  tests/          -- 214 automated tests
  Dockerfile + docker-compose.yml
  README.md
  CUSTOMIZATION.md -- Provider customization guide
  API_REFERENCE.md -- Complete API documentation
  COST_GUIDE.md   -- Cost optimization strategies
  ARCHITECTURE.md -- System design overview
```

**License**: MIT -- use in unlimited commercial projects
**Updates**: 90 days of free updates included
**Support**: Email support at caymanroden@gmail.com

## Pricing

**$39** -- one-time purchase. Use with as many providers and projects as you want.

**Launch Special**: First 10 buyers get 20% off -- just **$31**.

Compare: Commercial LLM gateways cost $50-200/month. AgentForge is a one-time investment.

## Social Proof

- 214 automated tests with full CI pipeline passing
- 15KB core -- 3,000x smaller than LangChain
- Part of a portfolio with 11 repos and 7,016+ total tests -- all CI green
- Built by an engineer running multi-LLM workflows in production (Claude + Gemini + Perplexity)
- Quickstart code that works in under 10 lines

## Call to Action

**Get AgentForge now for $39** and unify your LLM integrations in a single afternoon. Full source code, 214 tests, mock provider for free development, 30-day money-back guarantee. Ship multi-provider AI applications without the dependency headache.

---
---

# Product 3: Scrape-and-Serve -- Web Scraper & Price Monitor Toolkit

## Headline

**Define Scrapers in YAML. Track Prices Automatically. No Code Required.**

## Subheadline

A complete web scraping toolkit with SHA-256 change detection, historical price tracking, SEO scoring, and async scheduling -- configure everything in YAML, deploy with Docker.

## The Problem

Every new scraping project starts the same way: write a BeautifulSoup script, handle pagination, build change detection, set up scheduling, and create a dashboard to view results. That is two weeks of boilerplate before you scrape a single page. Commercial tools like Octoparse ($75-249/month) and ParseHub ($149-499/month) solve this but drain your budget month after month. You need production scraping infrastructure you can reuse across every project, configured in minutes, not coded in weeks.

## The Solution

Scrape-and-Serve lets you define scrapers entirely in YAML -- selectors, pagination, scheduling, and extraction logic -- then handles everything else automatically. SHA-256 change detection alerts you only when content actually changes (not cosmetic updates). Historical price tracking stores every data point with Plotly-powered charts. The built-in SEO scoring engine rates pages 0-100 across eight optimization factors. Deploy once, configure new scrapers in minutes.

## Key Features

- **YAML-Configurable Scrapers** -- Define selectors, pagination, and extraction logic without writing code
- **SHA-256 Change Detection** -- Intelligent content hashing that ignores cosmetic changes and alerts on real updates
- **Historical Price Tracking** -- Full price history with automatic Plotly chart generation and trend analysis
- **SEO Scoring Engine** -- 0-100 score covering meta tags, content length, headings, links, images, and load speed
- **Async Job Scheduler** -- Cron-like scheduling for background scraping with configurable intervals
- **Excel-to-Web-App Converter** -- Transform static spreadsheets into interactive Streamlit dashboards instantly
- **Data Validation** -- Pydantic schema enforcement with detailed error reporting on every scrape
- **Production Ready** -- Rate limiting, proxy rotation support, and structured error handling built in

## Technical Specs

| Spec | Detail |
|------|--------|
| **Language** | Python 3.11+ |
| **HTML Parsing** | BeautifulSoup4 |
| **HTTP Client** | httpx (async/sync) |
| **Data Processing** | Pandas |
| **Visualization** | Plotly, Streamlit |
| **Scheduling** | APScheduler |
| **Validation** | Pydantic |
| **Docker** | Dockerfile + docker-compose.yml included |
| **Tests** | 236 automated tests |
| **CI Status** | All passing |

## Who Is This For?

- **E-commerce sellers** monitoring competitor pricing across Amazon, Shopify, and marketplace listings
- **Affiliate marketers** tracking product availability and price drops to trigger promotional campaigns
- **SEO professionals** who need automated page scoring across client websites without paying for enterprise tools
- **Data engineers** building ingestion pipelines from web sources who want reusable, YAML-driven scraper templates

## What's Included

```
scrape-and-serve/
  src/            -- Core scraper engine, extractors (product, article, custom), change detectors, SEO scorer, price/content trackers, validators
  cli/            -- CLI tool for scraper management
  ui/             -- Streamlit dashboard with scraper management, price tracking, SEO analysis, and scheduler pages
  templates/      -- Excel-to-dashboard template, scraper YAML template
  examples/       -- 3 ready-to-use YAML configs (Amazon product, e-commerce price, SEO analysis)
  config/         -- Global settings + scraper definitions
  tests/          -- 236 automated tests
  Dockerfile + docker-compose.yml
  README.md
  CUSTOMIZATION.md -- Advanced customization guide
  API_REFERENCE.md -- Programmatic API documentation
  SEO_GUIDE.md    -- SEO scoring methodology
  ARCHITECTURE.md -- System architecture overview
```

**License**: MIT -- use in unlimited commercial projects
**Updates**: 90 days of free updates included
**Support**: Email support at caymanroden@gmail.com

## Pricing

**$29** -- one-time purchase. Scrape as many sites as you want, forever.

**Launch Special**: First 10 buyers get 20% off -- just **$23**.

Compare: Octoparse = $75-249/month. ParseHub = $149-499/month. This toolkit pays for itself in the first hour.

## Social Proof

- 236 automated tests with full CI pipeline passing
- Live demo available at [ct-scrape-and-serve.streamlit.app](https://ct-scrape-and-serve.streamlit.app)
- Part of a portfolio with 11 repos and 7,016+ total tests -- all CI green
- SEO scoring engine validated against 8 weighted factors used by professional SEO auditing tools
- YAML-first approach means non-developers on your team can configure scrapers too

## Call to Action

**Get Scrape-and-Serve now for $29** and never write scraper boilerplate again. YAML configs, price tracking, SEO scoring, 236 tests, Docker-ready, 30-day money-back guarantee. Your first scraper will be running in under 5 minutes.

---
---

# Product 4: Insight Engine -- Data Intelligence Dashboard

## Headline

**Upload a CSV. Get Dashboards, Predictions, and PDF Reports in 30 Seconds.**

## Subheadline

A self-hosted business intelligence toolkit that automatically profiles your data, runs ML models with explainable predictions, and generates stakeholder-ready PDF reports -- no data science degree required.

## The Problem

Your team has data in spreadsheets but getting insights requires a data scientist, a BI tool subscription, and weeks of dashboard building. Tableau costs $70/user/month. Power BI locks you into Microsoft's ecosystem. Even open-source options like Metabase take days to configure. You need something that goes from raw CSV to actionable insights in minutes, not months -- and you need the ML models to explain themselves so stakeholders trust the results.

## The Solution

The Insight Engine takes a CSV or Excel upload and automatically generates a data profile, runs four marketing attribution models, builds predictive models with SHAP explanations, performs clustering analysis, detects anomalies, and creates time series forecasts -- all in under 30 seconds. Every analysis exports to a professional PDF report. The interactive Streamlit dashboard lets non-technical users filter, drill down, and explore without touching code.

## Key Features

- **30-Second Analysis Pipeline** -- Upload data, get profiling + visualizations + predictions automatically
- **Auto Data Profiler** -- Quality assessment, distribution analysis, correlation mapping, and anomaly flagging
- **4 Marketing Attribution Models** -- First-touch, last-touch, linear, and time-decay attribution in one click
- **Predictive Modeling with SHAP** -- Classification and regression models with explainable feature importance
- **Clustering Analysis** -- K-means and hierarchical clustering for automatic customer segmentation
- **Time Series Forecasting** -- ARIMA-based forecasting with confidence intervals for trend prediction
- **Anomaly Detection** -- Statistical and ML-based outlier detection across all numeric columns
- **Professional PDF Reports** -- Auto-generated reports with executive summary, methodology, and recommendations

## Technical Specs

| Spec | Detail |
|------|--------|
| **Language** | Python 3.11+ |
| **UI Framework** | Streamlit |
| **Visualization** | Plotly |
| **ML** | scikit-learn, XGBoost |
| **Explainability** | SHAP |
| **Data Processing** | Pandas, NumPy |
| **Statistical Analysis** | SciPy, Statsmodels |
| **PDF Generation** | ReportLab, FPDF |
| **Docker** | Dockerfile + docker-compose.yml included |
| **Tests** | 313 automated tests |
| **Supported Formats** | CSV, Excel, JSON, Parquet, SQL |

## Who Is This For?

- **Marketing analysts** who need attribution modeling and campaign performance insights without building custom pipelines
- **Startup founders** validating business hypotheses from raw data who cannot afford a full-time data scientist
- **Business intelligence teams** that need a self-hosted alternative to Tableau/Power BI with ML capabilities built in
- **Data consultants** who deliver client reports and need a white-label analysis engine they can deploy per engagement

## What's Included

```
insight-engine/
  src/            -- Analysis pipeline, auto-profiler, 4 attribution models, predictive modeling with SHAP, clustering, forecasting, anomaly detection, data cleaning, feature engineering, PDF reporting
  ui/             -- Streamlit app with 9 pages (upload, profile, visualize, attribution, predict, cluster, forecast, clean, report)
  config/         -- Dashboard settings
  templates/      -- PDF report template
  tests/          -- 313 automated tests
  Dockerfile + docker-compose.yml
  README.md
  CUSTOMIZATION.md -- Advanced customization guide
  API_REFERENCE.md -- Programmatic API documentation
  ATTRIBUTION_GUIDE.md -- Marketing attribution methodology
  ARCHITECTURE.md -- System architecture overview
```

**License**: MIT -- use in unlimited commercial projects
**Updates**: 90 days of free updates included
**Support**: Email support at caymanroden@gmail.com

## Pricing

**$39** -- one-time purchase. Analyze unlimited datasets, generate unlimited reports.

**Launch Special**: First 10 buyers get 20% off -- just **$31**.

Compare: Tableau = $70/user/month. Power BI = $15-70/user/month. This is a one-time investment with ML included.

## Social Proof

- 313 automated tests with full CI pipeline passing
- Live demo available at [ct-insight-engine.streamlit.app](https://ct-insight-engine.streamlit.app)
- Part of a portfolio with 11 repos and 7,016+ total tests -- all CI green
- SHAP explanations on every prediction so you can show stakeholders exactly why the model made each call
- Supports 5 data formats (CSV, Excel, JSON, Parquet, SQL) out of the box

## Call to Action

**Get the Insight Engine now for $39** and turn your next CSV into a boardroom-ready analysis. Auto-profiling, attribution models, ML predictions with SHAP, PDF reports, 313 tests, Docker-ready, 30-day money-back guarantee. From upload to insight in 30 seconds.

---
---

# Complete AI Toolkit -- Bundle

## Headline

**All 4 Production AI Tools for $120. Save $36.**

## The Best Value in Developer AI Tools

Why buy one when you can own the complete stack? The Complete AI Toolkit bundles all four production-ready tools into a single package at 23% off the individual price.

## What's Included

| Product | Individual Price | What It Does |
|---------|-----------------|-------------|
| **DocQA Engine** | $49 | Self-hosted RAG pipeline with hybrid retrieval, citation scoring, and production REST API |
| **AgentForge** | $39 | Unified async interface for Claude, Gemini, OpenAI, and Perplexity with cost tracking |
| **Scrape-and-Serve** | $29 | YAML-configurable web scraping with price tracking, SEO scoring, and async scheduling |
| **Insight Engine** | $39 | Auto-profiling BI dashboard with ML predictions, attribution models, and PDF reports |

**Individual total: $156**
**Bundle price: $120**
**You save: $36 (23% off)**

## Bundle Stats

- **1,085 automated tests** across all 4 products
- **4 Streamlit demo UIs** -- every product has a working interface out of the box
- **4 Docker configurations** -- deploy any product in minutes
- **4 sets of documentation** -- README, API reference, customization guide, architecture overview
- **MIT license on everything** -- use in unlimited commercial projects
- **90 days of updates** on all products
- **30-day money-back guarantee** -- full refund if any product does not meet your expectations

## How They Work Together

These tools are designed to complement each other:

1. **Scrape-and-Serve** collects data from the web (competitor pricing, market research, content)
2. **DocQA Engine** indexes that data into a searchable Q&A system with cited answers
3. **AgentForge** powers the LLM generation layer, letting you switch between Claude, Gemini, and OpenAI
4. **Insight Engine** analyzes the results -- attribution, forecasting, clustering, anomaly detection

Together, they form a complete data-to-intelligence pipeline: **collect, index, generate, analyze**.

## Who Buys the Bundle?

- **AI startup founders** building multiple products who need a production foundation for each
- **Freelance developers** delivering AI projects to clients who want a reusable toolkit across engagements
- **Engineering teams** standardizing on a tested, documented set of AI components
- **Indie hackers** who want to ship AI-powered features fast without reinventing infrastructure

## Pricing

**$120** -- one-time purchase for all 4 products.

**Launch Special**: First 10 bundle buyers get 20% off -- just **$96**.

That is **$24 per product** -- less than the cost of a single month on most SaaS alternatives.

## Call to Action

**Get the Complete AI Toolkit for $120** and own every tool you need to build production AI applications. 1,085 tests. 4 Docker configs. 4 Streamlit UIs. Full source code. MIT license. 30-day money-back guarantee. This is the best value in developer AI tools on Gumroad.

---

*All products by [Cayman Roden](https://github.com/ChunkyTortoise) -- 11 production repos, 7,016+ tests, all CI green.*
*Questions? Email caymanroden@gmail.com*
