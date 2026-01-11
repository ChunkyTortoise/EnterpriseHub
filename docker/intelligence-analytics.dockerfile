"""
Docker Configuration for Intelligence Analytics System
Production-ready Docker image for the enhanced dashboard components.

This Dockerfile creates an optimized image for:
- Intelligence performance monitoring
- Analytics dashboard
- Real-time data connectors
- Enhanced visualizations

Created: January 10, 2026
Author: EnterpriseHub Development Team
"""

FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    APP_HOME=/app

# Set work directory
WORKDIR $APP_HOME

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    redis-tools \
    postgresql-client \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .
COPY requirements-analytics.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-analytics.txt

# Copy application code
COPY ghl_real_estate_ai/ ./ghl_real_estate_ai/
COPY scripts/ ./scripts/
COPY config/ ./config/

# Copy analytics-specific files
COPY ghl_real_estate_ai/services/intelligence_performance_monitor.py ./ghl_real_estate_ai/services/
COPY ghl_real_estate_ai/streamlit_components/intelligence_analytics_dashboard.py ./ghl_real_estate_ai/streamlit_components/
COPY ghl_real_estate_ai/streamlit_components/advanced_intelligence_visualizations.py ./ghl_real_estate_ai/streamlit_components/
COPY ghl_real_estate_ai/streamlit_components/unified_intelligence_dashboard.py ./ghl_real_estate_ai/streamlit_components/
COPY ghl_real_estate_ai/services/realtime_intelligence_connector.py ./ghl_real_estate_ai/services/
COPY ghl_real_estate_ai/services/dashboard_orchestrator.py ./ghl_real_estate_ai/services/

# Create necessary directories
RUN mkdir -p logs deployment_reports temp

# Set proper permissions
RUN chown -R appuser:appuser $APP_HOME

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8501/healthz', timeout=10)"

# Expose ports
EXPOSE 8501 8502 8503

# Default command
CMD ["python", "-m", "streamlit", "run", "ghl_real_estate_ai/streamlit_components/intelligence_analytics_dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]