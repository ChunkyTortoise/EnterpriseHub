"""
LangGraph Compliance Loop - Self-Healing AI Workflows.
Implements a stateful loop that forces AI re-generation if Fair Housing compliance fails.
"""

import logging
import operator
from typing import Annotated, Any, Dict, List, TypedDict

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.agent_system.dojo.evaluator import DojoEvaluator
from ghl_real_estate_ai.core.llm_client import LLMClient, TaskComplexity

logger = logging.getLogger(__name__)


class ComplianceState(TypedDict):
    """The state of the compliance-guarded generation."""

    messages: Annotated[List[Dict[str, str]], operator.add]
    last_response: str
    compliance_score: float
    audit_trail: Dict[str, Any]
    feedback: str
    iterations: int


async def generation_node(state: ComplianceState):
    """Generates a response, considering feedback from previous failed compliance checks."""
    llm = LLMClient()

    system_prompt = (
        "You are a helpful Real Estate AI Assistant. You must strictly follow Fair Housing Act (FHA) guidelines."
    )

    if state.get("feedback"):
        system_prompt += (
            f"\n\nCRITICAL COMPLIANCE FEEDBACK: {state['feedback']}\nPLEASE RE-GENERATE YOUR RESPONSE TO BE COMPLIANT."
        )

    # Prepare history for LLM
    prompt = state["messages"][-1]["content"]
    history = state["messages"][:-1]

    response = await llm.agenerate(
        prompt=prompt, system_prompt=system_prompt, history=history, complexity=TaskComplexity.COMPLEX
    )

    return {"last_response": response.content, "iterations": state.get("iterations", 0) + 1}


async def compliance_sensei_node(state: ComplianceState):
    """Evaluates the last response for compliance using DojoEvaluator."""
    evaluator = DojoEvaluator()

    # Construct a temporary history to grade the new response
    temp_history = state["messages"] + [{"role": "assistant", "content": state["last_response"]}]

    evaluation = await evaluator.grade_conversation(temp_history)

    return {
        "compliance_score": evaluation["scores"].get("compliance", 5.0),
        "audit_trail": evaluation.get("audit_trail", {}),
        "feedback": evaluation.get("feedback", ""),
    }


def should_continue(state: ComplianceState):
    """Router: Check if we need to heal the response."""
    if state["compliance_score"] >= 4.0:
        return "end"

    if state.get("iterations", 0) >= 3:
        logger.warning(f"Max compliance iterations reached. Forcing stop.")
        return "end"

    return "heal"


# Build the Graph
builder = StateGraph(ComplianceState)

builder.add_node("generator", generation_node)
builder.add_node("compliance_sensei", compliance_sensei_node)

builder.set_entry_point("generator")

builder.add_edge("generator", "compliance_sensei")

builder.add_conditional_edges("compliance_sensei", should_continue, {"heal": "generator", "end": END})

# Compile
compliance_graph = builder.compile()


async def run_guarded_generation(messages: List[Dict[str, str]]):
    """Entry point for running a compliance-guarded interaction."""
    initial_state = {
        "messages": messages,
        "last_response": "",
        "compliance_score": 5.0,
        "audit_trail": {},
        "feedback": "",
        "iterations": 0,
    }

    final_state = await compliance_graph.ainvoke(initial_state)
    return final_state
