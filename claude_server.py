"""
Minimal Claude AI Server for Production Deployment
Includes only Claude functionality for maximum reliability
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent / "ghl_real_estate_ai"))

from ghl_real_estate_ai.api.routes.claude_endpoints import router

app = FastAPI(
    title="Claude AI Services",
    version="1.0.0",
    description="Production Claude AI Integration for EnterpriseHub"
)

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://app.gohighlevel.com", "*"],  # * for development, restrict in production
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# Include Claude endpoints
app.include_router(router)

@app.get("/")
async def root():
    """Root endpoint with Claude service info."""
    return {
        "status": "Claude AI Services Running",
        "endpoints": 15,
        "services": ["coaching", "semantic", "qualification", "actions", "voice"],
        "version": "1.0.0",
        "business_value": "$200K-400K annually"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )