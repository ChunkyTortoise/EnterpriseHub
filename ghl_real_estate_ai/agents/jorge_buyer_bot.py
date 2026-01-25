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
from typing import Dict, Any, List, Literal, Optional
from datetime import datetime, timezone
from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder

# Custom exceptions for proper error handling and escalation
class BuyerQualificationError(Exception):
    """Base exception for buyer qualification failures"""
    def __init__(self, message: str, recoverable: bool = False, escalate: bool = False):
        super().__init__(message)
        self.recoverable = recoverable
        self.escalate = escalate

class BuyerIntentAnalysisError(BuyerQualificationError):
    """Raised when buyer intent analysis fails"""
    pass

class FinancialAssessmentError(BuyerQualificationError):
    """Raised when financial readiness assessment fails"""
    pass

class ClaudeAPIError(BuyerQualificationError):
    """Raised when Claude AI service fails"""
    pass

class NetworkError(BuyerQualificationError):
    """Raised when network connectivity issues occur"""
    pass

class ComplianceValidationError(BuyerQualificationError):
    """Raised when compliance validation fails (Fair Housing, TREC)"""
    pass

# Error IDs for monitoring and alerting
ERROR_ID_BUYER_QUALIFICATION_FAILED = "BUYER_QUALIFICATION_FAILED"
ERROR_ID_FINANCIAL_ASSESSMENT_FAILED = "FINANCIAL_ASSESSMENT_FAILED"
ERROR_ID_COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
ERROR_ID_SYSTEM_FAILURE = "SYSTEM_FAILURE"
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

        except (ClaudeAPIError, NetworkError) as e:
            # Transient errors - retry with backoff
            logger.warning(f"Transient error analyzing buyer intent for {state['buyer_id']}: {e}",
                         extra={"error_id": ERROR_ID_BUYER_QUALIFICATION_FAILED,
                                "buyer_id": state['buyer_id'],
                                "recoverable": True})
            # TODO: Implement retry mechanism with exponential backoff
            return {
                "intent_profile": None,
                "qualification_status": "retry_required",
                "error": "Temporary service issue. Retrying analysis.",
                "financial_readiness_score": None,  # Don't default to low scores
                "buying_motivation_score": None,
                "current_qualification_step": "intent_retry"
            }
        except BuyerIntentAnalysisError as e:
            # Business logic errors - alert and escalate
            logger.error(f"BUSINESS CRITICAL: Intent analysis failed for {state['buyer_id']}: {e}",
                        extra={"error_id": ERROR_ID_BUYER_QUALIFICATION_FAILED,
                               "buyer_id": state['buyer_id'],
                               "escalate": True})
            # TODO: Implement escalate_to_human_review method
            return {
                "intent_profile": None,
                "qualification_status": "manual_review_required",
                "error": "Analysis requires human review. Lead prioritized for immediate attention.",
                "escalation_reason": "intent_analysis_failure",
                "financial_readiness_score": None,  # Preserve unknown state
                "buying_motivation_score": None,
                "current_qualification_step": "human_review"
            }
        except Exception as e:
            # Unexpected system errors - escalate immediately
            logger.error(f"SYSTEM ERROR: Unexpected failure in buyer intent analysis: {e}",
                        extra={"error_id": ERROR_ID_SYSTEM_FAILURE,
                               "buyer_id": state['buyer_id'],
                               "critical": True})
            # Don't hide system failures - let them bubble up
            raise BuyerQualificationError(f"System failure in intent analysis: {str(e)}",
                                        recoverable=False, escalate=True)

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
            financing_score = float(profile.financing_status_score or 0)
            budget_score = float(profile.budget_clarity or 0)
            
            if financing_score >= 75:
                financing_status = "pre_approved"
            elif financing_score >= 50:
                financing_status = "needs_approval"
            elif budget_score >= 70:
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

        except NetworkError as e:
            # External service failures - retry with alternative sources
            logger.warning(f"Financial service network error for buyer {state['buyer_id']}: {e}",
                         extra={"error_id": ERROR_ID_FINANCIAL_ASSESSMENT_FAILED,
                                "buyer_id": state['buyer_id'],
                                "retry_recommended": True})
            # TODO: Implement fallback financial assessment method
            return {
                "financing_status": "assessment_pending",
                "budget_range": None,
                "requires_manual_review": True,
                "error": "Financial assessment temporarily unavailable. Will retry shortly."
            }
        except ComplianceValidationError as e:
            # Compliance failures - immediate escalation
            logger.error(f"COMPLIANCE VIOLATION: Financial assessment failed validation for {state['buyer_id']}: {e}",
                        extra={"error_id": ERROR_ID_COMPLIANCE_VIOLATION,
                               "buyer_id": state['buyer_id'],
                               "compliance_alert": True})
            # TODO: Implement escalate_compliance_violation method
            return {
                "financing_status": "compliance_review_required",
                "budget_range": None,
                "error": "Assessment requires compliance review",
                "compliance_issue": str(e)
            }
        except Exception as e:
            logger.error(f"Unexpected error in financial assessment for {state['buyer_id']}: {e}",
                        extra={"error_id": ERROR_ID_FINANCIAL_ASSESSMENT_FAILED,
                               "buyer_id": state['buyer_id']})
            # Don't hide unexpected errors - let them bubble up for investigation
            raise FinancialAssessmentError(f"Unexpected financial assessment failure: {str(e)}",
                                         recoverable=False, escalate=True)

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
            urgency_score = float(profile.urgency_score or 0)
            if urgency_score >= 75:
                urgency_level = "immediate"
            elif urgency_score >= 50:
                urgency_level = "3_months"
            elif urgency_score >= 30:
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
            if not state.get("budget_range"):
                return {
                    "matched_properties": [],
                    "properties_viewed_count": 0,
                    "next_action": "qualify_more"
                }

            # Use existing property matching service
            # Handle both sync and async property matcher (for tests/mocks)
            if asyncio.iscoroutinefunction(self.property_matcher.find_matches):
                matches = await self.property_matcher.find_matches(
                    preferences=state.get("property_preferences") or {},
                    limit=5
                )
            else:
                matches = self.property_matcher.find_matches(
                    preferences=state.get("property_preferences") or {},
                    limit=5
                )

            # Emit property match event
            await self.event_publisher.publish_property_match_update(
                contact_id=state["buyer_id"],
                properties_matched=len(matches),
                match_criteria=state["property_preferences"]
            )

            return {
                "matched_properties": matches[:5],  # Top 5 matches
                "property_matches": matches[:5],    # Add for consistency with script expectation
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
                "last_action_timestamp": datetime.now(timezone.utc)
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

            # Find dollar amounts with optional k
            dollar_pattern = r'\$([0-9,]+)([kK]?)'
            matches = re.findall(dollar_pattern, conversation_text)
            
            amounts = []
            for val, k_suffix in matches:
                amount = int(val.replace(',', ''))
                if k_suffix:
                    amount *= 1000
                elif amount < 1000: # Handle cases like "500" meaning 500k
                    amount *= 1000
                amounts.append(amount)

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
                matched_properties=[],
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