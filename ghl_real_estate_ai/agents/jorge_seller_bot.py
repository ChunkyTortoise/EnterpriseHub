
"""
Jorge Seller Bot - Unified Enterprise Implementation
Combines all research enhancements into production-ready unified implementation.

REFACTORED: This module now delegates to specialized services in the seller/ package:
- CMAService: CMA generation and valuation defense
- MarketAnalyzer: Market conditions and pricing guidance
- StallDetector: Stall detection and property condition extraction
- ResponseGenerator: Response generation with sentiment analysis
- StrategySelector: Strategy selection with Track 3.1 intelligence
- ListingService: Listing preparation recommendations
- FollowUpService: Automated follow-up execution
- HandoffManager: Handoff context management
- ConversationMemory/AdaptiveQuestionEngine: Conversation memory and adaptive questioning
- ExecutiveService: Executive brief generation
- ObjectionHandler: Objection handling with graduated responses

The public API remains unchanged for backward compatibility.
"""

import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from langgraph.graph import END, StateGraph

# Import new modular services
from ghl_real_estate_ai.agents.seller import (
    JorgeFeatureConfig,
    QualificationResult,
    CMAService,
    MarketAnalyzer,
    StallDetector,
    ResponseGenerator,
    StrategySelector,
    ListingService,
    FollowUpService,
    HandoffManager,
    ConversationMemory,
    AdaptiveQuestionEngine,
    ExecutiveService,
    ObjectionHandler,
)
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
from ghl_real_estate_ai.services.jorge.acceptance_predictor_service import get_acceptance_predictor_service
from ghl_real_estate_ai.services.jorge.alerting_service import AlertingService
from ghl_real_estate_ai.services.jorge.bot_metrics_collector import BotMetricsCollector
from ghl_real_estate_ai.services.jorge.performance_tracker import PerformanceTracker
from ghl_real_estate_ai.services.market_intelligence import get_market_intelligence
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer
from ghl_real_estate_ai.agents.base_bot_workflow import BaseBotWorkflow

# Phase 1.5 - 1.8 Integration
from ghl_real_estate_ai.services.sentiment_analysis_service import SentimentAnalysisService
from ghl_real_estate_ai.services.lead_scoring_integration import LeadScoringIntegration
from ghl_real_estate_ai.services.ghl_workflow_service import GHLWorkflowService
from ghl_real_estate_ai.services.churn_detection_service import ChurnDetectionService
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeRequest, ClaudeTaskType

# Phase 3 Loop 3: Handoff context propagation
try:
    from ghl_real_estate_ai.services.jorge.jorge_handoff_service import EnrichedHandoffContext
    HANDOFF_CONTEXT_AVAILABLE = True
except ImportError:
    HANDOFF_CONTEXT_AVAILABLE = False
    EnrichedHandoffContext = None

try:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient
    GHL_CLIENT_AVAILABLE = True
except ImportError:
    GHL_CLIENT_AVAILABLE = False

from ghl_real_estate_ai.services.jorge.calendar_booking_service import CalendarBookingService

# Track 3.1 Predictive Intelligence Integration
try:
    from bots.shared.ml_analytics_engine import MLAnalyticsEngine, get_ml_analytics_engine
    ML_ANALYTICS_AVAILABLE = True
except ImportError:
    from ghl_real_estate_ai.stubs.bots_stub import get_ml_analytics_engine
    ML_ANALYTICS_AVAILABLE = False

# Phase 3.3 Bot Intelligence Middleware Integration
try:
    from ghl_real_estate_ai.models.intelligence_context import BotIntelligenceContext
    from ghl_real_estate_ai.services.bot_intelligence_middleware import get_bot_intelligence_middleware
    BOT_INTELLIGENCE_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
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

# Re-export for backward compatibility
__all__ = [
    "JorgeSellerBot",
    "JorgeFeatureConfig",
    "QualificationResult",
    "get_jorge_seller_bot",
]


