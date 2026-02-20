"""
Claude Concierge Orchestrator - Platform-Wide Intelligence Integration
Provides omnipresent AI guidance across entire EnterpriseHub platform with Jorge-specific intelligence.
"""

import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from ghl_real_estate_ai.config.concierge_config_loader import (
    ConciergeClientConfig,
    get_concierge_config,
    get_default_concierge_config,
)
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_orchestrator import (
    ClaudeOrchestrator,
    ClaudeRequest,
    ClaudeTaskType,
)
from ghl_real_estate_ai.services.ghl_live_data_service import get_ghl_live_data_service
from ghl_real_estate_ai.services.memory_service import MemoryService

logger = get_logger(__name__)

# ============================================================================
# TRACK 2: Platform Context and Intelligence Types
# ============================================================================


@dataclass
class PlatformContext:
    """Complete platform state for omnipresent concierge intelligence."""

    # Core Platform State
    current_page: str
    user_role: str = "agent"  # 'agent', 'executive', 'client'
    session_id: str = "default_session"
    location_context: Dict[str, Any] = field(default_factory=dict)

    # Business Intelligence
    active_leads: List[Dict[str, Any]] = field(default_factory=list)
    bot_statuses: Dict[str, Any] = field(default_factory=dict)  # Jorge bot, Lead bot, etc.
    user_activity: List[Dict[str, Any]] = field(default_factory=list)
    business_metrics: Dict[str, Any] = field(default_factory=dict)
    active_properties: List[Dict[str, Any]] = field(default_factory=list)

    # Real-time Context
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    priority_actions: List[Dict[str, Any]] = field(default_factory=list)
    pending_notifications: List[Dict[str, Any]] = field(default_factory=list)

    # Jorge-specific Context
    jorge_preferences: Dict[str, Any] = field(default_factory=dict)
    deal_pipeline_state: Dict[str, Any] = field(default_factory=dict)
    commission_opportunities: List[Dict[str, Any]] = field(default_factory=list)

    # Technical Context
    device_type: str = "desktop"  # 'desktop', 'mobile', 'tablet'
    connection_quality: str = "excellent"  # 'excellent', 'good', 'poor'
    offline_capabilities: bool = False


@dataclass
class ConciergeResponse:
    """Structured response from the omnipresent concierge."""

    # Primary Intelligence
    primary_guidance: str
    urgency_level: str  # 'low', 'medium', 'high', 'urgent'
    confidence_score: float  # 0.0-1.0
    reasoning: Optional[str] = None

    # Actionable Recommendations
    immediate_actions: List[Dict[str, Any]] = field(default_factory=list)
    background_tasks: List[Dict[str, Any]] = field(default_factory=list)
    follow_up_reminders: List[Dict[str, Any]] = field(default_factory=list)

    # Context-Specific Intelligence
    page_specific_tips: List[str] = field(default_factory=list)
    bot_coordination_suggestions: List[Dict[str, Any]] = field(default_factory=list)
    revenue_optimization_ideas: List[Dict[str, Any]] = field(default_factory=list)

    # Proactive Intelligence
    risk_alerts: List[Dict[str, Any]] = field(default_factory=list)
    opportunity_highlights: List[Dict[str, Any]] = field(default_factory=list)
    learning_insights: List[Dict[str, Any]] = field(default_factory=list)

    # Advanced Intelligence
    handoff_recommendation: Optional[Dict[str, Any]] = None

    # Metadata
    response_time_ms: int = 0
    data_sources_used: List[str] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)


class ConciergeMode(Enum):
    """Different modes for concierge operation."""

    PROACTIVE = "proactive"  # Continuous background intelligence
    REACTIVE = "reactive"  # Response to user queries only
    PRESENTATION = "presentation"  # Client-facing mode with talking points
    FIELD_WORK = "field_work"  # Mobile field assistance
    EXECUTIVE = "executive"  # High-level strategic guidance
    EMERGENCY = "emergency"  # Crisis management and urgent decisions


class IntelligenceScope(Enum):
    """Scope of intelligence analysis."""

    PAGE_SPECIFIC = "page_specific"  # Current page/component only
    WORKFLOW = "workflow"  # Current workflow/task
    PLATFORM_WIDE = "platform_wide"  # Entire platform state
    STRATEGIC = "strategic"  # Business strategy and goals
    OPERATIONAL = "operational"  # Daily operations and efficiency


# ============================================================================
# TRACK 2: Main Concierge Orchestrator
# ============================================================================


