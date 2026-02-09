"""
Security Monitoring and Incident Response Service

Features:
- Real-time security event monitoring
- Automated threat detection and response
- Audit trail logging with retention
- Security incident alerting
- Performance and security metrics
- Compliance reporting
"""

import asyncio
import json
import time
from collections import defaultdict, deque
from contextlib import asynccontextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import CacheService

logger = get_logger(__name__)


class ThreatLevel(str, Enum):
    """Security threat levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventType(str, Enum):
    """Security event types for monitoring."""

    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM_INTEGRITY = "system_integrity"
    NETWORK_SECURITY = "network_security"
    RATE_LIMITING = "rate_limiting"
    INPUT_VALIDATION = "input_validation"


@dataclass
class SecurityEvent:
    """Security event data structure."""

    event_id: str
    event_type: EventType
    threat_level: ThreatLevel
    timestamp: datetime
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    method: str
    description: str
    details: Dict[str, Any]
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


class SecurityMetrics:
    """Real-time security metrics tracking."""

    def __init__(self):
        self.metrics = {
            "total_events": 0,
            "events_by_type": defaultdict(int),
            "events_by_threat_level": defaultdict(int),
            "blocked_requests": 0,
            "authentication_failures": 0,
            "rate_limit_violations": 0,
            "suspicious_activities": 0,
            "unique_ips": set(),
            "top_threat_sources": defaultdict(int),
            "average_response_time": 0.0,
            "last_reset": datetime.now(timezone.utc),
        }
        self.recent_events = deque(maxlen=1000)  # Keep last 1000 events

    def record_event(self, event: SecurityEvent):
        """Record a security event in metrics."""
        self.metrics["total_events"] += 1
        self.metrics["events_by_type"][event.event_type] += 1
        self.metrics["events_by_threat_level"][event.threat_level] += 1
        self.metrics["unique_ips"].add(event.source_ip)
        self.metrics["top_threat_sources"][event.source_ip] += 1

        # Track specific event types
        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]:
            self.metrics["suspicious_activities"] += 1

        if event.event_type == EventType.AUTHENTICATION and "failed" in event.description:
            self.metrics["authentication_failures"] += 1

        if event.event_type == EventType.RATE_LIMITING:
            self.metrics["rate_limit_violations"] += 1

        self.recent_events.append(event)

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get current security metrics summary."""
        return {
            "total_events": self.metrics["total_events"],
            "events_by_type": dict(self.metrics["events_by_type"]),
            "events_by_threat_level": dict(self.metrics["events_by_threat_level"]),
            "blocked_requests": self.metrics["blocked_requests"],
            "authentication_failures": self.metrics["authentication_failures"],
            "rate_limit_violations": self.metrics["rate_limit_violations"],
            "suspicious_activities": self.metrics["suspicious_activities"],
            "unique_ips_count": len(self.metrics["unique_ips"]),
            "top_threat_sources": dict(
                sorted(self.metrics["top_threat_sources"].items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "last_reset": self.metrics["last_reset"].isoformat(),
            "uptime_hours": (datetime.now(timezone.utc) - self.metrics["last_reset"]).total_seconds() / 3600,
        }


class ThreatDetector:
    """Advanced threat detection engine."""

    def __init__(self):
        self.ip_reputation = defaultdict(int)  # IP reputation scores
        self.failed_attempts = defaultdict(list)  # Failed auth attempts by IP
        self.suspicious_patterns = defaultdict(int)  # Suspicious activity patterns
        self.blocked_ips = set()  # Currently blocked IPs
        self.whitelist_ips = set()  # Whitelisted IPs

    def analyze_event(self, event: SecurityEvent) -> ThreatLevel:
        """Analyze event and determine threat level."""
        threat_score = 0

        # IP reputation analysis
        ip_score = self.ip_reputation.get(event.source_ip, 0)
        if ip_score > 50:
            threat_score += 30

        # Failed authentication analysis
        if event.event_type == EventType.AUTHENTICATION and "failed" in event.description:
            recent_failures = len(
                [
                    attempt
                    for attempt in self.failed_attempts[event.source_ip]
                    if attempt > datetime.now(timezone.utc) - timedelta(minutes=15)
                ]
            )
            self.failed_attempts[event.source_ip].append(datetime.now(timezone.utc))

            if recent_failures > 5:
                threat_score += 40
            elif recent_failures > 3:
                threat_score += 20

        # Rate limiting violations
        if event.event_type == EventType.RATE_LIMITING:
            threat_score += 25

        # SQL injection or XSS attempts
        if event.event_type == EventType.INPUT_VALIDATION:
            if any(keyword in event.description.lower() for keyword in ["sql", "xss", "script"]):
                threat_score += 50

        # Determine threat level
        if threat_score >= 70:
            return ThreatLevel.CRITICAL
        elif threat_score >= 50:
            return ThreatLevel.HIGH
        elif threat_score >= 30:
            return ThreatLevel.MEDIUM
        else:
            return ThreatLevel.LOW

    def update_ip_reputation(self, ip: str, score_delta: int):
        """Update IP reputation score."""
        self.ip_reputation[ip] += score_delta
        # Cap the scores
        self.ip_reputation[ip] = max(-100, min(100, self.ip_reputation[ip]))

    def is_ip_blocked(self, ip: str) -> bool:
        """Check if IP is blocked."""
        return ip in self.blocked_ips and ip not in self.whitelist_ips

    def block_ip(self, ip: str, duration_minutes: int = 30):
        """Block IP for specified duration."""
        self.blocked_ips.add(ip)
        # In a real implementation, you'd use a scheduler to unblock
        logger.warning(f"IP {ip} blocked for {duration_minutes} minutes")


class SecurityMonitor:
    """Comprehensive security monitoring service."""

    def __init__(self, cache_service: Optional[CacheService] = None):
        self.cache_service = cache_service
        self.metrics = SecurityMetrics()
        self.threat_detector = ThreatDetector()
        self.event_handlers = []
        self.alert_thresholds = {
            "authentication_failures": 10,
            "rate_limit_violations": 20,
            "suspicious_activities": 5,
            "unique_threat_ips": 5,
        }
        self._running = False
        self._monitor_task = None

    async def start_monitoring(self):
        """Start security monitoring."""
        if self._running:
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("Security monitoring started")

    async def stop_monitoring(self):
        """Stop security monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Security monitoring stopped")

    async def log_security_event(
        self,
        event_type: EventType,
        source_ip: str,
        endpoint: str,
        method: str,
        description: str,
        details: Dict[str, Any],
        user_id: Optional[str] = None,
        user_agent: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> SecurityEvent:
        """Log a security event."""
        # Create security event
        event = SecurityEvent(
            event_id=f"SEC_{int(time.time() * 1000)}_{hash(source_ip) % 10000:04d}",
            event_type=event_type,
            threat_level=ThreatLevel.LOW,  # Will be updated by threat detector
            timestamp=datetime.now(timezone.utc),
            source_ip=source_ip,
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            description=description,
            details=details,
            user_agent=user_agent,
            session_id=session_id,
            request_id=request_id,
        )

        # Analyze threat level
        event.threat_level = self.threat_detector.analyze_event(event)

        # Record metrics
        self.metrics.record_event(event)

        # Store event (with retention)
        await self._store_event(event)

        # Check for alerts
        await self._check_alert_conditions(event)

        # Log event
        logger.info(
            f"Security event logged: {event.description}",
            extra={
                "security_event": event.event_type,
                "threat_level": event.threat_level,
                "event_id": event.event_id,
                "source_ip": event.source_ip,
                "endpoint": event.endpoint,
            },
        )

        return event

    async def _store_event(self, event: SecurityEvent):
        """Store security event with retention policy."""
        try:
            if self.cache_service:
                # Store in Redis with TTL (30 days for security events)
                key = f"security_event:{event.event_id}"
                await self.cache_service.set(
                    key,
                    json.dumps(event.to_dict()),
                    ttl=30 * 24 * 3600,  # 30 days
                )

                # Add to daily index for reporting
                date_key = f"security_events:{event.timestamp.strftime('%Y-%m-%d')}"
                await self.cache_service.lpush(date_key, event.event_id)
                await self.cache_service.expire(date_key, 30 * 24 * 3600)

        except Exception as e:
            logger.error(f"Failed to store security event: {e}")

    async def _check_alert_conditions(self, event: SecurityEvent):
        """Check if event triggers any alerts."""
        # Critical events always trigger alerts
        if event.threat_level == ThreatLevel.CRITICAL:
            await self._send_alert(f"CRITICAL Security Event: {event.description}", event, level="critical")

        # Check threshold-based alerts
        current_metrics = self.metrics.get_metrics_summary()

        for metric, threshold in self.alert_thresholds.items():
            if current_metrics.get(metric, 0) >= threshold:
                await self._send_alert(
                    f"Security threshold exceeded: {metric} = {current_metrics[metric]}", event, level="warning"
                )

    async def _send_alert(self, message: str, event: SecurityEvent, level: str = "warning"):
        """Send security alert."""
        alert_data = {
            "message": message,
            "level": level,
            "event": event.to_dict(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "metrics_summary": self.metrics.get_metrics_summary(),
        }

        # Log alert
        logger.warning(
            f"Security alert: {message}",
            extra={
                "security_alert": True,
                "alert_level": level,
                "event_id": event.event_id,
                "source_ip": event.source_ip,
            },
        )

        # In production, send to monitoring system (PagerDuty, Slack, etc.)
        # For now, just log it
        logger.critical(f"SECURITY ALERT: {message}")

    async def _monitoring_loop(self):
        """Background monitoring loop."""
        while self._running:
            try:
                # Clean up old events and update reputation scores
                await self._cleanup_old_data()

                # Generate periodic security report
                await self._generate_security_report()

                # Wait before next iteration
                await asyncio.sleep(300)  # Every 5 minutes

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in security monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait 1 minute on error

    async def _cleanup_old_data(self):
        """Clean up old security data."""
        # Clean up old failed attempts
        cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
        for ip, attempts in list(self.threat_detector.failed_attempts.items()):
            cleaned_attempts = [attempt for attempt in attempts if attempt > cutoff]
            if cleaned_attempts:
                self.threat_detector.failed_attempts[ip] = cleaned_attempts
            else:
                del self.threat_detector.failed_attempts[ip]

    async def _generate_security_report(self):
        """Generate periodic security report."""
        metrics = self.metrics.get_metrics_summary()
        logger.info(
            "Security monitoring report",
            extra={"security_report": True, "metrics": metrics, "timestamp": datetime.now(timezone.utc).isoformat()},
        )

    async def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get data for security dashboard."""
        return {
            "metrics": self.metrics.get_metrics_summary(),
            "recent_events": [event.to_dict() for event in list(self.metrics.recent_events)[-10:]],
            "threat_analysis": {
                "blocked_ips": len(self.threat_detector.blocked_ips),
                "high_risk_ips": len([ip for ip, score in self.threat_detector.ip_reputation.items() if score > 50]),
                "active_threats": len(
                    [
                        event
                        for event in self.metrics.recent_events
                        if event.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]
                        and (datetime.now(timezone.utc) - event.timestamp).total_seconds() < 3600
                    ]
                ),
            },
            "system_health": {
                "monitoring_active": self._running,
                "uptime": (datetime.now(timezone.utc) - self.metrics.metrics["last_reset"]).total_seconds(),
            },
        }

    async def search_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        event_type: Optional[EventType] = None,
        threat_level: Optional[ThreatLevel] = None,
        source_ip: Optional[str] = None,
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """Search security events with filters."""
        # This would implement a full search in a production system
        # For now, return recent events that match filters
        events = []
        for event in self.metrics.recent_events:
            if start_date and event.timestamp < start_date:
                continue
            if end_date and event.timestamp > end_date:
                continue
            if event_type and event.event_type != event_type:
                continue
            if threat_level and event.threat_level != threat_level:
                continue
            if source_ip and event.source_ip != source_ip:
                continue

            events.append(event)
            if len(events) >= limit:
                break

        return events


# Singleton instance
_security_monitor: Optional[SecurityMonitor] = None


async def get_security_monitor() -> SecurityMonitor:
    """Get the security monitor instance."""
    global _security_monitor
    if _security_monitor is None:
        from ghl_real_estate_ai.services.cache_service import CacheService

        cache_service = CacheService()
        _security_monitor = SecurityMonitor(cache_service)
        await _security_monitor.start_monitoring()
    return _security_monitor


@asynccontextmanager
async def security_monitoring_context():
    """Context manager for security monitoring lifecycle."""
    monitor = await get_security_monitor()
    try:
        yield monitor
    finally:
        await monitor.stop_monitoring()
