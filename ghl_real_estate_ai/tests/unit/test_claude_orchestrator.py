"""Unit tests for ClaudeOrchestrator.

Coverage areas:
- Response parsing: _extract_json_block, _extract_balanced_json, _extract_list_items,
  _parse_confidence_score, _parse_recommended_actions, _parse_risk_factors,
  _parse_opportunities, _parse_script_variants, _structure_action,
  _structure_risk, _structure_opportunity
- Pure logic: _get_complexity_for_task, _get_system_prompt, _build_prompt,
  _update_metrics, _get_demo_fallback_response
- Execute paths: process_request end-to-end with mocked LLM, tool calling loop,
  memory cache hit/miss, error fallback to demo mode, streaming, context enhancement
"""

import json
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Heavy imports in ClaudeOrchestrator.__init__ require mocking
_init_mocks = {
    "ghl_real_estate_ai.services.claude_orchestrator.LLMClient": MagicMock,
    "ghl_real_estate_ai.services.claude_orchestrator.MemoryService": MagicMock,
    "ghl_real_estate_ai.services.claude_orchestrator.SentimentDriftEngine": MagicMock,
    "ghl_real_estate_ai.services.claude_orchestrator.PsychographicSegmentationEngine": MagicMock,
    "ghl_real_estate_ai.services.claude_orchestrator.MarketContextInjector": MagicMock,
    "ghl_real_estate_ai.services.claude_orchestrator.skill_registry": MagicMock(),
    "ghl_real_estate_ai.core.llm_client.LLMClient": MagicMock,
    "ghl_real_estate_ai.services.behavioral_triggers.BehavioralTriggerEngine": MagicMock,
    "ghl_real_estate_ai.services.churn_prediction_engine.ChurnPredictionEngine": MagicMock,
    "ghl_real_estate_ai.services.lead_lifecycle.LeadLifecycleTracker": MagicMock,
    "ghl_real_estate_ai.services.lead_scorer.LeadScorer": MagicMock,
    "ghl_real_estate_ai.services.perplexity_researcher.PerplexityResearcher": MagicMock,
    "ghl_real_estate_ai.services.predictive_lead_scorer.PredictiveLeadScorer": MagicMock,
    "ghl_real_estate_ai.services.ghl_client.GHLClient": MagicMock,
    "ghl_real_estate_ai.services.analytics_service.AnalyticsService": MagicMock,
    "ghl_real_estate_ai.core.mcp_servers.domain.analytics_intelligence_server.mcp": MagicMock(),
    "ghl_real_estate_ai.core.mcp_servers.domain.lead_intelligence_server.mcp": MagicMock(),
    "ghl_real_estate_ai.core.mcp_servers.domain.market_intelligence_server.mcp": MagicMock(),
    "ghl_real_estate_ai.core.mcp_servers.domain.negotiation_intelligence_server.mcp": MagicMock(),
    "ghl_real_estate_ai.core.mcp_servers.domain.property_intelligence_server.mcp": MagicMock(),
    "ghl_real_estate_ai.services.memory_service.MemoryService": MagicMock,
    "ghl_real_estate_ai.services.market_context_injector.MarketContextInjector": MagicMock,
    "ghl_real_estate_ai.services.sentiment_drift_engine.SentimentDriftEngine": MagicMock,
    "ghl_real_estate_ai.services.psychographic_segmentation_engine.PsychographicSegmentationEngine": MagicMock,
}


@pytest.fixture
def orchestrator():
    """Create a ClaudeOrchestrator with all heavy deps mocked."""
    with patch.multiple("ghl_real_estate_ai.services.claude_orchestrator", **{
        "LLMClient": MagicMock,
        "MemoryService": MagicMock,
        "SentimentDriftEngine": MagicMock,
        "PsychographicSegmentationEngine": MagicMock,
        "MarketContextInjector": MagicMock,
        "safe_create_task": MagicMock(),
    }):
        from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator, ClaudeTaskType

        orch = ClaudeOrchestrator.__new__(ClaudeOrchestrator)
        # Manually init the fields we need for parsing tests
        orch.system_prompts = orch._load_system_prompts()
        orch.performance_metrics = {"requests_processed": 0, "avg_response_time": 0.0, "errors": 0}
        orch.agents = {}
        orch._memory_context_cache = {}
    return orch


@pytest.fixture
def task_types():
    from ghl_real_estate_ai.services.claude_orchestrator import ClaudeTaskType
    return ClaudeTaskType