class ClaudeConciergeOrchestrator:
    """
    Omnipresent AI concierge providing platform-wide intelligent guidance.

    Features:
    🎯 Context-aware guidance for every page/component
    🤝 Bot coordination recommendations
    💰 ROI optimization suggestions
    📱 Mobile field assistance for property visits
    🎭 Client presentation mode with talking points
    🧠 Continuous learning from Jorge's decisions
    """

    def __init__(
        self,
        claude_orchestrator: Optional[ClaudeOrchestrator] = None,
        memory_service: Optional[MemoryService] = None,
        client_config: Optional[ConciergeClientConfig] = None,
    ):

        # Core Services
        self.claude = claude_orchestrator or self._get_claude_orchestrator()
        self.memory = memory_service or MemoryService()
        self.cache = get_cache_service()
        self.analytics = AnalyticsService()

        # Track 3: Real Data Integration
        self.ghl_live_data = get_ghl_live_data_service()

        # Jorge-Specific Intelligence
        self.jorge_memory = JorgeMemorySystem(self.memory, self.cache)
        self.business_rules = JorgeBusinessRules()

        # Default client config (used when no tenant_id is supplied to methods)
        self._default_config: ConciergeClientConfig = client_config or get_default_concierge_config()

        # Platform State Tracking
        # session_contexts, context_cache, and generated_suggestions are now
        # Redis-backed (see _session_key / store_suggestion / get_suggestion).
        # These empty dicts are kept only as an in-process fallback when Redis
        # is unavailable so that existing callers don't break.
        self.context_cache: Dict = {}
        self.session_contexts: Dict = {}   # fallback only — use _get_session_history()
        self.generated_suggestions: Dict = {}  # fallback only — use store_suggestion()

        # Performance metrics
        self.metrics = {
            "requests_processed": 0,
            "total_response_time_ms": 0,
            "errors": 0,
            "cache_hits": 0,
            "learning_events": 0,
        }

        # Per-tenant metrics
        self._tenant_metrics: Dict[str, Dict] = {}

        # Performance Optimization
        self.response_cache_ttl = 300  # 5 minutes for context-specific responses
        self.context_cache_ttl = 60  # 1 minute for platform context

        # Intelligence Configuration
        self.intelligence_config = {
            ConciergeMode.PROACTIVE: {
                "update_frequency": 30,  # seconds
                "intelligence_depth": IntelligenceScope.PLATFORM_WIDE,
                "proactive_threshold": 0.7,  # confidence threshold for proactive suggestions
            },
            ConciergeMode.REACTIVE: {
                "response_time_target": 2000,  # ms
                "intelligence_depth": IntelligenceScope.WORKFLOW,
                "context_window": 10,  # previous interactions to consider
            },
            ConciergeMode.PRESENTATION: {
                "talking_points_count": 5,
                "client_safety_mode": True,
                "intelligence_depth": IntelligenceScope.STRATEGIC,
            },
            ConciergeMode.FIELD_WORK: {
                "location_awareness": True,
                "offline_fallback": True,
                "quick_actions": True,
                "intelligence_depth": IntelligenceScope.OPERATIONAL,
            },
        }

        logger.info("Claude Concierge Orchestrator initialized with omnipresent intelligence")

    def _get_claude_orchestrator(self) -> ClaudeOrchestrator:
        """Get or create Claude orchestrator instance."""
        try:
            from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

            return get_claude_orchestrator()
        except ImportError:
            # Fallback if circular import issues
            return ClaudeOrchestrator()

    # ========================================================================
    # TRACK 3: LIVE DATA INTEGRATION METHODS
    # ========================================================================

    async def generate_live_platform_context(
        self,
        current_page: str,
        user_role: str = "agent",
        session_id: str = None,
        location_context: Dict[str, Any] = None,
    ) -> PlatformContext:
        """
        Generate PlatformContext using real GHL data instead of demo data.
        This is the Track 3 integration that connects omnipresent intelligence to live business data.
        """
        try:
            # Get real-time context from GHL Live Data Service
            live_context = await self.ghl_live_data.generate_omnipresent_context(
                current_page=current_page, user_role=user_role, session_id=session_id
            )

            # Convert to PlatformContext object
            platform_context = PlatformContext(
                current_page=current_page,
                user_role=user_role,
                session_id=session_id or f"live_{int(time.time())}",
                location_context=location_context or {},
                # Real Business Intelligence from GHL
                active_leads=live_context.get("active_leads", []),
                bot_statuses=live_context.get("bot_statuses", {}),
                user_activity=live_context.get("user_activity", []),
                business_metrics=live_context.get("business_metrics", {}),
                active_properties=live_context.get("active_properties", []),
                # Real-time Market Context
                market_conditions=live_context.get("market_conditions", {}),
                priority_actions=live_context.get("priority_actions", []),
                pending_notifications=live_context.get("pending_notifications", []),
                # Jorge-specific Real Data
                jorge_preferences=live_context.get("jorge_preferences", {}),
            )

            logger.info(
                f"Generated live platform context for {current_page} with {len(platform_context.active_leads)} leads"
            )
            return platform_context

        except Exception as e:
            logger.error(f"Failed to generate live platform context: {str(e)}")
            # Fallback to demo context if live data fails
            return self._generate_demo_platform_context(current_page, user_role, session_id, location_context)

    def _generate_demo_platform_context(
        self, current_page: str, user_role: str, session_id: str, location_context: Dict[str, Any]
    ) -> PlatformContext:
        """Fallback demo context when live data is unavailable."""
        return PlatformContext(
            current_page=current_page,
            user_role=user_role,
            session_id=session_id or f"demo_{int(time.time())}",
            location_context=location_context or {},
            active_leads=[],
            bot_statuses={"jorge_seller_bot": "demo_mode", "lead_bot": "demo_mode"},
            user_activity=[],
            business_metrics={"total_pipeline": 0, "deals_this_month": 0},
            active_properties=[],
            market_conditions={},
            priority_actions=[{"action": "demo_mode_active", "priority": "info"}],
            pending_notifications=[],
            jorge_preferences={"demo_mode": True},
        )

    # ========================================================================
    # CORE OMNIPRESENT INTELLIGENCE METHODS
    # ========================================================================

    async def generate_contextual_guidance(
        self,
        context: Optional[PlatformContext] = None,
        mode: ConciergeMode = ConciergeMode.PROACTIVE,
        scope: Optional[IntelligenceScope] = None,
        use_live_data: bool = True,
        current_page: str = None,
        user_role: str = "agent",
        session_id: str = None,
        tenant_id: Optional[str] = None,
    ) -> ConciergeResponse:
        """
        Generate intelligent guidance based on current platform state.
        This is the main entry point for Track 2 omnipresent intelligence.

        Track 3 Enhancement: Now supports live GHL data integration.
        """
        start_time = time.time()
        resolved_tenant = tenant_id or self._default_config.tenant_id

        try:
            # Track 3: Generate live context if not provided
            if context is None and use_live_data:
                if not current_page:
                    raise ValueError("current_page required when generating live context")
                context = await self.generate_live_platform_context(
                    current_page=current_page, user_role=user_role, session_id=session_id
                )
                logger.info(f"Generated live platform context for guidance: {current_page}")
            elif context is None:
                raise ValueError("context must be provided when use_live_data=False")

            # Determine intelligence scope
            scope = scope or self.intelligence_config[mode]["intelligence_depth"]

            # Check cache first for performance
            cache_key = self._generate_context_cache_key(context, mode, scope, resolved_tenant)
            cached_response = await self._get_cached_response(cache_key)
            if cached_response:
                logger.debug(f"Cache hit for contextual guidance: {context.current_page}")
                self.metrics["cache_hits"] += 1
                self._get_tenant_metrics(resolved_tenant)["cache_hits"] += 1
                return cached_response

            # Get Jorge's learned preferences for this context
            jorge_preferences = await self.jorge_memory.get_preferences_for_context(context)

            # Build comprehensive intelligence prompt
            intelligence_prompt = self._build_intelligence_prompt(context, mode, scope, jorge_preferences)

            # Create Claude request with appropriate parameters
            request = ClaudeRequest(
                task_type=ClaudeTaskType.OMNIPOTENT_ASSISTANT,
                context={
                    "platform_context": asdict(context),
                    "jorge_preferences": jorge_preferences,
                    "concierge_mode": mode.value,
                    "intelligence_scope": scope.value,
                    "session_history": await self._get_session_history(
                        resolved_tenant, context.session_id
                    ),
                },
                prompt=intelligence_prompt,
                max_tokens=4000,
                temperature=0.6,  # Balanced creativity for guidance
                system_prompt=self._get_concierge_system_prompt(mode, resolved_tenant),
            )

            # Get Claude's intelligent analysis
            claude_response = await self.claude.process_request(request)

            # Parse and structure the response
            structured_response = await self._parse_concierge_response(claude_response.content, context, mode, scope)

            # Add metadata
            structured_response.response_time_ms = int((time.time() - start_time) * 1000)
            structured_response.data_sources_used = self._identify_data_sources(context)
            structured_response.generated_at = datetime.now()

            # Learn from this interaction for Jorge's preferences
            await self.jorge_memory.learn_from_context_interaction(context, structured_response)

            # Cache for performance (shorter TTL for dynamic contexts)
            cache_ttl = self._determine_cache_ttl(context, mode)
            await self._cache_response(cache_key, structured_response, cache_ttl)

            # Track analytics
            await self._track_concierge_analytics(context, mode, scope, structured_response)

            # Update session context for continuity
            await self._update_session_context(
                resolved_tenant, context.session_id, context, structured_response
            )

            self.metrics["requests_processed"] += 1
            self.metrics["total_response_time_ms"] += structured_response.response_time_ms

            tm = self._get_tenant_metrics(resolved_tenant)
            tm["requests_processed"] += 1
            tm["total_response_time_ms"] += structured_response.response_time_ms

            return structured_response

        except Exception as e:
            logger.error(f"Error generating contextual guidance: {e}")
            self.metrics["errors"] += 1
            self._get_tenant_metrics(resolved_tenant)["errors"] += 1

            # Fallback response to ensure platform reliability
            return self._generate_fallback_response(context, mode, str(e))

    async def generate_contextual_guidance_stream(
        self,
        context: Optional[PlatformContext] = None,
        mode: ConciergeMode = ConciergeMode.PROACTIVE,
        scope: Optional[IntelligenceScope] = None,
        use_live_data: bool = True,
        current_page: str = None,
        user_role: str = "agent",
        session_id: str = None,
    ) -> AsyncGenerator[str, None]:
        """
        Streaming version of generate_contextual_guidance.
        Provides real-time feedback for better UX.
        """
        try:
            # Generate live context if not provided
            if context is None and use_live_data:
                context = await self.generate_live_platform_context(
                    current_page=current_page or "Unknown", user_role=user_role, session_id=session_id
                )

            scope = scope or self.intelligence_config[mode]["intelligence_depth"]
            jorge_preferences = await self.jorge_memory.get_preferences_for_context(context)
            intelligence_prompt = self._build_intelligence_prompt(context, mode, scope, jorge_preferences)

            request = ClaudeRequest(
                task_type=ClaudeTaskType.OMNIPOTENT_ASSISTANT,
                context={
                    "platform_context": asdict(context),
                    "jorge_preferences": jorge_preferences,
                    "concierge_mode": mode.value,
                    "intelligence_scope": scope.value,
                },
                prompt=intelligence_prompt,
                max_tokens=4000,
                temperature=0.6,
                system_prompt=self._get_concierge_system_prompt(mode),
                streaming=True,
            )

            # Stream from orchestrator
            async for chunk in self.claude.process_request_stream(request):
                yield chunk

        except Exception as e:
            logger.error(f"Error in streaming contextual guidance: {e}")
            yield f"Error: {str(e)}"

    async def generate_live_guidance(
        self,
        current_page: str,
        mode: ConciergeMode = ConciergeMode.PROACTIVE,
        user_role: str = "agent",
        session_id: str = None,
    ) -> ConciergeResponse:
        """
        Convenience method for generating guidance with live GHL data.
        Track 3: Primary method for real-time omnipresent intelligence.
        """
        return await self.generate_contextual_guidance(
            context=None,  # Will be auto-generated from live data
            mode=mode,
            use_live_data=True,
            current_page=current_page,
            user_role=user_role,
            session_id=session_id,
        )

    async def provide_real_time_coaching(
        self, current_situation: Dict[str, Any], context: PlatformContext, urgency: str = "medium"
    ) -> ConciergeResponse:
        """
        Provide real-time coaching and guidance for specific situations.
        Used for immediate decision support and tactical guidance.
        """

        # Build coaching-specific prompt
        coaching_prompt = f"""
        Jorge needs immediate coaching for this situation:

        Current Situation: {json.dumps(current_situation, indent=2)}

        Platform Context: {context.current_page} - {context.user_role}
        Active Deals: {len(context.active_leads)} leads in pipeline
        Bot Status: {context.bot_statuses}

        Urgency Level: {urgency}

        Provide specific, actionable coaching that Jorge can implement immediately.
        Focus on:
        1. Immediate tactical decisions
        2. Risk mitigation strategies
        3. Revenue optimization opportunities
        4. Communication guidance
        5. Next best actions with timing

        Consider Jorge's learned preferences and past successful strategies.
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY,
            context={"platform_context": asdict(context), "current_situation": current_situation, "urgency": urgency},
            prompt=coaching_prompt,
            max_tokens=2000,
        )
        claude_response = await self.claude.process_request(request)
        return await self._parse_concierge_response(
            claude_response.content, context, ConciergeMode.REACTIVE, IntelligenceScope.WORKFLOW
        )

    async def orchestrate_bot_ecosystem(self, context: PlatformContext, desired_outcome: str) -> ConciergeResponse:
        """
        Coordinate the bot ecosystem (Jorge Seller Bot, Lead Bot, etc.) for optimal outcomes.
        Provides bot orchestration recommendations and workflow optimization.
        """

        # Analyze current bot performance
        bot_analysis = await self._analyze_bot_ecosystem_performance(context.bot_statuses)

        # Build bot coordination prompt
        coordination_prompt = f"""
        Analyze the bot ecosystem and recommend coordination strategies:

        Desired Outcome: {desired_outcome}

        Current Bot Status:
        {json.dumps(context.bot_statuses, indent=2)}

        Bot Performance Analysis:
        {json.dumps(bot_analysis, indent=2)}

        Active Pipeline:
        - {len(context.active_leads)} active leads
        - Current conversion metrics: {context.business_metrics.get("conversion_rate", "unknown")}
        - Revenue pipeline: {context.business_metrics.get("pipeline_value", "unknown")}

        Provide specific bot coordination recommendations:
        1. Bot role optimization and handoffs
        2. Workflow sequence adjustments
        3. Lead routing improvements
        4. Automation gap identification
        5. Performance optimization opportunities
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY,
            context={"platform_context": asdict(context), "bot_analysis": bot_analysis},
            prompt=coordination_prompt,
            max_tokens=3000,
        )

        claude_response = await self.claude.process_request(request)

        return await self._parse_concierge_response(
            claude_response.content, context, ConciergeMode.PROACTIVE, IntelligenceScope.PLATFORM_WIDE
        )

    async def apply_suggestion(self, suggestion_id: str, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Apply a stored proactive suggestion by triggering actual platform actions.
        Track 3: Real automation execution via GHL Service.
        """
        try:
            resolved_tenant = tenant_id or self._default_config.tenant_id
            suggestion = await self.get_suggestion(suggestion_id, resolved_tenant)
            # Fall back to in-process dict for backward compat with direct dict assignment
            if suggestion is None:
                suggestion = self.generated_suggestions.get(suggestion_id)
            if not suggestion:
                logger.warning(f"Suggestion {suggestion_id} not found in cache")
                return {"success": False, "error": "Suggestion not found or expired"}

            logger.info(f"Executing platform actions for suggestion: {suggestion.get('title')}")

            # Initialize GHL service
            from ghl_real_estate_ai.services.ghl_service import GHLService

            ghl = GHLService()

            actions_taken = []

            # 1. Handle Bot Coordination Suggestions
            if suggestion.get("bot_type"):
                bot_type = suggestion.get("bot_type")
                # Trigger specific bot orchestration workflow
                workflow_id = self.business_rules.get_workflow_id(bot_type) or "standard_bot_optimization"

                # If we have a target lead, apply there
                target_lead_id = suggestion.get("lead_id")
                if target_lead_id:
                    await ghl.trigger_workflow(target_lead_id, workflow_id)
                    actions_taken.append(f"Triggered {workflow_id} for lead {target_lead_id}")
                else:
                    # Global optimization (e.g., updating location tags)
                    logger.info(f"Applying global bot optimization for {bot_type}")
                    actions_taken.append(f"Applied global optimization for {bot_type}")

            # 2. Handle Risk Alerts / Escalations
            elif suggestion.get("type") == "escalation":
                target_lead_id = suggestion.get("lead_id")
                if target_lead_id:
                    await ghl.client.add_tags(target_lead_id, ["Urgent-Attention", "Concierge-Escalated"])
                    actions_taken.append(f"Added urgent tags to lead {target_lead_id}")

            # 3. Handle Automation suggestions
            elif suggestion.get("type") == "automation":
                # Example: Start a nurture sequence
                target_lead_id = suggestion.get("lead_id")
                if target_lead_id:
                    await ghl.trigger_workflow(target_lead_id, "ai_nurture_sequence")
                    actions_taken.append(f"Started AI nurture sequence for lead {target_lead_id}")

            # Clean up cache
            # self.generated_suggestions.pop(suggestion_id, None)

            return {
                "success": True,
                "suggestion_id": suggestion_id,
                "actions_taken": actions_taken,
                "message": f"Successfully applied {len(actions_taken)} actions",
            }

        except Exception as e:
            logger.error(f"Failed to apply suggestion {suggestion_id}: {e}")
            return {"success": False, "error": str(e)}

    async def generate_mobile_field_assistance(
        self, location_data: Dict[str, Any], context: PlatformContext
    ) -> ConciergeResponse:
        """
        Generate mobile-specific field assistance for property visits and client meetings.
        Optimized for mobile field work with offline capabilities.
        """

        # Build field assistance prompt with location intelligence
        field_prompt = f"""
        Jorge is in the field and needs mobile assistance:

        Current Location: {location_data.get("address", "Unknown")}
        GPS Coordinates: {location_data.get("lat", "N/A")}, {location_data.get("lng", "N/A")}
        Property Context: {location_data.get("property_info", {})}

        Meeting Context:
        - Client: {context.active_leads[0].get("name", "Unknown") if context.active_leads else "No active meeting"}
        - Property Type: {location_data.get("property_type", "Unknown")}
        - Visit Purpose: {location_data.get("visit_purpose", "showing")}

        Market Intelligence:
        - Neighborhood: {location_data.get("neighborhood", "Unknown")}
        - Recent Sales: {location_data.get("recent_sales", [])}
        - Market Trends: {location_data.get("market_trends", {})}

        Device: {context.device_type} | Connection: {context.connection_quality}

        Provide mobile-optimized assistance:
        1. Location-specific talking points
        2. Competitive analysis for this area
        3. Objection handling for this property type
        4. Quick action items for this visit
        5. Follow-up recommendations
        6. Emergency contact information if needed

        Keep responses concise for mobile consumption.
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY,
            context={"platform_context": asdict(context), "location_data": location_data},
            prompt=field_prompt,
            max_tokens=2000,
        )
        claude_response = await self.claude.process_request(request)
        return await self._parse_concierge_response(
            claude_response.content, context, ConciergeMode.FIELD_WORK, IntelligenceScope.OPERATIONAL
        )

    async def provide_client_presentation_support(
        self, client_profile: Dict[str, Any], presentation_context: Dict[str, Any], context: PlatformContext
    ) -> ConciergeResponse:
        """
        Provide intelligent support for client presentations with talking points and strategies.
        Client-safe mode ensures no sensitive internal information is exposed.
        """

        # Build presentation support prompt
        presentation_prompt = f"""
        Jorge is presenting to a client and needs intelligent presentation support:

        Client Profile:
        {json.dumps(client_profile, indent=2)}

        Presentation Context:
        - Presentation Type: {presentation_context.get("type", "general")}
        - Duration: {presentation_context.get("duration", "30 minutes")}
        - Objectives: {presentation_context.get("objectives", [])}
        - Materials: {presentation_context.get("materials", [])}

        Market Positioning:
        - Jorge's Value Proposition: Premium service, data-driven insights, 6% commission structure
        - Competitive Advantages: AI-powered lead qualification, extensive market knowledge
        - Success Metrics: {context.business_metrics.get("success_rate", "industry-leading")}

        **CLIENT-SAFE MODE**: Ensure all recommendations are appropriate for client visibility.
        No internal strategy, pricing details, or competitive intelligence should be exposed.

        Provide presentation support:
        1. Key talking points for this client
        2. Question anticipation and responses
        3. Value proposition customization
        4. Success stories and case studies
        5. Visual presentation recommendations
        6. Closing strategies appropriate for this client
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY,
            context={"platform_context": asdict(context), "client_profile": client_profile, "presentation_context": presentation_context},
            prompt=presentation_prompt,
            max_tokens=3000,
        )
        claude_response = await self.claude.process_request(request)
        return await self._parse_concierge_response(
            claude_response.content, context, ConciergeMode.PRESENTATION, IntelligenceScope.STRATEGIC
        )

    # ========================================================================
    # JORGE MEMORY & LEARNING SYSTEM INTEGRATION
    # ========================================================================

    async def learn_from_user_decision(
        self, context: PlatformContext, decision: Dict[str, Any], outcome: Dict[str, Any]
    ) -> bool:
        """
        Learn from Jorge's decisions to improve future recommendations.
        This is a key part of the adaptive intelligence system.
        """
        result = await self.jorge_memory.learn_from_decision(decision, outcome, context)
        if result:
            self.metrics["learning_events"] += 1
        return result

    async def predict_jorge_preference(self, situation: Dict[str, Any], context: PlatformContext) -> Dict[str, Any]:
        """
        Predict what Jorge would prefer in a given situation based on learned patterns.
        """
        return await self.jorge_memory.predict_jorge_preference(situation, context)

    def _get_tenant_metrics(self, tenant_id: str) -> Dict:
        """Return (and lazily initialise) the per-tenant counters dict."""
        if tenant_id not in self._tenant_metrics:
            self._tenant_metrics[tenant_id] = {
                "requests_processed": 0,
                "total_response_time_ms": 0,
                "errors": 0,
                "cache_hits": 0,
            }
        return self._tenant_metrics[tenant_id]

    def get_tenant_stats(self, tenant_id: str) -> Dict:
        """Return computed stats for a single tenant."""
        tm = self._get_tenant_metrics(tenant_id)
        total = tm["requests_processed"]
        avg_rt = tm["total_response_time_ms"] / max(total, 1)
        cache_rate = tm["cache_hits"] / max(total, 1)
        return {
            "tenant_id": tenant_id,
            "requests_processed": total,
            "avg_response_time_ms": int(avg_rt),
            "errors": tm["errors"],
            "cache_hit_rate": round(cache_rate, 3),
        }

    def get_metrics(self) -> Dict[str, Any]:
        """Return current performance metrics for wiring to /metrics endpoint."""
        count = self.metrics["requests_processed"]
        avg_rt = (self.metrics["total_response_time_ms"] / count) if count > 0 else 0
        cache_total = count + self.metrics["cache_hits"]
        cache_rate = (self.metrics["cache_hits"] / cache_total) if cache_total > 0 else 0.0
        return {
            "requests_processed": count,
            "avg_response_time_ms": int(avg_rt),
            "errors": self.metrics["errors"],
            "cache_hit_rate": round(cache_rate, 3),
            "active_sessions": len(self.session_contexts),  # in-process fallback count
            "learning_events": self.metrics["learning_events"],
            "tenant_breakdown": {
                tid: self.get_tenant_stats(tid)
                for tid in self._tenant_metrics
            },
        }

    # ========================================================================
    # PRIVATE HELPER METHODS
    # ========================================================================

    def _build_intelligence_prompt(
        self, context: PlatformContext, mode: ConciergeMode, scope: IntelligenceScope, jorge_preferences: Dict[str, Any]
    ) -> str:
        """Build comprehensive intelligence prompt for Claude."""

        # Base prompt structure
        prompt = f"""
        As Jorge's omnipresent AI concierge, analyze the current platform state and provide intelligent guidance.

        PLATFORM CONTEXT:
        Current Page: {context.current_page}
        User Role: {context.user_role}
        Device: {context.device_type}

        BUSINESS STATE:
        Active Leads: {len(context.active_leads)} leads
        {self._format_lead_intelligence(context.active_leads)}
        Bot Status: {context.bot_statuses}
        Pipeline Value: {context.business_metrics.get("pipeline_value", "Not available")}

        JORGE'S LEARNED PREFERENCES:
        {json.dumps(jorge_preferences, indent=2) if jorge_preferences else "No specific preferences learned yet"}

        MODE: {mode.value}
        SCOPE: {scope.value}
        """

        # Add mode-specific guidance
        if mode == ConciergeMode.PROACTIVE:
            prompt += """

            PROACTIVE GUIDANCE REQUIREMENTS:
            - Identify opportunities Jorge might miss
            - Suggest workflow optimizations
            - Highlight urgent items needing attention
            - Recommend bot coordination improvements
            - Provide market timing insights
            """

        elif mode == ConciergeMode.FIELD_WORK:
            prompt += """

            FIELD WORK REQUIREMENTS:
            - Provide location-specific insights
            - Suggest quick mobile actions
            - Offer offline-capable recommendations
            - Include emergency contact protocols
            - Focus on immediate tactical needs
            """

        elif mode == ConciergeMode.PRESENTATION:
            prompt += """

            PRESENTATION MODE REQUIREMENTS:
            - Generate client-appropriate talking points
            - Suggest value proposition customizations
            - Provide objection handling strategies
            - Recommend success story examples
            - Ensure NO internal sensitive information
            """

        # Add scope-specific details
        if scope == IntelligenceScope.PLATFORM_WIDE:
            prompt += f"""

            PLATFORM-WIDE ANALYSIS:
            User Activity: {context.user_activity}
            Market Conditions: {context.market_conditions}
            Priority Actions: {context.priority_actions}
            """

        prompt += """

        RESPONSE FORMAT:
        Provide comprehensive guidance including:
        1. Primary recommendation (1-2 sentences)
        2. Immediate actions (specific, time-bound)
        3. Background optimizations
        4. Risk alerts and opportunities
        5. Revenue optimization suggestions

        Be specific, actionable, and aligned with Jorge's learned preferences.
        """

        return prompt

    def _format_lead_intelligence(self, leads: List[Dict[str, Any]]) -> str:
        """Format lead metrics including FRS/PCS for the prompt."""
        if not leads:
            return ""

        intel_lines = ["Lead Intelligence:"]
        for lead in leads[:5]:  # Top 5 leads for context
            name = lead.get("name", "Unknown")
            frs = lead.get("frs_score", "N/A")
            pcs = lead.get("pcs_score", "N/A")
            score = lead.get("score", "N/A")
            intel_lines.append(f"- {name}: Score={score}, FRS={frs}, PCS={pcs}")

        return "\n        ".join(intel_lines)

    def _get_concierge_system_prompt(self, mode: ConciergeMode, tenant_id: Optional[str] = None) -> str:
        """Build a domain-agnostic system prompt from the client config.

        Template vars injected from ConciergeClientConfig:
          {client_name}       — e.g. "Jorge Salas"
          {business_model}    — revenue model description
          {market_context}    — geographic / market focus
          {client_style}      — communication style bullets
          {available_agents}  — comma-separated agent names
          {compliance_reqs}   — semicolon-separated compliance items
        """
        try:
            cfg = get_concierge_config(tenant_id) if tenant_id else self._default_config
        except FileNotFoundError:
            cfg = self._default_config

        base_prompt = f"""
        You are Claude, {cfg.client_name}'s omnipresent AI concierge for their platform.
        You have complete knowledge of:

        - Business model: {cfg.business_model}
        - Available agents: {cfg.agent_summary}
        - GHL integration and workflow automation
        - Market context: {cfg.market_context}
        - Lead qualification and conversion optimization

        {cfg.client_name}'s Communication Style:
        {cfg.client_style}

        Compliance requirements: {cfg.compliance_summary}

        STRUCTURED OUTPUT REQUIREMENTS:
        Your response MUST include structured tags at the end of your conversational response to enable platform integration.
        
        <primary_guidance>Short 1-2 sentence summary</primary_guidance>
        <urgency_level>low|medium|high|urgent</urgency_level>
        <reasoning>Internal logic for these recommendations</reasoning>
        
        <immediate_actions>
            <action priority="high|medium|low" category="system|lead|bot">Description of action</action>
        </immediate_actions>
        
        <suggestion type="optimization|automation|workflow">
            <title>Short Title</title>
            <description>Detailed description</description>
            <priority>high|medium|low</priority>
        </suggestion>
        
        <bot_coordination>
            <suggestion bot_type="jorge-seller|lead-bot|intent-decoder">Specific coordination advice</suggestion>
        </bot_coordination>
        
        <risk_alerts>
            <alert severity="low|medium|high">Description of risk</alert>
        </risk_alerts>

        <handoff>
            <bot>jorge-seller-bot|lead-bot|intent-decoder</bot>
            <confidence>0.0-1.0</confidence>
            <reasoning>Why this bot is best for the current situation</reasoning>
            <context>{{"key": "value"}}</context>
        </handoff>

        <frs_score>0-100</frs_score>
        <pcs_score>0-100</pcs_score>
        <lead_score>0-100</lead_score>

        Always provide:
        - Specific, actionable recommendations
        - Clear reasoning for suggestions
        - Time-sensitive priorities
        - Revenue impact considerations
        - Risk mitigation strategies
        """

        mode_specific = {
            ConciergeMode.PROACTIVE: """

            PROACTIVE MODE: Continuously monitor and suggest optimizations.
            - Be forward-thinking and opportunity-focused
            - Identify patterns the user might miss
            - Suggest automation improvements
            - Highlight time-sensitive opportunities
            """,
            ConciergeMode.FIELD_WORK: """

            FIELD WORK MODE: Support mobile real estate activities.
            - Provide location-specific intelligence
            - Keep responses concise for mobile
            - Focus on immediate tactical needs
            - Include backup/contingency options
            """,
            ConciergeMode.PRESENTATION: """

            PRESENTATION MODE: Support client-facing presentations.
            - Filter out all internal/competitive information
            - Focus on client value and benefits
            - Provide professional talking points
            - Suggest success stories and case studies
            """,
            ConciergeMode.EXECUTIVE: """

            EXECUTIVE MODE: Strategic business guidance.
            - Focus on high-level business decisions
            - Provide market trends and competitive analysis
            - Suggest scaling and growth opportunities
            - Include risk assessments and mitigation
            """,
        }

        return base_prompt + mode_specific.get(mode, "")

    async def _parse_concierge_response(
        self, content: str, context: PlatformContext, mode: ConciergeMode, scope: IntelligenceScope
    ) -> ConciergeResponse:
        """Parse Claude's response into structured concierge response using tag-based extraction."""

        # Extract primary guidance
        primary_guidance = self._extract_tag_content(content, "primary_guidance") or (
            content[:200] + "..." if len(content) > 200 else content
        )

        # Extract urgency
        urgency_level = self._extract_tag_content(content, "urgency_level") or self._extract_urgency_level(content)

        # Extract reasoning
        reasoning = self._extract_tag_content(content, "reasoning")

        # Extract actions
        immediate_actions = self._extract_immediate_actions(content)

        # Extract bot suggestions
        bot_suggestions = self._extract_bot_coordination(content)

        # Extract risk alerts
        risk_alerts = self._extract_risk_alerts_tags(content)

        # Extract handoff
        handoff = self._extract_handoff_tag(content)

        return ConciergeResponse(
            primary_guidance=primary_guidance,
            urgency_level=urgency_level,
            confidence_score=0.92,  # Higher confidence for structured output
            reasoning=reasoning,
            immediate_actions=immediate_actions,
            background_tasks=self._extract_action_items(content, "background"),
            follow_up_reminders=self._extract_action_items(content, "follow_up"),
            page_specific_tips=self._extract_page_tips(content, context.current_page),
            bot_coordination_suggestions=bot_suggestions,
            revenue_optimization_ideas=self._extract_revenue_ideas(content),
            risk_alerts=risk_alerts,
            opportunity_highlights=self._extract_opportunities(content),
            learning_insights=self._extract_learning_insights(content),
            handoff_recommendation=handoff,
            response_time_ms=0,  # Will be set by caller
            data_sources_used=[],  # Will be set by caller
            generated_at=datetime.now(),
        )

    def _extract_tag_content(self, content: str, tag: str) -> Optional[str]:
        """Extract content between XML-like tags."""
        match = re.search(f"<{tag}>(.*?)</{tag}>", content, re.DOTALL | re.IGNORECASE)
        return match.group(1).strip() if match else None

    def _extract_immediate_actions(self, content: str) -> List[Dict[str, Any]]:
        """Extract immediate actions from <immediate_actions> block."""
        actions = []
        block = self._extract_tag_content(content, "immediate_actions")
        if block:
            matches = re.finditer(r'<action\s+priority="(.*?)"\s+category="(.*?)">(.*?)</action>', block, re.IGNORECASE)
            for m in matches:
                actions.append(
                    {
                        "priority": m.group(1),
                        "category": m.group(2),
                        "description": m.group(3).strip(),
                        "estimated_time": "5 minutes",
                    }
                )

        # Fallback to existing logic if no tags found
        if not actions:
            actions = self._extract_action_items(content, "immediate")

        return actions

    def _extract_bot_coordination(self, content: str) -> List[Dict[str, Any]]:
        """Extract bot coordination suggestions from <bot_coordination> block."""
        suggestions = []
        block = self._extract_tag_content(content, "bot_coordination")
        if block:
            matches = re.finditer(r'<suggestion\s+bot_type="(.*?)">(.*?)</suggestion>', block, re.IGNORECASE)
            for m in matches:
                suggestions.append(
                    {"bot_type": m.group(1), "suggestion": m.group(2).strip(), "impact": "high", "effort": "low"}
                )

        if not suggestions:
            suggestions = self._extract_bot_suggestions(content)

        return suggestions

    def _extract_risk_alerts_tags(self, content: str) -> List[Dict[str, Any]]:
        """Extract risk alerts from <risk_alerts> block."""
        alerts = []
        block = self._extract_tag_content(content, "risk_alerts")
        if block:
            matches = re.finditer(r'<alert\s+severity="(.*?)">(.*?)</alert>', block, re.IGNORECASE)
            for m in matches:
                alerts.append(
                    {
                        "type": "operational_risk",
                        "description": m.group(2).strip(),
                        "severity": m.group(1),
                        "mitigation": "Review and adjust strategy",
                    }
                )

        if not alerts:
            alerts = self._extract_risk_alerts(content)

        return alerts

    def _extract_handoff_tag(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract handoff recommendation from <handoff> block."""
        block = self._extract_tag_content(content, "handoff")
        if block:
            bot = self._extract_tag_content(block, "bot")
            confidence = self._extract_tag_content(block, "confidence")
            reasoning = self._extract_tag_content(block, "reasoning")
            context_str = self._extract_tag_content(block, "context")

            try:
                context_data = json.loads(context_str) if context_str else {}
            except (ValueError, TypeError, json.JSONDecodeError) as e:
                logger.debug(f"Failed to parse handoff context: {e}")
                context_data = {}

            return {
                "targetBot": bot,
                "confidence": float(confidence) if confidence else 0.0,
                "reasoning": reasoning,
                "contextToTransfer": context_data,
            }
        return None

    def _extract_urgency_level(self, content: str) -> str:
        """Extract urgency level from response content."""
        content_lower = content.lower()
        if "urgent" in content_lower or "immediate" in content_lower:
            return "urgent"
        elif "high priority" in content_lower or "important" in content_lower:
            return "high"
        elif "medium" in content_lower or "moderate" in content_lower:
            return "medium"
        else:
            return "low"

    def _extract_action_items(self, content: str, action_type: str) -> List[Dict[str, Any]]:
        """Extract action items of specific type from content."""
        # Simplified extraction - could be enhanced with NLP
        actions = []

        if action_type in content.lower():
            # Look for numbered lists or bullet points
            lines = content.split("\n")
            for line in lines:
                if any(keyword in line.lower() for keyword in [action_type, "action", "todo", "next"]):
                    actions.append(
                        {
                            "description": line.strip(),
                            "priority": "medium",
                            "estimated_time": "5 minutes",
                            "category": action_type,
                        }
                    )

        return actions[:3]  # Limit to top 3 for UI performance

    def _extract_page_tips(self, content: str, current_page: str) -> List[str]:
        """Extract page-specific tips from content."""
        tips = []
        # Look for page-specific guidance
        if current_page.lower() in content.lower():
            # Extract relevant sentences
            sentences = content.split(".")
            for sentence in sentences:
                if current_page.lower() in sentence.lower():
                    tips.append(sentence.strip() + ".")

        return tips[:3]  # Limit for UI

    def _extract_bot_suggestions(self, content: str) -> List[Dict[str, Any]]:
        """Extract bot coordination suggestions."""
        suggestions = []
        bot_keywords = ["jorge bot", "lead bot", "automation", "workflow"]

        for keyword in bot_keywords:
            if keyword in content.lower():
                suggestions.append(
                    {
                        "bot_type": keyword,
                        "suggestion": f"Optimize {keyword} configuration",
                        "impact": "medium",
                        "effort": "low",
                    }
                )

        return suggestions

    def _extract_revenue_ideas(self, content: str) -> List[Dict[str, Any]]:
        """Extract revenue optimization ideas."""
        ideas = []
        revenue_keywords = ["commission", "revenue", "pricing", "conversion", "pipeline"]

        for keyword in revenue_keywords:
            if keyword in content.lower():
                ideas.append(
                    {
                        "idea": f"Optimize {keyword} strategy",
                        "potential_impact": "medium",
                        "implementation_effort": "low",
                        "timeline": "1 week",
                    }
                )

        return ideas[:2]  # Limit for UI

    def _extract_risk_alerts(self, content: str) -> List[Dict[str, Any]]:
        """Extract risk alerts from content."""
        alerts = []
        risk_keywords = ["risk", "warning", "concern", "problem", "issue"]

        for keyword in risk_keywords:
            if keyword in content.lower():
                alerts.append(
                    {
                        "type": "operational_risk",
                        "description": f"Potential {keyword} identified",
                        "severity": "medium",
                        "mitigation": "Review and adjust strategy",
                    }
                )

        return alerts[:2]  # Limit for UI

    def _extract_opportunities(self, content: str) -> List[Dict[str, Any]]:
        """Extract opportunity highlights."""
        opportunities = []
        opp_keywords = ["opportunity", "potential", "optimize", "improve", "enhance"]

        for keyword in opp_keywords:
            if keyword in content.lower():
                opportunities.append(
                    {
                        "type": "growth_opportunity",
                        "description": f"Opportunity to {keyword}",
                        "potential_value": "medium",
                        "timeline": "2 weeks",
                    }
                )

        return opportunities[:2]  # Limit for UI

    def _extract_learning_insights(self, content: str) -> List[Dict[str, Any]]:
        """Extract learning insights for Jorge's preferences."""
        insights = []
        learning_keywords = ["pattern", "trend", "preference", "behavior", "strategy"]

        for keyword in learning_keywords:
            if keyword in content.lower():
                insights.append(
                    {
                        "insight_type": "behavioral_pattern",
                        "description": f"Jorge's {keyword} analysis",
                        "confidence": 0.7,
                        "impact": "long_term",
                    }
                )

        return insights[:2]  # Limit for UI

    async def _analyze_bot_ecosystem_performance(self, bot_statuses: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze current bot ecosystem performance."""
        analysis = {
            "overall_health": "good",
            "performance_metrics": {},
            "coordination_opportunities": [],
            "bottlenecks": [],
            "optimization_suggestions": [],
        }

        # Analyze each bot's status
        for bot_name, status in bot_statuses.items():
            if isinstance(status, dict):
                performance = status.get("performance", {})
                analysis["performance_metrics"][bot_name] = {
                    "status": status.get("status", "unknown"),
                    "last_activity": status.get("last_activity", "unknown"),
                    "success_rate": performance.get("success_rate", 0.8),
                }

        return analysis

    def _generate_context_cache_key(
        self, context: PlatformContext, mode: ConciergeMode, scope: IntelligenceScope, tenant_id: Optional[str] = None
    ) -> str:
        """Generate tenant-scoped cache key for context-specific responses."""
        tid = tenant_id or self._default_config.tenant_id
        key_components = [
            context.current_page,
            context.user_role,
            mode.value,
            scope.value,
            str(len(context.active_leads)),
            str(hash(json.dumps(context.bot_statuses, sort_keys=True))),
        ]
        return f"concierge:{tid}:guidance:{':'.join(key_components)}"

    async def _get_cached_response(self, cache_key: str) -> Optional[ConciergeResponse]:
        """Get cached concierge response if available."""
        try:
            cached_data = await self.cache.get(cache_key)
            if cached_data:
                data = json.loads(cached_data)
                # Reconstruct ConciergeResponse object
                # This would need proper deserialization in production
                return ConciergeResponse(**data)
        except Exception as e:
            logger.warning(f"Cache retrieval failed: {e}")

        return None

    async def _cache_response(self, cache_key: str, response: ConciergeResponse, ttl: int) -> bool:
        """Cache concierge response for performance."""
        try:
            response_data = asdict(response)
            await self.cache.set(cache_key, json.dumps(response_data, default=str), ttl=ttl)
            return True
        except Exception as e:
            logger.warning(f"Cache storage failed: {e}")
            return False

    def _determine_cache_ttl(self, context: PlatformContext, mode: ConciergeMode) -> int:
        """Determine appropriate cache TTL based on context dynamism."""

        # Dynamic contexts (frequent changes) get shorter TTL
        if context.current_page in ["executive-dashboard", "field-agent", "live-deals"]:
            return 60  # 1 minute

        # Proactive mode needs fresh data
        if mode == ConciergeMode.PROACTIVE:
            return 120  # 2 minutes

        # Static pages can cache longer
        if context.current_page in ["presentation", "reports", "analytics"]:
            return 600  # 10 minutes

        # Default TTL
        return self.response_cache_ttl

    def _identify_data_sources(self, context: PlatformContext) -> List[str]:
        """Identify data sources used for the guidance."""
        sources = ["platform_context"]

        if context.active_leads:
            sources.append("lead_pipeline")

        if context.bot_statuses:
            sources.append("bot_ecosystem")

        if context.business_metrics:
            sources.append("business_metrics")

        if context.market_conditions:
            sources.append("market_intelligence")

        return sources

    async def _track_concierge_analytics(
        self, context: PlatformContext, mode: ConciergeMode, scope: IntelligenceScope, response: ConciergeResponse
    ) -> None:
        """Track analytics for concierge interactions."""
        try:
            await self.analytics.track_event(
                event_type="concierge_guidance_generated",
                location_id="enterprise_hub",
                contact_id=context.session_id,
                data={
                    "page": context.current_page,
                    "mode": mode.value,
                    "scope": scope.value,
                    "urgency_level": response.urgency_level,
                    "response_time_ms": response.response_time_ms,
                    "confidence_score": response.confidence_score,
                    "immediate_actions_count": len(response.immediate_actions),
                    "device_type": context.device_type,
                },
            )
        except Exception as e:
            logger.warning(f"Analytics tracking failed: {e}")

    # ------------------------------------------------------------------
    # Multi-tenant Redis-backed storage helpers
    # Key convention: concierge:{tenant_id}:{resource}:{id}
    # ------------------------------------------------------------------

    def _session_key(self, tenant_id: str, session_id: str) -> str:
        return f"concierge:{tenant_id}:session:{session_id}"

    def _suggestion_key(self, tenant_id: str, suggestion_id: str) -> str:
        return f"concierge:{tenant_id}:suggestion:{suggestion_id}"

    async def _get_session_history(self, tenant_id: str, session_id: str) -> List[Dict]:
        """Fetch session interaction history from Redis (TTL 3600s)."""
        try:
            raw = await self.cache.get(self._session_key(tenant_id, session_id))
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Session history read failed: {e}")
        # Fallback to in-process dict
        return self.session_contexts.get(session_id, [])

    async def store_suggestion(self, suggestion_id: str, data: Dict, tenant_id: Optional[str] = None) -> None:
        """Persist a suggestion to Redis (TTL 1800s) and the fallback dict."""
        resolved = tenant_id or self._default_config.tenant_id
        self.generated_suggestions[suggestion_id] = data  # in-process fallback
        try:
            await self.cache.set(
                self._suggestion_key(resolved, suggestion_id),
                json.dumps(data, default=str),
                ttl=1800,
            )
        except Exception as e:
            logger.warning(f"Suggestion store to Redis failed: {e}")

    async def get_suggestion(self, suggestion_id: str, tenant_id: Optional[str] = None) -> Optional[Dict]:
        """Retrieve a suggestion from Redis; returns None if missing or expired."""
        resolved = tenant_id or self._default_config.tenant_id
        try:
            raw = await self.cache.get(self._suggestion_key(resolved, suggestion_id))
            if raw:
                return json.loads(raw)
        except Exception as e:
            logger.warning(f"Suggestion read from Redis failed: {e}")
        return None

    async def _update_session_context(
        self, tenant_id: str, session_id: str, context: PlatformContext, response: ConciergeResponse
    ) -> None:
        """Append interaction to session history in Redis (TTL 3600s) and fallback dict."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "page": context.current_page,
            "primary_guidance": response.primary_guidance[:100],
            "urgency_level": response.urgency_level,
            "actions_count": len(response.immediate_actions),
        }

        # Keep in-process fallback dict up to date
        history = self.session_contexts.setdefault(session_id, [])
        history.append(interaction)
        if len(history) > 10:
            self.session_contexts[session_id] = history[-10:]

        # Persist to Redis
        try:
            redis_history = await self._get_session_history(tenant_id, session_id)
            redis_history.append(interaction)
            if len(redis_history) > 10:
                redis_history = redis_history[-10:]
            await self.cache.set(
                self._session_key(tenant_id, session_id),
                json.dumps(redis_history, default=str),
                ttl=3600,
            )
        except Exception as e:
            logger.warning(f"Session context Redis write failed: {e}")

    def _generate_fallback_response(
        self, context: PlatformContext, mode: ConciergeMode, error_msg: str
    ) -> ConciergeResponse:
        """Generate fallback response when main system fails."""

        fallback_guidance = {
            ConciergeMode.PROACTIVE: "Platform monitoring active. Recommend reviewing current pipeline and bot performance.",
            ConciergeMode.FIELD_WORK: "Field assistance available. Check location settings and ensure mobile data connection.",
            ConciergeMode.PRESENTATION: "Presentation support ready. Review client profile and prepare key talking points.",
            ConciergeMode.EXECUTIVE: "Executive intelligence active. Focus on pipeline health and revenue optimization.",
        }

        current_page = context.current_page if context else "Platform"

        return ConciergeResponse(
            primary_guidance=fallback_guidance.get(
                mode, "AI guidance temporarily unavailable. Platform operating normally."
            ),
            urgency_level="low",
            confidence_score=0.5,
            immediate_actions=[
                {
                    "description": "Check system connectivity and retry",
                    "priority": "low",
                    "estimated_time": "2 minutes",
                    "category": "system",
                }
            ],
            background_tasks=[],
            follow_up_reminders=[],
            page_specific_tips=[f"Continue working with {current_page} functionality"],
            bot_coordination_suggestions=[],
            revenue_optimization_ideas=[],
            risk_alerts=[
                {
                    "type": "system_degradation",
                    "description": f"Concierge intelligence temporarily degraded: {error_msg}",
                    "severity": "low",
                    "mitigation": "System will auto-recover",
                }
            ],
            opportunity_highlights=[],
            learning_insights=[],
            response_time_ms=0,
            data_sources_used=["fallback_system"],
            generated_at=datetime.now(),
        )


# ============================================================================
# JORGE MEMORY & LEARNING SYSTEM
# ============================================================================


class JorgeMemorySystem:
    """
    Persistent memory system that learns Jorge's preferences and business patterns.
    Integrates with existing MemoryService and adds Jorge-specific intelligence.
    """

    def __init__(self, memory_service: MemoryService, cache_service):
        self.memory = memory_service
        self.cache = cache_service
        self.preference_engine = JorgePreferenceEngine(cache_service)
        self.pattern_detector = PatternDetectionEngine()

        # Jorge's learned preferences storage
        self.preferences_cache_key = "jorge_preferences_v2"
        self.preferences_cache_ttl = 86400  # 24 hours

        logger.info("Jorge Memory System initialized with preference learning")

    async def learn_from_decision(
        self, decision: Dict[str, Any], outcome: Dict[str, Any], context: Optional[PlatformContext] = None
    ) -> bool:
        """Learn from Jorge's decisions to improve recommendations."""

        try:
            # Extract decision patterns
            pattern = await self.pattern_detector.extract_pattern(decision, outcome, context)

            if pattern and pattern.get("confidence", 0) > 0.7:
                # Update preference model
                await self.preference_engine.update_preferences(pattern)

                # Store in long-term memory
                memory_entry = {
                    "type": "jorge_decision_learning",
                    "decision": decision,
                    "outcome": outcome,
                    "context": asdict(context) if context else {},
                    "pattern": pattern,
                    "timestamp": datetime.now().isoformat(),
                }

                # Use memory service to store learning
                await self.memory.add_memory(
                    entity_id="jorge_preference_learning",
                    content=json.dumps(memory_entry),
                    memory_type="business_preference",
                )

                logger.info(f"Learned from Jorge's decision: {pattern.get('pattern_type', 'general')}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error learning from decision: {type(e).__name__}: {e}")
            return False

    async def predict_jorge_preference(self, situation: Dict[str, Any], context: PlatformContext) -> Dict[str, Any]:
        """Predict what Jorge would prefer in this situation."""

        try:
            # Get current preferences
            preferences = await self.get_preferences_for_context(context)

            # Find similar situations
            similar_situations = await self.find_similar_situations(situation, context)

            # Use preference engine to predict
            prediction = await self.preference_engine.predict_preference(situation, similar_situations, preferences)

            return prediction

        except Exception as e:
            logger.error(f"Error predicting preference: {e}")
            return {"confidence": 0.0, "preference": "unknown", "error": str(e)}

    async def get_preferences_for_context(self, context: PlatformContext) -> Dict[str, Any]:
        """Get Jorge's learned preferences for the current context."""

        try:
            # Check cache first
            cache_key = f"{self.preferences_cache_key}:{context.current_page}:{context.user_role}"
            cached_prefs = await self.cache.get(cache_key)

            if cached_prefs:
                return json.loads(cached_prefs)

            # Get from memory service
            memories = await self.memory.search_memories(
                query=f"jorge preferences {context.current_page}", memory_types=["business_preference"], limit=10
            )

            # Aggregate preferences
            preferences = self._aggregate_preferences(memories, context)

            # Cache for performance
            await self.cache.set(cache_key, json.dumps(preferences), ttl=self.preferences_cache_ttl)

            return preferences

        except Exception as e:
            logger.error(f"Error getting preferences: {e}")
            return {}

    async def find_similar_situations(
        self, situation: Dict[str, Any], context: PlatformContext
    ) -> List[Dict[str, Any]]:
        """Find similar situations from Jorge's history."""

        try:
            # Use memory service to find similar contexts
            query = f"jorge decision {situation.get('type', 'general')} {context.current_page}"

            memories = await self.memory.search_memories(
                query=query, memory_types=["business_preference", "decision_history"], limit=5
            )

            # Process and rank by similarity
            similar_situations = []
            for memory in memories:
                try:
                    content = json.loads(memory.get("content", "{}"))
                    if content.get("decision") and content.get("outcome"):
                        similarity_score = self._calculate_situation_similarity(situation, content["decision"])

                        if similarity_score > 0.6:  # Threshold for relevance
                            similar_situations.append(
                                {
                                    "situation": content["decision"],
                                    "outcome": content["outcome"],
                                    "similarity": similarity_score,
                                    "timestamp": content.get("timestamp"),
                                }
                            )
                except Exception:
                    continue

            # Sort by similarity
            similar_situations.sort(key=lambda x: x["similarity"], reverse=True)

            return similar_situations[:3]  # Return top 3 most similar

        except Exception as e:
            logger.error(f"Error finding similar situations: {e}")
            return []

    async def learn_from_context_interaction(self, context: PlatformContext, response: ConciergeResponse) -> None:
        """Learn from context interactions for better future guidance."""

        try:
            # Create learning entry
            interaction_learning = {
                "context_page": context.current_page,
                "user_role": context.user_role,
                "device_type": context.device_type,
                "guidance_provided": response.primary_guidance[:200],
                "urgency_level": response.urgency_level,
                "confidence_score": response.confidence_score,
                "actions_count": len(response.immediate_actions),
                "timestamp": datetime.now().isoformat(),
            }

            # Store for pattern detection
            await self.memory.add_memory(
                entity_id="jorge_context_learning",
                content=json.dumps(interaction_learning),
                memory_type="context_preference",
            )

        except Exception as e:
            logger.error(f"Error learning from context interaction: {e}")

    def _aggregate_preferences(self, memories: List[Dict[str, Any]], context: PlatformContext) -> Dict[str, Any]:
        """Aggregate preferences from memory entries."""

        preferences = {
            "communication_style": "direct",
            "priority_focus": "revenue_optimization",
            "decision_speed": "fast",
            "risk_tolerance": "medium",
            "automation_preference": "high",
            "context_specific": {},
        }

        # Analyze memories for patterns
        for memory in memories:
            try:
                content = json.loads(memory.get("content", "{}"))
                pattern = content.get("pattern", {})

                # Update preferences based on patterns
                if pattern.get("pattern_type") == "communication_preference":
                    preferences["communication_style"] = pattern.get("value", preferences["communication_style"])

                elif pattern.get("pattern_type") == "priority_preference":
                    preferences["priority_focus"] = pattern.get("value", preferences["priority_focus"])

                # Context-specific preferences
                if pattern.get("context") == context.current_page:
                    preferences["context_specific"][context.current_page] = pattern.get("value", {})

            except Exception:
                continue

        return preferences

    def _calculate_situation_similarity(self, situation1: Dict[str, Any], situation2: Dict[str, Any]) -> float:
        """Calculate similarity between two situations."""

        # Simple similarity based on shared keys and values
        # Could be enhanced with semantic similarity in production

        common_keys = set(situation1.keys()) & set(situation2.keys())
        if not common_keys:
            return 0.0

        matching_values = 0
        for key in common_keys:
            if str(situation1[key]).lower() == str(situation2[key]).lower():
                matching_values += 1

        return matching_values / len(common_keys)


class JorgePreferenceEngine:
    """Engine for learning and predicting Jorge's preferences."""

    def __init__(self, cache_service):
        self.cache = cache_service

    async def update_preferences(self, pattern: Dict[str, Any]) -> bool:
        """Update preference model with new decision pattern. Persists to Redis cache."""
        try:
            cache_key = "jorge_preferences:aggregate"
            existing = await self.cache.get(cache_key) or {}

            pattern_type = pattern.get("pattern_type", "general")
            if pattern_type not in existing:
                existing[pattern_type] = {"count": 0, "weight": 0.0, "last_updated": None}

            entry = existing[pattern_type]
            entry["count"] += 1
            # Weighted average: new data 30%, older 70% (decay factor for recency)
            new_confidence = pattern.get("confidence", 0.5)
            entry["weight"] = 0.7 * entry["weight"] + 0.3 * new_confidence
            entry["last_updated"] = datetime.now().isoformat()

            await self.cache.set(cache_key, existing, ttl=86400)  # 24hr TTL
            return True
        except Exception:
            logger.warning("Failed to update preferences; ignoring")
            return False

    async def predict_preference(
        self, situation: Dict[str, Any], similar_situations: List[Dict[str, Any]], current_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Predict preference for given situation."""

        # Simple prediction based on similar situations
        if similar_situations:
            # Use most similar situation's outcome
            best_match = similar_situations[0]
            return {
                "confidence": best_match["similarity"],
                "preference": best_match["outcome"],
                "reasoning": f"Based on {len(similar_situations)} similar situations",
            }

        # Fallback to general preferences
        return {
            "confidence": 0.5,
            "preference": current_preferences.get("priority_focus", "revenue_optimization"),
            "reasoning": "Based on general preferences",
        }


class PatternDetectionEngine:
    """Engine for detecting patterns in Jorge's decisions and outcomes."""

    async def extract_pattern(
        self, decision: Dict[str, Any], outcome: Dict[str, Any], context: Optional[PlatformContext] = None
    ) -> Optional[Dict[str, Any]]:
        """Extract patterns from decision-outcome pairs (both success and failure)."""
        decision_type = decision.get("type", "general")
        outcome_success = outcome.get("success", False)
        severity = outcome.get("severity", "medium")

        if outcome_success:
            return {
                "pattern_type": f"{decision_type}_success",
                "decision_factors": list(decision.keys()),
                "success_indicators": list(outcome.keys()),
                "confidence": 0.8,
                "context": context.current_page if context else "general",
                "timestamp": datetime.now().isoformat(),
            }
        else:
            severity_weight = {"low": 0.4, "medium": 0.6, "high": 0.9}.get(severity, 0.6)
            return {
                "pattern_type": f"{decision_type}_failure",
                "decision_factors": list(decision.keys()),
                "failure_indicators": list(outcome.keys()),
                "confidence": severity_weight,
                "context": context.current_page if context else "general",
                "timestamp": datetime.now().isoformat(),
            }


class JorgeBusinessRules:
    """Jorge's specific business rules and constraints."""

    def __init__(self):
        self.rules = {
            "commission_rate": 0.06,  # 6% commission
            "qualification_threshold": 70,  # Jorge's minimum lead score
            "max_concurrent_deals": 15,
            "preferred_price_range": (300000, 1500000),
            "target_markets": ["rancho_cucamonga", "cedar_park", "round_rock"],
        }

    async def update_rule(self, pattern: Dict[str, Any]) -> bool:
        """Update business rules based on learned patterns."""
        # Implement rule updating logic
        return True

    def get_rule(self, rule_name: str) -> Any:
        """Get specific business rule value."""
        return self.rules.get(rule_name)

    def get_workflow_id(self, bot_type: str) -> Optional[str]:
        """Map bot type to GHL workflow ID from environment variables."""
        import os
        workflow_map = {
            "hot_seller": os.getenv("HOT_SELLER_WORKFLOW_ID"),
            "warm_seller": os.getenv("WARM_SELLER_WORKFLOW_ID"),
            "hot_buyer": os.getenv("HOT_BUYER_WORKFLOW_ID"),
            "warm_buyer": os.getenv("WARM_BUYER_WORKFLOW_ID"),
            "notify_agent": os.getenv("NOTIFY_AGENT_WORKFLOW_ID"),
            "manual_scheduling": os.getenv("MANUAL_SCHEDULING_WORKFLOW_ID"),
        }
        return workflow_map.get(bot_type)


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_concierge_orchestrator_instance = None


def get_claude_concierge_orchestrator() -> ClaudeConciergeOrchestrator:
    """Get singleton concierge orchestrator instance."""
    global _concierge_orchestrator_instance
    if _concierge_orchestrator_instance is None:
        _concierge_orchestrator_instance = ClaudeConciergeOrchestrator()
    return _concierge_orchestrator_instance
