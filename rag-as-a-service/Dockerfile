# Multi-stage build for RAG-as-a-Service
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY src/ src/

RUN pip install --no-cache-dir --prefix=/install .


FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

RUN groupadd -r rag && useradd -r -g rag -d /app -s /sbin/nologin rag

COPY --from=builder /install /usr/local
COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .
COPY scripts/start.sh scripts/start.sh

RUN chown -R rag:rag /app

USER rag

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["bash", "scripts/start.sh"]