# ---------------------------------------------------------------------------
# _extract_json_block tests
# ---------------------------------------------------------------------------

class TestExtractJsonBlock:
    def test_extract_from_markdown_code_block(self, orchestrator):
        content = 'Some text\n```json\n{"key": "value"}\n```\nmore text'
        result = orchestrator._extract_json_block(content)
        assert result == {"key": "value"}

    def test_extract_from_generic_code_block(self, orchestrator):
        content = 'Text\n```\n{"score": 85}\n```'
        result = orchestrator._extract_json_block(content)
        assert result == {"score": 85}

    def test_extract_plain_json(self, orchestrator):
        content = 'Analysis: {"confidence": 0.9, "risk": "low"} end'
        result = orchestrator._extract_json_block(content)
        assert result["confidence"] == 0.9

    def test_no_json_returns_none(self, orchestrator):
        content = "No JSON here at all."
        result = orchestrator._extract_json_block(content)
        assert result is None

    def test_invalid_json_returns_none(self, orchestrator):
        content = '```json\n{broken json\n```'
        result = orchestrator._extract_json_block(content)
        assert result is None


# ---------------------------------------------------------------------------
# _extract_balanced_json tests
# ---------------------------------------------------------------------------

class TestExtractBalancedJson:
    def test_simple_object(self, orchestrator):
        content = 'prefix {"a": 1} suffix'
        result = orchestrator._extract_balanced_json(content, content.index("{"))
        assert json.loads(result) == {"a": 1}

    def test_nested_object(self, orchestrator):
        content = '{"outer": {"inner": true}}'
        result = orchestrator._extract_balanced_json(content, 0)
        assert json.loads(result)["outer"]["inner"] is True

    def test_strings_with_braces(self, orchestrator):
        content = '{"text": "contains {braces}"}'
        result = orchestrator._extract_balanced_json(content, 0)
        assert json.loads(result)["text"] == "contains {braces}"

    def test_unbalanced_returns_none(self, orchestrator):
        content = '{"incomplete": true'
        result = orchestrator._extract_balanced_json(content, 0)
        assert result is None


# ---------------------------------------------------------------------------
# _parse_confidence_score tests
# ---------------------------------------------------------------------------

class TestParseConfidenceScore:
    def test_from_json_decimal(self, orchestrator):
        score = orchestrator._parse_confidence_score("", {"confidence": 0.85})
        assert score == 0.85

    def test_from_json_percentage(self, orchestrator):
        score = orchestrator._parse_confidence_score("", {"confidence": 85})
        assert score == 0.85

    def test_from_text_percentage(self, orchestrator):
        score = orchestrator._parse_confidence_score("The confidence: 92%", None)
        assert score == 0.92

    def test_from_text_decimal(self, orchestrator):
        score = orchestrator._parse_confidence_score("confidence score: 0.75", None)
        assert score == 0.75

    def test_qualitative_high(self, orchestrator):
        score = orchestrator._parse_confidence_score("I have high confidence in this.", None)
        assert score == 0.9

    def test_qualitative_low(self, orchestrator):
        score = orchestrator._parse_confidence_score("low confidence assessment", None)
        assert score == 0.4

    def test_no_confidence_returns_none(self, orchestrator):
        score = orchestrator._parse_confidence_score("No score here.", None)
        assert score is None


# ---------------------------------------------------------------------------
# _structure_action tests
# ---------------------------------------------------------------------------

class TestStructureAction:
    def test_high_priority_detection(self, orchestrator):
        action = orchestrator._structure_action("URGENT: Call the lead immediately")
        assert action["priority"] == "high"
        assert action["timing"] == "immediate"

    def test_low_priority_detection(self, orchestrator):
        action = orchestrator._structure_action("Consider sending a follow-up next week")
        assert action["priority"] == "low"
        assert action["timing"] == "low"

    def test_default_medium_priority(self, orchestrator):
        action = orchestrator._structure_action("Schedule a property tour this week")
        assert action["priority"] == "medium"
        assert action["timing"] == "moderate"


# ---------------------------------------------------------------------------
# _structure_risk tests
# ---------------------------------------------------------------------------

