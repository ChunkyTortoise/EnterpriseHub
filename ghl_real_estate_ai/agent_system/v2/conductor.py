"""
Conductor (V2) - Agent Orchestrator
Uses LangGraph to coordinate Research, Analysis, Design, Executive, and Marketing agents.
Implements the 'Modular Agentic Powerhouse' state machine with Phase 6 Enterprise Polish.
"""

from typing import TypedDict, List, Optional, Annotated, Any, Dict
import operator
import time
from langgraph.graph import StateGraph, START, END

from ghl_real_estate_ai.agent_system.v2.agents.research_agent import research_agent, ResearchDeps
from ghl_real_estate_ai.agent_system.v2.agents.analysis_agent import analysis_agent, AnalysisDeps
from ghl_real_estate_ai.agent_system.v2.agents.design_agent import design_agent, DesignDeps
from ghl_real_estate_ai.agent_system.v2.agents.executive_agent import executive_agent, ExecutiveDeps
from ghl_real_estate_ai.agent_system.v2.agents.marketing_agent import marketing_agent, MarketingDeps

from ghl_real_estate_ai.services.semantic_cache_service import semantic_cache
from ghl_real_estate_ai.services.ghl_integration_service import ghl_integration_service
from ghl_real_estate_ai.services.lead_scoring_service import lead_scoring_service
from ghl_real_estate_ai.services.visual_asset_service import visual_asset_service
from ghl_real_estate_ai.services.performance_monitoring_service import performance_monitor
from ghl_real_estate_ai.services.service6_ai_integration import create_service6_ai_orchestrator

# 1. Define the Graph State
class ConductorState(TypedDict):
    # Inputs
    user_request: str
    property_address: str
    market: Optional[str]
    
    # Internal State
    intent: Optional[str]
    research_data: Optional[Dict[str, Any]]
    analysis_results: Optional[Dict[str, Any]]
    design_data: Optional[Dict[str, Any]]
    executive_summary: Optional[Dict[str, Any]]
    
    # Phase 5: Outreach & Revenue Bridge
    matched_leads: Optional[List[Dict[str, Any]]]
    marketing_campaigns: Optional[Dict[str, Any]]
    
    # Phase 6 & 7: Enterprise Polish & Moat
    evaluations: Annotated[Dict[str, Any], operator.ior] # Merges dicts
    staged_images: Optional[List[Dict[str, str]]]
    service6_insights: Optional[Dict[str, Any]] # Advanced Lead Recovery
    
    # Metadata
    errors: Annotated[List[str], operator.add]
    status: str

# 2. Define Node Functions
async def intent_classifier_node(state: ConductorState):
    """Classify the user intent to route to the correct agents."""
    request = state["user_request"].lower()
    intent = "FULL_PIPELINE"
    if "research" in request and "analyze" not in request:
        intent = "RESEARCH_ONLY"
    elif "analyze" in request and "research" not in request:
        intent = "ANALYZE_ONLY"
    elif "market" in request or "outreach" in request:
        intent = "MARKETING_FOCUS"
        
    return {"intent": intent, "status": "classifying"}

async def research_node(state: ConductorState):
    """Execute the Research Agent."""
    start_time = time.time()
    query = f"research:{state['property_address']}:{state.get('market')}"
    cached = await semantic_cache.get(query)
    if cached:
        return {"research_data": cached, "status": "research_complete_cached"}

    print(f"🔍 Researching property: {state['property_address']}")
    deps = ResearchDeps()
    try:
        result = await research_agent.run(
            f"Perform research on {state['property_address']} in {state.get('market') or 'Unknown'}",
            deps=deps
        )
        data = result.output.model_dump()
        
        # Phase 6: Log Performance
        performance_monitor.log_agent_run("researcher", time.time() - start_time, {"input": 1200, "output": 800}, "success")
        
        await semantic_cache.set(query, data)
        return {
            "research_data": data,
            "status": "research_complete"
        }
    except Exception as e:
        return {"errors": [f"Research Error: {str(e)}"], "status": "failed"}

async def analysis_node(state: ConductorState):
    """Execute the Analysis Agent using research data."""
    start_time = time.time()
    if not state.get("research_data"):
        return {"errors": ["No research data for analysis"], "status": "failed"}
        
    query = f"analysis:{state['property_address']}:{state['research_data']}"
    cached = await semantic_cache.get(query)
    if cached:
        return {"analysis_results": cached, "status": "analysis_complete_cached"}

    print(f"📊 Analyzing investment potential for: {state['property_address']}")
    deps = AnalysisDeps()
    try:
        result = await analysis_agent.run(
            f"Analyze investment potential based on this research: {state['research_data']}",
            deps=deps
        )
        data = result.output.model_dump()
        
        # Phase 6: Log Performance
        performance_monitor.log_agent_run("analyst", time.time() - start_time, {"input": 2500, "output": 450}, "success")
        
        await semantic_cache.set(query, data)
        return {
            "analysis_results": data,
            "status": "analysis_complete"
        }
    except Exception as e:
        return {"errors": [f"Analysis Error: {str(e)}"], "status": "failed"}

