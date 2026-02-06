#!/usr/bin/env python3
"""
Standalone Jorge's Seller and Follow-up Engines

Simplified versions of Jorge's seller qualification and follow-up systems
without external dependencies.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass

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

        for q_type in [SellerQuestionType.MOTIVATION, SellerQuestionType.TIMELINE,
                       SellerQuestionType.CONDITION, SellerQuestionType.PRICE]:
            field_name = field_mapping[q_type]
            if not answered_questions.get(field_name):
                return question_mapping[q_type]
        return None


class JorgeToneEngine:
    """Jorge's confrontational tone engine for seller responses"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def generate_qualification_message(
        self,
        question_number: int,
        seller_name: Optional[str] = None,
        context: Dict[str, Any] = None
    ) -> str:
        """Generate Jorge's confrontational qualification message"""

        questions = [
            SellerQuestions.MOTIVATION,
            SellerQuestions.TIMELINE,
            SellerQuestions.CONDITION,
            SellerQuestions.PRICE
        ]

        if question_number <= len(questions):
            question = questions[question_number - 1]
        else:
            question = "Are you ready to move forward with selling?"

        # Add Jorge's confrontational tone
        if seller_name:
            message = f"{seller_name}, {question}"
        else:
            message = question

        return self._ensure_sms_compliance(message)

    def generate_hot_seller_handoff(
        self,
        seller_name: Optional[str] = None,
        agent_name: str = "our team"
    ) -> str:
        """Generate hot seller handoff message"""

        if seller_name:
            message = f"{seller_name}, perfect! You're qualified. {agent_name} will call you within the hour to discuss next steps."
        else:
            message = f"Perfect! You're qualified. {agent_name} will call you within the hour to discuss next steps."

        return self._ensure_sms_compliance(message)

    def generate_take_away_close(
        self,
        seller_name: Optional[str] = None,
        reason: str = "vague",
        psychology_profile: Any = None
    ) -> str:
        """Generate Jorge's take-away close for unresponsive leads"""

        if reason == "low_probability":
            base_message = "I can tell you're not serious about selling right now. I'll remove you from our priority list unless you have specific questions."
        else:
            base_message = "It sounds like you're not ready to make decisions about selling. Should I follow up in a few months instead?"

        if seller_name:
            message = f"{seller_name}, {base_message.lower()}"
        else:
            message = base_message

        return self._ensure_sms_compliance(message)

    def validate_message_compliance(self, message: str) -> Dict[str, Any]:
        """Validate message compliance for SMS"""

        compliance_result = {
            "character_count": len(message),
            "sms_compliant": len(message) <= 160,
            "directness_score": self._calculate_directness(message),
            "has_emojis": any(ord(char) > 127 for char in message),
            "has_hyphens": "-" in message
        }

        return compliance_result

    def _ensure_sms_compliance(self, message: str) -> str:
        """Ensure message meets SMS compliance requirements"""

        # Remove emojis
        message = ''.join(char for char in message if ord(char) <= 127)

        # Remove hyphens (Jorge's preference)
        message = message.replace("-", " ")

        # Trim to 160 characters if needed
        if len(message) > 160:
            message = message[:157] + "..."

        return message.strip()

    def _calculate_directness(self, message: str) -> float:
        """Calculate directness score for Jorge's style"""

        # Jorge prefers direct, confrontational language
        direct_words = ["what", "when", "why", "how", "would", "will", "can", "should"]
        direct_count = sum(1 for word in direct_words if word.lower() in message.lower())

        # Penalty for wishy-washy language
        weak_words = ["maybe", "perhaps", "might", "could", "possibly"]
        weak_count = sum(1 for word in weak_words if word.lower() in message.lower())

        score = (direct_count * 0.2) - (weak_count * 0.3)
        return max(0.0, min(1.0, 0.5 + score))

    def _apply_confrontational_tone(self, message: str, seller_name: Optional[str] = None) -> str:
        """Apply Jorge's confrontational tone to message"""

        # Jorge's style is direct and challenging
        if seller_name and not message.startswith(seller_name):
            message = f"{seller_name}, {message.lower()}"

        return message


