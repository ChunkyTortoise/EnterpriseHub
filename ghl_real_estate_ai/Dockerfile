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
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/knowledge_base data/memory data/analytics .chroma_db

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose FastAPI port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8000/api/health/live || exit 1

# Run FastAPI with uvicorn
CMD ["uvicorn", "ghl_real_estate_ai.api.main:socketio_app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
