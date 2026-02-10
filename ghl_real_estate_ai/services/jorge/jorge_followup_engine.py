#!/usr/bin/env python3
"""
Jorge's Follow-up Automation Engine

This module handles automated follow-up sequences for seller leads:
- 2-3 day intervals for first 30 days
- 14-day intervals ongoing after 30 days
- Temperature-based nurture content
- Integration with GHL workflows

Author: Claude Code Assistant
Created: 2026-01-19
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
import logging

from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

logger = logging.getLogger(__name__)


class FollowUpType(Enum):
    """Types of follow-up sequences"""
    INITIAL_NURTURE = "initial_nurture"      # 2-3 days for 30 days
    LONG_TERM_NURTURE = "long_term_nurture"  # 14 days ongoing
    QUALIFICATION_RETRY = "qualification_retry"  # Retry incomplete qualification
    TEMPERATURE_ESCALATION = "temperature_escalation"  # Warm → Hot attempts
    BEHAVIORAL_REACTIVATION = "behavioral_reactivation" # Reactivate based on intent signals


@dataclass
class FollowUpSchedule:
    """Schedule configuration for follow-up sequences"""
    
    # Initial 30-day sequence (2-3 day intervals)
    INITIAL_SEQUENCE_DAYS = [2, 5, 8, 12, 16, 20, 25, 30]
    
    # Long-term sequence (14-day intervals)
    LONG_TERM_INTERVAL_DAYS = 14
    
    # Maximum follow-up duration (6 months)
    MAX_FOLLOW_UP_DAYS = 180


@dataclass
class FollowUpMessage:
    """Container for follow-up message data"""
    content: str
    message_type: FollowUpType
    temperature: str
    sequence_number: int
    days_since_last_contact: int
    compliance_score: float


class JorgeFollowUpEngine:
    """
    Manages Jorge's automated follow-up sequences for seller leads.
    
    Features:
    1. Temperature-based content (Hot/Warm/Cold)
    2. Time-based scheduling (2-3 days → 14 days)
    3. Jorge's confrontational tone consistency
    4. GHL workflow integration
    """

    def __init__(self, conversation_manager=None, ghl_client=None):
        """Initialize with conversation manager and GHL client"""
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.tone_engine = JorgeToneEngine()
        self.schedule = FollowUpSchedule()
        self.logger = logging.getLogger(__name__)

    async def process_follow_up_trigger(
        self,
        contact_id: str,
        location_id: str,
        trigger_type: str,
        seller_data: Dict[str, Any],
        variant_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for follow-up automation.
        
        Args:
            contact_id: GHL contact ID
            location_id: GHL location ID  
            trigger_type: Type of follow-up trigger (time_based, temperature_change, etc.)
            seller_data: Current seller profile data
            variant_config: Optional A/B test variant configuration
            
        Returns:
            Follow-up result with message, actions, and scheduling
        """
        try:
            self.logger.info(f"Processing follow-up trigger for contact {contact_id}")
            
            # 1. Determine follow-up type and timing
            follow_up_config = await self._determine_follow_up_type(
                seller_data=seller_data,
                trigger_type=trigger_type
            )
            
            # 2. Generate appropriate follow-up message
            follow_up_message = await self._generate_follow_up_message(
                seller_data=seller_data,
                follow_up_config=follow_up_config,
                contact_id=contact_id,
                variant_config=variant_config
            )
            
            # 3. Create follow-up actions (tags, workflows, scheduling)
            follow_up_actions = await self._create_follow_up_actions(
                contact_id=contact_id,
                location_id=location_id,
                follow_up_config=follow_up_config,
                seller_data=seller_data
            )
            
            # 4. Schedule next follow-up
            next_follow_up = await self._schedule_next_follow_up(
                seller_data=seller_data,
                follow_up_config=follow_up_config
            )
            
            # 5. Update conversation context
            await self._update_follow_up_context(
                contact_id=contact_id,
                location_id=location_id,
                follow_up_message=follow_up_message,
                next_follow_up=next_follow_up
            )
            
            return {
                "message": follow_up_message.content,
                "actions": follow_up_actions,
                "next_follow_up": next_follow_up,
                "follow_up_type": follow_up_message.message_type.value,
                "sequence_number": follow_up_message.sequence_number,
                "compliance": {
                    "character_count": len(follow_up_message.content),
                    "compliance_score": follow_up_message.compliance_score
                }
            }
            
        except Exception as e:
            self.logger.error(f"Error processing follow-up trigger: {str(e)}")
            return {
                "error": str(e),
                "message": "Follow up scheduling failed. Manual intervention required.",
                "actions": []
            }

    async def _determine_follow_up_type(
        self,
        seller_data: Dict[str, Any],
        trigger_type: str
    ) -> Dict[str, Any]:
        """Determine the appropriate follow-up type and timing"""
        
        temperature = seller_data.get("seller_temperature", "cold")
        questions_answered = seller_data.get("questions_answered", 0)
        last_contact_date = seller_data.get("last_contact_date")
        days_since_last_contact = self._calculate_days_since_contact(last_contact_date)
        
        # Determine follow-up sequence position
        if days_since_last_contact <= 30:
            # Initial 30-day sequence (2-3 day intervals)
            sequence_type = FollowUpType.INITIAL_NURTURE
            sequence_position = self._get_initial_sequence_position(days_since_last_contact)
        else:
            # Long-term sequence (14-day intervals)
            sequence_type = FollowUpType.LONG_TERM_NURTURE
            sequence_position = self._get_long_term_sequence_position(days_since_last_contact)
        
        # Special cases override normal sequencing
        if questions_answered < 4 and temperature != "hot":
            sequence_type = FollowUpType.QUALIFICATION_RETRY
        elif temperature == "warm" and days_since_last_contact >= 7:
            sequence_type = FollowUpType.TEMPERATURE_ESCALATION
            
        return {
            "type": sequence_type,
            "position": sequence_position,
            "days_since_contact": days_since_last_contact,
            "temperature": temperature,
            "questions_answered": questions_answered
        }

    async def _generate_follow_up_message(
        self,
        seller_data: Dict[str, Any],
        follow_up_config: Dict[str, Any],
        contact_id: str,
        variant_config: Optional[Dict[str, Any]] = None
    ) -> FollowUpMessage:
        """Generate appropriate follow-up message based on type and sequence"""
        
        follow_up_type = follow_up_config["type"]
        temperature = follow_up_config["temperature"]
        sequence_position = follow_up_config["position"]
        days_since_contact = follow_up_config["days_since_contact"]
        
        seller_name = seller_data.get("contact_name")
        
        # Generate message based on follow-up type
        if follow_up_type == FollowUpType.QUALIFICATION_RETRY:
            message_content = self._create_qualification_retry_message(
                seller_data, sequence_position, seller_name
            )
        elif follow_up_type == FollowUpType.BEHAVIORAL_REACTIVATION:
            message_content = self._create_behavioral_reactivation_message(
                seller_data, seller_name
            )
        elif follow_up_type == FollowUpType.TEMPERATURE_ESCALATION:
            message_content = self._create_temperature_escalation_message(
                seller_data, sequence_position, seller_name
            )
        elif follow_up_type == FollowUpType.INITIAL_NURTURE:
            message_content = self._create_initial_nurture_message(
                temperature, sequence_position, seller_name
            )
        else:  # LONG_TERM_NURTURE
            message_content = self._create_long_term_nurture_message(
                temperature, sequence_position, seller_name
            )
        
        # --- A/B TESTING: VARIANT ADAPTATION ---
        if variant_config and variant_config.get("name") != "Standard Direct":
            try:
                adapted = await self._adapt_followup_to_variant(
                    message_content, 
                    variant_config["name"]
                )
                if adapted:
                    message_content = adapted
            except Exception as e:
                self.logger.warning(f"Follow-up variant adaptation failed: {e}")

        # Validate message compliance
        compliance_result = self.tone_engine.validate_message_compliance(message_content)
        
        return FollowUpMessage(
            content=message_content,
            message_type=follow_up_type,
            temperature=temperature,
            sequence_number=sequence_position,
            days_since_last_contact=days_since_contact,
            compliance_score=compliance_result.get("directness_score", 0.0)
        )

    async def _adapt_followup_to_variant(self, message: str, variant_name: str) -> str:
        """Subtly adapt follow-up message based on A/B test variant."""
        try:
            from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
            llm_client = LLMClient(provider="claude")

            variant_prompts = {
                "Educational Hook": "Subtly add a small educational insight or market context before the close. Maintain Jorge's directness.",
                "Urgency Escalation": "Increase the sense of market urgency and speed. Emphasize why waiting costs money."
            }
            
            instruction = variant_prompts.get(variant_name, "")
            if not instruction:
                return message

            prompt = f"""Adapt this real estate follow-up SMS based on this strategy: {instruction}
            
            ORIGINAL SMS: "{message}"
            
            CONSTRAINTS:
            1. Keep it under 160 characters.
            2. NO EMOJIS. NO HYPHENS.
            3. Maintain Jorge's professional and confrontational style.
            
            Return ONLY the adjusted message text."""

            response = await llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are a linguistic adaptation engine for SMS real estate marketing.",
                temperature=0.3,
                max_tokens=100,
                complexity=TaskComplexity.ROUTINE
            )
            
            adapted = response.content.strip()
            return self.tone_engine._ensure_sms_compliance(adapted)
        except Exception:
            return message

    def _create_qualification_retry_message(
        self,
        seller_data: Dict[str, Any],
        sequence_position: int,
        seller_name: Optional[str]
    ) -> str:
        """Create message to retry incomplete qualification"""
        
        questions_answered = seller_data.get("questions_answered", 0)
        
        # Escalating urgency based on sequence position
        if sequence_position == 1:
            base_message = "Still interested in selling? I need a few more details to help you."
        elif sequence_position == 2:
            base_message = "Market conditions are changing fast. Can we finish your qualifying questions?"
        elif sequence_position >= 3:
            base_message = "Final check: are you serious about selling or should I remove you from our list?"
        else:
            base_message = "Do you still need help selling your home?"
        
        # Apply tone engine for SMS compliance
        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"
            
        return self.tone_engine._ensure_sms_compliance(base_message)

    def _create_temperature_escalation_message(
        self,
        seller_data: Dict[str, Any],
        sequence_position: int,
        seller_name: Optional[str]
    ) -> str:
        """Create message to escalate warm sellers to hot"""
        
        if sequence_position == 1:
            base_message = "Market update: home values in your area increased 8% this quarter. Ready to discuss selling?"
        elif sequence_position == 2:
            base_message = "Interest rates dropped. Now might be the perfect time to make your move. Thoughts?"
        else:
            base_message = "Last chance to get ahead of the spring market rush. Should we schedule a quick call?"
        
        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"
            
        return self.tone_engine._ensure_sms_compliance(base_message)

    def _create_behavioral_reactivation_message(
        self,
        seller_data: Dict[str, Any],
        seller_name: Optional[str]
    ) -> str:
        """Create confrontational re-engagement message based on behavioral signals"""
        
        # Trigger reason (default to valuation search)
        trigger = seller_data.get("last_behavioral_trigger", "checking home values")
        
        base_message = f"I saw you were {trigger} again. Are you ready to be serious about selling or should we stop wasting time?"
        
        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"
            
        return self.tone_engine._ensure_sms_compliance(base_message)

    def _create_initial_nurture_message(
        self,
        temperature: str,
        sequence_position: int,
        seller_name: Optional[str]
    ) -> str:
        """Create initial nurture message (first 30 days)"""
        
        # Different messages based on temperature and sequence
        if temperature == "cold":
            messages = [
                "Things change. If your selling timeline moves up, let me know.",
                "Keeping you updated: home sales in your area are strong this month.",
                "Quick question: has your situation changed at all since we talked?",
                "Market alert: prices in your neighborhood jumped 3% last month."
            ]
        elif temperature == "warm":
            messages = [
                "Following up on our conversation. Any updates on your selling timeline?",
                "Market update: multiple offers are common in your area right now.",
                "Checking in: are you any closer to making a decision about selling?",
                "New data shows your area is trending up. Want to discuss options?"
            ]
        else:  # hot (shouldn't normally get here, but safety)
            messages = [
                "Our team is ready when you are. What works for scheduling?",
                "Quick follow up on next steps for your home sale.",
                "Touching base about your selling timeline. Still on track?",
                "Checking in on your home sale progress."
            ]
        
        # Select message based on sequence position
        message_index = (sequence_position - 1) % len(messages)
        base_message = messages[message_index]
        
        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"
            
        return self.tone_engine._ensure_sms_compliance(base_message)

    def _create_long_term_nurture_message(
        self,
        temperature: str,
        sequence_position: int,
        seller_name: Optional[str]
    ) -> str:
        """Create long-term nurture message (14-day intervals)"""
        
        # Rotate through different long-term messages
        messages = [
            "Quarterly market update: home values continue rising in your area.",
            "New buyer financing options might affect your selling strategy.",
            "Spring market preview: early indicators show strong seller conditions.",
            "Tax season reminder: selling could impact your 2026 filing strategy.",
            "Interest rate update: changes could affect your selling decision.",
            "Summer market outlook: historically strong for sellers in your area."
        ]
        
        message_index = (sequence_position - 1) % len(messages)
        base_message = messages[message_index]
        
        if seller_name:
            base_message = f"{seller_name}, {base_message.lower()}"
            
        return self.tone_engine._ensure_sms_compliance(base_message)

    async def _create_follow_up_actions(
        self,
        contact_id: str,
        location_id: str,
        follow_up_config: Dict[str, Any],
        seller_data: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create GHL actions for follow-up processing"""
        
        actions = []
        follow_up_type = follow_up_config["type"]
        sequence_position = follow_up_config["position"]
        
        # Update follow-up sequence tag
        actions.append({
            "type": "add_tag",
            "tag": f"FollowUp-Seq-{sequence_position}"
        })
        
        # Remove previous sequence tag
        if sequence_position > 1:
            actions.append({
                "type": "remove_tag", 
                "tag": f"FollowUp-Seq-{sequence_position - 1}"
            })
        
        # Type-specific actions
        if follow_up_type == FollowUpType.QUALIFICATION_RETRY:
            actions.append({
                "type": "add_tag",
                "tag": "Qualification-Retry"
            })
            
            # Escalation after 3 attempts
            if sequence_position >= 3:
                actions.append({
                    "type": "add_tag", 
                    "tag": "Manual-Review-Required"
                })
                
        elif follow_up_type == FollowUpType.TEMPERATURE_ESCALATION:
            actions.append({
                "type": "add_tag",
                "tag": "Temperature-Escalation"
            })
            
        # Update custom fields for tracking
        actions.append({
            "type": "update_custom_field",
            "field": "last_followup_date",
            "value": datetime.now().strftime("%Y-%m-%d")
        })
        
        actions.append({
            "type": "update_custom_field",
            "field": "followup_sequence_position", 
            "value": str(sequence_position)
        })
        
        return actions

    async def _schedule_next_follow_up(
        self,
        seller_data: Dict[str, Any],
        follow_up_config: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Schedule the next follow-up in the sequence"""

        follow_up_type = follow_up_config["type"]
        sequence_position = follow_up_config["position"]
        days_since_contact = follow_up_config["days_since_contact"]
        temperature = str(
            seller_data.get("seller_temperature", follow_up_config.get("temperature", "cold"))
        ).lower()
        questions_answered = int(seller_data.get("questions_answered", 0) or 0)
        appointment_status = str(seller_data.get("appointment_status", "")).lower()
        appointment_booked = bool(seller_data.get("appointment_booked")) or appointment_status in {
            "booked", "confirmed", "completed"
        }

        # Determine next follow-up date
        next_follow_up_date = None

        # Scope-aligned cadence once qualification is complete:
        # hot=daily (until appointment booked/completed), warm=weekly, cold=monthly.
        if questions_answered >= 4:
            cadence_days = self.tone_engine.config.FOLLOWUP_CADENCE_DAYS.get(temperature)
            if temperature == "hot" and appointment_booked:
                return None
            if cadence_days:
                next_follow_up_date = datetime.now() + timedelta(days=cadence_days)
                return {
                    "scheduled_date": next_follow_up_date.isoformat(),
                    "type": follow_up_type.value,
                    "sequence_position": sequence_position + 1
                }

        if follow_up_type in [FollowUpType.INITIAL_NURTURE, FollowUpType.QUALIFICATION_RETRY]:
            # Check if there's a next position in initial sequence
            if sequence_position < len(self.schedule.INITIAL_SEQUENCE_DAYS):
                days_to_add = self.schedule.INITIAL_SEQUENCE_DAYS[sequence_position] - days_since_contact
                if days_to_add > 0:
                    next_follow_up_date = datetime.now() + timedelta(days=days_to_add)
                else:
                    # Move to long-term sequence
                    next_follow_up_date = datetime.now() + timedelta(days=self.schedule.LONG_TERM_INTERVAL_DAYS)
            else:
                # Transition to long-term sequence
                next_follow_up_date = datetime.now() + timedelta(days=self.schedule.LONG_TERM_INTERVAL_DAYS)
                
        elif follow_up_type == FollowUpType.LONG_TERM_NURTURE:
            # Continue long-term sequence if under max duration
            if days_since_contact < self.schedule.MAX_FOLLOW_UP_DAYS:
                next_follow_up_date = datetime.now() + timedelta(days=self.schedule.LONG_TERM_INTERVAL_DAYS)
            
        elif follow_up_type == FollowUpType.TEMPERATURE_ESCALATION:
            # Limited escalation attempts (max 3)
            if sequence_position < 3:
                next_follow_up_date = datetime.now() + timedelta(days=7)  # Weekly for escalation
        
        if next_follow_up_date:
            return {
                "scheduled_date": next_follow_up_date.isoformat(),
                "type": follow_up_type.value,
                "sequence_position": sequence_position + 1
            }
        
        return None

    async def _update_follow_up_context(
        self,
        contact_id: str,
        location_id: str,
        follow_up_message: FollowUpMessage,
        next_follow_up: Optional[Dict[str, Any]]
    ) -> None:
        """Update conversation context with follow-up data"""
        
        if not self.conversation_manager:
            return
            
        try:
            # Get current context
            context = await self.conversation_manager.get_context(contact_id, location_id)
            
            # Update follow-up tracking
            follow_up_history = context.get("follow_up_history", [])
            follow_up_history.append({
                "date": datetime.now().isoformat(),
                "message": follow_up_message.content,
                "type": follow_up_message.message_type.value,
                "sequence_number": follow_up_message.sequence_number,
                "temperature": follow_up_message.temperature
            })
            
            context["follow_up_history"] = follow_up_history[-10:]  # Keep last 10
            context["last_follow_up_date"] = datetime.now().isoformat()
            context["next_follow_up"] = next_follow_up
            
            # Save updated context
            await self.conversation_manager.save_context(contact_id, context, location_id)
            
        except Exception as e:
            self.logger.error(f"Failed to update follow-up context: {e}")

    def _calculate_days_since_contact(self, last_contact_date: Optional[str]) -> int:
        """Calculate days since last contact"""
        if not last_contact_date:
            return 0
            
        try:
            last_contact = datetime.fromisoformat(last_contact_date.replace('Z', '+00:00'))
            return (datetime.now() - last_contact).days
        except Exception:
            return 0

    def _get_initial_sequence_position(self, days_since_contact: int) -> int:
        """Get position in initial 30-day sequence"""
        for i, day in enumerate(self.schedule.INITIAL_SEQUENCE_DAYS):
            if days_since_contact <= day:
                return i + 1
        return len(self.schedule.INITIAL_SEQUENCE_DAYS)

    def _get_long_term_sequence_position(self, days_since_contact: int) -> int:
        """Get position in long-term sequence"""
        # Calculate which 14-day interval we're in
        intervals_passed = (days_since_contact - 30) // self.schedule.LONG_TERM_INTERVAL_DAYS
        return max(1, intervals_passed + 1)

    async def get_follow_up_analytics(
        self,
        contact_id: str,
        location_id: str
    ) -> Dict[str, Any]:
        """Get follow-up analytics for a contact"""
        
        if not self.conversation_manager:
            return {"error": "Conversation manager not available"}
            
        try:
            context = await self.conversation_manager.get_context(contact_id, location_id)
            follow_up_history = context.get("follow_up_history", [])
            
            return {
                "total_follow_ups": len(follow_up_history),
                "last_follow_up_date": context.get("last_follow_up_date"),
                "next_follow_up": context.get("next_follow_up"),
                "follow_up_history": follow_up_history,
                "current_sequence": {
                    "type": follow_up_history[-1].get("type") if follow_up_history else None,
                    "position": follow_up_history[-1].get("sequence_number") if follow_up_history else 0
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get follow-up analytics: {e}")
            return {"error": str(e)}
