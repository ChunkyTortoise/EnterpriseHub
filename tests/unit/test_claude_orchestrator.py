"""Unit tests for ClaudeOrchestrator parsing and response structuring methods.

Tests the pure parsing functions that extract structured data from Claude responses:
- JSON extraction (markdown code blocks, balanced brackets)
- Confidence score parsing (JSON, percentage, qualitative)
- Recommended action extraction
- Script variant parsing
- Risk factor and opportunity extraction
- Conversation message validation
- Prompt building and system prompt mapping

These are the highest test-to-value ratio functions in the orchestrator since they
handle all response parsing without external dependencies.
"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import pytest

pytestmark = pytest.mark.unit


# ---------------------------------------------------------------------------
# Helpers — create a bare ClaudeOrchestrator without running __init__
# ---------------------------------------------------------------------------

def _bare_orchestrator():
    """Create a ClaudeOrchestrator instance without triggering __init__.

    The real __init__ imports many heavy services (LLM, memory, GHL, etc.).
    Parsing helpers only use ``self`` to call sibling methods, so a bare
    instance produced via ``object.__new__`` is sufficient.
    """
    from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator

    return object.__new__(ClaudeOrchestrator)


@pytest.fixture
def orch():
    """Fixture providing a lightweight ClaudeOrchestrator for parsing tests."""
    return _bare_orchestrator()


# ============================================================================
# ClaudeTaskType Enum
# ============================================================================


class TestClaudeTaskType:
    """Tests for the ClaudeTaskType enumeration."""

    def test_all_task_types_exist(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        expected = {
            "CHAT_QUERY",
            "LEAD_ANALYSIS",
            "REPORT_SYNTHESIS",
            "SCRIPT_GENERATION",
            "INTERVENTION_STRATEGY",
            "BEHAVIORAL_INSIGHT",
            "OMNIPOTENT_ASSISTANT",
            "PERSONA_OPTIMIZATION",
            "EXECUTIVE_BRIEFING",
            "REVENUE_PROJECTION",
            "RESEARCH_QUERY",
        }
        actual = {member.name for member in ClaudeTaskType}
        assert actual == expected

    def test_task_type_values_are_strings(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        for member in ClaudeTaskType:
            assert isinstance(member.value, str)


# ============================================================================
# ClaudeRequest / ClaudeResponse dataclasses
# ============================================================================


class TestClaudeRequest:
    """Tests for the ClaudeRequest dataclass."""

    def test_minimal_creation(self):
        from ghl_real_estate_ai.services.claude_orchestrator import (
            ClaudeRequest,
            ClaudeTaskType,
        )

        req = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY,
            context={"lead_id": "L1"},
            prompt="What is the market trend?",
        )
        assert req.task_type == ClaudeTaskType.CHAT_QUERY
        assert req.prompt == "What is the market trend?"
        assert req.temperature == 0.7
        assert req.max_tokens == 4000
        assert req.streaming is False
        assert req.tenant_id is None

    def test_full_creation(self):
        from ghl_real_estate_ai.services.claude_orchestrator import (
            ClaudeRequest,
            ClaudeTaskType,
        )

        req = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "L2"},
            prompt="Analyze this lead",
            tenant_id="tenant-1",
            model="claude-opus-4-6",
            max_tokens=8000,
            temperature=0.3,
            system_prompt="You are an analyst.",
            streaming=True,
            use_tools=True,
        )
        assert req.tenant_id == "tenant-1"
        assert req.model == "claude-opus-4-6"
        assert req.max_tokens == 8000
        assert req.streaming is True
        assert req.use_tools is True


class TestClaudeResponse:
    """Tests for the ClaudeResponse dataclass."""

    def test_defaults(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        resp = ClaudeResponse(content="Hello")
        assert resp.content == "Hello"
        assert resp.sources == []
        assert resp.recommended_actions == []
        assert resp.metadata == {}
        assert resp.confidence is None
        assert resp.reasoning is None

    def test_post_init_fills_none_lists(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        resp = ClaudeResponse(content="test", sources=None, recommended_actions=None, metadata=None)
        assert resp.sources == []
        assert resp.recommended_actions == []
        assert resp.metadata == {}

    def test_explicit_values_preserved(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeResponse

        resp = ClaudeResponse(
            content="analysis",
            confidence=0.85,
            sources=["web", "mls"],
            metadata={"region": "RC"},
            response_time_ms=123,
            input_tokens=500,
            output_tokens=300,
            model="claude-opus-4-6",
            provider="anthropic",
        )
        assert resp.confidence == 0.85
        assert resp.sources == ["web", "mls"]
        assert resp.response_time_ms == 123
        assert resp.input_tokens == 500


# ============================================================================
# _extract_json_block
# ============================================================================


class TestExtractJsonBlock:
    """Tests for _extract_json_block — multi-strategy JSON extraction."""

    def test_extract_from_markdown_json_block(self, orch):
        content = 'Here is the result:\n```json\n{"score": 85}\n```\nDone.'
        result = orch._extract_json_block(content)
        assert result == {"score": 85}

    def test_extract_from_generic_code_block(self, orch):
        content = 'Data:\n```\n{"key": "value"}\n```'
        result = orch._extract_json_block(content)
        assert result == {"key": "value"}

    def test_extract_plain_json_object(self, orch):
        content = 'The analysis shows {"confidence": 0.92, "status": "ok"} for this lead.'
        result = orch._extract_json_block(content)
        assert result is not None
        assert result["confidence"] == 0.92

    def test_returns_none_for_no_json(self, orch):
        content = "This is just plain text with no JSON at all."
        result = orch._extract_json_block(content)
        assert result is None

    def test_returns_none_for_malformed_json(self, orch):
        content = '```json\n{"broken: true}\n```'
        result = orch._extract_json_block(content)
        assert result is None

    def test_nested_json_in_code_block(self, orch):
        content = '```json\n{"lead": {"name": "Alice", "score": 90}}\n```'
        result = orch._extract_json_block(content)
        assert result["lead"]["name"] == "Alice"

    def test_empty_string(self, orch):
        assert orch._extract_json_block("") is None

    def test_non_json_code_block_falls_through(self, orch):
        content = "```\nprint('hello')\n```\n{\"fallback\": true}"
        result = orch._extract_json_block(content)
        assert result is not None
        assert result["fallback"] is True


# ============================================================================
# _extract_balanced_json
# ============================================================================


class TestExtractBalancedJson:
    """Tests for _extract_balanced_json — bracket matching."""

    def test_simple_object(self, orch):
        content = '{"a": 1}'
        result = orch._extract_balanced_json(content, 0)
        assert result == '{"a": 1}'

    def test_nested_braces(self, orch):
        content = '{"outer": {"inner": 42}}'
        result = orch._extract_balanced_json(content, 0)
        parsed = json.loads(result)
        assert parsed["outer"]["inner"] == 42

    def test_string_with_braces(self, orch):
        content = '{"msg": "hello {world}"}'
        result = orch._extract_balanced_json(content, 0)
        parsed = json.loads(result)
        assert parsed["msg"] == "hello {world}"

    def test_escaped_quotes_in_string(self, orch):
        content = '{"msg": "say \\"hi\\"", "x": 1}'
        result = orch._extract_balanced_json(content, 0)
        assert result is not None
        parsed = json.loads(result)
        assert parsed["x"] == 1

    def test_offset_start(self, orch):
        content = 'prefix text {"val": 99}'
        start_idx = content.index("{")
        result = orch._extract_balanced_json(content, start_idx)
        parsed = json.loads(result)
        assert parsed["val"] == 99

    def test_returns_none_for_unbalanced(self, orch):
        content = '{"open": true'
        result = orch._extract_balanced_json(content, 0)
        assert result is None

    def test_empty_object(self, orch):
        content = "{}"
        result = orch._extract_balanced_json(content, 0)
        assert result == "{}"


# ============================================================================
# _extract_list_items
# ============================================================================


class TestExtractListItems:
    """Tests for _extract_list_items — markdown list parsing."""

    def test_numbered_list(self, orch):
        content = "Recommended Actions:\n1. Call the lead\n2. Send follow-up email\n3. Schedule showing\n"
        items = orch._extract_list_items(content, "Recommended Actions")
        assert len(items) >= 2
        assert any("Call" in item for item in items)

    def test_bullet_list(self, orch):
        content = "Next Steps:\n- Review CMA\n- Contact seller\n- Update GHL\n"
        items = orch._extract_list_items(content, "Next Steps")
        assert len(items) >= 2

    def test_case_insensitive_header(self, orch):
        content = "risk factors:\n1. Market downturn\n2. Low inventory\n"
        items = orch._extract_list_items(content, "Risk Factors")
        assert len(items) >= 1

    def test_no_matching_section(self, orch):
        content = "Some unrelated text\n1. Item A\n"
        items = orch._extract_list_items(content, "Nonexistent Section")
        assert items == []

    def test_empty_content(self, orch):
        items = orch._extract_list_items("", "Actions")
        assert items == []

    def test_section_stops_at_next_header(self, orch):
        content = (
            "Actions:\n1. First action\n2. Second action\n\n"
            "## Other Section\n1. Unrelated item\n"
        )
        items = orch._extract_list_items(content, "Actions")
        assert all("Unrelated" not in item for item in items)


# ============================================================================
# _parse_confidence_score
# ============================================================================


class TestParseConfidenceScore:
    """Tests for _parse_confidence_score — multi-strategy confidence extraction."""

    def test_from_json_decimal(self, orch):
        result = orch._parse_confidence_score("", {"confidence": 0.85})
        assert result == 0.85

    def test_from_json_percentage(self, orch):
        result = orch._parse_confidence_score("", {"confidence": 85})
        assert result == 0.85

    def test_from_json_confidence_score_key(self, orch):
        result = orch._parse_confidence_score("", {"confidence_score": 0.72})
        assert result == 0.72

    def test_from_text_percentage(self, orch):
        result = orch._parse_confidence_score("The confidence: 90% for this lead.", None)
        assert result == pytest.approx(0.9, abs=0.01)

    def test_from_text_decimal(self, orch):
        result = orch._parse_confidence_score("confidence score: 0.78", None)
        assert result == pytest.approx(0.78, abs=0.01)

    def test_qualitative_high(self, orch):
        result = orch._parse_confidence_score("I have high confidence in this analysis.", None)
        assert result is not None
        assert result >= 0.8

    def test_qualitative_very_high(self, orch):
        result = orch._parse_confidence_score("very high confidence", None)
        assert result is not None
        assert result >= 0.85

    def test_qualitative_moderate(self, orch):
        result = orch._parse_confidence_score("moderate confidence in this result", None)
        assert result is not None
        assert 0.6 <= result <= 0.8

    def test_qualitative_low(self, orch):
        result = orch._parse_confidence_score("low confidence", None)
        assert result is not None
        assert result <= 0.5

    def test_no_confidence_returns_none(self, orch):
        result = orch._parse_confidence_score("No relevant text here.", None)
        assert result is None

    def test_clamps_above_one(self, orch):
        result = orch._parse_confidence_score("", {"confidence": 150})
        assert result == 1.0

    def test_clamps_below_zero(self, orch):
        result = orch._parse_confidence_score("", {"confidence": -5})
        assert result == 0.0

    def test_json_takes_priority_over_text(self, orch):
        result = orch._parse_confidence_score(
            "low confidence", {"confidence": 0.95}
        )
        assert result == 0.95

    def test_generic_confidence_word_returns_default(self, orch):
        result = orch._parse_confidence_score("Based on my confidence analysis...", None)
        assert result is not None
        assert result == 0.7


# ============================================================================
# _structure_action
# ============================================================================


class TestStructureAction:
    """Tests for _structure_action — priority and timing detection."""

    def test_default_priority_and_timing(self, orch):
        result = orch._structure_action("Send a follow-up email this week")
        assert result["action"] == "Send a follow-up email this week"
        assert result["priority"] == "medium"
        assert result["timing"] == "moderate"

    def test_high_priority_detected(self, orch):
        result = orch._structure_action("URGENT: Call the lead immediately")
        assert result["priority"] == "high"
        assert result["timing"] == "immediate"

    def test_low_priority_detected(self, orch):
        result = orch._structure_action("Consider updating the CRM later")
        assert result["priority"] == "low"

    def test_timing_tomorrow(self, orch):
        result = orch._structure_action("Send the report tomorrow")
        assert result["timing"] == "urgent"

    def test_timing_next_week(self, orch):
        result = orch._structure_action("Schedule a review next week")
        assert result["timing"] == "low"


# ============================================================================
# _parse_recommended_actions
# ============================================================================


class TestParseRecommendedActions:
    """Tests for _parse_recommended_actions."""

    def test_from_json_list_of_strings(self, orch):
        json_data = {"recommended_actions": ["Call lead", "Send CMA"]}
        actions = orch._parse_recommended_actions("", json_data)
        assert len(actions) == 2
        assert actions[0]["action"] == "Call lead"

    def test_from_json_list_of_dicts(self, orch):
        json_data = {
            "recommended_actions": [
                {"action": "Call lead", "priority": "high"},
                {"action": "Update CRM", "priority": "low"},
            ]
        }
        actions = orch._parse_recommended_actions("", json_data)
        assert len(actions) == 2
        assert actions[0]["priority"] == "high"

    def test_from_json_actions_key(self, orch):
        json_data = {"actions": ["Step 1", "Step 2"]}
        actions = orch._parse_recommended_actions("", json_data)
        assert len(actions) == 2

    def test_from_text_section(self, orch):
        content = "Analysis complete.\n\nRecommended Actions:\n1. Call the lead now\n2. Send pricing info\n"
        actions = orch._parse_recommended_actions(content, None)
        assert len(actions) >= 1

    def test_empty_returns_empty_list(self, orch):
        actions = orch._parse_recommended_actions("No actions here.", None)
        assert actions == []


# ============================================================================
# _structure_risk
# ============================================================================


class TestStructureRisk:
    """Tests for _structure_risk — severity classification."""

    def test_default_severity(self, orch):
        result = orch._structure_risk("Lead may not respond in time")
        assert result["severity"] == "medium"
        assert result["factor"] == "Lead may not respond in time"

    def test_high_severity(self, orch):
        result = orch._structure_risk("Critical: financing may fall through")
        assert result["severity"] == "high"

    def test_low_severity(self, orch):
        result = orch._structure_risk("Minor delay in document processing")
        assert result["severity"] == "low"

    def test_mitigation_extracted(self, orch):
        result = orch._structure_risk("Lead may stall. Mitigation: Schedule a follow-up call")
        assert result["mitigation"] == "Schedule a follow-up call"

    def test_no_mitigation(self, orch):
        result = orch._structure_risk("Market conditions are volatile")
        assert result["mitigation"] == ""


# ============================================================================
# _parse_risk_factors
# ============================================================================


class TestParseRiskFactors:
    """Tests for _parse_risk_factors."""

    def test_from_json_list_of_strings(self, orch):
        json_data = {"risk_factors": ["Market downturn", "Lead cold"]}
        risks = orch._parse_risk_factors("", json_data)
        assert len(risks) == 2
        assert risks[0]["factor"] == "Market downturn"

    def test_from_json_list_of_dicts(self, orch):
        json_data = {"risk_factors": [{"factor": "Financing risk", "severity": "high"}]}
        risks = orch._parse_risk_factors("", json_data)
        assert len(risks) == 1
        assert risks[0]["severity"] == "high"

    def test_from_json_risks_key(self, orch):
        json_data = {"risks": ["Price too high"]}
        risks = orch._parse_risk_factors("", json_data)
        assert len(risks) == 1

    def test_from_text_section(self, orch):
        content = "Risk Factors:\n- Market correction possible\n- Interest rates rising\n"
        risks = orch._parse_risk_factors(content, None)
        assert len(risks) >= 1

    def test_empty_returns_empty_list(self, orch):
        risks = orch._parse_risk_factors("No risks identified.", None)
        assert risks == []


# ============================================================================
# _structure_opportunity
# ============================================================================


class TestStructureOpportunity:
    """Tests for _structure_opportunity — value extraction."""

    def test_dollar_amount_extracted(self, orch):
        result = orch._structure_opportunity("Upsell potential worth $15,000")
        assert result["potential_value"] == "$15,000"

    def test_percentage_extracted(self, orch):
        result = orch._structure_opportunity("Could increase conversion by 25%")
        assert "25%" in result["potential_value"]

    def test_qualitative_high(self, orch):
        result = orch._structure_opportunity("Significant growth area in luxury segment")
        assert result["potential_value"] == "high"

    def test_qualitative_low(self, orch):
        result = orch._structure_opportunity("Minimal upside from cold leads")
        assert result["potential_value"] == "low"

    def test_action_extracted(self, orch):
        result = orch._structure_opportunity("Market expansion. Action: Launch targeted campaign")
        assert result["action_required"] == "Launch targeted campaign"

    def test_no_action(self, orch):
        result = orch._structure_opportunity("General market opportunity")
        assert result["action_required"] == ""


# ============================================================================
# _parse_opportunities
# ============================================================================


class TestParseOpportunities:
    """Tests for _parse_opportunities."""

    def test_from_json_list_of_strings(self, orch):
        json_data = {"opportunities": ["Cross-sell buyer services", "Referral program"]}
        opps = orch._parse_opportunities("", json_data)
        assert len(opps) == 2

    def test_from_json_list_of_dicts(self, orch):
        json_data = {"opportunities": [{"opportunity": "Luxury market", "potential_value": "high"}]}
        opps = orch._parse_opportunities("", json_data)
        assert len(opps) == 1
        assert opps[0]["potential_value"] == "high"

    def test_from_text_section(self, orch):
        content = "Opportunities:\n1. Expand into Upland market\n2. Launch seller services\n"
        opps = orch._parse_opportunities(content, None)
        assert len(opps) >= 1

    def test_empty_returns_empty_list(self, orch):
        opps = orch._parse_opportunities("Nothing to see here.", None)
        assert opps == []


# ============================================================================
# _parse_script_variants
# ============================================================================


class TestParseScriptVariants:
    """Tests for _parse_script_variants — A/B test script extraction."""

    def test_from_json_variants_list(self, orch):
        json_data = {
            "variants": [
                {"variant_name": "A", "script_text": "Hi there!"},
                {"variant_name": "B", "script_text": "Hello!"},
            ]
        }
        variants = orch._parse_script_variants("", json_data)
        assert len(variants) == 2
        assert variants[0]["variant_name"] == "A"

    def test_from_json_variants_dict(self, orch):
        json_data = {
            "variants": {
                "Control": {"script_text": "Standard greeting"},
                "Treatment": {"script_text": "Personalized greeting"},
            }
        }
        variants = orch._parse_script_variants("", json_data)
        assert len(variants) == 2

    def test_from_json_scripts_key_delegates(self, orch):
        json_data = {
            "scripts": [
                {"variant_name": "X", "script_text": "test"},
            ]
        }
        variants = orch._parse_script_variants("", json_data)
        assert len(variants) == 1

    def test_empty_returns_empty_list(self, orch):
        variants = orch._parse_script_variants("No scripts here.", None)
        assert variants == []


# ============================================================================
# _parse_response (integration of all parsers)
# ============================================================================


class TestParseResponse:
    """Tests for _parse_response — full response parsing orchestration."""

    def test_basic_response_with_json(self, orch):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        content = '```json\n{"confidence": 0.9, "recommended_actions": ["Call lead"]}\n```\nGreat lead.'
        response = orch._parse_response(content, ClaudeTaskType.CHAT_QUERY)
        assert response.content == content
        assert response.confidence == 0.9
        assert len(response.recommended_actions) == 1

    def test_lead_analysis_extracts_risks_and_opportunities(self, orch):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        content = (
            '```json\n{"confidence": 0.8, "risk_factors": ["Market downturn"], '
            '"opportunities": ["Cross-sell buyer services"]}\n```'
        )
        response = orch._parse_response(content, ClaudeTaskType.LEAD_ANALYSIS)
        assert len(response.metadata.get("risk_factors", [])) == 1
        assert len(response.metadata.get("opportunities", [])) == 1

    def test_script_generation_extracts_variants(self, orch):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        content = '```json\n{"variants": [{"variant_name": "A", "script_text": "Hi!"}]}\n```'
        response = orch._parse_response(content, ClaudeTaskType.SCRIPT_GENERATION)
        assert len(response.metadata.get("script_variants", [])) == 1

    def test_graceful_degradation_on_unparseable(self, orch):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        content = "Just plain text, nothing structured."
        response = orch._parse_response(content, ClaudeTaskType.CHAT_QUERY)
        assert response.content == content
        assert response.confidence is None

    def test_intervention_strategy_extracts_opportunities(self, orch):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        content = '```json\n{"opportunities": ["Referral program"]}\n```'
        response = orch._parse_response(content, ClaudeTaskType.INTERVENTION_STRATEGY)
        assert len(response.metadata.get("opportunities", [])) == 1


# ============================================================================
# _extract_conversation_messages
# ============================================================================


class TestExtractConversationMessages:
    """Tests for _extract_conversation_messages — message validation."""

    def test_direct_conversation_history(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": "I want to buy a home"},
                {"role": "assistant", "content": "Great! What is your budget?"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 2
        assert messages[0]["role"] == "user"

    def test_messages_field(self, orch):
        memory_data = {
            "messages": [
                {"role": "user", "content": "Hello"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 1

    def test_nested_in_context(self, orch):
        memory_data = {
            "context": {
                "conversation_history": [
                    {"role": "human", "content": "Hi"},
                ]
            }
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 1

    def test_role_normalization_customer_to_user(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "customer", "content": "I need help"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert messages[0]["role"] == "user"

    def test_role_normalization_jorge_to_assistant(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "jorge", "content": "Welcome!"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert messages[0]["role"] == "assistant"

    def test_skips_missing_content(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": "Valid"},
                {"role": "assistant"},  # no content
                {"role": "user", "content": "Also valid"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 2

    def test_skips_non_dict_messages(self, orch):
        memory_data = {
            "conversation_history": [
                "not a dict",
                {"role": "user", "content": "Valid"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 1

    def test_skips_empty_content(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": ""},
                {"role": "user", "content": "   "},
                {"role": "user", "content": "Valid"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        assert len(messages) == 1
        assert messages[0]["content"] == "Valid"

    def test_empty_memory_data(self, orch):
        messages = orch._extract_conversation_messages({})
        assert messages == []

    def test_truncates_very_long_messages(self, orch):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": "x" * 20000},
                {"role": "user", "content": "short"},
            ]
        }
        messages = orch._extract_conversation_messages(memory_data)
        # The excessively long message should be skipped (>10000 chars)
        assert len(messages) == 1
        assert messages[0]["content"] == "short"


# ============================================================================
# _get_system_prompt
# ============================================================================


class TestGetSystemPrompt:
    """Tests for _get_system_prompt — prompt mapping."""

    def test_chat_query_maps_correctly(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        orch = _bare_orchestrator()
        orch.system_prompts = {
            "chat_assistant": "You are a chat assistant.",
            "lead_analyzer": "You are a lead analyzer.",
        }
        result = orch._get_system_prompt(ClaudeTaskType.CHAT_QUERY)
        assert result == "You are a chat assistant."

    def test_lead_analysis_maps_correctly(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        orch = _bare_orchestrator()
        orch.system_prompts = {
            "chat_assistant": "You are a chat assistant.",
            "lead_analyzer": "You are a lead analyzer.",
        }
        result = orch._get_system_prompt(ClaudeTaskType.LEAD_ANALYSIS)
        assert result == "You are a lead analyzer."

    def test_unknown_task_falls_back_to_chat(self):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType

        orch = _bare_orchestrator()
        orch.system_prompts = {
            "chat_assistant": "fallback prompt",
        }
        # REVENUE_PROJECTION maps to "report_synthesizer" which is missing
        result = orch._get_system_prompt(ClaudeTaskType.REVENUE_PROJECTION)
        assert result == "fallback prompt"


# ============================================================================
# _build_prompt
# ============================================================================


class TestBuildPrompt:
    """Tests for _build_prompt — prompt construction."""

    def test_includes_base_prompt(self, orch):
        result = orch._build_prompt("Analyze this lead", {"lead_id": "L1"})
        assert "Analyze this lead" in result

    def test_includes_context_as_json(self, orch):
        result = orch._build_prompt("Query", {"lead_id": "L1", "score": 85})
        assert '"lead_id": "L1"' in result
        assert '"score": 85' in result

    def test_includes_current_time(self, orch):
        result = orch._build_prompt("Query", {})
        assert "Current Time:" in result
        # Should contain a date-like string
        year = str(datetime.now().year)
        assert year in result

    def test_context_with_non_serializable_values(self, orch):
        """Datetime in context should be serialized via default=str."""
        dt = datetime(2026, 1, 15, 10, 30)
        result = orch._build_prompt("Query", {"timestamp": dt})
        assert "2026-01-15" in result
