"""LiteLLM adapter for AgentForge.

This module provides an adapter for the LiteLLM library, offering a unified
interface to 100+ LLM providers (OpenAI, Anthropic, Google, Azure, etc.).

Requires the 'litellm' package: pip install agentforge[llm]
"""

import time
from collections.abc import AsyncIterator
from typing import Any

from agentforge.llm.base import (
    LLMConfig,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMUsage,
)


class LiteLLMProvider(LLMProvider):
    """LLM provider using LiteLLM as the backend.

    LiteLLM provides a unified interface to 100+ LLM providers,
    handling API differences automatically. Supports fallbacks
    for high availability.

    Supported providers include:
    - OpenAI (gpt-4o, gpt-4-turbo, gpt-3.5-turbo, etc.)
    - Anthropic (claude-3-opus, claude-3-sonnet, claude-3-haiku, etc.)
    - Google (gemini-pro, gemini-1.5-pro, etc.)
    - Azure OpenAI
    - AWS Bedrock
    - Cohere
    - Replicate
    - And many more...

    Example:
        ```python
        provider = LiteLLMProvider(
            model="gpt-4o",
            fallbacks=["claude-3-opus", "gemini-pro"],
            api_key="sk-..."
        )
        response = await provider.complete([{"role": "user", "content": "Hello!"}])
        ```
    """

    def __init__(
        self,
        model: str,
        fallbacks: list[str] | None = None,
        api_key: str | None = None,
    ) -> None:
        """Initialize the LiteLLM provider.

        Args:
            model: Primary model identifier (e.g., "gpt-4o", "claude-3-opus").
            fallbacks: List of fallback models if primary fails.
            api_key: API key (can also use environment variables).
        """
        self.model = model
        self.fallbacks = fallbacks or []
        self.api_key = api_key
        self._litellm: Any = None

    def _get_litellm(self) -> Any:
        """Lazy import litellm.

        Returns:
            The litellm module.

        Raises:
            ImportError: If litellm is not installed.
        """
        if self._litellm is None:
            try:
                import litellm
                self._litellm = litellm
            except ImportError as e:
                raise ImportError(
                    "litellm is required for LiteLLMProvider. "
                    "Install with: pip install agentforge[llm]"
                ) from e
        return self._litellm

    def _build_params(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build parameters for litellm.acompletion.

        Args:
            messages: Conversation history.
            config: Optional configuration override.
            **kwargs: Additional parameters.

        Returns:
            Dict of parameters for litellm.
        """
        effective_config = config or LLMConfig(model=self.model)

        params: dict[str, Any] = {
            "model": effective_config.model,
            "messages": messages,
            "temperature": effective_config.temperature,
        }

        if effective_config.max_tokens is not None:
            params["max_tokens"] = effective_config.max_tokens

        if effective_config.top_p != 1.0:
            params["top_p"] = effective_config.top_p

        if effective_config.stop:
            params["stop"] = effective_config.stop

        if effective_config.tools:
            params["tools"] = effective_config.tools

        if effective_config.tool_choice:
            params["tool_choice"] = effective_config.tool_choice

        if self.api_key:
            params["api_key"] = self.api_key

        if self.fallbacks:
            params["fallbacks"] = self.fallbacks

        params.update(kwargs)

        return params

    async def complete(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using LiteLLM.

        Args:
            messages: Conversation history as list of dicts.
            config: Optional configuration override.
            **kwargs: Additional parameters.

        Returns:
            LLMResponse with the generated content.
        """
        litellm = self._get_litellm()
        params = self._build_params(messages, config, **kwargs)

        start_time = time.perf_counter()

        try:
            response = await litellm.acompletion(**params)

            latency_ms = (time.perf_counter() - start_time) * 1000

            choice = response.choices[0]
            content = choice.message.content or ""

            # Extract tool calls if present
            tool_calls = None
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                tool_calls = []
                for tc in choice.message.tool_calls:
                    tool_calls.append({
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    })

            usage = LLMUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            )

            return LLMResponse(
                content=content,
                model=response.model,
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
                latency_ms=latency_ms,
            )

        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="litellm",
                details={"model": params.get("model", self.model)},
            ) from e

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using LiteLLM.

        Args:
            messages: Conversation history as list of dicts.
            config: Optional configuration override.
            **kwargs: Additional parameters.

        Yields:
            Chunks of generated text.
        """
        litellm = self._get_litellm()
        params = self._build_params(messages, config, **kwargs)
        params["stream"] = True

        try:
            response = await litellm.acompletion(**params)

            async for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="litellm",
                details={"model": params.get("model", self.model)},
            ) from e

    def supports_tools(self) -> bool:
        """Return True - LiteLLM handles tool calling across providers.

        Returns:
            bool: Always True for LiteLLM.
        """
        return True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using LiteLLM.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        litellm = self._get_litellm()

        try:
            response = await litellm.aembedding(
                model=self.model,
                input=texts,
            )

            return [item["embedding"] for item in response.data]

        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="litellm",
                details={"model": self.model},
            ) from e


__all__ = ["LiteLLMProvider"]
