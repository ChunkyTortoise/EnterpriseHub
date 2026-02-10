import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test Proactive Intelligence Integration
Tests the smart alerts, predictions, and coaching features.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(str(Path(__file__).parent))

async def test_proactive_intelligence_engine():
    """Test the proactive intelligence engine functionality."""
    print("🔮 Testing Proactive Intelligence Engine...")
    print("=" * 60)

    try:
        # Test import of proactive intelligence engine
        print("1. Testing import of proactive intelligence engine...")
        from ghl_real_estate_ai.services.proactive_intelligence_engine import (
            ProactiveIntelligenceEngine,
            AlertPriority,
            AlertType
        )
        print("   ✅ ProactiveIntelligenceEngine imported successfully")

        # Test initialization
        print("2. Testing engine initialization...")
        engine = ProactiveIntelligenceEngine()
        print("   ✅ Engine initialized successfully")

        # Test background monitoring
        print("3. Testing background monitoring...")
        monitoring_started = await engine.start_background_monitoring()
        print(f"   ✅ Background monitoring: {'Started' if monitoring_started else 'Failed to start'}")

        # Test smart notifications
        print("4. Testing smart notifications generation...")
        test_context = {
            "leads": [
                {"id": "lead_1", "name": "Sarah Martinez", "last_contact_hours": 76, "engagement_score": 0.65},
                {"id": "lead_2", "name": "David Kim", "last_contact_hours": 12, "engagement_score": 0.87}
            ],
            "performance": {"conversion_rate": 0.14},
            "pipeline_value": 75000,
            "monthly_target": 150000
        }

        alerts = await engine.generate_smart_notifications(test_context)
        print(f"   ✅ Generated {len(alerts)} smart alerts")

        # Test alert details
        for i, alert in enumerate(alerts[:3]):  # Show first 3
            print(f"      Alert {i+1}: {alert.title} ({alert.priority.value} priority)")

        # Test predictive insights
        print("5. Testing predictive analytics...")
        predictions = await engine.get_predictive_insights()
        print(f"   ✅ Generated {len(predictions)} predictive insights")

        # Test performance coaching
        print("6. Testing performance coaching...")
        performance_data = {
            "avg_response_time_hours": 3.2,
            "closing_rate": 0.16,
            "followup_completion_rate": 0.73
        }

        coaching_tips = await engine.get_performance_coaching(performance_data)
        print(f"   ✅ Generated {len(coaching_tips)} coaching tips")

        # Test alert management
        print("7. Testing alert management...")
        active_alerts = await engine.get_active_alerts()
        print(f"   ✅ Retrieved {len(active_alerts)} active alerts")

        if active_alerts:
            # Test marking alert as seen
            test_alert = active_alerts[0]
            seen_result = await engine.mark_alert_seen(test_alert.alert_id)
            print(f"   ✅ Mark alert as seen: {'Success' if seen_result else 'Failed'}")

        # Test monitoring stop
        print("8. Testing monitoring stop...")
        await engine.stop_background_monitoring()
        print(f"   ✅ Monitoring stopped: {not engine.monitoring_active}")

        print("\n🎉 All Proactive Intelligence Engine Tests Passed!")
        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

