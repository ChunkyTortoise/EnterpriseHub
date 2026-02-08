"""
Scenario Simulation Engine - Advanced "What-If" Business Modeling
==============================================================

Provides real-time scenario simulation for strategic decision making.
Enables Jorge to answer questions like "What if I change commission rates?"
or "What if I raise qualification thresholds?" with instant data-driven projections.

Author: Enhanced from research recommendations - January 2026
"""

import asyncio
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.cache_service import get_cache_service

logger = get_logger(__name__)


class ScenarioType(Enum):
    """Types of business scenarios to simulate."""

    COMMISSION_ADJUSTMENT = "commission_adjustment"
    QUALIFICATION_THRESHOLD = "qualification_threshold"
    PRICING_STRATEGY = "pricing_strategy"
    TERRITORY_EXPANSION = "territory_expansion"
    TEAM_SCALING = "team_scaling"
    MARKET_CONDITIONS = "market_conditions"
    COMPETITION_RESPONSE = "competition_response"


@dataclass
class ScenarioInput:
    """Input parameters for scenario simulation."""

    scenario_type: ScenarioType
    base_period: str  # "12M", "6M", "3M"
    adjustments: Dict[str, Any]  # Specific changes to simulate
    confidence_level: float = 0.95
    simulation_runs: int = 10000
    time_horizon_months: int = 12


@dataclass
class ScenarioOutcome:
    """Single outcome from Monte Carlo simulation."""

    revenue: float
    deals_closed: int
    avg_deal_value: float
    close_rate: float
    cost_structure: Dict[str, float]
    net_profit: float
    agent_satisfaction: float  # 0-100
    market_share_change: float  # %


@dataclass
class ScenarioResults:
    """Complete results from scenario simulation."""

    scenario_name: str
    input_params: ScenarioInput

    # Statistical results
    mean_outcome: ScenarioOutcome
    confidence_intervals: Dict[str, Tuple[float, float]]
    probability_distributions: Dict[str, List[float]]

    # Comparative analysis
    baseline_comparison: Dict[str, float]  # % change from baseline
    risk_metrics: Dict[str, float]
    success_probability: float  # Prob of positive outcome

    # Insights and recommendations
    key_insights: List[str]
    recommended_actions: List[str]
    risk_factors: List[str]

    calculation_time_ms: float
    generated_at: datetime


