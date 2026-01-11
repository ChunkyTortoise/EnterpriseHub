"""
Claude Coaching Analytics and A/B Testing Engine

Advanced analytics system for tracking coaching effectiveness, running A/B tests
on coaching strategies, and optimizing Claude's real-time guidance performance.

Features:
- A/B testing framework for coaching strategies
- Real-time coaching effectiveness measurement
- Performance attribution analysis
- Predictive coaching optimization
- Business impact quantification
"""

import asyncio
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from scipy import stats
import hashlib

from anthropic import AsyncAnthropic

from ..ghl_utils.config import settings
from .redis_conversation_service import redis_conversation_service
from .websocket_manager import get_websocket_manager, IntelligenceEventType

logger = logging.getLogger(__name__)


class CoachingStrategy(Enum):
    """Types of coaching strategies for A/B testing."""
    EMPATHETIC = "empathetic"  # Focus on emotional connection
    ANALYTICAL = "analytical"  # Focus on data and logic
    ASSERTIVE = "assertive"    # Focus on urgency and action
    CONSULTATIVE = "consultative"  # Focus on questions and discovery
    RELATIONSHIP = "relationship"  # Focus on rapport building


class ExperimentStatus(Enum):
    """A/B test experiment statuses."""
    PLANNING = "planning"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MetricType(Enum):
    """Types of coaching metrics."""
    CONVERSION_RATE = "conversion_rate"
    ENGAGEMENT_SCORE = "engagement_score"
    APPOINTMENT_RATE = "appointment_rate"
    OBJECTION_RESOLUTION = "objection_resolution"
    COACHING_SATISFACTION = "coaching_satisfaction"
    RESPONSE_TIME = "response_time"
    CONVERSATION_LENGTH = "conversation_length"


@dataclass
class CoachingExperiment:
    """A/B testing experiment configuration."""
    experiment_id: str
    name: str
    description: str
    strategies: List[CoachingStrategy]
    target_metric: MetricType
    start_date: datetime
    end_date: Optional[datetime]
    status: ExperimentStatus
    traffic_split: Dict[str, float]  # strategy -> percentage
    minimum_sample_size: int
    confidence_level: float
    created_by: str
    metadata: Dict[str, Any]


@dataclass
class CoachingMetrics:
    """Coaching performance metrics."""
    agent_id: str
    session_id: str
    strategy_used: CoachingStrategy
    conversation_outcome: str  # "converted", "continued", "lost"
    coaching_count: int
    avg_response_time_ms: float
    conversation_duration_min: float
    objections_handled: int
    objections_resolved: int
    engagement_score: float
    lead_advancement: bool  # Did lead advance in qualification/stage?
    appointment_scheduled: bool
    timestamp: datetime
    experiment_id: Optional[str] = None


@dataclass
class ExperimentResults:
    """A/B test experiment results."""
    experiment_id: str
    strategy_results: Dict[str, Dict[str, float]]
    winner: Optional[CoachingStrategy]
    statistical_significance: bool
    confidence_interval: Tuple[float, float]
    p_value: float
    effect_size: float
    business_impact_estimate: Dict[str, float]
    recommendations: List[str]


@dataclass
class CoachingInsight:
    """Coaching performance insight."""
    insight_type: str
    title: str
    description: str
    impact_level: str  # "high", "medium", "low"
    recommended_action: str
    supporting_data: Dict[str, Any]
    confidence_score: float


