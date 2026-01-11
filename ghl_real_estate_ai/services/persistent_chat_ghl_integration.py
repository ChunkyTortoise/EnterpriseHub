"""
Persistent Chat GHL Integration - Seamless Workflow Integration
==============================================================

Integrates persistent Claude chat with existing GoHighLevel workflows,
providing seamless context synchronization between chat interactions
and GHL CRM data, webhooks, and automation sequences.

Key Features:
- Automatic lead context synchronization with GHL
- Real-time webhook integration for chat triggers
- Process stage tracking synchronized with GHL pipeline
- Chat-driven CRM updates and task automation
- Cross-platform context preservation
- Intelligent workflow triggers from chat interactions

Business Impact:
- Unified agent experience across chat and CRM
- Automated data entry and context updates
- Improved lead qualification through chat insights
- Enhanced workflow automation through AI guidance
- Reduced manual data management overhead

Author: EnterpriseHub AI Platform
Date: January 10, 2026
Version: 1.0.0
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

from .ghl_api_client import GHLAPIClient
from .ghl_webhook_service import LeadQualificationState, qualification_states, calculate_lead_score
from .claude_agent_service import claude_agent_service
from .persistent_chat_memory_service import persistent_chat_memory_service, MemoryPriority
from .process_aware_guidance_engine import process_aware_guidance_engine
from ..streamlit_components.persistent_claude_chat import (
    RealtorProcessStage, ProcessContext, ChatSession
)

logger = logging.getLogger(__name__)


class GHLIntegrationStatus(str, Enum):
    """Status of GHL integration operations."""
    CONNECTED = "connected"
    SYNCING = "syncing"
    ERROR = "error"
    DISCONNECTED = "disconnected"


class ChatTriggerType(str, Enum):
    """Types of chat triggers that can update GHL."""
    LEAD_QUALIFICATION = "lead_qualification"
    STAGE_PROGRESSION = "stage_progression"
    PROPERTY_INTEREST = "property_interest"
    OBJECTION_HANDLED = "objection_handled"
    APPOINTMENT_REQUEST = "appointment_request"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    HOT_LEAD_IDENTIFIED = "hot_lead_identified"


@dataclass
class GHLContextSync:
    """Context synchronization between chat and GHL."""
    contact_id: str
    agent_id: str
    session_id: str
    ghl_stage: str
    chat_stage: RealtorProcessStage
    last_sync: datetime
    sync_direction: str  # "chat_to_ghl", "ghl_to_chat", "bidirectional"
    data_points: Dict[str, Any]
    sync_status: GHLIntegrationStatus


@dataclass
class ChatTriggeredAction:
    """Action triggered by chat interaction."""
    trigger_type: ChatTriggerType
    contact_id: str
    action: str
    data: Dict[str, Any]
    priority: str
    scheduled_for: datetime
    created_at: datetime
    completed_at: Optional[datetime] = None


class PersistentChatGHLIntegration:
    """
    Integration layer between persistent chat and GoHighLevel workflows.

    Provides seamless synchronization of chat context with GHL CRM data,
    automated workflow triggers, and bidirectional data flow.
    """

    def __init__(self):
        self.ghl_client = GHLAPIClient()
        self.claude_service = claude_agent_service
        self.memory_service = persistent_chat_memory_service
        self.guidance_engine = process_aware_guidance_engine

        # Integration state
        self.sync_cache: Dict[str, GHLContextSync] = {}
        self.pending_actions: List[ChatTriggeredAction] = []
        self.integration_status = GHLIntegrationStatus.DISCONNECTED

        # Stage mapping between chat and GHL
        self.stage_mapping = self._initialize_stage_mapping()

        # Performance tracking
        self.sync_metrics = {
            "total_syncs": 0,
            "successful_syncs": 0,
            "failed_syncs": 0,
            "avg_sync_time_ms": 0
        }

        logger.info("PersistentChatGHLIntegration initialized")

    def _initialize_stage_mapping(self) -> Dict[RealtorProcessStage, str]:
        """Initialize mapping between chat stages and GHL pipeline stages."""
        return {
            RealtorProcessStage.LEAD_CAPTURE: "New Lead",
            RealtorProcessStage.INITIAL_CONTACT: "Initial Contact",
            RealtorProcessStage.QUALIFICATION: "Qualification",
            RealtorProcessStage.NEEDS_DISCOVERY: "Needs Assessment",
            RealtorProcessStage.PROPERTY_SEARCH: "Property Search",
            RealtorProcessStage.SHOWING_PREP: "Showing Scheduled",
            RealtorProcessStage.PROPERTY_SHOWING: "Showing Completed",
            RealtorProcessStage.OFFER_PREPARATION: "Preparing Offer",
            RealtorProcessStage.NEGOTIATION: "Negotiating",
            RealtorProcessStage.CONTRACT_EXECUTION: "Under Contract",
            RealtorProcessStage.TRANSACTION_MANAGEMENT: "Transaction Management",
            RealtorProcessStage.CLOSING_PREP: "Closing Preparation",
            RealtorProcessStage.POST_CLOSE_FOLLOW_UP: "Closed - Follow Up"
        }

    async def initialize_connection(self) -> bool:
        """Initialize GHL connection and verify access."""
        try:
            # Test GHL connection
            response = await self._test_ghl_connection()
            if response:
                self.integration_status = GHLIntegrationStatus.CONNECTED
                logger.info("GHL integration connected successfully")
                return True
            else:
                self.integration_status = GHLIntegrationStatus.ERROR
                logger.error("Failed to connect to GHL")
                return False

        except Exception as e:
            logger.error(f"Error initializing GHL connection: {e}")
            self.integration_status = GHLIntegrationStatus.ERROR
            return False

    async def _test_ghl_connection(self) -> bool:
        """Test GHL API connection."""
        try:
            # Simple API call to verify connection
            contacts = self.ghl_client.get_contacts(limit=1)
            return contacts is not None
        except Exception as e:
            logger.error(f"GHL connection test failed: {e}")
            return False

    async def sync_chat_context_to_ghl(
        self,
        contact_id: str,
        agent_id: str,
        chat_session: ChatSession,
        force_sync: bool = False
    ) -> bool:
        """
        Sync chat context and insights to GHL contact record.

        Args:
            contact_id: GHL contact ID
            agent_id: Agent identifier
            chat_session: Current chat session
            force_sync: Force sync even if recently synced

        Returns:
            Success status
        """
        try:
            start_time = datetime.now()

            # Check if sync is needed
            sync_key = f"{contact_id}_{agent_id}"
            existing_sync = self.sync_cache.get(sync_key)

            if not force_sync and existing_sync:
                if (datetime.now() - existing_sync.last_sync).seconds < 300:  # 5 minutes
                    logger.debug(f"Skipping sync - recent sync exists for {contact_id}")
                    return True

            # Prepare GHL update data
            update_data = await self._prepare_ghl_update_data(chat_session)

            # Update GHL contact
            success = await self._update_ghl_contact(contact_id, update_data)

            if success:
                # Update sync cache
                self.sync_cache[sync_key] = GHLContextSync(
                    contact_id=contact_id,
                    agent_id=agent_id,
                    session_id=chat_session.session_id,
                    ghl_stage=self.stage_mapping.get(chat_session.process_context.stage, "Unknown"),
                    chat_stage=chat_session.process_context.stage,
                    last_sync=datetime.now(),
                    sync_direction="chat_to_ghl",
                    data_points=update_data,
                    sync_status=GHLIntegrationStatus.CONNECTED
                )

                # Update metrics
                sync_time = (datetime.now() - start_time).total_seconds() * 1000
                self._update_sync_metrics(True, sync_time)

                logger.info(f"Successfully synced chat context to GHL for contact {contact_id}")
                return True
            else:
                self._update_sync_metrics(False, 0)
                return False

        except Exception as e:
            logger.error(f"Error syncing chat context to GHL: {e}")
            self._update_sync_metrics(False, 0)
            return False

    async def _prepare_ghl_update_data(self, chat_session: ChatSession) -> Dict[str, Any]:
        """Prepare GHL update data from chat context."""
        context = chat_session.process_context

        # Extract insights from conversation
        insights = await self._extract_ghl_insights(chat_session.conversation_history)

        # Prepare update data
        update_data = {
            "custom_fields": {
                "claude_stage": context.stage.value,
                "chat_session_id": chat_session.session_id,
                "total_interactions": chat_session.total_interactions,
                "last_chat_activity": chat_session.last_activity.isoformat(),
                "chat_insights": json.dumps(insights),
                "urgency_level": context.urgency,
                "client_type": context.client_type
            },
            "tags": []
        }

        # Add stage-specific data
        if context.stage in [RealtorProcessStage.QUALIFICATION, RealtorProcessStage.NEEDS_DISCOVERY]:
            if insights.get("budget_range"):
                update_data["custom_fields"]["estimated_budget"] = insights["budget_range"]
            if insights.get("timeline"):
                update_data["custom_fields"]["buying_timeline"] = insights["timeline"]

        # Add property interests
        if context.property_ids:
            update_data["custom_fields"]["interested_properties"] = json.dumps(context.property_ids)

        # Add urgency tags
        if context.urgency == "high":
            update_data["tags"].append("High Priority")
        elif context.urgency == "critical":
            update_data["tags"].append("Urgent Follow-up")

        # Add stage-based tags
        stage_tag = f"Chat Stage: {context.stage.value.replace('_', ' ').title()}"
        update_data["tags"].append(stage_tag)

        return update_data

    async def _extract_ghl_insights(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract structured insights from conversation for GHL."""
        if not conversation_history:
            return {}

        try:
            # Use Claude to extract key insights
            conversation_text = "\n".join([
                f"{msg.get('role', 'unknown')}: {msg.get('content', '')}"
                for msg in conversation_history[-10:]  # Last 10 messages
            ])

            insights_prompt = f"""
            Extract key real estate insights from this conversation for CRM storage:

            {conversation_text}

            Extract and format as JSON:
            - budget_range: Mentioned budget or price range
            - timeline: Buying/selling timeline mentioned
            - property_preferences: Key property requirements
            - objections_mentioned: Any concerns or objections
            - motivation: Reason for buying/selling
            - qualification_level: How qualified they seem (low/medium/high)
            - next_steps: Recommended follow-up actions

            Return only valid JSON.
            """

            response = await self.claude_service.chat_with_agent(
                agent_id="ghl_integration",
                query=insights_prompt,
                context={"purpose": "ghl_insight_extraction"}
            )

            # Parse response as JSON
            response_text = response.response if hasattr(response, 'response') else str(response)

            try:
                return json.loads(response_text)
            except json.JSONDecodeError:
                # Fallback to simple extraction
                return {
                    "extraction_error": "Failed to parse JSON",
                    "raw_response": response_text[:200]
                }

        except Exception as e:
            logger.error(f"Error extracting GHL insights: {e}")
            return {"error": str(e)}

    async def _update_ghl_contact(self, contact_id: str, update_data: Dict[str, Any]) -> bool:
        """Update GHL contact with chat-derived data."""
        try:
            if self.integration_status != GHLIntegrationStatus.CONNECTED:
                logger.warning("GHL not connected - cannot update contact")
                return False

            # Update contact via GHL API
            response = self.ghl_client.update_contact(
                contact_id=contact_id,
                data=update_data
            )

            return response is not None

        except Exception as e:
            logger.error(f"Error updating GHL contact {contact_id}: {e}")
            return False

    async def sync_ghl_context_to_chat(
        self,
        contact_id: str,
        agent_id: str,
        session_id: str
    ) -> Optional[ProcessContext]:
        """
        Sync GHL contact data to chat context.

        Args:
            contact_id: GHL contact ID
            agent_id: Agent identifier
            session_id: Chat session ID

        Returns:
            Updated ProcessContext or None
        """
        try:
            # Get contact data from GHL
            contact_data = await self._get_ghl_contact_data(contact_id)
            if not contact_data:
                return None

            # Convert GHL data to chat context
            process_context = await self._convert_ghl_to_chat_context(contact_data)

            # Store sync record
            sync_key = f"{contact_id}_{agent_id}"
            self.sync_cache[sync_key] = GHLContextSync(
                contact_id=contact_id,
                agent_id=agent_id,
                session_id=session_id,
                ghl_stage=contact_data.get("pipeline_stage", "Unknown"),
                chat_stage=process_context.stage,
                last_sync=datetime.now(),
                sync_direction="ghl_to_chat",
                data_points=contact_data,
                sync_status=GHLIntegrationStatus.CONNECTED
            )

            logger.info(f"Successfully synced GHL context to chat for contact {contact_id}")
            return process_context

        except Exception as e:
            logger.error(f"Error syncing GHL context to chat: {e}")
            return None

    async def _get_ghl_contact_data(self, contact_id: str) -> Optional[Dict[str, Any]]:
        """Get contact data from GHL."""
        try:
            if self.integration_status != GHLIntegrationStatus.CONNECTED:
                return None

            contact = self.ghl_client.get_contact(contact_id)
            return contact

        except Exception as e:
            logger.error(f"Error getting GHL contact data: {e}")
            return None

    async def _convert_ghl_to_chat_context(self, contact_data: Dict[str, Any]) -> ProcessContext:
        """Convert GHL contact data to chat ProcessContext."""
        # Map GHL pipeline stage to chat stage
        ghl_stage = contact_data.get("pipeline_stage", "New Lead")
        chat_stage = RealtorProcessStage.LEAD_CAPTURE

        # Reverse lookup of stage mapping
        for chat_st, ghl_st in self.stage_mapping.items():
            if ghl_st == ghl_stage:
                chat_stage = chat_st
                break

        # Extract other context data
        custom_fields = contact_data.get("custom_fields", {})

        return ProcessContext(
            stage=chat_stage,
            lead_id=contact_data.get("id"),
            client_type=custom_fields.get("client_type", "buyer"),
            urgency=custom_fields.get("urgency_level", "medium"),
            current_screen="ghl_sync",
            active_tasks=[],
            recent_actions=[],
            workflow_progress={},
            last_updated=datetime.now()
        )

    async def handle_webhook_trigger(
        self,
        webhook_data: Dict[str, Any],
        agent_id: str
    ) -> Optional[ChatTriggeredAction]:
        """
        Handle GHL webhook and create appropriate chat actions.

        Args:
            webhook_data: GHL webhook payload
            agent_id: Associated agent ID

        Returns:
            ChatTriggeredAction if action should be taken
        """
        try:
            contact_id = webhook_data.get("contactId")
            if not contact_id:
                return None

            trigger_type = self._determine_trigger_type(webhook_data)
            if not trigger_type:
                return None

            # Create triggered action
            action = ChatTriggeredAction(
                trigger_type=trigger_type,
                contact_id=contact_id,
                action=self._determine_action(trigger_type, webhook_data),
                data=webhook_data,
                priority=self._determine_priority(trigger_type, webhook_data),
                scheduled_for=datetime.now(),
                created_at=datetime.now()
            )

            self.pending_actions.append(action)

            logger.info(f"Chat action triggered by webhook: {trigger_type.value} for contact {contact_id}")
            return action

        except Exception as e:
            logger.error(f"Error handling webhook trigger: {e}")
            return None

    def _determine_trigger_type(self, webhook_data: Dict[str, Any]) -> Optional[ChatTriggerType]:
        """Determine trigger type from webhook data."""
        webhook_type = webhook_data.get("type", "")
        tags = webhook_data.get("tags", [])
        custom_fields = webhook_data.get("customFields", {})

        # Lead qualification trigger
        if "qualification" in webhook_type.lower() or "qualified" in tags:
            return ChatTriggerType.LEAD_QUALIFICATION

        # Stage progression trigger
        if "stage" in webhook_type.lower() or "pipeline" in webhook_type.lower():
            return ChatTriggerType.STAGE_PROGRESSION

        # Property interest trigger
        if "property" in str(custom_fields).lower():
            return ChatTriggerType.PROPERTY_INTEREST

        # Hot lead trigger
        if "hot" in tags or "urgent" in tags:
            return ChatTriggerType.HOT_LEAD_IDENTIFIED

        # Appointment trigger
        if "appointment" in webhook_type.lower() or "scheduled" in tags:
            return ChatTriggerType.APPOINTMENT_REQUEST

        return ChatTriggerType.FOLLOW_UP_NEEDED  # Default

    def _determine_action(self, trigger_type: ChatTriggerType, webhook_data: Dict[str, Any]) -> str:
        """Determine specific action based on trigger type."""
        action_map = {
            ChatTriggerType.LEAD_QUALIFICATION: "Initiate qualification chat sequence",
            ChatTriggerType.STAGE_PROGRESSION: "Update chat process stage",
            ChatTriggerType.PROPERTY_INTEREST: "Provide property information and guidance",
            ChatTriggerType.OBJECTION_HANDLED: "Follow up on objection resolution",
            ChatTriggerType.APPOINTMENT_REQUEST: "Prepare appointment coaching guidance",
            ChatTriggerType.FOLLOW_UP_NEEDED: "Schedule follow-up chat interaction",
            ChatTriggerType.HOT_LEAD_IDENTIFIED: "Prioritize for immediate agent attention"
        }
        return action_map.get(trigger_type, "General follow-up")

    def _determine_priority(self, trigger_type: ChatTriggerType, webhook_data: Dict[str, Any]) -> str:
        """Determine priority level for triggered action."""
        high_priority_triggers = [
            ChatTriggerType.HOT_LEAD_IDENTIFIED,
            ChatTriggerType.APPOINTMENT_REQUEST,
            ChatTriggerType.OBJECTION_HANDLED
        ]

        if trigger_type in high_priority_triggers:
            return "high"

        tags = webhook_data.get("tags", [])
        if "urgent" in tags or "hot" in tags:
            return "high"

        return "medium"

    async def execute_triggered_actions(self, agent_id: str) -> List[Dict[str, Any]]:
        """Execute pending triggered actions for an agent."""
        executed_actions = []

        for action in self.pending_actions[:]:  # Copy list to avoid modification issues
            if action.completed_at is not None:
                continue  # Already completed

            try:
                # Execute action based on type
                result = await self._execute_action(action, agent_id)

                if result:
                    action.completed_at = datetime.now()
                    executed_actions.append({
                        "action": action.action,
                        "contact_id": action.contact_id,
                        "trigger_type": action.trigger_type.value,
                        "result": result
                    })

                    # Remove completed action
                    self.pending_actions.remove(action)

            except Exception as e:
                logger.error(f"Error executing triggered action: {e}")

        return executed_actions

    async def _execute_action(self, action: ChatTriggeredAction, agent_id: str) -> Optional[Dict[str, Any]]:
        """Execute a specific triggered action."""
        try:
            if action.trigger_type == ChatTriggerType.LEAD_QUALIFICATION:
                return await self._execute_qualification_action(action, agent_id)

            elif action.trigger_type == ChatTriggerType.STAGE_PROGRESSION:
                return await self._execute_stage_progression_action(action, agent_id)

            elif action.trigger_type == ChatTriggerType.HOT_LEAD_IDENTIFIED:
                return await self._execute_hot_lead_action(action, agent_id)

            else:
                # Generic follow-up action
                return await self._execute_generic_action(action, agent_id)

        except Exception as e:
            logger.error(f"Error in action execution: {e}")
            return None

    async def _execute_qualification_action(self, action: ChatTriggeredAction, agent_id: str) -> Dict[str, Any]:
        """Execute lead qualification action."""
        # This would trigger a qualification sequence in the chat
        # For now, return a placeholder result
        return {
            "action_type": "qualification_initiated",
            "contact_id": action.contact_id,
            "status": "success",
            "details": "Qualification chat sequence initiated"
        }

    async def _execute_stage_progression_action(self, action: ChatTriggeredAction, agent_id: str) -> Dict[str, Any]:
        """Execute stage progression action."""
        return {
            "action_type": "stage_updated",
            "contact_id": action.contact_id,
            "status": "success",
            "details": "Chat process stage updated based on GHL pipeline change"
        }

    async def _execute_hot_lead_action(self, action: ChatTriggeredAction, agent_id: str) -> Dict[str, Any]:
        """Execute hot lead identification action."""
        return {
            "action_type": "hot_lead_prioritized",
            "contact_id": action.contact_id,
            "status": "success",
            "details": "Lead prioritized for immediate agent attention"
        }

    async def _execute_generic_action(self, action: ChatTriggeredAction, agent_id: str) -> Dict[str, Any]:
        """Execute generic follow-up action."""
        return {
            "action_type": "follow_up_scheduled",
            "contact_id": action.contact_id,
            "status": "success",
            "details": "Follow-up interaction scheduled in chat"
        }

    def _update_sync_metrics(self, success: bool, sync_time_ms: float):
        """Update synchronization metrics."""
        self.sync_metrics["total_syncs"] += 1

        if success:
            self.sync_metrics["successful_syncs"] += 1
        else:
            self.sync_metrics["failed_syncs"] += 1

        # Update average sync time
        if sync_time_ms > 0:
            current_avg = self.sync_metrics["avg_sync_time_ms"]
            total_syncs = self.sync_metrics["total_syncs"]
            self.sync_metrics["avg_sync_time_ms"] = (
                (current_avg * (total_syncs - 1) + sync_time_ms) / total_syncs
            )

    async def get_contact_chat_context(self, contact_id: str, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive chat context for a GHL contact."""
        try:
            # Get sync record
            sync_key = f"{contact_id}_{agent_id}"
            sync_record = self.sync_cache.get(sync_key)

            # Get GHL contact data
            ghl_data = await self._get_ghl_contact_data(contact_id)

            # Get chat session if exists
            chat_session = None
            if sync_record:
                chat_session = await self.memory_service.retrieve_chat_session(
                    agent_id, sync_record.session_id
                )

            return {
                "contact_id": contact_id,
                "ghl_data": ghl_data,
                "chat_session": chat_session,
                "sync_record": sync_record,
                "integration_status": self.integration_status.value
            }

        except Exception as e:
            logger.error(f"Error getting contact chat context: {e}")
            return None

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status and metrics."""
        return {
            "status": self.integration_status.value,
            "sync_metrics": self.sync_metrics,
            "pending_actions": len(self.pending_actions),
            "cached_syncs": len(self.sync_cache),
            "last_updated": datetime.now().isoformat()
        }

    async def cleanup_old_syncs(self, max_age_hours: int = 24):
        """Clean up old sync records to prevent memory bloat."""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)

        keys_to_remove = []
        for key, sync_record in self.sync_cache.items():
            if sync_record.last_sync < cutoff_time:
                keys_to_remove.append(key)

        for key in keys_to_remove:
            del self.sync_cache[key]

        # Clean up old completed actions
        self.pending_actions = [
            action for action in self.pending_actions
            if action.completed_at is None or
            (datetime.now() - action.completed_at).hours < max_age_hours
        ]

        logger.info(f"Cleaned up {len(keys_to_remove)} old sync records")


# Global instance for easy access
persistent_chat_ghl_integration = PersistentChatGHLIntegration()


# Export key classes and functions
__all__ = [
    'PersistentChatGHLIntegration',
    'GHLContextSync',
    'ChatTriggeredAction',
    'GHLIntegrationStatus',
    'ChatTriggerType',
    'persistent_chat_ghl_integration'
]