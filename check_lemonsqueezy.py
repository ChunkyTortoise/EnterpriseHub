
import asyncio
from playwright.async_api import async_playwright

async def check_status():
    email = "caymanroden@gmail.com"
    password = "LemonSqueezy2026!#"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            print("Navigating to login...")
            await page.goto("https://app.lemonsqueezy.com/login", timeout=60000)
            
            print("Typing credentials...")
            await page.wait_for_selector("input[name='email']", timeout=10000)
            await page.fill("input[name='email']", email)
            await page.fill("input[name='password']", password)
            await page.click("button[type='submit']")
            
            print("Waiting for dashboard...")
            await page.wait_for_url("**/dashboard", timeout=30000)
            
            # Check for activation status
            print("Checking activation status...")
            content = await page.content()
            inner_text = await page.inner_text('body')
            
            if "Activate your store" in inner_text or "Fill out your business details" in inner_text:
                print("Store still needs activation/business details.")
            else:
                print("Store appears to be moving towards activation or is activated.")
            
            # Check for identity verification status specifically if possible
            await page.goto("https://app.lemonsqueezy.com/settings/general", timeout=60000)
            settings_text = await page.inner_text('body')
            if "Identity verification" in settings_text:
                print("Identity verification section found.")
                # We could click it but let's just see what's on the main settings page
            
            await page.screenshot(path="lemonsqueezy_current_status.png")
            print("Screenshot saved: lemonsqueezy_current_status.png")
                
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="lemonsqueezy_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_status())
