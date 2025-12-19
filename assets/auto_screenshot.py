#!/usr/bin/env python3
"""
Automated Screenshot Capture for EnterpriseHub
Captures all 7 module screenshots automatically using Playwright

Usage:
    python assets/auto_screenshot.py

Requirements:
    pip install playwright pillow
    playwright install chromium
"""

import asyncio
import os
from pathlib import Path
from playwright.async_api import async_playwright, Page
from PIL import Image
import io

# Configuration
DEMO_URL = "https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
VIEWPORT_SIZE = {"width": 1920, "height": 1080}

# Screenshot definitions for all 7 modules
SCREENSHOTS = [
    {
        "filename": "margin_hunter_main.png",
        "module": "Margin Hunter",
        "description": "CVP analysis dashboard with SaaS scenario",
    },
    {
        "filename": "market_pulse_chart.png",
        "module": "Market Pulse",
        "description": "SPY stock with 4-panel technical chart",
    },
    {
        "filename": "financial_analyst_main.png",
        "module": "Financial Analyst",
        "description": "Stock fundamentals analysis",
    },
    {
        "filename": "content_engine_main.png",
        "module": "Content Engine",
        "description": "AI-powered LinkedIn post generator",
    },
    {
        "filename": "data_detective_main.png",
        "module": "Data Detective",
        "description": "Data profiling and analysis",
    },
    {
        "filename": "marketing_analytics_main.png",
        "module": "Marketing Analytics",
        "description": "Campaign performance dashboard",
    },
    {
        "filename": "agent_logic_main.png",
        "module": "Agent Logic",
        "description": "Sentiment analysis engine",
    },
]


async def setup_directories():
    """Create screenshot directory if it doesn't exist"""
    SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)
    print(f"✓ Screenshot directory ready: {SCREENSHOTS_DIR}")


async def wait_for_streamlit_ready(page: Page):
    """Wait for Streamlit to fully load"""
    try:
        # Wait for Streamlit's stale element remover to finish
        await page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        await asyncio.sleep(2)  # Extra buffer for dynamic content
    except Exception as e:
        print(f"  Warning: Streamlit detection timeout - {e}")


async def click_sidebar_module(page: Page, module_name: str):
    """Click a module in the Streamlit sidebar"""
    try:
        # Look for the module link in sidebar
        await page.click(f'text="{module_name}"', timeout=5000)
        await wait_for_streamlit_ready(page)
        print(f"  → Navigated to {module_name}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to click {module_name}: {e}")
        return False


async def optimize_image(image_path: Path, max_size_kb: int = 500):
    """Compress image to target file size"""
    try:
        img = Image.open(image_path)

        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        # Save with optimization
        img.save(image_path, 'PNG', optimize=True, quality=85)

        # Check file size
        size_kb = image_path.stat().st_size / 1024
        print(f"    Optimized: {size_kb:.1f} KB")
    except Exception as e:
        print(f"    Warning: Optimization failed - {e}")


async def capture_margin_hunter(page: Page):
    """Capture Margin Hunter with SaaS scenario data"""
    print("\n📊 Capturing Margin Hunter...")

    if not await click_sidebar_module(page, "Margin Hunter"):
        return

    try:
        # Fill SaaS scenario inputs
        print("  → Filling SaaS scenario ($99 price, $18 cost, $75K fixed costs)...")
        await page.fill('input[aria-label="Price per Unit ($)"]', "99")
        await page.fill('input[aria-label="Variable Cost per Unit ($)"]', "18")
        await page.fill('input[aria-label="Total Fixed Costs ($)"]', "75000")
        await page.fill('input[aria-label="Target Profit ($)"]', "25000")
        await page.fill('input[aria-label="Current Sales Volume (units)"]', "1100")

        # Wait for calculations to render
        await asyncio.sleep(3)

        # Capture full dashboard
        screenshot_path = SCREENSHOTS_DIR / "margin_hunter_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: margin_hunter_main.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Margin Hunter: {e}")


async def capture_market_pulse(page: Page):
    """Capture Market Pulse with SPY ticker and 4-panel chart"""
    print("\n📈 Capturing Market Pulse...")

    if not await click_sidebar_module(page, "Market Pulse"):
        return

    try:
        # Fill ticker SPY
        print("  → Entering ticker SPY...")
        await page.fill('input[placeholder="Enter ticker (e.g., AAPL, MSFT)"]', "SPY")

        # Select period (6 months for good chart detail)
        await page.select_option('select:has-text("Time Period")', "6mo")

        # Click Load Data button
        await page.click('button:has-text("Load Data")')

        # Wait for all 4 panels to render (Price, RSI, MACD, Volume)
        print("  → Waiting for 4-panel chart to render...")
        await asyncio.sleep(8)

        # Capture full page with chart
        screenshot_path = SCREENSHOTS_DIR / "market_pulse_chart.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: market_pulse_chart.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Market Pulse: {e}")


