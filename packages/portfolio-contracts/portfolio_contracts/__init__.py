"""portfolio-contracts — Shared Pydantic v2 types for AI portfolio products."""

from portfolio_contracts.agents import AgentAction, AgentStatus
from portfolio_contracts.api import APIError, ErrorDetail, PaginationMeta
from portfolio_contracts.documents import DocumentChunk, DocumentMetadata, DocumentType
from portfolio_contracts.llm import CostEstimate, LLMProvider, LLMResponse, TokenUsage

__all__ = [
    "AgentAction",
    "AgentStatus",
    "APIError",
    "CostEstimate",
    "DocumentChunk",
    "DocumentMetadata",
    "DocumentType",
    "ErrorDetail",
    "LLMProvider",
    "LLMResponse",
    "PaginationMeta",
    "TokenUsage",
]

__version__ = "0.1.0"
