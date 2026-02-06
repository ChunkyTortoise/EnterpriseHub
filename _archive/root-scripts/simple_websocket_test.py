#!/usr/bin/env python3
"""
Simple WebSocket Connection Test

Test a single WebSocket endpoint to debug the 403 issue.
"""

import asyncio
import websockets
import json
from datetime import datetime

async def test_simple_connection():
    """Test a single WebSocket connection with debug info."""

    url = "ws://localhost:8001/ws/dashboard/default"

    print(f"🔗 Attempting to connect to: {url}")

    try:
        # Try connecting with additional debugging
        websocket = await websockets.connect(
            url,
            extra_headers={}  # Try with no extra headers first
        )

        print(f"✅ Connected successfully!")
        print(f"📋 WebSocket state: {websocket.state}")

        # Send a simple test message
        test_message = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }

        await websocket.send(json.dumps(test_message))
        print(f"📤 Sent test message: {test_message}")

        # Wait for a response
        try:
            response = await asyncio.wait_for(websocket.recv(), timeout=2.0)
            print(f"📨 Received response: {response}")
        except asyncio.TimeoutError:
            print(f"⏰ No response received (timeout)")

        await websocket.close()
        print(f"🔌 Connection closed")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ Invalid status code: {e.status_code}")
        print(f"📋 Response headers: {e.response_headers}")
        if hasattr(e, 'response_body'):
            print(f"📄 Response body: {e.response_body}")
    except websockets.exceptions.ConnectionClosed as e:
        print(f"❌ Connection closed: {e}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

async def test_all_endpoints():
    """Test all endpoints one by one."""

    endpoints = [
        "ws://localhost:8001/ws/dashboard/default",
        "ws://localhost:8001/ws/bi/revenue-intelligence/default",
        "ws://localhost:8001/ws/bot-performance/default",
        "ws://localhost:8001/ws/business-intelligence/default",
        "ws://localhost:8001/ws/ai-concierge/default",
        "ws://localhost:8001/ws/analytics/advanced/default"
    ]

    for i, url in enumerate(endpoints, 1):
        print(f"\n{'='*60}")
        print(f"🧪 Test {i}/6: {url.split('/')[-2]}")
        print(f"{'='*60}")

        try:
            websocket = await websockets.connect(url)
            print(f"✅ SUCCESS: Connected to {url}")
            await websocket.close()
        except websockets.exceptions.InvalidStatusCode as e:
            print(f"❌ FAILED: {url} -> HTTP {e.status_code}")
        except Exception as e:
            print(f"❌ FAILED: {url} -> {e}")

    print(f"\n{'='*60}")
    print(f"🏁 All endpoint tests completed")
    print(f"{'='*60}")

if __name__ == "__main__":
    print("🧪 Simple WebSocket Connection Test")
    print("=" * 40)

    asyncio.run(test_all_endpoints())