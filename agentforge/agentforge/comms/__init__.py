"""Communications module for AgentForge.

This module provides inter-agent communication:
- Message envelope and routing
- Message bus for pub/sub
- Request/response patterns
- Agent-to-agent delegation
- A2A protocol support (v0.3, July 2025)

A2A Protocol:
- AgentCard for agent discovery at /.well-known/agent.json
- Task lifecycle management (submitted, working, completed, failed, cancelled)
- JSON-RPC 2.0 message wrappers for protocol communication
- Zero-dependency HTTP client using urllib.request with asyncio.to_thread
"""

# Legacy A2A support (backward compatible)
from agentforge.comms.a2a import A2AProtocolSupport

# New comprehensive A2A types
from agentforge.comms.a2a_types import (
    A2AErrorCode,
    A2AMessage,
    A2AResponse,
    AgentCapability,
    AgentCard,
    Task,
    TaskStatus,
    TaskUpdate,
)

# A2A client and server
from agentforge.comms.a2a_bridge import A2ABridge
from agentforge.comms.a2a_client import A2AClient, A2AClientError
from agentforge.comms.a2a_server import A2AServer

# Message and patterns
from agentforge.comms.message import MessageBus, MessageEnvelope
from agentforge.comms.patterns import (
    CommunicationPattern,
    DelegationPattern,
    PubSubPattern,
    RequestResponsePattern,
)

__all__ = [
    # Message
    "MessageEnvelope",
    "MessageBus",
    # Patterns
    "CommunicationPattern",
    "RequestResponsePattern",
    "DelegationPattern",
    "PubSubPattern",
    # Legacy A2A (backward compatible)
    "A2AProtocolSupport",
    # A2A Types
    "AgentCard",
    "AgentCapability",
    "Task",
    "TaskStatus",
    "TaskUpdate",
    "A2AMessage",
    "A2AResponse",
    "A2AErrorCode",
    # A2A Client/Server
    "A2AServer",
    "A2AClient",
    "A2AClientError",
    "A2ABridge",
]
