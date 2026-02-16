"""FastAPI application with lifespan, CORS, and all routers."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from devops_suite.api import alerts, dashboards, events, experiments, extractions, jobs, prompts, schedules
from devops_suite.config import get_settings
from devops_suite.middleware.errors import register_error_handlers
from devops_suite.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from devops_suite.middleware.security import APIKeyMiddleware


def _parse_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS from env var (comma-separated) or default to localhost."""
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000"]


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Unified AI DevOps platform: agent monitoring, prompt registry, data pipeline",
        lifespan=lifespan,
    )

    # Rate limiter
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

    # CORS — locked to ALLOWED_ORIGINS env var
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_parse_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API key authentication
    app.add_middleware(APIKeyMiddleware)

    # Standardized error handlers
    register_error_handlers(app)

    # Mount all routers
    app.include_router(events.router)
    app.include_router(dashboards.router)
    app.include_router(alerts.router)
    app.include_router(prompts.router)
    app.include_router(experiments.router)
    app.include_router(jobs.router)
    app.include_router(schedules.router)
    app.include_router(extractions.router)

    @app.get("/health")
    async def health():
        return {"status": "healthy", "version": "0.1.0"}

    return app


app = create_app()
