"""Observability module for EnterpriseHub.

Provides centralized OpenTelemetry configuration with auto-instrumentation
for FastAPI, httpx, asyncpg, and Redis.

Usage:
    from ghl_real_estate_ai.observability import setup_observability
    setup_observability()  # Call at app startup
"""

from ghl_real_estate_ai.observability.otel_config import setup_observability

__all__ = ["setup_observability"]
