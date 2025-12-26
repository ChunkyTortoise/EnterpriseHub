#!/usr/bin/env python3
"""Selenium-based screenshot automation for EnterpriseHub (Playwright alternative)."""

import time
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configuration
STREAMLIT_URL = "http://localhost:8501"
OUTPUT_DIR = Path("screenshots")
WAIT_TIME = 5  # seconds to wait for page load

# Screenshot targets (module_name, description)
MODULES = [
    ("Market Pulse", "Real-time stock market analysis"),
    ("Financial Analyst", "AI-powered financial insights"),
    ("Content Engine", "LinkedIn content generation"),
    ("Sentiment Compass", "Market sentiment analysis"),
    ("Data Detective", "Data quality profiling"),
    ("Price Prophet", "Price optimization tool"),
    ("Document Processor", "Document analysis tool"),
]


def setup_driver():
    """Configure and return Selenium Chrome driver."""
    print("🔧 Setting up Chrome driver...")

    options = Options()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    # Install and setup ChromeDriver automatically
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1920, 1080)

    print("✓ Chrome driver ready")
    return driver


def wait_for_streamlit(driver, timeout=10):
    """Wait for Streamlit app to be ready."""
    try:
        WebDriverWait(driver, timeout).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(2)  # Extra wait for Streamlit rendering
        return True
    except TimeoutException:
        return False


def navigate_to_module(driver, module_name):
    """Navigate to a specific module in Streamlit sidebar."""
    try:
        # Wait for sidebar navigation
        time.sleep(1)

        # Try to find and click the module radio button
        radios = driver.find_elements(By.CSS_SELECTOR, "[role='radio']")
        for radio in radios:
            label = radio.find_element(By.TAG_NAME, "label")
            if module_name.lower() in label.text.lower():
                label.click()
                time.sleep(WAIT_TIME)  # Wait for module to load
                return True

        print(f"⚠️  Could not find module: {module_name}")
        return False

    except Exception as e:
        print(f"❌ Error navigating to {module_name}: {e}")
        return False


def take_screenshot(driver, module_name, output_dir):
    """Take screenshot of current page."""
    filename = f"{module_name.lower().replace(' ', '_')}.png"
    filepath = output_dir / filename

    try:
        driver.save_screenshot(str(filepath))
        print(f"✓ Screenshot saved: {filename}")
        return True
    except Exception as e:
        print(f"❌ Failed to save screenshot: {e}")
        return False


def main():
    print("=" * 60)
    print("EnterpriseHub Screenshot Automation (Selenium)")
    print("=" * 60)

    # Create output directory
    OUTPUT_DIR.mkdir(exist_ok=True)
    print(f"✓ Output directory: {OUTPUT_DIR.absolute()}")

    driver = None
    try:
        # Setup driver
        driver = setup_driver()

        # Navigate to Streamlit app
        print(f"\n🌐 Opening Streamlit app: {STREAMLIT_URL}")
        driver.get(STREAMLIT_URL)

        if not wait_for_streamlit(driver):
            print("❌ Streamlit app failed to load")
            print("   Make sure the app is running: streamlit run app.py")
            return

        print("✓ Streamlit app loaded")

        # Take screenshots of each module
        print(f"\n📸 Capturing {len(MODULES)} module screenshots...\n")

        success_count = 0
        for i, (module_name, description) in enumerate(MODULES, 1):
            print(f"[{i}/{len(MODULES)}] {module_name}")

            if navigate_to_module(driver, module_name):
                if take_screenshot(driver, module_name, OUTPUT_DIR):
                    success_count += 1

            time.sleep(1)  # Brief pause between modules

        print(f"\n{'=' * 60}")
        print(f"✅ Complete! {success_count}/{len(MODULES)} screenshots captured")
        print(f"📁 Location: {OUTPUT_DIR.absolute()}")
        print(f"{'=' * 60}")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        if driver:
            print("\n🔒 Closing browser...")
            driver.quit()


if __name__ == "__main__":
    # Check if Streamlit is running
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("localhost", 8501))
    sock.close()

    if result != 0:
        print("\n⚠️  WARNING: Streamlit app doesn't appear to be running")
        print("   Start it with: streamlit run app.py")
        print("\nPress Enter to try anyway, or Ctrl+C to exit...")
        input()

    main()
