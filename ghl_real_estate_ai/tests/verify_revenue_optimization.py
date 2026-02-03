import asyncio
import json
from decimal import Decimal
from datetime import datetime
from ghl_real_estate_ai.services.dynamic_pricing_optimizer_v2 import create_dynamic_pricing_optimizer_v2, PricingStrategy
from ghl_real_estate_ai.services.roi_calculator_service import roi_calculator

async def verify_revenue_optimization():
    print("🚀 Starting Revenue Optimization Engine Verification...")
    
    optimizer = create_dynamic_pricing_optimizer_v2()
    
    # 1. Test Pricing Calculation
    print("\n--- Testing Pricing Optimization ---")
    lead_data = {
        "lead_id": "v2_test_001",
        "engagement_score": 0.85,
        "urgency_signals": ["pre_approved", "relocating_soon"]
    }
    
    result = await optimizer.calculate_optimized_price(
        lead_id="v2_test_001",
        lead_data=lead_data,
        location_id="test_loc_123",
        strategy=PricingStrategy.VALUE_BASED
    )
    
    print(f"Final Price: ${result.final_price}")
    print(f"Justification: {result.roi_justification}")
    print(f"Sensitivity Score: {result.price_sensitivity_score}")
    
    # 2. Test ROI Reporting
    print("\n--- Testing ROI Reporting ---")
    report = await roi_calculator.generate_client_roi_report("test_loc_123", days=30)
    print(f"ROI Percentage: {report.roi_percentage}%")
    print(f"Total Savings: ${report.total_savings}")
    print(f"Projected Annual Savings: ${report.projections_12mo['projected_annual_savings']}")
    
    # 3. Test Human vs AI Comparison
    print("\n--- Testing Human vs AI Comparison ---")
    comparisons = await roi_calculator.calculate_human_vs_ai_comparison("test_loc_123")
    for comp in comparisons:
        print(f"- {comp.task_name}: {comp.cost_savings_pct}% cost savings, {comp.time_savings_pct}% time savings")
        
    # 4. Test Savings Calculator
    print("\n--- Testing Savings Calculator ---")
    calculator_result = await roi_calculator.get_savings_calculator(150, 8.5, 20.0)
    print(f"Monthly Savings: ${calculator_result['monthly_savings']}")
    print(f"ROI Multiple: {calculator_result['roi_multiple']}x")
    
    print("\n✅ Verification Complete!")

if __name__ == "__main__":
    asyncio.run(verify_revenue_optimization())
