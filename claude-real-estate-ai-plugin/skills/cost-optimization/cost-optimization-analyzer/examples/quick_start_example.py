#!/usr/bin/env python3
"""
Cost Optimization Analyzer - Quick Start Example
Demonstrates how to quickly implement cost monitoring and optimization
"""

import sys
import os
from pathlib import Path

# Add the project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.append(str(project_root))

def demonstrate_cost_optimization():
    """Demonstrate the key cost optimization features"""

    print("🔧 Cost Optimization Analyzer - Quick Start Demo")
    print("=" * 60)

    # 1. Infrastructure Cost Analysis
    print("\n📊 1. Infrastructure Cost Analysis")
    print("-" * 40)

    # Simulated current costs
    current_costs = {
        'railway_compute': 45.00,
        'database_storage': 25.00,
        'api_calls_anthropic': 120.00,
        'api_calls_openai': 85.00,
        'bandwidth': 15.00
    }

    # Calculate total
    total_monthly_cost = sum(current_costs.values())
    print(f"Current Monthly Costs: ${total_monthly_cost:.2f}")

    for service, cost in current_costs.items():
        percentage = (cost / total_monthly_cost) * 100
        print(f"  • {service.replace('_', ' ').title()}: ${cost:.2f} ({percentage:.1f}%)")

    # 2. Optimization Opportunities
    print("\n💡 2. Optimization Opportunities")
    print("-" * 40)

    optimizations = {
        'api_calls_anthropic': {
            'current': 120.00,
            'optimized': 75.00,
            'method': 'Intelligent caching and request batching',
            'savings_percent': 37.5
        },
        'railway_compute': {
            'current': 45.00,
            'optimized': 35.00,
            'method': 'Right-sizing based on actual usage patterns',
            'savings_percent': 22.2
        },
        'api_calls_openai': {
            'current': 85.00,
            'optimized': 60.00,
            'method': 'Use cheaper models for non-critical operations',
            'savings_percent': 29.4
        }
    }

    total_savings = 0
    for service, opt in optimizations.items():
        savings = opt['current'] - opt['optimized']
        total_savings += savings
        print(f"  🎯 {service.replace('_', ' ').title()}:")
        print(f"     Current: ${opt['current']:.2f} → Optimized: ${opt['optimized']:.2f}")
        print(f"     Savings: ${savings:.2f}/month ({opt['savings_percent']:.1f}%)")
        print(f"     Method: {opt['method']}")
        print()

    # 3. ROI Calculation
    print("💰 3. ROI Calculation")
    print("-" * 40)

    annual_savings = total_savings * 12
    optimization_investment = 20 * 150  # 20 hours at $150/hour

    roi_percentage = ((annual_savings - optimization_investment) / optimization_investment) * 100
    payback_months = optimization_investment / total_savings

    print(f"Monthly Savings: ${total_savings:.2f}")
    print(f"Annual Savings: ${annual_savings:.2f}")
    print(f"Investment Required: ${optimization_investment:.2f}")
    print(f"ROI: {roi_percentage:.1f}%")
    print(f"Payback Period: {payback_months:.1f} months")

    # 4. Implementation Priority
    print("\n🚀 4. Implementation Priority")
    print("-" * 40)

    # Sort by ROI (savings / implementation effort)
    implementation_priorities = [
        {
            'optimization': 'API Request Caching',
            'savings': 45.00,
            'effort_hours': 8,
            'roi_score': 45.00 / 8
        },
        {
            'optimization': 'Infrastructure Right-sizing',
            'savings': 10.00,
            'effort_hours': 4,
            'roi_score': 10.00 / 4
        },
        {
            'optimization': 'API Model Optimization',
            'savings': 25.00,
            'effort_hours': 12,
            'roi_score': 25.00 / 12
        }
    ]

    # Sort by ROI score
    implementation_priorities.sort(key=lambda x: x['roi_score'], reverse=True)

    for i, priority in enumerate(implementation_priorities, 1):
        print(f"  {i}. {priority['optimization']}")
        print(f"     Monthly Savings: ${priority['savings']:.2f}")
        print(f"     Implementation: {priority['effort_hours']} hours")
        print(f"     ROI Score: {priority['roi_score']:.1f} (savings per hour)")
        print()

    # 5. Quick Implementation Guide
    print("📋 5. Quick Implementation Steps")
    print("-" * 40)

    steps = [
        "1. Set up cost monitoring dashboard (15 minutes)",
        "2. Implement API response caching (4 hours)",
        "3. Configure infrastructure monitoring (30 minutes)",
        "4. Optimize database queries (2 hours)",
        "5. Set up automated cost alerts (20 minutes)"
    ]

    for step in steps:
        print(f"  ✓ {step}")

    total_implementation_time = 6.75  # hours
    print(f"\nTotal Implementation Time: {total_implementation_time} hours")
    print(f"Expected Monthly Savings: ${total_savings:.2f}")
    print(f"Time to Value: Immediate cost visibility, {payback_months:.1f} months full ROI")

if __name__ == "__main__":
    demonstrate_cost_optimization()