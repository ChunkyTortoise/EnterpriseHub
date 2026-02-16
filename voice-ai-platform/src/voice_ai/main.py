"""FastAPI application entry point with lifespan, CORS, and routers."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from voice_ai.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application lifespan — initialize and clean up resources."""
    settings = get_settings()
    logger.info("Starting %s (debug=%s)", settings.app_name, settings.debug)

    # Store settings on app state
    app.state.settings = settings
    app.state.db_session = None
    app.state.redis = None
    app.state.twilio_handler = None

    # Initialize Twilio handler
    if settings.twilio_account_sid:
        from voice_ai.telephony.twilio_handler import TwilioHandler

        app.state.twilio_handler = TwilioHandler(
            account_sid=settings.twilio_account_sid,
            auth_token=settings.twilio_auth_token,
            base_url=settings.base_url,
            phone_number=settings.twilio_phone_number,
        )

    yield

    # Cleanup
    logger.info("Shutting down %s", settings.app_name)


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Real-time Voice AI Agent Platform for real estate",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register routers
    from voice_ai.api.calls import router as calls_router
    from voice_ai.api.transcripts import router as transcripts_router
    from voice_ai.api.agents import router as agents_router
    from voice_ai.api.analytics import router as analytics_router
    from voice_ai.api.webhooks import router as webhooks_router

    app.include_router(calls_router)
    app.include_router(transcripts_router)
    app.include_router(agents_router)
    app.include_router(analytics_router)
    app.include_router(webhooks_router)

    @app.get("/health")
    async def health_check() -> dict[str, str]:
        return {"status": "healthy", "service": "voice-ai-platform"}

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"error": "internal_server_error", "message": "An unexpected error occurred"},
        )

    return app


app = create_app()
