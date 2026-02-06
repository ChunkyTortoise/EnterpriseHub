# Customer Intelligence Platform - Docker Image
# Multi-stage build for optimized production image

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create application user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY demo.py .

# Create necessary directories
RUN mkdir -p logs .cache data

# Change ownership to application user
RUN chown -R appuser:appuser /app

# Switch to application user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose ports
EXPOSE 8000 8501

# Default command (can be overridden)
CMD ["python", "src/api/main.py"]


# Production stage with minimal dependencies
FROM base as production

# Copy only necessary files
COPY --from=base /app /app
COPY --from=base /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=base /usr/local/bin /usr/local/bin

# Production optimizations
ENV ENVIRONMENT=production \
    LOG_LEVEL=INFO \
    CACHE_DIR=/app/.cache

# Set proper permissions
USER appuser

WORKDIR /app

# Default production command
CMD ["python", "src/api/main.py"]


# Development stage with additional tools
FROM base as development

# Install development dependencies
RUN pip install pytest pytest-asyncio black flake8 mypy

# Copy development configuration
COPY .env.example .env

# Development-specific environment variables
ENV ENVIRONMENT=development \
    LOG_LEVEL=DEBUG \
    RELOAD=true

# Development command
CMD ["python", "src/api/main.py"]