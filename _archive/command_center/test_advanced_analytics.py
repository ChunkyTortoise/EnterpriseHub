import pytest

@pytest.mark.unit
#!/usr/bin/env python3
"""
Test script for Advanced Analytics Dashboard
===========================================

Simple test to verify the advanced analytics dashboard loads correctly
and all components render without errors.

Usage:
    python test_advanced_analytics.py

Author: Claude Command Center
Created: January 2026
"""

import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, project_root)

def test_advanced_analytics_import():
    """Test that we can import the advanced analytics dashboard"""
    try:
        from components.advanced_analytics import (
            AdvancedAnalyticsDashboard,
            render_advanced_analytics_dashboard,
            CohortMetrics,
            FunnelMetrics,
            AttributionMetrics,
            MarketIntelligence
        )
        print("✅ Advanced Analytics Dashboard imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_dashboard_initialization():
    """Test dashboard initialization"""
    try:
        from components.advanced_analytics import AdvancedAnalyticsDashboard

        dashboard = AdvancedAnalyticsDashboard()
        print("✅ Advanced Analytics Dashboard initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Initialization error: {e}")
        return False

def test_mock_data_generation():
    """Test mock data generation methods"""
    try:
        from components.advanced_analytics import AdvancedAnalyticsDashboard

        dashboard = AdvancedAnalyticsDashboard()

        # Test cohort data generation
        cohort_data = dashboard._generate_mock_cohort_data()
        assert len(cohort_data) == 12, f"Expected 12 cohorts, got {len(cohort_data)}"
        print(f"✅ Generated {len(cohort_data)} cohort records")

        # Test funnel data generation
        funnel_data = dashboard._generate_mock_funnel_data()
        assert hasattr(funnel_data, 'leads_generated'), "Funnel data missing leads_generated"
        print(f"✅ Generated funnel data with {funnel_data.leads_generated} leads")

        # Test attribution data generation
        attribution_data = dashboard._generate_mock_attribution_data()
        assert len(attribution_data) > 0, "No attribution data generated"
        print(f"✅ Generated {len(attribution_data)} attribution touchpoints")

        # Test market intelligence generation
        market_data = dashboard._generate_mock_market_intelligence()
        assert hasattr(market_data, 'market_share'), "Market data missing market_share"
        print(f"✅ Generated market intelligence with {market_data.market_share:.1%} market share")

        return True
    except Exception as e:
        print(f"❌ Mock data generation error: {e}")
        return False

def test_data_structures():
    """Test that data structures are properly defined"""
    try:
        from components.advanced_analytics import (
            CohortMetrics,
            FunnelMetrics,
            AttributionMetrics,
            MarketIntelligence
        )
        from datetime import date
        from decimal import Decimal

        # Test CohortMetrics creation
        cohort = CohortMetrics(
            cohort_date=date.today(),
            cohort_size=100,
            period_0_conversion=0.2,
            period_1_conversion=0.3,
            period_2_conversion=0.4,
            period_3_conversion=0.5,
            period_4_conversion=0.6,
            period_8_conversion=0.65,
            period_12_conversion=0.67,
            total_revenue=Decimal("1000000"),
            avg_deal_value=Decimal("485000"),
            retention_curve=[0.2, 0.3, 0.4, 0.5, 0.6, 0.65, 0.67]
        )
        print("✅ CohortMetrics data structure works correctly")

        # Test FunnelMetrics creation
        funnel = FunnelMetrics(
            leads_generated=1000,
            qualified_leads=680,
            showing_scheduled=306,
            under_contract=98,
            closed_deals=76,
            qualification_rate=0.68,
            showing_rate=0.45,
            contract_rate=0.32,
            close_rate=0.78,
            avg_qualification_time=14.5,
            avg_showing_time=3.2,
            avg_contract_time=12.8,
            avg_close_time=31.5,
            predicted_closings=80,
            confidence_score=0.87
        )
        print("✅ FunnelMetrics data structure works correctly")

        return True
    except Exception as e:
        print(f"❌ Data structure error: {e}")
        return False

def main():
    """Run all tests"""
    print("🔥 Testing Advanced Analytics Dashboard")
    print("=" * 50)

    tests = [
        test_advanced_analytics_import,
        test_dashboard_initialization,
        test_data_structures,
        test_mock_data_generation
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()

    print("=" * 50)
    print(f"📊 Test Results: {passed} passed, {failed} failed")

    if failed == 0:
        print("🎉 All tests passed! Advanced Analytics Dashboard is ready.")
        return True
    else:
        print("⚠️  Some tests failed. Please review the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)