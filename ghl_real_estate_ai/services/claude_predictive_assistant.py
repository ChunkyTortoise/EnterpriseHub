"""
Claude Predictive Assistant - Phase 4: Proactive Coaching Intelligence

This service provides proactive, predictive coaching assistance by analyzing conversation
patterns, agent behavior, and contextual signals to anticipate coaching needs before
they're explicitly requested. Uses machine learning to predict optimal intervention
points and provide just-in-time guidance.

Key Features:
- Conversation flow prediction and intervention timing
- Proactive coaching suggestions based on behavioral patterns
- Risk detection and early warning systems
- Opportunity identification and recommendation
- Context-aware assistance timing optimization
- Agent performance prediction and intervention strategies

Integrates with orchestration, learning, and automation engines for comprehensive intelligence.
"""

import asyncio
import json
import logging
import numpy as np
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field

from pydantic import BaseModel, Field
import redis.asyncio as redis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split

from ..core.service_registry import ServiceRegistry
from ..services.claude_orchestration_engine import ClaudeOrchestrationEngine, WorkflowType
from ..services.claude_learning_optimizer import ClaudeLearningOptimizer, ConversationData, OutcomeType
from ..services.claude_workflow_automation import ClaudeWorkflowAutomation
from ..services.agent_profile_service import AgentProfileService
from ..models.agent_profile_models import AgentProfile, AgentRole, GuidanceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PredictionType(str, Enum):
    """Types of predictions the assistant can make."""
    CONVERSATION_OUTCOME = "conversation_outcome"
    INTERVENTION_NEED = "intervention_need"
    PERFORMANCE_RISK = "performance_risk"
    OPPORTUNITY_IDENTIFICATION = "opportunity_identification"
    OPTIMAL_TIMING = "optimal_timing"
    GUIDANCE_EFFECTIVENESS = "guidance_effectiveness"
    CLIENT_SATISFACTION = "client_satisfaction"
    CONVERSION_LIKELIHOOD = "conversion_likelihood"


class InterventionType(str, Enum):
    """Types of proactive interventions."""
    COACHING_SUGGESTION = "coaching_suggestion"
    PROCESS_GUIDANCE = "process_guidance"
    RISK_WARNING = "risk_warning"
    OPPORTUNITY_ALERT = "opportunity_alert"
    STRATEGY_RECOMMENDATION = "strategy_recommendation"
    TIMING_OPTIMIZATION = "timing_optimization"
    RESOURCE_SUGGESTION = "resource_suggestion"
    ESCALATION_ALERT = "escalation_alert"


class UrgencyLevel(str, Enum):
    """Urgency levels for predictive interventions."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Confidence levels for predictions."""
    VERY_LOW = "very_low"      # < 50%
    LOW = "low"                # 50-65%
    MEDIUM = "medium"          # 65-80%
    HIGH = "high"              # 80-90%
    VERY_HIGH = "very_high"    # > 90%


@dataclass
class PredictiveSignal:
    """Signal used for predictive analysis."""
    signal_id: str
    signal_type: str
    value: float
    confidence: float
    timestamp: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    source: str = "system"


@dataclass
class Prediction:
    """Prediction made by the assistant."""
    prediction_id: str
    prediction_type: PredictionType
    predicted_outcome: str
    confidence: ConfidenceLevel
    probability: float
    contributing_factors: List[str]
    signals_used: List[PredictiveSignal]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProactiveIntervention:
    """Proactive intervention recommendation."""
    intervention_id: str
    intervention_type: InterventionType
    urgency: UrgencyLevel
    title: str
    description: str
    guidance: str
    predicted_impact: float
    timing_window: Dict[str, datetime]  # start, end, optimal
    target_agent_id: str
    conversation_context: Dict[str, Any]
    supporting_predictions: List[Prediction]
    action_items: List[str] = field(default_factory=list)
    resources: List[str] = field(default_factory=list)
    success_metrics: List[str] = field(default_factory=list)


@dataclass
class ConversationState:
    """Current state of agent conversation for predictive analysis."""
    conversation_id: str
    agent_id: str
    client_id: str
    start_time: datetime
    last_update: datetime
    message_count: int
    interaction_type: WorkflowType
    current_stage: str
    sentiment_trend: List[float]
    engagement_level: float
    signals: List[PredictiveSignal]
    predictions: List[Prediction]
    interventions_sent: List[str]
    outcome: Optional[OutcomeType] = None


class PredictiveRequest(BaseModel):
    """Request for predictive analysis."""
    agent_id: str
    conversation_id: Optional[str] = None
    prediction_types: List[PredictionType]
    context: Dict[str, Any] = Field(default_factory=dict)
    urgency_threshold: UrgencyLevel = UrgencyLevel.MEDIUM
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    time_horizon_minutes: int = Field(default=60, ge=1, le=1440)


class PredictiveResponse(BaseModel):
    """Response from predictive analysis."""
    agent_id: str
    conversation_id: Optional[str]
    predictions: List[Dict[str, Any]]
    interventions: List[Dict[str, Any]]
    risk_assessment: Dict[str, Any]
    opportunities: List[Dict[str, Any]]
    recommendations: List[str]
    confidence_summary: Dict[str, float]
    next_analysis_time: datetime


class RealTimeAnalysis(BaseModel):
    """Real-time conversation analysis results."""
    conversation_id: str
    current_stage: str
    sentiment_score: float
    engagement_level: float
    risk_indicators: List[str]
    opportunity_indicators: List[str]
    suggested_next_actions: List[str]
    intervention_recommendations: List[Dict[str, Any]]


