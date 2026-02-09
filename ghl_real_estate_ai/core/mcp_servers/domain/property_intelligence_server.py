"""
Property Intelligence MCP Server
Exposes specialized property matching and analysis tools using Claude Semantic Matching.
"""

import json
from typing import Any, Dict

from fastmcp import FastMCP

from ghl_real_estate_ai.services.claude_semantic_property_matcher import ClaudeSemanticPropertyMatcher

# Create the MCP server
mcp = FastMCP("PropertyIntelligence")

# Initialize the service
property_service = ClaudeSemanticPropertyMatcher()


@mcp.tool()
async def find_lifestyle_matches(lead_profile: Dict[str, Any], limit: int = 5) -> str:
    """
    Find property matches based on the lead's lifestyle profile and psychological DNA.
    """
    try:
        matches = await property_service.find_lifestyle_matches(lead_profile, limit=limit)
        # Convert objects to dicts
        result = []
        for match in matches:
            if hasattr(match, "__dict__"):
                result.append(match.__dict__)
            else:
                result.append(match)
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return f"Error finding matches: {str(e)}"


@mcp.tool()
async def analyze_property_fit(property_data: Dict[str, Any], lead_profile: Dict[str, Any]) -> str:
    """
    Perform a deep psychological analysis of how well a specific property fits a lead.
    """
    try:
        # Extract lifestyle profile first if needed or assume analyze_property_match handles it
        lifestyle_profile = await property_service._extract_lifestyle_profile(lead_profile)
        match_analysis = await property_service._analyze_property_match(property_data, lead_profile, lifestyle_profile)

        if hasattr(match_analysis, "__dict__"):
            return json.dumps(match_analysis.__dict__, indent=2, default=str)
        return json.dumps(match_analysis, indent=2, default=str)
    except Exception as e:
        return f"Error analyzing property fit: {str(e)}"


@mcp.tool()
async def predict_life_transitions(lead_profile: Dict[str, Any]) -> str:
    """
    Predict future life transitions for a lead to anticipate their future property needs.
    """
    try:
        lifestyle_profile = await property_service._extract_lifestyle_profile(lead_profile)
        transitions = await property_service.predict_life_transitions(lifestyle_profile)
        return json.dumps(transitions, indent=2, default=str)
    except Exception as e:
        return f"Error predicting transitions: {str(e)}"


if __name__ == "__main__":
    mcp.run()
