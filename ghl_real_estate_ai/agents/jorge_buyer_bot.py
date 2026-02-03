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
import random
import uuid
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
    """Raised when compliance validation fails (Fair Housing, DRE)"""
    pass

# Error IDs for monitoring and alerting
ERROR_ID_BUYER_QUALIFICATION_FAILED = "BUYER_QUALIFICATION_FAILED"
ERROR_ID_FINANCIAL_ASSESSMENT_FAILED = "FINANCIAL_ASSESSMENT_FAILED"
ERROR_ID_COMPLIANCE_VIOLATION = "COMPLIANCE_VIOLATION"
ERROR_ID_SYSTEM_FAILURE = "SYSTEM_FAILURE"
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from bots.shared.ml_analytics_engine import get_ml_analytics_engine

# Phase 3.3 Bot Intelligence Middleware Integration
try:
    from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware
    from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
    BOT_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Bot Intelligence Middleware unavailable: {e}")
    BOT_INTELLIGENCE_AVAILABLE = False

logger = get_logger(__name__)


# ================================
# RETRY MECHANISM WITH EXPONENTIAL BACKOFF
# ================================

class RetryConfig:
    """Configuration for retry behavior."""
    def __init__(self, max_retries: int = 3, initial_backoff_ms: int = 500,
                 exponential_base: float = 2.0, jitter_factor: float = 0.1):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.exponential_base = exponential_base
        self.jitter_factor = jitter_factor

DEFAULT_RETRY_CONFIG = RetryConfig()

RETRYABLE_EXCEPTIONS = (ClaudeAPIError, NetworkError)
NON_RETRYABLE_EXCEPTIONS = (BuyerIntentAnalysisError, ComplianceValidationError)


async def async_retry_with_backoff(coro_factory, retry_config: RetryConfig = None,
                                    context_label: str = "operation"):
    """
    Retry an async operation with exponential backoff and jitter.

    Args:
        coro_factory: Callable that returns a new coroutine on each invocation.
        retry_config: Retry configuration. Uses DEFAULT_RETRY_CONFIG if None.
        context_label: Label for logging.

    Returns:
        The result of the coroutine on success.

    Raises:
        The last exception if all retries are exhausted, or immediately
        for non-retryable exceptions.
    """
    config = retry_config or DEFAULT_RETRY_CONFIG
    last_exception = None

    for attempt in range(config.max_retries + 1):
        try:
            return await coro_factory()
        except NON_RETRYABLE_EXCEPTIONS:
            raise
        except RETRYABLE_EXCEPTIONS as e:
            last_exception = e
            if attempt < config.max_retries:
                backoff_ms = config.initial_backoff_ms * (config.exponential_base ** attempt)
                jitter = backoff_ms * config.jitter_factor * (2 * random.random() - 1)
                sleep_seconds = (backoff_ms + jitter) / 1000.0
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} for {context_label}: {e}. "
                    f"Backing off {sleep_seconds:.3f}s"
                )
                await asyncio.sleep(sleep_seconds)
            else:
                logger.error(
                    f"All {config.max_retries} retries exhausted for {context_label}: {e}"
                )
                raise

    raise last_exception  # Should not reach here, but safety net


# ================================
# COMPLIANCE SEVERITY LEVELS
# ================================

