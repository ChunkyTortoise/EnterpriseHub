"""Multi-category objection engine for the Jorge Seller Bot.

Detects and responds to 6 categories of seller objections using a graduated
response strategy: validate -> data -> social_proof -> market_test.

Objection categories:
1. Pricing: "too expensive", "can't afford", "reduce commission"
2. Timing: "not ready", "too soon", "wait for spring"
3. Competition: "checking other agents", "interview others"
4. Trust: "don't know you", "new to area", "reviews"
5. Authority: "need to check with spouse", "consult lawyer"
6. Value: "what's included", "why should I", "what do you do"

Legacy pricing-specific objections (loss aversion, anchoring, etc.) are
now mapped to the PRICING category for backward compatibility.
"""

import logging
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ObjectionCategory(str, Enum):
    """High-level objection categories for Phase 2.2."""

    PRICING = "pricing"
    TIMING = "timing"
    COMPETITION = "competition"
    TRUST = "trust"
    AUTHORITY = "authority"
    VALUE = "value"


class ObjectionType(str, Enum):
    """Specific objection types (legacy + new)."""

    # Legacy pricing objections (mapped to PRICING category)
    LOSS_AVERSION = "loss_aversion"
    ANCHORING = "anchoring"
    NEIGHBOR_COMP = "neighbor_comp"
    MARKET_DENIAL = "market_denial"
    IMPROVEMENT_OVERVALUE = "improvement_overvalue"

    # New multi-category objections
    PRICING_GENERAL = "pricing_general"
    TIMING_NOT_READY = "timing_not_ready"
    COMPETITION_SHOPPING = "competition_shopping"
    TRUST_CREDIBILITY = "trust_credibility"
    AUTHORITY_DECISION_MAKER = "authority_decision_maker"
    VALUE_PROPOSITION = "value_proposition"


class ResponseGraduation(str, Enum):
    """Graduated response levels, escalated in order."""

    VALIDATE = "validate"  # Acknowledge the concern
    DATA = "data"  # Present market data
    SOCIAL_PROOF = "social_proof"  # Show comparable sales
    MARKET_TEST = "market_test"  # Propose a market test strategy


# Map objection types to categories
OBJECTION_CATEGORY_MAP: Dict[ObjectionType, ObjectionCategory] = {
    # Legacy pricing objections
    ObjectionType.LOSS_AVERSION: ObjectionCategory.PRICING,
    ObjectionType.ANCHORING: ObjectionCategory.PRICING,
    ObjectionType.NEIGHBOR_COMP: ObjectionCategory.PRICING,
    ObjectionType.MARKET_DENIAL: ObjectionCategory.PRICING,
    ObjectionType.IMPROVEMENT_OVERVALUE: ObjectionCategory.PRICING,
    # New multi-category
    ObjectionType.PRICING_GENERAL: ObjectionCategory.PRICING,
    ObjectionType.TIMING_NOT_READY: ObjectionCategory.TIMING,
    ObjectionType.COMPETITION_SHOPPING: ObjectionCategory.COMPETITION,
    ObjectionType.TRUST_CREDIBILITY: ObjectionCategory.TRUST,
    ObjectionType.AUTHORITY_DECISION_MAKER: ObjectionCategory.AUTHORITY,
    ObjectionType.VALUE_PROPOSITION: ObjectionCategory.VALUE,
}


@dataclass
class ObjectionDetection:
    """Result of objection detection."""

    detected: bool
    objection_type: Optional[ObjectionType] = None
    objection_category: Optional[ObjectionCategory] = None
    confidence: float = 0.0
    matched_text: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ObjectionResponse:
    """Generated response to a detected objection."""

    objection_type: ObjectionType
    objection_category: ObjectionCategory
    graduation_level: ResponseGraduation
    response_text: str
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    next_graduation: Optional[ResponseGraduation] = None


