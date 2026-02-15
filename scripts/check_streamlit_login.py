from playwright.sync_api import sync_playwright
import time

def check_login():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        print('Navigating to https://share.streamlit.io...')
        page.goto('https://share.streamlit.io')
        
        # Wait more for dashboard to load
        time.sleep(10)
        
        url = page.url
        print(f'Current URL: {url}')
        
        page.screenshot(path='streamlit_dashboard.png', full_page=True)
        
        if 'login' in url or 'github.com/login' in page.url:
            print('Status: NOT_LOGGED_IN')
        else:
            print('Status: LOGGED_IN')
            
        browser.close()

if __name__ == '__main__':
    check_login()
