"""
Predictive Lead Intervention Strategies (Phase 5: Advanced AI Features)

Advanced intervention system that predicts optimal timing, methods, and content
for lead outreach based on behavioral analysis, engagement patterns, and churn
risk assessment. Maximizes conversion rates while preventing lead attrition
through intelligent, personalized intervention strategies.

Features:
- Predictive intervention timing (optimal moments for outreach)
- Multi-channel intervention orchestration (email, phone, SMS, in-person)
- Behavioral trigger-based interventions
- Churn prevention automation
- Conversion acceleration strategies
- Personalized content generation per intervention
- A/B testing for intervention effectiveness
- Real-time intervention adjustment based on response

Intervention Types:
- Preventive: Before disengagement occurs
- Reactive: In response to behavioral changes
- Progressive: Escalating intervention intensity
- Opportunistic: Capitalizing on engagement spikes
- Relationship: Long-term nurturing strategies

Performance Targets:
- Intervention timing accuracy: >90%
- Churn prevention rate: >75%
- Conversion acceleration: +25%
- Response rate improvement: +40%
"""

import asyncio
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np
import pandas as pd

# Local imports
from ghl_real_estate_ai.services.claude_semantic_analyzer import ClaudeSemanticAnalyzer
from ghl_real_estate_ai.services.claude.advanced.predictive_behavior_analyzer import (
    AdvancedPredictiveBehaviorAnalyzer, AdvancedPredictionType, BehavioralAnomaly,
    InterventionStrategy
)
from ghl_real_estate_ai.services.claude.advanced.industry_vertical_specialization import (
    IndustryVerticalSpecializer, RealEstateVertical, ClientSegment
)

logger = logging.getLogger(__name__)


class InterventionTrigger(Enum):
    """Triggers that initiate intervention strategies"""
    CHURN_RISK_SPIKE = "churn_risk_spike"
    ENGAGEMENT_DECLINE = "engagement_decline"
    RESPONSE_DELAY = "response_delay"
    BEHAVIORAL_ANOMALY = "behavioral_anomaly"
    CONVERSION_OPPORTUNITY = "conversion_opportunity"
    COMPETITIVE_THREAT = "competitive_threat"
    TIMELINE_PRESSURE = "timeline_pressure"
    DECISION_MOMENT = "decision_moment"
    RELATIONSHIP_MAINTENANCE = "relationship_maintenance"
    SEASONAL_OPPORTUNITY = "seasonal_opportunity"


class InterventionChannel(Enum):
    """Available intervention channels"""
    PERSONAL_CALL = "personal_call"
    PERSONALIZED_EMAIL = "personalized_email"
    TEXT_MESSAGE = "text_message"
    IN_PERSON_MEETING = "in_person_meeting"
    VIDEO_CALL = "video_call"
    HANDWRITTEN_NOTE = "handwritten_note"
    DIRECT_MAIL = "direct_mail"
    SOCIAL_MEDIA_ENGAGEMENT = "social_media_engagement"
    REFERRAL_INTRODUCTION = "referral_introduction"
    EVENT_INVITATION = "event_invitation"


class InterventionUrgency(Enum):
    """Urgency levels for interventions"""
    IMMEDIATE = "immediate"  # Within 1 hour
    HIGH = "high"           # Within 4 hours
    MODERATE = "moderate"   # Within 24 hours
    LOW = "low"            # Within 3 days
    SCHEDULED = "scheduled" # At specific optimal time


class InterventionOutcome(Enum):
    """Possible outcomes from interventions"""
    SUCCESSFUL_ENGAGEMENT = "successful_engagement"
    PARTIAL_ENGAGEMENT = "partial_engagement"
    NO_RESPONSE = "no_response"
    NEGATIVE_RESPONSE = "negative_response"
    CONVERSION_ACCELERATED = "conversion_accelerated"
    CHURN_PREVENTED = "churn_prevented"
    RELATIONSHIP_STRENGTHENED = "relationship_strengthened"
    FOLLOW_UP_REQUIRED = "follow_up_required"


@dataclass
class InterventionContext:
    """Context information for intervention decision making"""
    lead_id: str
    current_behavioral_state: Dict[str, Any]
    historical_patterns: Dict[str, Any]
    vertical_context: Optional[RealEstateVertical]
    client_segment: Optional[ClientSegment]
    recent_interactions: List[Dict]
    engagement_trajectory: List[float]
    churn_risk_evolution: List[float]
    conversion_probability_trend: List[float]
    external_factors: Dict[str, Any]
    agent_relationship_quality: float
    previous_interventions: List[Dict]
    market_conditions: Dict[str, Any]


@dataclass
class InterventionStrategy:
    """Comprehensive intervention strategy definition"""
    strategy_id: str
    trigger: InterventionTrigger
    urgency: InterventionUrgency
    primary_channel: InterventionChannel
    fallback_channels: List[InterventionChannel]

    # Timing and scheduling
    optimal_timing: datetime
    timing_flexibility_hours: int
    follow_up_sequence: List[Tuple[InterventionChannel, int]]  # (channel, hours_delay)

    # Content and messaging
    message_framework: Dict[str, str]
    personalization_variables: Dict[str, Any]
    call_to_action: str
    value_proposition: str

    # Behavioral adaptation
    communication_style: str
    emotional_tone: str
    information_depth: str
    relationship_approach: str

    # Success criteria
    success_metrics: Dict[str, float]
    escalation_triggers: List[str]
    termination_conditions: List[str]

    # Performance tracking
    expected_response_rate: float
    predicted_outcome: InterventionOutcome
    confidence_score: float
    risk_factors: List[str]


@dataclass
class InterventionResult:
    """Result and outcome tracking for interventions"""
    intervention_id: str
    strategy_id: str
    execution_timestamp: datetime
    channel_used: InterventionChannel

    # Response tracking
    response_received: bool
    response_timestamp: Optional[datetime]
    response_type: str
    response_content: Optional[str]

    # Outcome assessment
    achieved_outcome: InterventionOutcome
    success_score: float
    engagement_impact: float
    conversion_impact: float
    relationship_impact: float

    # Performance metrics
    response_time_hours: Optional[float]
    follow_up_required: bool
    escalation_triggered: bool

    # Learning data
    behavioral_changes_observed: Dict[str, Any]
    unexpected_outcomes: List[str]
    improvement_insights: List[str]


@dataclass
class InterventionCampaign:
    """Multi-touch intervention campaign"""
    campaign_id: str
    lead_id: str
    campaign_goal: str
    start_date: datetime
    expected_duration_days: int

    # Campaign strategy
    intervention_sequence: List[InterventionStrategy]
    decision_points: List[Dict[str, Any]]
    success_criteria: Dict[str, float]

    # Performance tracking
    interventions_executed: List[InterventionResult]
    current_stage: int
    campaign_success_score: float

    # Dynamic adjustment
    strategy_adjustments: List[Dict[str, Any]]
    learning_insights: List[str]
    next_intervention_date: Optional[datetime]


