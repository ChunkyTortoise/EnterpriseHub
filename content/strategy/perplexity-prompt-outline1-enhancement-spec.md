# Perplexity Deep Research Prompt — Outline 1: Portfolio Enhancement Spec

**Purpose**: Generate a comprehensive, agent-executable technical specification for enhancing 7 existing Gumroad products + EnterpriseHub platform. The output must be detailed enough that a team of AI coding agents can execute tasks in parallel without human clarification.

---

## PROMPT (copy everything below this line)

```
I need you to research and synthesize a COMPREHENSIVE TECHNICAL SPECIFICATION for
enhancing 8 existing Python AI/ML products. This spec will be executed by a swarm of
AI coding agents working in parallel — so every task must be self-contained with
exact file structures, API signatures, dependency versions, and acceptance criteria.

## CONTEXT: MY EXISTING TECH STACK

All products are Python 3.11+, use pytest for testing (8,500+ tests total), have
Docker + GitHub Actions CI, and follow these conventions:
- FastAPI for APIs (async)
- Pydantic v2 for schemas
- SQLAlchemy for ORM
- Redis for caching (3-tier: L1 in-memory, L2 Redis, L3 persistent)
- Claude/GPT/Gemini for AI reasoning
- Streamlit for dashboards
- snake_case files/functions, PascalCase classes, SCREAMING_SNAKE_CASE constants

## THE 8 PRODUCTS TO ENHANCE

### 1. AgentForge Multi-LLM Orchestrator (ai-orchestrator repo)
Current: Multi-agent coordination framework, 4.3M dispatches/sec, ReAct loops,
model registry, guardrails. ~550 tests.

**Enhancements needed (in priority order):**

A) **LangGraph + CrewAI Native Connectors** (P0, 40 hrs)
   - LangGraph adapter for stateful cyclic workflow integration
   - CrewAI adapter for role-based multi-agent setups
   - Must not replace existing orchestration — adapters that wrap external frameworks

B) **MCP Server Integration** (P1, 60 hrs)
   - Expose AgentForge as an MCP server (tools, resources, prompts)
   - Consume external MCP servers from within agent workflows
   - MCP discovery/registry for dynamic tool loading

C) **Human-in-the-Loop Gates** (P2, 30 hrs)
   - Structured approval workflows for high-stakes agent decisions
   - Configurable approval rules (always, threshold-based, never)

D) **Agentic RAG Module** (P2, 35 hrs)
   - Multi-knowledge-base queries with source routing
   - Self-correction loop (detect low-confidence answers, retry with refined query)
   - Answer validation against source documents

E) **Agent Evaluation Framework** (P2, 20 hrs)
   - Success rate, cost, latency metrics per agent
   - Benchmark comparison between agent configurations

### 2. DocQA Engine (docqa-engine repo)
Current: RAG pipeline with cross-encoder re-ranking, multi-hop QA, query expansion,
89% LLM cost reduction via 3-tier Redis caching. ~500 tests.

**Enhancements needed:**

A) **Haystack + LlamaIndex Adapters** (P1, 35 hrs)
   - Integration adapters that wrap DocQA core for Haystack pipeline compatibility
   - LlamaIndex node/retriever adapters

B) **RAG Evaluation Toolkit** (P1, 25 hrs)
   - RAGAS-style metrics: retrieval precision, answer faithfulness, cost-per-query
   - Benchmark comparison mode (your pipeline vs baseline)

C) **Multi-Modal Document Processing** (P2, 50 hrs)
   - PDF table extraction to structured output
   - Image/chart understanding via vision models (Claude 3.5, GPT-4V)
   - Mixed-media document processing pipeline

D) **SaaS Wrapper** (P2, 80 hrs)
   - Hosted DocQA API with API key auth and metered access
   - Web upload interface + team management
   - Usage-based billing via Stripe

### 3. Insight Engine (insight-engine repo)
Current: Anomaly detection, KPI frameworks, SHAP explanations, statistical testing,
forecasting. ~640 tests.

**Enhancements needed:**

A) **AI Narrative Generation** (P1, 20 hrs)
   - Auto-generate plain-English insight summaries from anomaly detection results
   - Template-based with LLM refinement

B) **LLM Root Cause Analysis** (P1, 10 hrs)
   - Explain WHY KPIs moved using correlated data + LLM reasoning
   - Structured output: cause, evidence, confidence, recommended action

C) **AI Dashboard Components** (P2, 15 hrs)
   - LLM chat widget for Streamlit dashboards
   - RAG search widget (natural language data queries)
   - Agent monitoring component

### 4. Scrape-and-Serve (scrape-and-serve repo)
Current: Web scraping framework with data pipelines, content intelligence,
data quality monitoring. ~370 tests.

**Enhancements needed:**

A) **MCP Server Output Mode** (P1, 15 hrs)
   - Scraped data exposed as MCP resources for AI agent consumption
   - Structured extraction with schema definitions

B) **LLM Post-Processing** (P1, 10 hrs)
   - LLM-powered structured data extraction from raw HTML
   - Schema-driven extraction (user defines output schema, LLM extracts)

C) **Scheduled Scraping + Webhooks** (P2, 20 hrs)
   - Cron-based scheduling with diff detection
   - Webhook notifications on data changes

### 5. AI Integration Starter Kit (llm-integration-starter repo)
Current: Observability, batch processing, fallback/retry patterns. ~250 tests.

**Enhancement needed:**

A) **Rebrand to "AI Agent Starter Kit"** (P1, 20 hrs)
   - Pre-built agent templates: customer support, data analysis, content generation
   - MCP server boilerplate
   - LangGraph starter patterns
   - Update all references, README, package name

### 6. Prompt Engineering Toolkit (prompt-engineering-lab repo)
Current: Versioning, safety checking, template management. ~220 tests.

**Enhancement needed:**

A) **Prompt Evaluation/Scoring** (P0 decision, 15 hrs for implementation)
   - Benchmark datasets for prompt quality scoring
   - A/B comparison of prompt variants with statistical significance
   - NOTE: May be bundled into AgentForge instead — spec both options

### 7. Streamlit Dashboard Templates (insight-engine repo, templates module)
Current: BI components, Monte Carlo, sentiment analysis. Part of Insight Engine.

**Enhancement needed:**

A) **AI-Powered Components** (P2, 15 hrs)
   - LLM chat interface component
   - RAG search widget component
   - Agent observability panel component

### 8. EnterpriseHub Platform (EnterpriseHub repo)
Current: Real estate AI platform — FastAPI, PostgreSQL, Redis, 3 AI chatbots (lead,
buyer, seller), GoHighLevel CRM, Stripe, A/B testing, handoff orchestration. ~5,100 tests.

**Enhancements needed:**

A) **Voice AI Integration** (P2, 80 hrs)
   - Deepgram STT + ElevenLabs TTS integration with existing chatbots
   - Voice-enabled lead qualification (24/7)
   - Voice for buyer + seller bots

B) **MCP Server for GoHighLevel** (P2, 40 hrs)
   - Expose GHL CRM integration as MCP server
   - Enable external AI agents to query/update real estate CRM data

C) **Autonomous SDR Agent** (P3, 60 hrs)
   - AI agent for outbound lead generation + automated follow-up
   - Integration with existing lead scoring + GHL workflows

## WHAT I NEED YOU TO RESEARCH AND PRODUCE

For EACH enhancement above, produce a detailed technical spec containing:

### 1. Architecture & Design
- **Component diagram** showing how the enhancement integrates with existing code
- **Data flow** from input to output, including all intermediate transformations
- **Interface contracts**: exact Python class/function signatures with type hints
- **Database schema changes** (if any): exact SQLAlchemy model definitions
- **Configuration schema**: Pydantic models for any new config
- **Dependencies**: exact PyPI packages with version pins (research latest stable
  versions as of Feb 2026)

### 2. File Structure
- **Exact file paths** for every new file to create (following existing repo conventions)
- **Existing files to modify** with description of changes
- **Test file paths** and what each test file covers

### 3. API Specifications
- **REST endpoints** (if applicable): method, path, request/response schemas
- **Python API**: public class/method signatures with docstrings
- **MCP tool definitions** (if applicable): name, description, input schema

### 4. Implementation Details
For each component, provide:
- **Algorithm/approach**: specific libraries, patterns, techniques to use
- **Error handling**: what can fail and how to handle it
- **Performance targets**: latency, throughput, memory bounds
- **Security considerations**: input validation, auth, data handling

### 5. Testing Strategy
- **Unit tests**: what to test, expected assertions, mock boundaries
- **Integration tests**: end-to-end scenarios
- **Benchmark tests**: performance validation
- **Minimum test count** per enhancement (maintain 80%+ coverage)

### 6. Parallel Execution Plan
This is CRITICAL. Structure the spec so that:
- **Independent tasks** are clearly marked (can run in parallel)
- **Dependencies** are explicit (task X must complete before task Y)
- **Shared interfaces** are defined upfront (so parallel agents don't conflict)
- Group tasks into **3-4 parallel workstreams** that can execute simultaneously

### 7. Integration Points & Shared Code
Research and specify:
- **LangGraph** (latest stable version, Feb 2026): exact adapter pattern for
  integrating external orchestrators. How does StateGraph work? What's the node
  and edge API? How to wrap an existing orchestrator as a LangGraph node?
- **CrewAI** (latest stable version, Feb 2026): exact adapter pattern. How do
  Agents, Tasks, and Crews work? How to delegate to an external orchestrator?
- **MCP Protocol** (latest spec, Feb 2026): exact server implementation pattern
  in Python. What's the current SDK? How to define tools, resources, prompts?
  How to implement a client that discovers and calls MCP servers?
- **Haystack** (latest stable version): pipeline API, component interface, how
  to wrap a custom retriever as a Haystack component
- **LlamaIndex** (latest stable version): node parser API, retriever interface,
  how to wrap a custom RAG pipeline as a LlamaIndex retriever
- **RAGAS** (latest stable version): evaluation metrics API, how to integrate
  with a custom RAG pipeline
- **Deepgram** Python SDK: STT streaming API, event handling, configuration
- **ElevenLabs** Python SDK: TTS streaming API, voice cloning, WebSocket interface

### 8. Acceptance Criteria
For each enhancement:
- **Definition of done**: specific, testable conditions
- **Regression checks**: what existing functionality must NOT break
- **Performance baselines**: metrics that must be maintained or improved

## OUTPUT FORMAT

Structure your response as a spec document with clear sections per product,
numbered sub-tasks, and explicit parallel/sequential markers. Use tables for
API signatures, dependency lists, and file structures. Include code snippets
for critical interface definitions.

The goal: an AI coding agent should be able to read ONE section of this spec
and implement it completely without needing to ask questions or reference other
sections (except for shared interface definitions, which should be in a
dedicated "Shared Contracts" section at the top).
```
