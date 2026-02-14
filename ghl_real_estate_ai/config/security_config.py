"""
Production Security Configuration

Features:
- Environment-specific security settings
- Secure defaults for production deployment
- Security policy enforcement
- Configuration validation
- Secrets management guidelines
"""

import logging
import secrets
from enum import Enum
from typing import Dict, List, Optional

from pydantic import Field, ValidationInfo, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecurityLevel(str, Enum):
    """Security level configurations."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityConfig(BaseSettings):
    """Production-ready security configuration."""

    # Environment Configuration
    environment: SecurityLevel = Field(default=SecurityLevel.DEVELOPMENT)

    # JWT Security
    jwt_secret_key: str = Field(..., min_length=32)
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=30)
    jwt_refresh_token_expire_days: int = Field(default=7)

    # Rate Limiting
    rate_limit_requests_per_minute: int = Field(default=100)
    rate_limit_authenticated_rpm: int = Field(default=1000)
    rate_limit_burst_size: int = Field(default=20)
    rate_limit_block_duration_minutes: int = Field(default=15)

    # Input Validation
    max_request_size_mb: int = Field(default=10)
    enable_input_sanitization: bool = Field(default=True)
    enable_sql_injection_protection: bool = Field(default=True)
    enable_xss_protection: bool = Field(default=True)

    # Security Headers
    enable_csp: bool = Field(default=True)
    enable_hsts: bool = Field(default=True)
    enable_security_headers: bool = Field(default=True)
    csp_report_uri: Optional[str] = None

    # WebSocket Security
    websocket_max_connections_per_ip: int = Field(default=10)
    websocket_max_message_rate: int = Field(default=60)
    websocket_max_message_size_kb: int = Field(default=64)
    websocket_require_auth: bool = Field(default=True)

    # Monitoring and Logging
    enable_security_monitoring: bool = Field(default=True)
    security_log_level: str = Field(default="INFO")
    security_event_retention_days: int = Field(default=30)
    enable_audit_logging: bool = Field(default=True)

    # Threat Detection
    enable_threat_detection: bool = Field(default=True)
    ip_reputation_threshold: int = Field(default=50)
    failed_auth_threshold: int = Field(default=5)
    auto_block_suspicious_ips: bool = Field(default=True)

    # API Security
    api_key_length: int = Field(default=32)
    api_rate_limit_per_key: int = Field(default=5000)
    require_https: bool = Field(default=True)

    # Database Security
    db_connection_timeout: int = Field(default=30)
    db_max_connections: int = Field(default=20)
    enable_db_query_logging: bool = Field(default=False)

    # Redis Security
    redis_password: Optional[str] = None
    redis_ssl: bool = Field(default=False)
    redis_connection_timeout: int = Field(default=5)

    # CORS Configuration
    cors_allow_origins: List[str] = Field(default=[])
    cors_allow_credentials: bool = Field(default=True)
    cors_max_age: int = Field(default=3600)

    # Content Security Policy
    csp_default_src: List[str] = Field(default=["'self'"])
    csp_script_src: List[str] = Field(default=["'self'"])
    csp_style_src: List[str] = Field(default=["'self'"])
    csp_img_src: List[str] = Field(default=["'self'", "data:", "https:"])
    csp_connect_src: List[str] = Field(default=["'self'"])

    # Security Feature Flags
    enable_ip_whitelisting: bool = Field(default=False)
    ip_whitelist: List[str] = Field(default=[])
    enable_geo_blocking: bool = Field(default=False)
    blocked_countries: List[str] = Field(default=[])

    model_config = SettingsConfigDict(env_prefix="SECURITY_", case_sensitive=False)

    @field_validator("jwt_secret_key")
    @classmethod
    def validate_jwt_secret_key(cls, v):
        """Ensure JWT secret key is strong enough."""
        if len(v) < 32:
            raise ValueError("JWT secret key must be at least 32 characters long")
        return v

    @field_validator("environment")
    @classmethod
    def set_security_defaults_by_environment(cls, v, info: ValidationInfo):
        """Set security defaults based on environment."""
        if v == SecurityLevel.PRODUCTION:
            # Production security defaults
            info.data.update(
                {
                    "require_https": True,
                    "enable_hsts": True,
                    "enable_csp": True,
                    "enable_security_monitoring": True,
                    "enable_threat_detection": True,
                    "auto_block_suspicious_ips": True,
                    "websocket_require_auth": True,
                    "rate_limit_requests_per_minute": 100,
                    "jwt_access_token_expire_minutes": 15,  # Shorter in production
                }
            )
        elif v == SecurityLevel.DEVELOPMENT:
            # Development-friendly defaults
            info.data.update(
                {
                    "require_https": False,
                    "rate_limit_requests_per_minute": 1000,
                    "jwt_access_token_expire_minutes": 60,  # Longer for development
                }
            )
        return v

    @field_validator("cors_allow_origins")
    @classmethod
    def validate_cors_origins(cls, v, info: ValidationInfo):
        """Validate CORS origins for security."""
        environment = info.data.get("environment", SecurityLevel.DEVELOPMENT)
        if environment == SecurityLevel.PRODUCTION:
            # In production, ensure no wildcard origins
            if "*" in v:
                raise ValueError("Wildcard CORS origins not allowed in production")
        return v

    def get_csp_policy(self) -> str:
        """Generate Content Security Policy string."""
        if not self.enable_csp:
            return ""

        policy_parts = []
        policy_parts.append(f"default-src {' '.join(self.csp_default_src)}")
        policy_parts.append(f"script-src {' '.join(self.csp_script_src)}")
        policy_parts.append(f"style-src {' '.join(self.csp_style_src)}")
        policy_parts.append(f"img-src {' '.join(self.csp_img_src)}")
        policy_parts.append(f"connect-src {' '.join(self.csp_connect_src)}")

        # Add production-specific directives
        if self.environment == SecurityLevel.PRODUCTION:
            policy_parts.extend(
                [
                    "frame-ancestors 'none'",
                    "form-action 'self'",
                    "base-uri 'self'",
                    "object-src 'none'",
                    "upgrade-insecure-requests",
                    "block-all-mixed-content",
                ]
            )

        if self.csp_report_uri:
            policy_parts.append(f"report-uri {self.csp_report_uri}")

        return "; ".join(policy_parts)

    def get_security_headers(self) -> Dict[str, str]:
        """Get all security headers configuration."""
        headers = {}

        if self.enable_security_headers:
            headers.update(
                {
                    "X-Content-Type-Options": "nosniff",
                    "X-Frame-Options": "DENY",
                    "X-XSS-Protection": "0",  # Rely on CSP instead
                    "Referrer-Policy": "strict-origin-when-cross-origin",
                    "Permissions-Policy": (
                        "accelerometer=(), camera=(), geolocation=(), "
                        "gyroscope=(), magnetometer=(), microphone=(), "
                        "payment=(), usb=()"
                    ),
                }
            )

        if self.enable_hsts and self.environment == SecurityLevel.PRODUCTION:
            headers["Strict-Transport-Security"] = "max-age=31536000; includeSubOntario Millss; preload"

        if self.enable_csp:
            headers["Content-Security-Policy"] = self.get_csp_policy()

        return headers

    def validate_configuration(self) -> List[str]:
        """Validate security configuration and return warnings."""
        warnings = []

        # Production security checks
        if self.environment == SecurityLevel.PRODUCTION:
            if not self.require_https:
                warnings.append("HTTPS should be required in production")

            if self.jwt_access_token_expire_minutes > 60:
                warnings.append("JWT access token expiry too long for production")

            if not self.enable_security_monitoring:
                warnings.append("Security monitoring should be enabled in production")

            if not self.enable_threat_detection:
                warnings.append("Threat detection should be enabled in production")

            if self.rate_limit_requests_per_minute > 500:
                warnings.append("Rate limiting may be too permissive for production")

        # General security checks
        if len(self.jwt_secret_key) < 64:
            warnings.append("Consider using a longer JWT secret key (64+ characters)")

        if not self.enable_input_sanitization:
            warnings.append("Input sanitization should be enabled")

        if not self.websocket_require_auth:
            warnings.append("WebSocket authentication should be required")

        return warnings

    def generate_secure_api_key(self) -> str:
        """Generate a cryptographically secure API key."""
        return secrets.token_urlsafe(self.api_key_length)

    def is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is in whitelist."""
        if not self.enable_ip_whitelisting:
            return True
        return ip in self.ip_whitelist

    def get_rate_limit_for_user(self, is_authenticated: bool, has_api_key: bool) -> int:
        """Get appropriate rate limit for user type."""
        if has_api_key:
            return self.api_rate_limit_per_key
        elif is_authenticated:
            return self.rate_limit_authenticated_rpm
        else:
            return self.rate_limit_requests_per_minute


