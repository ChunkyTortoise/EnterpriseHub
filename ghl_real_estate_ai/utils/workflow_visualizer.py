"""
Workflow Visualization Utility

Generates Mermaid diagrams for LangGraph workflows across all Jorge bots.
Uses LangGraph's built-in .get_graph().draw_mermaid() method.

Usage:
    python -m ghl_real_estate_ai.utils.workflow_visualizer --all
    python -m ghl_real_estate_ai.utils.workflow_visualizer --bot lead
    python -m ghl_real_estate_ai.utils.workflow_visualizer --bot buyer
    python -m ghl_real_estate_ai.utils.workflow_visualizer --bot seller
"""
import os
from pathlib import Path
from typing import Literal

# Suppress warnings during visualization
os.environ.setdefault("SUPPRESS_WARNINGS", "1")

from ghl_real_estate_ai.ghl_utils.logger import get_logger

logger = get_logger(__name__)

BotType = Literal["lead", "buyer", "seller"]


def visualize_lead_bot_workflow(output_dir: Path) -> None:
    """Generate Mermaid diagram for Lead Bot workflow"""
    # Import only what we need for graph building
    from langgraph.graph import END, StateGraph

    from ghl_real_estate_ai.models.workflows import LeadFollowUpState

    logger.info("Generating Lead Bot workflow diagram...")

    # Build standard workflow directly (minimal dependencies)
    workflow_standard = StateGraph(LeadFollowUpState)

    # Define standard workflow nodes (names only, no actual functions needed for visualization)
    nodes_standard = [
        "analyze_intent",
        "determine_path",
        "generate_cma",
        "send_day_3_sms",
        "initiate_day_7_call",
        "send_day_14_email",
        "send_day_30_nudge",
        "schedule_showing",
        "post_showing_survey",
        "facilitate_offer",
        "contract_to_close_nurture",
    ]

    # Add dummy nodes (we just need structure for visualization)
    dummy_func = lambda state: state
    for node in nodes_standard:
        workflow_standard.add_node(node, dummy_func)

    # Define edges
    workflow_standard.set_entry_point("analyze_intent")
    workflow_standard.add_edge("analyze_intent", "determine_path")

    # Conditional routing
    workflow_standard.add_conditional_edges(
        "determine_path",
        lambda state: "generate_cma",  # Dummy router
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

    # All actions end
    for node in nodes_standard[2:]:  # Skip analyze_intent and determine_path
        workflow_standard.add_edge(node, END)

    graph_standard = workflow_standard.compile()
    mermaid_standard = graph_standard.get_graph().draw_mermaid()
    standard_path = output_dir / "lead_bot_standard_workflow.mmd"
    standard_path.write_text(mermaid_standard)
    logger.info(f"✓ Lead Bot standard workflow → {standard_path}")

    # Build enhanced workflow
    workflow_enhanced = StateGraph(LeadFollowUpState)

    nodes_enhanced = [
        "analyze_intent",
        "behavioral_analysis",
        "predict_optimization",
        "track3_market_intelligence",
        "determine_path",
        "generate_cma",
        "send_optimized_day_3",
        "initiate_predictive_day_7",
        "send_adaptive_day_14",
        "send_intelligent_day_30",
        "schedule_showing",
        "post_showing_survey",
        "facilitate_offer",
        "contract_to_close_nurture",
    ]

    for node in nodes_enhanced:
        workflow_enhanced.add_node(node, dummy_func)

    workflow_enhanced.set_entry_point("analyze_intent")
    workflow_enhanced.add_edge("analyze_intent", "behavioral_analysis")
    workflow_enhanced.add_edge("behavioral_analysis", "predict_optimization")
    workflow_enhanced.add_edge("predict_optimization", "track3_market_intelligence")
    workflow_enhanced.add_edge("track3_market_intelligence", "determine_path")

    workflow_enhanced.add_conditional_edges(
        "determine_path",
        lambda state: "generate_cma",
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

    for node in nodes_enhanced[5:]:  # Skip early stages
        workflow_enhanced.add_edge(node, END)

    graph_enhanced = workflow_enhanced.compile()
    mermaid_enhanced = graph_enhanced.get_graph().draw_mermaid()
    enhanced_path = output_dir / "lead_bot_enhanced_workflow.mmd"
    enhanced_path.write_text(mermaid_enhanced)
    logger.info(f"✓ Lead Bot enhanced workflow → {enhanced_path}")


def visualize_buyer_bot_workflow(output_dir: Path) -> None:
    """Generate Mermaid diagram for Buyer Bot workflow"""
    from langgraph.graph import END, StateGraph

    from ghl_real_estate_ai.models.buyer_bot_state import BuyerBotState

    logger.info("Generating Buyer Bot workflow diagram...")

    workflow = StateGraph(BuyerBotState)

    nodes = [
        "analyze_buyer_intent",
        "classify_buyer_persona",
        "generate_executive_brief",
        "assess_financial_readiness",
        "calculate_affordability",
        "qualify_property_needs",
        "match_properties",
        "handle_objections",
        "generate_buyer_response",
        "schedule_next_action",
    ]

    dummy_func = lambda state: state
    for node in nodes:
        workflow.add_node(node, dummy_func)

    workflow.set_entry_point("analyze_buyer_intent")
    workflow.add_edge("analyze_buyer_intent", "classify_buyer_persona")
    workflow.add_edge("classify_buyer_persona", "assess_financial_readiness")
    workflow.add_edge("assess_financial_readiness", "calculate_affordability")
    workflow.add_edge("calculate_affordability", "qualify_property_needs")
    workflow.add_edge("qualify_property_needs", "match_properties")

    # Conditional routing for objection handling
    workflow.add_conditional_edges(
        "match_properties",
        lambda state: "handle_objections",
        {
            "handle_objections": "handle_objections",
            "generate_response": "generate_buyer_response",
        },
    )

    workflow.add_edge("handle_objections", "generate_buyer_response")
    workflow.add_edge("generate_buyer_response", "generate_executive_brief")
    workflow.add_edge("generate_executive_brief", "schedule_next_action")
    workflow.add_edge("schedule_next_action", END)

    graph = workflow.compile()
    mermaid = graph.get_graph().draw_mermaid()

    output_path = output_dir / "buyer_bot_workflow.mmd"
    output_path.write_text(mermaid)
    logger.info(f"✓ Buyer Bot workflow → {output_path}")


def visualize_seller_bot_workflow(output_dir: Path) -> None:
    """Generate Mermaid diagram for Seller Bot workflow"""
    from langgraph.graph import END, StateGraph

    from ghl_real_estate_ai.models.seller_bot_state import JorgeSellerState

    logger.info("Generating Seller Bot workflow diagram...")

    # Standard workflow
    workflow_standard = StateGraph(JorgeSellerState)

    nodes_standard = [
        "analyze_intent",
        "handle_objection",
        "generate_cma",
        "provide_pricing_guidance",
        "analyze_market_conditions",
        "detect_stall",
        "defend_valuation",
        "prepare_listing",
        "select_strategy",
        "generate_jorge_response",
        "generate_executive_brief",
        "recalculate_pcs",
        "execute_follow_up",
    ]

    dummy_func = lambda state: state
    for node in nodes_standard:
        workflow_standard.add_node(node, dummy_func)

    workflow_standard.set_entry_point("analyze_intent")
    workflow_standard.add_edge("analyze_intent", "detect_stall")

    # Conditional routing
    workflow_standard.add_conditional_edges(
        "detect_stall",
        lambda state: "select_strategy",
        {
            "handle_objection": "handle_objection",
            "generate_cma": "generate_cma",
            "pricing_guidance": "provide_pricing_guidance",
            "market_analysis": "analyze_market_conditions",
            "defend_valuation": "defend_valuation",
            "prepare_listing": "prepare_listing",
            "select_strategy": "select_strategy",
        },
    )

    # Intermediate routing
    for node in ["handle_objection", "generate_cma", "provide_pricing_guidance", "analyze_market_conditions", "defend_valuation", "prepare_listing"]:
        workflow_standard.add_edge(node, "select_strategy")

    workflow_standard.add_edge("select_strategy", "generate_jorge_response")
    workflow_standard.add_edge("generate_jorge_response", "generate_executive_brief")
    workflow_standard.add_edge("generate_executive_brief", "recalculate_pcs")
    workflow_standard.add_edge("recalculate_pcs", "execute_follow_up")
    workflow_standard.add_edge("execute_follow_up", END)

    graph_standard = workflow_standard.compile()
    mermaid_standard = graph_standard.get_graph().draw_mermaid()
    standard_path = output_dir / "seller_bot_standard_workflow.mmd"
    standard_path.write_text(mermaid_standard)
    logger.info(f"✓ Seller Bot standard workflow → {standard_path}")

    # Enhanced adaptive workflow
    workflow_enhanced = StateGraph(JorgeSellerState)

    nodes_enhanced = [
        "analyze_intent",
        "detect_stall",
        "adaptive_strategy",
        "generate_adaptive_response",
        "generate_executive_brief",
        "recalculate_pcs",
        "execute_follow_up",
        "update_memory",
    ]

    for node in nodes_enhanced:
        workflow_enhanced.add_node(node, dummy_func)

    workflow_enhanced.set_entry_point("analyze_intent")
    workflow_enhanced.add_edge("analyze_intent", "detect_stall")
    workflow_enhanced.add_edge("detect_stall", "adaptive_strategy")

    # Conditional adaptive routing
    workflow_enhanced.add_conditional_edges(
        "adaptive_strategy",
        lambda state: "generate_adaptive_response",
        {
            "generate_adaptive_response": "generate_adaptive_response",
            "update_memory": "update_memory",
        },
    )

    workflow_enhanced.add_edge("generate_adaptive_response", "generate_executive_brief")
    workflow_enhanced.add_edge("generate_executive_brief", "recalculate_pcs")
    workflow_enhanced.add_edge("recalculate_pcs", "update_memory")
    workflow_enhanced.add_edge("update_memory", "execute_follow_up")
    workflow_enhanced.add_edge("execute_follow_up", END)

    graph_enhanced = workflow_enhanced.compile()
    mermaid_enhanced = graph_enhanced.get_graph().draw_mermaid()
    enhanced_path = output_dir / "seller_bot_enhanced_workflow.mmd"
    enhanced_path.write_text(mermaid_enhanced)
    logger.info(f"✓ Seller Bot enhanced workflow → {enhanced_path}")


def generate_workflow_diagrams(bot: BotType | None = None) -> None:
    """Generate workflow diagrams for specified bot(s)"""
    output_dir = Path(__file__).parent.parent.parent / "docs" / "workflows"
    output_dir.mkdir(exist_ok=True)
    
    if bot is None or bot == "lead":
        visualize_lead_bot_workflow(output_dir)
    
    if bot is None or bot == "buyer":
        visualize_buyer_bot_workflow(output_dir)
    
    if bot is None or bot == "seller":
        visualize_seller_bot_workflow(output_dir)
    
    logger.info(f"\n✅ Workflow diagrams generated in {output_dir}")
    logger.info("\nTo view diagrams:")
    logger.info("  - Use Mermaid Live Editor: https://mermaid.live")
    logger.info("  - Install Mermaid VS Code extension")
    logger.info("  - Use GitHub's native Mermaid rendering in markdown")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate LangGraph workflow diagrams")
    parser.add_argument(
        "--bot",
        choices=["lead", "buyer", "seller"],
        help="Generate diagram for specific bot (default: all)",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Generate diagrams for all bots",
    )
    
    args = parser.parse_args()
    
    bot_filter = None if args.all else args.bot
    generate_workflow_diagrams(bot_filter)
