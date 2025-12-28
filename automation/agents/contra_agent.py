"""Contra Account Creation Agent"""

import asyncio
from typing import Dict
from .base_agent import BaseAgent


class ContraAgent(BaseAgent):
    """Specialized agent for Contra account creation."""

    def __init__(self, profile: Dict):
        super().__init__(profile, "contra")
        self.signup_url = "https://contra.com/signup"

    async def create_account(self) -> Dict:
        """Create Contra account (0% commission platform)."""
        try:
            await self.setup_browser(headless=False)
            print(f"🎯 [{self.platform_name.upper()}] Starting registration...")

            await self.page.goto(self.signup_url)
            await self.human_delay(2, 3)

            # Contra often uses social signup first - try email option
            try:
                await self.page.click('text="Continue with Email"')
                await self.human_delay(1, 2)
            except:
                pass

            await self.type_human('input[name="email"]', self.profile["email"])
            await self.type_human('input[name="full_name"]', self.profile["full_name"])
            await self.type_human('input[name="password"]', self.profile["password"])

            await self.page.click('button:has-text("Sign Up")')
            await self.human_delay(3, 5)

            if "onboarding" in self.page.url or "welcome" in self.page.url:
                return {"status": "success", "profile_url": f"https://contra.com/@{self.profile['username']}"}
            else:
                return {"status": "pending_verification", "verification_type": "email"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            await asyncio.sleep(300)
            await self.close()
