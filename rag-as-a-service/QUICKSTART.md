# RAG-as-a-Service -- Quick Start

Multi-tenant RAG platform with hybrid search, PII detection, and Stripe metered billing. Deploy a production document Q&A API for multiple customers from a single instance.

## What You Get

- Multi-tenant architecture with schema-per-tenant PostgreSQL isolation
- Hybrid search: pgvector cosine similarity + BM25 full-text with RRF fusion
- Query expansion via HyDE and multi-query techniques
- Built-in PII detection and redaction (email, phone, SSN, credit card, IP)
- Stripe metered billing with three pricing tiers
- Immutable audit logging for compliance
- 196+ automated tests with 90%+ coverage

## Prerequisites

- Python 3.11+
- PostgreSQL 15+ with the `pgvector` extension installed
- Redis 7+
- A Stripe account (for billing features)
- An OpenAI API key (or compatible LLM provider)

## Installation

```bash
git clone https://github.com/CaymanRoden/EnterpriseHub.git
cd EnterpriseHub/rag-as-a-service

python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

pip install -e ".[dev]"
```

## Configuration

```bash
cp .env.example .env
```

Edit `.env` with the required values:

```bash
# Required
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/rag_service
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-key-here
STRIPE_API_KEY=sk_test_your-key-here

# Security -- change in production
RAG_JWT_SECRET=change-me-to-64-char-random-string

# Optional
RAG_DEBUG=true
RAG_LLM_API_KEY=sk-your-key-here
RAG_EMBEDDING_API_KEY=sk-your-key-here
```

## Database Setup

```bash
# Enable pgvector (run once)
psql -U postgres -c "CREATE DATABASE rag_service"
psql -U postgres -d rag_service -c "CREATE EXTENSION IF NOT EXISTS vector"

# Run migrations
alembic upgrade head
```

## First Run

```bash
uvicorn rag_service.main:app --reload --port 8000
```

Expected output:

```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Application startup complete.
```

Verify the server is running:

```bash
curl http://localhost:8000/health
# {"status": "healthy"}
```

## Basic Usage

### 1. Create a Tenant

```bash
curl -X POST http://localhost:8000/api/v1/tenants \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corp",
    "slug": "acme-corp",
    "email": "admin@acme.com",
    "tier": "pro"
  }'
# Returns: {"api_key": "rag_live_xxxxx", "tenant_id": "..."}
```

Save the `api_key` from the response -- you need it for all subsequent requests.

### 2. Upload a Document

```bash
curl -X POST http://localhost:8000/api/v1/documents \
  -H "Authorization: Bearer rag_live_xxxxx" \
  -F "file=@your-document.pdf" \
  -F "collection_id=col_123"
```

### 3. Query Your Documents

```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Authorization: Bearer rag_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the key findings?",
    "collection_id": "col_123",
    "top_k": 5,
    "expand": true
  }'
```

Response:

```json
{
  "answer": "Based on the documents...",
  "sources": [
    {
      "chunk_id": "...",
      "content": "...",
      "score": 0.95
    }
  ],
  "latency_ms": 150
}
```

### 4. Stream Responses

```bash
curl -X POST http://localhost:8000/api/v1/query/stream \
  -H "Authorization: Bearer rag_live_xxxxx" \
  -H "Content-Type: application/json" \
  -d '{"query": "Summarize the document"}' \
  --no-buffer
```

## Running Tests

```bash
# All tests
pytest tests/

# With coverage report
pytest tests/ --cov=rag_service --cov-report=html

# Specific module
pytest tests/test_core/test_rag_engine.py -v
```

## Tier Limits

| Feature | Starter ($29/mo) | Pro ($99/mo) | Business ($499/mo) |
|---------|-------------------|--------------|---------------------|
| Queries/month | 5,000 | 50,000 | 500,000 |
| Storage | 1 GB | 10 GB | 100 GB |
| Collections | 5 | 50 | Unlimited |
| Team members | 1 | 5 | 25 |
| API rate limit | 60/min | 600/min | 6,000/min |

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| `connection refused` on startup | PostgreSQL not running | `brew services start postgresql` or `sudo systemctl start postgresql` |
| `extension "vector" not found` | pgvector not installed | Install pgvector: `brew install pgvector` or build from source |
| `OPENAI_API_KEY not set` | Missing env var | Add `OPENAI_API_KEY=sk-...` to `.env` |
| `Redis connection error` | Redis not running | `brew services start redis` or `sudo systemctl start redis` |
| `alembic: Target database is not up to date` | Pending migrations | Run `alembic upgrade head` |
| `ModuleNotFoundError: rag_service` | Package not installed | Run `pip install -e ".[dev]"` from the `rag-as-a-service/` directory |

## Next Steps

- Browse the API docs at `http://localhost:8000/docs` (Swagger UI)
- Set up Stripe webhooks for production billing
- Configure PII detection rules in `rag_service/compliance/pii_detector.py`
- Review the full README for deployment, Docker, and production checklist
- Explore multi-tenant isolation in `rag_service/multi_tenant/schema_manager.py`