# Detection patterns for each objection type
OBJECTION_PATTERNS: Dict[ObjectionType, List[Tuple[str, float]]] = {
    ObjectionType.LOSS_AVERSION: [
        (r"\bcan'?t\s+sell\s+for\s+less\b", 0.9),
        (r"\bpaid\s+\$?\d", 0.8),
        (r"\bowe\s+more\s+than\b", 0.9),
        (r"\bunderwater\b", 0.7),
        (r"\blose\s+money\b", 0.85),
        (r"\bwon'?t\s+take\s+a\s+loss\b", 0.9),
    ],
    ObjectionType.ANCHORING: [
        (r"\bzillow\b", 0.85),
        (r"\bredfin\b", 0.8),
        (r"\bestimate\s+(says?|shows?)\b", 0.75),
        (r"\bonline\s+(value|estimate|price)\b", 0.7),
        (r"\bzestimate\b", 0.9),
    ],
    ObjectionType.NEIGHBOR_COMP: [
        (r"\bneighbor\b.{0,30}\b(sold|got|received)\b", 0.85),
        (r"\b(down|across)\s+the\s+street\b.{0,30}\b(sold|got)\b", 0.8),
        (r"\bsimilar\s+home\s+(sold|went)\b", 0.75),
        (r"\bcomp.{0,10}\$([\d,]+)\b", 0.7),
    ],
    ObjectionType.MARKET_DENIAL: [
        (r"\bmarket\s+will\s+(come\s+back|recover|bounce)\b", 0.9),
        (r"\bwait\s+(for|until)\s+(the\s+)?market\b", 0.85),
        (r"\bprices\s+(will|are\s+going\s+to)\s+(go\s+up|rise|increase)\b", 0.8),
        (r"\bnot\s+a\s+good\s+time\s+to\s+sell\b", 0.7),
    ],
    ObjectionType.IMPROVEMENT_OVERVALUE: [
        (r"\bput\s+\$?\d.{0,20}\binto\b", 0.85),
        (r"\brenovated\b|\bremodeled\b", 0.7),
        (r"\bnew\s+(kitchen|bathroom|roof|hvac|flooring)\b", 0.75),
        (r"\bupgraded?\b.{0,20}\b(worth|value)\b", 0.7),
        (r"\bspent\s+\$?\d", 0.8),
    ],
    # New multi-category objections
    ObjectionType.PRICING_GENERAL: [
        (r"\btoo\s+(expensive|much|high)\b", 0.85),
        (r"\bcan'?t\s+afford\b", 0.9),
        (r"\breduce\s+(your\s+)?commission\b", 0.9),
        (r"\bfees?\s+(are|too)\b", 0.8),
        (r"\bcheaper\s+agent\b", 0.85),
        (r"\b(lower|reduce)\s+(the\s+)?price\b", 0.8),
    ],
    ObjectionType.TIMING_NOT_READY: [
        (r"\bnot\s+ready\b", 0.85),
        (r"\btoo\s+soon\b", 0.8),
        (r"\bwait\s+(for|until)\s+(spring|summer|fall|market)\b", 0.85),
        (r"\bneed\s+(more\s+)?time\b", 0.75),
        (r"\brushing\s+(me|us)\b", 0.8),
        (r"\bthinking\s+about\s+it\b", 0.7),
    ],
    ObjectionType.COMPETITION_SHOPPING: [
        (r"\bcheck(ing)?\s+(with\s+)?other\s+agents?\b", 0.9),
        (r"\binterview(ing)?\s+(other|multiple|a\s+few)\b", 0.85),
        (r"\bcomparing\s+agents?\b", 0.85),
        (r"\btalking\s+to\s+(other|someone\s+else)\b", 0.8),
        (r"\bhave\s+another\s+agent\b", 0.9),
    ],
    ObjectionType.TRUST_CREDIBILITY: [
        (r"\bdon'?t\s+know\s+(you|anything\s+about\s+you)\b", 0.9),
        (r"\bnew\s+to\s+(the\s+)?(area|market)\b", 0.8),
        (r"\bhow\s+(long|many)\s+(have\s+you\s+been|years|experience)\b", 0.75),
        (r"\breview?s\b", 0.7),
        (r"\breferences?\b", 0.75),
        (r"\bcredentials?\b", 0.8),
    ],
    ObjectionType.AUTHORITY_DECISION_MAKER: [
        (r"\bneed\s+to\s+(check|talk|consult)\s+(with|my)\s+(spouse|wife|husband|partner)\b", 0.9),
        (r"\bneed\s+to\s+(think|consult)\s+(it\s+over|my\s+lawyer|my\s+family)\b", 0.85),
        (r"\bnot\s+the\s+only\s+decision\s+maker\b", 0.9),
        (r"\bmy\s+(wife|husband|partner)\s+needs\s+to\b", 0.85),
    ],
    ObjectionType.VALUE_PROPOSITION: [
        (r"\bwhat'?s\s+included\b", 0.8),
        (r"\bwhy\s+should\s+I\b", 0.75),
        (r"\bwhat\s+do\s+you\s+(do|offer)\b", 0.7),
        (r"\bhow\s+(are\s+you\s+)?different\b", 0.8),
        (r"\bwhat\s+makes\s+you\s+(special|better|unique)\b", 0.85),
        (r"\bwhat'?s\s+in\s+it\s+for\s+me\b", 0.9),
    ],
}

