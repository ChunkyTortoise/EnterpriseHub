"""
Claude Conversation Intelligence Engine - Advanced Real-time Analysis
Provides real-time conversation analysis, intent detection, and response suggestions.
"""
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import streamlit as st

# Import existing services
from services.claude_assistant import ClaudeAssistant
from services.memory_service import MemoryService
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class ConversationAnalysis:
    """Structure for conversation analysis results."""
    intent_level: float  # 0.0-1.0
    urgency_score: float  # 0.0-1.0
    objection_type: Optional[str]
    recommended_response: str
    property_readiness: str  # low/medium/high
    next_best_action: str
    confidence: float  # 0.0-1.0
    analysis_timestamp: datetime

@dataclass
class IntentSignals:
    """Extracted intent signals from conversation."""
    financial_readiness: float  # 0.0-1.0
    timeline_urgency: float  # 0.0-1.0
    decision_authority: float  # 0.0-1.0
    emotional_investment: float  # 0.0-1.0
    hidden_concerns: List[str]
    lifestyle_indicators: Dict[str, float]

@dataclass
class ConversationThread:
    """Multi-turn conversation analysis with state persistence."""
    thread_id: str
    messages: List[Dict]  # Complete conversation history
    intent_evolution: List[Tuple[datetime, float]]  # Intent progression over time
    emotional_journey: List[Tuple[datetime, str, float]]  # (timestamp, emotion, intensity)
    trust_score_history: List[Tuple[datetime, float]]  # Trust building progression
    objection_patterns: List[Dict]  # Recurring objections and resolutions
    engagement_metrics: Dict[str, float]  # Response time, message length, etc.
    conversation_health: str  # excellent/good/concerning/poor
    closing_readiness: float  # 0.0-1.0, separate from urgency
    last_updated: datetime

@dataclass
class EmotionalState:
    """Detailed emotional state analysis with progression tracking."""
    primary_emotion: str  # excited, cautious, frustrated, analytical, overwhelmed, confident
    emotion_intensity: float  # 0.0-1.0
    secondary_emotions: List[Tuple[str, float]]  # [(emotion, intensity)]
    emotional_trajectory: str  # improving, stable, declining, volatile
    empathy_score: float  # 0.0-1.0, how well agent is connecting
    stress_indicators: List[str]  # Signs of stress or pressure
    excitement_indicators: List[str]  # Signs of enthusiasm or interest
    trust_indicators: List[str]  # Signs of building trust/rapport
    decision_readiness: float  # 0.0-1.0, psychological readiness to decide

@dataclass
class TrustMetrics:
    """Trust building and rapport analysis."""
    overall_trust_score: float  # 0.0-1.0
    rapport_level: str  # building, established, strong, excellent
    credibility_score: float  # 0.0-1.0, perceived agent expertise
    communication_alignment: float  # 0.0-1.0, style matching
    value_demonstration: float  # 0.0-1.0, perceived value provided
    responsiveness_score: float  # 0.0-1.0, timely responses
    trust_building_recommendations: List[str]
    rapport_risks: List[str]  # Things that could damage trust

@dataclass
class ClosingSignals:
    """Advanced buying signal detection and closing readiness."""
    buying_urgency: float  # 0.0-1.0, immediate purchase intent
    decision_timing: str  # immediate, days, weeks, months, exploring
    closing_readiness_score: float  # 0.0-1.0, ready to make decision
    price_sensitivity: str  # low, medium, high
    negotiation_likelihood: float  # 0.0-1.0
    competitive_pressure: float  # 0.0-1.0, urgency due to other options
    commitment_signals: List[str]  # Verbal commitments or strong interests
    hesitation_signals: List[str]  # Doubts or concerns slowing decision
    optimal_closing_strategy: str  # Strategy recommendation
    timing_recommendation: str  # When to present properties or push decision

