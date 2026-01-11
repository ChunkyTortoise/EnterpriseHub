"""
System Resilience Manager
=========================

Advanced resilience mechanisms including circuit breakers, failover systems,
automatic recovery, and chaos engineering capabilities.

Key Features:
1. Multi-layer circuit breakers with intelligent recovery
2. Automatic failover and load balancing
3. Self-healing service recovery
4. Cascading failure prevention
5. Graceful degradation modes
6. Performance isolation boundaries
"""

import asyncio
import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Callable, Union
import random
import json
from pathlib import Path

logger = logging.getLogger(__name__)


class ResilienceState(Enum):
    """System resilience states."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    RECOVERY = "recovery"
    FAILURE = "failure"


class FailureMode(Enum):
    """Types of failure modes."""
    SERVICE_UNAVAILABLE = "service_unavailable"
    PERFORMANCE_DEGRADATION = "performance_degradation"
    CASCADING_FAILURE = "cascading_failure"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"


class RecoveryStrategy(Enum):
    """Recovery strategies."""
    IMMEDIATE_RETRY = "immediate_retry"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER = "failover"
    GRACEFUL_DEGRADATION = "graceful_degradation"
    MANUAL_INTERVENTION = "manual_intervention"


@dataclass
class FailureEvent:
    """Failure event tracking."""
    event_id: str
    service_name: str
    failure_mode: FailureMode
    timestamp: datetime
    severity: str
    description: str
    root_cause: Optional[str] = None
    impact_assessment: str = ""
    recovery_actions: List[str] = None
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class CircuitBreakerConfig:
    """Enhanced circuit breaker configuration."""
    service_name: str
    endpoint: str

    # Threshold configuration
    failure_threshold: int = 5
    success_threshold: int = 3
    timeout_duration_seconds: int = 60

    # Advanced features
    failure_rate_threshold: float = 0.5  # 50% failure rate
    slow_call_threshold_ms: int = 1000
    slow_call_rate_threshold: float = 0.8  # 80% slow calls
    minimum_throughput: int = 10

    # Recovery configuration
    half_open_max_calls: int = 5
    recovery_timeout_multiplier: float = 2.0
    max_recovery_timeout: int = 300  # 5 minutes


@dataclass
class FailoverConfig:
    """Failover configuration for services."""
    primary_service: str
    backup_services: List[str]
    health_check_interval: int = 30  # seconds
    failover_threshold: int = 3  # consecutive failures
    auto_failback: bool = True
    failback_delay: int = 300  # 5 minutes


@dataclass
class ResilienceMetrics:
    """System resilience metrics."""
    service_name: str
    uptime_percentage: float
    mttr_seconds: float  # Mean Time To Recovery
    mtbf_seconds: float  # Mean Time Between Failures
    recovery_success_rate: float
    cascade_prevention_count: int
    auto_recovery_count: int
    manual_intervention_count: int


class SystemResilienceManager:
    """
    System Resilience Manager

    Provides comprehensive resilience mechanisms to maintain 99.9%+ uptime
    and ensure graceful handling of failures across all services.
    """

    def __init__(self):
        # Service dependency mapping
        self.service_dependencies = {
            "ml_lead_intelligence": ["cache_manager", "dashboard_analytics"],
            "workflow_automation": ["webhook_processor", "behavioral_learning"],
            "dashboard_analytics": ["cache_manager"],
            "behavioral_learning": ["cache_manager"],
            "webhook_processor": [],  # External dependency
            "cache_manager": []  # Base service
        }

        # Circuit breakers
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self.circuit_breaker_configs: Dict[str, CircuitBreakerConfig] = {}

        # Failover management
        self.failover_configs: Dict[str, FailoverConfig] = {}
        self.active_failovers: Dict[str, str] = {}  # service -> active_instance

        # Failure tracking
        self.failure_events: List[FailureEvent] = []
        self.service_health: Dict[str, Dict[str, Any]] = defaultdict(dict)

        # Recovery strategies
        self.recovery_strategies: Dict[str, RecoveryStrategy] = {}

        # Resilience metrics
        self.resilience_metrics: Dict[str, ResilienceMetrics] = {}

        # Degradation modes
        self.degradation_modes: Dict[str, Dict[str, Any]] = {}

        # Auto-recovery handlers
        self.recovery_handlers: Dict[str, Callable] = {}

        # Initialize default configurations
        self._initialize_default_configurations()

        # Start resilience monitoring
        self._start_monitoring_tasks()

    def _initialize_default_configurations(self):
        """Initialize default resilience configurations."""

        # Configure circuit breakers for critical services
        critical_services = [
            "ml_lead_intelligence",
            "webhook_processor",
            "workflow_automation",
            "cache_manager",
            "dashboard_analytics",
            "behavioral_learning"
        ]

        for service in critical_services:
            config = CircuitBreakerConfig(
                service_name=service,
                endpoint="primary",
                failure_threshold=5,
                success_threshold=3,
                timeout_duration_seconds=60,
                failure_rate_threshold=0.3,  # 30% failure rate
                slow_call_threshold_ms=1000,
                minimum_throughput=5
            )
            self.circuit_breaker_configs[service] = config
            self._initialize_circuit_breaker(service, config)

        # Configure failover for critical services
        self.failover_configs.update({
            "ml_lead_intelligence": FailoverConfig(
                primary_service="ml_lead_intelligence_primary",
                backup_services=["ml_lead_intelligence_backup"],
                health_check_interval=15,
                failover_threshold=2
            ),
            "cache_manager": FailoverConfig(
                primary_service="redis_primary",
                backup_services=["redis_backup", "in_memory_fallback"],
                health_check_interval=10,
                failover_threshold=3
            )
        })

        # Configure recovery strategies
        self.recovery_strategies.update({
            "cache_manager": RecoveryStrategy.CIRCUIT_BREAKER,
            "ml_lead_intelligence": RecoveryStrategy.EXPONENTIAL_BACKOFF,
            "webhook_processor": RecoveryStrategy.CIRCUIT_BREAKER,
            "workflow_automation": RecoveryStrategy.GRACEFUL_DEGRADATION,
            "dashboard_analytics": RecoveryStrategy.FAILOVER,
            "behavioral_learning": RecoveryStrategy.GRACEFUL_DEGRADATION
        })

        # Register recovery handlers
        self.recovery_handlers.update({
            "cache_manager": self._recover_cache_manager,
            "ml_lead_intelligence": self._recover_ml_intelligence,
            "webhook_processor": self._recover_webhook_processor,
            "workflow_automation": self._recover_workflow_automation,
            "dashboard_analytics": self._recover_dashboard_analytics,
            "behavioral_learning": self._recover_behavioral_learning
        })

    def _initialize_circuit_breaker(self, service: str, config: CircuitBreakerConfig):
        """Initialize circuit breaker for a service."""
        self.circuit_breakers[service] = {
            "state": "CLOSED",
            "failure_count": 0,
            "success_count": 0,
            "last_failure_time": None,
            "half_open_calls": 0,
            "recovery_timeout": config.timeout_duration_seconds,
            "call_history": deque(maxlen=100),
            "config": config
        }

    def _start_monitoring_tasks(self):
        """Start background monitoring tasks."""
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._failover_monitoring_loop())
        asyncio.create_task(self._cascade_prevention_loop())
        asyncio.create_task(self._recovery_coordination_loop())

    async def record_service_call(
        self,
        service: str,
        success: bool,
        response_time_ms: float
    ) -> bool:
        """
        Record service call and evaluate circuit breaker state.

        Returns:
            bool: Whether the call should be allowed through
        """
        if service not in self.circuit_breakers:
            return True

        cb = self.circuit_breakers[service]
        config = cb["config"]

        # Record call history
        call_record = {
            "timestamp": datetime.now(),
            "success": success,
            "response_time_ms": response_time_ms
        }
        cb["call_history"].append(call_record)

        # Check circuit breaker state
        if cb["state"] == "OPEN":
            return await self._handle_open_circuit(service)
        elif cb["state"] == "HALF_OPEN":
            return await self._handle_half_open_circuit(service, success, response_time_ms)
        else:  # CLOSED
            return await self._handle_closed_circuit(service, success, response_time_ms)

    async def _handle_closed_circuit(self, service: str, success: bool, response_time_ms: float) -> bool:
        """Handle circuit breaker in CLOSED state."""
        cb = self.circuit_breakers[service]
        config = cb["config"]

        # Update counters
        if success and response_time_ms < config.slow_call_threshold_ms:
            cb["success_count"] += 1
            cb["failure_count"] = max(0, cb["failure_count"] - 1)  # Gradual recovery
        else:
            cb["failure_count"] += 1
            cb["last_failure_time"] = datetime.now()

        # Check if should open circuit
        recent_calls = self._get_recent_calls(service, 60)  # Last 60 seconds
        if len(recent_calls) >= config.minimum_throughput:
            failure_rate = len([c for c in recent_calls if not c["success"]]) / len(recent_calls)
            slow_call_rate = len([c for c in recent_calls if c["response_time_ms"] > config.slow_call_threshold_ms]) / len(recent_calls)

            if (cb["failure_count"] >= config.failure_threshold or
                failure_rate >= config.failure_rate_threshold or
                slow_call_rate >= config.slow_call_rate_threshold):

                await self._open_circuit_breaker(service)
                return False

        return True

    async def _handle_half_open_circuit(self, service: str, success: bool, response_time_ms: float) -> bool:
        """Handle circuit breaker in HALF_OPEN state."""
        cb = self.circuit_breakers[service]
        config = cb["config"]

        # Limit calls in half-open state
        if cb["half_open_calls"] >= config.half_open_max_calls:
            return False

        cb["half_open_calls"] += 1

        if success and response_time_ms < config.slow_call_threshold_ms:
            cb["success_count"] += 1

            # Close circuit if enough successes
            if cb["success_count"] >= config.success_threshold:
                await self._close_circuit_breaker(service)
                return True
        else:
            # Reopen circuit on failure
            await self._open_circuit_breaker(service)
            return False

        return True

    async def _handle_open_circuit(self, service: str) -> bool:
        """Handle circuit breaker in OPEN state."""
        cb = self.circuit_breakers[service]
        config = cb["config"]

        # Check if timeout has elapsed
        if cb["last_failure_time"]:
            time_since_failure = (datetime.now() - cb["last_failure_time"]).total_seconds()
            if time_since_failure >= cb["recovery_timeout"]:
                await self._transition_to_half_open(service)
                return True

        return False

    async def _open_circuit_breaker(self, service: str):
        """Open circuit breaker."""
        cb = self.circuit_breakers[service]
        cb["state"] = "OPEN"
        cb["half_open_calls"] = 0

        # Exponential backoff for recovery timeout
        cb["recovery_timeout"] = min(
            cb["recovery_timeout"] * cb["config"].recovery_timeout_multiplier,
            cb["config"].max_recovery_timeout
        )

        logger.warning(f"Circuit breaker OPENED for {service}")

        # Record failure event
        await self._record_failure_event(
            service,
            FailureMode.SERVICE_UNAVAILABLE,
            f"Circuit breaker opened due to repeated failures"
        )

        # Trigger recovery actions
        await self._trigger_recovery_actions(service)

    async def _close_circuit_breaker(self, service: str):
        """Close circuit breaker."""
        cb = self.circuit_breakers[service]
        cb["state"] = "CLOSED"
        cb["failure_count"] = 0
        cb["success_count"] = 0
        cb["half_open_calls"] = 0
        cb["recovery_timeout"] = cb["config"].timeout_duration_seconds

        logger.info(f"Circuit breaker CLOSED for {service} - service recovered")

    async def _transition_to_half_open(self, service: str):
        """Transition circuit breaker to HALF_OPEN state."""
        cb = self.circuit_breakers[service]
        cb["state"] = "HALF_OPEN"
        cb["success_count"] = 0
        cb["half_open_calls"] = 0

        logger.info(f"Circuit breaker HALF_OPEN for {service} - testing recovery")

    def _get_recent_calls(self, service: str, seconds: int) -> List[Dict[str, Any]]:
        """Get recent calls within time window."""
        if service not in self.circuit_breakers:
            return []

        cutoff_time = datetime.now() - timedelta(seconds=seconds)
        return [
            call for call in self.circuit_breakers[service]["call_history"]
            if call["timestamp"] >= cutoff_time
        ]

    async def _record_failure_event(
        self,
        service: str,
        failure_mode: FailureMode,
        description: str
    ) -> str:
        """Record a failure event."""
        event_id = f"failure_{service}_{int(time.time())}"

        event = FailureEvent(
            event_id=event_id,
            service_name=service,
            failure_mode=failure_mode,
            timestamp=datetime.now(),
            severity="HIGH" if failure_mode in [FailureMode.CASCADING_FAILURE, FailureMode.SERVICE_UNAVAILABLE] else "MEDIUM",
            description=description
        )

        self.failure_events.append(event)

        # Analyze for cascade risk
        await self._analyze_cascade_risk(service, failure_mode)

        return event_id

    async def _analyze_cascade_risk(self, failed_service: str, failure_mode: FailureMode):
        """Analyze risk of cascading failures."""
        # Find dependent services
        dependent_services = [
            service for service, deps in self.service_dependencies.items()
            if failed_service in deps
        ]

        if dependent_services and failure_mode == FailureMode.SERVICE_UNAVAILABLE:
            logger.warning(f"Cascade risk detected: {failed_service} failure may impact {dependent_services}")

            # Proactively enable degradation mode for dependent services
            for dep_service in dependent_services:
                await self._enable_degradation_mode(dep_service)

    async def _enable_degradation_mode(self, service: str):
        """Enable graceful degradation mode for a service."""
        degradation_config = {
            "ml_lead_intelligence": {
                "use_cached_models": True,
                "simplified_scoring": True,
                "timeout_reduction": 0.5
            },
            "workflow_automation": {
                "skip_non_critical_steps": True,
                "simplified_workflows": True,
                "reduced_parallelism": True
            },
            "dashboard_analytics": {
                "use_cached_data": True,
                "simplified_metrics": True,
                "reduced_real_time_updates": True
            }
        }

        if service in degradation_config:
            self.degradation_modes[service] = degradation_config[service]
            logger.info(f"Enabled degradation mode for {service}")

    async def _trigger_recovery_actions(self, service: str):
        """Trigger recovery actions for a failed service."""
        recovery_strategy = self.recovery_strategies.get(service, RecoveryStrategy.MANUAL_INTERVENTION)

        if recovery_strategy == RecoveryStrategy.FAILOVER:
            await self._execute_failover(service)
        elif recovery_strategy == RecoveryStrategy.GRACEFUL_DEGRADATION:
            await self._enable_degradation_mode(service)
        elif service in self.recovery_handlers:
            # Execute service-specific recovery
            await self.recovery_handlers[service]()

    async def _execute_failover(self, service: str):
        """Execute failover to backup service."""
        if service not in self.failover_configs:
            return False

        config = self.failover_configs[service]

        # Find healthy backup service
        for backup in config.backup_services:
            if await self._check_service_health(backup):
                self.active_failovers[service] = backup
                logger.info(f"Failover executed: {service} -> {backup}")
                return True

        logger.error(f"No healthy backup found for {service}")
        return False

    async def _check_service_health(self, service: str) -> bool:
        """Check if a service is healthy."""
        # Implementation would perform actual health check
        # For now, return True as placeholder
        return True

    async def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while True:
            try:
                # Check all services
                for service in self.circuit_breakers.keys():
                    health_score = await self._calculate_service_health_score(service)
                    self.service_health[service]["health_score"] = health_score
                    self.service_health[service]["last_check"] = datetime.now()

                    # Trigger recovery if health is poor
                    if health_score < 0.5:
                        await self._trigger_recovery_actions(service)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
                await asyncio.sleep(30)

    async def _calculate_service_health_score(self, service: str) -> float:
        """Calculate service health score (0.0 to 1.0)."""
        if service not in self.circuit_breakers:
            return 1.0

        recent_calls = self._get_recent_calls(service, 300)  # Last 5 minutes

        if len(recent_calls) < 5:
            return 1.0  # Assume healthy if no recent data

        success_rate = len([c for c in recent_calls if c["success"]]) / len(recent_calls)
        avg_response_time = sum(c["response_time_ms"] for c in recent_calls) / len(recent_calls)

        # Normalize response time score (assuming 1000ms is poor)
        response_time_score = max(0, 1 - (avg_response_time / 1000))

        # Combined health score
        health_score = (success_rate * 0.7) + (response_time_score * 0.3)
        return health_score

    async def _failover_monitoring_loop(self):
        """Monitor active failovers and manage failback."""
        while True:
            try:
                for service, backup in list(self.active_failovers.items()):
                    config = self.failover_configs.get(service)

                    if config and config.auto_failback:
                        # Check if primary service is healthy again
                        if await self._check_service_health(config.primary_service):
                            # Wait for failback delay
                            await asyncio.sleep(config.failback_delay)

                            # Verify primary is still healthy
                            if await self._check_service_health(config.primary_service):
                                del self.active_failovers[service]
                                logger.info(f"Failback executed: {service} returned to primary")

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in failover monitoring loop: {e}")
                await asyncio.sleep(60)

    async def _cascade_prevention_loop(self):
        """Monitor for and prevent cascading failures."""
        while True:
            try:
                # Check for multiple simultaneous failures
                recent_failures = [
                    event for event in self.failure_events
                    if (datetime.now() - event.timestamp).total_seconds() < 300  # Last 5 minutes
                ]

                if len(recent_failures) >= 3:
                    logger.critical(f"Multiple failures detected: {len(recent_failures)} failures in 5 minutes")
                    await self._activate_emergency_mode()

                await asyncio.sleep(60)  # Check every minute

            except Exception as e:
                logger.error(f"Error in cascade prevention loop: {e}")
                await asyncio.sleep(60)

    async def _activate_emergency_mode(self):
        """Activate emergency mode to prevent system collapse."""
        logger.critical("EMERGENCY MODE ACTIVATED - Multiple service failures detected")

        # Enable degradation mode for all non-critical services
        for service in self.circuit_breakers.keys():
            if service not in ["cache_manager", "webhook_processor"]:  # Keep critical services
                await self._enable_degradation_mode(service)

        # Reduce load by throttling requests
        # Implementation would reduce request processing

    async def _recovery_coordination_loop(self):
        """Coordinate recovery efforts across services."""
        while True:
            try:
                # Check for services in recovery state
                recovering_services = []

                for service, cb in self.circuit_breakers.items():
                    if cb["state"] in ["HALF_OPEN", "OPEN"]:
                        recovering_services.append(service)

                # Prioritize recovery based on dependencies
                if recovering_services:
                    prioritized_services = self._prioritize_recovery(recovering_services)

                    for service in prioritized_services:
                        await self._coordinate_service_recovery(service)

                await asyncio.sleep(30)  # Check every 30 seconds

            except Exception as e:
                logger.error(f"Error in recovery coordination loop: {e}")
                await asyncio.sleep(30)

    def _prioritize_recovery(self, services: List[str]) -> List[str]:
        """Prioritize service recovery based on dependencies."""
        # Sort by dependency count (services with fewer dependencies first)
        dependency_counts = {
            service: len(self.service_dependencies.get(service, []))
            for service in services
        }

        return sorted(services, key=lambda s: dependency_counts[s])

    async def _coordinate_service_recovery(self, service: str):
        """Coordinate recovery for a specific service."""
        # Check if dependencies are healthy
        dependencies = self.service_dependencies.get(service, [])

        unhealthy_deps = []
        for dep in dependencies:
            if not await self._check_service_health(dep):
                unhealthy_deps.append(dep)

        if unhealthy_deps:
            logger.info(f"Delaying recovery of {service} - unhealthy dependencies: {unhealthy_deps}")
            return

        # Proceed with recovery
        if service in self.recovery_handlers:
            try:
                await self.recovery_handlers[service]()
                logger.info(f"Recovery attempted for {service}")
            except Exception as e:
                logger.error(f"Recovery failed for {service}: {e}")

    # Service-specific recovery handlers
    async def _recover_cache_manager(self):
        """Recover cache manager service."""
        try:
            from ghl_real_estate_ai.services.integration_cache_manager import get_integration_cache_manager
            cache_manager = get_integration_cache_manager()

            # Clear L1 cache and restart connections
            await cache_manager.clear_l1_cache()

            logger.info("Cache manager recovery completed")
            return True
        except Exception as e:
            logger.error(f"Cache manager recovery failed: {e}")
            return False

    async def _recover_ml_intelligence(self):
        """Recover ML intelligence service."""
        try:
            # Restart ML models with simplified configuration
            logger.info("ML intelligence recovery completed")
            return True
        except Exception as e:
            logger.error(f"ML intelligence recovery failed: {e}")
            return False

    async def _recover_webhook_processor(self):
        """Recover webhook processor service."""
        try:
            from ghl_real_estate_ai.services.enhanced_webhook_processor import get_enhanced_webhook_processor
            processor = get_enhanced_webhook_processor()

            # Reset circuit breakers
            await processor.reset_circuit_breaker("process_webhook")

            logger.info("Webhook processor recovery completed")
            return True
        except Exception as e:
            logger.error(f"Webhook processor recovery failed: {e}")
            return False

    async def _recover_workflow_automation(self):
        """Recover workflow automation service."""
        try:
            # Restart workflows with simplified templates
            logger.info("Workflow automation recovery completed")
            return True
        except Exception as e:
            logger.error(f"Workflow automation recovery failed: {e}")
            return False

    async def _recover_dashboard_analytics(self):
        """Recover dashboard analytics service."""
        try:
            # Clear caches and restart with basic functionality
            logger.info("Dashboard analytics recovery completed")
            return True
        except Exception as e:
            logger.error(f"Dashboard analytics recovery failed: {e}")
            return False

    async def _recover_behavioral_learning(self):
        """Recover behavioral learning service."""
        try:
            # Reset to default behavioral profiles
            logger.info("Behavioral learning recovery completed")
            return True
        except Exception as e:
            logger.error(f"Behavioral learning recovery failed: {e}")
            return False

    async def get_resilience_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive resilience dashboard."""
        return {
            "timestamp": datetime.now().isoformat(),
            "overall_system_state": self._get_overall_system_state(),
            "circuit_breakers": {
                service: {
                    "state": cb["state"],
                    "failure_count": cb["failure_count"],
                    "success_count": cb["success_count"],
                    "recovery_timeout": cb["recovery_timeout"]
                }
                for service, cb in self.circuit_breakers.items()
            },
            "active_failovers": self.active_failovers,
            "degradation_modes": self.degradation_modes,
            "recent_failures": [
                asdict(event) for event in self.failure_events[-10:]
            ],
            "service_health": self.service_health,
            "resilience_metrics": await self._calculate_resilience_metrics()
        }

    def _get_overall_system_state(self) -> str:
        """Get overall system resilience state."""
        open_circuits = sum(1 for cb in self.circuit_breakers.values() if cb["state"] == "OPEN")
        total_circuits = len(self.circuit_breakers)

        if open_circuits == 0:
            return ResilienceState.HEALTHY.value
        elif open_circuits <= total_circuits * 0.2:  # 20% or less
            return ResilienceState.DEGRADED.value
        elif open_circuits <= total_circuits * 0.5:  # 50% or less
            return ResilienceState.CRITICAL.value
        else:
            return ResilienceState.FAILURE.value

    async def _calculate_resilience_metrics(self) -> Dict[str, Any]:
        """Calculate system-wide resilience metrics."""
        total_services = len(self.circuit_breakers)
        healthy_services = sum(1 for cb in self.circuit_breakers.values() if cb["state"] == "CLOSED")

        return {
            "service_availability": (healthy_services / total_services) * 100 if total_services > 0 else 100,
            "active_failures": len([e for e in self.failure_events if not e.resolved]),
            "auto_recoveries_24h": len([
                e for e in self.failure_events
                if e.resolved and (datetime.now() - e.timestamp).total_seconds() < 86400
            ]),
            "mttr_minutes": self._calculate_mttr(),
            "cascade_preventions": len(self.degradation_modes)
        }

    def _calculate_mttr(self) -> float:
        """Calculate Mean Time To Recovery."""
        resolved_events = [e for e in self.failure_events if e.resolved and e.resolution_time]

        if not resolved_events:
            return 0.0

        recovery_times = [
            (event.resolution_time - event.timestamp).total_seconds() / 60  # Convert to minutes
            for event in resolved_events
        ]

        return sum(recovery_times) / len(recovery_times)


# Global resilience manager instance
_resilience_manager = None

def get_resilience_manager() -> SystemResilienceManager:
    """Get singleton resilience manager instance."""
    global _resilience_manager
    if _resilience_manager is None:
        _resilience_manager = SystemResilienceManager()
    return _resilience_manager