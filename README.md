<div align="center">
  <h1>EnterpriseHub</h1>
  <p><strong>Real Estate AI Platform with Multi-Agent Orchestration</strong></p>

  [![Python 3.11+](https://img.shields.io/badge/python-3.11+-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
  [![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
  [![Streamlit](https://img.shields.io/badge/Streamlit-1.41+-FF4B4B.svg?logo=streamlit&logoColor=white)](https://streamlit.io)
  [![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-336791.svg?logo=postgresql&logoColor=white)](https://postgresql.org/)
  [![Redis](https://img.shields.io/badge/Redis-7.0+-DC382D.svg?logo=redis&logoColor=white)](https://redis.io/)
  [![License: MIT](https://img.shields.io/badge/License-MIT-F1C40F.svg)](LICENSE)
</div>

---

## What This Is

EnterpriseHub is a real estate AI platform that automates lead qualification through coordinated AI agents. Three specialized bots (Lead, Buyer, Seller) qualify prospects using a Q0-Q4 framework, with results surfaced through a Streamlit BI dashboard and synced to GoHighLevel CRM.

Built as a working platform for a real estate client in the Rancho Cucamonga market.

## Architecture

```
                          +---------------------------+
                          |    Streamlit BI Dashboard  |
                          |  (Command Center)          |
                          +------------+--------------+
                                       |
+------------------+     +-------------+-------------+     +-------------------+
|   Jorge Bots     |     |       FastAPI Core         |     | GoHighLevel CRM   |
|                  +---->+    (Orchestration Layer)    +<----+   Integration     |
|  Lead Bot :8001  |     |                             |     |                   |
|  Seller Bot :8002|     |  Claude Orchestrator        |     |  Webhooks         |
|  Buyer Bot :8003 |     |  Agent Mesh Coordinator     |     |  Contact Sync     |
+------------------+     +-------------+---------------+     +-------------------+
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

- **Multi-agent bot orchestration** -- Lead, Buyer, and Seller qualification bots with Q0-Q4 framework and cross-bot handoff
- **Claude AI orchestration** -- Multi-strategy LLM parsing with L1/L2/L3 response caching and provider fallback
- **Agent mesh coordination** -- Governance, routing, auto-scaling, and audit trails across agent fleet
- **Real-time BI dashboard** -- Streamlit command center with lead pipeline, performance analytics, and commission tracking
- **GoHighLevel CRM integration** -- Webhook handling, contact sync, workflow triggers, rate-limited at 10 req/s
- **Advanced RAG pipeline** -- Hybrid BM25 + dense search with ChromaDB vector store and query enhancement
- **SMS compliance** -- TCPA opt-out handling, frequency limits, business hours enforcement

## Tech Stack

| Layer | Technology |
|-------|-----------|
| API | FastAPI (async), Pydantic validation |
| UI | Streamlit, Plotly, WebSocket |
| Database | PostgreSQL, Alembic migrations |
| Cache | Redis (L1), Application memory (L2), Database (L3) |
| AI/ML | Claude (primary), Gemini (analysis), OpenRouter (fallback) |
| CRM | GoHighLevel (webhooks, contacts, workflows) |
| Search | ChromaDB vector store, BM25, hybrid retrieval |
| Payments | Stripe (subscriptions, webhooks) |
| Infrastructure | Docker Compose, Fly.io |

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
streamlit run admin_dashboard.py --server.port 8501
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
│   ├── agents/                   # Bot implementations (Lead, Buyer, Seller)
│   ├── api/routes/               # FastAPI endpoints
│   ├── services/                 # Business logic layer
│   │   ├── claude_orchestrator.py    # Multi-LLM coordination + caching
│   │   ├── agent_mesh_coordinator.py # Agent fleet management
│   │   └── enhanced_ghl_client.py    # CRM integration (rate-limited)
│   ├── models/                   # SQLAlchemy models, Pydantic schemas
│   ├── intelligence/             # BI dashboard backends
│   ├── analytics/                # Revenue attribution, CLV
│   ├── compliance/               # SMS compliance, TCPA
│   └── streamlit_demo/           # Dashboard UI components
├── advanced_rag_system/          # RAG pipeline
│   └── src/                      # BM25, dense search, ChromaDB
├── tests/                        # Test suite
├── docker-compose.yml            # Container orchestration
├── alembic/                      # Database migrations
├── app.py                        # FastAPI entry point
├── admin_dashboard.py            # Streamlit BI dashboard
└── requirements.txt              # Python dependencies
```

## Core Services

| Service | File | What It Does |
|---------|------|-------------|
| Claude Orchestrator | `services/claude_orchestrator.py` | Multi-strategy LLM parsing, L1/L2/L3 response cache, provider fallback |
| Agent Mesh | `services/agent_mesh_coordinator.py` | Agent routing, governance, auto-scaling, audit trails |
| GHL Client | `services/enhanced_ghl_client.py` | GoHighLevel CRM sync with 10 req/s rate limiting |

## Testing

```bash
# Run test suite
python -m pytest tests/ -v

# Run with coverage
python -m pytest --cov=ghl_real_estate_ai --cov-report=term-missing
```

## Deployment

| Platform | Config File |
|----------|-------------|
| Docker Compose | `docker-compose.yml` |
| Fly.io | `fly.toml` |
| Railway | `railway.json` |
| Render | `render.yaml` |

```bash
docker-compose --profile production up -d
```

## Related Projects

- [**Jorge Bots**](https://github.com/ChunkyTortoise/jorge_real_estate_bots) -- Standalone 3-bot qualification system extracted from this platform. 279 tests, full technical spec.
- [**AgentForge**](https://github.com/ChunkyTortoise/ai-orchestrator) -- Provider-agnostic async LLM client library (Claude, Gemini, OpenAI, Perplexity).
- [**Revenue-Sprint**](https://github.com/ChunkyTortoise/Revenue-Sprint) -- Freelancer automation: Upwork scanner, proposal pipeline, LinkedIn outreach. 212+ tests.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.

---

**Author:** Cayman Roden ([@ChunkyTortoise](https://github.com/ChunkyTortoise))
