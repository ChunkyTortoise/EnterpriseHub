"""
Claude Executive Intelligence Service
Orchestrates a swarm of specialized agents for executive-level business intelligence.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict

from ghl_real_estate_ai.services.lead_swarm_service import BaseSwarmAgent


class MarketAnalystAgent(BaseSwarmAgent):
    """Analyzes market trends and competitive landscape."""

    def __init__(self):
        super().__init__(
            name="Market Analyst",
            role="market_analyst",
            description="Analyzes market trends, interest rates, and competitive positioning.",
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        market = data.get("market", "Austin, TX")
        prompt = f"""
        You are an Elite Real Estate Market Analyst.
        Analyze the following business data for the {market} market.
        
        Business Data: {json.dumps(data, default=str)}
        
        Focus on:
        1. Market Trends vs. Internal Performance
        2. Competitive Opportunities
        3. External Economic Factors (Interest rates, local developments)
        
        Return a JSON object with keys:
        - "market_sentiment" (Bullish/Neutral/Bearish)
        - "key_opportunities" (List of strings)
        - "economic_impact_score" (0-1)
        - "strategic_recommendation"
        """
        response = await self.orchestrator.chat_query(query=prompt, context={"agent": self.name, "market": market})
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"market_sentiment": "Unknown", "raw_analysis": content}


class PerformanceAnalystAgent(BaseSwarmAgent):
    """Analyzes team and system performance metrics."""

    def __init__(self):
        super().__init__(
            name="Performance Analyst",
            role="performance_analyst",
            description="Analyzes conversion rates, response times, and agent efficiency.",
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a Real Estate Operations & Performance Expert.
        Analyze the following performance metrics.
        
        Metrics: {json.dumps(data.get("metrics", {}), default=str)}
        
        Determine:
        1. Efficiency Bottlenecks
        2. Top Performing Segments
        3. ROI on AI interventions
        
        Return a JSON object with keys:
        - "performance_score" (0-100)
        - "top_wins" (List)
        - "critical_bottlenecks" (List)
        - "operational_efficiency_index" (0-1)
        """
        response = await self.orchestrator.chat_query(query=prompt, context={"agent": self.name})
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"performance_score": 0, "raw_analysis": content}


class PipelineAnalystAgent(BaseSwarmAgent):
    """Analyzes pipeline velocity and deal flow."""

    def __init__(self):
        super().__init__(
            name="Pipeline Analyst",
            role="pipeline_analyst",
            description="Analyzes lead velocity, deal sizes, and pipeline health.",
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        prompt = f"""
        You are a Pipeline Velocity Specialist.
        Analyze the current deal pipeline.
        
        Pipeline Data: {json.dumps(data.get("pipeline", {}), default=str)}
        
        Identify:
        1. Lead-to-Close Velocity
        2. Pipeline Leakage Points
        3. Revenue Forecasting Accuracy
        
        Return a JSON object with keys:
        - "pipeline_health" (Healthy/At Risk/Stagnant)
        - "forecasted_revenue_next_30d"
        - "velocity_improvement_ops" (List)
        - "risk_score" (0-1)
        """
        response = await self.orchestrator.chat_query(query=prompt, context={"agent": self.name})
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"pipeline_health": "Unknown", "raw_analysis": content}


class StrategyAnalystAgent(BaseSwarmAgent):
    """Synthesizes all insights into strategic business recommendations."""

    def __init__(self):
        super().__init__(
            name="Strategic Advisor",
            role="strategic_advisor",
            description="Synthesizes multi-dimensional insights into high-level strategy.",
        )

    async def analyze(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # This agent should ideally take results from other agents
        swarm_results = data.get("swarm_results", {})

        prompt = f"""
        You are the Chief Strategy Officer AI for a major Real Estate firm.
        Synthesize the following insights from your team of specialist agents.
        
        Specialist Insights: {json.dumps(swarm_results, default=str)}
        
        Develop:
        1. Executive Action Plan
        2. Long-term Strategic Direction
        3. High-Priority Resource Allocation
        
        Return a JSON object with keys:
        - "executive_summary"
        - "top_3_action_items" (List)
        - "strategic_horizon_view" (12-month outlook)
        - "confidence_in_strategy" (0-1)
        """
        response = await self.orchestrator.chat_query(query=prompt, context={"agent": self.name})
        return self._parse_response(response.content)

    def _parse_response(self, content: str) -> Dict[str, Any]:
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except Exception:
            return {"executive_summary": "Analysis failed", "raw_analysis": content}


class ExecutiveIntelligenceService:
    """Orchestrator for the Executive Intelligence Swarm."""

    def __init__(self):
        self.market_agent = MarketAnalystAgent()
        self.performance_agent = PerformanceAnalystAgent()
        self.pipeline_agent = PipelineAnalystAgent()
        self.strategy_agent = StrategyAnalystAgent()

    async def run_executive_swarm(self, business_data: Dict[str, Any]) -> Dict[str, Any]:
        """Runs specialized agents in parallel and then synthesizes with Strategy Agent."""

        # Phase 1: Parallel specialized analysis
        specialist_tasks = [
            self.market_agent.analyze(business_data),
            self.performance_agent.analyze(business_data),
            self.pipeline_agent.analyze(business_data),
        ]

        specialist_results = await asyncio.gather(*specialist_tasks, return_exceptions=True)

        swarm_results = {
            "Market Analysis": specialist_results[0],
            "Performance Analysis": specialist_results[1],
            "Pipeline Analysis": specialist_results[2],
        }

        # Phase 2: Strategic Synthesis
        synthesis_data = {"business_data": business_data, "swarm_results": swarm_results}

        strategy_result = await self.strategy_agent.analyze(synthesis_data)

        return {
            "specialist_insights": swarm_results,
            "strategic_advisor": strategy_result,
            "timestamp": datetime.now().isoformat(),
        }


# Singleton
_executive_intelligence_service = None


def get_executive_intelligence_service() -> ExecutiveIntelligenceService:
    global _executive_intelligence_service
    if _executive_intelligence_service is None:
        _executive_intelligence_service = ExecutiveIntelligenceService()
    return _executive_intelligence_service
