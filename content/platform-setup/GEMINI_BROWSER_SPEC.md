# Gemini Browser Automation Spec
# Platforms: Gumroad, Lemon Squeezy, Contra, Toptal
# Date: 2026-02-17

All content is inline. No other files needed.
Priority order: Gumroad → Lemon Squeezy → Contra → Toptal

---

## PLATFORM 0: GUMROAD (DO THIS FIRST)
**Dashboard**: https://app.gumroad.com/dashboard
**Account**: caymanroden@gmail.com
**ZIPs location**: /Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/

### Context
14 products already exist and are published. The Gumroad API no longer supports
product creation or updates — all changes must be made via the web dashboard.

### Step 1: Update 4 Existing Products (Fix Names/Prices)

Go to https://app.gumroad.com/products and click each product to edit.

#### Update A: "Prompt Engineering Toolkit"
- Current price: $49 → Change to: $29
- Current name: "Prompt Engineering Toolkit" → Change to: "Prompt Engineering Toolkit - Starter"
- Save changes

#### Update B: "AI Integration Starter Kit"
- Current price: $49 → Change to: $39
- Current name: "AI Integration Starter Kit" → Change to: "AI Integration Starter Kit - Starter"
- Save changes

#### Update C: "Data Intelligence Dashboard Pro"
- Current price: $249 → Change to: $199
- Current name: "Data Intelligence Dashboard Pro" → Change to: "Insight Engine - Pro"
- Save changes

#### Update D: "Data Intelligence Dashboard Enterprise"
- Current price: $1499 → Change to: $999
- Current name: "Data Intelligence Dashboard Enterprise" → Change to: "Insight Engine - Enterprise"
- Save changes

### Step 2: Create 7 New Individual Products

Navigate to https://app.gumroad.com/products/new for each product.
For each: set name, price, paste description, upload ZIP, then click "Publish".

---

#### New Product 1: Prompt Engineering Toolkit - Pro
**Price**: $79
**ZIP to upload**: prompt-toolkit-pro-v1.0-20260214.zip
**Description**:
```
Prompt Engineering Toolkit - Pro

Everything in Starter, plus A/B testing, cost optimization, and prompt versioning. Run experiments to find your best-performing prompts, track costs per query, and manage prompt versions across your team.

What You Get (in addition to Starter):
- A/B testing framework for prompt comparison
- Cost calculator with per-model pricing (Claude, GPT-4, GPT-3.5, Gemini)
- Prompt versioning system with rollback
- Prompt safety checker (injection detection)
- Evaluation metrics (relevance, coherence, completeness)
- CLI tool (pel) for terminal workflows
- Extended documentation with advanced patterns

Also Includes Everything in Starter:
- 8 production-ready prompt patterns
- Template manager with variable substitution
- Token counter for cost estimation
- 190 automated tests

Ideal For: Teams optimizing LLM costs, products with user-facing AI features, engineers running prompt experiments.

30-day money-back guarantee. MIT License.
```

---

#### New Product 2: Prompt Engineering Toolkit - Enterprise
**Price**: $199
**ZIP to upload**: prompt-toolkit-enterprise-v1.0-20260214.zip
**Description**:
```
Prompt Engineering Toolkit - Enterprise

Full toolkit with commercial license, priority support, and enterprise features. Everything in Pro plus benchmark runner, report generation, and dedicated email support.

What You Get (in addition to Pro):
- Benchmark runner for systematic prompt evaluation
- Report generator (Markdown/PDF) for stakeholder presentations
- Category-based prompt organization
- Docker deployment files
- CI/CD workflow templates
- Commercial license (unlimited team members)
- 30-day priority email support
- Architecture consultation (30-min call)

Also Includes Everything in Pro:
- A/B testing framework, cost calculator, prompt versioning
- Safety checker, evaluation metrics, CLI tool
- 8 prompt patterns, template manager, 190 automated tests

Ideal For: Enterprise teams with compliance requirements, agencies building AI products for clients, startups shipping LLM-powered features.

30-day money-back guarantee. Commercial license.
```

---

