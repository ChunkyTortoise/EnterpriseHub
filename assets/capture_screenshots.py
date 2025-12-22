#!/usr/bin/env python3
"""
Enhanced Playwright Screenshot Automation for EnterpriseHub UI/UX Documentation.

This script captures screenshots for documentation:
1. Light Theme - Main page or representative module
2. Dark Theme - Same view with dark theme
3. Design System Gallery - Component showcase

Requirements:
- Playwright installed: pip install playwright
- Playwright browsers: playwright install chromium
- Streamlit app running: streamlit run app.py

Usage:
    python3 assets/capture_screenshots.py
"""

import asyncio
import socket
import sys
from pathlib import Path

from playwright.async_api import TimeoutError as PlaywrightTimeout
from playwright.async_api import async_playwright

# Configuration
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_DIR = Path("docs/screenshots")
VIEWPORT_SIZE = {"width": 1920, "height": 1080}
WAIT_TIME = 3000  # milliseconds to wait for page load
SCREENSHOT_DELAY = 2000  # milliseconds delay before screenshot

# Screenshot targets
SCREENSHOTS = [
    {
        "name": "01_light_theme_main",
        "description": "Main page - Light Theme",
        "module": "Market Pulse",  # Default landing page
        "theme": "light",
        "filename": "light_theme_main.png",
    },
    {
        "name": "02_dark_theme_main",
        "description": "Main page - Dark Theme",
        "module": "Market Pulse",
        "theme": "dark",
        "filename": "dark_theme_main.png",
    },
    {
        "name": "03_design_system_light",
        "description": "Design System Gallery - Light Theme",
        "module": "Design System",
        "theme": "light",
        "filename": "design_system_light.png",
    },
    {
        "name": "04_design_system_dark",
        "description": "Design System Gallery - Dark Theme",
        "module": "Design System",
        "theme": "dark",
        "filename": "design_system_dark.png",
    },
]


