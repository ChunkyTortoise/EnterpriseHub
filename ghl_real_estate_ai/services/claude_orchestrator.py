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

from core.llm_client import LLMClient, LLMProvider
from services.memory_service import MemoryService


class ClaudeTaskType(Enum):
    CHAT_QUERY = "chat_query"
    LEAD_ANALYSIS = "lead_analysis"
    REPORT_SYNTHESIS = "report_synthesis"
    SCRIPT_GENERATION = "script_generation"
    INTERVENTION_STRATEGY = "intervention_strategy"
    BEHAVIORAL_INSIGHT = "behavioral_insight"


@dataclass
class ClaudeRequest:
    """Standardized request format for all Claude operations"""
    task_type: ClaudeTaskType
    context: Dict[str, Any]
    prompt: str
    model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4000
    temperature: float = 0.7
    system_prompt: Optional[str] = None
    streaming: bool = False


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
        from services.lead_scorer import LeadScorer
        from services.predictive_lead_scorer import PredictiveLeadScorer
        from services.churn_prediction_engine import ChurnPredictionEngine
        from services.lead_lifecycle import LeadLifecycleTracker
        from services.behavioral_triggers import BehavioralTriggerEngine

        # Core services
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.memory = memory_service or MemoryService()

        # Scoring services
        self.jorge_scorer = LeadScorer()
        self.ml_scorer = PredictiveLeadScorer()
        
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
            - A/B testable with variants"""
        }

    async def process_request(self, request: ClaudeRequest) -> ClaudeResponse:
        """
        Main entry point for all Claude operations.
        Handles routing, context injection, and response standardization.
        """
        start_time = time.time()

        try:
            # Get system prompt for task type
            system_prompt = self._get_system_prompt(request.task_type)
            if request.system_prompt:
                system_prompt = request.system_prompt

            # Enhance context with memory if available
            enhanced_context = await self._enhance_context(request.context)

            # Build full prompt
            full_prompt = self._build_prompt(request.prompt, enhanced_context)

            # Make Claude API call
            response_content = await self._call_claude(
                system_prompt=system_prompt,
                user_prompt=full_prompt,
                model=request.model,
                max_tokens=request.max_tokens,
                temperature=request.temperature,
                streaming=request.streaming
            )

            # Parse and structure response
            structured_response = self._parse_response(response_content, request.task_type)

            # Calculate response time
            response_time = int((time.time() - start_time) * 1000)
            structured_response.response_time_ms = response_time

            # Update performance metrics
            self._update_metrics(response_time, success=True)

            return structured_response

        except Exception as e:
            self._update_metrics(0, success=False)
            return ClaudeResponse(
                content=f"Error processing request: {str(e)}",
                metadata={"error": True, "error_type": type(e).__name__}
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
            temperature=0.8  # Slightly more creative for chat
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

    # Private helper methods

    def _get_system_prompt(self, task_type: ClaudeTaskType) -> str:
        """Get appropriate system prompt for task type"""
        prompt_mapping = {
            ClaudeTaskType.CHAT_QUERY: "chat_assistant",
            ClaudeTaskType.LEAD_ANALYSIS: "lead_analyzer",
            ClaudeTaskType.REPORT_SYNTHESIS: "report_synthesizer",
            ClaudeTaskType.SCRIPT_GENERATION: "script_generator",
            ClaudeTaskType.INTERVENTION_STRATEGY: "script_generator",  # Same as script gen
            ClaudeTaskType.BEHAVIORAL_INSIGHT: "lead_analyzer"
        }

        return self.system_prompts.get(
            prompt_mapping.get(task_type, "chat_assistant"),
            self.system_prompts["chat_assistant"]
        )

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
                          streaming: bool = False) -> str:
        """Make actual Claude API call"""

        if streaming:
            # Handle streaming response
            response = await self.llm.stream_chat(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            # Collect streaming response
            content = ""
            async for chunk in response:
                content += chunk
            return content
        else:
            # Standard response
            response = await self.llm.chat(
                messages=[{"role": "user", "content": user_prompt}],
                system=system_prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.content

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
                ml_result = await self.ml_scorer.calculate_score(memory_data)

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