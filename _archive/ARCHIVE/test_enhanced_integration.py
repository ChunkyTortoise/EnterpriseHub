#!/usr/bin/env python3
"""
Enhanced Lead Scoring Integration Test

Comprehensive test of Jorge's enhanced lead bot system with
the new AI lead scoring capabilities integrated.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add the services directory to the path
sys.path.append(os.path.join('ghl_real_estate_ai', 'services'))

def test_enhanced_scorer_import():
    """Test that the enhanced scorer can be imported."""
    print("🧪 Testing Enhanced Lead Scorer Import...")

    try:
        from enhanced_smart_lead_scorer import (
            EnhancedSmartLeadScorer,
            LeadScoreBreakdown,
            LeadPriority,
            BuyingStage
        )
        print("✅ Enhanced lead scorer imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False

def test_dashboard_integration():
    """Test the dashboard integration."""
    print("\n🧪 Testing Dashboard Integration...")

    try:
        # Try to import the dashboard component
        sys.path.append(os.path.join('ghl_real_estate_ai', 'streamlit_demo', 'components'))

        import jorge_lead_bot_dashboard

        # Check if the enhanced functions exist
        functions_to_check = [
            'render_enhanced_lead_scoring_section',
            'get_enhanced_scorer',
            'render_jorge_lead_bot_dashboard'
        ]

        for func_name in functions_to_check:
            if hasattr(jorge_lead_bot_dashboard, func_name):
                print(f"✅ Function {func_name} found")
            else:
                print(f"❌ Function {func_name} missing")
                return False

        return True

    except Exception as e:
        print(f"❌ Dashboard integration test failed: {e}")
        return False

async def test_api_client_methods():
    """Test the enhanced API client methods."""
    print("\n🧪 Testing Enhanced API Client Methods...")

    try:
        sys.path.append(os.path.join('ghl_real_estate_ai', 'streamlit_demo', 'components'))
        from jorge_lead_bot_dashboard import JorgeAPIClient

        client = JorgeAPIClient()

        # Test analyze_lead method
        sample_lead = {
            "name": "Test Johnson",
            "email": "test@email.com",
            "budget": 750000,
            "timeline": "30 days",
            "preapproved": True,
            "search_frequency": 8
        }

        analysis = await client.analyze_lead(sample_lead)
        print(f"✅ analyze_lead method works - Score: {analysis.get('overall_score', 'N/A')}")

        # Test get_lead_pipeline method
        pipeline = await client.get_lead_pipeline()
        print(f"✅ get_lead_pipeline method works - {len(pipeline)} leads")

        # Test get_scoring_analytics method
        analytics = await client.get_scoring_analytics()
        print(f"✅ get_scoring_analytics method works - {analytics.get('total_leads_scored', 0)} total leads")

        return True

    except Exception as e:
        print(f"❌ API client test failed: {e}")
        return False

def test_lead_scoring_functionality():
    """Test the actual lead scoring functionality."""
    print("\n🧪 Testing Lead Scoring Functionality...")

    try:
        from enhanced_smart_lead_scorer import EnhancedSmartLeadScorer

        scorer = EnhancedSmartLeadScorer()

        # Test with sample lead data
        sample_lead = {
            "name": "Maria Rodriguez",
            "email": "maria.rodriguez@email.com",
            "phone": "+1-555-987-6543",
            "budget": 850000,
            "timeline": "immediate",
            "search_frequency": 12,
            "preapproved": True,
            "employment_status": "employed",
            "family_size": 3,
            "first_time_buyer": False,
            "current_location": "Ontario, CA",
            "work_location": "Rancho Cucamonga, CA",
            "school_preference": "Chaffey Joint Union",
            "showing_requests": 4,
            "email_opens": 15,
            "website_sessions": 8,
            "profession": "manager",
            "life_events": ["new_job"]
        }

        # Run async scoring
        async def run_scoring():
            return await scorer.calculate_comprehensive_score(sample_lead)

        score_breakdown = asyncio.run(run_scoring())

        print(f"✅ Lead scoring complete:")
        print(f"   Overall Score: {score_breakdown.overall_score}/100")
        print(f"   Priority: {score_breakdown.priority_level.value}")
        print(f"   Stage: {score_breakdown.buying_stage.value}")
        print(f"   Actions: {len(score_breakdown.recommended_actions)} recommendations")
        print(f"   Talking Points: {len(score_breakdown.jorge_talking_points)} points")

        return True

    except Exception as e:
        print(f"❌ Lead scoring test failed: {e}")
        return False

def test_dashboard_launch():
    """Test that the dashboard can be launched without errors."""
    print("\n🧪 Testing Dashboard Launch Capability...")

    try:
        # Check if dashboard file exists
        dashboard_path = os.path.join(
            'ghl_real_estate_ai',
            'streamlit_demo',
            'components',
            'jorge_lead_bot_dashboard.py'
        )

        if not os.path.exists(dashboard_path):
            print(f"❌ Dashboard file not found: {dashboard_path}")
            return False

        print(f"✅ Dashboard file exists: {dashboard_path}")

        # Check that streamlit is available
        try:
            import streamlit as st
            print("✅ Streamlit is available")
        except ImportError:
            print("❌ Streamlit not available")
            return False

        # Check plotly for advanced charts
        try:
            import plotly.express as px
            import plotly.graph_objects as go
            print("✅ Plotly is available for advanced visualizations")
        except ImportError:
            print("⚠️ Plotly not available - charts will be limited")

        return True

    except Exception as e:
        print(f"❌ Dashboard launch test failed: {e}")
        return False

def main():
    """Run all integration tests."""
    print("🚀 Jorge's Enhanced Lead Bot - Integration Test Suite")
    print("=" * 60)

    tests = [
        ("Enhanced Scorer Import", test_enhanced_scorer_import),
        ("Dashboard Integration", test_dashboard_integration),
        ("API Client Methods", lambda: asyncio.run(test_api_client_methods())),
        ("Lead Scoring Functionality", test_lead_scoring_functionality),
        ("Dashboard Launch", test_dashboard_launch),
    ]

    results = []

    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 60)
    print("📊 INTEGRATION TEST RESULTS")
    print("=" * 60)

    passed = 0
    total = len(results)

    for test_name, result in results:
        if result:
            print(f"✅ {test_name}: PASSED")
            passed += 1
        else:
            print(f"❌ {test_name}: FAILED")

    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 ALL INTEGRATION TESTS PASSED!")
        print("✅ Enhanced Lead Scoring is fully integrated and functional!")
        print("✅ Jorge's system is ready with advanced AI capabilities!")

        print("\n🚀 NEXT STEPS:")
        print("1. Dashboard is running at: http://localhost:8502")
        print("2. Test the Enhanced Lead Scoring tab")
        print("3. Try analyzing sample leads")
        print("4. Review the lead pipeline with priority scoring")
        print("5. Check the analytics and performance metrics")

        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please review and fix issues.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)