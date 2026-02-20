"""
Shared Contracts Subpackage

Contains interface contracts for cross-product interoperability.
"""

from shared.contracts.agent_result import AgentResult, AgentStatus
from shared.contracts.eval_metrics import EvalMetric, EvalSample, EvalScore
from shared.contracts.llm_provider import LLMMessage, LLMProvider, LLMResponse
from shared.contracts.mcp_base import MCPServerConfig, create_mcp_server

__all__ = [
    "LLMMessage",
    "LLMResponse",
    "LLMProvider",
    "MCPServerConfig",
    "create_mcp_server",
    "AgentResult",
    "AgentStatus",
    "EvalSample",
    "EvalScore",
    "EvalMetric",
]
