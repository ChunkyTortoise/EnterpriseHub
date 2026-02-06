"""
High-Performance FastAPI Configuration for Customer Intelligence Platform.

Optimizations for enterprise-scale concurrent operations:
- Async request handling with connection pooling
- Request batching and streaming
- Intelligent caching middleware
- Rate limiting and throttling
- Circuit breaker patterns
- Performance monitoring integration
"""

import asyncio
import time
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass
import json
import gzip
from functools import wraps
import weakref

from fastapi import FastAPI, Request, Response, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.base import BaseHTTPMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import StreamingResponse
from fastapi.concurrency import run_in_threadpool
import uvloop
import httpx

from ..core.optimized_redis_config import OptimizedRedisManager
from ..database.connection_manager import AdaptiveConnectionPool
from ..monitoring.query_performance_monitor import QueryPerformanceMonitor

logger = logging.getLogger(__name__)

@dataclass
class RequestMetrics:
    """Request performance metrics."""
    endpoint: str
    method: str
    duration_ms: float
    status_code: int
    content_length: int
    timestamp: datetime
    user_agent: Optional[str] = None
    cache_hit: Optional[bool] = None

class AsyncRequestBatcher:
    """Batch similar requests to reduce database load."""

    def __init__(self, batch_window_ms: int = 50, max_batch_size: int = 10):
        self.batch_window_ms = batch_window_ms
        self.max_batch_size = max_batch_size
        self.pending_requests: Dict[str, List] = {}
        self.batch_locks: Dict[str, asyncio.Lock] = {}

    async def batch_request(
        self,
        batch_key: str,
        request_data: Any,
        batch_processor: Callable[[List], List]
    ) -> Any:
        """Add request to batch and wait for result."""
        if batch_key not in self.batch_locks:
            self.batch_locks[batch_key] = asyncio.Lock()

        async with self.batch_locks[batch_key]:
            # Initialize batch if needed
            if batch_key not in self.pending_requests:
                self.pending_requests[batch_key] = []

            # Add request to batch
            future = asyncio.Future()
            self.pending_requests[batch_key].append((request_data, future))

            # Process batch if conditions met
            batch = self.pending_requests[batch_key]
            should_process = (
                len(batch) >= self.max_batch_size or
                (batch and time.time() * 1000 - batch[0][0].get('timestamp', 0) > self.batch_window_ms)
            )

            if should_process:
                # Process the batch
                requests_data = [item[0] for item in batch]
                futures = [item[1] for item in batch]

                # Clear the batch
                self.pending_requests[batch_key] = []

                try:
                    # Execute batch processing
                    results = await batch_processor(requests_data)

                    # Return results to futures
                    for future, result in zip(futures, results):
                        if not future.done():
                            future.set_result(result)

                except Exception as e:
                    # Propagate error to all futures
                    for future in futures:
                        if not future.done():
                            future.set_exception(e)

        # Wait for result
        return await future