#### New Product 3: AI Integration Starter Kit - Pro
**Price**: $99
**ZIP to upload**: llm-starter-pro-v1.0-20260214.zip
**Description**:
```
AI Integration Starter Kit - Pro

Everything in Starter, plus production hardening: retry with exponential backoff, circuit breaker pattern, response caching, batch processing, and observability. Ship LLM features that don't break at scale.

What You Get (in addition to Starter):
- Retry with exponential backoff and jitter
- Circuit breaker for external API resilience
- Response caching (in-memory and Redis)
- Batch processor for bulk LLM operations
- Guardrails framework (content filtering, rate limiting)
- Latency tracker with P50/P95/P99 percentiles
- Fallback chain (primary to fallback provider)
- CLI tool (llm-starter) for terminal workflows
- Extended documentation with architecture guide

Also Includes Everything in Starter:
- Multi-provider LLM client, streaming, function calling, RAG pipeline
- Cost tracker, token counter, 15 examples, 220 automated tests

Ideal For: Production applications with real users, teams needing reliability guarantees, engineers optimizing LLM costs at scale.

30-day money-back guarantee. MIT License.
```

---

#### New Product 4: AI Integration Starter Kit - Enterprise
**Price**: $249
**ZIP to upload**: llm-starter-enterprise-v1.0-20260214.zip
**Description**:
```
AI Integration Starter Kit - Enterprise

Full starter kit with commercial license, priority support, and enterprise features. Everything in Pro plus multi-provider orchestration, observability pipeline, and dedicated support.

What You Get (in addition to Pro):
- Multi-provider orchestration (route to cheapest/fastest provider)
- Structured observability pipeline (logging, metrics, traces)
- Mock LLM for testing (no API calls needed)
- Docker deployment files + CI/CD workflow templates
- Kubernetes manifests
- Commercial license (unlimited team members)
- 30-day priority email support
- Architecture consultation (30-min call)

Also Includes Everything in Pro:
- Retry, circuit breaker, caching, batch processing, guardrails
- Latency tracker, fallback chain, CLI tool
- Multi-provider client, streaming, function calling, RAG, 220 tests

Ideal For: Enterprise teams with SLA requirements, agencies building AI products, startups preparing for production launch.

30-day money-back guarantee. Commercial license.
```

---

#### New Product 5: Streamlit Dashboard Templates - Starter
**Price**: $49
**ZIP to upload**: dashboard-starter-v1.0-20260214.zip
**Description**:
```
Streamlit Dashboard Templates - Starter

Stop building dashboards from scratch. Get 5 pre-built Streamlit dashboard components with auto-profiling, interactive charts, and data cleaning -- ready to customize for your data in minutes.

What You Get:
- Auto-profiler (column type detection, distributions, outliers, correlations)
- Dashboard generator (Plotly histograms, pie charts, heatmaps, scatter matrices)
- Data cleaner (dedup, standardization, smart imputation)
- Anomaly detector (Z-score, IQR outlier detection)
- Report generator (Markdown reports with findings and metrics)
- 3 demo datasets (e-commerce, marketing, HR)
- Quick-start guide with customization examples

Ideal For: Data analysts building client dashboards, startups needing quick data visualization, students learning Streamlit and Plotly.

Includes:
- Source code (Python 3.11+)
- Streamlit app.py ready to deploy
- Docker files for one-command deployment
- README with customization guide
- 520+ automated tests

30-day money-back guarantee. MIT License.
```

---

#### New Product 6: Streamlit Dashboard Templates - Pro
**Price**: $99
**ZIP to upload**: dashboard-pro-v1.0-20260214.zip
**Description**:
```
Streamlit Dashboard Templates - Pro

Everything in Starter, plus ML predictions, clustering, forecasting, and statistical testing. Turn your CSV into a full analytics platform with SHAP explanations and customer segmentation.

What You Get (in addition to Starter):
- Predictor (auto-detect classification/regression, gradient boosting, SHAP)
- Clustering (K-means, DBSCAN with silhouette scoring)
- Forecaster (moving average, exponential smoothing, ensemble)
- Statistical tests (t-test, chi-square, ANOVA, Mann-Whitney, Shapiro-Wilk)
- Feature lab (scaling, encoding, polynomial features, interaction terms)
- KPI framework (custom metrics, threshold alerting, trend tracking)
- Data quality scoring (completeness, validity, consistency)
- Extended documentation

Also Includes Everything in Starter:
- Auto-profiler, dashboard generator, data cleaner, anomaly detector
- Report generator, 3 demo datasets, 520+ automated tests

Ideal For: Data scientists building ML dashboards, marketing teams tracking campaign performance, product managers monitoring KPIs.

30-day money-back guarantee. MIT License.
```

