"""
Jorge's Client Behavior Analyzer - Advanced Client Psychology Prediction
Provides deep client behavior analysis and purchase timing prediction

This module provides:
- Client purchase probability and timing prediction
- Behavioral pattern analysis and negotiation style profiling
- Lifetime value and referral potential assessment
- Optimal engagement timing and approach strategy
- Jorge's confrontational methodology fit analysis
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from ...ghl_utils.jorge_config import JorgeConfig
from ...services.cache_service import CacheService
from ...services.claude_assistant import ClaudeAssistant

logger = logging.getLogger(__name__)


class ClientPersonalityType(Enum):
    """Client personality classifications for Jorge's methodology"""

    ANALYTICAL_DECIDER = "analytical_decider"  # Data-driven, methodical
    EMOTIONAL_BUYER = "emotional_buyer"  # Heart-based decisions
    AGGRESSIVE_NEGOTIATOR = "aggressive_negotiator"  # Confrontational style
    COLLABORATIVE_PARTNER = "collaborative_partner"  # Relationship-focused
    PRICE_FOCUSED = "price_focused"  # Cost-conscious primary
    STATUS_SEEKER = "status_seeker"  # Prestige-motivated
    PRACTICAL_INVESTOR = "practical_investor"  # ROI-focused decisions


class PurchaseReadinessStage(Enum):
    """Stages of purchase readiness"""

    EXPLORATION = "exploration"  # Just looking, not serious
    CONSIDERATION = "consideration"  # Actively considering options
    EVALUATION = "evaluation"  # Comparing specific properties
    NEGOTIATION = "negotiation"  # Ready to make offers
    COMMITMENT = "commitment"  # Serious about closing
    POST_DECISION = "post_decision"  # Already committed


class EngagementTiming(Enum):
    """Optimal engagement timing classifications"""

    IMMEDIATE = "immediate"  # Contact within hours
    URGENT = "urgent"  # Contact within 24 hours
    PROMPT = "prompt"  # Contact within 3 days
    SCHEDULED = "scheduled"  # Contact on specific date
    PATIENT = "patient"  # Wait for client to re-engage


@dataclass
class ClientPsychProfile:
    """Comprehensive client psychological profile"""

    client_id: str
    personality_type: ClientPersonalityType
    decision_making_style: str
    risk_tolerance: str  # 'high', 'moderate', 'low'
    communication_preference: str  # 'direct', 'collaborative', 'consultative'
    pressure_sensitivity: float  # 0-100, higher = more sensitive
    authority_level: str  # 'sole_decision', 'joint_decision', 'influencer'
    emotional_triggers: List[str]
    logical_triggers: List[str]
    stress_indicators: List[str]


@dataclass
class BehavioralPatterns:
    """Client behavioral pattern analysis"""

    client_id: str
    response_time_avg: float  # Average response time in hours
    engagement_frequency: str  # 'high', 'moderate', 'low'
    question_patterns: List[str]
    objection_patterns: List[str]
    decision_velocity: str  # 'fast', 'moderate', 'slow'
    information_consumption: str  # 'high', 'moderate', 'minimal'
    meeting_preferences: Dict[str, Any]
    communication_channels: List[str]


@dataclass
class FinancialProfile:
    """Client financial readiness assessment"""

    client_id: str
    financial_readiness_score: float  # 0-100
    pre_approval_status: str
    budget_range: Dict[str, Decimal]
    budget_flexibility: float  # 0-100
    financing_confidence: str  # 'strong', 'moderate', 'uncertain'
    down_payment_readiness: str
    debt_to_income_estimate: float
    credit_confidence: str


@dataclass
class PurchasePrediction:
    """Purchase timing and probability prediction"""

    client_id: str
    purchase_probability: float  # 0-100
    predicted_timeframe: PurchaseReadinessStage
    predicted_purchase_date: Optional[datetime]
    confidence_level: float
    accelerating_factors: List[str]
    delaying_factors: List[str]
    conversion_triggers: List[str]
    optimal_follow_up_schedule: List[Dict[str, Any]]


