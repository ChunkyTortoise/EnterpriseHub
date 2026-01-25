"""
Claude Orchestrator - Unified AI Intelligence Layer
Coordinates all Claude AI functionality across chat, scoring, reports, and scripts.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.services.memory_service import MemoryService
from ghl_real_estate_ai.services.sentiment_drift_engine import SentimentDriftEngine
from ghl_real_estate_ai.services.psychographic_segmentation_engine import PsychographicSegmentationEngine
from ghl_real_estate_ai.services.market_context_injector import MarketContextInjector
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
    model: str = "claude-3-5-sonnet-20241022"
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

    def __init__(self,
                 llm_client: Optional[LLMClient] = None,
                 memory_service: Optional[MemoryService] = None):
        # Local imports to avoid circular dependencies
        from ghl_real_estate_ai.services.lead_scorer import LeadScorer
        from ghl_real_estate_ai.services.predictive_lead_scorer import PredictiveLeadScorer
        from ghl_real_estate_ai.services.churn_prediction_engine import ChurnPredictionEngine
        from ghl_real_estate_ai.services.lead_lifecycle import LeadLifecycleTracker
        from ghl_real_estate_ai.services.behavioral_triggers import BehavioralTriggerEngine
        from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher

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
        from ghl_real_estate_ai.core.mcp_servers.domain.lead_intelligence_server import mcp as lead_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.property_intelligence_server import mcp as property_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.market_intelligence_server import mcp as market_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.negotiation_intelligence_server import mcp as negotiation_mcp
        from ghl_real_estate_ai.core.mcp_servers.domain.analytics_intelligence_server import mcp as analytics_mcp

        self.mcp_servers = {
            "LeadIntelligence": lead_mcp,
            "PropertyIntelligence": property_mcp,
            "MarketIntelligence": market_mcp,
            "NegotiationIntelligence": negotiation_mcp,
            "AnalyticsIntelligence": analytics_mcp
        }
        
        # Initialize dependencies for ChurnPredictionEngine
        try:
            self.lifecycle_tracker = LeadLifecycleTracker(location_id="demo_location")
            self.behavioral_engine = BehavioralTriggerEngine()
            
            self.churn_predictor = ChurnPredictionEngine(
                memory_service=self.memory,
                lifecycle_tracker=self.lifecycle_tracker,
                behavioral_engine=self.behavioral_engine,
                lead_scorer=self.jorge_scorer
            )
        except Exception as e:
            print(f"Warning: ChurnPredictionEngine initialization failed in ClaudeOrchestrator: {e}")
            self.churn_predictor = None

        # System prompts for different contexts
        self.system_prompts = self._load_system_prompts()

        # Performance tracking
        self.performance_metrics = {
            "requests_processed": 0,
            "avg_response_time": 0.0,
            "errors": 0
        }

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
            
            Provide clear, data-backed reports with citations where possible."""
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
                    last_tool_names = [
                        m["name"] for m in tool_executions[-1]["content"] 
                        if m.get("type") == "tool_use"
                    ]
                    if last_tool_names:
                        last_category = skill_registry.get_category_for_tool(last_tool_names[-1])
                        if last_category:
                            handoff_prompts = {
                                SkillCategory.DISCOVERY: "\n\n[SPECIALIST HANDOFF] You are now acting as the Market Discovery Specialist. Focus on identifying trends and finding the perfect neighborhood/property matches.",
                                SkillCategory.ANALYSIS: "\n\n[SPECIALIST HANDOFF] You are now acting as the Deep Intelligence Analyst. Synthesize the raw data into strategic lead profiles and risk assessments.",
                                SkillCategory.STRATEGY: "\n\n[SPECIALIST HANDOFF] You are now acting as the Negotiation Strategist. Formulate high-stakes plans to move the deal forward and handle objections.",
                                SkillCategory.ACTION: "\n\n[SPECIALIST HANDOFF] You are now acting as the Sales Execution Specialist. Focus on high-conversion outreach, scripts, and real-time appointment scheduling.",
                                SkillCategory.GOVERNANCE: "\n\n[SPECIALIST HANDOFF] You are now acting as the Platform Auditor. Ensure ROI is tracked and all compliance guardrails are respected."
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
                    tools=tools if tools else None
                )

                # Update messages with assistant response
                assistant_content = []
                if llm_response.content:
                    assistant_content.append({"type": "text", "text": llm_response.content})
                
                if llm_response.tool_calls:
                    for tc in llm_response.tool_calls:
                        assistant_content.append({
                            "type": "tool_use",
                            "id": tc["id"],
                            "name": tc["name"],
                            "input": tc["args"]
                        })

                assistant_message = {"role": "assistant", "content": assistant_content}
                messages.append(assistant_message)
                
                # Log execution step
                tool_executions.append(assistant_message)

                if not llm_response.tool_calls:
                    # No more tools to call, we're done
                    break

                # Execute tool calls and add results to messages
                tool_results_content = []
                for tool_call in llm_response.tool_calls:
                    result_text = await self._execute_tool_call(tool_call)
                    
                    # GHL Sync Logic for ACTION tools
                    tool_name = tool_call["name"]
                    category = skill_registry.get_category_for_tool(tool_name)
                    
                    if category == SkillCategory.ACTION:
                        # Trigger background sync to GHL
                        safe_create_task(self._sync_action_to_ghl(
                            tool_name, 
                            tool_call.get("args", {}), 
                            result_text,
                            request.context.get("contact_id") or request.context.get("lead_id")
                        ))

                    tool_results_content.append({
                        "type": "tool_result",
                        "tool_use_id": tool_call["id"],
                        "content": result_text
                    })
                
                user_tool_message = {
                    "role": "user",
                    "content": tool_results_content
                }
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
                metadata={"error": True, "error_type": type(e).__name__}
            )

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
                    except Exception:
                        # Fallback for complex schemas that Pydantic V2 fails to serialize for JSON Schema
                        parameters = {"type": "object", "properties": {}}
                        
                    tools.append({
                        "name": mcp_tool.name,
                        "description": mcp_tool.description,
                        "parameters": parameters
                    })
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

    async def _sync_action_to_ghl(self, tool_name: str, arguments: Dict[str, Any], result: str, contact_id: Optional[str]) -> None:
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
            "analyze_lead": "qualification_summary"
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
                from ghl_real_estate_ai.services.analytics_service import AnalyticsService
                analytics = AnalyticsService()
                await analytics.track_event(
                    event_type="ghl_sync_success",
                    location_id=tenant_id,
                    contact_id=contact_id,
                    data={"tool": tool_name, "field": field_id}
                )
            except Exception as e:
                print(f"Error syncing {tool_name} to GHL: {e}")

    def _get_complexity_for_task(self, task_type: ClaudeTaskType) -> TaskComplexity:
        """Maps ClaudeTaskType to TaskComplexity for intelligent routing"""
        routine_tasks = [
            ClaudeTaskType.BEHAVIORAL_INSIGHT,
            ClaudeTaskType.LEAD_ANALYSIS,
            ClaudeTaskType.PERSONA_OPTIMIZATION,
            ClaudeTaskType.CHAT_QUERY
        ]
        
        high_stakes_tasks = [
            ClaudeTaskType.INTERVENTION_STRATEGY,
            ClaudeTaskType.REVENUE_PROJECTION,
            ClaudeTaskType.EXECUTIVE_BRIEFING
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
            ClaudeTaskType.SCRIPT_GENERATION: "Simulated SMS: 'Hi! I noticed you were looking at the Zilker listings. I've prepared a custom market update for that area—would you like me to send it over?'"
        }
        
        return ClaudeResponse(
            content=fallbacks.get(task_type, "Simulated intelligence active. System is functioning in offline demo mode."),
            metadata={"demo_mode": True, "reason": "auth_failure"},
            input_tokens=0,
            output_tokens=0,
            model="simulated-model",
            provider="simulated"
        )

    async def chat_query(self,
                        query: str,
                        context: Dict[str, Any],
                        lead_id: Optional[str] = None) -> ClaudeResponse:
        """Handle interactive chat queries with lead context"""

        request = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY,
            context={
                **context,
                "lead_id": lead_id,
                "query_type": "interactive_chat"
            },
            prompt=f"Jorge asks: {query}",
            temperature=0.8,  # Slightly more creative for chat
            use_tools=True
        )

        return await self.process_request(request)

    async def analyze_lead(self,
                          lead_id: str,
                          include_scoring: bool = True,
                          include_churn_analysis: bool = True) -> ClaudeResponse:
        """Comprehensive lead analysis with Claude reasoning"""

        # Gather all available data
        context = await self._gather_lead_context(
            lead_id, include_scoring, include_churn_analysis
        )

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
            max_tokens=6000  # Longer for comprehensive analysis
        )

        return await self.process_request(request)

    async def synthesize_report(self,
                               metrics: Dict[str, Any],
                               report_type: str = "weekly_summary",
                               market_context: Optional[Dict] = None) -> ClaudeResponse:
        """Generate narrative reports from quantitative metrics"""

        context = {
            "metrics": metrics,
            "report_type": report_type,
            "market_context": market_context or {},
            "generated_at": datetime.now().isoformat()
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
            task_type=ClaudeTaskType.REPORT_SYNTHESIS,
            context=context,
            prompt=prompt,
            max_tokens=5000
        )

        return await self.process_request(request)

    async def generate_script(self,
                             lead_id: str,
                             script_type: str,
                             channel: str = "sms",
                             variants: int = 1) -> ClaudeResponse:
        """Generate personalized scripts for lead communication"""

        # Get lead context
        context = await self._gather_lead_context(lead_id)

        # Add script-specific context
        context.update({
            "script_type": script_type,
            "channel": channel,
            "variants_requested": variants
        })

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
            task_type=ClaudeTaskType.SCRIPT_GENERATION,
            context=context,
            prompt=prompt,
            max_tokens=4000
        )

        return await self.process_request(request)

    async def orchestrate_intervention(self,
                                     lead_id: str,
                                     churn_prediction: Dict[str, Any]) -> ClaudeResponse:
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
            task_type=ClaudeTaskType.INTERVENTION_STRATEGY,
            context=context,
            prompt=prompt,
            max_tokens=4000
        )

        return await self.process_request(request)

    async def analyze_conversation_sentiment(self, 
                                          lead_id: str, 
                                          messages: List[Dict[str, str]],
                                          tenant_id: Optional[str] = None) -> Dict[str, Any]:
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
            messages=messages,
            lead_id=lead_id,
            tenant_id=tenant_id
        )

    async def detect_lead_persona(self, 
                                 lead_id: str, 
                                 messages: List[Dict[str, str]],
                                 lead_context: Dict[str, Any],
                                 tenant_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Detect lead persona for tone adaptation.
        """
        return await self.psychographic_engine.detect_persona(
            messages=messages,
            lead_context=lead_context,
            tenant_id=tenant_id
        )

    async def provide_market_reality_check(self, 
                                         expected_price: float, 
                                         address: str, 
                                         zip_code: str,
                                         tenant_id: Optional[str] = None) -> str:
        """
        Provide a market-aware pricing reality check.
        """
        market_context = await self.market_injector.get_market_context(address, zip_code)
        return await self.market_injector.synthesize_price_reality_check(
            seller_expected_price=expected_price,
            market_context=market_context,
            tenant_id=tenant_id
        )

    async def perform_research(self,
                               topic: str,
                               context: Optional[Dict[str, Any]] = None) -> ClaudeResponse:
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
            task_type=ClaudeTaskType.RESEARCH_QUERY,
            context=context or {},
            prompt=prompt,
            max_tokens=4000
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
            ClaudeTaskType.RESEARCH_QUERY: "researcher_assistant"
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
                memory_context = await self.memory.get_context(context["lead_id"])
                enhanced["semantic_memory"] = memory_context.get("relevant_knowledge", "")
                enhanced["conversation_history"] = memory_context.get("conversation_history", [])
                enhanced["extracted_preferences"] = memory_context.get("extracted_preferences", {})
            except Exception:
                # Graceful degradation if memory unavailable
                pass

        return enhanced

    def _build_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Build comprehensive prompt with context"""
        return f"""{base_prompt}

Context:
{json.dumps(context, indent=2, default=str)}

Current Time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
"""

    async def _call_claude(self,
                          system_prompt: str,
                          user_prompt: str,
                          model: str,
                          max_tokens: int,
                          temperature: float,
                          streaming: bool = False,
                          complexity: Optional[TaskComplexity] = None,
                          tenant_id: Optional[str] = None) -> Any:
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
                tenant_id=tenant_id
            ):
                content += chunk
            # Note: streaming doesn't return usage info in current LLMClient implementation
            from ghl_real_estate_ai.core.llm_client import LLMResponse, LLMProvider
            return LLMResponse(content=content, provider=LLMProvider.CLAUDE, model=model)
        else:
            # Standard response using agenerate
            return await self.llm.agenerate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                complexity=complexity,
                tenant_id=tenant_id
            )

    def _parse_response(self, content: str, task_type: ClaudeTaskType) -> ClaudeResponse:
        """Parse and structure Claude response"""
        # Basic parsing - could be enhanced with JSON extraction

        response = ClaudeResponse(content=content)

        # Try to extract structured elements if present
        try:
            # Look for confidence indicators
            if "confidence:" in content.lower():
                # Extract confidence score
                pass

            # Look for recommended actions
            if "recommended actions:" in content.lower() or "next steps:" in content.lower():
                # Extract action items
                pass

            # Task-specific parsing
            if task_type == ClaudeTaskType.SCRIPT_GENERATION:
                # Extract script variants, rationale, etc.
                pass
            elif task_type == ClaudeTaskType.LEAD_ANALYSIS:
                # Extract risk factors, opportunities, etc.
                pass

        except Exception:
            # If parsing fails, return basic response
            pass

        return response

    async def _gather_lead_context(self,
                                  lead_id: str,
                                  include_scoring: bool = True,
                                  include_churn_analysis: bool = True) -> Dict[str, Any]:
        """Gather comprehensive context for a lead"""
        context = {"lead_id": lead_id}

        try:
            # Get memory context
            memory_data = await self.memory.get_context(lead_id)
            context["memory"] = memory_data

            # Get lead scoring if requested
            if include_scoring:
                jorge_result = self.jorge_scorer.calculate_with_reasoning(memory_data)
                # predict_conversion is synchronous in predictive_lead_scorer.py
                ml_result = self.ml_scorer.predict_conversion(memory_data)

                context["scoring"] = {
                    "jorge_score": jorge_result,
                    "ml_score": ml_result
                }

            # Get churn analysis if requested
            if include_churn_analysis:
                # This would need to be implemented based on available data
                # churn_result = await self.churn_predictor.predict_churn_risk(lead_id)
                # context["churn_analysis"] = churn_result
                pass

        except Exception as e:
            context["error"] = f"Error gathering context: {str(e)}"

        return context

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