class ScenarioSimulationEngine:
    """
    Advanced Monte Carlo simulation engine for business scenario modeling.

    Capabilities:
    - Commission rate optimization modeling
    - Lead qualification threshold analysis
    - Market expansion viability assessment
    - Competitive response planning
    - Team scaling economics
    """

    def __init__(self, analytics_service: Optional[AnalyticsService] = None):
        self.analytics = analytics_service or AnalyticsService()
        self.cache = get_cache_service()

        # Historical data for modeling (loaded from analytics)
        self.historical_deals = None
        self.market_conditions = None
        self.agent_performance = None

    async def run_scenario_simulation(self, scenario_input: ScenarioInput) -> ScenarioResults:
        """
        Run comprehensive Monte Carlo scenario simulation.

        Args:
            scenario_input: Parameters defining the scenario to simulate

        Returns:
            Detailed results with statistical analysis and recommendations
        """
        start_time = datetime.now()

        # Load historical data if not cached
        if not self.historical_deals:
            await self._load_historical_data()

        # Generate baseline model
        baseline_outcomes = await self._generate_baseline_outcomes(scenario_input)

        # Run Monte Carlo simulation
        simulated_outcomes = await self._monte_carlo_simulation(scenario_input, baseline_outcomes)

        # Calculate statistical metrics
        mean_outcome = self._calculate_mean_outcome(simulated_outcomes)
        confidence_intervals = self._calculate_confidence_intervals(simulated_outcomes, scenario_input.confidence_level)

        # Generate insights and recommendations
        insights = await self._generate_insights(scenario_input, simulated_outcomes, baseline_outcomes)
        recommendations = await self._generate_recommendations(scenario_input, simulated_outcomes)
        risk_factors = self._identify_risk_factors(simulated_outcomes)

        # Calculate risk metrics
        risk_metrics = self._calculate_risk_metrics(simulated_outcomes, baseline_outcomes)

        calc_time = (datetime.now() - start_time).total_seconds() * 1000

        return ScenarioResults(
            scenario_name=self._generate_scenario_name(scenario_input),
            input_params=scenario_input,
            mean_outcome=mean_outcome,
            confidence_intervals=confidence_intervals,
            probability_distributions=self._extract_distributions(simulated_outcomes),
            baseline_comparison=self._calculate_baseline_comparison(mean_outcome, baseline_outcomes),
            risk_metrics=risk_metrics,
            success_probability=self._calculate_success_probability(simulated_outcomes, baseline_outcomes),
            key_insights=insights,
            recommended_actions=recommendations,
            risk_factors=risk_factors,
            calculation_time_ms=calc_time,
            generated_at=datetime.now(),
        )

    async def _load_historical_data(self):
        """Load historical performance data for modeling."""
        try:
            # Cache key for historical data
            cache_key = "scenario_historical_data_v1"
            cached_data = await self.cache.get(cache_key)

            if cached_data:
                data = json.loads(cached_data)
                self.historical_deals = data["deals"]
                self.market_conditions = data["market"]
                self.agent_performance = data["agents"]
                return

            # Load from analytics service
            # Simulated historical data - replace with actual analytics calls
            self.historical_deals = await self._generate_simulated_historical_data()
            self.market_conditions = await self._generate_market_conditions()
            self.agent_performance = await self._generate_agent_performance_data()

            # Cache for 24 hours
            await self.cache.set(
                cache_key,
                json.dumps(
                    {"deals": self.historical_deals, "market": self.market_conditions, "agents": self.agent_performance}
                ),
                expire=86400,
            )

        except Exception as e:
            logger.error(f"Error loading historical data: {e}")
            # Use fallback data
            await self._load_fallback_data()

    async def _generate_simulated_historical_data(self) -> List[Dict[str, Any]]:
        """Generate realistic historical deal data for simulation."""
        deals = []
        base_date = datetime.now() - timedelta(days=365)

        for i in range(250):  # 250 deals in past year
            deal_date = base_date + timedelta(days=i * 1.5)

            # Austin market pricing characteristics
            price_base = np.random.lognormal(12.9, 0.3)  # ~$400K average
            price = max(250000, min(2000000, price_base))

            deals.append(
                {
                    "id": f"deal_{i}",
                    "close_date": deal_date.isoformat(),
                    "sale_price": price,
                    "commission_rate": np.random.normal(0.06, 0.005),  # 6% ± 0.5%
                    "days_to_close": int(np.random.gamma(2, 10)),  # ~20 days average
                    "lead_score_at_qualification": np.random.beta(3, 2) * 100,  # Skewed toward higher scores
                    "agent_id": f"agent_{np.random.randint(1, 6)}",
                    "property_type": np.random.choice(["single_family", "condo", "townhome"], p=[0.7, 0.2, 0.1]),
                    "buyer_type": np.random.choice(
                        ["first_time", "investor", "relocating", "upgrading"], p=[0.3, 0.15, 0.25, 0.3]
                    ),
                    "fell_through": np.random.random() < 0.08,  # 8% fallthrough rate
                }
            )

        return deals

    async def _generate_market_conditions(self) -> Dict[str, Any]:
        """Generate current market condition parameters."""
        return {
            "mortgage_rates": 6.3,
            "inventory_months": 2.1,
            "price_appreciation_yoy": 0.045,  # 4.5%
            "competing_agents_local": 450,
            "average_marketing_cost_per_listing": 1200,
            "buyer_sentiment_index": 0.72,  # 72% positive
            "seller_sentiment_index": 0.68,  # 68% positive
        }

    async def _generate_agent_performance_data(self) -> Dict[str, Any]:
        """Generate agent performance metrics."""
        return {
            "jorge_efficiency_multiplier": 1.35,  # 35% above average
            "team_collaboration_bonus": 0.15,  # 15% bonus from team coordination
            "ai_automation_time_savings": 0.42,  # 42% time savings from AI
            "client_satisfaction_score": 4.7,  # /5.0
            "referral_rate": 0.31,  # 31% of clients refer others
        }

    async def _load_fallback_data(self):
        """Load fallback data if analytics unavailable."""
        self.historical_deals = []
        self.market_conditions = {"mortgage_rates": 6.5, "inventory_months": 2.0, "price_appreciation_yoy": 0.04}
        self.agent_performance = {"jorge_efficiency_multiplier": 1.2, "ai_automation_time_savings": 0.3}

    async def _generate_baseline_outcomes(self, scenario_input: ScenarioInput) -> ScenarioOutcome:
        """Generate baseline scenario for comparison."""
        if not self.historical_deals:
            await self._load_historical_data()

        # Calculate baseline metrics from historical data
        total_deals = len([d for d in self.historical_deals if not d["fell_through"]])
        total_revenue = sum(
            d["sale_price"] * d["commission_rate"] for d in self.historical_deals if not d["fell_through"]
        )
        avg_deal_value = total_revenue / total_deals if total_deals > 0 else 0

        # Project forward based on historical performance
        monthly_deals = total_deals / 12
        projected_deals = int(monthly_deals * scenario_input.time_horizon_months)
        projected_revenue = projected_deals * avg_deal_value

        return ScenarioOutcome(
            revenue=projected_revenue,
            deals_closed=projected_deals,
            avg_deal_value=avg_deal_value,
            close_rate=0.92,  # 92% of qualified leads close
            cost_structure={
                "marketing": projected_revenue * 0.03,
                "operations": projected_revenue * 0.12,
                "agent_comp": projected_revenue * 0.65,
            },
            net_profit=projected_revenue * 0.20,
            agent_satisfaction=78.0,
            market_share_change=0.0,
        )

    async def _monte_carlo_simulation(
        self, scenario_input: ScenarioInput, baseline: ScenarioOutcome
    ) -> List[ScenarioOutcome]:
        """Run Monte Carlo simulation with scenario adjustments."""
        outcomes = []

        for run in range(scenario_input.simulation_runs):
            outcome = await self._simulate_single_run(scenario_input, baseline, run)
            outcomes.append(outcome)

        return outcomes

    async def _simulate_single_run(
        self, scenario_input: ScenarioInput, baseline: ScenarioOutcome, run_id: int
    ) -> ScenarioOutcome:
        """Simulate a single scenario outcome with random variations."""

        # Apply scenario-specific adjustments
        if scenario_input.scenario_type == ScenarioType.COMMISSION_ADJUSTMENT:
            return await self._simulate_commission_adjustment(scenario_input, baseline)
        elif scenario_input.scenario_type == ScenarioType.QUALIFICATION_THRESHOLD:
            return await self._simulate_qualification_threshold(scenario_input, baseline)
        else:
            # Default simulation with random variations
            return await self._simulate_baseline_variation(baseline)

    async def _simulate_commission_adjustment(
        self, scenario_input: ScenarioInput, baseline: ScenarioOutcome
    ) -> ScenarioOutcome:
        """Simulate commission rate adjustment scenario."""
        commission_change = scenario_input.adjustments.get("commission_rate_change", 0.0)

        # Model buyer agent response to commission changes
        if commission_change < -0.005:  # Reducing commission by >0.5%
            # Some buyer agents may be less willing to show properties
            agent_willingness = 1.0 - abs(commission_change) * 8  # 8x sensitivity
            deal_flow_impact = max(0.85, agent_willingness)
        else:
            deal_flow_impact = 1.0

        # Calculate new metrics with random variation
        new_deals = int(baseline.deals_closed * deal_flow_impact * np.random.normal(1.0, 0.05))
        new_commission_rate = 0.06 + commission_change
        new_avg_value = baseline.avg_deal_value * np.random.normal(1.0, 0.03)
        new_revenue = new_deals * new_avg_value * new_commission_rate / 0.06  # Adjust for new rate

        # Model agent satisfaction (they may prefer higher commissions)
        satisfaction_impact = 1.0 + (commission_change * 5)  # 5x multiplier
        new_satisfaction = min(100, baseline.agent_satisfaction * satisfaction_impact)

        return ScenarioOutcome(
            revenue=new_revenue,
            deals_closed=new_deals,
            avg_deal_value=new_avg_value,
            close_rate=baseline.close_rate * deal_flow_impact,
            cost_structure={
                "marketing": new_revenue * 0.03,
                "operations": new_revenue * 0.12,
                "agent_comp": new_revenue * 0.65,
            },
            net_profit=new_revenue * 0.20,
            agent_satisfaction=new_satisfaction,
            market_share_change=(deal_flow_impact - 1.0) * 100,
        )

    async def _simulate_qualification_threshold(
        self, scenario_input: ScenarioInput, baseline: ScenarioOutcome
    ) -> ScenarioOutcome:
        """Simulate lead qualification threshold adjustment."""
        threshold_change = scenario_input.adjustments.get("threshold_change", 0)  # Points (e.g., 50 -> 60)

        # Model impact on lead volume and quality
        if threshold_change > 0:  # Raising threshold
            # Fewer leads but higher quality
            volume_impact = 1.0 - (threshold_change * 0.02)  # 2% drop per point
            quality_impact = 1.0 + (threshold_change * 0.015)  # 1.5% quality increase per point
        else:  # Lowering threshold
            # More leads but potentially lower quality
            volume_impact = 1.0 + (abs(threshold_change) * 0.025)
            quality_impact = 1.0 - (abs(threshold_change) * 0.01)

        new_deals = int(baseline.deals_closed * volume_impact * np.random.normal(1.0, 0.04))
        new_close_rate = min(0.98, baseline.close_rate * quality_impact)
        new_avg_value = baseline.avg_deal_value * quality_impact * np.random.normal(1.0, 0.02)

        return ScenarioOutcome(
            revenue=new_deals * new_avg_value,
            deals_closed=new_deals,
            avg_deal_value=new_avg_value,
            close_rate=new_close_rate,
            cost_structure={
                "marketing": (new_deals * new_avg_value) * 0.03,
                "operations": (new_deals * new_avg_value) * 0.10,  # Slightly lower ops cost per deal
                "agent_comp": (new_deals * new_avg_value) * 0.65,
            },
            net_profit=(new_deals * new_avg_value) * 0.22,  # Higher margin from better leads
            agent_satisfaction=baseline.agent_satisfaction
            + (threshold_change * 0.5),  # Agents like higher quality leads
            market_share_change=0.0,
        )

    async def _simulate_baseline_variation(self, baseline: ScenarioOutcome) -> ScenarioOutcome:
        """Add random variation to baseline scenario."""
        return ScenarioOutcome(
            revenue=baseline.revenue * np.random.normal(1.0, 0.08),
            deals_closed=int(baseline.deals_closed * np.random.normal(1.0, 0.06)),
            avg_deal_value=baseline.avg_deal_value * np.random.normal(1.0, 0.05),
            close_rate=max(0.7, baseline.close_rate * np.random.normal(1.0, 0.03)),
            cost_structure={k: v * np.random.normal(1.0, 0.04) for k, v in baseline.cost_structure.items()},
            net_profit=baseline.net_profit * np.random.normal(1.0, 0.12),
            agent_satisfaction=max(0, min(100, baseline.agent_satisfaction * np.random.normal(1.0, 0.02))),
            market_share_change=np.random.normal(0.0, 2.0),
        )

    def _calculate_mean_outcome(self, outcomes: List[ScenarioOutcome]) -> ScenarioOutcome:
        """Calculate mean values across all simulation runs."""
        return ScenarioOutcome(
            revenue=np.mean([o.revenue for o in outcomes]),
            deals_closed=int(np.mean([o.deals_closed for o in outcomes])),
            avg_deal_value=np.mean([o.avg_deal_value for o in outcomes]),
            close_rate=np.mean([o.close_rate for o in outcomes]),
            cost_structure={
                "marketing": np.mean([o.cost_structure["marketing"] for o in outcomes]),
                "operations": np.mean([o.cost_structure["operations"] for o in outcomes]),
                "agent_comp": np.mean([o.cost_structure["agent_comp"] for o in outcomes]),
            },
            net_profit=np.mean([o.net_profit for o in outcomes]),
            agent_satisfaction=np.mean([o.agent_satisfaction for o in outcomes]),
            market_share_change=np.mean([o.market_share_change for o in outcomes]),
        )

    def _calculate_confidence_intervals(
        self, outcomes: List[ScenarioOutcome], confidence_level: float
    ) -> Dict[str, Tuple[float, float]]:
        """Calculate confidence intervals for key metrics."""
        alpha = 1 - confidence_level

        metrics = {
            "revenue": [o.revenue for o in outcomes],
            "deals_closed": [o.deals_closed for o in outcomes],
            "net_profit": [o.net_profit for o in outcomes],
            "close_rate": [o.close_rate for o in outcomes],
        }

        intervals = {}
        for metric, values in metrics.items():
            lower = np.percentile(values, (alpha / 2) * 100)
            upper = np.percentile(values, (1 - alpha / 2) * 100)
            intervals[metric] = (lower, upper)

        return intervals

    def _extract_distributions(self, outcomes: List[ScenarioOutcome]) -> Dict[str, List[float]]:
        """Extract probability distributions for visualization."""
        return {
            "revenue": [o.revenue for o in outcomes],
            "deals_closed": [float(o.deals_closed) for o in outcomes],
            "net_profit": [o.net_profit for o in outcomes],
            "agent_satisfaction": [o.agent_satisfaction for o in outcomes],
        }

    def _calculate_baseline_comparison(
        self, mean_outcome: ScenarioOutcome, baseline: ScenarioOutcome
    ) -> Dict[str, float]:
        """Calculate percentage changes from baseline."""
        return {
            "revenue_change": ((mean_outcome.revenue - baseline.revenue) / baseline.revenue) * 100,
            "deals_change": ((mean_outcome.deals_closed - baseline.deals_closed) / baseline.deals_closed) * 100,
            "profit_change": ((mean_outcome.net_profit - baseline.net_profit) / baseline.net_profit) * 100,
            "satisfaction_change": mean_outcome.agent_satisfaction - baseline.agent_satisfaction,
        }

    def _calculate_risk_metrics(self, outcomes: List[ScenarioOutcome], baseline: ScenarioOutcome) -> Dict[str, float]:
        """Calculate risk and volatility metrics."""
        revenues = [o.revenue for o in outcomes]
        profits = [o.net_profit for o in outcomes]

        return {
            "revenue_volatility": np.std(revenues) / np.mean(revenues),  # Coefficient of variation
            "profit_volatility": np.std(profits) / np.mean(profits),
            "downside_risk": len([r for r in revenues if r < baseline.revenue]) / len(revenues),
            "value_at_risk_95": np.percentile(revenues, 5),  # 5th percentile
            "expected_shortfall": np.mean([r for r in revenues if r < np.percentile(revenues, 5)]),
        }

    def _calculate_success_probability(self, outcomes: List[ScenarioOutcome], baseline: ScenarioOutcome) -> float:
        """Calculate probability of outperforming baseline."""
        successes = len([o for o in outcomes if o.revenue > baseline.revenue])
        return successes / len(outcomes)

    async def _generate_insights(
        self, scenario_input: ScenarioInput, outcomes: List[ScenarioOutcome], baseline: ScenarioOutcome
    ) -> List[str]:
        """Generate AI-powered insights about scenario results."""
        mean_outcome = self._calculate_mean_outcome(outcomes)

        insights = []

        # Revenue impact insight
        revenue_change = ((mean_outcome.revenue - baseline.revenue) / baseline.revenue) * 100
        if abs(revenue_change) > 5:
            direction = "increase" if revenue_change > 0 else "decrease"
            insights.append(
                f"Expected {direction} in annual revenue of {abs(revenue_change):.1f}% ({revenue_change:+.0f}K)"
            )

        # Risk assessment
        volatility = np.std([o.revenue for o in outcomes]) / np.mean([o.revenue for o in outcomes])
        if volatility > 0.15:
            insights.append(
                f"Higher revenue volatility detected ({volatility:.1%}), suggesting increased business risk"
            )
        elif volatility < 0.08:
            insights.append(f"Lower revenue volatility ({volatility:.1%}), indicating more predictable outcomes")

        # Agent satisfaction impact
        satisfaction_change = mean_outcome.agent_satisfaction - baseline.agent_satisfaction
        if abs(satisfaction_change) > 5:
            direction = "improve" if satisfaction_change > 0 else "reduce"
            insights.append(
                f"Scenario likely to {direction} agent satisfaction by {abs(satisfaction_change):.1f} points"
            )

        return insights

    async def _generate_recommendations(
        self, scenario_input: ScenarioInput, outcomes: List[ScenarioOutcome]
    ) -> List[str]:
        """Generate strategic recommendations based on simulation results."""
        recommendations = []

        success_rate = len([o for o in outcomes if o.net_profit > 0]) / len(outcomes)

        if success_rate > 0.85:
            recommendations.append("Strong probability of success - consider implementing this strategy")
        elif success_rate > 0.65:
            recommendations.append("Moderate success probability - test with small-scale pilot first")
        else:
            recommendations.append("High risk scenario - explore alternative approaches")

        # Scenario-specific recommendations
        if scenario_input.scenario_type == ScenarioType.COMMISSION_ADJUSTMENT:
            commission_change = scenario_input.adjustments.get("commission_rate_change", 0)
            if commission_change < -0.005:
                recommendations.append("Consider gradual implementation to minimize buyer agent resistance")

        return recommendations

    def _identify_risk_factors(self, outcomes: List[ScenarioOutcome]) -> List[str]:
        """Identify key risk factors from simulation results."""
        risk_factors = []

        # Check for high variability
        revenues = [o.revenue for o in outcomes]
        if (max(revenues) - min(revenues)) / np.mean(revenues) > 0.5:
            risk_factors.append("High revenue variability - outcomes heavily dependent on market conditions")

        # Check for negative outcomes
        negative_outcomes = len([o for o in outcomes if o.net_profit < 0])
        if negative_outcomes > len(outcomes) * 0.1:
            risk_factors.append(f"{negative_outcomes / len(outcomes):.1%} probability of negative profit outcomes")

        # Check for deal volume risks
        deal_counts = [o.deals_closed for o in outcomes]
        if min(deal_counts) < max(deal_counts) * 0.6:
            risk_factors.append("Significant deal volume variability could impact cash flow")

        return risk_factors

    def _generate_scenario_name(self, scenario_input: ScenarioInput) -> str:
        """Generate human-readable scenario name."""
        base_name = scenario_input.scenario_type.value.replace("_", " ").title()

        if scenario_input.scenario_type == ScenarioType.COMMISSION_ADJUSTMENT:
            rate_change = scenario_input.adjustments.get("commission_rate_change", 0)
            direction = "Increase" if rate_change > 0 else "Decrease"
            return f"{direction} Commission by {abs(rate_change * 100):.1f}%"
        elif scenario_input.scenario_type == ScenarioType.QUALIFICATION_THRESHOLD:
            threshold_change = scenario_input.adjustments.get("threshold_change", 0)
            direction = "Raise" if threshold_change > 0 else "Lower"
            return f"{direction} Qualification Threshold by {abs(threshold_change)} points"
        else:
            return base_name


# Singleton instance
_scenario_engine = None


async def get_scenario_simulation_engine() -> ScenarioSimulationEngine:
    """Get singleton scenario simulation engine."""
    global _scenario_engine
    if _scenario_engine is None:
        _scenario_engine = ScenarioSimulationEngine()
    return _scenario_engine
