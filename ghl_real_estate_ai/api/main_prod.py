"""
Minimal production entrypoint for Railway deployment.

Only loads what Jorge bots need:
  - /api/health/live  — Railway health check
  - /api/ghl/*        — GHL webhook handler (all 3 Jorge bots)

Intentionally skips: mobile, AR, enterprise SSO, analytics dashboard,
billing portal, Socket.IO — none needed for bot operation.
"""

from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from ghl_real_estate_ai.api import health
from ghl_real_estate_ai.api.routes import webhook


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Jorge Bot Server",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Railway health check: GET /api/health/live → 200
app.include_router(health.router, prefix="/api")

# GHL webhook: POST /api/ghl/webhook → bot logic
app.include_router(webhook.router, prefix="/api")
