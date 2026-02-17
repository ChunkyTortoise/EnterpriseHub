"""Zero-dependency OpenAI-compatible client for AgentForge.

This module provides a direct HTTP client for OpenAI-compatible APIs
without requiring any external HTTP libraries. Uses only Python's built-in
urllib with asyncio.to_thread for async support.

This is useful for:
- Minimal dependency installations
- Custom OpenAI-compatible endpoints (vLLM, Ollama, etc.)
- Full control over HTTP behavior
- Environments where httpx/aiohttp are not available
"""

import asyncio
import json
import os
import time
import urllib.error
import urllib.request
from collections.abc import AsyncIterator
from typing import Any

from agentforge.llm.base import (
    LLMConfig,
    LLMError,
    LLMProvider,
    LLMResponse,
    LLMUsage,
)


class OpenAICompatibleProvider(LLMProvider):
    """Zero-dependency OpenAI-compatible LLM provider.

    Directly implements the OpenAI chat completions API using only
    Python's built-in urllib module with asyncio.to_thread for async.

    Supports:
    - OpenAI API
    - Azure OpenAI
    - vLLM
    - Ollama
    - Any OpenAI-compatible endpoint

    Example:
        ```python
        provider = OpenAICompatibleProvider(
            model="gpt-4o",
            api_key="sk-...",
            base_url="https://api.openai.com/v1"
        )
        response = await provider.complete([{"role": "user", "content": "Hello!"}])
        ```
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> None:
        """Initialize the OpenAI-compatible provider.

        Args:
            model: Model identifier (default: "gpt-4o").
            api_key: API key (falls back to OPENAI_API_KEY env var).
            base_url: API base URL (default: "https://api.openai.com/v1").
        """
        self.model = model
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.base_url = base_url or "https://api.openai.com/v1"

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication.

        Returns:
            Dict of HTTP headers.
        """
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _build_body(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        stream: bool = False,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Build the request body for the API.

        Args:
            messages: Conversation history.
            config: Optional configuration override.
            stream: Whether to enable streaming.
            **kwargs: Additional parameters.

        Returns:
            Dict representing the request body.
        """
        effective_config = config or LLMConfig(model=self.model)

        body: dict[str, Any] = {
            "model": effective_config.model,
            "messages": messages,
            "temperature": effective_config.temperature,
            "stream": stream,
        }

        if effective_config.max_tokens is not None:
            body["max_tokens"] = effective_config.max_tokens

        if effective_config.top_p != 1.0:
            body["top_p"] = effective_config.top_p

        if effective_config.stop:
            body["stop"] = effective_config.stop

        if effective_config.tools:
            body["tools"] = effective_config.tools

        if effective_config.tool_choice:
            body["tool_choice"] = effective_config.tool_choice

        body.update(kwargs)

        return body

    def _make_request(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> dict[str, Any]:
        """Make a synchronous HTTP request (called via asyncio.to_thread).

        Args:
            url: Request URL.
            headers: Request headers.
            body: Request body.

        Returns:
            Parsed JSON response.

        Raises:
            LLMError: If the request fails.
        """
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )

        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise LLMError(
                message=f"API request failed: {error_body}",
                provider="openai-compatible",
                status_code=e.code,
                details={"response": error_body},
            ) from e

        except urllib.error.URLError as e:
            raise LLMError(
                message=f"Network error: {e.reason}",
                provider="openai-compatible",
            ) from e

    def _make_stream_request(
        self,
        url: str,
        headers: dict[str, str],
        body: dict[str, Any],
    ) -> list[str]:
        """Make a streaming HTTP request (called via asyncio.to_thread).

        Args:
            url: Request URL.
            headers: Request headers.
            body: Request body.

        Returns:
            List of content chunks.

        Raises:
            LLMError: If the request fails.
        """
        data = json.dumps(body).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers=headers,
            method="POST",
        )

        chunks: list[str] = []

        try:
            with urllib.request.urlopen(request, timeout=120) as response:
                for line in response:
                    line = line.decode("utf-8").strip()
                    if line.startswith("data: "):
                        data_str = line[6:]
                        if data_str == "[DONE]":
                            break
                        try:
                            chunk_data = json.loads(data_str)
                            delta = chunk_data.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                chunks.append(content)
                        except json.JSONDecodeError:
                            continue

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            raise LLMError(
                message=f"API request failed: {error_body}",
                provider="openai-compatible",
                status_code=e.code,
                details={"response": error_body},
            ) from e

        except urllib.error.URLError as e:
            raise LLMError(
                message=f"Network error: {e.reason}",
                provider="openai-compatible",
            ) from e

        return chunks

    async def complete(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """Generate a completion using the OpenAI-compatible API.

        Args:
            messages: Conversation history as list of dicts.
            config: Optional configuration override.
            **kwargs: Additional parameters.

        Returns:
            LLMResponse with the generated content.
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        body = self._build_body(messages, config, stream=False, **kwargs)

        start_time = time.perf_counter()

        try:
            # Run synchronous request in thread pool
            data = await asyncio.to_thread(
                self._make_request,
                url,
                headers,
                body,
            )

            latency_ms = (time.perf_counter() - start_time) * 1000

            choice = data["choices"][0]
            message = choice["message"]

            # Extract tool calls
            tool_calls = None
            if "tool_calls" in message:
                tool_calls = message["tool_calls"]

            usage_data = data.get("usage", {})
            usage = LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            )

            return LLMResponse(
                content=message.get("content") or "",
                model=data.get("model", self.model),
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=choice.get("finish_reason"),
                latency_ms=latency_ms,
            )

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="openai-compatible",
            ) from e

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream a completion using the OpenAI-compatible API.

        Args:
            messages: Conversation history as list of dicts.
            config: Optional configuration override.
            **kwargs: Additional parameters.

        Yields:
            Chunks of generated text.
        """
        url = f"{self.base_url}/chat/completions"
        headers = self._get_headers()
        body = self._build_body(messages, config, stream=True, **kwargs)

        try:
            # Run streaming request in thread pool and yield results
            chunks = await asyncio.to_thread(
                self._make_stream_request,
                url,
                headers,
                body,
            )

            for chunk in chunks:
                yield chunk

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="openai-compatible",
            ) from e

    def supports_tools(self) -> bool:
        """Return True - OpenAI API supports tool calling.

        Returns:
            bool: Always True for OpenAI-compatible providers.
        """
        return True

    async def embed(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings using the OpenAI-compatible API.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        url = f"{self.base_url}/embeddings"
        headers = self._get_headers()
        body = {
            "model": self.model,
            "input": texts,
        }

        try:
            data = await asyncio.to_thread(
                self._make_request,
                url,
                headers,
                body,
            )

            return [item["embedding"] for item in data["data"]]

        except LLMError:
            raise
        except Exception as e:
            raise LLMError(
                message=str(e),
                provider="openai-compatible",
            ) from e


__all__ = ["OpenAICompatibleProvider"]
