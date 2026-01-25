"""
Security Monitoring and Management API Routes

Features:
- Security dashboard endpoints
- Threat monitoring and alerting
- Security event search and analysis
- System security health checks
- Compliance reporting
- Incident response tools
"""

from fastapi import APIRouter, HTTPException, Depends, Query, Request, status
from fastapi.security import HTTPBearer
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.security_monitor import (
    get_security_monitor, SecurityEvent, EventType, ThreatLevel
)
from ghl_real_estate_ai.api.middleware.jwt_auth import get_current_user
from ghl_real_estate_ai.api.middleware.websocket_security import get_websocket_manager

logger = get_logger(__name__)
security = HTTPBearer()

router = APIRouter(prefix="/api/security", tags=["security"])


# Pydantic Models for Security API

class SecurityDashboardResponse(BaseModel):
    """Security dashboard data response."""
    metrics: Dict[str, Any]
    recent_events: List[Dict[str, Any]]
    threat_analysis: Dict[str, Any]
    system_health: Dict[str, Any]
    websocket_stats: Dict[str, Any]


class SecurityEventResponse(BaseModel):
    """Security event response model."""
    event_id: str
    event_type: str
    threat_level: str
    timestamp: str
    source_ip: str
    user_id: Optional[str]
    endpoint: str
    method: str
    description: str
    details: Dict[str, Any]


class SecuritySearchRequest(BaseModel):
    """Security event search request."""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_type: Optional[EventType] = None
    threat_level: Optional[ThreatLevel] = None
    source_ip: Optional[str] = None
    limit: int = Field(default=100, ge=1, le=1000)


class ThreatResponse(BaseModel):
    """Response model for threat analysis."""
    
    threat_level: str
    confidence: float
    action: str = Field(..., pattern="^(block_ip|unblock_ip|escalate|dismiss)$")
    reason: str
    metadata: Dict[str, Any] = {}
    duration_minutes: Optional[int] = None


class SecurityHealthResponse(BaseModel):
    """Security system health response."""
    overall_status: str
    components: Dict[str, Dict[str, Any]]
    last_updated: str
    recommendations: List[str]


# Security Dashboard Endpoints

@router.get("/dashboard", response_model=SecurityDashboardResponse)
async def get_security_dashboard(
    current_user = Depends(get_current_user)
) -> SecurityDashboardResponse:
    """
    Get comprehensive security dashboard data.

    Requires admin privileges.
    """
    # Check admin privileges (implement based on your user system)
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        security_monitor = await get_security_monitor()
        dashboard_data = await security_monitor.get_security_dashboard_data()

        # Get WebSocket statistics
        websocket_manager = get_websocket_manager()
        websocket_stats = websocket_manager.get_connection_stats()

        return SecurityDashboardResponse(
            metrics=dashboard_data["metrics"],
            recent_events=dashboard_data["recent_events"],
            threat_analysis=dashboard_data["threat_analysis"],
            system_health=dashboard_data["system_health"],
            websocket_stats=websocket_stats
        )

    except Exception as e:
        logger.error(f"Error fetching security dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch security dashboard data"
        )


