"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
import os
from contextlib import asynccontextmanager

from ghl_real_estate_ai.api.routes import (
    analytics,
    attribution_reports,
    bulk_operations,
    claude_chat,
    crm,
    golden_lead_detection,
    health,
    lead_lifecycle,
    portal,
    predictive_analytics,
    pricing_optimization,
    properties,
    team,
    voice,
    webhook,
    auth,
    lead_intelligence,
)
from ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from ghl_real_estate_ai.api.middleware.error_handler import ErrorHandlerMiddleware
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI."""
    # Startup logic
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
            
    yield
    
    # Shutdown logic
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered real estate assistant for GoHighLevel - Phase 3 Voice Enhanced",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# HTTPS enforcement in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# Add CORS middleware (SECURITY FIX: Restrict origins)
ALLOWED_ORIGINS = [
    "https://app.gohighlevel.com",
    "https://*.gohighlevel.com",
    os.getenv("STREAMLIT_URL", "http://localhost:8501"),
    os.getenv("FRONTEND_URL", "http://localhost:3000"),
]

# Production security: Remove localhost origins
if os.getenv("ENVIRONMENT") == "production":
    ALLOWED_ORIGINS = [
        origin for origin in ALLOWED_ORIGINS
        if not origin.startswith("http://localhost")
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Location-ID"],
)
# Security middleware (added by Agent 5)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(SecurityHeadersMiddleware)


# Include routers
app.include_router(webhook.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(bulk_operations.router, prefix="/api")
app.include_router(claude_chat.router, prefix="/api")  # Claude chat interface
app.include_router(lead_lifecycle.router, prefix="/api")
app.include_router(health.router)  # Health endpoint at root level

# Authentication routes (added by Agent 5)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(properties.router, prefix="/api")
app.include_router(portal.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(lead_intelligence.router, prefix="/api")
app.include_router(predictive_analytics.router)  # Predictive Analytics ML endpoints
app.include_router(pricing_optimization.router)  # Pricing & ROI endpoints
app.include_router(golden_lead_detection.router)  # Golden Lead Detection endpoints
app.include_router(attribution_reports.router, prefix="/api")  # Attribution Reports endpoints


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


# Health endpoint now handled by health router


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
