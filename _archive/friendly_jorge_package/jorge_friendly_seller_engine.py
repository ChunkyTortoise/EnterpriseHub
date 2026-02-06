"""
Jorge's Friendly Seller Engine - Customer Service Excellence
===========================================================

Main processing engine for Jorge's friendly, consultative approach to seller
qualification. Focuses on relationship building, helpful guidance, and
customer service excellence in the Rancho Cucamonga, California market.

Key Features:
- Warm, consultative conversation management
- Relationship-building qualification process
- Rancho Cucamonga market expertise
- California DRE compliant processes
- Family-friendly, supportive approach
- Customer satisfaction focused

Author: Claude Code Assistant
Created: 2026-01-25 for Friendly CA Approach
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import asyncio
import json
import logging
import time
from datetime import datetime

from jorge_friendly_tone_engine import JorgeFriendlyToneEngine, FriendlyMessageType
from jorge_friendly_config import JorgeFriendlyConfig

logger = logging.getLogger(__name__)


class FriendlySellerQuestionType(Enum):
    """Jorge's 4 friendly qualification question types"""
    MOTIVATION = "motivation"
    TIMELINE = "timeline"
    CONDITION = "condition"
    PRICE_RANGE = "price_range"


class RelationshipTemperature(Enum):
    """Friendly relationship-based temperature classification"""
    READY_TO_MOVE = "ready_to_move"
    INTERESTED = "interested"
    EXPLORING = "exploring"


@dataclass
class FriendlySellerQuestions:
    """Jorge's 4 friendly, consultative qualification questions"""

    # Question 1: Motivation & Future Plans (Consultative)
    MOTIVATION = "I'd love to understand your situation better. What's prompting you to consider selling, and do you have a location in mind for your next home?"

    # Question 2: Timeline Preferences (Flexible, Family-Focused)
    TIMELINE = "To help you plan properly, would selling within the next 2-3 months work with your timeline and family needs?"

    # Question 3: Property Condition (Helpful, Non-Judgmental)
    CONDITION = "Could you help me understand your home's condition? Would you describe it as move-in ready, or are there areas that might need attention?"

    # Question 4: Price Range Discussion (Supportive, Educational)
    PRICE_RANGE = "What price range would feel right for you? I want to make sure we're aligned with realistic market values for your area."

    @classmethod
    def get_question_order(cls) -> List[FriendlySellerQuestionType]:
        """Get Jorge's friendly questions in the correct order"""
        return [
            FriendlySellerQuestionType.MOTIVATION,
            FriendlySellerQuestionType.TIMELINE,
            FriendlySellerQuestionType.CONDITION,
            FriendlySellerQuestionType.PRICE_RANGE
        ]

    @classmethod
    def get_next_question(cls, answered_questions: Dict) -> Optional[str]:
        """Get the next unanswered question in Jorge's friendly sequence"""
        question_mapping = {
            FriendlySellerQuestionType.MOTIVATION: cls.MOTIVATION,
            FriendlySellerQuestionType.TIMELINE: cls.TIMELINE,
            FriendlySellerQuestionType.CONDITION: cls.CONDITION,
            FriendlySellerQuestionType.PRICE_RANGE: cls.PRICE_RANGE
        }

        field_mapping = {
            FriendlySellerQuestionType.MOTIVATION: "motivation",
            FriendlySellerQuestionType.TIMELINE: "timeline_preferences",
            FriendlySellerQuestionType.CONDITION: "property_condition",
            FriendlySellerQuestionType.PRICE_RANGE: "price_range_interest"
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
            "timeline_preferences",
            "property_condition",
            "price_range_interest"
        ]

        for i, field in enumerate(field_mapping, 1):
            if not answered_questions.get(field):
                return i
        return 5  # All questions answered


@dataclass
class FriendlyQualificationResult:
    """Enhanced qualification result for friendly approach"""
    relationship_score: float  # Relationship quality score (1-10)
    engagement_score: float   # Engagement level (1-10)
    temperature: RelationshipTemperature
    consultation_ready: bool
    confidence: float
    next_action: str
    family_considerations: Dict
    support_level: str  # standard, extra_support, guidance
    appreciation_notes: List[str]


@dataclass
class FriendlySellerProfile:
    """Comprehensive friendly seller profile for relationship building"""
    seller_id: str
    property_details: Dict[str, Any]
    family_situation: Dict[str, Any]
    motivation_details: Dict[str, Any]
    timeline_preferences: Dict[str, Any]
    communication_style: str
    support_needs: List[str]
    interaction_history: List[Dict]
    relationship_notes: List[str]


