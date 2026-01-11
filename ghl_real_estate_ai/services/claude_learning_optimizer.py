"""
Claude Learning & Optimization Engine - Phase 4: Self-Improving AI Coaching

This service implements machine learning-driven optimization for Claude coaching effectiveness,
analyzing conversation patterns, coaching outcomes, and agent performance to continuously
improve the quality and relevance of AI-generated guidance.

Key Features:
- Conversation pattern analysis and outcome prediction
- Coaching effectiveness tracking and optimization
- Agent behavior learning and personalization
- Real-time feedback loop integration
- Performance-based model fine-tuning
- Predictive coaching intervention strategies

Integration with the orchestration engine for comprehensive intelligence enhancement.
"""

import asyncio
import json
import logging
import numpy as np
import pandas as pd
import pickle
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel, Field
import redis.asyncio as redis
from sklearn.ensemble import RandomForestClassifier, GradientBoostingRegressor
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, mean_squared_error, classification_report

from ..core.service_registry import ServiceRegistry
from ..services.agent_profile_service import AgentProfileService
from ..services.claude_orchestration_engine import ClaudeOrchestrationEngine
from ..models.agent_profile_models import AgentProfile, AgentRole, GuidanceType

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LearningObjective(str, Enum):
    """Learning objectives for optimization engine."""
    COACHING_EFFECTIVENESS = "coaching_effectiveness"
    RESPONSE_RELEVANCE = "response_relevance"
    CONVERSION_OPTIMIZATION = "conversion_optimization"
    EFFICIENCY_IMPROVEMENT = "efficiency_improvement"
    PERSONALIZATION_ENHANCEMENT = "personalization_enhancement"
    RISK_MITIGATION = "risk_mitigation"
    SATISFACTION_OPTIMIZATION = "satisfaction_optimization"


class InteractionType(str, Enum):
    """Types of agent-Claude interactions for analysis."""
    LEAD_QUALIFICATION = "lead_qualification"
    PROPERTY_CONSULTATION = "property_consultation"
    NEGOTIATION_COACHING = "negotiation_coaching"
    MARKET_ANALYSIS = "market_analysis"
    PERFORMANCE_REVIEW = "performance_review"
    PROCESS_GUIDANCE = "process_guidance"
    CLIENT_COMMUNICATION = "client_communication"
    CRISIS_MANAGEMENT = "crisis_management"


class OutcomeType(str, Enum):
    """Outcome categories for learning analysis."""
    POSITIVE = "positive"           # Successful outcome, high satisfaction
    NEUTRAL = "neutral"             # Adequate outcome, moderate satisfaction
    NEGATIVE = "negative"           # Poor outcome, low satisfaction
    EXCEPTIONAL = "exceptional"     # Outstanding outcome, very high satisfaction
    UNKNOWN = "unknown"             # Outcome not yet determined


class LearningFeature(str, Enum):
    """Feature categories for machine learning models."""
    CONVERSATION_LENGTH = "conversation_length"
    RESPONSE_TIME = "response_time"
    GUIDANCE_TYPE_MIX = "guidance_type_mix"
    AGENT_EXPERIENCE = "agent_experience"
    CLIENT_COMPLEXITY = "client_complexity"
    MARKET_CONDITIONS = "market_conditions"
    TIME_OF_DAY = "time_of_day"
    DAY_OF_WEEK = "day_of_week"
    SEASONAL_FACTORS = "seasonal_factors"
    INTERACTION_FREQUENCY = "interaction_frequency"


@dataclass
class ConversationData:
    """Structured conversation data for learning analysis."""
    conversation_id: str
    agent_id: str
    interaction_type: InteractionType
    guidance_types: List[GuidanceType]
    start_time: datetime
    end_time: datetime
    messages_count: int
    claude_responses_count: int
    outcome: OutcomeType
    satisfaction_score: Optional[float] = None  # 0.0 to 1.0
    conversion_achieved: Optional[bool] = None
    follow_up_required: bool = False
    agent_feedback: Optional[str] = None
    context_metadata: Dict[str, Any] = field(default_factory=dict)
    features: Dict[LearningFeature, float] = field(default_factory=dict)


@dataclass
class LearningPattern:
    """Discovered patterns from conversation analysis."""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    predicted_outcome: OutcomeType
    confidence_score: float
    sample_size: int
    effectiveness_metrics: Dict[str, float]
    recommendations: List[str]
    created_at: datetime
    last_validated: datetime


@dataclass
class OptimizationRule:
    """Rules derived from learning patterns for coaching optimization."""
    rule_id: str
    rule_type: str
    trigger_conditions: Dict[str, Any]
    optimization_action: str
    expected_improvement: float
    priority_score: float
    success_rate: float
    created_at: datetime
    last_applied: Optional[datetime] = None
    application_count: int = 0


class LearningRequest(BaseModel):
    """Request for learning analysis or optimization."""
    objective: LearningObjective
    agent_id: Optional[str] = None
    interaction_type: Optional[InteractionType] = None
    time_period_hours: int = Field(default=24, ge=1, le=8760)  # 1 hour to 1 year
    include_patterns: bool = True
    include_recommendations: bool = True
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)


class LearningResponse(BaseModel):
    """Response from learning analysis."""
    objective: LearningObjective
    analysis_period: str
    total_conversations: int
    patterns_discovered: int
    optimization_rules: int
    effectiveness_score: float
    improvement_potential: float
    key_insights: List[str]
    recommended_actions: List[str]
    performance_metrics: Dict[str, float]
    confidence_level: float


class CoachingOptimization(BaseModel):
    """Coaching optimization recommendations."""
    agent_id: str
    optimization_type: str
    current_effectiveness: float
    target_effectiveness: float
    recommended_changes: List[str]
    expected_improvement: float
    implementation_priority: float
    monitoring_metrics: List[str]


