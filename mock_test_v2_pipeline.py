"""
Mock Test script for the V2 Agentic Pipeline.
Uses PydanticAI TestModel to bypass API rate limits.
"""

import asyncio
import json
from pydantic_ai.models.test import TestModel
from ghl_real_estate_ai.agent_system.v2.agents.research_agent import research_agent, ResearchResult, MarketContext
from ghl_real_estate_ai.agent_system.v2.agents.analysis_agent import analysis_agent, AnalysisResult, FinancialProjections, RiskAssessment
from ghl_real_estate_ai.agent_system.v2.agents.design_agent import design_agent, DesignResult, StagingConcept, UIComponentSpec
from ghl_real_estate_ai.agent_system.v2.agents.executive_agent import executive_agent, ExecutiveResult, SlideContent
from ghl_real_estate_ai.agent_system.v2.conductor import conductor_app

async def main():
    print("🧪 Starting Mock V2 Pipeline Test...")
    
    # 1. Setup Mock Models for all agents
    research_agent.model = TestModel()
    analysis_agent.model = TestModel()
    design_agent.model = TestModel()
    executive_agent.model = TestModel()
    
    address = "123 Maple St, Austin, TX"
    request = "full_pipeline"
    market = "Austin, TX"
    
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
        "status": "started"
    }
    
    try:
        # We invoke the graph directly since conductor.process_request 
        # might re-instantiate deps or something if we aren't careful, 
        # but here we just want to see the nodes fire.
        result = await conductor_app.ainvoke(initial_state)
        
        print("\n--- MOCK TEST RESULTS ---")
        print(f"Status: {result.get('status')}")
        
        class EnumEncoder(json.JSONEncoder):
            def default(self, obj):
                from enum import Enum
                if isinstance(obj, Enum):
                    return obj.value
                return super().default(obj)

        if result.get('research_data'):
            print("✅ Research Data captured (Mock)")
        if result.get('analysis_results'):
            print("✅ Analysis Results captured (Mock)")
        if result.get('design_data'):
            print("✅ Design Data captured (Mock)")
        if result.get('executive_summary'):
            print("✅ Executive Summary captured (Mock)")
            
        if result.get('errors'):
            print(f"⚠️ Errors: {result.get('errors')}")
            
        with open("mock_v2_results.json", "w") as f:
            json.dump(result, f, indent=2, cls=EnumEncoder)
            
    except Exception as e:
        print(f"💥 Mock Pipeline Test CRASHED: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
