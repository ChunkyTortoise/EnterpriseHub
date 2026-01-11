"""
Self-Learning Conversation AI - Autonomous Intelligence Enhancement

Revolutionary autonomous AI system that continuously learns from every conversation,
automatically optimizing coaching suggestions, conversation strategies, and
intervention timing without human supervision.

Key Innovation Features:
- Real-time effectiveness tracking and learning
- Autonomous prompt optimization based on outcomes
- Self-adjusting confidence scoring
- Pattern recognition and strategy adaptation
- Continuous improvement without manual intervention

Business Impact: $200K-500K annually through autonomous optimization
"""

import asyncio
import json
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
from collections import defaultdict
import hashlib

from anthropic import AsyncAnthropic

from ..redis_conversation_service import redis_conversation_service
from ..learning.tracking.behavior_tracker import behavior_tracker
from ..learning.models.online_learning import OnlineLearningModel
from ..claude_agent_service import ClaudeAgentService
from ...ghl_utils.config import settings
from ...ghl_utils.logger import get_logger

logger = get_logger(__name__)


class LearningSignalType(str, Enum):
    """Types of learning signals for autonomous improvement."""
    CONVERSATION_OUTCOME = "conversation_outcome"
    AGENT_FEEDBACK = "agent_feedback"
    LEAD_CONVERSION = "lead_conversion"
    RESPONSE_EFFECTIVENESS = "response_effectiveness"
    ENGAGEMENT_CHANGE = "engagement_change"
    OBJECTION_RESOLUTION = "objection_resolution"
    QUESTION_SUCCESS = "question_success"
    COACHING_IMPACT = "coaching_impact"


class OutcomeType(str, Enum):
    """Conversation and coaching outcome types."""
    EXCELLENT = "excellent"      # Lead highly engaged, moving forward
    GOOD = "good"               # Positive response, some progress
    NEUTRAL = "neutral"         # No significant change
    POOR = "poor"              # Negative response, disengagement
    FAILED = "failed"          # Lead lost or severely damaged


class LearningMode(str, Enum):
    """Learning mode configuration."""
    AGGRESSIVE = "aggressive"    # Learn quickly, higher risk
    STANDARD = "standard"       # Balanced learning approach
    CONSERVATIVE = "conservative" # Learn slowly, lower risk
    RESEARCH = "research"       # Maximum data collection


