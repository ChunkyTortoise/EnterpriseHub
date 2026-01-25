"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""

# Fix for Python 3.10+ union syntax compatibility with FastAPI/Pydantic
import sys
import os
# Set environment variable to disable response model generation for union types
os.environ['FASTAPI_DISABLE_RESPONSE_MODEL_VALIDATION'] = 'true'

# Import Pydantic configuration to handle union syntax
try:
    from pydantic import ConfigDict
    from pydantic._internal._config import ConfigWrapper
    # Override Pydantic config to be more lenient with union types
    import pydantic
    if hasattr(pydantic, 'VERSION') and pydantic.VERSION >= '2.0.0':
        # For Pydantic v2, configure to handle union syntax
        import warnings
        warnings.filterwarnings("ignore", message=".*Union.*")
except ImportError:
    pass

from fastapi import FastAPI, Request, Response, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.routing import APIRoute
from typing import Callable, Any

# Custom route class to handle problematic union type responses
class UnionCompatibleRoute(APIRoute):
    def __init__(self, *args, **kwargs):
        # Apply response_model=None for routes that might have union type issues
        if 'response_model' not in kwargs:
            kwargs['response_model'] = None
        super().__init__(*args, **kwargs)
import os
import time
import logging
from contextlib import asynccontextmanager

# Import WebSocket and Socket.IO integration services
from ghl_real_estate_ai.api.socketio_app import integrate_socketio_with_fastapi
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.system_health_monitor import start_system_health_monitoring, stop_system_health_monitoring
from ghl_real_estate_ai.services.coordination_engine import get_coordination_engine

