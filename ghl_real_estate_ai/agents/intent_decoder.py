"""
Intent Decoder Engine - Section 1 of 2026 Strategic Roadmap
Calculates Financial Readiness Score (FRS) and Psychological Commitment Score (PCS).
"""

import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

class IntentPillars(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    motivation: float = Field(0.0, ge=0, le=100)
    timeline: float = Field(0.0, ge=0, le=100)
    condition: float = Field(0.0, ge=0, le=100)
    price: float = Field(0.0, ge=0, le=100)

class PCSMetrics(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    response_velocity: float = Field(0.0, ge=0, le=100)
    message_length: float = Field(0.0, ge=0, le=100)
    question_depth: float = Field(0.0, ge=0, le=100)
    objection_handling: float = Field(0.0, ge=0, le=100)
    call_acceptance: float = Field(0.0, ge=0, le=100)

class LeadIntentProfile(BaseModel):
    model_config = ConfigDict(use_enum_values=True)
    contact_id: str
    frs_score: float = Field(0.0, ge=0, le=100)
    pcs_score: float = Field(0.0, ge=0, le=100)
    pillars: IntentPillars
    pcs_metrics: PCSMetrics
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    insights: List[str] = []

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

    def analyze_lead(self, contact_id: str, conversation_history: List[Dict[str, str]]) -> LeadIntentProfile:
        """
        Main entry point for lead intent decoding.
        """
        logger.info(f"Decoding intent for lead {contact_id}")
        
        all_text = " ".join([m.get("content", "").lower() for m in conversation_history])
        
        # Calculate Pillars
        motivation_score = self._score_pillar(all_text, self.high_intent_motivation, self.mixed_intent_motivation, self.low_intent_motivation)
        timeline_score = self._score_pillar(all_text, self.high_intent_timeline, self.flexible_timeline, self.vague_timeline)
        condition_score = self._score_pillar(all_text, self.realistic_condition, self.negotiable_condition, self.unrealistic_condition)
        price_score = self._score_pillar(all_text, self.price_aware, self.price_flexible, [])

        pillars = IntentPillars(
            motivation=motivation_score,
            timeline=timeline_score,
            condition=condition_score,
            price=price_score
        )

        # Calculate FRS
        frs_score = (motivation_score * 0.35) + (timeline_score * 0.30) + (condition_score * 0.20) + (price_score * 0.15)

        # Calculate PCS Metrics (Heuristic for now)
        pcs_metrics = self._calculate_pcs_metrics(conversation_history)
        
        # Calculate PCS
        pcs_score = (pcs_metrics.response_velocity * 0.20) + \
                    (pcs_metrics.message_length * 0.15) + \
                    (pcs_metrics.question_depth * 0.20) + \
                    (pcs_metrics.objection_handling * 0.25) + \
                    (pcs_metrics.call_acceptance * 0.20)

        insights = self._generate_insights(pillars, pcs_metrics)

        return LeadIntentProfile(
            contact_id=contact_id,
            frs_score=round(frs_score, 2),
            pcs_score=round(pcs_score, 2),
            pillars=pillars,
            pcs_metrics=pcs_metrics,
            insights=insights
        )

    def _score_pillar(self, text: str, high: List[str], mixed: List[str], low: List[str]) -> float:
        """Scores a specific intent pillar based on linguistic markers."""
        score = 50.0 # Baseline
        
        if any(marker in text for marker in high):
            score += 35
        elif any(marker in text for marker in mixed):
            score += 10
        elif any(marker in text for marker in low):
            score -= 30
            
        return max(0.0, min(100.0, score))

    def _calculate_pcs_metrics(self, history: List[Dict[str, str]]) -> PCSMetrics:
        """Heuristic calculation of psychological commitment signals."""
        if not history:
            return PCSMetrics()

        # Message Length
        avg_len = sum(len(m.get("content", "").split()) for m in history) / len(history)
        len_score = min(100, avg_len * 4) # 25 words = 100

        # Question Depth
        q_count = sum(1 for m in history if "?" in m.get("content", ""))
        q_score = min(100, q_count * 25) # 4 questions = 100

        # Call Acceptance
        call_keywords = ["call", "phone", "tour", "schedule", "meet"]
        call_score = 100 if any(kw in " ".join([m.get("content", "").lower() for m in history]) for kw in call_keywords) else 0

        # Placeholder for complex velocity and objection handling
        return PCSMetrics(
            response_velocity=80.0, # Mocked
            message_length=len_score,
            question_depth=q_score,
            objection_handling=60.0, # Mocked
            call_acceptance=call_score
        )

    def _generate_insights(self, pillars: IntentPillars, pcs: PCSMetrics) -> List[str]:
        """Generates human-readable insights based on scores."""
        insights = []
        if pillars.motivation > 75:
            insights.append("High motivation detected - prioritize immediate outreach.")
        if pillars.timeline > 75:
            insights.append("Urgent timeline confirmed (30-45 day window).")
        if pcs.call_acceptance > 50:
            insights.append("Lead is open to direct voice communication.")
        if pillars.condition < 40:
            insights.append("Alert: Potential condition/price mismatch.")
        return insights