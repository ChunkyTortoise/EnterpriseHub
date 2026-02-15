from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from uuid import uuid4

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from .dependencies import AuthMisconfiguredError, DemoAuthError
from .models import ApiErrorDetail, ApiErrorResponse, HealthResponse
from .routers import admin as admin_router
from .routers import ghl as ghl_router
from .routers import language as language_router
from .routers import portal as portal_router
from .routers import root as root_router
from .routers import vapi as vapi_router

load_dotenv()
REQUEST_ID_HEADER = "X-Request-ID"
IDEMPOTENCY_KEY_HEADER = "Idempotency-Key"
IDEMPOTENCY_REPLAYED_HEADER = "X-Idempotency-Replayed"
IDEMPOTENCY_STORE_MAX_ENTRIES = 512
IDEMPOTENT_MUTATION_ROUTES = {
    ("POST", "/portal/swipe"),
    ("POST", "/vapi/tools/book-tour"),
    ("POST", "/ghl/sync"),
    ("POST", "/system/reset"),
    ("POST", "/admin/reset"),
    ("POST", "/reset"),
}
NO_BODY_IDEMPOTENCY_ROUTES = {
    ("POST", "/ghl/sync"),
    ("POST", "/system/reset"),
    ("POST", "/admin/reset"),
    ("POST", "/reset"),
}
request_logger = logging.getLogger("portal_api.request")


@dataclass(frozen=True)
class IdempotencyRecord:
    request_hash: str
    status_code: int
    body: bytes
    headers: dict[str, str]
    media_type: str | None


class IdempotencyStore:
    def __init__(self, max_entries: int = IDEMPOTENCY_STORE_MAX_ENTRIES) -> None:
        self._max_entries = max_entries
        self._records: OrderedDict[tuple[str, str, str], IdempotencyRecord] = OrderedDict()
        self._lock = threading.Lock()

    def lookup(
        self, method: str, path: str, idempotency_key: str, request_hash: str
    ) -> tuple[IdempotencyRecord | None, bool]:
        key = (method, path, idempotency_key)
        with self._lock:
            existing = self._records.get(key)
            if existing is None:
                return None, False
            self._records.move_to_end(key)
            if existing.request_hash != request_hash:
                return None, True
            return existing, False

    def save(
        self,
        method: str,
        path: str,
        idempotency_key: str,
        request_hash: str,
        status_code: int,
        body: bytes,
        headers: dict[str, str],
        media_type: str | None,
    ) -> None:
        key = (method, path, idempotency_key)
        with self._lock:
            self._records[key] = IdempotencyRecord(
                request_hash=request_hash,
                status_code=status_code,
                body=body,
                headers=headers,
                media_type=media_type,
            )
            self._records.move_to_end(key)
            while len(self._records) > self._max_entries:
                self._records.popitem(last=False)

    def clear(self) -> None:
        with self._lock:
            self._records.clear()


idempotency_store = IdempotencyStore()


def reset_idempotency_store() -> None:
    idempotency_store.clear()


def _build_api_error_response(status_code: int, code: str, message: str, request_id: str | None) -> JSONResponse:
    payload = ApiErrorResponse(error=ApiErrorDetail(code=code, message=message, request_id=request_id)).model_dump()
    response = JSONResponse(status_code=status_code, content=payload)
    if request_id:
        response.headers[REQUEST_ID_HEADER] = request_id
    return response


