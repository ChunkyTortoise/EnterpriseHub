"""
Content Generation Service - Automated Campaign Engine

This service generates automated social media, email, and SMS campaign content
based on real-time market trends, pricing arbitrage, and economic indicators.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import logging
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity
from ghl_real_estate_ai.services.market_timing_opportunity_intelligence import MarketTimingOpportunityEngine
from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

logger = logging.getLogger(__name__)


class ContentGenerationService:
    """
    Engine for generating market-aware real estate marketing content.
    """

    def __init__(self):
        self.market_intel = get_national_market_intelligence()
        self.opportunity_engine = MarketTimingOpportunityEngine()
        self.llm_client = LLMClient(provider="claude")

    async def generate_market_update_sms(self, location: str, contact_name: Optional[str] = None) -> str:
        """
        Generate a data-driven market update SMS.
        Strictly <160 chars, no emojis, no hyphens.
        """
        try:
            metrics = await self.market_intel.get_market_metrics(location)

            # Extract key data points
            inventory_status = metrics.inventory_trend if metrics else "shifting"
            dom = metrics.days_on_market if metrics else 30

            prompt = f"""Generate a confrontational, data-driven real estate SMS for {location}.
            
            DATA:
            - Inventory: {inventory_status}
            - Days on Market: {dom}
            
            CONSTRAINTS:
            - Max 160 characters.
            - NO emojis.
            - NO hyphens.
            - Tone: Professional, data-driven, elite.
            - Must include a direct question at the end.
            """

            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are an elite real estate analyst. Write direct, data-driven SMS content.",
                temperature=0.7,
                complexity=TaskComplexity.ROUTINE,
            )

            content = response.content.strip()
            # Clean up any accidental hyphens or emojis
            import re

            content = re.sub(r"[^\x00-\x7F]+", "", content)  # Remove non-ASCII (emojis)
            content = content.replace("-", " ")  # Remove hyphens

            if contact_name:
                content = f"{contact_name}, {content.lower()}"

            return content[:160]

        except Exception as e:
            logger.error(f"Error generating market SMS: {e}")
            return f"Market update for {location}: Inventory is {inventory_status}. Serious buyers are moving fast. Are you ready to sell?"

    async def generate_arbitrage_email(self, location: str, investor_name: str) -> Dict[str, str]:
        """
        Generate an elite arbitrage opportunity email for investors.
        """
        try:
            dashboard = await self.opportunity_engine.get_opportunity_dashboard(location)
            arbitrage_opp = next(
                (o for o in dashboard.get("opportunities", []) if o["type"] == "pricing_arbitrage"), None
            )

            yield_spread = arbitrage_opp["score"] if arbitrage_opp else 7.5

            prompt = f"""Write an elite, technical email to an investor named {investor_name} regarding a {yield_spread}% yield spread opportunity in {location}.
            
            TONE: Confrontational, data-driven, no 'salesy' fluff. Focus on arbitrage exploitation and yield spreads.
            
            STRUCTURE:
            - Subject: Technical, data-focused.
            - Body: Direct, highlighting the pricing inefficiency.
            - Call to action: Reply 'DATA' for the full proforma.
            """

            response = await self.llm_client.agenerate(
                prompt=prompt,
                system_prompt="You are a high-concurrency real estate investment architect.",
                temperature=0.4,
                complexity=TaskComplexity.ROUTINE,
            )

            # Simple parsing of Subject/Body if LLM followed instructions
            content = response.content.strip()
            lines = content.split("\n")
            subject = "Arbitrage Opportunity Detected"
            body = content

            for line in lines:
                if line.lower().startswith("subject:"):
                    subject = line.split(":", 1)[1].strip()
                    body = "\n".join([l for l in lines if not l.lower().startswith("subject:")]).strip()
                    break

            return {"subject": subject, "body": body}

        except Exception as e:
            logger.error(f"Error generating arbitrage email: {e}")
            return {
                "subject": f"Yield Spread Opportunity: {location}",
                "body": f"{investor_name},\n\nWe've detected a significant pricing arbitrage in {location}. Yield spreads are currently outpacing the city average. Reply DATA if you want the proforma.",
            }

    async def generate_campaign_package(self, location: str) -> List[Dict[str, Any]]:
        """
        Generate a full multi-channel campaign package based on current market trends.
        """
        sms = await self.generate_market_update_sms(location)
        email = await self.generate_arbitrage_email(location, "Investor")

        return [{"type": "sms", "content": sms}, {"type": "email", "subject": email["subject"], "body": email["body"]}]


def get_content_generation_service():
    return ContentGenerationService()
