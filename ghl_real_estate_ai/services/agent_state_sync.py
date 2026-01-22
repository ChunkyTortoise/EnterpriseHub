"""
Agent State Sync Service (AG-UI Protocol)
Handles real-time state synchronization between AI Agents and the Frontend.
Implements a simplified version of RFC 6902 (JSON Patch) for State Deltas.
"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional
import copy
import asyncio
from ghl_real_estate_ai.services.cache_service import get_cache_service
from ghl_real_estate_ai.services.lead_scorer import LeadScorer
from ghl_real_estate_ai.services.market_prediction_engine import MarketPredictionEngine
from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

class AgentStateSync:
    """
    Manages global AI state and computes incremental deltas.
    Used to keep the Elite Dashboard in sync with agent "thoughts" and actions.
    """

    def __init__(self):
        self.cache = get_cache_service()
        self.lead_scorer = LeadScorer() # Initialize LeadScorer
        self.market_predictor = MarketPredictionEngine() # Initialize MarketPredictionEngine

        self.state: Dict[str, Any] = {
            "agents": {
                "Orchestrator": {"status": "Active", "health": 100, "uptime": "32d", "load": "Idle"},
                "SalesBot-Alpha": {"status": "Active", "health": 98, "uptime": "14d", "load": "Low"},
                "SellerBot-Beta": {"status": "Active", "health": 95, "uptime": "14d", "load": "Medium"},
                "LeadScorer": {"status": "Active", "health": 100, "uptime": "32d", "load": "Idle"},
                "MarketBot": {"status": "Active", "health": 99, "uptime": "5d", "load": "Low"},
                "WhatsAppBot": {"status": "Active", "health": 100, "uptime": "2d", "load": "Idle"},
                "ObjectionBot": {"status": "Active", "health": 100, "uptime": "1d", "load": "Idle"},
                "ComplianceBot": {"status": "Active", "health": 100, "uptime": "1d", "load": "Idle"},
                "RevenueBot": {"status": "Active", "health": 100, "uptime": "1d", "load": "Idle"},
            },
            "market_predictions": [],
            "kpis": {
                "total_leads": 0,
                "response_rate": 94.2,
                "conversion": 4.2,
                "total_revenue": 452652,
                "roi": 15.9
            },
            "leads": [],
            "recent_thoughts": [],
            "lead_events": {}, # New: Map of lead_id -> list of events

            "system_health": "optimal",
            "last_updated": datetime.now().isoformat()
        }

        self.previous_state = copy.deepcopy(self.state)
        self._initialization_lock = asyncio.Lock()
        self._is_initialized = False

        logger.info("AgentStateSync initialized (lazy)")

    async def _ensure_initialized(self):
        """Ensure the state is fully initialized"""
        if self._is_initialized:
            return
            
        async with self._initialization_lock:
            if self._is_initialized:
                return
            
            # Start background initialization
            await self._load_initial_state()
            await self._initialize_leads()
            await self._initialize_market_predictions()
            
            # Ensure lead_events exists in state
            if "lead_events" not in self.state:
                self.state["lead_events"] = {}

            self._is_initialized = True

    async def _initialize_market_predictions(self):
        # Fetch market predictions for Rancho Cucamonga (example location)
        # In a real scenario, this might be dynamic based on user location or agent focus
        rc_predictions = await self.market_predictor.get_area_predictions("Rancho Cucamonga")
        
        # Transform predictions to match the dashboard's expected format
        transformed_predictions = []
        for pred in rc_predictions:
            transformed_predictions.append({
                "neighborhood": pred["area"],
                "prediction": f"{pred['predicted_growth']:.1f}%",
                "horizon": f"{pred['horizon_months']} Months",
                "confidence": pred["confidence"].capitalize(),
                "trend": "up" if pred["predicted_growth"] > 0 else "down"
            })
        self.state["market_predictions"] = transformed_predictions
        await self.cache.set("agent_state_sync_state", self.state)


    async def _initialize_leads(self):
        sample_leads_data = [
            {
                "id": "L1", "name": "Sarah Jenkins", "status": "Hot",
                "engagement_status": "offer_sent",
                "current_step": "facilitate_offer",
                "extracted_preferences": {
                    "budget": 500000, "location": "Austin, TX", "timeline": "ASAP",
                    "bedrooms": 3, "motivation": "Relocating for job"
                }
            },
            {
                "id": "L2", "name": "Michael Chen", "status": "Warm",
                "engagement_status": "qualified",
                "current_step": "post_showing_survey",
                "extracted_preferences": {
                    "budget": 350000, "location": "Miami, FL", "timeline": "3 months"
                }
            },
            {
                "id": "L3", "name": "Emma Wilson", "status": "Cold",
                "engagement_status": "new",
                "current_step": "analyze_intent",
                "extracted_preferences": {
                    "location": "Dallas, TX"
                }
            }
        ]

        leads_with_scores = []
        for lead_data in sample_leads_data:
            score_details = await self.lead_scorer.calculate_with_reasoning(lead_data["extracted_preferences"])
            leads_with_scores.append({
                **lead_data,
                "score": score_details["score"],
                "classification": score_details["classification"],
                "reasoning": score_details["reasoning"],
                "last_action": "System Generated",
                "timestamp": datetime.now().isoformat()
            })
        self.state["leads"] = leads_with_scores
        self.state["kpis"]["total_leads"] = len(leads_with_scores)
        await self.cache.set("agent_state_sync_state", self.state)


    async def _load_initial_state(self):
        cached_state = await self.cache.get("agent_state_sync_state")
        if cached_state:
            self.state = cached_state
            self.previous_state = copy.deepcopy(self.state)
        else:
            await self.cache.set("agent_state_sync_state", self.state)

    def get_state(self) -> Dict[str, Any]:
        """Return the current full state"""
        return self.state

    async def update_state(self, path: str, value: Any):
        """ Surogately update state and track changes """
        await self._ensure_initialized()
        self.previous_state = copy.deepcopy(self.state)
        
        # Simple path-based update (e.g., "kpis/total_leads")
        parts = path.split('/')
        target = self.state
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]
        
        target[parts[-1]] = value
        self.state["last_updated"] = datetime.now().isoformat()
        await self.cache.set("agent_state_sync_state", self.state)

    def get_delta(self) -> List[Dict[str, Any]]:
        """
        Compute a simplified JSON Patch delta between previous and current state.
        Format: [{"op": "replace", "path": "/kpis/total_leads", "value": 12700}]
        """
        deltas = []
        
        def compare(prev, curr, path=""):
            if isinstance(curr, dict):
                for key in curr:
                    new_path = f"{path}/{key}"
                    if key not in prev:
                        deltas.append({"op": "add", "path": new_path, "value": curr[key]})
                    else:
                        compare(prev[key], curr[key], new_path)
                for key in prev:
                    if key not in curr:
                        deltas.append({"op": "remove", "path": f"{path}/{key}"})
            elif prev != curr:
                deltas.append({"op": "replace", "path": path, "value": curr})

        compare(self.previous_state, self.state)
        return deltas

    async def record_agent_thought(self, agent_id: str, thought: str, status: str = "Success"):
        """High-level helper to update agent thoughts"""
        await self._ensure_initialized()
        new_thought = {
            "agent": agent_id,
            "task": thought,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to beginning of list
        thoughts = self.state.get("recent_thoughts", [])
        thoughts.insert(0, new_thought)
        
        # Keep only last 10
        self.state["recent_thoughts"] = thoughts[:10]
        self.state["last_updated"] = datetime.now().isoformat()
        await self.cache.set("agent_state_sync_state", self.state)

    async def record_lead_event(self, lead_id: str, source: str, event: str, event_type: str = "thought"):
        """
        Records a specific event for a lead.
        source: "AI", "GHL", "System"
        event_type: "thought", "action", "node", "sms", "error"
        """
        await self._ensure_initialized()
        
        if "lead_events" not in self.state:
            self.state["lead_events"] = {}
            
        if lead_id not in self.state["lead_events"]:
            self.state["lead_events"][lead_id] = []
            
        new_event = {
            "time": datetime.now().strftime("%I:%M %p"),
            "full_timestamp": datetime.now().isoformat(),
            "source": source,
            "event": event,
            "type": event_type
        }
        
        # Add to the beginning of the list
        self.state["lead_events"][lead_id].insert(0, new_event)
        
        # Keep only last 50 events per lead
        self.state["lead_events"][lead_id] = self.state["lead_events"][lead_id][:50]
        
        self.state["last_updated"] = datetime.now().isoformat()
        await self.cache.set("agent_state_sync_state", self.state)
        
        # Also mirror to recent_thoughts for global visibility if it's AI
        if source == "AI":
            await self.record_agent_thought(source, f"Lead {lead_id}: {event}")

    def get_lead_events(self, lead_id: str) -> List[Dict[str, Any]]:
        """Retrieve events for a specific lead"""
        if "lead_events" not in self.state:
            return []
        return self.state["lead_events"].get(lead_id, [])

# Singleton for prototype
sync_service = AgentStateSync()
