"""
Service 6 Enhanced Lead Recovery Engine - System Health Checker
Automated system validation and recovery orchestration.
"""

import asyncio
import logging
import time
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from ..core.llm_client import LLMClient
from ..services.cache_service import CacheService
from ..services.database_service import DatabaseService
from .service6_alerting_engine import AlertLevel, Service6AlertingEngine
from .service6_metrics_collector import Service6MetricsCollector

logger = logging.getLogger(__name__)


class HealthCheckType(Enum):
    """Types of health checks."""

    CRITICAL = "critical"  # Database, Redis, core services
    ESSENTIAL = "essential"  # Agent orchestration, lead processing
    PERFORMANCE = "performance"  # Response times, throughput
    BUSINESS = "business"  # Revenue pipeline, conversion rates


class HealthCheckStatus(Enum):
    """Health check result status."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Individual health check result."""

    check_name: str
    check_type: HealthCheckType
    status: HealthCheckStatus
    message: str
    response_time_ms: float
    details: Dict[str, Any]
    timestamp: datetime
    recovery_action: Optional[str] = None


@dataclass
class SystemHealthReport:
    """Comprehensive system health report."""

    overall_status: HealthCheckStatus
    critical_checks: List[HealthCheckResult]
    essential_checks: List[HealthCheckResult]
    performance_checks: List[HealthCheckResult]
    business_checks: List[HealthCheckResult]
    total_checks: int
    passed_checks: int
    failed_checks: int
    warning_checks: int
    check_duration_seconds: float
    recovery_actions_triggered: List[str]
    next_check_time: datetime


