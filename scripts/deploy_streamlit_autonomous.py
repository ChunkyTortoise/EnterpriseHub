from playwright.sync_api import sync_playwright
import time
import os

def deploy():
    # Use the copy of the profile
    user_data_dir = os.path.abspath('scripts/chrome_copy')
    
    with sync_playwright() as p:
        try:
            # We don't specify executable_path to use playwright's bundled chromium
            # but we use the persistent context with the user data dir copy
            context = p.chromium.launch_persistent_context(
                user_data_dir,
                headless=True,
                viewport={'width': 1280, 'height': 800}
            )
            page = context.new_page()
            
            print("Navigating to Streamlit...")
            page.goto("https://share.streamlit.io")
            time.sleep(5)
            
            print(f"Current URL: {page.url}")
            page.screenshot(path="streamlit_autonomous_check.png")
            
            # Check if we are logged in
            if "Continue to sign-in" in page.content():
                print("Not logged in. Attempting sign-in...")
                page.click("button:has-text('Continue to sign-in')")
                time.sleep(5)
                print(f"URL after click: {page.url}")
                page.screenshot(path="streamlit_after_click.png")
            
            context.close()
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    deploy()
