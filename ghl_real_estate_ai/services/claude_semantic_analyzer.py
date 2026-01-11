"""
Claude Semantic Analyzer for Intelligent Lead Analysis

Advanced AI-powered conversation analysis using Claude API to:
- Detect subtle objections and concerns
- Analyze conversation sentiment and flow
- Generate context-aware response suggestions
- Provide real-time agent coaching insights
- Extract qualification information intelligently

Integrates with the Lead Evaluation Orchestrator for enhanced lead analysis.
"""

import asyncio
import json
import logging
import re
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from pydantic import BaseModel, Field

# Local imports
from models.evaluation_models import (
    ObjectionAnalysis,
    RecommendedAction,
    SentimentType,
    ObjectionType,
    ActionPriority,
    EngagementLevel
)

logger = logging.getLogger(__name__)


class AnalysisType(str, Enum):
    """Types of semantic analysis."""
    OBJECTION_DETECTION = "objection_detection"
    SENTIMENT_ANALYSIS = "sentiment_analysis"
    QUALIFICATION_EXTRACTION = "qualification_extraction"
    CONVERSATION_FLOW = "conversation_flow"
    RAPPORT_ASSESSMENT = "rapport_assessment"
    URGENCY_DETECTION = "urgency_detection"
    RESPONSE_SUGGESTION = "response_suggestion"


class ConversationContext(BaseModel):
    """Context for conversation analysis."""
    lead_id: str
    conversation_id: str
    messages: List[Dict[str, Any]]
    agent_info: Optional[Dict[str, Any]] = None
    property_context: Optional[Dict[str, Any]] = None
    lead_background: Optional[Dict[str, Any]] = None


class SemanticAnalysisResult(BaseModel):
    """Result from semantic analysis."""
    analysis_type: AnalysisType
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    findings: Dict[str, Any]
    recommendations: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    processing_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ObjectionDetectionResult(BaseModel):
    """Specific result for objection detection analysis."""
    objections_found: List[ObjectionAnalysis]
    overall_objection_severity: float = Field(..., ge=0.0, le=10.0)
    dominant_objection_type: Optional[ObjectionType] = None
    recommended_responses: List[str] = Field(default_factory=list)
    conversation_risk_level: str = Field(default="low")  # low, medium, high


class QualificationExtractionResult(BaseModel):
    """Result for qualification information extraction."""
    extracted_fields: Dict[str, Any]
    field_confidence_scores: Dict[str, float]
    missing_critical_fields: List[str]
    suggested_questions: List[str] = Field(default_factory=list)
    qualification_progress_pct: float = Field(..., ge=0.0, le=100.0)


class ResponseSuggestionResult(BaseModel):
    """Result for response suggestions."""
    primary_suggestion: str
    alternative_suggestions: List[str] = Field(default_factory=list)
    conversation_strategy: str
    talking_points: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)
    urgency_level: str = Field(default="normal")  # low, normal, high


class ClaudeSemanticAnalyzer:
    """
    Advanced semantic analyzer using Claude API for intelligent conversation analysis.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        max_tokens: int = 4000,
        timeout_seconds: int = 30
    ):
        """
        Initialize Claude semantic analyzer.

        Args:
            api_key: Anthropic API key (falls back to env variable)
            model: Claude model to use
            max_tokens: Maximum tokens for responses
            timeout_seconds: Request timeout
        """
        self.api_key = api_key or self._get_api_key()
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout_seconds

        # HTTP client for API requests
        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds),
            headers={
                "Content-Type": "application/json",
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01"
            }
        )

        # Analysis templates and prompts
        self._init_analysis_templates()

        # Performance tracking
        self.stats = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "average_response_time_ms": 0.0,
            "objections_detected": 0,
            "recommendations_generated": 0
        }

    def _get_api_key(self) -> str:
        """Get API key from environment or raise error."""
        import os
        api_key = os.getenv("ANTHROPIC_API_KEY") or os.getenv("CLAUDE_API_KEY")
        if not api_key:
            raise ValueError("Claude API key not found. Set ANTHROPIC_API_KEY or CLAUDE_API_KEY environment variable.")
        return api_key

    def _init_analysis_templates(self) -> None:
        """Initialize analysis prompt templates."""
        self.templates = {
            "objection_detection": """
