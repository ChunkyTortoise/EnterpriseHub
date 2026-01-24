"""
Property Intelligence Agent - Advanced Property Analysis Engine
Deep property analysis beyond CMA generation for investment decisions and market positioning.

This agent provides comprehensive property intelligence including:
- Investment scoring and ROI analysis
- Market positioning and competitive analysis
- Property condition assessment and renovation recommendations
- Neighborhood analysis and demographic insights
- Risk assessment and market timing predictions
"""

import asyncio
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import re

from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class PropertyIntelligenceLevel(Enum):
    """Levels of property intelligence analysis."""
    BASIC = "basic"               # Quick assessment
    STANDARD = "standard"         # Comprehensive analysis
    PREMIUM = "premium"           # Deep dive with predictions
    INSTITUTIONAL = "institutional" # Investment-grade analysis

class PropertyType(Enum):
    """Property type classifications."""
    SINGLE_FAMILY = "single_family"
    MULTI_FAMILY = "multi_family"
    CONDO = "condo"
    TOWNHOUSE = "townhouse"
    COMMERCIAL = "commercial"
    LAND = "land"
    LUXURY = "luxury"

class InvestmentStrategy(Enum):
    """Investment strategy types."""
    BUY_AND_HOLD = "buy_and_hold"
    FIX_AND_FLIP = "fix_and_flip"
    RENTAL_INCOME = "rental_income"
    DEVELOPMENT = "development"
    WHOLESALE = "wholesale"
    LIVE_IN_FLIP = "live_in_flip"

@dataclass
class PropertyIntelligenceRequest:
    """Request for property intelligence analysis."""
    property_address: str
    property_type: PropertyType
    intelligence_level: PropertyIntelligenceLevel
    investment_strategy: Optional[InvestmentStrategy] = None
    budget_range: Optional[Tuple[int, int]] = None
    timeline: Optional[str] = None
    investor_profile: Optional[str] = None  # beginner, intermediate, advanced
    special_requirements: List[str] = field(default_factory=list)

@dataclass
class InvestmentScoring:
    """Investment potential scoring."""
    total_score: float  # 0-100
    cash_flow_score: float
    appreciation_score: float
    risk_score: float
    liquidity_score: float
    market_timing_score: float

    # Detailed metrics
    projected_roi: float
    cap_rate: Optional[float]
    cash_on_cash_return: float
    break_even_analysis: Dict[str, Any]
    exit_strategy_viability: float

@dataclass
class MarketPositioning:
    """Property's position in the market."""
    competitive_rank: str  # "top_tier", "mid_market", "value_tier"
    price_position: str    # "below_market", "at_market", "above_market"
    days_on_market_prediction: int
    target_buyer_profile: str
    market_absorption_rate: float
    comparable_properties: List[Dict]
    pricing_recommendations: Dict[str, Any]

@dataclass
class PropertyConditionAssessment:
    """Assessment of property condition and needed improvements."""
    overall_condition: str  # "excellent", "good", "fair", "poor"
    condition_score: float  # 0-100

    # Systems assessment
    structural_score: float
    mechanical_score: float
    electrical_score: float
    plumbing_score: float
    hvac_score: float
    roofing_score: float

    # Improvement recommendations
    immediate_repairs: List[Dict]
    value_add_opportunities: List[Dict]
    cosmetic_improvements: List[Dict]
    major_renovations: List[Dict]

    # Cost estimates
    total_repair_estimate: float
    value_add_estimate: float
    renovation_timeline: str

@dataclass
class NeighborhoodIntelligence:
    """Comprehensive neighborhood analysis."""
    neighborhood_score: float  # 0-100
    walkability_score: float
    school_rating: float
    crime_index: float
    amenities_score: float

    # Demographics
    median_income: float
    age_demographics: Dict[str, float]
    education_level: str
    employment_trends: List[str]

    # Market trends
    price_appreciation_trend: float
    rental_demand: str
    development_projects: List[Dict]
    gentrification_indicators: List[str]

    # Investment insights
    investor_activity: str
    rental_yield_potential: float
    future_growth_projections: List[str]