class ClaudeLearningOptimizer:
    """Learning and optimization engine for Claude coaching effectiveness."""

    def __init__(
        self,
        service_registry: ServiceRegistry,
        redis_client: Optional[redis.Redis] = None,
        model_storage_path: str = "ml_models/claude_optimization"
    ):
        self.service_registry = service_registry
        self.redis_client = redis_client or redis.from_url("redis://localhost:6379/0")
        self.agent_service = AgentProfileService(service_registry, redis_client)

        # ML Models storage
        self.model_storage_path = Path(model_storage_path)
        self.model_storage_path.mkdir(parents=True, exist_ok=True)

        # ML Models for different objectives
        self.effectiveness_predictor: Optional[GradientBoostingRegressor] = None
        self.outcome_classifier: Optional[RandomForestClassifier] = None
        self.satisfaction_predictor: Optional[GradientBoostingRegressor] = None
        self.pattern_clusterer: Optional[KMeans] = None
        self.feature_scaler: Optional[StandardScaler] = None

        # Learning state
        self.conversation_data: List[ConversationData] = []
        self.discovered_patterns: Dict[str, LearningPattern] = {}
        self.optimization_rules: Dict[str, OptimizationRule] = {}
        self.learning_history: List[Dict[str, Any]] = []

        # Configuration
        self.min_data_points = 50  # Minimum data points for ML training
        self.pattern_confidence_threshold = 0.75
        self.optimization_threshold = 0.1  # Minimum improvement to suggest optimization
        self.retraining_interval_hours = 24
        self.max_stored_conversations = 10000

        # Performance tracking
        self.model_performance: Dict[str, Dict[str, float]] = {}
        self.last_training_time = None

        # Initialize learning system
        asyncio.create_task(self._initialize_learning_system())

    async def _initialize_learning_system(self) -> None:
        """Initialize the learning system with existing data and models."""
        try:
            # Load existing models
            await self._load_trained_models()

            # Load historical conversation data
            await self._load_historical_data()

            # Initialize feature extraction
            self._initialize_feature_extraction()

            logger.info("Claude Learning Optimizer initialized successfully")

        except Exception as e:
            logger.error(f"Error initializing learning system: {str(e)}")

    async def record_conversation_outcome(
        self, conversation_id: str, agent_id: str, interaction_type: InteractionType,
        outcome: OutcomeType, satisfaction_score: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Record conversation outcome for learning analysis."""
        try:
            # Get conversation details from cache/database
            conversation_data = await self._extract_conversation_features(
                conversation_id, agent_id, interaction_type, outcome,
                satisfaction_score, metadata or {}
            )

            if conversation_data:
                # Add to learning dataset
                self.conversation_data.append(conversation_data)

                # Store in Redis for persistence
                cache_key = f"conversation_learning:{conversation_id}"
                await self.redis_client.setex(
                    cache_key,
                    30 * 24 * 3600,  # 30 days
                    json.dumps({
                        "conversation_id": conversation_id,
                        "agent_id": agent_id,
                        "interaction_type": interaction_type.value,
                        "outcome": outcome.value,
                        "satisfaction_score": satisfaction_score,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": metadata
                    })
                )

                # Trigger learning if we have enough data
                if len(self.conversation_data) % 20 == 0:  # Every 20 new conversations
                    asyncio.create_task(self._update_learning_models())

                return True

        except Exception as e:
            logger.error(f"Error recording conversation outcome: {str(e)}")

        return False

    async def analyze_learning_patterns(self, request: LearningRequest) -> LearningResponse:
        """Analyze conversation patterns and learning opportunities."""
        try:
            start_time = time.time()

            # Filter conversations based on request criteria
            filtered_conversations = self._filter_conversations(request)

            if len(filtered_conversations) < self.min_data_points:
                return LearningResponse(
                    objective=request.objective,
                    analysis_period=f"Last {request.time_period_hours} hours",
                    total_conversations=len(filtered_conversations),
                    patterns_discovered=0,
                    optimization_rules=0,
                    effectiveness_score=0.0,
                    improvement_potential=0.0,
                    key_insights=["Insufficient data for meaningful analysis"],
                    recommended_actions=["Collect more conversation data"],
                    performance_metrics={},
                    confidence_level=0.0
                )

            # Discover patterns in the data
            patterns = await self._discover_patterns(filtered_conversations, request)

            # Generate optimization rules
            optimization_rules = await self._generate_optimization_rules(patterns, request)

            # Calculate effectiveness metrics
            effectiveness_metrics = await self._calculate_effectiveness_metrics(
                filtered_conversations, request.objective
            )

            # Generate insights and recommendations
            insights = await self._generate_insights(patterns, optimization_rules, effectiveness_metrics)
            recommendations = await self._generate_recommendations(optimization_rules, request)

            analysis_time = time.time() - start_time

            return LearningResponse(
                objective=request.objective,
                analysis_period=f"Last {request.time_period_hours} hours",
                total_conversations=len(filtered_conversations),
                patterns_discovered=len(patterns),
                optimization_rules=len(optimization_rules),
                effectiveness_score=effectiveness_metrics.get("overall_effectiveness", 0.0),
                improvement_potential=effectiveness_metrics.get("improvement_potential", 0.0),
                key_insights=insights,
                recommended_actions=recommendations,
                performance_metrics={
                    "analysis_time": analysis_time,
                    "data_quality_score": effectiveness_metrics.get("data_quality", 0.8),
                    "pattern_confidence": effectiveness_metrics.get("pattern_confidence", 0.7),
                    "prediction_accuracy": effectiveness_metrics.get("prediction_accuracy", 0.0)
                },
                confidence_level=effectiveness_metrics.get("confidence_level", 0.7)
            )

        except Exception as e:
            logger.error(f"Error analyzing learning patterns: {str(e)}")
            return self._create_error_learning_response(request, str(e))

    async def get_coaching_optimization(self, agent_id: str) -> CoachingOptimization:
        """Get personalized coaching optimization recommendations for an agent."""
        try:
            # Get agent profile and conversation history
            agent_profile = await self.agent_service.get_agent_profile(agent_id)
            if not agent_profile:
                raise ValueError(f"Agent profile not found: {agent_id}")

            # Get agent's conversation data
            agent_conversations = [
                conv for conv in self.conversation_data
                if conv.agent_id == agent_id
            ]

            if len(agent_conversations) < 10:
                return CoachingOptimization(
                    agent_id=agent_id,
                    optimization_type="insufficient_data",
                    current_effectiveness=0.0,
                    target_effectiveness=0.0,
                    recommended_changes=["Collect more interaction data for meaningful optimization"],
                    expected_improvement=0.0,
                    implementation_priority=0.0,
                    monitoring_metrics=["conversation_count", "satisfaction_scores"]
                )

            # Calculate current effectiveness
            current_effectiveness = self._calculate_agent_effectiveness(agent_conversations)

            # Identify optimization opportunities
            optimization_opportunities = await self._identify_optimization_opportunities(
                agent_profile, agent_conversations
            )

            # Generate recommendations
            recommended_changes = []
            expected_improvement = 0.0

            for opportunity in optimization_opportunities:
                recommended_changes.append(opportunity["recommendation"])
                expected_improvement += opportunity.get("expected_improvement", 0.0)

            # Calculate target effectiveness
            target_effectiveness = min(1.0, current_effectiveness + expected_improvement)

            # Determine implementation priority
            implementation_priority = self._calculate_implementation_priority(
                current_effectiveness, expected_improvement, agent_profile
            )

            return CoachingOptimization(
                agent_id=agent_id,
                optimization_type="personalized_coaching",
                current_effectiveness=current_effectiveness,
                target_effectiveness=target_effectiveness,
                recommended_changes=recommended_changes[:5],  # Top 5 recommendations
                expected_improvement=expected_improvement,
                implementation_priority=implementation_priority,
                monitoring_metrics=[
                    "satisfaction_score", "conversion_rate", "response_time",
                    "guidance_effectiveness", "client_retention"
                ]
            )

        except Exception as e:
            logger.error(f"Error getting coaching optimization: {str(e)}")
            return CoachingOptimization(
                agent_id=agent_id,
                optimization_type="error",
                current_effectiveness=0.0,
                target_effectiveness=0.0,
                recommended_changes=[f"Error analyzing agent data: {str(e)}"],
                expected_improvement=0.0,
                implementation_priority=0.0,
                monitoring_metrics=[]
            )

    async def apply_real_time_optimization(
        self, agent_id: str, interaction_type: InteractionType,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply real-time optimization based on learned patterns."""
        try:
            # Get applicable optimization rules
            applicable_rules = self._get_applicable_rules(agent_id, interaction_type, context)

            if not applicable_rules:
                return {"status": "no_optimization", "message": "No applicable optimization rules found"}

            optimizations = {}

            for rule in applicable_rules[:3]:  # Apply top 3 rules
                optimization = await self._apply_optimization_rule(rule, agent_id, context)
                if optimization:
                    optimizations[rule.rule_id] = optimization

                    # Update rule usage statistics
                    rule.last_applied = datetime.now()
                    rule.application_count += 1

            return {
                "status": "optimization_applied",
                "optimizations": optimizations,
                "rules_applied": len(optimizations),
                "expected_improvement": sum(
                    opt.get("expected_improvement", 0.0) for opt in optimizations.values()
                )
            }

        except Exception as e:
            logger.error(f"Error applying real-time optimization: {str(e)}")
            return {"status": "error", "message": str(e)}

    def _filter_conversations(self, request: LearningRequest) -> List[ConversationData]:
        """Filter conversations based on request criteria."""
        cutoff_time = datetime.now() - timedelta(hours=request.time_period_hours)

        filtered = [
            conv for conv in self.conversation_data
            if conv.start_time > cutoff_time
        ]

        if request.agent_id:
            filtered = [conv for conv in filtered if conv.agent_id == request.agent_id]

        if request.interaction_type:
            filtered = [conv for conv in filtered if conv.interaction_type == request.interaction_type]

        return filtered

    async def _discover_patterns(
        self, conversations: List[ConversationData], request: LearningRequest
    ) -> List[LearningPattern]:
        """Discover patterns in conversation data using ML clustering."""
        try:
            if len(conversations) < self.min_data_points:
                return []

            # Prepare feature matrix
            feature_matrix = self._prepare_feature_matrix(conversations)

            if self.pattern_clusterer is None:
                # Initialize clustering model
                self.pattern_clusterer = KMeans(
                    n_clusters=min(10, len(conversations) // 10),
                    random_state=42
                )

            # Perform clustering
            cluster_labels = self.pattern_clusterer.fit_predict(feature_matrix)

            patterns = []

            # Analyze each cluster to identify patterns
            for cluster_id in range(self.pattern_clusterer.n_clusters):
                cluster_conversations = [
                    conv for i, conv in enumerate(conversations)
                    if cluster_labels[i] == cluster_id
                ]

                if len(cluster_conversations) < 5:  # Skip small clusters
                    continue

                pattern = await self._analyze_cluster_pattern(cluster_conversations, cluster_id)
                if pattern and pattern.confidence_score >= request.min_confidence:
                    patterns.append(pattern)

            return patterns

        except Exception as e:
            logger.error(f"Error discovering patterns: {str(e)}")
            return []

    async def _analyze_cluster_pattern(
        self, conversations: List[ConversationData], cluster_id: int
    ) -> Optional[LearningPattern]:
        """Analyze a cluster of conversations to identify patterns."""
        try:
            if not conversations:
                return None

            # Calculate cluster characteristics
            outcomes = [conv.outcome for conv in conversations]
            satisfaction_scores = [
                conv.satisfaction_score for conv in conversations
                if conv.satisfaction_score is not None
            ]

            # Identify dominant patterns
            dominant_outcome = max(set(outcomes), key=outcomes.count)
            avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.0

            # Calculate effectiveness metrics
            effectiveness_metrics = {
                "outcome_consistency": outcomes.count(dominant_outcome) / len(outcomes),
                "avg_satisfaction": avg_satisfaction,
                "sample_size": len(conversations),
                "conversion_rate": sum(1 for conv in conversations if conv.conversion_achieved) / len(conversations)
            }

            # Determine pattern conditions
            feature_averages = {}
            for feature in LearningFeature:
                values = [
                    conv.features.get(feature, 0.0) for conv in conversations
                    if feature in conv.features
                ]
                if values:
                    feature_averages[feature.value] = sum(values) / len(values)

            # Generate recommendations based on pattern
            recommendations = self._generate_pattern_recommendations(
                dominant_outcome, effectiveness_metrics, feature_averages
            )

            confidence_score = min(
                effectiveness_metrics["outcome_consistency"],
                0.5 + (len(conversations) / 100),  # Size-based confidence boost
                0.8 if avg_satisfaction > 0.7 else 0.6
            )

            pattern = LearningPattern(
                pattern_id=f"cluster_{cluster_id}_{int(time.time())}",
                pattern_type="conversation_cluster",
                conditions=feature_averages,
                predicted_outcome=dominant_outcome,
                confidence_score=confidence_score,
                sample_size=len(conversations),
                effectiveness_metrics=effectiveness_metrics,
                recommendations=recommendations,
                created_at=datetime.now(),
                last_validated=datetime.now()
            )

            return pattern

        except Exception as e:
            logger.error(f"Error analyzing cluster pattern: {str(e)}")
            return None

    async def _generate_optimization_rules(
        self, patterns: List[LearningPattern], request: LearningRequest
    ) -> List[OptimizationRule]:
        """Generate optimization rules from discovered patterns."""
        rules = []

        try:
            for pattern in patterns:
                # Only create rules for positive patterns with high confidence
                if (pattern.predicted_outcome in [OutcomeType.POSITIVE, OutcomeType.EXCEPTIONAL]
                    and pattern.confidence_score >= self.pattern_confidence_threshold):

                    rule = OptimizationRule(
                        rule_id=f"rule_{pattern.pattern_id}",
                        rule_type="pattern_based",
                        trigger_conditions=pattern.conditions.copy(),
                        optimization_action=self._generate_optimization_action(pattern),
                        expected_improvement=self._calculate_expected_improvement(pattern),
                        priority_score=self._calculate_rule_priority(pattern),
                        success_rate=pattern.confidence_score,
                        created_at=datetime.now()
                    )

                    rules.append(rule)
                    self.optimization_rules[rule.rule_id] = rule

            return rules

        except Exception as e:
            logger.error(f"Error generating optimization rules: {str(e)}")
            return []

    def _generate_optimization_action(self, pattern: LearningPattern) -> str:
        """Generate optimization action based on pattern characteristics."""
        conditions = pattern.conditions
        effectiveness = pattern.effectiveness_metrics

        actions = []

        # Response time optimization
        if conditions.get("response_time", 0) > 500:
            actions.append("Optimize response time through caching and model selection")

        # Conversation length optimization
        if conditions.get("conversation_length", 0) > 20:
            actions.append("Provide more concise, focused guidance to reduce conversation length")
        elif conditions.get("conversation_length", 0) < 5:
            actions.append("Encourage deeper engagement through follow-up questions")

        # Guidance type optimization
        if effectiveness.get("avg_satisfaction", 0) > 0.8:
            actions.append(f"Replicate successful guidance pattern with {effectiveness['avg_satisfaction']:.1%} satisfaction")

        # Agent experience-based optimization
        if conditions.get("agent_experience", 0) < 2:
            actions.append("Provide more detailed, educational guidance for new agents")
        elif conditions.get("agent_experience", 0) > 10:
            actions.append("Focus on advanced strategies and market insights for experienced agents")

        return "; ".join(actions) if actions else "Monitor pattern for optimization opportunities"

    def _calculate_expected_improvement(self, pattern: LearningPattern) -> float:
        """Calculate expected improvement from applying pattern-based optimization."""
        base_improvement = 0.1  # Base 10% improvement

        # Boost based on pattern confidence
        confidence_boost = (pattern.confidence_score - 0.5) * 0.4

        # Boost based on satisfaction scores
        satisfaction_boost = max(0, pattern.effectiveness_metrics.get("avg_satisfaction", 0.5) - 0.5)

        # Boost based on sample size (larger samples = more reliable)
        sample_boost = min(0.2, pattern.sample_size / 500)

        return min(0.5, base_improvement + confidence_boost + satisfaction_boost + sample_boost)

    def _calculate_rule_priority(self, pattern: LearningPattern) -> float:
        """Calculate priority score for optimization rule."""
        priority = 0.5  # Base priority

        # High satisfaction patterns get higher priority
        if pattern.effectiveness_metrics.get("avg_satisfaction", 0) > 0.8:
            priority += 0.3

        # Large sample sizes get higher priority
        if pattern.sample_size > 100:
            priority += 0.2

        # High confidence patterns get higher priority
        priority += (pattern.confidence_score - 0.5) * 0.4

        return min(1.0, priority)

    async def _calculate_effectiveness_metrics(
        self, conversations: List[ConversationData], objective: LearningObjective
    ) -> Dict[str, float]:
        """Calculate effectiveness metrics based on learning objective."""
        if not conversations:
            return {"overall_effectiveness": 0.0}

        metrics = {}

        # Base metrics
        satisfaction_scores = [
            conv.satisfaction_score for conv in conversations
            if conv.satisfaction_score is not None
        ]

        if satisfaction_scores:
            metrics["avg_satisfaction"] = sum(satisfaction_scores) / len(satisfaction_scores)
        else:
            metrics["avg_satisfaction"] = 0.5

        # Outcome distribution
        outcomes = [conv.outcome for conv in conversations]
        positive_outcomes = [o for o in outcomes if o in [OutcomeType.POSITIVE, OutcomeType.EXCEPTIONAL]]
        metrics["positive_outcome_rate"] = len(positive_outcomes) / len(outcomes)

        # Conversion metrics
        conversions = [conv.conversion_achieved for conv in conversations if conv.conversion_achieved is not None]
        if conversions:
            metrics["conversion_rate"] = sum(conversions) / len(conversions)
        else:
            metrics["conversion_rate"] = 0.0

        # Objective-specific metrics
        if objective == LearningObjective.COACHING_EFFECTIVENESS:
            metrics["overall_effectiveness"] = (
                metrics["avg_satisfaction"] * 0.4 +
                metrics["positive_outcome_rate"] * 0.4 +
                metrics["conversion_rate"] * 0.2
            )
        elif objective == LearningObjective.RESPONSE_RELEVANCE:
            # Response relevance based on conversation efficiency
            avg_length = sum(conv.messages_count for conv in conversations) / len(conversations)
            relevance_score = max(0, 1 - (avg_length - 10) / 20)  # Optimal ~10 messages
            metrics["overall_effectiveness"] = relevance_score
        else:
            # Default effectiveness calculation
            metrics["overall_effectiveness"] = (
                metrics["avg_satisfaction"] * 0.5 +
                metrics["positive_outcome_rate"] * 0.5
            )

        # Calculate improvement potential
        current_effectiveness = metrics["overall_effectiveness"]
        theoretical_max = 0.95  # Leave room for variability
        metrics["improvement_potential"] = max(0, theoretical_max - current_effectiveness)

        # Data quality indicators
        metrics["data_quality"] = min(1.0, len(conversations) / 100)
        metrics["pattern_confidence"] = self.pattern_confidence_threshold

        # Model prediction accuracy (if models are trained)
        if self.outcome_classifier is not None:
            try:
                features = self._prepare_feature_matrix(conversations)
                predictions = self.outcome_classifier.predict(features)
                actual = [conv.outcome.value for conv in conversations]
                metrics["prediction_accuracy"] = accuracy_score(actual, predictions)
            except Exception:
                metrics["prediction_accuracy"] = 0.0

        # Overall confidence
        metrics["confidence_level"] = min(
            metrics["data_quality"],
            metrics.get("prediction_accuracy", 0.7),
            0.5 + (len(conversations) / 200)
        )

        return metrics

    async def _generate_insights(
        self, patterns: List[LearningPattern], rules: List[OptimizationRule],
        effectiveness_metrics: Dict[str, float]
    ) -> List[str]:
        """Generate key insights from learning analysis."""
        insights = []

        # Effectiveness insights
        overall_effectiveness = effectiveness_metrics.get("overall_effectiveness", 0.0)
        if overall_effectiveness > 0.8:
            insights.append(f"Claude coaching is highly effective with {overall_effectiveness:.1%} overall success rate")
        elif overall_effectiveness > 0.6:
            insights.append(f"Claude coaching shows good effectiveness at {overall_effectiveness:.1%} with room for improvement")
        else:
            insights.append(f"Claude coaching effectiveness at {overall_effectiveness:.1%} indicates significant optimization opportunities")

        # Pattern insights
        if patterns:
            high_confidence_patterns = [p for p in patterns if p.confidence_score > 0.8]
            if high_confidence_patterns:
                insights.append(f"Identified {len(high_confidence_patterns)} high-confidence success patterns")

            # Best performing pattern
            best_pattern = max(patterns, key=lambda p: p.effectiveness_metrics.get("avg_satisfaction", 0))
            if best_pattern.effectiveness_metrics.get("avg_satisfaction", 0) > 0.8:
                insights.append(f"Top performing pattern achieves {best_pattern.effectiveness_metrics['avg_satisfaction']:.1%} satisfaction")

        # Optimization insights
        if rules:
            high_impact_rules = [r for r in rules if r.expected_improvement > 0.2]
            if high_impact_rules:
                insights.append(f"Found {len(high_impact_rules)} high-impact optimization opportunities")

            total_potential = sum(rule.expected_improvement for rule in rules)
            if total_potential > 0.5:
                insights.append(f"Combined optimizations could improve effectiveness by {total_potential:.1%}")

        # Conversion insights
        conversion_rate = effectiveness_metrics.get("conversion_rate", 0.0)
        if conversion_rate > 0.0:
            insights.append(f"Current conversion rate: {conversion_rate:.1%}")

        return insights[:5]  # Return top 5 insights

    async def _generate_recommendations(
        self, rules: List[OptimizationRule], request: LearningRequest
    ) -> List[str]:
        """Generate actionable recommendations from optimization rules."""
        recommendations = []

        if not rules:
            recommendations.append("Collect more conversation data to identify optimization patterns")
            recommendations.append("Focus on improving satisfaction scores through better response relevance")
            return recommendations

        # Sort rules by priority and expected improvement
        sorted_rules = sorted(
            rules,
            key=lambda r: (r.priority_score + r.expected_improvement),
            reverse=True
        )

        for rule in sorted_rules[:3]:  # Top 3 rules
            recommendation = f"Apply optimization: {rule.optimization_action} (Expected improvement: {rule.expected_improvement:.1%})"
            recommendations.append(recommendation)

        # General recommendations based on analysis
        if request.objective == LearningObjective.COACHING_EFFECTIVENESS:
            recommendations.append("Focus on personalization based on agent experience and specialization")
        elif request.objective == LearningObjective.RESPONSE_RELEVANCE:
            recommendations.append("Optimize response conciseness and relevance to conversation context")

        recommendations.append("Monitor satisfaction scores and outcome metrics to validate improvements")

        return recommendations[:5]

    def _prepare_feature_matrix(self, conversations: List[ConversationData]) -> np.ndarray:
        """Prepare feature matrix for machine learning models."""
        features = []

        for conv in conversations:
            feature_vector = []

            # Temporal features
            feature_vector.append(conv.start_time.hour)  # Hour of day
            feature_vector.append(conv.start_time.weekday())  # Day of week
            feature_vector.append((conv.end_time - conv.start_time).total_seconds() / 60)  # Duration in minutes

            # Conversation features
            feature_vector.append(conv.messages_count)
            feature_vector.append(conv.claude_responses_count)
            feature_vector.append(len(conv.guidance_types))

            # Extracted features
            for feature_type in LearningFeature:
                feature_vector.append(conv.features.get(feature_type, 0.0))

            # Outcome encoding
            outcome_encoding = {
                OutcomeType.NEGATIVE: 0,
                OutcomeType.NEUTRAL: 1,
                OutcomeType.POSITIVE: 2,
                OutcomeType.EXCEPTIONAL: 3,
                OutcomeType.UNKNOWN: 1
            }
            feature_vector.append(outcome_encoding.get(conv.outcome, 1))

            # Satisfaction score
            feature_vector.append(conv.satisfaction_score or 0.5)

            features.append(feature_vector)

        return np.array(features)

    async def _extract_conversation_features(
        self, conversation_id: str, agent_id: str, interaction_type: InteractionType,
        outcome: OutcomeType, satisfaction_score: Optional[float],
        metadata: Dict[str, Any]
    ) -> Optional[ConversationData]:
        """Extract features from conversation for learning analysis."""
        try:
            # Get conversation data from cache/database
            # This is a simplified implementation - in practice, you would
            # retrieve actual conversation data from your storage system

            current_time = datetime.now()

            # Mock conversation data - replace with actual data retrieval
            conversation_data = ConversationData(
                conversation_id=conversation_id,
                agent_id=agent_id,
                interaction_type=interaction_type,
                guidance_types=[GuidanceType.RESPONSE_SUGGESTIONS, GuidanceType.STRATEGY_COACHING],
                start_time=current_time - timedelta(minutes=metadata.get("duration_minutes", 15)),
                end_time=current_time,
                messages_count=metadata.get("messages_count", 10),
                claude_responses_count=metadata.get("claude_responses", 5),
                outcome=outcome,
                satisfaction_score=satisfaction_score,
                conversion_achieved=metadata.get("conversion_achieved"),
                follow_up_required=metadata.get("follow_up_required", False),
                agent_feedback=metadata.get("agent_feedback"),
                context_metadata=metadata
            )

            # Extract learning features
            conversation_data.features = {
                LearningFeature.CONVERSATION_LENGTH: float(conversation_data.messages_count),
                LearningFeature.RESPONSE_TIME: metadata.get("avg_response_time", 500.0),
                LearningFeature.GUIDANCE_TYPE_MIX: float(len(conversation_data.guidance_types)),
                LearningFeature.TIME_OF_DAY: float(conversation_data.start_time.hour),
                LearningFeature.DAY_OF_WEEK: float(conversation_data.start_time.weekday()),
                LearningFeature.INTERACTION_FREQUENCY: metadata.get("recent_interactions", 1.0)
            }

            # Get agent-specific features
            agent_profile = await self.agent_service.get_agent_profile(agent_id)
            if agent_profile:
                conversation_data.features[LearningFeature.AGENT_EXPERIENCE] = float(agent_profile.years_experience)

            return conversation_data

        except Exception as e:
            logger.error(f"Error extracting conversation features: {str(e)}")
            return None

    def _calculate_agent_effectiveness(self, conversations: List[ConversationData]) -> float:
        """Calculate overall effectiveness score for an agent."""
        if not conversations:
            return 0.0

        # Weight different outcome types
        outcome_weights = {
            OutcomeType.EXCEPTIONAL: 1.0,
            OutcomeType.POSITIVE: 0.8,
            OutcomeType.NEUTRAL: 0.5,
            OutcomeType.NEGATIVE: 0.2,
            OutcomeType.UNKNOWN: 0.4
        }

        # Calculate weighted outcome score
        outcome_score = sum(outcome_weights.get(conv.outcome, 0.4) for conv in conversations) / len(conversations)

        # Calculate satisfaction score
        satisfaction_scores = [conv.satisfaction_score for conv in conversations if conv.satisfaction_score is not None]
        satisfaction_score = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.5

        # Calculate conversion rate
        conversions = [conv.conversion_achieved for conv in conversations if conv.conversion_achieved is not None]
        conversion_score = sum(conversions) / len(conversions) if conversions else 0.0

        # Weighted combination
        effectiveness = (outcome_score * 0.4 + satisfaction_score * 0.4 + conversion_score * 0.2)

        return min(1.0, effectiveness)

    async def _identify_optimization_opportunities(
        self, agent_profile: AgentProfile, conversations: List[ConversationData]
    ) -> List[Dict[str, Any]]:
        """Identify specific optimization opportunities for an agent."""
        opportunities = []

        # Analyze response times
        response_times = [conv.features.get(LearningFeature.RESPONSE_TIME, 500) for conv in conversations]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 500

        if avg_response_time > 600:
            opportunities.append({
                "type": "response_time",
                "recommendation": "Optimize response time through intelligent caching and model selection",
                "expected_improvement": 0.15,
                "current_value": avg_response_time,
                "target_value": 400
            })

        # Analyze conversation patterns
        avg_length = sum(conv.messages_count for conv in conversations) / len(conversations)

        if avg_length > 15:
            opportunities.append({
                "type": "conversation_efficiency",
                "recommendation": "Provide more concise, actionable guidance to reduce conversation length",
                "expected_improvement": 0.12,
                "current_value": avg_length,
                "target_value": 10
            })

        # Analyze satisfaction patterns
        satisfaction_scores = [conv.satisfaction_score for conv in conversations if conv.satisfaction_score is not None]
        avg_satisfaction = sum(satisfaction_scores) / len(satisfaction_scores) if satisfaction_scores else 0.5

        if avg_satisfaction < 0.7:
            opportunities.append({
                "type": "satisfaction_improvement",
                "recommendation": "Enhance guidance relevance and personalization for higher satisfaction",
                "expected_improvement": 0.2,
                "current_value": avg_satisfaction,
                "target_value": 0.8
            })

        # Experience-based recommendations
        if agent_profile.years_experience < 2:
            opportunities.append({
                "type": "new_agent_support",
                "recommendation": "Provide more educational content and step-by-step guidance",
                "expected_improvement": 0.18,
                "current_value": agent_profile.years_experience,
                "target_value": "educational_focus"
            })

        return opportunities[:5]  # Return top 5 opportunities

    def _calculate_implementation_priority(
        self, current_effectiveness: float, expected_improvement: float,
        agent_profile: AgentProfile
    ) -> float:
        """Calculate implementation priority for optimization recommendations."""
        base_priority = 0.5

        # Higher priority for lower current effectiveness
        if current_effectiveness < 0.5:
            base_priority += 0.3
        elif current_effectiveness < 0.7:
            base_priority += 0.2

        # Higher priority for larger expected improvements
        base_priority += min(0.3, expected_improvement)

        # Higher priority for new agents (more impact potential)
        if agent_profile.years_experience < 3:
            base_priority += 0.1

        return min(1.0, base_priority)

    def _get_applicable_rules(
        self, agent_id: str, interaction_type: InteractionType, context: Dict[str, Any]
    ) -> List[OptimizationRule]:
        """Get optimization rules applicable to current context."""
        applicable_rules = []

        for rule in self.optimization_rules.values():
            # Check if rule conditions match current context
            if self._rule_matches_context(rule, agent_id, interaction_type, context):
                applicable_rules.append(rule)

        # Sort by priority and expected improvement
        applicable_rules.sort(
            key=lambda r: (r.priority_score + r.expected_improvement),
            reverse=True
        )

        return applicable_rules

    def _rule_matches_context(
        self, rule: OptimizationRule, agent_id: str,
        interaction_type: InteractionType, context: Dict[str, Any]
    ) -> bool:
        """Check if optimization rule matches current context."""
        # Simplified matching logic - in practice, this would be more sophisticated
        # involving feature similarity, agent characteristics, etc.

        # For now, assume rules are generally applicable
        # but could be filtered based on specific conditions
        return True

    async def _apply_optimization_rule(
        self, rule: OptimizationRule, agent_id: str, context: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Apply an optimization rule and return the optimization result."""
        try:
            optimization = {
                "rule_id": rule.rule_id,
                "optimization_type": rule.rule_type,
                "action": rule.optimization_action,
                "expected_improvement": rule.expected_improvement,
                "priority": rule.priority_score,
                "applied_at": datetime.now().isoformat(),
                "context": context
            }

            return optimization

        except Exception as e:
            logger.error(f"Error applying optimization rule {rule.rule_id}: {str(e)}")
            return None

    def _generate_pattern_recommendations(
        self, outcome: OutcomeType, effectiveness_metrics: Dict[str, float],
        feature_averages: Dict[str, float]
    ) -> List[str]:
        """Generate recommendations based on identified patterns."""
        recommendations = []

        if outcome in [OutcomeType.POSITIVE, OutcomeType.EXCEPTIONAL]:
            if effectiveness_metrics.get("avg_satisfaction", 0) > 0.8:
                recommendations.append("Replicate this successful interaction pattern")

            response_time = feature_averages.get("response_time", 500)
            if response_time < 300:
                recommendations.append("Maintain fast response times for optimal satisfaction")

            conversation_length = feature_averages.get("conversation_length", 10)
            if conversation_length < 8:
                recommendations.append("Continue providing concise, focused guidance")

        else:  # Negative or neutral outcomes
            recommendations.append("Analyze failure points to avoid similar patterns")

            if feature_averages.get("response_time", 500) > 600:
                recommendations.append("Improve response time to enhance user experience")

        return recommendations

    async def _update_learning_models(self) -> None:
        """Update machine learning models with new conversation data."""
        try:
            if len(self.conversation_data) < self.min_data_points:
                return

            # Prepare training data
            feature_matrix = self._prepare_feature_matrix(self.conversation_data)

            # Scale features
            if self.feature_scaler is None:
                self.feature_scaler = StandardScaler()

            scaled_features = self.feature_scaler.fit_transform(feature_matrix)

            # Train outcome classifier
            outcomes = [conv.outcome.value for conv in self.conversation_data]
            if len(set(outcomes)) > 1:  # Need multiple classes
                if self.outcome_classifier is None:
                    self.outcome_classifier = RandomForestClassifier(
                        n_estimators=100, random_state=42
                    )

                X_train, X_test, y_train, y_test = train_test_split(
                    scaled_features, outcomes, test_size=0.2, random_state=42
                )

                self.outcome_classifier.fit(X_train, y_train)

                # Evaluate model
                y_pred = self.outcome_classifier.predict(X_test)
                accuracy = accuracy_score(y_test, y_pred)

                self.model_performance["outcome_classifier"] = {
                    "accuracy": accuracy,
                    "last_updated": datetime.now().isoformat(),
                    "training_samples": len(X_train)
                }

            # Train satisfaction predictor
            satisfaction_data = [
                (conv, conv.satisfaction_score) for conv in self.conversation_data
                if conv.satisfaction_score is not None
            ]

            if len(satisfaction_data) >= self.min_data_points:
                satisfaction_features = self._prepare_feature_matrix([conv for conv, _ in satisfaction_data])
                satisfaction_scores = [score for _, score in satisfaction_data]

                if self.satisfaction_predictor is None:
                    self.satisfaction_predictor = GradientBoostingRegressor(
                        n_estimators=100, random_state=42
                    )

                scaled_satisfaction_features = self.feature_scaler.transform(satisfaction_features)

                X_train, X_test, y_train, y_test = train_test_split(
                    scaled_satisfaction_features, satisfaction_scores,
                    test_size=0.2, random_state=42
                )

                self.satisfaction_predictor.fit(X_train, y_train)

                # Evaluate model
                y_pred = self.satisfaction_predictor.predict(X_test)
                mse = mean_squared_error(y_test, y_pred)

                self.model_performance["satisfaction_predictor"] = {
                    "mse": mse,
                    "rmse": np.sqrt(mse),
                    "last_updated": datetime.now().isoformat(),
                    "training_samples": len(X_train)
                }

            # Save models
            await self._save_trained_models()

            self.last_training_time = datetime.now()

            logger.info(f"Updated learning models with {len(self.conversation_data)} conversations")

        except Exception as e:
            logger.error(f"Error updating learning models: {str(e)}")

    def _initialize_feature_extraction(self) -> None:
        """Initialize feature extraction components."""
        # Feature extraction is already implemented in _extract_conversation_features
        # This method can be used for additional initialization if needed
        pass

    async def _load_historical_data(self) -> None:
        """Load historical conversation data from Redis."""
        try:
            # Get all conversation learning keys
            keys = await self.redis_client.keys("conversation_learning:*")

            for key in keys[:self.max_stored_conversations]:  # Limit to prevent memory issues
                try:
                    data = await self.redis_client.get(key)
                    if data:
                        conversation_info = json.loads(data)

                        # Convert to ConversationData object
                        conversation_data = await self._extract_conversation_features(
                            conversation_info["conversation_id"],
                            conversation_info["agent_id"],
                            InteractionType(conversation_info["interaction_type"]),
                            OutcomeType(conversation_info["outcome"]),
                            conversation_info.get("satisfaction_score"),
                            conversation_info.get("metadata", {})
                        )

                        if conversation_data:
                            self.conversation_data.append(conversation_data)

                except Exception as e:
                    logger.error(f"Error loading conversation data from {key}: {str(e)}")
                    continue

            logger.info(f"Loaded {len(self.conversation_data)} historical conversations")

        except Exception as e:
            logger.error(f"Error loading historical data: {str(e)}")

    async def _load_trained_models(self) -> None:
        """Load pre-trained ML models from storage."""
        try:
            model_files = {
                "outcome_classifier": self.model_storage_path / "outcome_classifier.pkl",
                "satisfaction_predictor": self.model_storage_path / "satisfaction_predictor.pkl",
                "feature_scaler": self.model_storage_path / "feature_scaler.pkl",
                "pattern_clusterer": self.model_storage_path / "pattern_clusterer.pkl"
            }

            for model_name, model_path in model_files.items():
                if model_path.exists():
                    try:
                        with open(model_path, 'rb') as f:
                            model = pickle.load(f)
                            setattr(self, model_name, model)
                        logger.info(f"Loaded {model_name} from {model_path}")
                    except Exception as e:
                        logger.warning(f"Failed to load {model_name}: {str(e)}")

        except Exception as e:
            logger.error(f"Error loading trained models: {str(e)}")

    async def _save_trained_models(self) -> None:
        """Save trained ML models to storage."""
        try:
            models_to_save = {
                "outcome_classifier": self.outcome_classifier,
                "satisfaction_predictor": self.satisfaction_predictor,
                "feature_scaler": self.feature_scaler,
                "pattern_clusterer": self.pattern_clusterer
            }

            for model_name, model in models_to_save.items():
                if model is not None:
                    model_path = self.model_storage_path / f"{model_name}.pkl"
                    try:
                        with open(model_path, 'wb') as f:
                            pickle.dump(model, f)
                        logger.info(f"Saved {model_name} to {model_path}")
                    except Exception as e:
                        logger.error(f"Failed to save {model_name}: {str(e)}")

        except Exception as e:
            logger.error(f"Error saving trained models: {str(e)}")

    def _create_error_learning_response(
        self, request: LearningRequest, error_message: str
    ) -> LearningResponse:
        """Create error response for failed learning analysis."""
        return LearningResponse(
            objective=request.objective,
            analysis_period=f"Last {request.time_period_hours} hours",
            total_conversations=0,
            patterns_discovered=0,
            optimization_rules=0,
            effectiveness_score=0.0,
            improvement_potential=0.0,
            key_insights=[f"Analysis failed: {error_message}"],
            recommended_actions=["Review error and retry analysis"],
            performance_metrics={"error": True},
            confidence_level=0.0
        )

    async def get_learning_status(self) -> Dict[str, Any]:
        """Get current status of the learning system."""
        try:
            return {
                "total_conversations": len(self.conversation_data),
                "discovered_patterns": len(self.discovered_patterns),
                "optimization_rules": len(self.optimization_rules),
                "models_trained": {
                    "outcome_classifier": self.outcome_classifier is not None,
                    "satisfaction_predictor": self.satisfaction_predictor is not None,
                    "pattern_clusterer": self.pattern_clusterer is not None,
                    "feature_scaler": self.feature_scaler is not None
                },
                "model_performance": self.model_performance,
                "last_training_time": self.last_training_time.isoformat() if self.last_training_time else None,
                "learning_history_count": len(self.learning_history),
                "system_health": {
                    "memory_usage_conversations": len(self.conversation_data),
                    "redis_connected": True,  # Simplified check
                    "storage_path_exists": self.model_storage_path.exists()
                }
            }

        except Exception as e:
            logger.error(f"Error getting learning status: {str(e)}")
            return {"error": str(e)}