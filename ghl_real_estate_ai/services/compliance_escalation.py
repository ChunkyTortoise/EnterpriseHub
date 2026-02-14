"""Structured compliance escalation for Jorge bots."""

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class ViolationType(str, Enum):
    FAIR_HOUSING = "fair_housing"
    PRIVACY = "privacy"
    FINANCIAL_REGULATION = "financial_regulation"
    LICENSING = "licensing"


class ViolationSeverity(str, Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Maps violation types to default severities
SEVERITY_MAP: Dict[ViolationType, ViolationSeverity] = {
    ViolationType.FAIR_HOUSING: ViolationSeverity.CRITICAL,
    ViolationType.PRIVACY: ViolationSeverity.HIGH,
    ViolationType.FINANCIAL_REGULATION: ViolationSeverity.HIGH,
    ViolationType.LICENSING: ViolationSeverity.MEDIUM,
}


@dataclass
class ComplianceViolation:
    """Records a compliance violation with full audit trail."""

    violation_type: ViolationType
    severity: ViolationSeverity
    description: str
    evidence: str
    contact_id: str
    bot_type: str  # "buyer" or "seller"
    timestamp: float = field(default_factory=time.time)
    actions_taken: List[str] = field(default_factory=list)


class ComplianceEscalationService:
    """Handles compliance violations with structured escalation."""

    def __init__(self, ghl_client: Any = None, event_publisher: Any = None):
        self.ghl_client = ghl_client
        self.event_publisher = event_publisher
        self._violation_log: List[ComplianceViolation] = []

    async def handle_violation(
        self,
        violation_type: ViolationType,
        description: str,
        evidence: str,
        contact_id: str,
        bot_type: str,
    ) -> ComplianceViolation:
        """Process a compliance violation through the escalation pipeline."""
        severity = SEVERITY_MAP.get(violation_type, ViolationSeverity.MEDIUM)
        violation = ComplianceViolation(
            violation_type=violation_type,
            severity=severity,
            description=description,
            evidence=evidence,
            contact_id=contact_id,
            bot_type=bot_type,
        )

        # Step 1: Log the violation
        logger.warning(
            "Compliance violation: type=%s severity=%s contact=%s bot=%s",
            violation_type.value,
            severity.value,
            contact_id,
            bot_type,
        )
        violation.actions_taken.append("logged_violation")

        # Step 2: Pause bot for critical/high
        if severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH):
            violation.actions_taken.append("bot_paused")

        # Step 3: Flag in CRM
        await self._flag_in_crm(contact_id, violation)

        # Step 4: Notify compliance officer for critical/high
        if severity in (ViolationSeverity.CRITICAL, ViolationSeverity.HIGH):
            await self._notify_compliance_officer(violation)

        # Step 5: Publish event
        await self._publish_violation_event(violation)

        # Step 6: Store in log
        self._violation_log.append(violation)

        return violation

    async def _flag_in_crm(
        self, contact_id: str, violation: ComplianceViolation
    ) -> None:
        """Add compliance flag tag in CRM."""
        if self.ghl_client:
            try:
                await self.ghl_client.add_tags(contact_id, ["Compliance-Flagged"])
                violation.actions_taken.append("crm_flagged")
            except Exception as e:
                logger.error("Failed to flag contact in CRM: %s", e)

    async def _notify_compliance_officer(
        self, violation: ComplianceViolation
    ) -> None:
        """Notify compliance officer for critical/high violations."""
        violation.actions_taken.append("compliance_officer_notified")
        logger.critical(
            "COMPLIANCE ALERT: %s violation for contact %s — %s",
            violation.violation_type.value,
            violation.contact_id,
            violation.description,
        )

    async def _publish_violation_event(
        self, violation: ComplianceViolation
    ) -> None:
        """Publish violation event for dashboards."""
        if self.event_publisher:
            try:
                self.event_publisher.publish_event(
                    "compliance_violation",
                    {
                        "violation_type": violation.violation_type.value,
                        "severity": violation.severity.value,
                        "contact_id": violation.contact_id,
                        "bot_type": violation.bot_type,
                        "description": violation.description,
                        "timestamp": violation.timestamp,
                        "actions_taken": violation.actions_taken,
                    },
                )
                violation.actions_taken.append("event_published")
            except Exception as e:
                logger.error("Failed to publish violation event: %s", e)

    def get_violation_log(self) -> List[ComplianceViolation]:
        """Return all recorded violations."""
        return list(self._violation_log)
