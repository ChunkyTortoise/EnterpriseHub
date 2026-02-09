"""
Analytics Intelligence MCP Server
Exposes specialized analytics and ROI tracking tools for the AI platform.
"""

import json

from fastmcp import FastMCP

from ghl_real_estate_ai.services.analytics_service import AnalyticsService

# Create the MCP server
mcp = FastMCP("AnalyticsIntelligence")

# Initialize the service
analytics_service = AnalyticsService()


@mcp.tool()
async def get_daily_summary(location_id: str) -> str:
    """
    Get a summary of AI activity and performance for a specific location today.
    """
    try:
        summary = await analytics_service.get_daily_summary(location_id)
        return json.dumps(summary, indent=2, default=str)
    except Exception as e:
        return f"Error getting daily summary: {str(e)}"


@mcp.tool()
async def get_conversion_metrics(location_id: str, days: int = 30) -> str:
    """
    Get lead conversion metrics and trends over a specified period.
    """
    try:
        # Assuming the service has a method for this
        metrics = await analytics_service.get_conversion_metrics(location_id, days=days)
        return json.dumps(metrics, indent=2, default=str)
    except Exception as e:
        return f"Error getting conversion metrics: {str(e)}"


@mcp.tool()
async def get_llm_roi(location_id: str) -> str:
    """
    Calculate the ROI of AI operations, including cost savings from caching and automation.
    """
    try:
        roi_data = await analytics_service.get_llm_roi_analysis(location_id)
        return json.dumps(roi_data, indent=2, default=str)
    except Exception as e:
        return f"Error calculating ROI: {str(e)}"


if __name__ == "__main__":
    mcp.run()