class TestStructureRisk:
    def test_high_severity_detection(self, orchestrator):
        risk = orchestrator._structure_risk("Critical: Lead may churn due to competitor offer")
        assert risk["severity"] == "high"

    def test_low_severity_detection(self, orchestrator):
        risk = orchestrator._structure_risk("Minor timing concern with school districts")
        assert risk["severity"] == "low"

    def test_mitigation_extraction(self, orchestrator):
        risk = orchestrator._structure_risk("Budget concern. Mitigation: offer payment plan")
        assert "payment plan" in risk["mitigation"]


# ---------------------------------------------------------------------------
# _structure_opportunity tests
# ---------------------------------------------------------------------------

class TestStructureOpportunity:
    def test_dollar_value_extraction(self, orchestrator):
        opp = orchestrator._structure_opportunity("Upsell potential $50,000 commission")
        assert opp["potential_value"] == "$50,000"

    def test_percentage_value_extraction(self, orchestrator):
        opp = orchestrator._structure_opportunity("15% conversion improvement possible")
        assert opp["potential_value"] == "15%"

    def test_qualitative_high_value(self, orchestrator):
        opp = orchestrator._structure_opportunity("Significant referral network opportunity")
        assert opp["potential_value"] == "high"


# ---------------------------------------------------------------------------
# _get_complexity_for_task tests
# ---------------------------------------------------------------------------

class TestGetComplexity:
    def test_routine_task(self, orchestrator, task_types):
        from ghl_real_estate_ai.core.llm_client import TaskComplexity
        result = orchestrator._get_complexity_for_task(task_types.CHAT_QUERY)
        assert result == TaskComplexity.ROUTINE

    def test_high_stakes_task(self, orchestrator, task_types):
        from ghl_real_estate_ai.core.llm_client import TaskComplexity
        result = orchestrator._get_complexity_for_task(task_types.EXECUTIVE_BRIEFING)
        assert result == TaskComplexity.HIGH_STAKES

    def test_complex_task_default(self, orchestrator, task_types):
        from ghl_real_estate_ai.core.llm_client import TaskComplexity
        result = orchestrator._get_complexity_for_task(task_types.REPORT_SYNTHESIS)
        assert result == TaskComplexity.COMPLEX


# ---------------------------------------------------------------------------
# _get_system_prompt tests
# ---------------------------------------------------------------------------

class TestGetSystemPrompt:
    def test_chat_query_prompt(self, orchestrator, task_types):
        prompt = orchestrator._get_system_prompt(task_types.CHAT_QUERY)
        assert "real estate" in prompt.lower()

    def test_lead_analysis_prompt(self, orchestrator, task_types):
        prompt = orchestrator._get_system_prompt(task_types.LEAD_ANALYSIS)
        assert "analyst" in prompt.lower()

    def test_script_generation_prompt(self, orchestrator, task_types):
        prompt = orchestrator._get_system_prompt(task_types.SCRIPT_GENERATION)
        assert "script" in prompt.lower() or "communication" in prompt.lower()


# ---------------------------------------------------------------------------
# _update_metrics tests
# ---------------------------------------------------------------------------

class TestUpdateMetrics:
    def test_success_increments_count(self, orchestrator):
        orchestrator._update_metrics(100, success=True)
        assert orchestrator.performance_metrics["requests_processed"] == 1

    def test_failure_increments_errors(self, orchestrator):
        orchestrator._update_metrics(0, success=False)
        assert orchestrator.performance_metrics["errors"] == 1

    def test_avg_response_time_updates(self, orchestrator):
        orchestrator._update_metrics(100, success=True)
        orchestrator._update_metrics(200, success=True)
        avg = orchestrator.performance_metrics["avg_response_time"]
        assert avg == 150.0


# ---------------------------------------------------------------------------
# _get_demo_fallback_response tests
# ---------------------------------------------------------------------------

class TestDemoFallback:
    def test_chat_query_fallback(self, orchestrator, task_types):
        resp = orchestrator._get_demo_fallback_response(task_types.CHAT_QUERY)
        assert "Simulated" in resp.content
        assert resp.metadata["demo_mode"] is True

    def test_unknown_task_type_fallback(self, orchestrator, task_types):
        resp = orchestrator._get_demo_fallback_response(task_types.OMNIPOTENT_ASSISTANT)
        assert "Simulated" in resp.content


# ---------------------------------------------------------------------------
# _extract_list_items tests
# ---------------------------------------------------------------------------

