"""
Commission Forecasting Engine

Revenue and commission prediction from pipeline data, seasonal modeling,
Monte Carlo simulation, and executive reporting summaries.

Usage::

    engine = get_forecast_engine()
    forecast = await engine.forecast_revenue(
        pipeline=pipeline_data,
        horizon_months=3,
    )
    executive = await engine.generate_executive_summary(forecast)
"""

import logging
import math
import random
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Rancho Cucamonga seasonal factors (index by month 1-12)
SEASONAL_FACTORS = {
    1: 0.75,   # January — post-holiday slowdown
    2: 0.80,   # February — early spring stirrings
    3: 0.95,   # March — spring market begins
    4: 1.10,   # April — peak listing season
    5: 1.15,   # May — highest activity
    6: 1.10,   # June — strong but cooling
    7: 1.00,   # July — summer plateau
    8: 0.95,   # August — back-to-school dip
    9: 0.90,   # September — fall stabilisation
    10: 0.85,  # October — seasonal wind-down
    11: 0.78,  # November — holiday slowdown
    12: 0.70,  # December — year-end low
}

# Commission rate bands
DEFAULT_COMMISSION_RATE = 0.025  # 2.5% per side
LUXURY_COMMISSION_RATE = 0.03   # 3% for luxury ($1.2M+)
LUXURY_THRESHOLD = 1_200_000


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

class DealStage(Enum):
    PROSPECT = "prospect"
    QUALIFIED = "qualified"
    SHOWING = "showing"
    OFFER = "offer"
    UNDER_CONTRACT = "under_contract"
    CLOSED = "closed"


# Stage-to-close probability
STAGE_PROBABILITIES: Dict[DealStage, float] = {
    DealStage.PROSPECT: 0.10,
    DealStage.QUALIFIED: 0.25,
    DealStage.SHOWING: 0.40,
    DealStage.OFFER: 0.65,
    DealStage.UNDER_CONTRACT: 0.90,
    DealStage.CLOSED: 1.00,
}


@dataclass
class PipelineDeal:
    """Single deal in the pipeline."""
    deal_id: str
    contact_name: str
    property_value: int
    stage: DealStage
    expected_close_month: int  # 1-12
    deal_type: str = "buyer"  # buyer or seller
    commission_rate: Optional[float] = None


@dataclass
class MonthlyForecast:
    """Revenue forecast for a single month."""
    month: int  # 1-12
    expected_revenue: float
    weighted_pipeline: float
    deal_count: int
    seasonal_factor: float
    confidence_low: float
    confidence_high: float


@dataclass
class RevenueForecast:
    """Complete revenue forecast."""
    total_expected: float
    total_weighted: float
    monthly_forecasts: List[MonthlyForecast]
    deal_count: int
    avg_deal_value: float
    avg_commission: float
    forecast_horizon_months: int
    generated_at: float = field(default_factory=time.time)


@dataclass
class MonteCarloResult:
    """Monte Carlo simulation result."""
    simulations: int
    mean_revenue: float
    median_revenue: float
    std_dev: float
    percentile_10: float
    percentile_25: float
    percentile_75: float
    percentile_90: float
    worst_case: float
    best_case: float
    probability_above_target: float


@dataclass
class ExecutiveSummary:
    """Executive reporting summary."""
    total_pipeline_value: int
    weighted_pipeline_value: float
    expected_commission: float
    forecast_confidence: str  # "high", "moderate", "low"
    top_deals: List[Dict[str, Any]]
    monthly_breakdown: List[Dict[str, Any]]
    risk_factors: List[str]
    opportunities: List[str]
    recommendation: str


# ---------------------------------------------------------------------------
# Engine
# ---------------------------------------------------------------------------

