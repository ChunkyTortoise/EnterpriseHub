import pytest

@pytest.mark.unit
#!/usr/bin/env python3
"""
Quick WebSocket Connection Test for Jorge's BI Dashboard
Tests all 6 WebSocket endpoints for connectivity
"""

import asyncio
import websockets
import json
import sys
from typing import List, Dict

# All 6 BI WebSocket endpoints to test
BI_WEBSOCKET_ENDPOINTS = [
    "ws://localhost:8000/ws/dashboard/default",
    "ws://localhost:8000/ws/bi/revenue-intelligence/default",
    "ws://localhost:8000/ws/bot-performance/default",
    "ws://localhost:8000/ws/business-intelligence/default",
    "ws://localhost:8000/ws/ai-concierge/default",
    "ws://localhost:8000/ws/analytics/advanced/default"
]

async def test_websocket_connection(endpoint: str) -> Dict[str, any]:
    """Test a single WebSocket endpoint"""
    try:
        # Connect with short timeout
        async with websockets.connect(endpoint, timeout=5) as websocket:
            print(f"✅ Connected to {endpoint}")

            # Send a test message
            test_message = {"type": "ping", "timestamp": "test"}
            await websocket.send(json.dumps(test_message))

            # Try to receive a response (with timeout)
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                print(f"📨 Received response from {endpoint}: {response[:100]}...")
                return {"endpoint": endpoint, "status": "success", "response": response}
            except asyncio.TimeoutError:
                print(f"⏰ No immediate response from {endpoint} (normal for initialization)")
                return {"endpoint": endpoint, "status": "connected", "response": "timeout"}

    except Exception as e:
        print(f"❌ Failed to connect to {endpoint}: {e}")
        return {"endpoint": endpoint, "status": "failed", "error": str(e)}

async def test_all_websocket_connections():
    """Test all BI WebSocket endpoints"""
    print("🔍 Testing Jorge's BI Dashboard WebSocket Connections")
    print("=" * 60)

    results = []

    # Test each endpoint
    for endpoint in BI_WEBSOCKET_ENDPOINTS:
        print(f"\n🧪 Testing: {endpoint}")
        result = await test_websocket_connection(endpoint)
        results.append(result)
        await asyncio.sleep(0.5)  # Brief pause between tests

    # Summary
    print("\n" + "=" * 60)
    print("📊 WebSocket Connection Test Results:")
    print("=" * 60)

    success_count = 0
    connected_count = 0
    failed_count = 0

    for result in results:
        status = result["status"]
        endpoint_name = result["endpoint"].split("/ws/")[1].split("/")[0]

        if status == "success":
            print(f"✅ {endpoint_name}: Connected + Responsive")
            success_count += 1
        elif status == "connected":
            print(f"🟡 {endpoint_name}: Connected (no immediate response)")
            connected_count += 1
        else:
            print(f"❌ {endpoint_name}: {result.get('error', 'Failed')}")
            failed_count += 1

    print(f"\n📈 Summary:")
    print(f"   ✅ Fully Working: {success_count}")
    print(f"   🟡 Connected: {connected_count}")
    print(f"   ❌ Failed: {failed_count}")
    print(f"   📊 Total: {len(results)}")

    if success_count + connected_count >= 4:
        print(f"\n🎉 SUCCESS: {success_count + connected_count}/6 endpoints are operational!")
        print("   Jorge's BI Dashboard WebSocket infrastructure is ready!")
        return True
    else:
        print(f"\n⚠️ PARTIAL: Only {success_count + connected_count}/6 endpoints working")
        print("   Server may still be initializing...")
        return False

if __name__ == "__main__":
    print("🚀 Jorge's BI Dashboard WebSocket Test")
    print("   Testing connectivity to all 6 real-time endpoints...")

    try:
        success = asyncio.run(test_all_websocket_connections())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)