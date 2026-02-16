"""FastAPI application entry point with lifespan, CORS, and routers."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi.errors import RateLimitExceeded

from voice_ai.config import get_settings
from voice_ai.logging_config import RequestLoggingMiddleware, get_logger, setup_logging
from voice_ai.middleware.errors import register_error_handlers
from voice_ai.middleware.rate_limit import limiter, rate_limit_exceeded_handler
from voice_ai.middleware.security import APIKeyMiddleware
from voice_ai.middleware.security_headers import SecurityHeadersMiddleware

setup_logging()
logger = get_logger(__name__)


def _parse_allowed_origins() -> list[str]:
    """Parse ALLOWED_ORIGINS from env var (comma-separated) or default to localhost."""
    raw = os.environ.get("ALLOWED_ORIGINS", "")
    if raw:
        return [o.strip() for o in raw.split(",") if o.strip()]
    return ["http://localhost:3000"]


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

    # Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # Request logging (structured)
    app.add_middleware(RequestLoggingMiddleware)

    # Standardized error handlers
    register_error_handlers(app)

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

    @app.get("/ready")
    async def readiness_check():
        checks: dict[str, str] = {}

        # Database check
        try:
            if app.state.db_session:
                from sqlalchemy import text

                async with app.state.db_session() as session:
                    await session.execute(text("SELECT 1"))
                checks["database"] = "ok"
            else:
                checks["database"] = "not_configured"
        except Exception:
            checks["database"] = "error"

        # Redis check
        try:
            if app.state.redis:
                await app.state.redis.ping()
                checks["redis"] = "ok"
            else:
                checks["redis"] = "not_configured"
        except Exception:
            checks["redis"] = "error"

        # Twilio check
        try:
            if app.state.twilio_handler:
                checks["twilio"] = "ok"
            else:
                checks["twilio"] = "not_configured"
        except Exception:
            checks["twilio"] = "error"

        all_ok = all(v in ("ok", "not_configured") for v in checks.values())
        status_code = 200 if all_ok else 503
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_ok else "not_ready",
                "checks": checks,
            },
        )

    return app


app = create_app()
