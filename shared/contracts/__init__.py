"""
Shared Contracts Subpackage

Contains interface contracts for cross-product interoperability.
"""

from shared.contracts.llm_provider import LLMMessage, LLMResponse, LLMProvider
from shared.contracts.mcp_base import MCPServerConfig, create_mcp_server
from shared.contracts.agent_result import AgentResult, AgentStatus
from shared.contracts.eval_metrics import EvalSample, EvalScore, EvalMetric

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
