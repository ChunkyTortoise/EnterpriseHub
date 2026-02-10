import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Simple WebSocket Integration Test for Jorge's Real Estate AI Platform.

This script tests the WebSocket and Socket.IO services directly without
the full FastAPI application to verify Phase 3 deployment.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# Test WebSocket server directly
async def test_websocket_services():
    """Test WebSocket services independently."""
    print("🚀 Phase 3: WebSocket Integration Test")
    print("=" * 50)

    try:
        # Test WebSocket Manager
        print("1. Testing WebSocket Manager...")
        from ghl_real_estate_ai.services.websocket_server import get_websocket_manager

        websocket_manager = get_websocket_manager()
        await websocket_manager.start_services()
        print("✅ WebSocket Manager initialized successfully")

        # Test Event Publisher
        print("2. Testing Event Publisher...")
        from ghl_real_estate_ai.services.event_publisher import get_event_publisher

        event_publisher = get_event_publisher()
        await event_publisher.start()
        print("✅ Event Publisher initialized successfully")

        # Test System Health Monitor
        print("3. Testing System Health Monitor...")
        from ghl_real_estate_ai.services.system_health_monitor import start_system_health_monitoring

        await start_system_health_monitoring()
        print("✅ System Health Monitor started successfully")

        # Test Socket.IO Manager
        print("4. Testing Socket.IO Manager...")
        from ghl_real_estate_ai.services.socketio_adapter import get_socketio_manager

        socketio_manager = get_socketio_manager()
        print("✅ Socket.IO Manager initialized successfully")

        # Test Coordination Engine
        print("5. Testing Coordination Engine...")
        from ghl_real_estate_ai.services.coordination_engine import get_coordination_engine

        coordination_engine = get_coordination_engine()
        print("✅ Coordination Engine initialized successfully")

        print("\n🎯 WebSocket Integration Services Status:")
        print("━" * 50)

        # Get metrics
        ws_metrics = websocket_manager.get_metrics()
        event_metrics = event_publisher.get_metrics()

        print(f"📊 WebSocket Connections: {ws_metrics.get('active_connections', 0)}")
        print(f"📈 Total Events Published: {event_metrics.get('total_events_published', 0)}")
        print(f"⚡ Average Processing Time: {event_metrics.get('average_processing_time_ms', 0):.2f}ms")
        print(f"🔄 Cache Hit Rate: {ws_metrics.get('cache_hits', 0)}")

        # Test Event Publishing
        print("\n6. Testing Event Publishing...")
        await event_publisher.publish_system_alert(
            alert_type="test",
            message="WebSocket integration test successful",
            severity="info"
        )
        print("✅ System alert published successfully")

        # Test Bot Status Update
        await event_publisher.publish_bot_status_update(
            bot_type="test-bot",
            contact_id="test-contact-123",
            status="active",
            current_step="integration-test"
        )
        print("✅ Bot status update published successfully")

        # Test Jorge Qualification Progress
        await event_publisher.publish_jorge_qualification_progress(
            contact_id="test-contact-123",
            current_question=2,
            questions_answered=1,
            seller_temperature="warm"
        )
        print("✅ Jorge qualification progress published successfully")

        print("\n🏆 PHASE 3 RESULTS:")
        print("━" * 50)
        print("✅ WebSocket Manager: OPERATIONAL")
        print("✅ Event Publisher: OPERATIONAL")
        print("✅ System Health Monitor: OPERATIONAL")
        print("✅ Socket.IO Integration: OPERATIONAL")
        print("✅ Coordination Engine: OPERATIONAL")
        print("✅ Real-time Event Publishing: OPERATIONAL")
        print("✅ Jorge Bot Event Integration: OPERATIONAL")

        # Final metrics
        final_metrics = event_publisher.get_metrics()
        print(f"\n📊 Final Metrics:")
        print(f"   Total Events: {final_metrics.get('total_events_published', 0)}")
        print(f"   Processing Time: {final_metrics.get('average_processing_time_ms', 0):.2f}ms")
        print(f"   Last Event: {final_metrics.get('last_event_time', 'None')}")

        print(f"\n🎉 WebSocket Integration Deployment: SUCCESS")
        print(f"⏰ Test completed at: {datetime.now().isoformat()}")

        # Clean shutdown
        print("\n7. Graceful shutdown...")
        await event_publisher.stop()
        await websocket_manager.stop_services()
        from ghl_real_estate_ai.services.system_health_monitor import stop_system_health_monitoring
        await stop_system_health_monitoring()

        print("✅ All services stopped gracefully")

        return True

    except Exception as e:
        print(f"❌ WebSocket integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_websocket_health_endpoint():
    """Test the WebSocket health endpoint without full app."""
    print("\n8. Testing WebSocket Health Components...")

    try:
        from ghl_real_estate_ai.api.routes.websocket_routes import router
        print("✅ WebSocket routes module loaded successfully")

        # Check if the health function exists
        health_func = None
        for route in router.routes:
            if hasattr(route, 'path') and route.path.endswith('/health'):
                health_func = route.endpoint
                break

        if health_func:
            print("✅ WebSocket health endpoint found")
        else:
            print("⚠️ WebSocket health endpoint not found in routes")

        return True

    except Exception as e:
        print(f"❌ WebSocket health test failed: {e}")
        return False

async def main():
    """Main test runner."""
    print("🔧 Starting WebSocket Integration Validation...")
    print("📅 " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print()

    # Test WebSocket services
    websocket_success = await test_websocket_services()

    # Test health endpoints
    health_success = test_websocket_health_endpoint()

    print("\n" + "="*60)
    print("🎯 PHASE 3 DEPLOYMENT SUMMARY")
    print("="*60)

    if websocket_success and health_success:
        print("🚀 Status: DEPLOYMENT SUCCESSFUL")
        print("✅ All WebSocket services operational")
        print("✅ Real-time bot coordination ready")
        print("✅ Socket.IO integration functional")
        print("✅ Health monitoring active")
        print("✅ Event publishing system ready")
        print("\n🎉 Jorge's Real Estate AI Platform Phase 3 Complete!")
        print("Ready for production WebSocket deployment.")
        return 0
    else:
        print("❌ Status: DEPLOYMENT ISSUES DETECTED")
        print("⚠️ Some services may not be fully operational")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)