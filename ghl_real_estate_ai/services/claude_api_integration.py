"""
Claude Services API Integration

Provides FastAPI endpoints and integration layer for Claude services within
the EnterpriseHub ecosystem. Integrates with Phase 4 infrastructure for
enterprise-grade scaling, monitoring, and performance.

Created: January 2026
Author: Enterprise Development Team
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import json

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, validator
import redis.asyncio as redis

from .claude_agent_orchestrator import ClaudeAgentOrchestrator, AgentRole, TaskPriority
from .claude_enterprise_intelligence import ClaudeEnterpriseIntelligence
from .claude_business_intelligence_automation import ClaudeBusinessIntelligenceAutomation
from .advanced_cache_optimization import OptimizedRedisManager
from .enterprise_metrics_exporter import EnterpriseMetricsExporter
from .predictive_scaling_engine import PredictiveScalingEngine

logger = logging.getLogger(__name__)

class ClaudeServiceStatus(str, Enum):
    """Claude service operational status."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    MAINTENANCE = "maintenance"
    ERROR = "error"

@dataclass
class ClaudeServiceHealth:
    """Claude service health metrics."""
    service: str
    status: ClaudeServiceStatus
    last_check: datetime
    response_time_ms: float
    active_tasks: int
    error_rate: float
    uptime_percentage: float
    metadata: Dict[str, Any]

class AgentTaskRequest(BaseModel):
    """Request model for Claude agent tasks."""
    task_type: str
    description: str
    context: Dict[str, Any]
    agent_role: Optional[str] = None
    priority: str = "normal"

    @validator('priority')
    def validate_priority(cls, v):
        valid_priorities = ['low', 'normal', 'high', 'critical']
        if v not in valid_priorities:
            raise ValueError(f'Priority must be one of {valid_priorities}')
        return v

    @validator('agent_role')
    def validate_agent_role(cls, v):
        if v is not None:
            valid_roles = [role.value for role in AgentRole]
            if v not in valid_roles:
                raise ValueError(f'Agent role must be one of {valid_roles}')
        return v

class IntelligenceAnalysisRequest(BaseModel):
    """Request model for enterprise intelligence analysis."""
    focus_area: str = "overall"
    include_predictions: bool = True
    include_recommendations: bool = True
    time_window_hours: int = 24

class BusinessReportRequest(BaseModel):
    """Request model for business intelligence reports."""
    report_type: str
    period_start: datetime
    period_end: datetime
    include_forecasts: bool = True
    include_recommendations: bool = True

