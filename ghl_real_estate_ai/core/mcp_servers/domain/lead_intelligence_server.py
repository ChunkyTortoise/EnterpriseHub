"""
Lead Intelligence MCP Server
Exposes specialized lead analysis tools for the real estate domain.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from ghl_real_estate_ai.services.enhanced_lead_intelligence import EnhancedLeadIntelligence

# Create the MCP server
mcp = FastMCP("LeadIntelligence")

# Initialize the service (lazy loaded or singleton)
lead_service = EnhancedLeadIntelligence()


@mcp.tool()
async def analyze_lead(lead_name: str, lead_context: Dict[str, Any]) -> str:
    """
    Perform a comprehensive multi-dimensional analysis of a lead.
    Returns strategic summary, behavioral insights, and recommended actions.
    """
    try:
        # Wrap the existing service call
        result = await lead_service.get_comprehensive_lead_analysis(lead_name, lead_context)

        # Format for LLM consumption
        analysis = {
            "final_score": result.final_score,
            "strategic_summary": result.strategic_summary,
            "recommended_actions": result.recommended_actions,
            "behavioral_insights": result.behavioral_insights,
            "conversion_probability": result.ml_conversion_score,
        }
        return json.dumps(analysis, indent=2)
    except Exception as e:
        return f"Error analyzing lead {lead_name}: {str(e)}"


@mcp.tool()
async def get_lead_score_breakdown(lead_context: Dict[str, Any]) -> str:
    """
    Get a detailed breakdown of the lead's score based on Claude's reasoning.
    """
    try:
        result = lead_service.enhanced_scorer.calculate_with_reasoning(lead_context)
        return json.dumps(result, indent=2)
    except Exception as e:
        return f"Error getting score breakdown: {str(e)}"


@mcp.tool()
async def generate_lead_outreach_script(lead_name: str, lead_context: Dict[str, Any], goal: str = "Discovery") -> str:
    """
    Generate a personalized outreach script for a lead based on their behavioral DNA.
    """
    try:
        # Assuming automation_engine has a method for this
        script = await lead_service.automation_engine.generate_script(
            lead_name=lead_name, lead_context=lead_context, script_type="SMS" if goal == "Discovery" else "EMAIL"
        )
        return script
    except Exception as e:
        return f"Error generating script for {lead_name}: {str(e)}"


if __name__ == "__main__":
    mcp.run()
