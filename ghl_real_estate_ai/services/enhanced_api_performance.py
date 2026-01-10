"""
Enhanced API Performance Layer
=============================

Advanced API performance optimizations with connection pooling, request batching,
adaptive rate limiting, and intelligent async patterns for maximum throughput.
"""

import asyncio
import aiohttp
import time
import logging
from typing import Dict, List, Any, Optional, Union, Callable, Awaitable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import json
import hashlib
from contextlib import asynccontextmanager
import weakref

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Request priority levels for queue management"""
    CRITICAL = 1    # Real-time user requests
    HIGH = 2       # Time-sensitive operations
    NORMAL = 3     # Standard operations
    LOW = 4        # Background tasks
    BATCH = 5      # Bulk operations


class RateLimitStrategy(Enum):
    """Rate limiting strategies"""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    ADAPTIVE = "adaptive"


@dataclass
class APIEndpointConfig:
    """Configuration for API endpoint optimization"""
    base_url: str
    max_concurrent: int = 10
    rate_limit_per_second: float = 10.0
    rate_limit_strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE
    connection_timeout: int = 30
    read_timeout: int = 60
    retry_attempts: int = 3
    retry_backoff: float = 1.0
    enable_caching: bool = True
    cache_ttl: int = 300


@dataclass
class RequestMetrics:
    """Request performance metrics"""
    url: str
    method: str
    status_code: int
    response_time_ms: float
    payload_size_bytes: int
    cache_hit: bool
    timestamp: datetime
    priority: RequestPriority


@dataclass
class BatchRequest:
    """Batched request structure"""
    requests: List[Dict[str, Any]]
    callback: Callable
    priority: RequestPriority = RequestPriority.BATCH
    created_at: datetime = field(default_factory=datetime.now)


class AdaptiveRateLimiter:
    """
    Intelligent rate limiter that adapts to server response patterns
    and optimizes throughput while respecting limits.
    """

    def __init__(self,
                 initial_rate: float = 10.0,
                 strategy: RateLimitStrategy = RateLimitStrategy.ADAPTIVE):
        self.strategy = strategy
        self.current_rate = initial_rate
        self.max_rate = initial_rate * 2.0
        self.min_rate = initial_rate * 0.1

        # Token bucket for rate limiting
        self.tokens = initial_rate
        self.last_refill = time.time()

        # Adaptive learning
        self.success_streak = 0
        self.failure_streak = 0
        self.response_times: deque = deque(maxlen=100)
        self.last_adjustment = time.time()

    async def acquire_token(self, priority: RequestPriority = RequestPriority.NORMAL) -> bool:
        """Acquire a token for making a request"""
        current_time = time.time()

        if self.strategy == RateLimitStrategy.ADAPTIVE:
            return await self._adaptive_acquire(current_time, priority)
        elif self.strategy == RateLimitStrategy.TOKEN_BUCKET:
            return await self._token_bucket_acquire(current_time)
        elif self.strategy == RateLimitStrategy.SLIDING_WINDOW:
            return await self._sliding_window_acquire(current_time)
        else:
            return await self._fixed_window_acquire(current_time)

    async def _adaptive_acquire(self, current_time: float, priority: RequestPriority) -> bool:
        """Adaptive rate limiting with learning"""
        # Refill tokens
        time_passed = current_time - self.last_refill
        self.tokens = min(self.current_rate, self.tokens + (time_passed * self.current_rate))
        self.last_refill = current_time

        # Priority-based token allocation
        priority_weights = {
            RequestPriority.CRITICAL: 1.0,
            RequestPriority.HIGH: 0.8,
            RequestPriority.NORMAL: 0.6,
            RequestPriority.LOW: 0.4,
            RequestPriority.BATCH: 0.2
        }

        required_tokens = priority_weights.get(priority, 0.6)

        if self.tokens >= required_tokens:
            self.tokens -= required_tokens
            return True

        return False

    async def _token_bucket_acquire(self, current_time: float) -> bool:
        """Standard token bucket algorithm"""
        time_passed = current_time - self.last_refill
        self.tokens = min(self.current_rate, self.tokens + (time_passed * self.current_rate))
        self.last_refill = current_time

        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        return False

    async def _sliding_window_acquire(self, current_time: float) -> bool:
        """Sliding window rate limiting"""
        # Remove old response times
        cutoff = current_time - 1.0  # 1 second window
        while self.response_times and self.response_times[0] < cutoff:
            self.response_times.popleft()

        if len(self.response_times) < self.current_rate:
            self.response_times.append(current_time)
            return True

        return False

    async def _fixed_window_acquire(self, current_time: float) -> bool:
        """Fixed window rate limiting"""
        window_start = int(current_time)
        self.response_times = deque([t for t in self.response_times if t >= window_start], maxlen=100)

        if len(self.response_times) < self.current_rate:
            self.response_times.append(current_time)
            return True

        return False

    def record_response(self, success: bool, response_time: float) -> None:
        """Record response for adaptive learning"""
        current_time = time.time()
        self.response_times.append(current_time)

        if success:
            self.success_streak += 1
            self.failure_streak = 0
        else:
            self.failure_streak += 1
            self.success_streak = 0

        # Adaptive rate adjustment
        if current_time - self.last_adjustment > 10:  # Adjust every 10 seconds
            self._adjust_rate()
            self.last_adjustment = current_time

    def _adjust_rate(self) -> None:
        """Adjust rate based on success/failure patterns"""
        if self.success_streak > 20 and self.current_rate < self.max_rate:
            # Increase rate on sustained success
            self.current_rate = min(self.max_rate, self.current_rate * 1.1)
            logger.debug(f"Increased rate limit to {self.current_rate}")

        elif self.failure_streak > 5:
            # Decrease rate on failures
            self.current_rate = max(self.min_rate, self.current_rate * 0.8)
            logger.debug(f"Decreased rate limit to {self.current_rate}")

        # Reset streaks after adjustment
        self.success_streak = 0
        self.failure_streak = 0


class ConnectionPoolManager:
    """
    Advanced HTTP connection pool manager with load balancing,
    health monitoring, and automatic scaling.
    """

    def __init__(self, config: APIEndpointConfig):
        self.config = config
        self.sessions: Dict[str, aiohttp.ClientSession] = {}
        self.session_stats: Dict[str, Dict[str, Any]] = {}
        self.health_status: Dict[str, bool] = {}
        self._cleanup_task: Optional[asyncio.Task] = None

    async def initialize(self) -> None:
        """Initialize connection pools"""
        # Create session with optimized settings
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent * 2,  # Total connection pool size
            limit_per_host=self.config.max_concurrent,  # Per-host limit
            keepalive_timeout=30,
            enable_cleanup_closed=True,
            use_dns_cache=True
        )

        timeout = aiohttp.ClientTimeout(
            total=self.config.connection_timeout + self.config.read_timeout,
            connect=self.config.connection_timeout,
            sock_read=self.config.read_timeout
        )

        session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={
                'User-Agent': 'EnterpriseHub-OptimizedClient/1.0',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive'
            }
        )

        self.sessions[self.config.base_url] = session
        self.session_stats[self.config.base_url] = {
            "requests_sent": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "errors": 0,
            "avg_response_time": 0.0
        }
        self.health_status[self.config.base_url] = True

        # Start cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Connection pool initialized for {self.config.base_url}")

    async def close(self) -> None:
        """Close all connection pools"""
        if self._cleanup_task:
            self._cleanup_task.cancel()

        for session in self.sessions.values():
            await session.close()

        logger.info("All connection pools closed")

    @asynccontextmanager
    async def get_session(self, url: str):
        """Get an HTTP session for the URL"""
        base_url = self._extract_base_url(url)

        if base_url not in self.sessions:
            await self._create_session_for_url(base_url)

        session = self.sessions[base_url]

        try:
            yield session
        except Exception as e:
            self.session_stats[base_url]["errors"] += 1
            self.health_status[base_url] = False
            logger.error(f"Session error for {base_url}: {e}")
            raise

    async def _create_session_for_url(self, base_url: str) -> None:
        """Create a new session for a specific URL"""
        connector = aiohttp.TCPConnector(
            limit=self.config.max_concurrent,
            keepalive_timeout=30,
            enable_cleanup_closed=True
        )

        session = aiohttp.ClientSession(connector=connector)
        self.sessions[base_url] = session
        self.session_stats[base_url] = {
            "requests_sent": 0,
            "bytes_sent": 0,
            "bytes_received": 0,
            "errors": 0,
            "avg_response_time": 0.0
        }
        self.health_status[base_url] = True

    def _extract_base_url(self, url: str) -> str:
        """Extract base URL from full URL"""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}"

    async def _cleanup_loop(self) -> None:
        """Periodic cleanup of unused connections"""
        while True:
            try:
                await asyncio.sleep(300)  # Cleanup every 5 minutes

                for base_url, session in list(self.sessions.items()):
                    stats = self.session_stats.get(base_url, {})

                    # Close sessions with no recent activity
                    if stats.get("requests_sent", 0) == 0:
                        await session.close()
                        del self.sessions[base_url]
                        del self.session_stats[base_url]
                        logger.debug(f"Cleaned up unused session for {base_url}")

                    # Reset request counters
                    stats["requests_sent"] = 0

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")

    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics"""
        return {
            "active_sessions": len(self.sessions),
            "session_stats": self.session_stats,
            "health_status": self.health_status
        }


