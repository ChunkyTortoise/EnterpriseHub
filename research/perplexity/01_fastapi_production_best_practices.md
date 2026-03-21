# FastAPI Production Best Practices 2025-2026

**Research date**: 2026-03-19
**Context**: EnterpriseHub — 555 service files, 86 route files, module-level singleton instantiation, no DI framework, god-class route files (max 2,715 lines), no structured lifespan management.

---

## Key Findings

The FastAPI ecosystem has converged on a set of production patterns that directly address every structural problem present in EnterpriseHub:

1. **Lifespan context managers** (not `@app.on_event`) are the current standard for managing shared resources. Module-level instantiation is the primary documented anti-pattern for async applications.
2. **Domain-driven directory structure** is universally recommended over file-type grouping. Files exceeding ~300 lines are a signal of missing domain decomposition.
3. **Dependency injection via `Depends()`** eliminates singletons and makes resources testable. Third-party DI frameworks (Dependency Injector, Lagom) are recommended for apps at EnterpriseHub's scale.
4. **Gunicorn + Uvicorn workers** remains the production standard. Worker count = `(2 × CPU cores) + 1` with `max_requests` recycling to prevent memory leaks.
5. **OpenTelemetry** via `FastAPIInstrumentor` is the standard observability approach, initialized in the lifespan handler to survive Gunicorn fork semantics.

---

## Middleware Patterns

### Ordering is Execution Order

Middleware executes in the order it is registered. The recommended ordering is:

1. **Security headers** — must execute first on every request
2. **Request ID / correlation ID** — generates `X-Request-ID` for distributed tracing before any logging occurs
3. **Structured request logging** — logs method, path, status, and duration using the request ID
4. **CORS** — `CORSMiddleware` with explicit origins only (never `allow_origins=["*"]` in production; this disables credential support)
5. **Authentication / rate limiting** — downstream of logging so auth failures are captured
6. **Compression** (`GZipMiddleware`) — applied last, closest to the response

### CORS Configuration

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # explicit list, never ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    max_age=3600,  # cache preflight for 1 hour
)
```

### Request ID Middleware

Every incoming request should receive a `X-Request-ID` UUID (or propagate one from upstream). Store it in `request.state.request_id` so it flows through all downstream logging, exception handlers, and outbound HTTP calls. Return it in response headers so clients can correlate errors with support tickets.

### Security Headers Middleware

Add via middleware rather than per-route decorators:

- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`

### Structured Logging Middleware

Log at request entry and exit. Entry log: method, path, client IP, request ID. Exit log: status code, duration in milliseconds, request ID. Use a structured logger (e.g., `structlog` or `python-json-logger`) so fields are machine-parseable in log aggregation systems (Datadog, CloudWatch, Loki).

---

## Dependency Injection

### The Core Problem: Module-Level Singletons

Module-level instantiation (e.g., `db = Database()` at import time) is the primary documented anti-pattern for async FastAPI applications. It causes three distinct failure modes:

1. **Blocks the event loop** before the lifespan handler has run, meaning async setup (connection pools, async HTTP clients) cannot be awaited.
2. **Makes testing impossible** without monkey-patching or import tricks.
3. **Couples all code** to a specific implementation, preventing configuration changes per environment.

### The Replacement Pattern: `Depends()` + `app.state`

```python
# lifespan.py
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize all shared resources
    app.state.db_pool = await create_async_engine(settings.DATABASE_URL, ...)
    app.state.redis = await aioredis.from_url(settings.REDIS_URL)
    app.state.http_client = httpx.AsyncClient()
    yield
    # Shutdown: clean up in reverse order
    await app.state.http_client.aclose()
    await app.state.redis.close()
    await app.state.db_pool.dispose()

# dependencies.py
async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(request.app.state.db_pool) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

# route.py
@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ...
```

### Request-Scoped vs App-Scoped Dependencies

| Scope | Mechanism | Use Case |
|-------|-----------|----------|
| App-scoped | `app.state` (set in lifespan) | DB pools, Redis clients, HTTP clients, ML models |
| Request-scoped | `Depends()` with `yield` | DB sessions, auth context, per-request caches |
| Cached per-request | `Depends(use_cache=True)` (default) | JWT parsing, user lookup — called once even if multiple routes depend on it |

