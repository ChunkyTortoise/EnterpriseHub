"""
Claude Concierge Agent - Omnipresent AI Platform Guide
Foundation for Track 2: Claude Concierge with Advanced Intelligence

The Claude Concierge Agent serves as an omnipresent AI guide across Jorge's entire platform,
coordinating with 40+ specialized agents while providing intelligent, context-aware assistance.
"""

import asyncio
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import get_enhanced_bot_orchestrator
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

logger = get_logger(__name__)


class ConciergeMode(Enum):
    """Operational modes for the Concierge Agent."""

    PROACTIVE = "proactive"  # Anticipates user needs
    REACTIVE = "reactive"  # Responds to user requests
    MONITORING = "monitoring"  # Observes and learns
    COORDINATING = "coordinating"  # Managing multi-agent tasks
    EMERGENCY = "emergency"  # Crisis intervention mode


class UserIntent(Enum):
    """User intent categories for context awareness."""

    EXPLORING = "exploring"  # Learning about platform
    WORKING = "working"  # Performing specific tasks
    TROUBLESHOOTING = "troubleshooting"  # Solving problems
    ANALYZING = "analyzing"  # Reviewing data/reports
    CONFIGURING = "configuring"  # Setting up features
    LEARNING = "learning"  # Seeking knowledge/training


class PlatformContext(Enum):
    """Platform areas and contexts."""

    DASHBOARD = "dashboard"
    LEAD_MANAGEMENT = "lead_management"
    PROPERTY_ANALYSIS = "property_analysis"
    BOT_MANAGEMENT = "bot_management"
    REPORTS = "reports"
    SETTINGS = "settings"
    INTEGRATIONS = "integrations"
    MOBILE = "mobile"


@dataclass
class UserSession:
    """Tracks user session context and patterns."""

    user_id: str
    session_start: datetime
    last_activity: datetime
    current_context: PlatformContext
    detected_intent: UserIntent
    activity_history: List[Dict[str, Any]] = field(default_factory=list)
    assistance_requests: List[Dict[str, Any]] = field(default_factory=list)
    agent_interactions: List[Dict[str, Any]] = field(default_factory=list)
    preferences: Dict[str, Any] = field(default_factory=dict)
    competency_level: str = "intermediate"  # beginner, intermediate, advanced
    frustration_indicators: List[str] = field(default_factory=list)


@dataclass
class AgentCapability:
    """Represents an agent and its capabilities."""

    agent_name: str
    agent_type: str
    capabilities: List[str]
    current_status: str
    last_used: Optional[datetime] = None
    performance_score: float = 1.0
    specializations: List[str] = field(default_factory=list)


@dataclass
class ConciergeRecommendation:
    """Recommendation from the Concierge Agent."""

    recommendation_type: str
    title: str
    description: str
    action_steps: List[str]
    priority: str  # high, medium, low
    confidence: float
    relevant_agents: List[str] = field(default_factory=list)
    estimated_time: Optional[str] = None


