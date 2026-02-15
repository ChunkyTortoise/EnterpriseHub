from playwright.sync_api import sync_playwright
import time
import sys

def deploy_app(page, repo, branch, main_file, url_subdomain):
    print(f"Deploying {repo}...")
    page.goto("https://share.streamlit.io")
    time.sleep(3)
    
    # Click "New app"
    # The button might be "New app" or have an icon
    try:
        page.click("button:has-text('New app')")
    except:
        # Try another selector
        page.click("text=New app")
    
    time.sleep(2)
    
    # Select "Deploy an existing app" if prompted (sometimes there's a choice)
    # But usually it goes straight to the form
    
    # Fill Repository
    page.fill("input[placeholder='GitHub repository']", repo)
    time.sleep(1)
    
    # Fill Branch
    page.fill("input[placeholder='Main branch']", branch)
    time.sleep(1)
    
    # Fill Main file path
    page.fill("input[placeholder='Main file path']", main_file)
    time.sleep(1)
    
    # Click "Advanced settings" to set the URL if possible, 
    # but wait, the instructions say "App URL (custom subdomain)"
    # Usually there is an "App URL" field in the form.
    
    # Let's check for the URL field
    try:
        # Streamlit often has a "URL" field in the form now
        page.fill("input[placeholder='Your app URL']", url_subdomain)
    except:
        print(f"Warning: Could not find URL subdomain field for {repo}. Might need manual setting.")
    
    # Click Deploy
    page.click("button:has-text('Deploy!')")
    
    print(f"Waiting for deployment of {repo} to start...")
    time.sleep(10)
    
    # Screenshot the result
    page.screenshot(path=f"deploy_{url_subdomain}.png")
    print(f"Finished deployment steps for {repo}. Check deploy_{url_subdomain}.png")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Use a longer timeout for slow pages
        context = browser.new_context(viewport={'width': 1280, 'height': 800})
        page = context.new_page()
        
        # Initial login check/navigation
        page.goto("https://share.streamlit.io")
        time.sleep(5)
        
        if "login" in page.url or "github.com/login" in page.url:
            print("Error: Not logged in. Please ensure session is active.")
            browser.close()
            sys.exit(1)
            
        # App 1: Prompt Engineering Lab
        deploy_app(page, "ChunkyTortoise/prompt-engineering-lab", "main", "app.py", "ct-prompt-lab")
        
        # App 2: LLM Integration Starter
        deploy_app(page, "ChunkyTortoise/llm-integration-starter", "main", "app.py", "ct-llm-starter")
        
        # App 3: AgentForge
        deploy_app(page, "ChunkyTortoise/ai-orchestrator", "main", "streamlit_app.py", "ct-agentforge")
        
        browser.close()

if __name__ == "__main__":
    main()