# Response templates per objection type per graduation level
RESPONSE_TEMPLATES: Dict[ObjectionType, Dict[ResponseGraduation, str]] = {
    ObjectionType.LOSS_AVERSION: {
        ResponseGraduation.VALIDATE: (
            "I completely understand the concern about selling below what you paid. "
            "No one wants to feel like they're losing money on their home."
        ),
        ResponseGraduation.DATA: (
            "Let me share some context. The Rancho Cucamonga market has shifted since you purchased. "
            "Current comparable sales in your area show a median of {median_price}. "
            "The gap between your purchase price and current market is about {gap_percent}%."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "Several homeowners in your area faced the same situation. "
            "Those who priced competitively from the start actually netted more — "
            "overpriced homes averaged {avg_days_overpriced} days on market and sold for "
            "{avg_reduction}% below their original asking price."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's what I'd suggest: let's price at {suggested_price} for 14 days "
            "as a market test. If we get strong showing activity and offers, we know "
            "we're in the right range. If not, we can adjust. No long-term commitment."
        ),
    },
    ObjectionType.ANCHORING: {
        ResponseGraduation.VALIDATE: (
            "Those online estimates are a great starting point for research! "
            "It's smart to come prepared with that information."
        ),
        ResponseGraduation.DATA: (
            "Online estimates use broad algorithms that can't account for your home's "
            "unique features. Zillow's own data shows their Zestimate has a median error "
            "rate of about 7%. For your home, that could mean a {error_range} difference."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I recently helped a seller on {nearby_street} whose Zillow estimate was "
            "${zestimate_example}. After a proper CMA, we listed at ${actual_list} and "
            "sold for ${actual_sold}."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Let's do this: I'll prepare a detailed CMA using actual closed sales "
            "in the last 90 days within a mile of your property. We can compare that "
            "side-by-side with the online estimate and find the right price together."
        ),
    },
    ObjectionType.NEIGHBOR_COMP: {
        ResponseGraduation.VALIDATE: (
            "That's a great reference point! Knowing what nearby homes sold for "
            "is exactly the kind of research that helps."
        ),
        ResponseGraduation.DATA: (
            "Let me pull up that sale. Comparable sales need to account for "
            "square footage, lot size, condition, and upgrades. Even on the same street, "
            "homes can differ by {typical_variance}% in value."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "When we look at the actual comparables, your home has {advantages} "
            "that the neighbor's didn't, but their home had {neighbor_advantages}. "
            "The adjusted comparison puts your home at {adjusted_value}."
        ),
        ResponseGraduation.MARKET_TEST: (
            "I'd suggest we list at {suggested_price} and see how the market responds "
            "in the first two weeks. Buyer activity will tell us exactly where we stand "
            "relative to your neighbor's sale."
        ),
    },
    ObjectionType.MARKET_DENIAL: {
        ResponseGraduation.VALIDATE: (
            "I appreciate that perspective. Timing the market is something every seller thinks about."
        ),
        ResponseGraduation.DATA: (
            "Here's what the data shows for Rancho Cucamonga: {market_trend}. "
            "Meanwhile, your carrying costs (mortgage, taxes, insurance, maintenance) "
            "add up to roughly ${monthly_carrying}/month while you wait."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "Sellers who waited 6+ months in similar market conditions in this area "
            "typically saw {wait_outcome}. The carrying costs alone can offset any "
            "potential price gain."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's an option: let's get your home market-ready now and list at "
            "a strong price. If we don't get the right offer in 30 days, "
            "we can reassess. You'll have real market data instead of predictions."
        ),
    },
    ObjectionType.IMPROVEMENT_OVERVALUE: {
        ResponseGraduation.VALIDATE: (
            "Those improvements clearly show you've taken great care of your home! "
            "A remodeled {improvement_type} is definitely a selling point."
        ),
        ResponseGraduation.DATA: (
            "Renovation ROI varies by project. According to the latest Cost vs. Value report, "
            "a {improvement_type} remodel in our market typically returns about {roi_percent}% "
            "of the investment. Your ${spent} investment adds roughly ${value_add} in market value."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I see this often. A recent seller invested ${similar_spent} in upgrades "
            "and we were able to capture ${similar_recovered} of that in the final price. "
            "The key is positioning those upgrades as differentiators."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Let's highlight your {improvement_type} as a premium feature in our marketing. "
            "I'll prepare a targeted marketing plan that showcases these upgrades "
            "to buyers who specifically value them."
        ),
    },
    # ── New multi-category types (Phase 3) ──────────────────────────────────
    ObjectionType.PRICING_GENERAL: {
        ResponseGraduation.VALIDATE: (
            "I completely understand your concern about costs. Selling a home is a significant "
            "financial decision, and you want to make sure every dollar counts."
        ),
        ResponseGraduation.DATA: (
            "Let me break down the numbers. In Rancho Cucamonga, homes listed with full-service "
            "agents sell for an average of {price_premium}% more than discount listings, which "
            "typically covers the commission difference and then some."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "A recent seller on {nearby_street} was considering a discount broker to save on "
            "commission. We ran the numbers, and my full marketing package got them "
            "${additional_proceeds} more than they would have netted with the discount option."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's what I propose: let me prepare a no-obligation market analysis showing you "
            "the projected net proceeds with different pricing and commission structures. "
            "You'll see exactly what you'd walk away with under each scenario."
        ),
    },
    ObjectionType.TIMING_NOT_READY: {
        ResponseGraduation.VALIDATE: (
            "I appreciate you being honest about where you are in the process. "
            "There's never a rush when it comes to something this important."
        ),
        ResponseGraduation.DATA: (
            "Let me share some timing context. Right now we're in {market_season} in Rancho "
            "Cucamonga, which historically sees {seasonal_activity}. "
            "The next {upcoming_season} typically brings {upcoming_trend}."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I had a seller last year in {nearby_area} who wanted to wait for spring. We did "
            "the math on carrying costs versus potential price increase, and they decided to "
            "list in February. Sold in {days_to_sale} days for ${sale_price}."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's an option: let's prepare your home for market now, so when you're ready, "
            "we can go live within 48 hours. I'll do the staging consultation and photography "
            "prep — no commitment until you give me the green light."
        ),
    },
    ObjectionType.COMPETITION_SHOPPING: {
        ResponseGraduation.VALIDATE: (
            "Absolutely, you should interview other agents! This is an important decision, "
            "and you deserve to find the right fit. I'm confident you'll find that I bring "
            "a unique approach to selling homes in this market."
        ),
        ResponseGraduation.DATA: (
            "Here's what I'd suggest you ask other agents: What's your average days on market? "
            "How many homes in this price range have you sold in the past 12 months? "
            "What's your list-to-sale price ratio? Mine are {dom}, {homes_sold}, and {list_sale_ratio}."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I compete for business every day, and I welcome the comparison. Here's what sets "
            "me apart: {unique_value_prop}. My last {recent_count} sellers all had multiple "
            "offers within {offer_timeline}."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's what I'll do: give me 15 minutes to show you my marketing plan and recent "
            "sales results. If you're not impressed, no hard feelings. But I think you'll see "
            "why my clients choose to work exclusively with me."
        ),
    },
    ObjectionType.TRUST_CREDIBILITY: {
        ResponseGraduation.VALIDATE: (
            "That's a very fair concern. You're about to trust someone with one of your biggest "
            "assets — you should absolutely know who you're working with and what they've accomplished."
        ),
        ResponseGraduation.DATA: (
            "I've been selling real estate in Rancho Cucamonga for {years_experience} years. "
            "In that time, I've closed {total_sales} transactions worth ${total_volume} in "
            "sales volume. My average seller rating is {avg_rating}/5."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I'd love to share some client testimonials. Here's what {client_name} from "
            "{nearby_area} said: '{testimonial}'. I can also provide references from recent "
            "sellers who are happy to speak with you."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Here's what I suggest: let's start with a no-obligation market analysis. "
            "I'll show you how I'd position and market your home, and you can judge for "
            "yourself whether I know this market."
        ),
    },
    ObjectionType.AUTHORITY_DECISION_MAKER: {
        ResponseGraduation.VALIDATE: (
            "Absolutely, this is a decision you should make together. I'd be happy to include "
            "your {partner_relation} in our next conversation so everyone's on the same page."
        ),
        ResponseGraduation.DATA: (
            "When we meet with your {partner_relation}, I'll bring a complete market analysis, "
            "pricing strategy, and projected net proceeds. That way everyone has the same "
            "information to make an informed decision."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "I work with couples and families all the time. What I've found is that when "
            "everyone's involved from the start, the selling process goes much more smoothly. "
            "I make sure all decision-makers feel heard and informed."
        ),
        ResponseGraduation.MARKET_TEST: (
            "Let's schedule a consultation that works for everyone. I'll present the full "
            "strategy, answer any questions, and we can make sure all decision-makers are "
            "comfortable before moving forward."
        ),
    },
    ObjectionType.VALUE_PROPOSITION: {
        ResponseGraduation.VALIDATE: (
            "Great question. You should absolutely know what you're getting for your investment. "
            "Let me walk you through exactly what I provide and how it translates to results."
        ),
        ResponseGraduation.DATA: (
            "Here's what's included: {service_list}. My marketing budget per listing averages "
            "${marketing_budget}, and I invest in professional photography, 3D virtual tours, "
            "targeted online advertising, and open house events."
        ),
        ResponseGraduation.SOCIAL_PROOF: (
            "My clients consistently tell me that what sets me apart is {client_feedback}. "
            "Here's a recent testimonial: '{testimonial_quote}'"
        ),
        ResponseGraduation.MARKET_TEST: (
            "Let me show you exactly what I'll do for your home. I'll prepare a custom "
            "marketing plan with sample ads, staging recommendations, and a pricing strategy. "
            "You'll see the full scope of what you're getting."
        ),
    },
}