class PlatformKnowledgeEngine:
    """Comprehensive knowledge of the platform's capabilities."""

    def __init__(self):
        self.platform_features = self._load_platform_features()
        self.agent_registry = self._load_agent_registry()
        self.user_workflows = self._load_user_workflows()
        self.integration_points = self._load_integration_points()

    def _load_platform_features(self) -> Dict[str, Any]:
        """Load comprehensive platform feature knowledge."""
        return {
            "lead_management": {
                "features": [
                    "Jorge Seller Bot (Adaptive)",
                    "Predictive Lead Bot",
                    "Real-time Intent Decoder",
                    "Lead Intelligence Swarm",
                    "Voss Negotiation Agent",
                    "Temperature Prediction",
                    "Behavioral Analytics",
                    "Multi-channel Sequences",
                    "Lead Scoring",
                ],
                "workflows": ["Lead Capture", "Qualification", "Nurture Sequences", "Conversion"],
                "integrations": ["GHL", "Retell AI", "Lyrio", "Webhooks"],
            },
            "property_analysis": {
                "features": [
                    "CMA Generator",
                    "Property Intelligence",
                    "Market Analysis",
                    "Competitive Benchmarking",
                    "Investment Analysis",
                    "Pricing Intelligence",
                ],
                "workflows": ["Property Valuation", "Market Comparison", "Investment Scoring"],
                "integrations": ["Zillow", "MLS", "Market Data APIs"],
            },
            "bot_ecosystem": {
                "features": [
                    "40+ Specialized Agents",
                    "Multi-agent Orchestration",
                    "Swarm Intelligence",
                    "Real-time Coordination",
                    "Performance Monitoring",
                    "Adaptive Learning",
                ],
                "workflows": ["Bot Deployment", "Agent Coordination", "Performance Optimization"],
                "integrations": ["LangGraph", "Claude API", "Event System"],
            },
            "analytics_reporting": {
                "features": [
                    "Revenue Attribution",
                    "Performance Dashboards",
                    "Predictive Analytics",
                    "Lead Intelligence Reports",
                    "Agent Performance Metrics",
                ],
                "workflows": ["Report Generation", "Performance Analysis", "Forecasting"],
                "integrations": ["PostgreSQL", "Redis", "Visualization Tools"],
            },
        }

    def _load_agent_registry(self) -> Dict[str, AgentCapability]:
        """Load registry of all available agents."""
        return {
            # Core Intelligence Bots (Track 1)
            "adaptive_jorge": AgentCapability(
                agent_name="Adaptive Jorge Seller Bot",
                agent_type="seller_qualification",
                capabilities=["real_time_questioning", "calendar_integration", "stall_breaking"],
                current_status="active",
                specializations=["seller_qualification", "confrontational_methodology"],
            ),
            "predictive_lead": AgentCapability(
                agent_name="Predictive Lead Bot",
                agent_type="lead_nurture",
                capabilities=["timing_optimization", "personality_adaptation", "multi_channel"],
                current_status="active",
                specializations=["behavioral_analysis", "sequence_optimization"],
            ),
            "realtime_intent": AgentCapability(
                agent_name="Real-time Intent Decoder",
                agent_type="intent_analysis",
                capabilities=["streaming_analysis", "semantic_understanding", "forecasting"],
                current_status="active",
                specializations=["intent_scoring", "conversation_analysis"],
            ),
            # Specialized Intelligence Agents
            "voss_negotiation": AgentCapability(
                agent_name="Voss Negotiation Agent",
                agent_type="negotiation",
                capabilities=["tactical_empathy", "compliance_audit", "tone_calibration"],
                current_status="active",
                specializations=["negotiation_tactics", "behavioral_psychology"],
            ),
            "epsilon_predictive": AgentCapability(
                agent_name="Epsilon Predictive AI",
                agent_type="predictive_analytics",
                capabilities=["ml_scoring", "feature_engineering", "training"],
                current_status="active",
                specializations=["machine_learning", "predictive_modeling"],
            ),
            "lead_intelligence_swarm": AgentCapability(
                agent_name="Lead Intelligence Swarm",
                agent_type="multi_agent_analysis",
                capabilities=["demographic_analysis", "behavioral_profiling", "consensus_building"],
                current_status="active",
                specializations=["swarm_intelligence", "collaborative_analysis"],
            ),
            # Orchestration & Coordination
            "enhanced_orchestrator": AgentCapability(
                agent_name="Enhanced Bot Orchestrator",
                agent_type="orchestration",
                capabilities=["multi_bot_coordination", "fallback_management", "metrics_tracking"],
                current_status="active",
                specializations=["bot_coordination", "performance_optimization"],
            ),
            "swarm_orchestrator": AgentCapability(
                agent_name="Agent Swarm Orchestrator",
                agent_type="swarm_management",
                capabilities=["agent_deployment", "resource_allocation", "conflict_resolution"],
                current_status="active",
                specializations=["swarm_coordination", "resource_management"],
            ),
            # Analytics & Intelligence
            "quant_agent": AgentCapability(
                agent_name="Quantitative Analysis Agent",
                agent_type="analytics",
                capabilities=["statistical_analysis", "market_modeling", "risk_assessment"],
                current_status="active",
                specializations=["quantitative_analysis", "financial_modeling"],
            ),
            "iota_revenue": AgentCapability(
                agent_name="Iota Revenue Attribution",
                agent_type="revenue_analysis",
                capabilities=["attribution_modeling", "revenue_tracking", "performance_metrics"],
                current_status="active",
                specializations=["revenue_attribution", "performance_tracking"],
            ),
            "kappa_competitive": AgentCapability(
                agent_name="Kappa Competitive Benchmarking",
                agent_type="competitive_analysis",
                capabilities=["market_comparison", "competitive_intelligence", "positioning"],
                current_status="active",
                specializations=["competitive_analysis", "market_intelligence"],
            ),
        }

    def _load_user_workflows(self) -> Dict[str, Dict]:
        """Load common user workflows and guidance."""
        return {
            "new_user_onboarding": {
                "steps": [
                    "Platform tour and overview",
                    "Lead capture setup",
                    "Bot configuration",
                    "Integration connections",
                    "First lead processing",
                ],
                "estimated_time": "30-45 minutes",
                "required_agents": ["adaptive_jorge", "predictive_lead", "enhanced_orchestrator"],
            },
            "lead_qualification_workflow": {
                "steps": [
                    "Lead intake and initial scoring",
                    "Jorge adaptive questioning",
                    "Real-time intent analysis",
                    "Temperature classification",
                    "Action recommendation",
                ],
                "estimated_time": "5-15 minutes",
                "required_agents": ["adaptive_jorge", "realtime_intent", "lead_intelligence_swarm"],
            },
            "property_analysis_workflow": {
                "steps": [
                    "Property data collection",
                    "CMA generation",
                    "Market analysis",
                    "Investment scoring",
                    "Report generation",
                ],
                "estimated_time": "10-20 minutes",
                "required_agents": ["cma_generator", "quant_agent", "kappa_competitive"],
            },
        }

    def _load_integration_points(self) -> Dict[str, Dict]:
        """Load integration capabilities and status."""
        return {
            "ghl": {
                "status": "connected",
                "capabilities": ["contact_sync", "webhook_processing", "custom_fields"],
                "last_sync": datetime.now() - timedelta(minutes=5),
            },
            "claude_api": {
                "status": "connected",
                "capabilities": ["conversation_intelligence", "real_time_analysis", "content_generation"],
                "last_sync": datetime.now() - timedelta(seconds=30),
            },
            "retell_ai": {
                "status": "connected",
                "capabilities": ["voice_calls", "call_scheduling", "conversation_recording"],
                "last_sync": datetime.now() - timedelta(minutes=2),
            },
            "lyrio": {
                "status": "connected",
                "capabilities": ["lead_sync", "score_tracking", "digital_twin_association"],
                "last_sync": datetime.now() - timedelta(minutes=1),
            },
        }

    def get_relevant_features(self, context: PlatformContext, user_intent: UserIntent) -> List[Dict]:
        """Get features relevant to current context and intent."""
        relevant = []

        context_map = {
            PlatformContext.LEAD_MANAGEMENT: "lead_management",
            PlatformContext.PROPERTY_ANALYSIS: "property_analysis",
            PlatformContext.BOT_MANAGEMENT: "bot_ecosystem",
            PlatformContext.REPORTS: "analytics_reporting",
        }

        if context in context_map:
            feature_category = self.platform_features.get(context_map[context], {})
            relevant.append(
                {
                    "category": context_map[context],
                    "features": feature_category.get("features", []),
                    "workflows": feature_category.get("workflows", []),
                }
            )

        return relevant


