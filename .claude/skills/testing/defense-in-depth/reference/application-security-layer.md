# Layer 5: Application Security Layer

## Complete Implementation Reference

This layer provides runtime security monitoring, anomaly detection, and comprehensive logging.

### Security Monitoring and Anomaly Detection

```python
"""
Application security layer with monitoring and anomaly detection.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from collections import defaultdict, deque
import hashlib
import json
from enum import Enum


class SecurityEventType(Enum):
    """Types of security events."""
    AUTH_FAILURE = "auth_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_BREACH_ATTEMPT = "data_breach_attempt"


class SecurityEvent:
    """Security event data structure."""

    def __init__(
        self,
        event_type: SecurityEventType,
        severity: ValidationSeverity,
        user_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Optional[Dict] = None
    ):
        self.event_type = event_type
        self.severity = severity
        self.user_id = user_id
        self.ip_address = ip_address
        self.details = details or {}
        self.timestamp = datetime.now()
        self.event_id = self._generate_event_id()

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        data = f"{self.timestamp}{self.event_type}{self.user_id}".encode()
        return hashlib.sha256(data).hexdigest()[:16]

    def to_dict(self) -> Dict:
        """Convert to dictionary for logging."""
        return {
            'event_id': self.event_id,
            'event_type': self.event_type.value,
            'severity': self.severity.value,
            'user_id': self.user_id,
            'ip_address': self.ip_address,
            'details': self.details,
            'timestamp': self.timestamp.isoformat()
        }


class ApplicationSecurityLayer:
    """Runtime security monitoring and enforcement."""

    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.security_events = deque(maxlen=10000)  # Keep last 10k events
        self.user_activity = defaultdict(list)
        self.ip_activity = defaultdict(list)
        self.alert_handlers = []

    def log_security_event(self, event: SecurityEvent):
        """Log security event with alerting."""
        # Add to event log
        self.security_events.append(event)

        # Track by user and IP
        if event.user_id:
            self.user_activity[event.user_id].append(event)
        if event.ip_address:
            self.ip_activity[event.ip_address].append(event)

        # Trigger alerts for critical events
        if event.severity == ValidationSeverity.CRITICAL:
            self._trigger_alert(event)

        # Check for patterns
        self._detect_attack_patterns(event)

    def _trigger_alert(self, event: SecurityEvent):
        """Trigger security alerts."""
        for handler in self.alert_handlers:
            try:
                handler(event)
            except Exception as e:
                # Don't let alert failures affect security logging
                print(f"Alert handler failed: {e}")

    def _detect_attack_patterns(self, event: SecurityEvent):
        """Detect attack patterns from multiple events."""
        # Pattern 1: Repeated auth failures
        if event.event_type == SecurityEventType.AUTH_FAILURE:
            recent_failures = self._get_recent_events(
                event.user_id or event.ip_address,
                SecurityEventType.AUTH_FAILURE,
                minutes=10
            )
            if len(recent_failures) >= 5:
                self._trigger_alert(SecurityEvent(
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ValidationSeverity.CRITICAL,
                    user_id=event.user_id,
                    ip_address=event.ip_address,
                    details={'pattern': 'brute_force_attempt', 'attempts': len(recent_failures)}
                ))

        # Pattern 2: Multiple injection attempts
        injection_types = [
            SecurityEventType.SQL_INJECTION_ATTEMPT,
            SecurityEventType.XSS_ATTEMPT
        ]
        if event.event_type in injection_types:
            recent_injections = []
            for inj_type in injection_types:
                recent_injections.extend(
                    self._get_recent_events(event.ip_address, inj_type, minutes=5)
                )
            if len(recent_injections) >= 3:
                self._trigger_alert(SecurityEvent(
                    SecurityEventType.SUSPICIOUS_ACTIVITY,
                    ValidationSeverity.CRITICAL,
                    ip_address=event.ip_address,
                    details={'pattern': 'injection_attack', 'attempts': len(recent_injections)}
                ))

    def _get_recent_events(
        self,
        identifier: str,
        event_type: SecurityEventType,
        minutes: int = 10
    ) -> List[SecurityEvent]:
        """Get recent events for pattern detection."""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        events = self.user_activity.get(identifier, []) + self.ip_activity.get(identifier, [])
        return [
            e for e in events
            if e.event_type == event_type and e.timestamp > cutoff
        ]

    def check_user_permissions(
        self,
        user_id: str,
        resource: str,
        action: str,
        user_permissions: List[str]
    ) -> ValidationResult:
        """Multi-layer permission checking."""
        errors = []
        warnings = []

        # Layer 1: Check basic permission format
        required_permission = f"{resource}:{action}"

        # Layer 2: Direct permission match
        if required_permission in user_permissions:
            return ValidationResult(True, errors, warnings)

        # Layer 3: Wildcard permission match
        wildcard_permission = f"{resource}:*"
        if wildcard_permission in user_permissions:
            return ValidationResult(True, errors, warnings)

        # Layer 4: Admin override
        if "admin:*" in user_permissions:
            warnings.append("Access granted via admin override")
            return ValidationResult(True, errors, warnings)

        # Layer 5: Log unauthorized access attempt
        self.log_security_event(SecurityEvent(
            SecurityEventType.UNAUTHORIZED_ACCESS,
            ValidationSeverity.WARNING,
            user_id=user_id,
            details={
                'resource': resource,
                'action': action,
                'required_permission': required_permission
            }
        ))

        errors.append(f"Permission denied: {required_permission}")
        return ValidationResult(False, errors, warnings)

    def detect_anomalous_behavior(
        self,
        user_id: str,
        current_behavior: Dict[str, Any]
    ) -> ValidationResult:
        """Detect anomalous user behavior."""
        errors = []
        warnings = []

        # Layer 1: Get user's historical behavior
        historical_behavior = self._get_user_behavior_profile(user_id)

        # Layer 2: Check for unusual access patterns
        if current_behavior.get('requests_per_minute', 0) > historical_behavior.get('avg_rpm', 0) * 5:
            warnings.append("Unusual request rate detected")

        # Layer 3: Check for unusual resource access
        accessed_resources = current_behavior.get('resources', [])
        typical_resources = historical_behavior.get('typical_resources', [])
        unusual_resources = [r for r in accessed_resources if r not in typical_resources]

        if len(unusual_resources) > 5:
            warnings.append(f"Accessing unusual resources: {unusual_resources}")

        # Layer 4: Check for suspicious time patterns
        current_hour = datetime.now().hour
        typical_hours = historical_behavior.get('typical_hours', [])
        if typical_hours and current_hour not in typical_hours:
            warnings.append(f"Access at unusual time: {current_hour}:00")

        # Layer 5: Geographic anomaly
        if current_behavior.get('location') != historical_behavior.get('typical_location'):
            warnings.append("Access from unusual location")

        # Log if anomalies detected
        if warnings:
            self.log_security_event(SecurityEvent(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                ValidationSeverity.WARNING,
                user_id=user_id,
                details={'anomalies': warnings, 'behavior': current_behavior}
            ))

        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def _get_user_behavior_profile(self, user_id: str) -> Dict[str, Any]:
        """Get user's historical behavior profile."""
        # This would query actual user behavior data
        # Placeholder implementation
        return {
            'avg_rpm': 10,
            'typical_resources': ['leads', 'properties', 'dashboard'],
            'typical_hours': list(range(9, 18)),  # 9 AM - 6 PM
            'typical_location': 'US'
        }

    def validate_session(
        self,
        session_id: str,
        user_id: str,
        ip_address: str
    ) -> ValidationResult:
        """Multi-layer session validation."""
        errors = []
        warnings = []

        # Layer 1: Check session exists
        session_data = self._get_session(session_id)
        if not session_data:
            errors.append("Invalid session")
            self.log_security_event(SecurityEvent(
                SecurityEventType.AUTH_FAILURE,
                ValidationSeverity.WARNING,
                user_id=user_id,
                ip_address=ip_address,
                details={'reason': 'invalid_session'}
            ))
            return ValidationResult(False, errors, warnings)

        # Layer 2: Check session expiration
        if session_data.get('expires_at') < datetime.now():
            errors.append("Session expired")
            return ValidationResult(False, errors, warnings)

        # Layer 3: Validate user ID matches
        if session_data.get('user_id') != user_id:
            errors.append("Session user mismatch")
            self.log_security_event(SecurityEvent(
                SecurityEventType.UNAUTHORIZED_ACCESS,
                ValidationSeverity.CRITICAL,
                user_id=user_id,
                details={'reason': 'session_hijack_attempt'}
            ))
            return ValidationResult(False, errors, warnings)

        # Layer 4: Check IP consistency (optional)
        if self.config.get('enforce_ip_consistency', False):
            if session_data.get('ip_address') != ip_address:
                warnings.append("IP address changed during session")

        # Layer 5: Update session activity
        self._update_session_activity(session_id)

        return ValidationResult(True, errors, warnings)

    def _get_session(self, session_id: str) -> Optional[Dict]:
        """Get session data."""
        # This would query actual session store
        return None

    def _update_session_activity(self, session_id: str):
        """Update last activity timestamp."""
        # This would update actual session store
        pass
```

