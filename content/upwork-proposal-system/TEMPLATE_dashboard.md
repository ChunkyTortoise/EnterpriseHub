# Data Dashboard / Analytics Proposal Template

**Target Jobs**: Data visualization, analytics dashboards, BI tools, data pipeline, ETL, reporting, Streamlit/Plotly/Dash apps

**Avg Win Rate**: 15-20%

**Typical Budget**: $1.5K-$5K fixed-price OR $65-85/hr hourly

---

## Template

Hi [CLIENT NAME],

[HOOK — Reference their specific data sources, current pain point, or visualization need. Examples below.]

I build data pipelines and analytics dashboards in Python. Here's what matches your needs:

[BULLET 1 — Choose most relevant from proof points library]

[BULLET 2 — Secondary technical capability]

[BULLET 3 — Deployment or integration detail if mentioned]

My typical stack: pandas/polars for processing, PostgreSQL or SQLite for storage, Streamlit or [their preferred tool] for dashboards, and Docker for deployment. For ML components I use scikit-learn and XGBoost — I keep it simple unless the problem genuinely needs deep learning.

[CTA — Choose from library based on urgency and complexity]

— Cayman Roden

---

## Hook Examples (Pick One, Customize)

### 1. Multi-Source Data Integration
> "Pulling data from 5 different sources (Shopify, Google Analytics, Stripe, etc.) into a single dashboard with daily refreshes — I've built exactly that with auto-profiling, scheduled ETL, and error alerting when sources go down."

**When to use**: Client mentions multiple APIs, data silos, or "need everything in one place."

### 2. Real-Time Dashboard
> "Real-time dashboards with live PostgreSQL/MongoDB backends require efficient querying and smart caching. I've built Streamlit dashboards that refresh every 30 seconds with <1s load time even with 100K+ rows."

**When to use**: Posts mentioning "real-time," "live updates," or operational dashboards.

### 3. Predictive Analytics
> "Your need for sales forecasting and churn prediction is a great ML use case. I've built predictive models (XGBoost, scikit-learn) with SHAP-based explanations so stakeholders understand why the model predicts what it does."

**When to use**: Posts mentioning forecasting, predictions, ML, or "identify trends."

### 4. Custom Visualizations
> "Building custom interactive charts beyond what PowerBI/Tableau offer — I've used Plotly and Altair to create [specific viz type] with drill-down, filtering, and export to PDF/Excel."

**When to use**: Posts frustrated with BI tool limitations, wanting "custom dashboards," or mentioning specific viz types (Sankey, network graphs, geospatial).

### 5. Performance Optimization
> "Dashboards loading slowly with large datasets is a common pain point. I've optimized dashboards from 15s load time to <2s using query indexing, aggregation tables, and smart caching (Redis/Memcached)."

**When to use**: Client mentions slow dashboards, large datasets, or performance issues.

---

## Proof Point Selection (Choose 2-3)

Rank these based on job post emphasis. Lead with the most relevant.

