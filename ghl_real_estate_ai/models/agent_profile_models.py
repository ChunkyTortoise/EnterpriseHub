"""
Multi-Tenant Agent Profile System Data Models

This module defines the core data models for the agent profile system,
building on the existing EnterpriseHub architecture patterns.

Models support:
- Multi-tenant shared agent pool
- Role-specific specializations (Buyer/Seller/Transaction Coordinator)
- Session-based context management
- Claude AI integration with guidance type preferences
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, EmailStr, validator, root_validator
import json


# ============================================================================
# Enumerations for Type Safety
# ============================================================================

class AgentRole(str, Enum):
    """Agent role specializations (User Requirements)"""
    SELLER_AGENT = "seller_agent"
    BUYER_AGENT = "buyer_agent"
    TRANSACTION_COORDINATOR = "transaction_coordinator"
    DUAL_AGENT = "dual_agent"


class GuidanceType(str, Enum):
    """Claude guidance types (User Requirements)"""
    RESPONSE_SUGGESTIONS = "response_suggestions"
    STRATEGY_COACHING = "strategy_coaching"
    PROCESS_NAVIGATION = "process_navigation"
    PERFORMANCE_INSIGHTS = "performance_insights"


class CoachingStylePreference(str, Enum):
    """Agent coaching style preferences"""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    SUPPORTIVE = "supportive"


class CommunicationStyle(str, Enum):
    """Agent communication style preferences"""
    CASUAL = "casual"
    PROFESSIONAL = "professional"
    FORMAL = "formal"


class ConversationStage(str, Enum):
    """Workflow conversation stages"""
    DISCOVERY = "discovery"
    QUALIFICATION = "qualification"
    PRESENTATION = "presentation"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    FOLLOW_UP = "follow_up"


class SessionStatus(str, Enum):
    """Agent session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"
    ERROR = "error"


# ============================================================================
# Core Profile Models
# ============================================================================

