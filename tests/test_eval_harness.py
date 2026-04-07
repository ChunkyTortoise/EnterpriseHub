"""Tests for the LLM-as-judge evaluation harness.

All Claude API calls are mocked -- no real LLM invocations.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from unittest.mock import AsyncMock, MagicMock

import pytest

from evals.judge import (
    AI_DISCLOSURE_PATTERNS,
    EvalResult,
    judge_response,
    run_deterministic_checks,
    run_eval_suite,
)
from evals.rubrics import ALL_RUBRICS, format_rubrics_for_prompt


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

GOOD_RESPONSE = "What's prompting the move? Just helps me understand your timeline."

LONG_RESPONSE = "x" * 500

AI_DISCLOSURE_RESPONSE = "I'm an AI assistant and I can help you sell your house."

SAMPLE_TEST_CASE = {
    "id": "TC-001",
    "input": "I'm thinking about selling my house in Etiwanda",
    "expected_output_properties": {
        "contains_question": True,
        "max_length": 160,
        "no_urls": True,
        "no_ai_disclosure": True,
        "persona_maintained": True,
        "topic_boundary": "real_estate",
    },
    "category": "seller_qualification",
    "difficulty": "easy",
    "bot_type": "seller",
    "description": "Seller Q1 - motivation question",
}


def _mock_judge_client(scores: dict | None = None) -> AsyncMock:
    """Create a mock Anthropic client that returns judge scores."""
    scores = scores or {
        "correctness": 0.9,
        "tone": 0.85,
        "safety": 1.0,
        "compliance": 1.0,
        "reasoning": "Good qualifying question in Jorge's style.",
    }
    content_block = MagicMock()
    content_block.text = json.dumps(scores)
    message = MagicMock()
    message.content = [content_block]
    client = AsyncMock()
    client.messages.create = AsyncMock(return_value=message)
    return client


# ---------------------------------------------------------------------------
# Deterministic check tests
# ---------------------------------------------------------------------------


class TestDeterministicChecks:
    def test_pass_good_response(self):
        """A short, clean response passes all deterministic checks."""
        checks = run_deterministic_checks(GOOD_RESPONSE, SAMPLE_TEST_CASE)
        assert checks["length"] is True
        assert checks["no_urls"] is True
        assert checks["no_ai_disclosure"] is True
        assert checks["no_competitor_mentions"] is True
        assert all(checks.values())

    def test_fail_long_response(self):
        """A response exceeding max_length fails the length check."""
        checks = run_deterministic_checks(LONG_RESPONSE, SAMPLE_TEST_CASE)
        assert checks["length"] is False

    def test_fail_ai_disclosure(self):
        """A response containing AI identity language fails the disclosure check."""
        checks = run_deterministic_checks(AI_DISCLOSURE_RESPONSE, SAMPLE_TEST_CASE)
        assert checks["no_ai_disclosure"] is False

    def test_url_detection(self):
        """URLs in the response trigger the no_urls check failure."""
        response = "Check out https://example.com for more info"
        checks = run_deterministic_checks(response, SAMPLE_TEST_CASE)
        assert checks["no_urls"] is False

    def test_competitor_detection(self):
        """Competitor name mentions trigger the competitor check failure."""
        response = "You should also check Zillow for pricing"
        checks = run_deterministic_checks(response, SAMPLE_TEST_CASE)
        assert checks["no_competitor_mentions"] is False

    def test_disclosure_expected_skips_check(self):
        """When test case expects AI disclosure, the check is skipped (always True)."""
        tc = {
            **SAMPLE_TEST_CASE,
            "expected_output_properties": {
                **SAMPLE_TEST_CASE["expected_output_properties"],
                "no_ai_disclosure": False,
            },
        }
        checks = run_deterministic_checks(AI_DISCLOSURE_RESPONSE, tc)
        assert checks["no_ai_disclosure"] is True


# ---------------------------------------------------------------------------
# Judge response tests
# ---------------------------------------------------------------------------


class TestJudgeResponse:
    @pytest.mark.asyncio
    async def test_parses_scores(self):
        """Judge response parses LLM JSON output into EvalResult scores."""
        client = _mock_judge_client()
        result = await judge_response(
            response=GOOD_RESPONSE,
            test_case=SAMPLE_TEST_CASE,
            client=client,
        )
        assert isinstance(result, EvalResult)
        assert result.test_case_id == "TC-001"
        assert result.scores["correctness"] == 0.9
        assert result.scores["tone"] == 0.85
        assert result.scores["safety"] == 1.0
        assert result.scores["compliance"] == 1.0
        assert result.passed is True
        assert result.reasoning == "Good qualifying question in Jorge's style."
        client.messages.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_handles_invalid_json(self):
        """Judge gracefully handles malformed LLM output."""
        content_block = MagicMock()
        content_block.text = "NOT VALID JSON"
        message = MagicMock()
        message.content = [content_block]
        client = AsyncMock()
        client.messages.create = AsyncMock(return_value=message)

        result = await judge_response(
            response=GOOD_RESPONSE,
            test_case=SAMPLE_TEST_CASE,
            client=client,
        )
        assert result.scores["correctness"] == 0.0
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_fail_on_deterministic_overrides_llm(self):
        """Even with perfect LLM scores, a deterministic failure means overall fail."""
        client = _mock_judge_client({
            "correctness": 1.0,
            "tone": 1.0,
            "safety": 1.0,
            "compliance": 1.0,
            "reasoning": "Perfect response.",
        })
        result = await judge_response(
            response=LONG_RESPONSE,
            test_case=SAMPLE_TEST_CASE,
            client=client,
        )
        assert result.deterministic_checks["length"] is False
        assert result.passed is False


# ---------------------------------------------------------------------------
# Suite runner test
# ---------------------------------------------------------------------------


class TestRunEvalSuite:
    @pytest.mark.asyncio
    async def test_loads_dataset(self, tmp_path):
        """run_eval_suite loads the golden dataset and runs all test cases."""
        # Create a minimal 2-case dataset
        mini_dataset = [
            SAMPLE_TEST_CASE,
            {**SAMPLE_TEST_CASE, "id": "TC-002", "input": "Need to sell fast"},
        ]
        dataset_path = tmp_path / "test_dataset.json"
        dataset_path.write_text(json.dumps(mini_dataset))

        client = _mock_judge_client()

        async def mock_response_fn(tc):
            return GOOD_RESPONSE

        results = await run_eval_suite(
            golden_dataset_path=str(dataset_path),
            fail_threshold=0.5,
            client=client,
            response_fn=mock_response_fn,
        )
        assert len(results) == 2
        assert all(isinstance(r, EvalResult) for r in results)
        assert results[0].test_case_id == "TC-001"
        assert results[1].test_case_id == "TC-002"

    @pytest.mark.asyncio
    async def test_raises_below_threshold(self, tmp_path):
        """run_eval_suite raises ValueError when pass rate is below threshold."""
        mini_dataset = [SAMPLE_TEST_CASE]
        dataset_path = tmp_path / "test_dataset.json"
        dataset_path.write_text(json.dumps(mini_dataset))

        # Return scores that make the test fail
        client = _mock_judge_client({
            "correctness": 0.1,
            "tone": 0.1,
            "safety": 0.1,
            "compliance": 0.1,
            "reasoning": "Bad response.",
        })

        async def mock_response_fn(tc):
            return GOOD_RESPONSE

        with pytest.raises(ValueError, match="pass rate"):
            await run_eval_suite(
                golden_dataset_path=str(dataset_path),
                fail_threshold=1.0,
                client=client,
                response_fn=mock_response_fn,
            )


# ---------------------------------------------------------------------------
# Rubrics tests
# ---------------------------------------------------------------------------


class TestRubrics:
    def test_all_rubrics_present(self):
        assert "correctness" in ALL_RUBRICS
        assert "tone" in ALL_RUBRICS
        assert "safety" in ALL_RUBRICS
        assert "compliance" in ALL_RUBRICS

    def test_weights_sum_to_one(self):
        total = sum(r.weight for r in ALL_RUBRICS.values())
        assert abs(total - 1.0) < 0.001

    def test_format_for_prompt(self):
        text = format_rubrics_for_prompt()
        assert "correctness" in text
        assert "tone" in text
        assert "safety" in text
        assert "compliance" in text
        assert "weight:" in text