def check_streamlit_running() -> bool:
    """Check if Streamlit app is running on localhost:8501."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", 8501))
    sock.close()
    return result == 0


async def wait_for_streamlit_ready(page):
    """Wait for Streamlit app to be fully loaded and interactive."""
    try:
        # Wait for the main app container
        await page.wait_for_selector('[data-testid="stApp"]', timeout=10000)

        # Wait for sidebar to be present
        await page.wait_for_selector('[data-testid="stSidebar"]', timeout=5000)

        # Additional wait for rendering
        await asyncio.sleep(2)

        return True
    except PlaywrightTimeout:
        return False


async def toggle_theme(page, target_theme: str):
    """Toggle between light and dark theme using sidebar buttons."""
    try:
        # Wait for sidebar to be ready
        await page.wait_for_selector('[data-testid="stSidebar"]', timeout=5000)
        await asyncio.sleep(0.5)

        # Find theme toggle buttons in sidebar
        # Looking for buttons with text "☀️ Light" or "🌙 Dark"
        sidebar = await page.query_selector('[data-testid="stSidebar"]')
        if not sidebar:
            print("  ⚠️  Sidebar not found")
            return False

        buttons = await sidebar.query_selector_all("button")

        target_button_text = "☀️ Light" if target_theme == "light" else "🌙 Dark"
        theme_button = None

        for button in buttons:
            try:
                text = await button.inner_text()
                # Match either "☀️ Light" or "🌙 Dark"
                if (
                    target_button_text in text
                    or (target_theme == "light" and "Light" in text)
                    or (target_theme == "dark" and "Dark" in text)
                ):
                    theme_button = button
                    break
            except:
                continue

        if theme_button:
            await theme_button.click()
            # Wait for Streamlit to rerun and apply the theme
            await asyncio.sleep(2)
            print(f"  ✓ Theme switched to: {target_theme}")
            return True
        else:
            print(f"  ⚠️  Theme button not found for: {target_theme}")
            print(f"  Looking for button text: {target_button_text}")
            return False

    except Exception as e:
        print(f"  ⚠️  Could not toggle theme: {e}")
        print("  Note: Manual theme switching may be required")
        return False


async def navigate_to_module(page, module_name: str):
    """Navigate to a specific module via sidebar radio buttons."""
    try:
        # Wait for sidebar navigation
        await asyncio.sleep(1)

        # Find all radio button labels in sidebar
        sidebar = await page.query_selector('[data-testid="stSidebar"]')
        if not sidebar:
            print("  ⚠️  Sidebar not found")
            return False

        # Look for radio buttons with matching text
        labels = await sidebar.query_selector_all("label")

        for label in labels:
            text = await label.inner_text()
            if module_name in text:
                await label.click()
                await asyncio.sleep(WAIT_TIME / 1000)
                print(f"  ✓ Navigated to: {module_name}")
                return True

        print(f"  ⚠️  Module not found in navigation: {module_name}")
        return False

    except Exception as e:
        print(f"  ❌ Error navigating to {module_name}: {e}")
        return False


async def take_screenshot(page, filepath: Path):
    """Capture full-page screenshot."""
    try:
        # Wait a bit for any animations to complete
        await asyncio.sleep(SCREENSHOT_DELAY / 1000)

        # Hide any loading spinners or progress indicators
        await page.evaluate(
            """
            () => {
                // Hide Streamlit's hamburger menu (top-right)
                const menu = document.querySelector('[data-testid="stToolbar"]');
                if (menu) menu.style.display = 'none';

                // Hide any loading spinners
                const spinners = document.querySelectorAll('[data-testid="stSpinner"]');
                spinners.forEach(s => s.style.display = 'none');
            }
        """
        )

        # Take the screenshot
        await page.screenshot(path=str(filepath), full_page=True)
        print(f"  ✓ Screenshot saved: {filepath.name}")
        return True

    except Exception as e:
        print(f"  ❌ Failed to save screenshot: {e}")
        return False


async def capture_screenshots():
    """Main screenshot capture workflow."""
    print("=" * 70)
    print("EnterpriseHub Screenshot Automation (Playwright)")
    print("=" * 70)

    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR.absolute()}\n")

    async with async_playwright() as p:
        # Launch browser
        print("🌐 Launching browser...")
        browser = await p.chromium.launch(
            headless=True, args=["--disable-blink-features=AutomationControlled"]
        )

        # Create context with viewport
        context = await browser.new_context(
            viewport=VIEWPORT_SIZE,
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        )

        page = await context.new_page()
        print("✓ Browser ready\n")

        # Navigate to Streamlit app
        print(f"🔗 Opening Streamlit app: {STREAMLIT_URL}")
        await page.goto(STREAMLIT_URL, wait_until="networkidle")

        if not await wait_for_streamlit_ready(page):
            print("❌ Streamlit app failed to load")
            print("   Make sure the app is running: streamlit run app.py")
            await browser.close()
            return False

        print("✓ Streamlit app loaded\n")

        # Capture screenshots
        print(f"📸 Capturing {len(SCREENSHOTS)} screenshots...\n")

        success_count = 0
        current_theme = "light"  # Track current theme

        for i, config in enumerate(SCREENSHOTS, 1):
            print(f"[{i}/{len(SCREENSHOTS)}] {config['description']}")

            # Navigate to module if needed
            if await navigate_to_module(page, config["module"]):
                # Toggle theme if needed
                if config["theme"] != current_theme:
                    if await toggle_theme(page, config["theme"]):
                        current_theme = config["theme"]
                    else:
                        print(f"  ⚠️  Continuing with current theme: {current_theme}")

                # Capture screenshot
                filepath = OUTPUT_DIR / config["filename"]
                if await take_screenshot(page, filepath):
                    success_count += 1

            print()  # Blank line between screenshots

        # Close browser
        await browser.close()

        # Summary
        print("=" * 70)
        print(f"✅ Complete! {success_count}/{len(SCREENSHOTS)} screenshots captured")
        print(f"📁 Location: {OUTPUT_DIR.absolute()}")
        print("=" * 70)

        if success_count < len(SCREENSHOTS):
            print("\n⚠️  Some screenshots failed. Common issues:")
            print("   - Theme toggle not found (manual switching may be needed)")
            print("   - Module navigation changed")
            print("   - Network timeout")
            print("\nTip: Run with headless=False in launch() to debug visually")

        return success_count == len(SCREENSHOTS)


async def main():
    """Entry point."""
    # Check if Streamlit is running
    if not check_streamlit_running():
        print("\n⚠️  WARNING: Streamlit app doesn't appear to be running")
        print("   Start it with: streamlit run app.py")
        print("\nPress Enter to try anyway, or Ctrl+C to exit...")
        try:
            input()
        except KeyboardInterrupt:
            print("\n\nAborted.")
            sys.exit(1)

    # Run screenshot capture
    success = await capture_screenshots()

    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