class ConversationIntelligenceEngine:
    """
    Advanced conversation intelligence using Claude AI.

    Provides real-time analysis, intent detection, and strategic guidance
    for real estate conversations.
    """

    def __init__(self):
        self.memory_service = MemoryService()
        self.analysis_cache = {}  # Cache recent analyses
        self.cache_ttl = timedelta(minutes=5)  # Cache for 5 minutes

        # Enhanced conversation tracking
        self.conversation_threads = {}  # Dict[str, ConversationThread] - in-memory thread storage
        self.thread_ttl = timedelta(hours=24)  # Threads persist for 24 hours
        self.emotional_transitions = {}  # Track emotional state changes
        self.trust_building_history = {}  # Track trust progression per lead

        # Initialize Claude client
        try:
            from ghl_real_estate_ai.core.llm_client import LLMClient
            from ghl_real_estate_ai.ghl_utils.config import settings

            self.claude_client = LLMClient(
                provider="claude",
                model=settings.claude_model
            )
            self.enabled = True
            logger.info("ConversationIntelligenceEngine initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Claude client: {e}")
            self.claude_client = None
            self.enabled = False

    async def analyze_conversation_realtime(self, messages: List[Dict], lead_context: Dict = None) -> ConversationAnalysis:
        """
        Real-time conversation analysis for agent guidance.

        Args:
            messages: List of conversation messages with 'role', 'content', 'timestamp'
            lead_context: Additional context about the lead

        Returns:
            ConversationAnalysis object with detailed insights
        """
        if not self.enabled:
            return self._get_fallback_analysis()

        # Check cache first
        cache_key = self._generate_cache_key(messages, lead_context)
        if cache_key in self.analysis_cache:
            cached_analysis, timestamp = self.analysis_cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_analysis

        try:
            # Build comprehensive prompt for conversation analysis
            analysis_prompt = self._build_conversation_analysis_prompt(messages, lead_context)

            # Get Claude analysis
            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.3  # Lower temperature for more consistent analysis
            )

            # Parse Claude's response into structured analysis
            analysis = self._parse_claude_analysis(response.content)

            # Cache the result
            self.analysis_cache[cache_key] = (analysis, datetime.now())

            logger.info(f"Conversation analysis completed: intent={analysis.intent_level:.2f}, urgency={analysis.urgency_score:.2f}")
            return analysis

        except Exception as e:
            logger.error(f"Error in conversation analysis: {e}")
            return self._get_fallback_analysis()

    async def extract_intent_signals(self, conversation_history: List[str], lead_profile: Dict = None) -> IntentSignals:
        """
        Deep intent analysis using Claude's conversation understanding.

        Args:
            conversation_history: List of conversation messages
            lead_profile: Lead profile data for context

        Returns:
            IntentSignals object with detailed psychological insights
        """
        if not self.enabled:
            return self._get_fallback_intent_signals()

        try:
            intent_prompt = self._build_intent_analysis_prompt(conversation_history, lead_profile)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": intent_prompt}],
                temperature=0.2
            )

            intent_signals = self._parse_intent_signals(response.content)

            logger.info(f"Intent signals extracted: financial={intent_signals.financial_readiness:.2f}")
            return intent_signals

        except Exception as e:
            logger.error(f"Error extracting intent signals: {e}")
            return self._get_fallback_intent_signals()

    async def generate_response_suggestions(self, context: Dict, conversation_analysis: ConversationAnalysis) -> List[str]:
        """
        Generate contextually appropriate response options.

        Args:
            context: Current conversation context
            conversation_analysis: Previous analysis results

        Returns:
            List of suggested response options
        """
        if not self.enabled:
            return self._get_fallback_suggestions()

        try:
            suggestions_prompt = self._build_suggestions_prompt(context, conversation_analysis)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": suggestions_prompt}],
                temperature=0.7  # Higher temperature for creative suggestions
            )

            suggestions = self._parse_response_suggestions(response.content)

            logger.info(f"Generated {len(suggestions)} response suggestions")
            return suggestions

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return self._get_fallback_suggestions()

    async def predict_conversation_outcome(self, history: List[Dict], lead_context: Dict = None) -> Dict:
        """
        Predict likely conversation outcomes and optimal paths.

        Args:
            history: Conversation history
            lead_context: Lead profile and context

        Returns:
            Dictionary with outcome predictions and recommendations
        """
        if not self.enabled:
            return self._get_fallback_prediction()

        try:
            prediction_prompt = self._build_prediction_prompt(history, lead_context)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": prediction_prompt}],
                temperature=0.4
            )

            prediction = self._parse_outcome_prediction(response.content)

            logger.info(f"Conversation outcome predicted: {prediction.get('primary_outcome', 'unknown')}")
            return prediction

        except Exception as e:
            logger.error(f"Error predicting conversation outcome: {e}")
            return self._get_fallback_prediction()

    async def analyze_conversation_thread(self, thread_id: str, messages: List[Dict],
                                          lead_context: Dict = None) -> Dict:
        """
        Advanced multi-turn conversation analysis with state persistence.

        This is the core enhanced feature that tracks conversation evolution,
        emotional progression, trust building, and closing readiness across
        the entire conversation history.

        Args:
            thread_id: Unique conversation thread identifier
            messages: Complete conversation history
            lead_context: Lead profile and context data

        Returns:
            Comprehensive analysis dictionary with enhanced insights
        """
        if not self.enabled:
            return self._get_fallback_thread_analysis()

        try:
            # Get or create conversation thread
            thread = self._get_or_create_thread(thread_id, messages)

            # Update thread with new messages
            self._update_thread_messages(thread, messages)

            # Perform comprehensive multi-turn analysis
            analysis_results = await self._perform_comprehensive_thread_analysis(
                thread, lead_context
            )

            # Update thread state with new insights
            self._update_thread_state(thread, analysis_results)

            logger.info(f"Thread analysis completed for {thread_id}: "
                       f"health={thread.conversation_health}, "
                       f"closing_readiness={thread.closing_readiness:.2f}")

            return analysis_results

        except Exception as e:
            logger.error(f"Error in thread analysis for {thread_id}: {e}")
            return self._get_fallback_thread_analysis()

    async def analyze_emotional_progression(self, thread_id: str) -> EmotionalState:
        """
        Analyze emotional state progression throughout conversation.

        Args:
            thread_id: Conversation thread identifier

        Returns:
            EmotionalState with detailed emotional analysis
        """
        if not self.enabled or thread_id not in self.conversation_threads:
            return self._get_fallback_emotional_state()

        try:
            thread = self.conversation_threads[thread_id]

            # Build prompt for emotional progression analysis
            emotion_prompt = self._build_emotional_progression_prompt(thread)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": emotion_prompt}],
                temperature=0.3
            )

            emotional_state = self._parse_emotional_state(response.content)

            # Update emotional journey tracking
            self._update_emotional_journey(thread, emotional_state)

            return emotional_state

        except Exception as e:
            logger.error(f"Error analyzing emotional progression: {e}")
            return self._get_fallback_emotional_state()

    async def analyze_trust_metrics(self, thread_id: str) -> TrustMetrics:
        """
        Analyze trust building and rapport development.

        Args:
            thread_id: Conversation thread identifier

        Returns:
            TrustMetrics with rapport and credibility analysis
        """
        if not self.enabled or thread_id not in self.conversation_threads:
            return self._get_fallback_trust_metrics()

        try:
            thread = self.conversation_threads[thread_id]

            # Build trust analysis prompt
            trust_prompt = self._build_trust_analysis_prompt(thread)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": trust_prompt}],
                temperature=0.2  # Lower temperature for consistent trust assessment
            )

            trust_metrics = self._parse_trust_metrics(response.content)

            # Update trust history tracking
            self._update_trust_history(thread, trust_metrics)

            return trust_metrics

        except Exception as e:
            logger.error(f"Error analyzing trust metrics: {e}")
            return self._get_fallback_trust_metrics()

    async def detect_closing_signals(self, thread_id: str) -> ClosingSignals:
        """
        Advanced buying signal detection and closing readiness analysis.

        Args:
            thread_id: Conversation thread identifier

        Returns:
            ClosingSignals with detailed buying intent and timing analysis
        """
        if not self.enabled or thread_id not in self.conversation_threads:
            return self._get_fallback_closing_signals()

        try:
            thread = self.conversation_threads[thread_id]

            # Build closing signals detection prompt
            closing_prompt = self._build_closing_signals_prompt(thread)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": closing_prompt}],
                temperature=0.25
            )

            closing_signals = self._parse_closing_signals(response.content)

            # Update closing readiness in thread
            thread.closing_readiness = closing_signals.closing_readiness_score
            thread.last_updated = datetime.now()

            return closing_signals

        except Exception as e:
            logger.error(f"Error detecting closing signals: {e}")
            return self._get_fallback_closing_signals()

    async def monitor_conversation_health(self, thread_id: str) -> Dict:
        """
        Real-time conversation health monitoring with engagement trends.

        Args:
            thread_id: Conversation thread identifier

        Returns:
            Dictionary with health metrics and trend analysis
        """
        if thread_id not in self.conversation_threads:
            return {"health": "unknown", "engagement_trend": "unknown"}

        try:
            thread = self.conversation_threads[thread_id]

            # Calculate engagement metrics
            health_metrics = self._calculate_conversation_health_metrics(thread)

            # Analyze trends over time
            trend_analysis = self._analyze_engagement_trends(thread)

            # Update thread health status
            thread.conversation_health = health_metrics["overall_health"]
            thread.engagement_metrics.update(health_metrics["metrics"])

            return {
                "health": health_metrics["overall_health"],
                "engagement_trend": trend_analysis["trend"],
                "health_score": health_metrics["health_score"],
                "engagement_metrics": health_metrics["metrics"],
                "trend_indicators": trend_analysis["indicators"],
                "recommendations": health_metrics["recommendations"]
            }

        except Exception as e:
            logger.error(f"Error monitoring conversation health: {e}")
            return {"health": "unknown", "engagement_trend": "unknown"}

    # ========== ENHANCED THREAD MANAGEMENT METHODS ==========

    def _get_or_create_thread(self, thread_id: str, messages: List[Dict]) -> ConversationThread:
        """Get existing thread or create new one."""
        if thread_id in self.conversation_threads:
            # Clean up expired threads
            thread = self.conversation_threads[thread_id]
            if datetime.now() - thread.last_updated > self.thread_ttl:
                del self.conversation_threads[thread_id]
                return self._create_new_thread(thread_id, messages)
            return thread
        else:
            return self._create_new_thread(thread_id, messages)

    def _create_new_thread(self, thread_id: str, messages: List[Dict]) -> ConversationThread:
        """Create new conversation thread."""
        thread = ConversationThread(
            thread_id=thread_id,
            messages=messages.copy(),
            intent_evolution=[],
            emotional_journey=[],
            trust_score_history=[],
            objection_patterns=[],
            engagement_metrics={
                "avg_response_time": 0.0,
                "message_length_trend": 0.0,
                "engagement_score": 0.5,
                "responsiveness": 0.5
            },
            conversation_health="good",
            closing_readiness=0.3,
            last_updated=datetime.now()
        )
        self.conversation_threads[thread_id] = thread
        return thread

    def _update_thread_messages(self, thread: ConversationThread, messages: List[Dict]) -> None:
        """Update thread with new messages."""
        # Only add truly new messages
        existing_count = len(thread.messages)
        if len(messages) > existing_count:
            new_messages = messages[existing_count:]
            thread.messages.extend(new_messages)
            thread.last_updated = datetime.now()

    async def _perform_comprehensive_thread_analysis(self, thread: ConversationThread,
                                                    lead_context: Dict = None) -> Dict:
        """Perform comprehensive multi-turn analysis."""
        try:
            # Build comprehensive thread analysis prompt
            thread_prompt = self._build_thread_analysis_prompt(thread, lead_context)

            response = await self.claude_client.chat(
                messages=[{"role": "user", "content": thread_prompt}],
                temperature=0.3
            )

            analysis = self._parse_thread_analysis(response.content)

            # Parallel analysis of specific aspects
            emotional_analysis = await self.analyze_emotional_progression(thread.thread_id)
            trust_analysis = await self.analyze_trust_metrics(thread.thread_id)
            closing_analysis = await self.detect_closing_signals(thread.thread_id)

            # Combine all analyses
            comprehensive_analysis = {
                "thread_analysis": analysis,
                "emotional_state": emotional_analysis,
                "trust_metrics": trust_analysis,
                "closing_signals": closing_analysis,
                "conversation_health": thread.conversation_health,
                "thread_id": thread.thread_id,
                "analysis_timestamp": datetime.now()
            }

            return comprehensive_analysis

        except Exception as e:
            logger.error(f"Error in comprehensive thread analysis: {e}")
            return self._get_fallback_thread_analysis()

    def _update_thread_state(self, thread: ConversationThread, analysis_results: Dict) -> None:
        """Update thread state with analysis results."""
        try:
            # Update intent evolution
            current_intent = analysis_results.get("thread_analysis", {}).get("intent_level", 0.5)
            thread.intent_evolution.append((datetime.now(), current_intent))

            # Update conversation health
            health = analysis_results.get("thread_analysis", {}).get("conversation_health", "good")
            thread.conversation_health = health

            # Update closing readiness
            closing_signals = analysis_results.get("closing_signals")
            if closing_signals:
                thread.closing_readiness = closing_signals.closing_readiness_score

            thread.last_updated = datetime.now()

        except Exception as e:
            logger.error(f"Error updating thread state: {e}")

    def _update_emotional_journey(self, thread: ConversationThread,
                                 emotional_state: EmotionalState) -> None:
        """Update emotional journey tracking."""
        thread.emotional_journey.append((
            datetime.now(),
            emotional_state.primary_emotion,
            emotional_state.emotion_intensity
        ))

    def _update_trust_history(self, thread: ConversationThread, trust_metrics: TrustMetrics) -> None:
        """Update trust building history."""
        thread.trust_score_history.append((datetime.now(), trust_metrics.overall_trust_score))

    def _calculate_conversation_health_metrics(self, thread: ConversationThread) -> Dict:
        """Calculate conversation health metrics."""
        try:
            messages = thread.messages
            if not messages:
                return {
                    "overall_health": "unknown",
                    "health_score": 0.5,
                    "metrics": {},
                    "recommendations": []
                }

            # Calculate engagement metrics
            total_messages = len(messages)
            agent_messages = [m for m in messages if m.get('role') == 'agent']
            lead_messages = [m for m in messages if m.get('role') == 'lead']

            engagement_score = min(len(lead_messages) / max(len(agent_messages), 1), 2.0) * 0.5
            avg_message_length = sum(len(m.get('content', '')) for m in lead_messages) / max(len(lead_messages), 1)

            # Calculate response patterns
            response_consistency = 1.0 if len(lead_messages) > 2 else 0.5

            # Overall health score
            health_score = (engagement_score + response_consistency + thread.closing_readiness) / 3

            # Determine health status
            if health_score >= 0.8:
                overall_health = "excellent"
            elif health_score >= 0.6:
                overall_health = "good"
            elif health_score >= 0.4:
                overall_health = "concerning"
            else:
                overall_health = "poor"

            metrics = {
                "total_messages": total_messages,
                "engagement_score": engagement_score,
                "avg_message_length": avg_message_length,
                "response_consistency": response_consistency,
                "closing_readiness": thread.closing_readiness
            }

            recommendations = self._generate_health_recommendations(overall_health, metrics)

            return {
                "overall_health": overall_health,
                "health_score": health_score,
                "metrics": metrics,
                "recommendations": recommendations
            }

        except Exception as e:
            logger.error(f"Error calculating health metrics: {e}")
            return {
                "overall_health": "unknown",
                "health_score": 0.5,
                "metrics": {},
                "recommendations": []
            }

    def _analyze_engagement_trends(self, thread: ConversationThread) -> Dict:
        """Analyze engagement trends over time."""
        try:
            if len(thread.intent_evolution) < 2:
                return {"trend": "insufficient_data", "indicators": []}

            # Analyze intent progression
            recent_intents = [intent for _, intent in thread.intent_evolution[-5:]]
            if len(recent_intents) >= 2:
                intent_trend = "increasing" if recent_intents[-1] > recent_intents[0] else "decreasing"
            else:
                intent_trend = "stable"

            # Analyze emotional progression
            emotional_trend = "stable"
            if len(thread.emotional_journey) >= 3:
                recent_emotions = thread.emotional_journey[-3:]
                positive_emotions = ["excited", "confident", "interested"]
                negative_emotions = ["frustrated", "overwhelmed", "cautious"]

                positive_count = sum(1 for _, emotion, _ in recent_emotions if emotion in positive_emotions)
                negative_count = sum(1 for _, emotion, _ in recent_emotions if emotion in negative_emotions)

                if positive_count > negative_count:
                    emotional_trend = "improving"
                elif negative_count > positive_count:
                    emotional_trend = "declining"

            # Combine trends
            if intent_trend == "increasing" and emotional_trend == "improving":
                overall_trend = "improving"
            elif intent_trend == "decreasing" or emotional_trend == "declining":
                overall_trend = "declining"
            else:
                overall_trend = "stable"

            indicators = []
            if intent_trend == "increasing":
                indicators.append("Rising buying intent")
            if emotional_trend == "improving":
                indicators.append("Positive emotional progression")
            if len(thread.trust_score_history) >= 2 and thread.trust_score_history[-1][1] > thread.trust_score_history[-2][1]:
                indicators.append("Building trust and rapport")

            return {
                "trend": overall_trend,
                "intent_trend": intent_trend,
                "emotional_trend": emotional_trend,
                "indicators": indicators
            }

        except Exception as e:
            logger.error(f"Error analyzing engagement trends: {e}")
            return {"trend": "unknown", "indicators": []}

    def _generate_health_recommendations(self, health_status: str, metrics: Dict) -> List[str]:
        """Generate recommendations based on conversation health."""
        recommendations = []

        if health_status == "poor":
            recommendations.extend([
                "Consider re-engaging with value-driven content",
                "Ask open-ended questions to encourage participation",
                "Address any unstated concerns or objections"
            ])
        elif health_status == "concerning":
            recommendations.extend([
                "Focus on building rapport and trust",
                "Provide more personalized responses",
                "Consider scheduling a phone call for better engagement"
            ])
        elif health_status == "good":
            recommendations.extend([
                "Continue current approach - conversation is healthy",
                "Look for opportunities to introduce relevant properties",
                "Begin qualifying timeline and budget if not done"
            ])
        else:  # excellent
            recommendations.extend([
                "Strong engagement - consider moving to next phase",
                "Present curated property options",
                "Schedule property viewings or deeper consultation"
            ])

        return recommendations

    def _build_conversation_analysis_prompt(self, messages: List[Dict], lead_context: Dict = None) -> str:
        """Build comprehensive prompt for conversation analysis."""

        # Format conversation history
        conversation_text = "\\n".join([
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in messages[-10:]  # Last 10 messages for context
        ])

        # Add lead context if available
        context_text = ""
        if lead_context:
            context_text = f"\\nLead Profile: {json.dumps(lead_context, indent=2)}"

        return f"""
You are an expert real estate conversation analyst. Analyze this conversation for buying intent and provide strategic guidance.

Conversation History:
{conversation_text}
{context_text}

Provide a detailed analysis in JSON format with these fields:
{{
    "intent_level": float (0.0-1.0, where 1.0 is extremely high buying intent),
    "urgency_score": float (0.0-1.0, how urgent is their timeline),
    "objection_type": string or null (primary objection: "budget", "timeline", "features", "location", "financing", "decision_maker", null),
    "recommended_response": string (specific response strategy),
    "property_readiness": string ("low", "medium", "high" - ready to view properties),
    "next_best_action": string (immediate next step recommendation),
    "confidence": float (0.0-1.0, confidence in this analysis),
    "key_insights": [list of 2-3 most important insights],
    "emotional_state": string ("excited", "cautious", "frustrated", "analytical", "overwhelmed"),
    "decision_timeline": string ("immediate", "within_week", "within_month", "exploring", "unknown")
}}

Focus on psychological signals, hidden motivations, and actionable guidance for the agent.
"""

    def _build_intent_analysis_prompt(self, conversation_history: List[str], lead_profile: Dict = None) -> str:
        """Build prompt for deep intent signal extraction."""

        conversation_text = "\\n".join(conversation_history[-15:])  # Last 15 messages

        profile_text = ""
        if lead_profile:
            profile_text = f"\\nLead Profile: {json.dumps(lead_profile, indent=2)}"

        return f"""
As a real estate psychology expert, analyze this conversation for deep buying intent signals.

Conversation:
{conversation_text}
{profile_text}

Extract detailed psychological insights in JSON format:
{{
    "financial_readiness": float (0.0-1.0, ability and willingness to purchase),
    "timeline_urgency": float (0.0-1.0, how soon they need to buy),
    "decision_authority": float (0.0-1.0, their role in the buying decision),
    "emotional_investment": float (0.0-1.0, attachment to the buying process),
    "hidden_concerns": [list of unstated objections or fears],
    "lifestyle_indicators": {{
        "family_focused": float (0.0-1.0),
        "career_driven": float (0.0-1.0),
        "investment_minded": float (0.0-1.0),
        "status_conscious": float (0.0-1.0),
        "security_focused": float (0.0-1.0),
        "convenience_seeking": float (0.0-1.0)
    }},
    "communication_style": string ("analytical", "emotional", "direct", "collaborative", "skeptical"),
    "motivation_drivers": [list of primary motivating factors],
    "risk_tolerance": string ("low", "medium", "high"),
    "research_behavior": string ("thorough", "moderate", "impulsive", "delegator")
}}

Look for subtle signals, unstated preferences, and psychological motivations.
"""

    def _build_suggestions_prompt(self, context: Dict, analysis: ConversationAnalysis) -> str:
        """Build prompt for generating response suggestions."""

        return f"""
As a real estate conversation expert, provide response suggestions based on this analysis:

Current Analysis:
- Intent Level: {analysis.intent_level:.2f}
- Urgency Score: {analysis.urgency_score:.2f}
- Objection Type: {analysis.objection_type}
- Property Readiness: {analysis.property_readiness}
- Next Best Action: {analysis.next_best_action}

Context:
{json.dumps(context, indent=2)}

Generate 3-5 response options in JSON format:
{{
    "suggestions": [
        {{
            "response": "Specific response text",
            "strategy": "Brief strategy explanation",
            "expected_outcome": "What this might achieve",
            "confidence": float (0.0-1.0)
        }}
    ],
    "priority_suggestion": "Which suggestion to try first",
    "follow_up_timing": "When to send follow-up",
    "escalation_triggers": [list of signals that require human intervention]
}}

Focus on responses that:
1. Address the identified objection or concern
2. Move the conversation toward the next best action
3. Match the lead's communication style and emotional state
4. Provide value and build trust
"""

    def _build_prediction_prompt(self, history: List[Dict], lead_context: Dict = None) -> str:
        """Build prompt for conversation outcome prediction."""

        recent_messages = history[-8:]  # Last 8 messages
        conversation_summary = "\\n".join([
            f"{msg.get('role', '').upper()}: {msg.get('content', '')[:100]}..."
            for msg in recent_messages
        ])

        context_text = ""
        if lead_context:
            context_text = f"\\nLead Context: {json.dumps(lead_context, indent=2)}"

        return f"""
As a real estate conversation strategist, predict the likely outcomes of this conversation.

Recent Conversation:
{conversation_summary}
{context_text}

Predict outcomes in JSON format:
{{
    "primary_outcome": string ("appointment_scheduled", "follow_up_needed", "objection_surfaced", "information_gathering", "nurturing_required", "disqualified"),
    "probability": float (0.0-1.0, confidence in primary outcome),
    "alternative_outcomes": [
        {{
            "outcome": string,
            "probability": float
        }}
    ],
    "timeline_to_outcome": string ("immediate", "within_24h", "within_week", "longer_term"),
    "success_factors": [list of factors that increase success probability],
    "risk_factors": [list of factors that could derail the conversation],
    "optimization_recommendations": [list of strategies to improve outcomes],
    "conversation_health": string ("excellent", "good", "concerning", "poor"),
    "engagement_trend": string ("increasing", "stable", "decreasing"),
    "next_conversation_strategy": string (strategy for next interaction)
}}

Consider conversation momentum, engagement patterns, and buying signals.
"""

    # ========== ENHANCED PROMPT BUILDING METHODS ==========

    def _build_thread_analysis_prompt(self, thread: ConversationThread, lead_context: Dict = None) -> str:
        """Build comprehensive thread analysis prompt for multi-turn conversations."""

        # Format complete conversation history
        conversation_text = "\\n".join([
            f"[{msg.get('timestamp', 'Unknown')}] {msg.get('role', 'unknown').upper()}: {msg.get('content', '')}"
            for msg in thread.messages
        ])

        # Add historical context
        intent_history = ""
        if thread.intent_evolution:
            recent_intents = thread.intent_evolution[-5:]
            intent_history = f"\\nIntent Evolution: {', '.join([f'{timestamp.strftime('%H:%M')}:{intent:.2f}' for timestamp, intent in recent_intents])}"

        emotional_history = ""
        if thread.emotional_journey:
            recent_emotions = thread.emotional_journey[-3:]
            emotional_history = f"\\nEmotional Journey: {', '.join([f'{timestamp.strftime('%H:%M')}:{emotion}({intensity:.1f})' for timestamp, emotion, intensity in recent_emotions])}"

        context_text = ""
        if lead_context:
            context_text = f"\\nLead Profile: {json.dumps(lead_context, indent=2)}"

        return f"""
You are an expert real estate conversation analyst specializing in multi-turn conversation intelligence.
Analyze this COMPLETE conversation thread for comprehensive insights and strategic guidance.

Thread ID: {thread.thread_id}
Conversation History (chronological):
{conversation_text}
{intent_history}
{emotional_history}
{context_text}

Current Thread Metrics:
- Messages: {len(thread.messages)}
- Current Health: {thread.conversation_health}
- Current Closing Readiness: {thread.closing_readiness:.2f}

Provide comprehensive analysis in JSON format:
{{
    "intent_level": float (0.0-1.0, current buying intent based on entire thread),
    "intent_progression": string ("rising", "stable", "declining", "volatile"),
    "conversation_momentum": float (0.0-1.0, forward movement toward purchase),
    "engagement_quality": string ("excellent", "good", "fair", "poor"),
    "trust_building_progress": float (0.0-1.0, rapport development over time),
    "objection_patterns": [{{
        "objection": string,
        "frequency": int,
        "resolution_status": string ("resolved", "ongoing", "escalating"),
        "impact": string ("low", "medium", "high")
    }}],
    "conversation_health": string ("excellent", "good", "concerning", "poor"),
    "closing_readiness": float (0.0-1.0, readiness to make purchase decision),
    "next_phase_recommendation": string (specific next step),
    "thread_insights": [list of 3-5 key insights from complete conversation],
    "strategic_opportunities": [list of opportunities to advance the conversation],
    "risk_factors": [list of potential conversation risks or concerns]
}}

Focus on patterns that emerge across the entire conversation thread, not just recent messages.
"""

    def _build_emotional_progression_prompt(self, thread: ConversationThread) -> str:
        """Build prompt for emotional progression analysis."""

        # Recent messages for emotional context
        recent_messages = thread.messages[-10:] if len(thread.messages) > 10 else thread.messages
        conversation_text = "\\n".join([
            f"{msg.get('role', '').upper()}: {msg.get('content', '')}"
            for msg in recent_messages
        ])

        # Historical emotional context
        emotional_context = ""
        if thread.emotional_journey:
            emotional_context = f"\\nPrevious Emotions: {', '.join([f'{emotion}({intensity:.1f})' for _, emotion, intensity in thread.emotional_journey])}"

        return f"""
As a real estate psychology expert, analyze the emotional progression in this conversation thread.

Thread ID: {thread.thread_id}
Recent Conversation:
{conversation_text}
{emotional_context}

Analyze emotional state and progression in JSON format:
{{
    "primary_emotion": string ("excited", "cautious", "frustrated", "analytical", "overwhelmed", "confident", "interested", "skeptical"),
    "emotion_intensity": float (0.0-1.0, strength of primary emotion),
    "secondary_emotions": [
        {{"emotion": string, "intensity": float}}
    ],
    "emotional_trajectory": string ("improving", "stable", "declining", "volatile"),
    "empathy_score": float (0.0-1.0, how well agent is connecting emotionally),
    "stress_indicators": [list of signs showing stress or pressure],
    "excitement_indicators": [list of signs showing enthusiasm or interest],
    "trust_indicators": [list of signs showing building trust/rapport],
    "decision_readiness": float (0.0-1.0, psychological readiness to make decisions),
    "emotional_triggers": [list of topics/approaches that evoke strong responses],
    "optimal_emotional_approach": string (recommended emotional strategy),
    "empathy_recommendations": [specific ways to improve emotional connection]
}}

Look for subtle emotional cues, energy shifts, and psychological readiness indicators.
"""

    def _build_trust_analysis_prompt(self, thread: ConversationThread) -> str:
        """Build prompt for trust and rapport analysis."""

        conversation_text = "\\n".join([
            f"{msg.get('role', '').upper()}: {msg.get('content', '')}"
            for msg in thread.messages[-15:]  # Last 15 messages for trust context
        ])

        trust_context = ""
        if thread.trust_score_history:
            trust_context = f"\\nTrust History: {', '.join([f'{score:.2f}' for _, score in thread.trust_score_history])}"

        return f"""
As a real estate relationship expert, analyze trust building and rapport in this conversation.

Thread ID: {thread.thread_id}
Conversation Context:
{conversation_text}
{trust_context}

Analyze trust and rapport in JSON format:
{{
    "overall_trust_score": float (0.0-1.0, comprehensive trust level),
    "rapport_level": string ("building", "established", "strong", "excellent"),
    "credibility_score": float (0.0-1.0, perceived agent expertise and reliability),
    "communication_alignment": float (0.0-1.0, style matching and understanding),
    "value_demonstration": float (0.0-1.0, perceived value and helpfulness),
    "responsiveness_score": float (0.0-1.0, timely and relevant responses),
    "trust_building_recommendations": [specific actions to strengthen trust],
    "rapport_risks": [potential trust-damaging behaviors to avoid],
    "credibility_factors": [specific elements building or undermining credibility],
    "relationship_stage": string ("initial", "developing", "established", "partnership"),
    "trust_acceleration_opportunities": [ways to build trust faster],
    "vulnerability_indicators": [signs the lead is opening up or sharing concerns]
}}

Focus on subtle trust signals, credibility indicators, and relationship dynamics.
"""

    def _build_closing_signals_prompt(self, thread: ConversationThread) -> str:
        """Build prompt for closing signals and buying readiness analysis."""

        conversation_text = "\\n".join([
            f"{msg.get('role', '').upper()}: {msg.get('content', '')}"
            for msg in thread.messages
        ])

        return f"""
As a real estate closing expert, analyze buying signals and closing readiness in this conversation.

Thread ID: {thread.thread_id}
Complete Conversation:
{conversation_text}

Analyze closing signals and buying readiness in JSON format:
{{
    "buying_urgency": float (0.0-1.0, immediate purchase intent and urgency),
    "decision_timing": string ("immediate", "days", "weeks", "months", "exploring"),
    "closing_readiness_score": float (0.0-1.0, readiness to make purchase decision),
    "price_sensitivity": string ("low", "medium", "high"),
    "negotiation_likelihood": float (0.0-1.0, probability they'll negotiate),
    "competitive_pressure": float (0.0-1.0, urgency due to other options or market),
    "commitment_signals": [specific verbal commitments or strong interest indicators],
    "hesitation_signals": [doubts, concerns, or factors slowing decision],
    "financial_readiness_indicators": [signs of financial preparation or capability],
    "decision_maker_confirmation": float (0.0-1.0, confirmed decision-making authority),
    "optimal_closing_strategy": string (recommended approach for moving to purchase),
    "timing_recommendation": string (when to present properties or push decision),
    "closing_acceleration_tactics": [specific methods to speed up decision],
    "objection_prevention": [anticipated objections and how to address them proactively]
}}

Look for micro-commitments, buying language, urgency indicators, and decision-making patterns.
"""

    def _parse_claude_analysis(self, response_content: str) -> ConversationAnalysis:
        """Parse Claude's response into ConversationAnalysis object."""
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                # Fallback parsing if no JSON found
                data = self._extract_fallback_analysis(response_content)

            return ConversationAnalysis(
                intent_level=float(data.get('intent_level', 0.5)),
                urgency_score=float(data.get('urgency_score', 0.5)),
                objection_type=data.get('objection_type'),
                recommended_response=data.get('recommended_response', 'Continue building rapport'),
                property_readiness=data.get('property_readiness', 'medium'),
                next_best_action=data.get('next_best_action', 'Gather more information'),
                confidence=float(data.get('confidence', 0.7)),
                analysis_timestamp=datetime.now()
            )
        except Exception as e:
            logger.error(f"Error parsing Claude analysis: {e}")
            return self._get_fallback_analysis()

    def _parse_intent_signals(self, response_content: str) -> IntentSignals:
        """Parse Claude's intent analysis response."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            lifestyle_indicators = data.get('lifestyle_indicators', {})

            return IntentSignals(
                financial_readiness=float(data.get('financial_readiness', 0.5)),
                timeline_urgency=float(data.get('timeline_urgency', 0.5)),
                decision_authority=float(data.get('decision_authority', 0.5)),
                emotional_investment=float(data.get('emotional_investment', 0.5)),
                hidden_concerns=data.get('hidden_concerns', []),
                lifestyle_indicators={
                    k: float(v) for k, v in lifestyle_indicators.items()
                }
            )
        except Exception as e:
            logger.error(f"Error parsing intent signals: {e}")
            return self._get_fallback_intent_signals()

    def _parse_response_suggestions(self, response_content: str) -> List[str]:
        """Parse response suggestions from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                suggestions_data = data.get('suggestions', [])
                return [s.get('response', '') for s in suggestions_data]
            else:
                # Extract suggestions from text if no JSON
                lines = response_content.split('\\n')
                suggestions = []
                for line in lines:
                    if line.strip().startswith(('1.', '2.', '3.', '-', '•')):
                        suggestions.append(line.strip())
                return suggestions[:5]  # Limit to 5 suggestions
        except Exception as e:
            logger.error(f"Error parsing response suggestions: {e}")
            return self._get_fallback_suggestions()

    def _parse_outcome_prediction(self, response_content: str) -> Dict:
        """Parse outcome prediction from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                return {
                    "primary_outcome": "information_gathering",
                    "probability": 0.6,
                    "timeline_to_outcome": "within_24h",
                    "conversation_health": "good"
                }
        except Exception as e:
            logger.error(f"Error parsing outcome prediction: {e}")
            return self._get_fallback_prediction()

    # ========== ENHANCED PARSING METHODS ==========

    def _parse_thread_analysis(self, response_content: str) -> Dict:
        """Parse comprehensive thread analysis from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            return {
                "intent_level": float(data.get("intent_level", 0.5)),
                "intent_progression": data.get("intent_progression", "stable"),
                "conversation_momentum": float(data.get("conversation_momentum", 0.5)),
                "engagement_quality": data.get("engagement_quality", "good"),
                "trust_building_progress": float(data.get("trust_building_progress", 0.5)),
                "objection_patterns": data.get("objection_patterns", []),
                "conversation_health": data.get("conversation_health", "good"),
                "closing_readiness": float(data.get("closing_readiness", 0.3)),
                "next_phase_recommendation": data.get("next_phase_recommendation", "Continue conversation"),
                "thread_insights": data.get("thread_insights", []),
                "strategic_opportunities": data.get("strategic_opportunities", []),
                "risk_factors": data.get("risk_factors", [])
            }
        except Exception as e:
            logger.error(f"Error parsing thread analysis: {e}")
            return self._get_fallback_thread_analysis()

    def _parse_emotional_state(self, response_content: str) -> EmotionalState:
        """Parse emotional state analysis from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            # Parse secondary emotions
            secondary_emotions = []
            for emotion_data in data.get("secondary_emotions", []):
                if isinstance(emotion_data, dict):
                    secondary_emotions.append((
                        emotion_data.get("emotion", "neutral"),
                        float(emotion_data.get("intensity", 0.3))
                    ))

            return EmotionalState(
                primary_emotion=data.get("primary_emotion", "analytical"),
                emotion_intensity=float(data.get("emotion_intensity", 0.5)),
                secondary_emotions=secondary_emotions,
                emotional_trajectory=data.get("emotional_trajectory", "stable"),
                empathy_score=float(data.get("empathy_score", 0.5)),
                stress_indicators=data.get("stress_indicators", []),
                excitement_indicators=data.get("excitement_indicators", []),
                trust_indicators=data.get("trust_indicators", []),
                decision_readiness=float(data.get("decision_readiness", 0.5))
            )
        except Exception as e:
            logger.error(f"Error parsing emotional state: {e}")
            return self._get_fallback_emotional_state()

    def _parse_trust_metrics(self, response_content: str) -> TrustMetrics:
        """Parse trust metrics analysis from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            return TrustMetrics(
                overall_trust_score=float(data.get("overall_trust_score", 0.5)),
                rapport_level=data.get("rapport_level", "building"),
                credibility_score=float(data.get("credibility_score", 0.5)),
                communication_alignment=float(data.get("communication_alignment", 0.5)),
                value_demonstration=float(data.get("value_demonstration", 0.5)),
                responsiveness_score=float(data.get("responsiveness_score", 0.5)),
                trust_building_recommendations=data.get("trust_building_recommendations", []),
                rapport_risks=data.get("rapport_risks", [])
            )
        except Exception as e:
            logger.error(f"Error parsing trust metrics: {e}")
            return self._get_fallback_trust_metrics()

    def _parse_closing_signals(self, response_content: str) -> ClosingSignals:
        """Parse closing signals analysis from Claude."""
        try:
            import re
            json_match = re.search(r'\\{.*\\}', response_content, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = {}

            return ClosingSignals(
                buying_urgency=float(data.get("buying_urgency", 0.3)),
                decision_timing=data.get("decision_timing", "exploring"),
                closing_readiness_score=float(data.get("closing_readiness_score", 0.3)),
                price_sensitivity=data.get("price_sensitivity", "medium"),
                negotiation_likelihood=float(data.get("negotiation_likelihood", 0.5)),
                competitive_pressure=float(data.get("competitive_pressure", 0.3)),
                commitment_signals=data.get("commitment_signals", []),
                hesitation_signals=data.get("hesitation_signals", []),
                optimal_closing_strategy=data.get("optimal_closing_strategy", "Build more rapport"),
                timing_recommendation=data.get("timing_recommendation", "Continue qualifying")
            )
        except Exception as e:
            logger.error(f"Error parsing closing signals: {e}")
            return self._get_fallback_closing_signals()

    # ========== ENHANCED FALLBACK METHODS ==========

    def _get_fallback_thread_analysis(self) -> Dict:
        """Get fallback thread analysis when Claude is unavailable."""
        return {
            "intent_level": 0.5,
            "intent_progression": "stable",
            "conversation_momentum": 0.5,
            "engagement_quality": "good",
            "trust_building_progress": 0.5,
            "objection_patterns": [],
            "conversation_health": "good",
            "closing_readiness": 0.3,
            "next_phase_recommendation": "Continue building rapport and gathering information",
            "thread_insights": ["Insufficient data for detailed analysis"],
            "strategic_opportunities": ["Build rapport", "Qualify needs"],
            "risk_factors": ["Limited conversation data"]
        }

    def _get_fallback_emotional_state(self) -> EmotionalState:
        """Get fallback emotional state."""
        return EmotionalState(
            primary_emotion="analytical",
            emotion_intensity=0.5,
            secondary_emotions=[("curious", 0.3), ("cautious", 0.2)],
            emotional_trajectory="stable",
            empathy_score=0.5,
            stress_indicators=[],
            excitement_indicators=[],
            trust_indicators=[],
            decision_readiness=0.5
        )

    def _get_fallback_trust_metrics(self) -> TrustMetrics:
        """Get fallback trust metrics."""
        return TrustMetrics(
            overall_trust_score=0.5,
            rapport_level="building",
            credibility_score=0.5,
            communication_alignment=0.5,
            value_demonstration=0.5,
            responsiveness_score=0.5,
            trust_building_recommendations=[
                "Provide valuable market insights",
                "Respond promptly to questions",
                "Show expertise through detailed answers"
            ],
            rapport_risks=[
                "Being too pushy too early",
                "Not listening to stated concerns",
                "Generic responses without personalization"
            ]
        )

    def _get_fallback_closing_signals(self) -> ClosingSignals:
        """Get fallback closing signals."""
        return ClosingSignals(
            buying_urgency=0.3,
            decision_timing="exploring",
            closing_readiness_score=0.3,
            price_sensitivity="medium",
            negotiation_likelihood=0.5,
            competitive_pressure=0.3,
            commitment_signals=["Asking about properties"],
            hesitation_signals=["Need to think about it"],
            optimal_closing_strategy="Build trust and rapport first",
            timing_recommendation="Continue qualifying before presenting properties"
        )

    def _generate_cache_key(self, messages: List[Dict], lead_context: Dict = None) -> str:
        """Generate cache key for analysis results."""
        messages_hash = hash(str(messages[-5:]))  # Hash last 5 messages
        context_hash = hash(str(lead_context)) if lead_context else 0
        return f"{messages_hash}_{context_hash}"

    def _get_fallback_analysis(self) -> ConversationAnalysis:
        """Get fallback analysis when Claude is unavailable."""
        return ConversationAnalysis(
            intent_level=0.6,
            urgency_score=0.5,
            objection_type=None,
            recommended_response="Continue building rapport and gathering information",
            property_readiness="medium",
            next_best_action="Ask qualifying questions",
            confidence=0.5,
            analysis_timestamp=datetime.now()
        )

    def _get_fallback_intent_signals(self) -> IntentSignals:
        """Get fallback intent signals."""
        return IntentSignals(
            financial_readiness=0.5,
            timeline_urgency=0.5,
            decision_authority=0.5,
            emotional_investment=0.5,
            hidden_concerns=["Budget concerns", "Timeline uncertainty"],
            lifestyle_indicators={
                "family_focused": 0.5,
                "career_driven": 0.5,
                "investment_minded": 0.3,
                "status_conscious": 0.3,
                "security_focused": 0.6,
                "convenience_seeking": 0.5
            }
        )

    def _get_fallback_suggestions(self) -> List[str]:
        """Get fallback suggestions."""
        return [
            "Ask about their ideal timeline for making a decision",
            "Inquire about their budget range and financing status",
            "Discuss their must-have features and preferences",
            "Offer to schedule a property viewing",
            "Provide market insights relevant to their interests"
        ]

    def _get_fallback_prediction(self) -> Dict:
        """Get fallback prediction."""
        return {
            "primary_outcome": "information_gathering",
            "probability": 0.6,
            "alternative_outcomes": [
                {"outcome": "follow_up_needed", "probability": 0.3}
            ],
            "timeline_to_outcome": "within_24h",
            "conversation_health": "good",
            "engagement_trend": "stable",
            "next_conversation_strategy": "Continue building rapport"
        }

    def render_enhanced_intelligence_dashboard(self, thread_id: str, messages: List[Dict],
                                             lead_context: Dict = None) -> None:
        """
        Render comprehensive enhanced conversation intelligence dashboard.

        This is the main UI method that showcases all enhanced features:
        - Multi-turn conversation analysis
        - Emotional progression tracking
        - Trust building metrics
        - Advanced closing signals
        - Conversation health monitoring

        Args:
            thread_id: Conversation thread identifier
            messages: Current conversation messages
            lead_context: Lead profile and context
        """
        if not self.enabled:
            st.error("🤖 Enhanced Conversation Intelligence requires Claude API access")
            return

        if not messages or len(messages) < 2:
            st.info("🧠 Start a conversation to see enhanced intelligence analysis")
            return

        # Run enhanced analysis
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        st.markdown("## 🧠 Enhanced Conversation Intelligence Dashboard")

        # Main analysis tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📊 Thread Analysis",
            "💭 Emotional State",
            "🤝 Trust & Rapport",
            "🎯 Closing Signals",
            "📈 Health Monitor"
        ])

        with tab1:
            st.markdown("### 🔍 Multi-Turn Conversation Analysis")

            with st.spinner("🧠 Analyzing complete conversation thread..."):
                thread_analysis = loop.run_until_complete(
                    self.analyze_conversation_thread(thread_id, messages, lead_context)
                )

            # Key metrics row
            col1, col2, col3, col4 = st.columns(4)

            thread_data = thread_analysis.get("thread_analysis", {})

            with col1:
                intent_level = thread_data.get("intent_level", 0.5)
                st.metric(
                    "Intent Level",
                    f"{intent_level:.0%}",
                    delta=f"Progression: {thread_data.get('intent_progression', 'stable').title()}"
                )

            with col2:
                momentum = thread_data.get("conversation_momentum", 0.5)
                st.metric("Momentum", f"{momentum:.0%}")

            with col3:
                closing = thread_data.get("closing_readiness", 0.3)
                st.metric("Closing Readiness", f"{closing:.0%}")

            with col4:
                health = thread_data.get("conversation_health", "good")
                health_emoji = "🟢" if health == "excellent" else "🟡" if health == "good" else "🟠" if health == "concerning" else "🔴"
                st.metric("Health", f"{health_emoji} {health.title()}")

            # Strategic insights
            st.markdown("#### 💡 Thread Insights")
            insights = thread_data.get("thread_insights", [])
            for insight in insights[:3]:  # Show top 3 insights
                st.info(f"💡 {insight}")

            # Strategic opportunities
            if thread_data.get("strategic_opportunities"):
                st.markdown("#### 🎯 Strategic Opportunities")
                for opportunity in thread_data.get("strategic_opportunities", [])[:3]:
                    st.success(f"🎯 {opportunity}")

            # Risk factors
            if thread_data.get("risk_factors"):
                st.markdown("#### ⚠️ Risk Factors")
                for risk in thread_data.get("risk_factors", [])[:2]:
                    st.warning(f"⚠️ {risk}")

            st.markdown(f"**Next Phase:** {thread_data.get('next_phase_recommendation', 'Continue conversation')}")

        with tab2:
            st.markdown("### 💭 Emotional Progression Analysis")

            with st.spinner("🧠 Analyzing emotional state..."):
                emotional_state = loop.run_until_complete(
                    self.analyze_emotional_progression(thread_id)
                )

            # Emotional metrics
            col1, col2, col3 = st.columns(3)

            with col1:
                emotion_emoji = {"excited": "😊", "cautious": "🤔", "frustrated": "😤",
                               "analytical": "🧐", "confident": "😎", "interested": "👀"}.get(
                    emotional_state.primary_emotion, "😐"
                )
                st.metric(
                    "Primary Emotion",
                    f"{emotion_emoji} {emotional_state.primary_emotion.title()}",
                    delta=f"Intensity: {emotional_state.emotion_intensity:.1f}"
                )

            with col2:
                trajectory_emoji = {"improving": "📈", "stable": "➡️", "declining": "📉", "volatile": "📊"}.get(
                    emotional_state.emotional_trajectory, "➡️"
                )
                st.metric("Trajectory", f"{trajectory_emoji} {emotional_state.emotional_trajectory.title()}")

            with col3:
                empathy_color = "green" if emotional_state.empathy_score >= 0.7 else "orange" if emotional_state.empathy_score >= 0.4 else "red"
                st.metric("Empathy Score", f"{emotional_state.empathy_score:.0%}")

            # Secondary emotions
            if emotional_state.secondary_emotions:
                st.markdown("#### 🌈 Secondary Emotions")
                emotion_cols = st.columns(min(len(emotional_state.secondary_emotions), 4))
                for i, (emotion, intensity) in enumerate(emotional_state.secondary_emotions[:4]):
                    with emotion_cols[i]:
                        st.metric(emotion.title(), f"{intensity:.1f}")

            # Emotional indicators
            col1, col2 = st.columns(2)

            with col1:
                if emotional_state.excitement_indicators:
                    st.markdown("#### ✨ Excitement Signals")
                    for indicator in emotional_state.excitement_indicators[:3]:
                        st.success(f"✨ {indicator}")

                if emotional_state.trust_indicators:
                    st.markdown("#### 🤝 Trust Signals")
                    for indicator in emotional_state.trust_indicators[:3]:
                        st.info(f"🤝 {indicator}")

            with col2:
                if emotional_state.stress_indicators:
                    st.markdown("#### ⚠️ Stress Signals")
                    for indicator in emotional_state.stress_indicators[:3]:
                        st.warning(f"⚠️ {indicator}")

            # Decision readiness
            decision_readiness = emotional_state.decision_readiness
            readiness_color = "green" if decision_readiness >= 0.7 else "orange" if decision_readiness >= 0.5 else "red"
            st.progress(decision_readiness, text=f"Decision Readiness: {decision_readiness:.0%}")

        with tab3:
            st.markdown("### 🤝 Trust & Rapport Analysis")

            with st.spinner("🧠 Analyzing trust metrics..."):
                trust_metrics = loop.run_until_complete(
                    self.analyze_trust_metrics(thread_id)
                )

            # Trust overview
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("Overall Trust", f"{trust_metrics.overall_trust_score:.0%}")
            with col2:
                rapport_emoji = {"building": "🌱", "established": "🌿", "strong": "🌳", "excellent": "🌟"}.get(
                    trust_metrics.rapport_level, "🌱"
                )
                st.metric("Rapport", f"{rapport_emoji} {trust_metrics.rapport_level.title()}")
            with col3:
                st.metric("Credibility", f"{trust_metrics.credibility_score:.0%}")
            with col4:
                st.metric("Alignment", f"{trust_metrics.communication_alignment:.0%}")

            # Trust building recommendations
            if trust_metrics.trust_building_recommendations:
                st.markdown("#### 📈 Trust Building Recommendations")
                for recommendation in trust_metrics.trust_building_recommendations[:4]:
                    st.success(f"📈 {recommendation}")

            # Rapport risks
            if trust_metrics.rapport_risks:
                st.markdown("#### ⚠️ Rapport Risks to Avoid")
                for risk in trust_metrics.rapport_risks[:3]:
                    st.warning(f"⚠️ {risk}")

            # Trust components breakdown
            st.markdown("#### 🔍 Trust Components")
            trust_components = {
                "Credibility": trust_metrics.credibility_score,
                "Communication": trust_metrics.communication_alignment,
                "Value Demo": trust_metrics.value_demonstration,
                "Responsiveness": trust_metrics.responsiveness_score
            }

            for component, score in trust_components.items():
                st.progress(score, text=f"{component}: {score:.0%}")

        with tab4:
            st.markdown("### 🎯 Advanced Closing Signals")

            with st.spinner("🧠 Detecting closing signals..."):
                closing_signals = loop.run_until_complete(
                    self.detect_closing_signals(thread_id)
                )

            # Closing metrics
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                urgency_emoji = "🔥" if closing_signals.buying_urgency >= 0.7 else "🔸" if closing_signals.buying_urgency >= 0.4 else "❄️"
                st.metric("Buying Urgency", f"{urgency_emoji} {closing_signals.buying_urgency:.0%}")

            with col2:
                timing_emoji = {"immediate": "⚡", "days": "📅", "weeks": "📆", "months": "🗓️", "exploring": "🔍"}.get(
                    closing_signals.decision_timing, "🔍"
                )
                st.metric("Decision Timing", f"{timing_emoji} {closing_signals.decision_timing.title()}")

            with col3:
                readiness_color = "green" if closing_signals.closing_readiness_score >= 0.7 else "orange"
                st.metric("Closing Readiness", f"{closing_signals.closing_readiness_score:.0%}")

            with col4:
                sensitivity_emoji = {"low": "💰", "medium": "💵", "high": "💲"}.get(
                    closing_signals.price_sensitivity, "💵"
                )
                st.metric("Price Sensitivity", f"{sensitivity_emoji} {closing_signals.price_sensitivity.title()}")

            # Commitment vs Hesitation
            col1, col2 = st.columns(2)

            with col1:
                if closing_signals.commitment_signals:
                    st.markdown("#### ✅ Commitment Signals")
                    for signal in closing_signals.commitment_signals[:4]:
                        st.success(f"✅ {signal}")

            with col2:
                if closing_signals.hesitation_signals:
                    st.markdown("#### ❌ Hesitation Signals")
                    for signal in closing_signals.hesitation_signals[:4]:
                        st.warning(f"❌ {signal}")

            # Strategic recommendations
            st.markdown("#### 🎯 Closing Strategy")
            st.info(f"**Optimal Strategy:** {closing_signals.optimal_closing_strategy}")
            st.info(f"**Timing Recommendation:** {closing_signals.timing_recommendation}")

        with tab5:
            st.markdown("### 📈 Conversation Health Monitor")

            with st.spinner("🧠 Monitoring conversation health..."):
                health_monitor = loop.run_until_complete(
                    self.monitor_conversation_health(thread_id)
                )

            # Health overview
            col1, col2, col3 = st.columns(3)

            health = health_monitor.get("health", "unknown")
            health_score = health_monitor.get("health_score", 0.5)
            trend = health_monitor.get("engagement_trend", "unknown")

            with col1:
                health_emoji = {"excellent": "🟢", "good": "🟡", "concerning": "🟠", "poor": "🔴"}.get(health, "⚪")
                st.metric("Overall Health", f"{health_emoji} {health.title()}")

            with col2:
                st.metric("Health Score", f"{health_score:.0%}")

            with col3:
                trend_emoji = {"improving": "📈", "stable": "➡️", "declining": "📉"}.get(trend, "❓")
                st.metric("Engagement Trend", f"{trend_emoji} {trend.title()}")

            # Engagement metrics
            metrics = health_monitor.get("engagement_metrics", {})
            if metrics:
                st.markdown("#### 📊 Engagement Metrics")

                for metric, value in metrics.items():
                    if isinstance(value, (int, float)):
                        st.metric(metric.replace("_", " ").title(), f"{value:.2f}")

            # Health recommendations
            recommendations = health_monitor.get("recommendations", [])
            if recommendations:
                st.markdown("#### 💡 Health Recommendations")
                for rec in recommendations[:4]:
                    st.info(f"💡 {rec}")

            # Trend indicators
            indicators = health_monitor.get("trend_indicators", [])
            if indicators:
                st.markdown("#### 📈 Trend Indicators")
                for indicator in indicators[:3]:
                    st.success(f"📈 {indicator}")

        # Action buttons at the bottom
        st.markdown("---")
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🔄 Refresh Analysis", help="Re-analyze conversation with latest messages"):
                st.rerun()

        with col2:
            if st.button("💬 Get Response Suggestions", help="Generate contextual response options"):
                with st.spinner("Generating response suggestions..."):
                    suggestions = loop.run_until_complete(
                        self.generate_response_suggestions(
                            {"thread_id": thread_id, "analysis": thread_analysis},
                            ConversationAnalysis(
                                intent_level=thread_data.get("intent_level", 0.5),
                                urgency_score=closing_signals.buying_urgency,
                                objection_type=None,
                                recommended_response="Based on analysis",
                                property_readiness="medium",
                                next_best_action=thread_data.get("next_phase_recommendation", "Continue"),
                                confidence=0.8,
                                analysis_timestamp=datetime.now()
                            )
                        )
                    )

                if suggestions:
                    st.markdown("### 💬 AI Response Suggestions")
                    for i, suggestion in enumerate(suggestions, 1):
                        st.markdown(f"**Option {i}:** {suggestion}")

        with col3:
            if st.button("📊 Export Analysis", help="Export analysis results"):
                st.success("Analysis exported! (Feature placeholder)")

    def render_intelligence_panel(self, messages: List[Dict], lead_context: Dict = None) -> None:
        """
        Render real-time conversation intelligence in Streamlit.

        Args:
            messages: Recent conversation messages
            lead_context: Lead profile and context
        """
        if not messages:
            st.info("🤖 Start a conversation to see real-time intelligence")
            return

        # Only analyze if we have recent messages
        if len(messages) < 2:
            st.info("🤖 Analyzing conversation patterns...")
            return

        # Run analysis asynchronously in Streamlit
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        with st.spinner("🧠 Analyzing conversation with Claude..."):
            analysis = loop.run_until_complete(
                self.analyze_conversation_realtime(messages, lead_context)
            )

        # Display results
        st.markdown("### 🎯 Real-time Intelligence")

        # Key metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            intent_color = "red" if analysis.intent_level >= 0.7 else "orange" if analysis.intent_level >= 0.4 else "blue"
            st.metric(
                "Intent Level",
                f"{analysis.intent_level:.0%}",
                delta=f"Confidence: {analysis.confidence:.0%}",
                delta_color="normal"
            )

        with col2:
            urgency_color = "red" if analysis.urgency_score >= 0.7 else "orange" if analysis.urgency_score >= 0.4 else "blue"
            st.metric("Urgency Score", f"{analysis.urgency_score:.0%}")

        with col3:
            readiness_emoji = "🔥" if analysis.property_readiness == "high" else "🔸" if analysis.property_readiness == "medium" else "❄️"
            st.metric("Property Readiness", f"{readiness_emoji} {analysis.property_readiness.title()}")

        # Strategic guidance
        st.markdown("### 💡 Strategic Guidance")

        if analysis.objection_type:
            st.warning(f"**Objection Detected:** {analysis.objection_type.replace('_', ' ').title()}")

        st.info(f"**Recommended Response:** {analysis.recommended_response}")

        st.success(f"**Next Best Action:** {analysis.next_best_action}")

        # Get and display response suggestions
        if st.button("🚀 Get Response Suggestions", key="get_suggestions"):
            with st.spinner("Generating response options..."):
                suggestions = loop.run_until_complete(
                    self.generate_response_suggestions(
                        {"current_analysis": analysis.__dict__},
                        analysis
                    )
                )

            if suggestions:
                st.markdown("### 💬 Response Options")
                for i, suggestion in enumerate(suggestions, 1):
                    st.markdown(f"**Option {i}:** {suggestion}")

# Global instance for easy access
_conversation_intelligence = None

def get_conversation_intelligence() -> ConversationIntelligenceEngine:
    """Get global conversation intelligence instance."""
    global _conversation_intelligence
    if _conversation_intelligence is None:
        _conversation_intelligence = ConversationIntelligenceEngine()
    return _conversation_intelligence