"""
Base Agent Class
Provides common functionality for all platform agents.
"""

import asyncio
import random
from pathlib import Path
from typing import Dict, Optional
from datetime import datetime

try:
    from playwright.async_api import async_playwright, Page, Browser
    from playwright_stealth import stealth_async

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  playwright not installed. Run: pip install playwright playwright-stealth")


class BaseAgent:
    """Base class for platform-specific account creation agents."""

    def __init__(self, profile: Dict, platform_name: str):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError("Playwright not available")

        self.profile = profile
        self.platform_name = platform_name
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshots_dir = Path(__file__).parent.parent / "screenshots" / platform_name
        self.screenshots_dir.mkdir(parents=True, exist_ok=True)

    async def setup_browser(self, headless: bool = False):
        """Initialize browser with stealth mode."""
        print(f"🌐 [{self.platform_name.upper()}] Setting up browser...")

        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )

        # Create context with realistic user agent
        context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )

        self.page = await context.new_page()

        # Apply stealth mode
        await stealth_async(self.page)

        print(f"✅ [{self.platform_name.upper()}] Browser ready")

    async def human_delay(self, min_sec: float = 1.0, max_sec: float = 3.0):
        """Simulate human-like delay."""
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)

    async def type_human(self, selector: str, text: str):
        """Type text with human-like delays."""
        await self.page.click(selector)
        await self.human_delay(0.2, 0.5)

        for char in text:
            await self.page.type(selector, char)
            await asyncio.sleep(random.uniform(0.05, 0.15))

    async def screenshot(self, name: str):
        """Take screenshot for debugging."""
        timestamp = datetime.now().strftime("%H%M%S")
        filepath = self.screenshots_dir / f"{timestamp}_{name}.png"
        await self.page.screenshot(path=str(filepath))
        print(f"📸 [{self.platform_name.upper()}] Screenshot: {filepath.name}")

    async def wait_for_captcha(self, timeout: int = 120):
        """Pause and wait for user to solve CAPTCHA."""
        print(f"\n⏸️  [{self.platform_name.upper()}] CAPTCHA DETECTED")
        print("   Please solve the CAPTCHA in the browser window.")
        print(f"   Waiting up to {timeout} seconds...")

        await self.screenshot("captcha_detected")

        # Wait for user to solve
        start_time = asyncio.get_event_loop().time()
        while (asyncio.get_event_loop().time() - start_time) < timeout:
            # Check if CAPTCHA is still present (platform-specific implementation)
            await asyncio.sleep(2)
            # Assume solved after timeout/2 for now
            if (asyncio.get_event_loop().time() - start_time) > timeout / 2:
                break

        await self.screenshot("after_captcha")
        print(f"▶️  [{self.platform_name.upper()}] Continuing...")

    async def close(self):
        """Clean up browser resources."""
        if self.browser:
            await self.browser.close()
            print(f"🔒 [{self.platform_name.upper()}] Browser closed")

    async def create_account(self) -> Dict:
        """
        Platform-specific account creation logic.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement create_account()")
