"""Freelancer.com Account Creation Agent"""

import asyncio
from typing import Dict
from .base_agent import BaseAgent


class FreelancerAgent(BaseAgent):
    """Specialized agent for Freelancer.com account creation."""

    def __init__(self, profile: Dict):
        super().__init__(profile, "freelancer")
        self.signup_url = "https://www.freelancer.com/get-started"

    async def create_account(self) -> Dict:
        """Create Freelancer.com account."""
        try:
            await self.setup_browser(headless=False)
            print(f"🎯 [{self.platform_name.upper()}] Starting registration...")

            await self.page.goto(self.signup_url)
            await self.human_delay(2, 3)
            await self.screenshot("01_landing")

            # Fill signup form
            await self.type_human('input[name="email"]', self.profile["email"])
            await self.human_delay(0.5, 1)

            await self.type_human('input[name="username"]', self.profile["username"])
            await self.human_delay(0.5, 1)

            await self.type_human('input[name="password"]', self.profile["password"])
            await self.human_delay(0.5, 1)

            await self.screenshot("02_form_filled")

            # Check for CAPTCHA
            if await self.page.query_selector('iframe[src*="recaptcha"]'):
                await self.wait_for_captcha()

            # Submit
            await self.page.click('button:has-text("Create My Account")')
            await self.human_delay(3, 5)
            await self.screenshot("03_after_submit")

            # Check result
            if "email-verification" in self.page.url:
                return {"status": "pending_verification", "verification_type": "email"}
            elif "dashboard" in self.page.url:
                return {"status": "success", "profile_url": f"https://www.freelancer.com/u/{self.profile['username']}"}
            else:
                return {"status": "unknown", "message": self.page.url}

        except Exception as e:
            await self.screenshot("error")
            return {"status": "error", "error": str(e)}
        finally:
            await asyncio.sleep(300)
            await self.close()
