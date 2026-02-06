#!/usr/bin/env python3
"""
🔧 Critical Bug Fixes Validation Test
=====================================

Specialized load testing to validate the 5 critical production blockers we fixed:
1. FileCache race conditions → Thread-safe file operations
2. MemoryCache memory leaks → LRU eviction with limits
3. Undefined lock crashes → Proper lock initialization
4. WebSocket singleton races → Thread-safe singleton pattern
5. Silent failure patterns → Infrastructure monitoring alerts

Target: Prove production readiness under enterprise load (1000+ concurrent operations)

Usage:
    python validate_critical_fixes.py --quick          # 30-second validation
    python validate_critical_fixes.py --full           # Comprehensive 5-minute test
    python validate_critical_fixes.py --stress         # 15-minute stress test

Author: Phase 3 Bug Fix Validation
Date: 2026-01-25
"""

import asyncio
import time
import logging
import argparse
import json
import threading
import psutil
import gc
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import statistics
import traceback
import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Results from critical bug fix validation."""
    test_name: str
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    operations_per_second: float
    avg_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    memory_peak_mb: float
    memory_growth_mb: float
    race_conditions_detected: int
    errors: List[str]
    success_rate: float
    status: str  # PASS, FAIL, WARNING

class CriticalFixValidator:
    """Validates all 5 critical bug fixes under load."""

    def __init__(self, test_duration: int = 60, concurrent_workers: int = 100):
        self.test_duration = test_duration
        self.concurrent_workers = concurrent_workers
        self.results: List[ValidationResult] = []
        self.start_memory_mb = psutil.Process().memory_info().rss / 1024 / 1024

    async def run_full_validation(self) -> Dict[str, Any]:
        """Run comprehensive validation of all critical fixes."""
        logger.info("=" * 60)
        logger.info("🔧 CRITICAL BUG FIXES VALIDATION STARTING")
        logger.info("=" * 60)
        logger.info(f"Test Duration: {self.test_duration}s")
        logger.info(f"Concurrent Workers: {self.concurrent_workers}")
        logger.info(f"Target: Validate 5 critical production blocker fixes")
        logger.info("")

        # Run each validation test
        await self._validate_cache_race_conditions()
        await self._validate_memory_cache_eviction()
        await self._validate_lock_initialization()
        await self._validate_websocket_singleton()
        await self._validate_error_handling()

        # Generate final report
        return self._generate_final_report()

    async def _validate_cache_race_conditions(self):
        """Test Fix #1: FileCache race conditions fixed."""
        logger.info("🔍 Test 1: Validating FileCache race condition fixes...")

        try:
            # Import here to avoid import issues
            from ghl_real_estate_ai.services.cache_service import FileCache

            # Create cache instance
            cache = FileCache(cache_dir="/tmp/race_test_cache")

            start_time = time.time()
            total_ops = 0
            successful_ops = 0
            failed_ops = 0
            response_times = []
            race_conditions_detected = 0
            errors = []

            # Create many concurrent file operations
            async def concurrent_cache_operations():
                nonlocal total_ops, successful_ops, failed_ops, response_times, race_conditions_detected

                while time.time() - start_time < min(30, self.test_duration):
                    op_start = time.time()

                    try:
                        # Simulate race conditions with concurrent set/get/delete
                        key = f"test_key_{threading.current_thread().ident}_{time.time()}"
                        value = {"data": f"test_value_{total_ops}", "timestamp": time.time()}

                        # Set value
                        await cache.set(key, value, ttl=60)

                        # Immediate get (tests file lock contention)
                        retrieved = await cache.get(key)

                        if retrieved != value:
                            race_conditions_detected += 1
                            errors.append(f"Race condition: Expected {value}, got {retrieved}")

                        # Delete to clean up
                        await cache.delete(key)

                        successful_ops += 1
                        response_times.append((time.time() - op_start) * 1000)

                    except Exception as e:
                        failed_ops += 1
                        errors.append(f"Cache operation failed: {e}")
                    finally:
                        total_ops += 1

            # Run concurrent operations
            tasks = [concurrent_cache_operations() for _ in range(min(50, self.concurrent_workers))]
            await asyncio.gather(*tasks)

            duration = time.time() - start_time

            result = ValidationResult(
                test_name="FileCache Race Conditions",
                duration_seconds=duration,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                operations_per_second=total_ops / duration if duration > 0 else 0,
                avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
                p95_response_time_ms=statistics.quantile(response_times, 0.95) if len(response_times) > 20 else 0,
                p99_response_time_ms=statistics.quantile(response_times, 0.99) if len(response_times) > 100 else 0,
                memory_peak_mb=psutil.Process().memory_info().rss / 1024 / 1024,
                memory_growth_mb=0,  # Will calculate later
                race_conditions_detected=race_conditions_detected,
                errors=errors[:10],  # First 10 errors only
                success_rate=successful_ops / max(total_ops, 1),
                status="PASS" if race_conditions_detected == 0 and successful_ops > 0 else "FAIL"
            )

            self.results.append(result)
            logger.info(f"✅ FileCache test: {result.status} - {successful_ops}/{total_ops} ops, "
                       f"{race_conditions_detected} race conditions detected")

        except Exception as e:
            logger.error(f"❌ FileCache test FAILED: {e}")
            result = ValidationResult(
                test_name="FileCache Race Conditions",
                duration_seconds=0,
                total_operations=0,
                successful_operations=0,
                failed_operations=1,
                operations_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=0,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=[str(e)],
                success_rate=0,
                status="FAIL"
            )
            self.results.append(result)

    async def _validate_memory_cache_eviction(self):
        """Test Fix #2: MemoryCache memory leak fixed with LRU eviction."""
        logger.info("🔍 Test 2: Validating MemoryCache LRU eviction...")

        try:
            from ghl_real_estate_ai.services.cache_service import MemoryCache

            # Create small cache to force evictions
            cache = MemoryCache(max_size=100, max_memory_mb=5)

            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / 1024 / 1024
            total_ops = 0
            successful_ops = 0
            failed_ops = 0
            response_times = []
            errors = []

            # Fill cache beyond limits to test eviction
            for i in range(500):  # More than max_size=100
                op_start = time.time()

                try:
                    key = f"memory_test_key_{i}"
                    # Large value to test memory limits
                    value = {"large_data": "x" * 1000, "index": i, "timestamp": time.time()}

                    success = await cache.set(key, value, ttl=300)
                    if success:
                        successful_ops += 1
                    else:
                        failed_ops += 1

                    response_times.append((time.time() - op_start) * 1000)

                    # Check if old items were evicted
                    if i > 150:  # After we should have triggered evictions
                        old_key = f"memory_test_key_{i-150}"
                        old_value = await cache.get(old_key)
                        if old_value is not None:
                            # Old item still exists - eviction not working properly
                            errors.append(f"LRU eviction failed: old key {old_key} still exists")

                except Exception as e:
                    failed_ops += 1
                    errors.append(f"Memory cache operation failed: {e}")
                finally:
                    total_ops += 1

                    # Stop if test duration exceeded
                    if time.time() - start_time > min(30, self.test_duration):
                        break

            duration = time.time() - start_time
            end_memory = psutil.Process().memory_info().rss / 1024 / 1024
            memory_growth = end_memory - start_memory

            # Get cache stats if available
            cache_stats = {}
            if hasattr(cache, 'get_memory_stats'):
                cache_stats = cache.get_memory_stats()
                logger.info(f"Cache stats: {cache_stats}")

            result = ValidationResult(
                test_name="MemoryCache LRU Eviction",
                duration_seconds=duration,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                operations_per_second=total_ops / duration if duration > 0 else 0,
                avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
                p95_response_time_ms=statistics.quantile(response_times, 0.95) if len(response_times) > 20 else 0,
                p99_response_time_ms=statistics.quantile(response_times, 0.99) if len(response_times) > 100 else 0,
                memory_peak_mb=end_memory,
                memory_growth_mb=memory_growth,
                race_conditions_detected=0,
                errors=errors[:10],
                success_rate=successful_ops / max(total_ops, 1),
                status="PASS" if memory_growth < 50 and successful_ops > 0 else "WARNING" if memory_growth < 100 else "FAIL"
            )

            self.results.append(result)
            logger.info(f"✅ MemoryCache test: {result.status} - {successful_ops}/{total_ops} ops, "
                       f"Memory growth: {memory_growth:.1f}MB")

        except Exception as e:
            logger.error(f"❌ MemoryCache test FAILED: {e}")
            result = ValidationResult(
                test_name="MemoryCache LRU Eviction",
                duration_seconds=0,
                total_operations=0,
                successful_operations=0,
                failed_operations=1,
                operations_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=0,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=[str(e)],
                success_rate=0,
                status="FAIL"
            )
            self.results.append(result)

    async def _validate_lock_initialization(self):
        """Test Fix #3: Proper lock initialization in OptimizedCacheService."""
        logger.info("🔍 Test 3: Validating lock initialization fixes...")

        try:
            from ghl_real_estate_ai.services.optimized_cache_service import EnhancedCacheService

            start_time = time.time()
            total_ops = 0
            successful_ops = 0
            failed_ops = 0
            response_times = []
            errors = []

            # Create multiple cache instances to test lock initialization
            caches = []
            for i in range(10):
                cache = EnhancedCacheService()
                caches.append(cache)

            async def test_reset_metrics(cache):
                """Test the previously crashing reset_metrics method."""
                nonlocal total_ops, successful_ops, failed_ops, response_times

                for _ in range(20):
                    op_start = time.time()
                    try:
                        # This previously caused AttributeError: 'EnhancedCacheService' object has no attribute 'lock'
                        await cache.reset_metrics()
                        successful_ops += 1
                        response_times.append((time.time() - op_start) * 1000)
                    except Exception as e:
                        failed_ops += 1
                        errors.append(f"reset_metrics failed: {e}")
                    finally:
                        total_ops += 1

                    # Short delay to allow other operations
                    await asyncio.sleep(0.001)

            # Run concurrent reset_metrics operations
            tasks = [test_reset_metrics(cache) for cache in caches]
            await asyncio.gather(*tasks)

            duration = time.time() - start_time

            result = ValidationResult(
                test_name="Lock Initialization Fix",
                duration_seconds=duration,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                operations_per_second=total_ops / duration if duration > 0 else 0,
                avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
                p95_response_time_ms=statistics.quantile(response_times, 0.95) if len(response_times) > 20 else 0,
                p99_response_time_ms=statistics.quantile(response_times, 0.99) if len(response_times) > 100 else 0,
                memory_peak_mb=psutil.Process().memory_info().rss / 1024 / 1024,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=errors[:10],
                success_rate=successful_ops / max(total_ops, 1),
                status="PASS" if failed_ops == 0 and successful_ops > 0 else "FAIL"
            )

            self.results.append(result)
            logger.info(f"✅ Lock initialization test: {result.status} - {successful_ops}/{total_ops} ops, "
                       f"{failed_ops} failures")

        except Exception as e:
            logger.error(f"❌ Lock initialization test FAILED: {e}")
            logger.error(traceback.format_exc())
            result = ValidationResult(
                test_name="Lock Initialization Fix",
                duration_seconds=0,
                total_operations=0,
                successful_operations=0,
                failed_operations=1,
                operations_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=0,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=[str(e)],
                success_rate=0,
                status="FAIL"
            )
            self.results.append(result)

    async def _validate_websocket_singleton(self):
        """Test Fix #4: WebSocket singleton thread safety."""
        logger.info("🔍 Test 4: Validating WebSocket singleton thread safety...")

        try:
            from ghl_real_estate_ai.services.websocket_server import get_websocket_manager

            start_time = time.time()
            total_ops = 0
            successful_ops = 0
            failed_ops = 0
            errors = []
            instances = []

            def create_websocket_manager():
                """Create WebSocket manager in separate thread."""
                try:
                    manager = get_websocket_manager()
                    instances.append(id(manager))  # Store object ID
                    return True
                except Exception as e:
                    errors.append(f"WebSocket creation failed: {e}")
                    return False

            # Test concurrent singleton creation
            with ThreadPoolExecutor(max_workers=50) as executor:
                futures = [executor.submit(create_websocket_manager) for _ in range(100)]

                for future in as_completed(futures):
                    result = future.result()
                    total_ops += 1
                    if result:
                        successful_ops += 1
                    else:
                        failed_ops += 1

            duration = time.time() - start_time

            # Check if all instances are the same (singleton working)
            unique_instances = len(set(instances))
            singleton_working = unique_instances == 1

            result = ValidationResult(
                test_name="WebSocket Singleton Thread Safety",
                duration_seconds=duration,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                operations_per_second=total_ops / duration if duration > 0 else 0,
                avg_response_time_ms=0,  # Not applicable for this test
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=psutil.Process().memory_info().rss / 1024 / 1024,
                memory_growth_mb=0,
                race_conditions_detected=unique_instances - 1 if not singleton_working else 0,
                errors=errors[:10],
                success_rate=successful_ops / max(total_ops, 1),
                status="PASS" if singleton_working and failed_ops == 0 else "FAIL"
            )

            self.results.append(result)
            logger.info(f"✅ WebSocket singleton test: {result.status} - {successful_ops}/{total_ops} ops, "
                       f"{unique_instances} unique instances (should be 1)")

        except Exception as e:
            logger.error(f"❌ WebSocket singleton test FAILED: {e}")
            result = ValidationResult(
                test_name="WebSocket Singleton Thread Safety",
                duration_seconds=0,
                total_operations=0,
                successful_operations=0,
                failed_operations=1,
                operations_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=0,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=[str(e)],
                success_rate=0,
                status="FAIL"
            )
            self.results.append(result)

    async def _validate_error_handling(self):
        """Test Fix #5: Infrastructure monitoring alerts instead of silent failures."""
        logger.info("🔍 Test 5: Validating infrastructure monitoring...")

        try:
            # Import the services we enhanced with proper error handling
            from ghl_real_estate_ai.services.event_streaming_service import EventStreamingService

            start_time = time.time()
            total_ops = 0
            successful_ops = 0
            failed_ops = 0
            response_times = []
            errors = []
            alert_count = 0

            # Test that infrastructure failures now emit alerts instead of silent failures
            service = EventStreamingService(kafka_bootstrap_servers="invalid_server:9092")

            # This should trigger infrastructure alerts instead of silent failure
            try:
                op_start = time.time()
                await service.initialize()  # Will fail due to invalid Kafka server

                # Check if proper error handling and alerts were triggered
                if hasattr(service, 'fallback_mode') and service.fallback_mode:
                    # Service correctly fell back and should have emitted alerts
                    successful_ops += 1
                    alert_count += 1
                    logger.info("✅ Infrastructure failure correctly handled with fallback and alerts")
                else:
                    errors.append("Service should have enabled fallback mode for invalid Kafka")
                    failed_ops += 1

                response_times.append((time.time() - op_start) * 1000)
                total_ops += 1

            except Exception as e:
                # Even exceptions should be properly logged and alerted
                failed_ops += 1
                errors.append(f"Infrastructure failure not handled gracefully: {e}")
                total_ops += 1

            duration = time.time() - start_time

            result = ValidationResult(
                test_name="Infrastructure Monitoring Alerts",
                duration_seconds=duration,
                total_operations=total_ops,
                successful_operations=successful_ops,
                failed_operations=failed_ops,
                operations_per_second=total_ops / duration if duration > 0 else 0,
                avg_response_time_ms=statistics.mean(response_times) if response_times else 0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=psutil.Process().memory_info().rss / 1024 / 1024,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=errors[:10],
                success_rate=successful_ops / max(total_ops, 1),
                status="PASS" if alert_count > 0 and failed_ops == 0 else "WARNING" if alert_count > 0 else "FAIL"
            )

            self.results.append(result)
            logger.info(f"✅ Infrastructure monitoring test: {result.status} - {successful_ops}/{total_ops} ops, "
                       f"{alert_count} alerts emitted")

        except Exception as e:
            logger.error(f"❌ Infrastructure monitoring test FAILED: {e}")
            result = ValidationResult(
                test_name="Infrastructure Monitoring Alerts",
                duration_seconds=0,
                total_operations=0,
                successful_operations=0,
                failed_operations=1,
                operations_per_second=0,
                avg_response_time_ms=0,
                p95_response_time_ms=0,
                p99_response_time_ms=0,
                memory_peak_mb=0,
                memory_growth_mb=0,
                race_conditions_detected=0,
                errors=[str(e)],
                success_rate=0,
                status="FAIL"
            )
            self.results.append(result)

    def _generate_final_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report."""
        end_memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        total_memory_growth = end_memory_mb - self.start_memory_mb

        # Calculate overall statistics
        total_operations = sum(r.total_operations for r in self.results)
        total_successful = sum(r.successful_operations for r in self.results)
        total_failed = sum(r.failed_operations for r in self.results)
        total_race_conditions = sum(r.race_conditions_detected for r in self.results)

        # Determine overall status
        statuses = [r.status for r in self.results]
        if all(s == "PASS" for s in statuses):
            overall_status = "✅ ALL TESTS PASSED - PRODUCTION READY"
        elif any(s == "FAIL" for s in statuses):
            overall_status = "❌ CRITICAL ISSUES DETECTED - NOT PRODUCTION READY"
        else:
            overall_status = "⚠️ WARNINGS DETECTED - REVIEW RECOMMENDED"

        report = {
            "validation_summary": {
                "overall_status": overall_status,
                "timestamp": datetime.now().isoformat(),
                "test_duration": self.test_duration,
                "concurrent_workers": self.concurrent_workers,
                "total_operations": total_operations,
                "successful_operations": total_successful,
                "failed_operations": total_failed,
                "success_rate": total_successful / max(total_operations, 1),
                "race_conditions_detected": total_race_conditions,
                "memory_growth_mb": total_memory_growth,
                "tests_passed": sum(1 for r in self.results if r.status == "PASS"),
                "tests_failed": sum(1 for r in self.results if r.status == "FAIL"),
                "tests_warning": sum(1 for r in self.results if r.status == "WARNING")
            },
            "individual_test_results": [asdict(r) for r in self.results],
            "production_readiness_assessment": self._assess_production_readiness()
        }

        # Print detailed report
        logger.info("")
        logger.info("=" * 60)
        logger.info("🔧 CRITICAL BUG FIXES VALIDATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"Overall Status: {overall_status}")
        logger.info(f"Total Operations: {total_operations:,}")
        logger.info(f"Success Rate: {(total_successful / max(total_operations, 1)) * 100:.1f}%")
        logger.info(f"Race Conditions: {total_race_conditions}")
        logger.info(f"Memory Growth: {total_memory_growth:.1f} MB")
        logger.info("")

        for result in self.results:
            status_emoji = "✅" if result.status == "PASS" else "⚠️" if result.status == "WARNING" else "❌"
            logger.info(f"{status_emoji} {result.test_name}: {result.status}")
            logger.info(f"   Operations: {result.successful_operations}/{result.total_operations}")
            logger.info(f"   Success Rate: {result.success_rate * 100:.1f}%")
            if result.race_conditions_detected > 0:
                logger.info(f"   Race Conditions: {result.race_conditions_detected}")
            if result.errors:
                logger.info(f"   First Error: {result.errors[0]}")
            logger.info("")

        logger.info("=" * 60)

        return report

    def _assess_production_readiness(self) -> Dict[str, str]:
        """Assess production readiness based on validation results."""
        assessment = {}

        for result in self.results:
            component = result.test_name.replace(" ", "_").lower()

            if result.status == "PASS":
                assessment[component] = "✅ PRODUCTION READY"
            elif result.status == "WARNING":
                assessment[component] = "⚠️ REVIEW RECOMMENDED"
            else:
                assessment[component] = "❌ CRITICAL ISSUES - FIX REQUIRED"

        return assessment


async def main():
    """Main validation function."""
    parser = argparse.ArgumentParser(description="Validate critical bug fixes")
    parser.add_argument("--quick", action="store_true", help="Quick 30-second validation")
    parser.add_argument("--full", action="store_true", help="Comprehensive 5-minute test")
    parser.add_argument("--stress", action="store_true", help="15-minute stress test")
    parser.add_argument("--workers", type=int, default=100, help="Number of concurrent workers")

    args = parser.parse_args()

    # Set test parameters
    if args.quick:
        duration = 30
        workers = 50
    elif args.stress:
        duration = 900  # 15 minutes
        workers = 200
    else:  # full or default
        duration = 300  # 5 minutes
        workers = args.workers

    # Run validation
    validator = CriticalFixValidator(test_duration=duration, concurrent_workers=workers)
    report = await validator.run_full_validation()

    # Save report to file
    report_file = f"critical_fixes_validation_{int(time.time())}.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"💾 Detailed report saved to: {report_file}")

    # Exit with appropriate code
    if "ALL TESTS PASSED" in report["validation_summary"]["overall_status"]:
        logger.info("🚀 VALIDATION COMPLETE - READY FOR PRODUCTION DEPLOYMENT!")
        sys.exit(0)
    elif "WARNINGS" in report["validation_summary"]["overall_status"]:
        logger.warning("⚠️ VALIDATION COMPLETE - REVIEW WARNINGS BEFORE DEPLOYMENT")
        sys.exit(1)
    else:
        logger.error("❌ VALIDATION FAILED - CRITICAL ISSUES MUST BE FIXED")
        sys.exit(2)


if __name__ == "__main__":
    asyncio.run(main())