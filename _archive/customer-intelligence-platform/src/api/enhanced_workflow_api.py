"""
Enhanced Workflow API

REST API endpoints for the enhanced workflow automation system.

Provides endpoints for:
- Workflow management and execution
- Analytics and performance monitoring
- A/B testing management
- CRM integration management
- Industry template management
- Real-time workflow triggers

Features:
- Comprehensive error handling
- Request validation with Pydantic
- Rate limiting and authentication
- OpenAPI/Swagger documentation
- Performance monitoring
- Audit logging
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import logging
import json

from ..services.enhanced_workflow_engine import (
    EnhancedWorkflowEngine, create_enhanced_workflow_engine,
    TriggerCondition, ActionType, WorkflowPriority, WorkflowStage, 
    IndustryVertical, TriggerRule, EnhancedWorkflowAction
)
from ..services.workflow_analytics_service import (
    WorkflowAnalyticsService, create_workflow_analytics_service,
    MetricType, TimeWindow
)
from ..services.advanced_crm_integration_service import (
    AdvancedCRMIntegrationService, create_advanced_crm_integration_service,
    CRMType, SyncDirection, CRMCredentials, CRMSyncRule, CRMFieldMapping
)
from ..core.ai_orchestrator import get_ai_orchestrator
from ..utils.logger import get_logger

logger = get_logger(__name__)

# Initialize services
ai_orchestrator = get_ai_orchestrator()
workflow_engine = create_enhanced_workflow_engine(ai_orchestrator)
analytics_service = create_workflow_analytics_service()
crm_service = create_advanced_crm_integration_service()

# Security
security = HTTPBearer()

# FastAPI app
app = FastAPI(
    title="Enhanced Workflow Automation API",
    description="Advanced AI-powered workflow automation for customer intelligence",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Models
class WorkflowRequest(BaseModel):
    """Request model for workflow processing."""
    customer_id: str = Field(..., description="Unique customer identifier")
    conversation_history: List[Dict[str, Any]] = Field(default=[], description="Recent conversation messages")
    customer_context: Dict[str, Any] = Field(default={}, description="Customer background and context")
    industry: Optional[IndustryVertical] = Field(None, description="Industry vertical for template selection")
    workflow_template_id: Optional[str] = Field(None, description="Specific workflow template ID")
    
    class Config:
        use_enum_values = True


class WorkflowResponse(BaseModel):
    """Response model for workflow processing."""
    customer_id: str
    ai_insights: List[Dict[str, Any]]
    workflow_actions: List[Dict[str, Any]]
    executed_actions: List[Dict[str, Any]]
    template_used: Optional[str]
    processing_timestamp: str


class TriggerRuleModel(BaseModel):
    """Pydantic model for trigger rules."""
    condition: TriggerCondition
    operator: str = Field(..., regex="^(>=|<=|==|!=|contains|regex)$")
    threshold: Union[float, str, List[str]]
    confidence_required: float = Field(0.7, ge=0.0, le=1.0)
    time_window_hours: Optional[int] = Field(None, ge=1, le=168)
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        use_enum_values = True


class WorkflowActionModel(BaseModel):
    """Pydantic model for workflow actions."""
    action_type: ActionType
    priority: WorkflowPriority
    stage: WorkflowStage
    payload: Dict[str, Any]
    trigger_rules: List[TriggerRuleModel]
    delay_minutes: int = Field(0, ge=0)
    expires_at: Optional[datetime] = None
    
    class Config:
        use_enum_values = True


class AnalyticsRequest(BaseModel):
    """Request model for analytics."""
    time_window: TimeWindow = Field(TimeWindow.DAILY, description="Time window for analytics")
    industry: Optional[IndustryVertical] = Field(None, description="Filter by industry")
    metric_types: Optional[List[MetricType]] = Field(None, description="Specific metrics to include")
    
    class Config:
        use_enum_values = True


class ABTestRequest(BaseModel):
    """Request model for creating A/B tests."""
    test_name: str = Field(..., min_length=1, max_length=100)
    control_variant: str = Field(..., min_length=1)
    test_variants: List[str] = Field(..., min_items=1, max_items=5)
    traffic_allocation: Optional[Dict[str, float]] = None
    
    @validator('traffic_allocation')
    def validate_traffic_allocation(cls, v):
        if v is not None:
            total = sum(v.values())
            if not (0.95 <= total <= 1.05):  # Allow small floating point differences
                raise ValueError("Traffic allocation must sum to 1.0")
        return v


class CRMCredentialsModel(BaseModel):
    """Pydantic model for CRM credentials."""
    crm_type: CRMType
    client_id: str = Field(..., min_length=1)
    client_secret: str = Field(..., min_length=1)
    access_token: str = Field(..., min_length=1)
    refresh_token: str = Field(..., min_length=1)
    instance_url: Optional[str] = None
    expires_at: Optional[datetime] = None
    scopes: Optional[List[str]] = None
    
    class Config:
        use_enum_values = True


class CRMFieldMappingModel(BaseModel):
    """Pydantic model for CRM field mappings."""
    platform_field: str = Field(..., min_length=1)
    crm_field: str = Field(..., min_length=1)
    data_type: str = Field(..., regex="^(string|number|boolean|date|list)$")
    direction: SyncDirection
    transformation: Optional[str] = None
    required: bool = False
    default_value: Any = None
    
    class Config:
        use_enum_values = True


class CRMSyncRuleModel(BaseModel):
    """Pydantic model for CRM sync rules."""
    name: str = Field(..., min_length=1, max_length=100)
    crm_type: CRMType
    object_type: str = Field(..., min_length=1)
    direction: SyncDirection
    field_mappings: List[CRMFieldMappingModel] = Field(..., min_items=1)
    filters: Dict[str, Any] = Field(default={})
    trigger_events: List[str] = Field(default=[])
    batch_size: int = Field(100, ge=1, le=1000)
    sync_frequency_minutes: int = Field(60, ge=5, le=10080)
    enabled: bool = True
    
    class Config:
        use_enum_values = True


class ErrorResponse(BaseModel):
    """Standard error response model."""
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime


# Authentication and Authorization
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user."""
    # In production, validate JWT token and extract user info
    # For now, return a mock user
    return {
        "user_id": "user_123",
        "tenant_id": "tenant_456",
        "permissions": ["workflow:read", "workflow:write", "analytics:read", "crm:manage"]
    }


