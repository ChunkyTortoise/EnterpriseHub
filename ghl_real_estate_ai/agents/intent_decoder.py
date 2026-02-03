"""
Intent Decoder Engine - Section 1 of 2026 Strategic Roadmap
Calculates Financial Readiness Score (FRS) and Psychological Commitment Score (PCS).
Updated to use unified models in ghl_real_estate_ai.models.lead_scoring.
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from ghl_real_estate_ai.models.lead_scoring import (
    LeadIntentProfile,
    FinancialReadinessScore,
    PsychologicalCommitmentScore,
    MotivationSignals,
    TimelineCommitment,
    ConditionRealism,
    PriceResponsiveness
)

logger = logging.getLogger(__name__)

class LeadIntentDecoder:
    """
    Decodes lead intent using linguistic markers and behavioral signals.
    Implements FRS (Financial Readiness) and PCS (Psychological Commitment) scoring.
    """
    
    def __init__(self):
        # Motivation Markers
        self.high_intent_motivation = ["need to sell fast", "relocating in 30 days", "behind on payments", "divorce", "estate", "probate"]
        self.mixed_intent_motivation = ["thinking about it", "might sell next year", "curious about value"]
        self.low_intent_motivation = ["just browsing", "not sure", "what if rates drop"]
        
        # Timeline Markers
        self.high_intent_timeline = ["asap", "30 days", "this month", "immediately"]
        self.flexible_timeline = ["soon", "this year", "flexible"]
        self.vague_timeline = ["eventually", "when the time is right", "maybe later"]

        # Condition Markers
        self.realistic_condition = ["as-is", "needs work", "fixer", "defect", "discount"]
        self.negotiable_condition = ["minor fixes", "flexible on condition"]
        self.unrealistic_condition = ["perfect", "turnkey", "premium pricing"]

        # Price Markers
        self.price_aware = ["zestimate", "comps", "comparable", "market value"]
        self.price_flexible = ["range", "open to expectations", "negotiable"]

        # Buyer vs Seller Intent Markers
        self.buyer_markers = [
            "looking for", "want to buy", "searching for", "need a home",
            "bedroom", "3 bed", "4 bed", "bd house", "buying", "pre-approved",
            "mortgage", "first time buyer", "house hunting", "move in",
            "looking to purchase", "budget", "under 700k", "under 500k"
        ]
        self.seller_markers = [
            "want to sell", "selling my", "sell my", "list my",
            "home value", "what's my home worth", "thinking about selling",
            "how much is my", "considering selling", "need to sell",
            "sell the house", "put my house on the market"
        ]

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

        # 2. Calculate FRS
        frs_total = (motivation_data.score * 0.35) + \
                    (timeline_data.score * 0.30) + \
                    (condition_data.score * 0.20) + \
                    (price_data.score * 0.15)
        
        frs_classification = "Cold"
        if frs_total >= 75: frs_classification = "Hot"
        elif frs_total >= 50: frs_classification = "Warm"
        elif frs_total >= 25: frs_classification = "Lukewarm"

        frs_score = FinancialReadinessScore(
            total_score=round(frs_total, 2),
            motivation=motivation_data,
            timeline=timeline_data,
            condition=condition_data,
            price=price_data,
            classification=frs_classification
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

        return LeadIntentProfile(
            lead_id=contact_id,
            frs=frs_score,
            pcs=pcs_score,
            lead_type=lead_type,
            next_best_action=next_action
        )

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
                call_acceptance_score=0
            )

        # Message Length
        avg_len = sum(len(m.get("content", "").split()) for m in history) / len(history)
        len_score = min(100, int(avg_len * 4))

        # Question Depth
        q_count = sum(1 for m in history if "?" in m.get("content", ""))
        q_score = min(100, q_count * 25)

        # Call Acceptance
        call_keywords = ["call", "phone", "tour", "schedule", "meet"]
        call_score = 100 if any(kw in " ".join([m.get("content", "").lower() for m in history]) for kw in call_keywords) else 0

        # Heuristics for others
        velocity_score = 80
        objection_score = 60

        total = (velocity_score * 0.20) + \
                (len_score * 0.15) + \
                (q_score * 0.20) + \
                (objection_score * 0.25) + \
                (call_score * 0.20)

        return PsychologicalCommitmentScore(
            total_score=round(total, 2),
            response_velocity_score=velocity_score,
            message_length_score=len_score,
            question_depth_score=q_score,
            objection_handling_score=objection_score,
            call_acceptance_score=call_score
        )
