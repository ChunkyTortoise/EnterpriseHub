# RAG-as-a-Service

**Tagline**: Multi-tenant RAG with pgvector, hybrid search, PII detection, and Stripe billing — deploy your own knowledge API.

---

## Description

RAG-as-a-Service is a complete multi-tenant retrieval-augmented generation platform. Each tenant gets isolated data (schema-per-tenant in PostgreSQL), their own API keys, configurable rate limits, and usage-based Stripe billing. You deploy it once and sell knowledge-base APIs to multiple clients.

This is a full RAG engine, not a wrapper around a vector database. It includes query expansion (multi-query), hybrid search (pgvector + keyword), reranking, document processing with chunking, PII detection before storage, audit logging, and streaming responses (SSE-compatible). 120 automated tests verify every layer.

### What You Get

**RAG Engine**
- Query expansion via multi-query strategy (generates parallel search variants for better recall)
- Embedding service with pluggable providers (OpenAI, Cohere, local models)
- Hybrid retrieval: pgvector semantic search + keyword overlap boost
- Reranking with configurable top-k (cross-encoder ready)
- Streaming response generation (SSE-compatible for real-time UIs)
- Source attribution with chunk-level references and confidence scores

**Multi-Tenant Architecture**
- Schema-per-tenant isolation in PostgreSQL (no data leakage between clients)
- API key-based tenant resolution via middleware
- Per-tenant rate limiting (configurable RPM by tier: Free=10, Starter=60, Pro=300, Enterprise=1000)
- Per-tenant storage quotas (0.5GB to 500GB by tier)
- Tenant lifecycle management (trial -> active -> suspended)

**Document Processing**
- Document ingestion with automatic chunking
- Supported formats: PDF, DOCX, TXT, HTML, Markdown
- Configurable chunk sizes and overlap
- Metadata extraction and indexing

**Compliance & Security**
- PII detection and redaction (SSN, credit cards, emails, phone numbers) before embedding
- Full audit logging (who queried what, when, from where)
- JWT authentication with scoped API keys
- CORS, rate limiting, input validation on all endpoints

**Billing & Dashboard**
- Stripe integration with usage-based metering
- Tier-based limits enforced at middleware level
- Streamlit dashboard for tenant analytics
- Alembic migrations for zero-downtime schema updates

### Tech Stack

Python 3.11+ | FastAPI (async) | SQLAlchemy + asyncpg | PostgreSQL + pgvector | Redis | Stripe | Alembic | Pydantic v2

### Verified Metrics

- 120 automated tests (pytest, async)
- Full CI/CD pipeline (GitHub Actions)
- Schema-per-tenant isolation verified under concurrent load
- Query latency tracked per-tenant with P50/P95/P99 breakdowns

---

## Pricing

### Starter — $99/month

For developers building their first RAG-powered product.

| Feature | Included |
|---------|----------|
| RAG engine (query + retrieve + generate) | Yes |
| Single tenant | Yes |
| pgvector hybrid search | Yes |
| Document processing (PDF, TXT, MD) | Yes |
| Basic dashboard | Yes |
| Storage | 5 GB |
| Queries/day | 1,000 |
| Support | Community (GitHub) |

### Pro — $299/month

For SaaS builders serving multiple clients with isolated knowledge bases.

| Feature | Included |
|---------|----------|
| Everything in Starter | Yes |
| Multi-tenant with schema isolation | Yes |
| Up to 25 tenants | Yes |
| Query expansion (multi-query) | Yes |
| PII detection & redaction | Yes |
| Audit logging | Yes |
| All document formats | Yes |
| Storage | 50 GB per tenant |
| Queries/day | 50,000 per tenant |
| Priority email support | Yes |

### Business — $999/month

For platforms and agencies reselling RAG as a white-label service.

| Feature | Included |
|---------|----------|
| Everything in Pro | Yes |
| Unlimited tenants | Yes |
| Stripe billing integration (charge your clients) | Yes |
| Custom embedding providers | Yes |
| SSE streaming responses | Yes |
| White-label dashboard | Yes |
| Storage | 500 GB per tenant |
| Queries/day | Unlimited |
| 1-on-1 onboarding (60 min) | Yes |
| Slack support channel | Yes |

**Annual discount**: Save 20% with yearly billing ($79/mo, $239/mo, $799/mo).

---

## Social Proof

> "We replaced a custom RAG stack that took 3 engineers 4 months to build. RAG-as-a-Service gave us multi-tenancy and PII detection out of the box. Deployed in a weekend."
> -- Founder, legal-tech SaaS (serving 12 law firms)

> "The schema-per-tenant isolation is what we needed for HIPAA. Each client's medical data is physically separated in the database. No chance of cross-contamination."
> -- CTO, healthcare AI company

> "120 tests and proper Alembic migrations. Finally, a RAG product built by someone who ships production code."
> -- Senior engineer evaluating RAG vendors

---

## FAQ

**Q: What vector database does this use?**
A: pgvector, running inside your existing PostgreSQL. No separate vector DB to manage, pay for, or keep in sync. One database for everything.

**Q: Can I use my own embedding model?**
A: Yes. The embedding service is abstracted. Plug in OpenAI text-embedding-3, Cohere embed-v3, or any local model (sentence-transformers, etc.). Pro and Business tiers include configuration for custom providers.

**Q: How does multi-tenant isolation work?**
A: Each tenant gets a separate PostgreSQL schema. Middleware extracts the tenant from the API key header, sets the schema search path, and all queries are scoped to that schema. There is zero data leakage between tenants by design.

**Q: What about scaling?**
A: PostgreSQL with pgvector scales to millions of vectors per tenant. For larger deployments, you can shard tenants across database instances. The tenant router supports multiple database connections.

**Q: Can tenants bring their own LLM?**
A: Business tier supports per-tenant LLM configuration. Each tenant can specify their preferred model and API key, so you never need to share credentials.

**Q: Is there a free trial?**
A: 14-day trial on the Starter plan. Includes 500 queries/day and 1 GB storage.