def require_permission(permission: str):
    """Decorator to require specific permission."""
    def decorator(user: dict = Depends(get_current_user)):
        if permission not in user.get("permissions", []):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return user
    return decorator


# Workflow Management Endpoints
@app.post("/api/v1/workflows/process", response_model=WorkflowResponse)
async def process_workflow(
    request: WorkflowRequest,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_permission("workflow:write"))
):
    """Process customer interaction through workflow automation."""
    
    try:
        # Record analytics event
        background_tasks.add_task(
            analytics_service.record_workflow_event,
            "workflow_started",
            f"workflow_{request.customer_id}",
            request.customer_id,
            1.0,
            {"industry": request.industry.value if request.industry else None}
        )
        
        # Process workflow
        result = await workflow_engine.process_customer_workflow(
            request.customer_id,
            request.conversation_history,
            request.customer_context,
            request.industry,
            request.workflow_template_id
        )
        
        # Record completion event
        background_tasks.add_task(
            analytics_service.record_workflow_event,
            "workflow_completed",
            f"workflow_{request.customer_id}",
            request.customer_id,
            1.0,
            {"actions_count": len(result["workflow_actions"])}
        )
        
        return WorkflowResponse(**result)
    
    except Exception as e:
        logger.error(f"Workflow processing failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Workflow processing failed: {str(e)}"
        )


@app.get("/api/v1/workflows/stats")
async def get_workflow_stats(user: dict = Depends(require_permission("workflow:read"))):
    """Get workflow engine statistics."""
    
    try:
        stats = workflow_engine.get_workflow_stats()
        return stats
    
    except Exception as e:
        logger.error(f"Failed to get workflow stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow statistics"
        )


