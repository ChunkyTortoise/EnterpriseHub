"""
Enterprise Canary Deployment System for RAG Models
Demonstrates advanced MLOps deployment strategies and risk management
"""

import asyncio
import hashlib
import json
import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import aiohttp
import numpy as np

logger = logging.getLogger(__name__)


class DeploymentStage(Enum):
    """Deployment stages for canary deployment"""

    PENDING = "pending"
    VALIDATION = "validation"
    CANARY = "canary"
    RAMP_UP = "ramp_up"
    FULL_DEPLOYMENT = "full_deployment"
    ROLLBACK = "rollback"
    FAILED = "failed"
    COMPLETED = "completed"


class HealthStatus(Enum):
    """Health check status"""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class DeploymentMetrics:
    """Metrics for deployment monitoring"""

    timestamp: datetime
    stage: DeploymentStage
    traffic_percentage: float
    request_count: int
    error_rate: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    success_rate: float
    throughput_rps: float
    memory_usage_mb: float
    cpu_usage_percent: float
    custom_metrics: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["stage"] = self.stage.value
        return data


@dataclass
class CanaryConfig:
    """Configuration for canary deployment"""

    # Basic configuration
    model_name: str
    new_version: str
    current_version: str

    # Traffic splitting configuration
    initial_canary_percentage: float = 5.0
    max_canary_percentage: float = 50.0
    ramp_up_step: float = 10.0
    ramp_up_interval_minutes: int = 10

    # Success criteria
    min_requests_for_decision: int = 100
    max_error_rate_threshold: float = 0.05
    max_response_time_degradation: float = 0.2  # 20% slower is acceptable
    min_success_rate: float = 0.95

    # Monitoring configuration
    observation_window_minutes: int = 15
    health_check_interval_seconds: int = 30
    metrics_collection_interval_seconds: int = 60

    # Safety configuration
    auto_rollback_enabled: bool = True
    manual_approval_required: bool = False
    max_deployment_duration_hours: int = 4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)


@dataclass
class HealthCheck:
    """Health check configuration and result"""

    endpoint: str
    expected_status_code: int = 200
    timeout_seconds: int = 10
    expected_response_fields: List[str] = field(default_factory=list)

    # Result fields
    last_check_time: Optional[datetime] = None
    status: HealthStatus = HealthStatus.UNKNOWN
    response_time_ms: float = 0.0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        if self.last_check_time:
            data["last_check_time"] = self.last_check_time.isoformat()
        data["status"] = self.status.value
        return data


