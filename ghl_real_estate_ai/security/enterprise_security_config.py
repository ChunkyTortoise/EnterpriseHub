#!/usr/bin/env python3
"""
Enterprise Security Configuration - Production Security Standards
Comprehensive security configuration for enterprise deployment.

SECURITY STANDARDS:
1. OWASP compliance
2. GDPR/HIPAA readiness
3. PCI DSS considerations
4. Zero-trust security model
5. Defense in depth
"""

import os
import secrets
import ssl
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Union

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SecurityLevel(Enum):
    """Security levels for different deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    HIGH_SECURITY = "high_security"  # For healthcare/financial clients


class ComplianceStandard(Enum):
    """Supported compliance standards."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    PCI_DSS = "pci_dss"
    SOC2 = "soc2"
    CCPA = "ccpa"


@dataclass
class SecurityHeaders:
    """Security headers configuration."""

    # OWASP recommended headers
    x_content_type_options: str = "nosniff"
    x_frame_options: str = "DENY"
    x_xss_protection: str = "1; mode=block"
    strict_transport_security: str = "max-age=31536000; includeSubDomains; preload"
    referrer_policy: str = "strict-origin-when-cross-origin"

    # Content Security Policy (restrictive by default)
    content_security_policy: str = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "font-src 'self'; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'"
    )

    # Feature Policy / Permissions Policy
    permissions_policy: str = (
        "camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), accelerometer=(), gyroscope=()"
    )

    # Additional security headers
    x_permitted_cross_domain_policies: str = "none"
    x_dns_prefetch_control: str = "off"

    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for FastAPI middleware."""
        return {
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "X-XSS-Protection": self.x_xss_protection,
            "Strict-Transport-Security": self.strict_transport_security,
            "Referrer-Policy": self.referrer_policy,
            "Content-Security-Policy": self.content_security_policy,
            "Permissions-Policy": self.permissions_policy,
            "X-Permitted-Cross-Domain-Policies": self.x_permitted_cross_domain_policies,
            "X-DNS-Prefetch-Control": self.x_dns_prefetch_control,
        }


@dataclass
class CORSConfig:
    """CORS configuration with security controls."""

    # Production allowed origins (strict)
    allowed_origins: List[str] = field(
        default_factory=lambda: ["https://app.gohighlevel.com", "https://*.gohighlevel.com", "https://your-domain.com"]
    )

    # Development additional origins
    development_origins: List[str] = field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:8501", "http://127.0.0.1:8501"]
    )

    allowed_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    allowed_headers: List[str] = field(
        default_factory=lambda: [
            "Accept",
            "Accept-Language",
            "Content-Language",
            "Content-Type",
            "Authorization",
            "X-Requested-With",
            "X-Request-ID",
        ]
    )

    # Security settings
    allow_credentials: bool = True
    max_age: int = 600  # 10 minutes (shorter for security)

    # Forbidden headers that should never be allowed
    forbidden_headers: Set[str] = field(
        default_factory=lambda: {"X-Forwarded-For", "X-Real-IP", "X-Forwarded-Host", "X-Original-URL"}
    )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    # General API rate limits (requests per minute)
    default_rate_limit: int = 100
    authenticated_rate_limit: int = 1000
    admin_rate_limit: int = 5000

    # Burst limits
    burst_multiplier: float = 1.5

    # Authentication specific limits
    login_attempts_per_hour: int = 10
    password_reset_per_hour: int = 5

    # Webhook limits (higher for legitimate traffic)
    webhook_rate_limit: int = 500

    # Time windows
    window_seconds: int = 60

    # Redis key prefixes
    key_prefix: str = "rate_limit:"

    # Whitelist/Blacklist
    whitelist_ips: Set[str] = field(default_factory=set)
    blacklist_ips: Set[str] = field(default_factory=set)


@dataclass
class EncryptionConfig:
    """Encryption and cryptography configuration."""

    # JWT Configuration
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15  # Short for security
    jwt_refresh_token_expire_days: int = 7
    jwt_min_secret_length: int = 64

    # Database encryption
    database_encryption_key_rotation_days: int = 90

    # File encryption (for PII storage)
    file_encryption_algorithm: str = "AES-256-GCM"

    # TLS/SSL Configuration
    tls_version: str = "TLSv1.3"
    ssl_ciphers: List[str] = field(
        default_factory=lambda: [
            "ECDHE-ECDSA-AES256-GCM-SHA384",
            "ECDHE-RSA-AES256-GCM-SHA384",
            "ECDHE-ECDSA-CHACHA20-POLY1305",
            "ECDHE-RSA-CHACHA20-POLY1305",
        ]
    )

    # Key management
    key_rotation_enabled: bool = True
    key_backup_enabled: bool = True

    def get_ssl_context(self) -> ssl.SSLContext:
        """Get SSL context with secure configuration."""
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        context.minimum_version = ssl.TLSVersion.TLSv1_3
        context.set_ciphers(":".join(self.ssl_ciphers))
        return context


@dataclass
class AuditConfig:
    """Audit logging and monitoring configuration."""

    # Audit event types to log
    audit_events: Set[str] = field(
        default_factory=lambda: {
            "authentication_success",
            "authentication_failure",
            "authorization_failure",
            "sensitive_data_access",
            "configuration_change",
            "user_creation",
            "user_deletion",
            "password_change",
            "role_change",
            "webhook_received",
            "api_key_created",
            "api_key_revoked",
            "data_export",
            "security_event",
        }
    )

    # PII fields that should be masked in logs
    pii_fields: Set[str] = field(
        default_factory=lambda: {
            "email",
            "phone",
            "ssn",
            "tax_id",
            "credit_card",
            "bank_account",
            "address",
            "date_of_birth",
            "full_name",
            "first_name",
            "last_name",
        }
    )

    # Log retention
    audit_log_retention_days: int = 2555  # 7 years for compliance

    # Real-time monitoring
    enable_real_time_alerts: bool = True
    alert_threshold_failed_logins: int = 5
    alert_threshold_api_errors: int = 100

    # Integration settings
    siem_integration_enabled: bool = False
    siem_endpoint: Optional[str] = None


@dataclass
class ComplianceConfig:
    """Compliance-specific configuration."""

    enabled_standards: Set[ComplianceStandard] = field(default_factory=lambda: {ComplianceStandard.GDPR})

    # GDPR specific
    gdpr_data_retention_days: int = 1095  # 3 years default
    gdpr_consent_required: bool = True
    gdpr_right_to_erasure_enabled: bool = True

    # HIPAA specific (if healthcare data)
    hipaa_encryption_at_rest: bool = False  # Enable for healthcare
    hipaa_audit_controls: bool = False
    hipaa_access_logging: bool = False

    # PCI DSS (if processing payments)
    pci_dss_enabled: bool = False
    pci_dss_network_segmentation: bool = False
    pci_dss_cardholder_data_protection: bool = False

    # Data classification
    data_classification_enabled: bool = True
    classify_as_sensitive: Set[str] = field(
        default_factory=lambda: {"email", "phone", "address", "financial_data", "health_data", "biometric_data"}
    )


@dataclass
class InputValidationConfig:
    """Input validation and sanitization configuration."""

    # String validation
    max_string_length: int = 10000
    max_field_count: int = 100
    max_nested_depth: int = 10

    # File upload validation
    max_file_size_mb: int = 50
    allowed_file_extensions: Set[str] = field(
        default_factory=lambda: {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".csv", ".txt"}
    )

    # Content validation
    allow_html: bool = False
    allow_javascript: bool = False
    allow_sql_keywords: bool = False

    # Dangerous patterns to block
    blocked_patterns: List[str] = field(
        default_factory=lambda: [
            r"<script[^>]*>",
            r"javascript:",
            r"on\w+\s*=",
            r"expression\s*\(",
            r"@import",
            r"<iframe",
            r"<object",
            r"<embed",
            r"vbscript:",
            r"data:text/html",
        ]
    )

    # SQL injection patterns
    sql_injection_patterns: List[str] = field(
        default_factory=lambda: [
            r"(\b(Union[select, union]|Union[insert, update]|Union[delete, drop]|Union[create, alter]|exec)\b)",
            r"(\b(Union[or, and])\b\s+\d+\s*=\s*\d+)",
            r'(\b(Union[or, and])\b\s+[\'"]\w+[\'"])',
            r"(/\*.*\*/)",
            r"(--[^\n]*)",
            r"(\bxp_\w+)",
            r"(\bsp_\w+)",
        ]
    )


class EnterpriseSecurityConfig:
    """Main enterprise security configuration."""

    def __init__(self, security_level: SecurityLevel = SecurityLevel.PRODUCTION):
        self.security_level = security_level
        self.headers = SecurityHeaders()
        self.cors = CORSConfig()
        self.rate_limiting = RateLimitConfig()
        self.encryption = EncryptionConfig()
        self.audit = AuditConfig()
        self.compliance = ComplianceConfig()
        self.input_validation = InputValidationConfig()

        # Apply security level adjustments
        self._apply_security_level()

    def _apply_security_level(self):
        """Apply security level specific configurations."""
        if self.security_level == SecurityLevel.DEVELOPMENT:
            # Relaxed settings for development
            self.cors.allowed_origins.extend(self.cors.development_origins)
            self.rate_limiting.default_rate_limit = 1000
            self.encryption.jwt_access_token_expire_minutes = 60
            self.audit.enable_real_time_alerts = False

        elif self.security_level == SecurityLevel.STAGING:
            # Production-like but with some relaxations
            self.rate_limiting.default_rate_limit = 200
            self.encryption.jwt_access_token_expire_minutes = 30

        elif self.security_level == SecurityLevel.PRODUCTION:
            # Standard production security
            pass  # Use defaults

        elif self.security_level == SecurityLevel.HIGH_SECURITY:
            # Maximum security for healthcare/financial
            self.headers.content_security_policy = (
                "default-src 'none'; script-src 'self'; style-src 'self'; img-src 'self'; connect-src 'self'"
            )
            self.rate_limiting.default_rate_limit = 50
            self.encryption.jwt_access_token_expire_minutes = 5
            self.compliance.enabled_standards.update(
                {ComplianceStandard.HIPAA, ComplianceStandard.PCI_DSS, ComplianceStandard.SOC2}
            )
            self.compliance.hipaa_encryption_at_rest = True
            self.compliance.hipaa_audit_controls = True
            self.compliance.pci_dss_enabled = True

    def validate_configuration(self) -> List[str]:
        """Validate security configuration and return any issues."""
        issues = []

        # Validate JWT secret
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if not jwt_secret:
            issues.append("JWT_SECRET_KEY environment variable not set")
        elif len(jwt_secret) < self.encryption.jwt_min_secret_length:
            issues.append(f"JWT secret too short (minimum {self.encryption.jwt_min_secret_length} characters)")

        # Validate TLS in production
        if self.security_level in [SecurityLevel.PRODUCTION, SecurityLevel.HIGH_SECURITY]:
            if not os.getenv("TLS_CERT_PATH") or not os.getenv("TLS_KEY_PATH"):
                issues.append("TLS certificates not configured for production")

        # Validate compliance requirements
        if ComplianceStandard.HIPAA in self.compliance.enabled_standards:
            if not self.compliance.hipaa_encryption_at_rest:
                issues.append("HIPAA compliance requires encryption at rest")
            if not self.compliance.hipaa_audit_controls:
                issues.append("HIPAA compliance requires audit controls")

        # Validate CORS in production
        if self.security_level == SecurityLevel.PRODUCTION:
            if "localhost" in str(self.cors.allowed_origins):
                issues.append("localhost origins should not be allowed in production")

        return issues

    def generate_security_report(self) -> Dict[str, Any]:
        """Generate comprehensive security configuration report."""
        issues = self.validate_configuration()

        return {
            "security_level": self.security_level.value,
            "configuration_valid": len(issues) == 0,
            "validation_issues": issues,
            "enabled_standards": [std.value for std in self.compliance.enabled_standards],
            "security_headers_count": len(self.headers.to_dict()),
            "rate_limit_default": self.rate_limiting.default_rate_limit,
            "jwt_expiry_minutes": self.encryption.jwt_access_token_expire_minutes,
            "audit_events_count": len(self.audit.audit_events),
            "blocked_patterns_count": len(self.input_validation.blocked_patterns),
            "timestamp": os.getenv("DEPLOYMENT_TIMESTAMP", "unknown"),
        }


# Factory functions for different environments
def get_development_config() -> EnterpriseSecurityConfig:
    """Get development security configuration."""
    return EnterpriseSecurityConfig(SecurityLevel.DEVELOPMENT)


def get_staging_config() -> EnterpriseSecurityConfig:
    """Get staging security configuration."""
    return EnterpriseSecurityConfig(SecurityLevel.STAGING)


def get_production_config() -> EnterpriseSecurityConfig:
    """Get production security configuration."""
    return EnterpriseSecurityConfig(SecurityLevel.PRODUCTION)


def get_high_security_config() -> EnterpriseSecurityConfig:
    """Get high security configuration for healthcare/financial."""
    return EnterpriseSecurityConfig(SecurityLevel.HIGH_SECURITY)


# Export security configuration
__all__ = [
    "EnterpriseSecurityConfig",
    "SecurityLevel",
    "ComplianceStandard",
    "SecurityHeaders",
    "CORSConfig",
    "RateLimitConfig",
    "EncryptionConfig",
    "AuditConfig",
    "ComplianceConfig",
    "InputValidationConfig",
    "get_development_config",
    "get_staging_config",
    "get_production_config",
    "get_high_security_config",
]