class AgentProfile(BaseModel):
    """
    Core agent profile model with multi-tenant support.
    Supports shared agent pool where agents can work across multiple locations.
    """

    # Identity & Contact Information
    agent_id: str = Field(..., min_length=1, max_length=255, description="Unique agent identifier")
    agent_name: str = Field(..., min_length=1, max_length=255, description="Agent display name")
    email: EmailStr = Field(..., description="Agent email address")
    phone: Optional[str] = Field(None, max_length=50, description="Agent phone number")

    # Multi-tenant Configuration (Shared Agent Pool Support)
    primary_location_id: str = Field(..., min_length=1, max_length=255, description="Primary location/tenant")
    accessible_locations: List[str] = Field(default_factory=list, description="Locations where agent can work")
    role_permissions: Dict[str, List[AgentRole]] = Field(default_factory=dict, description="Role permissions per location")

    # Professional Profile (User Requirements)
    primary_role: AgentRole = Field(..., description="Primary agent role specialization")
    secondary_roles: List[AgentRole] = Field(default_factory=list, description="Additional role capabilities")
    years_experience: int = Field(default=0, ge=0, le=50, description="Years of real estate experience")
    specializations: List[str] = Field(default_factory=list, description="Agent specialization areas")

    # Claude AI Configuration (User Requirements)
    preferred_guidance_types: List[GuidanceType] = Field(
        default_factory=lambda: [GuidanceType.RESPONSE_SUGGESTIONS, GuidanceType.STRATEGY_COACHING],
        description="Preferred Claude guidance types"
    )
    coaching_style_preference: CoachingStylePreference = Field(
        default=CoachingStylePreference.BALANCED,
        description="Preferred coaching style"
    )
    communication_style: CommunicationStyle = Field(
        default=CommunicationStyle.PROFESSIONAL,
        description="Communication style preference"
    )

    # Session Management (Session-based Context Requirement)
    current_session_id: Optional[str] = Field(None, description="Currently active session ID")
    active_conversations: List[str] = Field(default_factory=list, description="Currently active conversation IDs")

    # Performance & Skills
    skill_levels: Dict[str, int] = Field(default_factory=dict, description="Skill level ratings (1-10)")
    performance_metrics_summary: Dict[str, float] = Field(
        default_factory=dict,
        description="Summary performance metrics"
    )
    notification_preferences: Dict[str, Any] = Field(
        default_factory=dict,
        description="Notification and alert preferences"
    )

    # System Configuration
    timezone: str = Field(default="UTC", description="Agent timezone")
    language_preference: str = Field(default="en-US", description="Language preference")
    profile_version: str = Field(default="1.0", description="Profile schema version")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Profile creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    is_active: bool = Field(default=True, description="Profile active status")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    login_count: int = Field(default=0, description="Total login count")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    @validator('accessible_locations')
    def validate_accessible_locations(cls, v, values):
        """Ensure primary_location_id is in accessible_locations"""
        if 'primary_location_id' in values and values['primary_location_id']:
            if values['primary_location_id'] not in v:
                v.append(values['primary_location_id'])
        return v

    @validator('skill_levels')
    def validate_skill_levels(cls, v):
        """Ensure skill levels are between 1-10"""
        for skill, level in v.items():
            if not isinstance(level, int) or level < 1 or level > 10:
                raise ValueError(f"Skill level for '{skill}' must be integer between 1-10")
        return v

    @validator('specializations')
    def validate_specializations(cls, v):
        """Validate specialization format"""
        if len(v) > 20:  # Reasonable limit
            raise ValueError("Maximum 20 specializations allowed")
        return [spec.strip() for spec in v if spec.strip()]

    @root_validator
    def validate_role_consistency(cls, values):
        """Ensure role configuration is consistent"""
        primary_role = values.get('primary_role')
        secondary_roles = values.get('secondary_roles', [])

        # Primary role should not be in secondary roles
        if primary_role and primary_role in secondary_roles:
            secondary_roles.remove(primary_role)
            values['secondary_roles'] = secondary_roles

        return values

    def get_all_roles(self) -> List[AgentRole]:
        """Get all roles (primary + secondary)"""
        roles = [self.primary_role]
        roles.extend(self.secondary_roles)
        return list(set(roles))  # Remove duplicates

    def has_access_to_location(self, location_id: str) -> bool:
        """Check if agent has access to a specific location"""
        return location_id in self.accessible_locations

    def has_role_in_location(self, location_id: str, role: AgentRole) -> bool:
        """Check if agent has specific role in location"""
        if not self.has_access_to_location(location_id):
            return False

        # Primary role applies to all accessible locations
        if role == self.primary_role:
            return True

        # Check location-specific permissions
        location_roles = self.role_permissions.get(location_id, [])
        return role in location_roles

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = self.dict()
        # Convert datetime objects to ISO strings
        for field in ['created_at', 'updated_at', 'last_login']:
            if data.get(field):
                data[field] = data[field].isoformat() if isinstance(data[field], datetime) else data[field]
        return data


# ============================================================================
# Session Models
# ============================================================================

