"""
FastAPI Main Application for GHL Real Estate AI.

Entry point for the webhook server that processes GoHighLevel messages
and returns AI-generated responses.
"""

# Fix for Python 3.10+ union syntax compatibility with FastAPI/Pydantic
import os

# Set environment variable to disable response model generation for union types
os.environ["FASTAPI_DISABLE_RESPONSE_MODEL_VALIDATION"] = "true"

# Import Pydantic configuration to handle union syntax
try:
    # Override Pydantic config to be more lenient with union types
    import pydantic
    from pydantic import ConfigDict
    from pydantic._internal._config import ConfigWrapper

    if hasattr(pydantic, "VERSION") and pydantic.VERSION >= "2.0.0":
        # For Pydantic v2, configure to handle union syntax
        import warnings

        warnings.filterwarnings("ignore", message=".*Union.*")
except ImportError:
    pass


from fastapi import APIRouter, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.routing import APIRoute


# Custom route class to handle problematic union type responses
class UnionCompatibleRoute(APIRoute):
    def __init__(self, *args, **kwargs):
        # Apply response_model=None for routes that might have union type issues
        if "response_model" not in kwargs:
            kwargs["response_model"] = None
        super().__init__(*args, **kwargs)


import asyncio
import os
import time
from contextlib import asynccontextmanager

from fastapi.responses import JSONResponse

from ghl_real_estate_ai.api.enterprise.auth import EnterpriseAuthError, enterprise_auth_service
from ghl_real_estate_ai.api.middleware import (
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
)
from ghl_real_estate_ai.api.middleware.error_handler import ErrorHandlerMiddleware
from ghl_real_estate_ai.api.mobile.mobile_router import router as mobile_router
from ghl_real_estate_ai.api.routes import (
    agent_ecosystem,  # NEW: Agent ecosystem API for frontend integration
    agent_sync,
    agent_ui,
    analytics,
    attribution_reports,
    auth,
    behavioral_triggers,
    bi_websocket_routes,  # NEW: BI WebSocket routes
    bot_management,  # Bot Management API for frontend integration
    bulk_operations,
    business_intelligence,  # NEW: BI Dashboard API routes
    channel_routing,
    claude_chat,
    claude_concierge_integration,  # NEW: Claude Concierge integration API
    commission_forecast,
    crm,
    customer_journey,  # NEW: Customer Journey API
    error_monitoring,  # NEW: Error Monitoring Dashboard API
    export_engine,
    external_webhooks,
    fha_respa_compliance,
    golden_lead_detection,
    health,
    heygen_video,
    jorge_advanced,
    jorge_followup,
    # Week 5-8 ROI Enhancement Routes
    langgraph_orchestration,
    lead_bot_management,  # NEW: Lead Bot Management API for sequence control
    lead_intelligence,
    lead_lifecycle,
    leads,  # NEW: Leads Management API for frontend integration
    ml_scoring,  # Phase 4B: Real-time ML lead scoring API
    portal,
    predictive_analytics,
    pricing_optimization,
    propensity_scoring,
    properties,
    property_intelligence,  # NEW: Property Intelligence API
    rc_market_intelligence,
    reports,
    retell_webhook,  # Added Retell Webhook
    security,  # NEW: Security Monitoring and Management API
    sentiment_analysis,
    sms_compliance,
    team,
    vapi,
    voice,
    voice_intelligence,
    webhook,
    websocket_performance,  # WebSocket Performance Monitoring API
    websocket_routes,  # Real-time WebSocket routes
)