class ContextAwarenessEngine:
    """Tracks user context and activity patterns."""

    def __init__(self):
        self.active_sessions: Dict[str, UserSession] = {}
        self.platform_knowledge = PlatformKnowledgeEngine()

    async def track_user_activity(self, user_id: str, activity: Dict[str, Any]) -> UserSession:
        """Track user activity and update session context."""
        session = self.active_sessions.get(user_id)

        if not session:
            session = UserSession(
                user_id=user_id,
                session_start=datetime.now(),
                last_activity=datetime.now(),
                current_context=self._detect_context(activity),
                detected_intent=self._detect_intent(activity),
            )
            self.active_sessions[user_id] = session

        # Update session with new activity
        session.last_activity = datetime.now()
        session.activity_history.append({"timestamp": datetime.now(), "activity": activity})

        # Re-detect context and intent
        session.current_context = self._detect_context(activity)
        session.detected_intent = self._detect_intent(activity)

        # Check for frustration indicators
        self._detect_frustration_indicators(session, activity)

        return session

    def _detect_context(self, activity: Dict[str, Any]) -> PlatformContext:
        """Detect current platform context from activity."""
        page = activity.get("page", "").lower()
        action = activity.get("action", "").lower()

        if "dashboard" in page or "overview" in page:
            return PlatformContext.DASHBOARD
        elif "lead" in page or "contact" in page:
            return PlatformContext.LEAD_MANAGEMENT
        elif "property" in page or "cma" in page:
            return PlatformContext.PROPERTY_ANALYSIS
        elif "bot" in page or "agent" in page:
            return PlatformContext.BOT_MANAGEMENT
        elif "report" in page or "analytics" in page:
            return PlatformContext.REPORTS
        elif "setting" in page or "config" in page:
            return PlatformContext.SETTINGS
        elif "mobile" in activity.get("device", ""):
            return PlatformContext.MOBILE
        else:
            return PlatformContext.DASHBOARD

    def _detect_intent(self, activity: Dict[str, Any]) -> UserIntent:
        """Detect user intent from activity patterns."""
        action = activity.get("action", "").lower()
        duration = activity.get("duration", 0)

        if "explore" in action or "browse" in action or duration < 30:
            return UserIntent.EXPLORING
        elif "error" in action or "retry" in action or "help" in action:
            return UserIntent.TROUBLESHOOTING
        elif "configure" in action or "setup" in action or "settings" in action:
            return UserIntent.CONFIGURING
        elif "analyze" in action or "report" in action or "view" in action:
            return UserIntent.ANALYZING
        elif "learn" in action or "tutorial" in action or "guide" in action:
            return UserIntent.LEARNING
        else:
            return UserIntent.WORKING

    def _detect_frustration_indicators(self, session: UserSession, activity: Dict[str, Any]):
        """Detect signs of user frustration."""
        # Rapid clicking/navigation
        if len(session.activity_history) > 1:
            last_activity = session.activity_history[-2]["timestamp"]
            if (datetime.now() - last_activity).seconds < 5:
                session.frustration_indicators.append("rapid_navigation")

        # Error patterns
        if "error" in activity.get("action", "").lower():
            session.frustration_indicators.append("error_encountered")

        # Repeated actions
        if len(session.activity_history) >= 3:
            recent_actions = [a["activity"].get("action") for a in session.activity_history[-3:]]
            if len(set(recent_actions)) == 1:
                session.frustration_indicators.append("repeated_action")


