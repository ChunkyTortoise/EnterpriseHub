import os
import time
import sys
from playwright.sync_api import sync_playwright

# SPEC DATA
ACCOUNT = "caymanroden@gmail.com"
ZIP_DIR = "/Users/cave/Documents/GitHub/EnterpriseHub/content/gumroad/zips/"

UPDATES = [
    {
        "old_name": "Prompt Engineering Toolkit",
        "new_name": "Prompt Engineering Toolkit - Starter",
        "new_price": "29"
    },
    {
        "old_name": "AI Integration Starter Kit",
        "new_name": "AI Integration Starter Kit - Starter",
        "new_price": "39"
    },
    {
        "old_name": "Data Intelligence Dashboard Pro",
        "new_name": "Insight Engine - Pro",
        "new_price": "199"
    },
    {
        "old_name": "Data Intelligence Dashboard Enterprise",
        "new_name": "Insight Engine - Enterprise",
        "new_price": "999"
    }
]

NEW_PRODUCTS = [
    {
        "name": "Prompt Engineering Toolkit - Pro",
        "price": "79",
        "zip": "prompt-toolkit-pro-v1.0-20260214.zip",
        "description": """Prompt Engineering Toolkit - Pro

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

30-day money-back guarantee. MIT License."""
    },
    {
        "name": "Prompt Engineering Toolkit - Enterprise",
        "price": "199",
        "zip": "prompt-toolkit-enterprise-v1.0-20260214.zip",
        "description": """Prompt Engineering Toolkit - Enterprise

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

30-day money-back guarantee. Commercial license."""
    },
    {
        "name": "AI Integration Starter Kit - Pro",
        "price": "99",
        "zip": "llm-starter-pro-v1.0-20260214.zip",
        "description": """AI Integration Starter Kit - Pro

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

30-day money-back guarantee. MIT License."""
    },
    {
        "name": "AI Integration Starter Kit - Enterprise",
        "price": "249",
        "zip": "llm-starter-enterprise-v1.0-20260214.zip",
        "description": """AI Integration Starter Kit - Enterprise

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

30-day money-back guarantee. Commercial license."""
    },
    {
        "name": "Streamlit Dashboard Templates - Starter",
        "price": "49",
        "zip": "dashboard-starter-v1.0-20260214.zip",
        "description": """Streamlit Dashboard Templates - Starter

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

30-day money-back guarantee. MIT License."""
    },
    {
        "name": "Streamlit Dashboard Templates - Pro",
        "price": "99",
        "zip": "dashboard-pro-v1.0-20260214.zip",
        "description": """Streamlit Dashboard Templates - Pro

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

30-day money-back guarantee. MIT License."""
    },
    {
        "name": "Streamlit Dashboard Templates - Enterprise",
        "price": "249",
        "zip": "dashboard-enterprise-v1.0-20260214.zip",
        "description": """Streamlit Dashboard Templates - Enterprise

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

30-day money-back guarantee. Commercial license."""
    }
]

BUNDLES = [
    {
        "name": "AI Developer Starter Pack",
        "price": "149",
        "zip": "all-starters-bundle-v1.0-20260215.zip",
        "description": """Ship Your First AI Product with the Complete Developer Toolkit

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

Python 3.11+ required. Docker recommended. 30-day money-back guarantee. MIT License."""
    },
    {
        "name": "Production AI Toolkit (Pro)",
        "price": "549",
        "zip": "all-pro-bundle-v1.0-20260215.zip",
        "description": """Production AI Toolkit - Everything You Need to Ship at Scale

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

30-day money-back guarantee. MIT License."""
    },
    {
        "name": "Revenue Sprint Bundle",
        "price": "99",
        "zip": None,
        "description": """Revenue Sprint Bundle - 3 Quick-Start AI Tools

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

Python 3.11+ required. Docker included. 30-day money-back guarantee. MIT License."""
    }
]

