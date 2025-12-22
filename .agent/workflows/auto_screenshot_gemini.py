#!/usr/bin/env python3
"""
Automated Screenshot Capture for EnterpriseHub
Captures all 15 portfolio screenshots automatically using Playwright

Usage:
    python assets/auto_screenshot.py

Requirements:
    pip install playwright pillow google-generativeai
    playwright install chromium
"""

import asyncio
from pathlib import Path
from playwright.async_api import async_playwright, Page
from PIL import Image
import google.generativeai as genai

# Configuration
DEMO_URL = "https://staging-enterprise-hub.streamlit.app/"
SCREENSHOTS_DIR = Path(__file__).parent / "screenshots"
VIEWPORT_SIZE = {"width": 1920, "height": 1080}

# Screenshot definitions
SCREENSHOTS = {
    "marketing": [
        {
            "filename": "marketing-analytics-dashboard.png",
            "module": "Marketing Analytics",
            "description": "Dashboard with 4 KPI cards",
        },
        {
            "filename": "marketing-analytics-roi-heatmap.png",
            "module": "Marketing Analytics",
            "tab": "ROI Calculator",
            "description": "ROI heatmap",
        },
        {
            "filename": "marketing-analytics-ab-test.png",
            "module": "Marketing Analytics",
            "tab": "A/B Testing",
            "description": "A/B test results",
        },
        {
            "filename": "marketing-analytics-attribution.png",
            "module": "Marketing Analytics",
            "tab": "Attribution Modeling",
            "description": "Attribution models comparison",
        },
        {
            "filename": "content-engine-full.png",
            "module": "Content Engine",
            "description": "Full 4-panel interface",
        },
        {
            "filename": "content-engine-templates.png",
            "module": "Content Engine",
            "description": "6 template cards",
        },
        {
            "filename": "content-engine-output.png",
            "module": "Content Engine",
            "description": "Generated LinkedIn post",
        },
    ],
    "bi": [
        {
            "filename": "margin-hunter-dashboard.png",
            "module": "Margin Hunter",
            "description": "Full CVP dashboard",
        },
        {
            "filename": "margin-hunter-heatmap.png",
            "module": "Margin Hunter",
            "description": "Sensitivity heatmap",
        },
        {
            "filename": "margin-hunter-scenarios.png",
            "module": "Margin Hunter",
            "description": "Scenario comparison table",
        },
        {
            "filename": "market-pulse-4panel.png",
            "module": "Market Pulse",
            "description": "4-panel technical chart",
        },
        {
            "filename": "data-detective-profile.png",
            "module": "Data Detective",
            "description": "Data profile overview",
        },
        {
            "filename": "data-detective-heatmap.png",
            "module": "Data Detective",
            "description": "Correlation heatmap",
        },
        {
            "filename": "data-detective-ai.png",
            "module": "Data Detective",
            "description": "AI insights",
        },
        {
            "filename": "financial-analyst-metrics.png",
            "module": "Financial Analyst",
            "description": "Key metrics cards",
        },
    ],
}


async def generate_with_gemini(prompt: str) -> str:
    """Generates text using the Gemini API"""
    try:
        print(f"  → Generating with Gemini: {prompt}")
        model = genai.GenerativeModel("gemini-pro")
        response = await model.generate_content_async(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"  ✗ Gemini generation failed: {e}")
        return ""


