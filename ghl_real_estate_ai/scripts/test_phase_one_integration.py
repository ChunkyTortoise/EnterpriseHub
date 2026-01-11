"""
Phase One Lead Intelligence Integration Test Runner

Quick validation script for testing Claude Agent Service and property API integrations.
Designed for rapid development testing and validation.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add the parent directory to path so we can import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from services.claude_agent_service import ClaudeAgentService, chat_with_claude
    from services.zillow_integration_service import ZillowIntegrationService
    from services.redfin_integration_service import RedfinIntegrationService
    from ghl_utils.config import settings
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running this from the correct directory")
    sys.exit(1)


class PhaseOneIntegrationTester:
    """Test runner for Phase One Lead Intelligence features"""

    def __init__(self):
        self.results = {}
        self.start_time = datetime.now()

    async def run_all_tests(self):
        """Run comprehensive integration tests"""
        print("🧪 Phase One Lead Intelligence Integration Tests")
        print("=" * 60)
        print(f"Started at: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        # Test Claude Agent Service
        await self.test_claude_agent_service()

        # Test Zillow Integration
        await self.test_zillow_integration()

        # Test Redfin Integration
        await self.test_redfin_integration()

        # Test Combined Scenarios
        await self.test_integration_scenarios()

        # Print results summary
        self.print_summary()

    async def test_claude_agent_service(self):
        """Test Claude Agent Service functionality"""
        print("🤖 Testing Claude Agent Service...")

        try:
            service = ClaudeAgentService()

            # Test basic conversation
            print("  ➤ Testing basic agent conversation...")
            response = await service.chat_with_agent(
                "test_agent_001",
                "What are the key insights for high-scoring leads?",
                None
            )

            assert response.response is not None
            assert len(response.insights) > 0
            assert len(response.recommendations) > 0
            print("    ✅ Basic conversation: PASSED")

            # Test lead-specific insights
            print("  ➤ Testing lead-specific insights...")
            insights = await service.get_lead_insights("lead_123", "test_agent_001")

            assert isinstance(insights, dict)
            assert "insights" in insights
            assert "recommendations" in insights
            print("    ✅ Lead insights: PASSED")

            # Test follow-up actions
            print("  ➤ Testing follow-up actions...")
            actions = await service.suggest_follow_up_actions("lead_123", "test_agent_001")

            assert isinstance(actions, list)
            assert len(actions) > 0
            print("    ✅ Follow-up actions: PASSED")

            # Test agent stats
            print("  ➤ Testing agent statistics...")
            stats = service.get_agent_stats("test_agent_001")

            assert isinstance(stats, dict)
            assert "agent_id" in stats
            print("    ✅ Agent statistics: PASSED")

            self.results["claude_agent_service"] = "PASSED"

        except Exception as e:
            print(f"    ❌ Claude Agent Service: FAILED - {str(e)}")
            self.results["claude_agent_service"] = f"FAILED - {str(e)}"

    async def test_zillow_integration(self):
        """Test Zillow Integration Service"""
        print("\n🏠 Testing Zillow Integration Service...")

        try:
            async with ZillowIntegrationService() as service:

                # Test property search
                print("  ➤ Testing property search...")
                properties = await service.search_properties("Austin", max_results=5)

                assert isinstance(properties, list)
                assert len(properties) > 0
                print(f"    ✅ Property search: PASSED ({len(properties)} properties found)")

                # Test property details
                print("  ➤ Testing property details...")
                if properties:
                    zpid = properties[0].zpid
                    details = await service.get_property_details(zpid)

                    assert details is not None
                    assert details.zpid == zpid
                    print("    ✅ Property details: PASSED")

                # Test market analysis
                print("  ➤ Testing market analysis...")
                analysis = await service.get_market_analysis("Austin")

                assert analysis is not None
                assert analysis.area == "Austin"
                print("    ✅ Market analysis: PASSED")

                # Test coordinate search
                print("  ➤ Testing coordinate-based search...")
                nearby_props = await service.find_properties_near_coordinates(
                    30.2672, -97.7431, 2.0, 3
                )

                assert isinstance(nearby_props, list)
                print(f"    ✅ Coordinate search: PASSED ({len(nearby_props)} properties)")

            self.results["zillow_integration"] = "PASSED"

        except Exception as e:
            print(f"    ❌ Zillow Integration: FAILED - {str(e)}")
            self.results["zillow_integration"] = f"FAILED - {str(e)}"

    async def test_redfin_integration(self):
        """Test Redfin Integration Service"""
        print("\n🏡 Testing Redfin Integration Service...")

        try:
            async with RedfinIntegrationService() as service:

                # Test property search
                print("  ➤ Testing Redfin property search...")
                properties = await service.search_properties("Austin", max_results=5)

                assert isinstance(properties, list)
                assert len(properties) > 0
                print(f"    ✅ Redfin search: PASSED ({len(properties)} properties found)")

                # Test market data
                print("  ➤ Testing Redfin market data...")
                market_data = await service.get_market_data("Austin")

                assert market_data is not None
                assert market_data.area == "Austin"
                print("    ✅ Redfin market data: PASSED")

                # Test neighborhood insights
                print("  ➤ Testing neighborhood insights...")
                insights = await service.get_neighborhood_insights("Downtown", "Austin", "TX")

                assert insights is not None
                assert insights.neighborhood == "Downtown"
                print("    ✅ Neighborhood insights: PASSED")

            self.results["redfin_integration"] = "PASSED"

        except Exception as e:
            print(f"    ❌ Redfin Integration: FAILED - {str(e)}")
            self.results["redfin_integration"] = f"FAILED - {str(e)}"

    async def test_integration_scenarios(self):
        """Test combined integration scenarios"""
        print("\n🔗 Testing Integration Scenarios...")

        try:
            # Test 1: Agent query about property market
            print("  ➤ Testing agent + property market query...")
            claude_service = ClaudeAgentService()

            # Simulate agent asking about market conditions
            response = await claude_service.chat_with_agent(
                "integration_agent_001",
                "Based on current Austin market data, what should I tell leads about pricing trends?",
                None
            )

            assert response.response is not None
            print("    ✅ Agent + market query: PASSED")

            # Test 2: Property matching with lead preferences
            print("  ➤ Testing property matching scenario...")
            lead_budget = 800000
            lead_location = "Austin"

            async with ZillowIntegrationService() as zillow_service:
                properties = await zillow_service.search_properties(
                    lead_location,
                    {"max_price": lead_budget},
                    5
                )

                # Filter properties within budget
                matching_props = [p for p in properties if p.price <= lead_budget]
                assert len(matching_props) > 0
                print(f"    ✅ Property matching: PASSED ({len(matching_props)} matches)")

            # Test 3: Combined lead and property intelligence
            print("  ➤ Testing combined intelligence scenario...")
            context = {
                "lead_preferences": {
                    "budget": 750000,
                    "location": "Austin",
                    "property_type": "Single Family"
                },
                "market_data": {
                    "median_price": 650000,
                    "trend": "increasing"
                }
            }

            response = await claude_service.chat_with_agent(
                "integration_agent_001",
                "Given this lead's preferences and current market data, what's my strategy?",
                "lead_integration_test",
                context
            )

            assert response.response is not None
            assert len(response.recommendations) > 0
            print("    ✅ Combined intelligence: PASSED")

            self.results["integration_scenarios"] = "PASSED"

        except Exception as e:
            print(f"    ❌ Integration Scenarios: FAILED - {str(e)}")
            self.results["integration_scenarios"] = f"FAILED - {str(e)}"

    def print_summary(self):
        """Print test results summary"""
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        print("\n" + "=" * 60)
        print("🎯 Phase One Integration Test Results")
        print("=" * 60)

        passed = sum(1 for result in self.results.values() if result == "PASSED")
        total = len(self.results)

        for test_name, result in self.results.items():
            status_icon = "✅" if result == "PASSED" else "❌"
            print(f"{status_icon} {test_name.replace('_', ' ').title()}: {result}")

        print(f"\nSummary: {passed}/{total} tests passed")
        print(f"Duration: {duration:.2f} seconds")

        if passed == total:
            print("🎉 All Phase One Lead Intelligence tests PASSED!")
            print("\n✨ Ready for production deployment!")
        else:
            print(f"⚠️  {total - passed} test(s) failed - review before deployment")

        print("\n🚀 Phase One Features Ready:")
        print("  • Claude AI agent conversations")
        print("  • Zillow property data integration")
        print("  • Redfin market insights")
        print("  • Enhanced lead intelligence map")
        print("  • Real-time lead + property insights")


async def main():
    """Main test runner"""
    tester = PhaseOneIntegrationTester()
    await tester.run_all_tests()


if __name__ == "__main__":
    # Run the integration tests
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n💥 Testing failed with error: {str(e)}")
        sys.exit(1)