async def capture_marketing_analytics(page: Page):
    """Capture Marketing Analytics dashboard"""
    print("\n📊 Capturing Marketing Analytics...")

    if not await click_sidebar_module(page, "Marketing Analytics"):
        return

    try:
        # Wait for dashboard to load with demo data
        print("  → Waiting for dashboard to load...")
        await asyncio.sleep(3)

        # Capture main dashboard with KPI cards
        screenshot_path = SCREENSHOTS_DIR / "marketing_analytics_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: marketing_analytics_main.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Marketing Analytics: {e}")


async def capture_content_engine(page: Page):
    """Capture Content Engine AI post generator"""
    print("\n✍️ Capturing Content Engine...")

    if not await click_sidebar_module(page, "Content Engine"):
        return

    try:
        # Wait for interface to load
        print("  → Waiting for interface to load...")
        await asyncio.sleep(2)

        # Capture main interface (shows all template options)
        screenshot_path = SCREENSHOTS_DIR / "content_engine_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: content_engine_main.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Content Engine: {e}")


async def capture_data_detective(page: Page):
    """Capture Data Detective data profiling interface"""
    print("\n🔍 Capturing Data Detective...")

    if not await click_sidebar_module(page, "Data Detective"):
        return

    try:
        # Wait for upload interface to load
        print("  → Waiting for interface to load...")
        await asyncio.sleep(2)

        # Capture main interface (shows upload prompt and instructions)
        screenshot_path = SCREENSHOTS_DIR / "data_detective_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: data_detective_main.png")
        await optimize_image(screenshot_path)
        print("  ℹ Note: For data analysis screenshots, upload a CSV file manually")

    except Exception as e:
        print(f"  ✗ Error capturing Data Detective: {e}")


async def capture_financial_analyst(page: Page):
    """Capture Financial Analyst stock fundamentals"""
    print("\n💰 Capturing Financial Analyst...")

    if not await click_sidebar_module(page, "Financial Analyst"):
        return

    try:
        # Fill ticker AAPL
        print("  → Entering ticker AAPL...")
        await page.fill('input[placeholder="Enter ticker"]', "AAPL")
        await page.click('button:has-text("Analyze")')

        # Wait for fundamental data to load
        print("  → Waiting for fundamental data to load...")
        await asyncio.sleep(6)

        # Capture full analysis
        screenshot_path = SCREENSHOTS_DIR / "financial_analyst_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: financial_analyst_main.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Financial Analyst: {e}")


async def capture_agent_logic(page: Page):
    """Capture Agent Logic sentiment analysis"""
    print("\n🤖 Capturing Agent Logic...")

    if not await click_sidebar_module(page, "Agent Logic"):
        return

    try:
        # Wait for interface to load
        print("  → Waiting for interface to load...")
        await asyncio.sleep(2)

        # Capture main interface
        screenshot_path = SCREENSHOTS_DIR / "agent_logic_main.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print(f"  ✓ Saved: agent_logic_main.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Agent Logic: {e}")


async def main():
    """Main screenshot capture orchestration"""
    print("=" * 70)
    print("EnterpriseHub - Automated Screenshot Capture")
    print("Capturing all 7 modules from live Streamlit app")
    print("=" * 70)

    # Setup
    await setup_directories()

    async with async_playwright() as p:
        print("\n🌐 Launching browser...")
        browser = await p.chromium.launch(headless=False)  # Set headless=True to hide browser
        context = await browser.new_context(viewport=VIEWPORT_SIZE)
        page = await context.new_page()

        try:
            # Load live app
            print(f"🔗 Opening live app: {DEMO_URL}")
            await page.goto(DEMO_URL, timeout=60000)
            await wait_for_streamlit_ready(page)
            print("✓ Live app loaded successfully\n")

            # Capture all 7 modules in order
            await capture_margin_hunter(page)
            await capture_market_pulse(page)
            await capture_financial_analyst(page)
            await capture_content_engine(page)
            await capture_data_detective(page)
            await capture_marketing_analytics(page)
            await capture_agent_logic(page)

            print("\n" + "=" * 70)
            print("✅ Screenshot capture complete!")
            print("=" * 70)
            print(f"\n📁 Screenshots saved to: {SCREENSHOTS_DIR}")
            print("\n📋 Screenshots captured:")
            for screenshot in SCREENSHOTS:
                print(f"   • {screenshot['filename']} - {screenshot['description']}")
            print("\n💡 Next steps:")
            print("   1. Review screenshots in assets/screenshots/")
            print("   2. Use screenshots for portfolio, documentation, or demos")
            print("   3. Optional: Run 'git add assets/screenshots/' to commit")

        except Exception as e:
            print(f"\n❌ Fatal error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            print("\n🔒 Closing browser...")
            await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