class JorgeSellerBot(BaseBotWorkflow):
    """
    Unified Jorge Seller Bot - Production-ready with optional enhancements.

    Inherits from BaseBotWorkflow to share common monitoring and service patterns.

    This class now delegates to specialized service classes for specific responsibilities
    while maintaining full backward compatibility with the original public API.

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
        # Initialize base workflow (handles industry_config, event_publisher, ml_analytics)
        self.config = config or JorgeFeatureConfig()
        super().__init__(
            tenant_id=tenant_id,
            industry_config=industry_config,
            enable_ml_analytics=self.config.enable_track3_intelligence,
        )

        # Core components (bot-specific)
        self.intent_decoder = LeadIntentDecoder(industry_config=self.industry_config)
        self.seller_intent_decoder = SellerIntentDecoder(industry_config=self.industry_config)
        self.cma_generator = CMAGenerator()
        self.market_intelligence = get_market_intelligence()
        self.claude = ClaudeAssistant()
        self.seller_psychology_analyzer = get_seller_psychology_analyzer()

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
            # Import JorgeSellerConfig to get the current mode setting
            from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

            simple_mode = JorgeSellerConfig.JORGE_SIMPLE_MODE
            self.conversation_memory = ConversationMemory()
            self.question_engine = AdaptiveQuestionEngine(
                questions_config=self.industry_config.questions,
                simple_mode=simple_mode
            )
            mode_name = "simple (4 questions)" if simple_mode else "full (10 questions)"
            logger.info(f"Jorge bot: Adaptive questioning enabled in {mode_name} mode")

        # Phase 3.3 Bot Intelligence Middleware (optional)
        self.intelligence_middleware = None
        if self.config.enable_bot_intelligence and BOT_INTELLIGENCE_AVAILABLE:
            self.intelligence_middleware = get_bot_intelligence_middleware()
            logger.info("Jorge bot: Bot Intelligence Middleware enabled (Phase 3.3)")
        elif self.config.enable_bot_intelligence:
            logger.warning("Jorge bot: Bot Intelligence requested but dependencies not available")

        # Phase 1.5 - 1.8 Services Initialization
        self.sentiment_service = SentimentAnalysisService()
        self.lead_scoring_integration = LeadScoringIntegration()
        self.workflow_service = GHLWorkflowService()
        self.churn_service = ChurnDetectionService(sentiment_service=self.sentiment_service)
        logger.info("Jorge bot: Phase 1.5-1.8 services (Sentiment, Scoring, Workflow, Churn) initialized")

        # Initialize modular service layer (NEW: Decomposed services)
        self._init_service_layer()

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

    def _init_service_layer(self):
        """Initialize the decomposed service layer."""
        # Calendar booking service for HOT sellers
        self.calendar_service = None
        if GHL_CLIENT_AVAILABLE:
            try:
                ghl_client = EnhancedGHLClient()
                self.calendar_service = CalendarBookingService(ghl_client)
                logger.info("Jorge bot: CalendarBookingService initialized")
            except Exception as e:
                logger.warning(f"Jorge bot: CalendarBookingService unavailable: {e}")

        # Core workflow services
        self.cma_service = CMAService(
            cma_generator=self.cma_generator,
            claude=self.claude
        )
        self.market_analyzer = MarketAnalyzer(ab_testing=self.ab_testing)
        self.stall_detector = StallDetector(event_publisher=self.event_publisher)
        self.response_generator = ResponseGenerator(
            claude=self.claude,
            event_publisher=self.event_publisher,
            sentiment_service=self.sentiment_service,
            ab_testing=self.ab_testing,
            calendar_service=self.calendar_service,
        )
        self.strategy_selector = StrategySelector(
            event_publisher=self.event_publisher,
            ml_analytics=self.ml_analytics,
            tenant_id=self.tenant_id
        )
        self.listing_service = ListingService()
        self.followup_service = FollowUpService(event_publisher=self.event_publisher)
        self.handoff_manager = HandoffManager()
        self.executive_service = ExecutiveService(event_publisher=self.event_publisher)
        self.objection_handler = ObjectionHandler(event_publisher=self.event_publisher)
        
        logger.info("Jorge bot: Service layer initialized with decomposed modules")

    def _build_unified_graph(self) -> StateGraph:
        """Build workflow graph based on enabled features"""
        if self.config.enable_adaptive_questioning:
            return self._build_adaptive_graph()
        else:
            return self._build_standard_graph()

    def _build_standard_graph(self) -> StateGraph:
        workflow = StateGraph(JorgeSellerState)

        # Define Nodes - delegate to service layer
        workflow.add_node("analyze_intent", self.analyze_intent)

        # Add intelligence gathering node if enabled
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_node("gather_intelligence", self.gather_intelligence_context)

        # Phase 2.2: Objection handling node - delegated to service
        workflow.add_node("handle_objection", self._handle_objection_node)

        # CMA & Market Intelligence nodes - delegated to services
        workflow.add_node("generate_cma", self._generate_cma_node)
        workflow.add_node("provide_pricing_guidance", self._provide_pricing_guidance_node)
        workflow.add_node("analyze_market_conditions", self._analyze_market_conditions_node)

        workflow.add_node("detect_stall", self._detect_stall_node)
        workflow.add_node("defend_valuation", self._defend_valuation_node)
        workflow.add_node("prepare_listing", self._prepare_listing_node)
        workflow.add_node("select_strategy", self._select_strategy_node)
        workflow.add_node("generate_jorge_response", self._generate_jorge_response_node)
        workflow.add_node("generate_executive_brief", self._generate_executive_brief_node)
        workflow.add_node("recalculate_pcs", self.recalculate_pcs_node)
        workflow.add_node("execute_follow_up", self._execute_follow_up_node)

        # Define Edges
        workflow.set_entry_point("analyze_intent")

        # Conditional routing for intelligence gathering
        if self.config.enable_bot_intelligence and self.intelligence_middleware:
            workflow.add_edge("analyze_intent", "gather_intelligence")
            workflow.add_edge("gather_intelligence", "handle_objection")
        else:
            workflow.add_edge("analyze_intent", "handle_objection")

        # Conditional routing from objection handling
        workflow.add_conditional_edges(
            "handle_objection",
            self._route_after_objection,
            {
                "objection_response": "select_strategy",
                "continue_normal": "generate_cma",
            },
        )

        # Phase 4: ML pricing guidance flow
        workflow.add_edge("generate_cma", "provide_pricing_guidance")
        workflow.add_edge("provide_pricing_guidance", "analyze_market_conditions")
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
        workflow.add_edge("recalculate_pcs", "generate_executive_brief")
        workflow.add_edge("generate_executive_brief", END)
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

        workflow.add_node("detect_stall", self._detect_stall_node)
        workflow.add_node("adaptive_strategy", self._adaptive_strategy_node)
        workflow.add_node("generate_adaptive_response", self._generate_adaptive_response_node)
        workflow.add_node("generate_executive_brief", self._generate_executive_brief_node)
        workflow.add_node("recalculate_pcs", self.recalculate_pcs_node)
        workflow.add_node("execute_follow_up", self._execute_follow_up_node)
        workflow.add_node("update_memory", self._update_conversation_memory_node)

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
        workflow.add_edge("recalculate_pcs", "generate_executive_brief")
        workflow.add_edge("generate_executive_brief", "update_memory")
        workflow.add_edge("execute_follow_up", "update_memory")
        workflow.add_edge("update_memory", END)

        return workflow.compile()

    # ================================
    # DELEGATED NODE METHODS (NEW)
    # ================================

    async def _generate_cma_node(self, state: JorgeSellerState) -> Dict:
        """Delegate CMA generation to CMAService."""
        return await self.cma_service.generate_cma(state)

    async def _defend_valuation_node(self, state: JorgeSellerState) -> Dict:
        """Delegate valuation defense to CMAService."""
        return await self.cma_service.defend_valuation(state)

    async def _analyze_market_conditions_node(self, state: JorgeSellerState) -> Dict:
        """Delegate market analysis to MarketAnalyzer."""
        return await self.market_analyzer.analyze_market_conditions(state)

    async def _provide_pricing_guidance_node(self, state: JorgeSellerState) -> Dict:
        """Delegate pricing guidance to MarketAnalyzer."""
        return await self.market_analyzer.provide_pricing_guidance(state)

    async def _detect_stall_node(self, state: JorgeSellerState) -> Dict:
        """Delegate stall detection to StallDetector."""
        return await self.stall_detector.detect_stall(state)

    async def _select_strategy_node(self, state: JorgeSellerState) -> Dict:
        """Delegate strategy selection to StrategySelector."""
        return await self.strategy_selector.select_strategy(state)

    async def _adaptive_strategy_node(self, state: JorgeSellerState) -> Dict:
        """Delegate adaptive strategy selection to StrategySelector."""
        # Create base strategy with adaptive mode
        pcs = state.get("psychological_commitment", 0)
        adaptation_count = state.get("adaptation_count", 0)
        
        if pcs > 70:
            strategy = {"current_tone": "DIRECT", "next_action": "fast_track", "adaptive_mode": "calendar_focused"}
        elif state.get("stall_detected"):
            strategy = {"current_tone": "UNDERSTANDING", "next_action": "respond", "adaptive_mode": "supportive_guidance"}
        elif adaptation_count > 2:
            strategy = {"current_tone": "HONEST", "next_action": "respond", "adaptive_mode": "clarity_focused"}
        else:
            strategy = {"current_tone": "CONSULTATIVE", "next_action": "respond", "adaptive_mode": "standard_qualification"}
        
        return strategy

    async def _generate_jorge_response_node(self, state: JorgeSellerState) -> Dict:
        """Delegate response generation to ResponseGenerator."""
        tone_variant = state.get("tone_variant")
        return await self.response_generator.generate_jorge_response(state, tone_variant)

    async def _generate_adaptive_response_node(self, state: JorgeSellerState) -> Dict:
        """Delegate adaptive response generation to ResponseGenerator."""
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)
        next_question = await self.question_engine.select_next_question(state, context)
        
        self.workflow_stats["adaptive_question_selections"] += 1
        
        tone_variant = state.get("tone_variant")
        return await self.response_generator.generate_adaptive_response(state, next_question, tone_variant)

    async def _prepare_listing_node(self, state: JorgeSellerState) -> Dict:
        """Delegate listing preparation to ListingService."""
        return await self.listing_service.prepare_listing(state)

    async def _execute_follow_up_node(self, state: JorgeSellerState) -> Dict:
        """Delegate follow-up execution to FollowUpService."""
        return await self.followup_service.execute_follow_up(state)

    async def _generate_executive_brief_node(self, state: JorgeSellerState) -> Dict:
        """Delegate executive brief generation to ExecutiveService."""
        return await self.executive_service.generate_executive_brief(state)

    async def _handle_objection_node(self, state: JorgeSellerState) -> Dict:
        """Delegate objection handling to ObjectionHandler."""
        return await self.objection_handler.handle_objection(state)

    async def _update_conversation_memory_node(self, state: JorgeSellerState) -> Dict:
        """Update conversation memory with new interaction."""
        conversation_id = f"jorge_{state['lead_id']}"
        context = await self.conversation_memory.get_context(conversation_id)
        
        update = {
            "last_scores": {"frs": state["intent_profile"].frs.total_score if state.get("intent_profile") else 0, 
                          "pcs": state.get("psychological_commitment", 0)},
            "last_interaction_time": datetime.now(timezone.utc),
            "adaptation_count": context.get("adaptation_count", 0) + 1,
            "response_patterns": {
                "adaptive_mode": state.get("adaptive_mode"),
                "question_used": state.get("adaptive_question_used"),
            },
        }
        
        await self.conversation_memory.update_context(conversation_id, update)
        return {"memory_updated": True}

    # ================================
    # ROUTING METHODS
    # ================================

    def _route_seller_action(
        self, state: JorgeSellerState
    ) -> Literal["respond", "follow_up", "listing_prep", "end"]:
        """Determine if we should respond immediately or queue a follow-up."""
        return self.strategy_selector.route_seller_action(state)

    def _route_after_stall_detection(
        self, state: JorgeSellerState
    ) -> Literal["defend_valuation", "select_strategy"]:
        """Route to valuation defense if Zestimate stall detected with CMA data."""
        return self.strategy_selector.route_after_stall_detection(state)

    def _route_after_objection(
        self, state: JorgeSellerState
    ) -> Literal["objection_response", "continue_normal"]:
        """Route based on objection detection."""
        return self.strategy_selector.route_after_objection(state)

    def _route_adaptive_action(
        self, state: JorgeSellerState
    ) -> Literal["respond", "follow_up", "fast_track", "end"]:
        """Enhanced routing with fast-track capability."""
        return self.strategy_selector.route_adaptive_action(state)

    # ================================
    # EXISTING METHODS (maintained for compatibility)
    # ================================

    async def generate_executive_brief(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to ExecutiveService."""
        return await self.executive_service.generate_executive_brief(state)

    async def analyze_intent(self, state: JorgeSellerState) -> Dict:
        """Score the lead and identify psychological commitment."""
        # Phase 3 Loop 3: Skip intent analysis if handoff context already populated state
        if state.get("skip_qualification") and state.get("handoff_context_used"):
            logger.info(f"Skipping intent analysis for {state.get('lead_id')} - using handoff context")
            # Return high-quality default profile for handed-off contacts
            from ghl_real_estate_ai.models.lead_scoring import (
                LeadIntentProfile,
                FinancialReadinessScore,
                PsychologicalCommitmentScore,
                MotivationSignals,
                TimelineCommitment,
                ConditionRealism,
                PriceResponsiveness,
            )

            # Create high-confidence profile for handed-off seller
            frs = FinancialReadinessScore(
                total_score=70.0,  # High confidence from handoff
                motivation=MotivationSignals(
                    score=75,
                    detected_markers=["handoff_context"],
                    category="High Intent"
                ),
                timeline=TimelineCommitment(
                    score=70,
                    target_date=None,
                    category="High Commitment"
                ),
                condition=ConditionRealism(
                    score=65,
                    acknowledged_defects=[],
                    category="Realistic"
                ),
                price=PriceResponsiveness(
                    score=70,
                    zestimate_mentioned=False,
                    category="Price-Aware"
                ),
                classification="Warm"
            )
            pcs = PsychologicalCommitmentScore(
                total_score=68.0,
                response_velocity_score=70,
                message_length_score=65,
                question_depth_score=70,
                objection_handling_score=65,
                call_acceptance_score=70
            )
            profile = LeadIntentProfile(
                lead_id=state.get("lead_id", "unknown"),
                frs=frs,
                pcs=pcs,
                lead_type="seller",
                next_best_action="qualify_seller"
            )

            return {
                "intent_profile": profile,
                "seller_temperature": "warm",
                "property_condition": state.get("property_condition", "unknown"),
                "seller_intent_profile": None,
                "seller_classification": {"persona_type": "Traditional", "confidence": 0.7},
            }

        # Emit bot status update - starting analysis
        await self.event_publisher.publish_bot_status_update(
            bot_type="jorge-seller", contact_id=state["lead_id"], status="processing", current_step="analyze_intent"
        )

        logger.info(f"Analyzing seller intent for {state['lead_name']}")
        profile = self.intent_decoder.analyze_lead(state["lead_id"], state["conversation_history"])

        # Classify seller temperature based on scores
        seller_temperature = self.stall_detector.classify_temperature(profile)

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
        property_condition = self.stall_detector.extract_property_condition(
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

        # Phase 1.6: Calculate Composite Lead Score
        composite_score_data = {}
        try:
            temp_state = {
                "frs_score": profile.frs.total_score,
                "pcs_score": profile.pcs.total_score,
                "conversation_history": state["conversation_history"],
                "seller_persona": seller_classification
            }
            
            scoring_result = await self.lead_scoring_integration.calculate_and_store_composite_score(
                state=temp_state,
                contact_id=state["lead_id"],
                use_ml_ensemble=self.config.enable_track3_intelligence
            )
            composite_score_data = scoring_result.get("composite_score_data", {})
            logger.info(f"Composite score calculated for {state['lead_id']}: {composite_score_data.get('total_score', 0)}")
        except Exception as e:
            logger.error(f"Failed to calculate composite score: {e}")

        return {
            "intent_profile": profile,
            "psychological_commitment": profile.pcs.total_score,
            "is_qualified": profile.frs.classification in ["Hot Lead", "Warm Lead"],
            "seller_temperature": seller_temperature,
            "last_action_timestamp": datetime.now(timezone.utc),
            "property_condition": property_condition,
            "seller_intent_profile": seller_intent_profile,
            "seller_persona": seller_classification,
            "composite_score": composite_score_data,
        }

    async def gather_intelligence_context(self, state: JorgeSellerState) -> Dict:
        """Phase 3.3: Gather intelligence context for enhanced decision making."""
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
                    location_id=state.get("location_id", "rancho_cucamonga"),
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

    async def handle_objection(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to ObjectionHandler."""
        return await self.objection_handler.handle_objection(state)

    async def generate_cma(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to CMAService."""
        return await self.cma_service.generate_cma(state)

    async def provide_pricing_guidance(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to MarketAnalyzer."""
        return await self.market_analyzer.provide_pricing_guidance(state)

    async def analyze_market_conditions(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to MarketAnalyzer."""
        return await self.market_analyzer.analyze_market_conditions(state)

    async def defend_valuation(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to CMAService."""
        return await self.cma_service.defend_valuation(state)

    async def prepare_listing(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to ListingService."""
        return await self.listing_service.prepare_listing(state)

    async def detect_stall(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to StallDetector."""
        return await self.stall_detector.detect_stall(state)

    async def select_strategy(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to StrategySelector."""
        return await self.strategy_selector.select_strategy(state)

    async def generate_jorge_response(self, state: JorgeSellerState) -> Dict:
        """Legacy method - delegates to ResponseGenerator."""
        return await self.response_generator.generate_jorge_response(state)

    async def recalculate_pcs_node(self, state: JorgeSellerState) -> Dict:
        """Recalculate PCS dynamically based on conversation flow."""
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
                if GHL_CLIENT_AVAILABLE and EnhancedGHLClient:
                    contact_id = state.get("lead_id")
                    async with EnhancedGHLClient() as ghl:
                        await ghl.update_contact(
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
        """Legacy method - delegates to FollowUpService."""
        return await self.followup_service.execute_follow_up(state)

    # ================================
    # ADAPTIVE INTELLIGENCE METHODS
    # ================================

    async def adaptive_strategy_selection(self, state: JorgeSellerState) -> Dict:
        """Legacy adaptive strategy method."""
        return await self._adaptive_strategy_node(state)

    async def generate_adaptive_response(self, state: JorgeSellerState) -> Dict:
        """Legacy adaptive response method."""
        return await self._generate_adaptive_response_node(state)

    async def update_conversation_memory(self, state: JorgeSellerState) -> Dict:
        """Legacy memory update method."""
        return await self._update_conversation_memory_node(state)

    # ================================
    # PROGRESSIVE SKILLS METHODS
    # ================================

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
                "rancho cucamonga" in address_lower,
                "tx 78" in address_lower,
                " atx" in address_lower,
                "rancho cucamonga, ca" in address_lower,
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

    # ================================
    # AGENT MESH INTEGRATION METHODS
    # ================================

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

    # ================================
    # MCP INTEGRATION METHODS
    # ================================

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

    # ================================
    # UTILITY METHODS
    # ================================

    @staticmethod
    def _detect_slot_selection(message: str) -> Optional[int]:
        """Detect if the user message is selecting a calendar slot.

        Recognizes patterns like "1", "slot 1", "option 2", "#3", "number 2".
        Returns 0-based index or None if no slot selection detected.
        """
        import re

        msg = message.strip().lower()
        # Direct number: "1", "2", "3"
        if re.fullmatch(r"\d+", msg):
            num = int(msg)
            if 1 <= num <= 10:
                return num - 1
        # Patterns: "slot 1", "option 2", "#3", "number 2"
        match = re.search(r"(?:slot|option|number|#)\s*(\d+)", msg)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 10:
                return num - 1
        return None

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

    # ================================
    # PUBLIC API (process_seller_message)
    # ================================

    async def process_seller_message(
        self,
        conversation_id: str,
        user_message: str,
        seller_name: Optional[str] = None,
        conversation_history: Optional[List[ConversationMessage]] = None,
        seller_phone: Optional[str] = None,
        seller_email: Optional[str] = None,
        metadata: Optional[BotMetadata] = None,
        handoff_context: Optional[Any] = None,
    ) -> SellerBotResponse:
        """
        Main public API for processing seller messages.
        Maintains full backward compatibility while delegating to service layer.
        """
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

            # Check if this is a calendar slot selection response
            if self.calendar_service:
                slot_index = self._detect_slot_selection(user_message)
                if slot_index is not None:
                    booking_result = await self.calendar_service.book_appointment(conversation_id, slot_index)
                    return {
                        "response_content": booking_result["message"],
                        "lead_id": conversation_id,
                        "current_step": "calendar_booked" if booking_result["success"] else "calendar_retry",
                        "engagement_status": "appointment_booked" if booking_result["success"] else "qualification",
                        "frs_score": 0.0,
                        "pcs_score": 0.0,
                        "handoff_signals": {},
                    }

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
                "skip_qualification": False,
                "handoff_context_used": False,
            }

            if seller_phone:
                initial_state["seller_phone"] = seller_phone
            if seller_email:
                initial_state["seller_email"] = seller_email
            if metadata:
                initial_state["metadata"] = metadata

            # Phase 3 Loop 3: Apply handoff context if valid (delegated to HandoffManager)
            if handoff_context and self.handoff_manager.has_valid_handoff_context(handoff_context):
                initial_state = self.handoff_manager.populate_state_from_context(handoff_context, initial_state)
                logger.info(f"Seller bot using handoff context for {conversation_id} - skipping re-qualification")

            result = await self.workflow.ainvoke(initial_state)

            _workflow_duration_ms = (time.time() - _workflow_start) * 1000

            self.workflow_stats["total_interactions"] += 1

            handoff_signals = {}
            if self.config.jorge_handoff_enabled:
                from ghl_real_estate_ai.services.jorge.jorge_handoff_service import JorgeHandoffService
                handoff_signals = JorgeHandoffService.extract_intent_signals(user_message)

            intent_profile = result.get("intent_profile")
            seller_persona = result.get("seller_persona", {})
            frs_score = 0.0
            pcs_score = 0.0
            if intent_profile:
                frs_score = getattr(getattr(intent_profile, "frs", None), "total_score", 0.0)
                pcs_score = getattr(getattr(intent_profile, "pcs", None), "total_score", 0.0)

            # Phase 1.7: GHL Workflow Integration (Auto-tagging & Pipeline)
            try:
                scores = {"frs": frs_score, "pcs": pcs_score, "composite": 0.0}
                persona_str = seller_persona.get("persona_type") if seller_persona else None

                await self.workflow_service.apply_tag_rules(
                    contact_id=conversation_id,
                    scores=scores,
                    persona=persona_str,
                    sentiment=None,
                    escalation=False,
                    appointment_booked=False
                )
                logger.info(f"Applied GHL workflow tags for {conversation_id}")
            except Exception as e:
                logger.warning(f"Failed to execute GHL workflow operations: {e}")

            # Phase 1.8: Churn Detection Integration
            churn_assessment = None
            try:
                last_activity = datetime.now(timezone.utc)
                churn_assessment = await self.churn_service.assess_churn_risk(
                    contact_id=conversation_id,
                    conversation_history=conversation_history,
                    last_activity=last_activity
                )
                logger.info(f"Churn risk assessed for {conversation_id}: {churn_assessment.risk_level}")
            except Exception as e:
                logger.warning(f"Failed to assess churn risk: {e}")

            # Record performance metrics
            await self.performance_tracker.track_operation("seller_bot", "process", _workflow_duration_ms, success=True)
            self.metrics_collector.record_bot_interaction("seller", duration_ms=_workflow_duration_ms, success=True)

            # Feed metrics to alerting (non-blocking)
            try:
                self.metrics_collector.feed_to_alerting(self.alerting_service)
            except Exception as e:
                logger.debug(f"Failed to feed metrics to alerting: {str(e)}")

            # Record A/B test outcome
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
                "composite_score": result.get("composite_score", {}).get("total_score", 0.0),
                "handoff_signals": handoff_signals,
                "seller_persona": seller_persona,
                "churn_assessment": churn_assessment,
                "property_address": result.get("property_address"),
                "seller_motivation": result.get("seller_motivation"),
                "timeline_urgency": result.get("timeline_urgency"),
                "property_condition": result.get("property_condition"),
                "price_expectation": result.get("price_expectation"),
                "seller_liens": result.get("seller_liens"),
                "seller_repairs": result.get("seller_repairs"),
                "seller_listing_history": result.get("seller_listing_history"),
                "seller_decision_maker": result.get("seller_decision_maker"),
                "seller_contact_method": result.get("seller_contact_method"),
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
        """Sync seller persona classification to GHL as tags."""
        if not GHL_CLIENT_AVAILABLE:
            logger.warning("GHL client not available, skipping persona tag sync")
            return False

        if confidence < 0.3:
            logger.info(f"Skipping persona tag sync for {contact_id} - confidence too low: {confidence:.2f}")
            return False

        try:
            persona_tag = f"{persona_type}-Seller"

            async with EnhancedGHLClient() as ghl:
                contact = await ghl.get_contact(contact_id)
                if not contact:
                    logger.warning(f"Contact {contact_id} not found in GHL")
                    return False

                existing_tags = contact.tags or []
                persona_tags = ["Investor-Seller", "Distressed-Seller", "Traditional-Seller"]
                cleaned_tags = [tag for tag in existing_tags if tag not in persona_tags]
                updated_tags = cleaned_tags + [persona_tag]

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
            response_content=qualification_analysis.get("response_content", ""),
            qualification_summary=qualification_analysis.get("qualification_summary", ""),
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
            actions.extend([
                "Schedule immediate listing appointment",
                "Send Jorge's 6% commission structure",
                "Provide market analysis with value proposition",
            ])
        elif temperature == "warm" and qualification_score >= 50:
            actions.extend([
                "Schedule follow-up call within 48 hours",
                "Send market statistics and Jorge's track record",
                "Prepare preliminary home value estimate",
            ])
        else:
            actions.extend(["Add to 30-day nurture sequence", "Monitor for re-engagement signals"])

        return actions

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
            enable_bot_intelligence=True,
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
            enable_bot_intelligence=True,
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
                "bot_intelligence": self.config.enable_bot_intelligence,
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
            except AttributeError as e:
                logger.warning(f"Progressive skills health check failed (not initialized): {e}")
                health_status["progressive_skills"] = f"error: {e}"
                health_status["overall_status"] = "degraded"
            except Exception as e:
                logger.error(f"Unexpected error in progressive skills health check: {e}", exc_info=True)
                health_status["progressive_skills"] = f"error: {e}"
                health_status["overall_status"] = "degraded"

        # Check agent mesh
        if self.config.enable_agent_mesh and self.mesh_coordinator:
            try:
                health_status["agent_mesh"] = "healthy"
            except AttributeError as e:
                logger.warning(f"Agent mesh health check failed (not initialized): {e}")
                health_status["agent_mesh"] = f"error: {e}"
                health_status["overall_status"] = "degraded"
            except Exception as e:
                logger.error(f"Unexpected error in agent mesh health check: {e}", exc_info=True)
                health_status["agent_mesh"] = f"error: {e}"
                health_status["overall_status"] = "degraded"

        # Check MCP integration
        if self.config.enable_mcp_integration and self.mcp_client:
            try:
                mcp_health = await self.mcp_client.health_check()
                health_status["mcp_integration"] = mcp_health
                if isinstance(mcp_health, dict) and mcp_health.get("status") != "healthy":
                    health_status["overall_status"] = "degraded"
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"MCP health check failed (connection issue): {e}")
                health_status["mcp_integration"] = f"error: {e}"
                health_status["overall_status"] = "degraded"
            except AttributeError as e:
                logger.warning(f"MCP health check failed (not initialized): {e}")
                health_status["mcp_integration"] = f"error: {e}"
                health_status["overall_status"] = "degraded"
            except Exception as e:
                logger.error(f"Unexpected error in MCP health check: {e}", exc_info=True)
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