---

#### New Product 7: Streamlit Dashboard Templates - Enterprise
**Price**: $249
**ZIP to upload**: dashboard-enterprise-v1.0-20260214.zip
**Description**:
```
Streamlit Dashboard Templates - Enterprise

Full analytics suite with attribution models, advanced anomaly detection, hyperparameter tuning, and commercial license. Everything you need for production BI dashboards.

What You Get (in addition to Pro):
- Marketing attribution (first-touch, last-touch, linear, time-decay)
- Advanced anomaly detection (isolation forest, LOF, Mahalanobis, ensemble)
- Model observatory (SHAP explanations, feature importance, model comparison)
- Hyperparameter tuner (automated cross-validation)
- PCA/t-SNE dimensionality reduction
- Database connectors (PostgreSQL, BigQuery)
- Docker + Docker Compose deployment + CI/CD templates
- Commercial license (unlimited team members)
- 30-day priority email support
- Architecture consultation (30-min call)

Also Includes Everything in Pro:
- Predictor, clustering, forecaster, statistical tests
- Feature lab, KPI framework, data quality scoring
- Auto-profiler, dashboard generator, 520+ tests

Ideal For: Enterprise teams building BI platforms, consulting firms delivering client analytics, data teams needing production-grade dashboards.

30-day money-back guarantee. Commercial license.
```

---

### Step 3: Create 3 Bundles

Note: Gumroad bundles are regular products with a discounted price. Create them as normal products.

#### Bundle 1: AI Developer Starter Pack
**Price**: $149
**ZIP to upload**: all-starters-bundle-v1.0-20260215.zip
**Description**:
```
Ship Your First AI Product with the Complete Developer Toolkit

Stop buying tools one at a time. Get all 7 production-ready AI tools in one bundle and save vs buying individually.

Perfect for junior-to-mid developers entering the AI space or building their first LLM-powered product.

What's Inside (7 Products):

1. AgentForge Starter ($49) - Multi-LLM orchestration framework. Claude, GPT-4, Gemini, Perplexity unified API. 550+ tests.
2. DocQA Engine Starter ($59) - Production RAG pipeline. Hybrid retrieval, 5 chunking strategies, citation scoring. 500+ tests.
3. Web Scraper Starter ($49) - YAML-configured web scraping toolkit. SHA-256 change detection, rate limiting. 370+ tests.
4. Insight Engine Starter ($49) - CSV to dashboard in 30 seconds. 20+ interactive charts, attribution models, SHAP explanations. 640+ tests.
5. Prompt Engineering Toolkit Starter ($29) - 8 battle-tested prompt patterns. Template manager, token counter. 190+ tests.
6. AI Integration Starter Kit ($39) - Multi-provider LLM client, streaming, function calling, RAG, cost tracking. 220+ tests.
7. Streamlit Dashboard Templates Starter ($49) - 20+ chart templates. Auto-profiling, ML predictions with SHAP. 520+ tests.

Total Test Coverage: 2,870+ Automated Tests. Production-grade code, not tutorial examples.

Individual Total: $323 | Bundle Price: $149 | You Save: $174 (54%)

Python 3.11+ required. Docker recommended. 30-day money-back guarantee. MIT License.
```

---

