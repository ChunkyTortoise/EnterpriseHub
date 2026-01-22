"""
Perplexity Researcher Service - Deep research and market intelligence.

Uses Perplexity AI to perform real-time web research and synthesize 
data-driven insights for real estate professionals.
"""
import asyncio
from typing import Any, Dict, List, Optional
from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider
from ghl_real_estate_ai.ghl_utils.config import settings
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class PerplexityResearcher:
    """
    Service for performing deep research using Perplexity AI.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Perplexity researcher.
        
        Args:
            api_key: Optional API key. Defaults to settings.perplexity_api_key.
        """
        self.client = LLMClient(
            provider="perplexity",
            api_key=api_key or settings.perplexity_api_key
        )
        self.enabled = self.client.is_available()
        if not self.enabled:
            logger.warning("PerplexityResearcher disabled: PERPLEXITY_API_KEY not set")

    async def research_topic(self, topic: str, context: Optional[str] = None) -> str:
        """
        Perform deep research on a general topic. 
        
        Args:
            topic: The research topic or question.
            context: Additional context to guide the research.
            
        Returns:
            Synthesized research report.
        """
        if not self.enabled:
            return "Perplexity research is currently unavailable."

        system_prompt = (
            "You are an expert real estate research analyst. "
            "Your goal is to provide deep, data-driven insights with citations. "
            "Be objective, thorough, and professional."
        )
        
        prompt = f"Research the following topic: {topic}"
        if context:
            prompt += f"\n\nAdditional Context: {context}"
            
        try:
            response = await self.client.agenerate(
                prompt=prompt,
                system_prompt=system_prompt,
                max_tokens=4000
            )
            return response.content
        except Exception as e:
            logger.error(f"Research failed: {e}")
            return f"Error during research: {str(e)}"

    async def get_market_trends(self, location: str, period: str = "current") -> str:
        """
        Get real-time market trends for a specific location.
        """
        topic = f"Real estate market trends in {location} for {period}"
        context = "Focus on median prices, inventory levels, days on market, and mortgage rate impacts."
        return await self.research_topic(topic, context)

    async def analyze_neighborhood(self, neighborhood: str, city: str) -> str:
        """
        Analyze a specific neighborhood's lifestyle, schools, and investment potential.
        """
        topic = f"Detailed analysis of the {neighborhood} neighborhood in {city}"
        context = "Include school ratings, local amenities, safety, and recent property value appreciation."
        return await self.research_topic(topic, context)

    async def find_property_info(self, address: str) -> str:
        """
        Search for public information about a specific property.
        """
        topic = f"Public records and information for property at {address}"
        context = "Find square footage, lot size, last sold price, year built, and any unique architectural features."
        return await self.research_topic(topic, context)

    async def find_high_yield_markets(self, criteria: str = "net yield > 15%") -> List[Dict[str, Any]]:
        """
        Phase 5: Dynamic Market Expansion.
        Uses Perplexity to find new high-yield markets.
        """
        topic = f"Find 3-5 US zip codes with high real estate investment potential meeting criteria: {criteria}"
        context = "Focus on net yield, cash-on-cash return, and stable market indicators. Return as structured list if possible."
        
        report = await self.research_topic(topic, context)
        # In a real system, we'd use Claude to parse this report into structured JSON
        # For now, we return the report content as a 'reasoning' block
        return [{"zip_code": "unknown", "reasoning": report}]

    async def refresh_market_data(self, location: str):
        """
        Phase 5: Self-Healing Data Pipeline (The Hunter).
        Refreshes market data in RAG engine.
        """
        logger.info(f"Refreshing market data for {location}...")
        trends = await self.get_market_trends(location)
        # Integration with RAG engine would go here:
        # await rag_engine.update_document(f"market_trends_{location}", trends)
        return trends

def get_perplexity_researcher() -> PerplexityResearcher:
    """Get global PerplexityResearcher instance."""
    return PerplexityResearcher()