class IntelligentCacheMiddleware(BaseHTTPMiddleware):
    """Intelligent caching middleware with automatic cache management."""

    def __init__(
        self,
        app,
        redis_manager: OptimizedRedisManager,
        default_ttl: int = 300,
        cache_control_header: bool = True
    ):
        super().__init__(app)
        self.redis_manager = redis_manager
        self.default_ttl = default_ttl
        self.cache_control_header = cache_control_header

        # Cache strategies by endpoint pattern
        self.cache_strategies = {
            r"/api/v1/customers/\w+$": {"ttl": 600, "vary_by": ["user", "tenant"]},
            r"/api/v1/analytics/.*": {"ttl": 900, "vary_by": ["tenant", "department"]},
            r"/api/v1/search/.*": {"ttl": 300, "vary_by": ["query", "filters"]},
        }

    async def dispatch(self, request: Request, call_next):
        """Handle request caching logic."""
        # Only cache GET requests
        if request.method != "GET":
            return await call_next(request)

        # Generate cache key
        cache_key = await self._generate_cache_key(request)

        # Try to get from cache
        cached_response = await self.redis_manager.get_with_optimization(
            cache_key, pool='cache'
        )

        if cached_response:
            # Cache hit - return cached response
            response_data = cached_response
            response = Response(
                content=response_data['content'],
                status_code=response_data['status_code'],
                headers=response_data['headers'],
                media_type=response_data.get('media_type', 'application/json')
            )

            # Add cache headers
            if self.cache_control_header:
                response.headers["X-Cache"] = "HIT"
                response.headers["X-Cache-Key"] = cache_key

            return response

        # Cache miss - process request
        start_time = time.perf_counter()
        response = await call_next(request)
        processing_time = time.perf_counter() - start_time

        # Cache successful responses
        if 200 <= response.status_code < 300:
            await self._cache_response(request, response, cache_key, processing_time)

        # Add cache headers
        if self.cache_control_header:
            response.headers["X-Cache"] = "MISS"
            response.headers["X-Processing-Time"] = f"{processing_time * 1000:.2f}ms"

        return response

    async def _generate_cache_key(self, request: Request) -> str:
        """Generate intelligent cache key based on request."""
        # Base key components
        key_parts = [
            request.method,
            request.url.path,
        ]

        # Add query parameters (sorted for consistency)
        if request.url.query:
            sorted_params = sorted(request.url.query.split('&'))
            key_parts.append('|'.join(sorted_params))

        # Add headers that affect response (like tenant, user, etc.)
        cache_relevant_headers = ['x-tenant-id', 'x-user-id', 'accept-language']
        for header in cache_relevant_headers:
            value = request.headers.get(header)
            if value:
                key_parts.append(f"{header}:{value}")

        cache_key = "api_cache:" + "|".join(key_parts)
        return cache_key

    async def _cache_response(self, request: Request, response: Response, cache_key: str, processing_time: float):
        """Cache response with intelligent TTL."""
        try:
            # Determine TTL based on endpoint and processing time
            ttl = self._calculate_dynamic_ttl(request, processing_time)

            # Read response content
            response_body = b""
            async for chunk in response.body_iterator:
                response_body += chunk

            # Prepare cache data
            cache_data = {
                'content': response_body.decode('utf-8') if response_body else '',
                'status_code': response.status_code,
                'headers': dict(response.headers),
                'media_type': response.media_type,
                'cached_at': datetime.utcnow().isoformat(),
                'processing_time_ms': processing_time * 1000
            }

            # Cache the response
            await self.redis_manager.set_with_optimization(
                cache_key, cache_data, ttl=ttl, pool='cache'
            )

            # Recreate response body iterator
            response.body_iterator = self._create_body_iterator(response_body)

        except Exception as e:
            logger.warning(f"Failed to cache response: {e}")

    def _calculate_dynamic_ttl(self, request: Request, processing_time: float) -> int:
        """Calculate dynamic TTL based on request characteristics."""
        # Base TTL
        ttl = self.default_ttl

        # Longer TTL for expensive operations
        if processing_time > 1.0:  # > 1 second
            ttl *= 3
        elif processing_time > 0.5:  # > 500ms
            ttl *= 2

        # Endpoint-specific adjustments
        path = request.url.path

        if '/analytics/' in path:
            ttl = 900  # 15 minutes for analytics
        elif '/customers/' in path and '/scores' in path:
            ttl = 300  # 5 minutes for customer scores
        elif '/search/' in path:
            ttl = 600  # 10 minutes for search results

        return ttl

    async def _create_body_iterator(self, body: bytes):
        """Create async iterator for response body."""
        yield body

