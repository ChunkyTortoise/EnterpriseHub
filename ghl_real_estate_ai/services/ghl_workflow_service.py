"""
GHL Workflow Service

This module provides integration with GoHighLevel CRM workflows, including
auto-tagging, pipeline stage updates, and appointment booking synchronization.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.ghl_workflow import (
    BotAppointment,
    GHLWorkflowOperation,
    PipelineStageHistory,
)
from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

logger = get_logger(__name__)


class PipelineStage(str, Enum):
    """Pipeline stage enumeration."""

    NEW = "new"
    QUALIFYING = "qualifying"
    QUALIFIED = "qualified"
    HOT_LEAD = "hot_lead"
    WARM_LEAD = "warm_lead"
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    FOLLOW_UP = "follow_up"
    RE_ENGAGEMENT = "re_engagement"
    DORMANT = "dormant"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class TagAction(str, Enum):
    """Tag action enumeration."""

    ADD = "add"
    REMOVE = "remove"


class OperationStatus(str, Enum):
    """Operation status enumeration."""

    PENDING = "pending"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class TagOperation:
    """Represents a tag operation."""

    tag: str
    action: TagAction
    reason: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PipelineUpdate:
    """Represents a pipeline stage update."""

    contact_id: str
    from_stage: Optional[PipelineStage]
    to_stage: PipelineStage
    reason: str
    score: Optional[float]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AppointmentDetails:
    """Represents appointment details."""

    contact_id: str
    title: str
    start_time: datetime
    end_time: datetime
    calendar_id: str
    location: Optional[str] = None
    notes: Optional[str] = None
    attendees: List[str] = field(default_factory=list)
    appointment_id: Optional[str] = None


@dataclass
class WorkflowResult:
    """Result of a workflow operation."""

    success: bool
    tags_applied: List[str] = field(default_factory=list)
    tags_removed: List[str] = field(default_factory=list)
    stage_updated: bool = False
    appointment_synced: bool = False
    errors: List[str] = field(default_factory=list)
    operation_ids: List[str] = field(default_factory=list)


class GHLWorkflowService:
    """
    Manages GHL CRM workflow operations.

    This service provides methods for:
    - Auto-tagging based on lead scores and signals
    - Pipeline stage updates based on lead progression
    - Appointment booking and synchronization
    - Contact data synchronization
    """

    # Auto-tagging rules
    TAG_RULES = {
        "hot_lead": {
            "trigger": lambda scores: scores.get("composite_score", 0) >= 80,
            "tag": "Hot-Lead",
            "remove_tag": "Cold-Lead",
            "reason": "Composite score >= 80",
        },
        "warm_lead": {
            "trigger": lambda scores: 60 <= scores.get("composite_score", 0) < 80,
            "tag": "Warm-Lead",
            "remove_tag": None,
            "reason": "Composite score 60-79",
        },
        "cold_lead": {
            "trigger": lambda scores: scores.get("composite_score", 0) < 40,
            "tag": "Cold-Lead",
            "remove_tag": None,
            "reason": "Composite score < 40",
        },
        "high_commitment": {
            "trigger": lambda scores: scores.get("pcs_score", 0) >= 80,
            "tag": "High-Commitment",
            "remove_tag": "Low-Commitment",
            "reason": "PCS score >= 80",
        },
        "priority_lead": {
            "trigger": lambda scores: scores.get("composite_score", 0) >= 80,
            "tag": "Priority-Lead",
            "remove_tag": None,
            "reason": "Top-tier lead",
        },
        "investor_seller": {
            "trigger": lambda scores, persona: persona == "Investor",
            "tag": "Investor-Seller",
            "remove_tag": None,
            "reason": "Investor persona detected",
        },
        "distressed_seller": {
            "trigger": lambda scores, persona: persona == "Distressed",
            "tag": "Distressed-Seller",
            "remove_tag": None,
            "reason": "Distressed persona detected",
        },
        "first_time_buyer": {
            "trigger": lambda scores, persona: persona == "First-Time",
            "tag": "First-Time-Buyer",
            "remove_tag": None,
            "reason": "First-time buyer persona",
        },
        "high_urgency": {
            "trigger": lambda scores: scores.get("urgency_level", 0) >= 0.7,
            "tag": "High-Urgency",
            "remove_tag": None,
            "reason": "Urgency level >= 0.7",
        },
        "needs_attention": {
            "trigger": lambda scores, sentiment: sentiment in ["negative", "angry", "frustrated"],
            "tag": "Needs-Attention",
            "remove_tag": None,
            "reason": "Negative sentiment detected",
        },
        "escalated": {
            "trigger": lambda scores, escalation: escalation is True,
            "tag": "Escalated",
            "remove_tag": None,
            "reason": "Human handoff initiated",
        },
        "appointment_set": {
            "trigger": lambda scores, appointment: appointment is True,
            "tag": "Appointment-Set",
            "remove_tag": None,
            "reason": "Meeting scheduled",
        },
    }

    # Pipeline transition rules
    PIPELINE_RULES = {
        (PipelineStage.NEW, "first_message"): PipelineStage.QUALIFYING,
        (PipelineStage.QUALIFYING, "qualified"): PipelineStage.QUALIFIED,
        (PipelineStage.QUALIFIED, "hot"): PipelineStage.HOT_LEAD,
        (PipelineStage.QUALIFIED, "warm"): PipelineStage.WARM_LEAD,
        (PipelineStage.HOT_LEAD, "appointment_booked"): PipelineStage.APPOINTMENT_SCHEDULED,
        (PipelineStage.WARM_LEAD, "appointment_booked"): PipelineStage.APPOINTMENT_SCHEDULED,
        (PipelineStage.APPOINTMENT_SCHEDULED, "completed"): PipelineStage.FOLLOW_UP,
        (PipelineStage.FOLLOW_UP, "no_response_7d"): PipelineStage.RE_ENGAGEMENT,
        (PipelineStage.FOLLOW_UP, "no_response_30d"): PipelineStage.DORMANT,
        (PipelineStage.RE_ENGAGEMENT, "no_response_30d"): PipelineStage.DORMANT,
        (PipelineStage.FOLLOW_UP, "closed_won"): PipelineStage.CLOSED_WON,
        (PipelineStage.FOLLOW_UP, "closed_lost"): PipelineStage.CLOSED_LOST,
    }

    def __init__(
        self,
        ghl_client: Optional[EnhancedGHLClient] = None,
        db_session=None,
    ):
        """
        Initialize GHL workflow service.

        Args:
            ghl_client: Enhanced GHL client instance
            db_session: Database session for logging operations
        """
        self.ghl_client = ghl_client or EnhancedGHLClient()
        self.db_session = db_session

    async def apply_auto_tags(
        self,
        contact_id: str,
        scores: Dict[str, float],
        persona: Optional[str] = None,
        sentiment: Optional[str] = None,
        escalation: bool = False,
        appointment_booked: bool = False,
    ) -> WorkflowResult:
        """
        Apply auto-tagging rules based on scores and signals.

        Args:
            contact_id: GHL contact ID
            scores: Dictionary of scores (frs_score, pcs_score, composite_score, urgency_level)
            persona: Buyer/seller persona type
            sentiment: Sentiment analysis result
            escalation: Whether escalation was triggered
            appointment_booked: Whether appointment was booked

        Returns:
            WorkflowResult with applied tags
        """
        result = WorkflowResult(success=True)
        operations = []

        try:
            # Get current contact to check existing tags
            contact = await self.ghl_client.get_contact(contact_id)
            current_tags = set(contact.tags) if contact else set()

            # Apply each tag rule
            for rule_name, rule_config in self.TAG_RULES.items():
                trigger_func = rule_config["trigger"]
                tag = rule_config["tag"]
                remove_tag = rule_config.get("remove_tag")
                reason = rule_config["reason"]

                # Check if rule triggers
                try:
                    if rule_name in ["investor_seller", "distressed_seller", "first_time_buyer"]:
                        triggered = trigger_func(scores, persona)
                    elif rule_name in ["needs_attention"]:
                        triggered = trigger_func(scores, sentiment)
                    elif rule_name == "escalated":
                        triggered = trigger_func(scores, escalation)
                    elif rule_name == "appointment_set":
                        triggered = trigger_func(scores, appointment_booked)
                    else:
                        triggered = trigger_func(scores)
                except Exception as e:
                    logger.warning(f"Error evaluating tag rule {rule_name}: {e}")
                    continue

                if triggered:
                    # Add tag if not already present
                    if tag not in current_tags:
                        operation = TagOperation(
                            tag=tag,
                            action=TagAction.ADD,
                            reason=reason,
                        )
                        operations.append(operation)
                        result.tags_applied.append(tag)

                    # Remove conflicting tag if specified
                    if remove_tag and remove_tag in current_tags:
                        operation = TagOperation(
                            tag=remove_tag,
                            action=TagAction.REMOVE,
                            reason=f"Conflicting with {tag}",
                        )
                        operations.append(operation)
                        result.tags_removed.append(remove_tag)

            # Execute tag operations
            if operations:
                await self._execute_tag_operations(contact_id, operations, result)

            logger.info(
                f"Applied auto-tags for contact {contact_id}: "
                f"{len(result.tags_applied)} added, {len(result.tags_removed)} removed"
            )

        except Exception as e:
            logger.error(f"Error applying auto-tags for contact {contact_id}: {e}")
            result.success = False
            result.errors.append(str(e))

        return result

    async def update_pipeline_stage(
        self,
        contact_id: str,
        current_stage: PipelineStage,
        scores: Dict[str, float],
        conversation_state: Dict[str, Any],
    ) -> WorkflowResult:
        """
        Update pipeline stage based on lead progression.

        Args:
            contact_id: GHL contact ID
            current_stage: Current pipeline stage
            scores: Dictionary of scores
            conversation_state: Conversation state with triggers

        Returns:
            WorkflowResult with stage update status
        """
        result = WorkflowResult(success=True)
        new_stage = current_stage

        try:
            # Determine trigger based on scores and state
            trigger = self._determine_pipeline_trigger(current_stage, scores, conversation_state)

            # Find new stage based on trigger
            if trigger:
                new_stage = self.PIPELINE_RULES.get((current_stage, trigger), current_stage)

            # Check if stage changed
            if new_stage != current_stage:
                # Update pipeline stage in GHL
                await self._update_ghl_pipeline_stage(contact_id, new_stage)

                # Log the transition
                await self._log_pipeline_transition(
                    contact_id=contact_id,
                    from_stage=current_stage,
                    to_stage=new_stage,
                    reason=trigger,
                    score=scores.get("composite_score"),
                )

                result.stage_updated = True
                logger.info(
                    f"Updated pipeline stage for contact {contact_id}: "
                    f"{current_stage} -> {new_stage} (trigger: {trigger})"
                )
            else:
                logger.debug(f"No pipeline stage change for contact {contact_id}")

        except Exception as e:
            logger.error(f"Error updating pipeline stage for contact {contact_id}: {e}")
            result.success = False
            result.errors.append(str(e))

        return result

    async def sync_appointment(
        self,
        appointment: AppointmentDetails,
    ) -> WorkflowResult:
        """
        Sync appointment to GHL calendar.

        Args:
            appointment: Appointment details

        Returns:
            WorkflowResult with appointment sync status
        """
        result = WorkflowResult(success=True)

        try:
            # Create appointment in GHL
            ghl_appointment_id = await self._create_ghl_appointment(appointment)

            if ghl_appointment_id:
                # Log appointment in database
                await self._log_appointment(appointment, ghl_appointment_id)

                result.appointment_synced = True
                logger.info(
                    f"Synced appointment for contact {appointment.contact_id}: "
                    f"{ghl_appointment_id}"
                )
            else:
                result.success = False
                result.errors.append("Failed to create appointment in GHL")

        except Exception as e:
            logger.error(f"Error syncing appointment for contact {appointment.contact_id}: {e}")
            result.success = False
            result.errors.append(str(e))

        return result

    async def detect_appointment_request(
        self,
        conversation_history: List[Dict[str, Any]],
    ) -> Optional[AppointmentDetails]:
        """
        Detect and parse appointment requests from conversation.

        Args:
            conversation_history: List of conversation messages

        Returns:
            AppointmentDetails if detected, None otherwise
        """
        if not conversation_history:
            return None

        # Get last user message
        last_user_message = None
        for msg in reversed(conversation_history):
            if msg.get("role") == "user":
                last_user_message = msg.get("content", "")
                break

        if not last_user_message:
            return None

        # Check for appointment keywords
        appointment_keywords = [
            "schedule", "book", "appointment", "meeting", "call", "visit",
            "showing", "tour", "available", "when can", "set up"
        ]

        if not any(keyword in last_user_message.lower() for keyword in appointment_keywords):
            return None

        # Try to extract date/time
        date_pattern = r"(?:on|at|for)\s+(?:tomorrow|today|monday|tuesday|wednesday|thursday|friday|saturday|sunday|\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{1,2}:\d{2}\s*(?:am|pm)?)"
        date_match = re.search(date_pattern, last_user_message, re.IGNORECASE)

        if date_match:
            # This is a simplified detection - in production, use proper date parsing
            logger.info(f"Detected appointment request with date: {date_match.group()}")
            # Return a placeholder - actual implementation would parse the date properly
            return None

        return None

    async def sync_contact_data(
        self,
        contact_id: str,
        bot_data: Dict[str, Any],
    ) -> bool:
        """
        Sync bot-collected data to GHL contact.

        Args:
            contact_id: GHL contact ID
            bot_data: Dictionary of bot-collected data

        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare update payload
            updates = {}
            from ghl_real_estate_ai.ghl_utils.config import settings

            # Map bot data to GHL fields
            updates["custom_fields"] = updates.get("custom_fields", {})

            # 1. Standard scores
            if "frs_score" in bot_data:
                updates["custom_fields"]["frs_score"] = str(bot_data["frs_score"])
            if "pcs_score" in bot_data:
                updates["custom_fields"]["pcs_score"] = str(bot_data["pcs_score"])
            if "composite_score" in bot_data:
                updates["custom_fields"]["composite_score"] = str(bot_data["composite_score"])
            if "persona" in bot_data:
                updates["custom_fields"]["persona"] = bot_data["persona"]

            # 2. Deep Seller Field Mapping (Phase 2 enhancements)
            field_map = {
                "seller_temperature": settings.custom_field_seller_temperature,
                "pcs_score": settings.custom_field_pcs_score,
                "seller_motivation": settings.custom_field_seller_motivation,
                "timeline_urgency": settings.custom_field_timeline_urgency,
                "property_condition": settings.custom_field_property_condition,
                "price_expectation": settings.custom_field_price_expectation,
                "seller_liens": settings.custom_field_seller_liens,
                "seller_repairs": settings.custom_field_seller_repairs,
                "seller_listing_history": settings.custom_field_seller_listing_history,
                "seller_decision_maker": settings.custom_field_seller_decision_maker,
            }

            for data_key, field_id in field_map.items():
                if field_id and data_key in bot_data and bot_data[data_key] is not None:
                    updates["custom_fields"][field_id] = str(bot_data[data_key])

            # 3. Special handling for address/location
            if "property_address" in bot_data and settings.custom_field_location:
                updates["custom_fields"][settings.custom_field_location] = bot_data["property_address"]

            if updates["custom_fields"]:
                success = await self.ghl_client.update_contact(contact_id, updates)
                if success:
                    logger.info(f"Synced bot data to contact {contact_id}")
                return success

            return True

        except Exception as e:
            logger.error(f"Error syncing contact data for {contact_id}: {e}")
            return False

    async def get_pipeline_summary(
        self,
        pipeline_id: str,
    ) -> Dict[str, int]:
        """
        Get summary of contacts by pipeline stage.

        Args:
            pipeline_id: GHL pipeline ID

        Returns:
            Dictionary mapping stage names to contact counts
        """
        # This would query the pipeline_stage_history table
        # For now, return empty dict
        return {}

    # ========================================================================
    # Private Helper Methods
    # ========================================================================

    async def _execute_tag_operations(
        self,
        contact_id: str,
        operations: List[TagOperation],
        result: WorkflowResult,
    ) -> None:
        """Execute tag operations against GHL."""
        try:
            # Get current contact
            contact = await self.ghl_client.get_contact(contact_id)
            if not contact:
                logger.error(f"Contact {contact_id} not found")
                return

            current_tags = set(contact.tags)
            updated_tags = list(current_tags)

            # Process operations
            for operation in operations:
                if operation.action == TagAction.ADD:
                    if operation.tag not in current_tags:
                        updated_tags.append(operation.tag)
                elif operation.action == TagAction.REMOVE:
                    if operation.tag in current_tags:
                        updated_tags.remove(operation.tag)

            # Update contact with new tags
            success = await self.ghl_client.update_contact(
                contact_id,
                {"tags": updated_tags},
            )

            if success:
                # Log operation
                await self._log_workflow_operation(
                    contact_id=contact_id,
                    operation_type="tag",
                    operation_data={
                        "operations": [
                            {
                                "tag": op.tag,
                                "action": op.action.value,
                                "reason": op.reason,
                            }
                            for op in operations
                        ]
                    },
                    status=OperationStatus.SUCCESS,
                )
            else:
                result.success = False
                result.errors.append("Failed to update tags in GHL")

        except Exception as e:
            logger.error(f"Error executing tag operations: {e}")
            result.success = False
            result.errors.append(str(e))

    async def _update_ghl_pipeline_stage(
        self,
        contact_id: str,
        new_stage: PipelineStage,
    ) -> bool:
        """Update pipeline stage in GHL."""
        try:
            # Update contact with pipeline stage in custom fields
            updates = {
                "custom_fields": {
                    "pipeline_stage": new_stage.value,
                }
            }
            return await self.ghl_client.update_contact(contact_id, updates)
        except Exception as e:
            logger.error(f"Error updating GHL pipeline stage: {e}")
            return False

    async def _log_pipeline_transition(
        self,
        contact_id: str,
        from_stage: PipelineStage,
        to_stage: PipelineStage,
        reason: str,
        score: Optional[float],
    ) -> None:
        """Log pipeline stage transition to database."""
        if not self.db_session:
            return

        try:
            history = PipelineStageHistory(
                contact_id=contact_id,
                from_stage=from_stage.value if from_stage else None,
                to_stage=to_stage.value,
                reason=reason,
                score_at_transition=str(score) if score else None,
            )
            self.db_session.add(history)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging pipeline transition: {e}")

    async def _create_ghl_appointment(
        self,
        appointment: AppointmentDetails,
    ) -> Optional[str]:
        """Create appointment in GHL calendar."""
        if settings.test_mode:
            logger.info(f"[TEST MODE] Mock appointment creation for {appointment.contact_id}")
            return f"mock_appointment_{int(datetime.utcnow().timestamp())}"

        # Note: GHL calendar API integration would go here
        # For now, return mock ID
        logger.info(f"Creating appointment in GHL for {appointment.contact_id}")
        return f"ghl_appt_{int(datetime.utcnow().timestamp())}"

    async def _log_appointment(
        self,
        appointment: AppointmentDetails,
        ghl_appointment_id: str,
    ) -> None:
        """Log appointment to database."""
        if not self.db_session:
            return

        try:
            bot_appointment = BotAppointment(
                contact_id=appointment.contact_id,
                ghl_appointment_id=ghl_appointment_id,
                title=appointment.title,
                start_time=appointment.start_time,
                end_time=appointment.end_time,
                calendar_id=appointment.calendar_id,
                location=appointment.location,
                notes=appointment.notes,
                status="scheduled",
            )
            self.db_session.add(bot_appointment)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging appointment: {e}")

    async def _log_workflow_operation(
        self,
        contact_id: str,
        operation_type: str,
        operation_data: Dict[str, Any],
        status: OperationStatus,
        error_message: Optional[str] = None,
    ) -> None:
        """Log workflow operation to database."""
        if not self.db_session:
            return

        try:
            operation = GHLWorkflowOperation(
                contact_id=contact_id,
                operation_type=operation_type,
                operation_data=operation_data,
                status=status.value,
                error_message=error_message,
                completed_at=datetime.utcnow() if status == OperationStatus.SUCCESS else None,
            )
            self.db_session.add(operation)
            await self.db_session.commit()
        except Exception as e:
            logger.error(f"Error logging workflow operation: {e}")

    def _determine_pipeline_trigger(
        self,
        current_stage: PipelineStage,
        scores: Dict[str, float],
        conversation_state: Dict[str, Any],
    ) -> Optional[str]:
        """Determine pipeline transition trigger based on scores and state."""
        composite_score = scores.get("composite_score", 0)
        frs_score = scores.get("frs_score", 0)
        pcs_score = scores.get("pcs_score", 0)

        # Check for first message
        if current_stage == PipelineStage.NEW and conversation_state.get("message_count", 0) > 0:
            return "first_message"

        # Check for qualification
        if current_stage == PipelineStage.QUALIFYING:
            if frs_score >= 60 and pcs_score >= 60:
                return "qualified"

        # Check for hot/warm lead
        if current_stage == PipelineStage.QUALIFIED:
            if composite_score >= 80:
                return "hot"
            elif composite_score >= 60:
                return "warm"

        # Check for appointment booking
        if current_stage in [PipelineStage.HOT_LEAD, PipelineStage.WARM_LEAD]:
            if conversation_state.get("appointment_booked"):
                return "appointment_booked"

        # Check for appointment completion
        if current_stage == PipelineStage.APPOINTMENT_SCHEDULED:
            if conversation_state.get("appointment_completed"):
                return "completed"

        # Check for no response
        if current_stage == PipelineStage.FOLLOW_UP:
            days_no_response = conversation_state.get("days_no_response", 0)
            if days_no_response >= 30:
                return "no_response_30d"
            elif days_no_response >= 7:
                return "no_response_7d"

        # Check for no response from re-engagement
        if current_stage == PipelineStage.RE_ENGAGEMENT:
            days_no_response = conversation_state.get("days_no_response", 0)
            if days_no_response >= 30:
                return "no_response_30d"

        # Check for closed status
        if current_stage == PipelineStage.FOLLOW_UP:
            if conversation_state.get("status") == "closed_won":
                return "closed_won"
            elif conversation_state.get("status") == "closed_lost":
                return "closed_lost"

        return None
