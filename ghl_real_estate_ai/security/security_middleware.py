"""
Enterprise Security Middleware
Comprehensive security middleware integrating authentication, authorization, rate limiting, and monitoring
"""

import time
import uuid
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

import redis.asyncio as redis
from fastapi import HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .audit_logger import AuditLogger, AuditSeverity
from .auth_manager import AuthManager, SecurityConfig
from .input_validator import InputValidator
from .rate_limiter import RateLimiter
from .rbac import PermissionType, ResourceType, RoleManager


@dataclass
class SecurityHeaders:
    """Security headers configuration"""

    strict_transport_security: str = "max-age=31536000; includeSubOntario Millss"
    content_type_options: str = "nosniff"
    frame_options: str = "DENY"
    xss_protection: str = "1; mode=block"
    content_security_policy: str = "default-src 'self'"
    referrer_policy: str = "strict-origin-when-cross-origin"
    permissions_policy: str = "geolocation=(), microphone=(), camera=()"


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive security middleware that provides:
    - Authentication and authorization
    - Rate limiting
    - Security headers
    - Input validation
    - Audit logging
    - Threat detection
    """

    def __init__(
        self,
        app,
        auth_manager: AuthManager,
        rate_limiter: RateLimiter,
        role_manager: RoleManager,
        audit_logger: AuditLogger,
        input_validator: InputValidator,
        security_headers: SecurityHeaders = None,
        exempt_paths: List[str] = None,
    ):
        super().__init__(app)
        self.auth_manager = auth_manager
        self.rate_limiter = rate_limiter
        self.role_manager = role_manager
        self.audit_logger = audit_logger
        self.input_validator = input_validator
        self.security_headers = security_headers or SecurityHeaders()

        # Paths that don't require authentication
        self.exempt_paths = set(
            exempt_paths
            or ["/docs", "/redoc", "/openapi.json", "/health", "/ready", "/metrics", "/auth/login", "/auth/token"]
        )

        # Threat detection
        self._suspicious_ips: Set[str] = set()
        self._blocked_ips: Set[str] = set()
        self._request_patterns: Dict[str, List[float]] = {}

    async def dispatch(self, request: Request, call_next):
        """Main middleware processing"""
        start_time = time.time()
        request_id = str(uuid.uuid4())

        # Add request ID to state
        request.state.request_id = request_id
        request.state.start_time = start_time

        try:
            # Security pre-checks
            await self._security_pre_checks(request)

            # Input validation
            await self._validate_input(request)

            # Rate limiting
            await self._check_rate_limits(request)

            # Authentication (if required)
            user_context = await self._authenticate_request(request)

            # Authorization (if authenticated)
            if user_context:
                await self._authorize_request(request, user_context)

            # Process request
            response = await call_next(request)

            # Add security headers
            self._add_security_headers(response)

            # Audit successful request
            await self._audit_request(request, response, user_context, start_time)

            return response

        except HTTPException as e:
            # Create error response
            response = JSONResponse(status_code=e.status_code, content={"error": e.detail, "request_id": request_id})

            # Add security headers to error response
            self._add_security_headers(response)

            # Audit failed request
            await self._audit_failed_request(request, e, start_time)

            return response

        except Exception as e:
            # Handle unexpected errors
            self.audit_logger.log_error(
                "security_middleware_error",
                {"error": str(e), "path": request.url.path, "method": request.method, "request_id": request_id},
                severity=AuditSeverity.HIGH,
            )

            response = JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content={"error": "Internal server error", "request_id": request_id},
            )

            self._add_security_headers(response)
            return response

    async def _security_pre_checks(self, request: Request):
        """Perform security pre-checks"""
        ip_address = self._get_client_ip(request)

        # Check blocked IPs
        if ip_address in self._blocked_ips:
            await self.audit_logger.log_security_event(
                "blocked_ip_access", {"ip_address": ip_address, "path": request.url.path}, severity=AuditSeverity.HIGH
            )
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

        # Check suspicious activity
        if ip_address in self._suspicious_ips:
            await self.audit_logger.log_security_event(
                "suspicious_ip_access",
                {"ip_address": ip_address, "path": request.url.path},
                severity=AuditSeverity.MEDIUM,
            )

        # Detect potential attacks
        await self._detect_threats(request, ip_address)

    async def _detect_threats(self, request: Request, ip_address: str):
        """Detect potential security threats"""
        import urllib.parse

        path = urllib.parse.unquote_plus(request.url.path.lower())
        query = urllib.parse.unquote_plus(str(request.query_params).lower())

        # SQL injection patterns
        sql_patterns = [
            "union select",
            "drop table",
            "insert into",
            "update set",
            "delete from",
            "' or '1'='1",
            "'; drop",
            "exec(",
            "script>",
        ]

        # XSS patterns
        xss_patterns = ["<script", "javascript:", "onload=", "onerror=", "onclick=", "alert(", "document.cookie"]

        # Path traversal patterns
        path_traversal_patterns = ["../", "..\\", "..\\/", "..%2f", "..%5c"]

        suspicious_activity = False
        threat_type = ""

        # Check for SQL injection
        for pattern in sql_patterns:
            # ROADMAP-090: For large scale, implement better indexing (Redis search, DB index)
            if pattern in query or pattern in path:
                suspicious_activity = True
                threat_type = "sql_injection"
                break

        # Check for XSS
        if not suspicious_activity:
            for pattern in xss_patterns:
                if pattern in query or pattern in path:
                    suspicious_activity = True
                    threat_type = "xss_attempt"
                    break

        # Check for path traversal
        if not suspicious_activity:
            for pattern in path_traversal_patterns:
                if pattern in query or pattern in path:
                    suspicious_activity = True
                    threat_type = "path_traversal"
                    break

        # Check request rate patterns
        current_time = time.time()
        if ip_address not in self._request_patterns:
            self._request_patterns[ip_address] = []

        # Clean old requests (last 60 seconds)
        self._request_patterns[ip_address] = [
            req_time for req_time in self._request_patterns[ip_address] if current_time - req_time < 60
        ]

        self._request_patterns[ip_address].append(current_time)

        # Check for rapid requests (potential DDoS)
        if len(self._request_patterns[ip_address]) > 100:  # More than 100 requests per minute
            suspicious_activity = True
            threat_type = "potential_ddos"

        if suspicious_activity:
            self._suspicious_ips.add(ip_address)

            await self.audit_logger.log_security_event(
                "threat_detected",
                {
                    "threat_type": threat_type,
                    "ip_address": ip_address,
                    "path": request.url.path,
                    "query_params": str(request.query_params),
                    "user_agent": request.headers.get("user-agent", ""),
                },
                severity=AuditSeverity.HIGH,
            )

            # Block IP for severe threats
            if threat_type in ["sql_injection", "path_traversal", "potential_ddos"]:
                self._blocked_ips.add(ip_address)
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Malicious activity detected")

    async def _validate_input(self, request: Request):
        """Validate request input"""
        try:
            # Validate headers
            await self.input_validator.validate_headers(dict(request.headers))

            # Validate query parameters
            if request.query_params:
                await self.input_validator.validate_query_params(dict(request.query_params))

            # Validate request body for POST/PUT requests
            if request.method in ["POST", "PUT", "PATCH"]:
                content_type = request.headers.get("content-type", "")
                if "application/json" in content_type:
                    # Note: Body validation would need to be implemented carefully
                    # to avoid consuming the body before the actual handler
                    pass

        except ValueError as e:
            await self.audit_logger.log_security_event(
                "input_validation_failed",
                {
                    "error": str(e),
                    "path": request.url.path,
                    "method": request.method,
                    "ip_address": self._get_client_ip(request),
                },
                severity=AuditSeverity.MEDIUM,
            )
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid input")

    async def _check_rate_limits(self, request: Request):
        """Check rate limits"""
        # Determine which rate limit rules to apply
        path = request.url.path
        rules = []

        if path.startswith("/auth/"):
            rules = ["auth_login_global", "auth_login_ip"]
        elif path.startswith("/api/webhook/"):
            rules = ["webhook_ghl"]
        elif path.startswith("/api/claude/"):
            rules = ["claude_requests", "api_user"]
        else:
            rules = ["api_general"]

        # Extract user info if available
        user_id = getattr(request.state, "user_id", None)
        api_key = request.headers.get("x-api-key")

        # Check rate limits
        result = await self.rate_limiter.check_rate_limit(
            request=request, rule_names=rules, user_id=user_id, api_key=api_key
        )

        if not result.allowed:
            # Add rate limit headers
            if result.headers:
                for key, value in result.headers.items():
                    request.state.rate_limit_headers = getattr(request.state, "rate_limit_headers", {})
                    request.state.rate_limit_headers[key] = value

            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="Rate limit exceeded", headers=result.headers
            )

    async def _authenticate_request(self, request: Request) -> Optional[Dict]:
        """Authenticate request if required"""
        path = request.url.path

        # Skip authentication for exempt paths
        if path in self.exempt_paths or any(path.startswith(exempt) for exempt in self.exempt_paths):
            return None

        # Check for authorization header
        auth_header = request.headers.get("authorization", "")
        api_key = request.headers.get("x-api-key", "")

        user_context = None

        # JWT authentication
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                user_context = await self.auth_manager.validate_token(token)
                request.state.user_id = user_context["user"]["user_id"]
                request.state.session_id = user_context["session"].session_id
                request.state.auth_method = "jwt"

            except HTTPException as e:
                await self.audit_logger.log_security_event(
                    "authentication_failed",
                    {"reason": "invalid_jwt_token", "ip_address": self._get_client_ip(request), "path": path},
                    severity=AuditSeverity.MEDIUM,
                )
                raise e

        # API key authentication
        elif api_key:
            # ROADMAP-089: Implement API key validation against database/secrets
            request.state.api_key = api_key
            request.state.auth_method = "api_key"

        # No authentication provided for protected path
        else:
            await self.audit_logger.log_security_event(
                "authentication_required",
                {"path": path, "ip_address": self._get_client_ip(request)},
                severity=AuditSeverity.MEDIUM,
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user_context

    async def _authorize_request(self, request: Request, user_context: Dict):
        """Authorize request based on user permissions"""
        path = request.url.path
        method = request.method

        # Determine required resource and permission
        resource, permission_type = self._map_endpoint_to_permission(path, method)

        if resource and permission_type:
            user = user_context["user"]
            user_roles = [role.name for role in user.roles]

            # Check permissions
            has_permission = self.role_manager.check_permission(
                user_roles=user_roles, resource=resource, permission_type=permission_type
            )

            if not has_permission:
                await self.audit_logger.log_security_event(
                    "authorization_failed",
                    {
                        "user_id": user.user_id,
                        "required_resource": resource.value,
                        "required_permission": permission_type.value,
                        "user_roles": user_roles,
                        "path": path,
                        "method": method,
                    },
                    severity=AuditSeverity.HIGH,
                )

                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    def _map_endpoint_to_permission(
        self, path: str, method: str
    ) -> tuple[Optional[ResourceType], Optional[PermissionType]]:
        """Map API endpoint to required resource and permission"""
        # Admin endpoints
        if path.startswith("/admin/"):
            if "users" in path:
                resource = ResourceType.USERS
            elif "roles" in path:
                resource = ResourceType.SECURITY
            elif "config" in path:
                resource = ResourceType.SYSTEM_CONFIG
            elif "audit" in path:
                resource = ResourceType.AUDIT_LOGS
            else:
                resource = ResourceType.SYSTEM_CONFIG

            permission = PermissionType.ADMIN if method in ["DELETE"] else PermissionType.MANAGE
            return resource, permission

        # API endpoints
        elif path.startswith("/api/"):
            if "leads" in path:
                resource = ResourceType.LEADS
            elif "properties" in path:
                resource = ResourceType.PROPERTIES
            elif "contacts" in path:
                resource = ResourceType.CONTACTS
            elif "campaigns" in path:
                resource = ResourceType.CAMPAIGNS
            elif "reports" in path:
                resource = ResourceType.REPORTS
            elif "analytics" in path:
                resource = ResourceType.ANALYTICS
            elif "claude" in path:
                resource = ResourceType.CLAUDE_ASSISTANT
            elif "webhook" in path:
                resource = ResourceType.WEBHOOKS
            else:
                resource = ResourceType.API

            # Map HTTP method to permission type
            permission_map = {
                "GET": PermissionType.READ,
                "POST": PermissionType.WRITE,
                "PUT": PermissionType.WRITE,
                "PATCH": PermissionType.WRITE,
                "DELETE": PermissionType.DELETE,
            }

            permission = permission_map.get(method, PermissionType.READ)
            return resource, permission

        return None, None

    def _add_security_headers(self, response: Response):
        """Add security headers to response"""
        headers = {
            "Strict-Transport-Security": self.security_headers.strict_transport_security,
            "X-Content-Type-Options": self.security_headers.content_type_options,
            "X-Frame-Options": self.security_headers.frame_options,
            "X-XSS-Protection": self.security_headers.xss_protection,
            "Content-Security-Policy": self.security_headers.content_security_policy,
            "Referrer-Policy": self.security_headers.referrer_policy,
            "Permissions-Policy": self.security_headers.permissions_policy,
            "X-Request-ID": getattr(response, "request_id", "unknown"),
        }

        for key, value in headers.items():
            response.headers[key] = value

        # Add rate limit headers if available
        if hasattr(response, "rate_limit_headers"):
            for key, value in response.rate_limit_headers.items():
                response.headers[key] = value

    async def _audit_request(
        self, request: Request, response: Response, user_context: Optional[Dict], start_time: float
    ):
        """Audit successful request"""
        duration_ms = (time.time() - start_time) * 1000

        # Log API access
        await self.audit_logger.log_api_event(
            endpoint=request.url.path,
            method=request.method,
            status_code=response.status_code,
            duration_ms=duration_ms,
            user_id=user_context["user"]["user_id"] if user_context else None,
            ip_address=self._get_client_ip(request),
            user_agent=request.headers.get("user-agent", ""),
            request_id=request.state.request_id,
        )

        # Record success for adaptive rate limiting
        if user_context:
            await self.rate_limiter.record_request_result(
                user_context["user"]["user_id"], success=200 <= response.status_code < 400
            )

    async def _audit_failed_request(self, request: Request, error: HTTPException, start_time: float):
        """Audit failed request"""
        duration_ms = (time.time() - start_time) * 1000

        await self.audit_logger.log_security_event(
            "request_failed",
            {
                "path": request.url.path,
                "method": request.method,
                "status_code": error.status_code,
                "error": error.detail,
                "duration_ms": duration_ms,
                "ip_address": self._get_client_ip(request),
                "user_agent": request.headers.get("user-agent", ""),
                "request_id": request.state.request_id,
            },
            severity=AuditSeverity.MEDIUM if error.status_code >= 400 else AuditSeverity.LOW,
        )

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded IP headers
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
                return ip.split(",")[0].strip()

        return request.client.host if request.client else "unknown"


def create_security_middleware(
    redis_client: redis.Redis, config: SecurityConfig, exempt_paths: List[str] = None
) -> SecurityMiddleware:
    """Factory function to create configured security middleware"""

    # Initialize components
    auth_manager = AuthManager(config, redis_client)
    rate_limiter = RateLimiter(redis_client)
    role_manager = RoleManager()
    audit_logger = AuditLogger(redis_client=redis_client, log_file_path="logs/audit.log")
    input_validator = InputValidator()

    # Create middleware
    return SecurityMiddleware(
        app=None,  # Will be set by FastAPI
        auth_manager=auth_manager,
        rate_limiter=rate_limiter,
        role_manager=role_manager,
        audit_logger=audit_logger,
        input_validator=input_validator,
        exempt_paths=exempt_paths,
    )