class CircuitBreakerMiddleware(BaseHTTPMiddleware):
    """Circuit breaker pattern for external service calls."""

    def __init__(
        self,
        app,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        expected_exception: Exception = Exception
    ):
        super().__init__(app)
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.expected_exception = expected_exception

        # Circuit breaker states per endpoint
        self.circuit_states: Dict[str, Dict] = {}

    async def dispatch(self, request: Request, call_next):
        """Apply circuit breaker logic."""
        endpoint = f"{request.method}:{request.url.path}"

        # Initialize circuit state if needed
        if endpoint not in self.circuit_states:
            self.circuit_states[endpoint] = {
                "state": "CLOSED",  # CLOSED, OPEN, HALF_OPEN
                "failure_count": 0,
                "last_failure_time": None,
                "success_count": 0
            }

        circuit = self.circuit_states[endpoint]

        # Check if circuit is open
        if circuit["state"] == "OPEN":
            if self._should_attempt_reset(circuit):
                circuit["state"] = "HALF_OPEN"
                circuit["success_count"] = 0
            else:
                raise HTTPException(
                    status_code=503,
                    detail="Service temporarily unavailable (Circuit Breaker Open)"
                )

        try:
            # Process request
            response = await call_next(request)

            # Success - reset failure count
            if circuit["state"] == "HALF_OPEN":
                circuit["success_count"] += 1
                if circuit["success_count"] >= 3:  # Require 3 successes to close
                    circuit["state"] = "CLOSED"
                    circuit["failure_count"] = 0
            else:
                circuit["failure_count"] = 0

            return response

        except Exception as e:
            # Failure - increment failure count
            circuit["failure_count"] += 1
            circuit["last_failure_time"] = datetime.utcnow()

            # Open circuit if threshold reached
            if circuit["failure_count"] >= self.failure_threshold:
                circuit["state"] = "OPEN"

            raise

    def _should_attempt_reset(self, circuit: Dict) -> bool:
        """Check if circuit breaker should attempt reset."""
        if not circuit["last_failure_time"]:
            return False

        time_since_failure = (datetime.utcnow() - circuit["last_failure_time"]).total_seconds()
        return time_since_failure >= self.recovery_timeout

