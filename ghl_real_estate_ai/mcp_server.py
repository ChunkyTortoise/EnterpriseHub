
from fastmcp import FastMCP
import asyncio
import os
from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider
from ghl_real_estate_ai.ghl_utils.config import settings

# Create a unified MCP server for EnterpriseHub
mcp = FastMCP("EnterpriseHub")

@mcp.tool()
async def search_perplexity(query: str) -> str:
    """
    Search the web using Perplexity AI.
    Use this for up-to-date real estate news, market trends, or general facts.
    """
    client = LLMClient(provider=LLMProvider.PERPLEXITY)
    try:
        response = await client.agenerate(
            prompt=query,
            system_prompt="You are a real estate market analyst. Provide precise information with citations."
        )
        return response.content
    except Exception as e:
        return f"Error searching Perplexity: {str(e)}"

@mcp.tool()
async def analyze_with_gemini(prompt: str) -> str:
    """
    Use Google Gemini for complex reasoning, long-context analysis, or data synthesis.
    """
    client = LLMClient(provider=LLMProvider.GEMINI)
    try:
        response = await client.agenerate(
            prompt=prompt,
            system_prompt="You are an expert real estate consultant. Analyze the following data deeply."
        )
        return response.content
    except Exception as e:
        return f"Error with Gemini analysis: {str(e)}"

@mcp.tool()
async def get_lead_intelligence(lead_name: str) -> str:
    """
    Get AI-driven insights about a specific lead from the local CRM (GHL).
    """
    # This acts as a bridge to your existing lead intelligence hub
    return f"Claude would now pull behavioral DNA and conversion probability for {lead_name}..."

if __name__ == "__main__":
    mcp.run()