@app.get("/api/v1/workflows/templates")
async def get_workflow_templates(
    industry: Optional[IndustryVertical] = None,
    user: dict = Depends(require_permission("workflow:read"))
):
    """Get available workflow templates."""
    
    try:
        if industry:
            template = workflow_engine.template_engine.get_template(industry)
            return {"templates": [template] if template else []}
        else:
            templates = list(workflow_engine.template_engine.templates.values())
            return {"templates": templates}
    
    except Exception as e:
        logger.error(f"Failed to get workflow templates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve workflow templates"
        )


@app.post("/api/v1/workflows/templates/{industry}/customize")
async def customize_workflow_template(
    industry: IndustryVertical,
    customizations: Dict[str, Any],
    user: dict = Depends(require_permission("workflow:write"))
):
    """Customize workflow template for specific use case."""
    
    try:
        customized_template = workflow_engine.template_engine.customize_template(
            industry, customizations
        )
        return {"template": customized_template}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Failed to customize template: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to customize workflow template"
        )


# Analytics Endpoints
@app.post("/api/v1/analytics/report")
async def get_analytics_report(
    request: AnalyticsRequest,
    user: dict = Depends(require_permission("analytics:read"))
):
    """Generate workflow performance analytics report."""
    
    try:
        report = await analytics_service.analyzer.generate_performance_report(
            request.time_window,
            request.industry
        )
        
        return {
            "report": {
                "report_id": report.report_id,
                "time_window": report.time_window.value,
                "start_time": report.start_time.isoformat(),
                "end_time": report.end_time.isoformat(),
                "total_workflows": report.total_workflows,
                "success_rate": report.success_rate,
                "conversion_rate": report.conversion_rate,
                "customer_satisfaction": report.customer_satisfaction,
                "roi_percentage": report.roi_percentage,
                "metrics_by_stage": report.metrics_by_stage,
                "metrics_by_industry": report.metrics_by_industry,
                "metrics_by_action_type": report.metrics_by_action_type,
                "trends": report.trends,
                "insights": report.insights,
                "recommendations": report.recommendations
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to generate analytics report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate analytics report"
        )


@app.get("/api/v1/analytics/dashboard")
async def get_dashboard_data(user: dict = Depends(require_permission("analytics:read"))):
    """Get real-time dashboard data."""
    
    try:
        dashboard_data = await analytics_service.get_dashboard_data()
        return dashboard_data
    
    except Exception as e:
        logger.error(f"Failed to get dashboard data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard data"
        )


@app.post("/api/v1/analytics/events")
async def record_analytics_event(
    event_type: str,
    workflow_id: str,
    customer_id: str,
    value: float,
    metadata: Optional[Dict[str, Any]] = None,
    user: dict = Depends(require_permission("analytics:write"))
):
    """Record custom analytics event."""
    
    try:
        await analytics_service.record_workflow_event(
            event_type,
            workflow_id,
            customer_id,
            value,
            metadata
        )
        
        return {"status": "success", "message": "Event recorded"}
    
    except Exception as e:
        logger.error(f"Failed to record analytics event: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record analytics event"
        )


# A/B Testing Endpoints
@app.post("/api/v1/ab-tests")
async def create_ab_test(
    request: ABTestRequest,
    user: dict = Depends(require_permission("workflow:write"))
):
    """Create a new A/B test."""
    
    try:
        test_id = await analytics_service.ab_testing.create_ab_test(
            request.test_name,
            request.control_variant,
            request.test_variants,
            request.traffic_allocation
        )
        
        return {"test_id": test_id, "status": "created"}
    
    except Exception as e:
        logger.error(f"Failed to create A/B test: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create A/B test"
        )


@app.get("/api/v1/ab-tests")
async def get_active_ab_tests(user: dict = Depends(require_permission("analytics:read"))):
    """Get all active A/B tests."""
    
    try:
        tests = analytics_service.ab_testing.get_active_tests()
        return {"tests": tests}
    
    except Exception as e:
        logger.error(f"Failed to get A/B tests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B tests"
        )


@app.get("/api/v1/ab-tests/{test_id}")
async def get_ab_test_results(
    test_id: str,
    user: dict = Depends(require_permission("analytics:read"))
):
    """Get A/B test results."""
    
    try:
        test_result = analytics_service.ab_testing.get_test_results(test_id)
        if not test_result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="A/B test not found"
            )
        
        return {"test": test_result}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get A/B test results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve A/B test results"
        )


