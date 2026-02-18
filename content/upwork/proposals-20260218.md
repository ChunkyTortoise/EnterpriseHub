# Upwork Job Search & Draft Proposals — 2026-02-18

**Generated**: February 18, 2026
**Status**: DRAFT — Review before submitting
**Note**: Upwork MCP tools failed (AWS Secrets Manager credentials unavailable). Jobs sourced via web search of upwork.com listings.

---

## Search Summary

| Search Category | Keywords | Jobs Found |
|----------------|----------|------------|
| RAG / Vector DB | RAG, retrieval augmented generation, vector database | 8+ |
| LLM / AI Agents | LLM, AI agent, chatbot, Claude, GPT | 6+ |
| FastAPI / Backend | FastAPI, Python API, data pipeline | 5+ |
| GoHighLevel / CRM | GoHighLevel, GHL, CRM automation | 7+ |
| Streamlit / Dashboards | Streamlit, dashboard, data visualization | 4+ |

**Filtering criteria**: Skill match, budget >= $500 fixed or $50+/hr, recent posting, client quality.

**Already proposed** (excluded from this batch): Claude Code AI Agent Architect, Claude API/MCP for MSP, Full Stack Python + Claude Code, OpenClaw/Clawdbot jobs, Python LLM Workflow Developer, RAG Chatbot (Custom LLMs), Hybrid Graph RAG/LLM, Semantic RAG, Education RAG, RAG Debugging, Modular AI Platform, Support Chatbot.

---

## TOP 7 BEST-FIT JOBS

---

### Job 1: Education RAG Development Using Open Source Models

**URL**: https://www.upwork.com/freelance-jobs/apply/Education-RAG-Development-Using-Open-Source-Models_~021970373490520944132/
**Type**: Hourly + Fixed-Price Hybrid (MVP fixed, follow-ups hourly)
**Duration**: 3-6 weeks for MVP, 6+ months potential
**Hours**: 30+ hrs/week, Contract to Hire
**Match Score**: 9/10

#### Job Details
A client needs an education-focused RAG system using open-source models (Llama-3-8B/Qwen-2-7B via Ollama/llama.cpp). Key deliverables:
- Hybrid retrieval pipeline (BM25 + dense) with cross-encoder reranking
- Educational PDF/slide ingestion with page-aware chunking and metadata
- FastAPI endpoints: /ingest, /query, /feedback
- Citations (doc + page) and response guardrails (no hallucinations)
- Evaluation (ragas/TruLens) and telemetry
- Docker setup + documentation

**Required Skills**: Python (FastAPI), embeddings, vector search, BM25, cross-encoders, Qdrant/Weaviate/FAISS, sentence-transformers, LLM serving (Ollama/llama.cpp), PDF parsing (PyMuPDF), Docker, CI.

**Application Requirement**: 3 relevant RAG links (repos, demos) + brief note on role.

#### Why This Is a Top Match
- Direct overlap with EnterpriseHub's RAG system (advanced_rag_system/src/) and DocQA Engine
- BM25 + dense hybrid retrieval is exactly what DocQA uses
- FastAPI backend with Docker is our standard stack
- Cross-encoder reranking implemented in DocQA (Wave 5)
- Education domain is adjacent to document processing expertise

#### Recommended Bid
- **MVP Fixed**: $3,500-$4,500 (3-4 weeks)
- **Follow-up Hourly**: $75/hr

#### Draft Proposal (232 words)

Your hybrid retrieval approach (BM25 + dense with cross-encoder reranking) is the right architecture for education content -- dense embeddings alone miss keyword-exact matches on technical terms, while BM25 alone lacks semantic understanding. I've built this exact stack in production.

I'm a senior AI engineer with 20+ years of software experience and 11 production repositories. My most relevant projects:

