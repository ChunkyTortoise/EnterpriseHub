# Screenshot Capture Checklist - Step-by-Step Guide

## Pre-Capture Setup (5 minutes)

### Browser Configuration
- [ ] Open browser in **incognito/private mode** (clean screenshots, no extensions)
- [ ] Set window size to **1920x1080** resolution
- [ ] Set browser zoom to **100%** (CMD+0 / CTRL+0)
- [ ] Close all other tabs
- [ ] Disable browser extensions (for clean screenshots)

### Preparation
- [ ] Open live demo: https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/
- [ ] Verify Anthropic API key ready: `sk-ant-...`
- [ ] Prepare sample CSV file (for Data Detective):
  - Option 1: Use `/Users/Cave/Desktop/enterprise-hub/EnterpriseHub/scenarios/saas-pricing-template.md` data
  - Option 2: Download sample from Kaggle (sales data, 100+ rows, 10+ columns)
- [ ] Have screenshot tool ready:
  - macOS: CMD+SHIFT+4 (select area) or CMD+SHIFT+5 (full screen)
  - Windows: Snipping Tool or Windows+SHIFT+S
- [ ] Create save directories:
  ```bash
  cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/assets/screenshots
  mkdir -p marketing bi hero
  ```

---

## Phase 1: No API Required (30 minutes)

### Screenshot 1: Margin Hunter - Dashboard Full
**Time:** 5 min
**File:** `bi/margin-hunter-dashboard.png`

**Navigation:**
1. Open https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/
2. Wait for page to fully load
3. In sidebar, click **"Margin Hunter"**
4. Input the following values:
   - **Price per Unit:** $99
   - **Variable Cost per Unit:** $18
   - **Total Fixed Costs:** $75000
   - **Target Profit:** $25000
   - **Current Sales Volume:** 1100
5. Wait 2 seconds for charts to render
6. Scroll to top of page
7. Screenshot: Full view from "Margin Hunter" title down to top of CVP chart

**What should be visible:**
- Input panel with all values filled
- Contribution Margin card ($81 / 81.82%)
- Break-Even card (926 units / $91,674)
- Margin of Safety card ($8,326 / 8.33%)
- Operating Leverage card (1.11x)
- Top of CVP chart

**Screenshot tip:** Use CMD+SHIFT+4 (macOS) and drag from top-left to capture entire visible area. Don't include browser chrome.

---

### Screenshot 2: Margin Hunter - Heatmap Zoom
**Time:** 2 min
**File:** `bi/margin-hunter-heatmap.png`

**Navigation:**
1. Continue from previous screenshot (same module, same inputs)
2. Scroll down to "Sensitivity Analysis" section
3. Wait for heatmap to fully render (colors loaded)
4. Screenshot: Just the heatmap chart (not the full page)

**What should be visible:**
- Interactive Plotly heatmap
- Y-axis: Price per Unit ($90-$108)
- X-axis: Variable Cost per Unit ($16-$20)
- Color scale: red (loss) → yellow (break-even) → green (profit)
- Hover tooltip (if you hover before screenshot)

**Screenshot tip:** Get close on the heatmap - this is a hero visual.

---

### Screenshot 3: Margin Hunter - Scenarios Table
**Time:** 2 min
**File:** `bi/margin-hunter-scenarios.png`

**Navigation:**
1. Continue from previous (same module)
2. Scroll down to "Scenario Comparison" section
3. Screenshot: The 3-column table comparing Break-Even, Current, Target

**What should be visible:**
- Table with 3 scenarios
- Rows: Sales Volume, Revenue, Total Costs, Profit/Loss, Contribution Margin
- Clear profit progression: $0 → $14,400 → $25,000

---

### Screenshot 4: Market Pulse - 4-Panel Chart
**Time:** 5 min
**File:** `bi/market-pulse-4panel.png`

**Navigation:**
1. In sidebar, click **"Market Pulse"**
2. Input values:
   - **Ticker Symbol:** SPY
   - **Time Period:** 6 months
   - **Interval:** 1 day
3. Click **"Load Data"** button
4. Wait 3-5 seconds for all 4 panels to render
5. Scroll to see all 4 panels in one screenshot

**What should be visible:**
- Panel 1 (Top): Candlestick chart with 20-day MA (blue line)
- Panel 2: RSI indicator (purple line, 0-100 scale)
- Panel 3: MACD histogram (blue bars) with signal line (orange)
- Panel 4 (Bottom): Volume bars (green/red)
- All panels aligned vertically

**Screenshot tip:** This is a wide shot - capture from "SPY Price" title down to bottom of volume panel.

---

### Screenshot 5: Marketing Analytics - Dashboard
**Time:** 5 min
**File:** `marketing/marketing-analytics-dashboard.png`

