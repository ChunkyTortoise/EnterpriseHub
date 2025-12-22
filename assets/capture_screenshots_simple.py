#!/usr/bin/env python3
"""
Simplified Screenshot Capture Script for EnterpriseHub.

This is a streamlined version with better error handling and debugging output.
Captures screenshots for UI/UX documentation.

Requirements:
    playwright install chromium (one-time setup)

Usage:
    # Start Streamlit app first
    streamlit run app.py

    # Then run this script
    python3 assets/capture_screenshots_simple.py
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

# Configuration
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_DIR = Path("docs/screenshots")
VIEWPORT = {"width": 1920, "height": 1080}

# Screenshots to capture
CAPTURES = [
    ("Market Pulse", "light", "01_light_theme_main.png"),
    ("Market Pulse", "dark", "02_dark_theme_main.png"),
    ("Design System", "light", "03_design_system_light.png"),
    ("Design System", "dark", "04_design_system_dark.png"),
]


async def wait_for_streamlit(page):
    """Wait for Streamlit to fully load."""
    print("  ⏳ Waiting for Streamlit to load...")
    try:
        await page.wait_for_selector('[data-testid="stApp"]', timeout=15000)
        await page.wait_for_selector('[data-testid="stSidebar"]', timeout=10000)
        await asyncio.sleep(3)  # Extra time for initial render
        print("  ✓ Streamlit loaded")
        return True
    except PlaywrightTimeout:
        print("  ❌ Timeout waiting for Streamlit")
        return False


async def click_theme_button(page, theme: str):
    """Click the light or dark theme button in sidebar."""
    print(f"  🎨 Switching to {theme} theme...")

    try:
        # Get sidebar
        sidebar = await page.wait_for_selector('[data-testid="stSidebar"]', timeout=5000)

        # Find all buttons in sidebar
        buttons = await sidebar.query_selector_all("button")

        # Look for theme button
        target_text = "Light" if theme == "light" else "Dark"

        for button in buttons:
            try:
                text = await button.text_content()
                if text and target_text in text:
                    # Check if button is already active (primary type)
                    # If already active, skip clicking
                    classes = await button.get_attribute("class") or ""

                    await button.click()
                    await asyncio.sleep(2.5)  # Wait for theme to apply
                    print(f"  ✓ {theme.capitalize()} theme activated")
                    return True
            except Exception:
                continue

        print(f"  ⚠️  Could not find {theme} theme button")
        return False

    except Exception as e:
        print(f"  ❌ Error switching theme: {e}")
        return False


async def navigate_to_module(page, module_name: str):
    """Navigate to a module via sidebar navigation."""
    print(f"  📍 Navigating to: {module_name}")

    try:
        sidebar = await page.wait_for_selector('[data-testid="stSidebar"]', timeout=5000)

        # Find radio button labels
        labels = await sidebar.query_selector_all("label")

        for label in labels:
            try:
                text = await label.text_content()
                if text and module_name in text:
                    await label.click()
                    await asyncio.sleep(3)  # Wait for module to load
                    print(f"  ✓ Loaded {module_name}")
                    return True
            except:
                continue

        print(f"  ⚠️  Module not found: {module_name}")
        return False

    except Exception as e:
        print(f"  ❌ Navigation error: {e}")
        return False


async def capture_screenshot(page, filepath: Path):
    """Take a full-page screenshot."""
    print(f"  📸 Capturing: {filepath.name}")

    try:
        # Wait for any animations to complete
        await asyncio.sleep(1)

        # Hide Streamlit's top-right menu
        await page.evaluate(
            """
            () => {
                const toolbar = document.querySelector('[data-testid="stToolbar"]');
                if (toolbar) toolbar.style.visibility = 'hidden';
            }
        """
        )

        # Take screenshot
        await page.screenshot(path=str(filepath), full_page=True)
        print(f"  ✓ Saved: {filepath.name}")
        return True

    except Exception as e:
        print(f"  ❌ Screenshot failed: {e}")
        return False


async def main():
    """Main screenshot capture workflow."""
    print("\n" + "=" * 70)
    print("EnterpriseHub Screenshot Automation")
    print("=" * 70 + "\n")

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"📁 Output: {OUTPUT_DIR.absolute()}\n")

    # Launch browser
    async with async_playwright() as p:
        print("🌐 Launching browser...")

        browser = await p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )

        context = await browser.new_context(
            viewport=VIEWPORT,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        )

        page = await context.new_page()
        print("✓ Browser ready\n")

        # Navigate to app
        print(f"🔗 Opening: {STREAMLIT_URL}")
        try:
            await page.goto(STREAMLIT_URL, wait_until="networkidle", timeout=30000)
        except Exception as e:
            print(f"❌ Failed to open app: {e}")
            print("\n💡 Make sure Streamlit is running: streamlit run app.py")
            await browser.close()
            return False

        if not await wait_for_streamlit(page):
            print("\n❌ App did not load properly")
            await browser.close()
            return False

        print()

        # Capture screenshots
        success = 0
        total = len(CAPTURES)
        current_theme = None

        for i, (module, theme, filename) in enumerate(CAPTURES, 1):
            print(f"[{i}/{total}] {filename}")

            # Switch theme if needed
            if theme != current_theme:
                if await click_theme_button(page, theme):
                    current_theme = theme
                else:
                    print("  ⚠️  Continuing with current theme\n")

            # Navigate to module
            if await navigate_to_module(page, module):
                # Capture screenshot
                filepath = OUTPUT_DIR / filename
                if await capture_screenshot(page, filepath):
                    success += 1

            print()  # Blank line between captures

        await browser.close()

        # Summary
        print("=" * 70)
        print(f"✅ Complete! {success}/{total} screenshots captured")
        print(f"📁 Location: {OUTPUT_DIR.absolute()}")
        print("=" * 70 + "\n")

        if success < total:
            print("⚠️  Some screenshots failed. Common issues:")
            print("   • Module names changed in sidebar")
            print("   • Theme buttons not found")
            print("   • Network timeout")
            print("\n💡 Try running with headless=False to debug visually\n")

        return success == total


if __name__ == "__main__":
    try:
        # Check if Streamlit is likely running
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(("localhost", 8501))
        sock.close()

        if result != 0:
            print("\n⚠️  Streamlit doesn't appear to be running on port 8501")
            print("\n1. Start Streamlit: streamlit run app.py")
            print("2. Wait for it to open in browser")
            print("3. Then run this script again\n")
            sys.exit(1)

        # Run capture
        success = asyncio.run(main())
        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        print("\n\n🛑 Cancelled by user\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)
