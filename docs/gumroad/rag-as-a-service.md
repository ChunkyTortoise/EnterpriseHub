# RAG-as-a-Service

## Headline

**Multi-Tenant RAG Platform -- pgvector + Hybrid Search + Stripe Billing**

Deploy a production RAG system with tenant isolation, hybrid search (semantic + BM25), PII redaction, and metered billing -- ready to serve your customers.

---

## Value Proposition

Building multi-tenant RAG is hard. Tenant isolation, hybrid retrieval, billing metering, PII compliance -- most teams spend months on infrastructure before they write a single query handler. This platform ships all of it with 120 tests and 90%+ coverage.

Used in production to achieve 89% LLM cost reduction via 3-tier caching.

---

## Features

- **Multi-tenant architecture**: PostgreSQL schema-per-tenant isolation
- **Hybrid search**: pgvector cosine similarity + BM25 full-text with RRF fusion
- **Query expansion**: HyDE (Hypothetical Document Embeddings) + multi-query
- **PII detection & redaction**: Regex-based with optional Presidio integration
- **Stripe metered billing**: Per-query usage tracking with 3 pricing tiers
- **Audit logging**: Immutable audit trail for compliance (SOC2, HIPAA prep)
- **Redis caching**: Tenant routing cache + query result cache
- **Async architecture**: FastAPI + async/await for high throughput
- **Document processing**: PDF, CSV, TXT ingestion with chunking strategies

---

## Technical Specs

| Spec | Detail |
|------|--------|
| Language | Python 3.11+ |
| Framework | FastAPI (async) + SQLAlchemy |
| Vector DB | PostgreSQL 15+ with pgvector |
| Search | Hybrid: cosine similarity + BM25 + RRF |
| Query Expansion | HyDE, multi-query |
| PII | Regex + optional Presidio |
| Billing | Stripe metered subscriptions |
| Cache | Redis 7+ |
| Tests | 120 automated tests, 90%+ coverage |
| Deployment | Docker + docker-compose |
| CI/CD | GitHub Actions |

---

## What You Get

### Starter -- $199

- Full source code (RAG engine, tenant manager, billing, API)
- README + architecture documentation
- Docker deployment files
- 120 passing tests
- .env.example with all config vars
- Community support (GitHub Issues)

### Pro -- $349

Everything in Starter, plus:

- **Production deployment guide** (PostgreSQL + pgvector + Redis setup)
- **Tenant onboarding playbook** (API key provisioning, schema creation)
- **Embedding model comparison guide** (OpenAI vs Cohere vs local)
- **Cost optimization guide** (caching strategies that achieved 89% reduction)
- **1-hour setup call** via Zoom
- Priority email support (48hr response)

### Enterprise -- $699

Everything in Pro, plus:

- **Custom tenant configuration** for your specific use case
- **Stripe billing integration** with your pricing model
- **PII compliance review** for your industry (healthcare, finance, legal)
- **Performance tuning** (index optimization, query routing)
- **Architecture review** of your RAG deployment
- **30-day dedicated support** via Slack channel
- **SLA**: 24hr response, 72hr bug fix

---

## Who This Is For

- **SaaS companies** adding document Q&A to their product
- **AI agencies** deploying RAG for enterprise clients
- **Legal/healthcare/finance** teams with compliance requirements
- **Developers** who need multi-tenant RAG without building from scratch

---

## Architecture

```
Client --> API Gateway --> Tenant Router --> RAG Engine
                              |                |
                          Redis Cache     pgvector + BM25
                              |                |
                        Multi-tenant DB   Document Store
```

---

## FAQ

**Q: Can I use this with OpenAI, Cohere, or local embeddings?**
A: Yes. The embedding layer is provider-agnostic. Swap with a config change.

**Q: How does tenant isolation work?**
A: Each tenant gets a separate PostgreSQL schema. No data leakage between tenants.

**Q: What about scale?**
A: pgvector handles millions of vectors. Add read replicas for horizontal scaling.

---

## Proof

- 120 automated tests, 90%+ coverage
- Hybrid search (semantic + BM25) with RRF fusion -- not just vector similarity
- 89% LLM cost reduction achieved in production via 3-tier caching
- Part of an 8,500+ test portfolio across 11 production repos
