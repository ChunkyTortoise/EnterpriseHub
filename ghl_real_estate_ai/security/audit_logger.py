"""
Enterprise Audit Logging System
Provides comprehensive audit logging for security events, admin actions, and data access
"""

import asyncio
import json
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import logging
from pathlib import Path

import redis.asyncio as redis


class AuditEventType(str, Enum):
    """Types of audit events"""
    # Security Events
    LOGIN_ATTEMPT = "login_attempt"
    LOGIN_SUCCESS = "login_success"
    SUCCESSFUL_LOGIN = "successful_login"
    LOGIN_FAILURE = "login_failure"
    LOGIN_ATTEMPT_INACTIVE_USER = "login_attempt_inactive_user"
    LOGIN_ATTEMPT_LOCKED_USER = "login_attempt_locked_user"
    FAILED_LOGIN_ATTEMPT = "failed_login_attempt"
    LOGOUT = "logout"
    SESSION_EXPIRED = "session_expired"
    SESSION_REVOKED = "session_revoked"
    PASSWORD_CHANGED = "password_changed"
    MFA_ENABLED = "mfa_enabled"
    MFA_DISABLED = "mfa_disabled"
    MFA_VERIFICATION_FAILED = "mfa_verification_failed"
    MFA_VERIFICATION_ERROR = "mfa_verification_error"
    ACCOUNT_LOCKED = "account_locked"
    ACCOUNT_UNLOCKED = "account_unlocked"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    AUTHENTICATION_FAILED = "authentication_failed"
    AUTHENTICATION_REQUIRED = "authentication_required"
    AUTHORIZATION_FAILED = "authorization_failed"
    THREAT_DETECTED = "threat_detected"
    BLOCKED_IP_ACCESS = "blocked_ip_access"
    SUSPICIOUS_IP_ACCESS = "suspicious_ip_access"
    INPUT_VALIDATION_FAILED = "input_validation_failed"
    REQUEST_FAILED = "request_failed"
    
    # Admin Actions
    USER_CREATED = "user_created"
    USER_UPDATED = "user_updated"
    USER_DELETED = "user_deleted"
    ROLE_CREATED = "role_created"
    ROLE_UPDATED = "role_updated"
    ROLE_DELETED = "role_deleted"
    PERMISSION_GRANTED = "permission_granted"
    PERMISSION_REVOKED = "permission_revoked"
    SYSTEM_CONFIG_CHANGED = "system_config_changed"
    BACKUP_CREATED = "backup_created"
    BACKUP_RESTORED = "backup_restored"
    TOKEN_REFRESHED = "token_refreshed"
    ALL_SESSIONS_REVOKED = "all_sessions_revoked"
    ROLES_IMPORTED = "roles_imported"
    
    # Data Access
    DATA_ACCESSED = "data_accessed"
    DATA_EXPORTED = "data_exported"
    DATA_IMPORTED = "data_imported"
    DATA_MODIFIED = "data_modified"
    DATA_DELETED = "data_deleted"
    BULK_OPERATION = "bulk_operation"
    SENSITIVE_DATA_ACCESS = "sensitive_data_access"
    
    # API Events
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    WEBHOOK_RECEIVED = "webhook_received"
    API_RATE_LIMITED = "api_rate_limited"
    API_ERROR = "api_error"
    
    # AI/ML Events
    AI_MODEL_USED = "ai_model_used"
    CLAUDE_REQUEST = "claude_request"
    LEAD_SCORED = "lead_scored"
    PREDICTION_GENERATED = "prediction_generated"
    
    # System Events
    SYSTEM_STARTED = "system_started"
    SYSTEM_STOPPED = "system_stopped"
    ERROR_OCCURRED = "error_occurred"
    PERFORMANCE_ALERT = "performance_alert"


class AuditSeverity(str, Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Audit event data structure"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: datetime
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    resource: Optional[str] = None
    action: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    duration_ms: Optional[float] = None
    request_id: Optional[str] = None
    location_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "session_id": self.session_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "resource": self.resource,
            "action": self.action,
            "details": self.details,
            "success": self.success,
            "duration_ms": self.duration_ms,
            "request_id": self.request_id,
            "location_id": self.location_id
        }
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str, ensure_ascii=False)


