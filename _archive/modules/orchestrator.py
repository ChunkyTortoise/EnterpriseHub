import os
import json
from typing import TypedDict, List, Optional, Dict, Any, Annotated
import operator
from langgraph.graph import StateGraph, END
import google.generativeai as genai
from modules.inventory_manager import InventoryManager

# Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

class AgentState(TypedDict):
    """
    The state of the agent workflow.
    """
    lead_id: str
    task: str # e.g., "find_match", "draft_email"
    lead_data: Optional[Dict[str, Any]]
    matched_properties: List[Dict[str, Any]]
    selected_property: Optional[Dict[str, Any]]
    generated_content: Optional[str] # The draft email/message
    logs: Annotated[List[str], operator.add]
    status: str

class RealEstateOrchestrator:
    def __init__(self):
        self.inventory = InventoryManager()
        # Using Gemini 2.0 Flash per roadmap
        self.model = genai.GenerativeModel('gemini-2.0-flash-exp')
        self.workflow = self._build_graph()

    def _build_graph(self):
        """
        Constructs the LangGraph workflow.
        """
        builder = StateGraph(AgentState)

        # 1. Define Nodes
        builder.add_node("lookup_lead", self.lookup_lead_node)
        builder.add_node("find_matches", self.find_matches_node)
        builder.add_node("generate_narrative", self.generate_narrative_node)
        builder.add_node("update_crm", self.update_crm_node)

        # 2. Define Edges
        # Start -> Lookup Lead
        builder.set_entry_point("lookup_lead")

        # Lookup -> Find Matches (if lead found) OR End (if not)
        builder.add_conditional_edges(
            "lookup_lead",
            self.check_lead_found,
            {
                "found": "find_matches",
                "not_found": END
            }
        )

        # Matches -> Generate Narrative (if matches found) OR End
        builder.add_conditional_edges(
            "find_matches",
            self.check_matches_found,
            {
                "has_matches": "generate_narrative",
                "no_matches": END
            }
        )

        # Narrative -> Update CRM
        builder.add_edge("generate_narrative", "update_crm")

        # Update CRM -> End
        builder.add_edge("update_crm", END)

        return builder.compile()

    # --- Node Implementations ---

    def lookup_lead_node(self, state: AgentState) -> Dict:
        """Fetch lead data from DB."""
        lead_id = state["lead_id"]
        print(f"🔍 Orchestrator: Looking up lead {lead_id}...")
        lead = self.inventory.get_lead(lead_id)
        
        if lead:
            return {
                "lead_data": lead, 
                "logs": [f"Found lead: {lead['name']}"]
            }
        else:
            print(f"❌ Orchestrator: Lead {lead_id} not found.")
            return {
                "lead_data": None,
                "logs": [f"Lead {lead_id} not found"],
                "status": "failed"
            }

    def find_matches_node(self, state: AgentState) -> Dict:
        """Use InventoryManager to get smart deck."""
        lead_id = state["lead_id"]
        print(f"🏡 Orchestrator: Finding matches for {lead_id}...")
        
        deck = self.inventory.get_smart_deck(lead_id)
        
        # Take top match for now for the narrative
        top_match = deck[0] if deck else None
        
        return {
            "matched_properties": deck,
            "selected_property": top_match,
            "logs": [f"Found {len(deck)} matches. Top: {top_match['address'] if top_match else 'None'}"]
        }

    def generate_narrative_node(self, state: AgentState) -> Dict:
        """Generate a personalized email/pitch using Gemini."""
        lead = state["lead_data"]
        prop = state["selected_property"]
        
        print(f"✍️ Orchestrator: Generating narrative for {prop['address']}...")
        
        prompt = f"""
        Role: Expert Real Estate Agent.
        Task: Write a short, personalized email to a client about a property match.
        
        Client: {lead['name']}
        Preferences: {json.dumps(lead['must_haves'])}
        
        Property: {prop['address']}, {prop['city']}
        Price: ${prop['price']:,}
        Features: {json.dumps(prop['tags'])}
        Description: {prop['description']}
        
        Instruction:
        1. Be warm and professional.
        2. Highlight why this property matches their specific preferences (mention the features).
        3. Keep it under 150 words.
        4. Ask for a viewing time.
        """
        
        try:
            response = self.model.generate_content(prompt)
            content = response.text.strip()
        except Exception as e:
            print(f"⚠️ API Error: {e}")
            content = f"Hi {lead['name']},\n\nI found a great property for you at {prop['address']}. It matches your needs! Let's view it soon.\n\n(Fallback generated due to API error: {str(e)[:50]}...)"
            
        return {
            "generated_content": content,
            "logs": ["Generated narrative"]
        }

    def update_crm_node(self, state: AgentState) -> Dict:
        """Log the interaction in the DB."""
        lead_id = state["lead_id"]
        prop = state["selected_property"]
        content = state["generated_content"]
        
        print(f"💾 Orchestrator: Updating CRM...")
        
        # Log that we sent a pitch (using 'pitch_sent' as action)
        self.inventory.log_interaction(
            lead_id=lead_id,
            property_id=prop['id'],
            action="pitch_generated",
            feedback={"content_snippet": content[:50] + "..."}
        )
        
        return {
            "status": "completed",
            "logs": ["CRM updated with pitch interaction"]
        }

    # --- Conditional Logic ---

    def check_lead_found(self, state: AgentState) -> str:
        return "found" if state["lead_data"] else "not_found"

    def check_matches_found(self, state: AgentState) -> str:
        return "has_matches" if state["matched_properties"] else "no_matches"

    # --- Public API ---

    def run_workflow(self, lead_id: str, task: str = "match_and_pitch"):
        """
        Main entry point to run the orchestrator.
        """
        initial_state = {
            "lead_id": lead_id,
            "task": task,
            "lead_data": None,
            "matched_properties": [],
            "selected_property": None,
            "generated_content": None,
            "logs": [],
            "status": "started"
        }
        
        result = self.workflow.invoke(initial_state)
        return result

if __name__ == "__main__":
    # Quick Test if run directly
    orc = RealEstateOrchestrator()
    # Assuming lead_001 exists from inventory_manager.py's main run or similar
    # We might need to ensure data exists first.
    print("Orchestrator loaded. Run via scripts/demo_orchestration.py")
