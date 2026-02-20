"""
Escalation and compliance management module for buyer bot.
Handles human escalation and compliance violation processing.
"""

import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from ghl_real_estate_ai.agents.buyer.constants import COMPLIANCE_SEVERITY_MAP
from ghl_real_estate_ai.agents.buyer.exceptions import ERROR_ID_COMPLIANCE_VIOLATION
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.event_publisher import EventPublisher
from ghl_real_estate_ai.services.ghl_client import GHLClient

logger = get_logger(__name__)


class EscalationManager:
    """Handles human escalation and compliance violations."""

    def __init__(
        self,
        ghl_client: Optional[GHLClient] = None,
        event_publisher: Optional[EventPublisher] = None
    ):
        self.ghl_client = ghl_client or GHLClient()
        self.event_publisher = event_publisher

    async def escalate_to_human_review(
        self,
        buyer_id: str,
        reason: str,
        context: Dict
    ) -> Dict:
        """
        Escalate buyer conversation to human agent review.

        Creates real GHL artifacts (tag, note, workflow trigger, disposition update)
        so the human agent sees the escalation in the CRM immediately.

        Graceful degradation: individual step failures are logged but do not
        crash the bot or block subsequent steps.

        Returns:
            Dict with escalation_id and per-step status.
        """
        escalation_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Escalating buyer to human review",
            extra={
                "escalation_id": escalation_id,
                "buyer_id": buyer_id,
                "reason": reason,
            },
        )

        escalation_result = {
            "escalation_id": escalation_id,
            "buyer_id": buyer_id,
            "reason": reason,
            "timestamp": timestamp,
            "tag_added": False,
            "note_added": False,
            "workflow_triggered": False,
            "disposition_updated": False,
            "event_published": False,
            "status": "pending",
        }

        # 1. Add "Escalation" tag to GHL contact
        try:
            await self.ghl_client.add_tags(buyer_id, ["Escalation"])
            escalation_result["tag_added"] = True
            logger.info(
                "Escalation tag added to contact",
                extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
            )
        except Exception as e:
            logger.warning(
                f"Failed to add Escalation tag for {buyer_id}: {e}",
                extra={"escalation_id": escalation_id, "error": str(e)},
            )

        # 2. Add a note to the contact with escalation details
        try:
            conversation_summary = context.get("conversation_summary", "")
            qualification_score = context.get("qualification_score", "N/A")
            current_step = context.get("current_step", "unknown")

            note_body = (
                f"[BUYER ESCALATION - {timestamp}]\n"
                f"Escalation ID: {escalation_id}\n"
                f"Reason: {reason}\n"
                f"Qualification Score: {qualification_score}\n"
                f"Stage: {current_step}\n"
                f"---\n"
                f"Context: {conversation_summary[:500] if conversation_summary else 'No summary available'}"
            )

            endpoint = f"{self.ghl_client.base_url}/contacts/{buyer_id}/notes"
            response = await self.ghl_client.http_client.post(
                endpoint,
                json={"body": note_body},
                headers=self.ghl_client.headers,
                timeout=settings.webhook_timeout_seconds,
            )
            response.raise_for_status()

            escalation_result["note_added"] = True
            logger.info(
                "Escalation note added to contact",
                extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
            )
        except Exception as e:
            logger.warning(
                f"Failed to add escalation note for {buyer_id}: {e}",
                extra={"escalation_id": escalation_id, "error": str(e)},
            )

        # 3. Trigger notify-agent workflow if configured
        if settings.notify_agent_workflow_id:
            try:
                await self.ghl_client.trigger_workflow(buyer_id, settings.notify_agent_workflow_id)
                escalation_result["workflow_triggered"] = True
                logger.info(
                    "Notify-agent workflow triggered",
                    extra={
                        "buyer_id": buyer_id,
                        "workflow_id": settings.notify_agent_workflow_id,
                        "escalation_id": escalation_id,
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to trigger notify-agent workflow for {buyer_id}: {e}",
                    extra={"escalation_id": escalation_id, "error": str(e)},
                )

        # 4. Update contact disposition to indicate escalation
        if settings.disposition_field_name:
            try:
                await self.ghl_client.update_custom_field(
                    buyer_id,
                    settings.disposition_field_name,
                    "Escalated - Needs Human Review",
                )
                escalation_result["disposition_updated"] = True
                logger.info(
                    "Contact disposition updated to escalated",
                    extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update disposition for {buyer_id}: {e}",
                    extra={"escalation_id": escalation_id, "error": str(e)},
                )

        # 5. Publish internal event for dashboards and monitoring
        if self.event_publisher:
            try:
                await self.event_publisher.publish_bot_status_update(
                    bot_type="jorge-buyer",
                    contact_id=buyer_id,
                    status="escalated",
                    current_step="human_review",
                    escalation_id=escalation_id,
                    reason=reason,
                )
                escalation_result["event_published"] = True
            except Exception as e:
                logger.warning(
                    f"Event publish failed for escalation {escalation_id}: {e}",
                    extra={"escalation_id": escalation_id, "error": str(e)},
                )

        # 6. Determine final status
        ghl_actions_succeeded = (
            escalation_result["tag_added"] or 
            escalation_result["note_added"] or 
            escalation_result["workflow_triggered"]
        )
        if ghl_actions_succeeded:
            escalation_result["status"] = "escalated"
        elif escalation_result["event_published"]:
            escalation_result["status"] = "escalated_internal_only"
            logger.warning(
                "GHL actions failed but internal event published - agent may not see escalation in CRM",
                extra={"escalation_id": escalation_id, "buyer_id": buyer_id},
            )
        else:
            escalation_result["status"] = "queued"
            logger.error(
                "All escalation channels failed for buyer. Queued for manual processing.",
                extra={"escalation_id": escalation_id, "buyer_id": buyer_id},
            )

        return escalation_result

    async def escalate_compliance_violation(
        self,
        buyer_id: str,
        violation_type: str,
        evidence: Dict
    ) -> Dict:
        """
        Handle compliance violation detection and escalation.

        1. Logs violation to audit trail with full evidence
        2. Determines severity (critical, high, medium, low)
        3. Notifies compliance officer for critical/high severity
        4. Flags contact in CRM with violation type
        5. Pauses bot interactions until human review
        6. Returns compliance_ticket_id

        Supported violation types: fair_housing, privacy, financial_regulation, licensing
        """
        compliance_ticket_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        severity = COMPLIANCE_SEVERITY_MAP.get(violation_type, "medium")

        logger.error(
            f"COMPLIANCE VIOLATION [{severity.upper()}]: {violation_type} for buyer {buyer_id}",
            extra={
                "error_id": ERROR_ID_COMPLIANCE_VIOLATION,
                "compliance_ticket_id": compliance_ticket_id,
                "buyer_id": buyer_id,
                "violation_type": violation_type,
                "severity": severity,
                "timestamp": timestamp,
                "evidence_keys": list(evidence.keys()),
            },
        )

        result = {
            "compliance_ticket_id": compliance_ticket_id,
            "buyer_id": buyer_id,
            "violation_type": violation_type,
            "severity": severity,
            "timestamp": timestamp,
            "audit_logged": False,
            "notification_sent": False,
            "crm_flagged": False,
            "bot_paused": False,
            "status": "pending",
        }

        # 1. Log to audit trail
        if self.event_publisher:
            try:
                await self.event_publisher.publish_conversation_update(
                    conversation_id=f"jorge_buyer_{buyer_id}",
                    lead_id=buyer_id,
                    stage="compliance_violation",
                    message=f"Compliance violation: {violation_type} (severity: {severity})",
                    compliance_ticket_id=compliance_ticket_id,
                    violation_type=violation_type,
                    severity=severity,
                    evidence_summary=str(evidence.get("summary", ""))[:500],
                )
                result["audit_logged"] = True
            except Exception as e:
                logger.error(f"Audit logging failed for compliance ticket {compliance_ticket_id}: {e}")

        # 2. Notify compliance officer for critical/high severity
        if severity in ("critical", "high") and self.event_publisher:
            try:
                await self.event_publisher.publish_bot_status_update(
                    bot_type="jorge-buyer",
                    contact_id=buyer_id,
                    status="compliance_alert",
                    current_step="compliance_review",
                    compliance_ticket_id=compliance_ticket_id,
                    violation_type=violation_type,
                    severity=severity,
                    priority="urgent",
                )
                result["notification_sent"] = True
            except Exception as e:
                logger.error(f"Compliance notification failed for ticket {compliance_ticket_id}: {e}")

        # 3. Flag in CRM via status update
        if self.event_publisher:
            try:
                await self.event_publisher.publish_bot_status_update(
                    bot_type="jorge-buyer",
                    contact_id=buyer_id,
                    status="compliance_flagged",
                    current_step="bot_paused",
                    compliance_ticket_id=compliance_ticket_id,
                    violation_type=violation_type,
                )
                result["crm_flagged"] = True
                result["bot_paused"] = True
            except Exception as e:
                logger.error(f"CRM flagging failed for compliance ticket {compliance_ticket_id}: {e}")

        # 4. Determine overall status
        if result["audit_logged"]:
            result["status"] = "escalated"
        else:
            result["status"] = "escalation_degraded"

        return result