class TestExtractListItems:
    def test_numbered_list(self, orchestrator):
        content = """Recommended Actions:
1. Call the lead
2. Send market report
3. Schedule showing
"""
        items = orchestrator._extract_list_items(content, "Recommended Actions")
        assert len(items) >= 2

    def test_bullet_list(self, orchestrator):
        content = """Next Steps:
- Review pricing
- Contact agent
"""
        items = orchestrator._extract_list_items(content, "Next Steps")
        assert len(items) >= 1

    def test_missing_section_returns_empty(self, orchestrator):
        content = "No sections here"
        items = orchestrator._extract_list_items(content, "Nonexistent Section")
        assert items == []


# ---------------------------------------------------------------------------
# _parse_response integration tests
# ---------------------------------------------------------------------------

class TestParseResponse:
    def test_parse_lead_analysis_extracts_risks(self, orchestrator, task_types):
        content = """Analysis complete. confidence: 85%

Risk Factors:
1. Critical budget constraint
2. Minor timing issue

Opportunities:
- Significant referral network
"""
        resp = orchestrator._parse_response(content, task_types.LEAD_ANALYSIS)
        assert resp.confidence == 0.85
        assert len(resp.metadata.get("risk_factors", [])) >= 1
        assert len(resp.metadata.get("opportunities", [])) >= 1

    def test_parse_script_generation(self, orchestrator, task_types):
        content = """Here are your scripts:

Variant A:
Hi! I noticed you were looking at homes in Rancho Cucamonga.

Variant B:
Jorge here - got a hot listing you might like!
"""
        resp = orchestrator._parse_response(content, task_types.SCRIPT_GENERATION)
        assert "script_variants" in resp.metadata

    def test_parse_with_json_block(self, orchestrator, task_types):
        content = """Analysis:
```json
{"confidence": 0.92, "recommended_actions": ["Call lead", "Send CMA"]}
```
"""
        resp = orchestrator._parse_response(content, task_types.LEAD_ANALYSIS)
        assert resp.confidence == 0.92
        assert len(resp.recommended_actions) == 2


# ---------------------------------------------------------------------------
# Helpers for process_request tests
# ---------------------------------------------------------------------------

def _make_mock_llm_response(content="Test response", tool_calls=None):
    """Build a mock LLMResponse-like object."""
    resp = MagicMock()
    resp.content = content
    resp.input_tokens = 100
    resp.output_tokens = 50
    resp.model = "claude-sonnet-4-5-20250514"
    resp.provider = MagicMock()
    resp.provider.value = "claude"
    resp.tool_calls = tool_calls
    return resp


def _make_full_orchestrator():
    """Create a ClaudeOrchestrator with wired-up mocks suitable for process_request."""
    with patch.multiple("ghl_real_estate_ai.services.claude_orchestrator", **{
        "LLMClient": MagicMock,
        "MemoryService": MagicMock,
        "SentimentDriftEngine": MagicMock,
        "PsychographicSegmentationEngine": MagicMock,
        "MarketContextInjector": MagicMock,
        "safe_create_task": MagicMock(),
        "skill_registry": MagicMock(),
    }):
        from ghl_real_estate_ai.services.claude_orchestrator import (
            ClaudeOrchestrator,
            ClaudeRequest,
            ClaudeResponse,
            ClaudeTaskType,
        )

        orch = ClaudeOrchestrator.__new__(ClaudeOrchestrator)
        orch.system_prompts = orch._load_system_prompts()
        orch.performance_metrics = {"requests_processed": 0, "avg_response_time": 0.0, "errors": 0}
        orch._memory_context_cache = {}
        orch._response_cache = {}
        orch._response_cache_ttl = 300
        orch._response_cache_hits = 0
        orch._response_cache_misses = 0
        orch.llm = MagicMock()
        orch.memory = MagicMock()
        orch.mcp_servers = {}
    return orch, ClaudeRequest, ClaudeResponse, ClaudeTaskType


# ---------------------------------------------------------------------------
# process_request end-to-end tests (mocked LLM)
# ---------------------------------------------------------------------------

