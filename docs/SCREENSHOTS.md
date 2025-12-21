# Screenshot Documentation

This document provides instructions for capturing UI/UX screenshots for the EnterpriseHub documentation.

## Overview

We maintain screenshots for:
1. **Light Theme** - Showcasing the default light mode interface
2. **Dark Theme** - Demonstrating dark mode accessibility
3. **Design System Gallery** - Component showcase and design tokens

## Automated Capture (Recommended)

### Prerequisites

**One-time setup:**
```bash
# Install Playwright browsers
playwright install chromium
```

### Running the Script

**Step 1: Start Streamlit**
```bash
streamlit run app.py
```

Wait for the app to open in your browser (`http://localhost:8501`).

**Step 2: Run Screenshot Script**

In a new terminal:
```bash
python3 assets/capture_screenshots_simple.py
```

### Expected Output

```
======================================================================
EnterpriseHub Screenshot Automation
======================================================================

📁 Output: /path/to/docs/screenshots

🌐 Launching browser...
✓ Browser ready

🔗 Opening: http://localhost:8501
  ⏳ Waiting for Streamlit to load...
  ✓ Streamlit loaded

[1/4] 01_light_theme_main.png
  🎨 Switching to light theme...
  ✓ Light theme activated
  📍 Navigating to: Market Pulse
  ✓ Loaded Market Pulse
  📸 Capturing: 01_light_theme_main.png
  ✓ Saved: 01_light_theme_main.png

[2/4] 02_dark_theme_main.png
  🎨 Switching to dark theme...
  ✓ Dark theme activated
  📍 Navigating to: Market Pulse
  ✓ Loaded Market Pulse
  📸 Capturing: 02_dark_theme_main.png
  ✓ Saved: 02_dark_theme_main.png

[3/4] 03_design_system_light.png
  🎨 Switching to light theme...
  ✓ Light theme activated
  📍 Navigating to: Design System
  ✓ Loaded Design System
  📸 Capturing: 03_design_system_light.png
  ✓ Saved: 03_design_system_light.png

[4/4] 04_design_system_dark.png
  🎨 Switching to dark theme...
  ✓ Dark theme activated
  📍 Navigating to: Design System
  ✓ Loaded Design System
  📸 Capturing: 04_design_system_dark.png
  ✓ Saved: 04_design_system_dark.png

======================================================================
✅ Complete! 4/4 screenshots captured
📁 Location: /path/to/docs/screenshots
======================================================================
```

### Output Files

Screenshots are saved to `docs/screenshots/`:

| File | Description | Size |
|------|-------------|------|
| `01_light_theme_main.png` | Market Pulse in light theme | 1920x1080+ |
| `02_dark_theme_main.png` | Market Pulse in dark theme | 1920x1080+ |
| `03_design_system_light.png` | Design System Gallery (light) | 1920x1080+ |
| `04_design_system_dark.png` | Design System Gallery (dark) | 1920x1080+ |

---

## Manual Capture (Fallback)

If automation fails, use manual capture:

### Setup

1. Open Streamlit app: `streamlit run app.py`
2. Navigate to `http://localhost:8501`
3. Set browser window to 1920x1080

### Browser Screenshot Tools

**Chrome/Edge:**
1. Press `F12` to open DevTools
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
3. Type "screenshot"
4. Select "Capture full size screenshot"
5. Save to `docs/screenshots/`

**Firefox:**
1. Press `F12` to open DevTools
2. Click `...` (more tools) menu
3. Select "Take a screenshot"
4. Click "Save full page"
5. Save to `docs/screenshots/`

**Safari:**
1. Enable Developer Menu: Preferences → Advanced → "Show Develop menu"
2. Develop → Show Web Inspector
3. File → Export as Image → Full Size
4. Save to `docs/screenshots/`

### Capture Steps

**1. Light Theme - Main Page**
```
→ Ensure light theme is active (☀️ Light button)
→ Navigate to "📊 Market Pulse"
→ Wait for data to load
→ Capture full-page screenshot
→ Save as: docs/screenshots/01_light_theme_main.png
```

