"""
Analysis Agent (V2)
Specialized in investment scoring, financial projections, and risk assessment.
Built with PydanticAI and optimized for Gemini 3 Pro.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

from ghl_real_estate_ai.models.jorge_property_models import ConfidenceLevel, MatchReasoning
from ghl_real_estate_ai.services.competitive_intelligence_hub import IntelligenceType, get_competitive_intelligence_hub
from ghl_real_estate_ai.services.roi_calculator_service import roi_calculator


# 1. Define the Analysis Result Schema
class FinancialProjections(BaseModel):
    estimated_monthly_rent: float
    annual_gross_income: float
    estimated_expenses: float
    net_operating_income: float
    cap_rate: float
    cash_on_cash_return: float
    appreciation_projection_5yr: float
    ten_year_equity_projection: float


class RiskAssessment(BaseModel):
    market_risk: int = Field(ge=0, le=10)  # 0-10 scale
    property_risk: int = Field(ge=0, le=10)
    liquidity_risk: int = Field(ge=0, le=10)
    mitigation_strategies: List[str]


class CompetitiveLandscape(BaseModel):
    competitor_count: int
    threat_level: str  # e.g., "Low", "Medium", "High"
    market_share_delta: float
    competitor_pricing_avg: float
    strategic_advantage: str


class AnalysisResult(BaseModel):
    investment_score: int = Field(ge=0, le=100)
    financials: FinancialProjections
    risk: RiskAssessment
    competitive_landscape: Optional[CompetitiveLandscape] = None
    reasoning: MatchReasoning
    confidence: ConfidenceLevel
    verdict: str  # e.g., "Strong Buy", "Hold", "Pass"


# 2. Define Dependencies
class AnalysisDeps:
    def __init__(self):
        self.roi_calc = roi_calculator
        self.competitive_hub = get_competitive_intelligence_hub()


# 3. Initialize Gemini Model
model = GeminiModel("gemini-2.0-flash")

# 4. Create the Analysis Agent
analysis_agent = Agent(
    model,
    deps_type=AnalysisDeps,
    output_type=AnalysisResult,
    system_prompt=(
        "You are an Elite Real Estate Investment Analyst. "
        "Your goal is to perform rigorous financial analysis on property data. "
        "Calculate Cap Rate, ROI, and Cash-on-Cash returns accurately. "
        "Use the 10-year projection tool for long-term equity estimates. "
        "Assess risks objectively and provide actionable investment reasoning. "
        "Integrate competitive intelligence to understand market positioning. "
        "Always output structured financial and competitive data."
    ),
)


# 5. Define Tools
@analysis_agent.tool
def get_long_term_projection(
    ctx: RunContext[AnalysisDeps], price: float, rent: float, expenses: float
) -> Dict[str, Any]:
    """Calculate 10-year growth and cash flow projections."""
    projections = ctx.deps.roi_calc.calculate_10yr_projection(
        purchase_price=price, down_payment_pct=0.20, monthly_rent=rent, annual_expenses=expenses
    )
    return {"projections": [p.dict() for p in projections]}


@analysis_agent.tool
def calculate_cap_rate(ctx: RunContext[AnalysisDeps], price: float, annual_noi: float) -> float:
    """Calculate the capitalization rate for a property."""
    if price <= 0:
        return 0.0
    return (annual_noi / price) * 100


@analysis_agent.tool
def estimate_rental_income(ctx: RunContext[AnalysisDeps], neighborhood: str, sqft: int, beds: int) -> float:
    """Estimate monthly rental income based on property features and location."""
    # Simplified mock logic
    base_rate = 1.5  # $1.50 per sqft
    if "luxury" in neighborhood.lower():
        base_rate = 3.5
    return sqft * base_rate + (beds * 200)


@analysis_agent.tool
def assess_market_stability(ctx: RunContext[AnalysisDeps], city: str) -> str:
    """Get a qualitative assessment of market stability for a city."""
    return f"Market in {city} is currently stable with a 4.2% annual growth rate."


@analysis_agent.tool
async def get_competitive_intelligence(ctx: RunContext[AnalysisDeps], market: str) -> Dict[str, Any]:
    """Fetch competitive intelligence for a specific market or area."""
    # In a real scenario, this would search for competitors in the market
    # For now we use the hub to get performance metrics as a proxy
    metrics = await ctx.deps.competitive_hub.get_performance_metrics()

    # Simulate a benchmark for the market
    benchmark = {
        "market": market,
        "competitor_count": metrics.get("total_competitors", 5),
        "avg_market_share": 15.5,
        "threat_level": "Medium",
        "recent_alerts": metrics.get("active_alerts", 2),
    }
    return benchmark