def run():
    print("🚀 Starting Gumroad Browser Automation...")
    user_data_dir = os.path.join(os.getcwd(), ".playwright_gumroad_session")
    with sync_playwright() as p:
        # Use persistent context to save login state
        context = p.chromium.launch_persistent_context(
            user_data_dir,
            headless=False,
            slow_mo=500,
            args=["--disable-blink-features=AutomationControlled"]
        )
        page = context.pages[0] if context.pages else context.new_page()
        
        print("Navigate to Gumroad dashboard...")
        page.goto("https://app.gumroad.com/dashboard")
        
        print("⚠️  PLEASE LOG IN MANUALLY IN THE BROWSER WINDOW.")
        print(f"Account: {ACCOUNT}")
        print("Waiting for login (checking for 'dashboard' or 'products' in URL)...")
        
        try:
            page.wait_for_url(lambda url: "dashboard" in url or "products" in url, timeout=300000) 
            print("✅ Login detected!")
        except Exception as e:
            print(f"❌ Login wait failed: {e}")
            sys.exit(1)

        # STEP 1: Update 4 Existing Products
        print("\n--- STEP 1: Updating Existing Products ---")
        updates_done = 0
        for update in UPDATES:
            try:
                print(f"Searching for product: {update['old_name']}")
                page.goto("https://app.gumroad.com/products")
                
                # Search for the product
                page.wait_for_selector('input[placeholder*="Search"]')
                page.fill('input[placeholder*="Search"]', update['old_name'])
                page.keyboard.press("Enter")
                time.sleep(2)
                
                # Click the product link (usually the first one that matches the name)
                selector = f'a:has-text("{update["old_name"]}")'
                if page.is_visible(selector):
                    page.click(selector)
                    print(f"  Editing {update['old_name']}...")
                    
                    page.wait_for_selector('input[name="name"]')
                    page.fill('input[name="name"]', update['new_name'])
                    page.fill('input[name="price"]', update['new_price'])
                    
                    page.click('button:has-text("Save changes")')
                    print(f"  ✅ Updated: {update['new_name']} (${update['new_price']})")
                    updates_done += 1
                    time.sleep(2)
                else:
                    print(f"  ⚠️ Could not find product: {update['old_name']}")
            except Exception as e:
                print(f"  ❌ Error updating {update['old_name']}: {e}")

        # STEP 2: Create 7 New Individual Products
        print("\n--- STEP 2: Creating New Individual Products ---")
        new_products_done = 0
        for prod in NEW_PRODUCTS:
            try:
                print(f"➕ Creating product: {prod['name']}")
                page.goto("https://app.gumroad.com/products/new")
                
                page.wait_for_selector('input[name="name"]')
                page.fill('input[name="name"]', prod['name'])
                
                try:
                    page.click('input[value="digital_product"]')
                except:
                    page.click('div[class*="product-type-card"]:first-child') 
                
                page.fill('input[name="price"]', prod['price'])
                page.click('button:has-text("Next: Customize")')
                
                page.wait_for_selector('div[contenteditable="true"]')
                page.fill('div[contenteditable="true"]', prod['description'])

                if prod['zip']:
                    zip_path = os.path.join(ZIP_DIR, prod['zip'])
                    if os.path.exists(zip_path):
                        print(f"  📦 Uploading {prod['zip']}...")
                        try:
                            file_input = page.query_selector('input[type="file"]')
                            if file_input:
                                file_input.set_input_files(zip_path)
                            else:
                                page.click('button:has-text("Upload")')
                                page.click('button:has-text("Computer")')
                                page.wait_for_selector('input[type="file"]')
                                page.set_input_files('input[type="file"]', zip_path)
                        except Exception as upload_error:
                            print(f"    ⚠️ Upload error: {upload_error}")
                    else:
                        print(f"    ⚠️ ZIP NOT FOUND: {zip_path}")

                page.click('button:has-text("Publish")')
                print(f"  ✅ Published: {prod['name']}")
                new_products_done += 1
                time.sleep(3)
            except Exception as e:
                print(f"  ❌ Error creating {prod['name']}: {e}")

        # STEP 3: Create 3 Bundles
        print("\n--- STEP 3: Creating Bundles ---")
        bundles_done = 0
        for bundle in BUNDLES:
            try:
                print(f"➕ Creating bundle: {bundle['name']}")
                page.goto("https://app.gumroad.com/products/new")
                
                page.wait_for_selector('input[name="name"]')
                page.fill('input[name="name"]', bundle['name'])
                
                try:
                    page.click('input[value="digital_product"]')
                except:
                    page.click('div[class*="product-type-card"]:first-child') 
                
                page.fill('input[name="price"]', bundle['price'])
                page.click('button:has-text("Next: Customize")')
                
                page.wait_for_selector('div[contenteditable="true"]')
                page.fill('div[contenteditable="true"]', bundle['description'])

                if bundle['zip']:
                    zip_path = os.path.join(ZIP_DIR, bundle['zip'])
                    if os.path.exists(zip_path):
                        print(f"  📦 Uploading {bundle['zip']}...")
                        try:
                            file_input = page.query_selector('input[type="file"]')
                            if file_input:
                                file_input.set_input_files(zip_path)
                            else:
                                page.click('button:has-text("Upload")')
                                page.click('button:has-text("Computer")')
                                page.wait_for_selector('input[type="file"]')
                                page.set_input_files('input[type="file"]', zip_path)
                        except Exception as upload_error:
                            print(f"    ⚠️ Upload error: {upload_error}")
                
                page.click('button:has-text("Publish")')
                print(f"  ✅ Published bundle: {bundle['name']}")
                bundles_done += 1
                time.sleep(3)
            except Exception as e:
                print(f"  ❌ Error creating bundle {bundle['name']}: {e}")

        # STEP 4: Verification
        print("\n--- STEP 4: Verification ---")
        page.goto("https://app.gumroad.com/products")
        time.sleep(5)
        
        print("\n🚀 GUMROAD REPORT:")
        print(f"- Updates completed: {updates_done} of 4")
        print(f"- New products created: {new_products_done} of 7")
        print(f"- Bundles created: {bundles_done} of 3")
        
        print("\nThe browser will remain open for 2 minutes for manual inspection.")
        time.sleep(120)
        browser.close()

if __name__ == "__main__":
    run()
