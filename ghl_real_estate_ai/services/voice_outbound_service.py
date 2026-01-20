"""
Voice AI Outbound Service - Bridge to Vapi.ai / Retell
Prepares "Seller Psychology" payloads for outbound Voice AI calls.
"""
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from ghl_real_estate_ai.ghl_utils.logger import get_logger
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator, ClaudeTaskType, ClaudeRequest
from ghl_real_estate_ai.services.seller_psychology_analyzer import get_seller_psychology_analyzer

logger = get_logger(__name__)

class VoiceOutboundService:
    """
    Orchestrates outbound voice AI calls by preparing psychologically-optimized payloads.
    """

    def __init__(self):
        self.orchestrator = get_claude_orchestrator()
        self.psychology_analyzer = get_seller_psychology_analyzer()

    async def prepare_vapi_payload(self, lead_id: str, lead_data: Dict[str, Any], property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare a comprehensive payload for Vapi.ai.
        Includes:
        - Call Script (psychologically optimized)
        - Lead Emotional State
        - Predicted Objections
        - Market Context
        """
        logger.info(f"Preparing Voice AI payload for lead {lead_id}")

        # 1. Analyze seller psychology
        psychology = await self.psychology_analyzer.analyze_seller_psychology(
            property_id=property_data.get("id", "unknown"),
            listing_history=property_data.get("history", {}),
            communication_data=lead_data.get("conversation_history", [])
        )

        # 2. Generate optimized script and objection handlers using Claude
        prompt = f"""
        As a world-class real estate listing agent, prepare a Voice AI call script payload.
        
        LEAD PROFILE:
        {json.dumps(lead_data, indent=2)}
        
        SELLER PSYCHOLOGY:
        - Motivation: {psychology.motivation_type}
        - Urgency: {psychology.urgency_level}
        - Flexibility: {psychology.flexibility_score}/100
        
        PROPERTY DATA:
        {json.dumps(property_data, indent=2)}
        
        Provide a JSON payload for Vapi.ai containing:
        1. system_prompt: The core persona and instructions for the Voice AI.
        2. first_message: The opening line of the call.
        3. knowledge_base: Key facts about the property and market.
        4. emotional_state: Analysis of lead's current mood/attitude.
        5. predicted_objections: List of likely objections and how to handle them.
        """

        request = ClaudeRequest(
            task_type=ClaudeTaskType.SCRIPT_GENERATION,
            context={"lead_id": lead_id, "mode": "voice_outbound"},
            prompt=prompt,
            temperature=0.5
        )

        response = await self.orchestrator.process_request(request)
        
        try:
            # Parse JSON from Claude's response
            import re
            json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
            if json_match:
                payload_data = json.loads(json_match.group())
            else:
                payload_data = {"error": "Could not parse Claude response"}
        except Exception as e:
            logger.error(f"Failed to parse Voice AI payload: {e}")
            payload_data = {"error": str(e)}

        return {
            "lead_id": lead_id,
            "vapi_config": {
                "model": "gpt-4-turbo", # Vapi default or configured
                "voice": "jorge-custom-voice",
                "system_prompt": payload_data.get("system_prompt", "You are a professional real estate assistant calling on behalf of Jorge."),
                "first_message": payload_data.get("first_message", f"Hi {lead_data.get('first_name', '')}, it's Jorge's office calling about your property."),
            },
            "intelligence": {
                "emotional_state": payload_data.get("emotional_state", "Unknown"),
                "predicted_objections": payload_data.get("predicted_objections", []),
                "psychology": {
                    "motivation": psychology.motivation_type,
                    "urgency": psychology.urgency_level.value
                }
            },
            "timestamp": datetime.now().isoformat()
        }

# Singleton instance
_voice_outbound_service = None

def get_voice_outbound_service() -> VoiceOutboundService:
    global _voice_outbound_service
    if _voice_outbound_service is None:
        _voice_outbound_service = VoiceOutboundService()
    return _voice_outbound_service
