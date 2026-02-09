"""
Enterprise Rate Limiting System
Provides comprehensive rate limiting with Redis backend, multiple strategies, and intelligent monitoring
"""

import time
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional

import redis.asyncio as redis
from fastapi import Request, status

from .audit_logger import AuditLogger


class RateLimitStrategy(str, Enum):
    """Rate limiting strategies"""

    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window"
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"
    ADAPTIVE = "adaptive"


class RateLimitScope(str, Enum):
    """Rate limit scope types"""

    GLOBAL = "global"
    IP = "ip"
    USER = "user"
    API_KEY = "api_key"
    ENDPOINT = "endpoint"
    USER_ENDPOINT = "user_endpoint"
    IP_ENDPOINT = "ip_endpoint"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration"""

    name: str
    strategy: RateLimitStrategy
    scope: RateLimitScope
    limit: int
    window_seconds: int
    burst_limit: Optional[int] = None  # For token bucket
    refill_rate: Optional[float] = None  # For token/leaky bucket
    adaptive_factor: Optional[float] = None  # For adaptive limiting
    enabled: bool = True


@dataclass
class RateLimitResult:
    """Rate limit check result"""

    allowed: bool
    limit: int
    remaining: int
    reset_time: datetime
    retry_after: Optional[int] = None
    rule_name: str = ""
    headers: Dict[str, str] = None


class RateLimiter:
    """
    Enterprise rate limiting system with multiple strategies and Redis persistence
    """

    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.audit_logger = AuditLogger()

        # Default rate limit rules
        self.rules: Dict[str, RateLimitRule] = {
            # Authentication endpoints
            "auth_login_global": RateLimitRule(
                name="auth_login_global",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.GLOBAL,
                limit=1000,
                window_seconds=3600,  # 1000 login attempts per hour globally
            ),
            "auth_login_ip": RateLimitRule(
                name="auth_login_ip",
                strategy=RateLimitStrategy.SLIDING_WINDOW,
                scope=RateLimitScope.IP,
                limit=10,
                window_seconds=900,  # 10 attempts per 15 min per IP
            ),
            "auth_login_user": RateLimitRule(
                name="auth_login_user",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.USER,
                limit=5,
                window_seconds=300,  # 5 attempts per 5 min per user
            ),
            # API endpoints
            "api_general": RateLimitRule(
                name="api_general",
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                scope=RateLimitScope.IP,
                limit=100,
                window_seconds=60,
                burst_limit=120,
                refill_rate=1.67,  # ~100 tokens per minute
            ),
            "api_user": RateLimitRule(
                name="api_user",
                strategy=RateLimitStrategy.TOKEN_BUCKET,
                scope=RateLimitScope.USER,
                limit=1000,
                window_seconds=3600,
                burst_limit=1200,
                refill_rate=0.28,  # ~1000 tokens per hour
            ),
            # Sensitive operations
            "password_reset": RateLimitRule(
                name="password_reset",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.IP,
                limit=3,
                window_seconds=3600,  # 3 password resets per hour per IP
            ),
            "data_export": RateLimitRule(
                name="data_export",
                strategy=RateLimitStrategy.FIXED_WINDOW,
                scope=RateLimitScope.USER,
                limit=5,
                window_seconds=86400,  # 5 data exports per day per user
            ),
            # AI/ML operations
            "claude_requests": RateLimitRule(
                name="claude_requests",
                strategy=RateLimitStrategy.ADAPTIVE,
                scope=RateLimitScope.USER,
                limit=50,
                window_seconds=3600,
                adaptive_factor=1.5,  # Increase limit based on success rate
            ),
            # Webhook endpoints
            "webhook_ghl": RateLimitRule(
                name="webhook_ghl",
                strategy=RateLimitStrategy.LEAKY_BUCKET,
                scope=RateLimitScope.IP,
                limit=1000,
                window_seconds=60,
                refill_rate=16.67,  # ~1000 requests per minute
            ),
        }

        # Rate limit monitoring
        self._blocked_requests: Dict[str, int] = defaultdict(int)
        self._adaptive_metrics: Dict[str, Dict] = defaultdict(dict)

    async def check_rate_limit(
        self,
        request: Request,
        rule_names: List[str],
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        custom_identifier: Optional[str] = None,
    ) -> RateLimitResult:
        """
        Check multiple rate limit rules and return the most restrictive result

        Args:
            request: FastAPI request object
            rule_names: List of rule names to check
            user_id: Optional user identifier
            api_key: Optional API key identifier
            custom_identifier: Optional custom identifier

        Returns:
            RateLimitResult: Most restrictive rate limit result
        """
        ip_address = self._get_client_ip(request)
        endpoint = request.url.path

        results = []

        # Check each rule
        for rule_name in rule_names:
            rule = self.rules.get(rule_name)
            if not rule or not rule.enabled:
                continue

            # Generate identifier based on scope
            identifier = self._generate_identifier(
                rule.scope, ip_address, user_id, api_key, endpoint, custom_identifier
            )

            # Check specific strategy
            if rule.strategy == RateLimitStrategy.FIXED_WINDOW:
                result = await self._check_fixed_window(rule, identifier)
            elif rule.strategy == RateLimitStrategy.SLIDING_WINDOW:
                result = await self._check_sliding_window(rule, identifier)
            elif rule.strategy == RateLimitStrategy.TOKEN_BUCKET:
                result = await self._check_token_bucket(rule, identifier)
            elif rule.strategy == RateLimitStrategy.LEAKY_BUCKET:
                result = await self._check_leaky_bucket(rule, identifier)
            elif rule.strategy == RateLimitStrategy.ADAPTIVE:
                result = await self._check_adaptive(rule, identifier, user_id)
            else:
                result = RateLimitResult(
                    allowed=True,
                    limit=rule.limit,
                    remaining=rule.limit,
                    reset_time=datetime.utcnow() + timedelta(seconds=rule.window_seconds),
                    rule_name=rule_name,
                )

            result.rule_name = rule_name
            results.append(result)

        # Return most restrictive result
        most_restrictive = min(results, key=lambda r: r.remaining, default=None)

        if not most_restrictive:
            # No rules applied, allow request
            return RateLimitResult(
                allowed=True,
                limit=float("inf"),
                remaining=float("inf"),
                reset_time=datetime.utcnow() + timedelta(seconds=3600),
            )

        # Add rate limit headers
        most_restrictive.headers = self._generate_headers(most_restrictive)

        # Log if blocked
        if not most_restrictive.allowed:
            await self._log_rate_limit_exceeded(
                rule_name=most_restrictive.rule_name,
                identifier=identifier,
                ip_address=ip_address,
                user_id=user_id,
                endpoint=endpoint,
            )

        return most_restrictive

    async def _check_fixed_window(self, rule: RateLimitRule, identifier: str) -> RateLimitResult:
        """Check fixed window rate limit"""
        current_time = int(time.time())
        window_start = (current_time // rule.window_seconds) * rule.window_seconds
        key = f"rate_limit:fixed:{rule.name}:{identifier}:{window_start}"

        async with self.redis.pipeline() as pipe:
            await pipe.incr(key)
            await pipe.expire(key, rule.window_seconds)
            results = await pipe.execute()

        current_count = results[0]
        allowed = current_count <= rule.limit
        remaining = max(0, rule.limit - current_count)
        reset_time = datetime.fromtimestamp(window_start + rule.window_seconds)
        retry_after = None if allowed else int(reset_time.timestamp() - current_time)

        return RateLimitResult(
            allowed=allowed, limit=rule.limit, remaining=remaining, reset_time=reset_time, retry_after=retry_after
        )

    async def _check_sliding_window(self, rule: RateLimitRule, identifier: str) -> RateLimitResult:
        """Check sliding window rate limit"""
        current_time = int(time.time())
        window_start = current_time - rule.window_seconds
        key = f"rate_limit:sliding:{rule.name}:{identifier}"

        async with self.redis.pipeline() as pipe:
            # Remove old entries
            await pipe.zremrangebyscore(key, 0, window_start)
            # Count current entries
            await pipe.zcard(key)
            # Add current request
            await pipe.zadd(key, {str(current_time): current_time})
            # Set expiration
            await pipe.expire(key, rule.window_seconds)
            results = await pipe.execute()

        current_count = results[1] + 1  # +1 for the new request we just added
        allowed = current_count <= rule.limit
        remaining = max(0, rule.limit - current_count)
        reset_time = datetime.fromtimestamp(current_time + rule.window_seconds)
        retry_after = None if allowed else rule.window_seconds

        # Remove the request we added if not allowed
        if not allowed:
            await self.redis.zrem(key, str(current_time))

        return RateLimitResult(
            allowed=allowed, limit=rule.limit, remaining=remaining, reset_time=reset_time, retry_after=retry_after
        )

    async def _check_token_bucket(self, rule: RateLimitRule, identifier: str) -> RateLimitResult:
        """Check token bucket rate limit"""
        current_time = time.time()
        key = f"rate_limit:token:{rule.name}:{identifier}"

        # Get bucket state
        bucket_data = await self.redis.hmget(key, "tokens", "last_refill")
        tokens = float(bucket_data[0] or rule.burst_limit or rule.limit)
        last_refill = float(bucket_data[1] or current_time)

        # Calculate tokens to add
        time_passed = current_time - last_refill
        tokens_to_add = time_passed * (rule.refill_rate or (rule.limit / rule.window_seconds))
        tokens = min(rule.burst_limit or rule.limit, tokens + tokens_to_add)

        # Check if request allowed
        if tokens >= 1:
            tokens -= 1
            allowed = True
            remaining = int(tokens)
        else:
            allowed = False
            remaining = 0

        # Update bucket state
        await self.redis.hmset(key, {"tokens": tokens, "last_refill": current_time})
        await self.redis.expire(key, rule.window_seconds * 2)

        # Calculate retry after
        retry_after = None
        if not allowed and rule.refill_rate:
            retry_after = int((1 - tokens) / rule.refill_rate)

        return RateLimitResult(
            allowed=allowed,
            limit=rule.burst_limit or rule.limit,
            remaining=remaining,
            reset_time=datetime.fromtimestamp(current_time + rule.window_seconds),
            retry_after=retry_after,
        )

    async def _check_leaky_bucket(self, rule: RateLimitRule, identifier: str) -> RateLimitResult:
        """Check leaky bucket rate limit"""
        current_time = time.time()
        key = f"rate_limit:leaky:{rule.name}:{identifier}"

        # Get bucket state
        bucket_data = await self.redis.hmget(key, "level", "last_leak")
        level = float(bucket_data[0] or 0)
        last_leak = float(bucket_data[1] or current_time)

        # Calculate leaked amount
        time_passed = current_time - last_leak
        leaked = time_passed * (rule.refill_rate or (rule.limit / rule.window_seconds))
        level = max(0, level - leaked)

        # Check if request allowed (bucket not full)
        if level < rule.limit:
            level += 1
            allowed = True
            remaining = int(rule.limit - level)
        else:
            allowed = False
            remaining = 0

        # Update bucket state
        await self.redis.hmset(key, {"level": level, "last_leak": current_time})
        await self.redis.expire(key, rule.window_seconds * 2)

        # Calculate retry after
        retry_after = None
        if not allowed and rule.refill_rate:
            retry_after = int(1 / rule.refill_rate)

        return RateLimitResult(
            allowed=allowed,
            limit=rule.limit,
            remaining=remaining,
            reset_time=datetime.fromtimestamp(current_time + rule.window_seconds),
            retry_after=retry_after,
        )

    async def _check_adaptive(self, rule: RateLimitRule, identifier: str, user_id: Optional[str]) -> RateLimitResult:
        """Check adaptive rate limit (adjusts based on success rate)"""
        current_time = int(time.time())
        window_start = current_time - rule.window_seconds

        # Get success rate for user
        success_rate = await self._get_success_rate(user_id, rule.window_seconds)

        # Adjust limit based on success rate and adaptive factor
        adaptive_factor = rule.adaptive_factor or 1.0
        if success_rate > 0.9:  # High success rate
            adjusted_limit = int(rule.limit * adaptive_factor)
        elif success_rate > 0.7:  # Medium success rate
            adjusted_limit = rule.limit
        else:  # Low success rate
            adjusted_limit = int(rule.limit / adaptive_factor)

        # Use sliding window check with adjusted limit
        temp_rule = RateLimitRule(
            name=rule.name,
            strategy=RateLimitStrategy.SLIDING_WINDOW,
            scope=rule.scope,
            limit=adjusted_limit,
            window_seconds=rule.window_seconds,
        )

        return await self._check_sliding_window(temp_rule, identifier)

    async def _get_success_rate(self, user_id: Optional[str], window_seconds: int) -> float:
        """Get success rate for adaptive rate limiting"""
        if not user_id:
            return 0.8  # Default success rate

        current_time = int(time.time())
        window_start = current_time - window_seconds

        success_key = f"success_rate:{user_id}"

        # Get success and total counts
        success_count = await self.redis.zcount(f"{success_key}:success", window_start, current_time)
        total_count = await self.redis.zcount(f"{success_key}:total", window_start, current_time)

        if total_count == 0:
            return 0.8  # Default success rate

        return success_count / total_count

    async def record_request_result(self, user_id: str, success: bool):
        """Record request result for adaptive rate limiting"""
        current_time = int(time.time())

        success_key = f"success_rate:{user_id}"

        # Record total request
        await self.redis.zadd(f"{success_key}:total", {str(current_time): current_time})
        await self.redis.expire(f"{success_key}:total", 86400)  # Keep for 24 hours

        # Record successful request
        if success:
            await self.redis.zadd(f"{success_key}:success", {str(current_time): current_time})
            await self.redis.expire(f"{success_key}:success", 86400)

    def _generate_identifier(
        self,
        scope: RateLimitScope,
        ip_address: str,
        user_id: Optional[str],
        api_key: Optional[str],
        endpoint: str,
        custom_identifier: Optional[str],
    ) -> str:
        """Generate rate limit identifier based on scope"""
        if scope == RateLimitScope.GLOBAL:
            return "global"
        elif scope == RateLimitScope.IP:
            return f"ip:{ip_address}"
        elif scope == RateLimitScope.USER:
            return f"user:{user_id or 'anonymous'}"
        elif scope == RateLimitScope.API_KEY:
            return f"api:{api_key or 'none'}"
        elif scope == RateLimitScope.ENDPOINT:
            return f"endpoint:{endpoint}"
        elif scope == RateLimitScope.USER_ENDPOINT:
            return f"user:{user_id or 'anonymous'}:endpoint:{endpoint}"
        elif scope == RateLimitScope.IP_ENDPOINT:
            return f"ip:{ip_address}:endpoint:{endpoint}"
        else:
            return custom_identifier or "unknown"

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request headers"""
        # Check for forwarded IP headers (in order of preference)
        forwarded_headers = [
            "x-forwarded-for",
            "x-real-ip",
            "cf-connecting-ip",
            "x-forwarded",
            "forwarded-for",
            "forwarded",
        ]

        for header in forwarded_headers:
            ip = request.headers.get(header)
            if ip:
                # Take the first IP if there are multiple
                return ip.split(",")[0].strip()

        # Fall back to client host
        return request.client.host if request.client else "unknown"

    def _generate_headers(self, result: RateLimitResult) -> Dict[str, str]:
        """Generate rate limit headers for response"""
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(result.remaining),
            "X-RateLimit-Reset": str(int(result.reset_time.timestamp())),
        }

        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)

        if result.rule_name:
            headers["X-RateLimit-Rule"] = result.rule_name

        return headers

    async def _log_rate_limit_exceeded(
        self, rule_name: str, identifier: str, ip_address: str, user_id: Optional[str], endpoint: str
    ):
        """Log rate limit exceeded event"""
        self._blocked_requests[rule_name] += 1

        await self.audit_logger.log_security_event(
            "rate_limit_exceeded",
            {
                "rule_name": rule_name,
                "identifier": identifier,
                "ip_address": ip_address,
                "user_id": user_id,
                "endpoint": endpoint,
                "blocked_count": self._blocked_requests[rule_name],
            },
        )

    async def get_rate_limit_stats(self) -> Dict:
        """Get rate limiting statistics"""
        return {
            "rules": {
                name: {
                    "strategy": rule.strategy.value,
                    "scope": rule.scope.value,
                    "limit": rule.limit,
                    "window_seconds": rule.window_seconds,
                    "enabled": rule.enabled,
                }
                for name, rule in self.rules.items()
            },
            "blocked_requests": dict(self._blocked_requests),
            "total_rules": len(self.rules),
            "active_rules": sum(1 for rule in self.rules.values() if rule.enabled),
        }

    def add_rule(self, rule: RateLimitRule):
        """Add a new rate limiting rule"""
        self.rules[rule.name] = rule

    def update_rule(self, name: str, **kwargs):
        """Update an existing rate limiting rule"""
        if name in self.rules:
            rule = self.rules[name]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)

    def enable_rule(self, name: str):
        """Enable a rate limiting rule"""
        if name in self.rules:
            self.rules[name].enabled = True

    def disable_rule(self, name: str):
        """Disable a rate limiting rule"""
        if name in self.rules:
            self.rules[name].enabled = False

    async def reset_rate_limit(self, rule_name: str, identifier: str):
        """Reset rate limit for specific identifier"""
        rule = self.rules.get(rule_name)
        if not rule:
            return False

        key_pattern = f"rate_limit:*:{rule_name}:{identifier}*"
        keys = await self.redis.keys(key_pattern)

        if keys:
            await self.redis.delete(*keys)
            await self.audit_logger.log_security_event(
                "rate_limit_reset", {"rule_name": rule_name, "identifier": identifier}
            )
            return True

        return False


