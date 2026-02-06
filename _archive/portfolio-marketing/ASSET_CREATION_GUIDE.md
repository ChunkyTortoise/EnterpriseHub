# Asset Creation Guide

> Step-by-step guide for creating all visual assets needed for the portfolio

## Overview

This portfolio requires professional visual assets to maximize conversion. This guide shows you exactly what to create and how.

## Asset Checklist (Status: Updated 2025-12-31)

### Phase 1: Essential (Required for Launch)

- [ ] Profile photo (headshot) - **ACTION REQUIRED: Add your photo to assets/images/profile.jpg**
- [x] 4-6 module screenshots - **COMPLETED: 6 high-quality screenshots generated**
- [x] Favicon - **COMPLETED: Generated in multiple sizes**
- [x] Social share image (Open Graph) - **COMPLETED: og-image.jpg generated**

### Phase 2: Enhanced (Within 1 Week)

- [ ] 3 demo videos (60-90 seconds each) - **ACTION REQUIRED: Use Loom/OBS to record**
- [ ] 8-10 certification badges - **ACTION REQUIRED: Download from Coursera/IBM/Google**
- [x] 2-3 architecture diagrams - **COMPLETED: Swarm Architecture and Process Diagram generated**

### Phase 3: Premium (Within 2 Weeks)

- [ ] Case study PDFs
- [ ] Service brochure PDF
- [ ] White paper PDFs

---

## Pre-Generated Assets
The following assets have been automatically generated for you:
- `assets/images/arete-swarm-arch.svg`: High-quality architecture diagram.
- `assets/images/process-diagram.svg`: 5-Phase delivery process visual.
- `assets/images/linkedin-banner.png`: Professional banner for LinkedIn.
- `assets/images/upwork-banner.png`: Professional banner for Upwork.
- `assets/images/og-image.jpg`: Social sharing preview image.
- `assets/images/favicon-*`: Browser tab icons.
- `assets/images/screenshots/*.png`: Module UI showcases.

---

## Phase 1: Essential Assets

### 1. Profile Photo

**Purpose:** Humanize the portfolio, build trust

**Specifications:**
- Size: 400x400px (minimum)
- Format: JPG or PNG
- File size: <100KB
- Background: Professional (neutral, blurred office, or solid color)

**Guidelines:**
- Professional attire
- Good lighting (natural light or ring light)
- Friendly but professional expression
- Direct eye contact with camera
- Clean background (not cluttered)

