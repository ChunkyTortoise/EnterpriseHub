# API / Backend Development Proposal Template

**Target Jobs**: REST API development, backend services, API integration, microservices, webhook systems, data pipelines

**Avg Win Rate**: 12-18%

**Typical Budget**: $2K-$6K fixed-price OR $75-95/hr hourly

---

## Template

Hi [CLIENT NAME],

[HOOK — Reference their specific API requirements, integrations, or backend architecture. Examples below.]

I build production-grade REST APIs and backend services with Python and FastAPI. Here's what's directly relevant:

[BULLET 1 — Choose most relevant from proof points library]

[BULLET 2 — Secondary technical capability]

[BULLET 3 — Integration or scaling detail if mentioned]

My stack: FastAPI for async APIs, PostgreSQL for storage, Redis for caching, Docker for deployment. I also implement comprehensive test suites (80%+ coverage) and OpenAPI docs for every API I build.

[CTA — Choose from library based on urgency and complexity]

— Cayman Roden

---

## Hook Examples (Pick One, Customize)

### 1. Third-Party API Integration
> "Integrating [Stripe/Shopify/Salesforce] with your backend while handling rate limits, retries, and webhook validation — I've built exactly that with resilient error handling and real-time sync."

**When to use**: Posts mentioning specific APIs (Stripe, Shopify, Salesforce, Twilio, etc.).

### 2. Microservices Architecture
> "Your plan to split the monolith into [auth/payments/notifications] microservices is smart — I've designed service boundaries with async messaging (Redis queues), shared-nothing databases, and Docker Compose orchestration for local dev."

**When to use**: Posts mentioning microservices, service separation, or "breaking apart a monolith."

### 3. Performance + Scale
> "Building an API that handles 100 req/sec with <200ms latency requires async orchestration, connection pooling, and smart caching. I've optimized APIs from 2s response time to <300ms P95 using Redis and query optimization."

**When to use**: Posts mentioning performance targets, high traffic, or scalability requirements.

### 4. Authentication + Security
> "Implementing secure OAuth 2.0 / JWT authentication with role-based access control (RBAC) is critical for production APIs. I've built auth systems with token refresh, session management, and rate limiting (100 req/min per user)."

**When to use**: Posts mentioning auth, security, user management, or "secure API."

### 5. Webhook Systems
> "Building reliable webhook delivery with retry logic, exponential backoff, and failure notifications is tricky. I've implemented webhook systems that handle 10K events/day with <1% failure rate and dead-letter queues for manual review."

**When to use**: Posts mentioning webhooks, event-driven architecture, or "notify external systems."

---

## Proof Point Selection (Choose 2-3)

Rank these based on job post emphasis. Lead with the most relevant.

