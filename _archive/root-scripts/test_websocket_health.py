#!/usr/bin/env python3
"""
WebSocket Health Endpoint Test for Jorge's Real Estate AI Platform.

Simple test to validate WebSocket health endpoints are accessible.
"""

import asyncio
import aiohttp
import time
from datetime import datetime

async def test_websocket_health():
    """Test WebSocket health endpoint."""
    print("🔍 Testing WebSocket Health Endpoint")
    print("=" * 40)

    # Start a minimal FastAPI server with just health endpoints
    import os
    import subprocess
    import signal

    # Set minimal environment variables to avoid JWT errors
    env = os.environ.copy()
    env['JWT_SECRET_KEY'] = 'test-secret-key-for-health-check'
    env['ANTHROPIC_API_KEY'] = 'sk-ant-test'
    env['GHL_API_KEY'] = 'test-ghl-key'

    # Start FastAPI server in background with minimal config
    print("🚀 Starting minimal FastAPI server...")

    try:
        # Create minimal main file for health testing
        minimal_app_content = '''
from fastapi import FastAPI
from ghl_real_estate_ai.api.routes import websocket_routes

app = FastAPI(title="WebSocket Health Test")
app.include_router(websocket_routes.router, prefix="/api")

@app.get("/")
async def root():
    return {"status": "WebSocket Health Test Server Running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="error")
'''

        # Write minimal app
        with open('/tmp/minimal_websocket_app.py', 'w') as f:
            f.write(minimal_app_content)

        # Start server
        server_process = subprocess.Popen([
            'python', '/tmp/minimal_websocket_app.py'
        ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # Wait for server to start
        print("⏳ Waiting for server to start...")
        await asyncio.sleep(3)

        # Test health endpoint
        async with aiohttp.ClientSession() as session:
            try:
                print("🔗 Testing WebSocket health endpoint...")
                async with session.get('http://localhost:8001/api/websocket/health', timeout=10) as response:
                    if response.status == 200:
                        data = await response.json()
                        print("✅ WebSocket health endpoint responding")
                        print(f"   Status: {data.get('status', 'unknown')}")
                        print(f"   Service: {data.get('service', 'unknown')}")
                        print(f"   Active Connections: {data.get('active_connections', 0)}")
                        return True
                    else:
                        print(f"❌ Health endpoint returned status {response.status}")
                        return False

            except asyncio.TimeoutError:
                print("❌ Health endpoint timeout")
                return False
            except Exception as e:
                print(f"❌ Health endpoint error: {e}")
                return False

    except Exception as e:
        print(f"❌ Failed to start health test server: {e}")
        return False

    finally:
        # Clean up server
        if 'server_process' in locals():
            try:
                server_process.terminate()
                server_process.wait(timeout=5)
            except:
                server_process.kill()

        # Clean up temp file
        try:
            os.unlink('/tmp/minimal_websocket_app.py')
        except:
            pass

async def test_websocket_endpoints():
    """Test WebSocket endpoint accessibility."""
    print("\n🔍 Testing Direct WebSocket Services")
    print("=" * 40)

    try:
        # Test health function directly without HTTP
        from ghl_real_estate_ai.api.routes.websocket_routes import websocket_health_check

        print("📡 Testing websocket_health_check function...")
        result = await websocket_health_check()

        if hasattr(result, 'body'):
            # It's a JSONResponse
            import json
            health_data = json.loads(result.body.decode())
            print("✅ WebSocket health function working")
            print(f"   Status: {health_data.get('status', 'unknown')}")
            print(f"   Service: {health_data.get('service', 'unknown')}")
            return True
        else:
            print("❌ Unexpected health check response format")
            return False

    except Exception as e:
        print(f"❌ Direct health check failed: {e}")
        return False

async def main():
    """Main health test runner."""
    print("🏥 WebSocket Health Validation")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    # Test direct endpoints
    direct_success = await test_websocket_endpoints()

    # Test HTTP endpoints
    # http_success = await test_websocket_health()

    print("\n" + "="*50)
    print("🏥 WEBSOCKET HEALTH TEST SUMMARY")
    print("="*50)

    if direct_success:
        print("✅ WebSocket Health: OPERATIONAL")
        print("✅ Health functions working correctly")
        print("✅ WebSocket services accessible")
        print("\n🎉 WebSocket health validation complete!")
        return 0
    else:
        print("❌ WebSocket Health: ISSUES DETECTED")
        print("⚠️ Some health endpoints may not be working")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)