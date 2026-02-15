import os
from playwright.sync_api import sync_playwright
import time

def check_with_profile():
    # Common path for Chrome profile on macOS
    user_data_dir = os.path.expanduser('~/Library/Application Support/Google/Chrome')
    profile = 'Default'
    
    executable_path = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    
    if not os.path.exists(executable_path):
        print(f"Chrome not found at {executable_path}")
        # Try to find it
        return

    with sync_playwright() as p:
        try:
            # We must use launch_persistent_context
            browser_context = p.chromium.launch_persistent_context(
                user_data_dir,
                executable_path=executable_path,
                headless=True, # Try headless first, but it might not use the same session as headful
                args=["--profile-directory=" + profile]
            )
            page = browser_context.new_page()
            
            print('Navigating to https://share.streamlit.io...')
            page.goto('https://share.streamlit.io')
            
            time.sleep(10)
            
            print(f'Current URL: {page.url}')
            page.screenshot(path='streamlit_profile_check.png')
            
            # Check for buttons
            buttons = page.query_selector_all('button')
            print("Buttons found:")
            for btn in buttons:
                try:
                    text = btn.inner_text()
                    if text:
                        print(f" - {text}")
                except:
                    pass
            
            browser_context.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == '__main__':
    check_with_profile()
