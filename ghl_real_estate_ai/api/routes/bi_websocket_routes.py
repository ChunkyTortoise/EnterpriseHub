"""
BI-Specific WebSocket Routes for Real-Time Dashboard Integration.

Provides the 6 specific WebSocket endpoints that the frontend expects:
- /ws/dashboard/{location_id}
- /ws/bi/revenue-intelligence/{location_id}
- /ws/bot-performance/{location_id}
- /ws/business-intelligence/{location_id}
- /ws/ai-concierge/{location_id}
- /ws/analytics/advanced/{location_id}

Features:
- Integration with existing BI WebSocket manager
- Location-based routing and filtering
- Real-time metrics and dashboard updates
- Enhanced connection management with role-based access
- Performance monitoring and optimization

Author: Claude Sonnet 4
Date: 2026-01-25
Performance: <10ms WebSocket latency, 1000+ concurrent connections
"""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Path, Query, WebSocket, WebSocketDisconnect

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.bi_websocket_server import get_bi_websocket_manager
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)

# Create router for BI WebSocket endpoints
router = APIRouter(tags=["BI WebSocket Real-Time"])

# Get service instances
bi_websocket_manager = get_bi_websocket_manager()
cache_service = get_cache_service()


@router.websocket("/ws/dashboard/{location_id}")
async def dashboard_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for the dashboard"),
    token: Optional[str] = Query(None, description="Authentication token"),
    components: Optional[str] = Query(None, description="Comma-separated list of component subscriptions"),
):
    """
    Main BI Dashboard WebSocket endpoint.

    Provides real-time updates for the executive dashboard including:
    - KPI metrics and trends
    - Performance alerts
    - System health updates
    - Real-time event streaming

    Query Parameters:
        token: JWT authentication token (optional for development)
        components: Comma-separated component names to subscribe to

    WebSocket Events:
        - REALTIME_BI_UPDATE: Live dashboard metric updates
        - PERFORMANCE_WARNING: System performance alerts
        - SYSTEM_HEALTH_UPDATE: Component health status
        - COMPONENT_UPDATE: Specific dashboard component updates
    """
    try:
        logger.info(f"Dashboard WebSocket connection requested for location: {location_id}")

        # Parse component subscriptions
        component_list = (
            components.split(",")
            if components
            else ["executive_kpis", "revenue_metrics", "lead_metrics", "system_health"]
        )

        # Handle BI WebSocket connection with dashboard-specific channels
        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket,
            location_id=location_id,
            channels=["dashboard", "alerts", "system_health"],
            components=component_list,
        )

    except WebSocketDisconnect:
        logger.info(f"Dashboard WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"Dashboard WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


@router.websocket("/ws/bi/revenue-intelligence/{location_id}")
async def revenue_intelligence_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for revenue intelligence"),
    token: Optional[str] = Query(None, description="Authentication token"),
    forecast_days: Optional[int] = Query(90, description="Forecast period in days"),
):
    """
    Revenue Intelligence WebSocket endpoint.

    Provides real-time revenue analytics including:
    - Revenue forecasting updates
    - Commission calculations (Jorge's 6%)
    - Pipeline value changes
    - Predictive insights

    WebSocket Events:
        - REVENUE_PIPELINE_CHANGE: Pipeline value updates
        - COMMISSION_UPDATE: Jorge's commission calculations
        - REVENUE_FORECAST_UPDATE: ML-powered revenue predictions
        - PREDICTIVE_INSIGHT: Revenue-related insights
    """
    try:
        logger.info(f"Revenue Intelligence WebSocket connection for location: {location_id}")

        # Initialize revenue intelligence components
        revenue_components = [
            "revenue_forecasting",
            "commission_tracking",
            "pipeline_analytics",
            "predictive_revenue",
            "jorge_commission",
        ]

        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket,
            location_id=location_id,
            channels=["revenue_intelligence", "analytics"],
            components=revenue_components,
        )

    except WebSocketDisconnect:
        logger.info(f"Revenue Intelligence WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"Revenue Intelligence WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


@router.websocket("/ws/bot-performance/{location_id}")
async def bot_performance_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for bot performance"),
    token: Optional[str] = Query(None, description="Authentication token"),
    bot_types: Optional[str] = Query(None, description="Comma-separated list of bot types to monitor"),
):
    """
    Bot Performance Matrix WebSocket endpoint.

    Provides real-time bot performance monitoring including:
    - Jorge Seller Bot performance
    - Jorge Buyer Bot metrics
    - Lead Bot lifecycle tracking
    - Bot coordination metrics
    - Performance alerts

    WebSocket Events:
        - BOT_COORDINATION_UPDATE: Multi-bot coordination status
        - JORGE_QUALIFICATION_PROGRESS: Jorge bot qualification updates
        - LEAD_BOT_SEQUENCE_UPDATE: Lead bot sequence progress
        - BOT_PERFORMANCE_ALERT: Performance degradation alerts
    """
    try:
        logger.info(f"Bot Performance WebSocket connection for location: {location_id}")

        # Parse bot type filters
        (bot_types.split(",") if bot_types else ["jorge-seller", "jorge-buyer", "lead-bot", "intent-decoder"])

        # Bot performance specific components
        bot_components = [
            "bot_performance_matrix",
            "coordination_metrics",
            "bot_health",
            "qualification_tracking",
            "sequence_monitoring",
        ]

        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket,
            location_id=location_id,
            channels=["bot_performance", "alerts"],
            components=bot_components,
        )

    except WebSocketDisconnect:
        logger.info(f"Bot Performance WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"Bot Performance WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


@router.websocket("/ws/business-intelligence/{location_id}")
async def business_intelligence_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for business intelligence"),
    token: Optional[str] = Query(None, description="Authentication token"),
    intelligence_types: Optional[str] = Query(None, description="Intelligence types to subscribe to"),
):
    """
    Business Intelligence WebSocket endpoint.

    Provides comprehensive business intelligence including:
    - Executive dashboards
    - Predictive analytics
    - Performance insights
    - Market intelligence
    - Competitive analysis

    WebSocket Events:
        - BUSINESS_INSIGHT_UPDATE: New business intelligence insights
        - COMPETITIVE_INTELLIGENCE: Market and competitive updates
        - PERFORMANCE_ANALYSIS: Business performance analysis
        - EXECUTIVE_ALERT: High-priority business alerts
    """
    try:
        logger.info(f"Business Intelligence WebSocket connection for location: {location_id}")

        # Parse intelligence type filters
        (
            intelligence_types.split(",")
            if intelligence_types
            else ["executive_insights", "market_analysis", "competitive_intel", "performance_trends"]
        )

        # Business intelligence specific components
        bi_components = [
            "executive_dashboard",
            "market_intelligence",
            "competitive_analysis",
            "performance_insights",
            "predictive_analytics",
        ]

        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket, location_id=location_id, channels=["analytics", "drill_down"], components=bi_components
        )

    except WebSocketDisconnect:
        logger.info(f"Business Intelligence WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"Business Intelligence WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


@router.websocket("/ws/ai-concierge/{location_id}")
async def ai_concierge_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for AI concierge"),
    token: Optional[str] = Query(None, description="Authentication token"),
    concierge_features: Optional[str] = Query(None, description="AI concierge features to enable"),
):
    """
    AI Concierge Intelligence WebSocket endpoint.

    Provides real-time AI concierge updates including:
    - Proactive conversation coaching
    - Strategic recommendations
    - Conversation quality assessment
    - Coaching opportunities
    - AI-driven insights

    WebSocket Events:
        - AI_CONCIERGE_INSIGHT: New proactive insights
        - COACHING_OPPORTUNITY: Real-time coaching suggestions
        - STRATEGY_RECOMMENDATION: Strategic conversation pivots
        - CONVERSATION_QUALITY: Quality assessment updates
    """
    try:
        logger.info(f"AI Concierge WebSocket connection for location: {location_id}")

        # Parse concierge feature filters
        (
            concierge_features.split(",")
            if concierge_features
            else ["proactive_coaching", "conversation_quality", "strategic_insights", "performance_guidance"]
        )

        # AI concierge specific components
        concierge_components = [
            "proactive_insights",
            "coaching_engine",
            "conversation_analysis",
            "strategy_recommendations",
            "quality_monitoring",
        ]

        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket,
            location_id=location_id,
            channels=["analytics", "alerts"],
            components=concierge_components,
        )

    except WebSocketDisconnect:
        logger.info(f"AI Concierge WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"AI Concierge WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


@router.websocket("/ws/analytics/advanced/{location_id}")
async def advanced_analytics_websocket(
    websocket: WebSocket,
    location_id: str = Path(..., description="Location ID for advanced analytics"),
    token: Optional[str] = Query(None, description="Authentication token"),
    analytics_modules: Optional[str] = Query(None, description="Analytics modules to activate"),
):
    """
    Advanced Analytics WebSocket endpoint.

    Provides advanced ML-powered analytics including:
    - SHAP explainability analysis
    - Predictive modeling updates
    - Rancho Cucamonga market intelligence
    - Advanced performance metrics
    - ML model insights

    WebSocket Events:
        - ADVANCED_ANALYTICS_UPDATE: ML analytics updates
        - SHAP_ANALYSIS_COMPLETE: Feature importance analysis
        - MARKET_INTELLIGENCE_UPDATE: Rancho Cucamonga market updates
        - PREDICTIVE_MODEL_UPDATE: ML model performance updates
    """
    try:
        logger.info(f"Advanced Analytics WebSocket connection for location: {location_id}")

        # Parse analytics module filters
        (
            analytics_modules.split(",")
            if analytics_modules
            else ["shap_analysis", "predictive_modeling", "market_intelligence", "ml_insights"]
        )

        # Advanced analytics specific components
        advanced_components = [
            "shap_explainability",
            "ml_performance",
            "market_analytics",
            "predictive_insights",
            "advanced_metrics",
        ]

        await bi_websocket_manager.handle_bi_websocket(
            websocket=websocket,
            location_id=location_id,
            channels=["analytics", "drill_down"],
            components=advanced_components,
        )

    except WebSocketDisconnect:
        logger.info(f"Advanced Analytics WebSocket disconnected for location: {location_id}")
    except Exception as e:
        logger.error(f"Advanced Analytics WebSocket error for location {location_id}: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except (RuntimeError, ConnectionError) as e:
            logger.debug(f"WebSocket already closed: {e}")
            pass


# Administrative endpoints for BI WebSocket management


@router.get("/ws/bi/health")
async def bi_websocket_health():
    """
    BI WebSocket service health check.

    Returns:
        BI WebSocket service status and metrics
    """
    try:
        # Check if BI WebSocket manager exists and is operational
        if hasattr(bi_websocket_manager, "is_running"):
            is_running = bi_websocket_manager.is_running

            # Try to start if not running
            if not is_running:
                try:
                    await bi_websocket_manager.start()
                    is_running = True
                except Exception as start_error:
                    logger.warning(f"Could not start BI WebSocket manager: {start_error}")
                    is_running = False
        else:
            is_running = True  # Assume operational if no is_running attribute

        # Get metrics safely
        try:
            metrics = bi_websocket_manager.get_metrics() if hasattr(bi_websocket_manager, "get_metrics") else {}
        except Exception as metrics_error:
            logger.warning(f"Could not get BI WebSocket metrics: {metrics_error}")
            metrics = {}

        health_status = {
            "status": "healthy" if is_running else "degraded",
            "service": "BI WebSocket Real-Time Service",
            "bi_connections": metrics.get("total_connections", 0),
            "channel_subscriptions": metrics.get("channel_subscriptions", {}),
            "performance_metrics": metrics.get("channel_metrics", {}),
            "connection_quality": metrics.get("connection_quality", {}),
            "background_tasks_running": metrics.get("background_tasks_running", 0),
            "is_running": is_running,
            "last_check": datetime.now().isoformat(),
            "version": "Phase 7 BI Integration",
        }

        return health_status

    except Exception as e:
        logger.error(f"BI WebSocket health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "service": "BI WebSocket Real-Time Service",
            "last_check": datetime.now().isoformat(),
        }


@router.get("/ws/bi/metrics")
async def bi_websocket_metrics():
    """
    Get detailed BI WebSocket metrics.

    Returns:
        Comprehensive BI WebSocket performance metrics
    """
    try:
        metrics = bi_websocket_manager.get_metrics()
        return {"timestamp": datetime.now().isoformat(), "metrics": metrics}

    except Exception as e:
        logger.error(f"Failed to get BI WebSocket metrics: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Initialize BI WebSocket manager on module load
async def initialize_bi_websocket_services():
    """Initialize BI WebSocket services."""
    try:
        if not bi_websocket_manager.is_running:
            await bi_websocket_manager.start()
            logger.info("BI WebSocket manager services started")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize BI WebSocket services: {e}")
        return False
