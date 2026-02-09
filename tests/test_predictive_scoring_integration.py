import pytest
pytestmark = pytest.mark.integration

import asyncio
import json
import os
from datetime import datetime, timedelta

import pytest

# Mock environment variables for Settings validation - MUST be before imports
os.environ["ANTHROPIC_API_KEY"] = "sk-test-123"
os.environ["GHL_API_KEY"] = "ghl-test-456"
os.environ["GHL_LOCATION_ID"] = "loc-test-789"
os.environ["JORGE_SELLER_MODE"] = "false"

from ghl_real_estate_ai.core.conversation_manager import ConversationManager

@pytest.mark.integration


@pytest.mark.asyncio
async def test_predictive_integration():
    print("🚀 Testing Predictive Lead Scoring Integration...")

    # Initialize without relying on external services if possible, or mock them
    # For integration test, we assume environment is set up or mocks are handled
    manager = ConversationManager()

    # Mock data for a high-intent lead
    contact_id = "test_lead_123"
    location_id = "test_loc_456"

    # Simulate a conversation
    now = datetime.utcnow()
    history = [
        {
            "role": "user",
            "content": "Hi, I'm looking for a 3 bedroom house in Austin. My budget is around $500k.",
            "timestamp": (now - timedelta(minutes=10)).isoformat(),
        },
        {
            "role": "assistant",
            "content": "Hi! Austin is a great choice. I can certainly help you with that. Are you already pre-approved for a loan?",
            "timestamp": (now - timedelta(minutes=9)).isoformat(),
        },
        {
            "role": "user",
            "content": "Yes, I'm pre-approved and I need to move within the next month.",
            "timestamp": (now - timedelta(minutes=8)).isoformat(),
        },
    ]

    context = {
        "contact_id": contact_id,
        "location_id": location_id,
        "conversation_history": history,
        "extracted_preferences": {
            "location": "Austin",
            "budget": 500000,
            "bedrooms": 3,
            "financing": "pre-approved",
            "timeline": "next month",
        },
        "last_interaction_at": history[-1]["timestamp"],
        "is_returning_lead": False,
    }

    # Test the scorer directly first
    # Note: Using V2 scorer which returns a dataclass (PredictiveScore)
    print("\n📊 Testing PredictiveScorer directly...")

    # Mock the predict_closing_probability method since it uses ML model
    # We want to test integration of the manager, not the ML model training
    # But for a real integration test, we might want to let it run if it has defaults

    # Actually, let's call calculate_predictive_score directly
    prediction_result = await manager.predictive_scorer.calculate_predictive_score(context, location=location_id)

    print(f"Closing Probability: {prediction_result.closing_probability:.1%}")
    print(f"Priority Level: {prediction_result.priority_level}")
    print(f"Overall Score: {prediction_result.overall_priority_score}")

    print("\n🧠 Reasoning (Risk Factors):")
    for r in prediction_result.risk_factors:
        print(f"  - {r}")

    print("\n📋 Recommended Actions:")
    for action in prediction_result.recommended_actions:
        print(f"  - {action}")

    # Verify rule-based score still works
    rule_score = await manager.lead_scorer.calculate(context)
    print(f"\n📏 Rule-Based Score (Questions Answered): {rule_score}/7")

    if rule_score >= 3:
        print("✅ Correctly identified as HOT lead by Jorge's rules.")


if __name__ == "__main__":
    asyncio.run(test_predictive_integration())