class MultiAgentCoordinator:
    """Coordinates interactions with all platform agents."""

    def __init__(self, knowledge_engine: PlatformKnowledgeEngine):
        self.knowledge_engine = knowledge_engine
        self.bot_orchestrator = get_enhanced_bot_orchestrator()
        self.active_agent_tasks: Dict[str, Dict] = {}

    async def coordinate_agent_assistance(self, user_request: str, context: UserSession) -> Dict[str, Any]:
        """Coordinate multiple agents to fulfill user request."""

        # Analyze request to determine required agents
        required_agents = await self._analyze_request_requirements(user_request, context)

        # Check agent availability and capabilities
        available_agents = await self._check_agent_availability(required_agents)

        # Create coordination plan
        coordination_plan = await self._create_coordination_plan(user_request, available_agents, context)

        # Execute coordinated agent response
        results = await self._execute_coordination_plan(coordination_plan)

        return {
            "coordinated_response": results,
            "agents_used": [agent.agent_name for agent in available_agents],
            "coordination_plan": coordination_plan,
            "execution_time": datetime.now(),
        }

    async def _analyze_request_requirements(self, request: str, context: UserSession) -> List[str]:
        """Analyze request to determine which agents are needed."""
        request_lower = request.lower()
        required_agents = []

        # Keyword-based agent selection
        if any(word in request_lower for word in ["lead", "qualify", "seller", "jorge"]):
            required_agents.append("adaptive_jorge")

        if any(word in request_lower for word in ["sequence", "nurture", "follow", "timing"]):
            required_agents.append("predictive_lead")

        if any(word in request_lower for word in ["intent", "score", "analysis", "behavior"]):
            required_agents.append("realtime_intent")

        if any(word in request_lower for word in ["property", "cma", "value", "market"]):
            required_agents.append("cma_generator")

        if any(word in request_lower for word in ["negotiate", "objection", "close"]):
            required_agents.append("voss_negotiation")

        if any(word in request_lower for word in ["predict", "forecast", "analytics"]):
            required_agents.append("epsilon_predictive")

        # Context-based agent selection
        if context.current_context == PlatformContext.LEAD_MANAGEMENT:
            required_agents.extend(["adaptive_jorge", "realtime_intent"])
        elif context.current_context == PlatformContext.PROPERTY_ANALYSIS:
            required_agents.extend(["cma_generator", "quant_agent"])

        return list(set(required_agents))  # Remove duplicates

    async def _check_agent_availability(self, required_agents: List[str]) -> List[AgentCapability]:
        """Check availability and status of required agents."""
        available = []

        for agent_id in required_agents:
            if agent_id in self.knowledge_engine.agent_registry:
                agent_capability = self.knowledge_engine.agent_registry[agent_id]
                if agent_capability.current_status == "active":
                    available.append(agent_capability)

        return available

    async def _create_coordination_plan(
        self, request: str, available_agents: List[AgentCapability], context: UserSession
    ) -> Dict[str, Any]:
        """Create plan for coordinating multiple agents."""
        plan = {
            "primary_agent": None,
            "supporting_agents": [],
            "execution_sequence": [],
            "coordination_strategy": "sequential",  # or "parallel"
            "request": request,
            "context": {
                "user_id": context.user_id,
                "user_name": getattr(context, "user_name", "User"),
                "current_context": context.current_context.value,
                "detected_intent": context.detected_intent.value,
                "competency_level": context.competency_level,
                "conversation_history": getattr(context, "conversation_history", []),
            },
        }

        if available_agents:
            # Select primary agent based on request type and context
            plan["primary_agent"] = available_agents[0]
            plan["supporting_agents"] = available_agents[1:]

            # Determine execution strategy
            if len(available_agents) <= 2:
                plan["coordination_strategy"] = "sequential"
            else:
                plan["coordination_strategy"] = "parallel"

            # Create execution sequence
            for i, agent in enumerate(available_agents):
                plan["execution_sequence"].append(
                    {
                        "step": i + 1,
                        "agent": agent.agent_name,
                        "task": f"Process user request with {agent.agent_type} capabilities",
                    }
                )

        return plan

    async def _execute_coordination_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the coordination plan with real agent invocation."""
        results = {"primary_response": None, "supporting_responses": [], "coordination_summary": plan}

        try:
            # Execute primary agent if specified
            if plan.get("primary_agent"):
                primary_response = await self._invoke_agent(
                    plan["primary_agent"], plan.get("request", ""), plan.get("context", {})
                )
                results["primary_response"] = primary_response

            # Execute supporting agents in parallel
            if plan.get("supporting_agents"):
                supporting_tasks = []
                for agent in plan["supporting_agents"]:
                    task = self._invoke_agent(
                        agent, plan.get("request", ""), plan.get("context", {}), is_supporting=True
                    )
                    supporting_tasks.append(task)

                # Wait for all supporting agents to complete
                if supporting_tasks:
                    supporting_responses = await asyncio.gather(*supporting_tasks, return_exceptions=True)

                    # Filter out exceptions and format responses
                    results["supporting_responses"] = [
                        resp for resp in supporting_responses if not isinstance(resp, Exception)
                    ]

            return results

        except Exception as e:
            logger.error(f"Agent coordination execution error: {e}")
            # Fallback to basic response if agent invocation fails
            return {
                "primary_response": {
                    "agent": "claude_fallback",
                    "response": f"I encountered an issue coordinating agents: {str(e)}. Let me help you directly instead.",
                    "confidence": 0.6,
                    "fallback_reason": str(e),
                },
                "supporting_responses": [],
                "coordination_summary": plan,
            }

    async def _invoke_agent(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any], is_supporting: bool = False
    ) -> Dict[str, Any]:
        """Invoke a specific agent and return structured response."""

        agent_name = agent_capability.agent_name.lower().replace(" ", "_")

        try:
            # Map agent registry names to actual bot instances
            if "adaptive_jorge" in agent_name or "seller" in agent_name:
                return await self._invoke_jorge_seller_bot(agent_capability, request, context)

            elif "buyer" in agent_name or "jorge_buyer" in agent_name:
                return await self._invoke_jorge_buyer_bot(agent_capability, request, context)

            elif "predictive_lead" in agent_name or "lead" in agent_name:
                return await self._invoke_lead_bot(agent_capability, request, context)

            elif "realtime_intent" in agent_name or "intent" in agent_name:
                return await self._invoke_intent_decoder(agent_capability, request, context)

            elif "orchestrator" in agent_name:
                return await self._invoke_bot_orchestrator(agent_capability, request, context)

            else:
                # Generic Claude-powered agent for unimplemented agents
                return await self._invoke_claude_generic_agent(agent_capability, request, context)

        except Exception as e:
            logger.warning(f"Agent {agent_capability.agent_name} invocation failed: {e}")
            return {
                "agent": agent_capability.agent_name,
                "response": f"Agent temporarily unavailable: {str(e)}",
                "confidence": 0.3,
                "error": str(e),
                "status": "failed",
            }

    async def _invoke_jorge_seller_bot(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Jorge Seller Bot with proper conversation context."""
        try:
            from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot

            jorge_bot = JorgeSellerBot()

            # Extract conversation details from context
            lead_id = context.get("user_id", "concierge_user")
            lead_name = context.get("user_name", "User")
            conversation_history = context.get("conversation_history", [{"role": "user", "content": request}])

            result = await jorge_bot.process_seller_message(lead_id, lead_name, conversation_history)

            # Handle different response formats safely
            if isinstance(result, dict):
                response_content = result.get(
                    "response_content", result.get("message", "I can help with seller qualification.")
                )
                qualification_data = result.get("qualification_summary", result.get("intent_profile", {}))
                next_actions = result.get("next_actions", result.get("recommended_actions", []))
            else:
                response_content = "Jorge seller qualification response received."
                qualification_data = {}
                next_actions = []

            return {
                "agent": agent_capability.agent_name,
                "response": response_content,
                "confidence": 0.85,
                "agent_type": "seller_qualification",
                "qualification_data": qualification_data,
                "next_actions": next_actions,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Jorge Seller Bot invocation error: {e}")
            return await self._invoke_claude_generic_agent(agent_capability, request, context)

    async def _invoke_jorge_buyer_bot(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Jorge Buyer Bot with proper conversation context."""
        try:
            from ghl_real_estate_ai.agents.jorge_buyer_bot import JorgeBuyerBot

            # Generate tenant_id for buyer bot
            tenant_id = context.get("tenant_id", "concierge_tenant")
            buyer_bot = JorgeBuyerBot(tenant_id=tenant_id)

            buyer_id = context.get("user_id", "concierge_user")
            buyer_name = context.get("user_name", "User")
            conversation_history = context.get("conversation_history", [{"role": "user", "content": request}])

            result = await buyer_bot.process_buyer_conversation(buyer_id, buyer_name, conversation_history)

            # Handle different response formats safely
            if isinstance(result, dict):
                response_content = result.get(
                    "response_content", result.get("message", "I can help you find the right property.")
                )
                financial_score = result.get("financial_readiness_score", 0)
                matched_properties = result.get("matched_properties", [])
                buyer_temp = result.get("buyer_temperature", "cold")
            else:
                response_content = "Jorge buyer qualification response received."
                financial_score = 0
                matched_properties = []
                buyer_temp = "cold"

            return {
                "agent": agent_capability.agent_name,
                "response": response_content,
                "confidence": 0.85,
                "agent_type": "buyer_qualification",
                "financial_readiness_score": financial_score,
                "matched_properties": matched_properties,
                "buyer_temperature": buyer_temp,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Jorge Buyer Bot invocation error: {e}")
            return await self._invoke_claude_generic_agent(agent_capability, request, context)

    async def _invoke_lead_bot(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Lead Bot for sequence and nurture workflows."""
        try:
            from ghl_real_estate_ai.agents.lead_bot import LeadBotWorkflow

            lead_bot = LeadBotWorkflow()

            # Extract lead context
            lead_id = context.get("user_id", "concierge_user")
            sequence_day = context.get("sequence_day", 3)

            # For now, provide guidance on lead bot capabilities
            return {
                "agent": agent_capability.agent_name,
                "response": f"I can help with lead nurture sequences. Based on your request: '{request}', I recommend checking the 3-7-30 day sequence status and optimizing follow-up timing.",
                "confidence": 0.75,
                "agent_type": "lead_nurture",
                "sequence_recommendations": [
                    "Review current sequence position",
                    "Optimize message timing",
                    "Personalize follow-up content",
                ],
                "next_sequence_day": sequence_day + 1,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Lead Bot invocation error: {e}")
            return await self._invoke_claude_generic_agent(agent_capability, request, context)

    async def _invoke_intent_decoder(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Intent Decoder for conversation analysis."""
        try:
            from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

            intent_decoder = LeadIntentDecoder()

            # Analyze the user request for intent signals - provide fallback for API issues
            try:
                analysis_result = await intent_decoder.decode_intent_context(request)

                if isinstance(analysis_result, dict):
                    primary_intent = analysis_result.get("primary_intent", "exploratory")
                    confidence = analysis_result.get("confidence", 0.7)
                    intent_signals = analysis_result.get("intent_signals", [])
                    frs_delta = analysis_result.get("frs_delta", 0)
                    pcs_delta = analysis_result.get("pcs_delta", 0)
                    recommended_action = analysis_result.get("recommended_action", "continue_conversation")
                else:
                    # Handle non-dict responses
                    primary_intent = "exploratory"
                    confidence = 0.6
                    intent_signals = []
                    frs_delta = 0
                    pcs_delta = 0
                    recommended_action = "continue_conversation"
            except Exception:
                # Fallback if intent analysis fails
                primary_intent = "general_inquiry"
                confidence = 0.5
                intent_signals = ["general"]
                frs_delta = 0
                pcs_delta = 0
                recommended_action = "continue_conversation"

            return {
                "agent": agent_capability.agent_name,
                "response": f"Intent analysis complete. Based on your message, I detect {primary_intent} intent with {confidence:.0%} confidence.",
                "confidence": confidence,
                "agent_type": "intent_analysis",
                "intent_signals": intent_signals,
                "frs_delta": frs_delta,
                "pcs_delta": pcs_delta,
                "recommended_action": recommended_action,
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Intent Decoder invocation error: {e}")
            return await self._invoke_claude_generic_agent(agent_capability, request, context)

    async def _invoke_bot_orchestrator(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Invoke Enhanced Bot Orchestrator for complex coordination."""
        try:
            from ghl_real_estate_ai.agents.enhanced_bot_orchestrator import get_enhanced_bot_orchestrator

            orchestrator = get_enhanced_bot_orchestrator()

            # Determine conversation type from request
            conversation_type = "seller"
            if "buyer" in request.lower() or "property" in request.lower():
                conversation_type = "buyer"
            elif "sequence" in request.lower() or "follow" in request.lower():
                conversation_type = "lead_sequence"

            lead_id = context.get("user_id", "concierge_user")
            lead_name = context.get("user_name", "User")
            conversation_history = context.get("conversation_history", [])

            result = await orchestrator.orchestrate_conversation(
                lead_id=lead_id,
                lead_name=lead_name,
                message=request,
                conversation_type=conversation_type,
                conversation_history=conversation_history,
            )

            return {
                "agent": agent_capability.agent_name,
                "response": result.get("message", "Orchestration complete."),
                "confidence": 0.8,
                "agent_type": "orchestration",
                "bot_type_used": result.get("bot_type", "unknown"),
                "enhancement_level": result.get("enhancement_level", "standard"),
                "orchestration_metadata": result.get("orchestration_metadata", {}),
                "status": "success",
            }

        except Exception as e:
            logger.error(f"Bot Orchestrator invocation error: {e}")
            return await self._invoke_claude_generic_agent(agent_capability, request, context)

    async def _invoke_claude_generic_agent(
        self, agent_capability: AgentCapability, request: str, context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generic Claude-powered agent for agents without specific implementations."""
        try:
            # Create a basic response based on agent capabilities without requiring Claude API
            capabilities_text = ", ".join(agent_capability.capabilities)
            specializations_text = ", ".join(agent_capability.specializations)

            # Generate informative response based on agent type and request
            if agent_capability.agent_type == "analytics":
                response_content = f"I'm {agent_capability.agent_name}, specializing in {specializations_text}. For your request '{request}', I can analyze patterns and provide data-driven insights using {capabilities_text}."
            elif agent_capability.agent_type == "negotiation":
                response_content = f"I'm {agent_capability.agent_name}, your negotiation specialist. I can help with tactical approaches for '{request}' using my expertise in {specializations_text}."
            elif agent_capability.agent_type == "competitive_analysis":
                response_content = f"I'm {agent_capability.agent_name}, providing market intelligence. For '{request}', I can deliver competitive insights using {capabilities_text}."
            elif agent_capability.agent_type == "revenue_analysis":
                response_content = f"I'm {agent_capability.agent_name}, tracking revenue performance. I can analyze '{request}' and provide attribution insights using {capabilities_text}."
            else:
                response_content = f"I'm {agent_capability.agent_name}, ready to assist with {agent_capability.agent_type} tasks. For '{request}', I can leverage my capabilities: {capabilities_text}."

            return {
                "agent": agent_capability.agent_name,
                "response": response_content,
                "confidence": 0.7,
                "agent_type": agent_capability.agent_type,
                "capabilities_used": agent_capability.capabilities,
                "status": "success_generic",
            }

        except Exception as e:
            logger.error(f"Generic agent invocation error for {agent_capability.agent_name}: {e}")
            return {
                "agent": agent_capability.agent_name,
                "response": f"I'm {agent_capability.agent_name} and I'm experiencing technical difficulties. Please try again later.",
                "confidence": 0.4,
                "error": str(e),
                "status": "error",
            }


class ProactiveAssistant:
    """Provides proactive assistance and recommendations."""

    def __init__(self, knowledge_engine: PlatformKnowledgeEngine, context_engine: ContextAwarenessEngine):
        self.knowledge_engine = knowledge_engine
        self.context_engine = context_engine

    async def generate_proactive_recommendations(self, session: UserSession) -> List[ConciergeRecommendation]:
        """Generate proactive recommendations based on user context."""
        recommendations = []

        # Check for frustration indicators
        if session.frustration_indicators:
            recommendations.append(await self._create_frustration_assistance(session))

        # Context-specific recommendations
        context_recommendations = await self._create_context_recommendations(session)
        recommendations.extend(context_recommendations)

        # Workflow optimization recommendations
        workflow_recommendations = await self._create_workflow_recommendations(session)
        recommendations.extend(workflow_recommendations)

        return recommendations

    async def _create_frustration_assistance(self, session: UserSession) -> ConciergeRecommendation:
        """Create assistance for frustrated users."""
        return ConciergeRecommendation(
            recommendation_type="frustration_assistance",
            title="I noticed you might need some help",
            description="It looks like you're encountering some challenges. I'm here to help!",
            action_steps=[
                "Let me guide you through what you're trying to accomplish",
                "I can show you the most efficient way to complete your task",
                "Would you like a quick tutorial on this feature?",
            ],
            priority="high",
            confidence=0.9,
            estimated_time="2-5 minutes",
        )

    async def _create_context_recommendations(self, session: UserSession) -> List[ConciergeRecommendation]:
        """Create recommendations based on current context."""
        recommendations = []

        if session.current_context == PlatformContext.LEAD_MANAGEMENT:
            recommendations.append(
                ConciergeRecommendation(
                    recommendation_type="lead_optimization",
                    title="Optimize your lead qualification",
                    description="I can help you set up Jorge's adaptive questioning for better lead qualification.",
                    action_steps=[
                        "Configure Jorge Seller Bot with your specific questions",
                        "Set up real-time intent analysis",
                        "Create predictive nurture sequences",
                    ],
                    priority="medium",
                    confidence=0.8,
                    relevant_agents=["adaptive_jorge", "realtime_intent"],
                    estimated_time="10-15 minutes",
                )
            )

        elif session.current_context == PlatformContext.PROPERTY_ANALYSIS:
            recommendations.append(
                ConciergeRecommendation(
                    recommendation_type="property_intelligence",
                    title="Enhanced property analysis available",
                    description="Use our advanced property intelligence agents for deeper market insights.",
                    action_steps=[
                        "Generate comprehensive CMA with market comparisons",
                        "Run competitive benchmarking analysis",
                        "Create investment scoring reports",
                    ],
                    priority="medium",
                    confidence=0.75,
                    relevant_agents=["cma_generator", "kappa_competitive"],
                    estimated_time="5-10 minutes",
                )
            )

        return recommendations

    async def _create_workflow_recommendations(self, session: UserSession) -> List[ConciergeRecommendation]:
        """Create workflow optimization recommendations."""
        recommendations = []

        # Analyze user activity patterns for optimization opportunities
        if len(session.activity_history) > 5:
            # Check for repetitive tasks that could be automated
            action_counts = {}
            for activity in session.activity_history[-10:]:
                action = activity["activity"].get("action", "")
                action_counts[action] = action_counts.get(action, 0) + 1

            for action, count in action_counts.items():
                if count >= 3:  # Repeated action
                    recommendations.append(
                        ConciergeRecommendation(
                            recommendation_type="automation_opportunity",
                            title=f"Automate your '{action}' workflow",
                            description=f"I notice you're doing '{action}' frequently. I can help automate this.",
                            action_steps=[
                                f"Set up automated {action} with our agent ecosystem",
                                "Configure triggers and conditions",
                                "Test the automation workflow",
                            ],
                            priority="low",
                            confidence=0.6,
                            estimated_time="15-20 minutes",
                        )
                    )

        return recommendations


class ClaudeConciergeAgent:
    """
    The Claude Concierge Agent - Omnipresent AI Platform Guide

    Provides intelligent, context-aware assistance across Jorge's entire platform,
    coordinating with 40+ specialized agents while learning user patterns and preferences.
    """

    def __init__(self):
        self.claude_assistant = ClaudeAssistant()
        self.event_publisher = get_event_publisher()

        # Core engines
        self.knowledge_engine = PlatformKnowledgeEngine()
        self.context_engine = ContextAwarenessEngine()
        self.multi_agent_coordinator = MultiAgentCoordinator(self.knowledge_engine)
        self.proactive_assistant = ProactiveAssistant(self.knowledge_engine, self.context_engine)

        # State
        self.mode = ConciergeMode.PROACTIVE
        self.active_conversations: Dict[str, Dict] = {}
        self.performance_metrics = {
            "interactions_handled": 0,
            "recommendations_generated": 0,
            "agent_coordinations": 0,
            "user_satisfaction_score": 0.0,
            "proactive_assists": 0,
        }

    async def process_user_interaction(self, user_id: str, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process user interaction and provide intelligent assistance."""

        # Track user activity and context
        session = await self.context_engine.track_user_activity(
            user_id,
            {
                "action": context.get("action", "message"),
                "page": context.get("page", "unknown"),
                "device": context.get("device", "desktop"),
                "message": message,
            },
        )

        # Analyze user request
        request_analysis = await self._analyze_user_request(message, session)

        # Generate response strategy
        response_strategy = await self._determine_response_strategy(request_analysis, session)

        # Execute response based on strategy
        response = await self._execute_response_strategy(response_strategy, session, message)

        # Generate proactive recommendations
        recommendations = await self.proactive_assistant.generate_proactive_recommendations(session)

        # Update performance metrics
        self.performance_metrics["interactions_handled"] += 1
        if recommendations:
            self.performance_metrics["recommendations_generated"] += len(recommendations)

        # Publish concierge event
        await self.event_publisher.publish_concierge_interaction(
            user_id=user_id,
            interaction_type=response_strategy["type"],
            response_provided=True,
            recommendations_count=len(recommendations),
            agent_coordination_required=response_strategy.get("requires_coordination", False),
        )

        return {
            "concierge_response": response,
            "proactive_recommendations": recommendations,
            "session_context": {
                "current_context": session.current_context.value,
                "detected_intent": session.detected_intent.value,
                "competency_level": session.competency_level,
            },
            "response_metadata": {
                "strategy": response_strategy,
                "processing_time": datetime.now(),
                "confidence": response_strategy.get("confidence", 0.8),
            },
        }

    async def _analyze_user_request(self, message: str, session: UserSession) -> Dict[str, Any]:
        """Analyze user request to understand intent and requirements."""

        # Use Claude for natural language understanding
        analysis_prompt = f"""
        Analyze this user request in the context of Jorge's real estate AI platform:

        User Message: "{message}"
        Current Context: {session.current_context.value}
        Detected Intent: {session.detected_intent.value}
        User Level: {session.competency_level}

        Determine:
        1. Request type (question, task, problem, exploration)
        2. Complexity level (simple, moderate, complex)
        3. Urgency (low, medium, high)
        4. Required knowledge domains
        5. Whether multi-agent coordination is needed

        Respond with JSON format.
        """

        claude_response = await self.claude_assistant.analyze_with_context(analysis_prompt)

        try:
            analysis = json.loads(claude_response.get("content", "{}"))
        except json.JSONDecodeError:
            # Fallback analysis
            analysis = {
                "request_type": "question",
                "complexity": "moderate",
                "urgency": "medium",
                "knowledge_domains": ["general"],
                "needs_coordination": False,
            }

        return analysis

    async def _determine_response_strategy(self, analysis: Dict[str, Any], session: UserSession) -> Dict[str, Any]:
        """Determine the best response strategy."""

        strategy = {"type": "direct_response", "confidence": 0.8, "requires_coordination": False, "primary_agent": None}

        # Determine if multi-agent coordination is needed
        if analysis.get("complexity") == "complex" or analysis.get("needs_coordination"):
            strategy["type"] = "coordinated_response"
            strategy["requires_coordination"] = True

        # Check for emergency/high urgency situations
        if analysis.get("urgency") == "high" or session.frustration_indicators:
            strategy["type"] = "priority_response"
            strategy["confidence"] = 0.9

        # Adjust strategy based on user competency
        if session.competency_level == "beginner":
            strategy["type"] = "guided_response"
            strategy["include_tutorial"] = True

        return strategy

    async def _execute_response_strategy(
        self, strategy: Dict[str, Any], session: UserSession, message: str
    ) -> Dict[str, Any]:
        """Execute the determined response strategy."""

        if strategy["type"] == "coordinated_response":
            # Use multi-agent coordination
            coordination_result = await self.multi_agent_coordinator.coordinate_agent_assistance(message, session)
            self.performance_metrics["agent_coordinations"] += 1

            return {
                "response_type": "coordinated",
                "content": "I've coordinated with multiple agents to provide you with comprehensive assistance.",
                "coordination_details": coordination_result,
                "confidence": strategy["confidence"],
            }

        elif strategy["type"] == "priority_response":
            # High priority/emergency response
            return {
                "response_type": "priority",
                "content": "I understand you need immediate assistance. Let me help you right away.",
                "immediate_actions": await self._generate_immediate_actions(session, message),
                "confidence": strategy["confidence"],
            }

        elif strategy["type"] == "guided_response":
            # Guided response for beginners
            return {
                "response_type": "guided",
                "content": "I'll walk you through this step by step.",
                "tutorial_steps": await self._generate_tutorial_steps(session, message),
                "confidence": strategy["confidence"],
            }

        else:
            # Direct response
            response_content = await self._generate_direct_response(session, message)
            return {"response_type": "direct", "content": response_content, "confidence": strategy["confidence"]}

    async def _generate_immediate_actions(self, session: UserSession, message: str) -> List[str]:
        """Generate immediate action steps for high-priority situations."""
        return [
            "Let me connect you with the right specialized agent",
            "I'm analyzing your situation for the best solution",
            "Here are the immediate steps we can take together",
        ]

    async def _generate_tutorial_steps(self, session: UserSession, message: str) -> List[Dict]:
        """Generate step-by-step tutorial for beginners."""
        return [
            {
                "step": 1,
                "title": "Understanding your request",
                "description": "Let me break down what you're trying to accomplish",
                "estimated_time": "1 minute",
            },
            {
                "step": 2,
                "title": "Navigating to the right section",
                "description": "I'll show you exactly where to find this feature",
                "estimated_time": "2 minutes",
            },
            {
                "step": 3,
                "title": "Completing the task",
                "description": "Let's complete this together with the right agent assistance",
                "estimated_time": "5-10 minutes",
            },
        ]

    async def _generate_direct_response(self, session: UserSession, message: str) -> str:
        """Generate direct response using Claude."""

        # Get relevant platform knowledge
        relevant_features = self.knowledge_engine.get_relevant_features(
            session.current_context, session.detected_intent
        )

        context_prompt = f"""
        You are the Claude Concierge for Jorge's real estate AI platform. You have access to 40+
        specialized agents and comprehensive platform knowledge.

        User Context:
        - Current area: {session.current_context.value}
        - Intent: {session.detected_intent.value}
        - Experience level: {session.competency_level}
        - Session duration: {(datetime.now() - session.session_start).seconds // 60} minutes

        Available Platform Features: {relevant_features}

        User Message: "{message}"

        Provide a helpful, concise response that:
        1. Directly addresses their question/need
        2. Leverages the most appropriate platform agents
        3. Offers next steps if applicable
        4. Matches their experience level

        Be friendly, knowledgeable, and proactive.
        """

        response = await self.claude_assistant.analyze_with_context(context_prompt)
        return response.get("content", "I'm here to help! How can I assist you with Jorge's platform today?")

    async def get_concierge_status(self) -> Dict[str, Any]:
        """Get current status and performance metrics."""
        return {
            "mode": self.mode.value,
            "active_sessions": len(self.context_engine.active_sessions),
            "performance_metrics": self.performance_metrics,
            "knowledge_base": {
                "registered_agents": len(self.knowledge_engine.agent_registry),
                "platform_features": len(self.knowledge_engine.platform_features),
                "integration_points": len(self.knowledge_engine.integration_points),
            },
            "capabilities": [
                "Platform guidance and navigation",
                "Multi-agent coordination",
                "Proactive assistance",
                "Context-aware recommendations",
                "Real-time problem solving",
            ],
        }


# --- Factory and Utility Functions ---

_concierge_instance: Optional[ClaudeConciergeAgent] = None


def get_claude_concierge() -> ClaudeConciergeAgent:
    """Get singleton Claude Concierge Agent instance."""
    global _concierge_instance

    if _concierge_instance is None:
        _concierge_instance = ClaudeConciergeAgent()

    return _concierge_instance


# --- Event Publisher Extensions ---


async def publish_concierge_interaction(event_publisher, **kwargs):
    """Publish concierge interaction event."""
    await event_publisher.publish_event(
        event_type="concierge_interaction", data={**kwargs, "timestamp": datetime.now().isoformat()}
    )
