# GHL Real Estate AI - Production Dockerfile
# Multi-stage build for optimized image size
# Supports: Python 3.11 on Linux amd64

FROM python:3.12-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for chromadb and ML libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (better layer caching)
COPY requirements-prod.txt .

# Install Python dependencies (prod-only: no heavy ML stack)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements-prod.txt

# Production stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code into named package directory so "ghl_real_estate_ai"
# is importable from WORKDIR (/app). Railway build context = ghl_real_estate_ai/,
# so COPY . . puts contents flat in /app/ — package wouldn't be found.
COPY . ./ghl_real_estate_ai/

# Create necessary runtime directories (relative to WORKDIR /app)
RUN mkdir -p data/knowledge_base data/memory data/analytics .chroma_db

# Set environment variables
ENV PYTHONUNBUFFERED=1
# Make sibling packages (ghl_integration, etc.) importable as top-level modules
# They live inside /app/ghl_real_estate_ai/ but are imported without the prefix
ENV PYTHONPATH=/app

# Expose FastAPI port (Railway overrides with $PORT)
EXPOSE 8000

# Run FastAPI with uvicorn (shell form so $PORT is expanded)
CMD ["/bin/sh", "-c", "uvicorn ghl_real_estate_ai.api.main_prod:app --host 0.0.0.0 --port ${PORT:-8000}"]