class AuditLogger:
    """
    Enterprise audit logging system with multiple storage backends and real-time monitoring
    """
    
    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        log_file_path: Optional[str] = None,
        enable_console_logging: bool = True,
        buffer_size: int = 100,
        flush_interval: int = 30
    ):
        self.redis = redis_client
        self.log_file_path = Path(log_file_path) if log_file_path else None
        self.enable_console_logging = enable_console_logging
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        
        # Event buffer for batch processing
        self._event_buffer: List[AuditEvent] = []
        self._buffer_lock = asyncio.Lock()
        
        # Metrics and monitoring
        self._event_counts: Dict[str, int] = {}
        self._severity_counts: Dict[str, int] = {}
        
        # Setup logging
        self._setup_logging()
        
        # Start background flush task
        self._flush_task = asyncio.create_task(self._periodic_flush())
    
    def _setup_logging(self):
        """Setup standard Python logging for audit events"""
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Console handler
        if self.enable_console_logging:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            formatter = logging.Formatter(
                '%(asctime)s - AUDIT - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if self.log_file_path:
            self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(self.log_file_path)
            file_handler.setLevel(logging.INFO)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        success: bool = True,
        duration_ms: Optional[float] = None,
        request_id: Optional[str] = None,
        location_id: Optional[str] = None
    ) -> str:
        """
        Log an audit event
        
        Returns:
            str: Event ID
        """
        # Ensure severity is AuditSeverity enum
        if isinstance(severity, str):
            try:
                severity = AuditSeverity(severity.lower())
            except ValueError:
                severity = AuditSeverity.MEDIUM

        # Generate event ID
        event_id = self._generate_event_id(event_type, user_id, session_id)
        
        # Create event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
            user_agent=user_agent,
            resource=resource,
            action=action,
            details=details or {},
            success=success,
            duration_ms=duration_ms,
            request_id=request_id,
            location_id=location_id
        )
        
        # Add to buffer
        async with self._buffer_lock:
            self._event_buffer.append(event)
            
            # Update metrics
            event_type_val = event_type.value if hasattr(event_type, "value") else str(event_type)
            severity_val = severity.value if hasattr(severity, "value") else str(severity)
            
            self._event_counts[event_type_val] = self._event_counts.get(event_type_val, 0) + 1
            self._severity_counts[severity_val] = self._severity_counts.get(severity_val, 0) + 1
            
            # Immediate flush for critical events
            if severity == AuditSeverity.CRITICAL:
                await self._flush_events([event])
                self._event_buffer.remove(event)
            elif len(self._event_buffer) >= self.buffer_size:
                await self._flush_buffer()
        
        # Console logging
        self._log_to_console(event)
        
        return event_id
    
    async def log_security_event(
        self,
        event_type: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.HIGH,
        **kwargs
    ) -> str:
        """Log security-related events"""
        return await self.log_event(
            event_type=AuditEventType(event_type),
            severity=severity,
            resource="security",
            action=event_type,
            details=details,
            **kwargs
        )
    
    async def log_admin_action(
        self,
        action: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log administrative actions"""
        return await self.log_event(
            event_type=AuditEventType(action),
            severity=AuditSeverity.MEDIUM,
            resource="admin",
            action=action,
            details=details,
            user_id=user_id,
            **kwargs
        )
    
    async def log_data_access(
        self,
        resource: str,
        action: str,
        details: Dict[str, Any],
        user_id: str,
        **kwargs
    ) -> str:
        """Log data access events"""
        # Determine if this is sensitive data
        sensitive_resources = ["users", "contacts", "financial", "personal"]
        is_sensitive = any(sens in resource.lower() for sens in sensitive_resources)
        
        event_type = AuditEventType.SENSITIVE_DATA_ACCESS if is_sensitive else AuditEventType.DATA_ACCESSED
        severity = AuditSeverity.HIGH if is_sensitive else AuditSeverity.MEDIUM
        
        return await self.log_event(
            event_type=event_type,
            severity=severity,
            resource=resource,
            action=action,
            details=details,
            user_id=user_id,
            **kwargs
        )
    
    async def log_api_event(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        duration_ms: float,
        user_id: Optional[str] = None,
        api_key: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log API usage events"""
        success = 200 <= status_code < 400
        severity = AuditSeverity.LOW if success else AuditSeverity.MEDIUM
        
        details = {
            "endpoint": endpoint,
            "method": method,
            "status_code": status_code,
            "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:16] if api_key else None
        }
        
        return await self.log_event(
            event_type=AuditEventType.DATA_ACCESSED,
            severity=severity,
            resource="api",
            action=f"{method} {endpoint}",
            details=details,
            user_id=user_id,
            success=success,
            duration_ms=duration_ms,
            **kwargs
        )
    
    async def log_ai_event(
        self,
        model: str,
        operation: str,
        tokens_used: int,
        success: bool = True,
        user_id: Optional[str] = None,
        **kwargs
    ) -> str:
        """Log AI/ML events"""
        details = {
            "model": model,
            "operation": operation,
            "tokens_used": tokens_used
        }
        
        return await self.log_event(
            event_type=AuditEventType.AI_MODEL_USED,
            severity=AuditSeverity.LOW,
            resource="ai",
            action=operation,
            details=details,
            user_id=user_id,
            success=success,
            **kwargs
        )
    
    async def log_error(
        self,
        error_type: str,
        details: Dict[str, Any],
        severity: AuditSeverity = AuditSeverity.MEDIUM,
        **kwargs
    ) -> str:
        """Log error events"""
        return await self.log_event(
            event_type=AuditEventType.ERROR_OCCURRED,
            severity=severity,
            resource="system",
            action=error_type,
            details=details,
            success=False,
            **kwargs
        )
    
    async def search_events(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        event_types: Optional[List[AuditEventType]] = None,
        user_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        resource: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[AuditEvent]:
        """Search audit events with filters"""
        if not self.redis:
            return []
        
        # Build search criteria
        criteria = {}
        if start_time:
            criteria["start_time"] = start_time.isoformat()
        if end_time:
            criteria["end_time"] = end_time.isoformat()
        if event_types:
            criteria["event_types"] = [et.value for et in event_types]
        if user_id:
            criteria["user_id"] = user_id
        if severity:
            criteria["severity"] = severity.value
        if resource:
            criteria["resource"] = resource
        
        # Search in Redis (simplified implementation)
        # In production, you might want to use Elasticsearch or similar
        events = []
        
        try:
            # Get event keys from Redis
            pattern = "audit:event:*"
            keys = await self.redis.keys(pattern)
            
            for key in keys[offset:offset + limit]:
                event_data = await self.redis.get(key)
                if event_data:
                    event_dict = json.loads(event_data)
                    
                    # Apply filters
                    if self._matches_criteria(event_dict, criteria):
                        events.append(self._dict_to_event(event_dict))
            
            # Sort by timestamp (newest first)
            events.sort(key=lambda e: e.timestamp, reverse=True)
            
        except Exception as e:
            self.logger.error(f"Error searching audit events: {e}")
        
        return events[:limit]
    
    async def get_event_statistics(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get audit event statistics"""
        stats = {
            "total_events": sum(self._event_counts.values()),
            "event_types": dict(self._event_counts),
            "severity_distribution": dict(self._severity_counts),
            "events_per_hour": {},
            "top_users": {},
            "top_resources": {},
            "error_rate": 0.0
        }
        
        # Calculate error rate
        total_events = stats["total_events"]
        if total_events > 0:
            error_events = sum(
                count for event_type, count in self._event_counts.items()
                if "error" in event_type.lower() or "failed" in event_type.lower()
            )
            stats["error_rate"] = error_events / total_events
        
        return stats
    
    async def export_events(
        self,
        start_time: datetime,
        end_time: datetime,
        format_type: str = "json"
    ) -> str:
        """Export audit events for compliance or analysis"""
        events = await self.search_events(
            start_time=start_time,
            end_time=end_time,
            limit=10000  # Large limit for export
        )
        
        if format_type.lower() == "json":
            return json.dumps([event.to_dict() for event in events], indent=2, default=str)
        elif format_type.lower() == "csv":
            # CSV export implementation
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Headers
            headers = ["timestamp", "event_type", "severity", "user_id", "resource", "action", "success", "details"]
            writer.writerow(headers)
            
            # Data
            for event in events:
                writer.writerow([
                    event.timestamp.isoformat(),
                    event.event_type.value,
                    event.severity.value,
                    event.user_id or "",
                    event.resource or "",
                    event.action or "",
                    event.success,
                    json.dumps(event.details)
                ])
            
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported export format: {format_type}")
    
    def _generate_event_id(self, event_type: AuditEventType, user_id: Optional[str], session_id: Optional[str]) -> str:
        """Generate unique event ID"""
        timestamp = str(int(time.time() * 1000000))  # microseconds
        components = [timestamp, event_type.value]
        
        if user_id:
            components.append(user_id[:8])
        if session_id:
            components.append(session_id[:8])
        
        base_string = ":".join(components)
        return hashlib.sha256(base_string.encode()).hexdigest()[:16]
    
    def _log_to_console(self, event: AuditEvent):
        """Log event to console/file logger"""
        log_level = {
            AuditSeverity.LOW: logging.INFO,
            AuditSeverity.MEDIUM: logging.WARNING,
            AuditSeverity.HIGH: logging.ERROR,
            AuditSeverity.CRITICAL: logging.CRITICAL
        }.get(event.severity, logging.INFO)
        
        message = f"[{event.event_type.value}] {event.action or 'N/A'}"
        if event.user_id:
            message += f" (user: {event.user_id})"
        if event.resource:
            message += f" (resource: {event.resource})"
        if not event.success:
            message += " [FAILED]"
        
        self.logger.log(log_level, message)
    
    async def _flush_buffer(self):
        """Flush event buffer to persistent storage"""
        if not self._event_buffer:
            return
        
        events_to_flush = self._event_buffer.copy()
        self._event_buffer.clear()
        
        await self._flush_events(events_to_flush)
    
    async def _flush_events(self, events: List[AuditEvent]):
        """Flush events to all configured storage backends"""
        tasks = []
        
        # Redis storage
        if self.redis:
            tasks.append(self._store_to_redis(events))
        
        # File storage
        if self.log_file_path:
            tasks.append(self._store_to_file(events))
        
        # Execute all storage operations concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _store_to_redis(self, events: List[AuditEvent]):
        """Store events to Redis"""
        try:
            async with self.redis.pipeline() as pipe:
                for event in events:
                    key = f"audit:event:{event.event_id}"
                    pipe.set(key, event.to_json(), ex=86400 * 30)  # 30 days TTL
                    
                    # Add to time-series for quick queries
                    timestamp_key = f"audit:timeline:{event.timestamp.strftime('%Y-%m-%d')}"
                    pipe.zadd(timestamp_key, {event.event_id: event.timestamp.timestamp()})
                    pipe.expire(timestamp_key, 86400 * 30)
                
                await pipe.execute()
                
        except Exception as e:
            self.logger.error(f"Failed to store events to Redis: {e}")
    
    async def _store_to_file(self, events: List[AuditEvent]):
        """Store events to file"""
        try:
            with open(self.log_file_path, 'a', encoding='utf-8') as f:
                for event in events:
                    f.write(event.to_json() + '\n')
        except Exception as e:
            self.logger.error(f"Failed to store events to file: {e}")
    
    async def _periodic_flush(self):
        """Periodically flush event buffer"""
        while True:
            try:
                await asyncio.sleep(self.flush_interval)
                async with self._buffer_lock:
                    if self._event_buffer:
                        await self._flush_buffer()
            except Exception as e:
                self.logger.error(f"Error in periodic flush: {e}")
    
    def _matches_criteria(self, event_dict: Dict, criteria: Dict) -> bool:
        """Check if event matches search criteria"""
        # Implement filtering logic
        if "event_types" in criteria:
            if event_dict["event_type"] not in criteria["event_types"]:
                return False
        
        if "user_id" in criteria:
            if event_dict["user_id"] != criteria["user_id"]:
                return False
        
        if "severity" in criteria:
            if event_dict["severity"] != criteria["severity"]:
                return False
        
        if "resource" in criteria:
            if event_dict["resource"] != criteria["resource"]:
                return False
        
        # Time range filtering
        if "start_time" in criteria or "end_time" in criteria:
            event_time = datetime.fromisoformat(event_dict["timestamp"].replace('Z', '+00:00'))
            
            if "start_time" in criteria:
                start_time = datetime.fromisoformat(criteria["start_time"])
                if event_time < start_time:
                    return False
            
            if "end_time" in criteria:
                end_time = datetime.fromisoformat(criteria["end_time"])
                if event_time > end_time:
                    return False
        
        return True
    
    def _dict_to_event(self, event_dict: Dict) -> AuditEvent:
        """Convert dictionary back to AuditEvent"""
        return AuditEvent(
            event_id=event_dict["event_id"],
            event_type=AuditEventType(event_dict["event_type"]),
            severity=AuditSeverity(event_dict["severity"]),
            timestamp=datetime.fromisoformat(event_dict["timestamp"].replace('Z', '+00:00')),
            user_id=event_dict.get("user_id"),
            session_id=event_dict.get("session_id"),
            ip_address=event_dict.get("ip_address"),
            user_agent=event_dict.get("user_agent"),
            resource=event_dict.get("resource"),
            action=event_dict.get("action"),
            details=event_dict.get("details", {}),
            success=event_dict.get("success", True),
            duration_ms=event_dict.get("duration_ms"),
            request_id=event_dict.get("request_id"),
            location_id=event_dict.get("location_id")
        )
    
    async def close(self):
        """Clean shutdown of audit logger"""
        # Cancel flush task
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        
        # Final flush
        async with self._buffer_lock:
            if self._event_buffer:
                await self._flush_buffer()


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def initialize_audit_logger(
    redis_client: Optional[redis.Redis] = None,
    log_file_path: Optional[str] = None,
    **kwargs
) -> AuditLogger:
    """Initialize global audit logger"""
    global _audit_logger
    _audit_logger = AuditLogger(
        redis_client=redis_client,
        log_file_path=log_file_path,
        **kwargs
    )
    return _audit_logger