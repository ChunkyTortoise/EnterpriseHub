"""
Workflow Builder for constructing LangGraph workflow graphs.
"""

from typing import TYPE_CHECKING

from langgraph.graph import END, StateGraph

from ghl_real_estate_ai.ghl_utils.logger import get_logger

if TYPE_CHECKING:
    from ghl_real_estate_ai.agents.lead.config import LeadBotConfig

logger = get_logger(__name__)


class WorkflowBuilder:
    """Builds LangGraph workflow graphs for lead follow-up sequences"""

    def __init__(self, config: "LeadBotConfig", nodes: "WorkflowNodes"):
        self.config = config
        self.nodes = nodes

    def build_unified_graph(self) -> StateGraph:
        """Build workflow graph based on enabled features"""
        if (
            self.config.enable_predictive_analytics
            or self.config.enable_behavioral_optimization
            or self.config.enable_track3_intelligence
            or self.config.enable_bot_intelligence
        ):
            return self._build_enhanced_graph()
        else:
            return self._build_standard_graph()

    def _build_standard_graph(self) -> StateGraph:
        """Build standard workflow graph"""
        from ghl_real_estate_ai.models.workflows import LeadFollowUpState

        workflow = StateGraph(LeadFollowUpState)

        # Define Nodes
        workflow.add_node("analyze_intent", self.nodes.analyze_intent)
        workflow.add_node("determine_path", self.nodes.determine_path)
        workflow.add_node("generate_cma", self.nodes.generate_cma)

        # Follow-up Nodes
        workflow.add_node("send_day_3_sms", self.nodes.send_day_3_sms)
        workflow.add_node("initiate_day_7_call", self.nodes.initiate_day_7_call)
        workflow.add_node("send_day_14_email", self.nodes.send_day_14_email)
        workflow.add_node("send_day_30_nudge", self.nodes.send_day_30_nudge)

        # Full Lifecycle Nodes
        workflow.add_node("schedule_showing", self.nodes.schedule_showing)
        workflow.add_node("post_showing_survey", self.nodes.post_showing_survey)
        workflow.add_node("facilitate_offer", self.nodes.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.nodes.contract_to_close_nurture)

        # Define Edges
        workflow.set_entry_point("analyze_intent")
        workflow.add_edge("analyze_intent", "determine_path")

        # Conditional Routing based on 'current_step' and 'engagement_status'
        workflow.add_conditional_edges(
            "determine_path",
            self.nodes.route_next_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_day_3_sms",
                "day_7": "initiate_day_7_call",
                "day_14": "send_day_14_email",
                "day_30": "send_day_30_nudge",
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
                "qualified": END,
                "nurture": END,
            },
        )

        # All actions end for this single-turn execution
        workflow.add_edge("generate_cma", END)
        workflow.add_edge("send_day_3_sms", END)
        workflow.add_edge("initiate_day_7_call", END)
        workflow.add_edge("send_day_14_email", END)
        workflow.add_edge("send_day_30_nudge", END)
        workflow.add_edge("schedule_showing", END)
        workflow.add_edge("post_showing_survey", END)
        workflow.add_edge("facilitate_offer", END)
        workflow.add_edge("contract_to_close_nurture", END)

        return workflow.compile()

    def _build_enhanced_graph(self) -> StateGraph:
        """Build enhanced workflow with predictive analytics and optimization"""
        from ghl_real_estate_ai.models.workflows import LeadFollowUpState

        workflow = StateGraph(LeadFollowUpState)

        # Enhanced nodes
        workflow.add_node("analyze_intent", self.nodes.analyze_intent)
        if self.config.enable_bot_intelligence and self.nodes.intelligence_middleware:
            workflow.add_node("gather_lead_intelligence", self.nodes.gather_lead_intelligence)
        if self.config.enable_behavioral_optimization or self.config.enable_predictive_analytics:
            workflow.add_node("behavioral_analysis", self.nodes.analyze_behavioral_patterns)
        if self.config.enable_behavioral_optimization:
            workflow.add_node("predict_optimization", self.nodes.predict_sequence_optimization)
        if self.config.enable_track3_intelligence:
            workflow.add_node("track3_market_intelligence", self.nodes.apply_track3_market_intelligence)

        workflow.add_node("determine_path", self.nodes.determine_path)
        workflow.add_node("generate_cma", self.nodes.generate_cma)

        # Enhanced follow-up nodes
        workflow.add_node("send_optimized_day_3", self.nodes.send_optimized_day_3)
        workflow.add_node("initiate_predictive_day_7", self.nodes.initiate_predictive_day_7)
        workflow.add_node("send_adaptive_day_14", self.nodes.send_adaptive_day_14)
        workflow.add_node("send_intelligent_day_30", self.nodes.send_intelligent_day_30)

        # Lifecycle nodes (unchanged)
        workflow.add_node("schedule_showing", self.nodes.schedule_showing)
        workflow.add_node("post_showing_survey", self.nodes.post_showing_survey)
        workflow.add_node("facilitate_offer", self.nodes.facilitate_offer)
        workflow.add_node("contract_to_close_nurture", self.nodes.contract_to_close_nurture)

        # Enhanced flow
        workflow.set_entry_point("analyze_intent")

        # Build flow based on enabled features
        current_node = "analyze_intent"

        if self.config.enable_bot_intelligence and self.nodes.intelligence_middleware:
            workflow.add_edge(current_node, "gather_lead_intelligence")
            current_node = "gather_lead_intelligence"

        if self.config.enable_behavioral_optimization or self.config.enable_predictive_analytics:
            workflow.add_edge(current_node, "behavioral_analysis")
            current_node = "behavioral_analysis"

        if self.config.enable_behavioral_optimization:
            workflow.add_edge(current_node, "predict_optimization")
            current_node = "predict_optimization"

        if self.config.enable_track3_intelligence:
            workflow.add_edge(current_node, "track3_market_intelligence")
            current_node = "track3_market_intelligence"

        workflow.add_edge(current_node, "determine_path")

        # Enhanced conditional routing
        workflow.add_conditional_edges(
            "determine_path",
            self.nodes.route_enhanced_step,
            {
                "generate_cma": "generate_cma",
                "day_3": "send_optimized_day_3",
                "day_7": "initiate_predictive_day_7",
                "day_14": "send_adaptive_day_14",
                "day_30": "send_intelligent_day_30",
                "schedule_showing": "schedule_showing",
                "post_showing": "post_showing_survey",
                "facilitate_offer": "facilitate_offer",
                "closing_nurture": "contract_to_close_nurture",
                "qualified": END,
                "nurture": END,
            },
        )

        # All actions end
        for node in [
            "generate_cma",
            "send_optimized_day_3",
            "initiate_predictive_day_7",
            "send_adaptive_day_14",
            "send_intelligent_day_30",
            "schedule_showing",
            "post_showing_survey",
            "facilitate_offer",
            "contract_to_close_nurture",
        ]:
            workflow.add_edge(node, END)

        return workflow.compile()
