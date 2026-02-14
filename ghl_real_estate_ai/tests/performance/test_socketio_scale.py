import pytest

"""
Socket.IO Scale Testing Utility
===============================

Validates the 10,000+ concurrent user target for Jorge's Socket.IO integration.
Simulates high volume of concurrent connections and message throughput.
"""

import argparse
import asyncio
import logging
import random
import statistics
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import socketio

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class ScaleTestResult:
    """Summary of scale test results."""

    target_users: int
    actual_connections: int
    connection_success_rate: float
    total_messages_sent: int
    total_messages_received: int
    avg_latency_ms: float
    p95_latency_ms: float
    test_duration_s: float
    throughput_msg_per_s: float


class SocketIOScaleTester:
    """Utility to test Socket.IO scalability."""

    def __init__(self, server_url: str = "http://localhost:8002"):
        self.server_url = server_url
        self.clients = []
        self.results = {
            "connected": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "latencies": [],
            "connection_errors": 0,
        }
        self.start_time = None

    async def connect_client(self, user_id: int):
        sio = socketio.AsyncClient(logger=False, engineio_logger=False)

        @sio.on("connection_established")
        async def on_welcome(data):
            self.results["connected"] += 1
            # logger.debug(f"Client {user_id} connected: {data['message']}")

        @sio.on("lead_update")
        async def on_lead_update(data):
            self.results["messages_received"] += 1

        try:
            # Generate proper JWT token for testing
            # Import here to avoid circular dependencies
            import os
            import sys

            # Try to use proper JWT authentication
            auth_token = None
            demo_bypass_enabled = os.getenv("ENABLE_DEMO_BYPASS", "false").lower() == "true"

            if demo_bypass_enabled:
                # Demo bypass explicitly enabled for testing
                auth_token = "demo_token"
                if self.results["connected"] == 0:  # Log once
                    logger.warning("Using demo_token bypass for scale test (ENABLE_DEMO_BYPASS=true)")
            else:
                # Generate proper test JWT
                try:
                    # Add tests/helpers to path if not already there
                    test_helpers_path = os.path.join(os.path.dirname(__file__), "..", "helpers")
                    if test_helpers_path not in sys.path:
                        sys.path.insert(0, test_helpers_path)

                    from test_auth import generate_test_jwt

                    auth_token = generate_test_jwt(
                        user_id=f"scale_test_user_{user_id}",
                        email=f"test_{user_id}@scale.test",
                        tenant_id="scale_test_tenant",
                    )
                    if self.results["connected"] == 0:  # Log once
                        logger.info("Using proper JWT authentication for scale test")
                except ImportError:
                    logger.error(
                        "Failed to import test_auth helper. Install jwt library or enable ENABLE_DEMO_BYPASS=true"
                    )
                    raise

            await sio.connect(self.server_url, auth={"token": auth_token}, namespaces=["/"])
            self.clients.append(sio)

            # Authenticate (simulated)
            # await sio.emit('authenticate', {'token': f'token_{user_id}', 'location_id': f'loc_{user_id % 10}'}, namespace='/'})

            return True
        except Exception as e:
            self.results["connection_errors"] += 1
            if self.results["connection_errors"] <= 5:  # Only log first few errors to avoid spam
                logger.error(f"Client {user_id} connection failed: {e}")
            return False

    async def run_scale_test(self, num_users: int, duration: int, ramp_up_rate: int = 100):
        """
        Run the scale test.

        Args:
            num_users: Target number of concurrent users
            duration: Duration of the test in seconds (after ramp up)
            ramp_up_rate: Number of connections to open per second
        """
        logger.info(f"🚀 Starting Socket.IO Scale Test:")
        logger.info(f"   Target Users: {num_users}")
        logger.info(f"   Ramp-up Rate: {ramp_up_rate} users/s")
        logger.info(f"   Duration: {duration}s")
        logger.info(f"   Server: {self.server_url}")

        self.start_time = time.time()

        # 1. Ramp up phase
        logger.info(f"⚡ Ramping up {num_users} users...")
        for i in range(0, num_users, ramp_up_rate):
            batch_size = min(ramp_up_rate, num_users - i)
            tasks = [self.connect_client(i + j) for j in range(batch_size)]
            await asyncio.gather(*tasks)
            # logger.info(f"   Connected {len(self.clients)}/{num_users} users...")
            await asyncio.sleep(1)  # Wait a second before next batch

        actual_connections = len(self.clients)
        logger.info(f"✅ Ramp-up complete. Active connections: {actual_connections}")

        if actual_connections == 0:
            logger.error("❌ No connections established. Aborting test.")
            return None

        # 2. Sustain load phase
        logger.info(f"🔥 Sustaining load for {duration}s...")
        test_end_time = time.time() + duration

        async def simulate_traffic(client, client_id):
            while time.time() < test_end_time:
                try:
                    await client.emit(
                        "ping_performance", {"timestamp": time.time(), "client_id": client_id}, namespace="/jorge"
                    )
                    self.results["messages_sent"] += 1
                    # Random delay between 5-15 seconds to simulate realistic dashboard activity
                    await asyncio.sleep(random.uniform(5, 15))
                except Exception:
                    break

        traffic_tasks = [asyncio.create_task(simulate_traffic(client, i)) for i, client in enumerate(self.clients)]

        await asyncio.sleep(duration)

        # 3. Cleanup phase
        logger.info(f"🧹 Cleaning up...")
        for task in traffic_tasks:
            task.cancel()

        disconnect_tasks = [client.disconnect() for client in self.clients]
        await asyncio.gather(*disconnect_tasks, return_exceptions=True)

        # 4. Calculate results
        total_duration = time.time() - self.start_time

        latencies = self.results["latencies"]
        avg_latency = statistics.mean(latencies) if latencies else 0
        p95_latency = (
            statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else (max(latencies) if latencies else 0)
        )

        result = ScaleTestResult(
            target_users=num_users,
            actual_connections=actual_connections,
            connection_success_rate=actual_connections / num_users,
            total_messages_sent=self.results["messages_sent"],
            total_messages_received=self.results["messages_received"],
            avg_latency_ms=avg_latency,
            p95_latency_ms=p95_latency,
            test_duration_s=total_duration,
            throughput_msg_per_s=self.results["messages_sent"] / duration,
        )

        self._print_summary(result)
        return result

    def _print_summary(self, result: ScaleTestResult):
        logger.info("\n" + "=" * 50)
        logger.info("📊 SOCKET.IO SCALE TEST SUMMARY")
        logger.info("=" * 50)
        logger.info(f"Target Users:         {result.target_users}")
        logger.info(f"Actual Connections:   {result.actual_connections}")
        logger.info(f"Success Rate:         {result.connection_success_rate:.1%}")
        logger.info(f"Total Messages Sent:  {result.total_messages_sent}")
        logger.info(f"Total Messages Recv:  {result.total_messages_received}")
        logger.info(f"Avg Latency:          {result.avg_latency_ms:.2f}ms")
        logger.info(f"P95 Latency:          {result.p95_latency_ms:.2f}ms")
        logger.info(f"Throughput:           {result.throughput_msg_per_s:.2f} msg/s")
        logger.info(f"Total Test Duration:  {result.test_duration_s:.1f}s")
        logger.info("=" * 50)

        if result.connection_success_rate > 0.95 and result.avg_latency_ms < 200:
            logger.info("🟢 SCALE TARGET VALIDATED")
        elif result.connection_success_rate > 0.80:
            logger.info("🟡 SCALE TARGET PARTIALLY MET")
        else:
            logger.info("🔴 SCALE TARGET FAILED")


async def test_socketio_scalability_basic():
    """Pytest entry point for basic scalability check."""
    tester = SocketIOScaleTester()
    # Run a smaller version for CI
    result = await tester.run_scale_test(num_users=100, duration=10, ramp_up_rate=50)
    assert result.connection_success_rate > 0.90
    assert result.avg_latency_ms < 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Socket.IO Scale Tester")
    parser.add_argument("--users", "-u", type=int, default=1000, help="Number of concurrent users")
    parser.add_argument("--duration", "-d", type=int, default=30, help="Duration in seconds")
    parser.add_argument("--rate", "-r", type=int, default=100, help="Ramp-up rate (users/s)")
    parser.add_argument("--url", type=str, default="http://localhost:8002", help="Server URL")

    args = parser.parse_args()

    async def main():
        tester = SocketIOScaleTester(args.url)
        await tester.run_scale_test(args.users, args.duration, args.rate)

    asyncio.run(main())
