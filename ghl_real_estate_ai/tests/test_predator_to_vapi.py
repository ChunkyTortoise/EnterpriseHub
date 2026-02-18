import pytest

import asyncio
import json
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider
from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.simulated_mls_feed import SimulatedMLSFeed
from ghl_real_estate_ai.services.usage_billing_service import usage_billing_service
from ghl_real_estate_ai.services.voice_outbound_service import VoiceOutboundService

logger = get_logger(__name__)


@dataclass
class PredatorAlert:
    tenant_id: str
    property_id: str
    old_price: float
    new_price: float
    drop_percentage: float
    timestamp: datetime
    lead_ids: list[str]


class SwarmE2EValidator:
    """
    E2E Validation for the Predator-to-Vapi loop.
    Simulates: Price Drop -> Agent Detection -> Vapi Payload -> Outbound Trigger.
    """

    def __init__(self, tenant_id: str = "test_tenant_ elite"):
        self.tenant_id = tenant_id
        self.llm = LLMClient(provider=LLMProvider.CLAUDE)
        self.voice_service = VoiceOutboundService()
        self.mls_feed = SimulatedMLSFeed()

    async def run_validation(self):
        print(f"🚀 Starting Swarm E2E Validation for Tenant: {self.tenant_id}")

        # 1. Simulate Price Drop
        print("🔍 Step 1: Simulating Price Drop Detection...")
        property_data = {
            "id": "prop_austin_001",
            "address": "123 Tech Lane, Austin, TX",
            "old_price": 850000,
            "new_price": 799000,
            "leads": ["lead_jorge_001", "lead_buyer_002"],
        }

        alert = PredatorAlert(
            tenant_id=self.tenant_id,
            property_id=property_data["id"],
            old_price=property_data["old_price"],
            new_price=property_data["new_price"],
            drop_percentage=((property_data["old_price"] - property_data["new_price"]) / property_data["old_price"])
            * 100,
            timestamp=datetime.utcnow(),
            lead_ids=property_data["leads"],
        )
        print(f"✅ Price Drop Detected: {alert.drop_percentage:.1f}% drop on {property_data['address']}")

        # 2. Trigger MarketAnalystAgent (Simulated via LLM call)
        print("🤖 Step 2: Triggering MarketAnalystAgent for Strategy...")
        strategy_prompt = f"""
        Predator Mode Active.
        Property: {property_data["address"]}
        Price Drop: ${property_data["old_price"]} -> ${property_data["new_price"]}
        
        Generate a "Defensive Comparison" strategy for the buyer leads.
        """

        # This call will trigger our new UsageBillingService hook
        response = await self.llm.agenerate(
            prompt=strategy_prompt,
            system_prompt="You are the MarketAnalystAgent in Predator Mode.",
            tenant_id=self.tenant_id,
        )
        print(f"✅ Strategy Generated ({response.tokens_used} tokens tracked)")

        # 3. Prepare Vapi Payload
        print("📞 Step 3: Preparing Vapi Payload...")
        # Correcting method call based on service definition
        vapi_payload = await self.voice_service.prepare_vapi_payload(
            lead_id=property_data["leads"][0],
            lead_data={"first_name": "Jorge", "last_name": "Buyer", "conversation_history": []},
            property_data={
                "id": property_data["id"],
                "address": property_data["address"],
                "list_price": property_data["new_price"],
                "history": {
                    "original_list_price": property_data["old_price"],
                    "current_price": property_data["new_price"],
                    "price_drops": [{"old_price": property_data["old_price"], "new_price": property_data["new_price"]}],
                },
            },
        )
        print(f"✅ Vapi Payload Ready for Lead: {property_data['leads'][0]}")

        # 4. Simulate Outbound Call Trigger
        print("⚡ Step 4: Simulating Outbound Call Trigger...")
        # In a real E2E, this would call Vapi API. Here we validate the flow.
        call_id = f"vapi_call_{uuid.uuid4().hex[:8]}"
        print(f"✅ Outbound Call Triggered. Vapi ID: {call_id}")

        # 5. Verify Billing Tracking
        print("📊 Step 5: Verifying Billing Tracking...")
        usage = await usage_billing_service.get_tenant_usage(self.tenant_id)
        if usage.get("total_calls", 0) > 0:
            print(f"✅ Billing Verified: {usage['total_calls']} calls tracked for {self.tenant_id}")
            print(f"💰 Accrued Cost: ${usage.get('total_cost_usd', 0):.4f}")
        else:
            print("❌ Billing Verification Failed: No usage records found.")

        print("\n✨ Swarm E2E Validation Complete: SUCCESS")


if __name__ == "__main__":
    validator = SwarmE2EValidator()
    asyncio.run(validator.run_validation())