async def design_node(state: ConductorState):
    """Execute the Design Agent using analysis results."""
    start_time = time.time()
    if not state.get("analysis_results"):
        return {"errors": ["No analysis results for design"], "status": "failed"}
        
    query = f"design:{state['property_address']}:{state['analysis_results']}"
    cached = await semantic_cache.get(query)
    if cached:
        # Regenerate images if not in cache (or just return them if they were stored)
        staged_images = cached.get("staged_images")
        if not staged_images:
            staged_rooms = [room.get("room_name") for room in cached.get("staged_rooms", [])]
            staging_style = cached.get("theme_name", "Modern")
            staged_images = await visual_asset_service.generate_staging_images(staging_style, staged_rooms)
            cached["staged_images"] = staged_images
            await semantic_cache.set(query, cached)
            
        return {
            "design_data": cached, 
            "staged_images": staged_images,
            "status": "design_complete_cached"
        }

    print(f"🎨 Generating design concepts for: {state['property_address']}")
    deps = DesignDeps()
    try:
        result = await design_agent.run(
            f"Create visual staging and UI specs for this property based on analysis: {state['analysis_results']}",
            deps=deps
        )
        data = result.output.model_dump()
        
        # Phase 6: Generate High-Fidelity Staging Images
        staged_rooms = [room.room_name for room in result.output.staged_rooms]
        staging_style = result.output.staged_rooms[0].style if result.output.staged_rooms else "Modern"
        staged_images = await visual_asset_service.generate_staging_images(staging_style, staged_rooms)
        
        # Store images in the data dict for caching
        data["staged_images"] = staged_images
        
        # Log Performance
        performance_monitor.log_agent_run("designer", time.time() - start_time, {"input": 1500, "output": 600}, "success")
        
        await semantic_cache.set(query, data)
        return {
            "design_data": data,
            "staged_images": staged_images,
            "status": "design_complete"
        }
    except Exception as e:
        return {"errors": [f"Design Error: {str(e)}"], "status": "failed"}

async def executive_node(state: ConductorState):
    """Execute the Executive Agent to synthesize everything."""
    start_time = time.time()
    if not state.get("design_data"):
        return {"errors": ["No design data for executive synthesis"], "status": "failed"}
        
    query = f"executive:{state['property_address']}:{state['analysis_results']}:{state['design_data']}"
    cached = await semantic_cache.get(query)
    if cached:
        return {"executive_summary": cached, "status": "executive_complete_cached"}

    print(f"👔 Synthesizing executive summary for: {state['property_address']}")
    deps = ExecutiveDeps()
    try:
        result = await executive_agent.run(
            (
                f"Synthesize this property opportunity into an executive narrative.\n"
                f"Research: {state['research_data']}\n"
                f"Analysis: {state['analysis_results']}\n"
                f"Design: {state['design_data']}"
            ),
            deps=deps
        )
        data = result.output.model_dump()
        
        # Log Performance
        performance_monitor.log_agent_run("executive", time.time() - start_time, {"input": 3500, "output": 1200}, "success")
        
        await semantic_cache.set(query, data)
        return {
            "executive_summary": data,
            "status": "executive_complete"
        }
    except Exception as e:
        return {"errors": [f"Executive Error: {str(e)}"], "status": "failed"}

