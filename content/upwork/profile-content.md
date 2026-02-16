# Upwork Profile Content

---

## Professional Title Options

1. **Senior AI Automation Engineer | RAG, Multi-Agent Systems, GoHighLevel**
2. **AI Platform Engineer | Voice AI, RAG-as-a-Service, Production Python**
3. **Full-Stack AI Engineer | FastAPI, Multi-Tenant SaaS, LLM Integration**

Recommended: Option 1 (covers the three highest-value keywords for incoming searches).

---

## Overview / Bio (490 words)

I build production AI systems — not prototypes, not demos, production code with automated tests, CI/CD pipelines, and real deployment history.

My portfolio includes 11 repositories with 8,500+ automated tests, 33 Architecture Decision Records, and benchmark suites with P50/P95/P99 latency metrics in every project. The flagship system manages a $50M+ real estate pipeline in Southern California with three AI chatbots, real-time CRM sync, and an 89% reduction in LLM costs through a 3-tier Redis caching layer.

What I specialize in:

**RAG Systems & Knowledge Bases**
Multi-tenant retrieval-augmented generation with pgvector, schema-per-tenant isolation, query expansion, hybrid search, PII detection, and Stripe billing. I've built RAG platforms where each client's data is physically separated in PostgreSQL — not just filtered by tenant_id, but isolated at the schema level. 120 tests verify the isolation.

**Voice AI Agents**
Real-time voice pipelines using Twilio + Deepgram STT + ElevenLabs TTS with sub-second latency. The system handles inbound/outbound calls, qualifies leads, books appointments, and syncs to GoHighLevel. Barge-in support means callers can interrupt the bot mid-sentence — it actually listens, unlike most voice bots.

**Multi-Agent Orchestration**
Agent coordination with governance, routing, auto-scaling, and audit trails. I've built handoff systems with circular prevention, rate limiting, pattern learning from outcomes, and performance-based routing. The core engine handles 4.3M tool dispatches per second.

**GoHighLevel Integration**
Native GHL integration across CRM sync, workflow triggers, temperature tagging, calendar booking, and custom field mapping. I've also built an MCP server specifically for GHL so AI assistants like Claude can interact with GHL contacts, pipelines, and fields directly.

**AI DevOps & Monitoring**
Prompt registries with git-like versioning and A/B testing, agent monitoring with percentile-based alerting, anomaly detection, and data pipeline orchestration. If you're running AI in production, you need observability — I build the infrastructure for it.

My tech stack: Python 3.11+, FastAPI (async), SQLAlchemy, PostgreSQL, Redis, Docker, GitHub Actions, Pydantic v2, Stripe, Claude API, GPT-4, Deepgram, ElevenLabs, Twilio, Streamlit.

I work remote-only from California. Communication is async-first with daily commits, over-documented PRs, and structured handoff notes. Every project gets tests, CI, Docker, and documentation as standard — not as add-ons.

Rates start at $150/hour for advisory and architecture work, $65-75/hour for implementation contracts. Project-based pricing available for defined scopes.

---

## Portfolio Case Studies

### Case Study 1: Real-Time Voice AI for Real Estate Lead Qualification

Built a production voice AI system for a Southern California real estate brokerage managing a $50M+ pipeline. The system handles inbound calls via Twilio, transcribes in real-time with Deepgram, generates responses through Claude, and speaks via ElevenLabs — all with sub-second latency and barge-in support. Three specialized bots (Lead, Buyer, Seller) route conversations based on intent detection with 0.7 confidence threshold. All data syncs to GoHighLevel: contact fields, temperature tags (Hot/Warm/Cold), and calendar bookings. 66 automated tests, CI/CD pipeline, Docker deployment. Lead response time dropped from 4+ hours to under 30 seconds.

### Case Study 2: Multi-Tenant RAG Platform with PII Compliance

