# Enterprise Hub Walkthrough -- Video Script

**Duration**: 6:30
**Format**: Screen recording + talking head (optional)
**Purpose**: Product demo for Gumroad, LinkedIn, cold outreach links

---

## 0:00-0:30 -- Hook + Introduction

**[SCREEN: Terminal with test suite running, green checkmarks scrolling]**

"Most AI repositories on GitHub have zero tests. This one has 8,500. I am Cayman Roden, a senior AI automation engineer, and I am going to walk you through the 5 production AI products I built that can save your team 2-4 months of infrastructure work."

**[SCREEN: Split view -- all 5 product READMEs side by side]**

"Voice AI agents, DevOps monitoring, multi-tenant RAG, MCP servers, and shared SaaS infrastructure. All tested, all Docker-ready, all documented. Let me show you what they actually do."

---

## 0:30-1:30 -- Voice AI Platform (60 seconds)

**[SCREEN: voice-ai-platform README with architecture diagram]**

"First, the Voice AI Platform. This is a real-time voice agent system built on Twilio, Deepgram for speech-to-text, ElevenLabs for text-to-speech, and Claude for the conversation intelligence."

**[SCREEN: Architecture diagram -- Twilio -> WebSocket -> Pipecat -> STT/LLM/TTS]**

"The architecture uses Pipecat for pipeline orchestration. A phone call comes in via Twilio, streams audio over WebSocket, Deepgram transcribes in real-time, Claude generates the response, and ElevenLabs speaks it back. Sub-second latency."

**[SCREEN: Code -- multi-bot configuration, lead/buyer/seller]**

"It ships with three bot personalities -- Lead qualification, Buyer assistance, and Seller consultation. Multi-tenant, with GHL CRM sync and Stripe billing built in."

**[SCREEN: pytest output -- 66 tests passing]**

"66 automated tests. Not demo code."

---

## 1:30-2:30 -- RAG-as-a-Service (60 seconds)

**[SCREEN: rag-as-a-service README]**

"Product two: multi-tenant RAG with pgvector. This is the infrastructure SaaS companies need to add document Q&A to their product."

**[SCREEN: Code -- hybrid search: pgvector + BM25 + RRF fusion]**

"What makes this different from tutorial RAG: hybrid search combining pgvector cosine similarity with BM25 full-text search, fused with Reciprocal Rank Fusion. Query expansion with HyDE. PII detection and redaction. Stripe metered billing per query."

**[SCREEN: Architecture diagram -- tenant isolation]**

"Each tenant gets a separate PostgreSQL schema. No data leakage. This is the pattern you need for B2B SaaS."

**[SCREEN: Benchmark results]**

"We achieved 89% LLM cost reduction in production with 3-tier caching. 120 tests, 90%+ coverage."

---

## 2:30-3:30 -- AI DevOps Suite (60 seconds)

**[SCREEN: ai-devops-suite README]**

"Product three: AI DevOps. Three capabilities in one platform."

**[SCREEN: Monitoring dashboard -- Streamlit with P50/P95/P99 charts]**

"Agent monitoring with P50/P95/P99 latency metrics and anomaly detection. I run this on my own agent fleet."

**[SCREEN: Prompt registry code -- versioning, A/B testing]**

"A prompt registry with git-like versioning and A/B testing using z-test statistical significance. No more 'which prompt version is in production?' confusion."

**[SCREEN: Data pipeline configuration -- APScheduler + scraping]**

"And a data pipeline with scheduled scraping, LLM extraction, and DAG-based orchestration. 123 tests."

---

## 3:30-4:30 -- MCP Server Toolkit (60 seconds)

**[SCREEN: PyPI page for mcp-server-toolkit]**

"Product four: the MCP Server Toolkit. This one is live on PyPI -- pip install mcp-server-toolkit."

**[SCREEN: Code -- EnhancedMCP class with decorators]**

"The EnhancedMCP base class gives you caching, rate limiting, and telemetry as decorators. Three lines to add a cached tool. Three lines to add rate limiting."

**[SCREEN: Code -- MCPTestClient usage]**

"It includes an MCPTestClient for unit testing your tools, and three pre-built servers: database queries with SQL validation, web scraping with LLM extraction, and file processing with RAG chunking."

**[SCREEN: pytest output -- 190 tests passing]**

"190 tests. The most thoroughly tested MCP framework available."

---

## 4:30-5:15 -- Shared Schemas + Integration (45 seconds)

**[SCREEN: shared-schemas README]**

"Product five: Shared Schemas. This is the glue. Pydantic v2 models for tenants, auth, billing, and domain events. FastAPI middleware for JWT auth, Redis rate limiting, Stripe billing, and health checks."

**[SCREEN: Code showing shared imports across products]**

"All five products use these schemas. When you buy the bundle, everything integrates cleanly because they share the same types and middleware."

**[SCREEN: GitHub Actions CI -- all green]**

"Reusable CI templates are included too. 69 tests in this package alone."

---

## 5:15-6:00 -- The Numbers (45 seconds)

**[SCREEN: Metrics summary slide/terminal output]**

"Let me give you the full picture."

"568 automated tests across these 5 products. 8,500+ tests across my full portfolio of 11 repos. 89% LLM cost reduction. 4.3 million tool dispatches per second. P99 orchestration overhead under one-tenth of a millisecond."

**[SCREEN: Docker compose up -- all services starting]**

"Every product ships with Docker Compose. Clone, configure environment variables, docker compose up, done."

**[SCREEN: GitHub profile -- all repos with green CI badges]**

"Every repo has GitHub Actions CI, architecture decision records, benchmark suites, and Mermaid architecture diagrams. This is how production software is built."

---

## 6:00-6:30 -- CTA

**[SCREEN: Gumroad product page / bundle page]**

"You can buy each product individually or get the full Enterprise AI Toolkit bundle starting at $499. That gives you all 5 products, 568 tests, and Docker deployment for everything."

"If you want me to build something custom -- RAG systems, voice agents, CRM integrations, multi-agent workflows -- I am available at $150 to $250 per hour."

"Links are in the description. If you have questions, drop a comment or DM me on LinkedIn."

**[SCREEN: Contact info -- LinkedIn, GitHub, email]**

"I am Cayman Roden. Thanks for watching."

---

## Production Notes

- **Screen recording tool**: OBS Studio or ScreenFlow
- **Resolution**: 1920x1080, 30fps minimum
- **Audio**: External mic, not laptop mic
- **Pacing**: Each section is timed -- practice transitions
- **B-roll**: Terminal output, code scrolling, test suites running
- **Thumbnail**: "568 Tests. 5 Products. $499." with terminal screenshot background
- **Upload to**: YouTube (unlisted or public), embed on Gumroad + LinkedIn