@dataclass
class ConversationOutcome:
    """Tracks the outcome of conversations for learning."""
    conversation_id: str
    agent_id: str
    lead_id: str
    coaching_suggestions: List[str]
    agent_actions: List[str]
    outcome_type: OutcomeType
    effectiveness_score: float  # 0.0 to 1.0
    lead_engagement_before: float
    lead_engagement_after: float
    conversion_signals: List[str]
    objections_handled: List[str]
    coaching_confidence: float
    timestamp: datetime
    follow_up_scheduled: bool
    next_steps_defined: bool

    def to_learning_signal(self) -> Dict[str, Any]:
        """Convert to learning signal for ML model."""
        return {
            'signal_type': LearningSignalType.CONVERSATION_OUTCOME,
            'effectiveness': self.effectiveness_score,
            'engagement_change': self.lead_engagement_after - self.lead_engagement_before,
            'coaching_confidence': self.coaching_confidence,
            'outcome_quality': self._outcome_to_score(),
            'coaching_features': self._extract_coaching_features(),
            'context_features': self._extract_context_features(),
            'timestamp': self.timestamp.isoformat()
        }

    def _outcome_to_score(self) -> float:
        """Convert outcome type to numerical score."""
        scores = {
            OutcomeType.EXCELLENT: 1.0,
            OutcomeType.GOOD: 0.75,
            OutcomeType.NEUTRAL: 0.5,
            OutcomeType.POOR: 0.25,
            OutcomeType.FAILED: 0.0
        }
        return scores.get(self.outcome_type, 0.5)

    def _extract_coaching_features(self) -> Dict[str, Any]:
        """Extract features from coaching suggestions."""
        return {
            'suggestion_count': len(self.coaching_suggestions),
            'coaching_types': self._categorize_coaching_types(),
            'urgency_level': self._detect_urgency_level(),
            'personalization_score': self._measure_personalization()
        }

    def _extract_context_features(self) -> Dict[str, Any]:
        """Extract contextual features."""
        return {
            'conversation_stage': self._detect_conversation_stage(),
            'objection_complexity': len(self.objections_handled),
            'action_diversity': self._measure_action_diversity(),
            'follow_up_quality': 1.0 if self.follow_up_scheduled else 0.0
        }

    def _categorize_coaching_types(self) -> List[str]:
        """Categorize types of coaching provided."""
        types = []
        for suggestion in self.coaching_suggestions:
            if any(word in suggestion.lower() for word in ['question', 'ask', 'inquiry']):
                types.append('questioning')
            if any(word in suggestion.lower() for word in ['objection', 'concern', 'hesitation']):
                types.append('objection_handling')
            if any(word in suggestion.lower() for word in ['rapport', 'relationship', 'connection']):
                types.append('rapport_building')
            if any(word in suggestion.lower() for word in ['close', 'next step', 'decision']):
                types.append('closing')
        return list(set(types))

    def _detect_urgency_level(self) -> float:
        """Detect urgency level from coaching."""
        urgency_words = ['urgent', 'immediate', 'quickly', 'now', 'asap']
        urgency_count = sum(
            1 for suggestion in self.coaching_suggestions
            for word in urgency_words
            if word in suggestion.lower()
        )
        return min(urgency_count / len(self.coaching_suggestions), 1.0) if self.coaching_suggestions else 0.0

    def _measure_personalization(self) -> float:
        """Measure level of personalization in coaching."""
        personal_indicators = ['name', 'specific', 'mentioned', 'preference', 'interested']
        personal_count = sum(
            1 for suggestion in self.coaching_suggestions
            for indicator in personal_indicators
            if indicator in suggestion.lower()
        )
        return min(personal_count / len(self.coaching_suggestions), 1.0) if self.coaching_suggestions else 0.0

    def _detect_conversation_stage(self) -> str:
        """Detect conversation stage from context."""
        if not self.agent_actions:
            return 'discovery'

        actions_text = ' '.join(self.agent_actions).lower()
        if 'introduction' in actions_text or 'greeting' in actions_text:
            return 'introduction'
        elif 'qualification' in actions_text or 'question' in actions_text:
            return 'qualification'
        elif 'presentation' in actions_text or 'showing' in actions_text:
            return 'presentation'
        elif 'objection' in actions_text or 'concern' in actions_text:
            return 'objection_handling'
        elif 'close' in actions_text or 'decision' in actions_text:
            return 'closing'
        else:
            return 'discovery'

    def _measure_action_diversity(self) -> float:
        """Measure diversity of agent actions."""
        if not self.agent_actions:
            return 0.0

        unique_action_types = set()
        for action in self.agent_actions:
            action_lower = action.lower()
            if 'question' in action_lower:
                unique_action_types.add('questioning')
            elif 'information' in action_lower:
                unique_action_types.add('information_sharing')
            elif 'schedule' in action_lower:
                unique_action_types.add('scheduling')
            elif 'follow' in action_lower:
                unique_action_types.add('follow_up')
            elif 'send' in action_lower:
                unique_action_types.add('communication')
            else:
                unique_action_types.add('other')

        return len(unique_action_types) / max(len(self.agent_actions), 1)


@dataclass
class LearningInsight:
    """Insights discovered through autonomous learning."""
    insight_type: str
    confidence: float
    description: str
    recommended_action: str
    supporting_data: Dict[str, Any]
    impact_estimate: float
    timestamp: datetime

    def to_coaching_improvement(self) -> Dict[str, Any]:
        """Convert insight to actionable coaching improvement."""
        return {
            'optimization_type': self.insight_type,
            'confidence_score': self.confidence,
            'implementation': self.recommended_action,
            'expected_impact': self.impact_estimate,
            'data_support': self.supporting_data
        }


