# Production AI Systems: Complete Syllabus

6-week curriculum. 2 sessions per week (90 min each). 1 lab per week.

## Course Prerequisites

- Python proficiency (2+ years)
- Familiarity with REST APIs and HTTP
- Basic SQL knowledge
- Git/GitHub comfort
- A web browser (all labs run in Codespaces)

## Schedule Overview

| Week | Topic | Repo | Lab Deliverable |
|------|-------|------|-----------------|
| 1 | Agent Architecture | AgentForge | Multi-tool agent with structured output |
| 2 | RAG Systems | DocQA-Insight | Hybrid search pipeline with evaluation |
| 3 | MCP + Tool Integration | MCP Server Toolkit | 2 custom MCP servers |
| 4 | Production Orchestration | EnterpriseHub | Caching + rate limiting + CRM integration |
| 5 | Observability + Testing | Insight Engine | Instrumented system with 50+ tests |
| 6 | Deployment + Operations | Student Project | Deployed product with CI/CD + Stripe |

## Session Format

**Session A (Tuesdays, 6:00 PM PT)**
| Time | Activity |
|------|----------|
| 0:00-0:15 | Concept introduction with architecture diagrams |
| 0:15-1:00 | Live coding walkthrough using actual repo code |
| 1:00-1:15 | Lab assignment introduction and setup verification |
| 1:15-1:30 | Q&A |

**Session B (Thursdays, 6:00 PM PT)**
| Time | Activity |
|------|----------|
| 0:00-0:20 | Lab solution review (common patterns and mistakes) |
| 0:20-1:00 | Advanced topic deep-dive |
| 1:00-1:20 | Guest speaker or production case study |
| 1:20-1:30 | Next week preview |

## Grading

| Component | Weight | Requirement |
|-----------|--------|-------------|
| Lab completion | 60% | Submit 5 of 6 labs (passing autograder) |
| Final project | 30% | Deploy a working product in Week 6 |
| Participation | 10% | Discord engagement, peer reviews |

**Certificate**: Awarded upon completing 5/6 labs + final project deployment.

---

## Week 1: Agent Architecture (AgentForge)

**Learning Objectives:**
- Understand multi-agent system architecture patterns
- Implement tool registration with typed schemas
- Build structured output parsing with fallback strategies
- Configure pluggable memory backends

**Session A: Concept + Live Coding**
- Agent architectures: ReAct, function calling, multi-agent routing
- Tool registry pattern: schema definition, validation, execution
- Live coding: Build a 3-tool agent from scratch
- Demo: AgentForge's dependency injection system

**Session B: Lab Review + Deep Dive**
- Review Lab 1 submissions (common issues)
- Deep dive: Memory systems (in-memory, Redis, PostgreSQL backends)
- Advanced: Structured output parsing — JSON extraction, regex fallback, re-prompting
- Preview: Week 2 RAG concepts

**Readings:**
- AgentForge README and architecture docs
- "Building Reliable AI Agents" (course materials)
- OpenAI Function Calling documentation

**Lab:** Build a multi-agent customer service bot with 3 tools and structured output
**Deliverable:** Passing autograder tests + working demo in Codespace

---

## Week 2: RAG Systems (DocQA)

**Learning Objectives:**
- Design a document ingestion pipeline with chunking strategies
- Implement hybrid search combining BM25 and vector similarity
- Build retrieval evaluation metrics (precision, recall, MRR)
- Optimize chunk size and overlap for different document types

**Session A: Concept + Live Coding**
- RAG architecture: ingest → chunk → embed → index → retrieve → generate
- Chunking strategies: fixed-size, semantic, recursive
- Embedding models: trade-offs between speed, quality, and cost
- Live coding: Build a document ingestion pipeline

**Session B: Lab Review + Deep Dive**
- Review Lab 2 submissions
- Deep dive: Hybrid search (BM25 keyword + vector semantic, score fusion)
- Advanced: Evaluation frameworks — how to measure retrieval quality
- Preview: Week 3 MCP protocol

**Readings:**
- DocQA-Insight README and architecture docs
- "Retrieval-Augmented Generation" (course materials)
- pgvector documentation

**Lab:** Build a document Q&A system with hybrid search and evaluation metrics
**Deliverable:** Passing autograder tests + retrieval evaluation report

---

## Week 3: MCP + Tool Integration (MCP Server Toolkit)

**Learning Objectives:**
- Understand the Model Context Protocol specification
- Build MCP servers that expose tools to AI agents
- Implement authentication and error handling in MCP servers
- Connect agents to external services via MCP