class PredictiveLeadInterventionEngine:
    """
    🎯 Predictive Lead Intervention Engine

    Advanced system for predicting optimal intervention timing and strategies
    to maximize conversion rates and prevent lead churn through intelligent,
    personalized outreach orchestration.
    """

    def __init__(self):
        self.claude_analyzer = ClaudeSemanticAnalyzer()
        self.behavior_analyzer = AdvancedPredictiveBehaviorAnalyzer()
        self.vertical_specializer = IndustryVerticalSpecializer()

        # Intervention models and strategies
        self.intervention_models = {}
        self.strategy_templates = self._initialize_strategy_templates()
        self.channel_effectiveness_models = {}

        # Active interventions tracking
        self.active_interventions: Dict[str, InterventionCampaign] = {}
        self.intervention_history: List[InterventionResult] = []

        # Performance benchmarks
        self.performance_targets = {
            'intervention_timing_accuracy': 0.90,
            'churn_prevention_rate': 0.75,
            'conversion_acceleration_rate': 0.25,
            'response_rate_improvement': 0.40
        }

        # Learning and optimization
        self.intervention_effectiveness_data = {}
        self.channel_preference_models = {}

        # Real-time monitoring
        self.intervention_queue = []
        self.monitoring_alerts = []

    def _initialize_strategy_templates(self) -> Dict[InterventionTrigger, List[InterventionStrategy]]:
        """Initialize intervention strategy templates"""
        templates = {}

        # Churn Risk Spike Interventions
        templates[InterventionTrigger.CHURN_RISK_SPIKE] = [
            InterventionStrategy(
                strategy_id="churn_prevention_immediate",
                trigger=InterventionTrigger.CHURN_RISK_SPIKE,
                urgency=InterventionUrgency.IMMEDIATE,
                primary_channel=InterventionChannel.PERSONAL_CALL,
                fallback_channels=[InterventionChannel.PERSONALIZED_EMAIL, InterventionChannel.TEXT_MESSAGE],

                optimal_timing=datetime.now(),  # Will be calculated dynamically
                timing_flexibility_hours=2,
                follow_up_sequence=[
                    (InterventionChannel.PERSONALIZED_EMAIL, 4),
                    (InterventionChannel.TEXT_MESSAGE, 24),
                    (InterventionChannel.IN_PERSON_MEETING, 72)
                ],

                message_framework={
                    "opening": "I wanted to personally reach out because I value our relationship",
                    "concern_acknowledgment": "I sense you might have some concerns about moving forward",
                    "value_restatement": "Let me clarify how this opportunity aligns with your goals",
                    "next_steps": "Can we schedule a brief conversation to address any questions?"
                },
                personalization_variables={
                    "relationship_duration": "dynamic",
                    "specific_concerns": "detected_from_behavior",
                    "value_props": "vertical_specific",
                    "timeline_flexibility": "client_preference"
                },
                call_to_action="Schedule 15-minute clarification call",
                value_proposition="Ensure you have all information needed for confident decision",

                communication_style="concerned_professional",
                emotional_tone="supportive_understanding",
                information_depth="focused_targeted",
                relationship_approach="personal_investment",

                success_metrics={
                    "response_rate": 0.75,
                    "engagement_restoration": 0.60,
                    "churn_prevention": 0.70
                },
                escalation_triggers=["no_response_48h", "negative_sentiment"],
                termination_conditions=["explicit_rejection", "conversion_completed"],

                expected_response_rate=0.65,
                predicted_outcome=InterventionOutcome.CHURN_PREVENTED,
                confidence_score=0.80,
                risk_factors=["timing_sensitivity", "relationship_quality"]
            ),

            InterventionStrategy(
                strategy_id="churn_prevention_value_focused",
                trigger=InterventionTrigger.CHURN_RISK_SPIKE,
                urgency=InterventionUrgency.HIGH,
                primary_channel=InterventionChannel.PERSONALIZED_EMAIL,
                fallback_channels=[InterventionChannel.DIRECT_MAIL, InterventionChannel.VIDEO_CALL],

                optimal_timing=datetime.now(),
                timing_flexibility_hours=6,
                follow_up_sequence=[
                    (InterventionChannel.PERSONAL_CALL, 12),
                    (InterventionChannel.IN_PERSON_MEETING, 48)
                ],

                message_framework={
                    "opening": "I've been thinking about your specific situation and wanted to share some insights",
                    "value_demonstration": "Based on our conversations, here's how this addresses your key priorities",
                    "market_context": "Current market conditions create unique opportunities for someone in your position",
                    "next_steps": "I'd love to discuss how we can move forward together"
                },
                personalization_variables={
                    "specific_priorities": "extracted_from_needs",
                    "market_insights": "vertical_specific",
                    "competitive_advantages": "property_specific",
                    "decision_timeline": "client_preference"
                },
                call_to_action="Review personalized market analysis",
                value_proposition="Exclusive insights and opportunities aligned with your goals",

                communication_style="consultative_expert",
                emotional_tone="confident_informative",
                information_depth="comprehensive_analytical",
                relationship_approach="trusted_advisor",

                success_metrics={
                    "response_rate": 0.55,
                    "engagement_renewal": 0.45,
                    "information_request": 0.65
                },
                escalation_triggers=["continued_disengagement"],
                termination_conditions=["engagement_restored", "explicit_feedback"],

                expected_response_rate=0.50,
                predicted_outcome=InterventionOutcome.SUCCESSFUL_ENGAGEMENT,
                confidence_score=0.70,
                risk_factors=["information_overload", "timing_mismatch"]
            )
        ]

        # Engagement Decline Interventions
        templates[InterventionTrigger.ENGAGEMENT_DECLINE] = [
            InterventionStrategy(
                strategy_id="engagement_restoration_personal",
                trigger=InterventionTrigger.ENGAGEMENT_DECLINE,
                urgency=InterventionUrgency.MODERATE,
                primary_channel=InterventionChannel.PERSONAL_CALL,
                fallback_channels=[InterventionChannel.TEXT_MESSAGE, InterventionChannel.PERSONALIZED_EMAIL],

                optimal_timing=datetime.now(),
                timing_flexibility_hours=12,
                follow_up_sequence=[
                    (InterventionChannel.PERSONALIZED_EMAIL, 6),
                    (InterventionChannel.TEXT_MESSAGE, 24)
                ],

                message_framework={
                    "opening": "I noticed we haven't connected recently and wanted to check in",
                    "relationship_focus": "Your success in finding the right property is important to me",
                    "assistance_offer": "Is there anything I can help clarify or any new developments in your situation?",
                    "next_steps": "Let's reconnect when it's convenient for you"
                },
                personalization_variables={
                    "last_interaction": "time_since_contact",
                    "previous_interests": "property_preferences",
                    "life_changes": "detected_circumstances",
                    "preferred_communication": "historical_preference"
                },
                call_to_action="Brief check-in conversation",
                value_proposition="Continued support and updated market information",

                communication_style="friendly_professional",
                emotional_tone="caring_supportive",
                information_depth="light_conversational",
                relationship_approach="relationship_maintenance",

                success_metrics={
                    "response_rate": 0.60,
                    "conversation_renewal": 0.40,
                    "engagement_increase": 0.35
                },
                escalation_triggers=["no_response_week"],
                termination_conditions=["engagement_restored", "client_communication"],

                expected_response_rate=0.55,
                predicted_outcome=InterventionOutcome.PARTIAL_ENGAGEMENT,
                confidence_score=0.75,
                risk_factors=["communication_preferences", "life_circumstances"]
            )
        ]

        # Conversion Opportunity Interventions
        templates[InterventionTrigger.CONVERSION_OPPORTUNITY] = [
            InterventionStrategy(
                strategy_id="conversion_acceleration_urgent",
                trigger=InterventionTrigger.CONVERSION_OPPORTUNITY,
                urgency=InterventionUrgency.HIGH,
                primary_channel=InterventionChannel.PERSONAL_CALL,
                fallback_channels=[InterventionChannel.IN_PERSON_MEETING, InterventionChannel.VIDEO_CALL],

                optimal_timing=datetime.now(),
                timing_flexibility_hours=4,
                follow_up_sequence=[
                    (InterventionChannel.PERSONALIZED_EMAIL, 2),
                    (InterventionChannel.TEXT_MESSAGE, 6)
                ],

                message_framework={
                    "opening": "I'm excited to share that the property you've been considering has some new developments",
                    "urgency_creation": "There's been increased interest, and I want to ensure you have priority consideration",
                    "decision_facilitation": "Based on our conversations, this seems like the perfect match for your needs",
                    "next_steps": "Let's discuss securing this opportunity today"
                },
                personalization_variables={
                    "specific_property": "property_details",
                    "competition_level": "market_activity",
                    "client_priorities": "stated_preferences",
                    "decision_factors": "behavioral_analysis"
                },
                call_to_action="Schedule immediate decision consultation",
                value_proposition="Secure ideal property before market opportunity passes",

                communication_style="enthusiastic_professional",
                emotional_tone="excited_urgent",
                information_depth="focused_decisive",
                relationship_approach="collaborative_partner",

                success_metrics={
                    "response_rate": 0.85,
                    "meeting_scheduled": 0.70,
                    "decision_acceleration": 0.60
                },
                escalation_triggers=["interest_from_others"],
                termination_conditions=["decision_made", "opportunity_expired"],

                expected_response_rate=0.80,
                predicted_outcome=InterventionOutcome.CONVERSION_ACCELERATED,
                confidence_score=0.85,
                risk_factors=["market_timing", "decision_readiness"]
            )
        ]

        # Decision Moment Interventions
        templates[InterventionTrigger.DECISION_MOMENT] = [
            InterventionStrategy(
                strategy_id="decision_support_comprehensive",
                trigger=InterventionTrigger.DECISION_MOMENT,
                urgency=InterventionUrgency.IMMEDIATE,
                primary_channel=InterventionChannel.IN_PERSON_MEETING,
                fallback_channels=[InterventionChannel.VIDEO_CALL, InterventionChannel.PERSONAL_CALL],

                optimal_timing=datetime.now(),
                timing_flexibility_hours=1,
                follow_up_sequence=[
                    (InterventionChannel.PERSONALIZED_EMAIL, 1),
                    (InterventionChannel.PERSONAL_CALL, 4)
                ],

                message_framework={
                    "opening": "I understand you're at a decision point, and I'm here to support you",
                    "decision_support": "Let's review all the factors together to ensure you feel completely confident",
                    "risk_mitigation": "I'll address any final concerns and ensure you have everything you need",
                    "next_steps": "We can proceed at your pace with full support throughout the process"
                },
                personalization_variables={
                    "decision_factors": "key_considerations",
                    "remaining_concerns": "identified_hesitations",
                    "support_needed": "decision_style",
                    "timeline_pressure": "external_factors"
                },
                call_to_action="Final decision consultation meeting",
                value_proposition="Complete support and confidence for your important decision",

                communication_style="supportive_authoritative",
                emotional_tone="calm_confident",
                information_depth="comprehensive_clear",
                relationship_approach="trusted_guide",

                success_metrics={
                    "response_rate": 0.90,
                    "meeting_completion": 0.85,
                    "decision_facilitation": 0.75
                },
                escalation_triggers=["external_pressure"],
                termination_conditions=["decision_completed", "postponement_requested"],

                expected_response_rate=0.85,
                predicted_outcome=InterventionOutcome.CONVERSION_ACCELERATED,
                confidence_score=0.90,
                risk_factors=["decision_complexity", "external_influences"]
            )
        ]

        return templates

    async def predict_optimal_intervention(
        self,
        lead_id: str,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any],
        behavioral_predictions: List[Dict]
    ) -> List[InterventionStrategy]:
        """
        Predict optimal intervention strategies for a lead

        Args:
            lead_id: Lead identifier
            conversation_history: Recent conversations
            interaction_data: Interaction metrics
            behavioral_predictions: Advanced behavioral predictions

        Returns:
            List of recommended intervention strategies ranked by effectiveness
        """
        try:
            # Create intervention context
            context = await self._build_intervention_context(
                lead_id, conversation_history, interaction_data, behavioral_predictions
            )

            # Identify intervention triggers
            active_triggers = await self._identify_intervention_triggers(context)

            # Generate candidate strategies for each trigger
            candidate_strategies = []
            for trigger in active_triggers:
                trigger_strategies = await self._generate_strategies_for_trigger(
                    trigger, context
                )
                candidate_strategies.extend(trigger_strategies)

            # Rank strategies by predicted effectiveness
            ranked_strategies = await self._rank_intervention_strategies(
                candidate_strategies, context
            )

            # Optimize timing for top strategies
            optimized_strategies = await self._optimize_intervention_timing(
                ranked_strategies, context
            )

            logger.info(f"Generated {len(optimized_strategies)} intervention strategies for lead {lead_id}")
            return optimized_strategies

        except Exception as e:
            logger.error(f"Error predicting optimal intervention: {e}")
            return []

    async def _build_intervention_context(
        self,
        lead_id: str,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any],
        behavioral_predictions: List[Dict]
    ) -> InterventionContext:
        """Build comprehensive context for intervention decision making"""
        try:
            # Detect vertical and client segment
            vertical_analysis = await self.vertical_specializer.detect_vertical_from_conversation(
                conversation_history, interaction_data
            )

            # Extract behavioral state
            current_behavioral_state = {
                'engagement_level': interaction_data.get('engagement_score', 0.5),
                'response_pattern': self._analyze_response_pattern(conversation_history),
                'content_preferences': self._analyze_content_preferences(conversation_history),
                'communication_style': self._detect_communication_style(conversation_history)
            }

            # Analyze engagement trajectory
            engagement_trajectory = self._calculate_engagement_trajectory(
                conversation_history, interaction_data
            )

            # Extract churn risk evolution
            churn_predictions = [p for p in behavioral_predictions
                               if p.get('prediction_type') == 'churn_prediction_temporal']
            churn_risk_evolution = [p.get('score', 0.5) for p in churn_predictions]

            # Get conversion probability trend
            conversion_predictions = [p for p in behavioral_predictions
                                    if p.get('prediction_type') == 'conversion_likelihood_advanced']
            conversion_probability_trend = [p.get('score', 0.5) for p in conversion_predictions]

            # Assess agent relationship quality
            agent_relationship_quality = await self._assess_agent_relationship_quality(
                conversation_history, interaction_data
            )

            return InterventionContext(
                lead_id=lead_id,
                current_behavioral_state=current_behavioral_state,
                historical_patterns=interaction_data,
                vertical_context=vertical_analysis.detected_vertical,
                client_segment=vertical_analysis.client_segment,
                recent_interactions=conversation_history[-10:],
                engagement_trajectory=engagement_trajectory,
                churn_risk_evolution=churn_risk_evolution,
                conversion_probability_trend=conversion_probability_trend,
                external_factors=await self._assess_external_factors(lead_id),
                agent_relationship_quality=agent_relationship_quality,
                previous_interventions=await self._get_previous_interventions(lead_id),
                market_conditions=await self._get_market_conditions(vertical_analysis.detected_vertical)
            )

        except Exception as e:
            logger.error(f"Error building intervention context: {e}")
            raise

    def _analyze_response_pattern(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze response patterns from conversation history"""
        try:
            if not conversation_history:
                return {'average_response_time': 0, 'response_consistency': 0.5}

            # Calculate response times
            response_times = []
            for i in range(1, len(conversation_history)):
                prev_msg = conversation_history[i-1]
                curr_msg = conversation_history[i]

                if prev_msg.get('speaker') != curr_msg.get('speaker'):
                    prev_time = pd.to_datetime(prev_msg.get('timestamp', datetime.now()))
                    curr_time = pd.to_datetime(curr_msg.get('timestamp', datetime.now()))
                    response_time = (curr_time - prev_time).total_seconds() / 3600  # hours
                    response_times.append(response_time)

            avg_response_time = np.mean(response_times) if response_times else 24
            response_consistency = 1.0 - (np.std(response_times) / max(avg_response_time, 1)) if response_times else 0.5

            return {
                'average_response_time': avg_response_time,
                'response_consistency': max(0.0, min(1.0, response_consistency)),
                'total_exchanges': len(response_times),
                'longest_silence': max(response_times) if response_times else 0
            }

        except Exception as e:
            logger.warning(f"Error analyzing response pattern: {e}")
            return {'average_response_time': 24, 'response_consistency': 0.5}

    def _analyze_content_preferences(self, conversation_history: List[Dict]) -> Dict[str, Any]:
        """Analyze content preferences from conversation history"""
        try:
            content_types = {
                'detailed_information': 0,
                'quick_summaries': 0,
                'visual_content': 0,
                'data_driven': 0,
                'emotional_appeal': 0
            }

            for msg in conversation_history:
                content = msg.get('content', '').lower()

                # Detect preferences from response patterns
                if any(word in content for word in ['details', 'explain', 'comprehensive']):
                    content_types['detailed_information'] += 1

                if any(word in content for word in ['quick', 'summary', 'briefly']):
                    content_types['quick_summaries'] += 1

                if any(word in content for word in ['show', 'picture', 'video', 'visual']):
                    content_types['visual_content'] += 1

                if any(word in content for word in ['numbers', 'data', 'statistics', 'analysis']):
                    content_types['data_driven'] += 1

                if any(word in content for word in ['feel', 'excited', 'worried', 'dream']):
                    content_types['emotional_appeal'] += 1

            # Normalize preferences
            total = max(sum(content_types.values()), 1)
            normalized_preferences = {k: v / total for k, v in content_types.items()}

            return normalized_preferences

        except Exception as e:
            logger.warning(f"Error analyzing content preferences: {e}")
            return {'detailed_information': 0.5, 'quick_summaries': 0.3, 'visual_content': 0.2}

    def _detect_communication_style(self, conversation_history: List[Dict]) -> str:
        """Detect preferred communication style"""
        try:
            style_indicators = {
                'formal': ['sir', 'madam', 'please', 'would you', 'could you'],
                'casual': ['hey', 'sure', 'cool', 'awesome', 'great'],
                'business': ['opportunity', 'investment', 'analysis', 'strategy'],
                'personal': ['family', 'home', 'feel', 'comfortable', 'excited']
            }

            style_scores = {style: 0 for style in style_indicators}

            for msg in conversation_history:
                content = msg.get('content', '').lower()
                for style, indicators in style_indicators.items():
                    style_scores[style] += sum(1 for indicator in indicators if indicator in content)

            # Determine dominant style
            if style_scores:
                dominant_style = max(style_scores, key=style_scores.get)
                return dominant_style if style_scores[dominant_style] > 0 else 'professional'

            return 'professional'

        except Exception as e:
            logger.warning(f"Error detecting communication style: {e}")
            return 'professional'

    def _calculate_engagement_trajectory(
        self,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any]
    ) -> List[float]:
        """Calculate engagement trajectory over time"""
        try:
            # Simplified engagement calculation
            trajectory = []

            # Base engagement from interaction data
            base_engagement = interaction_data.get('engagement_score', 0.5)

            # Calculate engagement for each recent interaction
            for i, msg in enumerate(conversation_history[-10:]):
                # Engagement factors
                recency_factor = (i + 1) / 10.0  # More recent = higher weight
                length_factor = min(1.0, len(msg.get('content', '')) / 100.0)

                engagement_score = (base_engagement + length_factor + recency_factor) / 3.0
                trajectory.append(max(0.0, min(1.0, engagement_score)))

            return trajectory if trajectory else [base_engagement]

        except Exception as e:
            logger.warning(f"Error calculating engagement trajectory: {e}")
            return [0.5]

    async def _assess_agent_relationship_quality(
        self,
        conversation_history: List[Dict],
        interaction_data: Dict[str, Any]
    ) -> float:
        """Assess the quality of the agent-client relationship"""
        try:
            quality_factors = []

            # Conversation depth and length
            total_exchanges = len(conversation_history) / 2  # Approximate exchanges
            depth_score = min(1.0, total_exchanges / 10.0)
            quality_factors.append(depth_score)

            # Response rate and consistency
            response_pattern = self._analyze_response_pattern(conversation_history)
            response_score = response_pattern.get('response_consistency', 0.5)
            quality_factors.append(response_score)

            # Content quality (positive sentiment, engagement)
            content_quality = 0.5
            for msg in conversation_history:
                content = msg.get('content', '').lower()
                if any(word in content for word in ['thank', 'appreciate', 'helpful', 'great']):
                    content_quality += 0.1
                elif any(word in content for word in ['confused', 'frustrated', 'disappointed']):
                    content_quality -= 0.1

            content_quality = max(0.0, min(1.0, content_quality))
            quality_factors.append(content_quality)

            # Overall engagement score
            engagement_score = interaction_data.get('engagement_score', 0.5)
            quality_factors.append(engagement_score)

            # Calculate weighted average
            relationship_quality = np.mean(quality_factors)
            return max(0.0, min(1.0, relationship_quality))

        except Exception as e:
            logger.warning(f"Error assessing relationship quality: {e}")
            return 0.5

    async def _assess_external_factors(self, lead_id: str) -> Dict[str, Any]:
        """Assess external factors that might influence intervention timing"""
        try:
            # In production, this would integrate with external data sources
            return {
                'market_conditions': 'stable',
                'seasonal_factors': 'spring_buying_season',
                'interest_rate_environment': 'rising',
                'local_market_activity': 'high',
                'economic_indicators': 'positive',
                'competitive_activity': 'moderate'
            }

        except Exception as e:
            logger.warning(f"Error assessing external factors: {e}")
            return {}

    async def _get_previous_interventions(self, lead_id: str) -> List[Dict]:
        """Get previous intervention history for the lead"""
        try:
            # Filter intervention history for this lead
            previous_interventions = [
                asdict(result) for result in self.intervention_history
                if result.intervention_id.startswith(lead_id)
            ]

            return previous_interventions[-10:]  # Last 10 interventions

        except Exception as e:
            logger.warning(f"Error getting previous interventions: {e}")
            return []

    async def _get_market_conditions(self, vertical: Optional[RealEstateVertical]) -> Dict[str, Any]:
        """Get current market conditions for the vertical"""
        try:
            # In production, this would connect to market data APIs
            market_conditions = {
                'inventory_levels': 'low',
                'buyer_activity': 'high',
                'price_trends': 'increasing',
                'time_on_market': 'decreasing',
                'competition_level': 'high'
            }

            # Adjust for specific verticals
            if vertical == RealEstateVertical.LUXURY_RESIDENTIAL:
                market_conditions.update({
                    'luxury_inventory': 'limited',
                    'international_interest': 'high',
                    'price_appreciation': 'strong'
                })
            elif vertical == RealEstateVertical.COMMERCIAL_REAL_ESTATE:
                market_conditions.update({
                    'cap_rates': 'stable',
                    'occupancy_rates': 'high',
                    'investment_activity': 'strong'
                })

            return market_conditions

        except Exception as e:
            logger.warning(f"Error getting market conditions: {e}")
            return {}

    async def _identify_intervention_triggers(
        self,
        context: InterventionContext
    ) -> List[InterventionTrigger]:
        """Identify active intervention triggers based on context"""
        try:
            active_triggers = []

            # Churn risk spike detection
            if context.churn_risk_evolution:
                recent_churn_risk = context.churn_risk_evolution[-1]
                if recent_churn_risk > 0.7:
                    active_triggers.append(InterventionTrigger.CHURN_RISK_SPIKE)

                # Check for trend increases
                if len(context.churn_risk_evolution) >= 3:
                    trend = np.polyfit(range(3), context.churn_risk_evolution[-3:], 1)[0]
                    if trend > 0.1:  # Increasing churn risk
                        active_triggers.append(InterventionTrigger.CHURN_RISK_SPIKE)

            # Engagement decline detection
            if context.engagement_trajectory:
                recent_engagement = context.engagement_trajectory[-1]
                if recent_engagement < 0.4:
                    active_triggers.append(InterventionTrigger.ENGAGEMENT_DECLINE)

                # Check for declining trend
                if len(context.engagement_trajectory) >= 3:
                    trend = np.polyfit(range(3), context.engagement_trajectory[-3:], 1)[0]
                    if trend < -0.05:  # Declining engagement
                        active_triggers.append(InterventionTrigger.ENGAGEMENT_DECLINE)

            # Response delay detection
            response_pattern = context.current_behavioral_state.get('response_pattern', {})
            avg_response_time = response_pattern.get('average_response_time', 0)
            if avg_response_time > 48:  # More than 2 days
                active_triggers.append(InterventionTrigger.RESPONSE_DELAY)

            # Conversion opportunity detection
            if context.conversion_probability_trend:
                recent_conversion_prob = context.conversion_probability_trend[-1]
                if recent_conversion_prob > 0.7:
                    active_triggers.append(InterventionTrigger.CONVERSION_OPPORTUNITY)

            # Decision moment detection
            # Look for decision-related language in recent conversations
            recent_content = " ".join([
                msg.get('content', '') for msg in context.recent_interactions[-3:]
            ]).lower()

            decision_indicators = ['decide', 'choice', 'option', 'ready', 'move forward', 'next step']
            if any(indicator in recent_content for indicator in decision_indicators):
                active_triggers.append(InterventionTrigger.DECISION_MOMENT)

            # Relationship maintenance (for high-value leads with no recent activity)
            if (context.agent_relationship_quality > 0.7 and
                avg_response_time > 72 and
                len(context.recent_interactions) < 5):
                active_triggers.append(InterventionTrigger.RELATIONSHIP_MAINTENANCE)

            # Remove duplicates
            return list(set(active_triggers))

        except Exception as e:
            logger.error(f"Error identifying intervention triggers: {e}")
            return [InterventionTrigger.RELATIONSHIP_MAINTENANCE]  # Safe default

    async def _generate_strategies_for_trigger(
        self,
        trigger: InterventionTrigger,
        context: InterventionContext
    ) -> List[InterventionStrategy]:
        """Generate intervention strategies for a specific trigger"""
        try:
            # Get base strategies for the trigger
            base_strategies = self.strategy_templates.get(trigger, [])

            if not base_strategies:
                # Generate default strategy
                return [await self._create_default_strategy(trigger, context)]

            # Customize strategies for the context
            customized_strategies = []
            for strategy in base_strategies:
                customized_strategy = await self._customize_strategy_for_context(
                    strategy, context
                )
                customized_strategies.append(customized_strategy)

            return customized_strategies

        except Exception as e:
            logger.error(f"Error generating strategies for trigger {trigger}: {e}")
            return []

    async def _customize_strategy_for_context(
        self,
        base_strategy: InterventionStrategy,
        context: InterventionContext
    ) -> InterventionStrategy:
        """Customize a base strategy for specific context"""
        try:
            # Create a copy of the base strategy
            customized_strategy = InterventionStrategy(
                strategy_id=f"{base_strategy.strategy_id}_{context.lead_id}",
                trigger=base_strategy.trigger,
                urgency=base_strategy.urgency,
                primary_channel=base_strategy.primary_channel,
                fallback_channels=base_strategy.fallback_channels.copy(),

                optimal_timing=await self._calculate_optimal_timing(context),
                timing_flexibility_hours=base_strategy.timing_flexibility_hours,
                follow_up_sequence=base_strategy.follow_up_sequence.copy(),

                message_framework=base_strategy.message_framework.copy(),
                personalization_variables=base_strategy.personalization_variables.copy(),
                call_to_action=base_strategy.call_to_action,
                value_proposition=base_strategy.value_proposition,

                communication_style=await self._adapt_communication_style(base_strategy, context),
                emotional_tone=await self._adapt_emotional_tone(base_strategy, context),
                information_depth=await self._adapt_information_depth(base_strategy, context),
                relationship_approach=base_strategy.relationship_approach,

                success_metrics=base_strategy.success_metrics.copy(),
                escalation_triggers=base_strategy.escalation_triggers.copy(),
                termination_conditions=base_strategy.termination_conditions.copy(),

                expected_response_rate=await self._calculate_expected_response_rate(base_strategy, context),
                predicted_outcome=base_strategy.predicted_outcome,
                confidence_score=await self._calculate_strategy_confidence(base_strategy, context),
                risk_factors=await self._identify_strategy_risks(base_strategy, context)
            )

            # Customize message framework with personalization
            customized_strategy.message_framework = await self._personalize_message_framework(
                customized_strategy.message_framework, context
            )

            return customized_strategy

        except Exception as e:
            logger.error(f"Error customizing strategy: {e}")
            return base_strategy

    async def _calculate_optimal_timing(self, context: InterventionContext) -> datetime:
        """Calculate optimal timing for intervention"""
        try:
            now = datetime.now()

            # Base timing considerations
            optimal_timing = now

            # Consider communication patterns
            response_pattern = context.current_behavioral_state.get('response_pattern', {})
            avg_response_time = response_pattern.get('average_response_time', 24)

            # Adjust for typical response time (don't interrupt their usual pattern)
            if avg_response_time < 4:  # Quick responder
                optimal_timing = now + timedelta(hours=1)
            elif avg_response_time < 24:  # Daily responder
                optimal_timing = now + timedelta(hours=2)
            else:  # Slower responder
                optimal_timing = now + timedelta(hours=4)

            # Consider business hours and preferences
            # Adjust to business hours if outside
            if optimal_timing.hour < 9:
                optimal_timing = optimal_timing.replace(hour=9, minute=0)
            elif optimal_timing.hour > 18:
                optimal_timing = optimal_timing.replace(hour=9, minute=0) + timedelta(days=1)

            # Consider urgency level
            if context.churn_risk_evolution and context.churn_risk_evolution[-1] > 0.8:
                # High churn risk - intervene immediately during business hours
                optimal_timing = min(optimal_timing, now + timedelta(hours=2))

            return optimal_timing

        except Exception as e:
            logger.warning(f"Error calculating optimal timing: {e}")
            return datetime.now() + timedelta(hours=2)

    async def _adapt_communication_style(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> str:
        """Adapt communication style based on context"""
        try:
            detected_style = context.current_behavioral_state.get('communication_style', 'professional')

            # Adapt based on vertical
            if context.vertical_context == RealEstateVertical.LUXURY_RESIDENTIAL:
                return 'exclusive_professional'
            elif context.vertical_context == RealEstateVertical.COMMERCIAL_REAL_ESTATE:
                return 'analytical_professional'
            elif context.vertical_context == RealEstateVertical.NEW_CONSTRUCTION:
                return 'educational_friendly'

            # Adapt based on detected client style
            style_mapping = {
                'formal': 'respectful_formal',
                'casual': 'friendly_approachable',
                'business': 'professional_efficient',
                'personal': 'warm_personal'
            }

            return style_mapping.get(detected_style, strategy.communication_style)

        except Exception as e:
            logger.warning(f"Error adapting communication style: {e}")
            return strategy.communication_style

    async def _adapt_emotional_tone(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> str:
        """Adapt emotional tone based on context"""
        try:
            # Adjust tone based on relationship quality
            if context.agent_relationship_quality > 0.8:
                return 'warm_confident'
            elif context.agent_relationship_quality < 0.4:
                return 'professional_respectful'

            # Adjust based on churn risk
            if context.churn_risk_evolution and context.churn_risk_evolution[-1] > 0.7:
                return 'concerned_supportive'

            return strategy.emotional_tone

        except Exception as e:
            logger.warning(f"Error adapting emotional tone: {e}")
            return strategy.emotional_tone

    async def _adapt_information_depth(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> str:
        """Adapt information depth based on preferences"""
        try:
            content_prefs = context.current_behavioral_state.get('content_preferences', {})

            if content_prefs.get('detailed_information', 0) > 0.5:
                return 'comprehensive_detailed'
            elif content_prefs.get('quick_summaries', 0) > 0.5:
                return 'concise_focused'
            elif content_prefs.get('data_driven', 0) > 0.5:
                return 'analytical_factual'

            return strategy.information_depth

        except Exception as e:
            logger.warning(f"Error adapting information depth: {e}")
            return strategy.information_depth

    async def _calculate_expected_response_rate(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> float:
        """Calculate expected response rate for strategy given context"""
        try:
            base_rate = strategy.expected_response_rate

            # Adjust based on relationship quality
            relationship_adjustment = (context.agent_relationship_quality - 0.5) * 0.2
            adjusted_rate = base_rate + relationship_adjustment

            # Adjust based on recent response patterns
            response_pattern = context.current_behavioral_state.get('response_pattern', {})
            consistency = response_pattern.get('response_consistency', 0.5)
            consistency_adjustment = (consistency - 0.5) * 0.15
            adjusted_rate += consistency_adjustment

            # Adjust based on channel effectiveness (simplified)
            if strategy.primary_channel == InterventionChannel.PERSONAL_CALL:
                adjusted_rate *= 1.1
            elif strategy.primary_channel == InterventionChannel.TEXT_MESSAGE:
                adjusted_rate *= 0.9

            return max(0.1, min(0.95, adjusted_rate))

        except Exception as e:
            logger.warning(f"Error calculating expected response rate: {e}")
            return strategy.expected_response_rate

    async def _calculate_strategy_confidence(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> float:
        """Calculate confidence score for strategy effectiveness"""
        try:
            confidence_factors = []

            # Data quality factor
            data_completeness = min(1.0, len(context.recent_interactions) / 10.0)
            confidence_factors.append(data_completeness)

            # Relationship quality factor
            confidence_factors.append(context.agent_relationship_quality)

            # Context clarity factor
            if context.vertical_context and context.client_segment:
                confidence_factors.append(0.8)
            else:
                confidence_factors.append(0.5)

            # Historical success factor (simplified)
            historical_success = 0.7  # Would be calculated from actual intervention history
            confidence_factors.append(historical_success)

            return np.mean(confidence_factors)

        except Exception as e:
            logger.warning(f"Error calculating strategy confidence: {e}")
            return 0.5

    async def _identify_strategy_risks(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> List[str]:
        """Identify risks for the strategy"""
        try:
            risks = strategy.risk_factors.copy()

            # Add context-specific risks
            if context.agent_relationship_quality < 0.4:
                risks.append("low_relationship_quality")

            if context.churn_risk_evolution and context.churn_risk_evolution[-1] > 0.8:
                risks.append("high_churn_risk")

            response_pattern = context.current_behavioral_state.get('response_pattern', {})
            if response_pattern.get('average_response_time', 0) > 72:
                risks.append("slow_response_pattern")

            # Remove duplicates
            return list(set(risks))

        except Exception as e:
            logger.warning(f"Error identifying strategy risks: {e}")
            return strategy.risk_factors

    async def _personalize_message_framework(
        self,
        message_framework: Dict[str, str],
        context: InterventionContext
    ) -> Dict[str, str]:
        """Personalize message framework with context-specific information"""
        try:
            personalized_framework = message_framework.copy()

            # Add vertical-specific language
            if context.vertical_context == RealEstateVertical.LUXURY_RESIDENTIAL:
                # Enhance with luxury terminology
                for key, message in personalized_framework.items():
                    if 'property' in message:
                        personalized_framework[key] = message.replace('property', 'estate')

            # Add client segment specific messaging
            if context.client_segment == ClientSegment.HIGH_NET_WORTH_INDIVIDUAL:
                for key, message in personalized_framework.items():
                    if key == 'value_proposition':
                        personalized_framework[key] += " tailored to your exclusive requirements"

            return personalized_framework

        except Exception as e:
            logger.warning(f"Error personalizing message framework: {e}")
            return message_framework

    async def _create_default_strategy(
        self,
        trigger: InterventionTrigger,
        context: InterventionContext
    ) -> InterventionStrategy:
        """Create a default strategy when templates aren't available"""
        return InterventionStrategy(
            strategy_id=f"default_{trigger.value}_{context.lead_id}",
            trigger=trigger,
            urgency=InterventionUrgency.MODERATE,
            primary_channel=InterventionChannel.PERSONALIZED_EMAIL,
            fallback_channels=[InterventionChannel.PERSONAL_CALL],

            optimal_timing=datetime.now() + timedelta(hours=4),
            timing_flexibility_hours=12,
            follow_up_sequence=[(InterventionChannel.PERSONAL_CALL, 24)],

            message_framework={
                "opening": "I wanted to reach out and check in with you",
                "value_statement": "Your success in finding the right property is important to me",
                "assistance_offer": "Is there anything I can help clarify or assist with?",
                "next_steps": "I'm here to support you throughout this process"
            },
            personalization_variables={},
            call_to_action="Schedule a brief conversation",
            value_proposition="Continued professional support and guidance",

            communication_style="professional",
            emotional_tone="supportive",
            information_depth="appropriate",
            relationship_approach="professional_service",

            success_metrics={"response_rate": 0.4, "engagement_increase": 0.3},
            escalation_triggers=["no_response_72h"],
            termination_conditions=["client_response", "explicit_request"],

            expected_response_rate=0.4,
            predicted_outcome=InterventionOutcome.PARTIAL_ENGAGEMENT,
            confidence_score=0.6,
            risk_factors=["generic_approach"]
        )

    async def _rank_intervention_strategies(
        self,
        strategies: List[InterventionStrategy],
        context: InterventionContext
    ) -> List[InterventionStrategy]:
        """Rank strategies by predicted effectiveness"""
        try:
            # Calculate effectiveness scores
            scored_strategies = []

            for strategy in strategies:
                effectiveness_score = await self._calculate_strategy_effectiveness(
                    strategy, context
                )
                scored_strategies.append((effectiveness_score, strategy))

            # Sort by effectiveness score (descending)
            scored_strategies.sort(key=lambda x: x[0], reverse=True)

            # Return ranked strategies
            return [strategy for _, strategy in scored_strategies]

        except Exception as e:
            logger.error(f"Error ranking intervention strategies: {e}")
            return strategies

    async def _calculate_strategy_effectiveness(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> float:
        """Calculate overall effectiveness score for a strategy"""
        try:
            effectiveness_factors = []

            # Expected response rate (30% weight)
            response_score = strategy.expected_response_rate
            effectiveness_factors.append((response_score, 0.30))

            # Confidence score (25% weight)
            confidence_score = strategy.confidence_score
            effectiveness_factors.append((confidence_score, 0.25))

            # Urgency alignment (20% weight)
            urgency_score = await self._calculate_urgency_alignment(strategy, context)
            effectiveness_factors.append((urgency_score, 0.20))

            # Channel preference alignment (15% weight)
            channel_score = await self._calculate_channel_alignment(strategy, context)
            effectiveness_factors.append((channel_score, 0.15))

            # Risk mitigation (10% weight)
            risk_score = 1.0 - (len(strategy.risk_factors) * 0.1)
            risk_score = max(0.0, risk_score)
            effectiveness_factors.append((risk_score, 0.10))

            # Calculate weighted average
            weighted_sum = sum(score * weight for score, weight in effectiveness_factors)
            total_weight = sum(weight for _, weight in effectiveness_factors)

            return weighted_sum / total_weight

        except Exception as e:
            logger.warning(f"Error calculating strategy effectiveness: {e}")
            return 0.5

    async def _calculate_urgency_alignment(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> float:
        """Calculate how well strategy urgency aligns with context"""
        try:
            # Assess context urgency needs
            context_urgency = 0.5

            # High churn risk increases urgency needs
            if context.churn_risk_evolution and context.churn_risk_evolution[-1] > 0.7:
                context_urgency += 0.3

            # High conversion probability increases urgency
            if context.conversion_probability_trend and context.conversion_probability_trend[-1] > 0.7:
                context_urgency += 0.2

            # Normalize
            context_urgency = min(1.0, context_urgency)

            # Map strategy urgency to score
            urgency_mapping = {
                InterventionUrgency.IMMEDIATE: 1.0,
                InterventionUrgency.HIGH: 0.8,
                InterventionUrgency.MODERATE: 0.5,
                InterventionUrgency.LOW: 0.2,
                InterventionUrgency.SCHEDULED: 0.3
            }

            strategy_urgency_score = urgency_mapping.get(strategy.urgency, 0.5)

            # Calculate alignment (1.0 - absolute difference)
            alignment = 1.0 - abs(context_urgency - strategy_urgency_score)
            return max(0.0, alignment)

        except Exception as e:
            logger.warning(f"Error calculating urgency alignment: {e}")
            return 0.5

    async def _calculate_channel_alignment(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> float:
        """Calculate how well strategy channel aligns with preferences"""
        try:
            # Infer channel preferences from context
            preferred_channels = await self._infer_channel_preferences(context)

            # Score primary channel
            primary_score = preferred_channels.get(strategy.primary_channel.value, 0.5)

            # Score fallback channels
            fallback_scores = [
                preferred_channels.get(channel.value, 0.3)
                for channel in strategy.fallback_channels
            ]

            # Weighted average (70% primary, 30% best fallback)
            best_fallback = max(fallback_scores) if fallback_scores else 0.3
            channel_score = (primary_score * 0.7) + (best_fallback * 0.3)

            return channel_score

        except Exception as e:
            logger.warning(f"Error calculating channel alignment: {e}")
            return 0.5

    async def _infer_channel_preferences(self, context: InterventionContext) -> Dict[str, float]:
        """Infer channel preferences from context"""
        try:
            # Default preferences
            preferences = {
                'personal_call': 0.6,
                'personalized_email': 0.7,
                'text_message': 0.4,
                'in_person_meeting': 0.5,
                'video_call': 0.5
            }

            # Adjust based on vertical
            if context.vertical_context == RealEstateVertical.LUXURY_RESIDENTIAL:
                preferences.update({
                    'personal_call': 0.8,
                    'in_person_meeting': 0.9,
                    'handwritten_note': 0.7
                })
            elif context.vertical_context == RealEstateVertical.COMMERCIAL_REAL_ESTATE:
                preferences.update({
                    'personalized_email': 0.8,
                    'video_call': 0.7,
                    'personal_call': 0.6
                })

            # Adjust based on client segment
            if context.client_segment == ClientSegment.HIGH_NET_WORTH_INDIVIDUAL:
                preferences['in_person_meeting'] = 0.9
                preferences['personal_call'] = 0.8

            return preferences

        except Exception as e:
            logger.warning(f"Error inferring channel preferences: {e}")
            return {'personalized_email': 0.7, 'personal_call': 0.6}

    async def _optimize_intervention_timing(
        self,
        strategies: List[InterventionStrategy],
        context: InterventionContext
    ) -> List[InterventionStrategy]:
        """Optimize timing for intervention strategies"""
        try:
            optimized_strategies = []

            for strategy in strategies:
                # Refine optimal timing based on additional factors
                optimized_timing = await self._refine_optimal_timing(strategy, context)

                # Create optimized strategy
                optimized_strategy = strategy
                optimized_strategy.optimal_timing = optimized_timing

                optimized_strategies.append(optimized_strategy)

            return optimized_strategies

        except Exception as e:
            logger.error(f"Error optimizing intervention timing: {e}")
            return strategies

    async def _refine_optimal_timing(
        self,
        strategy: InterventionStrategy,
        context: InterventionContext
    ) -> datetime:
        """Refine optimal timing based on additional context"""
        try:
            base_timing = strategy.optimal_timing

            # Consider external factors
            external_factors = context.external_factors

            # Avoid busy market periods for certain verticals
            if context.vertical_context == RealEstateVertical.LUXURY_RESIDENTIAL:
                # Avoid month-end for luxury clients
                if base_timing.day > 25:
                    next_month = base_timing.replace(day=1) + timedelta(days=32)
                    base_timing = next_month.replace(day=2)

            # Consider urgency overrides
            if strategy.urgency == InterventionUrgency.IMMEDIATE:
                # Immediate interventions within business hours
                now = datetime.now()
                if 9 <= now.hour <= 18:
                    return now + timedelta(minutes=30)
                else:
                    return now.replace(hour=9, minute=0) + timedelta(days=1 if now.hour > 18 else 0)

            return base_timing

        except Exception as e:
            logger.warning(f"Error refining optimal timing: {e}")
            return strategy.optimal_timing

    async def get_intervention_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive intervention performance metrics"""
        try:
            total_interventions = len(self.intervention_history)

            if total_interventions == 0:
                return {
                    'total_interventions': 0,
                    'performance_summary': 'No intervention data available'
                }

            # Calculate response rates
            responded_interventions = [
                r for r in self.intervention_history if r.response_received
            ]
            response_rate = len(responded_interventions) / total_interventions

            # Calculate success rates by outcome
            outcome_counts = {}
            for result in self.intervention_history:
                outcome = result.achieved_outcome.value
                outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

            # Calculate average response time
            response_times = [
                r.response_time_hours for r in self.intervention_history
                if r.response_time_hours is not None
            ]
            avg_response_time = np.mean(response_times) if response_times else None

            # Performance by channel
            channel_performance = {}
            for result in self.intervention_history:
                channel = result.channel_used.value
                if channel not in channel_performance:
                    channel_performance[channel] = {'total': 0, 'responded': 0}
                channel_performance[channel]['total'] += 1
                if result.response_received:
                    channel_performance[channel]['responded'] += 1

            # Calculate channel response rates
            for channel_data in channel_performance.values():
                channel_data['response_rate'] = channel_data['responded'] / channel_data['total']

            return {
                'total_interventions': total_interventions,
                'overall_response_rate': response_rate,
                'performance_targets': self.performance_targets,
                'target_achievement': {
                    'response_rate_vs_target': response_rate / self.performance_targets.get('response_rate_improvement', 0.4)
                },
                'outcome_distribution': outcome_counts,
                'average_response_time_hours': avg_response_time,
                'channel_performance': channel_performance,
                'active_interventions': len(self.active_interventions),
                'strategy_templates_available': len(self.strategy_templates),
                'total_triggers_supported': len(InterventionTrigger)
            }

        except Exception as e:
            logger.error(f"Error getting intervention performance metrics: {e}")
            return {"error": str(e)}


# Global instance
predictive_intervention_engine = PredictiveLeadInterventionEngine()


async def get_intervention_engine() -> PredictiveLeadInterventionEngine:
    """Get global predictive intervention engine."""
    return predictive_intervention_engine


# Configuration guide
INTERVENTION_CONFIGURATION_GUIDE = """
Predictive Lead Intervention Strategies Configuration:

Intervention Triggers:
- Churn Risk Spike: Behavioral indicators of disengagement
- Engagement Decline: Decreasing interaction patterns
- Response Delay: Extended silence periods
- Conversion Opportunity: High readiness signals
- Decision Moment: Critical decision timeframes
- Competitive Threat: External competitive pressure

Available Channels:
- Personal Call: High-touch, immediate response
- Personalized Email: Detailed, documented communication
- Text Message: Quick, casual engagement
- In-Person Meeting: Highest impact, relationship building
- Video Call: Face-to-face with convenience
- Direct Mail: Physical, memorable touchpoint

Performance Targets:
- Intervention Timing Accuracy: >90%
- Churn Prevention Rate: >75%
- Conversion Acceleration: +25%
- Response Rate Improvement: +40%

Configuration Features:
- Behavioral trigger detection
- Multi-channel orchestration
- Personalized messaging frameworks
- Timing optimization
- Performance tracking and optimization
- A/B testing for continuous improvement
"""

if __name__ == "__main__":
    print("Predictive Lead Intervention Strategies (Phase 5)")
    print("="*55)
    print(INTERVENTION_CONFIGURATION_GUIDE)