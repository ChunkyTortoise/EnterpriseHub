"""
Market Intelligence Weekly Digest - White-Label Agent Product
Generates narrative summaries of market trends for automated client outreach.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.services.neighborhood_insights import NeighborhoodInsightsEngine
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class MarketDigestGenerator:
    """
    Generates weekly market intelligence digests for GHL agencies.
    
    Pillar 4: Predictive Market Intelligence
    Feature #7: Market Intelligence Weekly Digest (White-Label)
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.neighborhood_engine = NeighborhoodInsightsEngine()
        
    async def generate_weekly_digest(
        self, 
        market_name: str, 
        zip_codes: List[str],
        agency_branding: Dict[str, str],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a weekly market digest for an agency.
        """
        # Step 1: Aggregate data for zips
        market_data = []
        for zip_code in zip_codes[:3]: # Limit to top 3 for digest
            profile = self.neighborhood_engine.get_neighborhood_profile(zip_code=zip_code)
            market_data.append(profile['market_trends'])
            
        # Step 2: Synthesize narrative
        prompt = f"""
        Generate a 'Weekly Market Intelligence Digest' for real estate clients in {market_name}.
        
        MARKET DATA:
        {json.dumps(market_data, indent=2)}
        
        AGENCY BRANDING:
        {json.dumps(agency_branding, indent=2)}
        
        The digest should include:
        1. A catchy headline.
        2. 'The Big Picture' summary of current trends.
        3. Neighborhood highlights for the specific ZIPs.
        4. A 'Pro-Tip' for sellers this week.
        5. A 'Pro-Tip' for buyers this week.
        
        Tone: Professional, expert, and authoritative yet accessible.
        Use Jorge's style: Direct and data-driven.
        """
        
        try:
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are a senior market analyst at a top-tier real estate brokerage.",
                complexity=TaskComplexity.COMPLEX,
                tenant_id=tenant_id,
                max_tokens=1500
            )
            
            return {
                "market": market_name,
                "generated_at": datetime.now().isoformat(),
                "content": response.content.strip(),
                "agency": agency_branding.get("name", "Lyrio AI"),
                "status": "ready_for_email"
            }
        except Exception as e:
            logger.error(f"Error generating market digest: {e}")
            return {"error": str(e)}