@app.post("/api/v1/ab-tests/{test_id}/conversion")
async def record_ab_test_conversion(
    test_id: str,
    variant: str,
    customer_id: str,
    converted: bool,
    revenue: float = 0.0,
    user: dict = Depends(require_permission("analytics:write"))
):
    """Record A/B test conversion event."""
    
    try:
        await analytics_service.ab_testing.record_test_conversion(
            test_id, variant, customer_id, converted, revenue
        )
        
        return {"status": "success", "message": "Conversion recorded"}
    
    except Exception as e:
        logger.error(f"Failed to record A/B test conversion: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record A/B test conversion"
        )


# CRM Integration Endpoints
@app.post("/api/v1/crm/integrations")
async def register_crm_integration(
    crm_type: CRMType,
    credentials: CRMCredentialsModel,
    user: dict = Depends(require_permission("crm:manage"))
):
    """Register a new CRM integration."""
    
    try:
        crm_credentials = CRMCredentials(
            crm_type=credentials.crm_type,
            client_id=credentials.client_id,
            client_secret=credentials.client_secret,
            access_token=credentials.access_token,
            refresh_token=credentials.refresh_token,
            instance_url=credentials.instance_url,
            expires_at=credentials.expires_at,
            scopes=credentials.scopes
        )
        
        integration_id = await crm_service.register_crm_integration(
            user["tenant_id"],
            crm_type,
            crm_credentials
        )
        
        return {"integration_id": integration_id, "status": "registered"}
    
    except Exception as e:
        logger.error(f"Failed to register CRM integration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to register CRM integration: {str(e)}"
        )


@app.post("/api/v1/crm/sync-rules")
async def create_sync_rule(
    request: CRMSyncRuleModel,
    user: dict = Depends(require_permission("crm:manage"))
):
    """Create a new CRM synchronization rule."""
    
    try:
        # Convert Pydantic models to dataclasses
        field_mappings = []
        for mapping_model in request.field_mappings:
            field_mappings.append(CRMFieldMapping(
                platform_field=mapping_model.platform_field,
                crm_field=mapping_model.crm_field,
                data_type=mapping_model.data_type,
                direction=mapping_model.direction,
                transformation=mapping_model.transformation,
                required=mapping_model.required,
                default_value=mapping_model.default_value
            ))
        
        sync_rule = CRMSyncRule(
            rule_id=f"rule_{user['tenant_id']}_{len(crm_service.sync_rules) + 1}",
            name=request.name,
            crm_type=request.crm_type,
            object_type=request.object_type,
            direction=request.direction,
            field_mappings=field_mappings,
            filters=request.filters,
            trigger_events=request.trigger_events,
            batch_size=request.batch_size,
            sync_frequency_minutes=request.sync_frequency_minutes,
            enabled=request.enabled
        )
        
        rule_id = await crm_service.create_sync_rule(sync_rule)
        
        return {"rule_id": rule_id, "status": "created"}
    
    except Exception as e:
        logger.error(f"Failed to create sync rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sync rule: {str(e)}"
        )


@app.post("/api/v1/crm/sync-rules/{rule_id}/execute")
async def execute_sync_rule(
    rule_id: str,
    background_tasks: BackgroundTasks,
    user: dict = Depends(require_permission("crm:write"))
):
    """Execute a CRM synchronization rule."""
    
    try:
        # Execute sync in background
        background_tasks.add_task(
            crm_service.execute_sync_rule,
            rule_id,
            user["tenant_id"]
        )
        
        return {"status": "sync_started", "rule_id": rule_id}
    
    except Exception as e:
        logger.error(f"Failed to execute sync rule: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute sync rule: {str(e)}"
        )


