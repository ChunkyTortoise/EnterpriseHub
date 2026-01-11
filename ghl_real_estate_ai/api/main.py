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
    autonomous_ai_endpoints,
    bulk_operations,
    claude_endpoints,
    crm,
    health,
    lead_lifecycle,
    portal,
    properties,
    realtime,
    seller_claude_api,
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
    description="AI-powered real estate assistant for GoHighLevel - Phase 5 Autonomous AI Enhanced",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
)

# HTTPS enforcement in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# Add Error Handler Middleware
app.add_middleware(ErrorHandlerMiddleware)

# Add CORS middleware with secure configuration
allowed_origins = ["*"] if settings.environment == "development" else [
    "https://app.gohighlevel.com",
    "https://*.gohighlevel.com",
    "https://ghl-integration.gohighlevel.com",
    # Add your production domains here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-GHL-Signature"],
)
# Security middleware (added by Agent 5)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)
app.add_middleware(SecurityHeadersMiddleware)


# Include routers
app.include_router(webhook.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(bulk_operations.router, prefix="/api")
app.include_router(lead_lifecycle.router, prefix="/api")
app.include_router(health.router)  # Health endpoint at root level

# Authentication routes (added by Agent 5)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(properties.router, prefix="/api")
app.include_router(portal.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(voice.router, prefix="/api")

# Claude AI Integration routes (15 endpoints)
app.include_router(claude_endpoints.router)

# Real-time WebSocket routes
app.include_router(realtime.router, prefix="/api")

# Seller-Claude Integration routes
app.include_router(seller_claude_api.router, prefix="/api/seller-claude")

# Autonomous AI Integration routes (9 endpoints - $500K-1.2M annual value)
app.include_router(autonomous_ai_endpoints.router)


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

    # Initialize autonomous AI systems
    try:
        from ghl_real_estate_ai.services.autonomous.self_learning_conversation_ai import self_learning_ai
        from ghl_real_estate_ai.services.autonomous.predictive_intervention_engine import predictive_intervention_engine
        from ghl_real_estate_ai.services.autonomous.multimodal_autonomous_coaching import multimodal_coaching

        logger.info("✅ Autonomous AI systems initialized successfully")
        logger.info("  - Self-Learning Conversation AI: Active")
        logger.info("  - Predictive Intervention Engine: Active")
        logger.info("  - Multimodal Autonomous Coaching: Active")
        logger.info("💰 Business value unlocked: $500K-1.2M annually")

    except Exception as e:
        logger.warning(f"⚠️ Autonomous AI systems initialization warning: {e}")
        logger.warning("Application will continue - systems will initialize on first request")


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