### Dependency Caching

FastAPI caches dependency results within a single request by default. A dependency like `get_current_user` that is consumed by three other dependencies is called only once per request. This eliminates redundant database lookups without any manual caching.

### Router-Level Dependencies

Apply shared dependencies (authentication, role checking) at the router level rather than repeating them on every endpoint:

```python
protected_router = APIRouter(
    prefix="/api/v1",
    dependencies=[Depends(require_authenticated_user)],
)
```

### At Scale: Third-Party DI Frameworks

For codebases with 500+ service files, consider `dependency-injector` or `lagom`:

- Declarative container definitions replace ad-hoc wiring
- Wire containers to FastAPI's `Depends()` via adapters
- Supports overriding dependencies per-environment without import hacks
- Enables constructor injection for service classes rather than function-level `Depends()`

---

## Async Patterns

### Lifespan Context Manager (Current Standard)

The `@app.on_event("startup")` and `@app.on_event("shutdown")` decorators are deprecated. The `lifespan` parameter with `@asynccontextmanager` is the current standard (FastAPI 0.95.0+):

```python
app = FastAPI(lifespan=lifespan)
```

Everything before `yield` in the lifespan handler is startup. Everything after is shutdown. This collocation makes the relationship between resource acquisition and release explicit and auditable.

### Async vs Sync Route Handlers

FastAPI runs sync route handlers in a threadpool automatically, but with important caveats:

- **Async routes** (`async def`): Must only call non-blocking I/O. A single `time.sleep()` or synchronous database call blocks the entire event loop for all concurrent requests.
- **Sync routes** (`def`): FastAPI runs them in `asyncio`'s default threadpool. Use for CPU-bound operations (JWT parsing, data transformations, image processing).
- **CPU-heavy tasks**: Use worker processes (Celery, ARQ, multiprocessing). The GIL prevents effective parallelism on threads; CPU work kills async throughput.

### Background Tasks

Use `BackgroundTasks` (built-in) for lightweight post-response work (sending emails, audit logging). Use ARQ or Celery for durable, retriable, or long-running tasks. Never block a response for work that can be deferred.

### Connection Pooling (Async SQLAlchemy 2.0)

```python
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,          # base connections kept alive
    max_overflow=20,       # burst capacity (30 total)
    pool_pre_ping=True,    # validates connection before use (catches stale connections)
    pool_recycle=3600,     # recycle connections hourly (avoids server-side timeout drops)
)
```

The `pool_pre_ping=True` parameter is critical for long-lived deployments — without it, connections idle past the database server's `wait_timeout` return errors on the next use.

### Avoiding N+1 Queries

Use SQLAlchemy's `selectinload()` and `joinedload()` for eager loading of relationships. N+1 is the single most common performance regression in ORM-backed FastAPI apps — each lazy-loaded relationship inside a loop adds one database roundtrip per row.

### Async HTTP Clients

Use `httpx.AsyncClient` (initialized in lifespan, injected via `Depends()`) rather than `requests` (sync) or creating a new client per request (expensive). A shared client reuses connection pools and TLS sessions.

---

## Error Handling

### Custom Exception Hierarchy

Define domain-specific exceptions rather than raising generic `HTTPException` everywhere:

```python
# src/users/exceptions.py
class UserNotFoundError(AppError):
    status_code = 404
    detail = "User not found"

class InsufficientPermissionsError(AppError):
    status_code = 403
    detail = "Insufficient permissions"
```

### Global Exception Handler

Register a single handler that:
1. Logs the full stack trace internally (with `request_id` for correlation)
2. Returns a sanitized, structured JSON response to the client (never expose internal stack traces)
3. Maps domain exceptions to HTTP status codes

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    logger.error("Application error", request_id=request.state.request_id, exc_info=exc)
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "request_id": request.state.request_id},
    )
