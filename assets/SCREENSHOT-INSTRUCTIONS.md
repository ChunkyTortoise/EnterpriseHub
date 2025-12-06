# 📸 Screenshot Instructions for Margin Hunter

To complete the Margin Hunter hero project marketing, please capture the following screenshots from the live demo.

---

## 🎯 Required Screenshots

### 1. `margin-hunter-dashboard.png` (PRIMARY - Hero Screenshot)

**URL**: https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/
**Navigate to**: 💰 Margin Hunter page

**Setup**:
Use these example values to showcase a compelling scenario (SaaS pricing):
```
Unit Selling Price: $99.00
Unit Variable Cost: $18.00
Total Fixed Costs: $75,000.00
Target Profit: $25,000.00
Current Sales (Units): 1,100
```

**What to capture**:
- Full page view showing:
  - Left panel: All input parameters (⚙️ Parameters section)
  - Right panel: Analysis Results with all 6 metrics
  - CVP Chart (green revenue line crossing red cost line)
  - Sensitivity heatmap (colorful grid)
  - Scenarios table at bottom

**Settings**:
- Browser: Chrome or Firefox (clean UI, no extensions visible)
- Window size: 1920x1080 (or similar 16:9 ratio)
- Zoom: 100% (default)
- Remove browser address bar via F11 fullscreen (optional but cleaner)

**Tips**:
- Make sure all text is readable
- Ensure the break-even point "star" is visible on the CVP chart
- Heatmap should show full color gradient (green to red)
- Take screenshot AFTER all charts have fully loaded

---

### 2. `margin-hunter-heatmap.png` (SECONDARY - Detail Screenshot)

**Same setup as above**, but zoom in on the sensitivity heatmap section:

**What to capture**:
- 🌡️ Sensitivity Heatmap: Net Profit section
- The full heatmap grid (10x10)
- Axis labels (Unit Price on X, Variable Cost on Y)
- Color scale bar on the right
- Title and caption

**Window size**: Crop to just the heatmap area (approx 800x600px)

**Purpose**: Use in detailed documentation and presentations to highlight the sensitivity analysis feature

---

## 📱 Optional Screenshots (Bonus)

### 3. `margin-hunter-mobile.png`
- Capture on mobile device or responsive view (375x812 iPhone size)
- Shows mobile-friendly layout
- Same inputs as primary screenshot

### 4. `margin-hunter-ecommerce-scenario.png`
- Use E-Commerce scenario values:
```
Unit Selling Price: $59.99
Unit Variable Cost: $28.50
Total Fixed Costs: $18,000.00
Target Profit: $8,000.00
Current Sales (Units): 650
```

### 5. `margin-hunter-manufacturing-scenario.png`
- Use Manufacturing scenario values:
```
Unit Selling Price: $145.00
Unit Variable Cost: $82.00
Total Fixed Costs: $95,000.00
Target Profit: $40,000.00
Current Sales (Units): 2,100
```

---

## 🛠️ Screenshot Tools

### Recommended Tools:
1. **Windows**: Snipping Tool (Win + Shift + S) or Greenshot
2. **Mac**: Screenshot (Cmd + Shift + 4) or CleanShot X
3. **Linux**: GNOME Screenshot or Flameshot
4. **Browser Extension**: Awesome Screenshot, Nimbus Screenshot

### Settings:
- Format: PNG (lossless quality)
- File naming: Use exact names above (e.g., `margin-hunter-dashboard.png`)
- Location: Save to `enterprise-hub/assets/` directory

---

## ✅ After Taking Screenshots

1. **Save files** to `enterprise-hub/assets/` with exact filenames
2. **Verify image quality** - open each PNG and confirm text is readable
3. **Update README** - The main README already references these images
4. **Commit to GitHub**:
   ```bash
   cd ~/enterprise-hub
   git add assets/*.png
   git commit -m "Add Margin Hunter screenshots for hero project showcase"
   git push
   ```

5. **Verify on GitHub** - Visit your repo to confirm images display correctly in README

---

## 📏 Image Specifications

| Screenshot | Dimensions | Max File Size | Format |
|-----------|-----------|--------------|--------|
| margin-hunter-dashboard.png | 1920x1080 (or 16:9) | 2 MB | PNG |
| margin-hunter-heatmap.png | ~800x600 | 500 KB | PNG |
| margin-hunter-mobile.png | 375x812 | 300 KB | PNG |
| (scenario screenshots) | 1920x1080 | 2 MB | PNG |

**Optimization tip**: Use TinyPNG.com or ImageOptim to compress without quality loss

---

## 🎨 Visual Guidelines

### What Makes a Great Screenshot:
✅ Clean browser UI (no clutter, bookmarks bar hidden)
✅ All charts fully loaded and rendered
✅ Realistic, business-appropriate input values
✅ Results that tell a story (e.g., "close to break-even" or "highly profitable")
✅ Good contrast and readability

### What to Avoid:
❌ Partial chart rendering (wait for Plotly to finish)
❌ Browser dev tools visible
❌ Unrealistic values (e.g., $0 costs, $1M price)
❌ Error messages or warnings visible
❌ Personal information in browser (email, profile picture)

---

## 📊 Example Storytelling Scenarios

### SaaS Scenario (Current Default)
**Story**: "Early-stage SaaS company just reached profitability"
- Break-even: 926 customers
- Current: 1,100 customers
- Margin of Safety: 15.8% ✅ (healthy cushion)

### E-Commerce Scenario
**Story**: "Product is profitable but low margin of safety"
- Break-even: 632 units
- Current: 650 units
- Margin of Safety: 2.8% ⚠️ (vulnerable to sales drop)

### Manufacturing Scenario
**Story**: "Strong profitability with capacity headroom"
- Break-even: 1,508 meters
- Current: 2,100 meters
- Margin of Safety: 28.2% ✅ (excellent)

---

## 🚀 Timeline

**Estimated time**: 15-30 minutes for all screenshots

**Priority order**:
1. `margin-hunter-dashboard.png` (MUST HAVE - used in main README)
2. `margin-hunter-heatmap.png` (SHOULD HAVE - highlights key feature)
3. Optional scenario screenshots (NICE TO HAVE - for documentation)

---

**Questions?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues)

---

*Part of Priority 1: Deploy Hero (Margin Hunter) - 48-Hour Portfolio Sprint*