@dataclass
class RiskAssessment:
    """Comprehensive risk analysis."""
    overall_risk_level: str  # "low", "moderate", "high", "very_high"
    risk_score: float  # 0-100 (lower is better)

    # Risk categories
    market_risk: float
    liquidity_risk: float
    condition_risk: float
    location_risk: float
    financing_risk: float
    regulatory_risk: float

    # Risk factors
    identified_risks: List[Dict]
    mitigation_strategies: List[Dict]
    risk_timeline: Dict[str, str]

    # Insurance and legal
    insurance_considerations: List[str]
    legal_considerations: List[str]
    disclosure_items: List[str]

@dataclass
class PropertyIntelligenceReport:
    """Comprehensive property intelligence report."""
    property_address: str
    analysis_date: datetime
    intelligence_level: PropertyIntelligenceLevel

    # Core analysis
    investment_scoring: InvestmentScoring
    market_positioning: MarketPositioning
    condition_assessment: PropertyConditionAssessment
    neighborhood_intelligence: NeighborhoodIntelligence
    risk_assessment: RiskAssessment

    # Strategic recommendations
    investment_recommendation: str
    optimal_strategy: InvestmentStrategy
    key_opportunities: List[str]
    critical_concerns: List[str]
    action_timeline: Dict[str, str]

    # Executive summary
    executive_summary: str
    confidence_level: float
    analysis_accuracy: str

