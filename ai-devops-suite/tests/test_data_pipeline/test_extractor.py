"""Unit tests for LLMExtractor — structured data extraction from text."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock

import pytest

from devops_suite.data_pipeline.extractor import (
    LLMExtractor,
    ExtractionSchema,
    ExtractionResult,
)


@pytest.fixture
def schema():
    return ExtractionSchema(
        fields={"name": "Full name", "email": "Email address", "company": "Company name"},
        required=["name", "email"],
    )


@pytest.fixture
def mock_llm():
    return AsyncMock()


class TestLLMExtractor:
    @pytest.mark.asyncio
    async def test_extract_parses_json_response(self, schema, mock_llm):
        mock_llm.complete.return_value = json.dumps({"name": "John", "email": "john@test.com", "company": "Acme"})
        extractor = LLMExtractor(llm_client=mock_llm)

        result = await extractor.extract("Some text about John", schema, "http://test.com")

        assert result.data["name"] == "John"
        assert result.data["email"] == "john@test.com"
        assert result.confidence == 1.0
        assert result.missing_fields == []

    @pytest.mark.asyncio
    async def test_extract_reports_missing_required_fields(self, schema, mock_llm):
        mock_llm.complete.return_value = json.dumps({"name": "John", "email": None, "company": None})
        extractor = LLMExtractor(llm_client=mock_llm)

        result = await extractor.extract("text", schema)

        assert "email" in result.missing_fields
        assert result.confidence < 1.0

    @pytest.mark.asyncio
    async def test_extract_handles_code_block_response(self, schema, mock_llm):
        mock_llm.complete.return_value = '```json\n{"name": "Jane", "email": "jane@test.com", "company": "Corp"}\n```'
        extractor = LLMExtractor(llm_client=mock_llm)

        result = await extractor.extract("text", schema)
        assert result.data["name"] == "Jane"

    @pytest.mark.asyncio
    async def test_extract_handles_invalid_json(self, schema, mock_llm):
        mock_llm.complete.return_value = "Not valid JSON at all"
        extractor = LLMExtractor(llm_client=mock_llm)

        result = await extractor.extract("text", schema)
        # Should return None values for all fields
        assert all(v is None for v in result.data.values())

    @pytest.mark.asyncio
    async def test_extract_raises_without_client(self, schema):
        extractor = LLMExtractor(llm_client=None)
        with pytest.raises(RuntimeError, match="No LLM client"):
            await extractor.extract("text", schema)

    @pytest.mark.asyncio
    async def test_extract_batch(self, schema, mock_llm):
        mock_llm.complete.return_value = json.dumps({"name": "A", "email": "a@t.com", "company": "X"})
        extractor = LLMExtractor(llm_client=mock_llm)

        results = await extractor.extract_batch(
            [("text1", "url1"), ("text2", "url2")], schema
        )

        assert len(results) == 2
        assert results[0].source_url == "url1"
        assert results[1].source_url == "url2"


class TestBuildPrompt:
    def test_prompt_contains_field_descriptions(self, schema):
        extractor = LLMExtractor()
        prompt = extractor._build_prompt("Hello world", schema)
        assert "Full name" in prompt
        assert "Email address" in prompt

    def test_prompt_truncates_long_text(self, schema):
        extractor = LLMExtractor()
        long_text = "x" * 10000
        prompt = extractor._build_prompt(long_text, schema)
        # Text should be truncated to 4000 chars
        assert len(prompt) < 10000


class TestParseResponse:
    def test_parses_valid_json(self):
        schema = ExtractionSchema(fields={"a": "desc"})
        extractor = LLMExtractor()
        result = extractor._parse_response('{"a": "value"}', schema)
        assert result["a"] == "value"

    def test_strips_markdown_code_fences(self):
        schema = ExtractionSchema(fields={"a": "desc"})
        extractor = LLMExtractor()
        result = extractor._parse_response('```json\n{"a": "value"}\n```', schema)
        assert result["a"] == "value"

    def test_returns_nulls_for_invalid_json(self):
        schema = ExtractionSchema(fields={"a": "desc", "b": "desc2"})
        extractor = LLMExtractor()
        result = extractor._parse_response("invalid", schema)
        assert result == {"a": None, "b": None}
