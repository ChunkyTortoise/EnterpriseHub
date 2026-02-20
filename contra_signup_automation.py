
import asyncio
import os
import secrets
import string

from playwright.async_api import async_playwright


async def run():
    email = "caymanroden@gmail.com"
    # Generate a random password
    alphabet = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(secrets.choice(alphabet) for i in range(16))
    
    print(f"Attempting signup for {email}...")
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # 1. Navigate to home and find signup
            print("Navigating to https://contra.com...")
            await page.goto("https://contra.com", wait_until="networkidle", timeout=60000)
            await page.wait_for_timeout(3000)
            
            # Find and click "Sign Up" button
            # Based on 404 page dump: <button type="button" variant="V2Primary" class="Buttonstyles__StyledButton-sc-w63a17-0 iRgQcN"><span class="ButtonContainerstyles__StyledButtonContainer-sc-e8rsx8-0 bvRzws"><span textstyle="text-base-medium" variant="V2Primary" class="Text-sc-1k5lnf-0 ButtonTextstyles__StyledButtonText-sc-1smg0pq-0 gDtfPS cUjFSt">Sign Up</span></span></button>
            signup_btn = page.get_by_role("button", name="Sign Up").first
            if await signup_btn.is_visible():
                print("Clicking 'Sign Up' button...")
                await signup_btn.click()
                await page.wait_for_timeout(5000)
            else:
                print("Sign Up button not found. Trying direct register URL...")
                await page.goto("https://contra.com/onboarding", wait_until="networkidle")
                await page.wait_for_timeout(3000)

            # 2. Look for email input
            print("Searching for email input...")
            # Try various selectors for email
            selectors = ["input[type='email']", "input[name='email']", "input[placeholder*='email']"]
            email_input = None
            for selector in selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        break
                except:
                    continue

            if email_input:
                print(f"Email input found via selector. Typing {email}...")
                await email_input.fill(email)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
            else:
                print("Email input not found. Checking for 'Continue with email'...")
                email_btn = page.get_by_text("Continue with email", exact=False)
                if await email_btn.is_visible():
                    await email_btn.click()
                    await page.wait_for_timeout(2000)
                    email_input = await page.wait_for_selector("input[type='email']", timeout=5000)
                    await email_input.fill(email)
                    await page.keyboard.press("Enter")
                else:
                    print("Could not find email entry point.")
                    await page.screenshot(path="contra_entry_fail.png")
                    return
            
            # 3. Check what happens next (Password or OTP)
            await page.wait_for_timeout(3000)
            content = await page.content()
            
            if "check your email" in content.lower() or "verify" in content.lower() or "code" in content.lower():
                print("!!! Email verification (OTP/Link) required. Stopping.")
                await page.screenshot(path="contra_verification_required.png")
                print("Screenshot saved: contra_verification_required.png")
                # We save the generated password just in case we need it later if it was set
                with open("contra_generated_password.txt", "w") as f:
                    f.write(password)
                return
            
            # 4. Look for password field if it exists
            password_input = await page.wait_for_selector("input[type='password']", timeout=5000)
            if password_input:
                print("Password input found. Setting password...")
                await password_input.fill(password)
                await page.keyboard.press("Enter")
                await page.wait_for_timeout(3000)
                
                # Check for profile setup fields
                print("Checking for profile setup fields...")
                await page.screenshot(path="contra_after_password.png")
                print("Screenshot saved: contra_after_password.png")
                
                with open("contra_generated_password.txt", "w") as f:
                    f.write(password)
                print(f"Generated password saved to contra_generated_password.txt")
            else:
                print("Password input not found. Maybe it's a passwordless/OTP flow.")
                await page.screenshot(path="contra_after_email.png")
                print("Screenshot saved: contra_after_email.png")

        except Exception as e:
            print(f"An error occurred: {e}")
            await page.screenshot(path="contra_signup_error.png")
            print("Screenshot saved: contra_signup_error.png")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(run())
