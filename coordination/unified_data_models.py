"""
Unified Data Models for Service 6 Enhanced Platform
Coordinated across all 4 parallel development phases
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
import uuid


# Common Enums
class UserRole(str, Enum):
    """User roles across all phases"""
    ADMIN = "admin"
    EXECUTIVE = "executive"
    AGENT = "agent"
    VIEWER = "viewer"


class ServiceStatus(str, Enum):
    """Service health status for monitoring"""
    UP = "up"
    DOWN = "down"
    DEGRADED = "degraded"


class SystemHealth(str, Enum):
    """Overall system health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


# Phase 1: Security & Infrastructure Models
class User(BaseModel):
    """User model with security context"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str = Field(..., regex=r'^[^@]+@[^@]+\.[^@]+$')
    role: UserRole
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = None
    permissions: List[str] = []
    is_active: bool = True
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AuthToken(BaseModel):
    """JWT token structure"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 3600  # seconds
    user_id: str
    role: UserRole
    permissions: List[str] = []


class SecurityContext(BaseModel):
    """Security context for requests"""
    user_id: str
    role: UserRole
    permissions: List[str]
    session_id: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# Phase 2: AI Enhancement Models
class LeadScore(BaseModel):
    """AI-powered lead scoring model"""
    lead_id: str
    score: float = Field(..., ge=0, le=100, description="Lead score from 0-100")
    confidence: float = Field(..., ge=0, le=1, description="Model confidence 0-1")
    explanation: str = Field(..., min_length=10, description="Human-readable explanation")
    factors: List[Dict[str, Union[str, float]]] = []
    model_version: str = "claude-3.5-sonnet"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    @validator('factors')
    def validate_factors(cls, v):
        """Ensure factors have required structure"""
        for factor in v:
            if not all(key in factor for key in ['factor', 'weight', 'impact']):
                raise ValueError("Each factor must have 'factor', 'weight', and 'impact' keys")
            if factor['impact'] not in ['positive', 'negative', 'neutral']:
                raise ValueError("Impact must be 'positive', 'negative', or 'neutral'")
        return v


class VoiceAnalysis(BaseModel):
    """Voice call analysis results"""
    call_id: str
    lead_id: Optional[str] = None
    transcript: str
    duration_seconds: int
    sentiment: Dict[str, Union[str, float]] = Field(
        default_factory=lambda: {"overall": "neutral", "score": 0.0}
    )
    key_insights: List[str] = []
    next_actions: List[str] = []
    entities_extracted: List[Dict[str, str]] = []
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    model_version: str = "claude-voice-1.0"
    
    @validator('sentiment')
    def validate_sentiment(cls, v):
        """Validate sentiment structure"""
        if 'overall' not in v or v['overall'] not in ['positive', 'neutral', 'negative']:
            raise ValueError("Sentiment must have valid 'overall' value")
        if 'score' in v and not (-1 <= v['score'] <= 1):
            raise ValueError("Sentiment score must be between -1 and 1")
        return v


class AIModelMetrics(BaseModel):
    """AI model performance metrics"""
    model_name: str
    version: str
    request_count: int = 0
    avg_response_time: float = 0.0
    error_rate: float = 0.0
    accuracy_score: Optional[float] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    resource_usage: Dict[str, float] = {}


# Phase 3: Frontend Enhancement Models
class DashboardMetrics(BaseModel):
    """Dashboard metrics tailored to user role"""
    user_role: UserRole
    timeframe: str = "today"  # today, week, month, quarter
    metrics: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    permissions: List[str] = []
    cache_key: Optional[str] = None
    
    @validator('metrics')
    def validate_metrics_by_role(cls, v, values):
        """Validate metrics based on user role"""
        if 'user_role' not in values:
            return v
            
        role = values['user_role']
        required_metrics = {
            UserRole.EXECUTIVE: ['total_leads', 'conversion_rate', 'revenue', 'team_performance'],
            UserRole.AGENT: ['my_leads', 'my_conversions', 'my_calls', 'my_pipeline'],
            UserRole.ADMIN: ['system_health', 'user_activity', 'performance_metrics'],
            UserRole.VIEWER: ['basic_stats']
        }
        
        if role in required_metrics:
            # Ensure at least some required metrics are present
            has_required = any(metric in v for metric in required_metrics[role][:2])
            if not has_required and v:  # Only validate if metrics exist
                raise ValueError(f"Missing required metrics for role {role}")
        
        return v


