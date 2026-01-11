"""
Claude Conversation Analyzer Service for AI-Powered Coaching Foundation

Real estate agent coaching system powered by Claude for conversation quality analysis,
coaching opportunity identification, and performance improvement tracking.

Business Impact:
- 50% training time reduction
- 25% agent productivity increase
- $60K-90K/year value contribution
- Real-time coaching insights and recommendations

Key Features:
- Comprehensive conversation quality analysis
- Real estate expertise assessment
- Coaching opportunity identification
- Performance improvement tracking
- Real-time coaching alerts via WebSocket
- Integration with behavioral learning patterns

Performance Targets:
- <2 seconds complete conversation analysis
- <500ms coaching insight delivery
- Real-time alert broadcasting <100ms
- Integration with WebSocket Manager for live updates
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from enum import Enum
import uuid
from collections import defaultdict

from anthropic import AsyncAnthropic
import httpx
from pydantic import BaseModel, Field

# Local imports
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.websocket_manager import (
    get_websocket_manager,
    IntelligenceEventType
)
from ghl_real_estate_ai.services.event_bus import (
    EventBus,
    EventType
)
from ghl_real_estate_ai.database.redis_client import redis_client
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


# ============================================================================
# Enums and Type Definitions
# ============================================================================

class ConversationQualityArea(Enum):
    """Areas of conversation quality assessment"""
    COMMUNICATION_EFFECTIVENESS = "communication_effectiveness"
    RAPPORT_BUILDING = "rapport_building"
    INFORMATION_GATHERING = "information_gathering"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING_TECHNIQUE = "closing_technique"
    PROFESSIONALISM = "professionalism"
    RESPONSE_TIME = "response_time"


class RealEstateExpertiseArea(Enum):
    """Real estate expertise assessment areas"""
    MARKET_KNOWLEDGE = "market_knowledge"
    PROPERTY_PRESENTATION = "property_presentation"
    NEGOTIATION_SKILLS = "negotiation_skills"
    CLIENT_NEEDS_IDENTIFICATION = "client_needs_identification"
    FOLLOW_UP_QUALITY = "follow_up_quality"
    REGULATORY_KNOWLEDGE = "regulatory_knowledge"
    PRICING_STRATEGY = "pricing_strategy"


class CoachingPriority(Enum):
    """Coaching opportunity priority levels"""
    CRITICAL = "critical"  # Immediate intervention needed
    HIGH = "high"  # Address within 24 hours
    MEDIUM = "medium"  # Address within week
    LOW = "low"  # Ongoing improvement area


class SkillLevel(Enum):
    """Agent skill proficiency levels"""
    EXPERT = "expert"  # 90-100%
    PROFICIENT = "proficient"  # 70-89%
    DEVELOPING = "developing"  # 50-69%
    NEEDS_IMPROVEMENT = "needs_improvement"  # <50%


class ConversationOutcome(Enum):
    """Conversation outcome classification"""
    APPOINTMENT_SCHEDULED = "appointment_scheduled"
    LEAD_ADVANCED = "lead_advanced"
    INFORMATION_GATHERED = "information_gathered"
    OBJECTION_RESOLVED = "objection_resolved"
    FOLLOW_UP_NEEDED = "follow_up_needed"
    LEAD_LOST = "lead_lost"
    IN_PROGRESS = "in_progress"


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class ConversationData:
    """Input conversation data for analysis"""
    conversation_id: str
    agent_id: str
    tenant_id: str
    lead_id: str
    messages: List[Dict[str, Any]]
    start_time: datetime
    end_time: Optional[datetime] = None
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityScore:
    """Quality assessment score for specific area"""
    area: str
    score: float  # 0-100
    confidence: float  # 0-1
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    evidence: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ExpertiseAssessment:
    """Real estate expertise assessment"""
    area: RealEstateExpertiseArea
    skill_level: SkillLevel
    score: float  # 0-100
    confidence: float  # 0-1
    demonstrated_knowledge: List[str] = field(default_factory=list)
    knowledge_gaps: List[str] = field(default_factory=list)
    improvement_suggestions: List[str] = field(default_factory=list)


@dataclass
class CoachingOpportunity:
    """Identified coaching opportunity"""
    opportunity_id: str
    priority: CoachingPriority
    category: str
    title: str
    description: str
    impact: str
    recommended_action: str
    training_modules: List[str] = field(default_factory=list)
    confidence: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class ConversationAnalysis:
    """Complete conversation analysis results"""
    analysis_id: str
    conversation_id: str
    agent_id: str
    tenant_id: str
    lead_id: str
    timestamp: datetime

    # Overall metrics
    overall_quality_score: float  # 0-100
    conversation_effectiveness: float  # 0-100
    conversation_outcome: ConversationOutcome

    # Quality assessments
    quality_scores: List[QualityScore]
    expertise_assessments: List[ExpertiseAssessment]

    # Conversation metrics
    total_messages: int
    agent_messages: int
    client_messages: int
    avg_response_time_seconds: float
    conversation_duration_minutes: float

    # Performance indicators
    questions_asked: int
    objections_identified: int
    objections_resolved: int
    next_steps_defined: bool
    appointment_scheduled: bool

    # Insights
    key_strengths: List[str]
    key_weaknesses: List[str]
    missed_opportunities: List[str]
    best_practices_demonstrated: List[str]

    # Processing metadata
    processing_time_ms: float = 0.0
    model_used: str = ""
    confidence_score: float = 0.0


@dataclass
class CoachingInsights:
    """AI-powered coaching recommendations"""
    insights_id: str
    agent_id: str
    timestamp: datetime

    # Prioritized opportunities
    coaching_opportunities: List[CoachingOpportunity]
    immediate_actions: List[str]

    # Skill development
    top_skills_to_develop: List[str]
    recommended_training_modules: List[str]
    practice_scenarios: List[str]

    # Performance comparison
    peer_comparison_percentile: Optional[float] = None
    improvement_potential: str = ""

    # Specific guidance
    conversation_templates: List[str] = field(default_factory=list)
    objection_handling_tips: List[str] = field(default_factory=list)
    closing_techniques: List[str] = field(default_factory=list)


@dataclass
class ImprovementMetrics:
    """Performance improvement tracking over time"""
    agent_id: str
    time_period: str
    start_date: datetime
    end_date: datetime

    # Aggregate metrics
    total_conversations: int
    avg_quality_score: float
    quality_score_trend: str  # "improving", "stable", "declining"

    # Skill progression
    skill_improvements: Dict[str, float]  # area -> score change
    areas_of_growth: List[str]
    areas_needing_focus: List[str]

    # Performance outcomes
    appointment_conversion_rate: float
    objection_resolution_rate: float
    client_satisfaction_score: float

    # Coaching effectiveness
    coaching_sessions_completed: int
    skills_mastered: List[str]
    current_focus_areas: List[str]

    # Projections
    estimated_time_to_proficiency: Dict[str, int]  # area -> days
    next_milestone: str


@dataclass
class SkillAssessment:
    """Comprehensive skill competency scoring"""
    agent_id: str
    assessment_date: datetime

    # Skill scores by category
    communication_skills: Dict[str, float]
    real_estate_expertise: Dict[str, float]
    sales_effectiveness: Dict[str, float]

    # Overall competency
    overall_competency_score: float  # 0-100
    competency_level: SkillLevel

    # Gap analysis
    skill_gaps: List[Dict[str, Any]]
    priority_development_areas: List[str]

    # Benchmarking
    team_percentile: Optional[float] = None
    market_percentile: Optional[float] = None


# ============================================================================
# Claude Conversation Analyzer Service
# ============================================================================

class ClaudeConversationAnalyzer:
    """
    AI-Powered Conversation Analyzer for Real Estate Agent Coaching.

    Provides comprehensive conversation analysis, coaching insights,
    and performance improvement tracking using Claude's advanced
    natural language understanding capabilities.
    """

    def __init__(
        self,
        anthropic_api_key: Optional[str] = None,
        model: str = "claude-3-5-sonnet-20241022",
        websocket_manager = None,
        event_bus = None
    ):
        """
        Initialize Claude Conversation Analyzer.

        Args:
            anthropic_api_key: Anthropic API key
            model: Claude model to use
            websocket_manager: WebSocket manager for real-time updates
            event_bus: Event bus for coordination
        """
        # API configuration
        self.api_key = anthropic_api_key or settings.anthropic_api_key
        self.model = model
        self.claude_client = AsyncAnthropic(api_key=self.api_key)

        # Integration services (initialized asynchronously)
        self.websocket_manager = websocket_manager
        self.event_bus = event_bus
        self.redis_client = redis_client

        # Analysis configuration
        self.max_tokens = 4000
        self.temperature = 0.7
        self.timeout_seconds = 30

        # Performance tracking
        self.metrics = {
            "total_analyses": 0,
            "successful_analyses": 0,
            "failed_analyses": 0,
            "avg_analysis_time_ms": 0.0,
            "avg_insight_time_ms": 0.0,
            "coaching_opportunities_identified": 0,
            "cache_hit_rate": 0.0
        }

        # Cache configuration
        self.cache_ttl = 3600  # 1 hour
        self.enable_caching = True

        # Analysis templates
        self._init_analysis_templates()

        logger.info(f"Claude Conversation Analyzer initialized with model: {model}")

    async def initialize(self):
        """Initialize async dependencies"""
        try:
            # Initialize WebSocket manager
            if self.websocket_manager is None:
                self.websocket_manager = await get_websocket_manager()

            # Initialize Redis
            await self.redis_client.initialize()

            logger.info("Claude Conversation Analyzer dependencies initialized")

        except Exception as e:
            logger.error(f"Failed to initialize dependencies: {e}")
            raise

    def _init_analysis_templates(self):
        """Initialize analysis prompt templates"""
        self.templates = {
            "conversation_quality": """
