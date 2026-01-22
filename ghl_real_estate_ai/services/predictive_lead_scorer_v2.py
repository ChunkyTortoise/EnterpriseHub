"""
Predictive Lead Scorer v2 - Advanced ML-Powered Lead Scoring.

Combines traditional qualification-based scoring with machine learning
predictions of closing probability. Provides multi-dimensional scoring:
- Engagement Score (traditional questions answered)
- Closing Probability (ML-predicted)
- Urgency Score (timeline and behavioral signals)
- Overall Priority Score (composite)
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import numpy as np

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.ml.closing_probability_model import ClosingProbabilityModel, ModelPrediction
from ghl_real_estate_ai.ml.feature_engineering import FeatureEngineer

logger = get_logger(__name__)
cache = get_cache_service()


class LeadPriority(Enum):
    """Lead priority levels for Jorge's workflow optimization."""

    CRITICAL = "critical"      # 90-100% - Immediate action required
    HIGH = "high"             # 75-89% - Contact within 2 hours
    MEDIUM = "medium"         # 50-74% - Contact within 24 hours
    LOW = "low"              # 25-49% - Add to nurture campaign
    COLD = "cold"            # 0-24% - Long-term nurture only


@dataclass
class PredictiveScore:
    """Comprehensive predictive scoring result."""

    # Traditional scoring
    qualification_score: int  # 0-7 questions answered
    qualification_percentage: int  # 0-100%

    # ML-powered predictions
    closing_probability: float  # 0.0-1.0
    closing_confidence_interval: Tuple[float, float]

    # Multi-dimensional analysis
    engagement_score: float  # 0-100
    urgency_score: float    # 0-100
    risk_score: float       # 0-100 (higher = more risk)

    # Composite scoring
    overall_priority_score: float  # 0-100
    priority_level: LeadPriority

    # Insights and reasoning
    risk_factors: List[str]
    positive_signals: List[str]
    recommended_actions: List[str]
    optimal_contact_timing: str
    time_investment_recommendation: str

    # ROI predictions
    estimated_revenue_potential: float
    effort_efficiency_score: float  # Revenue potential / effort required
    
    # Model metadata
    model_confidence: float
    last_updated: datetime

    # ROI predictions (continued)
    net_yield_estimate: Optional[float] = None # For sellers: (Market - (Price+Repairs))/Market
    potential_margin: Optional[float] = None    # For sellers: Estimated dollar profit
    
    # Phase 5: Autonomous Expansion
    has_conflicting_intent: bool = False # Flag for HITL escalation


@dataclass
class LeadInsights:
    """Deep insights for Jorge's decision making."""

    # Behavioral analysis
    response_pattern_analysis: str
    engagement_trend: str  # "increasing", "stable", "declining"
    conversation_quality_score: float

    # Market context
    market_timing_advantage: str
    competitive_pressure_level: str
    inventory_availability_impact: str

    # Action recommendations
    next_best_action: str
    optimal_communication_channel: str
    recommended_follow_up_interval: str
    pricing_strategy_recommendation: str

    # Resource allocation
    estimated_time_to_close: int  # days
    recommended_effort_level: str  # "minimal", "standard", "intensive"
    probability_of_churn: float


