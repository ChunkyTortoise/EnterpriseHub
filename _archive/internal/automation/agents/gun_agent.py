"""Gun.io Account Creation Agent"""

import asyncio
from typing import Dict
from .base_agent import BaseAgent


class GunAgent(BaseAgent):
    """Specialized agent for Gun.io account creation."""

    def __init__(self, profile: Dict):
        super().__init__(profile, "gun")
        self.signup_url = "https://gun.io/signup"

    async def create_account(self) -> Dict:
        """Create Gun.io account."""
        try:
            await self.setup_browser(headless=False)
            print(f"🎯 [{self.platform_name.upper()}] Starting registration...")

            await self.page.goto(self.signup_url)
            await self.human_delay(2, 3)

            # Gun.io has a developer application process
            await self.type_human('input[name="email"]', self.profile["email"])
            await self.type_human('input[name="first_name"]', self.profile["full_name"].split()[0])
            await self.type_human(
                'input[name="last_name"]', " ".join(self.profile["full_name"].split()[1:])
            )
            await self.type_human('input[name="github"]', self.profile["github"])

            await self.page.click('button:has-text("Apply")')
            await self.human_delay(3, 5)

            # Gun.io typically requires manual review
            if "application" in self.page.url or "thank" in self.page.url.lower():
                return {
                    "status": "pending_verification",
                    "verification_type": "manual_review",
                    "message": "Application submitted - Gun.io will review manually",
                }
            else:
                return {"status": "success"}

        except Exception as e:
            return {"status": "error", "error": str(e)}
        finally:
            await asyncio.sleep(300)
            await self.close()
