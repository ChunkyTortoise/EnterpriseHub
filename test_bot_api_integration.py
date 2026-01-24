#!/usr/bin/env python3
"""
Test Script for Bot Management API Integration
Run this after starting the FastAPI server to verify all endpoints work correctly.
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

BASE_URL = "http://localhost:8000"  # Adjust if server runs on different port

async def test_endpoint(session: aiohttp.ClientSession, method: str, url: str, data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Test a single endpoint and return response"""
    try:
        if method.upper() == "GET":
            async with session.get(url) as response:
                result = {
                    "status": response.status,
                    "url": url,
                    "success": response.status < 400,
                    "content_type": response.content_type,
                }

                if "application/json" in response.content_type:
                    result["data"] = await response.json()
                else:
                    result["text"] = await response.text()

                return result

        elif method.upper() == "POST":
            headers = {"Content-Type": "application/json"}
            async with session.post(url, json=data, headers=headers) as response:
                result = {
                    "status": response.status,
                    "url": url,
                    "success": response.status < 400,
                    "content_type": response.content_type,
                }

                if "application/json" in response.content_type:
                    result["data"] = await response.json()
                else:
                    result["text"] = await response.text()

                return result

    except Exception as e:
        return {
            "status": "ERROR",
            "url": url,
            "success": False,
            "error": str(e)
        }

async def test_streaming_endpoint(session: aiohttp.ClientSession, url: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Test streaming SSE endpoint"""
    try:
        headers = {"Content-Type": "application/json"}
        async with session.post(url, json=data, headers=headers) as response:

            if response.status >= 400:
                return {
                    "status": response.status,
                    "url": url,
                    "success": False,
                    "error": await response.text()
                }

            # Read first few SSE chunks
            chunks = []
            chunk_count = 0

            async for line in response.content:
                if chunk_count >= 5:  # Limit for testing
                    break

                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('data: '):
                    try:
                        chunk_data = json.loads(decoded_line[6:])  # Remove 'data: '
                        chunks.append(chunk_data)
                        chunk_count += 1
                    except json.JSONDecodeError:
                        continue

            return {
                "status": response.status,
                "url": url,
                "success": True,
                "content_type": response.content_type,
                "chunks": chunks,
                "chunk_count": len(chunks)
            }

    except Exception as e:
        return {
            "status": "ERROR",
            "url": url,
            "success": False,
            "error": str(e)
        }

async def run_bot_api_tests():
    """Run comprehensive tests for Bot Management API"""
    print("🤖 Testing Jorge's Bot Management API Integration")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        tests = []

        # Test 1: Health Check
        print("\n1️⃣  Testing Health Check...")
        result = await test_endpoint(session, "GET", f"{BASE_URL}/api/bots/health")
        tests.append(("Health Check", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")

        # Test 2: List Bots
        print("\n2️⃣  Testing List Bots...")
        result = await test_endpoint(session, "GET", f"{BASE_URL}/api/bots")
        tests.append(("List Bots", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")
        if result['success'] and 'data' in result:
            print(f"   Found {len(result['data'])} bots")

        # Test 3: Bot Status
        print("\n3️⃣  Testing Bot Status...")
        result = await test_endpoint(session, "GET", f"{BASE_URL}/api/bots/jorge-seller-bot/status")
        tests.append(("Jorge Bot Status", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")

        # Test 4: Jorge Start
        print("\n4️⃣  Testing Jorge Qualification Start...")
        start_data = {
            "leadId": "test_lead_123",
            "leadName": "Test Lead",
            "phone": "555-1234"
        }
        result = await test_endpoint(session, "POST", f"{BASE_URL}/api/jorge-seller/start", start_data)
        tests.append(("Jorge Start", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")

        # Test 5: Intent Scoring
        print("\n5️⃣  Testing Intent Decoder...")
        result = await test_endpoint(session, "GET", f"{BASE_URL}/api/intent-decoder/test_lead_123/score")
        tests.append(("Intent Decoder", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")

        # Test 6: Lead Bot Schedule
        print("\n6️⃣  Testing Lead Bot Scheduling...")
        schedule_data = {"sequenceDay": 3}
        result = await test_endpoint(session, "POST", f"{BASE_URL}/api/lead-bot/test_lead_123/schedule", schedule_data)
        tests.append(("Lead Bot Schedule", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")

        # Test 7: Streaming Chat (LIMITED)
        print("\n7️⃣  Testing Streaming Chat (Jorge)...")
        chat_data = {
            "content": "I want to sell my house quickly",
            "leadId": "test_lead_123",
            "leadName": "Test Lead"
        }
        result = await test_streaming_endpoint(session, f"{BASE_URL}/api/bots/jorge-seller-bot/chat", chat_data)
        tests.append(("Streaming Chat", result))
        print(f"   Status: {result['status']} {'✅' if result['success'] else '❌'}")
        if result['success']:
            print(f"   Received {result['chunk_count']} SSE chunks")

        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = 0
        failed = 0

        for test_name, test_result in tests:
            status_icon = "✅" if test_result['success'] else "❌"
            print(f"{status_icon} {test_name:<25} Status: {test_result['status']}")

            if test_result['success']:
                passed += 1
            else:
                failed += 1
                if 'error' in test_result:
                    print(f"   Error: {test_result['error']}")

        print(f"\n✅ Passed: {passed}/{len(tests)}")
        print(f"❌ Failed: {failed}/{len(tests)}")

        if failed == 0:
            print("\n🎉 ALL TESTS PASSED! Bot Management API is ready for frontend integration.")
        else:
            print(f"\n⚠️  {failed} tests failed. Check server logs and fix issues before proceeding.")

        return failed == 0

if __name__ == "__main__":
    print("""
🚀 Bot Management API Test Suite
================================

This script tests all 7 bot management endpoints to ensure they're working correctly.

Prerequisites:
1. Start the FastAPI server: `uvicorn ghl_real_estate_ai.api.main:app --reload --port 8000`
2. Ensure Redis is running (for caching/session management)
3. Ensure all dependencies are installed

Running tests...
""")

    try:
        success = asyncio.run(run_bot_api_tests())
        exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️  Tests interrupted by user")
        exit(1)
    except Exception as e:
        print(f"\n❌ Test suite failed with error: {e}")
        exit(1)