class TestProcessRequest:
    @pytest.mark.asyncio
    async def test_process_request_success(self):
        orch, ClaudeRequest, _, ClaudeTaskType = _make_full_orchestrator()
        mock_resp = _make_mock_llm_response("Lead analysis complete. confidence: 80%")
        orch.llm.agenerate = AsyncMock(return_value=mock_resp)
        orch.memory.get_context = AsyncMock(return_value={"relevant_knowledge": ""})

        request = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={"lead_id": "lead-1"},
            prompt="Analyze this lead",
        )
        response = await orch.process_request(request)

        assert response.content == "Lead analysis complete. confidence: 80%"
        assert response.response_time_ms >= 0
        assert response.input_tokens == 100
        assert response.output_tokens == 50
        assert orch.performance_metrics["requests_processed"] == 1

    @pytest.mark.asyncio
    async def test_process_request_uses_custom_system_prompt(self):
        orch, ClaudeRequest, _, ClaudeTaskType = _make_full_orchestrator()
        mock_resp = _make_mock_llm_response("OK")
        orch.llm.agenerate = AsyncMock(return_value=mock_resp)
        orch.memory.get_context = AsyncMock(return_value={})

        custom_prompt = "You are a test assistant."
        request = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY,
            context={},
            prompt="Hello",
            system_prompt=custom_prompt,
        )
        await orch.process_request(request)

        # Verify the custom system prompt was forwarded to the LLM
        call_kwargs = orch.llm.agenerate.call_args
        assert call_kwargs.kwargs.get("system_prompt") == custom_prompt

    @pytest.mark.asyncio
    async def test_process_request_auth_error_returns_demo(self):
        orch, ClaudeRequest, _, ClaudeTaskType = _make_full_orchestrator()
        orch.llm.agenerate = AsyncMock(side_effect=Exception("401 authentication_error"))
        orch.memory.get_context = AsyncMock(return_value={})

        request = ClaudeRequest(
            task_type=ClaudeTaskType.CHAT_QUERY,
            context={},
            prompt="Hello",
        )
        response = await orch.process_request(request)

        assert response.metadata.get("demo_mode") is True
        assert orch.performance_metrics["errors"] == 1

    @pytest.mark.asyncio
    async def test_process_request_generic_error(self):
        orch, ClaudeRequest, _, ClaudeTaskType = _make_full_orchestrator()
        orch.llm.agenerate = AsyncMock(side_effect=RuntimeError("connection failed"))
        orch.memory.get_context = AsyncMock(return_value={})

        request = ClaudeRequest(
            task_type=ClaudeTaskType.LEAD_ANALYSIS,
            context={},
            prompt="Analyze",
        )
        response = await orch.process_request(request)

        assert "connection failed" in response.content
        assert response.metadata.get("error") is True

    @pytest.mark.asyncio
    async def test_process_request_with_tool_calls(self):
        orch, ClaudeRequest, _, ClaudeTaskType = _make_full_orchestrator()

        # First call returns a tool call, second returns final text
        tool_call_resp = _make_mock_llm_response("Thinking...", tool_calls=[
            {"id": "tc_1", "name": "analyze_lead", "args": {"lead_id": "L1"}}
        ])
        final_resp = _make_mock_llm_response("Final analysis complete.")

        orch.llm.agenerate = AsyncMock(side_effect=[tool_call_resp, final_resp])
        orch.memory.get_context = AsyncMock(return_value={})

        # Mock skill_registry to return a server
        from unittest.mock import PropertyMock
        mock_registry = MagicMock()
        mock_registry.get_all_tools.return_value = ["analyze_lead"]
        mock_registry.get_server_for_tool.return_value = "LeadIntelligence"
        mock_registry.get_category_for_tool.return_value = None

        mock_server = MagicMock()
        mock_server.get_tool = AsyncMock(return_value=MagicMock(
            name="analyze_lead", description="Analyze a lead",
            model_json_schema=MagicMock(return_value={"type": "object", "properties": {}})
        ))
        mock_server._call_tool = AsyncMock(return_value="Tool result data")
        orch.mcp_servers = {"LeadIntelligence": mock_server}

        with patch("ghl_real_estate_ai.services.claude_orchestrator.skill_registry", mock_registry):
            request = ClaudeRequest(
                task_type=ClaudeTaskType.LEAD_ANALYSIS,
                context={},
                prompt="Analyze lead",
                use_tools=True,
            )
            response = await orch.process_request(request)

        assert response.content == "Final analysis complete."
        assert response.metadata.get("tool_executions") is not None


# ---------------------------------------------------------------------------
# Memory cache hit / miss tests
# ---------------------------------------------------------------------------

