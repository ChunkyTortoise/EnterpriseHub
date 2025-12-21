# Media Production Guide for EnterpriseHub

**Purpose:** Comprehensive instructions for creating visual assets (screenshots, videos, GIFs) to showcase the project on Upwork, LinkedIn, and GitHub.
**Last Updated:** December 21, 2025

---

## 📸 Part 1: Screenshot Guide

High-quality screenshots are critical for Upwork proposals. Clients ignore proposals without visual proof.

### 🎯 Required Screenshots Checklist

| Screenshot Name | Focus Module | Scenario to Capture |
|-----------------|--------------|---------------------|
| `margin-hunter-heatmap.png` | **Margin Hunter** | SaaS Pricing: $99 price, $18 cost, $75k fixed. Show sensitivity heatmap. |
| `market-pulse-4panel.png` | **Market Pulse** | SPY stock, 6-month view. Show Price, RSI, MACD, Volume. |
| `marketing-analytics-dashboard.png` | **Marketing Analytics** | Campaign Dashboard showing ROI, Spend, Revenue cards + Trend chart. |
| `data-detective-ai.png` | **Data Detective** | Upload CSV, show "AI Insights" tab with generated analysis. |
| `content-engine-output.png` | **Content Engine** | Generated LinkedIn post (topic: "AI in marketing") showing output text. |

### 🛠️ How to Capture (Best Practices)
1.  **Resolution**: 1920x1080 (Full HD).
2.  **Browser**: Use Chrome/Firefox in Incognito mode.
3.  **Clean UI**: Hide bookmarks bar (`Cmd+Shift+B` or `Ctrl+Shift+B`).
4.  **Zoom**: Set to 100% (`Cmd+0`).
5.  **Method**: Use "Capture full size screenshot" in DevTools or `Cmd+Shift+4` on Mac.

### 💾 Save Location
Save all images to: `assets/screenshots/`

---

## 🎥 Part 2: Demo Video Guide (60 Seconds)

A 60-second walkthrough is the highest-ROI asset for LinkedIn and Upwork portfolios.

### 🎬 Script (60-Second Narration)

**[0:00-0:05] Hook**
"I built what would cost $24,000 at Bloomberg - for free."
*(Visual: Market Pulse 4-panel chart)*

**[0:05-0:15] Margin Hunter**
"This is Margin Hunter. Financial modeling for product pricing. Break-even analysis, CVP charts, and 100 pricing scenarios visualized simultaneously."
*(Visual: Dashboard → Zoom to Heatmap)*

**[0:15-0:25] Marketing Analytics**
"Marketing Analytics tracks campaign ROI, A/B test significance, and five attribution models - from First-Touch to Position-Based."
*(Visual: Dashboard with 4 KPI cards)*

**[0:25-0:35] Data Detective**
"Data Detective automates exploratory data analysis. Upload a CSV, get AI-powered insights in 2 minutes instead of 2 hours."
*(Visual: Data Profile → AI Insights tab)*

**[0:35-0:45] Content Engine**
"Content Engine generates LinkedIn posts in 3 seconds using Claude AI. Cost: $0.003 per post versus $50 to $150 for human writers."
*(Visual: Click Generate → Show Output)*

**[0:45-0:55] Production Quality**
"Seven modules. 220 automated tests. 85% code coverage. Live on Streamlit Cloud."
*(Visual: Quick montage of modules → GitHub Actions passing)*

**[0:55-1:00] Call to Action**
"Link to live demo in the comments. Full source code on GitHub."
*(Visual: Homepage → Fade to text)*

### 🛠️ Recording Settings
-   **Resolution**: 1920x1080 (1080p)
-   **Frame Rate**: 30 FPS
-   **Format**: MP4 (H.264)
-   **Audio**: Clear voiceover (speak 20% slower than normal)

### 📤 Distribution
1.  **LinkedIn**: Upload natively (do not link YouTube). Add captions.
2.  **Upwork**: Add to "Portfolio" section.
3.  **YouTube**: Upload as "Unlisted" for embedding.

---

## 🎞️ Part 3: GIF Guide (GitHub README)

GIFs are essential for the GitHub README where videos don't autoplay.

### 🎯 Required GIFs
1.  **Margin Hunter Interaction**: Changing a price input and seeing the heatmap update (10 sec).
2.  **Content Engine Generation**: Clicking "Generate" and seeing text appear (10 sec).

### 🛠️ Tools
-   **Mac**: Kap or GIPHY Capture
-   **Windows**: ScreenToGif
-   **Size Limit**: Keep under 5MB for fast loading.

---

## 🤖 Part 4: Automated Screenshots (Optional)

If you have Playwright installed, you can automate screenshot capture:

```bash
# Terminal 1: Start App
streamlit run app.py

# Terminal 2: Run Script
python3 assets/capture_screenshots_simple.py
```
*Note: This generates theme-check screenshots in `docs/screenshots/`.*
