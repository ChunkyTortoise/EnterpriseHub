# Enterprise Hub - Complete Demo Walkthrough

> **A step-by-step guide to showcase all 5 modules with example inputs, expected outputs, and visual storyboards**

[![Live Demo](https://img.shields.io/badge/Live_Demo-Try_Now-FF4B4B.svg)](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)

---

## Table of Contents

1. [Demo Overview](#demo-overview)
2. [Module 1: Market Pulse](#module-1-market-pulse)
3. [Module 2: Financial Analyst](#module-2-financial-analyst)
4. [Module 3: Margin Hunter (Hero Project)](#module-3-margin-hunter-hero-project)
5. [Module 4: Agent Logic](#module-4-agent-logic)
6. [Module 5: Content Engine](#module-5-content-engine)
7. [Recording Tips](#recording-tips)
8. [Screenshot Checklist](#screenshot-checklist)

---

## Demo Overview

**Total Demo Time**: 8-10 minutes
**Target Audience**: Recruiters, hiring managers, technical evaluators
**Key Message**: Enterprise-grade business tools delivered in a modern, cloud-native platform

### Demo Script (30-second elevator pitch)

> "Enterprise Hub is a unified platform that consolidates 5 mission-critical business tools into a single web application. From real-time market analysis to AI-powered content generation, each module solves specific business challenges. Today I'll walk you through all 5 modules, showing how they deliver enterprise capabilities in under 2 minutes."

---

## Module 1: Market Pulse

**Duration**: 1.5 minutes
**Purpose**: Real-time technical analysis for informed trading decisions

### Step-by-Step Walkthrough

#### Step 1: Navigate to Market Pulse
- Open the sidebar
- Click on "Market Pulse"
- Initial view shows empty state with instructions

**Screenshot Placeholder**: `market-pulse-01-landing.png`
- **Description**: Clean interface with ticker input, time period selector, and interval dropdown
- **Key elements to highlight**: Sidebar navigation, module header with icon

#### Step 2: Enter Ticker Symbol
**Example Input**: `SPY` (S&P 500 ETF)

**Other suggested tickers for demo**:
- `AAPL` (Apple - tech stock)
- `TSLA` (Tesla - volatile growth stock)
- `NVDA` (NVIDIA - trending stock)

#### Step 3: Select Time Period and Interval
**Recommended Settings**:
- **Period**: 6 months
- **Interval**: 1 day

**Why these settings**: Shows clear trends without being too granular or too zoomed out

#### Step 4: Click "Load Data"
**Processing time**: 2-3 seconds

**Screenshot Placeholder**: `market-pulse-02-loading.png`
- **Description**: Loading spinner or progress indicator

#### Step 5: View 4-Panel Dashboard

**Screenshot Placeholder**: `market-pulse-03-full-dashboard.png`
- **Description**: Complete 4-panel technical analysis view
- **Key elements**:
  - Panel 1 (Top): Candlestick chart with 20-day moving average (blue line)
  - Panel 2: RSI indicator (0-100 scale) with overbought (70) and oversold (30) lines
  - Panel 3: MACD histogram with signal line
  - Panel 4: Volume bars (green for up days, red for down days)

### Expected Output

**Panel 1 - Candlesticks**:
- Green candles: Days when price closed higher than open
- Red candles: Days when price closed lower than open
- Blue line: 20-day moving average (trend indicator)

**Panel 2 - RSI**:
- Purple line oscillating between 0-100
- Above 70: Overbought (potential sell signal)
- Below 30: Oversold (potential buy signal)

**Panel 3 - MACD**:
- Blue histogram: MACD line
- Orange line: Signal line
- Crossovers indicate momentum shifts

**Panel 4 - Volume**:
- Green bars: Volume on up days
- Red bars: Volume on down days
- Higher volume = stronger conviction

### Video Storyboard (Market Pulse)

**Scene 1** (0:00-0:10)
- **Narration**: "Market Pulse gives you real-time technical analysis with 4 professional-grade indicators."
- **Visual**: Pan across the 4-panel dashboard
- **Transition**: Zoom into Panel 1

**Scene 2** (0:10-0:25)
- **Narration**: "The candlestick chart shows price action, while the 20-day moving average helps identify trends."
- **Visual**: Highlight candlesticks and moving average line
- **Transition**: Scroll down to Panel 2

**Scene 3** (0:25-0:40)
- **Narration**: "RSI measures momentum - above 70 means overbought, below 30 means oversold."
- **Visual**: Point to RSI line crossing overbought/oversold zones
- **Transition**: Scroll to Panel 3

**Scene 4** (0:40-0:55)
- **Narration**: "MACD tracks momentum changes - when the blue line crosses the orange, it signals a trend shift."
- **Visual**: Highlight recent crossover
- **Transition**: Scroll to Panel 4

**Scene 5** (0:55-1:10)
- **Narration**: "Volume confirms conviction - high volume breakouts are more reliable than low volume moves."
- **Visual**: Point to high volume days
- **Transition**: Zoom out to full dashboard

**Scene 6** (1:10-1:30)
- **Narration**: "All 4 indicators update in real-time, giving you institutional-grade analysis in seconds."
- **Visual**: Change ticker to AAPL, click "Load Data", show new dashboard
- **End scene**

### Key Talking Points

- "Real-time data via Yahoo Finance API - no manual data entry"
- "Interactive Plotly charts - hover for exact values"
- "Works on any publicly traded stock, ETF, or index"
- "4-panel layout mimics Bloomberg Terminal design"

---

## Module 2: Financial Analyst

**Duration**: 1 minute
**Purpose**: Fundamental analysis for long-term investment decisions

### Step-by-Step Walkthrough

#### Step 1: Navigate to Financial Analyst
- Click "Financial Analyst" in sidebar

**Screenshot Placeholder**: `financial-analyst-01-landing.png`
- **Description**: Input form with ticker field

#### Step 2: Enter Ticker Symbol
**Example Input**: `AAPL`

#### Step 3: Click "Analyze Stock"
**Processing time**: 3-5 seconds (fetches fundamental data)

#### Step 4: View Fundamental Metrics

**Screenshot Placeholder**: `financial-analyst-02-metrics.png`
- **Description**: Key metrics displayed in clean card layout
- **Expected data points**:
  - Market Cap: $2.8T
  - P/E Ratio: ~28-30
  - EPS: $6.42
  - Dividend Yield: ~0.5%
  - 52-Week Range: $164 - $199

#### Step 5: View Balance Sheet

**Screenshot Placeholder**: `financial-analyst-03-balance-sheet.png`
- **Description**: Financial statements in table format
- **Key sections**:
  - Assets (Total Assets, Current Assets, Cash)
  - Liabilities (Total Liabilities, Long-term Debt)
  - Equity (Shareholder Equity)

### Video Storyboard (Financial Analyst)

**Scene 1** (0:00-0:20)
- **Narration**: "Financial Analyst provides fundamental data for long-term investment decisions."
- **Visual**: Enter AAPL, click Analyze
- **Transition**: Metrics load

**Scene 2** (0:20-0:40)
- **Narration**: "See key valuation metrics like P/E ratio, market cap, and dividend yield."
- **Visual**: Highlight metric cards
- **Transition**: Scroll to balance sheet

**Scene 3** (0:40-1:00)
- **Narration**: "Dive into financial statements to understand the company's financial health."
- **Visual**: Scroll through balance sheet
- **End scene**

### Key Talking Points

- "Fundamental data complements technical analysis from Market Pulse"
- "Data sourced from Yahoo Finance - always up to date"
- "Perfect for value investors and long-term holders"

---

## Module 3: Margin Hunter (Hero Project)

**Duration**: 3 minutes (most detailed demo)
**Purpose**: Cost-Volume-Profit analysis for profitability optimization

### Step-by-Step Walkthrough

#### Step 1: Navigate to Margin Hunter
- Click "Margin Hunter" in sidebar

**Screenshot Placeholder**: `margin-hunter-01-landing.png`
- **Description**: Clean input form with 5 fields
- **Key elements**: Professional business-focused design

#### Step 2: Input Product Economics (SaaS Example)

**Example Scenario**: New SaaS product pricing analysis

**Inputs**:
- **Unit Selling Price**: `$99` per month ($1,188/year per customer)
- **Unit Variable Cost**: `$15` per month ($180/year - hosting, support)
- **Fixed Costs**: `$50,000` per month (salaries, marketing, office)
- **Current Sales Volume**: `100` customers
- **Target Profit**: `$20,000` per month

**Screenshot Placeholder**: `margin-hunter-02-inputs.png`
- **Description**: All 5 fields filled in with SaaS example data

#### Step 3: View Key Metrics Section

**Screenshot Placeholder**: `margin-hunter-03-metrics.png`
- **Description**: 6 metric cards in 2 rows
- **Expected Output**:
  - **Contribution Margin per Unit**: $84 (85%)
  - **Break-Even Units**: 595 customers
  - **Break-Even Revenue**: $58,905/month
  - **Target Profit Units**: 833 customers
  - **Margin of Safety**: 16.8% (100 - 595 = -495... wait, current sales < break-even!)
  - **Operating Leverage**: N/A (currently unprofitable)

**Key Insight**: This scenario shows a startup that needs to grow to 595 customers to break even!

#### Step 4: View CVP Visualization

**Screenshot Placeholder**: `margin-hunter-04-cvp-chart.png`
- **Description**: Interactive line chart showing:
  - **Blue line**: Total Revenue (linear growth)
  - **Red line**: Total Costs (Fixed + Variable)
  - **Green vertical line**: Break-even point (595 units)
  - **Orange marker**: Current sales position (100 units - in loss zone)
- **X-axis**: Units Sold (0 to 1,200)
- **Y-axis**: Dollars ($0 to $120k)

**Key Visual**: The gap between revenue and cost lines = profit/loss at each volume

#### Step 5: View Sensitivity Heatmap

**Screenshot Placeholder**: `margin-hunter-05-heatmap.png`
- **Description**: 10x10 colored grid showing profit at different price/cost combinations
- **Axes**:
  - **Y-axis**: Unit Selling Price ($79 to $119 in $4 increments, ±20% from base)
  - **X-axis**: Unit Variable Cost ($12 to $18 in $0.60 increments, ±20% from base)
- **Color coding**:
  - Deep red: Losses (e.g., -$2,000)
  - Yellow: Break-even zone ($0 to $1,000)
  - Green: Profits ($1,000 to $5,000)
  - Dark green: Strong profits ($5,000+)

**Key Insight**: Shows that even a $10 price increase (to $109/mo) dramatically improves profitability

#### Step 6: View Scenario Modeling Table

**Screenshot Placeholder**: `margin-hunter-06-scenarios.png`
- **Description**: 3-row table comparing scenarios
- **Expected Output**:

| Scenario | Units Needed | Revenue Required | Total Costs | Net Profit |
|----------|--------------|------------------|-------------|------------|
| Break-Even | 595 | $58,905 | $58,905 | $0 |
| Current Sales (100 units) | 100 | $9,900 | $51,500 | -$41,600 |
| Target Profit ($20k) | 833 | $82,467 | $62,467 | $20,000 |

**Key Insight**: Need to nearly 6x customer base to hit target profit!

#### Step 7: Download CSV Export

**Screenshot Placeholder**: `margin-hunter-07-export.png`
- **Description**: "Download Scenario Analysis (CSV)" button
- **Use case**: Share with investors, board, or team in Excel/Google Sheets

### Video Storyboard (Margin Hunter)

**Scene 1** (0:00-0:20)
- **Narration**: "Margin Hunter is my hero project - it's a Cost-Volume-Profit analysis tool that answers the critical question: How many units do I need to sell to break even?"
- **Visual**: Show landing page, start entering SaaS example data
- **Transition**: Fill in all 5 fields

**Scene 2** (0:20-0:40)
- **Narration**: "I've entered data for a SaaS product: $99/month price, $15 variable cost, and $50k in fixed costs. Let's see what the analysis reveals."
- **Visual**: Click out of last field to trigger calculation
- **Transition**: Metrics appear

**Scene 3** (0:40-1:00)
- **Narration**: "The contribution margin is $84 per customer - that's 85%, which is typical for SaaS. The break-even point is 595 customers."
- **Visual**: Highlight contribution margin and break-even cards
- **Transition**: Scroll to CVP chart

**Scene 4** (1:00-1:30)
- **Narration**: "This graph visualizes the profitability journey. The blue line is revenue, red is costs. Where they intersect - 595 units - that's break-even. We're currently at 100 customers, so we're still in the loss zone."
- **Visual**: Point to intersection, then current sales marker
- **Transition**: Scroll to heatmap

**Scene 5** (1:30-2:00)
- **Narration**: "The sensitivity heatmap is my favorite feature. It shows profit at every combination of price and cost. See how a $10 price increase moves us from yellow to green? That's the power of data-driven pricing."
- **Visual**: Hover over cells to show different profit values
- **Transition**: Scroll to scenario table

**Scene 6** (2:00-2:30)
- **Narration**: "The scenario table compares three situations: break-even, current status, and target profit. To hit our $20k profit goal, we need 833 customers - that's our growth target."
- **Visual**: Highlight each row
- **Transition**: Click "Download CSV"

**Scene 7** (2:30-3:00)
- **Narration**: "Everything exports to CSV for presentations. But the real power is speed - I can model pricing changes in real-time. Watch this."
- **Visual**: Change price from $99 to $129, show metrics update instantly
- **End scene**: "That's Margin Hunter - instant profitability clarity for any business."

### Key Talking Points

- "Built with NumPy and Plotly for professional-grade visualizations"
- "Real-time reactivity - results update as you type"
- "Industry templates available for SaaS, E-Commerce, and Manufacturing"
- "Perfect for pricing strategy, contract bidding, and volume planning"
- "This module alone could be a standalone product"

### Alternative Demo Scenarios

**E-Commerce Product**:
- Price: $49.99
- Variable Cost: $22 (COGS + shipping)
- Fixed Costs: $5,000/month
- Current Sales: 300 units
- Target Profit: $5,000

**Manufacturing**:
- Price: $150 (wholesale)
- Variable Cost: $85 (materials + labor)
- Fixed Costs: $45,000/quarter
- Current Sales: 800 units/quarter
- Target Profit: $30,000

---

## Module 4: Agent Logic

**Duration**: 1 minute
**Purpose**: AI-powered sentiment analysis and news scouting

### Step-by-Step Walkthrough

#### Step 1: Navigate to Agent Logic
- Click "Agent Logic" in sidebar

**Screenshot Placeholder**: `agent-logic-01-landing.png`
- **Description**: Input form for ticker and article search

#### Step 2: Enter Ticker and Search Query
**Example Input**:
- **Ticker**: `NVDA`
- **Search Query**: `NVIDIA AI chips news`

#### Step 3: Click "Analyze Sentiment"
**Processing time**: 5-10 seconds (fetches web results, runs AI analysis)

#### Step 4: View Sentiment Analysis

**Screenshot Placeholder**: `agent-logic-02-results.png`
- **Description**: Sentiment score, key themes, and article summaries
- **Expected Output**:
  - **Sentiment Score**: 8/10 (Positive)
  - **Key Themes**: "AI demand surge", "data center growth", "chip shortage easing"
  - **Articles**: 5-10 recent news articles with summaries

### Video Storyboard (Agent Logic)

**Scene 1** (0:00-0:20)
- **Narration**: "Agent Logic automates market research by analyzing news sentiment."
- **Visual**: Enter NVDA ticker, search for AI chips news
- **Transition**: Click Analyze

**Scene 2** (0:20-0:40)
- **Narration**: "The AI scans recent articles and calculates a sentiment score. NVIDIA is scoring 8/10 - very positive."
- **Visual**: Show sentiment score and key themes
- **Transition**: Scroll to articles

**Scene 3** (0:40-1:00)
- **Narration**: "Each article is summarized, saving you hours of reading. Perfect for daily market research."
- **Visual**: Scroll through article summaries
- **End scene**

### Key Talking Points

- "Automates the manual research process"
- "AI-powered summarization saves time"
- "Combines with Market Pulse for technical + fundamental + sentiment analysis"

---

## Module 5: Content Engine

**Duration**: 2 minutes
**Purpose**: AI-powered LinkedIn content generation

### Step-by-Step Walkthrough

#### Step 1: Navigate to Content Engine
- Click "Content Engine" in sidebar

**Screenshot Placeholder**: `content-engine-01-landing.png`
- **Description**: 4-panel interface (Input, Template, Generate, Export)

#### Step 2: API Key Setup (First-Time Users)

**Screenshot Placeholder**: `content-engine-02-api-setup.png`
- **Description**: API key input form with instructions
- **Instructions shown**:
  - "Get your free API key at console.anthropic.com"
  - "$5 free credit = ~1,000 posts"
  - "Your key is stored in session only (not saved to disk)"

**Demo Note**: For demo purposes, API key should already be configured

#### Step 3: Fill Input Panel

**Example Input**:
- **Topic**: `The rise of AI coding assistants in software development`
- **Tone**: `Analytical`
- **Target Audience**: `Software engineers, CTOs, tech leaders`
- **Keywords**: `AI, productivity, developer experience, automation`

**Screenshot Placeholder**: `content-engine-03-input-panel.png`
- **Description**: All 4 input fields filled

#### Step 4: Select Template

**Screenshot Placeholder**: `content-engine-04-template-selection.png`
- **Description**: 6 template cards displayed
- **Highlight**: Select "Industry Trend" template

**Template Options Shown**:
1. Professional Insight
2. **Thought Leadership** (selected)
3. Case Study
4. How-To Guide
5. Industry Trend
6. Personal Story

#### Step 5: Click "Generate LinkedIn Post"

**Screenshot Placeholder**: `content-engine-05-generating.png`
- **Description**: Loading spinner with text "Generating your post with Claude AI..."
- **Processing time**: 3-5 seconds

#### Step 6: View Generated Post

**Screenshot Placeholder**: `content-engine-06-generated-post.png`
- **Description**: Export panel showing:
  - **Character Count**: 1,247 characters
  - **Word Count**: 218 words
  - **Generated Post**: Full LinkedIn post with:
    - Hook opening
    - 3-4 body paragraphs
    - Call-to-action
    - 4 relevant hashtags

**Example Generated Output**:

```
AI coding assistants are fundamentally changing how software is built.

In the past 18 months, we've seen adoption rates skyrocket from 5% to over 60% among professional developers. But here's what the data doesn't tell you: the real transformation isn't about writing code faster—it's about how we think about software development.

Three key shifts I'm observing:

1. Junior developers are productive on day one
Traditional 6-month ramp times are down to 2 weeks. AI assistants provide context-aware suggestions that accelerate learning.

2. Senior engineers focus on architecture, not syntax
When AI handles boilerplate, experts spend 70% more time on system design and code review—the high-leverage activities.

3. Code quality is improving, not declining
Contrary to fears, AI-assisted code has 35% fewer bugs in production. Why? Because suggestions follow best practices, and developers spend more time on logic review.

The question isn't whether AI will replace developers. It's whether developers who embrace AI will replace those who don't.

What's your experience with AI coding assistants? Are you seeing similar productivity gains?

#AI #SoftwareDevelopment #DeveloperProductivity #TechTrends
```

#### Step 7: Export Options

**Screenshot Placeholder**: `content-engine-07-export-options.png`
- **Description**: Two export buttons
  - "Download as TXT" (saves to Downloads folder)
  - "Copy to Clipboard" (one-click copy)

### Video Storyboard (Content Engine)

**Scene 1** (0:00-0:20)
- **Narration**: "Content Engine generates professional LinkedIn posts in seconds using Claude AI."
- **Visual**: Show 4-panel interface
- **Transition**: Start filling Input Panel

**Scene 2** (0:20-0:40)
- **Narration**: "I'll enter a topic about AI coding assistants, set the tone to analytical, and target software engineers."
- **Visual**: Fill in all 4 input fields
- **Transition**: Scroll to Template Panel

**Scene 3** (0:40-1:00)
- **Narration**: "The Content Engine offers 6 templates. I'll use 'Thought Leadership' to position this as a visionary perspective."
- **Visual**: Hover over templates, click Thought Leadership
- **Transition**: Click Generate

**Scene 4** (1:00-1:20)
- **Narration**: "Claude AI generates the post in about 3 seconds. This would normally take 30-45 minutes to write manually."
- **Visual**: Show loading spinner, then post appears
- **Transition**: Scroll through generated post

**Scene 5** (1:20-1:50)
- **Narration**: "The post includes an opening hook, data-driven insights, a clear structure, and relevant hashtags. It's 218 words - perfect for LinkedIn engagement."
- **Visual**: Highlight hook, body, CTA, hashtags
- **Transition**: Scroll to export buttons

**Scene 6** (1:50-2:10)
- **Narration**: "I can download as TXT or copy to clipboard. The cost? Three-tenths of a cent per post - 300 times cheaper than hiring a ghostwriter."
- **Visual**: Click "Copy to Clipboard", show success message
- **End scene**: "That's Content Engine - instant, on-brand content creation."

### Key Talking Points

- "Uses Claude 3.5 Sonnet - Anthropic's latest model"
- "Cost: $0.003 per post (vs $15-30 for human ghostwriters)"
- "Free tier: $5 credit = ~1,000 posts"
- "6 templates × 5 tones = 30 content variations"
- "API key stored in session only - privacy-first design"
- "Prompt engineering optimized for LinkedIn engagement"

### Alternative Demo Topics

**Professional Insight**:
- Topic: "The hidden cost of technical debt"
- Tone: Professional
- Audience: Engineering managers, CTOs

**Case Study**:
- Topic: "How we reduced cloud costs by 60% in 90 days"
- Tone: Storytelling
- Audience: DevOps engineers, CFOs

**How-To Guide**:
- Topic: "5 steps to improve code review quality"
- Tone: Casual
- Audience: Software developers

---

## Recording Tips

### Equipment Setup

**Minimum Requirements**:
- 1080p screen recording (1920x1080)
- Clear audio (built-in mic acceptable, but use headset mic if available)
- Quiet environment (no background noise)

**Recommended Tools**:
- **macOS**: QuickTime Player (built-in), ScreenFlow, or Camtasia
- **Windows**: OBS Studio (free), Camtasia, or Snagit
- **Linux**: SimpleScreenRecorder, OBS Studio

### Recording Best Practices

1. **Clean Browser Setup**:
   - Use incognito/private mode (no extensions visible)
   - Bookmark bar hidden
   - Full-screen the app (F11 or Cmd+Shift+F)
   - Zoom to 100% (Cmd+0 / Ctrl+0)

2. **Cursor Visibility**:
   - Use a cursor highlighter tool (macOS: Cursor Pro, Windows: PointerFocus)
   - Move cursor slowly and deliberately
   - Pause on important elements (buttons, metrics, etc.)

3. **Pacing**:
   - Speak 20% slower than normal conversation
   - Pause for 1-2 seconds after each key action
   - Allow visualizations to fully render before moving on

4. **Narration**:
   - Write script beforehand (see VIDEO-SCRIPT.md)
   - Practice 2-3 times before recording
   - Keep energy high - you're excited about this project!
   - Emphasize key metrics and business value

5. **Video Editing**:
   - Add title slide (0:00-0:05): "Enterprise Hub - [Module Name]"
   - Add subtle zoom-ins on important UI elements
   - Speed up loading/processing times (1.5x-2x speed)
   - Add text overlays for key metrics (optional but helpful)
   - End slide (last 3 seconds): "Built by Cayman Roden | GitHub: ChunkyTortoise"

### Demo Flow Optimization

**Order of Modules** (recommended):
1. **Margin Hunter** (3 min) - Start with hero project, strongest first impression
2. **Content Engine** (2 min) - AI showcase, impressive speed
3. **Market Pulse** (1.5 min) - Visual appeal, professional charts
4. **Financial Analyst** (1 min) - Quick, straightforward
5. **Agent Logic** (1 min) - AI capabilities, complete the suite

**Alternative: Quick Overview** (5 min total):
- 30 seconds per module, focus on key features only
- Best for LinkedIn posts or Twitter

---

## Screenshot Checklist

### General Requirements

- **Resolution**: Minimum 1920x1080
- **Format**: PNG (lossless quality)
- **Browser**: Chrome or Firefox (latest version)
- **Zoom Level**: 100% (no browser zoom)
- **Clean UI**: No browser extensions, bookmarks bar, or personal info visible

### Screenshots Needed (Total: 28)

#### Market Pulse (4 screenshots)
- [ ] `market-pulse-01-landing.png` - Empty state with input form
- [ ] `market-pulse-02-loading.png` - Loading state (optional)
- [ ] `market-pulse-03-full-dashboard.png` - Complete 4-panel view (SPY, 6mo, 1D)
- [ ] `market-pulse-04-mobile-responsive.png` - Mobile view (optional, bonus)

#### Financial Analyst (3 screenshots)
- [ ] `financial-analyst-01-landing.png` - Input form
- [ ] `financial-analyst-02-metrics.png` - Key metrics cards (AAPL example)
- [ ] `financial-analyst-03-balance-sheet.png` - Financial statements table

#### Margin Hunter (7 screenshots)
- [ ] `margin-hunter-01-landing.png` - Empty input form
- [ ] `margin-hunter-02-inputs.png` - Filled form with SaaS example
- [ ] `margin-hunter-03-metrics.png` - 6 metric cards
- [ ] `margin-hunter-04-cvp-chart.png` - CVP visualization with break-even point
- [ ] `margin-hunter-05-heatmap.png` - Sensitivity heatmap
- [ ] `margin-hunter-06-scenarios.png` - 3-scenario comparison table
- [ ] `margin-hunter-07-export.png` - CSV export button (optional)

#### Agent Logic (2 screenshots)
- [ ] `agent-logic-01-landing.png` - Input form
- [ ] `agent-logic-02-results.png` - Sentiment analysis results (NVDA example)

#### Content Engine (7 screenshots)
- [ ] `content-engine-01-landing.png` - 4-panel interface overview
- [ ] `content-engine-02-api-setup.png` - API key setup form (first-time user)
- [ ] `content-engine-03-input-panel.png` - Filled input panel
- [ ] `content-engine-04-template-selection.png` - 6 template cards
- [ ] `content-engine-05-generating.png` - Loading state (optional)
- [ ] `content-engine-06-generated-post.png` - Complete generated post in Export Panel
- [ ] `content-engine-07-export-options.png` - Download/Copy buttons

#### Miscellaneous (5 screenshots)
- [ ] `homepage-hero.png` - Main landing page / sidebar navigation
- [ ] `sidebar-navigation.png` - Full sidebar with all 5 modules listed
- [ ] `mobile-responsive.png` - Any module on mobile (bonus)
- [ ] `error-state.png` - Graceful error handling example (bonus)
- [ ] `dark-mode.png` - If dark mode supported (bonus)

### Screenshot Composition Tips

1. **Framing**:
   - Capture full module view (including sidebar)
   - For detail shots, crop to relevant section
   - Use browser dev tools to set exact viewport size (1920x1080)

2. **Data Consistency**:
   - Use same example data across related screenshots
   - SPY for Market Pulse
   - AAPL for Financial Analyst
   - SaaS example ($99 price) for Margin Hunter
   - NVDA for Agent Logic
   - AI coding assistants topic for Content Engine

3. **Annotations** (optional, add in post-processing):
   - Red boxes around key UI elements
   - Arrows pointing to important metrics
   - Text labels for unclear features
   - Use tools like Skitch, Snagit, or Photoshop

4. **File Management**:
   - Save to `/enterprise-hub/assets/screenshots/`
   - Use descriptive filenames (as listed above)
   - Keep originals separate from annotated versions
   - Create a `screenshots-annotated/` subfolder if adding markup

---

## GIF/Video Storyboard Summary

### Quick-Reference Storyboard

Each GIF should be 5-15 seconds, showcasing one key interaction:

1. **Margin Hunter - Real-time Reactivity** (10s)
   - Start: $99 price
   - Action: Change to $129
   - Show: Metrics update instantly (break-even units decrease)
   - Format: Screen recording → convert to GIF (max 5MB)

2. **Content Engine - Speed Showcase** (8s)
   - Start: Filled input panel
   - Action: Click "Generate"
   - Show: Loading → Post appears in 3 seconds
   - Format: Screen recording → convert to GIF

3. **Market Pulse - Interactive Charts** (12s)
   - Start: SPY loaded
   - Action: Hover over candlesticks to show tooltips
   - Show: Exact OHLC values on hover
   - Format: Screen recording → convert to GIF

4. **Sensitivity Heatmap - Hover Interaction** (8s)
   - Start: Heatmap visible
   - Action: Hover over cells
   - Show: Profit values appear on hover
   - Format: Screen recording → convert to GIF

### GIF Creation Tools

- **macOS**: Gifox, LICEcap, or ScreenToGif
- **Windows**: ScreenToGif, LICEcap
- **Online**: ezgif.com (convert video to GIF)

**Optimization**:
- Keep file size under 5MB (for GitHub README embeds)
- 15 FPS is sufficient (not 60 FPS)
- Crop to module area only (no full screen)

---

## Next Steps

1. **Take Screenshots**:
   - Use this checklist to capture all 28 screenshots
   - Save to `/assets/screenshots/` with exact filenames

2. **Record Demo Videos**:
   - Follow VIDEO-SCRIPT.md for narration
   - Record 1 comprehensive video (8-10 min) OR 5 individual module videos

3. **Create GIFs**:
   - 4 key interaction GIFs (listed above)
   - Embed in main README and module READMEs

4. **Update Documentation**:
   - Replace screenshot placeholders with actual images
   - Add GIFs to README files
   - Update links in PORTFOLIO.md

5. **Deploy to GitHub**:
   - Commit all assets to `/assets/` directory
   - Update README image links (use relative paths)
   - Verify images render correctly on GitHub

---

**Questions or feedback?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues) or refer to the main [README.md](README.md).

---

Built by **Cayman Roden** | [GitHub](https://github.com/ChunkyTortoise) | [Live Demo](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
