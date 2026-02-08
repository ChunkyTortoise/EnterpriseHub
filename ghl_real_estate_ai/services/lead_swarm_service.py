"""
Lead Intelligence Swarm Service
Orchestrates a swarm of specialized agents to analyze leads from multiple dimensions.
Now with Inter-Agent Messaging and Reasoning Traces.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator


class BaseSwarmAgent:
    """Base class for specialized swarm agents."""

    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description
        self.orchestrator = get_claude_orchestrator()

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Perform analysis on the lead data."""
        raise NotImplementedError

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            # Extract JSON and Reasoning Trace
            # If Claude provides reasoning outside the JSON block, we capture it
            reasoning = ""
            if "Reasoning Trace:" in content:
                parts = content.split("Reasoning Trace:")
                reasoning = parts[1].split("```")[0].strip()

            json_content = content
            if "```json" in content:
                json_content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(json_content)
            if reasoning and "reasoning_trace" not in data:
                data["reasoning_trace"] = reasoning
            elif "reasoning_trace" not in data:
                # Fallback: use the content before the JSON block as reasoning
                data["reasoning_trace"] = content.split("```")[0].strip()

            return data
        except Exception:
            return {
                "name": self.name,
                "error": "Failed to parse structured response",
                "raw_content": content,
                "reasoning_trace": content,
            }


class FinancialAgent(BaseSwarmAgent):
    """Analyzes financial capability and budget alignment."""

    def __init__(self):
        super().__init__(
            name="Financial Analyst",
            role="financial_analyst",
            description="Analyzes income, credit hints, budget realism, and investment potential.",
        )

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You are an expert Real Estate Financial Analyst.
        Analyze the following lead data to assess their financial qualification and purchasing power.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        Focus on:
        1. Budget vs. Market Reality
        2. Financial Readiness Signals
        3. Potential Constraints
        
        OUTPUT FORMAT:
        Provide your 'Reasoning Trace' first, then a JSON block.
        The JSON must include: "qualification_status", "estimated_budget_range", "financial_signals", "risk_assessment", and "reasoning_trace".
        """
        response = await self.orchestrator.chat_query(
            query=prompt, context={"agent": self.name}, lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)


class TimelineAgent(BaseSwarmAgent):
    """Analyzes urgency and moving timeline."""

    def __init__(self):
        super().__init__(
            name="Timeline Assessor",
            role="timeline_assessor",
            description="Determines urgency, move dates, and time-sensitive triggers.",
        )

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You are a Real Estate Timeline Specialist.
        Analyze the lead's urgency and timeline.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        OUTPUT FORMAT:
        Provide your 'Reasoning Trace' first, then a JSON block with:
        "urgency_level", "target_move_date", "drivers", "recommended_pace", and "reasoning_trace".
        """
        response = await self.orchestrator.chat_query(
            query=prompt, context={"agent": self.name}, lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)


class PsychAgent(BaseSwarmAgent):
    """Analyzes personality, preferences, and decision-making style."""

    def __init__(self):
        super().__init__(
            name="Behavioral Psychologist",
            role="psych_profiler",
            description="Profiles personality type, communication style, and hidden motivators.",
        )

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You are a Behavioral Psychologist specializing in Sales.
        Profile this lead's personality and decision-making style.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        OUTPUT FORMAT:
        Provide your 'Reasoning Trace' first, then a JSON block with:
        "personality_type", "communication_style", "motivators", "interaction_tips", and "reasoning_trace".
        """
        response = await self.orchestrator.chat_query(
            query=prompt, context={"agent": self.name}, lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)


class RiskAgent(BaseSwarmAgent):
    """Identifies risks, objections, and deal-breakers."""

    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            role="risk_analyst",
            description="Identifies potential deal-killers, objections, and flight risks.",
        )

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        prompt = f"""
        You are a Deal Risk Analyst.
        Identify potential risks and objections for this lead.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        OUTPUT FORMAT:
        Provide your 'Reasoning Trace' first, then a JSON block with:
        "risk_level", "primary_objections", "competitor_risk", "mitigation_strategy", and "reasoning_trace".
        If you find a 'Deal-Killer', explicitly flag it in the JSON.
        """
        response = await self.orchestrator.chat_query(
            query=prompt, context={"agent": self.name}, lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)


class NegotiationAgent(BaseSwarmAgent):
    """Prepares counter-scripts and negotiation strategies."""

    def __init__(self):
        super().__init__(
            name="Negotiation Engine",
            role="negotiation_specialist",
            description="Preps counter-scripts and tactical negotiation rebuttals.",
        )

    async def analyze(
        self, lead_data: Dict[str, Any], messages: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        inter_agent_context = ""
        if messages:
            for msg in messages:
                if msg["from"] == "Risk Analyst" and msg.get("deal_killer"):
                    inter_agent_context = f"\n⚠️ DEAL-KILLER ALERT FROM RISK ANALYST: {msg['deal_killer']}"

        prompt = f"""
        You are an Elite Real Estate Negotiation Expert.
        Prepare a tactical negotiation playbook for this lead.
        {inter_agent_context}
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        OUTPUT FORMAT:
        Provide your 'Reasoning Trace' first, then a JSON block with:
        "negotiation_style", "counter_scripts" (List), "tactical_rebuttals" (Dict), and "reasoning_trace".
        """
        response = await self.orchestrator.chat_query(
            query=prompt, context={"agent": self.name}, lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)


class LeadSwarmService:
    """Orchestrator for the Lead Intelligence Swarm with Inter-Agent Communication."""

    def __init__(self):
        self.risk_agent = RiskAgent()
        self.specialists = [FinancialAgent(), TimelineAgent(), PsychAgent()]
        self.neg_engine = NegotiationAgent()

        from ghl_real_estate_ai.services.swarm_synthesis_service import get_swarm_synthesis_service

        self.synthesizer = get_swarm_synthesis_service()

    async def run_swarm(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs swarm with interactive messaging chain."""
        # 1. Start with Risk Assessment to find potential deal-killers
        risk_result = await self.risk_agent.analyze(lead_data)

        # 2. Parallel run of other specialists
        tasks = [agent.analyze(lead_data) for agent in self.specialists]
        other_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 3. Inter-Agent Messaging: Pass Risk signals to Negotiation Engine
        messages = []
        deal_killer = risk_result.get("deal_killer") or risk_result.get("primary_objections", [])
        if risk_result.get("risk_level") == "High" or deal_killer:
            messages.append({"from": "Risk Analyst", "to": "Negotiation Engine", "deal_killer": str(deal_killer)})

        neg_result = await self.neg_engine.analyze(lead_data, messages=messages)

        # Aggregate all results
        aggregated_results = {self.risk_agent.name: risk_result, self.neg_engine.name: neg_result}

        for agent, result in zip(self.specialists, other_results):
            if isinstance(result, Exception):
                aggregated_results[agent.name] = {"error": str(result)}
            else:
                aggregated_results[agent.name] = result

        # Synthesis
        synthesis = await self.synthesizer.synthesize(lead_data, aggregated_results)

        return {
            "specialist_findings": aggregated_results,
            "strategic_synthesis": synthesis,
            "swarm_metadata": {
                "timestamp": datetime.now().isoformat(),
                "agent_count": len(self.specialists) + 3,
                "inter_agent_messages": messages,
                "lead_id": lead_data.get("lead_id", "unknown"),
            },
        }


# Singleton
_lead_swarm_service = None


def get_lead_swarm_service() -> LeadSwarmService:
    global _lead_swarm_service
    if _lead_swarm_service is None:
        _lead_swarm_service = LeadSwarmService()
    return _lead_swarm_service