class PredictiveLeadScorerV2:
    """
    Advanced predictive lead scoring with ML-powered closing probability.

    Combines Jorge's traditional qualification scoring with machine learning
    predictions to provide comprehensive lead analysis and prioritization.
    """

    def __init__(self):
        """Initialize the predictive lead scorer."""
        self.traditional_scorer = LeadScorer()
        self.ml_model = ClosingProbabilityModel()
        self.feature_engineer = FeatureEngineer()
        self.cache_ttl = 1800  # 30 minutes

        # Scoring weights for composite score
        self.default_weights = {
            "qualification": 0.25,    # Traditional qualification
            "closing_probability": 0.35,  # ML prediction (highest weight)
            "engagement": 0.20,       # Conversation engagement
            "urgency": 0.20          # Timeline urgency
        }
        self.weights = self.default_weights.copy()

        # Priority thresholds aligned with business requirements
        # Score 95+ → CRITICAL, 80-94 → HIGH, 60-79 → MEDIUM, 35-59 → LOW, <35 → COLD
        self.priority_thresholds = {
            LeadPriority.CRITICAL: 95,
            LeadPriority.HIGH: 80,
            LeadPriority.MEDIUM: 60,
            LeadPriority.LOW: 35,
            LeadPriority.COLD: 0
        }

    async def _load_dynamic_weights(self):
        """Phase 7: Load weights adjusted by the retraining loop."""
        dynamic_weights = await cache.get("dynamic_scoring_weights")
        if dynamic_weights:
            self.weights = dynamic_weights
            logger.debug(f"Applied dynamic weights: {self.weights}")

    async def calculate_predictive_score(
        self, conversation_context: List[Dict[str, str]], location: str = "austin"
    ) -> "PredictiveScore":
        """
        Calculate comprehensive predictive score for a lead.

        Args:
            conversation_context: List of message dictionaries or Dict with conversation data
            location: Market location for context

        Returns:
            PredictiveScore object with multi-dimensional analysis
        """
        logger.info("Calculating predictive score v2...")

        # Input validation - handle None or invalid inputs
        if conversation_context is None:
            logger.warning("Received None conversation_context, using empty fallback")
            conversation_context = {
                "conversation_history": [],
                "extracted_preferences": {},
                "created_at": datetime.now().isoformat()
            }

        # Normalize input: if it's a list, wrap it in a dict
        if isinstance(conversation_context, list):
            conversation_context = {
                "conversation_history": conversation_context,
                "extracted_preferences": {},
                "created_at": datetime.now().isoformat()
            }

        # Ensure required keys exist
        if not isinstance(conversation_context, dict):
            logger.warning(f"Invalid conversation_context type: {type(conversation_context)}, using empty fallback")
            conversation_context = {
                "conversation_history": [],
                "extracted_preferences": {},
                "created_at": datetime.now().isoformat()
            }

        # Ensure conversation_history key exists
        if "conversation_history" not in conversation_context:
            conversation_context["conversation_history"] = []
        if "extracted_preferences" not in conversation_context:
            conversation_context["extracted_preferences"] = {}

        # Generate cache key from context hash
        cache_key = f"predictive_score:{hash(str(conversation_context))}:{location}"

        try:
            # Phase 7: Dynamic Weights
            await self._load_dynamic_weights()

            # 1. Traditional qualification scoring
            traditional_result = await self.traditional_scorer.calculate_with_reasoning(conversation_context)
            qualification_score = traditional_result["score"]
            qualification_percentage = self.traditional_scorer.get_percentage_score(qualification_score)

            # 2. ML-powered closing probability
            ml_prediction: ModelPrediction = await self.ml_model.predict_closing_probability(
                conversation_context, location
            )

            # 3. Extract conversation features for detailed analysis
            conv_features = await self.feature_engineer.extract_conversation_features(conversation_context)
            market_features = await self.feature_engineer.extract_market_features(location)

            # 4. Calculate engagement score
            engagement_score = await self._calculate_engagement_score(conv_features)

            # 5. Calculate urgency score
            urgency_score = await self._calculate_urgency_score(conv_features, conversation_context)

            # 6. Calculate risk score
            risk_score = await self._calculate_risk_score(conv_features, ml_prediction)

            # 7. Calculate composite priority score
            overall_priority_score = self._calculate_composite_score(
                qualification_percentage,
                ml_prediction.closing_probability * 100,
                engagement_score,
                urgency_score
            )

            # 8. Determine priority level
            priority_level = self._determine_priority_level(overall_priority_score)

            # 9. Generate recommendations
            recommended_actions = await self._generate_advanced_recommendations(
                priority_level, ml_prediction, conv_features, traditional_result
            )

            # 10. ROI analysis
            estimated_revenue, effort_efficiency, net_yield, potential_margin = await self._calculate_roi_predictions(
                ml_prediction.closing_probability, conv_features, conversation_context
            )

            # 11. Optimal timing analysis
            optimal_timing = await self._analyze_optimal_contact_timing(conv_features, urgency_score)
            time_investment = await self._recommend_time_investment(
                ml_prediction.closing_probability, effort_efficiency
            )
            
            # 12. Phase 5: Conflicting Intent Detection
            has_conflicting_intent = self._detect_conflicting_intent(conversation_context, urgency_score)

            score = PredictiveScore(
                # Traditional scoring
                qualification_score=qualification_score,
                qualification_percentage=qualification_percentage,

                # ML predictions
                closing_probability=ml_prediction.closing_probability,
                closing_confidence_interval=ml_prediction.confidence_interval,

                # Multi-dimensional scores
                engagement_score=engagement_score,
                urgency_score=urgency_score,
                risk_score=risk_score,

                # Composite scoring
                overall_priority_score=overall_priority_score,
                priority_level=priority_level,

                # Insights
                risk_factors=ml_prediction.risk_factors,
                positive_signals=ml_prediction.positive_signals,
                recommended_actions=recommended_actions,
                optimal_contact_timing=optimal_timing,
                time_investment_recommendation=time_investment,

                # ROI predictions
                estimated_revenue_potential=estimated_revenue,
                effort_efficiency_score=effort_efficiency,
                net_yield_estimate=net_yield,
                potential_margin=potential_margin,

                # Model metadata
                model_confidence=ml_prediction.model_confidence,
                last_updated=datetime.now(),
                
                # Phase 5
                has_conflicting_intent=has_conflicting_intent
            )

            # Cache for 30 minutes
            await cache.set(cache_key, score, self.cache_ttl)
            return score

        except Exception as e:
            logger.error(f"Error calculating predictive score: {e}")
            # Fallback to traditional scoring
            return await self._fallback_scoring(conversation_context)

    async def generate_lead_insights(
        self,
        conversation_context: Dict[str, Any],
        location: Optional[str] = None
    ) -> LeadInsights:
        """
        Generate deep insights for Jorge's decision making.

        Args:
            conversation_context: Full conversation context
            location: Target location

        Returns:
            LeadInsights with comprehensive analysis
        """
        cache_key = f"lead_insights:{hash(str(conversation_context))}"
        cached = await cache.get(cache_key)
        if cached:
            return cached

        try:
            # Get predictive score first
            score = await self.calculate_predictive_score(conversation_context, location)
            conv_features = await self.feature_engineer.extract_conversation_features(conversation_context)
            market_features = await self.feature_engineer.extract_market_features(location)

            # Behavioral analysis
            response_pattern = await self._analyze_response_patterns(conv_features)
            engagement_trend = await self._analyze_engagement_trend(conversation_context)
            conversation_quality = await self._calculate_conversation_quality(conv_features)

            # Market context analysis
            market_timing = await self._analyze_market_timing(market_features)
            competitive_pressure = await self._analyze_competitive_pressure(market_features, conv_features)
            inventory_impact = await self._analyze_inventory_impact(market_features, conversation_context)

            # Advanced action recommendations
            next_best_action = await self._recommend_next_best_action(score, conv_features)
            optimal_channel = await self._recommend_communication_channel(conv_features, score)
            follow_up_interval = await self._recommend_follow_up_interval(score, conv_features)
            pricing_strategy = await self._recommend_pricing_strategy(market_features, conversation_context)

            # Resource allocation
            time_to_close = await self._estimate_time_to_close(score.closing_probability, conv_features)
            effort_level = await self._recommend_effort_level(score.overall_priority_score, score.effort_efficiency_score)
            churn_probability = await self._calculate_churn_probability(conv_features, score)

            insights = LeadInsights(
                # Behavioral analysis
                response_pattern_analysis=response_pattern,
                engagement_trend=engagement_trend,
                conversation_quality_score=conversation_quality,

                # Market context
                market_timing_advantage=market_timing,
                competitive_pressure_level=competitive_pressure,
                inventory_availability_impact=inventory_impact,

                # Action recommendations
                next_best_action=next_best_action,
                optimal_communication_channel=optimal_channel,
                recommended_follow_up_interval=follow_up_interval,
                pricing_strategy_recommendation=pricing_strategy,

                # Resource allocation
                estimated_time_to_close=time_to_close,
                recommended_effort_level=effort_level,
                probability_of_churn=churn_probability
            )

            await cache.set(cache_key, insights, self.cache_ttl)
            return insights

        except Exception as e:
            logger.error(f"Error generating lead insights: {e}")
            return await self._default_insights()

    async def _calculate_engagement_score(self, conv_features) -> float:
        """Calculate engagement score from conversation features."""
        # Combine multiple engagement indicators
        base_engagement = conv_features.engagement_score * 100

        # Boost for high message count
        if conv_features.message_count > 10:
            base_engagement += 10
        elif conv_features.message_count > 20:
            base_engagement += 20

        # Boost for question asking
        if conv_features.question_asking_frequency > 0.5:
            base_engagement += 15

        # Boost for location specificity
        if conv_features.location_specificity > 0.7:
            base_engagement += 10

        # Cap at 100
        return min(base_engagement, 100.0)

    async def _calculate_urgency_score(self, conv_features, context) -> float:
        """Calculate urgency score from conversation and context."""
        base_urgency = conv_features.urgency_score * 100

        # Handle both dict and list context types
        if isinstance(context, list):
            # If context is a list of messages, wrap it
            context = {"conversation_history": context, "extracted_preferences": {}}
        elif not isinstance(context, dict):
            context = {"conversation_history": [], "extracted_preferences": {}}

        # Check timeline from preferences
        prefs = context.get("extracted_preferences", {})
        if prefs is None:
            prefs = {}
        timeline = prefs.get("timeline", "")

        if timeline:
            timeline_lower = timeline.lower()
            if any(word in timeline_lower for word in ["asap", "immediately", "urgent", "this week", "this month"]):
                base_urgency += 30
            elif any(word in timeline_lower for word in ["next month", "soon", "quickly"]):
                base_urgency += 20
            elif any(word in timeline_lower for word in ["3 months", "spring", "summer"]):
                base_urgency += 10

        # Boost for urgency signals in conversation
        base_urgency += conv_features.timeline_urgency_signals * 10

        return min(base_urgency, 100.0)

    async def _calculate_risk_score(self, conv_features, ml_prediction) -> float:
        """Calculate risk score (higher = more risky lead)."""
        risk_score = 0.0

        # Low qualification completeness
        if conv_features.qualification_completeness < 0.5:
            risk_score += 30

        # Poor budget alignment
        if conv_features.budget_to_market_ratio and conv_features.budget_to_market_ratio < 0.7:
            risk_score += 25

        # Low engagement
        if conv_features.engagement_score < 0.3:
            risk_score += 20

        # Negative sentiment
        if conv_features.overall_sentiment < -0.2:
            risk_score += 15

        # Long response times
        if conv_features.avg_response_time > 1800:  # 30 minutes
            risk_score += 10

        # ML model identified risks
        if len(ml_prediction.risk_factors) > 2:
            risk_score += 15

        return min(risk_score, 100.0)

    def _calculate_composite_score(
        self,
        qualification_pct: float,
        closing_probability_pct: float,
        engagement_score: float,
        urgency_score: float
    ) -> float:
        """Calculate weighted composite priority score."""
        composite = (
            qualification_pct * self.weights["qualification"] +
            closing_probability_pct * self.weights["closing_probability"] +
            engagement_score * self.weights["engagement"] +
            urgency_score * self.weights["urgency"]
        )

        return min(composite, 100.0)

    def _determine_priority_level(self, score: float) -> LeadPriority:
        """Determine priority level from composite score."""
        for priority, threshold in self.priority_thresholds.items():
            if score >= threshold:
                return priority
        return LeadPriority.COLD

    async def _generate_advanced_recommendations(
        self,
        priority: LeadPriority,
        ml_prediction: ModelPrediction,
        conv_features,
        traditional_result: Dict
    ) -> List[str]:
        """Generate advanced action recommendations."""
        actions = []

        if priority == LeadPriority.CRITICAL:
            actions.extend([
                "🚨 IMMEDIATE ACTION: Contact within 1 hour",
                "📞 Call directly - don't rely on text/email",
                "🎯 Prepare property showing options",
                "💰 Ready pre-approval documentation",
                "🏠 Schedule showing within 24-48 hours"
            ])
        elif priority == LeadPriority.HIGH:
            actions.extend([
                "⏰ High priority: Contact within 2 hours",
                "📲 SMS first, follow with call",
                "🏡 Send targeted property recommendations",
                "📋 Complete qualification questionnaire",
                "📅 Schedule consultation this week"
            ])
        elif priority == LeadPriority.MEDIUM:
            actions.extend([
                "📞 Contact within 24 hours",
                "📧 Send market update and new listings",
                "❓ Gather missing qualification details",
                "📊 Provide market analysis for their area"
            ])
        else:
            actions.extend([
                "📮 Add to nurture email campaign",
                "📚 Send educational real estate content",
                "📅 Schedule follow-up in 7-14 days",
                "🎯 Continue qualification process gradually"
            ])

        # Add ML-specific recommendations
        if ml_prediction.risk_factors:
            actions.append(f"⚠️ Address risk factors: {', '.join(ml_prediction.risk_factors[:2])}")

        if conv_features.qualification_completeness < 0.7:
            missing_count = int((1 - conv_features.qualification_completeness) * 7)
            actions.append(f"📝 Complete {missing_count} remaining qualification questions")

        return actions

    def _detect_conflicting_intent(self, context: Dict, urgency_score: float) -> bool:
        """
        Phase 5: Detects if a lead has conflicting motivations (e.g., urgent but high price).
        Used for HITL escalation.
        """
        seller_prefs = context.get("seller_preferences", {})
        if not seller_prefs:
            return False
            
        # Example 1: Urgent timeline but demanding firm top-dollar price
        is_urgent = urgency_score > 70 or seller_prefs.get("timeline_urgency") == "urgent"
        is_firm_on_price = seller_prefs.get("price_flexibility") == "firm"
        
        # In a real system, we'd compare price_expectation to market ARV
        # For now, if both are high, flag as conflicting
        if is_urgent and is_firm_on_price:
            return True
            
        # Example 2: Major repairs needed but expects move-in ready price
        condition = seller_prefs.get("property_condition")
        if condition in ["major repairs", "poor"] and is_firm_on_price:
            return True
            
        return False

    async def _calculate_roi_predictions(
        self,
        closing_probability: float,
        conv_features,
        context: Dict
    ) -> Tuple[float, float, Optional[float], Optional[float]]:
        """Calculate ROI predictions for Jorge's time investment."""

        # Estimate commission based on budget/market data
        prefs = context.get("extracted_preferences", {})
        seller_prefs = context.get("seller_preferences", {})
        
        # Determine if this is a seller deal
        is_seller = bool(seller_prefs)
        
        budget = prefs.get("budget")
        price_expectation = seller_prefs.get("price_expectation")
        repair_estimate = seller_prefs.get("repair_estimate", 0)

        try:
            if is_seller and price_expectation:
                # Use price expectation for sellers
                estimated_value = float(price_expectation)
            elif isinstance(budget, str):
                # Extract numeric value
                import re
                budget_str = re.sub(r'[^\d.]', '', budget)
                if 'k' in budget.lower():
                    estimated_value = float(budget_str) * 1000
                elif 'm' in budget.lower():
                    estimated_value = float(budget_str) * 1000000
                else:
                    estimated_value = float(budget_str)
            else:
                estimated_value = float(budget) if budget else 650000  # Default market value

        except (ValueError, TypeError):
            estimated_value = 650000  # Default market value

        # Assume 3% commission for standard deals
        potential_commission = estimated_value * 0.03

        # Calculate expected revenue
        expected_revenue = potential_commission * closing_probability
        
        # Calculate Seller-Specific Net Yield & Margin (Jorge System 3.0 Enterprise)
        net_yield = None
        potential_margin = None
        
        if is_seller and price_expectation:
            try:
                # PHASE 7: FINANCIAL PRECISION
                # Use data-driven valuation via NationalMarketIntelligence
                from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence
                market_intel = get_national_market_intelligence()
                
                # Fetch refined ARV (Market Valuation)
                location_str = seller_prefs.get("property_address") or context.get("location_id") or "national"
                price_val = float(price_expectation)
                
                # Use the new precise tool
                arv = await market_intel.get_market_valuation(location_str, price_val)
                
                repair_cost = float(repair_estimate) if repair_estimate else 0
                
                # Transactional Costs (Jorge System 3.0 Standard)
                acquisition_closing = float(price_expectation) * 0.03
                selling_costs = arv * 0.06
                holding_costs = arv * 0.008 * 6 # 6 months holding
                
                potential_margin = arv - float(price_expectation) - repair_cost - acquisition_closing - selling_costs - holding_costs
                net_yield = potential_margin / arv if arv > 0 else 0
                
                # Revenue Potential: 30% weighting for commission, 70% for investment profit
                expected_revenue = (expected_revenue * 0.3) + (potential_margin * closing_probability * 0.7)
            except (ValueError, TypeError):
                pass

        # Estimate effort required based on lead characteristics
        base_effort = 10  # Base hours for any lead

        # Add effort for qualification gaps
        if conv_features.qualification_completeness < 0.8:
            base_effort += 5

        # Add effort for low engagement
        if conv_features.engagement_score < 0.5:
            base_effort += 3

        # Reduce effort for highly qualified leads
        if conv_features.qualification_completeness > 0.9:
            base_effort -= 2

        # Efficiency score: revenue per hour of effort
        effort_efficiency = expected_revenue / max(base_effort, 1)

        return expected_revenue, effort_efficiency, net_yield, potential_margin

    async def _analyze_optimal_contact_timing(self, conv_features, urgency_score: float) -> str:
        """Analyze optimal timing for next contact."""

        if urgency_score > 80:
            return "Within 1 hour - extremely time sensitive"
        elif urgency_score > 60:
            return "Within 2-4 hours during business hours"
        elif urgency_score > 40:
            return "Within 24 hours, prefer morning contact"
        elif conv_features.weekend_activity:
            return "Weekend contact OK, prefer Saturday morning"
        elif conv_features.late_night_activity:
            return "Evening contact OK after 6 PM"
        else:
            return "Business hours, Tuesday-Thursday optimal"

    async def _recommend_time_investment(self, closing_probability: float, effort_efficiency: float) -> str:
        """Recommend how much time Jorge should invest."""

        if closing_probability > 0.8 and effort_efficiency > 500:
            return "Maximum investment - top priority lead"
        elif closing_probability > 0.6 and effort_efficiency > 300:
            return "High investment - allocate significant time"
        elif closing_probability > 0.4:
            return "Moderate investment - standard follow-up process"
        elif closing_probability > 0.2:
            return "Minimal investment - automated nurture with periodic check-ins"
        else:
            return "Very minimal investment - long-term nurture only"

    async def _fallback_scoring(self, context: Dict) -> PredictiveScore:
        """Fallback scoring when ML model fails."""
        try:
            # Handle None or invalid context
            if context is None:
                context = {"conversation_history": [], "extracted_preferences": {}}

            # Handle list input (normalize to dict)
            if isinstance(context, list):
                context = {"conversation_history": context, "extracted_preferences": {}}
            elif not isinstance(context, dict):
                context = {"conversation_history": [], "extracted_preferences": {}}

            # Ensure required keys exist
            if "conversation_history" not in context:
                context["conversation_history"] = []

            traditional_result = await self.traditional_scorer.calculate_with_reasoning(context)
            score = traditional_result.get("score", 0)
            percentage = self.traditional_scorer.get_percentage_score(score)
            recommended_actions = traditional_result.get("recommended_actions", ["Continue qualification process"])

        except Exception as e:
            logger.warning(f"Fallback scoring error in traditional scorer: {e}")
            score = 0
            percentage = 0
            recommended_actions = ["Continue qualification process"]

        return PredictiveScore(
            qualification_score=score,
            qualification_percentage=percentage,
            closing_probability=max(0.0, percentage / 100.0 * 0.8),  # Conservative estimate
            closing_confidence_interval=(0.0, 0.8),
            engagement_score=float(percentage),
            urgency_score=50.0,
            risk_score=50.0,
            overall_priority_score=float(percentage),
            priority_level=self._determine_priority_level(float(percentage)),
            risk_factors=["ML model unavailable"],
            positive_signals=[f"Traditional score: {score}/7 questions"],
            recommended_actions=recommended_actions,
            optimal_contact_timing="Within 24 hours",
            time_investment_recommendation="Standard process",
            estimated_revenue_potential=15000.0,  # Average commission
            effort_efficiency_score=300.0,
            model_confidence=0.5,
            last_updated=datetime.now()
        )

    # Additional helper methods for insights generation
    async def _analyze_response_patterns(self, conv_features) -> str:
        """Analyze response patterns."""
        if conv_features.response_consistency > 0.8:
            return "Highly consistent response pattern - engaged and focused"
        elif conv_features.response_consistency > 0.6:
            return "Moderately consistent - some variation in engagement"
        else:
            return "Inconsistent response pattern - may indicate distraction or uncertainty"

    async def _analyze_engagement_trend(self, context: Dict) -> str:
        """Analyze engagement trend over time."""
        messages = context.get("conversation_history", [])
        if len(messages) < 5:
            return "stable"

        # Simple analysis - in production would track actual engagement metrics over time
        recent_engagement = sum(1 for msg in messages[-3:] if len(msg.get("text", "")) > 20)
        early_engagement = sum(1 for msg in messages[:3] if len(msg.get("text", "")) > 20)

        if recent_engagement > early_engagement:
            return "increasing"
        elif recent_engagement < early_engagement:
            return "declining"
        else:
            return "stable"

    async def _calculate_conversation_quality(self, conv_features) -> float:
        """Calculate overall conversation quality score."""
        quality = (
            conv_features.engagement_score * 0.3 +
            conv_features.qualification_completeness * 0.4 +
            (conv_features.overall_sentiment + 1) / 2 * 0.2 +
            min(conv_features.question_asking_frequency, 1.0) * 0.1
        ) * 100

        return min(quality, 100.0)

    # Market analysis methods
    async def _analyze_market_timing(self, market_features) -> str:
        """Analyze market timing advantage."""
        if market_features.seasonal_factor > 0.8:
            return "Excellent timing - peak market season"
        elif market_features.seasonal_factor > 0.6:
            return "Good timing - favorable market conditions"
        elif market_features.seasonal_factor > 0.4:
            return "Neutral timing - standard market conditions"
        else:
            return "Challenging timing - slower market season"

    async def _analyze_competitive_pressure(self, market_features, conv_features) -> str:
        """Analyze competitive pressure level."""
        base_competition = market_features.competition_level

        if conv_features.urgency_score > 0.7 and base_competition > 0.7:
            return "Very high - urgent timeline in competitive market"
        elif base_competition > 0.7:
            return "High - competitive market conditions"
        elif base_competition > 0.4:
            return "Moderate - balanced market competition"
        else:
            return "Low - favorable competitive position"

    async def _analyze_inventory_impact(self, market_features, context: Dict) -> str:
        """Analyze inventory availability impact."""
        if market_features.inventory_level < 0.3:
            return "Low inventory - limited options, act quickly"
        elif market_features.inventory_level < 0.6:
            return "Moderate inventory - good selection available"
        else:
            return "High inventory - extensive options, buyer's market"

    # Action recommendation methods
    async def _recommend_next_best_action(self, score: PredictiveScore, conv_features) -> str:
        """Recommend next best action."""
        if score.priority_level == LeadPriority.CRITICAL:
            if conv_features.qualification_completeness < 0.8:
                return "Complete qualification questions before showing properties"
            else:
                return "Schedule property showing immediately"
        elif score.closing_probability > 0.6:
            return "Focus on building trust and addressing concerns"
        elif conv_features.budget_confidence < 0.5:
            return "Clarify budget and financing options"
        else:
            return "Continue relationship building and education"

    async def _recommend_communication_channel(self, conv_features, score: PredictiveScore) -> str:
        """Recommend optimal communication channel."""
        if score.urgency_score > 70:
            return "Phone call - immediate verbal communication needed"
        elif conv_features.engagement_score > 70:
            return "SMS - maintains high engagement level"
        elif score.priority_level == LeadPriority.HIGH:
            return "Video call - build stronger personal connection"
        else:
            return "Email - appropriate for nurturing and information sharing"

    async def _recommend_follow_up_interval(self, score: PredictiveScore, conv_features) -> str:
        """Recommend follow-up interval."""
        if score.priority_level == LeadPriority.CRITICAL:
            return "Every 6-12 hours until showing scheduled"
        elif score.priority_level == LeadPriority.HIGH:
            return "Every 2-3 days with value-added content"
        elif score.closing_probability > 0.4:
            return "Weekly check-ins with market updates"
        else:
            return "Bi-weekly nurture emails"

    async def _recommend_pricing_strategy(self, market_features, context: Dict) -> str:
        """Recommend pricing strategy."""
        prefs = context.get("extracted_preferences", {})

        if market_features.price_trend > 0.1:  # Rising market
            return "Act quickly - prices rising, consider offers near asking"
        elif market_features.inventory_level > 0.7:  # High inventory
            return "Negotiate aggressively - buyer's market conditions"
        elif prefs.get("budget") and "k" in str(prefs.get("budget", "")).lower():
            return "Focus on value - emphasize long-term investment potential"
        else:
            return "Standard pricing approach - market-competitive offers"

    # Resource allocation methods
    async def _estimate_time_to_close(self, closing_probability: float, conv_features) -> int:
        """Estimate time to close in days."""
        base_time = 45  # Average days to close

        # Adjust based on closing probability
        if closing_probability > 0.8:
            base_time -= 15
        elif closing_probability > 0.6:
            base_time -= 7
        elif closing_probability < 0.3:
            base_time += 30

        # Adjust based on urgency
        if conv_features.urgency_score > 0.8:
            base_time -= 10
        elif conv_features.urgency_score < 0.3:
            base_time += 20

        # Adjust based on qualification completeness
        if conv_features.qualification_completeness > 0.8:
            base_time -= 5
        elif conv_features.qualification_completeness < 0.5:
            base_time += 15

        return max(base_time, 7)  # Minimum 1 week

    async def _recommend_effort_level(self, priority_score: float, efficiency_score: float) -> str:
        """Recommend effort level for Jorge."""
        if priority_score > 85 and efficiency_score > 500:
            return "intensive"
        elif priority_score > 65 or efficiency_score > 300:
            return "standard"
        else:
            return "minimal"

    async def _calculate_churn_probability(self, conv_features, score: PredictiveScore) -> float:
        """Calculate probability of lead churning."""
        churn_prob = 0.0

        # Base churn rate
        churn_prob += 0.2

        # Reduce for high engagement
        if conv_features.engagement_score > 0.7:
            churn_prob -= 0.1
        elif conv_features.engagement_score < 0.3:
            churn_prob += 0.2

        # Reduce for completed qualification
        churn_prob -= conv_features.qualification_completeness * 0.2

        # Adjust for response consistency
        if conv_features.response_consistency < 0.5:
            churn_prob += 0.15

        # Adjust for urgency
        if conv_features.urgency_score > 0.7:
            churn_prob -= 0.1
        elif conv_features.urgency_score < 0.3:
            churn_prob += 0.1

        return max(0.0, min(1.0, churn_prob))

    async def _default_insights(self) -> LeadInsights:
        """Default insights when analysis fails."""
        return LeadInsights(
            response_pattern_analysis="Analysis unavailable",
            engagement_trend="stable",
            conversation_quality_score=50.0,
            market_timing_advantage="Standard market conditions",
            competitive_pressure_level="Moderate",
            inventory_availability_impact="Normal inventory levels",
            next_best_action="Continue standard follow-up process",
            optimal_communication_channel="Email",
            recommended_follow_up_interval="Weekly",
            pricing_strategy_recommendation="Market-competitive approach",
            estimated_time_to_close=45,
            recommended_effort_level="standard",
            probability_of_churn=0.3
        )