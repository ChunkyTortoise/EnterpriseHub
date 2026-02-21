"""Tests for the AgentForge LLM module.

This module contains tests for:
- LLMConfig validation
- LLMResponse model
- LLMUsage model
- MockLLMProvider for testing
- OpenAICompatibleProvider request formatting
- LiteLLMProvider lazy import
"""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from agentforge.llm import (
    LLMConfig,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMUsage,
    OpenAICompatibleProvider,
    get_provider,
)
from agentforge.llm.litellm import LiteLLMProvider

# =============================================================================
# Test Models
# =============================================================================


class TestLLMUsage:
    """Tests for LLMUsage model."""

    def test_default_values(self):
        """Test default values are zero."""
        usage = LLMUsage()
        assert usage.prompt_tokens == 0
        assert usage.completion_tokens == 0
        assert usage.total_tokens == 0

    def test_custom_values(self):
        """Test custom values are set correctly."""
        usage = LLMUsage(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
        )
        assert usage.prompt_tokens == 100
        assert usage.completion_tokens == 50
        assert usage.total_tokens == 150

    def test_from_dict(self):
        """Test creating from dictionary."""
        usage = LLMUsage(
            **{
                "prompt_tokens": 200,
                "completion_tokens": 100,
                "total_tokens": 300,
            }
        )
        assert usage.prompt_tokens == 200


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_model_required(self):
        """Test that model is required."""
        with pytest.raises(ValidationError):
            LLMConfig()

    def test_default_values(self):
        """Test default configuration values."""
        config = LLMConfig(model="gpt-4o")
        assert config.model == "gpt-4o"
        assert config.temperature == 0.7
        assert config.max_tokens is None
        assert config.top_p == 1.0
        assert config.stop is None
        assert config.tools is None
        assert config.tool_choice is None

    def test_custom_values(self):
        """Test custom configuration values."""
        config = LLMConfig(
            model="claude-3-opus",
            temperature=0.5,
            max_tokens=2048,
            top_p=0.9,
            stop=["END"],
            tools=[{"type": "function", "function": {"name": "test"}}],
            tool_choice="auto",
        )
        assert config.model == "claude-3-opus"
        assert config.temperature == 0.5
        assert config.max_tokens == 2048
        assert config.top_p == 0.9
        assert config.stop == ["END"]
        assert len(config.tools) == 1
        assert config.tool_choice == "auto"

    def test_tool_choice_types(self):
        """Test tool_choice accepts string or dict."""
        config1 = LLMConfig(model="gpt-4o", tool_choice="auto")
        assert config1.tool_choice == "auto"

        config2 = LLMConfig(
            model="gpt-4o", tool_choice={"type": "function", "function": {"name": "test"}}
        )
        assert isinstance(config2.tool_choice, dict)


class TestLLMResponse:
    """Tests for LLMResponse model."""

    def test_required_fields(self):
        """Test that content and model are required."""
        response = LLMResponse(content="Hello!", model="gpt-4o")
        assert response.content == "Hello!"
        assert response.model == "gpt-4o"

    def test_default_values(self):
        """Test default values."""
        response = LLMResponse(content="Test", model="gpt-4o")
        assert response.usage.prompt_tokens == 0
        assert response.tool_calls is None
        assert response.finish_reason is None
        assert response.latency_ms == 0.0

    def test_full_response(self):
        """Test response with all fields."""
        response = LLMResponse(
            content="Hello, world!",
            model="gpt-4o",
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            tool_calls=[
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                }
            ],
            finish_reason="stop",
            latency_ms=150.5,
        )
        assert response.content == "Hello, world!"
        assert response.usage.total_tokens == 15
        assert len(response.tool_calls) == 1
        assert response.finish_reason == "stop"
        assert response.latency_ms == 150.5


