from datetime import datetime
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


class AgentMessage(BaseModel):
    """A message within the agentic workflow."""

    role: str = Field(..., description="Role of the sender (user, assistant, tool, system)")
    content: str = Field(..., description="Content of the message")
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentState(TypedDict):
    """The global state for the EnterpriseHub LangGraph orchestration."""

    messages: Annotated[List[AgentMessage], "The conversation history"]
    lead_id: str
    tenant_id: str
    current_agent: str
    metadata: Dict[str, Any]
    next_action: Optional[str]
    errors: List[str]


class LeadProfile(BaseModel):
    """Structured lead profile for reasoning."""

    lead_id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    intent_score: float = 0.0
    sentiment: str = "neutral"
    preferences: Dict[str, Any] = Field(default_factory=dict)
    last_updated: datetime = Field(default_factory=datetime.now)
