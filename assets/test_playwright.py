#!/usr/bin/env python3
"""Minimal Playwright test to diagnose browser launch issues."""

import asyncio

from playwright.async_api import async_playwright


async def test_browser():
    print("Starting Playwright test...")
    async with async_playwright() as p:
        print("Launching browser in headless mode...")
        browser = await p.chromium.launch(headless=True, timeout=30000)
        print("✓ Browser launched successfully!")

        print("Creating page...")
        page = await browser.new_page()
        print("✓ Page created!")

        print("Navigating to example.com...")
        await page.goto("https://example.com", timeout=10000)
        print("✓ Navigation successful!")

        title = await page.title()
        print(f"✓ Page title: {title}")

        await browser.close()
        print("✓ Browser closed successfully!")
        print("\n✅ All tests passed! Playwright is working.")


if __name__ == "__main__":
    try:
        asyncio.run(test_browser())
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