# Security configuration factory
def create_security_config() -> SecurityConfig:
    """Create security configuration from environment variables."""
    try:
        config = SecurityConfig()

        # Validate configuration
        warnings = config.validate_configuration()
        if warnings:
            logger = logging.getLogger(__name__)
            for warning in warnings:
                logger.warning(f"Security configuration warning: {warning}")

        return config

    except Exception as e:
        # Fallback to secure defaults if configuration fails
        logging.error(f"Failed to load security configuration: {e}")
        return SecurityConfig(
            jwt_secret_key=secrets.token_urlsafe(32),
            environment=SecurityLevel.PRODUCTION,  # Safe default
        )


# Production deployment security checklist
PRODUCTION_SECURITY_CHECKLIST = [
    "✓ JWT_SECRET_KEY is set to a strong, unique value (64+ characters)",
    "✓ HTTPS is enabled and enforced",
    "✓ Security headers middleware is enabled",
    "✓ Rate limiting is configured appropriately",
    "✓ Input validation and sanitization is enabled",
    "✓ Security monitoring and logging is active",
    "✓ Database connections are secured with authentication",
    "✓ Redis is secured with authentication if used",
    "✓ CORS origins are explicitly configured (no wildcards)",
    "✓ Content Security Policy is configured",
    "✓ WebSocket authentication is required",
    "✓ Threat detection and IP blocking is enabled",
    "✓ Security event retention is configured",
    "✓ API keys are properly secured",
    "✓ Environment variables are not exposed in logs",
    "✓ Error messages don't leak sensitive information",
    "✓ Regular security audits are scheduled",
    "✓ Incident response procedures are documented",
    "✓ Backup and recovery procedures are tested",
    "✓ Security compliance requirements are met",
]

