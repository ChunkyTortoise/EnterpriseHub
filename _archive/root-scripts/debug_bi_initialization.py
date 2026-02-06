#!/usr/bin/env python3
"""
Debug BI WebSocket Service Initialization

Check if the BI WebSocket services can be properly initialized.
"""

import sys
import asyncio
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

async def test_bi_initialization():
    """Test BI WebSocket service initialization."""

    print("🧪 Debug BI WebSocket Initialization")
    print("=" * 50)

    try:
        print("📋 Importing BI WebSocket manager...")
        from ghl_real_estate_ai.services.bi_websocket_server import get_bi_websocket_manager

        bi_manager = get_bi_websocket_manager()
        print(f"✅ BI WebSocket manager imported successfully")
        print(f"📊 Manager running status: {bi_manager.is_running}")

        if not bi_manager.is_running:
            print("⚠️  BI WebSocket manager is not running")
            print("📋 Attempting to start...")

            try:
                await bi_manager.start()
                print(f"✅ BI WebSocket manager started successfully")
                print(f"📊 New running status: {bi_manager.is_running}")
            except Exception as e:
                print(f"❌ Failed to start BI WebSocket manager: {e}")
                print(f"🔍 Error type: {type(e).__name__}")
        else:
            print("✅ BI WebSocket manager is already running")

        # Get manager status
        try:
            status = await bi_manager.get_status()
            print(f"📊 Manager status: {status}")
        except Exception as e:
            print(f"⚠️ Could not get manager status: {e}")

    except ImportError as e:
        print(f"❌ Import failed: {e}")
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

async def test_bi_routes_import():
    """Test if BI routes can be imported."""

    print(f"\n📋 Testing BI routes import...")

    try:
        from ghl_real_estate_ai.api.routes.bi_websocket_routes import initialize_bi_websocket_services
        print("✅ BI routes imported successfully")

        print("📋 Attempting to initialize BI WebSocket services...")
        result = await initialize_bi_websocket_services()
        print(f"📊 Initialization result: {result}")

        if result:
            print("✅ BI WebSocket services initialized successfully")
        else:
            print("❌ BI WebSocket services initialization failed")

    except Exception as e:
        print(f"❌ BI routes import/init failed: {e}")
        print(f"🔍 Error type: {type(e).__name__}")

if __name__ == "__main__":
    asyncio.run(test_bi_initialization())
    asyncio.run(test_bi_routes_import())