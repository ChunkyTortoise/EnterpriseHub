"""
Jorge's Seller Bot Engine - Main Processing Logic

This module handles the core seller qualification process with Jorge's 4 specific questions
and confrontational tone requirements. Integrates with existing conversation manager
and provides temperature-based lead classification.

Author: Claude Code Assistant
Created: 2026-01-19
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from enum import Enum
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class SellerQuestionType(Enum):
    """Jorge's 4 seller qualification question types"""
    MOTIVATION = "motivation"
    TIMELINE = "timeline"
    CONDITION = "condition"
    PRICE = "price"


@dataclass
class SellerQuestions:
    """Jorge's 4 seller qualification questions in exact order"""

    # Question 1: Motivation & Relocation
    MOTIVATION = "What's got you considering wanting to sell, where would you move to?"

    # Question 2: Timeline Urgency (Critical for Jorge)
    TIMELINE = "If our team sold your home within the next 30 to 45 days, would that pose a problem for you?"

    # Question 3: Property Condition Assessment
    CONDITION = "How would you describe your home, would you say it's move-in ready or would it need some work?"

    # Question 4: Price Expectations
    PRICE = "What price would incentivize you to sell?"

    @classmethod
    def get_question_order(cls) -> List[SellerQuestionType]:
        """Get Jorge's questions in the correct order"""
        return [
            SellerQuestionType.MOTIVATION,
            SellerQuestionType.TIMELINE,
            SellerQuestionType.CONDITION,
            SellerQuestionType.PRICE
        ]

    @classmethod
    def get_next_question(cls, answered_questions: Dict) -> Optional[str]:
        """Get the next unanswered question in Jorge's sequence"""
        question_mapping = {
            SellerQuestionType.MOTIVATION: cls.MOTIVATION,
            SellerQuestionType.TIMELINE: cls.TIMELINE,
            SellerQuestionType.CONDITION: cls.CONDITION,
            SellerQuestionType.PRICE: cls.PRICE
        }

        field_mapping = {
            SellerQuestionType.MOTIVATION: "motivation",
            SellerQuestionType.TIMELINE: "timeline_acceptable",
            SellerQuestionType.CONDITION: "property_condition",
            SellerQuestionType.PRICE: "price_expectation"
        }

        for q_type in cls.get_question_order():
            field_name = field_mapping[q_type]
            if not answered_questions.get(field_name):
                return question_mapping[q_type]
        return None

    @classmethod
    def get_question_number(cls, answered_questions: Dict) -> int:
        """Get the current question number (1-4) based on answered questions"""
        field_mapping = [
            "motivation",
            "timeline_acceptable",
            "property_condition",
            "price_expectation"
        ]

        for i, field in enumerate(field_mapping, 1):
            if not answered_questions.get(field):
                return i
        return 5  # All questions answered


