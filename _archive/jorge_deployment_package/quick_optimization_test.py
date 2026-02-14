#!/usr/bin/env python3
"""
Quick Optimization Validation Test

Simple test to verify the optimized bots are working correctly.
"""

import asyncio
from datetime import datetime

# Test the optimized components directly
from jorge_engines_optimized import JorgeSellerEngineOptimized, JorgeLeadEngineOptimized
from lead_intelligence_optimized import get_enhanced_lead_intelligence
from ghl_client import GHLClient
from conversation_manager import ConversationManager
from config_settings import settings


async def test_optimized_lead_intelligence():
    """Test optimized lead intelligence directly"""

    print('🧠 TESTING OPTIMIZED LEAD INTELLIGENCE')
    print('=' * 45)

    # Test various message types
    test_messages = [
        {
            "name": "High-Quality Lead",
            "message": "Hi! I'm relocating to Rancho Cucamonga for Apple and have $600k budget. I need 4 bedrooms in Westlake Hills and I'm pre-approved. Can close within 30 days.",
            "expected_score_min": 80
        },
        {
            "name": "Medium-Quality Lead",
            "message": "I'm looking to buy a house in Rancho Cucamonga under $400k. Timeline is flexible but prefer North Rancho Cucamonga.",
            "expected_score_min": 60
        },
        {
            "name": "Low-Quality Lead",
            "message": "Hey, maybe interested in a house sometime. What do you have?",
            "expected_score_min": 30
        }
    ]

    results = []

    for test in test_messages:
        try:
            result = get_enhanced_lead_intelligence(test["message"])
            success = result["lead_score"] >= test["expected_score_min"]

            print(f'📝 {test["name"]}:')
            print(f'   Score: {result["lead_score"]:.1f} (expected: {test["expected_score_min"]}+) {"✅" if success else "❌"}')
            print(f'   Budget: {result["budget_analysis"]}')
            print(f'   Timeline: {result["timeline_analysis"]}')
            print(f'   Financing: {result["financing_analysis"]}')
            print(f'   Quality: Qualification={result["qualification"]:.2f}, Intent={result["intent_confidence"]:.2f}')

            if result["errors"]:
                print(f'   Errors: {result["errors"]}')

            print()

            results.append({
                "name": test["name"],
                "success": success,
                "score": result["lead_score"],
                "expected": test["expected_score_min"]
            })

        except Exception as e:
            print(f'❌ {test["name"]} FAILED: {e}')
            results.append({
                "name": test["name"],
                "success": False,
                "error": str(e)
            })

    return results


async def test_optimized_seller_engine():
    """Test optimized seller engine"""

    print('💪 TESTING OPTIMIZED SELLER ENGINE')
    print('=' * 45)

    # Create minimal components for testing
    conversation_manager = ConversationManager()
    ghl_client = GHLClient()

    seller_engine = JorgeSellerEngineOptimized(
        conversation_manager=conversation_manager,
        ghl_client=ghl_client
    )

    # Test seller messages
    test_messages = [
        {
            "name": "Motivated Seller - Divorce",
            "message": "My wife and I are getting divorced and need to sell our Round Rock house fast. We don't want to deal with repairs or showings.",
            "expected_temp": "hot"
        },
        {
            "name": "Casual Inquiry",
            "message": "Just curious what you might offer for my house. Not really sure if I want to sell.",
            "expected_temp": "cold"
        }
    ]

    results = []

    for test in test_messages:
        try:
            result = await seller_engine.process_seller_response(
                contact_id=f"test_seller_{len(results)}",
                user_message=test["message"],
                location_id=settings.ghl_location_id or "test_location"
            )

            success = result.get("temperature") == test["expected_temp"]

            print(f'🏠 {test["name"]}:')
            print(f'   Temperature: {result.get("temperature")} (expected: {test["expected_temp"]}) {"✅" if success else "❌"}')
            print(f'   Response: {result.get("message", "No response")[:80]}...')
            print(f'   Confidence: {result.get("confidence", 0):.2f}')
            print(f'   Tone Quality: {result.get("tone_quality", "unknown")}')
            print()

            results.append({
                "name": test["name"],
                "success": success,
                "temperature": result.get("temperature"),
                "confidence": result.get("confidence", 0)
            })

        except Exception as e:
            print(f'❌ {test["name"]} FAILED: {e}')
            results.append({
                "name": test["name"],
                "success": False,
                "error": str(e)
            })

    return results


async def main():
    """Run quick optimization validation"""

    print('🚀 JORGE\'S BOT OPTIMIZATION - QUICK VALIDATION')
    print('=' * 60)
    print(f'Started: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print()

    # Test lead intelligence
    lead_results = await test_optimized_lead_intelligence()

    print()

    # Test seller engine
    seller_results = await test_optimized_seller_engine()

    # Summary
    print('📊 QUICK VALIDATION RESULTS')
    print('=' * 40)

    lead_successes = [r for r in lead_results if r.get("success", False)]
    seller_successes = [r for r in seller_results if r.get("success", False)]

    total_tests = len(lead_results) + len(seller_results)
    total_successes = len(lead_successes) + len(seller_successes)

    success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0

    print(f'🎯 Overall Success Rate: {success_rate:.1f}%')
    print(f'   Lead Intelligence: {len(lead_successes)}/{len(lead_results)} tests passed')
    print(f'   Seller Engine: {len(seller_successes)}/{len(seller_results)} tests passed')
    print()

    if success_rate >= 70:
        print('✅ OPTIMIZATION SUCCESSFUL!')
        print('🚀 Jorge\'s bots are significantly improved and ready!')
    elif success_rate >= 50:
        print('⚡ PARTIAL SUCCESS - Good improvement, minor tweaks needed')
    else:
        print('⚠️  NEEDS MORE WORK - Additional optimization required')

    return success_rate >= 70


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit(0 if success else 1)
    except Exception as e:
        print(f'❌ Test failed: {e}')
        exit(1)