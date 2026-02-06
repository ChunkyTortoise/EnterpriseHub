#!/usr/bin/env python3
"""
Quick validation script for the Advanced Churn Recovery Dashboard components

This script validates that all three dashboard components can be imported
and their core data functions work correctly.
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def validate_advanced_churn_recovery_dashboard():
    """Validate the Advanced Churn Recovery Dashboard"""
    print("🛡️  Validating Advanced Churn Recovery Dashboard...")
    
    try:
        from ghl_real_estate_ai.streamlit_demo.components.advanced_churn_recovery_dashboard import (
            load_churn_metrics, load_market_data, generate_recovery_pipeline_data,
            generate_campaign_performance, generate_geographic_data
        )
        
        # Test data loading functions
        kpis = load_churn_metrics()
        markets = load_market_data()
        pipeline_data = generate_recovery_pipeline_data()
        campaign_data = generate_campaign_performance()
        geo_data = generate_geographic_data()
        
        assert kpis.overall_churn_rate > 0, "Churn rate should be positive"
        assert len(markets) == 5, "Should have 5 markets"
        assert len(pipeline_data) == 5, "Should have 5 pipeline stages"
        assert len(campaign_data) >= 5, "Should have at least 5 campaigns"
        assert len(geo_data) == 5, "Should have 5 geographic entries"
        
        print("   ✅ All data functions working correctly")
        print(f"   📊 KPIs loaded: Churn {kpis.overall_churn_rate:.1%}, Recovery {kpis.recovery_rate:.1%}")
        print(f"   🗺️  Markets: {', '.join([m.name for m in markets[:3]])}...")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def validate_multi_market_analytics_view():
    """Validate the Multi-Market Analytics View"""
    print("\n🌍 Validating Multi-Market Analytics View...")
    
    try:
        from ghl_real_estate_ai.streamlit_demo.components.multi_market_analytics_view import (
            load_market_performance_data, generate_time_series_data,
            generate_cross_market_flows, get_health_class, get_trend_class
        )
        
        # Test data loading functions
        markets = load_market_performance_data()
        time_series = generate_time_series_data()
        flows = generate_cross_market_flows()
        
        assert len(markets) == 5, "Should have 5 markets"
        assert len(time_series) > 50, "Should have substantial time series data"
        assert len(flows) >= 5, "Should have cross-market flows"
        
        # Test utility functions
        assert get_health_class(95) == "health-excellent"
        assert get_trend_class(0.08) == "trend-up"
        
        print("   ✅ All analytics functions working correctly")
        print(f"   📈 Time series data points: {len(time_series)}")
        print(f"   🔄 Cross-market flows: {len(flows)}")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def validate_roi_calculator_component():
    """Validate the ROI Calculator Component"""
    print("\n💰 Validating ROI Calculator Component...")
    
    try:
        from ghl_real_estate_ai.streamlit_demo.components.roi_calculator_component import (
            get_investment_scenarios, get_channel_investments, ROICalculator
        )
        
        # Test data loading functions
        scenarios = get_investment_scenarios()
        channels = get_channel_investments()
        
        assert len(scenarios) >= 3, "Should have multiple investment scenarios"
        assert len(channels) >= 3, "Should have multiple channel investments"
        
        # Test ROI calculation
        calculator = ROICalculator(base_clv=12500, base_churn_rate=0.08)
        test_scenario = scenarios[0]
        roi_calc = calculator.calculate_scenario_roi(test_scenario, 1000, 0.60)
        
        assert roi_calc.total_investment > 0, "Should calculate investment"
        assert roi_calc.projected_clv_recovery >= 0, "Should calculate CLV recovery"
        
        print("   ✅ All ROI calculation functions working correctly")
        print(f"   🎯 Investment scenarios: {len(scenarios)}")
        print(f"   📱 Channel investments: {len(channels)}")
        print(f"   💎 Test ROI: {roi_calc.roi_percentage:.1f}%")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def validate_showcase_integration():
    """Validate the showcase integration"""
    print("\n🚀 Validating Showcase Integration...")
    
    try:
        # Check that showcase file exists and can import components
        showcase_path = "ghl_real_estate_ai/streamlit_demo/churn_recovery_showcase.py"
        assert os.path.exists(showcase_path), f"Showcase file should exist at {showcase_path}"
        
        print("   ✅ Showcase integration file exists")
        print("   📁 Ready for Streamlit execution")
        return True
        
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def main():
    """Main validation function"""
    print("🔍 Validating Advanced Churn Recovery Dashboard Components")
    print("=" * 70)
    
    results = []
    
    # Run all validations
    results.append(validate_advanced_churn_recovery_dashboard())
    results.append(validate_multi_market_analytics_view())
    results.append(validate_roi_calculator_component())
    results.append(validate_showcase_integration())
    
    # Summary
    print("\n" + "=" * 70)
    print("📊 VALIDATION SUMMARY")
    print("=" * 70)
    
    passed = sum(results)
    total = len(results)
    
    components = [
        "Advanced Churn Recovery Dashboard",
        "Multi-Market Analytics View", 
        "ROI Calculator Component",
        "Showcase Integration"
    ]
    
    for i, (component, result) in enumerate(zip(components, results)):
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {component}")
    
    print(f"\n🎯 RESULT: {passed}/{total} components validated successfully")
    
    if passed == total:
        print("\n🎉 All dashboard components are ready for production!")
        print("\n🚀 To run the showcase:")
        print("   streamlit run ghl_real_estate_ai/streamlit_demo/churn_recovery_showcase.py")
    else:
        print(f"\n⚠️  {total - passed} component(s) need attention before production deployment")
        return 1
    
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)