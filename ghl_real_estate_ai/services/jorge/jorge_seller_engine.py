"""
Jorge's Seller Bot Engine - Main Processing Logic

This module handles the core seller qualification process with Jorge's 4 specific questions
and consultative tone requirements. Integrates with existing conversation manager
and provides temperature-based lead classification.

Author: Claude Code Assistant
Created: 2026-01-19
"""

import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig
from ghl_real_estate_ai.services.compliance_escalation import ComplianceEscalationService
from ghl_real_estate_ai.services.jorge.jorge_tone_engine import JorgeToneEngine

# Lazy import to avoid circular dependency - imported where used

logger = logging.getLogger(__name__)


class SellerQuestionType(Enum):
    """Expanded seller qualification question types"""

    MOTIVATION = "motivation"
    TIMELINE = "timeline"
    CONDITION = "condition"
    PRICE = "price"
    PROPERTY_ADDRESS = "property_address"
    PROPERTY_TYPE = "property_type"
    MORTGAGE_BALANCE = "mortgage_balance"
    REPAIR_ESTIMATE = "repair_estimate"
    PRIOR_LISTING_HISTORY = "prior_listing_history"
    DECISION_MAKER = "decision_maker_confirmed"
    CONTACT_METHOD = "best_contact_method"
    AVAILABILITY_WINDOWS = "availability_windows"


@dataclass
class SellerQuestions:
    """Expanded seller qualification questions in runtime order."""

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
        """Get seller intake questions in the correct order."""
        return [
            SellerQuestionType.MOTIVATION,
            SellerQuestionType.TIMELINE,
            SellerQuestionType.CONDITION,
            SellerQuestionType.PRICE,
            SellerQuestionType.PROPERTY_ADDRESS,
            SellerQuestionType.PROPERTY_TYPE,
            SellerQuestionType.MORTGAGE_BALANCE,
            SellerQuestionType.REPAIR_ESTIMATE,
            SellerQuestionType.PRIOR_LISTING_HISTORY,
            SellerQuestionType.DECISION_MAKER,
            SellerQuestionType.CONTACT_METHOD,
            SellerQuestionType.AVAILABILITY_WINDOWS,
        ]

    @classmethod
    def get_next_question(cls, answered_questions: Dict) -> Optional[str]:
        """Get the next unanswered question in the expanded sequence."""
        question_number = cls.get_question_number(answered_questions)
        return JorgeSellerConfig.SELLER_QUESTIONS.get(question_number)

    @classmethod
    def get_question_number(cls, answered_questions: Dict) -> int:
        """Get current question number based on expanded seller intake state."""
        field_mapping = [
            ("motivation",),
            ("timeline_acceptable", "timeline_days"),
            ("property_condition",),
            ("asking_price", "price_expectation"),
            ("property_address",),
            ("property_type",),
            ("mortgage_balance",),
            ("repair_estimate",),
            ("prior_listing_history",),
            ("decision_maker_confirmed",),
            ("best_contact_method",),
            ("availability_windows",),
        ]

        for i, aliases in enumerate(field_mapping, 1):
            if not any(
                field in answered_questions and not JorgeSellerConfig._is_empty_value(answered_questions.get(field))
                for field in aliases
            ):
                return i
        return len(field_mapping) + 1


