"""
Claude Agent Service - AI-Powered Agent Assistant for Lead Intelligence

Provides conversational AI interface for real estate agents to interact with
lead data, get insights, and receive recommendations through Claude.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

from anthropic import AsyncAnthropic

from ..ghl_utils.config import settings
from .lead_intelligence_integration import analyze_message_intelligence, get_lead_analytics
from .lead_scorer import LeadScorer

logger = logging.getLogger(__name__)


@dataclass
class AgentQuery:
    """Structure for agent queries about leads"""
    agent_id: str
    query: str
    lead_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    timestamp: datetime = datetime.now()


@dataclass
class ClaudeResponse:
    """Structure for Claude responses to agents"""
    response: str
    insights: List[str]
    recommendations: List[str]
    confidence: float
    follow_up_questions: List[str]
    timestamp: datetime = datetime.now()


class ClaudeAgentService:
    """
    Claude-powered conversational AI service for real estate agents.

    Enables natural language interaction with lead intelligence system,
    providing insights, recommendations, and property matching through AI.
    """

    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.anthropic_api_key)
        self.lead_scorer = LeadScorer()
        self.conversation_history: Dict[str, List[Dict]] = {}
        self.agent_context: Dict[str, Dict] = {}

    async def chat_with_agent(
        self,
        agent_id: str,
        query: str,
        lead_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> ClaudeResponse:
        """
        Main conversation interface for agents to chat with Claude about leads.

        Args:
            agent_id: Unique identifier for the agent
            query: Natural language query from the agent
            lead_id: Optional specific lead ID to focus on
            context: Additional context (property data, market info, etc.)

        Returns:
            ClaudeResponse with AI insights and recommendations
        """
        try:
            # Initialize agent context if new
            if agent_id not in self.agent_context:
                self.agent_context[agent_id] = {
                    "name": f"Agent {agent_id}",
                    "active_leads": [],
                    "preferences": {},
                    "last_activity": datetime.now()
                }

            # Build comprehensive context for Claude
            system_prompt = await self._build_agent_system_prompt(agent_id, lead_id)
            conversation_context = await self._build_conversation_context(agent_id, lead_id, context)

            # Create messages for Claude
            messages = self._get_conversation_history(agent_id) + [
                {
                    "role": "user",
                    "content": f"Query: {query}\n\nContext: {json.dumps(conversation_context, indent=2)}"
                }
            ]

            # Call Claude API
            response = await self.client.messages.create(
                model=settings.claude_model,
                max_tokens=800,
                temperature=0.7,
                system=system_prompt,
                messages=messages[-10:]  # Keep last 10 messages for context
            )

            # Parse Claude's response and extract insights
            claude_text = response.content[0].text
            parsed_response = await self._parse_claude_response(claude_text, lead_id)

            # Store conversation history
            self._store_conversation(agent_id, query, claude_text)

            # Update agent context
            self.agent_context[agent_id]["last_activity"] = datetime.now()
            if lead_id and lead_id not in self.agent_context[agent_id]["active_leads"]:
                self.agent_context[agent_id]["active_leads"].append(lead_id)

            logger.info(f"Claude response generated for agent {agent_id}, query length: {len(query)}")
            return parsed_response

        except Exception as e:
            logger.error(f"Error in Claude agent chat: {str(e)}")
            return ClaudeResponse(
                response=f"I apologize, but I encountered an error processing your request: {str(e)}",
                insights=["Error occurred during processing"],
                recommendations=["Please try rephrasing your question"],
                confidence=0.0,
                follow_up_questions=["Would you like to try a different question?"]
            )

    async def _build_agent_system_prompt(self, agent_id: str, lead_id: Optional[str] = None) -> str:
        """Build comprehensive system prompt for Claude based on agent context"""

        base_prompt = f"""You are an AI assistant for real estate agent {agent_id}. You have access to comprehensive lead intelligence data and property information through the GHL Real Estate AI system.

Your role is to help agents:
1. Understand lead behavior, preferences, and conversion probability
2. Get insights about property matches and market opportunities
3. Receive actionable recommendations for lead nurturing and follow-up
4. Analyze conversation patterns and engagement signals
5. Identify high-priority leads and optimal timing for contact

Current date: {datetime.now().strftime('%Y-%m-%d %H:%M')}

RESPONSE FORMAT - Always structure your responses with these sections:
1. **Direct Answer**: Clear, concise response to the agent's question
2. **Key Insights**: 2-3 bullet points with specific insights about the lead/situation
3. **Recommendations**: 1-2 actionable next steps the agent should take
4. **Follow-up Questions**: 1-2 relevant questions to help the agent dig deeper

LEAD SCORING CONTEXT:
- Hot Leads (80-100): High engagement, clear intent, qualified budget
- Warm Leads (50-79): Some interest, needs nurturing, potential qualified
- Cold Leads (0-49): Early stage, requires education and relationship building

Always provide specific, actionable advice based on data rather than generic suggestions."""

        # Add lead-specific context if provided
        if lead_id:
            try:
                lead_analytics = await get_lead_analytics("default_tenant")
                if lead_analytics and not lead_analytics.get("error"):
                    base_prompt += f"\n\nCURRENT LEAD FOCUS: {lead_id}\nAnalytics available: {json.dumps(lead_analytics, indent=2)}"
            except:
                pass

        return base_prompt

    async def _build_conversation_context(
        self,
        agent_id: str,
        lead_id: Optional[str] = None,
        additional_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build comprehensive context for the conversation"""

        context = {
            "agent_info": self.agent_context.get(agent_id, {}),
            "timestamp": datetime.now().isoformat(),
            "system_capabilities": [
                "Lead scoring and qualification analysis",
                "Conversation sentiment and intent detection",
                "Property matching recommendations",
                "Follow-up timing optimization",
                "Market insights and competitive analysis"
            ]
        }

        # Add lead-specific data if available
        if lead_id:
            try:
                # Get lead intelligence data
                lead_intelligence = await analyze_message_intelligence(
                    lead_id, "default_tenant", "Context request for agent conversation"
                )
                if lead_intelligence and not lead_intelligence.get("error"):
                    context["lead_data"] = lead_intelligence

                # Add lead scoring
                score = await self.lead_scorer.score_lead_comprehensive(lead_id)
                context["lead_score"] = score

            except Exception as e:
                logger.warning(f"Could not fetch lead context: {str(e)}")

        # Add any additional context provided
        if additional_context:
            context["additional_info"] = additional_context

        return context

    def _get_conversation_history(self, agent_id: str) -> List[Dict]:
        """Get recent conversation history for context"""
        if agent_id not in self.conversation_history:
            self.conversation_history[agent_id] = []

        # Return last 8 messages for context (4 back-and-forth exchanges)
        return self.conversation_history[agent_id][-8:]

    def _store_conversation(self, agent_id: str, query: str, response: str):
        """Store conversation for context and history"""
        if agent_id not in self.conversation_history:
            self.conversation_history[agent_id] = []

        self.conversation_history[agent_id].extend([
            {"role": "user", "content": query},
            {"role": "assistant", "content": response}
        ])

        # Keep only last 20 messages to prevent memory bloat
        self.conversation_history[agent_id] = self.conversation_history[agent_id][-20:]

    async def _parse_claude_response(self, claude_text: str, lead_id: Optional[str] = None) -> ClaudeResponse:
        """Parse Claude's response and extract structured insights"""

        # Extract sections from Claude's response
        insights = []
        recommendations = []
        follow_up_questions = []

        try:
            # Simple parsing - look for bullet points and sections
            lines = claude_text.split('\n')
            current_section = None

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                # Detect sections
                if "**Key Insights" in line or "insights:" in line.lower():
                    current_section = "insights"
                    continue
                elif "**Recommendations" in line or "recommendations:" in line.lower():
                    current_section = "recommendations"
                    continue
                elif "**Follow-up" in line or "follow-up" in line.lower():
                    current_section = "follow_up"
                    continue

                # Extract content based on current section
                if current_section == "insights" and (line.startswith('-') or line.startswith('•')):
                    insights.append(line.lstrip('-• '))
                elif current_section == "recommendations" and (line.startswith('-') or line.startswith('•')):
                    recommendations.append(line.lstrip('-• '))
                elif current_section == "follow_up" and (line.startswith('-') or line.startswith('•')):
                    follow_up_questions.append(line.lstrip('-• '))

            # Fallback extraction if structured parsing fails
            if not insights:
                # Look for any bullet points as insights
                for line in lines:
                    if (line.strip().startswith('•') or line.strip().startswith('-')) and len(line.strip()) > 10:
                        insights.append(line.strip().lstrip('-• '))

        except Exception as e:
            logger.warning(f"Error parsing Claude response: {str(e)}")

        # Ensure we have some default content
        if not insights:
            insights = ["Analysis completed - see response for details"]
        if not recommendations:
            recommendations = ["Review lead data and consider appropriate follow-up"]
        if not follow_up_questions:
            follow_up_questions = ["What specific aspect would you like to explore further?"]

        # Calculate confidence based on response quality
        confidence = min(0.9, len(claude_text) / 500)  # Simple heuristic

        return ClaudeResponse(
            response=claude_text,
            insights=insights[:3],  # Limit to top 3
            recommendations=recommendations[:2],  # Limit to top 2
            confidence=confidence,
            follow_up_questions=follow_up_questions[:2]  # Limit to 2
        )

    async def get_lead_insights(self, lead_id: str, agent_id: str) -> Dict[str, Any]:
        """Get comprehensive AI insights for a specific lead"""

        query = f"Give me a comprehensive analysis of lead {lead_id}. What are the key insights about their behavior, preferences, and conversion potential? What should I prioritize in my next interaction with them?"

        response = await self.chat_with_agent(agent_id, query, lead_id)

        return {
            "lead_id": lead_id,
            "agent_id": agent_id,
            "insights": response.insights,
            "recommendations": response.recommendations,
            "confidence": response.confidence,
            "timestamp": response.timestamp.isoformat(),
            "ai_summary": response.response[:200] + "..." if len(response.response) > 200 else response.response
        }

    async def suggest_follow_up_actions(self, lead_id: str, agent_id: str) -> List[Dict[str, Any]]:
        """Get AI-suggested follow-up actions for a lead"""

        query = f"Based on lead {lead_id}'s current status and behavior, what are the top 3 follow-up actions I should take? Consider timing, channel, and messaging approach."

        response = await self.chat_with_agent(agent_id, query, lead_id)

        actions = []
        for i, recommendation in enumerate(response.recommendations):
            actions.append({
                "id": f"action_{i+1}",
                "action": recommendation,
                "priority": "high" if i == 0 else "medium",
                "suggested_timing": "within 24 hours" if i == 0 else "within 3 days",
                "confidence": response.confidence
            })

        return actions

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics about agent's usage of the Claude service"""

        context = self.agent_context.get(agent_id, {})
        history = self.conversation_history.get(agent_id, [])

        return {
            "agent_id": agent_id,
            "total_conversations": len(history) // 2,  # Divide by 2 for user/assistant pairs
            "active_leads": len(context.get("active_leads", [])),
            "last_activity": context.get("last_activity", datetime.now()).isoformat(),
            "avg_session_length": len(history) / max(1, len(context.get("active_leads", []))),
            "status": "active" if context.get("last_activity", datetime.min) > datetime.now() - timedelta(hours=24) else "inactive"
        }


# Global instance for easy access
claude_agent_service = ClaudeAgentService()


async def chat_with_claude(agent_id: str, query: str, lead_id: Optional[str] = None) -> ClaudeResponse:
    """Convenience function for agents to chat with Claude"""
    return await claude_agent_service.chat_with_agent(agent_id, query, lead_id)


async def get_claude_lead_insights(lead_id: str, agent_id: str) -> Dict[str, Any]:
    """Convenience function to get lead insights"""
    return await claude_agent_service.get_lead_insights(lead_id, agent_id)


async def get_claude_follow_up_actions(lead_id: str, agent_id: str) -> List[Dict[str, Any]]:
    """Convenience function to get follow-up action suggestions"""
    return await claude_agent_service.suggest_follow_up_actions(lead_id, agent_id)