# Gumroad Product Upload & Optimization Spec — Gemini Handoff

**Date**: 2026-02-16
**Account**: gumroad.com (Cayman Roden / caymanroden@gmail.com)
**Products to Upload**: 18 individual + 3 bundles = 21 total listings
**Estimated Time**: 4-6 hours total
**Priority**: Revenue-Sprint products first (fastest path to sales)

---

## WHAT'S ALREADY DONE (Do Not Redo)

### Content Created (All listing copy complete)
- [x] 15 individual product listing files (`content/gumroad/*-LISTING.md`)
- [x] 3 bundle product specifications (`content/gumroad/BUNDLE_LISTINGS.md`)
- [x] 14 pro-tier case studies (`content/gumroad/pro-content/*.md`)
- [x] Supporting files for Pro/Enterprise tiers (`content/gumroad/supporting-files/`)
- [x] Email upsell sequences (Starter→Pro, Pro→Enterprise)
- [x] SEO optimization guide
- [x] Repricing strategy document
- [x] Listing audit report with specific improvements

### ZIP Packages Built (All 24 ZIPs exist)
Location: `content/gumroad/zips/`

Individual products (21 ZIPs):
- `agentforge-starter-v1.0-20260214.zip`
- `agentforge-pro-v1.0-20260214.zip`
- `agentforge-enterprise-v1.0-20260214.zip`
- `docqa-starter-v1.0-20260214.zip`
- `docqa-pro-v1.0-20260214.zip`
- `docqa-enterprise-v1.0-20260214.zip`
- `scraper-starter-v1.0-20260214.zip`
- `scraper-pro-v1.0-20260214.zip`
- `scraper-enterprise-v1.0-20260214.zip`
- `insight-starter-v1.0-20260214.zip`
- `insight-pro-v1.0-20260214.zip`
- `insight-enterprise-v1.0-20260214.zip`
- `prompt-toolkit-starter-v1.0-20260214.zip`
- `prompt-toolkit-pro-v1.0-20260214.zip`
- `prompt-toolkit-enterprise-v1.0-20260214.zip`
- `llm-starter-starter-v1.0-20260214.zip`
- `llm-starter-pro-v1.0-20260214.zip`
- `llm-starter-enterprise-v1.0-20260214.zip`
- `dashboard-starter-v1.0-20260214.zip`
- `dashboard-pro-v1.0-20260214.zip`
- `dashboard-enterprise-v1.0-20260214.zip`

Bundles (3 ZIPs):
- `all-starters-bundle-v1.0-20260215.zip`
- `all-pro-bundle-v1.0-20260215.zip`
- `revenue-sprint-bundle-v1.0-20260215.zip`

### Screenshots (AgentForge only)
Location: `content/gumroad/screenshots/agentforge/` (7 images)

### Live Streamlit Demos (for screenshots)
- https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/ (AgentForge)
- https://ct-document-engine.streamlit.app/ (DocQA)
- https://ct-prompt-lab.streamlit.app/ (Prompt Lab)
- https://ct-llm-starter.streamlit.app/ (LLM Starter)

---

## PREREQUISITE CHECKS (Do These First)

### Check 1: Gumroad Payment Method
1. Go to https://gumroad.com/settings/payments
2. Verify a payment method (Stripe/PayPal) is connected
3. **If NOT connected**: This BLOCKS all publishing. Stop and notify the user.
4. **CRITICAL**: Without payment configured, the "Publish and continue" button will show a red toast error and NOT actually publish.

### Check 2: Existing Products
1. Go to https://gumroad.com/dashboard/products
2. List ALL existing products (there may be old single-tier products at $29-$49)
3. **If old products exist at old prices**: Do NOT delete them. Instead:
   - Unpublish them (set to draft/private)
   - They serve as historical record
   - Create NEW products with the new 3-tier pricing
4. Note the exact number and names of existing products

### Check 3: Account Profile
1. Go to https://gumroad.com/settings
2. Verify profile name: "Cayman Roden" or "ChunkyTortoise"
3. Verify profile bio mentions AI engineering, production-grade code, 7,000+ tests
4. If bio is empty/generic, set it to:
   > AI Engineer building production-grade developer tools. 11 repos, 7,000+ automated tests, real deployments. Specializing in LLM orchestration, RAG pipelines, web scraping, and data dashboards.

---

## TASK 1: Upload Revenue-Sprint Products (Priority — Do First)

These are the fastest path to revenue. Upload all 3 products, each with 3 tiers = 9 listings.

### Product 1: Prompt Engineering Toolkit

#### Starter ($29)
1. **Create new product**: Products → New Product → Digital Product
2. **Name**: `Prompt Engineering Toolkit - Starter`
3. **URL slug**: `prompt-toolkit-starter`
4. **Price**: $29 (fixed price, NOT pay-what-you-want)
5. **Upload file**: `content/gumroad/zips/prompt-toolkit-starter-v1.0-20260214.zip`
6. **Description**: Copy the "Full Description" section from `content/gumroad/revenue-sprint-1-prompt-toolkit-LISTING.md`
   - Start from "# Prompt Engineering Toolkit - Stop Guessing, Start Shipping"
   - End before the "What's Included" metadata section
   - Gumroad supports Markdown formatting
