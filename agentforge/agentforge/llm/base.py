"""Base LLM provider interface for AgentForge.

This module defines the abstract interface that all LLM providers must implement.
Provides a unified interface for multiple LLM backends with support for
completions, streaming, tool calling, and embeddings.
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any

from pydantic import BaseModel, Field


class LLMUsage(BaseModel):
    """Token usage statistics for an LLM request.

    Attributes:
        prompt_tokens: Number of tokens in the prompt.
        completion_tokens: Number of tokens in the completion.
        total_tokens: Total tokens used (prompt + completion).
    """

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMResponse(BaseModel):
    """Response from an LLM completion request.

    Attributes:
        content: The generated text content (may be empty if tool_calls present).
        model: The model that generated this response.
        usage: Token usage statistics.
        tool_calls: List of tool calls requested by the model (as dicts).
        finish_reason: Reason for completion (stop, length, tool_calls, etc.).
        latency_ms: Time taken for the request in milliseconds.
    """

    content: str = ""
    model: str
    usage: LLMUsage = Field(default_factory=LLMUsage)
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str | None = None
    latency_ms: float = 0.0


class LLMConfig(BaseModel):
    """Configuration for LLM completion requests.

    Attributes:
        model: Model identifier (e.g., "gpt-4o", "claude-3-opus").
        temperature: Sampling temperature (0.0 to 2.0).
        max_tokens: Maximum tokens in the response.
        top_p: Nucleus sampling parameter.
        stop: Stop sequences that halt generation.
        tools: List of tool schemas available for the model.
        tool_choice: Tool selection mode ("auto", "none", "required", or specific tool).
    """

    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    top_p: float = 1.0
    stop: list[str] | None = None
    tools: list[dict[str, Any]] | None = None
    tool_choice: str | dict[str, Any] | None = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers.

    Defines the interface that all LLM implementations must follow.
    Supports both regular and streaming responses, with optional
    tool calling and embedding capabilities.

    Subclasses must implement the complete() and stream() methods.

    Example:
        ```python
        class MyProvider(LLMProvider):
            async def complete(self, messages, config=None, **kwargs):
                # Implementation here
                return LLMResponse(content="Hello!", model="my-model")

            async def stream(self, messages, config=None, **kwargs):
                yield "Hello"
                yield "!"
        ```
    """

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Complete a chat completion request.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'.
            config: Optional configuration override for this request.
            **kwargs: Additional provider-specific parameters.

        Returns:
            LLMResponse with the generated content.

        Raises:
            LLMError: If the request fails.
        """
        ...

    @abstractmethod
    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a chat completion response.

        Args:
            messages: Conversation history as list of dicts with 'role' and 'content'.
            config: Optional configuration override for this request.
            **kwargs: Additional provider-specific parameters.

        Yields:
            Chunks of generated text.

        Raises:
            LLMError: If the request fails.
        """
        ...

    def supports_tools(self) -> bool:
        """Return True if this provider supports tool calling.

        Returns:
            bool: True if tool calling is supported, False otherwise.
        """
        return False

    def supports_streaming(self) -> bool:
        """Return True if this provider supports streaming.

        Returns:
            bool: True if streaming is supported, False otherwise.
        """
        return True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for texts.

        This is an optional method that providers can implement
        if they support embeddings.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.

        Raises:
            NotImplementedError: If the provider doesn't support embeddings.
        """
        raise NotImplementedError("Embedding not supported by this provider")


class LLMError(Exception):
    """Exception raised when an LLM request fails.

    Attributes:
        message: Error description.
        provider: Name of the provider that raised the error.
        status_code: HTTP status code if applicable.
        details: Additional error details.
    """

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.provider = provider
        self.status_code = status_code
        self.details = details or {}


__all__ = ["LLMProvider", "LLMConfig", "LLMResponse", "LLMUsage", "LLMError"]