class ClaudePredictiveAssistant:
    """Predictive assistant for proactive coaching and intervention."""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        orchestration_engine: ClaudeOrchestrationEngine,
        learning_optimizer: ClaudeLearningOptimizer,
        automation_engine: ClaudeWorkflowAutomation,
        redis_client: Optional[redis.Redis] = None
    ):
        self.service_registry = service_registry
        self.orchestration_engine = orchestration_engine
        self.learning_optimizer = learning_optimizer
        self.automation_engine = automation_engine
        self.redis_client = redis_client or redis.from_url("redis://localhost:6379/0")
        self.agent_service = AgentProfileService(service_registry, redis_client)

        # Predictive models
        self.conversation_outcome_predictor: Optional[RandomForestClassifier] = None
        self.intervention_timing_predictor: Optional[GradientBoostingRegressor] = None
        self.satisfaction_predictor: Optional[GradientBoostingRegressor] = None
        self.risk_predictor: Optional[RandomForestClassifier] = None
        self.feature_scaler: Optional[StandardScaler] = None

        # Conversation tracking
        self.active_conversations: Dict[str, ConversationState] = {}
        self.conversation_history: deque = deque(maxlen=1000)

        # Signal processing
        self.signal_processors: Dict[str, callable] = {}
        self.signal_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))

        # Prediction cache
        self.prediction_cache: Dict[str, Prediction] = {}
        self.intervention_history: List[ProactiveIntervention] = []

        # Configuration
        self.prediction_refresh_interval = 30  # seconds
        self.max_concurrent_predictions = 100
        self.signal_collection_interval = 10  # seconds
        self.intervention_cooldown_minutes = 15

        # Performance tracking
        self.prediction_accuracy: Dict[PredictionType, float] = defaultdict(float)
        self.intervention_effectiveness: Dict[InterventionType, float] = defaultdict(float)

        # Initialize system
        self._register_signal_processors()
        asyncio.create_task(self._initialize_predictive_system())

    async def _initialize_predictive_system(self) -> None:
        """Initialize the predictive assistant system."""
        try:
            # Load trained models
            await self._load_predictive_models()

            # Start background processes
            asyncio.create_task(self._continuous_signal_collection())
            asyncio.create_task(self._continuous_prediction_updates())
            asyncio.create_task(self._proactive_intervention_monitor())

            logger.info("Claude Predictive Assistant initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing predictive system: {str(e)}")

    def _register_signal_processors(self) -> None:
        """Register signal processing functions."""
        self.signal_processors = {
            "conversation_pace": self._process_conversation_pace,
            "sentiment_trend": self._process_sentiment_trend,
            "engagement_level": self._process_engagement_level,
            "response_time": self._process_response_time,
            "question_patterns": self._process_question_patterns,
            "topic_transitions": self._process_topic_transitions,
            "client_signals": self._process_client_signals,
            "agent_confidence": self._process_agent_confidence
        }

    async def start_conversation_monitoring(
        self, conversation_id: str, agent_id: str, client_id: str,
        interaction_type: WorkflowType
    ) -> ConversationState:
        """Start monitoring a conversation for predictive analysis."""
        try:
            conversation_state = ConversationState(
                conversation_id=conversation_id,
                agent_id=agent_id,
                client_id=client_id,
                start_time=datetime.now(),
                last_update=datetime.now(),
                message_count=0,
                interaction_type=interaction_type,
                current_stage="initial",
                sentiment_trend=[0.5],  # Neutral starting sentiment
                engagement_level=0.5,
                signals=[],
                predictions=[],
                interventions_sent=[]
            )

            self.active_conversations[conversation_id] = conversation_state

            # Generate initial predictions
            await self._generate_conversation_predictions(conversation_state)

            logger.info(f"Started monitoring conversation {conversation_id}")
            return conversation_state

        except Exception as e:
            logger.error(f"Error starting conversation monitoring: {str(e)}")
            raise

    async def update_conversation_state(
        self, conversation_id: str, update_data: Dict[str, Any]
    ) -> Optional[ConversationState]:
        """Update conversation state with new data."""
        try:
            if conversation_id not in self.active_conversations:
                logger.warning(f"Conversation {conversation_id} not being monitored")
                return None

            conversation_state = self.active_conversations[conversation_id]

            # Update basic state
            conversation_state.last_update = datetime.now()
            conversation_state.message_count += update_data.get("new_messages", 0)

            # Process and update signals
            new_signals = await self._extract_signals_from_update(conversation_state, update_data)
            conversation_state.signals.extend(new_signals)

            # Update conversation stage
            new_stage = self._detect_conversation_stage(conversation_state, update_data)
            if new_stage != conversation_state.current_stage:
                conversation_state.current_stage = new_stage
                logger.info(f"Conversation {conversation_id} transitioned to stage: {new_stage}")

            # Update predictions
            await self._update_conversation_predictions(conversation_state)

            # Check for intervention opportunities
            interventions = await self._check_intervention_opportunities(conversation_state)
            for intervention in interventions:
                await self._send_proactive_intervention(intervention)

            return conversation_state

        except Exception as e:
            logger.error(f"Error updating conversation state: {str(e)}")
            return None

    async def get_predictive_analysis(self, request: PredictiveRequest) -> PredictiveResponse:
        """Get predictive analysis for an agent or conversation."""
        try:
            predictions = []
            interventions = []

            # Get conversation state if specified
            conversation_state = None
            if request.conversation_id:
                conversation_state = self.active_conversations.get(request.conversation_id)

            # Generate predictions based on request
            for prediction_type in request.prediction_types:
                prediction = await self._generate_prediction(
                    prediction_type, request.agent_id, conversation_state, request.context
                )
                if prediction and prediction.probability >= request.confidence_threshold:
                    predictions.append(self._prediction_to_dict(prediction))

            # Generate intervention recommendations
            if conversation_state:
                potential_interventions = await self._generate_intervention_recommendations(
                    conversation_state, request.urgency_threshold
                )
                interventions = [self._intervention_to_dict(i) for i in potential_interventions]

            # Risk assessment
            risk_assessment = await self._assess_risks(request.agent_id, conversation_state)

            # Opportunity identification
            opportunities = await self._identify_opportunities(request.agent_id, conversation_state)

            # Generate recommendations
            recommendations = await self._generate_recommendations(
                predictions, interventions, risk_assessment, opportunities
            )

            # Calculate confidence summary
            confidence_summary = self._calculate_confidence_summary(predictions)

            # Next analysis time
            next_analysis_time = datetime.now() + timedelta(seconds=self.prediction_refresh_interval)

            return PredictiveResponse(
                agent_id=request.agent_id,
                conversation_id=request.conversation_id,
                predictions=predictions,
                interventions=interventions,
                risk_assessment=risk_assessment,
                opportunities=opportunities,
                recommendations=recommendations,
                confidence_summary=confidence_summary,
                next_analysis_time=next_analysis_time
            )

        except Exception as e:
            logger.error(f"Error getting predictive analysis: {str(e)}")
            return self._create_error_predictive_response(request, str(e))

    async def get_real_time_analysis(self, conversation_id: str) -> Optional[RealTimeAnalysis]:
        """Get real-time analysis of an active conversation."""
        try:
            if conversation_id not in self.active_conversations:
                return None

            conversation_state = self.active_conversations[conversation_id]

            # Current sentiment
            current_sentiment = conversation_state.sentiment_trend[-1] if conversation_state.sentiment_trend else 0.5

            # Risk indicators
            risk_indicators = []
            for signal in conversation_state.signals[-10:]:  # Last 10 signals
                if signal.signal_type in ["negative_sentiment", "low_engagement", "confusion_detected"]:
                    risk_indicators.append(f"{signal.signal_type}: {signal.value:.2f}")

            # Opportunity indicators
            opportunity_indicators = []
            for signal in conversation_state.signals[-10:]:
                if signal.signal_type in ["high_engagement", "buying_signals", "urgency_detected"]:
                    opportunity_indicators.append(f"{signal.signal_type}: {signal.value:.2f}")

            # Suggested next actions
            suggested_actions = await self._suggest_next_actions(conversation_state)

            # Intervention recommendations
            intervention_recs = []
            recent_predictions = [p for p in conversation_state.predictions if p.created_at > datetime.now() - timedelta(minutes=5)]
            for prediction in recent_predictions:
                if prediction.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]:
                    intervention_recs.append({
                        "type": prediction.prediction_type.value,
                        "recommendation": f"Based on {prediction.prediction_type.value} prediction",
                        "confidence": prediction.confidence.value,
                        "urgency": "medium"
                    })

            return RealTimeAnalysis(
                conversation_id=conversation_id,
                current_stage=conversation_state.current_stage,
                sentiment_score=current_sentiment,
                engagement_level=conversation_state.engagement_level,
                risk_indicators=risk_indicators,
                opportunity_indicators=opportunity_indicators,
                suggested_next_actions=suggested_actions,
                intervention_recommendations=intervention_recs
            )

        except Exception as e:
            logger.error(f"Error getting real-time analysis: {str(e)}")
            return None

    async def end_conversation_monitoring(
        self, conversation_id: str, outcome: OutcomeType,
        satisfaction_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """End conversation monitoring and update learning data."""
        try:
            if conversation_id not in self.active_conversations:
                return {"error": "Conversation not being monitored"}

            conversation_state = self.active_conversations[conversation_id]
            conversation_state.outcome = outcome

            # Calculate final metrics
            final_metrics = {
                "duration_minutes": (datetime.now() - conversation_state.start_time).total_seconds() / 60,
                "message_count": conversation_state.message_count,
                "stage_transitions": len(set(signal.context.get("stage") for signal in conversation_state.signals if signal.context.get("stage"))),
                "intervention_count": len(conversation_state.interventions_sent),
                "final_sentiment": conversation_state.sentiment_trend[-1] if conversation_state.sentiment_trend else 0.5,
                "final_engagement": conversation_state.engagement_level,
                "satisfaction_score": satisfaction_score
            }

            # Update prediction accuracy
            await self._update_prediction_accuracy(conversation_state, outcome, satisfaction_score)

            # Store conversation data for learning
            await self._store_conversation_learning_data(conversation_state, final_metrics)

            # Move to history
            self.conversation_history.append(conversation_state)
            del self.active_conversations[conversation_id]

            logger.info(f"Ended monitoring for conversation {conversation_id}")
            return {
                "status": "completed",
                "final_metrics": final_metrics,
                "predictions_made": len(conversation_state.predictions),
                "interventions_sent": len(conversation_state.interventions_sent)
            }

        except Exception as e:
            logger.error(f"Error ending conversation monitoring: {str(e)}")
            return {"error": str(e)}

    async def _extract_signals_from_update(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> List[PredictiveSignal]:
        """Extract predictive signals from conversation update data."""
        signals = []
        current_time = datetime.now()

        try:
            # Process each registered signal type
            for signal_type, processor in self.signal_processors.items():
                try:
                    signal_value = await processor(conversation_state, update_data)
                    if signal_value is not None:
                        signal = PredictiveSignal(
                            signal_id=f"{signal_type}_{conversation_state.conversation_id}_{int(current_time.timestamp())}",
                            signal_type=signal_type,
                            value=signal_value,
                            confidence=0.8,  # Default confidence
                            timestamp=current_time,
                            context=update_data,
                            source="real_time"
                        )
                        signals.append(signal)
                except Exception as e:
                    logger.warning(f"Error processing signal {signal_type}: {str(e)}")
                    continue

            return signals

        except Exception as e:
            logger.error(f"Error extracting signals: {str(e)}")
            return []

    # Signal processors
    async def _process_conversation_pace(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process conversation pace signal."""
        if conversation_state.message_count < 2:
            return None

        duration_minutes = (datetime.now() - conversation_state.start_time).total_seconds() / 60
        pace = conversation_state.message_count / duration_minutes if duration_minutes > 0 else 0

        # Normalize pace (0-1 scale, where 1 message per minute = 0.5)
        normalized_pace = min(1.0, pace / 2.0)
        return normalized_pace

    async def _process_sentiment_trend(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process sentiment trend signal."""
        # This would integrate with actual sentiment analysis
        # For now, simulate based on conversation data
        current_sentiment = update_data.get("sentiment_score", 0.5)

        conversation_state.sentiment_trend.append(current_sentiment)
        if len(conversation_state.sentiment_trend) > 10:
            conversation_state.sentiment_trend = conversation_state.sentiment_trend[-10:]

        # Calculate trend (positive trend = sentiment improving)
        if len(conversation_state.sentiment_trend) >= 3:
            recent = conversation_state.sentiment_trend[-3:]
            trend = (recent[-1] - recent[0]) / 2.0 + 0.5  # Normalize to 0-1
            return max(0.0, min(1.0, trend))

        return current_sentiment

    async def _process_engagement_level(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process engagement level signal."""
        engagement_indicators = {
            "question_count": update_data.get("question_count", 0),
            "response_speed": 1.0 / (update_data.get("avg_response_time", 60) / 60),  # Faster = higher engagement
            "message_length": min(1.0, update_data.get("avg_message_length", 50) / 100),
            "emoji_usage": min(1.0, update_data.get("emoji_count", 0) / 5),
            "enthusiasm_words": min(1.0, update_data.get("enthusiasm_score", 0))
        }

        # Weighted engagement score
        weights = {
            "question_count": 0.3,
            "response_speed": 0.25,
            "message_length": 0.2,
            "emoji_usage": 0.1,
            "enthusiasm_words": 0.15
        }

        engagement_level = sum(
            weights[indicator] * value
            for indicator, value in engagement_indicators.items()
        )

        conversation_state.engagement_level = engagement_level
        return engagement_level

    async def _process_response_time(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process response time signal."""
        response_time = update_data.get("last_response_time", 0)
        if response_time <= 0:
            return None

        # Normalize response time (0-1 scale, where 30 seconds = 0.5)
        normalized_time = max(0.0, min(1.0, (60 - response_time) / 60))
        return normalized_time

    async def _process_question_patterns(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process question patterns signal."""
        question_types = update_data.get("question_types", [])
        if not question_types:
            return None

        # Analyze question progression
        positive_patterns = ["specific_requirements", "next_steps", "timeline", "pricing"]
        negative_patterns = ["confusion", "repetitive", "concern", "objection"]

        positive_score = sum(1 for q in question_types if q in positive_patterns)
        negative_score = sum(1 for q in question_types if q in negative_patterns)
        total_questions = len(question_types)

        if total_questions == 0:
            return 0.5

        pattern_score = (positive_score - negative_score + total_questions) / (2 * total_questions)
        return max(0.0, min(1.0, pattern_score))

    async def _process_topic_transitions(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process topic transitions signal."""
        topic_changes = update_data.get("topic_changes", 0)
        message_count = update_data.get("new_messages", 1)

        # Calculate transition rate
        if message_count == 0:
            return None

        transition_rate = topic_changes / message_count

        # Lower transition rate generally indicates better flow
        flow_score = max(0.0, min(1.0, 1.0 - transition_rate))
        return flow_score

    async def _process_client_signals(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process client behavior signals."""
        client_signals = update_data.get("client_signals", {})
        if not client_signals:
            return None

        # Positive client signals
        positive_indicators = [
            "buying_keywords", "urgency_expressed", "budget_discussed",
            "availability_confirmed", "referral_mentioned"
        ]

        # Negative client signals
        negative_indicators = [
            "price_objections", "timeline_concerns", "competitor_mentioned",
            "hesitation_detected", "delay_requested"
        ]

        positive_score = sum(client_signals.get(indicator, 0) for indicator in positive_indicators)
        negative_score = sum(client_signals.get(indicator, 0) for indicator in negative_indicators)

        # Normalize to 0-1 scale
        total_signals = positive_score + negative_score
        if total_signals == 0:
            return 0.5

        client_signal_score = positive_score / total_signals
        return client_signal_score

    async def _process_agent_confidence(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> Optional[float]:
        """Process agent confidence signals."""
        agent_indicators = update_data.get("agent_indicators", {})

        confidence_factors = {
            "response_certainty": agent_indicators.get("response_certainty", 0.5),
            "question_clarity": agent_indicators.get("question_clarity", 0.5),
            "product_knowledge": agent_indicators.get("product_knowledge", 0.5),
            "process_adherence": agent_indicators.get("process_adherence", 0.5)
        }

        # Calculate weighted confidence score
        confidence_score = sum(confidence_factors.values()) / len(confidence_factors)
        return confidence_score

    def _detect_conversation_stage(
        self, conversation_state: ConversationState, update_data: Dict[str, Any]
    ) -> str:
        """Detect the current stage of the conversation."""
        # Simplified stage detection based on signals and content

        stage_indicators = update_data.get("stage_indicators", {})
        current_stage = conversation_state.current_stage

        # Stage progression rules
        stage_transitions = {
            "initial": {
                "next": "qualification",
                "triggers": ["questions_started", "information_gathering"]
            },
            "qualification": {
                "next": "presentation",
                "triggers": ["needs_identified", "budget_discussed"]
            },
            "presentation": {
                "next": "negotiation",
                "triggers": ["options_presented", "interest_confirmed"]
            },
            "negotiation": {
                "next": "closing",
                "triggers": ["terms_discussed", "objections_handled"]
            },
            "closing": {
                "next": "follow_up",
                "triggers": ["agreement_reached", "next_steps_defined"]
            }
        }

        # Check for stage transition triggers
        if current_stage in stage_transitions:
            transition_rule = stage_transitions[current_stage]
            triggers = transition_rule["triggers"]

            for trigger in triggers:
                if stage_indicators.get(trigger, False):
                    return transition_rule["next"]

        return current_stage

    async def _generate_conversation_predictions(self, conversation_state: ConversationState) -> None:
        """Generate initial predictions for a conversation."""
        try:
            prediction_types = [
                PredictionType.CONVERSATION_OUTCOME,
                PredictionType.CLIENT_SATISFACTION,
                PredictionType.CONVERSION_LIKELIHOOD
            ]

            for pred_type in prediction_types:
                prediction = await self._generate_prediction(
                    pred_type, conversation_state.agent_id, conversation_state, {}
                )
                if prediction:
                    conversation_state.predictions.append(prediction)
                    self.prediction_cache[prediction.prediction_id] = prediction

        except Exception as e:
            logger.error(f"Error generating conversation predictions: {str(e)}")

    async def _update_conversation_predictions(self, conversation_state: ConversationState) -> None:
        """Update predictions based on new conversation data."""
        try:
            # Update existing predictions with new data
            for prediction in conversation_state.predictions:
                if prediction.expires_at and prediction.expires_at < datetime.now():
                    continue

                # Re-evaluate prediction with new data
                updated_prediction = await self._generate_prediction(
                    prediction.prediction_type, conversation_state.agent_id,
                    conversation_state, {}
                )

                if updated_prediction:
                    # Update probability if significantly changed
                    probability_change = abs(prediction.probability - updated_prediction.probability)
                    if probability_change > 0.1:  # 10% threshold
                        prediction.probability = updated_prediction.probability
                        prediction.confidence = updated_prediction.confidence
                        prediction.contributing_factors = updated_prediction.contributing_factors

        except Exception as e:
            logger.error(f"Error updating predictions: {str(e)}")

    async def _generate_prediction(
        self, prediction_type: PredictionType, agent_id: str,
        conversation_state: Optional[ConversationState], context: Dict[str, Any]
    ) -> Optional[Prediction]:
        """Generate a specific prediction."""
        try:
            prediction_id = f"{prediction_type.value}_{agent_id}_{int(time.time())}"

            if prediction_type == PredictionType.CONVERSATION_OUTCOME:
                return await self._predict_conversation_outcome(prediction_id, agent_id, conversation_state)
            elif prediction_type == PredictionType.CLIENT_SATISFACTION:
                return await self._predict_client_satisfaction(prediction_id, agent_id, conversation_state)
            elif prediction_type == PredictionType.CONVERSION_LIKELIHOOD:
                return await self._predict_conversion_likelihood(prediction_id, agent_id, conversation_state)
            elif prediction_type == PredictionType.INTERVENTION_NEED:
                return await self._predict_intervention_need(prediction_id, agent_id, conversation_state)
            elif prediction_type == PredictionType.PERFORMANCE_RISK:
                return await self._predict_performance_risk(prediction_id, agent_id, conversation_state)
            else:
                return None

        except Exception as e:
            logger.error(f"Error generating {prediction_type} prediction: {str(e)}")
            return None

    async def _predict_conversation_outcome(
        self, prediction_id: str, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Optional[Prediction]:
        """Predict conversation outcome."""
        if not conversation_state:
            return None

        try:
            # Extract features for prediction
            features = self._extract_conversation_features(conversation_state)

            # Use ML model if available, otherwise use heuristics
            if self.conversation_outcome_predictor is not None:
                # Placeholder for actual ML prediction
                probability = 0.75  # Mock probability
                predicted_outcome = "positive"
            else:
                # Heuristic-based prediction
                engagement_factor = conversation_state.engagement_level
                sentiment_factor = conversation_state.sentiment_trend[-1] if conversation_state.sentiment_trend else 0.5
                stage_factor = {"initial": 0.3, "qualification": 0.5, "presentation": 0.7, "negotiation": 0.8, "closing": 0.9}.get(conversation_state.current_stage, 0.5)

                probability = (engagement_factor * 0.4 + sentiment_factor * 0.4 + stage_factor * 0.2)
                predicted_outcome = "positive" if probability > 0.6 else "neutral" if probability > 0.4 else "negative"

            confidence = self._calculate_confidence_level(probability)

            contributing_factors = [
                f"Engagement level: {conversation_state.engagement_level:.2f}",
                f"Sentiment trend: {conversation_state.sentiment_trend[-1]:.2f}" if conversation_state.sentiment_trend else "No sentiment data",
                f"Conversation stage: {conversation_state.current_stage}",
                f"Message count: {conversation_state.message_count}"
            ]

            return Prediction(
                prediction_id=prediction_id,
                prediction_type=PredictionType.CONVERSATION_OUTCOME,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                probability=probability,
                contributing_factors=contributing_factors,
                signals_used=conversation_state.signals[-5:],  # Last 5 signals
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=30),
                metadata={"model_version": "heuristic_v1", "features_used": len(features)}
            )

        except Exception as e:
            logger.error(f"Error predicting conversation outcome: {str(e)}")
            return None

    async def _predict_client_satisfaction(
        self, prediction_id: str, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Optional[Prediction]:
        """Predict client satisfaction."""
        if not conversation_state:
            return None

        try:
            # Calculate satisfaction based on multiple factors
            response_quality = sum(1 for signal in conversation_state.signals if signal.signal_type == "positive_response") / max(1, len(conversation_state.signals))
            conversation_flow = 1 - (sum(1 for signal in conversation_state.signals if signal.signal_type == "topic_transition") / max(1, conversation_state.message_count))
            agent_expertise = sum(1 for signal in conversation_state.signals if signal.signal_type == "expert_response") / max(1, len(conversation_state.signals))

            satisfaction_score = (response_quality * 0.4 + conversation_flow * 0.3 + agent_expertise * 0.3)

            predicted_outcome = "high" if satisfaction_score > 0.7 else "medium" if satisfaction_score > 0.4 else "low"
            confidence = self._calculate_confidence_level(satisfaction_score)

            contributing_factors = [
                f"Response quality: {response_quality:.2f}",
                f"Conversation flow: {conversation_flow:.2f}",
                f"Agent expertise: {agent_expertise:.2f}"
            ]

            return Prediction(
                prediction_id=prediction_id,
                prediction_type=PredictionType.CLIENT_SATISFACTION,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                probability=satisfaction_score,
                contributing_factors=contributing_factors,
                signals_used=conversation_state.signals[-3:],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=20),
                metadata={"satisfaction_model": "composite_v1"}
            )

        except Exception as e:
            logger.error(f"Error predicting client satisfaction: {str(e)}")
            return None

    async def _predict_conversion_likelihood(
        self, prediction_id: str, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Optional[Prediction]:
        """Predict conversion likelihood."""
        if not conversation_state:
            return None

        try:
            # Conversion indicators
            buying_signals = sum(1 for signal in conversation_state.signals if signal.signal_type in ["buying_signals", "urgency_detected"])
            objection_signals = sum(1 for signal in conversation_state.signals if signal.signal_type in ["price_objections", "hesitation_detected"])
            engagement_trend = conversation_state.engagement_level

            # Simple conversion probability calculation
            conversion_probability = max(0, min(1,
                (buying_signals * 0.3 + engagement_trend * 0.5 - objection_signals * 0.2 + 0.2)
            ))

            predicted_outcome = "high" if conversion_probability > 0.7 else "medium" if conversion_probability > 0.4 else "low"
            confidence = self._calculate_confidence_level(conversion_probability)

            contributing_factors = [
                f"Buying signals: {buying_signals}",
                f"Objection signals: {objection_signals}",
                f"Engagement level: {engagement_trend:.2f}",
                f"Conversation stage: {conversation_state.current_stage}"
            ]

            return Prediction(
                prediction_id=prediction_id,
                prediction_type=PredictionType.CONVERSION_LIKELIHOOD,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                probability=conversion_probability,
                contributing_factors=contributing_factors,
                signals_used=conversation_state.signals[-4:],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=45),
                metadata={"conversion_model": "signals_v1"}
            )

        except Exception as e:
            logger.error(f"Error predicting conversion likelihood: {str(e)}")
            return None

    async def _predict_intervention_need(
        self, prediction_id: str, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Optional[Prediction]:
        """Predict if intervention is needed."""
        if not conversation_state:
            return None

        try:
            # Risk indicators
            negative_signals = [s for s in conversation_state.signals if s.value < 0.4]
            stalled_conversation = conversation_state.message_count > 10 and conversation_state.current_stage == "initial"
            low_engagement = conversation_state.engagement_level < 0.3

            intervention_score = len(negative_signals) * 0.2 + (1 if stalled_conversation else 0) * 0.4 + (1 if low_engagement else 0) * 0.4

            predicted_outcome = "high" if intervention_score > 0.6 else "medium" if intervention_score > 0.3 else "low"
            confidence = self._calculate_confidence_level(intervention_score)

            contributing_factors = [
                f"Negative signals: {len(negative_signals)}",
                f"Conversation stalled: {stalled_conversation}",
                f"Low engagement: {low_engagement}",
                f"Current stage: {conversation_state.current_stage}"
            ]

            return Prediction(
                prediction_id=prediction_id,
                prediction_type=PredictionType.INTERVENTION_NEED,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                probability=intervention_score,
                contributing_factors=contributing_factors,
                signals_used=negative_signals[:3],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(minutes=15),
                metadata={"intervention_model": "risk_assessment_v1"}
            )

        except Exception as e:
            logger.error(f"Error predicting intervention need: {str(e)}")
            return None

    async def _predict_performance_risk(
        self, prediction_id: str, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Optional[Prediction]:
        """Predict performance risk for agent."""
        try:
            # Get agent profile and history
            agent_profile = await self.agent_service.get_agent_profile(agent_id)
            if not agent_profile:
                return None

            # Calculate risk factors
            experience_factor = max(0, (5 - agent_profile.years_experience) / 5)  # Higher risk for less experienced

            if conversation_state:
                current_performance = conversation_state.engagement_level * conversation_state.sentiment_trend[-1] if conversation_state.sentiment_trend else 0.25
            else:
                current_performance = 0.5  # Default

            performance_risk = (experience_factor * 0.4 + (1 - current_performance) * 0.6)

            predicted_outcome = "high" if performance_risk > 0.7 else "medium" if performance_risk > 0.4 else "low"
            confidence = self._calculate_confidence_level(performance_risk)

            contributing_factors = [
                f"Agent experience: {agent_profile.years_experience} years",
                f"Current performance: {current_performance:.2f}",
                f"Agent role: {agent_profile.primary_role.value}"
            ]

            return Prediction(
                prediction_id=prediction_id,
                prediction_type=PredictionType.PERFORMANCE_RISK,
                predicted_outcome=predicted_outcome,
                confidence=confidence,
                probability=performance_risk,
                contributing_factors=contributing_factors,
                signals_used=[],
                created_at=datetime.now(),
                expires_at=datetime.now() + timedelta(hours=1),
                metadata={"risk_model": "experience_performance_v1"}
            )

        except Exception as e:
            logger.error(f"Error predicting performance risk: {str(e)}")
            return None

    def _extract_conversation_features(self, conversation_state: ConversationState) -> List[float]:
        """Extract features from conversation state for ML models."""
        features = []

        # Basic conversation features
        features.append(conversation_state.message_count)
        features.append((datetime.now() - conversation_state.start_time).total_seconds() / 60)  # Duration in minutes
        features.append(conversation_state.engagement_level)

        # Sentiment features
        if conversation_state.sentiment_trend:
            features.extend([
                conversation_state.sentiment_trend[-1],  # Current sentiment
                np.mean(conversation_state.sentiment_trend),  # Average sentiment
                np.std(conversation_state.sentiment_trend) if len(conversation_state.sentiment_trend) > 1 else 0  # Sentiment volatility
            ])
        else:
            features.extend([0.5, 0.5, 0.0])

        # Stage encoding
        stage_encoding = {"initial": 0, "qualification": 1, "presentation": 2, "negotiation": 3, "closing": 4}.get(conversation_state.current_stage, 0)
        features.append(stage_encoding)

        # Signal-based features
        recent_signals = conversation_state.signals[-10:]  # Last 10 signals
        signal_types = ["positive", "negative", "neutral"]
        for signal_type in signal_types:
            count = sum(1 for s in recent_signals if signal_type in s.signal_type.lower())
            features.append(count)

        return features

    def _calculate_confidence_level(self, probability: float) -> ConfidenceLevel:
        """Calculate confidence level from probability."""
        if probability >= 0.9:
            return ConfidenceLevel.VERY_HIGH
        elif probability >= 0.8:
            return ConfidenceLevel.HIGH
        elif probability >= 0.65:
            return ConfidenceLevel.MEDIUM
        elif probability >= 0.5:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.VERY_LOW

    async def _check_intervention_opportunities(
        self, conversation_state: ConversationState
    ) -> List[ProactiveIntervention]:
        """Check for proactive intervention opportunities."""
        interventions = []

        try:
            # Check recent predictions for intervention needs
            recent_predictions = [
                p for p in conversation_state.predictions
                if p.created_at > datetime.now() - timedelta(minutes=5)
            ]

            for prediction in recent_predictions:
                if prediction.prediction_type == PredictionType.INTERVENTION_NEED and prediction.probability > 0.6:
                    intervention = await self._create_intervention_from_prediction(conversation_state, prediction)
                    if intervention:
                        interventions.append(intervention)

                elif prediction.prediction_type == PredictionType.CONVERSION_LIKELIHOOD and prediction.probability > 0.8:
                    # High conversion likelihood - suggest closing techniques
                    intervention = ProactiveIntervention(
                        intervention_id=f"closing_opportunity_{int(time.time())}",
                        intervention_type=InterventionType.OPPORTUNITY_ALERT,
                        urgency=UrgencyLevel.HIGH,
                        title="High Conversion Opportunity",
                        description="Client showing strong buying signals",
                        guidance="Consider transitioning to closing techniques. Client appears ready to move forward.",
                        predicted_impact=0.8,
                        timing_window={
                            "start": datetime.now(),
                            "end": datetime.now() + timedelta(minutes=10),
                            "optimal": datetime.now() + timedelta(minutes=2)
                        },
                        target_agent_id=conversation_state.agent_id,
                        conversation_context={"conversation_id": conversation_state.conversation_id},
                        supporting_predictions=[prediction],
                        action_items=["Review closing techniques", "Identify next steps", "Ask for commitment"],
                        resources=["Closing scripts", "Objection handling guide"]
                    )
                    interventions.append(intervention)

            return interventions

        except Exception as e:
            logger.error(f"Error checking intervention opportunities: {str(e)}")
            return []

    async def _create_intervention_from_prediction(
        self, conversation_state: ConversationState, prediction: Prediction
    ) -> Optional[ProactiveIntervention]:
        """Create intervention from prediction."""
        try:
            if prediction.predicted_outcome == "high":
                urgency = UrgencyLevel.HIGH
                guidance = "Immediate intervention recommended. Consider providing strategic guidance or escalating to supervisor."
            elif prediction.predicted_outcome == "medium":
                urgency = UrgencyLevel.MEDIUM
                guidance = "Moderate intervention suggested. Provide coaching or process guidance to improve conversation flow."
            else:
                urgency = UrgencyLevel.LOW
                guidance = "Monitor conversation closely. Consider light coaching if patterns continue."

            intervention = ProactiveIntervention(
                intervention_id=f"intervention_{prediction.prediction_id}",
                intervention_type=InterventionType.COACHING_SUGGESTION,
                urgency=urgency,
                title=f"Intervention Needed - {prediction.predicted_outcome.title()} Risk",
                description=f"Prediction model indicates {prediction.predicted_outcome} intervention need",
                guidance=guidance,
                predicted_impact=prediction.probability,
                timing_window={
                    "start": datetime.now(),
                    "end": datetime.now() + timedelta(minutes=20),
                    "optimal": datetime.now() + timedelta(minutes=3)
                },
                target_agent_id=conversation_state.agent_id,
                conversation_context={"conversation_id": conversation_state.conversation_id},
                supporting_predictions=[prediction],
                action_items=self._generate_intervention_actions(prediction),
                resources=self._suggest_intervention_resources(prediction)
            )

            return intervention

        except Exception as e:
            logger.error(f"Error creating intervention from prediction: {str(e)}")
            return None

    def _generate_intervention_actions(self, prediction: Prediction) -> List[str]:
        """Generate action items for intervention."""
        actions = []

        if prediction.prediction_type == PredictionType.INTERVENTION_NEED:
            if "low engagement" in str(prediction.contributing_factors).lower():
                actions.extend([
                    "Ask open-ended questions to increase engagement",
                    "Use client's name more frequently",
                    "Shift to more interactive conversation style"
                ])
            if "negative sentiment" in str(prediction.contributing_factors).lower():
                actions.extend([
                    "Address any concerns directly",
                    "Use empathetic language",
                    "Refocus on client benefits"
                ])

        return actions[:3]  # Limit to 3 actions

    def _suggest_intervention_resources(self, prediction: Prediction) -> List[str]:
        """Suggest resources for intervention."""
        resources = []

        if prediction.prediction_type == PredictionType.INTERVENTION_NEED:
            resources.extend([
                "Engagement techniques guide",
                "Objection handling scripts",
                "Conversation flow checklist"
            ])

        return resources

    async def _send_proactive_intervention(self, intervention: ProactiveIntervention) -> bool:
        """Send proactive intervention to agent."""
        try:
            # Check cooldown period
            recent_interventions = [
                i for i in self.intervention_history
                if i.target_agent_id == intervention.target_agent_id
                and i.created_at > datetime.now() - timedelta(minutes=self.intervention_cooldown_minutes)
            ]

            if len(recent_interventions) >= 3:  # Max 3 interventions per cooldown period
                logger.info(f"Intervention cooldown active for agent {intervention.target_agent_id}")
                return False

            # Send intervention (in real implementation, this would send to UI/notification system)
            intervention_data = {
                "intervention_id": intervention.intervention_id,
                "type": intervention.intervention_type.value,
                "urgency": intervention.urgency.value,
                "title": intervention.title,
                "description": intervention.description,
                "guidance": intervention.guidance,
                "action_items": intervention.action_items,
                "resources": intervention.resources,
                "timing": {
                    "optimal_time": intervention.timing_window["optimal"].isoformat(),
                    "expires_at": intervention.timing_window["end"].isoformat()
                }
            }

            # Store intervention in conversation state
            if intervention.conversation_context.get("conversation_id") in self.active_conversations:
                conversation_state = self.active_conversations[intervention.conversation_context["conversation_id"]]
                conversation_state.interventions_sent.append(intervention.intervention_id)

            # Add to intervention history
            self.intervention_history.append(intervention)

            # Cache intervention data
            cache_key = f"intervention:{intervention.intervention_id}"
            await self.redis_client.setex(
                cache_key,
                3600,  # 1 hour
                json.dumps(intervention_data)
            )

            logger.info(f"Sent proactive intervention {intervention.intervention_id} to agent {intervention.target_agent_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending proactive intervention: {str(e)}")
            return False

    async def _generate_intervention_recommendations(
        self, conversation_state: ConversationState, urgency_threshold: UrgencyLevel
    ) -> List[ProactiveIntervention]:
        """Generate intervention recommendations for a conversation."""
        recommendations = []

        try:
            # Analyze current conversation state
            risk_level = await self._assess_conversation_risk(conversation_state)
            opportunity_level = await self._assess_conversation_opportunity(conversation_state)

            # Generate risk-based interventions
            if risk_level > 0.6:
                risk_intervention = ProactiveIntervention(
                    intervention_id=f"risk_{conversation_state.conversation_id}_{int(time.time())}",
                    intervention_type=InterventionType.RISK_WARNING,
                    urgency=UrgencyLevel.HIGH if risk_level > 0.8 else UrgencyLevel.MEDIUM,
                    title="Conversation Risk Detected",
                    description=f"Risk level: {risk_level:.2f}",
                    guidance="Consider adjusting approach based on client signals",
                    predicted_impact=risk_level,
                    timing_window={
                        "start": datetime.now(),
                        "end": datetime.now() + timedelta(minutes=15),
                        "optimal": datetime.now() + timedelta(minutes=2)
                    },
                    target_agent_id=conversation_state.agent_id,
                    conversation_context={"conversation_id": conversation_state.conversation_id},
                    supporting_predictions=[]
                )
                recommendations.append(risk_intervention)

            # Generate opportunity-based interventions
            if opportunity_level > 0.7:
                opportunity_intervention = ProactiveIntervention(
                    intervention_id=f"opportunity_{conversation_state.conversation_id}_{int(time.time())}",
                    intervention_type=InterventionType.OPPORTUNITY_ALERT,
                    urgency=UrgencyLevel.MEDIUM,
                    title="Opportunity Identified",
                    description=f"Opportunity level: {opportunity_level:.2f}",
                    guidance="Client showing positive signals - consider advancing conversation",
                    predicted_impact=opportunity_level,
                    timing_window={
                        "start": datetime.now(),
                        "end": datetime.now() + timedelta(minutes=10),
                        "optimal": datetime.now() + timedelta(minutes=1)
                    },
                    target_agent_id=conversation_state.agent_id,
                    conversation_context={"conversation_id": conversation_state.conversation_id},
                    supporting_predictions=[]
                )
                recommendations.append(opportunity_intervention)

            return recommendations

        except Exception as e:
            logger.error(f"Error generating intervention recommendations: {str(e)}")
            return []

    async def _assess_conversation_risk(self, conversation_state: ConversationState) -> float:
        """Assess risk level for conversation."""
        risk_factors = []

        # Low engagement risk
        if conversation_state.engagement_level < 0.3:
            risk_factors.append(0.4)

        # Negative sentiment risk
        if conversation_state.sentiment_trend and conversation_state.sentiment_trend[-1] < 0.4:
            risk_factors.append(0.3)

        # Stalled conversation risk
        if conversation_state.message_count > 15 and conversation_state.current_stage == "initial":
            risk_factors.append(0.5)

        # Calculate overall risk
        overall_risk = sum(risk_factors) / len(risk_factors) if risk_factors else 0
        return min(1.0, overall_risk)

    async def _assess_conversation_opportunity(self, conversation_state: ConversationState) -> float:
        """Assess opportunity level for conversation."""
        opportunity_factors = []

        # High engagement opportunity
        if conversation_state.engagement_level > 0.7:
            opportunity_factors.append(0.4)

        # Positive sentiment opportunity
        if conversation_state.sentiment_trend and conversation_state.sentiment_trend[-1] > 0.7:
            opportunity_factors.append(0.3)

        # Advanced stage opportunity
        stage_scores = {"presentation": 0.3, "negotiation": 0.4, "closing": 0.5}
        if conversation_state.current_stage in stage_scores:
            opportunity_factors.append(stage_scores[conversation_state.current_stage])

        # Calculate overall opportunity
        overall_opportunity = sum(opportunity_factors) / len(opportunity_factors) if opportunity_factors else 0
        return min(1.0, overall_opportunity)

    async def _assess_risks(
        self, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> Dict[str, Any]:
        """Assess various risks for agent or conversation."""
        risks = {
            "overall_risk_level": 0.0,
            "risk_categories": {},
            "mitigation_suggestions": []
        }

        try:
            risk_categories = {}

            # Performance risk
            perf_risk_prediction = await self._generate_prediction(
                PredictionType.PERFORMANCE_RISK, agent_id, conversation_state, {}
            )
            if perf_risk_prediction:
                risk_categories["performance"] = perf_risk_prediction.probability

            # Conversation risk
            if conversation_state:
                conversation_risk = await self._assess_conversation_risk(conversation_state)
                risk_categories["conversation"] = conversation_risk

            # Calculate overall risk
            if risk_categories:
                overall_risk = sum(risk_categories.values()) / len(risk_categories)
                risks["overall_risk_level"] = overall_risk
                risks["risk_categories"] = risk_categories

                # Generate mitigation suggestions
                if overall_risk > 0.7:
                    risks["mitigation_suggestions"] = [
                        "Consider immediate supervisor intervention",
                        "Provide additional coaching resources",
                        "Monitor conversation closely"
                    ]
                elif overall_risk > 0.4:
                    risks["mitigation_suggestions"] = [
                        "Offer proactive guidance",
                        "Check in with agent",
                        "Review conversation progress"
                    ]

            return risks

        except Exception as e:
            logger.error(f"Error assessing risks: {str(e)}")
            return risks

    async def _identify_opportunities(
        self, agent_id: str, conversation_state: Optional[ConversationState]
    ) -> List[Dict[str, Any]]:
        """Identify opportunities for improvement or success."""
        opportunities = []

        try:
            if conversation_state:
                opportunity_level = await self._assess_conversation_opportunity(conversation_state)

                if opportunity_level > 0.6:
                    opportunities.append({
                        "type": "conversation_opportunity",
                        "title": "Strong Conversion Opportunity",
                        "description": f"Client showing positive signals (score: {opportunity_level:.2f})",
                        "recommended_action": "Advance conversation to next stage",
                        "impact_potential": opportunity_level,
                        "timing": "immediate"
                    })

                # Check for specific signal-based opportunities
                recent_signals = conversation_state.signals[-5:]
                positive_signals = [s for s in recent_signals if s.value > 0.7]

                if len(positive_signals) >= 3:
                    opportunities.append({
                        "type": "engagement_opportunity",
                        "title": "High Client Engagement",
                        "description": f"Client showing sustained high engagement ({len(positive_signals)} positive signals)",
                        "recommended_action": "Capitalize on engagement with detailed product presentation",
                        "impact_potential": 0.8,
                        "timing": "within_5_minutes"
                    })

            return opportunities

        except Exception as e:
            logger.error(f"Error identifying opportunities: {str(e)}")
            return []

    async def _suggest_next_actions(self, conversation_state: ConversationState) -> List[str]:
        """Suggest next actions for agent based on conversation state."""
        suggestions = []

        try:
            # Stage-based suggestions
            stage_suggestions = {
                "initial": [
                    "Ask qualifying questions about client needs",
                    "Establish rapport and trust",
                    "Understand client timeline and budget"
                ],
                "qualification": [
                    "Identify specific property requirements",
                    "Explore client motivations and priorities",
                    "Present relevant market information"
                ],
                "presentation": [
                    "Show properties that match client criteria",
                    "Highlight unique selling points",
                    "Address any client questions or concerns"
                ],
                "negotiation": [
                    "Discuss terms and pricing",
                    "Handle objections professionally",
                    "Find win-win solutions"
                ],
                "closing": [
                    "Confirm client commitment",
                    "Outline next steps clearly",
                    "Schedule follow-up activities"
                ]
            }

            # Get stage-specific suggestions
            suggestions.extend(stage_suggestions.get(conversation_state.current_stage, []))

            # Add engagement-specific suggestions
            if conversation_state.engagement_level < 0.4:
                suggestions.insert(0, "Increase client engagement with interactive questions")

            # Add sentiment-specific suggestions
            if conversation_state.sentiment_trend and conversation_state.sentiment_trend[-1] < 0.4:
                suggestions.insert(0, "Address any client concerns or hesitations")

            return suggestions[:3]  # Return top 3 suggestions

        except Exception as e:
            logger.error(f"Error suggesting next actions: {str(e)}")
            return ["Continue conversation professionally", "Monitor client response", "Seek guidance if needed"]

    async def _generate_recommendations(
        self, predictions: List[Dict], interventions: List[Dict],
        risk_assessment: Dict, opportunities: List[Dict]
    ) -> List[str]:
        """Generate overall recommendations based on analysis."""
        recommendations = []

        try:
            # High-risk recommendations
            if risk_assessment.get("overall_risk_level", 0) > 0.7:
                recommendations.append("High risk detected - consider immediate intervention or escalation")

            # High-opportunity recommendations
            high_value_opportunities = [opp for opp in opportunities if opp.get("impact_potential", 0) > 0.7]
            if high_value_opportunities:
                recommendations.append(f"Capitalize on {len(high_value_opportunities)} high-value opportunities identified")

            # Prediction-based recommendations
            high_confidence_predictions = [pred for pred in predictions if pred.get("confidence") in ["high", "very_high"]]
            if high_confidence_predictions:
                recommendations.append(f"Act on {len(high_confidence_predictions)} high-confidence predictions")

            # Intervention recommendations
            urgent_interventions = [inv for inv in interventions if inv.get("urgency") in ["high", "critical"]]
            if urgent_interventions:
                recommendations.append(f"Address {len(urgent_interventions)} urgent intervention needs")

            # Default recommendations if none above apply
            if not recommendations:
                recommendations = [
                    "Continue monitoring conversation progress",
                    "Maintain professional engagement standards",
                    "Follow established process guidelines"
                ]

            return recommendations[:5]  # Limit to 5 recommendations

        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            return ["Monitor situation and follow best practices"]

    def _calculate_confidence_summary(self, predictions: List[Dict]) -> Dict[str, float]:
        """Calculate confidence summary from predictions."""
        summary = {
            "average_confidence": 0.0,
            "high_confidence_count": 0,
            "total_predictions": len(predictions)
        }

        if predictions:
            confidence_values = [
                {"very_high": 0.95, "high": 0.85, "medium": 0.725, "low": 0.575, "very_low": 0.4}.get(pred.get("confidence", "medium"), 0.7)
                for pred in predictions
            ]

            summary["average_confidence"] = sum(confidence_values) / len(confidence_values)
            summary["high_confidence_count"] = sum(1 for conf in confidence_values if conf >= 0.8)

        return summary

    # Background processes
    async def _continuous_signal_collection(self) -> None:
        """Background process for continuous signal collection."""
        while True:
            try:
                await asyncio.sleep(self.signal_collection_interval)

                # Collect signals for all active conversations
                for conversation_id, conversation_state in self.active_conversations.items():
                    # Simulated signal collection - in real implementation,
                    # this would collect data from various sources
                    await self._collect_ambient_signals(conversation_state)

            except Exception as e:
                logger.error(f"Error in continuous signal collection: {str(e)}")

    async def _continuous_prediction_updates(self) -> None:
        """Background process for updating predictions."""
        while True:
            try:
                await asyncio.sleep(self.prediction_refresh_interval)

                # Update predictions for all active conversations
                for conversation_state in self.active_conversations.values():
                    await self._update_conversation_predictions(conversation_state)

            except Exception as e:
                logger.error(f"Error in continuous prediction updates: {str(e)}")

    async def _proactive_intervention_monitor(self) -> None:
        """Background process for monitoring intervention opportunities."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds

                # Check all active conversations for intervention needs
                for conversation_state in self.active_conversations.values():
                    interventions = await self._check_intervention_opportunities(conversation_state)
                    for intervention in interventions:
                        await self._send_proactive_intervention(intervention)

            except Exception as e:
                logger.error(f"Error in proactive intervention monitor: {str(e)}")

    async def _collect_ambient_signals(self, conversation_state: ConversationState) -> None:
        """Collect ambient signals for a conversation."""
        try:
            # This is a placeholder for ambient signal collection
            # In a real implementation, this would integrate with:
            # - Voice tone analysis
            # - Typing pattern analysis
            # - Browser activity monitoring
            # - Real-time sentiment analysis
            pass

        except Exception as e:
            logger.error(f"Error collecting ambient signals: {str(e)}")

    # Utility methods
    def _prediction_to_dict(self, prediction: Prediction) -> Dict[str, Any]:
        """Convert Prediction to dictionary."""
        return {
            "prediction_id": prediction.prediction_id,
            "prediction_type": prediction.prediction_type.value,
            "predicted_outcome": prediction.predicted_outcome,
            "confidence": prediction.confidence.value,
            "probability": prediction.probability,
            "contributing_factors": prediction.contributing_factors,
            "created_at": prediction.created_at.isoformat(),
            "expires_at": prediction.expires_at.isoformat() if prediction.expires_at else None,
            "metadata": prediction.metadata
        }

    def _intervention_to_dict(self, intervention: ProactiveIntervention) -> Dict[str, Any]:
        """Convert ProactiveIntervention to dictionary."""
        return {
            "intervention_id": intervention.intervention_id,
            "intervention_type": intervention.intervention_type.value,
            "urgency": intervention.urgency.value,
            "title": intervention.title,
            "description": intervention.description,
            "guidance": intervention.guidance,
            "predicted_impact": intervention.predicted_impact,
            "timing_window": {
                k: v.isoformat() for k, v in intervention.timing_window.items()
            },
            "action_items": intervention.action_items,
            "resources": intervention.resources,
            "success_metrics": intervention.success_metrics
        }

    async def _update_prediction_accuracy(
        self, conversation_state: ConversationState, outcome: OutcomeType,
        satisfaction_score: Optional[float]
    ) -> None:
        """Update prediction accuracy based on actual outcomes."""
        try:
            for prediction in conversation_state.predictions:
                if prediction.prediction_type == PredictionType.CONVERSATION_OUTCOME:
                    # Map outcomes to predictions
                    predicted_positive = prediction.predicted_outcome in ["positive", "high"]
                    actual_positive = outcome in [OutcomeType.POSITIVE, OutcomeType.EXCEPTIONAL]

                    accuracy = 1.0 if predicted_positive == actual_positive else 0.0

                    # Update rolling accuracy
                    current_accuracy = self.prediction_accuracy[prediction.prediction_type]
                    self.prediction_accuracy[prediction.prediction_type] = (current_accuracy * 0.9 + accuracy * 0.1)

                elif prediction.prediction_type == PredictionType.CLIENT_SATISFACTION and satisfaction_score is not None:
                    predicted_high_satisfaction = prediction.predicted_outcome in ["high"]
                    actual_high_satisfaction = satisfaction_score > 0.7

                    accuracy = 1.0 if predicted_high_satisfaction == actual_high_satisfaction else 0.0

                    current_accuracy = self.prediction_accuracy[prediction.prediction_type]
                    self.prediction_accuracy[prediction.prediction_type] = (current_accuracy * 0.9 + accuracy * 0.1)

        except Exception as e:
            logger.error(f"Error updating prediction accuracy: {str(e)}")

    async def _store_conversation_learning_data(
        self, conversation_state: ConversationState, final_metrics: Dict[str, Any]
    ) -> None:
        """Store conversation data for learning and model improvement."""
        try:
            learning_data = {
                "conversation_id": conversation_state.conversation_id,
                "agent_id": conversation_state.agent_id,
                "interaction_type": conversation_state.interaction_type.value,
                "outcome": conversation_state.outcome.value if conversation_state.outcome else "unknown",
                "final_metrics": final_metrics,
                "predictions_made": len(conversation_state.predictions),
                "interventions_sent": len(conversation_state.interventions_sent),
                "signals_collected": len(conversation_state.signals),
                "timestamp": datetime.now().isoformat()
            }

            # Store in Redis for later analysis
            cache_key = f"predictive_learning:{conversation_state.conversation_id}"
            await self.redis_client.setex(
                cache_key,
                30 * 24 * 3600,  # 30 days
                json.dumps(learning_data)
            )

            # Update learning optimizer if available
            if hasattr(self.learning_optimizer, 'record_conversation_outcome'):
                await self.learning_optimizer.record_conversation_outcome(
                    conversation_state.conversation_id,
                    conversation_state.agent_id,
                    conversation_state.interaction_type,
                    conversation_state.outcome,
                    final_metrics.get("satisfaction_score"),
                    final_metrics
                )

        except Exception as e:
            logger.error(f"Error storing conversation learning data: {str(e)}")

    async def _load_predictive_models(self) -> None:
        """Load pre-trained predictive models."""
        try:
            # Placeholder for model loading
            # In practice, this would load actual ML models from storage
            logger.info("Predictive models loaded (placeholder implementation)")

        except Exception as e:
            logger.error(f"Error loading predictive models: {str(e)}")

    def _create_error_predictive_response(
        self, request: PredictiveRequest, error_message: str
    ) -> PredictiveResponse:
        """Create error response for failed predictive analysis."""
        return PredictiveResponse(
            agent_id=request.agent_id,
            conversation_id=request.conversation_id,
            predictions=[],
            interventions=[],
            risk_assessment={"error": error_message},
            opportunities=[],
            recommendations=[f"Analysis failed: {error_message}"],
            confidence_summary={"error": True},
            next_analysis_time=datetime.now() + timedelta(minutes=5)
        )

    async def get_predictive_status(self) -> Dict[str, Any]:
        """Get current status of the predictive assistant."""
        try:
            return {
                "active_conversations": len(self.active_conversations),
                "prediction_cache_size": len(self.prediction_cache),
                "intervention_history_count": len(self.intervention_history),
                "prediction_accuracy": dict(self.prediction_accuracy),
                "intervention_effectiveness": dict(self.intervention_effectiveness),
                "models_loaded": {
                    "conversation_outcome_predictor": self.conversation_outcome_predictor is not None,
                    "intervention_timing_predictor": self.intervention_timing_predictor is not None,
                    "satisfaction_predictor": self.satisfaction_predictor is not None,
                    "risk_predictor": self.risk_predictor is not None
                },
                "system_health": {
                    "signal_processors_count": len(self.signal_processors),
                    "background_processes_active": True,  # Simplified check
                    "redis_connected": True  # Simplified check
                }
            }

        except Exception as e:
            logger.error(f"Error getting predictive status: {str(e)}")
            return {"error": str(e)}