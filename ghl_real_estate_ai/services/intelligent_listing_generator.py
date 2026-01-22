"""
Intelligent Listing Generator - AI Property Descriptions with Market Context
Generates high-conversion listing descriptions using Claude and real-time market data.
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.services.neighborhood_insights import NeighborhoodInsightsEngine
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class IntelligentListingGenerator:
    """
    Generates compelling listing descriptions injected with hyper-local market context.
    
    Pillar 3: SaaS Monetization
    Feature #3: AI-Generated Listing Descriptions (White-Label SaaS Product)
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.neighborhood_engine = NeighborhoodInsightsEngine()
        
    async def generate_enhanced_listings(
        self, 
        property_data: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate multiple listing variations with market context.
        
        Args:
            property_data: Basic property details (address, beds, baths, sqft, price, features)
            tenant_id: Optional tenant ID
            
        Returns:
            List of listing variations (tone, target, text, context).
        """
        # Step 1: Fetch hyper-local market context
        market_context = self.neighborhood_engine.get_neighborhood_profile(
            address=property_data.get("address"),
            zip_code=property_data.get("zip_code")
        )
        
        # Step 2: Prepare variations
        variations = [
            {
                "tone": "emotional",
                "target": "owner-occupants",
                "focus": "family appeal, lifestyle, schools, community"
            },
            {
                "tone": "analytical",
                "target": "investors",
                "focus": "ROI, market positioning, price per sqft, rental potential"
            },
            {
                "tone": "premium",
                "target": "luxury",
                "focus": "architectural features, high-end finishes, exclusivity"
            }
        ]
        
        results = []
        for var in variations:
            listing_text = await self._generate_listing_variation(
                property_data=property_data,
                market_context=market_context,
                tone=var["tone"],
                target=var["target"],
                focus=var["focus"],
                tenant_id=tenant_id
            )
            
            results.append({
                "tone": var["tone"],
                "target": var["target"],
                "text": listing_text,
                "market_summary": market_context.get("summary"),
                "neighborhood": market_context.get("neighborhood")
            })
            
        return results
        
    async def _generate_listing_variation(
        self,
        property_data: Dict[str, Any],
        market_context: Dict[str, Any],
        tone: str,
        target: str,
        focus: str,
        tenant_id: Optional[str] = None
    ) -> str:
        """Use Claude Sonnet to generate a specific listing variation."""
        
        prompt = f"""
        Generate a compelling real estate listing description for the following property:
        
        PROPERTY DETAILS:
        {json.dumps(property_data, indent=2)}
        
        NEIGHBORHOOD CONTEXT:
        {json.dumps(market_context, indent=2)}
        
        STYLE REQUIREMENTS:
        - Tone: {tone}
        - Target Audience: {target}
        - Focus Areas: {focus}
        - Length: 150-250 words
        
        The description should feel professional, authentic, and highly persuasive. 
        Inject specific neighborhood details (schools, vibes, trends) from the context provided.
        """
        
        try:
            # Use Sonnet for high-quality creative writing
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are a top-performing real estate copywriter known for high-conversion listing descriptions.",
                complexity=TaskComplexity.COMPLEX,
                tenant_id=tenant_id,
                max_tokens=1000,
                temperature=0.7
            )
            return response.content.strip()
        except Exception as e:
            logger.error(f"Error generating listing variation: {e}")
            return f"Error generating {tone} listing. Please check logs."

    async def generate_seo_keywords(self, property_data: Dict[str, Any], tenant_id: Optional[str] = None) -> List[str]:
        """Generate SEO-optimized keywords using AI."""
        prompt = f"""
        Generate 15 SEO-optimized keywords for this real estate listing:
        Property: {property_data.get('address')}
        Type: {property_data.get('type')}
        Price: ${property_data.get('price')}
        
        Return as a comma-separated list.
        """
        
        try:
            response = await self.llm.agenerate(
                prompt=prompt,
                complexity=TaskComplexity.ROUTINE,
                tenant_id=tenant_id,
                max_tokens=100
            )
            return [k.strip() for k in response.content.split(",")]
        except Exception:
            return ["real estate", "home for sale"]
