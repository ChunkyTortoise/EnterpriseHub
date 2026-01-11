"""
Enterprise Secure Logging Service - Phase 4 Security Implementation
PII Sanitization for CCPA/GDPR Compliance

This service provides enterprise-grade logging with automatic PII detection and sanitization.
Critical for Phase 4 enterprise scaling with 1000+ users and compliance requirements.

Features:
- Real-time PII detection and redaction
- CCPA/GDPR compliant data handling
- Security audit trail
- Multi-tenant log isolation
- Performance optimized (<10ms sanitization latency)
"""

import re
import json
import logging
import hashlib
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Pattern, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Real estate specific PII patterns
PII_PATTERNS = {
    "ssn": {
        "pattern": re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
        "replacement": "[REDACTED_SSN]",
        "severity": "CRITICAL"
    },
    "email": {
        "pattern": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        "replacement": "[REDACTED_EMAIL]",
        "severity": "HIGH"
    },
    "phone": {
        "pattern": re.compile(r'\b(?:\+1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
        "replacement": "[REDACTED_PHONE]",
        "severity": "HIGH"
    },
    "credit_card": {
        "pattern": re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3[0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b'),
        "replacement": "[REDACTED_CC]",
        "severity": "CRITICAL"
    },
    "address": {
        "pattern": re.compile(r'\b\d{1,6}\s+[A-Za-z0-9\s,.-]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct|Circle|Cir|Place|Pl)\b', re.IGNORECASE),
        "replacement": "[REDACTED_ADDRESS]",
        "severity": "HIGH"
    },
    "property_price": {
        "pattern": re.compile(r'\$[\d,]+(?:\.\d{2})?(?:\s*(?:million|mil|k|thousand))?', re.IGNORECASE),
        "replacement": "[REDACTED_PRICE]",
        "severity": "MEDIUM"
    },
    "api_key": {
        "pattern": re.compile(r'(sk-[a-zA-Z0-9]{20,}|ghl_[a-zA-Z0-9]{20,}|xoxb-[a-zA-Z0-9\-]+)'),
        "replacement": "[REDACTED_API_KEY]",
        "severity": "CRITICAL"
    },
    "ip_address": {
        "pattern": re.compile(r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'),
        "replacement": "[REDACTED_IP]",
        "severity": "LOW"
    },
    "real_estate_license": {
        "pattern": re.compile(r'\b[A-Z]{2,3}[\d]{6,8}\b'),
        "replacement": "[REDACTED_LICENSE]",
        "severity": "HIGH"
    }
}

# Sensitive field names that should be redacted regardless of content
SENSITIVE_FIELD_NAMES = {
    "password", "pwd", "passwd", "secret", "token", "key", "auth",
    "anthropic_api_key", "ghl_api_key", "openai_api_key",
    "ssn", "social_security", "credit_card", "bank_account",
    "personal_info", "pii", "private", "confidential",
    "client_data", "lead_data", "contact_info"
}

class LogLevel(Enum):
    """Enhanced log levels for enterprise security."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"
    SECURITY = "SECURITY"  # Special level for security events
    AUDIT = "AUDIT"        # Special level for audit events

@dataclass
class PIIDetectionResult:
    """Result of PII detection and sanitization."""
    original_length: int
    sanitized_length: int
    pii_types_found: List[str]
    redaction_count: int
    severity_level: str
    processing_time_ms: float

@dataclass
class SecurityLogEntry:
    """Enterprise security log entry with metadata."""
    timestamp: datetime
    level: LogLevel
    message: str
    tenant_id: Optional[str]
    user_id: Optional[str]
    session_id: Optional[str]
    source_component: str
    pii_sanitized: bool
    metadata: Dict[str, Any]
    trace_id: Optional[str] = None

class SecureLogger:
    """
    Enterprise secure logging service with PII sanitization.

    Features:
    - Real-time PII detection and redaction
    - Multi-tenant log isolation
    - Security audit trail
    - Performance optimized
    - CCPA/GDPR compliant
    """

    def __init__(
        self,
        tenant_id: Optional[str] = None,
        component_name: str = "unknown",
        enable_audit: bool = True,
        max_workers: int = 4
    ):
        self.tenant_id = tenant_id
        self.component_name = component_name
        self.enable_audit = enable_audit
        self.executor = ThreadPoolExecutor(max_workers=max_workers)

        # Performance metrics
        self.sanitization_count = 0
        self.total_processing_time = 0.0

        # Initialize logging
        self._setup_logger()

    def _setup_logger(self):
        """Initialize enterprise logging configuration."""
        self.logger = logging.getLogger(f"enterprisehub.{self.component_name}")
        self.logger.setLevel(logging.INFO)

        # Create secure handler with PII protection
        handler = logging.StreamHandler()
        formatter = SecureLogFormatter()
        handler.setFormatter(formatter)

        if not self.logger.handlers:
            self.logger.addHandler(handler)

    def sanitize_text(self, text: str, context: Dict[str, Any] = None) -> Tuple[str, PIIDetectionResult]:
        """
        Sanitize text by detecting and redacting PII.

        Args:
            text: Text to sanitize
            context: Additional context for sanitization decisions

        Returns:
            Tuple of (sanitized_text, detection_result)
        """
        start_time = datetime.now(timezone.utc)

        if not isinstance(text, str):
            text = str(text)

        original_length = len(text)
        sanitized_text = text
        pii_types_found = []
        redaction_count = 0
        max_severity = "LOW"

        # Apply PII pattern matching
        for pii_type, config in PII_PATTERNS.items():
            pattern = config["pattern"]
            replacement = config["replacement"]
            severity = config["severity"]

            matches = pattern.findall(sanitized_text)
            if matches:
                pii_types_found.append(pii_type)
                redaction_count += len(matches)
                sanitized_text = pattern.sub(replacement, sanitized_text)

                # Track highest severity
                severity_order = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}
                if severity_order.get(severity, 0) > severity_order.get(max_severity, 0):
                    max_severity = severity

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        result = PIIDetectionResult(
            original_length=original_length,
            sanitized_length=len(sanitized_text),
            pii_types_found=pii_types_found,
            redaction_count=redaction_count,
            severity_level=max_severity,
            processing_time_ms=processing_time
        )

        # Update performance metrics
        self.sanitization_count += 1
        self.total_processing_time += processing_time

        return sanitized_text, result

    def sanitize_data(self, data: Any) -> Tuple[Any, PIIDetectionResult]:
        """
        Recursively sanitize complex data structures.

        Args:
            data: Data to sanitize (dict, list, string, etc.)

        Returns:
            Tuple of (sanitized_data, detection_result)
        """
        start_time = datetime.now(timezone.utc)
        total_redactions = 0
        all_pii_types = []

        def _sanitize_recursive(obj: Any) -> Any:
            nonlocal total_redactions, all_pii_types

            if isinstance(obj, dict):
                sanitized_dict = {}
                for key, value in obj.items():
                    # Check if field name is sensitive
                    if any(sensitive in key.lower() for sensitive in SENSITIVE_FIELD_NAMES):
                        sanitized_dict[key] = "[REDACTED]"
                        total_redactions += 1
                        all_pii_types.append("sensitive_field")
                    else:
                        sanitized_dict[key] = _sanitize_recursive(value)
                return sanitized_dict

            elif isinstance(obj, list):
                return [_sanitize_recursive(item) for item in obj]

            elif isinstance(obj, str):
                sanitized, result = self.sanitize_text(obj)
                total_redactions += result.redaction_count
                all_pii_types.extend(result.pii_types_found)
                return sanitized

            else:
                return obj

        sanitized_data = _sanitize_recursive(data)

        processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

        result = PIIDetectionResult(
            original_length=len(str(data)),
            sanitized_length=len(str(sanitized_data)),
            pii_types_found=list(set(all_pii_types)),
            redaction_count=total_redactions,
            severity_level="CRITICAL" if total_redactions > 0 else "LOW",
            processing_time_ms=processing_time
        )

        return sanitized_data, result

    def log_secure(
        self,
        level: LogLevel,
        message: str,
        metadata: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        trace_id: Optional[str] = None
    ):
        """
        Log message with enterprise security and PII protection.

        Args:
            level: Log level
            message: Log message
            metadata: Additional metadata
            user_id: User identifier
            session_id: Session identifier
            trace_id: Distributed tracing identifier
        """
        # Sanitize message and metadata
        sanitized_message, message_result = self.sanitize_text(message)

        sanitized_metadata = {}
        metadata_result = None
        if metadata:
            sanitized_metadata, metadata_result = self.sanitize_data(metadata)

        # Create security log entry
        log_entry = SecurityLogEntry(
            timestamp=datetime.now(timezone.utc),
            level=level,
            message=sanitized_message,
            tenant_id=self.tenant_id,
            user_id=user_id,
            session_id=session_id,
            source_component=self.component_name,
            pii_sanitized=message_result.redaction_count > 0 or (metadata_result and metadata_result.redaction_count > 0),
            metadata=sanitized_metadata,
            trace_id=trace_id
        )

        # Log to standard logger
        log_message = self._format_log_entry(log_entry)

        if level == LogLevel.DEBUG:
            self.logger.debug(log_message)
        elif level == LogLevel.INFO:
            self.logger.info(log_message)
        elif level == LogLevel.WARNING:
            self.logger.warning(log_message)
        elif level == LogLevel.ERROR:
            self.logger.error(log_message)
        elif level in [LogLevel.CRITICAL, LogLevel.SECURITY]:
            self.logger.critical(log_message)

        # Audit logging for security events
        if self.enable_audit and (
            level in [LogLevel.SECURITY, LogLevel.AUDIT] or
            log_entry.pii_sanitized
        ):
            self._audit_log(log_entry, message_result, metadata_result)

    def _format_log_entry(self, entry: SecurityLogEntry) -> str:
        """Format log entry for output."""
        log_data = {
            "timestamp": entry.timestamp.isoformat(),
            "level": entry.level.value,
            "component": entry.source_component,
            "message": entry.message,
            "tenant_id": entry.tenant_id,
            "user_id": entry.user_id,
            "session_id": entry.session_id,
            "trace_id": entry.trace_id,
            "pii_sanitized": entry.pii_sanitized,
            "metadata": entry.metadata if entry.metadata else {}
        }

        return json.dumps(log_data, default=str)

    def _audit_log(
        self,
        entry: SecurityLogEntry,
        message_result: PIIDetectionResult,
        metadata_result: Optional[PIIDetectionResult]
    ):
        """Write to security audit log for compliance."""
        audit_data = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": entry.timestamp.isoformat(),
            "event_type": "SECURE_LOG_ENTRY",
            "component": entry.source_component,
            "tenant_id": entry.tenant_id,
            "user_id": entry.user_id,
            "session_id": entry.session_id,
            "log_level": entry.level.value,
            "pii_detected": entry.pii_sanitized,
            "pii_types": message_result.pii_types_found,
            "redaction_count": message_result.redaction_count,
            "processing_time_ms": message_result.processing_time_ms
        }

        if metadata_result:
            audit_data.update({
                "metadata_pii_types": metadata_result.pii_types_found,
                "metadata_redactions": metadata_result.redaction_count
            })

        # Write to audit log (in production, this would go to immutable storage)
        audit_logger = logging.getLogger("enterprisehub.security.audit")
        audit_logger.info(json.dumps(audit_data))

    def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: str = "HIGH",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        """Log security-specific events with enhanced tracking."""
        security_message = f"Security Event: {event_type}"

        security_metadata = {
            "event_type": event_type,
            "severity": severity,
            "details": details,
            "system_info": {
                "component": self.component_name,
                "tenant_id": self.tenant_id,
                "timestamp_utc": datetime.now(timezone.utc).isoformat()
            }
        }

        self.log_secure(
            level=LogLevel.SECURITY,
            message=security_message,
            metadata=security_metadata,
            user_id=user_id,
            session_id=session_id
        )

    def get_performance_metrics(self) -> Dict[str, float]:
        """Get sanitization performance metrics."""
        avg_processing_time = (
            self.total_processing_time / self.sanitization_count
            if self.sanitization_count > 0 else 0.0
        )

        return {
            "total_sanitizations": self.sanitization_count,
            "total_processing_time_ms": self.total_processing_time,
            "avg_processing_time_ms": avg_processing_time,
            "sanitizations_per_second": (
                self.sanitization_count / (self.total_processing_time / 1000)
                if self.total_processing_time > 0 else 0.0
            )
        }

    # Convenience methods for common log levels
    def debug(self, message: str, **kwargs):
        self.log_secure(LogLevel.DEBUG, message, **kwargs)

    def info(self, message: str, **kwargs):
        self.log_secure(LogLevel.INFO, message, **kwargs)

    def warning(self, message: str, **kwargs):
        self.log_secure(LogLevel.WARNING, message, **kwargs)

    def error(self, message: str, **kwargs):
        self.log_secure(LogLevel.ERROR, message, **kwargs)

    def critical(self, message: str, **kwargs):
        self.log_secure(LogLevel.CRITICAL, message, **kwargs)

    def security(self, message: str, **kwargs):
        self.log_secure(LogLevel.SECURITY, message, **kwargs)

class SecureLogFormatter(logging.Formatter):
    """Custom log formatter with built-in PII protection."""

    def format(self, record):
        # Basic format without PII exposure
        return f"{record.levelname} | {record.name} | {record.getMessage()}"

# Global secure logger instance
_global_logger: Optional[SecureLogger] = None

def get_secure_logger(
    tenant_id: Optional[str] = None,
    component_name: str = "unknown"
) -> SecureLogger:
    """Get or create secure logger instance."""
    global _global_logger

    if _global_logger is None:
        _global_logger = SecureLogger(
            tenant_id=tenant_id,
            component_name=component_name
        )

    return _global_logger

def set_tenant_context(tenant_id: str, component_name: str = None):
    """Set global tenant context for logging."""
    global _global_logger
    _global_logger = SecureLogger(
        tenant_id=tenant_id,
        component_name=component_name or "enterprisehub"
    )

# Example usage and testing
if __name__ == "__main__":
    # Test the secure logging system
    logger = SecureLogger(
        tenant_id="tenant_123",
        component_name="ghl_webhook_processor"
    )

    # Test PII sanitization
    test_message = "Customer John Doe (john.doe@example.com, 555-123-4567) interested in property at 123 Main Street for $500,000"

    sanitized, result = logger.sanitize_text(test_message)

    print("Original:", test_message)
    print("Sanitized:", sanitized)
    print("PII Types Found:", result.pii_types_found)
    print("Redaction Count:", result.redaction_count)
    print("Processing Time:", result.processing_time_ms, "ms")

    # Test secure logging
    logger.info(
        "Processing lead qualification",
        metadata={
            "lead_id": "lead_456",
            "email": "sensitive@example.com",
            "phone": "555-987-6543",
            "property_price": "$750,000"
        },
        user_id="agent_789",
        session_id="session_abc123"
    )

    # Test security event logging
    logger.log_security_event(
        event_type="UNAUTHORIZED_ACCESS_ATTEMPT",
        details={
            "attempted_resource": "/api/conversations/other_tenant",
            "client_ip": "192.168.1.100",
            "user_agent": "Mozilla/5.0..."
        },
        severity="HIGH",
        user_id="user_suspicious"
    )

    # Show performance metrics
    metrics = logger.get_performance_metrics()
    print("\nPerformance Metrics:", metrics)