**2. Dark Theme - Main Page**
```
→ Click "🌙 Dark" button in sidebar
→ Navigate to "📊 Market Pulse"
→ Wait for data to load
→ Capture full-page screenshot
→ Save as: docs/screenshots/02_dark_theme_main.png
```

**3. Design System - Light Theme**
```
→ Click "☀️ Light" button in sidebar
→ Navigate to "🎨 Design System"
→ Ensure you're on the "🎨 Colors" tab
→ Scroll to top
→ Capture full-page screenshot
→ Save as: docs/screenshots/03_design_system_light.png
```

**4. Design System - Dark Theme**
```
→ Click "🌙 Dark" button in sidebar
→ Navigate to "🎨 Design System"
→ Ensure you're on the "🎨 Colors" tab
→ Scroll to top
→ Capture full-page screenshot
→ Save as: docs/screenshots/04_design_system_dark.png
```

### Quality Checklist

Before saving each screenshot:

- [ ] Correct module is displayed
- [ ] Correct theme is active (check background color)
- [ ] Page is fully loaded (no spinners/loading indicators)
- [ ] Data is visible (charts, metrics loaded)
- [ ] No personal data visible (API keys, real data)
- [ ] Viewport is 1920x1080 or wider
- [ ] Streamlit hamburger menu is hidden (if possible)
- [ ] File naming matches convention

---

## Advanced Usage

### Debugging Failed Captures

**Enable visual mode:**

Edit `assets/capture_screenshots_simple.py`:

```python
browser = await p.chromium.launch(
    headless=False,  # Show browser window
    slow_mo=1000     # Slow down by 1 second per action
)
```

Run script again to watch it work.

**Increase wait times:**

If pages aren't loading fully:

```python
await asyncio.sleep(5)  # Increase from 3 to 5 seconds
```

**Check console output:**

```python
page.on('console', lambda msg: print(f'BROWSER: {msg.text}'))
page.on('pageerror', lambda exc: print(f'ERROR: {exc}'))
```

### Capture Additional Screenshots

Edit `CAPTURES` in `assets/capture_screenshots_simple.py`:

```python
CAPTURES = [
    # Standard screenshots
    ("Market Pulse", "light", "01_light_theme_main.png"),
    ("Market Pulse", "dark", "02_dark_theme_main.png"),
    ("Design System", "light", "03_design_system_light.png"),
    ("Design System", "dark", "04_design_system_dark.png"),

    # Add more modules
    ("Financial Analyst", "light", "05_financial_analyst_light.png"),
    ("Content Engine", "light", "06_content_engine_light.png"),
    ("Data Detective", "dark", "07_data_detective_dark.png"),
]
```

### Custom Viewport Sizes

For responsive design testing:

```python
# Mobile
VIEWPORT = {"width": 375, "height": 667}

# Tablet
VIEWPORT = {"width": 768, "height": 1024}

# Desktop
VIEWPORT = {"width": 1920, "height": 1080}

# 4K
VIEWPORT = {"width": 3840, "height": 2160}
```

### Capture Specific Components

For design system docs:

```python
# Screenshot a specific element
element = await page.query_selector('.metric-card')
await element.screenshot(path='metric_card.png')

# Screenshot the sidebar
sidebar = await page.query_selector('[data-testid="stSidebar"]')
await sidebar.screenshot(path='sidebar.png')

# Screenshot a chart
chart = await page.query_selector('[data-testid="stPlotlyChart"]')
await chart.screenshot(path='chart.png')
```

---

## Image Optimization

Screenshots can be large. Optimize before committing:

### Using ImageMagick

```bash
# Compress all PNGs (quality 85%)
mogrify -quality 85 docs/screenshots/*.png

# Resize to max width 1600px
mogrify -resize 1600x docs/screenshots/*.png

# Convert to WebP (smaller file size)
for file in docs/screenshots/*.png; do
  cwebp -q 85 "$file" -o "${file%.png}.webp"
done
```

