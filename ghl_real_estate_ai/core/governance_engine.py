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
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class GovernanceEngine:
    """
    Final validator for all bot responses before they reach the lead.
    Forces compliance with Jorge's specific SMS constraints.
    """
    
    def enforce(self, message: str) -> str:
        """
        Applies all governance rules to a message.
        """
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
