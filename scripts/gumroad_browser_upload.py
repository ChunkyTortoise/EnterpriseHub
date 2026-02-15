import os
import time
from playwright.sync_api import sync_playwright

# Data from manifest
PRODUCTS = [
    {
        "name": "AI Prompt Studio - Starter",
        "price": "29",
        "description": "8 battle-tested prompt patterns, template manager, and token counter. Includes 190 automated tests. Compatible with Claude, GPT, and Gemini.",
        "url": "ai-prompt-studio-starter"
    },
    {
        "name": "AI Prompt Studio - Pro",
        "price": "79",
        "description": "Everything in Starter plus A/B testing, cost optimizer, prompt versioning, safety checker, and evaluation metrics.",
        "url": "ai-prompt-studio-pro"
    },
    {
        "name": "AI Prompt Studio - Enterprise",
        "price": "199",
        "description": "Full Pro version plus benchmark runner, report generator, Docker deployment, and CI/CD templates. Includes 30-day priority support.",
        "url": "ai-prompt-studio-enterprise"
    },
    {
        "name": "LLM Integration Framework - Starter",
        "price": "39",
        "description": "Ship your first LLM integration in hours. Claude, GPT, Gemini client + streaming + function calling + RAG + cost tracking.",
        "url": "llm-integration-framework-starter"
    },
    {
        "name": "LLM Integration Framework - Pro",
        "price": "99",
        "description": "Everything in Starter + retry with backoff, circuit breaker, response caching, batch processor, guardrails + latency tracking.",
        "url": "llm-integration-framework-pro"
    },
    {
        "name": "LLM Integration Framework - Enterprise",
        "price": "249",
        "description": "Full Pro + multi-provider orchestration, observability pipeline, mock LLM, Docker/K8s deployment + 30-day priority support.",
        "url": "llm-integration-framework-enterprise"
    },
    {
        "name": "Analytics Dashboard Framework - Starter",
        "price": "49",
        "description": "Upload CSV/Excel, get interactive dashboards in 30 seconds. Auto-profiling, visualizations, data cleaning. 520+ tests.",
        "url": "analytics-dashboard-framework-starter"
    },
    {
        "name": "Analytics Dashboard Framework - Pro",
        "price": "99",
        "description": "Everything in Starter + predictive analytics, anomaly detection, time-series forecasting, clustering + advanced visualizations.",
        "url": "analytics-dashboard-framework-pro"
    },
    {
        "name": "Analytics Dashboard Framework - Enterprise",
        "price": "249",
        "description": "Full Pro + real-time streaming, database connectors, custom dashboards + Docker/K8s + 30-day priority support.",
        "url": "analytics-dashboard-framework-enterprise"
    }
]

def run():
    print("🚀 Launching Browser Automation for Gumroad Upload...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context()
        page = context.new_page()
        
        print("Navigate to Gumroad login...")
        page.goto("https://app.gumroad.com/login")
        
        print("⚠️  PLEASE LOG IN MANUALLY IN THE BROWSER WINDOW.")
        print("Waiting for login (checking for 'dashboard' or 'products' in URL)...")
        
        # Wait up to 5 minutes for login
        try:
            # Gumroad dashboard URL usually contains /dashboard or /products
            page.wait_for_url(lambda url: "dashboard" in url or "products" in url, timeout=300000) 
            print("✅ Login detected!")
        except Exception as e:
            print(f"❌ Login wait failed: {e}")
            print("Trying to proceed anyway...")
            
        for product in PRODUCTS:
            try:
                print(f"➕ Creating product: {product['name']}")
                page.goto("https://app.gumroad.com/products/new")
                
                # Fill Name
                page.wait_for_selector('input[name="name"]')
                page.fill('input[name="name"]', product['name'])
                
                # Select Type (Classic Digital Product)
                # Usually it's the first radio/card
                try:
                    page.click('input[value="digital_product"]')
                except:
                    # Fallback to clicking the first card if radio not found
                    page.click('div[class*="product-type-card"]:first-child') 
                
                # Price
                page.fill('input[name="price"]', product['price'])
                
                # Next / Customize
                page.click('button:has-text("Next: Customize")')
                
                # Wait for the next page to load
                page.wait_for_selector('div[contenteditable="true"]', timeout=10000)
                
                # Description
                print(f"  📝 Filling description for {product['name']}...")
                page.fill('div[contenteditable="true"]', product['description'])

                # URL / Permalink
                try:
                    page.fill('input[name="permalink"]', product['url'])
                except:
                    pass

                # Save / Publish
                print(f"  🚀 Publishing {product['name']}...")
                page.click('button:has-text("Publish")')
                
                print(f"  ✅ Finished: {product['name']}")
                time.sleep(3)
            except Exception as e:
                print(f"  ❌ Error creating {product['name']}: {e}")
                print("Continuing to next product...")

        print("\n🎉 Phase 1 Batch Complete.")
        print("The browser will remain open for 60 seconds for you to inspect.")
        time.sleep(60)
        browser.close()

if __name__ == "__main__":
    run()