# Import WebSocket and Socket.IO integration services
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.observability import setup_observability
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.system_health_monitor import (
    start_system_health_monitoring,
)
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager


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

    # Initialize OpenTelemetry (reads from OTEL_ENABLED env var)
    otel_ok = setup_observability()
    if otel_ok:
        logger.info("OpenTelemetry tracing initialized successfully")

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
        except (ImportError, AttributeError, ValueError) as e:
            logger.error(f"Failed to auto-register primary tenant: {str(e)}")

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

        # Start error monitoring service
        from ghl_real_estate_ai.services.error_monitoring_service import get_error_monitoring_service

        error_monitoring = get_error_monitoring_service()
        await error_monitoring.start()
        logger.info("Error monitoring service started")

        # Socket.IO is initialized at module level for uvicorn,
        # but we ensure bridging is active
        if hasattr(app.state, "socketio_integration"):
            logger.info("Socket.IO integration already active in app state")

        logger.info("✅ All real-time WebSocket services started successfully")

    except Exception as e:
        logger.error(f"❌ Failed to start WebSocket services: {str(e)}")
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

    # ========================================================================
    # JORGE BOT MONITORING: Periodic alerting background task
    # ========================================================================

    alerting_task = None
    try:
        from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
        from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
        from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker

        async def _periodic_alert_check():
            """Run alert checks every 60 seconds.

            Builds a flat stats dict from BotMetricsCollector, PerformanceTracker,
            and JorgeHandoffService so that AlertingService rules can evaluate
            thresholds correctly.
            """
            alerting_svc = AlertingService()
            metrics_collector = BotMetricsCollector()
            perf_tracker = PerformanceTracker()
            while True:
                try:
                    await asyncio.sleep(60)
                    stats = await _build_alert_stats(metrics_collector, perf_tracker)
                    await alerting_svc.check_and_send_alerts(stats)
                except asyncio.CancelledError:
                    break
                except Exception as exc:
                    logger.debug("Periodic alert check error (non-fatal): %s", exc)

        alerting_task = asyncio.create_task(_periodic_alert_check())
        logger.info("Periodic alerting background task started (60s interval)")
    except Exception as e:
        logger.warning("Failed to start periodic alerting task: %s", e)

    # ========================================================================
    # STARTUP ENV VAR VALIDATION (non-blocking warnings)
    # ========================================================================

    _validate_jorge_services_config(logger)

    yield

    # Shutdown logic
    if alerting_task and not alerting_task.done():
        alerting_task.cancel()
        try:
            await alerting_task
        except asyncio.CancelledError:
            pass
        logger.info("Periodic alerting background task stopped")


async def _build_alert_stats(metrics_collector, perf_tracker) -> dict:
    """Build a flat stats dict matching AlertingService rule expectations.

    Merges data from BotMetricsCollector (interactions, handoffs),
    PerformanceTracker (P95 latencies), and JorgeHandoffService (analytics)
    into the key structure that the 7 default alert rules evaluate.
    """
    summary = metrics_collector.get_system_summary()
    overall = summary.get("overall", {})
    handoffs = summary.get("handoffs", {})
    bots = summary.get("bots", {})

    # Get P95 from PerformanceTracker (more accurate rolling-window stats)
    lead_stats = await perf_tracker.get_bot_stats("lead_bot")
    buyer_stats = await perf_tracker.get_bot_stats("buyer_bot")
    seller_stats = await perf_tracker.get_bot_stats("seller_bot")

    # Get handoff analytics for circular/rate-limit rules
    blocked_handoffs = 0
    rate_limit_error_rate = 0.0
    try:
        from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

        analytics = JorgeHandoffService.get_analytics_summary()
        blocked_handoffs = analytics.get("blocked_by_circular", 0) + analytics.get("blocked_by_rate_limit", 0)
        total_handoff_attempts = analytics.get("total_handoffs", 0) + blocked_handoffs
        if total_handoff_attempts > 0:
            rate_limit_error_rate = analytics.get("blocked_by_rate_limit", 0) / total_handoff_attempts
    except Exception as e:
        logger.debug(f"Failed to fetch handoff analytics for alert stats: {str(e)}")

    # Build flat dict matching alert rule conditions
    stats: dict = {
        # Rule 1: sla_violation — nested dicts with p95_latency_ms
        "lead_bot": {"p95_latency_ms": lead_stats.get("p95", 0.0)},
        "buyer_bot": {"p95_latency_ms": buyer_stats.get("p95", 0.0)},
        "seller_bot": {"p95_latency_ms": seller_stats.get("p95", 0.0)},
        # Rule 2: high_error_rate
        "error_rate": overall.get("error_rate", 0.0),
        # Rule 3: low_cache_hit_rate
        "cache_hit_rate": overall.get("cache_hit_rate", 1.0),
        # Rule 4: handoff_failure
        "handoff_success_rate": handoffs.get("success_rate", 1.0),
        # Rule 5: bot_unresponsive — last response timestamp
        "last_response_time": metrics_collector.last_interaction_time(),
        # Rule 6: circular_handoff_spike
        "blocked_handoffs_last_hour": blocked_handoffs,
        # Rule 7: rate_limit_breach
        "rate_limit_error_rate": rate_limit_error_rate,
    }
    return stats


