
import asyncio
from playwright.async_api import async_playwright
import json
import os
from datetime import datetime

async def deep_debug():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        page.set_default_timeout(60000)
        
        results = []
        screenshots_dir = "debug_screenshots"
        os.makedirs(screenshots_dir, exist_ok=True)

        print("🚀 Starting Deep Debug of Obsidian Command Center (http://localhost:8505)...")
        
        try:
            await page.goto("http://localhost:8505")
            await page.wait_for_selector("[data-testid='stAppViewContainer']")
            await asyncio.sleep(5) # Let initial animations finish

            hubs = ["🎯 Lead Command", "⚔️ Seller Command", "📊 Business Analytics", "⚙️ System Config"]
            
            for hub in hubs:
                print(f"\n📁 Testing Hub: {hub}")
                # Try multiple ways to find the hub button
                hub_selectors = [
                    page.get_by_text(hub),
                    page.locator(f"label:has-text('{hub}')"),
                    page.locator(f"div[data-testid='stMarkdownContainer']:has-text('{hub}')")
                ]
                
                found = False
                for selector in hub_selectors:
                    if await selector.count() > 0:
                        await selector.first.click()
                        found = True
                        break
                
                if found:
                    await asyncio.sleep(5) # Let hub load
                    print(f"  ✅ Hub '{hub}' selected.")
                    
                    # Hub-level check
                    hub_screenshot = f"{screenshots_dir}/{hub.replace(' ', '_').lower().replace('🎯', 'lead').replace('⚔️', 'seller').replace('📊', 'analytics').replace('⚙️', 'config')}.png"
                    await page.screenshot(path=hub_screenshot)
                    
                    # Tab list logic
                    tab_list = []
                    if "Lead" in hub:
                        tab_list = ["🎯 Neural Scoring", "📊 Pipeline", "🎤 Voice AI", "💼 Seller Bot", "👻 Follow-Up", "🤝 Retention", "📈 Market Intelligence", "🏠 Property AI", "📊 Analytics", "🧠 Intent Analysis", "🔥 War Room", "🎤 Whisper Mode"]
                    elif "Seller" in hub:
                        tab_list = ["🎯 Negotiation", "📊 Pipeline", "🛡️ Compliance"]
                    elif "Analytics" in hub:
                        tab_list = ["💰 Revenue Forecasting", "🎯 Conversion Funnel", "🗺️ Geographic Analytics", "🧠 Lead Intelligence", "💵 ROI Attribution"]
                    elif "Config" in hub:
                        tab_list = ["🎯 Lead Bot Config", "⚔️ Seller Bot Config", "🔗 GHL Integration"]

                    for tab_name in tab_list:
                        print(f"  📑 Testing Tab: {tab_name}")
                        # Clean tab name for simpler finding if emoji fails
                        clean_tab = tab_name.split(" ", 1)[1] if " " in tab_name else tab_name
                        
                        tab_selectors = [
                            page.get_by_text(tab_name),
                            page.get_by_text(clean_tab),
                            page.locator(f"button:has-text('{clean_tab}')"),
                            page.locator(f"div[data-testid='stMarkdownContainer']:has-text('{clean_tab}')")
                        ]
                        
                        tab_found = False
                        for t_selector in tab_selectors:
                            if await t_selector.count() > 0:
                                await t_selector.first.click()
                                tab_found = True
                                break
                        
                        if tab_found:
                            await asyncio.sleep(3)
                            # Check for common error indicators
                            body_text = await page.inner_text("body")
                            errors = []
                            if "Traceback" in body_text: errors.append("Python Traceback detected")
                            if "StreamlitAPIException" in body_text: errors.append("Streamlit API Exception")
                            if "Error:" in body_text: errors.append("Visible 'Error:' text")
                            
                            # Check for charts/tables
                            plotly_charts = await page.locator(".js-plotly-plot").count()
                            tables = await page.locator("table").count()
                            
                            status = "PASS" if not errors else "FAIL"
                            print(f"    Status: {status} | Charts: {plotly_charts} | Tables: {tables}")
                            
                            tab_screenshot = f"{screenshots_dir}/{hub.replace(' ', '_')}_{tab_name.replace(' ', '_')}.png"
                            await page.screenshot(path=tab_screenshot)
                            
                            results.append({
                                "hub": hub,
                                "tab": tab_name,
                                "status": status,
                                "errors": errors,
                                "plotly_charts": plotly_charts,
                                "tables": tables,
                                "screenshot": tab_screenshot
                            })
                        else:
                            print(f"    ⚠️ Tab '{tab_name}' not found")
                else:
                    print(f"  ❌ Hub button '{hub}' not found")

            # Final report
            report_path = "deep_debug_report.json"
            with open(report_path, "w") as f:
                json.dump(results, f, indent=2)
            
            print(f"\n✅ Deep debug complete. Results saved to {report_path}")
            print(f"📸 Screenshots saved in {screenshots_dir}/")

        except Exception as e:
            print(f"❌ Critical error during deep debug: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(deep_debug())