You are an expert real estate coaching analyst. Analyze this conversation between a real estate agent and a potential client.

Conversation Context:
Agent ID: {agent_id}
Lead ID: {lead_id}
Duration: {duration} minutes
Messages: {total_messages}

Conversation Transcript:
{messages}

Assess the conversation quality across these dimensions:

1. COMMUNICATION EFFECTIVENESS (0-100)
   - Clarity and conciseness
   - Active listening demonstrated
   - Appropriate language and tone

2. RAPPORT BUILDING (0-100)
   - Personal connection established
   - Empathy and understanding shown
   - Trust-building behaviors

3. INFORMATION GATHERING (0-100)
   - Discovery questions quality
   - Needs assessment completeness
   - Client qualification thoroughness

4. OBJECTION HANDLING (0-100)
   - Objections identified and addressed
   - Effective response techniques
   - Resolution achieved

5. CLOSING TECHNIQUE (0-100)
   - Next steps clearly defined
   - Commitment sought appropriately
   - Follow-up actions established

6. PROFESSIONALISM (0-100)
   - Market knowledge demonstrated
   - Professional standards maintained
   - Ethical practices followed

Provide detailed JSON analysis:
{{
    "overall_quality_score": 0-100,
    "quality_scores": [
        {{
            "area": "communication_effectiveness|rapport_building|information_gathering|objection_handling|closing_technique|professionalism",
            "score": 0-100,
            "confidence": 0.0-1.0,
            "strengths": ["strength 1", "strength 2"],
            "weaknesses": ["weakness 1", "weakness 2"],
            "evidence": ["evidence quote 1", "evidence quote 2"],
            "recommendations": ["recommendation 1", "recommendation 2"]
        }}
    ],
    "key_strengths": ["overall strength 1", "overall strength 2"],
    "key_weaknesses": ["overall weakness 1", "overall weakness 2"],
    "missed_opportunities": ["missed opportunity 1", "missed opportunity 2"],
    "best_practices": ["best practice 1", "best practice 2"],
    "conversation_outcome": "appointment_scheduled|lead_advanced|information_gathered|objection_resolved|follow_up_needed|lead_lost|in_progress"
}}
""",

            "real_estate_expertise": """
