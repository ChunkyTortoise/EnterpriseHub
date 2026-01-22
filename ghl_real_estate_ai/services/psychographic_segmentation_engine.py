"""
Psychographic Segmentation Engine - AI-Powered Persona Detection
Identifies buyer personas and adapts bot tone dynamically.
"""
import json
import logging
from typing import Dict, List, Any, Optional

from ghl_real_estate_ai.core.llm_client import LLMClient, LLMProvider, TaskComplexity
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class PsychographicPersona:
    INVESTOR = "investor"
    OWNER_OCCUPANT = "owner_occupant"
    FIRST_TIME_BUYER = "first_time_buyer"
    MOTIVATED_SELLER = "motivated_seller"
    FLIPPER = "flipper"
    LUXURY_SEEKER = "luxury_seeker"
    LOSS_AVERSION = "loss_aversion"

class PsychographicSegmentationEngine:
    """
    Detects lead personas based on conversation patterns and adapts bot tone.
    
    Pillar 1: NLP & Behavioral Intelligence
    Feature #5: Psychographic Buyer Segmentation + Dynamic Tone Adaptation
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm = llm_client or LLMClient(provider=LLMProvider.CLAUDE)
        
    async def detect_persona(
        self, 
        messages: List[Dict[str, str]], 
        lead_context: Dict[str, Any],
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze conversation to detect psychographic persona.
        
        Args:
            messages: Conversation history
            lead_context: Metadata about the lead
            tenant_id: Optional tenant ID
            
        Returns:
            Detected persona and confidence scores.
        """
        prompt = f"""
        Analyze the following real estate conversation and lead data to identify the primary psychographic persona.
        
        CONVERSATION:
        {json.dumps(messages, indent=2)}
        
        LEAD DATA:
        {json.dumps(lead_context, indent=2)}
        
        PERSONA DEFINITIONS:
        - Investor: ROI-driven, data-focused, looks for yield/cap rates.
        - Owner-Occupant: Emotional, lifestyle-focused, community and family importance.
        - First-Time Buyer: Needs guidance, cautious, budget-conscious, educational tone.
        - Motivated Seller: Urgency, looking for quick close, distressed or relocating.
        - Flipper: Looking for "fixer-uppers", speed and price flexibility.
        - Luxury Seeker: High-end finishes, exclusivity, prestige, high budget.
        - Loss Aversion: Primarily motivated by avoiding a loss rather than making a gain. Fear of market crash, rising rates, or "missing the window".
        
        Return ONLY a JSON object:
        {{
            "primary_persona": "one of the above keys",
            "confidence": 0.0 to 1.0,
            "secondary_persona": "optional secondary match",
            "key_traits": ["trait1", "trait2"],
            "recommended_tone": "detailed description of how to talk to this person"
        }}
        """
        
        try:
            # Route to Sonnet for persona detection
            response = await self.llm.agenerate(
                prompt=prompt,
                system_prompt="You are an AI Behavioral Psychologist specializing in real estate transactions.",
                complexity=TaskComplexity.COMPLEX,
                tenant_id=tenant_id,
                max_tokens=300,
                temperature=0.0
            )
            
            content = response.content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error in persona detection: {e}")
            return {"primary_persona": "unknown", "confidence": 0.0}

    def get_system_prompt_override(self, persona_data: Dict[str, Any]) -> str:
        """Get a system prompt snippet to adapt the bot's tone."""
        persona = persona_data.get("primary_persona")
        tone_desc = persona_data.get("recommended_tone", "Professional and helpful")
        
        overrides = {
            PsychographicPersona.INVESTOR: f"Tone: Analytical and ROI-driven. Focus on data, comps, and investment potential. {tone_desc}",
            PsychographicPersona.OWNER_OCCUPANT: f"Tone: Warm and lifestyle-focused. Emphasize community, schools, and living experience. {tone_desc}",
            PsychographicPersona.FIRST_TIME_BUYER: f"Tone: Educational and reassuring. Explain the process clearly and address common anxieties. {tone_desc}",
            PsychographicPersona.MOTIVATED_SELLER: f"Tone: Direct and solution-oriented. Focus on speed, ease of transaction, and certain outcomes. {tone_desc}",
            PsychographicPersona.FLIPPER: f"Tone: Fast-paced and professional. Focus on property potential, as-is conditions, and quick math. {tone_desc}",
            PsychographicPersona.LUXURY_SEEKER: f"Tone: Sophisticated and exclusive. Emphasize prestige, architectural details, and high-end finishes. {tone_desc}",
            PsychographicPersona.LOSS_AVERSION: f"Tone: Urgent and risk-focused. Emphasize the 'Cost of Waiting' and the risk of missing the current market window. {tone_desc}"
        }
        
        return overrides.get(persona, f"Tone: {tone_desc}")
