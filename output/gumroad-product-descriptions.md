# Gumroad Product Descriptions -- Revenue Sprint

---

## Product 1: DocQA Engine -- Production RAG Pipeline

**Title**: DocQA Engine: Production RAG with Hybrid Search
**Tagline**: Ship an enterprise-grade document Q&A system with hybrid retrieval, re-ranking, and evaluation -- not a tutorial, a working pipeline.
**Price**: $49 (Starter) / $149 (Pro) / $497 (Enterprise)

### Description (paste into Gumroad)

Stop building toy RAG demos that fall apart with real documents. DocQA Engine is a production-ready retrieval-augmented generation pipeline that combines dense embeddings, BM25 sparse search, and cross-encoder re-ranking to deliver answers your users can trust -- with citations.

Built and tested across 844 automated tests, this is the same architecture behind systems handling enterprise knowledge bases, multi-modal search, and research workflows.

**What you get:**
- Complete hybrid retrieval pipeline (dense + sparse + RRF fusion + cross-encoder re-ranking)
- FastAPI gateway with health checks, ingestion, and query endpoints
- Multi-modal support for text, images, and structured data
- Evaluation framework with automated faithfulness detection and benchmarking
- Three-tier caching (L1/L2/L3) targeting 95%+ cache hit rate
- OpenTelemetry observability with Prometheus metrics and Grafana dashboards
- Full test suite (844 tests) and Makefile for zero-friction development

**Results you can expect:**
- P95 retrieval latency under 200ms with hybrid BM25 + vector search
- 89% citation accuracy out of the box
- 50% token reduction via contextual compression (HyDE, self-querying, parent document retrieval)

**Who this is for:**
- AI engineers building document search or knowledge base products
- Teams replacing basic vector-only RAG with production-grade hybrid retrieval
- Developers preparing portfolio projects that demonstrate real engineering depth

**FAQ:**
Q: What LLM providers are supported?
A: OpenAI out of the box, with optional Cohere re-ranking and spaCy NLP. The architecture is provider-agnostic.

Q: Do I need Docker to run this?
A: No. You can run locally with `pip install -e ".[dev]"` and `make run`. Docker is optional for Redis and observability services.

---

## Product 2: AgentForge -- Multi-Agent LLM Framework

**Title**: AgentForge: DAG-First Multi-Agent Orchestration
**Tagline**: Build multi-agent LLM apps with one dependency, DAG workflows, and MCP-native tool integration -- production-tested with 683 tests.
**Price**: $49 (Starter) / $149 (Pro) / $497 (Enterprise)

### Description (paste into Gumroad)

Most agent frameworks bury you in dependencies and lock you into one LLM provider. AgentForge ships with exactly one required dependency (Pydantic v2), supports 100+ LLM providers via LiteLLM, and gives you DAG-first workflow orchestration that actually scales.

This is the framework behind a 4.3M dispatches/sec production system. Every pattern is tested across 683 automated tests.

**What you get:**
- Complete multi-agent framework with DAG workflow engine (topological sort, cycle detection, retry logic)
- MCP-native integration -- consume and expose agents as Model Context Protocol tools
- Four memory backends: WorkingMemory, SessionMemory, FileMemory, CheckpointStore
- Inter-agent communication: MessageBus, pub/sub, request-response, delegation patterns
- YAML pipeline definitions with hot-reload capability
- Plugin architecture via Python entry points with pre/post execution hooks
- OpenTelemetry observability with ASCII terminal dashboard
- Async-first throughout with concurrent node execution

**Results you can expect:**
- 4.3M dispatches/sec throughput (multi-agent, Redis-backed)
- P99 latency of 0.095ms for dispatch operations
- Support for 100+ LLM providers (Claude, OpenAI, Gemini, Ollama) via optional LiteLLM

**Who this is for:**
- Developers building multi-step AI workflows (research, content, analysis pipelines)
- Teams that need agent orchestration without the dependency bloat of LangChain or CrewAI
- Engineers who want MCP-native tool integration from day one

**FAQ:**
Q: How does this compare to LangChain or CrewAI?
A: AgentForge has 1 core dependency vs many. It is DAG-first (not chain-first), MCP-native (not bolted on), and async throughout. See the comparison table in the README.

Q: Can I use this with my existing OpenAI/Claude setup?
A: Yes. Install `agentforge[llm]` for LiteLLM support and point it at any provider. Or use the base install and bring your own client.

---

## Product 3: RAG-as-a-Service -- Multi-Tenant RAG Platform

**Title**: RAG-as-a-Service: Multi-Tenant Document Q&A SaaS
**Tagline**: Launch a document Q&A SaaS with tenant isolation, Stripe billing, and PII detection -- the backend for your next AI product.
**Price**: $79 (Starter) / $199 (Pro) / $597 (Enterprise)

### Description (paste into Gumroad)

You have the RAG pipeline. Now you need to sell it. RAG-as-a-Service is a complete multi-tenant backend that turns document Q&A into a billable SaaS product -- with tenant isolation, metered Stripe billing, PII compliance, and audit logging built in from day one.

Every tenant gets their own PostgreSQL schema, their own API key, and their own usage meter. You deploy once and onboard customers with a single API call. Tested across 196 automated tests with 90%+ coverage.

**What you get:**
- Multi-tenant architecture with schema-per-tenant PostgreSQL isolation (no cross-tenant data leakage)
- Hybrid search engine: pgvector cosine similarity + BM25 full-text with Reciprocal Rank Fusion
- Query expansion via HyDE and multi-query techniques
- Stripe metered billing with three pricing tiers (Starter/Pro/Business) and webhook handling
- PII detection and redaction for email, phone, SSN, credit card, and IP addresses
- Immutable audit logging for compliance requirements
- JWT authentication, rate limiting, and Redis-cached tenant routing
- FastAPI async backend with streaming query support
- Alembic migrations and Docker deployment ready

**Results you can expect:**
- P95 query latency under 500ms including LLM generation
- Vector search in ~10ms for 1M chunks
- 1,000+ queries/sec throughput with caching enabled
- Three billing tiers from $29/mo to $499/mo with per-query metering

**Who this is for:**
- Developers who want to launch a document Q&A SaaS product without building billing and multi-tenancy from scratch
- Agencies building white-label AI search for multiple clients
- Teams that need PII compliance and audit trails for regulated industries

**FAQ:**
Q: Can I use this with a provider other than OpenAI?
A: Yes. The embedding and LLM layers accept any compatible API key. Swap the provider by changing environment variables.

Q: How does tenant isolation work?
A: Each tenant gets a dedicated PostgreSQL schema (`tenant_<slug>`) with isolated tables for documents, chunks, collections, and query logs. API keys route to schemas via Redis cache. No shared tables, no cross-tenant queries.
