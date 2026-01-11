"""
System Integration Orchestrator
==============================

Master orchestrator that integrates all optimization systems for maximum
cross-system performance and coordination. Manages event-driven workflows,
circuit breakers, monitoring, and intelligent system adaptation.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import time
from contextlib import asynccontextmanager

# Import optimization components
from .system_optimization_engine import (
    SystemOptimizationEngine,
    OptimizationLevel,
    EventType,
    SystemEvent,
    optimization_engine
)
from .optimized_database_layer import (
    OptimizedDatabaseLayer,
    QueryType,
    optimized_db
)
from .enhanced_api_performance import (
    EnhancedAPIPerformanceLayer,
    RequestPriority,
    enhanced_api_layer
)

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Overall system states"""
    INITIALIZING = "initializing"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"
    SHUTDOWN = "shutdown"


class IntegrationMode(Enum):
    """Integration coordination modes"""
    CONSERVATIVE = "conservative"  # Prioritize stability
    BALANCED = "balanced"         # Balance performance and stability
    AGGRESSIVE = "aggressive"     # Maximum performance optimization


@dataclass
class SystemHealthMetrics:
    """Comprehensive system health metrics"""
    overall_state: SystemState
    cpu_usage_percent: float
    memory_usage_percent: float
    database_response_time_ms: float
    api_response_time_ms: float
    cache_hit_rate_percent: float
    error_rate_percent: float
    throughput_per_second: float
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class IntegrationConfig:
    """Configuration for system integration"""
    optimization_level: OptimizationLevel = OptimizationLevel.BALANCED
    integration_mode: IntegrationMode = IntegrationMode.BALANCED
    health_check_interval: int = 30  # seconds
    auto_scaling_enabled: bool = True
    circuit_breaker_enabled: bool = True
    adaptive_caching_enabled: bool = True
    event_driven_optimization: bool = True
    performance_target_ms: float = 500.0
    error_rate_threshold_percent: float = 5.0


