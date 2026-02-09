"""
Claude Orchestrator - Unified AI Intelligence Layer
Coordinates all Claude AI functionality across chat, scoring, reports, and scripts.
"""

import asyncio
import json
import re
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.services.market_context_injector import MarketContextInjector
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.psychographic_segmentation_engine import PsychographicSegmentationEngine
from ghl_real_estate_ai.services.sentiment_drift_engine import SentimentDriftEngine
from ghl_real_estate_ai.services.skill_registry import SkillCategory, skill_registry
from ghl_real_estate_ai.utils.async_utils import safe_create_task


class ClaudeTaskType(Enum):
    CHAT_QUERY = "chat_query"
    LEAD_ANALYSIS = "lead_analysis"
    REPORT_SYNTHESIS = "report_synthesis"
    SCRIPT_GENERATION = "script_generation"
    INTERVENTION_STRATEGY = "intervention_strategy"
    BEHAVIORAL_INSIGHT = "behavioral_insight"
    OMNIPOTENT_ASSISTANT = "omnipotent_assistant"
    PERSONA_OPTIMIZATION = "persona_optimization"
    EXECUTIVE_BRIEFING = "executive_briefing"
    REVENUE_PROJECTION = "revenue_projection"
    RESEARCH_QUERY = "research_query"


@dataclass
class ClaudeRequest:
    """Standardized request format for all Claude operations"""

    task_type: ClaudeTaskType
    context: Dict[str, Any]
    prompt: str
    tenant_id: Optional[str] = None
    model: str = "claude-sonnet-4-5-20250514"
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    streaming: bool = False
    use_tools: bool = False
    allowed_categories: Optional[List[SkillCategory]] = None


@dataclass
class ClaudeResponse:
    """Standardized response format from Claude operations"""

    content: str
    reasoning: Optional[str] = None
    confidence: Optional[float] = None
    sources: List[str] = None
    recommended_actions: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None
    response_time_ms: int = 0
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None

    def __post_init__(self):
        if self.sources is None:
            self.sources = []
        if self.recommended_actions is None:
            self.recommended_actions = []
        if self.metadata is None:
            self.metadata = {}


