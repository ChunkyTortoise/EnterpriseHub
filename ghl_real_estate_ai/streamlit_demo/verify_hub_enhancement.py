#!/usr/bin/env python3
"""
Verification script for Lead Intelligence Hub enhancements.
Tests that all components load correctly and Sarah Chen data is present.
"""
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "streamlit_demo"))
sys.path.insert(0, str(project_root / "streamlit_demo" / "components"))

def test_sarah_chen_data():
    """Verify Sarah Chen lead data exists and has correct attributes"""
    from components.interactive_lead_map import generate_sample_lead_data
    
    print("Testing Sarah Chen lead data...")
    data = generate_sample_lead_data("Austin")
    
    sarah = next((l for l in data if "Sarah Chen" in l['name'] and "Apple" in l['name']), None)
    assert sarah is not None, "❌ Sarah Chen (Apple Engineer) lead data missing"
    assert sarah['occupation'] == "Apple Engineer", "❌ Occupation not set correctly"
    assert sarah['lead_score'] == 100, "❌ Lead score should be 100"
    assert sarah['budget'] == 550000, "❌ Budget should be $550,000"
    assert "Round Rock" in sarah['location'], "❌ Location should include Round Rock"
    assert "URGENT" in sarah['timeline'], "❌ Timeline should indicate urgency"
    assert sarah['financing'] == "Pre-approved", "❌ Financing should be Pre-approved"
    
    print("✅ Sarah Chen data verified successfully")
    print(f"   - Name: {sarah['name']}")
    print(f"   - Occupation: {sarah['occupation']}")
    print(f"   - Lead Score: {sarah['lead_score']}")
    print(f"   - Location: {sarah['location']}")
    print(f"   - Budget: ${sarah['budget']:,}")
    return True

def test_comprehensive_hub_import():
    """Verify comprehensive lead intelligence hub can be imported"""
    print("\nTesting comprehensive hub imports...")
    
    from components.comprehensive_lead_intelligence_hub import (
        render_comprehensive_lead_intelligence_hub,
        render_quick_actions_dashboard,
        render_claude_lead_insights
    )
    
    print("✅ Comprehensive hub components imported successfully")
    print("   - render_comprehensive_lead_intelligence_hub")
    print("   - render_quick_actions_dashboard")  
    print("   - render_claude_lead_insights")
    return True

def test_app_integration():
    """Verify app.py can import render_complete_enhanced_hub"""
    print("\nTesting app.py integration...")
    
    sys.path.insert(0, str(project_root / "streamlit_demo" / "services"))
    from lead_intelligence_integration import render_complete_enhanced_hub, get_intelligence_status
    
    status = get_intelligence_status()
    assert status['initialized'] == True, "❌ Intelligence system not initialized"
    assert status['version'] == "2.0.0", "❌ Version mismatch"
    
    print("✅ App integration verified successfully")
    print(f"   - Intelligence Status: {status}")
    return True

def run_all_tests():
    """Run all verification tests"""
    print("=" * 60)
    print("🧪 Lead Intelligence Hub Enhancement Verification")
    print("=" * 60)
    print()
    
    try:
        test_sarah_chen_data()
        test_comprehensive_hub_import()
        test_app_integration()
        
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED - Enhancement Successful!")
        print("=" * 60)
        return True
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        return False
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("=" * 60)
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
