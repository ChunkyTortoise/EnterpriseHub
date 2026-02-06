
import asyncio
from playwright.async_api import async_playwright
import time
import os

async def run_audit():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Use a large viewport to ensure all elements are visible
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()

        print("--- Step 1: Launching Dashboard ---")
        try:
            await page.goto("http://localhost:8505", wait_until="networkidle", timeout=60000)
        except Exception as e:
            print(f"Failed to load dashboard: {e}")
            await browser.close()
            return

        # Wait for Streamlit to load
        await page.wait_for_selector('h1', timeout=30000)
        
        print("--- Step 2: Audit '🎯 Lead Command' ---")
        # Navigate to Intent Analysis Tab (Tab 10) for the message audit
        # Streamlit tabs are usually buttons. We can find them by text.
        tabs = page.get_by_role("tab")
        await tabs.get_by_text("🧠 Intent Analysis").click()
        await page.wait_for_timeout(1000)

        # Enter lead message
        lead_msg = "Need to sell my Alta Loma home in 3 weeks, relocating for Google job."
        # The text area has label "Lead Message"
        await page.get_by_label("Lead Message").first.fill(lead_msg)
        
        # Click "🧠 Analyze Intent"
        await page.get_by_role("button", name="🧠 Analyze Intent").click()
        
        # Wait for results
        await page.wait_for_selector("text=FRS:", timeout=20000)
        
        # Verify FRS Score > 80
        frs_text = await page.get_by_text("FRS:").inner_text()
        print(f"Found FRS Text: {frs_text}")
        # Expecting something like "#### FRS: 88.5 (Hot Lead)"
        score = float(frs_text.split(":")[1].split("(")[0].strip())
        if score > 80:
            print(f"✅ FRS Score Verified: {score} > 80")
        else:
            print(f"❌ FRS Score Validation Failed: {score}")

        # Verify CSS 'Elite' styling (check for obsidian theme colors or custom classes)
        # The elite-card class is used in the dashboard
        elite_cards = await page.locator(".elite-card").count()
        if elite_cards > 0:
            print(f"✅ CSS 'Elite' styling applied (Found {elite_cards} elite cards)")
        else:
            print("❌ CSS 'Elite' styling not detected")

        print("--- Step 3: Audit '⚔️ Seller Command' ---")
        # The prompt says Audit '⚔️ Seller Command' which usually means the sidebar hub
        # But the stall message task matches the Tab 4 in Lead Command
        # Let's try to find it in the current hub first (Lead Command)
        await tabs.get_by_text("💼 Seller Bot").click()
        await page.wait_for_timeout(1000)
        
        # Enter seller stall
        seller_stall = "I'm busy, just tell me what Zillow says."
        await page.get_by_label("Seller Message").fill(seller_stall)
        
        # Click "🚀 ENGAGE JORGE PERSONA"
        await page.get_by_role("button", name="🚀 ENGAGE JORGE PERSONA").click()
        
        # Wait for Jorge's response
        await page.wait_for_selector("text=STRATEGY:", timeout=20000)
        
        strategy_text = await page.get_by_text("STRATEGY:").inner_text()
        print(f"Jorge Strategy: {strategy_text}")
        
        # Verify 'Confrontational Mode' triggered
        # In the mock/real bot, this stall should trigger a specific mode
        if "Confrontational" in strategy_text or "STALL DETECTED" in await page.content():
            print("✅ Confrontational Mode/Stall Detection triggered")
        else:
            print(f"❌ Confrontational Mode not explicitly confirmed in strategy text: {strategy_text}")

        # Verify response quality (Psychological Commitment)
        commitment_text = await page.get_by_text("Psychological Commitment:").inner_text()
        print(f"Commitment: {commitment_text}")
        commitment_val = int(commitment_text.split(":")[1].replace("%", "").strip())
        if commitment_val > 90:
            print(f"✅ Response quality/Commitment Verified: {commitment_val}% > 90%")
        else:
            # Note: The mock might return lower, let's see. 
            # In the code it was res['psychological_commitment']
            print(f"⚠️ Commitment Value: {commitment_val}% (Expected > 90%)")

        print("--- Step 4: Audit '📊 Business Analytics' ---")
        # Navigate via Sidebar
        await page.get_by_text("📊 Business Analytics").click()
        # Wait for hub change animation (Swarm Sync)
        await page.wait_for_timeout(2000)
        
        # Verify Plotly charts
        plotly_charts = await page.locator(".js-plotly-plot").count()
        if plotly_charts > 0:
            print(f"✅ Found {plotly_charts} Plotly charts")
        else:
            print("❌ No Plotly charts found")

        # Verify Obsidian theme (check for dark background)
        bg_color = await page.evaluate("window.getComputedStyle(document.body).backgroundColor")
        print(f"Background Color: {bg_color}")
        # Dark mode check (roughly)
        if "0, 0, 0" in bg_color or "5, 7, 10" in bg_color or "38, 39, 48" in bg_color:
             print("✅ Obsidian Elite theme (dark mode) verified")
        else:
             print("⚠️ Theme might not be dark mode")

        # Final Screenshot
        await page.screenshot(path="audit_final_report.png")
        print("--- Audit Complete. Final screenshot saved to audit_final_report.png ---")

        await browser.close()

if __name__ == "__main__":
    asyncio.run(run_audit())