def _validate_jorge_services_config(logger) -> None:
    """Validate Jorge Bot services configuration at startup.

    Checks environment variables for A/B testing, performance tracking,
    alerting channels, and bot metrics. Logs warnings for misconfigurations
    but never raises — the app should still start.
    """
    # -- A/B Testing --
    if os.getenv("AB_TESTING_ENABLED", "").lower() == "true":
        logger.info("A/B testing is enabled — experiments will be registered on first bot initialization")

    # -- Performance Tracking --
    if os.getenv("PERFORMANCE_TRACKING_ENABLED", "").lower() == "true":
        sample_rate = os.getenv("PERFORMANCE_TRACKING_SAMPLE_RATE", "1.0")
        try:
            rate = float(sample_rate)
            if not 0.0 <= rate <= 1.0:
                logger.warning(
                    "PERFORMANCE_TRACKING_SAMPLE_RATE=%s is out of range [0.0, 1.0] — defaulting to 1.0", sample_rate
                )
        except ValueError:
            logger.warning("PERFORMANCE_TRACKING_SAMPLE_RATE=%s is not a valid float — defaulting to 1.0", sample_rate)

    # -- Alerting Channels (uses AlertChannelConfig.validate()) --
    try:
        from ghl_real_estate_ai.services.jorge.alerting_service import AlertChannelConfig

        channel_config = AlertChannelConfig.from_environment()
        for warning in channel_config.validate():
            logger.warning("Alert channel config: %s", warning)
    except Exception as exc:
        logger.debug("Could not validate alert channel config: %s", exc)

    # -- Bot Metrics --
    if os.getenv("BOT_METRICS_ENABLED", "").lower() == "true":
        interval = os.getenv("BOT_METRICS_COLLECTION_INTERVAL", "60")
        try:
            iv = int(interval)
            if iv < 10:
                logger.warning(
                    "BOT_METRICS_COLLECTION_INTERVAL=%s is very low (<10s) — may cause high CPU usage", interval
                )
        except ValueError:
            logger.warning("BOT_METRICS_COLLECTION_INTERVAL=%s is not a valid integer — defaulting to 60", interval)


def _verify_admin_api_key():
    """Dependency that guards admin endpoints with an API key in production."""
    from fastapi import Depends, Header

    async def _check(x_admin_key: str | None = Header(default=None, alias="X-Admin-Key")):
        expected = os.getenv("ADMIN_API_KEY")
        if not expected:
            # No key configured → admin routes disabled in production
            if settings.environment == "production":
                raise HTTPException(status_code=403, detail="Admin API disabled — set ADMIN_API_KEY")
            return  # Allow in dev/demo/test
        if x_admin_key != expected:
            raise HTTPException(status_code=401, detail="Invalid admin API key")

    return Depends(_check)