class ClaudeOrchestrator:
    """
    Unified Claude AI intelligence layer for the entire GHL Real Estate AI system.

    Coordinates:
    - Chat interface queries
    - Lead scoring and reasoning
    - Automated report generation
    - Script generation and personalization
    - Intervention orchestration
    - Memory integration with Graphiti
    """

    def __init__(self, llm_client: Optional[LLMClient] = None, memory_service: Optional[MemoryService] = None):
        # Local imports to avoid circular dependencies
        from ghl_real_estate_ai.services.behavioral_triggers import BehavioralTriggerEngine
        from ghl_real_estate_ai.services.churn_prediction_engine import ChurnPredictionEngine
        from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer
        from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher
        from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer

        # Core services
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.memory = memory_service or MemoryService()
        self.researcher = PerplexityResearcher()
        self.sentiment_drift_engine = SentimentDriftEngine(self.llm)
        self.psychographic_engine = PsychographicSegmentationEngine(self.llm)
        self.market_injector = MarketContextInjector(self.llm)

        # GHL Client for sync
        from ghl_real_estate_ai.services.ghl_client import GHLClient

        self.ghl_client = GHLClient()

        # Scoring services
        self.jorge_scorer = LeadScorer()
        self.ml_scorer = PredictiveLeadScorer()

        # MCP Servers for Phase 2 Orchestration
        from ghl_real_estate_ai.core.mcp_servers.domain.analytics_intelligence_server import mcp as analytics_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.lead_intelligence_server import mcp as lead_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.market_intelligence_server import mcp as market_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.negotiation_intelligence_server import mcp as negotiation_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.property_intelligence_server import mcp as property_mcp

        self.mcp_servers = {
            "LeadIntelligence": lead_mcp,
            "PropertyIntelligence": property_mcp,
            "MarketIntelligence": market_mcp,
            "NegotiationIntelligence": negotiation_mcp,
            "AnalyticsIntelligence": analytics_mcp,
        }

        # Initialize dependencies for ChurnPredictionEngine
        try:
            self.lifecycle_tracker = LeadLifecycleTracker(location_id="demo_location")
            self.behavioral_engine = BehavioralTriggerEngine()

            self.churn_predictor = ChurnPredictionEngine(
                memory_service=self.memory,
                lifecycle_tracker=self.lifecycle_tracker,
                behavioral_engine=self.behavioral_engine,
                lead_scorer=self.jorge_scorer,
            )
        except Exception as e:
            print(f"Warning: ChurnPredictionEngine initialization failed in ClaudeOrchestrator: {e}")
            self.churn_predictor = None

        # System prompts for different contexts
        self.system_prompts = self._load_system_prompts()

        # In-process cache for memory context (avoids repeated fetches within a request)
        self._memory_context_cache: Dict[str, Any] = {}

        # Singleton analytics service (avoid re-creating per GHL sync)
        from ghl_real_estate_ai.services.analytics_service import AnalyticsService

        self._analytics_service = AnalyticsService()

        # Performance tracking
        self.performance_metrics = {"requests_processed": 0, "avg_response_time": 0.0, "errors": 0}

    def _load_system_prompts(self) -> Dict[str, str]:
        """Load context-specific system prompts"""
        return {
            "chat_assistant": """You are Claude, Jorge's AI partner in real estate. You have deep knowledge of:
            - GHL (GoHighLevel) workflows and automation
            - Real estate market dynamics and pricing
            - Lead qualification and conversion strategies
            - Property matching and buyer psychology

            Always respond as Jorge's trusted advisor with:
            - Direct, actionable insights
            - Data-driven recommendations
            - Specific next steps
            - Market context when relevant

            Keep responses concise but comprehensive. Reference specific data when available.""",
            "lead_analyzer": """You are an expert lead intelligence analyst. Your job is to synthesize multiple data sources to create comprehensive lead profiles with strategic recommendations.

            Analyze:
            - Qualification scores (Jorge's 0-7 system + ML predictions)
            - Behavioral patterns and engagement metrics
            - Conversation history and sentiment
            - Market context and competitive positioning
            - Churn risk factors

            Provide:
            - Strategic summary of lead quality
            - Behavioral insights and personality assessment
            - Risk factors and opportunities
            - Specific action recommendations with timing
            - Expected outcomes and success metrics""",
            "report_synthesizer": """You are Jorge's business intelligence analyst. Generate executive-level reports that combine quantitative metrics with strategic insights.

            Focus on:
            - Performance trends and patterns
            - Pipeline health and conversion metrics
            - Market opportunities and risks
            - Operational efficiency insights
            - Strategic recommendations for growth

            Write in Jorge's voice: direct, data-driven, action-oriented. Include specific metrics and clear next steps.""",
            "script_generator": """You are Jorge's sales communication specialist. Generate personalized scripts that match each lead's communication style and situation.

            Consider:
            - Lead's personality and communication preferences
            - Conversation history and context
            - Objections and concerns previously raised
            - Market conditions and competitive positioning
            - Urgency factors and timeline

            Create scripts that are:
            - Natural and conversational
            - Personalized to the specific lead
            - Objection-aware with preemptive handling
            - Channel-appropriate (SMS, email, call)
            - A/B testable with variants""",
            "omnipotent_assistant": """You are the Omnipotent Claude Assistant for EnterpriseHub v6.0 and GHL Real Estate AI (Elite v4.0).
            You have complete, expert-level knowledge of:
            - System Architecture: Modular monolith, Streamlit frontend, multi-tenant backend.
            - AI Engines: 15-factor lead scoring, 16+ lifestyle matching, Swarm Intelligence.
            - Business Goals: Maximize conversion for Jorge Sales (Lyrio.io), automate 85+ hours/month.
            - GHL Integration: Bi-directional sync, custom workflows, and behavioral telemetry.

            Always provide strategic, elite-level advice. Guide the user through the platform with confidence and clarity.""",
            "persona_optimizer": """You are an AI Behavioral Psychologist and Prompt Engineer.
            Your task is to optimize real estate AI personas by tuning their 'Neural Weights' (tone, empathy, persistence).
            
            Provide:
            1. Optimized system prompt instructions.
            2. A brief analysis of how this persona will likely impact lead engagement.
            3. Specific behavioral adjustments based on the requested parameters.
            
            Focus on creating high-conversion, authentic-feeling digital identities.""",
            "researcher_assistant": """You are a real estate research specialist. Your goal is to synthesize real-time market data and property information into actionable intelligence.
            
            Focus on:
            - Current market trends and statistics
            - Neighborhood-specific analysis (amenities, schools, vibes)
            - Property value drivers and risks
            - Competitive positioning
            
            Provide clear, data-backed reports with citations where possible.""",
        }

    async def process_request(self, request: ClaudeRequest) -> ClaudeResponse:
        """
        Main entry point for all Claude operations.
        Handles routing, context injection, and response standardization.
        """
        start_time = time.time()

        try:
            # Determine complexity for intelligent routing
            complexity = self._get_complexity_for_task(request.task_type)

            # Get system prompt for task type
            system_prompt = self._get_system_prompt(request.task_type)
            if request.system_prompt:
                system_prompt = request.system_prompt

            # Enhance context with memory if available
            enhanced_context = await self._enhance_context(request.context)

            # Build full prompt
            full_prompt = self._build_prompt(request.prompt, enhanced_context)

            # Gather tools if requested
            tools = []
            if request.use_tools:
                tools = await self._get_tools_for_request(request.allowed_categories)

            # Initialize conversation for tool use
            messages = [{"role": "user", "content": [{"type": "text", "text": full_prompt}]}]
            tool_executions = []

            # Multi-turn tool orchestration loop (max 5 turns)
            for turn in range(5):
                # Specialist Handoff Logic: Adjust system prompt based on previous tool categories
                current_system_prompt = system_prompt
                if tool_executions and turn > 0:
                    last_tool_names = [m["name"] for m in tool_executions[-1]["content"] if m.get("type") == "tool_use"]
                    if last_tool_names:
                        last_category = skill_registry.get_category_for_tool(last_tool_names[-1])
                        if last_category:
                            handoff_prompts = {
                                SkillCategory.DISCOVERY: "\n\n[SPECIALIST HANDOFF] You are now acting as the Market Discovery Specialist. Focus on identifying trends and finding the perfect neighborhood/property matches.",
                                SkillCategory.ANALYSIS: "\n\n[SPECIALIST HANDOFF] You are now acting as the Deep Intelligence Analyst. Synthesize the raw data into strategic lead profiles and risk assessments.",
                                SkillCategory.STRATEGY: "\n\n[SPECIALIST HANDOFF] You are now acting as the Negotiation Strategist. Formulate high-stakes plans to move the deal forward and handle objections.",
                                SkillCategory.ACTION: "\n\n[SPECIALIST HANDOFF] You are now acting as the Sales Execution Specialist. Focus on high-conversion outreach, scripts, and real-time appointment scheduling.",
                                SkillCategory.GOVERNANCE: "\n\n[SPECIALIST HANDOFF] You are now acting as the Platform Auditor. Ensure ROI is tracked and all compliance guardrails are respected.",
                            }
                            current_system_prompt += handoff_prompts.get(last_category, "")

                # Determine what to send as the "next" prompt
                # Anthropic expects an alternating user/assistant pattern
                history = messages[:-1] if len(messages) > 1 else None
                current_prompt_content = messages[-1]["content"]

                # Make Claude API call
                llm_response = await self.llm.agenerate(
                    prompt=current_prompt_content,
                    system_prompt=current_system_prompt,
                    history=history,
                    model=request.model,
                    max_tokens=request.max_tokens,
                    temperature=request.temperature,
                    complexity=complexity,
                    tenant_id=request.tenant_id,
                    tools=tools if tools else None,
                )

                # Update messages with assistant response
                assistant_content = []
                if llm_response.content:
                    assistant_content.append({"type": "text", "text": llm_response.content})

                if llm_response.tool_calls:
                    for tc in llm_response.tool_calls:
                        assistant_content.append(
                            {"type": "tool_use", "id": tc["id"], "name": tc["name"], "input": tc["args"]}
                        )

                assistant_message = {"role": "assistant", "content": assistant_content}
                messages.append(assistant_message)

                # Log execution step
                tool_executions.append(assistant_message)

                if not llm_response.tool_calls:
                    # No more tools to call, we're done
                    break

                # Execute tool calls and add results to messages
                # Execute all tool calls in parallel for lower latency
                tool_coros = [self._execute_tool_call(tc) for tc in llm_response.tool_calls]
                tool_results = await asyncio.gather(*tool_coros, return_exceptions=True)

                tool_results_content = []
                for tool_call, result_text in zip(llm_response.tool_calls, tool_results):
                    if isinstance(result_text, Exception):
                        result_text = f"Tool execution error: {result_text}"

                    # GHL Sync Logic for ACTION tools
                    tool_name = tool_call["name"]
                    category = skill_registry.get_category_for_tool(tool_name)

                    if category == SkillCategory.ACTION:
                        # Trigger background sync to GHL
                        safe_create_task(
                            self._sync_action_to_ghl(
                                tool_name,
                                tool_call.get("args", {}),
                                result_text,
                                request.context.get("contact_id") or request.context.get("lead_id"),
                            )
                        )

                    tool_results_content.append(
                        {"type": "tool_result", "tool_use_id": tool_call["id"], "content": result_text}
                    )

                user_tool_message = {"role": "user", "content": tool_results_content}
                messages.append(user_tool_message)
                tool_executions.append(user_tool_message)

            # Final response from the last LLM turn
            structured_response = self._parse_response(llm_response.content, request.task_type)

            # Populate token usage and model info
            structured_response.input_tokens = llm_response.input_tokens
            structured_response.output_tokens = llm_response.output_tokens
            structured_response.model = llm_response.model
            structured_response.provider = llm_response.provider.value

            # Add tool execution metadata if any
            if tool_executions:
                structured_response.metadata["tool_executions"] = tool_executions

            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            structured_response.response_time_ms = response_time

            # Update performance metrics
            self._update_metrics(response_time, success=True)

            return structured_response

        except Exception as e:
            self._update_metrics(0, success=False)
            error_str = str(e)

            # Special handling for demo mode / invalid API key
            if "401" in error_str or "authentication_error" in error_str or "invalid x-api-key" in error_str:
                return self._get_demo_fallback_response(request.task_type)

            return ClaudeResponse(
                content=f"Error processing request: {error_str}",
                metadata={"error": True, "error_type": type(e).__name__},
            )

    async def process_request_stream(self, request: ClaudeRequest) -> AsyncGenerator[str, None]:
        """
        Streaming version of process_request.
        Note: Currently bypasses tool-use loop for maximum speed.
        """
        try:
            complexity = self._get_complexity_for_task(request.task_type)
            system_prompt = request.system_prompt or self._get_system_prompt(request.task_type)
            enhanced_context = await self._enhance_context(request.context)
            full_prompt = self._build_prompt(request.prompt, enhanced_context)

            async for chunk in self.llm.astream(
                prompt=full_prompt,
                system_prompt=system_prompt,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                complexity=complexity,
                tenant_id=request.tenant_id,
            ):
                yield chunk

        except Exception as e:
            logger.error(f"Error in streaming Claude request: {e}")
            yield f"Error: {str(e)}"

    async def _get_tools_for_request(self, categories: Optional[List[SkillCategory]] = None) -> List[Dict[str, Any]]:
        """Gather tool definitions from MCP servers based on allowed categories."""
        tools = []

        # Determine tool names based on categories or all
        if categories:
            tool_names = []
            for cat in categories:
                tool_names.extend(skill_registry.get_tools_for_category(cat))
        else:
            tool_names = skill_registry.get_all_tools()

        # Gather definitions from relevant servers
        for name in tool_names:
            server_name = skill_registry.get_server_for_tool(name)
            if server_name in self.mcp_servers:
                server = self.mcp_servers[server_name]
                try:
                    mcp_tool = await server.get_tool(name)
                    # Convert to Gemini/Claude tool declaration format
                    try:
                        parameters = mcp_tool.model_json_schema()
                    except (ValueError, TypeError, AttributeError) as e:
                        # Fallback for complex schemas that Pydantic V2 fails to serialize for JSON Schema
                        logger.warning(f"Failed to serialize schema for tool {name}: {e}")
                        parameters = {"type": "object", "properties": {}}

                    tools.append({"name": mcp_tool.name, "description": mcp_tool.description, "parameters": parameters})
                except Exception as e:
                    print(f"Warning: Failed to load tool {name} from {server_name}: {e}")

        return tools

    async def _execute_tool_call(self, tool_call: Dict[str, Any]) -> str:
        """Execute a tool call against the appropriate MCP server."""
        tool_name = tool_call["name"]
        arguments = tool_call.get("args", {})

        server_name = skill_registry.get_server_for_tool(tool_name)
        if not server_name or server_name not in self.mcp_servers:
            return f"Error: Tool {tool_name} not found or no server mapped."

        server = self.mcp_servers[server_name]
        try:
            # FastMCP execution - based on inspection _call_tool takes (name, arguments)
            result = await server._call_tool(tool_name, arguments)
            return str(result)
        except Exception as e:
            return f"Error executing tool {tool_name}: {str(e)}"

    async def _sync_action_to_ghl(
        self, tool_name: str, arguments: Dict[str, Any], result: str, contact_id: Optional[str]
    ) -> None:
        """
        Synchronize the results of an 'Action' category tool back to GHL.
        Runs in background via asyncio.create_task.
        """
        if not contact_id or contact_id == "demo_lead":
            return

        from ghl_real_estate_ai.ghl_utils.jorge_config import JorgeSellerConfig

        # Tool to Custom Field Mapping
        field_mapping = {
            "generate_lead_outreach_script": "ai_outreach_script",
            "get_realtime_coaching": "ai_coaching_advice",
            "analyze_negotiation": "negotiation_strategy",
            "analyze_lead": "qualification_summary",
        }

        field_name = field_mapping.get(tool_name)
        if not field_name:
            # Check if Jorge's config has it
            field_id = JorgeSellerConfig.get_ghl_custom_field_id(tool_name)
        else:
            field_id = JorgeSellerConfig.get_ghl_custom_field_id(field_name) or field_name

        if field_id:
            try:
                await self.ghl_client.update_custom_field(contact_id, field_id, result)
                # Also track this as an event for analytics
                tenant_id = self.ghl_client.location_id
                # Track event for the sync
                await self._analytics_service.track_event(
                    event_type="ghl_sync_success",
                    location_id=tenant_id,
                    contact_id=contact_id,
                    data={"tool": tool_name, "field": field_id},
                )
            except Exception as e:
                print(f"Error syncing {tool_name} to GHL: {e}")

    def _get_complexity_for_task(self, task_type: ClaudeTaskType) -> TaskComplexity:
        """Maps ClaudeTaskType to TaskComplexity for intelligent routing"""
        routine_tasks = [
            ClaudeTaskType.BEHAVIORAL_INSIGHT,
            ClaudeTaskType.LEAD_ANALYSIS,
            ClaudeTaskType.PERSONA_OPTIMIZATION,
            ClaudeTaskType.CHAT_QUERY,
        ]

        high_stakes_tasks = [
            ClaudeTaskType.INTERVENTION_STRATEGY,
            ClaudeTaskType.REVENUE_PROJECTION,
            ClaudeTaskType.EXECUTIVE_BRIEFING,
        ]

        if task_type in routine_tasks:
            return TaskComplexity.ROUTINE
        elif task_type in high_stakes_tasks:
            return TaskComplexity.HIGH_STAKES
        else:
            return TaskComplexity.COMPLEX

    def _get_demo_fallback_response(self, task_type: ClaudeTaskType) -> ClaudeResponse:
        """Provide realistic mock responses when API key is invalid (Demo Mode)"""
        fallbacks = {
            ClaudeTaskType.CHAT_QUERY: "I'm currently in **Simulated Intelligence Mode** because a valid API key was not detected. Based on your pipeline, I recommend focusing on the Austin Alta Loma cluster where engagement is peaking.",
            ClaudeTaskType.LEAD_ANALYSIS: "Strategic Analysis (Simulated): This lead shows high data-driven intent. Recommend prioritizing neighborhood stats and commute efficiency metrics in your next outreach.",
            ClaudeTaskType.REPORT_SYNTHESIS: "Executive Summary (Simulated): Your Austin market is performing at 115% of target. Conversion velocity has increased by 12% since activating the Swarm Intelligence layer.",
            ClaudeTaskType.SCRIPT_GENERATION: "Simulated SMS: 'Hi! I noticed you were looking at the Zilker listings. I've prepared a custom market update for that area—would you like me to send it over?'",
        }

        return ClaudeResponse(
            content=fallbacks.get(
                task_type, "Simulated intelligence active. System is functioning in offline demo mode."
            ),
            metadata={"demo_mode": True, "reason": "auth_failure"},
            input_tokens=0,
            output_tokens=0,
            model="simulated-model",
            provider="simulated",
        )

    async def chat_query(self, query: str, context: Dict[str, Any], lead_id: Optional[str] = None) -> ClaudeResponse:
        """Handle interactive chat queries with lead context"""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY,
            context={**context, "lead_id": lead_id, "query_type": "interactive_chat"},
            prompt=f"Jorge asks: {query}",
            temperature=0.8,  # Slightly more creative for chat
            use_tools=True,
        )

        return await self.process_request(request)

    async def analyze_lead(
        self, lead_id: str, include_scoring: bool = True, include_churn_analysis: bool = True
    ) -> ClaudeResponse:
        """Comprehensive lead analysis with Claude reasoning"""

        # Gather all available data
        context = await self._gather_lead_context(lead_id, include_scoring, include_churn_analysis)

        prompt = f"""Analyze this lead comprehensively:

        Lead ID: {lead_id}

        Available data:
        {json.dumps(context, indent=2, default=str)}

        Provide a complete intelligence analysis including:
        1. Executive summary (2-3 sentences)
        2. Qualification assessment
        3. Behavioral insights and personality profile
        4. Risk factors and mitigation strategies
        5. Opportunities and competitive advantages
        6. Recommended next actions with timing
        7. Expected outcomes and success probability"""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context=context,
            prompt=prompt,
            max_tokens=6000,  # Longer for comprehensive analysis
        )

        return await self.process_request(request)

    async def synthesize_report(
        self, metrics: Dict[str, Any], report_type: str = "weekly_summary", market_context: Optional[Dict] = None
    ) -> ClaudeResponse:
        """Generate narrative reports from quantitative metrics"""

        context = {
            "metrics": metrics,
            "report_type": report_type,
            "market_context": market_context or {},
            "generated_at": datetime.now().isoformat(),
        }

        prompt = f"""Generate a {report_type} report for Jorge:

        Performance Metrics:
        {json.dumps(metrics, indent=2, default=str)}

        Market Context:
        {json.dumps(market_context or {}, indent=2, default=str)}

        Create a comprehensive report with:
        1. Executive Summary (key takeaways)
        2. Performance Analysis (trends and patterns)
        3. Strategic Insights (what the data means)
        4. Risk Assessment (potential issues)
        5. Opportunities (growth areas)
        6. Action Items (specific next steps)

        Use Jorge's voice: direct, data-driven, action-oriented."""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.REPORT_SYNTHESIS, context=context, prompt=prompt, max_tokens=5000
        )

        return await self.process_request(request)

    async def generate_script(
        self, lead_id: str, script_type: str, channel: str = "sms", variants: int = 1
    ) -> ClaudeResponse:
        """Generate personalized scripts for lead communication"""

        # Get lead context
        context = await self._gather_lead_context(lead_id)

        # Add script-specific context
        context.update({"script_type": script_type, "channel": channel, "variants_requested": variants})

        prompt = f"""Generate a personalized {script_type} script for {channel}:

        Lead Context:
        {json.dumps(context, indent=2, default=str)}

        Requirements:
        - Match lead's communication style
        - Reference conversation history appropriately
        - Handle potential objections proactively
        - Include clear call-to-action
        - Optimize for {channel} format

        {"Generate " + str(variants) + " variants for A/B testing" if variants > 1 else "Generate primary script"}

        For each script provide:
        1. The script text
        2. Rationale for approach
        3. Expected objections and responses
        4. Success metrics to track"""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.SCRIPT_GENERATION, context=context, prompt=prompt, max_tokens=4000
        )

        return await self.process_request(request)

    async def orchestrate_intervention(self, lead_id: str, churn_prediction: Dict[str, Any]) -> ClaudeResponse:
        """Plan intervention strategy for at-risk leads"""

        context = await self._gather_lead_context(lead_id, include_churn_analysis=True)
        context["churn_prediction"] = churn_prediction

        prompt = f"""Design an intervention strategy for an at-risk lead:

        Lead Context:
        {json.dumps(context, indent=2, default=str)}

        Churn Analysis:
        {json.dumps(churn_prediction, indent=2, default=str)}

        Create a comprehensive intervention plan:
        1. Situation Assessment (why at risk)
        2. Intervention Strategy (approach and timing)
        3. Communication Plan (channel, message, frequency)
        4. Escalation Path (if initial approach fails)
        5. Success Metrics (how to measure effectiveness)
        6. Fallback Strategy (if lead is lost)

        Consider:
        - Lead's personality and preferences
        - Previous intervention attempts
        - Market timing and urgency
        - Jorge's capacity and resources"""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY, context=context, prompt=prompt, max_tokens=4000
        )

        return await self.process_request(request)

    async def analyze_conversation_sentiment(
        self, lead_id: str, messages: List[Dict[str, str]], tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze conversation sentiment for drift and re-engagement opportunity.

        Args:
            lead_id: The ID of the lead
            messages: Conversation history
            tenant_id: Optional tenant ID

        Returns:
            Analysis results from SentimentDriftEngine
        """
        return await self.sentiment_drift_engine.analyze_conversation_drift(
            messages=messages, lead_id=lead_id, tenant_id=tenant_id
        )

    async def detect_lead_persona(
        self,
        lead_id: str,
        messages: List[Dict[str, str]],
        lead_context: Dict[str, Any],
        tenant_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Detect lead persona for tone adaptation.
        """
        return await self.psychographic_engine.detect_persona(
            messages=messages, lead_context=lead_context, tenant_id=tenant_id
        )

    async def provide_market_reality_check(
        self, expected_price: float, address: str, zip_code: str, tenant_id: Optional[str] = None
    ) -> str:
        """
        Provide a market-aware pricing reality check.
        """
        market_context = await self.market_injector.get_market_context(address, zip_code)
        return await self.market_injector.synthesize_price_reality_check(
            seller_expected_price=expected_price, market_context=market_context, tenant_id=tenant_id
        )

    async def perform_research(self, topic: str, context: Optional[Dict[str, Any]] = None) -> ClaudeResponse:
        """Perform deep research using Perplexity and synthesize with Claude"""

        # 1. Get raw research from Perplexity
        raw_research = await self.researcher.research_topic(topic, json.dumps(context) if context else None)

        # 2. Synthesize with Claude for strategic depth
        prompt = f"""Synthesize this research data for Jorge:
        
        Topic: {topic}
        
        Raw Research Data:
        {raw_research}
        
        Provide:
        1. Strategic Summary (The 'So What?')
        2. Top 3 Actionable Takeaways
        3. Local Market Impact Analysis
        4. Risk/Opportunity Assessment
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.RESEARCH_QUERY, context=context or {}, prompt=prompt, max_tokens=4000
        )

        return await self.process_request(request)

    # Private helper methods

    def _get_system_prompt(self, task_type: ClaudeTaskType) -> str:
        """Get appropriate system prompt for task type"""
        prompt_mapping = {
            ClaudeTaskType.CHAT_QUERY: "chat_assistant",
            ClaudeTaskType.LEAD_ANALYSIS: "lead_analyzer",
            ClaudeTaskType.REPORT_SYNTHESIS: "report_synthesizer",
            ClaudeTaskType.SCRIPT_GENERATION: "script_generator",
            ClaudeTaskType.INTERVENTION_STRATEGY: "script_generator",
            ClaudeTaskType.BEHAVIORAL_INSIGHT: "lead_analyzer",
            ClaudeTaskType.OMNIPOTENT_ASSISTANT: "omnipotent_assistant",
            ClaudeTaskType.PERSONA_OPTIMIZATION: "persona_optimizer",
            ClaudeTaskType.EXECUTIVE_BRIEFING: "report_synthesizer",
            ClaudeTaskType.REVENUE_PROJECTION: "report_synthesizer",
            ClaudeTaskType.RESEARCH_QUERY: "researcher_assistant",
        }

        # Check if the mapped prompt exists, fallback to chat_assistant
        prompt_key = prompt_mapping.get(task_type, "chat_assistant")
        return self.system_prompts.get(prompt_key, self.system_prompts.get("chat_assistant", ""))

    async def _enhance_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance request context with memory and historical data"""
        enhanced = context.copy()

        # Add semantic memory if lead_id is available
        if "lead_id" in context and context["lead_id"]:
            try:
                lead_id = context["lead_id"]
                # Use short-lived in-process cache to avoid repeated memory fetches
                cache_key = f"mem_ctx:{lead_id}"
                cached = self._memory_context_cache.get(cache_key)
                if cached is not None:
                    memory_context = cached
                else:
                    memory_context = await self.memory.get_context(lead_id)
                    self._memory_context_cache[cache_key] = memory_context
                enhanced["semantic_memory"] = memory_context.get("relevant_knowledge", "")
                enhanced["conversation_history"] = memory_context.get("conversation_history", [])
                enhanced["extracted_preferences"] = memory_context.get("extracted_preferences", {})
            except (ConnectionError, TimeoutError, KeyError) as e:
                # Graceful degradation if memory unavailable
                logger.debug(f"Memory service unavailable for lead {lead_id}: {e}")
                pass

        return enhanced

    def _build_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt with context"""
        return f"""{base_prompt}

Context:
{json.dumps(context, indent=2, default=str)}

Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    async def _call_claude(
        self,
        system_prompt: str,
        user_prompt: str,
        model: str,
        max_tokens: int,
        temperature: float,
        streaming: bool = False,
        complexity: Optional[TaskComplexity] = None,
        tenant_id: Optional[str] = None,
    ) -> Any:
        """Make actual Claude API call"""

        if streaming:
            # Handle streaming response using astream
            content = ""
            async for chunk in self.llm.astream(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                complexity=complexity,
                tenant_id=tenant_id,
            ):
                content += chunk
            # Note: streaming doesn't return usage info in current LLMClient implementation
            from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse

            return LLMResponse(content=content, provider=LLMProvider.CLAUDE, model=model)
        else:
            # Standard response using agenerate
            return await self.llm.agenerate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                complexity=complexity,
                tenant_id=tenant_id,
            )

    # ==================== COMPREHENSIVE RESPONSE PARSING HELPERS ====================

    def _extract_json_block(self, content: str) -> Optional[Dict[str, Any]]:
        """
        Extract JSON block from Claude response.

        Handles:
        - Markdown code blocks: ```json ... ```
        - Plain JSON objects
        - Nested JSON structures

        Returns:
            Parsed JSON dict or None if extraction fails
        """
        try:
            # Strategy 1: Extract from markdown JSON code block
            if "```json" in content:
                json_match = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(1))

            # Strategy 2: Extract from generic code block
            if "```" in content:
                code_match = re.search(r"```\s*\n?(.*?)\n?```", content, re.DOTALL)
                if code_match:
                    try:
                        return json.loads(code_match.group(1))
                    except json.JSONDecodeError:
                        pass

            # Strategy 3: Find first JSON object using balanced bracket matching
            json_start = content.find("{")
            if json_start >= 0:
                json_str = self._extract_balanced_json(content, json_start)
                if json_str:
                    return json.loads(json_str)

            return None
        except (json.JSONDecodeError, AttributeError, IndexError):
            return None

    def _extract_balanced_json(self, content: str, start_idx: int) -> Optional[str]:
        """
        Extract a JSON object using balanced bracket matching to avoid regex catastrophic backtracking.

        Args:
            content: Text content
            start_idx: Index of the opening brace

        Returns:
            JSON string if valid brackets found, None otherwise
        """
        try:
            brace_count = 0
            in_string = False
            escape_next = False

            for i in range(start_idx, len(content)):
                char = content[i]

                # Handle string escaping
                if escape_next:
                    escape_next = False
                    continue

                if char == "\\" and in_string:
                    escape_next = True
                    continue

                # Handle string boundaries
                if char == '"':
                    in_string = not in_string
                    continue

                # Only count braces outside of strings
                if not in_string:
                    if char == "{":
                        brace_count += 1
                    elif char == "}":
                        brace_count -= 1

                        # Found matching closing brace
                        if brace_count == 0:
                            candidate = content[start_idx : i + 1]
                            # Validate it's actually JSON before returning
                            try:
                                json.loads(candidate)
                                return candidate
                            except json.JSONDecodeError:
                                # Continue searching for next JSON object
                                break

            return None

        except (IndexError, TypeError):
            return None

    def _extract_list_items(self, content: str, section_header: str) -> List[str]:
        """
        Extract list items from markdown sections.

        Handles:
        - Numbered lists: 1. Item, 2. Item
        - Bullet lists: - Item, * Item, • Item
        - Nested lists

        Args:
            content: Full text content
            section_header: Section header to look for (case-insensitive)

        Returns:
            List of extracted items
        """
        items = []

        try:
            # Find section in content (case-insensitive)
            pattern = re.compile(rf"{re.escape(section_header)}:?\s*\n", re.IGNORECASE)
            match = pattern.search(content)

            if not match:
                return items

            # Extract text after header until next major section or end
            start_pos = match.end()
            remaining_text = content[start_pos:]

            # Stop at next major header (##, ###, or capitalized section)
            next_section = re.search(r"\n#{2,}|\n[A-Z][A-Za-z\s]+:\s*\n", remaining_text)
            if next_section:
                section_text = remaining_text[: next_section.start()]
            else:
                section_text = remaining_text

            # Extract numbered items (1., 2., etc.)
            numbered_items = re.findall(
                r"^\s*\d+\.\s+(.+?)(?=\n\s*\d+\.|\n\n|\Z)", section_text, re.MULTILINE | re.DOTALL
            )
            if numbered_items:
                items.extend([item.strip() for item in numbered_items])

            # Extract bullet items (-, *, •)
            bullet_items = re.findall(
                r"^\s*[-*•]\s+(.+?)(?=\n\s*[-*•]|\n\n|\Z)", section_text, re.MULTILINE | re.DOTALL
            )
            if bullet_items and not numbered_items:
                items.extend([item.strip() for item in bullet_items])

        except (AttributeError, IndexError, re.error):
            pass

        return items

    def _parse_response(self, content: str, task_type: ClaudeTaskType) -> ClaudeResponse:
        """
        Parse and structure Claude response with intelligent extraction.

        Extracts:
        - Confidence scores
        - Recommended actions
        - Script variants (for A/B testing)
        - Risk factors
        - Opportunities

        Args:
            content: Raw Claude response text
            task_type: Type of task for context-specific parsing

        Returns:
            Structured ClaudeResponse with extracted metadata
        """
        response = ClaudeResponse(content=content)

        try:
            # Extract JSON block if present for structured data
            json_data = self._extract_json_block(content)

            # Parse confidence score
            response.confidence = self._parse_confidence_score(content, json_data)

            # Parse recommended actions
            response.recommended_actions = self._parse_recommended_actions(content, json_data)

            # Task-specific parsing
            if task_type == ClaudeTaskType.SCRIPT_GENERATION:
                # Extract script variants for A/B testing
                script_variants = self._parse_script_variants(content, json_data)
                response.metadata["script_variants"] = script_variants

            elif task_type == ClaudeTaskType.LEAD_ANALYSIS:
                # Extract risk factors and opportunities
                risk_factors = self._parse_risk_factors(content, json_data)
                opportunities = self._parse_opportunities(content, json_data)

                response.metadata["risk_factors"] = risk_factors
                response.metadata["opportunities"] = opportunities

            elif task_type in [ClaudeTaskType.INTERVENTION_STRATEGY, ClaudeTaskType.REPORT_SYNTHESIS]:
                # Extract opportunities for strategic tasks
                opportunities = self._parse_opportunities(content, json_data)
                response.metadata["opportunities"] = opportunities

        except Exception as e:
            # Graceful degradation - log error but don't fail
            response.metadata["parsing_error"] = str(e)
            response.metadata["parsing_failed"] = True

        return response

    def _parse_confidence_score(self, content: str, json_data: Optional[Dict[str, Any]] = None) -> Optional[float]:
        """
        Extract confidence score from Claude response.

        Extraction strategies:
        1. JSON field: {"confidence": 0.85}
        2. Percentage: "confidence: 85%" or "85% confidence"
        3. Decimal: "confidence: 0.85"
        4. Qualitative: "high confidence" → 0.8

        Args:
            content: Response text
            json_data: Parsed JSON data if available

        Returns:
            Confidence score (0-1) or None if not found
        """
        try:
            # Strategy 1: Extract from JSON
            if json_data:
                if "confidence" in json_data:
                    conf = json_data["confidence"]
                    # Handle percentage or decimal
                    if isinstance(conf, (int, float)):
                        return min(1.0, max(0.0, conf if conf <= 1.0 else conf / 100.0))
                if "confidence_score" in json_data:
                    conf = json_data["confidence_score"]
                    return min(1.0, max(0.0, conf if conf <= 1.0 else conf / 100.0))

            # Strategy 2: Extract percentage from text
            # Patterns: "confidence: 85%", "85% confidence", "confidence = 0.85"
            percentage_patterns = [
                r"confidence:?\s*(\d+(?:\.\d+)?)\s*%",
                r"(\d+(?:\.\d+)?)\s*%\s*confidence",
                r"confidence(?:\s+score)?:?\s*=?\s*(\d+(?:\.\d+)?)",
            ]

            for pattern in percentage_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    value = float(match.group(1))
                    # Normalize to 0-1 range
                    return min(1.0, max(0.0, value if value <= 1.0 else value / 100.0))

            # Strategy 3: Qualitative confidence mapping
            qualitative_map = {
                r"\b(very\s+)?high\s+confidence\b": 0.9,
                r"\bconfident\b": 0.8,
                r"\bmoderate\s+confidence\b": 0.7,
                r"\bsome\s+confidence\b": 0.6,
                r"\blow\s+confidence\b": 0.4,
                r"\bvery\s+low\s+confidence\b": 0.3,
            }

            for pattern, score in qualitative_map.items():
                if re.search(pattern, content, re.IGNORECASE):
                    return score

            # Default: Return moderate confidence if indicators found
            if re.search(r"\bconfidence\b", content, re.IGNORECASE):
                return 0.7

            return None

        except (ValueError, TypeError, AttributeError):
            return None

    def _parse_recommended_actions(
        self, content: str, json_data: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Extract recommended actions from Claude response.

        Returns structured actions with:
        - action: The action to take
        - priority: high/medium/low
        - timing: immediate/urgent/moderate/low
        - reasoning: Why this action is recommended

        Args:
            content: Response text
            json_data: Parsed JSON data if available

        Returns:
            List of action dictionaries
        """
        actions = []

        try:
            # Strategy 1: Extract from JSON
            if json_data:
                if "recommended_actions" in json_data:
                    json_actions = json_data["recommended_actions"]
                    if isinstance(json_actions, list):
                        for item in json_actions:
                            if isinstance(item, dict):
                                actions.append(item)
                            elif isinstance(item, str):
                                actions.append(self._structure_action(item))
                    return actions

                if "actions" in json_data:
                    json_actions = json_data["actions"]
                    if isinstance(json_actions, list):
                        for item in json_actions:
                            if isinstance(item, dict):
                                actions.append(item)
                            elif isinstance(item, str):
                                actions.append(self._structure_action(item))
                    return actions

            # Strategy 2: Extract from text sections
            section_headers = [
                "recommended actions",
                "next steps",
                "action items",
                "recommendations",
                "suggested actions",
            ]

            for header in section_headers:
                items = self._extract_list_items(content, header)
                if items:
                    for item in items:
                        actions.append(self._structure_action(item))
                    break  # Use first matching section

            return actions

        except (ValueError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse recommended actions: {e}")
            return []

    def _structure_action(self, action_text: str) -> Dict[str, Any]:
        """
        Convert action text into structured dict with priority and timing.

        Args:
            action_text: Raw action description

        Returns:
            Structured action dict
        """
        # Detect priority keywords
        priority = "medium"
        if re.search(r"\b(critical|urgent|immediate|high\s+priority)\b", action_text, re.IGNORECASE):
            priority = "high"
        elif re.search(r"\b(low\s+priority|optional|consider)\b", action_text, re.IGNORECASE):
            priority = "low"

        # Detect timing keywords
        timing = "moderate"
        if re.search(r"\b(immediate|now|asap|today|urgent)\b", action_text, re.IGNORECASE):
            timing = "immediate"
        elif re.search(r"\b(within\s+24|tomorrow|soon)\b", action_text, re.IGNORECASE):
            timing = "urgent"
        elif re.search(r"\b(this\s+week|next\s+few\s+days)\b", action_text, re.IGNORECASE):
            timing = "moderate"
        elif re.search(r"\b(next\s+week|later|when\s+possible)\b", action_text, re.IGNORECASE):
            timing = "low"

        return {"action": action_text.strip(), "priority": priority, "timing": timing}

    def _parse_script_variants(self, content: str, json_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extract script variants for A/B testing.

        Returns structured variants with:
        - variant_name: A, B, Control, etc.
        - script_text: The actual script
        - rationale: Why this approach works
        - expected_performance: Predicted effectiveness
        - channel: SMS, email, call, etc.

        Args:
            content: Response text
            json_data: Parsed JSON data if available

        Returns:
            List of script variant dictionaries
        """
        variants = []

        try:
            # Strategy 1: Extract from JSON
            if json_data:
                if "variants" in json_data:
                    json_variants = json_data["variants"]
                    if isinstance(json_variants, list):
                        return json_variants
                    elif isinstance(json_variants, dict):
                        # Convert dict of variants to list
                        for name, data in json_variants.items():
                            if isinstance(data, dict):
                                data["variant_name"] = name
                                variants.append(data)
                            else:
                                variants.append({"variant_name": name, "script_text": str(data)})
                        return variants

                if "scripts" in json_data:
                    return self._parse_script_variants(content, {"variants": json_data["scripts"]})

            # Strategy 2: Extract from text sections
            # Look for "Variant A:", "Script 1:", "Option A:", etc.
            variant_patterns = [
                r"(?:Variant|Script|Option)\s+([A-Z\d]+):\s*\n(.*?)(?=(?:Variant|Script|Option)\s+[A-Z\d]+:|$)",
                r"(\d+)\.\s+(.+?)(?=\n\d+\.|\Z)",
            ]

            for pattern in variant_patterns:
                matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                if matches:
                    for name, script_text in matches:
                        # Extract rationale if present
                        rationale_match = re.search(
                            r"rationale:?\s*(.+?)(?=\n\n|\n[A-Z]|\Z)", script_text, re.IGNORECASE | re.DOTALL
                        )
                        rationale = rationale_match.group(1).strip() if rationale_match else ""

                        # Clean script text
                        clean_script = re.sub(r"rationale:.*", "", script_text, flags=re.IGNORECASE | re.DOTALL).strip()

                        variants.append(
                            {"variant_name": name.strip(), "script_text": clean_script, "rationale": rationale}
                        )
                    break

            return variants

        except (ValueError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse script variants: {e}")
            return []

    def _parse_risk_factors(self, content: str, json_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """
        Extract risk factors from lead analysis.

        Returns structured risks with:
        - factor: Description of the risk
        - severity: high/medium/low
        - mitigation: Suggested mitigation strategy

        Args:
            content: Response text
            json_data: Parsed JSON data if available

        Returns:
            List of risk factor dictionaries
        """
        risks = []

        try:
            # Strategy 1: Extract from JSON
            if json_data:
                if "risk_factors" in json_data:
                    json_risks = json_data["risk_factors"]
                    if isinstance(json_risks, list):
                        for item in json_risks:
                            if isinstance(item, dict):
                                risks.append(item)
                            elif isinstance(item, str):
                                risks.append(self._structure_risk(item))
                    return risks

                if "risks" in json_data:
                    json_risks = json_data["risks"]
                    if isinstance(json_risks, list):
                        for item in json_risks:
                            if isinstance(item, dict):
                                risks.append(item)
                            elif isinstance(item, str):
                                risks.append(self._structure_risk(item))
                    return risks

            # Strategy 2: Extract from text sections
            section_headers = ["risk factors", "risks", "potential risks", "concerns", "challenges"]

            for header in section_headers:
                items = self._extract_list_items(content, header)
                if items:
                    for item in items:
                        risks.append(self._structure_risk(item))
                    break

            return risks

        except (ValueError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse risk factors: {e}")
            return []

    def _structure_risk(self, risk_text: str) -> Dict[str, str]:
        """
        Convert risk text into structured dict with severity classification.

        Args:
            risk_text: Raw risk description

        Returns:
            Structured risk dict
        """
        # Detect severity keywords
        severity = "medium"
        if re.search(r"\b(critical|severe|high\s+risk|major)\b", risk_text, re.IGNORECASE):
            severity = "high"
        elif re.search(r"\b(low\s+risk|minor|slight)\b", risk_text, re.IGNORECASE):
            severity = "low"

        # Extract mitigation if present
        mitigation_match = re.search(r"(?:mitigation|solution|address|handle):?\s*(.+?)$", risk_text, re.IGNORECASE)
        mitigation = mitigation_match.group(1).strip() if mitigation_match else ""

        # Clean risk text
        clean_risk = re.sub(r"(?:mitigation|solution|address|handle):.*", "", risk_text, flags=re.IGNORECASE).strip()

        return {"factor": clean_risk, "severity": severity, "mitigation": mitigation}

    def _parse_opportunities(self, content: str, json_data: Optional[Dict[str, Any]] = None) -> List[Dict[str, str]]:
        """
        Extract opportunities from analysis (upsell, cross-sell, growth areas).

        Returns structured opportunities with:
        - opportunity: Description of the opportunity
        - potential_value: Estimated value (dollar amount or qualitative)
        - action_required: What action to take
        - timeframe: When to pursue

        Args:
            content: Response text
            json_data: Parsed JSON data if available

        Returns:
            List of opportunity dictionaries
        """
        opportunities = []

        try:
            # Strategy 1: Extract from JSON
            if json_data:
                if "opportunities" in json_data:
                    json_opps = json_data["opportunities"]
                    if isinstance(json_opps, list):
                        for item in json_opps:
                            if isinstance(item, dict):
                                opportunities.append(item)
                            elif isinstance(item, str):
                                opportunities.append(self._structure_opportunity(item))
                    return opportunities

            # Strategy 2: Extract from text sections
            section_headers = [
                "opportunities",
                "growth opportunities",
                "upsell potential",
                "competitive advantages",
                "strategic opportunities",
            ]

            for header in section_headers:
                items = self._extract_list_items(content, header)
                if items:
                    for item in items:
                        opportunities.append(self._structure_opportunity(item))
                    break

            return opportunities

        except (ValueError, KeyError, AttributeError) as e:
            logger.warning(f"Failed to parse opportunities: {e}")
            return []

    def _structure_opportunity(self, opp_text: str) -> Dict[str, str]:
        """
        Convert opportunity text into structured dict with value assessment.

        Args:
            opp_text: Raw opportunity description

        Returns:
            Structured opportunity dict
        """
        # Extract dollar amounts
        value_match = re.search(r"\$\s*([\d,]+(?:\.\d{2})?)", opp_text)
        potential_value = value_match.group(0) if value_match else ""

        # Extract percentage values
        if not potential_value:
            pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", opp_text)
            potential_value = pct_match.group(0) if pct_match else "medium"

        # Classify qualitatively if no numbers found
        if not potential_value or potential_value == "medium":
            if re.search(r"\b(high|significant|major|substantial)\b", opp_text, re.IGNORECASE):
                potential_value = "high"
            elif re.search(r"\b(low|minimal|small)\b", opp_text, re.IGNORECASE):
                potential_value = "low"

        # Extract action if present
        action_match = re.search(r"(?:action|next\s+step):?\s*(.+?)$", opp_text, re.IGNORECASE)
        action_required = action_match.group(1).strip() if action_match else ""

        # Clean opportunity text
        clean_opp = re.sub(r"(?:action|next\s+step):.*", "", opp_text, flags=re.IGNORECASE).strip()
        clean_opp = re.sub(r"\$[\d,]+(?:\.\d{2})?", "", clean_opp).strip()

        return {"opportunity": clean_opp, "potential_value": potential_value, "action_required": action_required}

    async def _gather_lead_context(
        self, lead_id: str, include_scoring: bool = True, include_churn_analysis: bool = True
    ) -> Dict[str, Any]:
        """Gather comprehensive context for a lead"""
        context = {"lead_id": lead_id}

        try:
            # Get memory context
            memory_data = await self.memory.get_context(lead_id)
            context["memory"] = memory_data

            # Run scoring and churn analysis in parallel where possible
            parallel_tasks = {}

            if include_scoring:
                # Run both scorers concurrently via executor (they are synchronous)
                loop = asyncio.get_event_loop()
                parallel_tasks["jorge"] = loop.run_in_executor(
                    None, self.jorge_scorer.calculate_with_reasoning, memory_data
                )
                parallel_tasks["ml"] = loop.run_in_executor(None, self.ml_scorer.predict_conversion, memory_data)

            if include_churn_analysis:
                parallel_tasks["churn"] = self._analyze_churn_risk_comprehensive(lead_id, memory_data)

            if parallel_tasks:
                results = await asyncio.gather(*parallel_tasks.values(), return_exceptions=True)
                result_map = dict(zip(parallel_tasks.keys(), results))

                if include_scoring:
                    jorge_result = result_map.get("jorge")
                    ml_result = result_map.get("ml")
                    if not isinstance(jorge_result, Exception) and not isinstance(ml_result, Exception):
                        context["scoring"] = {
                            "jorge_score": jorge_result,
                            "ml_score": ml_result,
                        }

                if include_churn_analysis:
                    churn_result = result_map.get("churn")
                    if not isinstance(churn_result, Exception):
                        context["churn_analysis"] = churn_result

        except Exception as e:
            context["error"] = f"Error gathering context: {str(e)}"

        return context

    def _extract_conversation_messages(self, memory_data: Dict[str, Any]) -> List[Dict[str, str]]:
        """
        Extract and validate conversation messages from memory data.

        Args:
            memory_data: Memory context dictionary

        Returns:
            List of validated message dictionaries with 'role' and 'content' keys
        """
        try:
            raw_messages = []

            # Strategy 1: Direct conversation_history field
            if "conversation_history" in memory_data:
                history = memory_data["conversation_history"]
                if isinstance(history, list) and len(history) > 0:
                    raw_messages = history

            # Strategy 2: Messages field
            elif "messages" in memory_data:
                messages = memory_data["messages"]
                if isinstance(messages, list) and len(messages) > 0:
                    raw_messages = messages

            # Strategy 3: Nested in context
            elif "context" in memory_data:
                context = memory_data["context"]
                if isinstance(context, dict):
                    if "conversation_history" in context:
                        raw_messages = context["conversation_history"]
                    elif "messages" in context:
                        raw_messages = context["messages"]

            # Validate and clean messages
            validated_messages = []
            for i, msg in enumerate(raw_messages):
                try:
                    # Ensure message is a dictionary
                    if not isinstance(msg, dict):
                        continue

                    # Extract and validate required fields
                    role = msg.get("role")
                    content = msg.get("content")

                    # Skip invalid messages
                    if not role or not content:
                        continue

                    # Normalize role values
                    role_str = str(role).lower().strip()
                    if role_str not in ["user", "assistant", "system", "human", "ai", "bot"]:
                        # Map common role variations
                        if role_str in ["customer", "lead", "client"]:
                            role_str = "user"
                        elif role_str in ["agent", "jorge", "bot", "ai"]:
                            role_str = "assistant"
                        else:
                            role_str = "user"  # Default fallback

                    # Clean and validate content
                    content_str = str(content).strip()
                    if not content_str or len(content_str) > 10000:  # Skip empty or excessively long messages
                        continue

                    validated_messages.append({"role": role_str, "content": content_str})

                except (ValueError, KeyError, TypeError) as e:
                    # Skip individual malformed messages
                    logger.debug(f"Skipping malformed message: {e}")
                    continue

            return validated_messages

        except (ValueError, KeyError, TypeError) as e:
            # Graceful degradation on any error
            logger.warning(f"Failed to validate messages: {e}")
            return []

    async def _analyze_churn_risk_comprehensive(self, lead_id: str, memory_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform comprehensive multi-dimensional churn risk analysis.

        Integrates:
        - Core ML-based churn prediction
        - Sentiment drift analysis
        - Psychographic risk factors
        - Historical engagement patterns

        Args:
            lead_id: Lead identifier
            memory_data: Memory context data

        Returns:
            Comprehensive churn analysis dictionary with:
            - core_prediction: ML model results
            - sentiment_analysis: Drift detection results
            - psychographic_factors: Personality-based risk
            - composite_risk_score: Weighted average risk (0-100)
            - intervention_recommendations: Actionable steps
            - confidence_level: Overall analysis confidence (0-1)
            - analysis_timestamp: When analysis was performed
        """
        try:
            # Initialize result structure
            analysis = {"lead_id": lead_id, "analysis_timestamp": datetime.now().isoformat(), "status": "success"}

            # Extract conversation messages for behavioral analysis
            messages = self._extract_conversation_messages(memory_data)

            # Robust parallel execution with named task mapping and timeout protection
            task_map = {}

            # Build task map only for available/applicable analyses
            if hasattr(self, "churn_predictor") and self.churn_predictor:
                task_map["core_prediction"] = self.churn_predictor.predict_churn_risk(lead_id)

            if len(messages) >= 4:
                task_map["sentiment"] = self.sentiment_drift_engine.analyze_conversation_drift(
                    messages=messages, lead_id=lead_id
                )

            if len(messages) >= 2:
                task_map["psychographic"] = self.psychographic_engine.detect_persona(
                    messages=messages, lead_context=memory_data
                )

            # Execute tasks with timeout protection
            results = {}
            if task_map:
                try:
                    task_results = await asyncio.wait_for(
                        asyncio.gather(*task_map.values(), return_exceptions=True),
                        timeout=7.0,  # Fail fast — services should respond within 5s
                    )
                    results = dict(zip(task_map.keys(), task_results))
                except asyncio.TimeoutError:
                    # Log timeout and continue with defaults
                    analysis["execution_warning"] = f"Churn analysis timeout for lead {lead_id}"

            # Process core prediction results with robust error handling
            ml_risk_score = 50.0  # Default neutral risk
            ml_confidence = 0.3  # Default low confidence

            if "core_prediction" in results:
                result = results["core_prediction"]
                if isinstance(result, Exception):
                    analysis["core_prediction"] = {"error": f"ML prediction failed: {str(result)}"}
                elif result and hasattr(result, "risk_score_14d"):
                    # ChurnPrediction dataclass - extract with validation
                    try:
                        analysis["core_prediction"] = {
                            "risk_score_7d": getattr(result, "risk_score_7d", 50.0),
                            "risk_score_14d": getattr(result, "risk_score_14d", 50.0),
                            "risk_score_30d": getattr(result, "risk_score_30d", 50.0),
                            "risk_tier": result.risk_tier.value
                            if hasattr(result.risk_tier, "value")
                            else str(result.risk_tier),
                            "confidence": getattr(result, "confidence", 0.3),
                            "top_risk_factors": getattr(result, "top_risk_factors", [])[:5],  # Top 5 factors
                            "recommended_actions": getattr(result, "recommended_actions", [])[:3],  # Top 3 actions
                            "intervention_urgency": getattr(result, "intervention_urgency", "medium"),
                            "model_version": getattr(result, "model_version", "unknown"),
                        }
                        ml_risk_score = float(result.risk_score_14d)
                        ml_confidence = float(result.confidence)
                    except (AttributeError, ValueError, TypeError) as e:
                        analysis["core_prediction"] = {"error": f"ML prediction parsing failed: {str(e)}"}
                else:
                    analysis["core_prediction"] = {"error": "ML prediction returned invalid data"}
            else:
                analysis["core_prediction"] = {"error": "ML prediction not available"}

            # Process sentiment analysis results with robust error handling
            sentiment_risk = 50.0  # Default neutral risk
            sentiment_confidence = 0.2  # Default low confidence

            if "sentiment" in results:
                result = results["sentiment"]
                if isinstance(result, Exception):
                    analysis["sentiment_analysis"] = {"error": f"Sentiment analysis failed: {str(result)}"}
                elif result and isinstance(result, dict):
                    analysis["sentiment_analysis"] = result

                    # Convert sentiment drift to risk contribution
                    drift_score = result.get("drift_score", 0)
                    if drift_score < -0.4:  # Significant negative drift
                        sentiment_risk = 75.0
                    elif drift_score < -0.2:  # Moderate negative drift
                        sentiment_risk = 55.0
                    elif drift_score < 0:  # Slight negative drift
                        sentiment_risk = 35.0
                    else:  # Positive or neutral
                        sentiment_risk = 20.0

                    sentiment_confidence = result.get("confidence", 0.5)
                else:
                    analysis["sentiment_analysis"] = {"status": "invalid_data"}
            else:
                analysis["sentiment_analysis"] = {"status": "insufficient_data"}

            # Process psychographic analysis results with robust error handling
            psycho_risk_modifier = 1.0  # Default neutral modifier
            persona_confidence = 0.2  # Default low confidence

            if "psychographic" in results:
                result = results["psychographic"]
                if isinstance(result, Exception):
                    analysis["psychographic_factors"] = {"error": f"Psychographic analysis failed: {str(result)}"}
                elif result and isinstance(result, dict):
                    analysis["psychographic_factors"] = result

                    # Map personas to churn risk modifiers
                    persona = result.get("primary_persona", "unknown")
                    persona_confidence = result.get("confidence", 0.5)

                    # High-risk personas
                    if persona in ["loss_aversion", "motivated_seller"]:
                        psycho_risk_modifier = 1.2  # 20% higher risk
                    # Medium-risk personas
                    elif persona in ["first_time_buyer", "owner_occupant"]:
                        psycho_risk_modifier = 1.0  # Neutral
                    # Lower-risk personas
                    elif persona in ["investor", "luxury_seeker"]:
                        psycho_risk_modifier = 0.8  # 20% lower risk
                    else:
                        psycho_risk_modifier = 1.0  # Default neutral
                else:
                    analysis["psychographic_factors"] = {"status": "invalid_data"}
            else:
                analysis["psychographic_factors"] = {"status": "insufficient_data"}

            # Calculate composite risk score (weighted average)
            # Weights: ML (60%), Sentiment (25%), Psychographic modifier (15%)
            base_risk = (ml_risk_score * 0.60) + (sentiment_risk * 0.25)
            composite_risk_score = min(100.0, base_risk * (0.85 + (psycho_risk_modifier * 0.15)))

            # Calculate overall confidence (average of component confidences)
            overall_confidence = (ml_confidence * 0.5) + (sentiment_confidence * 0.3) + (persona_confidence * 0.2)

            analysis["composite_risk_score"] = round(composite_risk_score, 2)
            analysis["confidence_level"] = round(overall_confidence, 2)

            # Generate synthesized intervention recommendations
            recommendations = []

            # Add ML-based recommendations
            if core_prediction and hasattr(core_prediction, "recommended_actions"):
                recommendations.extend(core_prediction.recommended_actions[:2])

            # Add sentiment-based recommendations
            if sentiment_result and sentiment_result.get("alert") == "COLD_LEAD":
                objection = sentiment_result.get("objection_hint", "general concerns")
                recommendations.append(f"Address {objection} with personalized re-engagement message")

            # Add psychographic-based recommendations
            if psycho_result and "recommended_tone" in psycho_result:
                tone = psycho_result["recommended_tone"]
                recommendations.append(f"Adjust communication tone: {tone}")

            # Prioritize if high risk
            if composite_risk_score >= 70:
                recommendations.insert(0, "URGENT: Immediate intervention required")

            analysis["intervention_recommendations"] = recommendations[:5]  # Top 5

            # Add risk tier classification
            if composite_risk_score >= 80:
                analysis["risk_tier"] = "critical"
            elif composite_risk_score >= 60:
                analysis["risk_tier"] = "high"
            elif composite_risk_score >= 30:
                analysis["risk_tier"] = "medium"
            else:
                analysis["risk_tier"] = "low"

            return analysis

        except Exception as e:
            # Graceful fallback with error details
            return {
                "lead_id": lead_id,
                "analysis_timestamp": datetime.now().isoformat(),
                "status": "error",
                "error_message": str(e),
                "composite_risk_score": 50.0,  # Neutral default
                "confidence_level": 0.1,  # Very low confidence
                "risk_tier": "unknown",
                "intervention_recommendations": ["Manual review recommended due to analysis error"],
            }

    def _update_metrics(self, response_time: int, success: bool):
        """Update performance metrics"""
        self.performance_metrics["requests_processed"] += 1

        if success:
            current_avg = self.performance_metrics["avg_response_time"]
            count = self.performance_metrics["requests_processed"]
            new_avg = ((current_avg * (count - 1)) + response_time) / count
            self.performance_metrics["avg_response_time"] = new_avg
        else:
            self.performance_metrics["errors"] += 1

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return self.performance_metrics.copy()


# Singleton instance for the application
_orchestrator_instance = None


def get_claude_orchestrator() -> ClaudeOrchestrator:
    """Get singleton Claude orchestrator instance"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = ClaudeOrchestrator()
    return _orchestrator_instance