class Service6SystemHealthChecker:
    """
    Automated system health checker for Service 6 Enhanced Lead Recovery Engine.
    Performs comprehensive health validation and triggers automated recovery.
    """

    def __init__(self):
        self.db_service = DatabaseService()
        self.cache_service = CacheService()
        self.metrics_collector = Service6MetricsCollector()
        self.alerting_engine = Service6AlertingEngine()

        # Health check configuration
        self.check_intervals = {
            HealthCheckType.CRITICAL: 30,  # Every 30 seconds
            HealthCheckType.ESSENTIAL: 60,  # Every minute
            HealthCheckType.PERFORMANCE: 120,  # Every 2 minutes
            HealthCheckType.BUSINESS: 300,  # Every 5 minutes
        }

        # Performance thresholds
        self.performance_thresholds = {
            "database_query_time_ms": 100,
            "agent_response_time_ms": 3000,
            "lead_processing_rate_per_hour": 50,
            "cache_hit_rate_percent": 80,
            "error_rate_percent": 1.0,
            "memory_usage_percent": 85,
            "cpu_usage_percent": 80,
        }

        # Recovery actions registry
        self.recovery_actions = {
            "database_connection_failed": self._recover_database_connection,
            "cache_unavailable": self._recover_cache_connection,
            "agent_timeout": self._recover_agent_timeouts,
            "high_error_rate": self._recover_high_error_rate,
            "memory_pressure": self._recover_memory_pressure,
            "lead_processing_stalled": self._recover_lead_processing,
        }

        self._running = False
        self._last_check_results = {}

    async def start_continuous_monitoring(self) -> None:
        """Start continuous system health monitoring."""
        if self._running:
            logger.warning("Health checker already running")
            return

        self._running = True
        logger.info("Starting Service 6 continuous health monitoring")

        # Start monitoring tasks for each check type
        tasks = []
        for check_type in HealthCheckType:
            interval = self.check_intervals[check_type]
            task = asyncio.create_task(self._run_periodic_checks(check_type, interval))
            tasks.append(task)

        # Wait for all monitoring tasks
        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Health monitoring error: {e}")
        finally:
            self._running = False

    def stop_monitoring(self) -> None:
        """Stop continuous health monitoring."""
        self._running = False
        logger.info("Stopping Service 6 health monitoring")

    async def run_comprehensive_health_check(self) -> SystemHealthReport:
        """Run comprehensive health check across all system components."""
        start_time = time.time()
        logger.info("Starting comprehensive Service 6 health check")

        # Execute all health checks in parallel
        check_tasks = [
            self._run_critical_checks(),
            self._run_essential_checks(),
            self._run_performance_checks(),
            self._run_business_checks(),
        ]

        try:
            results = await asyncio.gather(*check_tasks)
            critical_checks, essential_checks, performance_checks, business_checks = results

            # Aggregate results
            all_checks = critical_checks + essential_checks + performance_checks + business_checks

            # Determine overall status
            overall_status = self._determine_overall_status(all_checks)

            # Count check results
            passed = len([c for c in all_checks if c.status == HealthCheckStatus.PASS])
            failed = len([c for c in all_checks if c.status == HealthCheckStatus.FAIL])
            warnings = len([c for c in all_checks if c.status == HealthCheckStatus.WARN])

            # Trigger recovery actions if needed
            recovery_actions = await self._trigger_recovery_actions(all_checks)

            check_duration = time.time() - start_time

            report = SystemHealthReport(
                overall_status=overall_status,
                critical_checks=critical_checks,
                essential_checks=essential_checks,
                performance_checks=performance_checks,
                business_checks=business_checks,
                total_checks=len(all_checks),
                passed_checks=passed,
                failed_checks=failed,
                warning_checks=warnings,
                check_duration_seconds=check_duration,
                recovery_actions_triggered=recovery_actions,
                next_check_time=datetime.utcnow() + timedelta(minutes=1),
            )

            # Send alerts for critical failures
            if failed > 0 or overall_status == HealthCheckStatus.FAIL:
                await self._send_health_alerts(report)

            logger.info(
                f"Health check completed in {check_duration:.2f}s: {passed} passed, {failed} failed, {warnings} warnings"
            )
            return report

        except Exception as e:
            logger.error(f"Comprehensive health check failed: {e}")
            return self._create_error_report(str(e), time.time() - start_time)

    async def _run_periodic_checks(self, check_type: HealthCheckType, interval_seconds: int) -> None:
        """Run periodic health checks for a specific check type."""
        while self._running:
            try:
                start_time = time.time()

                if check_type == HealthCheckType.CRITICAL:
                    results = await self._run_critical_checks()
                elif check_type == HealthCheckType.ESSENTIAL:
                    results = await self._run_essential_checks()
                elif check_type == HealthCheckType.PERFORMANCE:
                    results = await self._run_performance_checks()
                elif check_type == HealthCheckType.BUSINESS:
                    results = await self._run_business_checks()
                else:
                    results = []

                # Store results for trending
                self._last_check_results[check_type] = results

                # Check for failures and trigger recovery
                failed_checks = [r for r in results if r.status == HealthCheckStatus.FAIL]
                if failed_checks:
                    await self._trigger_recovery_actions(failed_checks)

                # Calculate sleep time to maintain interval
                elapsed = time.time() - start_time
                sleep_time = max(0, interval_seconds - elapsed)
                await asyncio.sleep(sleep_time)

            except Exception as e:
                logger.error(f"Periodic {check_type.value} health check error: {e}")
                await asyncio.sleep(interval_seconds)

    async def _run_critical_checks(self) -> List[HealthCheckResult]:
        """Run critical infrastructure health checks."""
        checks = []

        # Database connectivity
        checks.append(await self._check_database_connectivity())

        # Redis cache connectivity
        checks.append(await self._check_cache_connectivity())

        # Core services availability
        checks.append(await self._check_llm_service_availability())

        # File system access
        checks.append(await self._check_file_system_access())

        return checks

    async def _run_essential_checks(self) -> List[HealthCheckResult]:
        """Run essential service health checks."""
        checks = []

        # Agent orchestration system
        checks.append(await self._check_agent_orchestration())

        # Lead processing pipeline
        checks.append(await self._check_lead_processing_pipeline())

        # Webhook processing
        checks.append(await self._check_webhook_processing())

        # Background task processing
        checks.append(await self._check_background_tasks())

        return checks

    async def _run_performance_checks(self) -> List[HealthCheckResult]:
        """Run performance health checks."""
        checks = []

        # Database query performance
        checks.append(await self._check_database_performance())

        # Cache performance
        checks.append(await self._check_cache_performance())

        # Agent response times
        checks.append(await self._check_agent_response_times())

        # System resource usage
        checks.append(await self._check_system_resources())

        return checks

    async def _run_business_checks(self) -> List[HealthCheckResult]:
        """Run business KPI health checks."""
        checks = []

        # Lead processing rate
        checks.append(await self._check_lead_processing_rate())

        # Revenue pipeline health
        checks.append(await self._check_revenue_pipeline())

        # Conversion rate trends
        checks.append(await self._check_conversion_rates())

        # Customer satisfaction metrics
        checks.append(await self._check_customer_satisfaction())

        return checks

    async def _check_database_connectivity(self) -> HealthCheckResult:
        """Check database connectivity and basic operations."""
        start_time = time.time()
        check_name = "database_connectivity"

        try:
            # Test basic connectivity
            async with self.db_service.get_connection() as conn:
                # Execute simple query
                result = await conn.fetchval("SELECT 1")

                if result == 1:
                    response_time = (time.time() - start_time) * 1000
                    return HealthCheckResult(
                        check_name=check_name,
                        check_type=HealthCheckType.CRITICAL,
                        status=HealthCheckStatus.PASS,
                        message="Database connectivity successful",
                        response_time_ms=response_time,
                        details={"query_result": result},
                        timestamp=datetime.utcnow(),
                    )
                else:
                    return self._create_fail_result(
                        check_name,
                        HealthCheckType.CRITICAL,
                        "Database query returned unexpected result",
                        {"expected": 1, "actual": result},
                    )

        except Exception as e:
            return self._create_fail_result(
                check_name,
                HealthCheckType.CRITICAL,
                f"Database connectivity failed: {str(e)}",
                {"error": str(e)},
                recovery_action="database_connection_failed",
            )

    async def _check_cache_connectivity(self) -> HealthCheckResult:
        """Check Redis cache connectivity and operations."""
        start_time = time.time()
        check_name = "cache_connectivity"
        test_key = f"health_check_{int(time.time())}"

        try:
            # Test cache set/get operations
            await self.cache_service.set(test_key, "health_check_value", ttl=10)
            value = await self.cache_service.get(test_key)
            await self.cache_service.delete(test_key)

            if value == "health_check_value":
                response_time = (time.time() - start_time) * 1000
                return HealthCheckResult(
                    check_name=check_name,
                    check_type=HealthCheckType.CRITICAL,
                    status=HealthCheckStatus.PASS,
                    message="Cache connectivity successful",
                    response_time_ms=response_time,
                    details={"test_key": test_key},
                    timestamp=datetime.utcnow(),
                )
            else:
                return self._create_fail_result(
                    check_name,
                    HealthCheckType.CRITICAL,
                    "Cache operation failed - value mismatch",
                    {"expected": "health_check_value", "actual": value},
                )

        except Exception as e:
            return self._create_fail_result(
                check_name,
                HealthCheckType.CRITICAL,
                f"Cache connectivity failed: {str(e)}",
                {"error": str(e)},
                recovery_action="cache_unavailable",
            )

    async def _check_llm_service_availability(self) -> HealthCheckResult:
        """Check LLM service availability and response."""
        start_time = time.time()
        check_name = "llm_service_availability"

        try:
            # Test LLM with simple request
            llm_client = LLMClient()
            test_prompt = "Respond with exactly: 'Service health check successful'"

            response = await llm_client.generate_response(
                messages=[{"role": "user", "content": test_prompt}], max_tokens=20
            )

            response_time = (time.time() - start_time) * 1000

            if "health check successful" in response.lower():
                return HealthCheckResult(
                    check_name=check_name,
                    check_type=HealthCheckType.CRITICAL,
                    status=HealthCheckStatus.PASS,
                    message="LLM service responding correctly",
                    response_time_ms=response_time,
                    details={"response_preview": response[:100]},
                    timestamp=datetime.utcnow(),
                )
            else:
                return self._create_warn_result(
                    check_name,
                    HealthCheckType.CRITICAL,
                    "LLM service responding but with unexpected content",
                    {"response_preview": response[:100]},
                )

        except Exception as e:
            return self._create_fail_result(
                check_name, HealthCheckType.CRITICAL, f"LLM service unavailable: {str(e)}", {"error": str(e)}
            )

    async def _check_file_system_access(self) -> HealthCheckResult:
        """Check file system access for logs and temporary files."""
        start_time = time.time()
        check_name = "file_system_access"

        try:
            import os
            import tempfile

            # Test temporary file creation
            with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
                test_content = f"health_check_{int(time.time())}"
                f.write(test_content)
                temp_path = f.name

            # Test file reading
            with open(temp_path, "r") as f:
                read_content = f.read()

            # Clean up
            os.unlink(temp_path)

            response_time = (time.time() - start_time) * 1000

            if read_content == test_content:
                return HealthCheckResult(
                    check_name=check_name,
                    check_type=HealthCheckType.CRITICAL,
                    status=HealthCheckStatus.PASS,
                    message="File system access successful",
                    response_time_ms=response_time,
                    details={"temp_file_path": temp_path},
                    timestamp=datetime.utcnow(),
                )
            else:
                return self._create_fail_result(
                    check_name,
                    HealthCheckType.CRITICAL,
                    "File system read/write mismatch",
                    {"expected": test_content, "actual": read_content},
                )

        except Exception as e:
            return self._create_fail_result(
                check_name, HealthCheckType.CRITICAL, f"File system access failed: {str(e)}", {"error": str(e)}
            )

    def _determine_overall_status(self, checks: List[HealthCheckResult]) -> HealthCheckStatus:
        """Determine overall system status from individual check results."""
        if not checks:
            return HealthCheckStatus.UNKNOWN

        # Critical failures result in overall failure
        critical_failures = [
            c for c in checks if c.check_type == HealthCheckType.CRITICAL and c.status == HealthCheckStatus.FAIL
        ]

        if critical_failures:
            return HealthCheckStatus.FAIL

        # Any failures in essential systems result in overall failure
        essential_failures = [
            c for c in checks if c.check_type == HealthCheckType.ESSENTIAL and c.status == HealthCheckStatus.FAIL
        ]

        if essential_failures:
            return HealthCheckStatus.FAIL

        # Multiple warnings or performance issues result in warning
        warnings = [c for c in checks if c.status == HealthCheckStatus.WARN]
        performance_failures = [
            c for c in checks if c.check_type == HealthCheckType.PERFORMANCE and c.status == HealthCheckStatus.FAIL
        ]

        if len(warnings) >= 3 or len(performance_failures) >= 2:
            return HealthCheckStatus.WARN

        # Otherwise system is passing
        return HealthCheckStatus.PASS

    async def _trigger_recovery_actions(self, failed_checks: List[HealthCheckResult]) -> List[str]:
        """Trigger automated recovery actions for failed checks."""
        triggered_actions = []

        for check in failed_checks:
            if check.recovery_action and check.recovery_action in self.recovery_actions:
                try:
                    recovery_function = self.recovery_actions[check.recovery_action]
                    success = await recovery_function(check)

                    if success:
                        triggered_actions.append(check.recovery_action)
                        logger.info(f"Recovery action '{check.recovery_action}' completed successfully")
                    else:
                        logger.warning(f"Recovery action '{check.recovery_action}' failed")

                except Exception as e:
                    logger.error(f"Recovery action '{check.recovery_action}' error: {e}")

        return triggered_actions

    def _create_fail_result(
        self,
        check_name: str,
        check_type: HealthCheckType,
        message: str,
        details: Dict[str, Any],
        recovery_action: Optional[str] = None,
    ) -> HealthCheckResult:
        """Create a failed health check result."""
        return HealthCheckResult(
            check_name=check_name,
            check_type=check_type,
            status=HealthCheckStatus.FAIL,
            message=message,
            response_time_ms=0.0,
            details=details,
            timestamp=datetime.utcnow(),
            recovery_action=recovery_action,
        )

    def _create_warn_result(
        self, check_name: str, check_type: HealthCheckType, message: str, details: Dict[str, Any]
    ) -> HealthCheckResult:
        """Create a warning health check result."""
        return HealthCheckResult(
            check_name=check_name,
            check_type=check_type,
            status=HealthCheckStatus.WARN,
            message=message,
            response_time_ms=0.0,
            details=details,
            timestamp=datetime.utcnow(),
        )

    # Recovery action implementations
    async def _recover_database_connection(self, check: HealthCheckResult) -> bool:
        """Recover from database connection failures."""
        try:
            # Attempt to refresh database connection pool
            await self.db_service.refresh_connection_pool()
            logger.info("Database connection pool refreshed")
            return True
        except Exception as e:
            logger.error(f"Database connection recovery failed: {e}")
            return False

    async def _recover_cache_connection(self, check: HealthCheckResult) -> bool:
        """Recover from cache connection failures."""
        try:
            # Attempt to reconnect to Redis
            await self.cache_service.reconnect()
            logger.info("Cache connection restored")
            return True
        except Exception as e:
            logger.error(f"Cache connection recovery failed: {e}")
            return False

    # Additional recovery methods would be implemented here...
