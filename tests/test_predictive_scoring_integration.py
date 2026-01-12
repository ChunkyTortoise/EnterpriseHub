import asyncio
import json
import os
from datetime import datetime, timedelta

# Mock environment variables for Settings validation
os.environ["ANTHROPIC_API_KEY"] = "sk-test-123"
os.environ["GHL_API_KEY"] = "ghl-test-456"
os.environ["GHL_LOCATION_ID"] = "loc-test-789"

from ghl_real_estate_ai.core.conversation_manager import ConversationManager

async def test_predictive_integration():
    print("🚀 Testing Predictive Lead Scoring Integration...")
    
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
            "timestamp": (now - timedelta(minutes=10)).isoformat()
        },
        {
            "role": "assistant",
            "content": "Hi! Austin is a great choice. I can certainly help you with that. Are you already pre-approved for a loan?",
            "timestamp": (now - timedelta(minutes=9)).isoformat()
        },
        {
            "role": "user",
            "content": "Yes, I'm pre-approved and I need to move within the next month.",
            "timestamp": (now - timedelta(minutes=8)).isoformat()
        }
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
            "timeline": "next month"
        },
        "last_interaction_at": history[-1]["timestamp"],
        "is_returning_lead": False
    }
    
    # Test the scorer directly first
    print("\n📊 Testing PredictiveScorer directly...")
    prediction = manager.predictive_scorer.predict_conversion(context)
    
    print(f"Lead ID: {prediction['contact_id']}")
    print(f"Conversion Probability: {prediction['conversion_probability']}%")
    print(f"Confidence: {prediction['confidence']}")
    print(f"Trajectory: {prediction['trajectory']}")
    print("\n🧠 Reasoning:")
    for r in prediction['reasoning']:
        print(f"  - {r}")
        
    print("\n📋 Recommendations:")
    for rec in prediction['recommendations']:
        print(f"  - [{rec['type'].upper()}] {rec['title']}: {rec['action']}")

    # Verify rule-based score still works
    rule_score = manager.lead_scorer.calculate(context)
    print(f"\n📏 Rule-Based Score (Questions Answered): {rule_score}/7")
    
    if rule_score >= 3:
        print("✅ Correctly identified as HOT lead by Jorge's rules.")

if __name__ == "__main__":
    asyncio.run(test_predictive_integration())