class RealTimeUpdate(BaseModel):
    """Real-time update message for WebSocket"""
    type: str  # lead_score_update, new_lead, call_completed, metric_update
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    target_users: List[str] = []  # User IDs who should receive this update
    target_roles: List[UserRole] = []  # Roles who should receive this update
    channel: str = "general"  # WebSocket channel
    priority: str = "normal"  # low, normal, high, critical


class UIComponentState(BaseModel):
    """State management for UI components"""
    component_id: str
    user_id: str
    state_data: Dict[str, Any]
    last_modified: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    session_id: str


# Phase 4: Deployment & Scaling Models
class ServiceHealth(BaseModel):
    """Individual service health status"""
    service_name: str
    status: ServiceStatus
    response_time: float = 0.0  # milliseconds
    error_rate: float = 0.0  # percentage
    last_check: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = []


class SystemHealthCheck(BaseModel):
    """Complete system health check"""
    overall_status: SystemHealth
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    services: Dict[str, ServiceHealth] = Field(default_factory=dict)
    active_alerts: List[str] = []
    performance_summary: Dict[str, float] = Field(default_factory=dict)


class ScalingMetrics(BaseModel):
    """Infrastructure scaling metrics"""
    cpu_usage: float = Field(..., ge=0, le=100, description="CPU usage percentage")
    memory_usage: float = Field(..., ge=0, le=100, description="Memory usage percentage")
    request_rate: float = Field(..., ge=0, description="Requests per second")
    response_time: float = Field(..., ge=0, description="Average response time in ms")
    error_rate: float = Field(..., ge=0, le=100, description="Error rate percentage")
    active_connections: int = Field(..., ge=0, description="Active connections count")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AutoScalingConfig(BaseModel):
    """Auto-scaling configuration"""
    enabled: bool = True
    min_replicas: int = Field(..., ge=1, le=100)
    max_replicas: int = Field(..., ge=1, le=100)
    target_cpu_percent: float = Field(..., ge=1, le=100)
    target_memory_percent: float = Field(..., ge=1, le=100)
    scale_up_threshold: float = 70.0
    scale_down_threshold: float = 30.0
    cooldown_period: int = 300  # seconds
    
    @validator('max_replicas')
    def validate_max_replicas(cls, v, values):
        """Ensure max_replicas >= min_replicas"""
        if 'min_replicas' in values and v < values['min_replicas']:
            raise ValueError("max_replicas must be >= min_replicas")
        return v


# Cross-Phase Integration Models
class IntegrationTestResult(BaseModel):
    """Integration test result across phases"""
    test_name: str
    phase_1_security: bool = False
    phase_2_ai: bool = False
    phase_3_frontend: bool = False
    phase_4_scaling: bool = False
    overall_status: SystemHealth
    test_duration: float = 0.0  # seconds
    errors: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class CrossPhaseEvent(BaseModel):
    """Event that affects multiple phases"""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str  # user_login, lead_scored, dashboard_accessed, system_scaled
    source_phase: int = Field(..., ge=1, le=4)  # Which phase generated the event
    target_phases: List[int] = Field(..., min_items=1)  # Which phases should handle it
    payload: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    processed_by: List[int] = []  # Phases that have processed this event


class SystemConfiguration(BaseModel):
    """Unified system configuration across phases"""
    environment: str  # development, staging, production
    database_config: Dict[str, Any]
    redis_config: Dict[str, Any]
    ai_model_config: Dict[str, Any]
    frontend_config: Dict[str, Any]
    scaling_config: AutoScalingConfig
    security_config: Dict[str, Any]
    feature_flags: Dict[str, bool] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.utcnow)


