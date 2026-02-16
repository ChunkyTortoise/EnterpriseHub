"""LLM-based structured data extraction from HTML/text."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Protocol


class LLMClient(Protocol):
    """Protocol for LLM clients used by the extractor."""

    async def complete(self, prompt: str) -> str: ...


@dataclass
class ExtractionSchema:
    fields: dict[str, str]  # field_name -> description
    required: list[str] = field(default_factory=list)


@dataclass
class ExtractionResult:
    data: dict[str, Any]
    source_url: str
    confidence: float
    raw_response: str
    missing_fields: list[str] = field(default_factory=list)


class LLMExtractor:
    """Extracts structured data from text using an LLM client."""

    def __init__(self, llm_client: LLMClient | None = None):
        self._client = llm_client

    async def extract(
        self,
        text: str,
        schema: ExtractionSchema,
        source_url: str = "",
    ) -> ExtractionResult:
        if not self._client:
            raise RuntimeError("No LLM client configured")

        prompt = self._build_prompt(text, schema)
        raw = await self._client.complete(prompt)
        data = self._parse_response(raw, schema)

        missing = [f for f in schema.required if f not in data or data[f] is None]
        confidence = 1.0 - (len(missing) / max(len(schema.fields), 1))

        return ExtractionResult(
            data=data, source_url=source_url,
            confidence=confidence, raw_response=raw,
            missing_fields=missing,
        )

    def _build_prompt(self, text: str, schema: ExtractionSchema) -> str:
        fields_desc = "\n".join(
            f"- {name}: {desc}" for name, desc in schema.fields.items()
        )
        return (
            f"Extract the following fields from the text below.\n"
            f"Return ONLY valid JSON with these fields:\n{fields_desc}\n\n"
            f"Text:\n{text[:4000]}\n\n"
            f"JSON output:"
        )

    def _parse_response(self, raw: str, schema: ExtractionSchema) -> dict[str, Any]:
        # Try to find JSON in the response
        raw = raw.strip()
        if raw.startswith("```"):
            lines = raw.split("\n")
            raw = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Return empty dict for each field
            return {f: None for f in schema.fields}

    async def extract_batch(
        self,
        texts: list[tuple[str, str]],  # (text, source_url)
        schema: ExtractionSchema,
    ) -> list[ExtractionResult]:
        results = []
        for text, url in texts:
            result = await self.extract(text, schema, url)
            results.append(result)
        return results