### Using pngquant

```bash
# Lossy compression (good quality, smaller size)
pngquant --quality 65-80 docs/screenshots/*.png --ext .png --force
```

### Using Python (Pillow)

```python
from PIL import Image

for png_file in Path('docs/screenshots').glob('*.png'):
    img = Image.open(png_file)
    # Resize if too large
    if img.width > 1600:
        ratio = 1600 / img.width
        new_size = (1600, int(img.height * ratio))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    # Save with optimization
    img.save(png_file, optimize=True, quality=85)
```

---

## Git Best Practices

### .gitignore

If you regenerate screenshots frequently, consider:

```gitignore
# docs/screenshots/*.png  # Ignore all screenshots
docs/screenshots/*_temp.png  # Ignore temp screenshots
```

### Git LFS

For large binary files:

```bash
# Install Git LFS
git lfs install

# Track PNG files
git lfs track "docs/screenshots/*.png"

# Commit
git add .gitattributes
git add docs/screenshots/*.png
git commit -m "Add UI/UX screenshots"
```

### Commit Message Convention

```bash
git commit -m "docs: add UI/UX screenshots (light/dark themes + design system)"
```

---

## Usage in Documentation

### Markdown

```markdown
## Light Theme
![Light Theme](screenshots/01_light_theme_main.png)

## Dark Theme
![Dark Theme](screenshots/02_dark_theme_main.png)

## Design System
![Design System Colors](screenshots/03_design_system_light.png)
```

### HTML (with sizing)

```html
<img src="screenshots/01_light_theme_main.png" alt="Light Theme" width="800">
```

### Side-by-side Comparison

```markdown
| Light Theme | Dark Theme |
|-------------|------------|
| ![Light](screenshots/01_light_theme_main.png) | ![Dark](screenshots/02_dark_theme_main.png) |
```

---

## CI/CD Automation

Generate screenshots in GitHub Actions:

```yaml
name: Generate Screenshots

on:
  push:
    paths:
      - 'modules/**'
      - 'utils/ui.py'

jobs:
  screenshots:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install playwright
          playwright install chromium --with-deps

      - name: Start Streamlit
        run: |
          streamlit run app.py &
          sleep 15

      - name: Generate screenshots
        run: python3 assets/capture_screenshots_simple.py

      - name: Upload screenshots
        uses: actions/upload-artifact@v3
        with:
          name: ui-screenshots
          path: docs/screenshots/

      - name: Commit screenshots
        run: |
          git config user.name "GitHub Actions"
          git config user.email "actions@github.com"
          git add docs/screenshots/
          git commit -m "docs: update UI screenshots [skip ci]" || true
          git push || true
```

---

## Troubleshooting

### Common Issues

**1. "Streamlit app failed to load"**
```bash
# Check if Streamlit is running
lsof -i :8501

# If not, start it
streamlit run app.py
```

**2. "Theme button not found"**
```bash
# Verify theme buttons exist in sidebar
# Check app.py for current implementation
grep -A 5 "theme" app.py
```

**3. "Module not found in navigation"**
```bash
# Check module names in app.py
grep "MODULES" app.py -A 15
```

**4. "Playwright not installed"**
```bash
pip install playwright
playwright install chromium
```

**5. "Screenshots are blank"**
```bash
# Increase wait times in script
# Or run with headless=False to debug visually
```

### Getting Help

1. Check `assets/README.md` for script documentation
2. See `docs/SCREENSHOT_GUIDE.md` for detailed manual instructions
3. Run `python3 assets/test_playwright.py` to verify Playwright installation
4. Open an issue with error logs

---

## Reference

- **Scripts**: `assets/capture_screenshots_simple.py`, `assets/capture_screenshots.py`
- **Detailed Guide**: `docs/SCREENSHOT_GUIDE.md`
- **Asset README**: `assets/README.md`
- **Output Directory**: `docs/screenshots/`

---

**Last Updated**: 2025-12-20
