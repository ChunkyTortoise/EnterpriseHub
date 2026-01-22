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
import time
from datetime import datetime

from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine, MessageType
from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

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
        self.tone_engine = JorgeToneEngine()
        self.logger = logging.getLogger(__name__)
        
        # Initialize Analytics Service
        from ghl_real_estate_ai.services.analytics_service import AnalyticsService
        self.analytics_service = AnalyticsService()

    async def process_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None,
        images: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Main processing method for Jorge's seller bot.

        Args:
            contact_id: GHL contact ID
            user_message: User's message response
            location_id: GHL location ID
            tenant_config: Tenant configuration settings
            images: Optional list of base64 images

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
                tenant_config=tenant_config or {},
                images=images
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
                    "message_length": len(response_result["message"]),
                    "vague_streak": extracted_seller_data.get("vague_streak", 0),
                    "response_type": response_result.get("response_type", "unknown")
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
        tenant_config: Dict,
        images: Optional[List[str]] = None
    ) -> Dict:
        """Extract and merge seller data from user message"""
        try:
            # Use existing conversation manager's extraction capabilities
            extracted_data = await self.conversation_manager.extract_seller_data(
                user_message=user_message,
                current_seller_data=current_seller_data,
                tenant_config=tenant_config,
                images=images
            )

            # --- LOCAL REGEX ENHANCEMENT (Pillar 1: NLP Optimization) ---
            # Fallback/Validation if ConversationManager missed it
            import re
            msg_lower = user_message.lower()

            # 1. Timeline (30-45 days)
            if extracted_data.get("timeline_acceptable") is None:
                if re.search(r'(yes|yeah|sure|fine|ok|works|doable)', msg_lower):
                    # Check if context implies agreement to timeline
                    # (This assumes the bot just asked Q2)
                    pass  # Hard to be sure without knowing previous question context explicitly here, rely on flow
                if re.search(r'(no|nope|cant|impossible|too fast)', msg_lower):
                    extracted_data["timeline_acceptable"] = False
                elif re.search(r'(30|45|thirty|forty)', msg_lower) and not re.search(r'(no|not)', msg_lower):
                    extracted_data["timeline_acceptable"] = True

            # 2. Price
            if not extracted_data.get("price_expectation"):
                price_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*(?:k)?)', user_message)
                if price_match:
                    extracted_data["price_expectation"] = price_match.group(1)

            # 3. Condition
            if not extracted_data.get("property_condition"):
                if re.search(r'(move.?in.?ready|perfect|great|good|excellent)', msg_lower):
                    extracted_data["property_condition"] = "Move-in Ready"
                elif re.search(r'(needs?.?work|fixer|repairs|bad|rough)', msg_lower):
                    extracted_data["property_condition"] = "Needs Work"

            # --- VAGUE ANSWER TRACKING (Pillar 1: NLP Optimization) ---

            # Calculate response quality using semantic analysis
            quality = await self._assess_response_quality_semantic(user_message)
            extracted_data["response_quality"] = quality

            # Update Vague Streak
            vague_streak = current_seller_data.get("vague_streak", 0)
            if quality < 0.5:
                vague_streak += 1
            else:
                vague_streak = 0
            extracted_data["vague_streak"] = vague_streak

            # Ensure questions_answered count is accurate
            question_fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
            questions_answered = sum(1 for field in question_fields if extracted_data.get(field) is not None)
            extracted_data["questions_answered"] = questions_answered
            
            # Store current user message for follow-up handling
            extracted_data["last_user_message"] = user_message

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
            response_quality >= 0.7):
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
        """Generate Jorge's confrontational seller response using tone engine"""
        questions_answered = seller_data.get("questions_answered", 0)
        current_question_number = SellerQuestions.get_question_number(seller_data)
        vague_streak = seller_data.get("vague_streak", 0)

        # 1. Hot Seller Handoff
        if temperature == "hot":
            message = self.tone_engine.generate_hot_seller_handoff(
                seller_name=seller_data.get("contact_name"),
                agent_name="our team"
            )
            response_type = "handoff"

        # 2. Vague Answer Escalation (Take-Away Close)
        elif vague_streak >= 2:
            # Pillar 1: Vague Answer Escalation
            message = "It sounds like you aren't ready to sell right now. Should we close your file?"
            response_type = "take_away_close"

        # 3. Qualification Flow
        elif questions_answered < 4 and current_question_number <= 4:
            # Check for inadequate previous response
            last_response = seller_data.get("last_user_message", "")
            response_quality = seller_data.get("response_quality", 1.0)

            if response_quality < 0.5 and last_response:
                # Generate confrontational follow-up for poor response
                message = self.tone_engine.generate_follow_up_message(
                    last_response=last_response,
                    question_number=current_question_number - 1, # Follow up on PREVIOUS question
                    seller_name=seller_data.get("contact_name")
                )
            else:
                # Generate next qualification question
                message = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data
                )
            response_type = "qualification"

        # 4. Nurture (Completed but not hot)
        else:
            message = self._create_nurture_message(seller_data, temperature)
            response_type = "nurture"

        # Validate message compliance using tone engine
        compliance_result = self.tone_engine.validate_message_compliance(message)

        return {
            "message": message,
            "response_type": response_type,
            "character_count": len(message),
            "compliance": compliance_result,
            "directness_score": compliance_result.get("directness_score", 0.0)
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

            # Trigger Vapi Outbound Call (Voice AI Handoff) with exponential backoff retry
            from ghl_real_estate_ai.services.vapi_service import VapiService
            vapi_service = VapiService()
            contact_phone = seller_data.get("phone")
            if contact_phone:
                # Retry configuration: 3 attempts with exponential backoff (1s, 2s, 4s)
                max_retries = 3
                retry_delays = [1, 2, 4]  # Exponential backoff delays in seconds
                vapi_success = False

                for attempt in range(max_retries):
                    try:
                        vapi_success = vapi_service.trigger_outbound_call(
                            contact_phone=contact_phone,
                            lead_name=seller_data.get("contact_name", "Lead"),
                            property_address=seller_data.get("property_address", "your property"),
                            extra_variables=seller_data  # Pass full seller context to Voice AI
                        )

                        if vapi_success:
                            self.logger.info(f"Vapi Call succeeded on attempt {attempt + 1} for contact {contact_id}")
                            break
                        else:
                            if attempt < max_retries - 1:
                                delay = retry_delays[attempt]
                                self.logger.warning(
                                    f"Vapi Call attempt {attempt + 1} failed for contact {contact_id}. "
                                    f"Retrying in {delay}s..."
                                )
                                time.sleep(delay)
                            else:
                                self.logger.error(
                                    f"Vapi Call failed after {max_retries} attempts for contact {contact_id}"
                                )
                    except Exception as e:
                        if attempt < max_retries - 1:
                            delay = retry_delays[attempt]
                            self.logger.warning(
                                f"Vapi Call attempt {attempt + 1} raised exception for contact {contact_id}: {e}. "
                                f"Retrying in {delay}s..."
                            )
                            time.sleep(delay)
                        else:
                            self.logger.error(
                                f"Vapi Call raised exception after {max_retries} attempts for contact {contact_id}: {e}"
                            )

                if vapi_success:
                    actions.append({
                        "type": "log_event",
                        "event": "Vapi Outbound Call Triggered",
                        "details": f"Initiated voice handoff for Hot Seller: {contact_id}"
                    })
                else:
                    self.logger.warning(f"Vapi Call Failed for contact {contact_id}")
                    actions.append({
                        "type": "log_event",
                        "event": "Vapi Outbound Call Failed",
                        "details": "Voice AI handoff failed after retries. Manual follow-up required."
                    })
                    actions.append({
                        "type": "add_tag",
                        "tag": "Voice-Handoff-Failed"
                    })

            # Add qualified tag
            actions.append({
                "type": "add_tag",
                "tag": "Seller-Qualified"
            })

        # Update custom fields with seller data
        # Use centralized config to map to correct GHL Field IDs
        
        # Price
        if seller_data.get("price_expectation"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("price_expectation") or "price_expectation"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": str(seller_data["price_expectation"])
            })

        # Condition
        if seller_data.get("property_condition"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("property_condition") or "property_condition"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": seller_data["property_condition"]
            })
            
        # Motivation
        if seller_data.get("motivation"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("seller_motivation") or "motivation"
            actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": seller_data["motivation"]
            })

        # Timeline
        if seller_data.get("timeline_acceptable") is not None:
             field_id = JorgeSellerConfig.get_ghl_custom_field_id("timeline_urgency") or "timeline_acceptable"
             val = "30-45 Days Accepted" if seller_data["timeline_acceptable"] else "Timeline Conflict"
             actions.append({
                "type": "update_custom_field",
                "field": field_id,
                "value": val
            })

        return actions

    def _create_nurture_message(self, seller_data: Dict, temperature: str) -> str:
        """Create nurture message for qualified but not hot sellers"""
        if temperature == "warm":
            base_message = "Thanks for the info. Let me have our team review your situation and get back to you with next steps."
        else:  # cold
            base_message = "I'll keep your info on file. Reach out if your timeline or situation changes."
        
        # Use tone engine to ensure SMS compliance
        return self.tone_engine._ensure_sms_compliance(base_message)

    async def _assess_response_quality_semantic(self, user_message: str) -> float:
        """
        Assess quality of user response using semantic analysis via Claude AI.

        This replaces the simplistic length-based assessment with true semantic understanding.
        A good short answer like "yes" or "$450k" should score high, while a long vague
        rambling answer should score low.

        Args:
            user_message: User's message text

        Returns:
            Quality score (0.0-1.0)
        """
        try:
            # Import here to avoid circular dependency
            from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity

            # Use Haiku for cost efficiency (routine task)
            llm_client = LLMClient(provider="claude")

            assessment_prompt = f"""Analyze this seller's response and rate its quality from 0.0 to 1.0.

Response: "{user_message}"

Quality Criteria:
- HIGH (0.8-1.0): Specific, definitive answers like "yes", "no", "$450k", "30 days works", "move-in ready"
- MEDIUM (0.5-0.7): Somewhat informative but lacking specificity or commitment
- LOW (0.0-0.4): Vague, evasive, or non-committal like "maybe", "idk", "not sure", rambling

Consider:
1. Specificity: Does it contain concrete information (numbers, dates, definitive yes/no)?
2. Clarity: Is the intent clear and direct?
3. Commitment: Does it show genuine engagement or hesitation?
4. Relevance: Does it answer a question directly?

IMPORTANT: Length does NOT equal quality. "yes" is excellent. Long rambling is poor.

Return ONLY a JSON object with this exact format:
{{"quality_score": 0.85, "reasoning": "Definitive yes answer shows clear commitment"}}"""

            response = await llm_client.agenerate(
                prompt=assessment_prompt,
                system_prompt="You are a response quality analyzer. Return only valid JSON.",
                temperature=0,
                max_tokens=150,
                complexity=TaskComplexity.ROUTINE
            )

            # Parse the JSON response
            import json
            result = json.loads(response.content)
            quality_score = float(result.get("quality_score", 0.5))

            # Clamp to valid range
            quality_score = max(0.0, min(1.0, quality_score))

            self.logger.debug(
                f"Semantic quality assessment: {quality_score:.2f}",
                extra={
                    "message": user_message,
                    "quality": quality_score,
                    "reasoning": result.get("reasoning", "")
                }
            )

            return quality_score

        except Exception as e:
            self.logger.warning(f"Semantic quality assessment failed, using fallback: {e}")
            # Fallback to improved heuristic (better than original length-based)
            return self._assess_response_quality_heuristic(user_message)

    def _assess_response_quality_heuristic(self, user_message: str) -> float:
        """
        Fallback heuristic-based quality assessment (improved version).
        Used when Claude API is unavailable.
        """
        message = user_message.strip().lower()
        import re

        # Check for multiple vague indicators (rambling)
        vague_count = 0
        vague_indicators = [
            "maybe", "not sure", "idk", "i don't know", "thinking about it",
            "unsure", "dunno", "who knows", "we'll see", "depends",
            "i guess", "kind of", "sort of", "i'm not really"
        ]
        for indicator in vague_indicators:
            if indicator in message:
                vague_count += 1

        # Multiple vague indicators = very low quality (rambling)
        if vague_count >= 2:
            return 0.25

        # Single vague indicator
        if vague_count == 1:
            return 0.3

        # Definitive short answers (yes, no, specific numbers/dates)
        definitive_indicators = [
            r'\byes\b', r'\bno\b', r'\bnope\b', r'\byeah\b', r'\bsure\b',
            r'\$\d+', r'\d+k\b', r'\d+\s*days?\b', r'\d+\s*weeks?\b', r'\d+\s*months?\b'
        ]
        if any(re.search(pattern, message) for pattern in definitive_indicators):
            return 0.85

        # Very short without definitive content
        if len(message) < 10:
            return 0.4

        # Specific condition/property indicators
        specific_indicators = [
            "move-in ready", "needs work", "fixer", "renovated", "updated",
            "relocating", "downsizing", "divorce", "inherited"
        ]
        if any(indicator in message for indicator in specific_indicators):
            return 0.75

        # Medium length with some content
        if 10 <= len(message) <= 50:
            return 0.6

        # Longer responses (potentially informative or rambling - hard to tell)
        return 0.55

    def _assess_response_quality(self, user_message: str) -> float:
        """
        DEPRECATED: Legacy synchronous wrapper for compatibility.
        Use _assess_response_quality_semantic instead.
        """
        # Use heuristic fallback for sync calls
        return self._assess_response_quality_heuristic(user_message)

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

            # Integrate with analytics service
            await self.analytics_service.track_event(
                event_type="jorge_seller_interaction",
                location_id=location_id,
                contact_id=contact_id,
                data=interaction_data
            )

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