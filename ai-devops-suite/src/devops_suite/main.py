"""FastAPI application with lifespan, CORS, and all routers."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from devops_suite.api import alerts, dashboards, events, experiments, extractions, jobs, prompts, schedules
from devops_suite.config import get_settings


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

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
