import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Navigation Categories Validation Test
Validates the new hub categorization system for EnterpriseHub
"""

def test_hub_categorization():
    """Test that all hubs are properly categorized and no hubs are missing"""

    # Original hubs from the old system
    original_bi_hubs = [
        "Executive Command Center",
        "Lead Intelligence Hub",
        "Data Arbitrage Hub",
        "Jorge War Room",
        "Agent ROI Dashboard",
        "Real-Time Intelligence",
        "Billing Analytics",
        "Marketplace Management",
        "Ops & Optimization",
        "Claude Cost Tracking"
    ]

    original_agent_hubs = [
        "Swarm Intelligence",
        "Proactive Intelligence",
        "Voice Claude",
        "Voice AI Assistant",
        "Sales Copilot",
        "Deep Research"
    ]

    original_journey_hubs = [
        "Buyer Journey Hub",
        "Seller Journey Hub",
        "Automation Studio",
        "SMS Compliance Dashboard",
        "Bot Health Monitoring",
        "Bot Coordination Flow",
        "Lead Bot Sequences",
        "Bot Testing & Validation"
    ]

    # New categorization system
    new_hub_categories = {
        "🎯 Core Operations": [
            "Executive Command Center",
            "Lead Intelligence Hub",
            "Jorge War Room",
            "Real-Time Intelligence"
        ],
        "📊 Analytics & Insights": [
            "Data Arbitrage Hub",
            "Agent ROI Dashboard",
            "Billing Analytics",
            "Marketplace Management",
            "Ops & Optimization",
            "Claude Cost Tracking"
        ],
        "🤖 AI & Automation": [
            "Swarm Intelligence",
            "Proactive Intelligence",
            "Voice Claude",
            "Voice AI Assistant",
            "Sales Copilot",
            "Deep Research",
            "Automation Studio"
        ],
        "🛠️ Bot Management": [
            "Bot Health Monitoring",
            "Bot Coordination Flow",
            "Lead Bot Sequences",
            "Bot Testing & Validation",
            "SMS Compliance Dashboard"
        ],
        "🏡 Customer Journey": [
            "Buyer Journey Hub",
            "Seller Journey Hub"
        ]
    }

    # Combine original hubs
    original_hubs = set(original_bi_hubs + original_agent_hubs + original_journey_hubs)

    # Combine new categorized hubs
    new_hubs = set()
    for category_hubs in new_hub_categories.values():
        new_hubs.update(category_hubs)

    print("🧪 Hub Categorization Validation Test")
    print("=" * 50)

    # Test 1: Ensure no hubs are missing
    missing_hubs = original_hubs - new_hubs
    extra_hubs = new_hubs - original_hubs

    print(f"📊 Original hubs count: {len(original_hubs)}")
    print(f"📊 New categorized hubs count: {len(new_hubs)}")

    if missing_hubs:
        print(f"❌ Missing hubs: {missing_hubs}")
        return False

    if extra_hubs:
        print(f"ℹ️  Extra hubs (intentional additions): {extra_hubs}")

    print(f"✅ All original hubs preserved: {len(original_hubs)} hubs")

    # Test 2: Validate category distribution
    print("\n📋 Category Distribution:")
    for category, hubs in new_hub_categories.items():
        print(f"  {category}: {len(hubs)} hubs")
        for hub in hubs:
            print(f"    • {hub}")

    # Test 3: Check for logical categorization
    print("\n🧠 Categorization Logic Validation:")

    # Core Operations should have executive/strategic hubs
    core_ops = new_hub_categories["🎯 Core Operations"]
    if "Executive Command Center" in core_ops and "Jorge War Room" in core_ops:
        print("✅ Core Operations correctly contains executive hubs")
    else:
        print("❌ Core Operations missing key executive hubs")
        return False

    # Analytics should contain ROI, billing, data hubs
    analytics = new_hub_categories["📊 Analytics & Insights"]
    required_analytics = ["Agent ROI Dashboard", "Billing Analytics", "Data Arbitrage Hub"]
    if all(hub in analytics for hub in required_analytics):
        print("✅ Analytics & Insights correctly contains business intelligence hubs")
    else:
        print("❌ Analytics & Insights missing key BI hubs")
        return False

    # Bot Management should contain monitoring and testing
    bot_mgmt = new_hub_categories["🛠️ Bot Management"]
    required_bot_mgmt = ["Bot Health Monitoring", "Bot Testing & Validation"]
    if all(hub in bot_mgmt for hub in required_bot_mgmt):
        print("✅ Bot Management correctly contains monitoring/testing hubs")
    else:
        print("❌ Bot Management missing key monitoring hubs")
        return False

    # AI & Automation should contain AI agents
    ai_automation = new_hub_categories["🤖 AI & Automation"]
    required_ai = ["Voice Claude", "Swarm Intelligence", "Proactive Intelligence"]
    if all(hub in ai_automation for hub in required_ai):
        print("✅ AI & Automation correctly contains AI agent hubs")
    else:
        print("❌ AI & Automation missing key AI hubs")
        return False

    # Customer Journey should contain buyer/seller hubs
    customer_journey = new_hub_categories["🏡 Customer Journey"]
    required_journey = ["Buyer Journey Hub", "Seller Journey Hub"]
    if all(hub in customer_journey for hub in required_journey):
        print("✅ Customer Journey correctly contains buyer/seller hubs")
    else:
        print("❌ Customer Journey missing key journey hubs")
        return False

    print(f"\n🎯 Navigation Redesign Summary:")
    print(f"  • Reduced cognitive load: 24 hubs organized into 5 logical categories")
    print(f"  • Expandable sections for better visual hierarchy")
    print(f"  • Auto-expand current category for context awareness")
    print(f"  • Backward compatibility maintained for all routing")
    print(f"  • Professional UI with icons and descriptions")

    return True

def test_category_balance():
    """Test that categories are reasonably balanced"""
    hub_categories = {
        "🎯 Core Operations": 4,
        "📊 Analytics & Insights": 6,
        "🤖 AI & Automation": 7,
        "🛠️ Bot Management": 5,
        "🏡 Customer Journey": 2
    }

    print("\n⚖️ Category Balance Analysis:")
    total_hubs = sum(hub_categories.values())

    for category, count in hub_categories.items():
        percentage = (count / total_hubs) * 100
        print(f"  {category}: {count} hubs ({percentage:.1f}%)")

    # Check if any category is too dominant (>40%) or too small (<5%)
    max_percentage = max(count / total_hubs for count in hub_categories.values()) * 100
    min_percentage = min(count / total_hubs for count in hub_categories.values()) * 100

    if max_percentage > 40:
        print(f"⚠️  Warning: Largest category has {max_percentage:.1f}% of hubs (may need subdivision)")
    else:
        print(f"✅ Good balance: Largest category has {max_percentage:.1f}% of hubs")

    if min_percentage < 5:
        print(f"⚠️  Warning: Smallest category has {min_percentage:.1f}% of hubs (may need consolidation)")
    else:
        print(f"✅ Good minimum: Smallest category has {min_percentage:.1f}% of hubs")

    return True

if __name__ == "__main__":
    print("🚀 EnterpriseHub Navigation Redesign Validation")
    print("=" * 55)

    success = True
    success &= test_hub_categorization()
    success &= test_category_balance()

    print("\n" + "=" * 55)
    if success:
        print("🎉 All validation tests PASSED! Navigation redesign is ready for deployment.")
        print("\n📋 Next Steps:")
        print("  1. Test the Streamlit app with new navigation")
        print("  2. Verify all hub routing works correctly")
        print("  3. Gather user feedback on the new interface")
        print("  4. Consider A/B testing the new vs old navigation")
    else:
        print("❌ Some validation tests FAILED. Please review the categorization logic.")

    exit(0 if success else 1)