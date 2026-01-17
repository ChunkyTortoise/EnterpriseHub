# EnterpriseHub - Optimized Guidelines

## Core Principles
- TDD discipline: RED → GREEN → REFACTOR
- Security-first: No secrets in code, validate inputs
- Quality gates: Tests pass, lint clean

## Tech Stack
- Python 3.11+, Streamlit, PostgreSQL, Redis
- Claude Assistant integration
- Docker deployment

## Workflow
1. Explore → Plan → Test → Code → Commit
2. Use skills: test-driven-development, frontend-design
3. Context: Focus on ghl_real_estate_ai/ directory

## Key Files
- claude_assistant.py - Core AI patterns
- cache_service.py - Redis caching
- llm_client.py - API integration

## Quality
```bash
pytest --cov=ghl_real_estate_ai
ruff check . && ruff format .
```

---
Optimized: <3k chars | v2.1.0