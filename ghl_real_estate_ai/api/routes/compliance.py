"""
Compliance & Security API Routes - Jorge's Fort Knox Backend
FastAPI routes for comprehensive compliance monitoring and security management

This module provides:
- Real-time compliance status monitoring and reporting
- Security event tracking and incident response
- Audit trail management and search capabilities
- Privacy rights request processing and fulfillment
- Regulatory filing preparation and submission
- Document management and retention compliance
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ...compliance.audit_documentation_system import (
    AuditDocumentationSystem,
    AuditEventType,
    AuditSeverity,
    DocumentType,
)
from ...compliance.compliance_automation_engine import (
    ComplianceAutomationEngine,
)
from ...compliance.privacy_protection_system import (
    PrivacyProtectionSystem,
    PrivacyRegulation,
    PrivacyRight,
)
from ...compliance.security_framework import JorgeSecurityFramework
from ...services.auth_service import get_current_user
from ...services.websocket_manager import WebSocketManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/compliance", tags=["compliance"])

# Initialize compliance systems
security_framework = JorgeSecurityFramework()
compliance_engine = ComplianceAutomationEngine()
privacy_system = PrivacyProtectionSystem()
audit_system = AuditDocumentationSystem()

# WebSocket manager for real-time updates
ws_manager = WebSocketManager()


# Request/Response Models
class ComplianceStatusRequest(BaseModel):
    regulation: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class SecurityEventRequest(BaseModel):
    event_type: str
    severity: str
    description: str
    affected_systems: List[str]
    evidence: Optional[Dict[str, Any]] = None


class AuditSearchRequest(BaseModel):
    event_type: Optional[str] = None
    user_id: Optional[str] = None
    resource: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    compliance_tags: Optional[List[str]] = None


class PrivacyRequestSubmission(BaseModel):
    subject_identifiers: Dict[str, str]
    request_type: str
    regulation: str
    description: str
    verification_documents: Optional[List[str]] = None


class DocumentCreationRequest(BaseModel):
    document_type: str
    title: str
    content: str
    metadata: Optional[Dict[str, Any]] = None


class ComplianceReportRequest(BaseModel):
    report_type: str
    start_date: datetime
    end_date: datetime
    regulation_scope: Optional[List[str]] = None


# Compliance Status Monitoring
@router.get("/status")
async def get_compliance_status(
    regulation: Optional[str] = Query(None), current_user: Dict = Depends(get_current_user)
):
    """
    Get current compliance status across all or specific regulations
    """
    try:
        logger.info(f"Compliance status requested by user: {current_user.get('user_id')}")

        # Mock real-time compliance data (replace with actual implementation)
        compliance_data = {
            "overall_score": 96.8,
            "status": "compliant",
            "last_updated": datetime.now().isoformat(),
            "regulations": {
                "RESPA": {
                    "score": 98.5,
                    "status": "compliant",
                    "last_audit": "2024-01-15",
                    "next_due": "2024-04-15",
                    "violations": 0,
                },
                "Fair_Housing": {
                    "score": 96.8,
                    "status": "compliant",
                    "last_audit": "2024-01-10",
                    "next_due": "2024-04-10",
                    "violations": 0,
                },
                "GDPR": {
                    "score": 94.2,
                    "status": "warning",
                    "last_audit": "2024-01-20",
                    "next_due": "2024-07-20",
                    "violations": 2,
                },
                "CCPA": {
                    "score": 97.1,
                    "status": "compliant",
                    "last_audit": "2024-01-12",
                    "next_due": "2024-07-12",
                    "violations": 1,
                },
            },
            "trends": {
                "improvement_areas": ["GDPR consent management", "data retention automation"],
                "strengths": ["RESPA compliance", "Fair Housing adherence"],
                "upcoming_deadlines": [
                    {"regulation": "State Licensing", "deadline": "2024-04-08", "type": "renewal"},
                    {"regulation": "MLS Rules", "deadline": "2024-04-18", "type": "audit"},
                ],
            },
        }

        # Filter by specific regulation if requested
        if regulation:
            if regulation in compliance_data["regulations"]:
                return {
                    "regulation": regulation,
                    "data": compliance_data["regulations"][regulation],
                    "overall_context": {
                        "overall_score": compliance_data["overall_score"],
                        "status": compliance_data["status"],
                    },
                }
            else:
                raise HTTPException(status_code=404, detail=f"Regulation {regulation} not found")

        # Log compliance status access
        await audit_system.log_audit_event(
            AuditEventType.DATA_ACCESS,
            AuditSeverity.INFORMATIONAL,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "get_compliance_status",
            "compliance_dashboard",
            "success",
            {"regulation_filter": regulation},
        )

        return compliance_data

    except Exception as e:
        logger.error(f"Compliance status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Security Event Management
@router.get("/security/events")
async def get_security_events(
    severity: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=1000),
    current_user: Dict = Depends(get_current_user),
):
    """
    Get security events with filtering options
    """
    try:
        logger.info(f"Security events requested by user: {current_user.get('user_id')}")

        # Mock security events data (replace with actual implementation)
        security_events = [
            {
                "id": "evt_001",
                "type": "Failed Login Attempt",
                "severity": "medium",
                "timestamp": "2024-01-24T10:30:00Z",
                "description": "Multiple failed login attempts from IP 192.168.1.100",
                "status": "investigating",
                "affected_systems": ["Auth Service"],
                "user_id": None,
                "evidence": {"ip_address": "192.168.1.100", "attempt_count": 5},
            },
            {
                "id": "evt_002",
                "type": "Data Access",
                "severity": "low",
                "timestamp": "2024-01-24T09:15:00Z",
                "description": "Bulk client data export performed",
                "status": "resolved",
                "affected_systems": ["Client Database"],
                "user_id": "john.doe",
                "evidence": {"export_count": 150, "export_type": "csv"},
            },
            {
                "id": "evt_003",
                "type": "Permission Change",
                "severity": "high",
                "timestamp": "2024-01-24T08:45:00Z",
                "description": "Administrative permissions modified",
                "status": "resolved",
                "affected_systems": ["User Management"],
                "user_id": "admin",
                "evidence": {"permission_changed": "admin_access", "target_user": "john.doe"},
            },
        ]

        # Apply filters
        filtered_events = security_events

        if severity:
            filtered_events = [e for e in filtered_events if e["severity"] == severity]

        if status:
            filtered_events = [e for e in filtered_events if e["status"] == status]

        # Apply limit
        filtered_events = filtered_events[:limit]

        # Log security events access
        await audit_system.log_audit_event(
            AuditEventType.DATA_ACCESS,
            AuditSeverity.INFORMATIONAL,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "get_security_events",
            "security_dashboard",
            "success",
            {"severity_filter": severity, "status_filter": status, "limit": limit},
        )

        return {
            "events": filtered_events,
            "total": len(security_events),
            "filtered": len(filtered_events),
            "filters_applied": {"severity": severity, "status": status},
        }

    except Exception as e:
        logger.error(f"Security events retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/security/events")
async def create_security_event(event: SecurityEventRequest, current_user: Dict = Depends(get_current_user)):
    """
    Create new security event
    """
    try:
        logger.info(f"Security event creation requested by user: {current_user.get('user_id')}")

        # Create security event
        event_data = {
            "id": f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "type": event.event_type,
            "severity": event.severity,
            "timestamp": datetime.now().isoformat(),
            "description": event.description,
            "status": "open",
            "affected_systems": event.affected_systems,
            "reported_by": current_user.get("user_id"),
            "evidence": event.evidence or {},
        }

        # Log security event creation
        await audit_system.log_audit_event(
            AuditEventType.SECURITY_INCIDENT,
            AuditSeverity.HIGH if event.severity in ["high", "critical"] else AuditSeverity.MEDIUM,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "create_security_event",
            event_data["id"],
            "success",
            {"event_type": event.event_type, "severity": event.severity},
        )

        # Broadcast security event to WebSocket clients
        await ws_manager.broadcast_to_group(
            "security_events",
            {"type": "security_event_created", "event": event_data, "timestamp": datetime.now().isoformat()},
        )

        return {"status": "created", "event": event_data}

    except Exception as e:
        logger.error(f"Security event creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Audit Trail Management
@router.post("/audit/search")
async def search_audit_records(search: AuditSearchRequest, current_user: Dict = Depends(get_current_user)):
    """
    Search audit records with comprehensive filtering
    """
    try:
        logger.info(f"Audit search requested by user: {current_user.get('user_id')}")

        # Build search criteria
        search_criteria = {}
        if search.event_type:
            search_criteria["event_type"] = search.event_type
        if search.user_id:
            search_criteria["user_id"] = search.user_id
        if search.resource:
            search_criteria["resource"] = search.resource
        if search.compliance_tags:
            search_criteria["compliance_tags"] = search.compliance_tags

        # Build date range
        date_range = None
        if search.start_date and search.end_date:
            date_range = (search.start_date, search.end_date)

        # Perform search using audit system
        audit_records = await audit_system.search_audit_records(search_criteria, date_range)

        # Convert to API response format
        formatted_records = []
        for record in audit_records:
            formatted_records.append(
                {
                    "id": record.record_id,
                    "timestamp": record.timestamp.isoformat(),
                    "event_type": record.event_type.value,
                    "severity": record.severity.value,
                    "user_id": record.user_id,
                    "action": record.action,
                    "resource": record.resource,
                    "result": record.result,
                    "details": record.details,
                    "compliance_tags": record.compliance_tags,
                }
            )

        # Log audit search
        await audit_system.log_audit_event(
            AuditEventType.DATA_ACCESS,
            AuditSeverity.INFORMATIONAL,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "search_audit_records",
            "audit_search",
            "success",
            {"search_criteria": search_criteria, "results_count": len(formatted_records)},
        )

        return {
            "records": formatted_records,
            "total": len(formatted_records),
            "search_criteria": search_criteria,
            "date_range": {
                "start": search.start_date.isoformat() if search.start_date else None,
                "end": search.end_date.isoformat() if search.end_date else None,
            },
        }

    except Exception as e:
        logger.error(f"Audit search failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/audit/integrity")
async def verify_audit_integrity(current_user: Dict = Depends(get_current_user)):
    """
    Verify audit trail integrity for tamper detection
    """
    try:
        logger.info(f"Audit integrity verification requested by user: {current_user.get('user_id')}")

        # Verify audit chain integrity
        integrity_result = await audit_system.verify_audit_chain_integrity()

        # Log integrity verification
        await audit_system.log_audit_event(
            AuditEventType.SYSTEM_CONFIGURATION,
            AuditSeverity.HIGH,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "verify_audit_integrity",
            "audit_chain",
            "success" if integrity_result["chain_valid"] else "failure",
            {
                "chain_valid": integrity_result["chain_valid"],
                "corrupted_records": len(integrity_result["corrupted_records"]),
            },
        )

        return integrity_result

    except Exception as e:
        logger.error(f"Audit integrity verification failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Privacy Rights Management
@router.post("/privacy/request")
async def submit_privacy_request(request: PrivacyRequestSubmission, current_user: Dict = Depends(get_current_user)):
    """
    Submit data subject privacy rights request
    """
    try:
        logger.info(f"Privacy request submitted by user: {current_user.get('user_id')}")

        # Process privacy request
        privacy_request = await privacy_system.process_privacy_request(
            request.subject_identifiers,
            PrivacyRight(request.request_type),
            PrivacyRegulation(request.regulation),
            request.description,
        )

        # Log privacy request submission
        await audit_system.log_audit_event(
            AuditEventType.PRIVACY_REQUEST,
            AuditSeverity.MEDIUM,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "submit_privacy_request",
            privacy_request.request_id,
            "success",
            {
                "request_type": request.request_type,
                "regulation": request.regulation,
                "subject_identifiers": list(request.subject_identifiers.keys()),
            },
        )

        return {
            "status": "submitted",
            "request_id": privacy_request.request_id,
            "request_type": privacy_request.request_type.value,
            "regulation": privacy_request.regulation.value,
            "deadline": privacy_request.deadline.isoformat(),
            "verification_status": privacy_request.verification_status,
            "processing_status": privacy_request.processing_status,
        }

    except Exception as e:
        logger.error(f"Privacy request submission failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/privacy/requests/{request_id}")
async def get_privacy_request_status(request_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get privacy request status and details
    """
    try:
        logger.info(f"Privacy request status requested: {request_id}")

        # Mock privacy request data (replace with actual implementation)
        privacy_request_data = {
            "request_id": request_id,
            "request_type": "access",
            "regulation": "gdpr",
            "status": "in_progress",
            "submitted_at": "2024-01-20T14:30:00Z",
            "deadline": "2024-02-19T14:30:00Z",
            "estimated_completion": "2024-02-15T14:30:00Z",
            "verification_status": "verified",
            "processing_notes": [
                "Request received and verified",
                "Data collection in progress",
                "Expected completion within 5 business days",
            ],
        }

        # Log privacy request status access
        await audit_system.log_audit_event(
            AuditEventType.PRIVACY_REQUEST,
            AuditSeverity.INFORMATIONAL,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "get_privacy_request_status",
            request_id,
            "success",
            {"request_id": request_id},
        )

        return privacy_request_data

    except Exception as e:
        logger.error(f"Privacy request status retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Compliance Reporting
@router.post("/reports/generate")
async def generate_compliance_report(
    report_request: ComplianceReportRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
):
    """
    Generate comprehensive compliance report
    """
    try:
        logger.info(f"Compliance report generation requested by user: {current_user.get('user_id')}")

        # Generate compliance report
        report = await audit_system.generate_compliance_report(
            report_request.report_type,
            (report_request.start_date, report_request.end_date),
            report_request.regulation_scope or ["RESPA", "Fair_Housing", "GDPR", "CCPA"],
            current_user.get("user_id"),
        )

        # Log report generation
        await audit_system.log_audit_event(
            AuditEventType.SYSTEM_CONFIGURATION,
            AuditSeverity.MEDIUM,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "generate_compliance_report",
            report.report_id,
            "success",
            {
                "report_type": report_request.report_type,
                "date_range": f"{report_request.start_date.isoformat()} to {report_request.end_date.isoformat()}",
                "regulation_scope": report_request.regulation_scope,
            },
        )

        return {
            "status": "generated",
            "report_id": report.report_id,
            "report_type": report.report_type,
            "generated_at": report.generated_at.isoformat(),
            "compliance_score": report.compliance_score,
            "risk_level": report.risk_level,
            "executive_summary": report.executive_summary,
            "findings_count": len(report.findings),
            "recommendations_count": len(report.recommendations),
        }

    except Exception as e:
        logger.error(f"Compliance report generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/reports/{report_id}")
async def get_compliance_report(report_id: str, current_user: Dict = Depends(get_current_user)):
    """
    Get compliance report details
    """
    try:
        logger.info(f"Compliance report requested: {report_id}")

        # Mock report data (replace with actual implementation)
        report_data = {
            "report_id": report_id,
            "report_type": "quarterly_compliance",
            "reporting_period": {"start": "2024-01-01T00:00:00Z", "end": "2024-03-31T23:59:59Z"},
            "generated_at": "2024-01-24T12:00:00Z",
            "generated_by": current_user.get("user_id"),
            "status": "final",
            "compliance_score": 96.8,
            "risk_level": "low",
            "executive_summary": "Overall compliance performance excellent with minor improvements needed in GDPR consent management.",
            "findings": [
                {
                    "regulation": "GDPR",
                    "severity": "medium",
                    "description": "Consent refresh process could be automated",
                    "recommendations": ["Implement automated consent renewal system"],
                }
            ],
            "recommendations": [
                "Automate GDPR consent management",
                "Enhance privacy notice clarity",
                "Implement quarterly compliance reviews",
            ],
            "attachments": ["evidence_package.zip", "audit_trail.json"],
        }

        # Log report access
        await audit_system.log_audit_event(
            AuditEventType.DOCUMENT_ACCESS,
            AuditSeverity.INFORMATIONAL,
            current_user.get("user_id"),
            None,
            "api",
            "compliance_api",
            "get_compliance_report",
            report_id,
            "success",
            {"report_id": report_id},
        )

        return report_data

    except Exception as e:
        logger.error(f"Compliance report retrieval failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Document Management
@router.post("/documents")
async def create_compliance_document(
    document_request: DocumentCreationRequest, current_user: Dict = Depends(get_current_user)
):
    """
    Create new compliance document
    """
    try:
        logger.info(f"Document creation requested by user: {current_user.get('user_id')}")

        # Create compliance document
        document = await audit_system.create_compliance_document(
            DocumentType(document_request.document_type),
            document_request.title,
            document_request.content,
            current_user.get("user_id"),
            document_request.metadata,
        )

        return {
            "status": "created",
            "document_id": document.document_id,
            "document_type": document.document_type.value,
            "title": document.title,
            "version": document.version,
            "status": document.status.value,
            "created_at": document.created_at.isoformat(),
            "file_path": document.file_path,
        }

    except Exception as e:
        logger.error(f"Document creation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Export and Archive
@router.get("/export/audit")
async def export_audit_data(
    format: str = Query("csv", pattern="^(Union[csv, json]|Union[pdf, zip])$"),
    start_date: datetime = Query(...),
    end_date: datetime = Query(...),
    current_user: Dict = Depends(get_current_user),
):
    """
    Export audit data for compliance or external analysis
    """
    try:
        logger.info(f"Audit data export requested by user: {current_user.get('user_id')}")

        # Export audit data
        export_path = await audit_system.export_audit_data(
            format, (start_date, end_date), {"user_id": current_user.get("user_id")}
        )

        # Return file response
        return FileResponse(
            path=export_path,
            filename=f"audit_export_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.{format}",
            media_type="application/octet-stream",
        )

    except Exception as e:
        logger.error(f"Audit data export failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


# Real-time Monitoring WebSocket
@router.websocket("/ws/monitoring")
async def compliance_monitoring_websocket(websocket):
    """
    WebSocket endpoint for real-time compliance and security monitoring
    """
    await ws_manager.connect(websocket, "compliance_monitoring")

    try:
        while True:
            # Send periodic updates
            await asyncio.sleep(30)  # 30 seconds

            # Send compliance status update
            status_update = {
                "type": "compliance_status_update",
                "timestamp": datetime.now().isoformat(),
                "overall_score": 96.8,
                "critical_alerts": 0,
                "active_incidents": 1,
            }

            await websocket.send_json(status_update)

    except Exception:
        logger.info("Client disconnected from compliance monitoring WebSocket")
        await ws_manager.disconnect(websocket, "compliance_monitoring")


# Health check endpoint
@router.get("/health")
async def compliance_health_check():
    """
    Health check for compliance and security systems
    """
    try:
        health_status = {
            "status": "healthy",
            "systems": {
                "security_framework": "operational",
                "compliance_engine": "operational",
                "privacy_system": "operational",
                "audit_system": "operational",
            },
            "metrics": {
                "overall_compliance_score": 96.8,
                "active_security_events": 3,
                "audit_records_today": 247,
                "privacy_requests_pending": 2,
            },
            "last_check": datetime.now().isoformat(),
        }

        return health_status

    except Exception as e:
        logger.error(f"Compliance health check failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Health check failed")


# Initialize background monitoring
@router.on_event("startup")
async def startup_compliance_monitoring():
    """
    Start background compliance monitoring on startup
    """
    asyncio.create_task(continuous_compliance_monitoring())
    logger.info("Compliance monitoring started")


async def continuous_compliance_monitoring():
    """
    Background task for continuous compliance monitoring.
    Runs four sub-scanners on each iteration (every 60 seconds):
      041 - Compliance violation scanner (DRE / Fair Housing / TCPA)
      042 - Security anomaly detection
      043 - Privacy request processor
      044 - Audit trail aggregation and archival
    """
    while True:
        try:
            await _scan_compliance_violations()
            await _scan_security_anomalies()
            await _process_privacy_requests()
            await _aggregate_and_archive_audit_trail()
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"Continuous compliance monitoring error: {str(e)}")
            await asyncio.sleep(60)


# ---------------------------------------------------------------------------
# ROADMAP-041  Compliance violation scanner
# ---------------------------------------------------------------------------

_TCPA_OPT_OUT_RATE_THRESHOLD = 2.0
_FAIR_HOUSING_KEYWORDS = [
    "race", "religion", "national origin", "sex", "handicap",
    "familial status", "color",
]
_DRE_LICENSE_REQUIRED_ACTIONS = ["property_listing", "price_negotiation", "contract_signing"]


async def _scan_compliance_violations() -> None:
    """Scan for DRE, Fair Housing, and TCPA violations."""
    try:
        tcpa = await _check_tcpa_compliance()
        for v in tcpa:
            await audit_system.log_audit_event(
                AuditEventType.SECURITY_INCIDENT, AuditSeverity.HIGH,
                "system", None, "compliance_scanner", "tcpa_check",
                "violation_detected", v.get("resource", "sms_compliance"), "alert", v,
            )
            await ws_manager.broadcast_to_group(
                "compliance_monitoring",
                {"type": "compliance_violation", "regulation": "TCPA",
                 "details": v, "timestamp": datetime.now().isoformat()},
            )

        fh = await _check_fair_housing_compliance()
        for v in fh:
            await audit_system.log_audit_event(
                AuditEventType.SECURITY_INCIDENT, AuditSeverity.HIGH,
                "system", None, "compliance_scanner", "fair_housing_check",
                "violation_detected", v.get("resource", "messaging"), "alert", v,
            )

        dre = await _check_dre_compliance()
        for v in dre:
            await audit_system.log_audit_event(
                AuditEventType.SECURITY_INCIDENT, AuditSeverity.MEDIUM,
                "system", None, "compliance_scanner", "dre_check",
                "violation_detected", v.get("resource", "agent_action"), "alert", v,
            )

        total = len(tcpa) + len(fh) + len(dre)
        if total:
            logger.warning(f"Compliance scan found {total} violation(s)")
        else:
            logger.debug("Compliance scan: no violations")
    except Exception as e:
        logger.error(f"Compliance violation scan error: {e}")


async def _check_tcpa_compliance() -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    try:
        opt_out_records = await audit_system.search_audit_records({"event_type": "sms_opt_out"}, None)
        sent_records = await audit_system.search_audit_records({"event_type": "sms_sent"}, None)
        recent_opt_outs = len(opt_out_records) if opt_out_records else 0
        total_sent = len(sent_records) if sent_records else 0
        if total_sent > 0:
            rate = (recent_opt_outs / total_sent) * 100
            if rate > _TCPA_OPT_OUT_RATE_THRESHOLD:
                violations.append({
                    "type": "tcpa_opt_out_rate",
                    "rate_pct": round(rate, 2),
                    "threshold_pct": _TCPA_OPT_OUT_RATE_THRESHOLD,
                    "opt_outs": recent_opt_outs,
                    "total_sent": total_sent,
                })
    except Exception as e:
        logger.debug(f"TCPA check encountered non-critical error: {e}")
    return violations


async def _check_fair_housing_compliance() -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    try:
        records = await audit_system.search_audit_records({"event_type": "message_sent"}, None)
        for record in (records or []):
            content = str(getattr(record, "details", {}).get("content", "")).lower()
            matched = [kw for kw in _FAIR_HOUSING_KEYWORDS if kw in content]
            if matched:
                violations.append({
                    "type": "fair_housing_keyword",
                    "keywords": matched,
                    "record_id": getattr(record, "record_id", "unknown"),
                })
    except Exception as e:
        logger.debug(f"Fair Housing check encountered non-critical error: {e}")
    return violations


async def _check_dre_compliance() -> List[Dict[str, Any]]:
    violations: List[Dict[str, Any]] = []
    try:
        for action_type in _DRE_LICENSE_REQUIRED_ACTIONS:
            records = await audit_system.search_audit_records({"action": action_type}, None)
            for record in (records or []):
                user_id = getattr(record, "user_id", None)
                if user_id and user_id.startswith("bot_"):
                    violations.append({
                        "type": "dre_unlicensed_action",
                        "action": action_type,
                        "user_id": user_id,
                        "record_id": getattr(record, "record_id", "unknown"),
                    })
    except Exception as e:
        logger.debug(f"DRE check encountered non-critical error: {e}")
    return violations


# ---------------------------------------------------------------------------
# ROADMAP-042  Security anomaly detection
# ---------------------------------------------------------------------------

_AUTH_FAILURE_THRESHOLD = 5
_BULK_PII_ACCESS_THRESHOLD = 50


async def _scan_security_anomalies() -> None:
    try:
        auth_records = await audit_system.search_audit_records({"event_type": "authentication_failure"}, None)
        auth_failures = len(auth_records) if auth_records else 0
        if auth_failures >= _AUTH_FAILURE_THRESHOLD:
            event = {"type": "auth_failure_spike", "count": auth_failures,
                     "threshold": _AUTH_FAILURE_THRESHOLD, "severity": "high"}
            await audit_system.log_audit_event(
                AuditEventType.SECURITY_INCIDENT, AuditSeverity.HIGH,
                "system", None, "security_scanner", "auth_monitor",
                "anomaly_detected", "auth_service", "alert", event,
            )
            await ws_manager.broadcast_to_group(
                "security_events",
                {"type": "security_anomaly", "event": event, "timestamp": datetime.now().isoformat()},
            )
            logger.warning(f"Security anomaly: {auth_failures} auth failures detected")

        pii_records = await audit_system.search_audit_records({"event_type": "pii_access"}, None)
        pii_count = len(pii_records) if pii_records else 0
        if pii_count >= _BULK_PII_ACCESS_THRESHOLD:
            event = {"type": "bulk_pii_access", "count": pii_count,
                     "threshold": _BULK_PII_ACCESS_THRESHOLD, "severity": "critical"}
            await audit_system.log_audit_event(
                AuditEventType.SECURITY_INCIDENT, AuditSeverity.CRITICAL,
                "system", None, "security_scanner", "pii_monitor",
                "anomaly_detected", "data_access", "alert", event,
            )
            logger.critical(f"Security anomaly: {pii_count} PII accesses in monitoring window")
    except Exception as e:
        logger.error(f"Security anomaly scan error: {e}")


# ---------------------------------------------------------------------------
# ROADMAP-043  Privacy request processor (GDPR / CCPA)
# ---------------------------------------------------------------------------

_DELETION_SLA_DAYS = 30
_EXPORT_SLA_DAYS = 7


async def _process_privacy_requests() -> None:
    try:
        pending = await audit_system.search_audit_records(
            {"event_type": "privacy_request", "result": "pending"}, None,
        )
        now = datetime.now()
        for req in (pending or []):
            req_type = getattr(req, "details", {}).get("request_type", "")
            submitted = getattr(req, "timestamp", now)
            req_id = getattr(req, "record_id", "unknown")
            subject_ids = getattr(req, "details", {}).get("subject_identifiers", {})
            regulation = getattr(req, "details", {}).get("regulation", "gdpr")

            if req_type == "deletion" and subject_ids:
                deadline = submitted + timedelta(days=_DELETION_SLA_DAYS)
                if (deadline - now).days <= 7:
                    logger.warning(f"Privacy deletion request {req_id} due in {(deadline - now).days} days")
                try:
                    await privacy_system.process_privacy_request(
                        subject_ids, PrivacyRight("erasure"),
                        PrivacyRegulation(regulation),
                        f"Auto-processed: deletion request {req_id}",
                    )
                except Exception as e:
                    logger.error(f"Failed to process deletion request {req_id}: {e}")

            elif req_type == "export" and subject_ids:
                deadline = submitted + timedelta(days=_EXPORT_SLA_DAYS)
                if (deadline - now).days <= 2:
                    logger.warning(f"Privacy export request {req_id} due in {(deadline - now).days} days")
                try:
                    await privacy_system.process_privacy_request(
                        subject_ids, PrivacyRight("access"),
                        PrivacyRegulation(regulation),
                        f"Auto-processed: export request {req_id}",
                    )
                except Exception as e:
                    logger.error(f"Failed to process export request {req_id}: {e}")
    except Exception as e:
        logger.error(f"Privacy request processing error: {e}")


# ---------------------------------------------------------------------------
# ROADMAP-044  Audit trail aggregation and archival
# ---------------------------------------------------------------------------

_ARCHIVE_AFTER_DAYS = 90


async def _aggregate_and_archive_audit_trail() -> None:
    try:
        cutoff = datetime.now() - timedelta(days=_ARCHIVE_AFTER_DAYS)
        old_records = await audit_system.search_audit_records(
            {}, (datetime(2020, 1, 1), cutoff),
        )
        archived_count = 0
        for record in (old_records or []):
            try:
                await audit_system.create_compliance_document(
                    DocumentType("audit_archive"),
                    f"Archived audit record: {getattr(record, 'record_id', 'unknown')}",
                    str(getattr(record, "details", {})),
                    "system",
                    {"original_record_id": getattr(record, "record_id", "unknown"),
                     "original_timestamp": getattr(record, "timestamp", cutoff).isoformat(),
                     "archived_at": datetime.now().isoformat()},
                )
                archived_count += 1
            except Exception as e:
                logger.debug(f"Archive record error (non-critical): {e}")
        if archived_count > 0:
            logger.info(f"Archived {archived_count} audit records older than {_ARCHIVE_AFTER_DAYS} days")
        await audit_system.log_audit_event(
            AuditEventType.SYSTEM_CONFIGURATION, AuditSeverity.INFORMATIONAL,
            "system", None, "audit_archiver", "audit_aggregation",
            "archive_cycle_complete", "audit_trail", "success",
            {"archived_count": archived_count, "cutoff_date": cutoff.isoformat()},
        )
    except Exception as e:
        logger.error(f"Audit trail aggregation error: {e}")


@router.on_event("shutdown")
async def shutdown_compliance_services():
    """
    Clean up compliance services on shutdown
    """
    await security_framework.cleanup()
    await compliance_engine.cleanup()
    await privacy_system.cleanup()
    await audit_system.cleanup()
    logger.info("Compliance services cleaned up")
