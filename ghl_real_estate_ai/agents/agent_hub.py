"""LangGraph-powered Agent Hub with planner, researcher, reviewer, publisher."""
from __future__ import annotations

from typing import Dict, TypedDict

from langgraph.graph import StateGraph, END

from ghl_real_estate_ai.core.llm_client import get_llm_client


class AgentHubState(TypedDict, total=False):
    query: str
    plan: str
    research: str
    draft: str
    review_notes: str
    approved: bool
    iterations: int
    final: str


class AgentHub:
    def __init__(self) -> None:
        self.llm = get_llm_client()
        self.graph = self._build_graph()

    def _safe_generate(self, prompt: str, fallback: str) -> str:
        try:
            response = self.llm.generate(prompt=prompt, max_tokens=600, temperature=0.3)
            return response.content.strip() if response and response.content else fallback
        except Exception:
            return fallback

    def _planner(self, state: AgentHubState) -> Dict[str, str]:
        prompt = f"Create a concise action plan for: {state.get('query', '')}"
        plan = self._safe_generate(prompt, "Plan: Gather key facts, summarize findings, propose next steps.")
        return {"plan": plan}

    def _researcher(self, state: AgentHubState) -> Dict[str, str]:
        prompt = f"Research summary for: {state.get('query', '')}\nPlan: {state.get('plan', '')}"
        research = self._safe_generate(prompt, "Research: No external sources configured; provide internal summary.")
        return {"research": research}

    def _reviewer(self, state: AgentHubState) -> Dict[str, str]:
        draft = f"{state.get('plan', '')}\n\n{state.get('research', '')}"
        prompt = f"Review the draft for gaps and clarity. Return brief notes.\n\nDraft:\n{draft}"
        review_notes = self._safe_generate(prompt, "Review: Looks good. Minor wording improvements suggested.")
        approved = "gap" not in review_notes.lower()
        iterations = int(state.get("iterations", 0)) + 1
        return {"review_notes": review_notes, "approved": approved, "draft": draft, "iterations": iterations}

    def _publisher(self, state: AgentHubState) -> Dict[str, str]:
        prompt = (
            "Publish a final response based on the plan, research, and review notes.\n\n"
            f"Plan:\n{state.get('plan', '')}\n\nResearch:\n{state.get('research', '')}\n\n"
            f"Review Notes:\n{state.get('review_notes', '')}"
        )
        final = self._safe_generate(prompt, state.get("draft", ""))
        return {"final": final}

    def _review_router(self, state: AgentHubState) -> str:
        if state.get("approved"):
            return "publisher"
        if int(state.get("iterations", 0)) >= 2:
            return "publisher"
        return "researcher"

    def _build_graph(self):
        workflow = StateGraph(AgentHubState)
        workflow.add_node("planner", self._planner)
        workflow.add_node("researcher", self._researcher)
        workflow.add_node("reviewer", self._reviewer)
        workflow.add_node("publisher", self._publisher)

        workflow.add_edge("planner", "researcher")
        workflow.add_edge("researcher", "reviewer")
        workflow.add_conditional_edges(
            "reviewer",
            self._review_router,
            {"researcher": "researcher", "publisher": "publisher"},
        )
        workflow.add_edge("publisher", END)

        return workflow.compile()

    def run(self, query: str) -> AgentHubState:
        initial_state: AgentHubState = {"query": query, "iterations": 0, "approved": False}
        return self.graph.invoke(initial_state)

    def run_for_review(self, query: str) -> AgentHubState:
        state: AgentHubState = {"query": query, "iterations": 0, "approved": False}
        state.update(self._planner(state))
        state.update(self._researcher(state))
        state.update(self._reviewer(state))
        return state

    def publish(self, state: AgentHubState, edits: str | None = None) -> AgentHubState:
        if edits:
            state["draft"] = edits
        state.update(self._publisher(state))
        return state
