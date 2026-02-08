"""
Negotiation Intelligence MCP Server
Exposes specialized negotiation tools for real estate deal orchestration.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from ghl_real_estate_ai.services.ai_negotiation_partner import AINegotiationPartner

# Create the MCP server
mcp = FastMCP("NegotiationIntelligence")

# Initialize the service
negotiation_partner = AINegotiationPartner()


@mcp.tool()
async def analyze_negotiation(
    listing_id: str, buyer_context: Dict[str, Any], listing_history: List[Dict[str, Any]]
) -> str:
    """
    Perform a comprehensive analysis of a negotiation situation.
    Returns seller psychology, market leverage, and win probability.
    """
    try:
        # Create a request object if the service expects it, or pass parameters
        # For simplicity, assuming the service has a direct orchestrator method
        analysis = await negotiation_partner.generate_comprehensive_analysis(
            listing_id=listing_id, buyer_context=buyer_context, listing_history=listing_history
        )
        return json.dumps(analysis, indent=2, default=str)
    except Exception as e:
        return f"Error analyzing negotiation: {str(e)}"


@mcp.tool()
async def get_negotiation_strategy(negotiation_state: Dict[str, Any], leverage_factors: Dict[str, Any]) -> str:
    """
    Generate the optimal negotiation strategy based on current state and leverage.
    """
    try:
        strategy = await negotiation_partner.strategy_engine.generate_strategy(
            state=negotiation_state, leverage=leverage_factors
        )
        return json.dumps(strategy, indent=2, default=str)
    except Exception as e:
        return f"Error generating strategy: {str(e)}"


@mcp.tool()
async def get_realtime_coaching(current_chat_history: List[Dict[str, str]], negotiation_id: str) -> str:
    """
    Provide real-time coaching for an active negotiation based on message history.
    """
    try:
        coaching = await negotiation_partner.get_real_time_coaching(
            history=current_chat_history, negotiation_id=negotiation_id
        )
        return json.dumps(coaching, indent=2, default=str)
    except Exception as e:
        return f"Error getting coaching: {str(e)}"


if __name__ == "__main__":
    mcp.run()