#### Bundle 2: Production AI Toolkit (Pro)
**Price**: $549
**ZIP to upload**: all-pro-bundle-v1.0-20260215.zip
**Description**:
```
Production AI Toolkit - Everything You Need to Ship at Scale

For senior developers and small teams deploying AI in production.

This isn't a beginner bundle. You get the Pro tier of all 7 tools plus case studies, architecture consultations, optimization guides, and priority support.

What's Inside (7 Pro-Tier Products):

1. AgentForge Pro ($199) - Framework + 3 case studies ($147K savings proven) + 30-min consult + 9 advanced examples + CI/CD templates + priority support.
2. DocQA Engine Pro ($249) - RAG pipeline + 30-page optimization guide + 3 domain case studies (94% recall) + 30-min consult + priority support.
3. Web Scraper Pro ($149) - Toolkit + 15 production templates + proxy rotation guide + anti-detection strategies + 30-min consult.
4. Insight Engine Pro ($199) - BI dashboards + advanced analytics guide + 3 case studies (92% forecast accuracy) + 5 PDF templates + 30-min consult.
5. Prompt Toolkit Pro ($79) - 8 patterns + A/B testing + cost calculator + prompt versioning + safety checker + CLI tool.
6. AI Integration Pro ($99) - Multi-LLM + circuit breaker + caching + batch processing + monitoring + load testing guide.
7. Streamlit Templates Pro ($99) - 20+ charts + clustering + forecasting + statistical tests + database connectors.

Individual Total: $1,073 | Bundle Price: $549 | You Save: $524 (49%)

30-day money-back guarantee. MIT License.
```

---

