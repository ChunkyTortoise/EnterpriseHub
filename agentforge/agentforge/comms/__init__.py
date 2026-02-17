"""Communications module for AgentForge.

This module provides inter-agent communication:
- Message envelope and routing
- Message bus for pub/sub
- Request/response patterns
- Agent-to-agent delegation
- A2A protocol support
"""

from agentforge.comms.a2a import A2AProtocolSupport, AgentCard
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
    # A2A
    "AgentCard",
    "A2AProtocolSupport",
]
