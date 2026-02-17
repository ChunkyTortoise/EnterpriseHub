"""LLM module for AgentForge.

This module provides LLM provider abstractions and implementations:
- LLMProvider: Abstract base class for LLM providers
- LLMConfig: Configuration model for LLM requests
- LLMResponse: Response model from LLM completions
- LLMUsage: Token usage statistics
- LiteLLMProvider: Unified interface to 100+ LLM providers
- OpenAICompatibleProvider: Zero-dependency OpenAI API client

Example:
    ```python
    from agentforge.llm import get_provider, LLMConfig

    # Using the factory function
    provider = get_provider("openai", model="gpt-4o", api_key="sk-...")
    response = await provider.complete([{"role": "user", "content": "Hello!"}])

    # Or instantiate directly
    from agentforge.llm import OpenAICompatibleProvider
    provider = OpenAICompatibleProvider(model="gpt-4o")
    ```
"""

from typing import Any

from agentforge.llm.base import (
    LLMConfig,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMUsage,
)
from agentforge.llm.litellm import LiteLLMProvider
from agentforge.llm.openai_compat import OpenAICompatibleProvider


def get_provider(name: str = "openai", **kwargs: Any) -> LLMProvider:
    """Factory function to get an LLM provider by name.

    Args:
        name: Provider name ("openai" or "litellm").
        **kwargs: Arguments passed to the provider constructor.

    Returns:
        LLMProvider instance.

    Raises:
        ValueError: If the provider name is unknown.

    Example:
        ```python
        # Get OpenAI provider
        provider = get_provider("openai", model="gpt-4o", api_key="sk-...")

        # Get LiteLLM provider with fallbacks
        provider = get_provider(
            "litellm",
            model="gpt-4o",
            fallbacks=["claude-3-opus"],
            api_key="sk-..."
        )
        ```
    """
    if name == "litellm":
        return LiteLLMProvider(**kwargs)
    elif name == "openai":
        return OpenAICompatibleProvider(**kwargs)
    else:
        raise ValueError(
            f"Unknown provider: {name}. "
            f"Supported providers: 'openai', 'litellm'"
        )


__all__ = [
    # Base classes
    "LLMProvider",
    "LLMConfig",
    "LLMResponse",
    "LLMUsage",
    "LLMError",
    # Implementations
    "LiteLLMProvider",
    "OpenAICompatibleProvider",
    # Factory
    "get_provider",
]
