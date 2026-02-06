
import asyncio
from playwright.async_api import async_playwright

async def dump_body():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8505")
        await asyncio.sleep(10) # Wait 10 seconds
        
        html = await page.inner_html("body")
        with open("body_dump.html", "w") as f:
            f.write(html)
        print("✅ Body HTML dumped to body_dump.html")
        
        text = await page.inner_text("body")
        print(f"--- BODY TEXT (FIRST 500 chars) ---\n{text[:500]}\n---")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_body())
