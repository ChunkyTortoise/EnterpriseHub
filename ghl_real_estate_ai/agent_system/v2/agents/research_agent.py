"""
Research Agent (V2)
Specialized in property research, market trends, and comparable finding.
Built with PydanticAI and optimized for Gemini 3 Pro.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

from ghl_real_estate_ai.models.jorge_property_models import Property, PropertyAddress, PropertyFeatures, PropertyType
from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher
from ghl_real_estate_ai.services.simulated_mls_feed import get_simulated_mls


# 1. Define the Research Result Schema
class ComparableProperty(BaseModel):
    address: str
    price: float
    bedrooms: int
    bathrooms: float
    sqft: int
    days_on_market: Optional[int] = None
    distance_miles: Optional[float] = None
    source: str = "MLS"


class MarketContext(BaseModel):
    neighborhood: str
    median_price: float
    price_trend: str  # e.g., "appreciating", "stable", "declining"
    inventory_level: str  # e.g., "low", "balanced", "high"
    days_on_market_avg: int
    investment_score: int = Field(ge=0, le=100)
    top_selling_points: List[str]


class ResearchResult(BaseModel):
    subject_property: Optional[Property] = None
    comparables: List[ComparableProperty] = Field(default_factory=list)
    market_context: MarketContext
    summary: str
    raw_research_notes: Optional[str] = None


# 2. Define Dependencies
class ResearchDeps:
    def __init__(self, perplexity_api_key: Optional[str] = None):
        self.perplexity = PerplexityResearcher(api_key=perplexity_api_key)
        self.mls = get_simulated_mls()


# 3. Initialize Gemini Model
# Ensure GOOGLE_API_KEY is in environment
model = GeminiModel("gemini-2.0-flash")

# 4. Create the Research Agent
research_agent = Agent(
    model,
    deps_type=ResearchDeps,
    output_type=ResearchResult,
    system_prompt=(
        "You are an Elite Real Estate Research Analyst. "
        "Your goal is to provide deep, data-driven property and market analysis. "
        "Use your tools to find comparable properties and market trends. "
        "Synthesize raw data into a structured research report for investors."
    ),
)


# 5. Define Tools
@research_agent.tool
async def search_market_data(ctx: RunContext[ResearchDeps], location: str) -> str:
    """Search for real-time market trends and neighborhood info."""
    return await ctx.deps.perplexity.get_market_trends(location)


@research_agent.tool
async def research_neighborhood(ctx: RunContext[ResearchDeps], neighborhood: str, city: str) -> str:
    """Get detailed neighborhood analysis including schools and lifestyle."""
    return await ctx.deps.perplexity.analyze_neighborhood(neighborhood, city)


@research_agent.tool
async def find_comparables(ctx: RunContext[ResearchDeps], address: str, radius_miles: float = 2.0) -> str:
    """Find comparable properties in the area."""
    # In a real system, this would call a real MLS/Zillow API
    # For now, we use Perplexity to 'research' comparables
    topic = f"Recently sold comparable properties for {address} within {radius_miles} miles"
    return await ctx.deps.perplexity.research_topic(topic)


@research_agent.tool
async def get_property_details(ctx: RunContext[ResearchDeps], address: str) -> str:
    """Find public records for a specific property."""
    return await ctx.deps.perplexity.find_property_info(address)


# Example Usage (Commented out):
# async def run_research(address: str):
#     deps = ResearchDeps()
#     result = await research_agent.run(
#         f"Perform full research on {address}. Find 3-5 comps and analyze the local market.",
#         deps=deps
#     )
#     return result.data