class PropertyDataCollector:
    """Collects comprehensive property data from multiple sources."""

    def __init__(self):
        self.data_sources = {
            "mls": {"status": "connected", "reliability": 0.95},
            "zillow": {"status": "connected", "reliability": 0.85},
            "redfin": {"status": "connected", "reliability": 0.90},
            "public_records": {"status": "connected", "reliability": 0.98},
            "rental_comps": {"status": "connected", "reliability": 0.80},
            "demographic_data": {"status": "connected", "reliability": 0.92}
        }

    async def collect_property_data(self, address: str, intelligence_level: PropertyIntelligenceLevel) -> Dict[str, Any]:
        """Collect comprehensive property data."""
        logger.info(f"Collecting property data for {address} at {intelligence_level.value} level")

        data = {
            "basic_info": await self._collect_basic_info(address),
            "market_data": await self._collect_market_data(address),
            "neighborhood_data": await self._collect_neighborhood_data(address),
            "comparable_sales": await self._collect_comparable_sales(address),
            "rental_comps": await self._collect_rental_comps(address),
            "public_records": await self._collect_public_records(address)
        }

        # Add premium data for higher intelligence levels
        if intelligence_level in [PropertyIntelligenceLevel.PREMIUM, PropertyIntelligenceLevel.INSTITUTIONAL]:
            data.update({
                "investment_metrics": await self._collect_investment_metrics(address),
                "predictive_data": await self._collect_predictive_data(address),
                "institutional_metrics": await self._collect_institutional_metrics(address)
            })

        return data

    async def _collect_basic_info(self, address: str) -> Dict[str, Any]:
        """Collect basic property information."""
        # Mock implementation - in production would connect to actual APIs
        return {
            "property_type": "single_family",
            "square_footage": 2400,
            "bedrooms": 4,
            "bathrooms": 3,
            "lot_size": 0.25,
            "year_built": 1995,
            "last_sale_date": "2020-03-15",
            "last_sale_price": 450000,
            "current_list_price": None,
            "property_tax": 8400,
            "hoa_fees": 0
        }

    async def _collect_market_data(self, address: str) -> Dict[str, Any]:
        """Collect market data and trends."""
        return {
            "median_home_value": 520000,
            "price_per_sqft": 250,
            "market_appreciation_1y": 8.5,
            "market_appreciation_5y": 35.2,
            "days_on_market_avg": 25,
            "inventory_levels": "low",
            "market_trend": "seller_favorable",
            "seasonal_patterns": {"best_listing_month": "May", "best_buying_month": "November"}
        }

    async def _collect_neighborhood_data(self, address: str) -> Dict[str, Any]:
        """Collect neighborhood demographics and characteristics."""
        return {
            "median_income": 85000,
            "population_density": 2500,
            "walkability_score": 72,
            "transit_score": 45,
            "school_ratings": {"elementary": 8, "middle": 7, "high": 9},
            "crime_index": 15,  # Lower is better
            "amenities": ["parks", "shopping", "restaurants", "gym"],
            "employment_centers": ["downtown", "tech_park", "medical_center"]
        }

    async def _collect_comparable_sales(self, address: str) -> List[Dict]:
        """Collect comparable sales data."""
        return [
            {
                "address": "123 Similar St",
                "sale_date": "2025-11-20",
                "sale_price": 485000,
                "square_footage": 2350,
                "price_per_sqft": 206,
                "bedrooms": 4,
                "bathrooms": 3,
                "similarity_score": 0.92
            },
            {
                "address": "456 Nearby Ave",
                "sale_date": "2025-10-15",
                "sale_price": 495000,
                "square_footage": 2450,
                "price_per_sqft": 202,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "similarity_score": 0.88
            }
        ]

    async def _collect_rental_comps(self, address: str) -> List[Dict]:
        """Collect rental comparable data."""
        return [
            {
                "address": "789 Rental Rd",
                "monthly_rent": 2800,
                "square_footage": 2300,
                "bedrooms": 4,
                "bathrooms": 3,
                "rent_per_sqft": 1.22
            },
            {
                "address": "321 Lease Ln",
                "monthly_rent": 2950,
                "square_footage": 2500,
                "bedrooms": 4,
                "bathrooms": 3.5,
                "rent_per_sqft": 1.18
            }
        ]

    async def _collect_public_records(self, address: str) -> Dict[str, Any]:
        """Collect public records data."""
        return {
            "ownership_history": [
                {"owner": "Current Owner", "purchase_date": "2020-03-15", "purchase_price": 450000}
            ],
            "permit_history": [
                {"permit_type": "bathroom_remodel", "date": "2022-06-01", "cost": 15000},
                {"permit_type": "roof_replacement", "date": "2021-09-15", "cost": 12000}
            ],
            "tax_assessment": {
                "land_value": 125000,
                "improvement_value": 325000,
                "total_assessment": 450000,
                "assessment_date": "2025-01-01"
            }
        }

    async def _collect_investment_metrics(self, address: str) -> Dict[str, Any]:
        """Collect investment-specific metrics."""
        return {
            "rental_yield": 6.2,
            "cap_rate": 5.8,
            "cash_flow_potential": 450,
            "appreciation_forecast": 7.5,
            "market_cycle_position": "growth_phase",
            "investor_activity": "high",
            "flip_potential": 8.5
        }

    async def _collect_predictive_data(self, address: str) -> Dict[str, Any]:
        """Collect predictive analytics data."""
        return {
            "price_forecast_1y": 8.2,
            "price_forecast_3y": 22.5,
            "price_forecast_5y": 38.1,
            "rental_growth_forecast": 4.5,
            "market_risk_indicators": ["interest_rate_sensitivity", "economic_dependency"],
            "future_development_impact": "positive"
        }

    async def _collect_institutional_metrics(self, address: str) -> Dict[str, Any]:
        """Collect institutional-grade metrics."""
        return {
            "irr_projection": 12.8,
            "npv_calculation": 85000,
            "sensitivity_analysis": {"best_case": 15.2, "base_case": 12.8, "worst_case": 8.9},
            "portfolio_fit_score": 0.85,
            "liquidity_timeline": 180,  # days to sell
            "institutional_demand": "high"
        }