**Session A: Concept + Live Coding**
- MCP protocol: server, client, transport, tool definitions
- Server framework: decorators, schema validation, error handling
- Live coding: Build an MCP server for database queries
- Demo: Connecting Claude Desktop to custom MCP servers

**Session B: Lab Review + Deep Dive**
- Review Lab 3 submissions
- Deep dive: Authentication patterns for MCP servers
- Advanced: Rate limiting and error propagation across MCP boundaries
- Preview: Week 4 production patterns

**Readings:**
- MCP specification (modelcontextprotocol.io)
- MCP Server Toolkit README
- "Building MCP Servers" (course materials)

**Lab:** Build 2 custom MCP servers (database query + web scraping)
**Deliverable:** Passing autograder tests + both servers runnable via MCP client

---

## Week 4: Production Orchestration (EnterpriseHub)

**Learning Objectives:**
- Implement L1/L2/L3 caching for LLM calls
- Build rate-aware API clients with backoff and queuing
- Design multi-strategy output parsing with fallback chains
- Integrate with external CRM systems (GoHighLevel)

**Session A: Concept + Live Coding**
- Production patterns: caching, rate limiting, circuit breakers, retries
- L1 (in-memory) / L2 (Redis) / L3 (PostgreSQL) caching architecture
- Live coding: Add caching to an AI orchestrator
- Demo: Measuring cache hit rates and cost reduction

**Session B: Lab Review + Deep Dive**
- Review Lab 4 submissions
- Deep dive: CRM integration patterns — webhook handling, field mapping, rate limits
- Advanced: Multi-strategy parsing (JSON → regex → key-value → re-prompt)
- Production case study: EnterpriseHub managing $50M+ pipeline

**Readings:**
- EnterpriseHub CLAUDE.md (architecture overview)
- `services/claude_orchestrator.py` (source code walkthrough)
- "Production Caching for AI" (course materials)

**Lab:** Add caching, rate limiting, and error handling to an AI orchestration platform
**Deliverable:** Passing autograder tests + cache hit rate > 70% on test workload

---

## Week 5: Observability + Testing (Insight Engine)

**Learning Objectives:**
- Instrument AI systems with structured logging and metrics
- Build latency histograms and P50/P95/P99 tracking
- Implement anomaly detection for business metrics
- Write comprehensive tests for non-deterministic AI systems

**Session A: Concept + Live Coding**
- Observability pillars: logs, metrics, traces
- Structured logging for AI: request IDs, token counts, cache status
- Live coding: Build a Streamlit monitoring dashboard
- Demo: Real-time latency and cost tracking

**Session B: Lab Review + Deep Dive**
- Review Lab 5 submissions
- Deep dive: Testing AI systems — behavior tests, scoring tests, integration tests
- Advanced: Anomaly detection algorithms for KPI monitoring
- Preview: Week 6 deployment

**Readings:**
- Insight Engine README and dashboard architecture
- `services/jorge/performance_tracker.py` (source code walkthrough)
- "Testing Non-Deterministic Systems" (course materials)

**Lab:** Instrument an AI system with monitoring and build a Streamlit dashboard. Write 50+ tests.
**Deliverable:** Passing autograder tests + working dashboard + test coverage report

---

## Week 6: Deployment + Operations (Student Project)

**Learning Objectives:**
- Containerize an AI application with Docker
- Set up CI/CD with GitHub Actions and quality gates
- Configure health checks, monitoring, and alerting
- Integrate Stripe for subscription billing

**Session A: Concept + Live Coding**
- Docker: multi-stage builds, compose, health checks
- CI/CD: GitHub Actions workflows, quality gates, automated testing
- Live coding: Dockerize and deploy a complete AI application
- Demo: Stripe integration for SaaS billing

**Session B: Lab Review + Final Presentations**
- Review Lab 6 submissions
- Student final project presentations (5 min each)
- Course retrospective and feedback
- Next steps: portfolio, job search, freelancing, Cohort alumni community

**Readings:**
- Docker best practices for Python applications
- GitHub Actions documentation
- Stripe API documentation (Checkout Sessions, Subscriptions)

**Lab:** Deploy your own AI project with Docker, CI/CD, monitoring, and Stripe billing
**Deliverable:** Live deployed URL + passing CI/CD pipeline + Stripe test checkout working

---

## Post-Course Resources

- Alumni Discord channel (lifetime access)
- All session recordings (lifetime access)
- Lab repositories (forever accessible via GitHub)
- Certificate of completion (Certifier, LinkedIn-verifiable)
- Instructor office hours (quarterly for alumni)
