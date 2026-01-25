"""
Socket.IO FastAPI Integration for Jorge's Real Estate AI Platform

Integrates Socket.IO server with FastAPI for horizontal scalability:
- Provides Socket.IO endpoint compatibility for frontend
- Maintains existing WebSocket infrastructure
- Supports multiple backend instances with Redis adapter
- Enables seamless scaling to 10,000+ concurrent users

This integration allows the frontend to use Socket.IO while preserving
the enterprise WebSocket manager for backend services.
"""

import os
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ghl_real_estate_ai.services.socketio_adapter import get_socketio_manager
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class SocketIOIntegration:
    """
    Socket.IO Integration for FastAPI Application

    Handles the integration of Socket.IO server with FastAPI while
    maintaining compatibility with existing WebSocket infrastructure
    for horizontal scaling.
    """

    def __init__(self, main_app: FastAPI):
        self.main_app = main_app
        self.socketio_manager = get_socketio_manager()
        self.websocket_manager = get_websocket_manager()
        self.sio = None

    def setup_socketio(self):
        """Setup Socket.IO server and integrate with FastAPI"""
        try:
            # Define CORS origins for Socket.IO
            cors_origins = [
                "http://localhost:3000",  # Next.js dev server
                "http://localhost:8501",  # Streamlit dev server
                "https://app.gohighlevel.com",
                "https://*.gohighlevel.com",
                os.getenv("FRONTEND_URL", "http://localhost:3000"),
                os.getenv("STREAMLIT_URL", "http://localhost:8501"),
            ]

            # Remove localhost origins in production
            if os.getenv("ENVIRONMENT") == "production":
                cors_origins = [
                    origin for origin in cors_origins
                    if not origin.startswith("http://localhost")
                ]

            # Create Socket.IO server (synchronous now)
            self.sio = self.socketio_manager.create_server(
                cors_allowed_origins=cors_origins
            )

            # Create ASGI app for Socket.IO
            socketio_asgi_app = socketio.ASGIApp(
                self.sio,
                other_asgi_app=self.main_app
            )

            # Bridge WebSocket events to Socket.IO
            self._setup_event_bridging()

            logger.info("Socket.IO integrated with FastAPI for horizontal scaling")
            return socketio_asgi_app

        except Exception as e:
            logger.error(f"Socket.IO setup error: {e}")
            raise

    def _setup_event_bridging(self):
        """
        Setup bidirectional event bridging between WebSocket and Socket.IO

        This ensures events flow correctly between:
        - Native WebSocket clients (backend services)
        - Socket.IO clients (frontend applications)
        """
        try:
            # Add Socket.IO bridge to WebSocket manager
            if hasattr(self.websocket_manager, '_socketio_bridge'):
                self.websocket_manager._socketio_bridge = self.socketio_manager.jorge_namespace.broadcast_to_socketio
            else:
                # Monkey patch for compatibility
                setattr(
                    self.websocket_manager,
                    '_socketio_bridge',
                    self.socketio_manager.jorge_namespace.broadcast_to_socketio
                )

            logger.info("Event bridging established between WebSocket and Socket.IO")

        except Exception as e:
            logger.error(f"Event bridging setup error: {e}")

def create_socketio_app(main_app: FastAPI) -> socketio.ASGIApp:
    """
    Create integrated Socket.IO + FastAPI application

    Args:
        main_app: Main FastAPI application instance

    Returns:
        ASGI application with Socket.IO integration
    """
    try:
        integration = SocketIOIntegration(main_app)
        socketio_app = integration.setup_socketio()

        logger.info("Socket.IO application created successfully")
        return socketio_app

    except Exception as e:
        logger.error(f"Socket.IO app creation failed: {e}")
        raise

# Startup integration function for main.py
async def integrate_socketio_with_fastapi(app: FastAPI):
    """
    Integration function to be called from main.py startup

    Modifies the main FastAPI app to include Socket.IO support
    while preserving all existing functionality.
    """
    try:
        # Start WebSocket background services
        websocket_manager = get_websocket_manager()
        await websocket_manager.start_services()

        # Create Socket.IO integration
        integration = SocketIOIntegration(app)

        # Setup Socket.IO server (this creates the server but doesn't replace the app)
        integration.setup_socketio()

        # Store integration in app state for access in main.py
        app.state.socketio_integration = integration

        logger.info("Socket.IO integration completed in FastAPI startup")

    except Exception as e:
        logger.error(f"Socket.IO integration error: {e}")
        raise

def get_socketio_app_for_uvicorn(main_app: FastAPI):
    """
    Get Socket.IO ASGI app for uvicorn deployment

    Returns a lazy factory function that uvicorn can call to create the
    integrated Socket.IO + FastAPI app when the event loop is ready.

    This avoids the uvloop/nest_asyncio compatibility issue by deferring
    the async setup until uvicorn has established the event loop.
    """
    class SocketIOAppFactory:
        """Lazy factory for Socket.IO app that works with uvicorn lifecycle"""

        def __init__(self, main_app: FastAPI):
            self.main_app = main_app
            self._app_cache = None

        async def __call__(self, scope, receive, send):
            """ASGI callable that creates the Socket.IO app on first request"""
            if self._app_cache is None:
                logger.info("Creating Socket.IO app (lazy initialization)")
                self._app_cache = create_socketio_app(self.main_app)

            # Delegate to the cached Socket.IO app
            return await self._app_cache(scope, receive, send)

    return SocketIOAppFactory(main_app)