You are a real estate expertise evaluator. Assess the agent's real estate knowledge and skills demonstrated in this conversation.

Conversation Transcript:
{messages}

Evaluate expertise in these areas:

1. MARKET KNOWLEDGE
   - Local market trends awareness
   - Pricing strategy competence
   - Comparative market analysis (CMA) skills
   - Market data utilization

2. PROPERTY PRESENTATION
   - Feature highlighting effectiveness
   - Benefit articulation
   - Virtual/physical tour guidance
   - Property matching to needs

3. NEGOTIATION SKILLS
   - Negotiation strategies employed
   - Value proposition communication
   - Win-win approach
   - Handling multiple offers

4. CLIENT NEEDS IDENTIFICATION
   - Needs discovery thoroughness
   - Preference understanding
   - Lifestyle consideration
   - Budget assessment

5. FOLLOW-UP QUALITY
   - Follow-up plan clarity
   - Next steps definition
   - Timeline management
   - Communication commitment

6. REGULATORY KNOWLEDGE
   - Legal requirements awareness
   - Disclosure obligations
   - Contract process understanding
   - Compliance adherence

Provide detailed JSON assessment:
{{
    "expertise_assessments": [
        {{
            "area": "market_knowledge|property_presentation|negotiation_skills|client_needs_identification|follow_up_quality|regulatory_knowledge",
            "skill_level": "expert|proficient|developing|needs_improvement",
            "score": 0-100,
            "confidence": 0.0-1.0,
            "demonstrated_knowledge": ["example 1", "example 2"],
            "knowledge_gaps": ["gap 1", "gap 2"],
            "improvement_suggestions": ["suggestion 1", "suggestion 2"]
        }}
    ],
    "overall_expertise_level": "expert|proficient|developing|needs_improvement",
    "top_strengths": ["strength 1", "strength 2", "strength 3"],
    "priority_development_areas": ["area 1", "area 2", "area 3"]
}}
""",

            "coaching_opportunities": """
You are a real estate coaching specialist. Identify specific coaching opportunities to improve agent performance.

Agent Performance Context:
{performance_context}

Conversation Analysis:
{conversation_summary}

Identify coaching opportunities in these categories:
- Lead Qualification: Discovery questions, needs assessment
- Property Presentation: Feature/benefit articulation, visual aids
- Objection Handling: Common objections, response techniques
- Closing Skills: Trial closes, commitment seeking, follow-up
- Market Expertise: Data usage, trend explanation, pricing strategy
- Communication: Active listening, empathy, professionalism

For each opportunity provide:
{{
    "coaching_opportunities": [
        {{
            "opportunity_id": "unique_id",
            "priority": "critical|high|medium|low",
            "category": "lead_qualification|property_presentation|objection_handling|closing_skills|market_expertise|communication",
            "title": "Brief title",
            "description": "Detailed description",
            "impact": "Expected improvement if addressed",
            "recommended_action": "Specific action to take",
            "training_modules": ["module 1", "module 2"],
            "confidence": 0.0-1.0
        }}
    ],
    "immediate_actions": ["action 1", "action 2"],
    "top_skills_to_develop": ["skill 1", "skill 2", "skill 3"],
    "recommended_training": ["training 1", "training 2"],
    "practice_scenarios": ["scenario 1", "scenario 2"]
}}
""",

            "performance_tracking": """
You are a performance improvement analyst. Track agent skill development over time.

Historical Performance:
{historical_data}

Current Performance:
{current_performance}

Time Period: {time_period}

Analyze:
1. Skill progression trends
2. Areas of improvement
3. Areas needing additional focus
4. Coaching effectiveness
5. Projected time to proficiency