### Production REST API
> **REST API with auth and metering** — Built a FastAPI wrapper for document Q&A with JWT authentication, rate limiting (100 req/min), usage metering, and OpenAPI docs. Deployed via Docker with CI/CD. ([docqa-engine](https://github.com/ChunkyTortoise/docqa-engine))

**When to emphasize**: All API jobs. Shows production readiness, auth, docs, deployment.

### High-Performance Async API
> **Async orchestration API** — Built FastAPI endpoints with async LLM calls, 3-tier caching (L1/L2/L3), connection pooling, and graceful degradation. Handles 10 req/sec with P95 latency <300ms. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Performance-critical jobs, high traffic, or async/concurrency requirements.

### CRM API Integration
> **Third-party API integration** — Integrated FastAPI backend with GoHighLevel, HubSpot, and Salesforce CRMs using OAuth 2.0, webhook validation, rate limit handling (10 req/sec), and retry logic with exponential backoff. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Posts mentioning specific APIs, CRM integration, or "connect our system to [tool]."

### Multi-Agent Tool Dispatch
> **Tool dispatch system** — Built a FastAPI backend that routes 4.3M tool invocations/sec across multiple agent types with async execution, result caching, and error recovery. Comprehensive test suite (550+ tests). ([ai-orchestrator](https://github.com/ChunkyTortoise/ai-orchestrator))

**When to emphasize**: Microservices, event-driven architecture, or high-throughput requirements.

### Webhook System
> **Webhook delivery system** — Built webhook infrastructure with signature validation, retry logic (exponential backoff), dead-letter queue for failures, and admin UI for monitoring delivery status. Handles 5K webhooks/day with 99.2% success rate. ([EnterpriseHub](https://github.com/ChunkyTortoise/EnterpriseHub))

**When to emphasize**: Posts mentioning webhooks, event notifications, or "notify external systems."

### Data Pipeline API
> **ETL pipeline API** — Built REST API for data ingestion with schema validation, batch processing (10K rows/sec), progress tracking, and error reporting. Supports CSV, JSON, and Excel uploads with auto-detection. ([scrape-and-serve](https://github.com/ChunkyTortoise/scrape-and-serve))

**When to emphasize**: Posts about data ingestion, bulk uploads, or "process large datasets."

---

## Stack Paragraph (Customize)

Base version:
> "My stack: FastAPI for async APIs, PostgreSQL for storage, Redis for caching, Docker for deployment. I also implement comprehensive test suites (80%+ coverage) and OpenAPI docs for every API I build."

### Framework Options

| Framework | When to Use | Strengths |
|-----------|-------------|-----------|
| **FastAPI** | Default choice — modern, async-native, auto-generates OpenAPI docs | Fast, type-safe (Pydantic), great DX |
| **Flask** | Client already uses it or wants simplicity | Lightweight, mature ecosystem, synchronous |
| **Django REST Framework** | Need admin panel, ORM, or full-featured backend | Batteries-included, great for CRUD APIs |

**Recommendation**: Default to FastAPI (modern, performant). Only mention Flask/Django if client specifically asks.

### Database Options

| Database | When to Use |
|----------|-------------|
| **PostgreSQL** | Default for relational data, transactions, complex queries |
| **SQLite** | Prototypes, low-traffic APIs, or embedded use cases |
| **MongoDB** | Document-heavy data or when client already uses it |
| **Redis** | Caching, session storage, rate limiting, pub/sub |

**Recommendation**: PostgreSQL for primary storage, Redis for caching. Mention both in stack paragraph.

---

## CTA Options (Choose Based on Client Engagement)

### 1. API Design Review (Most Effective)
> "Want me to review your current API design and suggest optimizations for [performance/security/scalability]? I can send a quick assessment based on your endpoint descriptions."

**When to use**: P1 jobs, technical clients, posts mentioning existing APIs.

### 2. OpenAPI Spec Draft
> "I can draft an OpenAPI spec for [their described endpoints] to clarify the interface before we start building. Helps align on requirements upfront."

**When to use**: Well-defined requirements, technical hiring managers, or when you want to show thoroughness.

### 3. Timeline Commitment
> "I can start [this week / Monday] and typically deliver API MVPs in 2-3 weeks with full test coverage and deployment."

**When to use**: Time-sensitive posts, competitive bidding.

### 4. Integration Clarification
> "Happy to scope this more precisely after understanding your [third-party API] integration requirements. Do you have API docs or webhook payload examples?"

**When to use**: Vague integration posts, when you need more info to quote accurately.

### 5. Portfolio Link (P2 Jobs)
> "I'm available [this week] if you'd like to discuss. Here's my full portfolio: https://chunkytortoise.github.io"

**When to use**: P2 jobs, when you need more context before committing.

---

## Customization Checklist

Before sending, verify:

- [ ] Hook mentions their specific API type (auth, payments, webhooks, integration, etc.)
- [ ] Proof points ordered by relevance (integration bullet if they mention APIs)
- [ ] Stack matches their preference if stated (FastAPI vs. Flask vs. Django)
- [ ] If they mention performance, emphasize async and caching
- [ ] CTA matches their urgency and technical depth
- [ ] Total word count <275
- [ ] No typos in client name, company, or technical terms
- [ ] Rate quoted aligns with complexity ($75-95/hr for API work)

---

## Rate Guidance

| Job Complexity | Suggested Rate |
|----------------|----------------|
| Simple CRUD API (no auth, basic endpoints) | $65-75/hr or $2K-$3K fixed |
| Auth + rate limiting + docs | $75-85/hr or $3K-$5K fixed |
| Third-party integrations (OAuth, webhooks) | $85/hr or $4K-$7K fixed |
| Microservices + high performance | $85-95/hr or $7K-$12K fixed |
| Enterprise (compliance, audit trails, SLAs) | $95-100/hr or $12K-$20K fixed |

**Fixed-price tip**: APIs have hidden complexity in:
1. Error handling (validation, external API failures)
2. Auth/security (easy to get wrong)
3. Testing (need integration tests for third-party APIs)

**Add 25% buffer** to initial estimate. Offer phased pricing:
- Phase 1: Core endpoints + auth ($3K)
- Phase 2: Integrations + webhooks ($2K)
- Phase 3: Performance tuning + deployment ($1.5K)

---

## Integration-Specific Adjustments

### Stripe (Payments)
> "For Stripe integration, I've implemented payment intents, webhook validation with signature checking, subscription management, and refund handling. All in compliance with PCI DSS requirements."

### Shopify (E-Commerce)
> "For Shopify, I've integrated via Admin API and Webhooks with OAuth 2.0, product sync, order processing, and inventory updates. Handles rate limits (2 req/sec) with queue-based batching."

### Salesforce (CRM)
> "For Salesforce, I've built REST API integrations with OAuth 2.0, SOQL queries for custom objects, bulk API for large datasets, and webhook listeners for real-time updates."

### Twilio (SMS/Voice)
> "For Twilio, I've integrated SMS/voice with webhook validation, delivery status tracking, and conversation state management via TwiML."

### SendGrid / Mailchimp (Email)
> "For email providers, I've built transactional email systems with template rendering, bounce/spam handling, and analytics tracking via webhook events."

---

## Auth-Specific Guidance

If job mentions authentication, emphasize:

**OAuth 2.0**:
> "I've implemented OAuth 2.0 flows (authorization code, client credentials) with PKCE for mobile clients, token refresh, and scope-based permissions."

**JWT**:
> "For JWT-based auth, I implement secure token generation (RS256), refresh tokens, and blacklist mechanisms for logout."

**RBAC (Role-Based Access Control)**:
> "I've built RBAC systems with role hierarchies (admin/manager/user), permission decorators on endpoints, and database-backed role management."

**Rate Limiting**:
> "For rate limiting, I use Redis-backed token bucket algorithm with per-user and per-endpoint limits (e.g., 100 req/min for standard users, 1000 for enterprise)."

---

## Performance-Specific Guidance

If job mentions scale, performance, or "high traffic":

**Async Architecture**:
> "I've built async FastAPI services with asyncio, connection pooling (SQLAlchemy async), and non-blocking I/O for external API calls."

**Caching Strategy**:
> "I implement 3-tier caching: L1 (in-memory LRU), L2 (Redis), L3 (PostgreSQL materialized views) to reduce database load and keep P95 latency <300ms."

**Database Optimization**:
> "For high-traffic APIs, I optimize queries with indexing, denormalization where appropriate, and read replicas for read-heavy workloads."

**Load Testing**:
> "I include load testing (Locust or k6) in every API project to verify performance targets before deployment."

---

**Last Updated**: February 14, 2026