You are a real estate conversation analyst. Analyze the following conversation between a real estate agent and a potential buyer to detect any objections, concerns, or hesitations.

Conversation Context:
{context}

Recent Messages:
{messages}

Please identify:
1. Any explicit or implicit objections
2. The type of objection (price, timeline, location, financing, features, market conditions, trust, competition, family decision)
3. The severity level (1-10)
4. Specific text that indicates the objection
5. Recommended response strategies
6. Whether the objection seems resolvable or is a deal-breaker

Provide analysis in JSON format:
{{
    "objections": [
        {{
            "type": "price|timeline|location|financing|features|market_conditions|trust|competition|family_decision|other",
            "severity": 1-10,
            "confidence": 0.0-1.0,
            "text_evidence": "specific quote from conversation",
            "context": "surrounding conversation context",
            "is_resolvable": true/false,
            "recommended_responses": ["response 1", "response 2"],
            "urgency": "low|medium|high"
        }}
    ],
    "overall_risk_level": "low|medium|high",
    "conversation_sentiment": "positive|neutral|concerned|frustrated|angry",
    "recommendations": ["overall recommendation 1", "overall recommendation 2"]
}}
""",

            "qualification_extraction": """
You are a lead qualification specialist. Extract and analyze qualification information from this real estate conversation.

Conversation Context:
{context}

Recent Messages:
{messages}

Extract the following qualification fields with confidence scores:
- Budget/Price range
- Timeline for purchase
- Preferred location/areas
- Property type preferences
- Number of bedrooms/bathrooms
- Square footage requirements
- Financing status/pre-approval
- Current living situation
- Decision-making timeline
- Family/personal circumstances affecting purchase

Provide analysis in JSON format:
{{
    "extracted_fields": {{
        "budget": "value or null",
        "timeline": "value or null",
        "location": "value or null",
        "property_type": "value or null",
        "bedrooms": "value or null",
        "bathrooms": "value or null",
        "square_footage": "value or null",
        "financing_status": "value or null",
        "current_situation": "value or null",
        "decision_timeline": "value or null"
    }},
    "confidence_scores": {{
        "budget": 0.0-1.0,
        "timeline": 0.0-1.0,
        "location": 0.0-1.0,
        "property_type": 0.0-1.0,
        "bedrooms": 0.0-1.0,
        "bathrooms": 0.0-1.0,
        "square_footage": 0.0-1.0,
        "financing_status": 0.0-1.0,
        "current_situation": 0.0-1.0,
        "decision_timeline": 0.0-1.0
    }},
    "missing_critical": ["list of missing critical fields"],
    "qualification_completeness": 0-100,
    "suggested_questions": ["question 1", "question 2", "question 3"],
    "next_priority_field": "field to focus on next"
}}
""",

            "response_suggestion": """
You are an expert real estate sales coach. Based on the conversation context and the buyer's current state, suggest the best response for the agent.

Conversation Context:
{context}

Recent Messages:
{messages}

Current Situation:
- Lead qualification level: {qualification_level}
- Detected objections: {objections}
- Conversation sentiment: {sentiment}
- Engagement level: {engagement}

Provide a response suggestion that:
1. Addresses any objections appropriately
2. Moves the conversation forward
3. Builds rapport and trust
4. Gathers missing qualification information
5. Maintains appropriate urgency without being pushy

Response format:
{{
    "primary_response": "main suggested response",
    "alternative_responses": ["alternative 1", "alternative 2"],
    "strategy_explanation": "why this approach",
    "talking_points": ["key point 1", "key point 2"],
    "follow_up_questions": ["question 1", "question 2"],
    "tone_guidance": "professional|friendly|empathetic|confident|urgent",
    "risk_assessment": "low|medium|high risk response",
    "expected_outcome": "what this response should achieve"
}}
""",

            "sentiment_flow_analysis": """
You are a conversation flow analyst. Analyze the sentiment progression and conversation dynamics in this real estate discussion.

Conversation Context:
{context}

Full Conversation:
{messages}

Analyze:
1. Sentiment progression throughout the conversation
2. Engagement level changes
3. Conversation flow and transitions
4. Rapport building effectiveness
5. Information gathering success rate
6. Potential conversation sticking points
7. Optimal next conversation direction

