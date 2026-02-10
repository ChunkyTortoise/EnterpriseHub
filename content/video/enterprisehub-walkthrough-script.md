# EnterpriseHub Video Walkthrough Script

**Total Duration:** 6:30
**Target Audience:** Potential clients, employers, and customers evaluating the platform
**Demo URL:** https://ct-enterprise-ai.streamlit.app
**GitHub:** https://github.com/ChunkyTortoise/EnterpriseHub

> **⚠️ Before Recording:** Verify that the demo URL (https://ct-enterprise-ai.streamlit.app) is active and responding. Streamlit Community Cloud apps can go to sleep after inactivity — wake the app at least 30 minutes before recording to ensure smooth performance during the demo.

---

## Section 1: Hook & Introduction [0:00-0:30]

### Visual
- Opening title card: "EnterpriseHub: AI-Powered Real Estate Platform"
- Cut to narrator on camera (clean background, good lighting)
- Brief B-roll of frustrated real estate agent with phone/computer

### Audio
"Real estate teams lose 40% of leads because their response time exceeds the critical 5-minute window. That's thousands of dollars in lost commission every week.

I built EnterpriseHub to solve this problem. It's an AI-powered platform with three specialized bots that qualify leads instantly — 24/7 — and sync everything to your CRM.

The platform is production-ready with 4,937 automated tests, 89% token cost reduction through intelligent caching, and P95 latency under 2 seconds.

Let me show you how it works."

### Duration
- 0:00-0:10: Problem statement with statistic
- 0:10-0:20: Solution overview
- 0:20-0:30: Credibility metrics + transition

### B-roll Notes
- Animation showing "40% LEADS LOST" statistic
- Quick montage of the three bot icons (Lead, Buyer, Seller)
- CI green checkmark badge animation

---

## Section 2: Architecture Overview [0:30-1:30]

### Visual
- Full-screen architecture diagram from README (Mermaid diagram)
- Zoom into each layer as mentioned
- Animated arrows showing data flow

### Audio
"Here's how the system is architected.

At the top, you have three specialized bot services — Lead Bot on port 8001, Seller Bot on 8002, and Buyer Bot on 8003. Each bot handles a specific part of the customer journey.

In the middle is the FastAPI orchestration layer. This is where the magic happens. The Claude Orchestrator handles multi-strategy parsing with a three-tier cache — memory, Redis, and database — which is how we achieved that 89% cost reduction.

The Agent Mesh Coordinator manages 22 specialized agents with capability routing and full audit trails. And the Handoff Service enables seamless bot-to-bot transitions at a 0.7 confidence threshold.

On the right, we integrate with GoHighLevel, HubSpot, and Salesforce CRMs. On the left, we connect to multiple AI services — Claude as primary, Gemini for analysis, Perplexity for research, and OpenRouter as fallback.

Everything is backed by PostgreSQL for persistence and Redis for caching and rate limiting."

### Duration
- 0:30-0:45: Bot services layer
- 0:45-1:05: Orchestration layer (Claude Orchestrator, Agent Mesh, Handoff)
- 1:05-1:20: CRM integrations and AI services
- 1:20-1:30: Data layer + transition

### B-roll Notes
- Animated zoom on each component as mentioned
- Highlight the "L1/L2/L3 cache" text when discussing cost reduction
- Show data flow animation from bots → orchestration → CRM

---

## Section 3: Live Demo - Lead Bot [1:30-3:00]

### Visual
- Browser navigation to https://ct-enterprise-ai.streamlit.app
- Show the Lead Bot interface
- Type a sample conversation (see script below)
- Highlight intent detection results and score

### Audio
"Let me show you a live demo. I'm opening the Streamlit dashboard hosted at ct-enterprise-ai.streamlit.app.

Here's the Lead Bot interface. Let me simulate a new lead coming in."

*[Type in chat]*: "Hi, I saw your listing on Zillow. I'm looking for a 3-bedroom house in Rancho Cucamonga, budget around 600K."

"Watch what happens. The bot detects this is a buyer lead with high intent. It extracts the budget — 600K — the location preference, and the property type.

Now look at the qualification panel on the right. The bot has assigned a lead score of 78 out of 100, which triggers a 'Warm-Lead' temperature tag. It's also identified handoff signals to the Buyer Bot because the user expressed clear purchase intent.

The conversation continues naturally while, behind the scenes, the system is qualifying this lead, preparing handoff context, and readying CRM sync."

*[Type follow-up]*: "Yes, I'm pre-approved for 650K and need to move in the next 60 days."

"Now the score jumps to 89 — that's a Hot-Lead. The bot detected pre-approval status and urgency. This would trigger priority workflows in a production setup — instant agent notification and expedited follow-up."

### Duration
- 1:30-1:45: Navigate to demo, show interface
- 1:45-2:15: First message + analysis
- 2:15-2:40: Follow-up message + score increase
- 2:40-3:00: Explain handoff signals + transition

### B-roll Notes
- Cursor highlight when typing
- Zoom on lead score number when it changes
- Highlight "Hot-Lead" tag with brief animation
- Show handoff signals panel

---

## Section 4: BI Dashboard Walkthrough [3:00-4:00]

### Visual
- Navigate to BI dashboard tab
- Show Monte Carlo simulation panel
- Scroll to sentiment analysis section
- Demonstrate churn detection features

### Audio
"Now let's look at the Business Intelligence dashboard.

This Monte Carlo simulation runs 10,000 scenarios to predict commission outcomes. You can adjust probability weightings and see the confidence intervals for revenue forecasting. This helps teams set realistic targets and understand variance.

Here's the sentiment analysis panel. The system tracks conversation sentiment over time — you can see spikes when leads express frustration or excitement. This helps identify at-risk conversations before they go cold.

The churn detection module analyzes engagement patterns. It flags contacts who haven't responded in 7, 14, or 30 days and suggests re-engagement actions. This alone can recover 15-20% of leads that would otherwise be lost.

All of this updates in real-time as conversations happen. No manual data entry, no spreadsheets to maintain."

### Duration
- 3:00-3:20: Monte Carlo simulation
- 3:20-3:40: Sentiment analysis
- 3:40-4:00: Churn detection + transition

### B-roll Notes
- Run Monte Carlo simulation live (click "Run Simulation")
- Hover over sentiment chart to show tooltips
- Highlight churn risk flags in red/yellow/green

---

## Section 5: Technical Deep Dive [4:00-5:00]

### Visual
- VS Code or GitHub showing project structure
- Navigate to key files
- Show code snippets with syntax highlighting

### Audio
"For the developers watching, let's look under the hood.

The project is organized into clear modules. The `agents/` directory contains the three bot implementations — Lead, Buyer, and Seller. Each bot has its own personality, qualification logic, and handoff triggers.

The `services/` directory is where the business logic lives. Here's the Claude Orchestrator — this handles all LLM communication with the three-tier caching I mentioned. L1 is in-memory for instant hits, L2 uses Redis for distributed caching, and L3 falls back to PostgreSQL for persistence.

Let me show you the Handoff Service. This is the core of cross-bot transitions."

*[Show code snippet from jorge_handoff_service.py]*

```python
class JorgeHandoffService:
    """Evaluates and executes cross-bot handoffs based on intent signals."""
    
    THRESHOLDS = {
        ("lead", "buyer"): 0.7,
        ("lead", "seller"): 0.7,
        ("buyer", "seller"): 0.8,
        ("seller", "buyer"): 0.6,
    }
    
    CIRCULAR_WINDOW_SECONDS = 30 * 60  # 30 minutes
    HOURLY_HANDOFF_LIMIT = 3
    DAILY_HANDOFF_LIMIT = 10
```

"You can see the confidence thresholds for each handoff direction. Lead-to-Buyer requires 0.7 confidence. The system also prevents circular handoffs — if a contact was just handed off, they can't bounce back within 30 minutes. And there are rate limits: 3 handoffs per hour, 10 per day per contact.

The API layer has 82 FastAPI routes covering webhooks, CRM sync, analytics, and health checks. Everything is async, validated with Pydantic, and fully typed."

### Duration
- 4:00-4:15: Project structure overview
- 4:15-4:30: Claude Orchestrator + caching
- 4:30-4:50: Handoff Service code walkthrough
- 4:50-5:00: API routes + transition

### B-roll Notes
- Use VS Code with One Dark Pro or similar theme
- Highlight key lines in code snippets
- Brief flash of file tree when discussing structure

---

## Section 6: Performance Metrics [5:00-5:45]

### Visual
- Metrics dashboard or README metrics table
- Animated counters for key numbers
- CI/CD pipeline green status

### Audio
"Here are the production metrics that matter.

89% token cost reduction — that's from 93,000 tokens per workflow down to 7,800. The three-tier cache achieves an 87% hit rate for repeated queries.

P95 latency is under 2 seconds for the Lead Bot. That includes LLM calls, database writes, and cache operations. The orchestration layer adds less than 200 milliseconds of overhead.

The test suite has 4,937 automated tests — all green in CI. This covers unit tests, integration tests, and end-to-end scenarios. Every PR runs the full suite before merge.

The platform integrates with three CRMs — GoHighLevel, HubSpot, and Salesforce. The GoHighLevel client is rate-limited to 10 requests per second to stay within API limits.

And the bot handoff accuracy sits at 0.7 confidence threshold with circular prevention and rate limiting built in."

### Duration
- 5:00-5:15: Cost reduction + cache hit rate
- 5:15-5:30: Latency + test coverage
- 5:30-5:45: CRM integrations + handoff accuracy

### B-roll Notes
- Animated counters: 93K → 7.8K tokens
- Show GitHub Actions green checkmark
- Brief table view of all metrics

---

## Section 7: Quick Start & Call to Action [5:45-6:30]

### Visual
- Terminal showing `make demo` command
- Docker Compose starting up
- GitHub repository page
- Contact information / LinkedIn / portfolio

### Audio
"Getting started is simple.

Clone the repo, install requirements, and run `make demo`. This launches a fully functional demo with pre-populated data — no API keys, no database setup required.

For full deployment, copy the example environment file, add your keys, and run `docker-compose up`. PostgreSQL, Redis, the API, all three bots, and the Streamlit dashboard come up in under 10 minutes.

The repo is at github.com/ChunkyTortoise/EnterpriseHub. Star it if you find it useful.

If you're looking to build something similar — AI-powered automation, multi-agent systems, or business intelligence dashboards — I'm available for consulting and contract work. You can reach me through LinkedIn or my portfolio at chunkytortoise.github.io.

Thanks for watching. Go check out the live demo and let me know what you think."

### Duration
- 5:45-6:00: Quick start commands
- 6:00-6:15: Full deployment + GitHub
- 6:15-6:30: CTA + sign-off

### B-roll Notes
- Terminal recording of `make demo` output
- Docker Compose containers starting
- GitHub star button click
- LinkedIn profile / portfolio URL on screen

---

## Production Notes

### Recording Setup
- **Microphone:** USB condenser or lapel mic (avoid built-in laptop mic)
- **Camera:** 1080p minimum, centered framing
- **Lighting:** Ring light or two-point lighting setup
- **Background:** Clean, professional (bookshelf, plants, or solid color)
- **Screen Recording:** 1440p or 4K, 30fps minimum

### Software Recommendations
- **Screen Recording:** OBS Studio or Loom (pro)
- **Video Editing:** DaVinci Resolve (free) or Final Cut Pro
- **Captions:** Descript or Rev.com for accuracy

### Delivery Tips
- Speak 10-20% slower than conversational pace
- Pause briefly between sections for editing flexibility
- Record each section separately for easier editing
- Do 2-3 takes of each section and pick the best

### Post-Production
- Add lower-third graphics for key metrics
- Include subtle background music (royalty-free)
- Add chapter markers for YouTube
- Create thumbnail with "4,937 Tests" and "89% Cost Reduction" text

### Thumbnail Concepts
1. Split screen: Code on left, dashboard on right, "EnterpriseHub" title
2. Face + "AI Real Estate Platform" + "Live Demo" badge
3. Architecture diagram with "Production Ready" overlay

---

## Key Moments/Highlights

| Timestamp | Moment | Why It Matters |
|-----------|--------|----------------|
| 0:15 | "40% of leads lost" | Hooks viewer with relatable pain point |
| 1:45 | Live demo starts | Shows real product, not slides |
| 2:20 | Score jumps to 89 | Demonstrates intelligent qualification |
| 3:10 | Monte Carlo simulation | Shows advanced BI capabilities |
| 4:35 | Handoff Service code | Proves technical depth |
| 5:05 | "89% cost reduction" | Quantified business value |
| 6:15 | Consulting CTA | Converts viewers to leads |

---

## File References

- Architecture: [`README.md`](README.md#architecture)
- Handoff Service: [`ghl_real_estate_ai/services/jorge/jorge_handoff_service.py`](ghl_real_estate_ai/services/jorge/jorge_handoff_service.py)
- Claude Orchestrator: [`ghl_real_estate_ai/services/claude_orchestrator.py`](ghl_real_estate_ai/services/claude_orchestrator.py)
- Demo URL: https://ct-enterprise-ai.streamlit.app
- GitHub: https://github.com/ChunkyTortoise/EnterpriseHub

---

*Script Version: 1.0*  
*Created: February 2026*  
*Estimated Word Count: ~1,100 words (2.8 words/second average)*
