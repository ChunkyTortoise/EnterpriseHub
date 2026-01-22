
import asyncio
from playwright.async_api import async_playwright
import json
import os

async def validate_interactions():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        page.set_default_timeout(60000)
        
        print("🚀 Starting Interaction Validation...")
        try:
            await page.goto("http://localhost:8505")
            await page.wait_for_selector("[data-testid='stAppViewContainer']")
            await asyncio.sleep(5)

            # 1. Test "Analyze Lead" in Lead Command
            print("\n🔍 Testing 'Analyze Lead' form...")
            await page.get_by_text("🎯 Lead Command").first.click()
            await asyncio.sleep(2)
            
            # Fill the form
            await page.fill("input[aria-label='Lead Name']", "Validation Test Lead")
            await page.get_by_text("🚀 Analyze Lead").click()
            await asyncio.sleep(5)
            
            # Check if result appeared
            if "NEURAL HEALTH" in await page.inner_text("body"):
                print("✅ 'Analyze Lead' produced results.")
            else:
                print("❌ 'Analyze Lead' failed to show Neural Health results.")

            # 2. Test "Engage Jorge Persona" in Seller Bot tab
            print("\n💼 Testing 'Engage Jorge Persona'...")
            # Click the tab
            seller_bot_tab = page.get_by_text("💼 Seller Bot")
            if await seller_bot_tab.count() > 0:
                await seller_bot_tab.first.click()
                await asyncio.sleep(2)
                
                await page.get_by_text("🚀 ENGAGE JORGE PERSONA").click()
                await asyncio.sleep(5)
                
                if "STRATEGY:" in await page.inner_text("body"):
                    print("✅ 'Engage Jorge Persona' produced results.")
                else:
                    print("❌ 'Engage Jorge Persona' failed to show strategy.")
            else:
                print("⚠️ '💼 Seller Bot' tab not found.")

            # 3. Test "Inject CMA Snapshot" in Whisper Mode
            print("\n🎤 Testing 'Inject CMA Snapshot' in Whisper Mode...")
            whisper_tab = page.get_by_text("🎤 Whisper Mode")
            if await whisper_tab.count() > 0:
                await whisper_tab.first.click()
                await asyncio.sleep(2)
                
                await page.get_by_text("📊 INJECT CMA SNAPSHOT").click()
                await asyncio.sleep(2)
                
                # Check for toast or decision stream update
                body_text = await page.inner_text("body")
                if "CMA Data injected" in body_text or "CMA Injection" in body_text:
                    print("✅ 'Inject CMA Snapshot' triggered successfully.")
                else:
                    print("❌ 'Inject CMA Snapshot' failed to trigger.")
            else:
                print("⚠️ '🎤 Whisper Mode' tab not found.")

            # 4. Test "Test GHL Connection" in System Config
            print("\n⚙️ Testing 'Test GHL Connection'...")
            await page.get_by_text("⚙️ System Config").first.click()
            await asyncio.sleep(2)
            await page.get_by_text("🔗 GHL Integration").first.click()
            await asyncio.sleep(2)
            
            await page.get_by_text("🛰️ Test GHL Connection").click()
            await asyncio.sleep(3)
            
            if "Successful" in await page.inner_text("body"):
                print("✅ 'Test GHL Connection' verified.")
            else:
                print("❌ 'Test GHL Connection' did not report success.")

            print("\n🏁 Interaction validation complete.")

        except Exception as e:
            print(f"❌ Error during validation: {e}")
        finally:
            await browser.close()

if __name__ == "__main__":
    asyncio.run(validate_interactions())