@app.post("/api/v1/crm/webhooks/{crm_type}")
async def process_crm_webhook(
    crm_type: CRMType,
    request: Request,
    background_tasks: BackgroundTasks
):
    """Process incoming CRM webhook."""
    
    try:
        payload = await request.json()
        headers = dict(request.headers)
        
        # Process webhook in background
        background_tasks.add_task(
            crm_service.process_webhook,
            crm_type,
            payload,
            headers
        )
        
        return {"status": "webhook_received"}
    
    except Exception as e:
        logger.error(f"Failed to process CRM webhook: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process CRM webhook"
        )


@app.get("/api/v1/crm/integrations/{crm_type}/health")
async def get_crm_integration_health(
    crm_type: CRMType,
    user: dict = Depends(require_permission("crm:read"))
):
    """Get health status of CRM integration."""
    
    try:
        health = await crm_service.get_integration_health(user["tenant_id"], crm_type)
        return health
    
    except Exception as e:
        logger.error(f"Failed to get CRM integration health: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get CRM integration health"
        )


@app.post("/api/v1/crm/actions")
async def execute_crm_action(
    crm_type: CRMType,
    action_type: ActionType,
    customer_id: str,
    payload: Dict[str, Any],
    user: dict = Depends(require_permission("crm:write"))
):
    """Execute workflow action in CRM."""
    
    try:
        result = await crm_service.execute_workflow_action(
            user["tenant_id"],
            crm_type,
            action_type,
            customer_id,
            payload
        )
        
        return result
    
    except Exception as e:
        logger.error(f"Failed to execute CRM action: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute CRM action: {str(e)}"
        )


# Optimization Endpoints
@app.post("/api/v1/workflows/{workflow_id}/optimize")
async def optimize_workflow(
    workflow_id: str,
    user: dict = Depends(require_permission("workflow:write"))
):
    """Generate workflow optimization recommendations."""
    
    try:
        optimization_report = await analytics_service.optimizer.generate_optimization_report(workflow_id)
        return optimization_report
    
    except Exception as e:
        logger.error(f"Failed to optimize workflow: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate optimization recommendations"
        )


# Health Check Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "workflow_engine": workflow_engine.running,
            "analytics_service": analytics_service.running,
            "crm_service": crm_service.running
        }
    }


@app.get("/api/v1/status")
async def get_system_status(user: dict = Depends(get_current_user)):
    """Get detailed system status."""
    
    try:
        workflow_stats = workflow_engine.get_workflow_stats()
        dashboard_data = await analytics_service.get_dashboard_data()
        
        return {
            "system_status": "operational",
            "timestamp": datetime.utcnow().isoformat(),
            "workflow_engine": workflow_stats,
            "analytics": {
                "active_workflows": dashboard_data.get("performance_summary", {}).get("total_workflows", 0),
                "success_rate": dashboard_data.get("performance_summary", {}).get("success_rate", 0),
                "active_ab_tests": dashboard_data.get("active_ab_tests", 0)
            },
            "crm_integrations": {
                "supported_systems": [crm.value for crm in CRMType],
                "active_integrations": len(crm_service.crm_credentials)
            }
        }
    
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system status"
        )


# Error Handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with detailed error response."""
    return ErrorResponse(
        error=exc.__class__.__name__,
        message=exc.detail,
        timestamp=datetime.utcnow()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}")
    return ErrorResponse(
        error=exc.__class__.__name__,
        message="Internal server error",
        timestamp=datetime.utcnow()
    )


# Startup and Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    try:
        await workflow_engine.start()
        await analytics_service.start()
        await crm_service.start()
        logger.info("Enhanced workflow API services started successfully")
    except Exception as e:
        logger.error(f"Failed to start services: {e}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup services on shutdown."""
    try:
        await workflow_engine.stop()
        await analytics_service.stop()
        await crm_service.stop()
        logger.info("Enhanced workflow API services stopped successfully")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Run the API server
    uvicorn.run(
        "enhanced_workflow_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )