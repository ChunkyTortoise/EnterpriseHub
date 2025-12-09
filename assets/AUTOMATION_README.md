# Automated Screenshot Capture

## Quick Start (5 Minutes)

### Step 1: Install Dependencies
```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/assets
chmod +x setup_screenshot_automation.sh
./setup_screenshot_automation.sh
```

This installs:
- `playwright` (browser automation)
- `pillow` (image optimization)
- Chromium browser

### Step 2: Run the Script
```bash
python3 auto_screenshot.py
```

You'll be prompted:
```
🔑 Optional: Enter Anthropic API key for Content Engine/Data Detective
   (Press Enter to skip AI-powered screenshots)
API Key:
```

- **With API key:** Captures Content Engine output and Data Detective AI insights
- **Without API key:** Skips AI-powered screenshots (you'll need to capture 3 manually later)

### Step 3: Watch It Work
The script will:
1. Open Chrome browser (you'll see it navigate automatically)
2. Visit your live demo
3. Click through modules
4. Fill in inputs
5. Take screenshots
6. Optimize images
7. Save to `/assets/screenshots/`

**Time:** 5-10 minutes total

---

## What Gets Captured Automatically

### ✅ Fully Automated (12 screenshots)

**Margin Hunter (3):**
- ✓ margin-hunter-dashboard.png
- ✓ margin-hunter-heatmap.png
- ✓ margin-hunter-scenarios.png

**Market Pulse (1):**
- ✓ market-pulse-4panel.png

**Marketing Analytics (4):**
- ✓ marketing-analytics-dashboard.png
- ✓ marketing-analytics-ab-test.png
- ✓ marketing-analytics-roi-heatmap.png
- ✓ marketing-analytics-attribution.png

**Content Engine (2-3):**
- ✓ content-engine-full.png
- ✓ content-engine-templates.png
- ✓ content-engine-output.png (only if API key provided)

**Financial Analyst (1):**
- ✓ financial-analyst-metrics.png

### ⚠️ Manual Required (3 screenshots)

**Data Detective (3):** Requires CSV file upload
- ❌ data-detective-profile.png
- ❌ data-detective-heatmap.png
- ❌ data-detective-ai.png

**Why manual?** File upload dialogs can't be automated without actual files on disk.

**Solution:** Use `SCREENSHOT_CHECKLIST.md` Phase 2 (15 minutes) to capture these 3 manually.

---

## Customization Options

### Run in Background (Headless Mode)
Edit `auto_screenshot.py` line 284:
```python
browser = await p.chromium.launch(headless=True)  # No browser window
```

### Change Resolution
Edit `auto_screenshot.py` line 17:
```python
VIEWPORT_SIZE = {"width": 2560, "height": 1440}  # 2K resolution
```

### Adjust Wait Times
If screenshots are blank (charts not rendered):
```python
await asyncio.sleep(5)  # Increase from 3 to 5 seconds
```

### Skip Optimization
Comment out line in each `capture_*` function:
```python
# await optimize_image(screenshot_path)
```

---

## Troubleshooting

### Issue: "Module 'playwright' not found"
**Solution:**
```bash
pip install playwright
playwright install chromium
```

### Issue: Browser opens but nothing happens
**Solution:** Your live demo might be slow. Edit wait times:
```python
# Line 31: Increase timeout
await page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=20000)
```

### Issue: Screenshots are blank
**Solution:** Streamlit needs more time to render. Increase sleep:
```python
await asyncio.sleep(8)  # Increase from 3
```

### Issue: "Can't find input field"
**Solution:** Streamlit selectors changed. Run in non-headless mode:
```python
browser = await p.chromium.launch(headless=False)
```
Then watch where it fails and update the selector.

### Issue: Script hangs
**Solution:** Kill it (Ctrl+C) and run again with:
```bash
python3 auto_screenshot.py 2>&1 | tee screenshot_log.txt
```
This logs output so you can see where it stuck.

---

## Manual Screenshot Guide

For the 3 Data Detective screenshots:

### 1. Prepare Sample CSV
Create `sample_data.csv`:
```csv
Date,Product,Region,Revenue,Units,Customer_Type
2024-01-01,Widget A,North,1500,50,Business
2024-01-02,Widget B,South,2300,75,Consumer
2024-01-03,Widget A,East,1800,60,Business
...
```
(Add 100+ rows with varied data)

### 2. Navigate to Data Detective
1. Open https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/
2. Click "Data Detective" in sidebar
3. Upload `sample_data.csv`

### 3. Screenshot #1: Data Profile
- Wait for auto-profiling (5-10 seconds)
- Scroll to top
- Screenshot: **data-detective-profile.png**

### 4. Screenshot #2: Correlation Heatmap
- Scroll to "Correlation Matrix" section
- Wait for heatmap to render
- Screenshot: **data-detective-heatmap.png**

### 5. Screenshot #3: AI Insights
- Click "AI Insights" tab
- Enter API key (if prompted)
- Click "Generate Insights"
- Wait 5-10 seconds
- Screenshot: **data-detective-ai.png**

---

## File Organization

After running, you'll have:

```
/assets/screenshots/
├── marketing/
│   ├── marketing-analytics-dashboard.png
│   ├── marketing-analytics-roi-heatmap.png
│   ├── marketing-analytics-ab-test.png
│   ├── marketing-analytics-attribution.png
│   ├── content-engine-full.png
│   ├── content-engine-templates.png
│   └── content-engine-output.png
├── bi/
│   ├── margin-hunter-dashboard.png
│   ├── margin-hunter-heatmap.png
│   ├── margin-hunter-scenarios.png
│   ├── market-pulse-4panel.png
│   ├── financial-analyst-metrics.png
│   ├── data-detective-profile.png (manual)
│   ├── data-detective-heatmap.png (manual)
│   └── data-detective-ai.png (manual)
└── hero/
    └── (empty - copy best screenshot here)
```

---

## Git Commit

After all screenshots are captured:

```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub

# Review screenshots
open assets/screenshots/marketing/
open assets/screenshots/bi/

# Commit
git add assets/screenshots/
git commit -m "Add automated portfolio screenshots

- 12 automated: Margin Hunter, Market Pulse, Marketing Analytics, Content Engine, Financial Analyst
- 3 manual: Data Detective (requires CSV upload)
- Organized by niche (marketing/, bi/)
- Optimized file sizes (<500KB each)
"

git push origin main
```

---

## Next Steps After Screenshots

1. **Verify on GitHub:**
   https://github.com/ChunkyTortoise/enterprise-hub/tree/main/assets/screenshots

2. **Use in Upwork proposals:**
   - Open `UPWORK_PROPOSALS.md`
   - Attach 2-3 screenshots per proposal

3. **Post to LinkedIn:**
   - Open `LINKEDIN_POSTS.md`
   - Use Post #1 with `market-pulse-4panel.png`

4. **Record demo video:**
   - Open `DEMO_VIDEO_GUIDE.md`
   - Use screenshots as B-roll reference

---

## Advanced: Batch Screenshot Multiple Environments

To capture staging, production, local:

```python
# Edit auto_screenshot.py
ENVIRONMENTS = {
    "production": "https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/",
    "staging": "https://staging-enterprise-hub.streamlit.app/",
    "local": "http://localhost:8501",
}

for env, url in ENVIRONMENTS.items():
    print(f"Capturing {env}...")
    # Run screenshot logic
```

---

## FAQ

**Q: Can I run this on Windows?**
A: Yes! Just use `python` instead of `python3` and the script works identically.

**Q: Can I schedule this to run daily?**
A: Yes! Use cron (Mac/Linux) or Task Scheduler (Windows):
```bash
# Run every night at 2 AM
0 2 * * * cd /path/to/EnterpriseHub/assets && python3 auto_screenshot.py
```

**Q: Can I screenshot specific modules only?**
A: Yes! Comment out functions you don't need:
```python
# await capture_market_pulse(page, SCREENSHOTS_DIR)  # Skip this
await capture_margin_hunter(page, SCREENSHOTS_DIR)  # Keep this
```

**Q: Can I use this for other Streamlit apps?**
A: Yes! Just change `DEMO_URL` and update the selectors in each `capture_*` function.

**Q: What if my demo has authentication?**
A: Add login before screenshot capture:
```python
await page.goto(DEMO_URL)
await page.fill('input[name="username"]', "your_username")
await page.fill('input[name="password"]', "your_password")
await page.click('button[type="submit"]')
await wait_for_streamlit_ready(page)
```

---

## Performance Metrics

**Manual (from SCREENSHOT_CHECKLIST.md):**
- Setup: 5 min
- Phase 1: 30 min
- Phase 2: 45 min
- Phase 3: 15 min
- **Total: 95 minutes**

**Automated (this script):**
- Setup: 2 min (one-time)
- Run script: 5-10 min
- Manual 3 screenshots: 15 min
- **Total: 20-25 minutes**

**Time saved: 70 minutes (73% faster)**

---

## Support

Issues? Check:
1. Python version: `python3 --version` (need 3.8+)
2. Dependencies: `pip list | grep playwright`
3. Browser: `playwright show-trace` (debug tool)

Still stuck? Review the console output - it tells you exactly what failed.
