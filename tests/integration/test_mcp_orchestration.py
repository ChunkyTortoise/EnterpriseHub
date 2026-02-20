import pytest

pytestmark = pytest.mark.integration

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from ghl_real_estate_ai.core.llm_client import LLMProvider, LLMResponse
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator, ClaudeRequest, ClaudeTaskType
from ghl_real_estate_ai.services.skill_registry import SkillCategory


@pytest.mark.asyncio
async def test_mcp_tool_discovery():
    """Test that the orchestrator can discover and format tools from MCP servers."""
    orchestrator = ClaudeOrchestrator()

    # Mock MCP servers to avoid recursion into real services
    mock_lead_server = MagicMock()
    mock_lead_tool = MagicMock()
    mock_lead_tool.name = "analyze_lead"
    mock_lead_tool.description = "Test Description"
    mock_lead_tool.model_json_schema.return_value = {"type": "object"}
    mock_lead_server.get_tool = AsyncMock(return_value=mock_lead_tool)

    mock_analytics_server = MagicMock()
    mock_analytics_tool = MagicMock()
    mock_analytics_tool.name = "get_daily_summary"
    mock_analytics_tool.description = "Test Description"
    mock_analytics_tool.model_json_schema.return_value = {"type": "object"}
    mock_analytics_server.get_tool = AsyncMock(return_value=mock_analytics_tool)

    orchestrator.mcp_servers = {"LeadIntelligence": mock_lead_server, "AnalyticsIntelligence": mock_analytics_server}

    # Test discovery for ANALYSIS category
    tools = await orchestrator._get_tools_for_request([SkillCategory.ANALYSIS])

    # Verify we have tools from LeadIntelligence and AnalyticsIntelligence
    tool_names = [t["name"] for t in tools]
    assert "analyze_lead" in tool_names
    assert "get_daily_summary" in tool_names

    # Verify tool structure
    analyze_tool = next(t for t in tools if t["name"] == "analyze_lead")
    assert "description" in analyze_tool
    assert "parameters" in analyze_tool
    assert analyze_tool["parameters"]["type"] == "object"


@pytest.mark.asyncio
async def test_mcp_tool_execution():
    """Test that the orchestrator can execute a tool call."""
    orchestrator = ClaudeOrchestrator()

    # Mock the server and tool execution to avoid recursion into real services
    mock_server = MagicMock()
    mock_server._call_tool = AsyncMock(return_value='{"score": 7, "reasoning": "High intent"}')
    orchestrator.mcp_servers["LeadIntelligence"] = mock_server

    # Mock tool call
    tool_call = {"id": "call_123", "name": "get_lead_score_breakdown", "args": {"lead_context": {"test": "data"}}}

    # Execute
    result = await orchestrator._execute_tool_call(tool_call)

    # Verify result looks like JSON
    import json

    parsed = json.loads(result)
    assert parsed["score"] == 7


@pytest.mark.asyncio
async def test_multi_turn_orchestration():
    """Test the full multi-turn tool orchestration loop."""
    # Mock LLM Client
    mock_llm = MagicMock()
    orchestrator = ClaudeOrchestrator(llm_client=mock_llm)

    # Mock _execute_tool_call to avoid recursion
    orchestrator._execute_tool_call = AsyncMock(return_value='{"status": "success"}')

    # 1. First turn: LLM decides to use a tool
    turn1_response = LLMResponse(
        content="I need to analyze this lead first.",
        provider=LLMProvider.CLAUDE,
        model="claude-3-5-sonnet",
        tool_calls=[{"id": "tc_01", "name": "analyze_lead", "args": {"lead_name": "John Doe", "lead_context": {}}}],
    )

    # 2. Second turn: LLM gives final answer
    turn2_response = LLMResponse(
        content="Based on the analysis, John Doe is a high-intent buyer.",
        provider=LLMProvider.CLAUDE,
        model="claude-3-5-sonnet",
        input_tokens=100,
        output_tokens=50,
    )

    mock_llm.agenerate = AsyncMock(side_effect=[turn1_response, turn2_response])

    request = ClaudeRequest(
        task_type=ClaudeTaskType.CHAT_QUERY,
        context={"lead_id": "test_lead"},
        prompt="Tell me about this lead",
        use_tools=True,
        allowed_categories=[SkillCategory.ANALYSIS],
    )

    response = await orchestrator.process_request(request)

    assert "John Doe" in response.content
    assert "tool_executions" in response.metadata
    # 3 steps: 1. Assistant tool_use, 2. User tool_result, 3. Assistant final text (last step doesn't have tool calls but is the final answer)
    # Actually tool_executions appends ONLY when it calls tools or receives results.
    # Turn 1: appends assistant tool_use
    # Turn 1 loop: appends user tool_result
    # Turn 2: appends assistant final text (loop ends)
    assert len(response.metadata["tool_executions"]) >= 3


@pytest.mark.asyncio
async def test_ghl_sync_on_action():
    """Test that GHL background sync is triggered when an ACTION category tool is used."""
    mock_llm = MagicMock()
    orchestrator = ClaudeOrchestrator(llm_client=mock_llm)

    # Mock GHL client
    orchestrator.ghl_client = MagicMock()
    orchestrator.ghl_client.update_custom_field = AsyncMock(return_value={"status": "success"})
    orchestrator.ghl_client.location_id = "test_location"

    # Mock sync method to see if it's called
    orchestrator._sync_action_to_ghl = AsyncMock()

    # Mock _execute_tool_call
    orchestrator._execute_tool_call = AsyncMock(return_value='{"script": "Hi John!"}')

    # First turn: Use an ACTION tool
    turn1_response = LLMResponse(
        content="I will generate a script for this lead.",
        provider=LLMProvider.CLAUDE,
        model="claude-3-5-sonnet",
        tool_calls=[
            {"id": "tc_action", "name": "generate_lead_outreach_script", "args": {"lead_id": "real_contact_123"}}
        ],
    )

    turn2_response = LLMResponse(
        content="Script generated and synced.", provider=LLMProvider.CLAUDE, model="claude-3-5-sonnet"
    )

    mock_llm.agenerate = AsyncMock(side_effect=[turn1_response, turn2_response])

    request = ClaudeRequest(
        task_type=ClaudeTaskType.SCRIPT_GENERATION,
        context={"contact_id": "real_contact_123"},
        prompt="Generate a script",
        use_tools=True,
    )

    await orchestrator.process_request(request)

    # Give it a tiny bit of time for the async task to be scheduled/run
    await asyncio.sleep(0.1)

    # Verify _sync_action_to_ghl was called for the ACTION tool
    orchestrator._sync_action_to_ghl.assert_called_once()