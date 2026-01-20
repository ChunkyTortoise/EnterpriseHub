"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os
import time
import logging
from contextlib import asynccontextmanager

from ghl_real_estate_ai.api.routes import (
    analytics,
    attribution_reports,
    bulk_operations,
    claude_chat,
    crm,
    golden_lead_detection,
    health,
    jorge_advanced,
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
from ghl_real_estate_ai.api.mobile.mobile_router import router as mobile_router
from ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from ghl_real_estate_ai.api.middleware.error_handler import ErrorHandlerMiddleware
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from fastapi.responses import JSONResponse

class OptimizedJSONResponse(JSONResponse):
    """Optimized JSON response with null value removal and compression."""
    
    def render(self, content) -> bytes:
        """Render JSON with optimization for smaller payloads."""
        if isinstance(content, dict):
            # Remove null values to reduce payload size
            content = self._remove_nulls(content)
        
        return super().render(content)
    
    def _remove_nulls(self, obj):
        """Recursively remove null values from dictionaries."""
        if isinstance(obj, dict):
            return {k: self._remove_nulls(v) for k, v in obj.items() if v is not None}
        elif isinstance(obj, list):
            return [self._remove_nulls(item) for item in obj if item is not None]
        return obj

# Override default JSON response
app.default_response_class = OptimizedJSONResponse

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
    description="AI-powered real estate assistant for GoHighLevel - Mobile-First Agent Experience with AR/VR and Voice AI",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# HTTPS enforcement in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# PERFORMANCE OPTIMIZATION: GZip compression middleware for 30% payload reduction
app.add_middleware(GZipMiddleware, minimum_size=500)

# PERFORMANCE OPTIMIZATION: Custom response optimization middleware
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """Performance optimization middleware with caching headers and monitoring."""
    start_time = time.time()
    
    # Add response optimization
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    
    # Add caching headers based on endpoint type
    path = request.url.path
    if path.startswith("/static/") or path.endswith((".css", ".js", ".png", ".jpg", ".ico")):
        # Static assets - long cache
        response.headers["Cache-Control"] = "public, max-age=86400"  # 24 hours
    elif path.startswith("/api/analytics") or path.startswith("/api/dashboard"):
        # Analytics endpoints - medium cache
        response.headers["Cache-Control"] = "public, max-age=300"   # 5 minutes
    elif path.startswith("/api/health"):
        # Health checks - short cache
        response.headers["Cache-Control"] = "public, max-age=60"    # 1 minute
    elif path.startswith("/api/properties") or path.startswith("/api/leads"):
        # Dynamic data - minimal cache
        response.headers["Cache-Control"] = "public, max-age=30"    # 30 seconds
    
    # Add performance monitoring headers
    response.headers["X-Server-Version"] = settings.version
    
    # Log slow requests for optimization
    if process_time > 0.5:  # Log requests over 500ms
        logger.warning(
            f"Slow request detected",
            extra={
                "method": request.method,
                "path": path,
                "process_time": f"{process_time:.3f}s",
                "status_code": response.status_code
            }
        )
    
    return response

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
    allow_headers=[
        "Content-Type", 
        "Authorization", 
        "X-API-Key", 
        "X-Location-ID",
        "X-Device-ID",          # Mobile device identification
        "X-App-Version",        # Mobile app version
        "X-Platform",           # iOS/Android platform
        "X-Device-Model",       # Device model for optimization
        "X-Biometric-Token",    # Biometric authentication
        "X-GPS-Coordinates",    # Location services
        "X-AR-Capabilities"     # AR/VR capabilities
    ],
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
app.include_router(jorge_advanced.router, prefix="/api")  # Jorge's Advanced Features endpoints

# Mobile API endpoints (Mobile-First Agent Experience)
app.include_router(mobile_router, prefix="/api")  # Mobile API with AR/VR and voice capabilities


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
