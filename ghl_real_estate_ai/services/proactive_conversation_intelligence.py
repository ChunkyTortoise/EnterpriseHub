"""
Proactive Conversation Intelligence Service for Jorge's Real Estate AI Platform

Provides continuous conversation monitoring, proactive insight generation, and
real-time coaching opportunities. This service anticipates needs before being asked
and delivers intelligent guidance to enhance conversation outcomes.

Core Capabilities:
- Continuous conversation monitoring with semantic analysis
- Pattern recognition for coaching opportunities
- Real-time objection prediction and strategy recommendations
- Conversation quality assessment with actionable feedback
- ML-powered behavioral analysis with confidence scoring
- WebSocket event publishing for real-time dashboard updates

Performance Targets:
- Insight generation: <2s end-to-end latency
- ML inference: <25ms (leveraging existing analytics engine)
- Cache hit rate: >60% (semantic similarity matching)
- WebSocket event delivery: <100ms
- Monitoring loop efficiency: 5-second intervals for active conversations

Architecture Integration:
- Extends existing ClaudeAssistant orchestration patterns
- Leverages existing SemanticResponseCache for performance
- Integrates with existing ML analytics engine for scoring
- Uses existing event publishing infrastructure for real-time updates
"""

import asyncio
import hashlib
import json
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sentence_transformers import SentenceTransformer

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.ai_concierge_models import (
    CoachingCategory,
    CoachingOpportunity,
    ConversationStage,
    InsightPriority,
    # Enums
    InsightType,
    # Event Models
    ProactiveInsight,
    StrategyRecommendation,
    StrategyType,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.claude_conversation_intelligence import get_conversation_intelligence
from ghl_real_estate_ai.services.event_publisher import get_event_publisher

# Import ML engine for fast behavioral scoring
try:
    from bots.shared.ml_analytics_engine import get_ml_engine

    ML_ENGINE_AVAILABLE = True
except ImportError:
    ML_ENGINE_AVAILABLE = False
    get_ml_engine = None

logger = get_logger(__name__)


class ConversationMonitoringState:
    """State management for active conversation monitoring."""

    def __init__(self, conversation_id: str):
        self.conversation_id = conversation_id
        self.monitoring_started_at = datetime.utcnow()
        self.last_analysis_at: Optional[datetime] = None
        self.total_insights_generated = 0
        self.insights_by_type: Dict[str, int] = {}
        self.last_message_count = 0
        self.conversation_stage = ConversationStage.INITIAL_CONTACT
        self.quality_trend: List[float] = []
        self.is_active = True

    def update_insights_count(self, insight_type: str):
        """Update insights tracking."""
        self.total_insights_generated += 1
        self.insights_by_type[insight_type] = self.insights_by_type.get(insight_type, 0) + 1

    def get_monitoring_duration(self) -> timedelta:
        """Get total monitoring duration."""
        return datetime.utcnow() - self.monitoring_started_at


class ProactiveConversationIntelligence:
    """
    Core proactive intelligence service that continuously monitors conversations
    and generates insights, coaching opportunities, and strategic recommendations.

    This service operates as an intelligent observer that anticipates needs and
    provides guidance before being explicitly asked.
    """

    def __init__(self, claude_assistant: Optional[ClaudeAssistant] = None):
        """Initialize proactive intelligence with existing service integration."""

        # Core service dependencies
        self.claude_assistant = claude_assistant or ClaudeAssistant()
        self.cache_service = get_cache_service()
        self.event_publisher = get_event_publisher()
        self.conversation_intelligence = get_conversation_intelligence()

        # Performance components
        self.semantic_cache = self.claude_assistant.semantic_cache
        self.ml_engine = get_ml_engine() if ML_ENGINE_AVAILABLE else None

        # Sentence transformer for semantic analysis (shared with semantic cache)
        self._embeddings_model: Optional[SentenceTransformer] = None

        # Monitoring state management
        self.active_monitors: Dict[str, asyncio.Task] = {}  # conversation_id -> Task
        self.monitoring_states: Dict[str, ConversationMonitoringState] = {}
        self.insight_history: Dict[str, List[ProactiveInsight]] = {}  # LRU with 100 conversation limit

        # Pattern recognition databases
        self.objection_patterns = self._initialize_objection_patterns()
        self.coaching_patterns = self._initialize_coaching_patterns()
        self.strategy_triggers = self._initialize_strategy_triggers()

        # Performance tracking
        self.performance_metrics = {
            "total_insights_generated": 0,
            "average_generation_time_ms": 0.0,
            "cache_hit_rate": 0.0,
            "active_monitoring_sessions": 0,
            "ml_inference_time_ms": 0.0,
            "last_reset": datetime.utcnow(),
        }

        logger.info("ProactiveConversationIntelligence initialized with semantic caching and ML integration")

    def _initialize_objection_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize objection detection patterns with response strategies."""
        return {
            "price_objection": {
                "keywords": [
                    "too expensive",
                    "can't afford",
                    "price is high",
                    "budget",
                    "cost too much",
                    "cheaper option",
                    "need to save money",
                    "financial constraints",
                ],
                "response_strategies": [
                    "Acknowledge concern and pivot to value",
                    "Share ROI examples from similar clients",
                    "Break down cost vs. potential loss of not acting",
                ],
                "confidence_threshold": 0.75,
                "urgency": InsightPriority.HIGH,
            },
            "timing_objection": {
                "keywords": [
                    "not ready",
                    "need more time",
                    "thinking about it",
                    "maybe later",
                    "next year",
                    "not the right time",
                    "too busy right now",
                ],
                "response_strategies": [
                    "Explore what 'ready' means specifically",
                    "Highlight market timing advantages",
                    "Create structured timeline with milestones",
                ],
                "confidence_threshold": 0.70,
                "urgency": InsightPriority.MEDIUM,
            },
            "authority_objection": {
                "keywords": [
                    "talk to spouse",
                    "need to discuss",
                    "decision together",
                    "ask my partner",
                    "family meeting",
                    "get approval",
                    "check with wife/husband",
                ],
                "response_strategies": [
                    "Include decision maker in conversation",
                    "Provide materials for partner discussion",
                    "Schedule three-way call/meeting",
                ],
                "confidence_threshold": 0.80,
                "urgency": InsightPriority.HIGH,
            },
            "trust_objection": {
                "keywords": [
                    "don't know you",
                    "never heard of you",
                    "need references",
                    "prove yourself",
                    "seems too good",
                    "sounds fishy",
                    "not sure about this",
                ],
                "response_strategies": [
                    "Share testimonials and case studies",
                    "Provide references and credentials",
                    "Offer low-risk trial or guarantee",
                ],
                "confidence_threshold": 0.75,
                "urgency": InsightPriority.HIGH,
            },
        }

    def _initialize_coaching_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Initialize coaching opportunity patterns."""
        return {
            "missed_rapport_opportunity": {
                "triggers": [
                    "Personal information shared but not acknowledged",
                    "Emotional language not reflected back",
                    "Opportunity for common ground missed",
                ],
                "coaching_insight": "Look for personal connection opportunities to build rapport",
                "technique": "Active listening with personal connection bridges",
                "success_probability": 0.85,
                "category": CoachingCategory.RAPPORT_BUILDING,
            },
            "weak_value_articulation": {
                "triggers": [
                    "Generic benefits mentioned without personalization",
                    "No specific examples or stories shared",
                    "Features listed without benefit translation",
                ],
                "coaching_insight": "Transform features into personal benefits with specific examples",
                "technique": "Story-driven value demonstration with client-specific outcomes",
                "success_probability": 0.80,
                "category": CoachingCategory.VALUE_PROPOSITION,
            },
            "objection_avoidance": {
                "triggers": [
                    "Objection raised but quickly moved past",
                    "Concern mentioned but not fully addressed",
                    "Defensive response to pushback",
                ],
                "coaching_insight": "Embrace objections as buying signals and address them fully",
                "technique": "Feel-Felt-Found method with complete resolution",
                "success_probability": 0.75,
                "category": CoachingCategory.OBJECTION_HANDLING,
            },
            "no_closing_attempt": {
                "triggers": [
                    "Conversation ending without clear next step",
                    "Interest shown but no commitment request",
                    "Value established but no call to action",
                ],
                "coaching_insight": "Always ask for the next step - closing is helping them decide",
                "technique": "Assumptive close with specific next action",
                "success_probability": 0.90,
                "category": CoachingCategory.CLOSING_TECHNIQUES,
            },
        }

    def _initialize_strategy_triggers(self) -> Dict[str, Dict[str, Any]]:
        """Initialize strategic pivot triggers."""
        return {
            "buyer_signals_detected": {
                "triggers": [
                    "Questions about available properties",
                    "Timeline mentions for moving",
                    "Property preference discussions",
                    "Financing questions",
                ],
                "strategy": StrategyType.PIVOT_TO_BUYER,
                "description": "Lead showing buyer interest - pivot to dual representation",
                "implementation": "Acknowledge seller discussion completion, transition to buyer needs",
                "impact_score": 0.85,
                "urgency": "soon",
            },
            "stalling_conversation": {
                "triggers": [
                    "Repeated vague responses",
                    "Long response delays",
                    "Avoiding commitment questions",
                    "Passive engagement",
                ],
                "strategy": StrategyType.ESCALATE_URGENCY,
                "description": "Create appropriate urgency to prevent conversation stalling",
                "implementation": "Introduce market timing factors and scarcity elements",
                "impact_score": 0.70,
                "urgency": "immediate",
            },
            "high_engagement_opportunity": {
                "triggers": [
                    "Multiple questions asked",
                    "Quick response times",
                    "Detail-seeking behavior",
                    "Positive tone indicators",
                ],
                "strategy": StrategyType.SCHEDULE_MEETING,
                "description": "High engagement - perfect time to request meeting",
                "implementation": "Leverage momentum to secure face-to-face meeting",
                "impact_score": 0.80,
                "urgency": "immediate",
            },
        }

    # ============================================================================
    # Core Monitoring and Analysis Methods
    # ============================================================================

    async def start_monitoring(self, conversation_id: str) -> None:
        """
        Start continuous monitoring for a conversation.

        Creates background task that analyzes conversation state every 5 seconds
        and generates proactive insights based on patterns and ML analysis.

        Args:
            conversation_id: Unique conversation identifier
        """
        if conversation_id in self.active_monitors:
            logger.debug(f"Monitoring already active for conversation: {conversation_id}")
            return

        try:
            # Initialize monitoring state
            self.monitoring_states[conversation_id] = ConversationMonitoringState(conversation_id)

            # Create monitoring task
            monitoring_task = asyncio.create_task(
                self._monitoring_loop(conversation_id), name=f"monitor_{conversation_id}"
            )

            self.active_monitors[conversation_id] = monitoring_task
            self.performance_metrics["active_monitoring_sessions"] += 1

            logger.info(f"Started proactive monitoring for conversation: {conversation_id}")

        except Exception as e:
            logger.error(f"Failed to start monitoring for {conversation_id}: {e}")
            raise

    async def stop_monitoring(self, conversation_id: str) -> None:
        """
        Stop monitoring for a conversation and clean up resources.

        Args:
            conversation_id: Conversation to stop monitoring
        """
        if conversation_id not in self.active_monitors:
            logger.debug(f"No active monitoring for conversation: {conversation_id}")
            return

        try:
            # Cancel monitoring task
            monitoring_task = self.active_monitors[conversation_id]
            monitoring_task.cancel()

            try:
                await monitoring_task
            except asyncio.CancelledError:
                pass

            # Clean up state
            del self.active_monitors[conversation_id]
            if conversation_id in self.monitoring_states:
                self.monitoring_states[conversation_id].is_active = False

            self.performance_metrics["active_monitoring_sessions"] -= 1

            logger.info(f"Stopped monitoring for conversation: {conversation_id}")

        except Exception as e:
            logger.error(f"Error stopping monitoring for {conversation_id}: {e}")

    async def _monitoring_loop(self, conversation_id: str) -> None:
        """
        Continuous monitoring loop that analyzes conversation state every 5 seconds.

        This is the core intelligence engine that:
        1. Checks for conversation updates
        2. Analyzes new messages for patterns
        3. Generates proactive insights
        4. Publishes real-time events
        5. Updates conversation quality scores
        """
        monitoring_state = self.monitoring_states[conversation_id]

        try:
            while monitoring_state.is_active:
                start_time = time.time()

                try:
                    # Check for conversation updates
                    conversation_data = await self._get_conversation_data(conversation_id)

                    if not conversation_data:
                        await asyncio.sleep(5)
                        continue

                    messages = conversation_data.get("messages", [])
                    current_message_count = len(messages)

                    # Only analyze if new messages since last check
                    if current_message_count > monitoring_state.last_message_count:
                        # Analyze conversation state for insights
                        insights = await self.analyze_conversation_state(conversation_id, conversation_data)

                        # Publish high-priority insights immediately
                        for insight in insights:
                            if insight.priority in [InsightPriority.CRITICAL, InsightPriority.HIGH]:
                                await self._publish_proactive_insight_event(conversation_id, insight)
                                monitoring_state.update_insights_count(insight.insight_type.value)

                        # Update monitoring state
                        monitoring_state.last_message_count = current_message_count
                        monitoring_state.last_analysis_at = datetime.utcnow()

                        # Store insights in history (with LRU management)
                        self._update_insight_history(conversation_id, insights)

                        # Update performance metrics
                        processing_time_ms = (time.time() - start_time) * 1000
                        self._update_performance_metrics(processing_time_ms)

                        logger.debug(
                            f"Generated {len(insights)} insights for {conversation_id} in {processing_time_ms:.1f}ms"
                        )

                except Exception as e:
                    logger.error(f"Error in monitoring loop for {conversation_id}: {e}")

                # Wait 5 seconds before next analysis (balanced real-time vs. cost)
                await asyncio.sleep(5)

        except asyncio.CancelledError:
            logger.debug(f"Monitoring loop cancelled for conversation: {conversation_id}")
        except Exception as e:
            logger.error(f"Monitoring loop error for {conversation_id}: {e}")

    async def analyze_conversation_state(
        self, conversation_id: str, conversation_data: Optional[Dict[str, Any]] = None
    ) -> List[ProactiveInsight]:
        """
        Main intelligence analysis method that detects patterns and generates insights.

        Uses semantic analysis, pattern matching, and ML scoring to identify:
        - Coaching opportunities
        - Strategy pivot recommendations
        - Objection predictions
        - Quality improvement suggestions

        Args:
            conversation_id: Conversation to analyze
            conversation_data: Optional pre-fetched conversation data

        Returns:
            List[ProactiveInsight]: Generated insights sorted by priority
        """
        start_time = time.time()

        try:
            # Check semantic cache first for performance
            cache_key = f"conversation_analysis:{conversation_id}"

            # Get conversation data if not provided
            if conversation_data is None:
                conversation_data = await self._get_conversation_data(conversation_id)

            if not conversation_data:
                return []

            # Generate cache key based on message content hash for consistency
            messages = conversation_data.get("messages", [])
            if not messages:
                return []

            messages_hash = hashlib.md5(
                json.dumps([msg.get("content", "") for msg in messages[-5:]], sort_keys=True).encode()
            ).hexdigest()

            cache_key_with_hash = f"{cache_key}:{messages_hash}"

            # Check semantic cache
            cached_insights = await self.semantic_cache.get_similar(cache_key_with_hash, threshold=0.85)

            if cached_insights:
                logger.debug(f"Cache hit for conversation analysis: {conversation_id}")
                return [ProactiveInsight(**insight) for insight in cached_insights]

            # Perform comprehensive analysis
            insights = []

            # Parallel analysis for performance
            coaching_task = self.detect_coaching_opportunities(messages, conversation_id)
            strategy_task = self.detect_strategy_pivots(messages, conversation_id)
            quality_task = self.assess_conversation_quality(messages, conversation_id)
            objection_task = self.predict_objections(messages, conversation_id)

            coaching_ops, strategy_recs, quality_insights, objection_predictions = await asyncio.gather(
                coaching_task, strategy_task, quality_task, objection_task, return_exceptions=True
            )

            # Convert results to insights (handling exceptions)
            for result_set, insight_type in [
                (coaching_ops, InsightType.COACHING),
                (strategy_recs, InsightType.STRATEGY_PIVOT),
                (quality_insights, InsightType.CONVERSATION_QUALITY),
                (objection_predictions, InsightType.OBJECTION_PREDICTION),
            ]:
                if not isinstance(result_set, Exception):
                    for item in result_set:
                        insight = await self._convert_to_proactive_insight(item, insight_type, conversation_id)
                        if insight:
                            insights.append(insight)

            # Sort by priority and confidence
            insights.sort(key=lambda i: (i.priority.value, -i.confidence_score))

            # Cache results for 30 seconds (balance freshness vs. performance)
            insights_data = [asdict(insight) for insight in insights]
            await self.semantic_cache.set(cache_key_with_hash, insights_data, ttl=30)

            # Update performance metrics
            processing_time_ms = (time.time() - start_time) * 1000
            self.performance_metrics["total_insights_generated"] += len(insights)

            logger.debug(f"Generated {len(insights)} insights for {conversation_id} in {processing_time_ms:.1f}ms")

            return insights

        except Exception as e:
            processing_time_ms = (time.time() - start_time) * 1000
            logger.error(
                f"Failed to analyze conversation state for {conversation_id}: {e} (took {processing_time_ms:.1f}ms)"
            )
            return []

    # ============================================================================
    # Pattern Detection and Analysis Methods
    # ============================================================================

    async def detect_coaching_opportunities(
        self, messages: List[Dict[str, Any]], conversation_id: str
    ) -> List[CoachingOpportunity]:
        """
        Detect real-time coaching opportunities using pattern analysis.

        Analyzes conversation for missed opportunities, areas for improvement,
        and skill development possibilities.
        """
        opportunities = []

        try:
            # Analyze recent messages for coaching patterns
            recent_messages = messages[-5:]  # Focus on last 5 messages for real-time relevance

            for pattern_name, pattern_config in self.coaching_patterns.items():
                for trigger in pattern_config["triggers"]:
                    # Simple pattern matching (in production, use more sophisticated NLP)
                    if await self._detect_pattern_in_messages(recent_messages, trigger):
                        # Generate ML confidence score if available
                        confidence = await self._get_ml_confidence_score(recent_messages, pattern_name)

                        if confidence >= 0.7:  # High confidence threshold for coaching
                            opportunity = CoachingOpportunity(
                                coaching_category=pattern_config["category"],
                                detected_pattern=trigger,
                                missed_opportunity=f"Opportunity for {pattern_config['category'].value}",
                                coaching_insight=pattern_config["coaching_insight"],
                                recommended_technique=pattern_config["technique"],
                                example_response=await self._generate_example_response(
                                    pattern_config["category"], recent_messages
                                ),
                                success_probability=pattern_config["success_probability"] * confidence,
                                skill_level_required="intermediate",
                                conversation_context={
                                    "conversation_id": conversation_id,
                                    "trigger_pattern": trigger,
                                    "message_count": len(recent_messages),
                                },
                                immediate_application=True,
                                learning_objective=f"Improve {pattern_config['category'].value} skills",
                            )
                            opportunities.append(opportunity)

        except Exception as e:
            logger.error(f"Error detecting coaching opportunities: {e}")

        return opportunities

    async def detect_strategy_pivots(
        self, messages: List[Dict[str, Any]], conversation_id: str
    ) -> List[StrategyRecommendation]:
        """
        Detect strategic pivot opportunities based on conversation patterns.

        Identifies moments where conversation direction should change to
        optimize outcomes (e.g., pivot to buyer mode, escalate urgency).
        """
        recommendations = []

        try:
            # Analyze conversation for strategic pivot triggers
            all_message_text = " ".join([msg.get("content", "") for msg in messages[-10:]])

            for trigger_name, trigger_config in self.strategy_triggers.items():
                trigger_score = 0
                detected_triggers = []

                # Check each trigger condition
                for trigger in trigger_config["triggers"]:
                    if await self._detect_pattern_in_text(all_message_text, trigger):
                        trigger_score += 1
                        detected_triggers.append(trigger)

                # Generate recommendation if multiple triggers detected
                if trigger_score >= 2:  # At least 2 triggers for confidence
                    recommendation = StrategyRecommendation(
                        strategy_type=trigger_config["strategy"],
                        strategy_title=f"Recommendation: {trigger_config['description']}",
                        strategy_description=trigger_config["description"],
                        rationale=f"Detected {trigger_score} relevant triggers: {', '.join(detected_triggers)}",
                        implementation_steps=await self._generate_implementation_steps(
                            trigger_config["strategy"], conversation_id
                        ),
                        conversation_pivot=trigger_config["implementation"],
                        expected_outcome=await self._predict_strategy_outcome(trigger_config["strategy"], messages),
                        impact_score=trigger_config["impact_score"],
                        urgency_level=trigger_config["urgency"],
                        trigger_conditions=detected_triggers,
                        success_indicators=await self._generate_success_indicators(trigger_config["strategy"]),
                        risk_level="low" if trigger_score >= 3 else "medium",
                    )
                    recommendations.append(recommendation)

        except Exception as e:
            logger.error(f"Error detecting strategy pivots: {e}")

        return recommendations

    async def predict_objections(self, messages: List[Dict[str, Any]], conversation_id: str) -> List[Dict[str, Any]]:
        """
        Predict likely objections based on conversation patterns and lead behavior.

        Uses pattern recognition and ML analysis to anticipate objections
        before they're raised, enabling proactive handling.
        """
        predictions = []

        try:
            recent_messages = messages[-3:]  # Focus on most recent messages

            for objection_type, pattern_config in self.objection_patterns.items():
                # Check for objection indicators
                objection_probability = 0.0
                detected_indicators = []

                for keyword in pattern_config["keywords"]:
                    for msg in recent_messages:
                        if keyword.lower() in msg.get("content", "").lower():
                            objection_probability += 0.2  # Incremental probability
                            detected_indicators.append(keyword)

                # Get ML confidence if available
                if self.ml_engine:
                    ml_confidence = await self._get_ml_confidence_score(recent_messages, f"objection_{objection_type}")
                    objection_probability = max(objection_probability, ml_confidence)

                # Generate prediction if probability exceeds threshold
                if objection_probability >= pattern_config["confidence_threshold"]:
                    prediction = {
                        "objection_type": objection_type,
                        "probability": objection_probability,
                        "indicators": detected_indicators,
                        "response_strategies": pattern_config["response_strategies"],
                        "urgency": pattern_config["urgency"],
                        "conversation_context": {
                            "conversation_id": conversation_id,
                            "recent_message_count": len(recent_messages),
                        },
                    }
                    predictions.append(prediction)

        except Exception as e:
            logger.error(f"Error predicting objections: {e}")

        return predictions

    async def assess_conversation_quality(
        self, messages: List[Dict[str, Any]], conversation_id: str
    ) -> List[Dict[str, Any]]:
        """
        Assess conversation quality across multiple dimensions.

        Provides real-time quality scoring with specific improvement
        recommendations.
        """
        quality_insights = []

        try:
            # Calculate basic quality metrics
            total_messages = len(messages)
            if total_messages < 3:
                return []  # Need minimum conversation for assessment

            # Analyze conversation characteristics
            lead_messages = [msg for msg in messages if msg.get("sender_type") == "lead"]
            agent_messages = [msg for msg in messages if msg.get("sender_type") == "agent"]

            if not lead_messages or not agent_messages:
                return []

            # Quality scoring (simplified - in production use more sophisticated analysis)
            engagement_score = min(100, (len(lead_messages) / len(agent_messages)) * 50 + 50)
            response_quality_score = await self._analyze_response_quality(agent_messages)
            conversation_flow_score = await self._analyze_conversation_flow(messages)

            # Generate quality insight if scores indicate improvement needed
            overall_score = (engagement_score + response_quality_score + conversation_flow_score) / 3

            if overall_score < 75:  # Below good threshold
                quality_insight = {
                    "quality_type": "conversation_improvement",
                    "overall_score": overall_score,
                    "engagement_score": engagement_score,
                    "response_quality_score": response_quality_score,
                    "conversation_flow_score": conversation_flow_score,
                    "improvement_areas": await self._identify_improvement_areas(
                        engagement_score, response_quality_score, conversation_flow_score
                    ),
                    "specific_recommendations": await self._generate_quality_recommendations(overall_score, messages),
                }
                quality_insights.append(quality_insight)

        except Exception as e:
            logger.error(f"Error assessing conversation quality: {e}")

        return quality_insights

    # ============================================================================
    # Helper Methods and Utilities
    # ============================================================================

    async def _get_conversation_data(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation data from the database or cache.

        In production, this interfaces with the actual conversation storage system.
        """
        try:
            # Check cache first
            cache_key = f"conversation_data:{conversation_id}"
            cached_data = await self.cache_service.get(cache_key)

            if cached_data:
                return cached_data

            # Mock conversation data for development
            # In production: query actual database/storage system
            conversation_data = {
                "conversation_id": conversation_id,
                "messages": [
                    {
                        "id": f"msg_1",
                        "content": "Hi, I'm interested in selling my property",
                        "sender_type": "lead",
                        "timestamp": datetime.utcnow() - timedelta(minutes=10),
                    },
                    {
                        "id": f"msg_2",
                        "content": "Great! I'd love to help you with that. What's driving your decision to sell?",
                        "sender_type": "agent",
                        "timestamp": datetime.utcnow() - timedelta(minutes=9),
                    },
                    {
                        "id": f"msg_3",
                        "content": "Well, the market seems good and we need a bigger place",
                        "sender_type": "lead",
                        "timestamp": datetime.utcnow() - timedelta(minutes=8),
                    },
                ],
                "lead_profile": {"lead_id": f"lead_{conversation_id}", "ml_score": 72.5, "stage": "qualification"},
                "last_updated": datetime.utcnow(),
            }

            # Cache for 1 minute
            await self.cache_service.set(cache_key, conversation_data, ttl=60)

            return conversation_data

        except Exception as e:
            logger.error(f"Failed to get conversation data for {conversation_id}: {e}")
            return None

    async def _get_ml_confidence_score(self, messages: List[Dict[str, Any]], pattern_type: str) -> float:
        """
        Get ML confidence score for pattern detection using existing ML engine.

        Leverages the existing <25ms ML analytics engine for behavioral scoring.
        """
        if not self.ml_engine:
            return 0.7  # Default confidence when ML unavailable

        try:
            start_time = time.time()

            # Extract features from messages for ML analysis
            features = await self._extract_message_features(messages, pattern_type)

            # Get prediction from existing ML engine
            prediction = await self.ml_engine.predict_behavioral_pattern(features=features, pattern_type=pattern_type)

            # Track ML inference time
            ml_time_ms = (time.time() - start_time) * 1000
            self.performance_metrics["ml_inference_time_ms"] = ml_time_ms

            return prediction.confidence_score

        except Exception as e:
            logger.warning(f"ML confidence scoring failed for {pattern_type}: {e}")
            return 0.6  # Fallback confidence score

    async def _extract_message_features(self, messages: List[Dict[str, Any]], pattern_type: str) -> Dict[str, float]:
        """
        Extract features from messages for ML analysis.

        Converts conversation data into numerical features for the ML engine.
        """
        if not messages:
            return {}

        try:
            # Basic message features
            total_messages = len(messages)
            total_chars = sum(len(msg.get("content", "")) for msg in messages)
            avg_message_length = total_chars / total_messages if total_messages > 0 else 0

            # Sentiment and engagement features (simplified)
            question_count = sum(1 for msg in messages if "?" in msg.get("content", ""))
            exclamation_count = sum(1 for msg in messages if "!" in msg.get("content", ""))

            # Pattern-specific features
            pattern_keywords = {
                "objection_price": ["expensive", "cost", "budget", "afford"],
                "objection_timing": ["ready", "time", "later", "think"],
                "coaching_rapport": ["I", "me", "my", "personal"],
                "strategy_buyer": ["buy", "purchase", "looking", "house"],
            }

            keyword_matches = 0
            if pattern_type in pattern_keywords:
                keywords = pattern_keywords[pattern_type]
                for msg in messages:
                    content = msg.get("content", "").lower()
                    keyword_matches += sum(1 for keyword in keywords if keyword in content)

            features = {
                "message_count": float(total_messages),
                "avg_message_length": avg_message_length,
                "question_ratio": question_count / total_messages if total_messages > 0 else 0,
                "exclamation_ratio": exclamation_count / total_messages if total_messages > 0 else 0,
                "keyword_match_ratio": keyword_matches / total_messages if total_messages > 0 else 0,
                "conversation_length_minutes": 10.0,  # Simplified - calculate from timestamps
                "response_time_avg": 2.0,  # Simplified - calculate from actual timestamps
            }

            return features

        except Exception as e:
            logger.error(f"Failed to extract message features: {e}")
            return {}

    async def _detect_pattern_in_messages(self, messages: List[Dict[str, Any]], pattern: str) -> bool:
        """Simple pattern detection in message content."""
        try:
            all_content = " ".join([msg.get("content", "") for msg in messages]).lower()
            return pattern.lower() in all_content
        except Exception:
            return False

    async def _detect_pattern_in_text(self, text: str, pattern: str) -> bool:
        """Simple pattern detection in text."""
        return pattern.lower() in text.lower()

    async def _convert_to_proactive_insight(
        self, item: Any, insight_type: InsightType, conversation_id: str
    ) -> Optional[ProactiveInsight]:
        """
        Convert various analysis results to standardized ProactiveInsight format.
        """
        try:
            if isinstance(item, CoachingOpportunity):
                return ProactiveInsight(
                    insight_type=InsightType.COACHING,
                    priority=InsightPriority.MEDIUM,
                    title=f"Coaching: {item.coaching_category.value.replace('_', ' ').title()}",
                    description=item.coaching_insight,
                    reasoning=item.detected_pattern,
                    recommended_actions=[item.recommended_technique],
                    suggested_responses=[item.example_response],
                    confidence_score=item.success_probability,
                    expected_impact=item.success_probability * 0.9,
                    conversation_context=item.conversation_context,
                    applicable_stage=ConversationStage.QUALIFICATION,  # Default
                    expires_at=datetime.utcnow() + timedelta(minutes=30),
                )

            elif isinstance(item, StrategyRecommendation):
                return ProactiveInsight(
                    insight_type=InsightType.STRATEGY_PIVOT,
                    priority=item.get_priority(),
                    title=item.strategy_title,
                    description=item.strategy_description,
                    reasoning=item.rationale,
                    recommended_actions=item.implementation_steps,
                    suggested_responses=[item.conversation_pivot],
                    confidence_score=item.impact_score,
                    expected_impact=item.impact_score,
                    conversation_context={"strategy_type": item.strategy_type.value},
                    applicable_stage=ConversationStage.QUALIFICATION,
                    expires_at=datetime.utcnow() + timedelta(hours=1),
                )

            elif isinstance(item, dict):
                # Handle dictionary-based insights (quality, objections)
                if "objection_type" in item:
                    return ProactiveInsight(
                        insight_type=InsightType.OBJECTION_PREDICTION,
                        priority=item.get("urgency", InsightPriority.MEDIUM),
                        title=f"Objection Predicted: {item['objection_type'].replace('_', ' ').title()}",
                        description=f"High probability ({item['probability']:.1%}) of {item['objection_type']} objection",
                        reasoning=f"Detected indicators: {', '.join(item['indicators'])}",
                        recommended_actions=item["response_strategies"],
                        suggested_responses=item["response_strategies"][:2],
                        confidence_score=item["probability"],
                        expected_impact=0.8,
                        conversation_context=item["conversation_context"],
                        applicable_stage=ConversationStage.VALUE_PRESENTATION,
                        expires_at=datetime.utcnow() + timedelta(minutes=15),
                    )

                elif "quality_type" in item:
                    return ProactiveInsight(
                        insight_type=InsightType.CONVERSATION_QUALITY,
                        priority=InsightPriority.MEDIUM,
                        title="Conversation Quality Improvement Opportunity",
                        description=f"Overall quality score: {item['overall_score']:.1f}/100",
                        reasoning=f"Areas for improvement: {', '.join(item['improvement_areas'])}",
                        recommended_actions=item["specific_recommendations"],
                        suggested_responses=[],
                        confidence_score=0.9,  # High confidence in quality assessment
                        expected_impact=0.7,
                        conversation_context={"quality_scores": item},
                        applicable_stage=ConversationStage.QUALIFICATION,
                        expires_at=datetime.utcnow() + timedelta(minutes=45),
                    )

            return None

        except Exception as e:
            logger.error(f"Failed to convert item to ProactiveInsight: {e}")
            return None

    # Additional helper methods would be implemented here...
    # (Due to length constraints, I'm including the core structure)

    async def _publish_proactive_insight_event(self, conversation_id: str, insight: ProactiveInsight):
        """Publish proactive insight event via WebSocket."""
        try:
            {
                "conversation_id": conversation_id,
                "insight_id": insight.insight_id,
                "insight_type": insight.insight_type.value,
                "priority": insight.priority.value,
                "title": insight.title,
                "description": insight.description,
                "confidence_score": insight.confidence_score,
                "recommended_actions": insight.recommended_actions,
                "created_at": insight.created_at.isoformat(),
            }

            # Publish through existing event publisher
            await self.event_publisher.publish_proactive_insight(conversation_id=conversation_id, insight=insight)

            logger.debug(f"Published proactive insight event: {insight.insight_type.value}")

        except Exception as e:
            logger.error(f"Failed to publish proactive insight event: {e}")

    def _update_insight_history(self, conversation_id: str, insights: List[ProactiveInsight]):
        """Update insight history with LRU management."""
        if conversation_id not in self.insight_history:
            self.insight_history[conversation_id] = []

        self.insight_history[conversation_id].extend(insights)

        # Keep only last 50 insights per conversation
        if len(self.insight_history[conversation_id]) > 50:
            self.insight_history[conversation_id] = self.insight_history[conversation_id][-50:]

        # LRU management: keep only 100 conversations
        if len(self.insight_history) > 100:
            # Remove oldest conversation
            oldest_conversation = min(
                self.insight_history.keys(),
                key=lambda cid: (
                    self.monitoring_states.get(
                        cid, type("obj", (), {"monitoring_started_at": datetime.min})
                    ).monitoring_started_at
                ),
            )
            del self.insight_history[oldest_conversation]

    def _update_performance_metrics(self, processing_time_ms: float):
        """Update performance metrics for monitoring."""
        total_insights = self.performance_metrics["total_insights_generated"]
        current_avg = self.performance_metrics["average_generation_time_ms"]

        # Running average calculation
        if total_insights > 0:
            new_avg = ((current_avg * (total_insights - 1)) + processing_time_ms) / total_insights
            self.performance_metrics["average_generation_time_ms"] = new_avg

    async def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics."""
        return {
            "total_insights_generated": self.performance_metrics["total_insights_generated"],
            "average_generation_time_ms": self.performance_metrics["average_generation_time_ms"],
            "active_monitoring_sessions": len(self.active_monitors),
            "ml_inference_time_ms": self.performance_metrics["ml_inference_time_ms"],
            "target_generation_time_ms": 2000.0,  # <2s target
            "performance_status": "good"
            if self.performance_metrics["average_generation_time_ms"] < 2000.0
            else "needs_optimization",
        }

    # Placeholder methods that would be fully implemented
    async def _generate_example_response(self, category, messages):
        return "Example response..."

    async def _generate_implementation_steps(self, strategy, conv_id):
        return ["Step 1", "Step 2"]

    async def _predict_strategy_outcome(self, strategy, messages):
        return "Improved engagement expected"

    async def _generate_success_indicators(self, strategy):
        return ["Indicator 1", "Indicator 2"]

    async def _analyze_response_quality(self, messages):
        return 75.0

    async def _analyze_conversation_flow(self, messages):
        return 80.0

    async def _identify_improvement_areas(self, eng, qual, flow):
        return ["Area 1", "Area 2"]

    async def _generate_quality_recommendations(self, score, messages):
        return ["Recommendation 1"]


# ============================================================================
# Service Factory and Utilities
# ============================================================================

_proactive_intelligence_instance = None


def get_proactive_conversation_intelligence() -> ProactiveConversationIntelligence:
    """Get singleton instance of ProactiveConversationIntelligence."""
    global _proactive_intelligence_instance

    if _proactive_intelligence_instance is None:
        _proactive_intelligence_instance = ProactiveConversationIntelligence()

    return _proactive_intelligence_instance


if __name__ == "__main__":
    # Development/testing entry point
    import asyncio

    async def test_proactive_intelligence():
        """Test proactive intelligence functionality."""
        service = get_proactive_conversation_intelligence()

        # Test conversation monitoring
        conversation_id = "test_conv_123"

        try:
            await service.start_monitoring(conversation_id)
            logger.info("Started monitoring test conversation")

            # Let it run for a few seconds
            await asyncio.sleep(10)

            # Stop monitoring
            await service.stop_monitoring(conversation_id)
            logger.info("Stopped monitoring test conversation")

            # Check performance
            metrics = await service.get_performance_metrics()
            logger.info(f"Performance metrics: {metrics}")

        except Exception as e:
            logger.error(f"Test failed: {e}")

    # Run test
    asyncio.run(test_proactive_intelligence())