### Security Audit Logging

```python
class SecurityAuditLogger:
    """Comprehensive security audit logging."""

    def __init__(self, log_file: str = "security_audit.log"):
        self.log_file = log_file

    def log_audit_event(
        self,
        event_type: str,
        user_id: Optional[str],
        action: str,
        resource: str,
        success: bool,
        details: Optional[Dict] = None
    ):
        """Log security audit event."""
        audit_entry = {
            'timestamp': datetime.now().isoformat(),
            'event_type': event_type,
            'user_id': user_id,
            'action': action,
            'resource': resource,
            'success': success,
            'details': details or {},
            'event_id': hashlib.sha256(
                f"{datetime.now()}{user_id}{action}".encode()
            ).hexdigest()[:16]
        }

        # Write to audit log
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(audit_entry) + '\n')

    def get_audit_trail(
        self,
        user_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[str] = None
    ) -> List[Dict]:
        """Retrieve audit trail with filters."""
        results = []

        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line)

                    # Apply filters
                    if user_id and entry['user_id'] != user_id:
                        continue

                    if event_type and entry['event_type'] != event_type:
                        continue

                    entry_time = datetime.fromisoformat(entry['timestamp'])
                    if start_date and entry_time < start_date:
                        continue
                    if end_date and entry_time > end_date:
                        continue

                    results.append(entry)

                except json.JSONDecodeError:
                    continue

        return results
```

## Best Practices

1. **Log all security events** for audit trails
2. **Monitor for attack patterns** across multiple events
3. **Implement anomaly detection** for unusual behavior
4. **Validate sessions** on every request
5. **Check permissions** at multiple layers
6. **Alert on critical events** immediately
7. **Maintain audit logs** for compliance
8. **Review security events** regularly
