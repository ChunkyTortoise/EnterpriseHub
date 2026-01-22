
import asyncio
from playwright.async_api import async_playwright

async def dump_errors():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8505")
        await asyncio.sleep(5)
        
        hub = "⚙️ System Config"
        print(f"📁 Navigating to {hub}...")
        await page.get_by_text(hub).first.click()
        await asyncio.sleep(5)
        
        # Capture all text that looks like a traceback or error
        body_text = await page.inner_text("body")
        
        print("\n🔍 Searching for errors in the page...")
        
        # Look for the specific traceback
        if "Traceback" in body_text:
            start_index = body_text.find("Traceback")
            # Capture a good chunk of text after Traceback
            error_dump = body_text[start_index:start_index + 2000]
            print(f"\n🛑 ERROR DUMP:\n{error_dump}\n")
            
            with open("system_config_error.txt", "w") as f:
                f.write(error_dump)
        else:
            print("✅ No 'Traceback' found in page text. (Maybe it's inside an iframe or component?)")
            # Dump all body text to a file for investigation
            with open("full_page_dump.txt", "w") as f:
                f.write(body_text)

        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_errors())
