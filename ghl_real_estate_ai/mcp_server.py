import asyncio
import os

from fastmcp import FastMCP

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.services.data_arbitrage_service import get_data_arbitrage_service
from ghl_real_estate_ai.services.mcp_infrastructure_service import get_mcp_infrastructure_service
from ghl_real_estate_ai.services.negotiation.mia_rvelous import get_mia_optimizer

# Create a unified MCP server for EnterpriseHub
mcp = FastMCP("EnterpriseHub")

# Services
arbitrage = get_data_arbitrage_service()
optimizer = get_mia_optimizer()
infra = get_mcp_infrastructure_service()


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
            system_prompt="You are a real estate market analyst. Provide precise information with citations.",
        )
        return response.content
    except Exception as e:
        return f"Error searching Perplexity: {str(e)}"


@mcp.tool()
async def get_probate_leads(zip_code: str) -> list:
    """Vanguard 1: Get pre-MLS probate leads for a given zip code."""
    return await arbitrage.get_probate_leads(zip_code)


@mcp.tool()
async def calculate_optimal_bids(agent_walkaway: float, buyer_range_min: float, buyer_range_max: float) -> list:
    """Vanguard 3: Use MIA-RVelous algorithm to calculate optimal negotiation bid sequence."""
    return optimizer.calculate_optimal_sequence(agent_walkaway, (buyer_range_min, buyer_range_max))


# Vanguard 4: Core Infrastructure Tools
@mcp.tool()
async def get_lead_history(lead_id: str) -> list:
    """Returns last 30 days of lead interactions."""
    return await infra.get_lead_history(lead_id)


@mcp.tool()
async def analyze_stall_pattern(lead_id: str) -> str:
    """Classifies lead activity: active, stalled_3d, stalled_30d_plus."""
    return await infra.analyze_stall_pattern(lead_id)


@mcp.tool()
async def find_similar_deals(property_value: float, status: str = "closed") -> list:
    """Vector search across similar GHL deals."""
    return await infra.find_similar_deals(property_value, status)


@mcp.tool()
async def predict_close_probability(property_id: str, lead_id: str) -> int:
    """ML score [0-100] based on property and buyer DNA."""
    return await infra.predict_close_probability(property_id, lead_id)


@mcp.tool()
async def extract_objection_keywords(conversation_id: str) -> list:
    """NLP on transcripts to extract key objections (price, timeline, etc.)."""
    return await infra.extract_objection_keywords(conversation_id)


@mcp.tool()
async def get_agent_win_patterns(agent_id: str) -> dict:
    """ML summary of agent win rates by deal type and timing."""
    return await infra.get_agent_win_patterns(agent_id)


@mcp.tool()
async def analyze_with_gemini(prompt: str) -> str:
    """
    Use Google Gemini for complex reasoning, long-context analysis, or data synthesis.
    """
    client = LLMClient(provider=LLMProvider.GEMINI)
    try:
        response = await client.agenerate(
            prompt=prompt, system_prompt="You are an expert real estate consultant. Analyze the following data deeply."
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


@mcp.tool()
async def analyze_lead_intent(conversation_history: list) -> dict:
    """
    Decodes lead intent using the FRS (Financial Readiness) and PCS (Psychological Commitment) frameworks.
    Returns a structured analysis of motivation, timeline, condition, and price realism.
    """
    from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder

    decoder = LeadIntentDecoder()
    # In a real run, we'd pass a contact_id, here we use a mock for MCP
    profile = decoder.analyze_lead("mcp_lead", conversation_history)
    return profile.model_dump()


@mcp.tool()
async def generate_cma_analysis(property_address: str, zestimate: float = 0.0) -> dict:
    """
    Generates a Zillow-Defense CMA report.
    Compares the subject property against recent market comps and explains Zestimate variances.
    """
    from ghl_real_estate_ai.agents.cma_generator import CMAGenerator

    generator = CMAGenerator()
    report = await generator.generate_report(property_address, zestimate)
    return report.dict()


if __name__ == "__main__":
    mcp.run()
