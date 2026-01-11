"""
Real-Time Collaboration Models for EnterpriseHub

Data models for live agent coordination, team collaboration, and
real-time communication with sub-50ms message latency.

Performance Targets:
- Message latency: <50ms
- Connection establishment: <100ms
- Concurrent users: 1000+ per instance
- Message throughput: 10,000 msg/sec
- Uptime: 99.95%
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field, validator


class RoomType(str, Enum):
    """Types of collaboration rooms."""
    AGENT_TEAM = "agent_team"  # Team coordination
    CLIENT_SESSION = "client_session"  # Client portal communication
    LEAD_COLLABORATION = "lead_collaboration"  # Lead handoff and coordination
    PROPERTY_TOUR = "property_tour"  # Virtual property tour coordination
    TRAINING_SESSION = "training_session"  # Agent training and coaching
    EMERGENCY_RESPONSE = "emergency_response"  # Urgent issue coordination


class MessageType(str, Enum):
    """Types of collaboration messages."""
    TEXT = "text"
    SYSTEM = "system"
    TYPING_INDICATOR = "typing_indicator"
    STATUS_UPDATE = "status_update"
    FILE_SHARE = "file_share"
    DOCUMENT_SHARE = "document_share"
    LEAD_HANDOFF = "lead_handoff"
    PROPERTY_SHARE = "property_share"
    COACHING_TIP = "coaching_tip"
    ALERT = "alert"
    COMMAND = "command"


class UserStatus(str, Enum):
    """User presence status."""
    ONLINE = "online"
    AWAY = "away"
    BUSY = "busy"
    OFFLINE = "offline"
    IN_CALL = "in_call"
    DO_NOT_DISTURB = "do_not_disturb"


class MessagePriority(str, Enum):
    """Message priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"


