import asyncio
from playwright.async_api import async_playwright
import json
import sys
from datetime import datetime

async def debug_dashboard():
    async with async_playwright() as p:
        # Use headful for debugging if needed, but headless is standard for agents
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        print("🚀 Navigating to http://localhost:8505...")
        try:
            await page.goto("http://localhost:8505")
            await page.wait_for_selector("[data-testid='stAppViewContainer']")
            print("✅ Dashboard base loaded.")
            
            # Wait for content to stabilize
            await asyncio.sleep(5)

            # 1. Check Neural Uplink Status
            print("\n📡 Checking Neural Uplink...")
            sidebar = page.locator("[data-testid='stSidebar']")
            if await sidebar.count() > 0:
                sidebar_text = await sidebar.inner_text()
                uplink_status = {}
                for bot in ["Lead Bot", "Seller Bot", "Vapi Voice AI"]:
                    if bot in sidebar_text:
                        # Extract the status line after the bot name
                        lines = sidebar_text.split("\n")
                        for i, line in enumerate(lines):
                            if bot in line:
                                status = lines[i+1] if i+1 < len(lines) else "UNKNOWN"
                                uplink_status[bot] = status
                print(f"Status: {uplink_status}")
            else:
                print("❌ Sidebar not found")
                uplink_status = {}

            # 2. Extract Terminal Logs (Scroll to bottom first)
            print("\n💻 Extracting Terminal Logs...")
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            
            terminal_lines = page.locator(".terminal-line")
            terminal_logs = []
            count = await terminal_lines.count()
            print(f"Found {count} .terminal-line elements")
            
            for i in range(count):
                text = await terminal_lines.nth(i).inner_text()
                if text.strip() and text.strip() != "_":
                    terminal_logs.append(text.strip())
            
            if not terminal_logs:
                # Fallback to searching body text for log patterns
                all_text = await page.inner_text("body")
                for line in all_text.split("\n"):
                    if any(prefix in line for prefix in ["[ANALYSIS]", "[PROTOCOL]", "[SYNTHESIS]", "[VOICE_AI]", "[MARKET]", "[NEGOTIATION]", "[STRATEGY]"]):
                        terminal_logs.append(line.strip())

            print(f"Captured {len(terminal_logs)} logs.")

            # 3. Check System Config
            print("\n⚙️ Navigating to System Config...")
            config_hub = page.get_by_text("⚙️ System Config")
            if await config_hub.count() > 0:
                await config_hub.first.click()
                print("✅ Clicked System Config Hub")
                await asyncio.sleep(5)
                
                # Click GHL Integration Tab
                integration_tab = page.get_by_text("GHL Integration")
                if await integration_tab.count() > 0:
                    await integration_tab.first.click()
                    print("✅ Clicked GHL Integration Tab")
                    await asyncio.sleep(3)
                    
                    # Check Field Mapping Table
                    print("\n🛰️ Checking Field Mapping (MOAT)...")
                    # Streamlit tables are sometimes div-wrapped
                    mapping_table = page.locator("table")
                    table_data = "Not found"
                    if await mapping_table.count() > 0:
                        table_data = await mapping_table.first.inner_text()
                        print(f"Table Data:\n{table_data}")
                    else:
                        # Try to find by content
                        body_text = await page.inner_text("body")
                        if "GHL Field ID" in body_text:
                            print("✅ Found 'GHL Field ID' text in body")
                            table_data = "Headers found but table selector failed"
                else:
                    print("❌ Integration tab not found")
            else:
                print("❌ System Config hub button not found")

            # 4. Final Report
            report = {
                "timestamp": datetime.now().isoformat(),
                "uplink_status": uplink_status,
                "terminal_logs": terminal_logs[-10:],
                "ghl_mapping": table_data if 'table_data' in locals() else "Not found"
            }
            
            with open("debug_report.json", "w") as f:
                json.dump(report, f, indent=2)
            
            # Take a final screenshot of the current state
            await page.screenshot(path="debug_final_state.png", full_page=True)
            print("\n✅ Debugging complete. Report and screenshot saved.")

        except Exception as e:
            print(f"❌ Error during debugging: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_dashboard())