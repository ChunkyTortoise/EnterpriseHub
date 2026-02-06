"""
Real-Time Dashboard Components

Advanced real-time visualization components with WebSocket connectivity,
live data streaming, and responsive design for executive dashboards.

Features:
- WebSocket-based live data streaming
- Real-time competitive intelligence updates
- Mobile-responsive dashboard components
- Progressive web app capabilities
- Live analytics visualization
- Multi-device synchronization

Author: Claude
Date: January 2026
"""

from .websocket_manager import WebSocketManager, WebSocketEvent, ConnectionStatus
from .live_data_streamer import LiveDataStreamer, StreamType, DataStream
from .real_time_visualizations import (
    RealTimeChart, LiveMetricsCard, StreamingHeatmap, 
    DynamicCompetitorMap, AlertNotificationSystem
)
from .mobile_responsive_components import (
    MobileExecutiveDashboard, ResponsiveLayoutManager, TouchOptimizedControls
)

# Export public API
__all__ = [
    # WebSocket management
    "WebSocketManager",
    "WebSocketEvent", 
    "ConnectionStatus",
    
    # Data streaming
    "LiveDataStreamer",
    "StreamType",
    "DataStream",
    
    # Real-time visualizations
    "RealTimeChart",
    "LiveMetricsCard",
    "StreamingHeatmap",
    "DynamicCompetitorMap", 
    "AlertNotificationSystem",
    
    # Mobile components
    "MobileExecutiveDashboard",
    "ResponsiveLayoutManager",
    "TouchOptimizedControls"
]

# Version info
__version__ = "1.0.0"
__author__ = "Claude"
__description__ = "Real-Time Dashboard Components for Competitive Intelligence"