class ClaudeCoachingAnalytics:
    """
    Advanced coaching analytics and experimentation engine.

    Provides A/B testing framework for coaching strategies, performance tracking,
    and business impact measurement for Claude coaching effectiveness.
    """

    def __init__(self):
        self.claude_client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.redis_service = redis_conversation_service
        self.websocket_manager = get_websocket_manager()

        # Active experiments tracking
        self.active_experiments: Dict[str, CoachingExperiment] = {}

        # Strategy templates for A/B testing
        self.strategy_templates = self._initialize_strategy_templates()

        # Performance baseline data
        self.baseline_metrics = {}

        # Initialize system
        asyncio.create_task(self._load_active_experiments())

    def _initialize_strategy_templates(self) -> Dict[CoachingStrategy, Dict[str, Any]]:
        """Initialize coaching strategy templates for A/B testing."""
        return {
            CoachingStrategy.EMPATHETIC: {
                "prompt_style": "Focus on understanding their emotions and concerns. Use empathetic language.",
                "question_style": "How are you feeling about this process?",
                "objection_approach": "Acknowledge feelings, then provide reassurance",
                "urgency_level": "low",
                "tone": "warm and understanding"
            },
            CoachingStrategy.ANALYTICAL: {
                "prompt_style": "Provide data-driven insights and logical reasoning.",
                "question_style": "What specific criteria are most important for your decision?",
                "objection_approach": "Present facts and comparative data",
                "urgency_level": "medium",
                "tone": "professional and factual"
            },
            CoachingStrategy.ASSERTIVE: {
                "prompt_style": "Create urgency and encourage decisive action.",
                "question_style": "What's preventing you from moving forward today?",
                "objection_approach": "Address concerns quickly, create action timeline",
                "urgency_level": "high",
                "tone": "confident and action-oriented"
            },
            CoachingStrategy.CONSULTATIVE: {
                "prompt_style": "Ask probing questions to understand deeper needs.",
                "question_style": "Help me understand what success looks like for you.",
                "objection_approach": "Use questions to help them work through concerns",
                "urgency_level": "medium",
                "tone": "curious and helpful"
            },
            CoachingStrategy.RELATIONSHIP: {
                "prompt_style": "Focus on building long-term trust and connection.",
                "question_style": "Tell me more about your family and what matters most.",
                "objection_approach": "Build trust first, then address concerns",
                "urgency_level": "low",
                "tone": "personal and relationship-focused"
            }
        }

    async def _load_active_experiments(self):
        """Load active experiments from storage."""
        try:
            # In a real implementation, this would load from database
            # For now, we'll initialize some sample experiments
            sample_experiment = CoachingExperiment(
                experiment_id="exp_001",
                name="Empathetic vs Analytical Coaching",
                description="Testing whether empathetic or analytical coaching works better for high-intent leads",
                strategies=[CoachingStrategy.EMPATHETIC, CoachingStrategy.ANALYTICAL],
                target_metric=MetricType.CONVERSION_RATE,
                start_date=datetime.now() - timedelta(days=7),
                end_date=datetime.now() + timedelta(days=14),
                status=ExperimentStatus.ACTIVE,
                traffic_split={
                    CoachingStrategy.EMPATHETIC.value: 0.5,
                    CoachingStrategy.ANALYTICAL.value: 0.5
                },
                minimum_sample_size=100,
                confidence_level=0.95,
                created_by="system",
                metadata={"lead_type": "high_intent"}
            )

            self.active_experiments[sample_experiment.experiment_id] = sample_experiment
            logger.info(f"Loaded {len(self.active_experiments)} active experiments")

        except Exception as e:
            logger.error(f"Error loading active experiments: {e}")

    async def create_experiment(
        self,
        name: str,
        description: str,
        strategies: List[CoachingStrategy],
        target_metric: MetricType,
        duration_days: int,
        traffic_split: Dict[str, float],
        minimum_sample_size: int = 100,
        confidence_level: float = 0.95,
        created_by: str = "system"
    ) -> CoachingExperiment:
        """Create new A/B testing experiment for coaching strategies."""
        try:
            experiment_id = f"exp_{uuid.uuid4().hex[:8]}"

            experiment = CoachingExperiment(
                experiment_id=experiment_id,
                name=name,
                description=description,
                strategies=strategies,
                target_metric=target_metric,
                start_date=datetime.now(),
                end_date=datetime.now() + timedelta(days=duration_days),
                status=ExperimentStatus.ACTIVE,
                traffic_split=traffic_split,
                minimum_sample_size=minimum_sample_size,
                confidence_level=confidence_level,
                created_by=created_by,
                metadata={}
            )

            self.active_experiments[experiment_id] = experiment

            # Store experiment configuration
            await self._store_experiment(experiment)

            # Broadcast experiment start
            await self._broadcast_experiment_event("experiment_started", experiment)

            logger.info(f"Created coaching experiment: {experiment_id}")
            return experiment

        except Exception as e:
            logger.error(f"Error creating experiment: {e}")
            raise

    async def assign_coaching_strategy(
        self,
        agent_id: str,
        lead_context: Dict[str, Any],
        session_id: str
    ) -> Tuple[CoachingStrategy, Optional[str]]:
        """
        Assign coaching strategy based on active experiments and lead context.

        Returns:
            Tuple of (strategy, experiment_id)
        """
        try:
            # Check if lead qualifies for any active experiments
            for experiment in self.active_experiments.values():
                if experiment.status == ExperimentStatus.ACTIVE and \
                   datetime.now() <= experiment.end_date:

                    # Check if lead matches experiment criteria
                    if await self._qualifies_for_experiment(lead_context, experiment):
                        # Assign strategy based on traffic split
                        strategy = self._assign_strategy_from_split(
                            agent_id, session_id, experiment.traffic_split, experiment.strategies
                        )
                        return strategy, experiment.experiment_id

            # Default strategy assignment (no active experiment)
            default_strategy = await self._determine_default_strategy(lead_context)
            return default_strategy, None

        except Exception as e:
            logger.error(f"Error assigning coaching strategy: {e}")
            return CoachingStrategy.CONSULTATIVE, None  # Safe default

    async def _qualifies_for_experiment(self, lead_context: Dict[str, Any], experiment: CoachingExperiment) -> bool:
        """Check if lead qualifies for the experiment."""
        # Implement qualification logic based on experiment metadata
        # For example, check lead stage, score, source, etc.

        # Simple example: high-intent leads only
        if experiment.metadata.get("lead_type") == "high_intent":
            lead_score = lead_context.get("lead_score", 0)
            return lead_score >= 70

        return True  # Default: all leads qualify

    def _assign_strategy_from_split(
        self,
        agent_id: str,
        session_id: str,
        traffic_split: Dict[str, float],
        strategies: List[CoachingStrategy]
    ) -> CoachingStrategy:
        """Assign strategy based on traffic split using consistent hashing."""
        # Use consistent hashing for stable assignments
        hash_input = f"{agent_id}_{session_id}".encode()
        hash_value = int(hashlib.md5(hash_input).hexdigest(), 16) % 100 / 100.0

        cumulative_prob = 0.0
        for strategy in strategies:
            strategy_weight = traffic_split.get(strategy.value, 0.0)
            cumulative_prob += strategy_weight

            if hash_value <= cumulative_prob:
                return strategy

        return strategies[0]  # Fallback to first strategy

    async def _determine_default_strategy(self, lead_context: Dict[str, Any]) -> CoachingStrategy:
        """Determine default coaching strategy based on lead context."""
        lead_score = lead_context.get("lead_score", 50)
        engagement_level = lead_context.get("engagement_score", 0.5)

        # High-scoring engaged leads get assertive approach
        if lead_score >= 80 and engagement_level >= 0.7:
            return CoachingStrategy.ASSERTIVE

        # Well-qualified leads get analytical approach
        elif lead_score >= 60:
            return CoachingStrategy.ANALYTICAL

        # New or low-engaged leads get relationship building
        elif engagement_level < 0.4:
            return CoachingStrategy.RELATIONSHIP

        # Default to consultative
        return CoachingStrategy.CONSULTATIVE

    async def generate_strategy_prompt(
        self,
        base_coaching_prompt: str,
        strategy: CoachingStrategy,
        lead_context: Dict[str, Any]
    ) -> str:
        """Generate strategy-specific coaching prompt for Claude."""
        try:
            strategy_config = self.strategy_templates.get(strategy, {})

            enhanced_prompt = f"""{base_coaching_prompt}

            COACHING STRATEGY: {strategy.value.upper()}

            Strategy Guidelines:
            - Style: {strategy_config.get('prompt_style', 'Standard coaching approach')}
            - Question Approach: {strategy_config.get('question_style', 'Ask relevant questions')}
            - Objection Handling: {strategy_config.get('objection_approach', 'Address concerns directly')}
            - Urgency Level: {strategy_config.get('urgency_level', 'medium')}
            - Tone: {strategy_config.get('tone', 'professional')}

            Lead Context: {json.dumps(lead_context, indent=2)}

            Apply this coaching strategy consistently while maintaining professionalism and effectiveness.
            """

            return enhanced_prompt

        except Exception as e:
            logger.error(f"Error generating strategy prompt: {e}")
            return base_coaching_prompt  # Fallback to original

    async def record_coaching_metrics(
        self,
        agent_id: str,
        session_id: str,
        strategy_used: CoachingStrategy,
        metrics_data: Dict[str, Any],
        experiment_id: Optional[str] = None
    ):
        """Record coaching session metrics for analysis."""
        try:
            metrics = CoachingMetrics(
                agent_id=agent_id,
                session_id=session_id,
                strategy_used=strategy_used,
                conversation_outcome=metrics_data.get("outcome", "unknown"),
                coaching_count=metrics_data.get("coaching_count", 0),
                avg_response_time_ms=metrics_data.get("avg_response_time", 0.0),
                conversation_duration_min=metrics_data.get("duration_minutes", 0.0),
                objections_handled=metrics_data.get("objections_handled", 0),
                objections_resolved=metrics_data.get("objections_resolved", 0),
                engagement_score=metrics_data.get("engagement_score", 0.0),
                lead_advancement=metrics_data.get("lead_advancement", False),
                appointment_scheduled=metrics_data.get("appointment_scheduled", False),
                timestamp=datetime.now(),
                experiment_id=experiment_id
            )

            # Store metrics
            await self._store_metrics(metrics)

            # Update real-time analytics
            await self._update_realtime_analytics(metrics)

            # Check experiment progress if applicable
            if experiment_id and experiment_id in self.active_experiments:
                await self._check_experiment_progress(experiment_id)

            logger.info(f"Recorded coaching metrics for session {session_id}")

        except Exception as e:
            logger.error(f"Error recording coaching metrics: {e}")

    async def _store_metrics(self, metrics: CoachingMetrics):
        """Store coaching metrics for analysis."""
        try:
            metrics_data = {
                "type": "coaching_metrics",
                "data": asdict(metrics),
                "timestamp": datetime.now().isoformat()
            }

            await self.redis_service.store_conversation_message(
                f"metrics_{metrics.session_id}",
                "system",
                json.dumps(metrics_data, default=str),
                metrics.session_id,
                {"metric_type": "coaching_performance"}
            )

        except Exception as e:
            logger.warning(f"Failed to store coaching metrics: {e}")

    async def _update_realtime_analytics(self, metrics: CoachingMetrics):
        """Update real-time analytics dashboard."""
        try:
            analytics_update = {
                "type": "coaching_metrics_update",
                "agent_id": metrics.agent_id,
                "strategy": metrics.strategy_used.value,
                "outcome": metrics.conversation_outcome,
                "response_time": metrics.avg_response_time_ms,
                "engagement_score": metrics.engagement_score,
                "timestamp": metrics.timestamp.isoformat()
            }

            await self.websocket_manager.broadcast_intelligence_update(
                IntelligenceEventType.PERFORMANCE_UPDATE,
                analytics_update
            )

        except Exception as e:
            logger.warning(f"Failed to update real-time analytics: {e}")

    async def _check_experiment_progress(self, experiment_id: str):
        """Check if experiment has reached statistical significance."""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                return

            # Get current sample sizes
            sample_sizes = await self._get_experiment_sample_sizes(experiment_id)
            total_samples = sum(sample_sizes.values())

            # Check if minimum sample size reached
            if total_samples >= experiment.minimum_sample_size:
                results = await self._calculate_experiment_results(experiment_id)

                if results.statistical_significance:
                    # Experiment has significant results
                    await self._complete_experiment(experiment_id, results)

                elif datetime.now() >= experiment.end_date:
                    # Experiment duration ended, complete anyway
                    await self._complete_experiment(experiment_id, results)

        except Exception as e:
            logger.error(f"Error checking experiment progress: {e}")

    async def _calculate_experiment_results(self, experiment_id: str) -> ExperimentResults:
        """Calculate statistical results for A/B experiment."""
        try:
            experiment = self.active_experiments.get(experiment_id)
            if not experiment:
                raise ValueError(f"Experiment {experiment_id} not found")

            # Get metrics for each strategy
            strategy_metrics = {}
            for strategy in experiment.strategies:
                metrics = await self._get_strategy_metrics(experiment_id, strategy)
                strategy_metrics[strategy.value] = metrics

            # Perform statistical analysis
            target_metric = experiment.target_metric
            strategy_values = {}

            for strategy, metrics in strategy_metrics.items():
                if target_metric == MetricType.CONVERSION_RATE:
                    conversions = sum(1 for m in metrics if m.get('outcome') == 'converted')
                    strategy_values[strategy] = conversions / len(metrics) if metrics else 0
                elif target_metric == MetricType.ENGAGEMENT_SCORE:
                    strategy_values[strategy] = np.mean([m.get('engagement_score', 0) for m in metrics]) if metrics else 0

            # Statistical significance test (simplified)
            strategies = list(strategy_values.keys())
            if len(strategies) == 2:
                strategy_a, strategy_b = strategies
                value_a, value_b = strategy_values[strategy_a], strategy_values[strategy_b]

                # Simplified t-test (in production, use proper statistical tests)
                p_value = 0.05 if abs(value_a - value_b) > 0.1 else 0.15
                is_significant = p_value < 0.05

                winner = strategy_a if value_a > value_b else strategy_b if is_significant else None
                effect_size = abs(value_a - value_b)
            else:
                p_value = 0.1
                is_significant = False
                winner = None
                effect_size = 0.0

            # Calculate business impact
            business_impact = await self._calculate_business_impact(strategy_values)

            return ExperimentResults(
                experiment_id=experiment_id,
                strategy_results=strategy_metrics,
                winner=CoachingStrategy(winner) if winner else None,
                statistical_significance=is_significant,
                confidence_interval=(0.95, 0.99),  # Simplified
                p_value=p_value,
                effect_size=effect_size,
                business_impact_estimate=business_impact,
                recommendations=await self._generate_experiment_recommendations(strategy_values, winner)
            )

        except Exception as e:
            logger.error(f"Error calculating experiment results: {e}")
            return ExperimentResults(
                experiment_id=experiment_id,
                strategy_results={},
                winner=None,
                statistical_significance=False,
                confidence_interval=(0.0, 0.0),
                p_value=1.0,
                effect_size=0.0,
                business_impact_estimate={},
                recommendations=["Error in analysis - manual review needed"]
            )

    async def _calculate_business_impact(self, strategy_values: Dict[str, float]) -> Dict[str, float]:
        """Calculate business impact of experiment results."""
        # Simplified business impact calculation
        max_value = max(strategy_values.values()) if strategy_values else 0
        min_value = min(strategy_values.values()) if strategy_values else 0
        improvement = max_value - min_value

        return {
            "conversion_rate_improvement": improvement,
            "estimated_monthly_impact": improvement * 1000,  # Assuming 1000 leads/month
            "annual_revenue_impact": improvement * 12000 * 5000  # Simplified calculation
        }

    async def _generate_experiment_recommendations(
        self,
        strategy_values: Dict[str, float],
        winner: Optional[str]
    ) -> List[str]:
        """Generate recommendations based on experiment results."""
        recommendations = []

        if winner:
            recommendations.append(f"Implement {winner} strategy as default for similar leads")
            recommendations.append(f"Train agents on {winner} approach best practices")
            recommendations.append("Monitor performance to ensure sustained improvement")
        else:
            recommendations.append("No significant difference found - continue current approach")
            recommendations.append("Consider testing with different lead segments")
            recommendations.append("Extend experiment duration for more data")

        return recommendations

    async def generate_coaching_insights(self, agent_id: Optional[str] = None) -> List[CoachingInsight]:
        """Generate AI-powered coaching insights."""
        try:
            insights = []

            # Get recent coaching data
            coaching_data = await self._get_recent_coaching_data(agent_id)

            # Analyze patterns with Claude
            claude_analysis = await self._analyze_coaching_patterns_with_claude(coaching_data)

            # Generate insights from analysis
            insights.extend(await self._extract_insights_from_claude_analysis(claude_analysis))

            # Generate statistical insights
            insights.extend(await self._generate_statistical_insights(coaching_data))

            # Sort by impact level and confidence
            insights.sort(key=lambda x: (x.impact_level == "high", x.confidence_score), reverse=True)

            return insights[:10]  # Top 10 insights

        except Exception as e:
            logger.error(f"Error generating coaching insights: {e}")
            return []

    async def _analyze_coaching_patterns_with_claude(self, coaching_data: List[Dict]) -> str:
        """Analyze coaching patterns using Claude."""
        try:
            analysis_prompt = f"""You are an expert real estate coaching analyst. Analyze these coaching performance patterns and identify opportunities for improvement.

            Coaching Data Summary: {json.dumps(coaching_data[:20], indent=2)}

            Please analyze:
            1. Performance patterns and trends
            2. Strategy effectiveness by situation
            3. Common coaching challenges
            4. Opportunities for improvement
            5. Agent development recommendations

            Focus on actionable insights that can improve coaching effectiveness and conversion rates."""

            response = await self.claude_client.messages.create(
                model=settings.claude_model,
                max_tokens=1000,
                temperature=0.4,
                system="You are an expert coaching performance analyst.",
                messages=[{"role": "user", "content": "Analyze these coaching patterns for insights."}]
            )

            return response.content[0].text

        except Exception as e:
            logger.error(f"Error analyzing patterns with Claude: {e}")
            return "Error in pattern analysis"

    async def _extract_insights_from_claude_analysis(self, analysis: str) -> List[CoachingInsight]:
        """Extract structured insights from Claude's analysis."""
        insights = []

        try:
            # Parse Claude's analysis for insights
            lines = analysis.split('\n')
            current_insight = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if any(keyword in line.lower() for keyword in ["opportunity", "recommend", "improve"]):
                    if current_insight:
                        insights.append(current_insight)

                    current_insight = CoachingInsight(
                        insight_type="performance_optimization",
                        title=line[:50] + "..." if len(line) > 50 else line,
                        description=line,
                        impact_level="medium",
                        recommended_action="Review and implement",
                        supporting_data={},
                        confidence_score=0.8
                    )

            if current_insight:
                insights.append(current_insight)

        except Exception as e:
            logger.warning(f"Error extracting insights: {e}")

        return insights

    async def _get_recent_coaching_data(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get recent coaching performance data."""
        # This would fetch from your metrics storage
        # For now, return sample data
        return [
            {
                "agent_id": agent_id or "agent_001",
                "strategy": "empathetic",
                "outcome": "converted",
                "engagement_score": 0.8,
                "response_time": 45.2,
                "timestamp": datetime.now().isoformat()
            }
        ]

    async def _generate_statistical_insights(self, coaching_data: List[Dict]) -> List[CoachingInsight]:
        """Generate insights from statistical analysis."""
        insights = []

        try:
            if not coaching_data:
                return insights

            # Calculate key metrics
            conversion_rates = {}
            response_times = {}

            for session in coaching_data:
                strategy = session.get('strategy', 'unknown')
                outcome = session.get('outcome')
                response_time = session.get('response_time', 0)

                if strategy not in conversion_rates:
                    conversion_rates[strategy] = []
                    response_times[strategy] = []

                conversion_rates[strategy].append(1 if outcome == 'converted' else 0)
                response_times[strategy].append(response_time)

            # Find best performing strategy
            best_strategy = None
            best_rate = 0
            for strategy, conversions in conversion_rates.items():
                rate = np.mean(conversions) if conversions else 0
                if rate > best_rate:
                    best_rate = rate
                    best_strategy = strategy

            if best_strategy and best_rate > 0.6:
                insights.append(CoachingInsight(
                    insight_type="strategy_performance",
                    title=f"{best_strategy.title()} strategy shows highest conversion",
                    description=f"The {best_strategy} coaching strategy has a {best_rate:.1%} conversion rate",
                    impact_level="high",
                    recommended_action=f"Increase usage of {best_strategy} strategy for similar leads",
                    supporting_data={"conversion_rate": best_rate, "strategy": best_strategy},
                    confidence_score=0.9
                ))

        except Exception as e:
            logger.warning(f"Error generating statistical insights: {e}")

        return insights

    # Additional methods for experiment management...

    async def _store_experiment(self, experiment: CoachingExperiment):
        """Store experiment configuration."""
        # Implementation for storing experiment data
        pass

    async def _broadcast_experiment_event(self, event_type: str, experiment: CoachingExperiment):
        """Broadcast experiment events."""
        # Implementation for broadcasting experiment events
        pass

    async def _get_experiment_sample_sizes(self, experiment_id: str) -> Dict[str, int]:
        """Get current sample sizes for experiment."""
        # Implementation for getting sample sizes
        return {"empathetic": 50, "analytical": 48}  # Sample data

    async def _get_strategy_metrics(self, experiment_id: str, strategy: CoachingStrategy) -> List[Dict]:
        """Get metrics for specific strategy in experiment."""
        # Implementation for getting strategy metrics
        return []

    async def _complete_experiment(self, experiment_id: str, results: ExperimentResults):
        """Complete experiment and store results."""
        try:
            if experiment_id in self.active_experiments:
                self.active_experiments[experiment_id].status = ExperimentStatus.COMPLETED

            # Store results and notify stakeholders
            await self._store_experiment_results(experiment_id, results)
            await self._broadcast_experiment_completion(experiment_id, results)

            logger.info(f"Experiment {experiment_id} completed with winner: {results.winner}")

        except Exception as e:
            logger.error(f"Error completing experiment: {e}")

    async def _store_experiment_results(self, experiment_id: str, results: ExperimentResults):
        """Store experiment results."""
        # Implementation for storing results
        pass

    async def _broadcast_experiment_completion(self, experiment_id: str, results: ExperimentResults):
        """Broadcast experiment completion."""
        # Implementation for broadcasting completion
        pass


# Global instance
claude_coaching_analytics = ClaudeCoachingAnalytics()


async def get_coaching_analytics() -> ClaudeCoachingAnalytics:
    """Get global coaching analytics service."""
    return claude_coaching_analytics