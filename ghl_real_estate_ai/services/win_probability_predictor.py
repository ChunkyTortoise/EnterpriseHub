"""
Win Probability Predictor

ML-powered prediction of offer acceptance probability based on negotiation intelligence,
market factors, and historical outcome patterns.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict

import numpy as np

from ghl_real_estate_ai.api.schemas.negotiation import (
    MarketCondition,
    MarketLeverage,
    NegotiationStrategy,
    NegotiationTactic,
    SellerMotivationType,
    SellerPsychologyProfile,
    WinProbabilityAnalysis,
)
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = logging.getLogger(__name__)


@dataclass
class PredictionFeatures:
    """Feature vector for win probability prediction"""

    # Pricing features
    offer_to_list_ratio: float
    price_per_sqft_variance: float
    days_on_market: int
    price_reduction_count: int
    total_price_reduction_pct: float

    # Psychology features
    urgency_score: float
    flexibility_score: float
    emotional_attachment: float
    financial_pressure: float
    motivation_type_encoded: int

    # Market features
    leverage_score: float
    competitive_pressure: float
    inventory_months: float
    market_condition_encoded: int
    seasonal_advantage: float

    # Buyer features
    financing_strength: float
    cash_offer: bool
    quick_close: bool
    pre_approved: bool

    # Property features
    property_uniqueness: float
    price_positioning_encoded: int
    comparable_sales_strength: float


class WinProbabilityPredictor:
    """
    Predicts offer acceptance probability using rule-based models with plans
    for future ML enhancement. Provides scenario analysis and factor importance.
    """

    def __init__(self):
        self.cache_service = get_cache_service()

        # Model coefficients (will be replaced with trained ML model)
        self.feature_weights = {
            "offer_to_list_ratio": 40.0,
            "urgency_score": 0.25,
            "flexibility_score": 0.20,
            "leverage_score": 0.15,
            "cash_offer_boost": 15.0,
            "quick_close_boost": 8.0,
            "days_on_market_factor": 0.10,
            "competitive_pressure_factor": -0.08,
            "seasonal_advantage": 0.05,
        }

    async def predict_win_probability(
        self,
        property_id: str,
        seller_psychology: SellerPsychologyProfile,
        market_leverage: MarketLeverage,
        negotiation_strategy: NegotiationStrategy,
        property_data: Dict[str, Any],
        buyer_profile: Dict[str, Any],
    ) -> WinProbabilityAnalysis:
        """
        Predict offer acceptance probability with comprehensive analysis.
        """
        cache_key = f"win_probability:{property_id}:v2"
        cached_result = await self.cache_service.get(cache_key)

        if cached_result:
            logger.info(f"Returning cached win probability for {property_id}")
            return WinProbabilityAnalysis.model_validate(cached_result)

        logger.info(f"Predicting win probability for property {property_id}")

        # Extract features for prediction
        features = self._extract_prediction_features(
            seller_psychology, market_leverage, negotiation_strategy, property_data, buyer_profile
        )

        # Calculate base win probability
        base_probability = await self._calculate_base_probability(features)

        # Apply strategy-specific adjustments
        strategy_adjusted_probability = self._apply_strategy_adjustments(
            base_probability, negotiation_strategy, features
        )

        # Generate confidence intervals
        confidence_interval = self._calculate_confidence_interval(strategy_adjusted_probability, features)

        # Analyze contributing factors
        factor_analysis = self._analyze_contributing_factors(features, strategy_adjusted_probability)

        # Generate scenario analysis
        scenarios = await self._generate_scenario_analysis(features, negotiation_strategy)

        # Create optimal offer analysis
        optimal_analysis = await self._analyze_optimal_offer_scenarios(features, negotiation_strategy, property_data)

        win_analysis = WinProbabilityAnalysis(
            win_probability=strategy_adjusted_probability,
            confidence_interval=confidence_interval,
            factor_weights=factor_analysis["weights"],
            risk_factors=factor_analysis["risk_factors"],
            success_drivers=factor_analysis["success_drivers"],
            scenarios=scenarios,
            optimal_offer_analysis=optimal_analysis,
        )

        # Cache result for 30 minutes
        await self.cache_service.set(cache_key, win_analysis.model_dump(), ttl=1800)

        logger.info(f"Win probability prediction complete: {strategy_adjusted_probability:.1f}%")
        return win_analysis

    def _extract_prediction_features(
        self,
        psychology: SellerPsychologyProfile,
        leverage: MarketLeverage,
        strategy: NegotiationStrategy,
        property_data: Dict[str, Any],
        buyer_profile: Dict[str, Any],
    ) -> PredictionFeatures:
        """Extract numerical features for prediction model"""

        list_price = float(property_data.get("list_price", 500000))
        offer_price = float(strategy.recommended_offer_price)

        return PredictionFeatures(
            # Pricing features
            offer_to_list_ratio=offer_price / list_price,
            price_per_sqft_variance=0.0,  # TODO: Calculate from comps
            days_on_market=property_data.get("days_on_market", 30),
            price_reduction_count=property_data.get("price_drops", 0),
            total_price_reduction_pct=property_data.get("total_reduction_pct", 0),
            # Psychology features
            urgency_score=psychology.urgency_score,
            flexibility_score=psychology.flexibility_score,
            emotional_attachment=psychology.emotional_attachment_score,
            financial_pressure=psychology.financial_pressure_score,
            motivation_type_encoded=self._encode_motivation_type(psychology.motivation_type),
            # Market features
            leverage_score=leverage.overall_leverage_score,
            competitive_pressure=leverage.competitive_pressure,
            inventory_months=leverage.inventory_levels.get("target_range", 6),
            market_condition_encoded=self._encode_market_condition(leverage.market_condition),
            seasonal_advantage=leverage.seasonal_advantage,
            # Buyer features
            financing_strength=leverage.financing_strength,
            cash_offer=buyer_profile.get("cash_offer", False),
            quick_close=buyer_profile.get("quick_close", False),
            pre_approved=buyer_profile.get("pre_approved", False),
            # Property features
            property_uniqueness=leverage.property_uniqueness_score,
            price_positioning_encoded=self._encode_price_positioning(leverage.price_positioning),
            comparable_sales_strength=leverage.comparable_sales_strength,
        )

    def _encode_motivation_type(self, motivation: SellerMotivationType) -> int:
        """Encode motivation type as numerical value"""
        encoding = {
            SellerMotivationType.EMOTIONAL: 1,
            SellerMotivationType.FINANCIAL: 2,
            SellerMotivationType.STRATEGIC: 3,
            SellerMotivationType.DISTRESSED: 4,
        }
        return encoding.get(motivation, 1)

    def _encode_market_condition(self, condition: MarketCondition) -> int:
        """Encode market condition as numerical value"""
        encoding = {MarketCondition.BUYERS_MARKET: 1, MarketCondition.BALANCED: 2, MarketCondition.SELLERS_MARKET: 3}
        return encoding.get(condition, 2)

    def _encode_price_positioning(self, positioning: str) -> int:
        """Encode price positioning as numerical value"""
        encoding = {"underpriced": 1, "fairly_priced": 2, "above_market": 3, "overpriced": 4}
        return encoding.get(positioning, 2)

    async def _calculate_base_probability(self, features: PredictionFeatures) -> float:
        """Calculate base win probability using rule-based model"""

        # Start with baseline probability
        base_prob = 50.0

        # Primary factor: Offer ratio
        offer_ratio_impact = self._calculate_offer_ratio_impact(features.offer_to_list_ratio)
        base_prob += offer_ratio_impact

        # Psychology factors
        psychology_impact = self._calculate_psychology_impact(features)
        base_prob += psychology_impact

        # Market factors
        market_impact = self._calculate_market_impact(features)
        base_prob += market_impact

        # Buyer strength factors
        buyer_impact = self._calculate_buyer_impact(features)
        base_prob += buyer_impact

        # Property factors
        property_impact = self._calculate_property_impact(features)
        base_prob += property_impact

        # Time factors
        time_impact = self._calculate_time_impact(features)
        base_prob += time_impact

        return max(5, min(95, base_prob))  # Cap between 5% and 95%

    def _calculate_offer_ratio_impact(self, ratio: float) -> float:
        """Calculate impact of offer-to-list ratio on win probability"""

        # Sigmoid-like function for offer ratio impact
        if ratio >= 1.0:  # At or above asking
            return 35
        elif ratio >= 0.98:  # 98-100% of asking
            return 25
        elif ratio >= 0.95:  # 95-98% of asking
            return 15
        elif ratio >= 0.90:  # 90-95% of asking
            return 0
        elif ratio >= 0.85:  # 85-90% of asking
            return -15
        elif ratio >= 0.80:  # 80-85% of asking
            return -25
        else:  # Below 80% of asking
            return -35

    def _calculate_psychology_impact(self, features: PredictionFeatures) -> float:
        """Calculate impact of seller psychology on win probability"""

        impact = 0.0

        # Urgency impact
        urgency_impact = (features.urgency_score - 50) * 0.3  # Scale urgency
        impact += urgency_impact

        # Flexibility impact
        flexibility_impact = (features.flexibility_score - 50) * 0.25
        impact += flexibility_impact

        # Financial pressure impact
        financial_impact = (features.financial_pressure - 50) * 0.2
        impact += financial_impact

        # Motivation type impact
        motivation_impacts = {1: -5, 2: 5, 3: 0, 4: 10}  # emotional, financial, strategic, distressed
        impact += motivation_impacts.get(features.motivation_type_encoded, 0)

        return impact

    def _calculate_market_impact(self, features: PredictionFeatures) -> float:
        """Calculate impact of market conditions on win probability"""

        impact = 0.0

        # Overall leverage impact
        leverage_impact = (features.leverage_score - 50) * 0.2
        impact += leverage_impact

        # Market condition impact
        market_impacts = {1: 15, 2: 0, 3: -10}  # buyers, balanced, sellers
        impact += market_impacts.get(features.market_condition_encoded, 0)

        # Inventory impact
        if features.inventory_months > 8:
            impact += 10  # High inventory favors buyers
        elif features.inventory_months < 3:
            impact -= 8  # Low inventory favors sellers

        # Competitive pressure impact
        pressure_impact = (features.competitive_pressure - 50) * 0.15
        impact += pressure_impact

        # Seasonal advantage
        impact += features.seasonal_advantage * 0.5

        return impact

    def _calculate_buyer_impact(self, features: PredictionFeatures) -> float:
        """Calculate impact of buyer characteristics on win probability"""

        impact = 0.0

        # Financing strength
        financing_impact = (features.financing_strength - 50) * 0.1
        impact += financing_impact

        # Cash offer boost
        if features.cash_offer:
            impact += 15

        # Quick close boost
        if features.quick_close:
            impact += 8

        # Pre-approval boost
        if features.pre_approved:
            impact += 5

        return impact

    def _calculate_property_impact(self, features: PredictionFeatures) -> float:
        """Calculate impact of property characteristics on win probability"""

        impact = 0.0

        # Property uniqueness (rare properties have less negotiation room)
        if features.property_uniqueness > 80:
            impact -= 8
        elif features.property_uniqueness < 30:
            impact += 5

        # Price positioning
        positioning_impacts = {1: -5, 2: 0, 3: 8, 4: 15}  # under, fair, above, over
        impact += positioning_impacts.get(features.price_positioning_encoded, 0)

        # Comparable sales strength
        if features.comparable_sales_strength > 80:
            impact += 5  # Strong comps support buyer position
        elif features.comparable_sales_strength < 40:
            impact -= 3  # Weak comps weaken buyer position

        return impact

    def _calculate_time_impact(self, features: PredictionFeatures) -> float:
        """Calculate impact of time factors on win probability"""

        impact = 0.0

        # Days on market impact
        if features.days_on_market > 90:
            impact += 12  # Stale listing favors buyers
        elif features.days_on_market > 60:
            impact += 6
        elif features.days_on_market < 10:
            impact -= 8  # Hot listing favors sellers

        # Price reduction impact
        if features.price_reduction_count > 2:
            impact += 8  # Multiple reductions show flexibility
        elif features.price_reduction_count > 0:
            impact += 4

        if features.total_price_reduction_pct > 10:
            impact += 10  # Significant reductions show motivation
        elif features.total_price_reduction_pct > 5:
            impact += 5

        return impact

    def _apply_strategy_adjustments(
        self, base_probability: float, strategy: NegotiationStrategy, features: PredictionFeatures
    ) -> float:
        """Apply negotiation strategy-specific adjustments"""

        adjusted_prob = base_probability
        strategy_impact = 0.0

        # Tactic-specific adjustments
        if strategy.primary_tactic == NegotiationTactic.PRICE_FOCUSED:
            # Price-focused strategy effectiveness depends on market leverage
            if features.leverage_score > 70:
                strategy_impact += 3
            elif features.leverage_score < 30:
                strategy_impact -= 5

        elif strategy.primary_tactic == NegotiationTactic.TIMELINE_FOCUSED:
            # Timeline strategy effectiveness depends on seller urgency
            if features.urgency_score > 70:
                strategy_impact += 8
            elif features.urgency_score < 30:
                strategy_impact -= 3

        elif strategy.primary_tactic == NegotiationTactic.RELATIONSHIP_BUILDING:
            # Relationship strategy effectiveness depends on emotional attachment
            if features.emotional_attachment > 70:
                strategy_impact += 6
            elif features.motivation_type_encoded == 1:  # Emotional seller
                strategy_impact += 4

        elif strategy.primary_tactic == NegotiationTactic.COMPETITIVE_PRESSURE:
            # Competitive strategy effectiveness depends on market conditions
            if features.market_condition_encoded == 1:  # Buyers market
                strategy_impact += 5
            elif features.competitive_pressure > 70:
                strategy_impact += 3

        elif strategy.primary_tactic == NegotiationTactic.TERMS_FOCUSED:
            # Terms strategy provides moderate boost across scenarios
            strategy_impact += 2

        # Strategy confidence adjustment
        confidence_adjustment = (strategy.confidence_score - 50) * 0.05
        strategy_impact += confidence_adjustment

        return max(5, min(95, adjusted_prob + strategy_impact))

    def _calculate_confidence_interval(self, probability: float, features: PredictionFeatures) -> Dict[str, float]:
        """Calculate confidence interval for the prediction"""

        # Base confidence interval width
        base_width = 15.0

        # Adjust width based on data quality and certainty
        if features.comparable_sales_strength > 80:
            base_width -= 3  # Strong data = narrower interval
        elif features.comparable_sales_strength < 40:
            base_width += 5  # Weak data = wider interval

        # Market clarity adjustment
        if features.market_condition_encoded != 2:  # Not balanced market
            base_width -= 2

        # Psychology clarity adjustment
        if features.urgency_score > 80 or features.urgency_score < 20:
            base_width -= 2  # Clear urgency signal

        # Calculate bounds
        half_width = base_width / 2
        lower_bound = max(0, probability - half_width)
        upper_bound = min(100, probability + half_width)

        return {"lower": lower_bound, "upper": upper_bound}

    def _analyze_contributing_factors(self, features: PredictionFeatures, final_probability: float) -> Dict[str, Any]:
        """Analyze which factors contribute most to the prediction"""

        # Calculate individual factor contributions
        factor_contributions = {}

        # Offer ratio contribution
        offer_contribution = self._calculate_offer_ratio_impact(features.offer_to_list_ratio)
        factor_contributions["offer_ratio"] = offer_contribution / 40.0  # Normalize

        # Psychology contribution
        psychology_contribution = self._calculate_psychology_impact(features)
        factor_contributions["seller_psychology"] = psychology_contribution / 20.0

        # Market contribution
        market_contribution = self._calculate_market_impact(features)
        factor_contributions["market_conditions"] = market_contribution / 15.0

        # Buyer contribution
        buyer_contribution = self._calculate_buyer_impact(features)
        factor_contributions["buyer_strength"] = buyer_contribution / 25.0

        # Identify risk factors and success drivers
        risk_factors = []
        success_drivers = []

        if features.offer_to_list_ratio < 0.90:
            risk_factors.append("Low offer price relative to listing")
        if features.competitive_pressure < 30:
            risk_factors.append("Low competitive pressure")
        if features.market_condition_encoded == 3:
            risk_factors.append("Sellers market conditions")
        if features.urgency_score < 30:
            risk_factors.append("Low seller urgency")

        if features.cash_offer:
            success_drivers.append("Cash offer advantage")
        if features.urgency_score > 70:
            success_drivers.append("High seller urgency")
        if features.flexibility_score > 70:
            success_drivers.append("Seller flexibility")
        if features.leverage_score > 70:
            success_drivers.append("Strong market leverage")
        if features.days_on_market > 60:
            success_drivers.append("Extended time on market")

        return {"weights": factor_contributions, "risk_factors": risk_factors, "success_drivers": success_drivers}

    async def _generate_scenario_analysis(
        self, features: PredictionFeatures, strategy: NegotiationStrategy
    ) -> Dict[str, float]:
        """Generate win probability for different offer scenarios"""

        base_offer_ratio = features.offer_to_list_ratio
        scenarios = {}

        # Scenario modifications
        scenario_configs = {
            "current_offer": 0.0,
            "5_percent_higher": 0.05,
            "3_percent_higher": 0.03,
            "2_percent_lower": -0.02,
            "5_percent_lower": -0.05,
            "asking_price": (1.0 - base_offer_ratio),
            "cash_offer_premium": 0.02 if not features.cash_offer else 0.0,
            "quick_close_premium": 0.015 if not features.quick_close else 0.0,
        }

        for scenario_name, ratio_adjustment in scenario_configs.items():
            if scenario_name == "cash_offer_premium" and features.cash_offer:
                continue  # Skip if already cash offer

            # Create modified features
            modified_features = features
            modified_features.offer_to_list_ratio = min(1.05, base_offer_ratio + ratio_adjustment)

            # Special adjustments for specific scenarios
            if scenario_name == "cash_offer_premium":
                modified_features.cash_offer = True
            elif scenario_name == "quick_close_premium":
                modified_features.quick_close = True

            # Calculate probability for this scenario
            scenario_prob = await self._calculate_base_probability(modified_features)
            scenario_prob = self._apply_strategy_adjustments(scenario_prob, strategy, modified_features)

            scenarios[scenario_name] = round(scenario_prob, 1)

        return scenarios

    async def _analyze_optimal_offer_scenarios(
        self, features: PredictionFeatures, strategy: NegotiationStrategy, property_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze optimal offer scenarios and recommendations"""

        list_price = float(property_data.get("list_price", 500000))
        current_offer = float(strategy.recommended_offer_price)

        # Test different offer levels to find optimal probability/price tradeoff
        offer_scenarios = []

        for offer_pct in np.arange(0.85, 1.06, 0.01):  # 85% to 105% in 1% increments
            test_features = features
            test_features.offer_to_list_ratio = offer_pct

            test_prob = await self._calculate_base_probability(test_features)
            test_prob = self._apply_strategy_adjustments(test_prob, strategy, test_features)

            offer_scenarios.append(
                {
                    "offer_percentage": round(offer_pct * 100, 1),
                    "offer_amount": round(list_price * offer_pct),
                    "win_probability": round(test_prob, 1),
                    "value_score": test_prob * offer_pct,  # Weighted value score
                }
            )

        # Find optimal scenarios
        max_probability = max(scenario["win_probability"] for scenario in offer_scenarios)
        optimal_value = max(scenario["value_score"] for scenario in offer_scenarios)

        max_prob_scenario = next(s for s in offer_scenarios if s["win_probability"] == max_probability)
        optimal_value_scenario = next(s for s in offer_scenarios if s["value_score"] == optimal_value)

        # Calculate probability thresholds
        probability_thresholds = {
            "50_percent_chance": next((s for s in offer_scenarios if s["win_probability"] >= 50), None),
            "70_percent_chance": next((s for s in offer_scenarios if s["win_probability"] >= 70), None),
            "80_percent_chance": next((s for s in offer_scenarios if s["win_probability"] >= 80), None),
            "90_percent_chance": next((s for s in offer_scenarios if s["win_probability"] >= 90), None),
        }

        return {
            "max_probability_scenario": max_prob_scenario,
            "optimal_value_scenario": optimal_value_scenario,
            "probability_thresholds": {k: v for k, v in probability_thresholds.items() if v},
            "current_offer_analysis": {
                "offer_percentage": round(features.offer_to_list_ratio * 100, 1),
                "position_vs_optimal": "optimal"
                if abs(features.offer_to_list_ratio - optimal_value_scenario["offer_percentage"] / 100) < 0.01
                else "suboptimal",
            },
        }


# Singleton instance
_win_probability_predictor = None


def get_win_probability_predictor() -> WinProbabilityPredictor:
    """Get singleton instance of WinProbabilityPredictor"""
    global _win_probability_predictor
    if _win_probability_predictor is None:
        _win_probability_predictor = WinProbabilityPredictor()
    return _win_probability_predictor