```

### Validation Error Responses

FastAPI's built-in `RequestValidationError` handler returns Pydantic validation errors. Override it to enforce a consistent error envelope shape across all error types.

---

## Router Organization

### Domain-Driven Directory Structure

The universally recommended pattern for large FastAPI codebases:

```
src/
  auth/
    router.py
    schemas.py
    models.py
    service.py
    dependencies.py
    exceptions.py
    constants.py
  users/
    router.py
    schemas.py
    ...
  orders/
    ...
  shared/
    dependencies.py
    middleware.py
    exceptions.py
main.py
lifespan.py
config.py
```

**Key rules:**
- One router per domain. Never combine unrelated resources in one route file.
- Route files should contain only HTTP-level logic: parse request → call service → return response. No business logic.
- Service files contain business logic. Repository files contain data access.
- Target 200-400 lines per file maximum.

### Decomposing God-Class Route Files

A 2,715-line route file contains multiple implicit domains. Identify split points by:
1. Resource type (users vs. orders vs. payments are always separate)
2. HTTP verb groups (CRUD operations on a single resource stay together)
3. Authentication scope (public vs. authenticated vs. admin endpoints)

Each extracted router is registered with a prefix:

```python
# main.py
app.include_router(auth_router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users_router, prefix="/api/v1/users", tags=["users"])
app.include_router(orders_router, prefix="/api/v1/orders", tags=["orders"])
```

### Configuration Per Domain

Avoid a single monolithic `Settings` class. Split into domain-specific configs:

```python
# src/auth/config.py
class AuthConfig(BaseSettings):
    jwt_secret: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
```

This prevents a single God-Config that exposes unrelated settings across domains.

---

## Performance

### Connection Pooling

See Async Patterns section. The pool configuration (`pool_size=10, max_overflow=20`) supports 30 concurrent database connections, which is appropriate for 4 Gunicorn workers each handling many async requests.

### Redis Caching

Use Redis for:
- Session data and JWT token invalidation lists
- Frequently-read, rarely-written data (configuration, feature flags)
- Rate limiting counters (per-IP and per-user)
- Background task queues (ARQ)

Apply caching at the service layer, not the route layer. Cache keys should include all parameters that affect the result.

### Response Compression

Add `GZipMiddleware` for API responses above a minimum size threshold (typically 1 KB). This is especially impactful for list endpoints returning large JSON payloads.

```python
from fastapi.middleware.gzip import GZipMiddleware
app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### Dependency Caching

FastAPI's built-in dependency caching (default behavior) eliminates redundant calls within a request. A dependency called by 5 different sub-dependencies executes once per request.

### Eager Loading

