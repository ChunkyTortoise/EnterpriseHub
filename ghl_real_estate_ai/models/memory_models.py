"""
Enhanced Memory Models for Multi-Tenant Continuous Memory System.

These models extend the existing memory service with PostgreSQL/Redis backend
while maintaining backward compatibility with the current file-based system.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from uuid import UUID
from dataclasses import dataclass, field
from enum import Enum
import json

from pydantic import BaseModel, Field
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class ConversationStage(str, Enum):
    """Conversation stages for lead lifecycle tracking."""
    INITIAL_CONTACT = "initial_contact"
    QUALIFYING = "qualifying"
    NURTURING = "nurturing"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class MessageRole(str, Enum):
    """Message roles in conversation."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class InteractionType(str, Enum):
    """Property interaction types."""
    VIEW = "view"
    LIKE = "like"
    PASS = "pass"
    INQUIRY = "inquiry"
    SHARE = "share"
    SAVE = "save"


class PreferenceType(str, Enum):
    """Behavioral preference types."""
    COMMUNICATION_STYLE = "communication_style"
    DECISION_PATTERN = "decision_pattern"
    INFO_PROCESSING = "info_processing"
    RESPONSE_TIMING = "response_timing"
    PROPERTY_FOCUS = "property_focus"
    BUDGET_FLEXIBILITY = "budget_flexibility"
    LOCATION_FLEXIBILITY = "location_flexibility"


@dataclass
class Tenant:
    """Tenant configuration model."""
    id: UUID
    location_id: str
    name: str
    claude_config: Dict[str, Any] = field(default_factory=dict)
    behavioral_learning_enabled: bool = True
    settings: Dict[str, Any] = field(default_factory=dict)
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class ConversationMessage:
    """Individual conversation message with metadata."""
    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    claude_reasoning: Optional[str] = None
    response_time_ms: Optional[int] = None
    token_count: Optional[int] = None
    message_order: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "role": self.role.value,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
            "claude_reasoning": self.claude_reasoning,
            "response_time_ms": self.response_time_ms,
            "token_count": self.token_count,
            "message_order": self.message_order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            conversation_id=UUID(data["conversation_id"]),
            role=MessageRole(data["role"]),
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
            claude_reasoning=data.get("claude_reasoning"),
            response_time_ms=data.get("response_time_ms"),
            token_count=data.get("token_count"),
            message_order=data.get("message_order", 0)
        )


@dataclass
class BehavioralPreference:
    """Learned behavioral preference with confidence scoring."""
    id: UUID
    conversation_id: UUID
    preference_type: PreferenceType
    preference_value: Dict[str, Any]
    confidence_score: float  # 0.0 to 1.0
    learned_from: str
    source_interaction_id: Optional[UUID] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "preference_type": self.preference_type.value,
            "preference_value": self.preference_value,
            "confidence_score": self.confidence_score,
            "learned_from": self.learned_from,
            "source_interaction_id": str(self.source_interaction_id) if self.source_interaction_id else None,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'BehavioralPreference':
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            conversation_id=UUID(data["conversation_id"]),
            preference_type=PreferenceType(data["preference_type"]),
            preference_value=data["preference_value"],
            confidence_score=data["confidence_score"],
            learned_from=data["learned_from"],
            source_interaction_id=UUID(data["source_interaction_id"]) if data.get("source_interaction_id") else None,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class PropertyInteraction:
    """Property interaction with behavioral analysis."""
    id: UUID
    conversation_id: UUID
    property_id: Optional[str]
    property_data: Dict[str, Any]
    interaction_type: InteractionType
    feedback_category: Optional[str] = None
    feedback_text: Optional[str] = None
    time_on_property: float = 0.0  # seconds
    claude_analysis: Dict[str, Any] = field(default_factory=dict)
    behavioral_signals: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "conversation_id": str(self.conversation_id),
            "property_id": self.property_id,
            "property_data": self.property_data,
            "interaction_type": self.interaction_type.value,
            "feedback_category": self.feedback_category,
            "feedback_text": self.feedback_text,
            "time_on_property": self.time_on_property,
            "claude_analysis": self.claude_analysis,
            "behavioral_signals": self.behavioral_signals,
            "timestamp": self.timestamp.isoformat(),
            "created_at": self.created_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PropertyInteraction':
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            conversation_id=UUID(data["conversation_id"]),
            property_id=data.get("property_id"),
            property_data=data["property_data"],
            interaction_type=InteractionType(data["interaction_type"]),
            feedback_category=data.get("feedback_category"),
            feedback_text=data.get("feedback_text"),
            time_on_property=data.get("time_on_property", 0.0),
            claude_analysis=data.get("claude_analysis", {}),
            behavioral_signals=data.get("behavioral_signals", {}),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            created_at=datetime.fromisoformat(data["created_at"])
        )


