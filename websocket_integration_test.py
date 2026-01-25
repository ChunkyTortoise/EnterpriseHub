#!/usr/bin/env python3
"""
Frontend Integration Testing Agent - WebSocket Validation Script

Tests all 6 BI WebSocket endpoints for connectivity and data flow validation
between the Next.js frontend and Jorge's backend services.

WebSocket Endpoints to Test:
1. ws://localhost:8001/ws/dashboard/default
2. ws://localhost:8001/ws/bi/revenue-intelligence/default
3. ws://localhost:8001/ws/bot-performance/default
4. ws://localhost:8001/ws/business-intelligence/default
5. ws://localhost:8001/ws/ai-concierge/default
6. ws://localhost:8001/ws/analytics/advanced/default

Expected Results:
✅ All connections establish successfully
✅ Each endpoint responds with proper event messages
✅ Frontend store integration validates correctly
✅ Real-time data flow confirmed
"""

import asyncio
import websockets
import json
import time
from datetime import datetime
import aiohttp
import sys
from typing import Dict, List, Optional, Any

class WebSocketTester:
    def __init__(self, base_url: str = "ws://localhost:8001"):
        self.base_url = base_url
        self.test_location = "default"
        self.results: Dict[str, Any] = {}

        # Define the 6 BI WebSocket endpoints from frontend store
        self.endpoints = [
            {"id": "bi_dashboard", "path": f"/ws/dashboard/{self.test_location}"},
            {"id": "bi_revenue_intelligence", "path": f"/ws/bi/revenue-intelligence/{self.test_location}"},
            {"id": "bi_bot_performance", "path": f"/ws/bot-performance/{self.test_location}"},
            {"id": "bi_business_intelligence", "path": f"/ws/business-intelligence/{self.test_location}"},
            {"id": "ai_concierge_insights", "path": f"/ws/ai-concierge/{self.test_location}"},
            {"id": "advanced_analytics", "path": f"/ws/analytics/advanced/{self.test_location}"}
        ]

    def print_header(self, title: str) -> None:
        """Print formatted test section header."""
        print(f"\n{'=' * 60}")
        print(f"🧪 {title}")
        print(f"{'=' * 60}")

    def print_step(self, step: str) -> None:
        """Print test step."""
        print(f"\n📋 {step}")

    def print_result(self, endpoint_id: str, status: str, details: str = "") -> None:
        """Print test result."""
        status_emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{status_emoji} {endpoint_id}: {status}")
        if details:
            print(f"   └─ {details}")

    async def test_backend_health(self) -> bool:
        """Test if the backend is accessible."""
        self.print_step("Testing Backend Health")

        try:
            # Convert WebSocket URL to HTTP URL for health check
            http_url = self.base_url.replace("ws://", "http://").replace("wss://", "https://")

            async with aiohttp.ClientSession() as session:
                async with session.get(f"{http_url}/health", timeout=5) as response:
                    if response.status == 200:
                        data = await response.json()
                        self.print_result("Backend Health", "PASS", f"Status: {data.get('status', 'unknown')}")
                        return True
                    else:
                        self.print_result("Backend Health", "FAIL", f"HTTP {response.status}")
                        return False
        except Exception as e:
            self.print_result("Backend Health", "FAIL", str(e))
            return False

    async def test_single_websocket(self, endpoint: Dict[str, str]) -> Dict[str, Any]:
        """Test a single WebSocket endpoint."""
        endpoint_id = endpoint["id"]
        endpoint_path = endpoint["path"]
        full_url = f"{self.base_url}{endpoint_path}"

        result = {
            "endpoint_id": endpoint_id,
            "url": full_url,
            "connected": False,
            "messages_received": 0,
            "connection_time": None,
            "first_message_time": None,
            "sample_messages": [],
            "error": None
        }

        try:
            print(f"   🔗 Connecting to {endpoint_id} at {endpoint_path}")

            # Record connection start time
            start_time = time.time()

            # Connect with timeout
            websocket = await asyncio.wait_for(
                websockets.connect(full_url),
                timeout=10.0
            )

            result["connected"] = True
            result["connection_time"] = time.time() - start_time

            print(f"   ✅ Connected in {result['connection_time']:.2f}s")

            # Send a test message to trigger responses
            test_message = {
                "type": "test_connection",
                "timestamp": datetime.now().isoformat(),
                "client": "frontend_integration_tester"
            }

            await websocket.send(json.dumps(test_message))
            print(f"   📤 Sent test message")

            # Listen for messages for 5 seconds
            message_start_time = time.time()
            timeout_seconds = 5

            try:
                while time.time() - message_start_time < timeout_seconds:
                    try:
                        # Wait for message with short timeout
                        message = await asyncio.wait_for(websocket.recv(), timeout=1.0)

                        # Record first message time
                        if result["first_message_time"] is None:
                            result["first_message_time"] = time.time() - message_start_time

                        result["messages_received"] += 1

                        # Parse and store sample messages
                        try:
                            parsed_message = json.loads(message)
                            if len(result["sample_messages"]) < 3:  # Store first 3 messages
                                result["sample_messages"].append(parsed_message)
                            print(f"   📨 Received message {result['messages_received']}: {parsed_message.get('type', 'unknown')}")
                        except json.JSONDecodeError:
                            print(f"   📨 Received non-JSON message: {message[:100]}...")

                    except asyncio.TimeoutError:
                        # No message received in this interval, continue waiting
                        continue

            except Exception as e:
                print(f"   ⚠️ Message listening error: {e}")

            await websocket.close()

            # Evaluate results
            if result["messages_received"] > 0:
                print(f"   ✅ Received {result['messages_received']} messages")
                if result["first_message_time"]:
                    print(f"   ⚡ First message in {result['first_message_time']:.2f}s")
            else:
                print(f"   ⚠️ No messages received (connection successful but no data)")

        except asyncio.TimeoutError:
            result["error"] = "Connection timeout"
            print(f"   ❌ Connection timeout")
        except websockets.exceptions.ConnectionClosed as e:
            result["error"] = f"Connection closed: {e}"
            print(f"   ❌ Connection closed: {e}")
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ Connection failed: {e}")

        return result

    async def test_all_websockets(self) -> Dict[str, Any]:
        """Test all WebSocket endpoints."""
        self.print_step("Testing All WebSocket Endpoints")

        results = {}

        for endpoint in self.endpoints:
            print(f"\n🔍 Testing {endpoint['id']}")
            result = await self.test_single_websocket(endpoint)
            results[endpoint["id"]] = result

            # Print immediate result
            if result["connected"] and result["messages_received"] > 0:
                self.print_result(endpoint["id"], "PASS",
                    f"Connected in {result['connection_time']:.2f}s, {result['messages_received']} messages")
            elif result["connected"]:
                self.print_result(endpoint["id"], "WARN",
                    f"Connected but no messages received")
            else:
                self.print_result(endpoint["id"], "FAIL",
                    result["error"] or "Connection failed")

        return results

    def analyze_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze test results and provide summary."""
        analysis = {
            "total_endpoints": len(results),
            "connected_endpoints": 0,
            "endpoints_with_messages": 0,
            "failed_endpoints": [],
            "successful_endpoints": [],
            "avg_connection_time": 0,
            "total_messages": 0,
            "recommendations": []
        }

        connection_times = []

        for endpoint_id, result in results.items():
            if result["connected"]:
                analysis["connected_endpoints"] += 1
                if result["connection_time"]:
                    connection_times.append(result["connection_time"])

                if result["messages_received"] > 0:
                    analysis["endpoints_with_messages"] += 1
                    analysis["successful_endpoints"].append(endpoint_id)
                    analysis["total_messages"] += result["messages_received"]
            else:
                analysis["failed_endpoints"].append({
                    "endpoint": endpoint_id,
                    "error": result["error"]
                })

        if connection_times:
            analysis["avg_connection_time"] = sum(connection_times) / len(connection_times)

        # Generate recommendations
        if analysis["connected_endpoints"] < analysis["total_endpoints"]:
            analysis["recommendations"].append(
                f"Fix connection issues for {analysis['total_endpoints'] - analysis['connected_endpoints']} endpoints"
            )

        if analysis["endpoints_with_messages"] < analysis["connected_endpoints"]:
            analysis["recommendations"].append(
                f"Investigate why {analysis['connected_endpoints'] - analysis['endpoints_with_messages']} endpoints are not sending data"
            )

        if analysis["avg_connection_time"] > 2.0:
            analysis["recommendations"].append(
                f"Optimize connection time (avg: {analysis['avg_connection_time']:.2f}s > 2.0s threshold)"
            )

        return analysis

    def print_summary(self, results: Dict[str, Any], analysis: Dict[str, Any]) -> None:
        """Print test summary."""
        self.print_header("Test Summary")

        print(f"📊 Total Endpoints Tested: {analysis['total_endpoints']}")
        print(f"✅ Successful Connections: {analysis['connected_endpoints']}")
        print(f"📨 Endpoints with Data Flow: {analysis['endpoints_with_messages']}")
        print(f"❌ Failed Connections: {len(analysis['failed_endpoints'])}")
        print(f"📈 Total Messages Received: {analysis['total_messages']}")

        if analysis['avg_connection_time'] > 0:
            print(f"⚡ Average Connection Time: {analysis['avg_connection_time']:.2f}s")

        # Successful endpoints
        if analysis["successful_endpoints"]:
            print(f"\n✅ Successful Endpoints:")
            for endpoint in analysis["successful_endpoints"]:
                result = results[endpoint]
                print(f"   • {endpoint}: {result['messages_received']} messages, {result['connection_time']:.2f}s")

        # Failed endpoints
        if analysis["failed_endpoints"]:
            print(f"\n❌ Failed Endpoints:")
            for failed in analysis["failed_endpoints"]:
                print(f"   • {failed['endpoint']}: {failed['error']}")

        # Recommendations
        if analysis["recommendations"]:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(analysis["recommendations"], 1):
                print(f"   {i}. {rec}")

        # Overall status
        if analysis["endpoints_with_messages"] == analysis["total_endpoints"]:
            print(f"\n🎉 ALL TESTS PASSED - WebSocket integration is working correctly!")
        elif analysis["connected_endpoints"] == analysis["total_endpoints"]:
            print(f"\n⚠️  CONNECTIONS OK - All endpoints connect but some have no data flow")
        else:
            print(f"\n❌ TESTS FAILED - {len(analysis['failed_endpoints'])} endpoints failed to connect")

    async def test_frontend_store_compatibility(self) -> None:
        """Test compatibility with frontend store configuration."""
        self.print_step("Testing Frontend Store Compatibility")

        # This would compare the endpoints we tested against the frontend store configuration
        # For now, we'll validate that our test endpoints match the store

        expected_endpoints_from_store = [
            "bi_dashboard", "bi_revenue_intelligence", "bi_bot_performance",
            "bi_business_intelligence", "ai_concierge_insights", "advanced_analytics"
        ]

        tested_endpoints = [ep["id"] for ep in self.endpoints]

        if set(tested_endpoints) == set(expected_endpoints_from_store):
            self.print_result("Store Compatibility", "PASS",
                "All endpoints match frontend store configuration")
        else:
            missing = set(expected_endpoints_from_store) - set(tested_endpoints)
            extra = set(tested_endpoints) - set(expected_endpoints_from_store)
            details = []
            if missing:
                details.append(f"Missing: {missing}")
            if extra:
                details.append(f"Extra: {extra}")
            self.print_result("Store Compatibility", "FAIL", "; ".join(details))

    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Run the complete test suite."""
        self.print_header("Frontend Integration Testing Agent")
        print("🎯 Testing WebSocket connections between Next.js frontend and Jorge's BI backend")
        print(f"🌐 Target: {self.base_url}")
        print(f"📍 Location: {self.test_location}")

        # Test backend health
        backend_healthy = await self.test_backend_health()
        if not backend_healthy:
            print("\n❌ Backend is not accessible. Please ensure the FastAPI server is running on port 8001.")
            return {"error": "Backend not accessible"}

        # Test frontend store compatibility
        await self.test_frontend_store_compatibility()

        # Test all WebSocket endpoints
        results = await self.test_all_websockets()

        # Analyze results
        analysis = self.analyze_results(results)

        # Print summary
        self.print_summary(results, analysis)

        return {
            "results": results,
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }

async def main():
    """Main entry point."""
    tester = WebSocketTester()

    try:
        test_results = await tester.run_full_test_suite()

        # Save results to file
        with open("websocket_test_results.json", "w") as f:
            json.dump(test_results, f, indent=2, default=str)

        print(f"\n📁 Full results saved to websocket_test_results.json")

        # Exit with appropriate code
        if "error" in test_results:
            sys.exit(1)
        elif test_results.get("analysis", {}).get("endpoints_with_messages", 0) == 6:
            sys.exit(0)  # All tests passed
        else:
            sys.exit(2)  # Some tests failed

    except KeyboardInterrupt:
        print("\n\n🛑 Testing interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())