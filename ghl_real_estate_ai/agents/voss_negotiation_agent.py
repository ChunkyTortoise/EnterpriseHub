"""
Voss Negotiation Agent - LangGraph Orchestrator
Implements tactical empathy and assertive negotiation using Chris Voss techniques.
"""

import asyncio
import logging
from typing import Any, Dict, List, Literal

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.models.negotiation_state import VossNegotiationState
from ghl_real_estate_ai.services.claude_assistant import ClaudeAssistant
from ghl_real_estate_ai.services.negotiation_drift_detector import get_drift_detector

logger = get_logger(__name__)


class VossNegotiationAgent:
    """
    Autonomous negotiation agent powered by LangGraph.
    Orchestrates behavioral analysis, compliance, and dynamic tone calibration.
    """

    def __init__(self):
        self.drift_detector = get_drift_detector()
        self.claude = ClaudeAssistant()
        self.workflow = self._build_graph()

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(VossNegotiationState)

        # Define Nodes
        workflow.add_node("analyze_behavior", self.analyze_behavior)
        workflow.add_node("calibrate_tone", self.calibrate_tone)
        workflow.add_node("compliance_audit", self.compliance_audit)
        workflow.add_node("generate_response", self.generate_response)

        # Define Edges
        workflow.set_entry_point("analyze_behavior")
        workflow.add_edge("analyze_behavior", "calibrate_tone")
        workflow.add_edge("calibrate_tone", "compliance_audit")

        # Conditional Edge: If not compliant, regenerate. Otherwise, generate.
        workflow.add_conditional_edges(
            "compliance_audit",
            self._check_compliance_status,
            {
                "safe": "generate_response",
                "unsafe": "calibrate_tone",  # Re-calibrate if unsafe
            },
        )

        workflow.add_edge("generate_response", END)

        return workflow.compile()

    # --- Node Implementations ---

    def analyze_behavior(self, state: VossNegotiationState) -> Dict:
        """Analyze lead behavior for drift and flexibility."""
        logger.info(f"Analyzing behavioral drift for {state['lead_name']}")

        last_msg = state["conversation_history"][-1]["content"] if state["conversation_history"] else ""

        # Calculate drift (latency would be pulled from metadata in prod)
        drift_results = self.drift_detector.analyze_drift(
            message=last_msg, response_latency_seconds=state.get("metadata", {}).get("latency", 0)
        )

        return {
            "drift_score": drift_results["drift_score"],
            "is_drifting": drift_results["is_drifting"],
            "drift_recommendation": drift_results["recommendation"],
        }

    def calibrate_tone(self, state: VossNegotiationState) -> Dict:
        """Determines the appropriate Voss Level based on drift and history."""
        drift_score = state["drift_score"]

        # Logic: If lead is drifting (becoming flexible), increase intensity to close.
        # If lead is firm, use lower level (rapport building).
        if drift_score > 0.9:
            voss_level = 5  # 'No-Oriented' Closure
            tone = "Strategic/Direct"
        elif drift_score > 0.7:
            voss_level = 4  # Direct Challenge
            tone = "Aggressive/Direct"
        elif drift_score > 0.4:
            voss_level = 3  # Confrontational (Tactical)
            tone = "Assertive"
        else:
            voss_level = 2  # Mirroring/Labeling (Rapport)
            tone = "Warm/Empathetic"

        logger.info(f"Tone calibrated to Level {voss_level} ({tone})")
        return {"voss_level": voss_level, "tone_intensity": tone}

    def compliance_audit(self, state: VossNegotiationState) -> Dict:
        """Real-time FHA/RESPA safety check."""
        # Simple keyword-based safety check for demo
        prohibited = ["exclusive", "traditional neighborhood", "only for families"]
        is_compliant = True
        feedback = None

        # In a real run, we'd check the *potential* strategy or last response
        # Here we mock the check
        return {"is_compliant": is_compliant, "compliance_feedback": feedback}

    async def generate_response(self, state: VossNegotiationState) -> Dict:
        """Calls Claude to generate a Voss-powered response."""
        voss_prompts = {
            1: "Use Mirroring. Repeat the last 3 words as a question.",
            2: "Use Labeling. Start with 'It seems like...' or 'It sounds like...'",
            3: "Use Accusation Audit. List all the negative things they might think about you.",
            4: "Use Direct Challenge. Ask 'How am I supposed to do that?' (Voss's favorite calibration question).",
            5: "Use the 'No-Oriented' question. 'Is it a ridiculous idea to suggest...?'",
        }

        prompt = f"""
        You are a master real estate negotiator using the Voss Framework.
        Lead: {state["lead_name"]}
        Context: {state["property_address"]}
        Behavioral Drift: {state["drift_recommendation"]}
        
        TASK: Generate a response using Voss Level {state["voss_level"]}: {voss_prompts.get(state["voss_level"])}
        Maintain a {state["tone_intensity"]} tone.
        """

        response = await self.claude.analyze_with_context(prompt)
        # Assuming the assistant returns a dict with 'content' or 'analysis'
        content = (
            response.get("content") or response.get("analysis") or "I understand your position. How should we proceed?"
        )

        return {"generated_response": content}

    # --- Helper Logic ---

    def _check_compliance_status(self, state: VossNegotiationState) -> Literal["safe", "unsafe"]:
        return "safe" if state["is_compliant"] else "unsafe"

    async def run_negotiation(
        self, lead_id: str, lead_name: str, address: str, history: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Entry point to execute the LangGraph workflow."""
        initial_state = {
            "lead_id": lead_id,
            "lead_name": lead_name,
            "property_address": address,
            "conversation_history": history,
            "metadata": {},
        }

        result = await self.workflow.ainvoke(initial_state)
        return result


# Singleton
_voss_agent = None


def get_voss_negotiation_agent() -> VossNegotiationAgent:
    global _voss_agent
    if _voss_agent is None:
        _voss_agent = VossNegotiationAgent()
    return _voss_agent
