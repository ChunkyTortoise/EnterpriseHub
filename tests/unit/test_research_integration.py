import asyncio
import unittest
from unittest.mock import MagicMock, patch

from ghl_real_estate_ai.models.orchestrator_types import OrchestratorContext
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeOrchestrator, ClaudeRequest, ClaudeTaskType
from ghl_real_estate_ai.services.skill_registry import SkillCategory


class TestResearchIntegration(unittest.IsolatedAsyncioTestCase):
    """Test suite for Perplexity and NotebookLM integration."""

    @patch("ghl_real_estate_ai.core.llm_client.LLMClient.agenerate")
    async def test_notebook_researcher(self, mock_agenerate):
        """Test NotebookResearcher grounded query."""
        from ghl_real_estate_ai.services.notebook_researcher import NotebookResearcher

        # Setup mock response
        mock_response = MagicMock()
        mock_response.content = "Based on the documents, the market is growing."
        mock_agenerate.return_value = mock_response

        researcher = NotebookResearcher(api_key="mock-key")
        nb_id = researcher.create_notebook("Test Notebook")
        researcher.add_source(nb_id, "Doc1", "Market is growing at 5%.")

        result = await researcher.query_notebook(nb_id, "How is the market?")

        self.assertIn("growing", result)
        mock_agenerate.assert_called_once()

    @patch("ghl_real_estate_ai.services.perplexity_researcher.LLMClient.agenerate")
    async def test_perplexity_researcher(self, mock_agenerate):
        """Test PerplexityResearcher web lookup."""
        from ghl_real_estate_ai.services.perplexity_researcher import PerplexityResearcher

        mock_response = MagicMock()
        mock_response.content = "Current mortgage rates are 6.5%."
        mock_agenerate.return_value = mock_response

        researcher = PerplexityResearcher(api_key="mock-key")
        result = await researcher.get_market_trends("Rancho Cucamonga, CA")

        self.assertIn("6.5%", result)

    @patch("ghl_real_estate_ai.services.claude_orchestrator.ClaudeOrchestrator._execute_tool_call")
    @patch("ghl_real_estate_ai.core.llm_client.LLMClient.agenerate")
    async def test_orchestrator_research_flow(self, mock_agenerate, mock_execute_tool):
        """Test ClaudeOrchestrator using research tools."""
        orchestrator = ClaudeOrchestrator()

        # 1. Mock first turn: Claude decides to use web_research
        turn1_response = MagicMock()
        turn1_response.content = "I need to check the latest data."
        turn1_response.tool_calls = [{"id": "call_1", "name": "web_research", "args": {"query": "latest trends"}}]
        turn1_response.model = "claude-3-sonnet"
        turn1_response.provider = MagicMock()
        turn1_response.provider.value = "claude"
        turn1_response.input_tokens = 100
        turn1_response.output_tokens = 50

        # 2. Mock tool execution result
        mock_execute_tool.return_value = "Trends are positive."

        # 3. Mock second turn: Claude synthesizes result
        turn2_response = MagicMock()
        turn2_response.content = "Research shows trends are positive."
        turn2_response.tool_calls = []
        turn2_response.model = "claude-3-sonnet"
        turn2_response.provider = MagicMock()
        turn2_response.provider.value = "claude"
        turn2_response.input_tokens = 200
        turn2_response.output_tokens = 100

        mock_agenerate.side_effect = [turn1_response, turn2_response]

        request = ClaudeRequest(
            task_type=ClaudeTaskType.RESEARCH_QUERY,
            context={"location_id": "test_loc"},
            prompt="What are the trends?",
            use_tools=True,
            allowed_categories=[SkillCategory.RESEARCH],
        )

        response = await orchestrator.process_request(request)

        self.assertIn("positive", response.content)
        self.assertEqual(mock_execute_tool.call_count, 1)


if __name__ == "__main__":
    unittest.main()
