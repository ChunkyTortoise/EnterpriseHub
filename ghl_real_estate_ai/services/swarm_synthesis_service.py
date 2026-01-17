"""
Swarm Synthesis Service - Strategic Advisor Agent
Aggregates and synthesizes specialized swarm insights into a single executive action plan.
"""
import asyncio
import json
from typing import Dict, List, Any, Optional
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

class StrategicAdvisorAgent:
    """The master agent that synthesizes specialized swarm findings."""
    
    def __init__(self):
        self.orchestrator = get_claude_orchestrator()

    async def synthesize(self, lead_data: Dict[str, Any], swarm_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Takes raw swarm results and lead data, then creates a unified strategy.
        """
        prompt = f"""
        You are the Master Strategic Advisor for an Elite Real Estate Swarm.
        
        LEAD DATA:
        {json.dumps(lead_data, default=str)}
        
        SPECIALIST FINDINGS:
        {json.dumps(swarm_results, indent=2, default=str)}
        
        Your goal is to synthesize these specialized reports into a single, cohesive, 
        and high-impact executive action plan for Jorge Salas.
        
        Identify:
        1. Conflicting signals between specialists (e.g., High Urgency but Low Finance).
        2. The 'Critical Path' to conversion.
        3. A custom 'Hook' based on personality and financial goals.
        4. Immediate 24-hour tactical actions.
        
        Return a JSON object with:
        - "executive_summary" (Natural, punchy overview)
        - "top_3_strategic_priorities" (List)
        - "custom_outreach_hook" (A personalized opening line)
        - "conversion_bottleneck" (The #1 thing stopping the deal)
        - "confidence_index" (0.0-1.0)
        - "tactical_next_steps" (List of 3 immediate actions)
        """
        
        try:
            response = await self.orchestrator.chat_query(
                query=prompt,
                context={"task": "swarm_synthesis"},
                lead_id=lead_data.get("lead_id", "unknown")
            )
            return self._parse_response(response.content)
        except Exception as e:
            return {"error": str(e), "fallback_summary": "Continue manual nurture."}

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except:
            return {"raw_synthesis": content}

# Singleton
_synthesis_instance = None

def get_swarm_synthesis_service() -> StrategicAdvisorAgent:
    global _synthesis_instance
    if _synthesis_instance is None:
        _synthesis_instance = StrategicAdvisorAgent()
    return _synthesis_instance
