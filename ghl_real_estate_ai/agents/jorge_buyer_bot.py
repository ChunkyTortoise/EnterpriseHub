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

This module now delegates to specialized components in the buyer/ package
while maintaining full backward compatibility with the existing API.
"""

import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

# Import from decomposed modules for backward compatibility
from ghl_real_estate_ai.agents.buyer.exceptions import (
    BuyerQualificationError,
    BuyerIntentAnalysisError,
    FinancialAssessmentError,
    ClaudeAPIError,
    NetworkError,
    ComplianceValidationError,
)
from ghl_real_estate_ai.agents.buyer.retry_utils import (
    RetryConfig,
    async_retry_with_backoff,
    DEFAULT_RETRY_CONFIG,
    RETRYABLE_EXCEPTIONS,
    NON_RETRYABLE_EXCEPTIONS,
)
from ghl_real_estate_ai.agents.buyer.constants import (
    OPT_OUT_PHRASES,
    MAX_CONVERSATION_HISTORY,
    SMS_MAX_LENGTH,
    MAX_MESSAGE_LENGTH,
)
from ghl_real_estate_ai.agents.buyer.utils import (
    extract_budget_range,
    extract_property_preferences,
    assess_financial_from_conversation,
)
from ghl_real_estate_ai.agents.buyer.financial_assessor import FinancialAssessor
from ghl_real_estate_ai.agents.buyer.property_service import PropertyService
from ghl_real_estate_ai.agents.buyer.response_generator import ResponseGenerator
from ghl_real_estate_ai.agents.buyer.handoff_manager import HandoffManager
from ghl_real_estate_ai.agents.buyer.escalation_manager import EscalationManager
from ghl_real_estate_ai.agents.buyer.state_manager import StateManager
from ghl_real_estate_ai.agents.buyer.workflow_service import BuyerWorkflowService

# Original imports
from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState
from ghl_real_estate_ai.services.buyer_persona_service import BuyerPersonaService
from ghl_real_estate_ai.services.sentiment_analysis_service import (
    SentimentAnalysisService,
)
from ghl_real_estate_ai.services.lead_scoring_integration import LeadScoringIntegration
from ghl_real_estate_ai.services.ghl_workflow_service import GHLWorkflowService
from ghl_real_estate_ai.services.churn_detection_service import ChurnDetectionService
from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import (
    BotMetadata,
    BuyerBotResponse,
    ConversationMessage,
)
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator
from ghl_real_estate_ai.agents.base_bot_workflow import BaseBotWorkflow

# Phase 3 Loop 3: Handoff context propagation
try:
    from ghl_real_estate_ai.services.jorge.jorge_handoff_service import EnrichedHandoffContext
    HANDOFF_CONTEXT_AVAILABLE = True
except ImportError:
    HANDOFF_CONTEXT_AVAILABLE = False
    EnrichedHandoffContext = None

try:
    from bots.shared.ml_analytics_engine import get_ml_analytics_engine
except ImportError:
    get_ml_analytics_engine = None

logger = get_logger(__name__)

# Phase 3.3 Bot Intelligence Middleware Integration
try:
    from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
    from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware

    BOT_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Bot Intelligence Middleware unavailable: {e}")
    BOT_INTELLIGENCE_AVAILABLE = False


class JorgeBuyerBot(BaseBotWorkflow):
    """
    Autonomous buyer bot using consultative qualification.
    Designed to identify 'Serious Buyers' and filter 'Window Shoppers'.

    Inherits from BaseBotWorkflow to share common monitoring and service patterns.

    Buyer Qualification Workflow:
    1. Analyze buyer intent and readiness signals
    2. Assess financial preparedness and budget clarity
    3. Qualify property needs and preferences
    4. Match available properties to buyer criteria
    5. Generate strategic response and education
    6. Schedule follow-up actions based on qualification level

    This class now delegates to specialized components while maintaining
    full backward compatibility with the existing API.
    """

    MAX_CONVERSATION_HISTORY = MAX_CONVERSATION_HISTORY
    SMS_MAX_LENGTH = SMS_MAX_LENGTH

    def __init__(
        self,
        tenant_id: str = "jorge_buyer",
        enable_bot_intelligence: bool = True,
        enable_handoff: bool = True,
        budget_ranges: Optional[Dict] = None,
        budget_config: Optional[BuyerBudgetConfig] = None,
        industry_config: Optional["IndustryConfig"] = None,
    ):
        # Initialize base workflow (handles industry_config, event_publisher, ml_analytics)
        super().__init__(
            tenant_id=tenant_id,
            industry_config=industry_config,
            enable_ml_analytics=bool(get_ml_analytics_engine),
        )

        # Core components (bot-specific)
        self.intent_decoder = BuyerIntentDecoder(industry_config=self.industry_config)
        self.claude = ClaudeAssistant()
        self.property_matcher = PropertyMatcher()
        self.ghl_client = GHLClient()
        self.enable_handoff = enable_handoff

        # Use provided budget config or create from environment defaults
        self.budget_config = budget_config or BuyerBudgetConfig.from_environment()

        # Use budget ranges from config if available, otherwise use provided or default
        if budget_ranges:
            self.budget_ranges = budget_ranges
        else:
            self.budget_ranges = self.budget_config.DEFAULT_BUDGET_RANGES

        # Phase 3.3 Bot Intelligence Middleware Integration
        self.enable_bot_intelligence = enable_bot_intelligence
        self.intelligence_middleware = None
        if self.enable_bot_intelligence and BOT_INTELLIGENCE_AVAILABLE:
            self.intelligence_middleware = get_bot_intelligence_middleware()
            logger.info("Jorge Buyer Bot: Bot Intelligence Middleware enabled (Phase 3.3)")
        elif self.enable_bot_intelligence:
            logger.warning("Jorge Buyer Bot: Bot Intelligence requested but dependencies not available")

        # Monitoring services (singletons — cheap to instantiate)
        self.performance_tracker = PerformanceTracker()
        self.metrics_collector = BotMetricsCollector()
        self.alerting_service = AlertingService()
        self.ab_testing = ABTestingService()
        self._init_ab_experiments()

        # Phase 1.4: Buyer Persona Classification
        self.buyer_persona_service = BuyerPersonaService()
        # Phase 1.5: Sentiment Analysis
        self.sentiment_service = SentimentAnalysisService(
            anthropic_api_key=os.getenv('ANTHROPIC_API_KEY'),
            gemini_api_key=os.getenv('GEMINI_API_KEY'),
        )
        # Phase 1.6 - 1.8 Services Initialization
        self.lead_scoring_integration = LeadScoringIntegration()
        self.workflow_service = GHLWorkflowService()
        self.churn_service = ChurnDetectionService(sentiment_service=self.sentiment_service)
        logger.info('Buyer Bot: Phase 1.5-1.8 services (Sentiment, Scoring, Workflow, Churn) initialized')

        # Performance tracking for intelligence enhancements
        self.workflow_stats = {
            "total_interactions": 0,
            "intelligence_enhancements": 0,
            "intelligence_cache_hits": 0,
        }

        # Initialize decomposed service components
        self._financial_assessor = FinancialAssessor(budget_config=self.budget_config)
        self._property_service = PropertyService(
            property_matcher=self.property_matcher,
            event_publisher=self.event_publisher,
            budget_config=self.budget_config
        )
        self._response_generator = ResponseGenerator(
            claude=self.claude,
            sentiment_service=self.sentiment_service,
            ab_testing=self.ab_testing
        )
        self._handoff_manager = HandoffManager()
        self._escalation_manager = EscalationManager(
            ghl_client=self.ghl_client,
            event_publisher=self.event_publisher
        )
        self._state_manager = StateManager(
            budget_config=self.budget_config,
            handoff_manager=self._handoff_manager
        )
        self._workflow_service = BuyerWorkflowService(
            event_publisher=self.event_publisher,
            buyer_persona_service=self.buyer_persona_service,
            ghl_client=self.ghl_client,
            budget_config=self.budget_config
        )

        self.workflow = self._build_graph()

    def _init_ab_experiments(self) -> None:
        """Create default A/B experiments if not already registered."""
        try:
            self.ab_testing.create_experiment(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                ["formal", "casual", "empathetic"],
            )
        except ValueError:
            pass  # Already exists

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(BuyerBotState)

        # Buyer Workflow with Affordability & Objection Handling
        workflow.add_node("analyze_buyer_intent", self.analyze_buyer_intent)

        # Add intelligence gathering node if enabled
        if self.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_buyer_intelligence", self.gather_buyer_intelligence)

        # Phase 1.4: Buyer Persona Classification
        workflow.add_node("classify_buyer_persona", self.classify_buyer_persona)

        workflow.add_node("generate_executive_brief", self.generate_executive_brief)

        workflow.add_node("assess_financial_readiness", self.assess_financial_readiness)
        workflow.add_node("calculate_affordability", self.calculate_affordability)
        workflow.add_node("qualify_property_needs", self.qualify_property_needs)
        workflow.add_node("match_properties", self.match_properties)
        workflow.add_node("handle_objections", self.handle_objections)
        workflow.add_node("generate_buyer_response", self.generate_buyer_response)
        workflow.add_node("schedule_next_action", self.schedule_next_action)

        # Define edges (linear with conditional routing)
        workflow.set_entry_point("analyze_buyer_intent")

        # Conditional routing for intelligence gathering
        if self.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge("analyze_buyer_intent", "gather_buyer_intelligence")
            workflow.add_edge("gather_buyer_intelligence", "classify_buyer_persona")
            workflow.add_edge("classify_buyer_persona", "assess_financial_readiness")
        else:
            workflow.add_edge("analyze_buyer_intent", "classify_buyer_persona")
            workflow.add_edge("classify_buyer_persona", "assess_financial_readiness")
        workflow.add_edge("assess_financial_readiness", "calculate_affordability")
        workflow.add_edge("calculate_affordability", "qualify_property_needs")
        workflow.add_edge("qualify_property_needs", "match_properties")

        # Routing based on qualification, objections, and property matches
        workflow.add_conditional_edges(
            "match_properties",
            self._route_after_matching,
            {
                "handle_objections": "handle_objections",
                "respond": "generate_buyer_response",
                "schedule": "schedule_next_action",
                "end": END,
            },
        )
        workflow.add_edge("handle_objections", "generate_buyer_response")

        workflow.add_edge("generate_buyer_response", "schedule_next_action")
        workflow.add_edge("schedule_next_action", "generate_executive_brief")
        workflow.add_edge("generate_executive_brief", END)

        return workflow.compile()

    def _route_buyer_action(self, state: BuyerBotState) -> Literal["respond", "schedule", "end"]:
        """Route to next action based on buyer qualification using budget_config."""
        return self._state_manager.route_buyer_action(state)

    def _route_after_matching(
        self, state: BuyerBotState
    ) -> Literal["handle_objections", "respond", "schedule", "end"]:
        """Route after property matching — check for objections first."""
        return self._state_manager.route_after_matching(state)

    async def analyze_buyer_intent(self, state: BuyerBotState) -> Dict:
        """Extract and structure buyer intent from conversation using BuyerIntentDecoder."""
        try:
            # Phase 3 Loop 3: Skip intent analysis if handoff context already populated state
            if state.get("skip_qualification") and state.get("handoff_context_used"):
                logger.info(f"Skipping intent analysis for {state.get('buyer_id')} - using handoff context")
                # Return existing state values
                return {
                    "intent_profile": state.get("intent_profile"),
                    "budget_range": state.get("budget_range"),
                    "urgency_score": state.get("urgency_score", 70),
                    "buying_motivation_score": state.get("buying_motivation_score", 70),
                    "preference_clarity": 0.8,  # High since came from qualified lead
                    "current_qualification_step": state.get("current_qualification_step", "property_matching"),
                }

            conversation_history = state.get("conversation_history", [])
            buyer_id = state.get("buyer_id", "unknown")

            # Use intent decoder to analyze buyer (returns BuyerIntentProfile)
            profile = self.intent_decoder.analyze_buyer(
                buyer_id=buyer_id,
                conversation_history=conversation_history,
            )

            # Extract key signals from BuyerIntentProfile model
            urgency_score = profile.urgency_score
            preference_clarity = profile.preference_clarity
            buying_motivation = (profile.financial_readiness + profile.urgency_score) / 2

            # Try to extract budget range from conversation
            budget_range = await extract_budget_range(conversation_history, self.budget_config)

            # Phase 1.6: Calculate Composite Lead Score
            composite_score_data = {}
            try:
                scoring_state = {
                    "financial_readiness": profile.financial_readiness,
                    "urgency_score": profile.urgency_score,
                    "conversation_history": conversation_history,
                    "buyer_persona": state.get("buyer_persona")
                }
                
                scoring_result = await self.lead_scoring_integration.calculate_and_store_composite_score(
                    state=scoring_state,
                    contact_id=buyer_id,
                    use_ml_ensemble=self.ml_analytics is not None
                )
                composite_score_data = scoring_result.get("composite_score_data", {})
                logger.info(f"Composite score calculated for buyer {buyer_id}: {composite_score_data.get('total_score', 0)}")
            except Exception as e:
                logger.error(f"Failed to calculate composite score for buyer: {e}")

            return {
                "intent_profile": profile,
                "budget_range": budget_range,
                "urgency_score": urgency_score,
                "buying_motivation_score": buying_motivation,
                "preference_clarity": preference_clarity,
                "current_qualification_step": profile.next_qualification_step,
                "composite_score": composite_score_data,
            }
        except Exception as e:
            logger.error(f"Error analyzing buyer intent for {state.get('buyer_id')}: {str(e)}")
            return {
                "intent_profile": None,
                "budget_range": None,
                "urgency_score": 25,
                "buying_motivation_score": 25,
                "preference_clarity": 0.5,
                "current_qualification_step": "error",
            }

    async def gather_buyer_intelligence(self, state: BuyerBotState) -> Dict:
        """Gather buyer intelligence using Bot Intelligence Middleware (Phase 3.3)."""
        try:
            intelligence_context = None
            performance_ms = 0.0

            if self.intelligence_middleware:
                start_time = time.time()

                intelligence_context = await self.intelligence_middleware.gather_intelligence(
                    conversation_history=state.get("conversation_history", []),
                    contact_id=state.get("buyer_id"),
                    intelligence_types=[
                        "conversation_intelligence",
                        "preference_intelligence",
                        "property_intelligence",
                    ],
                )

                performance_ms = (time.time() - start_time) * 1000
                self.workflow_stats["intelligence_enhancements"] += 1

            return {"intelligence_context": intelligence_context, "intelligence_performance_ms": performance_ms}
        except Exception as e:
            logger.warning(f"Buyer intelligence gathering failed: {e}")
            return {"intelligence_context": None, "intelligence_performance_ms": 0.0}

    async def assess_financial_readiness(self, state: BuyerBotState) -> Dict:
        """Assess buyer's financial preparedness using budget_config thresholds."""
        return await self._financial_assessor.assess_financial_readiness(
            state,
            skip_qualification=state.get("skip_qualification", False)
        )

    async def calculate_affordability(self, state: BuyerBotState) -> Dict:
        """Calculate affordability analysis from buyer's budget range."""
        return await self._financial_assessor.calculate_affordability(state)

    async def qualify_property_needs(self, state: BuyerBotState) -> Dict:
        """Qualify property needs and preferences using budget_config urgency thresholds."""
        return await self._property_service.qualify_property_needs(state)

    async def match_properties(self, state: BuyerBotState) -> Dict:
        """
        Match properties to buyer preferences using existing PropertyMatcher.
        Uses find_buyer_matches when budget is available for better filtering.
        """
        return await self._property_service.match_properties(state)

    async def handle_objections(self, state: BuyerBotState) -> Dict:
        """Handle detected buyer objections with appropriate strategies."""
        return await self._response_generator.handle_objections(state)

    async def generate_buyer_response(self, state: BuyerBotState) -> Dict:
        """
        Generate strategic buyer response based on qualification and property matches.
        Enhanced with Phase 3.3 intelligence context for consultative recommendations.
        """
        return await self._response_generator.generate_buyer_response(state)

    async def schedule_next_action(self, state: BuyerBotState) -> Dict:
        """
        Schedule next action based on buyer qualification level and engagement.
        Follows proven lead nurturing sequences.
        Uses budget_config for qualification thresholds.
        """
        return await self._workflow_service.schedule_next_action(state)

    # ================================
    # ERROR HANDLING & ESCALATION METHODS (Delegated)
    # ================================

    async def escalate_to_human_review(self, buyer_id: str, reason: str, context: Dict) -> Dict:
        """
        Escalate buyer conversation to human agent review.
        Delegates to EscalationManager.
        """
        return await self._escalation_manager.escalate_to_human_review(buyer_id, reason, context)

    async def escalate_compliance_violation(self, buyer_id: str, violation_type: str, evidence: Dict) -> Dict:
        """
        Handle compliance violation detection and escalation.
        Delegates to EscalationManager.
        """
        return await self._escalation_manager.escalate_compliance_violation(buyer_id, violation_type, evidence)

    # ================================
    # FALLBACK METHODS (Delegated)
    # ================================

    async def _fallback_financial_assessment(self, state: BuyerBotState) -> Dict:
        """
        Multi-tier fallback for financial assessment when primary service fails.
        Delegates to FinancialAssessor.
        """
        return await self._financial_assessor.fallback_financial_assessment(state)

    def _assess_financial_from_conversation(self, conversation_text: str) -> Optional[Dict]:
        """Extract financial signals from conversation text."""
        return assess_financial_from_conversation(conversation_text)

    # ================================
    # EXTRACTION HELPERS (Delegated)
    # ================================

    async def _extract_budget_range(self, conversation_history: List[Dict]) -> Optional[Dict[str, int]]:
        """Extract budget range from conversation history."""
        return await extract_budget_range(conversation_history, self.budget_config)

    async def _extract_property_preferences(self, conversation_history: List[ConversationMessage]) -> Optional[Dict[str, Any]]:
        """Extract property preferences from conversation history."""
        return await extract_property_preferences(conversation_history)

    async def _schedule_follow_up(self, buyer_id: str, action: str, hours: int):
        """Schedule follow-up action for buyer."""
        await self._workflow_service._schedule_follow_up(buyer_id, action, hours)

    # ================================
    # HANDOFF CONTEXT HELPERS (Delegated)
    # ================================

    def _has_valid_handoff_context(self, handoff_context: Optional["EnrichedHandoffContext"]) -> bool:
        """Check if handoff context is valid and recent (<24h)."""
        return self._handoff_manager.has_valid_handoff_context(handoff_context)

    def _populate_state_from_context(
        self,
        handoff_context: "EnrichedHandoffContext",
        initial_state: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Populate buyer state from handoff context to skip re-qualification."""
        return self._handoff_manager.populate_state_from_context(handoff_context, initial_state)

    # ================================
    # MAIN ENTRY POINT
    # ================================

    async def process_buyer_conversation(
        self,
        conversation_id: str,
        user_message: str,
        buyer_name: Optional[str] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        buyer_phone: Optional[str] = None,
        buyer_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
        handoff_context: Optional["EnrichedHandoffContext"] = None,
    ) -> BuyerBotResponse:
        """
        Main entry point for processing buyer conversations.

        Args:
            conversation_id: Unique identifier for the conversation
            user_message: The incoming message from the buyer
            buyer_name: Optional name of the buyer
            conversation_history: Optional list of previous messages
            buyer_phone: Optional phone number for SMS follow-ups
            buyer_email: Optional email for email follow-ups
            metadata: Optional additional metadata

        Returns:
            Dict containing:
                - response_content: Bot's response message
                - lead_id: The conversation/buyer identifier
                - current_step: Current qualification step
                - engagement_status: Current engagement state
                - financial_readiness: Financial readiness score
                - handoff_signals: Signals for cross-bot handoff
        """
        # Input validation
        if not conversation_id or not str(conversation_id).strip():
            raise ValueError("conversation_id must be a non-empty string")
        if not user_message or not str(user_message).strip():
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "response_content": "I didn't catch that. Could you say more?",
                "current_step": "awaiting_input",
                "engagement_status": "active",
                "financial_readiness": 0.0,
                "handoff_signals": {},
            }
        user_message = str(user_message).strip()[:MAX_MESSAGE_LENGTH]

        # TCPA opt-out check — must run BEFORE any AI processing
        msg_lower = user_message.lower().strip()
        if any(phrase in msg_lower for phrase in OPT_OUT_PHRASES):
            logger.info(f"Opt-out detected for buyer {conversation_id}")
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "response_content": (
                    "You've been unsubscribed from automated messages. "
                    "If you'd like to reconnect, just text us anytime."
                ),
                "opt_out_detected": True,
                "actions": [{"type": "add_tag", "tag": "AI-Off"}],
                "buyer_temperature": "unknown",
                "current_step": "opt_out",
                "engagement_status": "opted_out",
                "financial_readiness": 0.0,
                "handoff_signals": {},
            }

        try:
            _workflow_start = time.time()

            # Get A/B test variant for response tone (before workflow)
            try:
                _tone_variant = await self.ab_testing.get_variant(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT, conversation_id
                )
            except (KeyError, ValueError):
                _tone_variant = "empathetic"

            # Build initial state using StateManager
            initial_state = self._state_manager.build_initial_state(
                conversation_id=conversation_id,
                user_message=user_message,
                conversation_history=conversation_history,
                buyer_name=buyer_name,
                buyer_phone=buyer_phone,
                buyer_email=buyer_email,
                metadata=metadata,
                tone_variant=_tone_variant,
                handoff_context=handoff_context
            )

            result = await self.workflow.ainvoke(initial_state)

            _workflow_duration_ms = (time.time() - _workflow_start) * 1000
            self.workflow_stats["total_interactions"] += 1

            # Determine qualification status
            qualification_status = self._state_manager.determine_qualification_status(result)
            result.update(qualification_status)
            result["lead_id"] = conversation_id

            # Extract handoff signals
            handoff_signals = {}
            if self.enable_handoff:
                from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
                handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            result["handoff_signals"] = handoff_signals

            # SMS length guard
            response_truncation = self._state_manager.truncate_response_if_needed(
                result.get("response_content", ""),
                self.SMS_MAX_LENGTH
            )
            result.update(response_truncation)

            # Record performance metrics
            await self.performance_tracker.track_operation("buyer_bot", "process", _workflow_duration_ms, success=True)
            self.metrics_collector.record_bot_interaction("buyer", duration_ms=_workflow_duration_ms, success=True)

            # Feed metrics to alerting (non-blocking)
            try:
                self.metrics_collector.feed_to_alerting(self.alerting_service)
            except Exception as e:
                logger.debug(f"Failed to feed metrics to alerting: {str(e)}")

            # Record A/B test outcome (reuse variant from pre-workflow assignment)
            try:
                await self.ab_testing.record_outcome(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    conversation_id,
                    _tone_variant,
                    "response",
                )
            except (KeyError, ValueError):
                pass

            # Tag response with A/B experiment metadata
            result["ab_test"] = {
                "experiment_id": ABTestingService.RESPONSE_TONE_EXPERIMENT,
                "variant": _tone_variant,
            }

            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-buyer",
                contact_id=conversation_id,
                status="completed",
                current_step=result.get("current_qualification_step", "unknown"),
            )

            await self.event_publisher.publish_buyer_qualification_complete(
                contact_id=conversation_id,
                qualification_status="qualified" if qualification_status["is_qualified"] else "needs_nurturing",
                final_score=(result.get("financial_readiness_score", 0) + result.get("buying_motivation_score", 0)) / 2,
                properties_matched=len(result.get("matched_properties", [])),
            )

            # Phase 1.7: GHL Workflow Integration (Auto-tagging & Pipeline)
            try:
                # Prepare data for workflow service
                scores = {
                    "frs": result.get("financial_readiness_score", 0.0),
                    "pcs": result.get("buying_motivation_score", 0.0),
                    "composite": result.get("composite_score", {}).get("total_score", 0.0)
                }
                
                # Get sentiment result if available
                sentiment_val = None
                if result.get("sentiment_result"):
                    sentiment_val = result["sentiment_result"].sentiment.value

                # Apply tag rules
                await self.workflow_service.apply_tag_rules(
                    contact_id=conversation_id,
                    scores=scores,
                    persona=result.get("buyer_persona"),
                    sentiment=sentiment_val,
                    escalation=result.get("sentiment_escalation") is not None,
                    appointment_booked=result.get("current_qualification_step") == "appointment"
                )
                logger.info(f"Applied GHL workflow tags for buyer {conversation_id}")
                
            except Exception as e:
                logger.warning(f"Failed to execute GHL workflow operations for buyer: {e}")

            # Phase 1.8: Churn Detection Integration
            churn_assessment = None
            try:
                # Assess churn risk
                last_activity = datetime.now(timezone.utc)
                churn_assessment = await self.churn_service.assess_churn_risk(
                    contact_id=conversation_id,
                    conversation_history=initial_state.get("conversation_history", []),
                    last_activity=last_activity
                )
                result["churn_assessment"] = {
                    "risk_score": churn_assessment.risk_score,
                    "risk_level": churn_assessment.risk_level.value,
                    "recommended_action": churn_assessment.recommended_action.value
                }
                logger.info(f"Churn risk assessed for buyer {conversation_id}: {churn_assessment.risk_level}")
            except Exception as e:
                logger.warning(f"Failed to assess churn risk for buyer: {e}")

            return result

        except Exception as e:
            # Record failure metrics
            try:
                _fail_duration = (time.time() - _workflow_start) * 1000
                await self.performance_tracker.track_operation("buyer_bot", "process", _fail_duration, success=False)
                self.metrics_collector.record_bot_interaction("buyer", duration_ms=_fail_duration, success=False)
            except Exception as ex:
                logger.debug(f"Secondary failure in error metrics recording: {str(ex)}")

            logger.error(f"Error processing buyer conversation for {conversation_id}: {str(e)}")
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "error": str(e),
                "response_content": "I'm having technical difficulties. Let me connect you with Jorge directly.",
                "current_step": "error",
                "engagement_status": "error",
                "financial_readiness": 0.0,
                "handoff_signals": {},
            }

    # ================================
    # PHASE 3.3 INTELLIGENCE ENHANCEMENT METHODS
    # ================================

    async def _enhance_buyer_prompt_with_intelligence(
        self, base_prompt: str, intelligence_context: "BotIntelligenceContext", state: BuyerBotState
    ) -> str:
        """
        Enhance Claude prompt with buyer intelligence context for consultative responses.
        Delegates to ResponseGenerator.
        """
        return self._response_generator._enhance_buyer_prompt_with_intelligence(
            base_prompt, intelligence_context, state
        )

    async def _apply_buyer_conversation_intelligence(
        self,
        conversation_strategy: Dict[str, Any],
        intelligence_context: "BotIntelligenceContext",
        state: BuyerBotState,
    ) -> Dict[str, Any]:
        """
        Apply conversation intelligence to refine buyer consultation strategy.
        """
        try:
            conversation_intel = intelligence_context.conversation_intelligence

            # Analyze buyer concerns for consultative opportunities
            if conversation_intel.objections_detected:
                primary_concern = conversation_intel.objections_detected[0]
                concern_type = primary_concern.get("type", "unknown")
                severity = primary_concern.get("severity", 0.5)

                logger.info(f"Jorge Buyer Bot addressing {concern_type} concern with care (severity: {severity})")

                # Buyer-specific caring responses to common concerns
                if concern_type in ["price", "pricing", "budget"] and severity > 0.6:
                    # Budget concern - provide gentle education with understanding
                    conversation_strategy["approach"] = "budget_understanding_education"
                    conversation_strategy["talking_points"] = primary_concern.get("suggested_responses", [])
                elif concern_type in ["timing", "timeline"] and severity > 0.5:
                    # Timeline concern - understand their needs patiently
                    conversation_strategy["approach"] = "timeline_patient_guidance"
                elif concern_type in ["location", "area"]:
                    # Location concern - explore options together
                    conversation_strategy["approach"] = "area_collaborative_exploration"

            # Adjust approach based on sentiment
            sentiment = conversation_intel.overall_sentiment
            if sentiment < -0.2:
                # Negative sentiment - provide extra care and reassurance
                conversation_strategy["tone_modifier"] = "extra_caring_support"
            elif sentiment > 0.4:
                # Positive sentiment - opportunity for enthusiastic partnership
                conversation_strategy["tone_modifier"] = "enthusiastic_partnership"

            # Use response recommendations for buyer education
            if conversation_intel.response_recommendations:
                best_response = conversation_intel.response_recommendations[0]
                conversation_strategy["recommended_response"] = best_response.get("response_text")
                conversation_strategy["recommended_education"] = best_response.get("education_points", [])

            conversation_strategy["intelligence_enhanced"] = True
            return conversation_strategy

        except Exception as e:
            logger.warning(f"Buyer conversation intelligence application failed: {e}")
            return conversation_strategy

    # ================================
    # FACTORY METHODS & PERFORMANCE METRICS
    # ================================

    @classmethod
    def create_enhanced_buyer_bot(cls, tenant_id: str = "jorge_buyer") -> "JorgeBuyerBot":
        """Factory method: Create buyer bot with Phase 3.3 intelligence enhancements enabled"""
        return cls(tenant_id=tenant_id, enable_bot_intelligence=True)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for buyer bot intelligence features"""

        # Base metrics
        metrics = {
            "workflow_statistics": self.workflow_stats,
            "features_enabled": {"bot_intelligence": self.enable_bot_intelligence},
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
                "middleware_available": self.intelligence_middleware is not None,
            }

            # Get middleware performance metrics if available
            if self.intelligence_middleware:
                middleware_metrics = self.intelligence_middleware.get_metrics()
                metrics["bot_intelligence"]["middleware_performance"] = {
                    "avg_latency_ms": middleware_metrics.get("avg_latency_ms", 0),
                    "performance_status": middleware_metrics.get("performance_status", "unknown"),
                    "service_failures": middleware_metrics.get("service_failures", {}),
                }

        return metrics

    # ================================
    # PHASE 1.4: BUYER PERSONA CLASSIFICATION (Delegated)
    # ================================

    async def classify_buyer_persona(self, state: BuyerBotState) -> Dict:
        """Classify buyer persona based on conversation analysis (Phase 1.4)."""
        return await self._workflow_service.classify_buyer_persona(state)

    async def _sync_buyer_persona_to_ghl(
        self, buyer_id: str, persona_classification
    ) -> None:
        """Sync buyer persona to GHL as tags (Phase 1.4)."""
        await self._workflow_service._sync_buyer_persona_to_ghl(buyer_id, persona_classification)

    # ================================
    # EXECUTIVE BRIEF GENERATION (Phase 2)
    # ================================

    async def generate_executive_brief(self, state: BuyerBotState) -> Dict:
        """
        Generate a structured executive brief for human agents when a lead is highly qualified.
        Uses Claude Orchestrator with task type EXECUTIVE_BRIEFING.
        """
        buyer_id = state.get("buyer_id", "unknown")
        composite_score = state.get("composite_score", {}).get("total_score", 0.0)

        # Only generate brief for high-quality leads (Score > 80)
        if composite_score < 80:
            return {"executive_brief_generated": False}

        try:
            orchestrator = get_claude_orchestrator()
            
            # Prepare context for the brief
            context = {
                "lead_id": buyer_id,
                "bot_type": "buyer",
                "persona": state.get("buyer_persona"),
                "scores": {
                    "composite": composite_score,
                    "financial": state.get("financial_readiness_score"),
                    "urgency": state.get("urgency_score")
                },
                "preferences": state.get("property_preferences"),
                "conversation_history": state.get("conversation_history", [])[-10:]  # Last 10 turns
            }

            # Import here to avoid circular dependency
            from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType
            
            # Generate brief via Orchestrator
            brief_response = await orchestrator.process_request(
                ClaudeRequest(
                    task_type=ClaudeTaskType.EXECUTIVE_BRIEFING,
                    context=context,
                    prompt=f"Generate a one-page executive brief for Jorge regarding buyer {buyer_id}. Highlight key needs and recommended next steps."
                )
            )

            brief_content = brief_response.content

            # Sync brief to GHL as a note
            await self.ghl_client.add_contact_note(
                contact_id=buyer_id,
                body=f"--- EXECUTIVE BRIEF ---\n{brief_content}"
            )

            logger.info(f"Executive brief generated and synced for buyer {buyer_id}")

            return {
                "executive_brief": brief_content,
                "executive_brief_generated": True,
                "current_qualification_step": "handoff_ready"
            }

        except Exception as e:
            logger.error(f"Error generating executive brief for {buyer_id}: {e}")
            return {"executive_brief_generated": False}


# Re-export exceptions and utilities for backward compatibility
__all__ = [
    "JorgeBuyerBot",
    "BuyerQualificationError",
    "BuyerIntentAnalysisError",
    "FinancialAssessmentError",
    "ClaudeAPIError",
    "NetworkError",
    "ComplianceValidationError",
    "RetryConfig",
    "async_retry_with_backoff",
    "DEFAULT_RETRY_CONFIG",
    "RETRYABLE_EXCEPTIONS",
    "NON_RETRYABLE_EXCEPTIONS",
]
