from __future__ import annotations

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .models import HealthResponse
from .routers import admin as admin_router
from .routers import ghl as ghl_router
from .routers import portal as portal_router
from .routers import root as root_router
from .routers import vapi as vapi_router

load_dotenv()


def create_app() -> FastAPI:
    app = FastAPI(title="GHL Real Estate AI API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(root_router.router)
    app.include_router(vapi_router.router)
    app.include_router(portal_router.router)
    app.include_router(ghl_router.router)
    app.include_router(admin_router.router)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="portal-api")

    return app


app = create_app()
