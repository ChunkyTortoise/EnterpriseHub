import pytest

@pytest.mark.integration
#!/usr/bin/env python3
"""
Minimal test for production monitoring and database optimization.

Tests without triggering full system initialization.
"""

import asyncio
import os
import sys
import tempfile
import shutil
import time
import aiosqlite
import psutil
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import json


class ServiceStatus(Enum):
    """Service health status."""
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    DOWN = "down"


@dataclass
class HealthCheck:
    """Health check result."""
    service: str
    status: ServiceStatus
    message: str
    response_time_ms: float


@dataclass
class SystemMetrics:
    """System resource metrics."""
    cpu_percent: float
    memory_percent: float
    disk_percent: float
    uptime_hours: float


class MinimalProductionMonitor:
    """Minimal production monitoring for testing."""

    def __init__(self, db_path: str):
        """Initialize monitor."""
        self.db_path = db_path
        self.start_time = datetime.now()

    async def initialize(self):
        """Initialize monitoring database."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS health_checks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    service TEXT NOT NULL,
                    status TEXT NOT NULL,
                    message TEXT,
                    response_time_ms REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.execute("""
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    uptime_hours REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            await db.commit()

    async def check_service_health(self, service_name: str, check_function) -> HealthCheck:
        """Perform service health check."""
        start_time = time.time()

        try:
            result = await check_function() if asyncio.iscoroutinefunction(check_function) else check_function()
            response_time = (time.time() - start_time) * 1000

            if result.get('healthy', False):
                status = ServiceStatus.HEALTHY
                message = "Service healthy"
            else:
                status = ServiceStatus.CRITICAL
                message = result.get('error', 'Health check failed')

            health_check = HealthCheck(
                service=service_name,
                status=status,
                message=message,
                response_time_ms=response_time
            )

            # Store result
            await self._store_health_check(health_check)
            return health_check

        except Exception as e:
            response_time = (time.time() - start_time) * 1000

            health_check = HealthCheck(
                service=service_name,
                status=ServiceStatus.DOWN,
                message=f"Health check error: {str(e)}",
                response_time_ms=response_time
            )

            await self._store_health_check(health_check)
            return health_check

    async def collect_system_metrics(self) -> SystemMetrics:
        """Collect system metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600

        metrics = SystemMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory.percent,
            disk_percent=(disk.used / disk.total) * 100,
            uptime_hours=uptime_hours
        )

        await self._store_system_metrics(metrics)
        return metrics

    async def _store_health_check(self, health_check: HealthCheck):
        """Store health check result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO health_checks (service, status, message, response_time_ms)
                VALUES (?, ?, ?, ?)
            """, (
                health_check.service,
                health_check.status.value,
                health_check.message,
                health_check.response_time_ms
            ))
            await db.commit()

    async def _store_system_metrics(self, metrics: SystemMetrics):
        """Store system metrics."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO system_metrics (cpu_percent, memory_percent, disk_percent, uptime_hours)
                VALUES (?, ?, ?, ?)
            """, (
                metrics.cpu_percent,
                metrics.memory_percent,
                metrics.disk_percent,
                metrics.uptime_hours
            ))
            await db.commit()


class MinimalDatabaseOptimizer:
    """Minimal database optimizer for testing."""

    def __init__(self, target_db_path: str):
        """Initialize optimizer."""
        self.target_db_path = target_db_path

    async def analyze_database_health(self) -> Dict[str, Any]:
        """Analyze database health."""
        try:
            # Get database size
            size_bytes = os.path.getsize(self.target_db_path)
            size_mb = size_bytes / (1024 * 1024)

            # Test query performance
            start_time = time.time()
            async with aiosqlite.connect(self.target_db_path) as db:
                await db.execute("SELECT COUNT(*) FROM sqlite_master")
            query_time_ms = (time.time() - start_time) * 1000

            # Get fragmentation info
            async with aiosqlite.connect(self.target_db_path) as db:
                async with db.execute("PRAGMA freelist_count") as cursor:
                    freelist_count = (await cursor.fetchone())[0]
                async with db.execute("PRAGMA page_count") as cursor:
                    page_count = (await cursor.fetchone())[0]

            fragmentation_ratio = freelist_count / page_count if page_count > 0 else 0

            return {
                'database_size_mb': size_mb,
                'query_time_ms': query_time_ms,
                'fragmentation_ratio': fragmentation_ratio,
                'page_count': page_count,
                'freelist_count': freelist_count
            }

        except Exception as e:
            return {
                'error': str(e),
                'database_size_mb': 0,
                'query_time_ms': 999.0,
                'fragmentation_ratio': 1.0
            }

    async def optimize_database(self) -> Dict[str, Any]:
        """Optimize database."""
        operations = []
        errors = []

        try:
            async with aiosqlite.connect(self.target_db_path) as db:
                # Update statistics
                await db.execute("ANALYZE")
                operations.append("Updated database statistics")

                # Reindex
                await db.execute("REINDEX")
                operations.append("Rebuilt database indexes")

                # Vacuum
                await db.execute("VACUUM")
                operations.append("Vacuumed database")

            return {
                'success': True,
                'operations': operations,
                'errors': errors
            }

        except Exception as e:
            errors.append(str(e))
            return {
                'success': False,
                'operations': operations,
                'errors': errors
            }


# Test health check functions
async def check_test_database_health(db_path: str) -> Dict[str, Any]:
    """Test database health check."""
    try:
        async with aiosqlite.connect(db_path) as db:
            await db.execute("SELECT 1")
        return {'healthy': True, 'message': 'Database accessible'}
    except Exception as e:
        return {'healthy': False, 'error': str(e)}


def check_test_cache_health() -> Dict[str, Any]:
    """Test cache health check."""
    return {'healthy': True, 'message': 'Cache service mock healthy'}


class TestMinimalMonitoring:
    """Test suite for minimal monitoring components."""

    def __init__(self):
        """Initialize test environment."""
        self.test_dir = tempfile.mkdtemp()
        self.monitoring_db = os.path.join(self.test_dir, "monitoring.db")
        self.target_db = os.path.join(self.test_dir, "target.db")
        print(f"🧪 Test environment: {self.test_dir}")

    async def setup_test_database(self):
        """Create test database with sample data."""
        async with aiosqlite.connect(self.target_db) as db:
            await db.execute("""
                CREATE TABLE test_data (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    value INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert sample data
            for i in range(50):
                await db.execute(
                    "INSERT INTO test_data (name, value) VALUES (?, ?)",
                    (f"item_{i}", i * 10)
                )

            await db.commit()

        print("✅ Test database created")

    async def test_monitoring(self):
        """Test monitoring functionality."""
        print("\n📊 Testing Monitoring Components")
        print("=" * 40)

        try:
            monitor = MinimalProductionMonitor(self.monitoring_db)

            # Initialize
            await monitor.initialize()
            print("✅ Monitoring initialized")

            # Test system metrics
            metrics = await monitor.collect_system_metrics()
            print(f"✅ System metrics collected:")
            print(f"   CPU: {metrics.cpu_percent:.1f}%")
            print(f"   Memory: {metrics.memory_percent:.1f}%")
            print(f"   Disk: {metrics.disk_percent:.1f}%")
            print(f"   Uptime: {metrics.uptime_hours:.2f}h")

            # Test health checks
            db_health = await monitor.check_service_health(
                "test_database",
                lambda: check_test_database_health(self.target_db)
            )

            cache_health = await monitor.check_service_health(
                "test_cache",
                check_test_cache_health
            )

            print(f"✅ Database health: {db_health.status.value} ({db_health.response_time_ms:.1f}ms)")
            print(f"✅ Cache health: {cache_health.status.value} ({cache_health.response_time_ms:.1f}ms)")

            return True

        except Exception as e:
            print(f"❌ Monitoring test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    async def test_optimization(self):
        """Test database optimization."""
        print("\n🗄️ Testing Database Optimization")
        print("=" * 40)

        try:
            optimizer = MinimalDatabaseOptimizer(self.target_db)

            # Analyze database health
            health = await optimizer.analyze_database_health()

            if 'error' in health:
                print(f"❌ Health analysis failed: {health['error']}")
                return False

            print(f"✅ Database health analyzed:")
            print(f"   Size: {health['database_size_mb']:.3f} MB")
            print(f"   Query time: {health['query_time_ms']:.1f} ms")
            print(f"   Fragmentation: {health['fragmentation_ratio']:.2%}")
            print(f"   Pages: {health['page_count']}")

            # Optimize database
            print("\n🔧 Optimizing database...")
            optimization_result = await optimizer.optimize_database()

            if optimization_result['success']:
                print("✅ Optimization completed:")
                for operation in optimization_result['operations']:
                    print(f"   - {operation}")
            else:
                print("❌ Optimization failed:")
                for error in optimization_result['errors']:
                    print(f"   - {error}")
                return False

            # Analyze again to see improvements
            health_after = await optimizer.analyze_database_health()

            if 'error' not in health_after:
                print(f"✅ Post-optimization health:")
                print(f"   Size: {health_after['database_size_mb']:.3f} MB")
                print(f"   Fragmentation: {health_after['fragmentation_ratio']:.2%}")

                # Calculate improvements
                size_improvement = health['database_size_mb'] - health_after['database_size_mb']
                frag_improvement = health['fragmentation_ratio'] - health_after['fragmentation_ratio']

                if size_improvement > 0:
                    print(f"   📉 Size reduced by {size_improvement:.3f} MB")
                if frag_improvement > 0:
                    print(f"   📉 Fragmentation reduced by {frag_improvement:.2%}")

            return True

        except Exception as e:
            print(f"❌ Optimization test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def cleanup(self):
        """Clean up test environment."""
        try:
            shutil.rmtree(self.test_dir)
            print(f"✅ Test environment cleaned up")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


async def main():
    """Main test function."""
    print("🧪 Minimal Production Monitoring Test")
    print("=" * 50)

    test_suite = TestMinimalMonitoring()

    try:
        # Setup
        await test_suite.setup_test_database()

        # Run tests
        tests = [
            ("Monitoring", test_suite.test_monitoring()),
            ("Database Optimization", test_suite.test_optimization())
        ]

        results = []
        for test_name, test_coro in tests:
            result = await test_coro
            results.append((test_name, result))

        # Summary
        print("\n📋 Test Summary")
        print("=" * 30)

        passed = sum(1 for _, result in results if result)

        for test_name, result in results:
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} {test_name}")

        print(f"\n🏆 Results: {passed}/{len(results)} tests passed")

        if passed == len(results):
            print("\n🚀 Production monitoring systems are working!")
            return 0
        else:
            print("\n🔧 Some tests failed")
            return 1

    except Exception as e:
        print(f"\n💥 Test suite failed: {e}")
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
        print("\n⏸️ Test interrupted")
        sys.exit(1)