class TestContextEnhancement:
    @pytest.mark.asyncio
    async def test_enhance_context_cache_miss(self):
        orch, _, _, _ = _make_full_orchestrator()
        orch.memory.get_context = AsyncMock(return_value={
            "relevant_knowledge": "Lead prefers 3BR homes",
            "conversation_history": [{"role": "user", "content": "hi"}],
            "extracted_preferences": {"bedrooms": 3},
        })

        context = {"lead_id": "lead-42"}
        enhanced = await orch._enhance_context(context)

        assert enhanced["semantic_memory"] == "Lead prefers 3BR homes"
        assert enhanced["extracted_preferences"]["bedrooms"] == 3
        orch.memory.get_context.assert_called_once_with("lead-42")
        # Should be cached now
        assert "mem_ctx:lead-42" in orch._memory_context_cache

    @pytest.mark.asyncio
    async def test_enhance_context_cache_hit(self):
        orch, _, _, _ = _make_full_orchestrator()
        orch._memory_context_cache["mem_ctx:lead-42"] = {
            "relevant_knowledge": "cached data",
            "conversation_history": [],
            "extracted_preferences": {},
        }
        orch.memory.get_context = AsyncMock()

        context = {"lead_id": "lead-42"}
        enhanced = await orch._enhance_context(context)

        assert enhanced["semantic_memory"] == "cached data"
        orch.memory.get_context.assert_not_called()

    @pytest.mark.asyncio
    async def test_enhance_context_memory_unavailable(self):
        orch, _, _, _ = _make_full_orchestrator()
        orch.memory.get_context = AsyncMock(side_effect=ConnectionError("Redis down"))

        context = {"lead_id": "lead-99"}
        enhanced = await orch._enhance_context(context)

        # Should gracefully degrade — no semantic_memory key
        assert "semantic_memory" not in enhanced
        assert enhanced["lead_id"] == "lead-99"

    @pytest.mark.asyncio
    async def test_enhance_context_no_lead_id(self):
        orch, _, _, _ = _make_full_orchestrator()
        orch.memory.get_context = AsyncMock()

        context = {"query_type": "general"}
        enhanced = await orch._enhance_context(context)

        orch.memory.get_context.assert_not_called()
        assert enhanced["query_type"] == "general"


# ---------------------------------------------------------------------------
# _build_prompt tests
# ---------------------------------------------------------------------------

class TestBuildPrompt:
    def test_build_prompt_includes_context(self, orchestrator):
        result = orchestrator._build_prompt("Analyze lead", {"lead_id": "L1"})
        assert "Analyze lead" in result
        assert "lead_id" in result
        assert "L1" in result

    def test_build_prompt_includes_timestamp(self, orchestrator):
        result = orchestrator._build_prompt("Hello", {})
        assert "Current Time:" in result


# ---------------------------------------------------------------------------
# _extract_conversation_messages tests
# ---------------------------------------------------------------------------

class TestExtractConversationMessages:
    def test_direct_conversation_history(self, orchestrator):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": "I want to buy a house"},
                {"role": "assistant", "content": "Great! What's your budget?"},
            ]
        }
        msgs = orchestrator._extract_conversation_messages(memory_data)
        assert len(msgs) == 2
        assert msgs[0]["role"] == "user"

    def test_role_normalization(self, orchestrator):
        memory_data = {
            "conversation_history": [
                {"role": "customer", "content": "hello"},
                {"role": "jorge", "content": "hi there"},
            ]
        }
        msgs = orchestrator._extract_conversation_messages(memory_data)
        assert msgs[0]["role"] == "user"
        assert msgs[1]["role"] == "assistant"

    def test_skips_invalid_messages(self, orchestrator):
        memory_data = {
            "conversation_history": [
                {"role": "user", "content": "valid"},
                {"role": "", "content": ""},  # empty role & content
                "not a dict",
                {"role": "user", "content": "also valid"},
            ]
        }
        msgs = orchestrator._extract_conversation_messages(memory_data)
        assert len(msgs) == 2

    def test_empty_memory_returns_empty(self, orchestrator):
        msgs = orchestrator._extract_conversation_messages({})
        assert msgs == []

    def test_nested_context_extraction(self, orchestrator):
        memory_data = {
            "context": {
                "messages": [
                    {"role": "user", "content": "from nested context"},
                ]
            }
        }
        msgs = orchestrator._extract_conversation_messages(memory_data)
        assert len(msgs) == 1


# ---------------------------------------------------------------------------
# get_performance_metrics tests
# ---------------------------------------------------------------------------

class TestGetPerformanceMetrics:
    def test_returns_copy(self, orchestrator):
        metrics = orchestrator.get_performance_metrics()
        metrics["requests_processed"] = 999
        assert orchestrator.performance_metrics["requests_processed"] == 0
