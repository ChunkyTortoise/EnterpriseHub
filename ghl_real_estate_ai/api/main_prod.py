"""
Minimal production entrypoint for Render deployment.

Only loads what Jorge bots need:
  - /api/health/live  — Render health check
  - /api/ghl/*        — GHL webhook handler (all 3 Jorge bots)

Intentionally skips: mobile, AR, enterprise SSO, analytics dashboard,
billing portal, Socket.IO — none needed for bot operation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response as StarletteResponse

from ghl_real_estate_ai.api import health
from ghl_real_estate_ai.api.routes import webhook


class SafeJSONResponse(JSONResponse):
    """JSON response that guarantees Pydantic models are properly serialized.

    Fixes the literal-newline bug where FastAPI's response pipeline may pass
    a Pydantic v2 model directly to json.dumps without calling model_dump()
    first, causing control characters (e.g. the \\n in the SB 243 footer)
    to appear unescaped in the response body.
    """

    def render(self, content) -> bytes:
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        return super().render(content)


class JSONBodySanitizeMiddleware(BaseHTTPMiddleware):
    """Escape bare control characters in JSON response bodies.

    Belt-and-suspenders guard: ensures the \\n in '\\n[AI-assisted message]'
    is always JSON-encoded as \\\\n, regardless of which response class or
    code path produced the response bytes.

    Operates at the raw bytes level so it catches any code path — including
    direct Response returns or third-party serializers — that might bypass
    SafeJSONResponse.render().
    """

    async def dispatch(self, request: StarletteRequest, call_next):
        response = await call_next(request)

        content_type = response.headers.get("content-type", "")
        if "application/json" not in content_type:
            return response

        # Buffer the full response body
        chunks = []
        async for chunk in response.body_iterator:
            if isinstance(chunk, str):
                chunk = chunk.encode("utf-8")
            chunks.append(chunk)
        body = b"".join(chunks)

        # Escape bare control characters (LF, CR) that must not appear
        # unescaped inside JSON string values. Safe for compact JSON
        # (no structural newlines between tokens).
        sanitized = body.replace(b"\x0a", b"\\n").replace(b"\x0d", b"\\r")

        # Rebuild headers: drop content-length (Starlette auto-sets it from
        # the new body) and transfer-encoding (incompatible with buffered body)
        headers = {
            k: v
            for k, v in response.headers.items()
            if k.lower() not in ("content-length", "transfer-encoding")
        }

        return StarletteResponse(
            content=sanitized,
            status_code=response.status_code,
            headers=headers,
            media_type="application/json",
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Jorge Bot Server",
    version="1.0.35",
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

# Add CORS first (inner), then sanitize middleware (outer).
# Starlette stacks middlewares in reverse-add order: last-added = outermost.
# JSONBodySanitizeMiddleware (outer) sees the response AFTER CORSMiddleware
# has already added its headers, so CORS headers are preserved.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(JSONBodySanitizeMiddleware)

# Render health check: GET /api/health/live → 200
app.include_router(health.router, prefix="/api")

# GHL webhook: POST /api/ghl/webhook → bot logic
app.include_router(webhook.router, prefix="/api")
