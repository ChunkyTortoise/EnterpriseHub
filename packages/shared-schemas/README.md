# shared-schemas

Multi-tenant schemas and shared infrastructure for AI portfolio products.

## Install

```bash
pip install -e ".[dev]"          # schemas only
pip install -e ".[all,dev]"      # schemas + stripe + fastapi + redis
```

## Packages

- **shared_schemas** — Pydantic v2 models for tenants, auth, billing, and domain events
- **shared_infra** — FastAPI middleware, Stripe billing, Redis rate limiter, health checks
- **ci_templates** — Reusable GitHub Actions workflows
