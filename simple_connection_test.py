#!/usr/bin/env python3
"""
Simple WebSocket Connection Test - Minimal Version
"""

import asyncio
import websockets

async def test_simple_connection():
    """Test basic WebSocket connection."""

    url = "ws://localhost:8001/ws/dashboard/default"

    print(f"🔗 Attempting simple connection to: {url}")

    try:
        websocket = await websockets.connect(url)
        print(f"✅ CONNECTED SUCCESSFULLY!")

        await websocket.send("ping")
        print(f"📤 Sent ping")

        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"📨 Received: {response}")
        except asyncio.TimeoutError:
            print(f"⏰ No response received")

        await websocket.close()
        print(f"🔌 Connection closed")

        return True

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_all_endpoints_simple():
    """Test all endpoints with simple connection."""

    endpoints = [
        "ws://localhost:8001/ws/dashboard/default",
        "ws://localhost:8001/ws/bi/revenue-intelligence/default",
        "ws://localhost:8001/ws/bot-performance/default",
        "ws://localhost:8001/ws/business-intelligence/default",
        "ws://localhost:8001/ws/ai-concierge/default",
        "ws://localhost:8001/ws/analytics/advanced/default"
    ]

    print(f"🧪 Simple Connection Test - All Endpoints")
    print(f"=" * 50)

    success_count = 0

    for i, url in enumerate(endpoints, 1):
        endpoint_name = url.split('/')[-2]
        print(f"\n{i}. Testing {endpoint_name}")

        try:
            websocket = await websockets.connect(url)
            print(f"   ✅ CONNECTED to {endpoint_name}")
            await websocket.close()
            success_count += 1
        except Exception as e:
            print(f"   ❌ FAILED: {e}")

    print(f"\n" + "=" * 50)
    print(f"📊 Results: {success_count}/{len(endpoints)} endpoints connected")
    print(f"=" * 50)

    return success_count == len(endpoints)

if __name__ == "__main__":
    asyncio.run(test_all_endpoints_simple())