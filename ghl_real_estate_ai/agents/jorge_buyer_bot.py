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
import inspect
import random
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.agents.buyer_intent_decoder import BuyerIntentDecoder
from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState


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

# TCPA opt-out phrases — mirrors webhook.py for consistent compliance handling
OPT_OUT_PHRASES = ["stop", "unsubscribe", "not interested", "opt out", "remove me", "cancel"]
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import (
    BotMetadata,
    BuyerBotResponse,
    ConversationMessage,
)
from ghl_real_estate_ai.services.compliance_guard import ComplianceStatus, compliance_guard
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.ghl_client import GHLClient
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.property_matcher import PropertyMatcher

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


# ================================
# RETRY MECHANISM WITH EXPONENTIAL BACKOFF
# ================================


class RetryConfig:
    """Configuration for retry behavior."""

    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 500,
        exponential_base: float = 2.0,
        jitter_factor: float = 0.1,
    ):
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.exponential_base = exponential_base
        self.jitter_factor = jitter_factor


DEFAULT_RETRY_CONFIG = RetryConfig()

RETRYABLE_EXCEPTIONS = (ClaudeAPIError, NetworkError)
NON_RETRYABLE_EXCEPTIONS = (BuyerIntentAnalysisError, ComplianceValidationError)


async def async_retry_with_backoff(coro_factory, retry_config: RetryConfig = None, context_label: str = "operation"):
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
                backoff_ms = config.initial_backoff_ms * (config.exponential_base**attempt)
                jitter = backoff_ms * config.jitter_factor * (2 * random.random() - 1)
                sleep_seconds = (backoff_ms + jitter) / 1000.0
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_retries} for {context_label}: {e}. "
                    f"Backing off {sleep_seconds:.3f}s"
                )
                await asyncio.sleep(sleep_seconds)
            else:
                logger.error(f"All {config.max_retries} retries exhausted for {context_label}: {e}")
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

    MAX_CONVERSATION_HISTORY = 50
    SMS_MAX_LENGTH = 160

    def __init__(
        self,
        tenant_id: str = "jorge_buyer",
        enable_bot_intelligence: bool = True,
        enable_handoff: bool = True,
        budget_ranges: Optional[Dict] = None,
        budget_config: Optional[BuyerBudgetConfig] = None,
        industry_config: Optional["IndustryConfig"] = None,
    ):
        # Industry-agnostic configuration layer (backward compatible)
        from ghl_real_estate_ai.config.industry_config import IndustryConfig

        self.industry_config: IndustryConfig = industry_config or IndustryConfig.default_real_estate()

        self.intent_decoder = BuyerIntentDecoder(industry_config=self.industry_config)
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
        self.property_matcher = PropertyMatcher()
        self.ml_analytics = get_ml_analytics_engine(tenant_id) if get_ml_analytics_engine else None
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

        # Performance tracking for intelligence enhancements
        self.workflow_stats = {
            "total_interactions": 0,
            "intelligence_enhancements": 0,
            "intelligence_cache_hits": 0,
        }

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

    def _sanitize_sms_response(self, message: Optional[str]) -> str:
        """Normalize buyer outbound text to consultative, SMS-safe format."""
        sanitized = compliance_guard.sanitize_for_sms(message or "", max_length=self.SMS_MAX_LENGTH)
        if sanitized:
            return sanitized
        return compliance_guard.get_safe_fallback_message(mode="buyer", max_length=self.SMS_MAX_LENGTH)

    def _extract_latest_user_message(self, conversation_history: List[ConversationMessage]) -> Optional[str]:
        """Get the most recent non-empty user message from conversation history."""
        for message in reversed(conversation_history):
            if str(message.get("role", "")).lower() != "user":
                continue
            content = str(message.get("content", "") or message.get("message", "")).strip()
            if content:
                return content
        return None

    async def _await_if_needed(self, maybe_awaitable: Any) -> Any:
        """Await coroutine values while allowing synchronous mocks in tests."""
        if inspect.isawaitable(maybe_awaitable):
            return await maybe_awaitable
        return maybe_awaitable

    async def _apply_outbound_compliance(self, message: str, buyer_id: str) -> Dict[str, Any]:
        """
        Apply compliance audit and return safe fallback when content is blocked/flagged.
        """
        status, reason, violations = await compliance_guard.audit_message(
            message, contact_context={"contact_id": buyer_id, "mode": "buyer"}
        )
        payload = {
            "response_content": self._sanitize_sms_response(message),
            "compliance_status": status.value,
            "compliance_reason": reason,
            "compliance_violations": violations,
            "compliance_fallback_applied": False,
        }

        if status in {ComplianceStatus.BLOCKED, ComplianceStatus.FLAGGED}:
            payload["response_content"] = compliance_guard.get_safe_fallback_message(
                mode="buyer", max_length=self.SMS_MAX_LENGTH
            )
            payload["compliance_fallback_applied"] = True

        return payload

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(BuyerBotState)

        # Buyer Workflow with Affordability & Objection Handling
        workflow.add_node("analyze_buyer_intent", self.analyze_buyer_intent)

        # Add intelligence gathering node if enabled
        if self.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_buyer_intelligence", self.gather_buyer_intelligence)

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
            workflow.add_edge("gather_buyer_intelligence", "assess_financial_readiness")
        else:
            workflow.add_edge("analyze_buyer_intent", "assess_financial_readiness")
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
        workflow.add_edge("schedule_next_action", END)

        return workflow.compile()

    def _route_buyer_action(self, state: BuyerBotState) -> Literal["respond", "schedule", "end"]:
        """Route to next action based on buyer qualification using budget_config."""
        try:
            next_action = state.get("next_action", "respond")
            qualification_score = state.get("financial_readiness_score", 0)

            # Use budget_config for routing thresholds
            return self.budget_config.get_routing_action(qualification_score, next_action)
        except Exception as e:
            logger.error(f"Error routing buyer action: {str(e)}")
            return "respond"

    def _route_after_matching(
        self, state: BuyerBotState
    ) -> Literal["handle_objections", "respond", "schedule", "end"]:
        """Route after property matching — check for objections first."""
        if state.get("objection_detected"):
            return "handle_objections"
        return self._route_buyer_action(state)

    async def analyze_buyer_intent(self, state: BuyerBotState) -> Dict:
        """Extract and structure buyer intent from conversation using BuyerIntentDecoder."""
        try:
            conversation_history = state.get("conversation_history", [])
            buyer_id = state.get("buyer_id", "unknown")

            # Use intent decoder to analyze buyer (returns BuyerIntentProfile)
            profile = self.intent_decoder.analyze_buyer(buyer_id, conversation_history)

            # Extract key signals from BuyerIntentProfile model
            urgency_score = profile.urgency_score
            preference_clarity = profile.preference_clarity
            buying_motivation = profile.urgency_score

            # Try to extract budget range from conversation
            budget_range = await self._extract_budget_range(conversation_history)

            # Emit analytics event (tests may provide an AsyncMock here)
            publish_intent = getattr(self.event_publisher, "publish_buyer_intent_analysis", None)
            if publish_intent:
                await self._await_if_needed(
                    publish_intent(
                        contact_id=buyer_id,
                        buyer_temperature=profile.buyer_temperature,
                        financial_readiness=profile.financial_readiness,
                        urgency_score=profile.urgency_score,
                    )
                )

            return {
                "intent_profile": profile,
                "budget_range": budget_range,
                "urgency_score": urgency_score,
                "buying_motivation_score": buying_motivation,
                "financial_readiness_score": profile.financial_readiness,
                "preference_clarity": preference_clarity,
                "current_qualification_step": profile.next_qualification_step,
                "buyer_temperature": profile.buyer_temperature,
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
                import time

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
        try:
            profile = state.get("intent_profile", {})
            budget_range = state.get("budget_range")
            intelligence_context = state.get("intelligence_context")

            def profile_get(key: str, default: Any = None) -> Any:
                if isinstance(profile, dict):
                    return profile.get(key, default)
                return getattr(profile, key, default)

            # Check budget ranges first
            if not budget_range:
                # Try to extract from conversation
                extracted = await self._extract_budget_range(state.get("conversation_history", []))
                if extracted:
                    budget_range = extracted

            # Use profile for additional signals
            financing_status = profile_get("financing_status")
            if not financing_status:
                financing_status_score = float(profile_get("financing_status_score", 0) or 0)
                if financing_status_score >= 75:
                    financing_status = "pre_approved"
                elif financing_status_score >= 55:
                    financing_status = "needs_approval"
                else:
                    financing_status = "unknown"

            urgency_score = state.get("urgency_score", profile_get("urgency_score", 25))
            financial_readiness = float(profile_get("financial_readiness", 0) or 0)

            # Apply thresholds from budget_config
            if financing_status == "pre_approved":
                score = self.budget_config.FINANCING_PRE_APPROVED_THRESHOLD
            elif financing_status == "cash":
                score = self.budget_config.FINANCING_CASH_BUDGET_THRESHOLD
            elif financing_status == "needs_approval":
                score = self.budget_config.FINANCING_NEEDS_APPROVAL_THRESHOLD
            else:
                # Default based on budget clarity and urgency
                score = financial_readiness or min(100, urgency_score + (50 if budget_range else 0))

            # Apply Phase 3.3 intelligence enhancements if available
            if intelligence_context:
                intelligence_context = await self._apply_buyer_conversation_intelligence(
                    {"approach": "standard"}, intelligence_context, state
                )

            return {
                "budget_range": budget_range,
                "financing_status": financing_status,
                "financial_readiness_score": min(100, financial_readiness or score),
                "current_qualification_step": "property",
            }
        except Exception as e:
            logger.error(f"Error assessing financial readiness for {state['buyer_id']}: {str(e)}")
            return {
                "budget_range": None,
                "financing_status": "assessment_error",
                "financial_readiness_score": 25,
                "current_qualification_step": "error",
            }

    async def calculate_affordability(self, state: BuyerBotState) -> Dict:
        """Calculate affordability analysis from buyer's budget range."""
        budget_range = state.get("budget_range")
        if not budget_range:
            return {}

        try:
            max_price = budget_range.get("max", 0)
            if max_price <= 0:
                return {}

            # Standard mortgage calculations (Rancho Cucamonga rates)
            down_payment_pct = 0.20
            interest_rate = 0.0685  # Current 30-yr fixed rate
            loan_term_years = 30
            property_tax_rate = 0.0115  # California / San Bernardino County
            insurance_annual = 1800  # Average annual homeowner's insurance

            down_payment = max_price * down_payment_pct
            loan_amount = max_price - down_payment

            # Monthly mortgage (standard amortization formula)
            monthly_rate = interest_rate / 12
            num_payments = loan_term_years * 12
            if monthly_rate > 0:
                monthly_mortgage = loan_amount * (
                    monthly_rate * (1 + monthly_rate) ** num_payments
                ) / ((1 + monthly_rate) ** num_payments - 1)
            else:
                monthly_mortgage = loan_amount / num_payments

            monthly_tax = (max_price * property_tax_rate) / 12
            monthly_insurance = insurance_annual / 12
            total_monthly = monthly_mortgage + monthly_tax + monthly_insurance

            affordability_analysis = {
                "max_price": max_price,
                "down_payment": round(down_payment, 2),
                "loan_amount": round(loan_amount, 2),
                "monthly_mortgage": round(monthly_mortgage, 2),
                "monthly_tax": round(monthly_tax, 2),
                "monthly_insurance": round(monthly_insurance, 2),
                "total_monthly_payment": round(total_monthly, 2),
            }

            mortgage_details = {
                "rate": interest_rate,
                "term_years": loan_term_years,
                "type": "30-year fixed",
                "down_payment_pct": down_payment_pct,
            }

            return {
                "affordability_analysis": affordability_analysis,
                "mortgage_details": mortgage_details,
                "max_monthly_payment": round(total_monthly, 2),
            }

        except Exception as e:
            logger.error(f"Error calculating affordability: {str(e)}")
            return {}

    async def qualify_property_needs(self, state: BuyerBotState) -> Dict:
        """Qualify property needs and preferences using budget_config urgency thresholds."""
        try:
            profile = state.get("intent_profile")
            if not profile:
                return {"property_preferences": None, "urgency_level": "browsing"}

            def profile_get(key: str, default: Any = None) -> Any:
                if isinstance(profile, dict):
                    return profile.get(key, default)
                return getattr(profile, key, default)

            # Extract property preferences from conversation
            preferences = await self._extract_property_preferences(state["conversation_history"])

            # Determine urgency level using budget_config
            urgency_score = float(state.get("urgency_score", profile_get("urgency_score", 0)))
            urgency_level = self.budget_config.get_urgency_level(urgency_score)

            return {
                "property_preferences": preferences,
                "urgency_level": urgency_level,
                "preference_clarity_score": state.get("preference_clarity", profile_get("preference_clarity", 0.5)),
            }

        except Exception as e:
            logger.error(f"Error qualifying property needs for {state['buyer_id']}: {str(e)}")
            return {"property_preferences": None, "urgency_level": "browsing"}

    async def match_properties(self, state: BuyerBotState) -> Dict:
        """
        Match properties to buyer preferences using existing PropertyMatcher.
        Uses find_buyer_matches when budget is available for better filtering.
        """
        try:
            if not state.get("budget_range"):
                return {"matched_properties": [], "properties_viewed_count": 0, "next_action": "qualify_more"}

            budget_range = state["budget_range"]
            preferences = state.get("property_preferences") or {}
            budget_max = budget_range.get("max")
            budget_min = budget_range.get("min")

            enriched_preferences = dict(preferences)
            if isinstance(budget_max, (int, float)) and budget_max > 0:
                enriched_preferences["budget_max"] = budget_max
            if isinstance(budget_min, (int, float)) and budget_min >= 0:
                enriched_preferences["budget_min"] = budget_min

            if hasattr(self.property_matcher, "find_matches"):
                if inspect.iscoroutinefunction(self.property_matcher.find_matches):
                    matches = await self.property_matcher.find_matches(preferences=preferences, limit=5)
                else:
                    matches = self.property_matcher.find_matches(preferences=preferences, limit=5)
            elif hasattr(self.property_matcher, "find_buyer_matches") and budget_max:
                beds = preferences.get("bedrooms")
                neighborhood = preferences.get("neighborhood")
                if inspect.iscoroutinefunction(self.property_matcher.find_buyer_matches):
                    matches = await self.property_matcher.find_buyer_matches(
                        budget=budget_max, beds=beds, neighborhood=neighborhood, limit=5
                    )
                else:
                    matches = self.property_matcher.find_buyer_matches(
                        budget=budget_max, beds=beds, neighborhood=neighborhood, limit=5
                    )
            else:
                matches = []

            # Emit property match event
            await self.event_publisher.publish_property_match_update(
                contact_id=state["buyer_id"],
                properties_matched=len(matches),
                match_criteria=enriched_preferences,
            )

            return {
                "matched_properties": matches[:5],  # Top 5 matches
                "property_matches": matches[:5],  # Add for consistency with script expectation
                "properties_viewed_count": len(matches),
                "next_action": "respond" if matches else "educate_market",
            }

        except Exception as e:
            logger.error(f"Error matching properties for {state['buyer_id']}: {str(e)}")
            return {"matched_properties": [], "properties_viewed_count": 0, "next_action": "qualify_more"}

    async def handle_objections(self, state: BuyerBotState) -> Dict:
        """Handle detected buyer objections with appropriate strategies."""
        objection_type = state.get("detected_objection_type")
        if not objection_type:
            return {}

        objection_strategies = {
            "budget_shock": {
                "approach": "Show affordable alternatives and financing options",
                "talking_points": [
                    "There are great neighborhoods with homes in your range",
                    "Let's explore areas that give you the best value",
                ],
            },
            "analysis_paralysis": {
                "approach": "Narrow focus and create urgency with market data",
                "talking_points": [
                    "Based on what you've told me, I'd focus on these top 3 options",
                    "Properties in this range are moving quickly right now",
                ],
            },
            "spouse_decision": {
                "approach": "Include partner and schedule joint viewing",
                "talking_points": [
                    "I'd love to include them in the conversation",
                    "Would a weekend showing work for both of you?",
                ],
            },
            "timing": {
                "approach": "Provide market education and soft follow-up",
                "talking_points": [
                    "I understand timing is important. Let me share what the market looks like",
                    "I can keep you updated on new listings that match your criteria",
                ],
            },
        }

        strategy = objection_strategies.get(objection_type, {
            "approach": "Address concern with empathy and helpful information",
            "talking_points": ["I understand your concern. Let's work through this together."],
        })

        # Enrich budget_shock with affordability data if available
        if objection_type == "budget_shock" and state.get("affordability_analysis"):
            analysis = state["affordability_analysis"]
            strategy["talking_points"].append(
                f"With 20% down, your estimated monthly payment would be "
                f"${analysis.get('total_monthly_payment', 0):,.0f}"
            )

        # Track objection in history
        objection_record = {
            "type": objection_type,
            "strategy": strategy["approach"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

        objection_history = state.get("objection_history") or []
        objection_history.append(objection_record)

        return {
            "objection_history": objection_history,
            "current_qualification_step": "objection_handling",
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

            # Use A/B test variant from state (assigned in process_buyer_conversation)
            tone_variant = state.get("tone_variant")
            if not tone_variant:
                buyer_id = state.get("buyer_id", "unknown")
                try:
                    tone_variant = await self._await_if_needed(
                        self.ab_testing.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, buyer_id)
                    )
                    if not isinstance(tone_variant, str) or not tone_variant:
                        tone_variant = "empathetic"
                except (KeyError, ValueError):
                    tone_variant = "empathetic"

            # Base prompt for buyer consultation
            buyer_temp = getattr(profile, "buyer_temperature", "cold") if profile else "cold"
            response_prompt = f"""
            As Jorge's Buyer Bot, generate a helpful and supportive response for this buyer:

            Buyer Temperature: {buyer_temp}
            Financial Readiness: {state.get("financial_readiness_score", 25)}/100
            Properties Matched: {len(matches)}
            Current Step: {state.get("current_qualification_step", "unknown")}

            Conversation Context: {state["conversation_history"][-2:] if state["conversation_history"] else []}

            Response should be:
            - Warm, helpful and genuinely caring
            - Educational and patient (never pushy)
            - Focused on understanding their needs first
            - Property-focused if qualified with matches
            - Market education if qualified but no matches
            - Professional, friendly and relationship-focused (Jorge's style)

            Tone style: {tone_variant}

            Keep under 160 characters for SMS compliance.
            """

            # Enhance prompt with intelligence context if available (Phase 3.3)
            if intelligence_context:
                response_prompt = await self._enhance_buyer_prompt_with_intelligence(
                    response_prompt, intelligence_context, state
                )

            response = await self.claude.generate_response(response_prompt)

            return {
                "response_content": response.get(
                    "content", "I'd love to help you find the perfect property for your needs."
                ),
                "response_tone": "friendly_consultative",
                "next_action": "send_response",
            }

        except Exception as e:
            logger.error(f"Error generating buyer response for {state['buyer_id']}: {str(e)}")
            return {
                "response_content": "I'd love to help you find the perfect property for your needs.",
                "response_tone": "friendly_supportive",
                "next_action": "send_response",
            }

    async def schedule_next_action(self, state: BuyerBotState) -> Dict:
        """
        Schedule next action based on buyer qualification level and engagement.
        Follows proven lead nurturing sequences.
        Uses budget_config for qualification thresholds.
        """
        try:
            profile = state.get("intent_profile")
            qualification_score = state.get("financial_readiness_score", 25)

            # Determine next action using budget_config
            next_action, follow_up_hours = self.budget_config.get_next_action(qualification_score)

            # Schedule the action
            await self._schedule_follow_up(state["buyer_id"], next_action, follow_up_hours)

            return {
                "next_action": next_action,
                "follow_up_scheduled": True,
                "follow_up_hours": follow_up_hours,
                "last_action_timestamp": datetime.now(timezone.utc),
            }

        except Exception as e:
            logger.error(f"Error scheduling next action for {state['buyer_id']}: {str(e)}")
            return {"next_action": "manual_review", "follow_up_scheduled": False}

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

            endpoint = f"{self.ghl_client.base_url}/contacts/{buyer_id}/notes"
            response = await self.ghl_client.http_client.post(
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
                await self.ghl_client.trigger_workflow(buyer_id, settings.notify_agent_workflow_id)
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
            escalation_result["tag_added"] or escalation_result["note_added"] or escalation_result["workflow_triggered"]
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
            msg.get("content", "").lower() for msg in conversation_history if msg.get("role") == "user"
        )

        # Tier 1: Conversation heuristics
        try:
            heuristic_result = self._assess_financial_from_conversation(conversation_text)
            if heuristic_result:
                logger.info(
                    f"Financial fallback Tier 1 (heuristic) used for buyer {buyer_id}",
                    extra={"fallback_tier": 1, "buyer_id": buyer_id},
                )
                return {
                    "financing_status": heuristic_result["financing_status"],
                    "budget_range": heuristic_result.get("budget_range"),
                    "financial_readiness_score": heuristic_result["confidence"],
                    "fallback_tier": 1,
                    "fallback_source": "conversation_heuristic",
                }
        except Exception as e:
            logger.warning(f"Tier 1 fallback failed for {buyer_id}: {e}")

        # Tier 2: Conservative default
        logger.info(
            f"Financial fallback Tier 2 (conservative default) used for buyer {buyer_id}",
            extra={"fallback_tier": 2, "buyer_id": buyer_id},
        )
        return {
            "financing_status": "assessment_pending",
            "budget_range": None,
            "financial_readiness_score": 25.0,
            "requires_manual_review": True,
            "fallback_tier": 2,
            "fallback_source": "conservative_default",
            "confidence": 0.3,
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

    async def escalate_compliance_violation(self, buyer_id: str, violation_type: str, evidence: Dict) -> Dict:
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
                "evidence_keys": list(evidence.keys()),
            },
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
            "status": "pending",
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
                evidence_summary=str(evidence.get("summary", ""))[:500],
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
                    priority="urgent",
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
                violation_type=violation_type,
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

            conversation_text = " ".join(
                [msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]
            )

            # Find dollar amounts with optional k
            dollar_pattern = r"\$([0-9,]+)([kK]?)"
            matches = re.findall(dollar_pattern, conversation_text)

            amounts = []
            for val, k_suffix in matches:
                amount = int(val.replace(",", ""))
                if k_suffix:
                    amount *= 1000
                elif 100 <= amount < self.budget_config.BUDGET_AMOUNT_K_THRESHOLD:
                    # Only auto-multiply 100-999 range (clear K-shorthand in real estate)
                    # "$500" -> $500K, but "$50" stays $50, "$1500" stays $1500
                    amount *= 1000
                amounts.append(amount)

            if len(amounts) >= 2:
                return {"min": min(amounts), "max": max(amounts)}
            elif len(amounts) == 1:
                # Single amount - assume it's max budget
                return {"min": int(amounts[0] * self.budget_config.BUDGET_SINGLE_AMOUNT_MIN_FACTOR), "max": amounts[0]}

            return None

        except Exception as e:
            logger.error(f"Error extracting budget range: {str(e)}")
            return None

    async def _extract_property_preferences(self, conversation_history: List[ConversationMessage]) -> Optional[Dict[str, Any]]:
        """Extract property preferences from conversation history."""
        try:
            conversation_text = " ".join(
                [msg.get("content", "").lower() for msg in conversation_history if msg.get("role") == "user"]
            )

            preferences = {}

            # Extract bedrooms
            import re

            bed_match = re.search(r"(\d+)\s*(bed|bedroom)", conversation_text)
            if bed_match:
                preferences["bedrooms"] = int(bed_match.group(1))

            # Extract bathrooms
            bath_match = re.search(r"(\d+)\s*(bath|bathroom)", conversation_text)
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
                contact_id=buyer_id, action_type=action, scheduled_hours=hours
            )

            logger.info(f"Scheduled {action} for buyer {buyer_id} in {hours} hours")

        except Exception as e:
            logger.error(f"Error scheduling follow-up for {buyer_id}: {str(e)}")

    async def process_buyer_conversation(
        self,
        conversation_id: Optional[str] = None,
        user_message: Optional[str] = None,
        buyer_name: Optional[str] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        buyer_phone: Optional[str] = None,
        buyer_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
        buyer_id: Optional[str] = None,
        **legacy_kwargs: Any,
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
            buyer_id: Backward-compatible alias for conversation_id
            legacy_kwargs: Reserved for backward-compatible call patterns

        Returns:
            Dict containing:
                - response_content: Bot's response message
                - lead_id: The conversation/buyer identifier
                - current_step: Current qualification step
                - engagement_status: Current engagement state
                - financial_readiness: Financial readiness score
                - handoff_signals: Signals for cross-bot handoff
        """
        MAX_MESSAGE_LENGTH = 10_000

        # Backward compatibility:
        # 1) Legacy positional call style:
        #    process_buyer_conversation(buyer_id, buyer_name, conversation_history)
        # 2) Legacy keyword call style:
        #    process_buyer_conversation(buyer_id=..., buyer_name=..., conversation_history=...)
        legacy_interface = buyer_id is not None
        if conversation_history is None and isinstance(buyer_name, list):
            conversation_history = buyer_name
            buyer_name = user_message if isinstance(user_message, str) else None
            user_message = None
            legacy_interface = True

        if not conversation_id:
            conversation_id = buyer_id or legacy_kwargs.get("lead_id")

        conversation_history = list(conversation_history or [])

        if not user_message or not str(user_message).strip():
            user_message = self._extract_latest_user_message(conversation_history)
        if legacy_interface and (not user_message or not str(user_message).strip()):
            # Keep legacy workflows moving even when only buyer_id/history were provided.
            user_message = "Can you help me with next steps to buy a home?"

        # Input validation
        if not conversation_id or not str(conversation_id).strip():
            raise ValueError("conversation_id must be a non-empty string")
        if not user_message or not str(user_message).strip():
            fallback = self._sanitize_sms_response("I did not catch that. Could you share a little more so I can help?")
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "response_content": fallback,
                "message": fallback,
                "current_step": "awaiting_input",
                "engagement_status": "active",
                "qualification_status": "in_progress",
                "financial_readiness": 0.0,
                "handoff_signals": {},
            }
        user_message = str(user_message).strip()[:MAX_MESSAGE_LENGTH]

        # TCPA opt-out check — must run BEFORE any AI processing
        msg_lower = user_message.lower().strip()
        if any(phrase in msg_lower for phrase in OPT_OUT_PHRASES):
            logger.info(f"Opt-out detected for buyer {conversation_id}")
            opt_out_message = (
                "You've been unsubscribed from automated messages. "
                "If you'd like to reconnect, just text us anytime."
            )
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "response_content": opt_out_message,
                "message": opt_out_message,
                "opt_out_detected": True,
                "actions": [{"type": "add_tag", "tag": "AI-Off"}],
                "buyer_temperature": "unknown",
                "current_step": "opt_out",
                "engagement_status": "opted_out",
                "qualification_status": "opted_out",
                "financial_readiness": 0.0,
                "handoff_signals": {},
            }

        try:
            import time as _time

            _workflow_start = _time.time()

            if not conversation_history or str(conversation_history[-1].get("content", "")).strip() != user_message:
                conversation_history.append(
                    {"role": "user", "content": user_message, "timestamp": datetime.now(timezone.utc).isoformat()}
                )

            # Prune to prevent unbounded memory growth
            if len(conversation_history) > self.MAX_CONVERSATION_HISTORY:
                conversation_history = conversation_history[-self.MAX_CONVERSATION_HISTORY :]

            # Get A/B test variant for response tone (before workflow)
            try:
                _tone_variant = await self._await_if_needed(
                    self.ab_testing.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, conversation_id)
                )
                if not isinstance(_tone_variant, str) or not _tone_variant:
                    _tone_variant = "empathetic"
            except (KeyError, ValueError):
                _tone_variant = "empathetic"

            initial_state = {
                "buyer_id": conversation_id,
                "buyer_name": buyer_name or f"Buyer {conversation_id}",
                "target_areas": None,
                "conversation_history": conversation_history,
                "intent_profile": None,
                "budget_range": None,
                "financing_status": "unknown",
                "urgency_level": "browsing",
                "property_preferences": None,
                "current_qualification_step": "budget",
                "objection_detected": False,
                "detected_objection_type": None,
                "next_action": "qualify",
                "response_content": "",
                "matched_properties": [],
                "financial_readiness_score": 0.0,
                "buying_motivation_score": 0.0,
                "is_qualified": False,
                "current_journey_stage": "discovery",
                "properties_viewed_count": 0,
                "last_action_timestamp": None,
                "user_message": user_message,
                "tone_variant": _tone_variant,
                "intelligence_context": None,
                "intelligence_performance_ms": 0.0,
            }

            if buyer_phone:
                initial_state["buyer_phone"] = buyer_phone
            if buyer_email:
                initial_state["buyer_email"] = buyer_email
            if metadata:
                initial_state["metadata"] = metadata

            result = await self.workflow.ainvoke(initial_state)

            _workflow_duration_ms = (_time.time() - _workflow_start) * 1000
            self.workflow_stats["total_interactions"] += 1

            is_qualified = (
                result.get("financial_readiness_score", 0) >= 50 and result.get("buying_motivation_score", 0) >= 50
            )
            result["is_qualified"] = is_qualified
            result["lead_id"] = conversation_id
            result["current_step"] = result.get("current_qualification_step", "unknown")
            result["engagement_status"] = "qualified" if is_qualified else "nurturing"
            result["qualification_status"] = "qualified" if is_qualified else "needs_nurturing"
            result["financial_readiness"] = result.get("financial_readiness_score", 0.0)

            handoff_signals = {}
            if self.enable_handoff:
                from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

                handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            result["handoff_signals"] = handoff_signals

            # SMS length guard
            response_text = result.get("response_content", "")
            if response_text and len(response_text) > self.SMS_MAX_LENGTH:
                result["response_content_full"] = response_text
                result["response_content"] = response_text[: self.SMS_MAX_LENGTH]

            # WS-5: enforce compliance-safe outbound text at bot layer.
            compliance_payload = await self._apply_outbound_compliance(
                message=str(result.get("response_content", "") or ""),
                buyer_id=conversation_id,
            )
            result.update(compliance_payload)
            result["message"] = result.get("response_content", "")

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
                await self._await_if_needed(
                    self.ab_testing.record_outcome(
                        ABTestingService.RESPONSE_TONE_EXPERIMENT,
                        conversation_id,
                        _tone_variant,
                        "response",
                    )
                )
            except (KeyError, ValueError):
                pass

            # Tag response with A/B experiment metadata
            result["ab_test"] = {
                "experiment_id": ABTestingService.RESPONSE_TONE_EXPERIMENT,
                "variant": _tone_variant,
            }

            await self._await_if_needed(
                self.event_publisher.publish_bot_status_update(
                    bot_type="jorge-buyer",
                    contact_id=conversation_id,
                    status="completed",
                    current_step=result.get("current_qualification_step", "unknown"),
                )
            )

            await self._await_if_needed(
                self.event_publisher.publish_buyer_qualification_complete(
                    contact_id=conversation_id,
                    qualification_status="qualified" if is_qualified else "needs_nurturing",
                    final_score=(result.get("financial_readiness_score", 0) + result.get("buying_motivation_score", 0))
                    / 2,
                    properties_matched=len(result.get("matched_properties", [])),
                )
            )

            return result

        except Exception as e:
            # Record failure metrics
            try:
                import time as _time

                _fail_duration = (_time.time() - _workflow_start) * 1000
                await self.performance_tracker.track_operation("buyer_bot", "process", _fail_duration, success=False)
                self.metrics_collector.record_bot_interaction("buyer", duration_ms=_fail_duration, success=False)
            except Exception as ex:
                logger.debug(f"Secondary failure in error metrics recording: {str(ex)}")

            logger.error(f"Error processing buyer conversation for {conversation_id}: {str(e)}")
            error_message = self._sanitize_sms_response(
                "I'm having technical difficulties right now. Please try again, and I can keep helping with your home search."
            )
            return {
                "buyer_id": conversation_id,
                "lead_id": conversation_id,
                "error": str(e),
                "response_content": error_message,
                "message": error_message,
                "current_step": "error",
                "engagement_status": "error",
                "qualification_status": "error",
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
                    concern_type = objection.get("type", "unknown")
                    confidence = objection.get("confidence", 0.0)
                    context = objection.get("context", "")
                    enhanced_prompt += f"\n- {concern_type.upper()} concern detected ({confidence:.0%}): {context}"

                    # Add consultative suggestions for buyer concerns
                    suggestions = objection.get("suggested_responses", [])
                    if suggestions:
                        enhanced_prompt += f"\n  Consultative approach: {suggestions[0]}"

            # Add preference intelligence insights for personalization
            preference_intel = intelligence_context.preference_intelligence
            if preference_intel.profile_completeness > 0.3:
                enhanced_prompt += f"\n\nBUYER PREFERENCE INTELLIGENCE:"
                enhanced_prompt += f"\n- Preference profile completeness: {preference_intel.profile_completeness:.0%}"

                # Add learned preferences for better consultation
                if hasattr(preference_intel, "learned_preferences") and preference_intel.learned_preferences:
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
        state: BuyerBotState,
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