Use `selectinload()` on all ORM queries that access relationships. Profile with query counters (SQLAlchemy's `echo=True` or pgBadger) to identify N+1 patterns.

### Rate Limiting

Use `slowapi` (Starlette-compatible) with a Redis backend for consistent rate limiting across multiple worker processes. Apply different limits per endpoint sensitivity:
- `100/minute` for standard read endpoints
- `10/minute` for write/mutation endpoints
- `5/minute` for auth endpoints

---

## Production Deployment

### Gunicorn + Uvicorn Workers

The production-standard process model for FastAPI:

```python
# gunicorn.conf.py
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
timeout = 120
graceful_timeout = 30
keepalive = 5
max_requests = 1000          # restart workers after N requests (prevents memory leaks)
max_requests_jitter = 50     # randomize restart to avoid thundering herd
worker_connections = 1000
```

Command: `gunicorn -c gunicorn.conf.py app.main:app`

**Why `max_requests`?** Python processes accumulate memory over time (reference cycles, library internals). Recycling workers after 1000 requests (with ±50 jitter to avoid all workers restarting simultaneously) bounds memory growth without requiring a full process restart.

### Docker Configuration

```dockerfile
FROM python:3.12-slim
WORKDIR /app
# Copy requirements first for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Non-root user for security
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
CMD ["gunicorn", "-c", "gunicorn.conf.py", "app.main:app"]
```

### Health Check Endpoints

Implement two separate endpoints with distinct semantics:

**Liveness** (`GET /health`): Returns 200 if the process is alive. Minimal — no external calls. Used by process supervisors to know when to restart a dead process.

**Readiness** (`GET /readiness`): Tests all critical dependencies (database, Redis, external APIs) with a 5-second timeout each. Returns 503 if any dependency is unhealthy. Used by load balancers to route traffic away from impaired instances.

```python
@router.get("/readiness")
async def readiness(db: AsyncSession = Depends(get_db), redis=Depends(get_redis)):
    try:
        await asyncio.wait_for(db.execute(text("SELECT 1")), timeout=5.0)
        await asyncio.wait_for(redis.ping(), timeout=5.0)
        return {"status": "ready"}
    except asyncio.TimeoutError:
        raise HTTPException(status_code=503, detail="Dependency timeout")
```

### Environment Configuration

Use Pydantic `BaseSettings` for all environment variables. Validate on startup — fail fast with a clear error rather than discovering a missing variable at runtime on the first request that needs it.

---

## OpenTelemetry Integration

### Installation

```
opentelemetry-api
opentelemetry-sdk
opentelemetry-instrumentation-fastapi
opentelemetry-exporter-otlp
opentelemetry-instrumentation-sqlalchemy
opentelemetry-instrumentation-redis
opentelemetry-instrumentation-httpx
```

### Lifespan Integration

Initialize OpenTelemetry inside the lifespan handler (before `yield`) rather than at module level. This is critical for Gunicorn deployments — the OTLP exporter uses a background thread that does not survive the fork. Initializing in the lifespan handler runs after the fork:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Configure OTel before any other resource initialization
    tracer_provider = TracerProvider(
        resource=Resource({"service.name": settings.SERVICE_NAME})
    )
    otlp_exporter = OTLPSpanExporter(endpoint=settings.OTEL_ENDPOINT)
    tracer_provider.add_span_processor(BatchSpanProcessor(otlp_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    SQLAlchemyInstrumentor().instrument(engine=engine)
    HTTPXClientInstrumentor().instrument()

    yield

    # Flush and shutdown telemetry on exit
    tracer_provider.shutdown()
```

### Key Environment Variables

| Variable | Purpose |
|----------|---------|
| `OTEL_SERVICE_NAME` | Service identifier in traces |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Backend URL (Jaeger, Tempo, Honeycomb) |
| `OTEL_TRACES_SAMPLER` | `always_on` (dev), `traceidratio` with rate (prod) |
| `OTEL_EXPORTER_OTLP_HEADERS` | API key for managed backends |
| `OTEL_METRICS_EXPORTER` | `prometheus` or `otlp` |

### Manual Spans for Business Logic

```python
tracer = trace.get_tracer(__name__)

async def process_order(order_id: int):
    with tracer.start_as_current_span("process_order") as span:
        span.set_attribute("order.id", order_id)
        # ... business logic
```

### Correlation with Request IDs

Enrich spans with the `X-Request-ID` from the request middleware so traces can be correlated with logs:

```python
span = trace.get_current_span()
span.set_attribute("http.request_id", request.state.request_id)
```

### Sampling in Production

Use `TraceIdRatioBased(0.1)` (10% sampling) in production to limit overhead. Sample 100% of error-status requests regardless of ratio by combining with `ParentBased` sampler.

---

## Recommendations for EnterpriseHub

Based on the codebase profile (555 service files, 86 route files, module-level singletons, god-class routes, no DI framework, no lifespan management), the following prioritized remediation plan is recommended:

### P0 — Stop the Bleeding (Week 1-2)

1. **Introduce `lifespan` context manager** in `main.py`. Move all module-level singleton instantiation (database engines, Redis clients, HTTP clients, ML models) into the lifespan handler. Store instances on `app.state`. This is the single highest-impact change — it fixes async event loop blocking on startup and unlocks proper resource cleanup on shutdown.

2. **Add `pool_pre_ping=True` and `pool_recycle=3600`** to all SQLAlchemy engine configurations immediately. Without these, long-lived deployments silently drop connections.

3. **Add `/health` and `/readiness` endpoints** if not present. Readiness endpoint should test DB and Redis. Wire to load balancer health checks.

### P1 — Dependency Injection (Week 3-4)

4. **Create `src/shared/dependencies.py`** with `get_db()`, `get_redis()`, `get_http_client()` — all reading from `request.app.state`. Replace all direct singleton access in route handlers with `Depends()`.

5. **Apply router-level `Depends(require_authenticated_user)`** for all protected routers. This removes repeated auth checks from individual endpoints.

6. **Evaluate `dependency-injector`** for the service layer. With 555 service files, manual wiring becomes unmanageable. A declarative container provides a single source of truth for how services are assembled.

### P2 — Router Decomposition (Week 5-8)

7. **Decompose the 2,715-line route file** first — it represents the highest concentration of risk. Identify the resource boundaries within it and extract to separate domain routers. Target: no route file exceeds 400 lines.

8. **Adopt domain-driven structure**: for each domain directory create `router.py`, `service.py`, `repository.py`, `schemas.py`, `exceptions.py`. Migrate files incrementally, domain by domain.

9. **Split monolithic `Settings`** into per-domain config classes using `BaseSettings`.

### P3 — Observability (Week 9-10)

10. **Add `structlog`** or `python-json-logger` with structured fields (request_id, user_id, duration_ms). Configure JSON output format for production log aggregation.

11. **Add `X-Request-ID` middleware** as a prerequisite to OpenTelemetry. Correlation IDs flow through logs → traces → client responses.

12. **Install OpenTelemetry instrumentation** in the lifespan handler. Start with automatic FastAPI + SQLAlchemy instrumentation. Add manual spans for business-critical code paths (payment processing, ML inference) in a second pass.

### P4 — Performance (Week 11-12)

13. **Audit all async route handlers** for blocking calls. Any `requests.get()`, `time.sleep()`, or sync ORM call inside `async def` must be converted or offloaded.

14. **Add `GZipMiddleware`** for list endpoints returning large payloads.

15. **Add `max_requests=1000` and `max_requests_jitter=50`** to Gunicorn config to bound memory growth.

16. **Profile top 10 slowest endpoints** for N+1 queries. Add `selectinload()` where relationships are accessed.

---

## Sources

- [FastAPI Best Practices — zhanymkanov/fastapi-best-practices (GitHub)](https://github.com/zhanymkanov/fastapi-best-practices)
- [FastAPI Production-Ready Patterns for 2025 — orchestrator.dev](https://orchestrator.dev/blog/2025-1-30-fastapi-production-patterns/)
- [FastAPI Production Deployment Best Practices — Render](https://render.com/articles/fastapi-production-deployment-best-practices)
- [Integrating OpenTelemetry with FastAPI — Last9](https://last9.io/blog/integrating-opentelemetry-with-fastapi/)
- [Understanding FastAPI Lifespan Events — Dev Central / TurmanSolutions](https://dev.turmansolutions.ai/2025/09/27/understanding-fastapis-lifespan-events-proper-initialization-and-shutdown/)
- [Safely Sharing FastAPI Dependencies Across Multiple Routers — Dev Central](https://dev.turmansolutions.ai/2025/09/15/safely-sharing-fastapi-dependencies-across-multiple-routers/)
- [FastAPI Lifespan Events — Official FastAPI Documentation](https://fastapi.tiangolo.com/advanced/events/)
- [Bigger Applications — Multiple Files (Official FastAPI Docs)](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [FastAPI Dependency Injection — Official FastAPI Documentation](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [The Definitive Guide to FastAPI Production Deployment with Docker (2025) — greeden.me](https://blog.greeden.me/en/2025/09/02/the-definitive-guide-to-fastapi-production-deployment-with-dockeryour-one-stop-reference-for-uvicorn-gunicorn-nginx-https-health-checks-and-observability-2025-edition/)
- [OpenTelemetry FastAPI Instrumentation — Uptrace](https://uptrace.dev/guides/opentelemetry-fastapi)
- [FastAPI OpenTelemetry Instrumentation — SigNoz](https://signoz.io/docs/instrumentation/fastapi/)
- [Python Application Servers in 2026: WSGI to ASGI — DeployHQ](https://www.deployhq.com/blog/python-application-servers-in-2025-from-wsgi-to-modern-asgi-solutions)
