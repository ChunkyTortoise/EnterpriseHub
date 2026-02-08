"""
Sentiment Drift Engine - AI-Powered Cold Lead Recovery
Analyzes conversation sentiment over time to detect declining engagement and trigger re-engagement.
"""

import json
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, LLMResponse, TaskComplexity
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


class SentimentDriftEngine:
    """
    Analyzes sentiment trends in conversations to identify at-risk leads.

    Pillar 1: NLP & Behavioral Intelligence
    Feature #1: Sentiment Drift Detection + Smart Re-Engagement
    """

    def __init__(self, llm_client: Optional[LLMClient] = None):
        # Use Claude for nuanced sentiment analysis
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        self.sentiment_window = 3  # Analyze the last 3 messages vs. the first 3
        self.drift_threshold = -0.4  # Alert if sentiment drops by more than 0.4

    async def analyze_conversation_drift(
        self, messages: List[Dict[str, str]], lead_id: str, tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze rolling sentiment across conversation to detect drift.

        Args:
            messages: List of conversation messages (role, content)
            lead_id: The ID of the lead
            tenant_id: Optional tenant ID for multi-tenancy

        Returns:
            Drift analysis result including alert status and recommended actions.
        """
        if len(messages) < 4:
            # Not enough messages to detect meaningful drift
            return {"alert": "INSUFFICIENT_DATA", "drift_score": 0.0}

        # Window 1: First 2-3 responses (baseline)
        early_msgs = messages[: self.sentiment_window + 1]  # Include some assistant context if needed
        early_sentiment = await self._analyze_sentiment_batch(early_msgs, tenant_id)

        # Window 2: Last 2-3 responses (recent)
        recent_msgs = messages[-self.sentiment_window :]
        recent_sentiment = await self._analyze_sentiment_batch(recent_msgs, tenant_id)

        # Drift calculation
        drift = recent_sentiment - early_sentiment

        logger.info(
            f"Sentiment drift for lead {lead_id}: {drift:.2f} (Early: {early_sentiment:.2f}, Recent: {recent_sentiment:.2f})"
        )

        if drift < self.drift_threshold:
            # Detect potential objections
            objection_hint = await self._detect_objections(recent_msgs, tenant_id)

            return {
                "alert": "COLD_LEAD",
                "drift_score": drift,
                "early_sentiment": early_sentiment,
                "recent_sentiment": recent_sentiment,
                "recommended_action": "re_engage",
                "objection_hint": objection_hint,
                "confidence": min(1.0, abs(drift) / 1.0),
            }

        return {
            "alert": "OK",
            "drift_score": drift,
            "early_sentiment": early_sentiment,
            "recent_sentiment": recent_sentiment,
        }

    async def _analyze_sentiment_batch(self, messages: List[Dict[str, str]], tenant_id: Optional[str] = None) -> float:
        """Use Sonnet for nuanced sentiment analysis."""
        prompt = f"""
        Analyze the overall sentiment of the human (user) in these messages on a scale from -1.0 (very negative/frustrated) to +1.0 (very positive/enthusiastic).
        Focus on engagement level, clarity, and willingness to cooperate.
        
        Conversation snippet:
        {json.dumps(messages, indent=2)}
        
        Return ONLY a JSON object with the score:
        {{"sentiment_score": float, "reasoning": "short string"}}
        """

        try:
            # Route to Sonnet for sentiment analysis (Routine/Complex task)
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are a real estate psychology expert analyzing lead sentiment.",
                complexity=TaskComplexity.COMPLEX,
                tenant_id=tenant_id,
                max_tokens=100,
                temperature=0.0,
            )

            # Extract score from JSON
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()

            data = json.loads(content)
            return float(data.get("sentiment_score", 0.0))
        except Exception as e:
            logger.error(f"Error in sentiment analysis: {e}")
            return 0.0

    async def _detect_objections(self, messages: List[Dict[str, str]], tenant_id: Optional[str] = None) -> str:
        """Detect specific objections from recent messages."""
        prompt = f"""
        Identify the primary concern or objection in these messages from a real estate lead.
        
        Messages:
        {json.dumps(messages, indent=2)}
        
        Return a short, 3-5 word summary of the main objection (e.g., "Price too high", "Bad timing", "Uncertain about market").
        If no clear objection, return "Vague disengagement".
        """

        try:
            response = await self.llm.agenerate(
                prompt=prompt, complexity=TaskComplexity.ROUTINE, tenant_id=tenant_id, max_tokens=50
            )
            return response.content.strip()
        except Exception:
            return "Unknown concern"

    def get_reengagement_message(self, lead_name: str, objection: str) -> str:
        """Generate a personalized re-engagement SMS."""
        if "Vague" in objection or "Unknown" in objection:
            return f"Hey {lead_name}, I noticed we hit a pause on our discussion. Just wanted to see if you had any other questions about the process? I'm here to help whenever you're ready."

        return f"Hey {lead_name}, I noticed we hit a pause. I sensed you might be concerned about {objection.lower()}. If that's the case, I'd love to share some data that might clarify things. Would you like to chat briefly?"
