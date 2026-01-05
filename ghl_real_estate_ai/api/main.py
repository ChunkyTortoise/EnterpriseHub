"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.routes import webhook, analytics, bulk_operations, lead_lifecycle, properties, team, crm, voice
from ghl_real_estate_ai.ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    get_current_user
)

logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered real estate assistant for GoHighLevel - Phase 3 Voice Enhanced",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None
)

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
from ghl_real_estate_ai.api.routes import auth
app.include_router(auth.router, prefix="/api/auth")
app.include_router(properties.router, prefix="/api")
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
        "docs": "/docs" if settings.environment == "development" else "disabled in production"
    }


@app.get("/health")
async def health():
    """Health check endpoint for Railway."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.version
    }


@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(
        f"Starting {settings.app_name} v{settings.version}",
        extra={
            "environment": settings.environment,
            "model": settings.claude_model
        }
    )


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
        log_level=settings.log_level.lower()
    )