# FastAPI middleware integration
from fastapi import Request
from fastapi.responses import JSONResponse


class RateLimitMiddleware:
    """FastAPI middleware for automatic rate limiting"""

    def __init__(self, rate_limiter: RateLimiter, default_rules: List[str] = None):
        self.rate_limiter = rate_limiter
        self.default_rules = default_rules or ["api_general"]

    async def __call__(self, request: Request, call_next):
        """Process request with rate limiting"""

        # Skip rate limiting for health check endpoints
        if request.url.path in ["/health", "/metrics", "/ready"]:
            return await call_next(request)

        # Determine rules to apply based on endpoint
        rules = self._get_rules_for_endpoint(request.url.path)

        # Extract user information
        user_id = getattr(request.state, "user_id", None)
        api_key = request.headers.get("x-api-key")

        # Check rate limits
        result = await self.rate_limiter.check_rate_limit(
            request=request, rule_names=rules, user_id=user_id, api_key=api_key
        )

        # Return rate limit error if blocked
        if not result.allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "error": "Rate limit exceeded",
                    "rule": result.rule_name,
                    "limit": result.limit,
                    "reset_time": result.reset_time.isoformat(),
                    "retry_after": result.retry_after,
                },
                headers=result.headers,
            )

        # Process request
        response = await call_next(request)

        # Add rate limit headers to response
        if result.headers:
            for key, value in result.headers.items():
                response.headers[key] = value

        # Record request result for adaptive rate limiting
        if user_id:
            success = 200 <= response.status_code < 400
            await self.rate_limiter.record_request_result(user_id, success)

        return response

    def _get_rules_for_endpoint(self, path: str) -> List[str]:
        """Get rate limit rules for specific endpoint"""
        if path.startswith("/auth/"):
            return ["auth_login_global", "auth_login_ip"]
        elif path.startswith("/api/webhook/"):
            return ["webhook_ghl"]
        elif path.startswith("/api/claude/"):
            return ["claude_requests", "api_user"]
        elif path.startswith("/admin/"):
            return ["api_user"]  # Stricter limits for admin
        else:
            return self.default_rules