**Tools:**
- Smartphone camera (portrait mode)
- Natural window light (morning/afternoon)
- Free photo editor: [Canva](https://canva.com) or [Photopea](https://photopea.com)

**Export:**
- Save as: `assets/images/profile.jpg`
- Compress: Use [TinyPNG](https://tinypng.com)

---

### 2. Module Screenshots

**Purpose:** Show real functionality, prove it exists

**Required Screenshots (6 total):**

#### A. Financial Analyst - DCF Valuation (2 screenshots)

**Screenshot 1: DCF Interface**
- Open Financial Analyst module
- Enter ticker: AAPL
- Show full DCF calculator with:
  - Growth rate sliders
  - Discount rate input
  - 10-year projection table
  - Fair value calculation
- Highlight: "Fair Value: $185.23 vs Current: $150.00 → 23.5% Upside"

**Screenshot 2: Sensitivity Analysis**
- Scroll to sensitivity heatmap
- Show 3x5 grid with color coding
- Highlight: Different scenarios (best/worst case)

**Tools:**
- Open [Live Demo](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
- Use browser screenshot: Cmd+Shift+4 (Mac) or Win+Shift+S (Windows)
- Or use Firefox Developer Tools → Take Screenshot (full page)

#### B. Market Pulse - Technical Analysis (2 screenshots)

**Screenshot 1: 4-Panel Chart**
- Enter ticker: SPY
- Period: 6 months
- Show all 4 panels:
  - Price with Bollinger Bands
  - RSI
  - MACD
  - Volume
- Full height (capture all panels)

**Screenshot 2: Multi-Ticker Comparison**
- Enter tickers: "SPY,QQQ,DIA,IWM,VTI"
- Show normalized performance chart
- Capture performance summary table with best performer highlighted

#### C. Margin Hunter (1 screenshot)

**Screenshot: Monte Carlo Simulation**
- Enter example product:
  - Price: $99
  - Cost: $15
  - Fixed Costs: $50,000
  - Sales: 1,000 units
- Run Monte Carlo (1000 simulations)
- Capture:
  - Histogram with profit distribution
  - Summary statistics
  - Profitability probability (green percentage)

#### D. Content Engine (1 screenshot)

**Screenshot: Generated Post with Engagement**
- Generate LinkedIn post about "AI in business"
- Template: Thought Leadership
- Tone: Professional
- Capture:
  - Full generated post
  - Engagement score (prominently displayed)
  - Character/word count
  - Copy button

**Editing:**
- Crop to remove browser chrome (URL bar, bookmarks)
- Resize to 1200px width (maintain aspect ratio)
- Add subtle drop shadow: 0 4px 20px rgba(0,0,0,0.1)
- Save as PNG

**Export:**
- `assets/images/screenshots/financial_analyst_dcf.png`
- `assets/images/screenshots/financial_analyst_sensitivity.png`
- `assets/images/screenshots/market_pulse_charts.png`
- `assets/images/screenshots/market_pulse_comparison.png`
- `assets/images/screenshots/margin_hunter_monte_carlo.png`
- `assets/images/screenshots/content_engine_post.png`

---

### 3. Favicon

**Purpose:** Brand recognition in browser tabs

**Specifications:**
- Size: 32x32px, 16x16px (multi-size ICO)
- Format: .ico or .png
- Simple design (recognizable at small size)

**Design Options:**

**Option 1: Letter "E"** (for EnterpriseHub)
- Bold sans-serif font
- Purple gradient background (#667eea to #764ba2)
- White letter

**Option 2: Icon**
- Simple chart icon (bar chart or line graph)
- Purple/blue color scheme

**Tools:**
- [Favicon.io](https://favicon.io) (generate from text or icon)
- [RealFaviconGenerator](https://realfavicongenerator.net) (all sizes)

**Implementation:**

```html
<!-- Add to <head> in both HTML files -->
<link rel="icon" type="image/png" sizes="32x32" href="assets/images/favicon-32x32.png">
<link rel="icon" type="image/png" sizes="16x16" href="assets/images/favicon-16x16.png">
<link rel="apple-touch-icon" sizes="180x180" href="assets/images/apple-touch-icon.png">
```

---

### 4. Social Share Image (Open Graph)

**Purpose:** Beautiful preview when sharing on LinkedIn, Twitter, Slack

**Specifications:**
- Size: 1200x630px
- Format: JPG or PNG
- File size: <300KB

**Design:**

**Layout:**
```
┌─────────────────────────────────────┐
│  EnterpriseHub                      │ ← Logo/Title
│                                     │
│  Transform Complex AI Tasks         │ ← Headline
│  Into Simple, Reliable Systems      │
│                                     │
│  ✓ 10 Production Modules            │ ← Key points
│  ✓ 1,768+ Hours Certified           │
│  ✓ 301+ Automated Tests             │
│                                     │
│  [Background: Gradient or abstract] │
└─────────────────────────────────────┘
```

**Tools:**
- [Canva](https://canva.com) (use Social Media → LinkedIn Post template, resize)
- [Figma](https://figma.com) (free, more control)

**Export:**
- Save as: `assets/images/og-image.jpg`

**Implementation:**

```html
<!-- Add to <head> in both HTML files -->
<meta property="og:image" content="https://yourdomain.com/assets/images/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:image" content="https://yourdomain.com/assets/images/og-image.jpg">
```

---

## Phase 2: Enhanced Assets

### 5. Demo Videos

**Purpose:** Show functionality in action, increase trust

**Required Videos (3):**

#### Video 1: Financial Analyst - DCF Valuation (90 seconds)

**Script:**

```
[0:00-0:10] Intro
"Hi, I'm Cayman. This is the Financial Analyst module - a DCF valuation calculator I built."

[0:10-0:30] Show Interface
- Enter ticker: AAPL
- "Here's the 10-year free cash flow projection."
- Adjust growth rate slider: "Easily change assumptions"
- Show fair value calculation

[0:30-0:60] Sensitivity Analysis
- Scroll to heatmap
- "This shows fair value across 15 scenarios"
- Highlight best/worst case

[0:60-0:90] Export
- Click "Export PDF"
- Show PDF opening
- "Professional reports for stakeholders in seconds"
- End screen: "Try it live: [URL]"
```

**Recording:**
- Tool: Loom (free, easy) or OBS Studio (free, more control)
- Resolution: 1920x1080 (1080p)
- Framerate: 30fps
- Audio: Built-in mic is fine (quiet room)
- Cursor: Visible (helps viewers follow)

#### Video 2: Market Pulse - Technical Analysis (90 seconds)

**Script:**

```
[0:00-0:10] Intro
"This is Market Pulse - Bloomberg-quality technical analysis."

[0:10-0:40] Single Ticker
- Enter: SPY
- "4-panel chart: Price, RSI, MACD, Volume"
- Zoom in on Bollinger Bands
- "Real-time data via Yahoo Finance"

[0:40-0:90] Multi-Ticker Comparison
- Enter: "SPY,QQQ,DIA,IWM,VTI"
- "Compare up to 5 tickers normalized to %"
- Show best performer highlighted
- End screen: "Try it live: [URL]"
```

#### Video 3: Margin Hunter - Goal Seek (90 seconds)

**Script:**

```
[0:00-0:10] Intro
"Margin Hunter helps you answer: 'What price do I need?'"

[0:10-0:40] Basic Input
- Enter SaaS example: $99 price, $15 cost, $50k fixed
- Show break-even: 595 units

[0:40-0:70] Goal Seek
- Go to Goal Seek tab
- Target profit: $100,000
- "What price do I need with 1,000 units?"
- Show calculation: $115 (+16% vs current)

[0:70-0:90] Monte Carlo
- Run simulation (1000 runs)
- Show probability: 94% chance of profit
- End screen: "Try it live: [URL]"
```

**Editing:**
- Trim dead space at start/end
- Add end screen with URL and CTA
- Export: 1080p, H.264, <50MB

**Upload:**
- YouTube (unlisted or public)
- Vimeo (free tier)

**Embed:**
```html
<!-- Add to homepage -->
<iframe width="560" height="315" src="https://www.youtube.com/embed/VIDEO_ID" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe>
```

---

### 6. Certification Badges

**Purpose:** Visual proof of credentials

**Where to Find:**

1. **DeepLearning.AI:**
   - Go to Coursera → Accomplishments
   - Download certificate PDF
   - Screenshot badge

2. **Google Data Analytics:**
   - Coursera → Accomplishments
   - Click "Share" → Download badge

3. **IBM Business Intelligence:**
   - Coursera → Accomplishments
   - Download certificate

4. **Microsoft GenAI:**
   - Microsoft Learn → Achievements
   - Download badge

5. **Vanderbilt GenAI:**
   - Coursera → Accomplishments

**Processing:**
- Resize to 200x200px
- Save as PNG
- Location: `assets/images/certifications/`

**Display:**
```html
<div class="grid grid-cols-4 gap-4">
  <img src="assets/images/certifications/deeplearning-ai.png" alt="DeepLearning.AI">
  <img src="assets/images/certifications/google-data-analytics.png" alt="Google Data Analytics">
  <!-- etc -->
</div>
```

---

### 7. Architecture Diagrams

**Purpose:** Explain frameworks visually

**Required Diagrams (3):**

#### Diagram 1: EnterpriseHub Architecture

**Shows:** Modular structure

**Tool:** [Excalidraw](https://excalidraw.com) (free, simple)

**Elements:**
- User → App.py (Streamlit)
- App.py → 10 Modules
- Modules → Utils Layer
- Utils → External APIs (yfinance, Claude, etc.)

**Export:**
- Download as PNG (2x resolution)
- Save as: `assets/images/diagrams/architecture.png`

#### Diagram 2: 5-Phase Delivery Process

**Shows:** How you work (from brief)

**Elements:**
- 5 horizontal cards:
  1. Discovery (30-60 min, FREE)
  2. Proposal (1-2 days)
  3. Development (varies)
  4. Deployment (1-3 days)
  5. Support (7-90 days)

**Tool:** Canva (use "Process" template)

#### Diagram 3: Meta-Prompting Flow

**Shows:** How technique selection works

**Elements:**
1. Task Input
2. Classification → 4 categories (Research, Code, Strategy, Creative)
3. Technique Library (100+)
4. Recommendation (Top 8-15)
5. Persona Generation
6. Execution

**Tool:** Figma or draw.io

**Export All:**
- `assets/images/diagrams/architecture.png`
- `assets/images/diagrams/process.png`
- `assets/images/diagrams/meta-prompting.png`

---

## Phase 3: Premium Assets

### 8. Case Study PDF

**Purpose:** Social proof, trust building

**When:** After you complete first 1-2 client projects

**Template:**

```
Page 1:
┌─────────────────────────────────┐
│ CASE STUDY                      │
│                                 │
│ How [Client] Achieved           │
│ [Result] with [Your Solution]   │
│                                 │
│ [Client logo]                   │
│ [Your logo]                     │
└─────────────────────────────────┘

Page 2:
THE CHALLENGE
- Problem statement
- Pain points (3-4 bullets)
- Previous attempts

THE SOLUTION
- What you built
- Technologies used
- Timeline

THE RESULTS
- Metric 1: X% improvement
- Metric 2: $X saved
- Metric 3: X time reduced
- Quote from client

CONCLUSION
- Key takeaways
- Client testimonial
```

**Tool:** Google Docs → Export as PDF

---

### 9. Service Brochure PDF

**Purpose:** Quick reference, shareable

**Template:**

```
Page 1:
- Company name + tagline
- Services overview (3 tiers)
- Key differentiators

Page 2:
- Detailed service descriptions
- Pricing table
- Contact info
- Live demo link
```

**Tool:** Canva (Business Brochure template)

---

## Quick Start Checklist

**Day 1 (2 hours):**
- [ ] Take/edit profile photo
- [ ] Screenshot 6 modules
- [ ] Create favicon

**Day 2 (3 hours):**
- [ ] Record 3 demo videos
- [ ] Create social share image
- [ ] Download certification badges

**Day 3 (2 hours):**
- [ ] Create 3 diagrams
- [ ] Optimize all images (<100KB each)
- [ ] Upload to portfolio

**Total time:** 7 hours

---

## Image Optimization

**Before uploading:**

```bash
# Resize screenshots
mogrify -resize 1200x assets/images/screenshots/*.png

# Compress
# Online: tinypng.com (batch upload)
# CLI:
for file in assets/images/**/*.png; do
  pngquant --quality=80-95 "$file" --ext .png --force
done
```

**Target file sizes:**
- Profile photo: <100KB
- Screenshots: <200KB each
- Diagrams: <150KB each
- Social share image: <300KB

---

## Tools Summary

**Free:**
- [Canva](https://canva.com) - Graphics, diagrams, PDFs
- [Excalidraw](https://excalidraw.com) - Architecture diagrams
- [Loom](https://loom.com) - Screen recording (free tier: 5 min)
- [TinyPNG](https://tinypng.com) - Image compression
- [Favicon.io](https://favicon.io) - Favicon generator

**Paid (Optional):**
- Figma (free with limits, $12/month Pro)
- Adobe Photoshop ($10/month)
- Screenflow (Mac, $169 one-time)

---

## Next Steps

1. **Start with Phase 1** (essential assets)
2. **Deploy portfolio** with placeholders
3. **Add Phase 2 assets** within 1 week
4. **Create Phase 3 assets** after first client

**Questions?** Review the main README.md for deployment instructions.