Provide analysis in JSON format:
{{
    "sentiment_progression": [
        {{"message_index": 1, "sentiment": "positive|neutral|negative", "intensity": 1-5}},
        {{"message_index": 2, "sentiment": "positive|neutral|negative", "intensity": 1-5}}
    ],
    "current_sentiment": "very_positive|positive|neutral|concerned|frustrated|angry",
    "engagement_trend": "increasing|stable|decreasing",
    "rapport_score": 1-10,
    "conversation_effectiveness": 1-10,
    "flow_quality": "smooth|choppy|stalled|natural",
    "recommended_next_direction": "continue_qualification|address_concerns|schedule_showing|provide_value|build_rapport",
    "conversation_risks": ["risk 1", "risk 2"],
    "positive_indicators": ["indicator 1", "indicator 2"]
}}
"""
        }

    async def analyze_conversation(
        self,
        context: ConversationContext,
        analysis_types: List[AnalysisType],
        priority: str = "normal"
    ) -> Dict[AnalysisType, SemanticAnalysisResult]:
        """
        Perform comprehensive conversation analysis.

        Args:
            context: Conversation context and messages
            analysis_types: Types of analysis to perform
            priority: Analysis priority (affects timeout and model)

        Returns:
            Dictionary of analysis results by type
        """
        start_time = time.time()
        results = {}

        try:
            # Prepare conversation data
            conversation_data = self._prepare_conversation_data(context)

            # Run analyses in parallel for efficiency
            if len(analysis_types) > 1:
                tasks = [
                    self._perform_single_analysis(analysis_type, conversation_data, context)
                    for analysis_type in analysis_types
                ]

                analysis_results = await asyncio.gather(*tasks, return_exceptions=True)

                for analysis_type, result in zip(analysis_types, analysis_results):
                    if isinstance(result, Exception):
                        logger.error(f"Analysis {analysis_type} failed: {result}")
                        results[analysis_type] = self._create_error_result(analysis_type, str(result))
                    else:
                        results[analysis_type] = result
            else:
                # Single analysis
                analysis_type = analysis_types[0]
                results[analysis_type] = await self._perform_single_analysis(
                    analysis_type, conversation_data, context
                )

            # Update statistics
            processing_time = int((time.time() - start_time) * 1000)
            self._update_stats(len(analysis_types), processing_time, True)

            logger.info(f"Completed {len(analysis_types)} analyses in {processing_time}ms")

            return results

        except Exception as e:
            self._update_stats(len(analysis_types), int((time.time() - start_time) * 1000), False)
            logger.error(f"Conversation analysis failed: {e}")
            raise

    async def detect_objections(self, context: ConversationContext) -> ObjectionDetectionResult:
        """
        Specialized objection detection with detailed analysis.

        Args:
            context: Conversation context

        Returns:
            Detailed objection detection result
        """
        analysis_result = await self._perform_single_analysis(
            AnalysisType.OBJECTION_DETECTION,
            self._prepare_conversation_data(context),
            context
        )

        # Parse Claude response into structured objection data
        findings = analysis_result.findings
        objections = []

        for obj_data in findings.get("objections", []):
            objection = ObjectionAnalysis(
                objection_type=ObjectionType(obj_data.get("type", "other")),
                raw_text=obj_data.get("text_evidence", ""),
                severity=float(obj_data.get("severity", 5.0)),
                confidence=float(obj_data.get("confidence", 0.5)),
                suggested_responses=obj_data.get("recommended_responses", []),
                talking_points=[],  # Could be expanded
                follow_up_questions=[],  # Could be expanded
                detected_at=datetime.utcnow()
            )
            objections.append(objection)

        # Calculate overall severity
        overall_severity = 0.0
        if objections:
            overall_severity = sum(obj.severity for obj in objections) / len(objections)

        # Determine dominant objection type
        dominant_type = None
        if objections:
            objection_counts = {}
            for obj in objections:
                objection_counts[obj.objection_type] = objection_counts.get(obj.objection_type, 0) + 1
            dominant_type = max(objection_counts, key=objection_counts.get)

        return ObjectionDetectionResult(
            objections_found=objections,
            overall_objection_severity=overall_severity,
            dominant_objection_type=dominant_type,
            recommended_responses=findings.get("recommendations", []),
            conversation_risk_level=findings.get("overall_risk_level", "low")
        )

    async def extract_qualification_info(self, context: ConversationContext) -> QualificationExtractionResult:
        """
        Extract qualification information with confidence scoring.

        Args:
            context: Conversation context

        Returns:
            Qualification extraction result
        """
        analysis_result = await self._perform_single_analysis(
            AnalysisType.QUALIFICATION_EXTRACTION,
            self._prepare_conversation_data(context),
            context
        )

        findings = analysis_result.findings

        return QualificationExtractionResult(
            extracted_fields=findings.get("extracted_fields", {}),
            field_confidence_scores=findings.get("confidence_scores", {}),
            missing_critical_fields=findings.get("missing_critical", []),
            suggested_questions=findings.get("suggested_questions", []),
            qualification_progress_pct=float(findings.get("qualification_completeness", 0.0))
        )

    async def suggest_response(
        self,
        context: ConversationContext,
        qualification_level: str = "developing",
        detected_objections: Optional[List[ObjectionAnalysis]] = None,
        sentiment: str = "neutral",
        engagement: str = "moderate"
    ) -> ResponseSuggestionResult:
        """
        Generate intelligent response suggestions.

        Args:
            context: Conversation context
            qualification_level: Current qualification level
            detected_objections: Any detected objections
            sentiment: Current sentiment
            engagement: Engagement level

        Returns:
            Response suggestion result
        """
        # Prepare enhanced context for response generation
        conversation_data = self._prepare_conversation_data(context)
        conversation_data["qualification_level"] = qualification_level
        conversation_data["objections"] = [obj.dict() for obj in detected_objections] if detected_objections else []
        conversation_data["sentiment"] = sentiment
        conversation_data["engagement"] = engagement

        analysis_result = await self._perform_single_analysis(
            AnalysisType.RESPONSE_SUGGESTION,
            conversation_data,
            context
        )

        findings = analysis_result.findings

        return ResponseSuggestionResult(
            primary_suggestion=findings.get("primary_response", ""),
            alternative_suggestions=findings.get("alternative_responses", []),
            conversation_strategy=findings.get("strategy_explanation", ""),
            talking_points=findings.get("talking_points", []),
            follow_up_questions=findings.get("follow_up_questions", []),
            urgency_level=findings.get("urgency_level", "normal")
        )

    async def analyze_conversation_flow(self, context: ConversationContext) -> Dict[str, Any]:
        """
        Analyze conversation flow and sentiment progression.

        Args:
            context: Conversation context

        Returns:
            Flow analysis results
        """
        analysis_result = await self._perform_single_analysis(
            AnalysisType.CONVERSATION_FLOW,
            self._prepare_conversation_data(context),
            context
        )

        return analysis_result.findings

    # Private helper methods
    async def _perform_single_analysis(
        self,
        analysis_type: AnalysisType,
        conversation_data: Dict[str, Any],
        context: ConversationContext
    ) -> SemanticAnalysisResult:
        """Perform a single type of analysis."""
        start_time = time.time()

        try:
            # Select appropriate template
            if analysis_type == AnalysisType.OBJECTION_DETECTION:
                prompt_template = self.templates["objection_detection"]
            elif analysis_type == AnalysisType.QUALIFICATION_EXTRACTION:
                prompt_template = self.templates["qualification_extraction"]
            elif analysis_type == AnalysisType.RESPONSE_SUGGESTION:
                prompt_template = self.templates["response_suggestion"]
            else:
                prompt_template = self.templates["sentiment_flow_analysis"]

            # Format prompt with conversation data
            prompt = prompt_template.format(**conversation_data)

            # Call Claude API
            response = await self._call_claude_api(prompt)

            # Parse response
            findings = self._parse_claude_response(response)

            processing_time = int((time.time() - start_time) * 1000)

            return SemanticAnalysisResult(
                analysis_type=analysis_type,
                confidence_score=0.85,  # Could be dynamically calculated
                findings=findings,
                recommendations=findings.get("recommendations", []),
                metadata={
                    "model_used": self.model,
                    "tokens_used": len(response.split()),
                    "context_length": len(str(conversation_data))
                },
                processing_time_ms=processing_time
            )

        except Exception as e:
            logger.error(f"Single analysis {analysis_type} failed: {e}")
            raise

    async def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API with the given prompt."""
        try:
            payload = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            }

            response = await self.client.post(
                "https://api.anthropic.com/v1/messages",
                json=payload
            )

            if response.status_code != 200:
                raise Exception(f"API request failed: {response.status_code} - {response.text}")

            result = response.json()
            return result["content"][0]["text"]

        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise

    def _parse_claude_response(self, response: str) -> Dict[str, Any]:
        """Parse Claude's JSON response safely."""
        try:
            # Extract JSON from response (Claude might include explanation text)
            json_start = response.find('{')
            json_end = response.rfind('}') + 1

            if json_start != -1 and json_end > json_start:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return {"raw_response": response, "parsed": False}

        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse Claude response as JSON: {e}")
            return {"raw_response": response, "parse_error": str(e)}

    def _prepare_conversation_data(self, context: ConversationContext) -> Dict[str, Any]:
        """Prepare conversation data for analysis templates."""
        # Format messages for readability
        formatted_messages = []
        for msg in context.messages[-10:]:  # Last 10 messages for context
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted_messages.append(f"[{role.upper()}]: {content}")

        return {
            "context": json.dumps({
                "lead_id": context.lead_id,
                "conversation_id": context.conversation_id,
                "agent_info": context.agent_info or {},
                "property_context": context.property_context or {},
                "lead_background": context.lead_background or {}
            }, indent=2),
            "messages": "\n".join(formatted_messages),
            "message_count": len(context.messages),
            "recent_messages": "\n".join(formatted_messages[-5:])  # Most recent 5
        }

    def _create_error_result(self, analysis_type: AnalysisType, error_message: str) -> SemanticAnalysisResult:
        """Create error result for failed analysis."""
        return SemanticAnalysisResult(
            analysis_type=analysis_type,
            confidence_score=0.0,
            findings={"error": error_message, "success": False},
            recommendations=[],
            metadata={"error": True, "error_message": error_message}
        )

    def _update_stats(self, analysis_count: int, processing_time: int, success: bool) -> None:
        """Update performance statistics."""
        self.stats["total_analyses"] += analysis_count

        if success:
            self.stats["successful_analyses"] += analysis_count
        else:
            self.stats["failed_analyses"] += analysis_count

        # Update average response time
        current_avg = self.stats["average_response_time_ms"]
        total_successful = self.stats["successful_analyses"]

        if total_successful > 0:
            new_avg = ((current_avg * (total_successful - analysis_count)) + processing_time) / total_successful
            self.stats["average_response_time_ms"] = round(new_avg, 2)

    async def close(self) -> None:
        """Close HTTP client and cleanup resources."""
        await self.client.aclose()

    async def get_stats(self) -> Dict[str, Any]:
        """Get analyzer performance statistics."""
        return self.stats.copy()

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check on the analyzer."""
        try:
            # Test API connectivity with a simple request
            test_prompt = "Respond with 'OK' if you can process this request."
            response = await self._call_claude_api(test_prompt)

            return {
                "status": "healthy",
                "api_accessible": True,
                "response_test": "OK" in response,
                "model": self.model,
                "stats": await self.get_stats()
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "api_accessible": False,
                "error": str(e),
                "model": self.model,
                "stats": await self.get_stats()
            }

    # =================== ENHANCED SEMANTIC QUALIFICATION METHODS ===================

    async def analyze_lead_intent(self, conversation_messages: List[Dict]) -> Dict[str, Any]:
        """
        Analyze conversation to determine lead intent and urgency using semantic understanding.

        Args:
            conversation_messages: List of conversation messages with role/content

        Returns:
            Dict with intent analysis results
        """
        try:
            system_prompt = """You are an expert real estate lead qualification specialist. Analyze conversations to determine lead intent and urgency with deep psychological understanding.

