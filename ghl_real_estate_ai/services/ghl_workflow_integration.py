"""
GHL Workflow Integration Module

This module provides integration helpers for adding GHL workflow capabilities
to bots (Lead, Buyer, Seller) without modifying their core implementation.
"""

from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.ghl_workflow_service import (
    AppointmentDetails,
    GHLWorkflowService,
    PipelineStage,
    WorkflowResult,
)

logger = get_logger(__name__)


class GHLWorkflowIntegrator:
    """
    Helper class for integrating GHL workflow operations into bot workflows.

    This class provides methods to:
    - Apply auto-tags based on lead scores and signals
    - Update pipeline stages based on lead progression
    - Sync appointments to GHL calendar
    - Sync bot-collected data to GHL contacts
    """

    def __init__(self, ghl_client=None, db_session=None):
        """
        Initialize GHL workflow integrator.

        Args:
            ghl_client: Enhanced GHL client instance
            db_session: Database session for logging operations
        """
        self.workflow_service = GHLWorkflowService(
            ghl_client=ghl_client,
            db_session=db_session,
        )

    async def process_lead_workflow(
        self,
        contact_id: str,
        scores: Dict[str, float],
        persona: Optional[str] = None,
        sentiment: Optional[str] = None,
        escalation: bool = False,
        appointment_booked: bool = False,
        current_stage: Optional[PipelineStage] = None,
        conversation_state: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Process complete GHL workflow for a lead.

        This method:
        1. Applies auto-tags based on scores and signals
        2. Updates pipeline stage based on lead progression
        3. Syncs bot-collected data to GHL contact

        Args:
            contact_id: GHL contact ID
            scores: Dictionary of scores (frs_score, pcs_score, composite_score, urgency_level)
            persona: Buyer/seller persona type
            sentiment: Sentiment analysis result
            escalation: Whether escalation was triggered
            appointment_booked: Whether appointment was booked
            current_stage: Current pipeline stage
            conversation_state: Conversation state with triggers

        Returns:
            Dict containing workflow results
        """
        results = {
            "tags_applied": [],
            "tags_removed": [],
            "stage_updated": False,
            "data_synced": False,
            "errors": [],
        }

        try:
            # Apply auto-tags
            tag_result = await self.workflow_service.apply_auto_tags(
                contact_id=contact_id,
                scores=scores,
                persona=persona,
                sentiment=sentiment,
                escalation=escalation,
                appointment_booked=appointment_booked,
            )

            results["tags_applied"] = tag_result.tags_applied
            results["tags_removed"] = tag_result.tags_removed
            results["errors"].extend(tag_result.errors)

            # Update pipeline stage if provided
            if current_stage and conversation_state:
                pipeline_result = await self.workflow_service.update_pipeline_stage(
                    contact_id=contact_id,
                    current_stage=current_stage,
                    scores=scores,
                    conversation_state=conversation_state,
                )

                results["stage_updated"] = pipeline_result.stage_updated
                results["errors"].extend(pipeline_result.errors)

            # Sync bot-collected data
            bot_data = {
                "frs_score": scores.get("frs_score"),
                "pcs_score": scores.get("pcs_score"),
                "composite_score": scores.get("composite_score"),
                "persona": persona,
            }

            data_synced = await self.workflow_service.sync_contact_data(
                contact_id=contact_id,
                bot_data=bot_data,
            )

            results["data_synced"] = data_synced

            logger.info(
                f"GHL workflow processed for contact {contact_id}: "
                f"{len(results['tags_applied'])} tags applied, "
                f"stage_updated={results['stage_updated']}, "
                f"data_synced={results['data_synced']}"
            )

        except Exception as e:
            logger.error(f"Error processing GHL workflow for contact {contact_id}: {e}")
            results["errors"].append(str(e))

        return results

    async def sync_appointment(
        self,
        contact_id: str,
        title: str,
        start_time,
        end_time,
        calendar_id: str,
        location: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Sync appointment to GHL calendar.

        Args:
            contact_id: GHL contact ID
            title: Appointment title
            start_time: Appointment start time
            end_time: Appointment end time
            calendar_id: GHL calendar ID
            location: Physical or virtual location
            notes: Additional notes

        Returns:
            Dict containing sync results
        """
        results = {
            "appointment_synced": False,
            "ghl_appointment_id": None,
            "errors": [],
        }

        try:
            appointment = AppointmentDetails(
                contact_id=contact_id,
                title=title,
                start_time=start_time,
                end_time=end_time,
                calendar_id=calendar_id,
                location=location,
                notes=notes,
            )

            sync_result = await self.workflow_service.sync_appointment(appointment)

            results["appointment_synced"] = sync_result.appointment_synced
            results["errors"].extend(sync_result.errors)

            if sync_result.appointment_synced:
                logger.info(f"Appointment synced for contact {contact_id}")

        except Exception as e:
            logger.error(f"Error syncing appointment for contact {contact_id}: {e}")
            results["errors"].append(str(e))

        return results

    async def detect_and_sync_appointment(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, Any]],
        calendar_id: str,
    ) -> Dict[str, Any]:
        """
        Detect appointment request in conversation and sync to GHL.

        Args:
            contact_id: GHL contact ID
            conversation_history: List of conversation messages
            calendar_id: GHL calendar ID

        Returns:
            Dict containing detection and sync results
        """
        results = {
            "appointment_detected": False,
            "appointment_synced": False,
            "ghl_appointment_id": None,
            "errors": [],
        }

        try:
            # Detect appointment request
            appointment = await self.workflow_service.detect_appointment_request(
                conversation_history=conversation_history,
            )

            if appointment:
                results["appointment_detected"] = True

                # Sync appointment
                sync_result = await self.workflow_service.sync_appointment(appointment)

                results["appointment_synced"] = sync_result.appointment_synced
                results["errors"].extend(sync_result.errors)

                if sync_result.appointment_synced:
                    logger.info(f"Appointment detected and synced for contact {contact_id}")
            else:
                logger.debug(f"No appointment request detected for contact {contact_id}")

        except Exception as e:
            logger.error(f"Error detecting/syncing appointment for contact {contact_id}: {e}")
            results["errors"].append(str(e))

        return results


