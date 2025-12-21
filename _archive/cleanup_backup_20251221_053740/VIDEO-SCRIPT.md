# Enterprise Hub - Video Demo Scripts

> **Professional narration scripts for demo videos, portfolio showcases, and presentation recordings**

---

## Table of Contents

1. [Full Platform Demo (8-10 minutes)](#full-platform-demo-8-10-minutes)
2. [Quick Pitch (60 seconds)](#quick-pitch-60-seconds)
3. [Individual Module Scripts](#individual-module-scripts)
4. [Technical Deep-Dive (15 minutes)](#technical-deep-dive-15-minutes)
5. [Portfolio Highlight Reel (3 minutes)](#portfolio-highlight-reel-3-minutes)
6. [Delivery Tips](#delivery-tips)

---

## Full Platform Demo (8-10 minutes)

**Target Audience**: Recruiters, hiring managers, technical evaluators
**Goal**: Showcase all 5 modules, emphasize technical sophistication and business value
**Tone**: Professional, confident, technically precise

### Opening (0:00 - 0:30)

> "Hi, I'm Cayman Roden, and this is Enterprise Hub - a unified platform that consolidates 5 mission-critical business tools into a single, cloud-native web application.
>
> Over the next 8 minutes, I'll walk you through each module, showing how they solve real business challenges - from market analysis to AI-powered content generation.
>
> This project demonstrates my ability to build production-grade applications with modern Python frameworks, integrate external APIs, and design intuitive user interfaces.
>
> Let's dive in."

**Visual**: Show homepage with sidebar navigation, pan across all 5 module icons

---

### Module 1: Margin Hunter (0:30 - 3:30) - 3 minutes

**Narration**:

> "Let's start with Margin Hunter - my hero project and the most feature-rich module in the platform.
>
> Margin Hunter is a Cost-Volume-Profit analysis tool designed for business leaders who need to answer critical profitability questions:
>
> - How many units do I need to sell to break even?
> - What happens to my profit if costs increase by 10%?
> - What's the optimal pricing strategy for maximum margin?
>
> I'll demonstrate with a real-world SaaS example."

**Action**: Navigate to Margin Hunter, show input form

> "I'm modeling a new software product priced at $99 per month. Variable costs - things like hosting and customer support - are $15 per customer per month. Fixed costs - salaries, marketing, office rent - total $50,000 per month.
>
> We currently have 100 customers and want to reach $20,000 in monthly profit.
>
> As soon as I enter these numbers, the calculations happen instantly."

**Action**: Fill in all 5 fields, show metrics update in real-time

> "The contribution margin is $84 per customer - that's 85%, which is typical for high-margin SaaS businesses.
>
> The break-even point is 595 customers. That means we need to 6x our current customer base just to cover costs.
>
> To hit our target profit of $20,000, we need 833 customers."

**Action**: Scroll to CVP Chart

> "This Cost-Volume-Profit graph visualizes the profitability journey. The blue line represents total revenue - it grows linearly with each sale. The red line is total costs - it starts high due to fixed costs, then increases at a slower rate.
>
> Where these two lines intersect - at 595 units - that's our break-even point. We're currently at 100 customers, marked by the orange line, so we're operating at a loss right now."

**Action**: Scroll to Sensitivity Heatmap

> "Now here's my favorite feature - the sensitivity heatmap.
>
> This shows profit at every combination of price and cost within a ±20% range. Each cell is color-coded: red means losses, yellow is break-even, and green is profit.
>
> See what happens if we increase the price to $109 per month? We move from the yellow break-even zone into solid green profitability - even at our current 100-customer volume.
>
> This is incredibly powerful for pricing negotiations. If a supplier increases costs by 10%, I can immediately see that I need to raise prices by at least $8 to maintain margin."

**Action**: Hover over different cells, show profit values

> "The scenario modeling table compares three situations side-by-side: break-even, current status, and target profit.
>
> I can export this entire analysis to CSV for presentations or further analysis in Excel."

**Action**: Scroll to scenario table, highlight Download button

> "But the real magic is real-time reactivity. Watch what happens when I change the price."

**Action**: Change price from $99 to $129, show all metrics update instantly

> "Every metric updates immediately. Break-even drops to 459 customers. Target profit units drop to 667. The entire analysis recalculates in milliseconds.
>
> This module alone could be a standalone SaaS product. I've built industry-specific templates for SaaS, e-commerce, and manufacturing use cases, complete with scenario walkthroughs and best practices.
>
> That's Margin Hunter - instant profitability clarity for any business model."

---

### Module 2: Content Engine (3:30 - 5:30) - 2 minutes

**Narration**:

> "Next up is Content Engine - an AI-powered LinkedIn post generator built with Anthropic's Claude 3.5 Sonnet.
>
> The challenge: most professionals know they should post on LinkedIn regularly, but creating quality content takes 30 to 45 minutes per post. That's unsustainable.
>
> Content Engine solves this by generating polished, on-brand posts in under 3 seconds."

**Action**: Navigate to Content Engine, show 4-panel interface

> "The workflow is streamlined into 4 panels: Input, Template, Generate, and Export.
>
> I'll create a post about AI coding assistants - a hot topic in software development."

**Action**: Fill in Input Panel

> "I'm entering the topic, setting the tone to analytical, and targeting software engineers and CTOs. I've added keywords for discoverability: AI, productivity, developer experience.
>
> Now I'll select a template. Content Engine offers 6 different post types, each optimized for different goals."

**Action**: Show template cards, select "Thought Leadership"

> "I'm choosing Thought Leadership because I want to position this as a visionary perspective, not just news reporting.
>
> Watch this."

**Action**: Click "Generate LinkedIn Post"

> "Claude AI generates the post in about 3 seconds. For context, this would take me 30 to 45 minutes to write manually - from research to drafting to editing.
>
> Let's look at the output."

**Action**: Scroll through generated post

> "The post opens with a strong hook - 'AI coding assistants are fundamentally changing how software is built.' That grabs attention.
>
> It includes data-driven insights - 'adoption rates skyrocketed from 5% to 60%' - which adds credibility.
>
> There are three clear takeaways, formatted as a numbered list for readability.
>
> And it ends with a call-to-action question to drive engagement: 'What's your experience with AI coding assistants?'
>
> The post is 218 words - right in LinkedIn's engagement sweet spot - and includes 4 contextually relevant hashtags.
>
> This is production-ready content. I could copy this to LinkedIn right now."

**Action**: Click "Copy to Clipboard", show success message

> "The cost? Three-tenths of a cent per post. For comparison, hiring a ghostwriter costs $15 to $30 per post - that's 300 times more expensive.
>
> From a technical standpoint, this demonstrates my ability to integrate third-party AI APIs, implement prompt engineering for consistent output quality, and design user experiences that feel magical.
>
> The API key is stored in session state only - never persisted to disk - which shows security-conscious design.
>
> That's Content Engine - instant, affordable, on-brand content creation."

---

### Module 3: Market Pulse (5:30 - 7:00) - 1.5 minutes

**Narration**:

> "Market Pulse provides real-time technical analysis with 4 professional-grade indicators - all in a single dashboard.
>
> I'll analyze the S&P 500 ETF - ticker symbol SPY - over the past 6 months with daily intervals."

**Action**: Enter SPY, select 6 months / 1 day, click Load Data

> "The data loads in 2 to 3 seconds via the Yahoo Finance API. No manual data entry, no CSV uploads - just instant, real-time market data.
>
> The dashboard uses a 4-panel layout inspired by Bloomberg Terminal design."

**Action**: Scroll through panels

> "Panel 1 shows candlestick price action with a 20-day moving average. Green candles are up days, red are down days. The blue line tracks the trend.
>
> Panel 2 is the Relative Strength Index - RSI. This oscillates between 0 and 100, measuring momentum. Above 70 is overbought, below 30 is oversold.
>
> Panel 3 displays MACD - Moving Average Convergence Divergence. When the blue histogram crosses the orange signal line, it indicates a potential trend reversal.
>
> Panel 4 shows volume. Green bars are high-volume up days, red are high-volume down days. High volume confirms conviction in price moves.
>
> All four indicators are interactive - built with Plotly. I can hover over any data point to see exact values."

**Action**: Hover over candlesticks, show tooltip with OHLC values

> "This works on any ticker - stocks, ETFs, crypto, indices. The calculations happen client-side using the TA-Lib technical analysis library, so it's fast and responsive.
>
> That's Market Pulse - institutional-grade charts in a consumer-friendly interface."

---

### Module 4: Financial Analyst (7:00 - 8:00) - 1 minute

**Narration**:

> "Financial Analyst complements Market Pulse by providing fundamental data for long-term investment decisions.
>
> I'll analyze Apple - ticker AAPL."

**Action**: Enter AAPL, click Analyze Stock

> "In 3 to 5 seconds, we get comprehensive fundamental metrics: market cap, P/E ratio, earnings per share, dividend yield, and 52-week trading range.
>
> Apple has a $2.8 trillion market cap, trades at a P/E of about 28, and yields 0.5% in dividends."

**Action**: Scroll to balance sheet

> "The balance sheet shows total assets, liabilities, and shareholder equity - critical for understanding financial health.
>
> All of this data comes from Yahoo Finance's API, so it's always up to date.
>
> This module is perfect for value investors who want to combine technical and fundamental analysis in one platform."

---

### Module 5: Agent Logic (8:00 - 9:00) - 1 minute

**Narration**:

> "Finally, Agent Logic automates market research by analyzing news sentiment.
>
> I'll search for recent news about NVIDIA's AI chips."

**Action**: Enter NVDA ticker, search for "NVIDIA AI chips news", click Analyze

> "The AI scans recent articles, extracts key themes, and calculates a sentiment score.
>
> NVIDIA is scoring 8 out of 10 - very positive sentiment. Key themes include 'AI demand surge', 'data center growth', and 'chip shortage easing'.
>
> Each article is summarized automatically, saving hours of manual reading.
>
> This demonstrates my ability to build intelligent automation - combining web scraping, natural language processing, and sentiment analysis into a cohesive user experience."

---

### Closing (9:00 - 10:00) - 1 minute

**Narration**:

> "That's Enterprise Hub - 5 modules, 1 unified platform.
>
> From a technical perspective, this project showcases:
>
> - Full-stack Python development with Streamlit
> - API integration with Yahoo Finance, Anthropic Claude, and web scraping
> - Interactive data visualization with Plotly
> - Real-time calculations and reactivity
> - Production-grade error handling and user experience design
> - Deployment to Streamlit Cloud with CI/CD via GitHub Actions
>
> The entire platform is deployed live at this URL [show URL], fully tested with 220+ passing tests, and documented with comprehensive READMEs for each module.
>
> I've also built industry-specific scenario templates, contribution guidelines for open-source collaboration, and security policies.
>
> This isn't just a portfolio piece - it's a production-ready application that delivers real business value.
>
> If you'd like to dive deeper, the full source code is on GitHub, and I'm happy to walk through the architecture in more detail.
>
> Thanks for watching."

**Visual**: Show GitHub repository, highlight key files (app.py, modules/, tests/)

---

## Quick Pitch (60 seconds)

**Target Audience**: LinkedIn posts, Twitter, quick portfolio showcase
**Goal**: Hook attention, drive to full demo or GitHub repo
**Tone**: Energetic, concise, value-focused

### Script

> "I built Enterprise Hub - a unified platform with 5 business tools in one application.
>
> [Show Margin Hunter heatmap] This is Margin Hunter - a Cost-Volume-Profit analyzer. Enter your product economics, and it shows you exactly how many units you need to sell to break even. The sensitivity heatmap visualizes profit at every price and cost combination.
>
> [Show Content Engine] This is Content Engine - AI-powered LinkedIn posts in 3 seconds. I just generated this thought leadership post using Claude AI. Cost? Three-tenths of a cent.
>
> [Show Market Pulse] This is Market Pulse - real-time stock analysis with candlesticks, RSI, MACD, and volume. It's like Bloomberg Terminal, but free.
>
> [Show homepage] Seven modules. One platform. Built with Python, Streamlit, and Plotly. Deployed live with 220+ passing tests.
>
> Full demo on my GitHub - link in bio."

**Runtime**: 55-60 seconds

---

## Individual Module Scripts

### Margin Hunter (3 minutes standalone)

**Opening**:

> "Margin Hunter is a Cost-Volume-Profit analysis tool that answers the question every business leader asks: How many units do I need to sell to break even?
>
> Whether you're launching a SaaS product, pricing an e-commerce item, or planning manufacturing volumes, Margin Hunter gives you instant profitability clarity.
>
> Let me show you how it works."

**Demo**: [Follow full demo script from Module 1 above]

**Closing**:

> "Margin Hunter combines advanced business analytics with an intuitive interface. It's built with NumPy for calculations, Plotly for visualizations, and Streamlit for the web framework.
>
> I've also created industry-specific templates with real-world scenarios for SaaS, e-commerce, and manufacturing.
>
> This is the kind of tool I'd want in every business leader's toolkit - and now it's live and free to use."

---

### Content Engine (2 minutes standalone)

**Opening**:

> "Content Engine solves a problem I experienced firsthand: creating quality LinkedIn content is time-consuming.
>
> Most professionals know they should post regularly, but writing a single post takes 30 to 45 minutes - from ideation to drafting to editing. That's unsustainable.
>
> Content Engine uses Claude AI to generate polished, on-brand posts in 3 seconds.
>
> Here's how it works."

**Demo**: [Follow full demo script from Module 2 above]

**Closing**:

> "From a technical standpoint, this demonstrates prompt engineering, API integration with Anthropic Claude, and session-based security for API keys.
>
> But from a user standpoint, it's magic. Idea to published post in under 2 minutes.
>
> The cost is negligible - $0.003 per post - making this 300 times cheaper than hiring a ghostwriter.
>
> Try it live at the URL below."

---

### Market Pulse (1.5 minutes standalone)

**Opening**:

> "Market Pulse provides institutional-grade technical analysis for anyone with an internet connection.
>
> If you've ever used Bloomberg Terminal or TradingView, you'll recognize the 4-panel layout: candlesticks, RSI, MACD, and volume.
>
> But unlike those platforms, Market Pulse is free, web-based, and requires zero setup.
>
> Let me analyze the S&P 500."

**Demo**: [Follow full demo script from Module 3 above]

**Closing**:

> "Market Pulse demonstrates my ability to work with financial APIs, implement technical indicators using the TA-Lib library, and create interactive visualizations with Plotly.
>
> It's fast, responsive, and works on any publicly traded security.
>
> This is the power of modern Python web frameworks like Streamlit - professional tools delivered in minutes, not months."

---

## Technical Deep-Dive (15 minutes)

**Target Audience**: Engineering teams, technical interviewers, senior developers
**Goal**: Showcase architecture, code quality, testing, and technical decisions
**Tone**: Technical, detailed, confident in expertise

### Script Outline

**1. Introduction (0:00 - 1:00)**

> "Today I'm going to walk through the technical architecture of Enterprise Hub - a full-stack Python application with 5 integrated modules.
>
> I'll cover:
> - Modular architecture and separation of concerns
> - API integration strategies
> - Real-time reactivity patterns in Streamlit
> - Testing and CI/CD
> - Performance optimizations
>
> Let's start with the project structure."

**2. Architecture Overview (1:00 - 3:00)**

**Visual**: Show file tree in IDE

> "The project follows a modular monolith pattern. Each module is a self-contained Python file in the `/modules` directory:
>
> - `margin_hunter.py` - CVP analysis logic
> - `content_engine.py` - AI content generation
> - `market_pulse.py` - Stock charting
> - `financial_analyst.py` - Fundamental data
> - `agent_logic.py` - Sentiment analysis
>
> The main `app.py` file handles routing and session management. Shared utilities like data loading, logging, and custom exceptions live in `/utils`.
>
> This structure makes it easy to add new modules, test in isolation, and collaborate with other developers.
>
> Each module exports a single `render()` function that Streamlit calls based on the selected navigation item."

**3. Key Technical Decisions (3:00 - 6:00)**

**Session State Management**:

> "Streamlit re-runs the entire script on every user interaction. To maintain state between runs, I use `st.session_state`.
>
> For example, in Content Engine, the API key is stored in session state so users don't have to re-enter it on every generation."

**Visual**: Show code snippet from `content_engine.py`

**Async API Calls**:

> "The Anthropic API can take 3 to 5 seconds to respond. I use Streamlit's caching decorators to prevent redundant calls.
>
> For the Market Pulse module, I cache yfinance results for 5 minutes using `@st.cache_data`. This improves performance dramatically when users toggle between tickers."

**4. Testing Strategy (6:00 - 9:00)**

**Visual**: Show test files in IDE

> "Enterprise Hub has 220+ automated tests covering:
> - Unit tests for calculation logic (CVP formulas, margin calculations)
> - Integration tests for API clients (mocked API responses)
> - End-to-end UI tests for critical user flows
>
> I use `pytest` for test running, `unittest.mock` for mocking external dependencies, and `pytest-cov` for coverage reports.
>
> The test suite runs automatically on every pull request via GitHub Actions CI/CD."

**Visual**: Show GitHub Actions workflow file

> "The CI pipeline runs linting with Flake8, formatting checks with Black, and the full test suite. If any check fails, the PR is blocked from merging.
>
> This ensures code quality and prevents regressions."

**5. Performance Optimizations (9:00 - 12:00)**

> "Streamlit applications can become slow if you're not careful about re-rendering. I've implemented several optimizations:
>
> **1. Selective re-computation**: In Margin Hunter, calculations only trigger when input values change, not on every re-run.
>
> **2. Chart rendering optimization**: Plotly charts are expensive to render. I cache chart objects and only regenerate when data changes.
>
> **3. Lazy loading**: The Financial Analyst module only fetches balance sheet data when the user expands that section.
>
> These optimizations make the app feel instantaneous, even with complex visualizations."

**6. Deployment & Scalability (12:00 - 14:00)**

> "Enterprise Hub deploys to Streamlit Cloud, which handles all infrastructure automatically.
>
> The deployment process is simple:
> 1. Push code to GitHub
> 2. Streamlit Cloud detects changes
> 3. Automatic rebuild and deploy in 2 minutes
>
> For scalability, Streamlit Cloud uses containerization and auto-scaling. The app can handle hundreds of concurrent users without performance degradation.
>
> If I were to scale beyond Streamlit Cloud, I'd containerize with Docker and deploy to AWS ECS or Google Cloud Run."

**7. Future Enhancements (14:00 - 15:00)**

> "The roadmap includes:
> - User authentication and saved scenarios
> - Multi-platform content generation (Twitter, Instagram)
> - Portfolio tracking across modules
> - Real-time alerts for stock movements
>
> The modular architecture makes these features straightforward to add without disrupting existing functionality.
>
> That's the technical deep-dive. Questions welcome in the comments or via GitHub issues."

---

## Portfolio Highlight Reel (3 minutes)

**Target Audience**: General audience, portfolio viewers, job applications
**Goal**: Show breadth of skills, visual appeal, energy
**Tone**: Fast-paced, exciting, visually driven

### Script

**Opening (0:00 - 0:15)**:

> "I'm Cayman Roden, and I build software that solves real problems.
>
> This is Enterprise Hub - five business tools in one platform. Let me show you what it can do."

**Fast Montage (0:15 - 2:30)**:

**15 seconds each module, rapid cuts**

**Margin Hunter**:
> "Break-even analysis for any business model. Watch the heatmap change in real-time."
**Visual**: Fast typing of inputs, show metrics update, zoom into heatmap

**Content Engine**:
> "AI-generated LinkedIn posts in 3 seconds. Professional quality, zero effort."
**Visual**: Click generate, post appears instantly, show copy-to-clipboard

**Market Pulse**:
> "Real-time stock charts. Four indicators. Bloomberg Terminal quality."
**Visual**: Quick pan across 4 panels, hover interactions

**Financial Analyst**:
> "Fundamental data at your fingertips. No spreadsheets needed."
**Visual**: Rapid ticker entry, metrics load

**Agent Logic**:
> "AI-powered news analysis. Know the market sentiment instantly."
**Visual**: Search executes, sentiment score appears

**Closing (2:30 - 3:00)**:

> "Python. Streamlit. Plotly. Claude AI. Yahoo Finance API.
>
> 220+ passing tests. CI/CD. Deployed live.
>
> This is Enterprise Hub.
>
> Code on GitHub. Live demo in the description.
>
> Let's build something."

**Visual**: Rapid showcase of code snippets, GitHub repo, live URL

---

## Delivery Tips

### Voice & Pacing

1. **Speak 20% slower than normal conversation**
   - Allow viewers to absorb information
   - Pause after key metrics or features

2. **Emphasize technical terms clearly**
   - "Cost-Volume-Profit" (pause between each word)
   - "Claude 3.5 Sonnet" (not "Claude three-point-five")
   - "RSI" not "R-S-I" (say the acronym as a word)

3. **Energy modulation**
   - High energy for openings and key features
   - Lower energy for technical explanations (calm, confident)
   - Rising energy for closings (call to action)

### Visual Coordination

1. **Narration matches visual**
   - When you say "Watch this", immediately perform the action
   - Pause speaking while charts load/render
   - Let impressive visuals breathe (2-3 seconds of silence)

2. **Cursor movement**
   - Move deliberately, not erratically
   - Point to elements as you mention them
   - Use a cursor highlighter for clarity

3. **Zoom & Pan**
   - Zoom into important UI elements (e.g., heatmap cells)
   - Pan slowly across multi-panel layouts
   - Return to full view before transitioning to next section

### Technical Terminology

Use precise terms to demonstrate expertise:

- "Real-time reactivity" (not "it updates fast")
- "Session-based state management" (not "it remembers stuff")
- "Sensitivity analysis" (not "what-if scenarios")
- "Contribution margin" (not "profit per unit")
- "Prompt engineering" (not "writing good prompts")

### Common Mistakes to Avoid

1. **Talking too fast** - Viewers need time to read on-screen text
2. **Apologizing** - Never say "this is kind of rough" or "I should have..."
3. **Hedging** - Say "This is powerful" not "I think this is pretty good"
4. **Filler words** - Edit out "um", "uh", "you know", "like"
5. **Over-explaining** - Trust viewers to understand basic concepts

### Recording Checklist

Before hitting record:

- [ ] Script printed or on second monitor
- [ ] Water nearby (prevent dry mouth)
- [ ] Phone on silent
- [ ] Background noise eliminated (close windows, turn off AC)
- [ ] Browser in incognito mode (no extensions)
- [ ] App pre-loaded to starting state
- [ ] Timer visible (stay on pace)
- [ ] Voice warm-up (read script aloud 2x)

---

## Export & Distribution

### Video Formats

**Full Demo (8-10 min)**:
- **YouTube**: 1080p MP4, 30fps
- **LinkedIn**: 720p MP4, max 10 minutes
- **Portfolio website**: 720p MP4 or embed YouTube

**Quick Pitch (60 sec)**:
- **Twitter**: 720p MP4, max 2:20 minutes
- **LinkedIn**: 1080p MP4
- **Instagram Reel**: 1080x1920 (vertical), max 90 sec

**Highlight Reel (3 min)**:
- **Portfolio hero video**: 1080p MP4
- **GitHub README**: Embed YouTube link
- **Job applications**: MP4 attachment or Loom link

### Captions & Subtitles

**Auto-generate with**:
- YouTube auto-captions (then edit for accuracy)
- Rev.com ($1.50/min, 99% accuracy)
- Descript (AI-powered, free tier available)

**Why captions matter**:
- 85% of LinkedIn videos watched without sound
- Accessibility for deaf/hard-of-hearing viewers
- SEO benefits (searchable text)

### Thumbnails

**Design eye-catching thumbnails**:
- Use Figma, Canva, or Photoshop
- Include module name + key visual (e.g., heatmap, chart)
- Bright, high-contrast colors
- Large text (readable at small sizes)
- Your face/logo for brand recognition

**Thumbnail templates**:
- Margin Hunter: Heatmap background + "BREAK-EVEN ANALYSIS" text
- Content Engine: AI brain graphic + "AI CONTENT IN 3 SECONDS"
- Market Pulse: Candlestick chart + "REAL-TIME STOCK ANALYSIS"

---

**Questions or feedback?** Open an issue on [GitHub](https://github.com/ChunkyTortoise/enterprise-hub/issues).

---

Built by **Cayman Roden** | [GitHub](https://github.com/ChunkyTortoise) | [Live Demo](https://enterprise-app-mwrxqf7cccewnomrbhjttf.streamlit.app/)