async def marketing_node(state: ConductorState):
    """Execute the Marketing Agent to bridge to revenue."""
    start_time = time.time()
    if not state.get("executive_summary"):
        return {"errors": ["No executive summary for marketing"], "status": "failed"}
        
    print(f"📣 Generating marketing campaigns and matching leads for: {state['property_address']}")
    
    # 1. Fetch leads from GHL
    leads = await ghl_integration_service.get_active_leads()
    
    # 2. Match leads to property
    research_data = state.get("research_data") or {}
    analysis_results = state.get("analysis_results") or {}
    subject_property = research_data.get("subject_property") or {}
    price = subject_property.get("price") or research_data.get("market_context", {}).get("median_price", 0)
    tags = research_data.get("market_context", {}).get("top_selling_points", [])
    
    property_info = {"address": state["property_address"], "market": state.get("market"), "price": price, "tags": tags}
    matched_leads = lead_scoring_service.match_leads_to_property(property_info, leads)
    
    # 3. Generate Marketing Campaign
    deps = MarketingDeps(ghl_service=ghl_integration_service)
    try:
        top_lead = matched_leads[0] if matched_leads else {"first_name": "Prospect"}
        result = await marketing_agent.run(
            (f"Create a marketing campaign for this property.\nNarrative: {state['executive_summary'].get('investor_narrative')}\nTarget Lead Example: {top_lead}"),
            deps=deps
        )
        marketing_data = result.output.model_dump()
        
        # Log Performance
        performance_monitor.log_agent_run("marketer", time.time() - start_time, {"input": 3000, "output": 900}, "success")
        
        return {
            "matched_leads": matched_leads,
            "marketing_campaigns": marketing_data,
            "status": "marketing_complete"
        }
    except Exception as e:
        return {"errors": [f"Marketing Error: {str(e)}"], "status": "failed"}

async def lead_recovery_node(state: ConductorState):
    """Phase 7: Hardened Lead Recovery Engine (Service 6)."""
    if not state.get("matched_leads"):
        return {"status": "no_leads_for_recovery"}
        
    print(f"🚀 Hardening lead recovery using Service 6 AI...")
    orchestrator = create_service6_ai_orchestrator()
    await orchestrator.initialize()
    
    recovery_results = []
    # Analyze the top 3 leads deeply
    for lead in state["matched_leads"][:3]:
        try:
            analysis = await orchestrator.analyze_lead(lead.get("id", "unknown"), lead)
            recovery_results.append({
                "lead_id": lead.get("id"),
                "unified_score": analysis.unified_lead_score,
                "priority": analysis.priority_level,
                "recommended_actions": analysis.immediate_actions,
                "sentiment": analysis.predictive_insights.get("sentiment") if analysis.predictive_insights else "Neutral"
            })
        except Exception as e:
            print(f"⚠️ Service 6 Analysis failed for lead {lead.get('id')}: {e}")
            
    return {
        "service6_insights": {"recovery_analysis": recovery_results},
        "status": "lead_recovery_complete"
    }

async def evaluation_node(state: ConductorState):
    """Phase 6: Final evaluation and data moat update."""
    print(f"⚖️ Performing final enterprise-grade evaluation...")
    
    # Evaluate the primary results
    analysis_eval = performance_monitor.evaluate_output("analyst", state.get("analysis_results"))
    exec_eval = performance_monitor.evaluate_output("executive", state.get("executive_summary"))
    
    evaluations = {
        "analysis_quality": analysis_eval,
        "executive_quality": exec_eval,
        "overall_platform_score": (analysis_eval["score"] + exec_eval["score"]) / 2
    }
    
    return {
        "evaluations": evaluations,
        "status": "complete_polished"
    }

# 3. Build the Graph
workflow = StateGraph(ConductorState)

# Add Nodes
workflow.add_node("classifier", intent_classifier_node)
workflow.add_node("researcher", research_node)
workflow.add_node("analyst", analysis_node)
workflow.add_node("designer", design_node)
workflow.add_node("executive", executive_node)
workflow.add_node("marketer", marketing_node)
workflow.add_node("lead_recovery", lead_recovery_node)
workflow.add_node("evaluator", evaluation_node)

# Define Edges
workflow.add_edge(START, "classifier")

def route_after_classifier(state: ConductorState):
    if state["intent"] == "ANALYZE_ONLY": return "analyst"
    return "researcher"

workflow.add_conditional_edges("classifier", route_after_classifier, {"researcher": "researcher", "analyst": "analyst"})
workflow.add_edge("researcher", "analyst")
workflow.add_edge("analyst", "designer")
workflow.add_edge("designer", "executive")
workflow.add_edge("executive", "marketer")
workflow.add_edge("marketer", "lead_recovery")
workflow.add_edge("lead_recovery", "evaluator")
workflow.add_edge("evaluator", END)

# Compile Graph
conductor_app = workflow.compile()

# Example invocation wrapper
async def process_request(address: str, request: str, market: Optional[str] = None):
    initial_state = {
        "user_request": request,
        "property_address": address,
        "market": market,
        "errors": [],
        "intent": None,
        "research_data": None,
        "analysis_results": None,
        "design_data": None,
        "executive_summary": None,
        "matched_leads": None,
        "marketing_campaigns": None,
        "evaluations": {},
        "staged_images": None,
        "service6_insights": None,
        "status": "started"
    }
    return await conductor_app.ainvoke(initial_state)