@dataclass
class ClientValueAssessment:
    """Client lifetime value and referral assessment"""

    client_id: str
    lifetime_value_prediction: Decimal
    referral_potential_score: int  # 0-10
    repeat_business_probability: float
    network_influence_score: int  # 0-10
    social_media_reach: str
    professional_connections: str
    geographic_influence: str
    testimonial_potential: str


class ClientBehaviorAnalyzer:
    """
    Advanced Client Behavior Analyzer for Jorge's Crystal Ball Technology
    Provides deep client psychology insights and behavior predictions
    """

    def __init__(self):
        self.config = JorgeConfig()
        self.claude = ClaudeAssistant()
        self.cache = CacheService()

        # Client analysis configurations
        self.analysis_config = {
            "prediction_accuracy_target": 0.90,
            "behavioral_data_lookback": 90,  # days
            "confidence_threshold": 0.70,
            "update_frequency": 1800,  # 30 minutes
            "psychology_factors": [
                "communication_patterns",
                "decision_timing",
                "objection_handling",
                "engagement_level",
                "information_seeking",
            ],
        }

        # Jorge's client methodology
        self.jorge_client_methodology = {
            "confrontational_fit_factors": [
                "pressure_tolerance",
                "direct_communication_preference",
                "results_orientation",
                "time_consciousness",
                "value_recognition",
            ],
            "qualification_thresholds": {
                "financial_readiness": 75,
                "psychological_commitment": 70,
                "urgency_level": 60,
                "jorge_methodology_fit": 65,
            },
            "engagement_optimization": {
                "high_probability_clients": "immediate_personal_attention",
                "moderate_probability_clients": "specialized_bot_nurture",
                "low_probability_clients": "automated_drip_campaign",
            },
        }

        # Client behavior cache and tracking
        self.client_cache = {}
        self.prediction_accuracy = {}
        self.behavioral_model_performance = {}

    async def analyze_client_psychology(
        self, client_id: str, interaction_history: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None
    ) -> ClientPsychProfile:
        """
        Analyze client psychology and personality for optimal approach
        """
        try:
            logger.info(f"Analyzing client psychology for: {client_id}")

            # Check cache first
            cache_key = f"client_psychology_{client_id}_{datetime.now().strftime('%Y%m%d')}"
            cached_profile = await self.cache.get(cache_key)
            if cached_profile:
                return ClientPsychProfile(**cached_profile)

            # Analyze interaction patterns for psychology insights
            psychology_data = await self._analyze_interaction_psychology(client_id, interaction_history, context)

            # Generate psychological profile using Jorge's methodology
            psychology_prompt = f"""
            Analyze client psychology using Jorge's confrontational methodology and behavioral science.

            Client ID: {client_id}
            Interaction History: {interaction_history}
            Psychology Data: {psychology_data}
            Context: {context}

            Jorge's Client Psychology Framework:
            1. Personality Type Classification - How does this client make decisions?
            2. Communication Style Analysis - Direct vs collaborative preferences
            3. Pressure Tolerance Assessment - Can they handle Jorge's approach?
            4. Authority Level Determination - Who makes the final decisions?
            5. Motivation Trigger Identification - What drives their actions?
            6. Stress Response Pattern - How do they react under pressure?

            Analyze comprehensive client psychology including:
            1. Primary personality type classification
            2. Decision-making style and risk tolerance
            3. Communication preferences and pressure sensitivity
            4. Authority level and decision-making structure
            5. Emotional and logical triggers
            6. Stress indicators and management strategies

            Provide specific insights for Jorge's confrontational methodology application.
            """

            psychology_response = await self.claude.generate_response(psychology_prompt)

            # Create psychological profile
            profile = ClientPsychProfile(
                client_id=client_id,
                personality_type=ClientPersonalityType(
                    psychology_response.get("personality_type", "analytical_decider")
                ),
                decision_making_style=psychology_response.get("decision_making_style", "analytical"),
                risk_tolerance=psychology_response.get("risk_tolerance", "moderate"),
                communication_preference=psychology_response.get("communication_preference", "direct"),
                pressure_sensitivity=psychology_response.get("pressure_sensitivity", 50.0),
                authority_level=psychology_response.get("authority_level", "joint_decision"),
                emotional_triggers=psychology_response.get("emotional_triggers", []),
                logical_triggers=psychology_response.get("logical_triggers", []),
                stress_indicators=psychology_response.get("stress_indicators", []),
            )

            # Cache profile
            await self.cache.set(cache_key, profile.__dict__, ttl=86400)  # 24 hours

            logger.info(f"Client psychology analysis completed - Type: {profile.personality_type.value}")
            return profile

        except Exception as e:
            logger.error(f"Client psychology analysis failed: {str(e)}")
            raise

    async def predict_purchase_behavior(
        self, client_id: str, current_engagement_level: str, market_context: Optional[Dict[str, Any]] = None
    ) -> PurchasePrediction:
        """
        Predict client purchase timing and probability
        """
        try:
            logger.info(f"Predicting purchase behavior for: {client_id}")

            # Check cache
            cache_key = (
                f"purchase_prediction_{client_id}_{current_engagement_level}_{datetime.now().strftime('%Y%m%d_%H')}"
            )
            cached_prediction = await self.cache.get(cache_key)
            if cached_prediction:
                return PurchasePrediction(**cached_prediction)

            # Gather behavioral prediction data
            behavioral_data = await self._gather_behavioral_prediction_data(
                client_id, current_engagement_level, market_context
            )

            # Generate purchase behavior prediction
            prediction_prompt = f"""
            Predict purchase behavior using Jorge's proven client analysis methodology.

            Client ID: {client_id}
            Current Engagement: {current_engagement_level}
            Market Context: {market_context}
            Behavioral Data: {behavioral_data}

            Jorge's Purchase Prediction Framework:
            1. Financial Readiness Assessment - Can they buy now?
            2. Psychological Commitment Analysis - Will they buy now?
            3. Urgency Factor Evaluation - What's driving their timeline?
            4. Market Timing Influence - How do market conditions affect them?
            5. Competitive Pressure Analysis - Are other agents involved?
            6. Decision Trigger Identification - What will push them to act?

            Predict comprehensive purchase behavior including:
            1. Purchase probability and confidence level
            2. Predicted timeframe and specific date if possible
            3. Accelerating factors that could speed up decision
            4. Delaying factors that could slow down decision
            5. Conversion triggers that would prompt immediate action
            6. Optimal follow-up schedule for Jorge's methodology

            Format with specific recommendations for Jorge's approach timing.
            """

            prediction_response = await self.claude.generate_response(prediction_prompt)

            # Create purchase prediction
            prediction = PurchasePrediction(
                client_id=client_id,
                purchase_probability=prediction_response.get("purchase_probability", 50.0),
                predicted_timeframe=PurchaseReadinessStage(
                    prediction_response.get("predicted_timeframe", "consideration")
                ),
                predicted_purchase_date=datetime.now() + timedelta(days=prediction_response.get("predicted_days", 30))
                if prediction_response.get("predicted_days")
                else None,
                confidence_level=prediction_response.get("confidence_level", 0.75),
                accelerating_factors=prediction_response.get("accelerating_factors", []),
                delaying_factors=prediction_response.get("delaying_factors", []),
                conversion_triggers=prediction_response.get("conversion_triggers", []),
                optimal_follow_up_schedule=prediction_response.get("optimal_follow_up_schedule", []),
            )

            # Cache prediction
            await self.cache.set(cache_key, prediction.__dict__, ttl=3600)

            logger.info(f"Purchase behavior prediction completed - Probability: {prediction.purchase_probability}%")
            return prediction

        except Exception as e:
            logger.error(f"Purchase behavior prediction failed: {str(e)}")
            raise

    async def assess_behavioral_patterns(self, client_id: str, interaction_window: int = 30) -> BehavioralPatterns:
        """
        Assess client behavioral patterns from interaction history
        """
        try:
            logger.info(f"Assessing behavioral patterns for: {client_id}")

            # Check cache
            cache_key = f"behavioral_patterns_{client_id}_{interaction_window}"
            cached_patterns = await self.cache.get(cache_key)
            if cached_patterns:
                return BehavioralPatterns(**cached_patterns)

            # Gather behavioral pattern data
            pattern_data = await self._gather_behavioral_pattern_data(client_id, interaction_window)

            # Analyze behavioral patterns
            patterns_prompt = f"""
            Analyze behavioral patterns using Jorge's client intelligence methodology.

            Client ID: {client_id}
            Interaction Window: {interaction_window} days
            Pattern Data: {pattern_data}

            Jorge's Behavioral Pattern Analysis:
            1. Response Time Patterns - How quickly do they respond?
            2. Engagement Frequency - How often do they initiate contact?
            3. Question Pattern Analysis - What do they consistently ask?
            4. Objection Pattern Recognition - What concerns do they raise?
            5. Decision Velocity Assessment - How fast do they make decisions?
            6. Information Consumption Style - How much data do they need?

            Analyze comprehensive behavioral patterns including:
            1. Average response times and communication frequency
            2. Common question themes and objection patterns
            3. Decision-making speed and information requirements
            4. Meeting preferences and communication channels
            5. Engagement consistency and reliability patterns
            6. Behavioral change indicators and trend analysis

            Provide insights for optimizing Jorge's engagement strategy.
            """

            patterns_response = await self.claude.generate_response(patterns_prompt)

            # Create behavioral patterns assessment
            patterns = BehavioralPatterns(
                client_id=client_id,
                response_time_avg=patterns_response.get("response_time_avg", 24.0),
                engagement_frequency=patterns_response.get("engagement_frequency", "moderate"),
                question_patterns=patterns_response.get("question_patterns", []),
                objection_patterns=patterns_response.get("objection_patterns", []),
                decision_velocity=patterns_response.get("decision_velocity", "moderate"),
                information_consumption=patterns_response.get("information_consumption", "moderate"),
                meeting_preferences=patterns_response.get("meeting_preferences", {}),
                communication_channels=patterns_response.get("communication_channels", ["phone", "email"]),
            )

            # Cache patterns
            await self.cache.set(cache_key, patterns.__dict__, ttl=7200)

            logger.info(f"Behavioral patterns assessment completed - Decision velocity: {patterns.decision_velocity}")
            return patterns

        except Exception as e:
            logger.error(f"Behavioral patterns assessment failed: {str(e)}")
            raise

    async def evaluate_financial_readiness(
        self, client_id: str, financial_data: Optional[Dict[str, Any]] = None
    ) -> FinancialProfile:
        """
        Evaluate client financial readiness for purchase
        """
        try:
            logger.info(f"Evaluating financial readiness for: {client_id}")

            # Check cache
            cache_key = f"financial_readiness_{client_id}_{datetime.now().strftime('%Y%m%d')}"
            cached_profile = await self.cache.get(cache_key)
            if cached_profile:
                return FinancialProfile(**cached_profile)

            # Analyze financial readiness indicators
            financial_analysis_data = await self._analyze_financial_indicators(client_id, financial_data)

            # Generate financial readiness assessment
            financial_prompt = f"""
            Evaluate financial readiness using Jorge's proven financial qualification methodology.

            Client ID: {client_id}
            Financial Data: {financial_data}
            Analysis Data: {financial_analysis_data}

            Jorge's Financial Readiness Framework:
            1. Pre-Approval Status Verification - Are they actually approved?
            2. Budget Range Assessment - What can they realistically afford?
            3. Down Payment Readiness - Do they have cash available?
            4. Debt-to-Income Analysis - Will they qualify for financing?
            5. Budget Flexibility Evaluation - Can they go higher if needed?
            6. Financial Confidence Level - How certain are they about their finances?

            Evaluate comprehensive financial readiness including:
            1. Financial readiness score (0-100)
            2. Pre-approval status and verification
            3. Realistic budget range and flexibility
            4. Down payment and financing confidence
            5. Debt-to-income considerations
            6. Financial risk factors and opportunities

            Provide specific guidance for Jorge's financial qualification approach.
            """

            financial_response = await self.claude.generate_response(financial_prompt)

            # Create financial profile
            profile = FinancialProfile(
                client_id=client_id,
                financial_readiness_score=financial_response.get("financial_readiness_score", 50.0),
                pre_approval_status=financial_response.get("pre_approval_status", "unknown"),
                budget_range={
                    "min": Decimal(str(financial_response.get("budget_range", {}).get("min", 200000))),
                    "max": Decimal(str(financial_response.get("budget_range", {}).get("max", 500000))),
                    "target": Decimal(str(financial_response.get("budget_range", {}).get("target", 350000))),
                },
                budget_flexibility=financial_response.get("budget_flexibility", 20.0),
                financing_confidence=financial_response.get("financing_confidence", "moderate"),
                down_payment_readiness=financial_response.get("down_payment_readiness", "adequate"),
                debt_to_income_estimate=financial_response.get("debt_to_income_estimate", 0.28),
                credit_confidence=financial_response.get("credit_confidence", "good"),
            )

            # Cache profile
            await self.cache.set(cache_key, profile.__dict__, ttl=86400)

            logger.info(f"Financial readiness evaluation completed - Score: {profile.financial_readiness_score}")
            return profile

        except Exception as e:
            logger.error(f"Financial readiness evaluation failed: {str(e)}")
            raise

    async def predict_client_value(
        self,
        client_id: str,
        behavioral_profile: Optional[BehavioralPatterns] = None,
        financial_profile: Optional[FinancialProfile] = None,
    ) -> ClientValueAssessment:
        """
        Predict client lifetime value and referral potential
        """
        try:
            logger.info(f"Predicting client value for: {client_id}")

            # Check cache
            cache_key = f"client_value_{client_id}_{datetime.now().strftime('%Y%m%d')}"
            cached_assessment = await self.cache.get(cache_key)
            if cached_assessment:
                return ClientValueAssessment(**cached_assessment)

            # Gather value prediction data
            value_data = await self._gather_client_value_data(client_id, behavioral_profile, financial_profile)

            # Generate client value prediction
            value_prompt = f"""
            Predict client lifetime value using Jorge's proven value assessment methodology.

            Client ID: {client_id}
            Behavioral Profile: {behavioral_profile.__dict__ if behavioral_profile else {}}
            Financial Profile: {financial_profile.__dict__ if financial_profile else {}}
            Value Data: {value_data}

            Jorge's Client Value Framework:
            1. Immediate Transaction Value - Current deal potential
            2. Repeat Business Probability - Future transaction likelihood
            3. Referral Network Analysis - Who will they refer to Jorge?
            4. Network Influence Assessment - How much influence do they have?
            5. Geographic Reach Evaluation - Where can they refer Jorge?
            6. Testimonial and Marketing Value - How will they promote Jorge?

            Predict comprehensive client value including:
            1. Lifetime value prediction with confidence intervals
            2. Referral potential score and network analysis
            3. Repeat business probability and timing
            4. Network influence and social media reach
            5. Professional connections and geographic influence
            6. Testimonial potential and marketing value

            Provide specific strategies for maximizing client value with Jorge's methodology.
            """

            value_response = await self.claude.generate_response(value_prompt)

            # Create client value assessment
            assessment = ClientValueAssessment(
                client_id=client_id,
                lifetime_value_prediction=Decimal(str(value_response.get("lifetime_value_prediction", 50000))),
                referral_potential_score=value_response.get("referral_potential_score", 5),
                repeat_business_probability=value_response.get("repeat_business_probability", 30.0),
                network_influence_score=value_response.get("network_influence_score", 5),
                social_media_reach=value_response.get("social_media_reach", "moderate"),
                professional_connections=value_response.get("professional_connections", "moderate"),
                geographic_influence=value_response.get("geographic_influence", "local"),
                testimonial_potential=value_response.get("testimonial_potential", "good"),
            )

            # Cache assessment
            await self.cache.set(cache_key, assessment.__dict__, ttl=86400)

            logger.info(f"Client value prediction completed - Lifetime value: ${assessment.lifetime_value_prediction}")
            return assessment

        except Exception as e:
            logger.error(f"Client value prediction failed: {str(e)}")
            raise

    async def determine_optimal_engagement_strategy(
        self, client_id: str, psychology_profile: ClientPsychProfile, purchase_prediction: PurchasePrediction
    ) -> Dict[str, Any]:
        """
        Determine optimal engagement strategy based on client analysis
        """
        try:
            logger.info(f"Determining optimal engagement strategy for: {client_id}")

            # Calculate Jorge methodology fit score
            jorge_fit_score = await self._calculate_jorge_methodology_fit(psychology_profile, purchase_prediction)

            # Determine engagement timing
            engagement_timing = await self._determine_engagement_timing(purchase_prediction)

            # Create optimal engagement strategy
            strategy = {
                "client_id": client_id,
                "jorge_methodology_fit_score": jorge_fit_score,
                "recommended_approach": await self._recommend_approach_strategy(psychology_profile, jorge_fit_score),
                "engagement_timing": engagement_timing,
                "communication_strategy": await self._determine_communication_strategy(psychology_profile),
                "pressure_application_timing": await self._determine_pressure_timing(
                    psychology_profile, purchase_prediction
                ),
                "follow_up_schedule": purchase_prediction.optimal_follow_up_schedule,
                "success_probability": await self._calculate_success_probability(
                    psychology_profile, purchase_prediction, jorge_fit_score
                ),
                "risk_mitigation": await self._identify_engagement_risks(psychology_profile),
                "value_maximization": await self._identify_value_opportunities(psychology_profile, purchase_prediction),
            }

            logger.info(f"Optimal engagement strategy determined - Jorge fit: {jorge_fit_score}")
            return strategy

        except Exception as e:
            logger.error(f"Engagement strategy determination failed: {str(e)}")
            raise

    # Helper methods for data gathering and analysis
    async def _analyze_interaction_psychology(
        self, client_id: str, interaction_history: List[Dict[str, Any]], context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze interaction patterns for psychological insights"""
        # Implement psychology analysis logic
        return {
            "communication_patterns": {},
            "response_timing": {},
            "question_themes": [],
            "objection_patterns": [],
            "engagement_consistency": {},
            "stress_indicators": [],
        }

    async def _gather_behavioral_prediction_data(
        self, client_id: str, engagement_level: str, market_context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Gather data for behavioral prediction"""
        # Implement behavioral prediction data gathering
        return {
            "client_id": client_id,
            "current_engagement": engagement_level,
            "interaction_history": {},
            "financial_indicators": {},
            "market_context": market_context or {},
            "timing_patterns": {},
            "decision_indicators": {},
        }

    async def _gather_behavioral_pattern_data(self, client_id: str, interaction_window: int) -> Dict[str, Any]:
        """Gather behavioral pattern data"""
        # Implement behavioral pattern data gathering
        return {
            "client_id": client_id,
            "interaction_window": interaction_window,
            "response_times": [],
            "engagement_frequency": {},
            "communication_preferences": {},
            "decision_patterns": {},
        }

    async def _analyze_financial_indicators(
        self, client_id: str, financial_data: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze financial readiness indicators"""
        # Implement financial analysis logic
        return {
            "client_id": client_id,
            "financial_data": financial_data or {},
            "pre_approval_indicators": {},
            "budget_signals": {},
            "financing_readiness": {},
            "financial_behavior_patterns": {},
        }

    async def _gather_client_value_data(
        self,
        client_id: str,
        behavioral_profile: Optional[BehavioralPatterns],
        financial_profile: Optional[FinancialProfile],
    ) -> Dict[str, Any]:
        """Gather client value prediction data"""
        # Implement value data gathering
        return {
            "client_id": client_id,
            "behavioral_profile": behavioral_profile.__dict__ if behavioral_profile else {},
            "financial_profile": financial_profile.__dict__ if financial_profile else {},
            "network_data": {},
            "referral_history": {},
            "social_influence": {},
        }

    async def _calculate_jorge_methodology_fit(
        self, psychology_profile: ClientPsychProfile, purchase_prediction: PurchasePrediction
    ) -> float:
        """Calculate how well client fits Jorge's methodology"""
        # Implement Jorge methodology fit calculation
        fit_factors = {
            "pressure_tolerance": 100 - psychology_profile.pressure_sensitivity,
            "direct_communication": 80 if psychology_profile.communication_preference == "direct" else 40,
            "decision_velocity": 80 if purchase_prediction.predicted_timeframe in ["negotiation", "commitment"] else 50,
            "results_orientation": 70,  # Default assumption
        }
        return sum(fit_factors.values()) / len(fit_factors)

    async def _determine_engagement_timing(self, purchase_prediction: PurchasePrediction) -> EngagementTiming:
        """Determine optimal engagement timing"""
        if purchase_prediction.purchase_probability >= 80:
            return EngagementTiming.IMMEDIATE
        elif purchase_prediction.purchase_probability >= 60:
            return EngagementTiming.URGENT
        elif purchase_prediction.purchase_probability >= 40:
            return EngagementTiming.PROMPT
        else:
            return EngagementTiming.PATIENT

    async def _recommend_approach_strategy(self, psychology_profile: ClientPsychProfile, jorge_fit_score: float) -> str:
        """Recommend approach strategy based on client profile"""
        if jorge_fit_score >= 75:
            return "full_confrontational_methodology"
        elif jorge_fit_score >= 50:
            return "moderate_pressure_with_relationship_building"
        else:
            return "collaborative_consultative_approach"

    async def _determine_communication_strategy(self, psychology_profile: ClientPsychProfile) -> Dict[str, Any]:
        """Determine optimal communication strategy"""
        return {
            "primary_style": psychology_profile.communication_preference,
            "pressure_level": "high" if psychology_profile.pressure_sensitivity < 30 else "moderate",
            "information_depth": "detailed"
            if psychology_profile.personality_type == ClientPersonalityType.ANALYTICAL_DECIDER
            else "summary",
            "frequency": "high"
            if psychology_profile.personality_type == ClientPersonalityType.EMOTIONAL_BUYER
            else "moderate",
        }

    async def _determine_pressure_timing(
        self, psychology_profile: ClientPsychProfile, purchase_prediction: PurchasePrediction
    ) -> List[str]:
        """Determine optimal timing for pressure application"""
        pressure_timing = []

        if psychology_profile.pressure_sensitivity < 40:
            pressure_timing.extend(["initial_contact", "objection_handling"])

        if purchase_prediction.purchase_probability >= 70:
            pressure_timing.append("closing_acceleration")

        if psychology_profile.personality_type == ClientPersonalityType.AGGRESSIVE_NEGOTIATOR:
            pressure_timing.append("negotiation_leverage")

        return pressure_timing

    async def _calculate_success_probability(
        self, psychology_profile: ClientPsychProfile, purchase_prediction: PurchasePrediction, jorge_fit_score: float
    ) -> float:
        """Calculate overall success probability with Jorge's methodology"""
        base_probability = purchase_prediction.purchase_probability
        jorge_multiplier = jorge_fit_score / 100
        methodology_bonus = 10 if jorge_fit_score >= 70 else 0

        success_probability = (base_probability * jorge_multiplier) + methodology_bonus
        return min(95.0, max(5.0, success_probability))  # Cap between 5-95%

    async def _identify_engagement_risks(self, psychology_profile: ClientPsychProfile) -> List[str]:
        """Identify potential risks in client engagement"""
        risks = []

        if psychology_profile.pressure_sensitivity > 70:
            risks.append("High pressure sensitivity - risk of client withdrawal")

        if psychology_profile.personality_type == ClientPersonalityType.COLLABORATIVE_PARTNER:
            risks.append("Collaborative preference - may resist confrontational approach")

        if psychology_profile.authority_level != "sole_decision":
            risks.append("Joint decision making - need to engage multiple stakeholders")

        return risks

    async def _identify_value_opportunities(
        self, psychology_profile: ClientPsychProfile, purchase_prediction: PurchasePrediction
    ) -> List[str]:
        """Identify value maximization opportunities"""
        opportunities = []

        if psychology_profile.personality_type == ClientPersonalityType.STATUS_SEEKER:
            opportunities.append("Leverage premium positioning for higher-value properties")

        if purchase_prediction.purchase_probability >= 80:
            opportunities.append("High closing probability - opportunity for premium commission")

        if psychology_profile.decision_making_style == "fast":
            opportunities.append("Fast decision maker - compress sales cycle for efficiency")

        return opportunities

    async def cleanup(self):
        """Clean up client behavior analyzer resources"""
        try:
            # Save behavioral model performance
            await self._save_behavioral_model_performance()

            logger.info("Client Behavior Analyzer cleanup completed")

        except Exception as e:
            logger.error(f"Client behavior analyzer cleanup failed: {str(e)}")

    async def _save_behavioral_model_performance(self):
        """Save behavioral model performance data"""
        # Implement model performance saving logic
        pass