Designed and built a multi-tenant RAG-as-a-Service platform where each tenant gets schema-isolated storage in PostgreSQL with pgvector. The system supports hybrid search (semantic + keyword), query expansion via multi-query strategy, reranking, and streaming responses. PII detection scans documents before embedding — SSN, credit cards, phone numbers are redacted automatically. Stripe billing integration enables usage-based pricing per tenant. Tier-based rate limiting (Free: 10 RPM to Enterprise: 1,000 RPM) enforced at middleware level. 120 automated tests verify tenant isolation under concurrent load.

### Case Study 3: AI Agent Monitoring & Prompt Operations Platform

Built a unified observability platform for teams running AI agents in production. Tracks P50/P95/P99 latency per agent and per model with rolling windows. Includes a git-like prompt registry where teams version prompts, tag them for environments (production/staging/canary), and run A/B tests with statistical significance via z-test. One client found a 23% conversion improvement by testing two system prompt variants. Anomaly detection flags degradations before users notice. 109 automated tests, Streamlit dashboard, configurable alerting with cooldown periods.

---

## Skills List with Proficiency

### Expert Level
- Python (3.11+)
- FastAPI / Async Python
- RAG Systems (pgvector, BM25, semantic search)
- Multi-Agent Systems / LLM Orchestration
- Prompt Engineering & Optimization
- Test-Driven Development (pytest, 8,500+ tests)
- Pydantic v2 / Data Validation
- Claude API / Anthropic SDK
- GoHighLevel CRM Integration

### Advanced Level
- PostgreSQL / SQLAlchemy / Alembic
- Redis (caching, pub/sub, rate limiting)
- Docker / Docker Compose
- GitHub Actions CI/CD
- Stripe Integration (billing, subscriptions, metering)
- Twilio / Voice AI (STT/TTS pipelines)
- Streamlit Dashboards
- OpenAI GPT-4 API
- Web Scraping (BeautifulSoup, Playwright)
- Security (JWT, Fernet encryption, PII detection, CCPA)

### Proficient Level
- Deepgram SDK (STT)
- ElevenLabs SDK (TTS)
- scikit-learn / pandas
- MCP (Model Context Protocol)
- Kubernetes basics
- Terraform basics

---

## Service Offerings with Rates

### Advisory & Architecture ($150-$300/hr)

- AI system architecture review and design
- RAG pipeline evaluation and optimization
- Multi-agent system design and governance
- LLM cost optimization audit
- GoHighLevel automation strategy

### Implementation ($65-$75/hr)

- Custom RAG system development
- Voice AI agent development
- GoHighLevel integration and automation
- AI monitoring and observability setup
- Prompt engineering and A/B testing infrastructure
- Multi-tenant SaaS backend development

### Project-Based Pricing

| Project Type | Range | Typical Timeline |
|-------------|------:|:----------------:|
| RAG system (single-tenant) | $1,500 - $4,000 | 2-3 weeks |
| RAG system (multi-tenant) | $4,000 - $8,000 | 4-6 weeks |
| Voice AI agent | $3,000 - $8,000 | 3-5 weeks |
| GHL automation suite | $1,500 - $4,000 | 2-3 weeks |
| AI monitoring setup | $2,000 - $5,000 | 2-4 weeks |
| MCP server (custom) | $800 - $2,000 | 1-2 weeks |
| Full platform (enterprise) | $8,000 - $12,000/phase | 6-8 weeks/phase |

### Retainer Options

| Tier | Monthly | Includes |
|------|--------:|----------|
| Starter | $2,500 | 40 hrs implementation, async support |
| Growth | $5,000 | 80 hrs, architecture reviews, priority |
| Enterprise | $8,000 | 120 hrs, dedicated availability, on-call |

---

## Profile Settings

- **Hourly Rate**: $150/hr (display rate for advisory; negotiate per-project)
- **Availability**: 30+ hrs/week
- **Response Time**: Within 4 hours during business hours (PST)
- **Languages**: English (native)
- **Location**: Palm Springs, CA (Remote only)
