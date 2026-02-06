#!/usr/bin/env python3
"""
Simple WebSocket Health Server for Testing

Demonstrates the deployed WebSocket functionality with a minimal FastAPI server.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Set required environment variables for testing
os.environ.setdefault('JWT_SECRET_KEY', 'test-secret-key-for-websocket-health-endpoint-validation-32plus-chars')
os.environ.setdefault('ANTHROPIC_API_KEY', 'sk-ant-test')
os.environ.setdefault('GHL_API_KEY', 'test-ghl-key')

# Import WebSocket routes
from ghl_real_estate_ai.api.routes import websocket_routes

# Create minimal FastAPI app
app = FastAPI(
    title="Jorge's WebSocket Integration Test",
    version="1.0.0",
    description="Testing WebSocket integration deployment"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include WebSocket routes
app.include_router(websocket_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {
        "status": "WebSocket Integration Test Server",
        "version": "1.0.0",
        "websocket_health": "/api/websocket/health",
        "websocket_status": "/api/websocket/status",
        "message": "Phase 3 WebSocket Integration: OPERATIONAL"
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting WebSocket Integration Test Server...")
    print("📊 Health Endpoint: http://localhost:8001/api/websocket/health")
    print("📈 Status Endpoint: http://localhost:8001/api/websocket/status")
    print("🎯 Root Endpoint: http://localhost:8001/")
    print()

    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")