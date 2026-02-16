
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
            await page.goto("https://app.lemonsqueezy.com/login", wait_until="networkidle")
            
            print("Typing credentials...")
            await page.fill("input[name='email']", email)
            await page.fill("input[name='password']", password)
            await page.click("button[type='submit']")
            
            await page.wait_for_timeout(5000)
            
            # Check if we are on dashboard or if there is a 2FA/Verification block
            url = page.url
            print(f"Current URL: {url}")
            
            content = await page.content()
            if "verify" in content.lower() or "code" in content.lower():
                print("Verification/2FA requested.")
                await page.screenshot(path="lemonsqueezy_verify.png")
            elif "dashboard" in url:
                print("Logged in successfully.")
                await page.screenshot(path="lemonsqueezy_dashboard.png")
                # Check for activation status
                if "activate" in content.lower():
                    print("Store still needs activation.")
                else:
                    print("Store appears activated.")
            else:
                print("Unknown state.")
                await page.screenshot(path="lemonsqueezy_unknown.png")
                
        except Exception as e:
            print(f"Error: {e}")
            await page.screenshot(path="lemonsqueezy_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(check_status())
