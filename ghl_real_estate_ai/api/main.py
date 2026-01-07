"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os

from ghl_real_estate_ai.api.routes import (
    analytics,
    bulk_operations,
    crm,
    lead_lifecycle,
    portal,
    properties,
    team,
    voice,
    webhook,
    auth,
)
from ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from ghl_real_estate_ai.api.middleware.error_handler import ErrorHandlerMiddleware
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered real estate assistant for GoHighLevel - Phase 3 Voice Enhanced",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# HTTPS enforcement in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to GHL domains
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Security middleware (added by Agent 5)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(SecurityHeadersMiddleware)


# Include routers
app.include_router(webhook.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(bulk_operations.router, prefix="/api")
app.include_router(lead_lifecycle.router, prefix="/api")

# Authentication routes (added by Agent 5)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(properties.router, prefix="/api")
app.include_router(portal.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(voice.router, prefix="/api")


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "environment": settings.environment,
        "docs": (
            "/docs"
            if settings.environment == "development"
            else "disabled in production"
        ),
    }


@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version,
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(
        f"Starting {settings.app_name} v{settings.version}",
        extra={"environment": settings.environment, "model": settings.claude_model},
    )

    # Auto-register primary tenant from environment variables
    if settings.ghl_location_id and settings.ghl_api_key:
        try:
            from ghl_real_estate_ai.services.tenant_service import TenantService

            tenant_service = TenantService()
            await tenant_service.save_tenant_config(
                location_id=settings.ghl_location_id,
                anthropic_api_key=settings.anthropic_api_key,
                ghl_api_key=settings.ghl_api_key,
            )
            logger.info(f"Auto-registered primary tenant: {settings.ghl_location_id}")
        except Exception as e:
            logger.error(f"Failed to auto-register primary tenant: {e}")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.app_name}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
