"""
Governance Engine (Agent G1)
Enforces Jorge's strict SMS compliance and tone rules.

Rules:
- Max 160 characters
- No emojis
- No hyphens
- Professional, Direct, Curious
"""
import re
import logging
from typing import Dict, Any, List, Optional, Union
from ghl_real_estate_ai.services.national_market_intelligence import get_national_market_intelligence

logger = logging.getLogger(__name__)

class GovernanceEngine:
    """
    Final validator for all bot responses before they reach the lead.
    Forces compliance with Jorge's specific SMS constraints and safety guardrails.
    
    G1: SMS Compliance (Length, Emojis, Hyphens)
    G2: Veracity (No Hallucinated Promises)
    G3: Tactical Professionalism (Tone & Boundaries)
    """
    
    def __init__(self):
        self.market_intel = get_national_market_intelligence()

    def enforce(self, message: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Applies all governance rules to a message.
        """
        # G2: Veracity Guardrails (Check for hallucinated yield/price promises)
        message = self._sanitize_veracity(message, context)
        
        # G3: Tactical Professionalism (Tone check)
        message = self._enforce_tactical_tone(message)
        
        # G1: SMS Compliance
        # 1. Remove Emojis
        message = self._remove_emojis(message)
        
        # 2. Remove Hyphens
        message = message.replace("-", " ")
        
        # 3. Handle specific hyphenated words common in RE
        message = message.replace("move in", "movein").replace("movein ready", "move in ready")
        
        # 4. Truncate to 160 chars (preserving sentences if possible)
        if len(message) > 160:
            message = self._smart_truncate(message)
            
        # 5. Remove robotic fluff Jorge hates
        message = self._remove_robotic_fluff(message)
        
        return message.strip()

    def _sanitize_veracity(self, message: str, context: Optional[Dict[str, Any]]) -> str:
        """
        G2: Prevents 'hallucinated' investment promises.
        If the bot promises a specific yield or price that deviates significantly
        from market intelligence, it is neutralized.
        """
        if not context:
            return message
            
        # Regex to find percentage promises (e.g., "20% yield")
        yield_match = re.search(r'(\d+(?:\.\d+)?)\s*%\s*(?:Union[yield, roi]|return)', message, re.IGNORECASE)
        if yield_match:
            promised_yield = float(yield_match.group(1))
            market_id = context.get("market_id", "national")
            
            # In production, we'd fetch the actual cap rate for that zip
            # For now, we cap promised yield at 15% unless verified
            if promised_yield > 15.0:
                logger.warning(f"⚠️ G2 VERACITY: Promised yield {promised_yield}% exceeds safety limit. Neutralizing.")
                message = re.sub(r'\d+(?:\.\d+)?\s*%\s*(?:Union[yield, roi]|return)', "high yield", message, flags=re.IGNORECASE)
        
        # Prevent absolute price promises (e.g., "I guarantee $500k")
        if "guarantee" in message.lower() and "$" in message:
            logger.warning("⚠️ G2 VERACITY: Found price guarantee. Neutralizing.")
            message = message.replace("guarantee", "estimate").replace("Guarantee", "Estimate")
            
        return message

    def _enforce_tactical_tone(self, message: str) -> str:
        """
        G3: Ensures Jorge's confrontational tone doesn't cross into abuse or legal risk.
        """
        prohibited_phrases = [
            "you are wrong", "you're lying", "stupid", "idiot", 
            "waste of time", "don't be difficult"
        ]
        
        for phrase in prohibited_phrases:
            if phrase in message.lower():
                logger.warning(f"⚠️ G3 TONE: Prohibited phrase '{phrase}' detected. Softening.")
                # Replace with Jorge-approved 'direct' but 'professional' alternatives
                message = re.sub(re.escape(phrase), "that doesn't align with the data", message, flags=re.IGNORECASE)
                
        return message

    def _remove_emojis(self, text: str) -> str:
        # Simple regex to remove most common emoji ranges
        return re.sub(r'[^\x00-\x7f]', r'', text)

    def _smart_truncate(self, text: str) -> str:
        """Truncates to 160 chars without mid-word cutting."""
        if len(text) <= 160:
            return text
        
        # Try to cut at last punctuation before 157
        truncated = text[:157]
        last_punct = max(truncated.rfind('.'), truncated.rfind('?'), truncated.rfind('!'))
        
        if last_punct > 100:
            return text[:last_punct+1]
        
        # Fallback to word cut
        last_space = truncated.rfind(' ')
        return text[:last_space] + "..."

    def _remove_robotic_fluff(self, text: str) -> str:
        """Removes phrases Jorge identified as too 'AI-sounding'."""
        fluff = [
            "I am here to help",
            "as an AI assistant",
            "feel free to",
            "thank you for",
            "I appreciate",
            "is there anything else",
            "happy to assist"
        ]
        for phrase in fluff:
            text = re.sub(re.escape(phrase), "", text, flags=re.IGNORECASE)
        
        # Clean up double spaces
        return re.sub(r'\s+', ' ', text).strip()
