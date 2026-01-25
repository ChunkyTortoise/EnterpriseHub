#!/usr/bin/env python3
"""
Test Jorge Bot Track 3.1 Integration
====================================

Validate that Jorge's LangGraph workflow is successfully enhanced with
Track 3.1 Predictive Intelligence while maintaining confrontational effectiveness.

Usage:
    python test_jorge_track3_integration.py

Author: Claude Sonnet 4
Date: 2026-01-24
Purpose: Validate Phase 2 Jorge Bot integration
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, '.')

from ghl_real_estate_ai.agents.jorge_seller_bot import JorgeSellerBot
from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState


async def test_jorge_track3_integration():
    """Test enhanced Jorge Bot with Track 3.1 predictive intelligence"""

    print("🤖 Testing Jorge Bot Track 3.1 Integration")
    print("=" * 60)

    # Initialize enhanced Jorge Bot
    print("📊 Initializing Jorge Bot with Track 3.1...")
    jorge = JorgeSellerBot(tenant_id="test_integration")
    await asyncio.sleep(0.5)  # Allow ML engine initialization

    # Test scenarios
    test_scenarios = {
        "hot_motivated_seller": {
            "description": "🔥 Hot motivated seller - should get AGGRESSIVE approach",
            "state": {
                "lead_id": "hot_seller_001",
                "lead_name": "Sarah Wilson",
                "property_address": "123 Rancho Cucamonga St",
                "conversation_history": [
                    {"sender": "lead", "content": "I need to sell ASAP. Job transfer in 30 days.", "timestamp": datetime.now().isoformat()},
                    {"sender": "agent", "content": "What's your timeline?", "timestamp": datetime.now().isoformat()},
                    {"sender": "lead", "content": "30 days max. Already found house in Dallas. Need to close quickly.", "timestamp": datetime.now().isoformat()},
                ],
                "intent_profile": None,
                "current_tone": "direct",
                "stall_detected": False,
                "detected_stall_type": None,
                "next_action": "respond",
                "response_content": "",
                "psychological_commitment": 85.0,  # High PCS
                "is_qualified": True,
                "current_journey_stage": "qualification",
                "follow_up_count": 0,
                "last_action_timestamp": datetime.now()
            }
        },

        "stalled_seller": {
            "description": "⏰ Stalled seller - should get CONFRONTATIONAL breakthrough",
            "state": {
                "lead_id": "stalled_seller_002",
                "lead_name": "Mike Rodriguez",
                "property_address": "456 Cedar Ave",
                "conversation_history": [
                    {"sender": "lead", "content": "Thinking about selling", "timestamp": (datetime.now() - timedelta(days=7)).isoformat()},
                    {"sender": "agent", "content": "What's your timeline?", "timestamp": (datetime.now() - timedelta(days=7)).isoformat()},
                    {"sender": "lead", "content": "Not sure yet. Need to think about it.", "timestamp": (datetime.now() - timedelta(days=5)).isoformat()},
                ],
                "intent_profile": None,
                "current_tone": "direct",
                "stall_detected": True,  # Stall detected
                "detected_stall_type": "thinking",
                "next_action": "respond",
                "response_content": "",
                "psychological_commitment": 45.0,  # Medium PCS
                "is_qualified": False,
                "current_journey_stage": "qualification",
                "follow_up_count": 2,
                "last_action_timestamp": datetime.now() - timedelta(days=5)
            }
        },

        "low_commitment_seller": {
            "description": "🌱 Low commitment seller - should get TAKE-AWAY approach",
            "state": {
                "lead_id": "low_commit_seller_003",
                "lead_name": "Jennifer Kim",
                "property_address": "789 Oak Dr",
                "conversation_history": [
                    {"sender": "lead", "content": "Maybe interested in selling", "timestamp": datetime.now().isoformat()},
                    {"sender": "agent", "content": "What's driving the potential sale?", "timestamp": datetime.now().isoformat()},
                    {"sender": "lead", "content": "Just curious about market value", "timestamp": datetime.now().isoformat()},
                ],
                "intent_profile": None,
                "current_tone": "direct",
                "stall_detected": False,
                "detected_stall_type": None,
                "next_action": "respond",
                "response_content": "",
                "psychological_commitment": 15.0,  # Low PCS
                "is_qualified": False,
                "current_journey_stage": "qualification",
                "follow_up_count": 0,
                "last_action_timestamp": datetime.now()
            }
        }
    }

    # Test each scenario
    results = {}

    for scenario_name, scenario_data in test_scenarios.items():
        print(f"\n🔍 Testing: {scenario_data['description']}")
        print("-" * 50)

        state = scenario_data["state"]

        # Mock _fetch_lead_data to return test data for Track 3.1
        original_fetch = jorge.ml_analytics._fetch_lead_data

        def mock_fetch_data(lead_id):
            return {
                "lead_id": lead_id,
                "jorge_score": state["psychological_commitment"] / 20.0,  # Convert PCS to Jorge score
                "created_at": datetime.now().isoformat(),
                "messages": state["conversation_history"],
                "property_preferences": {"timeline": "urgent" if state["psychological_commitment"] > 70 else "flexible"}
            }

        jorge.ml_analytics._fetch_lead_data = mock_fetch_data

        try:
            # Test enhanced select_strategy method
            strategy_result = await jorge.select_strategy(state)

            results[scenario_name] = {
                "original_pcs": state["psychological_commitment"],
                "original_stall": state["stall_detected"],
                "enhanced_tone": strategy_result["current_tone"],
                "enhancement_applied": strategy_result.get("track3_behavioral_applied", False),
                "timing_applied": strategy_result.get("track3_timing_applied", False),
                "enhancement_reason": strategy_result.get("enhancement_reason", "none"),
                "urgency_factors": strategy_result.get("timing_factors", {}),
                "behavioral_factors": strategy_result.get("behavioral_factors", {}),
            }

            print(f"✅ Strategy Result:")
            print(f"   Original PCS: {state['psychological_commitment']}")
            print(f"   Stall Detected: {state['stall_detected']}")
            print(f"   Enhanced Tone: {strategy_result['current_tone']}")
            print(f"   Track 3.1 Applied: {strategy_result.get('track3_behavioral_applied', False)}")

            if "enhancement_reason" in strategy_result:
                print(f"   Enhancement Reason: {strategy_result['enhancement_reason']}")

            if "timing_factors" in strategy_result:
                timing = strategy_result["timing_factors"]
                print(f"   Urgency Score: {timing.get('urgency_score', 0):.3f}")
                print(f"   Optimal Action: {timing.get('optimal_action', 'N/A')}")

            print(f"   ⚡ Performance: Enhanced decision-making with predictive intelligence")

        except Exception as e:
            print(f"❌ Test failed: {e}")
            results[scenario_name] = {"error": str(e)}

        finally:
            # Restore original method
            jorge.ml_analytics._fetch_lead_data = original_fetch

    # Validation Summary
    print(f"\n📊 Jorge Bot Track 3.1 Integration Summary")
    print("=" * 60)

    success_count = 0
    total_tests = len(test_scenarios)

    for scenario_name, result in results.items():
        if "error" not in result:
            success_count += 1
            print(f"✅ {scenario_name}: {result['enhanced_tone']} strategy")
            if result.get("enhancement_applied"):
                print(f"   🚀 Track 3.1 enhancement: {result.get('enhancement_reason', 'applied')}")
        else:
            print(f"❌ {scenario_name}: {result['error']}")

    print(f"\n🎯 Results: {success_count}/{total_tests} scenarios successful")

    # Validate Jorge's methodology preservation
    print(f"\n🤖 Jorge Methodology Validation:")
    hot_seller = results.get("hot_motivated_seller", {})
    stalled_seller = results.get("stalled_seller", {})
    low_commitment = results.get("low_commitment_seller", {})

    methodology_preserved = True

    # High PCS should remain aggressive
    if hot_seller.get("enhanced_tone") not in ["DIRECT", "CONFRONTATIONAL"]:
        print(f"⚠️  High PCS seller not handled aggressively: {hot_seller.get('enhanced_tone')}")
        methodology_preserved = False
    else:
        print(f"✅ High PCS seller handled correctly: {hot_seller.get('enhanced_tone')}")

    # Stalled should be confrontational
    if stalled_seller.get("enhanced_tone") != "CONFRONTATIONAL":
        print(f"⚠️  Stalled seller not confrontational: {stalled_seller.get('enhanced_tone')}")
        methodology_preserved = False
    else:
        print(f"✅ Stalled seller handled correctly: {stalled_seller.get('enhanced_tone')}")

    # Low commitment should be take-away
    if low_commitment.get("enhanced_tone") != "TAKE-AWAY":
        print(f"⚠️  Low commitment not take-away: {low_commitment.get('enhanced_tone')}")
        methodology_preserved = False
    else:
        print(f"✅ Low commitment handled correctly: {low_commitment.get('enhanced_tone')}")

    # Track 3.1 Enhancement Validation
    track3_working = any(r.get("enhancement_applied") for r in results.values() if "error" not in r)
    print(f"\n🔬 Track 3.1 Enhancement Status: {'✅ ACTIVE' if track3_working else '⚠️  NOT DETECTED'}")

    # Final Assessment
    overall_success = (success_count == total_tests and methodology_preserved and track3_working)

    print(f"\n🚀 OVERALL ASSESSMENT: {'✅ SUCCESS' if overall_success else '❌ NEEDS ATTENTION'}")

    if overall_success:
        print("🎉 Jorge Bot Track 3.1 integration is working perfectly!")
        print("   • Confrontational methodology preserved")
        print("   • Predictive intelligence enhancing decision-making")
        print("   • All scenarios handled appropriately")
        print("   • Ready for production deployment")
    else:
        print("🔧 Issues detected - review integration before deployment")

    return overall_success


if __name__ == "__main__":
    asyncio.run(test_jorge_track3_integration())