class DeliveryStatus(str, Enum):
    """Message delivery status."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


# Pydantic Models for API

class RoomMember(BaseModel):
    """Room member information."""
    user_id: str
    tenant_id: str
    display_name: str
    role: str = "member"  # member, moderator, admin
    status: UserStatus = UserStatus.ONLINE
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
    permissions: Set[str] = Field(default_factory=set)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v)
        }


class CollaborationMessage(BaseModel):
    """Real-time collaboration message."""
    message_id: str
    room_id: str
    sender_id: str
    sender_name: str
    message_type: MessageType
    content: str
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Delivery tracking
    delivery_status: DeliveryStatus = DeliveryStatus.PENDING
    sent_at: datetime = Field(default_factory=datetime.utcnow)
    delivered_at: Optional[datetime] = None
    read_by: Set[str] = Field(default_factory=set)

    # Performance metrics
    latency_ms: float = 0.0

    # File/document attachments
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

    # Reply threading
    reply_to: Optional[str] = None
    thread_id: Optional[str] = None

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            set: lambda v: list(v)
        }


class Room(BaseModel):
    """Collaboration room."""
    room_id: str
    tenant_id: str
    room_type: RoomType
    name: str
    description: Optional[str] = None

    # Members and permissions
    members: List[RoomMember] = Field(default_factory=list)
    max_members: int = 50

    # Room state
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str
    is_active: bool = True
    is_archived: bool = False

    # Message history
    message_count: int = 0
    last_message_at: Optional[datetime] = None

    # Room settings
    settings: Dict[str, Any] = Field(default_factory=dict)

    # Context data (lead, property, etc.)
    context: Dict[str, Any] = Field(default_factory=dict)

    # Performance tracking
    total_messages_sent: int = 0
    average_latency_ms: float = 0.0

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

    @validator('members')
    def validate_member_limit(cls, v, values):
        """Validate member count against max_members."""
        max_members = values.get('max_members', 50)
        if len(v) > max_members:
            raise ValueError(f"Room cannot have more than {max_members} members")
        return v


class PresenceUpdate(BaseModel):
    """User presence status update."""
    user_id: str
    tenant_id: str
    status: UserStatus
    status_message: Optional[str] = None
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    current_room_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class TypingIndicator(BaseModel):
    """Typing indicator event."""
    room_id: str
    user_id: str
    user_name: str
    is_typing: bool
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageDeliveryConfirmation(BaseModel):
    """Message delivery confirmation."""
    message_id: str
    room_id: str
    delivery_status: DeliveryStatus
    delivered_to: List[str] = Field(default_factory=list)
    failed_recipients: List[str] = Field(default_factory=list)
    latency_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class FileAttachment(BaseModel):
    """File attachment for collaboration messages."""
    file_id: str
    filename: str
    file_size: int
    mime_type: str
    storage_url: str
    thumbnail_url: Optional[str] = None
    uploaded_by: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class RoomInvitation(BaseModel):
    """Room invitation for new members."""
    invitation_id: str
    room_id: str
    tenant_id: str
    invited_by: str
    invited_user_id: str
    invited_user_email: Optional[str] = None
    role: str = "member"
    message: Optional[str] = None
    expires_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    accepted_at: Optional[datetime] = None
    status: str = "pending"  # pending, accepted, rejected, expired

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


# Dataclasses for internal use

@dataclass
class ConnectionState:
    """WebSocket connection state."""
    connection_id: str
    user_id: str
    tenant_id: str
    room_ids: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    status: UserStatus = UserStatus.ONLINE
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RoomState:
    """In-memory room state for fast access."""
    room_id: str
    tenant_id: str
    room_type: RoomType
    member_ids: Set[str] = field(default_factory=set)
    active_connections: Set[str] = field(default_factory=set)
    message_queue_size: int = 0
    last_activity: datetime = field(default_factory=datetime.utcnow)
    performance_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class MessageBatch:
    """Batch of messages for efficient processing."""
    batch_id: str
    room_id: str
    messages: List[CollaborationMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    total_size_bytes: int = 0


@dataclass
class CollaborationMetrics:
    """Real-time collaboration performance metrics."""
    # Connection metrics
    total_connections: int = 0
    active_rooms: int = 0
    total_messages_sent: int = 0

    # Performance metrics
    average_message_latency_ms: float = 0.0
    p95_message_latency_ms: float = 0.0
    p99_message_latency_ms: float = 0.0

    # Throughput metrics
    messages_per_second: float = 0.0
    bytes_per_second: float = 0.0

    # Connection health
    connection_success_rate: float = 1.0
    message_delivery_rate: float = 1.0

    # System health
    redis_pub_sub_healthy: bool = True
    websocket_server_healthy: bool = True

    # Resource utilization
    memory_usage_mb: float = 0.0
    cpu_usage_percent: float = 0.0

    # Target compliance
    latency_target_met: bool = True  # <50ms target
    throughput_target_met: bool = True  # 10k msg/sec target
    uptime_target_met: bool = True  # 99.95% target


# API Request/Response Models

class CreateRoomRequest(BaseModel):
    """Request to create a new collaboration room."""
    tenant_id: str
    room_type: RoomType
    name: str
    description: Optional[str] = None
    created_by: str
    initial_members: List[str] = Field(default_factory=list)
    max_members: int = 50
    settings: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        use_enum_values = True


class JoinRoomRequest(BaseModel):
    """Request to join a collaboration room."""
    room_id: str
    user_id: str
    display_name: str
    role: str = "member"

    class Config:
        use_enum_values = True


class SendMessageRequest(BaseModel):
    """Request to send a message."""
    room_id: str
    sender_id: str
    sender_name: str
    message_type: MessageType = MessageType.TEXT
    content: str
    priority: MessagePriority = MessagePriority.NORMAL
    metadata: Dict[str, Any] = Field(default_factory=dict)
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    reply_to: Optional[str] = None

    class Config:
        use_enum_values = True


class UpdatePresenceRequest(BaseModel):
    """Request to update user presence."""
    user_id: str
    tenant_id: str
    status: UserStatus
    status_message: Optional[str] = None
    current_room_id: Optional[str] = None

    class Config:
        use_enum_values = True


class GetRoomHistoryRequest(BaseModel):
    """Request to get room message history."""
    room_id: str
    limit: int = Field(default=50, ge=1, le=500)
    before_message_id: Optional[str] = None
    after_message_id: Optional[str] = None
    message_types: Optional[List[MessageType]] = None

    class Config:
        use_enum_values = True


__all__ = [
    # Enums
    "RoomType",
    "MessageType",
    "UserStatus",
    "MessagePriority",
    "DeliveryStatus",

    # Pydantic Models
    "RoomMember",
    "CollaborationMessage",
    "Room",
    "PresenceUpdate",
    "TypingIndicator",
    "MessageDeliveryConfirmation",
    "FileAttachment",
    "RoomInvitation",

    # Dataclasses
    "ConnectionState",
    "RoomState",
    "MessageBatch",
    "CollaborationMetrics",

    # Request/Response Models
    "CreateRoomRequest",
    "JoinRoomRequest",
    "SendMessageRequest",
    "UpdatePresenceRequest",
    "GetRoomHistoryRequest",
]