@router.get("/events/search", response_model=List[SecurityEventResponse])
async def search_security_events(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    event_type: Optional[EventType] = Query(None),
    threat_level: Optional[ThreatLevel] = Query(None),
    source_ip: Optional[str] = Query(None),
    limit: int = Query(default=100, ge=1, le=1000),
    current_user = Depends(get_current_user)
) -> List[SecurityEventResponse]:
    """
    Search security events with filters.

    Requires admin privileges.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        security_monitor = await get_security_monitor()
        events = await security_monitor.search_events(
            start_date=start_date,
            end_date=end_date,
            event_type=event_type,
            threat_level=threat_level,
            source_ip=source_ip,
            limit=limit
        )

        return [
            SecurityEventResponse(
                event_id=event.event_id,
                event_type=event.event_type,
                threat_level=event.threat_level,
                timestamp=event.timestamp.isoformat(),
                source_ip=event.source_ip,
                user_id=event.user_id,
                endpoint=event.endpoint,
                method=event.method,
                description=event.description,
                details=event.details
            )
            for event in events
        ]

    except Exception as e:
        logger.error(f"Error searching security events: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search security events"
        )


@router.post("/events/log")
async def log_security_event(
    request: Request,
    event_type: EventType,
    description: str,
    details: Dict[str, Any] = {},
    threat_level: Optional[ThreatLevel] = None,
    current_user = Depends(get_current_user)
):
    """
    Manually log a security event.

    Useful for external security tools integration.
    """
    try:
        security_monitor = await get_security_monitor()

        # Get client IP
        client_ip = request.client.host if request.client else "unknown"
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(',')[0].strip()

        event = await security_monitor.log_security_event(
            event_type=event_type,
            source_ip=client_ip,
            endpoint=request.url.path,
            method=request.method,
            description=description,
            details=details,
            user_id=str(current_user.id) if hasattr(current_user, 'id') else None,
            user_agent=request.headers.get("User-Agent"),
            request_id=request.headers.get("X-Request-ID")
        )

        return {
            "event_id": event.event_id,
            "message": "Security event logged successfully",
            "threat_level": event.threat_level
        }

    except Exception as e:
        logger.error(f"Error logging security event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to log security event"
        )


@router.get("/health", response_model=SecurityHealthResponse)
async def get_security_health(
    current_user = Depends(get_current_user)
) -> SecurityHealthResponse:
    """
    Get security system health status.

    Checks all security components and provides recommendations.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        security_monitor = await get_security_monitor()
        dashboard_data = await security_monitor.get_security_dashboard_data()
        websocket_manager = get_websocket_manager()

        # Assess component health
        components = {
            "security_monitor": {
                "status": "healthy" if dashboard_data["system_health"]["monitoring_active"] else "unhealthy",
                "uptime_hours": dashboard_data["system_health"]["uptime"] / 3600,
                "events_processed": dashboard_data["metrics"]["total_events"]
            },
            "rate_limiter": {
                "status": "healthy",
                "violations": dashboard_data["metrics"]["rate_limit_violations"],
                "blocked_ips": dashboard_data["threat_analysis"]["blocked_ips"]
            },
            "websocket_security": {
                "status": "healthy",
                "active_connections": dashboard_data["metrics"]["unique_ips_count"],
                "authenticated_rate": (
                    websocket_manager.get_connection_stats()["authenticated_connections"] /
                    max(websocket_manager.get_connection_stats()["total_connections"], 1)
                )
            },
            "threat_detection": {
                "status": "healthy",
                "active_threats": dashboard_data["threat_analysis"]["active_threats"],
                "high_risk_ips": dashboard_data["threat_analysis"]["high_risk_ips"]
            }
        }

        # Determine overall status
        component_statuses = [comp["status"] for comp in components.values()]
        if "unhealthy" in component_statuses:
            overall_status = "unhealthy"
        elif dashboard_data["threat_analysis"]["active_threats"] > 5:
            overall_status = "warning"
        else:
            overall_status = "healthy"

        # Generate recommendations
        recommendations = []
        if dashboard_data["metrics"]["authentication_failures"] > 50:
            recommendations.append("Consider implementing additional authentication security measures")

        if dashboard_data["threat_analysis"]["high_risk_ips"] > 10:
            recommendations.append("Review and potentially block high-risk IP addresses")

        if dashboard_data["metrics"]["rate_limit_violations"] > 100:
            recommendations.append("Consider adjusting rate limiting thresholds")

        if not recommendations:
            recommendations.append("Security posture is good - continue monitoring")

        return SecurityHealthResponse(
            overall_status=overall_status,
            components=components,
            last_updated=datetime.utcnow().isoformat(),
            recommendations=recommendations
        )

    except Exception as e:
        logger.error(f"Error fetching security health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch security health data"
        )


