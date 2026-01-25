#!/usr/bin/env python3
"""
Real Data Integration Validation Script
=====================================

Validates that the Market Sentiment Radar correctly integrates with real data sources
and can generate comprehensive sentiment analysis using live data feeds.

Tests:
- Travis County permit data integration
- Economic indicators data integration
- Composite sentiment analysis with real data
- Alert generation from real market conditions

Author: Data Integration Phase - January 2026
"""

import asyncio
import json
from ghl_real_estate_ai.utils.json_utils import safe_json_dumps, EnterpriseJSONEncoder
from datetime import datetime
from typing import Dict, Any
import sys
import os

# Add the parent directory to sys.path to import our modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ghl_real_estate_ai.services.market_sentiment_radar import get_market_sentiment_radar
from ghl_real_estate_ai.services.san_bernardino_county_permits import get_san_bernardino_county_permit_service
from ghl_real_estate_ai.services.economic_indicators_service import get_economic_indicators_service

# Test locations in Rancho Cucamonga area
TEST_LOCATIONS = [
    "91737",  # Rancho Cucamonga East - high-value area
    "91701",  # Rancho Cucamonga Central - established area
    "91729",  # Rancho Cucamonga North - new developments
    "91730",  # Rancho Cucamonga South - family area
    "Rancho Cucamonga, CA 91739",  # West area
    "Ontario, CA 91762",  # Adjacent city
]

async def test_individual_data_sources():
    """Test each real data source individually."""
    print("🔍 Testing Individual Data Sources")
    print("=" * 50)

    # Test San Bernardino County Permits
    print("\n📋 Testing San Bernardino County Permit Service...")
    try:
        permit_service = await get_san_bernardino_county_permit_service()
        permit_signals = await permit_service.fetch_sentiment_data("91737", 30)
        print(f"✅ Permit service returned {len(permit_signals)} signals")
        for signal in permit_signals[:2]:  # Show first 2
            print(f"   - {signal.source}: {signal.raw_content[:60]}...")
    except Exception as e:
        print(f"❌ Permit service error: {e}")

    # Test Economic Indicators
    print("\n📊 Testing Economic Indicators Service...")
    try:
        economic_service = await get_economic_indicators_service()
        economic_signals = await economic_service.fetch_sentiment_data("Rancho Cucamonga, CA", 30)
        print(f"✅ Economic service returned {len(economic_signals)} signals")
        for signal in economic_signals[:2]:  # Show first 2
            print(f"   - {signal.source}: {signal.raw_content[:60]}...")
    except Exception as e:
        print(f"❌ Economic service error: {e}")

async def test_market_sentiment_integration():
    """Test the integrated Market Sentiment Radar with real data."""
    print("\n🎯 Testing Market Sentiment Radar Integration")
    print("=" * 50)

    radar = await get_market_sentiment_radar()

    test_results = {}

    for location in TEST_LOCATIONS:
        print(f"\n📍 Testing {location}...")
        try:
            # Get comprehensive sentiment analysis
            profile = await radar.analyze_market_sentiment(location, timeframe_days=30)

            test_results[location] = {
                'seller_motivation_index': profile.seller_motivation_index,
                'overall_sentiment': profile.overall_sentiment,
                'trend_direction': profile.trend_direction,
                'economic_stress': profile.economic_stress,
                'permit_pressure': profile.permit_pressure,
                'optimal_window': profile.optimal_outreach_window,
                'confidence': profile.confidence_score,
                'signal_count': len(profile.key_signals)
            }

            print(f"   ✅ Seller Motivation: {profile.seller_motivation_index:.1f}/100")
            print(f"   📈 Overall Sentiment: {profile.overall_sentiment:.1f}")
            print(f"   📊 Trend: {profile.trend_direction}")
            print(f"   💰 Economic Stress: {profile.economic_stress:.1f}")
            print(f"   🏗️ Permit Pressure: {profile.permit_pressure:.1f}")
            print(f"   ⏰ Optimal Window: {profile.optimal_outreach_window}")
            print(f"   🎯 Confidence: {profile.confidence_score:.2f}")
            print(f"   📋 Total Signals: {len(profile.key_signals)}")

            # Show top signals from real data sources
            real_signals = [s for s in profile.key_signals
                          if s.source in ['travis_county_permits', 'economic_indicators']]
            if real_signals:
                print(f"   🔥 Real Data Signals:")
                for signal in real_signals[:2]:
                    print(f"      • {signal.source}: {signal.raw_content[:50]}...")

        except Exception as e:
            print(f"   ❌ Error testing {location}: {e}")
            test_results[location] = {'error': str(e)}

    return test_results