Consider:
1. Explicit statements about buying/selling intentions
2. Timeline indicators and urgency clues
3. Engagement level and question quality
4. Budget discussions and financial readiness
5. Decision-making authority and process
6. Behavioral signals and patterns

INTENT CLASSIFICATION:
- researching: Early stage information gathering
- actively_looking: Viewing properties, comparing options
- ready_to_buy: Clear intent with timeline and budget
- ready_to_sell: Wants to list property soon
- just_browsing: Casual interest, no clear intent
- needs_nurturing: Has potential but requires education
- not_qualified: Unlikely to transact in reasonable timeframe

URGENCY LEVELS:
- immediate: Ready to act within days/weeks
- high: Ready to act within 1-3 months
- medium: 3-6 month timeline
- low: 6+ months or no clear timeline
- unknown: Insufficient information

Format response as JSON:
{
    "primary_intent": "intent_type",
    "confidence": 0.0-1.0,
    "urgency_level": "urgency_level",
    "timeline": "estimated timeline string",
    "reasoning": "detailed explanation",
    "supporting_evidence": ["key quote 1", "key quote 2"],
    "behavioral_signals": ["signal 1", "signal 2"],
    "qualification_readiness": 0-100
}"""

            # Format conversation for analysis
            conversation_text = self._format_messages_for_analysis(conversation_messages)

            # Call Claude API
            response = await self._call_claude_api(
                f"{system_prompt}\n\nAnalyze this conversation for lead intent and urgency:\n\n{conversation_text}"
            )

            # Parse and return results
            return self._parse_claude_response(response)

        except Exception as e:
            logger.error(f"Error in intent analysis: {str(e)}")
            return {
                "primary_intent": "unknown",
                "confidence": 0.1,
                "urgency_level": "unknown",
                "timeline": None,
                "reasoning": f"Analysis failed: {str(e)}",
                "supporting_evidence": [],
                "behavioral_signals": [],
                "qualification_readiness": 30
            }

    async def extract_semantic_preferences(self, conversation_messages: List[str]) -> Dict[str, Any]:
        """
        Extract detailed preferences from conversation using semantic understanding.

        Args:
            conversation_messages: List of message texts

        Returns:
            Dict with structured preference profile
        """
        try:
            system_prompt = """You are a master at extracting nuanced real estate preferences from conversations. Use semantic understanding to identify not just explicit preferences, but implied needs, lifestyle factors, and decision criteria.