async def _request_body_hash(request: Request, route_key: tuple[str, str]) -> str:
    if route_key in NO_BODY_IDEMPOTENCY_ROUTES:
        normalized_body = b""
    else:
        raw_body = await request.body()
        if not raw_body:
            normalized_body = b""
        else:
            try:
                parsed = json.loads(raw_body)
            except json.JSONDecodeError:
                normalized_body = raw_body
            else:
                normalized_body = json.dumps(parsed, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode(
                    "utf-8"
                )
    return hashlib.sha256(normalized_body).hexdigest()


async def _capture_response(response: Response) -> tuple[bytes, dict[str, str], Response]:
    raw_body = getattr(response, "body", None)
    if raw_body is None:
        body = b""
        async for chunk in response.body_iterator:
            body += chunk
    else:
        body = bytes(raw_body)

    headers = {key: value for key, value in response.headers.items() if key.lower() != "content-length"}
    cloned = Response(
        content=body,
        status_code=response.status_code,
        headers=headers,
        media_type=response.media_type,
        background=response.background,
    )
    return body, headers, cloned


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
    async def idempotency_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        route_key = (request.method.upper(), request.url.path)
        if route_key not in IDEMPOTENT_MUTATION_ROUTES:
            return await call_next(request)

        idempotency_key = request.headers.get(IDEMPOTENCY_KEY_HEADER)
        if not idempotency_key:
            return await call_next(request)

        request_hash = await _request_body_hash(request, route_key)
        replay_record, conflict = idempotency_store.lookup(
            method=route_key[0],
            path=route_key[1],
            idempotency_key=idempotency_key,
            request_hash=request_hash,
        )
        request_id = getattr(request.state, "request_id", None)
        if conflict:
            request_logger.warning(
                "portal_api.idempotency_conflict method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            return _build_api_error_response(
                status_code=409,
                code="idempotency_conflict",
                message="Idempotency key reused with different request payload",
                request_id=request_id,
            )

        if replay_record is not None:
            replay_headers = dict(replay_record.headers)
            replay_headers[IDEMPOTENCY_REPLAYED_HEADER] = "true"
            request_logger.info(
                "portal_api.idempotency_replay method=%s path=%s request_id=%s",
                request.method,
                request.url.path,
                request_id,
            )
            return Response(
                content=replay_record.body,
                status_code=replay_record.status_code,
                headers=replay_headers,
                media_type=replay_record.media_type,
            )

        response = await call_next(request)
        body, headers, cloned_response = await _capture_response(response)
        idempotency_store.save(
            method=route_key[0],
            path=route_key[1],
            idempotency_key=idempotency_key,
            request_hash=request_hash,
            status_code=response.status_code,
            body=body,
            headers=headers,
            media_type=response.media_type,
        )
        return cloned_response

    @app.middleware("http")
    async def request_id_middleware(request: Request, call_next):  # type: ignore[no-untyped-def]
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            duration_ms = (time.perf_counter() - start) * 1000
            request_logger.exception(
                "portal_api.request_failed method=%s path=%s request_id=%s duration_ms=%.2f",
                request.method,
                request.url.path,
                request_id,
                duration_ms,
            )
            raise

        response.headers[REQUEST_ID_HEADER] = request_id
        duration_ms = (time.perf_counter() - start) * 1000
        request_logger.info(
            "portal_api.request_completed method=%s path=%s status=%s request_id=%s duration_ms=%.2f",
            request.method,
            request.url.path,
            response.status_code,
            request_id,
            duration_ms,
        )
        return response

    @app.exception_handler(DemoAuthError)
    async def demo_auth_exception_handler(request: Request, exc: DemoAuthError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        response = _build_api_error_response(
            status_code=401,
            code="unauthorized",
            message=str(exc),
            request_id=request_id,
        )
        request_logger.warning(
            "portal_api.auth_failed path=%s request_id=%s",
            request.url.path,
            request_id,
        )
        return response

    @app.exception_handler(AuthMisconfiguredError)
    async def auth_misconfigured_exception_handler(request: Request, exc: AuthMisconfiguredError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        response = _build_api_error_response(
            status_code=500,
            code="auth_misconfigured",
            message=str(exc),
            request_id=request_id,
        )
        request_logger.error(
            "portal_api.auth_misconfigured path=%s request_id=%s",
            request.url.path,
            request_id,
        )
        return response

    app.include_router(root_router.router)
    app.include_router(vapi_router.router)
    app.include_router(portal_router.router)
    app.include_router(ghl_router.router)
    app.include_router(admin_router.router)
    app.include_router(language_router.router)

    @app.get("/health", response_model=HealthResponse)
    async def health() -> HealthResponse:
        return HealthResponse(status="ok", service="portal-api")

    return app


app = create_app()
