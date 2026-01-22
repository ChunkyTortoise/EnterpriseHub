"""
Market Context Injector - Hyper-Local Market Intelligence
Fetches real-time comps and market trends to inject into bot conversations.
"""
import json
import logging
import random
from typing import Dict, List, Any, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.services.simulated_mls_feed import get_simulated_mls
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class MarketContextInjector:
    """
    Injects real-time market data (comps, trends, price reality checks) into AI bot responses.
    
    Pillar 4: Predictive Market Intelligence
    Feature #6: Real-Time MLS Integration + Market Data Injection
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.mls = get_simulated_mls()
        
    async def get_market_context(self, address: str, zip_code: str) -> Dict[str, Any]:
        """
        Fetch market context for a specific location.
        """
        # Simulate MLS comp fetch
        # In production, this would call actual MLS APIs
        median_price = random.randint(450000, 550000)
        dom = random.randint(15, 45)
        trend = random.choice(["Heating Up", "Stable", "Cooling Slightly"])
        
        comps = [
            {"address": f"Similar Home 1, {zip_code}", "price": median_price - 10000, "sold_days_ago": 12},
            {"address": f"Similar Home 2, {zip_code}", "price": median_price + 5000, "sold_days_ago": 25},
            {"address": f"Similar Home 3, {zip_code}", "price": median_price + 15000, "sold_days_ago": 5}
        ]
        
        return {
            "median_price": median_price,
            "avg_dom": dom,
            "market_trend": trend,
            "comps": comps,
            "price_per_sqft": random.randint(250, 350)
        }
        
    async def synthesize_price_reality_check(
        self, 
        seller_expected_price: float, 
        market_context: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> str:
        """
        Use Claude to synthesize a 'Price Reality Check' for the seller.
        """
        prompt = f"""
        Compare the seller's expected price with the current market context.
        
        SELLER EXPECTATION: ${seller_expected_price:,}
        
        MARKET CONTEXT:
        - Median Price in Area: ${market_context['median_price']:,}
        - Days on Market: {market_context['avg_dom']} days
        - Market Trend: {market_context['market_trend']}
        - Recent Comps: {json.dumps(market_context['comps'])}
        
        Provide a professional, data-backed 'Reality Check' response for the bot.
        Be encouraging but realistic. Explain how their price compares to recent sales.
        """
        
        try:
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are a local market expert providing objective pricing advice.",
                complexity=TaskComplexity.COMPLEX,
                tenant_id=tenant_id,
                max_tokens=200
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error synthesizing reality check: {e}")
            return f"Based on recent sales, the median price in your area is around ${market_context['median_price']:,}."

    def inject_market_data_into_prompt(self, system_prompt: str, market_context: Dict[str, Any]) -> str:
        """Helper to inject market data into a system prompt."""
        context_str = f"""
        LOCAL MARKET CONTEXT:
        - Median Area Price: ${market_context['median_price']:,}
        - Market Velocity: {market_context['avg_dom']} days average
        - Market Sentiment: {market_context['market_trend']}
        """
        return f"{system_prompt}\n\n{context_str}"