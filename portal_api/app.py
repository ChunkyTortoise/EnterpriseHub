from __future__ import annotations

from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .dependencies import DemoAuthError
from .models import ApiErrorDetail, ApiErrorResponse, HealthResponse
from .routers import admin as admin_router
from .routers import ghl as ghl_router
from .routers import portal as portal_router
from .routers import root as root_router
from .routers import vapi as vapi_router

load_dotenv()
REQUEST_ID_HEADER = "X-Request-ID"


def create_app() -> FastAPI:
    app = FastAPI(title="GHL Real Estate AI API", version="1.0.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response

    @app.exception_handler(DemoAuthError)
    async def demo_auth_exception_handler(request: Request, exc: DemoAuthError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        payload = ApiErrorResponse(
            error=ApiErrorDetail(code="unauthorized", message=str(exc), request_id=request_id)
        ).model_dump()
        response = JSONResponse(status_code=401, content=payload)
        if request_id:
            response.headers[REQUEST_ID_HEADER] = request_id
        return response

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
