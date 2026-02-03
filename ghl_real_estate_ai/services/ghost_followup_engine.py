"""
Ghost-in-the-Machine Follow-Up Engine - Section 2 of 2026 Strategic Roadmap
Autonomous multi-channel re-engagement using stall-breaking logic and FRS-driven branching.
"""

import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from ghl_real_estate_ai.agents.intent_decoder import LeadIntentDecoder
from ghl_real_estate_ai.agents.cma_generator import CMAGenerator
from ghl_real_estate_ai.utils.pdf_renderer import PDFRenderer
from ghl_real_estate_ai.services.claude_orchestrator import get_claude_orchestrator

logger = logging.getLogger(__name__)

class GhostState(BaseModel):
    contact_id: str
    current_day: int = 0
    frs_score: float = 0.0
    status: str = "active" # active, ghosted, converted, archived
    last_touchpoint: Optional[datetime] = None
    objections_detected: List[str] = []
    property_address: Optional[str] = None

class GhostFollowUpEngine:
    """
    Implements the 3-7-30 Day Follow-Up Architecture with stall-breaking logic.
    """
    
    def __init__(self):
        self.decoder = LeadIntentDecoder()
        self.claude = get_claude_orchestrator()
        self.cma_generator = CMAGenerator()
        # Ensure we use the correct relative path for data
        import os
        data_path = os.path.join(os.path.dirname(__file__), "..", "data", "stall_breakers.json")
        try:
            with open(data_path, "r") as f:
                self.stall_breakers = json.load(f)
        except FileNotFoundError:
            # Fallback for relative execution
            with open("ghl_real_estate_ai/data/stall_breakers.json", "r") as f:
                self.stall_breakers = json.load(f)

    async def process_lead_step(self, ghost_state: GhostState, history: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Determines the next action for a lead based on their current 'ghost day'.
        """
        # Re-score FRS using the unified decoder
        profile = self.decoder.analyze_lead(ghost_state.contact_id, history)
        ghost_state.frs_score = profile.frs.total_score
        
        # Detect objections
        ghost_state.objections_detected = await self.detect_objections(history)
        
        day = ghost_state.current_day
        action = {"day": day, "channel": None, "content": None}

        if day <= 0:
            action = await self._day_0_initial_contact(ghost_state)
        elif day <= 3:
            action = await self._day_3_sms_checkin(ghost_state)
        elif day <= 7:
            action = await self._day_7_voice_stallbreaker(ghost_state)
        elif day <= 14:
            action = await self._day_14_email_cma(ghost_state)
        elif day <= 30:
            action = await self._day_30_final_nudge(ghost_state)
            
        return action

    async def _day_0_initial_contact(self, state: GhostState) -> Dict[str, Any]:
        return {
            "channel": "sms",
            "content": "Thanks for reaching out! Qualifying now...",
            "logic": "FRS Scored immediately."
        }

    async def _day_3_sms_checkin(self, state: GhostState) -> Dict[str, Any]:
        """
        Logic:
        - IF FRS > 60: 'Buyers interested' frame
        - IF FRS 40-60: 'Information' frame
        - IF FRS < 40: 'No rush' frame
        """
        if state.frs_score > 60:
            frame = "We have qualified buyers interested in your market RIGHT NOW. Still thinking about it?"
        elif state.frs_score >= 40:
            frame = "Just wanted to share some new market data for your neighborhood. Still exploring?"
        else:
            frame = "No rush at all, but checking if you have any new questions about the property value."
            
        return {
            "channel": "sms",
            "content": frame,
            "logic": f"FRS {state.frs_score} - Urgency Frame"
        }

    async def _day_7_voice_stallbreaker(self, state: GhostState) -> Dict[str, Any]:
        """AI Voice Agent + Stall-Breaker #1"""
        return {
            "channel": "voice",
            "content": self.stall_breakers["market_shift"]["question"],
            "logic": "Retell AI Voice Call"
        }

    async def _day_14_email_cma(self, state: GhostState) -> Dict[str, Any]:
        """Email - Objection Handler + CMA Injection"""
        address = state.property_address or "123 Main St, Austin, TX"
        report = await self.cma_generator.generate_report(address)
        pdf_url = PDFRenderer.generate_pdf_url(report)
        
        return {
            "channel": "email",
            "content": f"Zillow's estimate for {address} is off by ${report.zillow_variance_abs:,.0f}. Here is your actual value report: {pdf_url}",
            "logic": "CMA PDF Auto-Injection",
            "pdf_url": pdf_url
        }

    async def detect_objections(self, history: List[Dict[str, str]]) -> List[str]:
        """Detects price or timeline objections in conversation history."""
        last_msg = history[-1]['content'].lower() if history else ""
        objections = []
        
        if any(k in last_msg for k in ["price", "worth", "value", "zestimate", "too expensive"]):
            objections.append("price")
        if any(k in last_msg for k in ["wait", "next year", "not ready", "not sure"]):
            objections.append("timeline")
            
        return objections

    async def _day_30_final_nudge(self, state: GhostState) -> Dict[str, Any]:
        """
        Day 30 - Final Nudge + Re-Qualification.
        Last-chance follow-up with a gentle tone and CMA/market update value-add.
        Outcome: Archive if unresponsive or route to Jorge for live handoff.
        """
        address = state.property_address or "your area"

        if state.frs_score > 60:
            content = (
                f"Hey, new comps just dropped near {address}. "
                f"I ran an updated CMA. Want me to send it over or are you done looking?"
            )
            logic = f"FRS {state.frs_score} - High intent final nudge with CMA offer"
        elif state.frs_score >= 40:
            content = (
                f"Market shifted around {address} since we last talked. "
                f"Worth a second look or should I close your file?"
            )
            logic = f"FRS {state.frs_score} - Mid intent final nudge with market update"
        else:
            content = (
                f"Last check: still thinking about {address}? "
                f"If not, I'll close your file. No hard feelings."
            )
            logic = f"FRS {state.frs_score} - Low intent graceful close"

        return {
            "channel": "sms",
            "content": content,
            "logic": logic
        }

    def get_stall_breaker(self, objection_type: str) -> str:
        """Returns a specific confrontational question from the library."""
        return self.stall_breakers.get(objection_type, {}).get("question", "Still thinking about it?")

_ghost_engine = None

def get_ghost_followup_engine() -> GhostFollowUpEngine:
    global _ghost_engine
    if _ghost_engine is None:
        _ghost_engine = GhostFollowUpEngine()
    return _ghost_engine