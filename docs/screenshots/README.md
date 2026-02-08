# Screenshots Directory

This directory contains automated screenshots for UI/UX documentation.

## Quick Start

### Generate Screenshots

```bash
# 1. Start Streamlit (Terminal 1)
streamlit run app.py

# 2. Run automation (Terminal 2)
python3 assets/capture_screenshots_simple.py
```

## Expected Output

After running the automation script, this directory will contain:

```
docs/screenshots/
├── 01_light_theme_main.png       # Market Pulse - Light Theme (1920x1080+)
├── 02_dark_theme_main.png        # Market Pulse - Dark Theme (1920x1080+)
├── 03_design_system_light.png    # Design System - Light Theme (1920x1080+)
└── 04_design_system_dark.png     # Design System - Dark Theme (1920x1080+)
```

## File Naming Convention

Screenshots follow this pattern:
- **Prefix**: `01_`, `02_`, etc. (ordered by importance)
- **Theme**: `light_theme_` or `dark_theme_`
- **Subject**: Module or feature name
- **Extension**: `.png` (full quality)

## Screenshot Specifications

| Attribute | Value |
|-----------|-------|
| Format | PNG (lossless) |
| Minimum Width | 1920px |
| Minimum Height | 1080px |
| Color Depth | 24-bit RGB |
| Screenshot Type | Full page |
| Browser | Chromium (via Playwright) |

## Usage in Documentation

### Markdown

```markdown
## Light Theme
![Light Theme](docs/screenshots/01_light_theme_main.png)

## Dark Theme
![Dark Theme](docs/screenshots/02_dark_theme_main.png)
```

### HTML

```html
<img src="docs/screenshots/01_light_theme_main.png"
     alt="Enterprise Hub - Light Theme"
     width="800">
```

### Side-by-Side Comparison

```markdown
| Light | Dark |
|-------|------|
| ![Light](docs/screenshots/01_light_theme_main.png) | ![Dark](docs/screenshots/02_dark_theme_main.png) |
```

## Regenerating Screenshots

Screenshots should be regenerated when:
- UI/UX design changes
- New components added to Design System
- Color scheme updates
- Layout modifications

**To regenerate:**
```bash
# Remove old screenshots
rm docs/screenshots/*.png

# Generate new ones
python3 assets/capture_screenshots_simple.py
```

## Manual Capture (Fallback)

If automation fails:

1. Open app: `http://localhost:8501`
2. Navigate to module
3. Switch theme (☀️ Light or 🌙 Dark button in sidebar)
4. Use browser screenshot:
   - **Chrome**: F12 → Ctrl+Shift+P → "Capture full size screenshot"
   - **Firefox**: F12 → ... menu → "Take a screenshot"
5. Save to this directory

See [docs/screenshots/MODULE_SCREENSHOTS.md](MODULE_SCREENSHOTS.md) for complete screenshot documentation.

## Optimization

For smaller file sizes (web use):

```bash
# Compress PNGs
pngquant --quality 65-80 *.png --ext .png --force

# Resize for web
mogrify -resize 1600x *.png

# Convert to WebP
for f in *.png; do cwebp -q 85 "$f" -o "${f%.png}.webp"; done
```

## Git Considerations

Screenshots are binary files and can be large. Options:

### Option 1: Track in Git (Small Projects)
```bash
git add docs/screenshots/*.png
git commit -m "docs: update UI screenshots"
```

### Option 2: Use Git LFS (Recommended for Large Projects)
```bash
git lfs track "docs/screenshots/*.png"
git add .gitattributes
git add docs/screenshots/*.png
git commit -m "docs: update UI screenshots"
```

### Option 3: Ignore (Regenerate in CI)
```gitignore
# .gitignore
docs/screenshots/*.png
```

Then regenerate in CI/CD pipeline.

## CI/CD Integration

Example GitHub Actions workflow:

```yaml
- name: Generate Screenshots
  run: |
    streamlit run app.py &
    sleep 15
    python3 assets/capture_screenshots_simple.py

- name: Upload Screenshots
  uses: actions/upload-artifact@v3
  with:
    name: ui-screenshots
    path: docs/screenshots/
```

## Troubleshooting

**No screenshots generated:**
- Check if Streamlit is running: `lsof -i :8501`
- Verify Playwright installed: `python3 -c "import playwright"`
- Run verification: `python3 assets/verify_screenshot_setup.py`

**Screenshots are blank:**
- Increase wait times in script
- Run with `headless=False` to debug visually

**Theme didn't switch:**
- Verify theme buttons exist in sidebar
- Check app.py for theme toggle implementation
- Use manual capture as fallback

## Documentation

- **Quick Start**: See [README.md](../README.md) for project setup
- **Comprehensive Guide**: [MODULE_SCREENSHOTS.md](MODULE_SCREENSHOTS.md) - Complete screenshot documentation
- **Asset Documentation**: [../../assets/README.md](../../assets/README.md) - Screenshot guidelines
- **Implementation Summary**: [SCREENSHOT_FIX_SUMMARY.md](SCREENSHOT_FIX_SUMMARY.md) - Screenshot creation report

## Verification

To verify setup before capturing:

```bash
python3 assets/verify_screenshot_setup.py
```

Expected output:
```
✓ Playwright
✓ Streamlit
✓ Output Directory
✓ Scripts
✓ Documentation
```

---

**Last Updated**: 2024-12-20
**Automation**: Playwright-based
**Maintainer**: See main repository
