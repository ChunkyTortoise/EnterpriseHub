# Assets & Screenshot Automation

This directory contains scripts for automating screenshot capture and testing the EnterpriseHub UI.

## Quick Start

### 1. Setup (One-time)

```bash
# Install Playwright browsers
playwright install chromium
```

### 2. Capture Screenshots

```bash
# Terminal 1: Start the app
streamlit run app.py

# Terminal 2: Run screenshot script
python3 assets/capture_screenshots_simple.py
```

Screenshots will be saved to `docs/screenshots/`.

---

## Available Scripts

### `capture_screenshots_simple.py` (Recommended)

**Simplified, reliable screenshot automation.**

**Captures:**
- Light theme (Market Pulse)
- Dark theme (Market Pulse)
- Design System Gallery (light)
- Design System Gallery (dark)

**Features:**
- Clear progress output
- Better error messages
- Automatic theme switching
- Full-page screenshots

**Usage:**
```bash
python3 assets/capture_screenshots_simple.py
```

---

### `capture_screenshots.py`

**Extended version with more configuration options.**

More configurable but similar to the simple version. Use this if you need to customize the screenshot workflow.

**Usage:**
```bash
python3 assets/capture_screenshots.py
```

---

### `selenium_screenshot.py`

**Legacy Selenium-based automation.**

Captures screenshots of all modules but doesn't handle theme switching.

**Requires:**
```bash
pip install selenium webdriver-manager
```

**Usage:**
```bash
python3 assets/selenium_screenshot.py
```

**Output:** `screenshots/*.png` (all modules, current theme only)

---

### `test_playwright.py`

**Minimal Playwright test script.**

Tests if Playwright is installed and working correctly. Useful for debugging.

**Usage:**
```bash
python3 assets/test_playwright.py
```

**Expected output:**
```
Starting Playwright test...
Launching browser in headless mode...
✓ Browser launched successfully!
✓ Page created!
✓ Navigation successful!
✓ Page title: Example Domain
✓ Browser closed successfully!

✅ All tests passed! Playwright is working.
```

---

## Troubleshooting

### "Playwright not installed"

```bash
pip install playwright
playwright install chromium
```

### "Streamlit app failed to load"

Make sure Streamlit is running:
```bash
streamlit run app.py
```

Wait for it to open in your browser, then run the screenshot script.

### "Theme button not found"

The theme buttons may have changed. Check `app.py` for the current theme toggle implementation and update the script's `click_theme_button()` function.

### "Module not found"

Check that module names in the script match the sidebar navigation exactly. See `MODULES` dict in `app.py`.

### Screenshots are blank or cut off

Try increasing wait times in the script:
```python
await asyncio.sleep(5)  # Increase from 3 to 5 seconds
```

### Visual debugging

Edit the script to show the browser:
```python
browser = await p.chromium.launch(
    headless=False,  # Show browser window
    slow_mo=1000     # Slow down actions
)
```

---

## Customizing Screenshots

### Add More Screenshots

Edit `CAPTURES` list in `capture_screenshots_simple.py`:

```python
CAPTURES = [
    # Existing screenshots...
    ("Financial Analyst", "light", "financial_analyst_light.png"),
    ("Content Engine", "dark", "content_engine_dark.png"),
]
```

### Change Output Directory

Edit `OUTPUT_DIR`:

```python
OUTPUT_DIR = Path("assets/screenshots")  # Save here instead
```

### Adjust Viewport Size

Edit `VIEWPORT`:

```python
VIEWPORT = {"width": 1280, "height": 720}  # Smaller size
```

### Take Component Screenshots

For specific components, use CSS selectors:

```python
# Example: Screenshot just the sidebar
element = await page.query_selector('[data-testid="stSidebar"]')
await element.screenshot(path="sidebar.png")
```

---

## Alternative: Manual Screenshots

If automation fails, see `docs/SCREENSHOT_GUIDE.md` for manual capture instructions.

**Quick manual method:**

1. Open app: `http://localhost:8501`
2. Navigate to desired page
3. Use browser dev tools (`F12` → `Ctrl+Shift+P` → "Capture full size screenshot")
4. Save to `docs/screenshots/`

---

## Output Structure

```
docs/
└── screenshots/
    ├── 01_light_theme_main.png       # Market Pulse, light theme
    ├── 02_dark_theme_main.png        # Market Pulse, dark theme
    ├── 03_design_system_light.png    # Design System, light theme
    └── 04_design_system_dark.png     # Design System, dark theme
```

---

## CI/CD Integration

To generate screenshots in CI (e.g., GitHub Actions):

```yaml
- name: Install Playwright
  run: |
    pip install playwright
    playwright install chromium --with-deps

- name: Start Streamlit
  run: streamlit run app.py &

- name: Wait for app
  run: sleep 10

- name: Capture screenshots
  run: python3 assets/capture_screenshots_simple.py

- name: Upload screenshots
  uses: actions/upload-artifact@v3
  with:
    name: screenshots
    path: docs/screenshots/
```

---

## Dependencies

**For Playwright scripts:**
```bash
pip install playwright
playwright install chromium
```

**For Selenium script:**
```bash
pip install selenium webdriver-manager
```

**For all scripts:**
Already included in main `requirements.txt`:
- `streamlit`
- Python 3.8+

---

## License

Same as main project.
