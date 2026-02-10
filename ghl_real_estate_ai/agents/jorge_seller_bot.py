"""
Jorge Seller Bot - Unified Enterprise Implementation
Combines all research enhancements into production-ready unified implementation.

UNIFIED FEATURES:
- LangGraph friendly qualification (Jorge's helpful customer service methodology)
- Track 3.1 Predictive Intelligence (ML-enhanced decision making)
- Progressive Skills (68% token reduction, optional)
- Agent Mesh Integration (enterprise orchestration, optional)
- MCP Protocol Integration (standardized external services, optional)
- Adaptive Intelligence (conversation memory & dynamic questioning, optional)

Feature flags allow selective enablement for different deployment scenarios.
Jorge now focuses on building relationships and helping customers succeed.
"""

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.seller_intent_decoder import SellerIntentDecoder
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.bot_context_types import (
    BotMetadata,
    ConversationMessage,
    QualificationData,
    SellerBotResponse,
)
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.jorge.ab_testing_service import ABTestingService
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.market_intelligence import get_market_intelligence
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer

try:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient

    GHL_CLIENT_AVAILABLE = True
except ImportError:
    GHL_CLIENT_AVAILABLE = False

# Track 3.1 Predictive Intelligence Integration
try:
    from bots.shared.ml_analytics_engine import MLAnalyticsEngine, get_ml_analytics_engine
except ImportError:
    from ghl_real_estate_ai.stubs.bots_stub import get_ml_analytics_engine

# Phase 3.3 Bot Intelligence Middleware Integration
try:
    from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
    from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware

    BOT_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logger.warning(f"Bot Intelligence Middleware unavailable: {e}")
    BOT_INTELLIGENCE_AVAILABLE = False

# Optional Enhanced Features (imported conditionally)
try:
    from ghl_real_estate_ai.services.progressive_skills_manager import ProgressiveSkillsManager
    from ghl_real_estate_ai.services.token_tracker import get_token_tracker

    PROGRESSIVE_SKILLS_AVAILABLE = True
except ImportError:
    PROGRESSIVE_SKILLS_AVAILABLE = False

try:
    from ghl_real_estate_ai.services.agent_mesh_coordinator import (
        AgentCapability,
        AgentTask,
        TaskPriority,
        get_mesh_coordinator,
    )
    from ghl_real_estate_ai.services.mesh_agent_registry import AgentMetrics, AgentStatus, MeshAgent

    AGENT_MESH_AVAILABLE = True
except ImportError:
    AGENT_MESH_AVAILABLE = False

try:
    from ghl_real_estate_ai.services.mcp_client import get_mcp_client

    MCP_INTEGRATION_AVAILABLE = True
except ImportError:
    MCP_INTEGRATION_AVAILABLE = False

logger = get_logger(__name__)

# ================================
# ENHANCED FEATURES DATACLASSES
# ================================


@dataclass
class JorgeFeatureConfig:
    """Configuration for Jorge's enhanced features"""

    enable_progressive_skills: bool = False
    enable_agent_mesh: bool = False
    enable_mcp_integration: bool = False
    enable_adaptive_questioning: bool = False
    enable_track3_intelligence: bool = True  # Default enabled
    enable_bot_intelligence: bool = True  # Phase 3.3 Intelligence Integration
    jorge_handoff_enabled: bool = True

    # Performance settings
    max_concurrent_tasks: int = 5
    sla_response_time: int = 15  # seconds
    cost_per_token: float = 0.000015

    # Jorge-specific settings
    commission_rate: float = 0.06
    friendly_approach_enabled: bool = True
    temperature_thresholds: Dict[str, int] = None

    def __post_init__(self):
        if self.temperature_thresholds is None:
            self.temperature_thresholds = {"hot": 75, "warm": 50, "lukewarm": 25}


@dataclass
class QualificationResult:
    """Comprehensive qualification result with all enhancement metadata"""

    lead_id: str
    qualification_score: float
    frs_score: float
    pcs_score: float
    temperature: str
    next_actions: List[str]
    confidence: float
    tokens_used: int
    cost_incurred: float

    # Enhancement metadata
    progressive_skills_applied: bool = False
    mesh_task_id: Optional[str] = None
    orchestrated_tasks: List[str] = None
    mcp_enrichment_applied: bool = False
    adaptive_questioning_used: bool = False
    timeline_ms: Dict[str, float] = None

    def __post_init__(self):
        if self.orchestrated_tasks is None:
            self.orchestrated_tasks = []
        if self.timeline_ms is None:
            self.timeline_ms = {}


class ConversationMemory:
    """Maintains conversation context and patterns across sessions (Adaptive Feature)"""

    def __init__(self):
        self._memory: Dict[str, Dict] = {}

    async def get_context(self, conversation_id: str) -> Dict:
        """Get conversation context including last scores and patterns"""
        return self._memory.get(
            conversation_id,
            {"last_scores": None, "question_history": [], "response_patterns": {}, "adaptation_count": 0},
        )

    async def update_context(self, conversation_id: str, update: Dict):
        """Update conversation context with new information"""
        if conversation_id not in self._memory:
            self._memory[conversation_id] = {}
        self._memory[conversation_id].update(update)