**Navigation:**
1. In sidebar, click **"Marketing Analytics"**
2. Dashboard tab should load automatically (default)
3. Default filters are fine: "All Channels", "Last 30 Days"
4. Wait for demo data to populate (2 seconds)
5. Scroll to top

**What should be visible:**
- 4 metric cards at top:
  - Total Spend
  - Total Revenue
  - Overall ROI (%)
  - Total Conversions
- Below: "Channel Performance Trends" line chart
- Filters at top (Channel dropdown, Date Range)

**Screenshot tip:** Capture from "Marketing Analytics" title down to bottom of trend chart.

---

### Screenshot 6: Marketing Analytics - A/B Test
**Time:** 5 min
**File:** `marketing/marketing-analytics-ab-test.png`

**Navigation:**
1. Continue in Marketing Analytics module
2. Click **"A/B Testing"** tab
3. Scroll to "2-Variant Test" section
4. Input values:
   - **Variant A Visitors:** 1000
   - **Variant A Conversions:** 50
   - **Variant B Visitors:** 1000
   - **Variant B Conversions:** 65
   - **Confidence Level:** 95%
5. Click **"Calculate Significance"**
6. Wait for results to render

**What should be visible:**
- Input panel with filled values
- Results section showing:
  - "Winner: Variant B"
  - Confidence level: 97.7%
  - P-value: 0.023
  - Interpretation: "Variant B is statistically significantly better"
- Conversion rate comparison bars

**Screenshot tip:** Capture inputs + results in one frame.

---

## Phase 2: API Required (45 minutes)

**Important:** Have Anthropic API key ready. If you don't have one, skip to Phase 3 and come back later.

### Screenshot 7: Content Engine - Full Interface
**Time:** 5 min
**File:** `marketing/content-engine-full.png`

**Navigation:**
1. In sidebar, click **"Content Engine"**
2. If API key not set, input in sidebar: `st.sidebar.text_input("Enter API Key")`
3. Fill out Input Panel:
   - **Topic/Theme:** How AI is transforming marketing analytics
   - **Target Audience:** CMOs and marketing directors
   - **Keywords:** AI, ROI, analytics, automation
   - **Post Objective:** Educate and establish thought leadership
4. **Don't click Generate yet** - we want the pre-generation state
5. Scroll to show all 4 panels

**What should be visible:**
- Panel 1 (Input): All fields filled
- Panel 2 (Template Selection): 6 template cards visible
- Panel 3 (Tone Selection): 5 tone options
- Panel 4 (Generated Post): Empty state with "Click Generate" prompt

**Screenshot tip:** Capture the entire 4-panel layout showing the workflow.

---

### Screenshot 8: Content Engine - Templates
**Time:** 2 min
**File:** `marketing/content-engine-templates.png`

**Navigation:**
1. Continue in Content Engine
2. Scroll to Template Selection panel
3. Zoom in on the 6 template cards

**What should be visible:**
- All 6 template cards:
  1. Professional Insight
  2. Thought Leadership
  3. Case Study
  4. How-To Guide
  5. Industry Trend
  6. Personal Story
- Each card should show icon and description

**Screenshot tip:** Just the template panel, cropped tight.

---

### Screenshot 9: Content Engine - Generated Output
**Time:** 5 min
**File:** `marketing/content-engine-output.png`

**Navigation:**
1. Continue in Content Engine (same inputs from Screenshot 7)
2. Select template: **"Thought Leadership"**
3. Select tone: **"Analytical"**
4. Click **"Generate LinkedIn Post"**
5. Wait 3-5 seconds for Claude API response
6. Scroll to Generated Post panel