COMPLIANCE_SEVERITY_MAP = {
    "fair_housing": "critical",
    "privacy": "high",
    "financial_regulation": "high",
    "licensing": "medium",
}


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

    def __init__(self, tenant_id: str = "jorge_buyer", enable_bot_intelligence: bool = True):
        self.intent_decoder = BuyerIntentDecoder()
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
        self.property_matcher = PropertyMatcher()
        self.ml_analytics = get_ml_analytics_engine(tenant_id)
        self.ghl_client = GHLClient()

        # Phase 3.3 Bot Intelligence Middleware Integration
        self.enable_bot_intelligence = enable_bot_intelligence
        self.intelligence_middleware = None
        if self.enable_bot_intelligence and BOT_INTELLIGENCE_AVAILABLE:
            self.intelligence_middleware = get_bot_intelligence_middleware()
            logger.info("Jorge Buyer Bot: Bot Intelligence Middleware enabled (Phase 3.3)")
        elif self.enable_bot_intelligence:
            logger.warning("Jorge Buyer Bot: Bot Intelligence requested but dependencies not available")

        # Performance tracking for intelligence enhancements
        self.workflow_stats = {
            "total_interactions": 0,
            "intelligence_enhancements": 0,
            "intelligence_cache_hits": 0,
        }

        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(BuyerBotState)

        # 6-Node Buyer Workflow + Intelligence Enhancement (mirrors seller's pattern)
        workflow.add_node("analyze_buyer_intent", self.analyze_buyer_intent)

        # Add intelligence gathering node if enabled
        if self.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_buyer_intelligence", self.gather_buyer_intelligence)

        workflow.add_node("assess_financial_readiness", self.assess_financial_readiness)
        workflow.add_node("qualify_property_needs", self.qualify_property_needs)
        workflow.add_node("match_properties", self.match_properties)
        workflow.add_node("generate_buyer_response", self.generate_buyer_response)
        workflow.add_node("schedule_next_action", self.schedule_next_action)

        # Define edges (linear with conditional routing)
        workflow.set_entry_point("analyze_buyer_intent")

        # Conditional routing for intelligence gathering
        if self.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge("analyze_buyer_intent", "gather_buyer_intelligence")
            workflow.add_edge("gather_buyer_intelligence", "assess_financial_readiness")
        else:
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
        Uses retry with exponential backoff for transient failures.
        """
        try:
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-buyer",
                contact_id=state["buyer_id"],
                status="processing",
                current_step="analyze_buyer_intent"
            )

            async def _do_intent_analysis():
                return self.intent_decoder.analyze_buyer(
                    state['buyer_id'],
                    state['conversation_history']
                )

            # Retry transient failures with exponential backoff
            profile = await async_retry_with_backoff(
                _do_intent_analysis,
                context_label=f"intent_analysis:{state['buyer_id']}"
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
            # All retries exhausted for transient errors
            logger.warning(f"All retries exhausted for buyer intent analysis {state['buyer_id']}: {e}",
                         extra={"error_id": ERROR_ID_BUYER_QUALIFICATION_FAILED,
                                "buyer_id": state['buyer_id'],
                                "recoverable": False})
            return {
                "intent_profile": None,
                "qualification_status": "retry_exhausted",
                "error": "Temporary service issue. Please try again shortly.",
                "financial_readiness_score": None,
                "buying_motivation_score": None,
                "current_qualification_step": "intent_retry"
            }
        except BuyerIntentAnalysisError as e:
            # Business logic errors - alert and escalate to human
            logger.error(f"BUSINESS CRITICAL: Intent analysis failed for {state['buyer_id']}: {e}",
                        extra={"error_id": ERROR_ID_BUYER_QUALIFICATION_FAILED,
                               "buyer_id": state['buyer_id'],
                               "escalate": True})
            escalation = await self.escalate_to_human_review(
                buyer_id=state['buyer_id'],
                reason="intent_analysis_failure",
                context={"error": str(e), "conversation_history": state.get("conversation_history", [])}
            )
            return {
                "intent_profile": None,
                "qualification_status": "manual_review_required",
                "error": "Analysis requires human review. Lead prioritized for immediate attention.",
                "escalation_reason": "intent_analysis_failure",
                "escalation_id": escalation.get("escalation_id"),
                "financial_readiness_score": None,
                "buying_motivation_score": None,
                "current_qualification_step": "human_review"
            }
        except Exception as e:
            # Unexpected system errors - escalate immediately
            logger.error(f"SYSTEM ERROR: Unexpected failure in buyer intent analysis: {e}",
                        extra={"error_id": ERROR_ID_SYSTEM_FAILURE,
                               "buyer_id": state['buyer_id'],
                               "critical": True})
            raise BuyerQualificationError(f"System failure in intent analysis: {str(e)}",
                                        recoverable=False, escalate=True)

    async def gather_buyer_intelligence(self, state: BuyerBotState) -> Dict:
        """
        Phase 3.3: Gather buyer intelligence context for enhanced property matching.

        Integrates with Bot Intelligence Middleware to provide:
        - Property matching intelligence for consultative recommendations
        - Conversation intelligence for preference detection
        - Market intelligence for realistic buyer education

        Designed for buyer bot's consultative workflow - graceful fallback on failures.
        """
        import time

        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-buyer",
            contact_id=state["buyer_id"],
            status="processing",
            current_step="gather_buyer_intelligence"
        )

        intelligence_context = None
        intelligence_performance_ms = 0.0

        try:
            if self.intelligence_middleware:
                logger.info(f"Gathering intelligence context for buyer {state['buyer_id']}")

                # Extract buyer preferences from conversation for intelligence gathering
                preferences = self._extract_buyer_preferences_from_conversation(
                    state.get("conversation_history", [])
                )

                # Get intelligence context with <200ms target (buyer-focused)
                start_time = time.time()
                intelligence_context = await self.intelligence_middleware.enhance_bot_context(
                    bot_type="jorge-buyer",
                    lead_id=state["buyer_id"],
                    location_id=state.get("location_id", "rancho_cucamonga"),  # Default to Rancho Cucamonga market
                    conversation_context=state.get("conversation_history", []),
                    preferences=preferences
                )
                intelligence_performance_ms = (time.time() - start_time) * 1000

                # Update performance statistics
                self.workflow_stats["intelligence_enhancements"] += 1
                if intelligence_context.cache_hit:
                    self.workflow_stats["intelligence_cache_hits"] += 1

                # Log performance metrics
                logger.info(
                    f"Buyer intelligence gathered for {state['buyer_id']} in {intelligence_performance_ms:.1f}ms "
                    f"(cache_hit: {intelligence_context.cache_hit})"
                )

                # Emit intelligence gathering event for monitoring (buyer-specific)
                await self.event_publisher.publish_conversation_update(
                    conversation_id=f"jorge_buyer_{state['buyer_id']}",
                    lead_id=state['buyer_id'],
                    stage="buyer_intelligence_enhanced",
                    message=f"Buyer intelligence gathered: {intelligence_context.property_intelligence.match_count} properties, "
                           f"sentiment {intelligence_context.conversation_intelligence.overall_sentiment:.2f}"
                )

        except Exception as e:
            logger.warning(f"Buyer intelligence enhancement unavailable for {state['buyer_id']}: {e}")
            # Don't let intelligence failures block buyer workflow
            intelligence_context = None

        return {
            "intelligence_context": intelligence_context,
            "intelligence_performance_ms": intelligence_performance_ms,
            "intelligence_available": intelligence_context is not None
        }

    def _extract_buyer_preferences_from_conversation(self, conversation_history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract buyer preferences from conversation for intelligence gathering."""
        preferences = {}

        if not conversation_history:
            return preferences

        # Look for buyer signals in conversation
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_history]).lower()

        # Budget extraction (buyer-focused)
        budget_keywords = {
            "under 300": {"budget_max": 700000, "buyer_type": "first_time"},
            "under 400": {"budget_max": 400000, "buyer_type": "entry_level"},
            "under 500": {"budget_max": 700000, "buyer_type": "mid_market"},
            "under 600": {"budget_max": 600000, "buyer_type": "mid_market"},
            "under 700": {"budget_max": 700000, "buyer_type": "move_up"},
            "under 800": {"budget_max": 800000, "buyer_type": "move_up"},
            "under 1m": {"budget_max": 1200000, "buyer_type": "luxury"},
            "under 1 million": {"budget_max": 1200000, "buyer_type": "luxury"},
            "over 1m": {"budget_min": 1200000, "buyer_type": "luxury_plus"}
        }

        for keyword, budget_info in budget_keywords.items():
            if keyword in conversation_text:
                preferences.update(budget_info)
                break

        # Timeline extraction (buyer urgency)
        urgency_keywords = {
            "asap": {"urgency": "immediate", "timeline": "1_month"},
            "quickly": {"urgency": "high", "timeline": "2_months"},
            "urgent": {"urgency": "high", "timeline": "1_month"},
            "3 months": {"urgency": "medium", "timeline": "3_months"},
            "6 months": {"urgency": "low", "timeline": "6_months"},
            "next year": {"urgency": "very_low", "timeline": "12_months"},
            "no rush": {"urgency": "browsing", "timeline": "flexible"}
        }

        for keyword, urgency_info in urgency_keywords.items():
            if keyword in conversation_text:
                preferences.update(urgency_info)
                break

        # Property type preferences (buyer-specific)
        property_keywords = {
            "condo": {"property_type": "condo"},
            "house": {"property_type": "house"},
            "townhouse": {"property_type": "townhouse"},
            "single family": {"property_type": "single_family"},
            "new construction": {"property_type": "new_construction"},
            "investment": {"buyer_intent": "investment"}
        }

        for keyword, prop_info in property_keywords.items():
            if keyword in conversation_text:
                preferences.update(prop_info)
                break

        return preferences

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
            # External service failures - use fallback financial assessment
            logger.warning(f"Financial service network error for buyer {state['buyer_id']}: {e}",
                         extra={"error_id": ERROR_ID_FINANCIAL_ASSESSMENT_FAILED,
                                "buyer_id": state['buyer_id'],
                                "retry_recommended": True})
            return await self._fallback_financial_assessment(state)
        except ComplianceValidationError as e:
            # Compliance failures - immediate escalation
            logger.error(f"COMPLIANCE VIOLATION: Financial assessment failed validation for {state['buyer_id']}: {e}",
                        extra={"error_id": ERROR_ID_COMPLIANCE_VIOLATION,
                               "buyer_id": state['buyer_id'],
                               "compliance_alert": True})
            compliance_result = await self.escalate_compliance_violation(
                buyer_id=state['buyer_id'],
                violation_type="financial_regulation",
                evidence={"error": str(e), "stage": "financial_assessment",
                          "buyer_id": state['buyer_id']}
            )
            return {
                "financing_status": "compliance_review_required",
                "budget_range": None,
                "error": "Assessment requires compliance review",
                "compliance_issue": str(e),
                "compliance_ticket_id": compliance_result.get("compliance_ticket_id"),
                "bot_paused": compliance_result.get("bot_paused", False)
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
        Enhanced with Phase 3.3 intelligence context for consultative recommendations.
        """
        try:
            profile = state.get("intent_profile")
            matches = state.get("matched_properties", [])
            intelligence_context = state.get("intelligence_context")

            # Base prompt for buyer consultation
            response_prompt = f"""
            As Jorge's Buyer Bot, generate a helpful and supportive response for this buyer:

            Buyer Temperature: {profile.buyer_temperature if profile else 'cold'}
            Financial Readiness: {state.get('financial_readiness_score', 25)}/100
            Properties Matched: {len(matches)}
            Current Step: {state.get('current_qualification_step', 'unknown')}

            Conversation Context: {state['conversation_history'][-2:] if state['conversation_history'] else []}

            Response should be:
            - Warm, helpful and genuinely caring
            - Educational and patient (never pushy)
            - Focused on understanding their needs first
            - Property-focused if qualified with matches
            - Market education if qualified but no matches
            - Professional, friendly and relationship-focused (Jorge's style)

            Keep under 160 characters for SMS compliance.
            """

            # Enhance prompt with intelligence context if available (Phase 3.3)
            if intelligence_context:
                response_prompt = await self._enhance_buyer_prompt_with_intelligence(
                    response_prompt, intelligence_context, state
                )

            response = await self.claude.generate_response(response_prompt)

            return {
                "response_content": response.get("content", "I'd love to help you find the perfect property for your needs."),
                "response_tone": "friendly_consultative",
                "next_action": "send_response"
            }

        except Exception as e:
            logger.error(f"Error generating buyer response for {state['buyer_id']}: {str(e)}")
            return {
                "response_content": "I'd love to help you find the perfect property for your needs.",
                "response_tone": "friendly_supportive",
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

    # ================================
    # ERROR HANDLING & ESCALATION METHODS
    # ================================

    async def escalate_to_human_review(self, buyer_id: str, reason: str, context: Dict) -> Dict:
        """
        Escalate buyer conversation to human agent review.

        Creates real GHL artifacts (tag, note, workflow trigger, disposition update)
        so the human agent sees the escalation in the CRM immediately.

        Graceful degradation: individual step failures are logged but do not
        crash the bot or block subsequent steps.

        Returns:
            Dict with escalation_id and per-step status.
        """
        escalation_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Escalating buyer to human review",
            extra={
                "escalation_id": escalation_id,
                "buyer_id": buyer_id,
                "reason": reason,
            },
        )

        escalation_result = {
            "escalation_id": escalation_id,
            "buyer_id": buyer_id,
            "reason": reason,
            "timestamp": timestamp,
            "tag_added": False,
            "note_added": False,
            "workflow_triggered": False,
            "disposition_updated": False,
            "event_published": False,
            "status": "pending",
        }

        # 1. Add "Escalation" tag to GHL contact
        try:
            await self.ghl_client.add_tags(buyer_id, ["Escalation"])
            escalation_result["tag_added"] = True
            logger.info(
                "Escalation tag added to contact",
                extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
            )
        except Exception as e:
            logger.warning(
                f"Failed to add Escalation tag for {buyer_id}: {e}",
                extra={"escalation_id": escalation_id, "error": str(e)},
            )

        # 2. Add a note to the contact with escalation details
        try:
            conversation_summary = context.get("conversation_summary", "")
            qualification_score = context.get("qualification_score", "N/A")
            current_step = context.get("current_step", "unknown")

            note_body = (
                f"[BUYER ESCALATION - {timestamp}]\n"
                f"Escalation ID: {escalation_id}\n"
                f"Reason: {reason}\n"
                f"Qualification Score: {qualification_score}\n"
                f"Stage: {current_step}\n"
                f"---\n"
                f"Context: {conversation_summary[:500] if conversation_summary else 'No summary available'}"
            )

            import httpx
            endpoint = f"{self.ghl_client.base_url}/contacts/{buyer_id}/notes"
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    endpoint,
                    json={"body": note_body},
                    headers=self.ghl_client.headers,
                    timeout=settings.webhook_timeout_seconds,
                )
                response.raise_for_status()

            escalation_result["note_added"] = True
            logger.info(
                "Escalation note added to contact",
                extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
            )
        except Exception as e:
            logger.warning(
                f"Failed to add escalation note for {buyer_id}: {e}",
                extra={"escalation_id": escalation_id, "error": str(e)},
            )

        # 3. Trigger notify-agent workflow if configured
        if settings.notify_agent_workflow_id:
            try:
                await self.ghl_client.trigger_workflow(
                    buyer_id, settings.notify_agent_workflow_id
                )
                escalation_result["workflow_triggered"] = True
                logger.info(
                    "Notify-agent workflow triggered",
                    extra={
                        "buyer_id": buyer_id,
                        "workflow_id": settings.notify_agent_workflow_id,
                        "escalation_id": escalation_id,
                    },
                )
            except Exception as e:
                logger.warning(
                    f"Failed to trigger notify-agent workflow for {buyer_id}: {e}",
                    extra={"escalation_id": escalation_id, "error": str(e)},
                )

        # 4. Update contact disposition to indicate escalation
        if settings.disposition_field_name:
            try:
                await self.ghl_client.update_custom_field(
                    buyer_id,
                    settings.disposition_field_name,
                    "Escalated - Needs Human Review",
                )
                escalation_result["disposition_updated"] = True
                logger.info(
                    "Contact disposition updated to escalated",
                    extra={"buyer_id": buyer_id, "escalation_id": escalation_id},
                )
            except Exception as e:
                logger.warning(
                    f"Failed to update disposition for {buyer_id}: {e}",
                    extra={"escalation_id": escalation_id, "error": str(e)},
                )

        # 5. Publish internal event for dashboards and monitoring
        try:
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-buyer",
                contact_id=buyer_id,
                status="escalated",
                current_step="human_review",
                escalation_id=escalation_id,
                reason=reason,
            )
            escalation_result["event_published"] = True
        except Exception as e:
            logger.warning(
                f"Event publish failed for escalation {escalation_id}: {e}",
                extra={"escalation_id": escalation_id, "error": str(e)},
            )

        # 6. Determine final status
        ghl_actions_succeeded = (
            escalation_result["tag_added"]
            or escalation_result["note_added"]
            or escalation_result["workflow_triggered"]
        )
        if ghl_actions_succeeded:
            escalation_result["status"] = "escalated"
        elif escalation_result["event_published"]:
            escalation_result["status"] = "escalated_internal_only"
            logger.warning(
                "GHL actions failed but internal event published - agent may not see escalation in CRM",
                extra={"escalation_id": escalation_id, "buyer_id": buyer_id},
            )
        else:
            escalation_result["status"] = "queued"
            logger.error(
                "All escalation channels failed for buyer. Queued for manual processing.",
                extra={"escalation_id": escalation_id, "buyer_id": buyer_id},
            )

        return escalation_result

    async def _fallback_financial_assessment(self, state: BuyerBotState) -> Dict:
        """
        Multi-tier fallback for financial assessment when primary service fails.

        Tier 1: Conversation history heuristics (pre-approval, budget mentions)
        Tier 2: Conservative default assessment
        Tier 3: Queue for manual review, continue conversation

        Never fails - always returns a reasonable assessment with confidence score.
        """
        buyer_id = state.get("buyer_id", "unknown")
        conversation_history = state.get("conversation_history", [])
        conversation_text = " ".join(
            msg.get("content", "").lower()
            for msg in conversation_history
            if msg.get("role") == "user"
        )

        # Tier 1: Conversation heuristics
        try:
            heuristic_result = self._assess_financial_from_conversation(conversation_text)
            if heuristic_result:
                logger.info(f"Financial fallback Tier 1 (heuristic) used for buyer {buyer_id}",
                           extra={"fallback_tier": 1, "buyer_id": buyer_id})
                return {
                    "financing_status": heuristic_result["financing_status"],
                    "budget_range": heuristic_result.get("budget_range"),
                    "financial_readiness_score": heuristic_result["confidence"],
                    "fallback_tier": 1,
                    "fallback_source": "conversation_heuristic"
                }
        except Exception as e:
            logger.warning(f"Tier 1 fallback failed for {buyer_id}: {e}")

        # Tier 2: Conservative default
        logger.info(f"Financial fallback Tier 2 (conservative default) used for buyer {buyer_id}",
                    extra={"fallback_tier": 2, "buyer_id": buyer_id})
        return {
            "financing_status": "assessment_pending",
            "budget_range": None,
            "financial_readiness_score": 25.0,
            "requires_manual_review": True,
            "fallback_tier": 2,
            "fallback_source": "conservative_default",
            "confidence": 0.3
        }

    def _assess_financial_from_conversation(self, conversation_text: str) -> Optional[Dict]:
        """Extract financial signals from conversation text."""
        if not conversation_text.strip():
            return None

        confidence = 0.5
        financing_status = "unknown"

        # High-confidence signals
        pre_approval_keywords = ["pre-approved", "preapproved", "pre approved", "got approved"]
        cash_keywords = ["cash buyer", "paying cash", "all cash", "cash offer"]
        budget_keywords = ["budget is", "can afford", "max price", "price range"]

        if any(kw in conversation_text for kw in pre_approval_keywords):
            financing_status = "pre_approved"
            confidence = 0.8
        elif any(kw in conversation_text for kw in cash_keywords):
            financing_status = "cash"
            confidence = 0.85
        elif any(kw in conversation_text for kw in budget_keywords):
            financing_status = "needs_approval"
            confidence = 0.6
        else:
            return None

        return {
            "financing_status": financing_status,
            "confidence": confidence * 100,
        }

    async def escalate_compliance_violation(self, buyer_id: str, violation_type: str,
                                            evidence: Dict) -> Dict:
        """
        Handle compliance violation detection and escalation.

        1. Logs violation to audit trail with full evidence
        2. Determines severity (critical, high, medium, low)
        3. Notifies compliance officer for critical/high severity
        4. Flags contact in CRM with violation type
        5. Pauses bot interactions until human review
        6. Returns compliance_ticket_id

        Supported violation types: fair_housing, privacy, financial_regulation, licensing
        """
        compliance_ticket_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        severity = COMPLIANCE_SEVERITY_MAP.get(violation_type, "medium")

        logger.error(
            f"COMPLIANCE VIOLATION [{severity.upper()}]: {violation_type} for buyer {buyer_id}",
            extra={
                "error_id": ERROR_ID_COMPLIANCE_VIOLATION,
                "compliance_ticket_id": compliance_ticket_id,
                "buyer_id": buyer_id,
                "violation_type": violation_type,
                "severity": severity,
                "timestamp": timestamp,
                "evidence_keys": list(evidence.keys())
            }
        )

        result = {
            "compliance_ticket_id": compliance_ticket_id,
            "buyer_id": buyer_id,
            "violation_type": violation_type,
            "severity": severity,
            "timestamp": timestamp,
            "audit_logged": False,
            "notification_sent": False,
            "crm_flagged": False,
            "bot_paused": False,
            "status": "pending"
        }

        # 1. Log to audit trail
        try:
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_buyer_{buyer_id}",
                lead_id=buyer_id,
                stage="compliance_violation",
                message=f"Compliance violation: {violation_type} (severity: {severity})",
                compliance_ticket_id=compliance_ticket_id,
                violation_type=violation_type,
                severity=severity,
                evidence_summary=str(evidence.get("summary", ""))[:500]
            )
            result["audit_logged"] = True
        except Exception as e:
            logger.error(f"Audit logging failed for compliance ticket {compliance_ticket_id}: {e}")

        # 2. Notify compliance officer for critical/high severity
        if severity in ("critical", "high"):
            try:
                await self.event_publisher.publish_bot_status_update(
                    bot_type="jorge-buyer",
                    contact_id=buyer_id,
                    status="compliance_alert",
                    current_step="compliance_review",
                    compliance_ticket_id=compliance_ticket_id,
                    violation_type=violation_type,
                    severity=severity,
                    priority="urgent"
                )
                result["notification_sent"] = True
            except Exception as e:
                logger.error(f"Compliance notification failed for ticket {compliance_ticket_id}: {e}")

        # 3. Flag in CRM via status update
        try:
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-buyer",
                contact_id=buyer_id,
                status="compliance_flagged",
                current_step="bot_paused",
                compliance_ticket_id=compliance_ticket_id,
                violation_type=violation_type
            )
            result["crm_flagged"] = True
            result["bot_paused"] = True
        except Exception as e:
            logger.error(f"CRM flagging failed for compliance ticket {compliance_ticket_id}: {e}")

        # 4. Determine overall status
        if result["audit_logged"]:
            result["status"] = "escalated"
        else:
            result["status"] = "escalation_degraded"

        return result

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
                elif amount < 1000: # Handle cases like "500" meaning 700k
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

            # Update performance statistics
            self.workflow_stats["total_interactions"] += 1

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

    # ================================
    # PHASE 3.3 INTELLIGENCE ENHANCEMENT METHODS
    # ================================

    async def _enhance_buyer_prompt_with_intelligence(
        self,
        base_prompt: str,
        intelligence_context: "BotIntelligenceContext",
        state: BuyerBotState
    ) -> str:
        """
        Enhance Claude prompt with buyer intelligence context for consultative responses.

        Adds property recommendations, preference insights, and market intelligence
        while maintaining the buyer bot's consultative and educational approach.
        """
        try:
            enhanced_prompt = base_prompt

            # Add property intelligence if available
            property_intel = intelligence_context.property_intelligence
            if property_intel.match_count > 0:
                enhanced_prompt += f"\n\nPROPERTY INTELLIGENCE:"
                enhanced_prompt += f"\n- Found {property_intel.match_count} properties matching buyer preferences"
                enhanced_prompt += f"\n- Best match score: {property_intel.best_match_score:.1f}%"
                if property_intel.behavioral_reasoning:
                    enhanced_prompt += f"\n- Match reasoning: {property_intel.behavioral_reasoning}"

            # Add conversation intelligence insights for buyer consultation
            conversation_intel = intelligence_context.conversation_intelligence
            if conversation_intel.objections_detected:
                enhanced_prompt += f"\n\nBUYER CONCERNS DETECTED:"
                for objection in conversation_intel.objections_detected[:2]:  # Top 2 concerns
                    concern_type = objection.get('type', 'unknown')
                    confidence = objection.get('confidence', 0.0)
                    context = objection.get('context', '')
                    enhanced_prompt += f"\n- {concern_type.upper()} concern detected ({confidence:.0%}): {context}"

                    # Add consultative suggestions for buyer concerns
                    suggestions = objection.get('suggested_responses', [])
                    if suggestions:
                        enhanced_prompt += f"\n  Consultative approach: {suggestions[0]}"

            # Add preference intelligence insights for personalization
            preference_intel = intelligence_context.preference_intelligence
            if preference_intel.profile_completeness > 0.3:
                enhanced_prompt += f"\n\nBUYER PREFERENCE INTELLIGENCE:"
                enhanced_prompt += f"\n- Preference profile completeness: {preference_intel.profile_completeness:.0%}"

                # Add learned preferences for better consultation
                if hasattr(preference_intel, 'learned_preferences') and preference_intel.learned_preferences:
                    preferences = preference_intel.learned_preferences
                    enhanced_prompt += f"\n- Key preferences: {', '.join(preferences.keys())}"

            # Add market intelligence for buyer education
            enhanced_prompt += f"\n\nMARKET GUIDANCE:"
            enhanced_prompt += f"\n- Use this intelligence to provide specific, helpful property guidance"
            enhanced_prompt += f"\n- Maintain warm, friendly tone - educate and guide with care"
            enhanced_prompt += f"\n- If concerns detected, address them with understanding and helpful alternatives"

            return enhanced_prompt

        except Exception as e:
            logger.warning(f"Buyer prompt enhancement failed: {e}")
            return base_prompt

    async def _apply_buyer_conversation_intelligence(
        self,
        conversation_strategy: Dict[str, Any],
        intelligence_context: "BotIntelligenceContext",
        state: BuyerBotState
    ) -> Dict[str, Any]:
        """
        Apply conversation intelligence to refine buyer consultation strategy.

        Uses buyer-specific signals to adjust consultative approach while
        maintaining educational and supportive methodology.
        """
        try:
            conversation_intel = intelligence_context.conversation_intelligence

            # Analyze buyer concerns for consultative opportunities
            if conversation_intel.objections_detected:
                primary_concern = conversation_intel.objections_detected[0]
                concern_type = primary_concern.get('type', 'unknown')
                severity = primary_concern.get('severity', 0.5)

                logger.info(f"Jorge Buyer Bot addressing {concern_type} concern with care (severity: {severity})")

                # Buyer-specific caring responses to common concerns
                if concern_type in ['price', 'pricing', 'budget'] and severity > 0.6:
                    # Budget concern - provide gentle education with understanding
                    conversation_strategy['approach'] = 'budget_understanding_education'
                    conversation_strategy['talking_points'] = primary_concern.get('suggested_responses', [])
                elif concern_type in ['timing', 'timeline'] and severity > 0.5:
                    # Timeline concern - understand their needs patiently
                    conversation_strategy['approach'] = 'timeline_patient_guidance'
                elif concern_type in ['location', 'area']:
                    # Location concern - explore options together
                    conversation_strategy['approach'] = 'area_collaborative_exploration'

            # Adjust approach based on sentiment
            sentiment = conversation_intel.overall_sentiment
            if sentiment < -0.2:
                # Negative sentiment - provide extra care and reassurance
                conversation_strategy['tone_modifier'] = 'extra_caring_support'
            elif sentiment > 0.4:
                # Positive sentiment - opportunity for enthusiastic partnership
                conversation_strategy['tone_modifier'] = 'enthusiastic_partnership'

            # Use response recommendations for buyer education
            if conversation_intel.response_recommendations:
                best_response = conversation_intel.response_recommendations[0]
                conversation_strategy['recommended_response'] = best_response.get('response_text')
                conversation_strategy['recommended_education'] = best_response.get('education_points', [])

            conversation_strategy['intelligence_enhanced'] = True
            return conversation_strategy

        except Exception as e:
            logger.warning(f"Buyer conversation intelligence application failed: {e}")
            return conversation_strategy

    # ================================
    # FACTORY METHODS & PERFORMANCE METRICS
    # ================================

    @classmethod
    def create_enhanced_buyer_bot(cls, tenant_id: str = "jorge_buyer") -> 'JorgeBuyerBot':
        """Factory method: Create buyer bot with Phase 3.3 intelligence enhancements enabled"""
        return cls(tenant_id=tenant_id, enable_bot_intelligence=True)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for buyer bot intelligence features"""

        # Base metrics
        metrics = {
            "workflow_statistics": self.workflow_stats,
            "features_enabled": {
                "bot_intelligence": self.enable_bot_intelligence
            }
        }

        # Phase 3.3 Bot intelligence metrics
        if self.enable_bot_intelligence:
            intelligence_enhancements = self.workflow_stats["intelligence_enhancements"]
            cache_hits = self.workflow_stats["intelligence_cache_hits"]

            metrics["bot_intelligence"] = {
                "total_enhancements": intelligence_enhancements,
                "cache_hits": cache_hits,
                "cache_hit_rate": (cache_hits / max(intelligence_enhancements, 1)) * 100,
                "enhancement_rate": intelligence_enhancements / max(self.workflow_stats["total_interactions"], 1),
                "middleware_available": self.intelligence_middleware is not None
            }

            # Get middleware performance metrics if available
            if self.intelligence_middleware:
                middleware_metrics = self.intelligence_middleware.get_metrics()
                metrics["bot_intelligence"]["middleware_performance"] = {
                    "avg_latency_ms": middleware_metrics.get("avg_latency_ms", 0),
                    "performance_status": middleware_metrics.get("performance_status", "unknown"),
                    "service_failures": middleware_metrics.get("service_failures", {})
                }

        return metrics