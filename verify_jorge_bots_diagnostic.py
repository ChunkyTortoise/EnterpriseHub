import asyncio
import os
import json
from ghl_real_estate_ai.api.routes.webhook import handle_ghl_webhook, tenant_service
from ghl_real_estate_ai.api.schemas.ghl import GHLWebhookEvent, GHLContact, GHLMessage, MessageType, MessageDirection
from ghl_real_estate_ai.ghl_utils.config import settings
from unittest.mock import MagicMock, AsyncMock

async def diagnostic():
    print("🚀 Starting Jorge's Bot Diagnostic...")
    
    # Mock tenant service to avoid "No tenant config found"
    tenant_service.get_tenant_config = AsyncMock(return_value={
        "location_id": "loc_123",
        "ghl_api_key": "mock_key",
        "anthropic_api_key": os.getenv("ANTHROPIC_API_KEY")
    })
    
    # Ensure JORGE_SELLER_MODE is true for this process
    os.environ["JORGE_SELLER_MODE"] = "true"
    
    # Mock background tasks
    bg_tasks = MagicMock()
    
    # Mock request
    request = MagicMock()
    
    # Get the undecorated function
    original_handler = handle_ghl_webhook
    if hasattr(handle_ghl_webhook, "__wrapped__"):
        original_handler = handle_ghl_webhook.__wrapped__

    # 1. Test Seller Bot Trigger
    print("\n--- Testing Seller Bot Trigger ---")
    seller_event = GHLWebhookEvent(
        type="InboundMessage",
        contact_id="seller_123",
        location_id="loc_123",
        message=GHLMessage(
            body="I want to sell my house", 
            type=MessageType.SMS,
            direction=MessageDirection.INBOUND
        ),
        contact=GHLContact(
            first_name="John",
            last_name="Seller",
            tags=["Needs Qualifying"]
        )
    )
    
    try:
        from ghl_real_estate_ai.ghl_utils.jorge_config import settings as jorge_settings
        jorge_settings.jorge_seller_mode = True
        
        response = await original_handler(request, seller_event, bg_tasks)
        print(f"✅ Seller Bot Response: {response.message}")
        print(f"✅ Actions: {[a.type for a in response.actions]}")
        
        is_seller_msg = any(word in response.message.lower() for word in ["considering", "sell", "move"])
        if is_seller_msg:
            print("💎 SUCCESS: Seller Bot correctly identified and triggered Question 1.")
        else:
            print("❌ FAILURE: Seller Bot did not trigger the correct sequence.")
    except Exception as e:
        print(f"❌ Error in Seller Bot diagnostic:")
        import traceback
        traceback.print_exc()

    # 2. Test Lead Bot (Buyer) Trigger
    print("\n--- Testing Lead Bot (Buyer) Trigger ---")
    buyer_event = GHLWebhookEvent(
        type="InboundMessage",
        contact_id="buyer_123",
        location_id="loc_123",
        message=GHLMessage(
            body="I'm looking for a 3 bed house in Rancho", 
            type=MessageType.SMS,
            direction=MessageDirection.INBOUND
        ),
        contact=GHLContact(
            first_name="Jane",
            last_name="Buyer",
            tags=["Needs Qualifying"]
        )
    )
    
    jorge_settings.jorge_seller_mode = False
    
    try:
        response = await original_handler(request, buyer_event, bg_tasks)
        print(f"✅ Buyer Bot Response: {response.message}")
        
        if any(word in response.message.lower() for word in ["jorge", "budget", "rancho", "looking"]):
            print("💎 SUCCESS: Lead Bot (Buyer) correctly triggered.")
        else:
            print("❌ FAILURE: Lead Bot (Buyer) did not trigger correctly.")
    except Exception as e:
        print(f"❌ Error in Buyer Bot diagnostic:")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import ghl_real_estate_ai.services.security_framework as sf
    sf.verify_webhook = lambda x: (lambda f: f)
    
    asyncio.run(diagnostic())