class RequestBatcher:
    """
    Intelligent request batcher that groups similar requests
    for optimal API utilization.
    """

    def __init__(self, batch_size: int = 10, batch_timeout: float = 1.0):
        self.batch_size = batch_size
        self.batch_timeout = batch_timeout
        self.pending_batches: Dict[str, List[Dict]] = defaultdict(list)
        self.batch_timers: Dict[str, asyncio.Task] = {}
        self.batch_callbacks: Dict[str, List[Callable]] = defaultdict(list)

    async def add_request(self,
                         batch_key: str,
                         request_data: Dict[str, Any],
                         callback: Callable,
                         priority: RequestPriority = RequestPriority.NORMAL) -> None:
        """Add a request to a batch group"""

        self.pending_batches[batch_key].append({
            "data": request_data,
            "priority": priority,
            "added_at": time.time()
        })
        self.batch_callbacks[batch_key].append(callback)

        # Start batch timer if this is the first request
        if len(self.pending_batches[batch_key]) == 1:
            self.batch_timers[batch_key] = asyncio.create_task(
                self._batch_timer(batch_key)
            )

        # Process batch if it's full
        if len(self.pending_batches[batch_key]) >= self.batch_size:
            await self._process_batch(batch_key)

    async def _batch_timer(self, batch_key: str) -> None:
        """Timer for automatic batch processing"""
        try:
            await asyncio.sleep(self.batch_timeout)
            if batch_key in self.pending_batches and self.pending_batches[batch_key]:
                await self._process_batch(batch_key)
        except asyncio.CancelledError:
            pass

    async def _process_batch(self, batch_key: str) -> None:
        """Process a batch of requests"""
        if batch_key not in self.pending_batches:
            return

        requests = self.pending_batches.pop(batch_key, [])
        callbacks = self.batch_callbacks.pop(batch_key, [])

        # Cancel timer
        if batch_key in self.batch_timers:
            self.batch_timers[batch_key].cancel()
            del self.batch_timers[batch_key]

        if not requests:
            return

        logger.debug(f"Processing batch {batch_key} with {len(requests)} requests")

        # Sort by priority
        requests.sort(key=lambda r: r["priority"].value)

        # Execute callbacks with batched requests
        for callback, request in zip(callbacks, requests):
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(request["data"])
                else:
                    callback(request["data"])
            except Exception as e:
                logger.error(f"Batch callback error: {e}")


