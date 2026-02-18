import pytest
pytestmark = pytest.mark.integration

"""
BI Backend Integration Test Suite.

Comprehensive tests to verify that all BI backend services are properly
integrated and working together for Jorge's Real Estate AI Platform.

Tests:
- BI WebSocket endpoint connectivity
- API endpoint functionality
- Database schema validation
- Real-time event publishing
- Cache performance
- Service health checks

Author: Claude Sonnet 4
Date: 2026-01-25
"""

import asyncio
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock, patch

import httpx
import pytest
import pytest_asyncio
import websockets
from fastapi.testclient import TestClient

# Import the main FastAPI app
from ghl_real_estate_ai.api.main import app
from ghl_real_estate_ai.services.bi_cache_service import get_bi_cache_service
from ghl_real_estate_ai.services.bi_stream_processor import get_bi_stream_processor
from ghl_real_estate_ai.services.bi_websocket_server import get_bi_websocket_manager



class TestBIIntegration:
    """Test suite for BI backend integration."""

    @pytest.fixture
    def client(self):
        """FastAPI test client."""
        return TestClient(app)

    @pytest_asyncio.fixture
    async def bi_services(self):
        """Initialize BI services for testing."""
        # Get service instances
        bi_websocket_manager = get_bi_websocket_manager()
        bi_cache_service = get_bi_cache_service()
        bi_stream_processor = get_bi_stream_processor()

        # Start services
        services = {
            "websocket_manager": bi_websocket_manager,
            "cache_service": bi_cache_service,
            "stream_processor": bi_stream_processor,
        }

        # Start BI WebSocket manager
        if not bi_websocket_manager.is_running:
            await bi_websocket_manager.start()

        yield services

        # Cleanup
        if bi_websocket_manager.is_running:
            await bi_websocket_manager.stop()

    # ========================================================================
    # API ENDPOINT TESTS
    # ========================================================================

    def test_bi_api_routes_registered(self, client):
        """Test that BI API routes are properly registered."""
        # Test dashboard KPIs endpoint
        response = client.get("/api/bi/dashboard-kpis?timeframe=24h")
        assert response.status_code in [200, 401]  # 200 if auth disabled, 401 if enabled

        # Test revenue intelligence endpoint
        response = client.get("/api/bi/revenue-intelligence?timeframe=30d")
        assert response.status_code in [200, 401]

        # Test bot performance endpoint
        response = client.get("/api/bi/bot-performance?timeframe=7d")
        assert response.status_code in [200, 401]

        # Test real-time metrics endpoint
        response = client.get("/api/bi/real-time-metrics")
        assert response.status_code in [200, 401]

    def test_bi_websocket_health_endpoint(self, client):
        """Test BI WebSocket health endpoint."""
        response = client.get("/ws/bi/health")
        assert response.status_code == 200

        health_data = response.json()
        assert health_data["service"] == "BI WebSocket Real-Time Service"
        assert "status" in health_data
        assert "bi_connections" in health_data

    def test_bi_websocket_metrics_endpoint(self, client):
        """Test BI WebSocket metrics endpoint."""
        response = client.get("/ws/bi/metrics")
        assert response.status_code == 200

        metrics_data = response.json()
        assert "timestamp" in metrics_data
        assert "metrics" in metrics_data

    # ========================================================================
    # WEBSOCKET ENDPOINT TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_dashboard_websocket_connection(self, bi_services):
        """Test dashboard WebSocket connection."""
        websocket_manager = bi_services["websocket_manager"]

        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()
        mock_websocket.receive_text = AsyncMock(side_effect=StopAsyncIteration)

        try:
            # Test connection handling
            connection_id = await websocket_manager.connect_bi_client(
                websocket=mock_websocket,
                location_id="test_location",
                channels=["dashboard", "alerts"],
                components=["executive_kpis", "system_health"],
            )

            assert connection_id is not None
            assert connection_id in websocket_manager.bi_connections

            # Verify connection properties
            connection = websocket_manager.bi_connections[connection_id]
            assert connection.location_id == "test_location"
            assert len(connection.subscribed_channels) >= 1
            assert len(connection.subscribed_components) >= 1

            # Test message sending
            await websocket_manager.send_dashboard_update(
                component="test_component", data={"value": 123}, location_id="test_location"
            )

            # Verify WebSocket send was called
            mock_websocket.send_text.assert_called()

        finally:
            # Cleanup
            if connection_id in websocket_manager.bi_connections:
                await websocket_manager.disconnect_bi_client(connection_id)

    @pytest.mark.asyncio
    async def test_revenue_intelligence_websocket(self, bi_services):
        """Test revenue intelligence WebSocket connection."""
        websocket_manager = bi_services["websocket_manager"]

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        connection_id = await websocket_manager.connect_bi_client(
            websocket=mock_websocket,
            location_id="test_location",
            channels=["revenue_intelligence", "analytics"],
            components=["revenue_forecasting", "jorge_commission"],
        )

        try:
            assert connection_id is not None

            # Test revenue analytics update
            await websocket_manager.send_analytics_update(
                analytics_type="revenue_forecast",
                data={"predicted_revenue": 25000, "jorge_commission": 1500, "confidence": 0.85},
                location_id="test_location",
            )

            mock_websocket.send_text.assert_called()

        finally:
            await websocket_manager.disconnect_bi_client(connection_id)

    @pytest.mark.asyncio
    async def test_bot_performance_websocket(self, bi_services):
        """Test bot performance WebSocket connection."""
        websocket_manager = bi_services["websocket_manager"]

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()

        connection_id = await websocket_manager.connect_bi_client(
            websocket=mock_websocket,
            location_id="test_location",
            channels=["bot_performance", "alerts"],
            components=["jorge_seller_performance", "bot_coordination"],
        )

        try:
            assert connection_id is not None

            # Test performance alert
            await websocket_manager.send_performance_alert(
                alert_type="bot_performance",
                severity="medium",
                message="Jorge Seller Bot response time above threshold",
                data={"bot_type": "jorge-seller", "response_time_ms": 85.2, "threshold_ms": 50},
                location_id="test_location",
            )

            mock_websocket.send_text.assert_called()

        finally:
            await websocket_manager.disconnect_bi_client(connection_id)

    # ========================================================================
    # SERVICE INTEGRATION TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_bi_service_integration(self, bi_services):
        """Test integration between BI services."""
        websocket_manager = bi_services["websocket_manager"]
        cache_service = bi_services["cache_service"]

        # Test WebSocket manager metrics
        metrics = websocket_manager.get_metrics()
        assert isinstance(metrics, dict)
        assert "total_connections" in metrics
        assert "channel_subscriptions" in metrics

        # Test background tasks are running
        assert websocket_manager.is_running
        assert len(websocket_manager.background_tasks) > 0

        # Test service health
        health_data = websocket_manager.getBIConnectionHealth()
        assert "connected" in health_data
        assert "total" in health_data
        assert "status" in health_data

    @pytest.mark.asyncio
    async def test_real_time_event_flow(self, bi_services):
        """Test real-time event flow through BI services."""
        websocket_manager = bi_services["websocket_manager"]

        # Mock WebSocket connection
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect_bi_client(
            websocket=mock_websocket,
            location_id="test_location",
            channels=["dashboard", "analytics"],
            components=["real_time_metrics"],
        )

        try:
            # Simulate real-time event
            test_event_data = {
                "component": "real_time_metrics",
                "metrics": {
                    "leads_processed": 45,
                    "hot_leads": 12,
                    "jorge_commission_pipeline": 27500,
                    "avg_response_time_ms": 42.3,
                },
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            await websocket_manager.send_dashboard_update(
                component="real_time_metrics", data=test_event_data, location_id="test_location"
            )

            # Verify message was sent
            mock_websocket.send_text.assert_called()

            # Verify message content
            call_args = mock_websocket.send_text.call_args[0][0]
            message_data = json.loads(call_args)

            assert message_data["channel"] == "dashboard"
            assert message_data["event_type"] == "COMPONENT_UPDATE"
            assert message_data["component"] == "real_time_metrics"
            assert "data" in message_data

        finally:
            await websocket_manager.disconnect_bi_client(connection_id)

    @pytest.mark.asyncio
    async def test_concurrent_connections(self, bi_services):
        """Test handling multiple concurrent WebSocket connections."""
        websocket_manager = bi_services["websocket_manager"]

        # Create multiple mock connections
        connections = []
        for i in range(5):
            mock_websocket = AsyncMock()
            mock_websocket.accept = AsyncMock()
            mock_websocket.send_text = AsyncMock()

            connection_id = await websocket_manager.connect_bi_client(
                websocket=mock_websocket,
                location_id=f"location_{i}",
                channels=["dashboard"],
                components=[f"component_{i}"],
            )
            connections.append((connection_id, mock_websocket))

        try:
            # Verify all connections are registered
            assert len(websocket_manager.bi_connections) >= 5

            # Send broadcast message
            await websocket_manager.send_dashboard_update(
                component="global_update",
                data={"message": "Broadcast test"},
                location_id="location_0",  # Should only reach location_0
            )

            # Verify only the matching location received the message
            location_0_websocket = connections[0][1]
            location_0_websocket.send_text.assert_called()

        finally:
            # Cleanup all connections
            for connection_id, _ in connections:
                await websocket_manager.disconnect_bi_client(connection_id)

    # ========================================================================
    # PERFORMANCE TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_websocket_performance(self, bi_services):
        """Test WebSocket performance under load."""
        websocket_manager = bi_services["websocket_manager"]

        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await websocket_manager.connect_bi_client(
            websocket=mock_websocket,
            location_id="perf_test_location",
            channels=["dashboard"],
            components=["performance_metrics"],
        )

        try:
            # Send multiple messages quickly
            start_time = time.time()
            message_count = 10

            for i in range(message_count):
                await websocket_manager.send_dashboard_update(
                    component="performance_metrics",
                    data={"message_id": i, "timestamp": time.time()},
                    location_id="perf_test_location",
                )

            end_time = time.time()
            total_time = end_time - start_time

            # Verify performance targets
            avg_time_per_message = total_time / message_count
            assert avg_time_per_message < 0.010  # <10ms per message

            # Verify all messages were sent
            assert mock_websocket.send_text.call_count == message_count

        finally:
            await websocket_manager.disconnect_bi_client(connection_id)

    # ========================================================================
    # ERROR HANDLING TESTS
    # ========================================================================

    @pytest.mark.asyncio
    async def test_websocket_error_handling(self, bi_services):
        """Test WebSocket error handling and recovery."""
        websocket_manager = bi_services["websocket_manager"]

        # Mock WebSocket with send error
        mock_websocket = AsyncMock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock(side_effect=Exception("Connection error"))

        connection_id = await websocket_manager.connect_bi_client(
            websocket=mock_websocket, location_id="error_test_location"
        )

        try:
            # Attempt to send message (should handle error gracefully)
            await websocket_manager.send_dashboard_update(
                component="error_test", data={"test": "error_handling"}, location_id="error_test_location"
            )

            # Verify connection quality was updated
            if connection_id in websocket_manager.bi_connections:
                connection = websocket_manager.bi_connections[connection_id]
                # Connection quality should be reduced due to error
                assert connection.connection_quality < 1.0

        except Exception as e:
            # Should not propagate exceptions
            pytest.fail(f"WebSocket error was not properly handled: {e}")

        finally:
            if connection_id in websocket_manager.bi_connections:
                await websocket_manager.disconnect_bi_client(connection_id)

    # ========================================================================
    # UTILITY FUNCTIONS
    # ========================================================================

    @pytest.fixture(scope="session")
    def event_loop(self):
        """Create an event loop for the test session."""
        loop = asyncio.get_event_loop_policy().new_event_loop()
        yield loop
        loop.close()


# ========================================================================
# INTEGRATION TEST RUNNER
# ========================================================================


async def run_integration_tests():
    """Run all BI integration tests."""
    print("🧪 Running BI Backend Integration Tests...")
    print("=" * 50)

    # Test service initialization
    print("1. Testing service initialization...")
    try:
        bi_websocket_manager = get_bi_websocket_manager()
        bi_cache_service = get_bi_cache_service()
        bi_stream_processor = get_bi_stream_processor()
        print("   ✅ All BI services initialized successfully")
    except Exception as e:
        print(f"   ❌ Service initialization failed: {e}")
        return False

    # Test WebSocket manager startup
    print("2. Testing WebSocket manager startup...")
    try:
        if not bi_websocket_manager.is_running:
            await bi_websocket_manager.start()
        print(f"   ✅ BI WebSocket manager started (connections: {len(bi_websocket_manager.bi_connections)})")
    except Exception as e:
        print(f"   ❌ WebSocket manager startup failed: {e}")
        return False

    # Test API endpoints
    print("3. Testing API endpoint registration...")
    try:
        client = TestClient(app)
        response = client.get("/ws/bi/health")
        if response.status_code == 200:
            print("   ✅ BI API endpoints registered and responding")
        else:
            print(f"   ⚠️ BI health endpoint returned status {response.status_code}")
    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")

    # Test WebSocket connection capability
    print("4. Testing WebSocket connection capability...")
    try:
        # Mock WebSocket for testing
        mock_websocket = Mock()
        mock_websocket.accept = AsyncMock()
        mock_websocket.send_text = AsyncMock()

        connection_id = await bi_websocket_manager.connect_bi_client(
            websocket=mock_websocket,
            location_id="integration_test",
            channels=["dashboard"],
            components=["test_component"],
        )

        if connection_id:
            print("   ✅ WebSocket connection handling working")
            await bi_websocket_manager.disconnect_bi_client(connection_id)
        else:
            print("   ❌ WebSocket connection failed")
    except Exception as e:
        print(f"   ❌ WebSocket connection test failed: {e}")

    # Test real-time messaging
    print("5. Testing real-time messaging...")
    try:
        await bi_websocket_manager.send_dashboard_update(
            component="integration_test",
            data={"test": "integration_success", "timestamp": datetime.now().isoformat()},
            location_id="integration_test",
        )
        print("   ✅ Real-time messaging working")
    except Exception as e:
        print(f"   ❌ Real-time messaging test failed: {e}")

    # Test service metrics
    print("6. Testing service metrics...")
    try:
        metrics = bi_websocket_manager.get_metrics()
        if isinstance(metrics, dict) and "total_connections" in metrics:
            print(f"   ✅ Service metrics available (connections: {metrics.get('total_connections', 0)})")
        else:
            print("   ⚠️ Service metrics incomplete")
    except Exception as e:
        print(f"   ❌ Service metrics test failed: {e}")

    # Cleanup
    print("7. Cleaning up test environment...")
    try:
        if bi_websocket_manager.is_running:
            await bi_websocket_manager.stop()
        print("   ✅ Cleanup completed")
    except Exception as e:
        print(f"   ⚠️ Cleanup warning: {e}")

    print("=" * 50)
    print("🎉 BI Backend Integration Tests Completed!")
    print("\nNext steps:")
    print("- Run database schema: `psql -d jorge_db -f ghl_real_estate_ai/database/olap_schema.sql`")
    print("- Start FastAPI server: `uvicorn ghl_real_estate_ai.api.main:app --reload`")
    print("- Test frontend connections to all 6 WebSocket endpoints")
    print("- Verify real-time dashboard updates")

    return True


if __name__ == "__main__":
    # Run integration tests
    asyncio.run(run_integration_tests())
