#!/usr/bin/env python3
"""
Capture screenshots of all EnterpriseHub modules.
Simplified version that waits for content to load naturally.
"""

import asyncio
from playwright.async_api import async_playwright
from pathlib import Path

MODULES_TO_CAPTURE = [
    ("🏠 Overview", "01_overview.png"),
    ("📊 Market Pulse", "02_market_pulse.png"),
    ("💰 Margin Hunter", "03_margin_hunter.png"),
    ("💼 Financial Analyst", "04_financial_analyst.png"),
    ("🔍 Data Detective", "05_data_detective.png"),
    ("✍️ Content Engine", "06_content_engine.png"),
    ("📈 Marketing Analytics", "07_marketing_analytics.png"),
    ("🎨 Design System", "08_design_system.png"),
]


async def capture_module(page, module_name: str, filename: str, output_dir: Path):
    """Capture screenshot of a specific module."""
    print(f"\n📸 Capturing: {module_name}")

    try:
        # Click on the module in sidebar navigation
        # Look for radio button or link with module name
        await page.click(f'text="{module_name}"', timeout=5000)

        # Wait for module to load
        print(f"   ⏳ Loading {module_name}...")
        await asyncio.sleep(5)

        # Take screenshot
        output_path = output_dir / filename
        await page.screenshot(path=str(output_path), full_page=True)
        print(f"   ✅ Saved: {filename}")
        return True

    except Exception as e:
        print(f"   ⚠️  Failed: {e}")
        return False


async def main():
    OUTPUT_DIR = Path("docs/screenshots")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("EnterpriseHub Module Screenshot Capture")
    print("=" * 70)
    print(f"\n📁 Output directory: {OUTPUT_DIR.absolute()}\n")

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page(viewport={"width": 1920, "height": 1080})

        print("🌐 Opening Streamlit app...")
        await page.goto("http://localhost:8501", timeout=30000)

        # Wait for initial load
        print("⏳ Waiting for app to initialize...")
        await asyncio.sleep(8)

        # Capture each module
        success = 0
        for module_name, filename in MODULES_TO_CAPTURE:
            if await capture_module(page, module_name, filename, OUTPUT_DIR):
                success += 1
            await asyncio.sleep(1)  # Brief pause between captures

        await browser.close()

        # Summary
        print("\n" + "=" * 70)
        print(f"✅ Complete! {success}/{len(MODULES_TO_CAPTURE)} screenshots captured")
        print(f"📁 Location: {OUTPUT_DIR.absolute()}")
        print("=" * 70 + "\n")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n🛑 Cancelled by user\n")
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback

        traceback.print_exc()