class InvestmentAnalysisEngine:
    """Analyzes investment potential and scoring."""

    def __init__(self):
        self.claude_assistant = ClaudeAssistant()

    async def analyze_investment_potential(self,
                                         property_data: Dict[str, Any],
                                         strategy: InvestmentStrategy,
                                         investor_profile: str) -> InvestmentScoring:
        """Analyze investment potential and generate scoring."""

        # Base calculations
        purchase_price = property_data["basic_info"]["current_list_price"] or self._estimate_market_value(property_data)
        rental_income = await self._calculate_rental_income(property_data)
        operating_expenses = await self._calculate_operating_expenses(property_data)

        # Strategy-specific analysis
        if strategy == InvestmentStrategy.RENTAL_INCOME:
            scoring = await self._analyze_rental_strategy(property_data, purchase_price, rental_income, operating_expenses)
        elif strategy == InvestmentStrategy.FIX_AND_FLIP:
            scoring = await self._analyze_flip_strategy(property_data, purchase_price)
        elif strategy == InvestmentStrategy.BUY_AND_HOLD:
            scoring = await self._analyze_buy_hold_strategy(property_data, purchase_price, rental_income)
        else:
            scoring = await self._analyze_general_investment(property_data, purchase_price, rental_income)

        return scoring

    async def _analyze_rental_strategy(self, property_data: Dict, purchase_price: float,
                                     rental_income: float, operating_expenses: float) -> InvestmentScoring:
        """Analyze rental income investment strategy."""

        annual_rental = rental_income * 12
        net_operating_income = annual_rental - operating_expenses

        # Calculate key metrics
        cap_rate = (net_operating_income / purchase_price) * 100
        cash_flow_monthly = rental_income - (operating_expenses / 12) - (purchase_price * 0.005)  # Assume mortgage payment
        cash_on_cash = (cash_flow_monthly * 12) / (purchase_price * 0.25) * 100  # 25% down

        # Scoring components
        cash_flow_score = min(100, max(0, (cash_flow_monthly + 500) / 10))  # Scale based on cash flow
        appreciation_score = property_data["market_data"]["market_appreciation_5y"] * 2  # 5-year appreciation scaled
        risk_score = 100 - (property_data["neighborhood_data"]["crime_index"] * 2)
        liquidity_score = 100 - property_data["market_data"]["days_on_market_avg"]
        market_timing_score = 85 if property_data["market_data"]["market_trend"] == "buyer_favorable" else 75

        total_score = (cash_flow_score * 0.3 + appreciation_score * 0.25 +
                      risk_score * 0.2 + liquidity_score * 0.15 + market_timing_score * 0.1)

        return InvestmentScoring(
            total_score=min(100, total_score),
            cash_flow_score=cash_flow_score,
            appreciation_score=appreciation_score,
            risk_score=risk_score,
            liquidity_score=liquidity_score,
            market_timing_score=market_timing_score,
            projected_roi=cash_on_cash,
            cap_rate=cap_rate,
            cash_on_cash_return=cash_on_cash,
            break_even_analysis={
                "months_to_break_even": 24 if cash_flow_monthly > 0 else 60,
                "total_investment": purchase_price * 0.25,
                "monthly_cash_flow": cash_flow_monthly
            },
            exit_strategy_viability=85.0
        )

    async def _analyze_flip_strategy(self, property_data: Dict, purchase_price: float) -> InvestmentScoring:
        """Analyze fix and flip strategy."""

        # Estimate renovation costs and ARV
        renovation_estimate = await self._estimate_renovation_costs(property_data)
        arv = await self._estimate_after_repair_value(property_data)

        total_investment = purchase_price + renovation_estimate + (purchase_price * 0.1)  # 10% for carrying costs
        projected_profit = arv - total_investment
        projected_roi = (projected_profit / total_investment) * 100

        # Scoring
        cash_flow_score = 0  # No ongoing cash flow for flips
        appreciation_score = min(100, projected_roi)
        risk_score = 100 - (renovation_estimate / purchase_price * 100)  # Higher renovation = higher risk
        liquidity_score = property_data["market_data"]["days_on_market_avg"]
        market_timing_score = 90 if property_data["market_data"]["market_trend"] == "seller_favorable" else 70

        total_score = (cash_flow_score * 0.1 + appreciation_score * 0.4 +
                      risk_score * 0.25 + liquidity_score * 0.15 + market_timing_score * 0.1)

        return InvestmentScoring(
            total_score=min(100, total_score),
            cash_flow_score=cash_flow_score,
            appreciation_score=appreciation_score,
            risk_score=risk_score,
            liquidity_score=liquidity_score,
            market_timing_score=market_timing_score,
            projected_roi=projected_roi,
            cap_rate=None,  # Not applicable for flips
            cash_on_cash_return=projected_roi,
            break_even_analysis={
                "purchase_price": purchase_price,
                "renovation_estimate": renovation_estimate,
                "arv": arv,
                "projected_profit": projected_profit
            },
            exit_strategy_viability=liquidity_score
        )

    async def _analyze_buy_hold_strategy(self, property_data: Dict, purchase_price: float, rental_income: float) -> InvestmentScoring:
        """Analyze buy and hold strategy."""
        # Combination of rental income and long-term appreciation
        rental_scoring = await self._analyze_rental_strategy(property_data, purchase_price, rental_income, 0)

        # Adjust for long-term holding
        rental_scoring.appreciation_score *= 1.2  # Higher weight on appreciation
        rental_scoring.liquidity_score *= 0.8     # Lower weight on liquidity

        # Recalculate total score
        total_score = (rental_scoring.cash_flow_score * 0.25 + rental_scoring.appreciation_score * 0.35 +
                      rental_scoring.risk_score * 0.2 + rental_scoring.liquidity_score * 0.1 +
                      rental_scoring.market_timing_score * 0.1)

        rental_scoring.total_score = min(100, total_score)
        return rental_scoring

    async def _analyze_general_investment(self, property_data: Dict, purchase_price: float, rental_income: float) -> InvestmentScoring:
        """General investment analysis."""
        return await self._analyze_rental_strategy(property_data, purchase_price, rental_income, 0)

    def _estimate_market_value(self, property_data: Dict) -> float:
        """Estimate current market value."""
        sqft = property_data["basic_info"]["square_footage"]
        price_per_sqft = property_data["market_data"]["price_per_sqft"]
        return sqft * price_per_sqft

    async def _calculate_rental_income(self, property_data: Dict) -> float:
        """Calculate estimated rental income."""
        rental_comps = property_data["rental_comps"]
        if rental_comps:
            avg_rent_per_sqft = sum(comp["rent_per_sqft"] for comp in rental_comps) / len(rental_comps)
            sqft = property_data["basic_info"]["square_footage"]
            return sqft * avg_rent_per_sqft
        return 0

    async def _calculate_operating_expenses(self, property_data: Dict) -> float:
        """Calculate annual operating expenses."""
        property_tax = property_data["basic_info"]["property_tax"]
        insurance = property_tax * 0.5  # Rough estimate
        maintenance = property_tax * 0.8  # Maintenance and repairs
        management = property_tax * 0.3   # Property management

        return property_tax + insurance + maintenance + management

    async def _estimate_renovation_costs(self, property_data: Dict) -> float:
        """Estimate renovation costs for fix and flip."""
        sqft = property_data["basic_info"]["square_footage"]
        # Mock renovation cost estimation
        return sqft * 25  # $25 per sqft average renovation

    async def _estimate_after_repair_value(self, property_data: Dict) -> float:
        """Estimate after repair value."""
        current_value = self._estimate_market_value(property_data)
        # Assume 20% increase after renovations
        return current_value * 1.2

