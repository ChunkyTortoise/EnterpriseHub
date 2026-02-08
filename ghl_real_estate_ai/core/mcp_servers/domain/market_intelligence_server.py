"""
Market Intelligence MCP Server
Exposes specialized market analysis tools for national and local real estate markets.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from ghl_real_estate_ai.services.national_market_intelligence import NationalMarketIntelligence

# Create the MCP server
mcp = FastMCP("MarketIntelligence")

# Initialize the service
market_service = NationalMarketIntelligence()


@mcp.tool()
async def get_market_analysis(market_id: str) -> str:
    """
    Get a comprehensive analysis of a specific real estate market.
    Returns metrics, trends, and opportunity scores.
    """
    try:
        # Assuming the service has a method like get_market_metrics
        metrics = await market_service.get_market_metrics(market_id)
        # Convert dataclass/object to dict for JSON serialization
        if hasattr(metrics, "__dict__"):
            return json.dumps(metrics.__dict__, indent=2, default=str)
        return json.dumps(metrics, indent=2, default=str)
    except Exception as e:
        return f"Error getting analysis for market {market_id}: {str(e)}"


@mcp.tool()
async def compare_markets(market_ids: List[str]) -> str:
    """
    Compare multiple real estate markets side-by-side.
    """
    try:
        comparison = await market_service.get_cross_market_analysis(market_ids)
        return json.dumps(comparison, indent=2, default=str)
    except Exception as e:
        return f"Error comparing markets {market_ids}: {str(e)}"


@mcp.tool()
async def get_opportunity_score(market_id: str) -> str:
    """
    Calculate the opportunity score for a market based on current trends and data.
    """
    try:
        score_data = await market_service.analyze_market_opportunity(market_id)
        return json.dumps(score_data, indent=2, default=str)
    except Exception as e:
        return f"Error calculating opportunity score for {market_id}: {str(e)}"


if __name__ == "__main__":
    mcp.run()