7. **Tags**: `prompt-engineering, llm-prompts, chatgpt-prompts, claude-prompts, ai-prompts, prompt-templates, prompt-optimization, token-counting, ai-cost-reduction, prompt-patterns, python, template-manager, developer-tools, ai-development`
8. **Category**: Software (or "Developer Tools" if available)
9. **Cover image**: Take a screenshot of https://ct-prompt-lab.streamlit.app/ and use as cover. Crop to 1280x720 if needed.
10. **Add FAQ** (type directly into description or use Gumroad's FAQ feature if available):

```
## FAQ

**Q: Do these patterns work with Claude and GPT?**
A: Yes. All 8 patterns work with Claude, GPT-4, GPT-3.5, Gemini, and any LLM that accepts text prompts. The template manager and token counter support all major providers.

**Q: Can I use this commercially?**
A: Absolutely. MIT License — use in unlimited commercial projects with no attribution required.

**Q: Do I need coding experience?**
A: Basic Python knowledge helps, but the README has step-by-step setup instructions. The 10 example templates work out of the box.

**Q: What's the difference between Starter and Pro?**
A: Starter gives you 8 patterns + template manager + token counter. Pro adds A/B testing, cost optimizer, prompt versioning, safety checker, and evaluation metrics.

**Q: Is there a refund policy?**
A: Yes, 30-day money-back guarantee. No questions asked.
```

11. **Publish** the product

#### Pro ($79)
1. **Name**: `Prompt Engineering Toolkit - Pro`
2. **URL slug**: `prompt-toolkit-pro`
3. **Price**: $79 (fixed)
4. **Upload file**: `content/gumroad/zips/prompt-toolkit-pro-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/revenue-sprint-1-prompt-toolkit-LISTING.md` — the Pro section starting at "# Prompt Engineering Toolkit Pro"
6. **Tags**: `prompt-engineering, ab-testing, cost-optimization, prompt-versioning, llm-prompts, prompt-safety, evaluation-metrics, cli-tool, chatgpt, claude, gemini, python, developer-tools, production-ready`
7. **Cover image**: Same Streamlit screenshot as Starter, but add "PRO" text overlay if possible (or reuse same image)
8. **Add FAQ**:

```
## FAQ

**Q: When do I get the A/B testing framework?**
A: Immediately upon purchase. Everything is in the ZIP file — A/B testing, cost optimizer, versioning, safety checker, and CLI tool.

**Q: Can I upgrade from Starter to Pro later?**
A: Yes, contact caymanroden@gmail.com with your Starter receipt and we'll provide a discount code for the price difference.

**Q: What does the CLI tool do?**
A: The `pel` command lets you test prompts from terminal, run batch processing, and integrate prompt testing into CI/CD pipelines.

**Q: Are the evaluation metrics automated?**
A: Yes. Relevance, coherence, completeness, accuracy, and conciseness are scored automatically with configurable thresholds.
```

9. **Publish**

#### Enterprise ($199)
1. **Name**: `Prompt Engineering Toolkit - Enterprise`
2. **URL slug**: `prompt-toolkit-enterprise`
3. **Price**: $199 (fixed)
4. **Upload file**: `content/gumroad/zips/prompt-toolkit-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from the listing file — Enterprise section starting at "# Prompt Engineering Toolkit Enterprise"
6. **Tags**: `prompt-engineering, enterprise, benchmark-runner, report-generator, commercial-license, priority-support, consulting, docker, ci-cd, production-grade, llm-prompts, team-training, python`
7. **Add FAQ**:

```
## FAQ

**Q: How do I schedule the 30-minute consultation?**
A: The ZIP includes CONSULTATION_BOOKING.txt with a Calendly link. Book within 90 days of purchase.

**Q: What does the commercial license allow?**
A: Unlimited team members, unlimited commercial projects, no attribution required, and resale rights for agencies.

**Q: How long does priority support last?**
A: 30 days from purchase. Direct email to caymanroden@gmail.com with 48-hour response SLA on business days.

**Q: Can I use the benchmark runner in CI/CD?**
A: Yes. GitHub Actions and GitLab CI templates are included. Quality gates automatically block prompt changes that reduce performance.
```

8. **Publish**

---

### Product 2: AI Integration Starter Kit

#### Starter ($39)
1. **Name**: `AI Integration Starter Kit`
2. **URL slug**: `llm-starter-kit`
3. **Price**: $39 (fixed)
4. **Upload file**: `content/gumroad/zips/llm-starter-starter-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/revenue-sprint-2-llm-starter-LISTING.md` — section starting "# AI Integration Starter Kit - Ship LLM Features in Hours, Not Weeks"
6. **Tags**: `llm-integration, ai-starter-kit, chatgpt-api, claude-api, openai-python, llm-python, ai-boilerplate, function-calling, rag-pipeline, ai-development, cost-tracking, streaming, multi-provider, python, developer-tools`
7. **Cover image**: Screenshot of https://ct-llm-starter.streamlit.app/
8. **Add FAQ**:

```
## FAQ

**Q: Which LLM providers are supported?**
A: Claude (Opus, Sonnet, Haiku), GPT (GPT-4, GPT-3.5 Turbo), and Gemini (Pro, Flash). All use a unified interface.

**Q: Do I need my own API keys?**
A: Yes, you'll need API keys from the providers you want to use. The code handles all authentication — just set environment variables.

**Q: Can I use this in production?**
A: The Starter tier is great for prototyping and MVPs. For production with retry logic, circuit breakers, and caching, see the Pro tier.

**Q: What's included in the 15 examples?**
A: Chat completion, streaming, function calling, RAG, multi-turn conversations, batch processing, cost-aware routing, error handling, testing with mocks, and more.

**Q: Is there a refund policy?**
A: 30-day money-back guarantee, no questions asked.
```

9. **Publish**

#### Pro ($99)
1. **Name**: `AI Integration Starter Kit - Pro`
2. **URL slug**: `llm-starter-kit-pro`
3. **Price**: $99 (fixed)
4. **Upload file**: `content/gumroad/zips/llm-starter-pro-v1.0-20260214.zip`
5. **Description**: Copy from listing file — Pro section "# AI Integration Starter Kit Pro - Production-Hardened LLM Integration"
6. **Tags**: `llm-integration, production-ready, retry-logic, circuit-breaker, response-caching, batch-processing, guardrails, latency-tracker, fallback-chain, cli-tool, claude, gpt-4, gemini, python, reliability`
7. **Add FAQ**:

```
## FAQ

**Q: What's the difference between Starter and Pro?**
A: Starter gives you the LLM client + examples. Pro adds production hardening: retry with exponential backoff, circuit breaker, response caching (in-memory + Redis), batch processor, guardrails (content filtering, PII detection), latency tracking, and fallback chains.

**Q: Does the circuit breaker work across providers?**
A: Yes. Each provider has independent circuit breaker state. If Claude is down, the fallback chain automatically routes to GPT or Gemini.

**Q: Is Redis required for caching?**
A: No. In-memory caching works out of the box. Redis is optional for multi-instance deployments.

**Q: Can I upgrade from Starter?**
A: Yes, email caymanroden@gmail.com with your Starter receipt for a discount code.
```

8. **Publish**

#### Enterprise ($249)
1. **Name**: `AI Integration Starter Kit - Enterprise`
2. **URL slug**: `llm-starter-kit-enterprise`
3. **Price**: $249 (fixed)
4. **Upload file**: `content/gumroad/zips/llm-starter-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from listing file — Enterprise section
6. **Tags**: `llm-integration, enterprise, multi-provider-orchestration, observability, mock-llm, docker, kubernetes, ci-cd, commercial-license, priority-support, consulting, production-grade, sla, team-training`
7. **Add FAQ**:

```
## FAQ

**Q: How do I schedule the 30-minute consultation?**
A: CONSULTATION_BOOKING.txt in the ZIP has a Calendly link. Book within 90 days of purchase.

**Q: Does this include Kubernetes manifests?**
A: Yes. Deployment, Service, ConfigMap, Secret, and HPA templates. Liveness and readiness probes included.

**Q: What does the mock LLM do?**
A: Zero API calls during testing. Configure responses, latencies, and error scenarios. Perfect for CI/CD pipelines.

**Q: What's in the observability pipeline?**
A: Structured logging with correlation IDs, Prometheus-compatible metrics, OpenTelemetry tracing, and pre-built Grafana dashboards.
```

8. **Publish**

---

### Product 3: Streamlit Dashboard Templates

#### Starter ($49)
1. **Name**: `Streamlit Dashboard Templates`
2. **URL slug**: `dashboard-templates-starter`
3. **Price**: $49 (fixed)
4. **Upload file**: `content/gumroad/zips/dashboard-starter-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/revenue-sprint-3-dashboard-templates-LISTING.md` — Starter section
6. **Tags**: `streamlit, dashboard, data-visualization, analytics, python, plotly, pandas, data-science, csv-to-dashboard, auto-profiling, anomaly-detection, ml-predictions, report-generator, templates`
7. **Cover image**: Screenshot of any Streamlit demo app showing charts/dashboards
8. **Add FAQ**:

```
## FAQ

**Q: What file formats do you accept?**
A: CSV and Excel (.xlsx, .xls). Upload and get dashboards in under 30 seconds.

**Q: Do I need Python or data science skills?**
A: Basic Python helps for customization, but the templates work out of the box. Upload data, get dashboards.

**Q: How many chart types are included?**
A: 20+ interactive charts: histograms, box plots, scatter matrices, heatmaps, time series, bar charts, pie charts, SHAP waterfall, feature importance, and more.

**Q: Can I deploy to Streamlit Cloud?**
A: Yes. All templates are Streamlit Cloud compatible. Free hosting available at share.streamlit.io.

**Q: Is there a refund policy?**
A: 30-day money-back guarantee, no questions asked.
```

9. **Publish**

#### Pro ($99)
1. **Name**: `Streamlit Dashboard Templates - Pro`
2. **URL slug**: `dashboard-templates-pro`
3. **Price**: $99 (fixed)
4. **Upload file**: `content/gumroad/zips/dashboard-pro-v1.0-20260214.zip`
5. **Description**: Copy from listing file — Pro section
6. **Tags**: `streamlit, dashboard, data-visualization, analytics, database-connectors, custom-styling, scheduled-reports, python, plotly, production-ready, advanced-templates`
7. **Publish**

#### Enterprise ($249)
1. **Name**: `Streamlit Dashboard Templates - Enterprise`
2. **URL slug**: `dashboard-templates-enterprise`
3. **Price**: $249 (fixed)
4. **Upload file**: `content/gumroad/zips/dashboard-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from listing file — Enterprise section
6. **Tags**: `streamlit, dashboard, enterprise, white-label, custom-development, real-time, commercial-license, priority-support, consulting, production-grade`
7. **Publish**

---

### Revenue-Sprint Bundle
1. **Name**: `Revenue-Sprint Starter Bundle (3 Products - Save 16%)`
2. **URL slug**: `revenue-sprint-bundle`
3. **Price**: $99 (fixed)
4. **Upload file**: `content/gumroad/zips/revenue-sprint-bundle-v1.0-20260215.zip`
5. **Description**: Copy from `content/gumroad/GUMROAD_UPLOAD_MANIFEST.md` — the Revenue-Sprint Bundle section starting "# Revenue-Sprint Starter Bundle"
6. **Tags**: `bundle, revenue-sprint, prompt-engineering, llm-integration, streamlit-dashboard, python, starter-kit, ai-development, developer-tools, production-ready, quick-win`
7. **Publish**

---

## TASK 2: Upload Original Products (4 Products x 3 Tiers = 12 Listings)

### Product 4: AgentForge (Multi-LLM Orchestration)

#### Starter ($49)
1. **Name**: `AgentForge Starter - Multi-LLM Orchestration Framework`
2. **URL slug**: `agentforge-starter`
3. **Price**: $49 — **Enable "Pay what you want"** (minimum $49)
4. **Upload file**: `content/gumroad/zips/agentforge-starter-v1.0-20260214.zip`
5. **Description**: Copy full description from `content/gumroad/agentforge-starter-LISTING.md` (lines after the metadata header)
6. **Tags**: `llm-orchestrator, multi-provider, claude, gemini, openai, python, async, rate-limiting, cost-tracking, production-ready, ai-api, chatbot, agent-framework, starter-kit, mit-license`
7. **Cover image**: Use screenshot from `content/gumroad/screenshots/agentforge/` — pick the best one showing the Streamlit demo
8. **Add FAQ**:

```
## FAQ

**Q: Do I need my own API keys?**
A: Yes, for real providers (Claude, GPT, Gemini). But the included Mock Provider lets you test everything WITHOUT API keys or costs.

**Q: Which LLM providers are supported?**
A: Claude (Anthropic), GPT-4/3.5 (OpenAI), Gemini (Google), and Perplexity. All unified under one async interface.

**Q: How does this compare to LangChain?**
A: AgentForge is 15KB core vs LangChain's 800KB+. No heavy dependencies. Focused on orchestration, not everything. 550+ tests vs LangChain's known reliability issues.

**Q: Can I use this commercially?**
A: Yes. MIT License — unlimited commercial projects, no attribution required.

**Q: What's the difference between Starter, Pro, and Enterprise?**
A: Starter = framework + docs + examples. Pro = adds 3 case studies + 30-min consult + priority support. Enterprise = adds 60-min deep-dive + white-label rights + 90-day Slack support.

**Q: Is there a refund policy?**
A: 30-day money-back guarantee, no questions asked.
```

9. **Publish**

#### Pro ($199)
1. **Name**: `AgentForge Pro - Framework + Case Studies + Expert Consult`
2. **URL slug**: `agentforge-pro`
3. **Price**: $199 (fixed, NO pay-what-you-want)
4. **Upload file**: `content/gumroad/zips/agentforge-pro-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/agentforge-pro-LISTING.md`
6. **Tags**: `llm-orchestrator, production-ready, case-studies, consulting, expert-support, claude, gpt-4, gemini, cost-optimization, hipaa, fraud-detection, legal-tech, healthcare-ai, fintech, python`
7. **Add FAQ**:

```
## FAQ

**Q: When do I get the 30-minute consultation?**
A: Immediately. The ZIP includes CONSULTATION_BOOKING.txt with a Calendly link. Book at your convenience within 90 days.

**Q: Are the case studies real or hypothetical?**
A: Based on real production deployments with anonymized details. Each includes full code, configuration, and measured results (e.g., $147K/year savings).

**Q: What's in "priority support"?**
A: Direct email to caymanroden@gmail.com with 48-hour response SLA on business days. Includes implementation guidance, debugging help, and architecture advice.

**Q: Can I upgrade from Starter?**
A: Yes. Email caymanroden@gmail.com with your Starter receipt for a discount code covering the price difference.
```

8. **Publish**

#### Enterprise ($999)
1. **Name**: `AgentForge Enterprise - Framework + Consulting + White-Label Rights`
2. **URL slug**: `agentforge-enterprise`
3. **Price**: $999 (fixed)
4. **Upload file**: `content/gumroad/zips/agentforge-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/agentforge-enterprise-LISTING.md`
6. **Tags**: `llm-orchestrator, enterprise, white-label, consulting, custom-development, slack-support, sla, hipaa, soc2, compliance, multi-tenant, resale-rights, agency, production-grade, team-training`
7. **Add FAQ**:

```
## FAQ

**Q: How quickly can I schedule the 60-minute deep-dive?**
A: Within 7 business days of purchase. ENTERPRISE_KICKOFF.txt has the booking link.

**Q: What does "white-label" legally allow?**
A: Full resale rights. Rebrand, embed in your product, sell to your clients. No attribution to us required. Full terms in WHITE_LABEL_LICENSE.txt.

**Q: Do you sign NDAs?**
A: Yes. Standard mutual NDA provided upon request.

**Q: What if my use case requires HIPAA/SOC2 compliance?**
A: The Enterprise package includes compliance configuration guides for HIPAA and SOC2. The 60-min deep-dive covers your specific compliance requirements.

**Q: Can I extend Slack support beyond 90 days?**
A: Yes. Renewal available at $200/month for continued Slack access and priority support.

**Q: What if I need more than 2-3 custom examples?**
A: Additional custom examples available at $150/each. Discuss during your deep-dive call.
```

8. **Publish**

---

### Product 5: DocQA Engine (Production RAG Pipeline)

#### Starter ($59)
1. **Name**: `DocQA Engine Starter - Production RAG Pipeline`
2. **URL slug**: `docqa-starter`
3. **Price**: $59 — **Enable "Pay what you want"** (minimum $59)
4. **Upload file**: `content/gumroad/zips/docqa-starter-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/docqa-starter-LISTING.md`
6. **Tags**: `rag, retrieval-augmented-generation, document-qa, hybrid-search, bm25, vector-search, semantic-search, chatbot, knowledge-base, fastapi, streamlit, self-hosted, production-ready, python, citation, embeddings`
7. **Cover image**: Screenshot of https://ct-document-engine.streamlit.app/
8. **Add to description** (append at bottom):

```
## Try Before You Buy

Live demo: https://ct-document-engine.streamlit.app/ — Upload your own PDFs and see RAG in action.

## FAQ

**Q: What document formats do you support?**
A: PDF, TXT, Markdown, and HTML out of the box. Extensible for DOCX, PPTX via optional parsers.

**Q: How many documents can I process?**
A: Tested with 500+ documents. The hybrid retrieval engine scales linearly. No external vector DB subscription required — ChromaDB included.

**Q: Is this better than using ChatGPT's file upload?**
A: Yes, for production use. You control the data (self-hosted), get source citations with page numbers, and can customize chunking/retrieval for your domain. ChatGPT's upload is a black box.

**Q: Do I need a vector database subscription?**
A: No. ChromaDB is included and runs locally. For enterprise scale, the Enterprise tier includes migration guides for Qdrant, Weaviate, and Pinecone.

**Q: Can I integrate this with my existing app?**
A: Yes. Full REST API with FastAPI. JWT auth, rate limiting, and CORS already configured.
```

9. **Publish**

#### Pro ($249)
1. **Name**: `DocQA Engine Pro - RAG Pipeline + Case Studies + Expert Consult`
2. **URL slug**: `docqa-pro`
3. **Price**: $249 (fixed)
4. **Upload file**: `content/gumroad/zips/docqa-pro-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/docqa-pro-LISTING.md`
6. **Tags**: `rag, retrieval-augmented-generation, document-qa, production-ready, case-studies, consulting, expert-support, hybrid-search, citation, hipaa, legal-tech, healthcare-ai, financial-analysis, python`
7. **Add FAQ**:

```
## FAQ

**Q: How detailed is the 30-page RAG optimization guide?**
A: Covers chunking strategy selection, embedding model benchmarks, hybrid retrieval tuning, re-ranking optimization, and evaluation metrics. Includes code for each technique.

**Q: Are the case studies code walkthroughs?**
A: Yes. Each case study includes the specific configuration, chunking strategy, retrieval setup, and before/after metrics. Legal case study: 78% → 94% recall improvement.

**Q: When do I get the 30-minute consultation?**
A: Calendly link in the ZIP. Book within 90 days of purchase.

**Q: What if I need help with a specific document type?**
A: The consultation covers your specific use case. Bring your document samples and we'll configure the optimal chunking/retrieval strategy together.
```

8. **Publish**

#### Enterprise ($1,499)
1. **Name**: `DocQA Engine Enterprise - RAG Pipeline + Consulting + White-Label`
2. **URL slug**: `docqa-enterprise`
3. **Price**: $1,499 (fixed)
4. **Upload file**: `content/gumroad/zips/docqa-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/docqa-enterprise-LISTING.md`
6. **Tags**: `rag, enterprise, white-label, consulting, custom-development, slack-support, sla, hipaa, compliance, production-grade, team-training, resale-rights, agency, document-qa, legal-tech`
7. **Add FAQ**:

```
## FAQ

**Q: What exactly is "custom domain tuning"?**
A: We analyze 50+ sample documents from your domain, configure chunk boundaries for your content structure, tune BM25 weights for your terminology, and benchmark retrieval quality on your actual queries. Delivered as a tuned config file + 10-page performance report.

**Q: Can you handle non-English documents?**
A: Yes. The system supports multilingual embeddings. Domain tuning can be configured for any language with available embedding models.

**Q: What's included in the vector DB migration guide?**
A: Step-by-step migration from ChromaDB to Qdrant, Weaviate, or Pinecone. Includes performance benchmarks, configuration templates, and cost comparison.

**Q: What happens after 90 days of Slack support?**
A: Renewal available at $300/month. Or switch to email-only priority support at $150/month.

**Q: Do you offer on-premise deployment assistance?**
A: Yes, covered in the 60-minute deep-dive. Docker and Kubernetes deployment templates included.
```

8. **Publish**

---

### Product 6: Web Scraper & Price Monitor

#### Starter ($49)
1. **Name**: `Web Scraper & Price Monitor - YAML-Config Toolkit`
2. **URL slug**: `scraper-starter`
3. **Price**: $49 — **Enable "Pay what you want"** (minimum $49)
4. **Upload file**: `content/gumroad/zips/scraper-starter-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/scraper-starter-LISTING.md`
6. **Tags**: `web-scraper, price-monitoring, price-tracking, seo, seo-scoring, yaml-config, change-detection, beautifulsoup, async, e-commerce, competitive-intelligence, affiliate, data-pipeline, streamlit, plotly, python, automation`
7. **Add FAQ**:

```
## FAQ

**Q: Is web scraping legal?**
A: Scraping publicly accessible data is generally legal. This toolkit includes robots.txt checking and rate limiting. Always respect website terms of service. A compliance note is included in the documentation.

**Q: Will I get blocked by websites?**
A: The Starter tier includes rate limiting and respectful request spacing. For advanced anti-detection (proxy rotation, browser fingerprinting), see the Pro tier.

**Q: Can I scrape JavaScript-heavy sites?**
A: The Starter tier uses BeautifulSoup (HTML only). For JS-rendered pages, the Pro tier includes Selenium/Playwright integration guides.

**Q: How does YAML configuration work?**
A: Define scraper rules in YAML files — no code needed. Specify URLs, CSS selectors, extraction rules, and scheduling. 3 example configs included (Amazon, e-commerce, SEO).

**Q: What's the SHA-256 change detection?**
A: Each page is hashed on every scrape. When the hash changes, you get notified. Perfect for price monitoring, content updates, and competitor tracking.
```

8. **Publish**

#### Pro ($149)
1. **Name**: `Web Scraper Pro - Toolkit + Templates + Anti-Detection`
2. **URL slug**: `scraper-pro`
3. **Price**: $149 (fixed)
4. **Upload file**: `content/gumroad/zips/scraper-pro-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/scraper-pro-LISTING.md`
6. **Tags**: `web-scraper, production-ready, proxy-rotation, anti-detection, price-monitoring, competitive-intelligence, seo, templates, consulting, expert-support, e-commerce, affiliate, data-pipeline, python`
7. **Publish**

#### Enterprise ($699)
1. **Name**: `Web Scraper Enterprise - Toolkit + Custom Configs + White-Label`
2. **URL slug**: `scraper-enterprise`
3. **Price**: $699 (fixed)
4. **Upload file**: `content/gumroad/zips/scraper-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/scraper-enterprise-LISTING.md`
6. **Tags**: `web-scraper, enterprise, white-label, consulting, custom-development, slack-support, sla, compliance, production-grade, resale-rights, agency, data-pipeline, e-commerce, competitive-intelligence`
7. **Publish**

---

### Product 7: Data Intelligence Dashboard

#### Starter ($49)
1. **Name**: `Data Intelligence Dashboard - Upload to Insights in 30 Seconds`
2. **URL slug**: `insight-starter`
3. **Price**: $49 — **Enable "Pay what you want"** (minimum $49)
4. **Upload file**: `content/gumroad/zips/insight-starter-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/insight-starter-LISTING.md`
6. **Tags**: `data-dashboard, business-intelligence, bi-tool, data-analysis, machine-learning, shap, explainable-ai, marketing-attribution, predictive-analytics, clustering, time-series-forecasting, anomaly-detection, data-cleaning, streamlit, plotly, sklearn, xgboost, python, self-hosted`
7. **Add FAQ**:

```
## FAQ

**Q: What file formats do you accept?**
A: CSV and Excel (.xlsx, .xls). Upload and get instant dashboards, predictions, and PDF reports.

**Q: How large of a dataset can I upload?**
A: Tested up to 1M rows. The auto-profiler and dashboard generator handle large datasets efficiently with sampling for visualizations.

**Q: Do I need to know Python or data science?**
A: No. Upload your data and the system auto-generates profiling, charts, anomaly detection, and forecasts. Python knowledge helps for customization.

**Q: What are the 4 attribution models?**
A: First Touch, Last Touch, Linear, and Time Decay. Each shows which marketing channels drive conversions, with SHAP explanations for transparency.

**Q: Is my data secure?**
A: 100% self-hosted. Your data never leaves your machine. No cloud dependencies, no data sharing.
```

8. **Publish**

#### Pro ($199)
1. **Name**: `Data Intelligence Pro - Dashboard + Case Studies + Analytics Guide`
2. **URL slug**: `insight-pro`
3. **Price**: $199 (fixed)
4. **Upload file**: `content/gumroad/zips/insight-pro-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/insight-pro-LISTING.md`
6. **Tags**: `data-dashboard, business-intelligence, production-ready, case-studies, consulting, expert-support, marketing-attribution, predictive-analytics, shap, clustering, forecasting, report-templates, database-connectors, python`
7. **Publish**

#### Enterprise ($999)
1. **Name**: `Data Intelligence Enterprise - Dashboard + Consulting + White-Label`
2. **URL slug**: `insight-enterprise`
3. **Price**: $999 (fixed)
4. **Upload file**: `content/gumroad/zips/insight-enterprise-v1.0-20260214.zip`
5. **Description**: Copy from `content/gumroad/insight-enterprise-LISTING.md`
6. **Tags**: `data-dashboard, enterprise, white-label, consulting, custom-development, slack-support, sla, production-grade, team-training, resale-rights, agency, business-intelligence, real-time, streaming, bigquery`
7. **Publish**

---

## TASK 3: Upload Bundle Products (3 Bundles)

### All Starters Bundle
1. **Name**: `All 4 Starters Bundle (Save 28%)`
2. **URL slug**: `all-starters-bundle`
3. **Price**: $149 (fixed)
4. **Upload file**: `content/gumroad/zips/all-starters-bundle-v1.0-20260215.zip`
5. **Description**: Copy from `content/gumroad/GUMROAD_UPLOAD_MANIFEST.md` — the "All 4 Original Products - Starter Bundle" section
6. **Tags**: `bundle, starter-bundle, llm-orchestrator, rag-pipeline, web-scraper, data-dashboard, production-ready, python, mit-license, developer-tools, ai-development`
7. **Publish**

### All Pro Bundle
1. **Name**: `All 4 Pro Bundle (Save 31%)`
2. **URL slug**: `all-pro-bundle`
3. **Price**: $549 (fixed)
4. **Upload file**: `content/gumroad/zips/all-pro-bundle-v1.0-20260215.zip`
5. **Description**: Copy from manifest — "All 4 Original Products - Pro Bundle" section
6. **Tags**: `bundle, pro-bundle, llm-orchestrator, rag-pipeline, web-scraper, data-dashboard, production-ready, case-studies, consulting, priority-support, python, expert-guidance`
7. **Publish**

### Revenue-Sprint Bundle
(Already covered in Task 1 above)

---

## TASK 4: Cross-Link Related Products

After ALL products are published, go back and link related products:

### Within Each Product Family (Starter → Pro → Enterprise)
For each of the 7 product families, edit each tier and add "Related Products":

| Product | Starter links to | Pro links to | Enterprise links to |
|---------|-----------------|--------------|-------------------|
| AgentForge | Pro | Starter + Enterprise | Pro |
| DocQA | Pro | Starter + Enterprise | Pro |
| Scraper | Pro | Starter + Enterprise | Pro |
| Insight | Pro | Starter + Enterprise | Pro |
| Prompt Toolkit | Pro | Starter + Enterprise | Pro |
| LLM Starter Kit | Pro | Starter + Enterprise | Pro |
| Dashboard Templates | Pro | Starter + Enterprise | Pro |

### Bundle Cross-Links
- Each Starter product → Link to "All Starters Bundle"
- Each Pro product → Link to "All Pro Bundle"
- Revenue-Sprint Starters → Link to "Revenue-Sprint Bundle"

**How to add related products**: Edit Product → scroll to "Related Products" or "Recommended Products" section → search and select

---

## TASK 5: Add Cover Images to All Products

### Priority: Revenue-Sprint Products First

Each product needs a cover image. Options in order of preference:

**Option A (Best): Screenshot of Live Streamlit App**
1. Navigate to the live demo URL in Chrome
2. Take a clean screenshot (1280x720 minimum)
3. Upload as the product cover image

| Product | Screenshot Source |
|---------|-----------------|
| Prompt Toolkit | https://ct-prompt-lab.streamlit.app/ |
| LLM Starter Kit | https://ct-llm-starter.streamlit.app/ |
| Dashboard Templates | Any Streamlit app showing charts |
| AgentForge | https://ai-orchest-7mnwp9untg7gyyvchzevid.streamlit.app/ |
| DocQA Engine | https://ct-document-engine.streamlit.app/ |
| Scraper | N/A (no live demo) |
| Insight Engine | N/A (no live demo) |
| Bundles | Composite of individual screenshots |

**Option B: Existing AgentForge Screenshots**
For AgentForge specifically, 7 screenshots already exist at `content/gumroad/screenshots/agentforge/`

**Option C: Simple Text-Based Cover**
If no screenshot is possible, create a simple cover using Canva (free) or any image tool:
- 1280x720px
- Dark gradient background (navy → dark purple)
- Product name in large white text
- 2-3 key metrics as badges ("550+ Tests", "$49", "MIT License")
- Tech stack icons if possible (Python, Docker logos)

### Products Without Live Demos
For Scraper and Insight Engine (no live Streamlit demos), use Option C or take screenshots of the code/documentation.

---

## TASK 6: Configure Gumroad Settings

### Email Delivery Setup
For each product, verify that the automatic email delivery is configured:
1. Product → Edit → scroll to "Content" section
2. Ensure ZIP is attached and will be delivered on purchase
3. Gumroad auto-delivers digital products — verify this is enabled

### Refund Policy
1. Go to Settings → Payments
2. Set refund window to 30 days (matching our guarantee)
3. This should be account-level, applying to all products

### Affiliate Program (Optional but Recommended)
1. Go to Settings → Affiliates
2. Enable affiliate program
3. Set commission rate: 20%
4. This allows others to promote your products for a commission

### Tax Settings
1. Go to Settings → Tax
2. Verify tax collection is enabled for applicable regions
3. Gumroad handles tax collection automatically in most cases

---

## TASK 7: Post-Upload Verification Checklist

After ALL products are uploaded, verify each one:

### Per-Product Verification (do for all 21)
- [ ] Open product page in **incognito browser**
- [ ] Verify price displays correctly
- [ ] Verify description renders properly (Markdown formatting)
- [ ] Verify "Buy" button is visible and clickable
- [ ] Verify product URL matches the slug you set
- [ ] Verify tags are showing (check "Discover" page)
- [ ] Verify cover image displays correctly (not stretched/cropped)
- [ ] Verify related products show at bottom

### Bundle Verification
- [ ] All Starters Bundle shows correct $149 price and 28% savings
- [ ] All Pro Bundle shows correct $549 price and 31% savings
- [ ] Revenue-Sprint Bundle shows correct $99 price and 16% savings

### Account-Level Verification
- [ ] Profile page (gumroad.com/caymanroden) shows all products
- [ ] Products appear in Gumroad Discover (may take 24-48 hours)
- [ ] Test purchase works (use Gumroad test mode or a $1 test)

---

## COMPLETE PRODUCT REFERENCE TABLE

| # | Product | Tier | Price | PWYW? | URL Slug | ZIP File | Listing File |
|---|---------|------|-------|-------|----------|----------|-------------|
| 1 | Prompt Toolkit | Starter | $29 | No | prompt-toolkit-starter | prompt-toolkit-starter-v1.0-20260214.zip | revenue-sprint-1-prompt-toolkit-LISTING.md |
| 2 | Prompt Toolkit | Pro | $79 | No | prompt-toolkit-pro | prompt-toolkit-pro-v1.0-20260214.zip | revenue-sprint-1-prompt-toolkit-LISTING.md |
| 3 | Prompt Toolkit | Enterprise | $199 | No | prompt-toolkit-enterprise | prompt-toolkit-enterprise-v1.0-20260214.zip | revenue-sprint-1-prompt-toolkit-LISTING.md |
| 4 | LLM Starter Kit | Starter | $39 | No | llm-starter-kit | llm-starter-starter-v1.0-20260214.zip | revenue-sprint-2-llm-starter-LISTING.md |
| 5 | LLM Starter Kit | Pro | $99 | No | llm-starter-kit-pro | llm-starter-pro-v1.0-20260214.zip | revenue-sprint-2-llm-starter-LISTING.md |
| 6 | LLM Starter Kit | Enterprise | $249 | No | llm-starter-kit-enterprise | llm-starter-enterprise-v1.0-20260214.zip | revenue-sprint-2-llm-starter-LISTING.md |
| 7 | Dashboard Templates | Starter | $49 | No | dashboard-templates-starter | dashboard-starter-v1.0-20260214.zip | revenue-sprint-3-dashboard-templates-LISTING.md |
| 8 | Dashboard Templates | Pro | $99 | No | dashboard-templates-pro | dashboard-pro-v1.0-20260214.zip | revenue-sprint-3-dashboard-templates-LISTING.md |
| 9 | Dashboard Templates | Enterprise | $249 | No | dashboard-templates-enterprise | dashboard-enterprise-v1.0-20260214.zip | revenue-sprint-3-dashboard-templates-LISTING.md |
| 10 | AgentForge | Starter | $49 | **Yes** (min $49) | agentforge-starter | agentforge-starter-v1.0-20260214.zip | agentforge-starter-LISTING.md |
| 11 | AgentForge | Pro | $199 | No | agentforge-pro | agentforge-pro-v1.0-20260214.zip | agentforge-pro-LISTING.md |
| 12 | AgentForge | Enterprise | $999 | No | agentforge-enterprise | agentforge-enterprise-v1.0-20260214.zip | agentforge-enterprise-LISTING.md |
| 13 | DocQA Engine | Starter | $59 | **Yes** (min $59) | docqa-starter | docqa-starter-v1.0-20260214.zip | docqa-starter-LISTING.md |
| 14 | DocQA Engine | Pro | $249 | No | docqa-pro | docqa-pro-v1.0-20260214.zip | docqa-pro-LISTING.md |
| 15 | DocQA Engine | Enterprise | $1,499 | No | docqa-enterprise | docqa-enterprise-v1.0-20260214.zip | docqa-enterprise-LISTING.md |
| 16 | Scraper | Starter | $49 | **Yes** (min $49) | scraper-starter | scraper-starter-v1.0-20260214.zip | scraper-starter-LISTING.md |
| 17 | Scraper | Pro | $149 | No | scraper-pro | scraper-pro-v1.0-20260214.zip | scraper-pro-LISTING.md |
| 18 | Scraper | Enterprise | $699 | No | scraper-enterprise | scraper-enterprise-v1.0-20260214.zip | scraper-enterprise-LISTING.md |
| 19 | Insight Engine | Starter | $49 | **Yes** (min $49) | insight-starter | insight-starter-v1.0-20260214.zip | insight-starter-LISTING.md |
| 20 | Insight Engine | Pro | $199 | No | insight-pro | insight-pro-v1.0-20260214.zip | insight-pro-LISTING.md |
| 21 | Insight Engine | Enterprise | $999 | No | insight-enterprise | insight-enterprise-v1.0-20260214.zip | insight-enterprise-LISTING.md |
| B1 | Revenue-Sprint Bundle | — | $99 | No | revenue-sprint-bundle | revenue-sprint-bundle-v1.0-20260215.zip | GUMROAD_UPLOAD_MANIFEST.md |
| B2 | All Starters Bundle | — | $149 | No | all-starters-bundle | all-starters-bundle-v1.0-20260215.zip | GUMROAD_UPLOAD_MANIFEST.md |
| B3 | All Pro Bundle | — | $549 | No | all-pro-bundle | all-pro-bundle-v1.0-20260215.zip | GUMROAD_UPLOAD_MANIFEST.md |

---

## FILE LOCATIONS REFERENCE

All files are relative to the project root: `/Users/cave/Documents/GitHub/EnterpriseHub/`

```
content/gumroad/
├── GEMINI_GUMROAD_COMPLETION_SPEC.md          ← THIS FILE
├── GUMROAD_UPLOAD_MANIFEST.md                 ← Master inventory (full descriptions)
├── LISTING_AUDIT_REPORT.md                    ← Quality audit with improvements
├── REPRICING-STRATEGY.md                      ← Pricing rationale
├── UPLOAD-READINESS-SUMMARY.md                ← AgentForge-specific readiness
├── GUMROAD-UPLOAD-CHECKLIST.md                ← Detailed AgentForge upload steps
├── BUNDLE_LISTINGS.md                         ← Bundle product descriptions
├── SEO_OPTIMIZATION.md                        ← SEO best practices
├── bank-setup-checklist.md                    ← Payment setup guide
├── email-sequence-starter-to-pro.md           ← Upsell email template
├── email-sequence-pro-to-enterprise.md        ← Upsell email template
├── package-zips.sh                            ← ZIP packaging script
│
├── agentforge-starter-LISTING.md              ← Product listing copy
├── agentforge-pro-LISTING.md
├── agentforge-enterprise-LISTING.md
├── agentforge-COMPARISON-TABLE.md
├── agentforge-3tier-IMPLEMENTATION.md
├── docqa-starter-LISTING.md
├── docqa-pro-LISTING.md
├── docqa-enterprise-LISTING.md
├── scraper-starter-LISTING.md
├── scraper-pro-LISTING.md
├── scraper-enterprise-LISTING.md
├── insight-starter-LISTING.md
├── insight-pro-LISTING.md
├── insight-enterprise-LISTING.md
├── revenue-sprint-1-prompt-toolkit-LISTING.md
├── revenue-sprint-2-llm-starter-LISTING.md
├── revenue-sprint-3-dashboard-templates-LISTING.md
│
├── zips/                                      ← All 24 ZIP files ready to upload
│   ├── agentforge-starter-v1.0-20260214.zip
│   ├── agentforge-pro-v1.0-20260214.zip
│   ├── ... (24 total)
│
├── screenshots/agentforge/                    ← 7 product screenshots
│
├── supporting-files/                          ← Pro/Enterprise support files
│   ├── CONSULTATION_BOOKING.txt
│   ├── PRIORITY_SUPPORT.txt
│   ├── ENTERPRISE_KICKOFF.txt
│   ├── CUSTOM_EXAMPLES_FORM.txt
│   ├── WHITE_LABEL_LICENSE.txt
│   ├── SLACK_INVITE.txt
│   └── TEAM_TRAINING.txt
│
└── pro-content/                               ← 14 case study files
    ├── agentforge-case-study-fintech.md
    ├── agentforge-case-study-healthcare.md
    ├── agentforge-case-study-legaltech.md
    ├── agentforge-optimization-guide.md
    ├── docqa-case-study-financial.md
    ├── docqa-case-study-healthcare.md
    ├── docqa-case-study-legal.md
    ├── docqa-rag-optimization-guide.md
    ├── insight-case-study-ecommerce.md
    ├── insight-case-study-marketing.md
    ├── insight-case-study-saas.md
    ├── insight-advanced-analytics-guide.md
    ├── scraper-case-study-ecommerce.md
    ├── scraper-case-study-realestate.md
    └── scraper-proxy-rotation-guide.md
```

---

## IMPORTANT NOTES & GOTCHAS

### Gumroad-Specific Behaviors
1. **"Publish and continue" fails silently** if payment method is not configured. It shows a red toast error that disappears quickly. Always verify payment setup FIRST.
2. **Markdown in descriptions**: Gumroad supports basic Markdown (headings, bold, lists, code blocks). Test formatting after first publish.
3. **URL slugs are permanent**: Once published, the slug cannot be changed without creating a new product. Double-check before publishing.
4. **Tags affect discoverability**: Maximum 15 tags per product. Use the exact tags specified in this doc — they've been SEO-optimized.
5. **Cover images**: Gumroad crops to 16:9 aspect ratio. Use 1280x720 or 1600x900 for best results.
6. **Pay-what-you-want**: Only enable for Starter tiers of the 4 original products. Revenue-Sprint and all Pro/Enterprise tiers should be fixed price.

### Content Editor Warning
7. **Gumroad uses a rich text editor** (similar to ProseMirror/Tiptap). Pasting Markdown directly may or may not render correctly:
   - **Best approach**: Paste plain text, then use Gumroad's editor toolbar to format headings, bold, lists
   - **Alternative**: If Gumroad has a Markdown toggle, enable it before pasting
   - **Test**: After pasting, preview the product page to verify formatting

### Ordering
8. **Upload Revenue-Sprint first** (Task 1) — these are simpler products with faster time-to-sale
9. **Upload bundles after all individual products** — bundles reference individual products

### Existing Products
10. If there are **existing products at old prices** ($29-$49 single tier):
    - Do NOT delete them (preserves any existing sales/reviews)
    - Unpublish them (set to draft)
    - Create new products with new 3-tier pricing
    - If the old products have the same URL slug, add "-legacy" suffix to old ones

---

## PRIORITY ORDER (Execute Top to Bottom)

1. **Prerequisite checks** (Check 1-3 above) — 10 min
2. **Task 1**: Revenue-Sprint products (9 listings + 1 bundle) — 90 min
3. **Task 5**: Cover images for Revenue-Sprint — 30 min
4. **Task 2**: Original products (12 listings) — 90 min
5. **Task 5**: Cover images for original products — 30 min
6. **Task 3**: Remaining bundles (2 bundles) — 20 min
7. **Task 4**: Cross-link all related products — 30 min
8. **Task 6**: Configure Gumroad settings — 15 min
9. **Task 7**: Verification checklist — 30 min

**Total estimated time: 5-6 hours**

---

## REVENUE PROJECTIONS

### If All 21 Products Published This Week

| Timeframe | Conservative | Optimistic |
|-----------|-------------|------------|
| Week 1 | $147-$444 | $500-$1,000 |
| Month 1 | $2,086-$3,728 | $5,000-$8,000 |
| Month 3 | $10,450 | $15,000-$20,000 |
| Annual | $75,000-$125,000 | $125,000-$200,000 |

### Revenue by Product Category

| Category | Products | Price Range | Annual Potential |
|----------|----------|-------------|-----------------|
| AgentForge | 3 tiers | $49-$999 | $24K-$60K |
| DocQA Engine | 3 tiers | $59-$1,499 | $15K-$50K |
| Scraper | 3 tiers | $49-$699 | $8K-$20K |
| Insight Engine | 3 tiers | $49-$999 | $12K-$30K |
| Revenue-Sprint (3) | 9 tiers | $29-$249 | $10K-$25K |
| Bundles (3) | — | $99-$549 | $6K-$15K |

---

## VERIFICATION CHECKLIST (Final)

After completing all tasks, verify:

- [ ] Payment method confirmed in Gumroad settings
- [ ] All 21 products published and visible
- [ ] All 3 bundles published and visible
- [ ] Cover images on all products (at least Revenue-Sprint + original Starters)
- [ ] FAQ sections added to at least all Starter tiers
- [ ] Related products linked between tiers
- [ ] All URL slugs match the spec
- [ ] All prices correct (check the reference table above)
- [ ] PWYW enabled ONLY on original 4 Starter tiers
- [ ] Product pages render correctly in incognito browser
- [ ] Profile page shows all products
- [ ] Test download works on at least 1 product
- [ ] No old products at conflicting prices still published

---

**END OF SPEC**