#### Bundle 3: Revenue Sprint Bundle
**Price**: $99
**ZIP to upload**: (no single ZIP — skip file upload, description explains what's included)
**Description**:
```
Revenue Sprint Bundle - 3 Quick-Start AI Tools

The fastest path to shipping AI features. Three lightweight tools that work together to help you build, test, and visualize AI applications.

What's Inside:

1. Prompt Engineering Toolkit - Starter ($29) - 8 battle-tested prompt patterns, template manager, token counter. 190 automated tests.
2. AI Integration Starter Kit - Starter ($39) - Multi-provider LLM client (Claude, GPT, Gemini), streaming, function calling, RAG pipeline, cost tracking. 220 automated tests.
3. Streamlit Dashboard Templates - Starter ($49) - Auto-profiling, 20+ interactive charts, data cleaning, anomaly detection, report generation. 520+ automated tests.

Why These 3 Together:
- Prompt Toolkit helps you write and test effective prompts
- Integration Kit helps you connect to LLM providers with retry logic and cost tracking
- Dashboard Templates helps you visualize results and share with stakeholders

Total: 930+ Automated Tests across all 3 tools.

Individual Total: $117 | Bundle Price: $99 | You Save: $18 (15%)

Python 3.11+ required. Docker included. 30-day money-back guarantee. MIT License.
```

---

### Step 4: Verify All Products

Go to https://app.gumroad.com/products and confirm:
- 14 original + 7 new individual + 3 bundles = 24 products total
- All are published (green status)
- Prices match exactly

### Gumroad Report Format
At the end, report:
- Updates completed: [0-4] of 4
- New products created: [0-7] of 7
- Bundles created: [0-3] of 3
- Total published: X of 24
- Any errors

---

---

## PLATFORM 1: LEMON SQUEEZY
**Account**: caymanroden@gmail.com
**Store URL**: chunkytortoise.lemonsqueezy.com
**Dashboard**: https://app.lemonsqueezy.com

### Step 1: Check Identity Verification Status
1. Navigate to https://app.lemonsqueezy.com/settings/general/identity
2. Check if identity verification is complete (look for "Verified" status or green checkmark)
3. If NOT verified: note the status and STOP for this platform — report what you see
4. If verified: proceed to Step 2

### Step 2: Upload 9 Products (if verified)
For each product below, navigate to https://app.lemonsqueezy.com/products → "New product"

Fill in:
- **Name**: (product name)
- **Description**: (paste from product entry below)
- **Media**: Upload the ZIP file from `content/gumroad/zips/` directory (same ZIP names)
- **Pricing**: Set up TWO variants:
  - Variant 1: "One-time Purchase" — one-time payment at listed price
  - Variant 2: "Monthly Subscription" — recurring monthly at listed price

#### Product 1: AgentForge - Starter
- One-time: $49 | Monthly: $9
- ZIP: agentforge-starter-v1.0-20260214.zip
- Description: "Get Started with Production-Ready Multi-LLM Orchestration. Single Python interface for Claude, GPT-4, Gemini, and Perplexity. 550+ tests, Docker setup, CLI tool, Streamlit demo. MIT License."

#### Product 2: AgentForge - Pro
- One-time: $199 | Monthly: $29
- ZIP: agentforge-pro-v1.0-20260214.zip
- Description: "AgentForge Pro — Production Deployment. Everything in Starter + 3 real-world case studies (LegalTech 70% cost reduction, Healthcare HIPAA, Fintech fraud detection), 30-min architecture consultation, 9 advanced code examples, CI/CD templates, priority support, lifetime updates."

#### Product 3: AgentForge - Enterprise
- One-time: $999 | Monthly: $149
- ZIP: agentforge-enterprise-v1.0-20260214.zip
- Description: "AgentForge Enterprise — Expert Support. Everything in Pro + 60-min architecture deep-dive, custom code examples for your domain, private Slack channel (90 days), white-label & resale rights, team training session. For teams of 10+ and enterprise deployments."

#### Product 4: DocQA Engine - Starter
- One-time: $59 | Monthly: $12
- ZIP: docqa-starter-v1.0-20260214.zip
- Description: "DocQA Engine — Production RAG in Hours. Hybrid BM25 + vector retrieval, 5 chunking strategies, source citations, FastAPI with JWT auth, 500+ tests. Self-hosted, zero API costs. MIT License."

#### Product 5: DocQA Engine - Pro
- One-time: $249 | Monthly: $39
- ZIP: docqa-pro-v1.0-20260214.zip
- Description: "DocQA Engine Pro — Enterprise RAG. Everything in Starter + advanced re-ranking (cross-encoder + MMR), multi-document QA, RAGAS evaluation suite (0.89 score), 30-min consultation, priority support, lifetime updates."

#### Product 6: DocQA Engine - Enterprise
- One-time: $1,499 | Monthly: $199
- ZIP: docqa-enterprise-v1.0-20260214.zip
- Description: "DocQA Engine Enterprise — Full RAG Platform. Everything in Pro + multi-tenant deployment, custom domain, SSO, audit logging, SLA-backed support, white-label rights, team training. For enterprise document intelligence at scale."

#### Product 7: Prompt Engineering Toolkit - Starter
- One-time: $29 | Monthly: $5
- ZIP: prompt-toolkit-starter-v1.0-20260214.zip
- Description: "Prompt Engineering Toolkit — Battle-tested prompt patterns, templates, and evaluation frameworks. 200+ prompts across 15 categories, A/B testing framework, cost calculator. Cut prompt development time by 80%."

#### Product 8: Prompt Engineering Toolkit - Pro
- One-time: $79 | Monthly: $12
- ZIP: prompt-toolkit-pro-v1.0-20260214.zip
- Description: "Prompt Toolkit Pro — Advanced patterns + case studies. Everything in Starter + domain-specific prompt libraries (legal, medical, finance, code), meta-prompting templates, prompt chaining patterns, 30-min consultation."

#### Product 9: Prompt Engineering Toolkit - Enterprise
- One-time: $199 | Monthly: $29
- ZIP: prompt-toolkit-enterprise-v1.0-20260214.zip
- Description: "Prompt Toolkit Enterprise — Team-wide prompt governance. Everything in Pro + team prompt library system, versioning & rollback, A/B testing dashboard, compliance templates, white-label rights, team training."

### Step 3: Verify & Publish
After creating all products:
1. Go to https://app.lemonsqueezy.com/products
2. Confirm all 9 products appear
3. Enable the store if still in test mode: Settings → Store → toggle to Live
4. Copy the store URL: https://chunkytortoise.lemonsqueezy.com

---

## PLATFORM 2: CONTRA
**Profile URL**: https://contra.com/cayman_roden_mb0ejazi
**Account**: caymanroden@gmail.com

### Step 1: Check Current Profile State
1. Navigate to https://contra.com/cayman_roden_mb0ejazi
2. Note what's already filled in vs. missing
3. Click "Edit Profile" or the edit button

### Step 2: Add Social Links (if not already set)
In profile edit → Social/Links section:
- LinkedIn: https://linkedin.com/in/caymanroden
- GitHub: https://github.com/ChunkyTortoise
- Portfolio/Website: https://chunkytortoise.github.io

### Step 3: Add Skills (if not already set)
Add these skills (search and select):
Python, FastAPI, AI/ML, RAG Systems, LLM Integration, Chatbot Development,
Data Visualization, Streamlit, PostgreSQL, Redis, Docker, GitHub Actions

### Step 4: Set Hourly Rate
- Rate: $75/hr (or $65-75/hr range if Contra allows a range)

### Step 5: Create Service Listing #1 — Custom RAG AI System

Navigate to Services section → "Add Service" or "Create Service"

**Title**: Custom RAG AI System (Question-Answering Engine)

**Price**: $1,500 (fixed price)

**Delivery**: 5-7 days

**Description** (paste exactly):
```
Transform your documents into an intelligent Q&A engine. Upload PDFs, policies, or manuals, ask questions in plain English, and get precise answers with exact source citations -- in under 200ms.

I build custom RAG (Retrieval-Augmented Generation) systems with 94% retrieval precision and 96% citation accuracy, validated by 322 automated tests and industry-standard RAGAS evaluation (0.89 score).

What you get:
- Production-ready document Q&A system
- Web interface for uploading docs and asking questions
- Source citations with highlighted passages and page numbers
- Hybrid search (keyword + semantic) for maximum recall
- Docker deployment with scaling capabilities
- Full source code and documentation

Tech Stack: Python, FastAPI, ChromaDB/Pinecone, OpenAI/Anthropic, LangChain, Docker
```

**What's Included / Deliverables**:
- Knowledge base system (100 docs)
- Hybrid search implementation
- Source citation engine
- Admin dashboard
- REST API access
- Docker configuration files

### Step 6: Create Service Listing #2 — Chatbot Integration

**Title**: Claude/GPT Chatbot Integration with Lead Qualification

**Price**: $2,000 (fixed price)

**Delivery**: 7-10 days

**Description** (paste exactly):
```
Stop losing leads outside business hours. I build multi-agent AI chatbots that qualify visitors, answer FAQs, and hand off to your sales team at the right moment -- with full CRM sync to GoHighLevel, HubSpot, or Salesforce.

My chatbot platform is backed by 4,937 automated tests, achieves a 94% handoff success rate, and responds in under 200ms. Specialized bot personas handle different conversation types and transfer context seamlessly.

What you get:
- Custom AI chatbot(s) with your brand personality
- Intent recognition and smart conversation routing
- CRM integration with contact creation and lead scoring
- Hot/warm/cold temperature tagging with automated workflows
- Analytics dashboard for tracking conversions
- Full source code and deployment automation

Tech Stack: Python, FastAPI, Redis, Anthropic Claude, OpenAI GPT-4, Pydantic, GitHub Actions
```

**Deliverables**:
- Multi-persona chatbot system (3 personas)
- CRM integration (GHL/HubSpot)
- Lead scoring & qualification logic
- Conversion analytics dashboard
- Web widget for site integration
- Source code & CI/CD pipeline

### Step 7: Create Service Listing #3 — Analytics Dashboard

**Title**: Custom Streamlit Analytics Dashboard & BI Suite

**Price**: $1,200 (fixed price)

**Delivery**: 5-7 days

**Description** (paste exactly):
```
Turn your raw spreadsheet data into a professional, interactive dashboard with filters, drill-downs, and charts that tell a clear story.

I build production-grade dashboards using Python and Streamlit, backed by 313 automated tests. Your dashboard handles messy data automatically -- missing values, duplicates, and formatting issues are cleaned on ingestion. Load 100K rows in under 500ms with no lag.

What you get:
- Interactive charts auto-selected for your data types
- Date, category, and dimension filtering
- Data cleaning and formatting included
- Export to PNG, PDF, or interactive HTML
- Full source code -- you own everything
- Responsive design for desktop and mobile

Tech Stack: Python, Streamlit, Pandas, Plotly, Scikit-learn, Docker
```

**Deliverables**:
- Analytics suite with 15+ interactive charts
- ML-powered forecasting module
- Automated data cleaning pipeline
- API endpoint for data updates
- PDF/PNG export functionality
- Source code & deployment guide

### Step 8: Verify All Services Published
1. Go to https://contra.com/cayman_roden_mb0ejazi/services
2. Confirm all 3 services are visible and live
3. Note the direct URL for each service listing

### Success Metrics
- Profile completeness: 90%+
- 3 services published and purchasable
- Social links, skills, and hourly rate all set

---

## PLATFORM 3: TOPTAL
**Application URL**: https://www.toptal.com/talent/apply
**Account to create/use**: caymanroden@gmail.com

### Step 1: Navigate to Application
1. Go to https://www.toptal.com/talent/apply
2. If already have an account, log in. If not, create one with caymanroden@gmail.com

### Step 2: Fill Application Form

**Full Name**: Cayman Roden

**Email**: caymanroden@gmail.com

**LinkedIn**: https://linkedin.com/in/caymanroden

**GitHub / Portfolio**: https://github.com/ChunkyTortoise

**Primary Expertise / Role**:
Select: Software Engineer (or "Full-Stack Engineer" if that's not available)

**Profile Title** (if asked):
```
Senior Python/AI Engineer | RAG Systems, LLM Orchestration, Production GenAI
```

**Summary / Bio** (paste exactly):
```
Production-focused AI/ML engineer with 20+ years of software experience. I specialize in taking GenAI systems from prototype to production with proper engineering: 80%+ test coverage, P50/P95/P99 benchmarks, Docker deployment, and comprehensive documentation.

Key achievements:
- 89% LLM cost reduction via 3-tier caching (verified benchmarks)
- 4.3M tool dispatches/sec in multi-agent orchestration
- 8,500+ automated tests across 11 production repos
- $50M+ real estate pipeline managed by my AI system

I build systems that run in production on day one: RAG document search (94% retrieval precision), multi-agent chatbot orchestration (94% handoff success rate), and BI dashboards (100K rows in <500ms).
```

**Skills to Select**:
Python, FastAPI, PostgreSQL, Redis, Docker, REST APIs, SQLAlchemy, Pydantic,
Machine Learning, NLP, LLM, RAG Systems, Streamlit, CI/CD, TDD, GitHub Actions

**Availability**:
- Part-time OR full-time (select whichever is available)
- Start date: Immediate
- Work type: Remote only

**Hourly Rate**: $125/hr (or whatever their minimum field allows — aim for $100-150)

**English Proficiency**: Native / Bilingual

**Location**: Palm Springs, CA, USA

### Step 3: Work Experience (if form requests it)
**Most Recent Role**:
- Title: AI/ML Engineer (Freelance)
- Duration: 2020 - Present
- Description: "Building production AI systems: RAG document search, multi-agent chatbot orchestration, and BI dashboards. Notable: 89% LLM cost reduction, 8,500+ automated tests, $50M pipeline under management."

### Step 4: Submit
1. Review all fields are filled
2. Submit the application
3. Note the confirmation message / next steps
4. Screenshot or note the application reference number if provided

### What to Expect After Submission
- Stage 1: Language & communication interview call (usually within 1-2 weeks)
- You'll get an email with scheduling link
- Just be yourself — native English speaker, 20+ years experience

---

## REPORTING

After completing each platform, report:

### Lemon Squeezy
- Verification status: [Verified / Not verified / Pending]
- Products uploaded: [0-9] of 9
- Store URL: https://chunkytortoise.lemonsqueezy.com
- Any errors encountered

### Contra
- Services created: [0-3] of 3
- Profile completeness estimate: [%]
- Profile URL: https://contra.com/cayman_roden_mb0ejazi
- Direct service URLs if available

### Toptal
- Application submitted: [Yes/No]
- Confirmation received: [Yes/No / message]
- Next steps indicated

---

*Generated: 2026-02-17 | For Gemini browser automation*
