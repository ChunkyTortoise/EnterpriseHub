# Enterprise Features -- Advanced RAG System

Production-grade authentication, multi-tenancy, and usage metering for the Advanced RAG System.

## Feature Matrix

| Feature | Starter | Pro | Enterprise |
|---------|---------|-----|------------|
| Document ingestion | 100 docs | 10,000 docs | Unlimited |
| Query API | 1,000/mo | 50,000/mo | Unlimited |
| Authentication | API Key | API Key + JWT | SSO + JWT + API Key |
| Multi-tenancy | Single tenant | Namespace isolation | Full isolation + audit |
| Usage metering | Basic counts | Per-tenant tracking | Real-time dashboards |
| Support | Community | Email (48hr SLA) | Dedicated (4hr SLA) |
| SLA | -- | 99.5% uptime | 99.9% uptime |

## Pricing

| Tier | Monthly | Annual (20% off) |
|------|---------|------------------|
| Starter | $99/mo | $950/yr |
| Pro | $499/mo | $4,790/yr |
| Enterprise | Custom | Custom |

## Quick Start

### API Key Authentication

Include your API key in the `X-API-Key` header:

```bash
curl -X POST https://api.example.com/query \
  -H "X-API-Key: your-api-key-here" \
  -H "Content-Type: application/json" \
  -d '{"query": "What are Q4 revenue projections?"}'
```

### JWT Authentication

Include a Bearer token in the `Authorization` header:

```bash
curl -X POST https://api.example.com/query \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{"query": "What are Q4 revenue projections?"}'
```

JWT tokens must include a `sub` claim identifying the tenant.

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENTERPRISE_API_KEYS` | Comma-separated valid API keys | `test-key-1,test-key-2` |
| `JWT_SECRET` | Secret for JWT validation | Dev secret (change in prod) |

## Contact

For enterprise pricing and custom deployments, contact: **enterprise@enterprisehub.dev**
