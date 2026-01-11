"""
Advanced AI Features API Routes (Phase 5)

Provides comprehensive API endpoints for all Phase 5 advanced AI capabilities:
- Multi-language voice processing with cultural adaptation
- Advanced predictive behavior analysis and intervention strategies
- Industry vertical specialization for different real estate markets
- Enhanced personalization with real-time recommendations
- WebSocket endpoints for real-time advanced feature processing

All endpoints support enterprise-grade performance and multi-tenant architecture.
"""

from .advanced_ai_endpoints import router as advanced_ai_router
from .multi_language_api import router as multi_language_router
from .intervention_api import router as intervention_router
from .personalization_api import router as personalization_router
from .websocket_endpoints import router as websocket_router

__all__ = [
    "advanced_ai_router",
    "multi_language_router",
    "intervention_router",
    "personalization_router",
    "websocket_router"
]