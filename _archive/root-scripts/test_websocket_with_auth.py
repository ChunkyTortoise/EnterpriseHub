#!/usr/bin/env python3
"""
WebSocket Authentication Test

Try connecting to WebSocket endpoints with various authentication methods.
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_with_headers(url, headers=None):
    """Test WebSocket connection with custom headers."""
    print(f"🔗 Testing {url}")
    if headers:
        print(f"📋 Headers: {headers}")

    try:
        websocket = await websockets.connect(
            url,
            extra_headers=headers or {}
        )

        print(f"✅ Connected successfully!")

        # Send test message
        test_message = {"type": "test", "timestamp": datetime.now().isoformat()}
        await websocket.send(json.dumps(test_message))
        print(f"📤 Sent test message")

        # Try to receive
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"📨 Received: {response[:100]}...")
        except asyncio.TimeoutError:
            print(f"⏰ No response (timeout)")

        await websocket.close()
        return True

    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e.code} - {e.reason}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_different_auth_methods():
    """Test WebSocket with different authentication approaches."""

    test_url = "ws://localhost:8001/ws/dashboard/default"

    # Test scenarios
    scenarios = [
        ("No headers", {}),
        ("With fake JWT", {"Authorization": "Bearer fake-jwt-token"}),
        ("With API Key", {"X-API-Key": "test-api-key"}),
        ("With Location ID", {"X-Location-ID": "default"}),
        ("With Origin", {"Origin": "http://localhost:3000"}),
        ("With User Agent", {"User-Agent": "Jorge-Frontend/1.0"}),
        ("Combined headers", {
            "Authorization": "Bearer test-token",
            "X-Location-ID": "default",
            "Origin": "http://localhost:3000",
            "User-Agent": "Jorge-Frontend/1.0"
        })
    ]

    print(f"🧪 Testing WebSocket Authentication Methods")
    print(f"🎯 Target: {test_url}")
    print(f"=" * 60)

    for scenario_name, headers in scenarios:
        print(f"\n📋 Scenario: {scenario_name}")
        success = await test_with_headers(test_url, headers)

        if success:
            print(f"🎉 SUCCESS: Found working authentication method!")
            break
        else:
            print(f"❌ Failed")

    print(f"\n" + "=" * 60)
    print(f"🏁 Authentication testing complete")

async def test_with_query_params():
    """Test WebSocket with query parameters instead of headers."""

    base_url = "ws://localhost:8001/ws/dashboard/default"

    query_scenarios = [
        ("With token query", f"{base_url}?token=test-token"),
        ("With multiple params", f"{base_url}?token=test&components=executive_kpis,revenue_metrics"),
    ]

    print(f"\n🧪 Testing Query Parameter Authentication")
    print(f"=" * 60)

    for scenario_name, url in query_scenarios:
        print(f"\n📋 Scenario: {scenario_name}")
        success = await test_with_headers(url)

        if success:
            print(f"🎉 SUCCESS: Query parameters work!")
            break

if __name__ == "__main__":
    print("🧪 WebSocket Authentication Testing")
    print("=" * 40)

    asyncio.run(test_different_auth_methods())
    asyncio.run(test_with_query_params())