async def setup_directories():
    """Create screenshot directories if they don't exist"""
    for folder in ["marketing", "bi", "hero"]:
        folder_path = SCREENSHOTS_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
    print("✓ Directories created")


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
        if img.mode == "RGBA":
            background = Image.new("RGB", img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        # Save with optimization
        img.save(image_path, "PNG", optimize=True, quality=85)

        # Check file size
        size_kb = image_path.stat().st_size / 1024
        print(f"    Optimized: {size_kb:.1f} KB")
    except Exception as e:
        print(f"    Warning: Optimization failed - {e}")


async def capture_margin_hunter(page: Page, output_dir: Path):
    """Capture Margin Hunter screenshots (3 total)"""
    print("\n📊 Capturing Margin Hunter...")

    if not await click_sidebar_module(page, "Margin Hunter"):
        return

    try:
        # Fill inputs
        print("  → Filling inputs...")
        await page.fill('input[aria-label="Price per Unit ($)"]', "99")
        await page.fill('input[aria-label="Variable Cost per Unit ($)"]', "18")
        await page.fill('input[aria-label="Total Fixed Costs ($)"]', "75000")
        await page.fill('input[aria-label="Target Profit ($)"]', "25000")
        await page.fill('input[aria-label="Current Sales Volume (units)"]', "1100")

        # Wait for calculations to render
        await asyncio.sleep(3)

        # Screenshot 1: Full dashboard
        screenshot_path = output_dir / "bi" / "margin-hunter-dashboard.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: margin-hunter-dashboard.png")
        await optimize_image(screenshot_path)

        # Scroll to heatmap
        await page.evaluate("window.scrollTo(0, 800)")
        await asyncio.sleep(2)

        # Screenshot 2: Heatmap
        screenshot_path = output_dir / "bi" / "margin-hunter-heatmap.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: margin-hunter-heatmap.png")
        await optimize_image(screenshot_path)

        # Scroll to scenarios
        await page.evaluate("window.scrollTo(0, 1400)")
        await asyncio.sleep(2)

        # Screenshot 3: Scenarios table
        screenshot_path = output_dir / "bi" / "margin-hunter-scenarios.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: margin-hunter-scenarios.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Margin Hunter: {e}")


async def capture_market_pulse(page: Page, output_dir: Path):
    """Capture Market Pulse 4-panel chart"""
    print("\n📈 Capturing Market Pulse...")

    if not await click_sidebar_module(page, "Market Pulse"):
        return

    try:
        # Fill ticker
        print("  → Entering ticker SPY...")
        await page.fill('input[placeholder="Enter ticker (e.g., AAPL, MSFT)"]', "SPY")

        # Select period (6 months)
        await page.select_option('select:has-text("Time Period")', "6mo")

        # Click Load Data button
        await page.click('button:has-text("Load Data")')

        # Wait for all 4 panels to render
        print("  → Waiting for charts to render...")
        await asyncio.sleep(8)

        # Screenshot
        screenshot_path = output_dir / "bi" / "market-pulse-4panel.png"
        await page.screenshot(path=str(screenshot_path), full_page=True)
        print("  ✓ Saved: market-pulse-4panel.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Market Pulse: {e}")


async def capture_marketing_analytics(page: Page, output_dir: Path, gemini_enabled: bool = False):
    """Capture Marketing Analytics screenshots (4 total)"""
    print("\n📊 Capturing Marketing Analytics...")

    if not await click_sidebar_module(page, "Marketing Analytics"):
        return

    try:
        # Wait for dashboard to load with demo data
        await asyncio.sleep(3)

        # Screenshot 1: Dashboard
        screenshot_path = output_dir / "marketing" / "marketing-analytics-dashboard.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: marketing-analytics-dashboard.png")
        await optimize_image(screenshot_path)

        # Navigate to A/B Testing tab
        print("  → Navigating to A/B Testing tab...")
        await page.click('button:has-text("A/B Testing")')
        await asyncio.sleep(2)

        # Fill A/B test inputs
        if gemini_enabled:
            visitors_a = await generate_with_gemini(
                "Generate a number of visitors for variant A of an A/B test (e.g., between 1000 and 2000)."
            )
            conversions_a = await generate_with_gemini(
                "Generate a number of conversions for variant A of an A/B test (e.g., between 50 and 100)."
            )
            visitors_b = await generate_with_gemini(
                "Generate a number of visitors for variant B of an A/B test (e.g., between 1000 and 2000)."
            )
            conversions_b = await generate_with_gemini(
                "Generate a number of conversions for variant B of an A/B test (e.g., between 60 and 120)."
            )
            await page.fill('input[aria-label="Variant A Visitors"]', visitors_a)
            await page.fill('input[aria-label="Variant A Conversions"]', conversions_a)
            await page.fill('input[aria-label="Variant B Visitors"]', visitors_b)
            await page.fill('input[aria-label="Variant B Conversions"]', conversions_b)
        else:
            await page.fill('input[aria-label="Variant A Visitors"]', "1000")
            await page.fill('input[aria-label="Variant A Conversions"]', "50")
            await page.fill('input[aria-label="Variant B Visitors"]', "1000")
            await page.fill('input[aria-label="Variant B Conversions"]', "65")

        # Calculate
        await page.click('button:has-text("Calculate")')
        await asyncio.sleep(2)

        # Screenshot 2: A/B Test results
        screenshot_path = output_dir / "marketing" / "marketing-analytics-ab-test.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: marketing-analytics-ab-test.png")
        await optimize_image(screenshot_path)

        # Navigate to ROI Calculator tab
        print("  → Navigating to ROI Calculator tab...")
        await page.click('button:has-text("ROI Calculator")')
        await asyncio.sleep(2)

        # Fill ROI inputs
        await page.fill('input[aria-label="Campaign Spend"]', "5000")
        await page.fill('input[aria-label="Visitors"]', "1000")

        # Scroll to heatmap
        await page.evaluate("window.scrollTo(0, 600)")
        await asyncio.sleep(2)

        # Screenshot 3: ROI Heatmap
        screenshot_path = output_dir / "marketing" / "marketing-analytics-roi-heatmap.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: marketing-analytics-roi-heatmap.png")
        await optimize_image(screenshot_path)

        # Navigate to Attribution Modeling tab
        print("  → Navigating to Attribution Modeling tab...")
        await page.click('button:has-text("Attribution")')
        await asyncio.sleep(2)

        # Screenshot 4: Attribution
        screenshot_path = output_dir / "marketing" / "marketing-analytics-attribution.png"
        await page.screenshot(path=str(screenshot_path), full_page=False)
        print("  ✓ Saved: marketing-analytics-attribution.png")
        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Marketing Analytics: {e}")