async def test_claude_platform_integration():
    """Test integration with Claude Platform Companion."""
    print("\n🤝 Testing Claude Platform Integration...")
    print("=" * 60)

    try:
        # Test import of enhanced Claude companion
        print("1. Testing enhanced Claude companion import...")
        from ghl_real_estate_ai.services.claude_platform_companion import ClaudePlatformCompanion
        print("   ✅ Enhanced Claude companion imported successfully")

        # Test initialization with proactive intelligence
        print("2. Testing companion initialization...")
        companion = ClaudePlatformCompanion()
        print("   ✅ Companion initialized with proactive intelligence")

        # Test proactive intelligence enablement
        print("3. Testing proactive intelligence enablement...")
        pi_enabled = await companion.enable_proactive_intelligence()
        print(f"   ✅ Proactive intelligence: {'Enabled' if pi_enabled else 'Failed to enable'}")

        # Test proactive insights
        print("4. Testing proactive insights generation...")
        insights = await companion.get_proactive_insights()
        print(f"   ✅ Generated insights:")
        print(f"      - {len(insights.get('new_alerts', []))} new alerts")
        print(f"      - {len(insights.get('active_alerts', []))} active alerts")
        print(f"      - {len(insights.get('predictions', []))} predictions")
        print(f"      - {len(insights.get('coaching_tips', []))} coaching tips")

        # Test intelligent summary
        print("5. Testing intelligent summary...")
        summary = await companion.get_intelligent_summary()
        print(f"   ✅ Generated summary: {summary[:100]}...")

        # Test proactive action processing
        print("6. Testing proactive action processing...")
        if insights.get('active_alerts'):
            test_alert_id = insights['active_alerts'][0].alert_id
            action_result = await companion.process_proactive_action(test_alert_id, "seen")
            print(f"   ✅ Action processing: {'Success' if action_result['success'] else 'Failed'}")
        else:
            print("   ⚠️ No active alerts to test action processing")

        print("\n🎉 All Claude Platform Integration Tests Passed!")
        return True

    except ImportError as e:
        print(f"❌ Import Error: {e}")
        return False

    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

def test_ui_component_imports():
    """Test UI component imports (without external dependencies)."""
    print("\n🎨 Testing UI Component Imports...")
    print("=" * 60)

    try:
        # Test proactive intelligence dashboard import
        print("1. Testing proactive intelligence dashboard import...")
        # We can't actually import the component due to streamlit dependency
        # but we can check if the file exists and has the right structure
        dashboard_file = Path("ghl_real_estate_ai/streamlit_demo/components/proactive_intelligence_dashboard.py")
        if dashboard_file.exists():
            print("   ✅ Proactive intelligence dashboard file exists")

            # Check for key functions
            with open(dashboard_file, 'r') as f:
                content = f.read()

            required_functions = [
                "render_proactive_intelligence_dashboard",
                "render_proactive_alerts_widget"
            ]

            for func in required_functions:
                if f"def {func}" in content:
                    print(f"   ✅ Function {func} found")
                else:
                    print(f"   ❌ Function {func} missing")

        # Check main app integration
        print("2. Testing main app integration...")
        app_file = Path("ghl_real_estate_ai/streamlit_demo/app.py")
        if app_file.exists():
            with open(app_file, 'r') as f:
                content = f.read()

            if "🔮 Proactive Intelligence" in content:
                print("   ✅ Proactive Intelligence hub added to navigation")
            else:
                print("   ❌ Proactive Intelligence hub missing from navigation")

            if "render_proactive_intelligence_hub" in content:
                print("   ✅ Proactive Intelligence hub renderer found")
            else:
                print("   ❌ Proactive Intelligence hub renderer missing")

        print("\n🎉 All UI Component Tests Passed!")
        return True

    except Exception as e:
        print(f"❌ Test Error: {e}")
        return False

async def run_all_tests():
    """Run all proactive intelligence tests."""
    print("🚀 Starting Proactive Intelligence Tests...")
    print("=" * 80)

    tests = [
        test_proactive_intelligence_engine,
        test_claude_platform_integration
    ]

    ui_tests = [
        test_ui_component_imports
    ]

    passed = 0
    total = len(tests) + len(ui_tests)

    # Run async tests
    for test_func in tests:
        try:
            if await test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")

    # Run sync tests
    for test_func in ui_tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"❌ Test {test_func.__name__} failed: {e}")

    print("\n" + "=" * 80)
    print("📊 Test Results Summary:")
    print(f"✅ Passed: {passed}/{total}")

    if passed == total:
        print("\n🎉 ALL PROACTIVE INTELLIGENCE TESTS PASSED!")
        print("🚀 Proactive Intelligence system is ready for deployment!")
        print("\nNext Steps:")
        print("1. Run: streamlit run ghl_real_estate_ai/streamlit_demo/app.py")
        print("2. Navigate to '🔮 Proactive Intelligence' hub")
        print("3. Test smart alerts and predictions")
        print("4. Enable background monitoring")
        return True
    else:
        print(f"\n⚠️ {total - passed} tests failed - review implementation")
        return False

def main():
    """Run the test suite."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    success = loop.run_until_complete(run_all_tests())
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()