**DocQA Engine** (https://chunkytortoise.github.io) -- Production RAG system with BM25 + semantic hybrid retrieval, cross-encoder reranking (Wave 5 feature), and multi-hop question answering. 500+ automated tests, Docker deployment, FastAPI backend. This is essentially the foundation for your education RAG.

**EnterpriseHub** -- Enterprise RAG system (advanced_rag_system/src/) with 3-tier Redis caching that achieved 89% LLM cost reduction and 88% cache hit rate. 5,100+ tests. Demonstrates the performance optimization your MVP-to-production path will need.

**AgentForge** -- Multi-agent orchestration framework. 4.3M tool dispatches/sec benchmark. Shows my systems engineering approach to AI infrastructure.

For your project, I'd deliver:
- **Week 1-2**: Ingestion pipeline (PyMuPDF + page-aware chunking), FAISS/Qdrant vector store, BM25 index
- **Week 3**: Hybrid retrieval + cross-encoder, Ollama/llama.cpp integration with tutor-mode prompts
- **Week 4**: FastAPI endpoints, evaluation (ragas), Docker, documentation

All code includes comprehensive tests (I maintain 8,500+ tests across my repos), CI/CD, and clean documentation.

Happy to walk through my DocQA codebase on a quick call -- it maps directly to your requirements.

---

### Job 2: AI Automation Engineer

**URL**: https://www.upwork.com/freelance-jobs/apply/Automation-Engineer_~022021459232049571238/
**Type**: Hourly
**Duration**: 6+ months, Contract to Hire
**Hours**: 30+ hrs/week
**Match Score**: 8/10

#### Job Details
An AI automation engineering role requiring:
- Hands-on experience with LLMs (APIs, prompt engineering, RAG, fine-tuning, agent frameworks)
- Building data pipelines and handling real-world data
- Experience with LLM orchestration (OpenAI, GPT-4/4o, LLaMA 3, Mistral, Mixtral)
- RAG systems (Pinecone, FAISS, Weaviate)
- AI Agents & Voice AI (CrewAI, AutoGen, Deepgram, Amazon Polly)

#### Why This Is a Top Match
- Direct match with EnterpriseHub's Claude orchestrator + multi-agent mesh
- RAG + agent framework experience is core competency
- Data pipeline experience from Insight Engine and Scrape-and-Serve
- Long-term contract to hire aligns with stable income goal

#### Recommended Bid
- **Hourly**: $70/hr

#### Draft Proposal (218 words)

Your AI automation role hits at the intersection of my deepest expertise -- LLM orchestration, RAG systems, and multi-agent architectures. I've been building production AI systems for the past year with measurable results.

My most relevant work:

**EnterpriseHub** (https://chunkytortoise.github.io) -- A production AI platform I built with Claude + Gemini orchestration, 3-tier Redis caching (89% cost reduction), and a multi-agent mesh coordinator with governance, routing, and auto-scaling. 5,100+ tests, FastAPI async backend, PostgreSQL + Redis. The orchestrator handles <200ms overhead at P99.

**AgentForge** -- Multi-agent framework with ReAct agent loops, tool dispatch (4.3M/sec benchmark), evaluation framework, and model registry. 550+ tests.

**DocQA Engine** -- Production RAG with BM25 + dense hybrid retrieval, cross-encoder reranking, and multi-hop QA. 500+ tests, Docker deployment.

What sets me apart from other AI engineers:
- **Production code, not prototypes** -- 8,500+ automated tests across 11 repos, all CI green
- **Cost-conscious engineering** -- Proven 89% LLM cost reduction via intelligent caching
- **Full delivery** -- Code + tests + docs + Docker + monitoring (P50/P95/P99 latency tracking)

I ship daily (check my GitHub commit history), communicate async, and over-document everything. I'm based in California (PST) and available 30+ hrs/week immediately.

Want to do a quick technical screen? I can walk through any of my production systems live.

---

### Job 3: Full-Time Expert in GoHighLevel (GHL) Implementation & AI CRM Integration

**URL**: https://www.upwork.com/freelance-jobs/apply/Full-Time-Expert-GoHighLevel-GHL-Implementation-CRM-Integration_~021883799660907938267/
**Type**: Hourly
**Duration**: 6+ months, Contract to Hire
**Hours**: 30+ hrs/week
**Match Score**: 9/10

#### Job Details
The Scaling Point is hiring a full-time GHL implementation specialist with AI CRM integration capabilities. The role involves:
- Full GoHighLevel implementation (pipelines, workflows, automation, reporting dashboards)
- AI-powered CRM integration
- Integration with third-party apps (payment processors, email marketing, scheduling)
- Client onboarding systems
- Cutting-edge SME solutions

#### Why This Is a Top Match
- EnterpriseHub is literally a GoHighLevel AI CRM integration platform
- 3 CRM integrations built (GoHighLevel, HubSpot, Salesforce)
- Jorge bot system with lead qualification, handoff, calendar booking -- all GHL-integrated
- Rate-limited GHL client (10 req/s), temperature tag publishing, pipeline management
- This is the rare job where domain expertise + technical skill intersect perfectly

#### Recommended Bid
- **Hourly**: $65-75/hr

#### Draft Proposal (241 words)

I've spent the past year building exactly what you're describing -- an AI-powered GoHighLevel CRM integration platform. This isn't hypothetical; it's running in production for a real estate operation in Rancho Cucamonga.

**EnterpriseHub** (https://chunkytortoise.github.io) is my production GHL AI platform:
- **3 AI chatbots** (Lead, Buyer, Seller) with autonomous lead qualification, financial readiness scoring, and property condition scoring -- all syncing to GHL in real-time
- **GHL integration**: Rate-limited API client (10 req/s), temperature tag publishing (Hot/Warm/Cold), pipeline management, calendar booking, custom field validation
- **Cross-bot handoff**: Intelligent routing between bots with confidence thresholds, circular prevention, rate limiting, and pattern learning
- **Response pipeline**: 5-stage post-processing (language mirroring, TCPA compliance, AI disclosure, SMS truncation)
- **5,100+ automated tests**, Docker deployment, PostgreSQL + Redis backend

I've also built CRM adapters for HubSpot and Salesforce using a unified protocol pattern, so I understand multi-CRM architecture deeply.

Technical highlights relevant to your role:
- **GHL API expertise**: Contacts, workflows, calendars, custom fields, tags, pipelines
- **AI orchestration**: Claude + Gemini with 3-tier caching (89% cost reduction)
- **Automation**: Webhook handlers, event-driven workflows, real-time sync
- **Dashboards**: Streamlit BI with Monte Carlo simulation, sentiment analysis, churn detection

I can start immediately at 30+ hrs/week. I'd love to show you the EnterpriseHub system -- it's the most relevant portfolio piece you'll see for this role.

---

### Job 4: GoHighLevel Technical Specialist (AI Voice Agents + API)

**URL**: https://www.upwork.com/freelance-jobs/apply/GoHighLevel-Technical-Specialist_~022013316808903811790/
**Type**: TBD (Not Sure on listing)
**Duration**: 6+ months
**Match Score**: 8/10

#### Job Details
A UK-based AI automation agency needs a highly experienced GoHighLevel technical specialist for:
- Advanced GHL setup and agency architecture
- Client onboarding systems
- AI voice agents
- API integrations
- Custom workflows

#### Why This Is a Top Match
- Direct GHL API experience from EnterpriseHub
- AI agent expertise (Jorge bots, AgentForge)
- API integration is a core competency (enhanced_ghl_client.py)
- Client onboarding aligns with the multi-tenant CRM experience

#### Recommended Bid
- **Hourly**: $70/hr (UK agency likely has higher budget)

#### Draft Proposal (224 words)

Your agency needs someone who can bridge the gap between GoHighLevel platform expertise and custom AI development -- that's exactly my niche.

I built **EnterpriseHub** (https://chunkytortoise.github.io), a production AI platform on top of GoHighLevel that goes well beyond standard GHL configuration:

**GHL Technical Depth**:
- Custom API client with 10 req/s rate limiting, retry logic, and webhook handlers
- Temperature tag publishing system (Hot/Warm/Cold leads auto-tagged from AI scoring)
- Pipeline automation with contact-level locking and conflict resolution
- Calendar booking integration for appointment-setting AI
- Custom field validation framework (validates all GHL fields before deployment)

**AI Agent Capabilities**:
- 3 production chatbots with intent decoding, handoff orchestration, and performance routing
- Multi-agent mesh coordinator with governance and auto-scaling
- 5-stage response pipeline (compliance, language mirroring, SMS formatting)
- AgentForge framework: 4.3M tool dispatches/sec, evaluation framework

**Agency-Ready Engineering**:
- Docker deployment ready for multi-client environments
- 8,500+ tests across 11 repos -- I don't ship untested code
- 33 Architecture Decision Records documenting technical tradeoffs
- P50/P95/P99 monitoring built into every service

For your AI voice agent work specifically, I've built real-time conversation systems with confidence scoring and handoff logic that would translate directly.

I'm available 30+ hrs/week and happy to do a technical walkthrough of the GHL integration code.

---

### Job 5: GTM Automation / Growth Engineer

**URL**: https://www.upwork.com/freelance-jobs/apply/GTM-Automation-Growth-Engineer_~022023214937103702529/
**Type**: Fixed Price — $4,000
**Posted**: February 15, 2026
**Duration**: Contract to Hire
**Match Score**: 8/10

#### Job Details
Building, connecting, and scaling omni-channel B2B lead generation systems using AI and automation. Starts part-time, expected to grow to full-time within 3-4 months.

#### Why This Is a Top Match
- Lead generation is core EnterpriseHub functionality
- AI-powered lead scoring and qualification built and tested
- CRM automation expertise (GHL, HubSpot, Salesforce adapters)
- $4,000 fixed price is good for initial engagement, with C2H upside
- Recently posted (Feb 15) = fresh opportunity

#### Recommended Bid
- **Fixed**: $4,000 (match their budget)

#### Draft Proposal (207 words)

B2B lead gen automation is where AI actually delivers measurable ROI -- I've seen this firsthand building lead qualification systems that process thousands of conversations.

I built **EnterpriseHub** (https://chunkytortoise.github.io), an AI-powered lead generation platform that automates the entire pipeline:

- **AI Lead Scoring**: Automated temperature classification (Hot/Warm/Cold) with confidence thresholds, driving different nurture sequences
- **Multi-Channel CRM**: GoHighLevel + HubSpot + Salesforce adapters with real-time sync, tag publishing, and pipeline automation
- **Intelligent Routing**: Performance-based lead routing with SLA monitoring (P95 < 120% threshold), auto-deferral when systems are slow
- **3 AI Chatbots**: Autonomous lead qualification, buyer financial readiness assessment, seller property evaluation -- all feeding into CRM pipelines

Results from production:
- **89% reduction** in AI processing costs via intelligent caching
- **<200ms** response overhead for lead scoring decisions
- **5,100+ automated tests** ensuring reliability at scale

For your GTM automation:
- **Week 1-2**: Audit existing systems, map omni-channel data flows, build integration layer
- **Week 3-4**: Deploy AI-powered lead scoring + routing, connect CRM pipelines
- **Ongoing**: Optimize conversion rates, add channels, scale automation

I ship daily, test everything, and over-document. Available to start immediately.

Shall we do a 15-minute call to map your current stack?

---

### Job 6: Backend Developer (FastAPI / Python) — HIPAA EHR Platform

**URL**: https://www.upwork.com/freelance-jobs/apply/Backend-Developer-FastAPI-Python_~021943779754275554901/
**Type**: Hourly
**Duration**: 1-3 months, Contract to Hire
**Hours**: 30+ hrs/week
**Match Score**: 7/10

#### Job Details
PraxtiveMD is hiring an experienced Python backend developer for a HIPAA-compliant EHR with AI charting, secure messaging, labs, and integrated billing. Required:
- Python 3.x + FastAPI
- PostgreSQL + SQLAlchemy (ORM)
- OAuth2 / JWT / token-based auth
- RESTful API design + OpenAPI
- API integration (HTTP, webhooks, auth)
- Background with HIPAA or secure health APIs
- Git, Docker, deployment (staging/prod split)

#### Why This Is a Top Match
- FastAPI + PostgreSQL + SQLAlchemy is the exact EnterpriseHub stack
- JWT/OAuth2 auth built and tested (security-focused development)
- API integration expertise (webhooks, HTTP, auth)
- Docker deployment standard
- Slightly lower match because healthcare domain is new, but tech stack is identical

#### Recommended Bid
- **Hourly**: $75/hr (HIPAA premium)

#### Draft Proposal (229 words)

Your FastAPI + PostgreSQL + SQLAlchemy stack is my daily driver -- I've built and maintain a production platform on this exact combination with 5,100+ tests proving it works at scale.

**EnterpriseHub** (https://chunkytortoise.github.io) is my production FastAPI platform:
- **FastAPI async backend** with Pydantic validation on all inputs, structured JSON error responses
- **PostgreSQL + SQLAlchemy + Alembic** migrations -- full ORM with typed models
- **JWT authentication** (1hr expiry) + OAuth2 flows + 100 req/min rate limiting
- **API integrations**: GoHighLevel webhooks, Stripe billing, multi-CRM adapters (HTTP, webhooks, auth)
- **Docker Compose** deployment with staging/prod configurations
- **Fernet encryption** for PII at rest, CCPA compliance patterns

While my domain is real estate AI rather than healthcare, the security patterns translate directly:
- **Data encryption**: PII encrypted at rest using Fernet (maps to PHI/ePHI requirements)
- **Access control**: JWT + role-based auth with configurable expiry
- **Audit trails**: Full logging with structured telemetry (P50/P95/P99)
- **Input validation**: Pydantic schemas on every endpoint boundary

My approach for PraxtiveMD:
- **Week 1**: Onboard, review architecture, understand HIPAA-specific requirements
- **Week 2-4**: Start contributing to API endpoints, integrations, auth flows
- **Ongoing**: Feature development, security hardening, test coverage expansion

I maintain 80%+ test coverage across all repos and ship with CI/CD on every commit. Happy to do a technical interview anytime.

---

### Job 7: Seeking Python Developer with FastAPI & API Integration for Smart Assistant

**URL**: https://www.upwork.com/freelance-jobs/apply/Seeking-Python-Developer-with-FastAPI-API-Integration-Experience-for-Smart-Assistant-Project_~021925996567252296092/
**Type**: Hourly/Fixed (TBD)
**Match Score**: 8/10

#### Job Details
Building a Smart Assistant project requiring:
- Python + FastAPI development
- API integration experience
- Smart assistant / AI assistant capabilities

#### Why This Is a Top Match
- FastAPI + AI assistant is exactly EnterpriseHub's core (Claude orchestrator + Jorge bots)
- API integration is a core strength
- Smart assistant with context management, memory, and orchestration is proven expertise

#### Recommended Bid
- **Hourly**: $70/hr

#### Draft Proposal (215 words)

Building a smart assistant that actually works in production requires more than LLM API calls -- it needs robust orchestration, context management, and graceful failure handling. That's what I specialize in.

**EnterpriseHub** (https://chunkytortoise.github.io) is my production smart assistant platform:
- **Claude Orchestrator**: Multi-strategy response parsing with L1/L2/L3 Redis caching (<200ms overhead, P99: 0.095ms)
- **3 AI Assistants**: Lead qualification bot, buyer advisor, seller evaluator -- each with intent decoding, context management, and conversation memory
- **Agent Mesh**: Multi-agent coordination with governance, routing, auto-scaling, and audit trails
- **Response Pipeline**: 5-stage post-processing ensuring compliance, formatting, and quality

Key metrics from production:
- **89% LLM cost reduction** via intelligent 3-tier caching
- **88% cache hit rate** across conversation patterns
- **<200ms orchestration overhead** even with multi-model routing
- **5,100+ tests** ensuring reliability

Additional relevant projects:
- **AgentForge**: Multi-agent framework, 4.3M tool dispatches/sec, evaluation framework (550+ tests)
- **DocQA Engine**: RAG-powered document Q&A with hybrid retrieval (500+ tests)

My approach:
- Start with a thorough requirements session to understand your assistant's domain
- Build with TDD -- failing test first, then implementation
- Ship incrementally with Docker + CI/CD from day one

Would love to understand your smart assistant's use case -- quick call to scope it out?

---

## Connects Budget Estimate

| Job | Est. Connects | Priority |
|-----|--------------|----------|
| #1 Education RAG (Open Source) | 6-12 | HIGH |
| #2 AI Automation Engineer | 8-16 | HIGH |
| #3 GHL Full-Time Implementation | 6-12 | HIGHEST |
| #4 GHL Technical Specialist | 6-12 | HIGH |
| #5 GTM Automation Engineer | 8-16 | HIGH |
| #6 FastAPI Backend (HIPAA) | 6-12 | MEDIUM |
| #7 FastAPI Smart Assistant | 6-12 | MEDIUM |
| **TOTAL** | **~46-92** | — |

**Action Required**: Buy connects before submitting. Currently at 2 connects remaining per pipeline file.

---

## Submission Priority Order

1. **Job #3** (GHL Full-Time) -- Highest domain match, long-term C2H
2. **Job #1** (Education RAG) -- Direct RAG expertise, solid fixed-price MVP
3. **Job #5** (GTM Automation) -- $4,000 fixed, recently posted, good C2H pipeline
4. **Job #2** (AI Automation Engineer) -- Long-term, high volume
5. **Job #4** (GHL Technical Specialist) -- UK agency, likely good budget
6. **Job #7** (FastAPI Smart Assistant) -- Good match, depends on details
7. **Job #6** (FastAPI HIPAA) -- Strong tech match, healthcare domain is new

---

## MCP Tool Failure Log

**Tool**: `mcp__upwork__upwork_search_jobs_by_keywords`, `mcp__upwork__upwork_get_latest_jobs`
**Error**: `MCP error -32603: Failed to get tokens from AWS Secrets Manager: Could not load credentials from any providers`
**Root Cause**: AWS credentials not configured in the current shell environment. The Upwork MCP server stores OAuth tokens in AWS Secrets Manager (secret: `upwork-oauth-tokens`) and requires valid AWS credentials to retrieve them.
**Resolution**: Configure `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, and `AWS_DEFAULT_REGION` environment variables, or ensure the AWS CLI is authenticated via `aws configure` or IAM role.

**Workaround used**: Web search of upwork.com to find current job listings manually. Job details extracted from search snippets (Upwork blocks direct page scraping with 403).
