# PeoplePerHour + Guru Proposals — Feb 19, 2026

**Prepared by**: Cayman Roden (caymanroden@gmail.com)
**GitHub**: github.com/ChunkyTortoise
**Total proposals**: 15

**Account Status**:
- **PeoplePerHour**: NOT logged in. Account likely needs creation or login. HUMAN ACTION REQUIRED to register as freelancer at peopleperhour.com/site/register#freelancer
- **Guru.com**: NOT logged in. Account likely needs creation. HUMAN ACTION REQUIRED to register at guru.com/registeraccount.aspx

---

## PPH-1: AI-Powered Price Scraper & Monitoring System (Multi-Website)
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-integration/ai-powered-price-scraper-monitoring-system-multi-website-4474651
**Budget**: $800 (fixed)
**Posted**: 20 hours ago
**Match score**: GREEN -- clear scope, strong budget, exact tech match (Python, scraping, AI, monitoring)

### Proposal:

I build exactly this -- AI-powered scraping systems with monitoring dashboards are in my wheelhouse.

Here's what I'd deliver: a scalable Python scraper using httpx (async) + BeautifulSoup/Playwright for JS-heavy sites, with AI-assisted selector adaptation so it doesn't break when sites change layouts. Price data feeds into a PostgreSQL store with Redis caching, and you get a real-time monitoring dashboard showing price changes, alerts, and trends.

My approach:
1. Map your target websites and identify data extraction patterns (selectors, APIs, or headless browser)
2. Build the async scraping engine with rate limiting, retry logic, and proxy rotation support
3. Add AI-powered comparison and anomaly detection -- flag price drops, outliers, and competitive shifts
4. Deploy with a simple dashboard and configurable alerts (email, webhook, or Slack)

I've built production data pipelines processing 50K+ rows with anomaly detection, all backed by automated test suites (8,500+ tests across my repos, all CI green). I also have experience with 3-tier Redis caching that reduced API costs by 89%.

I can have a working MVP within 5-7 days. Happy to share a relevant code sample from my GitHub before you commit.

One question: How many websites do you need scraped initially, and are any of them JavaScript-heavy (requiring a headless browser) vs. simple HTML?

---

## PPH-2: AI Sales Automation Expert: Build Data & Outreach Workflow
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-agent-development/ai-sales-automation-expert-build-data-outreach-workflow-4474309
**Budget**: $336 (fixed)
**Posted**: 2 days ago
**Match score**: GREEN -- GTM orchestration, AI-driven sales, automation pipeline

### Proposal:

GTM automation with AI orchestration is something I've built production systems for -- I can move fast on this.

You need a pipeline that finds prospects, enriches their data, scores them, and triggers personalized outreach at scale. Here's my approach:

1. **Data layer**: Build the prospect discovery and enrichment pipeline -- pull from your data sources, enrich with company/contact data via API integrations, and store in a structured CRM-ready format
2. **AI scoring**: Implement lead scoring using Claude/GPT to analyze prospect fit, intent signals, and engagement likelihood -- not just keyword matching, but contextual analysis
3. **Outreach orchestration**: Automated multi-channel sequences (email, LinkedIn, etc.) with AI-personalized messaging that references specific prospect details
4. **Dashboard**: Simple monitoring view showing pipeline metrics, conversion rates, and sequence performance

I recently built a 3-bot AI orchestration system for a real estate client -- lead qualification, buyer matching, and seller engagement all coordinated through a unified pipeline with 22 custom CRM fields and automated handoff logic. That system has 1,140+ automated tests and is in production.

I can deliver a working v1 within a week. Would love to understand: what's your current tech stack for CRM/email, and roughly how many prospects per month are you targeting?

---

## PPH-3: GoHighLevel Marketing & Ads Automation Specialist
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-software-development/gohighlevel-marketing-ads-automation-specialist-4468315
**Budget**: $202 (fixed, opportunity tag)
**Posted**: 23 days ago
**Match score**: GREEN -- GoHighLevel is my core domain expertise

### Proposal:

GHL automation is my specialty -- I just finished building a complete AI-powered GHL system for a real estate client and can bring that expertise directly to your project.

Here's what I recently delivered: a 3-workflow GHL automation system with 22 custom fields, automated lead qualification via AI chatbots (lead, buyer, and seller bots), pipeline management, SMS sequences, and intelligent handoff logic. The whole system runs on GoHighLevel with custom API integrations.