# Example secure environment variables template
SECURITY_ENV_TEMPLATE = """
# Security Configuration for Production
SECURITY_ENVIRONMENT=production
SECURITY_JWT_SECRET_KEY=<GENERATE_SECURE_KEY_64_CHARS>
SECURITY_JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
SECURITY_REQUIRE_HTTPS=true
SECURITY_ENABLE_SECURITY_MONITORING=true
SECURITY_ENABLE_THREAT_DETECTION=true
SECURITY_RATE_LIMIT_REQUESTS_PER_MINUTE=100
SECURITY_RATE_LIMIT_AUTHENTICATED_RPM=1000
SECURITY_WEBSOCKET_REQUIRE_AUTH=true
SECURITY_ENABLE_CSP=true
SECURITY_ENABLE_HSTS=true
SECURITY_CORS_ALLOW_ORIGINS=["https://yourontario_mills.com","https://app.yourontario_mills.com"]

# Optional: Advanced Security Features
SECURITY_ENABLE_IP_WHITELISTING=false
SECURITY_IP_WHITELIST=[]
SECURITY_ENABLE_GEO_BLOCKING=false
SECURITY_BLOCKED_COUNTRIES=[]

# Monitoring and Logging
SECURITY_SECURITY_LOG_LEVEL=INFO
SECURITY_SECURITY_EVENT_RETENTION_DAYS=90
SECURITY_ENABLE_AUDIT_LOGGING=true

# Database and Redis Security
SECURITY_DB_CONNECTION_TIMEOUT=30
SECURITY_REDIS_PASSWORD=<REDIS_PASSWORD>
SECURITY_REDIS_SSL=true
"""