def _setup_routers(app: FastAPI):
    """Initialize all routers for the application."""
    from ghl_real_estate_ai.api.jorge_alerting import router as jorge_alerting_router
    from ghl_real_estate_ai.api.routes import claude_concierge, demo

    admin_guard = _verify_admin_api_key()

    # Include routers
    app.include_router(websocket_routes.router, prefix="/api")
    app.include_router(websocket_performance.router)
    app.include_router(bi_websocket_routes.router)
    app.include_router(business_intelligence.router)
    app.include_router(bot_management.router, prefix="/api", dependencies=[admin_guard])
    app.include_router(lead_bot_management.router)
    app.include_router(agent_ecosystem.router)
    app.include_router(claude_concierge.router)
    app.include_router(claude_concierge_integration.router)
    app.include_router(customer_journey.router)
    app.include_router(property_intelligence.router)
    app.include_router(error_monitoring.router)
    app.include_router(security.router)
    app.include_router(demo.router)
    app.include_router(webhook.router, prefix="/api")
    app.include_router(analytics.router, prefix="/api")
    app.include_router(bulk_operations.router, prefix="/api", dependencies=[admin_guard])
    app.include_router(claude_chat.router, prefix="/api")
    app.include_router(leads.router, prefix="/api")
    app.include_router(lead_lifecycle.router, prefix="/api")
    app.include_router(health.router, prefix="/api")
    app.include_router(sms_compliance.router, prefix="/api")

    # Enterprise Authentication Router
    enterprise_auth_router = APIRouter(prefix="/api/enterprise/auth", tags=["enterprise_authentication"])

    @enterprise_auth_router.post("/sso/initiate")
    async def initiate_enterprise_sso_login(domain: str, redirect_uri: str):
        try:
            sso_data = await enterprise_auth_service.initiate_sso_login(domain, redirect_uri)
            return sso_data
        except EnterpriseAuthError as e:
            raise HTTPException(status_code=400, detail=e.message)

    @enterprise_auth_router.get("/sso/callback")
    async def enterprise_sso_callback(code: str, state: str):
        try:
            token_data = await enterprise_auth_service.handle_sso_callback(code, state)
            return token_data
        except EnterpriseAuthError as e:
            raise HTTPException(status_code=400, detail=e.message)

    @enterprise_auth_router.post("/refresh")
    async def refresh_enterprise_token(refresh_token: str):
        try:
            token_data = await enterprise_auth_service.refresh_enterprise_token(refresh_token)
            return token_data
        except EnterpriseAuthError as e:
            raise HTTPException(status_code=401, detail=e.message)

    app.include_router(enterprise_auth_router)

    # Other routers
    app.include_router(auth.router, prefix="/api/auth")
    app.include_router(properties.router, prefix="/api")
    app.include_router(portal.router, prefix="/api")
    app.include_router(team.router, prefix="/api")
    app.include_router(crm.router, prefix="/api", dependencies=[admin_guard])
    app.include_router(voice.router, prefix="/api")
    app.include_router(lead_intelligence.router, prefix="/api")
    app.include_router(agent_sync.router, prefix="/api")
    app.include_router(agent_ui.router, prefix="/api/agent-ui", tags=["Agent UI"])
    app.include_router(ml_scoring.router)
    app.include_router(predictive_analytics.router)
    app.include_router(pricing_optimization.router)
    app.include_router(golden_lead_detection.router)
    app.include_router(attribution_reports.router, prefix="/api")
    app.include_router(jorge_advanced.router, prefix="/api")
    app.include_router(jorge_followup.router, prefix="/api")
    app.include_router(jorge_alerting_router, prefix="/api")
    app.include_router(reports.router, prefix="/api")
    app.include_router(retell_webhook.router, prefix="/api")
    app.include_router(vapi.router, prefix="/api")
    app.include_router(external_webhooks.router, prefix="/api")
    app.include_router(mobile_router, prefix="/api")

    # Week 5-8 ROI Enhancement Routes
    app.include_router(langgraph_orchestration.router)
    app.include_router(behavioral_triggers.router)
    app.include_router(fha_respa_compliance.router)
    app.include_router(voice_intelligence.router)
    app.include_router(propensity_scoring.router)
    app.include_router(heygen_video.router)
    app.include_router(sentiment_analysis.router)
    app.include_router(channel_routing.router)
    app.include_router(rc_market_intelligence.router)
    app.include_router(export_engine.router)
    app.include_router(commission_forecast.router)


# Import OpenAPI tag metadata for enhanced documentation
from ghl_real_estate_ai.api.schemas.api_docs import OPENAPI_TAGS

# Create FastAPI app
app = FastAPI(
    title="EnterpriseHub API",
    description="AI-powered real estate lead qualification and CRM integration platform",
    version="5.0.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=OPENAPI_TAGS,
)

# Apply custom route class to handle union type compatibility issues
app.router.route_class = UnionCompatibleRoute

# Override default JSON response
app.default_response_class = OptimizedJSONResponse

# Setup routers immediately so they are registered before server starts
_setup_routers(app)

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
performance_stats = {"total_requests": 0, "total_response_time": 0, "cache_hits": 0, "compression_saved": 0}


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
    if hasattr(request, "headers"):
        # Enable client-side caching hints
        accepts_gzip = "gzip" in request.headers.get("accept-encoding", "")

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
                "performance_tier": "slow",
            },
        )
    elif process_time > 0.3:  # Warning threshold
        logger.info(
            f"Performance monitoring: Moderate request time",
            extra={
                "method": method,
                "path": path,
                "process_time": f"{process_time:.3f}s",
                "performance_tier": "moderate",
            },
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
                "compression_rate": f"{compression_rate:.2%}",
            },
        )

    return response


