#!/usr/bin/env bash
set -euo pipefail

echo "=== RAG-as-a-Service startup ==="

# Run Alembic migrations
echo "Running database migrations..."
alembic upgrade head
echo "Migrations complete."

# Determine worker count (default: 2 * CPU cores + 1, capped at 8)
WORKERS="${RAG_WORKERS:-$(python -c "import os; print(min(2 * os.cpu_count() + 1, 8))")}"

echo "Starting uvicorn with ${WORKERS} workers on ${RAG_HOST:-0.0.0.0}:${RAG_PORT:-8000}..."
exec uvicorn rag_service.main:app \
    --host "${RAG_HOST:-0.0.0.0}" \
    --port "${RAG_PORT:-8000}" \
    --workers "${WORKERS}" \
    --log-level info \
    --access-log