My approach for your project:
1. Audit your current GHL setup -- workflows, pipelines, custom fields, and identify automation gaps
2. Build your marketing workflows: lead capture triggers, tag-based routing, automated nurture sequences, and pipeline stage automation
3. Set up ads integration: connect your ad platforms to GHL, build attribution tracking, and automate lead assignment from ad sources
4. Test end-to-end with dummy contacts, document every workflow, and hand off with a walkthrough

I can deliver within 3-5 days depending on complexity. My GHL work is backed by 114 integration-specific tests -- I don't just configure, I verify everything works.

Quick question: What's your current GHL setup like -- are you starting from scratch, or do you have existing workflows that need enhancement?

---

## PPH-4: Website Development Using GoHighLevel
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-website-development/i-need-a-website-develop-using-go-high-level-4471571
**Budget**: $135 (fixed)
**Posted**: 12 days ago
**Match score**: GREEN -- GoHighLevel website + blog, brain injury niche

### Proposal:

I can build this for you in GHL -- I've been working extensively with GoHighLevel's website builder and API ecosystem.

For your brain injury website and blog, here's my plan:
1. Set up the site structure in GHL's website builder -- homepage, about, resources, blog section, and contact/intake forms
2. Configure the blog with proper categories, SEO-friendly URLs, and an easy-to-use content management flow so you can publish new posts yourself
3. Wire up contact forms to GHL's CRM pipeline -- new submissions automatically create contacts, trigger notification workflows, and start any follow-up sequences you need
4. Mobile-responsive design, fast loading, and accessibility considerations (important for brain injury community)

I recently built a complete GHL integration for a real estate client -- 22 custom fields, 3 automated workflows, pipeline management, and AI-powered chatbots all running through GHL. I know the platform inside and out.

Delivery: 2-3 days for the full site. I'll include a Loom walkthrough showing you how to manage blog posts and update content yourself. Fixed price, one revision included.

One question: Do you have existing content (text, images) for the site, or do you need help structuring the content as well?

---

## PPH-5: AI WhatsApp Sales Agent
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-chatbot-development/ai-what-app-sales-agent-4474027
**Budget**: $54 (fixed)
**Posted**: 3 days ago
**Match score**: YELLOW -- budget is very low, but perfect chatbot tech match. Worth bidding higher.

### Proposal:

I build AI-powered sales chatbots -- this is exactly what I do.

I recently built a 3-bot AI system for a real estate client: lead qualification bot, buyer bot, and seller bot, all communicating via SMS through GoHighLevel CRM. Each bot handles natural conversation, qualifies leads through structured questions, detects intent, and hands off to a human agent when ready. The system has 1,140+ automated tests and handles compliance (TCPA opt-out, AI disclosure).

For your WhatsApp sales bot, here's what I'd deliver:
1. AI-powered conversational agent using Claude or GPT that understands your products/services and handles sales inquiries naturally
2. WhatsApp Business API integration for automated responses
3. Lead qualification logic -- ask the right questions, score readiness, and route hot leads to your team
4. FAQ handling, objection management, and appointment booking capabilities
5. Dashboard or CRM integration so you can track conversations and conversions

Note: A production-quality AI WhatsApp bot with proper API integration, testing, and deployment typically runs $400-600 for a solid v1. I'd be happy to discuss scope and find a number that works for both of us.

What messaging platform are you using for WhatsApp -- the official Business API, or a third-party service like Twilio/360dialog?

---

## PPH-6: Data Center Construction Intelligence Platform
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-data-services/-4469857
**Budget**: $256 (fixed, opportunity tag)
**Posted**: 18 days ago (0 proposals!)
**Match score**: GREEN -- data platform, AI/Python, zero competition

### Proposal:

I noticed this has zero proposals -- I'd like to change that. Building data intelligence platforms is core to what I do.

For your Data Center Construction Intelligence Platform, I can help with the pre-development research and architecture phase:

1. **Requirements analysis**: Map out the data sources, entities, and relationships specific to data center construction -- site selection, permitting, supply chain, contractor management, capacity planning
2. **Architecture design**: Design the platform architecture -- data ingestion pipelines, storage (PostgreSQL + vector DB for AI-powered search), API layer (FastAPI), and frontend considerations
3. **AI integration plan**: Identify where AI adds the most value -- document analysis, predictive scheduling, cost estimation, risk assessment, or automated reporting
4. **MVP scope definition**: Define a focused first phase that delivers immediate value while establishing the foundation for expansion

I've built enterprise AI platforms with RAG (retrieval-augmented generation) pipelines, multi-tenant architecture, and production-grade APIs. My portfolio includes 11 production repos with 8,500+ automated tests, all CI green. I also have experience with 3-tier caching that reduced LLM costs by 89%.