class ClaudeAPIIntegration:
    """Main Claude services API integration."""

    def __init__(self):
        self.app = FastAPI(
            title="Claude Services API",
            description="Enterprise Claude AI integration for real estate operations",
            version="1.0.0"
        )

        # Initialize Claude services
        self.agent_orchestrator = ClaudeAgentOrchestrator()
        self.enterprise_intelligence = ClaudeEnterpriseIntelligence()
        self.business_intelligence = ClaudeBusinessIntelligenceAutomation()

        # Initialize Phase 4 infrastructure
        self.redis_manager = OptimizedRedisManager()
        self.metrics_exporter = EnterpriseMetricsExporter()
        self.scaling_engine = PredictiveScalingEngine()

        # Service health tracking
        self.service_health: Dict[str, ClaudeServiceHealth] = {}
        self.last_health_check = datetime.utcnow()

        # Setup FastAPI app
        self._setup_middleware()
        self._setup_routes()
        self._setup_background_tasks()

        logger.info("Claude API Integration initialized")

    def _setup_middleware(self):
        """Configure FastAPI middleware."""
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],  # Configure appropriately for production
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _setup_routes(self):
        """Setup FastAPI routes."""

        @self.app.get("/health")
        async def health_check():
            """Overall Claude services health check."""
            try:
                await self._update_service_health()
                overall_status = self._calculate_overall_status()

                return JSONResponse(
                    status_code=200 if overall_status == ClaudeServiceStatus.OPERATIONAL else 503,
                    content={
                        "status": overall_status.value,
                        "timestamp": datetime.utcnow().isoformat(),
                        "services": {k: asdict(v) for k, v in self.service_health.items()}
                    }
                )
            except Exception as e:
                logger.error(f"Health check failed: {e}")
                return JSONResponse(
                    status_code=503,
                    content={"status": "error", "message": str(e)}
                )

        @self.app.post("/agents/submit-task")
        async def submit_agent_task(request: AgentTaskRequest, background_tasks: BackgroundTasks):
            """Submit task to Claude agent orchestrator."""
            try:
                # Convert string role to enum
                agent_role = AgentRole(request.agent_role) if request.agent_role else None
                priority_map = {
                    'low': TaskPriority.LOW,
                    'normal': TaskPriority.NORMAL,
                    'high': TaskPriority.HIGH,
                    'critical': TaskPriority.CRITICAL
                }
                priority = priority_map[request.priority]

                # Submit task
                task_id = await self.agent_orchestrator.submit_task(
                    task_type=request.task_type,
                    description=request.description,
                    context=request.context,
                    agent_role=agent_role,
                    priority=priority
                )

                # Track metrics
                background_tasks.add_task(
                    self._track_agent_task_metrics,
                    task_type=request.task_type,
                    agent_role=request.agent_role
                )

                return {"task_id": task_id, "status": "submitted"}

            except Exception as e:
                logger.error(f"Agent task submission failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/agents/task-status/{task_id}")
        async def get_task_status(task_id: str):
            """Get status of submitted agent task."""
            try:
                status = await self.agent_orchestrator.get_task_status(task_id)
                return {"task_id": task_id, "status": status}
            except Exception as e:
                logger.error(f"Task status check failed: {e}")
                raise HTTPException(status_code=404, detail="Task not found")

        @self.app.post("/intelligence/analyze")
        async def analyze_system(request: IntelligenceAnalysisRequest):
            """Perform enterprise intelligence analysis."""
            try:
                analysis = await self.enterprise_intelligence.analyze_system_health()

                # Apply request filters
                if request.focus_area != "overall":
                    analysis = await self._filter_analysis_by_focus(analysis, request.focus_area)

                if not request.include_predictions:
                    analysis.predictions = []

                if not request.include_recommendations:
                    analysis.recommendations = []

                return asdict(analysis)

            except Exception as e:
                logger.error(f"Intelligence analysis failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/intelligence/optimize-performance")
        async def optimize_performance(background_tasks: BackgroundTasks):
            """Trigger performance optimization analysis."""
            try:
                # Run optimization in background
                background_tasks.add_task(self._run_performance_optimization)

                return {
                    "status": "optimization_started",
                    "message": "Performance optimization analysis initiated"
                }

            except Exception as e:
                logger.error(f"Performance optimization trigger failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/business-intelligence/generate-report")
        async def generate_business_report(request: BusinessReportRequest):
            """Generate business intelligence report."""
            try:
                if request.report_type == "executive":
                    report = await self.business_intelligence.generate_executive_report(
                        request.period_start,
                        request.period_end
                    )
                elif request.report_type == "coaching_performance":
                    report = await self.business_intelligence.generate_coaching_performance_report(
                        request.period_start,
                        request.period_end
                    )
                elif request.report_type == "roi":
                    report = await self.business_intelligence.generate_roi_report(
                        request.period_start,
                        request.period_end
                    )
                else:
                    raise ValueError(f"Unknown report type: {request.report_type}")

                return asdict(report)

            except Exception as e:
                logger.error(f"Business report generation failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/business-intelligence/insights")
        async def get_real_time_insights():
            """Get real-time business insights."""
            try:
                insights = await self.business_intelligence.generate_real_time_insights()
                return {"insights": insights, "timestamp": datetime.utcnow().isoformat()}
            except Exception as e:
                logger.error(f"Real-time insights failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/metrics/claude-services")
        async def get_claude_metrics():
            """Get Claude services performance metrics."""
            try:
                metrics = await self._collect_claude_metrics()
                return {"metrics": metrics, "timestamp": datetime.utcnow().isoformat()}
            except Exception as e:
                logger.error(f"Metrics collection failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/scaling/predict-demand")
        async def predict_scaling_demand():
            """Predict scaling demand for Claude services."""
            try:
                # Use enterprise intelligence to predict demand
                prediction = await self._predict_claude_demand()

                return {
                    "prediction": prediction,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                logger.error(f"Demand prediction failed: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    def _setup_background_tasks(self):
        """Setup background monitoring and maintenance tasks."""
        asyncio.create_task(self._health_monitoring_loop())
        asyncio.create_task(self._metrics_collection_loop())
        asyncio.create_task(self._intelligence_analysis_loop())

    async def _update_service_health(self):
        """Update health status for all Claude services."""
        services = {
            "agent_orchestrator": self.agent_orchestrator,
            "enterprise_intelligence": self.enterprise_intelligence,
            "business_intelligence": self.business_intelligence
        }

        for service_name, service in services.items():
            try:
                start_time = datetime.utcnow()

                # Perform health check (example ping operation)
                await service.health_check() if hasattr(service, 'health_check') else None

                response_time = (datetime.utcnow() - start_time).total_seconds() * 1000

                # Get service metrics
                active_tasks = await self._get_active_tasks_count(service_name)
                error_rate = await self._get_error_rate(service_name)
                uptime = await self._get_uptime_percentage(service_name)

                self.service_health[service_name] = ClaudeServiceHealth(
                    service=service_name,
                    status=ClaudeServiceStatus.OPERATIONAL,
                    last_check=datetime.utcnow(),
                    response_time_ms=response_time,
                    active_tasks=active_tasks,
                    error_rate=error_rate,
                    uptime_percentage=uptime,
                    metadata={}
                )

            except Exception as e:
                logger.error(f"Health check failed for {service_name}: {e}")
                self.service_health[service_name] = ClaudeServiceHealth(
                    service=service_name,
                    status=ClaudeServiceStatus.ERROR,
                    last_check=datetime.utcnow(),
                    response_time_ms=0.0,
                    active_tasks=0,
                    error_rate=100.0,
                    uptime_percentage=0.0,
                    metadata={"error": str(e)}
                )

    def _calculate_overall_status(self) -> ClaudeServiceStatus:
        """Calculate overall system status from service health."""
        if not self.service_health:
            return ClaudeServiceStatus.ERROR

        statuses = [health.status for health in self.service_health.values()]

        if ClaudeServiceStatus.ERROR in statuses:
            return ClaudeServiceStatus.ERROR
        elif ClaudeServiceStatus.DEGRADED in statuses:
            return ClaudeServiceStatus.DEGRADED
        elif ClaudeServiceStatus.MAINTENANCE in statuses:
            return ClaudeServiceStatus.MAINTENANCE
        else:
            return ClaudeServiceStatus.OPERATIONAL

    async def _track_agent_task_metrics(self, task_type: str, agent_role: Optional[str]):
        """Track metrics for agent task submission."""
        try:
            metrics = {
                "claude_agent_task_submitted": 1,
                "claude_agent_task_type": task_type,
                "claude_agent_role": agent_role or "auto",
                "timestamp": datetime.utcnow().isoformat()
            }

            await self.metrics_exporter.export_metrics(metrics)
            logger.debug(f"Tracked agent task metrics: {metrics}")

        except Exception as e:
            logger.error(f"Failed to track agent task metrics: {e}")

    async def _filter_analysis_by_focus(self, analysis, focus_area: str):
        """Filter intelligence analysis by focus area."""
        # Implementation would filter analysis results based on focus area
        # For now, return the analysis as-is
        return analysis

    async def _run_performance_optimization(self):
        """Run performance optimization in background."""
        try:
            logger.info("Starting performance optimization analysis")

            # Get performance analysis from enterprise intelligence
            optimization = await self.enterprise_intelligence.optimize_system_performance()

            # Apply optimization recommendations
            for rec in optimization.recommendations:
                if rec.confidence > 0.8:  # High confidence recommendations
                    await self._apply_optimization_recommendation(rec)

            logger.info("Performance optimization completed")

        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")

    async def _apply_optimization_recommendation(self, recommendation):
        """Apply optimization recommendation."""
        # Implementation would apply specific optimization based on recommendation
        logger.info(f"Applied optimization: {recommendation.description}")

    async def _collect_claude_metrics(self) -> Dict[str, Any]:
        """Collect comprehensive Claude services metrics."""
        try:
            # Collect metrics from all Claude services
            agent_metrics = await self.agent_orchestrator.get_metrics()
            intel_metrics = await self.enterprise_intelligence.get_metrics()
            bi_metrics = await self.business_intelligence.get_metrics()

            return {
                "agent_orchestrator": agent_metrics,
                "enterprise_intelligence": intel_metrics,
                "business_intelligence": bi_metrics,
                "overall_health": {name: asdict(health) for name, health in self.service_health.items()}
            }
        except Exception as e:
            logger.error(f"Failed to collect Claude metrics: {e}")
            return {}

    async def _predict_claude_demand(self) -> Dict[str, Any]:
        """Predict demand for Claude services."""
        try:
            # Use enterprise intelligence for demand prediction
            analysis = await self.enterprise_intelligence.analyze_system_health()

            # Extract demand indicators
            current_load = analysis.system_metrics.get("cpu_usage", 0)
            task_queue_size = analysis.system_metrics.get("task_queue_size", 0)

            # Simple demand prediction logic
            predicted_demand = "high" if current_load > 80 or task_queue_size > 100 else "normal"

            return {
                "current_load": current_load,
                "queue_size": task_queue_size,
                "predicted_demand": predicted_demand,
                "scaling_recommendation": "scale_up" if predicted_demand == "high" else "maintain"
            }
        except Exception as e:
            logger.error(f"Demand prediction failed: {e}")
            return {"error": str(e)}

    async def _get_active_tasks_count(self, service_name: str) -> int:
        """Get active tasks count for service."""
        try:
            if service_name == "agent_orchestrator":
                return await self.agent_orchestrator.get_active_tasks_count()
            return 0
        except:
            return 0

    async def _get_error_rate(self, service_name: str) -> float:
        """Get error rate for service."""
        try:
            # Implementation would calculate error rate from metrics
            return 0.0  # Placeholder
        except:
            return 0.0

    async def _get_uptime_percentage(self, service_name: str) -> float:
        """Get uptime percentage for service."""
        try:
            # Implementation would calculate uptime from monitoring data
            return 99.95  # Placeholder
        except:
            return 0.0

    async def _health_monitoring_loop(self):
        """Background health monitoring loop."""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                await self._update_service_health()

                # Alert on degraded services
                for service_name, health in self.service_health.items():
                    if health.status in [ClaudeServiceStatus.ERROR, ClaudeServiceStatus.DEGRADED]:
                        logger.warning(f"Service {service_name} is {health.status.value}")

            except Exception as e:
                logger.error(f"Health monitoring loop error: {e}")

    async def _metrics_collection_loop(self):
        """Background metrics collection loop."""
        while True:
            try:
                await asyncio.sleep(60)  # Collect every minute
                metrics = await self._collect_claude_metrics()
                await self.metrics_exporter.export_metrics(metrics)

            except Exception as e:
                logger.error(f"Metrics collection loop error: {e}")

    async def _intelligence_analysis_loop(self):
        """Background intelligence analysis loop."""
        while True:
            try:
                await asyncio.sleep(300)  # Analyze every 5 minutes
                analysis = await self.enterprise_intelligence.analyze_system_health()

                # Apply high-confidence recommendations automatically
                for rec in analysis.recommendations:
                    if rec.confidence > 0.9:  # Very high confidence
                        await self._apply_optimization_recommendation(rec)

            except Exception as e:
                logger.error(f"Intelligence analysis loop error: {e}")

# Global instance for FastAPI app
claude_api = ClaudeAPIIntegration()
app = claude_api.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)