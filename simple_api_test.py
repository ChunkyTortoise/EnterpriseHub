#!/usr/bin/env python3
"""
Simple FastAPI App Test - Without SocketIO
Tests Jorge's BI Dashboard API endpoints without WebSocket complexity
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os

# Set environment variables
os.environ["JWT_SECRET_KEY"] = "jorge-bi-dashboard-jwt-secret-2026"

# Import the BI routes directly
from ghl_real_estate_ai.api.routes.business_intelligence import router as bi_router

# Create simple FastAPI app
app = FastAPI(
    title="Jorge's BI Dashboard API (Test)",
    description="Simple test of BI API endpoints without SocketIO",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add the BI router (note: the router already has /api/bi prefix)
app.include_router(bi_router, tags=["Business Intelligence"])

# Simple health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "jorge-bi-api-test"}

@app.get("/")
async def root():
    return {"message": "Jorge's BI Dashboard API Test - Ready for testing!"}

if __name__ == "__main__":
    print("🚀 Starting Jorge's BI Dashboard API (Simple Test)")
    print("📊 Testing BI endpoints without SocketIO complexity")
    print("🔗 Available at: http://localhost:8001")
    print("📋 API Docs: http://localhost:8001/docs")

    uvicorn.run(
        app,
        host="localhost",
        port=8001,
        log_level="info",
        loop="asyncio"  # Use asyncio loop to avoid uvloop conflict
    )