# API Response Models
class ApiResponse(BaseModel):
    """Standardized API response format"""
    success: bool
    message: str = ""
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class PaginatedResponse(ApiResponse):
    """Paginated API response"""
    page: int = 1
    per_page: int = 50
    total: int = 0
    pages: int = 1
    has_next: bool = False
    has_prev: bool = False
    
    @validator('pages')
    def calculate_pages(cls, v, values):
        """Calculate total pages"""
        if 'total' in values and 'per_page' in values and values['per_page'] > 0:
            return (values['total'] + values['per_page'] - 1) // values['per_page']
        return v


# Error Models
class ValidationError(BaseModel):
    """Validation error details"""
    field: str
    message: str
    invalid_value: Optional[Any] = None


class ErrorResponse(BaseModel):
    """Standardized error response"""
    error: str
    message: str
    details: Optional[List[ValidationError]] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None


# Utility Functions for Model Coordination
def get_user_permissions(role: UserRole) -> List[str]:
    """Get default permissions for user role"""
    permissions_map = {
        UserRole.ADMIN: [
            "read:all", "write:all", "delete:all", "admin:system", 
            "view:analytics", "export:data", "manage:users"
        ],
        UserRole.EXECUTIVE: [
            "read:analytics", "view:dashboard", "export:reports", 
            "view:team_metrics", "read:leads"
        ],
        UserRole.AGENT: [
            "read:my_leads", "write:my_leads", "view:my_dashboard", 
            "read:properties", "write:activities"
        ],
        UserRole.VIEWER: [
            "read:basic", "view:dashboard"
        ]
    }
    return permissions_map.get(role, [])


def create_cache_key(*args) -> str:
    """Create consistent cache key across phases"""
    return ":".join(str(arg) for arg in args)


def validate_cross_phase_data(data: Dict[str, Any], required_phases: List[int]) -> bool:
    """Validate that data contains required fields for specified phases"""
    phase_requirements = {
        1: ["user_id", "permissions"],  # Security
        2: ["lead_id", "model_version"],  # AI
        3: ["user_role", "ui_context"],  # Frontend
        4: ["performance_metrics"]  # Scaling
    }
    
    for phase in required_phases:
        if phase in phase_requirements:
            required_fields = phase_requirements[phase]
            if not all(field in data for field in required_fields):
                return False
    return True


# Model Registry for Dynamic Loading
MODEL_REGISTRY = {
    "User": User,
    "AuthToken": AuthToken,
    "LeadScore": LeadScore,
    "VoiceAnalysis": VoiceAnalysis,
    "DashboardMetrics": DashboardMetrics,
    "RealTimeUpdate": RealTimeUpdate,
    "ServiceHealth": ServiceHealth,
    "ScalingMetrics": ScalingMetrics,
    "IntegrationTestResult": IntegrationTestResult,
    "CrossPhaseEvent": CrossPhaseEvent,
    "SystemConfiguration": SystemConfiguration,
    "ApiResponse": ApiResponse,
    "ErrorResponse": ErrorResponse
}


def get_model_by_name(model_name: str) -> Optional[BaseModel]:
    """Get model class by name for dynamic instantiation"""
    return MODEL_REGISTRY.get(model_name)


# Export all models for easy importing
__all__ = [
    # Enums
    "UserRole", "ServiceStatus", "SystemHealth",
    
    # Phase 1: Security & Infrastructure
    "User", "AuthToken", "SecurityContext",
    
    # Phase 2: AI Enhancement
    "LeadScore", "VoiceAnalysis", "AIModelMetrics",
    
    # Phase 3: Frontend Enhancement
    "DashboardMetrics", "RealTimeUpdate", "UIComponentState",
    
    # Phase 4: Deployment & Scaling
    "ServiceHealth", "SystemHealthCheck", "ScalingMetrics", "AutoScalingConfig",
    
    # Cross-Phase Integration
    "IntegrationTestResult", "CrossPhaseEvent", "SystemConfiguration",
    
    # API Responses
    "ApiResponse", "PaginatedResponse", "ErrorResponse", "ValidationError",
    
    # Utility Functions
    "get_user_permissions", "create_cache_key", "validate_cross_phase_data", "get_model_by_name"
]