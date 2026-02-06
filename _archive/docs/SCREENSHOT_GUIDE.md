# Screenshot Capture Guide

This guide covers both automated and manual screenshot capture for UI/UX documentation.

## Automated Capture (Recommended)

### Prerequisites

1. **Install Playwright browsers** (one-time setup):
   ```bash
   playwright install chromium
   ```

2. **Start Streamlit app**:
   ```bash
   streamlit run app.py
   ```

3. **Run screenshot script**:
   ```bash
   python3 assets/capture_screenshots.py
   ```

### Output

Screenshots are saved to `docs/screenshots/`:
- `light_theme_main.png` - Main page in light theme
- `dark_theme_main.png` - Main page in dark theme
- `design_system_light.png` - Design System Gallery in light theme
- `design_system_dark.png` - Design System Gallery in dark theme

### Troubleshooting

**Issue: Theme toggle not working automatically**

The script attempts to find and click theme toggle buttons, but if your UI structure is different, you may need to:

1. Edit `assets/capture_screenshots.py`
2. Update the `toggle_theme()` function with the correct selector
3. Or use manual capture (see below)

**Issue: Module not found**

Verify the module name in the script matches your sidebar navigation exactly. Check `MODULES` dict in `app.py`.

---

## Manual Capture (Fallback)

If automated capture fails, use these manual steps:

### Setup

1. Start the app: `streamlit run app.py`
2. Open browser to `http://localhost:8501`
3. Set browser window to 1920x1080 for consistency
4. Use browser's built-in screenshot tool:
   - **Chrome/Edge**: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac) → "Capture full size screenshot"
   - **Firefox**: `F12` → Click `...` menu → "Take a screenshot" → "Save full page"

### Screenshots Needed

#### 1. Light Theme - Main Page

1. Ensure light theme is active (check sidebar)
2. Navigate to "Market Pulse" or your default landing module
3. Wait for data to load fully
4. Capture screenshot
5. Save as: `docs/screenshots/light_theme_main.png`

#### 2. Dark Theme - Main Page

1. **Toggle to dark theme** via sidebar control
2. Navigate to "Market Pulse" (same as light theme)
3. Wait for data to load fully
4. Capture screenshot
5. Save as: `docs/screenshots/dark_theme_main.png`

#### 3. Design System Gallery - Light Theme

1. **Toggle to light theme** via sidebar control
2. Navigate to "🎨 Design System" in sidebar
3. Ensure you're on the **"🎨 Colors"** tab
4. Scroll to top of page
5. Capture screenshot
6. Save as: `docs/screenshots/design_system_light.png`

#### 4. Design System Gallery - Dark Theme

1. **Toggle to dark theme** via sidebar control
2. Navigate to "🎨 Design System" in sidebar (if not already there)
3. Ensure you're on the **"🎨 Colors"** tab
4. Scroll to top of page
5. Capture screenshot
6. Save as: `docs/screenshots/design_system_dark.png`

### Quality Checklist

Before saving screenshots, verify:

- [ ] Full page is visible (no cut-off content)
- [ ] Correct theme is active (check background color)
- [ ] No loading spinners or "Loading..." text visible
- [ ] Data is fully loaded (charts, metrics, etc.)
- [ ] No personal data visible (if using real API keys)
- [ ] Consistent viewport size (1920x1080)
- [ ] File saved with correct name

---

## Advanced: Custom Screenshot Script

If you need to customize the automation:

### Edit Theme Toggle Logic

The theme toggle detection in `capture_screenshots.py` is a best-effort attempt. Update the `toggle_theme()` function if needed:

```python
async def toggle_theme(page, target_theme: str):
    """Toggle between light and dark theme."""
    # Option 1: Find by button text
    theme_button = await page.query_selector('button:has-text("Toggle Theme")')
    if theme_button:
        await theme_button.click()

    # Option 2: Find by CSS selector
    theme_toggle = await page.query_selector('[data-testid="theme-toggle"]')
    if theme_toggle:
        await theme_toggle.click()

    # Option 3: Use Streamlit session state (if exposed)
    await page.evaluate('window.streamlitController.setTheme("dark")')

    await asyncio.sleep(1)
    return True
```

### Add More Screenshots

Edit the `SCREENSHOTS` list in `capture_screenshots.py`:

```python
SCREENSHOTS = [
    # Existing screenshots...
    {
        "name": "05_financial_analyst",
        "description": "Financial Analyst Module - Light Theme",
        "module": "Financial Analyst",
        "theme": "light",
        "filename": "financial_analyst_light.png"
    },
]
```

### Debug Mode

For visual debugging, change `headless=False` in the script:

```python
browser = await p.chromium.launch(
    headless=False,  # Shows browser window
    slow_mo=1000     # Slows down actions by 1 second
)
```

---

## Alternative: Selenium-Based Capture

If Playwright doesn't work, use the existing Selenium script:

```bash
# Install dependencies
pip install selenium webdriver-manager

# Run
python3 assets/selenium_screenshot.py
```

**Note**: The existing `selenium_screenshot.py` captures all modules but doesn't handle theme switching. You'll need to enhance it or use manual capture for theme screenshots.

---

## Screenshot Storage

### Recommended Structure

```
docs/
└── screenshots/
    ├── light_theme_main.png
    ├── dark_theme_main.png
    ├── design_system_light.png
    ├── design_system_dark.png
    └── modules/
        ├── market_pulse_light.png
        ├── market_pulse_dark.png
        ├── financial_analyst_light.png
        └── ... (other modules)
```

### Git Considerations

Screenshots can be large files. Consider:

1. **Add to .gitignore** if you regenerate frequently:
   ```
   docs/screenshots/*.png
   ```

2. **Use Git LFS** for version control:
   ```bash
   git lfs track "docs/screenshots/*.png"
   ```

3. **Compress images** before committing:
   ```bash
   # Using ImageMagick
   mogrify -quality 85 docs/screenshots/*.png

   # Using pngquant
   pngquant --quality 65-80 docs/screenshots/*.png
   ```

---

## Usage in Documentation

Once captured, reference screenshots in markdown:

```markdown
### Light Theme
![Light Theme](screenshots/light_theme_main.png)

### Dark Theme
![Dark Theme](screenshots/dark_theme_main.png)

### Design System
![Design System](screenshots/design_system_light.png)
```

For README badges or thumbnails, consider creating smaller versions:

```bash
# Create 600px wide thumbnails
convert docs/screenshots/light_theme_main.png \
  -resize 600x \
  docs/screenshots/light_theme_main_thumb.png
```

---

## Appendix: Playwright Installation Issues

If `playwright install` fails:

### macOS
```bash
# Install system dependencies
brew install --cask playwright

# Or use system Python
python3 -m playwright install chromium
```

### Linux
```bash
# Install dependencies
sudo apt-get install libnss3 libatk-bridge2.0-0 libdrm2 libxkbcommon0 libgbm1

# Install browsers
playwright install chromium
```

### Windows
```bash
# Run as administrator
python -m playwright install chromium
```

### Minimal Installation

If full Playwright is too heavy, use Firefox (smaller):

```bash
playwright install firefox
```

Then update the script to use `p.firefox.launch()`.

---

**Questions?** Check the [Playwright Documentation](https://playwright.dev/python/) or use manual capture.
