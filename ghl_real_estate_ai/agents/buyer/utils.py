"""
Utility functions for buyer bot including budget extraction and property preference parsing.
"""

import re
from typing import Any, Dict, List, Optional

from ghl_real_estate_ai.ghl_utils.jorge_config import BuyerBudgetConfig
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)


async def extract_budget_range(
    conversation_history: List[Dict], budget_config: Optional[BuyerBudgetConfig] = None
) -> Optional[Dict[str, int]]:
    """Extract budget range from conversation history."""
    try:
        config = budget_config or BuyerBudgetConfig.from_environment()

        # Look for dollar amounts in conversation
        conversation_text = " ".join(
            [msg.get("content", "") for msg in conversation_history if msg.get("role") == "user"]
        )

        # Find dollar amounts with optional k (e.g., $450k, $500,000)
        dollar_pattern = r"\$([0-9,]+)([kK]?)"
        matches = re.findall(dollar_pattern, conversation_text)

        # Fallback: also match plain number amounts without $ prefix
        # Handles inputs like "450 to 500", "around 475k", "between 400 and 500"
        if not matches:
            plain_pattern = r"(?<!\$)\b(\d{1,3}(?:,\d{3})*)([kK]?)\b"
            matches = re.findall(plain_pattern, conversation_text)

        amounts = []
        for val, k_suffix in matches:
            amount = int(val.replace(",", ""))
            if k_suffix:
                amount *= 1000
            elif 100 <= amount < config.BUDGET_AMOUNT_K_THRESHOLD:
                # Only auto-multiply 100-999 range (clear K-shorthand in real estate)
                # "$500" -> $500K, but "$50" stays $50, "$1500" stays $1500
                amount *= 1000
            elif amount < 100:
                # Skip values too small to be a budget — typically bedroom/bathroom
                # counts ("3-bedroom house" → 3) captured by the plain-number fallback.
                continue
            amounts.append(amount)

        if len(amounts) >= 2:
            return {"min": min(amounts), "max": max(amounts)}
        elif len(amounts) == 1:
            # Single amount - assume it's max budget
            return {"min": int(amounts[0] * config.BUDGET_SINGLE_AMOUNT_MIN_FACTOR), "max": amounts[0]}

        return None

    except Exception as e:
        logger.error(f"Error extracting budget range: {str(e)}")
        return None


def assess_financial_from_conversation(conversation_text: str) -> Optional[Dict]:
    """Extract financial signals from conversation text."""
    if not conversation_text.strip():
        return None

    confidence = 0.5
    financing_status = "unknown"

    # High-confidence signals
    pre_approval_keywords = ["pre-approved", "preapproved", "pre approved", "got approved"]
    cash_keywords = ["cash buyer", "paying cash", "all cash", "cash offer"]
    budget_keywords = ["budget is", "can afford", "max price", "price range"]

    if any(kw in conversation_text for kw in pre_approval_keywords):
        financing_status = "pre_approved"
        confidence = 0.8
    elif any(kw in conversation_text for kw in cash_keywords):
        financing_status = "cash"
        confidence = 0.85
    elif any(kw in conversation_text for kw in budget_keywords):
        financing_status = "needs_approval"
        confidence = 0.6
    else:
        return None

    return {
        "financing_status": financing_status,
        "confidence": confidence * 100,
    }


async def extract_property_preferences(conversation_history: List[Dict]) -> Optional[Dict[str, Any]]:
    """Extract property preferences from conversation history."""
    try:
        conversation_text = " ".join(
            [msg.get("content", "").lower() for msg in conversation_history if msg.get("role") == "user"]
        )

        preferences = {}

        # Extract bedrooms
        bed_match = re.search(r"(\d+)\s*(bed|bedroom)", conversation_text)
        if bed_match:
            preferences["bedrooms"] = int(bed_match.group(1))

        # Extract bathrooms
        bath_match = re.search(r"(\d+)\s*(bath|bathroom)", conversation_text)
        if bath_match:
            preferences["bathrooms"] = int(bath_match.group(1))

        # Extract features
        features = []
        if "garage" in conversation_text:
            features.append("garage")
        if "pool" in conversation_text:
            features.append("pool")
        if "yard" in conversation_text:
            features.append("yard")

        if features:
            preferences["features"] = features

        return preferences if preferences else None

    except Exception as e:
        logger.error(f"Error extracting property preferences: {str(e)}")
        return None