async def capture_content_engine(
    page: Page, output_dir: Path, api_key: str = None, gemini_enabled: bool = False
):
    """Capture Content Engine screenshots (3 total)"""

    print("\n✍️ Capturing Content Engine...")

    if not await click_sidebar_module(page, "Content Engine"):
        return

    try:
        # Check if API key needed

        if api_key:
            print("  → Entering API key...")

            await page.fill('input[type="password"]', api_key)

        # Fill inputs

        print("  → Filling inputs...")

        if gemini_enabled:
            topic = await generate_with_gemini(
                "Generate a topic for a LinkedIn post about the future of AI in marketing."
            )

            audience = await generate_with_gemini(
                "Generate a target audience for a LinkedIn post about the future of AI in marketing."
            )

            keywords = await generate_with_gemini(
                "Generate a few keywords for a LinkedIn post about the future of AI in marketing."
            )

            await page.fill('textarea[aria-label="Topic/Theme"]', topic)

            await page.fill('textarea[aria-label="Target Audience"]', audience)

            await page.fill('input[aria-label="Keywords"]', keywords)

        else:
            await page.fill(
                'textarea[aria-label="Topic/Theme"]', "How AI is transforming marketing analytics"
            )

            await page.fill(
                'textarea[aria-label="Target Audience"]', "CMOs and marketing directors"
            )

            await page.fill('input[aria-label="Keywords"]', "AI, ROI, analytics, automation")

        # Screenshot 1: Full interface (pre-generation)

        screenshot_path = output_dir / "marketing" / "content-engine-full.png"

        await page.screenshot(path=str(screenshot_path), full_page=True)

        print("  ✓ Saved: content-engine-full.png")

        await optimize_image(screenshot_path)

        # Scroll to templates

        await page.evaluate("window.scrollTo(0, 400)")

        await asyncio.sleep(1)

        # Screenshot 2: Template cards

        screenshot_path = output_dir / "marketing" / "content-engine-templates.png"

        await page.screenshot(path=str(screenshot_path), full_page=False)

        print("  ✓ Saved: content-engine-templates.png")

        await optimize_image(screenshot_path)

        # Select template and tone

        await page.click('button:has-text("Thought Leadership")')

        await page.click('button:has-text("Analytical")')

        if api_key:
            # Generate post

            print("  → Generating LinkedIn post...")

            await page.click('button:has-text("Generate")')

            await asyncio.sleep(5)  # Wait for Claude API

            # Screenshot 3: Generated output

            await page.evaluate("window.scrollTo(0, 800)")

            screenshot_path = output_dir / "marketing" / "content-engine-output.png"

            await page.screenshot(path=str(screenshot_path), full_page=False)

            print("  ✓ Saved: content-engine-output.png")

            await optimize_image(screenshot_path)

        else:
            print("  ⚠ Skipping generation (no API key provided)")

    except Exception as e:
        print(f"  ✗ Error capturing Content Engine: {e}")