# =============================================================================
# Test MockLLMProvider
# =============================================================================


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing purposes.

    Returns predefined responses and tracks call history.
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        model: str = "mock-model",
        supports_tools_flag: bool = True,
    ):
        """Initialize mock provider.

        Args:
            responses: List of responses to return in order.
            model: Model name to report.
            supports_tools_flag: Whether to report tool support.
        """
        self.responses = responses or ["Mock response"]
        self.model_name = model
        self._supports_tools = supports_tools_flag
        self.call_count = 0
        self.call_history: list[dict[str, Any]] = []

    async def complete(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Return a mock response."""
        self.call_count += 1
        self.call_history.append(
            {
                "messages": messages,
                "config": config,
                "kwargs": kwargs,
            }
        )

        response_content = self.responses[(self.call_count - 1) % len(self.responses)]

        return LLMResponse(
            content=response_content,
            model=self.model_name,
            usage=LLMUsage(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            finish_reason="stop",
            latency_ms=100.0,
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Yield mock response chunks."""
        self.call_count += 1
        response_content = self.responses[(self.call_count - 1) % len(self.responses)]
        for word in response_content.split():
            yield word + " "

    def supports_tools(self) -> bool:
        """Return configured tool support flag."""
        return self._supports_tools


class TestMockLLMProvider:
    """Tests for MockLLMProvider."""

    @pytest.mark.asyncio
    async def test_complete_returns_response(self):
        """Test complete returns a response."""
        provider = MockLLMProvider(responses=["Hello!"])
        response = await provider.complete([{"role": "user", "content": "Hi"}])

        assert response.content == "Hello!"
        assert response.model == "mock-model"
        assert provider.call_count == 1

    @pytest.mark.asyncio
    async def test_complete_tracks_history(self):
        """Test complete tracks call history."""
        provider = MockLLMProvider()
        messages = [{"role": "user", "content": "Test"}]
        config = LLMConfig(model="test-model", temperature=0.5)

        await provider.complete(messages, config=config, extra="value")

        assert len(provider.call_history) == 1
        assert provider.call_history[0]["messages"] == messages
        assert provider.call_history[0]["config"].model == "test-model"
        assert provider.call_history[0]["kwargs"]["extra"] == "value"

    @pytest.mark.asyncio
    async def test_complete_cycles_responses(self):
        """Test complete cycles through responses."""
        provider = MockLLMProvider(responses=["First", "Second", "Third"])

        r1 = await provider.complete([{"role": "user", "content": "Hi"}])
        r2 = await provider.complete([{"role": "user", "content": "Hi"}])
        r3 = await provider.complete([{"role": "user", "content": "Hi"}])
        r4 = await provider.complete([{"role": "user", "content": "Hi"}])

        assert r1.content == "First"
        assert r2.content == "Second"
        assert r3.content == "Third"
        assert r4.content == "First"  # Cycles back

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        """Test stream yields response chunks."""
        provider = MockLLMProvider(responses=["Hello world test"])
        chunks = []

        async for chunk in provider.stream([{"role": "user", "content": "Hi"}]):
            chunks.append(chunk)

        assert len(chunks) == 3
        assert "".join(chunks).strip() == "Hello world test"

    def test_supports_tools(self):
        """Test supports_tools returns configured flag."""
        provider_with_tools = MockLLMProvider(supports_tools_flag=True)
        provider_without_tools = MockLLMProvider(supports_tools_flag=False)

        assert provider_with_tools.supports_tools() is True
        assert provider_without_tools.supports_tools() is False


# =============================================================================
# Test OpenAICompatibleProvider
# =============================================================================


class TestOpenAICompatibleProvider:
    """Tests for OpenAICompatibleProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAICompatibleProvider(
            model="gpt-4o",
            api_key="test-key",
            base_url="https://api.example.com/v1",
        )

        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"
        assert provider.base_url == "https://api.example.com/v1"

    def test_initialization_defaults(self):
        """Test provider initialization with defaults."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAICompatibleProvider(model="gpt-4o")

            assert provider.model == "gpt-4o"
            assert provider.api_key == "env-key"
            assert provider.base_url == "https://api.openai.com/v1"

    def test_supports_tools(self):
        """Test supports_tools returns True."""
        provider = OpenAICompatibleProvider(model="gpt-4o")
        assert provider.supports_tools() is True

    def test_get_headers(self):
        """Test header generation."""
        provider = OpenAICompatibleProvider(model="gpt-4o", api_key="test-key")
        headers = provider._get_headers()

        assert headers["Content-Type"] == "application/json"
        assert headers["Accept"] == "application/json"
        assert headers["Authorization"] == "Bearer test-key"

    def test_build_body(self):
        """Test request body building."""
        provider = OpenAICompatibleProvider(model="gpt-4o")
        messages = [{"role": "user", "content": "Hello"}]

        body = provider._build_body(messages)

        assert body["model"] == "gpt-4o"
        assert body["messages"] == messages
        assert body["temperature"] == 0.7
        assert body["stream"] is False

    def test_build_body_with_config(self):
        """Test request body building with config override."""
        provider = OpenAICompatibleProvider(model="gpt-4o")
        messages = [{"role": "user", "content": "Hello"}]
        config = LLMConfig(
            model="gpt-4-turbo",
            temperature=0.5,
            max_tokens=100,
            stop=["END"],
            tools=[{"type": "function", "function": {"name": "test"}}],
            tool_choice="auto",
        )

        body = provider._build_body(messages, config=config)

        assert body["model"] == "gpt-4-turbo"
        assert body["temperature"] == 0.5
        assert body["max_tokens"] == 100
        assert body["stop"] == ["END"]
        assert body["tools"] is not None
        assert body["tool_choice"] == "auto"

    @pytest.mark.asyncio
    async def test_complete_request_format(self):
        """Test complete method formats request correctly."""
        provider = OpenAICompatibleProvider(
            model="gpt-4o",
            api_key="test-key",
            base_url="https://api.example.com/v1",
        )

        # Mock the _make_request method
        mock_response = {
            "choices": [
                {
                    "message": {"content": "Hello!"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
            "model": "gpt-4o",
        }

        with patch.object(
            provider,
            "_make_request",
            return_value=mock_response,
        ):
            response = await provider.complete(
                [{"role": "user", "content": "Hi"}],
                config=LLMConfig(model="gpt-4o", temperature=0.5),
            )

            assert response.content == "Hello!"
            assert response.model == "gpt-4o"
            assert response.usage.total_tokens == 15
            assert response.finish_reason == "stop"

    @pytest.mark.asyncio
    async def test_complete_with_tool_calls(self):
        """Test complete method handles tool calls."""
        provider = OpenAICompatibleProvider(model="gpt-4o")

        mock_response = {
            "choices": [
                {
                    "message": {
                        "content": None,  # Content can be None when tool_calls present
                        "tool_calls": [
                            {
                                "id": "call_123",
                                "type": "function",
                                "function": {
                                    "name": "get_weather",
                                    "arguments": '{"location": "SF"}',
                                },
                            }
                        ],
                    },
                    "finish_reason": "tool_calls",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            "model": "gpt-4o",
        }

        with patch.object(provider, "_make_request", return_value=mock_response):
            response = await provider.complete([{"role": "user", "content": "Weather?"}])

            # Content should be empty string when None
            assert response.content == ""
            assert response.tool_calls is not None
            assert len(response.tool_calls) == 1
            assert response.tool_calls[0]["function"]["name"] == "get_weather"
            assert response.finish_reason == "tool_calls"

    @pytest.mark.asyncio
    async def test_stream_yields_chunks(self):
        """Test stream method yields chunks."""
        provider = OpenAICompatibleProvider(model="gpt-4o")

        mock_chunks = ["Hello", " world", "!"]

        with patch.object(
            provider,
            "_make_stream_request",
            return_value=mock_chunks,
        ):
            chunks = []
            async for chunk in provider.stream([{"role": "user", "content": "Hi"}]):
                chunks.append(chunk)

            assert chunks == ["Hello", " world", "!"]


# =============================================================================
# Test LiteLLMProvider
# =============================================================================


class TestLiteLLMProvider:
    """Tests for LiteLLMProvider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = LiteLLMProvider(
            model="gpt-4o",
            fallbacks=["claude-3-opus"],
            api_key="test-key",
        )

        assert provider.model == "gpt-4o"
        assert provider.fallbacks == ["claude-3-opus"]
        assert provider.api_key == "test-key"
        assert provider._litellm is None  # Lazy import

    def test_lazy_import_success(self):
        """Test lazy import succeeds when litellm is available."""
        provider = LiteLLMProvider(model="gpt-4o")

        mock_litellm = MagicMock()
        with patch.dict("sys.modules", {"litellm": mock_litellm}):
            # Force the lazy import
            result = provider._get_litellm()
            assert result is mock_litellm

    def test_lazy_import_failure(self):
        """Test lazy import raises ImportError when litellm is not available."""
        provider = LiteLLMProvider(model="gpt-4o")

        with (
            patch.dict("sys.modules", {}, clear=True),
            patch("builtins.__import__", side_effect=ImportError("No module")),
            pytest.raises(ImportError) as exc_info,
        ):
            provider._get_litellm()

        assert "litellm is required" in str(exc_info.value)

    def test_supports_tools(self):
        """Test supports_tools returns True."""
        provider = LiteLLMProvider(model="gpt-4o")
        assert provider.supports_tools() is True

    def test_build_params(self):
        """Test parameter building."""
        provider = LiteLLMProvider(
            model="gpt-4o",
            fallbacks=["claude-3-opus"],
            api_key="test-key",
        )

        messages = [{"role": "user", "content": "Hello"}]
        params = provider._build_params(messages)

        assert params["model"] == "gpt-4o"
        assert params["messages"] == messages
        assert params["temperature"] == 0.7
        assert params["api_key"] == "test-key"
        assert params["fallbacks"] == ["claude-3-opus"]

    def test_build_params_with_config(self):
        """Test parameter building with config override."""
        provider = LiteLLMProvider(model="gpt-4o")

        config = LLMConfig(
            model="gpt-4-turbo",
            temperature=0.5,
            max_tokens=100,
            tools=[{"type": "function", "function": {"name": "test"}}],
            tool_choice="auto",
        )

        params = provider._build_params([{"role": "user", "content": "Hi"}], config=config)

        assert params["model"] == "gpt-4-turbo"
        assert params["temperature"] == 0.5
        assert params["max_tokens"] == 100
        assert params["tools"] is not None
        assert params["tool_choice"] == "auto"


# =============================================================================
# Test Factory Function
# =============================================================================


class TestGetProvider:
    """Tests for get_provider factory function."""

    def test_get_openai_provider(self):
        """Test getting OpenAI provider."""
        provider = get_provider("openai", model="gpt-4o", api_key="test-key")

        assert isinstance(provider, OpenAICompatibleProvider)
        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"

    def test_get_litellm_provider(self):
        """Test getting LiteLLM provider."""
        provider = get_provider("litellm", model="gpt-4o", api_key="test-key")

        assert isinstance(provider, LiteLLMProvider)
        assert provider.model == "gpt-4o"
        assert provider.api_key == "test-key"

    def test_get_unknown_provider(self):
        """Test getting unknown provider raises error."""
        with pytest.raises(ValueError) as exc_info:
            get_provider("unknown")

        assert "Unknown provider" in str(exc_info.value)

    def test_default_provider(self):
        """Test default provider is OpenAI."""
        provider = get_provider()
        assert isinstance(provider, OpenAICompatibleProvider)


# =============================================================================
# Test LLMError
# =============================================================================


class TestLLMError:
    """Tests for LLMError exception."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = LLMError("Something went wrong")

        assert str(error) == "Something went wrong"
        assert error.provider is None
        assert error.status_code is None
        assert error.details == {}

    def test_full_error(self):
        """Test error with all fields."""
        error = LLMError(
            message="API error",
            provider="openai",
            status_code=429,
            details={"reason": "rate_limit"},
        )

        assert str(error) == "API error"
        assert error.provider == "openai"
        assert error.status_code == 429
        assert error.details["reason"] == "rate_limit"


# =============================================================================
# Integration Tests
# =============================================================================


class TestProviderIntegration:
    """Integration tests for provider functionality."""

    @pytest.mark.asyncio
    async def test_provider_interface_contract(self):
        """Test that all providers implement the interface correctly."""
        providers = [
            MockLLMProvider(responses=["Test"]),
            OpenAICompatibleProvider(model="gpt-4o"),
            LiteLLMProvider(model="gpt-4o"),
        ]

        for provider in providers:
            # Check interface methods exist
            assert hasattr(provider, "complete")
            assert hasattr(provider, "stream")
            assert hasattr(provider, "supports_tools")
            assert hasattr(provider, "supports_streaming")

            # Check return types
            assert callable(provider.supports_tools)
            assert callable(provider.supports_streaming)

    @pytest.mark.asyncio
    async def test_config_override_in_request(self):
        """Test that config can be overridden per-request."""
        provider = MockLLMProvider(responses=["Test"])

        config1 = LLMConfig(model="model-1", temperature=0.1)
        config2 = LLMConfig(model="model-2", temperature=0.9)

        await provider.complete([{"role": "user", "content": "Hi"}], config=config1)
        await provider.complete([{"role": "user", "content": "Hi"}], config=config2)

        assert provider.call_history[0]["config"].model == "model-1"
        assert provider.call_history[1]["config"].model == "model-2"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
