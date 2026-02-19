"""
Response generation service for Jorge Seller Bot.

Handles generation of Jorge's conversational responses using Claude,
with support for sentiment analysis, persona adaptation, and objection handling.
"""

from typing import Any, Dict, Optional

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import EventPublisher, get_event_publisher
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService
from ghl_real_estate_ai.services.sentiment_analysis_service import SentimentAnalysisService

logger = get_logger(__name__)


class ResponseGenerator:
    """Service for generating Jorge's conversational responses."""

    # Tone instructions for response generation
    TONE_INSTRUCTIONS = {
        "consultative": "Be helpful and supportive. Understand their concerns and provide guidance.",
        "educational": "Share knowledge patiently. Help them understand their options without pressure.",
        "understanding": "Show empathy and patience. Address their concerns with care and expertise.",
        "enthusiastic": "Share their excitement while staying professional. Guide them toward success.",
        "supportive": "Provide comfort and reassurance. Help them feel confident in their decisions.",
    }

    # Persona-specific response guidance
    PERSONA_GUIDANCE = {
        "Investor": """
        INVESTOR SELLER APPROACH:
        - Focus on ROI, cash flow analysis, and tax benefits
        - Discuss 1031 exchange opportunities if timeline fits
        - Emphasize cap rate and market appreciation trends
        - Reference portfolio strategy and investment property performance
        - Be data-driven and business-focused
        """,
        "Distressed": """
        DISTRESSED SELLER APPROACH:
        - Emphasize speed, certainty, and flexible closing
        - Highlight as-is purchase acceptance
        - Show empathy for their situation without being pushy
        - Provide clear timeline expectations and next steps
        - Stress confidentiality and quick resolution
        """,
        "Traditional": """
        TRADITIONAL SELLER APPROACH:
        - Standard home sale process and marketing strategy
        - Focus on maximizing value through proper preparation
        - Emphasize local market expertise and negotiation skills
        - Build trust through education and relationship
        """,
    }

    def __init__(
        self,
        claude: Optional[ClaudeAssistant] = None,
        event_publisher: Optional[EventPublisher] = None,
        sentiment_service: Optional[SentimentAnalysisService] = None,
        ab_testing: Optional[ABTestingService] = None,
        calendar_service: Optional[CalendarBookingService] = None,
    ):
        self.claude = claude or ClaudeAssistant()
        self.event_publisher = event_publisher or get_event_publisher()
        self.sentiment_service = sentiment_service or SentimentAnalysisService()
        self.ab_testing = ab_testing or ABTestingService()
        self.calendar_service = calendar_service

    async def generate_jorge_response(
        self,
        state: JorgeSellerState,
        tone_variant: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate the actual response content using Jorge's specific persona."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="generate_response"
        )

        # Persona-aware stall responses (rotate to avoid repetition)
        import random
        seller_persona = state.get("seller_persona", {})
        persona_type = seller_persona.get("persona_type", "Traditional")
        is_investor = persona_type.lower() in ("investor", "arbitrage")

        friendly_responses = {
            "thinking": random.choice([
                "Totally get it, big decision. What's the main thing on your mind? Happy to pull numbers if that helps.",
                "No pressure at all. What info would help you feel more confident?",
                "Take your time. Is there something specific I can look into for you?",
            ]) if not is_investor else random.choice([
                "Makes sense to weigh the numbers. Want me to run a quick comp analysis so you can see the ROI picture?",
                "Smart to think it through. I can pull recent sale data for your area if that helps the decision.",
            ]),
            "get_back": random.choice([
                "No rush! Has anything changed with your timeline? I can send fresh comps if useful.",
                "Sounds good. When you're ready, I'm here. Anything new on your end?",
                "All good. Want me to keep an eye on the market for you in the meantime?",
            ]),
            "zestimate": random.choice([
                "Zillow can't walk through your house! Want to see what neighbors actually sold for recently?",
                "Online estimates miss a lot. I can show you what similar homes near you actually closed at.",
                "Those online numbers are a starting point. The real picture comes from actual closed sales nearby.",
            ]),
            "agent": random.choice([
                "Great you have someone! Happy to share comps from your area, could be useful for your agent too.",
                "Good to hear. If you ever want a second set of eyes on the numbers, I'm happy to help.",
            ]),
            "price": random.choice([
                "Pricing is tricky. Want me to pull recent sales nearby? Real data beats guessing.",
                "The right price makes all the difference. I can show you what's actually selling in your area.",
                "Happy to dig into the numbers with you. What range are you thinking?",
            ]),
            "timeline": random.choice([
                "Makes sense. What's driving your timeline, a move, the market, or something else?",
                "Got it. Is there a specific date you're working toward?",
                "Timelines are flexible. What would the ideal scenario look like for you?",
            ]),
        }

        # Get tone variant if not provided
        if not tone_variant:
            seller_id = state.get("lead_id", "unknown")
            try:
                tone_variant = await self.ab_testing.get_variant(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    seller_id
                )
            except (KeyError, ValueError):
                tone_variant = "empathetic"

        # Phase 1.5: Analyze sentiment of the user message
        sentiment_context = ""
        try:
            last_user_msg = next(
                (msg.get("content", "") for msg in reversed(state.get("conversation_history", [])) if msg.get("role") == "user"),
                ""
            )
            if last_user_msg:
                sentiment_result = await self.sentiment_service.analyze_message(last_user_msg)
                tone_adjustment = self.sentiment_service.get_response_tone_adjustment(sentiment_result.sentiment)

                sentiment_context = f"""
        SENTIMENT ANALYSIS (Phase 1.5):
        - Detected Sentiment: {sentiment_result.sentiment.value.upper()} (Confidence: {sentiment_result.confidence:.2f})
        - Suggested Tone: {tone_adjustment.get('tone', 'professional')}
        - Pacing: {tone_adjustment.get('pace', 'normal')}
        """
                # Check for escalation
                if sentiment_result.escalation_required.value != "none":
                    logger.warning(f"Sentiment escalation triggered: {sentiment_result.escalation_required.value}")
        except Exception as e:
            logger.warning(f"Sentiment analysis failed in response generation: {e}")

        # Phase 1.2: Get seller persona classification
        seller_persona = state.get("seller_persona", {})
        persona_type = seller_persona.get("persona_type", "Traditional")
        persona_confidence = seller_persona.get("confidence", 0.0)

        # Base prompt for Jorge Persona
        prompt = f"""
        You are Jorge Salas, a caring and knowledgeable real estate professional.
        Your approach is: HELPFUL, CONSULTATIVE, and RELATIONSHIP-FOCUSED.
        You genuinely want to help sellers achieve their goals and make great decisions.

        CORE VALUES:
        - Put the seller's success first
        - Build trust through expertise and care
        - Provide valuable insights and education
        - Be patient and understanding
        - Focus on long-term relationships

        CURRENT CONTEXT:
        Lead: {state["lead_name"]}
        Tone Mode: {state.get("current_tone", "consultative")} ({self.TONE_INSTRUCTIONS.get(state.get("current_tone", "consultative"), "Be helpful and professional")})
        Tone style: {tone_variant}
        Conversation Context: {state.get("detected_stall_type") or "None"}
        FRS Classification: {state["intent_profile"].frs.classification if state.get("intent_profile") else "Unknown"}
        Seller Type: {persona_type} (confidence: {persona_confidence:.0%})

        {self.PERSONA_GUIDANCE.get(persona_type, "")}
        {sentiment_context}

        AGENT STATUS DETECTION: If the seller mentions working with another agent, having a
        listing agreement, or being under contract, acknowledge positively and flag it.
        Example: "Great you have someone! Jorge can still share comps from your area if that's helpful."
        Never disparage another agent or pressure the seller to switch.

        TASK: Generate a helpful, friendly response that builds trust and provides value.
        Tailor your response to the seller's persona type above and detected sentiment.
        """

        # Inject CMA market context if available
        cma_report = state.get("cma_report")
        if cma_report:
            estimated_value = cma_report.get("estimated_value", 0)
            market_trend = state.get("market_trend", "balanced")
            market_data = state.get("market_data", {})
            dom_average = market_data.get("dom_average", 0)
            comp_count = len(state.get("comparable_properties", []))

            prompt += f"""
        MARKET DATA CONTEXT (use naturally in response when relevant):
        - Estimated property value: ${estimated_value:,.0f}
        - Average days on market: {dom_average}
        - Market trend: {market_trend.replace('_', ' ')}
        - Comparable properties analyzed: {comp_count}
        """

        # Phase 4: Inject ML pricing guidance if available
        pricing_guidance = state.get("pricing_guidance")
        if pricing_guidance and state.get("pricing_guidance_variant") == "treatment":
            prompt += f"""

        ML-POWERED PRICING INSIGHTS (Phase 4 - weave naturally into conversation):
        {pricing_guidance}

        Use this data-driven pricing analysis to provide specific, actionable recommendations.
        Present it conversationally as part of your expert guidance.
        """

        if state.get("stall_detected") and state.get("detected_stall_type") in friendly_responses:
            prompt += f"\nSUGGESTED HELPFUL RESPONSE: {friendly_responses[state['detected_stall_type']]}"

        # Phase 2.2: Use objection response if available
        if state.get("objection_detected") and state.get("objection_response_text"):
            objection_response = state.get("objection_response_text")
            objection_metadata = state.get("objection_metadata", {})
            prompt += f"\n\nOBJECTION HANDLING RESPONSE (Phase 2.2):"
            prompt += f"\n- Type: {objection_metadata.get('objection_category', 'unknown')}/{objection_metadata.get('objection_type', 'unknown')}"
            prompt += f"\n- Graduation level: {objection_metadata.get('graduation_level', 'validate')}"
            prompt += f"\n- Suggested response: {objection_response}"
            prompt += "\nUSE THIS OBJECTION RESPONSE as your primary reply, personalizing it to Jorge's style."

        # PHASE 3.3 ENHANCEMENT: Apply Bot Intelligence for Enhanced Responses
        if state.get("intelligence_available") and state.get("intelligence_context"):
            prompt = await self._enhance_prompt_with_intelligence(prompt, state["intelligence_context"], state)

        response = await self.claude.analyze_with_context(prompt)
        content = (
            response.get("content")
            or response.get("analysis")
            or state.get("objection_response_text")  # Fallback to objection response
            or random.choice([
                "What questions do you have about the selling process? Happy to walk you through it.",
                "What would be most helpful for me to look into for you right now?",
                "Anything specific about your home or the market you're curious about?",
            ])
        )

        # Calendar-focused mode: append real calendar slots for HOT sellers
        if state.get("adaptive_mode") == "calendar_focused" and self.calendar_service:
            try:
                slot_result = await self.calendar_service.offer_appointment_slots(state["lead_id"])
                content = content.rstrip() + "\n\n" + slot_result["message"]
            except Exception as e:
                logger.warning(f"Calendar slot offering failed for {state['lead_id']}: {e}")

        # Update qualification progress - increment question count
        current_q = state.get("current_question", 1)
        questions_answered = len([h for h in state.get("conversation_history", []) if h.get("role") == "user"])

        intent_profile = state.get("intent_profile")
        frs_score = 0
        if intent_profile:
            if hasattr(intent_profile, "frs"):
                frs_score = intent_profile.frs.total_score
            elif isinstance(intent_profile, dict):
                frs_score = intent_profile.get("frs", {}).get("total_score", 0)

        await self.event_publisher.publish_jorge_qualification_progress(
            contact_id=state["lead_id"],
            current_question=min(current_q + 1, 4),
            questions_answered=min(questions_answered, 4),
            seller_temperature=state.get("seller_temperature", "cold"),
            qualification_scores={"frs_score": frs_score, "pcs_score": state.get("psychological_commitment", 0)},
            next_action="await_response",
        )

        # Emit conversation event for response generated
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state["lead_id"],
            stage="response_generated",
            message=content,
        )

        # Mark bot as active (waiting for response)
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="active",
            current_step="awaiting_response"
        )

        return {"response_content": content}

    async def generate_adaptive_response(
        self,
        state: JorgeSellerState,
        next_question: str,
        tone_variant: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate response using adaptive question selection."""
        await self.event_publisher.publish_bot_status_update(
            bot_type="unified-jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="generate_adaptive_response",
        )

        # Get tone variant if not provided
        if not tone_variant:
            seller_id = state.get("lead_id", "unknown")
            try:
                tone_variant = await self.ab_testing.get_variant(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    seller_id
                )
            except (KeyError, ValueError):
                tone_variant = "empathetic"

        # Enhanced prompt with adaptive context
        prompt = f"""
        You are Jorge Salas, helpful real estate advisor and relationship builder.

        CURRENT CONTEXT:
        Lead: {state["lead_name"]}
        Adaptive Mode: {state.get("adaptive_mode", "standard")}
        Tone: {state.get("current_tone", "consultative")}
        Tone style: {tone_variant}
        PCS Score: {state.get("psychological_commitment", 0)}
        FRS Classification: {state["intent_profile"].frs.classification if state.get("intent_profile") else "Unknown"}

        RECOMMENDED QUESTION: {next_question}

        TASK: Deliver the question in Jorge's helpful, consultative style that builds trust and rapport.
        """

        response = await self.claude.analyze_with_context(prompt)
        content = response.get("content", next_question)

        # Calendar-focused mode: append real calendar slots for HOT sellers
        if state.get("adaptive_mode") == "calendar_focused" and self.calendar_service:
            try:
                slot_result = await self.calendar_service.offer_appointment_slots(state["lead_id"])
                content = content.rstrip() + "\n\n" + slot_result["message"]
            except Exception as e:
                logger.warning(f"Calendar slot offering failed for {state['lead_id']}: {e}")

        return {
            "response_content": content,
            "adaptive_question_used": next_question,
            "adaptation_applied": True
        }

    async def _enhance_prompt_with_intelligence(
        self,
        base_prompt: str,
        intelligence_context: Any,
        state: JorgeSellerState
    ) -> str:
        """Enhance Claude prompt with intelligence context for better responses."""
        try:
            enhanced_prompt = base_prompt

            # Add property intelligence if available
            property_intel = intelligence_context.property_intelligence
            if property_intel.match_count > 0:
                enhanced_prompt += f"\n\nPROPERTY INTELLIGENCE:"
                enhanced_prompt += f"\n- Found {property_intel.match_count} relevant properties for this seller"
                enhanced_prompt += f"\n- Best match score: {property_intel.best_match_score:.1f}%"
                if property_intel.behavioral_reasoning:
                    enhanced_prompt += f"\n- Reasoning: {property_intel.behavioral_reasoning}"

            # Add conversation intelligence insights
            conversation_intel = intelligence_context.conversation_intelligence
            if conversation_intel.objections_detected:
                enhanced_prompt += f"\n\nOBJECTION INTELLIGENCE:"
                for objection in conversation_intel.objections_detected[:2]:  # Top 2 objections
                    objection_type = objection.get("type", "unknown")
                    confidence = objection.get("confidence", 0.0)
                    context = objection.get("context", "")
                    enhanced_prompt += f"\n- {objection_type.upper()} objection detected ({confidence:.0%}): {context}"

                    # Add suggested responses
                    suggestions = objection.get("suggested_responses", [])
                    if suggestions:
                        enhanced_prompt += f"\n  Suggested approach: {suggestions[0]}"

            # Add preference intelligence insights
            preference_intel = intelligence_context.preference_intelligence
            if preference_intel.profile_completeness > 0.3:
                enhanced_prompt += f"\n\nPREFERENCE INTELLIGENCE:"
                enhanced_prompt += f"\n- Profile completeness: {preference_intel.profile_completeness:.0%}"
                enhanced_prompt += f"\n- Urgency level: {preference_intel.urgency_level:.1f}"

                if preference_intel.budget_range:
                    budget = preference_intel.budget_range
                    enhanced_prompt += f"\n- Budget range: ${budget.get('min', 0):,} - ${budget.get('max', 0):,}"

            # Add intelligent approach recommendations
            enhanced_prompt += f"\n\nINTELLIGENT APPROACH:"
            enhanced_prompt += f"\n- Recommended approach: {intelligence_context.recommended_approach}"
            enhanced_prompt += f"\n- Engagement score: {intelligence_context.composite_engagement_score:.1f}"

            if intelligence_context.priority_insights:
                enhanced_prompt += f"\n- Key insights: {', '.join(intelligence_context.priority_insights[:2])}"

            enhanced_prompt += "\n\nUSE THIS INTELLIGENCE to craft a more targeted, effective response while maintaining Jorge's authentic style."

            return enhanced_prompt

        except Exception as e:
            logger.warning(f"Prompt enhancement failed: {e}")
            return base_prompt
