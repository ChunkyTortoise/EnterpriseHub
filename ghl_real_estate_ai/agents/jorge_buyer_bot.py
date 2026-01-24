"""
Jorge Buyer Bot - LangGraph Orchestrator
Implements consultative buyer qualification to identify 'Serious Buyers'.
Follows proven JorgeSellerBot architecture patterns for buyer-side qualification.

Buyer Bot Features:
- Financial readiness qualification (pre-approval, budget clarity)
- Urgency assessment and timeline commitment
- Property preference qualification
- Decision-maker authority identification
- Market reality education
"""

import asyncio
from typing import Dict, Any, List, Literal
from datetime import datetime
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from bots.shared.ml_analytics_engine import get_ml_analytics_engine

logger = get_logger(__name__)

class JorgeBuyerBot:
    """
    Autonomous buyer bot using consultative qualification.
    Designed to identify 'Serious Buyers' and filter 'Window Shoppers'.

    Buyer Qualification Workflow:
    1. Analyze buyer intent and readiness signals
    2. Assess financial preparedness and budget clarity
    3. Qualify property needs and preferences
    4. Match available properties to buyer criteria
    5. Generate strategic response and education
    6. Schedule follow-up actions based on qualification level
    """

    def __init__(self, tenant_id: str = "jorge_buyer"):
        self.intent_decoder = BuyerIntentDecoder()
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
        self.property_matcher = PropertyMatcher()
        self.ml_analytics = get_ml_analytics_engine(tenant_id)
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(BuyerBotState)

        # 6-Node Buyer Workflow (mirrors seller's 5-node pattern + property matching)
        workflow.add_node("analyze_buyer_intent", self.analyze_buyer_intent)
        workflow.add_node("assess_financial_readiness", self.assess_financial_readiness)
        workflow.add_node("qualify_property_needs", self.qualify_property_needs)
        workflow.add_node("match_properties", self.match_properties)
        workflow.add_node("generate_buyer_response", self.generate_buyer_response)
        workflow.add_node("schedule_next_action", self.schedule_next_action)

        # Define edges (linear with conditional routing)
        workflow.set_entry_point("analyze_buyer_intent")
        workflow.add_edge("analyze_buyer_intent", "assess_financial_readiness")
        workflow.add_edge("assess_financial_readiness", "qualify_property_needs")
        workflow.add_edge("qualify_property_needs", "match_properties")

        # Routing based on qualification status
        workflow.add_conditional_edges(
            "match_properties",
            self._route_buyer_action,
            {
                "respond": "generate_buyer_response",
                "schedule": "schedule_next_action",
                "end": END
            }
        )

        workflow.add_edge("generate_buyer_response", END)
        workflow.add_edge("schedule_next_action", END)

        return workflow.compile()

    async def analyze_buyer_intent(self, state: BuyerBotState) -> Dict:
        """
        Analyze buyer intent and qualification level.
        First step: Understand buyer readiness signals and motivation.
        """
        try:
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-buyer",
                contact_id=state["buyer_id"],
                status="processing",
                current_step="analyze_buyer_intent"
            )

            profile = self.intent_decoder.analyze_buyer(
                state['buyer_id'],
                state['conversation_history']
            )

            # Emit buyer intent analysis event
            await self.event_publisher.publish_buyer_intent_analysis(
                contact_id=state["buyer_id"],
                buyer_temperature=profile.buyer_temperature,
                financial_readiness=profile.financial_readiness,
                urgency_score=profile.urgency_score,
                confidence_level=profile.confidence_level
            )

            return {
                "intent_profile": profile,
                "financial_readiness_score": profile.financial_readiness,
                "buying_motivation_score": profile.urgency_score,
                "current_qualification_step": profile.next_qualification_step,
                "buyer_temperature": profile.buyer_temperature
            }

        except Exception as e:
            logger.error(f"Error analyzing buyer intent for {state['buyer_id']}: {str(e)}")
            return {
                "intent_profile": None,
                "financial_readiness_score": 25.0,
                "buying_motivation_score": 25.0,
                "current_qualification_step": "budget"
            }

    async def assess_financial_readiness(self, state: BuyerBotState) -> Dict:
        """
        Assess financial preparedness and budget clarity.
        Critical for qualifying serious buyers vs window shoppers.
        """
        try:
            profile = state.get("intent_profile")
            if not profile:
                return {"financing_status": "unknown", "budget_range": None}

            # Determine financing status based on intent analysis
            if profile.financing_status_score >= 75:
                financing_status = "pre_approved"
            elif profile.financing_status_score >= 50:
                financing_status = "needs_approval"
            elif profile.budget_clarity >= 70:
                financing_status = "cash"
            else:
                financing_status = "unknown"

            # Extract budget range from conversation if mentioned
            budget_range = await self._extract_budget_range(state['conversation_history'])

            return {
                "financing_status": financing_status,
                "budget_range": budget_range,
                "financial_readiness_score": profile.financial_readiness
            }

        except Exception as e:
            logger.error(f"Error assessing financial readiness for {state['buyer_id']}: {str(e)}")
            return {
                "financing_status": "unknown",
                "budget_range": None
            }

    async def qualify_property_needs(self, state: BuyerBotState) -> Dict:
        """
        Qualify property needs and preferences clarity.
        Determines if buyer has realistic, actionable criteria.
        """
        try:
            profile = state.get("intent_profile")
            if not profile:
                return {"property_preferences": None, "urgency_level": "browsing"}

            # Extract property preferences from conversation
            preferences = await self._extract_property_preferences(state['conversation_history'])

            # Determine urgency level
            if profile.urgency_score >= 75:
                urgency_level = "immediate"
            elif profile.urgency_score >= 50:
                urgency_level = "3_months"
            elif profile.urgency_score >= 30:
                urgency_level = "6_months"
            else:
                urgency_level = "browsing"

            return {
                "property_preferences": preferences,
                "urgency_level": urgency_level,
                "preference_clarity_score": profile.preference_clarity
            }

        except Exception as e:
            logger.error(f"Error qualifying property needs for {state['buyer_id']}: {str(e)}")
            return {
                "property_preferences": None,
                "urgency_level": "browsing"
            }

    async def match_properties(self, state: BuyerBotState) -> Dict:
        """
        Match properties to buyer preferences using existing PropertyMatcher.
        Only proceed if buyer is sufficiently qualified.
        """
        try:
            if not state.get("property_preferences") or not state.get("budget_range"):
                return {
                    "matched_properties": [],
                    "properties_viewed_count": 0,
                    "next_action": "qualify_more"
                }

            # Use existing property matching service
            matches = await self.property_matcher.find_matches(
                buyer_preferences=state["property_preferences"],
                budget_range=state["budget_range"],
                max_results=5
            )

            # Emit property match event
            await self.event_publisher.publish_property_match_update(
                contact_id=state["buyer_id"],
                properties_matched=len(matches),
                match_criteria=state["property_preferences"]
            )

            return {
                "matched_properties": matches[:5],  # Top 5 matches
                "properties_viewed_count": len(matches),
                "next_action": "respond" if matches else "educate_market"
            }

        except Exception as e:
            logger.error(f"Error matching properties for {state['buyer_id']}: {str(e)}")
            return {
                "matched_properties": [],
                "properties_viewed_count": 0,
                "next_action": "qualify_more"
            }

    async def generate_buyer_response(self, state: BuyerBotState) -> Dict:
        """
        Generate strategic buyer response based on qualification and property matches.
        Uses Claude for contextual, educational responses.
        """
        try:
            profile = state.get("intent_profile")
            matches = state.get("matched_properties", [])

            # Generate strategic response using Claude
            response_prompt = f"""
            As Jorge's Buyer Bot, generate a response for this buyer:

            Buyer Temperature: {profile.buyer_temperature if profile else 'cold'}
            Financial Readiness: {state.get('financial_readiness_score', 25)}/100
            Properties Matched: {len(matches)}
            Current Step: {state.get('current_qualification_step', 'unknown')}

            Conversation Context: {state['conversation_history'][-2:] if state['conversation_history'] else []}

            Response should be:
            - Educational and consultative (not pushy)
            - Focused on next qualification step if not fully qualified
            - Property-focused if qualified with matches
            - Market education if qualified but no matches
            - Professional and direct (Jorge's style)

            Keep under 160 characters for SMS compliance.
            """

            response = await self.claude.generate_response(response_prompt)

            return {
                "response_content": response.get("content", "Let me help you find the right property."),
                "response_tone": "consultative",
                "next_action": "send_response"
            }

        except Exception as e:
            logger.error(f"Error generating buyer response for {state['buyer_id']}: {str(e)}")
            return {
                "response_content": "Let me help you find the right property for your needs.",
                "response_tone": "neutral",
                "next_action": "send_response"
            }

    async def schedule_next_action(self, state: BuyerBotState) -> Dict:
        """
        Schedule next action based on buyer qualification level and engagement.
        Follows proven lead nurturing sequences.
        """
        try:
            profile = state.get("intent_profile")
            qualification_score = state.get("financial_readiness_score", 25)

            # Determine next action based on qualification
            if qualification_score >= 75:
                next_action = "schedule_property_tour"
                follow_up_hours = 2  # Hot leads get immediate follow-up
            elif qualification_score >= 50:
                next_action = "send_property_updates"
                follow_up_hours = 24  # Warm leads get daily follow-up
            elif qualification_score >= 30:
                next_action = "market_education"
                follow_up_hours = 72  # Lukewarm leads get educational content
            else:
                next_action = "re_qualification"
                follow_up_hours = 168  # Cold leads get weekly check-in

            # Schedule the action
            await self._schedule_follow_up(
                state["buyer_id"],
                next_action,
                follow_up_hours
            )

            return {
                "next_action": next_action,
                "follow_up_scheduled": True,
                "follow_up_hours": follow_up_hours,
                "last_action_timestamp": datetime.now()
            }

        except Exception as e:
            logger.error(f"Error scheduling next action for {state['buyer_id']}: {str(e)}")
            return {
                "next_action": "manual_review",
                "follow_up_scheduled": False
            }

    def _route_buyer_action(self, state: BuyerBotState) -> Literal["respond", "schedule", "end"]:
        """
        Route to next action based on buyer qualification and context.
        """
        try:
            next_action = state.get("next_action", "respond")
            qualification_score = state.get("financial_readiness_score", 0)

            # Immediate response for qualified buyers with matches
            if next_action == "respond" and qualification_score >= 50:
                return "respond"

            # Schedule follow-up for qualified buyers without immediate action
            elif qualification_score >= 30:
                return "schedule"

            # End conversation for unqualified leads (let them nurture naturally)
            else:
                return "end"

        except Exception as e:
            logger.error(f"Error routing buyer action: {str(e)}")
            return "respond"

    async def _extract_budget_range(self, conversation_history: List[Dict]) -> Optional[Dict[str, int]]:
        """Extract budget range from conversation history."""
        try:
            # Look for dollar amounts in conversation
            import re
            conversation_text = " ".join([
                msg.get("content", "")
                for msg in conversation_history
                if msg.get("role") == "user"
            ])

            # Find dollar amounts
            dollar_pattern = r'\$([0-9,]+)'
            amounts = [int(match.replace(',', '')) for match in re.findall(dollar_pattern, conversation_text)]

            if len(amounts) >= 2:
                return {"min": min(amounts), "max": max(amounts)}
            elif len(amounts) == 1:
                # Single amount - assume it's max budget
                return {"min": int(amounts[0] * 0.8), "max": amounts[0]}

            return None

        except Exception as e:
            logger.error(f"Error extracting budget range: {str(e)}")
            return None

    async def _extract_property_preferences(self, conversation_history: List[Dict]) -> Optional[Dict[str, Any]]:
        """Extract property preferences from conversation history."""
        try:
            conversation_text = " ".join([
                msg.get("content", "").lower()
                for msg in conversation_history
                if msg.get("role") == "user"
            ])

            preferences = {}

            # Extract bedrooms
            import re
            bed_match = re.search(r'(\d+)\s*(bed|bedroom)', conversation_text)
            if bed_match:
                preferences["bedrooms"] = int(bed_match.group(1))

            # Extract bathrooms
            bath_match = re.search(r'(\d+)\s*(bath|bathroom)', conversation_text)
            if bath_match:
                preferences["bathrooms"] = int(bath_match.group(1))

            # Extract features
            features = []
            if "garage" in conversation_text:
                features.append("garage")
            if "pool" in conversation_text:
                features.append("pool")
            if "yard" in conversation_text:
                features.append("yard")

            if features:
                preferences["features"] = features

            return preferences if preferences else None

        except Exception as e:
            logger.error(f"Error extracting property preferences: {str(e)}")
            return None

    async def _schedule_follow_up(self, buyer_id: str, action: str, hours: int):
        """Schedule follow-up action for buyer."""
        try:
            # Emit scheduling event
            await self.event_publisher.publish_buyer_follow_up_scheduled(
                contact_id=buyer_id,
                action_type=action,
                scheduled_hours=hours
            )

            logger.info(f"Scheduled {action} for buyer {buyer_id} in {hours} hours")

        except Exception as e:
            logger.error(f"Error scheduling follow-up for {buyer_id}: {str(e)}")

    async def process_buyer_conversation(self, buyer_id: str, buyer_name: str,
                                       conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Main entry point for processing buyer conversations.
        Returns complete buyer qualification results.
        """
        try:
            # Prepare initial state
            initial_state = BuyerBotState(
                buyer_id=buyer_id,
                buyer_name=buyer_name,
                target_areas=None,
                conversation_history=conversation_history,
                intent_profile=None,
                budget_range=None,
                financing_status="unknown",
                urgency_level="browsing",
                property_preferences=None,
                current_qualification_step="budget",
                objection_detected=False,
                detected_objection_type=None,
                next_action="qualify",
                response_content="",
                financial_readiness_score=0.0,
                buying_motivation_score=0.0,
                is_qualified=False,
                current_journey_stage="discovery",
                properties_viewed_count=0,
                last_action_timestamp=None
            )

            # Execute buyer workflow
            result = await self.workflow.ainvoke(initial_state)

            # Mark as qualified if scores are high enough
            is_qualified = (
                result.get("financial_readiness_score", 0) >= 50 and
                result.get("buying_motivation_score", 0) >= 50
            )

            result["is_qualified"] = is_qualified

            # Emit final qualification result
            await self.event_publisher.publish_buyer_qualification_complete(
                contact_id=buyer_id,
                qualification_status="qualified" if is_qualified else "needs_nurturing",
                final_score=(result.get("financial_readiness_score", 0) +
                           result.get("buying_motivation_score", 0)) / 2,
                properties_matched=len(result.get("matched_properties", []))
            )

            return result

        except Exception as e:
            logger.error(f"Error processing buyer conversation for {buyer_id}: {str(e)}")
            return {
                "buyer_id": buyer_id,
                "error": str(e),
                "qualification_status": "error",
                "response_content": "I'm having technical difficulties. Let me connect you with Jorge directly."
            }