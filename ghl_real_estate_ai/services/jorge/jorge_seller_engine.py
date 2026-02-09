"""
Jorge's Seller Bot Engine - Main Processing Logic

This module handles the core seller qualification process with Jorge's 4 specific questions
and confrontational tone requirements. Integrates with existing conversation manager
and provides temperature-based lead classification.

Author: Claude Code Assistant
Created: 2026-01-19
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig
from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

# Lazy import to avoid circular dependency - imported where used

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

    # --- SPECIALIZED PERSONA QUESTIONS (Tactical Behavioral Response) ---

    # Investor Branch
    INVESTOR_CAP_RATE = "What's your target cap rate for this asset, and are you looking to do a 1031 exchange?"
    INVESTOR_LIQUIDITY = "Are you looking for a quick cash exit or are you open to terms if the ROI is right?"

    # Loss Aversion Branch
    LOSS_AVERSION_PLAN_B = (
        "If the market shifts and inventory doubles next month, what's your plan B if the home doesn't sell?"
    )
    LOSS_AVERSION_RATE_RISK = (
        "With rates being volatile, if your buying power drops 10% by waiting, does selling now become a necessity?"
    )

    @classmethod
    def get_question_order(cls) -> List[SellerQuestionType]:
        """Get Jorge's questions in the correct order"""
        return [
            SellerQuestionType.MOTIVATION,
            SellerQuestionType.TIMELINE,
            SellerQuestionType.CONDITION,
            SellerQuestionType.PRICE,
        ]

    @classmethod
    def get_next_question(cls, answered_questions: Dict) -> Optional[str]:
        """Get the next unanswered question in Jorge's sequence"""
        question_mapping = {
            SellerQuestionType.MOTIVATION: cls.MOTIVATION,
            SellerQuestionType.TIMELINE: cls.TIMELINE,
            SellerQuestionType.CONDITION: cls.CONDITION,
            SellerQuestionType.PRICE: cls.PRICE,
        }

        field_mapping = {
            SellerQuestionType.MOTIVATION: "motivation",
            SellerQuestionType.TIMELINE: "timeline_acceptable",
            SellerQuestionType.CONDITION: "property_condition",
            SellerQuestionType.PRICE: "price_expectation",
        }

        for q_type in cls.get_question_order():
            field_name = field_mapping[q_type]
            if not answered_questions.get(field_name):
                return question_mapping[q_type]
        return None

    @classmethod
    def get_question_number(cls, answered_questions: Dict) -> int:
        """Get the current question number (1-4) based on answered questions"""
        field_mapping = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]

        for i, field in enumerate(field_mapping, 1):
            if not answered_questions.get(field):
                return i
        return 5  # All questions answered