class PropertyIntelligenceAgent:
    """
    Advanced Property Intelligence Agent

    Provides comprehensive property analysis beyond basic CMA generation,
    including investment scoring, market positioning, condition assessment,
    and strategic recommendations.
    """

    def __init__(self):
        self.claude_assistant = ClaudeAssistant()
        self.event_publisher = get_event_publisher()
        self.data_collector = PropertyDataCollector()
        self.investment_analyzer = InvestmentAnalysisEngine()
        self.cma_generator = CMAGenerator()  # Leverage existing CMA capabilities

    async def analyze_property(self, request: PropertyIntelligenceRequest) -> PropertyIntelligenceReport:
        """Perform comprehensive property intelligence analysis."""

        logger.info(f"Starting property intelligence analysis for {request.property_address}")

        # Collect comprehensive property data
        property_data = await self.data_collector.collect_property_data(
            request.property_address,
            request.intelligence_level
        )

        # Perform investment analysis
        investment_scoring = await self.investment_analyzer.analyze_investment_potential(
            property_data,
            request.investment_strategy or InvestmentStrategy.BUY_AND_HOLD,
            request.investor_profile or "intermediate"
        )

        # Market positioning analysis
        market_positioning = await self._analyze_market_positioning(property_data)

        # Property condition assessment
        condition_assessment = await self._assess_property_condition(property_data, request)

        # Neighborhood intelligence
        neighborhood_intel = await self._analyze_neighborhood_intelligence(property_data)

        # Risk assessment
        risk_assessment = await self._conduct_risk_assessment(property_data, investment_scoring)

        # Generate strategic recommendations
        recommendations = await self._generate_strategic_recommendations(
            property_data, investment_scoring, market_positioning, request
        )

        # Create comprehensive report
        report = PropertyIntelligenceReport(
            property_address=request.property_address,
            analysis_date=datetime.now(),
            intelligence_level=request.intelligence_level,
            investment_scoring=investment_scoring,
            market_positioning=market_positioning,
            condition_assessment=condition_assessment,
            neighborhood_intelligence=neighborhood_intel,
            risk_assessment=risk_assessment,
            investment_recommendation=recommendations["recommendation"],
            optimal_strategy=recommendations["optimal_strategy"],
            key_opportunities=recommendations["opportunities"],
            critical_concerns=recommendations["concerns"],
            action_timeline=recommendations["timeline"],
            executive_summary=await self._generate_executive_summary(investment_scoring, recommendations),
            confidence_level=recommendations["confidence"],
            analysis_accuracy="high"
        )

        # Publish analysis event
        await self.event_publisher.publish_property_intelligence_analysis(
            property_address=request.property_address,
            intelligence_level=request.intelligence_level.value,
            investment_score=investment_scoring.total_score,
            recommendation=recommendations["recommendation"],
            confidence=recommendations["confidence"]
        )

        logger.info(f"Property intelligence analysis completed for {request.property_address}")

        return report

    async def _analyze_market_positioning(self, property_data: Dict) -> MarketPositioning:
        """Analyze property's market positioning."""

        current_value = property_data["basic_info"].get("current_list_price") or \
                       (property_data["basic_info"]["square_footage"] * property_data["market_data"]["price_per_sqft"])

        median_value = property_data["market_data"]["median_home_value"]

        # Determine price position
        if current_value < median_value * 0.85:
            price_position = "below_market"
        elif current_value > median_value * 1.15:
            price_position = "above_market"
        else:
            price_position = "at_market"

        # Determine competitive rank
        if current_value > median_value * 1.3:
            competitive_rank = "top_tier"
        elif current_value > median_value * 0.8:
            competitive_rank = "mid_market"
        else:
            competitive_rank = "value_tier"

        return MarketPositioning(
            competitive_rank=competitive_rank,
            price_position=price_position,
            days_on_market_prediction=property_data["market_data"]["days_on_market_avg"],
            target_buyer_profile="primary_residence" if competitive_rank == "mid_market" else "investor",
            market_absorption_rate=0.85,
            comparable_properties=property_data["comparable_sales"],
            pricing_recommendations={
                "optimal_list_price": current_value,
                "price_range": (current_value * 0.95, current_value * 1.05),
                "strategy": "competitive_pricing"
            }
        )

    async def _assess_property_condition(self, property_data: Dict, request: PropertyIntelligenceRequest) -> PropertyConditionAssessment:
        """Assess property condition and improvement opportunities."""

        year_built = property_data["basic_info"]["year_built"]
        current_year = datetime.now().year
        property_age = current_year - year_built

        # Base condition scoring on age and maintenance
        if property_age < 10:
            base_score = 90
        elif property_age < 20:
            base_score = 80
        elif property_age < 30:
            base_score = 70
        else:
            base_score = 60

        # Adjust based on permits/improvements
        permit_history = property_data["public_records"]["permit_history"]
        recent_improvements = len([p for p in permit_history if
                                 datetime.strptime(p["date"], "%Y-%m-%d").year >= current_year - 5])

        condition_score = min(100, base_score + (recent_improvements * 5))

        # Determine overall condition
        if condition_score >= 85:
            overall_condition = "excellent"
        elif condition_score >= 70:
            overall_condition = "good"
        elif condition_score >= 55:
            overall_condition = "fair"
        else:
            overall_condition = "poor"

        # Mock system scores (in production, would use inspection data)
        return PropertyConditionAssessment(
            overall_condition=overall_condition,
            condition_score=condition_score,
            structural_score=85,
            mechanical_score=75,
            electrical_score=80,
            plumbing_score=70,
            hvac_score=65,
            roofing_score=90,  # Recent roof replacement in permits
            immediate_repairs=[
                {"item": "HVAC tune-up", "cost": 300, "priority": "medium"},
                {"item": "Plumbing inspection", "cost": 150, "priority": "low"}
            ],
            value_add_opportunities=[
                {"improvement": "Kitchen update", "cost": 25000, "value_add": 35000},
                {"improvement": "Bathroom remodel", "cost": 15000, "value_add": 20000}
            ],
            cosmetic_improvements=[
                {"improvement": "Interior paint", "cost": 3000, "value_add": 5000},
                {"improvement": "Landscaping", "cost": 2000, "value_add": 3000}
            ],
            major_renovations=[
                {"renovation": "Addition", "cost": 80000, "value_add": 100000}
            ],
            total_repair_estimate=450,
            value_add_estimate=70000,
            renovation_timeline="3-6 months for value-add improvements"
        )

    async def _analyze_neighborhood_intelligence(self, property_data: Dict) -> NeighborhoodIntelligence:
        """Analyze neighborhood characteristics and trends."""

        neighborhood_data = property_data["neighborhood_data"]
        market_data = property_data["market_data"]

        # Calculate neighborhood score
        neighborhood_score = (
            min(100, neighborhood_data["walkability_score"]) * 0.2 +
            (neighborhood_data["school_ratings"]["elementary"] * 10) * 0.25 +
            (100 - neighborhood_data["crime_index"] * 5) * 0.25 +
            min(100, neighborhood_data["median_income"] / 1000) * 0.3
        )

        return NeighborhoodIntelligence(
            neighborhood_score=neighborhood_score,
            walkability_score=neighborhood_data["walkability_score"],
            school_rating=(neighborhood_data["school_ratings"]["elementary"] +
                          neighborhood_data["school_ratings"]["middle"] +
                          neighborhood_data["school_ratings"]["high"]) / 3,
            crime_index=neighborhood_data["crime_index"],
            amenities_score=len(neighborhood_data["amenities"]) * 10,
            median_income=neighborhood_data["median_income"],
            age_demographics={"25-44": 0.35, "45-64": 0.30, "65+": 0.15, "under_25": 0.20},
            education_level="college_educated",
            employment_trends=["tech_growth", "healthcare_expansion"],
            price_appreciation_trend=market_data["market_appreciation_5y"],
            rental_demand="high",
            development_projects=[
                {"project": "New shopping center", "completion": "2027", "impact": "positive"}
            ],
            gentrification_indicators=["rising_property_values", "new_businesses"],
            investor_activity="moderate",
            rental_yield_potential=6.2,
            future_growth_projections=["continued_appreciation", "increasing_demand"]
        )

    async def _conduct_risk_assessment(self, property_data: Dict, investment_scoring: InvestmentScoring) -> RiskAssessment:
        """Conduct comprehensive risk assessment."""

        # Calculate risk factors
        market_risk = 100 - investment_scoring.market_timing_score
        liquidity_risk = 100 - investment_scoring.liquidity_score
        condition_risk = 100 - property_data.get("condition_score", 75)
        location_risk = property_data["neighborhood_data"]["crime_index"]
        financing_risk = 25  # Moderate financing risk
        regulatory_risk = 15  # Low regulatory risk

        overall_risk_score = (
            market_risk * 0.25 +
            liquidity_risk * 0.20 +
            condition_risk * 0.20 +
            location_risk * 0.15 +
            financing_risk * 0.10 +
            regulatory_risk * 0.10
        )

        if overall_risk_score < 25:
            risk_level = "low"
        elif overall_risk_score < 50:
            risk_level = "moderate"
        elif overall_risk_score < 75:
            risk_level = "high"
        else:
            risk_level = "very_high"

        return RiskAssessment(
            overall_risk_level=risk_level,
            risk_score=overall_risk_score,
            market_risk=market_risk,
            liquidity_risk=liquidity_risk,
            condition_risk=condition_risk,
            location_risk=location_risk,
            financing_risk=financing_risk,
            regulatory_risk=regulatory_risk,
            identified_risks=[
                {"risk": "Market volatility", "probability": "medium", "impact": "high"},
                {"risk": "Interest rate changes", "probability": "high", "impact": "medium"}
            ],
            mitigation_strategies=[
                {"strategy": "Diversified portfolio", "effectiveness": "high"},
                {"strategy": "Fixed-rate financing", "effectiveness": "medium"}
            ],
            risk_timeline={"short_term": "low", "medium_term": "moderate", "long_term": "low"},
            insurance_considerations=["property_insurance", "liability_coverage"],
            legal_considerations=["title_insurance", "proper_disclosures"],
            disclosure_items=["roof_replacement_2021", "bathroom_remodel_2022"]
        )

    async def _generate_strategic_recommendations(self,
                                                property_data: Dict,
                                                investment_scoring: InvestmentScoring,
                                                market_positioning: MarketPositioning,
                                                request: PropertyIntelligenceRequest) -> Dict[str, Any]:
        """Generate strategic investment recommendations."""

        # Determine overall recommendation
        if investment_scoring.total_score >= 80:
            recommendation = "STRONG_BUY"
        elif investment_scoring.total_score >= 65:
            recommendation = "BUY"
        elif investment_scoring.total_score >= 50:
            recommendation = "CONDITIONAL_BUY"
        elif investment_scoring.total_score >= 35:
            recommendation = "HOLD"
        else:
            recommendation = "AVOID"

        # Determine optimal strategy
        if investment_scoring.cash_flow_score > 70:
            optimal_strategy = InvestmentStrategy.RENTAL_INCOME
        elif investment_scoring.appreciation_score > 80:
            optimal_strategy = InvestmentStrategy.BUY_AND_HOLD
        else:
            optimal_strategy = request.investment_strategy or InvestmentStrategy.BUY_AND_HOLD

        # Identify opportunities
        opportunities = []
        if investment_scoring.cash_flow_score > 60:
            opportunities.append("Strong rental income potential")
        if investment_scoring.appreciation_score > 70:
            opportunities.append("Excellent long-term appreciation prospects")
        if market_positioning.price_position == "below_market":
            opportunities.append("Below-market pricing opportunity")

        # Identify concerns
        concerns = []
        if investment_scoring.risk_score < 50:
            concerns.append("Higher than average risk profile")
        if investment_scoring.liquidity_score < 40:
            concerns.append("Potential liquidity challenges")
        if market_positioning.days_on_market_prediction > 60:
            concerns.append("Extended time to sell expected")

        # Create action timeline
        timeline = {
            "immediate": "Conduct property inspection and financing pre-approval",
            "30_days": "Complete due diligence and finalize purchase",
            "90_days": "Implement value-add improvements if applicable",
            "1_year": "Review performance and market conditions"
        }

        # Confidence calculation
        confidence = min(100, (investment_scoring.total_score + 20) / 100)

        return {
            "recommendation": recommendation,
            "optimal_strategy": optimal_strategy,
            "opportunities": opportunities,
            "concerns": concerns,
            "timeline": timeline,
            "confidence": confidence
        }

    async def _generate_executive_summary(self, investment_scoring: InvestmentScoring, recommendations: Dict) -> str:
        """Generate executive summary using Claude."""

        summary_prompt = f"""
        Generate a concise executive summary for a property investment analysis with these key metrics:

        Investment Score: {investment_scoring.total_score}/100
        Projected ROI: {investment_scoring.projected_roi:.1f}%
        Recommendation: {recommendations['recommendation']}

        Key Opportunities: {', '.join(recommendations['opportunities'])}
        Main Concerns: {', '.join(recommendations['concerns'])}

        Create a 2-3 sentence executive summary highlighting the most important points for an investor.
        """

        response = await self.claude_assistant.analyze_with_context(summary_prompt)
        return response.get("content", "Comprehensive property analysis completed with detailed investment metrics and strategic recommendations.")

# --- Factory Functions ---

def get_property_intelligence_agent() -> PropertyIntelligenceAgent:
    """Get singleton Property Intelligence Agent instance."""
    if not hasattr(get_property_intelligence_agent, '_instance'):
        get_property_intelligence_agent._instance = PropertyIntelligenceAgent()
    return get_property_intelligence_agent._instance

# --- Event Publisher Extensions ---

async def publish_property_intelligence_analysis(event_publisher, **kwargs):
    """Publish property intelligence analysis event."""
    await event_publisher.publish_event(
        event_type="property_intelligence_analysis",
        data={
            **kwargs,
            "timestamp": datetime.now().isoformat()
        }
    )