async def test_alert_generation():
    """Test alert generation with real data."""
    print("\n🚨 Testing Alert Generation")
    print("=" * 30)

    radar = await get_market_sentiment_radar()

    # Test alert generation for high-value areas
    high_value_areas = ["91737", "91739", "91730"]

    try:
        alerts = await radar.generate_sentiment_alerts(high_value_areas)
        print(f"✅ Generated {len(alerts)} alerts from real data")

        for alert in alerts[:3]:  # Show top 3 alerts
            print(f"\n🚨 {alert.priority.value.upper()} Alert - {alert.location}")
            print(f"   Message: {alert.message}")
            print(f"   Action: {alert.recommended_action}")
            print(f"   Target: {alert.target_audience}")
            print(f"   Timing: {alert.timing_window}")
            print(f"   Lead Quality: {alert.expected_lead_quality:.0f}/100")

        return len(alerts)
    except Exception as e:
        print(f"❌ Alert generation error: {e}")
        return 0

async def test_location_recommendations():
    """Test location recommendation system with real data."""
    print("\n🎯 Testing Location Recommendations")
    print("=" * 35)

    radar = await get_market_sentiment_radar()

    try:
        recommendations = await radar.get_location_recommendations(TEST_LOCATIONS, max_locations=5)
        print(f"✅ Generated {len(recommendations)} location recommendations")

        print("\n📍 Top Prospecting Locations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec['location']}")
            print(f"   📊 Prospecting Score: {rec['prospecting_score']:.1f}")
            print(f"   🎯 Motivation Index: {rec['motivation_index']:.1f}/100")
            print(f"   📈 Trend: {rec['trend']}")
            print(f"   ⏰ Optimal Window: {rec['optimal_window']}")
            print(f"   🔥 Key Triggers: {', '.join(rec['key_triggers'])}")
            print(f"   ✅ Confidence: {rec['confidence']:.2f}")

        return recommendations
    except Exception as e:
        print(f"❌ Location recommendation error: {e}")
        return []

async def main():
    """Run comprehensive real data integration tests."""
    print("🚀 Real Data Integration Validation")
    print("🏢 EnterpriseHub Market Intelligence Platform - Rancho Cucamonga Focus")
    print("⏱️ Starting at:", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)

    # Track overall results
    test_start = datetime.now()
    results = {
        'test_start': test_start.isoformat(),
        'individual_sources': True,
        'market_integration': {},
        'alerts_generated': 0,
        'recommendations': [],
        'errors': []
    }

    try:
        # Test 1: Individual data sources
        await test_individual_data_sources()

        # Test 2: Market sentiment integration
        integration_results = await test_market_sentiment_integration()
        results['market_integration'] = integration_results

        # Test 3: Alert generation
        alert_count = await test_alert_generation()
        results['alerts_generated'] = alert_count

        # Test 4: Location recommendations
        recommendations = await test_location_recommendations()
        results['recommendations'] = recommendations

        # Summary
        test_duration = (datetime.now() - test_start).total_seconds()
        print("\n" + "=" * 60)
        print("📊 INTEGRATION TEST SUMMARY")
        print("=" * 60)
        print(f"⏱️ Total Test Time: {test_duration:.1f} seconds")
        print(f"📍 Locations Tested: {len(TEST_LOCATIONS)}")
        print(f"✅ Successful Analyses: {len([r for r in integration_results.values() if 'error' not in r])}")
        print(f"🚨 Alerts Generated: {alert_count}")
        print(f"🎯 Recommendations: {len(recommendations)}")

        success_rate = len([r for r in integration_results.values() if 'error' not in r]) / len(TEST_LOCATIONS)
        print(f"📈 Success Rate: {success_rate * 100:.1f}%")

        results['success_rate'] = success_rate
        results['test_duration'] = test_duration
        results['test_end'] = datetime.now().isoformat()

        # Determine overall status
        if success_rate >= 0.8 and alert_count > 0:
            status = "✅ PRODUCTION READY"
        elif success_rate >= 0.6:
            status = "⚠️ NEEDS MINOR FIXES"
        else:
            status = "❌ NEEDS MAJOR FIXES"

        print(f"\n🎯 OVERALL STATUS: {status}")

        # Save detailed results
        with open('real_data_integration_results.json', 'w') as f:
            json.dump(results, f, indent=2, cls=EnterpriseJSONEncoder)
        print(f"\n📄 Detailed results saved to: real_data_integration_results.json")

    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {e}")
        results['critical_error'] = str(e)

    return results

if __name__ == "__main__":
    # Run the validation tests
    asyncio.run(main())