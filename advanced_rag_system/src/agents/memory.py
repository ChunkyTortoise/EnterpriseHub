"""Conversation memory with summarization and context window management."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List


@dataclass
class MemoryMessage:
    role: str
    content: str
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ConversationMemory:
    """Simple conversational memory with rolling summaries."""

    def __init__(self, max_tokens: int = 1200, summary_tokens: int = 300, max_messages: int = 50) -> None:
        self.max_tokens = max_tokens
        self.summary_tokens = summary_tokens
        self.max_messages = max_messages
        self._messages: List[MemoryMessage] = []
        self._summary: str = ""

    def add_message(self, role: str, content: str) -> None:
        if not content:
            return
        self._messages.append(MemoryMessage(role=role, content=content))
        self._trim_messages()

    def get_context(self) -> str:
        parts: List[str] = []
        if self._summary:
            parts.append(f"Summary: {self._summary}")
        for message in self._messages:
            parts.append(f"{message.role}: {message.content}")
        return "\n".join(parts).strip()

    def clear(self) -> None:
        self._messages = []
        self._summary = ""

    def _trim_messages(self) -> None:
        if len(self._messages) > self.max_messages:
            overflow = self._messages[:-self.max_messages]
            self._summary = self._merge_summary(self._summary, overflow)
            self._messages = self._messages[-self.max_messages:]

        while self._estimate_tokens(self.get_context()) > self.max_tokens and self._messages:
            removed = self._messages.pop(0)
            self._summary = self._merge_summary(self._summary, [removed])

        if self._summary and self._estimate_tokens(self._summary) > self.summary_tokens:
            self._summary = self._truncate_summary(self._summary, self.summary_tokens)

    def _estimate_tokens(self, text: str) -> int:
        return len(text.split())

    def _merge_summary(self, existing: str, messages: List[MemoryMessage]) -> str:
        additions = []
        for msg in messages:
            snippet = msg.content.replace("\n", " ").strip()
            if len(snippet) > 160:
                snippet = snippet[:160] + "..."
            additions.append(f"{msg.role}: {snippet}")
        combined = " | ".join(additions)
        if existing:
            return f"{existing} | {combined}"
        return combined

    def _truncate_summary(self, summary: str, max_tokens: int) -> str:
        words = summary.split()
        if len(words) <= max_tokens:
            return summary
        return " ".join(words[:max_tokens]) + " ..."