I'm available to start immediately. Would a 30-minute discovery call help align on scope and deliverables?

---

## PPH-7: Proving Business Concepts Fast Using AI (MVP Builder)
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-model-development/proving-business-concepts-fast-using-ai-4468512
**Budget**: $27/hr (hourly)
**Posted**: 22 days ago
**Match score**: YELLOW -- interesting concept, decent hourly rate, AI/Python match

### Proposal:

This is a great concept -- using AI to rapidly validate business ideas before committing development resources.

I can build an MVP that takes a business concept (written in your formal structure) and uses AI to:
1. **Market analysis**: Pull relevant market data and competitive landscape using web scraping + AI summarization
2. **Feasibility scoring**: Analyze the concept against common failure patterns, market fit indicators, and resource requirements
3. **Financial modeling**: Generate rough unit economics, TAM/SAM/SOM estimates, and break-even projections based on the concept parameters
4. **Validation roadmap**: Output a prioritized list of assumptions to test, with suggested validation methods

Tech stack: Python + FastAPI backend, Claude/GPT for the analysis engine, simple Streamlit frontend for the interface. I've built 5 live Streamlit demos and have production experience with LLM orchestration (including a 3-tier caching system that reduced AI costs by 89%).

I can have a working prototype within a week. The AI-powered analysis won't replace human judgment, but it can compress days of research into minutes and surface patterns that aren't immediately obvious.

What format are your business concepts currently in -- structured documents, pitch decks, or something else?

---

## PPH-8: AI-Powered Language Learning Platform
**Platform**: PeoplePerHour
**URL**: https://www.peopleperhour.com/freelance-jobs/artificial-intelligence/artificial-intelligence-agent-development/ai-powered-language-learning-platform-4474314
**Budget**: $148 (fixed)
**Posted**: 2 days ago
**Match score**: YELLOW -- good AI/ML match, budget is low for scope described

### Proposal:

Extending an AI-powered language learning platform is a great project -- I have direct experience with AI agent development and natural language processing.

For enhancing your platform's AI/ML capabilities, I can help with:
1. **Conversational AI improvements**: Better dialogue management, context retention across sessions, and adaptive difficulty based on learner performance
2. **Speech/pronunciation features**: Integration with speech-to-text APIs for pronunciation scoring and feedback
3. **Personalized learning paths**: ML-based progression that adapts to individual learning patterns, strengths, and weaknesses
4. **Content generation**: AI-powered exercise generation (fill-in-the-blank, translation, comprehension questions) from your existing content library

I've built multi-agent AI systems with sophisticated conversation management -- my most recent project is a 3-bot system that handles natural conversations, detects intent, manages state across sessions, and routes between specialized agents. The orchestration layer handles <200ms overhead with 3-tier caching.

Note: Depending on the scope of enhancements you need, $148 may cover an initial assessment and targeted improvement to one feature area. Happy to discuss phased delivery.

What's the current tech stack, and which specific AI/ML capabilities are you looking to add first?

---

## GURU-1: Agentic AI Development
**Platform**: Guru
**URL**: https://www.guru.com/jobs/agentic-ai-development/2116146
**Budget**: $10,000 - $25,000 (fixed)
**Posted**: Feb 18, 2026
**Match score**: GREEN -- high-value, agentic AI, document generation -- perfect match

### Proposal:

Agentic AI that generates documents from templates and prompts is exactly what I build in production.

I've built and deployed multi-agent AI systems including:
- A 3-bot agentic system for real estate (lead qualification, buyer matching, seller engagement) with autonomous decision-making, cross-agent handoffs, and CRM integration
- AgentForge, my open-source multi-agent orchestration framework with 4.3M tool dispatches/sec and <200ms orchestration overhead
- RAG (retrieval-augmented generation) pipelines that ground AI output in your actual documents and data

For your document generation system, here's my approach:
1. **Document understanding**: Parse and index your reference documents using embeddings + vector search (RAG pipeline) so the AI has deep context about your domain
2. **Agent architecture**: Build specialized agents -- one for document analysis, one for content generation, one for quality validation -- coordinated through an orchestration layer
3. **Template engine**: Design a flexible template system where agents populate sections based on prompts and source documents, maintaining consistent formatting and tone
4. **Quality assurance**: Automated checks for accuracy, completeness, and compliance with your document standards
5. **Deployment**: Production-ready API with authentication, rate limiting, and monitoring