### Auto-Profiling Dashboard Engine
> **Analytics platform** — Built an auto-profiling engine that generates dashboards from raw datasets, including attribution analysis, predictive modeling (scikit-learn + XGBoost), and SHAP-based feature explanations. 640+ tests. ([insight-engine](https://github.com/ChunkyTortoise/insight-engine))

**When to emphasize**: ML-heavy jobs, predictive analytics, or "build insights from raw data."

### BI Dashboards for Real Estate
> **BI dashboards** — Built Streamlit dashboards for a real estate platform: Monte Carlo simulations, sentiment tracking, churn detection, and pipeline forecasting with live PostgreSQL + Redis backends. Deployed via Docker. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: All dashboard jobs. Shows production deployment, real-time data, domain expertise.

### Data Ingestion + Transformation
> **Data ingestion & transformation** — Built scraping pipelines with change detection, price monitoring with Slack alerts, and Excel-to-SQLite converters with CRUD web interfaces. Handles 10K rows/sec. ([scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve))

**When to emphasize**: ETL jobs, data cleaning, or "pull data from multiple sources."

### Performance Optimization
> **Dashboard performance tuning** — Reduced dashboard load time from 12s to <2s by optimizing SQL queries (indexing, materialized views), implementing Redis caching, and using Polars for 10x faster data processing vs. pandas. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Posts mentioning slow dashboards, large datasets, or performance requirements.

### Custom Visualizations
> **Interactive visualizations** — Built custom Plotly dashboards with drill-down filtering, geographic heatmaps, network graphs, and PDF export. Integrated with PostgreSQL for live updates. ([insight-engine](https://github.com/ChunkyTortoise/insight-engine))

**When to emphasize**: Posts wanting "custom charts," specific viz types, or dissatisfaction with Tableau/PowerBI.

### Statistical Analysis
> **Statistical testing framework** — Implemented A/B testing with z-test significance, confidence intervals, and p-value calculations for product experiments. Built dashboards to visualize test results with statistical rigor. ([jorge_real_estate_bots](https://github.com/ChunkyTortoise/jorge_real_estate_bots))

**When to emphasize**: Posts mentioning A/B testing, experiments, or "need statistical analysis."

---

## Stack Paragraph (Customize)

Base version:
> "My typical stack: pandas/polars for processing, PostgreSQL or SQLite for storage, Streamlit or [their preferred tool] for dashboards, and Docker for deployment. For ML components I use scikit-learn and XGBoost — I keep it simple unless the problem genuinely needs deep learning."

### Dashboard Tool Selection

| Tool | When to Use | Strengths | Tradeoffs |
|------|-------------|-----------|-----------|
| **Streamlit** | Default choice — fast to build, Python-native | Easy deployment, interactive widgets, free hosting | Limited customization vs. React |
| **Plotly Dash** | Client wants React-like customization or enterprise features | More flexible layout, callbacks, production-ready | Steeper learning curve |
| **Retool** | Internal tools, CRUD operations, rapid prototyping | Drag-and-drop, fast iteration | Vendor lock-in, pricing |
| **Metabase/Superset** | Self-service BI, non-technical users | SQL-based, easy for analysts | Less custom than code-based tools |
| **Tableau/PowerBI** | Client already uses it, want extensions | Familiar to stakeholders | Expensive, limited custom logic |

**Recommendation**: Default to Streamlit (fast, cheap, easy deployment). Mention Dash if client wants more customization. Only suggest Retool/Metabase if they say "need analysts to build their own reports."

### Data Processing: pandas vs. polars

| Library | When to Use |
|---------|-------------|
| **pandas** | <1M rows, standard operations, wide ecosystem |
| **polars** | >1M rows, performance-critical, or when 10x speedup matters |

**In proposal**: Mention "pandas/polars" to show you know both. If client mentions "large datasets," emphasize polars explicitly.

---

## CTA Options (Choose Based on Client Engagement)

### 1. Sample Dashboard (Most Effective)
> "Want me to send a quick mockup of what [specific dashboard] could look like with your data? I can build a sample with dummy data to show the layout and interactivity."

**When to use**: P1 jobs, clients who are visual thinkers, when you want to stand out.

### 2. Data Source Clarification
> "Happy to scope this more precisely after a quick look at [their data sources / current setup]. What does your data structure look like (CSV, database, API)?"

**When to use**: Vague posts, when you need more info to quote accurately.

### 3. Timeline Commitment
> "I can start [this week / Monday] and typically deliver dashboard MVPs in 1-2 weeks with live data integration in week 3."

**When to use**: Time-sensitive posts, competitive bidding.

### 4. Cost Breakdown
> "Happy to provide a detailed cost breakdown (data pipeline + dashboard + hosting) once I understand your refresh cadence and user count."

**When to use**: Budget-conscious clients, posts asking for quotes.

### 5. Portfolio Link (P2 Jobs)
> "I'm available [this week] if you'd like to discuss. Here's my full portfolio: https://chunkytortoise.github.io"

**When to use**: P2 jobs, when you need more context before committing.

---

## Customization Checklist

Before sending, verify:

- [ ] Hook mentions their specific data sources (Shopify, Salesforce, CSV exports, etc.)
- [ ] Proof points ordered by relevance (ML bullet only if they mention predictions)
- [ ] Dashboard tool matches their preference (if stated)
- [ ] If they want "real-time," emphasize caching and performance
- [ ] CTA matches their urgency and detail level
- [ ] Total word count <275
- [ ] No typos in client name, company, or technical terms
- [ ] Rate quoted aligns with complexity ($65-85/hr for dashboard work)

---

## Rate Guidance

| Job Complexity | Suggested Rate |
|----------------|----------------|
| Simple dashboard (1-2 data sources, basic charts) | $65/hr or $1.5K-$2.5K fixed |
| Multi-source ETL + dashboard | $75/hr or $3K-$5K fixed |
| Predictive analytics + dashboard | $85/hr or $5K-$8K fixed |
| Enterprise (real-time, custom viz, high performance) | $85-100/hr or $8K-$15K fixed |

**Fixed-price tip**: Dashboards are iterative — stakeholders will request changes after seeing v1. Build in 2-3 revision rounds. Estimate conservatively and add 20% buffer.

**Phased pricing approach**:
- Phase 1: Data pipeline + basic dashboard ($2K)
- Phase 2: Custom visualizations + interactivity ($1.5K)
- Phase 3: Performance tuning + deployment ($1K)

---

## Data Source-Specific Adjustments

### Shopify / E-Commerce
> "For Shopify data, I've built dashboards pulling from the Admin API (orders, products, customers) with daily sync and cohort analysis for retention tracking."

### Google Analytics / Marketing
> "For GA4 data, I've used the Analytics Data API with attribution modeling, funnel analysis, and campaign ROI dashboards."

### Salesforce / CRM
> "For Salesforce, I've integrated via REST API with OAuth 2.0, pulling leads, opportunities, and custom objects for sales pipeline dashboards."

### Database (MySQL, PostgreSQL, MongoDB)
> "For direct database access, I've built read-replica connections with query optimization (indexing, materialized views) to avoid impacting production."

### CSV / Excel Files
> "For Excel/CSV uploads, I've built drag-and-drop interfaces with data validation, auto-detect column types, and error reporting for bad data."

---

## ML-Specific Guidance

Only include ML bullets if the job mentions:
- Forecasting / predictions
- Churn detection
- Anomaly detection
- Clustering / segmentation
- "ML" or "machine learning" explicitly

**ML hook example**:
> "Your need for sales forecasting with seasonality detection is a great time-series ML problem. I've built ARIMA + XGBoost ensemble models with confidence intervals and explainability (SHAP) so stakeholders trust the predictions."

**When NOT to mention ML**: Pure dashboard/visualization jobs. Clients who don't mention it will think you're overcomplicating.

---

**Last Updated**: February 14, 2026
