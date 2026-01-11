"""
Advanced Conversation Intelligence Engine - Phase 2 Enhancement

Sophisticated conversation analysis using Claude's advanced language understanding
for emotional intelligence, conversation flow optimization, and objection prediction.

Features:
- Emotional state detection and analysis
- Conversation trajectory prediction
- Flow optimization recommendations
- Advanced objection detection and handling
- Family dynamics and decision-maker identification
- Conversation health scoring
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import json
import re

from anthropic import AsyncAnthropic
import redis.asyncio as redis
from ..ghl_utils.config import settings
from .websocket_manager import get_websocket_manager, IntelligenceEventType

logger = logging.getLogger(__name__)


class EmotionalState(Enum):
    """Emotional states detected in conversations."""
    EXCITED = "excited"
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    FRUSTRATED = "frustrated"
    CONFUSED = "confused"
    SKEPTICAL = "skeptical"
    STRESSED = "stressed"
    OVERWHELMED = "overwhelmed"
    DECISIVE = "decisive"


class UrgencyLevel(Enum):
    """Urgency levels for prospect decision-making."""
    URGENT = "urgent"          # Immediate need (days)
    HIGH = "high"              # Near-term need (weeks)
    MODERATE = "moderate"      # Medium-term need (months)
    LOW = "low"               # Long-term need (6+ months)
    EXPLORATORY = "exploratory"  # Just browsing/learning


class ConversationStage(Enum):
    """Stages of real estate conversation flow."""
    INITIAL_CONTACT = "initial_contact"
    RAPPORT_BUILDING = "rapport_building"
    NEEDS_DISCOVERY = "needs_discovery"
    QUALIFICATION = "qualification"
    PROPERTY_PRESENTATION = "property_presentation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class ConversationHealth(Enum):
    """Overall conversation health status."""
    EXCELLENT = "excellent"      # 85-100% - On track, strong engagement
    GOOD = "good"               # 70-84% - Positive trajectory, minor issues
    FAIR = "fair"               # 55-69% - Manageable concerns, needs attention
    POOR = "poor"               # 40-54% - Significant issues, intervention needed
    CRITICAL = "critical"       # 0-39% - Major problems, immediate action required


@dataclass
class EmotionalAnalysis:
    """Emotional state analysis result."""
    primary_emotion: EmotionalState
    secondary_emotions: List[EmotionalState]
    confidence_score: float
    emotional_intensity: float  # 0.0 to 1.0
    stress_indicators: List[str]
    motivation_factors: List[str]
    decision_readiness: float  # 0.0 to 1.0


@dataclass
class ConversationParticipant:
    """Individual participant in conversation."""
    participant_id: str
    role: str  # "prospect", "spouse", "agent", "decision_maker"
    influence_level: float  # 0.0 to 1.0
    communication_style: str
    key_concerns: List[str]
    emotional_state: EmotionalState


@dataclass
class FamilyDynamicsAnalysis:
    """Analysis of family/group dynamics in conversation."""
    participants: List[ConversationParticipant]
    primary_decision_maker: str
    decision_making_style: str  # "collaborative", "authoritative", "democratic"
    consensus_level: float  # 0.0 to 1.0
    potential_conflicts: List[str]
    alignment_score: float


@dataclass
class ConversationFlowAnalysis:
    """Analysis of conversation flow and progression."""
    current_stage: ConversationStage
    stage_progress: float  # 0.0 to 1.0 within current stage
    optimal_next_stage: ConversationStage
    stage_transition_readiness: float
    flow_bottlenecks: List[str]
    acceleration_opportunities: List[str]


@dataclass
class ObjectionAnalysis:
    """Advanced objection detection and analysis."""
    objection_detected: bool
    objection_type: str
    objection_severity: str  # "mild", "moderate", "strong"
    underlying_concerns: List[str]
    objection_category: str  # "price", "timing", "trust", "property", "process"
    root_cause_analysis: str
    handling_strategies: List[str]
    success_probability: float


@dataclass
class ConversationIntelligenceResult:
    """Comprehensive conversation intelligence analysis."""
    conversation_id: str
    analysis_timestamp: datetime
    emotional_analysis: EmotionalAnalysis
    family_dynamics: Optional[FamilyDynamicsAnalysis]
    flow_analysis: ConversationFlowAnalysis
    objection_analysis: ObjectionAnalysis
    urgency_assessment: UrgencyLevel
    conversation_health: ConversationHealth
    health_score: float
    key_insights: List[str]
    recommended_actions: List[str]
    coaching_suggestions: List[str]
    next_conversation_topics: List[str]
    predicted_outcome_probability: float
    processing_time_ms: float


class AdvancedConversationIntelligence:
    """
    Advanced conversation intelligence engine using Claude's sophisticated
    language understanding for real estate conversations.
    """

    def __init__(self):
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.websocket_manager = get_websocket_manager()
        self.redis_client = None

        # Initialize conversation analysis templates
        self.emotional_analysis_template = self._create_emotional_analysis_template()
        self.flow_analysis_template = self._create_flow_analysis_template()
        self.objection_analysis_template = self._create_objection_analysis_template()

        # Initialize Redis for caching
        self._init_redis()

    async def _init_redis(self):
        """Initialize Redis connection for caching conversation intelligence."""
        try:
            self.redis_client = redis.from_url(
                settings.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            await self.redis_client.ping()
            logger.info("Advanced conversation intelligence Redis connection established")
        except Exception as e:
            logger.warning(f"Redis unavailable for conversation intelligence: {e}")
            self.redis_client = None

    async def analyze_conversation_intelligence(
        self,
        conversation_history: List[Dict[str, Any]],
        agent_id: str,
        lead_context: Optional[Dict[str, Any]] = None,
        real_time_mode: bool = False
    ) -> ConversationIntelligenceResult:
        """
        Perform comprehensive conversation intelligence analysis.

        Args:
            conversation_history: List of conversation messages with speaker, content, timestamp
            agent_id: ID of the agent requesting analysis
            lead_context: Additional context about the lead
            real_time_mode: Whether to optimize for real-time processing

        Returns:
            Complete conversation intelligence analysis
        """
        start_time = datetime.now()
        conversation_id = self._generate_conversation_id(conversation_history)

        try:
            logger.info(f"Starting conversation intelligence analysis for agent {agent_id}")

            # Check cache for recent analysis
            if not real_time_mode:
                cached_result = await self._get_cached_analysis(conversation_id)
                if cached_result:
                    return cached_result

            # Parallel analysis of different aspects
            analysis_tasks = [
                self._analyze_emotional_state(conversation_history, lead_context),
                self._analyze_conversation_flow(conversation_history, lead_context),
                self._detect_and_analyze_objections(conversation_history, lead_context),
                self._assess_family_dynamics(conversation_history),
                self._assess_urgency_level(conversation_history, lead_context)
            ]

            # Execute analysis in parallel for performance
            emotional_analysis, flow_analysis, objection_analysis, family_dynamics, urgency_level = await asyncio.gather(*analysis_tasks)

            # Calculate conversation health score
            health_score, health_status = self._calculate_conversation_health(
                emotional_analysis, flow_analysis, objection_analysis
            )

            # Generate strategic insights and recommendations
            insights, actions, coaching, next_topics = await self._generate_strategic_recommendations(
                emotional_analysis, flow_analysis, objection_analysis, family_dynamics, urgency_level
            )

            # Predict conversation outcome
            outcome_probability = self._predict_conversation_outcome(
                emotional_analysis, flow_analysis, objection_analysis, urgency_level
            )

            processing_time = (datetime.now() - start_time).total_seconds() * 1000

            # Compile comprehensive result
            result = ConversationIntelligenceResult(
                conversation_id=conversation_id,
                analysis_timestamp=datetime.now(),
                emotional_analysis=emotional_analysis,
                family_dynamics=family_dynamics,
                flow_analysis=flow_analysis,
                objection_analysis=objection_analysis,
                urgency_assessment=urgency_level,
                conversation_health=health_status,
                health_score=health_score,
                key_insights=insights,
                recommended_actions=actions,
                coaching_suggestions=coaching,
                next_conversation_topics=next_topics,
                predicted_outcome_probability=outcome_probability,
                processing_time_ms=processing_time
            )

            # Cache result for future reference
            await self._cache_analysis_result(conversation_id, result)

            # Broadcast real-time updates if enabled
            if real_time_mode:
                await self._broadcast_intelligence_update(agent_id, result)

            logger.info(f"Conversation intelligence analysis completed in {processing_time:.1f}ms")
            return result

        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(f"Error in conversation intelligence analysis: {e}")

            # Return fallback result
            return self._create_fallback_result(conversation_id, processing_time, str(e))

    async def _analyze_emotional_state(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_context: Optional[Dict[str, Any]] = None
    ) -> EmotionalAnalysis:
        """Analyze emotional states in conversation."""

        # Prepare conversation text for analysis
        conversation_text = self._format_conversation_for_analysis(conversation_history)

        # Create emotional analysis prompt
        prompt = self.emotional_analysis_template.format(
            conversation_text=conversation_text,
            context=json.dumps(lead_context, indent=2) if lead_context else "No additional context provided"
        )

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            return self._parse_emotional_analysis(analysis_text)

        except Exception as e:
            logger.warning(f"Error in emotional analysis: {e}")
            return self._create_fallback_emotional_analysis()

    async def _analyze_conversation_flow(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_context: Optional[Dict[str, Any]] = None
    ) -> ConversationFlowAnalysis:
        """Analyze conversation flow and stage progression."""

        conversation_text = self._format_conversation_for_analysis(conversation_history)

        prompt = self.flow_analysis_template.format(
            conversation_text=conversation_text,
            context=json.dumps(lead_context, indent=2) if lead_context else "No additional context provided"
        )

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            return self._parse_flow_analysis(analysis_text)

        except Exception as e:
            logger.warning(f"Error in flow analysis: {e}")
            return self._create_fallback_flow_analysis()

    async def _detect_and_analyze_objections(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_context: Optional[Dict[str, Any]] = None
    ) -> ObjectionAnalysis:
        """Detect and analyze objections in conversation."""

        conversation_text = self._format_conversation_for_analysis(conversation_history)

        prompt = self.objection_analysis_template.format(
            conversation_text=conversation_text,
            context=json.dumps(lead_context, indent=2) if lead_context else "No additional context provided"
        )

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            return self._parse_objection_analysis(analysis_text)

        except Exception as e:
            logger.warning(f"Error in objection analysis: {e}")
            return self._create_fallback_objection_analysis()

    async def _assess_family_dynamics(
        self,
        conversation_history: List[Dict[str, Any]]
    ) -> Optional[FamilyDynamicsAnalysis]:
        """Assess family dynamics if multiple participants detected."""

        # Check if multiple participants are involved
        participants = self._identify_conversation_participants(conversation_history)

        if len(participants) <= 1:
            return None

        # Analyze family dynamics
        conversation_text = self._format_conversation_for_analysis(conversation_history)

        prompt = f"""
        Analyze the family/group dynamics in this real estate conversation:

        {conversation_text}

        Identify:
        1. **Decision-making roles**: Who appears to be the primary decision-maker?
        2. **Communication patterns**: How do participants interact with each other?
        3. **Consensus level**: How aligned are the participants?
        4. **Potential conflicts**: Any areas of disagreement or tension?
        5. **Influence dynamics**: Who has more influence in the discussion?

        Provide specific insights about the family dynamics and how they might affect the real estate decision-making process.
        """

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=800,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            return self._parse_family_dynamics_analysis(analysis_text, participants)

        except Exception as e:
            logger.warning(f"Error in family dynamics analysis: {e}")
            return None

    async def _assess_urgency_level(
        self,
        conversation_history: List[Dict[str, Any]],
        lead_context: Optional[Dict[str, Any]] = None
    ) -> UrgencyLevel:
        """Assess the urgency level of the prospect's needs."""

        conversation_text = self._format_conversation_for_analysis(conversation_history)

        prompt = f"""
        Analyze the urgency level in this real estate conversation:

        {conversation_text}

        Look for indicators of:
        - **Timeline mentions**: When do they need to move/buy/sell?
        - **Pressure factors**: Job relocation, school deadlines, lease expiration, etc.
        - **Language urgency**: Words indicating immediacy or time pressure
        - **Decision readiness**: How quickly are they prepared to make decisions?

        Classify the urgency as:
        - URGENT: Immediate need (days to weeks)
        - HIGH: Near-term need (1-2 months)
        - MODERATE: Medium-term need (3-6 months)
        - LOW: Long-term need (6+ months)
        - EXPLORATORY: Just browsing/learning

        Provide the classification with specific evidence from the conversation.
        """

        try:
            response = await self.claude_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=400,
                temperature=0.2,
                messages=[{"role": "user", "content": prompt}]
            )

            analysis_text = response.content[0].text
            return self._parse_urgency_assessment(analysis_text)

        except Exception as e:
            logger.warning(f"Error in urgency assessment: {e}")
            return UrgencyLevel.MODERATE

    def _create_emotional_analysis_template(self) -> str:
        """Create template for emotional analysis."""
        return """
        You are an expert in emotional intelligence and psychology, specializing in real estate conversations.

        Analyze the emotional states in this conversation:

        {conversation_text}

        Context: {context}

        Provide a detailed emotional analysis including:

        1. **Primary Emotion**: The dominant emotional state (excited, confident, neutral, anxious, frustrated, confused, skeptical, stressed, overwhelmed, decisive)
        2. **Secondary Emotions**: Other emotions present (list 1-3)
        3. **Emotional Intensity**: How strong are these emotions? (0.0 to 1.0)
        4. **Stress Indicators**: Specific signs of stress or pressure
        5. **Motivation Factors**: What's driving their emotional state?
        6. **Decision Readiness**: How emotionally prepared are they to make decisions? (0.0 to 1.0)

        Focus on understanding the psychological state and how it affects their real estate decision-making process.
        Look for subtle emotional cues, language patterns, and underlying concerns.
        """

    def _create_flow_analysis_template(self) -> str:
        """Create template for conversation flow analysis."""
        return """
        You are an expert in real estate sales psychology and conversation flow optimization.

        Analyze the conversation flow and stage progression:

        {conversation_text}

        Context: {context}

        Evaluate:

        1. **Current Stage**: Which stage is the conversation currently in?
           - initial_contact, rapport_building, needs_discovery, qualification,
           - property_presentation, objection_handling, closing, follow_up

        2. **Stage Progress**: How far through the current stage? (0.0 to 1.0)
        3. **Optimal Next Stage**: What stage should come next?
        4. **Transition Readiness**: How ready are they to move forward? (0.0 to 1.0)
        5. **Flow Bottlenecks**: What's slowing down progression?
        6. **Acceleration Opportunities**: How can we move the conversation forward faster?

        Consider natural conversation flow, prospect readiness, and sales best practices.
        """

    def _create_objection_analysis_template(self) -> str:
        """Create template for objection analysis."""
        return """
        You are an expert real estate objection handler with deep knowledge of prospect psychology.

        Analyze this conversation for objections and resistance:

        {conversation_text}

        Context: {context}

        Look for:

        1. **Objection Detection**: Are there any explicit or implicit objections?
        2. **Objection Type**: What specifically are they objecting to?
        3. **Severity Level**: How strong is the objection? (mild, moderate, strong)
        4. **Underlying Concerns**: What are the real issues behind the objection?
        5. **Objection Category**: Is it about price, timing, trust, property features, or process?
        6. **Root Cause**: What's the fundamental reason for their resistance?
        7. **Handling Strategies**: Specific approaches to address this objection
        8. **Success Probability**: Likelihood of overcoming this objection (0.0 to 1.0)

        Pay attention to subtle resistance, hesitation, and indirect objections that may not be explicitly stated.
        """

    def _format_conversation_for_analysis(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Format conversation history for Claude analysis."""
        formatted_lines = []

        for message in conversation_history[-20:]:  # Limit to last 20 messages for context
            speaker = message.get('speaker', 'Unknown')
            content = message.get('content', message.get('message', ''))
            timestamp = message.get('timestamp', '')

            if timestamp:
                formatted_lines.append(f"[{timestamp}] {speaker}: {content}")
            else:
                formatted_lines.append(f"{speaker}: {content}")

        return "\n".join(formatted_lines)

    def _parse_emotional_analysis(self, analysis_text: str) -> EmotionalAnalysis:
        """Parse Claude's emotional analysis response."""
        try:
            # Extract key information using pattern matching
            primary_emotion = self._extract_primary_emotion(analysis_text)
            secondary_emotions = self._extract_secondary_emotions(analysis_text)
            confidence_score = self._extract_confidence_score(analysis_text)
            emotional_intensity = self._extract_emotional_intensity(analysis_text)
            stress_indicators = self._extract_stress_indicators(analysis_text)
            motivation_factors = self._extract_motivation_factors(analysis_text)
            decision_readiness = self._extract_decision_readiness(analysis_text)

            return EmotionalAnalysis(
                primary_emotion=primary_emotion,
                secondary_emotions=secondary_emotions,
                confidence_score=confidence_score,
                emotional_intensity=emotional_intensity,
                stress_indicators=stress_indicators,
                motivation_factors=motivation_factors,
                decision_readiness=decision_readiness
            )

        except Exception as e:
            logger.warning(f"Error parsing emotional analysis: {e}")
            return self._create_fallback_emotional_analysis()

    def _parse_flow_analysis(self, analysis_text: str) -> ConversationFlowAnalysis:
        """Parse Claude's flow analysis response."""
        try:
            current_stage = self._extract_current_stage(analysis_text)
            stage_progress = self._extract_stage_progress(analysis_text)
            optimal_next_stage = self._extract_optimal_next_stage(analysis_text)
            transition_readiness = self._extract_transition_readiness(analysis_text)
            flow_bottlenecks = self._extract_flow_bottlenecks(analysis_text)
            acceleration_opportunities = self._extract_acceleration_opportunities(analysis_text)

            return ConversationFlowAnalysis(
                current_stage=current_stage,
                stage_progress=stage_progress,
                optimal_next_stage=optimal_next_stage,
                stage_transition_readiness=transition_readiness,
                flow_bottlenecks=flow_bottlenecks,
                acceleration_opportunities=acceleration_opportunities
            )

        except Exception as e:
            logger.warning(f"Error parsing flow analysis: {e}")
            return self._create_fallback_flow_analysis()

    def _parse_objection_analysis(self, analysis_text: str) -> ObjectionAnalysis:
        """Parse Claude's objection analysis response."""
        try:
            objection_detected = "objection" in analysis_text.lower()
            objection_type = self._extract_objection_type(analysis_text)
            objection_severity = self._extract_objection_severity(analysis_text)
            underlying_concerns = self._extract_underlying_concerns(analysis_text)
            objection_category = self._extract_objection_category(analysis_text)
            root_cause_analysis = self._extract_root_cause(analysis_text)
            handling_strategies = self._extract_handling_strategies(analysis_text)
            success_probability = self._extract_success_probability(analysis_text)

            return ObjectionAnalysis(
                objection_detected=objection_detected,
                objection_type=objection_type,
                objection_severity=objection_severity,
                underlying_concerns=underlying_concerns,
                objection_category=objection_category,
                root_cause_analysis=root_cause_analysis,
                handling_strategies=handling_strategies,
                success_probability=success_probability
            )

        except Exception as e:
            logger.warning(f"Error parsing objection analysis: {e}")
            return self._create_fallback_objection_analysis()

    # Helper methods for parsing Claude responses
    def _extract_primary_emotion(self, text: str) -> EmotionalState:
        """Extract primary emotion from analysis text."""
        emotion_keywords = {
            EmotionalState.EXCITED: ["excited", "enthusiastic", "eager"],
            EmotionalState.CONFIDENT: ["confident", "assured", "certain"],
            EmotionalState.NEUTRAL: ["neutral", "calm", "balanced"],
            EmotionalState.ANXIOUS: ["anxious", "nervous", "worried"],
            EmotionalState.FRUSTRATED: ["frustrated", "annoyed", "irritated"],
            EmotionalState.CONFUSED: ["confused", "uncertain", "unclear"],
            EmotionalState.SKEPTICAL: ["skeptical", "doubtful", "suspicious"],
            EmotionalState.STRESSED: ["stressed", "pressured", "overwhelmed"],
            EmotionalState.DECISIVE: ["decisive", "determined", "ready"]
        }

        text_lower = text.lower()
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion

        return EmotionalState.NEUTRAL

    def _extract_secondary_emotions(self, text: str) -> List[EmotionalState]:
        """Extract secondary emotions from analysis text."""
        # Simplified extraction - could be enhanced with more sophisticated parsing
        emotions = []
        if "anxious" in text.lower() and len(emotions) < 3:
            emotions.append(EmotionalState.ANXIOUS)
        if "excited" in text.lower() and len(emotions) < 3:
            emotions.append(EmotionalState.EXCITED)
        return emotions

    def _extract_confidence_score(self, text: str) -> float:
        """Extract confidence score from analysis text."""
        # Look for percentage or decimal patterns
        import re
        pattern = r'confidence[:\s]*(\d+(?:\.\d+)?)[%]?'
        match = re.search(pattern, text.lower())
        if match:
            score = float(match.group(1))
            return score / 100 if score > 1 else score
        return 0.75  # Default confidence

    def _extract_emotional_intensity(self, text: str) -> float:
        """Extract emotional intensity from analysis text."""
        if "high intensity" in text.lower() or "very strong" in text.lower():
            return 0.8
        elif "moderate intensity" in text.lower():
            return 0.6
        elif "low intensity" in text.lower():
            return 0.3
        return 0.5

    def _extract_stress_indicators(self, text: str) -> List[str]:
        """Extract stress indicators from analysis text."""
        indicators = []
        if "time pressure" in text.lower():
            indicators.append("Time pressure mentioned")
        if "deadline" in text.lower():
            indicators.append("Deadline concerns")
        if "rushed" in text.lower():
            indicators.append("Rushed decision-making")
        return indicators

    def _extract_motivation_factors(self, text: str) -> List[str]:
        """Extract motivation factors from analysis text."""
        factors = []
        if "family" in text.lower():
            factors.append("Family considerations")
        if "investment" in text.lower():
            factors.append("Investment opportunity")
        if "relocation" in text.lower():
            factors.append("Job relocation")
        return factors

    def _extract_decision_readiness(self, text: str) -> float:
        """Extract decision readiness score from analysis text."""
        if "ready to decide" in text.lower():
            return 0.9
        elif "almost ready" in text.lower():
            return 0.7
        elif "needs more time" in text.lower():
            return 0.3
        return 0.5

    def _extract_current_stage(self, text: str) -> ConversationStage:
        """Extract current conversation stage from analysis text."""
        stage_keywords = {
            ConversationStage.INITIAL_CONTACT: ["initial", "introduction", "first contact"],
            ConversationStage.RAPPORT_BUILDING: ["rapport", "relationship", "trust"],
            ConversationStage.NEEDS_DISCOVERY: ["needs", "discovery", "requirements"],
            ConversationStage.QUALIFICATION: ["qualification", "budget", "timeline"],
            ConversationStage.PROPERTY_PRESENTATION: ["presentation", "showing", "property"],
            ConversationStage.OBJECTION_HANDLING: ["objection", "concern", "hesitation"],
            ConversationStage.CLOSING: ["closing", "decision", "agreement"],
            ConversationStage.FOLLOW_UP: ["follow-up", "next steps"]
        }

        text_lower = text.lower()
        for stage, keywords in stage_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return stage

        return ConversationStage.NEEDS_DISCOVERY  # Default stage

    def _extract_stage_progress(self, text: str) -> float:
        """Extract stage progress from analysis text."""
        if "beginning" in text.lower():
            return 0.2
        elif "middle" in text.lower() or "halfway" in text.lower():
            return 0.5
        elif "end" in text.lower() or "complete" in text.lower():
            return 0.8
        return 0.5

    def _extract_optimal_next_stage(self, text: str) -> ConversationStage:
        """Extract optimal next stage from analysis text."""
        # Simplified logic - in practice, this would be more sophisticated
        current_stage = self._extract_current_stage(text)
        stage_progression = {
            ConversationStage.INITIAL_CONTACT: ConversationStage.RAPPORT_BUILDING,
            ConversationStage.RAPPORT_BUILDING: ConversationStage.NEEDS_DISCOVERY,
            ConversationStage.NEEDS_DISCOVERY: ConversationStage.QUALIFICATION,
            ConversationStage.QUALIFICATION: ConversationStage.PROPERTY_PRESENTATION,
            ConversationStage.PROPERTY_PRESENTATION: ConversationStage.CLOSING,
            ConversationStage.OBJECTION_HANDLING: ConversationStage.CLOSING,
            ConversationStage.CLOSING: ConversationStage.FOLLOW_UP
        }
        return stage_progression.get(current_stage, ConversationStage.FOLLOW_UP)

    def _extract_transition_readiness(self, text: str) -> float:
        """Extract transition readiness from analysis text."""
        if "ready to move forward" in text.lower():
            return 0.9
        elif "partially ready" in text.lower():
            return 0.6
        elif "not ready" in text.lower():
            return 0.2
        return 0.5

    def _extract_flow_bottlenecks(self, text: str) -> List[str]:
        """Extract flow bottlenecks from analysis text."""
        bottlenecks = []
        if "lack of trust" in text.lower():
            bottlenecks.append("Trust building needed")
        if "unclear needs" in text.lower():
            bottlenecks.append("Needs clarification required")
        if "budget concerns" in text.lower():
            bottlenecks.append("Budget qualification needed")
        return bottlenecks

    def _extract_acceleration_opportunities(self, text: str) -> List[str]:
        """Extract acceleration opportunities from analysis text."""
        opportunities = []
        if "urgency" in text.lower():
            opportunities.append("Leverage urgency factors")
        if "competitive" in text.lower():
            opportunities.append("Emphasize competitive advantages")
        if "decision maker" in text.lower():
            opportunities.append("Focus on decision maker")
        return opportunities

    def _extract_objection_type(self, text: str) -> str:
        """Extract objection type from analysis text."""
        if "price" in text.lower() or "cost" in text.lower():
            return "Price objection"
        elif "timing" in text.lower() or "time" in text.lower():
            return "Timing objection"
        elif "property" in text.lower() or "location" in text.lower():
            return "Property objection"
        elif "trust" in text.lower() or "agent" in text.lower():
            return "Trust objection"
        return "General hesitation"

    def _extract_objection_severity(self, text: str) -> str:
        """Extract objection severity from analysis text."""
        if "strong" in text.lower() or "major" in text.lower():
            return "strong"
        elif "moderate" in text.lower():
            return "moderate"
        return "mild"

    def _extract_underlying_concerns(self, text: str) -> List[str]:
        """Extract underlying concerns from analysis text."""
        concerns = []
        if "budget" in text.lower():
            concerns.append("Budget constraints")
        if "timeline" in text.lower():
            concerns.append("Timeline pressures")
        if "family" in text.lower():
            concerns.append("Family considerations")
        return concerns

    def _extract_objection_category(self, text: str) -> str:
        """Extract objection category from analysis text."""
        categories = ["price", "timing", "trust", "property", "process"]
        text_lower = text.lower()
        for category in categories:
            if category in text_lower:
                return category
        return "general"

    def _extract_root_cause(self, text: str) -> str:
        """Extract root cause analysis from text."""
        # Simplified extraction
        if "financial" in text.lower():
            return "Financial constraints or concerns"
        elif "emotional" in text.lower():
            return "Emotional hesitation or fear"
        elif "logical" in text.lower():
            return "Logical concerns about decision"
        return "General hesitation about major purchase"

    def _extract_handling_strategies(self, text: str) -> List[str]:
        """Extract handling strategies from text."""
        strategies = []
        if "education" in text.lower():
            strategies.append("Provide educational materials")
        if "testimonials" in text.lower():
            strategies.append("Share client testimonials")
        if "comparison" in text.lower():
            strategies.append("Provide market comparisons")
        return strategies

    def _extract_success_probability(self, text: str) -> float:
        """Extract success probability from text."""
        if "high probability" in text.lower():
            return 0.8
        elif "moderate probability" in text.lower():
            return 0.6
        elif "low probability" in text.lower():
            return 0.3
        return 0.5

    def _identify_conversation_participants(self, conversation_history: List[Dict[str, Any]]) -> List[str]:
        """Identify unique participants in conversation."""
        participants = set()
        for message in conversation_history:
            speaker = message.get('speaker', 'Unknown')
            if speaker and speaker.lower() not in ['system', 'bot', 'assistant']:
                participants.add(speaker)
        return list(participants)

    def _parse_family_dynamics_analysis(self, analysis_text: str, participants: List[str]) -> FamilyDynamicsAnalysis:
        """Parse family dynamics analysis."""
        # Simplified implementation
        participant_objects = []
        for p in participants:
            participant_objects.append(ConversationParticipant(
                participant_id=p,
                role="prospect" if "prospect" in p.lower() else "participant",
                influence_level=0.5,
                communication_style="collaborative",
                key_concerns=[],
                emotional_state=EmotionalState.NEUTRAL
            ))

        return FamilyDynamicsAnalysis(
            participants=participant_objects,
            primary_decision_maker=participants[0] if participants else "unknown",
            decision_making_style="collaborative",
            consensus_level=0.7,
            potential_conflicts=[],
            alignment_score=0.75
        )

    def _parse_urgency_assessment(self, analysis_text: str) -> UrgencyLevel:
        """Parse urgency level from analysis text."""
        text_lower = analysis_text.lower()

        if any(keyword in text_lower for keyword in ["urgent", "immediate", "asap", "right away"]):
            return UrgencyLevel.URGENT
        elif any(keyword in text_lower for keyword in ["high", "soon", "near-term", "quickly"]):
            return UrgencyLevel.HIGH
        elif any(keyword in text_lower for keyword in ["moderate", "medium-term", "few months"]):
            return UrgencyLevel.MODERATE
        elif any(keyword in text_lower for keyword in ["low", "long-term", "6 months", "year"]):
            return UrgencyLevel.LOW
        elif any(keyword in text_lower for keyword in ["exploratory", "browsing", "learning", "research"]):
            return UrgencyLevel.EXPLORATORY

        return UrgencyLevel.MODERATE

    def _calculate_conversation_health(
        self,
        emotional_analysis: EmotionalAnalysis,
        flow_analysis: ConversationFlowAnalysis,
        objection_analysis: ObjectionAnalysis
    ) -> Tuple[float, ConversationHealth]:
        """Calculate overall conversation health score."""

        # Emotional health component (30%)
        emotional_score = 0.3 * (
            emotional_analysis.decision_readiness * 0.4 +
            (1 - emotional_analysis.emotional_intensity) * 0.3 +  # Lower stress is better
            emotional_analysis.confidence_score * 0.3
        )

        # Flow health component (40%)
        flow_score = 0.4 * (
            flow_analysis.stage_progress * 0.5 +
            flow_analysis.stage_transition_readiness * 0.5
        )

        # Objection health component (30%)
        objection_penalty = 0.3 if objection_analysis.objection_detected else 0.0
        objection_score = 0.3 * (
            objection_analysis.success_probability if objection_analysis.objection_detected else 1.0
        ) - objection_penalty

        total_score = emotional_score + flow_score + objection_score

        # Determine health status
        if total_score >= 0.85:
            health_status = ConversationHealth.EXCELLENT
        elif total_score >= 0.70:
            health_status = ConversationHealth.GOOD
        elif total_score >= 0.55:
            health_status = ConversationHealth.FAIR
        elif total_score >= 0.40:
            health_status = ConversationHealth.POOR
        else:
            health_status = ConversationHealth.CRITICAL

        return total_score, health_status

    async def _generate_strategic_recommendations(
        self,
        emotional_analysis: EmotionalAnalysis,
        flow_analysis: ConversationFlowAnalysis,
        objection_analysis: ObjectionAnalysis,
        family_dynamics: Optional[FamilyDynamicsAnalysis],
        urgency_level: UrgencyLevel
    ) -> Tuple[List[str], List[str], List[str], List[str]]:
        """Generate strategic insights and recommendations."""

        insights = []
        actions = []
        coaching = []
        next_topics = []

        # Emotional-based insights
        if emotional_analysis.primary_emotion == EmotionalState.ANXIOUS:
            insights.append("Prospect shows signs of anxiety - focus on reassurance and trust-building")
            coaching.append("Use calming language and provide plenty of reassurance")

        if emotional_analysis.decision_readiness > 0.7:
            insights.append("High decision readiness detected - opportunity to advance to closing")
            actions.append("Present next steps and create urgency")

        # Flow-based recommendations
        if flow_analysis.stage_transition_readiness > 0.8:
            insights.append(f"Ready to advance from {flow_analysis.current_stage.value} stage")
            actions.append(f"Transition to {flow_analysis.optimal_next_stage.value} stage")

        # Objection-based strategies
        if objection_analysis.objection_detected:
            insights.append(f"Active {objection_analysis.objection_category} objection detected")
            actions.extend(objection_analysis.handling_strategies)

        # Urgency-based tactics
        if urgency_level in [UrgencyLevel.URGENT, UrgencyLevel.HIGH]:
            insights.append("High urgency detected - leverage time sensitivity")
            coaching.append("Emphasize limited availability and timing benefits")
            next_topics.append("Discuss immediate next steps and timeline")

        # Family dynamics insights
        if family_dynamics:
            if family_dynamics.consensus_level < 0.6:
                insights.append("Low family consensus - address individual concerns")
                coaching.append("Facilitate discussion between family members")

        # Default recommendations if none generated
        if not insights:
            insights.append("Conversation progressing normally with standard engagement")
        if not actions:
            actions.append("Continue with current conversation flow")
        if not coaching:
            coaching.append("Maintain professional, consultative approach")
        if not next_topics:
            next_topics.append("Explore specific property requirements")

        return insights, actions, coaching, next_topics

    def _predict_conversation_outcome(
        self,
        emotional_analysis: EmotionalAnalysis,
        flow_analysis: ConversationFlowAnalysis,
        objection_analysis: ObjectionAnalysis,
        urgency_level: UrgencyLevel
    ) -> float:
        """Predict probability of successful conversation outcome."""

        # Base probability
        base_probability = 0.4

        # Emotional factors
        if emotional_analysis.primary_emotion in [EmotionalState.EXCITED, EmotionalState.CONFIDENT, EmotionalState.DECISIVE]:
            base_probability += 0.2
        elif emotional_analysis.primary_emotion in [EmotionalState.FRUSTRATED, EmotionalState.STRESSED]:
            base_probability -= 0.15

        # Decision readiness factor
        base_probability += emotional_analysis.decision_readiness * 0.2

        # Flow progression factor
        base_probability += flow_analysis.stage_progress * 0.1
        base_probability += flow_analysis.stage_transition_readiness * 0.1

        # Objection impact
        if objection_analysis.objection_detected:
            objection_impact = {
                "mild": -0.05,
                "moderate": -0.1,
                "strong": -0.2
            }.get(objection_analysis.objection_severity, -0.1)
            base_probability += objection_impact
            base_probability += objection_analysis.success_probability * 0.1

        # Urgency boost
        urgency_boost = {
            UrgencyLevel.URGENT: 0.15,
            UrgencyLevel.HIGH: 0.1,
            UrgencyLevel.MODERATE: 0.05,
            UrgencyLevel.LOW: 0.0,
            UrgencyLevel.EXPLORATORY: -0.1
        }.get(urgency_level, 0.0)
        base_probability += urgency_boost

        return max(0.0, min(1.0, base_probability))

    # Fallback methods
    def _create_fallback_emotional_analysis(self) -> EmotionalAnalysis:
        """Create fallback emotional analysis."""
        return EmotionalAnalysis(
            primary_emotion=EmotionalState.NEUTRAL,
            secondary_emotions=[],
            confidence_score=0.5,
            emotional_intensity=0.5,
            stress_indicators=["Analysis error - manual review recommended"],
            motivation_factors=["Unable to determine"],
            decision_readiness=0.5
        )

    def _create_fallback_flow_analysis(self) -> ConversationFlowAnalysis:
        """Create fallback flow analysis."""
        return ConversationFlowAnalysis(
            current_stage=ConversationStage.NEEDS_DISCOVERY,
            stage_progress=0.5,
            optimal_next_stage=ConversationStage.QUALIFICATION,
            stage_transition_readiness=0.5,
            flow_bottlenecks=["Analysis error occurred"],
            acceleration_opportunities=["Manual review recommended"]
        )

    def _create_fallback_objection_analysis(self) -> ObjectionAnalysis:
        """Create fallback objection analysis."""
        return ObjectionAnalysis(
            objection_detected=False,
            objection_type="Unknown",
            objection_severity="mild",
            underlying_concerns=["Analysis error - unable to determine"],
            objection_category="general",
            root_cause_analysis="Unable to analyze due to processing error",
            handling_strategies=["Manual review recommended"],
            success_probability=0.5
        )

    def _create_fallback_result(self, conversation_id: str, processing_time: float, error: str) -> ConversationIntelligenceResult:
        """Create fallback result when analysis fails."""
        return ConversationIntelligenceResult(
            conversation_id=conversation_id,
            analysis_timestamp=datetime.now(),
            emotional_analysis=self._create_fallback_emotional_analysis(),
            family_dynamics=None,
            flow_analysis=self._create_fallback_flow_analysis(),
            objection_analysis=self._create_fallback_objection_analysis(),
            urgency_assessment=UrgencyLevel.MODERATE,
            conversation_health=ConversationHealth.FAIR,
            health_score=0.5,
            key_insights=[f"Analysis failed: {error}"],
            recommended_actions=["Manual conversation review recommended"],
            coaching_suggestions=["Professional consultation suggested"],
            next_conversation_topics=["Continue with standard approach"],
            predicted_outcome_probability=0.5,
            processing_time_ms=processing_time
        )

    def _generate_conversation_id(self, conversation_history: List[Dict[str, Any]]) -> str:
        """Generate unique conversation ID."""
        import hashlib
        conversation_text = json.dumps(conversation_history, sort_keys=True)
        hash_obj = hashlib.sha256(conversation_text.encode('utf-8'))
        return f"conv_{hash_obj.hexdigest()[:12]}_{int(datetime.now().timestamp())}"

    async def _get_cached_analysis(self, conversation_id: str) -> Optional[ConversationIntelligenceResult]:
        """Get cached conversation analysis."""
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(f"conv_intelligence:{conversation_id}")
            if cached_data:
                data = json.loads(cached_data)
                # Convert timestamp strings back to datetime objects
                data['analysis_timestamp'] = datetime.fromisoformat(data['analysis_timestamp'])
                return ConversationIntelligenceResult(**data)
        except Exception as e:
            logger.warning(f"Error retrieving cached conversation analysis: {e}")

        return None

    async def _cache_analysis_result(self, conversation_id: str, result: ConversationIntelligenceResult, ttl_seconds: int = 1800):
        """Cache conversation analysis result."""
        if not self.redis_client:
            return

        try:
            result_data = asdict(result)
            # Convert datetime objects to strings for JSON serialization
            result_data['analysis_timestamp'] = result_data['analysis_timestamp'].isoformat()

            await self.redis_client.setex(
                f"conv_intelligence:{conversation_id}",
                ttl_seconds,
                json.dumps(result_data, default=str)
            )
        except Exception as e:
            logger.warning(f"Error caching conversation analysis: {e}")

    async def _broadcast_intelligence_update(self, agent_id: str, result: ConversationIntelligenceResult):
        """Broadcast conversation intelligence update via WebSocket."""
        try:
            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.CONVERSATION_ANALYSIS,
                {
                    "type": "conversation_intelligence_update",
                    "agent_id": agent_id,
                    "conversation_id": result.conversation_id,
                    "emotional_state": result.emotional_analysis.primary_emotion.value,
                    "conversation_stage": result.flow_analysis.current_stage.value,
                    "health_score": result.health_score,
                    "health_status": result.conversation_health.value,
                    "urgency_level": result.urgency_assessment.value,
                    "objection_detected": result.objection_analysis.objection_detected,
                    "outcome_probability": result.predicted_outcome_probability,
                    "key_insights": result.key_insights[:3],  # Top 3 insights
                    "recommended_actions": result.recommended_actions[:3],  # Top 3 actions
                    "processing_time_ms": result.processing_time_ms,
                    "timestamp": result.analysis_timestamp.isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to broadcast conversation intelligence update: {e}")


# Global instance
advanced_conversation_intelligence = AdvancedConversationIntelligence()


async def get_advanced_conversation_intelligence() -> AdvancedConversationIntelligence:
    """Get global advanced conversation intelligence service."""
    return advanced_conversation_intelligence