Extract and analyze:

FINANCIAL PREFERENCES:
- Budget ranges (explicit and implied)
- Financial constraints or flexibility
- Investment vs. personal use considerations

LOCATION INTELLIGENCE:
- Specific areas mentioned
- Commute requirements
- Lifestyle location needs (urban, suburban, rural)
- School district importance
- Neighborhood characteristics valued

PROPERTY CHARACTERISTICS:
- Size requirements (bedrooms, bathrooms, square footage)
- Property type preferences
- Architectural styles or features
- Age preferences (new construction, historic, etc.)

LIFESTYLE FACTORS:
- Family situation impact on needs
- Work-from-home requirements
- Entertainment/hosting needs
- Pet considerations
- Accessibility needs

DECISION PATTERNS:
- What drives their decisions
- Deal breakers vs. nice-to-haves
- Compromise willingness
- Timeline pressures

Be comprehensive but conservative - only extract information that has clear evidence.

Format as JSON:
{
    "budget_analysis": {
        "explicit_range": [min, max] or null,
        "implied_range": [min, max] or null,
        "flexibility_indicators": ["flexible on...", "firm on..."],
        "financial_confidence": 0-100
    },
    "location_profile": {
        "preferred_areas": ["area1", "area2"],
        "commute_requirements": "description",
        "lifestyle_needs": ["urban access", "quiet neighborhood"],
        "school_importance": 0-10,
        "location_flexibility": 0-10
    },
    "property_requirements": {
        "bedrooms": {number} or null,
        "bathrooms": {number} or null,
        "property_type": "type" or null,
        "size_requirements": "description",
        "must_have_features": ["feature1", "feature2"],
        "nice_to_have_features": ["feature1", "feature2"]
    },
    "lifestyle_factors": {
        "family_situation": "description",
        "work_requirements": "description",
        "special_needs": ["need1", "need2"],
        "timeline_drivers": ["driver1", "driver2"]
    },
    "decision_psychology": {
        "primary_motivators": ["motivator1", "motivator2"],
        "deal_breakers": ["breaker1", "breaker2"],
        "compromise_areas": ["area1", "area2"],
        "decision_confidence": 0-100
    },
    "extraction_confidence": 0-100,
    "reasoning": "explanation of analysis"
}"""

            messages_text = "\n".join(conversation_messages[-15:])  # Last 15 messages

            response = await self._call_claude_api(
                f"{system_prompt}\n\nExtract semantic preferences from:\n\n{messages_text}"
            )

            return self._parse_claude_response(response)

        except Exception as e:
            logger.error(f"Error extracting preferences: {str(e)}")
            return {
                "budget_analysis": {"financial_confidence": 0},
                "location_profile": {"location_flexibility": 5},
                "property_requirements": {},
                "lifestyle_factors": {},
                "decision_psychology": {"decision_confidence": 0},
                "extraction_confidence": 10,
                "reasoning": f"Extraction failed: {str(e)}"
            }

    async def assess_semantic_qualification(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive semantic assessment of lead qualification completeness.

        Args:
            lead_data: Complete lead information including conversations, preferences, etc.

        Returns:
            Dict with detailed qualification assessment
        """
        try:
            system_prompt = """You are an expert real estate qualification analyst. Assess lead qualification completeness using both explicit information and semantic understanding of conversations.

Evaluate these qualification dimensions:

FINANCIAL QUALIFICATION (25%):
- Budget clarity and realism
- Financing readiness/pre-approval status
- Income stability indicators
- Financial flexibility signs

TIMELINE QUALIFICATION (20%):
- Urgency and motivation clarity
- Decision timeline reasonableness
- External timeline pressures
- Readiness to act indicators

NEEDS CLARITY (20%):
- Property requirements specificity
- Location preference clarity
- Feature priority understanding
- Must-have vs. nice-to-have distinction

DECISION AUTHORITY (15%):
- Decision-maker identification
- Family/partner alignment
- Authority to commit
- Approval process understanding

MARKET READINESS (10%):
- Market understanding level
- Price expectation realism
- Competition awareness
- Process knowledge

AGENT RAPPORT (10%):
- Trust and communication quality
- Responsiveness level
- Openness to guidance
- Relationship strength

Provide comprehensive assessment with actionable insights.

Format as JSON:
{
    "overall_qualification_score": 0-100,
    "qualification_dimensions": {
        "financial": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]},
        "timeline": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]},
        "needs_clarity": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]},
        "decision_authority": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]},
        "market_readiness": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]},
        "agent_rapport": {"score": 0-100, "strength": "assessment", "gaps": ["gap1"]}
    },
    "critical_missing_info": ["info1", "info2"],
    "strong_qualification_indicators": ["indicator1", "indicator2"],
    "weak_qualification_signals": ["signal1", "signal2"],
    "recommended_next_steps": [
        {"priority": "high", "action": "action description", "expected_outcome": "outcome"}
    ],
    "risk_assessment": {
        "churn_risk": 0-100,
        "time_waste_risk": 0-100,
        "conversion_probability": 0-100
    },
    "strategic_recommendations": {
        "focus_areas": ["area1", "area2"],
        "conversation_strategy": "strategy description",
        "timeline_recommendations": "timeline guidance"
    },
    "assessment_confidence": 0-100,
    "reasoning": "detailed explanation"
}"""

            response = await self._call_claude_api(
                f"{system_prompt}\n\nAssess qualification for this lead:\n\n{json.dumps(lead_data, indent=2)}"
            )

            return self._parse_claude_response(response)

        except Exception as e:
            logger.error(f"Error in qualification assessment: {str(e)}")
            return {
                "overall_qualification_score": 50,
                "qualification_dimensions": {},
                "critical_missing_info": ["Unable to analyze due to error"],
                "assessment_confidence": 10,
                "reasoning": f"Assessment failed: {str(e)}"
            }

    async def generate_intelligent_questions(
        self,
        lead_profile: Dict[str, Any],
        conversation_context: Optional[Dict] = None,
        focus_area: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate intelligent, contextual questions based on semantic analysis.

        Args:
            lead_profile: Complete lead profile information
            conversation_context: Current conversation state and history
            focus_area: Specific area to focus questions on

        Returns:
            List of intelligent question objects
        """
        try:
            system_prompt = """You are a master real estate conversationalist and question strategist. Generate intelligent, contextual questions that feel natural and advance the relationship while gathering essential information.

Consider:
- What critical information is missing for qualification
- The lead's communication style and comfort level
- Current conversation flow and natural transitions
- Psychological readiness for different types of questions
- Most effective timing and sequencing

Question Categories:
- qualification: Essential buying/selling criteria
- discovery: Deeper lifestyle and preference understanding
- validation: Confirming and clarifying previous information
- commitment: Moving toward next steps and decisions
- relationship: Building rapport and trust

Generate 5-7 questions with strategic prioritization.

Format as JSON array:
[
    {
        "question_text": "natural, conversational question",
        "category": "qualification|discovery|validation|commitment|relationship",
        "priority": "critical|high|medium|low",
        "information_target": "specific info this reveals",
        "conversation_timing": "immediate|soon|later|when_appropriate",
        "psychological_readiness": "early|developing|ready|advanced",
        "expected_response_depth": "brief|moderate|detailed",
        "follow_up_opportunities": [
            {"natural_follow_up": "follow-up question", "context": "when to use"}
        ],
        "strategic_value": "why this question matters",
        "conversation_flow_impact": "how this affects conversation",
        "confidence": 0.0-1.0
    }
]"""

            context_text = f"Lead Profile: {json.dumps(lead_profile, indent=2)}"
            if conversation_context:
                context_text += f"\n\nConversation Context: {json.dumps(conversation_context, indent=2)}"
            if focus_area:
                context_text += f"\n\nFocus Area: {focus_area}"

            response = await self._call_claude_api(
                f"{system_prompt}\n\nGenerate intelligent questions for:\n\n{context_text}"
            )

            questions_data = self._parse_claude_response(response)
            return questions_data if isinstance(questions_data, list) else []

        except Exception as e:
            logger.error(f"Error generating questions: {str(e)}")
            return [{
                "question_text": "What's most important to you in finding your next home?",
                "category": "discovery",
                "priority": "high",
                "information_target": "core preferences and motivations",
                "confidence": 0.5,
                "strategic_value": "Establishes foundation for needs understanding"
            }]

    def _format_messages_for_analysis(self, messages: List[Dict]) -> str:
        """Format messages for semantic analysis."""
        formatted = []
        for i, msg in enumerate(messages[-10:], 1):  # Last 10 messages
            role = msg.get("role", "unknown").title()
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted.append(f"Message {i} [{role}]: {content}")
        return "\n".join(formatted)


# Factory function for easy instantiation
def create_claude_analyzer(
    api_key: Optional[str] = None,
    model: str = "claude-3-5-sonnet-20241022"
) -> ClaudeSemanticAnalyzer:
    """
    Factory function to create Claude semantic analyzer.

    Args:
        api_key: Anthropic API key
        model: Claude model to use

    Returns:
        Initialized ClaudeSemanticAnalyzer
    """
    return ClaudeSemanticAnalyzer(api_key=api_key, model=model)


# Usage example:
"""
# Initialize analyzer
analyzer = create_claude_analyzer()

# Prepare conversation context
context = ConversationContext(
    lead_id="lead_123",
    conversation_id="conv_456",
    messages=[
        {"role": "agent", "content": "Hi! What's your budget for a home?"},
        {"role": "prospect", "content": "Well, we're looking but the market is just too expensive right now..."},
        {"role": "agent", "content": "I understand. What price range were you initially considering?"},
        {"role": "prospect", "content": "Maybe around 400k, but everything seems overpriced"}
    ]
)

# Detect objections
objection_result = await analyzer.detect_objections(context)
print(f"Found {len(objection_result.objections_found)} objections")

# Extract qualification info
qual_result = await analyzer.extract_qualification_info(context)
print(f"Qualification progress: {qual_result.qualification_progress_pct}%")

# Get response suggestion
response = await analyzer.suggest_response(context, qualification_level="developing")
print(f"Suggested response: {response.primary_suggestion}")

# Cleanup
await analyzer.close()
"""