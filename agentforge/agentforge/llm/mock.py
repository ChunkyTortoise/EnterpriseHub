"""Mock LLM provider for offline tests and demos.

Provides deterministic completions without network calls so examples,
tests, and sales demos can run in any environment.
"""

from __future__ import annotations

import asyncio
import json
import re
from collections.abc import AsyncIterator
from typing import Any

from agentforge.llm.base import LLMConfig, LLMProvider, LLMResponse, LLMUsage


class MockLLMProvider(LLMProvider):
    """Deterministic mock provider with optional lightweight tool-call simulation."""

    def __init__(self, model: str = "mock-v1") -> None:
        self.model = model

    async def complete(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        _ = config
        tools = kwargs.get("tools") or []
        last = messages[-1] if messages else {"content": ""}
        content = str(last.get("content", ""))

        # If the prompt looks like arithmetic and a calculate tool exists,
        # emit a synthetic tool call so the Agent can execute it.
        if tools and self._is_math_query(content):
            calc_tool = self._find_tool_name(tools, "calculate")
            if calc_tool:
                expr = self._extract_expression(content)
                tool_calls = [
                    {
                        "id": "mock-tool-1",
                        "type": "function",
                        "function": {
                            "name": calc_tool,
                            "arguments": json.dumps({"expression": expr}),
                        },
                    }
                ]
                return LLMResponse(
                    content="",
                    model=self.model,
                    usage=LLMUsage(prompt_tokens=8, completion_tokens=2, total_tokens=10),
                    tool_calls=tool_calls,
                    finish_reason="tool_calls",
                    latency_ms=2.0,
                )

        # If tool output exists in history, summarize the most recent one.
        tool_messages = [m for m in messages if m.get("role") == "tool"]
        if tool_messages:
            out = str(tool_messages[-1].get("content", "")).strip()
            answer = out if out else "Done."
        else:
            answer = f"[mock] {content}".strip()

        return LLMResponse(
            content=answer,
            model=self.model,
            usage=LLMUsage(prompt_tokens=8, completion_tokens=6, total_tokens=14),
            finish_reason="stop",
            latency_ms=2.0,
        )

    async def stream(
        self,
        messages: list[dict[str, Any]],
        config: LLMConfig | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = await self.complete(messages, config=config, **kwargs)
        for token in result.content.split():
            yield token + " "
            await asyncio.sleep(0)

    def supports_tools(self) -> bool:
        return True

    @staticmethod
    def _find_tool_name(tools: list[dict[str, Any]], candidate: str) -> str | None:
        for tool in tools:
            fn = tool.get("function", {})
            name = fn.get("name")
            if name == candidate:
                return name
        return None

    @staticmethod
    def _is_math_query(text: str) -> bool:
        return bool(re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text))

    @staticmethod
    def _extract_expression(text: str) -> str:
        match = re.search(r"(\d+\s*[\+\-\*\/]\s*\d+)", text)
        if not match:
            return text
        return match.group(1)

