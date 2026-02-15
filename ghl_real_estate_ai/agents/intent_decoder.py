"""
Intent Decoder Engine - Section 1 of 2026 Strategic Roadmap
Calculates Financial Readiness Score (FRS) and Psychological Commitment Score (PCS).
Updated to use unified models in ghl_real_estate_ai.models.lead_scoring.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from ghl_real_estate_ai.services.enhanced_ghl_client import EnhancedGHLClient, GHLContact

from ghl_real_estate_ai.models.lead_scoring import (
    ConditionRealism,
    FinancialReadinessScore,
    LeadIntentProfile,
    MotivationSignals,
    PriceResponsiveness,
    PsychologicalCommitmentScore,
    TimelineCommitment,
)

logger = logging.getLogger(__name__)

# Phase 3 Loop 1: GHL Tag Boost Configuration
TAG_BOOST_MAP = {
    "urgent-seller": 15,
    "pre-approved-buyer": 20,
    "hot-lead": 15,
    "warm-lead": 10,
    "cold-lead": -5,
    "investor-seller": 10,
    "distressed-seller": 12,
    "referral": 5,
    "do-not-contact": -20,
    "dnc": -20,
}

# Phase 3 Loop 1: Custom Field Boost Configuration
CUSTOM_FIELD_BOOST_MAP = {
    "pre_approval_status": {
        "values": ["approved", "pre-approved"],
        "boost": 15,
    },
    "budget": {
        "threshold": 500000,
        "boost": 10,
        "field_type": "numeric",
    },
    "timeline": {
        "values": ["immediate", "asap", "urgent"],
        "boost": 12,
    },
    "property_type": {
        "values": ["investment", "cash-buyer"],
        "boost": 8,
    },
}

# Maximum total boost cap to prevent over-inflation
MAX_BOOST_CAP = 30


class LeadIntentDecoder:
    """
    Decodes lead intent using linguistic markers and behavioral signals.
    Implements FRS (Financial Readiness) and PCS (Psychological Commitment) scoring.
    """

    def __init__(self, ghl_client: Optional[EnhancedGHLClient] = None, industry_config: Optional["IndustryConfig"] = None):
        self.ghl_client = ghl_client

        # Load industry config for config-first marker initialization

        cfg = industry_config
        self._cfg = cfg

        # Motivation Markers (config-first, hardcoded fallback)
        self.high_intent_motivation = (
            cfg.intents.motivation.high if cfg and cfg.intents.motivation.high
            else ["need to sell fast", "relocating in 30 days", "behind on payments", "divorce", "estate", "probate"]
        )
        self.mixed_intent_motivation = (
            cfg.intents.motivation.medium if cfg and cfg.intents.motivation.medium
            else ["thinking about it", "might sell next year", "curious about value"]
        )
        self.low_intent_motivation = (
            cfg.intents.motivation.low if cfg and cfg.intents.motivation.low
            else ["just browsing", "not sure", "what if rates drop"]
        )

        # Timeline Markers
        self.high_intent_timeline = (
            cfg.intents.timeline.high if cfg and cfg.intents.timeline.high
            else ["asap", "30 days", "this month", "immediately"]
        )
        self.flexible_timeline = (
            cfg.intents.timeline.medium if cfg and cfg.intents.timeline.medium
            else ["soon", "this year", "flexible"]
        )
        self.vague_timeline = (
            cfg.intents.timeline.low if cfg and cfg.intents.timeline.low
            else ["eventually", "when the time is right", "maybe later"]
        )

        # Condition Markers
        self.realistic_condition = (
            cfg.intents.condition.high if cfg and cfg.intents.condition.high
            else ["as-is", "needs work", "fixer", "defect", "discount"]
        )
        self.negotiable_condition = (
            cfg.intents.condition.medium if cfg and cfg.intents.condition.medium
            else ["minor fixes", "flexible on condition"]
        )
        self.unrealistic_condition = (
            cfg.intents.condition.low if cfg and cfg.intents.condition.low
            else ["perfect", "turnkey", "premium pricing"]
        )

        # Price Markers
        self.price_aware = (
            cfg.intents.price.high if cfg and cfg.intents.price.high
            else ["zestimate", "comps", "comparable", "market value"]
        )
        self.price_flexible = (
            cfg.intents.price.medium if cfg and cfg.intents.price.medium
            else ["range", "open to expectations", "negotiable"]
        )

        # Buyer vs Seller Intent Markers
        self.buyer_markers = (
            cfg.intents.buyer_patterns if cfg and cfg.intents.buyer_patterns
            else [
                "looking for", "want to buy", "searching for", "need a home",
                "bedroom", "3 bed", "4 bed", "bd house", "buying",
                "pre-approved", "mortgage", "first time buyer", "house hunting",
                "move in", "looking to purchase", "budget", "under 700k", "under 500k",
            ]
        )
        self.seller_markers = (
            cfg.intents.seller_patterns if cfg and cfg.intents.seller_patterns
            else [
                "want to sell", "selling my", "sell my", "list my", "home value",
                "what's my home worth", "thinking about selling", "how much is my",
                "considering selling", "need to sell", "sell the house",
                "put my house on the market",
            ]
        )

    def detect_lead_type(self, conversation_history: List[Dict[str, str]]) -> str:
        """Detect whether lead is a buyer, seller, or unknown based on conversation."""
        all_text = " ".join([m.get("content", "").lower() for m in (conversation_history or [])])

        buyer_score = sum(1 for m in self.buyer_markers if m in all_text)
        seller_score = sum(1 for m in self.seller_markers if m in all_text)

        if seller_score > buyer_score:
            return "seller"
        elif buyer_score > seller_score:
            return "buyer"
        return "unknown"

    def _calculate_handoff_signals(self, conversation_history: List[Dict[str, str]]) -> tuple[float, float, List[str]]:
        """Calculate buyer/seller intent confidence scores for cross-bot handoff routing.

        Scans conversation history for buyer and seller intent patterns, computes
        confidence scores (0.0-1.0), and returns detected phrases for transparency.

        This method consolidates pattern matching previously duplicated in
        JorgeHandoffService.extract_intent_signals() and
        extract_intent_signals_from_history().

        Args:
            conversation_history: List of conversation message dicts with 'content' key.

        Returns:
            Tuple of (buyer_confidence, seller_confidence, detected_phrases)
            - buyer_confidence: 0.0-1.0 score (0.3 per pattern match, capped at 1.0)
            - seller_confidence: 0.0-1.0 score (0.3 per pattern match, capped at 1.0)
            - detected_phrases: List of human-readable phrases (e.g., ["buyer intent detected"])

        Example:
            >>> history = [{"content": "I want to buy a house with 3 bedrooms"}]
            >>> buyer_conf, seller_conf, phrases = decoder._calculate_handoff_signals(history)
            >>> buyer_conf
            0.6  # 2 matches: "want to buy", "3 bed"
            >>> phrases
            ["buyer intent detected"]
        """
        import re

        all_text = " ".join([m.get("content", "").lower() for m in (conversation_history or [])])

        # Pattern matching using regex for more precise detection
        # These patterns mirror JorgeHandoffService.BUYER_INTENT_PATTERNS / SELLER_INTENT_PATTERNS
        buyer_regex_patterns = [
            r"\bi\s+want\s+to\s+buy\b",
            r"\blooking\s+to\s+buy\b",
            r"\bbudget\b.*\$",
            r"\bpre[- ]?approv",
            r"\bpre[- ]?qualif",
            r"\bdown\s+payment\b",
            r"\bfha\b|\bva\s+loan\b|\bconventional\b",
            r"\bfind\s+(a|my)\s+(new\s+)?(home|house|place|property)\b",
        ]

        seller_regex_patterns = [
            r"\bsell\s+my\s+(home|house|property)\b",
            r"\bwhat'?s\s+my\s+home\s+worth\b",
            r"\bhome\s+valu",
            r"\bcma\b",
            r"\blist(ing)?\s+my\s+(home|house|property)\b",
            r"\bneed\s+to\s+sell\b",
            r"\bsell\s+before\s+buy",
            r"\bsell\s+first\b",
        ]

        buyer_matches = 0
        for pattern in buyer_regex_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                buyer_matches += 1

        seller_matches = 0
        for pattern in seller_regex_patterns:
            if re.search(pattern, all_text, re.IGNORECASE):
                seller_matches += 1

        # Score: each pattern match adds ~0.3, capped at 1.0
        buyer_confidence = min(1.0, buyer_matches * 0.3)
        seller_confidence = min(1.0, seller_matches * 0.3)

        # Collect human-readable phrases
        detected_phrases = []
        if buyer_matches > 0:
            detected_phrases.append("buyer intent detected")
        if seller_matches > 0:
            detected_phrases.append("seller intent detected")

        return buyer_confidence, seller_confidence, detected_phrases

    def analyze_lead(self, contact_id: str, conversation_history: List[Dict[str, str]]) -> LeadIntentProfile:
        """
        Main entry point for lead intent decoding.
        """
        logger.info(f"Decoding intent for lead {contact_id}")

        all_text = " ".join([m.get("content", "").lower() for m in (conversation_history or [])])

        # 1. Calculate Pillars
        motivation_data = self._analyze_motivation(all_text)
        timeline_data = self._analyze_timeline(all_text)
        condition_data = self._analyze_condition(all_text)
        price_data = self._analyze_price(all_text)

        # 2. Calculate FRS (config-driven weights with fallback)
        cfg = self._cfg
        weights = cfg.intents.scoring_weights if cfg and cfg.intents.scoring_weights else {}
        w_motivation = weights.get("motivation", 0.35)
        w_timeline = weights.get("timeline", 0.30)
        w_condition = weights.get("condition", 0.20)
        w_price = weights.get("price", 0.15)
        frs_total = (
            (motivation_data.score * w_motivation)
            + (timeline_data.score * w_timeline)
            + (condition_data.score * w_condition)
            + (price_data.score * w_price)
        )

        thresholds = cfg.intents.temperature_thresholds if cfg and cfg.intents.temperature_thresholds else {}
        hot_thresh = thresholds.get("hot", 75)
        warm_thresh = thresholds.get("warm", 50)
        lukewarm_thresh = thresholds.get("lukewarm", 25)
        frs_classification = "Cold"
        if frs_total >= hot_thresh:
            frs_classification = "Hot"
        elif frs_total >= warm_thresh:
            frs_classification = "Warm"
        elif frs_total >= lukewarm_thresh:
            frs_classification = "Lukewarm"

        frs_score = FinancialReadinessScore(
            total_score=round(frs_total, 2),
            motivation=motivation_data,
            timeline=timeline_data,
            condition=condition_data,
            price=price_data,
            classification=frs_classification,
        )

        # 3. Calculate PCS
        pcs_score = self._calculate_pcs(conversation_history)

        # 4. Determine Next Best Action
        next_action = "Nurture - Low Intent"
        if frs_classification == "Hot":
            next_action = "Urgent: Call Lead Immediately"
        elif frs_classification == "Warm":
            next_action = "Send Soft Check-in SMS"
        elif pcs_score.total_score > 70:
            next_action = "Schedule Property Tour"

        # 5. Detect buyer vs seller intent
        lead_type = self.detect_lead_type(conversation_history)

        # 6. Calculate handoff routing signals (new in 2026-02-15)
        buyer_confidence, seller_confidence, detected_phrases = self._calculate_handoff_signals(conversation_history)

        return LeadIntentProfile(
            lead_id=contact_id,
            frs=frs_score,
            pcs=pcs_score,
            lead_type=lead_type,
            next_best_action=next_action,
            buyer_intent_confidence=buyer_confidence,
            seller_intent_confidence=seller_confidence,
            detected_intent_phrases=detected_phrases,
        )

    async def analyze_lead_with_ghl(
        self,
        contact_id: str,
        conversation_history: List[Dict[str, str]],
        ghl_contact: Optional[GHLContact] = None,
    ) -> LeadIntentProfile:
        """
        Enhanced lead analysis that incorporates GHL contact data for better scoring.

        If ghl_contact is not provided but self.ghl_client is available, fetches the
        contact from GHL. Falls back to the standard analyze_lead() if GHL data is
        unavailable.

        Args:
            contact_id: The lead's GHL contact ID.
            conversation_history: List of conversation messages.
            ghl_contact: Pre-fetched GHLContact object (optional).

        Returns:
            LeadIntentProfile with GHL-boosted scores.
        """
        # Attempt to fetch GHL contact data if not provided
        if ghl_contact is None and self.ghl_client is not None:
            try:
                ghl_contact = await self.ghl_client.get_contact(contact_id)
            except Exception as e:
                logger.warning(
                    f"Failed to fetch GHL contact {contact_id}: {e}. Falling back to conversation-only analysis."
                )

        # Fall back to standard analysis if no GHL data available
        if ghl_contact is None:
            logger.info(f"No GHL data for {contact_id}, using conversation-only analysis")
            return self.analyze_lead(contact_id, conversation_history)

        # Run standard conversation-based analysis first
        profile = self.analyze_lead(contact_id, conversation_history)

        # Extract GHL data points
        try:
            ghl_data = {
                "tags": ghl_contact.tags or [],
                "custom_fields": ghl_contact.custom_fields or {},
                "source": ghl_contact.source,
                "date_added": ghl_contact.created_at,
                "last_activity": ghl_contact.last_activity_at or ghl_contact.updated_at,
            }
        except Exception as e:
            logger.warning(f"Error extracting GHL data for {contact_id}: {e}")
            return profile

        # Apply GHL-based boosts
        boosted_frs, boosted_pcs = self._apply_ghl_boosts(
            profile.frs.total_score,
            profile.pcs.total_score,
            ghl_data,
        )

        # Reclassify FRS based on boosted score
        frs_classification = "Cold"
        if boosted_frs >= 75:
            frs_classification = "Hot"
        elif boosted_frs >= 50:
            frs_classification = "Warm"
        elif boosted_frs >= 25:
            frs_classification = "Lukewarm"

        # Build updated FRS with boosted total
        updated_frs = FinancialReadinessScore(
            total_score=round(boosted_frs, 2),
            motivation=profile.frs.motivation,
            timeline=profile.frs.timeline,
            condition=profile.frs.condition,
            price=profile.frs.price,
            classification=frs_classification,
        )

        # Build updated PCS with boosted total
        updated_pcs = PsychologicalCommitmentScore(
            total_score=round(boosted_pcs, 2),
            response_velocity_score=profile.pcs.response_velocity_score,
            message_length_score=profile.pcs.message_length_score,
            question_depth_score=profile.pcs.question_depth_score,
            objection_handling_score=profile.pcs.objection_handling_score,
            call_acceptance_score=profile.pcs.call_acceptance_score,
        )

        # Redetermine next best action with boosted scores
        next_action = "Nurture - Low Intent"
        if frs_classification == "Hot":
            next_action = "Urgent: Call Lead Immediately"
        elif frs_classification == "Warm":
            next_action = "Send Soft Check-in SMS"
        elif updated_pcs.total_score > 70:
            next_action = "Schedule Property Tour"

        return LeadIntentProfile(
            lead_id=contact_id,
            frs=updated_frs,
            pcs=updated_pcs,
            lead_type=profile.lead_type,
            next_best_action=next_action,
            # Preserve handoff signals from original profile (calculated in analyze_lead)
            buyer_intent_confidence=profile.buyer_intent_confidence,
            seller_intent_confidence=profile.seller_intent_confidence,
            detected_intent_phrases=profile.detected_intent_phrases,
        )

    def _apply_ghl_boosts(
        self,
        frs_score: float,
        pcs_score: float,
        ghl_data: Dict[str, Any],
    ) -> tuple:
        """
        Apply FRS and PCS boosts/penalties based on GHL contact data.

        Phase 3 Loop 1 Enhancement:
        - Tag-based boosts using TAG_BOOST_MAP configuration
        - Custom field boosts using CUSTOM_FIELD_BOOST_MAP configuration
        - Lead age: < 7 days → +10 FRS (fresh), > 90 days → -10 FRS (stale)
        - Engagement recency: < 3 days → +10 PCS velocity, > 30 days → -15 PCS
        - Max boost cap: +30 to prevent over-inflation

        Args:
            frs_score: Base FRS total score from conversation analysis.
            pcs_score: Base PCS total score from conversation analysis.
            ghl_data: Extracted GHL data dict with tags, custom_fields, source,
                      date_added, and last_activity.

        Returns:
            Tuple of (boosted_frs, boosted_pcs) clamped to 0-100.
        """
        frs_boost = 0.0
        pcs_boost = 0.0
        applied_boosts = []  # For logging which boosts were applied

        tags = [t.lower() for t in ghl_data.get("tags", [])]

        # --- Tag-based FRS boosts (Phase 3 Loop 1) ---
        for tag_key, boost_value in TAG_BOOST_MAP.items():
            if tag_key in tags:
                frs_boost += boost_value
                applied_boosts.append(f"tag:{tag_key}({boost_value:+.0f})")
                logger.debug(f"Tag boost applied: {tag_key} → {boost_value:+.0f} FRS")

        # --- Custom field boosts (Phase 3 Loop 1) ---
        custom_fields = ghl_data.get("custom_fields", {})

        for field_name, field_config in CUSTOM_FIELD_BOOST_MAP.items():
            field_value = custom_fields.get(field_name)

            if field_value is None:
                continue

            # Handle numeric field types (e.g., budget)
            if field_config.get("field_type") == "numeric":
                try:
                    numeric_value = float(field_value)
                    threshold = field_config.get("threshold", 0)
                    if numeric_value >= threshold:
                        boost = field_config["boost"]
                        frs_boost += boost
                        applied_boosts.append(f"field:{field_name}>={threshold}({boost:+.0f})")
                        logger.debug(
                            f"Custom field boost applied: {field_name}={numeric_value} ≥ {threshold} → {boost:+.0f} FRS"
                        )
                except (ValueError, TypeError):
                    logger.debug(f"Could not parse numeric value for {field_name}: {field_value}")

            # Handle value-based matching (e.g., pre_approval_status, timeline)
            elif "values" in field_config:
                field_value_lower = str(field_value).lower()
                matching_values = [v.lower() for v in field_config["values"]]
                if field_value_lower in matching_values:
                    boost = field_config["boost"]
                    frs_boost += boost
                    applied_boosts.append(f"field:{field_name}={field_value}({boost:+.0f})")
                    logger.debug(
                        f"Custom field boost applied: {field_name}={field_value} → {boost:+.0f} FRS"
                    )

        # --- Lead age factor (days since date_added) ---
        date_added = ghl_data.get("date_added")
        if date_added is not None:
            try:
                now = datetime.now(timezone.utc)
                if date_added.tzinfo is None:
                    date_added = date_added.replace(tzinfo=timezone.utc)
                lead_age_days = (now - date_added).days
                if lead_age_days <= 7:
                    age_boost = 10  # Fresh lead
                    frs_boost += age_boost
                    applied_boosts.append(f"age:{lead_age_days}d({age_boost:+.0f})")
                elif lead_age_days <= 30:
                    age_boost = 5  # Recent lead
                    frs_boost += age_boost
                    applied_boosts.append(f"age:{lead_age_days}d({age_boost:+.0f})")
                elif lead_age_days > 90:
                    age_boost = -10  # Stale lead
                    frs_boost += age_boost
                    applied_boosts.append(f"age:{lead_age_days}d({age_boost:+.0f})")
            except Exception as e:
                logger.debug(f"Could not compute lead age: {e}")

        # --- Engagement recency factor (days since last_activity) ---
        last_activity = ghl_data.get("last_activity")
        if last_activity is not None:
            try:
                now = datetime.now(timezone.utc)
                if last_activity.tzinfo is None:
                    last_activity = last_activity.replace(tzinfo=timezone.utc)
                days_since_activity = (now - last_activity).days
                if days_since_activity <= 3:
                    engagement_boost = 10  # Very recent engagement
                    pcs_boost += engagement_boost
                    applied_boosts.append(f"engagement:{days_since_activity}d({engagement_boost:+.0f}PCS)")
                elif days_since_activity <= 7:
                    engagement_boost = 5  # Recent engagement
                    pcs_boost += engagement_boost
                    applied_boosts.append(f"engagement:{days_since_activity}d({engagement_boost:+.0f}PCS)")
                elif days_since_activity > 30:
                    engagement_boost = -15  # Disengaged
                    pcs_boost += engagement_boost
                    applied_boosts.append(f"engagement:{days_since_activity}d({engagement_boost:+.0f}PCS)")
            except Exception as e:
                logger.debug(f"Could not compute engagement recency: {e}")

        # --- Apply boost cap (Phase 3 Loop 1) ---
        original_frs_boost = frs_boost
        if frs_boost > MAX_BOOST_CAP:
            frs_boost = MAX_BOOST_CAP
            logger.info(f"FRS boost capped: {original_frs_boost:.1f} → {MAX_BOOST_CAP}")
            applied_boosts.append(f"CAPPED({original_frs_boost:.1f}→{MAX_BOOST_CAP})")

        boosted_frs = max(0, min(100, frs_score + frs_boost))
        boosted_pcs = max(0, min(100, pcs_score + pcs_boost))

        logger.info(
            f"GHL boosts applied: FRS {frs_score:.1f} → {boosted_frs:.1f} "
            f"({frs_boost:+.1f}), PCS {pcs_score:.1f} → {boosted_pcs:.1f} ({pcs_boost:+.1f})"
        )
        logger.info(f"Boost breakdown: {', '.join(applied_boosts) if applied_boosts else 'none'}")

        return boosted_frs, boosted_pcs

    def _analyze_motivation(self, text: str) -> MotivationSignals:
        detected = [m for m in self.high_intent_motivation if m in text]
        score = 50
        category = "Mixed Intent"

        if detected:
            score = 85
            category = "High Intent"
        elif any(m in text for m in self.low_intent_motivation):
            score = 20
            category = "Low Intent"

        return MotivationSignals(score=score, detected_markers=detected, category=category)

    def _analyze_timeline(self, text: str) -> TimelineCommitment:
        score = 50
        category = "Flexible"
        if any(m in text for m in self.high_intent_timeline):
            score = 90
            category = "High Commitment"
        elif any(m in text for m in self.vague_timeline):
            score = 20
            category = "Vague"
        return TimelineCommitment(score=score, category=category)

    def _analyze_condition(self, text: str) -> ConditionRealism:
        score = 50
        category = "Negotiable"
        if any(m in text for m in self.realistic_condition):
            score = 85
            category = "Realistic"
        elif any(m in text for m in self.unrealistic_condition):
            score = 20
            category = "Unrealistic"
        return ConditionRealism(score=score, category=category)

    def _analyze_price(self, text: str) -> PriceResponsiveness:
        score = 50
        category = "Price-Flexible"
        zestimate = "zestimate" in text
        if any(m in text for m in self.price_aware):
            score = 85
            category = "Price-Aware"
        return PriceResponsiveness(score=score, zestimate_mentioned=zestimate, category=category)

    def _calculate_pcs(self, history: List[Dict[str, str]]) -> PsychologicalCommitmentScore:
        if not history:
            return PsychologicalCommitmentScore(
                total_score=0,
                response_velocity_score=0,
                message_length_score=0,
                question_depth_score=0,
                objection_handling_score=0,
                call_acceptance_score=0,
            )

        # Message Length
        avg_len = sum(len(m.get("content", "").split()) for m in history) / len(history)
        len_score = min(100, int(avg_len * 4))

        # Question Depth
        q_count = sum(1 for m in history if "?" in m.get("content", ""))
        q_score = min(100, q_count * 25)

        # Call Acceptance
        call_keywords = ["call", "phone", "tour", "schedule", "meet"]
        call_score = (
            100 if any(kw in " ".join([m.get("content", "").lower() for m in history]) for kw in call_keywords) else 0
        )

        # Heuristics for others
        velocity_score = 80
        objection_score = 60

        total = (
            (velocity_score * 0.20)
            + (len_score * 0.15)
            + (q_score * 0.20)
            + (objection_score * 0.25)
            + (call_score * 0.20)
        )

        return PsychologicalCommitmentScore(
            total_score=round(total, 2),
            response_velocity_score=velocity_score,
            message_length_score=len_score,
            question_depth_score=q_score,
            objection_handling_score=objection_score,
            call_acceptance_score=call_score,
        )
