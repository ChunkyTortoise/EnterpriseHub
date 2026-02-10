"""
Claude Intent Detector - Deep Behavioral Intent Analysis
Provides high-fidelity intent detection using Claude's conversation understanding.
"""

import json
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.services.analytics_service import AnalyticsService
from ghl_real_estate_ai.services.claude_orchestrator import ClaudeRequest, ClaudeTaskType, get_claude_orchestrator


class ClaudeIntentDetector:
    """
    Claude-powered intent analysis for lead intelligence.

    Extracts structured signals:
    - Financial Readiness (0-1)
    - Timeline Urgency (0-1)
    - Decision Authority (0-1)
    - Emotional Investment (0-1)
    - Hidden Concerns
    - Lifestyle Indicators
    """

    def __init__(self):
        self._orchestrator = None
        self.analytics = AnalyticsService()

    @property
    def orchestrator(self):
        if self._orchestrator is None:
            self._orchestrator = get_claude_orchestrator()
        return self._orchestrator

    async def analyze_property_intent(
        self, conversation_history: List[Dict[str, str]], lead_profile: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Deep intent analysis using Claude's conversation understanding.
        """
        location_id = lead_profile.get("location_id", "unknown") if lead_profile else "unknown"
        lead_id = lead_profile.get("lead_id", "unknown") if lead_profile else "unknown"

        prompt = f"""
        As a real estate psychology expert, analyze this conversation for buying intent:

        CONVERSATION HISTORY:
        {json.dumps(conversation_history, indent=2)}

        LEAD PROFILE:
        {json.dumps(lead_profile, indent=2) if lead_profile else "N/A"}

        Extract structured insights in JSON format:
        1. financial_readiness: float (0-1)
        2. timeline_urgency: float (0-1)
        3. decision_authority: float (0-1)
        4. emotional_investment: float (0-1)
        5. hidden_concerns: List[str]
        6. lifestyle_indicators: Dict[str, float]
        7. intent_summary: string
        8. next_step_recommendation: string

        Return JSON only.
        """

        try:
            request = ClaudeRequest(
                task_type=ClaudeTaskType.BEHAVIORAL_INSIGHT,
                context={"task": "intent_detection"},
                prompt=prompt,
                temperature=0.3,
            )

            response = await self.orchestrator.process_request(request)

            # Record usage
            await self.analytics.track_llm_usage(
                location_id=location_id,
                model=response.model or "claude-3-5-sonnet",
                provider=response.provider or "claude",
                input_tokens=response.input_tokens or 0,
                output_tokens=response.output_tokens or 0,
                cached=False,
                contact_id=lead_id,
            )

            return self._parse_json_response(response.content)
        except Exception as e:
            return {"error": str(e), "financial_readiness": 0.5, "timeline_urgency": 0.5}

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Safely extracts and parses JSON from Claude's response."""
        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            return json.loads(content)
        except (json.JSONDecodeError, IndexError):
            return {}


# Singleton instance
_intent_detector_instance = None


def get_intent_detector() -> ClaudeIntentDetector:
    global _intent_detector_instance
    if _intent_detector_instance is None:
        _intent_detector_instance = ClaudeIntentDetector()
    return _intent_detector_instance
