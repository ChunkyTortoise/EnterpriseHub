"""
Marketing Agent (V2)
Specialized in personalized outreach, campaign copy, and GHL integration.
Built with PydanticAI and optimized for Gemini 2.0 Flash.
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext
from pydantic_ai.models.gemini import GeminiModel

# 1. Define the Marketing Result Schema
class MarketingResult(BaseModel):
    sms_copy: str = Field(description="Personalized SMS message content")
    email_body: str = Field(description="Personalized Email body (HTML or plain text)")
    ad_headlines: List[str] = Field(description="Suggested headlines for Facebook/Google ads")
    call_script: str = Field(description="Suggested script for a follow-up discovery call")
    campaign_name: str = Field(description="Recommended name for this outreach campaign")
    target_audience_segment: str = Field(description="Description of the target lead segment")

# 2. Define Dependencies
class MarketingDeps:
    def __init__(self, ghl_service=None):
        self.ghl = ghl_service

# 3. Initialize Gemini Model
model = GeminiModel('gemini-2.0-flash')

# 4. Create the Marketing Agent
marketing_agent = Agent(
    model,
    deps_type=MarketingDeps,
    output_type=MarketingResult,
    system_prompt=(
        "You are a Senior Real Estate Marketing Specialist and CRM Automation Expert. "
        "Your goal is to create highly personalized, high-converting marketing copy for property opportunities. "
        "You use the executive narrative, property details, and lead profiles to tailor SMS, email, and ad copy. "
        "Ensure the tone matches the brand: warm, professional, authoritative, and enthusiastic. "
        "Focus on 'Benefits over Features' and include clear Calls to Action (CTAs)."
    )
)

# 5. Define Tools
@marketing_agent.tool
async def ghl_campaign_sender(ctx: RunContext[MarketingDeps], contact_id: str, campaign_data: Dict[str, Any]) -> str:
    """Mock GHL API call to send a marketing campaign to a contact."""
    if ctx.deps.ghl:
        # In a real tool, we would call the GHL service
        # await ctx.deps.ghl.trigger_marketing_campaign(contact_id, campaign_data)
        return f"SUCCESS: Campaign sent to GHL Contact {contact_id}"
    return "MOCK_SUCCESS: GHL Service not available, but campaign would have been sent."
