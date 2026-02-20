"""Tests for concrete runtime Agent implementation."""

import pytest

from agentforge import Agent, AgentInput, tool


class TestRuntimeAgent:
    @pytest.mark.asyncio
    async def test_agent_mock_executes(self) -> None:
        agent = Agent(
            name="assistant",
            instructions="Respond briefly.",
            llm="mock/mock-v1",
        )
        out = await agent(AgentInput(messages=[{"role": "user", "content": "hello"}]))
        assert out.error is None
        assert isinstance(out.content, str)
        assert out.metadata["provider"] == "mock"

    @pytest.mark.asyncio
    async def test_agent_tool_call_round_trip(self) -> None:
        @tool
        def calculate(expression: str) -> float:
            return eval(expression)  # noqa: S307 - test-only input

        agent = Agent(
            name="calculator",
            instructions="Use tools when needed.",
            llm="mock/mock-v1",
            tools=[calculate],
        )
        out = await agent(
            AgentInput(messages=[{"role": "user", "content": "What is 2+2?"}])
        )
        assert out.error is None
        assert "4" in (out.content or "")