class PricingObjectionEngine:
    """Detects multi-category objections and generates graduated responses.

    Supports 6 objection categories:
    - PRICING: Commission, costs, fees
    - TIMING: Not ready, waiting for market
    - COMPETITION: Shopping other agents
    - TRUST: Credibility, experience, reviews
    - AUTHORITY: Need spouse/partner approval
    - VALUE: What's included, why choose you
    """

    def __init__(self):
        # Track graduation level per contact per objection type
        self._contact_graduation: Dict[str, Dict[ObjectionType, int]] = {}

    def get_objection_category(self, objection_type: ObjectionType) -> Optional[ObjectionCategory]:
        """Get the category for a specific objection type.

        Args:
            objection_type: The specific objection type.

        Returns:
            ObjectionCategory or None if not found.
        """
        return OBJECTION_CATEGORY_MAP.get(objection_type)

    def detect_objection(self, message: str) -> ObjectionDetection:
        """Detect if a message contains a pricing objection.

        Args:
            message: User message text.

        Returns:
            ObjectionDetection with type and confidence if found.
        """
        best_match: Optional[Tuple[ObjectionType, float, str]] = None

        for obj_type, patterns in OBJECTION_PATTERNS.items():
            for pattern, base_confidence in patterns:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    if best_match is None or base_confidence > best_match[1]:
                        best_match = (obj_type, base_confidence, match.group(0))

        if best_match is None:
            return ObjectionDetection(detected=False)

        obj_type = best_match[0]
        obj_category = OBJECTION_CATEGORY_MAP.get(obj_type)

        return ObjectionDetection(
            detected=True,
            objection_type=obj_type,
            objection_category=obj_category,
            confidence=best_match[1],
            matched_text=best_match[2],
        )

    def generate_response(
        self,
        objection: ObjectionDetection,
        contact_id: str,
        market_data: Optional[Dict[str, Any]] = None,
        variant_index: int = 0,
    ) -> Optional[ObjectionResponse]:
        """Generate a graduated response to a detected objection.

        Args:
            objection: Detection result.
            contact_id: GHL contact ID for tracking graduation.
            market_data: Optional market data for template variables.
            variant_index: A/B test variant index (default: 0).

        Returns:
            ObjectionResponse or None if no objection detected.
        """
        if not objection.detected or objection.objection_type is None:
            return None

        obj_type = objection.objection_type
        obj_category = objection.objection_category or OBJECTION_CATEGORY_MAP.get(obj_type)

        # Get current graduation level for this contact + objection type
        contact_state = self._contact_graduation.setdefault(contact_id, {})
        current_level_idx = contact_state.get(obj_type, 0)

        graduation_order = list(ResponseGraduation)
        level_idx = min(current_level_idx, len(graduation_order) - 1)
        graduation_level = graduation_order[level_idx]

        # Import here to avoid circular dependency
        try:
            from ghl_real_estate_ai.prompts.objection_responses import get_response_template

            template = get_response_template(obj_type, graduation_level, variant_index)
        except (ImportError, Exception) as e:
            logger.warning("Failed to import objection_responses, using legacy templates: %s", e)
            # Fallback to legacy RESPONSE_TEMPLATES
            templates = RESPONSE_TEMPLATES.get(obj_type, {})
            template = templates.get(graduation_level, "")

        if not template:
            return None

        # Fill template with market data
        response_text = template
        if market_data:
            try:
                response_text = template.format_map(_SafeFormatDict(market_data))
            except (KeyError, ValueError):
                pass  # Use template with unfilled placeholders

        # Advance graduation for next time
        next_idx = min(current_level_idx + 1, len(graduation_order) - 1)
        contact_state[obj_type] = next_idx
        next_graduation = graduation_order[next_idx] if next_idx > level_idx else None

        logger.info(
            "Objection response: %s/%s (level %s, variant %d) for contact %s",
            obj_category.value if obj_category else "unknown",
            obj_type.value,
            graduation_level.value,
            variant_index,
            contact_id,
        )

        return ObjectionResponse(
            objection_type=obj_type,
            objection_category=obj_category or ObjectionCategory.PRICING,
            graduation_level=graduation_level,
            response_text=response_text,
            supporting_data=market_data or {},
            next_graduation=next_graduation,
        )

    def get_graduation_level(self, contact_id: str, objection_type: ObjectionType) -> int:
        """Get current graduation level for a contact and objection type."""
        return self._contact_graduation.get(contact_id, {}).get(objection_type, 0)

    def reset_contact(self, contact_id: str) -> None:
        """Reset all graduation levels for a contact."""
        self._contact_graduation.pop(contact_id, None)


class _SafeFormatDict(dict):
    """Dict that returns '{key}' for missing keys during str.format_map()."""

    def __missing__(self, key: str) -> str:
        return f"{{{key}}}"


# Singleton
_engine: Optional[PricingObjectionEngine] = None


def get_pricing_objection_engine() -> PricingObjectionEngine:
    global _engine
    if _engine is None:
        _engine = PricingObjectionEngine()
    return _engine