# Convenience functions for quick integration

async def apply_lead_tags(
    contact_id: str,
    scores: Dict[str, float],
    persona: Optional[str] = None,
    sentiment: Optional[str] = None,
    ghl_client=None,
) -> WorkflowResult:
    """
    Quick function to apply auto-tags to a lead.

    Args:
        contact_id: GHL contact ID
        scores: Dictionary of scores
        persona: Buyer/seller persona type
        sentiment: Sentiment analysis result
        ghl_client: Enhanced GHL client instance

    Returns:
        WorkflowResult with applied tags
    """
    workflow_service = GHLWorkflowService(ghl_client=ghl_client)
    return await workflow_service.apply_auto_tags(
        contact_id=contact_id,
        scores=scores,
        persona=persona,
        sentiment=sentiment,
    )


async def update_lead_pipeline(
    contact_id: str,
    current_stage: PipelineStage,
    scores: Dict[str, float],
    conversation_state: Dict[str, Any],
    ghl_client=None,
) -> WorkflowResult:
    """
    Quick function to update lead pipeline stage.

    Args:
        contact_id: GHL contact ID
        current_stage: Current pipeline stage
        scores: Dictionary of scores
        conversation_state: Conversation state with triggers
        ghl_client: Enhanced GHL client instance

    Returns:
        WorkflowResult with stage update status
    """
    workflow_service = GHLWorkflowService(ghl_client=ghl_client)
    return await workflow_service.update_pipeline_stage(
        contact_id=contact_id,
        current_stage=current_stage,
        scores=scores,
        conversation_state=conversation_state,
    )


async def sync_lead_appointment(
    contact_id: str,
    title: str,
    start_time,
    end_time,
    calendar_id: str,
    location: Optional[str] = None,
    notes: Optional[str] = None,
    ghl_client=None,
) -> WorkflowResult:
    """
    Quick function to sync appointment to GHL.

    Args:
        contact_id: GHL contact ID
        title: Appointment title
        start_time: Appointment start time
        end_time: Appointment end time
        calendar_id: GHL calendar ID
        location: Physical or virtual location
        notes: Additional notes
        ghl_client: Enhanced GHL client instance

    Returns:
        WorkflowResult with appointment sync status
    """
    workflow_service = GHLWorkflowService(ghl_client=ghl_client)
    appointment = AppointmentDetails(
        contact_id=contact_id,
        title=title,
        start_time=start_time,
        end_time=end_time,
        calendar_id=calendar_id,
        location=location,
        notes=notes,
    )
    return await workflow_service.sync_appointment(appointment)
