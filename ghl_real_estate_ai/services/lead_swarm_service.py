"""
Lead Intelligence Swarm Service
Orchestrates a swarm of specialized agents to analyze leads from multiple dimensions.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from services.claude_orchestrator import get_claude_orchestrator

class BaseSwarmAgent:
    """Base class for specialized swarm agents."""
    def __init__(self, name: str, role: str, description: str):
        self.name = name
        self.role = role
        self.description = description
        self.orchestrator = get_claude_orchestrator()

    async def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform analysis on the lead data."""
        raise NotImplementedError

class FinancialAgent(BaseSwarmAgent):
    """Analyzes financial capability and budget alignment."""
    def __init__(self):
        super().__init__(
            name="Financial Analyst",
            role="financial_analyst",
            description="Analyzes income, credit hints, budget realism, and investment potential."
        )

    async def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are an expert Real Estate Financial Analyst.
        Analyze the following lead data to assess their financial qualification and purchasing power.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        Focus on:
        1. Budget vs. Market Reality
        2. Financial Readiness Signals (pre-approval mentioned, cash buyer, investor)
        3. Potential Constraints
        
        Return a JSON object with keys:
        - "qualification_status" (High/Medium/Low)
        - "estimated_budget_range"
        - "financial_signals" (List of strings)
        - "risk_assessment"
        """
        response = await self.orchestrator.chat_query(
            query=prompt,
            context={"agent": self.name},
            lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        # Simple heuristic parser if JSON parsing fails, but Claude usually returns valid JSON if prompted.
        # For robustness, we'd wrap this in try-catch and json.loads
        try:
            # Attempt to extract JSON if it's wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {
                "qualification_status": "Unknown",
                "raw_analysis": content,
                "error": "Failed to parse structured response"
            }

class TimelineAgent(BaseSwarmAgent):
    """Analyzes urgency and moving timeline."""
    def __init__(self):
        super().__init__(
            name="Timeline Assessor",
            role="timeline_assessor",
            description="Determines urgency, move dates, and time-sensitive triggers."
        )

    async def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a Real Estate Timeline Specialist.
        Analyze the lead's urgency and timeline.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        Identify:
        1. Target Move Date
        2. Urgency Level (Immediate/Soon/Future/Browsing)
        3. External Triggers (Lease ending, school start, job relocation)
        
        Return a JSON object with keys:
        - "urgency_level"
        - "target_move_date"
        - "drivers" (List of urgency drivers)
        - "recommended_pace" (Aggressive/Steady/Nurture)
        """
        response = await self.orchestrator.chat_query(
            query=prompt,
            context={"agent": self.name},
            lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)
    
    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"urgency_level": "Unknown", "raw_analysis": content}


class PsychAgent(BaseSwarmAgent):
    """Analyzes personality, preferences, and decision-making style."""
    def __init__(self):
        super().__init__(
            name="Behavioral Psychologist",
            role="psych_profiler",
            description="Profiles personality type, communication style, and hidden motivators."
        )

    async def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a Behavioral Psychologist specializing in Sales.
        Profile this lead's personality and decision-making style.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        Determine:
        1. DISC Profile (approximate)
        2. Communication Preference (Direct/Data-Heavy/Friendly/Visual)
        3. Key Motivators (Status, Safety, ROI, Comfort)
        
        Return a JSON object with keys:
        - "personality_type"
        - "communication_style"
        - "motivators" (List)
        - "interaction_tips" (List)
        """
        response = await self.orchestrator.chat_query(
            query=prompt,
            context={"agent": self.name},
            lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"personality_type": "Unknown", "raw_analysis": content}

class RiskAgent(BaseSwarmAgent):
    """Identifies risks, objections, and deal-breakers."""
    def __init__(self):
        super().__init__(
            name="Risk Analyst",
            role="risk_analyst",
            description="Identifies potential deal-killers, objections, and flight risks."
        )

    async def analyze(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a Deal Risk Analyst.
        Identify potential risks and objections for this lead.
        
        Lead Data: {json.dumps(lead_data, default=str)}
        
        Look for:
        1. Competitor mentions
        2. Unrealistic expectations
        3. Financial red flags
        4. Indecision signals
        
        Return a JSON object with keys:
        - "risk_level" (High/Medium/Low)
        - "primary_objections" (List)
        - "competitor_risk" (Boolean)
        - "mitigation_strategy"
        """
        response = await self.orchestrator.chat_query(
            query=prompt,
            context={"agent": self.name},
            lead_id=lead_data.get("lead_id", "unknown")
        )
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"risk_level": "Unknown", "raw_analysis": content}

class LeadSwarmService:
    """Orchestrator for the Lead Intelligence Swarm."""
    def __init__(self):
        self.agents = [
            FinancialAgent(),
            TimelineAgent(),
            PsychAgent(),
            RiskAgent()
        ]

    async def run_swarm(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs all agents in parallel and aggregates results."""
        tasks = [agent.analyze(lead_data) for agent in self.agents]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        aggregated_results = {}
        for agent, result in zip(self.agents, results):
            if isinstance(result, Exception):
                aggregated_results[agent.name] = {"error": str(result)}
            else:
                aggregated_results[agent.name] = result
        
        return aggregated_results

# Singleton
_lead_swarm_service = None

def get_lead_swarm_service() -> LeadSwarmService:
    global _lead_swarm_service
    if _lead_swarm_service is None:
        _lead_swarm_service = LeadSwarmService()
    return _lead_swarm_service
