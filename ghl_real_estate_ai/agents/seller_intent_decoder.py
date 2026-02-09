"""
Seller Intent Decoder Engine - Seller Bot Component
Calculates seller-specific qualification scores for property condition anxiety,
valuation confidence, prep readiness, listing urgency, and motivation.
Designed to identify 'Serious Sellers' and their readiness to list.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient, GHLContact

from ghl_real_estate_ai.models.lead_scoring import SellerIntentProfile

logger = logging.getLogger(__name__)


class SellerIntentDecoder:
    """
    Decodes seller intent using linguistic markers and behavioral signals.
    Implements seller-specific scoring for listing qualification.
    """

    def __init__(self, ghl_client: Optional[EnhancedGHLClient] = None, industry_config: Optional["IndustryConfig"] = None):
        self.ghl_client = ghl_client

        # Load industry config for config-first marker initialization

        cfg = industry_config

        # Condition Anxiety Markers
        self.high_condition_anxiety = [
            "needs work",
            "fixer",
            "dated",
            "old roof",
            "foundation issues",
            "major repairs",
        ]
        self.medium_condition_anxiety = [
            "some updates needed",
            "cosmetic fixes",
            "needs paint",
            "carpet replacement",
        ]
        self.low_condition_anxiety = [
            "move-in ready",
            "turnkey",
            "recently renovated",
            "just remodeled",
            "updated",
        ]

        # Valuation Confidence Markers
        self.high_valuation_confidence = [
            "know what it's worth",
            "had it appraised",
            "got a cma",
            "recent appraisal",
        ]
        self.medium_valuation_confidence = [
            "zestimate says",
            "zillow shows",
            "online estimate",
            "neighbor sold for",
        ]
        self.low_valuation_confidence = [
            "no idea what it's worth",
            "not sure of value",
            "what's my home worth",
        ]

        # Prep Readiness Markers
        self.high_prep_readiness = [
            "already staged",
            "house is ready",
            "cleared out",
            "decluttered",
            "ready to show",
        ]
        self.medium_prep_readiness = [
            "almost ready",
            "need to clean up",
            "finishing touches",
            "few things to do",
        ]
        self.low_prep_readiness = [
            "haven't started",
            "lot of stuff",
            "not ready yet",
            "need to pack",
            "hoarder",
        ]

        # Listing Urgency Markers (config-first, hardcoded fallback)
        self.immediate_urgency = (
            cfg.intents.timeline.high if cfg and cfg.intents.timeline.high
            else [
                "need to sell now",
                "relocating",
                "divorce",
                "foreclosure",
                "job transfer",
                "asap",
            ]
        )
        self.medium_urgency = (
            cfg.intents.timeline.medium if cfg and cfg.intents.timeline.medium
            else [
                "want to sell",
                "thinking of selling",
                "this year",
                "next few months",
            ]
        )
        self.low_urgency = (
            cfg.intents.motivation.low if cfg and cfg.intents.motivation.low
            else [
                "just curious",
                "no rush",
                "exploring options",
                "maybe someday",
                "testing the market",
            ]
        )

        # Price Flexibility Markers
        self.high_flexibility = [
            "flexible on price",
            "open to offers",
            "negotiable",
            "just want to sell",
            "take what I can get",
        ]
        self.medium_flexibility = [
            "reasonable offers",
            "close to asking",
            "within range",
        ]
        self.low_flexibility = [
            "firm on price",
            "won't go below",
            "bottom line",
            "non-negotiable",
            "not a penny less",
        ]

        # Motivation Markers (config-first, hardcoded fallback)
        self.high_motivation = (
            cfg.intents.motivation.high if cfg and cfg.intents.motivation.high
            else [
                "must sell",
                "have to move",
                "already bought",
                "relocating for work",
                "divorce settlement",
                "estate sale",
            ]
        )
        self.medium_motivation = (
            cfg.intents.motivation.medium if cfg and cfg.intents.motivation.medium
            else [
                "want to upgrade",
                "downsizing",
                "empty nesters",
                "outgrown",
            ]
        )
        self.low_motivation = (
            cfg.intents.motivation.low if cfg and cfg.intents.motivation.low
            else [
                "just seeing what it\'s worth",
                "curious about the market",
                "no pressure",
            ]
        )

    def analyze_seller(
        self, seller_id: str, conversation_history: List[Dict[str, str]]
    ) -> SellerIntentProfile:
        """
        Analyze seller intent from conversation history.

        Args:
            seller_id: The seller's unique identifier
            conversation_history: List of conversation messages

        Returns:
            SellerIntentProfile with scores and classification
        """
        try:
            conversation_text = " ".join(
                [
                    msg.get("content", "").lower()
                    for msg in conversation_history
                    if msg.get("role") == "user"
                ]
            )

            condition_anxiety = self._score_condition_anxiety(conversation_text)
            valuation_confidence = self._score_valuation_confidence(conversation_text)
            prep_readiness = self._score_prep_readiness(conversation_text)
            listing_urgency = self._score_listing_urgency(conversation_text)
            price_flexibility = self._score_price_flexibility(conversation_text)
            motivation_strength = self._score_motivation(conversation_text)

            # Calculate overall seller temperature
            # Higher anxiety lowers score, higher everything else raises it
            overall_score = (
                (100 - condition_anxiety) * 0.10
                + valuation_confidence * 0.15
                + prep_readiness * 0.15
                + listing_urgency * 0.25
                + price_flexibility * 0.10
                + motivation_strength * 0.25
            )

            seller_temperature = self._classify_seller_temperature(overall_score)
            next_step = self._determine_next_qualification_step(
                condition_anxiety,
                valuation_confidence,
                listing_urgency,
                motivation_strength,
            )

            return SellerIntentProfile(
                condition_anxiety=condition_anxiety,
                valuation_confidence=valuation_confidence,
                prep_readiness=prep_readiness,
                listing_urgency=listing_urgency,
                price_flexibility=price_flexibility,
                motivation_strength=motivation_strength,
                seller_temperature=seller_temperature,
                confidence_level=min(95.0, len(conversation_history) * 10),
                conversation_turns=len(conversation_history),
                key_insights=self._extract_key_insights(conversation_text),
                next_qualification_step=next_step,
            )

        except Exception as e:
            logger.error(
                f"Error analyzing seller intent for {seller_id}: {str(e)}",
                exc_info=True,
            )
            return self._create_default_profile()

    async def analyze_seller_with_ghl(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, str]],
        ghl_contact: Optional[GHLContact] = None,
    ) -> SellerIntentProfile:
        """
        Enhanced seller analysis incorporating GHL contact data.

        Falls back to standard analyze_seller() if GHL data is unavailable.
        """
        if ghl_contact is None and self.ghl_client is not None:
            try:
                ghl_contact = await self.ghl_client.get_contact(contact_id)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch GHL contact {contact_id}: {e}. "
                    f"Falling back to conversation-only analysis."
                )

        if ghl_contact is None:
            logger.info(
                f"No GHL data for seller {contact_id}, using conversation-only analysis"
            )
            return self.analyze_seller(contact_id, conversation_history)

        profile = self.analyze_seller(contact_id, conversation_history)

        try:
            ghl_data = {
                "tags": ghl_contact.tags or [],
                "custom_fields": ghl_contact.custom_fields or {},
                "source": ghl_contact.source,
                "date_added": ghl_contact.created_at,
                "last_activity": ghl_contact.last_activity_at
                or ghl_contact.updated_at,
            }
        except Exception as e:
            logger.warning(
                f"Error extracting GHL data for seller {contact_id}: {e}"
            )
            return profile

        return self._apply_ghl_seller_boosts(profile, ghl_data)

    def _apply_ghl_seller_boosts(
        self,
        profile: SellerIntentProfile,
        ghl_data: Dict[str, Any],
    ) -> SellerIntentProfile:
        """Apply seller-specific boosts based on GHL contact data."""
        tags = [t.lower() for t in ghl_data.get("tags", [])]
        custom_fields = ghl_data.get("custom_fields", {})

        listing_urgency = profile.listing_urgency
        motivation_strength = profile.motivation_strength
        valuation_confidence = profile.valuation_confidence

        # Tag-based boosts
        if "hot-seller" in tags:
            listing_urgency += 20
            motivation_strength += 15
        if "motivated-seller" in tags:
            motivation_strength += 20
        if "relocation" in tags:
            listing_urgency += 15
            motivation_strength += 10

        # Custom field boosts
        if custom_fields.get("property_condition"):
            valuation_confidence += 10
        if custom_fields.get("timeline_urgency"):
            listing_urgency += 10

        # Engagement recency
        last_activity = ghl_data.get("last_activity")
        if last_activity is not None:
            try:
                now = datetime.now(timezone.utc)
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                days_since = (now - last_activity).days
                if days_since <= 3:
                    listing_urgency += 10
                elif days_since > 30:
                    listing_urgency -= 10
            except Exception as e:
                logger.debug(f"Could not compute seller engagement recency: {e}")

        # Clamp all scores
        listing_urgency = max(0, min(100, listing_urgency))
        motivation_strength = max(0, min(100, motivation_strength))
        valuation_confidence = max(0, min(100, valuation_confidence))

        # Recalculate overall score
        overall_score = (
            (100 - profile.condition_anxiety) * 0.10
            + valuation_confidence * 0.15
            + profile.prep_readiness * 0.15
            + listing_urgency * 0.25
            + profile.price_flexibility * 0.10
            + motivation_strength * 0.25
        )

        seller_temperature = self._classify_seller_temperature(overall_score)
        next_step = self._determine_next_qualification_step(
            profile.condition_anxiety,
            valuation_confidence,
            listing_urgency,
            motivation_strength,
        )

        return SellerIntentProfile(
            condition_anxiety=profile.condition_anxiety,
            valuation_confidence=valuation_confidence,
            prep_readiness=profile.prep_readiness,
            listing_urgency=listing_urgency,
            price_flexibility=profile.price_flexibility,
            motivation_strength=motivation_strength,
            seller_temperature=seller_temperature,
            confidence_level=min(95.0, profile.confidence_level + 5.0),
            conversation_turns=profile.conversation_turns,
            key_insights=profile.key_insights,
            next_qualification_step=next_step,
        )

    def _score_condition_anxiety(self, text: str) -> float:
        """Score condition anxiety (0-100). Higher = more anxious about condition."""
        score = 30
        high_matches = sum(1 for m in self.high_condition_anxiety if m in text)
        score += min(high_matches * 20, 60)
        medium_matches = sum(1 for m in self.medium_condition_anxiety if m in text)
        score += min(medium_matches * 10, 20)
        low_matches = sum(1 for m in self.low_condition_anxiety if m in text)
        score -= min(low_matches * 15, 30)
        return max(0, min(100, score))

    def _score_valuation_confidence(self, text: str) -> float:
        """Score valuation confidence (0-100)."""
        score = 30
        high_matches = sum(1 for m in self.high_valuation_confidence if m in text)
        score += min(high_matches * 25, 50)
        medium_matches = sum(1 for m in self.medium_valuation_confidence if m in text)
        score += min(medium_matches * 10, 20)
        low_matches = sum(1 for m in self.low_valuation_confidence if m in text)
        score -= min(low_matches * 15, 30)

        # Dollar amounts boost confidence
        dollar_mentions = len(re.findall(r"\$[\d,]+", text))
        score += min(dollar_mentions * 10, 20)

        return max(0, min(100, score))

    def _score_prep_readiness(self, text: str) -> float:
        """Score preparation readiness (0-100)."""
        score = 30
        high_matches = sum(1 for m in self.high_prep_readiness if m in text)
        score += min(high_matches * 20, 60)
        medium_matches = sum(1 for m in self.medium_prep_readiness if m in text)
        score += min(medium_matches * 10, 20)
        low_matches = sum(1 for m in self.low_prep_readiness if m in text)
        score -= min(low_matches * 15, 30)
        return max(0, min(100, score))

    def _score_listing_urgency(self, text: str) -> float:
        """Score listing urgency (0-100)."""
        score = 25
        immediate_matches = sum(1 for m in self.immediate_urgency if m in text)
        score += min(immediate_matches * 25, 50)
        medium_matches = sum(1 for m in self.medium_urgency if m in text)
        score += min(medium_matches * 15, 30)
        low_matches = sum(1 for m in self.low_urgency if m in text)
        score -= min(low_matches * 15, 30)
        return max(0, min(100, score))

    def _score_price_flexibility(self, text: str) -> float:
        """Score price flexibility (0-100)."""
        score = 40
        high_matches = sum(1 for m in self.high_flexibility if m in text)
        score += min(high_matches * 20, 40)
        medium_matches = sum(1 for m in self.medium_flexibility if m in text)
        score += min(medium_matches * 10, 20)
        low_matches = sum(1 for m in self.low_flexibility if m in text)
        score -= min(low_matches * 15, 30)
        return max(0, min(100, score))

    def _score_motivation(self, text: str) -> float:
        """Score overall motivation (0-100)."""
        score = 25
        high_matches = sum(1 for m in self.high_motivation if m in text)
        score += min(high_matches * 25, 50)
        medium_matches = sum(1 for m in self.medium_motivation if m in text)
        score += min(medium_matches * 15, 30)
        low_matches = sum(1 for m in self.low_motivation if m in text)
        score -= min(low_matches * 15, 30)
        return max(0, min(100, score))

    def _classify_seller_temperature(self, overall_score: float) -> str:
        """Classify seller temperature based on overall score."""
        if overall_score >= 75:
            return "hot"
        elif overall_score >= 50:
            return "warm"
        elif overall_score >= 35:
            return "lukewarm"
        elif overall_score >= 20:
            return "cold"
        else:
            return "ice_cold"

    def _determine_next_qualification_step(
        self,
        condition: float,
        valuation: float,
        urgency: float,
        motivation: float,
    ) -> str:
        """Determine next qualification step based on scores."""
        if motivation < 50:
            return "motivation"
        elif urgency < 50:
            return "timeline"
        elif valuation < 50:
            return "valuation"
        elif condition > 60:
            return "condition_support"
        else:
            return "listing_prep"

    def _extract_key_insights(self, text: str) -> Dict[str, Any]:
        """Extract key insights from conversation."""
        return {
            "mentions_condition": any(
                m in text
                for m in self.high_condition_anxiety + self.medium_condition_anxiety
            ),
            "has_valuation_source": any(
                m in text
                for m in self.high_valuation_confidence
                + self.medium_valuation_confidence
            ),
            "shows_urgency": any(m in text for m in self.immediate_urgency),
            "is_motivated": any(m in text for m in self.high_motivation),
            "is_price_flexible": any(m in text for m in self.high_flexibility),
            "is_prep_ready": any(m in text for m in self.high_prep_readiness),
        }

    def _create_default_profile(self) -> SellerIntentProfile:
        """Create default profile for error cases."""
        return SellerIntentProfile(
            condition_anxiety=30.0,
            valuation_confidence=25.0,
            prep_readiness=25.0,
            listing_urgency=25.0,
            price_flexibility=40.0,
            motivation_strength=25.0,
            seller_temperature="cold",
            confidence_level=10.0,
            conversation_turns=0,
            key_insights={},
            next_qualification_step="motivation",
        )