async def capture_data_detective(page: Page, output_dir: Path, api_key: str = None):
    """Capture Data Detective screenshots (3 total)"""

    print("\n🔍 Capturing Data Detective...")

    if not await click_sidebar_module(page, "Data Detective"):
        return

    print("  ⚠ Note: Data Detective requires CSV upload - manual screenshots recommended")

    print("  → To capture manually:")

    print("     1. Upload a sample CSV (100+ rows)")

    print("     2. Screenshot the Data Profile tab")

    print("     3. Screenshot the Correlation Heatmap")

    print("     4. Enter API key and screenshot AI Insights")


async def capture_financial_analyst(page: Page, output_dir: Path):
    """Capture Financial Analyst screenshot"""

    print("\n💰 Capturing Financial Analyst...")

    if not await click_sidebar_module(page, "Financial Analyst"):
        return

    try:
        # Fill ticker

        print("  → Entering ticker AAPL...")

        await page.fill('input[placeholder="Enter ticker"]', "AAPL")

        await page.click('button:has-text("Analyze")')

        # Wait for data to load

        print("  → Waiting for data...")

        await asyncio.sleep(5)

        # Screenshot

        screenshot_path = output_dir / "bi" / "financial-analyst-metrics.png"

        await page.screenshot(path=str(screenshot_path), full_page=False)

        print("  ✓ Saved: financial-analyst-metrics.png")

        await optimize_image(screenshot_path)

    except Exception as e:
        print(f"  ✗ Error capturing Financial Analyst: {e}")


async def main():
    """Main screenshot capture orchestration"""

    print("=" * 60)

    print("EnterpriseHub Automated Screenshot Capture")

    print("=" * 60)

    # Setup

    await setup_directories()

    # Ask for API key (optional)

    print("\n🔑 Optional: Enter Anthropic API key for Content Engine/Data Detective")

    print("   (Press Enter to skip AI-powered screenshots)")

    anthropic_api_key = input("Anthropic API Key: ").strip() or None

    print("\n🔑 Optional: Enter Gemini API key for Content Engine/Data Detective")

    print("   (Press Enter to skip AI-powered screenshots)")

    gemini_api_key = input("Gemini API Key: ").strip() or None

    if gemini_api_key:
        genai.configure(api_key=gemini_api_key)

        async with async_playwright() as p:
            print("\n🌐 Launching browser...")

            browser = await p.chromium.launch(headless=True)  # headless=True to hide browser

            context = await browser.new_context(viewport=VIEWPORT_SIZE)

            page = await context.new_page()

            try:
                # Load demo

                print(f"🔗 Opening {DEMO_URL}")

                await page.goto(DEMO_URL, timeout=30000)

                await wait_for_streamlit_ready(page)

                print("✓ Demo loaded\n")

                # Capture screenshots in order

                await capture_margin_hunter(page, SCREENSHOTS_DIR)

                await capture_market_pulse(page, SCREENSHOTS_DIR)

                await capture_marketing_analytics(
                    page, SCREENSHOTS_DIR, gemini_enabled=bool(gemini_api_key)
                )

                await capture_content_engine(
                    page, SCREENSHOTS_DIR, anthropic_api_key, gemini_enabled=bool(gemini_api_key)
                )

                await capture_financial_analyst(page, SCREENSHOTS_DIR)

                # Data Detective requires manual upload

                await capture_data_detective(page, SCREENSHOTS_DIR, anthropic_api_key)

                print("\n" + "=" * 60)

                print("✅ Screenshot capture complete!")

                print("=" * 60)

                print(f"\n📁 Screenshots saved to: {SCREENSHOTS_DIR}")

                print("\n📋 Next steps:")

                print("   1. Review screenshots in /assets/screenshots/")

                print("   2. Manually capture Data Detective (requires CSV upload)")

                print("   3. Run: git add assets/screenshots/ && git commit -m 'Add screenshots'")

            except Exception as e:
                print(f"\n❌ Error: {e}")

            finally:
                await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
