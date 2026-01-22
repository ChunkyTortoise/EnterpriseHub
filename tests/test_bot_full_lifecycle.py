import pytest
import asyncio
import os
from datetime import datetime

# Mock environment
os.environ["ANTHROPIC_API_KEY"] = "sk-test-123"
os.environ["GHL_API_KEY"] = "ghl-test-456"

from ghl_real_estate_ai.agents.workflow_factory import get_workflow_factory
from ghl_real_estate_ai.models.workflows import SellerWorkflowState, LeadFollowUpState

@pytest.mark.asyncio
async def test_seller_lifecycle_workflow():
    print("\n🚀 Testing Jorge Seller Full-Lifecycle Workflow...")
    factory = get_workflow_factory()
    workflow = factory.get_workflow("seller")
    
    # Test Stage 1: Qualification
    state: SellerWorkflowState = {
        "lead_id": "seller_123",
        "lead_name": "John Seller",
        "contact_phone": "+1234567890",
        "contact_email": "john@example.com",
        "property_address": "456 Oak St, Rancho Cucamonga",
        "conversation_history": [
            {"role": "user", "content": "I want to sell my house because I am relocating."}
        ],
        "seller_data": {},
        "temperature": "cold",
        "current_step": "qualification",
        "engagement_status": "new",
        "questions_answered": 0,
        "last_interaction_time": datetime.now(),
        "valuation_provided": False,
        "listing_date": None,
        "contract_date": None,
        "closing_date": None,
        "final_sale_price": None,
        "net_proceeds": None,
        "closing_milestones": []
    }
    
    # In a real test we'd invoke the graph:
    # result = await workflow.workflow.ainvoke(state)
    # For this verification, we'll check the node logic
    node_result = await workflow.handle_qualification(state)
    print(f"✅ Qualification Node result: {node_result['engagement_status']}, QA: {node_result['questions_answered']}")
    
    # Test Stage 2: Pre-Listing
    state.update(node_result)
    state["temperature"] = "hot" # Force move to next stage
    
    pre_listing_result = await workflow.handle_pre_listing(state)
    print(f"✅ Pre-Listing Node result: {pre_listing_result['engagement_status']}")

@pytest.mark.asyncio
async def test_buyer_lifecycle_workflow():
    print("\n🚀 Testing Lead Bot (Buyer) Full-Lifecycle Workflow...")
    factory = get_workflow_factory()
    workflow = factory.get_workflow("buyer")
    
    state: LeadFollowUpState = {
        "lead_id": "buyer_123",
        "lead_name": "Jane Buyer",
        "contact_phone": "+1987654321",
        "contact_email": "jane@example.com",
        "property_address": "123 Main St",
        "conversation_history": [{"role": "user", "content": "I like this house."}],
        "intent_profile": None,
        "current_step": "schedule_showing",
        "engagement_status": "re_engaged",
        "last_interaction_time": datetime.now(),
        "stall_breaker_attempted": False,
        "cma_generated": True,
        "showing_date": None,
        "showing_feedback": None,
        "offer_amount": None,
        "closing_date": None
    }
    
    # Test showing coordination
    showing_result = await workflow.schedule_showing(state)
    print(f"✅ Showing Node result: {showing_result['engagement_status']}")
    
    # Test offer facilitation
    state.update(showing_result)
    offer_result = await workflow.facilitate_offer(state)
    print(f"✅ Offer Node result: {offer_result['engagement_status']}")

if __name__ == "__main__":
    asyncio.run(test_seller_lifecycle_workflow())
    asyncio.run(test_buyer_lifecycle_workflow())