class JorgeFriendlySellerEngine:
    """
    Main engine for Jorge's friendly seller qualification approach.
    Focused on customer service excellence and relationship building.
    """

    def __init__(self, conversation_manager, ghl_client, config: Optional[JorgeFriendlyConfig] = None):
        """Initialize with friendly customer service approach

        Args:
            conversation_manager: ConversationManager instance
            ghl_client: GHL API client
            config: Optional JorgeFriendlyConfig instance for configuration overrides
        """
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.tone_engine = JorgeFriendlyToneEngine()
        self.logger = logging.getLogger(__name__)

        # Store config for friendly settings
        self.config = config or JorgeFriendlyConfig()

        # Initialize Analytics Service for relationship tracking
        from ghl_real_estate_ai.services.analytics_service import AnalyticsService
        self.analytics_service = AnalyticsService()

    async def process_friendly_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main processing method for Jorge's friendly seller approach.

        Args:
            contact_id: GHL contact ID
            user_message: User's message response
            location_id: GHL location ID
            tenant_config: Tenant configuration settings
            images: Optional list of base64 images

        Returns:
            Dict with message, actions, temperature, and relationship data
        """
        try:
            self.logger.info(f"Processing friendly seller response for contact {contact_id}")

            # 1. Get conversation context
            context = await self.conversation_manager.get_context(contact_id, location_id)
            current_seller_data = context.get("seller_preferences", {})
            contact_name = context.get("contact_name", "")

            # 2. Extract seller data with friendly validation
            try:
                extracted_seller_data = await self._extract_seller_data_friendly(
                    user_message=user_message,
                    current_seller_data=current_seller_data,
                    tenant_config=tenant_config or {},
                    images=images
                )
            except Exception as ee:
                self.logger.warning(f"Friendly data extraction failed, using existing context: {ee}")
                extracted_seller_data = current_seller_data

            # 3. Calculate relationship temperature (Friendly approach)
            temperature_result = await self._calculate_friendly_temperature(extracted_seller_data)
            temperature = temperature_result["temperature"]

            # 4. Generate friendly response based on relationship building
            try:
                response_result = await self._generate_friendly_seller_response(
                    seller_data=extracted_seller_data,
                    temperature=temperature,
                    contact_id=contact_id,
                    location_id=location_id,
                    contact_name=contact_name
                )
                final_message = response_result["message"]
            except Exception as re:
                self.logger.error(f"Friendly response generation failed, using supportive fallback: {re}")
                final_message = self._get_supportive_fallback(contact_name, extracted_seller_data)

            # 5. Determine friendly actions based on relationship temperature
            actions = await self._create_friendly_seller_actions(
                contact_id=contact_id,
                location_id=location_id,
                temperature=temperature,
                seller_data=extracted_seller_data
            )

            # 6. Update conversation context with relationship focus
            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=final_message,
                extracted_data=extracted_seller_data,
                location_id=location_id,
                seller_temperature=temperature.value,
                relationship_score=temperature_result.get("relationship_score", 0.0),
                engagement_level=extracted_seller_data.get("engagement_level", 0.0)
            )

            # 7. Log friendly interaction analytics
            await self._track_friendly_interaction(
                contact_id=contact_id,
                location_id=location_id,
                interaction_data={
                    "temperature": temperature.value,
                    "questions_answered": extracted_seller_data.get("questions_answered", 0),
                    "relationship_quality": temperature_result.get("relationship_score", 0.0),
                    "message_length": len(final_message),
                    "support_level": extracted_seller_data.get("support_level", "standard"),
                    "engagement_level": extracted_seller_data.get("engagement_level", 0.0)
                }
            )

            return {
                "message": final_message,
                "actions": actions,
                "temperature": temperature.value,
                "seller_data": extracted_seller_data,
                "questions_answered": extracted_seller_data.get("questions_answered", 0),
                "analytics": {
                    **temperature_result,
                    "approach": "friendly_customer_service",
                    "market_focus": "rancho_cucamonga_ca"
                },
                "relationship_metrics": {
                    "relationship_score": temperature_result.get("relationship_score", 0.0),
                    "engagement_level": extracted_seller_data.get("engagement_level", 0.0),
                    "support_level": extracted_seller_data.get("support_level", "standard")
                }
            }

        except Exception as e:
            self.logger.error(f"Critical error in friendly seller processing: {str(e)}")
            # Friendly fallback
            safe_msg = self._get_supportive_fallback(contact_name, {})
            return {
                "message": safe_msg,
                "actions": [],
                "temperature": "exploring",
                "approach": "friendly_fallback",
                "error": str(e)
            }

    async def _extract_seller_data_friendly(
        self,
        user_message: str,
        current_seller_data: Dict,
        tenant_config: Dict,
        images: Optional[List[str]] = None
    ) -> Dict:
        """Extract and merge seller data using friendly validation approach"""
        try:
            # Use existing conversation manager's extraction capabilities
            extracted_data = await self.conversation_manager.extract_seller_data(
                user_message=user_message,
                current_seller_data=current_seller_data,
                tenant_config=tenant_config,
                images=images
            )

            # --- FRIENDLY ENHANCEMENT: Supportive Quality Assessment ---
            quality_result = await self._assess_response_quality_friendly(user_message)
            extracted_data["response_quality"] = quality_result["quality_score"]
            extracted_data["support_level"] = quality_result["support_level"]
            extracted_data["encouragement_notes"] = quality_result.get("encouragement", [])

            # --- GENTLE SUPPORT TRACKING (vs Aggressive Vague Tracking) ---
            support_needed = current_seller_data.get("support_needed", 0)
            if quality_result["support_level"] in ["extra_support", "guidance"]:
                support_needed += 1
            else:
                support_needed = max(0, support_needed - 1)  # Reduce when good responses
            extracted_data["support_needed"] = support_needed

            # Ensure questions_answered count is accurate
            question_fields = ["motivation", "timeline_preferences", "property_condition", "price_range_interest"]
            questions_answered = sum(1 for field in question_fields if extracted_data.get(field) is not None)

            # --- APPRECIATION TRACKING (Positive Reinforcement) ---
            newly_answered = []
            for field in question_fields:
                if extracted_data.get(field) is not None and current_seller_data.get(field) is None:
                    newly_answered.append(field)

            extracted_data["newly_answered_count"] = len(newly_answered)
            extracted_data["questions_answered"] = questions_answered

            # Store current user message for relationship building
            extracted_data["last_user_message"] = user_message

            # --- FAMILY CONTEXT DETECTION ---
            family_keywords = ["family", "kids", "children", "school", "spouse", "husband", "wife"]
            if any(keyword in user_message.lower() for keyword in family_keywords):
                extracted_data["has_family_context"] = True

            # --- ENGAGEMENT LEVEL CALCULATION ---
            engagement_level = await self._calculate_engagement_level(user_message, extracted_data)
            extracted_data["engagement_level"] = engagement_level

            return extracted_data

        except Exception as e:
            self.logger.error(f"Friendly seller data extraction failed: {e}")
            return current_seller_data

    async def _assess_response_quality_friendly(self, user_message: str) -> Dict:
        """Assess response quality with friendly, supportive approach"""

        message = user_message.strip().lower()

        # Friendly assessment (more supportive than confrontational)
        quality_result = {
            "quality_score": 0.7,  # Start with higher baseline
            "support_level": "standard",
            "encouragement": [],
            "next_steps": []
        }

        # Check for engagement indicators (positive assessment)
        engagement_indicators = [
            "yes", "definitely", "absolutely", "sure", "exactly", "perfect",
            "sounds good", "that works", "i'm interested", "tell me more"
        ]
        if any(indicator in message for indicator in engagement_indicators):
            quality_result["quality_score"] = 0.9
            quality_result["encouragement"].append("Great enthusiasm!")

        # Check for specific information (positive assessment)
        specific_indicators = [
            r'\$\d+', r'\d+k\b', r'\d+\s*months?', r'\d+\s*years?',
            "move-in ready", "needs work", "relocating", "downsizing"
        ]
        import re
        if any(re.search(pattern, message) for pattern in specific_indicators):
            quality_result["quality_score"] = min(1.0, quality_result["quality_score"] + 0.2)
            quality_result["encouragement"].append("Thanks for the specific details!")

        # Check for uncertainty (supportive, not penalizing)
        uncertainty_indicators = ["maybe", "not sure", "thinking about", "unsure", "don't know"]
        if any(indicator in message for indicator in uncertainty_indicators):
            quality_result["quality_score"] = max(0.4, quality_result["quality_score"] - 0.2)
            quality_result["support_level"] = "guidance"
            quality_result["encouragement"].append("No pressure - I'm here to help you think through the options.")

        # Very short responses (supportive follow-up)
        if len(message) < 8:
            quality_result["quality_score"] = 0.5
            quality_result["support_level"] = "extra_support"
            quality_result["encouragement"].append("Would love to hear more when you're ready.")

        return quality_result

    async def _calculate_engagement_level(self, user_message: str, seller_data: Dict) -> float:
        """Calculate user engagement level for relationship building"""

        engagement_score = 0.5  # Baseline

        # Message length factor (reasonable length shows engagement)
        message_length = len(user_message.strip())
        if 20 <= message_length <= 100:
            engagement_score += 0.2
        elif message_length > 100:
            engagement_score += 0.3

        # Question answering progress
        questions_answered = seller_data.get("questions_answered", 0)
        engagement_score += (questions_answered * 0.15)

        # Enthusiasm indicators
        enthusiasm_words = ["excited", "interested", "ready", "looking forward", "definitely", "absolutely"]
        if any(word in user_message.lower() for word in enthusiasm_words):
            engagement_score += 0.2

        # Specific details provided
        if seller_data.get("newly_answered_count", 0) > 0:
            engagement_score += 0.1

        return min(1.0, engagement_score)

    async def _calculate_friendly_temperature(self, seller_data: Dict) -> Dict:
        """Calculate relationship temperature using friendly, inclusive criteria"""

        questions_answered = seller_data.get("questions_answered", 0)
        response_quality = seller_data.get("response_quality", 0.0)
        engagement_level = seller_data.get("engagement_level", 0.0)
        timeline_preferences = seller_data.get("timeline_preferences")

        # Get friendly thresholds (more inclusive)
        ready_questions = self.config.HOT_QUESTIONS_REQUIRED  # 3 instead of 4
        ready_quality = self.config.HOT_QUALITY_THRESHOLD    # 0.6 instead of 0.7
        interested_questions = self.config.WARM_QUESTIONS_REQUIRED  # 2 instead of 3
        interested_quality = self.config.WARM_QUALITY_THRESHOLD     # 0.4 instead of 0.5

        # Calculate relationship score (holistic approach)
        relationship_score = (
            (questions_answered / 4.0) * 0.3 +  # Progress weight
            response_quality * 0.35 +           # Quality weight
            engagement_level * 0.35             # Engagement weight
        ) * 10  # Scale to 1-10

        # Ready to Move criteria (friendly, inclusive)
        if (questions_answered >= ready_questions and
            response_quality >= ready_quality and
            engagement_level >= 0.6):
            temperature = RelationshipTemperature.READY_TO_MOVE
            confidence = 0.85

        # Interested criteria (very inclusive)
        elif (questions_answered >= interested_questions and
              response_quality >= interested_quality):
            temperature = RelationshipTemperature.INTERESTED
            confidence = 0.70

        # Exploring (everyone gets good service)
        else:
            temperature = RelationshipTemperature.EXPLORING
            confidence = 0.60

        return {
            "temperature": temperature,
            "confidence": confidence,
            "relationship_score": relationship_score,
            "analytics": {
                "questions_answered": questions_answered,
                "response_quality": response_quality,
                "engagement_level": engagement_level,
                "classification_logic": f"{questions_answered}/{ready_questions} questions, {response_quality:.2f} quality, {engagement_level:.2f} engagement",
                "friendly_thresholds": {
                    "ready_questions": ready_questions,
                    "ready_quality": ready_quality,
                    "interested_questions": interested_questions,
                    "interested_quality": interested_quality
                }
            }
        }

    async def _generate_friendly_seller_response(
        self,
        seller_data: Dict,
        temperature: RelationshipTemperature,
        contact_id: str,
        location_id: str,
        contact_name: str = ""
    ) -> Dict:
        """Generate friendly, consultative seller response"""

        questions_answered = seller_data.get("questions_answered", 0)
        current_question_number = FriendlySellerQuestions.get_question_number(seller_data)
        support_needed = seller_data.get("support_needed", 0)
        newly_answered_count = seller_data.get("newly_answered_count", 0)
        user_message = seller_data.get("last_user_message", "")
        has_family_context = seller_data.get("has_family_context", False)

        # 1. Ready to Move Consultation Handoff
        if temperature == RelationshipTemperature.READY_TO_MOVE:
            message = self.tone_engine.generate_ready_to_move_handoff(
                seller_name=contact_name,
                agent_name="our local Rancho Cucamonga team"
            )
            response_type = "consultation_ready"

        # 2. Appreciation for Multiple Answers (Positive Reinforcement)
        elif newly_answered_count >= 2:
            appreciation = self.tone_engine.generate_appreciation_message("detailed_response")
            next_q = self.tone_engine.generate_consultative_question(
                current_question_number, contact_name, seller_data
            )
            message = f"{appreciation} {next_q}"
            response_type = "appreciation_and_progress"

        # 3. Family-Focused Response (If Family Context Detected)
        elif has_family_context and questions_answered >= 1:
            family_message = self.tone_engine.generate_family_focused_message("community")
            next_q = self.tone_engine.generate_consultative_question(
                current_question_number, contact_name, seller_data
            )
            message = f"{family_message} {next_q}"
            response_type = "family_focused"

        # 4. Supportive Follow-up for Uncertain Responses
        elif support_needed >= 2:
            message = self.tone_engine.generate_supportive_follow_up(
                user_message, current_question_number - 1, contact_name
            )
            response_type = "supportive_guidance"

        # 5. Market Insight Enhancement (Educational Value)
        elif seller_data.get("price_range_interest") and questions_answered >= 2:
            market_insight = self.tone_engine.generate_market_insight("Rancho Cucamonga")
            next_q = self.tone_engine.generate_consultative_question(
                current_question_number, contact_name, seller_data
            ) if current_question_number <= 4 else ""

            if next_q:
                message = f"{market_insight} {next_q}"
            else:
                message = f"{market_insight} I'd love to discuss your specific situation further."
            response_type = "market_insight"

        # 6. Qualification Flow (Friendly Questions)
        elif questions_answered < 4 and current_question_number <= 4:
            # Check for inadequate previous response (supportive handling)
            last_response = seller_data.get("last_user_message", "")
            response_quality = seller_data.get("response_quality", 1.0)

            if response_quality < 0.5 and last_response:
                # Generate supportive follow-up for unclear response
                message = self.tone_engine.generate_supportive_follow_up(
                    last_response, current_question_number - 1, contact_name
                )
                response_type = "supportive_clarification"
            else:
                # Generate next consultative question
                message = self.tone_engine.generate_consultative_question(
                    current_question_number, contact_name, seller_data
                )
                response_type = "consultative_question"

        # 7. Relationship Nurture (Completed Questions but not ready)
        else:
            message = self.tone_engine.generate_relationship_nurture_message(
                seller_data, temperature.value
            )
            response_type = "relationship_nurture"

        # Validate friendly compliance
        compliance_result = self.tone_engine.validate_message_compliance(message)

        return {
            "message": message,
            "response_type": response_type,
            "character_count": len(message),
            "compliance": compliance_result,
            "warmth_score": compliance_result.warmth_score,
            "professional_score": compliance_result.professional_score
        }

    def _get_supportive_fallback(self, contact_name: str, seller_data: Dict) -> str:
        """Generate supportive fallback message for errors"""
        name = contact_name or "there"

        fallback_messages = [
            f"Hi {name}, I appreciate your interest in Rancho Cucamonga real estate. I'm here to help when you're ready to discuss your options.",
            f"Thanks for reaching out, {name}. I'd love to help you explore your real estate goals in the Rancho Cucamonga area.",
            f"Hello {name}, I'm here to assist with your real estate needs. Please let me know how I can help you today."
        ]

        import random
        message = random.choice(fallback_messages)
        return self.tone_engine._ensure_sms_compliance(message)

    async def _create_friendly_seller_actions(
        self,
        contact_id: str,
        location_id: str,
        temperature: RelationshipTemperature,
        seller_data: Dict
    ) -> List[Dict]:
        """Create friendly seller-specific GHL actions"""
        actions = []

        # Apply friendly temperature tag
        temp_tag_mapping = {
            RelationshipTemperature.READY_TO_MOVE: "Ready-to-Move",
            RelationshipTemperature.INTERESTED: "Interested-Seller",
            RelationshipTemperature.EXPLORING: "Exploring-Options"
        }
        actions.append({
            "type": "add_tag",
            "tag": temp_tag_mapping[temperature]
        })

        # Remove other temperature tags
        all_temp_tags = ["Ready-to-Move", "Interested-Seller", "Exploring-Options",
                        "Hot-Seller", "Warm-Seller", "Cold-Seller"]  # Include old tags
        current_tag = temp_tag_mapping[temperature]
        for tag in all_temp_tags:
            if tag != current_tag:
                actions.append({
                    "type": "remove_tag",
                    "tag": tag
                })

        # Ready to Move actions
        if temperature == RelationshipTemperature.READY_TO_MOVE:
            # Remove qualification tag
            actions.append({
                "type": "remove_tag",
                "tag": "Needs Qualifying"
            })

            # Trigger friendly CA workflow
            actions.append({
                "type": "trigger_workflow",
                "workflow_id": self.config.HOT_SELLER_WORKFLOW_ID,
                "data": {**seller_data, "approach": "friendly_customer_service"}
            })

            # Add consultation ready tag
            actions.append({
                "type": "add_tag",
                "tag": "Consultation-Ready"
            })

        # Update custom fields with friendly approach
        if seller_data.get("motivation"):
            field_id = self.config.get_dre_custom_field_id("seller_motivation") or "ca_motivation"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": seller_data["motivation"]
            })

        if seller_data.get("property_condition"):
            field_id = self.config.get_dre_custom_field_id("property_condition") or "ca_condition"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": seller_data["property_condition"]
            })

        if seller_data.get("price_range_interest"):
            field_id = self.config.get_dre_custom_field_id("price_range_interest") or "ca_price_range"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": str(seller_data["price_range_interest"])
            })

        if seller_data.get("timeline_preferences"):
            field_id = self.config.get_dre_custom_field_id("timeline_preferences") or "ca_timeline"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": seller_data["timeline_preferences"]
            })

        # Relationship quality tracking
        if seller_data.get("engagement_level"):
            field_id = self.config.get_dre_custom_field_id("relationship_score") or "ca_relationship"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": f"{seller_data['engagement_level']:.2f}"
            })

        return actions

    async def _track_friendly_interaction(
        self,
        contact_id: str,
        location_id: str,
        interaction_data: Dict
    ) -> None:
        """Track friendly interaction analytics"""
        try:
            # Log friendly interaction for analytics
            self.logger.info(
                f"Friendly seller interaction - Contact: {contact_id}, "
                f"Temperature: {interaction_data['temperature']}, "
                f"Questions: {interaction_data['questions_answered']}/4, "
                f"Relationship Quality: {interaction_data['relationship_quality']:.2f}"
            )

            # Track with analytics service
            await self.analytics_service.track_event(
                event_type="jorge_friendly_seller_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data={
                    **interaction_data,
                    "approach": "friendly_customer_service",
                    "market": "rancho_cucamonga_ca",
                    "methodology": "consultative_relationship_building"
                }
            )

        except Exception as e:
            self.logger.error(f"Friendly analytics tracking failed: {e}")


class JorgeFriendlySellerResult:
    """Result container for Jorge friendly seller processing"""

    def __init__(
        self,
        message: str,
        temperature: RelationshipTemperature,
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
        self.is_engaged = temperature in [RelationshipTemperature.READY_TO_MOVE, RelationshipTemperature.INTERESTED]
        self.needs_consultation = temperature == RelationshipTemperature.READY_TO_MOVE
        self.approach = "friendly_customer_service"
        self.market_focus = "rancho_cucamonga_ca"


# Example usage for testing
async def demo_friendly_seller_engine():
    """Demonstration of Jorge's friendly seller engine"""

    print("🤝 Jorge Friendly Seller Engine - Rancho Cucamonga Edition")
    print("=" * 65)

    # Mock dependencies for demo
    class MockConversationManager:
        async def get_context(self, contact_id, location_id):
            return {"seller_preferences": {}, "contact_name": "Maria"}

        async def extract_seller_data(self, **kwargs):
            return {"motivation": "downsizing", "timeline_preferences": "flexible"}

        async def update_context(self, **kwargs):
            pass

    class MockGHLClient:
        async def apply_actions(self, contact_id, actions):
            return True

    # Create friendly engine
    engine = JorgeFriendlySellerEngine(
        MockConversationManager(),
        MockGHLClient(),
        JorgeFriendlyConfig()
    )

    # Demo interaction
    result = await engine.process_friendly_seller_response(
        contact_id="demo_001",
        user_message="We're thinking about downsizing. Our kids have moved out and this house feels too big now.",
        location_id="rc_demo"
    )

    print(f"Response: {result['message']}")
    print(f"Temperature: {result['temperature']}")
    print(f"Relationship Score: {result['analytics']['relationship_score']:.2f}")
    print(f"Questions Answered: {result['questions_answered']}/4")

if __name__ == "__main__":
    asyncio.run(demo_friendly_seller_engine())