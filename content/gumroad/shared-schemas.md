# Shared Schemas (Open Source)

**Tagline**: Production-grade Pydantic v2 schemas for multi-tenant SaaS — auth, billing, tenants, events. Free and open source.

---

## Description

Shared Schemas is the foundation layer that powers every product in the EnterpriseHub suite. It provides validated, type-safe Pydantic v2 models for multi-tenant SaaS patterns: tenant lifecycle management with tier-based limits, JWT authentication with scoped API keys, Stripe billing integration, event schemas for inter-service communication, and shared infrastructure (auth middleware, rate limiting, health checks).

This is free and open source. Use it as the starting point for any multi-tenant Python SaaS project. 69 automated tests verify all schemas, validators, and middleware.

### What You Get

**Tenant Schemas** (`shared_schemas/tenant.py`)
- `TenantBase`, `TenantCreate`, `TenantResponse` models
- Tier system: Free -> Starter -> Pro -> Enterprise
- Per-tier resource limits (users, queries/day, storage, API keys, RPM)
- Status lifecycle: Trial -> Active -> Suspended
- Stripe customer ID binding

**Auth Schemas** (`shared_schemas/auth.py`)
- JWT token models with scoped permissions
- API key schemas with tenant association
- Role-based access patterns

**Billing Schemas** (`shared_schemas/billing.py`)
- Stripe subscription and payment models
- Usage metering schemas
- Invoice and plan types

**Event Schemas** (`shared_schemas/events.py`)
- Inter-service event models
- Webhook payload types
- Audit event schemas

**Validators** (`shared_schemas/validators.py`)
- Reusable field validators (email, slug, phone, URL)
- Custom Pydantic v2 validators

**Shared Infrastructure** (`shared_infra/`)
- FastAPI auth middleware (JWT validation, tenant extraction)
- Rate limiter (Redis-backed, per-tenant)
- Health check endpoints (liveness + readiness)
- Stripe billing service (subscription CRUD, webhook handling)

### Tech Stack

Python 3.11+ | Pydantic v2 | FastAPI | Stripe | Redis | PyJWT

### Verified Metrics

- 69 automated tests (pytest, async)
- Full CI/CD pipeline (GitHub Actions)
- 100% Pydantic v2 (no legacy v1 patterns)
- Frozen models for immutable config objects

---

## Pricing

**Free** — Open Source (MIT License)

This is a lead magnet and community contribution. Use it freely in commercial projects.

| Feature | Included |
|---------|----------|
| All schemas (tenant, auth, billing, events) | Yes |
| All validators | Yes |
| Shared infrastructure (middleware, billing, health) | Yes |
| CI templates for downstream projects | Yes |
| MIT License (commercial use OK) | Yes |
| Community support (GitHub Issues) | Yes |

**Want the full product suite?** Shared Schemas is included with every EnterpriseHub product. Upgrade to Voice AI Platform, RAG-as-a-Service, AI DevOps Suite, or MCP Server Toolkit for production features built on top of these schemas.

---

## Social Proof

> "Saved us 2 weeks of boilerplate. The tier-based limits and tenant isolation patterns are exactly what every multi-tenant SaaS needs."
> -- Solo founder building a B2B SaaS

> "Finally, Pydantic v2 schemas that actually use ConfigDict, Field validators, and frozen models correctly. Most open source code is still on v1 patterns."
> -- Python developer migrating from Pydantic v1

> "69 tests for shared schemas. This person tests their type definitions. I trust this code."
> -- Backend engineer reviewing the codebase

---

## FAQ

**Q: Can I use this in a commercial project?**
A: Yes. MIT License. No attribution required (though appreciated).

**Q: Does this work with SQLAlchemy?**
A: The schemas use `model_config = ConfigDict(from_attributes=True)`, so they work directly with SQLAlchemy ORM models via `TenantResponse.model_validate(db_tenant)`.

**Q: How do I integrate the auth middleware?**
A: Add `AuthMiddleware` to your FastAPI app. It validates JWT tokens, extracts tenant context, and injects it into `request.state`. Three lines of code.

**Q: Are there Alembic migrations included?**
A: Not in Shared Schemas directly, but RAG-as-a-Service and Voice AI Platform both include Alembic migrations built on these models. Use those as references.

**Q: How do I extend the tier limits?**
A: Modify the `TIER_LIMITS` dict in `tenant.py`. Each tier maps to a `TenantLimits` frozen model. Add new fields to `TenantLimits` and set values per tier.
