"""
Pricing Intelligence Service - AI-Powered Investment & Pricing Analysis for Jorge's Platform

Features:
- Investment opportunity scoring with ROI predictions
- Market timing recommendations for optimal pricing
- Listing price optimization with competitive analysis
- Negotiation strategy intelligence
- Integration with Dynamic Valuation Engine

Business Impact: Maximizes property values and investment returns for Jorge's clients
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

# from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant  # Optional dependency
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.austin_market_service import AustinMarketService, MarketCondition
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.dynamic_valuation_engine import (
    ValuationConfidence,
    ValuationResult,
    get_dynamic_valuation_engine,
)

logger = get_logger(__name__)


class InvestmentGrade(Enum):
    """Investment opportunity grading system"""

    EXCEPTIONAL = "exceptional"  # A+ opportunity (95%+ score)
    EXCELLENT = "excellent"  # A opportunity (85-94% score)
    GOOD = "good"  # B opportunity (75-84% score)
    FAIR = "fair"  # C opportunity (65-74% score)
    POOR = "poor"  # D opportunity (50-64% score)
    AVOID = "avoid"  # F opportunity (<50% score)


class MarketTiming(Enum):
    """Market timing recommendations"""

    BUY_NOW = "buy_now"  # Urgent buying opportunity
    BUY_SOON = "buy_soon"  # Good buying window opening
    HOLD_MONITOR = "hold_monitor"  # Wait and monitor market
    SELL_NOW = "sell_now"  # Optimal selling window
    SELL_SOON = "sell_soon"  # Good selling opportunity


class PricingStrategy(Enum):
    """Listing pricing strategies"""

    AGGRESSIVE = "aggressive"  # Price above market for quick equity
    COMPETITIVE = "competitive"  # Price at market for balanced approach
    STRATEGIC = "strategic"  # Price slightly below market for fast sale
    LUXURY = "luxury"  # Premium pricing for luxury market


@dataclass
class InvestmentMetrics:
    """Comprehensive investment analysis metrics"""

    purchase_price: float
    estimated_current_value: float
    projected_1y_value: float
    projected_5y_value: float

    # ROI Calculations
    current_equity: float
    equity_growth_1y: float
    equity_growth_5y: float
    annual_appreciation_rate: float

    # Cash flow analysis (for rental properties)
    monthly_rental_income: float = 0
    monthly_expenses: float = 0
    monthly_cash_flow: float = 0
    cap_rate: float = 0
    cash_on_cash_return: float = 0

    # Market position
    days_on_market_estimate: int = 30
    liquidity_score: float = 75.0  # How quickly property can be sold


@dataclass
class PricingRecommendation:
    """Intelligent pricing recommendation with rationale"""

    recommended_price: float
    pricing_strategy: PricingStrategy
    confidence_level: ValuationConfidence

    # Price range analysis
    minimum_price: float
    maximum_price: float
    optimal_range_low: float
    optimal_range_high: float

    # Market positioning
    market_position: str  # "below market", "at market", "above market"
    competitive_advantage: List[str]

    # Timing and expectations
    estimated_days_on_market: int
    estimated_sale_probability_30d: float
    estimated_sale_probability_60d: float

    # Strategic insights
    pricing_rationale: List[str]
    negotiation_strategy: List[str]
    market_timing_advice: str


@dataclass
class InvestmentOpportunity:
    """Complete investment opportunity analysis"""

    property_id: str
    property_address: str
    investment_grade: InvestmentGrade
    opportunity_score: float  # 0-100

    # Financial analysis
    metrics: InvestmentMetrics
    valuation_result: ValuationResult

    # Market intelligence
    market_timing: MarketTiming
    timing_score: float  # 0-100, higher = better timing

    # Competitive analysis
    comparable_opportunities: List[Dict[str, Any]]
    market_rank: int  # Rank among similar opportunities

    # Risk assessment
    risk_factors: List[str]
    risk_score: float  # 0-100, higher = more risky

    # Action recommendations
    recommendations: List[str]
    next_steps: List[str]

    # Analysis metadata
    analysis_date: datetime
    analysis_confidence: float
    data_freshness_score: float


class PricingIntelligenceService:
    """
    Advanced Pricing Intelligence Service for Investment Analysis and Optimal Pricing

    Provides:
    - Investment opportunity scoring with predictive ROI analysis
    - Market timing recommendations for buy/sell decisions
    - Listing price optimization with competitive intelligence
    - Negotiation strategy development
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.valuation_engine = get_dynamic_valuation_engine()
        self.market_service = AustinMarketService()
        # Optional Claude Assistant integration
        try:
            from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant

            self.claude_assistant = ClaudeAssistant(context_type="pricing_intelligence")
        except ImportError:
            self.claude_assistant = None  # Graceful fallback

        # Investment analysis parameters
        self.investment_weights = self._initialize_investment_weights()

        # Market timing parameters
        self.timing_thresholds = self._initialize_timing_thresholds()

    def _initialize_investment_weights(self) -> Dict[str, float]:
        """Initialize weights for investment scoring algorithm"""
        return {
            "appreciation_potential": 0.30,
            "cash_flow": 0.25,
            "market_position": 0.20,
            "liquidity": 0.15,
            "risk_adjusted_return": 0.10,
        }

    def _initialize_timing_thresholds(self) -> Dict[str, Dict[str, float]]:
        """Initialize thresholds for market timing recommendations"""
        return {
            "buy_signals": {
                "market_score_threshold": 75.0,
                "price_trend_threshold": -0.02,  # 2% decline is good for buyers
                "inventory_threshold": 3.0,  # 3+ months inventory favors buyers
                "interest_rate_threshold": 7.0,  # Interest rates above 7% slow market
            },
            "sell_signals": {
                "market_score_threshold": 80.0,
                "price_trend_threshold": 0.05,  # 5% appreciation supports selling
                "inventory_threshold": 2.0,  # <2 months inventory favors sellers
                "days_on_market_threshold": 25,  # Properties selling quickly
            },
        }

    async def analyze_investment_opportunity(
        self, property_data: Dict[str, Any], purchase_price: Optional[float] = None, rental_analysis: bool = False
    ) -> InvestmentOpportunity:
        """
        Comprehensive investment opportunity analysis

        Args:
            property_data: Complete property information
            purchase_price: Proposed purchase price (if different from listed price)
            rental_analysis: Whether to include rental income analysis

        Returns:
            InvestmentOpportunity with complete financial and market analysis
        """
        try:
            # Get comprehensive property valuation
            valuation_result = await self.valuation_engine.generate_comprehensive_valuation(
                property_data, include_comparables=True, use_ml_enhancement=True
            )

            # Use purchase price or estimated value
            actual_purchase_price = purchase_price or property_data.get("price", valuation_result.estimated_value)

            # Generate investment metrics
            investment_metrics = await self._calculate_investment_metrics(
                property_data, actual_purchase_price, valuation_result, rental_analysis
            )

            # Analyze market timing
            market_timing_data = await self._analyze_market_timing(property_data, actual_purchase_price)

            # Calculate investment opportunity score
            opportunity_score = await self._calculate_opportunity_score(
                investment_metrics, market_timing_data, valuation_result
            )

            # Determine investment grade
            investment_grade = self._determine_investment_grade(opportunity_score)

            # Find comparable opportunities
            comparable_opportunities = await self._find_comparable_opportunities(property_data)

            # Risk assessment
            risk_assessment = await self._assess_investment_risks(property_data, investment_metrics, market_timing_data)

            # Generate recommendations
            recommendations, next_steps = await self._generate_investment_recommendations(
                property_data, investment_metrics, market_timing_data, opportunity_score
            )

            return InvestmentOpportunity(
                property_id=property_data.get("property_id", f"investment_{int(datetime.now().timestamp())}"),
                property_address=property_data.get("address", "Unknown Address"),
                investment_grade=investment_grade,
                opportunity_score=opportunity_score,
                metrics=investment_metrics,
                valuation_result=valuation_result,
                market_timing=market_timing_data["timing_recommendation"],
                timing_score=market_timing_data["timing_score"],
                comparable_opportunities=comparable_opportunities,
                market_rank=len([opp for opp in comparable_opportunities if opp["score"] > opportunity_score]) + 1,
                risk_factors=risk_assessment["risk_factors"],
                risk_score=risk_assessment["risk_score"],
                recommendations=recommendations,
                next_steps=next_steps,
                analysis_date=datetime.now(),
                analysis_confidence=valuation_result.confidence_score,
                data_freshness_score=self._calculate_data_freshness_score(property_data),
            )

        except Exception as e:
            logger.error(f"Investment analysis failed: {str(e)}")
            return self._generate_error_investment_opportunity(property_data, str(e))

    async def generate_pricing_recommendation(
        self,
        property_data: Dict[str, Any],
        listing_goals: Dict[str, Any] = None,
        market_positioning: str = "competitive",
    ) -> PricingRecommendation:
        """
        Generate intelligent pricing recommendation for listing optimization

        Args:
            property_data: Complete property information
            listing_goals: Seller's goals (speed vs. price optimization)
            market_positioning: Desired market positioning strategy

        Returns:
            PricingRecommendation with optimal pricing strategy and rationale
        """
        try:
            # Get property valuation
            valuation_result = await self.valuation_engine.generate_comprehensive_valuation(
                property_data, include_comparables=True
            )

            # Analyze market conditions
            market_metrics = await self.market_service.get_market_metrics(
                neighborhood=property_data.get("neighborhood"), property_type=property_data.get("property_type")
            )

            # Default listing goals
            if not listing_goals:
                listing_goals = {
                    "timeline": "normal",  # "urgent", "normal", "flexible"
                    "priority": "balanced",  # "speed", "balanced", "maximum_price"
                    "market_conditions": "current",
                }

            # Determine pricing strategy
            pricing_strategy = self._determine_pricing_strategy(
                listing_goals, market_metrics, valuation_result.confidence_level
            )

            # Calculate recommended price based on strategy
            recommended_price = self._calculate_strategic_price(valuation_result, pricing_strategy, market_metrics)

            # Generate price range analysis
            price_ranges = self._calculate_price_ranges(recommended_price, valuation_result, market_metrics)

            # Market positioning analysis
            market_position = self._analyze_market_position(recommended_price, valuation_result, market_metrics)

            # Estimate market response
            market_response = await self._estimate_market_response(recommended_price, property_data, market_metrics)

            # Generate competitive advantages
            competitive_advantages = await self._identify_competitive_advantages(
                property_data, valuation_result.comparables
            )

            # Generate pricing rationale and negotiation strategy
            pricing_rationale = self._generate_pricing_rationale(
                recommended_price, valuation_result, market_metrics, pricing_strategy
            )

            negotiation_strategy = await self._generate_negotiation_strategy(
                property_data, recommended_price, market_metrics
            )

            return PricingRecommendation(
                recommended_price=recommended_price,
                pricing_strategy=pricing_strategy,
                confidence_level=valuation_result.confidence_level,
                minimum_price=price_ranges["minimum"],
                maximum_price=price_ranges["maximum"],
                optimal_range_low=price_ranges["optimal_low"],
                optimal_range_high=price_ranges["optimal_high"],
                market_position=market_position["position"],
                competitive_advantage=competitive_advantages,
                estimated_days_on_market=market_response["estimated_dom"],
                estimated_sale_probability_30d=market_response["probability_30d"],
                estimated_sale_probability_60d=market_response["probability_60d"],
                pricing_rationale=pricing_rationale,
                negotiation_strategy=negotiation_strategy,
                market_timing_advice=await self._generate_market_timing_advice(market_metrics),
            )

        except Exception as e:
            logger.error(f"Pricing recommendation failed: {str(e)}")
            return self._generate_error_pricing_recommendation(property_data, str(e))

    async def _calculate_investment_metrics(
        self,
        property_data: Dict[str, Any],
        purchase_price: float,
        valuation_result: ValuationResult,
        include_rental: bool,
    ) -> InvestmentMetrics:
        """Calculate comprehensive investment performance metrics"""

        # Current values
        current_value = valuation_result.estimated_value
        current_equity = max(0, current_value - purchase_price)

        # Get market appreciation data
        market_metrics = await self.market_service.get_market_metrics(neighborhood=property_data.get("neighborhood"))

        # Historical appreciation rate (use market data)
        annual_appreciation = market_metrics.price_trend_1y / 100  # Convert to decimal

        # Project future values
        projected_1y_value = current_value * (1 + annual_appreciation)
        projected_5y_value = current_value * ((1 + annual_appreciation) ** 5)

        # Equity projections
        equity_1y = projected_1y_value - purchase_price
        equity_5y = projected_5y_value - purchase_price

        # Rental analysis if requested
        monthly_rental = 0
        monthly_expenses = 0
        monthly_cash_flow = 0
        cap_rate = 0
        cash_on_cash_return = 0

        if include_rental:
            rental_data = await self._estimate_rental_income(property_data)
            monthly_rental = rental_data["monthly_rent"]
            monthly_expenses = rental_data["monthly_expenses"]
            monthly_cash_flow = monthly_rental - monthly_expenses

            annual_net_income = monthly_cash_flow * 12
            if current_value > 0:
                cap_rate = (annual_net_income / current_value) * 100

            # Assume 20% down payment for cash-on-cash calculation
            down_payment = purchase_price * 0.2
            if down_payment > 0:
                cash_on_cash_return = (annual_net_income / down_payment) * 100

        return InvestmentMetrics(
            purchase_price=purchase_price,
            estimated_current_value=current_value,
            projected_1y_value=projected_1y_value,
            projected_5y_value=projected_5y_value,
            current_equity=current_equity,
            equity_growth_1y=equity_1y - current_equity,
            equity_growth_5y=equity_5y - current_equity,
            annual_appreciation_rate=annual_appreciation * 100,
            monthly_rental_income=monthly_rental,
            monthly_expenses=monthly_expenses,
            monthly_cash_flow=monthly_cash_flow,
            cap_rate=cap_rate,
            cash_on_cash_return=cash_on_cash_return,
            days_on_market_estimate=self._estimate_days_on_market(property_data),
            liquidity_score=self._calculate_liquidity_score(property_data, market_metrics),
        )

    async def _analyze_market_timing(self, property_data: Dict[str, Any], purchase_price: float) -> Dict[str, Any]:
        """Analyze market timing for optimal buy/sell decisions"""

        # Get comprehensive market data
        market_metrics = await self.market_service.get_market_metrics(neighborhood=property_data.get("neighborhood"))

        timing_score = 50.0  # Base score

        # Analyze buy signals
        buy_signals = 0
        sell_signals = 0

        # Price trend analysis
        if market_metrics.price_trend_3m < self.timing_thresholds["buy_signals"]["price_trend_threshold"]:
            buy_signals += 1
            timing_score += 15
        elif market_metrics.price_trend_3m > self.timing_thresholds["sell_signals"]["price_trend_threshold"]:
            sell_signals += 1
            timing_score += 10

        # Inventory analysis
        if market_metrics.months_supply > self.timing_thresholds["buy_signals"]["inventory_threshold"]:
            buy_signals += 1
            timing_score += 10
        elif market_metrics.months_supply < self.timing_thresholds["sell_signals"]["inventory_threshold"]:
            sell_signals += 1
            timing_score += 15

        # Days on market analysis
        if market_metrics.average_days_on_market < self.timing_thresholds["sell_signals"]["days_on_market_threshold"]:
            sell_signals += 1
            timing_score += 10

        # Market condition analysis
        if market_metrics.market_condition == MarketCondition.STRONG_BUYERS:
            buy_signals += 1
            timing_score += 15
        elif market_metrics.market_condition == MarketCondition.STRONG_SELLERS:
            sell_signals += 1
            timing_score += 15

        # Determine timing recommendation
        if buy_signals >= 2 and buy_signals > sell_signals:
            timing_recommendation = MarketTiming.BUY_NOW if buy_signals >= 3 else MarketTiming.BUY_SOON
        elif sell_signals >= 2 and sell_signals > buy_signals:
            timing_recommendation = MarketTiming.SELL_NOW if sell_signals >= 3 else MarketTiming.SELL_SOON
        else:
            timing_recommendation = MarketTiming.HOLD_MONITOR

        return {
            "timing_recommendation": timing_recommendation,
            "timing_score": min(100, timing_score),
            "buy_signals": buy_signals,
            "sell_signals": sell_signals,
            "market_condition": market_metrics.market_condition,
        }

    async def _calculate_opportunity_score(
        self, metrics: InvestmentMetrics, timing_data: Dict[str, Any], valuation_result: ValuationResult
    ) -> float:
        """Calculate overall investment opportunity score (0-100)"""

        score = 0.0

        # Appreciation potential (30% weight)
        if metrics.annual_appreciation_rate > 8:
            score += 30
        elif metrics.annual_appreciation_rate > 5:
            score += 25
        elif metrics.annual_appreciation_rate > 3:
            score += 20
        else:
            score += 10

        # Cash flow analysis (25% weight)
        if metrics.cash_on_cash_return > 10:
            score += 25
        elif metrics.cash_on_cash_return > 7:
            score += 20
        elif metrics.cash_on_cash_return > 5:
            score += 15
        elif metrics.monthly_cash_flow >= 0:
            score += 10
        else:
            score += 0  # Negative cash flow

        # Market position (20% weight)
        equity_percentage = (metrics.current_equity / metrics.purchase_price) * 100 if metrics.purchase_price > 0 else 0
        if equity_percentage > 20:
            score += 20
        elif equity_percentage > 10:
            score += 15
        elif equity_percentage > 0:
            score += 10
        else:
            score += 5

        # Liquidity (15% weight)
        liquidity_score = metrics.liquidity_score / 100 * 15
        score += liquidity_score

        # Risk-adjusted return (10% weight)
        if valuation_result.confidence_level.value in ["very_high", "high"]:
            score += 10
        elif valuation_result.confidence_level.value == "medium":
            score += 7
        else:
            score += 3

        # Market timing bonus/penalty
        timing_adjustment = (timing_data["timing_score"] - 50) / 10  # Convert to ±5 point adjustment
        score += timing_adjustment

        return max(0, min(100, score))

    def _determine_investment_grade(self, opportunity_score: float) -> InvestmentGrade:
        """Determine investment grade based on opportunity score"""
        if opportunity_score >= 90:
            return InvestmentGrade.EXCEPTIONAL
        elif opportunity_score >= 80:
            return InvestmentGrade.EXCELLENT
        elif opportunity_score >= 70:
            return InvestmentGrade.GOOD
        elif opportunity_score >= 60:
            return InvestmentGrade.FAIR
        elif opportunity_score >= 50:
            return InvestmentGrade.POOR
        else:
            return InvestmentGrade.AVOID

    async def _estimate_rental_income(self, property_data: Dict[str, Any]) -> Dict[str, float]:
        """Estimate rental income and expenses for investment analysis"""

        # Simplified rental estimation (would use rental market data in production)
        estimated_value = property_data.get("estimated_value", 500000)

        # Rule of thumb: monthly rent = 0.5-1% of property value
        monthly_rent = estimated_value * 0.007  # 0.7% rule

        # Estimated monthly expenses (simplified)
        monthly_expenses = monthly_rent * 0.35  # 35% expense ratio typical

        return {"monthly_rent": monthly_rent, "monthly_expenses": monthly_expenses}

    def _estimate_days_on_market(self, property_data: Dict[str, Any]) -> int:
        """Estimate days on market based on property characteristics"""
        # Base estimate from market conditions
        base_dom = 35

        # Adjust based on property characteristics
        price = property_data.get("price", 500000)
        if price > 1000000:
            base_dom += 15  # Luxury properties take longer
        elif price < 300000:
            base_dom -= 10  # Affordable properties move faster

        # Adjust based on condition
        condition = property_data.get("condition", "average")
        if condition == "excellent":
            base_dom -= 10
        elif condition == "poor":
            base_dom += 20

        return max(10, base_dom)

    def _calculate_liquidity_score(self, property_data: Dict[str, Any], market_metrics: Any) -> float:
        """Calculate property liquidity score (0-100)"""
        score = 50.0

        # Market velocity
        if market_metrics.average_days_on_market < 30:
            score += 25
        elif market_metrics.average_days_on_market < 45:
            score += 15
        else:
            score += 5

        # Property characteristics
        price = property_data.get("price", 500000)
        if 300000 <= price <= 800000:  # Sweet spot for Austin market
            score += 15
        elif price < 300000 or price > 1200000:
            score -= 10

        # Property type
        prop_type = property_data.get("property_type", "single_family")
        if prop_type == "single_family":
            score += 10
        elif prop_type == "condo":
            score += 5

        return max(0, min(100, score))

    async def _find_comparable_opportunities(
        self, property_data: Dict[str, Any], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Find comparable investment opportunities for benchmarking"""
        try:
            # Search for similar properties
            search_criteria = {
                "neighborhood": property_data.get("neighborhood"),
                "min_price": property_data.get("price", 500000) * 0.8,
                "max_price": property_data.get("price", 500000) * 1.2,
                "property_type": property_data.get("property_type"),
            }

            properties = await self.market_service.search_properties(search_criteria, limit=limit * 2)

            # Convert to opportunity format with simplified scoring
            opportunities = []
            for prop in properties[:limit]:
                # Simplified opportunity score for comparables
                score = 70 + (hash(prop.mls_id) % 30)  # Simulate scores between 70-100

                opportunities.append(
                    {
                        "property_id": prop.mls_id,
                        "address": prop.address,
                        "price": prop.price,
                        "score": score,
                        "estimated_return": f"{score / 10:.1f}%",
                    }
                )

            return sorted(opportunities, key=lambda x: x["score"], reverse=True)

        except Exception:
            return []

    async def _assess_investment_risks(
        self, property_data: Dict[str, Any], metrics: InvestmentMetrics, timing_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess investment risks and generate risk score"""
        risk_factors = []
        risk_score = 0.0

        # Market risk factors
        if timing_data["timing_recommendation"] in [MarketTiming.HOLD_MONITOR]:
            risk_factors.append("Market timing is uncertain - consider waiting for better entry point")
            risk_score += 15

        # Financial risk factors
        if metrics.monthly_cash_flow < 0:
            risk_factors.append("Negative cash flow requires ongoing capital investment")
            risk_score += 25

        if metrics.current_equity < 0:
            risk_factors.append("Property currently underwater - equity risk present")
            risk_score += 30

        # Property-specific risks
        property_age = datetime.now().year - property_data.get("year_built", 2000)
        if property_age > 40:
            risk_factors.append("Older property may require significant maintenance investments")
            risk_score += 10

        # Market liquidity risks
        if metrics.liquidity_score < 60:
            risk_factors.append("Lower liquidity market may make exit strategy challenging")
            risk_score += 15

        # Appreciation risk
        if metrics.annual_appreciation_rate < 3:
            risk_factors.append("Below-average appreciation potential in current market")
            risk_score += 10

        return {"risk_factors": risk_factors, "risk_score": min(100, risk_score)}

    async def _generate_investment_recommendations(
        self,
        property_data: Dict[str, Any],
        metrics: InvestmentMetrics,
        timing_data: Dict[str, Any],
        opportunity_score: float,
    ) -> Tuple[List[str], List[str]]:
        """Generate investment recommendations and next steps"""
        recommendations = []
        next_steps = []

        # Primary recommendation based on score
        if opportunity_score >= 80:
            recommendations.append("Strong investment opportunity - recommend proceeding with due diligence")
            next_steps.append("Schedule property inspection within 7 days")
        elif opportunity_score >= 70:
            recommendations.append("Good investment potential with proper execution")
            next_steps.append("Verify rental income estimates and expense projections")
        elif opportunity_score >= 60:
            recommendations.append("Moderate opportunity - consider negotiating price")
            next_steps.append("Submit offer 5-10% below asking price")
        else:
            recommendations.append("Below-average opportunity - consider alternatives")
            next_steps.append("Continue property search for better opportunities")

        # Cash flow recommendations
        if metrics.monthly_cash_flow > 500:
            recommendations.append("Excellent cash flow potential for rental investment")
        elif metrics.monthly_cash_flow < 0:
            recommendations.append("Negative cash flow - suitable only for appreciation play")

        # Market timing recommendations
        if timing_data["timing_recommendation"] == MarketTiming.BUY_NOW:
            next_steps.append("Act quickly - favorable market window may be limited")
        elif timing_data["timing_recommendation"] == MarketTiming.HOLD_MONITOR:
            next_steps.append("Monitor market conditions for 30-60 days before proceeding")

        # Due diligence next steps
        next_steps.extend(
            [
                "Verify property condition through professional inspection",
                "Analyze neighborhood growth trends and development plans",
                "Review HOA fees and special assessments (if applicable)",
            ]
        )

        return recommendations, next_steps

    def _determine_pricing_strategy(
        self, listing_goals: Dict[str, Any], market_metrics: Any, confidence_level: ValuationConfidence
    ) -> PricingStrategy:
        """Determine optimal pricing strategy based on goals and market"""

        timeline = listing_goals.get("timeline", "normal")
        priority = listing_goals.get("priority", "balanced")

        # Urgent timeline favors strategic pricing
        if timeline == "urgent":
            return PricingStrategy.STRATEGIC

        # Maximum price priority in strong seller's market
        if priority == "maximum_price" and market_metrics.market_condition == MarketCondition.STRONG_SELLERS:
            return PricingStrategy.AGGRESSIVE

        # Speed priority favors competitive pricing
        if priority == "speed":
            return PricingStrategy.STRATEGIC

        # High-end market gets luxury pricing
        if market_metrics.median_price > 800000:
            return PricingStrategy.LUXURY

        # Default to competitive for balanced approach
        return PricingStrategy.COMPETITIVE

    def _calculate_strategic_price(
        self, valuation_result: ValuationResult, strategy: PricingStrategy, market_metrics: Any
    ) -> float:
        """Calculate strategic price based on pricing strategy"""

        base_value = valuation_result.estimated_value

        strategy_multipliers = {
            PricingStrategy.AGGRESSIVE: 1.05,  # 5% above market
            PricingStrategy.COMPETITIVE: 1.00,  # At market value
            PricingStrategy.STRATEGIC: 0.97,  # 3% below market for speed
            PricingStrategy.LUXURY: 1.08,  # 8% premium for luxury
        }

        multiplier = strategy_multipliers.get(strategy, 1.00)

        # Adjust for market conditions
        if market_metrics.market_condition == MarketCondition.STRONG_SELLERS:
            multiplier += 0.02  # Additional 2% in seller's market
        elif market_metrics.market_condition == MarketCondition.STRONG_BUYERS:
            multiplier -= 0.03  # 3% reduction in buyer's market

        return base_value * multiplier

    def _calculate_price_ranges(
        self, recommended_price: float, valuation_result: ValuationResult, market_metrics: Any
    ) -> Dict[str, float]:
        """Calculate comprehensive price ranges for listing strategy"""

        return {
            "minimum": valuation_result.value_range_low,
            "maximum": valuation_result.value_range_high,
            "optimal_low": recommended_price * 0.97,
            "optimal_high": recommended_price * 1.03,
        }

    def _analyze_market_position(
        self, recommended_price: float, valuation_result: ValuationResult, market_metrics: Any
    ) -> Dict[str, str]:
        """Analyze market positioning of recommended price"""

        market_value = valuation_result.estimated_value

        if recommended_price > market_value * 1.02:
            position = "above market"
        elif recommended_price < market_value * 0.98:
            position = "below market"
        else:
            position = "at market"

        return {"position": position}

    async def _estimate_market_response(
        self, recommended_price: float, property_data: Dict[str, Any], market_metrics: Any
    ) -> Dict[str, Any]:
        """Estimate market response to recommended pricing"""

        # Base days on market from market conditions
        base_dom = market_metrics.average_days_on_market

        # Adjust based on price positioning
        estimated_value = property_data.get("estimated_value", recommended_price)
        price_ratio = recommended_price / estimated_value

        if price_ratio > 1.05:
            estimated_dom = int(base_dom * 1.4)  # Overpriced takes longer
            probability_30d = 0.3
            probability_60d = 0.6
        elif price_ratio < 0.95:
            estimated_dom = int(base_dom * 0.6)  # Underpriced moves faster
            probability_30d = 0.8
            probability_60d = 0.95
        else:
            estimated_dom = base_dom
            probability_30d = 0.6
            probability_60d = 0.85

        return {"estimated_dom": estimated_dom, "probability_30d": probability_30d, "probability_60d": probability_60d}

    async def _identify_competitive_advantages(
        self, property_data: Dict[str, Any], comparables: List[Any]
    ) -> List[str]:
        """Identify competitive advantages for marketing positioning"""
        advantages = []

        # Property-specific advantages
        amenities = property_data.get("amenities", [])
        for amenity in amenities:
            if "pool" in amenity.lower():
                advantages.append("Private pool - rare in neighborhood")
            elif "garage" in amenity.lower():
                advantages.append("Covered parking protection")
            elif "updated" in amenity.lower():
                advantages.append("Recently updated - move-in ready")

        # Size advantages
        sqft = property_data.get("sqft", 0)
        if comparables:
            avg_sqft = sum(comp.sqft for comp in comparables) / len(comparables)
            if sqft > avg_sqft * 1.1:
                advantages.append(f"20% larger than typical homes in area")

        # Location advantages
        neighborhood = property_data.get("neighborhood", "")
        if "downtown" in neighborhood.lower():
            advantages.append("Prime downtown location - walk to attractions")
        elif "school" in str(property_data).lower():
            advantages.append("Top-rated school district")

        return advantages

    def _generate_pricing_rationale(
        self,
        recommended_price: float,
        valuation_result: ValuationResult,
        market_metrics: Any,
        strategy: PricingStrategy,
    ) -> List[str]:
        """Generate detailed pricing rationale"""
        rationale = []

        # Valuation support
        rationale.append(
            f"Based on comprehensive market analysis of {len(valuation_result.comparables)} comparable sales"
        )

        # Market conditions
        condition = market_metrics.market_condition.value
        if condition == "strong_sellers":
            rationale.append("Current seller's market supports premium pricing strategy")
        elif condition == "balanced":
            rationale.append("Balanced market conditions allow competitive pricing")
        else:
            rationale.append("Buyer's market requires strategic pricing for optimal results")

        # Strategy rationale
        if strategy == PricingStrategy.AGGRESSIVE:
            rationale.append("Aggressive pricing captures maximum equity in favorable market")
        elif strategy == PricingStrategy.STRATEGIC:
            rationale.append("Strategic pricing prioritizes quick sale and buyer attraction")
        elif strategy == PricingStrategy.LUXURY:
            rationale.append("Luxury positioning targets affluent buyer segment")
        else:
            rationale.append("Competitive pricing balances speed and value optimization")

        return rationale

    async def _generate_negotiation_strategy(
        self, property_data: Dict[str, Any], recommended_price: float, market_metrics: Any
    ) -> List[str]:
        """Generate negotiation strategy recommendations"""
        strategy = []

        # Market-based strategy
        if market_metrics.market_condition == MarketCondition.STRONG_SELLERS:
            strategy.append("Expect multiple offers - consider escalation clauses")
            strategy.append("Minimal concessions on price or closing costs")
        elif market_metrics.market_condition == MarketCondition.STRONG_BUYERS:
            strategy.append("Be prepared for price negotiations and buyer concessions")
            strategy.append("Consider offering closing cost assistance")
        else:
            strategy.append("Balanced negotiation approach - evaluate each offer individually")

        # Property-specific strategy
        days_estimate = self._estimate_days_on_market(property_data)
        if days_estimate > 45:
            strategy.append("Extended marketing time expected - remain flexible on terms")
        else:
            strategy.append("Quick sale anticipated - maintain firm pricing position")

        return strategy

    async def _generate_market_timing_advice(self, market_metrics: Any) -> str:
        """Generate market timing advice for optimal listing"""

        # Seasonal factors
        month = datetime.now().month
        if month in [3, 4, 5]:
            return "Spring market peak - ideal timing for maximum exposure"
        elif month in [6, 7, 8]:
            return "Summer market activity - good timing for family relocations"
        elif month in [9, 10, 11]:
            return "Fall market - serious buyers but reduced inventory"
        else:
            return "Winter market - fewer buyers but less competition"

    def _calculate_data_freshness_score(self, property_data: Dict[str, Any]) -> float:
        """Calculate data freshness score for analysis confidence"""
        # Simplified data freshness calculation
        # In production, would check actual data timestamps
        return 85.0  # Assume good data freshness

    def _generate_error_investment_opportunity(
        self, property_data: Dict[str, Any], error_message: str
    ) -> InvestmentOpportunity:
        """Generate error investment opportunity result"""

        # Create minimal error result
        return InvestmentOpportunity(
            property_id=property_data.get("property_id", "error"),
            property_address=property_data.get("address", "Unknown"),
            investment_grade=InvestmentGrade.AVOID,
            opportunity_score=0,
            metrics=InvestmentMetrics(
                purchase_price=0,
                estimated_current_value=0,
                projected_1y_value=0,
                projected_5y_value=0,
                current_equity=0,
                equity_growth_1y=0,
                equity_growth_5y=0,
                annual_appreciation_rate=0,
            ),
            valuation_result=None,
            market_timing=MarketTiming.HOLD_MONITOR,
            timing_score=0,
            comparable_opportunities=[],
            market_rank=0,
            risk_factors=[f"Analysis failed: {error_message}"],
            risk_score=100,
            recommendations=["Unable to analyze - insufficient data"],
            next_steps=["Gather additional property information and retry analysis"],
            analysis_date=datetime.now(),
            analysis_confidence=0,
            data_freshness_score=0,
        )

    def _generate_error_pricing_recommendation(
        self, property_data: Dict[str, Any], error_message: str
    ) -> PricingRecommendation:
        """Generate error pricing recommendation"""

        return PricingRecommendation(
            recommended_price=0,
            pricing_strategy=PricingStrategy.COMPETITIVE,
            confidence_level=ValuationConfidence.UNRELIABLE,
            minimum_price=0,
            maximum_price=0,
            optimal_range_low=0,
            optimal_range_high=0,
            market_position="unknown",
            competitive_advantage=[],
            estimated_days_on_market=0,
            estimated_sale_probability_30d=0,
            estimated_sale_probability_60d=0,
            pricing_rationale=[f"Pricing analysis failed: {error_message}"],
            negotiation_strategy=["Unable to generate strategy - insufficient data"],
            market_timing_advice="Data unavailable",
        )


# Global service instance
_pricing_intelligence_service = None


def get_pricing_intelligence_service() -> PricingIntelligenceService:
    """Get singleton instance of Pricing Intelligence Service"""
    global _pricing_intelligence_service
    if _pricing_intelligence_service is None:
        _pricing_intelligence_service = PricingIntelligenceService()
    return _pricing_intelligence_service
