"""
FastAPI V2 Main Application (Modular Agentic Powerhouse)
This version implements the 'Elite Stack' as defined in the Jan 2026 roadmap.
"""

import time
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from ghl_real_estate_ai.api.routes import health
from ghl_real_estate_ai.api.v2.routes import properties as properties_v2


# CORS configuration - must not use wildcard with credentials
CORS_ALLOWED_ORIGINS = os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
if not CORS_ALLOWED_ORIGINS or CORS_ALLOWED_ORIGINS == [""]:
    CORS_ALLOWED_ORIGINS = ["https://yourontario_mills.com"]  # Safe default


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize DB, Cache, etc.
    print("🚀 Starting GHL Real Estate AI V2 (Elite Stack)")
    yield
    # Shutdown: Clean up resources
    print("🛑 Shutting down GHL Real Estate AI V2")


app = FastAPI(title="GHL Real Estate AI - Modular Agentic Powerhouse", version="2.0.0", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Add routes
app.include_router(health.router, prefix="/api/v2/health", tags=["Health"])
app.include_router(properties_v2.router, prefix="/api/v2/properties", tags=["Properties"])


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


@app.get("/")
async def root():
    return {
        "message": "Welcome to GHL Real Estate AI V2 (Modular Agentic Powerhouse)",
        "status": "operational",
        "version": "2.0.0",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("v2_main:app", host="0.0.0.0", port=8000, reload=True)
