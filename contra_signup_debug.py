
import asyncio

from playwright.async_api import async_playwright


async def run():
    email = "caymanroden@gmail.com"
    print(f"Starting fresh signup attempt for {email}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a realistic user agent and window size
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Home Page
            print("Step 1: Navigating to https://contra.com...")
            await page.goto("https://contra.com", wait_until="networkidle")
            await page.screenshot(path="debug_1_home.png")
            
            # 2. Click Sign Up
            print("Step 2: Locating Sign Up button...")
            # Try finding the button by text specifically in the header
            signup_btn = page.get_by_role("button", name="Sign Up").first
            if not await signup_btn.is_visible():
                 signup_btn = page.locator("button:has-text('Sign Up')").first
            
            if await signup_btn.is_visible():
                print("Clicking 'Sign Up'...")
                await signup_btn.click()
                await page.wait_for_timeout(5000)
                await page.screenshot(path="debug_2_after_click.png")
            else:
                print("Sign Up button not found visually, trying direct navigation to onboarding...")
                await page.goto("https://contra.com/onboarding", wait_until="networkidle")
                await page.wait_for_timeout(3000)
                await page.screenshot(path="debug_2_onboarding_direct.png")

            # 3. Enter Email
            print("Step 3: Searching for email input...")
            # Check for "Continue with email" button first (common in modern auth)
            continue_email = page.get_by_text("Continue with email", exact=False)
            if await continue_email.is_visible():
                print("Clicking 'Continue with email'...")
                await continue_email.click()
                await page.wait_for_timeout(2000)

            selectors = ["input[type='email']", "input[name='email']", "input[placeholder*='email']", "input[aria-label*='email']"]
            email_input = None
            for selector in selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=3000)
                    if email_input:
                        print(f"Found input via {selector}")
                        break
                except:
                    continue

            if email_input:
                await email_input.fill(email)
                await page.screenshot(path="debug_3_email_filled.png")
                await page.keyboard.press("Enter")
                print("Email submitted.")
                await page.wait_for_timeout(5000)
                await page.screenshot(path="debug_4_final_state.png")
                
                content = await page.content()
                if "code" in content.lower() or "verify" in content.lower() or "sent" in content.lower():
                    print("SUCCESS: Verification screen reached.")
                    # Look for the email mentioned on page to confirm
                    if email in content:
                        print(f"Confirmed: Code sent to {email}")
                    
                    # Check for resend button
                    resend = page.get_by_text("Resend", exact=False)
                    if await resend.is_visible():
                        print("Resend button is available.")
                else:
                    print("Reached final state but verification text not found.")
                    print(f"URL: {page.url}")
            else:
                print("FAILED: Could not find email input field.")
                
        except Exception as e:
            print(f"ERROR: {e}")
            await page.screenshot(path="debug_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