class JorgeSellerEngine:
    """
    Main engine for Jorge's seller qualification bot.
    Handles the 4-question sequence with confrontational tone.
    """

    def __init__(self, conversation_manager, ghl_client):
        """Initialize with existing conversation manager and GHL client"""
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.logger = logging.getLogger(__name__)

    async def process_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Main processing method for Jorge's seller bot.

        Args:
            contact_id: GHL contact ID
            user_message: User's message response
            location_id: GHL location ID
            tenant_config: Tenant configuration settings

        Returns:
            Dict with message, actions, temperature, and analytics data
        """
        try:
            self.logger.info(f"Processing seller response for contact {contact_id}")

            # 1. Get conversation context
            context = await self.conversation_manager.get_context(contact_id, location_id)
            current_seller_data = context.get("seller_preferences", {})

            # 2. Extract seller data from user message
            extracted_seller_data = await self._extract_seller_data(
                user_message=user_message,
                current_seller_data=current_seller_data,
                tenant_config=tenant_config or {}
            )

            # 3. Calculate seller temperature (Hot/Warm/Cold)
            temperature_result = await self._calculate_seller_temperature(extracted_seller_data)
            temperature = temperature_result["temperature"]

            # 4. Generate response based on temperature and progress
            response_result = await self._generate_seller_response(
                seller_data=extracted_seller_data,
                temperature=temperature,
                contact_id=contact_id,
                location_id=location_id
            )

            # 5. Determine actions based on temperature
            actions = await self._create_seller_actions(
                contact_id=contact_id,
                location_id=location_id,
                temperature=temperature,
                seller_data=extracted_seller_data
            )

            # 6. Update conversation context
            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=response_result["message"],
                extracted_data=extracted_seller_data,
                location_id=location_id,
                seller_temperature=temperature
            )

            # 7. Log analytics data
            await self._track_seller_interaction(
                contact_id=contact_id,
                location_id=location_id,
                interaction_data={
                    "temperature": temperature,
                    "questions_answered": extracted_seller_data.get("questions_answered", 0),
                    "response_quality": extracted_seller_data.get("response_quality", 0.0),
                    "message_length": len(response_result["message"])
                }
            )

            return {
                "message": response_result["message"],
                "actions": actions,
                "temperature": temperature,
                "seller_data": extracted_seller_data,
                "questions_answered": extracted_seller_data.get("questions_answered", 0),
                "analytics": temperature_result["analytics"]
            }

        except Exception as e:
            self.logger.error(f"Error processing seller response: {str(e)}")
            # Return safe fallback response
            return {
                "message": "Let me get back to you shortly.",
                "actions": [],
                "temperature": "cold",
                "error": str(e)
            }

    async def _extract_seller_data(
        self,
        user_message: str,
        current_seller_data: Dict,
        tenant_config: Dict
    ) -> Dict:
        """Extract and merge seller data from user message"""
        try:
            # Use existing conversation manager's extraction capabilities
            # but adapt for seller-specific fields
            extracted_data = await self.conversation_manager.extract_seller_data(
                user_message=user_message,
                current_seller_data=current_seller_data,
                tenant_config=tenant_config
            )

            # Ensure questions_answered count is accurate
            question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
            questions_answered = sum(1 for field in question_fields if extracted_data.get(field))
            extracted_data["questions_answered"] = questions_answered

            # Calculate response quality based on message content
            extracted_data["response_quality"] = self._assess_response_quality(user_message)

            return extracted_data

        except Exception as e:
            self.logger.error(f"Seller data extraction failed: {e}")
            return current_seller_data

    async def _calculate_seller_temperature(self, seller_data: Dict) -> Dict:
        """Calculate Jorge's seller temperature classification"""
        questions_answered = seller_data.get("questions_answered", 0)
        response_quality = seller_data.get("response_quality", 0.0)
        timeline_acceptable = seller_data.get("timeline_acceptable")

        # Jorge's Hot seller criteria (strictest)
        if (questions_answered == 4 and
            timeline_acceptable is True and  # Must accept 30-45 day timeline
            response_quality > 0.7):
            temperature = "hot"
            confidence = 0.95

        # Jorge's Warm seller criteria
        elif (questions_answered >= 3 and
              response_quality > 0.5):
            temperature = "warm"
            confidence = 0.75

        # Cold seller (default)
        else:
            temperature = "cold"
            confidence = 0.60

        return {
            "temperature": temperature,
            "confidence": confidence,
            "analytics": {
                "questions_answered": questions_answered,
                "response_quality": response_quality,
                "timeline_acceptable": timeline_acceptable,
                "classification_logic": f"{questions_answered}/4 questions, {response_quality:.2f} quality"
            }
        }

    async def _generate_seller_response(
        self,
        seller_data: Dict,
        temperature: str,
        contact_id: str,
        location_id: str
    ) -> Dict:
        """Generate Jorge's confrontational seller response"""
        questions_answered = seller_data.get("questions_answered", 0)

        # Hot seller - trigger handoff
        if temperature == "hot":
            message = self._create_handoff_message(seller_data)
            response_type = "handoff"

        # Continue qualification
        elif questions_answered < 4:
            next_question = SellerQuestions.get_next_question(seller_data)
            if next_question:
                message = self._apply_confrontational_tone(next_question, seller_data)
                response_type = "qualification"
            else:
                message = "Let me review your information and get back to you."
                response_type = "review"

        # All questions answered but not hot - nurture
        else:
            message = self._create_nurture_message(seller_data, temperature)
            response_type = "nurture"

        # Ensure SMS compliance (160 chars, no emojis, no hyphens)
        message = self._sanitize_for_sms(message)

        return {
            "message": message,
            "response_type": response_type,
            "character_count": len(message)
        }

    async def _create_seller_actions(
        self,
        contact_id: str,
        location_id: str,
        temperature: str,
        seller_data: Dict
    ) -> List[Dict]:
        """Create Jorge's seller-specific GHL actions"""
        actions = []

        # Apply temperature tag
        actions.append({
            "type": "add_tag",
            "tag": f"{temperature.capitalize()}-Seller"
        })

        # Remove previous temperature tags
        temp_tags = ["Hot-Seller", "Warm-Seller", "Cold-Seller"]
        current_tag = f"{temperature.capitalize()}-Seller"
        for tag in temp_tags:
            if tag != current_tag:
                actions.append({
                    "type": "remove_tag",
                    "tag": tag
                })

        # Hot seller actions
        if temperature == "hot":
            # Remove qualification tag
            actions.append({
                "type": "remove_tag",
                "tag": "Needs Qualifying"
            })

            # Trigger agent notification workflow
            actions.append({
                "type": "trigger_workflow",
                "workflow_id": "jorge_hot_seller_workflow",
                "data": seller_data
            })

            # Add qualified tag
            actions.append({
                "type": "add_tag",
                "tag": "Seller-Qualified"
            })

        # Update custom fields with seller data
        if seller_data.get("price_expectation"):
            actions.append({
                "type": "update_custom_field",
                "field": "price_expectation",
                "value": str(seller_data["price_expectation"])
            })

        if seller_data.get("property_condition"):
            actions.append({
                "type": "update_custom_field",
                "field": "property_condition",
                "value": seller_data["property_condition"]
            })

        return actions

    def _create_handoff_message(self, seller_data: Dict) -> str:
        """Create Jorge's hot seller handoff message"""
        return "Based on your answers, you're exactly who we help. Let me get you scheduled with our team to discuss your options. When works better for you, morning or afternoon?"

    def _create_nurture_message(self, seller_data: Dict, temperature: str) -> str:
        """Create nurture message for qualified but not hot sellers"""
        if temperature == "warm":
            return "Thanks for the info. Let me have our team review your situation and get back to you with next steps."
        else:  # cold
            return "I'll keep your info on file. Reach out if your timeline or situation changes."

    def _apply_confrontational_tone(self, question: str, seller_data: Dict) -> str:
        """Apply Jorge's confrontational tone to questions"""
        # Check for evasive previous responses
        response_quality = seller_data.get("response_quality", 1.0)

        if response_quality < 0.3:  # Very evasive
            return "Are you actually serious about selling or just wasting our time?"
        elif response_quality < 0.6:  # Somewhat evasive
            return f"Let me be direct: {question}"
        else:  # Normal flow
            return question

    def _assess_response_quality(self, user_message: str) -> float:
        """Assess quality of user response for confrontational tone adjustment"""
        message = user_message.strip().lower()

        # Very short/evasive responses
        if len(message) < 10:
            return 0.2

        # Vague responses
        vague_indicators = ["maybe", "not sure", "idk", "i don't know", "thinking about it"]
        if any(indicator in message for indicator in vague_indicators):
            return 0.4

        # Decent responses with some specifics
        if len(message) > 20:
            return 0.7

        # Good quality responses
        return 0.8

    def _sanitize_for_sms(self, message: str) -> str:
        """Ensure message meets Jorge's SMS requirements"""
        import re

        # Remove emojis (Jorge's requirement)
        message = re.sub(r'[^\w\s,.!?]', '', message)

        # Remove hyphens (Jorge's requirement)
        message = message.replace('-', ' ')

        # Ensure under 160 characters (SMS limit)
        if len(message) > 160:
            message = message[:157] + "..."

        return message.strip()

    async def _track_seller_interaction(
        self,
        contact_id: str,
        location_id: str,
        interaction_data: Dict
    ) -> None:
        """Track seller interaction analytics"""
        try:
            # Log interaction for analytics
            self.logger.info(
                f"Seller interaction - Contact: {contact_id}, "
                f"Temperature: {interaction_data['temperature']}, "
                f"Questions: {interaction_data['questions_answered']}/4"
            )

            # Could integrate with existing analytics service here
            # await analytics_service.track_event(...)

        except Exception as e:
            self.logger.error(f"Analytics tracking failed: {e}")


class JorgeSellerResult:
    """Result container for Jorge seller processing"""

    def __init__(
        self,
        message: str,
        temperature: str,
        actions: List[Dict],
        seller_data: Dict,
        analytics: Dict
    ):
        self.message = message
        self.temperature = temperature
        self.actions = actions
        self.seller_data = seller_data
        self.analytics = analytics
        self.questions_answered = seller_data.get("questions_answered", 0)
        self.is_qualified = temperature in ["hot", "warm"]
        self.requires_handoff = temperature == "hot"