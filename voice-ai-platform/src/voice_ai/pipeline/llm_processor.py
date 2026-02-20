"""LLM processor — Claude/GPT intent analysis and response generation."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ConversationTurn:
    """A single conversation turn."""

    role: str  # "user" | "assistant"
    content: str
    timestamp_ms: float = 0.0


@dataclass
class LLMProcessor:
    """Claude-based LLM processor for voice AI conversations.

    Handles persona context injection, conversation history management,
    and streaming token output for real-time TTS feeding.
    """

    api_key: str
    model: str = "claude-sonnet-4-5-20250929"
    max_history_turns: int = 20
    max_tokens: int = 256
    _history: list[ConversationTurn] = field(default_factory=list, repr=False)
    _system_prompt: str = ""

    def set_system_prompt(self, prompt: str) -> None:
        """Set the system prompt (persona + context)."""
        self._system_prompt = prompt

    def add_turn(self, role: str, content: str, timestamp_ms: float = 0.0) -> None:
        """Add a conversation turn to history."""
        self._history.append(ConversationTurn(role=role, content=content, timestamp_ms=timestamp_ms))
        # Trim to max history
        if len(self._history) > self.max_history_turns:
            self._history = self._history[-self.max_history_turns :]

    def get_history(self) -> list[ConversationTurn]:
        """Return current conversation history."""
        return list(self._history)

    def clear_history(self) -> None:
        """Clear conversation history (e.g., on bot handoff)."""
        self._history.clear()

    async def generate_response(self, user_text: str) -> str:
        """Generate a full response (non-streaming) for the given user text."""
        import httpx

        self.add_turn("user", user_text)

        messages = [{"role": t.role, "content": t.content} for t in self._history]

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": self.max_tokens,
                    "system": self._system_prompt,
                    "messages": messages,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()

        assistant_text = data["content"][0]["text"]
        self.add_turn("assistant", assistant_text)
        return assistant_text

    async def generate_response_stream(self, user_text: str) -> AsyncIterator[str]:
        """Generate a streaming response, yielding text tokens for real-time TTS."""
        import httpx

        self.add_turn("user", user_text)

        messages = [{"role": t.role, "content": t.content} for t in self._history]
        full_response = ""

        async with httpx.AsyncClient() as client, client.stream(
            "POST",
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": self.api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": self.model,
                "max_tokens": self.max_tokens,
                "stream": True,
                "system": self._system_prompt,
                "messages": messages,
            },
            timeout=30.0,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    import json

                    event = json.loads(line[6:])
                    if event.get("type") == "content_block_delta":
                        text = event["delta"].get("text", "")
                        if text:
                            full_response += text
                            yield text

        self.add_turn("assistant", full_response)
