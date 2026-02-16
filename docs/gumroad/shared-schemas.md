# Shared Schemas

## Headline

**Pydantic v2 SaaS Schemas + FastAPI Middleware + Stripe Billing + Redis Rate Limiter**

Production-ready shared infrastructure for multi-tenant AI applications. 69 tests.

---

## Value Proposition

Every multi-tenant SaaS needs the same boilerplate: tenant models, auth middleware, billing integration, rate limiting, health checks. This package gives you battle-tested Pydantic v2 schemas and FastAPI middleware so you stop rewriting infrastructure and start shipping features.

Extracted from a platform managing $50M+ in real estate pipeline.

---

## Features

### shared_schemas (Pydantic v2 Models)
- **Tenant models**: Multi-tenant isolation with org hierarchy
- **Auth schemas**: JWT token models, API key validation, RBAC roles
- **Billing models**: Stripe subscription, usage metering, invoice schemas
- **Domain events**: Event sourcing base types with serialization
- **Config models**: Environment-aware settings with validation

### shared_infra (FastAPI Middleware)
- **Auth middleware**: JWT validation + API key authentication
- **Rate limiter**: Redis-backed sliding window rate limiting
- **Stripe billing**: Subscription management + webhook handling
- **Health checks**: Liveness + readiness probes with dependency checks
- **Error handling**: Structured error responses with correlation IDs

### ci_templates (GitHub Actions)
- **Reusable workflows**: Test, lint, build, deploy pipelines
- **Matrix testing**: Python 3.11+ across multiple OS
- **Docker builds**: Multi-stage builds with caching

---

## Technical Specs

| Spec | Detail |
|------|--------|
| Language | Python 3.11+ |
| Models | Pydantic v2 |
| Framework | FastAPI |
| Auth | JWT + API Key |
| Billing | Stripe |
| Rate Limiting | Redis sliding window |
| Tests | 69 automated tests |
| CI/CD | GitHub Actions (reusable workflows) |

---

## What You Get

### Starter -- $49

- Full source code (schemas + infra + CI templates)
- README + usage documentation
- 69 passing tests
- Example FastAPI integration
- Community support (GitHub Issues)

### Pro -- $79

Everything in Starter, plus:

- **Integration guide** for existing FastAPI projects
- **Multi-tenant setup walkthrough** (PostgreSQL schema isolation)
- **Stripe billing configuration** (subscriptions + metering)
- **1-hour setup call** via Zoom
- Priority email support (48hr response)

### Enterprise -- $149

Everything in Pro, plus:

- **Custom schema development** for your domain
- **RBAC configuration** tailored to your org
- **CI/CD pipeline setup** in your GitHub repo
- **Architecture review** of your multi-tenant setup
- **30-day dedicated support** via Slack channel

---

## Who This Is For

- **SaaS developers** building multi-tenant applications
- **FastAPI teams** who need auth, billing, and rate limiting
- **AI startups** standardizing shared infrastructure
- **Solo developers** who want enterprise patterns without enterprise overhead

---

## Install

```bash
pip install -e ".[dev]"          # schemas only
pip install -e ".[all,dev]"      # schemas + stripe + fastapi + redis
```

---

## Bundle Note

This package is included **free** with the Enterprise AI Toolkit bundle ($499-$799). If you are buying multiple products from this portfolio, the bundle is a better deal.

---

## Proof

- 69 automated tests, all passing
- Extracted from production systems managing $50M+ pipeline
- Pydantic v2 with full type safety
- Part of an 8,500+ test portfolio across 11 production repos