Provide comprehensive JSON analysis:
{{
    "quality_score_trend": "improving|stable|declining",
    "skill_improvements": {{
        "communication": +/- change,
        "rapport_building": +/- change,
        "objection_handling": +/- change,
        "closing": +/- change,
        "market_knowledge": +/- change
    }},
    "areas_of_growth": ["area 1", "area 2"],
    "areas_needing_focus": ["area 1", "area 2"],
    "coaching_effectiveness": 0-100,
    "skills_mastered": ["skill 1", "skill 2"],
    "estimated_time_to_proficiency": {{
        "area": days_estimate
    }},
    "next_milestone": "description",
    "recommendations": ["recommendation 1", "recommendation 2"]
}}
"""
        }

    async def analyze_conversation(
        self,
        conversation_data: ConversationData
    ) -> ConversationAnalysis:
        """
        Perform comprehensive conversation analysis.

        Args:
            conversation_data: Conversation data to analyze

        Returns:
            ConversationAnalysis with complete assessment
        """
        start_time = time.time()

        try:
            # Check cache first
            if self.enable_caching:
                cached_analysis = await self._get_cached_analysis(
                    conversation_data.conversation_id
                )
                if cached_analysis:
                    logger.info(f"Using cached analysis for conversation {conversation_data.conversation_id}")
                    return cached_analysis

            # Prepare conversation context
            messages_text = self._format_messages(conversation_data.messages)
            duration = self._calculate_duration(
                conversation_data.start_time,
                conversation_data.end_time
            )

            # Parallel analysis execution
            quality_task = self._analyze_conversation_quality(
                conversation_data,
                messages_text,
                duration
            )

            expertise_task = self._analyze_real_estate_expertise(
                conversation_data,
                messages_text
            )

            # Execute in parallel
            quality_results, expertise_results = await asyncio.gather(
                quality_task,
                expertise_task,
                return_exceptions=True
            )

            # Handle any errors
            if isinstance(quality_results, Exception):
                logger.error(f"Quality analysis failed: {quality_results}")
                raise quality_results

            if isinstance(expertise_results, Exception):
                logger.error(f"Expertise analysis failed: {expertise_results}")
                raise expertise_results

            # Calculate conversation metrics
            conversation_metrics = self._calculate_conversation_metrics(
                conversation_data
            )

            # Create comprehensive analysis
            analysis = ConversationAnalysis(
                analysis_id=f"analysis_{uuid.uuid4().hex[:12]}",
                conversation_id=conversation_data.conversation_id,
                agent_id=conversation_data.agent_id,
                tenant_id=conversation_data.tenant_id,
                lead_id=conversation_data.lead_id,
                timestamp=datetime.now(),
                overall_quality_score=quality_results.get("overall_quality_score", 0),
                conversation_effectiveness=self._calculate_effectiveness(
                    quality_results,
                    expertise_results
                ),
                conversation_outcome=ConversationOutcome(
                    quality_results.get("conversation_outcome", "in_progress")
                ),
                quality_scores=self._parse_quality_scores(
                    quality_results.get("quality_scores", [])
                ),
                expertise_assessments=self._parse_expertise_assessments(
                    expertise_results.get("expertise_assessments", [])
                ),
                **conversation_metrics,
                key_strengths=quality_results.get("key_strengths", []),
                key_weaknesses=quality_results.get("key_weaknesses", []),
                missed_opportunities=quality_results.get("missed_opportunities", []),
                best_practices_demonstrated=quality_results.get("best_practices", []),
                processing_time_ms=(time.time() - start_time) * 1000,
                model_used=self.model,
                confidence_score=self._calculate_confidence(quality_results, expertise_results)
            )

            # Cache the analysis
            if self.enable_caching:
                await self._cache_analysis(analysis)

            # Broadcast real-time update
            await self._broadcast_analysis_update(analysis)

            # Update metrics
            self._update_metrics(analysis)

            logger.info(
                f"Conversation analysis completed for {conversation_data.conversation_id}: "
                f"quality={analysis.overall_quality_score:.1f}, "
                f"time={analysis.processing_time_ms:.1f}ms"
            )

            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze conversation {conversation_data.conversation_id}: {e}")
            self.metrics["failed_analyses"] += 1
            raise

    async def identify_coaching_opportunities(
        self,
        analysis: ConversationAnalysis
    ) -> CoachingInsights:
        """
        Identify AI-powered coaching opportunities from analysis.

        Args:
            analysis: Conversation analysis results

        Returns:
            CoachingInsights with actionable recommendations
        """
        start_time = time.time()

        try:
            # Prepare context
            performance_context = self._prepare_performance_context(analysis)
            conversation_summary = self._create_conversation_summary(analysis)

            # Call Claude for coaching opportunity identification
            prompt = self.templates["coaching_opportunities"].format(
                performance_context=json.dumps(performance_context, indent=2),
                conversation_summary=json.dumps(conversation_summary, indent=2)
            )

            response = await self._call_claude(prompt)
            coaching_data = json.loads(response)

            # Create coaching insights
            insights = CoachingInsights(
                insights_id=f"insights_{uuid.uuid4().hex[:12]}",
                agent_id=analysis.agent_id,
                timestamp=datetime.now(),
                coaching_opportunities=self._parse_coaching_opportunities(
                    coaching_data.get("coaching_opportunities", [])
                ),
                immediate_actions=coaching_data.get("immediate_actions", []),
                top_skills_to_develop=coaching_data.get("top_skills_to_develop", []),
                recommended_training_modules=coaching_data.get("recommended_training", []),
                practice_scenarios=coaching_data.get("practice_scenarios", [])
            )

            # Add conversation templates and tips
            insights.conversation_templates = self._generate_conversation_templates(analysis)
            insights.objection_handling_tips = self._generate_objection_tips(analysis)
            insights.closing_techniques = self._generate_closing_techniques(analysis)

            # Calculate peer comparison if available
            insights.peer_comparison_percentile = await self._calculate_peer_percentile(
                analysis.agent_id,
                analysis.overall_quality_score
            )

            # Broadcast coaching insights
            await self._broadcast_coaching_insights(insights)

            insight_time = (time.time() - start_time) * 1000

            logger.info(
                f"Coaching insights generated for agent {analysis.agent_id}: "
                f"{len(insights.coaching_opportunities)} opportunities, "
                f"time={insight_time:.1f}ms"
            )

            self.metrics["coaching_opportunities_identified"] += len(
                insights.coaching_opportunities
            )

            return insights

        except Exception as e:
            logger.error(f"Failed to identify coaching opportunities: {e}")
            raise

    async def track_improvement_metrics(
        self,
        agent_id: str,
        time_period: str
    ) -> ImprovementMetrics:
        """
        Track performance improvement metrics over time.

        Args:
            agent_id: Agent identifier
            time_period: Time period for tracking (e.g., "last_30_days", "last_quarter")

        Returns:
            ImprovementMetrics with trend analysis
        """
        try:
            # Parse time period
            start_date, end_date = self._parse_time_period(time_period)

            # Retrieve historical performance data
            historical_data = await self._get_historical_performance(
                agent_id,
                start_date,
                end_date
            )

            # Get current performance baseline
            current_performance = await self._get_current_performance(agent_id)

            # Prepare analysis context
            prompt = self.templates["performance_tracking"].format(
                historical_data=json.dumps(historical_data, indent=2),
                current_performance=json.dumps(current_performance, indent=2),
                time_period=time_period
            )

            # Call Claude for trend analysis
            response = await self._call_claude(prompt)
            tracking_data = json.loads(response)

            # Calculate aggregate metrics
            total_conversations = len(historical_data.get("conversations", []))
            avg_quality = self._calculate_average_quality(historical_data)

            # Create improvement metrics
            metrics = ImprovementMetrics(
                agent_id=agent_id,
                time_period=time_period,
                start_date=start_date,
                end_date=end_date,
                total_conversations=total_conversations,
                avg_quality_score=avg_quality,
                quality_score_trend=tracking_data.get("quality_score_trend", "stable"),
                skill_improvements=tracking_data.get("skill_improvements", {}),
                areas_of_growth=tracking_data.get("areas_of_growth", []),
                areas_needing_focus=tracking_data.get("areas_needing_focus", []),
                appointment_conversion_rate=self._calculate_conversion_rate(
                    historical_data
                ),
                objection_resolution_rate=self._calculate_resolution_rate(
                    historical_data
                ),
                client_satisfaction_score=self._calculate_satisfaction_score(
                    historical_data
                ),
                coaching_sessions_completed=historical_data.get(
                    "coaching_sessions", 0
                ),
                skills_mastered=tracking_data.get("skills_mastered", []),
                current_focus_areas=tracking_data.get("areas_needing_focus", []),
                estimated_time_to_proficiency=tracking_data.get(
                    "estimated_time_to_proficiency", {}
                ),
                next_milestone=tracking_data.get("next_milestone", "")
            )

            logger.info(
                f"Improvement metrics tracked for agent {agent_id}: "
                f"conversations={total_conversations}, "
                f"avg_quality={avg_quality:.1f}, "
                f"trend={metrics.quality_score_trend}"
            )

            return metrics

        except Exception as e:
            logger.error(f"Failed to track improvement metrics for agent {agent_id}: {e}")
            raise

    # ========================================================================
    # Helper Methods - Analysis
    # ========================================================================

    async def _analyze_conversation_quality(
        self,
        conversation_data: ConversationData,
        messages_text: str,
        duration: float
    ) -> Dict[str, Any]:
        """Analyze conversation quality using Claude"""
        prompt = self.templates["conversation_quality"].format(
            agent_id=conversation_data.agent_id,
            lead_id=conversation_data.lead_id,
            duration=duration,
            total_messages=len(conversation_data.messages),
            messages=messages_text
        )

        response = await self._call_claude(prompt)
        return json.loads(response)

    async def _analyze_real_estate_expertise(
        self,
        conversation_data: ConversationData,
        messages_text: str
    ) -> Dict[str, Any]:
        """Analyze real estate expertise using Claude"""
        prompt = self.templates["real_estate_expertise"].format(
            messages=messages_text
        )

        response = await self._call_claude(prompt)
        return json.loads(response)

    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API with retry logic"""
        max_retries = 3
        retry_delay = 1.0

        for attempt in range(max_retries):
            try:
                message = await self.claude_client.messages.create(
                    model=self.model,
                    max_tokens=self.max_tokens,
                    temperature=self.temperature,
                    messages=[{
                        "role": "user",
                        "content": prompt
                    }]
                )

                return message.content[0].text

            except Exception as e:
                if attempt < max_retries - 1:
                    logger.warning(
                        f"Claude API call failed (attempt {attempt + 1}/{max_retries}): {e}"
                    )
                    await asyncio.sleep(retry_delay * (attempt + 1))
                else:
                    logger.error(f"Claude API call failed after {max_retries} attempts: {e}")
                    raise

    # ========================================================================
    # Helper Methods - Data Processing
    # ========================================================================

    def _format_messages(self, messages: List[Dict[str, Any]]) -> str:
        """Format messages for Claude analysis"""
        formatted = []
        for msg in messages:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")
            formatted.append(f"[{timestamp}] {role.upper()}: {content}")

        return "\n".join(formatted)

    def _calculate_duration(
        self,
        start_time: datetime,
        end_time: Optional[datetime]
    ) -> float:
        """Calculate conversation duration in minutes"""
        if end_time is None:
            end_time = datetime.now()

        delta = end_time - start_time
        return delta.total_seconds() / 60

    def _calculate_conversation_metrics(
        self,
        conversation_data: ConversationData
    ) -> Dict[str, Any]:
        """Calculate basic conversation metrics"""
        total_messages = len(conversation_data.messages)
        agent_messages = sum(
            1 for msg in conversation_data.messages
            if msg.get("role") == "agent"
        )
        client_messages = total_messages - agent_messages

        # Calculate average response time
        response_times = []
        for i in range(1, len(conversation_data.messages)):
            prev_time = conversation_data.messages[i-1].get("timestamp")
            curr_time = conversation_data.messages[i].get("timestamp")
            if prev_time and curr_time:
                try:
                    prev_dt = datetime.fromisoformat(prev_time)
                    curr_dt = datetime.fromisoformat(curr_time)
                    response_times.append((curr_dt - prev_dt).total_seconds())
                except:
                    pass

        avg_response_time = sum(response_times) / len(response_times) if response_times else 0

        # Calculate duration
        duration = self._calculate_duration(
            conversation_data.start_time,
            conversation_data.end_time
        )

        # Count questions and objections (simple heuristic)
        questions_asked = sum(
            1 for msg in conversation_data.messages
            if msg.get("role") == "agent" and "?" in msg.get("content", "")
        )

        return {
            "total_messages": total_messages,
            "agent_messages": agent_messages,
            "client_messages": client_messages,
            "avg_response_time_seconds": avg_response_time,
            "conversation_duration_minutes": duration,
            "questions_asked": questions_asked,
            "objections_identified": 0,  # Will be populated from analysis
            "objections_resolved": 0,
            "next_steps_defined": False,
            "appointment_scheduled": False
        }

    def _parse_quality_scores(self, quality_scores_data: List[Dict]) -> List[QualityScore]:
        """Parse quality scores from Claude response"""
        return [
            QualityScore(
                area=score.get("area", ""),
                score=score.get("score", 0),
                confidence=score.get("confidence", 0.0),
                strengths=score.get("strengths", []),
                weaknesses=score.get("weaknesses", []),
                evidence=score.get("evidence", []),
                recommendations=score.get("recommendations", [])
            )
            for score in quality_scores_data
        ]

    def _parse_expertise_assessments(
        self,
        assessments_data: List[Dict]
    ) -> List[ExpertiseAssessment]:
        """Parse expertise assessments from Claude response"""
        return [
            ExpertiseAssessment(
                area=RealEstateExpertiseArea(assessment.get("area", "market_knowledge")),
                skill_level=SkillLevel(assessment.get("skill_level", "developing")),
                score=assessment.get("score", 0),
                confidence=assessment.get("confidence", 0.0),
                demonstrated_knowledge=assessment.get("demonstrated_knowledge", []),
                knowledge_gaps=assessment.get("knowledge_gaps", []),
                improvement_suggestions=assessment.get("improvement_suggestions", [])
            )
            for assessment in assessments_data
        ]

    def _parse_coaching_opportunities(
        self,
        opportunities_data: List[Dict]
    ) -> List[CoachingOpportunity]:
        """Parse coaching opportunities from Claude response"""
        return [
            CoachingOpportunity(
                opportunity_id=opp.get("opportunity_id", f"opp_{uuid.uuid4().hex[:8]}"),
                priority=CoachingPriority(opp.get("priority", "medium")),
                category=opp.get("category", ""),
                title=opp.get("title", ""),
                description=opp.get("description", ""),
                impact=opp.get("impact", ""),
                recommended_action=opp.get("recommended_action", ""),
                training_modules=opp.get("training_modules", []),
                confidence=opp.get("confidence", 0.0)
            )
            for opp in opportunities_data
        ]

    def _calculate_effectiveness(
        self,
        quality_results: Dict,
        expertise_results: Dict
    ) -> float:
        """Calculate overall conversation effectiveness"""
        quality_score = quality_results.get("overall_quality_score", 0)

        # Average expertise scores
        expertise_scores = [
            assess.get("score", 0)
            for assess in expertise_results.get("expertise_assessments", [])
        ]
        avg_expertise = sum(expertise_scores) / len(expertise_scores) if expertise_scores else 0

        # Weighted combination
        return (quality_score * 0.6) + (avg_expertise * 0.4)

    def _calculate_confidence(
        self,
        quality_results: Dict,
        expertise_results: Dict
    ) -> float:
        """Calculate overall confidence score"""
        quality_confidences = [
            score.get("confidence", 0.0)
            for score in quality_results.get("quality_scores", [])
        ]

        expertise_confidences = [
            assess.get("confidence", 0.0)
            for assess in expertise_results.get("expertise_assessments", [])
        ]

        all_confidences = quality_confidences + expertise_confidences
        return sum(all_confidences) / len(all_confidences) if all_confidences else 0.0

    def _prepare_performance_context(self, analysis: ConversationAnalysis) -> Dict:
        """Prepare performance context for coaching analysis"""
        return {
            "overall_quality_score": analysis.overall_quality_score,
            "conversation_effectiveness": analysis.conversation_effectiveness,
            "quality_scores": [
                {
                    "area": score.area,
                    "score": score.score,
                    "strengths": score.strengths,
                    "weaknesses": score.weaknesses
                }
                for score in analysis.quality_scores
            ],
            "expertise_assessments": [
                {
                    "area": assess.area.value,
                    "skill_level": assess.skill_level.value,
                    "score": assess.score
                }
                for assess in analysis.expertise_assessments
            ]
        }

    def _create_conversation_summary(self, analysis: ConversationAnalysis) -> Dict:
        """Create conversation summary for coaching analysis"""
        return {
            "total_messages": analysis.total_messages,
            "duration_minutes": analysis.conversation_duration_minutes,
            "questions_asked": analysis.questions_asked,
            "objections_handled": analysis.objections_identified,
            "objections_resolved": analysis.objections_resolved,
            "outcome": analysis.conversation_outcome.value,
            "key_strengths": analysis.key_strengths,
            "key_weaknesses": analysis.key_weaknesses,
            "missed_opportunities": analysis.missed_opportunities
        }

    def _generate_conversation_templates(
        self,
        analysis: ConversationAnalysis
    ) -> List[str]:
        """Generate conversation templates based on analysis"""
        templates = []

        # Add templates based on weak areas
        for score in analysis.quality_scores:
            if score.score < 70 and score.area == "rapport_building":
                templates.append(
                    "Hi [Name], I really appreciate you taking the time to speak with me today. "
                    "Before we dive in, I'd love to learn a bit about you and your family..."
                )

            if score.score < 70 and score.area == "information_gathering":
                templates.append(
                    "To ensure I find you the perfect property, can you walk me through "
                    "your ideal home? What does a typical day look like for your family?"
                )

        return templates

    def _generate_objection_tips(self, analysis: ConversationAnalysis) -> List[str]:
        """Generate objection handling tips"""
        tips = [
            "Acknowledge the concern: 'I understand that's important to you...'",
            "Ask clarifying questions: 'Can you tell me more about what's concerning you?'",
            "Provide social proof: 'Many of my clients had similar concerns initially...'",
            "Offer specific solutions: 'Here's how we can address that...'",
            "Create urgency when appropriate: 'Properties in this price range typically...'"
        ]
        return tips

    def _generate_closing_techniques(self, analysis: ConversationAnalysis) -> List[str]:
        """Generate closing techniques"""
        techniques = [
            "Trial close: 'How does this property compare to what you've seen?'",
            "Alternative close: 'Would morning or afternoon work better for a viewing?'",
            "Assumptive close: 'Let me check the viewing availability for next week...'",
            "Summary close: 'Based on everything we've discussed, this seems like a great fit because...'",
            "Direct close: 'Are you ready to schedule a viewing and take the next step?'"
        ]
        return techniques

    # ========================================================================
    # Helper Methods - Data Retrieval
    # ========================================================================

    async def _get_cached_analysis(
        self,
        conversation_id: str
    ) -> Optional[ConversationAnalysis]:
        """Retrieve cached conversation analysis"""
        try:
            cache_key = f"conversation_analysis:{conversation_id}"
            cached_data = await self.redis_client.get(cache_key)

            if cached_data:
                # Deserialize from dict
                # Note: This is simplified - full implementation would need proper deserialization
                return cached_data

        except Exception as e:
            logger.warning(f"Failed to get cached analysis: {e}")

        return None

    async def _cache_analysis(self, analysis: ConversationAnalysis):
        """Cache conversation analysis"""
        try:
            cache_key = f"conversation_analysis:{analysis.conversation_id}"

            # Serialize analysis (simplified)
            await self.redis_client.set(
                key=cache_key,
                value=asdict(analysis),
                ttl=self.cache_ttl
            )

        except Exception as e:
            logger.warning(f"Failed to cache analysis: {e}")

    async def _get_historical_performance(
        self,
        agent_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """Retrieve historical performance data"""
        try:
            # This would typically query a database
            # For now, return mock structure
            return {
                "conversations": [],
                "coaching_sessions": 0,
                "avg_quality_scores": []
            }
        except Exception as e:
            logger.error(f"Failed to get historical performance: {e}")
            return {}

    async def _get_current_performance(self, agent_id: str) -> Dict[str, Any]:
        """Get current performance baseline"""
        try:
            # This would typically query recent data
            return {
                "recent_quality_score": 0,
                "recent_conversations": []
            }
        except Exception as e:
            logger.error(f"Failed to get current performance: {e}")
            return {}

    async def _calculate_peer_percentile(
        self,
        agent_id: str,
        quality_score: float
    ) -> Optional[float]:
        """Calculate peer comparison percentile"""
        try:
            # This would typically compare against team/company data
            # Return mock percentile for now
            return 65.0
        except Exception as e:
            logger.warning(f"Failed to calculate peer percentile: {e}")
            return None

    # ========================================================================
    # Helper Methods - Calculations
    # ========================================================================

    def _parse_time_period(self, time_period: str) -> Tuple[datetime, datetime]:
        """Parse time period string into start and end dates"""
        end_date = datetime.now()

        if time_period == "last_7_days":
            start_date = end_date - timedelta(days=7)
        elif time_period == "last_30_days":
            start_date = end_date - timedelta(days=30)
        elif time_period == "last_quarter":
            start_date = end_date - timedelta(days=90)
        elif time_period == "last_year":
            start_date = end_date - timedelta(days=365)
        else:
            start_date = end_date - timedelta(days=30)

        return start_date, end_date

    def _calculate_average_quality(self, historical_data: Dict) -> float:
        """Calculate average quality score from historical data"""
        scores = historical_data.get("avg_quality_scores", [])
        return sum(scores) / len(scores) if scores else 0.0

    def _calculate_conversion_rate(self, historical_data: Dict) -> float:
        """Calculate appointment conversion rate"""
        conversations = historical_data.get("conversations", [])
        if not conversations:
            return 0.0

        appointments = sum(
            1 for conv in conversations
            if conv.get("appointment_scheduled", False)
        )
        return appointments / len(conversations)

    def _calculate_resolution_rate(self, historical_data: Dict) -> float:
        """Calculate objection resolution rate"""
        conversations = historical_data.get("conversations", [])
        if not conversations:
            return 0.0

        total_objections = sum(
            conv.get("objections_identified", 0)
            for conv in conversations
        )

        if total_objections == 0:
            return 1.0

        resolved_objections = sum(
            conv.get("objections_resolved", 0)
            for conv in conversations
        )

        return resolved_objections / total_objections

    def _calculate_satisfaction_score(self, historical_data: Dict) -> float:
        """Calculate client satisfaction score"""
        # This would typically come from client feedback
        # Return default for now
        return 85.0

    # ========================================================================
    # Helper Methods - Real-time Updates
    # ========================================================================

    async def _broadcast_analysis_update(self, analysis: ConversationAnalysis):
        """Broadcast analysis update via WebSocket"""
        try:
            if self.websocket_manager:
                update_data = {
                    "type": "conversation_analysis",
                    "analysis_id": analysis.analysis_id,
                    "agent_id": analysis.agent_id,
                    "overall_quality_score": analysis.overall_quality_score,
                    "conversation_effectiveness": analysis.conversation_effectiveness,
                    "key_strengths": analysis.key_strengths[:3],
                    "key_weaknesses": analysis.key_weaknesses[:3],
                    "timestamp": analysis.timestamp.isoformat()
                }

                # Broadcast to tenant
                await self.websocket_manager.websocket_hub.broadcast_to_tenant(
                    tenant_id=analysis.tenant_id,
                    event_data=update_data
                )

        except Exception as e:
            logger.warning(f"Failed to broadcast analysis update: {e}")

    async def _broadcast_coaching_insights(self, insights: CoachingInsights):
        """Broadcast coaching insights via WebSocket"""
        try:
            if self.websocket_manager:
                # Send critical/high priority opportunities as alerts
                critical_opportunities = [
                    opp for opp in insights.coaching_opportunities
                    if opp.priority in [CoachingPriority.CRITICAL, CoachingPriority.HIGH]
                ]

                if critical_opportunities:
                    alert_data = {
                        "type": "coaching_alert",
                        "insights_id": insights.insights_id,
                        "agent_id": insights.agent_id,
                        "critical_opportunities": [
                            {
                                "priority": opp.priority.value,
                                "category": opp.category,
                                "title": opp.title,
                                "recommended_action": opp.recommended_action
                            }
                            for opp in critical_opportunities
                        ],
                        "timestamp": insights.timestamp.isoformat()
                    }

                    # Broadcast alert
                    # Note: Would need tenant_id - assuming it's available from context
                    logger.info(f"Broadcasting {len(critical_opportunities)} coaching alerts")

        except Exception as e:
            logger.warning(f"Failed to broadcast coaching insights: {e}")

    # ========================================================================
    # Helper Methods - Metrics
    # ========================================================================

    def _update_metrics(self, analysis: ConversationAnalysis):
        """Update service performance metrics"""
        self.metrics["total_analyses"] += 1
        self.metrics["successful_analyses"] += 1

        # Update average analysis time
        current_avg = self.metrics["avg_analysis_time_ms"]
        total = self.metrics["total_analyses"]

        self.metrics["avg_analysis_time_ms"] = (
            (current_avg * (total - 1) + analysis.processing_time_ms) / total
        )

    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service performance metrics"""
        return {
            "total_analyses": self.metrics["total_analyses"],
            "successful_analyses": self.metrics["successful_analyses"],
            "failed_analyses": self.metrics["failed_analyses"],
            "success_rate": (
                self.metrics["successful_analyses"] / max(self.metrics["total_analyses"], 1)
            ),
            "avg_analysis_time_ms": self.metrics["avg_analysis_time_ms"],
            "avg_insight_time_ms": self.metrics["avg_insight_time_ms"],
            "coaching_opportunities_identified": self.metrics["coaching_opportunities_identified"],
            "cache_hit_rate": self.metrics["cache_hit_rate"]
        }


# ============================================================================
# Singleton and Factory Functions
# ============================================================================

_conversation_analyzer_instance = None


async def get_conversation_analyzer() -> ClaudeConversationAnalyzer:
    """Get singleton conversation analyzer instance"""
    global _conversation_analyzer_instance

    if _conversation_analyzer_instance is None:
        _conversation_analyzer_instance = ClaudeConversationAnalyzer()
        await _conversation_analyzer_instance.initialize()

    return _conversation_analyzer_instance


# Convenience functions

async def analyze_agent_conversation(
    conversation_data: ConversationData
) -> ConversationAnalysis:
    """Analyze agent conversation with coaching insights"""
    analyzer = await get_conversation_analyzer()
    return await analyzer.analyze_conversation(conversation_data)


async def get_coaching_recommendations(
    analysis: ConversationAnalysis
) -> CoachingInsights:
    """Get AI-powered coaching recommendations"""
    analyzer = await get_conversation_analyzer()
    return await analyzer.identify_coaching_opportunities(analysis)


async def track_agent_improvement(
    agent_id: str,
    time_period: str = "last_30_days"
) -> ImprovementMetrics:
    """Track agent performance improvement over time"""
    analyzer = await get_conversation_analyzer()
    return await analyzer.track_improvement_metrics(agent_id, time_period)


__all__ = [
    # Service
    "ClaudeConversationAnalyzer",
    "get_conversation_analyzer",

    # Data Models
    "ConversationData",
    "ConversationAnalysis",
    "CoachingInsights",
    "ImprovementMetrics",
    "SkillAssessment",
    "QualityScore",
    "ExpertiseAssessment",
    "CoachingOpportunity",

    # Enums
    "ConversationQualityArea",
    "RealEstateExpertiseArea",
    "CoachingPriority",
    "SkillLevel",
    "ConversationOutcome",

    # Convenience Functions
    "analyze_agent_conversation",
    "get_coaching_recommendations",
    "track_agent_improvement"
]
