"""
LangGraph Lead Qualification Orchestrator

Unified state machine for complex lead qualification workflows.
Routes leads through appropriate qualification paths (seller/buyer/general)
based on tags, behavioral signals, and conversation state.

Integrates:
- Lead type classification (seller/buyer/general)
- Behavioral trigger analysis
- Compliance pre-checks
- Temperature scoring and handoff routing
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.graph import END, StateGraph

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Models
# ---------------------------------------------------------------------------


class LeadType(str, Enum):
    SELLER = "seller"
    BUYER = "buyer"
    GENERAL = "general"


class QualificationStage(str, Enum):
    CLASSIFY = "classify"
    ANALYZE = "analyze"
    COMPLIANCE = "compliance"
    QUALIFYING = "qualifying"
    SCORING = "scoring"
    COMPLETE = "complete"
    ERROR = "error"


class OrchestratorState(TypedDict):
    """State passed through every node of the qualification graph."""

    contact_id: str
    location_id: str
    message: str
    contact_tags: list
    contact_info: dict
    conversation_history: list
    # Classification
    lead_type: str
    qualification_stage: str
    # Behavioral
    behavioral_signals: dict
    # Compliance
    compliance_passed: bool
    compliance_reason: str
    # Qualification result
    response_content: str
    actions: list
    temperature: str
    is_qualified: bool
    scores: dict
    # Error
    error: str


@dataclass
class QualificationResult:
    """Returned to the caller after the graph completes."""

    success: bool
    response_content: str
    actions: list
    temperature: str
    lead_type: str
    is_qualified: bool
    behavioral_signals: dict
    qualification_stage: str
    scores: dict = field(default_factory=dict)
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Tag constants
# ---------------------------------------------------------------------------

SELLER_TAGS = {"Needs Qualifying"}
BUYER_TAGS = {"Buyer-Lead"}
DEACTIVATION_TAGS = {"AI-Off", "Qualified", "Stop-Bot", "Seller-Qualified"}

SELLER_INTENT_KEYWORDS = [
    "sell",
    "selling",
    "list",
    "listing",
    "what's my home worth",
    "home value",
    "cash offer",
    "downsize",
]
BUYER_INTENT_KEYWORDS = [
    "buy",
    "buying",
    "looking for",
    "house hunt",
    "bedroom",
    "pre-approved",
    "mortgage",
    "move to",
    "relocate",
]


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------


class LeadQualificationOrchestrator:
    """
    LangGraph-based orchestrator that processes a single webhook interaction
    through a classify → analyze → compliance → qualify → score pipeline.

    Usage::

        orchestrator = LeadQualificationOrchestrator(
            conversation_manager=cm,
            behavioral_detector=detector,   # optional
        )
        result = await orchestrator.process(
            contact_id="c_123",
            location_id="loc_456",
            message="I want to sell my home",
            contact_tags=["Needs Qualifying"],
            contact_info={"first_name": "Maria"},
        )
    """

    def __init__(
        self,
        conversation_manager=None,
        behavioral_detector=None,
    ):
        self.conversation_manager = conversation_manager
        self.behavioral_detector = behavioral_detector
        self._graph = self._build_graph()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process(
        self,
        contact_id: str,
        location_id: str,
        message: str,
        contact_tags: List[str],
        contact_info: Dict[str, Any],
        conversation_history: Optional[List[Dict]] = None,
    ) -> QualificationResult:
        """Run the full qualification pipeline and return a result."""
        initial_state: OrchestratorState = {
            "contact_id": contact_id,
            "location_id": location_id,
            "message": message,
            "contact_tags": contact_tags or [],
            "contact_info": contact_info or {},
            "conversation_history": conversation_history or [],
            "lead_type": LeadType.GENERAL.value,
            "qualification_stage": QualificationStage.CLASSIFY.value,
            "behavioral_signals": {},
            "compliance_passed": True,
            "compliance_reason": "",
            "response_content": "",
            "actions": [],
            "temperature": "cold",
            "is_qualified": False,
            "scores": {},
            "error": "",
        }

        try:
            final_state = await self._graph.ainvoke(initial_state)
            return QualificationResult(
                success=not final_state.get("error"),
                response_content=final_state["response_content"],
                actions=final_state["actions"],
                temperature=final_state["temperature"],
                lead_type=final_state["lead_type"],
                is_qualified=final_state["is_qualified"],
                behavioral_signals=final_state["behavioral_signals"],
                qualification_stage=final_state["qualification_stage"],
                scores=final_state.get("scores", {}),
                error=final_state.get("error") or None,
            )
        except Exception as exc:
            logger.error("Orchestrator pipeline failed: %s", exc, exc_info=True)
            return QualificationResult(
                success=False,
                response_content="",
                actions=[],
                temperature="cold",
                lead_type=LeadType.GENERAL.value,
                is_qualified=False,
                behavioral_signals={},
                qualification_stage=QualificationStage.ERROR.value,
                error=str(exc),
            )

    # ------------------------------------------------------------------
    # Graph construction
    # ------------------------------------------------------------------

    def _build_graph(self) -> StateGraph:
        workflow = StateGraph(OrchestratorState)

        workflow.add_node("classify", self._classify_lead)
        workflow.add_node("analyze_behavior", self._analyze_behavior)
        workflow.add_node("compliance_check", self._compliance_check)
        workflow.add_node("qualify_seller", self._qualify_seller)
        workflow.add_node("qualify_buyer", self._qualify_buyer)
        workflow.add_node("qualify_general", self._qualify_general)
        workflow.add_node("score_and_route", self._score_and_route)

        workflow.set_entry_point("classify")
        workflow.add_edge("classify", "analyze_behavior")
        workflow.add_edge("analyze_behavior", "compliance_check")
        workflow.add_conditional_edges(
            "compliance_check",
            self._route_by_lead_type,
            {
                "seller": "qualify_seller",
                "buyer": "qualify_buyer",
                "general": "qualify_general",
            },
        )
        workflow.add_edge("qualify_seller", "score_and_route")
        workflow.add_edge("qualify_buyer", "score_and_route")
        workflow.add_edge("qualify_general", "score_and_route")
        workflow.add_edge("score_and_route", END)

        return workflow.compile()

    # ------------------------------------------------------------------
    # Node: classify
    # ------------------------------------------------------------------

    async def _classify_lead(self, state: OrchestratorState) -> dict:
        """Determine lead type from tags first, then message intent."""
        tags = set(state["contact_tags"])

        # Tag-based classification (highest priority)
        if tags & SELLER_TAGS:
            lead_type = LeadType.SELLER.value
        elif tags & BUYER_TAGS:
            lead_type = LeadType.BUYER.value
        else:
            # Fall back to keyword intent analysis
            lead_type = self._classify_by_keywords(state["message"])

        logger.info(
            "Lead classified as %s for contact %s",
            lead_type,
            state["contact_id"],
        )
        return {
            "lead_type": lead_type,
            "qualification_stage": QualificationStage.ANALYZE.value,
        }

    def _classify_by_keywords(self, message: str) -> str:
        msg_lower = message.lower()
        seller_hits = sum(1 for kw in SELLER_INTENT_KEYWORDS if kw in msg_lower)
        buyer_hits = sum(1 for kw in BUYER_INTENT_KEYWORDS if kw in msg_lower)

        if seller_hits > buyer_hits:
            return LeadType.SELLER.value
        elif buyer_hits > seller_hits:
            return LeadType.BUYER.value
        return LeadType.GENERAL.value

    # ------------------------------------------------------------------
    # Node: analyze_behavior
    # ------------------------------------------------------------------

    async def _analyze_behavior(self, state: OrchestratorState) -> dict:
        """Run behavioral trigger analysis if detector is available."""
        if not self.behavioral_detector:
            return {"behavioral_signals": {}}

        try:
            analysis = await self.behavioral_detector.analyze_message(
                message=state["message"],
                contact_id=state["contact_id"],
                conversation_history=state["conversation_history"],
            )
            signals = {
                "composite_score": analysis.composite_score,
                "hedging_score": analysis.hedging_score,
                "urgency_score": analysis.urgency_score,
                "commitment_score": analysis.commitment_score,
                "drift_direction": analysis.drift_direction,
                "trigger_count": len(analysis.triggers),
            }
            return {"behavioral_signals": signals}
        except Exception as exc:
            logger.warning("Behavioral analysis failed: %s", exc)
            return {"behavioral_signals": {}}

    # ------------------------------------------------------------------
    # Node: compliance_check
    # ------------------------------------------------------------------

    async def _compliance_check(self, state: OrchestratorState) -> dict:
        """Pre-qualification compliance gate (deactivation tags, etc.)."""
        tags = set(state["contact_tags"])

        if tags & DEACTIVATION_TAGS:
            return {
                "compliance_passed": False,
                "compliance_reason": "deactivation_tag_present",
                "qualification_stage": QualificationStage.COMPLIANCE.value,
            }

        return {
            "compliance_passed": True,
            "compliance_reason": "",
            "qualification_stage": QualificationStage.QUALIFYING.value,
        }

    # ------------------------------------------------------------------
    # Router
    # ------------------------------------------------------------------

    def _route_by_lead_type(self, state: OrchestratorState) -> str:
        return state["lead_type"]

    # ------------------------------------------------------------------
    # Node: qualify_seller
    # ------------------------------------------------------------------

    async def _qualify_seller(self, state: OrchestratorState) -> dict:
        """Delegate to seller qualification logic."""
        history = state["conversation_history"]
        questions_answered = self._count_seller_answers(history)

        # Temperature based on questions answered (matches JorgeSellerConfig thresholds)
        if questions_answered >= 4:
            temperature = "hot"
        elif questions_answered >= 3:
            temperature = "warm"
        else:
            temperature = "cold"

        actions = []
        tag_map = {"hot": "Hot-Seller", "warm": "Warm-Seller", "cold": "Cold-Seller"}
        actions.append({"type": "add_tag", "tag": tag_map[temperature]})

        is_qualified = temperature == "hot"
        if is_qualified:
            actions.append({"type": "add_tag", "tag": "Seller-Qualified"})

        return {
            "temperature": temperature,
            "is_qualified": is_qualified,
            "actions": actions,
            "scores": {
                "questions_answered": questions_answered,
                "lead_type_confidence": 1.0,
            },
        }

    def _count_seller_answers(self, history: list) -> int:
        """Count seller qualification data points from conversation history."""
        fields = ["motivation", "timeline_acceptable", "property_condition", "price_expectation"]
        seller_prefs = {}
        for entry in history:
            if isinstance(entry, dict):
                sp = entry.get("seller_preferences", {})
                if isinstance(sp, dict):
                    seller_prefs.update({k: v for k, v in sp.items() if v is not None})
        return sum(1 for f in fields if seller_prefs.get(f) is not None)

    # ------------------------------------------------------------------
    # Node: qualify_buyer
    # ------------------------------------------------------------------

    async def _qualify_buyer(self, state: OrchestratorState) -> dict:
        """Delegate to buyer qualification logic."""
        history = state["conversation_history"]
        buyer_data = self._extract_buyer_data(history)

        fin_score = buyer_data.get("financial_readiness", 0)
        mot_score = buyer_data.get("buying_motivation", 0)
        avg = (fin_score + mot_score) / 2

        if fin_score >= 70 and mot_score >= 70:
            temperature = "hot"
        elif avg >= 50:
            temperature = "warm"
        else:
            temperature = "cold"

        tag_map = {"hot": "Hot-Buyer", "warm": "Warm-Buyer", "cold": "Cold-Buyer"}
        actions = [{"type": "add_tag", "tag": tag_map[temperature]}]

        is_qualified = fin_score >= 50 and mot_score >= 50
        if is_qualified:
            actions.append({"type": "add_tag", "tag": "Buyer-Qualified"})

        return {
            "temperature": temperature,
            "is_qualified": is_qualified,
            "actions": actions,
            "scores": {
                "financial_readiness": fin_score,
                "buying_motivation": mot_score,
            },
        }

    def _extract_buyer_data(self, history: list) -> dict:
        """Extract buyer qualification signals from conversation history."""
        data: Dict[str, float] = {"financial_readiness": 0, "buying_motivation": 0}
        for entry in history:
            if isinstance(entry, dict):
                data["financial_readiness"] = max(
                    data["financial_readiness"],
                    entry.get("financial_readiness_score", 0),
                )
                data["buying_motivation"] = max(
                    data["buying_motivation"],
                    entry.get("buying_motivation_score", 0),
                )
        return data

    # ------------------------------------------------------------------
    # Node: qualify_general
    # ------------------------------------------------------------------

    async def _qualify_general(self, state: OrchestratorState) -> dict:
        """General lead qualification — basic scoring."""
        msg_len = len(state["message"].split())
        behavioral = state.get("behavioral_signals", {})
        urgency = behavioral.get("urgency_score", 0)

        # Simple heuristic: longer message + urgency = warmer
        if urgency >= 0.7 or msg_len > 30:
            temperature = "warm"
        else:
            temperature = "cold"

        actions = [{"type": "add_tag", "tag": f"{'Warm' if temperature == 'warm' else 'Cold'}-Lead"}]

        return {
            "temperature": temperature,
            "is_qualified": False,
            "actions": actions,
            "scores": {"message_length": msg_len, "urgency_score": urgency},
        }

    # ------------------------------------------------------------------
    # Node: score_and_route
    # ------------------------------------------------------------------

    async def _score_and_route(self, state: OrchestratorState) -> dict:
        """Final scoring — incorporate behavioral signals into temperature."""
        behavioral = state.get("behavioral_signals", {})
        composite = behavioral.get("composite_score", 0)

        temperature = state["temperature"]
        is_qualified = state["is_qualified"]
        actions = list(state.get("actions", []))

        # Behavioral boost: if composite score is high, upgrade temperature
        if composite >= 0.8 and temperature == "warm":
            temperature = "hot"
            logger.info(
                "Behavioral boost: warm → hot for %s (composite=%.2f)",
                state["contact_id"],
                composite,
            )

        # Response content stub (actual content comes from the bot layer)
        response = state.get("response_content", "")

        return {
            "temperature": temperature,
            "is_qualified": is_qualified,
            "actions": actions,
            "response_content": response,
            "qualification_stage": QualificationStage.COMPLETE.value,
        }


# ---------------------------------------------------------------------------
# Singleton accessor
# ---------------------------------------------------------------------------

_orchestrator: Optional[LeadQualificationOrchestrator] = None


def get_orchestrator(**kwargs) -> LeadQualificationOrchestrator:
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = LeadQualificationOrchestrator(**kwargs)
    return _orchestrator
