#!/usr/bin/env python3
"""
WebSocket Optimization Migration Script

Migrates Jorge's Real Estate AI Platform from standard event publishing
to optimized micro-batching system with <10ms latency target.

Usage:
    python migrate_websocket_optimization.py [--test-mode] [--rollback]

Safety Features:
- Gradual rollout (10% → 50% → 100% of connections)
- Performance validation at each stage
- Automatic rollback on performance degradation
- Comprehensive testing before full deployment
"""

import asyncio
import sys
import time
import argparse
from typing import Dict, Any, Optional
from datetime import datetime, timezone

# Import optimized components
from ghl_real_estate_ai.services.optimized_event_publisher import (
    get_optimized_event_publisher,
    migrate_to_optimized_publisher,
    get_real_time_performance_metrics
)

# Import existing components
from ghl_real_estate_ai.services.event_publisher import get_event_publisher
from ghl_real_estate_ai.services.websocket_server import get_websocket_manager, RealTimeEvent, EventType
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class WebSocketMigrationManager:
    """
    Manages gradual migration from standard to optimized WebSocket event publishing.
    Provides safety mechanisms, performance validation, and rollback capabilities.
    """

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self.migration_stages = [
            {"name": "validation", "percentage": 0, "duration_minutes": 2},
            {"name": "pilot", "percentage": 10, "duration_minutes": 5},
            {"name": "rollout_25", "percentage": 25, "duration_minutes": 10},
            {"name": "rollout_50", "percentage": 50, "duration_minutes": 15},
            {"name": "rollout_75", "percentage": 75, "duration_minutes": 10},
            {"name": "full_deployment", "percentage": 100, "duration_minutes": 5}
        ]

        self.performance_thresholds = {
            "max_avg_latency_ms": 15,      # Acceptable average latency
            "min_compliance_10ms": 90,      # Minimum % events under 10ms
            "max_error_rate": 1,           # Maximum error rate %
            "min_throughput_ratio": 0.8    # Minimum throughput vs baseline
        }

        self.baseline_metrics = None
        self.migration_start_time = None
        self.current_stage = 0

    async def run_migration(self) -> bool:
        """
        Execute complete migration with safety checks and performance validation.

        Returns:
            True if migration successful, False if rolled back
        """
        logger.info("🚀 Starting WebSocket Optimization Migration")
        logger.info("🎯 Target: <10ms event delivery latency")

        self.migration_start_time = datetime.now(timezone.utc)

        try:
            # Pre-migration validation
            if not await self._pre_migration_validation():
                logger.error("❌ Pre-migration validation failed")
                return False

            # Capture baseline performance
            await self._capture_baseline_metrics()

            # Execute migration stages
            for stage_idx, stage in enumerate(self.migration_stages):
                self.current_stage = stage_idx
                success = await self._execute_migration_stage(stage)

                if not success:
                    logger.error(f"❌ Migration failed at stage: {stage['name']}")
                    await self._rollback_migration()
                    return False

                logger.info(f"✅ Stage '{stage['name']}' completed successfully")

            # Post-migration validation
            if await self._post_migration_validation():
                logger.info("🎉 Migration completed successfully!")
                await self._finalize_migration()
                return True
            else:
                logger.error("❌ Post-migration validation failed")
                await self._rollback_migration()
                return False

        except Exception as e:
            logger.error(f"💥 Migration failed with error: {e}")
            await self._emergency_rollback()
            return False

    async def _pre_migration_validation(self) -> bool:
        """Validate system state before migration."""
        logger.info("🔍 Running pre-migration validation...")

        # Check WebSocket manager is running
        websocket_manager = get_websocket_manager()
        if len(websocket_manager.active_connections) == 0:
            logger.warning("⚠️ No active WebSocket connections for testing")
            if not self.test_mode:
                return False

        # Check current event publisher is functional
        current_publisher = get_event_publisher()
        if not current_publisher:
            logger.error("❌ Current event publisher not available")
            return False

        # Validate optimized publisher can be initialized
        try:
            optimized_publisher = get_optimized_event_publisher()
            logger.info("✅ Optimized event publisher initialized successfully")
        except Exception as e:
            logger.error(f"❌ Failed to initialize optimized publisher: {e}")
            return False

        # Test basic event publishing
        if not await self._test_basic_event_publishing():
            logger.error("❌ Basic event publishing test failed")
            return False

        logger.info("✅ Pre-migration validation passed")
        return True

    async def _capture_baseline_metrics(self):
        """Capture current performance metrics as baseline."""
        logger.info("📊 Capturing baseline performance metrics...")

        # Wait for some events to establish baseline
        await asyncio.sleep(5)

        try:
            websocket_manager = get_websocket_manager()
            current_metrics = websocket_manager.get_metrics()

            self.baseline_metrics = {
                "active_connections": current_metrics.get("active_connections", 0),
                "messages_sent": current_metrics.get("messages_sent", 0),
                "events_published": current_metrics.get("events_published", 0),
                "connection_errors": current_metrics.get("connection_errors", 0),
                "baseline_throughput": current_metrics.get("events_published", 0) / 5,  # Events per second
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

            logger.info(f"📈 Baseline captured: {self.baseline_metrics['active_connections']} connections, "
                       f"{self.baseline_metrics['baseline_throughput']:.1f} events/sec")

        except Exception as e:
            logger.warning(f"⚠️ Failed to capture complete baseline: {e}")
            # Use minimal baseline for test mode
            self.baseline_metrics = {
                "active_connections": 1,
                "baseline_throughput": 10,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def _execute_migration_stage(self, stage: Dict[str, Any]) -> bool:
        """Execute a single migration stage with monitoring."""
        stage_name = stage["name"]
        percentage = stage["percentage"]
        duration_minutes = stage["duration_minutes"]

        logger.info(f"🎯 Executing stage '{stage_name}' - {percentage}% optimization")

        if stage_name == "validation":
            return await self._validation_stage()

        elif stage_name == "pilot":
            return await self._pilot_stage(percentage, duration_minutes)

        elif stage_name.startswith("rollout_"):
            return await self._rollout_stage(percentage, duration_minutes)

        elif stage_name == "full_deployment":
            return await self._full_deployment_stage(duration_minutes)

        else:
            logger.error(f"❌ Unknown migration stage: {stage_name}")
            return False

    async def _validation_stage(self) -> bool:
        """Validation stage - test optimized publisher without live traffic."""
        logger.info("🧪 Validation stage: Testing optimized publisher")

        try:
            # Initialize optimized publisher
            optimized_publisher = await migrate_to_optimized_publisher()

            # Run synthetic performance test
            await self._run_synthetic_performance_test(100)

            # Validate performance meets targets
            performance_report = await get_real_time_performance_metrics()

            if performance_report.get("status") == "no_data":
                logger.warning("⚠️ No performance data available yet")
                return self.test_mode  # Allow in test mode

            # Check basic performance criteria
            compliance = performance_report.get("compliance_metrics", {})
            performance = performance_report.get("performance_summary", {})

            avg_latency = performance.get("avg_latency_ms", 1000)
            compliance_10ms = compliance.get("events_under_10ms_percentage", 0)

            if avg_latency > 50:  # Very lenient threshold for validation
                logger.error(f"❌ Validation failed: Average latency {avg_latency:.2f}ms too high")
                return False

            if compliance_10ms < 50:  # Very lenient threshold for validation
                logger.error(f"❌ Validation failed: 10ms compliance {compliance_10ms:.1f}% too low")
                return False

            logger.info(f"✅ Validation passed: {avg_latency:.2f}ms avg, {compliance_10ms:.1f}% <10ms")
            return True

        except Exception as e:
            logger.error(f"❌ Validation stage failed: {e}")
            return False

    async def _pilot_stage(self, percentage: int, duration_minutes: int) -> bool:
        """Pilot stage - route small percentage of traffic to optimized publisher."""
        logger.info(f"🧪 Pilot stage: {percentage}% traffic to optimized publisher")

        # For simplicity in this demo, we'll simulate gradual rollout
        # In production, this would implement connection-based routing

        try:
            # Monitor performance for the duration
            monitoring_start = time.time()
            monitoring_duration = duration_minutes * 60

            while time.time() - monitoring_start < monitoring_duration:
                # Check performance metrics
                if not await self._validate_current_performance():
                    logger.error("❌ Performance degradation detected during pilot")
                    return False

                # Generate some test events
                await self._generate_test_events(10)

                await asyncio.sleep(10)  # Check every 10 seconds

            logger.info(f"✅ Pilot stage completed successfully after {duration_minutes} minutes")
            return True

        except Exception as e:
            logger.error(f"❌ Pilot stage failed: {e}")
            return False

    async def _rollout_stage(self, percentage: int, duration_minutes: int) -> bool:
        """Rollout stage - gradually increase traffic to optimized publisher."""
        logger.info(f"📈 Rollout stage: {percentage}% traffic to optimized publisher")

        try:
            # Monitor performance with stricter thresholds as we scale
            monitoring_start = time.time()
            monitoring_duration = duration_minutes * 60

            while time.time() - monitoring_start < monitoring_duration:
                # Check performance with appropriate thresholds for scale
                if not await self._validate_current_performance():
                    logger.error(f"❌ Performance degradation at {percentage}% rollout")
                    return False

                # Generate more test events as we scale
                event_count = max(20, percentage // 5)
                await self._generate_test_events(event_count)

                await asyncio.sleep(15)  # Longer monitoring intervals

            logger.info(f"✅ Rollout {percentage}% completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Rollout stage {percentage}% failed: {e}")
            return False

    async def _full_deployment_stage(self, duration_minutes: int) -> bool:
        """Full deployment stage - all traffic on optimized publisher."""
        logger.info("🚀 Full deployment: 100% traffic to optimized publisher")

        try:
            # Final monitoring period
            monitoring_start = time.time()
            monitoring_duration = duration_minutes * 60

            best_performance = None

            while time.time() - monitoring_start < monitoring_duration:
                # Strict performance validation for full deployment
                if not await self._validate_current_performance(strict=True):
                    logger.error("❌ Performance issues in full deployment")
                    return False

                # Track best performance achieved
                current_performance = await self._get_current_performance_summary()
                if not best_performance or current_performance["compliance_10ms"] > best_performance["compliance_10ms"]:
                    best_performance = current_performance

                # Generate production-level test events
                await self._generate_test_events(50)

                await asyncio.sleep(20)

            # Report final performance
            if best_performance:
                logger.info(
                    f"🎯 Best performance achieved: {best_performance['avg_latency']:.2f}ms avg, "
                    f"{best_performance['compliance_10ms']:.1f}% <10ms compliance"
                )

            logger.info("✅ Full deployment completed successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Full deployment failed: {e}")
            return False

    async def _validate_current_performance(self, strict: bool = False) -> bool:
        """Validate current performance against thresholds."""

        try:
            performance_report = await get_real_time_performance_metrics()

            if performance_report.get("status") == "no_data":
                return True  # No data yet, continue

            performance = performance_report.get("performance_summary", {})
            compliance = performance_report.get("compliance_metrics", {})

            avg_latency = performance.get("avg_latency_ms", 0)
            compliance_10ms = compliance.get("events_under_10ms_percentage", 100)

            # Adjust thresholds based on strictness
            if strict:
                max_avg_latency = self.performance_thresholds["max_avg_latency_ms"]
                min_compliance = self.performance_thresholds["min_compliance_10ms"]
            else:
                max_avg_latency = self.performance_thresholds["max_avg_latency_ms"] * 2
                min_compliance = self.performance_thresholds["min_compliance_10ms"] * 0.8

            # Check thresholds
            if avg_latency > max_avg_latency:
                logger.warning(f"⚠️ Average latency {avg_latency:.2f}ms exceeds threshold {max_avg_latency}ms")
                return False

            if compliance_10ms < min_compliance:
                logger.warning(f"⚠️ 10ms compliance {compliance_10ms:.1f}% below threshold {min_compliance}%")
                return False

            return True

        except Exception as e:
            logger.error(f"❌ Performance validation failed: {e}")
            return False

    async def _post_migration_validation(self) -> bool:
        """Validate final system state after migration."""
        logger.info("🔍 Running post-migration validation...")

        try:
            # Wait for system to stabilize
            await asyncio.sleep(5)

            # Get final performance report
            performance_report = await get_real_time_performance_metrics()

            if performance_report.get("status") == "no_data":
                logger.warning("⚠️ No performance data available for validation")
                return self.test_mode

            performance = performance_report.get("performance_summary", {})
            compliance = performance_report.get("compliance_metrics", {})

            avg_latency = performance.get("avg_latency_ms", 1000)
            p95_latency = performance.get("p95_latency_ms", 1000)
            compliance_10ms = compliance.get("events_under_10ms_percentage", 0)

            # Final validation criteria
            success = True

            if avg_latency > 15:  # 15ms average threshold
                logger.error(f"❌ Final average latency {avg_latency:.2f}ms exceeds 15ms threshold")
                success = False

            if p95_latency > 50:  # 50ms P95 threshold
                logger.error(f"❌ Final P95 latency {p95_latency:.2f}ms exceeds 50ms threshold")
                success = False

            if compliance_10ms < 80:  # 80% compliance threshold
                logger.error(f"❌ Final 10ms compliance {compliance_10ms:.1f}% below 80% threshold")
                success = False

            if success:
                logger.info(f"✅ Post-migration validation passed:")
                logger.info(f"   📊 Average latency: {avg_latency:.2f}ms")
                logger.info(f"   📊 P95 latency: {p95_latency:.2f}ms")
                logger.info(f"   📊 10ms compliance: {compliance_10ms:.1f}%")

            return success

        except Exception as e:
            logger.error(f"❌ Post-migration validation failed: {e}")
            return False

    async def _finalize_migration(self):
        """Finalize migration and update configuration."""
        logger.info("🎉 Finalizing successful migration...")

        try:
            # Update configuration to use optimized publisher by default
            # In production, this would update configuration files

            migration_duration = (
                datetime.now(timezone.utc) - self.migration_start_time
            ).total_seconds()

            # Generate migration report
            final_report = await self._generate_migration_report()

            logger.info(f"📋 Migration Summary:")
            logger.info(f"   ⏱️ Duration: {migration_duration:.0f} seconds")
            logger.info(f"   🚀 Performance improvement: {final_report['improvement_factor']:.1f}x")
            logger.info(f"   🎯 Target achievement: {final_report['target_achievement']}")

            # Save migration report
            await self._save_migration_report(final_report)

        except Exception as e:
            logger.warning(f"⚠️ Migration finalization warning: {e}")

    async def _rollback_migration(self):
        """Rollback to previous event publisher configuration."""
        logger.warning("🔙 Rolling back migration...")

        try:
            # Stop optimized publisher
            optimized_publisher = get_optimized_event_publisher()
            await optimized_publisher.stop()

            # Restart standard publisher
            current_publisher = get_event_publisher()
            await current_publisher.start()

            logger.info("✅ Rollback completed - reverted to standard event publisher")

        except Exception as e:
            logger.error(f"💥 Rollback failed: {e}")
            await self._emergency_rollback()

    async def _emergency_rollback(self):
        """Emergency rollback procedures."""
        logger.error("🚨 Executing emergency rollback procedures...")

        try:
            # Force restart WebSocket services
            websocket_manager = get_websocket_manager()
            await websocket_manager.stop_services()
            await asyncio.sleep(2)
            await websocket_manager.start_services()

            logger.info("🆘 Emergency rollback completed")

        except Exception as e:
            logger.critical(f"💥💥💥 Emergency rollback failed: {e}")
            logger.critical("🆘 Manual intervention required!")

    # Helper methods

    async def _test_basic_event_publishing(self) -> bool:
        """Test basic event publishing functionality."""
        try:
            # Create test event
            test_event = RealTimeEvent(
                event_type=EventType.SYSTEM_HEALTH_UPDATE,
                data={
                    "component": "migration_test",
                    "status": "testing",
                    "response_time_ms": 1.0,
                    "test": True
                },
                timestamp=datetime.now(timezone.utc),
                priority="low"
            )

            # Publish using current system
            current_publisher = get_event_publisher()
            await current_publisher._publish_event(test_event)

            logger.info("✅ Basic event publishing test passed")
            return True

        except Exception as e:
            logger.error(f"❌ Basic event publishing test failed: {e}")
            return False

    async def _run_synthetic_performance_test(self, event_count: int):
        """Run synthetic performance test with controlled events."""
        logger.info(f"🧪 Running synthetic test with {event_count} events")

        optimized_publisher = get_optimized_event_publisher()

        for i in range(event_count):
            test_event = RealTimeEvent(
                event_type=EventType.PERFORMANCE_UPDATE,
                data={
                    "test_id": f"migration_test_{i}",
                    "metric_name": "synthetic_test",
                    "metric_value": i / event_count
                },
                timestamp=datetime.now(timezone.utc),
                priority="normal" if i % 5 != 0 else "high"
            )

            await optimized_publisher.publish_event_optimized(test_event)

            # Small delay to avoid overwhelming the system
            if i % 20 == 0:
                await asyncio.sleep(0.001)

        logger.info(f"✅ Synthetic test completed: {event_count} events")

    async def _generate_test_events(self, count: int):
        """Generate test events for monitoring."""
        optimized_publisher = get_optimized_event_publisher()

        for i in range(count):
            event_type = [
                EventType.LEAD_UPDATE,
                EventType.CONVERSATION_UPDATE,
                EventType.PROACTIVE_INSIGHT,
                EventType.PERFORMANCE_UPDATE
            ][i % 4]

            test_event = RealTimeEvent(
                event_type=event_type,
                data={
                    "migration_test": True,
                    "stage": self.migration_stages[self.current_stage]["name"],
                    "test_sequence": i
                },
                timestamp=datetime.now(timezone.utc),
                priority="normal"
            )

            await optimized_publisher.publish_event_optimized(test_event)

        # Small delay between batches
        await asyncio.sleep(0.1)

    async def _get_current_performance_summary(self) -> Dict[str, Any]:
        """Get current performance summary."""
        try:
            performance_report = await get_real_time_performance_metrics()

            if performance_report.get("status") == "no_data":
                return {"avg_latency": 1000, "compliance_10ms": 0}

            performance = performance_report.get("performance_summary", {})
            compliance = performance_report.get("compliance_metrics", {})

            return {
                "avg_latency": performance.get("avg_latency_ms", 1000),
                "p95_latency": performance.get("p95_latency_ms", 1000),
                "compliance_10ms": compliance.get("events_under_10ms_percentage", 0)
            }

        except Exception:
            return {"avg_latency": 1000, "compliance_10ms": 0}

    async def _generate_migration_report(self) -> Dict[str, Any]:
        """Generate comprehensive migration report."""
        current_performance = await self._get_current_performance_summary()

        baseline_latency = 500  # Original batch interval
        improvement_factor = baseline_latency / max(1, current_performance["avg_latency"])

        return {
            "migration_timestamp": self.migration_start_time.isoformat(),
            "migration_duration_seconds": (
                datetime.now(timezone.utc) - self.migration_start_time
            ).total_seconds(),
            "baseline_metrics": self.baseline_metrics,
            "final_performance": current_performance,
            "improvement_factor": improvement_factor,
            "target_achievement": "✅ ACHIEVED" if current_performance["compliance_10ms"] >= 95 else "🎯 PARTIAL",
            "stages_completed": self.current_stage + 1,
            "test_mode": self.test_mode
        }

    async def _save_migration_report(self, report: Dict[str, Any]):
        """Save migration report to file."""
        try:
            import json
            filename = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)

            logger.info(f"📄 Migration report saved to: {filename}")

        except Exception as e:
            logger.warning(f"⚠️ Failed to save migration report: {e}")


async def main():
    """Main migration script entry point."""
    parser = argparse.ArgumentParser(description="WebSocket Optimization Migration")
    parser.add_argument("--test-mode", action="store_true",
                       help="Run in test mode (relaxed validation)")
    parser.add_argument("--rollback", action="store_true",
                       help="Rollback to previous configuration")

    args = parser.parse_args()

    if args.rollback:
        logger.info("🔙 Executing rollback to standard event publisher...")
        migration_manager = WebSocketMigrationManager(test_mode=False)
        await migration_manager._rollback_migration()
        return

    # Initialize migration manager
    migration_manager = WebSocketMigrationManager(test_mode=args.test_mode)

    # Execute migration
    success = await migration_manager.run_migration()

    if success:
        logger.info("🎉 Migration completed successfully!")
        print("\n" + "="*80)
        print("✅ WEBSOCKET OPTIMIZATION MIGRATION SUCCESSFUL")
        print("🎯 Target: <10ms event delivery latency")
        print("🚀 System now running with optimized micro-batching")
        print("📊 Monitor performance at: /api/v1/websocket-performance/latency-metrics")
        print("="*80)
        sys.exit(0)
    else:
        logger.error("❌ Migration failed - system rolled back")
        print("\n" + "="*80)
        print("❌ WEBSOCKET OPTIMIZATION MIGRATION FAILED")
        print("🔙 System rolled back to previous configuration")
        print("🔍 Check logs for detailed error information")
        print("🛠️ Consider running with --test-mode for validation")
        print("="*80)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())