class JorgeSellerEngine:
    """
    Simplified version of Jorge's seller qualification engine.

    Handles the 4-question sequence with confrontational tone.
    """

    def __init__(self, conversation_manager, ghl_client, config=None):
        """Initialize seller engine"""
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.tone_engine = JorgeToneEngine()
        self.config = config or {}
        self.logger = logging.getLogger(__name__)

    async def process_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Process seller response with Jorge's 4-question system"""

        try:
            # Get conversation context
            context = await self.conversation_manager.get_context(contact_id, location_id)
            current_seller_data = context.get("seller_preferences", {})

            # Extract seller data from message
            extracted_data = await self._extract_seller_data(user_message, current_seller_data)

            # Calculate seller temperature
            temperature_result = await self._calculate_seller_temperature(extracted_data)
            temperature = temperature_result["temperature"]

            # Generate response
            response_result = await self._generate_seller_response(
                extracted_data, temperature, contact_id, location_id
            )

            # Create actions
            actions = await self._create_seller_actions(
                contact_id, location_id, temperature, extracted_data
            )

            # Update context
            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=response_result["message"],
                extracted_data=extracted_data,
                location_id=location_id,
                seller_temperature=temperature
            )

            return {
                "message": response_result["message"],
                "actions": actions,
                "temperature": temperature,
                "seller_data": extracted_data,
                "questions_answered": extracted_data.get("questions_answered", 0),
                "analytics": temperature_result["analytics"]
            }

        except Exception as e:
            self.logger.error(f"Error processing seller response: {e}")
            return {
                "message": "Thanks for your interest in selling. Our team will get back to you shortly.",
                "actions": [],
                "temperature": "cold",
                "error": str(e)
            }

    async def _extract_seller_data(self, user_message: str, current_data: Dict) -> Dict[str, Any]:
        """Extract seller data from user message using conversation manager"""

        return await self.conversation_manager.extract_seller_data(
            user_message=user_message,
            current_seller_data=current_data,
            tenant_config={},
            images=None
        )

    async def _calculate_seller_temperature(self, seller_data: Dict) -> Dict:
        """Calculate Jorge's seller temperature classification"""

        questions_answered = seller_data.get("questions_answered", 0)
        response_quality = seller_data.get("response_quality", 0.0)
        timeline_acceptable = seller_data.get("timeline_acceptable")

        # Jorge's criteria
        if (questions_answered >= 4 and
            timeline_acceptable is True and
            response_quality >= 0.7):
            temperature = "hot"
            confidence = 0.95
        elif (questions_answered >= 3 and response_quality >= 0.6):
            temperature = "warm"
            confidence = 0.75
        else:
            temperature = "cold"
            confidence = 0.60

        return {
            "temperature": temperature,
            "confidence": confidence,
            "analytics": {
                "questions_answered": questions_answered,
                "response_quality": response_quality,
                "timeline_acceptable": timeline_acceptable
            }
        }

    async def _generate_seller_response(
        self, seller_data: Dict, temperature: str, contact_id: str, location_id: str
    ) -> Dict:
        """Generate Jorge's seller response"""

        questions_answered = seller_data.get("questions_answered", 0)
        seller_name = seller_data.get("contact_name")

        # Hot seller handoff
        if temperature == "hot":
            message = self.tone_engine.generate_hot_seller_handoff(seller_name)
            response_type = "handoff"

        # Continue qualification
        elif questions_answered < 4:
            next_question = SellerQuestions.get_next_question(seller_data)
            if next_question:
                if seller_name:
                    message = f"{seller_name}, {next_question}"
                else:
                    message = next_question
            else:
                message = "Let me review your information and get back to you."

            message = self.tone_engine._ensure_sms_compliance(message)
            response_type = "qualification"

        # Nurture response
        else:
            message = "Thanks for the information. I'll have our team review and get back to you."
            response_type = "nurture"

        compliance = self.tone_engine.validate_message_compliance(message)

        return {
            "message": message,
            "response_type": response_type,
            "compliance": compliance
        }

    async def _create_seller_actions(
        self, contact_id: str, location_id: str, temperature: str, seller_data: Dict
    ) -> List[Dict]:
        """Create GHL actions for seller"""

        actions = []

        # Temperature tag
        actions.append({
            "type": "add_tag",
            "tag": f"{temperature.capitalize()}-Seller"
        })

        # Remove other temperature tags
        other_temps = ["Hot-Seller", "Warm-Seller", "Cold-Seller"]
        current_tag = f"{temperature.capitalize()}-Seller"
        for tag in other_temps:
            if tag != current_tag:
                actions.append({"type": "remove_tag", "tag": tag})

        # Update custom fields
        if seller_data.get("price_expectation"):
            actions.append({
                "type": "update_custom_field",
                "field": "price_expectation",
                "value": str(seller_data["price_expectation"])
            })

        # Hot seller actions
        if temperature == "hot":
            hot_workflow_id = os.getenv("HOT_SELLER_WORKFLOW_ID", "")
            if hot_workflow_id:
                actions.append({
                    "type": "trigger_workflow",
                    "workflow_id": hot_workflow_id
                })

        return actions


class JorgeFollowUpEngine:
    """
    Simplified follow-up engine for Jorge's seller system.
    """

    def __init__(self, conversation_manager=None, ghl_client=None):
        """Initialize follow-up engine"""
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.tone_engine = JorgeToneEngine()
        self.logger = logging.getLogger(__name__)

    async def process_follow_up_trigger(
        self,
        contact_id: str,
        location_id: str,
        trigger_type: str,
        seller_data: Dict[str, Any],
        variant_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process follow-up trigger for seller"""

        try:
            # Determine follow-up message
            message = await self._generate_follow_up_message(
                seller_data, trigger_type, contact_id
            )

            # Create actions
            actions = [
                {"type": "add_tag", "tag": "Follow-up-Sent"},
                {"type": "update_custom_field", "field": "last_followup_date", "value": datetime.now().strftime("%Y-%m-%d")}
            ]

            return {
                "message": message,
                "actions": actions,
                "follow_up_type": trigger_type,
                "success": True
            }

        except Exception as e:
            self.logger.error(f"Follow-up processing failed: {e}")
            return {
                "message": "Thanks for your interest. Our team will be in touch.",
                "actions": [],
                "error": str(e)
            }

    async def _generate_follow_up_message(
        self, seller_data: Dict, trigger_type: str, contact_id: str
    ) -> str:
        """Generate follow-up message based on seller data and trigger type"""

        seller_name = seller_data.get("contact_name")
        temperature = seller_data.get("seller_temperature", "cold")
        questions_answered = seller_data.get("questions_answered", 0)

        # Different messages based on temperature and completion
        if questions_answered < 4:
            # Incomplete qualification
            message = "Still interested in selling? I need a few more details to help you get the best price."
        elif temperature == "warm":
            # Warm follow-up
            message = "Market update: Home values in your area are up 8% this quarter. Ready to discuss selling?"
        else:
            # Cold follow-up
            message = "Quick market check: Are you still considering selling your home?"

        if seller_name:
            message = f"{seller_name}, {message.lower()}"

        return self.tone_engine._ensure_sms_compliance(message)