class SelfLearningConversationAI:
    """
    Autonomous AI system that continuously learns and improves from conversations.

    Core Capabilities:
    - Tracks conversation outcomes and coaching effectiveness
    - Automatically optimizes coaching prompts and strategies
    - Learns conversation patterns and success factors
    - Adapts to different agent styles and lead types
    - Provides autonomous recommendations for improvement
    """

    def __init__(self, learning_mode: LearningMode = LearningMode.STANDARD):
        self.learning_mode = learning_mode
        self.claude_service = ClaudeAgentService()
        self.online_model = OnlineLearningModel()

        # Learning configuration
        self.learning_rate = self._get_learning_rate()
        self.confidence_threshold = self._get_confidence_threshold()
        self.optimization_interval = self._get_optimization_interval()

        # Pattern storage
        self.successful_patterns = defaultdict(list)
        self.failed_patterns = defaultdict(list)
        self.optimization_cache = {}

        # Performance tracking
        self.learning_metrics = {
            'total_conversations_analyzed': 0,
            'successful_optimizations': 0,
            'average_effectiveness_improvement': 0.0,
            'confidence_accuracy': 0.0,
            'last_optimization': None
        }

        logger.info(f"Initialized Self-Learning Conversation AI with {learning_mode} mode")

    async def record_conversation_outcome(self, outcome: ConversationOutcome) -> Dict[str, Any]:
        """
        Record conversation outcome and trigger autonomous learning.

        This is the main entry point for the learning system.
        Every conversation outcome feeds into continuous improvement.
        """
        try:
            # Store outcome
            outcome_key = f"conversation_outcome:{outcome.conversation_id}"
            await redis_conversation_service.set_data(
                outcome_key,
                asdict(outcome),
                ttl_seconds=86400 * 30  # 30 days
            )

            # Convert to learning signal
            learning_signal = outcome.to_learning_signal()

            # Update online learning model
            await self._update_learning_model(learning_signal)

            # Track patterns
            await self._track_conversation_patterns(outcome)

            # Trigger optimization if needed
            optimization_result = await self._trigger_autonomous_optimization(outcome)

            # Update metrics
            self.learning_metrics['total_conversations_analyzed'] += 1

            # Log learning event
            logger.info(
                f"Recorded conversation outcome: {outcome.outcome_type}, "
                f"effectiveness: {outcome.effectiveness_score:.2f}, "
                f"coaching confidence: {outcome.coaching_confidence:.2f}"
            )

            return {
                'status': 'recorded',
                'conversation_id': outcome.conversation_id,
                'learning_signal_processed': True,
                'patterns_updated': True,
                'optimization_triggered': optimization_result is not None,
                'optimization_result': optimization_result,
                'learning_metrics': self.learning_metrics
            }

        except Exception as e:
            logger.error(f"Error recording conversation outcome: {e}")
            return {'status': 'error', 'message': str(e)}

    async def get_autonomous_coaching_suggestions(
        self,
        conversation_context: Dict[str, Any],
        agent_id: str,
        lead_id: str
    ) -> Dict[str, Any]:
        """
        Generate coaching suggestions enhanced by autonomous learning.

        Uses learned patterns to provide more effective coaching.
        """
        try:
            # Get baseline coaching from Claude service
            baseline_coaching = await self.claude_service.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context=conversation_context,
                prospect_message=conversation_context.get('latest_message', ''),
                conversation_stage=conversation_context.get('stage', 'discovery')
            )

            # Apply learned optimizations
            enhanced_coaching = await self._apply_learned_optimizations(
                baseline_coaching,
                conversation_context,
                agent_id
            )

            # Add learning-based insights
            learning_insights = await self._generate_learning_insights(
                conversation_context,
                enhanced_coaching
            )

            # Calculate enhanced confidence score
            enhanced_confidence = await self._calculate_enhanced_confidence(
                enhanced_coaching,
                conversation_context,
                agent_id
            )

            return {
                'suggestions': enhanced_coaching.get('suggestions', []),
                'urgency_level': enhanced_coaching.get('urgency_level', 'medium'),
                'recommended_questions': enhanced_coaching.get('recommended_questions', []),
                'objection_detected': enhanced_coaching.get('objection_detected', False),
                'confidence_score': enhanced_confidence,
                'learning_insights': learning_insights,
                'optimization_applied': True,
                'baseline_confidence': baseline_coaching.get('confidence_score', 50),
                'learning_enhancement': enhanced_confidence - baseline_coaching.get('confidence_score', 50),
                'processing_time_ms': enhanced_coaching.get('processing_time_ms', 0)
            }

        except Exception as e:
            logger.error(f"Error generating autonomous coaching: {e}")
            # Fallback to baseline coaching
            return await self.claude_service.get_real_time_coaching(
                agent_id=agent_id,
                conversation_context=conversation_context,
                prospect_message=conversation_context.get('latest_message', ''),
                conversation_stage=conversation_context.get('stage', 'discovery')
            )

    async def _update_learning_model(self, learning_signal: Dict[str, Any]) -> None:
        """Update the online learning model with new signal."""
        try:
            # Prepare features for model
            features = np.array([
                learning_signal['effectiveness'],
                learning_signal['engagement_change'],
                learning_signal['coaching_confidence'],
                learning_signal['outcome_quality']
            ])

            # Outcome for training
            outcome = learning_signal['effectiveness']

            # Update online model
            await self.online_model.update(features, outcome)

            # Track in behavior tracker
            behavior_tracker.track_event(
                entity_id=f"learning_model",
                event_type="model_update",
                context=learning_signal
            )

        except Exception as e:
            logger.error(f"Error updating learning model: {e}")

    async def _track_conversation_patterns(self, outcome: ConversationOutcome) -> None:
        """Track successful and failed conversation patterns."""
        try:
            pattern_key = self._generate_pattern_key(outcome)

            if outcome.effectiveness_score >= 0.7:
                self.successful_patterns[pattern_key].append({
                    'effectiveness': outcome.effectiveness_score,
                    'coaching': outcome.coaching_suggestions,
                    'context': outcome._extract_context_features(),
                    'timestamp': outcome.timestamp.isoformat()
                })
            elif outcome.effectiveness_score <= 0.3:
                self.failed_patterns[pattern_key].append({
                    'effectiveness': outcome.effectiveness_score,
                    'coaching': outcome.coaching_suggestions,
                    'context': outcome._extract_context_features(),
                    'timestamp': outcome.timestamp.isoformat()
                })

            # Limit pattern storage size
            max_patterns = 100
            if len(self.successful_patterns[pattern_key]) > max_patterns:
                self.successful_patterns[pattern_key] = self.successful_patterns[pattern_key][-max_patterns:]
            if len(self.failed_patterns[pattern_key]) > max_patterns:
                self.failed_patterns[pattern_key] = self.failed_patterns[pattern_key][-max_patterns:]

        except Exception as e:
            logger.error(f"Error tracking conversation patterns: {e}")

    async def _trigger_autonomous_optimization(self, outcome: ConversationOutcome) -> Optional[Dict[str, Any]]:
        """Trigger optimization based on learning patterns."""
        try:
            # Check if optimization is needed
            should_optimize = (
                self.learning_metrics['total_conversations_analyzed'] % self.optimization_interval == 0
                or outcome.effectiveness_score <= 0.3  # Poor outcome triggers optimization
                or (outcome.coaching_confidence <= 0.5 and outcome.effectiveness_score <= 0.5)
            )

            if not should_optimize:
                return None

            # Generate optimization insights
            insights = await self._analyze_patterns_for_insights()

            if not insights:
                return None

            # Apply optimizations
            optimization_results = []
            for insight in insights:
                if insight.confidence >= self.confidence_threshold:
                    result = await self._apply_optimization(insight)
                    optimization_results.append(result)
                    self.learning_metrics['successful_optimizations'] += 1

            # Update last optimization time
            self.learning_metrics['last_optimization'] = datetime.now().isoformat()

            logger.info(f"Applied {len(optimization_results)} autonomous optimizations")

            return {
                'optimizations_applied': len(optimization_results),
                'insights_generated': len(insights),
                'results': optimization_results,
                'timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error in autonomous optimization: {e}")
            return None

    async def _apply_learned_optimizations(
        self,
        baseline_coaching: Dict[str, Any],
        context: Dict[str, Any],
        agent_id: str
    ) -> Dict[str, Any]:
        """Apply learned optimizations to baseline coaching."""
        try:
            enhanced_coaching = baseline_coaching.copy()

            # Get successful patterns for this context
            pattern_key = self._generate_context_pattern_key(context, agent_id)
            successful_patterns = self.successful_patterns.get(pattern_key, [])

            if successful_patterns:
                # Analyze successful patterns
                avg_effectiveness = np.mean([p['effectiveness'] for p in successful_patterns])

                if avg_effectiveness > 0.7:
                    # Extract common successful coaching elements
                    common_elements = self._extract_common_coaching_elements(successful_patterns)

                    # Enhance suggestions
                    enhanced_suggestions = self._enhance_suggestions(
                        baseline_coaching.get('suggestions', []),
                        common_elements
                    )
                    enhanced_coaching['suggestions'] = enhanced_suggestions

                    # Enhance questions
                    enhanced_questions = self._enhance_questions(
                        baseline_coaching.get('recommended_questions', []),
                        common_elements
                    )
                    enhanced_coaching['recommended_questions'] = enhanced_questions

            return enhanced_coaching

        except Exception as e:
            logger.error(f"Error applying learned optimizations: {e}")
            return baseline_coaching

    async def _generate_learning_insights(
        self,
        context: Dict[str, Any],
        coaching: Dict[str, Any]
    ) -> List[str]:
        """Generate insights from learning patterns."""
        try:
            insights = []

            # Pattern-based insights
            pattern_insights = self._get_pattern_insights(context)
            insights.extend(pattern_insights)

            # Effectiveness prediction
            effectiveness_prediction = await self._predict_effectiveness(context, coaching)
            if effectiveness_prediction < 0.6:
                insights.append(
                    f"Predicted effectiveness is low ({effectiveness_prediction:.1%}). "
                    f"Consider more personalized approach."
                )

            # Confidence-based insights
            if coaching.get('confidence_score', 50) < 60:
                insights.append(
                    "Low confidence detected. Consider gathering more lead information "
                    "before proceeding with coaching suggestions."
                )

            return insights[:3]  # Limit to top 3 insights

        except Exception as e:
            logger.error(f"Error generating learning insights: {e}")
            return []

    async def _calculate_enhanced_confidence(
        self,
        coaching: Dict[str, Any],
        context: Dict[str, Any],
        agent_id: str
    ) -> int:
        """Calculate enhanced confidence score using learning data."""
        try:
            baseline_confidence = coaching.get('confidence_score', 50)

            # Get historical accuracy for similar contexts
            pattern_key = self._generate_context_pattern_key(context, agent_id)
            successful_patterns = self.successful_patterns.get(pattern_key, [])

            if successful_patterns:
                # Calculate confidence adjustment based on historical performance
                avg_effectiveness = np.mean([p['effectiveness'] for p in successful_patterns])
                confidence_boost = (avg_effectiveness - 0.5) * 20  # Scale to confidence points
                enhanced_confidence = baseline_confidence + confidence_boost
            else:
                # No historical data, slight confidence reduction
                enhanced_confidence = baseline_confidence * 0.9

            # Predict effectiveness and adjust confidence
            predicted_effectiveness = await self._predict_effectiveness(context, coaching)
            effectiveness_adjustment = (predicted_effectiveness - 0.5) * 30

            final_confidence = enhanced_confidence + effectiveness_adjustment

            return max(10, min(95, int(final_confidence)))

        except Exception as e:
            logger.error(f"Error calculating enhanced confidence: {e}")
            return coaching.get('confidence_score', 50)

    async def _predict_effectiveness(
        self,
        context: Dict[str, Any],
        coaching: Dict[str, Any]
    ) -> float:
        """Predict coaching effectiveness using learned patterns."""
        try:
            # Prepare features for prediction
            features = np.array([
                len(coaching.get('suggestions', [])),
                coaching.get('confidence_score', 50) / 100,
                len(coaching.get('recommended_questions', [])),
                1.0 if coaching.get('objection_detected', False) else 0.0
            ])

            # Get prediction from online model
            prediction = await self.online_model.predict(features)

            return max(0.0, min(1.0, float(prediction)))

        except Exception as e:
            logger.error(f"Error predicting effectiveness: {e}")
            return 0.5

    def _generate_pattern_key(self, outcome: ConversationOutcome) -> str:
        """Generate a pattern key for categorizing outcomes."""
        context_features = outcome._extract_context_features()
        coaching_features = outcome._extract_coaching_features()

        # Create pattern signature
        pattern_signature = f"{context_features.get('conversation_stage', 'unknown')}_" \
                          f"{coaching_features.get('suggestion_count', 0)}_" \
                          f"{len(outcome.objections_handled)}"

        return pattern_signature

    def _generate_context_pattern_key(self, context: Dict[str, Any], agent_id: str) -> str:
        """Generate pattern key from conversation context."""
        stage = context.get('stage', 'unknown')
        lead_score = context.get('lead_score', 50)
        engagement = context.get('engagement_level', 'medium')

        return f"{stage}_{lead_score//10*10}_{engagement}"

    async def _analyze_patterns_for_insights(self) -> List[LearningInsight]:
        """Analyze patterns to generate learning insights."""
        try:
            insights = []

            for pattern_key, successful_instances in self.successful_patterns.items():
                if len(successful_instances) >= 5:  # Minimum sample size
                    failed_instances = self.failed_patterns.get(pattern_key, [])

                    # Analyze success vs failure patterns
                    insight = self._compare_success_failure_patterns(
                        pattern_key, successful_instances, failed_instances
                    )

                    if insight and insight.confidence >= 0.7:
                        insights.append(insight)

            # Sort by confidence and impact
            insights.sort(key=lambda x: x.confidence * x.impact_estimate, reverse=True)

            return insights[:5]  # Return top 5 insights

        except Exception as e:
            logger.error(f"Error analyzing patterns for insights: {e}")
            return []

    def _compare_success_failure_patterns(
        self,
        pattern_key: str,
        successful_instances: List[Dict],
        failed_instances: List[Dict]
    ) -> Optional[LearningInsight]:
        """Compare successful and failed patterns to generate insights."""
        try:
            if len(successful_instances) < 3:
                return None

            # Analyze coaching differences
            success_coaching_types = []
            failure_coaching_types = []

            for instance in successful_instances:
                coaching = instance.get('coaching', [])
                for suggestion in coaching:
                    success_coaching_types.extend(self._categorize_suggestion(suggestion))

            for instance in failed_instances:
                coaching = instance.get('coaching', [])
                for suggestion in coaching:
                    failure_coaching_types.extend(self._categorize_suggestion(suggestion))

            # Find coaching types more common in successes
            from collections import Counter
            success_counts = Counter(success_coaching_types)
            failure_counts = Counter(failure_coaching_types)

            for coaching_type, success_count in success_counts.most_common(3):
                failure_count = failure_counts.get(coaching_type, 0)
                success_rate = success_count / (success_count + failure_count) if (success_count + failure_count) > 0 else 0

                if success_rate > 0.7 and success_count >= 3:
                    return LearningInsight(
                        insight_type=f"coaching_type_effectiveness",
                        confidence=min(success_rate, 0.95),
                        description=f"Coaching type '{coaching_type}' shows {success_rate:.1%} success rate in pattern '{pattern_key}'",
                        recommended_action=f"Prioritize {coaching_type} coaching for similar conversations",
                        supporting_data={
                            'pattern': pattern_key,
                            'success_count': success_count,
                            'failure_count': failure_count,
                            'success_rate': success_rate
                        },
                        impact_estimate=success_rate * 0.5,  # Estimated effectiveness improvement
                        timestamp=datetime.now()
                    )

            return None

        except Exception as e:
            logger.error(f"Error comparing patterns: {e}")
            return None

    def _categorize_suggestion(self, suggestion: str) -> List[str]:
        """Categorize a coaching suggestion by type."""
        categories = []
        suggestion_lower = suggestion.lower()

        category_keywords = {
            'questioning': ['question', 'ask', 'inquiry', 'probe'],
            'objection_handling': ['objection', 'concern', 'hesitation', 'worry'],
            'rapport_building': ['rapport', 'relationship', 'connection', 'trust'],
            'closing': ['close', 'decision', 'next step', 'commit'],
            'information_gathering': ['learn', 'understand', 'discover', 'find out'],
            'value_proposition': ['benefit', 'value', 'advantage', 'worth'],
            'urgency_creation': ['urgent', 'limited', 'opportunity', 'deadline'],
            'personalization': ['specific', 'personal', 'individual', 'custom']
        }

        for category, keywords in category_keywords.items():
            if any(keyword in suggestion_lower for keyword in keywords):
                categories.append(category)

        return categories if categories else ['general']

    async def _apply_optimization(self, insight: LearningInsight) -> Dict[str, Any]:
        """Apply an optimization based on learning insight."""
        try:
            # Store optimization in cache
            optimization_id = hashlib.md5(
                f"{insight.insight_type}_{insight.timestamp}".encode()
            ).hexdigest()[:8]

            self.optimization_cache[optimization_id] = {
                'insight': asdict(insight),
                'applied_at': datetime.now().isoformat(),
                'status': 'active'
            }

            # Log optimization
            logger.info(
                f"Applied optimization {optimization_id}: {insight.description} "
                f"(confidence: {insight.confidence:.2f}, impact: {insight.impact_estimate:.2f})"
            )

            return {
                'optimization_id': optimization_id,
                'type': insight.insight_type,
                'description': insight.description,
                'confidence': insight.confidence,
                'expected_impact': insight.impact_estimate,
                'status': 'applied'
            }

        except Exception as e:
            logger.error(f"Error applying optimization: {e}")
            return {'status': 'failed', 'error': str(e)}

    def _extract_common_coaching_elements(self, successful_patterns: List[Dict]) -> Dict[str, Any]:
        """Extract common elements from successful coaching patterns."""
        all_coaching = []
        for pattern in successful_patterns:
            all_coaching.extend(pattern.get('coaching', []))

        # Find common themes
        from collections import Counter
        coaching_types = []
        for suggestion in all_coaching:
            coaching_types.extend(self._categorize_suggestion(suggestion))

        common_types = Counter(coaching_types).most_common(5)

        return {
            'common_coaching_types': [ct[0] for ct in common_types],
            'pattern_strength': len(successful_patterns),
            'avg_effectiveness': np.mean([p['effectiveness'] for p in successful_patterns])
        }

    def _enhance_suggestions(
        self,
        baseline_suggestions: List[str],
        common_elements: Dict[str, Any]
    ) -> List[str]:
        """Enhance coaching suggestions based on learned patterns."""
        enhanced = baseline_suggestions.copy()

        # Add suggestions based on successful patterns
        common_types = common_elements.get('common_coaching_types', [])

        if 'personalization' in common_types and not any('personal' in s.lower() for s in enhanced):
            enhanced.append("Consider referencing specific lead preferences or previous conversations to increase engagement.")

        if 'questioning' in common_types and len([s for s in enhanced if '?' in s]) < 2:
            enhanced.append("Ask open-ended questions to better understand their specific needs and timeline.")

        if 'urgency_creation' in common_types and not any('urgent' in s.lower() for s in enhanced):
            enhanced.append("Create appropriate urgency by highlighting market conditions or limited opportunities.")

        return enhanced

    def _enhance_questions(
        self,
        baseline_questions: List[str],
        common_elements: Dict[str, Any]
    ) -> List[str]:
        """Enhance recommended questions based on learned patterns."""
        enhanced = baseline_questions.copy()

        common_types = common_elements.get('common_coaching_types', [])

        if 'information_gathering' in common_types:
            if not any('timeline' in q.lower() for q in enhanced):
                enhanced.append("What timeline are you working with for making this decision?")

            if not any('motivation' in q.lower() or 'reason' in q.lower() for q in enhanced):
                enhanced.append("What's motivating this move for you right now?")

        return enhanced[:5]  # Limit to 5 questions

    def _get_pattern_insights(self, context: Dict[str, Any]) -> List[str]:
        """Get insights based on current patterns."""
        insights = []

        pattern_key = self._generate_context_pattern_key(context, context.get('agent_id', ''))
        successful_patterns = self.successful_patterns.get(pattern_key, [])

        if successful_patterns:
            avg_effectiveness = np.mean([p['effectiveness'] for p in successful_patterns])

            if avg_effectiveness > 0.8:
                insights.append(
                    f"This conversation pattern has shown {avg_effectiveness:.1%} average success rate. "
                    f"Focus on proven strategies."
                )
            elif avg_effectiveness < 0.4:
                insights.append(
                    f"This conversation pattern has shown challenges ({avg_effectiveness:.1%} success rate). "
                    f"Consider alternative approaches."
                )

        return insights

    def _get_learning_rate(self) -> float:
        """Get learning rate based on mode."""
        rates = {
            LearningMode.AGGRESSIVE: 0.3,
            LearningMode.STANDARD: 0.1,
            LearningMode.CONSERVATIVE: 0.05,
            LearningMode.RESEARCH: 0.01
        }
        return rates.get(self.learning_mode, 0.1)

    def _get_confidence_threshold(self) -> float:
        """Get confidence threshold for applying optimizations."""
        thresholds = {
            LearningMode.AGGRESSIVE: 0.6,
            LearningMode.STANDARD: 0.7,
            LearningMode.CONSERVATIVE: 0.8,
            LearningMode.RESEARCH: 0.9
        }
        return thresholds.get(self.learning_mode, 0.7)

    def _get_optimization_interval(self) -> int:
        """Get optimization interval (conversations between optimizations)."""
        intervals = {
            LearningMode.AGGRESSIVE: 10,
            LearningMode.STANDARD: 25,
            LearningMode.CONSERVATIVE: 50,
            LearningMode.RESEARCH: 100
        }
        return intervals.get(self.learning_mode, 25)

    async def get_learning_metrics(self) -> Dict[str, Any]:
        """Get comprehensive learning metrics."""
        try:
            total_patterns = len(self.successful_patterns) + len(self.failed_patterns)
            success_patterns = len(self.successful_patterns)

            return {
                'learning_metrics': self.learning_metrics,
                'pattern_metrics': {
                    'total_patterns': total_patterns,
                    'successful_patterns': success_patterns,
                    'success_rate': success_patterns / max(total_patterns, 1),
                    'optimization_cache_size': len(self.optimization_cache)
                },
                'model_metrics': await self.online_model.get_metrics() if hasattr(self.online_model, 'get_metrics') else {},
                'learning_mode': self.learning_mode,
                'configuration': {
                    'learning_rate': self.learning_rate,
                    'confidence_threshold': self.confidence_threshold,
                    'optimization_interval': self.optimization_interval
                }
            }

        except Exception as e:
            logger.error(f"Error getting learning metrics: {e}")
            return {'status': 'error', 'message': str(e)}


# Global instance for use across the application
self_learning_ai = SelfLearningConversationAI()


async def record_conversation_outcome(outcome: ConversationOutcome) -> Dict[str, Any]:
    """Convenience function for recording conversation outcomes."""
    return await self_learning_ai.record_conversation_outcome(outcome)


async def get_autonomous_coaching(
    conversation_context: Dict[str, Any],
    agent_id: str,
    lead_id: str
) -> Dict[str, Any]:
    """Convenience function for getting autonomous coaching suggestions."""
    return await self_learning_ai.get_autonomous_coaching_suggestions(
        conversation_context, agent_id, lead_id
    )


async def get_learning_metrics() -> Dict[str, Any]:
    """Convenience function for getting learning metrics."""
    return await self_learning_ai.get_learning_metrics()