#!/usr/bin/env bash
set -euo pipefail

echo "Starting EnterpriseHub..."

# 1. Start PostgreSQL + Redis
docker compose up -d postgres redis

# 2. Wait for Postgres to be ready
echo "Waiting for PostgreSQL..."
until docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; do
  sleep 1
done

# 3. Run Alembic migrations
docker compose run --rm app alembic upgrade head

# 4. Seed demo data
docker compose run --rm app python scripts/seed_demo_environment.py

# 5. Start all services
docker compose up -d

echo ""
echo "EnterpriseHub is running:"
echo "  Streamlit Dashboard  -> http://localhost:8501"
echo "  FastAPI + Swagger    -> http://localhost:8000/docs"
echo "  Prometheus           -> http://localhost:9090"
echo "  Grafana              -> http://localhost:3000"