**What should be visible:**
- Full generated post text (150-250 words)
- Hashtags at bottom (#AI #MarketingAnalytics #ROI, etc.)
- Character count (should be under 3000)
- "Copy to Clipboard" button
- "Download as TXT" button

**Screenshot tip:** Capture the full output panel showing the quality of AI-generated content.

---

### Screenshot 10: Data Detective - Profile Full
**Time:** 10 min
**File:** `bi/data-detective-profile.png`

**Navigation:**
1. In sidebar, click **"Data Detective"**
2. Upload sample CSV (if you don't have one, create quick sample in Excel):
   - 100+ rows
   - 10+ columns (mix of numeric and categorical)
   - Example: sales data with Date, Product, Region, Revenue, Units, Customer_Type, etc.
3. Wait for file processing (5-10 seconds)
4. **"Data Profile"** tab loads automatically
5. Scroll to top

**What should be visible:**
- Dataset overview box:
  - Rows count
  - Columns count
  - Memory usage
- Missing values section with bar chart
- Duplicate rows count
- Column-by-column analysis starting (first 3-4 columns visible)

**Screenshot tip:** Capture from "Data Profile" title down to first few column analyses.

---

### Screenshot 11: Data Detective - Correlation Heatmap
**Time:** 3 min
**File:** `bi/data-detective-heatmap.png`

**Navigation:**
1. Continue in Data Detective (same uploaded file)
2. Stay on **"Data Profile"** tab
3. Scroll down to "Correlation Matrix" section
4. Wait for heatmap to render

**What should be visible:**
- Plotly heatmap showing correlations
- Color scale: -1 (negative correlation) to +1 (positive)
- Variable names on both axes
- Interactive hover tooltip (optional)

**Screenshot tip:** Just the heatmap chart, cropped close.

---

### Screenshot 12: Data Detective - AI Insights
**Time:** 10 min
**File:** `bi/data-detective-ai.png`

**Navigation:**
1. Continue in Data Detective
2. Click **"AI Insights"** tab
3. If API key not in session state, enter it
4. Click **"Generate Insights"** button
5. Wait 5-10 seconds for Claude API response

**What should be visible:**
- AI-generated insights section with:
  - Key findings (3-5 bullet points)
  - Data quality observations
  - Recommendations for next steps
  - Possible relationships between variables
- Professional formatting with markdown

**Screenshot tip:** Capture the full AI insights text showing the value of automated analysis.

---

## Phase 3: Remaining Screenshots (15 minutes)

### Screenshot 13: Marketing Analytics - ROI Heatmap
**Time:** 5 min
**File:** `marketing/marketing-analytics-roi-heatmap.png`

**Navigation:**
1. In sidebar, click **"Marketing Analytics"**
2. Click **"ROI Calculator"** tab
3. Input values:
   - **Campaign Spend:** $5000
   - **Visitors:** 1000
   - **Average Order Value:** $100
   - Leave conversion rate range as default (or set 1-10%)
4. Scroll down to "Scenario Analysis" section
5. Wait for heatmap to render

**What should be visible:**
- Interactive heatmap
- Y-axis: Conversion Rate (%)
- X-axis: Average Order Value ($)
- Color scale: red (loss) → yellow (break-even) → green (profit)
- 100 scenarios visible

**Screenshot tip:** Crop to just the heatmap for maximum visual impact.

---

### Screenshot 14: Marketing Analytics - Attribution
**Time:** 5 min
**File:** `marketing/marketing-analytics-attribution.png`

**Navigation:**
1. Continue in Marketing Analytics
2. Click **"Attribution Modeling"** tab
3. Input a 5-touchpoint customer journey:
   - **Touchpoint 1:** Organic Search
   - **Touchpoint 2:** Paid Social
   - **Touchpoint 3:** Email
   - **Touchpoint 4:** Paid Search
   - **Touchpoint 5:** Direct
4. Select attribution model: **"Position-Based"**
5. View results table

**What should be visible:**
- Journey input section with 5 touchpoints
- Attribution model selector (Position-Based selected)
- Results table showing:
  - All 5 attribution models side-by-side
  - Credit % for each touchpoint in each model
  - Visual comparison of how models differ

**Screenshot tip:** Capture the full comparison table showing all 5 models.

---

### Screenshot 15: Financial Analyst - Metrics
**Time:** 5 min
**File:** `bi/financial-analyst-metrics.png`

**Navigation:**
1. In sidebar, click **"Financial Analyst"**
2. Input ticker: **AAPL**
3. Click **"Analyze"** or press Enter
4. Wait 3-5 seconds for data to load
5. Scroll to top of results

**What should be visible:**
- Company profile section:
  - Company name (Apple Inc.)
  - Sector and Industry
  - Business summary (first few lines)
- Key metrics cards:
  - Market Cap
  - P/E Ratio
  - EPS
  - Dividend Yield
  - 52-Week Range
- Top of financial charts

**Screenshot tip:** Capture from "AAPL - Apple Inc." title down to metrics cards.

---

## Bonus Screenshots (Optional, Time Permitting)

### Screenshot 16: Homepage with Sidebar
**Time:** 2 min
**File:** `hero/homepage-sidebar.png`

**Navigation:**
1. Return to homepage: https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/
2. Ensure sidebar is expanded
3. Screenshot: Homepage welcome text + full sidebar showing all 7 modules

**What should be visible:**
- Welcome message and introduction
- Sidebar with all modules listed:
  - Market Pulse
  - Financial Analyst
  - Margin Hunter
  - Agent Logic
  - Content Engine
  - Data Detective
  - Marketing Analytics

---

### Screenshot 17: Agent Logic - Sentiment Gauge
**Time:** 5 min
**File:** `bi/agent-logic-sentiment.png`

**Navigation:**
1. In sidebar, click **"Agent Logic"**
2. Input ticker: **TSLA**
3. Toggle AI sentiment: **ON** (requires API key)
4. Click **"Analyze Sentiment"**
5. Wait for results

**What should be visible:**
- Sentiment gauge chart (-100 to +100)
- Overall sentiment score
- News feed with sentiment labels
- AI reasoning (if toggled on)

---

## Post-Capture Optimization (15 minutes)

### Image Optimization
1. [ ] Review all 15 screenshots for quality:
   - No browser chrome (address bar, tabs)
   - No personal info visible
   - All text readable
   - Colors rendered correctly

2. [ ] Optimize file sizes (keep under 500KB each):
   - **Online:** Upload to [TinyPNG](https://tinypng.com/) (free, lossless)
   - **Mac:** Use ImageOptim app
   - **Command line:**
     ```bash
     # Install imagemagick
     brew install imagemagick

     # Optimize all PNGs
     cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub/assets/screenshots
     for file in */*.png; do
       convert "$file" -quality 85 -resize 1920x1080\> "$file"
     done
     ```

3. [ ] Rename files for consistency:
   - Use lowercase
   - Use hyphens (not underscores or spaces)
   - Format: `module-name-description.png`
   - Example: `margin-hunter-dashboard.png`

### Git Commit
```bash
cd /Users/Cave/Desktop/enterprise-hub/EnterpriseHub
git add assets/screenshots/
git commit -m "Add 15 production screenshots for portfolio showcase

- 7 marketing niche screenshots (Marketing Analytics, Content Engine)
- 8 BI niche screenshots (Data Detective, Margin Hunter, Market Pulse, Financial Analyst)
- Organized by niche (marketing/, bi/, hero/)
- Optimized file sizes (<500KB each)
- Ready for Upwork proposals and LinkedIn posts"

git push origin main
```

### Verify on GitHub
1. [ ] Go to: https://github.com/ChunkyTortoise/enterprise-hub/tree/main/assets/screenshots
2. [ ] Confirm all images display correctly
3. [ ] Check file sizes (hover over file name to see size)

---

## Screenshot Usage Matrix

| Screenshot | Primary Use | Upwork Proposals | LinkedIn Posts | Portfolio |
|-----------|-------------|------------------|----------------|-----------|
| margin-hunter-dashboard.png | Hero shot | BI niche, Consulting | Post #2 | Featured |
| margin-hunter-heatmap.png | Visual impact | Financial modeling jobs | Post #2 carousel | Featured |
| margin-hunter-scenarios.png | Detail shot | Financial modeling jobs | - | Gallery |
| market-pulse-4panel.png | Technical credibility | Fintech jobs | Post #1 (hero) | Featured |
| marketing-analytics-dashboard.png | Hero shot (marketing) | Marketing niche | Post #3 carousel | Featured |
| marketing-analytics-ab-test.png | Statistical depth | A/B testing jobs | Post #3 carousel | Gallery |
| marketing-analytics-roi-heatmap.png | Visual analysis | ROI calculator jobs | - | Gallery |
| marketing-analytics-attribution.png | Enterprise feature | Attribution jobs | - | Gallery |
| content-engine-output.png | AI capability | Content gen jobs | Post #3 carousel | Featured |
| content-engine-templates.png | Feature variety | Content gen jobs | - | Gallery |
| content-engine-full.png | UX design | Streamlit jobs | - | Gallery |
| data-detective-profile.png | Automation value | Data analysis jobs | Post #2 carousel | Featured |
| data-detective-heatmap.png | Visual analytics | Data viz jobs | - | Gallery |
| data-detective-ai.png | AI integration | Claude API jobs | Post #3 carousel | Featured |
| financial-analyst-metrics.png | Financial depth | Financial analyst jobs | - | Gallery |

---

## Troubleshooting

### Issue: Module won't load
**Solution:** Refresh page, wait 10 seconds, try again. Streamlit Cloud sometimes has cold starts.

### Issue: API key not working
**Solution:**
1. Verify key starts with `sk-ant-`
2. Check billing status in Anthropic console
3. Try generating a new key

### Issue: Screenshots too large
**Solution:** Use TinyPNG or reduce resolution to 1440x900 (still readable).

### Issue: Charts not rendering
**Solution:** Wait 5 seconds after data input before screenshotting. Plotly needs time to render.

### Issue: Data Detective upload fails
**Solution:** Use CSV (not Excel) under 5MB. Streamlit Cloud has file size limits.

---

## Quality Checklist

Before considering Phase complete, verify:

- [ ] All 15 screenshots captured
- [ ] No browser chrome visible
- [ ] All text readable (no blurry text)
- [ ] Consistent sizing (all ~1920x1080)
- [ ] Files under 500KB each
- [ ] Organized in correct folders (marketing/, bi/, hero/)
- [ ] Committed to GitHub
- [ ] Verified display on GitHub

**Total time:** 90 minutes (setup + capture + optimization)
**Result:** Professional portfolio visuals ready for proposals and posts
