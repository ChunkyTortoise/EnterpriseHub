"""PeoplePerHour Account Creation Agent"""

import asyncio
from typing import Dict
from .base_agent import BaseAgent


class PeoplePerHourAgent(BaseAgent):
    """Specialized agent for PeoplePerHour account creation."""

    def __init__(self, profile: Dict):
        super().__init__(profile, "peopleperhour")
        self.signup_url = "https://www.peopleperhour.com/join"

    async def create_account(self) -> Dict:
        """Create PeoplePerHour account."""
        try:
            await self.setup_browser(headless=False)
            print(f"🎯 [{self.platform_name.upper()}] Starting registration...")

            await self.page.goto(self.signup_url)
            await self.human_delay(2, 3)

            # Click "I want to work"
            await self.page.click('text="I want to work"')
            await self.human_delay(1, 2)

            # Fill form
            await self.type_human('input[type="email"]', self.profile["email"])
            await self.type_human('input[type="password"]', self.profile["password"])
            await self.page.click('input[name="terms"]')  # Accept terms

            if await self.page.query_selector('iframe[src*="recaptcha"]'):
                await self.wait_for_captcha()

            await self.page.click('button[type="submit"]')
            await self.human_delay(3, 5)

            if "verify" in self.page.url.lower():
                return {"status": "pending_verification", "verification_type": "email"}
            else:
                return {"status": "success"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            await asyncio.sleep(300)
            await self.close()