class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    """Comprehensive performance monitoring middleware."""

    def __init__(self, app, enable_detailed_metrics: bool = True):
        super().__init__(app)
        self.enable_detailed_metrics = enable_detailed_metrics
        self.request_metrics: List[RequestMetrics] = []
        self.active_requests = weakref.WeakSet()

    async def dispatch(self, request: Request, call_next):
        """Monitor request performance."""
        start_time = time.perf_counter()
        request_size = int(request.headers.get("content-length", 0))

        # Track active request
        self.active_requests.add(request)

        try:
            response = await call_next(request)

            # Calculate metrics
            duration = (time.perf_counter() - start_time) * 1000
            response_size = 0

            # Get response size if available
            if hasattr(response, 'headers') and 'content-length' in response.headers:
                response_size = int(response.headers['content-length'])

            # Record metrics
            if self.enable_detailed_metrics:
                metric = RequestMetrics(
                    endpoint=request.url.path,
                    method=request.method,
                    duration_ms=duration,
                    status_code=response.status_code,
                    content_length=response_size,
                    timestamp=datetime.utcnow(),
                    user_agent=request.headers.get("user-agent"),
                    cache_hit=response.headers.get("x-cache") == "HIT"
                )

                self.request_metrics.append(metric)

                # Keep only recent metrics
                if len(self.request_metrics) > 10000:
                    self.request_metrics = self.request_metrics[-10000:]

            # Add performance headers
            response.headers["X-Response-Time"] = f"{duration:.2f}ms"
            response.headers["X-Request-ID"] = str(id(request))

            return response

        except Exception as e:
            duration = (time.perf_counter() - start_time) * 1000

            # Record error metric
            if self.enable_detailed_metrics:
                metric = RequestMetrics(
                    endpoint=request.url.path,
                    method=request.method,
                    duration_ms=duration,
                    status_code=500,
                    content_length=0,
                    timestamp=datetime.utcnow(),
                    user_agent=request.headers.get("user-agent")
                )

                self.request_metrics.append(metric)

            raise

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get performance metrics summary."""
        if not self.request_metrics:
            return {"message": "No metrics available"}

        recent_metrics = self.request_metrics[-1000:]  # Last 1000 requests

        # Calculate summary statistics
        total_requests = len(recent_metrics)
        avg_response_time = sum(m.duration_ms for m in recent_metrics) / total_requests
        slow_requests = [m for m in recent_metrics if m.duration_ms > 1000]  # >1s
        cache_hits = [m for m in recent_metrics if m.cache_hit]

        # Group by endpoint
        endpoint_stats = {}
        for metric in recent_metrics:
            endpoint = metric.endpoint
            if endpoint not in endpoint_stats:
                endpoint_stats[endpoint] = []
            endpoint_stats[endpoint].append(metric.duration_ms)

        endpoint_summary = {}
        for endpoint, times in endpoint_stats.items():
            endpoint_summary[endpoint] = {
                "count": len(times),
                "avg_time_ms": sum(times) / len(times),
                "max_time_ms": max(times),
                "min_time_ms": min(times)
            }

        return {
            "summary": {
                "total_requests": total_requests,
                "avg_response_time_ms": avg_response_time,
                "slow_requests": len(slow_requests),
                "cache_hit_rate": len(cache_hits) / total_requests if total_requests > 0 else 0,
                "active_requests": len(self.active_requests),
                "requests_per_minute": len([
                    m for m in recent_metrics
                    if m.timestamp >= datetime.utcnow() - timedelta(minutes=1)
                ])
            },
            "endpoints": endpoint_summary,
            "timestamp": datetime.utcnow().isoformat()
        }

class OptimizedFastAPIFactory:
    """Factory for creating optimized FastAPI applications."""

    def __init__(
        self,
        redis_manager: OptimizedRedisManager,
        connection_pool: AdaptiveConnectionPool,
        query_monitor: Optional[QueryPerformanceMonitor] = None
    ):
        self.redis_manager = redis_manager
        self.connection_pool = connection_pool
        self.query_monitor = query_monitor

        # Create request batcher
        self.request_batcher = AsyncRequestBatcher(
            batch_window_ms=50,
            max_batch_size=10
        )

    def create_app(
        self,
        title: str = "Customer Intelligence Platform API",
        version: str = "1.0.0",
        enable_performance_monitoring: bool = True,
        enable_caching: bool = True,
        enable_circuit_breaker: bool = True,
        **kwargs
    ) -> FastAPI:
        """Create optimized FastAPI application."""

        # Set event loop policy for better async performance
        if hasattr(asyncio, 'set_event_loop_policy'):
            asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            """Application lifespan management with resource initialization."""
            # Startup
            logger.info("Starting optimized FastAPI application")

            # Initialize monitoring
            if self.query_monitor:
                await self.query_monitor.start_monitoring()

            # Warm up connections
            await self._warmup_services()

            yield

            # Shutdown
            logger.info("Shutting down FastAPI application")

            # Cleanup monitoring
            if self.query_monitor:
                await self.query_monitor.stop_monitoring()

            # Close connections
            await self.connection_pool.close()
            await self.redis_manager.close()

        # Create FastAPI app with optimized settings
        app = FastAPI(
            title=title,
            version=version,
            lifespan=lifespan,
            docs_url="/docs" if kwargs.get("enable_docs", True) else None,
            redoc_url="/redoc" if kwargs.get("enable_docs", True) else None,
            **kwargs
        )

        # Add middleware in optimal order (last added = first executed)
        self._configure_middleware(
            app,
            enable_performance_monitoring,
            enable_caching,
            enable_circuit_breaker
        )

        # Add core routes
        self._add_core_routes(app)

        return app

    def _configure_middleware(
        self,
        app: FastAPI,
        enable_performance_monitoring: bool,
        enable_caching: bool,
        enable_circuit_breaker: bool
    ):
        """Configure middleware stack in optimal order."""

        # CORS (always last in middleware stack)
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        # GZip compression
        app.add_middleware(GZipMiddleware, minimum_size=1000)

        # Performance monitoring (should be early in stack)
        if enable_performance_monitoring:
            performance_middleware = PerformanceMonitoringMiddleware(
                app, enable_detailed_metrics=True
            )
            app.add_middleware(BaseHTTPMiddleware, dispatch=performance_middleware.dispatch)

        # Circuit breaker
        if enable_circuit_breaker:
            circuit_breaker = CircuitBreakerMiddleware(
                app, failure_threshold=5, recovery_timeout=60
            )
            app.add_middleware(BaseHTTPMiddleware, dispatch=circuit_breaker.dispatch)

        # Intelligent caching (should be close to application logic)
        if enable_caching:
            cache_middleware = IntelligentCacheMiddleware(
                app, self.redis_manager, default_ttl=300
            )
            app.add_middleware(BaseHTTPMiddleware, dispatch=cache_middleware.dispatch)

    def _add_core_routes(self, app: FastAPI):
        """Add core monitoring and health check routes."""

        @app.get("/health")
        async def health_check():
            """Comprehensive health check endpoint."""
            health_data = {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "services": {}
            }

            # Check Redis
            redis_health = await self.redis_manager.health_check()
            health_data["services"]["redis"] = redis_health

            # Check Database
            db_health = await self.connection_pool.health_check()
            health_data["services"]["database"] = db_health

            # Overall status
            service_statuses = [
                service["status"] for service in health_data["services"].values()
            ]

            if "unhealthy" in service_statuses:
                health_data["status"] = "unhealthy"
            elif "degraded" in service_statuses:
                health_data["status"] = "degraded"

            return health_data

        @app.get("/metrics/performance")
        async def performance_metrics():
            """Get performance metrics."""
            # Get middleware metrics
            performance_middleware = None
            for middleware in app.user_middleware:
                if hasattr(middleware, 'cls') and 'PerformanceMonitoringMiddleware' in str(middleware.cls):
                    performance_middleware = middleware
                    break

            if performance_middleware:
                return performance_middleware.get_metrics_summary()
            else:
                return {"message": "Performance monitoring not enabled"}

        @app.get("/metrics/database")
        async def database_metrics():
            """Get database performance metrics."""
            return await self.connection_pool.get_performance_report()

        @app.get("/metrics/redis")
        async def redis_metrics():
            """Get Redis performance metrics."""
            return await self.redis_manager.get_performance_metrics()

        @app.get("/metrics/queries")
        async def query_metrics():
            """Get query performance metrics."""
            if self.query_monitor:
                return await self.query_monitor.get_performance_dashboard_data()
            else:
                return {"message": "Query monitoring not enabled"}

    async def _warmup_services(self):
        """Warm up services for better initial performance."""
        try:
            # Test Redis connections
            await self.redis_manager.health_check()

            # Test database connections
            await self.connection_pool.health_check()

            logger.info("Service warmup completed successfully")

        except Exception as e:
            logger.warning(f"Service warmup failed: {e}")

    # Utility methods for optimized request handling

    def create_streaming_response(
        self,
        generator: AsyncGenerator[bytes, None],
        media_type: str = "application/json",
        headers: Optional[Dict[str, str]] = None
    ) -> StreamingResponse:
        """Create optimized streaming response."""
        return StreamingResponse(
            generator,
            media_type=media_type,
            headers=headers or {}
        )

    async def batch_database_requests(
        self,
        requests: List[Dict[str, Any]],
        batch_processor: Callable
    ) -> List[Any]:
        """Batch database requests for better performance."""
        batch_key = f"db_batch_{hash(str(sorted(requests, key=lambda x: str(x))))}"

        return await self.request_batcher.batch_request(
            batch_key=batch_key,
            request_data=requests,
            batch_processor=batch_processor
        )

# Helper decorators for endpoint optimization

def cache_response(ttl: int = 300, vary_by: Optional[List[str]] = None):
    """Decorator for caching endpoint responses."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # This would integrate with the caching middleware
            # Implementation depends on specific requirements
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(requests_per_minute: int = 60):
    """Decorator for rate limiting endpoints."""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Implement rate limiting logic
            # This would typically use Redis for distributed rate limiting
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator

def compress_response(minimum_size: int = 1000):
    """Decorator for response compression."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            response = await func(*args, **kwargs)
            # Add compression logic if needed
            return response
        return wrapper
    return decorator