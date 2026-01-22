#!/usr/bin/env python3
"""
Jorge's Follow-up Scheduler

This module manages the scheduling and automation of follow-up sequences:
- GHL workflow integration for automated triggers
- Time-based scheduling (2-3 days → 14 days)
- Batch processing for multiple contacts
- Webhook endpoints for follow-up triggers

Author: Claude Code Assistant
Created: 2026-01-19
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json

from ghl_real_estate_ai.services.jorge.jorge_followup_engine import (
    JorgeFollowUpEngine, FollowUpType, FollowUpSchedule
)

logger = logging.getLogger(__name__)


class SchedulerTriggerType(Enum):
    """Types of scheduler triggers"""
    TIME_BASED = "time_based"           # Regular interval triggers
    WEBHOOK_TRIGGER = "webhook_trigger" # Manual/workflow triggers
    BATCH_PROCESSING = "batch_processing" # Bulk processing
    TEMPERATURE_CHANGE = "temperature_change" # Seller temperature changes


@dataclass
class ScheduledFollowUp:
    """Container for scheduled follow-up data"""
    contact_id: str
    location_id: str
    scheduled_date: datetime
    follow_up_type: FollowUpType
    sequence_position: int
    seller_temperature: str
    priority: int = 0  # 0=normal, 1=high, 2=urgent


class JorgeFollowUpScheduler:
    """
    Manages automated scheduling and execution of Jorge's follow-up sequences.
    
    Features:
    1. GHL workflow integration for automated triggers
    2. Time-based scheduling with configurable intervals
    3. Batch processing for efficient execution
    4. Priority-based execution queue
    5. Error handling and retry logic
    """

    def __init__(self, conversation_manager=None, ghl_client=None, analytics_service=None):
        """Initialize scheduler with required services"""
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.analytics_service = analytics_service
        self.followup_engine = JorgeFollowUpEngine(conversation_manager, ghl_client)
        self.schedule_config = FollowUpSchedule()
        
        # Swarm Coordination: Cache & RAG Warming
        from ghl_real_estate_ai.services.cache_service import get_cache_service
        from ghl_real_estate_ai.core.rag_engine import RAGEngine
        from ghl_real_estate_ai.services.autonomous_ab_testing import get_autonomous_ab_testing
        
        self.cache = get_cache_service()
        self.rag_engine = RAGEngine()
        self.ab_testing = get_autonomous_ab_testing()
        
        self.logger = logging.getLogger(__name__)

    async def _get_or_create_follow_up_test(self) -> str:
        """Ensures a follow-up sequence A/B test exists and returns its ID."""
        test_name = "Follow-up Strategy Optimization"
        from ghl_real_estate_ai.services.autonomous_ab_testing import TestType
        
        # Check if already in active tests
        for test_id, config in self.ab_testing.active_tests.items():
            if config.test_name == test_name:
                return test_id
                
        # Create new test
        variants = [
            {"name": "Standard Direct", "description": "Jorge's standard confrontational style"},
            {"name": "Educational Hook", "description": "Subtly more educational before the close"},
            {"name": "Urgency Escalation", "description": "Heavy emphasis on market speed"}
        ]
        
        test_config = await self.ab_testing.create_test(
            test_name=test_name,
            test_type=TestType.FOLLOW_UP_SEQUENCE,
            variants=variants,
            target_metrics=["response_rate", "conversion_rate"],
            success_criteria={"response_rate": 0.15}
        )
        
        # Activate the test
        from ghl_real_estate_ai.services.autonomous_ab_testing import TestStatus
        test_config.status = TestStatus.ACTIVE
        
        return test_config.test_id

    async def process_webhook_follow_up(
        self,
        contact_id: str,
        location_id: str,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process follow-up triggered by GHL webhook.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID
            webhook_data: Webhook payload data
            
        Returns:
            Follow-up processing result
        """
        try:
            self.logger.info(f"Processing webhook follow-up for contact {contact_id}")
            
            # Extract seller data from webhook
            seller_data = await self._extract_seller_data_from_webhook(
                contact_id=contact_id,
                location_id=location_id, 
                webhook_data=webhook_data
            )
            
            # Determine if follow-up should be triggered
            should_trigger = await self._should_trigger_follow_up(seller_data)
            
            if not should_trigger:
                self.logger.info(f"Follow-up not triggered for contact {contact_id} - conditions not met")
                return {
                    "status": "skipped",
                    "reason": "Follow-up conditions not met",
                    "contact_id": contact_id
                }
            
            # --- SWARM COORDINATION: PRE-WARM RAG CACHE ---
            # Pre-calculate RAG context for expected replies to this follow-up
            try:
                # Map follow-up sequence to conversation stage for prefetching
                stage = "initial"
                if seller_data.get("questions_answered", 0) >= 2:
                    stage = "qualification"
                
                await self.cache.predictive_prefetch(
                    contact_id=contact_id,
                    conversation_stage=stage,
                    rag_engine_ref=self.rag_engine
                )
            except Exception as pe:
                self.logger.warning(f"RAG prefetch failed for contact {contact_id}: {pe}")

            # --- AUTONOMOUS A/B TESTING: ALLOCATE VARIANT ---
            variant_config = None
            try:
                test_id = await self._get_or_create_follow_up_test()
                variant = await self.ab_testing.allocate_participant(
                    test_id=test_id,
                    participant_id=contact_id,
                    context=seller_data
                )
                if variant:
                    variant_config = variant.configuration
                    variant_config["variant_id"] = variant.variant_id
                    variant_config["test_id"] = test_id
            except Exception as ab_e:
                self.logger.warning(f"A/B test allocation failed: {ab_e}")

            # Process the follow-up
            follow_up_result = await self.followup_engine.process_follow_up_trigger(
                contact_id=contact_id,
                location_id=location_id,
                trigger_type="webhook_trigger",
                seller_data=seller_data,
                variant_config=variant_config
            )
            
            # Execute actions via GHL
            if follow_up_result.get("actions"):
                await self._execute_follow_up_actions(
                    contact_id=contact_id,
                    location_id=location_id,
                    actions=follow_up_result["actions"],
                    message=follow_up_result.get("message", "")
                )
            
            # Schedule next follow-up if needed
            if follow_up_result.get("next_follow_up"):
                await self._schedule_next_follow_up(
                    contact_id=contact_id,
                    location_id=location_id,
                    next_follow_up=follow_up_result["next_follow_up"]
                )
            
            # --- FEEDBACK LOOP: Save A/B Test State to Context ---
            if self.conversation_manager:
                await self.conversation_manager.update_context(
                    contact_id=contact_id,
                    location_id=location_id,
                    user_message="", # No user message yet
                    ai_response=follow_up_result.get("message", ""),
                    active_ab_test=variant_config,
                    last_ai_message_type="follow_up"
                )

            # Track analytics
            await self._track_follow_up_analytics(
                contact_id=contact_id,
                follow_up_result=follow_up_result,
                trigger_type="webhook",
                variant_config=variant_config
            )
            
            return {
                "status": "success",
                "message_sent": follow_up_result.get("message", ""),
                "actions_executed": len(follow_up_result.get("actions", [])),
                "next_follow_up": follow_up_result.get("next_follow_up"),
                "contact_id": contact_id
            }
            
        except Exception as e:
            self.logger.error(f"Error processing webhook follow-up: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "contact_id": contact_id
            }

    async def process_scheduled_follow_ups(
        self,
        batch_size: int = 50,
        location_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process scheduled follow-ups in batches.
        
        Args:
            batch_size: Number of contacts to process per batch
            location_id: Optional location filter
            
        Returns:
            Batch processing results
        """
        try:
            self.logger.info(f"Processing scheduled follow-ups (batch size: {batch_size})")
            
            # Get contacts due for follow-up
            due_contacts = await self._get_contacts_due_for_follow_up(
                batch_size=batch_size,
                location_id=location_id
            )
            
            if not due_contacts:
                return {
                    "status": "success",
                    "processed": 0,
                    "message": "No contacts due for follow-up"
                }
            
            # Process each contact
            results = {
                "processed": 0,
                "successful": 0,
                "failed": 0,
                "errors": []
            }
            
            for contact_info in due_contacts:
                try:
                    contact_id = contact_info["contact_id"]
                    location_id = contact_info["location_id"]
                    
                    # Get seller data
                    seller_data = await self._get_seller_data_for_contact(
                        contact_id=contact_id,
                        location_id=location_id
                    )
                    
                    # --- SWARM COORDINATION: PRE-WARM RAG CACHE ---
                    try:
                        stage = "initial"
                        if seller_data.get("questions_answered", 0) >= 2:
                            stage = "qualification"
                        
                        await self.cache.predictive_prefetch(
                            contact_id=contact_id,
                            conversation_stage=stage,
                            rag_engine_ref=self.rag_engine
                        )
                    except Exception as pe:
                        self.logger.warning(f"RAG prefetch failed for contact {contact_id}: {pe}")

                    # --- AUTONOMOUS A/B TESTING: ALLOCATE VARIANT ---
                    variant_config = None
                    try:
                        test_id = await self._get_or_create_follow_up_test()
                        variant = await self.ab_testing.allocate_participant(
                            test_id=test_id,
                            participant_id=contact_id,
                            context=seller_data
                        )
                        if variant:
                            variant_config = variant.configuration
                            variant_config["variant_id"] = variant.variant_id
                            variant_config["test_id"] = test_id
                    except Exception as ab_e:
                        self.logger.warning(f"A/B test allocation failed: {ab_e}")

                    # Process follow-up
                    follow_up_result = await self.followup_engine.process_follow_up_trigger(
                        contact_id=contact_id,
                        location_id=location_id,
                        trigger_type="time_based",
                        seller_data=seller_data,
                        variant_config=variant_config
                    )
                    
                    # Execute actions
                    if follow_up_result.get("actions"):
                        await self._execute_follow_up_actions(
                            contact_id=contact_id,
                            location_id=location_id,
                            actions=follow_up_result["actions"],
                            message=follow_up_result.get("message", "")
                        )
                    
                    # Schedule next follow-up
                    if follow_up_result.get("next_follow_up"):
                        await self._schedule_next_follow_up(
                            contact_id=contact_id,
                            location_id=location_id,
                            next_follow_up=follow_up_result["next_follow_up"]
                        )
                    
                    # --- FEEDBACK LOOP: Save A/B Test State to Context ---
                    if self.conversation_manager:
                        await self.conversation_manager.update_context(
                            contact_id=contact_id,
                            location_id=location_id,
                            user_message="", # No user message yet
                            ai_response=follow_up_result.get("message", ""),
                            active_ab_test=variant_config,
                            last_ai_message_type="follow_up"
                        )

                    results["successful"] += 1
                    
                except Exception as e:
                    self.logger.error(f"Error processing follow-up for {contact_id}: {e}")
                    results["failed"] += 1
                    results["errors"].append(f"Contact {contact_id}: {str(e)}")
                
                results["processed"] += 1
                
                # Small delay to avoid rate limiting
                await asyncio.sleep(0.1)
            
            self.logger.info(
                f"Batch processing completed - "
                f"Processed: {results['processed']}, "
                f"Successful: {results['successful']}, "
                f"Failed: {results['failed']}"
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error in batch processing: {str(e)}")
            return {
                "status": "error",
                "error": str(e),
                "processed": 0
            }

    async def create_ghl_workflow_triggers(
        self,
        location_id: str
    ) -> Dict[str, Any]:
        """
        Create GHL workflows for automated follow-up triggers.
        
        Args:
            location_id: GHL location ID
            
        Returns:
            Workflow creation results
        """
        workflows = []
        
        try:
            # Workflow 1: Initial Follow-up Trigger (triggered when contact gets "Needs Qualifying" tag)
            initial_workflow = {
                "name": "Jorge Seller - Initial Follow-up",
                "trigger": {
                    "type": "tag_added",
                    "tag": "Needs Qualifying"
                },
                "actions": [
                    {
                        "type": "wait",
                        "duration": "2 days"
                    },
                    {
                        "type": "webhook",
                        "url": "/api/jorge-followup/webhook",
                        "method": "POST",
                        "data": {
                            "trigger_type": "initial_follow_up",
                            "contact_id": "{{contact.id}}",
                            "location_id": location_id,
                            "sequence_position": 1
                        }
                    }
                ]
            }
            workflows.append(initial_workflow)
            
            # Workflow 2: Qualification Retry (triggered when qualification incomplete after 5 days)
            qualification_retry_workflow = {
                "name": "Jorge Seller - Qualification Retry",
                "trigger": {
                    "type": "tag_added",
                    "tag": "Qualification-Incomplete"
                },
                "actions": [
                    {
                        "type": "wait",
                        "duration": "3 days"
                    },
                    {
                        "type": "webhook", 
                        "url": "/api/jorge-followup/webhook",
                        "method": "POST",
                        "data": {
                            "trigger_type": "qualification_retry",
                            "contact_id": "{{contact.id}}",
                            "location_id": location_id
                        }
                    }
                ]
            }
            workflows.append(qualification_retry_workflow)
            
            # Workflow 3: Temperature Escalation (warm sellers)
            temperature_escalation_workflow = {
                "name": "Jorge Seller - Temperature Escalation",
                "trigger": {
                    "type": "tag_added",
                    "tag": "Warm-Seller"
                },
                "actions": [
                    {
                        "type": "wait", 
                        "duration": "7 days"
                    },
                    {
                        "type": "webhook",
                        "url": "/api/jorge-followup/webhook",
                        "method": "POST",
                        "data": {
                            "trigger_type": "temperature_escalation",
                            "contact_id": "{{contact.id}}",
                            "location_id": location_id
                        }
                    }
                ]
            }
            workflows.append(temperature_escalation_workflow)
            
            # Workflow 4: Long-term Nurture (14-day intervals)
            long_term_nurture_workflow = {
                "name": "Jorge Seller - Long-term Nurture",
                "trigger": {
                    "type": "tag_added",
                    "tag": "Long-term-Nurture"
                },
                "actions": [
                    {
                        "type": "wait",
                        "duration": "14 days"
                    },
                    {
                        "type": "webhook",
                        "url": "/api/jorge-followup/webhook", 
                        "method": "POST",
                        "data": {
                            "trigger_type": "long_term_nurture",
                            "contact_id": "{{contact.id}}",
                            "location_id": location_id
                        }
                    }
                ]
            }
            workflows.append(long_term_nurture_workflow)
            
            # Create workflows via GHL API (if GHL client available)
            created_workflows = []
            if self.ghl_client:
                for workflow in workflows:
                    try:
                        # This would be implemented based on GHL API documentation
                        # created_workflow = await self.ghl_client.create_workflow(location_id, workflow)
                        # created_workflows.append(created_workflow)
                        
                        # For now, just log the workflow configuration
                        self.logger.info(f"Workflow template created: {workflow['name']}")
                        created_workflows.append({
                            "name": workflow["name"],
                            "status": "template_created",
                            "requires_manual_setup": True
                        })
                        
                    except Exception as e:
                        self.logger.error(f"Error creating workflow {workflow['name']}: {e}")
            
            return {
                "status": "success",
                "workflows_created": len(created_workflows),
                "workflows": created_workflows,
                "manual_setup_required": True,
                "setup_instructions": self._get_workflow_setup_instructions()
            }
            
        except Exception as e:
            self.logger.error(f"Error creating GHL workflows: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _get_workflow_setup_instructions(self) -> List[str]:
        """Get manual setup instructions for GHL workflows"""
        return [
            "1. In GHL, navigate to Automation → Workflows",
            "2. Create new workflow 'Jorge Seller - Initial Follow-up'",
            "3. Set trigger: Tag Added → 'Needs Qualifying'",
            "4. Add Wait action: 2 days",
            "5. Add Webhook action: POST to /api/jorge-followup/webhook",
            "6. Repeat for other workflow templates",
            "7. Ensure webhook URLs point to your server",
            "8. Test each workflow with a sample contact"
        ]

    async def _extract_seller_data_from_webhook(
        self,
        contact_id: str,
        location_id: str,
        webhook_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract seller data from webhook payload"""
        
        # Get existing conversation context
        if self.conversation_manager:
            context = await self.conversation_manager.get_context(contact_id, location_id)
            seller_data = context.get("seller_preferences", {})
        else:
            seller_data = {}
        
        # Merge with webhook data
        webhook_seller_data = webhook_data.get("seller_data", {})
        seller_data.update(webhook_seller_data)
        
        # Extract from contact data if available
        contact_data = webhook_data.get("contact", {})
        if contact_data:
            seller_data["contact_name"] = contact_data.get("firstName", "")
            seller_data["contact_id"] = contact_data.get("id", contact_id)
        
        # Add timestamp data
        seller_data["last_contact_date"] = webhook_data.get("timestamp", datetime.now().isoformat())
        
        return seller_data

    async def _should_trigger_follow_up(self, seller_data: Dict[str, Any]) -> bool:
        """Determine if follow-up should be triggered"""
        
        # 1. Business Hours Check (Jorge's Requirement: 9 AM - 6 PM)
        if not self._is_business_hours():
            return False

        # Don't follow up with hot sellers (they should be handled by agents)
        if seller_data.get("seller_temperature") == "hot":
            return False
            
        # Don't follow up if contact opted out
        if seller_data.get("opted_out", False):
            return False
            
        # Check if enough time has passed since last follow-up
        last_followup_date = seller_data.get("last_followup_date")
        if last_followup_date:
            try:
                last_followup = datetime.fromisoformat(last_followup_date)
                hours_since_followup = (datetime.now() - last_followup).total_seconds() / 3600
                # Minimum 24 hours between follow-ups
                if hours_since_followup < 24:
                    return False
            except:
                pass
        
        # Check if we've exceeded max follow-up duration
        first_contact_date = seller_data.get("first_contact_date")
        if first_contact_date:
            try:
                first_contact = datetime.fromisoformat(first_contact_date)
                days_since_first_contact = (datetime.now() - first_contact).days
                if days_since_first_contact > self.schedule_config.MAX_FOLLOW_UP_DAYS:
                    return False
            except:
                pass
        
        return True

    def _is_business_hours(self) -> bool:
        """
        Check if current time is within business hours (9 AM - 6 PM).
        TODO: Implement location-specific timezone lookup using location_id.
        Currently uses server time (assumed to be UTC or configured system time).
        """
        now = datetime.now()
        
        # Weekend Check (Optional: Jorge might want weekends)
        # if now.weekday() >= 5: return False 
        
        start_hour = 9
        end_hour = 18 # 6 PM
        
        return start_hour <= now.hour < end_hour

    async def _get_contacts_due_for_follow_up(
        self,
        batch_size: int,
        location_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get contacts that are due for follow-up"""
        
        # This would integrate with your database/storage to find contacts
        # For now, return empty list as placeholder
        contacts_due = []
        
        try:
            # Query logic would go here to find contacts where:
            # 1. Have "Needs Qualifying" or follow-up tags
            # 2. Last follow-up date > interval threshold
            # 3. Not opted out
            # 4. Not hot sellers
            # 5. Under max follow-up duration
            
            # Placeholder implementation
            self.logger.info(f"Queried for contacts due for follow-up (batch size: {batch_size})")
            
        except Exception as e:
            self.logger.error(f"Error querying contacts due for follow-up: {e}")
        
        return contacts_due

    async def _get_seller_data_for_contact(
        self,
        contact_id: str,
        location_id: str
    ) -> Dict[str, Any]:
        """Get seller data for a specific contact"""
        
        if self.conversation_manager:
            context = await self.conversation_manager.get_context(contact_id, location_id)
            return context.get("seller_preferences", {})
        
        return {}

    async def _execute_follow_up_actions(
        self,
        contact_id: str,
        location_id: str,
        actions: List[Dict[str, Any]],
        message: str
    ) -> None:
        """Execute follow-up actions via GHL API"""
        
        try:
            # Send the message
            if self.ghl_client and message:
                await self.ghl_client.send_message(
                    contact_id=contact_id,
                    location_id=location_id,
                    message=message,
                    message_type="SMS"  # Jorge uses SMS
                )
            
            # Execute other actions (tags, custom fields, workflows)
            if self.ghl_client and actions:
                await self.ghl_client.apply_actions(contact_id, actions)
                
            self.logger.info(f"Follow-up actions executed for contact {contact_id}")
            
        except Exception as e:
            self.logger.error(f"Error executing follow-up actions: {e}")

    async def _schedule_next_follow_up(
        self,
        contact_id: str,
        location_id: str,
        next_follow_up: Dict[str, Any]
    ) -> None:
        """Schedule the next follow-up"""
        
        try:
            # This would integrate with your scheduling system
            # For GHL, this might involve adding tags or triggering workflows
            
            scheduled_date = next_follow_up.get("scheduled_date")
            follow_up_type = next_follow_up.get("type")
            
            self.logger.info(
                f"Next follow-up scheduled for {contact_id} - "
                f"Date: {scheduled_date}, Type: {follow_up_type}"
            )
            
            # Could add a tag to trigger GHL workflow at the right time
            if self.ghl_client:
                await self.ghl_client.apply_actions(contact_id, [{
                    "type": "add_tag",
                    "tag": f"Next-FollowUp-{scheduled_date.split('T')[0]}"
                }])
                
        except Exception as e:
            self.logger.error(f"Error scheduling next follow-up: {e}")

    async def _track_follow_up_analytics(
        self,
        contact_id: str,
        follow_up_result: Dict[str, Any],
        trigger_type: str,
        variant_config: Optional[Dict[str, Any]] = None
    ) -> None:
        """Track follow-up analytics"""
        
        try:
            analytics_data = {
                "contact_id": contact_id,
                "timestamp": datetime.now().isoformat(),
                "trigger_type": trigger_type,
                "follow_up_type": follow_up_result.get("follow_up_type"),
                "sequence_number": follow_up_result.get("sequence_number"),
                "message_length": len(follow_up_result.get("message", "")),
                "actions_count": len(follow_up_result.get("actions", [])),
                "compliance_score": follow_up_result.get("compliance", {}).get("compliance_score", 0)
            }
            
            # Record A/B test data if available
            if variant_config:
                analytics_data["ab_test_id"] = variant_config.get("test_id")
                analytics_data["ab_variant_id"] = variant_config.get("variant_id")
                analytics_data["ab_variant_name"] = variant_config.get("name")
            
            if self.analytics_service:
                await self.analytics_service.track_event(
                    event_type="jorge_followup_sent",
                    data=analytics_data
                )
            
            self.logger.info(f"Follow-up analytics tracked for contact {contact_id}")
            
        except Exception as e:
            self.logger.error(f"Error tracking follow-up analytics: {e}")

    async def get_follow_up_statistics(
        self,
        location_id: Optional[str] = None,
        date_range_days: int = 30
    ) -> Dict[str, Any]:
        """Get follow-up system statistics"""
        
        try:
            # This would query your analytics/database for statistics
            # Placeholder implementation
            
            stats = {
                "total_follow_ups_sent": 0,
                "follow_ups_by_type": {
                    "initial_nurture": 0,
                    "qualification_retry": 0,
                    "temperature_escalation": 0,
                    "long_term_nurture": 0
                },
                "response_rates": {
                    "overall": 0.0,
                    "by_temperature": {
                        "hot": 0.0,
                        "warm": 0.0,
                        "cold": 0.0
                    }
                },
                "conversion_rates": {
                    "cold_to_warm": 0.0,
                    "warm_to_hot": 0.0
                },
                "average_days_to_conversion": 0,
                "date_range": f"Last {date_range_days} days"
            }
            
            return stats
            
        except Exception as e:
            self.logger.error(f"Error getting follow-up statistics: {e}")
            return {"error": str(e)}