@router.post("/threat-response")
async def handle_threat_response(
    response_request: ThreatResponse,
    current_user = Depends(get_current_user)
):
    """
    Handle threat response actions.

    Allows admins to block IPs, escalate threats, or dismiss false positives.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        security_monitor = await get_security_monitor()
        action_taken = False

        if response_request.action == "block_ip":
            # Block IP address
            security_monitor.threat_detector.block_ip(
                response_request.target,
                response_request.duration_minutes or 30
            )
            action_taken = True

            logger.warning(
                f"IP blocked by admin: {response_request.target}",
                extra={
                    "security_event": "admin_ip_block",
                    "admin_user": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
                    "blocked_ip": response_request.target,
                    "reason": response_request.reason
                }
            )

        elif response_request.action == "unblock_ip":
            # Unblock IP address
            security_monitor.threat_detector.blocked_ips.discard(response_request.target)
            action_taken = True

            logger.info(
                f"IP unblocked by admin: {response_request.target}",
                extra={
                    "security_event": "admin_ip_unblock",
                    "admin_user": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
                    "unblocked_ip": response_request.target,
                    "reason": response_request.reason
                }
            )

        elif response_request.action == "escalate":
            # Escalate threat (would integrate with external systems)
            logger.critical(
                f"Threat escalated by admin: {response_request.target}",
                extra={
                    "security_event": "threat_escalated",
                    "admin_user": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
                    "escalated_target": response_request.target,
                    "reason": response_request.reason
                }
            )
            action_taken = True

        elif response_request.action == "dismiss":
            # Dismiss threat (reduce IP reputation score)
            security_monitor.threat_detector.update_ip_reputation(
                response_request.target,
                -20  # Reduce threat score
            )
            action_taken = True

            logger.info(
                f"Threat dismissed by admin: {response_request.target}",
                extra={
                    "security_event": "threat_dismissed",
                    "admin_user": str(current_user.id) if hasattr(current_user, 'id') else "unknown",
                    "dismissed_target": response_request.target,
                    "reason": response_request.reason
                }
            )

        if action_taken:
            return {
                "success": True,
                "message": f"Threat response action '{response_request.action}' completed successfully",
                "target": response_request.target,
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or unsupported threat response action"
            )

    except Exception as e:
        logger.error(f"Error handling threat response: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute threat response action"
        )


@router.get("/compliance/report")
async def get_compliance_report(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    current_user = Depends(get_current_user)
):
    """
    Generate compliance report for security events.

    Useful for audit and compliance requirements.
    """
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        security_monitor = await get_security_monitor()

        # Set default date range (last 30 days)
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Search events in the date range
        events = await security_monitor.search_events(
            start_date=start_date,
            end_date=end_date,
            limit=10000  # Large limit for compliance reporting
        )

        # Generate compliance statistics
        compliance_data = {
            "report_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "duration_days": (end_date - start_date).days
            },
            "summary": {
                "total_events": len(events),
                "events_by_type": {},
                "events_by_threat_level": {},
                "unique_source_ips": len(set(event.source_ip for event in events)),
                "authentication_events": len([e for e in events if e.event_type == EventType.AUTHENTICATION]),
                "high_severity_events": len([e for e in events if e.threat_level in [ThreatLevel.HIGH, ThreatLevel.CRITICAL]])
            },
            "top_threats": {},
            "security_metrics": security_monitor.metrics.get_metrics_summary(),
            "generated_at": datetime.utcnow().isoformat(),
            "generated_by": str(current_user.id) if hasattr(current_user, 'id') else "unknown"
        }

        # Calculate event type distribution
        for event in events:
            event_type = event.event_type
            threat_level = event.threat_level

            compliance_data["summary"]["events_by_type"][event_type] = \
                compliance_data["summary"]["events_by_type"].get(event_type, 0) + 1
            compliance_data["summary"]["events_by_threat_level"][threat_level] = \
                compliance_data["summary"]["events_by_threat_level"].get(threat_level, 0) + 1

        return compliance_data

    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )


# WebSocket Security Management

@router.get("/websocket/connections")
async def get_websocket_connections(
    current_user = Depends(get_current_user)
):
    """Get active WebSocket connections information."""
    if not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    try:
        websocket_manager = get_websocket_manager()
        stats = websocket_manager.get_connection_stats()

        # Get detailed connection information (without sensitive data)
        connections_info = []
        for connection_id, metadata in websocket_manager.connection_metadata.items():
            connections_info.append({
                "connection_id": connection_id,
                "client_ip": metadata.get("client_ip"),
                "authenticated": metadata.get("authenticated", False),
                "connected_at": metadata.get("connected_at").isoformat() if metadata.get("connected_at") else None,
                "message_count": metadata.get("message_count", 0),
                "last_activity": metadata.get("last_activity").isoformat() if metadata.get("last_activity") else None
            })

        return {
            "statistics": stats,
            "connections": connections_info,
            "timestamp": datetime.utcnow().isoformat()
        }

    except Exception as e:
        logger.error(f"Error fetching WebSocket connections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch WebSocket connections"
        )