"""
LLM Provider Protocol

Defines the standard interface for LLM providers across the portfolio.
All LLM integrations (Claude, GPT, Gemini, etc.) should implement this protocol
to ensure interoperability with AgentForge and other orchestration systems.

Usage:
    from shared.contracts.llm_provider import LLMProvider, LLMMessage

    class ClaudeProvider(LLMProvider):
        async def complete(
            self,
            messages: list[LLMMessage],
            model: str | None = None,
            temperature: float = 0.7,
            max_tokens: int = 4096,
            **kwargs: Any,
        ) -> LLMResponse:
            # Implementation for Claude API
            ...
"""

from typing import Protocol, AsyncIterator, Any, Literal
from pydantic import BaseModel, Field, ConfigDict


class LLMMessage(BaseModel):
    """
    A single message in an LLM conversation.

    Attributes:
        role: The role of the message sender ("system", "user", or "assistant")
        content: The text content of the message
        name: Optional name for the message sender (useful for multi-turn conversations)
    """

    role: Literal["system", "user", "assistant"]
    content: str
    name: str | None = None

    model_config = ConfigDict(frozen=True)


class LLMResponse(BaseModel):
    """
    Standardized response from an LLM completion.

    Attributes:
        content: The generated text content
        model: The model identifier used for generation
        usage: Token usage statistics with prompt_tokens and completion_tokens
        latency_ms: Time taken for the completion in milliseconds
        finish_reason: Why the generation stopped (e.g., "stop", "length", "content_filter")
        metadata: Additional provider-specific metadata
    """

    content: str
    model: str
    usage: dict[str, int] = Field(
        default_factory=lambda: {"prompt_tokens": 0, "completion_tokens": 0}
    )
    latency_ms: float = 0.0
    finish_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(frozen=True)

    @property
    def total_tokens(self) -> int:
        """Total tokens used (prompt + completion)."""
        return self.usage.get("prompt_tokens", 0) + self.usage.get("completion_tokens", 0)


class LLMStreamChunk(BaseModel):
    """
    A single chunk in a streaming LLM response.

    Attributes:
        content: The text content of this chunk
        finish_reason: Why the generation stopped (None if still generating)
    """

    content: str
    finish_reason: str | None = None

    model_config = ConfigDict(frozen=True)


class LLMProvider(Protocol):
    """
    Protocol defining the interface for LLM providers.

    All LLM integrations must implement this protocol to be compatible
    with AgentForge's orchestration system and other portfolio components.

    The protocol supports both synchronous-style async completion and
    streaming responses for real-time applications.

    Example implementation:
        class OpenAIProvider(LLMProvider):
            def __init__(self, api_key: str):
                self.client = AsyncOpenAI(api_key=api_key)

            async def complete(
                self,
                messages: list[LLMMessage],
                model: str | None = None,
                temperature: float = 0.7,
                max_tokens: int = 4096,
                **kwargs: Any,
            ) -> LLMResponse:
                start = time.time()
                response = await self.client.chat.completions.create(
                    model=model or "gpt-4o",
                    messages=[{"role": m.role, "content": m.content} for m in messages],
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )
                return LLMResponse(
                    content=response.choices[0].message.content,
                    model=response.model,
                    usage={
                        "prompt_tokens": response.usage.prompt_tokens,
                        "completion_tokens": response.usage.completion_tokens,
                    },
                    latency_ms=(time.time() - start) * 1000,
                    finish_reason=response.choices[0].finish_reason,
                )
    """

    async def complete(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Generate a completion for the given messages.

        Args:
            messages: List of conversation messages
            model: Optional model override (uses provider default if None)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMProviderError: If the completion fails
        """
        ...

    async def stream(
        self,
        messages: list[LLMMessage],
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        **kwargs: Any,
    ) -> AsyncIterator[LLMStreamChunk]:
        """
        Generate a streaming completion for the given messages.

        This is useful for real-time applications where you want to
        display content as it's generated.

        Args:
            messages: List of conversation messages
            model: Optional model override (uses provider default if None)
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters

        Yields:
            LLMStreamChunk objects containing partial content

        Raises:
            LLMProviderError: If the streaming completion fails
        """
        ...


class LLMProviderError(Exception):
    """Base exception for LLM provider errors."""

    def __init__(
        self,
        message: str,
        provider: str | None = None,
        model: str | None = None,
        status_code: int | None = None,
    ):
        super().__init__(message)
        self.provider = provider
        self.model = model
        self.status_code = status_code


class LLMRateLimitError(LLMProviderError):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class LLMContentFilterError(LLMProviderError):
    """Raised when content is filtered by provider safety systems."""

    def __init__(
        self,
        message: str = "Content filtered by provider",
        filter_reason: str | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.filter_reason = filter_reason


class LLMTokenLimitError(LLMProviderError):
    """Raised when token limit is exceeded."""

    def __init__(
        self,
        message: str = "Token limit exceeded",
        requested_tokens: int | None = None,
        max_tokens: int | None = None,
        **kwargs,
    ):
        super().__init__(message, **kwargs)
        self.requested_tokens = requested_tokens
        self.max_tokens = max_tokens