class EnhancedAPIPerformanceLayer:
    """
    Main enhanced API performance layer coordinating all optimizations.
    """

    def __init__(self, configs: Dict[str, APIEndpointConfig]):
        self.configs = configs
        self.rate_limiters: Dict[str, AdaptiveRateLimiter] = {}
        self.connection_managers: Dict[str, ConnectionPoolManager] = {}
        self.request_batcher = RequestBatcher()

        # Performance tracking
        self.metrics: Dict[str, List[RequestMetrics]] = defaultdict(list)
        self.global_stats: Dict[str, Any] = {
            "total_requests": 0,
            "total_errors": 0,
            "average_response_time": 0.0,
            "cache_hit_rate": 0.0,
            "throughput_per_second": 0.0
        }

        # Request queues by priority
        self.request_queues: Dict[RequestPriority, asyncio.Queue] = {
            priority: asyncio.Queue() for priority in RequestPriority
        }

        self._processor_tasks: List[asyncio.Task] = []
        self._running = False

    async def initialize(self) -> None:
        """Initialize the enhanced API performance layer"""
        logger.info("Initializing Enhanced API Performance Layer")

        # Initialize rate limiters and connection managers
        for service_name, config in self.configs.items():
            self.rate_limiters[service_name] = AdaptiveRateLimiter(
                config.rate_limit_per_second,
                config.rate_limit_strategy
            )

            connection_manager = ConnectionPoolManager(config)
            await connection_manager.initialize()
            self.connection_managers[service_name] = connection_manager

        # Start request processors
        self._running = True
        for priority in RequestPriority:
            processor = asyncio.create_task(self._process_requests(priority))
            self._processor_tasks.append(processor)

        logger.info("Enhanced API Performance Layer initialized successfully")

    async def shutdown(self) -> None:
        """Shutdown the API performance layer"""
        self._running = False

        # Cancel processor tasks
        for task in self._processor_tasks:
            task.cancel()

        await asyncio.gather(*self._processor_tasks, return_exceptions=True)

        # Close connection managers
        for manager in self.connection_managers.values():
            await manager.close()

        logger.info("Enhanced API Performance Layer shut down")

    async def make_request(self,
                          service_name: str,
                          method: str,
                          url: str,
                          priority: RequestPriority = RequestPriority.NORMAL,
                          **kwargs) -> Dict[str, Any]:
        """
        Make an optimized API request with all performance enhancements.
        """
        request_data = {
            "service_name": service_name,
            "method": method,
            "url": url,
            "kwargs": kwargs,
            "timestamp": time.time()
        }

        # Add to appropriate priority queue
        await self.request_queues[priority].put(request_data)

        # Return a future that will be resolved when request completes
        future = asyncio.Future()
        request_data["future"] = future

        return await future

    async def make_batch_request(self,
                               service_name: str,
                               requests: List[Dict[str, Any]],
                               batch_key: Optional[str] = None) -> List[Dict[str, Any]]:
        """Make multiple requests as an optimized batch"""

        if not batch_key:
            batch_key = f"{service_name}_batch_{int(time.time())}"

        results = []
        futures = []

        # Add all requests to batch
        for request in requests:
            future = asyncio.Future()
            futures.append(future)

            await self.request_batcher.add_request(
                batch_key,
                {
                    "service_name": service_name,
                    "future": future,
                    **request
                },
                self._batch_callback,
                RequestPriority.BATCH
            )

        # Wait for all batch requests to complete
        results = await asyncio.gather(*futures, return_exceptions=True)
        return results

    async def _process_requests(self, priority: RequestPriority) -> None:
        """Process requests from priority queue"""
        while self._running:
            try:
                # Get request from queue
                request_data = await asyncio.wait_for(
                    self.request_queues[priority].get(),
                    timeout=1.0
                )

                # Process the request
                await self._execute_request(request_data)

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Request processor error for {priority}: {e}")

    async def _execute_request(self, request_data: Dict[str, Any]) -> None:
        """Execute a single API request with all optimizations"""
        service_name = request_data["service_name"]
        method = request_data["method"]
        url = request_data["url"]
        kwargs = request_data["kwargs"]
        future = request_data.get("future")

        start_time = time.time()

        try:
            # Rate limiting
            rate_limiter = self.rate_limiters.get(service_name)
            if rate_limiter:
                # Wait for rate limit clearance
                max_wait = 10.0  # Maximum wait time
                wait_start = time.time()

                while not await rate_limiter.acquire_token():
                    if time.time() - wait_start > max_wait:
                        raise Exception("Rate limit timeout")
                    await asyncio.sleep(0.1)

            # Get connection manager
            connection_manager = self.connection_managers.get(service_name)
            if not connection_manager:
                raise Exception(f"No connection manager for service: {service_name}")

            # Execute request with connection pooling
            async with connection_manager.get_session(url) as session:
                async with session.request(method, url, **kwargs) as response:
                    response_data = await response.json()

                    # Record metrics
                    execution_time = (time.time() - start_time) * 1000
                    self._record_metrics(
                        service_name, method, url, response.status,
                        execution_time, len(str(response_data)), False
                    )

                    # Update rate limiter
                    if rate_limiter:
                        rate_limiter.record_response(
                            response.status < 400,
                            execution_time / 1000
                        )

                    # Resolve future
                    if future:
                        future.set_result({
                            "status": response.status,
                            "data": response_data,
                            "response_time_ms": execution_time
                        })

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            self._record_metrics(
                service_name, method, url, 500,
                execution_time, 0, False
            )

            # Update rate limiter
            rate_limiter = self.rate_limiters.get(service_name)
            if rate_limiter:
                rate_limiter.record_response(False, execution_time / 1000)

            # Resolve future with error
            if future:
                future.set_exception(e)

            logger.error(f"Request execution failed: {e}")

    async def _batch_callback(self, request_data: Dict[str, Any]) -> None:
        """Callback for batch request processing"""
        await self._execute_request(request_data)

    def _record_metrics(self,
                       service_name: str,
                       method: str,
                       url: str,
                       status_code: int,
                       response_time_ms: float,
                       payload_size: int,
                       cache_hit: bool) -> None:
        """Record request metrics for analysis"""

        metric = RequestMetrics(
            url=url,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            payload_size_bytes=payload_size,
            cache_hit=cache_hit,
            timestamp=datetime.now(),
            priority=RequestPriority.NORMAL  # Default
        )

        self.metrics[service_name].append(metric)

        # Keep only recent metrics
        if len(self.metrics[service_name]) > 1000:
            self.metrics[service_name] = self.metrics[service_name][-1000:]

        # Update global stats
        self.global_stats["total_requests"] += 1
        if status_code >= 400:
            self.global_stats["total_errors"] += 1

        # Update average response time
        all_times = [
            metric.response_time_ms
            for metrics_list in self.metrics.values()
            for metric in metrics_list[-100:]  # Last 100 requests per service
        ]

        if all_times:
            self.global_stats["average_response_time"] = sum(all_times) / len(all_times)

    async def get_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive API performance report"""
        report = {
            "timestamp": datetime.now(),
            "global_stats": self.global_stats,
            "service_metrics": {},
            "rate_limiter_stats": {},
            "connection_pool_stats": {}
        }

        # Service-specific metrics
        for service_name, metrics_list in self.metrics.items():
            recent_metrics = metrics_list[-100:]  # Last 100 requests

            if recent_metrics:
                avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
                error_rate = sum(1 for m in recent_metrics if m.status_code >= 400) / len(recent_metrics)
                cache_hit_rate = sum(1 for m in recent_metrics if m.cache_hit) / len(recent_metrics)

                report["service_metrics"][service_name] = {
                    "total_requests": len(metrics_list),
                    "recent_requests": len(recent_metrics),
                    "average_response_time_ms": avg_response_time,
                    "error_rate": error_rate * 100,
                    "cache_hit_rate": cache_hit_rate * 100,
                    "throughput_per_minute": len([
                        m for m in recent_metrics
                        if m.timestamp > datetime.now() - timedelta(minutes=1)
                    ])
                }

        # Rate limiter stats
        for service_name, rate_limiter in self.rate_limiters.items():
            report["rate_limiter_stats"][service_name] = {
                "current_rate": rate_limiter.current_rate,
                "max_rate": rate_limiter.max_rate,
                "success_streak": rate_limiter.success_streak,
                "failure_streak": rate_limiter.failure_streak
            }

        # Connection pool stats
        for service_name, manager in self.connection_managers.items():
            report["connection_pool_stats"][service_name] = manager.get_pool_stats()

        return report


# Convenience functions for common API services
def create_ghl_api_config() -> APIEndpointConfig:
    """Create optimized config for GoHighLevel API"""
    return APIEndpointConfig(
        base_url="https://rest.gohighlevel.com",
        max_concurrent=5,  # GHL rate limits
        rate_limit_per_second=3.0,  # Conservative rate limiting
        rate_limit_strategy=RateLimitStrategy.ADAPTIVE,
        connection_timeout=10,
        read_timeout=30,
        retry_attempts=3,
        retry_backoff=1.0,
        enable_caching=True,
        cache_ttl=300
    )


def create_openai_api_config() -> APIEndpointConfig:
    """Create optimized config for OpenAI API"""
    return APIEndpointConfig(
        base_url="https://api.openai.com",
        max_concurrent=10,
        rate_limit_per_second=20.0,
        rate_limit_strategy=RateLimitStrategy.TOKEN_BUCKET,
        connection_timeout=15,
        read_timeout=120,  # AI responses can be slow
        retry_attempts=2,
        retry_backoff=2.0,
        enable_caching=True,
        cache_ttl=1800  # Cache AI responses longer
    )


def create_real_estate_api_config() -> APIEndpointConfig:
    """Create optimized config for real estate APIs"""
    return APIEndpointConfig(
        base_url="https://api.realtor.com",
        max_concurrent=15,
        rate_limit_per_second=10.0,
        rate_limit_strategy=RateLimitStrategy.SLIDING_WINDOW,
        connection_timeout=20,
        read_timeout=45,
        retry_attempts=3,
        retry_backoff=1.5,
        enable_caching=True,
        cache_ttl=3600  # Real estate data changes slowly
    )


# Global enhanced API performance layer
enhanced_api_layer = EnhancedAPIPerformanceLayer({
    "ghl": create_ghl_api_config(),
    "openai": create_openai_api_config(),
    "real_estate": create_real_estate_api_config()
})