class AgentSession(BaseModel):
    """
    Agent session model for session-based context management.
    Tracks current agent interaction state and Claude context.
    """

    # Session Identity
    session_id: str = Field(..., min_length=1, max_length=255, description="Unique session identifier")
    agent_id: str = Field(..., min_length=1, max_length=255, description="Associated agent ID")
    location_id: str = Field(..., min_length=1, max_length=255, description="Session location context")

    # Current Context
    current_lead_id: Optional[str] = Field(None, description="Currently active lead ID")
    conversation_stage: ConversationStage = Field(
        default=ConversationStage.DISCOVERY,
        description="Current conversation stage"
    )
    workflow_context: Dict[str, Any] = Field(default_factory=dict, description="Current workflow state")

    # Claude AI Context (Session-based Requirement)
    system_prompt_version: str = Field(default="1.0", description="System prompt version")
    conversation_history_summary: str = Field(default="", description="Summary of conversation history")
    active_guidance_types: List[GuidanceType] = Field(
        default_factory=lambda: [GuidanceType.RESPONSE_SUGGESTIONS],
        description="Active guidance types for session"
    )

    # Performance Tracking
    session_start_time: datetime = Field(default_factory=datetime.utcnow, description="Session start time")
    session_duration_seconds: int = Field(default=0, description="Session duration in seconds")
    messages_exchanged: int = Field(default=0, description="Total messages in session")
    guidance_requests: int = Field(default=0, description="Number of coaching requests")
    coaching_effectiveness_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Coaching effectiveness score (0-1)"
    )

    # Context Metadata
    client_info: Dict[str, Any] = Field(default_factory=dict, description="Client information context")
    property_context: Dict[str, Any] = Field(default_factory=dict, description="Property context information")
    market_context: Dict[str, Any] = Field(default_factory=dict, description="Market context information")

    # Session State
    is_active: bool = Field(default=True, description="Session active status")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    session_end_time: Optional[datetime] = Field(None, description="Session end time")

    # Integration Context
    ghl_contact_id: Optional[str] = Field(None, description="GoHighLevel contact ID")
    qualification_flow_id: Optional[str] = Field(None, description="Qualification flow ID")
    opportunity_id: Optional[str] = Field(None, description="GHL opportunity ID")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        validate_assignment = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()

    def add_message(self):
        """Increment message count and update activity"""
        self.messages_exchanged += 1
        self.update_activity()

    def add_guidance_request(self):
        """Increment guidance request count"""
        self.guidance_requests += 1
        self.update_activity()

    def end_session(self):
        """Mark session as ended and calculate duration"""
        self.session_end_time = datetime.utcnow()
        self.is_active = False
        if self.session_start_time:
            duration = self.session_end_time - self.session_start_time
            self.session_duration_seconds = int(duration.total_seconds())

    def get_session_duration_minutes(self) -> float:
        """Get session duration in minutes"""
        if self.session_end_time:
            duration = self.session_end_time - self.session_start_time
            return duration.total_seconds() / 60
        else:
            duration = datetime.utcnow() - self.session_start_time
            return duration.total_seconds() / 60

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        data = self.dict()
        # Convert datetime objects to ISO strings
        for field in ['session_start_time', 'last_activity', 'session_end_time']:
            if data.get(field):
                data[field] = data[field].isoformat() if isinstance(data[field], datetime) else data[field]
        return data


# ============================================================================
# Coaching History Models
# ============================================================================