class TrafficSplitter:
    """
    Traffic splitting controller for canary deployments

    Manages traffic distribution between current and canary versions
    """

    def __init__(self, config: CanaryConfig):
        """Initialize traffic splitter"""
        self.config = config
        self.current_canary_percentage = 0.0
        self.traffic_log: List[Dict[str, Any]] = []

    def should_route_to_canary(self, request_id: str = None) -> bool:
        """
        Determine if request should go to canary version

        Args:
            request_id: Optional request identifier for consistent routing

        Returns:
            True if should route to canary, False otherwise
        """
        if self.current_canary_percentage <= 0:
            return False

        # Use deterministic routing based on request ID if provided
        if request_id:
            hash_value = int(hashlib.md5(request_id.encode()).hexdigest(), 16)
            route_percentage = (hash_value % 100) + 1
        else:
            # Random routing
            route_percentage = np.random.uniform(0, 100)

        should_canary = route_percentage <= self.current_canary_percentage

        # Log traffic decision
        self.traffic_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "request_id": request_id,
                "canary_percentage": self.current_canary_percentage,
                "route_to_canary": should_canary,
            }
        )

        return should_canary

    def update_traffic_percentage(self, new_percentage: float) -> None:
        """Update traffic percentage to canary"""
        old_percentage = self.current_canary_percentage
        self.current_canary_percentage = max(0.0, min(100.0, new_percentage))

        logger.info(f"Traffic percentage updated: {old_percentage}% -> {self.current_canary_percentage}%")

    def get_traffic_statistics(self, window_minutes: int = 60) -> Dict[str, Any]:
        """Get traffic statistics for the specified window"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)

        recent_logs = [log for log in self.traffic_log if datetime.fromisoformat(log["timestamp"]) >= cutoff_time]

        if not recent_logs:
            return {"total_requests": 0, "canary_requests": 0, "canary_percentage": 0.0, "current_requests": 0}

        total_requests = len(recent_logs)
        canary_requests = sum(1 for log in recent_logs if log["route_to_canary"])
        current_requests = total_requests - canary_requests

        return {
            "total_requests": total_requests,
            "canary_requests": canary_requests,
            "canary_percentage": (canary_requests / total_requests * 100) if total_requests > 0 else 0,
            "current_requests": current_requests,
            "window_minutes": window_minutes,
        }


class MetricsCollector:
    """
    Metrics collection and analysis for canary deployments

    Collects and compares metrics between canary and current versions
    """

    def __init__(self, config: CanaryConfig):
        """Initialize metrics collector"""
        self.config = config
        self.metrics_history: List[DeploymentMetrics] = []
        self.baseline_metrics: Optional[DeploymentMetrics] = None

    async def collect_metrics(
        self, canary_endpoint: str, current_endpoint: str, traffic_stats: Dict[str, Any]
    ) -> Tuple[DeploymentMetrics, DeploymentMetrics]:
        """
        Collect metrics from both canary and current versions

        Args:
            canary_endpoint: Canary version metrics endpoint
            current_endpoint: Current version metrics endpoint
            traffic_stats: Current traffic statistics

        Returns:
            Tuple of (canary_metrics, current_metrics)
        """
        try:
            async with aiohttp.ClientSession() as session:
                # Collect canary metrics
                canary_metrics = await self._collect_endpoint_metrics(session, canary_endpoint, "canary")

                # Collect current metrics
                current_metrics = await self._collect_endpoint_metrics(session, current_endpoint, "current")

                # Add traffic information
                canary_metrics.traffic_percentage = traffic_stats.get("canary_percentage", 0)
                canary_metrics.request_count = traffic_stats.get("canary_requests", 0)
                current_metrics.traffic_percentage = 100 - traffic_stats.get("canary_percentage", 0)
                current_metrics.request_count = traffic_stats.get("current_requests", 0)

                # Store in history
                self.metrics_history.append(canary_metrics)
                self.metrics_history.append(current_metrics)

                # Keep only recent history (last 24 hours)
                cutoff_time = datetime.utcnow() - timedelta(hours=24)
                self.metrics_history = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

                return canary_metrics, current_metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            # Return empty metrics in case of failure
            empty_canary = self._create_empty_metrics("canary")
            empty_current = self._create_empty_metrics("current")
            return empty_canary, empty_current

    async def _collect_endpoint_metrics(
        self, session: aiohttp.ClientSession, endpoint: str, version_name: str
    ) -> DeploymentMetrics:
        """Collect metrics from a specific endpoint"""
        try:
            async with session.get(endpoint, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()

                    # Parse standard metrics
                    metrics = DeploymentMetrics(
                        timestamp=datetime.utcnow(),
                        stage=DeploymentStage.CANARY if version_name == "canary" else DeploymentStage.FULL_DEPLOYMENT,
                        traffic_percentage=0.0,  # Will be updated later
                        request_count=data.get("request_count", 0),
                        error_rate=data.get("error_rate", 0.0),
                        response_time_p50=data.get("response_time_p50", 0.0),
                        response_time_p95=data.get("response_time_p95", 0.0),
                        response_time_p99=data.get("response_time_p99", 0.0),
                        success_rate=data.get("success_rate", 0.0),
                        throughput_rps=data.get("throughput_rps", 0.0),
                        memory_usage_mb=data.get("memory_usage_mb", 0.0),
                        cpu_usage_percent=data.get("cpu_usage_percent", 0.0),
                        custom_metrics=data.get("custom_metrics", {}),
                    )

                    return metrics

                else:
                    logger.warning(f"Metrics endpoint {endpoint} returned status {response.status}")
                    return self._create_empty_metrics(version_name)

        except Exception as e:
            logger.error(f"Failed to collect metrics from {endpoint}: {e}")
            return self._create_empty_metrics(version_name)

    def _create_empty_metrics(self, version_name: str) -> DeploymentMetrics:
        """Create empty metrics object for error cases"""
        return DeploymentMetrics(
            timestamp=datetime.utcnow(),
            stage=DeploymentStage.CANARY if version_name == "canary" else DeploymentStage.FULL_DEPLOYMENT,
            traffic_percentage=0.0,
            request_count=0,
            error_rate=1.0,  # Assume failure if we can't collect metrics
            response_time_p50=0.0,
            response_time_p95=0.0,
            response_time_p99=0.0,
            success_rate=0.0,
            throughput_rps=0.0,
            memory_usage_mb=0.0,
            cpu_usage_percent=0.0,
        )

    def analyze_metrics_comparison(
        self, canary_metrics: DeploymentMetrics, current_metrics: DeploymentMetrics
    ) -> Dict[str, Any]:
        """
        Analyze metrics comparison between canary and current

        Returns analysis results with recommendations
        """
        analysis = {
            "timestamp": datetime.utcnow().isoformat(),
            "canary_version": self.config.new_version,
            "current_version": self.config.current_version,
            "comparison": {},
            "health_status": HealthStatus.HEALTHY.value,
            "recommendations": [],
        }

        try:
            # Error rate comparison
            error_rate_diff = canary_metrics.error_rate - current_metrics.error_rate
            analysis["comparison"]["error_rate"] = {
                "canary": canary_metrics.error_rate,
                "current": current_metrics.error_rate,
                "difference": error_rate_diff,
                "threshold_exceeded": canary_metrics.error_rate > self.config.max_error_rate_threshold,
            }

            if canary_metrics.error_rate > self.config.max_error_rate_threshold:
                analysis["health_status"] = HealthStatus.UNHEALTHY.value
                analysis["recommendations"].append(
                    f"Canary error rate ({canary_metrics.error_rate:.3f}) exceeds threshold ({self.config.max_error_rate_threshold})"
                )

            # Response time comparison
            if current_metrics.response_time_p95 > 0:
                response_time_degradation = (
                    canary_metrics.response_time_p95 - current_metrics.response_time_p95
                ) / current_metrics.response_time_p95
            else:
                response_time_degradation = 0.0

            analysis["comparison"]["response_time_p95"] = {
                "canary": canary_metrics.response_time_p95,
                "current": current_metrics.response_time_p95,
                "degradation_percentage": response_time_degradation * 100,
                "threshold_exceeded": response_time_degradation > self.config.max_response_time_degradation,
            }

            if response_time_degradation > self.config.max_response_time_degradation:
                analysis["health_status"] = HealthStatus.DEGRADED.value
                analysis["recommendations"].append(
                    f"Response time degradation ({response_time_degradation:.1%}) exceeds threshold ({self.config.max_response_time_degradation:.1%})"
                )

            # Success rate comparison
            analysis["comparison"]["success_rate"] = {
                "canary": canary_metrics.success_rate,
                "current": current_metrics.success_rate,
                "difference": canary_metrics.success_rate - current_metrics.success_rate,
                "threshold_exceeded": canary_metrics.success_rate < self.config.min_success_rate,
            }

            if canary_metrics.success_rate < self.config.min_success_rate:
                analysis["health_status"] = HealthStatus.UNHEALTHY.value
                analysis["recommendations"].append(
                    f"Canary success rate ({canary_metrics.success_rate:.3f}) below threshold ({self.config.min_success_rate})"
                )

            # Request volume check
            if canary_metrics.request_count < self.config.min_requests_for_decision:
                analysis["recommendations"].append(
                    f"Insufficient request volume for reliable decision ({canary_metrics.request_count} < {self.config.min_requests_for_decision})"
                )

            # Resource utilization comparison
            analysis["comparison"]["resource_usage"] = {
                "canary_memory_mb": canary_metrics.memory_usage_mb,
                "current_memory_mb": current_metrics.memory_usage_mb,
                "canary_cpu_percent": canary_metrics.cpu_usage_percent,
                "current_cpu_percent": current_metrics.cpu_usage_percent,
            }

        except Exception as e:
            logger.error(f"Metrics analysis failed: {e}")
            analysis["health_status"] = HealthStatus.UNKNOWN.value
            analysis["recommendations"].append(f"Analysis error: {str(e)}")

        return analysis


class HealthChecker:
    """Health check manager for deployment monitoring"""

    def __init__(self, health_checks: List[HealthCheck]):
        """Initialize health checker"""
        self.health_checks = health_checks

    async def run_health_checks(self) -> Dict[str, HealthStatus]:
        """Run all health checks and return results"""
        results = {}

        async with aiohttp.ClientSession() as session:
            for health_check in self.health_checks:
                status = await self._run_single_health_check(session, health_check)
                results[health_check.endpoint] = status

        return results

    async def _run_single_health_check(self, session: aiohttp.ClientSession, health_check: HealthCheck) -> HealthStatus:
        """Run a single health check"""
        try:
            start_time = time.time()

            async with session.get(health_check.endpoint, timeout=health_check.timeout_seconds) as response:
                response_time_ms = (time.time() - start_time) * 1000

                health_check.last_check_time = datetime.utcnow()
                health_check.response_time_ms = response_time_ms

                if response.status == health_check.expected_status_code:
                    # Validate response content if expected fields are specified
                    if health_check.expected_response_fields:
                        try:
                            response_data = await response.json()
                            for field in health_check.expected_response_fields:
                                if field not in response_data:
                                    health_check.status = HealthStatus.DEGRADED
                                    health_check.error_message = f"Missing expected field: {field}"
                                    return HealthStatus.DEGRADED
                        except Exception as e:
                            health_check.status = HealthStatus.DEGRADED
                            health_check.error_message = f"Invalid response format: {str(e)}"
                            return HealthStatus.DEGRADED

                    health_check.status = HealthStatus.HEALTHY
                    health_check.error_message = None
                    return HealthStatus.HEALTHY
                else:
                    health_check.status = HealthStatus.UNHEALTHY
                    health_check.error_message = f"Unexpected status code: {response.status}"
                    return HealthStatus.UNHEALTHY

        except asyncio.TimeoutError:
            health_check.status = HealthStatus.UNHEALTHY
            health_check.error_message = "Health check timeout"
            return HealthStatus.UNHEALTHY
        except Exception as e:
            health_check.status = HealthStatus.UNHEALTHY
            health_check.error_message = str(e)
            return HealthStatus.UNHEALTHY


class CanaryDeploymentController:
    """
    Main controller for canary deployments

    Orchestrates the entire canary deployment process with automated decision making
    """

    def __init__(
        self,
        config: CanaryConfig,
        canary_endpoint: str,
        current_endpoint: str,
        health_checks: Optional[List[HealthCheck]] = None,
    ):
        """Initialize canary deployment controller"""
        self.config = config
        self.canary_endpoint = canary_endpoint
        self.current_endpoint = current_endpoint

        self.traffic_splitter = TrafficSplitter(config)
        self.metrics_collector = MetricsCollector(config)
        self.health_checker = HealthChecker(health_checks or [])

        self.current_stage = DeploymentStage.PENDING
        self.deployment_start_time: Optional[datetime] = None
        self.deployment_log: List[Dict[str, Any]] = []
        self.should_stop = False

    async def start_canary_deployment(self) -> Dict[str, Any]:
        """
        Start the canary deployment process

        Returns deployment results
        """
        try:
            self.deployment_start_time = datetime.utcnow()
            self.current_stage = DeploymentStage.VALIDATION

            logger.info(f"Starting canary deployment for {self.config.model_name} {self.config.new_version}")

            # Initial validation
            validation_result = await self._run_initial_validation()
            if not validation_result["success"]:
                return await self._handle_deployment_failure("Initial validation failed", validation_result)

            # Start canary phase
            self.current_stage = DeploymentStage.CANARY
            self.traffic_splitter.update_traffic_percentage(self.config.initial_canary_percentage)

            logger.info(f"Canary deployment started with {self.config.initial_canary_percentage}% traffic")

            # Monitor and ramp up
            while not self.should_stop and self.current_stage in [DeploymentStage.CANARY, DeploymentStage.RAMP_UP]:
                # Check deployment timeout
                if self._is_deployment_timeout():
                    return await self._handle_deployment_failure("Deployment timeout exceeded")

                # Collect metrics and analyze
                analysis_result = await self._analyze_canary_performance()

                if analysis_result["health_status"] == HealthStatus.UNHEALTHY.value:
                    if self.config.auto_rollback_enabled:
                        return await self._execute_rollback("Unhealthy metrics detected", analysis_result)
                    else:
                        return await self._handle_deployment_failure("Manual intervention required", analysis_result)

                # Decide next action
                decision = self._make_deployment_decision(analysis_result)

                if decision["action"] == "ramp_up":
                    await self._ramp_up_traffic(decision["new_percentage"])
                elif decision["action"] == "promote_to_full":
                    return await self._promote_to_full_deployment()
                elif decision["action"] == "wait":
                    logger.info(f"Waiting for more data: {decision['reason']}")
                elif decision["action"] == "rollback":
                    if self.config.auto_rollback_enabled:
                        return await self._execute_rollback(decision["reason"], analysis_result)
                    else:
                        return await self._handle_deployment_failure("Manual intervention required", analysis_result)

                # Wait before next iteration
                await asyncio.sleep(self.config.metrics_collection_interval_seconds)

            return {"success": True, "final_stage": self.current_stage.value, "deployment_log": self.deployment_log}

        except Exception as e:
            logger.error(f"Canary deployment failed with exception: {e}")
            return await self._handle_deployment_failure(f"Unexpected error: {str(e)}")

    async def _run_initial_validation(self) -> Dict[str, Any]:
        """Run initial validation before starting canary"""
        try:
            # Health checks
            health_results = await self.health_checker.run_health_checks()

            unhealthy_endpoints = [
                endpoint for endpoint, status in health_results.items() if status != HealthStatus.HEALTHY
            ]

            if unhealthy_endpoints:
                return {
                    "success": False,
                    "reason": f"Unhealthy endpoints: {unhealthy_endpoints}",
                    "health_results": {k: v.value for k, v in health_results.items()},
                }

            # Collect baseline metrics
            traffic_stats = self.traffic_splitter.get_traffic_statistics()
            canary_metrics, current_metrics = await self.metrics_collector.collect_metrics(
                self.canary_endpoint + "/metrics", self.current_endpoint + "/metrics", traffic_stats
            )

            self.metrics_collector.baseline_metrics = current_metrics

            return {
                "success": True,
                "health_results": {k: v.value for k, v in health_results.items()},
                "baseline_metrics": current_metrics.to_dict(),
            }

        except Exception as e:
            return {"success": False, "reason": f"Validation error: {str(e)}"}

    async def _analyze_canary_performance(self) -> Dict[str, Any]:
        """Analyze canary performance and return health assessment"""
        try:
            # Collect current metrics
            traffic_stats = self.traffic_splitter.get_traffic_statistics(self.config.observation_window_minutes)

            canary_metrics, current_metrics = await self.metrics_collector.collect_metrics(
                self.canary_endpoint + "/metrics", self.current_endpoint + "/metrics", traffic_stats
            )

            # Analyze comparison
            analysis = self.metrics_collector.analyze_metrics_comparison(canary_metrics, current_metrics)

            # Run health checks
            health_results = await self.health_checker.run_health_checks()

            # Combine results
            analysis["traffic_stats"] = traffic_stats
            analysis["health_check_results"] = {k: v.value for k, v in health_results.items()}

            # Log analysis
            self.deployment_log.append(
                {"timestamp": datetime.utcnow().isoformat(), "stage": self.current_stage.value, "analysis": analysis}
            )

            return analysis

        except Exception as e:
            logger.error(f"Performance analysis failed: {e}")
            return {"health_status": HealthStatus.UNKNOWN.value, "error": str(e)}

    def _make_deployment_decision(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Make deployment decision based on analysis"""
        try:
            traffic_stats = analysis.get("traffic_stats", {})
            canary_requests = traffic_stats.get("canary_requests", 0)
            current_percentage = self.traffic_splitter.current_canary_percentage

            # Check if we have enough data
            if canary_requests < self.config.min_requests_for_decision:
                return {
                    "action": "wait",
                    "reason": f"Insufficient requests ({canary_requests} < {self.config.min_requests_for_decision})",
                }

            # Check health status
            if analysis["health_status"] == HealthStatus.UNHEALTHY.value:
                return {"action": "rollback", "reason": "Unhealthy metrics detected"}

            # Check if ready for full deployment
            if (
                current_percentage >= self.config.max_canary_percentage
                and analysis["health_status"] == HealthStatus.HEALTHY.value
            ):
                # Additional checks for full deployment
                comparison = analysis.get("comparison", {})
                error_rate_ok = not comparison.get("error_rate", {}).get("threshold_exceeded", True)
                response_time_ok = not comparison.get("response_time_p95", {}).get("threshold_exceeded", True)
                success_rate_ok = not comparison.get("success_rate", {}).get("threshold_exceeded", True)

                if error_rate_ok and response_time_ok and success_rate_ok:
                    return {"action": "promote_to_full", "reason": "All criteria met for full deployment"}

            # Ramp up if performance is good
            if (
                analysis["health_status"] == HealthStatus.HEALTHY.value
                and current_percentage < self.config.max_canary_percentage
            ):
                new_percentage = min(current_percentage + self.config.ramp_up_step, self.config.max_canary_percentage)

                return {
                    "action": "ramp_up",
                    "new_percentage": new_percentage,
                    "reason": f"Performance good, ramping to {new_percentage}%",
                }

            # Continue monitoring
            return {"action": "wait", "reason": "Continuing observation"}

        except Exception as e:
            logger.error(f"Decision making failed: {e}")
            return {"action": "rollback", "reason": f"Decision error: {str(e)}"}

    async def _ramp_up_traffic(self, new_percentage: float) -> None:
        """Ramp up traffic to canary version"""
        old_percentage = self.traffic_splitter.current_canary_percentage
        self.traffic_splitter.update_traffic_percentage(new_percentage)

        if new_percentage > self.config.initial_canary_percentage:
            self.current_stage = DeploymentStage.RAMP_UP

        logger.info(f"Traffic ramped up: {old_percentage}% -> {new_percentage}%")

        self.deployment_log.append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "action": "ramp_up",
                "old_percentage": old_percentage,
                "new_percentage": new_percentage,
            }
        )

    async def _promote_to_full_deployment(self) -> Dict[str, Any]:
        """Promote canary to full deployment"""
        self.current_stage = DeploymentStage.FULL_DEPLOYMENT
        self.traffic_splitter.update_traffic_percentage(100.0)

        logger.info("Promoted canary to full deployment (100% traffic)")

        self.deployment_log.append(
            {"timestamp": datetime.utcnow().isoformat(), "action": "promote_to_full", "stage": self.current_stage.value}
        )

        self.current_stage = DeploymentStage.COMPLETED

        return {
            "success": True,
            "action": "promoted_to_full",
            "final_stage": self.current_stage.value,
            "deployment_duration_minutes": self._get_deployment_duration_minutes(),
            "deployment_log": self.deployment_log,
        }

    async def _execute_rollback(self, reason: str, analysis: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute rollback to previous version"""
        self.current_stage = DeploymentStage.ROLLBACK
        self.traffic_splitter.update_traffic_percentage(0.0)

        logger.warning(f"Executing rollback: {reason}")

        rollback_result = {
            "success": False,
            "action": "rollback",
            "reason": reason,
            "final_stage": self.current_stage.value,
            "deployment_duration_minutes": self._get_deployment_duration_minutes(),
            "analysis": analysis,
            "deployment_log": self.deployment_log,
        }

        self.deployment_log.append({"timestamp": datetime.utcnow().isoformat(), "action": "rollback", "reason": reason})

        return rollback_result

    async def _handle_deployment_failure(self, reason: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Handle deployment failure"""
        self.current_stage = DeploymentStage.FAILED
        self.traffic_splitter.update_traffic_percentage(0.0)

        logger.error(f"Deployment failed: {reason}")

        return {
            "success": False,
            "action": "failed",
            "reason": reason,
            "final_stage": self.current_stage.value,
            "deployment_duration_minutes": self._get_deployment_duration_minutes(),
            "details": details,
            "deployment_log": self.deployment_log,
        }

    def _is_deployment_timeout(self) -> bool:
        """Check if deployment has exceeded maximum duration"""
        if not self.deployment_start_time:
            return False

        duration = datetime.utcnow() - self.deployment_start_time
        max_duration = timedelta(hours=self.config.max_deployment_duration_hours)
        return duration > max_duration

    def _get_deployment_duration_minutes(self) -> float:
        """Get deployment duration in minutes"""
        if not self.deployment_start_time:
            return 0.0

        duration = datetime.utcnow() - self.deployment_start_time
        return duration.total_seconds() / 60

    def stop_deployment(self) -> None:
        """Stop the deployment process"""
        self.should_stop = True
        logger.info("Deployment stop requested")

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status"""
        return {
            "stage": self.current_stage.value,
            "traffic_percentage": self.traffic_splitter.current_canary_percentage,
            "deployment_duration_minutes": self._get_deployment_duration_minutes(),
            "start_time": self.deployment_start_time.isoformat() if self.deployment_start_time else None,
            "config": self.config.to_dict(),
            "recent_log_entries": self.deployment_log[-5:],  # Last 5 entries
        }


# Example usage for RAG system
async def create_rag_canary_deployment():
    """Example canary deployment setup for RAG system"""
    config = CanaryConfig(
        model_name="rag_embeddings",
        new_version="v2.1.0",
        current_version="v2.0.0",
        initial_canary_percentage=5.0,
        max_canary_percentage=50.0,
        ramp_up_step=10.0,
        ramp_up_interval_minutes=15,
        min_requests_for_decision=200,
        max_error_rate_threshold=0.03,
        max_response_time_degradation=0.15,
        min_success_rate=0.97,
        observation_window_minutes=20,
        auto_rollback_enabled=True,
        max_deployment_duration_hours=3,
    )

    health_checks = [
        HealthCheck(
            endpoint="http://canary-rag-api:8000/health",
            expected_status_code=200,
            expected_response_fields=["status", "version", "uptime"],
        ),
        HealthCheck(endpoint="http://canary-rag-api:8000/api/v1/embedding/health", expected_status_code=200),
    ]

    controller = CanaryDeploymentController(
        config=config,
        canary_endpoint="http://canary-rag-api:8000",
        current_endpoint="http://current-rag-api:8000",
        health_checks=health_checks,
    )

    # Start deployment
    result = await controller.start_canary_deployment()
    return result