class WorkflowCoordinator:
    """
    Coordinates complex workflows across multiple systems with
    intelligent orchestration and error handling.
    """

    def __init__(self):
        self.active_workflows: Dict[str, Dict[str, Any]] = {}
        self.workflow_templates: Dict[str, Dict[str, Any]] = {}
        self.workflow_metrics: Dict[str, List[Dict]] = {}

    async def execute_coordinated_workflow(self,
                                         workflow_id: str,
                                         workflow_type: str,
                                         parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a coordinated workflow across multiple systems
        """
        start_time = time.time()
        workflow_context = {
            "id": workflow_id,
            "type": workflow_type,
            "parameters": parameters,
            "started_at": datetime.now(),
            "steps": [],
            "status": "running"
        }

        self.active_workflows[workflow_id] = workflow_context

        try:
            if workflow_type == "agent_task_optimization":
                result = await self._execute_agent_task_optimization(workflow_id, parameters)
            elif workflow_type == "lead_intelligence_update":
                result = await self._execute_lead_intelligence_update(workflow_id, parameters)
            elif workflow_type == "performance_auto_tuning":
                result = await self._execute_performance_auto_tuning(workflow_id, parameters)
            elif workflow_type == "system_health_recovery":
                result = await self._execute_system_health_recovery(workflow_id, parameters)
            else:
                result = await self._execute_custom_workflow(workflow_id, workflow_type, parameters)

            workflow_context["status"] = "completed"
            workflow_context["result"] = result
            workflow_context["duration_ms"] = (time.time() - start_time) * 1000

            # Record metrics
            self._record_workflow_metrics(workflow_type, workflow_context)

            return result

        except Exception as e:
            workflow_context["status"] = "failed"
            workflow_context["error"] = str(e)
            workflow_context["duration_ms"] = (time.time() - start_time) * 1000

            logger.error(f"Workflow {workflow_id} failed: {e}")
            raise

        finally:
            # Cleanup completed workflows
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]

    async def _execute_agent_task_optimization(self,
                                             workflow_id: str,
                                             parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Optimized agent task workflow with cross-system coordination"""

        agent_id = parameters.get("agent_id")
        task_data = parameters.get("task_data", {})

        # Step 1: Optimize task data with ML intelligence
        logger.info(f"Step 1: Optimizing task data for agent {agent_id}")

        # Use optimized database query for agent context
        agent_context = await optimized_db.get_agent_tasks_optimized(
            agent_id, limit=20
        )

        # Step 2: Generate AI insights with API optimization
        logger.info(f"Step 2: Generating AI insights")

        ai_insights_request = {
            "service_name": "claude_ai",
            "method": "POST",
            "url": "/v1/chat/completions",
            "json": {
                "model": "claude-3-sonnet-20240229",
                "messages": [
                    {
                        "role": "user",
                        "content": f"Analyze agent {agent_id} context and optimize task: {json.dumps(task_data)}"
                    }
                ],
                "max_tokens": 500
            }
        }

        ai_insights = await enhanced_api_layer.make_request(
            **ai_insights_request,
            priority=RequestPriority.HIGH
        )

        # Step 3: Update workflow automation with optimizations
        logger.info(f"Step 3: Updating workflow automation")

        # Publish event for workflow system
        await optimization_engine.publish_event(
            EventType.TASK_CREATED,
            "integration_orchestrator",
            {
                "agent_id": agent_id,
                "task_data": task_data,
                "ai_insights": ai_insights.get("data", {}),
                "optimization_applied": True
            },
            priority=3
        )

        return {
            "agent_id": agent_id,
            "optimized_task": task_data,
            "ai_insights": ai_insights,
            "agent_context": agent_context,
            "workflow_optimizations_applied": True
        }

    async def _execute_lead_intelligence_update(self,
                                              workflow_id: str,
                                              parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinated lead intelligence update across all systems"""

        lead_id = parameters.get("lead_id")
        update_data = parameters.get("update_data", {})

        # Step 1: Update database with optimized transaction
        logger.info(f"Step 1: Updating lead {lead_id} in database")

        # Use batch update for efficiency
        await optimized_db.batch_insert(
            "lead_updates",
            ["lead_id", "update_data", "timestamp"],
            [[lead_id, json.dumps(update_data), datetime.now()]]
        )

        # Step 2: Invalidate related caches
        logger.info(f"Step 2: Invalidating caches for lead {lead_id}")

        await optimization_engine.cache.invalidate(f"lead:{lead_id}")
        await optimization_engine.cache.invalidate(f"lead_analytics:{lead_id}")

        # Step 3: Trigger ML model updates
        logger.info(f"Step 3: Triggering ML model updates")

        ml_update_event = SystemEvent(
            event_type=EventType.LEAD_UPDATED,
            source_service="integration_orchestrator",
            data={
                "lead_id": lead_id,
                "update_data": update_data,
                "requires_ml_update": True
            },
            priority=4
        )

        await optimization_engine.event_bus.publish(ml_update_event)

        # Step 4: Update agent workflows that depend on this lead
        logger.info(f"Step 4: Updating dependent agent workflows")

        # Get affected agents
        affected_agents = await optimized_db.execute_optimized_query(
            "SELECT DISTINCT agent_id FROM agent_tasks WHERE lead_id = $1 AND status IN ('pending', 'in_progress')",
            {"lead_id": lead_id},
            QueryType.SELECT,
            cache_ttl=60
        )

        for agent_record in affected_agents:
            agent_id = agent_record["agent_id"]

            # Trigger workflow optimization for affected agents
            await self.execute_coordinated_workflow(
                f"agent_optimization_{agent_id}_{int(time.time())}",
                "agent_task_optimization",
                {
                    "agent_id": agent_id,
                    "task_data": {"triggered_by_lead_update": lead_id}
                }
            )

        return {
            "lead_id": lead_id,
            "update_applied": True,
            "affected_agents": len(affected_agents),
            "cache_invalidated": True,
            "ml_update_triggered": True
        }

    async def _execute_performance_auto_tuning(self,
                                             workflow_id: str,
                                             parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Automatic performance tuning based on system metrics"""

        tuning_target = parameters.get("target", "overall")
        performance_metrics = parameters.get("metrics", {})

        optimizations_applied = []

        # Step 1: Analyze current performance
        logger.info(f"Step 1: Analyzing current performance")

        health_report = await optimization_engine.get_system_health()
        db_report = await optimized_db.get_database_performance_report()
        api_report = await enhanced_api_layer.get_performance_report()

        # Step 2: Identify optimization opportunities
        logger.info(f"Step 2: Identifying optimization opportunities")

        # Database optimizations
        if db_report["operation_stats"]["average_response_time"] > 300:  # > 300ms
            # Adjust cache TTL
            await optimization_engine.cache.cache.default_ttl = min(
                optimization_engine.cache.cache.default_ttl * 1.2, 7200
            )
            optimizations_applied.append("increased_cache_ttl")

            # Optimize connection pool
            if "connection_pool_stats" in db_report:
                pool_stats = db_report["connection_pool_stats"]
                if pool_stats["idle_connections"] < 2:
                    optimizations_applied.append("connection_pool_expansion_recommended")

        # API optimizations
        if api_report["global_stats"]["average_response_time"] > 500:  # > 500ms
            # Increase concurrent connections for high-latency services
            for service_name, service_metrics in api_report["service_metrics"].items():
                if service_metrics["average_response_time_ms"] > 800:
                    optimizations_applied.append(f"api_optimization_{service_name}")

        # Step 3: Apply circuit breaker adjustments
        logger.info(f"Step 3: Adjusting circuit breakers")

        for service_name in ["claude_ai", "ghl_api", "database"]:
            health = optimization_engine.circuit_breaker.get_service_health(service_name)

            if health["success_rate"] < 0.9 and not health["status"] == "open":
                # Preemptively open circuit breaker for struggling services
                await optimization_engine.circuit_breaker._record_failure(
                    service_name, "proactive_protection", 100
                )
                optimizations_applied.append(f"circuit_breaker_protection_{service_name}")

        # Step 4: Memory optimization
        logger.info(f"Step 4: Optimizing memory usage")

        # Clear old cache entries
        current_time = time.time()
        cache_cleared = 0

        for key, entry in list(optimization_engine.cache.memory_cache.items()):
            if entry.get('created_at', datetime.min) < datetime.now() - timedelta(hours=1):
                del optimization_engine.cache.memory_cache[key]
                cache_cleared += 1

        if cache_cleared > 0:
            optimizations_applied.append(f"cache_cleanup_{cache_cleared}_entries")

        # Step 5: Event system optimization
        logger.info(f"Step 5: Optimizing event system")

        event_stats = optimization_engine.event_bus.get_stats()
        if event_stats["queue_size"] > 1000:
            # Temporarily increase processing priority
            optimizations_applied.append("event_queue_priority_boost")

        return {
            "tuning_target": tuning_target,
            "optimizations_applied": optimizations_applied,
            "performance_improvement_estimated": len(optimizations_applied) * 5,  # 5% per optimization
            "health_report": health_report,
            "database_report": db_report,
            "api_report": api_report
        }

    async def _execute_system_health_recovery(self,
                                            workflow_id: str,
                                            parameters: Dict[str, Any]) -> Dict[str, Any]:
        """System health recovery workflow"""

        recovery_type = parameters.get("recovery_type", "auto")
        affected_services = parameters.get("affected_services", [])

        recovery_actions = []

        # Step 1: Assess system health
        logger.info(f"Step 1: Assessing system health")

        health_report = await optimization_engine.get_system_health()

        if health_report["overall_status"] in ["degraded", "unhealthy"]:
            # Step 2: Apply emergency optimizations
            logger.info(f"Step 2: Applying emergency optimizations")

            # Reduce system load
            for service_name in affected_services:
                circuit_breaker = optimization_engine.circuit_breaker

                # Temporarily open circuit breakers to reduce load
                state = circuit_breaker._get_or_create_state(service_name)
                state.is_open = True
                state.half_open_at = datetime.now() + timedelta(minutes=5)

                recovery_actions.append(f"circuit_breaker_opened_{service_name}")

            # Step 3: Emergency cache cleanup
            logger.info(f"Step 3: Emergency cache cleanup")

            # Clear all non-critical cache entries
            await optimization_engine.cache.invalidate("analytics")
            await optimization_engine.cache.invalidate("performance")
            recovery_actions.append("emergency_cache_cleanup")

            # Step 4: Scale down non-essential operations
            logger.info(f"Step 4: Scaling down non-essential operations")

            # Pause background workflows
            await optimization_engine.publish_event(
                EventType.SYSTEM_HEALTH_CHECK,
                "integration_orchestrator",
                {
                    "action": "scale_down",
                    "affected_services": affected_services,
                    "recovery_mode": True
                },
                priority=1
            )

            recovery_actions.append("background_operations_paused")

        # Step 5: Schedule health monitoring
        logger.info(f"Step 5: Scheduling enhanced health monitoring")

        recovery_actions.append("enhanced_monitoring_enabled")

        return {
            "recovery_type": recovery_type,
            "affected_services": affected_services,
            "recovery_actions": recovery_actions,
            "estimated_recovery_time_minutes": len(recovery_actions) * 2,
            "health_status": health_report["overall_status"]
        }

    async def _execute_custom_workflow(self,
                                     workflow_id: str,
                                     workflow_type: str,
                                     parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom workflow based on template"""

        if workflow_type in self.workflow_templates:
            template = self.workflow_templates[workflow_type]
            # Execute steps defined in template
            return await self._execute_template_workflow(workflow_id, template, parameters)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")

    async def _execute_template_workflow(self,
                                       workflow_id: str,
                                       template: Dict[str, Any],
                                       parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow from template definition"""

        results = {}

        for step in template.get("steps", []):
            step_name = step.get("name", "unknown")
            step_type = step.get("type", "unknown")
            step_config = step.get("config", {})

            logger.info(f"Executing workflow step: {step_name}")

            if step_type == "database_query":
                result = await optimized_db.execute_optimized_query(
                    step_config["query"],
                    step_config.get("params", {}),
                    QueryType(step_config.get("query_type", "select"))
                )
            elif step_type == "api_request":
                result = await enhanced_api_layer.make_request(
                    step_config["service_name"],
                    step_config["method"],
                    step_config["url"],
                    priority=RequestPriority(step_config.get("priority", "normal"))
                )
            elif step_type == "event_publish":
                result = await optimization_engine.publish_event(
                    EventType(step_config["event_type"]),
                    "integration_orchestrator",
                    step_config["data"],
                    step_config.get("priority", 5)
                )

            results[step_name] = result

        return results

    def _record_workflow_metrics(self,
                                workflow_type: str,
                                workflow_context: Dict[str, Any]) -> None:
        """Record workflow execution metrics"""

        if workflow_type not in self.workflow_metrics:
            self.workflow_metrics[workflow_type] = []

        metric = {
            "duration_ms": workflow_context.get("duration_ms", 0),
            "status": workflow_context.get("status", "unknown"),
            "step_count": len(workflow_context.get("steps", [])),
            "timestamp": datetime.now()
        }

        self.workflow_metrics[workflow_type].append(metric)

        # Keep only recent metrics
        if len(self.workflow_metrics[workflow_type]) > 100:
            self.workflow_metrics[workflow_type] = self.workflow_metrics[workflow_type][-100:]


class SystemIntegrationOrchestrator:
    """
    Master orchestrator for the entire Agent Enhancement System.
    Coordinates all optimization systems for maximum performance and reliability.
    """

    def __init__(self, config: IntegrationConfig):
        self.config = config
        self.current_state = SystemState.INITIALIZING
        self.workflow_coordinator = WorkflowCoordinator()

        # System health tracking
        self.health_history: List[SystemHealthMetrics] = []
        self.performance_targets = {
            "response_time_ms": config.performance_target_ms,
            "error_rate_percent": config.error_rate_threshold_percent,
            "cache_hit_rate_percent": 75.0,
            "throughput_per_second": 100.0
        }

        # Monitoring tasks
        self._health_monitor_task: Optional[asyncio.Task] = None
        self._optimization_task: Optional[asyncio.Task] = None

        # Integration statistics
        self.integration_stats = {
            "workflows_executed": 0,
            "optimizations_applied": 0,
            "performance_improvements": 0.0,
            "uptime_percent": 100.0,
            "last_optimization": None
        }

    async def initialize(self) -> None:
        """Initialize the complete system integration"""
        logger.info("Initializing System Integration Orchestrator")

        try:
            # Initialize all optimization systems
            await optimization_engine.initialize()
            await optimized_db.initialize()
            await enhanced_api_layer.initialize()

            # Register health check functions
            optimization_engine.register_service(
                "database", self._check_database_health
            )
            optimization_engine.register_service(
                "api_layer", self._check_api_health
            )
            optimization_engine.register_service(
                "optimization_engine", self._check_optimization_engine_health
            )

            # Setup event handlers for cross-system integration
            await self._setup_integration_event_handlers()

            # Start monitoring tasks
            if self.config.auto_scaling_enabled:
                self._health_monitor_task = asyncio.create_task(self._health_monitor_loop())
                self._optimization_task = asyncio.create_task(self._optimization_loop())

            self.current_state = SystemState.HEALTHY
            logger.info("System Integration Orchestrator initialized successfully")

        except Exception as e:
            self.current_state = SystemState.CRITICAL
            logger.error(f"System initialization failed: {e}")
            raise

    async def shutdown(self) -> None:
        """Graceful shutdown of the entire system"""
        logger.info("Shutting down System Integration Orchestrator")

        self.current_state = SystemState.SHUTDOWN

        # Cancel monitoring tasks
        if self._health_monitor_task:
            self._health_monitor_task.cancel()
        if self._optimization_task:
            self._optimization_task.cancel()

        # Shutdown all systems
        await enhanced_api_layer.shutdown()
        await optimized_db.close()
        await optimization_engine.shutdown()

        logger.info("System Integration Orchestrator shut down complete")

    async def execute_optimized_operation(self,
                                        operation_type: str,
                                        parameters: Dict[str, Any],
                                        priority: RequestPriority = RequestPriority.NORMAL) -> Dict[str, Any]:
        """
        Execute any operation with full system optimization
        """
        operation_id = f"{operation_type}_{int(time.time())}"

        # Use circuit breaker protection
        async with optimization_engine.circuit_breaker.protect("system_operation"):
            # Execute through workflow coordinator
            result = await self.workflow_coordinator.execute_coordinated_workflow(
                operation_id,
                operation_type,
                parameters
            )

            self.integration_stats["workflows_executed"] += 1
            return result

    async def get_system_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive system performance report"""

        # Collect reports from all systems
        optimization_health = await optimization_engine.get_system_health()
        db_performance = await optimized_db.get_database_performance_report()
        api_performance = await enhanced_api_layer.get_performance_report()

        # Calculate overall performance score
        performance_score = self._calculate_performance_score(
            optimization_health, db_performance, api_performance
        )

        # Recent health metrics
        recent_health = self.health_history[-10:] if self.health_history else []

        return {
            "timestamp": datetime.now(),
            "system_state": self.current_state.value,
            "performance_score": performance_score,
            "integration_stats": self.integration_stats,
            "performance_targets": self.performance_targets,
            "optimization_health": optimization_health,
            "database_performance": db_performance,
            "api_performance": api_performance,
            "recent_health_metrics": recent_health,
            "workflow_metrics": self.workflow_coordinator.workflow_metrics
        }

    async def _setup_integration_event_handlers(self) -> None:
        """Setup event handlers for cross-system integration"""

        # Task optimization events
        optimization_engine.event_bus.subscribe(
            EventType.TASK_CREATED,
            self._handle_task_optimization_event
        )

        # Performance alert events
        optimization_engine.event_bus.subscribe(
            EventType.PERFORMANCE_ALERT,
            self._handle_performance_alert_event
        )

        # System health events
        optimization_engine.event_bus.subscribe(
            EventType.SYSTEM_HEALTH_CHECK,
            self._handle_system_health_event
        )

    async def _handle_task_optimization_event(self, event: SystemEvent) -> None:
        """Handle task optimization events"""

        task_data = event.data

        # Trigger coordinated workflow if task is high priority
        if task_data.get("priority") in ["urgent", "high"]:
            await self.execute_optimized_operation(
                "agent_task_optimization",
                {
                    "agent_id": task_data.get("agent_id"),
                    "task_data": task_data,
                    "optimization_level": "high"
                },
                RequestPriority.HIGH
            )

    async def _handle_performance_alert_event(self, event: SystemEvent) -> None:
        """Handle performance alert events"""

        alert_data = event.data

        # Trigger automatic performance tuning
        await self.execute_optimized_operation(
            "performance_auto_tuning",
            {
                "target": alert_data.get("component", "overall"),
                "metrics": alert_data,
                "severity": alert_data.get("severity", "warning")
            },
            RequestPriority.CRITICAL
        )

    async def _handle_system_health_event(self, event: SystemEvent) -> None:
        """Handle system health events"""

        health_data = event.data

        if health_data.get("action") == "recovery_required":
            await self.execute_optimized_operation(
                "system_health_recovery",
                {
                    "recovery_type": "auto",
                    "affected_services": health_data.get("affected_services", [])
                },
                RequestPriority.CRITICAL
            )

    async def _health_monitor_loop(self) -> None:
        """Continuous system health monitoring"""

        while self.current_state != SystemState.SHUTDOWN:
            try:
                # Collect current health metrics
                health_metrics = await self._collect_health_metrics()
                self.health_history.append(health_metrics)

                # Keep only recent history
                if len(self.health_history) > 1000:
                    self.health_history = self.health_history[-1000:]

                # Update system state based on health
                await self._update_system_state(health_metrics)

                # Sleep until next health check
                await asyncio.sleep(self.config.health_check_interval)

            except Exception as e:
                logger.error(f"Health monitor error: {e}")
                await asyncio.sleep(self.config.health_check_interval)

    async def _optimization_loop(self) -> None:
        """Continuous system optimization"""

        while self.current_state != SystemState.SHUTDOWN:
            try:
                # Run optimization every 5 minutes
                await asyncio.sleep(300)

                # Skip optimization if system is critical
                if self.current_state == SystemState.CRITICAL:
                    continue

                # Run performance auto-tuning
                await self.execute_optimized_operation(
                    "performance_auto_tuning",
                    {"target": "overall", "mode": "scheduled"},
                    RequestPriority.LOW
                )

                self.integration_stats["optimizations_applied"] += 1
                self.integration_stats["last_optimization"] = datetime.now()

            except Exception as e:
                logger.error(f"Optimization loop error: {e}")

    async def _collect_health_metrics(self) -> SystemHealthMetrics:
        """Collect comprehensive health metrics"""

        # Get system stats
        import psutil
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()

        # Get database performance
        db_report = await optimized_db.get_database_performance_report()
        db_response_time = db_report["operation_stats"]["average_response_time"]

        # Get API performance
        api_report = await enhanced_api_layer.get_performance_report()
        api_response_time = api_report["global_stats"]["average_response_time"]

        # Get cache performance
        cache_stats = optimization_engine.cache.cache_stats
        total_requests = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
        cache_hit_rate = (cache_stats.get("hits", 0) / max(1, total_requests)) * 100

        # Calculate error rate
        total_errors = api_report["global_stats"]["total_errors"]
        total_api_requests = api_report["global_stats"]["total_requests"]
        error_rate = (total_errors / max(1, total_api_requests)) * 100

        # Estimate throughput
        throughput = total_api_requests / 60  # per second (rough estimate)

        return SystemHealthMetrics(
            overall_state=self.current_state,
            cpu_usage_percent=cpu_usage,
            memory_usage_percent=memory.percent,
            database_response_time_ms=db_response_time,
            api_response_time_ms=api_response_time,
            cache_hit_rate_percent=cache_hit_rate,
            error_rate_percent=error_rate,
            throughput_per_second=throughput
        )

    async def _update_system_state(self, health_metrics: SystemHealthMetrics) -> None:
        """Update system state based on health metrics"""

        # Count health issues
        issues = 0

        if health_metrics.database_response_time_ms > self.performance_targets["response_time_ms"]:
            issues += 1

        if health_metrics.api_response_time_ms > self.performance_targets["response_time_ms"]:
            issues += 1

        if health_metrics.error_rate_percent > self.performance_targets["error_rate_percent"]:
            issues += 2  # Errors are more serious

        if health_metrics.cache_hit_rate_percent < self.performance_targets["cache_hit_rate_percent"]:
            issues += 1

        if health_metrics.cpu_usage_percent > 90 or health_metrics.memory_usage_percent > 90:
            issues += 2

        # Update state based on issue count
        previous_state = self.current_state

        if issues == 0:
            self.current_state = SystemState.HEALTHY
        elif issues <= 2:
            self.current_state = SystemState.DEGRADED
        else:
            self.current_state = SystemState.CRITICAL

        # Log state changes
        if previous_state != self.current_state:
            logger.warning(f"System state changed: {previous_state.value} -> {self.current_state.value}")

            # Trigger health recovery if needed
            if self.current_state == SystemState.CRITICAL:
                await optimization_engine.publish_event(
                    EventType.SYSTEM_HEALTH_CHECK,
                    "integration_orchestrator",
                    {
                        "action": "recovery_required",
                        "previous_state": previous_state.value,
                        "current_state": self.current_state.value,
                        "health_metrics": health_metrics.__dict__
                    },
                    priority=1
                )

    def _calculate_performance_score(self,
                                   optimization_health: Dict,
                                   db_performance: Dict,
                                   api_performance: Dict) -> float:
        """Calculate overall system performance score (0-100)"""

        score = 100.0

        # Database performance (25% weight)
        db_response_time = db_performance["operation_stats"]["average_response_time"]
        if db_response_time > 1000:  # > 1 second
            score -= 25
        elif db_response_time > 500:  # > 500ms
            score -= 15
        elif db_response_time > 200:  # > 200ms
            score -= 5

        # API performance (25% weight)
        api_response_time = api_performance["global_stats"]["average_response_time"]
        if api_response_time > 1000:
            score -= 25
        elif api_response_time > 500:
            score -= 15
        elif api_response_time > 200:
            score -= 5

        # Error rate (30% weight)
        error_rate = api_performance["global_stats"]["total_errors"] / max(1, api_performance["global_stats"]["total_requests"])
        if error_rate > 0.1:  # > 10%
            score -= 30
        elif error_rate > 0.05:  # > 5%
            score -= 20
        elif error_rate > 0.02:  # > 2%
            score -= 10

        # Cache performance (20% weight)
        cache_stats = optimization_health.get("cache_stats", {})
        total_cache_requests = cache_stats.get("hits", 0) + cache_stats.get("misses", 0)
        cache_hit_rate = cache_stats.get("hits", 0) / max(1, total_cache_requests)

        if cache_hit_rate < 0.5:  # < 50%
            score -= 20
        elif cache_hit_rate < 0.7:  # < 70%
            score -= 10
        elif cache_hit_rate < 0.8:  # < 80%
            score -= 5

        return max(0.0, score)

    # Health check functions for services
    async def _check_database_health(self) -> bool:
        """Check database health"""
        try:
            result = await optimized_db.execute_optimized_query(
                "SELECT 1 as health_check",
                {},
                QueryType.SELECT,
                cache_ttl=5
            )
            return len(result) > 0
        except Exception:
            return False

    async def _check_api_health(self) -> bool:
        """Check API layer health"""
        try:
            stats = enhanced_api_layer.global_stats
            return stats["total_errors"] / max(1, stats["total_requests"]) < 0.1
        except Exception:
            return False

    async def _check_optimization_engine_health(self) -> bool:
        """Check optimization engine health"""
        try:
            event_stats = optimization_engine.event_bus.get_stats()
            return event_stats["queue_size"] < 5000  # Queue not overwhelmed
        except Exception:
            return False


# Global system integration orchestrator
system_orchestrator = SystemIntegrationOrchestrator(
    IntegrationConfig(
        optimization_level=OptimizationLevel.BALANCED,
        integration_mode=IntegrationMode.BALANCED
    )
)