# Developer Guide

## Prerequisites
- Python 3.11+
- Docker + Docker Compose
- PostgreSQL and Redis (local or via Docker)

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Environment
- Configure `.env` based on `.env.example`
- Required secrets depend on enabled providers (Claude, OpenAI, GHL, etc.)

## Database
```bash
alembic upgrade head
python scripts/seed_data.py
```

## Running Locally
```bash
# API
uvicorn ghl_real_estate_ai.api.main:app --reload --host 0.0.0.0 --port 8000

# Streamlit UI
streamlit run ghl_real_estate_ai/streamlit_demo/app.py
```

## Testing
```bash
pytest --cov=ghl_real_estate_ai --cov-fail-under=80
```

## Code Style
- Follow existing conventions in the codebase
- Keep components self-contained and Streamlit-safe
- Prefer typed, composable services

## Smart Analyst
- Data grid powered by `streamlit-aggrid` if available
- NL2SQL uses schema-aware validation and SELECT-only enforcement

## Agent Hub
- LangGraph state graph
- Planner → Researcher → Reviewer → Publisher
- Human approval gate via Streamlit UI
