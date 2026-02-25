"""
Minimal production entrypoint for Render deployment.

Only loads what Jorge bots need:
  - /api/health/live  — Render health check
  - /api/ghl/*        — GHL webhook handler (all 3 Jorge bots)

Intentionally skips: mobile, AR, enterprise SSO, analytics dashboard,
billing portal, Socket.IO — none needed for bot operation.
"""

from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from ghl_real_estate_ai.api import health
from ghl_real_estate_ai.api.routes import webhook


class SafeJSONResponse(JSONResponse):
    """JSON response with belt-and-suspenders control-character escaping.

    Ensures Pydantic models are serialized via model_dump() before json.dumps,
    then replaces any bare LF/CR bytes that survive in the output.
    """

    def render(self, content: Any) -> bytes:
        if hasattr(content, "model_dump"):
            content = content.model_dump()
        result = super().render(content)
        # Escape bare control characters that must not appear unescaped in JSON
        return result.replace(b"\x0a", b"\\n").replace(b"\x0d", b"\\r")


class JSONSanitizeASGIMiddleware:
    """Pure ASGI middleware: escapes bare LF/CR bytes in JSON response bodies.

    Operates at the raw ASGI protocol level (http.response.body messages),
    bypassing BaseHTTPMiddleware's body_iterator streaming issues entirely.

    Replaces 0x0a → \\n and 0x0d → \\r so any multi-line response text
    is always JSON-safe, regardless of which code path assembled it.
    """

    def __init__(self, app: Any) -> None:
        self.app = app

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        is_json = False

        async def send_wrapper(message: Any) -> None:
            nonlocal is_json

            if message["type"] == "http.response.start":
                # Detect JSON content-type from response headers
                headers = dict(message.get("headers", []))
                ct = headers.get(b"content-type", b"").decode("utf-8", errors="ignore")
                is_json = "application/json" in ct
                await send(message)

            elif message["type"] == "http.response.body" and is_json:
                body = message.get("body", b"")
                if isinstance(body, str):
                    body = body.encode("utf-8")
                sanitized = body.replace(b"\x0a", b"\\n").replace(b"\x0d", b"\\r")
                await send({**message, "body": sanitized})

            else:
                await send(message)

        await self.app(scope, receive, send_wrapper)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Jorge Bot Server",
    version="1.0.67",
    lifespan=lifespan,
    default_response_class=SafeJSONResponse,
)

# Add CORS first (inner), then sanitize middleware (outer).
# Starlette stacks middlewares in reverse-add order: last-added = outermost.
# JSONSanitizeASGIMiddleware (outer) sees the response AFTER CORSMiddleware
# has already added its headers, so CORS headers are preserved.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
# Pure ASGI middleware: reliable alternative to BaseHTTPMiddleware for body sanitization.
# Works by intercepting http.response.body ASGI messages directly.
app.add_middleware(JSONSanitizeASGIMiddleware)

# Render health check: GET /api/health/live → 200
app.include_router(health.router, prefix="/api")

# GHL webhook: POST /api/ghl/webhook → bot logic
app.include_router(webhook.router, prefix="/api")

# Bot smoke-test endpoints — no auth, no DB, no GHL creds needed
# POST /test/seller  POST /test/buyer  DELETE /test/session/{id}  GET /test/sessions
from ghl_real_estate_ai.api.routes.test_bots import router as test_bots_router

app.include_router(test_bots_router)