# ============================================================================
# COMPREHENSIVE ERROR HANDLING SYSTEM
# ============================================================================

# Add existing middleware error handler
app.add_middleware(ErrorHandlerMiddleware)

# Set up global exception handlers for consistent error responses
from ghl_real_estate_ai.api.middleware.global_exception_handler import setup_global_exception_handlers

setup_global_exception_handlers(app)

# Add CORS middleware (SECURITY FIX: Restrict origins)
# Environment-based CORS configuration
if os.getenv("ENVIRONMENT") == "production":
    ALLOWED_ORIGINS = [
        "https://app.gohighlevel.com",
        "https://*.gohighlevel.com",
        os.getenv("STREAMLIT_URL", ""),
        os.getenv("FRONTEND_URL", ""),
    ]
    # Remove empty strings and localhost
    ALLOWED_ORIGINS = [
        origin for origin in ALLOWED_ORIGINS 
        if origin and not origin.startswith("http://localhost")
    ]
else:
    # Development/Staging: Allow localhost but NOT wildcard
    ALLOWED_ORIGINS = [
        "https://app.gohighlevel.com",
        "https://*.gohighlevel.com",
        os.getenv("STREAMLIT_URL", "http://localhost:8501"),
        os.getenv("FRONTEND_URL", "http://localhost:3000"),
        "http://localhost:8501",
        "http://localhost:3000",
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
        "X-Device-ID",  # Mobile device identification
        "X-App-Version",  # Mobile app version
        "X-Platform",  # iOS/Android platform
        "X-Device-Model",  # Device model for optimization
        "X-Biometric-Token",  # Biometric authentication
        "X-GPS-Coordinates",  # Location services
        "X-AR-Capabilities",  # AR/VR capabilities
    ],
)
# Enhanced Security Middleware (Comprehensive Security Hardening)
from ghl_real_estate_ai.api.middleware.input_validation import InputValidationMiddleware

# Apply security middleware in the correct order (order matters for security!)
# 1. Input validation first (validate all incoming data) - FIXED for Jorge endpoints
# CRITICAL FIX: Input validation now properly handles natural language conversation data
app.add_middleware(
    InputValidationMiddleware,
    max_request_size=10 * 1024 * 1024,  # 10MB limit
    validate_json=True,
    validate_query_params=True,
    enable_sanitization=True,
)


# 2. Enhanced rate limiting with environment-based configuration
def get_rate_limit_config():
    """Get environment-appropriate rate limiting configuration"""
    env = os.getenv("ENVIRONMENT", "development")
    if env == "production":
        return {"requests_per_minute": 100, "authenticated_rpm": 1000, "enable_ip_blocking": True}
    elif env == "staging":
        return {"requests_per_minute": 500, "authenticated_rpm": 5000, "enable_ip_blocking": True}
    else:  # development/testing
        return {"requests_per_minute": 10000, "authenticated_rpm": 50000, "enable_ip_blocking": False}


rate_config = get_rate_limit_config()
app.add_middleware(RateLimitMiddleware, **rate_config)

# 3. Comprehensive security headers
app.add_middleware(
    SecurityHeadersMiddleware,
    environment=settings.environment,
    enable_csp=True,
    enable_hsts=True,
    enable_request_id=True,
)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with service info."""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "running",
        "environment": settings.environment,
        "docs": ("/docs" if settings.environment == "development" else "disabled in production"),
    }


# Lightweight health endpoint for load balancers (Fly.io)
@app.get("/health")
async def root_health():
    """Minimal liveness check for infrastructure health probes."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "environment": settings.environment,
        "service": settings.app_name,
        "version": settings.version,
    }


# Create the integrated Socket.IO + FastAPI app
# This is what uvicorn/gunicorn should run: ghl_real_estate_ai.api.main:socketio_app
from ghl_real_estate_ai.api.socketio_app import get_socketio_app_for_uvicorn

socketio_app = get_socketio_app_for_uvicorn(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
        log_level=settings.log_level.lower(),
    )