Tech stack: Python, FastAPI, Claude API (or your preferred LLM), PostgreSQL, Redis caching (I've achieved 89% cost reduction through 3-tier caching), Docker deployment.

My repos have 8,500+ automated tests across 11 production projects. I deliver code that's tested, documented, and maintainable -- not prototypes.

I'm available to start this week. Happy to schedule a call to discuss requirements and architecture in detail.

---

## GURU-2: SAM.gov Automation Platform
**Platform**: Guru
**URL**: https://www.guru.com/jobs/developper-samgov-automation-platform/2116105
**Budget**: $1,000 - $2,500 (fixed)
**Posted**: Feb 16, 2026
**Match score**: GREEN -- Python automation, web scraping, government platform integration

### Proposal:

Building a production-ready SAM.gov automation platform is a well-scoped project that plays to my strengths in Python automation and web scraping.

Here's my approach:
1. **SAM.gov integration**: Build the data extraction layer -- whether via their public API, structured web scraping, or a combination. Handle authentication, rate limiting, and data parsing for registration workflows
2. **Automation engine**: Create the workflow automation that handles form population, status tracking, renewal reminders, and compliance checking
3. **Web application**: FastAPI backend + clean frontend for managing registrations, viewing status, and configuring automation rules
4. **Monitoring & alerts**: Automated notifications for expiring registrations, status changes, or required actions

Tech stack: Python 3.11+, FastAPI (async), PostgreSQL, Redis caching, httpx for API calls, Playwright for any browser automation needs. Docker deployment.

I've built production scraping and automation systems with full test suites. My recent work includes a 3-workflow CRM automation system with 22 custom fields and 1,140+ automated tests. I prioritize reliability -- retry logic, error handling, and monitoring are built in from day one.

I can deliver an MVP within 2 weeks. What's the primary use case -- are you automating registrations for multiple entities, or building this as a SaaS product for others?

---

## GURU-3: Web Scraper Required
**Platform**: Guru
**URL**: https://www.guru.com/jobs/web-scraper-required/2116204
**Budget**: Fixed price (not specified)
**Posted**: 2 hours ago (FRESH!)
**Match score**: GREEN -- classic Python scraping project, quick win

### Proposal:

I can have this done fast -- scraping emails, phone numbers, and addresses from directories is straightforward Python work.

My approach:
1. Identify the target directories and their structure (HTML parsing vs. API vs. headless browser)
2. Build the async scraper using Python (httpx + BeautifulSoup for static sites, Playwright for JS-heavy ones)
3. Clean and deduplicate the data, output to CSV/Excel with structured columns
4. Include rate limiting and retry logic so you don't get blocked

I've built production data pipelines processing 50K+ rows with anomaly detection and full test suites. For scraping specifically, I use async Python for speed (hundreds of concurrent requests where appropriate) and handle edge cases like pagination, CAPTCHAs, and dynamic content.

Delivery: 1-2 days depending on the number of directories and their complexity. Clean, commented code with a README so you can run it yourself going forward. Fixed price, one revision included.

Two quick questions: How many directories do you need scraped, and roughly how many records are you expecting?

---

## GURU-4: Migrate Algo to Web App (Hotel Revenue Management)
**Platform**: Guru
**URL**: https://www.guru.com/jobs/migrate-algo-to-web-app/2116153
**Budget**: Fixed price (not specified)
**Posted**: Feb 18, 2026
**Match score**: GREEN -- Python algorithm migration, web app deployment, data processing

### Proposal:

Migrating a revenue management algorithm from Google Sheets to a proper web application is a project I can execute cleanly.

Here's my approach:
1. **Algorithm extraction**: Analyze your Google Sheets prototype, understand the calculation logic, and rewrite it in clean Python with proper data structures and error handling
2. **Web application**: Build a FastAPI backend with the algorithm as a service, plus a Streamlit or React frontend for the user interface -- dashboards, input forms, and reporting
3. **Data layer**: PostgreSQL for historical data storage, with proper schemas for hotel properties, rate data, occupancy metrics, and revenue calculations
4. **Deployment**: Docker containerization for easy deployment on any cloud platform (AWS, GCP, DigitalOcean, etc.)

I've built 5 live Streamlit demos and multiple FastAPI applications with production-grade APIs. My work includes data processing pipelines, Monte Carlo simulations for forecasting, and real-time dashboards. Everything comes with automated tests (8,500+ across my repos).

The key advantage of moving off Sheets: your algorithm can handle much larger datasets, run faster, support multiple users simultaneously, and integrate with external data sources (OTAs, PMS systems, etc.).

I can have a working MVP deployed within 2 weeks. What's the scale of your current Sheets model -- how many properties/room types, and what data sources feed into it?

---

## GURU-5: AI-Powered Text-to-Video YouTube Auto-Poster
**Platform**: Guru
**URL**: https://www.guru.com/jobs/ai-powered-text-to-video/2115805
**Budget**: Fixed price or hourly
**Posted**: Feb 7, 2026
**Match score**: GREEN -- n8n/Python automation, AI content pipeline, YouTube API

### Proposal:

An automated text-to-video pipeline with YouTube posting is a great automation project -- I can build this using Python and n8n.

Here's the architecture I'd propose:
1. **Content pipeline**: Text input -> AI-powered script generation (Claude/GPT) -> scene breakdown with visual descriptions
2. **Video generation**: Integrate with AI video tools (Runway, Pika, or open-source alternatives) for scene-by-scene generation, plus TTS for narration
3. **Assembly**: FFmpeg-based video assembly -- combine generated scenes, add narration audio, transitions, intro/outro, and subtitles
4. **YouTube automation**: YouTube Data API v3 integration for automated uploading with proper metadata (title, description, tags, thumbnails)
5. **Orchestration**: n8n workflow or Python scheduler for end-to-end automation -- trigger on schedule or on-demand

I've built production automation systems with Python and have experience with API integrations across multiple platforms (3 CRM integrations, webhook handling, async processing). My systems include monitoring, error handling, and retry logic -- critical for a pipeline with multiple external API dependencies.

I can deliver an MVP within 1-2 weeks. What's your target video length, and do you have a preferred AI video generation tool, or should I recommend one based on quality and cost?

---

## GURU-6: Leads Enrichment with AI
**Platform**: Guru
**URL**: https://www.guru.com/jobs/leads-enrichment-with-ai/2115414
**Budget**: Fixed price (not specified)
**Posted**: Jan 27, 2026
**Match score**: GREEN -- AI-powered lead enrichment, web scraping, data processing

### Proposal:

AI-powered lead enrichment is something I've built production systems for -- combining web scraping with LLM analysis to turn raw leads into qualified prospects.

My approach:
1. **Data ingestion**: Accept your lead list (CSV, API, or CRM export) with basic info (company name, URL, contact name)
2. **Web enrichment**: Automated scraping of company websites, LinkedIn, Crunchbase, and other public sources to gather firmographic and technographic data
3. **AI analysis**: Use Claude/GPT to analyze the scraped content and extract structured data -- company size, industry, tech stack, recent news, funding stage, decision-maker info
4. **Scoring**: AI-powered lead scoring based on your ideal customer profile (ICP) -- rank leads by fit and likely intent
5. **Output**: Enriched CSV or direct CRM integration with all new fields populated

I recently built a lead qualification system for a real estate client with AI-powered intent detection, temperature scoring, and automated CRM field updates (22 custom fields in GoHighLevel). The system uses 3-tier caching to keep LLM costs down -- 89% cost reduction with an 88% cache hit rate.

I can deliver within a week. What's your typical lead volume per batch, and what CRM do you use?

---

## GURU-7: Partner - Claude Code AI Debugging + n8n
**Platform**: Guru
**URL**: https://www.guru.com/jobs/partner-claude-code-ai-debugging-n8n/2115353
**Budget**: Fixed price (not specified)
**Posted**: Jan 25, 2026
**Match score**: GREEN -- this is literally my daily workflow (Claude Code + automation)

### Proposal:

I use Claude Code daily as my primary development environment -- it's my core workflow tool, not something I'm learning. I can help you debug and complete your projects efficiently.

My background with Claude Code + automation:
- I run Claude Code with 22 custom agents for specialized tasks (architecture, security, testing, deployment, etc.)
- I've built and deployed production systems entirely through Claude Code -- including a 3-bot AI platform with 1,140+ tests
- I use n8n-style automation workflows for CI/CD, data pipelines, and multi-step business processes
- 11 production Python repos, 8,500+ automated tests, all CI green

For your project, I can:
1. Debug and fix your existing Claude Code-generated applications
2. Optimize your n8n workflows for reliability and performance
3. Complete any partially-built no-code/low-code apps that need a developer's touch
4. Set up proper testing and deployment so your apps are production-ready

I'm available for ongoing partnership work. My rate is $65-75/hr, and I'm happy to start with a small debugging task so you can evaluate my work before committing to a larger engagement.

What specific applications or workflows are you looking to debug? A quick screen share or repo access would let me give you a targeted estimate.

---

*Generated: Feb 19, 2026 | Total: 15 proposals (8 PPH + 7 Guru)*
*All proposals are ready to paste after human reviews and personalizes bracketed sections.*