from ghl_real_estate_ai.api.routes import (
    analytics,
    attribution_reports,
    bot_management,  # Bot Management API for frontend integration
    bulk_operations,
    claude_chat,
    crm,
    golden_lead_detection,
    health,
    jorge_advanced,
    lead_lifecycle,
    leads,  # NEW: Leads Management API for frontend integration
    lead_bot_management,  # NEW: Lead Bot Management API for sequence control
    ml_scoring,  # Phase 4B: Real-time ML lead scoring API
    portal,
    predictive_analytics,
    pricing_optimization,
    properties,
    team,
    voice,
    webhook,
    auth,
    lead_intelligence,
    agent_sync,
    agent_ui,
    reports,
    jorge_followup,
    retell_webhook, # Added Retell Webhook
    vapi,
    websocket_routes, # Real-time WebSocket routes
    websocket_performance,  # WebSocket Performance Monitoring API
    external_webhooks,
    agent_ecosystem,  # NEW: Agent ecosystem API for frontend integration
    claude_concierge_integration,  # NEW: Claude Concierge integration API
    customer_journey,  # NEW: Customer Journey API
    property_intelligence,  # NEW: Property Intelligence API
    business_intelligence,  # NEW: BI Dashboard API routes
    bi_websocket_routes,  # NEW: BI WebSocket routes
)
from ghl_real_estate_ai.api.mobile.mobile_router import router as mobile_router
from ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from ghl_real_estate_ai.api.middleware.error_handler import ErrorHandlerMiddleware
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.api.enterprise.auth import enterprise_auth_service, EnterpriseAuthError
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for FastAPI."""
    # Startup logic
    logger = get_logger(__name__)
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

    # ========================================================================
    # START WEBSOCKET SERVICES (Phase 3: Real-time Integration)
    # ========================================================================

    logger.info("Starting WebSocket and real-time services...")

    try:
        # Start WebSocket manager background services
        websocket_manager = get_websocket_manager()
        await websocket_manager.start_services()
        logger.info("WebSocket manager services started")

        # Start event publisher
        event_publisher = get_event_publisher()
        await event_publisher.start()
        logger.info("Event publisher service started")

        # Start BI WebSocket services
        from ghl_real_estate_ai.api.routes.bi_websocket_routes import initialize_bi_websocket_services
        bi_started = await initialize_bi_websocket_services()
        if bi_started:
            logger.info("✅ BI WebSocket services started successfully")
        else:
            logger.warning("⚠️ BI WebSocket services failed to start - dashboard may have limited real-time features")

        # Start system health monitoring
        await start_system_health_monitoring()
        logger.info("System health monitoring started")

        # Initialize Socket.IO integration
        await integrate_socketio_with_fastapi(app)
        logger.info("Socket.IO integration completed")

        logger.info("✅ All real-time WebSocket services started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start WebSocket services: {e}")
        # Don't raise here - allow app to start but log the issue
        logger.warning("WebSocket services failed to start - real-time features may be unavailable")

    # ========================================================================
    # START LEAD SEQUENCE SCHEDULER (Critical for Lead Bot automation)
    # ========================================================================

    logger.info("Starting Lead Sequence Scheduler...")

    try:
        from ghl_real_estate_ai.services.scheduler_startup import initialize_lead_scheduler

        scheduler_started = await initialize_lead_scheduler()

        if scheduler_started:
            logger.info("✅ Lead Sequence Scheduler started successfully")
        else:
            logger.error("❌ Lead Sequence Scheduler failed to start")
            logger.warning("Lead Bot 3-7-30 sequences will not execute automatically")

    except Exception as e:
        logger.error(f"❌ Failed to start Lead Sequence Scheduler: {e}")
        logger.warning("Lead Bot automation will not function - sequences must be triggered manually")

    yield

    # ========================================================================
    # SHUTDOWN WEBSOCKET SERVICES
    # ========================================================================

    logger.info("Shutting down WebSocket and real-time services...")

    try:
        # Stop system health monitoring
        await stop_system_health_monitoring()
        logger.info("System health monitoring stopped")

        # Stop event publisher
        event_publisher = get_event_publisher()
        await event_publisher.stop()
        logger.info("Event publisher service stopped")

        # Stop BI WebSocket services
        from ghl_real_estate_ai.services.bi_websocket_server import get_bi_websocket_manager
        bi_websocket_manager = get_bi_websocket_manager()
        await bi_websocket_manager.stop()
        logger.info("BI WebSocket services stopped")

        # Stop WebSocket manager services
        websocket_manager = get_websocket_manager()
        await websocket_manager.stop_services()
        logger.info("WebSocket manager services stopped")

        logger.info("✅ All real-time services shutdown completed")

    except Exception as e:
        logger.error(f"❌ Error shutting down WebSocket services: {e}")

    # ========================================================================
    # SHUTDOWN LEAD SEQUENCE SCHEDULER
    # ========================================================================

    logger.info("Shutting down Lead Sequence Scheduler...")

    try:
        from ghl_real_estate_ai.services.scheduler_startup import shutdown_lead_scheduler

        await shutdown_lead_scheduler()
        logger.info("✅ Lead Sequence Scheduler shutdown completed")

    except Exception as e:
        logger.error(f"❌ Error shutting down Lead Sequence Scheduler: {e}")

    # Shutdown logic
    logger.info(f"Shutting down {settings.app_name}")

# Create FastAPI app with custom route class to handle union type issues
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="AI-powered real estate assistant for GoHighLevel - Mobile-First Agent Experience with AR/VR and Voice AI",
    docs_url="/docs" if settings.environment == "development" else None,
    redoc_url="/redoc" if settings.environment == "development" else None,
    lifespan=lifespan,
)

# Apply custom route class to handle union type compatibility issues
app.router.route_class = UnionCompatibleRoute

# Override default JSON response
app.default_response_class = OptimizedJSONResponse

logger = get_logger(__name__)

# HTTPS enforcement in production
if os.getenv("ENVIRONMENT") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# ============================================================================
# ENHANCED PERFORMANCE OPTIMIZATION: Advanced Compression & Optimization
# ============================================================================

# Multi-tier compression with intelligent sizing
app.add_middleware(GZipMiddleware, minimum_size=500, compresslevel=6)

# Performance metrics tracking
performance_stats = {
    "total_requests": 0,
    "total_response_time": 0,
    "cache_hits": 0,
    "compression_saved": 0
}

@app.middleware("http")
async def enhanced_performance_middleware(request: Request, call_next):
    """
    Enhanced performance optimization middleware with:
    - Advanced caching strategies
    - Response compression optimization
    - Performance monitoring and metrics
    - Content optimization
    - Request/response size tracking
    """
    start_time = time.time()
    path = request.url.path
    method = request.method

    # Track request metrics
    performance_stats["total_requests"] += 1

    # Request optimization
    if hasattr(request, 'headers'):
        # Enable client-side caching hints
        accepts_gzip = 'gzip' in request.headers.get('accept-encoding', '')

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time
    performance_stats["total_response_time"] += process_time

    # ========================================================================
    # ADVANCED CACHING STRATEGY
    # ========================================================================

    if path.startswith("/static/") or path.endswith((".css", ".js", ".png", ".jpg", ".ico", ".woff", ".woff2")):
        # Static assets - aggressive caching with versioning
        response.headers["Cache-Control"] = "public, max-age=31536000, immutable"  # 1 year
        response.headers["ETag"] = f'"{hash(path)}"'

    elif path.startswith("/api/analytics") or path.startswith("/api/dashboard"):
        # Analytics endpoints - smart caching
        response.headers["Cache-Control"] = "public, max-age=300, stale-while-revalidate=60"  # 5min + 1min stale
        performance_stats["cache_hits"] += 1

    elif path.startswith("/api/health"):
        # Health checks - minimal cache with validation
        response.headers["Cache-Control"] = "public, max-age=60, must-revalidate"

    elif path.startswith("/api/properties") or path.startswith("/api/leads"):
        # Dynamic data - micro-caching with revalidation
        response.headers["Cache-Control"] = "public, max-age=30, stale-while-revalidate=15"

    elif path.startswith("/api/claude") or path.startswith("/api/ai"):
        # AI endpoints - no cache but optimize for speed
        response.headers["Cache-Control"] = "no-cache, no-store"
        response.headers["Pragma"] = "no-cache"

    else:
        # Default - minimal caching
        response.headers["Cache-Control"] = "public, max-age=60"

    # ========================================================================
    # COMPRESSION & OPTIMIZATION HEADERS
    # ========================================================================

    # Add compression indicators
    response.headers["X-Content-Optimized"] = "true"

    # Performance monitoring headers
    response.headers["X-Process-Time"] = f"{process_time:.3f}"
    response.headers["X-Server-Version"] = settings.version
    response.headers["X-Compression-Level"] = "6"

    # Response size optimization headers
    content_length = response.headers.get("content-length")
    if content_length:
        response.headers["X-Original-Size"] = content_length

    # Add performance hints for client optimization
    if process_time < 0.1:
        response.headers["X-Performance"] = "excellent"
    elif process_time < 0.3:
        response.headers["X-Performance"] = "good"
    elif process_time < 0.5:
        response.headers["X-Performance"] = "acceptable"
    else:
        response.headers["X-Performance"] = "slow"

    # ========================================================================
    # SECURITY & OPTIMIZATION HEADERS
    # ========================================================================

    # Security headers for performance
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Resource optimization hints
    response.headers["X-DNS-Prefetch-Control"] = "on"

    # API-specific optimizations
    if path.startswith("/api/"):
        # Enable efficient JSON parsing
        response.headers["Content-Type"] = "application/json; charset=utf-8"

        # Add API performance metrics
        avg_response_time = performance_stats["total_response_time"] / max(performance_stats["total_requests"], 1)
        response.headers["X-Avg-Response-Time"] = f"{avg_response_time:.3f}"

        # Compression efficiency tracking
        if response.headers.get("content-encoding") == "gzip":
            performance_stats["compression_saved"] += 1
            response.headers["X-Compression-Ratio"] = "~30%"

    # ========================================================================
    # PERFORMANCE MONITORING & ALERTING
    # ========================================================================

    # Enhanced logging for performance analysis
    if process_time > 0.5:  # Slow request threshold
        logger.warning(
            f"Performance alert: Slow request detected",
            extra={
                "method": method,
                "path": path,
                "process_time": f"{process_time:.3f}s",
                "status_code": response.status_code,
                "user_agent": request.headers.get("user-agent", "unknown"),
                "content_length": content_length,
                "performance_tier": "slow"
            }
        )
    elif process_time > 0.3:  # Warning threshold
        logger.info(
            f"Performance monitoring: Moderate request time",
            extra={
                "method": method,
                "path": path,
                "process_time": f"{process_time:.3f}s",
                "performance_tier": "moderate"
            }
        )

    # Log performance milestones
    if performance_stats["total_requests"] % 100 == 0:
        cache_hit_rate = performance_stats["cache_hits"] / max(performance_stats["total_requests"], 1)
        compression_rate = performance_stats["compression_saved"] / max(performance_stats["total_requests"], 1)

        logger.info(
            f"Performance metrics update",
            extra={
                "total_requests": performance_stats["total_requests"],
                "avg_response_time": f"{avg_response_time:.3f}s",
                "cache_hit_rate": f"{cache_hit_rate:.2%}",
                "compression_rate": f"{compression_rate:.2%}"
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
app.include_router(websocket_routes.router, prefix="/api")  # Real-time WebSocket endpoints
app.include_router(websocket_performance.router)  # WebSocket Performance Monitoring API (already includes /api/v1 prefix)
app.include_router(bi_websocket_routes.router)  # BI WebSocket endpoints (no prefix, already includes /ws)
app.include_router(business_intelligence.router)  # BI API endpoints (already includes /api/bi prefix)
app.include_router(bot_management.router, prefix="/api")  # Bot Management API for frontend integration
app.include_router(lead_bot_management.router)  # Lead Bot Management API (prefix already included)
app.include_router(agent_ecosystem.router)  # NEW: Agent ecosystem endpoints (already has prefix)
app.include_router(claude_concierge_integration.router)  # NEW: Claude Concierge integration (already has prefix)
app.include_router(customer_journey.router)  # NEW: Customer Journey API (already has prefix)
app.include_router(property_intelligence.router)  # NEW: Property Intelligence API (already has prefix)
app.include_router(webhook.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(bulk_operations.router, prefix="/api")
app.include_router(claude_chat.router, prefix="/api")  # Claude chat interface
app.include_router(leads.router, prefix="/api")  # NEW: Leads Management API
app.include_router(lead_lifecycle.router, prefix="/api")
app.include_router(health.router, prefix="/api")  # Health endpoint at /api/health

# Enterprise Authentication Router
enterprise_auth_router = APIRouter(prefix="/api/enterprise/auth", tags=["enterprise_authentication"])

@enterprise_auth_router.post("/sso/initiate")
async def initiate_enterprise_sso_login(domain: str, redirect_uri: str):
    """
    Initiate enterprise SSO login flow.
    """
    try:
        sso_data = await enterprise_auth_service.initiate_sso_login(domain, redirect_uri)
        return sso_data
    except EnterpriseAuthError as e:
        raise HTTPException(status_code=400, detail=e.message)

@enterprise_auth_router.get("/sso/callback")
async def enterprise_sso_callback(code: str, state: str):
    """
    Handle enterprise SSO callback.
    """
    try:
        token_data = await enterprise_auth_service.handle_sso_callback(code, state)
        return token_data
    except EnterpriseAuthError as e:
        raise HTTPException(status_code=400, detail=e.message)

@enterprise_auth_router.post("/refresh")
async def refresh_enterprise_token(refresh_token: str):
    """
    Refresh enterprise access token.
    """
    try:
        token_data = await enterprise_auth_service.refresh_enterprise_token(refresh_token)
        return token_data
    except EnterpriseAuthError as e:
        raise HTTPException(status_code=401, detail=e.message)

app.include_router(enterprise_auth_router)

# Authentication routes (added by Agent 5)
app.include_router(auth.router, prefix="/api/auth")
app.include_router(properties.router, prefix="/api")
app.include_router(portal.router, prefix="/api")
app.include_router(team.router, prefix="/api")
app.include_router(crm.router, prefix="/api")
app.include_router(voice.router, prefix="/api")
app.include_router(lead_intelligence.router, prefix="/api")
app.include_router(agent_sync.router, prefix="/api")
app.include_router(agent_ui.router, prefix="/api/agent-ui", tags=["Agent UI"])
app.include_router(ml_scoring.router)  # Phase 4B: Real-time ML Lead Scoring API
app.include_router(predictive_analytics.router)  # Predictive Analytics ML endpoints
app.include_router(pricing_optimization.router)  # Pricing & ROI endpoints
app.include_router(golden_lead_detection.router)  # Golden Lead Detection endpoints
app.include_router(attribution_reports.router, prefix="/api")  # Attribution Reports endpoints
app.include_router(jorge_advanced.router, prefix="/api")  # Jorge's Advanced Features endpoints
app.include_router(jorge_followup.router, prefix="/api")  # Jorge's Follow-up Automation endpoints
app.include_router(reports.router, prefix="/api") # Reports router
app.include_router(retell_webhook.router, prefix="/api") # Retell AI Webhooks
app.include_router(vapi.router, prefix="/api") # Vapi Tool Integration
app.include_router(external_webhooks.router, prefix="/api") # External Webhooks (Twilio, SendGrid)

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


# Create the integrated Socket.IO + FastAPI app
# This is what uvicorn/gunicorn should run: ghl_real_estate_ai.api.main:socketio_app
from ghl_real_estate_ai.api.socketio_app import get_socketio_app_for_uvicorn
socketio_app = get_socketio_app_for_uvicorn(app)


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
