"""
Enhanced Rate Limiting Middleware with Enterprise Security Features

Features:
- Multi-tier rate limiting (authenticated vs unauthenticated)
- IP-based blocking for repeated violations
- WebSocket connection rate limiting
- Security event logging for audit trails
- Intelligent rate limiting based on request patterns
- Automatic threat detection and mitigation
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, Tuple, Set, Optional
import asyncio
import json
import ipaddress
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class ThreatDetector:
    """Advanced threat detection for rate limiting."""

    def __init__(self):
        self.suspicious_patterns = {
            'rapid_requests': deque(maxlen=1000),  # Track rapid request patterns
            'failed_auth': defaultdict(int),       # Failed authentication attempts
            'bot_indicators': set(),               # Known bot user agents
            'blocked_ips': set(),                  # Temporarily blocked IPs
        }
        self.block_duration = timedelta(minutes=15)

    def is_blocked_ip(self, ip: str) -> bool:
        """Check if IP is currently blocked."""
        return ip in self.suspicious_patterns['blocked_ips']

    def add_blocked_ip(self, ip: str, reason: str = "rate_limit_violation"):
        """Add IP to blocked list with logging."""
        self.suspicious_patterns['blocked_ips'].add(ip)
        logger.warning(
            f"IP blocked due to {reason}",
            extra={
                "security_event": "ip_blocked",
                "ip_address": ip,
                "reason": reason,
                "blocked_until": (datetime.now() + self.block_duration).isoformat(),
                "event_id": "RATE_001"
            }
        )

    def detect_bot_patterns(self, user_agent: str) -> bool:
        """Detect potential bot traffic."""
        bot_indicators = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'postman', 'insomnia'
        ]
        user_agent_lower = user_agent.lower()
        return any(indicator in user_agent_lower for indicator in bot_indicators)


class EnhancedRateLimiter:
    """Enterprise-grade rate limiter with threat detection."""

    def __init__(
        self,
        requests_per_minute: int = 100,
        burst: int = 20,
        authenticated_rpm: int = 1000,
        websocket_connections_per_ip: int = 10
    ):
        self.requests_per_minute = requests_per_minute
        self.authenticated_rpm = authenticated_rpm
        self.burst = burst
        self.websocket_connections_per_ip = websocket_connections_per_ip

        self.buckets: Dict[str, Tuple[int, datetime]] = {}
        self.websocket_connections: Dict[str, int] = defaultdict(int)
        self.request_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.lock = asyncio.Lock()
        self.threat_detector = ThreatDetector()

    async def is_allowed(
        self,
        key: str,
        is_authenticated: bool = False,
        request_type: str = "http",
        user_agent: str = "",
        path: str = ""
    ) -> Tuple[bool, Optional[str]]:
        """
        Enhanced rate limiting with threat detection.

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
        """
        async with self.lock:
            # Check if IP is blocked
            if self.threat_detector.is_blocked_ip(key):
                return False, "IP temporarily blocked"

            # Bot detection
            if self.threat_detector.detect_bot_patterns(user_agent):
                logger.info(
                    f"Bot traffic detected from {key}",
                    extra={
                        "security_event": "bot_detection",
                        "ip_address": key,
                        "user_agent": user_agent,
                        "event_id": "RATE_002"
                    }
                )
                # Apply stricter limits for bots
                rpm = self.requests_per_minute // 4
            else:
                # Set rate limit based on authentication status
                rpm = self.authenticated_rpm if is_authenticated else self.requests_per_minute

            # WebSocket connection limiting
            if request_type == "websocket":
                if self.websocket_connections[key] >= self.websocket_connections_per_ip:
                    return False, "WebSocket connection limit exceeded"
                self.websocket_connections[key] += 1
                return True, None

            now = datetime.now()

            # Track request pattern
            self.request_history[key].append({
                'timestamp': now,
                'path': path,
                'authenticated': is_authenticated
            })

            # Detect rapid fire requests (potential attack)
            recent_requests = [
                req for req in self.request_history[key]
                if now - req['timestamp'] < timedelta(seconds=10)
            ]

            if len(recent_requests) > 50:  # More than 50 requests in 10 seconds
                self.threat_detector.add_blocked_ip(key, "rapid_fire_requests")
                return False, "Suspicious request pattern detected"

            # Token bucket algorithm
            if key not in self.buckets:
                self.buckets[key] = (self.burst - 1, now)
                return True, None

            tokens, last_update = self.buckets[key]

            # Refill tokens based on time passed
            time_passed = (now - last_update).total_seconds()
            tokens_to_add = int(time_passed * (rpm / 60))
            tokens = min(self.burst, tokens + tokens_to_add)

            if tokens > 0:
                self.buckets[key] = (tokens - 1, now)
                return True, None
            else:
                # Track rate limit violations
                violations = len([
                    req for req in self.request_history[key]
                    if now - req['timestamp'] < timedelta(minutes=5)
                ])

                if violations > rpm // 2:  # Too many violations in 5 minutes
                    self.threat_detector.add_blocked_ip(key, "repeated_rate_limit_violations")

                self.buckets[key] = (0, last_update)
                return False, "Rate limit exceeded"

    def release_websocket_connection(self, key: str):
        """Release a WebSocket connection."""
        if key in self.websocket_connections:
            self.websocket_connections[key] = max(0, self.websocket_connections[key] - 1)


class EnhancedRateLimitMiddleware(BaseHTTPMiddleware):
    """Enterprise FastAPI middleware for rate limiting with security features."""

    def __init__(
        self,
        app,
        requests_per_minute: int = 100,
        authenticated_rpm: int = 1000,
        enable_ip_blocking: bool = True
    ):
        super().__init__(app)
        self.limiter = EnhancedRateLimiter(
            requests_per_minute=requests_per_minute,
            authenticated_rpm=authenticated_rpm
        )
        self.enable_ip_blocking = enable_ip_blocking

    def _get_client_identifier(self, request: Request) -> str:
        """Get client identifier for rate limiting."""
        # Check for forwarded headers (behind proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP (original client)
            return forwarded_for.split(',')[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        return request.client.host if request.client else "127.0.0.1"

    def _is_authenticated(self, request: Request) -> bool:
        """Check if request is authenticated."""
        auth_header = request.headers.get("Authorization")
        api_key = request.headers.get("X-API-Key")
        return bool(auth_header or api_key)

    def _get_request_type(self, request: Request) -> str:
        """Determine request type for specialized handling."""
        if request.url.path.startswith("/ws"):
            return "websocket"
        elif request.url.path.startswith("/api"):
            return "api"
        return "http"

    async def dispatch(self, request: Request, call_next):
        """Process request with enhanced rate limiting and security."""
        client_ip = self._get_client_identifier(request)
        is_authenticated = self._is_authenticated(request)
        user_agent = request.headers.get("User-Agent", "")
        request_type = self._get_request_type(request)
        path = request.url.path

        # Skip rate limiting for health checks
        if path in ["/health", "/api/health", "/ping"]:
            return await call_next(request)

        # Check rate limit with enhanced features
        allowed, reason = await self.limiter.is_allowed(
            key=client_ip,
            is_authenticated=is_authenticated,
            request_type=request_type,
            user_agent=user_agent,
            path=path
        )

        if not allowed:
            # Log security event
            logger.warning(
                f"Rate limit exceeded for {client_ip}",
                extra={
                    "security_event": "rate_limit_exceeded",
                    "ip_address": client_ip,
                    "path": path,
                    "user_agent": user_agent,
                    "is_authenticated": is_authenticated,
                    "reason": reason or "Rate limit exceeded",
                    "event_id": "RATE_003"
                }
            )

            # Return detailed error response
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "Rate limit exceeded",
                    "message": reason or "Too many requests. Please try again later.",
                    "retry_after": 60,  # Seconds
                    "type": "rate_limit_error"
                },
                headers={
                    "Retry-After": "60",
                    "X-Rate-Limit-Remaining": "0",
                    "X-Rate-Limit-Reset": str(int((datetime.now() + timedelta(minutes=1)).timestamp()))
                }
            )

        # Process request
        response = await call_next(request)

        # Add rate limiting headers
        response.headers["X-Rate-Limit-Type"] = "authenticated" if is_authenticated else "anonymous"
        response.headers["X-Rate-Limit-Applied"] = "true"

        return response


# Backward compatibility
RateLimitMiddleware = EnhancedRateLimitMiddleware
RateLimiter = EnhancedRateLimiter
