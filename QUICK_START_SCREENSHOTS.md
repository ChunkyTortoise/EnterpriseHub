# Quick Start: Screenshot Capture

Automated screenshot generation for UI/UX documentation.

## Prerequisites (One-Time Setup)

```bash
# Install Playwright browsers
playwright install chromium
```

## Capture Screenshots

### Option 1: Automated (Recommended)

```bash
# Terminal 1: Start Streamlit
streamlit run app.py

# Terminal 2: Run screenshot script
python3 assets/capture_screenshots_simple.py
```

**Output:** `docs/screenshots/` (4 screenshots: light/dark themes + design system)

### Option 2: Manual

1. Start Streamlit: `streamlit run app.py`
2. Open `http://localhost:8501`
3. Use browser screenshot tool:
   - Chrome: `F12` → `Ctrl+Shift+P` → "Capture full size screenshot"
   - Firefox: `F12` → `...` menu → "Take a screenshot"

**Capture these views:**
- Market Pulse (Light theme) → save as `01_light_theme_main.png`
- Market Pulse (Dark theme) → save as `02_dark_theme_main.png`
- Design System (Light theme) → save as `03_design_system_light.png`
- Design System (Dark theme) → save as `04_design_system_dark.png`

**Save to:** `docs/screenshots/`

## Troubleshooting

**Playwright not installed:**
```bash
pip install playwright
playwright install chromium
```

**Streamlit not running:**
```bash
streamlit run app.py
# Wait for browser to open, then run screenshot script
```

**Screenshots failed:**
```bash
# Enable debug mode (shows browser)
# Edit assets/capture_screenshots_simple.py
# Change: headless=False
```

## Documentation

- **Detailed Guide:** `docs/SCREENSHOTS.md`
- **Manual Instructions:** `docs/SCREENSHOT_GUIDE.md`
- **Script Docs:** `assets/README.md`

## Files Created

```
docs/screenshots/
├── 01_light_theme_main.png       # Market Pulse (light)
├── 02_dark_theme_main.png        # Market Pulse (dark)
├── 03_design_system_light.png    # Design System (light)
└── 04_design_system_dark.png     # Design System (dark)
```

---

**That's it!** Screenshots are ready for documentation.
