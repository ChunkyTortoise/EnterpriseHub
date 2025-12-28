"""
Fiverr Account Creation Agent
Automates seller account setup on Fiverr.com
"""

from typing import Dict
from .base_agent import BaseAgent


class FiverrAgent(BaseAgent):
    """Specialized agent for Fiverr account creation."""

    def __init__(self, profile: Dict):
        super().__init__(profile, "fiverr")
        self.signup_url = "https://www.fiverr.com/start_selling"

    async def create_account(self) -> Dict:
        """Create Fiverr seller account."""
        try:
            await self.setup_browser(headless=False)  # Visible for CAPTCHA solving

            print(f"🎯 [{self.platform_name.upper()}] Starting account creation...")

            # Step 1: Navigate to signup page
            print(f"📍 [{self.platform_name.upper()}] Loading signup page...")
            await self.page.goto(self.signup_url)
            await self.human_delay(2, 4)
            await self.screenshot("01_landing_page")

            # Step 2: Check if already logged in or account exists
            if await self.page.query_selector('text="Dashboard"'):
                return {
                    "status": "error",
                    "error": "Already logged in or account exists",
                }

            # Step 3: Click "Join" or "Sign Up" button
            try:
                await self.page.click('text="Join"', timeout=5000)
            except:
                await self.page.click('a:has-text("Sign Up")', timeout=5000)

            await self.human_delay(1, 2)
            await self.screenshot("02_signup_form")

            # Step 4: Fill email
            print(f"✍️  [{self.platform_name.upper()}] Entering email...")
            await self.type_human('input[name="email"]', self.profile["email"])
            await self.human_delay(0.5, 1)

            # Step 5: Choose "Continue with Email" if present
            try:
                await self.page.click('button:has-text("Continue with Email")', timeout=3000)
                await self.human_delay(1, 2)
            except:
                pass

            # Step 6: Fill username (if separate field)
            try:
                print(f"✍️  [{self.platform_name.upper()}] Entering username...")
                await self.type_human('input[name="username"]', self.profile["username"])
                await self.human_delay(0.5, 1)
            except:
                pass

            # Step 7: Fill password
            print(f"✍️  [{self.platform_name.upper()}] Entering password...")
            await self.type_human('input[name="password"]', self.profile["password"])
            await self.human_delay(0.5, 1)

            await self.screenshot("03_form_filled")

            # Step 8: Check for CAPTCHA
            captcha_selectors = [
                'iframe[src*="recaptcha"]',
                'div[class*="captcha"]',
                '#captcha',
            ]

            for selector in captcha_selectors:
                if await self.page.query_selector(selector):
                    await self.wait_for_captcha()
                    break

            # Step 9: Submit form
            print(f"📤 [{self.platform_name.upper()}] Submitting registration...")
            try:
                await self.page.click('button[type="submit"]', timeout=5000)
            except:
                await self.page.click('button:has-text("Join")', timeout=5000)

            await self.human_delay(3, 5)
            await self.screenshot("04_after_submit")

            # Step 10: Check for success (email verification page or dashboard)
            url = self.page.url
            if "email_verification" in url or "verify" in url.lower():
                print(f"📧 [{self.platform_name.upper()}] Email verification required")
                return {
                    "status": "pending_verification",
                    "verification_type": "email",
                    "message": "Check email for verification link",
                }

            elif "dashboard" in url or "seller_dashboard" in url:
                print(f"✅ [{self.platform_name.upper()}] Account created successfully!")
                return {
                    "status": "success",
                    "profile_url": f"https://www.fiverr.com/{self.profile['username']}",
                }

            else:
                # Unknown state - take screenshot for debugging
                await self.screenshot("05_unknown_state")
                return {
                    "status": "unknown",
                    "message": f"Unexpected page: {url}",
                }

        except Exception as e:
            await self.screenshot("error")
            print(f"❌ [{self.platform_name.upper()}] Error: {e}")
            return {
                "status": "error",
                "error": str(e),
            }

        finally:
            # Keep browser open for manual verification if needed
            print(f"⏸️  [{self.platform_name.upper()}] Browser left open for manual steps")
            print(f"   Close manually when done or press Ctrl+C")
            await asyncio.sleep(300)  # Wait 5 minutes
            await self.close()
