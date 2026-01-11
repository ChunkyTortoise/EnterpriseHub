"""
Mobile API Routes

REST API endpoints optimized for mobile clients with voice integration.
"""

from .voice_endpoints import voice_router
from .mobile_coaching_endpoints import mobile_coaching_router
from .real_time_endpoints import realtime_router

__all__ = [
    "voice_router",
    "mobile_coaching_router",
    "realtime_router"
]
