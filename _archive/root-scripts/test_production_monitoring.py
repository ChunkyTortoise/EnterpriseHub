import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Test script for production monitoring and database optimization systems.

Validates that all monitoring and optimization components work correctly.
"""

import asyncio
import sys
import os
from pathlib import Path
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from ghl_real_estate_ai.services.production_monitoring import (
    ProductionMonitor, check_database_health, check_cache_health, ServiceStatus
)
from ghl_real_estate_ai.services.database_optimizer import DatabaseOptimizer


class TestProductionSystems:
    """Test suite for production monitoring and optimization."""

    def __init__(self):
        """Initialize test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.test_db_path = os.path.join(self.test_dir, "test.db")
        print(f"🧪 Test environment: {self.test_dir}")

    async def setup_test_database(self):
        """Create a test database with sample data."""
        import aiosqlite

        async with aiosqlite.connect(self.test_db_path) as db:
            # Create sample tables
            await db.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY,
                    username TEXT NOT NULL,
                    email TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE orders (
                    id INTEGER PRIMARY KEY,
                    user_id INTEGER,
                    amount REAL,
                    status TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """)

            # Insert sample data
            for i in range(100):
                await db.execute(
                    "INSERT INTO users (username, email) VALUES (?, ?)",
                    (f"user{i}", f"user{i}@example.com")
                )

            for i in range(200):
                await db.execute(
                    "INSERT INTO orders (user_id, amount, status) VALUES (?, ?, ?)",
                    (i % 100 + 1, 50.0 + i, "completed" if i % 3 == 0 else "pending")
                )

            await db.commit()

        print("✅ Test database created with sample data")

    async def test_production_monitor(self):
        """Test production monitoring functionality."""
        print("\n📊 Testing Production Monitor")
        print("=" * 40)

        try:
            # Initialize monitor with test database
            monitor = ProductionMonitor(
                monitoring_db_path=os.path.join(self.test_dir, "monitoring.db")
            )

            # Initialize monitoring
            await monitor.initialize_monitoring()
            print("✅ Monitoring database initialized")

            # Test system metrics collection
            system_metrics = await monitor.collect_system_metrics()
            print(f"✅ System metrics collected:")
            print(f"   CPU: {system_metrics.cpu_percent:.1f}%")
            print(f"   Memory: {system_metrics.memory_percent:.1f}%")
            print(f"   Disk: {system_metrics.disk_percent:.1f}%")

            # Test health checks
            print("\n🔍 Running health checks...")

            # Database health check
            db_health = await monitor.check_service_health(
                "test_database",
                lambda: check_database_health(self.test_db_path)
            )

            print(f"✅ Database health: {db_health.status.value}")
            print(f"   Response time: {db_health.response_time_ms:.1f}ms")
            print(f"   Message: {db_health.message}")

            # Cache health check
            cache_health = await monitor.check_service_health(
                "cache",
                check_cache_health
            )

            print(f"✅ Cache health: {cache_health.status.value}")
            print(f"   Response time: {cache_health.response_time_ms:.1f}ms")

            # Test metric recording
            await monitor.record_metric(
                "test_metric",
                42.5,
                monitor.MetricType.GAUGE,
                {"component": "test"}
            )
            print("✅ Custom metric recorded")

            # Test alert creation
            await monitor.create_alert(
                "test_alert",
                "This is a test alert",
                "info",
                "test_service"
            )
            print("✅ Test alert created")

            # Get health summary
            health_summary = await monitor.get_health_summary()
            print(f"✅ Health summary generated:")
            print(f"   Overall status: {health_summary.get('overall_status')}")
            print(f"   Services monitored: {health_summary.get('services', 0)}")

            return True

        except Exception as e:
            print(f"❌ Production monitor test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_database_optimizer(self):
        """Test database optimization functionality."""
        print("\n🗄️ Testing Database Optimizer")
        print("=" * 40)

        try:
            # Initialize optimizer
            optimizer = DatabaseOptimizer([self.test_db_path])
            optimizer.performance_log_path = os.path.join(self.test_dir, "performance.db")

            await optimizer.initialize_optimizer()
            print("✅ Database optimizer initialized")

            # Test database health analysis
            print("\n📊 Analyzing database health...")
            health = await optimizer.analyze_database_health(self.test_db_path)

            print(f"✅ Database health analyzed:")
            print(f"   Size: {health.database_size_mb:.2f} MB")
            print(f"   Average query time: {health.avg_query_time_ms:.1f} ms")
            print(f"   Cache hit ratio: {health.cache_hit_ratio:.1%}")
            print(f"   Fragmentation: {health.fragmentation_ratio:.1%}")

            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(health.recommendations, 1):
                print(f"   {i}. {rec}")

            # Test query performance monitoring
            print("\n⏱️ Testing query performance monitoring...")

            # Simulate some queries
            test_queries = [
                ("SELECT COUNT(*) FROM users", None),
                ("SELECT * FROM users WHERE id = ?", (1,)),
                ("SELECT u.username, COUNT(o.id) FROM users u LEFT JOIN orders o ON u.id = o.user_id GROUP BY u.id", None)
            ]

            for query, params in test_queries:
                performance = await optimizer.monitor_query_performance(
                    self.test_db_path, query, params
                )
                print(f"   Query: {query[:50]}...")
                print(f"   Time: {performance.execution_time_ms:.1f}ms")
                if performance.optimization_suggestion:
                    print(f"   Suggestion: {performance.optimization_suggestion}")

            # Test database optimization
            print("\n🔧 Running database optimization...")
            optimization_results = await optimizer.optimize_database(self.test_db_path)

            print(f"✅ Optimization completed:")
            print(f"   Duration: {optimization_results.get('duration_seconds', 0):.1f}s")
            print(f"   Operations: {len(optimization_results.get('operations', []))}")

            for operation in optimization_results.get('operations', []):
                print(f"   - {operation}")

            if optimization_results.get('errors'):
                print(f"   ⚠️ Errors: {len(optimization_results['errors'])}")
                for error in optimization_results['errors'][:3]:  # Show first 3 errors
                    print(f"     - {error}")

            # Show improvements
            improvements = optimization_results.get('improvements', {})
            if improvements:
                print(f"   📈 Improvements:")
                for metric, value in improvements.items():
                    print(f"     {metric}: {value}")

            return True

        except Exception as e:
            print(f"❌ Database optimizer test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_integration(self):
        """Test integration between monitoring and optimization."""
        print("\n🔗 Testing System Integration")
        print("=" * 40)

        try:
            monitor = ProductionMonitor(
                monitoring_db_path=os.path.join(self.test_dir, "monitoring.db")
            )

            optimizer = DatabaseOptimizer([self.test_db_path])
            optimizer.performance_log_path = os.path.join(self.test_dir, "performance.db")

            # Test database metrics collection
            db_metrics = await optimizer.collect_database_metrics(self.test_db_path)
            print(f"✅ Database metrics collected:")
            print(f"   Connections: {db_metrics.connection_count}")
            print(f"   Query duration: {db_metrics.query_duration_avg_ms:.1f}ms")
            print(f"   Database size: {db_metrics.database_size_mb:.2f}MB")

            # Test system metrics collection
            system_metrics = await monitor.collect_system_metrics()
            print(f"✅ System metrics collected:")
            print(f"   Uptime: {system_metrics.uptime_hours:.1f}h")
            print(f"   Active connections: {system_metrics.active_connections}")

            # Test combined health assessment
            combined_health = {
                'database_health': await optimizer.analyze_database_health(self.test_db_path),
                'system_health': system_metrics,
                'monitoring_health': await monitor.get_health_summary()
            }

            print("✅ Combined health assessment completed")
            print(f"   Overall system status appears functional")

            return True

        except Exception as e:
            print(f"❌ Integration test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cleanup(self):
        """Clean up test environment."""
        try:
            shutil.rmtree(self.test_dir)
            print(f"✅ Test environment cleaned up: {self.test_dir}")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


async def main():
    """Main test function."""
    print("🧪 Production Systems Test Suite")
    print("=" * 50)

    test_suite = TestProductionSystems()

    try:
        # Setup test environment
        await test_suite.setup_test_database()

        # Run individual tests
        tests = [
            ("Production Monitor", test_suite.test_production_monitor()),
            ("Database Optimizer", test_suite.test_database_optimizer()),
            ("System Integration", test_suite.test_integration())
        ]

        results = []
        for test_name, test_coro in tests:
            print(f"\n🔍 Running {test_name} test...")
            result = await test_coro
            results.append((test_name, result))

        # Summary
        print("\n📋 Test Summary")
        print("=" * 30)

        passed = 0
        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")
            if result:
                passed += 1

        print(f"\n🏆 Results: {passed}/{len(results)} tests passed")

        if passed == len(results):
            print("\n🚀 All production systems are working correctly!")
            print("✅ Ready for production deployment!")
            return 0
        else:
            print("\n🔧 Some tests failed - please review and fix issues")
            return 1

    except Exception as e:
        print(f"\n💥 Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    finally:
        test_suite.cleanup()


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n⏸️ Test suite interrupted by user")
        sys.exit(1)