class AdaptiveQuestionEngine:
    """Manages dynamic question selection and adaptation (Adaptive Feature)"""

    def __init__(self, questions_config=None):
        # Core questions (config-first, hardcoded fallback)
        if questions_config and questions_config.questions:
            self.jorge_core_questions = [q.get("text", q) if isinstance(q, dict) else q for q in questions_config.questions]
        else:
            self.jorge_core_questions = [
                "What's your timeline for selling?",
                "What's driving you to sell the property?",
                "What's your bottom-line number?",
                "Are you flexible on the closing date?",
            ]

        # Friendly questions for high-intent leads (config-first, hardcoded fallback)
        if questions_config and questions_config.accelerators:
            self.high_intent_accelerators = questions_config.accelerators
        else:
            self.high_intent_accelerators = [
                "It sounds like you're ready to move forward! I'd love to see your property. Would tomorrow afternoon or this week work better for a visit?",
                "Based on what you've shared, it sounds like we have a great opportunity here. Would you like to schedule a time to discuss your options in detail?",
                "I'm excited to help you with this! What timeline would work best for your situation?",
                "You seem ready to take the next step - that's wonderful! When would be a good time to meet and go over your options?",
                "I can see this is important to you. Let's find a time to sit down and create a plan that works for your situation.",
            ]

        self.supportive_clarifiers = {
            "zestimate": [
                "Online estimates are a great starting point! I'd love to show you what similar homes in your area have actually sold for recently.",
                "Those online tools don't see the unique features of your home. Would you like a more personalized market analysis?",
            ],
            "thinking": [
                "I completely understand you need time to consider this. What specific questions can I help answer for you?",
                "Taking time to think it through is smart! What aspects would be most helpful for us to discuss?",
            ],
            "agent": [
                "That's great that you're working with someone! I'm happy to share some additional market insights that might be helpful.",
                "Wonderful! If you'd like, I can provide some complementary information that might be useful for your decision.",
            ],
        }

    async def select_next_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select the optimal next question based on real-time analysis"""
        current_scores = state["intent_profile"]

        # Fast-track high-intent leads (PCS > 70)
        if current_scores.pcs.total_score > 70:
            return await self._fast_track_to_calendar(state)

        # Handle specific concerns with supportive questions
        if state.get("detected_stall_type"):
            return await self._select_supportive_clarifier(state["detected_stall_type"])

        # Adaptive questioning based on score progression
        if context.get("adaptation_count", 0) > 0:
            return await self._select_adaptive_question(state, context)

        # Default to core questions for first-time qualification
        return await self._select_standard_question(state)

    async def _fast_track_to_calendar(self, state: JorgeSellerState) -> str:
        """Direct high-intent leads to calendar scheduling"""
        import random

        return random.choice(self.high_intent_accelerators)

    async def _select_supportive_clarifier(self, clarifier_type: str) -> str:
        """Select supportive clarifier based on conversation context"""
        import random

        questions = self.supportive_clarifiers.get(clarifier_type, self.supportive_clarifiers["thinking"])
        return random.choice(questions)

    async def _select_adaptive_question(self, state: JorgeSellerState, context: Dict) -> str:
        """Select question based on conversation history and patterns"""
        # Analyze what's missing from qualification
        scores = state["intent_profile"]

        if scores.frs.timeline.score < 50:
            return "I'd love to better understand your timeline. What would work best for your situation?"
        elif scores.frs.price.score < 50:
            return "What price range would make this feel like a great decision for you?"
        elif scores.frs.condition.score < 50:
            return "Would you prefer to sell as-is, or are you thinking about making some updates first?"

        # Default fallback
        return "What's the most important outcome for you in this process?"

    async def _select_standard_question(self, state: JorgeSellerState) -> str:
        """Select from core Jorge questions"""
        current_q = state.get("current_question", 1)
        if current_q <= len(self.jorge_core_questions):
            return self.jorge_core_questions[current_q - 1]
        return "How can I best help you with your property goals?"


class JorgeSellerBot:
    """
    Unified Jorge Seller Bot - Production-ready with optional enhancements
    Designed to help sellers succeed while identifying 'Serious Sellers'.

    CORE FEATURES (always enabled):
    - LangGraph friendly qualification workflow
    - Track 3.1 Predictive Intelligence integration
    - Real-time event publishing and coordination

    OPTIONAL ENHANCEMENTS (configurable):
    - Progressive Skills (68% token reduction)
    - Agent Mesh Integration (enterprise orchestration)
    - MCP Protocol Integration (standardized external services)
    - Adaptive Intelligence (conversation memory & dynamic questioning)
    """

    def __init__(
        self,
        tenant_id: str = "jorge_seller",
        config: Optional[JorgeFeatureConfig] = None,
        industry_config: Optional["IndustryConfig"] = None,
    ):
        # Industry-agnostic configuration layer (backward compatible)
        from ghl_real_estate_ai.config.industry_config import IndustryConfig

        self.industry_config: IndustryConfig = industry_config or IndustryConfig.default_real_estate()

        # Core components (always initialized)
        self.tenant_id = tenant_id
        self.config = config or JorgeFeatureConfig()
        self.intent_decoder = LeadIntentDecoder(industry_config=self.industry_config)
        self.seller_intent_decoder = SellerIntentDecoder(industry_config=self.industry_config)
        self.cma_generator = CMAGenerator()
        self.market_intelligence = get_market_intelligence()
        self.claude = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
        self.seller_psychology_analyzer = get_seller_psychology_analyzer()

        # Track 3.1 Predictive Intelligence Engine (always enabled)
        if self.config.enable_track3_intelligence:
            self.ml_analytics = get_ml_analytics_engine(tenant_id)
        else:
            self.ml_analytics = None

        # Progressive Skills components (optional)
        self.skills_manager = None
        self.token_tracker = None
        if self.config.enable_progressive_skills and PROGRESSIVE_SKILLS_AVAILABLE:
            self.skills_manager = ProgressiveSkillsManager()
            self.token_tracker = get_token_tracker()
            logger.info("Jorge bot: Progressive skills enabled (68% token reduction)")
        elif self.config.enable_progressive_skills:
            logger.warning("Jorge bot: Progressive skills requested but dependencies not available")

        # Agent Mesh components (optional)
        self.mesh_coordinator = None
        if self.config.enable_agent_mesh and AGENT_MESH_AVAILABLE:
            self.mesh_coordinator = get_mesh_coordinator()
            logger.info("Jorge bot: Agent mesh integration enabled")
        elif self.config.enable_agent_mesh:
            logger.warning("Jorge bot: Agent mesh requested but dependencies not available")

        # MCP Integration components (optional)
        self.mcp_client = None
        if self.config.enable_mcp_integration and MCP_INTEGRATION_AVAILABLE:
            self.mcp_client = get_mcp_client()
            logger.info("Jorge bot: MCP integration enabled")
        elif self.config.enable_mcp_integration:
            logger.warning("Jorge bot: MCP integration requested but dependencies not available")

        # Adaptive Intelligence components (optional)
        self.conversation_memory = None
        self.question_engine = None
        if self.config.enable_adaptive_questioning:
            self.conversation_memory = ConversationMemory()
            self.question_engine = AdaptiveQuestionEngine(questions_config=self.industry_config.questions)
            logger.info("Jorge bot: Adaptive questioning enabled")

        # Phase 3.3 Bot Intelligence Middleware (optional)
        self.intelligence_middleware = None
        if self.config.enable_bot_intelligence and BOT_INTELLIGENCE_AVAILABLE:
            self.intelligence_middleware = get_bot_intelligence_middleware()
            logger.info("Jorge bot: Bot Intelligence Middleware enabled (Phase 3.3)")
        elif self.config.enable_bot_intelligence:
            logger.warning("Jorge bot: Bot Intelligence requested but dependencies not available")

        # Monitoring services (singletons — cheap to instantiate)
        self.performance_tracker = PerformanceTracker()
        self.metrics_collector = BotMetricsCollector()
        self.alerting_service = AlertingService()
        self.ab_testing = ABTestingService()
        self._init_ab_experiments()

        # Performance tracking
        self.workflow_stats = {
            "total_interactions": 0,
            "progressive_skills_usage": 0,
            "mesh_orchestrations": 0,
            "mcp_calls": 0,
            "adaptive_question_selections": 0,
            "token_savings": 0,
            "intelligence_enhancements": 0,
            "intelligence_cache_hits": 0,
        }

        # Build appropriate workflow based on enabled features
        self.workflow = self._build_unified_graph()

    def _init_ab_experiments(self) -> None:
        """Create default A/B experiments if not already registered."""
        try:
            self.ab_testing.create_experiment(
                ABTestingService.RESPONSE_TONE_EXPERIMENT,
                ["formal", "casual", "empathetic"],
            )
        except ValueError:
            pass  # Already exists

    def _build_unified_graph(self) -> StateGraph:
        """Build workflow graph based on enabled features"""
        if self.config.enable_adaptive_questioning:
            return self._build_adaptive_graph()
        else:
            return self._build_standard_graph()

    def _build_standard_graph(self) -> StateGraph:
        workflow = StateGraph(JorgeSellerState)

        # Define Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)

        # Add intelligence gathering node if enabled
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_intelligence", self.gather_intelligence_context)

        # CMA & Market Intelligence nodes
        workflow.add_node("generate_cma", self.generate_cma)
        workflow.add_node("analyze_market_conditions", self.analyze_market_conditions)

        workflow.add_node("detect_stall", self.detect_stall)
        workflow.add_node("defend_valuation", self.defend_valuation)
        workflow.add_node("prepare_listing", self.prepare_listing)
        workflow.add_node("select_strategy", self.select_strategy)
        workflow.add_node("generate_jorge_response", self.generate_jorge_response)
        workflow.add_node("recalculate_pcs", self.recalculate_pcs_node)
        workflow.add_node("execute_follow_up", self.execute_follow_up)

        # Define Edges
        workflow.set_entry_point("analyze_intent")

        # Conditional routing for intelligence gathering
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge("analyze_intent", "gather_intelligence")
            workflow.add_edge("gather_intelligence", "generate_cma")
        else:
            workflow.add_edge("analyze_intent", "generate_cma")

        workflow.add_edge("generate_cma", "analyze_market_conditions")
        workflow.add_edge("analyze_market_conditions", "detect_stall")

        # Conditional routing from detect_stall
        workflow.add_conditional_edges(
            "detect_stall",
            self._route_after_stall_detection,
            {
                "defend_valuation": "defend_valuation",
                "select_strategy": "select_strategy",
            },
        )
        workflow.add_edge("defend_valuation", "select_strategy")

        # Routing based on next_action
        workflow.add_conditional_edges(
            "select_strategy",
            self._route_seller_action,
            {
                "respond": "generate_jorge_response",
                "follow_up": "execute_follow_up",
                "listing_prep": "prepare_listing",
                "end": END,
            },
        )

        workflow.add_edge("generate_jorge_response", "recalculate_pcs")
        workflow.add_edge("recalculate_pcs", END)
        workflow.add_edge("execute_follow_up", END)
        workflow.add_edge("prepare_listing", "generate_jorge_response")

        return workflow.compile()

    def _build_adaptive_graph(self) -> StateGraph:
        """Build enhanced workflow with adaptive question selection"""
        workflow = StateGraph(JorgeSellerState)

        # Enhanced Nodes
        workflow.add_node("analyze_intent", self.analyze_intent)

        # Add intelligence gathering node if enabled
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_intelligence", self.gather_intelligence_context)

        workflow.add_node("detect_stall", self.detect_stall)
        workflow.add_node("adaptive_strategy", self.adaptive_strategy_selection)
        workflow.add_node("generate_adaptive_response", self.generate_adaptive_response)
        workflow.add_node("recalculate_pcs", self.recalculate_pcs_node)
        workflow.add_node("execute_follow_up", self.execute_follow_up)
        workflow.add_node("update_memory", self.update_conversation_memory)

        # Enhanced Flow
        workflow.set_entry_point("analyze_intent")

        # Conditional routing for intelligence gathering
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge("analyze_intent", "gather_intelligence")
            workflow.add_edge("gather_intelligence", "detect_stall")
        else:
            workflow.add_edge("analyze_intent", "detect_stall")

        workflow.add_edge("detect_stall", "adaptive_strategy")

        # Conditional routing with adaptive logic
        workflow.add_conditional_edges(
            "adaptive_strategy",
            self._route_adaptive_action,
            {
                "respond": "generate_adaptive_response",
                "follow_up": "execute_follow_up",
                "fast_track": "generate_adaptive_response",
                "end": "update_memory",
            },
        )

        workflow.add_edge("generate_adaptive_response", "recalculate_pcs")
        workflow.add_edge("recalculate_pcs", "update_memory")
        workflow.add_edge("execute_follow_up", "update_memory")
        workflow.add_edge("update_memory", END)

        return workflow.compile()

    # --- Node Implementations ---

    async def analyze_intent(self, state: JorgeSellerState) -> Dict:
        """Score the lead and identify psychological commitment."""
        # Emit bot status update - starting analysis
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="analyze_intent"
        )

        logger.info(f"Analyzing seller intent for {state['lead_name']}")
        profile = self.intent_decoder.analyze_lead(state["lead_id"], state["conversation_history"])

        # Classify seller temperature based on scores
        seller_temperature = self._classify_temperature(profile)

        # Emit qualification progress
        await self.event_publisher.publish_jorge_qualification_progress(
            contact_id=state["lead_id"],
            current_question=1,  # Starting with Q1
            questions_answered=0,
            seller_temperature=seller_temperature,
            qualification_scores={"frs_score": profile.frs.total_score, "pcs_score": profile.pcs.total_score},
            next_action="detect_stall",
        )

        # Extract property condition from conversation
        property_condition = self._extract_property_condition(
            state.get("conversation_history", [])
        )

        # Run seller intent decoder for enhanced analysis
        seller_intent_profile = self.seller_intent_decoder.analyze_seller(
            state["lead_id"], state["conversation_history"]
        )

        # Phase 1.2: Classify seller type (Investor, Distressed, Traditional)
        seller_classification = await self.seller_psychology_analyzer.classify_seller_type(
            conversation_history=state["conversation_history"],
            custom_fields=state.get("metadata", {}).get("custom_fields") if state.get("metadata") else None,
        )

        return {
            "intent_profile": profile,
            "psychological_commitment": profile.pcs.total_score,
            "is_qualified": profile.frs.classification in ["Hot Lead", "Warm Lead"],
            "seller_temperature": seller_temperature,
            "last_action_timestamp": datetime.now(timezone.utc),
            "property_condition": property_condition,
            "seller_intent_profile": seller_intent_profile,
            "seller_persona": seller_classification,
        }

    def _extract_property_condition(
        self, conversation_history: List[ConversationMessage]
    ) -> Optional[str]:
        """Extract property condition from conversation keywords."""
        if not conversation_history:
            return None

        text = " ".join(
            msg.get("content", "").lower()
            for msg in conversation_history
            if msg.get("role") == "user"
        )

        move_in_ready_markers = [
            "move-in ready", "move in ready", "turnkey", "just remodeled",
            "recently renovated", "updated", "great condition", "perfect condition",
        ]
        needs_work_markers = [
            "needs work", "needs some work", "needs updating", "dated",
            "cosmetic", "needs paint", "some updates", "a little work",
        ]
        major_repairs_markers = [
            "major repairs", "fixer", "fixer-upper", "foundation",
            "roof issues", "structural", "condemned", "tear down",
        ]

        if any(m in text for m in major_repairs_markers):
            return "major_repairs"
        elif any(m in text for m in needs_work_markers):
            return "needs_work"
        elif any(m in text for m in move_in_ready_markers):
            return "move_in_ready"

        return None

    async def gather_intelligence_context(self, state: JorgeSellerState) -> Dict:
        """
        Phase 3.3: Gather intelligence context for enhanced decision making.

        Integrates with Bot Intelligence Middleware to provide:
        - Property matching intelligence for better recommendations
        - Conversation intelligence for objection detection
        - Preference learning for personalized approaches

        Graceful fallback on service failures - never blocks Jorge's workflow.
        """
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="gather_intelligence",
        )

        intelligence_context = None
        intelligence_performance_ms = 0.0

        try:
            if self.intelligence_middleware:
                logger.info(f"Gathering intelligence context for seller lead {state['lead_id']}")

                # Extract basic preferences from conversation for intelligence gathering
                preferences = self._extract_preferences_from_conversation(state.get("conversation_history", []))

                # Get intelligence context with <200ms target
                start_time = time.time()
                intelligence_context = await self.intelligence_middleware.enhance_bot_context(
                    bot_type="jorge-seller",
                    lead_id=state["lead_id"],
                    location_id=state.get("location_id", "rancho_cucamonga"),  # Default to Rancho Cucamonga market
                    conversation_context=state.get("conversation_history", []),
                    preferences=preferences,
                )
                intelligence_performance_ms = (time.time() - start_time) * 1000

                # Update performance statistics
                self.workflow_stats["intelligence_enhancements"] += 1
                if intelligence_context.cache_hit:
                    self.workflow_stats["intelligence_cache_hits"] += 1

                # Log performance metrics
                logger.info(
                    f"Intelligence gathered for {state['lead_id']} in {intelligence_performance_ms:.1f}ms "
                    f"(cache_hit: {intelligence_context.cache_hit})"
                )

                # Emit intelligence gathering event for monitoring
                await self.event_publisher.publish_conversation_update(
                    conversation_id=f"jorge_{state['lead_id']}",
                    lead_id=state["lead_id"],
                    stage="intelligence_enhanced",
                    message=f"Intelligence context gathered: {intelligence_context.property_intelligence.match_count} properties, "
                    f"sentiment {intelligence_context.conversation_intelligence.overall_sentiment:.2f}",
                )

        except Exception as e:
            logger.warning(f"Intelligence enhancement unavailable for {state['lead_id']}: {e}")
            # Don't let intelligence failures block Jorge's workflow
            intelligence_context = None

        return {
            "intelligence_context": intelligence_context,
            "intelligence_performance_ms": intelligence_performance_ms,
            "intelligence_available": intelligence_context is not None,
        }

    def _extract_preferences_from_conversation(self, conversation_history: List[ConversationMessage]) -> Dict[str, Any]:
        """Extract basic preferences from conversation for intelligence gathering."""
        preferences = {}

        if not conversation_history:
            return preferences

        # Look for budget signals in conversation
        conversation_text = " ".join([msg.get("content", "") for msg in conversation_history]).lower()

        # Basic budget extraction (simple keyword matching)
        budget_keywords = {
            "under 400": {"budget_max": 400000},
            "under 500": {"budget_max": 700000},
            "under 600": {"budget_max": 600000},
            "under 700": {"budget_max": 700000},
            "under 800": {"budget_max": 800000},
            "under 1m": {"budget_max": 1200000},
            "under 1 million": {"budget_max": 1200000},
        }

        for keyword, budget_info in budget_keywords.items():
            if keyword in conversation_text:
                preferences.update(budget_info)
                break

        # Timeline extraction
        timeline_keywords = {
            "asap": "1_month",
            "quickly": "1_month",
            "urgent": "1_month",
            "3 months": "3_months",
            "6 months": "6_months",
            "next year": "12_months",
            "no rush": "flexible",
        }

        for keyword, timeline in timeline_keywords.items():
            if keyword in conversation_text:
                preferences["timeline"] = timeline
                break

        return preferences

    async def generate_cma(self, state: JorgeSellerState) -> Dict:
        """Generate CMA report if property address is available."""
        property_address = state.get("property_address")
        if not property_address:
            return {}

        try:
            zestimate = state.get("zestimate", 0.0)
            report = await self.cma_generator.generate_report(
                property_address, zestimate or 0.0
            )

            comparable_properties = []
            for comp in report.comparables:
                comparable_properties.append({
                    "address": comp.address,
                    "sale_price": comp.sale_price,
                    "sqft": comp.sqft,
                    "beds": comp.beds,
                    "baths": comp.baths,
                    "price_per_sqft": comp.price_per_sqft,
                })

            market_data = {
                "market_name": report.market_context.market_name,
                "price_trend": report.market_context.price_trend,
                "dom_average": report.market_context.dom_average,
                "inventory_level": report.market_context.inventory_level,
                "narrative": report.market_narrative,
            }

            logger.info(
                f"CMA generated for {property_address}: "
                f"estimated value ${report.estimated_value:,.0f}"
            )

            return {
                "cma_report": {
                    "estimated_value": report.estimated_value,
                    "value_range_low": report.value_range_low,
                    "value_range_high": report.value_range_high,
                    "confidence_score": report.confidence_score,
                    "zillow_variance_percent": report.zillow_variance_percent,
                    "zillow_explanation": report.zillow_explanation,
                    "market_narrative": report.market_narrative,
                },
                "estimated_value": report.estimated_value,
                "comparable_properties": comparable_properties,
                "market_data": market_data,
            }

        except Exception as e:
            logger.warning(f"CMA generation failed for {property_address}: {e}")
            return {}

    async def analyze_market_conditions(self, state: JorgeSellerState) -> Dict:
        """Determine market trend from available data."""
        market_data = state.get("market_data")
        if not market_data:
            return {"market_trend": "balanced"}

        try:
            inventory_level = market_data.get("inventory_level", 1450)
            # Use months of inventory approximation:
            # < 3 months supply = sellers market
            # > 6 months supply = buyers market
            # Rancho Cucamonga: ~480 sales/month avg, so months = inventory / 480
            months_of_inventory = inventory_level / 480

            if months_of_inventory < 3:
                trend = "sellers_market"
            elif months_of_inventory > 6:
                trend = "buyers_market"
            else:
                trend = "balanced"

            return {"market_trend": trend}

        except Exception as e:
            logger.warning(f"Market conditions analysis failed: {e}")
            return {"market_trend": "balanced"}

    async def defend_valuation(self, state: JorgeSellerState) -> Dict:
        """Build Zillow-defense response using CMA data when Zestimate stall detected."""
        cma_report = state.get("cma_report")
        if not cma_report:
            return {}

        try:
            estimated_value = cma_report.get("estimated_value", 0)
            variance = cma_report.get("zillow_variance_percent", 0)
            explanation = cma_report.get("zillow_explanation", "")
            comp_count = len(state.get("comparable_properties", []))
            market_narrative = cma_report.get("market_narrative", "")

            defense_context = (
                f"Our CMA analysis of {comp_count} recent comparable sales shows "
                f"an estimated value of ${estimated_value:,.0f}. "
                f"The Zillow Zestimate differs by {abs(variance):.1f}%. "
                f"{explanation} {market_narrative}"
            )

            prompt = f"""
            As Jorge, the seller mentioned Zillow/Zestimate. Use this CMA data to
            gently educate them about why real comparable sales are more accurate:

            {defense_context}

            Be helpful and educational, not dismissive. Keep under 160 chars for SMS.
            """

            response = await self.claude.analyze_with_context(prompt)
            content = (
                response.get("content")
                or response.get("analysis")
                or f"Real comps show ${estimated_value:,.0f} — Zillow can't walk through your house!"
            )

            return {"response_content": content}

        except Exception as e:
            logger.warning(f"Valuation defense failed: {e}")
            return {}

    async def prepare_listing(self, state: JorgeSellerState) -> Dict:
        """Generate listing preparation recommendations."""
        if not state.get("is_qualified") or not state.get("property_address"):
            return {}

        property_condition = state.get("property_condition")
        staging_recs = self._generate_staging_recommendations(property_condition)
        repair_estimates = self._estimate_repairs(property_condition)

        return {
            "staging_recommendations": staging_recs,
            "repair_estimates": repair_estimates,
            "current_journey_stage": "listing_prep",
        }

    def _generate_staging_recommendations(
        self, condition: Optional[str]
    ) -> List[str]:
        """Generate staging recommendations based on property condition."""
        base_recs = [
            "Declutter all rooms and remove personal photos",
            "Deep clean entire property including windows",
            "Maximize natural lighting — open all blinds and curtains",
            "Add fresh flowers or plants to key rooms",
        ]

        if condition == "move_in_ready":
            base_recs.extend([
                "Professional photography to showcase turnkey condition",
                "Highlight recent upgrades in listing description",
            ])
        elif condition == "needs_work":
            base_recs.extend([
                "Fresh neutral paint in main living areas",
                "Replace dated light fixtures and hardware",
                "Consider professional staging for primary living spaces",
            ])
        elif condition == "major_repairs":
            base_recs.extend([
                "Get pre-listing inspection to identify all issues",
                "Obtain contractor estimates for major repairs",
                "Consider selling as-is with repair credit",
                "Price accordingly to reflect condition",
            ])

        return base_recs

    def _estimate_repairs(
        self, condition: Optional[str]
    ) -> Dict[str, float]:
        """Estimate repair costs based on condition (Rancho Cucamonga rates)."""
        if condition == "move_in_ready":
            return {
                "deep_cleaning": 500.0,
                "touch_up_paint": 300.0,
                "landscaping_refresh": 400.0,
                "total": 1200.0,
            }
        elif condition == "needs_work":
            return {
                "interior_paint": 3500.0,
                "flooring_update": 5000.0,
                "fixture_replacement": 1500.0,
                "deep_cleaning": 500.0,
                "landscaping": 800.0,
                "total": 11300.0,
            }
        elif condition == "major_repairs":
            return {
                "roof_repair": 8000.0,
                "hvac_update": 6000.0,
                "plumbing_repair": 4000.0,
                "electrical_update": 3500.0,
                "foundation_assessment": 2000.0,
                "total": 23500.0,
            }
        return {"minimal_prep": 800.0, "total": 800.0}

    async def detect_stall(self, state: JorgeSellerState) -> Dict:
        """Detect if the lead is using standard stalling language."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="detect_stall"
        )

        last_msg = state["conversation_history"][-1]["content"].lower() if state["conversation_history"] else ""

        stall_map = {
            "thinking": ["think", "pondering", "consider", "decide"],
            "get_back": ["get back", "later", "next week", "busy"],
            "zestimate": ["zestimate", "zillow", "online value", "estimate says"],
            "agent": ["agent", "realtor", "broker", "with someone"],
        }

        detected_type = None
        for stall_type, keywords in stall_map.items():
            if any(k in last_msg for k in keywords):
                detected_type = stall_type
                break

        # Emit conversation event for stall detection
        if detected_type:
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="stall_detected",
                message=f"Stall type detected: {detected_type}",
            )

        return {"stall_detected": detected_type is not None, "detected_stall_type": detected_type}

    async def select_strategy(self, state: JorgeSellerState) -> Dict:
        """
        Enhanced strategy selection with Track 3.1 Predictive Intelligence.

        Maintains Jorge's confrontational methodology while adding:
        - Journey progression analysis for strategic timing
        - Behavioral pattern recognition for optimal approach
        - Market context injection for enhanced effectiveness
        - Conversion probability-driven decision making
        """
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="select_strategy_enhanced",
        )

        lead_id = state["lead_id"]
        pcs = state["psychological_commitment"]

        # FRIENDLY APPROACH: Jorge's helpful consultation foundation
        # Check for listing prep routing (qualified + address + listing_prep stage)
        if (
            state.get("is_qualified")
            and state.get("property_address")
            and state.get("current_journey_stage") == "listing_prep"
        ):
            base_strategy = {"current_tone": "ENTHUSIASTIC", "next_action": "listing_prep"}
        elif state["stall_detected"]:
            base_strategy = {"current_tone": "UNDERSTANDING", "next_action": "respond"}
        elif pcs < 30:
            # Low commitment = Supportive approach (help them understand)
            base_strategy = {"current_tone": "EDUCATIONAL", "next_action": "respond"}
        elif pcs >= 70:
            # High commitment = Enthusiastic support
            base_strategy = {"current_tone": "ENTHUSIASTIC", "next_action": "respond"}
        else:
            base_strategy = {"current_tone": "CONSULTATIVE", "next_action": "respond"}

        try:
            # TRACK 3.1 ENHANCEMENT: Predictive Intelligence Layer
            logger.info(f"Applying Track 3.1 predictive intelligence for lead {lead_id}")

            # Get comprehensive predictive analysis
            journey_analysis = await self.ml_analytics.predict_lead_journey(lead_id)
            conversion_analysis = await self.ml_analytics.predict_conversion_probability(
                lead_id, state.get("current_journey_stage", "qualification")
            )
            touchpoint_analysis = await self.ml_analytics.predict_optimal_touchpoints(lead_id)

            # BEHAVIORAL ENHANCEMENT: Adjust strategy based on response patterns
            enhanced_strategy = await self._apply_behavioral_intelligence(
                base_strategy, journey_analysis, conversion_analysis, touchpoint_analysis, state
            )

            # MARKET TIMING ENHANCEMENT: Add urgency and timing context
            final_strategy = await self._apply_market_timing_intelligence(
                enhanced_strategy, journey_analysis, conversion_analysis, state
            )

            # Emit enhanced conversation event with predictive context
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="strategy_selected_enhanced",
                message=f"Jorge tone: {final_strategy['current_tone']} (PCS: {pcs}) [Track 3.1: Conv={journey_analysis.conversion_probability:.2f}, Pattern={touchpoint_analysis.response_pattern}]",
            )

            # Emit Track 3.1 predictive insights event
            await self.event_publisher.publish_bot_status_update(
                bot_type="jorge-seller",
                contact_id=state["lead_id"],
                status="enhanced",
                current_step="predictive_analysis_complete",
                additional_data={
                    "conversion_probability": journey_analysis.conversion_probability,
                    "stage_progression_velocity": journey_analysis.stage_progression_velocity,
                    "response_pattern": touchpoint_analysis.response_pattern,
                    "urgency_score": conversion_analysis.urgency_score,
                    "optimal_action": conversion_analysis.optimal_action,
                    "enhancement_applied": True,
                    "processing_time_ms": (
                        journey_analysis.processing_time_ms
                        + conversion_analysis.processing_time_ms
                        + touchpoint_analysis.processing_time_ms
                    ),
                },
            )

            logger.info(
                f"Track 3.1 enhanced strategy for {lead_id}: {final_strategy['current_tone']} "
                f"(conv_prob={journey_analysis.conversion_probability:.3f}, "
                f"pattern={touchpoint_analysis.response_pattern})"
            )

            # PHASE 3.3 ENHANCEMENT: Bot Intelligence Middleware Integration
            if state.get("intelligence_available") and state.get("intelligence_context"):
                final_strategy = await self._apply_conversation_intelligence(
                    final_strategy, state["intelligence_context"], state
                )
                logger.info(f"Phase 3.3 intelligence applied to strategy for {lead_id}")

            return final_strategy

        except Exception as e:
            # GRACEFUL FALLBACK: Use Jorge's proven logic if Track 3.1 fails
            logger.warning(f"Track 3.1 enhancement failed for lead {lead_id}, using base strategy: {e}")

            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="strategy_selected",
                message=f"Jorge tone: {base_strategy['current_tone']} (PCS: {pcs}) [Fallback mode]",
            )

            return base_strategy

    async def generate_jorge_response(self, state: JorgeSellerState) -> Dict:
        """Generate the actual response content using Jorge's specific persona."""
        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="generate_response"
        )

        friendly_responses = {
            "thinking": "Totally get it—big decision. What's the main thing holding you back? Happy to pull numbers if that helps.",
            "get_back": "No rush! Has anything changed with your timeline? I can send fresh comps if useful.",
            "zestimate": "Zillow can't walk through your house! Want to see what neighbors actually sold for? Real numbers might surprise you.",
            "agent": "Great you have someone! Happy to share comps from your area—could be useful for your agent too.",
            "price": "Pricing is tricky. Want me to pull recent sales nearby? Real data beats guessing every time.",
            "timeline": "Makes sense. What's driving your timeline—market, a move, or something else?",
        }

        tone_instructions = {
            "consultative": "Be helpful and supportive. Understand their concerns and provide guidance.",
            "educational": "Share knowledge patiently. Help them understand their options without pressure.",
            "understanding": "Show empathy and patience. Address their concerns with care and expertise.",
            "enthusiastic": "Share their excitement while staying professional. Guide them toward success.",
            "supportive": "Provide comfort and reassurance. Help them feel confident in their decisions.",
        }

        # Use A/B test variant from state (assigned in process_seller_message)
        tone_variant = state.get("tone_variant")
        if not tone_variant:
            seller_id = state.get("lead_id", "unknown")
            try:
                tone_variant = await self.ab_testing.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, seller_id)
            except (KeyError, ValueError):
                tone_variant = "empathetic"

        # Phase 1.2: Get seller persona classification
        seller_persona = state.get("seller_persona", {})
        persona_type = seller_persona.get("persona_type", "Traditional")
        persona_confidence = seller_persona.get("confidence", 0.0)

        # Persona-specific response guidance
        persona_guidance = {
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
        Tone Mode: {state["current_tone"]} ({tone_instructions.get(state["current_tone"], "Be helpful and professional")})
        Tone style: {tone_variant}
        Conversation Context: {state["detected_stall_type"] or "None"}
        FRS Classification: {state["intent_profile"].frs.classification}
        Seller Type: {persona_type} (confidence: {persona_confidence:.0%})

        {persona_guidance.get(persona_type, "")}

        TASK: Generate a helpful, friendly response that builds trust and provides value.
        Tailor your response to the seller's persona type above.
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

        if state["stall_detected"] and state["detected_stall_type"] in friendly_responses:
            prompt += f"\nSUGGESTED HELPFUL RESPONSE: {friendly_responses[state['detected_stall_type']]}"

        # PHASE 3.3 ENHANCEMENT: Apply Bot Intelligence for Enhanced Responses
        if state.get("intelligence_available") and state.get("intelligence_context"):
            prompt = await self._enhance_prompt_with_intelligence(prompt, state["intelligence_context"], state)

        response = await self.claude.analyze_with_context(prompt)
        content = (
            response.get("content")
            or response.get("analysis")
            or "Are we selling this property or just talking about it?"
        )

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
            bot_type="jorge-seller", contact_id=state["lead_id"], status="active", current_step="awaiting_response"
        )

        return {"response_content": content}

    async def recalculate_pcs_node(self, state: JorgeSellerState) -> Dict:
        """
        Recalculate PCS dynamically based on conversation flow.
        Called after each message to track engagement evolution.
        """
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="recalculate_pcs"
        )

        logger.info(f"Recalculating PCS for {state['lead_name']}")

        # Get current PCS
        current_pcs = state.get("psychological_commitment", 0.0)
        conversation_history = state.get("conversation_history", [])

        # Get last user message
        user_messages = [msg for msg in conversation_history if msg.get("role") == "user"]
        last_message = user_messages[-1].get("content", "") if user_messages else ""

        # Recalculate PCS using seller psychology analyzer
        pcs_result = await self.seller_psychology_analyzer.recalculate_pcs(
            current_pcs=current_pcs,
            conversation_history=conversation_history,
            last_message=last_message,
        )

        updated_pcs = pcs_result["updated_pcs"]
        delta = pcs_result["delta"]
        trend = pcs_result["trend"]
        engagement_metrics = pcs_result["engagement_metrics"]

        logger.info(
            f"PCS updated for {state['lead_name']}: {current_pcs:.1f} → {updated_pcs:.1f} "
            f"(Δ{delta:+.1f}, trend: {trend})"
        )

        # Update intent_profile with new PCS
        intent_profile = state.get("intent_profile")
        if intent_profile:
            from ghl_real_estate_ai.models.lead_scoring import PsychologicalCommitmentScore

            # Create updated PCS object
            updated_pcs_obj = PsychologicalCommitmentScore(
                total_score=updated_pcs,
                response_velocity_score=intent_profile.pcs.response_velocity_score,
                message_length_score=intent_profile.pcs.message_length_score,
                question_depth_score=intent_profile.pcs.question_depth_score,
                objection_handling_score=intent_profile.pcs.objection_handling_score,
                call_acceptance_score=intent_profile.pcs.call_acceptance_score,
            )

            # Update intent profile
            from ghl_real_estate_ai.models.lead_scoring import LeadIntentProfile

            updated_profile = LeadIntentProfile(
                lead_id=intent_profile.lead_id,
                frs=intent_profile.frs,
                pcs=updated_pcs_obj,
                lead_type=intent_profile.lead_type,
                market_context=intent_profile.market_context,
                next_best_action=intent_profile.next_best_action,
            )

            # Sync updated PCS to GHL custom field
            try:
                if hasattr(self, "ghl_client") and self.ghl_client:
                    contact_id = state.get("lead_id")
                    await self.ghl_client.update_contact(
                        contact_id=contact_id,
                        updates={"custom_fields": {"pcs": str(int(updated_pcs))}},
                    )
                    logger.info(f"Synced PCS={updated_pcs:.1f} to GHL for contact {contact_id}")
            except Exception as e:
                logger.warning(f"Failed to sync PCS to GHL: {e}")

            # Emit event for PCS update
            await self.event_publisher.publish_conversation_update(
                conversation_id=f"jorge_{state['lead_id']}",
                lead_id=state["lead_id"],
                stage="pcs_updated",
                message=f"PCS: {current_pcs:.1f} → {updated_pcs:.1f} (trend: {trend})",
            )

            return {
                "intent_profile": updated_profile,
                "psychological_commitment": updated_pcs,
                "pcs_trend": trend,
                "pcs_delta": delta,
                "engagement_metrics": engagement_metrics,
            }

        return {"psychological_commitment": updated_pcs}


    async def execute_follow_up(self, state: JorgeSellerState) -> Dict:
        """Execute automated follow-up for unresponsive or lukewarm sellers."""
        follow_up_count = state.get("follow_up_count", 0) + 1

        # Update bot status
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="execute_follow_up"
        )

        logger.info(f"Executing follow-up for {state['lead_name']} (Attempt {follow_up_count})")

        # Follow-up scripts based on previous stage
        follow_ups = {
            "qualification": "Checking back—did you ever decide on a timeline for {address}?",
            "valuation_defense": "I've updated the comps for your neighborhood. Zillow is still high. Ready for the truth?",
            "listing_prep": "The photographer is in your area Thursday. Should I book him for your place?",
        }

        stage = state.get("current_journey_stage", "qualification")
        template = follow_ups.get(stage, "Still interested in selling {address} or should I close the file?")
        follow_up_message = template.format(address=state.get("property_address", "your property"))

        # Emit conversation event for follow-up
        await self.event_publisher.publish_conversation_update(
            conversation_id=f"jorge_{state['lead_id']}",
            lead_id=state["lead_id"],
            stage="follow_up_sent",
            message=f"Follow-up #{follow_up_count}: {follow_up_message[:50]}...",
        )

        # Mark bot as completed for this cycle
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="completed", current_step="follow_up_sent"
        )

        # In prod, send via GHL
        return {"response_content": follow_up_message, "follow_up_count": follow_up_count}

    # ================================
    # ENHANCED FEATURE METHODS
    # ================================

    # --- Adaptive Intelligence Methods ---

    async def adaptive_strategy_selection(self, state: JorgeSellerState) -> Dict:
        """Enhanced strategy selection with adaptive questioning"""
        await self.event_publisher.publish_bot_status_update(
            bot_type="unified-jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="adaptive_strategy",
        )

        pcs = state["psychological_commitment"]
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Enhanced strategy logic
        if pcs > 70:  # High commitment - fast track
            strategy = {"current_tone": "DIRECT", "next_action": "fast_track", "adaptive_mode": "calendar_focused"}
        elif state["stall_detected"]:
            strategy = {
                "current_tone": "UNDERSTANDING",
                "next_action": "respond",
                "adaptive_mode": "supportive_guidance",
            }
        elif context.get("adaptation_count", 0) > 2:  # Multiple adaptations
            strategy = {"current_tone": "HONEST", "next_action": "respond", "adaptive_mode": "clarity_focused"}
        else:
            strategy = {
                "current_tone": "CONSULTATIVE",
                "next_action": "respond",
                "adaptive_mode": "standard_qualification",
            }

        return strategy

    async def generate_adaptive_response(self, state: JorgeSellerState) -> Dict:
        """Generate response using adaptive question selection"""
        await self.event_publisher.publish_bot_status_update(
            bot_type="unified-jorge-seller",
            contact_id=state["lead_id"],
            status="processing",
            current_step="generate_adaptive_response",
        )

        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Select optimal question using adaptive engine
        next_question = await self.question_engine.select_next_question(state, context)
        self.workflow_stats["adaptive_question_selections"] += 1

        # Use A/B test variant from state (assigned in process_seller_message)
        tone_variant = state.get("tone_variant")
        if not tone_variant:
            seller_id = state.get("lead_id", "unknown")
            try:
                tone_variant = await self.ab_testing.get_variant(ABTestingService.RESPONSE_TONE_EXPERIMENT, seller_id)
            except (KeyError, ValueError):
                tone_variant = "empathetic"

        # Enhanced prompt with adaptive context
        prompt = f"""
        You are Jorge Salas, helpful real estate advisor and relationship builder.

        CURRENT CONTEXT:
        Lead: {state["lead_name"]}
        Adaptive Mode: {state.get("adaptive_mode", "standard")}
        Tone: {state["current_tone"]}
        Tone style: {tone_variant}
        PCS Score: {state["psychological_commitment"]}
        FRS Classification: {state["intent_profile"].frs.classification}
        Previous Adaptations: {context.get("adaptation_count", 0)}

        RECOMMENDED QUESTION: {next_question}

        TASK: Deliver the question in Jorge's helpful, consultative style that builds trust and rapport.
        """

        response = await self.claude.analyze_with_context(prompt)
        content = response.get("content", next_question)

        return {"response_content": content, "adaptive_question_used": next_question, "adaptation_applied": True}

    async def update_conversation_memory(self, state: JorgeSellerState) -> Dict:
        """Update conversation memory with new interaction patterns"""
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)

        # Update context with new information
        update = {
            "last_scores": {"frs": state["intent_profile"].frs.total_score, "pcs": state["psychological_commitment"]},
            "last_interaction_time": datetime.now(timezone.utc),
            "adaptation_count": context.get("adaptation_count", 0) + 1,
            "response_patterns": {
                "adaptive_mode": state.get("adaptive_mode"),
                "question_used": state.get("adaptive_question_used"),
            },
        }

        await self.conversation_memory.update_context(conversation_id, update)
        return {"memory_updated": True}

    def _route_adaptive_action(self, state: JorgeSellerState) -> Literal["respond", "follow_up", "fast_track", "end"]:
        """Enhanced routing with fast-track capability"""
        if state.get("adaptive_mode") == "calendar_focused":
            return "fast_track"
        if state["next_action"] == "follow_up":
            return "follow_up"
        if state["next_action"] == "end":
            return "end"
        return "respond"

    # --- Progressive Skills Methods ---

    async def _execute_progressive_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Progressive skills-based qualification (68% token reduction)"""
        if not self.skills_manager:
            return await self._execute_traditional_qualification(lead_data)

        start_time = time.time()

        # Enhanced discovery context with Rancho Cucamonga market intelligence
        discovery_context = {
            "lead_name": lead_data.get("lead_name"),
            "last_message": lead_data.get("last_message", ""),
            "interaction_count": lead_data.get("interaction_count", 1),
            "lead_source": lead_data.get("lead_source"),
            "property_address": lead_data.get("property_address"),
            "seller_temperature": lead_data.get("seller_temperature", "cold"),
            "frs_score": lead_data.get("frs_score", 0),
            "pcs_score": lead_data.get("pcs_score", 0),
            "stall_history": lead_data.get("stall_count", 0),
        }

        # Rancho Cucamonga market context injection (68% token reduction enhancement)
        if self._is_rancho_cucamonga_property(lead_data.get("property_address")):
            discovery_context["market_context"] = "rancho_cucamonga"
            discovery_context["rancho_cucamonga_neighborhood"] = self._detect_rancho_cucamonga_neighborhood(
                lead_data.get("property_address")
            )

        discovery_result = await self.skills_manager.discover_skills(
            context=discovery_context, task_type="jorge_seller_qualification"
        )

        skill_name = discovery_result["skills"][0]
        confidence = discovery_result["confidence"]

        # Execution phase (169 tokens average)
        skill_result = await self.skills_manager.execute_skill(skill_name=skill_name, context=discovery_context)

        # Track performance
        total_tokens = 103 + skill_result.get("tokens_estimated", 169)

        if self.token_tracker:
            await self.token_tracker.record_usage(
                task_id=f"jorge_progressive_{int(time.time())}",
                tokens_used=total_tokens,
                task_type="jorge_qualification",
                user_id=lead_data.get("lead_id", "unknown"),
                model="claude-sonnet-4",
                approach="progressive",
                skill_name=skill_name,
                confidence=confidence,
            )

        execution_time = time.time() - start_time
        self.workflow_stats["progressive_skills_usage"] += 1
        self.workflow_stats["token_savings"] += 853 - total_tokens  # vs baseline

        return {
            "qualification_method": "progressive_skills",
            "skill_used": skill_name,
            "confidence": confidence,
            "tokens_used": total_tokens,
            "baseline_tokens": 853,
            "token_reduction": ((853 - total_tokens) / 853) * 100,
            "qualification_summary": skill_result.get("response_content", ""),
            "is_qualified": confidence > 0.7,
            "seller_temperature": self._confidence_to_temperature(confidence),
            "execution_time": execution_time,
            "market_context": discovery_context.get("market_context"),
            "rancho_cucamonga_neighborhood": discovery_context.get("rancho_cucamonga_neighborhood"),
        }

    def _is_rancho_cucamonga_property(self, address: Optional[str]) -> bool:
        """Detect if property is in Rancho Cucamonga market for progressive skills enhancement."""
        if not address:
            return False
        address_lower = address.lower()
        return any(
            [
                "rancho_cucamonga" in address_lower,
                "tx 78" in address_lower,
                " atx" in address_lower,
                "rancho_cucamonga, ca" in address_lower,
            ]
        )

    def _detect_rancho_cucamonga_neighborhood(self, address: Optional[str]) -> Optional[str]:
        """Extract Rancho Cucamonga neighborhood from address for market-specific skills."""
        if not address:
            return None

        rancho_cucamonga_neighborhoods = {
            "alta_loma": ["alta_loma", "west lake hills"],
            "tarrytown": ["tarrytown"],
            "mueller": ["mueller"],
            "central_rc": ["central_rc", "west 6th", "rainey"],
            "south_congress": ["soco", "south congress", "zilker"],
            "east_rancho_cucamonga": ["east rancho_cucamonga", "cherrywood"],
            "etiwanda": ["cedar park"],
            "victoria_gardens": ["round rock"],
            "day_creek": ["day_creek"],
            "lakeway": ["lakeway"],
            "bee_cave": ["bee cave"],
        }

        address_lower = address.lower()
        for neighborhood, keywords in rancho_cucamonga_neighborhoods.items():
            if any(keyword in address_lower for keyword in keywords):
                return neighborhood

        return "central_rancho_cucamonga"  # Default for Rancho Cucamonga addresses

    async def _execute_traditional_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Traditional full-context qualification"""
        qualification_prompt = f"""
        You are Jorge Salas analyzing a seller lead with a helpful, consultative approach.
        Use friendly qualification to understand motivation and provide guidance.

        Lead Information:
        - Name: {lead_data.get("lead_name")}
        - Property: {lead_data.get("property_address")}
        - Last Message: {lead_data.get("last_message")}
        - Source: {lead_data.get("lead_source")}

        Determine:
        1. Seller motivation (1-10 scale)
        2. Timeline urgency
        3. Price sensitivity
        4. Jorge's recommended approach (CONSULTATIVE/EDUCATIONAL/SUPPORTIVE)
        """

        response = await self.claude.analyze_with_context(qualification_prompt, context=lead_data)

        return {
            "qualification_method": "traditional",
            "tokens_used": 853,  # Estimated baseline
            "qualification_summary": response.get("content", ""),
            "is_qualified": True,  # Simplified
            "seller_temperature": "lukewarm",
        }

    # --- Agent Mesh Integration Methods ---

    async def _create_mesh_qualification_task(self, lead_data: Dict[str, Any]) -> Optional[str]:
        """Create mesh task for Jorge qualification"""
        if not self.mesh_coordinator:
            return None

        qualification_task = AgentTask(
            task_id=str(uuid4()),
            task_type="jorge_seller_qualification",
            priority=TaskPriority.HIGH if lead_data.get("urgent", False) else TaskPriority.NORMAL,
            capabilities_required=[AgentCapability.LEAD_QUALIFICATION, AgentCapability.CONVERSATION_ANALYSIS],
            payload=lead_data,
            created_at=datetime.now(timezone.utc),
            deadline=None,
            max_cost=5.0,
            requester_id="jorge_bot_unified",
        )

        mesh_task_id = await self.mesh_coordinator.submit_task(qualification_task)
        self.workflow_stats["mesh_orchestrations"] += 1
        return mesh_task_id

    async def _orchestrate_supporting_tasks(
        self, lead_data: Dict[str, Any], qualification_analysis: Dict[str, Any], parent_task_id: str
    ) -> List[str]:
        """Orchestrate supporting tasks through agent mesh"""
        if not self.mesh_coordinator:
            return []

        orchestrated_tasks = []

        try:
            # Property valuation if address provided
            if lead_data.get("property_address"):
                valuation_task = AgentTask(
                    task_id=str(uuid4()),
                    task_type="property_valuation",
                    priority=TaskPriority.NORMAL,
                    capabilities_required=[AgentCapability.MARKET_INTELLIGENCE],
                    payload={
                        "address": lead_data["property_address"],
                        "parent_task": parent_task_id,
                        "jorge_commission": self.config.commission_rate,
                    },
                    created_at=datetime.now(timezone.utc),
                    deadline=None,
                    max_cost=2.0,
                    requester_id="jorge_bot_unified",
                )

                valuation_task_id = await self.mesh_coordinator.submit_task(valuation_task)
                orchestrated_tasks.append(valuation_task_id)

            return orchestrated_tasks

        except Exception as e:
            logger.error(f"Task orchestration failed: {e}")
            return orchestrated_tasks

    # --- MCP Integration Methods ---

    async def _enrich_with_mcp_data(self, lead_data: Dict[str, Any], qualification: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich qualification with MCP data sources"""
        if not self.mcp_client:
            return {"mcp_enrichment_applied": False}

        enrichment_data = {}
        mcp_calls = 0

        try:
            # Check if lead exists in CRM
            if lead_data.get("email") or lead_data.get("phone"):
                crm_search_result = await self.mcp_client.call_tool(
                    "ghl-crm",
                    "search_contacts",
                    {"query": lead_data.get("email", lead_data.get("phone", "")), "limit": 1},
                )
                mcp_calls += 1

                if crm_search_result.get("contacts"):
                    enrichment_data["existing_contact"] = crm_search_result["contacts"][0]
                    enrichment_data["is_return_lead"] = True
                else:
                    enrichment_data["is_return_lead"] = False

            # Get property data if address provided
            if lead_data.get("property_address"):
                property_search = await self.mcp_client.call_tool(
                    "mls-data",
                    "search_properties",
                    {"city": self._extract_city(lead_data["property_address"]), "limit": 5},
                )
                mcp_calls += 1

                enrichment_data["local_market_data"] = property_search.get("properties", [])

        except Exception as e:
            logger.error(f"MCP enrichment failed: {e}")
            enrichment_data["enrichment_error"] = str(e)

        self.workflow_stats["mcp_calls"] += mcp_calls

        return {
            "mcp_enrichment": enrichment_data,
            "mcp_calls": mcp_calls,
            "mcp_enrichment_applied": len(enrichment_data) > 0,
        }

    async def _sync_to_crm_via_mcp(self, lead_data: Dict[str, Any], qualification_analysis: Dict[str, Any]):
        """Sync qualification results to CRM using MCP protocol"""
        if not self.mcp_client:
            return

        try:
            # Update contact with qualification data
            await self.mcp_client.call_tool(
                "ghl-crm",
                "update_contact",
                {
                    "contact_id": lead_data["lead_id"],
                    "custom_fields": {
                        "jorge_qualification_score": qualification_analysis.get("qualification_score", 0),
                        "jorge_temperature": qualification_analysis.get("temperature", "cold"),
                        "jorge_qualified_date": datetime.now(timezone.utc).isoformat(),
                        "jorge_approach": qualification_analysis.get("jorge_strategy", "standard"),
                    },
                },
            )

            logger.info(f"CRM sync complete for lead {lead_data['lead_id']} via MCP")

        except Exception as e:
            logger.error(f"MCP CRM sync failed: {e}")

    # --- Utility Methods ---

    def _confidence_to_temperature(self, confidence: float) -> str:
        """Convert confidence score to Jorge's temperature scale"""
        if confidence >= 0.8:
            return "hot"
        elif confidence >= 0.6:
            return "warm"
        elif confidence >= 0.4:
            return "lukewarm"
        else:
            return "cold"

    def _extract_city(self, address: str) -> str:
        """Extract city from address string"""
        parts = address.split(",")
        return parts[-2].strip() if len(parts) > 2 else "Phoenix"

    # --- Helper Logic ---

    def _classify_temperature(self, profile) -> str:
        """Classify seller temperature based on intent scores."""
        total_score = profile.pcs.total_score + profile.frs.total_score

        if total_score >= 75:
            return "hot"
        elif total_score >= 50:
            return "warm"
        else:
            return "cold"

    def _route_seller_action(
        self, state: JorgeSellerState
    ) -> Literal["respond", "follow_up", "listing_prep", "end"]:
        """Determine if we should respond immediately or queue a follow-up."""
        next_action = state.get("next_action", "respond")
        if next_action == "follow_up":
            return "follow_up"
        if next_action == "end":
            return "end"
        if next_action == "listing_prep":
            return "listing_prep"
        return "respond"

    def _route_after_stall_detection(
        self, state: JorgeSellerState
    ) -> Literal["defend_valuation", "select_strategy"]:
        """Route to valuation defense if Zestimate stall detected with CMA data."""
        if (
            state.get("detected_stall_type") == "zestimate"
            and state.get("cma_report") is not None
        ):
            return "defend_valuation"
        return "select_strategy"

    # ================================
    # TRACK 3.1: PREDICTIVE INTELLIGENCE ENHANCEMENT METHODS
    # ================================

    async def _apply_behavioral_intelligence(
        self, base_strategy: Dict, journey_analysis, conversion_analysis, touchpoint_analysis, state: JorgeSellerState
    ) -> Dict:
        """
        Apply behavioral intelligence to enhance Jorge's confrontational approach.

        Uses Track 3.1 behavioral patterns to optimize strategy effectiveness while
        maintaining Jorge's proven confrontational methodology.
        """
        enhanced_strategy = base_strategy.copy()

        # BEHAVIORAL PATTERN ANALYSIS
        response_pattern = touchpoint_analysis.response_pattern
        conversion_prob = journey_analysis.conversion_probability
        stage_velocity = journey_analysis.stage_progression_velocity

        # ENHANCEMENT 1: Response Pattern Optimization
        if response_pattern == "fast" and conversion_prob > 0.6:
            # Fast responders with high conversion probability = MORE ENTHUSIASTIC
            if enhanced_strategy["current_tone"] == "CONSULTATIVE":
                enhanced_strategy["current_tone"] = "ENTHUSIASTIC"
                enhanced_strategy["enhancement_reason"] = "fast_responder_high_conversion"
            elif enhanced_strategy["current_tone"] == "EDUCATIONAL":
                enhanced_strategy["current_tone"] = "CONSULTATIVE"
                enhanced_strategy["enhancement_reason"] = "fast_responder_upgrade"

        elif response_pattern == "slow" and conversion_prob < 0.3:
            # Slow responders with low conversion = MORE EDUCATIONAL
            if enhanced_strategy["current_tone"] == "CONSULTATIVE":
                enhanced_strategy["current_tone"] = "EDUCATIONAL"
                enhanced_strategy["enhancement_reason"] = "slow_responder_education_needed"
            elif enhanced_strategy["current_tone"] == "ENTHUSIASTIC":
                enhanced_strategy["current_tone"] = "CONSULTATIVE"
                enhanced_strategy["enhancement_reason"] = "slow_responder_gentle_approach"

        # ENHANCEMENT 2: Stage Progression Velocity
        if stage_velocity > 0.8:
            # Fast-moving leads = MAINTAIN MOMENTUM WITH ENTHUSIASM
            enhanced_strategy["enthusiasm_boost"] = True
            enhanced_strategy["momentum_factor"] = "high"
        elif stage_velocity < 0.3:
            # Stalled progression = PROVIDE MORE SUPPORT
            if enhanced_strategy["current_tone"] != "EDUCATIONAL":
                enhanced_strategy["support_increase"] = True
                enhanced_strategy["educational_focus"] = True

        # ENHANCEMENT 3: Conversion Probability Context
        if conversion_prob > 0.7:
            # High conversion probability = MAINTAIN CURRENT APPROACH
            enhanced_strategy["confidence_level"] = "high"
            enhanced_strategy["approach_validation"] = "maintain_course"
        elif conversion_prob < 0.3 and enhanced_strategy["current_tone"] != "EDUCATIONAL":
            # Low conversion probability = PROVIDE MORE EDUCATION
            enhanced_strategy["education_emphasis"] = True

        # Track behavioral intelligence application
        enhanced_strategy["track3_behavioral_applied"] = True
        enhanced_strategy["behavioral_factors"] = {
            "response_pattern": response_pattern,
            "conversion_probability": conversion_prob,
            "stage_progression_velocity": stage_velocity,
        }

        logger.info(
            f"Applied behavioral intelligence for {state['lead_id']}: "
            f"{base_strategy['current_tone']} → {enhanced_strategy['current_tone']}"
        )

        return enhanced_strategy

    async def _apply_market_timing_intelligence(
        self, strategy: Dict, journey_analysis, conversion_analysis, state: JorgeSellerState
    ) -> Dict:
        """
        Apply market timing intelligence to enhance Jorge's strategic effectiveness.

        Incorporates market context and timing urgency to optimize confrontational approach.
        """
        final_strategy = strategy.copy()

        urgency_score = conversion_analysis.urgency_score
        optimal_action = conversion_analysis.optimal_action
        stage_bottlenecks = journey_analysis.stage_bottlenecks

        # MARKET TIMING ENHANCEMENT 1: Urgency-Based Support
        if urgency_score > 0.8:
            # HIGH URGENCY = MAXIMUM SUPPORT AND ENTHUSIASM
            final_strategy["market_urgency"] = "high"

            if final_strategy["current_tone"] == "CONSULTATIVE":
                final_strategy["current_tone"] = "ENTHUSIASTIC"
                final_strategy["timing_reason"] = "high_market_urgency"
            elif final_strategy["current_tone"] == "EDUCATIONAL":
                final_strategy["current_tone"] = "CONSULTATIVE"
                final_strategy["timing_reason"] = "urgency_upgrade_support"

        elif urgency_score < 0.3:
            # LOW URGENCY = PATIENT EDUCATION
            if final_strategy["current_tone"] == "ENTHUSIASTIC":
                final_strategy["current_tone"] = "CONSULTATIVE"
                final_strategy["timing_reason"] = "low_urgency_patience"

        # MARKET TIMING ENHANCEMENT 2: Optimal Action Integration
        jorge_action_mapping = {
            "schedule_qualification_call": "CONSULTATIVE",
            "schedule_appointment": "ENTHUSIASTIC",
            "clarify_requirements": "EDUCATIONAL",
            "nurture_relationship": "SUPPORTIVE",  # Build relationships over time
            "follow_up_contact": "CONSULTATIVE",
        }

        suggested_tone = jorge_action_mapping.get(optimal_action)
        if suggested_tone and suggested_tone != final_strategy["current_tone"]:
            # Adjust to maintain helpfulness while being effective
            tone_helpfulness = {"EDUCATIONAL": 1, "CONSULTATIVE": 2, "ENTHUSIASTIC": 3, "SUPPORTIVE": 2}

            current_helpfulness = tone_helpfulness.get(final_strategy["current_tone"], 2)
            suggested_helpfulness = tone_helpfulness.get(suggested_tone, 2)

            # Always use the suggested tone that best serves the customer
            final_strategy["current_tone"] = suggested_tone
            final_strategy["action_alignment"] = True
            final_strategy["optimal_action_applied"] = optimal_action

        # MARKET TIMING ENHANCEMENT 3: Bottleneck-Based Strategy
        if "stalled_in_stage" in stage_bottlenecks or "slow_response_time" in stage_bottlenecks:
            # STALLS = SUPPORTIVE BREAKTHROUGH
            if final_strategy["current_tone"] == "CONSULTATIVE":
                final_strategy["current_tone"] = "UNDERSTANDING"
                final_strategy["bottleneck_reason"] = "stage_stall_detected"

        elif "price_misalignment" in stage_bottlenecks:
            # PRICE ISSUES = GENTLE EDUCATION
            final_strategy["current_tone"] = "EDUCATIONAL"
            final_strategy["bottleneck_reason"] = "price_education_needed"

        # Track market timing intelligence application
        final_strategy["track3_timing_applied"] = True
        final_strategy["timing_factors"] = {
            "urgency_score": urgency_score,
            "optimal_action": optimal_action,
            "stage_bottlenecks": stage_bottlenecks,
        }

        # JORGE PHILOSOPHY: Always prioritize customer success and relationship building
        # If Track 3.1 suggests being less helpful, Jorge maintains his caring approach
        if final_strategy.get("suggested_de_escalation"):
            final_strategy["current_tone"] = "SUPPORTIVE"
            final_strategy["jorge_override"] = "always_helpful"

        logger.info(
            f"Applied market timing intelligence for {state['lead_id']}: "
            f"urgency={urgency_score:.2f}, action={optimal_action}"
        )

        return final_strategy

    async def process_seller_message(
        self,
        conversation_id: str,
        user_message: str,
        seller_name: Optional[str] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        seller_phone: Optional[str] = None,
        seller_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
    ) -> SellerBotResponse:
        try:
            _workflow_start = time.time()

            if conversation_history is None:
                conversation_history = []

            conversation_history.append(
                {"role": "user", "content": user_message, "timestamp": datetime.now(timezone.utc).isoformat()}
            )

            # Get A/B test variant for response tone (before workflow)
            try:
                _tone_variant = await self.ab_testing.get_variant(
                    ABTestingService.RESPONSE_TONE_EXPERIMENT, conversation_id
                )
            except (KeyError, ValueError):
                _tone_variant = "empathetic"

            initial_state = {
                "lead_id": conversation_id,
                "lead_name": seller_name or f"Seller {conversation_id}",
                "conversation_history": conversation_history,
                "property_address": None,
                "intent_profile": None,
                "current_tone": "direct",
                "stall_detected": False,
                "detected_stall_type": None,
                "next_action": "respond",
                "response_content": "",
                "psychological_commitment": 0.0,
                "is_qualified": False,
                "current_journey_stage": "qualification",
                "follow_up_count": 0,
                "last_action_timestamp": None,
                "tone_variant": _tone_variant,
            }

            if seller_phone:
                initial_state["seller_phone"] = seller_phone
            if seller_email:
                initial_state["seller_email"] = seller_email
            if metadata:
                initial_state["metadata"] = metadata

            result = await self.workflow.ainvoke(initial_state)

            _workflow_duration_ms = (time.time() - _workflow_start) * 1000

            self.workflow_stats["total_interactions"] += 1

            handoff_signals = {}
            if self.config.jorge_handoff_enabled:
                from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService

                handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            intent_profile = result.get("intent_profile")
            frs_score = 0.0
            pcs_score = 0.0
            if intent_profile:
                frs_score = getattr(getattr(intent_profile, "frs", None), "total_score", 0.0)
                pcs_score = getattr(getattr(intent_profile, "pcs", None), "total_score", 0.0)

            # Phase 1.2: Sync seller persona to GHL (non-blocking)
            seller_persona = result.get("seller_persona")
            if seller_persona and seller_persona.get("persona_type"):
                try:
                    await self._sync_seller_persona_to_ghl(
                        contact_id=conversation_id,
                        persona_type=seller_persona["persona_type"],
                        confidence=seller_persona.get("confidence", 0.0),
                    )
                except Exception as e:
                    logger.warning(f"Failed to sync persona tag (non-blocking): {e}")

            # Record performance metrics
            await self.performance_tracker.track_operation("seller_bot", "process", _workflow_duration_ms, success=True)
            self.metrics_collector.record_bot_interaction("seller", duration_ms=_workflow_duration_ms, success=True)

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

            await self.event_publisher.publish_bot_status_update(
                bot_type="seller-bot",
                contact_id=conversation_id,
                status="completed",
                current_step=result.get("next_action", "unknown"),
            )

            return {
                "response_content": result.get("response_content", ""),
                "lead_id": conversation_id,
                "current_step": result.get("next_action", "unknown"),
                "engagement_status": result.get("current_journey_stage", "qualification"),
                "frs_score": frs_score,
                "pcs_score": pcs_score,
                "handoff_signals": handoff_signals,
                "seller_persona": seller_persona,
                "ab_test": {
                    "experiment_id": ABTestingService.RESPONSE_TONE_EXPERIMENT,
                    "variant": _tone_variant,
                },
            }

        except Exception as e:
            # Record failure metrics
            try:
                _fail_duration = (time.time() - _workflow_start) * 1000
                await self.performance_tracker.track_operation("seller_bot", "process", _fail_duration, success=False)
                self.metrics_collector.record_bot_interaction("seller", duration_ms=_fail_duration, success=False)
            except Exception as ex:
                logger.debug(f"Secondary failure in error metrics recording: {str(ex)}")

            logger.error(f"Error processing seller message for {conversation_id}: {str(e)}")
            return {
                "response_content": "Thanks for reaching out! I'd love to help you with your property. Could you tell me more about what you're looking for?",
                "lead_id": conversation_id,
                "current_step": "error",
                "engagement_status": "error",
                "frs_score": 0.0,
                "pcs_score": 0.0,
                "handoff_signals": {},
            }

    async def _sync_seller_persona_to_ghl(
        self,
        contact_id: str,
        persona_type: str,
        confidence: float,
    ) -> bool:
        """
        Sync seller persona classification to GHL as tags.

        Tags applied:
        - "Investor-Seller" for persona_type == "Investor"
        - "Distressed-Seller" for persona_type == "Distressed"
        - "Traditional-Seller" for persona_type == "Traditional"

        Args:
            contact_id: GHL contact ID
            persona_type: Classified persona type
            confidence: Classification confidence (0.0-1.0)

        Returns:
            True if sync successful, False otherwise
        """
        if not GHL_CLIENT_AVAILABLE:
            logger.warning("GHL client not available, skipping persona tag sync")
            return False

        # Only sync if confidence is above threshold (30%)
        if confidence < 0.3:
            logger.info(f"Skipping persona tag sync for {contact_id} - confidence too low: {confidence:.2f}")
            return False

        try:
            persona_tag = f"{persona_type}-Seller"

            async with EnhancedGHLClient() as ghl:
                # Get existing tags
                contact = await ghl.get_contact(contact_id)
                if not contact:
                    logger.warning(f"Contact {contact_id} not found in GHL")
                    return False

                existing_tags = contact.tags or []

                # Remove old persona tags
                persona_tags = ["Investor-Seller", "Distressed-Seller", "Traditional-Seller"]
                cleaned_tags = [tag for tag in existing_tags if tag not in persona_tags]

                # Add new persona tag
                updated_tags = cleaned_tags + [persona_tag]

                # Update contact with new tags
                from ghl_real_estate_ai.models.ghl_webhook_types import GHLContactUpdatePayload

                update_payload = GHLContactUpdatePayload(tags=updated_tags)
                success = await ghl.update_contact(contact_id, update_payload)

                if success:
                    logger.info(f"Successfully synced persona tag '{persona_tag}' to GHL for contact {contact_id}")
                else:
                    logger.error(f"Failed to update persona tag for contact {contact_id}")

                return success

        except Exception as e:
            logger.error(f"Error syncing persona tag to GHL: {e}")
            return False

    # ================================
    # UNIFIED PROCESSING METHODS
    # ================================

    async def process_seller_with_enhancements(self, lead_data: Dict[str, Any]) -> QualificationResult:
        """
        Process seller through unified workflow with all enabled enhancements.
        This is the primary entry point for the enhanced Jorge Bot.
        """
        start_time = datetime.now(timezone.utc).timestamp() * 1000
        timeline = {}
        self.workflow_stats["total_interactions"] += 1

        try:
            # PHASE 1: Create mesh task if enabled
            mesh_task_id = None
            if self.config.enable_agent_mesh:
                mesh_task_id = await self._create_mesh_qualification_task(lead_data)
                timeline["mesh_task_created"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            # PHASE 2: Execute qualification (progressive or traditional)
            if self.config.enable_progressive_skills:
                qualification_analysis = await self._execute_progressive_qualification(lead_data)
            else:
                qualification_analysis = await self._execute_traditional_qualification(lead_data)

            timeline["qualification_complete"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            # PHASE 3: MCP data enrichment if enabled
            if self.config.enable_mcp_integration:
                enrichment_result = await self._enrich_with_mcp_data(lead_data, qualification_analysis)
                qualification_analysis.update(enrichment_result)
                timeline["mcp_enrichment_complete"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            # PHASE 4: Agent mesh task orchestration if enabled
            orchestrated_tasks = []
            if self.config.enable_agent_mesh and mesh_task_id:
                orchestrated_tasks = await self._orchestrate_supporting_tasks(
                    lead_data, qualification_analysis, mesh_task_id
                )
                timeline["orchestration_complete"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            # PHASE 5: CRM sync via MCP if enabled
            if self.config.enable_mcp_integration:
                await self._sync_to_crm_via_mcp(lead_data, qualification_analysis)
                timeline["crm_sync_complete"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            # PHASE 6: Generate comprehensive result
            result = await self._generate_unified_qualification_result(
                lead_data, qualification_analysis, orchestrated_tasks, mesh_task_id, timeline
            )

            timeline["total_time"] = datetime.now(timezone.utc).timestamp() * 1000 - start_time

            logger.info(
                f"Jorge unified qualification complete: {result.qualification_score:.1f}% in {timeline['total_time']:.0f}ms"
            )

            return result

        except Exception as e:
            logger.error(f"Jorge unified qualification failed: {e}")
            raise

    async def _generate_unified_qualification_result(
        self,
        lead_data: Dict[str, Any],
        qualification_analysis: Dict[str, Any],
        orchestrated_tasks: List[str],
        mesh_task_id: Optional[str],
        timeline: Dict[str, float],
    ) -> QualificationResult:
        """Generate comprehensive qualification result with all enhancement metadata"""

        # Calculate costs and metrics
        tokens_used = qualification_analysis.get("tokens_used", 0)
        cost_incurred = tokens_used * self.config.cost_per_token

        # Determine next actions
        next_actions = await self._determine_jorge_next_actions(qualification_analysis)

        # Build comprehensive result
        return QualificationResult(
            lead_id=lead_data["lead_id"],
            qualification_score=qualification_analysis.get(
                "qualification_score", qualification_analysis.get("confidence", 0) * 100
            ),
            frs_score=qualification_analysis.get("frs_score", 0),
            pcs_score=qualification_analysis.get("pcs_score", 0),
            temperature=qualification_analysis.get("seller_temperature", "cold"),
            next_actions=next_actions,
            confidence=qualification_analysis.get("confidence", 0),
            tokens_used=tokens_used,
            cost_incurred=cost_incurred,
            # Enhancement metadata
            progressive_skills_applied=self.config.enable_progressive_skills
            and qualification_analysis.get("qualification_method") == "progressive_skills",
            mesh_task_id=mesh_task_id,
            orchestrated_tasks=orchestrated_tasks,
            mcp_enrichment_applied=qualification_analysis.get("mcp_enrichment_applied", False),
            adaptive_questioning_used=self.config.enable_adaptive_questioning,
            timeline_ms=timeline,
        )

    async def _determine_jorge_next_actions(self, qualification_analysis: Dict[str, Any]) -> List[str]:
        """Determine Jorge's next actions based on qualification"""
        temperature = qualification_analysis.get("seller_temperature", "cold")
        qualification_score = qualification_analysis.get(
            "qualification_score", qualification_analysis.get("confidence", 0) * 100
        )
        is_return_lead = qualification_analysis.get("mcp_enrichment", {}).get("is_return_lead", False)

        actions = []

        if is_return_lead:
            actions.append("Apply return lead relationship-building script")

        if temperature == "hot" and qualification_score >= 75:
            actions.extend(
                [
                    "Schedule immediate listing appointment",
                    "Send Jorge's 6% commission structure",
                    "Provide market analysis with value proposition",
                ]
            )
        elif temperature == "warm" and qualification_score >= 50:
            actions.extend(
                [
                    "Schedule follow-up call within 48 hours",
                    "Send market statistics and Jorge's track record",
                    "Prepare preliminary home value estimate",
                ]
            )
        else:
            actions.extend(["Add to 30-day nurture sequence", "Monitor for re-engagement signals"])

        return actions

    # ================================
    # PHASE 3.3 INTELLIGENCE HELPER METHODS
    # ================================

    async def _apply_conversation_intelligence(
        self, strategy: Dict[str, Any], intelligence_context: "BotIntelligenceContext", state: JorgeSellerState
    ) -> Dict[str, Any]:
        """
        Apply conversation intelligence to refine Jorge's strategy.

        Uses objection detection and sentiment analysis to adjust approach while
        maintaining Jorge's friendly, relationship-focused methodology.
        """
        try:
            conversation_intel = intelligence_context.conversation_intelligence

            # Analyze objections for supportive breakthrough opportunities
            if conversation_intel.objections_detected:
                primary_objection = conversation_intel.objections_detected[0]
                objection_type = primary_objection.get("type", "unknown")
                severity = primary_objection.get("severity", 0.5)

                logger.info(f"Jorge addressing {objection_type} concern with care (severity: {severity})")

                # Jorge's helpful response to common concerns
                if objection_type in ["price", "pricing"] and severity > 0.6:
                    # Strong price objection - provide education and support
                    strategy["support_angle"] = "price_education_with_care"
                    strategy["talking_points"] = primary_objection.get("suggested_responses", [])
                elif objection_type in ["timing", "timeline"] and severity > 0.5:
                    # Timeline concern - understand their needs
                    strategy["support_angle"] = "timeline_understanding"
                elif objection_type in ["trust", "agent"]:
                    # Trust/agent concern - build relationships
                    strategy["current_tone"] = "SUPPORTIVE"  # Build trust through care

            # Adjust approach based on sentiment
            sentiment = conversation_intel.overall_sentiment
            if sentiment < -0.3:
                # Negative sentiment - provide more care and understanding
                strategy["care_modifier"] = "extra_supportive"
            elif sentiment > 0.3:
                # Positive sentiment - opportunity for enthusiastic engagement
                strategy["enthusiasm_modifier"] = "confident_partnership"

            # Use response recommendations for coaching opportunities
            if conversation_intel.response_recommendations:
                best_response = conversation_intel.response_recommendations[0]
                strategy["recommended_response"] = best_response.get("response_text")
                strategy["recommended_tone"] = best_response.get("tone", strategy.get("current_tone"))

            strategy["intelligence_enhanced"] = True
            return strategy

        except Exception as e:
            logger.warning(f"Conversation intelligence application failed: {e}")
            return strategy

    async def _enhance_prompt_with_intelligence(
        self, base_prompt: str, intelligence_context: "BotIntelligenceContext", state: JorgeSellerState
    ) -> str:
        """
        Enhance Claude prompt with intelligence context for better responses.

        Adds property recommendations, objection handling guidance, and
        personalized approach suggestions while maintaining Jorge's style.
        """
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

    # ================================
    # FACTORY METHODS AND UTILITIES
    # ================================

    @classmethod
    def create_standard_jorge(cls, tenant_id: str = "jorge_seller") -> "JorgeSellerBot":
        """Factory method: Create standard friendly Jorge bot (Track 3.1 only)"""
        config = JorgeFeatureConfig(enable_track3_intelligence=True, friendly_approach_enabled=True)
        return cls(tenant_id=tenant_id, config=config)

    @classmethod
    def create_progressive_jorge(cls, tenant_id: str = "jorge_seller") -> "JorgeSellerBot":
        """Factory method: Create friendly Jorge bot with progressive skills (68% token reduction)"""
        config = JorgeFeatureConfig(
            enable_track3_intelligence=True,
            enable_progressive_skills=True,
            enable_bot_intelligence=True,  # Phase 3.3 enabled
            friendly_approach_enabled=True,
        )
        return cls(tenant_id=tenant_id, config=config)

    @classmethod
    def create_enterprise_jorge(cls, tenant_id: str = "jorge_seller") -> "JorgeSellerBot":
        """Factory method: Create fully-enhanced friendly enterprise Jorge bot"""
        config = JorgeFeatureConfig(
            enable_track3_intelligence=True,
            enable_progressive_skills=True,
            enable_agent_mesh=True,
            enable_mcp_integration=True,
            enable_adaptive_questioning=True,
            enable_bot_intelligence=True,  # Phase 3.3 enabled
            friendly_approach_enabled=True,
        )
        return cls(tenant_id=tenant_id, config=config)

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics for all enabled features"""

        # Base metrics
        metrics = {
            "workflow_statistics": self.workflow_stats,
            "features_enabled": {
                "track3_intelligence": self.config.enable_track3_intelligence,
                "progressive_skills": self.config.enable_progressive_skills,
                "agent_mesh": self.config.enable_agent_mesh,
                "mcp_integration": self.config.enable_mcp_integration,
                "adaptive_questioning": self.config.enable_adaptive_questioning,
                "bot_intelligence": self.config.enable_bot_intelligence,  # Phase 3.3
            },
        }

        # Progressive skills metrics
        if self.config.enable_progressive_skills and self.workflow_stats["total_interactions"] > 0:
            avg_token_savings = self.workflow_stats["token_savings"] / max(self.workflow_stats["total_interactions"], 1)
            metrics["progressive_skills"] = {
                "average_token_reduction_percent": (avg_token_savings / 853) * 100,
                "total_tokens_saved": self.workflow_stats["token_savings"],
                "usage_count": self.workflow_stats["progressive_skills_usage"],
            }

        # Agent mesh metrics
        if self.config.enable_agent_mesh:
            metrics["agent_mesh"] = {
                "orchestrations_created": self.workflow_stats["mesh_orchestrations"],
                "average_orchestrations_per_interaction": self.workflow_stats["mesh_orchestrations"]
                / max(self.workflow_stats["total_interactions"], 1),
            }

        # MCP integration metrics
        if self.config.enable_mcp_integration:
            metrics["mcp_integration"] = {
                "total_calls": self.workflow_stats["mcp_calls"],
                "average_calls_per_interaction": self.workflow_stats["mcp_calls"]
                / max(self.workflow_stats["total_interactions"], 1),
            }

        # Adaptive questioning metrics
        if self.config.enable_adaptive_questioning:
            metrics["adaptive_questioning"] = {
                "question_selections": self.workflow_stats["adaptive_question_selections"],
                "usage_rate": self.workflow_stats["adaptive_question_selections"]
                / max(self.workflow_stats["total_interactions"], 1),
            }

        # Phase 3.3 Bot intelligence metrics
        if self.config.enable_bot_intelligence:
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

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all enabled systems"""
        health_status = {
            "jorge_bot": "healthy",
            "track3_intelligence": "disabled",
            "progressive_skills": "disabled",
            "agent_mesh": "disabled",
            "mcp_integration": "disabled",
            "adaptive_questioning": "disabled",
            "overall_status": "healthy",
        }

        # Check Track 3.1 intelligence
        if self.config.enable_track3_intelligence and self.ml_analytics:
            health_status["track3_intelligence"] = "healthy"

        # Check progressive skills
        if self.config.enable_progressive_skills and self.skills_manager:
            try:
                health_status["progressive_skills"] = "healthy"
            except Exception as e:
                health_status["progressive_skills"] = f"error: {e}"
                health_status["overall_status"] = "degraded"

        # Check agent mesh
        if self.config.enable_agent_mesh and self.mesh_coordinator:
            try:
                health_status["agent_mesh"] = "healthy"
            except Exception as e:
                health_status["agent_mesh"] = f"error: {e}"
                health_status["overall_status"] = "degraded"

        # Check MCP integration
        if self.config.enable_mcp_integration and self.mcp_client:
            try:
                mcp_health = await self.mcp_client.health_check()
                health_status["mcp_integration"] = mcp_health
                if isinstance(mcp_health, dict) and mcp_health.get("status") != "healthy":
                    health_status["overall_status"] = "degraded"
            except Exception as e:
                health_status["mcp_integration"] = f"error: {e}"
                health_status["overall_status"] = "degraded"

        # Check adaptive questioning
        if self.config.enable_adaptive_questioning:
            health_status["adaptive_questioning"] = (
                "healthy" if self.conversation_memory and self.question_engine else "misconfigured"
            )

        return health_status

    async def shutdown(self):
        """Clean shutdown of all enabled systems"""
        if self.config.enable_mcp_integration and self.mcp_client:
            await self.mcp_client.disconnect_all()
            logger.info("Jorge bot: MCP connections closed")

        logger.info(f"Jorge bot unified shutdown complete - tenant: {self.tenant_id}")


# ================================
# FACTORY FUNCTIONS FOR EASY USE
# ================================


def get_jorge_seller_bot(enhancement_level: str = "standard", tenant_id: str = "jorge_seller") -> JorgeSellerBot:
    """
    Factory function to get Jorge Seller Bot with env-based feature configuration.

    Loads feature flags from environment variables via load_feature_config_from_env(),
    then bridges them to JorgeFeatureConfig kwargs. Falls back to factory presets
    if the feature config module is unavailable.

    Args:
        enhancement_level: "standard", "progressive", or "enterprise" (used as fallback)
        tenant_id: Tenant identifier
    """
    try:
        from ghl_real_estate_ai.config.feature_config import (
            feature_config_to_jorge_kwargs,
            load_feature_config_from_env,
        )

        feature_cfg = load_feature_config_from_env()
        jorge_kwargs = feature_config_to_jorge_kwargs(feature_cfg)
        config = JorgeFeatureConfig(**jorge_kwargs)
        return JorgeSellerBot(tenant_id=tenant_id, config=config)
    except ImportError:
        logger.warning("feature_config module unavailable, falling back to factory presets")
        if enhancement_level == "progressive":
            return JorgeSellerBot.create_progressive_jorge(tenant_id)
        elif enhancement_level == "enterprise":
            return JorgeSellerBot.create_enterprise_jorge(tenant_id)
        else:
            return JorgeSellerBot.create_standard_jorge(tenant_id)