class JorgeSellerEngine:
    """
    Main engine for Jorge's seller qualification bot.
    Handles the 4-question sequence with consultative tone.
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
        self.compliance_escalation = ComplianceEscalationService(ghl_client=self.ghl_client)

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

            # Keep canonical contract fields synced with derived pricing outputs.
            extracted_seller_data["seller_temperature"] = str(temperature).upper()
            extracted_seller_data["seller_motivation"] = extracted_seller_data.get("seller_motivation") or extracted_seller_data.get(
                "motivation"
            )
            if pricing_result:
                extracted_seller_data["ai_valuation_price"] = int(pricing_result.final_price)
                extracted_seller_data["lead_value_tier"] = str(pricing_result.tier).upper()

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
                    await vapi.trigger_outbound_call(
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
            booking_message = ""
            booking_actions: List[Dict[str, Any]] = []
            pending_appointment_data = None
            booking_tracking_data: Dict[str, Any] = {}
            try:
                # Phase 7: Slot-Offer Scheduling for Hot Sellers
                if temperature == "hot" and not context.get("pending_appointment"):
                    from ghl_real_estate_ai.services.calendar_scheduler import get_smart_scheduler

                    scheduler = get_smart_scheduler(self.ghl_client)
                    (
                        booking_message,
                        pending_appointment_data,
                        booking_actions,
                        booking_tracking_data,
                    ) = await self._build_hot_seller_slot_offer(
                        scheduler=scheduler,
                        contact_id=contact_id,
                    )

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

            # Canonical lifecycle fields are updated after each message turn.
            extracted_seller_data["last_bot_interaction"] = datetime.utcnow().isoformat()
            extracted_seller_data["qualification_complete"] = JorgeSellerConfig.has_required_canonical_fields(
                extracted_seller_data
            )

            # 7. Determine actions based on temperature and pricing ROI
            actions = await self._create_seller_actions(
                contact_id=contact_id,
                location_id=location_id,
                temperature=temperature,
                seller_data=extracted_seller_data,
                previous_seller_data=current_seller_data,
                pricing_result=pricing_result,
                persona_data=persona_data,
            )
            if booking_actions:
                actions.extend(booking_actions)

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
            if booking_tracking_data:
                await self._track_seller_interaction(
                    contact_id=contact_id,
                    location_id=location_id,
                    interaction_data=booking_tracking_data,
                )

            # 8. Log analytics data including ROI insights
            await self._track_seller_interaction(
                contact_id=contact_id,
                location_id=location_id,
                interaction_data={
                    "temperature": temperature,
                    "questions_answered": extracted_seller_data.get("questions_answered", 0),
                    "expanded_questions_answered": extracted_seller_data.get("expanded_questions_answered", 0),
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
                "expanded_questions_answered": extracted_seller_data.get("expanded_questions_answered", 0),
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

    async def _build_hot_seller_slot_offer(
        self, scheduler: Any, contact_id: str
    ) -> tuple[str, Optional[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        """Build strict WS-3 hot-seller slot offer or manual fallback."""
        try:
            available_slots = await scheduler.get_hot_seller_consultation_slots(days_ahead=7)

            if len(available_slots) == scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT:
                options = []
                lines = []
                for i, slot in enumerate(available_slots, 1):
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

                pending_appointment_data = {
                    "status": "awaiting_selection",
                    "flow": "hot_seller_consultation_30min",
                    "required_slot_count": scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT,
                    "appointment_type": scheduler.HOT_SELLER_APPOINTMENT_TYPE.value,
                    "options": options,
                    "attempts": 0,
                    "expires_at": datetime.utcnow().isoformat(),
                }
                booking_message = (
                    "I can get you on Jorge's calendar for a quick 30 minute consultation. "
                    "Reply with 1, 2, or 3.\n" + "\n".join(lines)
                )
                return (
                    booking_message,
                    pending_appointment_data,
                    [],
                    {
                        "appointment_slot_offer_sent": True,
                        "appointment_offer_slot_count": scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT,
                        "appointment_offer_type": scheduler.HOT_SELLER_APPOINTMENT_TYPE.value,
                    },
                )

            self.logger.warning(
                "HOT seller slot offer fell back to manual scheduling due to insufficient valid slots",
                extra={
                    "contact_id": contact_id,
                    "required_slots": scheduler.HOT_SELLER_REQUIRED_SLOT_COUNT,
                    "available_slots": len(available_slots),
                },
            )
            fallback_actions = [
                action.model_dump(mode="json") for action in scheduler.build_manual_scheduling_actions(high_priority=True)
            ]
            return (
                scheduler.get_manual_scheduling_message(booking_failed=False),
                None,
                fallback_actions,
                {"appointment_slot_offer_sent": False, "appointment_slot_offer_fallback_reason": "insufficient_slots"},
            )
        except Exception as exc:
            self.logger.error(
                "HOT seller slot offer failed, falling back to manual scheduling",
                extra={"contact_id": contact_id, "error": str(exc), "error_type": type(exc).__name__},
                exc_info=True,
            )
            fallback_actions = [
                action.model_dump(mode="json") for action in scheduler.build_manual_scheduling_actions(high_priority=True)
            ]
            return (
                scheduler.get_manual_scheduling_message(booking_failed=False),
                None,
                fallback_actions,
                {"appointment_slot_offer_sent": False, "appointment_slot_offer_fallback_reason": "offer_generation_error"},
            )

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
            # Fallback/validation when upstream extraction omits key seller contract fields.
            import re

            msg_lower = user_message.lower()

            # 1. Timeline intent.
            if extracted_data.get("timeline_acceptable") is None:
                if re.search(r"\b(no|nope|cant|can't|impossible|too fast)\b", msg_lower):
                    extracted_data["timeline_acceptable"] = False
                elif re.search(r"\b(yes|yeah|sure|fine|ok|works|doable|30|45|thirty|forty)\b", msg_lower) and not re.search(
                    r"\b(no|not)\b", msg_lower
                ):
                    extracted_data["timeline_acceptable"] = True

            # 2. Price / asking price.
            if JorgeSellerConfig._is_empty_value(extracted_data.get("asking_price")) and JorgeSellerConfig._is_empty_value(
                extracted_data.get("price_expectation")
            ):
                price_match = re.search(r"\$?(\d{1,3}(?:,\d{3})*(?:\.\d+)?(?:k)?)", user_message)
                if price_match:
                    extracted_data["asking_price"] = price_match.group(1)
                    extracted_data["price_expectation"] = price_match.group(1)

            # 3. Condition.
            if JorgeSellerConfig._is_empty_value(extracted_data.get("property_condition")):
                if re.search(r"\b(move.?in.?ready|perfect|great|good|excellent)\b", msg_lower):
                    extracted_data["property_condition"] = "move-in ready"
                elif re.search(r"\b(needs?.?work|fixer|repairs?|bad|rough)\b", msg_lower):
                    extracted_data["property_condition"] = "needs work"

            # Normalize to canonical seller contract + apply non-erasing merge policy.
            extracted_data = self._normalize_seller_contract_data(extracted_data, current_seller_data, user_message)

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

            # Keep both legacy and expanded qualification counters.
            question_fields = list(JorgeSellerConfig.CORE_QUESTION_FIELDS)
            questions_answered = 0
            for field in question_fields:
                value = extracted_data.get(field)
                if field == "price_expectation" and JorgeSellerConfig._is_empty_value(value):
                    value = extracted_data.get("asking_price")
                if not JorgeSellerConfig._is_empty_value(value):
                    questions_answered += 1

            expanded_questions_answered = 0
            for field in JorgeSellerConfig.SELLER_INTAKE_FIELD_SEQUENCE:
                value = extracted_data.get(field)
                if field == "asking_price" and JorgeSellerConfig._is_empty_value(value):
                    value = extracted_data.get("price_expectation")
                if not JorgeSellerConfig._is_empty_value(value):
                    expanded_questions_answered += 1

            # --- MULTI-QUESTION DETECTION (Enhancement) ---
            newly_answered = []
            for field in JorgeSellerConfig.SELLER_INTAKE_FIELD_SEQUENCE:
                prev_value = current_seller_data.get(field)
                next_value = extracted_data.get(field)
                if field == "asking_price":
                    prev_value = prev_value or current_seller_data.get("price_expectation")
                    next_value = next_value or extracted_data.get("price_expectation")
                if JorgeSellerConfig._is_empty_value(prev_value) and not JorgeSellerConfig._is_empty_value(next_value):
                    newly_answered.append(field)

            extracted_data["newly_answered_count"] = len(newly_answered)
            extracted_data["questions_answered"] = questions_answered
            extracted_data["expanded_questions_answered"] = expanded_questions_answered
            extracted_data["qualification_complete"] = JorgeSellerConfig.is_intake_complete(extracted_data)

            # Store current user message for follow-up handling
            extracted_data["last_user_message"] = user_message
            extracted_data["last_bot_interaction"] = datetime.utcnow().isoformat()
            extracted_data["field_provenance"] = self._build_field_provenance(
                previous_data=current_seller_data, updated_data=extracted_data
            )

            # --- MARKET CONTEXT INJECTION PREP (Enhancement) ---
            # If they mentioned a location, flag it for market insight injection
            if extracted_data.get("relocation_destination") or extracted_data.get("property_address"):
                extracted_data["requires_market_insight"] = True

            return extracted_data

        except Exception as e:
            self.logger.error(f"Seller data extraction failed: {e}")
            return current_seller_data

    def _normalize_seller_contract_data(
        self, incoming_data: Dict[str, Any], current_data: Dict[str, Any], user_message: str
    ) -> Dict[str, Any]:
        """Normalize seller intake payloads and prevent null-overwrite of known values."""
        import re

        merged = dict(current_data or {})

        for key, value in (incoming_data or {}).items():
            if not JorgeSellerConfig._is_empty_value(value):
                merged[key] = value

        def parse_currency(value: Any) -> Optional[int]:
            if JorgeSellerConfig._is_empty_value(value):
                return None
            if isinstance(value, (int, float)):
                numeric_value = int(value)
                return numeric_value if numeric_value >= 10000 else None
            raw_text = str(value).strip().lower()
            text = raw_text.replace(",", "")
            multiplier = 1000 if text.endswith("k") else 1
            text = text[:-1] if text.endswith("k") else text
            match = re.search(r"(\d+(?:\.\d+)?)", text)
            if not match:
                return None
            parsed_value = int(float(match.group(1)) * multiplier)
            # Guard against timeline-like values (for example "30 days").
            if "$" in raw_text or "k" in raw_text or parsed_value >= 10000:
                return parsed_value
            return None

        def parse_timeline_days(value: Any) -> Optional[int]:
            if JorgeSellerConfig._is_empty_value(value):
                return None
            if isinstance(value, (int, float)):
                return int(value)
            text = str(value).lower()
            day_match = re.search(r"(\d+)\s*day", text)
            if day_match:
                return int(day_match.group(1))
            week_match = re.search(r"(\d+)\s*week", text)
            if week_match:
                return int(week_match.group(1)) * 7
            month_match = re.search(r"(\d+)\s*month", text)
            if month_match:
                return int(month_match.group(1)) * 30
            return None

        if JorgeSellerConfig._is_empty_value(merged.get("seller_motivation")) and not JorgeSellerConfig._is_empty_value(
            merged.get("motivation")
        ):
            merged["seller_motivation"] = merged.get("motivation")
        elif JorgeSellerConfig._is_empty_value(merged.get("motivation")) and not JorgeSellerConfig._is_empty_value(
            merged.get("seller_motivation")
        ):
            merged["motivation"] = merged.get("seller_motivation")

        asking_price = parse_currency(merged.get("asking_price"))
        if asking_price is None:
            asking_price = parse_currency(merged.get("price_expectation"))
        if asking_price is None:
            asking_price = parse_currency(user_message)
        if asking_price is not None:
            merged["asking_price"] = asking_price
            merged["price_expectation"] = asking_price

        timeline_days = parse_timeline_days(merged.get("timeline_days"))
        if timeline_days is None:
            timeline_days = parse_timeline_days(merged.get("timeline_urgency"))
        if timeline_days is None:
            timeline_days = parse_timeline_days(user_message)
        if timeline_days is None:
            if merged.get("timeline_acceptable") is True:
                timeline_days = 30
            elif merged.get("timeline_acceptable") is False:
                timeline_days = 90
        if timeline_days is not None:
            merged["timeline_days"] = timeline_days
            merged["timeline_urgency"] = "urgent" if timeline_days <= 45 else "flexible" if timeline_days <= 90 else "long-term"

        condition = merged.get("property_condition")
        if isinstance(condition, str):
            condition_lower = condition.strip().lower()
            if "move" in condition_lower and "ready" in condition_lower:
                merged["property_condition"] = "move-in ready"
            elif any(token in condition_lower for token in ("major", "extensive")):
                merged["property_condition"] = "major repairs"
            elif any(token in condition_lower for token in ("repair", "work", "fixer")):
                merged["property_condition"] = "needs work"

        if JorgeSellerConfig._is_empty_value(merged.get("timeline_acceptable")) and not JorgeSellerConfig._is_empty_value(
            merged.get("timeline_days")
        ):
            merged["timeline_acceptable"] = int(merged["timeline_days"]) <= 45

        return merged

    def _build_field_provenance(self, previous_data: Dict[str, Any], updated_data: Dict[str, Any]) -> Dict[str, str]:
        """Track per-field provenance for extracted/inferred/user-confirmed data writes."""
        existing = previous_data.get("field_provenance", {})
        provenance = dict(existing) if isinstance(existing, dict) else {}

        tracked_fields = set(JorgeSellerConfig.SELLER_INTAKE_FIELD_SEQUENCE + JorgeSellerConfig.CANONICAL_REQUIRED_FIELDS)
        tracked_fields.update({"motivation", "price_expectation", "timeline_acceptable"})

        for field in tracked_fields:
            prev_value = previous_data.get(field)
            new_value = updated_data.get(field)
            if field == "asking_price":
                prev_value = prev_value or previous_data.get("price_expectation")
                new_value = new_value or updated_data.get("price_expectation")
            if JorgeSellerConfig._is_empty_value(new_value):
                continue
            if JorgeSellerConfig._is_empty_value(prev_value):
                provenance[field] = "extracted"
            elif str(prev_value) != str(new_value):
                provenance[field] = "user_confirmed"
            else:
                provenance.setdefault(field, "inferred")

        return provenance

    async def _calculate_seller_temperature(self, seller_data: Dict) -> Dict:
        """Calculate Jorge's seller temperature classification

        Uses configurable thresholds from self.config to enable A/B testing
        and tuning without code deployment.
        """
        questions_answered = seller_data.get("questions_answered", 0)
        response_quality = seller_data.get("response_quality", 0.0)
        timeline_acceptable = seller_data.get("timeline_acceptable")
        timeline_days = seller_data.get("timeline_days")
        motivation_present = not JorgeSellerConfig._is_empty_value(
            seller_data.get("seller_motivation") or seller_data.get("motivation")
        )

        # Get configurable thresholds
        hot_questions = self.config.HOT_QUESTIONS_REQUIRED
        hot_quality = self.config.HOT_QUALITY_THRESHOLD
        warm_questions = self.config.WARM_QUESTIONS_REQUIRED
        warm_quality = self.config.WARM_QUALITY_THRESHOLD

        # Timeline gates are normalized to days where possible.
        hot_timeline = timeline_acceptable is True
        warm_timeline = timeline_acceptable is False
        if isinstance(timeline_days, (int, float)):
            hot_timeline = int(timeline_days) <= 30
            warm_timeline = 30 < int(timeline_days) <= 90

        # Hot seller criteria: strong motivation + urgent timeline + high quality.
        if (
            questions_answered >= hot_questions
            and motivation_present
            and hot_timeline
            and response_quality >= hot_quality
        ):
            temperature = "hot"
            confidence = 0.95

        # Warm seller criteria: partial motivation and medium timeline.
        elif (
            questions_answered >= warm_questions
            and response_quality >= warm_quality
            and (warm_timeline or motivation_present)
        ):
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
                "timeline_days": timeline_days,
                "motivation_present": motivation_present,
                "classification_logic": f"{questions_answered}/{hot_questions} questions, {response_quality:.2f} quality",
                "thresholds_used": {
                    "hot_questions": hot_questions,
                    "hot_quality": hot_quality,
                    "warm_questions": warm_questions,
                    "warm_quality": warm_quality,
                },
            },
        }

    def _generate_next_qualification_prompt(self, question_number: int, seller_data: Dict) -> str:
        """Generate next qualification prompt, supporting >4 expanded intake questions."""
        if question_number <= 4:
            return self.tone_engine.generate_qualification_message(
                question_number=question_number,
                seller_name=seller_data.get("contact_name"),
                context=seller_data,
            )

        question_text = JorgeSellerConfig.SELLER_QUESTIONS.get(question_number)
        if not question_text:
            return self._create_nurture_message(seller_data, "warm")

        message = self.tone_engine._apply_consultative_tone(question_text, seller_data.get("contact_name"))
        return self.tone_engine._ensure_sms_compliance(message)

    async def _generate_simple_response(self, seller_data: Dict, temperature: str, contact_id: str) -> Dict:
        """
        Simple mode response: strict 4-question flow only.
        No enterprise features (arbitrage, Voss, psychology, drift, market insights).
        """
        questions_answered = seller_data.get("questions_answered", 0)
        expanded_questions_answered = seller_data.get("expanded_questions_answered", questions_answered)
        current_question_number = SellerQuestions.get_question_number(seller_data)
        total_questions = len(SellerQuestions.get_question_order())
        vague_streak = seller_data.get("vague_streak", 0)
        response_quality = seller_data.get("response_quality", 1.0)
        last_response = seller_data.get("last_user_message", "")

        # 1. Hot → handoff message
        if temperature == "hot":
            message = self.tone_engine.generate_hot_seller_handoff(
                seller_name=seller_data.get("contact_name"), agent_name="our team"
            )
            response_type = "handoff"

        # 2. Vague streak >= 2 -> gentle pause/clarification
        elif vague_streak >= 2:
            message = self.tone_engine.generate_take_away_close(
                seller_name=seller_data.get("contact_name"), reason="vague"
            )
            response_type = "take_away_close"

        # 3. Continue expanded intake until all required prompts are covered.
        elif expanded_questions_answered < total_questions and current_question_number <= total_questions:
            if response_quality < 0.5 and last_response:
                message = self.tone_engine.generate_follow_up_message(
                    last_response=last_response,
                    question_number=max(1, current_question_number - 1),
                    seller_name=seller_data.get("contact_name"),
                )
            else:
                message = self._generate_next_qualification_prompt(current_question_number, seller_data)
            response_type = "qualification"

        # 4. Intake complete but not hot -> warm/cold acknowledgment
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
        """Generate Jorge's consultative seller response using tone engine with dynamic branching"""
        # SIMPLE MODE GUARD: Skip all enterprise branches
        if self.config.JORGE_SIMPLE_MODE:
            return await self._generate_simple_response(seller_data, temperature, contact_id)

        questions_answered = seller_data.get("questions_answered", 0)
        expanded_questions_answered = seller_data.get("expanded_questions_answered", questions_answered)
        current_question_number = SellerQuestions.get_question_number(seller_data)
        total_questions = len(SellerQuestions.get_question_order())
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
                psych_instruction += "Highlight timeline impact clearly but respectfully."
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
            next_q = self._generate_next_qualification_prompt(current_question_number, seller_data)

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
                next_q = self._generate_next_qualification_prompt(current_question_number, seller_data)
                message = f"{ack} {next_q}"
                response_type = "softening_drift_proforma"
            except Exception as doc_e:
                self.logger.warning(f"Failed to generate proforma ack: {doc_e}")
                message = self._generate_next_qualification_prompt(current_question_number, seller_data)
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

                # Dynamic threshold logic: higher opportunity allows a lower ROI gate.
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
                    message = self._generate_next_qualification_prompt(current_question_number, seller_data)
                    response_type = "qualification"
            except Exception as e:
                self.logger.warning(f"Failed to generate Net Yield justification: {e}")
                # Fallback to standard qualification
                message = self._generate_next_qualification_prompt(current_question_number, seller_data)
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

                next_q = self._generate_next_qualification_prompt(current_question_number, seller_data)
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
                message = self._generate_next_qualification_prompt(current_question_number, seller_data)
                response_type = "qualification"

        # 3. Market-Aware Insight Injection (Enhancement)
        elif seller_data.get("requires_market_insight") and questions_answered >= 1:
            # Inject a local market "Reality Check" to show elite intelligence
            address = seller_data.get("property_address") or seller_data.get("relocation_destination")
            market_insight = await self._get_market_insight(address)

            # Get next question but prefix with insight
            next_q = self._generate_next_qualification_prompt(current_question_number, seller_data)
            message = f"{market_insight} {next_q}"
            response_type = "market_aware_qualification"

        # 4. Multi-Question Detection Acknowledgment (Enhancement)
        elif newly_answered_count >= 2:
            # User was efficient, acknowledge and move to next
            ack = "Got it. You're moving fast, I like that."
            next_q = self._generate_next_qualification_prompt(current_question_number, seller_data)
            message = f"{ack} {next_q}"
            response_type = "multi_answer_qualification"

        # 5. Qualification Flow
        elif expanded_questions_answered < total_questions and current_question_number <= total_questions:
            # Check for inadequate previous response
            last_response = seller_data.get("last_user_message", "")
            response_quality = seller_data.get("response_quality", 1.0)

            if response_quality < 0.5 and last_response:
                # Generate clarification follow-up for poor response
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

                    # Apply Jorge's consultative tone and compliance
                    message = self.tone_engine._apply_consultative_tone(message, seller_data.get("contact_name"))
                    message = self.tone_engine._ensure_sms_compliance(message)
                    response_type = "investor_branch"

                elif primary_persona == "loss_aversion" and questions_answered >= 2:
                    # Switch to loss-aversion-specific high-stakes question
                    message = SellerQuestions.LOSS_AVERSION_PLAN_B
                    if seller_data.get("loss_aversion_q1_answered"):
                        message = SellerQuestions.LOSS_AVERSION_RATE_RISK

                    # Apply Jorge's consultative tone and compliance
                    message = self.tone_engine._apply_consultative_tone(message, seller_data.get("contact_name"))
                    message = self.tone_engine._ensure_sms_compliance(message)
                    response_type = "loss_aversion_branch"

                else:
                    # Standard Qualification Branch
                    message = self._generate_next_qualification_prompt(current_question_number, seller_data)
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
            5. Maintain Jorge's consultative, friendly, and professional style.
            
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
            self.logger.warning(f"Persona adaptation failed: {e}")
            return message

    async def _get_market_insight(self, location: str) -> str:
        """Fetch real-time market insight using NationalMarketIntelligence service"""
        try:
            from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

            market_intel = get_national_market_intelligence()

            # Fetch real market metrics
            metrics = await market_intel.get_market_metrics(location)
            if metrics:
                # Construct a direct but supportive insight based on real data
                insight = f"Market data for {location} shows inventory is {metrics.inventory_trend}. "
                if metrics.days_on_market < 30:
                    insight += f"Serious buyers are moving in under {metrics.days_on_market} days. "
                else:
                    insight += "Homes are sitting longer, which can reduce pricing leverage over time. "
                return insight

            return f"I've been tracking {location}. Buyer demand is shifting, so pricing and timing strategy matter."
        except Exception as e:
            self.logger.warning(f"Market insight fetch failed: {e}")
            return "Market conditions are shifting fast."

    @staticmethod
    def _serialize_custom_field_value(value: Any) -> str:
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (dict, list)):
            return json.dumps(value, separators=(",", ":"))
        return str(value)

    def _append_custom_field_if_changed(
        self,
        *,
        actions: List[Dict[str, Any]],
        field_name: str,
        value: Any,
        previous_seller_data: Dict[str, Any],
    ) -> bool:
        """
        Append a custom-field update only when value changed vs prior persisted seller context.

        Returns:
            True when an update action is appended, else False.
        """
        if JorgeSellerConfig._is_empty_value(value):
            return False

        previous_value = previous_seller_data.get(field_name)
        if field_name == "asking_price" and JorgeSellerConfig._is_empty_value(previous_value):
            previous_value = previous_seller_data.get("price_expectation")
        elif field_name == "price_expectation" and JorgeSellerConfig._is_empty_value(previous_value):
            previous_value = previous_seller_data.get("asking_price")

        serialized_value = self._serialize_custom_field_value(value)
        if not JorgeSellerConfig._is_empty_value(previous_value):
            serialized_previous = self._serialize_custom_field_value(previous_value)
            if serialized_previous == serialized_value:
                return False

        field_id = JorgeSellerConfig.get_ghl_custom_field_id(field_name) or field_name
        actions.append({"type": "update_custom_field", "field": field_id, "value": serialized_value})
        return True

    async def _create_seller_actions(
        self,
        contact_id: str,
        location_id: str,
        temperature: str,
        seller_data: Dict,
        previous_seller_data: Optional[Dict[str, Any]] = None,
        pricing_result: Any = None,
        persona_data: Dict = None,
    ) -> List[Dict]:
        """Create Jorge's seller-specific GHL actions."""
        actions: List[Dict[str, Any]] = []
        persona_data = persona_data or {}
        previous_seller_data = previous_seller_data or {}

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
                        vapi_success = await vapi_service.trigger_outbound_call(
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
                        if attempt < max_retries - 1:
                            delay = retry_delays[attempt]
                            self.logger.warning(
                                f"Vapi Call attempt {attempt + 1} failed for contact {contact_id}. "
                                f"Retrying in {delay}s..."
                            )
                            await asyncio.sleep(delay)  # P2 FIX: Non-blocking async sleep
                        else:
                            self.logger.error(f"Vapi Call failed after {max_retries} attempts for contact {contact_id}")
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

        # Canonical seller field persistence (Epic C)
        required_mapping_fields = JorgeSellerConfig.get_required_qualification_inputs() + ["qualification_complete"]
        mapping_validation = JorgeSellerConfig.validate_custom_field_mapping(required_mapping_fields)
        if not mapping_validation["is_valid"]:
            if JorgeSellerConfig.should_fail_on_missing_canonical_mapping():
                self.logger.error(
                    "Missing canonical GHL field mappings and fail-closed is enabled; suppressing canonical writes",
                    extra={"missing_fields": mapping_validation["missing_fields"]},
                )
                actions.append({"type": "add_tag", "tag": "Canonical-Mapping-Missing"})
                return actions
            self.logger.warning(
                "Missing canonical GHL field mappings for seller contract (fail-open mode)",
                extra={"missing_fields": mapping_validation["missing_fields"]},
            )

        timeline_days = seller_data.get("timeline_days")
        if JorgeSellerConfig._is_empty_value(timeline_days):
            if seller_data.get("timeline_acceptable") is True:
                timeline_days = 30
            elif seller_data.get("timeline_acceptable") is False:
                timeline_days = 90

        canonical_field_values: Dict[str, Any] = {
            "seller_temperature": str(temperature).upper(),
            "seller_motivation": seller_data.get("seller_motivation") or seller_data.get("motivation"),
            "property_condition": seller_data.get("property_condition"),
            "timeline_days": timeline_days,
            "asking_price": seller_data.get("asking_price") or seller_data.get("price_expectation"),
            "ai_valuation_price": seller_data.get("ai_valuation_price"),
            "lead_value_tier": seller_data.get("lead_value_tier"),
            "mortgage_balance": seller_data.get("mortgage_balance"),
            "repair_estimate": seller_data.get("repair_estimate"),
            "decision_maker_confirmed": seller_data.get("decision_maker_confirmed"),
            "best_contact_method": seller_data.get("best_contact_method"),
            "availability_windows": seller_data.get("availability_windows"),
            "prior_listing_history": seller_data.get("prior_listing_history"),
            "last_bot_interaction": seller_data.get("last_bot_interaction"),
            "qualification_complete": seller_data.get("qualification_complete"),
            "field_provenance": seller_data.get("field_provenance"),
            # Legacy fields retained for existing dashboards/integrations.
            "price_expectation": seller_data.get("asking_price") or seller_data.get("price_expectation"),
            "timeline_urgency": seller_data.get("timeline_urgency"),
        }

        changed_canonical_fields: List[str] = []
        for field_name, value in canonical_field_values.items():
            did_update = self._append_custom_field_if_changed(
                actions=actions,
                field_name=field_name,
                value=value,
                previous_seller_data=previous_seller_data,
            )
            if did_update:
                changed_canonical_fields.append(field_name)

        self.logger.info(
            "Canonical seller persistence diff computed",
            extra={
                "contact_id": contact_id,
                "location_id": location_id,
                "changed_fields_count": len(changed_canonical_fields),
                "changed_fields": changed_canonical_fields,
            },
        )

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
            expanded_answered = interaction_data.get("expanded_questions_answered", interaction_data.get("questions_answered", 0))
            self.logger.info(
                f"Seller interaction - Contact: {contact_id}, "
                f"Temperature: {interaction_data['temperature']}, "
                f"Questions: {expanded_answered}/{len(SellerQuestions.get_question_order())}"
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
