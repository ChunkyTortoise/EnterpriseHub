"""
Test script for Adaptive PCS Calculation (Phase 1.3)
Verifies that PCS updates dynamically based on conversation engagement.
"""

import asyncio
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer


async def test_adaptive_pcs():
    """Test adaptive PCS recalculation with simulated conversation flows."""
    analyzer = get_seller_psychology_analyzer()

    # Test 1: Cold seller (short answers) → should decrease PCS
    print("\n=== Test 1: Cold Seller (Short Answers) ===")
    cold_conversation = [
        {"role": "bot", "content": "Hi! Are you interested in selling your home?"},
        {"role": "user", "content": "Maybe"},
        {"role": "bot", "content": "What's your timeline?"},
        {"role": "user", "content": "Not sure"},
        {"role": "bot", "content": "What price range are you thinking?"},
        {"role": "user", "content": "No idea"},
    ]

    result = await analyzer.recalculate_pcs(
        current_pcs=50.0, conversation_history=cold_conversation, last_message="No idea"
    )

    print(f"Initial PCS: 50.0")
    print(f"Updated PCS: {result['updated_pcs']}")
    print(f"Delta: {result['delta']:+.1f}")
    print(f"Trend: {result['trend']}")
    print(f"Engagement Metrics: {result['engagement_metrics']}")
    assert result["updated_pcs"] < 50.0, "PCS should decrease for cold seller"
    assert result["trend"] == "cooling", "Trend should be cooling"
    print("✓ Test 1 passed: PCS decreased for cold seller")

    # Test 2: Warming seller (expanding responses) → should increase PCS
    print("\n=== Test 2: Warming Seller (Expanding Responses) ===")
    warming_conversation = [
        {"role": "bot", "content": "Hi! Are you interested in selling your home?"},
        {"role": "user", "content": "Yes"},
        {"role": "bot", "content": "Great! What's your timeline?"},
        {
            "role": "user",
            "content": "I'm thinking within the next 3 months because I need to relocate for work.",
        },
        {"role": "bot", "content": "What price range are you thinking?"},
        {
            "role": "user",
            "content": "I was thinking around $600,000 based on what my neighbor sold for. I'd like to get a professional opinion though. When can we schedule an appraisal?",
        },
    ]

    result = await analyzer.recalculate_pcs(
        current_pcs=50.0,
        conversation_history=warming_conversation,
        last_message="I was thinking around $600,000 based on what my neighbor sold for. I'd like to get a professional opinion though. When can we schedule an appraisal?",
    )

    print(f"Initial PCS: 50.0")
    print(f"Updated PCS: {result['updated_pcs']}")
    print(f"Delta: {result['delta']:+.1f}")
    print(f"Trend: {result['trend']}")
    print(f"Engagement Metrics: {result['engagement_metrics']}")
    assert result["updated_pcs"] > 50.0, "PCS should increase for warming seller"
    assert result["trend"] == "warming", "Trend should be warming"
    print("✓ Test 2 passed: PCS increased for warming seller")

    # Test 3: Acceptance signals → should increase PCS
    print("\n=== Test 3: Acceptance Signals ===")
    acceptance_conversation = [
        {"role": "bot", "content": "Would you like to schedule a property visit?"},
        {"role": "user", "content": "Sounds good! Let's do it. When can you come?"},
    ]

    result = await analyzer.recalculate_pcs(
        current_pcs=60.0,
        conversation_history=acceptance_conversation,
        last_message="Sounds good! Let's do it. When can you come?",
    )

    print(f"Initial PCS: 60.0")
    print(f"Updated PCS: {result['updated_pcs']}")
    print(f"Delta: {result['delta']:+.1f}")
    print(f"Trend: {result['trend']}")
    print(f"Engagement Metrics: {result['engagement_metrics']}")
    assert result["updated_pcs"] > 60.0, "PCS should increase with acceptance signals"
    assert result["engagement_metrics"]["objection_handling"] == "acceptance"
    print("✓ Test 3 passed: PCS increased with acceptance signals")

    # Test 4: Resistance signals → should decrease PCS
    print("\n=== Test 4: Resistance Signals ===")
    resistance_conversation = [
        {"role": "bot", "content": "Would you like to schedule a property visit?"},
        {"role": "user", "content": "Not interested. Don't call me again."},
    ]

    result = await analyzer.recalculate_pcs(
        current_pcs=60.0,
        conversation_history=resistance_conversation,
        last_message="Not interested. Don't call me again.",
    )

    print(f"Initial PCS: 60.0")
    print(f"Updated PCS: {result['updated_pcs']}")
    print(f"Delta: {result['delta']:+.1f}")
    print(f"Trend: {result['trend']}")
    print(f"Engagement Metrics: {result['engagement_metrics']}")
    assert result["updated_pcs"] < 60.0, "PCS should decrease with resistance signals"
    assert result["engagement_metrics"]["objection_handling"] == "resistance"
    print("✓ Test 4 passed: PCS decreased with resistance signals")

    # Test 5: High commitment indicators → should increase PCS
    print("\n=== Test 5: High Commitment Indicators ===")
    commitment_conversation = [
        {"role": "bot", "content": "Are you ready to move forward?"},
        {
            "role": "user",
            "content": "Yes! What's the next step? When can you come see the property? I'm ready to list. What do you need from me?",
        },
    ]

    result = await analyzer.recalculate_pcs(
        current_pcs=70.0,
        conversation_history=commitment_conversation,
        last_message="Yes! What's the next step? When can you come see the property? I'm ready to list. What do you need from me?",
    )

    print(f"Initial PCS: 70.0")
    print(f"Updated PCS: {result['updated_pcs']}")
    print(f"Delta: {result['delta']:+.1f}")
    print(f"Trend: {result['trend']}")
    print(f"Engagement Metrics: {result['engagement_metrics']}")
    assert result["updated_pcs"] > 70.0, "PCS should increase with commitment indicators"
    assert result["engagement_metrics"]["commitment_indicators"] > 0
    print("✓ Test 5 passed: PCS increased with commitment indicators")

    print("\n" + "=" * 60)
    print("✓ ALL TESTS PASSED!")
    print("=" * 60)
    print("\nAdaptive PCS Calculation is working correctly!")
    print("- PCS decreases for cold/disengaged sellers")
    print("- PCS increases for warming/engaged sellers")
    print("- Trend detection (warming/cooling/stable) works")
    print("- Engagement metrics accurately track conversation quality")


if __name__ == "__main__":
    asyncio.run(test_adaptive_pcs())
