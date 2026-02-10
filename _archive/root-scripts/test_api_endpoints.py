import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Jorge's AI Empire - API Endpoint Validation Script
Tests all critical endpoints to ensure routing is working correctly.
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, List
from datetime import datetime

class APITester:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.results: List[Dict] = []

    async def test_endpoint(self, session: aiohttp.ClientSession, method: str, endpoint: str,
                           expected_status: int = 200, payload: dict = None) -> Dict:
        """Test a single API endpoint"""
        url = f"{self.base_url}{endpoint}"

        try:
            if method.upper() == "GET":
                async with session.get(url) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = await response.text()
            elif method.upper() == "POST":
                async with session.post(url, json=payload) as response:
                    status = response.status
                    try:
                        data = await response.json()
                    except:
                        data = await response.text()
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = status == expected_status

            result = {
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": status,
                "success": success,
                "response_preview": str(data)[:200] if data else "No response",
                "timestamp": datetime.now().isoformat()
            }

            print(f"{'✅' if success else '❌'} {method} {endpoint} → {status}")

        except Exception as e:
            result = {
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            print(f"❌ {method} {endpoint} → ERROR: {e}")

        self.results.append(result)
        return result

    async def run_tests(self):
        """Run comprehensive API endpoint tests"""

        print("🚀 JORGE'S AI EMPIRE - API ENDPOINT VALIDATION")
        print("=" * 60)
        print(f"Testing API at: {self.base_url}")
        print(f"Started at: {datetime.now().isoformat()}")
        print()

        async with aiohttp.ClientSession() as session:

            # ================================================================
            # Core System Health Tests
            # ================================================================
            print("🔍 CORE SYSTEM HEALTH")
            print("-" * 30)

            await self.test_endpoint(session, "GET", "/")
            await self.test_endpoint(session, "GET", "/api/health")

            # ================================================================
            # Bot Management Tests (Fixed routing)
            # ================================================================
            print("\n🤖 BOT MANAGEMENT API")
            print("-" * 30)

            await self.test_endpoint(session, "GET", "/api/bots/health")
            await self.test_endpoint(session, "GET", "/api/bots")

            # ================================================================
            # Jorge Seller Bot Tests (NEW ENDPOINTS)
            # ================================================================
            print("\n💼 JORGE SELLER BOT API")
            print("-" * 30)

            # Test the existing endpoint
            test_payload = {
                "contact_id": "test_lead_001",
                "location_id": "3xt4qayAh35BlDLaUv7P",
                "message": "I'm thinking about selling my house"
            }
            await self.test_endpoint(session, "POST", "/api/jorge-seller/process",
                                   expected_status=200, payload=test_payload)

            # Test the NEW endpoints we just added
            await self.test_endpoint(session, "GET", "/api/jorge-seller/test_lead_001/progress")
            await self.test_endpoint(session, "GET", "/api/jorge-seller/conversations/conv_123")

            stall_payload = {"stall_type": "price", "apply_immediately": True}
            await self.test_endpoint(session, "POST", "/api/jorge-seller/test_lead_001/stall-breaker",
                                   expected_status=200, payload=stall_payload)

            handoff_payload = {"target_bot": "lead-bot", "reason": "qualification_complete"}
            await self.test_endpoint(session, "POST", "/api/jorge-seller/test_lead_001/handoff",
                                   expected_status=200, payload=handoff_payload)

            # ================================================================
            # Lead Bot Management Tests
            # ================================================================
            print("\n📞 LEAD BOT MANAGEMENT API")
            print("-" * 30)

            await self.test_endpoint(session, "GET", "/api/lead-bot/health")
            await self.test_endpoint(session, "GET", "/api/lead-bot/scheduler/status",
                                   expected_status=401)  # Requires auth

            # ================================================================
            # Performance Monitoring Tests
            # ================================================================
            print("\n📊 PERFORMANCE MONITORING API")
            print("-" * 30)

            await self.test_endpoint(session, "GET", "/api/performance/summary")
            await self.test_endpoint(session, "GET", "/api/performance/jorge")
            await self.test_endpoint(session, "GET", "/api/performance/health")

            # ================================================================
            # WebSocket Performance Tests
            # ================================================================
            print("\n⚡ WEBSOCKET PERFORMANCE API")
            print("-" * 30)

            await self.test_endpoint(session, "GET", "/api/v1/websocket-performance/summary")
            await self.test_endpoint(session, "GET", "/api/v1/websocket-performance/metrics")

        # ================================================================
        # Results Summary
        # ================================================================
        self.print_summary()

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 60)
        print("📋 TEST RESULTS SUMMARY")
        print("=" * 60)

        total_tests = len(self.results)
        successful_tests = len([r for r in self.results if r["success"]])
        failed_tests = total_tests - successful_tests

        success_rate = (successful_tests / total_tests * 100) if total_tests > 0 else 0

        print(f"Total Tests: {total_tests}")
        print(f"Successful: {successful_tests} ✅")
        print(f"Failed: {failed_tests} ❌")
        print(f"Success Rate: {success_rate:.1f}%")
        print()

        if failed_tests > 0:
            print("FAILED ENDPOINTS:")
            print("-" * 20)
            for result in self.results:
                if not result["success"]:
                    status = result.get("actual_status", "ERROR")
                    error = result.get("error", "Unknown error")
                    print(f"❌ {result['method']} {result['endpoint']} → {status}")
                    if "error" in result:
                        print(f"   Error: {error}")
            print()

        if success_rate >= 80:
            print("🎉 API HEALTH: EXCELLENT")
            print("✅ Platform is ready for frontend integration!")
        elif success_rate >= 60:
            print("⚠️ API HEALTH: GOOD")
            print("🔧 Minor issues need attention before full deployment")
        else:
            print("🚨 API HEALTH: NEEDS ATTENTION")
            print("🛠️ Major routing issues need to be resolved")

        print("\nNext Steps:")
        if failed_tests == 0:
            print("1. ✅ All endpoints working - proceed with frontend integration")
            print("2. ✅ Start performance dashboard testing")
            print("3. ✅ Begin production optimization phase")
        else:
            print("1. 🔧 Fix failed endpoints listed above")
            print("2. 🔄 Re-run this test script")
            print("3. ✅ Proceed when success rate > 80%")

async def main():
    """Main test execution"""
    import argparse

    parser = argparse.ArgumentParser(description="Test Jorge's AI Empire API endpoints")
    parser.add_argument("--url", default="http://localhost:8000",
                       help="Base URL for API testing (default: http://localhost:8000)")

    args = parser.parse_args()

    tester = APITester(base_url=args.url)
    await tester.run_tests()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test execution failed: {e}")
        sys.exit(1)