class JorgeSellerEngine:
    """
    Main engine for Jorge's seller qualification bot.
    Handles the 4-question sequence with confrontational tone.
    """

    def __init__(self, conversation_manager, ghl_client, config: Optional[JorgeSellerConfig] = None, mls_client=None):
        """Initialize with existing conversation manager and GHL client

        Args:
            conversation_manager: ConversationManager instance
            ghl_client: GHL API client
            config: Optional JorgeSellerConfig instance for configuration overrides
            mls_client: Optional MLSClient for real property data lookups
        """
        self.conversation_manager = conversation_manager
        self.ghl_client = ghl_client
        self.tone_engine = JorgeToneEngine()
        self.mls_client = mls_client
        self.logger = logging.getLogger(__name__)

        # Store config for threshold access
        self.config = config or JorgeSellerConfig()

        # Initialize Analytics Service
        from ghl_real_estate_ai.services.analytics_service import AnalyticsService

        self.analytics_service = AnalyticsService()

        # Governance & Recovery
        from ghl_real_estate_ai.core.governance_engine import GovernanceEngine
        from ghl_real_estate_ai.core.recovery_engine import RecoveryEngine
        from ghl_real_estate_ai.services.dynamic_pricing_optimizer import DynamicPricingOptimizer
        from ghl_real_estate_ai.services.predictive_lead_scorer_v2 import PredictiveLeadScorerV2
        from ghl_real_estate_ai.services.psychographic_segmentation_engine import PsychographicSegmentationEngine
        from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer

        self.governance = GovernanceEngine()
        self.recovery = RecoveryEngine()
        self.predictive_scorer = PredictiveLeadScorerV2()
        self.pricing_optimizer = DynamicPricingOptimizer()
        self.psychographic_engine = PsychographicSegmentationEngine()
        self.psychology_analyzer = get_seller_psychology_analyzer()

    async def process_seller_response(
        self,
        contact_id: str,
        user_message: str,
        location_id: str,
        tenant_config: Optional[Dict] = None,
        images: Optional[List[str]] = None,
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
            contact_name = context.get("contact_name", "there")

            # Phase 7: Track probability jump for Adaptive Escalation
            previous_closing_prob = context.get("closing_probability", 0.0)

            # --- AUTONOMOUS FEEDBACK LOOP: Record Conversion ---
            # If lead is responding to an active A/B test follow-up
            if context.get("active_ab_test") and context.get("last_ai_message_type") == "follow_up":
                try:
                    from ghl_real_estate_ai.services.autonomous_ab_testing import get_autonomous_ab_testing

                    ab_testing = get_autonomous_ab_testing()
                    await ab_testing.record_conversion(
                        test_id=context["active_ab_test"]["test_id"],
                        participant_id=contact_id,
                        conversion_data={"type": "response", "message": user_message},
                    )
                    self.logger.info(f"Recorded A/B test conversion for contact {contact_id}")
                except Exception as ab_conv_e:
                    self.logger.warning(f"Failed to record A/B conversion: {ab_conv_e}")

            # 2. Extract seller data from user message
            try:
                extracted_seller_data = await self._extract_seller_data(
                    user_message=user_message,
                    current_seller_data=current_seller_data,
                    tenant_config=tenant_config or {},
                    images=images,
                )
            except Exception as ee:
                self.logger.warning(f"Seller data extraction failed, using existing context: {ee}")
                extracted_seller_data = current_seller_data

            # 3. Calculate seller temperature (Hot/Warm/Cold)
            temperature_result = await self._calculate_seller_temperature(extracted_seller_data)
            temperature = temperature_result["temperature"]

            # --- SELLER PSYCHOLOGY ANALYSIS (New Enhancement) ---
            psychology_profile = None
            if extracted_seller_data.get("property_address"):
                try:
                    # Attempt to analyze seller psychology based on property and comms
                    # This uses DOM, price drops, and tone to determine negotiation stance
                    from ghl_real_estate_ai.api.schemas.negotiation import ListingHistory

                    # Attempt real listing history lookup via MLS/Attom
                    listing_history = None
                    property_address = extracted_seller_data.get("property_address") or context.get("property_address")
                    if property_address and self.mls_client:
                        try:
                            listing_history = await self.mls_client.get_listing_history(property_address)
                        except Exception as mls_err:
                            self.logger.warning(f"MLS lookup failed for {property_address}: {mls_err}")

                    # Fallback to contact-provided data
                    if not listing_history:
                        listing_history = ListingHistory(
                            days_on_market=context.get("days_since_first_contact", 0),
                            original_list_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
                            current_price=float(extracted_seller_data.get("price_expectation", 0) or 0),
                            price_drops=[],
                        )

                    comm_data = {
                        "avg_response_time_hours": context.get("avg_response_time", 24),
                        "communication_tone": context.get("last_ai_message_type", "professional"),
                    }

                    psychology_profile = await self.psychology_analyzer.analyze_seller_psychology(
                        property_id=contact_id, listing_history=listing_history, communication_data=comm_data
                    )
                    self.logger.info(
                        f"Psychology Profile detected for {contact_id}: {psychology_profile.motivation_type}"
                    )
                except Exception as pe:
                    self.logger.warning(f"Psychology analysis failed: {pe}")

            # 4. Calculate Predictive ML Score & ROI-Based Pricing (Extreme Value Phase)
            predictive_result = await self.predictive_scorer.calculate_predictive_score(context, location=location_id)
            pricing_result = await self.pricing_optimizer.calculate_lead_price(contact_id, location_id, context)

            # 5. Detect Psychographic Persona (Deep Behavioral Profiling)
            persona_data = await self.psychographic_engine.detect_persona(
                messages=context.get("conversation_history", []),
                lead_context={**extracted_seller_data, "contact_id": contact_id},
                tenant_id=location_id,
            )

            # 5b. Swarm Intelligence (Parallel Analysis)
            # Deploy the swarm to analyze the lead while we process other ML models
            # Lazy import to avoid circular dependency
            from ghl_real_estate_ai.agents.lead_intelligence_swarm import lead_intelligence_swarm

            swarm_task = asyncio.create_task(
                lead_intelligence_swarm.analyze_lead_comprehensive(
                    contact_id, {**context, **extracted_seller_data, "persona": persona_data.get("primary_persona")}
                )
            )

            # 5c. Detect Negotiation Drift (Tactical Behavioral Response)
            # We await the swarm result specifically for NegotiationStrategistAgent (COMMUNICATION_OPTIMIZER)
            try:
                swarm_consensus = await swarm_task
                optimizer_insight = next(
                    (i for i in swarm_consensus.agent_insights if i.agent_type.value == "communication_optimizer"), None
                )

                if optimizer_insight:
                    drift_data = optimizer_insight.metadata.get("drift", {})
                    extracted_seller_data["drift_softening"] = drift_data.get("is_softening", False)
                    extracted_seller_data["price_break_probability"] = drift_data.get("price_break_probability", 0.0)
                    self.logger.info(
                        f"🧠 Swarm-Driven Drift Detection: softening={extracted_seller_data['drift_softening']}"
                    )
                else:
                    # Fallback to local tone engine if agent failed
                    drift = self.tone_engine.detect_negotiation_drift(context.get("conversation_history", []))
                    extracted_seller_data["drift_softening"] = drift.is_softening
                    extracted_seller_data["price_break_probability"] = drift.price_break_probability
            except Exception as se:
                self.logger.warning(f"Swarm analysis failed, falling back to local drift: {se}")
                drift = self.tone_engine.detect_negotiation_drift(context.get("conversation_history", []))
                extracted_seller_data["drift_softening"] = drift.is_softening
                extracted_seller_data["price_break_probability"] = drift.price_break_probability

            # --- ADAPTIVE ESCALATION (Phase 7) ---
            new_closing_prob = predictive_result.closing_probability
            if (new_closing_prob - previous_closing_prob) > 0.30:
                self.logger.info(
                    f"🚀 ADAPTIVE ESCALATION for {contact_id}: Prob jumped {previous_closing_prob:.2f} -> {new_closing_prob:.2f}"
                )
                try:
                    from ghl_real_estate_ai.services.vapi_service import VapiService

                    vapi = VapiService()
                    vapi.trigger_outbound_call(
                        contact_phone=extracted_seller_data.get("phone", ""),
                        lead_name=contact_name,
                        property_address=extracted_seller_data.get("property_address", "your property"),
                        extra_variables={
                            "escalation_type": "high_intent_jump",
                            "prob_jump": new_closing_prob - previous_closing_prob,
                            "auto_book": True,
                            "persona": persona_data.get("primary_persona"),
                        },
                    )
                except Exception as ve:
                    self.logger.warning(f"Adaptive escalation failed: {ve}")

            # 6. Generate response based on temperature, progress, ML insights, and persona
            try:
                # Phase 7: Slot-Offer Scheduling for Hot Sellers
                booking_message = ""
                booking_actions = []
                pending_appointment_data = None

                if temperature == "hot" and not context.get("pending_appointment"):
                    from ghl_real_estate_ai.services.calendar_scheduler import AppointmentType, get_smart_scheduler

                    scheduler = get_smart_scheduler(self.ghl_client)

                    available_slots = await scheduler.get_available_slots(
                        appointment_type=AppointmentType.LISTING_APPOINTMENT, days_ahead=7
                    )

                    if available_slots:
                        options = []
                        lines = []
                        for i, slot in enumerate(available_slots[:3], 1):
                            display = slot.format_for_lead()
                            options.append(
                                {
                                    "label": str(i),
                                    "display": display,
                                    "start_time": slot.start_time.isoformat(),
                                    "end_time": slot.end_time.isoformat(),
                                    "appointment_type": slot.appointment_type.value,
                                }
                            )
                            lines.append(f"{i}) {display}")

                        booking_message = "I can get you on Jorge's calendar. Reply with 1, 2, or 3.\n" + "\n".join(
                            lines
                        )

                        pending_appointment_data = {
                            "status": "awaiting_selection",
                            "options": options,
                            "attempts": 0,
                            "expires_at": (datetime.utcnow().isoformat()),
                        }

                if booking_message:
                    final_message = booking_message
                else:
                    response_result = await self._generate_seller_response(
                        seller_data=extracted_seller_data,
                        temperature=temperature,
                        contact_id=contact_id,
                        location_id=location_id,
                        predictive_result=predictive_result,
                        persona_data=persona_data,
                        psychology_profile=psychology_profile,
                    )
                    final_message = response_result["message"]
            except Exception as re:
                self.logger.error(f"Seller response generation failed, triggering RECOVERY: {re}")
                self.recovery.log_failure("seller_llm")
                final_message = self.recovery.get_safe_fallback(
                    contact_name=contact_name,
                    conversation_history=context.get("conversation_history", []),
                    extracted_preferences=extracted_seller_data,
                    is_seller=True,
                )

            # --- GOVERNANCE ENFORCEMENT (AGENT G1) ---
            final_message = self.governance.enforce(final_message)

            # 7. Determine actions based on temperature and pricing ROI
            actions = await self._create_seller_actions(
                contact_id=contact_id,
                location_id=location_id,
                temperature=temperature,
                seller_data=extracted_seller_data,
                pricing_result=pricing_result,
                persona_data=persona_data,
            )

            # 7. Update conversation context
            await self.conversation_manager.update_context(
                contact_id=contact_id,
                user_message=user_message,
                ai_response=final_message,
                extracted_data=extracted_seller_data,
                location_id=location_id,
                seller_temperature=temperature,
                predictive_score=predictive_result.overall_priority_score,
                closing_probability=predictive_result.closing_probability,
                persona=persona_data.get("primary_persona"),
                persona_full=persona_data,
            )

            if pending_appointment_data:
                context = await self.conversation_manager.get_context(contact_id, location_id)
                context["pending_appointment"] = pending_appointment_data
                await self.conversation_manager.memory_service.save_context(
                    contact_id, context, location_id=location_id
                )
                await self._track_seller_interaction(
                    contact_id=contact_id,
                    location_id=location_id,
                    interaction_data={"appointment_slot_offer_sent": True},
                )

            # 8. Log analytics data including ROI insights
            await self._track_seller_interaction(
                contact_id=contact_id,
                location_id=location_id,
                interaction_data={
                    "temperature": temperature,
                    "questions_answered": extracted_seller_data.get("questions_answered", 0),
                    "response_quality": extracted_seller_data.get("response_quality", 0.0),
                    "message_length": len(final_message),
                    "vague_streak": extracted_seller_data.get("vague_streak", 0),
                    "closing_probability": predictive_result.closing_probability,
                    "expected_roi": pricing_result.expected_roi,
                    "final_price": pricing_result.final_price,
                },
            )

            # P0 FIX: Extract handoff signals for cross-bot handoff detection
            from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

            handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            return {
                "message": final_message,
                "actions": actions,
                "temperature": temperature,
                "seller_data": extracted_seller_data,
                "questions_answered": extracted_seller_data.get("questions_answered", 0),
                "handoff_signals": handoff_signals,  # P0 FIX: Add handoff signals to return dict
                "analytics": {
                    **temperature_result["analytics"],
                    "closing_probability": predictive_result.closing_probability,
                    "expected_roi": pricing_result.expected_roi,
                    "priority_level": predictive_result.priority_level.value,
                },
                "pricing": {
                    "final_price": pricing_result.final_price,
                    "tier": pricing_result.tier,
                    "justification": pricing_result.justification,
                },
            }

        except Exception as e:
            self.logger.error(f"Critical error in process_seller_response: {str(e)}")
            # Last resort fallback
            safe_msg = self.recovery.get_safe_fallback("there", [], {}, is_seller=True)
            return {
                "message": safe_msg,
                "actions": [],
                "temperature": "cold",
                "error": str(e),
                "handoff_signals": {},  # P0 FIX: Include empty handoff_signals in error case
            }

    async def handle_vapi_booking(self, contact_id: str, location_id: str, booking_details: Dict[str, Any]) -> bool:
        """
        Phase 7: Escalation Confirmation.
        Handle confirmation from Vapi that an appointment was booked autonomously.
        Updates GHL tags to 'Appointment-Booked-Autonomous'.
        """
        try:
            self.logger.info(f"📅 Received Vapi booking confirmation for contact {contact_id}")

            # 1. Update GHL Tags
            # Apply the specific tag requested: Appointment-Booked-Autonomous
            actions = [
                {"type": "add_tag", "tag": "Appointment-Booked-Autonomous"},
                {"type": "remove_tag", "tag": "Needs Qualifying"},
            ]
            await self.ghl_client.apply_actions(contact_id, actions)

            # 2. Log event in Analytics
            await self.analytics_service.track_event(
                event_type="vapi_appointment_booked",
                location_id=location_id,
                contact_id=contact_id,
                data=booking_details,
            )

            # 3. Add internal note to GHL
            note = f"Autonomous Voice AI (Vapi) successfully booked an appointment. Details: {booking_details.get('summary', 'No summary provided')}"
            try:
                # Assuming ghl_client has a method to create notes, or use a general API call
                # For now, we'll try to use a standard GHL action if supported,
                # otherwise just log it.
                self.logger.info(f"Adding note to GHL for {contact_id}: {note}")
            except Exception as note_e:
                self.logger.warning(f"Failed to add GHL note: {note_e}")

            return True
        except Exception as e:
            self.logger.error(f"❌ Error handling Vapi booking: {e}")
            return False

    async def _extract_seller_data(
        self, user_message: str, current_seller_data: Dict, tenant_config: Dict, images: Optional[List[str]] = None
    ) -> Dict:
        """Extract and merge seller data from user message"""
        try:
            # Use existing conversation manager's extraction capabilities
            extracted_data = await self.conversation_manager.extract_seller_data(
                user_message=user_message,
                current_seller_data=current_seller_data,
                tenant_config=tenant_config,
                images=images,
            )

            # --- LOCAL REGEX ENHANCEMENT (Pillar 1: NLP Optimization) ---
            # Fallback/Validation if ConversationManager missed it
            import re

            msg_lower = user_message.lower()

            # 1. Timeline (30-45 days)
            if extracted_data.get("timeline_acceptable") is None:
                if re.search(r"(Union[yes, yeah]|Union[sure, fine]|Union[ok, works]|doable)", msg_lower):
                    # Check if context implies agreement to timeline
                    # (This assumes the bot just asked Q2)
                    pass  # Hard to be sure without knowing previous question context explicitly here, rely on flow
                if re.search(r"(Union[no, nope]|Union[cant, impossible]|too fast)", msg_lower):
                    extracted_data["timeline_acceptable"] = False
                elif re.search(r"(Union[30, 45]|Union[thirty, forty])", msg_lower) and not re.search(
                    r"(Union[no, not])", msg_lower
                ):
                    extracted_data["timeline_acceptable"] = True

            # 2. Price
            if not extracted_data.get("price_expectation"):
                price_match = re.search(r"\$?(\d{1,3}(?:,\d{3})*(?:k)?)", user_message)
                if price_match:
                    extracted_data["price_expectation"] = price_match.group(1)

            # 3. Condition
            if not extracted_data.get("property_condition"):
                if re.search(r"(move.?in.?Union[ready, perfect]|Union[great, good]|excellent)", msg_lower):
                    extracted_data["property_condition"] = "Move-in Ready"
                elif re.search(r"(needs?.?Union[work, fixer]|Union[repairs, bad]|rough)", msg_lower):
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

            # --- MULTI-QUESTION DETECTION (Enhancement) ---
            # If the user answered multiple questions in one go, we should acknowledge it
            newly_answered = []
            for field in question_fields:
                if extracted_data.get(field) is not None and current_seller_data.get(field) is None:
                    newly_answered.append(field)

            extracted_data["newly_answered_count"] = len(newly_answered)
            extracted_data["questions_answered"] = questions_answered

            # Store current user message for follow-up handling
            extracted_data["last_user_message"] = user_message

            # --- MARKET CONTEXT INJECTION PREP (Enhancement) ---
            # If they mentioned a location, flag it for market insight injection
            if extracted_data.get("relocation_destination") or extracted_data.get("property_address"):
                extracted_data["requires_market_insight"] = True

            return extracted_data

        except Exception as e:
            self.logger.error(f"Seller data extraction failed: {e}")
            return current_seller_data

    async def _calculate_seller_temperature(self, seller_data: Dict) -> Dict:
        """Calculate Jorge's seller temperature classification

        Uses configurable thresholds from self.config to enable A/B testing
        and tuning without code deployment.
        """
        questions_answered = seller_data.get("questions_answered", 0)
        response_quality = seller_data.get("response_quality", 0.0)
        timeline_acceptable = seller_data.get("timeline_acceptable")

        # Get configurable thresholds
        hot_questions = self.config.HOT_QUESTIONS_REQUIRED
        hot_quality = self.config.HOT_QUALITY_THRESHOLD
        warm_questions = self.config.WARM_QUESTIONS_REQUIRED
        warm_quality = self.config.WARM_QUALITY_THRESHOLD

        # Jorge's Hot seller criteria (strictest)
        if (
            questions_answered >= hot_questions
            and timeline_acceptable is True  # Must accept 30-45 day timeline
            and response_quality >= hot_quality
        ):
            temperature = "hot"
            confidence = 0.95

        # Jorge's Warm seller criteria
        elif questions_answered >= warm_questions and response_quality >= warm_quality:
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
                "classification_logic": f"{questions_answered}/{hot_questions} questions, {response_quality:.2f} quality",
                "thresholds_used": {
                    "hot_questions": hot_questions,
                    "hot_quality": hot_quality,
                    "warm_questions": warm_questions,
                    "warm_quality": warm_quality,
                },
            },
        }

    async def _generate_simple_response(self, seller_data: Dict, temperature: str, contact_id: str) -> Dict:
        """
        Simple mode response: strict 4-question flow only.
        No enterprise features (arbitrage, Voss, psychology, drift, market insights).
        """
        questions_answered = seller_data.get("questions_answered", 0)
        current_question_number = SellerQuestions.get_question_number(seller_data)
        vague_streak = seller_data.get("vague_streak", 0)
        response_quality = seller_data.get("response_quality", 1.0)
        last_response = seller_data.get("last_user_message", "")

        # 1. Hot → handoff message
        if temperature == "hot":
            message = self.tone_engine.generate_hot_seller_handoff(
                seller_name=seller_data.get("contact_name"), agent_name="our team"
            )
            response_type = "handoff"

        # 2. Vague streak >= 2 → take-away close
        elif vague_streak >= 2:
            message = self.tone_engine.generate_take_away_close(
                seller_name=seller_data.get("contact_name"), reason="vague"
            )
            response_type = "take_away_close"

        # 3. Questions < 4 → next question (or confrontational follow-up if vague)
        elif questions_answered < 4 and current_question_number <= 4:
            if response_quality < 0.5 and last_response:
                message = self.tone_engine.generate_follow_up_message(
                    last_response=last_response,
                    question_number=current_question_number - 1,
                    seller_name=seller_data.get("contact_name"),
                )
            else:
                message = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
            response_type = "qualification"

        # 4. All 4 answered but not hot → warm/cold acknowledgment
        else:
            message = self._create_nurture_message(seller_data, temperature)
            response_type = "nurture"

        compliance_result = self.tone_engine.validate_message_compliance(message)

        return {
            "message": message,
            "response_type": response_type,
            "character_count": len(message),
            "compliance": compliance_result,
            "directness_score": compliance_result.get("directness_score", 0.0),
        }

    async def _generate_seller_response(
        self,
        seller_data: Dict,
        temperature: str,
        contact_id: str,
        location_id: str,
        predictive_result: Any = None,
        persona_data: Dict = None,
        psychology_profile: Any = None,
    ) -> Dict:
        """Generate Jorge's confrontational seller response using tone engine with dynamic branching"""
        # SIMPLE MODE GUARD: Skip all enterprise branches
        if self.config.JORGE_SIMPLE_MODE:
            return await self._generate_simple_response(seller_data, temperature, contact_id)

        questions_answered = seller_data.get("questions_answered", 0)
        current_question_number = SellerQuestions.get_question_number(seller_data)
        vague_streak = seller_data.get("vague_streak", 0)
        newly_answered_count = seller_data.get("newly_answered_count", 0)
        user_message = seller_data.get("last_user_message", "")

        # Extract persona details
        persona_data = persona_data or {}
        primary_persona = persona_data.get("primary_persona", "unknown")

        # PROACTIVE INTELLIGENCE: Trigger "Take-Away Close" early if ML predicts low conversion
        low_probability = False
        if predictive_result and predictive_result.closing_probability < 0.2 and questions_answered >= 1:
            low_probability = True

        # DEEP PSYCHOLOGICAL PROFILING: Adapt tone based on persona and psychology
        persona_override = ""
        if persona_data:
            persona_override = self.psychographic_engine.get_system_prompt_override(persona_data)

        # Add psychology-based instructions if profile exists
        if psychology_profile:
            psych_instruction = f"\nSELLER PSYCHOLOGY: Motivation={psychology_profile.motivation_type}, Urgency={psychology_profile.urgency_level}. "
            if psychology_profile.urgency_level in ["high", "critical"]:
                psych_instruction += "Increase pressure on the timeline."
            elif psychology_profile.motivation_type == "financial":
                psych_instruction += "Focus on the net proceeds and bottom line."
            persona_override += psych_instruction

        # 1. Hot Seller Handoff
        if temperature == "hot":
            message = self.tone_engine.generate_hot_seller_handoff(
                seller_name=seller_data.get("contact_name"), agent_name="our team"
            )
            response_type = "handoff"

        # 2. LOSS AVERSION / COST OF WAITING (Tactical Behavioral Response)
        elif primary_persona == "loss_aversion" and questions_answered >= 1:
            # Emphasize the cost of waiting while still moving the qualification forward
            cost_msg = self.tone_engine.generate_cost_of_waiting_message(
                seller_name=seller_data.get("contact_name"),
                market_trend="interest rates" if "rate" in user_message.lower() else "rising inventory",
            )

            # Get next question
            next_q = self.tone_engine.generate_qualification_message(
                question_number=current_question_number,
                seller_name=seller_data.get("contact_name"),
                context=seller_data,
            )

            # Combine them, ensuring SMS compliance
            message = f"{cost_msg} {next_q}"
            response_type = "loss_aversion_qualification"

        # 2b. NEGOTIATION DRIFT / ROI PROFORMA (Tactical Behavioral Response)
        elif seller_data.get("price_break_probability", 0) > 0.7 and questions_answered >= 2:
            try:
                # Price Break Detection: Seller is softening significantly
                # Trigger Voss-powered closure
                voss_result = await self.voss_agent.run_negotiation(
                    lead_id=contact_id,
                    lead_name=seller_data.get("contact_name", "there"),
                    address=seller_data.get("property_address", "your property"),
                    history=context.get("conversation_history", []),
                )
                message = voss_result.get(
                    "generated_response", "Is it a ridiculous idea to suggest we lock in a price today?"
                )

                # Apply Jorge's tone constraints
                message = self.tone_engine._ensure_sms_compliance(message)
                response_type = "price_break_closure"
            except Exception as ve:
                self.logger.warning(f"Voss closure failed: {ve}")
                message = (
                    "It sounds like you're becoming more flexible on the price. Should we finalize the numbers today?"
                )
                response_type = "price_break_fallback"

        elif seller_data.get("drift_softening") and questions_answered >= 2:
            try:
                # Use DynamicPricingOptimizer for live ROI Proforma data
                proforma_data = await self.pricing_optimizer.calculate_lead_price(contact_id, location_id, seller_data)

                ack = f"I'm sensing some flexibility. I've prepared a live ROI analysis for your property based on {proforma_data.expected_roi}% yield targets."
                next_q = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
                message = f"{ack} {next_q}"
                response_type = "softening_drift_proforma"
            except Exception as doc_e:
                self.logger.warning(f"Failed to generate proforma ack: {doc_e}")
                message = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
                response_type = "qualification"

        # 3. ROI DEFENSE: Net Yield Justification (Phase 7)
        elif (
            seller_data.get("property_condition") == "Needs Work"
            and seller_data.get("price_expectation")
            and predictive_result
            and predictive_result.net_yield_estimate is not None
        ):
            try:
                # Clean price expectation
                import re

                price_str = str(seller_data.get("price_expectation"))
                price_val = float(re.sub(r"[^\d.]", "", price_str.replace("k", "000").replace("K", "000")))

                # Phase 7: Financial Precision & Dynamic ROI Thresholds
                # Use actual market comps via NationalMarketIntelligence
                from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

                market_intel = get_national_market_intelligence()

                # Fetch refined valuation & opportunity score
                location_str = seller_data.get("property_address") or location_id
                ai_valuation = await market_intel.get_market_valuation(location_str, price_val)

                # Dynamic Threshold Logic: Higher opportunity = more aggressive (lower threshold)
                # Range: 0.10 (at score 100) to 0.20 (at score 0)
                metrics = await market_intel.get_market_metrics(location_str)
                opportunity_score = metrics.opportunity_score if metrics else 50.0
                dynamic_threshold = 0.20 - (opportunity_score / 100.0) * 0.10

                if predictive_result.net_yield_estimate < dynamic_threshold:
                    message = self.tone_engine.generate_net_yield_justification(
                        price_expectation=price_val,
                        ai_valuation=ai_valuation,
                        net_yield=predictive_result.net_yield_estimate,
                        repair_estimate=float(seller_data.get("repair_estimate", 50000)),  # Default repair if unknown
                        seller_name=seller_data.get("contact_name"),
                        psychology_profile=psychology_profile,
                    )
                    response_type = "roi_justification"
                else:
                    # Proceed to normal qualification if yield is acceptable for this market
                    message = self.tone_engine.generate_qualification_message(
                        question_number=current_question_number,
                        seller_name=seller_data.get("contact_name"),
                        context=seller_data,
                    )
                    response_type = "qualification"
            except Exception as e:
                self.logger.warning(f"Failed to generate Net Yield justification: {e}")
                # Fallback to standard qualification
                message = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
                response_type = "qualification"

        # 3. Low Probability or Vague Answer Escalation (Take-Away Close)
        elif low_probability or vague_streak >= 2:
            # Pillar 1: Vague Answer Escalation / Proactive Intelligence
            reason = "low_probability" if low_probability else "vague"
            message = self.tone_engine.generate_take_away_close(
                seller_name=seller_data.get("contact_name"), reason=reason, psychology_profile=psychology_profile
            )
            response_type = "take_away_close"

        # Phase 7: Arbitrage Execution for Investors
        elif (
            primary_persona == "investor" or "invest" in seller_data.get("motivation", "").lower()
        ) and questions_answered >= 1:
            try:
                from ghl_real_estate_ai.services.market_timing_opportunity_intelligence import (
                    MarketTimingOpportunityEngine,
                )

                opportunity_engine = MarketTimingOpportunityEngine()

                # Fetch opportunities for the market
                market_area = seller_data.get("property_address") or location_id
                dashboard = await opportunity_engine.get_opportunity_dashboard(market_area)

                # Find a PRICING_ARBITRAGE opportunity if available
                arbitrage_opp = next(
                    (o for o in dashboard.get("opportunities", []) if o["type"] == "pricing_arbitrage"), None
                )

                # Use centralized tone engine for elite arbitrage pitch
                ack = self.tone_engine.generate_arbitrage_pitch(
                    seller_name=seller_data.get("contact_name"),
                    yield_spread=arbitrage_opp["score"] if arbitrage_opp else 0.0,
                    market_area="adjacent zones" if arbitrage_opp else "sub markets",
                )

                next_q = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
                # Combine but ensure we don't double up on the name
                if seller_data.get("contact_name") and next_q.startswith(seller_data.get("contact_name")):
                    # Strip name and comma from next_q if ack already has it
                    next_q_clean = next_q.replace(f"{seller_data.get('contact_name')}, ", "", 1)
                    message = f"{ack} {next_q_clean}"
                else:
                    message = f"{ack} {next_q}"
                response_type = "arbitrage_pitch"
            except Exception as e:
                self.logger.warning(f"Failed to pitch arbitrage: {e}")
                message = self.tone_engine.generate_qualification_message(
                    question_number=current_question_number,
                    seller_name=seller_data.get("contact_name"),
                    context=seller_data,
                )
                response_type = "qualification"

        # 3. Market-Aware Insight Injection (Enhancement)
        elif seller_data.get("requires_market_insight") and questions_answered >= 1:
            # Inject a local market "Reality Check" to show elite intelligence
            address = seller_data.get("property_address") or seller_data.get("relocation_destination")
            market_insight = await self._get_market_insight(address)

            # Get next question but prefix with insight
            next_q = self.tone_engine.generate_qualification_message(
                question_number=current_question_number,
                seller_name=seller_data.get("contact_name"),
                context=seller_data,
            )
            message = f"{market_insight} {next_q}"
            response_type = "market_aware_qualification"

        # 4. Multi-Question Detection Acknowledgment (Enhancement)
        elif newly_answered_count >= 2:
            # User was efficient, acknowledge and move to next
            ack = "Got it. You're moving fast, I like that."
            next_q = self.tone_engine.generate_qualification_message(
                question_number=current_question_number,
                seller_name=seller_data.get("contact_name"),
                context=seller_data,
            )
            message = f"{ack} {next_q}"
            response_type = "multi_answer_qualification"

        # 5. Qualification Flow
        elif questions_answered < 4 and current_question_number <= 4:
            # Check for inadequate previous response
            last_response = seller_data.get("last_user_message", "")
            response_quality = seller_data.get("response_quality", 1.0)

            if response_quality < 0.5 and last_response:
                # Generate confrontational follow-up for poor response
                message = self.tone_engine.generate_follow_up_message(
                    last_response=last_response,
                    question_number=current_question_number - 1,  # Follow up on PREVIOUS question
                    seller_name=seller_data.get("contact_name"),
                )
            else:
                # DYNAMIC PERSONA BRANCHING (Tactical Behavioral Response)
                if primary_persona == "investor" and questions_answered >= 2:
                    # Switch to investor-specific high-stakes question
                    message = SellerQuestions.INVESTOR_CAP_RATE
                    if seller_data.get("investor_q1_answered"):
                        message = SellerQuestions.INVESTOR_LIQUIDITY

                    # Apply Jorge's tone & compliance
                    message = self.tone_engine._apply_confrontational_tone(message, seller_data.get("contact_name"))
                    message = self.tone_engine._ensure_sms_compliance(message)
                    response_type = "investor_branch"

                elif primary_persona == "loss_aversion" and questions_answered >= 2:
                    # Switch to loss-aversion-specific high-stakes question
                    message = SellerQuestions.LOSS_AVERSION_PLAN_B
                    if seller_data.get("loss_aversion_q1_answered"):
                        message = SellerQuestions.LOSS_AVERSION_RATE_RISK

                    # Apply Jorge's tone & compliance
                    message = self.tone_engine._apply_confrontational_tone(message, seller_data.get("contact_name"))
                    message = self.tone_engine._ensure_sms_compliance(message)
                    response_type = "loss_aversion_branch"

                else:
                    # Standard Qualification Branch
                    message = self.tone_engine.generate_qualification_message(
                        question_number=current_question_number,
                        seller_name=seller_data.get("contact_name"),
                        context=seller_data,
                    )
                    response_type = "qualification"

        # 6. Nurture (Completed but not hot)
        else:
            message = self._create_nurture_message(seller_data, temperature)
            response_type = "nurture"

        # --- PERSONA ADAPTATION (Extreme Value Phase) ---
        # If we have a persona override, we'll use LLM to subtly adjust the message tone
        # while keeping Jorge's core structure and SMS compliance.
        if persona_override and message:
            try:
                adapted_message = await self._adapt_message_to_persona(message, persona_override)
                if adapted_message:
                    message = adapted_message
            except Exception as ae:
                self.logger.warning(f"Message adaptation failed: {ae}")

        # Validate message compliance using tone engine
        compliance_result = self.tone_engine.validate_message_compliance(message)

        return {
            "message": message,
            "response_type": response_type,
            "character_count": len(message),
            "compliance": compliance_result,
            "directness_score": compliance_result.get("directness_score", 0.0),
        }

    async def _adapt_message_to_persona(self, message: str, persona_override: str) -> str:
        """Use LLM to subtly adjust message tone to match detected persona."""
        try:
            from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity

            llm_client = LLMClient(provider="claude")

            prompt = f"""Adjust the tone of this SMS message based on the persona guidelines provided.
            
            ORIGINAL SMS: "{message}"
            
            PERSONA GUIDELINES: {persona_override}
            
            CONSTRAINTS:
            1. Keep it under 160 characters.
            2. NO EMOJIS.
            3. NO HYPHENS.
            4. Keep the core question or call to action exactly the same.
            5. Maintain Jorge's direct and professional style.
            
            Return ONLY the adjusted message text."""

            response = await llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are a linguistic adaptation engine. Keep responses SMS compliant (<160 chars, no emojis, no hyphens).",
                temperature=0.3,
                max_tokens=100,
                complexity=TaskComplexity.ROUTINE,
            )

            adapted = response.content.strip()
            # Final SMS compliance check
            adapted = self.tone_engine._ensure_sms_compliance(adapted)
            return adapted
        except Exception as e:
            self.logger.warning(f"Persona adaptation failed for contact {contact_id}: {e}")  # P4 FIX: Add logging
            return message

    async def _get_market_insight(self, location: str) -> str:
        """Fetch real-time market insight using NationalMarketIntelligence service"""
        try:
            from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

            market_intel = get_national_market_intelligence()

            # Fetch real market metrics
            metrics = await market_intel.get_market_metrics(location)
            if metrics:
                # Construct a direct, confrontational insight based on real data
                insight = f"Market data for {location} shows inventory is {metrics.inventory_trend}. "
                if metrics.days_on_market < 30:
                    insight += f"Serious buyers are moving in under {metrics.days_on_market} days. "
                else:
                    insight += "Homes are sitting longer, which means you're losing leverage every day. "
                return insight

            return f"I've been tracking {location}. Buyers are getting picky, so you need to be realistic."
        except Exception as e:
            self.logger.warning(f"Market insight fetch failed: {e}")
            return "Market conditions are shifting fast."

    async def _create_seller_actions(
        self,
        contact_id: str,
        location_id: str,
        temperature: str,
        seller_data: Dict,
        pricing_result: Any = None,
        persona_data: Dict = None,
    ) -> List[Dict]:
        """Create Jorge's seller-specific GHL actions"""
        actions = []

        # Apply temperature tag
        actions.append({"type": "add_tag", "tag": f"{temperature.capitalize()}-Seller"})

        # --- ROI INTELLIGENCE (Extreme Value Phase) ---
        if pricing_result:
            # Update ROI & Lead Value fields using mapped IDs
            roi_field = JorgeSellerConfig.get_ghl_custom_field_id("expected_roi") or "expected_roi"
            tier_field = JorgeSellerConfig.get_ghl_custom_field_id("lead_value_tier") or "lead_value_tier"
            price_field = JorgeSellerConfig.get_ghl_custom_field_id("ai_valuation_price") or "ai_valuation_price"

            actions.append(
                {"type": "update_custom_field", "field": roi_field, "value": f"{pricing_result.expected_roi}%"}
            )
            actions.append({"type": "update_custom_field", "field": tier_field, "value": pricing_result.tier.upper()})
            actions.append(
                {"type": "update_custom_field", "field": price_field, "value": f"${pricing_result.final_price}"}
            )

        # --- PERSONA INTELLIGENCE ---
        if persona_data:
            persona_field = JorgeSellerConfig.get_ghl_custom_field_id("detected_persona") or "detected_persona"
            actions.append(
                {
                    "type": "update_custom_field",
                    "field": persona_field,
                    "value": persona_data.get("primary_persona", "unknown"),
                }
            )

        # Remove previous temperature tags
        temp_tags = ["Hot-Seller", "Warm-Seller", "Cold-Seller"]
        current_tag = f"{temperature.capitalize()}-Seller"
        for tag in temp_tags:
            if tag != current_tag:
                actions.append({"type": "remove_tag", "tag": tag})

        # Hot seller actions
        if temperature == "hot":
            # Remove qualification tag
            actions.append({"type": "remove_tag", "tag": "Needs Qualifying"})

            # Trigger agent notification workflow
            hot_workflow_id = JorgeSellerConfig.get_workflow_id("hot")
            if hot_workflow_id:
                actions.append(
                    {
                        "type": "trigger_workflow",
                        "workflow_id": hot_workflow_id,
                        "data": {**seller_data, "persona": persona_data},
                    }
                )

            # Trigger Vapi Outbound Call (Voice AI Handoff) with exponential backoff retry
            from ghl_real_estate_ai.services.vapi_service import VapiService

            vapi_service = VapiService()
            contact_phone = seller_data.get("phone")

            # Persona-Based Script Mapping (Tactical Behavioral Response)
            script_mapping = {
                "investor": "script_investor_roi_v3",
                "loss_aversion": "script_urgency_market_v2",
                "luxury_seeker": "script_high_end_white_glove",
                "first_time_buyer": "script_educational_guide",
            }
            voice_script_id = script_mapping.get(persona_data.get("primary_persona"), "script_standard_jorge")

            if contact_phone:
                # Retry configuration: 3 attempts with exponential backoff (1s, 2s, 4s)
                max_retries = 3
                retry_delays = [1, 2, 4]  # Exponential backoff delays in seconds
                vapi_success = False

                for attempt in range(max_retries):
                    try:
                        # Deep Persona Handoff: Inject psychographic context into Voice AI
                        vapi_success = vapi_service.trigger_outbound_call(
                            contact_phone=contact_phone,
                            lead_name=seller_data.get("contact_name", "Lead"),
                            property_address=seller_data.get("property_address", "your property"),
                            extra_variables={
                                **seller_data,
                                "persona": persona_data.get("primary_persona"),
                                "voice_script_id": voice_script_id,
                                "drift_softening": drift.is_softening if "drift" in locals() else False,
                                "tone_instruction": self.psychographic_engine.get_system_prompt_override(
                                    persona_data or {}
                                ),
                            },
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
                                await asyncio.sleep(delay)  # P2 FIX: Non-blocking async sleep
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
                            await asyncio.sleep(delay)  # P2 FIX: Non-blocking async sleep
                        else:
                            self.logger.error(
                                f"Vapi Call raised exception after {max_retries} attempts for contact {contact_id}: {e}"
                            )

                if vapi_success:
                    actions.append(
                        {
                            "type": "log_event",
                            "event": "Vapi Outbound Call Triggered",
                            "details": f"Initiated voice handoff for Hot Seller: {contact_id}",
                        }
                    )
                else:
                    self.logger.warning(f"Vapi Call Failed for contact {contact_id}")
                    actions.append(
                        {
                            "type": "log_event",
                            "event": "Vapi Outbound Call Failed",
                            "details": "Voice AI handoff failed after retries. Manual follow-up required.",
                        }
                    )
                    actions.append({"type": "add_tag", "tag": "Voice-Handoff-Failed"})

            # Add qualified tag
            actions.append({"type": "add_tag", "tag": "Seller-Qualified"})

        # Update custom fields with seller data
        # Use centralized config to map to correct GHL Field IDs

        # Price
        if seller_data.get("price_expectation"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("price_expectation") or "price_expectation"
            actions.append(
                {"type": "update_custom_field", "field": field_id, "value": str(seller_data["price_expectation"])}
            )

        # Condition
        if seller_data.get("property_condition"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("property_condition") or "property_condition"
            actions.append(
                {"type": "update_custom_field", "field": field_id, "value": seller_data["property_condition"]}
            )

        # Motivation
        if seller_data.get("motivation"):
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("seller_motivation") or "motivation"
            actions.append({"type": "update_custom_field", "field": field_id, "value": seller_data["motivation"]})

        # Timeline
        if seller_data.get("timeline_acceptable") is not None:
            field_id = JorgeSellerConfig.get_ghl_custom_field_id("timeline_urgency") or "timeline_acceptable"
            val = "30-45 Days Accepted" if seller_data["timeline_acceptable"] else "Timeline Conflict"
            actions.append({"type": "update_custom_field", "field": field_id, "value": val})

        return actions

    def _create_nurture_message(self, seller_data: Dict, temperature: str) -> str:
        """Create nurture message for qualified but not hot sellers"""
        if temperature == "warm":
            base_message = (
                "Thanks for the info. Let me have our team review your situation and get back to you with next steps."
            )
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
                complexity=TaskComplexity.ROUTINE,
            )

            # Parse the JSON response
            import json

            result = json.loads(response.content)
            quality_score = float(result.get("quality_score", 0.5))

            # Clamp to valid range
            quality_score = max(0.0, min(1.0, quality_score))

            self.logger.debug(
                f"Semantic quality assessment: {quality_score:.2f}",
                extra={"message": user_message, "quality": quality_score, "reasoning": result.get("reasoning", "")},
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
            "maybe",
            "not sure",
            "idk",
            "i don't know",
            "thinking about it",
            "unsure",
            "dunno",
            "who knows",
            "we'll see",
            "depends",
            "i guess",
            "kind of",
            "sort of",
            "i'm not really",
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
            r"\byes\b",
            r"\bno\b",
            r"\bnope\b",
            r"\byeah\b",
            r"\bsure\b",
            r"\$\d+",
            r"\d+k\b",
            r"\d+\s*days?\b",
            r"\d+\s*weeks?\b",
            r"\d+\s*months?\b",
        ]
        if any(re.search(pattern, message) for pattern in definitive_indicators):
            return 0.85

        # Very short without definitive content
        if len(message) < 10:
            return 0.4

        # Specific condition/property indicators
        specific_indicators = [
            "move-in ready",
            "needs work",
            "fixer",
            "renovated",
            "updated",
            "relocating",
            "downsizing",
            "divorce",
            "inherited",
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

    async def _track_seller_interaction(self, contact_id: str, location_id: str, interaction_data: Dict) -> None:
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
                data=interaction_data,
            )

        except Exception as e:
            self.logger.error(f"Analytics tracking failed: {e}")


class JorgeSellerResult:
    """Result container for Jorge seller processing"""

    def __init__(self, message: str, temperature: str, actions: List[Dict], seller_data: Dict, analytics: Dict):
        self.message = message
        self.temperature = temperature
        self.actions = actions
        self.seller_data = seller_data
        self.analytics = analytics
        self.questions_answered = seller_data.get("questions_answered", 0)
        self.is_qualified = temperature in ["hot", "warm"]
        self.requires_handoff = temperature == "hot"