class CoachingInteraction(BaseModel):
    """Model for individual coaching interactions"""

    # Identity
    id: Optional[int] = Field(None, description="Database ID")
    agent_id: str = Field(..., description="Agent ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    location_id: str = Field(..., description="Location context")

    # Coaching Details
    coaching_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Coaching timestamp")
    guidance_type: GuidanceType = Field(..., description="Type of guidance provided")
    user_message: str = Field(..., min_length=1, description="User's message/question")
    claude_response: Dict[str, Any] = Field(..., description="Claude's coaching response")

    # Effectiveness Tracking
    agent_followed_suggestion: Optional[bool] = Field(None, description="Did agent follow the suggestion?")
    outcome_rating: Optional[int] = Field(None, ge=1, le=5, description="Outcome rating 1-5")
    improvement_notes: Optional[str] = Field(None, description="Notes on improvement")

    # Context
    lead_stage: Optional[str] = Field(None, description="Lead stage during coaching")
    property_type: Optional[str] = Field(None, description="Property type context")

    class Config:
        """Pydantic configuration"""
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ============================================================================
# Request/Response Models for API
# ============================================================================

class CreateAgentProfileRequest(BaseModel):
    """Request model for creating agent profiles"""

    agent_name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    phone: Optional[str] = Field(None, max_length=50)

    primary_location_id: str = Field(..., min_length=1, max_length=255)
    accessible_locations: Optional[List[str]] = Field(None)
    role_permissions: Optional[Dict[str, List[AgentRole]]] = Field(None)

    primary_role: AgentRole
    secondary_roles: Optional[List[AgentRole]] = Field(None)
    years_experience: Optional[int] = Field(0, ge=0, le=50)
    specializations: Optional[List[str]] = Field(None)

    preferred_guidance_types: Optional[List[GuidanceType]] = Field(None)
    coaching_style_preference: Optional[CoachingStylePreference] = Field(None)
    communication_style: Optional[CommunicationStyle] = Field(None)

    timezone: Optional[str] = Field("UTC")
    language_preference: Optional[str] = Field("en-US")


class UpdateAgentProfileRequest(BaseModel):
    """Request model for updating agent profiles"""

    agent_name: Optional[str] = Field(None, min_length=1, max_length=255)
    phone: Optional[str] = Field(None, max_length=50)

    accessible_locations: Optional[List[str]] = Field(None)
    role_permissions: Optional[Dict[str, List[AgentRole]]] = Field(None)

    secondary_roles: Optional[List[AgentRole]] = Field(None)
    years_experience: Optional[int] = Field(None, ge=0, le=50)
    specializations: Optional[List[str]] = Field(None)

    preferred_guidance_types: Optional[List[GuidanceType]] = Field(None)
    coaching_style_preference: Optional[CoachingStylePreference] = Field(None)
    communication_style: Optional[CommunicationStyle] = Field(None)

    skill_levels: Optional[Dict[str, int]] = Field(None)
    notification_preferences: Optional[Dict[str, Any]] = Field(None)

    timezone: Optional[str] = Field(None)
    language_preference: Optional[str] = Field(None)
    is_active: Optional[bool] = Field(None)


class StartAgentSessionRequest(BaseModel):
    """Request model for starting agent sessions"""

    agent_id: str = Field(..., min_length=1, max_length=255)
    location_id: str = Field(..., min_length=1, max_length=255)

    current_lead_id: Optional[str] = Field(None)
    active_guidance_types: Optional[List[GuidanceType]] = Field(None)
    conversation_stage: Optional[ConversationStage] = Field(ConversationStage.DISCOVERY)

    client_info: Optional[Dict[str, Any]] = Field(None)
    property_context: Optional[Dict[str, Any]] = Field(None)
    market_context: Optional[Dict[str, Any]] = Field(None)

    ghl_contact_id: Optional[str] = Field(None)
    qualification_flow_id: Optional[str] = Field(None)


class CoachingRequest(BaseModel):
    """Request model for Claude coaching"""

    session_id: str = Field(..., min_length=1, max_length=255)
    user_message: str = Field(..., min_length=1, max_length=5000)
    guidance_types: Optional[List[GuidanceType]] = Field(None)

    additional_context: Optional[Dict[str, Any]] = Field(None)
    urgency_level: Optional[str] = Field(None)


class CoachingResponse(BaseModel):
    """Response model for Claude coaching"""

    session_id: str
    guidance_type: GuidanceType
    claude_response: Dict[str, Any]

    confidence_score: float = Field(..., ge=0.0, le=1.0)
    processing_time_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Coaching content
    recommended_response: Optional[str] = Field(None)
    coaching_suggestions: List[str] = Field(default_factory=list)
    next_questions: List[str] = Field(default_factory=list)
    objection_detected: Optional[str] = Field(None)
    urgency_level: Optional[str] = Field(None)
    reasoning: Optional[str] = Field(None)

    class Config:
        """Pydantic configuration"""
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


# ============================================================================
# Utility Functions
# ============================================================================

def create_agent_id(agent_name: str, email: str) -> str:
    """Generate agent ID from name and email"""
    import hashlib
    import re

    # Clean name for ID
    clean_name = re.sub(r'[^a-zA-Z0-9]', '_', agent_name.lower())

    # Create hash from email for uniqueness
    email_hash = hashlib.md5(email.encode()).hexdigest()[:8]

    return f"agent_{clean_name}_{email_hash}"


def create_session_id(agent_id: str) -> str:
    """Generate session ID"""
    import uuid
    timestamp = int(datetime.utcnow().timestamp())
    unique_id = str(uuid.uuid4())[:8]
    return f"session_{agent_id}_{timestamp}_{unique_id}"


# ============================================================================
# Export all models
# ============================================================================

__all__ = [
    # Enums
    'AgentRole',
    'GuidanceType',
    'CoachingStylePreference',
    'CommunicationStyle',
    'ConversationStage',
    'SessionStatus',

    # Core models
    'AgentProfile',
    'AgentSession',
    'CoachingInteraction',

    # Request/Response models
    'CreateAgentProfileRequest',
    'UpdateAgentProfileRequest',
    'StartAgentSessionRequest',
    'CoachingRequest',
    'CoachingResponse',

    # Utilities
    'create_agent_id',
    'create_session_id'
]