class CommissionForecastEngine:
    """
    Revenue and commission forecasting with Monte Carlo simulation,
    seasonal adjustment, and executive reporting.
    """

    def __init__(self, commission_rate: float = DEFAULT_COMMISSION_RATE):
        self.default_rate = commission_rate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def forecast_revenue(
        self,
        pipeline: List[Dict[str, Any]],
        horizon_months: int = 3,
        current_month: Optional[int] = None,
    ) -> RevenueForecast:
        """
        Generate weighted revenue forecast from pipeline data.
        """
        deals = [self._parse_deal(d) for d in pipeline]
        if current_month is None:
            import datetime
            current_month = datetime.datetime.now().month

        monthly: Dict[int, List[PipelineDeal]] = {}
        for deal in deals:
            month = deal.expected_close_month
            monthly.setdefault(month, []).append(deal)

        forecasts: List[MonthlyForecast] = []
        total_expected = 0.0
        total_weighted = 0.0

        for offset in range(horizon_months):
            month = ((current_month - 1 + offset) % 12) + 1
            month_deals = monthly.get(month, [])
            seasonal = SEASONAL_FACTORS.get(month, 1.0)

            expected = 0.0
            weighted = 0.0

            for deal in month_deals:
                comm = self._deal_commission(deal)
                prob = STAGE_PROBABILITIES.get(deal.stage, 0.10)
                expected += comm
                weighted += comm * prob * seasonal

            # Confidence interval (simple +/- 20%)
            low = weighted * 0.80
            high = weighted * 1.20

            forecasts.append(MonthlyForecast(
                month=month,
                expected_revenue=round(expected, 2),
                weighted_pipeline=round(weighted, 2),
                deal_count=len(month_deals),
                seasonal_factor=seasonal,
                confidence_low=round(low, 2),
                confidence_high=round(high, 2),
            ))

            total_expected += expected
            total_weighted += weighted

        avg_value = (
            sum(d.property_value for d in deals) / len(deals)
            if deals else 0
        )
        avg_comm = total_expected / len(deals) if deals else 0

        return RevenueForecast(
            total_expected=round(total_expected, 2),
            total_weighted=round(total_weighted, 2),
            monthly_forecasts=forecasts,
            deal_count=len(deals),
            avg_deal_value=round(avg_value, 2),
            avg_commission=round(avg_comm, 2),
            forecast_horizon_months=horizon_months,
        )

    async def monte_carlo_simulation(
        self,
        pipeline: List[Dict[str, Any]],
        simulations: int = 1000,
        target_revenue: float = 0.0,
    ) -> MonteCarloResult:
        """
        Run Monte Carlo simulation on pipeline to model revenue distribution.
        """
        deals = [self._parse_deal(d) for d in pipeline]
        results: List[float] = []

        for _ in range(simulations):
            sim_revenue = 0.0
            for deal in deals:
                prob = STAGE_PROBABILITIES.get(deal.stage, 0.10)
                seasonal = SEASONAL_FACTORS.get(deal.expected_close_month, 1.0)
                adjusted_prob = prob * seasonal

                # Bernoulli trial: does the deal close?
                if random.random() < adjusted_prob:
                    comm = self._deal_commission(deal)
                    # Add variance: +/- 10% of commission
                    variance = comm * random.uniform(-0.10, 0.10)
                    sim_revenue += comm + variance

            results.append(sim_revenue)

        results.sort()
        n = len(results)
        mean = sum(results) / n
        median = results[n // 2]
        variance = sum((r - mean) ** 2 for r in results) / n
        std_dev = math.sqrt(variance)

        above_target = sum(1 for r in results if r >= target_revenue) / n if target_revenue > 0 else 0.0

        return MonteCarloResult(
            simulations=simulations,
            mean_revenue=round(mean, 2),
            median_revenue=round(median, 2),
            std_dev=round(std_dev, 2),
            percentile_10=round(results[int(n * 0.10)], 2),
            percentile_25=round(results[int(n * 0.25)], 2),
            percentile_75=round(results[int(n * 0.75)], 2),
            percentile_90=round(results[int(n * 0.90)], 2),
            worst_case=round(results[0], 2),
            best_case=round(results[-1], 2),
            probability_above_target=round(above_target, 4),
        )

    async def generate_executive_summary(
        self,
        forecast: RevenueForecast,
        monte_carlo: Optional[MonteCarloResult] = None,
    ) -> ExecutiveSummary:
        """
        Generate executive reporting summary from forecast data.
        """
        total_pipeline = int(forecast.avg_deal_value * forecast.deal_count)

        # Determine confidence level
        if forecast.deal_count >= 10 and forecast.total_weighted > 50_000:
            confidence = "high"
        elif forecast.deal_count >= 5:
            confidence = "moderate"
        else:
            confidence = "low"

        # Monthly breakdown
        monthly = [
            {
                "month": f.month,
                "expected": f.expected_revenue,
                "weighted": f.weighted_pipeline,
                "deals": f.deal_count,
                "seasonal": f.seasonal_factor,
            }
            for f in forecast.monthly_forecasts
        ]

        # Top deals (highest expected commission months)
        top = sorted(
            forecast.monthly_forecasts,
            key=lambda f: f.weighted_pipeline,
            reverse=True,
        )[:3]
        top_deals = [
            {"month": t.month, "weighted_revenue": t.weighted_pipeline, "deals": t.deal_count}
            for t in top
        ]

        # Risk factors
        risks: List[str] = []
        low_months = [f for f in forecast.monthly_forecasts if f.seasonal_factor < 0.80]
        if low_months:
            risks.append(f"{len(low_months)} months in low-season period (seasonal factor < 0.80)")
        if forecast.deal_count < 5:
            risks.append("Small pipeline size increases forecast variance")
        if monte_carlo and monte_carlo.std_dev > monte_carlo.mean_revenue * 0.5:
            risks.append("High revenue variance detected in Monte Carlo simulation")

        # Opportunities
        opportunities: List[str] = []
        high_months = [f for f in forecast.monthly_forecasts if f.seasonal_factor >= 1.05]
        if high_months:
            opportunities.append(f"{len(high_months)} months in peak season — maximise listing activity")
        if forecast.avg_deal_value > LUXURY_THRESHOLD:
            opportunities.append("Luxury segment deals with higher commission potential")

        # Recommendation
        if confidence == "high":
            rec = "Pipeline is strong. Focus on converting qualified leads to showings."
        elif confidence == "moderate":
            rec = "Pipeline needs growth. Increase prospecting in high-appreciation neighborhoods."
        else:
            rec = "Pipeline is thin. Prioritise lead generation and absentee owner outreach."

        return ExecutiveSummary(
            total_pipeline_value=total_pipeline,
            weighted_pipeline_value=round(forecast.total_weighted, 2),
            expected_commission=round(forecast.total_expected, 2),
            forecast_confidence=confidence,
            top_deals=top_deals,
            monthly_breakdown=monthly,
            risk_factors=risks,
            opportunities=opportunities,
            recommendation=rec,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _deal_commission(self, deal: PipelineDeal) -> float:
        rate = deal.commission_rate or self.default_rate
        if deal.property_value >= LUXURY_THRESHOLD:
            rate = max(rate, LUXURY_COMMISSION_RATE)
        return deal.property_value * rate

    @staticmethod
    def _parse_deal(data: Dict[str, Any]) -> PipelineDeal:
        stage_str = data.get("stage", "prospect")
        try:
            stage = DealStage(stage_str)
        except ValueError:
            stage = DealStage.PROSPECT

        return PipelineDeal(
            deal_id=data.get("deal_id", "unknown"),
            contact_name=data.get("contact_name", ""),
            property_value=int(data.get("property_value", 0)),
            stage=stage,
            expected_close_month=int(data.get("expected_close_month", 1)),
            deal_type=data.get("deal_type", "buyer"),
            commission_rate=data.get("commission_rate"),
        )


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_engine: Optional[CommissionForecastEngine] = None


def get_forecast_engine() -> CommissionForecastEngine:
    global _engine
    if _engine is None:
        _engine = CommissionForecastEngine()
    return _engine
