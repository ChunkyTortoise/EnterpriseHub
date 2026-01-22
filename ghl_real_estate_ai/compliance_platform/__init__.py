"""
Enterprise AI Compliance & Risk Platform

Production-grade compliance management for EU AI Act, SEC, HIPAA regulations.
Built with enterprise security patterns from EnterpriseHub.

Author: Enterprise AI Solutions
Version: 1.0.0
"""

from .models.compliance_models import (
    ComplianceStatus,
    RiskLevel,
    RegulationType,
    ViolationSeverity,
    ComplianceScore,
    RiskAssessment,
    PolicyViolation,
    ComplianceReport,
    AuditRecord,
    RemediationAction,
)

from .engine.risk_detector import RiskDetector
from .engine.policy_enforcer import PolicyEnforcer
from .engine.audit_tracker import ComplianceAuditTracker
from .engine.regulatory_mapper import RegulatoryMapper

from .services.compliance_service import ComplianceService
from .services.report_generator import ComplianceReportGenerator

__version__ = "1.0.0"
__all__ = [
    # Models
    "ComplianceStatus",
    "RiskLevel",
    "RegulationType",
    "ViolationSeverity",
    "ComplianceScore",
    "RiskAssessment",
    "PolicyViolation",
    "ComplianceReport",
    "AuditRecord",
    "RemediationAction",
    # Engine
    "RiskDetector",
    "PolicyEnforcer",
    "ComplianceAuditTracker",
    "RegulatoryMapper",
    # Services
    "ComplianceService",
    "ComplianceReportGenerator",
]
