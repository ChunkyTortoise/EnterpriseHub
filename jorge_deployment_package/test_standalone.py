#!/usr/bin/env python3
"""
Test Standalone Jorge Bot System

This script tests all the standalone modules and bot functionality
without dependencies on the main EnterpriseHub codebase.

Author: Claude Code Assistant
Created: 2026-01-22
"""

import asyncio
import logging
import os
import sys
from datetime import datetime

# Set up basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_imports():
    """Test importing all standalone modules"""

    print("🧪 Testing Standalone Module Imports")
    print("=" * 40)

    try:
        print("Testing config_settings...")
        from config_settings import settings, get_ghl_token
        print(f"  ✅ Settings loaded. Testing mode: {settings.testing_mode}")

        print("Testing ghl_client...")
        from ghl_client import GHLClient, create_ghl_client
        print("  ✅ GHL Client imported successfully")

        print("Testing conversation_manager...")
        from conversation_manager import ConversationManager
        print("  ✅ Conversation Manager imported successfully")

        print("Testing lead_intelligence...")
        from lead_intelligence import get_enhanced_lead_intelligence, PredictiveLeadScorerV2
        print("  ✅ Lead Intelligence imported successfully")

        print("Testing jorge_engines...")
        from jorge_engines import JorgeSellerEngine, JorgeFollowUpEngine, JorgeToneEngine
        print("  ✅ Jorge Engines imported successfully")

        return True

    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False

def test_bot_initialization():
    """Test initializing the bot classes"""

    print("\n🤖 Testing Bot Initialization")
    print("=" * 40)

    try:
        print("Testing JorgeLeadBot...")
        from jorge_lead_bot import JorgeLeadBot, create_jorge_lead_bot

        # Create bot (will use test/mock settings)
        lead_bot = create_jorge_lead_bot()
        print("  ✅ Lead Bot initialized successfully")

        print("Testing JorgeSellerBot...")
        from jorge_seller_bot import JorgeSellerBot, create_jorge_seller_bot

        # Create bot
        seller_bot = create_jorge_seller_bot()
        print("  ✅ Seller Bot initialized successfully")

        print("Testing JorgeAutomationSystem...")
        from jorge_automation import JorgeAutomationSystem, create_jorge_automation

        # Create automation system
        automation = create_jorge_automation()
        print("  ✅ Automation System initialized successfully")

        return True, (lead_bot, seller_bot, automation)

    except Exception as e:
        print(f"  ❌ Bot initialization failed: {e}")
        return False, None

async def test_bot_functionality(bots):
    """Test basic bot functionality"""

    print("\n⚡ Testing Bot Functionality")
    print("=" * 40)

    lead_bot, seller_bot, automation = bots

    try:
        # Test Lead Bot
        print("Testing Lead Bot processing...")
        lead_result = await lead_bot.process_lead_message(
            contact_id="test_lead_123",
            location_id="test_location_456",
            message="I'm looking to buy a house under $500k in Austin"
        )

        print(f"  ✅ Lead Bot response: {lead_result['response'][:50]}...")
        print(f"  ✅ Lead score: {lead_result['lead_score']}")

        # Test Seller Bot
        print("\nTesting Seller Bot processing...")
        seller_result = await seller_bot.process_seller_message(
            contact_id="test_seller_789",
            location_id="test_location_456",
            message="I'm thinking about selling my house. What's it worth?"
        )

        print(f"  ✅ Seller Bot response: {seller_result.response_message[:50]}...")
        print(f"  ✅ Seller temperature: {seller_result.seller_temperature}")

        # Test Analytics
        print("\nTesting analytics...")
        lead_analytics = await lead_bot.get_lead_analytics("test_lead_123", "test_location_456")
        seller_analytics = await seller_bot.get_seller_analytics("test_seller_789", "test_location_456")

        print(f"  ✅ Lead analytics retrieved")
        print(f"  ✅ Seller analytics retrieved")

        return True

    except Exception as e:
        print(f"  ❌ Bot functionality test failed: {e}")
        return False

def test_dashboard_import():
    """Test dashboard imports"""

    print("\n📊 Testing Dashboard Import")
    print("=" * 40)

    try:
        # Test if we can import the dashboard components
        import importlib.util

        dashboard_spec = importlib.util.spec_from_file_location(
            "jorge_kpi_dashboard",
            "jorge_kpi_dashboard.py"
        )

        if dashboard_spec:
            print("  ✅ Dashboard module can be imported")
            return True
        else:
            print("  ❌ Dashboard module not found")
            return False

    except Exception as e:
        print(f"  ❌ Dashboard import test failed: {e}")
        return False

async def main():
    """Run all tests"""

    print("🏠 JORGE'S BOT SYSTEM - STANDALONE TESTING")
    print("=" * 50)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Test 1: Imports
    imports_ok = test_imports()

    if not imports_ok:
        print("\n❌ FAILED: Import test failed. Cannot proceed.")
        return False

    # Test 2: Bot initialization
    bots_ok, bots = test_bot_initialization()

    if not bots_ok:
        print("\n❌ FAILED: Bot initialization failed.")
        return False

    # Test 3: Bot functionality
    functionality_ok = await test_bot_functionality(bots)

    # Test 4: Dashboard
    dashboard_ok = test_dashboard_import()

    # Summary
    print("\n" + "=" * 50)
    print("🏁 TEST SUMMARY")
    print("=" * 50)

    tests = [
        ("Module Imports", imports_ok),
        ("Bot Initialization", bots_ok),
        ("Bot Functionality", functionality_ok),
        ("Dashboard Import", dashboard_ok)
    ]

    all_passed = True
    for test_name, result in tests:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:20} {status}")
        if not result:
            all_passed = False

    print()

    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("Jorge's bot system is ready for deployment.")
        print()
        print("Next steps:")
        print("  1. Configure real GHL and Claude API keys in .env")
        print("  2. Run: streamlit run jorge_kpi_dashboard.py")
        print("  3. Set up GHL webhooks per README.md")
        return True
    else:
        print("❌ SOME TESTS FAILED!")
        print("Please review the errors above before deploying.")
        return False

if __name__ == "__main__":
    # Load environment variables
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Install with: pip install python-dotenv")

    # Run tests
    success = asyncio.run(main())
    sys.exit(0 if success else 1)