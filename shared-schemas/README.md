# shared-schemas

Foundational schemas and infrastructure for the portfolio product suite. All products import from this package for consistent tenant models, authentication, billing, and CI/CD templates.

## Installation

```bash
pip install -e ".[dev]"
```

## Quick Start

### Schemas

```python
from shared_schemas import TenantCreate, TenantTier, UsageEvent, UsageEventType

# Create a tenant
tenant = TenantCreate(name="Acme Corp", slug="acme-corp", email="admin@acme.com", plan=TenantTier.PRO)

# Report usage
event = UsageEvent(tenant_id="cus_123", event_type=UsageEventType.RAG_QUERY, quantity=1.0)
```

### Stripe Billing

```python
from shared_infra import StripeBillingService
from shared_schemas import UsageEvent, UsageEventType

billing = StripeBillingService(api_key="sk_...", webhook_secret="whsec_...")
customer = await billing.create_customer("admin@acme.com", "Acme Corp")
await billing.report_usage(UsageEvent(tenant_id=customer["id"], event_type=UsageEventType.RAG_QUERY, quantity=1))
```

### Auth Middleware (FastAPI)

```python
from shared_infra import AuthMiddleware
from redis import asyncio as aioredis

redis = aioredis.from_url("redis://localhost:6379")
auth = AuthMiddleware(redis=redis, db_session_factory=get_session, jwt_secret="your-secret")

@app.get("/protected")
async def protected(ctx=Depends(auth.get_current_tenant)):
    return {"tenant": ctx.tenant_id}
```

### Rate Limiter

```python
from shared_infra import TokenBucketRateLimiter

limiter = TokenBucketRateLimiter(redis=redis, default_max_tokens=100, default_refill_rate=10.0)
allowed = await limiter.check_rate_limit("tenant-id", endpoint="api/query")
```

### Health Checks

```python
from shared_infra import create_health_router

app.include_router(create_health_router(redis=redis, service_name="my-service"))
# GET /health -> {"status": "healthy"}
# GET /ready  -> {"status": "ready", "checks": {"redis": "ok"}}
```

## Testing

```bash
pytest tests/ -v
```

## Package Structure

```
shared_schemas/     # Pydantic v2 schemas (tenant, auth, billing, events, validators)
shared_infra/       # Infrastructure services (Stripe, auth middleware, rate limiter, health)
ci_templates/       # Reusable GitHub Actions workflows
tests/              # 40+ tests with mocked dependencies
```
