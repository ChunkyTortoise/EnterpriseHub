<div align="center">
  <h1>EnterpriseHub</h1>
  <p><strong>Enterprise Real Estate AI Platform with Multi-Agent Orchestration</strong></p>

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.41+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)
</div>

---

## What This Is

EnterpriseHub is a production-grade real estate AI platform that combines multi-agent bot orchestration, ML-powered lead scoring, and real-time business intelligence dashboards. Built for the Rancho Cucamonga and Austin markets, it integrates with GoHighLevel CRM to automate lead qualification, buyer/seller workflows, and market analysis through a coordinated system of specialized AI agents.

## Architecture

```
                          +---------------------------+
                          |    Streamlit BI Dashboard  |
                          |  (5 Intelligence Hubs)     |
                          +------------+--------------+
                                       |
+------------------+     +-------------+-------------+     +-------------------+
|   Jorge Bots     |     |       FastAPI Core         |     | GoHighLevel CRM   |
|                  +---->+    (Orchestration Layer)    +<----+   Integration     |
|  Lead Bot        |     |                             |     |                   |
|  Buyer Bot       |     |  Claude Orchestrator        |     |  Webhooks         |
|  Seller Bot      |     |  Agent Mesh Coordinator     |     |  Contact Sync     |
+------------------+     |  ML Lead Scoring Pipeline   |     |  Workflow Triggers |
                         +-------------+---------------+     +-------------------+
                                       |
              +------------------------+------------------------+
              |                        |                        |
    +---------+--------+    +----------+---------+    +---------+---------+
    |   PostgreSQL     |    |      Redis         |    |  AI Providers     |
    |   (Leads, Props, |    |  (Cache, Sessions, |    |  Claude, Gemini,  |
    |    Analytics)    |    |   Rate Limiting)   |    |  OpenRouter       |
    +------------------+    +--------------------+    +-------------------+
```

## Key Capabilities

- **Multi-agent bot orchestration** -- Lead, Buyer, and Seller qualification bots with autonomous handoff and cross-bot coordination
- **ML lead scoring pipeline** -- Gradient boosting models with SHAP explainability, 85%+ accuracy, and continuous retraining
- **Real-time BI dashboard** -- 5 intelligence hubs (Executive, Lead Intelligence, Sales Copilot, Automation Studio, Operations)
- **Advanced RAG pipeline** -- 0.7ms end-to-end retrieval (214x faster than target), hybrid BM25 + dense search with query enhancement
- **Multi-LLM orchestration** -- Claude (primary), Gemini (analysis), OpenRouter (fallback), with semantic response caching
- **GoHighLevel CRM integration** -- Webhook handling, contact sync, workflow triggers, and custom field mapping
- **Enterprise cache layer** -- 4,900+ ops/sec with L1/L2/L3 caching, LRU eviction, and circuit breakers
- **SMS compliance engine** -- TCPA opt-out handling, frequency limits, business hours enforcement, and audit trails

## Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| API response time | < 200ms | 42ms |
| Cache throughput | 1,000 ops/sec | 4,900+ ops/sec |
| RAG retrieval | < 150ms | 0.7ms |
| Lead scoring accuracy | > 80% | 85%+ |
| Bot intent classification | > 90% | 95% |
| Thread safety (concurrent ops) | 100% | 100% |
| Test coverage | > 80% | 80%+ (650+ tests) |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI, async/await, Pydantic validation |
| UI | Streamlit, Plotly, WebSocket real-time updates |
| Database | PostgreSQL, Alembic migrations |
| Cache | Redis (L1), Application memory (L2), Database (L3) |
| AI/ML | Claude, Gemini, OpenRouter, XGBoost, SHAP |
| CRM | GoHighLevel (webhooks, contacts, workflows) |
| Search | ChromaDB vector store, BM25, hybrid retrieval |
| Payments | Stripe (subscriptions, webhooks) |
| Voice | Retell AI, Vapi.ai |
| Infrastructure | Docker Compose, Fly.io, nginx |

## Quick Start

### Docker (recommended)

```bash
git clone https://github.com/ChunkyTortoise/EnterpriseHub.git
cd EnterpriseHub
cp .env.example .env
# Edit .env with your API keys

docker-compose up -d postgres redis
docker-compose up app
```

### Manual Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Database
alembic upgrade head

# API server
uvicorn app:app --reload --port 8000

# BI Dashboard (separate terminal)
streamlit run ghl_real_estate_ai/streamlit_demo/app.py --server.port 8501
```

### Required Environment Variables

At minimum, set these in your `.env` file:

```
ANTHROPIC_API_KEY=sk-ant-...       # Claude AI (primary provider)
DATABASE_URL=postgresql://...       # PostgreSQL connection
REDIS_URL=redis://localhost:6379    # Redis for caching
GHL_API_KEY=...                     # GoHighLevel CRM API key
GHL_LOCATION_ID=...                 # GoHighLevel location
JWT_SECRET_KEY=...                  # Auth token signing
```

See [`.env.example`](.env.example) for the full configuration reference.

## Project Structure

```
EnterpriseHub/
├── ghl_real_estate_ai/           # Main application
│   ├── agents/                   # Jorge bot implementations (Lead, Buyer, Seller)
│   ├── api/routes/               # FastAPI endpoints (40+ route files)
│   ├── services/                 # Business logic (62+ services)
│   ├── models/                   # SQLAlchemy models, Pydantic schemas
│   ├── intelligence/             # BI dashboard backends
│   ├── analytics/                # Revenue attribution, CLV analytics
│   ├── prediction/               # ML forecasting engines
│   ├── compliance/               # SMS compliance, security framework
│   ├── markets/                  # Multi-market expansion support
│   └── streamlit_demo/           # Dashboard UI (137 components)
│       ├── components/           # Reusable dashboard components
│       └── pages/                # Streamlit multi-page app
├── advanced_rag_system/          # RAG pipeline infrastructure
│   └── src/
│       ├── retrieval/            # BM25, dense, hybrid search
│       ├── embeddings/           # Vector embeddings with caching
│       └── vector_store/         # ChromaDB integration
├── tests/                        # Test suite (650+ tests)
├── docker-compose.yml            # Container orchestration
├── fly.toml                      # Fly.io deployment config
├── alembic/                      # Database migrations
└── requirements.txt              # Python dependencies
```

## Testing

```bash
# Run full test suite
python -m pytest --cov=ghl_real_estate_ai --cov-report=term-missing

# Run specific test modules
python -m pytest tests/services/ -v
python -m pytest advanced_rag_system/tests/ -v

# Run with coverage threshold
python -m pytest --cov=ghl_real_estate_ai --cov-fail-under=80
```

**Coverage:** 650+ tests across unit, integration, and end-to-end categories covering bot logic, service layers, API routes, cache operations, and ML pipelines.

## Deployment

The platform supports multiple deployment targets:

| Platform | Config File | Notes |
|----------|-------------|-------|
| Docker Compose | `docker-compose.yml` | Full stack with PostgreSQL, Redis, nginx |
| Fly.io | `fly.toml` | Production deployment with auto-scaling |
| Railway | `railway.json` | One-click deploy |
| Render | `render.yaml` | Managed infrastructure |

```bash
# Validate production readiness
python3 validate_environment.py

# Deploy with Docker
docker-compose --profile production up -d
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Install dev dependencies (`pip install -r dev-requirements.txt`)
4. Write tests first, then implement
5. Run `pytest` and `flake8` before committing
6. Open a Pull Request

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Author:** Cayman Roden ([@ChunkyTortoise](https://github.com/ChunkyTortoise))