@dataclass
class Conversation:
    """Enhanced conversation model with behavioral context."""
    id: UUID
    tenant_id: UUID
    contact_id: str
    conversation_stage: ConversationStage = ConversationStage.INITIAL_CONTACT
    lead_score: int = 0
    last_interaction_at: datetime = field(default_factory=datetime.utcnow)
    extracted_preferences: Dict[str, Any] = field(default_factory=dict)
    lead_intelligence: Dict[str, Any] = field(default_factory=dict)
    previous_sessions_summary: Optional[str] = None
    behavioral_profile: Dict[str, Any] = field(default_factory=dict)
    session_count: int = 1
    total_messages: int = 0
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "id": str(self.id),
            "tenant_id": str(self.tenant_id),
            "contact_id": self.contact_id,
            "conversation_stage": self.conversation_stage.value,
            "lead_score": self.lead_score,
            "last_interaction_at": self.last_interaction_at.isoformat(),
            "extracted_preferences": self.extracted_preferences,
            "lead_intelligence": self.lead_intelligence,
            "previous_sessions_summary": self.previous_sessions_summary,
            "behavioral_profile": self.behavioral_profile,
            "session_count": self.session_count,
            "total_messages": self.total_messages,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create from dictionary."""
        return cls(
            id=UUID(data["id"]),
            tenant_id=UUID(data["tenant_id"]),
            contact_id=data["contact_id"],
            conversation_stage=ConversationStage(data.get("conversation_stage", "initial_contact")),
            lead_score=data.get("lead_score", 0),
            last_interaction_at=datetime.fromisoformat(data["last_interaction_at"]),
            extracted_preferences=data.get("extracted_preferences", {}),
            lead_intelligence=data.get("lead_intelligence", {}),
            previous_sessions_summary=data.get("previous_sessions_summary"),
            behavioral_profile=data.get("behavioral_profile", {}),
            session_count=data.get("session_count", 1),
            total_messages=data.get("total_messages", 0),
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"])
        )


@dataclass
class ConversationWithMemory:
    """Complete conversation context with memory."""
    conversation: Conversation
    message_history: List[ConversationMessage] = field(default_factory=list)
    behavioral_preferences: List[BehavioralPreference] = field(default_factory=list)
    property_interactions: List[PropertyInteraction] = field(default_factory=list)
    is_returning_lead: bool = False
    hours_since_last_interaction: float = 0.0
    memory_context_summary: Optional[str] = None

    def to_cache(self) -> str:
        """Serialize to JSON string for Redis cache."""
        cache_data = {
            "conversation": self.conversation.to_dict(),
            "message_history": [msg.to_dict() for msg in self.message_history],
            "behavioral_preferences": [pref.to_dict() for pref in self.behavioral_preferences],
            "property_interactions": [interaction.to_dict() for interaction in self.property_interactions],
            "is_returning_lead": self.is_returning_lead,
            "hours_since_last_interaction": self.hours_since_last_interaction,
            "memory_context_summary": self.memory_context_summary
        }
        return json.dumps(cache_data, default=str)

    @classmethod
    def from_cache(cls, cache_data: str) -> 'ConversationWithMemory':
        """Deserialize from JSON cache."""
        data = json.loads(cache_data)
        return cls(
            conversation=Conversation.from_dict(data["conversation"]),
            message_history=[ConversationMessage.from_dict(msg) for msg in data.get("message_history", [])],
            behavioral_preferences=[BehavioralPreference.from_dict(pref) for pref in data.get("behavioral_preferences", [])],
            property_interactions=[PropertyInteraction.from_dict(interaction) for interaction in data.get("property_interactions", [])],
            is_returning_lead=data.get("is_returning_lead", False),
            hours_since_last_interaction=data.get("hours_since_last_interaction", 0.0),
            memory_context_summary=data.get("memory_context_summary")
        )

    def get_recent_messages(self, limit: int = 10) -> List[ConversationMessage]:
        """Get recent messages for context."""
        return sorted(self.message_history, key=lambda x: x.timestamp, reverse=True)[:limit]

    def get_behavioral_insights(self) -> Dict[str, Any]:
        """Get summarized behavioral insights."""
        insights = {}
        for pref in self.behavioral_preferences:
            if pref.confidence_score >= 0.7:  # High confidence only
                if pref.preference_type.value not in insights:
                    insights[pref.preference_type.value] = []
                insights[pref.preference_type.value].append({
                    "value": pref.preference_value,
                    "confidence": pref.confidence_score,
                    "learned_from": pref.learned_from,
                    "timestamp": pref.timestamp.isoformat()
                })
        return insights

    def get_property_interaction_patterns(self) -> Dict[str, Any]:
        """Analyze property interaction patterns."""
        if not self.property_interactions:
            return {}

        total_interactions = len(self.property_interactions)
        like_count = sum(1 for i in self.property_interactions if i.interaction_type == InteractionType.LIKE)
        pass_count = sum(1 for i in self.property_interactions if i.interaction_type == InteractionType.PASS)
        avg_time_on_property = sum(i.time_on_property for i in self.property_interactions) / total_interactions

        return {
            "total_interactions": total_interactions,
            "like_ratio": like_count / total_interactions if total_interactions > 0 else 0,
            "pass_ratio": pass_count / total_interactions if total_interactions > 0 else 0,
            "avg_time_on_property": avg_time_on_property,
            "engagement_level": "high" if avg_time_on_property > 30 else "medium" if avg_time_on_property > 10 else "low"
        }


class CommunicationStyle(BaseModel):
    """Communication style analysis."""
    formality_level: str = Field(..., description="formal, casual, professional")
    directness_level: str = Field(..., description="direct, indirect, balanced")
    detail_preference: str = Field(..., description="detailed, summary, concise")
    response_speed: str = Field(..., description="immediate, measured, delayed")
    decision_style: str = Field(..., description="analytical, intuitive, collaborative")

    @property
    def description(self) -> str:
        """Get human-readable description."""
        return f"{self.formality_level}, {self.directness_level}, prefers {self.detail_preference} information"


class QualificationAnalysis(BaseModel):
    """Analysis of lead qualification status."""
    answered_questions: List[str] = Field(default_factory=list)
    missing_qualifiers: List[str] = Field(default_factory=list)
    next_priority_question: Optional[str] = None
    jorge_methodology_score: int = Field(default=0, description="Number of Jorge's 7 questions answered")
    confidence_level: float = Field(default=0.5, ge=0.0, le=1.0)
    qualification_gaps: List[str] = Field(default_factory=list)
    recommended_approach: Optional[str] = None


class ConversationContext(BaseModel):
    """Conversation context for intelligent responses."""
    stage: ConversationStage
    recent_messages: List[Dict[str, Any]] = Field(default_factory=list)
    extracted_preferences: Dict[str, Any] = Field(default_factory=dict)
    behavioral_profile: Dict[str, Any] = Field(default_factory=dict)
    lead_score: int = 0
    session_gap_hours: float = 0.0
    is_returning_session: bool = False


# Legacy compatibility functions for backward compatibility with existing MemoryService
def convert_legacy_context_to_conversation(
    legacy_context: Dict[str, Any],
    tenant_id: UUID,
    contact_id: str
) -> ConversationWithMemory:
    """Convert legacy file-based context to new conversation model."""

    conversation = Conversation(
        id=UUID(legacy_context.get("conversation_id", "00000000-0000-0000-0000-000000000000")),
        tenant_id=tenant_id,
        contact_id=contact_id,
        conversation_stage=ConversationStage(legacy_context.get("conversation_stage", "initial_contact")),
        lead_score=legacy_context.get("lead_score", 0),
        last_interaction_at=datetime.fromisoformat(legacy_context.get("last_interaction_at", datetime.utcnow().isoformat())),
        extracted_preferences=legacy_context.get("extracted_preferences", {}),
        lead_intelligence=legacy_context.get("lead_intelligence", {}),
        previous_sessions_summary=legacy_context.get("previous_sessions_summary"),
        behavioral_profile=legacy_context.get("behavioral_profile", {}),
        session_count=legacy_context.get("session_count", 1),
        total_messages=len(legacy_context.get("conversation_history", [])),
        created_at=datetime.fromisoformat(legacy_context.get("created_at", datetime.utcnow().isoformat())),
        updated_at=datetime.fromisoformat(legacy_context.get("updated_at", datetime.utcnow().isoformat()))
    )

    # Convert message history
    message_history = []
    for i, msg in enumerate(legacy_context.get("conversation_history", [])):
        message = ConversationMessage(
            id=UUID(f"00000000-0000-0000-0000-{i:012d}"),  # Generate deterministic UUIDs for migration
            conversation_id=conversation.id,
            role=MessageRole(msg.get("role", "user")),
            content=msg.get("content", ""),
            timestamp=datetime.fromisoformat(msg.get("timestamp", datetime.utcnow().isoformat())),
            metadata=msg.get("metadata", {}),
            message_order=i
        )
        message_history.append(message)

    return ConversationWithMemory(
        conversation=conversation,
        message_history=message_history,
        behavioral_preferences=[],  # Will be populated during migration
        property_interactions=[]     # Will be populated during migration
    )


def convert_conversation_to_legacy_context(conversation_with_memory: ConversationWithMemory) -> Dict[str, Any]:
    """Convert new conversation model back to legacy format for backward compatibility."""

    conversation = conversation_with_memory.conversation

    legacy_context = {
        "contact_id": conversation.contact_id,
        "location_id": str(conversation.tenant_id),  # Map tenant_id to location_id for compatibility
        "conversation_history": [
            {
                "role": msg.role.value,
                "content": msg.content,
                "timestamp": msg.timestamp.isoformat(),
                "metadata": msg.metadata
            }
            for msg in conversation_with_memory.message_history
        ],
        "extracted_preferences": conversation.extracted_preferences,
        "lead_score": conversation.lead_score,
        "conversation_stage": conversation.conversation_stage.value,
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "last_interaction_at": conversation.last_interaction_at.isoformat(),
        "previous_sessions_summary": conversation.previous_sessions_summary,
        "lead_intelligence": conversation.lead_intelligence,
        "behavioral_profile": conversation.behavioral_profile,
        "session_count": conversation.session_count,
        "total_messages": conversation.total_messages
    }

    # Add memory-specific fields for enhanced functionality
    if conversation_with_memory.is_returning_lead:
        legacy_context["is_returning_lead"] = True
        legacy_context["hours_since_last_interaction"] = conversation_with_memory.hours_since_last_interaction

    return legacy_context