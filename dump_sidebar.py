
import asyncio
from playwright.async_api import async_playwright

async def dump_sidebar():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("http://localhost:8505")
        await asyncio.sleep(5)
        
        sidebar = await page.query_selector("[data-testid='stSidebar']")
        if sidebar:
            html = await sidebar.inner_html()
            with open("sidebar_dump.html", "w") as f:
                f.write(html)
            print("✅ Sidebar HTML dumped to sidebar_dump.html")
            
            text = await sidebar.inner_text()
            print(f"--- SIDEBAR TEXT ---\n{text}\n---")
        else:
            print("❌ Sidebar not found")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(dump_sidebar())
