from playwright.sync_api import sync_playwright
import time

def dump_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        page.goto('https://share.streamlit.io')
        time.sleep(10)
        
        # Get all button texts
        buttons = page.query_selector_all('button')
        print("Buttons found:")
        for btn in buttons:
            try:
                text = btn.inner_text()
                if text:
                    print(f" - {text}")
            except:
                pass
            
        # Get all links
        links = page.query_selector_all('a')
        print("\nLinks found:")
        for link in links:
            try:
                text = link.inner_text()
                href = link.get_attribute('href')
                if text or href:
                    print(f" - {text} ({href})")
            except:
                pass
            
        browser.close()

if __name__ == '__main__':
    dump_page()
